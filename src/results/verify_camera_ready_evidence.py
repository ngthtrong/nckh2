"""Fail-closed checks for evidence quoted in the camera-ready manuscript."""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
import subprocess
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "src" / "results"
PAPER = (ROOT / "paper" / "main.tex").read_text(encoding="utf-8")
RQ1_SOURCE_COMMIT = "6ac75c202d04934deb46d84486132e54d42d735f"
RQ1_DATA_TREE = "5bb8f9e5f1bb1c4deec8f0db1351e27d1bf30333"
RQ1_NOTEBOOK_SHA256 = "13a586af7ac5331dd1afe354b9e5c9a46b90e0ff2f6ac6f71dbdc3badd6ca7ef"
RQ1_CONFIG_SHA256 = "e3c9f1ad333575862126315595835f01a7b660ac59c240ed0e282f653fb265f6"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha256(commit: str, relative_path: str) -> str:
    payload = subprocess.check_output(
        ["git", "show", f"{commit}:{relative_path}"], cwd=ROOT
    )
    return hashlib.sha256(payload).hexdigest()


def verify_hash_manifest(relative_path: str) -> None:
    manifest_path = RESULTS / relative_path
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, expected in manifest.items():
        actual = sha256(manifest_path.parent / name)
        assert actual == expected, f"{name}: {actual} != {expected}"


