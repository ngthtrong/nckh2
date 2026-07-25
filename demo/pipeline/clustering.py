"""Phân cụm đồ thị: Louvain + Leiden — Mục 4.3.

Tối ưu Modularity Q với tham số độ phân giải lambda (dạng Reichardt–Bornholdt):
Q = (1/2m) * sum_ij [ A_ij - lambda * k_i*k_j/(2m) ] * delta(c_i, c_j)
"""
from __future__ import annotations

import networkx as nx
import numpy as np
from community import community_louvain

try:
    import igraph as ig
    import leidenalg
    _HAS_LEIDEN = True
except ImportError:  # pragma: no cover
    _HAS_LEIDEN = False


def matrix_to_graph(w: np.ndarray) -> nx.Graph:
    g = nx.Graph()
    n = w.shape[0]
    g.add_nodes_from(range(n))
    for i in range(n):
        for j in range(i + 1, n):
            if w[i, j] > 0:
                g.add_edge(i, j, weight=float(w[i, j]))
    return g


def run_louvain(w: np.ndarray, resolution: float = 1.0, random_state: int = 42) -> list[int]:
    """Trả về nhãn cụm cho từng đỉnh (theo chỉ số hàng của w)."""
    g = matrix_to_graph(w)
    n = w.shape[0]
    if g.number_of_edges() == 0:
        return list(range(n))
    part = community_louvain.best_partition(
        g, weight="weight", resolution=resolution, random_state=random_state
    )
    return [int(part.get(i, i)) for i in range(n)]


def run_leiden(w: np.ndarray, resolution: float = 1.0, random_state: int = 42) -> list[int]:
    """Leiden (đảm bảo cộng đồng liên thông tốt) — Mục 4.3."""
    if not _HAS_LEIDEN:
        raise RuntimeError("leidenalg/igraph chưa được cài đặt")
    n = w.shape[0]
    edges, weights = [], []
    for i in range(n):
        for j in range(i + 1, n):
            if w[i, j] > 0:
                edges.append((i, j))
                weights.append(float(w[i, j]))
    g = ig.Graph(n=n, edges=edges)
    g.es["weight"] = weights
    if len(edges) == 0:
        return list(range(n))
    part = leidenalg.find_partition(
        g,
        leidenalg.RBConfigurationVertexPartition,
        weights="weight",
        resolution_parameter=resolution,
        seed=random_state,
    )
    labels = [0] * n
    for cid, comm in enumerate(part):
        for v in comm:
            labels[v] = cid
    return labels


def modularity(w: np.ndarray, labels: list[int], resolution: float = 1.0) -> float:
    """Modularity Q dạng Reichardt–Bornholdt với tham số độ phân giải lambda (Mục 4.3):

        Q = (1/2m) * sum_ij [ A_ij - lambda * k_i*k_j/(2m) ] * delta(c_i, c_j)

    Tính trực tiếp trên ma trận trọng số để tôn trọng `resolution`; hàm
    `community_louvain.modularity` của thư viện không nhận tham số này nên khi
    resolution=1.0 kết quả trùng khớp Modularity chuẩn.
    """
    n = w.shape[0]
    a = np.array(w, dtype=float)
    np.fill_diagonal(a, 0.0)
    two_m = a.sum()
    if two_m == 0:
        return 0.0
    k = a.sum(axis=1)
    lab = np.asarray(labels)
    same = lab[:, None] == lab[None, :]
    expected = resolution * np.outer(k, k) / two_m
    q = (a - expected)[same].sum() / two_m
    return float(q)


def count_disconnected_communities(w: np.ndarray, labels: list[int]) -> tuple[int, int]:
    """Đếm số cộng đồng bị đứt gãy nội bộ (không liên thông trong subgraph của cụm).

    Trả về (số cụm đứt gãy, tổng số cụm) — dùng cho thí nghiệm Louvain vs Leiden.
    """
    g = matrix_to_graph(w)
    clusters: dict[int, list[int]] = {}
    for node, lab in enumerate(labels):
        clusters.setdefault(lab, []).append(node)
    broken = 0
    for members in clusters.values():
        if len(members) <= 1:
            continue
        sub = g.subgraph(members)
        if sub.number_of_nodes() > 0 and not nx.is_connected(sub):
            broken += 1
    return broken, len(clusters)
