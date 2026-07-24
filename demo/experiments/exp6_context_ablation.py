"""Thí nghiệm 6 — Ablation circularity giữa S_context và ranking (phản biện 1.1).

Phản biện: F, E vừa quyết định gom cụm (qua S_context) vừa quyết định thứ hạng
(qua F_max, E_agg). Điểm ưu tiên P có thể chỉ 'đọc lại' cấu trúc mà chính nó tạo ra.

Câu hỏi định lượng: nếu gom cụm CHỈ bằng không gian-thời gian (bỏ S_context khỏi
đồ thị), rồi vẫn tính P như cũ, thứ hạng có đổi nhiều không?
  - tau cao  => S_context đóng góp ÍT cho *ranking* (chủ yếu giúp *gom cụm*).
  - tau thấp => cần lập luận vì sao ranking mới đúng hơn.

Bỏ S_context mà giữ gating: đặt gamma=0 -> w_ij = S_geo * (beta*S_temp).
"""
from __future__ import annotations

from scipy.stats import kendalltau

from common import prepared_events, print_table, save_table
from pipeline.config import DEFAULT_CONFIG as C
from pipeline.config import WeightParams
from pipeline.clustering import run_louvain
from pipeline.metrics import cluster_quality, geographic_spread
from pipeline.priority import score_clusters
from pipeline.weighting import build_weight_matrix, sparsify


def _cluster_of_event(events, labels, eid):
    idx = {e.event_id: i for i, e in enumerate(events)}
    return labels[idx[eid]] if eid in idx else None


def _priority_by_centroid(events, labels, params):
    """Trả về danh sách (center_lat, center_lng, priority) theo thứ hạng P giảm dần.

    Dùng trọng tâm không gian để so khớp cụm giữa hai lần gom cụm khác nhau
    (số cụm / id cụm không nhất thiết trùng nhau)."""
    scores = score_clusters(events, labels, params)
    return [(s.center_lat, s.center_lng, s.priority, s.cluster_id) for s in scores]


def _match_rankings_by_centroid(rank_full, rank_ablate, max_km=1.0):
    """Ghép cụm giữa hai bảng theo trọng tâm gần nhất (<= max_km), rồi trả về
    hai danh sách hạng (rank position) trên tập cụm ghép được."""
    from pipeline.attributes import haversine_m

    # rank position trong mỗi bảng (0 = ưu tiên cao nhất)
    pos_full = {c[3]: i for i, c in enumerate(rank_full)}
    pos_abl = {c[3]: i for i, c in enumerate(rank_ablate)}

    matched_full_pos, matched_abl_pos = [], []
    used_abl = set()
    for cf in rank_full:
        best_j, best_d = None, 1e18
        for j, ca in enumerate(rank_ablate):
            if ca[3] in used_abl:
                continue
            d = haversine_m(cf[0], cf[1], ca[0], ca[1]) / 1000.0
            if d < best_d:
                best_d, best_j = d, j
        if best_j is not None and best_d <= max_km:
            ca = rank_ablate[best_j]
            used_abl.add(ca[3])
            matched_full_pos.append(pos_full[cf[3]])
            matched_abl_pos.append(pos_abl[ca[3]])
    return matched_full_pos, matched_abl_pos


def main():
    events = prepared_events()
    gt = [e.gt_cluster for e in events]

    # (i) đồ thị đầy đủ: S_geo * (beta*S_temp + gamma*S_context)
    p_full = C.weight
    w_full = build_weight_matrix(events, p_full, mode="gating")
    ws_full = sparsify(w_full, p_full)
    lab_full = run_louvain(ws_full, C.cluster.resolution, C.cluster.random_state)

    # (ii) đồ thị bỏ context: gamma=0 -> S_geo * beta*S_temp
    p_abl = WeightParams(
        sigma_geo_m=p_full.sigma_geo_m,
        tau_temp_min=p_full.tau_temp_min,
        tau_f=p_full.tau_f,
        tau_e=p_full.tau_e,
        beta=p_full.beta,
        gamma=0.0,
        edge_threshold=p_full.edge_threshold,
        knn=p_full.knn,
    )
    w_abl = build_weight_matrix(events, p_abl, mode="gating")
    ws_abl = sparsify(w_abl, p_abl)
    lab_abl = run_louvain(ws_abl, C.cluster.resolution, C.cluster.random_state)

    q_full = cluster_quality(lab_full, gt)
    q_abl = cluster_quality(lab_abl, gt)
    sp_full = geographic_spread(events, lab_full)
    sp_abl = geographic_spread(events, lab_abl)

    # Xếp hạng P trên mỗi đồ thị
    rank_full = _priority_by_centroid(events, lab_full, C.priority)
    rank_abl = _priority_by_centroid(events, lab_abl, C.priority)

    # Ghép cụm theo trọng tâm rồi đo Kendall's tau giữa hai thứ hạng
    xf, xa = _match_rankings_by_centroid(rank_full, rank_abl, max_km=1.0)
    if len(xf) >= 2:
        tau, _ = kendalltau(xf, xa)
        tau = round(float(tau), 4)
    else:
        tau = None

    # Top-5 cụm ưu tiên cao nhất có khớp không (theo trọng tâm)
    from pipeline.attributes import haversine_m
    top_full = rank_full[:5]
    top_abl_centroids = [(c[0], c[1]) for c in rank_abl[:5]]
    top5_overlap = 0
    for cf in top_full:
        if any(haversine_m(cf[0], cf[1], la, lo) / 1000.0 <= 1.0
               for la, lo in top_abl_centroids):
            top5_overlap += 1

    summary = {
        "graph_full_ari": q_full["ari"],
        "graph_full_nmi": q_full["nmi"],
        "graph_full_n_clusters": sp_full["n_clusters"],
        "graph_full_mean_diam_km": sp_full["mean_diameter_km"],
        "graph_ablate_ari": q_abl["ari"],
        "graph_ablate_nmi": q_abl["nmi"],
        "graph_ablate_n_clusters": sp_abl["n_clusters"],
        "graph_ablate_mean_diam_km": sp_abl["mean_diameter_km"],
        "n_matched_clusters": len(xf),
        "kendall_tau_ranking": tau,
        "top5_matched_by_centroid": top5_overlap,
    }
    print_table("Exp6 — Ablation circularity: S_context bỏ khỏi gom cụm", [summary])
    interp = (
        "tau cao => S_context đóng góp ít cho RANKING (chủ yếu giúp gom cụm); "
        "tau thấp => ranking đổi nhiều, cần lập luận hướng đổi tốt hơn."
    )
    print(f"\nDiễn giải: {interp}")

    save_table("exp6_context_ablation.json", [summary])
    print("\n[saved] exp6_context_ablation.json -> results/tables/")


if __name__ == "__main__":
    main()
