"""Baseline phân cụm để đối chiếu với Louvain/Leiden — Mục 2.4.

K-Means: cần biết trước K; DBSCAN: nhạy tham số. Cả hai chạy trên đặc trưng
[lat, lng chuẩn hóa] để so sánh công bằng với đồ thị không gian-ngữ nghĩa.
"""
from __future__ import annotations

import numpy as np
from sklearn.cluster import (
    DBSCAN,
    HDBSCAN,
    AgglomerativeClustering,
    KMeans,
    SpectralClustering,
)
from sklearn.preprocessing import StandardScaler

from .attributes import Event


def _feature_matrix(events: list[Event], features: str = "geo_context") -> np.ndarray:
    """Đặc trưng (đã chuẩn hóa) cho các baseline hình học.

    `features` phải được khai TƯỜNG MINH ở nơi gọi, vì hai lựa chọn trả lời hai
    câu hỏi khác nhau và trước đây bị lẫn:
      - `"geo"`         : CHỈ [lat, lng]. Đây mới là baseline "toạ độ thô" thật,
        dùng để trả lời "địa lý một mình có đủ chưa?".
      - `"geo_context"` : [lat, lng, flood, urgency] — nối ngữ cảnh vào không gian
        Euclid theo kiểu CỘNG CHIỀU. Đây KHÔNG phải baseline toạ độ thô; nó là
        đối chứng cho thấy nhồi ngữ cảnh vào metric Euclid khác hẳn việc dùng
        ngữ cảnh theo dạng nhân (gating) như phương pháp đề xuất.
    """
    if features == "geo":
        cols = [[ev.lat, ev.lng] for ev in events]
    elif features == "geo_context":
        cols = [[ev.lat, ev.lng, ev.flood, ev.urgency] for ev in events]
    else:
        raise ValueError(f"features phải là 'geo' hoặc 'geo_context', nhận: {features!r}")
    return StandardScaler().fit_transform(np.array(cols, dtype=float))


def run_kmeans(
    events: list[Event],
    n_clusters: int,
    random_state: int = 42,
    features: str = "geo_context",
) -> list[int]:
    x = _feature_matrix(events, features)
    n_clusters = max(1, min(n_clusters, len(events)))
    km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    return km.fit_predict(x).tolist()


def run_dbscan(
    events: list[Event],
    eps: float = 0.5,
    min_samples: int = 3,
    features: str = "geo_context",
) -> list[int]:
    x = _feature_matrix(events, features)
    db = DBSCAN(eps=eps, min_samples=min_samples)
    return db.fit_predict(x).tolist()


def run_spectral(w: np.ndarray, n_clusters: int, random_state: int = 42) -> list[int]:
    """Spectral Clustering ăn TRỰC TIẾP ma trận affinity w_ij (đồ thị gating).

    Đây là baseline công bằng nhất: dùng cùng ma trận trọng số như Louvain/Leiden,
    khác biệt chỉ nằm ở thuật toán phân hoạch (spectral vs modularity).
    """
    n_clusters = max(1, min(n_clusters, w.shape[0]))
    sc = SpectralClustering(
        n_clusters=n_clusters,
        affinity="precomputed",
        assign_labels="discretize",
        random_state=random_state,
    )
    return sc.fit_predict(w).tolist()


def run_hdbscan_on_graph(w: np.ndarray, min_cluster_size: int = 3) -> list[int]:
    """HDBSCAN trên ma trận KHOẢNG CÁCH d_ij = 1 - w_ij_chuẩn_hóa (cùng đồ thị gating).

    Baseline mật độ, tự tìm số cụm, chạy trên cùng thông tin trọng số như phương pháp
    đề xuất — thay vì trên tọa độ thô.
    """
    wmax = w.max() if w.max() > 0 else 1.0
    dist = 1.0 - (w / wmax)
    np.fill_diagonal(dist, 0.0)
    hdb = HDBSCAN(min_cluster_size=min_cluster_size, metric="precomputed")
    return hdb.fit_predict(dist.astype(float)).tolist()


def run_agglomerative_on_graph(w: np.ndarray, n_clusters: int) -> list[int]:
    """Agglomerative (average linkage) trên khoảng cách d_ij = 1 - w_ij chuẩn hóa."""
    wmax = w.max() if w.max() > 0 else 1.0
    dist = 1.0 - (w / wmax)
    np.fill_diagonal(dist, 0.0)
    n_clusters = max(1, min(n_clusters, w.shape[0]))
    agg = AgglomerativeClustering(
        n_clusters=n_clusters, metric="precomputed", linkage="average"
    )
    return agg.fit_predict(dist).tolist()
