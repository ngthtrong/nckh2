"""Read-only RQ2 precision/provenance audit; never reruns ranking or generation.

Run with report/build/revision-rq2-env/bin/python. Outputs stay beside this file.
"""
from pathlib import Path
from collections import Counter
from importlib.metadata import version
import csv
import hashlib
import importlib.util
import json
import subprocess
import sys

import numpy as np
import pandas as pd
from scipy.stats import rankdata, wilcoxon

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
OLD = OUT.parent
SOURCE = ROOT / "thucnghiem/results/rq2_results"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def command(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).splitlines()


paths = [p for p in SOURCE.iterdir() if p.is_file()]
paths += [ROOT / "thucnghiem/results/RQ2_Priority_Robustness_Colab.ipynb",
          OLD / "historical-inference.py", OLD / "discrepancies.json"]
before = {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}
write("source-hashes.json", before)

# Search all reachable refs and historical paths, preserving the checked boundary.
refs = command("git", "for-each-ref", "--format=%(refname)")
all_objects = command("git", "rev-list", "--all", "--objects")
matched = []
for line in all_objects:
    fields = line.split(" ", 1)
    if len(fields) != 2:
        continue
    oid, path = fields
    if not any(term in path.lower() for term in
               ("rq2_", "priority_robustness", "candidate_v4")):
        continue
    kind = command("git", "cat-file", "-t", oid)[0]
    matched.append({"git_oid": oid, "path": path, "type": kind,
                    "bytes": int(command("git", "cat-file", "-s", oid)[0])})
history_paths = sorted(set(command("git", "log", "--all", "--format=",
                                  "--name-only", "--", "*rq2*", "*RQ2*",
                                  "*candidate_v4*")) - {""})
notebook_audit = []
for path in [SOURCE / "RQ2_Priority_Robustness_Colab.ipynb",
             ROOT / "thucnghiem/results/RQ2_Priority_Robustness_Colab.ipynb"]:
    book = json.loads(path.read_text())
    cells = []
    for index, cell in enumerate(book["cells"]):
        code = "".join(cell.get("source", []))
        if cell.get("outputs") or "float_format" in code:
            cells.append({"cell_zero_based": index,
                          "execution_count": cell.get("execution_count"),
                          "export_lines": [s for s in code.splitlines()
                                           if "to_csv" in s or "paired_comparison(" in s],
                          "outputs": [{"type": o.get("output_type"),
                                       "mime_types": list(o.get("data", {})),
                                       "text_characters": len("".join(o.get("text", [])))}
                                      for o in cell.get("outputs", [])]})
    notebook_audit.append({"path": str(path.relative_to(ROOT)), "cells": cells,
                           "full_precision_per_seed_array_found": False,
                           "observed_display": "summary head only; plot and stream receipts"})
write("recovery-search.json", {"head": command("git", "rev-parse", "HEAD")[0],
      "refs": refs, "historical_paths": history_paths, "matched_objects": matched,
      "notebooks": notebook_audit,
      "result": "NO_FULL_PRECISION_PER_SEED_ARTIFACT_FOUND_WITHIN_SEARCH_BOUNDARY",
      "limits": "Local reachable Git objects and two executed notebooks; no claim about inaccessible drives or Colab RAM."})

