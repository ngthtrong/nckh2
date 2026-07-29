from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from demo.experiments import exp18_tuned_baselines as exp18
from demo.experiments import evaluation_data as evaluation_release
from demo.experiments.calibration import (
    CandidateEvaluation,
    aggregate_seed_metrics,
    calibration_artifact_content_sha256,
    config_sha256,
    density_match_diagnostics,
    expand_search_space,
    load_calibration_contract,
    operational_selection_constraints,
    select_candidate,
    selection_identity_sha256,
    write_calibration_artifact,
)
from demo.experiments.exp15_calibrated_comparison import (
    BASELINE_REGISTRY,
    COMPOSITION_METHODS,
    _load_registry,
    _registry_methods,
    calibrate_composition_methods,
    default_frozen_dataset_root,
    evaluate_composition_seed,
)
from demo.experiments.exp18_tuned_baselines import (
    evaluate_baseline_seed,
    load_product_selections,
    tune_registered_baselines,
)
from demo.experiments.exp19_factorial_ablation import (
    build_factorial_affinity,
    clustering_factorial_variants,
    priority_factorial_variants,
)
from demo.pipeline.attributes import Event, compute_confidence
from demo.pipeline.config import DEFAULT_CONFIG
from demo.experiments.protocol import load_tuning_protocol


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


