from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path

import pytest

from demo.v2.external_benchmark import (
    DEFAULT_DATA_ROOT,
    DEFAULT_RUN_ROOT,
    DEFAULT_REPORTS,
    DEFAULT_SELECTION,
    DEFAULT_TRUTH,
    ExternalBenchmarkError,
    METHOD_ORDER,
    file_sha256,
    run_external_batch,
    load_external_dataset,
    load_external_run,
    run_external_benchmark,
)


def test_datav2_loader_uses_an_explicit_truth_isolated_adapter() -> None:
    dataset = load_external_dataset(DEFAULT_REPORTS, DEFAULT_TRUTH)

    assert dataset.dataset_id == "run_001"
    assert len(dataset.reports) == len(dataset.report_truth) == 316
    assert len({row.report_id for row in dataset.reports}) == 316
    assert {row.report_id for row in dataset.reports} == {
        row.report_id for row in dataset.report_truth
    }
    assert all(row.graph_eligible for row in dataset.reports)
    assert all(not hasattr(row, "gt_cluster") for row in dataset.reports)
    assert all(not hasattr(row, "is_fake") for row in dataset.reports)
    assert sum(row.incident_id is None for row in dataset.report_truth) == 60
    assert len(
        {row.incident_id for row in dataset.report_truth if row.incident_id is not None}
    ) == 16


def test_current_run_loader_audits_all_five_tables() -> None:
    dataset = load_external_run(DEFAULT_RUN_ROOT)

    assert dataset.input_mode == "algorithm_input"
    assert dataset.algorithm_payload_sha256
    assert dataset.observable_payload_sha256
    assert dataset.latent_payload_sha256
    assert dataset.manifest_payload_sha256
    assert len(dataset.latent_incidents) == 16
    assert dataset.run_manifest["generator_version"] == "3.0.0"


def test_datav2_loader_rejects_disagreement_in_exposed_oracle_fields(
    tmp_path: Path,
) -> None:
    observable_path = DEFAULT_RUN_ROOT / "observable_reports.json"
    observable = json.loads(observable_path.read_text(encoding="utf-8"))
    observable["reports"][0]["gt_cluster"] += 1
    changed = tmp_path / "observable_reports.json"
    changed.write_text(json.dumps(observable), encoding="utf-8")

    with pytest.raises(
        ExternalBenchmarkError,
        match="exposed evaluator fields disagree",
    ):
        load_external_dataset(changed, DEFAULT_TRUTH)


