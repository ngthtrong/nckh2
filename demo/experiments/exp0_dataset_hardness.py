"""Thí nghiệm 0 — KIỂM ĐỘ KHÓ CỦA DATASET (phản biện §3).

Mục đích: chứng minh dataset KHÔNG tự cho phương pháp đề xuất thắng. Đây là câu
trả lời trực tiếp cho §3 ("kết quả do generator quyết định, không do thuật toán")
và là Bảng 2 của bài. Script này chạy TRƯỚC mọi thí nghiệm khác và là một CỬA
CHẶN: nếu một tiêu chí không đạt, dataset chưa đủ khó và mọi kết luận sau đó
không dùng được — phải sửa GENERATOR, không sửa tiêu chí.

Năm tiêu chí nghiệm thu (đặt trước khi xem kết quả phương pháp đề xuất):

  P1.1 — baseline CHỈ dùng toạ độ phải KÉM:
    (1) KMeans(features="geo")           -> ARI < 0.75
    (2) Agglomerative Haversine thuần    -> ARI < 0.75
  P1.1 — ngữ cảnh phải CÓ TÁC DỤNG:
    (3) ablation S_context (gamma=0) làm ARI giảm >= 0.08 VÀ phân hoạch đổi
        (tau Kendall giữa hai nhãn < 1.0, tức không còn bit-identical).
  P1.2 — tin giả phải TRỘN được vào tin thật:
    (4) không đặc trưng đơn nào (n_corrob, has_image) đạt AUC > 0.75;
    (5) tỉ lệ tin giả nằm trong cụm >= 0.55.

Kết quả lưu vào results/tables/exp0_dataset_hardness.json.
"""
from __future__ import annotations

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score, roc_auc_score

from common import prepared_events, print_table, save_table
from pipeline.attributes import haversine_m
from pipeline.baselines import run_kmeans
from pipeline.clustering import run_louvain
from pipeline.config import DEFAULT_CONFIG as C
from pipeline.config import WeightParams
from pipeline.weighting import build_weight_matrix, sparsify

# Ngưỡng nghiệm thu (KHÔNG được nới sau khi xem kết quả).
GEO_ARI_MAX = 0.75          # baseline toạ độ thô phải kém hơn mức này
CTX_ARI_DROP_MIN = 0.08     # bỏ S_context phải làm ARI tụt ít nhất ngần này
SINGLE_FEATURE_AUC_MAX = 0.75  # không đặc trưng đơn nào vượt mức này
FAKE_IN_CLUSTER_MIN = 0.55  # tỉ lệ tin giả nằm trong cụm tối thiểu


def _labeled_idx(events):
    """Chỉ số các sự kiện có nhãn GT (>=0) — dùng để đo ARI."""
    return [i for i, e in enumerate(events) if e.gt_cluster is not None and e.gt_cluster >= 0]


def _ari_on_labeled(events, labels):
    idx = _labeled_idx(events)
    gt = [events[i].gt_cluster for i in idx]
    pred = [labels[i] for i in idx]
    return float(adjusted_rand_score(gt, pred))


def _geo_baselines(events):
    """(1)(2) baseline CHỈ dùng toạ độ: KMeans(geo) và Agglomerative Haversine."""
    idx = _labeled_idx(events)
    n_gt = len({events[i].gt_cluster for i in idx})

    # (1) KMeans trên [lat,lng] chuẩn hoá, đúng số cụm GT (ưu ái baseline hết mức)
    km = run_kmeans(events, n_gt, features="geo")
    ari_km = _ari_on_labeled(events, km)

    # (2) Agglomerative trên ma trận khoảng cách HAVERSINE thuần (mét)
    n = len(events)
    dist = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_m(events[i].lat, events[i].lng,
                            events[j].lat, events[j].lng)
            dist[i, j] = dist[j, i] = d
    agg = AgglomerativeClustering(
        n_clusters=max(1, min(n_gt, n)), metric="precomputed", linkage="average")
    lab_agg = agg.fit_predict(dist).tolist()
    ari_agg = _ari_on_labeled(events, lab_agg)

    return {
        "kmeans_geo_ari": round(ari_km, 4),
        "agglomerative_haversine_ari": round(ari_agg, 4),
        "n_gt_clusters": n_gt,
        "pass_geo_weak": bool(ari_km < GEO_ARI_MAX and ari_agg < GEO_ARI_MAX),
    }