def read_rows(relative_path: str) -> list[dict[str, str]]:
    with (RESULTS / relative_path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


verify_hash_manifest("rq2_results/rq2_artifact_sha256.json")
verify_hash_manifest("rq3_results/rq3_artifact_sha256.json")

rq3_provenance_path = RESULTS / "rq3_results/rq3_seed_level_reanalysis_provenance.json"
rq3_provenance = json.loads(rq3_provenance_path.read_text(encoding="utf-8"))
rq3_dir = rq3_provenance_path.parent
assert sha256(rq3_dir / rq3_provenance["input"]) == rq3_provenance["input_sha256"]
for name, expected in rq3_provenance["output_sha256"].items():
    assert sha256(rq3_dir / name) == expected
assert rq3_provenance["unit"].startswith("40 seed-level pairs")

data_tree = subprocess.check_output(
    ["git", "rev-parse", f"{RQ1_SOURCE_COMMIT}:src/data"], cwd=ROOT, text=True
).strip()
assert data_tree == RQ1_DATA_TREE
assert subprocess.check_output(
    ["git", "rev-parse", "HEAD:src/data"], cwd=ROOT, text=True
).strip() == RQ1_DATA_TREE

rq1_snapshot_files = {
    "src/results/Benchmark_Cij_Baselines_Colab.ipynb": RQ1_NOTEBOOK_SHA256,
    "src/results/cij_baseline_benchmark_results/selected_configs.json": RQ1_CONFIG_SHA256,
}
for relative_path, expected in rq1_snapshot_files.items():
    assert git_blob_sha256(RQ1_SOURCE_COMMIT, relative_path) == expected
    assert sha256(ROOT / relative_path) == expected

rq1_result_names = (
    "benchmark_summary.csv",
    "benchmark_test_40runs.csv",
    "paired_comparisons.csv",
)
for name in rq1_result_names:
    relative_path = f"src/results/cij_baseline_benchmark_results/{name}"
    assert sha256(ROOT / relative_path) == git_blob_sha256(RQ1_SOURCE_COMMIT, relative_path)

rq1_test_rows = read_rows("cij_baseline_benchmark_results/benchmark_test_40runs.csv")
assert len(rq1_test_rows) == 400
assert len({row["run_id"] for row in rq1_test_rows}) == 40
methods = {row["method"] for row in rq1_test_rows}
assert len(methods) == 10
assert all(len([row for row in rq1_test_rows if row["method"] == method]) == 40 for method in methods)

rq1_summary_rows = read_rows("cij_baseline_benchmark_results/benchmark_summary.csv")
rq1_expected = {
    "additive_cij_louvain": (".9191", ".8995", ".9381", ".9247", ".3477"),
    "product_cij_leiden": (".9165", ".8979", ".9351", ".9223", ".3547"),
    "convex_cij_louvain": (".9135", ".8940", ".9320", ".9195", ".3547"),
    "product_cij_louvain": (".9072", ".8864", ".9271", ".9138", ".3585"),
    "additive_cij_louvain_matched_density": (".8973", ".8763", ".9175", ".9046", ".3743"),
    "coordinate_kmeans": (".8176", ".7976", ".8384", ".8292", ".2977"),
    "spatial_agglomerative": (".6235", ".5964", ".6494", ".6506", "4.1648"),
    "hdbscan_all": (".5205", ".4565", ".5811", ".5787", "1.2527"),
    "geo_time_dbscan": (".4978", ".4589", ".5366", ".5450", ".6244"),
    "dbscan_all": (".4741", ".4273", ".5201", ".5488", ".9340"),
}
assert {row["method"] for row in rq1_summary_rows} == set(rq1_expected)
rq1_columns = ("ari_mean", "ari_ci95_low", "ari_ci95_high", "pair_f1_mean", "mean_diameter_km")
for row in rq1_summary_rows:
    values = tuple(f"{float(row[column]):.4f}".lstrip("0") for column in rq1_columns)
    assert values == rq1_expected[row["method"]], (row["method"], values)
    for value in values:
        assert value in PAPER

rq2_rows = read_rows("rq2_results/rq2_robustness_test.csv")
rq2_expected = {
    "contradictory_F_E": (40, ".0484", ".0611", ".0171", ".0290", ".0450", ".1100"),
    "coordinated_high_confidence_campaign": (40, ".1688", ".0309", ".0175", ".0006", ".0350", ".0000"),
    "exact_duplicate_10x": (40, ".0000", ".0148", ".0000", ".0075", ".0000", ".0150"),
    "exact_duplicate_2x": (40, ".0000", ".0026", ".0000", ".0015", ".0000", ".0000"),
    "exact_duplicate_5x": (40, ".0000", ".0086", ".0000", ".0046", ".0000", ".0100"),
    "low_confidence_inflate_E": (40, ".0034", ".0012", ".0008", ".0006", ".0050", ".0000"),
    "low_confidence_inflate_F": (40, ".0026", ".0072", ".0000", ".0040", ".0000", ".0150"),
    "low_confidence_inflate_N": (40, ".0696", ".0140", ".0240", ".0071", ".0600", ".0150"),
    "low_confidence_inflate_V": (40, ".0758", ".0074", ".0263", ".0040", ".0500", ".0150"),
    "near_duplicate": (320, ".0016", ".0055", ".0004", ".0017", ".0006", ".0019"),
    "source_missingness_zero_imputation": (628, ".0063", ".0075", ".0019", ".0025", ".0029", ".0064"),
}
rq2_metrics = (
    "priority_drift_abs_normalized",
    "mean_rank_drift_normalized",
    "top_k_churn",
)
assert {row["scenario"] for row in rq2_rows} == set(rq2_expected)
for scenario, expected in rq2_expected.items():
    values = []
    count = None
    for estimator in ("duplicate_aware_robust", "legacy_raw"):
        selected = [row for row in rq2_rows if row["scenario"] == scenario and row["estimator"] == estimator]
        count = len(selected) if count is None else count
        assert len(selected) == count
        for metric in rq2_metrics:
            mean = statistics.mean(float(row[metric]) for row in selected)
            values.append(f"{mean:.4f}".lstrip("0"))
    # Reorder R/P, R/rank, R/churn into the manuscript's paired columns.
    reordered = (values[0], values[3], values[1], values[4], values[2], values[5])
    assert (count, *reordered) == expected, (scenario, (count, *reordered), expected)
    for value in reordered:
        assert value in PAPER

rq3_rows = read_rows("rq3_results/rq3_dispatch_test.csv")
rq3_expected = {
    "lean_hue": ("691.37", "653.79", "585.55", ".9188", ".9203", ".8203"),
    "nominal_dual_depot": ("315.01", "303.16", "230.00", ".8453", ".8594", ".6313"),
    "regional_surge": ("113.53", "119.93", "94.71", ".6672", ".7078", ".4484"),
}
assert {row["resource_scenario"] for row in rq3_rows} == set(rq3_expected)
for scenario, expected in rq3_expected.items():
    values = []
    for metric in ("latent_harm", "deadline_miss_rate"):
        for policy in ("revised_priority", "legacy_priority", "nearest_first"):
            selected = [
                row for row in rq3_rows
                if row["resource_scenario"] == scenario
                and row["partition"] == "product_cij"
                and row["policy"] == policy
            ]
            assert len(selected) == 40
            mean = sum(Decimal(row[metric]) for row in selected) / Decimal(len(selected))
            quantum = Decimal(".01") if metric == "latent_harm" else Decimal(".0001")
            formatted = str(mean.quantize(quantum, rounding=ROUND_HALF_UP))
            if metric != "latent_harm":
                formatted = formatted.lstrip("0")
            values.append(formatted)
    assert tuple(values) == expected, (scenario, values, expected)
    for value in values:
        assert value in PAPER

sensitivity_rows = read_rows("rq2_results/rq2_parameter_sensitivity_test.csv")
assert len(sensitivity_rows) == 840
assert len({row["seed"] for row in sensitivity_rows}) == 40

print("PASS RQ2 and RQ3 artifact SHA-256 manifests")
print("PASS RQ3 seed-level provenance and 40-seed unit")
print("PASS RQ1 source snapshot, data tree, configuration, and result files")
print("PASS 400-row RQ1 test grain and 10 headline summaries quoted in paper")
print("PASS 11 RQ2 scenario summaries quoted in paper")
print("PASS 3 RQ3 resource summaries quoted in paper")
print("PASS 840-row sensitivity artifact")