def test_run_loader_rejects_observable_rows_as_algorithm_input(tmp_path: Path) -> None:
    run_copy = tmp_path / "run_001"
    shutil.copytree(DEFAULT_RUN_ROOT, run_copy)
    run_copy.joinpath("algorithm_input.json").write_text(
        (DEFAULT_RUN_ROOT / "observable_reports.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with pytest.raises(ExternalBenchmarkError, match="algorithm_input.json must declare"):
        load_external_run(run_copy)


def test_external_benchmark_uses_frozen_configs_and_retains_adverse_results() -> None:
    report = run_external_benchmark(
        reports_path=DEFAULT_REPORTS,
        truth_path=DEFAULT_TRUTH,
        selection_path=DEFAULT_SELECTION,
        random_state=42,
    )

    assert report["status"] == "completed_descriptive_only"
    assert report["scope"]["calibration_or_tuning_performed"] is False
    assert report["scope"]["frozen_confirmation_modified"] is False
    assert report["duplicate_audit"]["declared_exact_rows"] == 11
    assert report["duplicate_audit"]["declared_exact_fingerprint_matches"] == 0
    assert report["duplicate_audit"]["declared_near_rows"] == 32
    assert report["duplicate_audit"]["declared_near_rows_matching_near_envelope"] == 31
    assert report["duplicate_audit"]["pairwise"]["true_positive"] >= 0

    expected = {
        "method.product_louvain": "config.product_louvain.097",
        "method.additive_louvain": "config.additive_louvain.084",
        "method.st_dbscan": "config.st_dbscan.056",
        "method.hdbscan_geo_time": "config.hdbscan.007",
    }
    for method_id, configuration_id in expected.items():
        row = report["clustering"][method_id]
        assert row["configuration_id"] == configuration_id
        assert 0.0 <= row["metrics"]["ari_linked"] <= 1.0
        assert row["metrics"]["noise_rejection"] == 0.0
        assert row["metrics"]["n_false_destinations"] == 3
        assert row["external_metrics"]["mixed_noise_reports"] == 0
        assert all(
            campaign["n_rejected"] == 0
            and campaign["n_operational_destinations"] == 1
            for campaign in row["external_metrics"]["campaigns"].values()
        )


def test_batch_runner_writes_and_resumes_immutable_checkpoints(tmp_path: Path, monkeypatch) -> None:
    data_root = tmp_path / "dataV2"
    (data_root / "gold").mkdir(parents=True)
    source = DEFAULT_DATA_ROOT / "gold" / "run_001"
    shutil.copytree(source, data_root / "gold" / "run_001")
    output_dir = tmp_path / "results"

    def fake_execute(dataset, *, selection_path, random_state, source_paths):
        metrics = {
            "ari_linked": 0.5,
            "false_destinations_per_100_reports": 1.0,
            "noise_rejection": 0.0,
            "review_items_per_100_reports": 2.0,
            "split_loss": 0.1,
            "merge_loss": 0.2,
            "max_diameter_m": 100.0,
            "singleton_rate": 0.3,
        }
        return {
            "schema_version": "v2.external-sanity-run.1",
            "status": "completed_descriptive_only",
            "inputs": {
                "dataset_id": dataset.dataset_id,
                "random_state": random_state,
                "selection_sha256": file_sha256(selection_path),
                "reports_sha256": dataset.algorithm_payload_sha256,
                "truth_sha256": file_sha256(source_paths['truth']),
                "observable_sha256": file_sha256(source_paths['observable']),
                "latent_sha256": file_sha256(source_paths['latent']),
                "manifest_sha256": file_sha256(source_paths['manifest']),
            },
            "clustering": {
                method: {
                    "metrics": dict(metrics),
                    "external_metrics": {"campaigns": {}},
                }
                for method in METHOD_ORDER
            },
            "duplicate_audit": {},
        }

    monkeypatch.setattr(
        "demo.v2.external_benchmark._execute_external_dataset", fake_execute
    )
    first = run_external_batch(
        data_root=data_root,
        output_dir=output_dir,
        expected_runs=1,
        selection_path=DEFAULT_SELECTION,
        resume=True,
    )
    assert first["status"] == "completed"
    assert (output_dir / "per_run" / "run_001.json").is_file()
    assert (output_dir / "batch_manifest.json").is_file()
    assert (output_dir / "aggregate_results.json").is_file()

    def fail_if_called(*args, **kwargs):
        raise AssertionError("resume should use the immutable cached result")

    monkeypatch.setattr(
        "demo.v2.external_benchmark._execute_external_dataset", fail_if_called
    )
    resumed = run_external_batch(
        data_root=data_root,
        output_dir=output_dir,
        expected_runs=1,
        selection_path=DEFAULT_SELECTION,
        resume=True,
    )
    assert resumed["status"] == "completed"

    algorithm_path = data_root / "gold" / "run_001" / "algorithm_input.json"
    algorithm_path.write_text(algorithm_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ExternalBenchmarkError, match="cached result provenance mismatch"):
        run_external_batch(
            data_root=data_root,
            output_dir=output_dir,
            expected_runs=1,
            selection_path=DEFAULT_SELECTION,
            resume=True,
        )


def test_colab_notebook_is_valid_and_explains_each_code_cell() -> None:
    notebook_path = Path(__file__).resolve().parents[1] / "notebooks" / "datav2_external_benchmark_colab.ipynb"
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4
    cells = notebook["cells"]
    assert len(cells) >= 20
    for index, cell in enumerate(cells):
        if cell["cell_type"] != "code":
            continue
        assert index > 0 and cells[index - 1]["cell_type"] == "markdown"
        ast.parse("".join(cell["source"]))