def test_same_representation_baseline_reports_graph_connectivity() -> None:
    metrics = evaluate_baseline_seed(
        "product_leiden",
        {"resolution": 1.0},
        _dataset(),
        calibration_labels=True,
        product_config={
            "sigma_geo_m": 700,
            "tau_temp_min": 60,
            "threshold_quantile": 0.85,
            "knn": 4,
            "resolution": 1.0,
        },
    )
    assert metrics["disconnected_communities"] == 0.0
    assert 0.0 < metrics["retained_fraction"] <= 1.0


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


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _full_synthetic_composition_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, dict[str, object]]:
    """Build the complete registered Exp15 grid without running clustering."""

    protocol = load_tuning_protocol()
    contract = load_calibration_contract()
    methods = _registry_methods(_load_registry(BASELINE_REGISTRY))
    track_ids = tuple(track.id for track in protocol.tracks)
    evaluations: list[CandidateEvaluation] = []
    by_pair: dict[tuple[str, str], list[CandidateEvaluation]] = {}
    for track in protocol.tracks:
        objective, _ = contract.objectives[track.id]
        for method_id in COMPOSITION_METHODS:
            configs = expand_search_space(
                methods[method_id]["search_space"],
                maximum=protocol.max_candidates_per_method_track,
            )
            rows: list[CandidateEvaluation] = []
            for rank, config in enumerate(configs):
                score = 0.91 + 0.08 * rank / max(1, len(configs) - 1)
                seed_metrics: list[dict[str, float]] = []
                for seed in protocol.calibration_seeds:
                    metrics = {
                        "seed": float(seed),
                        "partition_stability": (
                            score
                            if objective == "partition_stability"
                            else 1.0
                        ),
                        "operator_review_burden_rate": 0.1,
                        "geographic_diameter": 1000.0,
                        "disconnected_communities": 0.0,
                        "retained_fraction": 0.1,
                        "mean_degree": 10.0,
                        "operator_review_burden": 1.0,
                        "complexity": float(len(config)),
                    }
                    if track.calibration_labels:
                        metrics["ari_labeled_reports"] = score
                    seed_metrics.append(metrics)
                candidate = CandidateEvaluation(
                    method_id=method_id,
                    track_id=track.id,
                    stage="calibration",
                    config=dict(config),
                    config_sha256=config_sha256(config),
                    status="succeeded",
                    seed_metrics=tuple(seed_metrics),
                    aggregate_metrics=aggregate_seed_metrics(seed_metrics),
                    failures=(),
                    configuration_evaluation_count=1,
                    seed_run_count=len(protocol.calibration_seeds),
                    wall_time_seconds=0.1,
                )
                rows.append(candidate)
                evaluations.append(candidate)
            by_pair[(method_id, track.id)] = rows

    constraints = operational_selection_constraints(contract, graph_method=True)
    raw_selections = {
        (method_id, track_id): select_candidate(
            by_pair[(method_id, track_id)],
            objective=contract.objectives[track_id][0],
            direction=contract.objectives[track_id][1],
            constraints=constraints,
        )
        for track_id in track_ids
        for method_id in COMPOSITION_METHODS
    }
    selections = [
        raw_selections[(method_id, track_id)]
        for track_id in track_ids
        for method_id in COMPOSITION_METHODS
    ]
    comparators = [
        method_id
        for method_id in COMPOSITION_METHODS
        if method_id != "product_louvain"
    ]
    joint_audit = [
        {
            "track_id": track_id,
            "required_comparators": comparators,
            "joint_matchable_product_configurations": len(
                by_pair[("product_louvain", track_id)]
            ),
            "joint_product_selection_status": raw_selections[
                ("product_louvain", track_id)
            ].status,
            "joint_product_selection_sha256": raw_selections[
                ("product_louvain", track_id)
            ].selection_sha256,
        }
        for track_id in track_ids
    ]
    match_rows: list[dict[str, object]] = []
    for track_id in track_ids:
        product_selection = raw_selections[("product_louvain", track_id)]
        product = next(
            row
            for row in by_pair[("product_louvain", track_id)]
            if row.config_sha256 == product_selection.selected_config_sha256
        )
        for method_id in COMPOSITION_METHODS:
            selection = raw_selections[(method_id, track_id)]
            candidate = next(
                row
                for row in by_pair[(method_id, track_id)]
                if row.config_sha256 == selection.selected_config_sha256
            )
            match_rows.append(
                {
                    "method_id": method_id,
                    "track_id": track_id,
                    **density_match_diagnostics(
                        {
                            "retained_fraction": product.aggregate_metrics[
                                "retained_fraction"
                            ],
                            "mean_degree": product.aggregate_metrics["mean_degree"],
                        },
                        {
                            "retained_fraction": candidate.aggregate_metrics[
                                "retained_fraction"
                            ],
                            "mean_degree": candidate.aggregate_metrics["mean_degree"],
                        },
                    ),
                }
            )

    _, frozen_record = exp18.resolve_frozen_dataset_root()
    metadata = {
        "stage": "calibration",
        "complete_seed_set": True,
        "seed_limit": None,
        "raw_unmatched_selections": [
            selection.to_dict() for selection in selections
        ],
        "joint_composition_selection": joint_audit,
        "matched_density_degree": match_rows,
        "matched_retained_fraction_tolerance": (
            contract.retained_fraction_match_tolerance
        ),
        "matched_mean_degree_relative_tolerance": (
            contract.mean_degree_match_relative_tolerance
        ),
        "negative_tie_failure_policy": "all candidate rows retained",
        "calibration_contract_sha256": contract.source_sha256,
        "frozen_dataset": frozen_record,
    }
    tables = tmp_path / "sealed-exp15" / "tables"
    tables.mkdir(parents=True)
    artifact_path = tables / "exp15_calibrated_comparison.json"
    write_calibration_artifact(
        artifact_path,
        protocol=protocol,
        evaluations=evaluations,
        selections=selections,
        metadata=metadata,
    )

    def sealed_manifest(manifest_path: Path | str) -> dict[str, object]:
        run_root = Path(manifest_path).parent
        checksums = {
            table.relative_to(run_root).as_posix(): hashlib.sha256(
                table.read_bytes()
            ).hexdigest()
            for table in (run_root / "tables").glob("*.json")
        }
        return {
            "status": "succeeded",
            "exit_code": 0,
            "command": [
                "python",
                "-m",
                "demo.experiments.exp15_calibrated_comparison",
                "--stage",
                "calibration",
            ],
            "checksums": checksums,
            "inputs": {
                "protocol": {"sha256": protocol.protocol_sha256},
                "datasets": [
                    {
                        "source": (
                            f"{frozen_record['dataset_root']}/manifest.json"
                        ),
                        "snapshot": "inputs/datasets/00-manifest.json",
                        "sha256": frozen_record["dataset_manifest_sha256"],
                    }
                ],
            },
        }

    original_manifest = sealed_manifest

    def sealed_manifest_with_dataset(
        manifest_path: Path | str,
    ) -> dict[str, object]:
        manifest = original_manifest(manifest_path)
        manifest["checksums"]["inputs/datasets/00-manifest.json"] = (
            frozen_record["dataset_manifest_sha256"]
        )
        return manifest

    monkeypatch.setattr(
        exp18,
        "validate_manifest",
        sealed_manifest_with_dataset,
    )
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    return artifact_path, artifact


