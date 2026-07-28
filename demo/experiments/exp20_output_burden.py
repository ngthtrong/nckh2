"""Experiment 20: incident integrity, noise, and operator-output burden.

This pre-Gate-2 experiment can load only the development or calibration view
exposed by :mod:`demo.experiments.protocol`.  Method runners receive sanitized
``Event`` objects only; evaluator labels and scenario families are joined after
prediction.  Failed methods, unfavorable paired differences, and ties remain
in the JSON artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import asdict, dataclass, replace
from numbers import Integral
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, Sequence

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from demo.experiments.calibration import TuningDataset, load_tuning_dataset
from demo.experiments.inference import (
    apply_holm,
    descriptive_summary,
    paired_comparison,
)
from demo.experiments.protocol import TuningProtocol, load_tuning_protocol
from demo.pipeline.attributes import Event
from demo.pipeline.baselines import run_dbscan
from demo.pipeline.clustering import run_louvain
from demo.pipeline.config import DEFAULT_CONFIG
from demo.pipeline.metrics import (
    ReviewPolicy,
    evaluate_output_burden,
    incident_split_loss,
)
from demo.pipeline.weighting import build_weight_matrix, sparsify


DEMO_ROOT = Path(__file__).resolve().parents[1]
RESULT_NAME = "exp20_output_burden.json"
SELECTOR_NAME = "exp20_output_burden_selectors.json"
Stage = Literal["development", "calibration"]
MethodRunner = Callable[[Sequence[Event]], Sequence[int]]


# Locked in source before final evaluation.  No policy is selected post hoc.
PREREGISTERED_REVIEW_POLICIES: tuple[ReviewPolicy, ...] = (
    ReviewPolicy(
        id="conservative",
        min_destination_reports=3,
        min_mean_confidence=0.75,
    ),
    ReviewPolicy(
        id="standard",
        min_destination_reports=2,
        min_mean_confidence=0.50,
    ),
    ReviewPolicy(
        id="permissive",
        min_destination_reports=1,
        min_mean_confidence=0.25,
    ),
)


@dataclass(frozen=True)
class MethodSpec:
    """One deterministic diagnostic method and its noise-label convention."""

    id: str
    runner: MethodRunner
    noise_label: int | None
    description: str
    configuration: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("method id must be a non-empty string")
        if not callable(self.runner):
            raise ValueError("method runner must be callable")
        if self.noise_label is not None and (
            isinstance(self.noise_label, bool)
            or not isinstance(self.noise_label, int)
        ):
            raise ValueError("method noise_label must be an integer or None")
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("method description must be a non-empty string")
        if self.configuration is not None:
            try:
                encoded = json.dumps(
                    dict(self.configuration),
                    sort_keys=True,
                    allow_nan=False,
                )
                decoded = json.loads(encoded)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "method configuration must be finite JSON data"
                ) from exc
            if not isinstance(decoded, dict):
                raise ValueError("method configuration must be an object")


def _product_louvain(events: Sequence[Event]) -> Sequence[int]:
    matrix = build_weight_matrix(list(events), DEFAULT_CONFIG.weight, mode="gating")
    sparse = sparsify(matrix, DEFAULT_CONFIG.weight)
    return run_louvain(
        sparse,
        resolution=DEFAULT_CONFIG.cluster.resolution,
        random_state=DEFAULT_CONFIG.cluster.random_state,
    )


def _additive_louvain(events: Sequence[Event]) -> Sequence[int]:
    matrix = build_weight_matrix(
        list(events),
        DEFAULT_CONFIG.weight,
        mode="additive",
    )
    sparse = sparsify(matrix, DEFAULT_CONFIG.weight)
    return run_louvain(
        sparse,
        resolution=DEFAULT_CONFIG.cluster.resolution,
        random_state=DEFAULT_CONFIG.cluster.random_state,
    )


def _dbscan_geo_context(events: Sequence[Event]) -> Sequence[int]:
    return run_dbscan(
        list(events),
        eps=0.5,
        min_samples=3,
        features="geo_context",
    )


DEFAULT_METHODS: tuple[MethodSpec, ...] = (
    MethodSpec(
        id="product_louvain",
        runner=_product_louvain,
        noise_label=None,
        description="product similarity plus Louvain; no predicted-noise label",
        configuration={
            "status": "fixed_development_diagnostic",
            "weight_mode": "gating",
            "weight": asdict(DEFAULT_CONFIG.weight),
            "cluster": asdict(DEFAULT_CONFIG.cluster),
        },
    ),
    MethodSpec(
        id="additive_louvain",
        runner=_additive_louvain,
        noise_label=None,
        description="additive similarity plus Louvain; no predicted-noise label",
        configuration={
            "status": "fixed_development_diagnostic",
            "weight_mode": "additive",
            "weight": asdict(DEFAULT_CONFIG.weight),
            "cluster": asdict(DEFAULT_CONFIG.cluster),
        },
    ),
    MethodSpec(
        id="dbscan_geo_context",
        runner=_dbscan_geo_context,
        noise_label=-1,
        description="direct density baseline with an explicit predicted-noise label",
        configuration={
            "status": "fixed_development_diagnostic",
            "features": "geo_context",
            "eps": 0.5,
            "min_samples": 3,
        },
    ),
)


@dataclass(frozen=True)
class EndpointSpec:
    id: str
    family: str
    direction: Literal["higher", "lower"]
    value_path: tuple[str, ...]
    denominator_path: tuple[str, ...]


def _endpoint_specs(policies: Sequence[ReviewPolicy]) -> tuple[EndpointSpec, ...]:
    fixed = (
        EndpointSpec(
            "incident_split_loss",
            "incident_integrity",
            "lower",
            ("metrics", "incident_split_loss", "rate"),
            ("metrics", "incident_split_loss", "denominator"),
        ),
        EndpointSpec(
            "incident_merge_loss",
            "incident_integrity",
            "lower",
            ("metrics", "incident_merge_loss", "rate"),
            ("metrics", "incident_merge_loss", "denominator"),
        ),
        EndpointSpec(
            "noise_rejection_rate",
            "noise_handling",
            "higher",
            ("metrics", "noise_rejection_rate", "rate"),
            ("metrics", "noise_rejection_rate", "denominator"),
        ),
        EndpointSpec(
            "noise_absorption_rate",
            "noise_handling",
            "lower",
            ("metrics", "noise_absorption_rate", "rate"),
            ("metrics", "noise_absorption_rate", "denominator"),
        ),
        EndpointSpec(
            "false_operational_destinations",
            "operational_burden",
            "lower",
            ("metrics", "false_operational_destinations", "count"),
            ("metrics", "false_operational_destinations", "denominator"),
        ),
    )
    policy_endpoints = tuple(
        EndpointSpec(
            f"operator_review_burden.{policy.id}",
            "operational_burden",
            "lower",
            (
                "metrics",
                "operator_review_burden",
                policy.id,
                "queue_size",
            ),
            (
                "metrics",
                "operator_review_burden",
                policy.id,
                "denominator",
            ),
        )
        for policy in policies
    )
    return fixed + policy_endpoints


def _nested(source: Mapping[str, Any], path: Sequence[str]) -> Any:
    value: Any = source
    for key in path:
        if not isinstance(value, Mapping) or key not in value:
            raise KeyError(".".join(path))
        value = value[key]
    return value


def _prediction_sha256(labels: Sequence[int]) -> str:
    encoded = json.dumps(
        list(labels),
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _family_by_ground_truth(
    incidents: Sequence[Mapping[str, Any]],
) -> dict[int, str]:
    result: dict[int, str] = {}
    for index, incident in enumerate(incidents):
        if not isinstance(incident, Mapping):
            raise ValueError(f"incident {index} is not an object")
        gt = incident.get("gt_cluster")
        family = incident.get("scenario_family")
        if (
            isinstance(gt, bool)
            or not isinstance(gt, int)
            or gt < 0
            or not isinstance(family, str)
            or not family
        ):
            raise ValueError(f"incident {index} has invalid gt/family identity")
        if gt in result:
            raise ValueError(f"duplicate incident ground-truth label: {gt}")
        result[gt] = family
    return result


def _family_metrics(
    labels: Sequence[int],
    truth: Sequence[int],
    family_lookup: Mapping[int, str],
    *,
    noise_label: int | None,
) -> list[dict[str, Any]]:
    missing = sorted({label for label in truth if label >= 0 and label not in family_lookup})
    if missing:
        raise ValueError(f"ground-truth labels have no incident family: {missing}")
    rows: list[dict[str, Any]] = []
    destinations: dict[int, list[int]] = {}
    unclustered: list[int] = []
    for index, label in enumerate(labels):
        if noise_label is not None and label == noise_label:
            unclustered.append(index)
        else:
            destinations.setdefault(label, []).append(index)
    unclustered_set = set(unclustered)
    for family in sorted(set(family_lookup.values())):
        indices = [
            index
            for index, gt in enumerate(truth)
            if gt >= 0 and family_lookup[gt] == family
        ]
        family_labels = [labels[index] for index in indices]
        family_truth = [truth[index] for index in indices]
        split = incident_split_loss(
            family_labels,
            family_truth,
            noise_label=noise_label,
        )
        family_destinations = [
            members
            for members in destinations.values()
            if any(
                truth[index] >= 0
                and family_lookup[truth[index]] == family
                for index in members
            )
        ]
        merged_destinations = sum(
            len({truth[index] for index in members if truth[index] >= 0}) >= 2
            for members in family_destinations
        )
        merge_denominator = len(family_destinations)
        merge = {
            "metric": "incident_merge_loss",
            "direction": "lower",
            "numerator": merged_destinations,
            "denominator": merge_denominator,
            "rate": (
                float(merged_destinations / merge_denominator)
                if merge_denominator
                else None
            ),
            "coverage": {
                "points_total": len(labels),
                "points_accounted": len(labels),
                "point_coverage_rate": 1.0,
                "population_points_total": len(indices),
                "population_points_accounted": len(indices),
                "population_coverage_rate": 1.0,
                "complete": True,
            },
            "details": {
                "definition": (
                    "destinations touched by this family that contain at least "
                    "two incidents, including cross-family merges"
                ),
                "n_family_destinations": merge_denominator,
                "n_family_reports_unclustered": sum(
                    index in unclustered_set for index in indices
                ),
                "noise_label_is_destination": False,
            },
        }
        rows.append(
            {
                "family": family,
                "n_reports": len(indices),
                "n_incidents": split["denominator"],
                "incident_split_loss": split,
                "incident_merge_loss": merge,
                "point_coverage_rate": 1.0,
            }
        )
    return rows


def evaluate_method(
    dataset: TuningDataset,
    method: MethodSpec,
    policies: Sequence[ReviewPolicy] = PREREGISTERED_REVIEW_POLICIES,
) -> dict[str, Any]:
    """Run a method on the inference view, then join evaluator-only outcomes."""

    try:
        method_events = tuple(replace(event) for event in dataset.events)
        if any(
            event.gt_cluster != -1 or event.is_fake is not False
            for event in method_events
        ):
            raise ValueError("evaluator-only fields leaked into method inputs")
        raw_labels = method.runner(method_events)
        labels = list(raw_labels)
        if len(labels) != len(dataset.events):
            raise ValueError(
                "prediction length does not match reports: "
                f"{len(labels)} != {len(dataset.events)}"
            )
        if any(
            isinstance(label, bool) or not isinstance(label, Integral)
            for label in labels
        ):
            raise ValueError("predicted labels must all be integers")
        labels = [int(label) for label in labels]
        if dataset.ground_truth is None:
            raise ValueError(
                "output-burden evaluation requires the restricted evaluator view"
            )
        if len(dataset.ground_truth) != len(dataset.events):
            raise ValueError("ground truth is not aligned with inference events")
        if any(
            event.gt_cluster != -1 or event.is_fake is not False
            for event in method_events
        ):
            raise ValueError("method mutated evaluator-isolation sentinels")
        scores = [float(event.confidence) for event in dataset.events]
        metrics = evaluate_output_burden(
            labels,
            dataset.ground_truth,
            scores,
            policies,
            noise_label=method.noise_label,
        )
        family_lookup = _family_by_ground_truth(dataset.incidents)
        family_rows = _family_metrics(
            labels,
            dataset.ground_truth,
            family_lookup,
            noise_label=method.noise_label,
        )
        label_counts: dict[str, int] = {}
        for label in labels:
            label_counts[str(label)] = label_counts.get(str(label), 0) + 1
        return {
            "method": method.id,
            "status": "succeeded",
            "description": method.description,
            "configuration": (
                None
                if method.configuration is None
                else dict(method.configuration)
            ),
            "prediction_noise_label": method.noise_label,
            "n_points": len(labels),
            "prediction_sha256": _prediction_sha256(labels),
            "prediction_label_counts": label_counts,
            "predicted_labels": labels,
            "metrics": metrics,
            "family_metrics": family_rows,
            "multimodal_family_metrics": [
                row
                for row in family_rows
                if "multimodal" in row["family"].casefold()
            ],
            "error": None,
        }
    except Exception as exc:
        return {
            "method": method.id,
            "status": "failed",
            "description": method.description,
            "prediction_noise_label": method.noise_label,
            "n_points": len(dataset.events),
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


def evaluate_seed(
    dataset: TuningDataset,
    methods: Sequence[MethodSpec] = DEFAULT_METHODS,
    policies: Sequence[ReviewPolicy] = PREREGISTERED_REVIEW_POLICIES,
) -> dict[str, Any]:
    method_ids = [method.id for method in methods]
    if not method_ids or len(method_ids) != len(set(method_ids)):
        raise ValueError("method ids must be non-empty and unique")
    policy_ids = [policy.id for policy in policies]
    if not policy_ids or len(policy_ids) != len(set(policy_ids)):
        raise ValueError("review policy ids must be non-empty and unique")
    rows = [evaluate_method(dataset, method, policies) for method in methods]
    return {
        "seed": dataset.seed,
        "stage": dataset.stage,
        "dataset_sha256": dataset.source_sha256,
        "dataset_manifest_sha256": dataset.manifest_sha256,
        "n_points": len(dataset.events),
        "status": (
            "succeeded"
            if all(row["status"] == "succeeded" for row in rows)
            else "partial_failure"
        ),
        "methods": rows,
    }


def _method_row(seed_row: Mapping[str, Any], method_id: str) -> Mapping[str, Any]:
    matches = [
        row
        for row in seed_row["methods"]
        if isinstance(row, Mapping) and row.get("method") == method_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"seed {seed_row.get('seed')} has {len(matches)} rows for {method_id}"
        )
    return matches[0]


def _stable_inference_seed(identifier: str) -> int:
    digest = hashlib.sha256(identifier.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def _metric_summary(
    seed_rows: Sequence[Mapping[str, Any]],
    method_id: str,
    endpoint: EndpointSpec,
) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for seed_row in seed_rows:
        method = _method_row(seed_row, method_id)
        if method["status"] != "succeeded":
            failures.append(
                {
                    "seed": seed_row["seed"],
                    "status": "failed",
                    "error": method["error"],
                }
            )
            continue
        value = _nested(method, endpoint.value_path)
        denominator = _nested(method, endpoint.denominator_path)
        if value is None:
            failures.append(
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
        "unavailable_seeds": len(failures),
        "metric_denominator_sum": sum(row["denominator"] for row in observations),
    }
    if not observations:
        return {
            "status": "unavailable",
            "endpoint": endpoint.id,
            "direction": endpoint.direction,
            "denominator": denominator,
            "observations": observations,
            "unavailable": failures,
        }
    return {
        "status": "available",
        "endpoint": endpoint.id,
        "direction": endpoint.direction,
        **descriptive_summary(
            [row["value"] for row in observations],
            denominator=denominator,
            bootstrap_seed=_stable_inference_seed(
                f"summary:{method_id}:{endpoint.id}"
            ),
        ),
        "observations": observations,
        "unavailable": failures,
    }


def build_method_summaries(
    seed_rows: Sequence[Mapping[str, Any]],
    method_ids: Sequence[str],
    policies: Sequence[ReviewPolicy] = PREREGISTERED_REVIEW_POLICIES,
) -> dict[str, dict[str, Any]]:
    endpoints = _endpoint_specs(policies)
    return {
        method_id: {
            endpoint.id: _metric_summary(seed_rows, method_id, endpoint)
            for endpoint in endpoints
        }
        for method_id in method_ids
    }


def _paired_endpoint(
    seed_rows: Sequence[Mapping[str, Any]],
    *,
    candidate_id: str,
    comparator_id: str,
    endpoint: EndpointSpec,
) -> dict[str, Any]:
    candidate_values: list[float] = []
    comparator_values: list[float] = []
    pair_rows: list[dict[str, Any]] = []
    candidate_denominator = 0
    comparator_denominator = 0
    for seed_row in seed_rows:
        candidate = _method_row(seed_row, candidate_id)
        comparator = _method_row(seed_row, comparator_id)
        if candidate["status"] != "succeeded" or comparator["status"] != "succeeded":
            pair_rows.append(
                {
                    "seed": seed_row["seed"],
                    "status": "failed",
                    "candidate_status": candidate["status"],
                    "comparator_status": comparator["status"],
                    "candidate_error": candidate["error"],
                    "comparator_error": comparator["error"],
                }
            )
            continue
        candidate_value = _nested(candidate, endpoint.value_path)
        comparator_value = _nested(comparator, endpoint.value_path)
        if candidate_value is None or comparator_value is None:
            pair_rows.append(
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
        raw_difference = first - second
        improvement = raw_difference if endpoint.direction == "higher" else -raw_difference
        outcome = (
            "candidate_better"
            if improvement > 0.0
            else "comparator_better"
            if improvement < 0.0
            else "tie"
        )
        pair_rows.append(
            {
                "seed": seed_row["seed"],
                "status": "analyzed",
                "candidate_value": first,
                "comparator_value": second,
                "raw_difference_candidate_minus_comparator": raw_difference,
                "direction_adjusted_improvement": improvement,
                "outcome": outcome,
            }
        )
        candidate_values.append(first)
        comparator_values.append(second)
        candidate_denominator += int(_nested(candidate, endpoint.denominator_path))
        comparator_denominator += int(_nested(comparator, endpoint.denominator_path))

    denominator = {
        "expected_seed_pairs": len(seed_rows),
        "analyzed_seed_pairs": len(candidate_values),
        "unavailable_seed_pairs": len(seed_rows) - len(candidate_values),
        "candidate_metric_denominator_sum": candidate_denominator,
        "comparator_metric_denominator_sum": comparator_denominator,
    }
    if not candidate_values:
        return {
            "status": "unavailable",
            "endpoint": endpoint.id,
            "family": endpoint.family,
            "direction": endpoint.direction,
            "raw_p_value": None,
            "holm_adjusted_p_value": None,
            "denominator": denominator,
            "pairs": pair_rows,
        }
    return {
        "status": "available",
        "endpoint": endpoint.id,
        "family": endpoint.family,
        **paired_comparison(
            candidate_values,
            comparator_values,
            direction=endpoint.direction,
            denominator=denominator,
            bootstrap_seed=_stable_inference_seed(
                f"paired:{candidate_id}:{comparator_id}:{endpoint.id}"
            ),
        ),
        "pairs": pair_rows,
    }


def _holm_by_family(
    comparisons: Mapping[str, Mapping[str, Any]],
    endpoints: Sequence[EndpointSpec],
) -> dict[str, dict[str, Any]]:
    result = {identifier: dict(row) for identifier, row in comparisons.items()}
    families = ("incident_integrity", "operational_burden")
    endpoint_lookup = {endpoint.id: endpoint for endpoint in endpoints}
    for family in families:
        available = {
            identifier: row
            for identifier, row in result.items()
            if endpoint_lookup[identifier].family == family
            and row.get("status") == "available"
        }
        adjusted = apply_holm(available) if available else {}
        for identifier, row in adjusted.items():
            result[identifier] = row
    return result


def build_paired_comparisons(
    seed_rows: Sequence[Mapping[str, Any]],
    method_ids: Sequence[str],
    *,
    comparator_id: str,
    policies: Sequence[ReviewPolicy] = PREREGISTERED_REVIEW_POLICIES,
) -> dict[str, dict[str, Any]]:
    if comparator_id not in method_ids:
        raise ValueError("comparator_id is not a registered method")
    endpoints = _endpoint_specs(policies)
    output: dict[str, dict[str, Any]] = {}
    for candidate_id in method_ids:
        if candidate_id == comparator_id:
            continue
        raw = {
            endpoint.id: _paired_endpoint(
                seed_rows,
                candidate_id=candidate_id,
                comparator_id=comparator_id,
                endpoint=endpoint,
            )
            for endpoint in endpoints
        }
        output[candidate_id] = _holm_by_family(raw, endpoints)
    return output


def _family_seed_row(
    seed_row: Mapping[str, Any],
    method_id: str,
    family: str,
) -> Mapping[str, Any] | None:
    method = _method_row(seed_row, method_id)
    if method["status"] != "succeeded":
        return None
    matches = [
        row for row in method["family_metrics"] if row.get("family") == family
    ]
    if len(matches) != 1:
        return None
    return matches[0]


def build_family_tables(
    seed_rows: Sequence[Mapping[str, Any]],
    method_ids: Sequence[str],
    *,
    comparator_id: str,
) -> dict[str, Any]:
    families = sorted(
        {
            family_row["family"]
            for seed_row in seed_rows
            for method in seed_row["methods"]
            if method["status"] == "succeeded"
            for family_row in method["family_metrics"]
        }
    )
    summaries: dict[str, Any] = {}
    comparisons: dict[str, Any] = {}
    for family in families:
        summaries[family] = {}
        for method_id in method_ids:
            rows = [
                (seed_row["seed"], _family_seed_row(seed_row, method_id, family))
                for seed_row in seed_rows
            ]
            method_summary: dict[str, Any] = {}
            for endpoint_id in ("incident_split_loss", "incident_merge_loss"):
                available = [
                    (seed, row)
                    for seed, row in rows
                    if row is not None and row[endpoint_id]["rate"] is not None
                ]
                denominator = {
                    "expected_seeds": len(seed_rows),
                    "analyzed_seeds": len(available),
                    "unavailable_seeds": len(seed_rows) - len(available),
                    "metric_denominator_sum": sum(
                        row[endpoint_id]["denominator"] for _, row in available
                    ),
                }
                if available:
                    method_summary[endpoint_id] = {
                        "status": "available",
                        **descriptive_summary(
                            [row[endpoint_id]["rate"] for _, row in available],
                            denominator=denominator,
                            bootstrap_seed=_stable_inference_seed(
                                f"family-summary:{family}:{method_id}:{endpoint_id}"
                            ),
                        ),
                        "observations": [
                            {
                                "seed": seed,
                                "value": row[endpoint_id]["rate"],
                                "denominator": row[endpoint_id]["denominator"],
                            }
                            for seed, row in available
                        ],
                    }
                else:
                    method_summary[endpoint_id] = {
                        "status": "unavailable",
                        "denominator": denominator,
                        "observations": [],
                    }
            summaries[family][method_id] = method_summary

        comparisons[family] = {}
        for candidate_id in method_ids:
            if candidate_id == comparator_id:
                continue
            raw: dict[str, Any] = {}
            for endpoint_id in ("incident_split_loss", "incident_merge_loss"):
                candidate_values: list[float] = []
                comparator_values: list[float] = []
                pair_rows: list[dict[str, Any]] = []
                for seed_row in seed_rows:
                    candidate = _family_seed_row(seed_row, candidate_id, family)
                    comparator = _family_seed_row(seed_row, comparator_id, family)
                    if (
                        candidate is None
                        or comparator is None
                        or candidate[endpoint_id]["rate"] is None
                        or comparator[endpoint_id]["rate"] is None
                    ):
                        pair_rows.append(
                            {"seed": seed_row["seed"], "status": "unavailable"}
                        )
                        continue
                    first = float(candidate[endpoint_id]["rate"])
                    second = float(comparator[endpoint_id]["rate"])
                    candidate_values.append(first)
                    comparator_values.append(second)
                    improvement = second - first
                    pair_rows.append(
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
                denominator = {
                    "expected_seed_pairs": len(seed_rows),
                    "analyzed_seed_pairs": len(candidate_values),
                    "unavailable_seed_pairs": len(seed_rows) - len(candidate_values),
                }
                if candidate_values:
                    raw[endpoint_id] = {
                        "status": "available",
                        "endpoint": endpoint_id,
                        "family": "incident_integrity",
                        **paired_comparison(
                            candidate_values,
                            comparator_values,
                            direction="lower",
                            denominator=denominator,
                            bootstrap_seed=_stable_inference_seed(
                                "family-paired:"
                                f"{family}:{candidate_id}:{comparator_id}:{endpoint_id}"
                            ),
                        ),
                        "pairs": pair_rows,
                    }
                else:
                    raw[endpoint_id] = {
                        "status": "unavailable",
                        "endpoint": endpoint_id,
                        "family": "incident_integrity",
                        "raw_p_value": None,
                        "holm_adjusted_p_value": None,
                        "denominator": denominator,
                        "pairs": pair_rows,
                    }
            available = {
                endpoint_id: row
                for endpoint_id, row in raw.items()
                if row["status"] == "available"
            }
            adjusted = apply_holm(available) if available else {}
            comparisons[family][candidate_id] = {
                endpoint_id: adjusted.get(endpoint_id, row)
                for endpoint_id, row in raw.items()
            }
    multimodal_families = [
        family for family in families if "multimodal" in family.casefold()
    ]
    return {
        "families": families,
        "summaries": summaries,
        "paired_comparisons": comparisons,
        "multimodal_focus": {
            "matched_families": multimodal_families,
            "status": "available" if multimodal_families else "not_present",
            "summaries": {
                family: summaries[family] for family in multimodal_families
            },
            "paired_comparisons": {
                family: comparisons[family] for family in multimodal_families
            },
        },
    }


def _exclusive_json(path: Path, payload: Mapping[str, Any]) -> None:
    encoded = (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    try:
        with path.open("xb") as stream:
            stream.write(encoded)
    except FileExistsError as exc:
        raise FileExistsError(f"refusing to overwrite output artifact: {path}") from exc


def run(
    dataset_root: Path | str,
    *,
    stage: Stage,
    output_dir: Path | str,
    methods: Sequence[MethodSpec] = DEFAULT_METHODS,
    policies: Sequence[ReviewPolicy] = PREREGISTERED_REVIEW_POLICIES,
    tuning_protocol: TuningProtocol | None = None,
) -> tuple[Path, Path]:
    """Evaluate the complete locked tuning split and write structured JSON."""

    protocol = tuning_protocol or load_tuning_protocol()
    seeds = protocol.seeds_for(stage)
    method_ids = [method.id for method in methods]
    if not method_ids or len(method_ids) != len(set(method_ids)):
        raise ValueError("method ids must be non-empty and unique")
    if method_ids[0] != "product_louvain":
        raise ValueError("the preregistered paired comparator must be product_louvain")
    policy_ids = [policy.id for policy in policies]
    if not policy_ids or len(policy_ids) != len(set(policy_ids)):
        raise ValueError("review policy ids must be non-empty and unique")

    seed_rows: list[dict[str, Any]] = []
    for seed in seeds:
        dataset = load_tuning_dataset(
            dataset_root,
            stage=stage,
            seed=seed,
            tuning_protocol=protocol,
            calibration_labels=True,
        )
        seed_rows.append(evaluate_seed(dataset, methods, policies))

    manifest_hashes = {
        row["dataset_manifest_sha256"] for row in seed_rows
    }
    if len(manifest_hashes) != 1:
        raise ValueError(
            "tuning datasets do not share one Gate-1-bound manifest hash"
        )
    summaries = build_method_summaries(seed_rows, method_ids, policies)
    paired = build_paired_comparisons(
        seed_rows,
        method_ids,
        comparator_id=method_ids[0],
        policies=policies,
    )
    family_tables = build_family_tables(
        seed_rows,
        method_ids,
        comparator_id=method_ids[0],
    )
    failed_runs = [
        {
            "seed": seed_row["seed"],
            "method": method["method"],
            "error": method["error"],
        }
        for seed_row in seed_rows
        for method in seed_row["methods"]
        if method["status"] != "succeeded"
    ]
    payload = {
        "schema_version": "exp20-output-burden-v1",
        "experiment": "exp20_output_burden",
        "stage": stage,
        "status": "succeeded" if not failed_runs else "partial_failure",
        "protocol": {
            "protocol_sha256": protocol.protocol_sha256,
            "seed_manifest_sha256": protocol.seed_manifest_sha256,
            "metric_contract_sha256": protocol.metric_contract_sha256,
            "dataset_manifest_sha256": next(iter(manifest_hashes)),
            "seed_count": len(seeds),
        },
        "method_registry": [
            {
                "id": method.id,
                "description": method.description,
                "configuration": (
                    None
                    if method.configuration is None
                    else dict(method.configuration)
                ),
                "prediction_noise_label": method.noise_label,
            }
            for method in methods
        ],
        "review_policies": [
            {
                "id": policy.id,
                "min_destination_reports": int(policy.min_destination_reports),
                "min_mean_confidence": float(policy.min_mean_confidence),
                "review_unclustered": policy.review_unclustered,
            }
            for policy in policies
        ],
        "endpoint_contract": [
            {
                "id": endpoint.id,
                "family": endpoint.family,
                "direction": endpoint.direction,
            }
            for endpoint in _endpoint_specs(policies)
        ],
        "per_seed": seed_rows,
        "summaries": summaries,
        "paired_comparisons": {
            "comparator": method_ids[0],
            "methods": paired,
            "unfavorable_and_tied_pairs_retained": True,
            "failed_pairs_retained": True,
        },
        "family_specific": family_tables,
        "failures": failed_runs,
        "coverage": {
            "expected_seeds": len(seeds),
            "reported_seeds": len(seed_rows),
            "seed_coverage_rate": 1.0,
            "all_points_required_per_successful_method": True,
        },
    }
    selectors = {
        "schema_version": 1,
        "source": RESULT_NAME,
        "selectors": {
            "per_seed_metrics": "$.per_seed[*].methods[*].metrics",
            "incident_split": (
                "$.per_seed[*].methods[*].metrics.incident_split_loss"
            ),
            "incident_merge": (
                "$.per_seed[*].methods[*].metrics.incident_merge_loss"
            ),
            "noise_rejection": (
                "$.per_seed[*].methods[*].metrics.noise_rejection_rate"
            ),
            "noise_absorption": (
                "$.per_seed[*].methods[*].metrics.noise_absorption_rate"
            ),
            "false_destinations": (
                "$.per_seed[*].methods[*].metrics."
                "false_operational_destinations"
            ),
            "review_burden": (
                "$.per_seed[*].methods[*].metrics.operator_review_burden"
            ),
            "paired_confidence_intervals": (
                "$.paired_comparisons.methods.*.*.paired_confidence_interval"
            ),
            "multimodal_error_table": "$.family_specific.multimodal_focus",
            "failures": "$.failures",
        },
    }

    destination = Path(output_dir).expanduser().resolve()
    historical = (DEMO_ROOT / "results").resolve()
    if destination == historical or historical in destination.parents:
        raise ValueError(
            "output_dir cannot be demo/results; use an isolated candidate run"
        )
    destination.mkdir(parents=True, exist_ok=True)
    result_path = destination / RESULT_NAME
    selector_path = destination / SELECTOR_NAME
    existing = [path for path in (result_path, selector_path) if path.exists()]
    if existing:
        raise FileExistsError(
            "refusing to overwrite output artifacts: "
            + ", ".join(str(path) for path in existing)
        )
    _exclusive_json(result_path, payload)
    _exclusive_json(selector_path, selectors)
    return result_path, selector_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=(
            Path(os.environ["DEMO_WORK_DIR"]) / "datasets"
            if "DEMO_WORK_DIR" in os.environ
            else None
        ),
        required="DEMO_WORK_DIR" not in os.environ,
        help="Frozen candidate root containing only the requested tuning split path.",
    )
    parser.add_argument(
        "--stage",
        choices=("development", "calibration"),
        default="calibration",
        help="Restricted tuning stage; no other split is accepted.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=(
            Path(os.environ["DEMO_TABLES_DIR"])
            if "DEMO_TABLES_DIR" in os.environ
            else None
        ),
        required="DEMO_TABLES_DIR" not in os.environ,
        help="Isolated artifact table directory.",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(arguments)
    result_path, selector_path = run(
        args.dataset_root,
        stage=args.stage,
        output_dir=args.output_dir,
    )
    print(f"[saved] {result_path}")
    print(f"[saved] {selector_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEFAULT_METHODS",
    "MethodSpec",
    "PREREGISTERED_REVIEW_POLICIES",
    "build_family_tables",
    "build_method_summaries",
    "build_paired_comparisons",
    "evaluate_method",
    "evaluate_seed",
    "run",
]
