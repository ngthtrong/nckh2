"""Fair paired graph clustering, direct baselines, and operational endpoints."""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from datetime import timezone
from statistics import mean
from typing import Literal, Mapping, Sequence

import networkx as nx
import numpy as np
from community import community_louvain
from sklearn.cluster import HDBSCAN
from sklearn.metrics import adjusted_rand_score
from sklearn.neighbors import BallTree

from demo.v2.contracts import ReportV2, TruthV2, validate_unique_report_ids
from demo.v2.priority import report_provenance_scores
from demo.v2.similarity import SimilarityParamsV2, context_similarity, geographic_similarity, haversine_m, temporal_similarity


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


def run_st_dbscan_v2(
    reports: Sequence[ReportV2],
    *,
    spatial_eps_m: float,
    temporal_eps_min: float,
    min_samples: int,
) -> ClusterRunV2:
    eligible, review = _eligible_indices(reports)
    labels = [-1] * len(reports)
    neighborhoods: dict[int, list[int]] = {}
    for left in eligible:
        neighborhoods[left] = [
            right
            for right in eligible
            if haversine_m(reports[left].L, reports[right].L) <= spatial_eps_m
            and abs((reports[left].T - reports[right].T).total_seconds()) / 60.0 <= temporal_eps_min
        ]
    unvisited = -2
    local = {index: unvisited for index in eligible}
    cluster_id = 0
    for point in eligible:
        if local[point] != unvisited:
            continue
        if len(neighborhoods[point]) < min_samples:
            local[point] = -1
            continue
        local[point] = cluster_id
        queue = deque(neighborhoods[point])
        queued = set(neighborhoods[point])
        while queue:
            candidate = queue.popleft()
            if local[candidate] == -1:
                local[candidate] = cluster_id
            if local[candidate] != unvisited:
                continue
            local[candidate] = cluster_id
            if len(neighborhoods[candidate]) >= min_samples:
                for neighbor in neighborhoods[candidate]:
                    if neighbor not in queued:
                        queued.add(neighbor)
                        queue.append(neighbor)
        cluster_id += 1
    for index in eligible:
        labels[index] = local[index]
    return ClusterRunV2(
        "st_dbscan",
        tuple(labels),
        tuple(reports[index].report_id for index in review),
        None,
        len(eligible) * (len(eligible) - 1) // 2,
        0,
    )


def _local_xy(reports: Sequence[ReportV2], eligible: Sequence[int]) -> np.ndarray:
    latitude = np.radians(np.asarray([reports[index].L[0] for index in eligible]))
    longitude = np.radians(np.asarray([reports[index].L[1] for index in eligible]))
    lat0, lon0 = float(np.median(latitude)), float(np.median(longitude))
    east = EARTH_RADIUS_M * math.cos(lat0) * (longitude - lon0)
    north = EARTH_RADIUS_M * (latitude - lat0)
    return np.column_stack((east, north))


def run_hdbscan_v2(
    reports: Sequence[ReportV2],
    *,
    min_cluster_size: int,
    min_samples: int,
    spatial_scale_m: float,
    temporal_scale_min: float,
) -> ClusterRunV2:
    eligible, review = _eligible_indices(reports)
    labels = [-1] * len(reports)
    if eligible:
        xy = _local_xy(reports, eligible) / spatial_scale_m
        timestamps = np.asarray(
            [reports[index].T.astimezone(timezone.utc).timestamp() / 60.0 for index in eligible]
        )
        time = ((timestamps - timestamps.min()) / temporal_scale_min)[:, None]
        features = np.column_stack((xy, time))
        local_labels = HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            copy=True,
        ).fit_predict(features)
        for index, label in zip(eligible, local_labels, strict=True):
            labels[index] = int(label)
    return ClusterRunV2(
        "hdbscan",
        tuple(labels),
        tuple(reports[index].report_id for index in review),
        None,
        0,
        0,
    )


