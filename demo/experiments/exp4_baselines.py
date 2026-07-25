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
from pipeline.metrics import cluster_quality, geographic_spread, noise_handling, noise_handling
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

    # Khai TƯỜNG MINH ba thuộc tính của từng baseline thay vì suy từ tên hiển thị:
    #   needs_k    : có phải cấp trước số cụm K?
    #   same_graph : có chạy trên CÙNG ma trận trọng số gating như phương pháp đề xuất?
    #   noise_label: nhãn "không thuộc cụm nào" (-1 với DBSCAN/HDBSCAN, None nếu
    #                thuật toán gán mọi điểm vào một cụm thật). Tham số này quyết định
    #                metrics có coi thùng nhiễu là một cụm hay không — xem metrics.py.
    methods = {
        "Louvain (gating graph)": (lou, False, True, None),
        "Leiden (gating graph)": (run_leiden(ws, 1.0, 42), False, True, None),
        # --- baseline CÔNG BẰNG: chạy trên CÙNG đồ thị/khoảng cách gating ---
        f"Spectral (affinity gating, K={k_lou} = Louvain's discovered K)":
            (run_spectral(ws, k_lou), True, True, None),
        f"Spectral (affinity gating, K={n_gt} true GT labels)":
            (run_spectral(ws, n_gt), True, True, None),
        "HDBSCAN (dist=1-w gating)":
            (run_hdbscan_on_graph(ws, min_cluster_size=3), False, True, -1),
        f"Agglomerative (dist=1-w, K={k_lou} = Louvain's discovered K)":
            (run_agglomerative_on_graph(ws, k_lou), True, True, None),
        # --- baseline hình học THUẦN TOẠ ĐỘ: chỉ [lat, lng] ---
        f"K-Means (K={n_gt}, coords only)":
            (run_kmeans(events, n_gt, features="geo"), True, False, None),
        "DBSCAN (eps=0.3, coords only)":
            (run_dbscan(events, eps=0.3, min_samples=3, features="geo"), False, False, -1),
        # --- baseline Euclid có nối thêm chiều ngữ cảnh: [lat, lng, F, E] ---
        f"K-Means (K={n_gt}, coords+F,E)":
            (run_kmeans(events, n_gt, features="geo_context"), True, False, None),
        "K-Means (K=3, wrong K, coords+F,E)":
            (run_kmeans(events, 3, features="geo_context"), True, False, None),
        "DBSCAN (eps=0.3, coords+F,E)":
            (run_dbscan(events, eps=0.3, min_samples=3, features="geo_context"), False, False, -1),
        "DBSCAN (eps=0.6, coords+F,E)":
            (run_dbscan(events, eps=0.6, min_samples=3, features="geo_context"), False, False, -1),
    }

    rows = []
    for name, (lab, needs_k, same_graph, noise_label) in methods.items():
        q = cluster_quality(lab, gt)
        sp = geographic_spread(events, lab, noise_label=noise_label)
        nz = noise_handling(lab, gt, noise_label=noise_label)
        rows.append({
            "method": name,
            "n_clusters": sp["n_clusters"],
            "ari": q["ari"],
            "nmi": q["nmi"],
            "mean_diam_km_multi": sp["mean_diameter_km_multi"],
            "max_diam_km": sp["max_diameter_km"],
            "noise_absorbed_pct": nz["noise_absorbed_pct"],
            "contaminated_clusters": nz["contaminated_clusters"],
            "n_unclustered": nz["n_unclustered"],
            "labeled_dropped_to_noise": nz["labeled_dropped_to_noise"],
            "n_singletons": sp["n_singletons"],
            "mean_diam_km_all": sp["mean_diameter_km"],
            "needs_preset_k": needs_k,
            "same_graph_as_ours": same_graph,
        })

    print_table(f"Baseline comparison (ground-truth clusters = {n_gt}, Louvain K = {k_lou})", rows)
    print("\nSo sánh đường kính phải dùng mean_diam_km_multi (cụm >= 2 thành viên) hoặc")
    print("max_diam_km; mean_diam_km_all tính cả singleton = 0 km nên thưởng giả tạo cho")
    print("phân hoạch vụn (phản biện 1.3). Cột same_graph_as_ours = True là baseline công")
    print("bằng: cùng ma trận trọng số gating, chỉ khác thuật toán phân hoạch.")
    print("\nĐỌC ARI CÙNG VỚI noise_absorbed_pct: ARI/NMI chỉ chấm trên điểm có nhãn")
    print("(gt >= 0) nên một phương pháp hút hết điểm nhiễu vào cụm thật vẫn có thể đạt")
    print("ARI = 1,0 trong khi kéo giãn cụm tới hàng chục km — ưu thế đó là giả về mặt")
    print("vận hành. Phương pháp tốt phải đồng thời: ARI cao, đường kính nhỏ, và")
    print("noise_absorbed_pct thấp.")
    save_table("exp4_baselines.json", rows)
    print("\n[saved] exp4_baselines.json -> results/tables/")


if __name__ == "__main__":
    main()
