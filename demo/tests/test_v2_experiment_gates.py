from __future__ import annotations

import gzip
import hashlib
import json
from collections import defaultdict
from dataclasses import replace
from pathlib import Path

import pytest

from demo.v2 import experiment
from demo.v2.generator import canonical_json_bytes
from demo.v2.protocol import ProtocolV2, file_sha256, load_protocol


@pytest.fixture(scope="module")
def protocol() -> ProtocolV2:
    return load_protocol()


@pytest.fixture(scope="module")
def complete_calibration_payload(protocol: ProtocolV2) -> dict[str, object]:
    configurations = experiment.all_configurations(protocol)
    rows: list[dict[str, object]] = []
    for configuration_index, configuration in enumerate(configurations):
        for seed in protocol.calibration_seeds:
            rows.append(
                {
                    "configuration_id": configuration.configuration_id,
                    "method": configuration.method_id,
                    "operator": configuration.operator,
                    "seed": seed,
                    "regime": "id",
                    "n_reports": 100,
                    "status": "success",
                    "metrics": {
                        "ari_linked": 0.5 + configuration_index / 100_000.0,
                        "false_destinations_per_100_reports": float(
                            configuration_index % 7
                        ),
                        "noise_rejection": 0.8,
                        "review_items_per_100_reports": float(
                            configuration_index % 5
                        ),
                        "n_reports": 100,
                        "n_linked_reports": 80,
                        "n_noise_reports": 20,
                        "n_noise_rejected": 16,
                        "n_false_destinations": configuration_index % 7,
                        "n_review_items": configuration_index % 5,
                    },
                }
            )
    return {
        "schema_version": "v2.calibration-rows.1",
        "protocol_sha256": protocol.bundle_sha256,
        "implementation_sha256": "implementation-for-test",
        "n_configurations": len(configurations),
        "n_seeds": len(protocol.calibration_seeds),
        "n_rows": len(rows),
        "rows": rows,
    }


def _selection_payload(protocol: ProtocolV2, implementation: str) -> dict[str, object]:
    by_method: dict[str, list[object]] = defaultdict(list)
    for configuration in experiment.all_configurations(protocol):
        by_method[configuration.method_id].append(configuration)
    return {
        "schema_version": "v2.calibration-selection.1",
        "protocol_sha256": protocol.bundle_sha256,
        "implementation_sha256": implementation,
        "selections": {
            method_id: {
                "status": "selected",
                "configuration": experiment._configuration_payload(configurations[0]),
            }
            for method_id, configurations in sorted(by_method.items())
        },
    }


def _patch_confirmation_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> dict[str, Path]:
    paths = {
        "selection": tmp_path / "calibration-selection.json",
        "freeze": tmp_path / "execution-freeze.json",
        "result": tmp_path / "confirmation-result.json.gz",
        "analysis": tmp_path / "confirmation-analysis.json",
        "state": tmp_path / "confirmation-state.json",
        "oracle": tmp_path / "oracle.json.gz",
    }
    monkeypatch.setattr(experiment, "CALIBRATION_SELECTION", paths["selection"])
    monkeypatch.setattr(experiment, "EXECUTION_FREEZE", paths["freeze"])
    monkeypatch.setattr(experiment, "CONFIRMATION_RESULT", paths["result"])
    monkeypatch.setattr(experiment, "CONFIRMATION_ANALYSIS", paths["analysis"])
    monkeypatch.setattr(experiment, "CONFIRMATION_MANIFEST", paths["state"])
    monkeypatch.setattr(experiment, "ORACLE_DIAGNOSTIC", paths["oracle"])
    return paths


