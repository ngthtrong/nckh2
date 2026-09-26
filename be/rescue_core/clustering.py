# Chép từ demo/v2/clustering.py tại commit a6be3e9 (chỉ phần run_graph_clustering);
# bỏ baseline HDBSCAN/ST-DBSCAN và metric benchmark, không sửa công thức.
"""Fair paired graph clustering, direct baselines, and operational endpoints."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Sequence

import networkx as nx
import numpy as np
from community import community_louvain
from sklearn.neighbors import BallTree

from .contracts import ReportV2, validate_unique_report_ids
from .similarity import SimilarityParamsV2, context_similarity, geographic_similarity, temporal_similarity


CompositionOperator = Literal["product", "additive"]
EARTH_RADIUS_M = 6_371_000.0
CANDIDATE_POOL_MIN_NEIGHBORS_V2 = 64
CANDIDATE_POOL_K_MULTIPLIER_V2 = 4
CANDIDATE_POOL_RULE_V2 = (
    "per eligible report retain min(n-1,max(64,4*k)) spatial neighbors; "
    "query every BallTree distance tie at the boundary, canonical-sort by "
    "(distance_rad,report_id), truncate to the declared count, then union "
    "the directed neighborhoods into undirected candidate pairs"
)


@dataclass(frozen=True, slots=True)
class GraphConfigV2:
    composition_operator: CompositionOperator
    sigma_geo_m: float
    tau_t: float
    threshold_quantile: float
    k: int
    resolution: float
    tau_F: float = 0.25
    tau_E: float = 0.35
    alpha: float = 0.5
    beta: float = 0.5
    gamma: float = 0.5

    def __post_init__(self) -> None:
        if self.composition_operator not in {"product", "additive"}:
            raise ValueError("unsupported composition operator")
        for name in ("sigma_geo_m", "tau_t", "tau_F", "tau_E"):
            if not math.isfinite(float(getattr(self, name))) or float(getattr(self, name)) <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        if not 0.0 < self.threshold_quantile < 1.0:
            raise ValueError("threshold_quantile must be in (0, 1)")
        if isinstance(self.k, bool) or not isinstance(self.k, int) or self.k < 1:
            raise ValueError("k must be a positive integer")
        if not math.isfinite(self.resolution) or self.resolution <= 0.0:
            raise ValueError("resolution must be finite and positive")
        if any(not math.isfinite(value) or value < 0.0 for value in (self.alpha, self.beta, self.gamma)):
            raise ValueError("composition weights must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class ClusterRunV2:
    method: str
    labels: tuple[int, ...]
    review_report_ids: tuple[str, ...]
    threshold_weight: float | None
    candidate_pairs: int
    retained_edges: int


def _eligible_indices(reports: Sequence[ReportV2]) -> tuple[list[int], list[int]]:
    eligible = [index for index, report in enumerate(reports) if report.graph_eligible]
    review = [index for index, report in enumerate(reports) if not report.graph_eligible]
    return eligible, review


def candidate_pool_neighbor_count_v2(*, n_eligible: int, graph_k: int) -> int:
    """Return the frozen per-report spatial candidate count."""

    if isinstance(n_eligible, bool) or not isinstance(n_eligible, int) or n_eligible < 0:
        raise ValueError("n_eligible must be a non-negative integer")
    if isinstance(graph_k, bool) or not isinstance(graph_k, int) or graph_k < 1:
        raise ValueError("graph_k must be a positive integer")
    return min(
        max(0, n_eligible - 1),
        max(CANDIDATE_POOL_MIN_NEIGHBORS_V2, CANDIDATE_POOL_K_MULTIPLIER_V2 * graph_k),
    )


def _canonical_balltree_neighbors(
    reports: Sequence[ReportV2],
    eligible: Sequence[int],
    coordinates: np.ndarray,
    tree: BallTree,
    *,
    local_left: int,
    neighbor_count: int,
) -> tuple[int, ...]:
    """Query through the kth-distance tie, then choose canonically.

    ``BallTree.query(k=...)`` may return an arbitrary subset when more than k
    points have the boundary distance.  The initial query identifies that
    distance; a radius query retrieves the full tie before the stable
    ``(distance, report_id)`` ordering and truncation.
    """

    if neighbor_count == 0:
        return ()
    initial_k = min(len(eligible), neighbor_count + 1)
    initial_distances, initial_indices = tree.query(
        coordinates[local_left : local_left + 1],
        k=initial_k,
        return_distance=True,
        sort_results=True,
    )
    non_self_distances = sorted(
        float(distance)
        for distance, raw_index in zip(
            initial_distances[0], initial_indices[0], strict=True
        )
        if int(raw_index) != local_left
    )
    if len(non_self_distances) < neighbor_count:
        # This can occur only if a backend omits the query point from a tied
        # initial result.  A full query is still bounded by the eligible batch
        # and determines the same canonical boundary.
        all_distances, all_indices = tree.query(
            coordinates[local_left : local_left + 1],
            k=len(eligible),
            return_distance=True,
            sort_results=True,
        )
        non_self_distances = sorted(
            float(distance)
            for distance, raw_index in zip(
                all_distances[0], all_indices[0], strict=True
            )
            if int(raw_index) != local_left
        )
    boundary_distance = non_self_distances[neighbor_count - 1]
    inclusive_radius = math.nextafter(boundary_distance, math.inf)
    radius_indices, radius_distances = tree.query_radius(
        coordinates[local_left : local_left + 1],
        r=inclusive_radius,
        return_distance=True,
        sort_results=False,
    )
    ranked = sorted(
        (
            float(distance),
            reports[eligible[int(raw_index)]].report_id,
            int(raw_index),
        )
        for raw_index, distance in zip(
            radius_indices[0], radius_distances[0], strict=True
        )
        if int(raw_index) != local_left
    )
    if len(ranked) < neighbor_count:
        # Some BallTree backends round the query-radius comparison one ulp
        # below the distance returned by ``query``.  Fall back to an all-point
        # query, then apply the same canonical ordering.  This is exceptional
        # (not the normal candidate search) and preserves the exact declared
        # neighbor set instead of dropping a boundary point or failing a seed.
        all_distances, all_indices = tree.query(
            coordinates[local_left : local_left + 1],
            k=len(eligible),
            return_distance=True,
            sort_results=False,
        )
        ranked = sorted(
            (
                float(distance),
                reports[eligible[int(raw_index)]].report_id,
                int(raw_index),
            )
            for raw_index, distance in zip(
                all_indices[0], all_distances[0], strict=True
            )
            if int(raw_index) != local_left
        )
    if len(ranked) < neighbor_count:
        raise RuntimeError("BallTree returned an incomplete eligible point set")
    return tuple(local_index for _, _, local_index in ranked[:neighbor_count])


def _spatial_candidate_pairs(
    reports: Sequence[ReportV2],
    eligible: Sequence[int],
    candidate_k: int,
) -> list[tuple[int, int]]:
    if len(eligible) < 2:
        return []
    coordinates = np.radians(np.asarray([reports[index].L for index in eligible], dtype=float))
    tree = BallTree(coordinates, metric="haversine")
    neighbor_count = min(len(eligible) - 1, candidate_k)
    pairs: set[tuple[int, int]] = set()
    for local_left in range(len(eligible)):
        left = eligible[local_left]
        local_neighbors = _canonical_balltree_neighbors(
            reports,
            eligible,
            coordinates,
            tree,
            local_left=local_left,
            neighbor_count=neighbor_count,
        )
        for local_right in local_neighbors:
            right = eligible[local_right]
            pairs.add((min(left, right), max(left, right)))
    return sorted(pairs)


def _weight(first: ReportV2, second: ReportV2, config: GraphConfigV2) -> float:
    params = SimilarityParamsV2(
        sigma_geo_m=config.sigma_geo_m,
        tau_t=config.tau_t,
        tau_F=config.tau_F,
        tau_E=config.tau_E,
        beta=config.beta,
        gamma=config.gamma,
        theta=0.0,
    )
    geographic = geographic_similarity(first, second, params)
    temporal = temporal_similarity(first, second, params)
    context = context_similarity(first, second, params)
    if config.composition_operator == "product":
        return geographic * (config.beta * temporal + config.gamma * context)
    return config.alpha * geographic + config.beta * temporal + config.gamma * context


def run_graph_clustering(
    reports: Sequence[ReportV2],
    config: GraphConfigV2,
    *,
    random_state: int = 42,
) -> ClusterRunV2:
    """Run one paired config on an identical sparse spatial candidate universe.

    Product and additive runs differ only in ``composition_operator``.  The
    quantile is computed on the shared spatial candidate pool; a union-kNN
    sparsifier then keeps an above-threshold edge if either endpoint selects
    it.  This convention is frozen in the protocol and avoids a dense matrix.
    """

    validate_unique_report_ids(reports)
    eligible, review = _eligible_indices(reports)
    labels = [-1] * len(reports)
    if not eligible:
        return ClusterRunV2(config.composition_operator, tuple(labels), tuple(reports[index].report_id for index in review), None, 0, 0)
    candidate_k = candidate_pool_neighbor_count_v2(
        n_eligible=len(eligible),
        graph_k=config.k,
    )
    pairs = _spatial_candidate_pairs(reports, eligible, candidate_k)
    weighted = [(left, right, _weight(reports[left], reports[right], config)) for left, right in pairs]
    positive = np.asarray([weight for _, _, weight in weighted if weight > 0.0], dtype=float)
    threshold = float(np.quantile(positive, config.threshold_quantile)) if positive.size else math.inf
    above = [(left, right, weight) for left, right, weight in weighted if weight > threshold]
    per_node: dict[int, list[tuple[float, int, int]]] = {index: [] for index in eligible}
    for left, right, weight in above:
        per_node[left].append((weight, left, right))
        per_node[right].append((weight, left, right))
    report_id_by_index = {index: reports[index].report_id for index in eligible}
    selected: set[tuple[int, int]] = set()
    for node in eligible:
        ranked = sorted(
            per_node[node],
            key=lambda row: (
                -row[0],
                report_id_by_index[row[2] if row[1] == node else row[1]],
                min(report_id_by_index[row[1]], report_id_by_index[row[2]]),
                max(report_id_by_index[row[1]], report_id_by_index[row[2]]),
            ),
        )
        selected.update((left, right) for _, left, right in ranked[: config.k])
    graph = nx.Graph()
    index_by_report_id = {identifier: index for index, identifier in report_id_by_index.items()}
    graph.add_nodes_from(sorted(index_by_report_id))
    weight_lookup = {(left, right): weight for left, right, weight in above}
    for left, right in sorted(
        selected,
        key=lambda edge: tuple(sorted((report_id_by_index[edge[0]], report_id_by_index[edge[1]]))),
    ):
        graph.add_edge(
            report_id_by_index[left],
            report_id_by_index[right],
            weight=weight_lookup[(left, right)],
        )
    if graph.number_of_edges() == 0:
        for cluster_id, index in enumerate(
            sorted(eligible, key=lambda item: reports[item].report_id)
        ):
            labels[index] = cluster_id
    else:
        partition = community_louvain.best_partition(
            graph,
            weight="weight",
            resolution=config.resolution,
            random_state=random_state,
        )
        raw_groups: dict[int, list[str]] = {}
        for report_id, raw_label in partition.items():
            raw_groups.setdefault(int(raw_label), []).append(str(report_id))
        ordered_groups = sorted(
            (tuple(sorted(members)), raw_label)
            for raw_label, members in raw_groups.items()
        )
        canonical = {
            raw_label: cluster_id
            for cluster_id, (_, raw_label) in enumerate(ordered_groups)
        }
        for report_id, raw_label in partition.items():
            labels[index_by_report_id[str(report_id)]] = canonical[int(raw_label)]
    return ClusterRunV2(
        method=config.composition_operator,
        labels=tuple(labels),
        review_report_ids=tuple(reports[index].report_id for index in review),
        threshold_weight=None if not math.isfinite(threshold) else threshold,
        candidate_pairs=len(pairs),
        retained_edges=len(selected),
    )


__all__ = [
    "CANDIDATE_POOL_K_MULTIPLIER_V2",
    "CANDIDATE_POOL_MIN_NEIGHBORS_V2",
    "CANDIDATE_POOL_RULE_V2",
    "ClusterRunV2",
    "GraphConfigV2",
    "candidate_pool_neighbor_count_v2",
    "run_graph_clustering",
]
