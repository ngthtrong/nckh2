"""Experiment 23: one-shot evaluation on the Gate-2-released test suite.

This module has no tuning, subset, resume, or method-filter option.  The CLI
can run only inside an immutable :mod:`run_candidate` directory, authenticates
all selected configurations before opening a test dataset, loads each of the
40 released datasets exactly once, and evaluates every selected method/track
pair.  Calibration exclusions, method failures, adverse comparisons, and ties
remain first-class rows in the sealed output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import replace
from numbers import Integral
from pathlib import Path
from typing import Any, Mapping, Sequence

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from demo.experiments.artifacts import sha256_bytes  # noqa: E402
from demo.experiments.calibration import (  # noqa: E402
    config_sha256,
    factorial_effect_summaries,
    graph_density,
    operational_calibration_metrics,
    sparsify_at_quantile,
)
from demo.experiments.evaluation_data import (  # noqa: E402
    DEFAULT_GATE1_LOCK,
    DEFAULT_GATE2_LOCK,
    DEFAULT_SELECTED_CONFIGS,
    EvaluationDataError,
    EvaluationDataset,
    SelectedConfig,
    SelectedConfigBundle,
    build_evaluator_analysis_view,
    load_evaluation_dataset,
    load_selected_configs,
)
from demo.experiments.evaluation_protocol import (  # noqa: E402
    load_locked_test_seeds,
)
from demo.experiments.exp15_calibrated_comparison import (  # noqa: E402
    COMPOSITION_METHODS,
    _weight_params,
)
from demo.experiments.exp16_priority_robustness import (  # noqa: E402
    _paired_estimator_effects,
    _seed_aggregates,
    _summaries,
    evaluate_loaded_priority_seed,
)
from demo.experiments.exp17_dispatch_outcomes import (  # noqa: E402
    _paired_policy_comparisons,
    _summary,
    evaluate_loaded_dispatch_seed,
)
from demo.experiments.exp18_tuned_baselines import (  # noqa: E402
    _predict_baseline_labels,
)
from demo.experiments.exp19_factorial_ablation import (  # noqa: E402
    CLUSTERING_FACTORS,
    PRIORITY_FACTORS,
    evaluate_loaded_factorial_seed,
)
from demo.experiments.exp20_output_burden import (  # noqa: E402
    MethodSpec,
    PREREGISTERED_REVIEW_POLICIES,
    build_family_tables,
    build_method_summaries,
    build_paired_comparisons,
    evaluate_method,
)
from demo.experiments.inference import (  # noqa: E402
    apply_holm,
    descriptive_summary,
    paired_comparison,
)
from demo.experiments.pre_gate2 import (  # noqa: E402
    resolve_frozen_dataset_root,
)
from demo.experiments.protocol import (  # noqa: E402
    DEFAULT_PROTOCOL_DIR,
    file_sha256,
)
from demo.pipeline.baselines import (  # noqa: E402
    build_convex_similarity_matrix,
    validate_simplex_weights,
)
from demo.pipeline.clustering import (  # noqa: E402
    disconnected_report,
    run_louvain,
)
from demo.pipeline.metrics import (  # noqa: E402
    cluster_quality,
    geographic_spread,
)
from demo.pipeline.weighting import build_weight_matrix_vec  # noqa: E402


SCHEMA_VERSION = "exp23-heldout-evaluation-v1"
SELECTOR_SCHEMA_VERSION = "exp23-heldout-selectors-v1"
RESULT_NAME = "exp23_heldout_evaluation.json"
SELECTOR_NAME = "exp23_heldout_selectors.json"
DEFAULT_X0_RELEASE = REPOSITORY_ROOT / "revision" / "x0-release.json"
STAGE = "test"
TRACK_IDS = ("benchmark_label_aware", "operational_label_free")
REFERENCE_METHOD = "product_louvain"
EXPECTED_TEST_SEED_COUNT = 40
EXPECTED_SELECTED_PAIR_COUNT = 12
EXPECTED_EXCLUSION_PAIR_COUNT = 8
PAIR_SEPARATOR = "::"
NOISE_METHODS = frozenset(
    {
        "st_dbscan",
        "dbscan_geo_time_context",
        "hdbscan_geo_time_context",
    }
)

SOURCE_FILES = (
    "requirements.lock",
    "demo/data/generate.py",
    "demo/data/schema.py",
    "demo/experiments/evaluation_data.py",
    "demo/experiments/exp15_calibrated_comparison.py",
    "demo/experiments/exp16_priority_robustness.py",
    "demo/experiments/exp17_dispatch_outcomes.py",
    "demo/experiments/exp18_tuned_baselines.py",
    "demo/experiments/exp19_factorial_ablation.py",
    "demo/experiments/exp20_output_burden.py",
    "demo/experiments/exp23_heldout_evaluation.py",
    "demo/experiments/inference.py",
    "demo/pipeline/baselines.py",
    "demo/pipeline/clustering.py",
    "demo/pipeline/metrics.py",
    "demo/pipeline/priority.py",
    "demo/pipeline/weighting.py",
    "demo/simulation/dispatch.py",
)

ENDPOINTS: tuple[dict[str, Any], ...] = (
    {
        "id": "ari_labeled_reports",
        "family": "clustering_ari",
        "confirmatory": True,
        "direction": "higher",
        "value_path": ("metrics", "ari_labeled_reports", "value"),
        "denominator_path": ("metrics", "ari_labeled_reports", "denominator"),
    },
    {
        "id": "incident_split_loss",
        "family": "incident_integrity",
        "confirmatory": True,
        "direction": "lower",
        "value_path": ("metrics", "incident_split_loss", "rate"),
        "denominator_path": ("metrics", "incident_split_loss", "denominator"),
    },
    {
        "id": "incident_merge_loss",
        "family": "incident_integrity",
        "confirmatory": True,
        "direction": "lower",
        "value_path": ("metrics", "incident_merge_loss", "rate"),
        "denominator_path": ("metrics", "incident_merge_loss", "denominator"),
    },
    {
        "id": "false_operational_destinations",
        "family": "operational_burden",
        "confirmatory": True,
        "direction": "lower",
        "value_path": (
            "metrics",
            "false_operational_destinations",
            "count",
        ),
        "denominator_path": (
            "metrics",
            "false_operational_destinations",
            "denominator",
        ),
    },
    {
        "id": "operator_review_burden",
        "family": "operational_burden",
        "confirmatory": True,
        "direction": "lower",
        "value_path": (
            "metrics",
            "operator_review_burden",
            "standard",
            "queue_size",
        ),
        "denominator_path": (
            "metrics",
            "operator_review_burden",
            "standard",
            "denominator",
        ),
    },
    {
        "id": "noise_rejection_rate",
        "family": "key_secondary",
        "confirmatory": False,
        "direction": "higher",
        "value_path": ("metrics", "noise_rejection_rate", "rate"),
        "denominator_path": (
            "metrics",
            "noise_rejection_rate",
            "denominator",
        ),
    },
    {
        "id": "noise_absorption_rate",
        "family": "key_secondary",
        "confirmatory": False,
        "direction": "lower",
        "value_path": ("metrics", "noise_absorption_rate", "rate"),
        "denominator_path": (
            "metrics",
            "noise_absorption_rate",
            "denominator",
        ),
    },
    {
        "id": "geographic_diameter",
        "family": "key_secondary",
        "confirmatory": False,
        "direction": "lower",
        "value_path": ("metrics", "geographic_diameter", "value_metres"),
        "denominator_path": (
            "metrics",
            "geographic_diameter",
            "denominator",
        ),
    },
    {
        "id": "partition_stability",
        "family": "operational_stability",
        "confirmatory": False,
        "direction": "higher",
        "value_path": ("metrics", "partition_stability", "value"),
        "denominator_path": (
            "metrics",
            "partition_stability",
            "denominator",
        ),
    },
)


def _pair_id(method_id: str, track_id: str) -> str:
    if PAIR_SEPARATOR in method_id or PAIR_SEPARATOR in track_id:
        raise ValueError("method/track identifiers contain the pair separator")
    return f"{method_id}{PAIR_SEPARATOR}{track_id}"


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _artifact_content_sha256(result: Mapping[str, Any]) -> str:
    content = dict(result)
    content.pop("artifact_content_sha256", None)
    return sha256_bytes(_canonical_json_bytes(content))


def _prediction_sha256(labels: Sequence[int]) -> str:
    return sha256_bytes(_canonical_json_bytes(list(labels)))


def _stable_seed(identifier: str) -> int:
    return int.from_bytes(
        hashlib.sha256(identifier.encode("utf-8")).digest()[:4],
        "big",
    )


def load_x0_authorization(
    path: Path | str = DEFAULT_X0_RELEASE,
    *,
    released_seeds: Sequence[int],
) -> dict[str, Any]:
    """Authenticate the single-use X0 authorization before any test read."""

    source = Path(path).resolve()
    if source != DEFAULT_X0_RELEASE.resolve():
        raise ValueError("X0 authorization must use the canonical release path")
    try:
        payload = source.read_bytes()
        authorization = json.loads(payload)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ValueError("X0 authorization is absent or invalid") from exc
    if not isinstance(authorization, dict):
        raise ValueError("X0 authorization must be an object")
    content = dict(authorization)
    recorded = content.pop("authorization_content_sha256", None)
    if (
        not isinstance(recorded, str)
        or len(recorded) != 64
        or recorded != sha256_bytes(_canonical_json_bytes(content))
    ):
        raise ValueError("X0 authorization content checksum mismatch")
    expected_seed_hash = sha256_bytes(
        _canonical_json_bytes([int(seed) for seed in released_seeds])
    )
    if (
        authorization.get("schema_version") != "x0-release-v1"
        or authorization.get("status") != "authorized"
        or authorization.get("maximum_candidate_suite_invocations") != 1
        or authorization.get("expected_test_seed_count")
        != EXPECTED_TEST_SEED_COUNT
        or authorization.get("expected_test_seed_sha256")
        != expected_seed_hash
        or authorization.get("gate1_lock_sha256")
        != file_sha256(DEFAULT_GATE1_LOCK)
        or authorization.get("gate2_lock_sha256")
        != file_sha256(DEFAULT_GATE2_LOCK)
        or authorization.get("selected_configs_sha256")
        != file_sha256(DEFAULT_SELECTED_CONFIGS)
        or authorization.get("runner_sha256")
        != file_sha256(Path(__file__).resolve())
        or authorization.get("seed_or_method_filter") is not None
        or authorization.get("resume") is not False
    ):
        raise ValueError("X0 authorization differs from the locked release")
    return authorization


def _nested(source: Mapping[str, Any], path: Sequence[str]) -> Any:
    value: Any = source
    for key in path:
        if not isinstance(value, Mapping) or key not in value:
            raise KeyError(".".join(path))
        value = value[key]
    return value


def _selection_map(
    bundle: SelectedConfigBundle,
) -> dict[tuple[str, str], SelectedConfig]:
    result = {
        (selection.method_id, selection.track_id): selection
        for selection in bundle.selections
    }
    if len(result) != len(bundle.selections):
        raise EvaluationDataError("selected bundle repeats a method/track pair")
    return result


def _composition_prediction(
    method_id: str,
    config: Mapping[str, Any],
    events: Sequence[Any],
    *,
    seed: int,
) -> tuple[list[int], Any]:
    event_list = list(events)
    params = _weight_params(config)
    if method_id == "product_louvain":
        dense = build_weight_matrix_vec(event_list, params, mode="gating")
    elif method_id == "additive_louvain":
        dense = build_weight_matrix_vec(
            event_list,
            params,
            mode="additive",
            alpha=float(config["alpha"]),
        )
    elif method_id == "multiple_similarity_louvain":
        validate_simplex_weights(config["simplex_weights"])
        dense = build_convex_similarity_matrix(
            event_list,
            params,
            config["simplex_weights"],
        )
    else:
        raise ValueError(f"unsupported composition method: {method_id}")
    graph, _ = sparsify_at_quantile(
        dense,
        float(config["threshold_quantile"]),
        knn=int(config.get("knn", 0)),
    )
    labels = run_louvain(
        graph,
        resolution=float(config["resolution"]),
        random_state=seed,
    )
    return list(labels), graph


def _predict_selected(
    method_id: str,
    config: Mapping[str, Any],
    events: Sequence[Any],
    *,
    seed: int,
    product_config: Mapping[str, Any],
) -> tuple[list[int], int | None, Any | None]:
    if method_id in COMPOSITION_METHODS:
        labels, graph = _composition_prediction(
            method_id,
            config,
            events,
            seed=seed,
        )
        return labels, None, graph
    labels, noise_label, _, representation_graph = _predict_baseline_labels(
        method_id,
        config,
        events,
        seed=seed,
        product_config=product_config,
        st_distance_matrices=None,
    )
    return labels, noise_label, representation_graph


def _failure_method_row(
    selection: SelectedConfig,
    *,
    n_points: int,
    exc: Exception,
) -> dict[str, Any]:
    return {
        "method": _pair_id(selection.method_id, selection.track_id),
        "method_id": selection.method_id,
        "track_id": selection.track_id,
        "status": "failed",
        "description": "Gate-2-selected configuration",
        "selection": {
            "config": dict(selection.config),
            "config_sha256": selection.config_sha256,
            "source_artifact_id": selection.source_artifact_id,
            "source_selection_sha256": selection.source_selection_sha256,
        },
        "prediction_noise_label": (
            -1 if selection.method_id in NOISE_METHODS else None
        ),
        "n_points": n_points,
        "prediction_sha256": None,
        "prediction_label_counts": None,
        "predicted_labels": None,
        "metrics": None,
        "family_metrics": [],
        "multimodal_family_metrics": [],
        "error": {
            "type": type(exc).__name__,
            "message": str(exc),
        },
    }


def evaluate_selected_pair(
    dataset: EvaluationDataset,
    selection: SelectedConfig,
    *,
    product_selection: SelectedConfig,
) -> dict[str, Any]:
    """Predict from sanitized events, then join every evaluator-only endpoint."""

    try:
        method_events = tuple(replace(event) for event in dataset.events)
        if any(
            event.gt_cluster != -1 or event.is_fake is not False
            for event in method_events
        ):
            raise ValueError("evaluator-only fields leaked into method inputs")
        labels, noise_label, graph = _predict_selected(
            selection.method_id,
            selection.config,
            method_events,
            seed=dataset.seed,
            product_config=product_selection.config,
        )
        expected_ids = tuple(str(event.event_id) for event in method_events)

        def cached_prediction(events: Sequence[Any]) -> Sequence[int]:
            observed_ids = tuple(str(event.event_id) for event in events)
            if observed_ids != expected_ids:
                raise ValueError("metric evaluator changed prediction input order")
            if any(
                event.gt_cluster != -1 or event.is_fake is not False
                for event in events
            ):
                raise ValueError("evaluator-only fields leaked into cached prediction")
            return list(labels)

        method = MethodSpec(
            id=_pair_id(selection.method_id, selection.track_id),
            runner=cached_prediction,
            noise_label=noise_label,
            description="Gate-2-selected configuration",
            configuration={
                "method_id": selection.method_id,
                "track_id": selection.track_id,
                "config": dict(selection.config),
                "config_sha256": selection.config_sha256,
                "source_artifact_id": selection.source_artifact_id,
                "source_selection_sha256": selection.source_selection_sha256,
            },
        )
        row = evaluate_method(dataset, method, PREREGISTERED_REVIEW_POLICIES)
        row["method_id"] = selection.method_id
        row["track_id"] = selection.track_id
        row["selection"] = {
            "config": dict(selection.config),
            "config_sha256": selection.config_sha256,
            "source_artifact_id": selection.source_artifact_id,
            "source_selection_sha256": selection.source_selection_sha256,
        }
        if row["status"] != "succeeded":
            return row

        reverse_events = tuple(replace(event) for event in reversed(method_events))
        reverse_labels, reverse_noise_label, _ = _predict_selected(
            selection.method_id,
            selection.config,
            reverse_events,
            seed=dataset.seed,
            product_config=product_selection.config,
        )
        if reverse_noise_label != noise_label:
            raise ValueError("noise convention changed under report permutation")
        operational = operational_calibration_metrics(
            method_events,
            labels,
            reverse_labels,
            noise_label=noise_label,
        )
        standard_review = row["metrics"]["operator_review_burden"]["standard"]
        if (
            float(standard_review["queue_size"])
            != operational["operator_review_burden"]
            or float(standard_review["denominator"])
            != operational["operator_review_burden_denominator"]
        ):
            raise ValueError("standard review burden differs across locked evaluators")

        quality = cluster_quality(list(labels), list(dataset.ground_truth))
        spread = geographic_spread(
            list(method_events),
            list(labels),
            noise_label=noise_label,
            gt_labels=list(dataset.ground_truth),
        )
        row["metrics"]["ari_labeled_reports"] = {
            "value": float(quality["ari"]),
            "nmi_diagnostic": float(quality["nmi"]),
            "denominator": int(quality["n_eval"]),
        }
        row["metrics"]["geographic_diameter"] = {
            "value_metres": float(spread["max_diameter_km"]) * 1000.0,
            "denominator": int(spread["n_clusters"]),
            "convention": (
                "maximum diameter across emitted destinations; predicted-noise "
                "bin excluded"
            ),
            "full_spread_diagnostics": spread,
        }
        row["metrics"]["partition_stability"] = {
            "value": float(operational["partition_stability"]),
            "denominator": len(labels),
            "reverse_prediction_sha256": _prediction_sha256(reverse_labels),
        }
        if graph is None:
            row["metrics"]["graph_diagnostics"] = {
                "applicable": False,
                "density": None,
                "disconnected_communities": None,
            }
        else:
            density = graph_density(graph)
            connectivity = disconnected_report(graph, list(labels))
            row["metrics"]["graph_diagnostics"] = {
                "applicable": True,
                "density": density.to_dict(),
                "disconnected_communities": int(connectivity["n_broken"]),
            }
        return row
    except Exception as exc:
        return _failure_method_row(
            selection,
            n_points=len(dataset.events),
            exc=exc,
        )


def _exclusion_row(exclusion: Any, *, n_points: int) -> dict[str, Any]:
    return {
        "method": _pair_id(exclusion.method_id, exclusion.track_id),
        "method_id": exclusion.method_id,
        "track_id": exclusion.track_id,
        "status": "no_feasible_candidate",
        "description": "No operationally feasible calibration candidate",
        "selection": {
            "config": None,
            "config_sha256": None,
            "source_artifact_id": exclusion.source_artifact_id,
            "source_selection_sha256": exclusion.source_selection_sha256,
        },
        "prediction_noise_label": (
            -1 if exclusion.method_id in NOISE_METHODS else None
        ),
        "n_points": n_points,
        "prediction_sha256": None,
        "prediction_label_counts": None,
        "predicted_labels": None,
        "metrics": None,
        "family_metrics": [],
        "multimodal_family_metrics": [],
        "error": None,
    }


def evaluate_clustering_suite(
    datasets: Sequence[EvaluationDataset],
    bundle: SelectedConfigBundle,
) -> list[dict[str, Any]]:
    """Evaluate all 20 registered method/track dispositions for every seed."""

    selections = _selection_map(bundle)
    expected_products = {
        track_id: selections[(REFERENCE_METHOD, track_id)]
        for track_id in TRACK_IDS
    }
    rows: list[dict[str, Any]] = []
    for dataset in datasets:
        selected_rows = [
            evaluate_selected_pair(
                dataset,
                selection,
                product_selection=expected_products[selection.track_id],
            )
            for selection in bundle.selections
        ]
        excluded_rows = [
            _exclusion_row(exclusion, n_points=len(dataset.events))
            for exclusion in bundle.exclusions
        ]
        method_rows = sorted(
            [*selected_rows, *excluded_rows],
            key=lambda row: (str(row["track_id"]), str(row["method_id"])),
        )
        rows.append(
            {
                "seed": dataset.seed,
                "stage": STAGE,
                "dataset_sha256": dataset.source_sha256,
                "dataset_manifest_sha256": dataset.dataset_manifest_sha256,
                "gate1_run_id": dataset.gate1_run_id,
                "gate1_manifest_sha256": dataset.gate1_manifest_sha256,
                "n_points": len(dataset.events),
                "status": (
                    "succeeded"
                    if all(
                        row["status"]
                        in {"succeeded", "no_feasible_candidate"}
                        for row in method_rows
                    )
                    else "complete_with_retained_failures"
                ),
                "methods": method_rows,
            }
        )
    return rows


def _method_row(
    seed_row: Mapping[str, Any],
    method_id: str,
    track_id: str,
) -> Mapping[str, Any]:
    matches = [
        row
        for row in seed_row["methods"]
        if isinstance(row, Mapping)
        and row.get("method_id") == method_id
        and row.get("track_id") == track_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"seed {seed_row.get('seed')} has {len(matches)} rows for "
            f"{method_id}/{track_id}"
        )
    return matches[0]


def _endpoint_summary(
    seed_rows: Sequence[Mapping[str, Any]],
    *,
    method_id: str,
    track_id: str,
    endpoint: Mapping[str, Any],
) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    unavailable: list[dict[str, Any]] = []
    for seed_row in seed_rows:
        method = _method_row(seed_row, method_id, track_id)
        if method["status"] != "succeeded":
            unavailable.append(
                {
                    "seed": seed_row["seed"],
                    "status": method["status"],
                    "error": method["error"],
                }
            )
            continue
        value = _nested(method, endpoint["value_path"])
        denominator = _nested(method, endpoint["denominator_path"])
        if value is None:
            unavailable.append(
                {
                    "seed": seed_row["seed"],
                    "status": "undefined_zero_denominator",
                    "error": None,
                }
            )
            continue
        observations.append(
            {
                "seed": seed_row["seed"],
                "value": float(value),
                "denominator": int(denominator),
            }
        )
    denominator = {
        "expected_seeds": len(seed_rows),
        "analyzed_seeds": len(observations),
        "unavailable_seeds": len(unavailable),
        "metric_denominator_sum": sum(
            row["denominator"] for row in observations
        ),
    }
    base = {
        "endpoint": endpoint["id"],
        "family": endpoint["family"],
        "direction": endpoint["direction"],
        "confirmatory": endpoint["confirmatory"],
        "denominator": denominator,
        "observations": observations,
        "unavailable": unavailable,
    }
    if not observations:
        return {"status": "unavailable", **base}
    return {
        "status": "available",
        **base,
        **descriptive_summary(
            [row["value"] for row in observations],
            denominator=denominator,
            bootstrap_seed=_stable_seed(
                f"summary:{track_id}:{method_id}:{endpoint['id']}"
            ),
        ),
    }


def _endpoint_comparison(
    seed_rows: Sequence[Mapping[str, Any]],
    *,
    candidate_id: str,
    comparator_id: str,
    track_id: str,
    endpoint: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_values: list[float] = []
    comparator_values: list[float] = []
    pairs: list[dict[str, Any]] = []
    candidate_denominator = 0
    comparator_denominator = 0
    for seed_row in seed_rows:
        candidate = _method_row(seed_row, candidate_id, track_id)
        comparator = _method_row(seed_row, comparator_id, track_id)
        if (
            candidate["status"] != "succeeded"
            or comparator["status"] != "succeeded"
        ):
            pairs.append(
                {
                    "seed": seed_row["seed"],
                    "status": "unavailable",
                    "candidate_status": candidate["status"],
                    "comparator_status": comparator["status"],
                    "candidate_error": candidate["error"],
                    "comparator_error": comparator["error"],
                }
            )
            continue
        candidate_value = _nested(candidate, endpoint["value_path"])
        comparator_value = _nested(comparator, endpoint["value_path"])
        if candidate_value is None or comparator_value is None:
            pairs.append(
                {
                    "seed": seed_row["seed"],
                    "status": "undefined_zero_denominator",
                    "candidate_value": candidate_value,
                    "comparator_value": comparator_value,
                }
            )
            continue
        first = float(candidate_value)
        second = float(comparator_value)
        improvement = (
            first - second
            if endpoint["direction"] == "higher"
            else second - first
        )
        pairs.append(
            {
                "seed": seed_row["seed"],
                "status": "analyzed",
                "candidate_value": first,
                "comparator_value": second,
                "raw_difference_candidate_minus_comparator": first - second,
                "direction_adjusted_improvement": improvement,
                "outcome": (
                    "candidate_better"
                    if improvement > 0.0
                    else "comparator_better"
                    if improvement < 0.0
                    else "tie"
                ),
            }
        )
        candidate_values.append(first)
        comparator_values.append(second)
        candidate_denominator += int(
            _nested(candidate, endpoint["denominator_path"])
        )
        comparator_denominator += int(
            _nested(comparator, endpoint["denominator_path"])
        )
    denominator = {
        "expected_seed_pairs": len(seed_rows),
        "analyzed_seed_pairs": len(candidate_values),
        "unavailable_seed_pairs": len(seed_rows) - len(candidate_values),
        "candidate_metric_denominator_sum": candidate_denominator,
        "comparator_metric_denominator_sum": comparator_denominator,
    }
    base = {
        "endpoint": endpoint["id"],
        "family": endpoint["family"],
        "confirmatory": endpoint["confirmatory"],
        "track_id": track_id,
        "candidate_method": candidate_id,
        "comparator_method": comparator_id,
        "denominator": denominator,
        "pairs": pairs,
    }
    if not candidate_values:
        return {
            "status": "unavailable",
            **base,
            "direction": endpoint["direction"],
            "raw_p_value": None,
            "holm_adjusted_p_value": None,
        }
    return {
        "status": "available",
        **base,
        **paired_comparison(
            candidate_values,
            comparator_values,
            direction=endpoint["direction"],
            denominator=denominator,
            bootstrap_seed=_stable_seed(
                "paired:"
                f"{track_id}:{candidate_id}:{comparator_id}:{endpoint['id']}"
            ),
        ),
    }


def build_clustering_analysis(
    seed_rows: Sequence[Mapping[str, Any]],
    bundle: SelectedConfigBundle,
) -> dict[str, Any]:
    """Recompute all descriptive and paired inference from per-seed rows."""

    methods_by_track = {
        track_id: sorted(
            selection.method_id
            for selection in bundle.selections
            if selection.track_id == track_id
        )
        for track_id in TRACK_IDS
    }
    summaries = {
        track_id: {
            method_id: {
                endpoint["id"]: _endpoint_summary(
                    seed_rows,
                    method_id=method_id,
                    track_id=track_id,
                    endpoint=endpoint,
                )
                for endpoint in ENDPOINTS
            }
            for method_id in methods_by_track[track_id]
        }
        for track_id in TRACK_IDS
    }

    comparisons: dict[str, dict[str, dict[str, Any]]] = {}
    for track_id in TRACK_IDS:
        track_raw: dict[str, dict[str, Any]] = {}
        for candidate_id in methods_by_track[track_id]:
            if candidate_id == REFERENCE_METHOD:
                continue
            track_raw[candidate_id] = {
                endpoint["id"]: _endpoint_comparison(
                    seed_rows,
                    candidate_id=candidate_id,
                    comparator_id=REFERENCE_METHOD,
                    track_id=track_id,
                    endpoint=endpoint,
                )
                for endpoint in ENDPOINTS
            }

        for family in (
            "clustering_ari",
            "incident_integrity",
            "operational_burden",
        ):
            flat = {
                f"{candidate_id}:{endpoint_id}": row
                for candidate_id, endpoint_rows in track_raw.items()
                for endpoint_id, row in endpoint_rows.items()
                if row["family"] == family
            }
            adjusted = apply_holm(flat)
            holm_family = f"{family}:{track_id}:all_method_comparisons"
            for identifier, row in adjusted.items():
                candidate_id, endpoint_id = identifier.split(":", 1)
                track_raw[candidate_id][endpoint_id] = {
                    **row,
                    "holm_family": holm_family,
                }
        for candidate_id, endpoint_rows in track_raw.items():
            for endpoint_id, row in endpoint_rows.items():
                if "holm_family" not in row:
                    endpoint_rows[endpoint_id] = {
                        **row,
                        "holm_family": None,
                    }
        comparisons[track_id] = track_raw

    exp20_sensitivity: dict[str, Any] = {}
    family_tables: dict[str, Any] = {}
    for track_id in TRACK_IDS:
        pair_ids = [
            _pair_id(method_id, track_id)
            for method_id in methods_by_track[track_id]
        ]
        comparator = _pair_id(REFERENCE_METHOD, track_id)
        exp20_sensitivity[track_id] = {
            "method_summaries": build_method_summaries(seed_rows, pair_ids),
            "paired_comparisons": build_paired_comparisons(
                seed_rows,
                pair_ids,
                comparator_id=comparator,
            ),
        }
        family_tables[track_id] = build_family_tables(
            seed_rows,
            pair_ids,
            comparator_id=comparator,
        )

    retention = {
        "candidate_favorable": 0,
        "tied": 0,
        "candidate_adverse": 0,
        "unavailable": 0,
    }
    for track_rows in comparisons.values():
        for endpoint_rows in track_rows.values():
            for row in endpoint_rows.values():
                if row["status"] != "available":
                    retention["unavailable"] += int(
                        row["denominator"]["unavailable_seed_pairs"]
                    )
                    continue
                retention["candidate_favorable"] += int(
                    row["n_candidate_better"]
                )
                retention["tied"] += int(row["n_ties"])
                retention["candidate_adverse"] += int(
                    row["n_comparator_better"]
                )
                retention["unavailable"] += int(
                    row["denominator"]["unavailable_seed_pairs"]
                )
    return {
        "endpoint_registry": [
            {
                **dict(endpoint),
                "value_path": list(endpoint["value_path"]),
                "denominator_path": list(endpoint["denominator_path"]),
            }
            for endpoint in ENDPOINTS
        ],
        "reference_method": REFERENCE_METHOD,
        "method_summaries": summaries,
        "paired_comparisons": comparisons,
        "review_policy_sensitivity": exp20_sensitivity,
        "scenario_family_error_tables": family_tables,
        "retention_counts": retention,
    }


def build_factorial_section(
    datasets: Sequence[EvaluationDataset],
    *,
    product_selection: SelectedConfig,
) -> dict[str, Any]:
    clustering_rows: list[dict[str, Any]] = []
    priority_rows: list[dict[str, Any]] = []
    seed_failures: list[dict[str, Any]] = []
    for dataset in datasets:
        try:
            fresh = replace(
                dataset,
                events=tuple(replace(event) for event in dataset.events),
            )
            evaluated = evaluate_loaded_factorial_seed(
                fresh,
                product_config=product_selection.config,
                stage=STAGE,
            )
            clustering_rows.extend(evaluated["clustering_rows"])
            priority_rows.extend(evaluated["priority_rows"])
        except Exception as exc:
            seed_failures.append(
                {
                    "seed": dataset.seed,
                    "stage": STAGE,
                    "dataset_source_sha256": dataset.source_sha256,
                    "status": "failed",
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                    },
                }
            )
    failed_clustering = [
        row for row in clustering_rows if row["status"] != "succeeded"
    ]
    failed_priority = [
        row for row in priority_rows if row["status"] != "succeeded"
    ]
    clustering_complete = (
        not seed_failures
        and not failed_clustering
        and len(clustering_rows) == len(datasets) * 16
    )
    priority_complete = (
        not seed_failures
        and not failed_priority
        and len(priority_rows) == len(datasets) * 8
    )
    return {
        "schema_version": "heldout-factorial-ablation-v1",
        "stage": STAGE,
        "scope": (
            "held-out confirmation of the complete factorial declared before "
            "test release; no cell selection or early stopping"
        ),
        "product_selection": {
            "method_id": product_selection.method_id,
            "track_id": product_selection.track_id,
            "config": dict(product_selection.config),
            "config_sha256": product_selection.config_sha256,
            "source_selection_sha256": (
                product_selection.source_selection_sha256
            ),
        },
        "seed_failures": seed_failures,
        "clustering": {
            "factors": list(CLUSTERING_FACTORS),
            "variant_count": 16,
            "rows": clustering_rows,
            "effects": (
                factorial_effect_summaries(
                    clustering_rows,
                    factors=CLUSTERING_FACTORS,
                    outcome="ari_labeled_reports",
                )
                if clustering_complete
                else []
            ),
            "effect_orders": [1, 2, 3, 4],
            "effects_status": (
                "complete"
                if clustering_complete
                else "unavailable_due_to_retained_failures"
            ),
            "evaluation_count": len(clustering_rows),
            "expected_evaluation_count": len(datasets) * 16,
            "failed_evaluation_count": len(failed_clustering),
            "density_match_failures": sum(
                row["status"] == "succeeded" and not row["density_matched"]
                for row in clustering_rows
            ),
            "unmatched_cells_retained": True,
        },
        "priority": {
            "factors": list(PRIORITY_FACTORS),
            "variant_count": 8,
            "rows": priority_rows,
            "effects": (
                factorial_effect_summaries(
                    priority_rows,
                    factors=PRIORITY_FACTORS,
                    outcome="priority_rank_correlation",
                )
                if priority_complete
                else []
            ),
            "effect_orders": [1, 2, 3],
            "effects_status": (
                "complete"
                if priority_complete
                else "unavailable_due_to_retained_failures"
            ),
            "evaluation_count": len(priority_rows),
            "expected_evaluation_count": len(datasets) * 8,
            "failed_evaluation_count": len(failed_priority),
        },
        "inference": {
            "unit": "paired_seed",
            "confidence_interval": "paired bootstrap",
            "hypothesis_test": "paired Wilcoxon signed-rank",
            "multiplicity": "Holm within clustering and priority families",
            "all_interaction_orders_reported": True,
            "failed_and_density_unmatched_cells_retained": True,
        },
    }


def build_priority_section(
    datasets: Sequence[EvaluationDataset],
) -> dict[str, Any]:
    rows: list[dict[str, object]] = []
    failures: list[dict[str, Any]] = []
    for dataset in datasets:
        try:
            evaluator_data = build_evaluator_analysis_view(dataset)
            rows.extend(
                evaluate_loaded_priority_seed(
                    seed=dataset.seed,
                    stage=STAGE,
                    inference_events=tuple(
                        replace(event) for event in dataset.events
                    ),
                    evaluator_data=evaluator_data,
                    source_sha256=dataset.source_sha256,
                )
            )
        except Exception as exc:
            failures.append(
                {
                    "seed": dataset.seed,
                    "stage": STAGE,
                    "dataset_source_sha256": dataset.source_sha256,
                    "status": "failed",
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                    },
                }
            )
    seed_rows = _seed_aggregates(rows)
    effects = _paired_estimator_effects(seed_rows) if seed_rows else []
    return {
        "schema_version": "heldout-priority-robustness-v1",
        "stage": STAGE,
        "scope": (
            "all preregistered duplicate, adversarial, and missingness "
            "scenarios on every released test seed"
        ),
        "seed_failures": failures,
        "scenario_rows": rows,
        "seed_aggregates": seed_rows,
        "summaries": _summaries(seed_rows) if seed_rows else [],
        "paired_estimator_effects": effects,
        "retention_counts": {
            "revised_estimator_favorable": sum(
                int(row["n_candidate_better"]) for row in effects
            ),
            "tied": sum(int(row["n_ties"]) for row in effects),
            "revised_estimator_adverse": sum(
                int(row["n_comparator_better"]) for row in effects
            ),
        },
        "all_seed_failures_retained": True,
    }


def build_dispatch_section(
    datasets: Sequence[EvaluationDataset],
) -> dict[str, Any]:
    rows: list[dict[str, object]] = []
    failures: list[dict[str, Any]] = []
    for dataset in datasets:
        try:
            evaluator_data = build_evaluator_analysis_view(dataset)
            rows.extend(
                evaluate_loaded_dispatch_seed(
                    seed=dataset.seed,
                    stage=STAGE,
                    inference_events=tuple(
                        replace(event) for event in dataset.events
                    ),
                    evaluator_data=evaluator_data,
                    source_sha256=dataset.source_sha256,
                )
            )
        except Exception as exc:
            failures.append(
                {
                    "seed": dataset.seed,
                    "stage": STAGE,
                    "dataset_source_sha256": dataset.source_sha256,
                    "status": "failed",
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                    },
                }
            )
    comparisons = _paired_policy_comparisons(rows) if rows else []
    return {
        "schema_version": "heldout-independent-dispatch-outcomes-v1",
        "stage": STAGE,
        "scientific_scope": (
            "illustrative synthetic dispatch simulation; policy weights and "
            "resource assumptions are not expert validated"
        ),
        "outcome_independence_contract": {
            "primary_endpoints": ["latent_harm", "deadline_miss_rate"],
            "reported_priority_components_used_in_outcome": [],
            "reported_flood_used_in_outcome": False,
            "reported_vulnerability_used_in_outcome": False,
            "priority_is_used_only_for_policy_ordering": True,
        },
        "seed_failures": failures,
        "per_seed_resource_policy_rows": rows,
        "summary": _summary(rows) if rows else [],
        "paired_policy_comparisons": comparisons,
        "retention_counts": {
            "reference_policy_favorable": sum(
                int(row["n_candidate_better"]) for row in comparisons
            ),
            "tied": sum(int(row["n_ties"]) for row in comparisons),
            "reference_policy_adverse": sum(
                int(row["n_comparator_better"]) for row in comparisons
            ),
        },
        "all_policies_resource_scenarios_and_failures_retained": True,
    }


def _source_hashes(repository_root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in SOURCE_FILES:
        source = repository_root / relative
        if not source.is_file():
            raise FileNotFoundError(f"required held-out source is absent: {relative}")
        result[relative] = file_sha256(source)
    return result


def build_provenance_record(
    *,
    repository_root: Path = REPOSITORY_ROOT,
    protocol_dir: Path = DEFAULT_PROTOCOL_DIR,
    gate1_lock: Path = DEFAULT_GATE1_LOCK,
    gate2_lock: Path = DEFAULT_GATE2_LOCK,
    selected_configs: Path = DEFAULT_SELECTED_CONFIGS,
) -> dict[str, Any]:
    gate2 = json.loads(gate2_lock.read_text(encoding="utf-8"))
    gate1 = json.loads(gate1_lock.read_text(encoding="utf-8"))
    if (
        not isinstance(gate2, dict)
        or gate2.get("gate") != "Gate 2"
        or gate2.get("status") != "locked"
    ):
        raise EvaluationDataError("Gate-2 provenance is not locked")
    data_contract = gate1.get("data_contract")
    if not isinstance(data_contract, dict):
        raise EvaluationDataError("Gate-1 data contract is unavailable")
    return {
        "run_id": os.environ.get("DEMO_RUN_ID"),
        "gate1_lock": {
            "path": gate1_lock.relative_to(repository_root).as_posix(),
            "sha256": file_sha256(gate1_lock),
        },
        "gate2_lock": {
            "path": gate2_lock.relative_to(repository_root).as_posix(),
            "sha256": file_sha256(gate2_lock),
            "protocol_sha256": gate2["protocol_sha256"],
            "calibration_protocol_sha256": gate2[
                "calibration_protocol_sha256"
            ],
        },
        "selected_configs": {
            "path": selected_configs.relative_to(repository_root).as_posix(),
            "sha256": file_sha256(selected_configs),
        },
        "protocol_members": {
            path.name: file_sha256(path)
            for path in sorted(protocol_dir.glob("*.json"))
            if path.is_file()
        },
        "dataset_contract": {
            "dataset_manifest_sha256": data_contract[
                "dataset_manifest_sha256"
            ],
            "generator_version": data_contract["generator_version"],
            "generator_sha256": data_contract["generator_sha256"],
            "schema_version": data_contract["dataset_schema_version"],
            "schema_sha256": data_contract["schema_sha256"],
            "data_spec_sha256": data_contract["data_spec_sha256"],
        },
        "source_files": _source_hashes(repository_root),
    }


def _bundle_registry(bundle: SelectedConfigBundle) -> dict[str, Any]:
    return {
        "calibration_protocol_sha256": bundle.calibration_protocol_sha256,
        "sources": [
            {
                "id": source.id,
                "run_id": source.run_id,
                "manifest_path": source.manifest_path,
                "manifest_sha256": source.manifest_sha256,
                "table_path": source.table_path,
                "table_sha256": source.table_sha256,
                "artifact_content_sha256": source.artifact_content_sha256,
            }
            for source in bundle.sources
        ],
        "selections": [
            {
                "method_id": selection.method_id,
                "track_id": selection.track_id,
                "config": dict(selection.config),
                "config_sha256": selection.config_sha256,
                "source_artifact_id": selection.source_artifact_id,
                "source_selection_sha256": (
                    selection.source_selection_sha256
                ),
            }
            for selection in bundle.selections
        ],
        "exclusions": [
            {
                "method_id": exclusion.method_id,
                "track_id": exclusion.track_id,
                "status": exclusion.status,
                "source_artifact_id": exclusion.source_artifact_id,
                "source_selection_sha256": (
                    exclusion.source_selection_sha256
                ),
            }
            for exclusion in bundle.exclusions
        ],
    }


def build_result(
    datasets: Sequence[EvaluationDataset],
    bundle: SelectedConfigBundle,
    *,
    released_seeds: Sequence[int],
    provenance: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the complete held-out artifact from already-loaded immutable views."""

    datasets = tuple(datasets)
    released = tuple(int(seed) for seed in released_seeds)
    observed = tuple(dataset.seed for dataset in datasets)
    if observed != released or len(observed) != len(set(observed)):
        raise ValueError(
            "loaded evaluation datasets do not exactly match the released order"
        )
    if len(released) != EXPECTED_TEST_SEED_COUNT:
        raise ValueError("held-out suite requires exactly 40 released seeds")
    if len(bundle.selections) != EXPECTED_SELECTED_PAIR_COUNT:
        raise ValueError("held-out suite requires exactly 12 selected pairs")
    if len(bundle.exclusions) != EXPECTED_EXCLUSION_PAIR_COUNT:
        raise ValueError("held-out suite requires exactly 8 exclusions")

    clustering_rows = evaluate_clustering_suite(datasets, bundle)
    clustering_analysis = build_clustering_analysis(clustering_rows, bundle)
    product_selection = bundle.selection_for(
        REFERENCE_METHOD,
        "benchmark_label_aware",
    )
    factorial = build_factorial_section(
        datasets,
        product_selection=product_selection,
    )
    priority = build_priority_section(datasets)
    dispatch = build_dispatch_section(datasets)

    selected_failures = sum(
        row["status"] == "failed"
        for seed_row in clustering_rows
        for row in seed_row["methods"]
    )
    scientific_seed_failures = (
        len(factorial["seed_failures"])
        + len(priority["seed_failures"])
        + len(dispatch["seed_failures"])
    )
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": "exp23_heldout_evaluation",
        "stage": STAGE,
        "status": (
            "succeeded"
            if selected_failures == 0 and scientific_seed_failures == 0
            else "complete_with_retained_failures"
        ),
        "scientific_scope": (
            "synthetic methodological held-out evaluation; no field-effectiveness "
            "or expert-validated policy claim"
        ),
        "protocol": {
            **dict(provenance),
            "test_release": {
                "seeds": list(released),
                "seed_count": len(released),
                "dataset_loader_invocations": len(datasets),
                "unique_dataset_files_loaded": len(
                    {dataset.source_sha256 for dataset in datasets}
                ),
                "candidate_suite_invocations": 1,
                "method_or_seed_filter_available": False,
                "resume_available": False,
            },
        },
        "method_track_registry": _bundle_registry(bundle),
        "clustering": {
            "per_seed_rows": clustering_rows,
            **clustering_analysis,
        },
        "factorial_ablation": factorial,
        "priority_robustness": priority,
        "dispatch_outcomes": dispatch,
        "retention_policy": {
            "calibration_exclusions_retained": True,
            "prediction_failures_retained": True,
            "factorial_failures_and_unmatched_cells_retained": True,
            "priority_failures_adverse_results_and_ties_retained": True,
            "dispatch_failures_adverse_results_and_ties_retained": True,
            "complete_case_seed_dropping_forbidden": True,
            "selected_prediction_failure_count": selected_failures,
            "scientific_seed_failure_count": scientific_seed_failures,
        },
        "validation": {
            "status": "pass",
            "expected_seed_count": EXPECTED_TEST_SEED_COUNT,
            "observed_seed_count": len(clustering_rows),
            "expected_selected_method_seed_rows": (
                EXPECTED_TEST_SEED_COUNT * EXPECTED_SELECTED_PAIR_COUNT
            ),
            "observed_selected_method_seed_rows": sum(
                row["status"] != "no_feasible_candidate"
                for seed_row in clustering_rows
                for row in seed_row["methods"]
            ),
            "expected_exclusion_seed_rows": (
                EXPECTED_TEST_SEED_COUNT * EXPECTED_EXCLUSION_PAIR_COUNT
            ),
            "observed_exclusion_seed_rows": sum(
                row["status"] == "no_feasible_candidate"
                for seed_row in clustering_rows
                for row in seed_row["methods"]
            ),
            "validation_errors": [],
        },
    }
    result["artifact_content_sha256"] = _artifact_content_sha256(result)
    return result


