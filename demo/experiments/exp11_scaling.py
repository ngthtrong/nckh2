"""Thí nghiệm 11 — Chi phí tính toán theo quy mô (phản biện 3.1).

Phản biện: bài báo tuyên bố hệ thống chạy được ở quy mô thảm hoạ thật nhưng mọi
bằng chứng đều trên n = 341 sự kiện, và không có một con số thời gian nào. Xây
ma trận trọng số là O(n^2) nên tuyên bố đó cần được ĐO, không được suy diễn.

Thí nghiệm này đo thời gian thực trên n tăng dần, tách theo ba giai đoạn:
  1. build   — dựng ma trận w_ij (O(n^2), phần chi phối)
  2. sparsify— ngưỡng theta + k-NN
  3. louvain — phát hiện cộng đồng

Đo cả hai cách dựng ma trận:
  - vòng lặp Python thuần (bản gốc, dễ đọc)
  - vectơ hoá numpy (cùng công thức, xem `build_weight_matrix_vec`)
để cho thấy hằng số nhân giảm bao nhiêu mà KHÔNG đổi bậc phức tạp — bậc vẫn là
O(n^2). Ta báo cáo cả tỉ số thời gian giữa các mức n để kiểm chứng bậc bình
phương theo kinh nghiệm (n gấp đôi -> thời gian ~gấp 4).
"""
from __future__ import annotations

import time

import numpy as np

from common import print_table, save_table
from data.generate import make_events
from pipeline.attributes import compute_confidence
from pipeline.config import DEFAULT_CONFIG as C
from pipeline.clustering import run_louvain
from pipeline.weighting import (
    build_weight_matrix,
    build_weight_matrix_vec,
    sparsify,
)

# n mục tiêu: điều khiển qua số điểm mỗi ốc đảo + số điểm nhiễu.
# 6 ốc đảo * n_per_cluster + n_noise + 41 điểm kịch bản.
SIZES = [
    (40, 60),      # ~341  — đúng dataset chính
    (160, 200),    # ~1201
    (490, 600),    # ~3581
    (990, 1200),   # ~7181
]

# Với n lớn, vòng lặp Python thuần quá chậm để đo lặp lại; chỉ đo tới ngưỡng này.
PURE_LOOP_MAX_N = 3600


def _timed(fn):
    t0 = time.perf_counter()
    out = fn()
    return out, time.perf_counter() - t0


def main() -> None:
    rows = []
    prev = None
    for n_per, n_noise in SIZES:
        events = make_events(seed=42, n_per_cluster=n_per, n_noise=n_noise)
        compute_confidence(events, C.confidence)
        n = len(events)

        # --- dựng ma trận: bản vectơ hoá (dùng cho mọi mức n) ---
        w_vec, t_build_vec = _timed(
            lambda: build_weight_matrix_vec(events, C.weight, mode="gating"))

        # --- dựng ma trận: vòng lặp Python thuần (chỉ n nhỏ) ---
        if n <= PURE_LOOP_MAX_N:
            w_pure, t_build_pure = _timed(
                lambda: build_weight_matrix(events, C.weight, mode="gating"))
            # xác nhận hai bản cho CÙNG kết quả (sai số số học không đáng kể)
            max_diff = float(np.max(np.abs(w_pure - w_vec)))
        else:
            t_build_pure = None
            max_diff = None

        ws, t_sparsify = _timed(lambda: sparsify(w_vec, C.weight))
        lab, t_louvain = _timed(
            lambda: run_louvain(ws, C.cluster.resolution, C.cluster.random_state))

        t_total_vec = t_build_vec + t_sparsify + t_louvain
        row = {
            "n_events": n,
            "build_vec_s": round(t_build_vec, 4),
            "build_pure_s": round(t_build_pure, 4) if t_build_pure else None,
            "speedup_vec": round(t_build_pure / t_build_vec, 1) if t_build_pure else None,
            "sparsify_s": round(t_sparsify, 4),
            "louvain_s": round(t_louvain, 4),
            "total_vec_s": round(t_total_vec, 4),
            "n_clusters": len(set(lab)),
            "edges_after_sparsify": int(np.count_nonzero(np.triu(ws, 1))),
            "max_abs_diff_vec_vs_pure": max_diff,
        }
        # kiểm chứng bậc O(n^2) theo kinh nghiệm
        if prev is not None:
            ratio_n = n / prev[0]
            ratio_t = t_build_vec / prev[1] if prev[1] > 0 else None
            row["n_ratio_vs_prev"] = round(ratio_n, 2)
            row["build_time_ratio_vs_prev"] = round(ratio_t, 2) if ratio_t else None
            row["expected_ratio_if_quadratic"] = round(ratio_n ** 2, 2)
        prev = (n, t_build_vec)
        rows.append(row)

    print_table("Exp11 — Chi phí tính toán theo quy mô (giây, tách theo giai đoạn)", rows)
    print("\n--- Diễn giải ---")
    print("build là giai đoạn chi phối và có bậc O(n^2): so cột build_time_ratio_vs_prev")
    print("với expected_ratio_if_quadratic. Vectơ hoá chỉ giảm HẰNG SỐ NHÂN (cột")
    print("speedup_vec), KHÔNG đổi bậc — nên với n cỡ chục nghìn, cần phân hoạch")
    print("không gian (grid/ball-tree) để chỉ tính w_ij cho các cặp trong bán kính")
    print("~3*sigma_geo; đây là giới hạn thật của bản hiện tại, nêu rõ trong bài.")
    print("max_abs_diff_vec_vs_pure ~ 0 xác nhận hai cách dựng cho cùng ma trận.")

    save_table("exp11_scaling.json", rows)
    print("\n[saved] exp11_scaling.json -> results/tables/")


if __name__ == "__main__":
    main()
