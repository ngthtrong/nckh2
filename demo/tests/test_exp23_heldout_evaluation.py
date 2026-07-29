from __future__ import annotations

from datetime import datetime, timezone
from types import MappingProxyType

import pytest

from demo.experiments.evaluation_data import (
    EvaluationDataError,
    EvaluationDataset,
    EvaluatorReport,
    SelectedConfig,
    SelectedConfigBundle,
    build_evaluator_analysis_view,
)
from demo.experiments.exp20_output_burden import (
    PREREGISTERED_REVIEW_POLICIES,
)
from demo.experiments.exp23_heldout_evaluation import (
    REFERENCE_METHOD,
    _pair_id,
    build_clustering_analysis,
    build_selectors,
    evaluate_selected_pair,
    load_x0_authorization,
    run_once,
    validate_selectors,
)
from demo.experiments.promote_gate3 import _validate_command
from demo.experiments.protocol import file_sha256
from demo.pipeline.attributes import Event
from demo.pipeline.metrics import evaluate_output_burden


def _event(index: int) -> Event:
    return Event(
        event_id=f"event-{index}",
        lat=10.0 + index * 0.001,
        lng=106.0 + index * 0.001,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        flood=0.5,
        urgency=0.5,
        n_trapped=2,
        vulnerability=1.0,
        has_image=True,
        source_type="fixture",
        province="fixture",
        note="fixture",
        missing_fields=(),
        confidence=0.8,
        gt_cluster=-1,
        is_fake=False,
    )


def _evaluator_report(index: int, truth: int) -> EvaluatorReport:
    return EvaluatorReport(
        event_id=f"event-{index}",
        incident_id=None if truth < 0 else f"incident-{truth}",
        gt_cluster=truth,
        scenario_family="fixture_multimodal",
        duplicate_kind="none",
        duplicate_family_id=None,
        coverage_n=None,
        coverage_v=None,
        population_member_indices=(),
        vulnerable_member_indices=(),
        is_fake=truth < 0,
        adversary=None,
    )


def _dataset(seed: int = 3000) -> EvaluationDataset:
    truth = (0, 0, 1, -1)
    return EvaluationDataset(
        seed=seed,
        events=tuple(_event(index) for index in range(len(truth))),
        ground_truth=truth,
        fake_truth=tuple(value < 0 for value in truth),
        evaluator_reports=tuple(
            _evaluator_report(index, value)
            for index, value in enumerate(truth)
        ),
        incidents=(
            MappingProxyType(
                {
                    "incident_id": "incident-0",
                    "gt_cluster": 0,
                    "scenario_family": "fixture_multimodal",
                }
            ),
            MappingProxyType(
                {
                    "incident_id": "incident-1",
                    "gt_cluster": 1,
                    "scenario_family": "fixture_multimodal",
                }
            ),
        ),
        quality=MappingProxyType({}),
        source_sha256=f"{seed:064x}",
        dataset_manifest_sha256="1" * 64,
        gate1_run_id="fixture-gate1",
        gate1_manifest_sha256="2" * 64,
    )


def _selection(method_id: str, track_id: str) -> SelectedConfig:
    return SelectedConfig(
        method_id=method_id,
        track_id=track_id,
        config=MappingProxyType({"resolution": 1.0}),
        config_sha256=(method_id + track_id).encode().hex()[:64].ljust(64, "0"),
        source_artifact_id="fixture-calibration",
        source_selection_sha256=(
            ("selection-" + method_id + track_id).encode().hex()[:64].ljust(64, "0")
        ),
    )


