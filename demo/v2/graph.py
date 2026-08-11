"""Sparse product-graph construction with an independent dense oracle."""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np
from sklearn.neighbors import BallTree

from .contracts import ReportV2, validate_unique_report_ids
from .similarity import (
    EARTH_RADIUS_M,
    ProductBoundV2,
    SimilarityParamsV2,
    product_distance_bound,
    product_similarity,
)


# Conservative floating-point belt.  Candidate pairs are still checked with
# the scalar oracle formula, so the belt can add work but cannot add an edge.
QUERY_RADIUS_SLACK_RAD = 64.0 * math.sqrt(np.finfo(float).eps)


@dataclass(frozen=True, slots=True, order=True)
class SparseEdgeV2:
    left: int
    right: int
    weight: float

    def __post_init__(self) -> None:
        if type(self.left) is not int or type(self.right) is not int:
            raise ValueError("edge endpoints must be integer report indices")
        if self.left < 0 or self.right <= self.left:
            raise ValueError("edges require 0 <= left < right")
        if not math.isfinite(self.weight) or self.weight <= 0.0:
            raise ValueError("edge weight must be finite and positive")


@dataclass(frozen=True, slots=True)
class SparseGraphV2:
    """Thresholded edge list over original report indices."""

    report_ids: tuple[str, ...]
    eligible_indices: tuple[int, ...]
    review_queue_indices: tuple[int, ...]
    edges: tuple[SparseEdgeV2, ...]
    bound: ProductBoundV2
    total_eligible_pairs: int
    candidate_pairs: int

    @property
    def review_queue(self) -> tuple[str, ...]:
        return tuple(self.report_ids[index] for index in self.review_queue_indices)

    @property
    def eligible_report_ids(self) -> tuple[str, ...]:
        return tuple(self.report_ids[index] for index in self.eligible_indices)

    @property
    def retained_edges(self) -> int:
        return len(self.edges)

    @property
    def candidate_fraction(self) -> float:
        if self.total_eligible_pairs == 0:
            return 0.0
        return self.candidate_pairs / self.total_eligible_pairs

    def to_dense(self) -> np.ndarray:
        return edge_list_to_dense(self)


def split_graph_eligible(
    reports: Sequence[ReportV2],
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Return eligible and review indices; missing L or T always means review."""

    eligible = tuple(
        index for index, report in enumerate(reports) if report.graph_eligible
    )
    review = tuple(
        index for index, report in enumerate(reports) if not report.graph_eligible
    )
    return eligible, review


def _all_pairs(indices: Sequence[int]) -> tuple[tuple[int, int], ...]:
    return tuple(itertools.combinations(indices, 2))


def _spatial_candidate_pairs(
    reports: Sequence[ReportV2],
    eligible: tuple[int, ...],
    bound: ProductBoundV2,
) -> tuple[tuple[int, int], ...]:
    if len(eligible) < 2 or bound.status == "empty":
        return ()
    if bound.status == "unbounded":
        # Theta=0 has no finite safe pruning radius.  Preserve correctness and
        # the sparse edge-list output, while making the all-pairs cost explicit
        # in ``candidate_pairs``.
        return _all_pairs(eligible)
    assert bound.radius_m is not None
    coordinates = np.radians(
        np.asarray([reports[index].L for index in eligible], dtype=float)
    )
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
    pairs: set[tuple[int, int]] = set()
    for local_left, neighbors in enumerate(neighborhoods):
        left = eligible[local_left]
        for raw_local_right in neighbors:
            local_right = int(raw_local_right)
            if local_right <= local_left:
                continue
            right = eligible[local_right]
            pairs.add((left, right))
    return tuple(sorted(pairs))


def build_sparse_product_graph(
    reports: Sequence[ReportV2],
    params: SimilarityParamsV2,
) -> SparseGraphV2:
    """Build a deterministic spatial-candidate edge list without a dense matrix."""

    validate_unique_report_ids(reports)
    eligible, review = split_graph_eligible(reports)
    bound = product_distance_bound(params)
    total_pairs = len(eligible) * (len(eligible) - 1) // 2
    candidates = _spatial_candidate_pairs(reports, eligible, bound)
    edges: list[SparseEdgeV2] = []
    for left, right in candidates:
        weight = product_similarity(reports[left], reports[right], params)
        if weight > params.theta:
            edges.append(SparseEdgeV2(left, right, weight))
    return SparseGraphV2(
        report_ids=tuple(report.report_id for report in reports),
        eligible_indices=eligible,
        review_queue_indices=review,
        edges=tuple(edges),
        bound=bound,
        total_eligible_pairs=total_pairs,
        candidate_pairs=len(candidates),
    )


def build_dense_product_oracle(
    reports: Sequence[ReportV2],
    params: SimilarityParamsV2,
) -> np.ndarray:
    """Independent all-pairs strict-threshold oracle used only for validation."""

    validate_unique_report_ids(reports)
    eligible, _ = split_graph_eligible(reports)
    matrix = np.zeros((len(reports), len(reports)), dtype=float)
    for left, right in itertools.combinations(eligible, 2):
        weight = product_similarity(reports[left], reports[right], params)
        if weight > params.theta:
            matrix[left, right] = weight
            matrix[right, left] = weight
    return matrix


def edge_list_to_dense(graph: SparseGraphV2) -> np.ndarray:
    matrix = np.zeros((len(graph.report_ids), len(graph.report_ids)), dtype=float)
    for edge in graph.edges:
        matrix[edge.left, edge.right] = edge.weight
        matrix[edge.right, edge.left] = edge.weight
    return matrix


def sparse_dense_equivalent(
    reports: Sequence[ReportV2],
    params: SimilarityParamsV2,
    *,
    absolute_tolerance: float = 1e-12,
) -> bool:
    """Whether the spatial edge list exactly matches the dense oracle."""

    tolerance = float(absolute_tolerance)
    if not math.isfinite(tolerance) or tolerance < 0.0:
        raise ValueError("absolute_tolerance must be finite and non-negative")
    sparse = build_sparse_product_graph(reports, params).to_dense()
    dense = build_dense_product_oracle(reports, params)
    return bool(np.allclose(sparse, dense, rtol=0.0, atol=tolerance))


# Descriptive alias used by experiment contracts.
build_sparse_spatial_edge_list = build_sparse_product_graph
dense_equivalence_oracle = build_dense_product_oracle

