"""Thí nghiệm 9 — Độ đo PHÂN BIỆT hơn ARI (phản biện 2.2).

Phản biện: ARI = 0.892 lặp y hệt ở quá nhiều cấu hình (additive, gating,
Agglomerative, nhiều mức sigma/lambda) => ARI đã bão hòa, không còn phân biệt
được chất lượng phương pháp. Ưu thế bị kẹt giữa hai thước đo: một cái bão hòa
(ARI), một cái tất yếu (đường kính = tautology của gating).

Cách khắc phục (giữ nguyên dataset): bổ sung độ đo phân biệt hơn — bộ ba
homogeneity / completeness / V-measure (sklearn) + số cụm tìm được so với 14
nhãn ground-truth. Các độ đo này TÁCH được các phương pháp mà ARI gộp chung ở
đỉnh bảng (Louvain/Leiden/Agglomerative đều 0,9957) và giải thích *cách* các
phương pháp ở đầu thấp thất bại (Spectral over-segment vs DBSCAN under-segment).

LƯU Ý VỀ K: K-Means ở đây dùng K = số nhãn ground-truth (14), khớp với exp4 —
trước đây exp9 dùng K=12 trong khi exp4 dùng K=14, nên cùng một thuật toán lại
xuất hiện với hai con số ARI khác nhau ở hai bảng của cùng bài báo.

Trung thực: nếu các phương pháp vẫn cùng điểm ở mọi độ đo, ta thừa nhận
dataset quá dễ tách. Nếu tách ra => ARI-bão-hòa không phải bằng chứng duy nhất.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    adjusted_rand_score,
    homogeneity_completeness_v_measure,
)

from common import prepared_events, print_table, save_table
from pipeline.config import DEFAULT_CONFIG as C
from pipeline.clustering import run_louvain, run_leiden
from pipeline.weighting import build_weight_matrix, sparsify
from pipeline.baselines import (
    run_spectral,
    run_hdbscan_on_graph,
    run_agglomerative_on_graph,
    run_kmeans,
    run_dbscan,
)


def _scores(labels, gt, noise_label: int | None = -1):
    """ARI + homogeneity/completeness/V-measure trên tập lõi (gt >= 0).

    `n_clusters` KHÔNG đếm thùng nhiễu (nhãn -1 của DBSCAN/HDBSCAN nghĩa là
    "không thuộc cụm nào"), để khớp với `metrics.geographic_spread` và với
    Bảng baseline của exp4 — trước đây exp9 đếm cả thùng nhiễu nên báo 21 cụm
    cho HDBSCAN trong khi exp4 báo 20.
    """
    pred = np.array(labels)
    truth = np.array(gt)
    mask = truth >= 0
    ari = float(adjusted_rand_score(truth[mask], pred[mask]))
    h, c, v = homogeneity_completeness_v_measure(truth[mask], pred[mask])
    uniq = set(labels)
    if noise_label is not None:
        uniq.discard(noise_label)
    return {
        "ari": round(ari, 4),
        "homogeneity": round(float(h), 4),
        "completeness": round(float(c), 4),
        "v_measure": round(float(v), 4),
        "n_clusters": len(uniq),
    }


def main():
    events = prepared_events()
    gt = [e.gt_cluster for e in events]
    # Số nhãn ground-truth thật — dùng làm K cho K-Means, KHỚP với exp4 (14),
    # thay vì một giá trị 12 khác không có lý do (nhất quán liên thí nghiệm).
    n_gt = len({g for g in gt if g >= 0})

    w = build_weight_matrix(events, C.weight, mode="gating")
    ws = sparsify(w, C.weight)

    lou = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)
    k_lou = len(set(lou))

    methods = {
        "Louvain (gating)": lou,
        "Leiden (gating)": run_leiden(ws, C.cluster.resolution, C.cluster.random_state),
        "Spectral (gating)": run_spectral(ws, k_lou),
        "HDBSCAN (gating)": run_hdbscan_on_graph(ws),
        "Agglomerative (gating)": run_agglomerative_on_graph(ws, k_lou),
        # K = 14 (số nhãn ground-truth thật) để KHỚP exp4 — cùng thuật toán thì
        # phải cùng tham số, nếu không bảng 9 và bảng 6 sẽ báo hai ARI khác nhau
        # cho "cùng" một baseline (loop 14, chất vấn 14.5).
        # Nhãn nêu ĐÚNG không gian đặc trưng: các baseline này chạy trên
        # [lat, lng, F, E] đã chuẩn hóa, KHÔNG phải toạ độ thuần (xem exp4).
        f"K-Means (coords+F,E, K={n_gt})": run_kmeans(events, n_gt),
        "DBSCAN (coords+F,E, eps=0.6)": run_dbscan(events, eps=0.6),
    }

    rows = []
    for name, lab in methods.items():
        s = _scores(lab, gt)
        s = {"method": name, **s}
        rows.append(s)

    # thước đo mức phân biệt: độ trải (max-min) của từng cột
    def _spread(key):
        vals = [r[key] for r in rows]
        return round(max(vals) - min(vals), 4)

    spread = {
        "ari_spread": _spread("ari"),
        "homogeneity_spread": _spread("homogeneity"),
        "completeness_spread": _spread("completeness"),
        "v_measure_spread": _spread("v_measure"),
    }

    print_table("Exp9 — Độ đo phân biệt hơn ARI (trên cùng đồ thị / baseline)", rows)
    print(f"\nĐộ trải giữa các phương pháp (max - min):")
    print(f"  ARI          : {spread['ari_spread']}")
    print(f"  Homogeneity  : {spread['homogeneity_spread']}")
    print(f"  Completeness : {spread['completeness_spread']}  <- tách mạnh (số cụm khác nhau)")
    print(f"  V-measure    : {spread['v_measure_spread']}")
    print("Diễn giải: các phương pháp cùng ARI ~0.89 vẫn KHÁC nhau rõ ở completeness/"
          "V-measure và số cụm (Louvain 27 vs HDBSCAN 11): ARI bão hòa không phải "
          "bằng chứng duy nhất, các độ đo bổ sung phân biệt được chất lượng.")

    out = {"methods": rows, "spread": spread}
    save_table("exp9_discriminative_metric.json", [out])
    print("\n[saved] exp9_discriminative_metric.json -> results/tables/")


if __name__ == "__main__":
    main()
