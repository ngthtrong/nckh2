from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from demo.experiments import exp20_output_burden as exp20
from demo.experiments.calibration import TuningDataset
from demo.experiments.exp20_output_burden import (
    MethodSpec,
    PREREGISTERED_REVIEW_POLICIES,
    build_paired_comparisons,
    evaluate_seed,
)
from demo.experiments.protocol import TuningProtocol
from demo.pipeline.attributes import Event
from demo.pipeline.metrics import evaluate_output_burden


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "exp20_output_burden.py"
)


def _event(identifier: str, confidence: float) -> Event:
    return Event(
        event_id=identifier,
        lat=16.0,
        lng=108.0,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        flood=0.5,
        urgency=0.5,
        n_trapped=1,
        vulnerability=0.0,
        has_image=True,
        confidence=confidence,
    )


def _dataset(seed: int = 1000) -> TuningDataset:
    scores = (0.9, 0.8, 0.7, 0.6, 0.3, 0.2)
    return TuningDataset(
        seed=seed,
        stage="development",
        events=tuple(
            _event(f"seed-{seed}-report-{index}", score)
            for index, score in enumerate(scores)
        ),
        ground_truth=(10, 10, 11, 11, -1, -1),
        incidents=(
            {"gt_cluster": 10, "scenario_family": "multimodal"},
            {"gt_cluster": 11, "scenario_family": "ordinary"},
        ),
        source_sha256=f"{seed:064x}",
        manifest_sha256="d" * 64,
    )


def test_seed_evaluation_reports_all_families_and_multimodal_focus() -> None:
    reference = MethodSpec(
        "product_louvain",
        lambda events: [0, 0, 1, 1, 2, 2],
        None,
        "fixture reference",
    )
    explicit_noise = MethodSpec(
        "density",
        lambda events: [0, 0, 1, 1, -1, -1],
        -1,
        "fixture density method",
    )

    result = evaluate_seed(_dataset(), (reference, explicit_noise))

    assert result["status"] == "succeeded"
    assert len(result["methods"]) == 2
    for method in result["methods"]:
        assert method["metrics"]["coverage"]["point_coverage_rate"] == 1.0
        assert method["metrics"]["noise_label_is_destination"] is False
        assert {row["family"] for row in method["family_metrics"]} == {
            "multimodal",
            "ordinary",
        }
        assert [row["family"] for row in method["multimodal_family_metrics"]] == [
            "multimodal"
        ]


def test_family_merge_table_counts_cross_family_merges() -> None:
    cross_family_merge = MethodSpec(
        "product_louvain",
        lambda events: [0, 0, 0, 0, 1, 1],
        None,
        "cross-family fixture",
    )

    result = evaluate_seed(_dataset(), (cross_family_merge,))
    by_family = {
        row["family"]: row
        for row in result["methods"][0]["family_metrics"]
    }

    assert by_family["multimodal"]["incident_merge_loss"]["numerator"] == 1
    assert by_family["multimodal"]["incident_merge_loss"]["denominator"] == 1
    assert by_family["ordinary"]["incident_merge_loss"]["numerator"] == 1
    assert by_family["ordinary"]["incident_merge_loss"]["denominator"] == 1
    assert "cross-family" in (
        by_family["multimodal"]["incident_merge_loss"]["details"]["definition"]
    )


def test_method_failure_is_retained_instead_of_dropped() -> None:
    def fail(events):
        raise RuntimeError("intentional fixture failure")

    reference = MethodSpec(
        "product_louvain",
        lambda events: [0, 0, 1, 1, 2, 2],
        None,
        "fixture reference",
    )
    failed = MethodSpec("failed_method", fail, None, "failure fixture")

    result = evaluate_seed(_dataset(), (reference, failed))
    row = result["methods"][1]

    assert result["status"] == "partial_failure"
    assert row["status"] == "failed"
    assert row["metrics"] is None
    assert row["error"] == {
        "type": "RuntimeError",
        "message": "intentional fixture failure",
    }


def _method_row(method: str, labels: list[int], status: str = "succeeded"):
    if status == "failed":
        return {
            "method": method,
            "status": "failed",
            "metrics": None,
            "error": {"type": "RuntimeError", "message": "fixture"},
        }
    incidents = [10, 10, 10, 11, 11, -1, -1, -1]
    scores = [0.9, 0.8, 0.7, 0.6, 0.5, 0.3, 0.2, 0.4]
    return {
        "method": method,
        "status": "succeeded",
        "metrics": evaluate_output_burden(
            labels,
            incidents,
            scores,
            PREREGISTERED_REVIEW_POLICIES,
        ),
        "error": None,
    }


