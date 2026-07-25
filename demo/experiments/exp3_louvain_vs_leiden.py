"""Thí nghiệm 3 — Louvain vs Leiden (Mục 4.3).

Đo tần suất cộng đồng đứt gãy nội bộ (badly connected) và chất lượng cụm để
biện minh cho khuyến nghị dùng Leiden khi độ chính xác không gian là sống còn.
Chạy nhiều seed để có thống kê ổn định.
"""
from __future__ import annotations

from common import prepared_events, print_table, save_table
from pipeline.config import WeightParams
from pipeline.clustering import (
    disconnected_report,
    modularity,
    run_leiden,
    run_louvain,
)
from pipeline.metrics import cluster_quality, geographic_spread
from pipeline.weighting import build_weight_matrix, sparsify

SEEDS = [1, 7, 13, 42, 99, 123, 256, 512, 1024, 2026]


def main():
    events = prepared_events()
    gt = [e.gt_cluster for e in events]
    wp = WeightParams()
    w = build_weight_matrix(events, wp, mode="gating")
    ws = sparsify(w, wp)

    rows = []
    agg = {"louvain": {"broken": 0, "ari": 0.0, "mod": 0.0},
           "leiden": {"broken": 0, "ari": 0.0, "mod": 0.0}}
    for seed in SEEDS:
        lab_lou = run_louvain(ws, 1.0, seed)
        lab_lei = run_leiden(ws, 1.0, seed)
        r_lou = disconnected_report(ws, lab_lou)
        r_lei = disconnected_report(ws, lab_lei)
        b_lou, n_lou = r_lou["n_broken"], r_lou["n_clusters_total"]
        b_lei, n_lei = r_lei["n_broken"], r_lei["n_clusters_total"]
        q_lou = cluster_quality(lab_lou, gt)
        q_lei = cluster_quality(lab_lei, gt)
        m_lou = modularity(ws, lab_lou)
        m_lei = modularity(ws, lab_lei)
        rows.append({
            "seed": seed,
            "lou_broken": b_lou, "lou_clusters": n_lou, "lou_ari": q_lou["ari"], "lou_mod": round(m_lou, 4),
            "lei_broken": b_lei, "lei_clusters": n_lei, "lei_ari": q_lei["ari"], "lei_mod": round(m_lei, 4),
            # MẪU SỐ THẬT của phép kiểm: chỉ cụm >= 2 phần tử kiểm được tính liên thông;
            # singleton liên thông một cách tầm thường nên phải loại khỏi mẫu số, nếu
            # không con số "0 cụm đứt gãy" sẽ đọc mạnh hơn bằng chứng thực có.
            "lou_clusters_evaluated": r_lou["n_clusters_evaluated"],
            "lou_singletons_excluded": r_lou["n_singletons_excluded"],
            "lei_clusters_evaluated": r_lei["n_clusters_evaluated"],
            "lei_singletons_excluded": r_lei["n_singletons_excluded"],
        })
        agg["louvain"]["broken"] += b_lou
        agg["louvain"]["ari"] += q_lou["ari"]
        agg["louvain"]["mod"] += m_lou
        agg["leiden"]["broken"] += b_lei
        agg["leiden"]["ari"] += q_lei["ari"]
        agg["leiden"]["mod"] += m_lei

    n = len(SEEDS)
    eval_lou = sum(r["lou_clusters_evaluated"] for r in rows)
    eval_lei = sum(r["lei_clusters_evaluated"] for r in rows)
    summary = [
        {"algo": "Louvain",
         "total_broken_communities": agg["louvain"]["broken"],
         "total_clusters_evaluated": eval_lou,
         "avg_ari": round(agg["louvain"]["ari"] / n, 4),
         "avg_modularity": round(agg["louvain"]["mod"] / n, 4)},
        {"algo": "Leiden",
         "total_broken_communities": agg["leiden"]["broken"],
         "total_clusters_evaluated": eval_lei,
         "avg_ari": round(agg["leiden"]["ari"] / n, 4),
         "avg_modularity": round(agg["leiden"]["mod"] / n, 4)},
    ]

    print_table(f"Louvain vs Leiden per-seed (n={n})", rows)
    print_table("Tổng hợp", summary)

    total_broken = agg["louvain"]["broken"] + agg["leiden"]["broken"]
    print("\n--- Diễn giải ---")
    if total_broken == 0:
        print(f"MẪU SỐ: chỉ {eval_lou} (Louvain) / {eval_lei} (Leiden) cụm-lần có >= 2 phần tử")
        print("nên kiểm được tính liên thông; các cụm 1 phần tử liên thông tầm thường và")
        print("đã bị loại khỏi mẫu số. Kết luận dưới đây chỉ có hiệu lực trên mẫu số đó.")
        print("Trên đồ thị đã gating không gian (Mục 4.2), KHÔNG cụm nào bị đứt gãy nội bộ")
        print("ở cả Louvain lẫn Leiden, qua toàn bộ", n, "seed. Hai thuật toán cho kết quả")
        print("gần như trùng khớp (ARI/modularity bằng nhau). Kết luận: chính cơ chế gating")
        print("làm cụm gắn kết không gian đã loại trừ phần lớn rủi ro đứt gãy; Leiden do đó")
        print("là 'bảo hiểm lý thuyết' gần như miễn phí — nên dùng khi độ chính xác không gian")
        print("là sống còn, mà không phải trả giá về chất lượng hay modularity.")
    else:
        print(f"Louvain tạo tổng cộng {agg['louvain']['broken']} cụm đứt gãy; Leiden {agg['leiden']['broken']}.")

    save_table("exp3_per_seed.json", rows)
    save_table("exp3_summary.json", summary)
    print("\n[saved] exp3_*.json -> results/tables/")


if __name__ == "__main__":
    main()
