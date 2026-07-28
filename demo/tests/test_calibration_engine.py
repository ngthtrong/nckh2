from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import numpy as np
import pytest

from demo.experiments.calibration import (
    MetricConstraint,
    config_sha256,
    density_match_diagnostics,
    evaluate_candidates,
    expand_search_space,
    factorial_effect_summaries,
    find_density_match,
    graph_density,
    holm_adjust,
    load_calibration_contract,
    load_tuning_dataset,
    operational_calibration_metrics,
    operational_selection_constraints,
    paired_endpoint_family,
    paired_inference,
    select_candidate,
    write_calibration_artifact,
)
from demo.experiments.protocol import ProtocolError, TrackSpec, TuningProtocol
from demo.pipeline.attributes import Event


def _protocol() -> TuningProtocol:
    return TuningProtocol(
        development_seeds=(11, 12),
        calibration_seeds=(21, 22),
        tracks=(
            TrackSpec(
                id="benchmark_label_aware",
                calibration_labels=True,
                constraints=(),
            ),
            TrackSpec(
                id="operational_label_free",
                calibration_labels=False,
                constraints=(),
            ),
        ),
        max_candidates_per_method_track=128,
        seed_manifest_sha256="a",
        metric_contract_sha256="b",
        protocol_sha256="c",
    )


def test_grid_and_config_hash_are_order_independent() -> None:
    first = expand_search_space({"z": [2, 1], "a": [False, True]})
    second = expand_search_space({"a": [False, True], "z": [2, 1]})
    assert first == second
    assert len(first) == 4
    assert config_sha256({"z": 2, "a": True}) == config_sha256(
        {"a": True, "z": 2}
    )


def test_evaluation_retains_seed_failures_and_counts_configurations() -> None:
    configs = [{"value": 1}, {"value": 2}]

    def evaluator(config, seed):
        if config["value"] == 2 and seed == 12:
            raise RuntimeError("negative outcome retained")
        return {"objective": config["value"] + seed, "operator_review_burden": 2}

    rows = evaluate_candidates(
        "method",
        "benchmark_label_aware",
        "development",
        configs,
        evaluator,
        tuning_protocol=_protocol(),
    )
    assert len(rows) == 2
    assert sum(row.configuration_evaluation_count for row in rows) == 2
    failed = next(row for row in rows if row.status == "failed")
    assert failed.failures[0].exception_type == "RuntimeError"
    assert failed.failures[0].message == "negative outcome retained"
    succeeded = next(row for row in rows if row.status == "succeeded")
    assert succeeded.aggregate_metrics["objective__min"] == 12.0
    assert succeeded.aggregate_metrics["objective__max"] == 13.0


def test_operational_calibration_metric_is_common_and_label_free() -> None:
    events = [
        Event(
            event_id=f"E-{index}",
            lat=16.0,
            lng=107.0,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            flood=0.5,
            urgency=0.5,
            n_trapped=1,
            vulnerability=0.0,
            has_image=True,
            confidence=0.8,
        )
        for index in range(4)
    ]
    contract = load_calibration_contract()
    metrics = operational_calibration_metrics(
        events,
        [0, 0, 1, -1],
        [-1, 1, 0, 0],
        noise_label=-1,
        contract=contract,
    )

    assert metrics["partition_stability"] == 1.0
    assert metrics["operator_review_burden"] == 2.0
    assert metrics["operator_review_burden_denominator"] == 3.0
    assert metrics["operator_review_burden_rate"] == pytest.approx(2 / 3)
    constraints = operational_selection_constraints(
        contract,
        graph_method=True,
    )
    assert {row.metric for row in constraints} == {
        "partition_stability__min",
        "operator_review_burden_rate__max",
        "geographic_diameter__max",
        "disconnected_communities__max",
        "retained_fraction__min",
        "retained_fraction__max",
    }


def test_label_free_track_rejects_label_aware_metrics_as_retained_failure() -> None:
    rows = evaluate_candidates(
        "method",
        "operational_label_free",
        "calibration",
        [{"value": 1}],
        lambda config, seed: {"ari_labeled_reports": 1.0},
        tuning_protocol=_protocol(),
    )
    assert rows[0].status == "failed"
    assert all(
        failure.exception_type == "ProtocolError" for failure in rows[0].failures
    )


