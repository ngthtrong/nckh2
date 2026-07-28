"""Hàm trọng số cạnh w_ij dạng nhân/gating — Mục 4.2.

w_ij = S_geo * (beta*S_temp + gamma*S_context)

S_geo    = exp(-dist^2 / (2*sigma_geo^2))           [cổng chặn Gaussian]
S_temp   = exp(-|dt| / tau_temp)                    [suy giảm mũ thời gian]
S_context= exp(-|dF|/tau_F - |dE|/tau_E)            [tương đồng vật lý]
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np

from .attributes import Event, haversine_m
from .config import WeightParams


BoundStatus = Literal["finite", "unbounded", "empty"]


@dataclass(frozen=True)
class GeographicBound:
    """Kết quả phân loại cận địa lý theo đúng miền tham số.

    `radius_m` chỉ có giá trị khi `status == "finite"`. Hai trạng thái còn lại
    được tách rõ để caller không biến tập cạnh rỗng thành cận bán kính 0, hoặc
    biến miền không có cận thành một con số dùng để đếm "vi phạm".
    """

    form: Literal["product", "additive"]
    status: BoundStatus
    theta: float
    beta_gamma_sum: float
    radius_m: float | None
    alpha: float | None = None

    @property
    def domain_eligible(self) -> bool:
        """Chỉ miền `finite` mới đủ điều kiện kiểm bất đẳng thức khoảng cách."""
        return self.status == "finite"


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


def _validate_bound_parameters(
    p: WeightParams, theta: float, alpha: float | None = None
) -> float:
    """Kiểm các giả thiết chung của đặc tả toán học trước khi phân loại miền."""
    values = {
        "theta": theta,
        "sigma_geo_m": p.sigma_geo_m,
        "beta": p.beta,
        "gamma": p.gamma,
    }
    if alpha is not None:
        values["alpha"] = alpha
    for name, value in values.items():
        if not math.isfinite(value):
            raise ValueError(f"{name} phải là số hữu hạn, nhận {value!r}")
    if p.sigma_geo_m <= 0.0:
        raise ValueError(f"sigma_geo_m phải > 0, nhận {p.sigma_geo_m!r}")
    if p.beta < 0.0 or p.gamma < 0.0:
        raise ValueError(
            "cận địa lý yêu cầu beta, gamma không âm; "
            f"nhận beta={p.beta!r}, gamma={p.gamma!r}"
        )
    if alpha is not None and alpha < 0.0:
        raise ValueError(f"cận dạng cộng yêu cầu alpha không âm, nhận {alpha!r}")
    b_sum = p.beta + p.gamma
    if not math.isfinite(b_sum):
        raise ValueError("beta + gamma phải biểu diễn được bằng số hữu hạn")
    return b_sum


def product_distance_bound(p: WeightParams, theta: float) -> GeographicBound:
    """Phân loại cận khoảng cách cho dạng nhân trên TOÀN miền ngưỡng.

    Đặt `B = beta + gamma`. Miền hữu hạn duy nhất là `B > 0` và
    `0 < theta < B`, khi đó mọi cạnh với `weight > theta` thoả

        d < sigma_geo_m * sqrt(2 * log(B / theta)).

    `status="empty"` nghĩa là không cạnh nào có thể vượt ngưỡng; đó không phải
    cận bán kính 0. `status="unbounded"` nghĩa là không có cận hữu hạn suy ra từ
    các tham số này. Xem `revision/math-spec.md`.
    """
    b_sum = _validate_bound_parameters(p, theta)
    if theta < 0.0:
        return GeographicBound("product", "unbounded", theta, b_sum, None)
    if b_sum == 0.0:
        return GeographicBound("product", "empty", theta, b_sum, None)
    if theta == 0.0:
        return GeographicBound("product", "unbounded", theta, b_sum, None)
    if theta >= b_sum:
        return GeographicBound("product", "empty", theta, b_sum, None)
    log_ratio = math.log(b_sum) - math.log(theta)
    radius = p.sigma_geo_m * math.sqrt(2.0 * log_ratio)
    if not math.isfinite(radius):
        raise OverflowError("cận product hữu hạn về toán học nhưng tràn kiểu float")
    return GeographicBound("product", "finite", theta, b_sum, float(radius))


def additive_distance_bound(
    p: WeightParams, theta: float, alpha: float | None = None
) -> GeographicBound:
    """Phân loại cận khoảng cách cho dạng cộng trên TOÀN miền ngưỡng.

    Với `B = beta + gamma` và `a = p.alpha` (hoặc `alpha` tường minh):

    - `B < theta < B + a`: cận hữu hạn
      `sigma * sqrt(2 * log(a / (theta - B)))`;
    - `theta >= B + a`: tập cạnh rỗng dưới ngưỡng strict;
    - miền thấp còn lại: không có cận hữu hạn, ngoại trừ trường hợp suy biến
      `a == 0 and theta == B` cũng là tập rỗng.
    """
    a_w = p.alpha if alpha is None else alpha
    b_sum = _validate_bound_parameters(p, theta, a_w)
    total = b_sum + a_w
    if not math.isfinite(total):
        raise ValueError("alpha + beta + gamma phải biểu diễn được bằng số hữu hạn")
    if theta < 0.0:
        return GeographicBound(
            "additive", "unbounded", theta, b_sum, None, alpha=a_w
        )
    if theta >= total:
        return GeographicBound(
            "additive", "empty", theta, b_sum, None, alpha=a_w
        )
    if theta <= b_sum:
        return GeographicBound(
            "additive", "unbounded", theta, b_sum, None, alpha=a_w
        )
    # `theta < total` và `theta > B` kéo theo `a_w > 0`.
    log_ratio = math.log(a_w) - math.log(theta - b_sum)
    radius = p.sigma_geo_m * math.sqrt(2.0 * log_ratio)
    if not math.isfinite(radius):
        raise OverflowError("cận additive hữu hạn về toán học nhưng tràn kiểu float")
    return GeographicBound(
        "additive", "finite", theta, b_sum, float(radius), alpha=a_w
    )


def implied_distance_cutoff(p: WeightParams, theta: float) -> float:
    """Cận product hữu hạn, giữ tên cũ cho caller trong miền hợp lệ.

    Khác implementation cũ, hàm không trả `0.0` cho tập cạnh rỗng và không trả
    `inf` cho miền không có cận. Hai giá trị đó khiến code downstream có thể
    đếm "vi phạm" ngoài miền định lý. Dùng `product_distance_bound` nếu caller
    cần xử lý cả ba trạng thái.

    Với cấu hình cũ `beta + gamma == 1`, kết quả trong `0 < theta < 1` không
    đổi. Với tổng hệ số khác 1, hàm dùng cận chặt tổng quát chứa `B`.
    """
    bound = product_distance_bound(p, theta)
    if not bound.domain_eligible:
        raise ValueError(
            "implied_distance_cutoff chỉ xác định trong miền product hữu hạn "
            f"(0 < theta < beta + gamma); trạng thái nhận được: {bound.status!r}. "
            "Dùng product_distance_bound để xử lý miền đầy đủ."
        )
    assert bound.radius_m is not None
    return bound.radius_m


def additive_floor(events: list[Event], p: WeightParams,
                   alpha: float | None = None,
                   mode: str = "additive") -> float:
    """Sàn dương, ĐỘC LẬP KHOẢNG CÁCH, của dạng cộng — Hệ quả của Bổ đề 1.

    Với `w_ij = alpha*S_geo + beta*S_temp + gamma*S_ctx`, mọi cặp thoả
    `w_ij >= beta*S_temp + gamma*S_ctx`. Số hạng bên phải KHÔNG phụ thuộc `d_ij`,
    nên với mọi theta nhỏ hơn giá trị nhỏ nhất của nó trên toàn bộ cặp, tập cạnh
    còn lại sau khi làm thưa không bị chặn về khoảng cách: tồn tại cặp cách nhau
    tuỳ ý xa vẫn được giữ.

    Hàm trả về đúng cái sàn đó: `min_{i<j} (beta*S_temp_ij + gamma*S_ctx_ij)`.
    `alpha` không ảnh hưởng giá trị trả về (sàn không chứa số hạng địa lý) nhưng
    được nhận vào cho đối xứng API và để gọi tường minh trong các sweep.
    """
    del alpha  # sàn không phụ thuộc alpha; tham số giữ cho đối xứng API
    ts = np.array([e.created_at.timestamp() for e in events]) / 60.0
    flood = np.array([e.flood for e in events])
    urg = np.array([e.urgency for e in events])
    temp = np.exp(-np.abs(ts[:, None] - ts[None, :]) / p.tau_temp_min)
    ctx = np.exp(-np.abs(flood[:, None] - flood[None, :]) / p.tau_f
                 - np.abs(urg[:, None] - urg[None, :]) / p.tau_e)
    if mode == "additive_norm":
        floor = (temp + ctx) / 3.0
    elif mode == "additive":
        floor = p.beta * temp + p.gamma * ctx
    else:
        raise ValueError(f"mode không hỗ trợ sàn dạng cộng: {mode!r}")
    iu = np.triu_indices(len(events), k=1)
    return float(floor[iu].min()) if len(iu[0]) else 0.0


def max_weight(events: list[Event], p: WeightParams, mode: str = "gating",
               alpha: float | None = None) -> float:
    """`w_max` = trọng số cạnh lớn nhất thực tế trên dataset, theo từng dạng.

    Dùng để chuẩn hoá theta (`theta / w_max`) khi so sánh các dạng trọng số có
    thang giá trị khác nhau — thước đo BẤT BIẾN theo phép tái tham số hoá, khác
    với độ rộng tuyệt đối của cửa sổ theta (không bất biến, xem exp13).
    """
    w = build_weight_matrix_vec(events, p, mode=mode, alpha=alpha)
    iu = np.triu_indices(len(events), k=1)
    return float(w[iu].max()) if len(iu[0]) else 0.0


def max_edge_distance_above(events: list[Event], p: WeightParams, theta: float,
                            mode: str = "gating",
                            alpha: float | None = None) -> tuple[float, int]:
    """`max{d_ij : w_ij > theta}` (mét) và số cạnh vượt ngưỡng.

    Đại lượng thực nghiệm để kiểm định lý trong MIỀN HỮU HẠN đã khai báo.
    Caller phải dùng `product_distance_bound` hoặc `additive_distance_bound`
    để xác nhận miền trước khi so khoảng cách; không đếm hàng `empty` hay
    `unbounded` như một phép kiểm cận.

    Trả về `(0.0, 0)` khi không cạnh nào vượt ngưỡng.
    """
    w = build_weight_matrix_vec(events, p, mode=mode, alpha=alpha)
    lat = np.radians(np.array([e.lat for e in events]))
    lng = np.radians(np.array([e.lng for e in events]))
    r = 6.371e6
    dlat = lat[:, None] - lat[None, :]
    dlng = lng[:, None] - lng[None, :]
    h = (np.sin(dlat / 2) ** 2
         + np.cos(lat)[:, None] * np.cos(lat)[None, :] * np.sin(dlng / 2) ** 2)
    dist = 2 * r * np.arcsin(np.sqrt(np.clip(h, 0.0, 1.0)))
    iu = np.triu_indices(len(events), k=1)
    mask = w[iu] > theta
    if not mask.any():
        return 0.0, 0
    return float(dist[iu][mask].max()), int(mask.sum())


def retained_fraction(events: list[Event], p: WeightParams, theta: float,
                      mode: str = "gating", alpha: float | None = None) -> float:
    """Tỉ lệ cạnh (trên tổng số cặp) còn lại sau khi cắt ở ngưỡng theta.

    Thước đo BẤT BIẾN thứ hai để so sánh các dạng trọng số: không phụ thuộc thang
    giá trị của `w`, chỉ phụ thuộc cấu trúc đồ thị mà ngưỡng sinh ra.
    """
    w = build_weight_matrix_vec(events, p, mode=mode, alpha=alpha)
    iu = np.triu_indices(len(events), k=1)
    vals = w[iu]
    return float((vals > theta).mean()) if len(vals) else 0.0


def max_retained_distance(events: list[Event], w: np.ndarray, theta: float) -> float:
    """Khoảng cách LỚN NHẤT giữa hai đầu của một cạnh có w_ij > theta (mét).

    Đây chỉ là phép đo dữ liệu. Caller phải phân loại miền bằng
    `product_distance_bound`/`additive_distance_bound` trước khi diễn giải nó
    như một phép kiểm định lý. Trả 0.0 nếu không còn cạnh nào.
    """
    n = len(events)
    max_d = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            if w[i, j] > theta:
                d = haversine_m(events[i].lat, events[i].lng,
                                events[j].lat, events[j].lng)
                max_d = max(max_d, d)
    return max_d


def sparsify(w: np.ndarray, p: WeightParams) -> np.ndarray:
    """Làm thưa đồ thị: strict threshold `weight > theta` + k-NN."""
    n = w.shape[0]
    out = w.copy()
    # (i) strict threshold: proof, diagnostics và code cùng dùng `w > theta`.
    out[out <= p.edge_threshold] = 0.0
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