def _assert_equal(observed: Any, expected: Any, *, label: str) -> None:
    if observed != expected:
        raise ValueError(f"held-out validation mismatch: {label}")


def validate_result(
    result: Mapping[str, Any],
    bundle: SelectedConfigBundle,
    *,
    released_seeds: Sequence[int],
) -> dict[str, Any]:
    """Independently recompute structure and inference from retained rows."""

    if result.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported held-out result schema")
    recorded_hash = result.get("artifact_content_sha256")
    if (
        not isinstance(recorded_hash, str)
        or len(recorded_hash) != 64
        or recorded_hash != _artifact_content_sha256(result)
    ):
        raise ValueError("held-out artifact content checksum mismatch")
    validation = result.get("validation")
    if (
        not isinstance(validation, Mapping)
        or validation.get("status") != "pass"
        or validation.get("validation_errors") != []
    ):
        raise ValueError("held-out artifact does not report a clean validation")
    _assert_equal(
        result.get("method_track_registry"),
        _bundle_registry(bundle),
        label="method-track registry",
    )
    released = tuple(int(seed) for seed in released_seeds)
    if len(released) != EXPECTED_TEST_SEED_COUNT:
        raise ValueError("validator requires the complete 40-seed test release")
    protocol = result.get("protocol")
    if not isinstance(protocol, Mapping):
        raise ValueError("held-out protocol record is absent")
    release = protocol.get("test_release")
    if not isinstance(release, Mapping):
        raise ValueError("held-out test-release audit is absent")
    expected_release = {
        "seeds": list(released),
        "seed_count": EXPECTED_TEST_SEED_COUNT,
        "dataset_loader_invocations": EXPECTED_TEST_SEED_COUNT,
        "unique_dataset_files_loaded": EXPECTED_TEST_SEED_COUNT,
        "candidate_suite_invocations": 1,
        "method_or_seed_filter_available": False,
        "resume_available": False,
    }
    _assert_equal(release, expected_release, label="test release audit")

    clustering = result.get("clustering")
    if not isinstance(clustering, Mapping):
        raise ValueError("held-out clustering section is absent")
    seed_rows = clustering.get("per_seed_rows")
    if not isinstance(seed_rows, list):
        raise ValueError("held-out per-seed rows are absent")
    if [row.get("seed") for row in seed_rows] != list(released):
        raise ValueError("held-out per-seed rows do not match the release order")

    selected = _selection_map(bundle)
    excluded = {
        (row.method_id, row.track_id): row for row in bundle.exclusions
    }
    expected_pairs = set(selected) | set(excluded)
    dataset_hashes: set[str] = set()
    common_manifest_hashes: set[str] = set()
    common_gate1_manifests: set[str] = set()
    selected_row_count = 0
    excluded_row_count = 0
    selected_failure_count = 0
    for seed_row in seed_rows:
        methods = seed_row.get("methods")
        if not isinstance(methods, list):
            raise ValueError("held-out seed has no method rows")
        identities = [
            (row.get("method_id"), row.get("track_id")) for row in methods
        ]
        if set(identities) != expected_pairs or len(identities) != len(
            expected_pairs
        ):
            raise ValueError("held-out seed does not cover every method/track pair")
        n_points = seed_row.get("n_points")
        if (
            isinstance(n_points, bool)
            or not isinstance(n_points, int)
            or n_points < 1
        ):
            raise ValueError("held-out seed has an invalid point count")
        dataset_sha = seed_row.get("dataset_sha256")
        manifest_sha = seed_row.get("dataset_manifest_sha256")
        gate1_manifest_sha = seed_row.get("gate1_manifest_sha256")
        if not all(
            isinstance(value, str) and len(value) == 64
            for value in (dataset_sha, manifest_sha, gate1_manifest_sha)
        ):
            raise ValueError("held-out seed has malformed dataset provenance")
        dataset_hashes.add(dataset_sha)
        common_manifest_hashes.add(manifest_sha)
        common_gate1_manifests.add(gate1_manifest_sha)
        for row in methods:
            identity = (row["method_id"], row["track_id"])
            if row.get("method") != _pair_id(*identity):
                raise ValueError("held-out method row has a malformed pair id")
            if row.get("n_points") != n_points:
                raise ValueError("held-out method point count is inconsistent")
            if identity in excluded:
                excluded_row_count += 1
                expected = excluded[identity]
                if (
                    row.get("status") != "no_feasible_candidate"
                    or row.get("predicted_labels") is not None
                    or row.get("prediction_sha256") is not None
                    or row.get("metrics") is not None
                    or row.get("selection", {}).get(
                        "source_selection_sha256"
                    )
                    != expected.source_selection_sha256
                ):
                    raise ValueError("calibration exclusion was altered at test")
                continue

            selected_row_count += 1
            expected = selected[identity]
            selection = row.get("selection")
            if not isinstance(selection, Mapping):
                raise ValueError("selected method row has no selection identity")
            if (
                selection.get("config") != dict(expected.config)
                or selection.get("config_sha256") != expected.config_sha256
                or selection.get("source_artifact_id")
                != expected.source_artifact_id
                or selection.get("source_selection_sha256")
                != expected.source_selection_sha256
            ):
                raise ValueError("selected method configuration changed at test")
            status = row.get("status")
            if status == "failed":
                selected_failure_count += 1
                if (
                    row.get("predicted_labels") is not None
                    or not isinstance(row.get("error"), Mapping)
                ):
                    raise ValueError("failed prediction row is not retained exactly")
                continue
            if status != "succeeded":
                raise ValueError("selected method has an unsupported test status")
            labels = row.get("predicted_labels")
            if (
                not isinstance(labels, list)
                or len(labels) != n_points
                or any(
                    isinstance(label, bool) or not isinstance(label, Integral)
                    for label in labels
                )
            ):
                raise ValueError("succeeded prediction labels are malformed")
            if row.get("prediction_sha256") != _prediction_sha256(labels):
                raise ValueError("succeeded prediction checksum mismatch")
            counts: dict[str, int] = {}
            for label in labels:
                counts[str(int(label))] = counts.get(str(int(label)), 0) + 1
            if row.get("prediction_label_counts") != counts:
                raise ValueError("succeeded prediction label counts mismatch")
            metrics = row.get("metrics")
            ari_denominator = (
                metrics.get("ari_labeled_reports", {}).get("denominator")
                if isinstance(metrics, Mapping)
                else None
            )
            if (
                not isinstance(metrics, Mapping)
                or metrics.get("all_metrics_complete") is not True
                or metrics.get("coverage", {}).get("point_coverage_rate") != 1.0
                or metrics.get("n_points") != n_points
                or isinstance(ari_denominator, bool)
                or not isinstance(ari_denominator, int)
                or not 0 <= ari_denominator <= n_points
            ):
                raise ValueError("succeeded prediction metrics are incomplete")

    if (
        len(dataset_hashes) != EXPECTED_TEST_SEED_COUNT
        or len(common_manifest_hashes) != 1
        or len(common_gate1_manifests) != 1
    ):
        raise ValueError("held-out dataset identities are incomplete or inconsistent")
    if selected_row_count != (
        EXPECTED_TEST_SEED_COUNT * EXPECTED_SELECTED_PAIR_COUNT
    ):
        raise ValueError("held-out selected-row count mismatch")
    if excluded_row_count != (
        EXPECTED_TEST_SEED_COUNT * EXPECTED_EXCLUSION_PAIR_COUNT
    ):
        raise ValueError("held-out exclusion-row count mismatch")

    recomputed_clustering = build_clustering_analysis(seed_rows, bundle)
    for key, expected in recomputed_clustering.items():
        _assert_equal(clustering.get(key), expected, label=f"clustering.{key}")

    factorial = result.get("factorial_ablation")
    if not isinstance(factorial, Mapping):
        raise ValueError("held-out factorial section is absent")
    factorial_seed_failures = factorial.get("seed_failures")
    if not isinstance(factorial_seed_failures, list):
        raise ValueError("factorial seed-failure ledger is absent")
    for section_name, factors, outcome, variants in (
        (
            "clustering",
            CLUSTERING_FACTORS,
            "ari_labeled_reports",
            16,
        ),
        (
            "priority",
            PRIORITY_FACTORS,
            "priority_rank_correlation",
            8,
        ),
    ):
        section = factorial.get(section_name)
        if not isinstance(section, Mapping):
            raise ValueError(f"factorial {section_name} section is absent")
        rows = section.get("rows")
        if not isinstance(rows, list):
            raise ValueError(f"factorial {section_name} rows are absent")
        expected_count = EXPECTED_TEST_SEED_COUNT * variants
        if section.get("expected_evaluation_count") != expected_count:
            raise ValueError(f"factorial {section_name} expected count mismatch")
        failed = [row for row in rows if row.get("status") != "succeeded"]
        complete = (
            not factorial_seed_failures
            and not failed
            and len(rows) == expected_count
        )
        expected_effects = (
            factorial_effect_summaries(
                rows,
                factors=factors,
                outcome=outcome,
            )
            if complete
            else []
        )
        _assert_equal(
            section.get("effects"),
            expected_effects,
            label=f"factorial.{section_name}.effects",
        )

    priority = result.get("priority_robustness")
    if not isinstance(priority, Mapping):
        raise ValueError("held-out priority section is absent")
    priority_rows = priority.get("scenario_rows")
    if not isinstance(priority_rows, list):
        raise ValueError("priority scenario rows are absent")
    expected_seed_aggregates = _seed_aggregates(priority_rows)
    expected_priority_effects = (
        _paired_estimator_effects(expected_seed_aggregates)
        if expected_seed_aggregates
        else []
    )
    _assert_equal(
        priority.get("seed_aggregates"),
        expected_seed_aggregates,
        label="priority.seed_aggregates",
    )
    _assert_equal(
        priority.get("summaries"),
        _summaries(expected_seed_aggregates)
        if expected_seed_aggregates
        else [],
        label="priority.summaries",
    )
    _assert_equal(
        priority.get("paired_estimator_effects"),
        expected_priority_effects,
        label="priority.paired_estimator_effects",
    )

    dispatch = result.get("dispatch_outcomes")
    if not isinstance(dispatch, Mapping):
        raise ValueError("held-out dispatch section is absent")
    dispatch_rows = dispatch.get("per_seed_resource_policy_rows")
    if not isinstance(dispatch_rows, list):
        raise ValueError("dispatch rows are absent")
    expected_dispatch_comparisons = (
        _paired_policy_comparisons(dispatch_rows) if dispatch_rows else []
    )
    _assert_equal(
        dispatch.get("summary"),
        _summary(dispatch_rows) if dispatch_rows else [],
        label="dispatch.summary",
    )
    _assert_equal(
        dispatch.get("paired_policy_comparisons"),
        expected_dispatch_comparisons,
        label="dispatch.paired_policy_comparisons",
    )

    retention = result.get("retention_policy")
    if (
        not isinstance(retention, Mapping)
        or retention.get("selected_prediction_failure_count")
        != selected_failure_count
        or any(
            retention.get(field) is not True
            for field in (
                "calibration_exclusions_retained",
                "prediction_failures_retained",
                "factorial_failures_and_unmatched_cells_retained",
                "priority_failures_adverse_results_and_ties_retained",
                "dispatch_failures_adverse_results_and_ties_retained",
                "complete_case_seed_dropping_forbidden",
            )
        )
    ):
        raise ValueError("held-out retention audit is inconsistent")
    return {
        "status": "pass",
        "artifact_content_sha256": recorded_hash,
        "seed_count": len(seed_rows),
        "selected_method_seed_rows": selected_row_count,
        "exclusion_seed_rows": excluded_row_count,
        "selected_prediction_failures": selected_failure_count,
        "validation_errors": [],
    }