def _context_ablation(events):
    """(3) ablation S_context: gating đầy đủ vs gamma=0. ARI phải tụt + đổi phân hoạch."""
    p_full = C.weight
    w_full = build_weight_matrix(events, p_full, mode="gating")
    lab_full = run_louvain(sparsify(w_full, p_full),
                           C.cluster.resolution, C.cluster.random_state)
    ari_full = _ari_on_labeled(events, lab_full)

    # bỏ ngữ cảnh: gamma=0, dồn trọng số sang thời gian (beta=1) để vẫn là gating hợp lệ
    p_abl = WeightParams(
        sigma_geo_m=p_full.sigma_geo_m, tau_temp_min=p_full.tau_temp_min,
        tau_f=p_full.tau_f, tau_e=p_full.tau_e,
        beta=1.0, gamma=0.0,
        edge_threshold=p_full.edge_threshold, knn=p_full.knn, alpha=p_full.alpha)
    w_abl = build_weight_matrix(events, p_abl, mode="gating")
    lab_abl = run_louvain(sparsify(w_abl, p_abl),
                          C.cluster.resolution, C.cluster.random_state)
    ari_abl = _ari_on_labeled(events, lab_abl)

    drop = ari_full - ari_abl
    # phân hoạch có đổi không? So trên các điểm có nhãn (bit-identical => tau=1.0).
    idx = _labeled_idx(events)
    identical = all(lab_full[i] == lab_abl[i] for i in idx)

    return {
        "ari_full_gating": round(ari_full, 4),
        "ari_context_ablated": round(ari_abl, 4),
        "ari_drop": round(drop, 4),
        "partition_identical": bool(identical),
        "pass_context_matters": bool(drop >= CTX_ARI_DROP_MIN and not identical),
    }


def _single_feature_auc(events):
    """(4) AUC biên của từng đặc trưng đơn dự đoán is_fake. Không cái nào > 0.75."""
    y = np.array([1 if e.is_fake else 0 for e in events])
    if y.sum() == 0 or y.sum() == len(y):
        return {"error": "không có cả hai lớp fake/real"}

    # n_corrob: tin giả TRONG cụm có n_corrob cao như tin thật -> AUC phải yếu.
    # has_image: tin giả có ảnh ~0.45, thật ~0.70 -> chồng lấn, AUC phải yếu.
    n_corrob = np.array([e.n_corrob for e in events], dtype=float)
    has_image = np.array([1.0 if e.has_image else 0.0 for e in events])

    def _auc_abs(score):
        # is_fake=1; đặc trưng có thể dự đoán theo chiều nào cũng được -> lấy
        # max(AUC, 1-AUC) để đo SỨC PHÂN BIỆT tuyệt đối của đặc trưng.
        a = float(roc_auc_score(y, score))
        return max(a, 1.0 - a)

    auc_ncorrob = _auc_abs(n_corrob)
    auc_image = _auc_abs(has_image)
    worst = max(auc_ncorrob, auc_image)
    return {
        "auc_n_corrob": round(auc_ncorrob, 4),
        "auc_has_image": round(auc_image, 4),
        "max_single_feature_auc": round(worst, 4),
        "pass_features_overlap": bool(worst <= SINGLE_FEATURE_AUC_MAX),
    }


def _fake_in_cluster(events):
    """(5) tỉ lệ tin giả nằm trong cụm thật (note fake_in_cluster / fake_campaign)."""
    fakes = [e for e in events if e.is_fake]
    if not fakes:
        return {"error": "không có tin giả"}
    in_cluster = sum(1 for e in fakes
                     if e.note in ("fake_in_cluster", "fake_campaign"))
    frac = in_cluster / len(fakes)
    return {
        "n_fake": len(fakes),
        "n_fake_in_cluster": in_cluster,
        "frac_fake_in_cluster": round(frac, 3),
        "pass_fake_mixed": bool(frac >= FAKE_IN_CLUSTER_MIN),
    }


def main():
    events = prepared_events()

    geo = _geo_baselines(events)
    ctx = _context_ablation(events)
    feat = _single_feature_auc(events)
    fake = _fake_in_cluster(events)

    print_table("P1.1 — baseline CHỈ toạ độ phải KÉM (ARI < 0.75)", [geo])
    print_table("P1.1 — S_context phải CÓ TÁC DỤNG (ARI drop >= 0.08, phân hoạch đổi)", [ctx])
    print_table("P1.2 — không đặc trưng đơn nào tách tin giả (AUC <= 0.75)", [feat])
    print_table("P1.2 — tin giả trộn vào tin thật (>= 0.55 trong cụm)", [fake])

    checks = {
        "geo_weak": geo["pass_geo_weak"],
        "context_matters": ctx["pass_context_matters"],
        "features_overlap": feat.get("pass_features_overlap", False),
        "fake_mixed": fake.get("pass_fake_mixed", False),
    }
    all_pass = all(checks.values())

    print("\n=== TỔNG KẾT 5 TIÊU CHÍ NGHIỆM THU ===")
    for k, v in checks.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print(f"\n{'✓ DATASET ĐẠT ĐỘ KHÓ' if all_pass else '✗ DATASET CHƯA ĐỦ KHÓ — sửa generator, KHÔNG sửa tiêu chí'}")

    out = {
        "geo_baselines": geo,
        "context_ablation": ctx,
        "single_feature_auc": feat,
        "fake_in_cluster": fake,
        "all_criteria_pass": bool(all_pass),
        "thresholds": {
            "geo_ari_max": GEO_ARI_MAX,
            "ctx_ari_drop_min": CTX_ARI_DROP_MIN,
            "single_feature_auc_max": SINGLE_FEATURE_AUC_MAX,
            "fake_in_cluster_min": FAKE_IN_CLUSTER_MIN,
        },
    }
    save_table("exp0_dataset_hardness.json", [out])
    print("\n[saved] exp0_dataset_hardness.json -> results/tables/")
    return all_pass


if __name__ == "__main__":
    main()