def test_selection_uses_objective_burden_complexity_then_hash() -> None:
    configs = [{"name": "b"}, {"name": "a"}, {"name": "failed"}]

    def evaluator(config, seed):
        if config["name"] == "failed":
            raise RuntimeError("keep me")
        return {
            "objective": 0.8,
            "operator_review_burden": 3 if config["name"] == "b" else 2,
            "constraint": 0,
        }

    rows = evaluate_candidates(
        "method",
        "benchmark_label_aware",
        "development",
        configs,
        evaluator,
        tuning_protocol=_protocol(),
    )
    selected = select_candidate(
        rows,
        objective="objective",
        direction="higher",
        constraints=(MetricConstraint("constraint", "<=", 0),),
    )
    assert selected.status == "selected"
    assert selected.selected_config == {"name": "a"}
    assert selected.considered_configurations == 3
    assert selected.succeeded_configurations == 2
    assert any("seed failure" in row["reasons"] for row in selected.rejected)


def test_density_matching_meets_both_locked_tolerances_when_feasible() -> None:
    weights = np.array(
        [
            [0, 0.9, 0.8, 0.7, 0.1],
            [0.9, 0, 0.6, 0.5, 0.2],
            [0.8, 0.6, 0, 0.4, 0.3],
            [0.7, 0.5, 0.4, 0, 0.05],
            [0.1, 0.2, 0.3, 0.05, 0],
        ],
        dtype=float,
    )
    reference_matrix = np.where(weights > 0.4, weights, 0.0)
    reference = graph_density(reference_matrix)
    match = find_density_match(weights, reference, knn_candidates=(0, 2))
    assert match.diagnostics["matched"] is True
    assert match.diagnostics["retained_fraction_absolute_error"] <= 0.01
    assert match.diagnostics["mean_degree_relative_error"] <= 0.05
    assert density_match_diagnostics(reference, match.density)["matched"] is True


def test_shared_inference_fields_and_holm_are_exposed() -> None:
    summary = paired_inference(
        [0.8, 0.7, 0.9, 0.6],
        [0.6, 0.7, 0.8, 0.5],
        direction="higher",
        bootstrap_samples=200,
    )
    for field in (
        "mean",
        "standard_deviation",
        "median",
        "paired_confidence_interval",
        "effect_size",
        "raw_p_value",
        "holm_adjusted_p_value",
        "denominator",
    ):
        assert field in summary
    adjusted = holm_adjust({"a": 0.01, "b": 0.03, "c": 0.2})
    assert adjusted == {"a": 0.03, "b": 0.06, "c": 0.2}

    family = paired_endpoint_family(
        [
            {"seed": 1, "ari": 0.8, "burden": 4},
            {"seed": 2, "ari": 0.9, "burden": 3},
            {"seed": 3, "ari": 0.7, "burden": 5},
        ],
        [
            {"seed": 1, "ari": 0.7, "burden": 5},
            {"seed": 2, "ari": 0.8, "burden": 4},
            {"seed": 3, "ari": 0.7, "burden": 6},
        ],
        endpoint_directions={"ari": "higher", "burden": "lower"},
        denominators={"ari": 99, "burden": 120},
    )
    assert set(family) == {"ari", "burden"}
    assert family["ari"]["denominator"] == 99
    assert family["burden"]["denominator"] == 120
    assert all(row["holm_adjusted_p_value"] is not None for row in family.values())


def test_factorial_summaries_report_main_and_interaction_effects() -> None:
    rows = []
    for seed in (1, 2, 3, 4):
        for first in (False, True):
            for second in (False, True):
                rows.append(
                    {
                        "seed": seed,
                        "first": first,
                        "second": second,
                        "outcome": (
                            seed + 2 * first + 3 * second + 4 * first * second
                        ),
                    }
                )
    effects = factorial_effect_summaries(
        rows,
        factors=("first", "second"),
        outcome="outcome",
        bootstrap_samples=200,
    )
    by_id = {row["effect_id"]: row for row in effects}
    assert set(by_id) == {
        "main:first",
        "main:second",
        "interaction:first:second",
    }
    assert by_id["interaction:first:second"]["mean"] == 4.0
    assert all("holm_adjusted_p_value" in row for row in effects)


def test_factorial_summaries_include_highest_order_interaction() -> None:
    rows = []
    for seed in (1, 2, 3):
        for first in (False, True):
            for second in (False, True):
                for third in (False, True):
                    rows.append(
                        {
                            "seed": seed,
                            "first": first,
                            "second": second,
                            "third": third,
                            "outcome": float(8 * first * second * third),
                        }
                    )
    effects = factorial_effect_summaries(
        rows,
        factors=("first", "second", "third"),
        outcome="outcome",
        bootstrap_samples=200,
    )
    by_id = {row["effect_id"]: row for row in effects}

    assert len(effects) == 7
    assert by_id["interaction:first:second:third"]["mean"] == 8.0
    assert (
        by_id["interaction:first:second:third"]["effect_kind"]
        == "3_way_interaction"
    )