spec = importlib.util.spec_from_file_location("locked", OLD / "historical-inference.py")
locked = importlib.util.module_from_spec(spec)
spec.loader.exec_module(locked)
alignment = pd.read_csv(SOURCE / "rq2_rank_alignment_test.csv")
paired = pd.read_csv(SOURCE / "rq2_paired_comparisons.csv")
checks = []
families = []
rank_audits = []
for comparator, group in paired[paired.section == "alignment"].groupby("comparator"):
    candidate = alignment[alignment.method == "duplicate_aware_robust"].set_index("seed").sort_index()
    other = alignment[alignment.method == comparator].set_index("seed").sort_index()
    assert list(candidate.index) == list(other.index) == list(range(3000, 3040))
    results = {}
    saved_raw = {}
    for _, row in group.iterrows():
        results[row.metric] = locked.paired_comparison(
            candidate[row.metric], other[row.metric], direction=row.direction,
            denominator={"paired_test_seeds": 40})
        saved_raw[row.metric] = float(row.raw_p_value)
    saved_holm = locked.holm_adjust(saved_raw)
    replay = locked.apply_holm(results)
    for _, row in group.iterrows():
        for field in ("raw_p_value", "holm_adjusted_p_value"):
            saved = float(row[field])
            actual = float(replay[row.metric][field])
            match = bool(np.isclose(saved, actual, rtol=1e-7, atol=1e-12))
            checks.append({"comparator": comparator, "metric": row.metric,
                           "field": field, "saved": saved, "replay": actual,
                           "match": match, "status": "MATCH" if match else "OPEN_NEEDS_UNROUNDED_ARTIFACT",
                           "root_test": f"{comparator}:spearman",
                           "disposition": "Original and rounded-CSV replay retained separately; historical numbers unchanged."})
        families.append({"comparator": comparator, "metric": row.metric,
                         "saved_raw": saved_raw[row.metric],
                         "Holm_from_saved_raw": saved_holm[row.metric],
                         "Holm_saved": float(row.holm_adjusted_p_value),
                         "match": bool(np.isclose(saved_holm[row.metric], row.holm_adjusted_p_value,
                                                  rtol=1e-7, atol=1e-12))})
    values = candidate.spearman.to_numpy() - other.spearman.to_numpy()
    _, counts = np.unique(np.abs(values[values != 0]), return_counts=True)
    saved_row = group[group.metric == "spearman"].iloc[0]
    # This second serialization is sensitivity analysis, never recovered data.
    coarser_a = np.array([float(format(x, ".9g")) for x in candidate.spearman])
    coarser_b = np.array([float(format(x, ".9g")) for x in other.spearman])
    coarse = wilcoxon(coarser_a - coarser_b, zero_method="wilcox", alternative="two-sided", method="auto")
    rank_audits.append({"comparator": comparator, "n": len(values),
                       "saved_W": float(saved_row.wilcoxon_statistic),
                       "replay_W": results["spearman"]["wilcoxon_statistic"],
                       "saved_p": float(saved_row.raw_p_value),
                       "replay_p": results["spearman"]["raw_p_value"],
                       "n_zero_differences": int(sum(values == 0)),
                       "n_tied_abs_groups": int(sum(counts > 1)),
                       "abs_tie_sizes": sorted([int(n) for n in counts if n > 1]),
                       "auto_branch_for_current_values": "exact" if len(counts) == len(values) else "asymptotic",
                       "nine_significant_digits_sensitivity_only": {"W": float(coarse.statistic),
                                                                      "p": float(coarse.pvalue)},
                       "original_unrounded_ranks_available": False})

discrepancies = [c for c in checks if not c["match"]]
old = json.loads((OLD / "discrepancies.json").read_text())
assert len(discrepancies) == len(old) == 8
assert len([c for c in discrepancies if c["field"] == "raw_p_value"]) == 3
assert len([c for c in discrepancies if c["field"] == "holm_adjusted_p_value"]) == 5
assert all(c["match"] for c in families)
assert before == {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}
write("comparison-checks.json", checks)
write("holm-lineage.json", families)
write("rank-diagnostics.json", rank_audits)
with (OUT / "disposition.csv").open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(discrepancies[0]))
    writer.writeheader()
    writer.writerows(discrepancies)
write("validation.json", {"verification_status": "ANALYZED_NOT_RECONCILED",
      "environment": {p: version(p) for p in ("numpy", "pandas", "scipy")},
      "python_executable": sys.executable, "alignment_p_or_Holm_checks": len(checks),
      "matching": len(checks) - len(discrepancies), "unresolved": len(discrepancies),
      "root_raw_p_discrepancies": 3, "dependent_Holm_discrepancies": 5,
      "saved_Holm_internal_consistency": f"{sum(c['match'] for c in families)}/{len(families)}",
      "original_input_hashes_preserved": True,
      "new_ranking_or_generator_runs": 0,
      "tolerance": {"rtol": 1e-7, "atol": 1e-12},
      "decision": "OPEN: original unrounded arrays or saved rank vectors needed; sensitivity is not provenance."})
print("30 alignment p/Holm fields: 22 match, 8 remain OPEN (3 raw p + 5 dependent Holm).")
print("15/15 saved Holm fields consistent with their saved raw p; original hashes preserved.")
