"""Recompute the primary RQ3 inference unit at the seed level.

The dispatch simulator already exports three resource scenarios per seed.  This
script averages those scenarios within seed, then applies the locked paired
comparison and Holm procedures to the resulting 40 seed pairs.  The original
120-pair result is retained as a diagnostic input and is never overwritten.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata, wilcoxon


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
INPUT = OUT / "rq3_dispatch_test.csv"
METRIC_DIRECTIONS = {
    "latent_harm": "lower",
    "deadline_miss_rate": "lower",
    "mean_arrival_min": "lower",
    "max_arrival_min": "lower",
    "cvar90_arrival_min": "lower",
    "unique_population_reached_by_deadline_rate": "higher",
    "total_fleet_workload_min": "lower",
    "boat_workload_cv": "lower",
    "arrival_equity_gap_min": "lower",
    "split_trips": "lower",
    "merge_caused_misses": "lower",
    "fake_dispatches": "lower",
    "duplicate_dispatches": "lower",
    "unserved_genuine_incidents": "lower",
}


def bootstrap_mean_ci(values: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(20260729)
    indices = rng.integers(0, values.size, size=(5000, values.size))
    means = values[indices].mean(axis=1)
    return (float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975)))


def rank_biserial(values: np.ndarray) -> float:
    values = values[values != 0]
    if values.size == 0:
        return 0.0
    ranks = rankdata(np.abs(values), method="average")
    positive = float(ranks[values > 0].sum())
    negative = float(ranks[values < 0].sum())
    return (positive - negative) / (positive + negative)


def paired(candidate: np.ndarray, comparator: np.ndarray, direction: str) -> dict:
    raw = candidate - comparator
    improvement = raw if direction == "higher" else -raw
    if np.all(improvement == 0):
        statistic, raw_p = 0.0, 1.0
    else:
        result = wilcoxon(
            improvement,
            zero_method="wilcox",
            alternative="two-sided",
            method="auto",
        )
        statistic, raw_p = float(result.statistic), float(result.pvalue)
    sd = float(np.std(improvement, ddof=1))
    standardized = float(np.mean(improvement) / sd) if sd else (
        0.0 if np.mean(improvement) == 0 else None
    )
    return {
        "direction": direction,
        "mean": float(np.mean(improvement)),
        "standard_deviation": sd,
        "median": float(np.median(improvement)),
        "paired_confidence_interval": json.dumps(bootstrap_mean_ci(improvement)),
        "mean_difference_candidate_minus_comparator": float(np.mean(raw)),
        "raw_p_value": raw_p,
        "holm_adjusted_p_value": None,
        "wilcoxon_statistic": statistic,
        "n_seed_pairs": int(improvement.size),
        "n_candidate_better": int(np.count_nonzero(improvement > 0)),
        "n_comparator_better": int(np.count_nonzero(improvement < 0)),
        "n_ties": int(np.count_nonzero(improvement == 0)),
        "effect_size.paired_standardized_mean": standardized,
        "effect_size.matched_pairs_rank_biserial": rank_biserial(improvement),
        "effect_size.orientation": "positive means candidate is better",
        "denominator.paired_seed_pairs": int(improvement.size),
    }


def holm(rows: dict[str, dict]) -> dict[str, dict]:
    ordered = sorted(rows, key=lambda key: (rows[key]["raw_p_value"], key))
    running = 0.0
    family_size = len(ordered)
    output = {key: dict(value) for key, value in rows.items()}
    for index, key in enumerate(ordered):
        running = max(running, min(1.0, (family_size - index) * rows[key]["raw_p_value"]))
        output[key]["holm_adjusted_p_value"] = running
    return output


def main() -> None:
    dispatch = pd.read_csv(INPUT)
    assert dispatch.seed.nunique() == 40
    assert dispatch.resource_scenario.nunique() == 3
    assert dispatch.groupby(["seed", "partition", "policy"]).size().eq(3).all()

    numeric = list(METRIC_DIRECTIONS)
    seed_level = (
        dispatch.groupby(["seed", "stage", "partition", "policy"], as_index=False)[numeric]
        .mean()
    )
    metadata = dispatch[[
        "generator_version", "seed_split", "candidate_bundle_sha256",
        "package_versions", "config_identity", "metric_direction",
    ]].drop_duplicates()
    assert len(metadata) == 1
    for column in metadata.columns:
        seed_level[column] = metadata.iloc[0][column]
    runtime_versions = {
        name: importlib.metadata.version(name)
        for name in ("numpy", "pandas", "scipy")
    }
    seed_level["reanalysis_package_versions"] = json.dumps(runtime_versions, sort_keys=True)
    seed_level.to_csv(OUT / "rq3_dispatch_test_seed.csv", index=False, float_format="%.10g")

    comparisons: list[dict] = []

    def compare_policy(candidate: str, comparator: str, partition: str) -> None:
        subset = seed_level[seed_level.partition == partition]
        left = subset[subset.policy == candidate].set_index("seed")
        right = subset[subset.policy == comparator].set_index("seed")
        family = {
            metric: paired(left[metric].to_numpy(), right[metric].to_numpy(), direction)
            for metric, direction in METRIC_DIRECTIONS.items()
        }
        for metric, result in holm(family).items():
            comparisons.append({
                "dimension": "policy",
                "candidate": candidate,
                "comparator": comparator,
                "fixed": json.dumps({"partition": partition}, sort_keys=True),
                "metric": metric,
                **result,
            })

    def compare_partition(candidate: str, comparator: str, policy: str) -> None:
        subset = seed_level[seed_level.policy == policy]
        left = subset[subset.partition == candidate].set_index("seed")
        right = subset[subset.partition == comparator].set_index("seed")
        family = {
            metric: paired(left[metric].to_numpy(), right[metric].to_numpy(), direction)
            for metric, direction in METRIC_DIRECTIONS.items()
        }
        for metric, result in holm(family).items():
            comparisons.append({
                "dimension": "partition",
                "candidate": candidate,
                "comparator": comparator,
                "fixed": json.dumps({"policy": policy}, sort_keys=True),
                "metric": metric,
                **result,
            })

    for partition in sorted(seed_level.partition.unique()):
        for comparator in ("legacy_priority", "nearest_first", "first_report_fifo"):
            compare_policy("revised_priority", comparator, partition)
    for policy in sorted(seed_level.policy.unique()):
        compare_partition("product_cij", "oracle", policy)
        compare_partition("product_cij", "additive_cij_matched_density", policy)

    result = pd.DataFrame(comparisons)
    for column in metadata.columns:
        result[column] = metadata.iloc[0][column]
    result["reanalysis_package_versions"] = json.dumps(runtime_versions, sort_keys=True)
    result.to_csv(OUT / "rq3_paired_comparisons_seed.csv", index=False, float_format="%.10g")

    hashes = {}
    for path in (OUT / "rq3_dispatch_test_seed.csv", OUT / "rq3_paired_comparisons_seed.csv"):
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    provenance = {
        "input": INPUT.name,
        "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "unit": "40 seed-level pairs; three resource scenarios averaged within seed",
        "diagnostic_unit": "120 seed-resource-scenario pairs in the original CSV",
        "bootstrap_resamples": 5000,
        "bootstrap_seed": 20260729,
        "holm_family_size": 14,
        "source_commit": "a6be3e988dad1aa442c8c8e158c2bba96b2b7fb9",
        "reanalysis_package_versions": runtime_versions,
        "reanalysis_note": "Run with the repository environment before camera-ready; the input artifact metadata records the original Candidate-4.1 execution environment.",
        "output_sha256": hashes,
    }
    (OUT / "rq3_seed_level_reanalysis_provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n"
    )
    assert len(result) == 21 * 14
    assert result.n_seed_pairs.eq(40).all()
    print(result.head(3).to_string(index=False))
    print("Wrote", OUT / "rq3_dispatch_test_seed.csv")
    print("Wrote", OUT / "rq3_paired_comparisons_seed.csv")


if __name__ == "__main__":
    main()
