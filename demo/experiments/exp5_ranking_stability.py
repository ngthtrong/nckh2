"""Thí nghiệm 5 — Độ ổn định của xếp hạng ưu tiên P(C_k).

Phản biện: ban chỉ huy đặt omega thủ công. Nếu thứ hạng cụm quá nhạy với omega,
danh sách ưu tiên trở nên tùy tiện. Ta nhiễu loạn omega quanh giá trị mặc định
(0.34, 0.33, 0.33), chuẩn hóa lại về tổng = 1, rồi đo Kendall's tau giữa thứ hạng
mới và thứ hạng mặc định. tau ~ 1.0 => xếp hạng ổn định.

Mở rộng (phản biện 4.3): omega không phải bậc tự do duy nhất ảnh hưởng thứ hạng.
Ta bổ sung hai phép thử robustness:
  - nhiễu loạn s (v_scale) — ảnh hưởng V_agg.
  - nhiễu loạn CẤU TRÚC cụm qua sigma_geo — cụm đổi thì thứ hạng còn giữ không?
    (đây mới là phép thử robustness thật, không chỉ đổi trọng số trên cùng cụm).
    Vì sigma_geo đổi làm tập cụm & cluster_id đổi, ta KHỚP cụm giữa hai cấu hình
    theo trọng tâm gần nhất rồi đo Kendall's tau trên các cụm khớp được.
"""
from __future__ import annotations

import random

from scipy.stats import kendalltau

from common import prepared_events, print_table, save_table
from pipeline.config import DEFAULT_CONFIG as C
from pipeline.config import PriorityParams, WeightParams
from pipeline.clustering import run_louvain
from pipeline.priority import score_clusters
from pipeline.attributes import haversine_m
from pipeline.weighting import build_weight_matrix, sparsify


def _ranking(events, labels, params) -> list[int]:
    """Trả về danh sách cluster_id theo thứ tự P giảm dần."""
    scores = score_clusters(events, labels, params)
    return [s.cluster_id for s in scores]


def _tau_vs_baseline(
    base_order: list[int], new_order: list[int], restrict: set[int] | None = None
) -> float:
    """Kendall's tau giữa hai thứ hạng trên cùng tập cụm.

    `restrict`: nếu cho, chỉ tính tau trên các cluster_id trong tập này.

    VÌ SAO CẦN `restrict`: phân hoạch gating sinh 61 singleton trong 74 cụm, tức
    82% "cụm" chỉ có một sự kiện. Singleton có V = 0 thường xuyên nên V_agg = 1
    và điểm P của chúng gần như chỉ phụ thuộc một điểm dữ liệu — thứ hạng của
    chúng rất ít bị đảo khi omega dao động. Tau tính trên toàn 74 cụm vì thế bị
    đám singleton "kéo lên" và có thể phóng đại độ ổn định của phần danh sách mà
    ban điều phối thực sự dùng. Tau hạn chế trên các cụm >= 2 thành viên là con
    số khắt khe hơn và phải được báo cáo song song.
    """
    pos_base = {cid: i for i, cid in enumerate(base_order)}
    pos_new = {cid: i for i, cid in enumerate(new_order)}
    common = [cid for cid in base_order if cid in pos_new]
    if restrict is not None:
        common = [cid for cid in common if cid in restrict]
    if len(common) < 2:
        return float("nan")
    x = [pos_base[cid] for cid in common]
    y = [pos_new[cid] for cid in common]
    tau, _ = kendalltau(x, y)
    return float(tau)


def _normalize(w_e, w_f, w_n):
    total = w_e + w_f + w_n
    return w_e / total, w_f / total, w_n / total


def _stability_omega(events, lab, base_order):
    """Nhiễu loạn omega (trọng số lõi) trên CÙNG tập cụm.

    Báo cáo tau theo HAI phạm vi (xem `_tau_vs_baseline`): toàn bộ cụm, và chỉ
    các cụm >= 2 thành viên. Phạm vi thứ hai loại 61 singleton — nhóm có thứ
    hạng gần như bất động nên làm tau toàn cục trông ổn định hơn thực tế đối với
    phần danh sách mà điều phối thực sự dùng.
    """
    base_params = C.priority
    rng = random.Random(42)

    # cụm có >= 2 thành viên (loại singleton)
    sizes: dict[int, int] = {}
    for l in lab:
        sizes[l] = sizes.get(l, 0) + 1
    multi = {cid for cid, n in sizes.items() if n >= 2}

    rows = []
    for level in (0.05, 0.10, 0.20):
        taus = []
        taus_multi = []
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
            taus_multi.append(_tau_vs_baseline(base_order, new_order, restrict=multi))
            top3_kept.append(set(base_order[:3]) == set(new_order[:3]))
        rows.append({
            "omega_perturbation": f"+/-{level:.2f}",
            "mean_kendall_tau": round(sum(taus) / len(taus), 4),
            "min_kendall_tau": round(min(taus), 4),
            "mean_kendall_tau_multi": round(sum(taus_multi) / len(taus_multi), 4),
            "min_kendall_tau_multi": round(min(taus_multi), 4),
            "n_clusters_multi": len(multi),
            "top3_set_preserved_pct": round(100 * sum(top3_kept) / len(top3_kept), 1),
            "n_trials": len(taus),
        })
    return rows


