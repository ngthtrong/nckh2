from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from demo.experiments.exp22_runtime_repro import (
    MEASURED_REPEATS,
    _verified_dataset_path,
    packet_payload,
    packet_size_summary,
    summarize_repeats,
)
from demo.pipeline.attributes import Event
from demo.pipeline.clustering import run_louvain
from demo.pipeline.config import WeightParams
from demo.pipeline.spatial_weighting import (
    build_product_graph_spatial,
    partitions_equivalent,
)
from demo.pipeline.weighting import build_weight_matrix_vec, sparsify


def _event(
    identifier: str,
    north_degrees: float,
    minute: int,
    *,
    confidence: float = 0.42,
) -> Event:
    return Event(
        event_id=identifier,
        lat=16.0 + north_degrees,
        lng=108.0,
        created_at=datetime(2026, 7, 1, tzinfo=timezone.utc)
        + timedelta(minutes=minute),
        flood=0.6,
        urgency=0.7,
        n_trapped=4,
        vulnerability=1.5,
        has_image=True,
        source_type="hotline",
        province="Đà Nẵng",
        missing_fields=("urgency",),
        confidence=confidence,
    )


def test_spatial_product_graph_matches_dense_threshold_and_partition() -> None:
    events = [
        _event("a", 0.0, 0),
        _event("b", 0.002, 3),
        _event("c", 0.004, 6),
        _event("d", 0.15, 0),
        _event("e", 0.152, 3),
    ]
    params = WeightParams(
        sigma_geo_m=700.0,
        tau_temp_min=45.0,
        tau_f=0.25,
        tau_e=0.35,
        beta=0.5,
        gamma=0.5,
        edge_threshold=0.05,
        knn=2,
    )
    dense = sparsify(build_weight_matrix_vec(events, params), params)
    spatial = build_product_graph_spatial(events, params)

    assert spatial.bound.status == "finite"
    assert spatial.candidate_pairs < spatial.total_pairs
    assert np.max(np.abs(dense - spatial.matrix)) <= 1e-12
    assert partitions_equivalent(
        run_louvain(dense, random_state=7),
        run_louvain(spatial.matrix, random_state=7),
    )


def test_spatial_graph_matches_dense_at_strict_threshold_rounding_boundary() -> None:
    events = [
        replace(
            _event("boundary-a", 0.0, 0),
            lat=74.793369760758,
            lng=162.712117526391,
            flood=0.5,
            urgency=0.5,
        ),
        replace(
            _event("boundary-b", 0.0, 0),
            lat=74.80455981449913,
            lng=162.67171557943652,
            flood=0.5,
            urgency=0.5,
        ),
    ]
    params = WeightParams(
        sigma_geo_m=700.0,
        tau_temp_min=45.0,
        tau_f=0.25,
        tau_e=0.35,
        beta=0.5,
        gamma=0.5,
        edge_threshold=0.05,
        knn=0,
    )

    dense = sparsify(build_weight_matrix_vec(events, params), params)
    spatial = build_product_graph_spatial(events, params)

    assert dense[0, 1] > params.edge_threshold
    assert np.array_equal(spatial.matrix, dense)
    assert spatial.retained_edges == 1


def test_spatial_graph_matches_dense_near_poles_and_date_line() -> None:
    base = _event("base", 0.0, 0)
    coordinates = (
        (89.9999, 179.9999),
        (89.9998, -179.9999),
        (-89.9999, 179.9998),
        (-89.9998, -179.9998),
        (0.0, 179.9999),
        (0.0, -179.9999),
    )
    events = [
        replace(
            base,
            event_id=f"edge-{index}",
            lat=latitude,
            lng=longitude,
            created_at=base.created_at + timedelta(minutes=index * 3),
            flood=0.1 * index,
            urgency=1.0 - 0.1 * index,
        )
        for index, (latitude, longitude) in enumerate(coordinates)
    ]
    params = WeightParams(
        sigma_geo_m=2_000_000.0,
        tau_temp_min=120.0,
        tau_f=0.5,
        tau_e=0.5,
        beta=0.5,
        gamma=0.5,
        edge_threshold=0.02,
        knn=2,
    )

    dense = sparsify(build_weight_matrix_vec(events, params), params)
    spatial = build_product_graph_spatial(events, params)

    assert np.array_equal(spatial.matrix, dense)
    assert spatial.retained_edges == int(np.count_nonzero(np.triu(dense, 1)))


def test_spatial_graph_matches_dense_on_random_parameters_with_knn() -> None:
    random = np.random.default_rng(20260729)
    base = _event("base", 0.0, 0)
    for trial in range(32):
        event_count = 9
        latitudes = random.uniform(-89.9999, 89.9999, event_count)
        longitudes = random.uniform(-180.0, 180.0, event_count)
        if trial % 2 == 0:
            longitudes[:2] = (179.9999, -179.9999)
        if trial % 3 == 0:
            latitudes[2:4] = (89.9999, -89.9999)
        events = [
            replace(
                base,
                event_id=f"random-{trial}-{index}",
                lat=float(latitudes[index]),
                lng=float(longitudes[index]),
                created_at=base.created_at
                + timedelta(minutes=int(random.integers(0, 1440))),
                flood=float(random.random()),
                urgency=float(random.random()),
            )
            for index in range(event_count)
        ]
        coefficient_sum = float(random.uniform(0.05, 2.0))
        beta_share = float(random.random())
        threshold_fraction = float(
            random.choice((1e-10, 0.001, 0.05, 0.5, 0.9999999999))
        )
        params = WeightParams(
            sigma_geo_m=float(np.exp(random.uniform(np.log(0.1), np.log(2.0e7)))),
            tau_temp_min=float(np.exp(random.uniform(np.log(0.1), np.log(10_000.0)))),
            tau_f=float(np.exp(random.uniform(np.log(0.01), np.log(10.0)))),
            tau_e=float(np.exp(random.uniform(np.log(0.01), np.log(10.0)))),
            beta=coefficient_sum * beta_share,
            gamma=coefficient_sum * (1.0 - beta_share),
            edge_threshold=coefficient_sum * threshold_fraction,
            knn=int(random.choice((0, 1, 3))),
        )

        dense = sparsify(build_weight_matrix_vec(events, params), params)
        spatial = build_product_graph_spatial(events, params)

        assert np.array_equal(spatial.matrix, dense), f"trial={trial}"
        assert spatial.retained_edges == int(np.count_nonzero(np.triu(dense, 1)))


