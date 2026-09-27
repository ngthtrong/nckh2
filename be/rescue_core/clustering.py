# Dựa trên demo/v2/clustering.py tại commit a6be3e9 (chỉ phần run_graph_clustering; bỏ
# baseline HDBSCAN/ST-DBSCAN và metric benchmark). Đã chỉnh cho khớp Algorithm 1 của bài
# báo ISDS 2026 và notebook Benchmark_Cij (commit 6ac75c2): G, T, C tính trên toàn bộ ma
# trận cặp đủ điều kiện thay cho candidate pool BallTree; công thức trọng số giữ nguyên.
"""Graph clustering of graph-eligible reports (Algorithm 1)."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Sequence

import networkx as nx
import numpy as np
from community import community_louvain

from .contracts import ReportV2, validate_unique_report_ids


CompositionOperator = Literal["product", "additive"]
EARTH_RADIUS_M = 6_371_000.0


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


def _pair_weight_matrix(
    reports: Sequence[ReportV2],
    eligible: Sequence[int],
    config: GraphConfigV2,
) -> np.ndarray:
    """Eq. (2)-(3) on the full eligible pair matrix, with a zero diagonal.

    Vectorized form of ``similarity.geographic/temporal/context_similarity``:
    missing F or E contributes nothing and discounts C by m_ij / 2.
    """

    rows = [reports[index] for index in eligible]
    lat = np.radians(np.asarray([row.L[0] for row in rows], dtype=float))
    lng = np.radians(np.asarray([row.L[1] for row in rows], dtype=float))
    dlat = lat[:, None] - lat[None, :]
    dlng = lng[:, None] - lng[None, :]
    hav = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat)[:, None] * np.cos(lat)[None, :] * np.sin(dlng / 2.0) ** 2
    )
    distance = 2.0 * EARTH_RADIUS_M * np.arcsin(np.sqrt(np.clip(hav, 0.0, 1.0)))
    t0 = rows[0].T
    minute = np.asarray([(row.T - t0).total_seconds() / 60.0 for row in rows], dtype=float)
    delta_min = np.abs(minute[:, None] - minute[None, :])

    def observed(field: str) -> tuple[np.ndarray, np.ndarray]:
        values = [getattr(row, field) for row in rows]
        mask = np.asarray([value is not None for value in values], dtype=bool)
        numbers = np.asarray([0.0 if value is None else float(value) for value in values])
        return mask, numbers

    obs_f, flood = observed("F")
    obs_e, urgency = observed("E")
    i_f = (obs_f[:, None] & obs_f[None, :]).astype(float)
    i_e = (obs_e[:, None] & obs_e[None, :]).astype(float)
    shared = i_f + i_e
    context = (shared / 2.0) * np.exp(
        -i_f * np.abs(flood[:, None] - flood[None, :]) / config.tau_F
        - i_e * np.abs(urgency[:, None] - urgency[None, :]) / config.tau_E
    )
    context[shared == 0.0] = 0.0

    geographic = np.exp(-(distance**2) / (2.0 * config.sigma_geo_m**2))
    temporal = np.exp(-delta_min / config.tau_t)
    if config.composition_operator == "product":
        weight = geographic * (config.beta * temporal + config.gamma * context)
    else:
        weight = config.alpha * geographic + config.beta * temporal + config.gamma * context
    np.fill_diagonal(weight, 0.0)
    return weight


def run_graph_clustering(
    reports: Sequence[ReportV2],
    config: GraphConfigV2,
    *,
    random_state: int = 42,
) -> ClusterRunV2:
    """Algorithm 1: threshold, union top-k and Louvain on the eligible pairs.

    Weights are computed on the full eligible pair matrix.  theta is the
    ``threshold_quantile`` of the nonzero pair weights; each report keeps its
    top-k neighbours above theta (ties broken by report_id) and the union of
    the directed selections forms the undirected graph.  Memory is O(n^2).
    """

    validate_unique_report_ids(reports)
    eligible, review = _eligible_indices(reports)
    labels = [-1] * len(reports)
    if not eligible:
        return ClusterRunV2(config.composition_operator, tuple(labels), tuple(reports[index].report_id for index in review), None, 0, 0)
    n_eligible = len(eligible)
    weights = _pair_weight_matrix(reports, eligible, config)
    upper = weights[np.triu_indices(n_eligible, 1)]
    positive = upper[upper > 0.0]
    threshold = float(np.quantile(positive, config.threshold_quantile)) if positive.size else math.inf
    above = weights > threshold
    report_id_by_index = {index: reports[index].report_id for index in eligible}
    # Rank of each report id, used to break weight ties deterministically.
    id_rank = np.empty(n_eligible, dtype=np.int64)
    id_rank[np.argsort([reports[index].report_id for index in eligible], kind="stable")] = np.arange(n_eligible)
    selected: set[tuple[int, int]] = set()
    for local in range(n_eligible):
        neighbours = np.nonzero(above[local])[0]
        if neighbours.size == 0:
            continue
        order = np.lexsort((id_rank[neighbours], -weights[local, neighbours]))
        for other in neighbours[order[: config.k]]:
            left, right = sorted((local, int(other)))
            selected.add((eligible[left], eligible[right]))
    local_by_index = {index: local for local, index in enumerate(eligible)}
    weight_lookup = {
        (left, right): float(weights[local_by_index[left], local_by_index[right]])
        for left, right in selected
    }
    graph = nx.Graph()
    index_by_report_id = {identifier: index for index, identifier in report_id_by_index.items()}
    graph.add_nodes_from(sorted(index_by_report_id))
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
        candidate_pairs=n_eligible * (n_eligible - 1) // 2,
        retained_edges=len(selected),
    )


__all__ = [
    "ClusterRunV2",
    "GraphConfigV2",
    "run_graph_clustering",
]
