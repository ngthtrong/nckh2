"""Experiment 19: complete clustering and priority factorial ablations.

The experiment runs on the frozen development/calibration bundle only.  Every
cell, including degenerate or density-infeasible cells, remains in the output.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import time
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.stats import spearmanr

from demo.experiments.calibration import (
    config_sha256,
    factorial_effect_summaries,
    find_density_match,
    graph_density,
    load_tuning_dataset,
    sparsify_at_quantile,
)
from demo.experiments.exp15_calibrated_comparison import (
    DEFAULT_CONFIG,
    _weight_params,
    default_frozen_dataset_root,
)
from demo.experiments.exp18_tuned_baselines import load_product_selections
from demo.experiments.protocol import TuningProtocol, load_tuning_protocol
from demo.experiments.pre_gate2 import (
    default_table_path,
    resolve_frozen_dataset_root,
    write_exclusive_json,
)
from demo.pipeline.baselines import primitive_similarity_matrices
from demo.pipeline.clustering import run_louvain
from demo.pipeline.metrics import cluster_quality
from demo.pipeline.priority import score_clusters
from demo.pipeline.weighting import build_weight_matrix_vec, sparsify


CLUSTERING_FACTORS = ("geography", "time", "context", "knn")
PRIORITY_FACTORS = ("confidence", "vulnerability", "aggregator")


def _boolean_factorial(factors: Sequence[str]) -> list[dict[str, bool]]:
    rows = [
        dict(zip(factors, values, strict=True))
        for values in itertools.product((False, True), repeat=len(factors))
    ]
    return sorted(rows, key=config_sha256)


def clustering_factorial_variants() -> list[dict[str, bool]]:
    variants = _boolean_factorial(CLUSTERING_FACTORS)
    if len(variants) != 16:
        raise RuntimeError("clustering factorial must contain exactly 16 cells")
    return variants


def priority_factorial_variants() -> list[dict[str, bool]]:
    variants = _boolean_factorial(PRIORITY_FACTORS)
    if len(variants) != 8:
        raise RuntimeError("priority factorial must contain exactly 8 cells")
    return variants


def build_factorial_affinity(
    geographic: np.ndarray,
    temporal: np.ndarray,
    contextual: np.ndarray,
    variant: Mapping[str, bool],
) -> np.ndarray:
    """Remove disabled formula components using their multiplicative neutral."""

    matrices = [
        np.asarray(geographic, dtype=float),
        np.asarray(temporal, dtype=float),
        np.asarray(contextual, dtype=float),
    ]
    if any(
        matrix.ndim != 2
        or matrix.shape != matrices[0].shape
        or matrix.shape[0] != matrix.shape[1]
        for matrix in matrices
    ):
        raise ValueError("primitive similarities must be equally sized square matrices")
    if any(not np.isfinite(matrix).all() for matrix in matrices):
        raise ValueError("primitive similarities must be finite")
    n_events = matrices[0].shape[0]
    neutral = np.ones((n_events, n_events), dtype=float)
    np.fill_diagonal(neutral, 0.0)

    gate = geographic if variant["geography"] else neutral
    active_inner: list[np.ndarray] = []
    if variant["time"]:
        active_inner.append(temporal)
    if variant["context"]:
        active_inner.append(contextual)
    inner = (
        sum(active_inner) / len(active_inner)
        if active_inner
        else neutral
    )
    affinity = np.asarray(gate * inner, dtype=float)
    np.fill_diagonal(affinity, 0.0)
    return affinity


def _incident_priority_rank_correlation(
    labels: Sequence[int],
    scores: Sequence[Any],
    ground_truth: Sequence[int],
    incidents: Sequence[Mapping[str, Any]],
) -> float:
    by_cluster = {int(score.cluster_id): float(score.priority) for score in scores}
    predictions: dict[int, list[float]] = {}
    for label, incident_label in zip(labels, ground_truth, strict=True):
        if incident_label >= 0:
            predictions.setdefault(int(incident_label), []).append(
                by_cluster[int(label)]
            )
    if not predictions:
        return 0.0

    max_population = max(float(incident["n_true"]) for incident in incidents)
    truth_by_label: dict[int, float] = {}
    for incident in incidents:
        profile = incident["generator_profile"]
        population = math.log1p(float(incident["n_true"])) / math.log1p(max_population)
        core = (
            float(profile["urgency_latent"])
            + float(profile["flood_latent"])
            + population
        ) / 3.0
        multiplier = 1.0 + math.tanh(
            float(incident["v_true"]) / DEFAULT_CONFIG.priority.v_scale
        )
        truth_by_label[int(incident["gt_cluster"])] = core * multiplier

    labels_in_both = sorted(set(predictions) & set(truth_by_label))
    predicted = [
        max(predictions[incident_label]) for incident_label in labels_in_both
    ]
    truth = [truth_by_label[incident_label] for incident_label in labels_in_both]
    if len(predicted) < 2 or len(set(predicted)) < 2 or len(set(truth)) < 2:
        return 0.0
    correlation = spearmanr(predicted, truth).statistic
    return 0.0 if not math.isfinite(float(correlation)) else float(correlation)


def evaluate_loaded_factorial_seed(
    dataset: Any,
    *,
    product_config: Mapping[str, Any],
    stage: str,
) -> dict[str, list[dict[str, Any]]]:
    """Evaluate every frozen factorial cell on one authenticated loaded view.

    This post-load entry point is used by the held-out suite.  It has no seed
    selection, search-space, or early-stopping argument, and therefore cannot
    expose an intermediate test subset for tuning.
    """

    if not isinstance(stage, str) or not stage:
        raise ValueError("stage must be a non-empty string")
    if dataset.ground_truth is None:
        raise RuntimeError("factorial evidence requires the evaluator view")
    if any(
        event.gt_cluster != -1 or event.is_fake is not False
        for event in dataset.events
    ):
        raise ValueError("evaluator-only fields leaked into factorial inputs")

    params = _weight_params(product_config)
    resolution = float(product_config["resolution"])
    selected_knn = int(product_config.get("knn", DEFAULT_CONFIG.weight.knn))
    seed = int(dataset.seed)
    events = list(dataset.events)
    truth = list(dataset.ground_truth)
    reference_dense = build_weight_matrix_vec(events, params, mode="gating")
    reference_graph, reference_threshold = sparsify_at_quantile(
        reference_dense,
        float(product_config["threshold_quantile"]),
        knn=selected_knn,
    )
    reference_density = graph_density(reference_graph)
    geographic, temporal, contextual = primitive_similarity_matrices(
        events,
        params,
    )

    clustering_rows: list[dict[str, Any]] = []
    for variant in clustering_factorial_variants():
        started = time.perf_counter()
        base_row: dict[str, Any] = {
            "seed": seed,
            "stage": stage,
            **variant,
            "variant_sha256": config_sha256(variant),
            "source_sha256": dataset.source_sha256,
        }
        try:
            affinity = build_factorial_affinity(
                geographic,
                temporal,
                contextual,
                variant,
            )
            knn = selected_knn if variant["knn"] else 0
            match = find_density_match(
                affinity,
                reference_density,
                knn_candidates=(knn,),
            )
            graph = sparsify(
                affinity,
                replace(
                    params,
                    edge_threshold=match.threshold,
                    knn=knn,
                ),
            )
            labels = run_louvain(
                graph,
                resolution=resolution,
                random_state=seed,
            )
            quality = cluster_quality(labels, truth)
            clustering_rows.append(
                {
                    **base_row,
                    "status": "succeeded",
                    "error": None,
                    "ari_labeled_reports": float(quality["ari"]),
                    "ari_denominator": int(quality["n_eval"]),
                    "reference_threshold": reference_threshold,
                    "matched_threshold": match.threshold,
                    "retained_fraction": match.density.retained_fraction,
                    "mean_degree": match.density.mean_degree,
                    "retained_fraction_absolute_error": float(
                        match.diagnostics["retained_fraction_absolute_error"]
                    ),
                    "mean_degree_relative_error": float(
                        match.diagnostics["mean_degree_relative_error"]
                    ),
                    "density_matched": bool(match.diagnostics["matched"]),
                    "wall_time_seconds": round(
                        time.perf_counter() - started,
                        6,
                    ),
                }
            )
        except Exception as exc:
            clustering_rows.append(
                {
                    **base_row,
                    "status": "failed",
                    "error": {
                        "exception_type": type(exc).__name__,
                        "message": str(exc),
                    },
                    "wall_time_seconds": round(
                        time.perf_counter() - started,
                        6,
                    ),
                }
            )

    full_labels = run_louvain(
        reference_graph,
        resolution=resolution,
        random_state=seed,
    )
    priority_rows: list[dict[str, Any]] = []
    for variant in priority_factorial_variants():
        started = time.perf_counter()
        base_row = {
            "seed": seed,
            "stage": stage,
            **variant,
            "variant_sha256": config_sha256(variant),
            "source_sha256": dataset.source_sha256,
        }
        try:
            priority_params = replace(
                DEFAULT_CONFIG.priority,
                v_cap_mu=(
                    DEFAULT_CONFIG.priority.v_cap_mu
                    if variant["vulnerability"]
                    else 1.0
                ),
            )
            scores = score_clusters(
                events,
                full_labels,
                priority_params,
                gate_confidence=variant["confidence"],
                gate_fmax=variant["confidence"],
                normalize_v=True,
                estimator=(
                    "duplicate_aware_robust"
                    if variant["aggregator"]
                    else "legacy_raw"
                ),
            )
            correlation = _incident_priority_rank_correlation(
                full_labels,
                scores,
                truth,
                dataset.incidents,
            )
            priority_rows.append(
                {
                    **base_row,
                    "status": "succeeded",
                    "error": None,
                    "priority_rank_correlation": correlation,
                    "incident_denominator": len(dataset.incidents),
                    "wall_time_seconds": round(
                        time.perf_counter() - started,
                        6,
                    ),
                }
            )
        except Exception as exc:
            priority_rows.append(
                {
                    **base_row,
                    "status": "failed",
                    "error": {
                        "exception_type": type(exc).__name__,
                        "message": str(exc),
                    },
                    "wall_time_seconds": round(
                        time.perf_counter() - started,
                        6,
                    ),
                }
            )
    return {
        "clustering_rows": clustering_rows,
        "priority_rows": priority_rows,
    }


def run_factorial_ablation(
    dataset_root: Path | str,
    *,
    product_config: Mapping[str, Any],
    stage: str = "calibration",
    seed_limit: int | None = None,
    protocol: TuningProtocol | None = None,
) -> dict[str, Any]:
    locked = protocol or load_tuning_protocol()
    if stage not in {"development", "calibration"}:
        raise ValueError("stage must be development or calibration")
    frozen_root, frozen_record = resolve_frozen_dataset_root(dataset_root)
    seeds = locked.seeds_for(stage)  # type: ignore[arg-type]
    if seed_limit is not None:
        if (
            isinstance(seed_limit, bool)
            or not isinstance(seed_limit, int)
            or not 1 <= seed_limit <= len(seeds)
        ):
            raise ValueError("seed_limit must select a non-empty tuning prefix")
        seeds = seeds[:seed_limit]

    params = _weight_params(product_config)
    resolution = float(product_config["resolution"])
    selected_knn = int(product_config.get("knn", DEFAULT_CONFIG.weight.knn))
    clustering_rows: list[dict[str, Any]] = []
    priority_rows: list[dict[str, Any]] = []

    for seed in seeds:
        dataset = load_tuning_dataset(
            frozen_root,
            stage=stage,  # type: ignore[arg-type]
            seed=seed,
            tuning_protocol=locked,
            calibration_labels=True,
        )
        if dataset.ground_truth is None:
            raise RuntimeError("factorial evidence requires the calibration evaluator view")
        events = list(dataset.events)
        truth = list(dataset.ground_truth)

        reference_dense = build_weight_matrix_vec(events, params, mode="gating")
        reference_graph, reference_threshold = sparsify_at_quantile(
            reference_dense,
            float(product_config["threshold_quantile"]),
            knn=selected_knn,
        )
        reference_density = graph_density(reference_graph)
        geographic, temporal, contextual = primitive_similarity_matrices(
            events, params
        )

        for variant in clustering_factorial_variants():
            started = time.perf_counter()
            base_row: dict[str, Any] = {
                "seed": seed,
                **variant,
                "variant_sha256": config_sha256(variant),
                "source_sha256": dataset.source_sha256,
            }
            try:
                affinity = build_factorial_affinity(
                    geographic,
                    temporal,
                    contextual,
                    variant,
                )
                knn = selected_knn if variant["knn"] else 0
                match = find_density_match(
                    affinity,
                    reference_density,
                    knn_candidates=(knn,),
                )
                graph = sparsify(
                    affinity,
                    replace(
                        params,
                        edge_threshold=match.threshold,
                        knn=knn,
                    ),
                )
                labels = run_louvain(
                    graph,
                    resolution=resolution,
                    random_state=seed,
                )
                quality = cluster_quality(labels, truth)
                clustering_rows.append(
                    {
                        **base_row,
                        "status": "succeeded",
                        "error": None,
                        "ari_labeled_reports": float(quality["ari"]),
                        "ari_denominator": int(quality["n_eval"]),
                        "reference_threshold": reference_threshold,
                        "matched_threshold": match.threshold,
                        "retained_fraction": match.density.retained_fraction,
                        "mean_degree": match.density.mean_degree,
                        "retained_fraction_absolute_error": float(
                            match.diagnostics[
                                "retained_fraction_absolute_error"
                            ]
                        ),
                        "mean_degree_relative_error": float(
                            match.diagnostics["mean_degree_relative_error"]
                        ),
                        "density_matched": bool(match.diagnostics["matched"]),
                        "wall_time_seconds": round(
                            time.perf_counter() - started,
                            6,
                        ),
                    }
                )
            except Exception as exc:
                clustering_rows.append(
                    {
                        **base_row,
                        "status": "failed",
                        "error": {
                            "exception_type": type(exc).__name__,
                            "message": str(exc),
                        },
                        "wall_time_seconds": round(
                            time.perf_counter() - started,
                            6,
                        ),
                    }
                )

        full_labels = run_louvain(
            reference_graph,
            resolution=resolution,
            random_state=seed,
        )
        for variant in priority_factorial_variants():
            started = time.perf_counter()
            base_row = {
                "seed": seed,
                **variant,
                "variant_sha256": config_sha256(variant),
                "source_sha256": dataset.source_sha256,
            }
            try:
                priority_params = replace(
                    DEFAULT_CONFIG.priority,
                    v_cap_mu=(
                        DEFAULT_CONFIG.priority.v_cap_mu
                        if variant["vulnerability"]
                        else 1.0
                    ),
                )
                scores = score_clusters(
                    events,
                    full_labels,
                    priority_params,
                    gate_confidence=variant["confidence"],
                    gate_fmax=variant["confidence"],
                    normalize_v=True,
                    estimator=(
                        "duplicate_aware_robust"
                        if variant["aggregator"]
                        else "legacy_raw"
                    ),
                )
                correlation = _incident_priority_rank_correlation(
                    full_labels,
                    scores,
                    truth,
                    dataset.incidents,
                )
                priority_rows.append(
                    {
                        **base_row,
                        "status": "succeeded",
                        "error": None,
                        "priority_rank_correlation": correlation,
                        "incident_denominator": len(dataset.incidents),
                        "wall_time_seconds": round(
                            time.perf_counter() - started,
                            6,
                        ),
                    }
                )
            except Exception as exc:
                priority_rows.append(
                    {
                        **base_row,
                        "status": "failed",
                        "error": {
                            "exception_type": type(exc).__name__,
                            "message": str(exc),
                        },
                        "wall_time_seconds": round(
                            time.perf_counter() - started,
                            6,
                        ),
                    }
                )

    failed_clustering = [
        row for row in clustering_rows if row["status"] != "succeeded"
    ]
    failed_priority = [
        row for row in priority_rows if row["status"] != "succeeded"
    ]
    clustering_effects = (
        []
        if failed_clustering
        else factorial_effect_summaries(
            clustering_rows,
            factors=CLUSTERING_FACTORS,
            outcome="ari_labeled_reports",
        )
    )
    priority_effects = (
        []
        if failed_priority
        else factorial_effect_summaries(
            priority_rows,
            factors=PRIORITY_FACTORS,
            outcome="priority_rank_correlation",
        )
    )
    return {
        "schema_version": "factorial-ablation-v1",
        "stage": stage,
        "complete_seed_set": seed_limit is None,
        "seed_limit": seed_limit,
        "protocol_sha256": locked.protocol_sha256,
        "frozen_dataset": frozen_record,
        "product_config": dict(product_config),
        "product_config_sha256": config_sha256(product_config),
        "clustering": {
            "factors": list(CLUSTERING_FACTORS),
            "variant_count": 16,
            "rows": clustering_rows,
            "effects": clustering_effects,
            "effect_orders": [1, 2, 3, 4],
            "effects_status": (
                "unavailable_due_to_retained_failures"
                if failed_clustering
                else "complete"
            ),
            "evaluation_count": len(clustering_rows),
            "expected_evaluation_count": len(seeds) * 16,
            "failed_evaluation_count": len(failed_clustering),
            "wall_time_seconds": round(
                sum(float(row["wall_time_seconds"]) for row in clustering_rows),
                6,
            ),
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
            "effects": priority_effects,
            "effect_orders": [1, 2, 3],
            "effects_status": (
                "unavailable_due_to_retained_failures"
                if failed_priority
                else "complete"
            ),
            "evaluation_count": len(priority_rows),
            "expected_evaluation_count": len(seeds) * 8,
            "failed_evaluation_count": len(failed_priority),
            "wall_time_seconds": round(
                sum(float(row["wall_time_seconds"]) for row in priority_rows),
                6,
            ),
        },
        "inference": {
            "unit": "paired_seed",
            "confidence_interval": "paired bootstrap",
            "hypothesis_test": "paired Wilcoxon signed-rank",
            "multiplicity": "Holm within clustering and priority families",
            "all_interaction_orders_reported": True,
            "failed_cells_retained": True,
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run complete clustering and priority factorial ablations."
    )
    parser.add_argument("--dataset-root", type=Path)
    parser.add_argument("--composition-artifact", type=Path, required=True)
    parser.add_argument(
        "--track",
        default="benchmark_label_aware",
        choices=("benchmark_label_aware",),
    )
    parser.add_argument(
        "--stage",
        choices=("development", "calibration"),
        default="calibration",
    )
    parser.add_argument("--seed-limit", type=int)
    parser.add_argument("--output", type=Path)
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    protocol = load_tuning_protocol()
    product_selections = load_product_selections(
        args.composition_artifact,
        protocol=protocol,
    )
    if args.track not in product_selections:
        raise ValueError(f"no frozen product selection for track {args.track!r}")
    result = run_factorial_ablation(
        args.dataset_root or default_frozen_dataset_root(),
        product_config=product_selections[args.track],
        stage=args.stage,
        seed_limit=args.seed_limit,
        protocol=protocol,
    )
    output = args.output or default_table_path("exp19_factorial_ablation.json")
    write_exclusive_json(output, result)
    print(
        json.dumps(
            {
                "output": str(output),
                "clustering_rows": len(result["clustering"]["rows"]),
                "priority_rows": len(result["priority"]["rows"]),
                "density_match_failures": result["clustering"][
                    "density_match_failures"
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
