from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from demo.pipeline.attributes import Event
from demo.pipeline.baselines import (
    build_convex_similarity_matrix,
    observable_feature_matrix,
    primitive_similarity_matrices,
    run_dbscan,
    run_hdbscan,
    run_spatial_constrained_agglomerative,
    run_st_dbscan,
    spatiotemporal_distance_matrices,
)
from demo.pipeline.config import WeightParams


def _event(
    index: int,
    *,
    lat: float,
    lng: float,
    minute: float,
    flood: float = 0.5,
    urgency: float = 0.5,
) -> Event:
    return Event(
        event_id=f"E{index}",
        lat=lat,
        lng=lng,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc)
        + timedelta(minutes=minute),
        flood=flood,
        urgency=urgency,
        n_trapped=5,
        vulnerability=1.0,
        has_image=True,
    )


def _two_spatiotemporal_groups() -> list[Event]:
    return [
        _event(0, lat=16.0000, lng=107.0000, minute=0),
        _event(1, lat=16.0001, lng=107.0001, minute=2),
        _event(2, lat=16.0002, lng=107.0000, minute=4),
        _event(3, lat=16.2000, lng=107.2000, minute=1),
        _event(4, lat=16.2001, lng=107.2001, minute=3),
        _event(5, lat=16.2002, lng=107.2000, minute=5),
    ]


def test_convex_similarity_is_exact_simplex_mixture() -> None:
    events = _two_spatiotemporal_groups()
    params = WeightParams()
    geographic, temporal, context = primitive_similarity_matrices(events, params)
    weights = (0.2, 0.3, 0.5)
    observed = build_convex_similarity_matrix(events, params, weights)
    expected = weights[0] * geographic + weights[1] * temporal + weights[2] * context
    assert np.allclose(observed, expected, atol=1e-14, rtol=0.0)
    assert np.allclose(observed, observed.T)
    assert np.count_nonzero(np.diag(observed)) == 0


@pytest.mark.parametrize(
    "weights",
    [
        (0.2, 0.3),
        (-0.1, 0.5, 0.6),
        (0.2, 0.3, 0.4),
        (float("nan"), 0.5, 0.5),
    ],
)
def test_convex_similarity_rejects_invalid_simplex(weights: tuple[float, ...]) -> None:
    with pytest.raises(ValueError):
        build_convex_similarity_matrix(
            _two_spatiotemporal_groups(),
            WeightParams(),
            weights,
        )


def test_st_dbscan_requires_space_and_time_conjunctively() -> None:
    events = [
        _event(0, lat=16.0, lng=107.0, minute=0),
        _event(1, lat=16.0001, lng=107.0001, minute=2),
        # Spatially close but outside the temporal neighborhood.
        _event(2, lat=16.0001, lng=107.0001, minute=200),
        # Temporally close but outside the spatial neighborhood.
        _event(3, lat=16.2, lng=107.2, minute=2),
    ]
    labels = run_st_dbscan(
        events,
        spatial_eps_m=100.0,
        temporal_eps_min=10.0,
        min_samples=2,
    )
    assert labels[0] == labels[1] >= 0
    assert labels[2] == -1
    assert labels[3] == -1
    assert labels == run_st_dbscan(
        events,
        spatial_eps_m=100.0,
        temporal_eps_min=10.0,
        min_samples=2,
        distance_matrices=spatiotemporal_distance_matrices(events),
    )


def test_geo_time_context_matrix_really_contains_time() -> None:
    events = [
        _event(0, lat=16.0, lng=107.0, minute=0),
        _event(1, lat=16.0, lng=107.0, minute=120),
    ]
    geo_context = observable_feature_matrix(
        events, features="geo_context", scaler="standard"
    )
    geo_time_context = observable_feature_matrix(
        events, features="geo_time_context", scaler="standard"
    )
    assert np.allclose(geo_context[0], geo_context[1])
    assert not np.allclose(geo_time_context[0], geo_time_context[1])
    assert geo_time_context.shape[1] == 5


def test_standardized_density_adapters_return_one_label_per_event() -> None:
    events = _two_spatiotemporal_groups()
    assert len(
        run_dbscan(
            events,
            eps=1.5,
            min_samples=2,
            features="geo_time_context",
            scaler="robust",
        )
    ) == len(events)
    assert len(
        run_hdbscan(
            events,
            min_cluster_size=2,
            min_samples=2,
            scaler="standard",
        )
    ) == len(events)


def test_spatial_constraint_never_merges_disconnected_geo_components() -> None:
    events = _two_spatiotemporal_groups()
    labels = run_spatial_constrained_agglomerative(
        events,
        connectivity_radius_m=100.0,
        n_clusters=1,
        time_context_mix=0.5,
    )
    first = set(labels[:3])
    second = set(labels[3:])
    assert len(first) == 1
    assert len(second) == 1
    assert first.isdisjoint(second)


@pytest.mark.parametrize(
    "call",
    [
        lambda events: run_st_dbscan(events, spatial_eps_m=0),
        lambda events: run_st_dbscan(events, temporal_eps_min=-1),
        lambda events: run_dbscan(events, eps=0),
        lambda events: run_hdbscan(events, min_cluster_size=1),
        lambda events: run_spatial_constrained_agglomerative(
            events, connectivity_radius_m=-1
        ),
    ],
)
def test_adapter_parameters_fail_closed(call) -> None:
    with pytest.raises(ValueError):
        call(_two_spatiotemporal_groups())