def test_product_selection_loader_recomputes_seed_metrics_and_winner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact_path, valid = _full_synthetic_composition_artifact(
        tmp_path,
        monkeypatch,
    )
    selected = load_product_selections(artifact_path)
    assert set(selected) == {
        "benchmark_label_aware",
        "operational_label_free",
    }
    protocol = load_tuning_protocol()
    evaluation_index = evaluation_release._calibration_evaluation_index(
        valid,
        calibration_seeds=protocol.calibration_seeds,
    )
    evaluation_release._verify_mechanical_selections(
        valid,
        evaluation_index,
        policy=evaluation_release._selection_policy(
            evaluation_release.DEFAULT_PROTOCOL_DIR
        ),
    )

    forged = json.loads(json.dumps(valid))
    selection = next(
        row
        for row in forged["selections"]
        if row["method_id"] == "product_louvain"
        and row["track_id"] == "benchmark_label_aware"
    )
    better_hash = selection["selected_config_sha256"]
    replacement = next(
        row
        for row in forged["evaluations"]
        if row["method_id"] == "product_louvain"
        and row["track_id"] == "benchmark_label_aware"
        and row["config_sha256"] != better_hash
    )
    selection["selected_config"] = replacement["config"]
    selection["selected_config_sha256"] = replacement["config_sha256"]
    selection["selection_sha256"] = selection_identity_sha256(
        method_id=selection["method_id"],
        track_id=selection["track_id"],
        objective=selection["objective"],
        direction=selection["direction"],
        selected_config_sha256=replacement["config_sha256"],
    )
    forged["artifact_content_sha256"] = calibration_artifact_content_sha256(
        forged
    )
    forged_path = artifact_path.with_name("forged-nonoptimal.json")
    _write_json(forged_path, forged)
    with pytest.raises(ValueError, match="winner/audit is not mechanically"):
        load_product_selections(forged_path)
    forged_index = evaluation_release._calibration_evaluation_index(
        forged,
        calibration_seeds=protocol.calibration_seeds,
    )
    with pytest.raises(
        evaluation_release.EvaluationDataError,
        match="winner/audit is not mechanically",
    ):
        evaluation_release._verify_mechanical_selections(
            forged,
            forged_index,
            policy=evaluation_release._selection_policy(
                evaluation_release.DEFAULT_PROTOCOL_DIR
            ),
        )

    missing_seed_rows = json.loads(json.dumps(valid))
    missing_seed_rows["evaluations"][0]["seed_metrics"] = []
    missing_seed_rows["evaluations"][0]["aggregate_metrics"] = {}
    missing_seed_rows["artifact_content_sha256"] = (
        calibration_artifact_content_sha256(missing_seed_rows)
    )
    missing_path = artifact_path.with_name("forged-empty-seed-metrics.json")
    _write_json(missing_path, missing_seed_rows)
    with pytest.raises(ValueError, match="exact calibration seed set"):
        load_product_selections(missing_path)