def test_paired_table_retains_negative_difference_tie_and_failure() -> None:
    reference_labels = [0, 0, 1, 1, -1, 1, 2, -1]
    better_labels = [0, 0, 0, 1, 1, 2, 2, -1]
    seed_rows = [
        {
            "seed": 1000,
            "methods": [
                _method_row("product_louvain", reference_labels),
                _method_row("candidate", better_labels),
            ],
        },
        {
            "seed": 1001,
            "methods": [
                _method_row("product_louvain", reference_labels),
                _method_row("candidate", reference_labels),
            ],
        },
        {
            "seed": 1002,
            "methods": [
                _method_row("product_louvain", reference_labels),
                _method_row("candidate", [], status="failed"),
            ],
        },
    ]

    comparisons = build_paired_comparisons(
        seed_rows,
        ("product_louvain", "candidate"),
        comparator_id="product_louvain",
    )
    standard = comparisons["candidate"]["operator_review_burden.standard"]

    assert standard["status"] == "available"
    assert standard["n_seed_pairs"] == 2
    assert standard["n_candidate_better"] == 1
    assert standard["n_ties"] == 1
    assert standard["holm_adjusted_p_value"] is not None
    assert [row["status"] for row in standard["pairs"]] == [
        "analyzed",
        "analyzed",
        "failed",
    ]
    assert standard["pairs"][0]["raw_difference_candidate_minus_comparator"] < 0
    assert standard["pairs"][1]["outcome"] == "tie"
    assert standard["pairs"][2]["candidate_error"]["message"] == "fixture"


def test_exp20_source_has_only_restricted_tuning_protocol_access() -> None:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    imported_modules = {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert all("evaluation_protocol" not in module for module in imported_modules)

    parser_choices: list[tuple[str, ...]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg == "choices" and isinstance(
                keyword.value, (ast.Tuple, ast.List)
            ):
                values = tuple(
                    element.value
                    for element in keyword.value.elts
                    if isinstance(element, ast.Constant)
                    and isinstance(element.value, str)
                )
                parser_choices.append(values)
    assert ("development", "calibration") in parser_choices


def test_prediction_payload_is_json_serializable_without_nan() -> None:
    reference = MethodSpec(
        "product_louvain",
        lambda events: [0, 0, 1, 1, 2, 2],
        None,
        "fixture reference",
    )
    payload = evaluate_seed(_dataset(), (reference,))
    encoded = json.dumps(payload, allow_nan=False)
    assert "multimodal" in encoded


def test_method_configuration_rejects_nonfinite_json() -> None:
    with pytest.raises(ValueError, match="finite JSON"):
        MethodSpec(
            "invalid",
            lambda events: [],
            None,
            "invalid configuration fixture",
            {"threshold": float("nan")},
        )


def test_run_requests_evaluator_view_and_writes_exclusive_artifacts(
    tmp_path, monkeypatch
) -> None:
    protocol = TuningProtocol(
        development_seeds=(1000, 1001),
        calibration_seeds=(2000,),
        tracks=(),
        max_candidates_per_method_track=128,
        seed_manifest_sha256="a" * 64,
        metric_contract_sha256="b" * 64,
        protocol_sha256="c" * 64,
    )
    calls: list[dict] = []

    def load_fixture(
        dataset_root,
        *,
        stage,
        seed,
        tuning_protocol,
        calibration_labels,
    ):
        calls.append(
            {
                "stage": stage,
                "seed": seed,
                "protocol": tuning_protocol,
                "calibration_labels": calibration_labels,
            }
        )
        return _dataset(seed)

    monkeypatch.setattr(exp20, "load_tuning_dataset", load_fixture)
    methods = (
        MethodSpec(
            "product_louvain",
            lambda events: [0, 0, 1, 1, 2, 2],
            None,
            "fixture reference",
        ),
        MethodSpec(
            "candidate",
            lambda events: [0, 0, 1, 1, -1, -1],
            -1,
            "fixture candidate",
        ),
    )
    output = tmp_path / "tables"

    result_path, selector_path = exp20.run(
        tmp_path / "datasets",
        stage="development",
        output_dir=output,
        methods=methods,
        tuning_protocol=protocol,
    )

    assert [row["seed"] for row in calls] == [1000, 1001]
    assert all(row["calibration_labels"] is True for row in calls)
    assert result_path.is_file()
    assert selector_path.is_file()
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["status"] == "succeeded"
    assert payload["coverage"]["seed_coverage_rate"] == 1.0
    assert payload["family_specific"]["multimodal_focus"]["status"] == "available"
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        exp20.run(
            tmp_path / "datasets",
            stage="development",
            output_dir=output,
            methods=methods,
            tuning_protocol=protocol,
        )