def _pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _resolve_pointer(document: Any, pointer: str) -> Any:
    if not pointer.startswith("/"):
        raise ValueError("selector JSON pointer must start with '/'")
    value = document
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            if not token.isdigit():
                raise ValueError(f"selector list token is not an index: {token}")
            value = value[int(token)]
        elif isinstance(value, Mapping) and token in value:
            value = value[token]
        else:
            raise ValueError(f"selector pointer is unresolved: {pointer}")
    return value


def build_selectors(result: Mapping[str, Any]) -> dict[str, Any]:
    selectors: list[dict[str, str]] = []
    clustering = result["clustering"]
    for track_id, methods in clustering["method_summaries"].items():
        for method_id, endpoints in methods.items():
            for endpoint_id in endpoints:
                selectors.append(
                    {
                        "id": (
                            f"clustering.summary.{track_id}."
                            f"{method_id}.{endpoint_id}"
                        ),
                        "kind": "method_endpoint_summary",
                        "json_pointer": (
                            "/clustering/method_summaries/"
                            f"{_pointer_escape(track_id)}/"
                            f"{_pointer_escape(method_id)}/"
                            f"{_pointer_escape(endpoint_id)}"
                        ),
                    }
                )
    for track_id, candidates in clustering["paired_comparisons"].items():
        for method_id, endpoints in candidates.items():
            for endpoint_id in endpoints:
                selectors.append(
                    {
                        "id": (
                            f"clustering.paired.{track_id}."
                            f"{method_id}.vs.{REFERENCE_METHOD}.{endpoint_id}"
                        ),
                        "kind": "paired_method_comparison",
                        "json_pointer": (
                            "/clustering/paired_comparisons/"
                            f"{_pointer_escape(track_id)}/"
                            f"{_pointer_escape(method_id)}/"
                            f"{_pointer_escape(endpoint_id)}"
                        ),
                    }
                )
    for section_name in ("clustering", "priority"):
        effects = result["factorial_ablation"][section_name]["effects"]
        for index, row in enumerate(effects):
            selectors.append(
                {
                    "id": (
                        f"factorial.{section_name}."
                        f"{row['effect_id']}"
                    ),
                    "kind": "factorial_effect",
                    "json_pointer": (
                        f"/factorial_ablation/{section_name}/effects/{index}"
                    ),
                }
            )
    for index, row in enumerate(result["priority_robustness"]["summaries"]):
        selectors.append(
            {
                "id": (
                    "priority.summary."
                    f"{row['scenario']}.{row['estimator']}"
                ),
                "kind": "priority_robustness_summary",
                "json_pointer": f"/priority_robustness/summaries/{index}",
            }
        )
    for index, row in enumerate(
        result["priority_robustness"]["paired_estimator_effects"]
    ):
        selectors.append(
            {
                "id": (
                    "priority.paired."
                    f"{row['scenario']}.{row['metric']}"
                ),
                "kind": "priority_robustness_comparison",
                "json_pointer": (
                    "/priority_robustness/paired_estimator_effects/"
                    f"{index}"
                ),
            }
        )
    for index, row in enumerate(result["dispatch_outcomes"]["summary"]):
        selectors.append(
            {
                "id": (
                    "dispatch.summary."
                    f"{row['resource_scenario']}.{row['policy']}"
                ),
                "kind": "dispatch_summary",
                "json_pointer": f"/dispatch_outcomes/summary/{index}",
            }
        )
    for index, row in enumerate(
        result["dispatch_outcomes"]["paired_policy_comparisons"]
    ):
        selectors.append(
            {
                "id": (
                    "dispatch.paired."
                    f"{row['resource_scenario']}."
                    f"{row['candidate_policy']}.vs."
                    f"{row['comparator_policy']}.{row['endpoint']}"
                ),
                "kind": "dispatch_comparison",
                "json_pointer": (
                    "/dispatch_outcomes/paired_policy_comparisons/"
                    f"{index}"
                ),
            }
        )
    selector_ids = [row["id"] for row in selectors]
    if len(selector_ids) != len(set(selector_ids)):
        raise ValueError("held-out selector ids are not unique")
    payload: dict[str, Any] = {
        "schema_version": SELECTOR_SCHEMA_VERSION,
        "source_schema_version": result["schema_version"],
        "source_artifact_content_sha256": result[
            "artifact_content_sha256"
        ],
        "selectors": selectors,
        "selector_count": len(selectors),
    }
    payload["selector_content_sha256"] = sha256_bytes(
        _canonical_json_bytes(payload)
    )
    return payload