def test_run_once_refuses_non_candidate_before_any_test_load(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in ("DEMO_RUN_ID", "DEMO_ARTIFACT_DIR", "DEMO_TABLES_DIR"):
        monkeypatch.delenv(name, raising=False)

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("test loader must not be reached")

    monkeypatch.setattr(
        "demo.experiments.exp23_heldout_evaluation.load_evaluation_dataset",
        forbidden,
    )
    with pytest.raises(RuntimeError, match="immutable candidate runner"):
        run_once()


def test_evaluator_analysis_view_contains_no_observable_attributes() -> None:
    dataset = _dataset()
    view = build_evaluator_analysis_view(dataset)
    assert set(view) == {"reports", "incidents"}
    assert len(view["reports"]) == len(dataset.events)
    assert set(view["reports"][0]) == {"event_id", "evaluation_only"}
    assert "lat" not in view["reports"][0]
    assert view["reports"][-1]["evaluation_only"]["gt_cluster"] is None

    misaligned = EvaluationDataset(
        **{
            **dataset.__dict__,
            "events": tuple(reversed(dataset.events)),
        }
    )
    with pytest.raises(EvaluationDataError, match="not aligned"):
        build_evaluator_analysis_view(misaligned)


def test_selected_pair_joins_truth_only_after_sanitized_prediction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset = _dataset()
    selection = _selection("product_louvain", "benchmark_label_aware")
    calls: list[tuple[str, ...]] = []
    by_id = {
        "event-0": 0,
        "event-1": 0,
        "event-2": 1,
        "event-3": 2,
    }

    def prediction(
        method_id: str,
        config: object,
        events: object,
        *,
        seed: int,
        product_config: object,
    ) -> tuple[list[int], None, None]:
        event_list = list(events)
        assert method_id == "product_louvain"
        assert seed == dataset.seed
        assert all(
            event.gt_cluster == -1 and event.is_fake is False
            for event in event_list
        )
        calls.append(tuple(str(event.event_id) for event in event_list))
        return [by_id[str(event.event_id)] for event in event_list], None, None

    monkeypatch.setattr(
        "demo.experiments.exp23_heldout_evaluation._predict_selected",
        prediction,
    )
    row = evaluate_selected_pair(
        dataset,
        selection,
        product_selection=selection,
    )
    assert row["status"] == "succeeded"
    assert len(calls) == 2
    assert calls[1] == tuple(reversed(calls[0]))
    assert row["metrics"]["coverage"]["point_coverage_rate"] == 1.0
    assert row["metrics"]["ari_labeled_reports"]["denominator"] == 3
    assert row["metrics"]["partition_stability"]["value"] == 1.0
    assert row["selection"]["config_sha256"] == selection.config_sha256


def _method_metrics(value: float) -> dict[str, object]:
    labels = [0, 0, 1, 2]
    truth = [0, 0, 1, -1]
    metrics = evaluate_output_burden(
        labels,
        truth,
        [0.8] * 4,
        PREREGISTERED_REVIEW_POLICIES,
        noise_label=None,
    )
    metrics["ari_labeled_reports"] = {
        "value": value,
        "nmi_diagnostic": value,
        "denominator": 3,
    }
    metrics["geographic_diameter"] = {
        "value_metres": 100.0 - value,
        "denominator": 3,
    }
    metrics["partition_stability"] = {
        "value": value,
        "denominator": 4,
    }
    return metrics


def test_analysis_uses_one_holm_family_and_retains_all_ties() -> None:
    selections = tuple(
        _selection(method_id, track_id)
        for track_id in (
            "benchmark_label_aware",
            "operational_label_free",
        )
        for method_id in (REFERENCE_METHOD, "additive_louvain")
    )
    bundle = SelectedConfigBundle(
        calibration_protocol_sha256="3" * 64,
        sources=(),
        selections=selections,
        exclusions=(),
    )
    seed_rows = []
    for seed in range(3000, 3040):
        methods = []
        for selection in selections:
            pair = _pair_id(selection.method_id, selection.track_id)
            labels = [0, 0, 1, 2]
            methods.append(
                {
                    "method": pair,
                    "method_id": selection.method_id,
                    "track_id": selection.track_id,
                    "status": "succeeded",
                    "selection": {
                        "config": dict(selection.config),
                        "config_sha256": selection.config_sha256,
                        "source_artifact_id": selection.source_artifact_id,
                        "source_selection_sha256": (
                            selection.source_selection_sha256
                        ),
                    },
                    "prediction_noise_label": None,
                    "n_points": 4,
                    "prediction_sha256": "4" * 64,
                    "prediction_label_counts": {"0": 2, "1": 1, "2": 1},
                    "predicted_labels": labels,
                    "metrics": _method_metrics(0.75),
                    "family_metrics": [],
                    "multimodal_family_metrics": [],
                    "error": None,
                }
            )
        seed_rows.append(
            {
                "seed": seed,
                "stage": "test",
                "dataset_sha256": f"{seed:064x}",
                "dataset_manifest_sha256": "1" * 64,
                "gate1_run_id": "fixture",
                "gate1_manifest_sha256": "2" * 64,
                "n_points": 4,
                "status": "succeeded",
                "methods": methods,
            }
        )

    analysis = build_clustering_analysis(seed_rows, bundle)
    comparison = analysis["paired_comparisons"][
        "benchmark_label_aware"
    ]["additive_louvain"]["incident_split_loss"]
    assert comparison["n_seed_pairs"] == 40
    assert comparison["n_ties"] == 40
    assert comparison["raw_p_value"] == 1.0
    assert comparison["holm_adjusted_p_value"] == 1.0
    assert comparison["holm_family"] == (
        "incident_integrity:benchmark_label_aware:all_method_comparisons"
    )


def test_selector_registry_detects_checksum_and_pointer_mutations() -> None:
    result = {
        "schema_version": "exp23-heldout-evaluation-v1",
        "artifact_content_sha256": "a" * 64,
        "clustering": {
            "method_summaries": {},
            "paired_comparisons": {},
        },
        "factorial_ablation": {
            "clustering": {"effects": []},
            "priority": {"effects": []},
        },
        "priority_robustness": {
            "summaries": [],
            "paired_estimator_effects": [],
        },
        "dispatch_outcomes": {
            "summary": [],
            "paired_policy_comparisons": [],
        },
    }
    selectors = build_selectors(result)
    assert validate_selectors(selectors, result)["status"] == "pass"

    changed = dict(selectors)
    changed["selector_count"] = 1
    with pytest.raises(ValueError, match="checksum mismatch"):
        validate_selectors(changed, result)


def test_x0_authorization_is_bound_before_release(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: object,
) -> None:
    from pathlib import Path

    from demo.experiments import exp23_heldout_evaluation as exp23

    root = Path(tmp_path)
    gate1 = root / "gate1.json"
    gate2 = root / "gate2.json"
    selected = root / "selected.json"
    authorization_path = root / "x0-release.json"
    for path, value in (
        (gate1, "gate1"),
        (gate2, "gate2"),
        (selected, "selected"),
    ):
        path.write_text(value, encoding="utf-8")
    monkeypatch.setattr(exp23, "DEFAULT_GATE1_LOCK", gate1)
    monkeypatch.setattr(exp23, "DEFAULT_GATE2_LOCK", gate2)
    monkeypatch.setattr(exp23, "DEFAULT_SELECTED_CONFIGS", selected)
    monkeypatch.setattr(exp23, "DEFAULT_X0_RELEASE", authorization_path)
    released = tuple(range(3000, 3040))
    authorization = {
        "schema_version": "x0-release-v1",
        "status": "authorized",
        "maximum_candidate_suite_invocations": 1,
        "expected_test_seed_count": 40,
        "expected_test_seed_sha256": exp23.sha256_bytes(
            exp23._canonical_json_bytes(list(released))
        ),
        "gate1_lock_sha256": file_sha256(gate1),
        "gate2_lock_sha256": file_sha256(gate2),
        "selected_configs_sha256": file_sha256(selected),
        "runner_sha256": file_sha256(Path(exp23.__file__).resolve()),
        "seed_or_method_filter": None,
        "resume": False,
    }
    authorization["authorization_content_sha256"] = exp23.sha256_bytes(
        exp23._canonical_json_bytes(authorization)
    )
    authorization_path.write_text(
        __import__("json").dumps(authorization),
        encoding="utf-8",
    )
    loaded = load_x0_authorization(
        authorization_path,
        released_seeds=released,
    )
    assert loaded["maximum_candidate_suite_invocations"] == 1

    authorization["maximum_candidate_suite_invocations"] = 2
    authorization_path.write_text(
        __import__("json").dumps(authorization),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_x0_authorization(
            authorization_path,
            released_seeds=released,
        )


def test_gate3_command_contract_is_relocatable_but_historically_exact(
    tmp_path: object,
) -> None:
    from pathlib import Path

    historical_root = (Path(tmp_path) / "historical-clone").resolve()
    gate1_lock = {
        "accepted_run": {
            "manifest": (
                "demo/artifacts/runs/locked-gate1-run/manifest.json"
            ),
        },
    }
    dataset_root = (
        historical_root
        / "demo"
        / "artifacts"
        / "runs"
        / "locked-gate1-run"
        / "work"
        / "datasets"
    )
    valid = {
        "repository": {"root": str(historical_root)},
        "command": [
            ".venv/bin/python",
            "-m",
            "demo.experiments.exp23_heldout_evaluation",
            "--dataset-root",
            str(dataset_root.resolve()),
        ]
    }
    _validate_command(valid, gate1_lock=gate1_lock)

    filtered = {
        **valid,
        "command": [
            *valid["command"],
            "--seed-limit",
            "1",
        ]
    }
    with pytest.raises(ValueError, match="no-filter contract"):
        _validate_command(filtered, gate1_lock=gate1_lock)

    relocated_command = {
        **valid,
        "command": [
            *valid["command"][:-1],
            str(
                Path(tmp_path)
                / "relocated-clone"
                / "demo"
                / "artifacts"
                / "runs"
                / "locked-gate1-run"
                / "work"
                / "datasets"
            ),
        ],
    }
    with pytest.raises(ValueError, match="no-filter contract"):
        _validate_command(relocated_command, gate1_lock=gate1_lock)

    tampered_root = {
        **valid,
        "repository": {
            "root": str((Path(tmp_path) / "tampered-root").resolve()),
        },
    }
    with pytest.raises(ValueError, match="no-filter contract"):
        _validate_command(tampered_root, gate1_lock=gate1_lock)

    tampered_gate1 = {
        "accepted_run": {
            "manifest": (
                "demo/artifacts/runs/tampered-gate1-run/manifest.json"
            ),
        },
    }
    with pytest.raises(ValueError, match="no-filter contract"):
        _validate_command(valid, gate1_lock=tampered_gate1)
