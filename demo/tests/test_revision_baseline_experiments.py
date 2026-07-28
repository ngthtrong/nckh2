from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import numpy as np

from demo.experiments.exp15_calibrated_comparison import (
    calibrate_composition_methods,
    default_frozen_dataset_root,
    evaluate_composition_seed,
)
from demo.experiments.exp18_tuned_baselines import (
    evaluate_baseline_seed,
    tune_registered_baselines,
)
from demo.experiments.exp19_factorial_ablation import (
    build_factorial_affinity,
    clustering_factorial_variants,
    priority_factorial_variants,
)
from demo.pipeline.attributes import Event, compute_confidence
from demo.pipeline.config import DEFAULT_CONFIG


def _dataset() -> SimpleNamespace:
    events = []
    truth = []
    for cluster, (lat, lng) in enumerate(((16.0, 107.0), (16.2, 107.2))):
        for offset in range(4):
            events.append(
                Event(
                    event_id=f"E{cluster}-{offset}",
                    lat=lat + offset * 0.00005,
                    lng=lng + offset * 0.00005,
                    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc)
                    + timedelta(minutes=offset),
                    flood=0.3 + 0.4 * cluster,
                    urgency=0.4 + 0.3 * cluster,
                    n_trapped=5 + cluster,
                    vulnerability=1.0,
                    has_image=True,
                )
            )
            truth.append(cluster)
    compute_confidence(events, DEFAULT_CONFIG.confidence)
    return SimpleNamespace(seed=11, events=tuple(events), ground_truth=tuple(truth))


def test_composition_evaluator_exposes_labels_only_when_allowed() -> None:
    config = {
        "sigma_geo_m": 700,
        "tau_temp_min": 60,
        "threshold_quantile": 0.85,
        "knn": 4,
        "resolution": 1.0,
    }
    labeled = evaluate_composition_seed(
        "product_louvain", config, _dataset(), calibration_labels=True
    )
    label_free = evaluate_composition_seed(
        "product_louvain", config, _dataset(), calibration_labels=False
    )
    assert "ari_labeled_reports" in labeled
    assert "ari_labeled_reports" not in label_free
    assert {"retained_fraction", "mean_degree", "operator_review_burden"} <= set(
        label_free
    )
    assert "partition_stability" in label_free


def test_convex_evaluator_rejects_non_simplex_weights_even_when_precomputed() -> None:
    dataset = _dataset()
    with np.testing.assert_raises_regex(ValueError, "summing to 1"):
        evaluate_composition_seed(
            "multiple_similarity_louvain",
            {
                "simplex_weights": [0.4, 0.4, 0.4],
                "threshold_quantile": 0.9,
                "knn": 4,
                "resolution": 1.0,
            },
            dataset,
            calibration_labels=False,
            precomputed_similarity=np.eye(len(dataset.events)),
        )


def test_tuners_reject_duplicate_method_scopes_before_evaluation() -> None:
    root = default_frozen_dataset_root()
    with np.testing.assert_raises_regex(ValueError, "unique"):
        calibrate_composition_methods(
            root,
            track_ids=("benchmark_label_aware",),
            method_ids=("product_louvain", "product_louvain"),
            seed_limit=1,
        )
    with np.testing.assert_raises_regex(ValueError, "unique"):
        tune_registered_baselines(
            root,
            track_ids=("benchmark_label_aware",),
            method_ids=("coordinate_kmeans", "coordinate_kmeans"),
            seed_limit=1,
        )


def test_each_new_direct_adapter_is_wired_into_exp18() -> None:
    dataset = _dataset()
    configs = {
        "st_dbscan": {
            "spatial_eps_m": 500,
            "temporal_eps_min": 30,
            "min_samples": 3,
        },
        "dbscan_geo_time_context": {
            "eps": 1.0,
            "min_samples": 3,
            "scaler": "standard",
        },
        "hdbscan_geo_time_context": {
            "min_cluster_size": 3,
            "min_samples": 3,
            "scaler": "robust",
        },
        "spatial_constrained_agglomerative": {
            "connectivity_radius_m": 500,
            "n_clusters": 2,
            "time_context_mix": 0.5,
        },
    }
    for method, config in configs.items():
        metrics = evaluate_baseline_seed(
            method,
            config,
            dataset,
            calibration_labels=True,
        )
        assert "ari_labeled_reports" in metrics
        assert "operator_review_burden" in metrics


def test_factorial_has_exact_declared_cells_and_neutral_removal() -> None:
    clustering = clustering_factorial_variants()
    priority = priority_factorial_variants()
    assert len(clustering) == 16
    assert len(priority) == 8
    assert len({tuple(sorted(row.items())) for row in clustering}) == 16
    assert len({tuple(sorted(row.items())) for row in priority}) == 8

    geographic = np.array([[0.0, 0.2], [0.2, 0.0]])
    temporal = np.array([[0.0, 0.4], [0.4, 0.0]])
    context = np.array([[0.0, 0.8], [0.8, 0.0]])
    full = build_factorial_affinity(
        geographic,
        temporal,
        context,
        {"geography": True, "time": True, "context": True, "knn": True},
    )
    geo_only = build_factorial_affinity(
        geographic,
        temporal,
        context,
        {"geography": True, "time": False, "context": False, "knn": False},
    )
    assert np.isclose(full[0, 1], 0.2 * (0.4 + 0.8) / 2)
    assert np.isclose(geo_only[0, 1], 0.2)
