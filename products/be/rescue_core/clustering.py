# Dựa trên demo/v2/clustering.py tại commit a6be3e9 (chỉ phần run_graph_clustering; bỏ
# baseline HDBSCAN/ST-DBSCAN và metric benchmark). Đã chỉnh cho khớp Algorithm 1 của bài
# báo ISDS 2026 và notebook Benchmark_Cij (commit 6ac75c2): G, T, C tính trên toàn bộ ma
# trận cặp đủ điều kiện thay cho candidate pool BallTree; công thức trọng số giữ nguyên.
# Ma trận trọng số tính tại chỗ (cùng phép tính, cùng thứ tự) để giảm bộ nhớ; trọng số
# và nhãn cụm trùng khớp từng bit với bản trước trên cả 80 run gold.
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

    Every step runs in place with the same operations in the same order as the
    direct expressions (bit-identical weights), so at most four n x n float
    matrices are alive at once instead of one per intermediate.
    """

    rows = [reports[index] for index in eligible]
    n = len(rows)

    def outer(values: np.ndarray, op) -> np.ndarray:
        return op(values[:, None], values[None, :])

    def observed(field: str) -> tuple[np.ndarray, np.ndarray]:
        values = [getattr(row, field) for row in rows]
        mask = np.asarray([value is not None for value in values], dtype=bool)
        numbers = np.asarray([0.0 if value is None else float(value) for value in values])
        return mask, numbers

    # C_ij = (m_ij / 2) * exp(-I_F |dF| / tau_F - I_E |dE| / tau_E), 0 when m_ij = 0.
    obs_f, flood = observed("F")
    obs_e, urgency = observed("E")
    context = outer(obs_f, np.logical_and).astype(float)  # i_f
    np.negative(context, out=context)
    work = outer(flood, np.subtract)
    np.abs(work, out=work)
    np.multiply(context, work, out=context)
    np.divide(context, config.tau_F, out=context)
    i_e = outer(obs_e, np.logical_and).astype(float)
    np.subtract(urgency[:, None], urgency[None, :], out=work)
    np.abs(work, out=work)
    np.multiply(i_e, work, out=work)
    np.divide(work, config.tau_E, out=work)
    np.subtract(context, work, out=context)
    np.exp(context, out=context)
    shared = outer(obs_f, np.logical_and).astype(float)  # i_f + i_e
    np.add(shared, i_e, out=shared)
    del i_e
    no_shared = shared == 0.0
    np.divide(shared, 2.0, out=shared)
    np.multiply(shared, context, out=context)
    context[no_shared] = 0.0
    del shared, no_shared

    # Haversine distance, then G_ij = exp(-d^2 / (2 sigma^2)).
    lat = np.radians(np.asarray([row.L[0] for row in rows], dtype=float))
    lng = np.radians(np.asarray([row.L[1] for row in rows], dtype=float))
    geographic = outer(lat, np.subtract)
    np.divide(geographic, 2.0, out=geographic)
    np.sin(geographic, out=geographic)
    np.square(geographic, out=geographic)
    np.subtract(lng[:, None], lng[None, :], out=work)
    np.divide(work, 2.0, out=work)
    np.sin(work, out=work)
    np.square(work, out=work)
    cos_lat = np.cos(lat)
    cos_product = outer(cos_lat, np.multiply)
    np.multiply(cos_product, work, out=work)
    del cos_product
    np.add(geographic, work, out=geographic)
    np.clip(geographic, 0.0, 1.0, out=geographic)
    np.sqrt(geographic, out=geographic)
    np.arcsin(geographic, out=geographic)
    np.multiply(2.0 * EARTH_RADIUS_M, geographic, out=geographic)
    np.square(geographic, out=geographic)
    np.negative(geographic, out=geographic)
    np.divide(geographic, 2.0 * config.sigma_geo_m**2, out=geographic)
    np.exp(geographic, out=geographic)

    # T_ij = exp(-|dt| / tau_t) in minutes.
    t0 = rows[0].T
    minute = np.asarray([(row.T - t0).total_seconds() / 60.0 for row in rows], dtype=float)
    temporal = work
    np.subtract(minute[:, None], minute[None, :], out=temporal)
    np.abs(temporal, out=temporal)
    np.negative(temporal, out=temporal)
    np.divide(temporal, config.tau_t, out=temporal)
    np.exp(temporal, out=temporal)

    np.multiply(config.beta, temporal, out=temporal)
    np.multiply(config.gamma, context, out=context)
    if config.composition_operator == "product":
        np.add(temporal, context, out=temporal)
        weight = np.multiply(geographic, temporal, out=geographic)
    else:
        np.multiply(config.alpha, geographic, out=geographic)
        np.add(geographic, temporal, out=geographic)
        weight = np.add(geographic, context, out=geographic)
    np.fill_diagonal(weight, 0.0)
    assert weight.shape == (n, n)
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
    # Mask thay cho np.triu_indices: cùng các phần tử, không cần hai mảng chỉ số cỡ n^2.
    upper = weights[np.triu(np.ones((n_eligible, n_eligible), dtype=bool), 1)]
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
