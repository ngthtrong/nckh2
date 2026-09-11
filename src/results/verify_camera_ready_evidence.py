"""Fail-closed checks for camera-ready evidence and manuscript quotations."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import subprocess
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "src" / "results"
STRESS = RESULTS / "rq1_results"
RQ1_SOURCE_COMMIT = "6ac75c202d04934deb46d84486132e54d42d735f"
RQ1_DATA_TREE = "5bb8f9e5f1bb1c4deec8f0db1351e27d1bf30333"
RQ1_NOTEBOOK_SHA256 = "13a586af7ac5331dd1afe354b9e5c9a46b90e0ff2f6ac6f71dbdc3badd6ca7ef"
RQ1_CONFIG_SHA256 = "e3c9f1ad333575862126315595835f01a7b660ac59c240ed0e282f653fb265f6"
EXPECTED_PROTOCOL_SHA256 = "8618feb9e58683dc33392fffb5a977777108ca76dd5828f145a2a4ca05dc7245"
EXPECTED_ZIP_SHA256 = "d53624bbb3e681504ce9691a77b93610559183187bfe731a3f7fd10de6e034c2"
TOLERANCE = 1e-10


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def git_bytes(commit: str, relative_path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{relative_path}"], cwd=ROOT)


def git_blob_sha256(commit: str, relative_path: str) -> str:
    return hashlib.sha256(git_bytes(commit, relative_path)).hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def close(actual: float, expected: float, message: object) -> None:
    assert math.isclose(actual, expected, rel_tol=0.0, abs_tol=TOLERANCE), (
        message,
        actual,
        expected,
    )


def verify_hash_manifest(relative_path: str) -> None:
    manifest_path = RESULTS / relative_path
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, expected in manifest.items():
        actual = sha256(manifest_path.parent / name)
        assert actual == expected, f"{name}: {actual} != {expected}"


def verify_base_artifacts() -> dict[str, object]:
    """Verify the submitted RQ1 benchmark and existing RQ2/RQ3 evidence."""
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
    rq1_snapshot_files = {
        "src/results/Benchmark_Cij_Baselines_Colab.ipynb": RQ1_NOTEBOOK_SHA256,
        "src/results/cij_baseline_benchmark_results/selected_configs.json": RQ1_CONFIG_SHA256,
    }
    for relative_path, expected in rq1_snapshot_files.items():
        assert git_blob_sha256(RQ1_SOURCE_COMMIT, relative_path) == expected
        assert sha256(ROOT / relative_path) == expected

    for name in ("benchmark_summary.csv", "benchmark_test_40runs.csv", "paired_comparisons.csv"):
        relative_path = f"src/results/cij_baseline_benchmark_results/{name}"
        assert sha256(ROOT / relative_path) == git_blob_sha256(RQ1_SOURCE_COMMIT, relative_path)

    rq1_test_rows = read_rows(
        RESULTS / "cij_baseline_benchmark_results/benchmark_test_40runs.csv"
    )
    assert len(rq1_test_rows) == 400
    assert len({row["run_id"] for row in rq1_test_rows}) == 40
    methods = {row["method"] for row in rq1_test_rows}
    assert len(methods) == 10
    assert all(sum(row["method"] == method for row in rq1_test_rows) == 40 for method in methods)

    rq2_rows = read_rows(RESULTS / "rq2_results/rq2_robustness_test.csv")
    assert len({row["scenario"] for row in rq2_rows}) == 11
    rq3_rows = read_rows(RESULTS / "rq3_results/rq3_dispatch_test.csv")
    sensitivity_rows = read_rows(RESULTS / "rq2_results/rq2_parameter_sensitivity_test.csv")
    assert len(sensitivity_rows) == 840
    assert len({row["seed"] for row in sensitivity_rows}) == 40

    return {
        "rq1_test_rows": rq1_test_rows,
        "rq2_rows": rq2_rows,
        "rq3_rows": rq3_rows,
    }


def csv_value_matches(value: object, csv_value: str) -> bool:
    if value is None:
        return csv_value == ""
    if isinstance(value, bool):
        return csv_value == str(value)
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return csv_value == ""
        return math.isclose(float(value), float(csv_value), rel_tol=0.0, abs_tol=1e-12)
    return str(value) == csv_value


def verify_executed_notebook() -> dict[str, object]:
    notebook_path = RESULTS / "RQ1_Reviewer_Stress_Colab_After_Run.ipynb"
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    outputs: list[str] = []
    errors: list[dict[str, object]] = []
    executed_cells = 0
    for cell in notebook["cells"]:
        if cell.get("cell_type") != "code":
            continue
        if cell.get("execution_count") is not None:
            executed_cells += 1
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                errors.append(output)
            outputs.append("".join(output.get("text", [])))
    output_text = "\n".join(outputs)
    required = (
        "PASS source commit and pinned environment",
        "PASS data tree",
        "PASS all seven deterministic transformation contracts",
        "PASS formula branches and fixed prediction functions",
        "PASS smoke: 35 fits",
        "PASS full batch: 1400 fits",
        "PASS aggregation: 1400 fit rows, 300 paired effect rows",
        f"ZIP SHA-256: {EXPECTED_ZIP_SHA256}",
    )
    assert not errors, errors
    assert executed_cells >= 9
    for marker in required:
        assert marker in output_text, marker
    assert "Python 3.13.15" in output_text
    return {"executed_cells": executed_cells, "zip_sha256_from_output": EXPECTED_ZIP_SHA256}


def verify_rq1_stress_artifact(base: dict[str, object]) -> dict[str, object]:
    """Verify returned RQ1 stress artifacts, including exact bootstrap replay."""
    try:
        import numpy as np
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "RQ1 stress verification requires NumPy 2.5.1 in an isolated environment"
        ) from error
    assert np.__version__ == "2.5.1", np.__version__

    manifest = json.loads((STRESS / "manifest.json").read_text(encoding="utf-8"))
    protocol = json.loads((STRESS / "protocol.json").read_text(encoding="utf-8"))
    selected_used = json.loads((STRESS / "selected_configs.used.json").read_text(encoding="utf-8"))

    assert canonical_sha256(protocol) == EXPECTED_PROTOCOL_SHA256
    assert manifest["protocol"] == protocol
    assert manifest["protocol_sha256"] == EXPECTED_PROTOCOL_SHA256
    assert manifest["checkpoint_count"] == 280
    assert manifest["fit_rows"] == 1400
    assert manifest["python_version"].startswith("3.13.15 ")
    assert "python_version" not in protocol
    assert manifest["package_versions"]["numpy"] == "2.5.1"
    assert protocol["source_commit"] == RQ1_SOURCE_COMMIT
    assert protocol["data_tree"] == RQ1_DATA_TREE
    assert protocol["source_notebook_sha256"] == RQ1_NOTEBOOK_SHA256
    assert protocol["selected_config_sha256"] == RQ1_CONFIG_SHA256
    assert protocol["no_retuning"] is True
    assert protocol["prediction_before_truth"] is True

    actual_artifact_files = {
        str(path.relative_to(STRESS))
        for path in STRESS.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    assert len(manifest["artifacts"]) == 288
    assert set(manifest["artifacts"]) == actual_artifact_files
    for relative_path, expected in manifest["artifacts"].items():
        assert sha256(STRESS / relative_path) == expected, relative_path

    failure_paths = list(STRESS.rglob("failures.jsonl"))
    assert all(not path.read_text(encoding="utf-8").strip() for path in failure_paths)

    required_names = ("algorithm_input.json", "ground_truth.json", "run_manifest.json")
    inventory = []
    source_event_ids: dict[str, list[str]] = {}
    for run_id in protocol["test_runs"]:
        for name in required_names:
            relative_path = f"src/data/gold/{run_id}/{name}"
            current = ROOT / relative_path
            assert current.read_bytes() == git_bytes(RQ1_SOURCE_COMMIT, relative_path)
            inventory.append({"path": relative_path, "sha256": sha256(current)})
        source_payload = json.loads(
            (ROOT / f"src/data/gold/{run_id}/algorithm_input.json").read_text(encoding="utf-8")
        )
        source_event_ids[run_id] = [str(row["event_id"]) for row in source_payload["reports"]]
    assert canonical_sha256(inventory) == protocol["dataset_inventory_sha256"]

    config_path = RESULTS / "cij_baseline_benchmark_results/selected_configs.json"
    all_selected = json.loads(config_path.read_text(encoding="utf-8"))["selected"]
    expected_selected = {method: all_selected[method] for method in protocol["methods"]}
    assert selected_used == {"sha256": RQ1_CONFIG_SHA256, "selected": expected_selected}
    assert protocol["selected_configs"] == expected_selected

    checkpoints = []
    for path in sorted((STRESS / "checkpoints").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["protocol_sha256"] == EXPECTED_PROTOCOL_SHA256
        assert payload["source_commit"] == RQ1_SOURCE_COMMIT
        assert payload["data_tree"] == RQ1_DATA_TREE
        assert path.stem == f'{payload["run_id"]}__{payload["scenario"]}'
        checkpoints.append(payload)
    assert len(checkpoints) == 280
    expected_checkpoints = {
        (run_id, scenario)
        for run_id in protocol["test_runs"]
        for scenario in protocol["scenarios"]
    }
    assert {(item["run_id"], item["scenario"]) for item in checkpoints} == expected_checkpoints

    per_run_rows = read_rows(STRESS / "aggregate/rq1_stress_per_run.csv")
    expected_tuples = {
        (run_id, scenario, method)
        for run_id in protocol["test_runs"]
        for scenario in protocol["scenarios"]
        for method in protocol["methods"]
    }
    row_index = {(row["run_id"], row["scenario"], row["method"]): row for row in per_run_rows}
    assert len(per_run_rows) == len(row_index) == 1400
    assert set(row_index) == expected_tuples
    for checkpoint in checkpoints:
        assert len(checkpoint["rows"]) == 5
        for row in checkpoint["rows"]:
            csv_row = row_index[(row["run_id"], row["scenario"], row["method"])]
            assert set(row) == set(csv_row)
            for key, value in row.items():
                assert csv_value_matches(value, csv_row[key]), (
                    row["run_id"],
                    row["scenario"],
                    row["method"],
                    key,
                )

    benchmark_index = {
        (row["run_id"], row["method"]): row for row in base["rq1_test_rows"]
    }
    for method in protocol["methods"]:
        for run_id in protocol["test_runs"]:
            stress_row = row_index[(run_id, "baseline", method)]
            benchmark_row = benchmark_index[(run_id, method)]
            close(float(stress_row["ari_original"]), float(benchmark_row["ari"]), (run_id, method, "ARI"))
            close(
                float(stress_row["pair_f1_original"]),
                float(benchmark_row["pair_f1"]),
                (run_id, method, "pair F1"),
            )

    aggregate_mapping = read_rows(STRESS / "aggregate/rq1_stress_duplication_mapping.csv")
    checkpoint_mapping = [row for item in checkpoints for row in item["duplication_mapping"]]
    assert len(aggregate_mapping) == len(checkpoint_mapping) == 92617
    mapping_fields = tuple(aggregate_mapping[0])
    serialized_mapping = [tuple(str(row[field]) for field in mapping_fields) for row in checkpoint_mapping]
    assert Counter(serialized_mapping) == Counter(
        tuple(row[field] for field in mapping_fields) for row in aggregate_mapping
    )
    for item in checkpoints:
        scenario = item["scenario"]
        mapping = item["duplication_mapping"]
        if scenario not in ("exact_transport_copy_2x", "exact_transport_copy_5x"):
            assert not mapping
            continue
        copies = int(protocol["scenarios"][scenario]["copies"])
        sources = source_event_ids[item["run_id"]]
        assert len(mapping) == len(sources) * copies
        assert len({row["perturbed_event_id"] for row in mapping}) == len(mapping)
        assert Counter(row["source_event_id"] for row in mapping) == Counter(
            {event_id: copies for event_id in sources}
        )
        assert {int(row["copy_index"]) for row in mapping} == set(range(copies))
        assert all(row["evaluator_only"] is True for row in mapping)
        for row in mapping:
            index = int(row["copy_index"])
            expected_id = (
                row["source_event_id"]
                if index == 0
                else f'{row["source_event_id"]}__transport_copy_{index + 1}'
            )
            assert row["perturbed_event_id"] == expected_id

    metric_columns = (
        "ari_original",
        "pair_f1_original",
        "ari_all",
        "pair_f1_all",
        "fake_absorption_rate_all",
        "fake_rejection_rate_all",
        "genuine_rejection_rate_all",
        "false_destination_rate_all",
        "retained_edge_fraction",
        "mean_degree",
    )
    summary_rows = read_rows(STRESS / "aggregate/rq1_stress_summary.csv")
    assert len(summary_rows) == 35
    for summary in summary_rows:
        selected = [
            row
            for row in per_run_rows
            if row["scenario"] == summary["scenario"] and row["method"] == summary["method"]
        ]
        assert len(selected) == 40
        for metric in metric_columns:
            values = [float(row[metric]) for row in selected if row[metric] != ""]
            assert int(summary[f"{metric}_count"]) == len(values)
            if not values:
                assert summary[f"{metric}_mean"] == summary[f"{metric}_std"] == ""
                continue
            close(
                statistics.fmean(values),
                float(summary[f"{metric}_mean"]),
                (summary["scenario"], summary["method"], metric, "mean"),
            )
            close(
                statistics.stdev(values),
                float(summary[f"{metric}_std"]),
                (summary["scenario"], summary["method"], metric, "std"),
            )

    effect_rows = read_rows(STRESS / "aggregate/rq1_stress_paired_effects.csv")
    assert len(effect_rows) == 300
    for effect in effect_rows:
        values = np.array(
            [
                float(row_index[(run_id, effect["scenario"], effect["method"])][effect["metric"]])
                - float(row_index[(run_id, "baseline", effect["method"])][effect["metric"]])
                for run_id in sorted(protocol["test_runs"])
                if row_index[(run_id, effect["scenario"], effect["method"])][effect["metric"]] != ""
            ],
            dtype=float,
        )
        assert int(effect["paired_runs"]) == len(values)
        assert int(effect["bootstrap_resamples"]) == protocol["bootstrap_resamples"] == 5000
        if not len(values):
            for field in ("mean_stress_minus_baseline", "bootstrap_ci95_low", "bootstrap_ci95_high"):
                assert effect[field] == ""
            continue
        seed_token = hashlib.sha256(
            f'{protocol["bootstrap_random_seed"]}|{effect["method"]}|{effect["scenario"]}|{effect["metric"]}'.encode()
        ).digest()
        rng = np.random.default_rng(int.from_bytes(seed_token[:8], "big"))
        bootstrap_means = np.mean(
            rng.choice(values, size=(protocol["bootstrap_resamples"], len(values)), replace=True),
            axis=1,
        )
        expected = (
            float(np.mean(values)),
            float(np.quantile(bootstrap_means, 0.025)),
            float(np.quantile(bootstrap_means, 0.975)),
        )
        actual = tuple(
            float(effect[field])
            for field in ("mean_stress_minus_baseline", "bootstrap_ci95_low", "bootstrap_ci95_high")
        )
        for actual_value, expected_value in zip(actual, expected):
            close(
                actual_value,
                expected_value,
                (effect["method"], effect["scenario"], effect["metric"]),
            )

    notebook = verify_executed_notebook()
    return {
        "manifest_files": len(manifest["artifacts"]),
        "checkpoints": len(checkpoints),
        "fit_rows": len(per_run_rows),
        "paired_effect_rows": len(effect_rows),
        "mapping_rows": len(aggregate_mapping),
        "audit_numpy": np.__version__,
        "colab_python": manifest["python_version"],
        **notebook,
    }


def manuscript_number(value: str) -> str:
    return value.lstrip("0") if value.startswith("0.") else value.replace("-0.", "-.")


def verify_manuscript(base: dict[str, object]) -> None:
    paper = (ROOT / "paper" / "main.tex").read_text(encoding="utf-8")
    rq1_summary_rows = read_rows(RESULTS / "cij_baseline_benchmark_results/benchmark_summary.csv")
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
        assert values == rq1_expected[row["method"]]
        assert all(value in paper for value in values)

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
    rq2_metrics = ("priority_drift_abs_normalized", "mean_rank_drift_normalized", "top_k_churn")
    rq2_rows = base["rq2_rows"]
    assert {row["scenario"] for row in rq2_rows} == set(rq2_expected)
    for scenario, expected in rq2_expected.items():
        values = []
        count = None
        for estimator in ("duplicate_aware_robust", "legacy_raw"):
            selected = [row for row in rq2_rows if row["scenario"] == scenario and row["estimator"] == estimator]
            count = len(selected) if count is None else count
            assert len(selected) == count
            for metric in rq2_metrics:
                values.append(f"{statistics.mean(float(row[metric]) for row in selected):.4f}".lstrip("0"))
        reordered = (values[0], values[3], values[1], values[4], values[2], values[5])
        assert (count, *reordered) == expected
        assert all(value in paper for value in reordered)

    rq3_expected = {
        "lean_hue": ("691.37", "653.79", "585.55", ".9188", ".9203", ".8203"),
        "nominal_dual_depot": ("315.01", "303.16", "230.00", ".8453", ".8594", ".6313"),
        "regional_surge": ("113.53", "119.93", "94.71", ".6672", ".7078", ".4484"),
    }
    rq3_rows = base["rq3_rows"]
    assert {row["resource_scenario"] for row in rq3_rows} == set(rq3_expected)
    for scenario, expected in rq3_expected.items():
        values = []
        for metric in ("latent_harm", "deadline_miss_rate"):
            for policy in ("revised_priority", "legacy_priority", "nearest_first"):
                selected = [
                    row
                    for row in rq3_rows
                    if row["resource_scenario"] == scenario
                    and row["partition"] == "product_cij"
                    and row["policy"] == policy
                ]
                assert len(selected) == 40
                mean = sum(Decimal(row[metric]) for row in selected) / Decimal(len(selected))
                quantum = Decimal(".01") if metric == "latent_harm" else Decimal(".0001")
                formatted = str(mean.quantize(quantum, rounding=ROUND_HALF_UP))
                values.append(formatted if metric == "latent_harm" else formatted.lstrip("0"))
        assert tuple(values) == expected
        assert all(value in paper for value in values)

    stress_summary = {
        (row["scenario"], row["method"]): row
        for row in read_rows(STRESS / "aggregate/rq1_stress_summary.csv")
    }
    paper_rows = {
        "baseline": "Control",
        "gps_noise_100m": "GPS noise, 100 m",
        "gps_noise_300m": "GPS noise, 300 m",
        "time_noise_15min": "Time noise, 15 min",
        "time_noise_60min": "Time noise, 60 min",
        "exact_transport_copy_2x": r"Exact copies, $2\times$",
        "exact_transport_copy_5x": r"Exact copies, $5\times$",
    }
    methods = (
        "product_cij_louvain",
        "additive_cij_louvain",
        "additive_cij_louvain_matched_density",
        "product_cij_leiden",
        "geo_time_dbscan",
    )
    for scenario, label in paper_rows.items():
        values = [
            manuscript_number(
                f'{float(stress_summary[(scenario, method)]["ari_original_mean"]):.4f}'
            )
            for method in methods
        ]
        expected_row = f'{label} & ' + " & ".join(values) + r"\\"
        assert expected_row in paper, expected_row
    for text in ("-.6108", "[-.6318,-.5881]"):
        assert text in paper, text
    normalized_paper = " ".join(paper.split())
    assert "score-level invariance does not imply clustering invariance" in normalized_paper


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-only",
        action="store_true",
        help="verify source artifacts and returned RQ1 stress results without reading manuscript quotations",
    )
    args = parser.parse_args()

    base = verify_base_artifacts()
    stress = verify_rq1_stress_artifact(base)
    print("PASS RQ2 and RQ3 manifests and RQ3 40-seed provenance")
    print("PASS submitted RQ1 snapshot, data tree, configurations, and 400 benchmark rows")
    print(
        "PASS returned RQ1 stress artifact: "
        f'{stress["manifest_files"]} hashes, {stress["checkpoints"]} checkpoints, '
        f'{stress["fit_rows"]} fits, {stress["mapping_rows"]} mappings'
    )
    print(
        "PASS exact recomputation: 35 summaries and "
        f'{stress["paired_effect_rows"]} paired bootstrap rows with NumPy {stress["audit_numpy"]}'
    )
    print("PASS executed notebook provenance and completion markers")
    print(
        "OPEN provenance gate: original ZIP file is absent; compare it with",
        stress["zip_sha256_from_output"],
    )
    print(
        "RECORDED limitation: Colab used",
        stress["colab_python"],
        "but python_version was not protocol-hashed",
    )
    if not args.artifact_only:
        verify_manuscript(base)
        print("PASS manuscript quotations for RQ1 benchmark/stress, RQ2, and RQ3")


if __name__ == "__main__":
    main()
