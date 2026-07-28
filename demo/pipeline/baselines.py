"""Implementable clustering baselines declared in ``protocol/baselines.json``.

The adapters in this module consume only inference-visible :class:`Event`
fields.  Ground-truth labels, duplicate lineage, and adversary annotations are
deliberately absent from every public signature.
"""
from __future__ import annotations

import math
from collections import deque
from datetime import timezone
from typing import Literal, Sequence

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.cluster import (
    DBSCAN,
    HDBSCAN,
    AgglomerativeClustering,
    KMeans,
    SpectralClustering,
)
from sklearn.preprocessing import RobustScaler, StandardScaler

from .attributes import Event, haversine_m
from .config import WeightParams


ScalerName = Literal["standard", "robust"]
FeatureSet = Literal["geo", "geo_context", "geo_time_context", "time_context"]


def _validate_events(events: Sequence[Event]) -> None:
    for index, event in enumerate(events):
        values = (
            event.lat,
            event.lng,
            event.created_at.timestamp(),
            event.flood,
            event.urgency,
        )
        if not all(math.isfinite(float(value)) for value in values):
            raise ValueError(f"event {index} contains a non-finite feature")


def _local_geo_columns(events: Sequence[Event]) -> np.ndarray:
    """Return local east/north coordinates in metres.

    Latitude and longitude degrees do not have the same physical scale.  A
    local equirectangular projection is sufficient for the bounded candidate
    region and prevents a raw-degree artifact before feature scaling.
    """

    if not events:
        return np.empty((0, 2), dtype=float)
    radius_m = 6_371_000.0
    lat = np.radians(np.asarray([event.lat for event in events], dtype=float))
    lng = np.radians(np.asarray([event.lng for event in events], dtype=float))
    lat0 = float(np.median(lat))
    lng0 = float(np.median(lng))
    east = radius_m * math.cos(lat0) * (lng - lng0)
    north = radius_m * (lat - lat0)
    return np.column_stack((east, north))


def _time_column(events: Sequence[Event]) -> np.ndarray:
    if not events:
        return np.empty((0, 1), dtype=float)
    timestamps = np.asarray(
        [
            (
                event.created_at.replace(tzinfo=timezone.utc)
                if event.created_at.tzinfo is None
                else event.created_at.astimezone(timezone.utc)
            ).timestamp()
            / 60.0
            for event in events
        ],
        dtype=float,
    )
    return (timestamps - float(np.min(timestamps)))[:, None]


def observable_feature_matrix(
    events: Sequence[Event],
    *,
    features: FeatureSet = "geo_time_context",
    scaler: ScalerName = "standard",
) -> np.ndarray:
    """Build a scaled matrix from an explicitly declared observable view."""

    _validate_events(events)
    if features not in {"geo", "geo_context", "geo_time_context", "time_context"}:
        raise ValueError(f"unsupported feature set: {features!r}")
    if scaler not in {"standard", "robust"}:
        raise ValueError(f"scaler must be 'standard' or 'robust', got {scaler!r}")
    if not events:
        width = {
            "geo": 2,
            "geo_context": 4,
            "geo_time_context": 5,
            "time_context": 3,
        }[features]
        return np.empty((0, width), dtype=float)

    columns: list[np.ndarray] = []
    if features in {"geo", "geo_context", "geo_time_context"}:
        columns.append(_local_geo_columns(events))
    if features in {"geo_time_context", "time_context"}:
        columns.append(_time_column(events))
    if features in {"geo_context", "geo_time_context", "time_context"}:
        columns.append(
            np.asarray(
                [[event.flood, event.urgency] for event in events],
                dtype=float,
            )
        )
    raw = np.column_stack(columns)
    transformer = StandardScaler() if scaler == "standard" else RobustScaler()
    return np.asarray(transformer.fit_transform(raw), dtype=float)


def _feature_matrix(events: list[Event], features: str = "geo_context") -> np.ndarray:
    """Backward-compatible feature helper used by historical experiments."""

    return observable_feature_matrix(
        events,
        features=features,  # type: ignore[arg-type]
        scaler="standard",
    )


