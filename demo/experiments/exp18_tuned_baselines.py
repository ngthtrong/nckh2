"""Experiment 18: tune every registered baseline on locked tuning splits."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from demo.experiments.calibration import (
    CalibrationSelection,
    CandidateEvaluation,
    MetricConstraint,
    OperationalCalibrationContract,
    SeedFailure,
    aggregate_seed_metrics,
    calibration_artifact_content_sha256,
    config_sha256,
    density_match_diagnostics,
    evaluate_candidates,
    expand_search_space,
    graph_density,
    load_calibration_contract,
    load_tuning_dataset,
    operational_calibration_metrics,
    operational_selection_constraints,
    select_candidate,
    sparsify_at_quantile,
    write_calibration_artifact,
)
from demo.experiments.exp15_calibrated_comparison import (
    BASELINE_REGISTRY,
    COMPOSITION_METHODS,
    _load_registry,
    _registry_methods,
    _weight_params,
    default_frozen_dataset_root,
    evaluate_composition_seed,
)
from demo.experiments.protocol import TuningProtocol, load_tuning_protocol
from demo.experiments.pre_gate2 import (
    default_table_path,
    resolve_frozen_dataset_root,
)
from demo.experiments.artifacts import validate_manifest
from demo.pipeline.baselines import (
    run_dbscan,
    run_hdbscan,
    run_kmeans,
    run_spatial_constrained_agglomerative,
    run_spectral,
    run_st_dbscan,
    spatiotemporal_distance_matrices,
)
from demo.pipeline.clustering import disconnected_report, run_leiden
from demo.pipeline.metrics import cluster_quality, geographic_spread
from demo.pipeline.weighting import build_weight_matrix_vec


SAME_REPRESENTATION_METHODS = {"product_leiden", "product_spectral"}
_LABEL_AWARE_TOKENS = (
    "ari",
    "nmi",
    "ground_truth",
    "latent",
    "incident_split",
    "incident_merge",
)
_CANDIDATE_EVALUATION_FIELDS = {
    "method_id",
    "track_id",
    "stage",
    "config",
    "config_sha256",
    "status",
    "seed_metrics",
    "aggregate_metrics",
    "failures",
    "configuration_evaluation_count",
    "seed_run_count",
    "wall_time_seconds",
}


def _candidate_from_artifact(
    row: Mapping[str, Any],
    *,
    calibration_seeds: Sequence[int],
    calibration_labels: bool,
) -> CandidateEvaluation:
    """Rebuild one candidate solely from its authenticated per-seed records."""

    if set(row) != _CANDIDATE_EVALUATION_FIELDS:
        raise ValueError("composition evaluation row schema is invalid")
    method_id = row.get("method_id")
    track_id = row.get("track_id")
    config = row.get("config")
    config_hash = row.get("config_sha256")
    status = row.get("status")
    seed_metrics = row.get("seed_metrics")
    aggregate = row.get("aggregate_metrics")
    failures = row.get("failures")
    wall_time = row.get("wall_time_seconds")
    if (
        not isinstance(method_id, str)
        or not method_id
        or not isinstance(track_id, str)
        or not track_id
        or not isinstance(config, dict)
        or not isinstance(config_hash, str)
        or config_sha256(config) != config_hash
        or row.get("stage") != "calibration"
        or status not in {"succeeded", "failed"}
        or row.get("configuration_evaluation_count") != 1
        or row.get("seed_run_count") != len(calibration_seeds)
        or not isinstance(seed_metrics, list)
        or not isinstance(aggregate, dict)
        or not isinstance(failures, list)
        or isinstance(wall_time, bool)
        or not isinstance(wall_time, (int, float))
        or not math.isfinite(float(wall_time))
        or float(wall_time) < 0.0
        or round(float(wall_time), 6) != float(wall_time)
    ):
        raise ValueError("composition evaluation identity/count is invalid")

    normalized_metrics: list[dict[str, float]] = []
    metric_seeds: list[int] = []
    for metric_row in seed_metrics:
        if (
            not isinstance(metric_row, dict)
            or len(metric_row) < 2
            or any(not isinstance(name, str) or not name for name in metric_row)
        ):
            raise ValueError("composition seed metric row is malformed")
        raw_seed = metric_row.get("seed")
        if (
            isinstance(raw_seed, bool)
            or not isinstance(raw_seed, (int, float))
            or not math.isfinite(float(raw_seed))
            or not float(raw_seed).is_integer()
        ):
            raise ValueError("composition seed metric identity is malformed")
        normalized: dict[str, float] = {}
        for name, raw_value in metric_row.items():
            if (
                isinstance(raw_value, bool)
                or not isinstance(raw_value, (int, float))
                or not math.isfinite(float(raw_value))
            ):
                raise ValueError("composition seed metrics must be finite numeric values")
            if (
                not calibration_labels
                and name != "seed"
                and any(token in name.casefold() for token in _LABEL_AWARE_TOKENS)
            ):
                raise ValueError("label-free composition metrics expose hidden labels")
            normalized[name] = float(raw_value)
        metric_seeds.append(int(raw_seed))
        normalized_metrics.append(normalized)

    normalized_failures: list[SeedFailure] = []
    failure_seeds: list[int] = []
    for failure in failures:
        if (
            not isinstance(failure, dict)
            or set(failure) != {"seed", "exception_type", "message"}
            or isinstance(failure.get("seed"), bool)
            or not isinstance(failure.get("seed"), int)
            or not isinstance(failure.get("exception_type"), str)
            or not failure["exception_type"]
            or not isinstance(failure.get("message"), str)
        ):
            raise ValueError("composition seed failure row is malformed")
        failure_seeds.append(failure["seed"])
        normalized_failures.append(
            SeedFailure(
                seed=failure["seed"],
                exception_type=failure["exception_type"],
                message=failure["message"],
            )
        )

    seed_positions = {
        seed: index for index, seed in enumerate(calibration_seeds)
    }
    covered_seeds = metric_seeds + failure_seeds
    if (
        len(seed_positions) != len(calibration_seeds)
        or len(covered_seeds) != len(set(covered_seeds))
        or set(covered_seeds) != set(calibration_seeds)
        or metric_seeds
        != sorted(metric_seeds, key=lambda seed: seed_positions.get(seed, -1))
        or failure_seeds
        != sorted(failure_seeds, key=lambda seed: seed_positions.get(seed, -1))
        or (status == "failed") != bool(normalized_failures)
    ):
        raise ValueError(
            "composition evaluation does not cover the exact calibration seed set"
        )

    expected_aggregate = aggregate_seed_metrics(normalized_metrics)
    if (
        any(
            not isinstance(name, str)
            or not name
            or isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            for name, value in aggregate.items()
        )
        or aggregate != expected_aggregate
    ):
        raise ValueError(
            "composition aggregate metrics are not mechanically reproducible"
        )

    candidate = CandidateEvaluation(
        method_id=method_id,
        track_id=track_id,
        stage="calibration",
        config=dict(config),
        config_sha256=config_hash,
        status=status,
        seed_metrics=tuple(normalized_metrics),
        aggregate_metrics=dict(aggregate),
        failures=tuple(normalized_failures),
        configuration_evaluation_count=1,
        seed_run_count=len(calibration_seeds),
        wall_time_seconds=float(wall_time),
    )
    if candidate.to_dict() != dict(row):
        raise ValueError("composition evaluation row is not in producer-normal form")
    return candidate


def _density_constraints(
    reference: CandidateEvaluation,
    contract: OperationalCalibrationContract,
) -> tuple[MetricConstraint, ...]:
    metrics = reference.aggregate_metrics
    try:
        fraction = float(metrics["retained_fraction"])
        degree = float(metrics["mean_degree"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("selected product has no valid density metrics") from exc
    if not math.isfinite(fraction) or not math.isfinite(degree) or degree < 0.0:
        raise ValueError("selected product density metrics are invalid")
    return (
        MetricConstraint(
            "retained_fraction",
            ">=",
            max(0.0, fraction - contract.retained_fraction_match_tolerance),
        ),
        MetricConstraint(
            "retained_fraction",
            "<=",
            min(1.0, fraction + contract.retained_fraction_match_tolerance),
        ),
        MetricConstraint(
            "mean_degree",
            ">=",
            degree * (1.0 - contract.mean_degree_match_relative_tolerance),
        ),
        MetricConstraint(
            "mean_degree",
            "<=",
            degree * (1.0 + contract.mean_degree_match_relative_tolerance),
        ),
    )


def _candidate_satisfies(
    evaluation: CandidateEvaluation,
    *,
    objective: str,
    constraints: Sequence[MetricConstraint],
) -> bool:
    return (
        evaluation.status == "succeeded"
        and objective in evaluation.aggregate_metrics
        and all(
            constraint.violation(evaluation.aggregate_metrics) is None
            for constraint in constraints
        )
    )


def _selected_evaluation(
    evaluations: Sequence[CandidateEvaluation],
    selection: CalibrationSelection,
) -> CandidateEvaluation | None:
    selected_hash = selection.selected_config_sha256
    if selected_hash is None:
        return None
    return next(
        (
            evaluation
            for evaluation in evaluations
            if evaluation.config_sha256 == selected_hash
        ),
        None,
    )


def _verify_composition_selections(
    evaluations: Sequence[CandidateEvaluation],
    selections: Sequence[Mapping[str, Any]],
    *,
    track_ids: Sequence[str],
    contract: OperationalCalibrationContract,
    metadata: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    """Re-run Exp15 selection, including its joint matched-density rule."""

    by_pair: dict[tuple[str, str], list[CandidateEvaluation]] = {}
    for evaluation in evaluations:
        by_pair.setdefault(
            (evaluation.method_id, evaluation.track_id),
            [],
        ).append(evaluation)
    for rows in by_pair.values():
        rows.sort(key=lambda evaluation: evaluation.config_sha256)

    expected_pairs = {
        (method_id, track_id)
        for track_id in track_ids
        for method_id in COMPOSITION_METHODS
    }
    if set(by_pair) != expected_pairs:
        raise ValueError("composition evaluation grid has an invalid method/track scope")

    raw_selections: dict[tuple[str, str], CalibrationSelection] = {}
    operational_constraints = operational_selection_constraints(
        contract,
        graph_method=True,
    )
    for track_id in track_ids:
        objective, direction = contract.objectives[track_id]
        for method_id in COMPOSITION_METHODS:
            raw_selections[(method_id, track_id)] = select_candidate(
                by_pair[(method_id, track_id)],
                objective=objective,
                direction=direction,
                constraints=operational_constraints,
            )

    expected_selections: dict[tuple[str, str], CalibrationSelection] = {}
    expected_joint_audit: list[dict[str, Any]] = []
    expected_match_rows: list[dict[str, Any]] = []
    comparator_ids = tuple(
        method_id
        for method_id in COMPOSITION_METHODS
        if method_id != "product_louvain"
    )
    for track_id in track_ids:
        objective, direction = contract.objectives[track_id]
        product_rows = by_pair[("product_louvain", track_id)]
        joint_rows: list[CandidateEvaluation] = []
        for product in product_rows:
            matchable = _candidate_satisfies(
                product,
                objective=objective,
                constraints=operational_constraints,
            ) and all(
                any(
                    _candidate_satisfies(
                        comparator,
                        objective=objective,
                        constraints=(
                            *operational_constraints,
                            *_density_constraints(product, contract),
                        ),
                    )
                    for comparator in by_pair[(comparator_id, track_id)]
                )
                for comparator_id in comparator_ids
            )
            joint_rows.append(
                replace(
                    product,
                    aggregate_metrics={
                        **product.aggregate_metrics,
                        "joint_density_match_available": float(matchable),
                    },
                )
            )
        product_selection = select_candidate(
            joint_rows,
            objective=objective,
            direction=direction,
            constraints=(
                *operational_constraints,
                MetricConstraint(
                    "joint_density_match_available",
                    ">=",
                    1.0,
                ),
            ),
        )
        product_evaluation = _selected_evaluation(
            product_rows,
            product_selection,
        )
        expected_joint_audit.append(
            {
                "track_id": track_id,
                "required_comparators": list(comparator_ids),
                "joint_matchable_product_configurations": sum(
                    row.aggregate_metrics["joint_density_match_available"] == 1.0
                    for row in joint_rows
                ),
                "joint_product_selection_status": product_selection.status,
                "joint_product_selection_sha256": (
                    product_selection.selection_sha256
                ),
            }
        )
        for method_id in COMPOSITION_METHODS:
            rows = by_pair[(method_id, track_id)]
            if method_id == "product_louvain":
                selected = product_selection
            elif product_evaluation is None:
                selected = raw_selections[(method_id, track_id)]
            else:
                selected = select_candidate(
                    rows,
                    objective=objective,
                    direction=direction,
                    constraints=(
                        *operational_constraints,
                        *_density_constraints(product_evaluation, contract),
                    ),
                )
            expected_selections[(method_id, track_id)] = selected
            selected_evaluation = _selected_evaluation(rows, selected)
            if product_evaluation is not None and selected_evaluation is not None:
                expected_match_rows.append(
                    {
                        "method_id": method_id,
                        "track_id": track_id,
                        **density_match_diagnostics(
                            {
                                "retained_fraction": product_evaluation.aggregate_metrics[
                                    "retained_fraction"
                                ],
                                "mean_degree": product_evaluation.aggregate_metrics[
                                    "mean_degree"
                                ],
                            },
                            {
                                "retained_fraction": selected_evaluation.aggregate_metrics[
                                    "retained_fraction"
                                ],
                                "mean_degree": selected_evaluation.aggregate_metrics[
                                    "mean_degree"
                                ],
                            },
                        ),
                    }
                )

    observed_selections: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in selections:
        if not isinstance(row, dict):
            raise ValueError("composition selection row must be an object")
        pair = (row.get("method_id"), row.get("track_id"))
        if (
            not all(isinstance(value, str) for value in pair)
            or pair in observed_selections
        ):
            raise ValueError("composition artifact repeats an invalid selection")
        observed_selections[(str(pair[0]), str(pair[1]))] = row
    if set(observed_selections) != expected_pairs:
        raise ValueError("composition artifact lacks a declared method/track selection")
    for pair, expected in expected_selections.items():
        if observed_selections[pair] != expected.to_dict():
            raise ValueError(
                "composition winner/audit is not mechanically reproducible for "
                f"{pair[0]}/{pair[1]}"
            )

    expected_raw = [
        raw_selections[(method_id, track_id)].to_dict()
        for track_id in track_ids
        for method_id in COMPOSITION_METHODS
    ]
    if (
        metadata.get("raw_unmatched_selections") != expected_raw
        or metadata.get("joint_composition_selection") != expected_joint_audit
        or metadata.get("matched_density_degree") != expected_match_rows
        or metadata.get("matched_retained_fraction_tolerance")
        != contract.retained_fraction_match_tolerance
        or metadata.get("matched_mean_degree_relative_tolerance")
        != contract.mean_degree_match_relative_tolerance
        or metadata.get("negative_tie_failure_policy")
        != "all candidate rows retained"
    ):
        raise ValueError("composition selection audit metadata is not reproducible")

    selected_products: dict[str, Mapping[str, Any]] = {}
    for track_id in track_ids:
        selection = expected_selections[("product_louvain", track_id)]
        if selection.status != "selected" or selection.selected_config is None:
            raise ValueError("composition artifact lacks one selected product per track")
        selected_products[track_id] = dict(selection.selected_config)
    return selected_products


def load_product_selections(
    artifact_path: Path | str,
    *,
    protocol: TuningProtocol | None = None,
) -> dict[str, Mapping[str, Any]]:
    """Read authenticated full-calibration product selections from Exp15."""

    locked = protocol or load_tuning_protocol()
    calibration_contract = load_calibration_contract()
    source = Path(artifact_path).resolve()
    try:
        raw = source.read_bytes()
        artifact = json.loads(raw)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ValueError("composition selection artifact is absent or invalid") from exc
    if not isinstance(artifact, dict):
        raise ValueError("composition selection artifact must be an object")
    canonical = (
        json.dumps(
            artifact,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    if raw != canonical:
        raise ValueError("composition selection artifact is not canonical JSON")
    if artifact.get("schema_version") != "calibration-artifact-v1":
        raise ValueError("composition selection artifact has an unsupported schema")
    expected_content_hash = calibration_artifact_content_sha256(artifact)
    if artifact.get("artifact_content_sha256") != expected_content_hash:
        raise ValueError("composition selection artifact content hash mismatch")
    if (
        artifact.get("protocol_sha256") != locked.protocol_sha256
        or artifact.get("seed_manifest_sha256") != locked.seed_manifest_sha256
        or artifact.get("metric_contract_sha256")
        != locked.metric_contract_sha256
    ):
        raise ValueError("composition selection artifact protocol hashes do not match")
    metadata = artifact.get("metadata")
    _, current_frozen_record = resolve_frozen_dataset_root()
    if (
        not isinstance(metadata, dict)
        or metadata.get("stage") != "calibration"
        or metadata.get("complete_seed_set") is not True
        or metadata.get("seed_limit") is not None
        or metadata.get("calibration_contract_sha256")
        != calibration_contract.source_sha256
        or metadata.get("frozen_dataset") != current_frozen_record
    ):
        raise ValueError(
            "composition selections require the complete authenticated calibration split"
        )

    if source.parent.name != "tables":
        raise ValueError("composition selection artifact must belong to a sealed run")
    run_manifest_path = source.parent.parent / "manifest.json"
    try:
        run_manifest = validate_manifest(run_manifest_path)
    except Exception as exc:
        raise ValueError("composition selection run manifest is invalid") from exc
    if run_manifest.get("status") != "succeeded" or run_manifest.get("exit_code") != 0:
        raise ValueError("composition selection run did not succeed")
    command = run_manifest.get("command")
    if (
        not isinstance(command, list)
        or not any(
            isinstance(part, str)
            and (
                "exp15_calibrated_comparison" in part
                or part.endswith("exp15_calibrated_comparison.py")
            )
            for part in command
        )
    ):
        raise ValueError("sealed run is not an Exp15 calibration execution")
    try:
        relative_source = source.relative_to(source.parent.parent).as_posix()
    except ValueError as exc:  # pragma: no cover - guarded by the layout check.
        raise ValueError("composition artifact escapes its sealed run") from exc
    observed_file_hash = hashlib.sha256(raw).hexdigest()
    if run_manifest.get("checksums", {}).get(relative_source) != observed_file_hash:
        raise ValueError("composition artifact is not authenticated by its run manifest")
    manifest_protocol = run_manifest.get("inputs", {}).get("protocol", {})
    if (
        not isinstance(manifest_protocol, dict)
        or manifest_protocol.get("sha256") != locked.protocol_sha256
    ):
        raise ValueError("composition run captured a different protocol")
    manifest_inputs = run_manifest.get("inputs")
    dataset_inputs = (
        manifest_inputs.get("datasets")
        if isinstance(manifest_inputs, dict)
        else None
    )
    expected_dataset_source = (
        f"{current_frozen_record['dataset_root']}/manifest.json"
    )
    if (
        not isinstance(dataset_inputs, list)
        or len(dataset_inputs) != 1
        or not isinstance(dataset_inputs[0], dict)
        or dataset_inputs[0].get("source") != expected_dataset_source
        or dataset_inputs[0].get("snapshot")
        != "inputs/datasets/00-manifest.json"
        or dataset_inputs[0].get("sha256")
        != current_frozen_record["dataset_manifest_sha256"]
        or run_manifest.get("checksums", {}).get(
            "inputs/datasets/00-manifest.json"
        )
        != current_frozen_record["dataset_manifest_sha256"]
    ):
        raise ValueError("composition run captured a different dataset manifest")

    evaluations = artifact.get("evaluations")
    selections = artifact.get("selections")
    if not isinstance(evaluations, list) or not isinstance(selections, list):
        raise ValueError("composition artifact is missing evaluations or selections")
    evaluation_index: dict[
        tuple[str, str, str],
        CandidateEvaluation,
    ] = {}
    validated_evaluations: list[CandidateEvaluation] = []
    counts: dict[tuple[str, str], int] = {}
    registry_methods = _registry_methods(_load_registry(BASELINE_REGISTRY))
    allowed_config_hashes = {
        method_id: {
            config_sha256(config)
            for config in expand_search_space(
                registry_methods[method_id]["search_space"],
                maximum=locked.max_candidates_per_method_track,
            )
        }
        for method_id in COMPOSITION_METHODS
    }
    track_specs = {track.id: track for track in locked.tracks}
    expected_tracks = set(track_specs)
    for row in evaluations:
        if not isinstance(row, dict):
            raise ValueError("composition evaluation row must be an object")
        method_id = row.get("method_id")
        track_id = row.get("track_id")
        config_hash = row.get("config_sha256")
        config = row.get("config")
        if (
            not isinstance(method_id, str)
            or not isinstance(track_id, str)
            or not isinstance(config_hash, str)
            or not isinstance(config, dict)
            or row.get("stage") != "calibration"
            or row.get("status") not in {"succeeded", "failed"}
            or config_sha256(config) != config_hash
            or row.get("configuration_evaluation_count") != 1
            or row.get("seed_run_count") != len(locked.calibration_seeds)
            or method_id not in allowed_config_hashes
            or track_id not in expected_tracks
            or config_hash not in allowed_config_hashes[method_id]
        ):
            raise ValueError("composition evaluation identity/count is invalid")
        candidate = _candidate_from_artifact(
            row,
            calibration_seeds=locked.calibration_seeds,
            calibration_labels=track_specs[track_id].calibration_labels,
        )
        key = (method_id, track_id, config_hash)
        if key in evaluation_index:
            raise ValueError("composition artifact repeats an evaluation")
        evaluation_index[key] = candidate
        validated_evaluations.append(candidate)
        counts[(method_id, track_id)] = counts.get((method_id, track_id), 0) + 1
    expected_counts = {
        (method_id, track_id): len(allowed_config_hashes[method_id])
        for method_id in COMPOSITION_METHODS
        for track_id in expected_tracks
    }
    if counts != expected_counts:
        raise ValueError("composition artifact is not the complete declared grid")
    if artifact.get("configuration_evaluation_count") != len(evaluations):
        raise ValueError("composition artifact evaluation total is inconsistent")
    if artifact.get("seed_run_count") != (
        len(evaluations) * len(locked.calibration_seeds)
    ):
        raise ValueError("composition artifact seed-run total is inconsistent")
    observed_failures = sum(
        row.get("status") == "failed" for row in evaluations
    )
    if artifact.get("failed_configuration_count") != observed_failures:
        raise ValueError("composition artifact failure total is inconsistent")
    return _verify_composition_selections(
        validated_evaluations,
        selections,
        track_ids=tuple(track.id for track in locked.tracks),
        contract=calibration_contract,
        metadata=metadata,
    )


def _selected_product_graph(
    events: Sequence[Any],
    product_config: Mapping[str, Any],
) -> Any:
    params = _weight_params(product_config)
    dense = build_weight_matrix_vec(list(events), params, mode="gating")
    sparse, _ = sparsify_at_quantile(
        dense,
        float(product_config["threshold_quantile"]),
        knn=int(product_config.get("knn", 0)),
    )
    return sparse


def _predict_baseline_labels(
    method_id: str,
    config: Mapping[str, Any],
    events: Sequence[Any],
    *,
    seed: int,
    product_config: Mapping[str, Any] | None,
    st_distance_matrices: Any | None,
) -> tuple[list[int], int | None, Any | None, Any | None]:
    """Run one non-composition adapter with a common prediction contract."""

    event_list = list(events)
    noise_label: int | None = None
    representation_density = None
    representation_graph = None
    if method_id == "st_dbscan":
        labels = run_st_dbscan(
            event_list,
            spatial_eps_m=float(config["spatial_eps_m"]),
            temporal_eps_min=float(config["temporal_eps_min"]),
            min_samples=int(config["min_samples"]),
            distance_matrices=st_distance_matrices,
        )
        noise_label = -1
    elif method_id == "dbscan_geo_time_context":
        labels = run_dbscan(
            event_list,
            eps=float(config["eps"]),
            min_samples=int(config["min_samples"]),
            features="geo_time_context",
            scaler=str(config["scaler"]),  # type: ignore[arg-type]
        )
        noise_label = -1
    elif method_id == "hdbscan_geo_time_context":
        labels = run_hdbscan(
            event_list,
            min_cluster_size=int(config["min_cluster_size"]),
            min_samples=(
                None
                if config["min_samples"] is None
                else int(config["min_samples"])
            ),
            features="geo_time_context",
            scaler=str(config["scaler"]),  # type: ignore[arg-type]
        )
        noise_label = -1
    elif method_id == "spatial_constrained_agglomerative":
        labels = run_spatial_constrained_agglomerative(
            event_list,
            connectivity_radius_m=float(config["connectivity_radius_m"]),
            n_clusters=int(config["n_clusters"]),
            time_context_mix=float(config["time_context_mix"]),
        )
    elif method_id == "coordinate_kmeans":
        labels = run_kmeans(
            event_list,
            n_clusters=int(config["n_clusters"]),
            random_state=seed,
            features="geo",
        )
    elif method_id in SAME_REPRESENTATION_METHODS:
        if product_config is None:
            raise ValueError(
                f"{method_id} requires the frozen product configuration"
            )
        graph = _selected_product_graph(event_list, product_config)
        representation_graph = graph
        representation_density = graph_density(graph)
        if method_id == "product_leiden":
            labels = run_leiden(
                graph,
                resolution=float(config["resolution"]),
                random_state=seed,
            )
        else:
            labels = run_spectral(
                graph,
                n_clusters=int(config["n_clusters"]),
                random_state=seed,
            )
    else:
        raise ValueError(f"unsupported registered baseline: {method_id!r}")
    return (
        list(labels),
        noise_label,
        representation_density,
        representation_graph,
    )


def evaluate_baseline_seed(
    method_id: str,
    config: Mapping[str, Any],
    dataset: Any,
    *,
    calibration_labels: bool,
    product_config: Mapping[str, Any] | None = None,
    st_distance_matrices: Any | None = None,
    calibration_contract: OperationalCalibrationContract | None = None,
) -> dict[str, float]:
    """Run one registered adapter and return comparable seed-level metrics."""

    if method_id in {
        "product_louvain",
        "additive_louvain",
        "multiple_similarity_louvain",
    }:
        return evaluate_composition_seed(
            method_id,
            config,
            dataset,
            calibration_labels=calibration_labels,
            calibration_contract=calibration_contract,
        )

    events = list(dataset.events)
    (
        labels,
        noise_label,
        representation_density,
        representation_graph,
    ) = _predict_baseline_labels(
        method_id,
        config,
        events,
        seed=dataset.seed,
        product_config=product_config,
        st_distance_matrices=st_distance_matrices,
    )
    reversed_distances = (
        None
        if st_distance_matrices is None
        else tuple(
            np.asarray(matrix)[::-1, ::-1].copy()
            for matrix in st_distance_matrices
        )
    )
    reverse_labels, reverse_noise_label, _, _ = _predict_baseline_labels(
        method_id,
        config,
        list(reversed(events)),
        seed=dataset.seed,
        product_config=product_config,
        st_distance_matrices=reversed_distances,
    )
    if reverse_noise_label != noise_label:
        raise AssertionError("prediction noise convention changed under permutation")

    truth = (
        list(dataset.ground_truth)
        if calibration_labels and dataset.ground_truth is not None
        else None
    )
    spread = geographic_spread(
        events,
        labels,
        noise_label=noise_label,
        gt_labels=truth,
    )
    n_unassigned = sum(label == -1 for label in labels) if noise_label == -1 else 0
    metrics: dict[str, float] = {
        "geographic_diameter": float(spread["max_diameter_km"]) * 1000.0,
        "unassigned_reports": float(n_unassigned),
        "complexity": float(len(config)),
        **operational_calibration_metrics(
            events,
            labels,
            reverse_labels,
            noise_label=noise_label,
            contract=calibration_contract,
        ),
    }
    if representation_density is not None:
        if representation_graph is None:  # pragma: no cover - tuple invariant.
            raise AssertionError("graph density has no representation graph")
        connectivity = disconnected_report(representation_graph, labels)
        metrics.update(
            {
                "retained_fraction": representation_density.retained_fraction,
                "mean_degree": representation_density.mean_degree,
                "disconnected_communities": float(connectivity["n_broken"]),
            }
        )
    if calibration_labels:
        if truth is None:
            raise RuntimeError("label-aware track received no evaluator view")
        quality = cluster_quality(labels, truth)
        metrics["ari_labeled_reports"] = float(quality["ari"])
        metrics["ari_denominator"] = float(quality["n_eval"])
    return metrics


def tune_registered_baselines(
    dataset_root: Path | str,
    *,
    stage: str = "calibration",
    track_ids: Sequence[str] = (
        "benchmark_label_aware",
        "operational_label_free",
    ),
    method_ids: Sequence[str] | None = None,
    product_selections: Mapping[str, Mapping[str, Any]] | None = None,
    seed_limit: int | None = None,
    protocol: TuningProtocol | None = None,
    registry_path: Path | str = BASELINE_REGISTRY,
) -> tuple[
    list[CandidateEvaluation],
    list[CalibrationSelection],
    dict[str, Any],
]:
    locked = protocol or load_tuning_protocol()
    if stage not in {"development", "calibration"}:
        raise ValueError("stage must be development or calibration")
    if Path(registry_path).resolve() != BASELINE_REGISTRY.resolve():
        raise ValueError("baseline tuning must use the locked protocol registry")
    frozen_root, frozen_record = resolve_frozen_dataset_root(dataset_root)
    calibration_contract = load_calibration_contract()
    registry = _load_registry(BASELINE_REGISTRY)
    methods = _registry_methods(registry)
    selected_methods = (
        tuple(method_ids)
        if method_ids is not None
        else tuple(
            method_id
            for method_id in methods
            if method_id not in COMPOSITION_METHODS
        )
    )
    if not selected_methods:
        raise ValueError("at least one non-composition baseline is required")
    if len(selected_methods) != len(set(selected_methods)):
        raise ValueError("baseline method ids must be unique")
    if set(selected_methods) & set(COMPOSITION_METHODS):
        raise ValueError(
            "composition selections are owned by Exp15 and cannot be retuned in Exp18"
        )
    if not track_ids or len(track_ids) != len(set(track_ids)):
        raise ValueError("calibration track ids must be non-empty and unique")
    unknown = sorted(set(selected_methods) - set(methods))
    if unknown:
        raise ValueError(f"unregistered methods: {unknown}")
    track_specs = {track.id: track for track in locked.tracks}
    if any(track not in track_specs for track in track_ids):
        raise ValueError("unknown calibration track")

    all_evaluations: list[CandidateEvaluation] = []
    selections: list[CalibrationSelection] = []
    config_count_audit: list[dict[str, Any]] = []
    for track_id in track_ids:
        label_access = track_specs[track_id].calibration_labels
        st_distance_cache: dict[int, Any] = {}

        @lru_cache(maxsize=None)
        def dataset_for(seed: int) -> Any:
            return load_tuning_dataset(
                frozen_root,
                stage=stage,  # type: ignore[arg-type]
                seed=seed,
                tuning_protocol=locked,
                calibration_labels=label_access,
            )

        selected_product = (product_selections or {}).get(track_id)
        for method_id in selected_methods:
            if method_id in SAME_REPRESENTATION_METHODS and selected_product is None:
                raise ValueError(
                    f"{method_id} requires an Exp15 product selection for {track_id}"
                )
            method = methods[method_id]
            configs = expand_search_space(
                method["search_space"],
                maximum=locked.max_candidates_per_method_track,
            )
            declared = int(method["configuration_count"])
            if len(configs) != declared:
                raise ValueError(
                    f"registry count mismatch for {method_id}: {len(configs)} != {declared}"
                )
            config_count_audit.append(
                {
                    "method_id": method_id,
                    "track_id": track_id,
                    "declared": declared,
                    "evaluated": len(configs),
                    "within_budget": len(configs)
                    <= locked.max_candidates_per_method_track,
                }
            )

            def evaluator(
                config: Mapping[str, Any],
                seed: int,
                selected_method: str = method_id,
                frozen_product: Mapping[str, Any] | None = selected_product,
            ) -> Mapping[str, float]:
                dataset = dataset_for(seed)
                st_distances = None
                if selected_method == "st_dbscan":
                    if seed not in st_distance_cache:
                        st_distance_cache[seed] = spatiotemporal_distance_matrices(
                            dataset.events
                        )
                    st_distances = st_distance_cache[seed]
                return evaluate_baseline_seed(
                    selected_method,
                    config,
                    dataset,
                    calibration_labels=label_access,
                    product_config=frozen_product,
                    st_distance_matrices=st_distances,
                    calibration_contract=calibration_contract,
                )

            rows = evaluate_candidates(
                method_id,
                track_id,
                stage,  # type: ignore[arg-type]
                configs,
                evaluator,
                tuning_protocol=locked,
                seed_limit=seed_limit,
            )
            all_evaluations.extend(rows)
            objective, direction = calibration_contract.objectives[track_id]
            constraints = operational_selection_constraints(
                calibration_contract,
                graph_method=method_id in SAME_REPRESENTATION_METHODS,
            )
            selections.append(
                select_candidate(
                    rows,
                    objective=objective,
                    direction=direction,
                    constraints=constraints,
                )
            )

    metadata = {
        "stage": stage,
        "complete_seed_set": seed_limit is None,
        "seed_limit": seed_limit,
        "configuration_count_audit": config_count_audit,
        "product_selection_hashes": {
            track: config_sha256(config)
            for track, config in (product_selections or {}).items()
        },
        "failed_and_infeasible_rows_retained": True,
        "oracle_k_is_not_primary": True,
        "calibration_contract_sha256": calibration_contract.source_sha256,
        "frozen_dataset": frozen_record,
        "composition_methods_reused_from_exp15": list(COMPOSITION_METHODS),
    }
    return all_evaluations, selections, metadata


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tune the complete preregistered baseline registry."
    )
    parser.add_argument("--dataset-root", type=Path)
    parser.add_argument(
        "--stage",
        choices=("development", "calibration"),
        default="calibration",
    )
    parser.add_argument("--composition-artifact", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seed-limit", type=int)
    parser.add_argument("--method", action="append", dest="methods")
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    protocol = load_tuning_protocol()
    registry = _load_registry()
    known = _registry_methods(registry)
    selected_methods = None if args.methods is None else tuple(args.methods)
    unknown = (
        []
        if selected_methods is None
        else sorted(set(selected_methods) - set(known))
    )
    if unknown:
        raise ValueError(f"unregistered methods: {unknown}")
    product_selections = (
        load_product_selections(args.composition_artifact, protocol=protocol)
        if args.composition_artifact is not None
        else {}
    )
    output = args.output or default_table_path("exp18_tuned_baselines.json")
    evaluations, selections, metadata = tune_registered_baselines(
        args.dataset_root or default_frozen_dataset_root(),
        stage=args.stage,
        method_ids=selected_methods,
        product_selections=product_selections,
        seed_limit=args.seed_limit,
        protocol=protocol,
    )
    write_calibration_artifact(
        output,
        protocol=protocol,
        evaluations=evaluations,
        selections=selections,
        metadata=metadata,
    )
    print(
        json.dumps(
            {
                "output": str(output),
                "configuration_evaluations": len(evaluations),
                "failed_configurations": sum(
                    row.status == "failed" for row in evaluations
                ),
                "selected": sum(row.status == "selected" for row in selections),
                "no_feasible_candidate": sum(
                    row.status == "no_feasible_candidate" for row in selections
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
