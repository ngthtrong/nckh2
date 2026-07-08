"""Thí nghiệm 5 — Độ ổn định của xếp hạng ưu tiên P(C_k) khi trọng số omega dao động.

Phản biện: ban chỉ huy đặt omega thủ công. Nếu thứ hạng cụm quá nhạy với omega,
danh sách ưu tiên trở nên tùy tiện. Ta nhiễu loạn omega quanh giá trị mặc định
(0.34, 0.33, 0.33), chuẩn hóa lại về tổng = 1, rồi đo Kendall's tau giữa thứ hạng
mới và thứ hạng mặc định. tau ~ 1.0 => xếp hạng ổn định.
"""
from __future__ import annotations

import random

from scipy.stats import kendalltau

from common import prepared_events, print_table, save_table
from pipeline.config import DEFAULT_CONFIG as C
from pipeline.config import PriorityParams
from pipeline.clustering import run_louvain
from pipeline.priority import score_clusters
from pipeline.weighting import build_weight_matrix, sparsify


def _ranking(events, labels, params) -> list[int]:
    """Trả về danh sách cluster_id theo thứ tự P giảm dần."""
    scores = score_clusters(events, labels, params)
    return [s.cluster_id for s in scores]


def _tau_vs_baseline(base_order: list[int], new_order: list[int]) -> float:
    """Kendall's tau giữa hai thứ hạng trên cùng tập cụm."""
    pos_base = {cid: i for i, cid in enumerate(base_order)}
    pos_new = {cid: i for i, cid in enumerate(new_order)}
    common = [cid for cid in base_order if cid in pos_new]
    x = [pos_base[cid] for cid in common]
    y = [pos_new[cid] for cid in common]
    tau, _ = kendalltau(x, y)
    return float(tau)


def _normalize(w_e, w_f, w_n):
    total = w_e + w_f + w_n
    return w_e / total, w_f / total, w_n / total


def main():
    events = prepared_events()
    w = build_weight_matrix(events, C.weight, mode="gating")
    ws = sparsify(w, C.weight)
    lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)

    base_params = C.priority
    base_order = _ranking(events, lab, base_params)

    rng = random.Random(42)
    rows = []
    for level in (0.05, 0.10, 0.20):
        taus = []
        top3_kept = []
        for _ in range(200):
            we = base_params.omega_e + rng.uniform(-level, level)
            wf = base_params.omega_f + rng.uniform(-level, level)
            wn = base_params.omega_n + rng.uniform(-level, level)
            we, wf, wn = _normalize(max(0.0, we), max(0.0, wf), max(0.0, wn))
            p = PriorityParams(
                omega_e=we, omega_f=wf, omega_n=wn, v_scale=base_params.v_scale
            )
            new_order = _ranking(events, lab, p)
            taus.append(_tau_vs_baseline(base_order, new_order))
            # Có giữ nguyên tập 3 cụm ưu tiên cao nhất không?
            top3_kept.append(set(base_order[:3]) == set(new_order[:3]))
        rows.append({
            "omega_perturbation": f"+/-{level:.2f}",
            "mean_kendall_tau": round(sum(taus) / len(taus), 4),
            "min_kendall_tau": round(min(taus), 4),
            "top3_set_preserved_pct": round(100 * sum(top3_kept) / len(top3_kept), 1),
            "n_trials": len(taus),
        })

    print_table("Độ ổn định xếp hạng P(C_k) khi omega dao động (Kendall's tau)", rows)
    save_table("exp5_ranking_stability.json", rows)
    print("\n[saved] exp5_ranking_stability.json -> results/tables/")


if __name__ == "__main__":
    main()
