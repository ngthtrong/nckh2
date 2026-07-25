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


def edge_weight_additive(a: Event, b: Event, p: WeightParams,
                         alpha: float | None = None) -> float:
    """Dạng cộng (baseline ablation — Mục 4.2 'dạng ngây thơ').

    w_ij = alpha*S_geo + beta*S_temp + gamma*S_context

    `alpha` mặc định lấy từ `p.alpha` (= 0.5 = beta = gamma), tức baseline được
    cho trọng số địa lý NGANG BẰNG thời gian/ngữ cảnh. Truyền alpha tường minh
    để quét tham số; mọi kết luận cộng-vs-nhân phải nêu rõ alpha đã dùng.
    """
    a_w = p.alpha if alpha is None else alpha
    geo = s_geo(a, b, p.sigma_geo_m)
    temp = s_temp(a, b, p.tau_temp_min)
    ctx = s_context(a, b, p.tau_f, p.tau_e)
    return a_w * geo + p.beta * temp + p.gamma * ctx


def edge_weight_additive_normalized(a: Event, b: Event, p: WeightParams) -> float:
    """Dạng cộng CHUẨN HOÁ: alpha = beta = gamma = 1/3 (tổng = 1).

    Đây là biến thể cộng công bằng nhất — cùng thang [0,1] với dạng nhân và
    không ưu tiên thành phần nào. Dùng làm baseline chính khi so sánh.
    """
    third = 1.0 / 3.0
    geo = s_geo(a, b, p.sigma_geo_m)
    temp = s_temp(a, b, p.tau_temp_min)
    ctx = s_context(a, b, p.tau_f, p.tau_e)
    return third * (geo + temp + ctx)


def build_weight_matrix(events: list[Event], p: WeightParams, mode: str = "gating",
                        alpha: float | None = None) -> np.ndarray:
    """Ma trận trọng số đối xứng W (n x n), chưa làm thưa.

    mode: "gating" | "additive" | "additive_norm"
    alpha: chỉ có tác dụng với mode="additive" (None = dùng p.alpha).
    """
    n = len(events)
    w = np.zeros((n, n), dtype=float)
    if mode == "gating":
        def fn(x, y):
            return edge_weight_gating(x, y, p)
    elif mode == "additive_norm":
        def fn(x, y):
            return edge_weight_additive_normalized(x, y, p)
    elif mode == "additive":
        def fn(x, y):
            return edge_weight_additive(x, y, p, alpha)
    else:
        raise ValueError(f"mode không hợp lệ: {mode!r}")
    for i in range(n):
        for j in range(i + 1, n):
            val = fn(events[i], events[j])
            w[i, j] = w[j, i] = val
    return w


def build_weight_matrix_vec(events: list[Event], p: WeightParams,
                            mode: str = "gating", alpha: float | None = None) -> np.ndarray:
    """Bản vector-hoá của `build_weight_matrix` (numpy broadcast).

    Cùng công thức, cùng kết quả (sai số < 1e-12), nhưng bỏ vòng lặp Python —
    dùng để chứng minh chi phí O(n^2) của bản tham chiếu là chi tiết cài đặt,
    không phải giới hạn của thuật toán (xem exp11).
    """
    lat = np.radians(np.array([e.lat for e in events]))
    lng = np.radians(np.array([e.lng for e in events]))
    ts = np.array([e.created_at.timestamp() for e in events]) / 60.0
    flood = np.array([e.flood for e in events])
    urg = np.array([e.urgency for e in events])

    # Haversine vector hoá (cùng R với attributes.haversine_m)
    r = 6.371e6
    dlat = lat[:, None] - lat[None, :]
    dlng = lng[:, None] - lng[None, :]
    h = (np.sin(dlat / 2) ** 2
         + np.cos(lat)[:, None] * np.cos(lat)[None, :] * np.sin(dlng / 2) ** 2)
    dist = 2 * r * np.arcsin(np.sqrt(np.clip(h, 0.0, 1.0)))

    geo = np.exp(-(dist ** 2) / (2.0 * p.sigma_geo_m ** 2))
    temp = np.exp(-np.abs(ts[:, None] - ts[None, :]) / p.tau_temp_min)
    ctx = np.exp(-np.abs(flood[:, None] - flood[None, :]) / p.tau_f
                 - np.abs(urg[:, None] - urg[None, :]) / p.tau_e)

    if mode == "gating":
        w = geo * (p.beta * temp + p.gamma * ctx)
    elif mode == "additive_norm":
        w = (geo + temp + ctx) / 3.0
    elif mode == "additive":
        a_w = p.alpha if alpha is None else alpha
        w = a_w * geo + p.beta * temp + p.gamma * ctx
    else:
        raise ValueError(f"mode không hợp lệ: {mode!r}")
    np.fill_diagonal(w, 0.0)
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