def primitive_similarity_matrices(
    events: Sequence[Event],
    params: WeightParams,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return geographic, temporal, and context similarities separately."""

    _validate_events(events)
    for name, value in (
        ("sigma_geo_m", params.sigma_geo_m),
        ("tau_temp_min", params.tau_temp_min),
        ("tau_f", params.tau_f),
        ("tau_e", params.tau_e),
    ):
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name} must be finite and positive")
    n_events = len(events)
    if n_events == 0:
        empty = np.empty((0, 0), dtype=float)
        return empty.copy(), empty.copy(), empty.copy()

    geo_xy = _local_geo_columns(events)
    geo_delta = geo_xy[:, None, :] - geo_xy[None, :, :]
    # The projection is used only for vectorization.  Correct the small local
    # approximation error with exact Haversine values outside the diagonal.
    distance = np.sqrt(np.sum(geo_delta * geo_delta, axis=2))
    if n_events <= 1024:
        for first in range(n_events):
            for second in range(first + 1, n_events):
                exact = haversine_m(
                    events[first].lat,
                    events[first].lng,
                    events[second].lat,
                    events[second].lng,
                )
                distance[first, second] = distance[second, first] = exact
    times = _time_column(events)[:, 0]
    flood = np.asarray([event.flood for event in events], dtype=float)
    urgency = np.asarray([event.urgency for event in events], dtype=float)

    geo = np.exp(-(distance**2) / (2.0 * params.sigma_geo_m**2))
    temporal = np.exp(
        -np.abs(times[:, None] - times[None, :]) / params.tau_temp_min
    )
    context = np.exp(
        -np.abs(flood[:, None] - flood[None, :]) / params.tau_f
        - np.abs(urgency[:, None] - urgency[None, :]) / params.tau_e
    )
    for matrix in (geo, temporal, context):
        np.fill_diagonal(matrix, 0.0)
    return geo, temporal, context


def build_convex_similarity_matrix(
    events: Sequence[Event],
    params: WeightParams,
    simplex_weights: Sequence[float],
) -> np.ndarray:
    """Convex mixture of the same geographic/time/context similarities."""

    weights = validate_simplex_weights(simplex_weights)
    geographic, temporal, context = primitive_similarity_matrices(events, params)
    mixture = (
        weights[0] * geographic
        + weights[1] * temporal
        + weights[2] * context
    )
    np.fill_diagonal(mixture, 0.0)
    return mixture


def validate_simplex_weights(simplex_weights: Sequence[float]) -> np.ndarray:
    """Return a validated three-component convex-mixture vector."""

    weights = np.asarray(tuple(simplex_weights), dtype=float)
    if (
        weights.shape != (3,)
        or not np.isfinite(weights).all()
        or (weights < 0.0).any()
        or not math.isclose(float(weights.sum()), 1.0, abs_tol=1e-12)
    ):
        raise ValueError("simplex_weights must contain three non-negative values summing to 1")
    return weights


def run_kmeans(
    events: list[Event],
    n_clusters: int,
    random_state: int = 42,
    features: str = "geo_context",
    scaler: ScalerName = "standard",
) -> list[int]:
    if not events:
        return []
    x = observable_feature_matrix(
        events,
        features=features,  # type: ignore[arg-type]
        scaler=scaler,
    )
    n_clusters = max(1, min(int(n_clusters), len(events)))
    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    return model.fit_predict(x).astype(int).tolist()


def run_dbscan(
    events: list[Event],
    eps: float = 0.5,
    min_samples: int = 3,
    features: str = "geo_time_context",
    scaler: ScalerName = "standard",
) -> list[int]:
    if not math.isfinite(eps) or eps <= 0.0:
        raise ValueError("eps must be finite and positive")
    if isinstance(min_samples, bool) or not isinstance(min_samples, int) or min_samples < 1:
        raise ValueError("min_samples must be a positive integer")
    if not events:
        return []
    x = observable_feature_matrix(
        events,
        features=features,  # type: ignore[arg-type]
        scaler=scaler,
    )
    return DBSCAN(eps=eps, min_samples=min_samples).fit_predict(x).astype(int).tolist()


def run_hdbscan(
    events: list[Event],
    min_cluster_size: int = 5,
    min_samples: int | None = None,
    features: FeatureSet = "geo_time_context",
    scaler: ScalerName = "standard",
) -> list[int]:
    if (
        isinstance(min_cluster_size, bool)
        or not isinstance(min_cluster_size, int)
        or min_cluster_size < 2
    ):
        raise ValueError("min_cluster_size must be an integer >= 2")
    if min_samples is not None and (
        isinstance(min_samples, bool)
        or not isinstance(min_samples, int)
        or min_samples < 1
    ):
        raise ValueError("min_samples must be None or a positive integer")
    if not events:
        return []
    x = observable_feature_matrix(events, features=features, scaler=scaler)
    model = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        copy=True,
    )
    return model.fit_predict(x).astype(int).tolist()


def spatiotemporal_distance_matrices(
    events: Sequence[Event],
) -> tuple[np.ndarray, np.ndarray]:
    """Precompute exact metres/minutes distances for a fair ST-DBSCAN grid."""

    _validate_events(events)
    n_events = len(events)
    spatial = np.zeros((n_events, n_events), dtype=float)
    utc_times = [
        (
            event.created_at.replace(tzinfo=timezone.utc)
            if event.created_at.tzinfo is None
            else event.created_at.astimezone(timezone.utc)
        )
        for event in events
    ]
    temporal = np.zeros((n_events, n_events), dtype=float)
    for first, event in enumerate(events):
        for second in range(first + 1, n_events):
            other = events[second]
            distance = haversine_m(event.lat, event.lng, other.lat, other.lng)
            delta_min = abs(
                (utc_times[first] - utc_times[second]).total_seconds()
            ) / 60.0
            spatial[first, second] = spatial[second, first] = distance
            temporal[first, second] = temporal[second, first] = delta_min
    return spatial, temporal


def _spatiotemporal_neighborhoods(
    spatial_distances: np.ndarray,
    temporal_distances: np.ndarray,
    spatial_eps_m: float,
    temporal_eps_min: float,
) -> list[list[int]]:
    mask = (
        (spatial_distances <= spatial_eps_m)
        & (temporal_distances <= temporal_eps_min)
    )
    return [
        np.flatnonzero(mask[index]).astype(int).tolist()
        for index in range(mask.shape[0])
    ]


def run_st_dbscan(
    events: list[Event],
    spatial_eps_m: float = 800.0,
    temporal_eps_min: float = 60.0,
    min_samples: int = 3,
    *,
    distance_matrices: tuple[np.ndarray, np.ndarray] | None = None,
) -> list[int]:
    """Direct ST-DBSCAN with conjunctive spatial and temporal neighborhoods."""

    if not math.isfinite(spatial_eps_m) or spatial_eps_m <= 0.0:
        raise ValueError("spatial_eps_m must be finite and positive")
    if not math.isfinite(temporal_eps_min) or temporal_eps_min <= 0.0:
        raise ValueError("temporal_eps_min must be finite and positive")
    if isinstance(min_samples, bool) or not isinstance(min_samples, int) or min_samples < 1:
        raise ValueError("min_samples must be a positive integer")
    if not events:
        return []

    if distance_matrices is None:
        spatial_distances, temporal_distances = spatiotemporal_distance_matrices(
            events
        )
    else:
        spatial_distances = np.asarray(distance_matrices[0], dtype=float)
        temporal_distances = np.asarray(distance_matrices[1], dtype=float)
        expected = (len(events), len(events))
        if (
            spatial_distances.shape != expected
            or temporal_distances.shape != expected
            or not np.isfinite(spatial_distances).all()
            or not np.isfinite(temporal_distances).all()
            or (spatial_distances < 0.0).any()
            or (temporal_distances < 0.0).any()
            or not np.allclose(spatial_distances, spatial_distances.T)
            or not np.allclose(temporal_distances, temporal_distances.T)
        ):
            raise ValueError("distance_matrices must be finite symmetric n-by-n arrays")
    neighborhoods = _spatiotemporal_neighborhoods(
        spatial_distances,
        temporal_distances,
        spatial_eps_m,
        temporal_eps_min,
    )
    unvisited = -2
    noise = -1
    labels = [unvisited] * len(events)
    cluster_id = 0

    for point in range(len(events)):
        if labels[point] != unvisited:
            continue
        neighbors = neighborhoods[point]
        if len(neighbors) < min_samples:
            labels[point] = noise
            continue

        labels[point] = cluster_id
        queue = deque(neighbors)
        enqueued = set(neighbors)
        while queue:
            candidate = queue.popleft()
            if labels[candidate] == noise:
                labels[candidate] = cluster_id
            if labels[candidate] != unvisited:
                continue
            labels[candidate] = cluster_id
            candidate_neighbors = neighborhoods[candidate]
            if len(candidate_neighbors) >= min_samples:
                for neighbor in candidate_neighbors:
                    if neighbor not in enqueued:
                        enqueued.add(neighbor)
                        queue.append(neighbor)
        cluster_id += 1
    return labels


def _geographic_connectivity(
    events: Sequence[Event], radius_m: float
) -> csr_matrix:
    rows: list[int] = []
    columns: list[int] = []
    for first, event in enumerate(events):
        rows.append(first)
        columns.append(first)
        for second in range(first + 1, len(events)):
            other = events[second]
            if haversine_m(event.lat, event.lng, other.lat, other.lng) <= radius_m:
                rows.extend((first, second))
                columns.extend((second, first))
    values = np.ones(len(rows), dtype=np.int8)
    return csr_matrix((values, (rows, columns)), shape=(len(events), len(events)))


def _allocate_component_clusters(
    component_sizes: Sequence[int], requested: int
) -> list[int]:
    """Allocate a deterministic cluster budget without crossing components."""

    n_components = len(component_sizes)
    total = sum(component_sizes)
    target = min(total, max(requested, n_components))
    allocation = [1] * n_components
    remaining = target - n_components
    if remaining <= 0:
        return allocation
    ideal_extra = [
        remaining * size / total for size in component_sizes
    ]
    for index, ideal in enumerate(ideal_extra):
        extra = min(component_sizes[index] - 1, int(math.floor(ideal)))
        allocation[index] += extra
    still = target - sum(allocation)
    order = sorted(
        range(n_components),
        key=lambda index: (
            -(ideal_extra[index] - math.floor(ideal_extra[index])),
            -component_sizes[index],
            index,
        ),
    )
    while still > 0:
        progressed = False
        for index in order:
            if allocation[index] < component_sizes[index]:
                allocation[index] += 1
                still -= 1
                progressed = True
                if still == 0:
                    break
        if not progressed:
            break
    return allocation


def run_spatial_constrained_agglomerative(
    events: list[Event],
    connectivity_radius_m: float = 1200.0,
    n_clusters: int = 13,
    time_context_mix: float = 0.5,
    scaler: ScalerName = "standard",
) -> list[int]:
    """Agglomerative time/context clustering that never crosses a geo component.

    Scikit-learn completes a disconnected connectivity matrix by adding edges.
    To preserve the declared spatial constraint, this adapter partitions the
    geographic graph first and clusters each connected component separately.
    If the requested ``K`` is below the number of geographic components, the
    actual output contains one cluster per component instead of silently
    violating the constraint.
    """

    if not math.isfinite(connectivity_radius_m) or connectivity_radius_m <= 0.0:
        raise ValueError("connectivity_radius_m must be finite and positive")
    if isinstance(n_clusters, bool) or not isinstance(n_clusters, int) or n_clusters < 1:
        raise ValueError("n_clusters must be a positive integer")
    if not math.isfinite(time_context_mix) or not 0.0 <= time_context_mix <= 1.0:
        raise ValueError("time_context_mix must lie in [0, 1]")
    if not events:
        return []
    if len(events) == 1:
        return [0]

    connectivity = _geographic_connectivity(events, connectivity_radius_m)
    component_count, component_ids = connected_components(
        connectivity, directed=False, return_labels=True
    )
    components = [
        np.flatnonzero(component_ids == component_id)
        for component_id in range(component_count)
    ]
    allocations = _allocate_component_clusters(
        [len(component) for component in components],
        min(n_clusters, len(events)),
    )
    features = observable_feature_matrix(
        events, features="time_context", scaler=scaler
    )
    # The registry parameter controls the relative temporal contribution;
    # context remains present for every declared configuration.
    features[:, 0] *= time_context_mix

    labels = np.full(len(events), -1, dtype=int)
    next_label = 0
    for component, component_k in zip(components, allocations, strict=True):
        if component_k == 1:
            labels[component] = next_label
            next_label += 1
            continue
        subset_connectivity = connectivity[component][:, component]
        model = AgglomerativeClustering(
            n_clusters=component_k,
            metric="euclidean",
            linkage="average",
            connectivity=subset_connectivity,
        )
        local = model.fit_predict(features[component]).astype(int)
        for local_label in sorted(set(local.tolist())):
            labels[component[local == local_label]] = next_label
            next_label += 1
    if (labels < 0).any():
        raise RuntimeError("spatial agglomerative adapter left an event unlabeled")
    return labels.tolist()


def run_spectral(
    weights: np.ndarray, n_clusters: int, random_state: int = 42
) -> list[int]:
    """Spectral clustering directly on a precomputed affinity matrix."""

    if weights.ndim != 2 or weights.shape[0] != weights.shape[1]:
        raise ValueError("weights must be a square matrix")
    if not np.isfinite(weights).all() or (weights < 0.0).any():
        raise ValueError("weights must be finite and non-negative")
    if weights.shape[0] == 0:
        return []
    n_clusters = max(1, min(int(n_clusters), weights.shape[0]))
    model = SpectralClustering(
        n_clusters=n_clusters,
        affinity="precomputed",
        assign_labels="discretize",
        random_state=random_state,
    )
    return model.fit_predict(weights).astype(int).tolist()


def run_hdbscan_on_graph(
    weights: np.ndarray, min_cluster_size: int = 3
) -> list[int]:
    """Historical same-graph diagnostic retained for backward compatibility."""

    if weights.ndim != 2 or weights.shape[0] != weights.shape[1]:
        raise ValueError("weights must be a square matrix")
    if weights.shape[0] == 0:
        return []
    maximum = float(weights.max()) if float(weights.max()) > 0.0 else 1.0
    distance = 1.0 - (weights / maximum)
    np.fill_diagonal(distance, 0.0)
    model = HDBSCAN(min_cluster_size=min_cluster_size, metric="precomputed")
    return model.fit_predict(distance.astype(float)).astype(int).tolist()


def run_agglomerative_on_graph(
    weights: np.ndarray, n_clusters: int
) -> list[int]:
    """Historical same-graph diagnostic retained for backward compatibility."""

    if weights.ndim != 2 or weights.shape[0] != weights.shape[1]:
        raise ValueError("weights must be a square matrix")
    if weights.shape[0] == 0:
        return []
    maximum = float(weights.max()) if float(weights.max()) > 0.0 else 1.0
    distance = 1.0 - (weights / maximum)
    np.fill_diagonal(distance, 0.0)
    n_clusters = max(1, min(int(n_clusters), weights.shape[0]))
    model = AgglomerativeClustering(
        n_clusters=n_clusters,
        metric="precomputed",
        linkage="average",
    )
    return model.fit_predict(distance).astype(int).tolist()


__all__ = [
    "build_convex_similarity_matrix",
    "observable_feature_matrix",
    "primitive_similarity_matrices",
    "run_agglomerative_on_graph",
    "run_dbscan",
    "run_hdbscan",
    "run_hdbscan_on_graph",
    "run_kmeans",
    "run_spatial_constrained_agglomerative",
    "run_spectral",
    "run_st_dbscan",
    "spatiotemporal_distance_matrices",
    "validate_simplex_weights",
]
