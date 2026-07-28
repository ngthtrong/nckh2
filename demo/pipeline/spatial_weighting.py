"""Exact geographic candidate pruning for the product-similarity graph.

This module does not change the locked weight formula.  It uses the finite
product bound only to avoid evaluating pairs that cannot pass the operational
strict threshold, then mirrors the locked dense NumPy kernel on those pairs
and calls the same sparsification API.

The returned matrix is intentionally dense for compatibility with the current
Louvain/Leiden pipeline.  Candidate pruning reduces pair evaluation, but the
matrix still uses O(n^2) memory; experiments and the manuscript must not call
this a fully sparse scalable implementation.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from sklearn.neighbors import BallTree

from .attributes import Event
from .config import WeightParams
from .weighting import (
    GeographicBound,
    product_distance_bound,
    sparsify,
)


EARTH_RADIUS_M = 6_371_000.0
# BallTree and the locked dense NumPy kernel use different but equivalent
# haversine evaluation orders.  Querying a conservative floating-point belt
# (about 6.1 m on Earth) cannot add an output edge because every candidate is
# still evaluated by the exact dense-reference weight kernel below.
QUERY_RADIUS_SLACK_RAD = 64.0 * math.sqrt(np.finfo(float).eps)


def _product_weights_for_pairs_vec(
    events: list[Event],
    left: np.ndarray,
    right: np.ndarray,
    params: WeightParams,
) -> np.ndarray:
    """Mirror the locked dense NumPy kernel on only the candidate pairs."""

    lat = np.radians(np.array([event.lat for event in events]))
    lng = np.radians(np.array([event.lng for event in events]))
    timestamps = (
        np.array([event.created_at.timestamp() for event in events]) / 60.0
    )
    flood = np.array([event.flood for event in events])
    urgency = np.array([event.urgency for event in events])

    dlat = lat[left] - lat[right]
    dlng = lng[left] - lng[right]
    haversine = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat[left])
        * np.cos(lat[right])
        * np.sin(dlng / 2.0) ** 2
    )
    distance_m = (
        2.0
        * EARTH_RADIUS_M
        * np.arcsin(np.sqrt(np.clip(haversine, 0.0, 1.0)))
    )
    geographic = np.exp(
        -(distance_m**2) / (2.0 * params.sigma_geo_m**2)
    )
    temporal = np.exp(
        -np.abs(timestamps[left] - timestamps[right]) / params.tau_temp_min
    )
    contextual = np.exp(
        -np.abs(flood[left] - flood[right]) / params.tau_f
        - np.abs(urgency[left] - urgency[right]) / params.tau_e
    )
    return geographic * (
        params.beta * temporal + params.gamma * contextual
    )


@dataclass(frozen=True)
class SpatialBuildResult:
    """A thresholded/k-NN matrix plus auditable candidate-pair counts."""

    matrix: np.ndarray
    bound: GeographicBound
    total_pairs: int
    candidate_pairs: int
    retained_edges: int

    @property
    def pruned_pairs(self) -> int:
        return self.total_pairs - self.candidate_pairs

    @property
    def candidate_fraction(self) -> float:
        if self.total_pairs == 0:
            return 0.0
        return self.candidate_pairs / self.total_pairs


def build_product_graph_spatial(
    events: list[Event],
    params: WeightParams,
) -> SpatialBuildResult:
    """Build the exact operational product graph via a BallTree radius query.

    Only the finite product-bound region permits geographic pruning.  An empty
    retained set returns an all-zero graph.  The unbounded region is refused
    because silently applying an arbitrary geographic radius would change the
    method.
    """

    bound = product_distance_bound(params, params.edge_threshold)
    n_events = len(events)
    total_pairs = n_events * (n_events - 1) // 2
    matrix = np.zeros((n_events, n_events), dtype=float)

    if bound.status == "empty" or n_events < 2:
        return SpatialBuildResult(
            matrix=matrix,
            bound=bound,
            total_pairs=total_pairs,
            candidate_pairs=0,
            retained_edges=0,
        )
    if bound.status != "finite" or bound.radius_m is None:
        raise ValueError(
            "spatial candidate pruning requires the finite product-bound region"
        )

    coordinates = np.radians(
        np.asarray([[event.lat, event.lng] for event in events], dtype=float)
    )
    if (
        not np.isfinite(coordinates).all()
        or (np.abs(coordinates[:, 0]) > math.pi / 2.0).any()
        or (np.abs(coordinates[:, 1]) > math.pi).any()
    ):
        raise ValueError("event coordinates must be finite latitude/longitude")

    tree = BallTree(coordinates, metric="haversine")
    angular_radius = math.nextafter(
        min(
            math.pi,
            bound.radius_m / EARTH_RADIUS_M + QUERY_RADIUS_SLACK_RAD,
        ),
        math.inf,
    )
    neighborhoods = tree.query_radius(
        coordinates,
        r=angular_radius,
        return_distance=False,
        sort_results=False,
    )

    left_indices: list[int] = []
    right_indices: list[int] = []
    for left, neighbors in enumerate(neighborhoods):
        for raw_right in neighbors:
            right = int(raw_right)
            if right <= left:
                continue
            left_indices.append(left)
            right_indices.append(right)

    candidate_pairs = len(left_indices)
    if candidate_pairs:
        left_array = np.asarray(left_indices, dtype=np.intp)
        right_array = np.asarray(right_indices, dtype=np.intp)
        values = _product_weights_for_pairs_vec(
            events,
            left_array,
            right_array,
            params,
        )
        retained = values > params.edge_threshold
        retained_left = left_array[retained]
        retained_right = right_array[retained]
        retained_values = values[retained]
        matrix[retained_left, retained_right] = retained_values
        matrix[retained_right, retained_left] = retained_values

    matrix = sparsify(matrix, params)
    retained_edges = int(np.count_nonzero(np.triu(matrix, 1)))
    return SpatialBuildResult(
        matrix=matrix,
        bound=bound,
        total_pairs=total_pairs,
        candidate_pairs=candidate_pairs,
        retained_edges=retained_edges,
    )


def partitions_equivalent(left: list[int], right: list[int]) -> bool:
    """Return whether two label vectors encode the same partition.

    Cluster identifiers are arbitrary, so direct label equality is not a valid
    equivalence check.
    """

    if len(left) != len(right):
        return False
    left_to_right: dict[int, int] = {}
    right_to_left: dict[int, int] = {}
    for left_label, right_label in zip(left, right, strict=True):
        mapped_right = left_to_right.setdefault(left_label, right_label)
        mapped_left = right_to_left.setdefault(right_label, left_label)
        if mapped_right != right_label or mapped_left != left_label:
            return False
    return True
