"""Experiment 15: fair calibration of product and non-product similarities.

Only development/calibration stages are accepted here.  The frozen selections
written by this module are inputs to the later one-shot evaluation entry point;
they are not changed in response to any downstream result.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

from demo.experiments.calibration import (
    CalibrationSelection,
    CandidateEvaluation,
    MetricConstraint,
    OperationalCalibrationContract,
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
from demo.experiments.protocol import TuningProtocol, load_tuning_protocol
from demo.experiments.pre_gate2 import (
    default_table_path,
    resolve_frozen_dataset_root,
)
from demo.pipeline.baselines import (
    build_convex_similarity_matrix,
    primitive_similarity_matrices,
    validate_simplex_weights,
)
from demo.pipeline.clustering import disconnected_report, run_louvain
from demo.pipeline.config import DEFAULT_CONFIG, WeightParams
from demo.pipeline.metrics import cluster_quality, geographic_spread
from demo.pipeline.weighting import build_weight_matrix_vec


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BASELINE_REGISTRY = REPOSITORY_ROOT / "demo" / "protocol" / "baselines.json"
GATE1_LOCK = REPOSITORY_ROOT / "revision" / "gate1-lock.json"
COMPOSITION_METHODS = (
    "product_louvain",
    "additive_louvain",
    "multiple_similarity_louvain",
)


def _load_registry(path: Path | str = BASELINE_REGISTRY) -> dict[str, Any]:
    registry = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(registry, dict) or not isinstance(registry.get("methods"), list):
        raise ValueError("baseline registry is malformed")
    return registry


def _registry_methods(registry: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(method["id"]): method for method in registry["methods"]}


def default_frozen_dataset_root(
    gate1_lock: Path | str = GATE1_LOCK,
) -> Path:
    """Resolve and authenticate the accepted Gate-1 dataset bundle."""

    root, _ = resolve_frozen_dataset_root(gate1_lock=gate1_lock)
    return root


def _weight_params(config: Mapping[str, Any]) -> WeightParams:
    base = DEFAULT_CONFIG.weight
    supported = {
        "sigma_geo_m",
        "tau_temp_min",
        "alpha",
        "knn",
    }
    updates = {key: config[key] for key in supported if key in config}
    # Threshold is derived from the declared per-seed weight quantile.
    updates["edge_threshold"] = 0.0
    return replace(base, **updates)


def evaluate_composition_seed(
    method_id: str,
    config: Mapping[str, Any],
    dataset: Any,
    *,
    calibration_labels: bool,
    precomputed_similarity: Any | None = None,
    calibration_contract: OperationalCalibrationContract | None = None,
) -> dict[str, float]:
    """Run one composition configuration on one frozen tuning seed."""

    events = list(dataset.events)
    params = _weight_params(config)
    if method_id not in COMPOSITION_METHODS:
        raise ValueError(f"unsupported composition method: {method_id!r}")
    if method_id == "multiple_similarity_louvain":
        validate_simplex_weights(config["simplex_weights"])
    if precomputed_similarity is not None:
        dense = precomputed_similarity
    elif method_id == "product_louvain":
        dense = build_weight_matrix_vec(events, params, mode="gating")
    elif method_id == "additive_louvain":
        dense = build_weight_matrix_vec(
            events,
            params,
            mode="additive",
            alpha=float(config["alpha"]),
        )
    elif method_id == "multiple_similarity_louvain":
        dense = build_convex_similarity_matrix(
            events,
            params,
            config["simplex_weights"],
        )
    else:  # pragma: no cover - guarded by COMPOSITION_METHODS above
        raise AssertionError("unreachable composition method")

    sparse, _ = sparsify_at_quantile(
        dense,
        float(config["threshold_quantile"]),
        knn=int(config.get("knn", 0)),
    )
    labels = run_louvain(
        sparse,
        resolution=float(config["resolution"]),
        random_state=dataset.seed,
    )
    reverse_labels = run_louvain(
        sparse[::-1, ::-1].copy(),
        resolution=float(config["resolution"]),
        random_state=dataset.seed,
    )
    density = graph_density(sparse)
    connectivity = disconnected_report(sparse, labels)
    spread = geographic_spread(
        events,
        labels,
        noise_label=None,
        gt_labels=(
            list(dataset.ground_truth)
            if calibration_labels and dataset.ground_truth is not None
            else None
        ),
    )
    metrics: dict[str, float] = {
        "retained_fraction": density.retained_fraction,
        "mean_degree": density.mean_degree,
        "disconnected_communities": float(connectivity["n_broken"]),
        "geographic_diameter": float(spread["max_diameter_km"]) * 1000.0,
        "complexity": float(len(config)),
        **operational_calibration_metrics(
            events,
            labels,
            reverse_labels,
            noise_label=None,
            contract=calibration_contract,
        ),
    }
    if calibration_labels:
        if dataset.ground_truth is None:
            raise RuntimeError("label-aware track received no evaluator view")
        quality = cluster_quality(labels, list(dataset.ground_truth))
        metrics["ari_labeled_reports"] = float(quality["ari"])
        metrics["ari_denominator"] = float(quality["n_eval"])
    return metrics


def _constraints_for_density(
    reference: CandidateEvaluation,
) -> tuple[MetricConstraint, ...]:
    metrics = reference.aggregate_metrics
    fraction = metrics["retained_fraction"]
    degree = metrics["mean_degree"]
    degree_lower = degree * 0.95
    degree_upper = degree * 1.05
    return (
        MetricConstraint("retained_fraction", ">=", max(0.0, fraction - 0.01)),
        MetricConstraint("retained_fraction", "<=", min(1.0, fraction + 0.01)),
        MetricConstraint("mean_degree", ">=", degree_lower),
        MetricConstraint("mean_degree", "<=", degree_upper),
    )


def _selected_evaluation(
    evaluations: Sequence[CandidateEvaluation],
    selection: CalibrationSelection,
) -> CandidateEvaluation | None:
    if selection.selected_config_sha256 is None:
        return None
    return next(
        (
            row
            for row in evaluations
            if row.config_sha256 == selection.selected_config_sha256
        ),
        None,
    )


def calibrate_composition_methods(
    dataset_root: Path | str,
    *,
    stage: str = "calibration",
    track_ids: Sequence[str] = (
        "benchmark_label_aware",
        "operational_label_free",
    ),
    method_ids: Sequence[str] = COMPOSITION_METHODS,
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
        raise ValueError("calibration must use the registry in the locked protocol bundle")
    frozen_root, frozen_record = resolve_frozen_dataset_root(dataset_root)
    calibration_contract = load_calibration_contract()
    registry = _load_registry(BASELINE_REGISTRY)
    methods = _registry_methods(registry)
    if not method_ids or len(method_ids) != len(set(method_ids)):
        raise ValueError("composition method ids must be non-empty and unique")
    if not track_ids or len(track_ids) != len(set(track_ids)):
        raise ValueError("calibration track ids must be non-empty and unique")
    unknown = sorted(set(method_ids) - set(COMPOSITION_METHODS))
    if unknown:
        raise ValueError(f"unsupported composition methods: {unknown}")
    track_specs = {track.id: track for track in locked.tracks}
    if any(track not in track_specs for track in track_ids):
        raise ValueError("unknown calibration track")

    all_evaluations: list[CandidateEvaluation] = []
    raw_selections: dict[tuple[str, str], CalibrationSelection] = {}
    by_method_track: dict[tuple[str, str], list[CandidateEvaluation]] = {}

    for track_id in track_ids:
        label_access = track_specs[track_id].calibration_labels
        primitive_cache: dict[tuple[int, float, float, float, float], Any] = {}

        @lru_cache(maxsize=None)
        def dataset_for(seed: int) -> Any:
            return load_tuning_dataset(
                frozen_root,
                stage=stage,  # type: ignore[arg-type]
                seed=seed,
                tuning_protocol=locked,
                calibration_labels=label_access,
            )

        for method_id in method_ids:
            method = methods[method_id]
            configs = expand_search_space(
                method["search_space"],
                maximum=locked.max_candidates_per_method_track,
            )
            if len(configs) != int(method["configuration_count"]):
                raise ValueError(
                    f"registry count mismatch for {method_id}: "
                    f"{len(configs)} != {method['configuration_count']}"
                )

            def evaluator(
                config: Mapping[str, Any],
                seed: int,
                selected_method: str = method_id,
            ) -> Mapping[str, float]:
                dense = None
                if selected_method == "multiple_similarity_louvain":
                    dataset = dataset_for(seed)
                    params = _weight_params(config)
                    primitive_key = (
                        seed,
                        float(params.sigma_geo_m),
                        float(params.tau_temp_min),
                        float(params.tau_f),
                        float(params.tau_e),
                    )
                    if primitive_key not in primitive_cache:
                        primitive_cache[primitive_key] = primitive_similarity_matrices(
                            dataset.events,
                            params,
                        )
                    geographic, temporal, contextual = primitive_cache[primitive_key]
                    weights = validate_simplex_weights(
                        config["simplex_weights"]
                    )
                    dense = (
                        float(weights[0]) * geographic
                        + float(weights[1]) * temporal
                        + float(weights[2]) * contextual
                    )
                return evaluate_composition_seed(
                    selected_method,
                    config,
                    dataset_for(seed),
                    calibration_labels=label_access,
                    precomputed_similarity=dense,
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
            by_method_track[(method_id, track_id)] = rows
            objective, direction = calibration_contract.objectives[track_id]
            raw_selections[(method_id, track_id)] = select_candidate(
                rows,
                objective=objective,
                direction=direction,
                constraints=operational_selection_constraints(
                    calibration_contract,
                    graph_method=True,
                ),
            )

    final_selections: list[CalibrationSelection] = []
    match_rows: list[dict[str, Any]] = []
    for track_id in track_ids:
        product_raw = raw_selections.get(("product_louvain", track_id))
        product_rows = by_method_track.get(("product_louvain", track_id), [])
        product_evaluation = (
            _selected_evaluation(product_rows, product_raw)
            if product_raw is not None
            else None
        )
        for method_id in method_ids:
            raw = raw_selections[(method_id, track_id)]
            rows = by_method_track[(method_id, track_id)]
            if method_id == "product_louvain" or product_evaluation is None:
                selected = raw
            else:
                objective, direction = calibration_contract.objectives[track_id]
                selected = select_candidate(
                    rows,
                    objective=objective,
                    direction=direction,
                    constraints=(
                        *operational_selection_constraints(
                            calibration_contract,
                            graph_method=True,
                        ),
                        *_constraints_for_density(product_evaluation),
                    ),
                )
            final_selections.append(selected)
            selected_evaluation = _selected_evaluation(rows, selected)
            if product_evaluation is not None and selected_evaluation is not None:
                match_rows.append(
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

    metadata = {
        "stage": stage,
        "complete_seed_set": seed_limit is None,
        "seed_limit": seed_limit,
        "raw_unmatched_selections": [
            selection.to_dict() for selection in raw_selections.values()
        ],
        "matched_density_degree": match_rows,
        "matched_retained_fraction_tolerance": 0.01,
        "matched_mean_degree_relative_tolerance": 0.05,
        "negative_tie_failure_policy": "all candidate rows retained",
        "calibration_contract_sha256": calibration_contract.source_sha256,
        "frozen_dataset": frozen_record,
    }
    return all_evaluations, final_selections, metadata


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calibrate product/additive/convex methods without evaluation release."
    )
    parser.add_argument("--dataset-root", type=Path)
    parser.add_argument(
        "--stage",
        choices=("development", "calibration"),
        default="calibration",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seed-limit", type=int)
    parser.add_argument(
        "--method",
        action="append",
        choices=COMPOSITION_METHODS,
        dest="methods",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    protocol = load_tuning_protocol()
    dataset_root = args.dataset_root or default_frozen_dataset_root()
    output = args.output or default_table_path("exp15_calibrated_comparison.json")
    evaluations, selections, metadata = calibrate_composition_methods(
        dataset_root,
        stage=args.stage,
        method_ids=tuple(args.methods or COMPOSITION_METHODS),
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
                "selection_statuses": [
                    {
                        "method_id": row.method_id,
                        "track_id": row.track_id,
                        "status": row.status,
                    }
                    for row in selections
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
