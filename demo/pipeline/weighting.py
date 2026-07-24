"""Hàm trọng số cạnh w_ij dạng nhân/gating — Mục 4.2.

w_ij = S_geo * (beta*S_temp + gamma*S_context)

S_geo    = exp(-dist^2 / (2*sigma_geo^2))           [cổng chặn Gaussian]
S_temp   = exp(-|dt| / tau_temp)                    [suy giảm mũ thời gian]
S_context= exp(-|dF|/tau_F - |dE|/tau_E)            [tương đồng vật lý]
"""
from __future__ import annotations

import math

import numpy as np

from .attributes import Event, haversine_m
from .config import WeightParams


def s_geo(a: Event, b: Event, sigma_geo_m: float) -> float:
    dist = haversine_m(a.lat, a.lng, b.lat, b.lng)
    return math.exp(-(dist ** 2) / (2.0 * sigma_geo_m ** 2))


def s_temp(a: Event, b: Event, tau_temp_min: float) -> float:
    dt_min = abs((a.created_at - b.created_at).total_seconds()) / 60.0
    return math.exp(-dt_min / tau_temp_min)


def s_context(a: Event, b: Event, tau_f: float, tau_e: float) -> float:
    d_flood = abs(a.flood - b.flood)
    d_urg = abs(a.urgency - b.urgency)
    return math.exp(-d_flood / tau_f - d_urg / tau_e)


def edge_weight_gating(a: Event, b: Event, p: WeightParams) -> float:
    """Dạng nhân/gating đã sửa (Mục 4.2)."""
    geo = s_geo(a, b, p.sigma_geo_m)
    temp = s_temp(a, b, p.tau_temp_min)
    ctx = s_context(a, b, p.tau_f, p.tau_e)
    return geo * (p.beta * temp + p.gamma * ctx)


def edge_weight_additive(a: Event, b: Event, p: WeightParams, alpha: float = 0.34) -> float:
    """Dạng cộng cũ (dùng cho ablation so sánh — Mục 4.2 'dạng ngây thơ').

    w_ij = alpha*S_geo + beta*S_temp + gamma*S_context
    """
    geo = s_geo(a, b, p.sigma_geo_m)
    temp = s_temp(a, b, p.tau_temp_min)
    ctx = s_context(a, b, p.tau_f, p.tau_e)
    return alpha * geo + p.beta * temp + p.gamma * ctx


def build_weight_matrix(events: list[Event], p: WeightParams, mode: str = "gating") -> np.ndarray:
    """Ma trận trọng số đối xứng W (n x n), chưa làm thưa."""
    n = len(events)
    w = np.zeros((n, n), dtype=float)
    fn = edge_weight_gating if mode == "gating" else edge_weight_additive
    for i in range(n):
        for j in range(i + 1, n):
            val = fn(events[i], events[j], p)
            w[i, j] = w[j, i] = val
    return w


def sparsify(w: np.ndarray, p: WeightParams) -> np.ndarray:
    """Làm thưa đồ thị: ngưỡng epsilon + k-NN (Mục 4.2)."""
    n = w.shape[0]
    out = w.copy()
    # (i) ngưỡng epsilon
    out[out < p.edge_threshold] = 0.0
    # (ii) k-NN: mỗi đỉnh chỉ giữ k cạnh trọng số cao nhất (đối xứng hóa bằng OR)
    if p.knn and p.knn > 0 and p.knn < n:
        mask = np.zeros_like(out, dtype=bool)
        for i in range(n):
            row = out[i]
            if np.count_nonzero(row) > p.knn:
                top = np.argpartition(row, -p.knn)[-p.knn:]
            else:
                top = np.nonzero(row)[0]
            mask[i, top] = True
        mask = mask | mask.T   # giữ cạnh nếu là k-NN của ít nhất một đầu
        out = np.where(mask, out, 0.0)
    np.fill_diagonal(out, 0.0)
    return out