def _frozen_payload(seed: int) -> bytes:
    payload = {
        "seed": seed,
        "split": "development",
        "incidents": [],
        "reports": [
            {
                "event_id": f"EV-{seed}",
                "lat": 16.0,
                "lng": 107.0,
                "created_at": "2026-01-01T00:00:00+00:00",
                "flood": 0.5,
                "urgency": 0.6,
                "n_trapped": 4,
                "vulnerability": 1.0,
                "has_image": True,
                "source_type": "hotline",
                "province": "P",
                "note": "synthetic_report",
                "missing_fields": [],
                "evaluation_only": {"gt_cluster": 0},
            }
        ],
    }
    return (
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()


def test_frozen_loader_binds_manifest_entry_and_rejects_relabel_or_swap(
    tmp_path,
) -> None:
    root = tmp_path / "datasets"
    split = root / "development"
    split.mkdir(parents=True)
    first = _frozen_payload(11)
    second = _frozen_payload(12)
    (split / "seed_11.json").write_bytes(first)
    (split / "seed_12.json").write_bytes(second)
    entries = [
        {
            "path": f"development/seed_{seed}.json",
            "seed": seed,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "split": "development",
        }
        for seed, payload in ((11, first), (12, second))
    ]
    manifest = (
        json.dumps({"entries": entries}, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode()
    (root / "manifest.json").write_bytes(manifest)
    gate1_lock = tmp_path / "gate1-lock.json"
    gate1_lock.write_text(
        json.dumps(
            {
                "gate": "Gate 1",
                "status": "locked",
                "data_contract": {
                    "dataset_manifest_sha256": hashlib.sha256(manifest).hexdigest()
                },
            }
        ),
        encoding="utf-8",
    )

    loaded = load_tuning_dataset(
        root,
        stage="development",
        seed=11,
        tuning_protocol=_protocol(),
        calibration_labels=True,
        gate1_lock=gate1_lock,
    )
    assert loaded.source_sha256 == hashlib.sha256(first).hexdigest()
    assert loaded.ground_truth == (0,)

    # A file swap keeps valid JSON and a plausible split label but breaks the
    # exact manifest entry binding before any payload can reach a method.
    (split / "seed_11.json").write_bytes(second)
    with pytest.raises(ProtocolError, match="checksum mismatch"):
        load_tuning_dataset(
            root,
            stage="development",
            seed=11,
            tuning_protocol=_protocol(),
            gate1_lock=gate1_lock,
        )

    # Relabeling the swapped payload cannot repair the authenticated checksum.
    relabeled = json.loads(second)
    relabeled["seed"] = 11
    (split / "seed_11.json").write_text(json.dumps(relabeled), encoding="utf-8")
    with pytest.raises(ProtocolError, match="checksum mismatch"):
        load_tuning_dataset(
            root,
            stage="development",
            seed=11,
            tuning_protocol=_protocol(),
            gate1_lock=gate1_lock,
        )


def test_calibration_artifact_is_canonical_and_refuses_overwrite(tmp_path) -> None:
    destination = tmp_path / "tables" / "calibration.json"
    written = write_calibration_artifact(
        destination,
        protocol=_protocol(),
        evaluations=[],
        selections=[],
        metadata={"z": 1, "a": 2},
    )
    assert written == destination
    payload = destination.read_bytes()
    assert payload.endswith(b"\n")
    decoded = json.loads(payload)
    assert decoded["schema_version"] == "calibration-artifact-v1"
    assert payload == (
        json.dumps(
            decoded,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    with pytest.raises(FileExistsError):
        write_calibration_artifact(
            destination,
            protocol=_protocol(),
            evaluations=[],
            selections=[],
        )


def test_calibration_artifact_cannot_escape_candidate_tables(
    tmp_path,
    monkeypatch,
) -> None:
    tables = tmp_path / "run" / "tables"
    tables.mkdir(parents=True)
    monkeypatch.setenv("DEMO_TABLES_DIR", str(tables))

    with pytest.raises(ValueError, match="DEMO_TABLES_DIR"):
        write_calibration_artifact(
            tmp_path / "escaped.json",
            protocol=_protocol(),
            evaluations=[],
            selections=[],
        )