def validate_selectors(
    selectors: Mapping[str, Any],
    result: Mapping[str, Any],
) -> dict[str, Any]:
    if selectors.get("schema_version") != SELECTOR_SCHEMA_VERSION:
        raise ValueError("unsupported held-out selector schema")
    content = dict(selectors)
    recorded = content.pop("selector_content_sha256", None)
    if (
        not isinstance(recorded, str)
        or len(recorded) != 64
        or recorded != sha256_bytes(_canonical_json_bytes(content))
    ):
        raise ValueError("held-out selector content checksum mismatch")
    if selectors.get("source_artifact_content_sha256") != result.get(
        "artifact_content_sha256"
    ):
        raise ValueError("selectors do not bind the held-out artifact")
    rows = selectors.get("selectors")
    if (
        not isinstance(rows, list)
        or selectors.get("selector_count") != len(rows)
        or len({row.get("id") for row in rows if isinstance(row, Mapping)})
        != len(rows)
    ):
        raise ValueError("held-out selector registry is malformed")
    for row in rows:
        if (
            not isinstance(row, Mapping)
            or not isinstance(row.get("id"), str)
            or not isinstance(row.get("kind"), str)
            or not isinstance(row.get("json_pointer"), str)
        ):
            raise ValueError("held-out selector row is malformed")
        _resolve_pointer(result, row["json_pointer"])
    return {
        "status": "pass",
        "selector_count": len(rows),
        "selector_content_sha256": recorded,
    }