def test_spatial_product_graph_handles_empty_and_refuses_unbounded() -> None:
    events = [_event("a", 0.0, 0), _event("b", 0.001, 0)]
    empty_params = WeightParams(
        beta=0.2,
        gamma=0.3,
        edge_threshold=0.5,
        knn=0,
    )
    empty = build_product_graph_spatial(events, empty_params)
    assert empty.bound.status == "empty"
    assert not np.any(empty.matrix)

    with pytest.raises(ValueError, match="finite product-bound"):
        build_product_graph_spatial(
            events,
            replace(empty_params, edge_threshold=0.0),
        )


def test_partition_equivalence_is_bijective_and_label_agnostic() -> None:
    assert partitions_equivalent([1, 1, 4, 4], [9, 9, 2, 2])
    assert not partitions_equivalent([1, 1, 4, 4], [9, 2, 2, 2])
    assert not partitions_equivalent([1], [1, 2])


def test_packet_uses_computed_confidence_and_declares_overhead_scope() -> None:
    event = _event("event-1", 0.0, 0, confidence=0.314159)
    payload = packet_payload(event)
    summary = packet_size_summary([event])

    assert payload["C"] == pytest.approx(0.314159)
    assert payload["C"] != 0.9
    assert payload["M"] == ["urgency"]
    assert summary["min_bytes"] == summary["median_bytes"] == summary["max_bytes"]
    assert summary["excluded_protocol_overhead"]
    assert "not an end-to-end" in summary["scope"]


def test_repeat_summary_requires_five_stable_inputs_and_keeps_raw_rows() -> None:
    row = {
        "development_seeds": [1000],
        "n_events": 4,
        "runtime_limits": {"one_core_claim_eligible": False},
        "dense": {"total_s": 2.0, "retained_edges": 3},
        "spatial": {
            "total_s": 1.0,
            "candidate_pairs": 4,
            "retained_edges": 3,
        },
        "equivalence": {
            "max_abs_matrix_difference": 1e-12,
            "matrix_within_tolerance": True,
            "labels_equal_up_to_permutation": True,
        },
        "peak_rss_bytes": 1234,
    }
    result = summarize_repeats([dict(row) for _ in range(MEASURED_REPEATS)])
    assert result["measured_repeats"] == 5
    assert result["dense_total_s"]["median"] == 2.0
    assert result["spatial_total_s"]["iqr"] == 0.0
    assert result["equivalence"]["all_matrices_within_1e_9"]
    assert result["equivalence"]["all_edge_counts_equal"]
    assert result["equivalence"]["exact_equivalence_pass"]
    assert len(result["raw_repeats"]) == 5

    with pytest.raises(ValueError, match="expected 5"):
        summarize_repeats([row])


def test_repeat_summary_rejects_edge_count_mismatch_from_exact_equivalence() -> None:
    row = {
        "development_seeds": [1000],
        "n_events": 4,
        "runtime_limits": {"one_core_claim_eligible": True},
        "dense": {"total_s": 2.0, "retained_edges": 3},
        "spatial": {
            "total_s": 1.0,
            "candidate_pairs": 4,
            "retained_edges": 2,
        },
        "equivalence": {
            "max_abs_matrix_difference": 1e-12,
            "matrix_within_tolerance": True,
            "labels_equal_up_to_permutation": True,
        },
        "peak_rss_bytes": 1234,
    }

    result = summarize_repeats([dict(row) for _ in range(MEASURED_REPEATS)])
    assert result["equivalence"]["all_matrices_within_1e_9"]
    assert not result["equivalence"]["all_edge_counts_equal"]
    assert not result["equivalence"]["exact_equivalence_pass"]


def test_frozen_dataset_path_is_bound_to_manifest_checksum(tmp_path) -> None:
    import hashlib

    development = tmp_path / "development"
    development.mkdir()
    source = development / "seed_1000.json"
    source.write_bytes(b'{"seed":1000}\n')
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    manifest = {
        "entries": [{
            "split": "development",
            "seed": 1000,
            "path": "development/seed_1000.json",
            "sha256": checksum,
        }]
    }

    assert _verified_dataset_path(
        tmp_path,
        manifest,
        stage="development",
        seed=1000,
    ) == source

    source.write_bytes(b'{"seed":2000}\n')
    with pytest.raises(ValueError, match="checksum mismatch"):
        _verified_dataset_path(
            tmp_path,
            manifest,
            stage="development",
            seed=1000,
        )
