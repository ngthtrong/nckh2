"""Thí nghiệm 4 — Đối chiếu Louvain/Leiden với baseline (Mục 2.4).

K-Means (cần biết trước K) và DBSCAN (nhạy tham số) chạy trên cùng dữ liệu.
So sánh ARI/NMI và độ gắn kết địa lý để làm nổi bật ưu thế của phát hiện
cộng đồng trên đồ thị trọng số không gian-ngữ nghĩa.
"""
from __future__ import annotations

from common import prepared_events, print_table, save_table
from pipeline.baselines import (
    run_agglomerative_on_graph,
    run_dbscan,
    run_hdbscan_on_graph,
    run_kmeans,
    run_spectral,
)
from pipeline.config import WeightParams
from pipeline.clustering import run_leiden, run_louvain
from pipeline.metrics import cluster_quality, geographic_spread
from pipeline.weighting import build_weight_matrix, sparsify


def main():
    events = prepared_events()
    gt = [e.gt_cluster for e in events]
    n_gt = len({g for g in gt if g >= 0})

    wp = WeightParams()
    w = build_weight_matrix(events, wp, mode="gating")
    ws = sparsify(w, wp)

    # Số cụm Louvain tìm được — dùng làm K cho các baseline cần biết trước K,
    # để so sánh công bằng trên cùng độ phân giải.
    lou = run_louvain(ws, 1.0, 42)
    k_lou = len(set(lou))

    methods = {
        "Louvain (gating graph)": lou,
        "Leiden (gating graph)": run_leiden(ws, 1.0, 42),
        # --- baseline CÔNG BẰNG: chạy trên CÙNG đồ thị/khoảng cách gating ---
        f"Spectral (affinity gating, K={k_lou})": run_spectral(ws, k_lou),
        f"Spectral (affinity gating, K={n_gt} true GT labels)": run_spectral(ws, n_gt),
        "HDBSCAN (dist=1-w gating)": run_hdbscan_on_graph(ws, min_cluster_size=3),
        f"Agglomerative (dist=1-w, K={k_lou})": run_agglomerative_on_graph(ws, k_lou),
        # --- baseline hình học thuần túy trên tọa độ thô (đối chiếu) ---
        f"K-Means (K={n_gt}, correct K, coords)": run_kmeans(events, n_gt),
        "K-Means (K=3, wrong K, coords)": run_kmeans(events, 3),
        "DBSCAN (eps=0.3, coords)": run_dbscan(events, eps=0.3, min_samples=3),
        "DBSCAN (eps=0.6, coords)": run_dbscan(events, eps=0.6, min_samples=3),
    }

    rows = []
    for name, lab in methods.items():
        q = cluster_quality(lab, gt)
        sp = geographic_spread(events, lab)
        fair = any(t in name for t in ("gating", "dist=1-w", "affinity"))
        rows.append({
            "method": name,
            "n_clusters": sp["n_clusters"],
            "ari": q["ari"],
            "nmi": q["nmi"],
            "mean_diam_km": sp["mean_diameter_km"],
            "max_diam_km": sp["max_diameter_km"],
            "needs_preset_k": ("K-Means" in name or "K=" in name),
            "same_graph_as_ours": fair,
        })

    print_table(f"Baseline comparison (ground-truth clusters = {n_gt}, Louvain K = {k_lou})", rows)
    save_table("exp4_baselines.json", rows)
    print("\n[saved] exp4_baselines.json -> results/tables/")


if __name__ == "__main__":
    main()