def _write_confirmation_inputs(
    protocol: ProtocolV2,
    paths: dict[str, Path],
    implementation: str,
) -> None:
    selection = _selection_payload(protocol, implementation)
    paths["selection"].write_bytes(canonical_json_bytes(selection))
    active_seeds = list(protocol.confirmation_seeds)
    freeze = {
        "schema_version": "v2.execution-freeze.1",
        "protocol_sha256": protocol.bundle_sha256,
        "implementation_sha256": implementation,
        "calibration_selection_sha256": file_sha256(paths["selection"]),
        "confirmation_master_seeds": active_seeds,
        "retired_confirmation_master_seeds": list(
            protocol.retired_confirmation_seeds
        ),
        "confirmation_master_seeds_sha256": hashlib.sha256(
            canonical_json_bytes(active_seeds)
        ).hexdigest(),
        "regimes_per_master_seed": ["id", "ood"],
        "confirmation_datasets": len(active_seeds) * 2,
    }
    paths["freeze"].write_bytes(canonical_json_bytes(freeze))


def test_first_and_last_configuration_of_every_method_routes_exact_parameters(
    protocol: ProtocolV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    by_method: dict[str, list[object]] = defaultdict(list)
    for configuration in experiment.all_configurations(protocol):
        by_method[configuration.method_id].append(configuration)
    assert {method_id: len(rows) for method_id, rows in by_method.items()} == {
        "method.product_louvain": 128,
        "method.additive_louvain": 128,
        "method.st_dbscan": 64,
        "method.hdbscan_geo_time": 96,
    }

    graph_calls: list[object] = []
    st_calls: list[dict[str, object]] = []
    hdb_calls: list[dict[str, object]] = []

    def graph_stub(reports: object, config: object, *, random_state: int) -> object:
        graph_calls.append(config)
        return config

    def st_stub(reports: object, **parameters: object) -> object:
        st_calls.append(parameters)
        return parameters

    def hdb_stub(reports: object, **parameters: object) -> object:
        hdb_calls.append(parameters)
        return parameters

    monkeypatch.setattr(experiment, "run_graph_clustering", graph_stub)
    monkeypatch.setattr(experiment, "run_st_dbscan_v2", st_stub)
    monkeypatch.setattr(experiment, "run_hdbscan_v2", hdb_stub)

    for configurations in by_method.values():
        for configuration in (configurations[0], configurations[-1]):
            experiment.execute_configuration((), configuration, seed=17)

    assert [call.tau_t for call in graph_calls] == [30.0, 60.0, 30.0, 60.0]
    assert st_calls == [
        {"spatial_eps_m": 250.0, "temporal_eps_min": 15.0, "min_samples": 3},
        {"spatial_eps_m": 1000.0, "temporal_eps_min": 120.0, "min_samples": 12},
    ]
    assert hdb_calls == [
        {
            "min_cluster_size": 3,
            "min_samples": 1,
            "spatial_scale_m": 250.0,
            "temporal_scale_min": 30.0,
        },
        {
            "min_cluster_size": 20,
            "min_samples": 10,
            "spatial_scale_m": 1000.0,
            "temporal_scale_min": 60.0,
        },
    ]


def test_select_calibration_binds_exact_payload_and_file_source(
    protocol: ProtocolV2,
    complete_calibration_payload: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        experiment, "implementation_sha256", lambda: "implementation-for-test"
    )
    source = tmp_path / "calibration.json.gz"
    source.write_bytes(
        gzip.compress(
            canonical_json_bytes(complete_calibration_payload),
            compresslevel=9,
            mtime=0,
        )
    )
    output = tmp_path / "selection.json"
    selected = experiment.select_calibration(
        protocol=protocol,
        calibration_path=source,
        output_path=output,
    )
    payload_hash = hashlib.sha256(
        canonical_json_bytes(complete_calibration_payload)
    ).hexdigest()
    assert selected["calibration_rows_sha256"] == payload_hash
    assert selected["calibration_rows_payload_sha256"] == payload_hash
    assert selected["calibration_rows_source"] == {
        "kind": "gzip_file",
        "path": str(source.resolve()),
        "sha256": file_sha256(source),
    }
    assert set(selected["selections"]) == {
        "method.product_louvain",
        "method.additive_louvain",
        "method.st_dbscan",
        "method.hdbscan_geo_time",
    }
    assert all(row["status"] == "selected" for row in selected["selections"].values())


def test_select_calibration_rejects_duplicate_key_and_implementation_mismatch(
    protocol: ProtocolV2,
    complete_calibration_payload: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        experiment, "implementation_sha256", lambda: "implementation-for-test"
    )
    rows = complete_calibration_payload["rows"]
    assert isinstance(rows, list)
    duplicate = {
        **complete_calibration_payload,
        "n_rows": len(rows) + 1,
        "rows": [*rows, rows[0]],
    }
    with pytest.raises(experiment.ExperimentV2Error, match="duplicate calibration"):
        experiment.select_calibration(
            duplicate,
            protocol,
            output_path=tmp_path / "duplicate-selection.json",
        )

    wrong_implementation = {
        **complete_calibration_payload,
        "implementation_sha256": "wrong",
    }
    with pytest.raises(experiment.ExperimentV2Error, match="current implementation"):
        experiment.select_calibration(
            wrong_implementation,
            protocol,
            output_path=tmp_path / "wrong-implementation.json",
        )


def test_select_calibration_rejects_corrupt_endpoint_denominator(
    protocol: ProtocolV2,
    complete_calibration_payload: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        experiment, "implementation_sha256", lambda: "implementation-for-test"
    )
    rows = complete_calibration_payload["rows"]
    assert isinstance(rows, list)
    first = dict(rows[0])
    metrics = dict(first["metrics"])
    metrics["n_noise_reports"] = 0
    first["metrics"] = metrics
    corrupt = {**complete_calibration_payload, "rows": [first, *rows[1:]]}
    with pytest.raises(experiment.ExperimentV2Error, match="invalid endpoint denominators"):
        experiment.select_calibration(
            corrupt,
            protocol,
            output_path=tmp_path / "corrupt-denominator-selection.json",
        )


def test_freeze_binds_active_seeds_and_refuses_existing_state(
    protocol: ProtocolV2,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _patch_confirmation_paths(monkeypatch, tmp_path)
    implementation = "implementation-for-test"
    monkeypatch.setattr(experiment, "implementation_sha256", lambda: implementation)
    selection = _selection_payload(protocol, implementation)
    paths["selection"].write_bytes(canonical_json_bytes(selection))
    freeze = experiment.freeze_execution(
        protocol,
        selection_path=paths["selection"],
        output_path=paths["freeze"],
    )
    assert freeze["confirmation_master_seeds"] == list(range(4400, 4440))
    assert freeze["retired_confirmation_master_seeds"] == list(range(4300, 4340))
    with pytest.raises(experiment.ExperimentV2Error, match="freeze already exists"):
        experiment.freeze_execution(
            protocol,
            selection_path=paths["selection"],
            output_path=paths["freeze"],
        )

    paths["freeze"].unlink()
    paths["state"].write_text('{"status":"failed"}', encoding="utf-8")
    with pytest.raises(experiment.ExperimentV2Error, match="confirmation state"):
        experiment.freeze_execution(
            protocol,
            selection_path=paths["selection"],
            output_path=paths["freeze"],
        )


def test_confirmation_start_is_o_excl_and_terminal_state_cannot_transition(
    tmp_path: Path,
) -> None:
    state = tmp_path / "state.json"
    started = {
        "status": "started",
        "protocol_sha256": "p",
        "implementation_sha256": "i",
        "execution_freeze_sha256": "f",
        "selection_sha256": "s",
        "confirmation_master_seeds": [4400],
        "confirmation_master_seeds_sha256": "h",
        "result_file": "result",
        "analysis_file": "analysis",
        "oracle_diagnostic_file": "oracle",
    }
    experiment._exclusive_write_json(state, started)
    with pytest.raises(experiment.ExperimentV2Error, match="overwrite/retry"):
        experiment._exclusive_write_json(state, started)
    failed = {**started, "status": "failed"}
    experiment._transition_confirmation_state(state, failed)
    with pytest.raises(experiment.ExperimentV2Error, match="terminal and immutable"):
        experiment._transition_confirmation_state(
            state, {**started, "status": "accepted"}
        )
    accepted_state = tmp_path / "accepted-state.json"
    experiment._exclusive_write_json(accepted_state, started)
    accepted = {
        **started,
        "status": "accepted",
        "result_sha256": "1" * 64,
        "analysis_sha256": "2" * 64,
        "oracle_diagnostic_sha256": "3" * 64,
    }
    experiment._transition_confirmation_state(
        accepted_state, accepted
    )
    assert json.loads(accepted_state.read_text(encoding="utf-8"))["status"] == "accepted"
    with pytest.raises(experiment.ExperimentV2Error, match="terminal and immutable"):
        experiment._transition_confirmation_state(
            accepted_state, {**started, "status": "failed"}
        )

    incomplete_state = tmp_path / "incomplete-analysis-state.json"
    experiment._exclusive_write_json(incomplete_state, started)
    with pytest.raises(experiment.ExperimentV2Error, match="analysis_sha256"):
        experiment._transition_confirmation_state(
            incomplete_state,
            {
                **started,
                "status": "accepted",
                "result_sha256": "1" * 64,
                "oracle_diagnostic_sha256": "3" * 64,
            },
        )
    assert json.loads(incomplete_state.read_text(encoding="utf-8"))["status"] == (
        "started"
    )


def test_confirmation_crash_marks_failed_and_forbids_retry_without_generating_data(
    protocol: ProtocolV2,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _patch_confirmation_paths(monkeypatch, tmp_path)
    implementation = "implementation-for-test"
    monkeypatch.setattr(experiment, "implementation_sha256", lambda: implementation)
    _write_confirmation_inputs(protocol, paths, implementation)
    attempted: list[tuple[int, str]] = []

    def crash_before_generation(
        seed: int, regime: str, *, confirmation_release: bool = False
    ) -> object:
        attempted.append((seed, regime))
        assert confirmation_release is True
        raise RuntimeError("simulated pre-generation crash")

    monkeypatch.setattr(experiment, "generate_dataset", crash_before_generation)
    with pytest.raises(RuntimeError, match="simulated pre-generation crash"):
        experiment.run_confirmation(protocol)
    state = json.loads(paths["state"].read_text(encoding="utf-8"))
    assert state["status"] == "failed"
    assert state["retry_permitted"] is False
    assert state["confirmation_master_seeds"] == list(range(4400, 4440))
    assert attempted == [(4400, "id")]
    assert not paths["result"].exists()
    assert not paths["analysis"].exists()

    with pytest.raises(experiment.ExperimentV2Error, match="retry is forbidden"):
        experiment.run_confirmation(protocol)
    assert attempted == [(4400, "id")]


def test_confirmation_forbids_custom_result_and_state_paths(
    protocol: ProtocolV2,
    tmp_path: Path,
) -> None:
    with pytest.raises(experiment.ExperimentV2Error, match="custom confirmation result"):
        experiment.run_confirmation(protocol, result_path=tmp_path / "custom.json.gz")
    with pytest.raises(experiment.ExperimentV2Error, match="custom confirmation state"):
        experiment.run_confirmation(protocol, manifest_path=tmp_path / "custom.json")


def test_exact_composite_coverage_rejects_duplicates_missing_and_extra() -> None:
    expected = {("a", 1), ("b", 1)}
    experiment._assert_exact_composite_keys(
        "fixture",
        [{"method": "a", "seed": 1}, {"method": "b", "seed": 1}],
        ("method", "seed"),
        expected,
    )
    with pytest.raises(experiment.ExperimentV2Error, match="duplicate"):
        experiment._assert_exact_composite_keys(
            "fixture",
            [{"method": "a", "seed": 1}, {"method": "a", "seed": 1}],
            ("method", "seed"),
            expected,
        )
    with pytest.raises(experiment.ExperimentV2Error, match="coverage mismatch"):
        experiment._assert_exact_composite_keys(
            "fixture",
            [{"method": "a", "seed": 1}],
            ("method", "seed"),
            expected,
        )


def test_scientific_loop_uses_predicted_priority_and_complete_end_to_end_rows(
    protocol: ProtocolV2,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Exercise the full loop on a development seed, never active confirmation."""

    mini = replace(protocol, confirmation_seeds=(4100,))
    selected: dict[str, object] = {}
    for configuration in experiment.all_configurations(protocol):
        selected.setdefault(configuration.method_id, configuration)
    freeze = tmp_path / "freeze.json"
    selection = tmp_path / "selection.json"
    result = tmp_path / "result.json.gz"
    analysis = tmp_path / "analysis.json"
    state = tmp_path / "state.json"
    oracle = tmp_path / "oracle.json.gz"
    freeze.write_text("freeze", encoding="utf-8")
    selection.write_text("selection", encoding="utf-8")
    monkeypatch.setattr(experiment, "EXECUTION_FREEZE", freeze)
    monkeypatch.setattr(experiment, "CALIBRATION_SELECTION", selection)
    monkeypatch.setattr(experiment, "ORACLE_DIAGNOSTIC", oracle)
    current_code = experiment.implementation_sha256()
    start = {
        "schema_version": "v2.confirmation-state.1",
        "status": "started",
        "protocol_sha256": mini.bundle_sha256,
        "implementation_sha256": current_code,
        "execution_freeze_sha256": file_sha256(freeze),
        "selection_sha256": file_sha256(selection),
        "confirmation_master_seeds": [4100],
        "confirmation_master_seeds_sha256": hashlib.sha256(
            canonical_json_bytes([4100])
        ).hexdigest(),
        "result_file": str(result.resolve()),
        "analysis_file": str(analysis.resolve()),
        "oracle_diagnostic_file": str(oracle.resolve()),
    }
    experiment._exclusive_write_json(state, start)
    manifest = experiment._run_confirmation_core(
        mini,
        result_path=result,
        analysis_path=analysis,
        state_path=state,
        current_code=current_code,
        selected=selected,  # type: ignore[arg-type]
        start_state=start,
    )
    assert manifest["status"] == "accepted"
    assert manifest["analysis_file"] == str(analysis.resolve())
    assert manifest["analysis_sha256"] == file_sha256(analysis)
    assert len(manifest["analysis_sha256"]) == 64
    assert file_sha256(state) != manifest["analysis_sha256"]
    payload = experiment._read_json_gzip(result)
    analysis_payload = experiment._read_json(analysis)
    assert analysis_payload["schema_version"] == "confirmation-analysis-v2"
    assert analysis_payload["coverage"]["status"] == "exact"
    assert analysis_payload["coverage"]["master_seed_count"] == 1
    assert analysis_payload["source_confirmation"][
        "confirmation_payload_sha256"
    ] == experiment._payload_sha256(payload)
    assert analysis_payload["analysis_contract"][
        "adverse_and_null_results_retained"
    ] is True
    assert "priority_construct_rows" not in payload
    assert len(payload["priority_rows"]) == 12
    assert {
        row["evaluation_partition"] for row in payload["priority_rows"]
    } == {"predicted_clusters_one_to_one_max_overlap"}
    campaigns = [
        row
        for row in payload["priority_stress_rows"]
        if row["family"] == "coordinated_high_confidence_campaign"
    ]
    assert campaigns
    assert all(row["false_priority_lift"]["applicable"] for row in campaigns)
    assert payload["priority_scoring_uses_truth"] is False
    assert payload["truth_used_by_scheduler"] is False
