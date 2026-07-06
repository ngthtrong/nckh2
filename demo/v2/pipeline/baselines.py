"""Baseline phân cụm để đối chiếu với Louvain/Leiden — Mục 2.4.

K-Means: cần biết trước K; DBSCAN: nhạy tham số. Cả hai chạy trên đặc trưng
[lat, lng chuẩn hóa] để so sánh công bằng với đồ thị không gian-ngữ nghĩa.
"""
from __future__ import annotations

import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler

from .attributes import Event


def _feature_matrix(events: list[Event]) -> np.ndarray:
    """Đặc trưng cho baseline: tọa độ + mức ngập + khẩn cấp (đã chuẩn hóa)."""
    raw = np.array(
        [[ev.lat, ev.lng, ev.flood, ev.urgency] for ev in events], dtype=float
    )
    return StandardScaler().fit_transform(raw)


def run_kmeans(events: list[Event], n_clusters: int, random_state: int = 42) -> list[int]:
    x = _feature_matrix(events)
    n_clusters = max(1, min(n_clusters, len(events)))
    km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    return km.fit_predict(x).tolist()


def run_dbscan(events: list[Event], eps: float = 0.5, min_samples: int = 3) -> list[int]:
    x = _feature_matrix(events)
    db = DBSCAN(eps=eps, min_samples=min_samples)
    return db.fit_predict(x).tolist()