def clustering_endpoints(
    reports: Sequence[ReportV2],
    report_truth: Sequence[TruthV2],
    run: ClusterRunV2,
    *,
    provenance_scores: Mapping[str, float] | None = None,
) -> dict[str, float | int]:
    """Compute co-primary and secondary metrics with complete denominators."""

    truth_by_id = {row.report_id: row for row in report_truth}
    if len(truth_by_id) != len(report_truth) or set(truth_by_id) != {row.report_id for row in reports}:
        raise ValueError("truth must join one-to-one with observable reports")
    truth_labels = [
        -1 if truth_by_id[report.report_id].incident_id is None else int(truth_by_id[report.report_id].gt_cluster)
        for report in reports
    ]
    linked = [index for index, value in enumerate(truth_labels) if value >= 0]
    # Every unresolved report is a distinct review unit.  Treating the shared
    # sentinel ``-1`` as one predicted cluster would spuriously reward methods
    # that reject many linked reports.
    predicted_for_ari = [
        run.labels[index] if run.labels[index] != -1 else -(1_000_000 + index)
        for index in linked
    ]
    ari = adjusted_rand_score(
        [truth_labels[index] for index in linked],
        predicted_for_ari,
    ) if linked else 0.0
    groups: dict[int, list[int]] = {}
    unresolved: list[int] = []
    for index, label in enumerate(run.labels):
        if label == -1:
            unresolved.append(index)
        else:
            groups.setdefault(label, []).append(index)
    false_destinations = sum(
        all(truth_labels[index] == -1 for index in members) for members in groups.values()
    )
    noise_indices = [index for index, value in enumerate(truth_labels) if value == -1]
    noise_rejected = sum(run.labels[index] == -1 for index in noise_indices)
    incident_units: dict[int, set[str]] = {}
    for index in linked:
        unit = f"review:{index}" if run.labels[index] == -1 else f"cluster:{run.labels[index]}"
        incident_units.setdefault(truth_labels[index], set()).add(unit)
    split_incidents = sum(len(units) > 1 for units in incident_units.values())
    split_loss = split_incidents / max(1, len(incident_units))
    linked_groups = [
        members
        for members in groups.values()
        if any(truth_labels[index] >= 0 for index in members)
    ]
    merged = sum(
        len({truth_labels[index] for index in members if truth_labels[index] >= 0}) >= 2
        for members in linked_groups
    )
    # Noise-only destinations are reported separately as false destinations;
    # including them here would dilute incident merge loss.
    merge_loss = merged / max(1, len(linked_groups))
    provenance = (
        dict(provenance_scores)
        if provenance_scores is not None
        else report_provenance_scores(reports)
    )
    if set(provenance) != {report.report_id for report in reports}:
        raise ValueError("provenance scores must cover every report exactly")
    reviewed_clusters = sum(
        len(members) < 2
        or mean(provenance[reports[index].report_id] for index in members) < 0.40
        for members in groups.values()
    )
    review_items = reviewed_clusters + len(unresolved)
    diameters: list[float] = []
    for members in groups.values():
        located = [reports[index] for index in members if reports[index].L is not None]
        diameter = max(
            (haversine_m(left.L, right.L) for offset, left in enumerate(located) for right in located[offset + 1 :]),
            default=0.0,
        )
        diameters.append(diameter)
    singleton_rate = sum(len(members) == 1 for members in groups.values()) / max(1, len(groups))
    n_reports = len(reports)
    return {
        "ari_linked": float(ari),
        "false_destinations_per_100_reports": 100.0 * false_destinations / max(1, n_reports),
        "noise_rejection": noise_rejected / max(1, len(noise_indices)),
        "review_items_per_100_reports": 100.0 * review_items / max(1, n_reports),
        "split_loss": split_loss,
        "merge_loss": merge_loss,
        "max_diameter_m": max(diameters, default=0.0),
        "singleton_rate": singleton_rate,
        "n_reports": n_reports,
        "n_linked_reports": len(linked),
        "n_noise_reports": len(noise_indices),
        "n_noise_rejected": noise_rejected,
        "n_incidents_with_reports": len(incident_units),
        "n_split_incidents": split_incidents,
        "n_operational_destinations": len(groups),
        "n_review_items": review_items,
        "n_false_destinations": false_destinations,
        "n_linked_destinations": len(linked_groups),
        "n_merged_linked_destinations": merged,
    }


__all__ = [
    "CANDIDATE_POOL_K_MULTIPLIER_V2",
    "CANDIDATE_POOL_MIN_NEIGHBORS_V2",
    "CANDIDATE_POOL_RULE_V2",
    "ClusterRunV2",
    "GraphConfigV2",
    "candidate_pool_neighbor_count_v2",
    "clustering_endpoints",
    "run_graph_clustering",
    "run_hdbscan_v2",
    "run_st_dbscan_v2",
]