def _exclusive_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    )
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(payload)
    except FileExistsError as exc:
        raise RuntimeError(f"refusing to overwrite held-out artifact: {path}") from exc


def _candidate_directories() -> tuple[str, Path, Path]:
    run_id = os.environ.get("DEMO_RUN_ID")
    artifact_raw = os.environ.get("DEMO_ARTIFACT_DIR")
    tables_raw = os.environ.get("DEMO_TABLES_DIR")
    if not run_id or not artifact_raw or not tables_raw:
        raise RuntimeError(
            "held-out evaluation must run through the immutable candidate runner"
        )
    artifact = Path(artifact_raw).resolve()
    tables = Path(tables_raw).resolve()
    if tables != artifact / "tables":
        raise RuntimeError("candidate tables directory is not the run-local directory")
    return run_id, artifact, tables


def run_once(*, dataset_root: Path | str | None = None) -> tuple[Path, Path]:
    """Authorize, record, execute, validate, and exclusively write one X0 run."""

    run_id, artifact_dir, tables_dir = _candidate_directories()
    bundle = load_selected_configs(
        DEFAULT_SELECTED_CONFIGS,
        gate2_lock=DEFAULT_GATE2_LOCK,
        protocol_dir=DEFAULT_PROTOCOL_DIR,
        artifact_root=REPOSITORY_ROOT,
    )
    released = load_locked_test_seeds(
        DEFAULT_GATE2_LOCK,
        DEFAULT_PROTOCOL_DIR,
    )
    authorization = load_x0_authorization(released_seeds=released)
    frozen_root, frozen_record = resolve_frozen_dataset_root(
        dataset_root,
        gate1_lock=DEFAULT_GATE1_LOCK,
    )
    provenance = build_provenance_record()
    provenance["frozen_dataset_root"] = frozen_record
    provenance["x0_authorization"] = {
        "path": DEFAULT_X0_RELEASE.relative_to(REPOSITORY_ROOT).as_posix(),
        "sha256": file_sha256(DEFAULT_X0_RELEASE),
        "authorization_content_sha256": authorization[
            "authorization_content_sha256"
        ],
        "maximum_candidate_suite_invocations": 1,
    }

    invocation = {
        "schema_version": "x0-invocation-v1",
        "run_id": run_id,
        "status": "authorized_pre_read",
        "command": list(sys.argv),
        "gate2_lock_sha256": file_sha256(DEFAULT_GATE2_LOCK),
        "selected_configs_sha256": file_sha256(DEFAULT_SELECTED_CONFIGS),
        "x0_authorization_sha256": file_sha256(DEFAULT_X0_RELEASE),
        "authorization_content_sha256": authorization[
            "authorization_content_sha256"
        ],
        "released_seed_count": len(released),
        "released_seed_sha256": sha256_bytes(
            _canonical_json_bytes(list(released))
        ),
        "dataset_root": str(frozen_root),
        "candidate_suite_invocation": 1,
        "seed_or_method_filter": None,
        "resume": False,
    }
    _exclusive_json(artifact_dir / "work" / "x0-invocation.json", invocation)

    # This is the only block in the repository that opens the released test
    # files.  Each seed appears exactly once and no intermediate result is
    # written or returned before the complete suite has been loaded.
    datasets = tuple(
        load_evaluation_dataset(
            frozen_root,
            seed=seed,
            gate2_lock=DEFAULT_GATE2_LOCK,
            gate1_lock=DEFAULT_GATE1_LOCK,
            protocol_dir=DEFAULT_PROTOCOL_DIR,
            repository_root=REPOSITORY_ROOT,
        )
        for seed in released
    )
    result = build_result(
        datasets,
        bundle,
        released_seeds=released,
        provenance=provenance,
    )
    validation = validate_result(result, bundle, released_seeds=released)
    if validation["status"] != "pass":
        raise RuntimeError("held-out self-validation did not pass")
    selectors = build_selectors(result)
    validate_selectors(selectors, result)

    result_path = tables_dir / RESULT_NAME
    selector_path = tables_dir / SELECTOR_NAME
    _exclusive_json(result_path, result)
    _exclusive_json(selector_path, selectors)
    return result_path, selector_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-root",
        type=Path,
        help=(
            "accepted Gate-1 work/datasets root; no seed, method, track, "
            "resume, or output filter is supported"
        ),
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    result_path, selector_path = run_once(dataset_root=args.dataset_root)
    print(f"exp23 wrote complete held-out result to {result_path}")
    print(f"exp23 wrote selector registry to {selector_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ENDPOINTS",
    "DEFAULT_X0_RELEASE",
    "RESULT_NAME",
    "SCHEMA_VERSION",
    "SELECTOR_NAME",
    "build_clustering_analysis",
    "build_result",
    "build_selectors",
    "evaluate_clustering_suite",
    "evaluate_selected_pair",
    "load_x0_authorization",
    "run_once",
    "validate_result",
    "validate_selectors",
]