def _stability_v_scale(events, lab, base_order):
    """Nhiễu loạn s (v_scale) trên cùng tập cụm."""
    rows = []
    for s in (5.0, 8.0, 10.0, 12.0, 20.0):
        order = _ranking(events, lab, PriorityParams(v_scale=s))
        tau = _tau_vs_baseline(base_order, order)
        rows.append({
            "v_scale_s": s,
            "kendall_tau_vs_default": round(tau, 4),
            "top3_preserved": set(base_order[:3]) == set(order[:3]),
        })
    return rows


def _match_by_centroid(base_scores, other_scores, max_km=2.0):
    """Khớp cụm giữa hai cấu hình theo trọng tâm gần nhất (<= max_km).

    Trả về danh sách cặp (rank_base, rank_other) cho các cụm khớp được, dùng để
    đo Kendall's tau khi cluster_id không còn tương ứng 1-1 giữa hai cấu hình.
    """
    base_rank = {s.cluster_id: i for i, s in enumerate(base_scores)}
    other_rank = {s.cluster_id: i for i, s in enumerate(other_scores)}
    pairs = []
    used = set()
    for b in base_scores:
        best = None
        best_d = max_km * 1000.0
        for o in other_scores:
            if o.cluster_id in used:
                continue
            d = haversine_m(b.center_lat, b.center_lng, o.center_lat, o.center_lng)
            if d < best_d:
                best_d = d
                best = o
        if best is not None:
            used.add(best.cluster_id)
            pairs.append((base_rank[b.cluster_id], other_rank[best.cluster_id]))
    return pairs


def _stability_structure(events):
    """Nhiễu loạn CẤU TRÚC: đổi sigma_geo -> cụm đổi -> khớp trọng tâm -> tau."""
    def _scores(sigma):
        wp = WeightParams(sigma_geo_m=sigma)
        w = build_weight_matrix(events, wp, mode="gating")
        ws = sparsify(w, wp)
        lab = run_louvain(ws, 1.0, 42)
        return score_clusters(events, lab, C.priority)

    base = _scores(700.0)
    rows = []
    for sigma in (400.0, 550.0, 700.0, 900.0, 1200.0):
        other = _scores(sigma)
        pairs = _match_by_centroid(base, other)
        if len(pairs) >= 2:
            x = [p[0] for p in pairs]
            y = [p[1] for p in pairs]
            tau, _ = kendalltau(x, y)
        else:
            tau = float("nan")
        rows.append({
            "sigma_geo_m": sigma,
            "n_clusters": len(other),
            "n_matched": len(pairs),
            "kendall_tau_matched": round(float(tau), 4),
        })
    return rows


def main():
    events = prepared_events()
    w = build_weight_matrix(events, C.weight, mode="gating")
    ws = sparsify(w, C.weight)
    lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)
    base_order = _ranking(events, lab, C.priority)

    rows_omega = _stability_omega(events, lab, base_order)
    print_table("Ổn định xếp hạng P(C_k) khi omega dao động (Kendall's tau)", rows_omega)
    save_table("exp5_ranking_stability.json", rows_omega)

    rows_s = _stability_v_scale(events, lab, base_order)
    print_table("Ổn định xếp hạng khi s (v_scale) dao động", rows_s)
    save_table("exp5_scale_stability.json", rows_s)

    rows_struct = _stability_structure(events)
    print_table("Ổn định xếp hạng khi CẤU TRÚC cụm đổi (sigma_geo, khớp trọng tâm)", rows_struct)
    save_table("exp5_structural_stability.json", rows_struct)

    print("\n[saved] exp5_ranking_stability.json, exp5_scale_stability.json, "
          "exp5_structural_stability.json -> results/tables/")


if __name__ == "__main__":
    main()
