"""Thí nghiệm 1 — Kiểm chứng 4 fix của Mục 4.

A. w_ij: cộng (quét alpha) vs nhân/gating -> đường kính địa lý cụm (S1: hai NHÓM xa
   nhau nhưng cùng ngữ cảnh). Quét alpha để dạng cộng không bị dựng thành người rơm.
B. P(C_k): chuẩn hóa vs không  -> chứng minh N_total áp đảo khi không chuẩn hóa.
C. V_agg: nhân vs cộng          -> chứng minh 'khuếch đại' chỉ đúng khi nhân (S2);
   so trên thang đã chuẩn hoá để hai dạng cùng miền giá trị.
D. tanh bão hòa: có/không s     -> khả năng phân biệt cụm ít vs nhiều đối tượng yếu thế.
E. gate C_i cho N_total         -> tin giả S3 bị hạ nhiệt.
F. gate C_i cho F_max           -> tin giả khai ngập cao không chiếm trọn F_max.
G. Phân rã ARI                  -> BẤT BIẾN dữ liệu: nhãn kịch bản phải khả tách
   bằng không gian (không nhóm nào trùng tâm ốc đảo), tức trần ARI không bị ghim
   bởi thiết kế dữ liệu.
"""
from __future__ import annotations

import math

from common import prepared_events, print_table, save_table
from pipeline.config import DEFAULT_CONFIG as C
from pipeline.clustering import run_louvain
from pipeline.metrics import cluster_quality, geographic_spread
from pipeline.priority import score_clusters
from pipeline.weighting import build_weight_matrix, sparsify


def exp_a_gating_vs_additive(events):
    """Dạng CỘNG vs NHÂN, quét alpha để loại bỏ nghi vấn 'người rơm'.

    Phản biện 2.1: bản trước cố định alpha = 0,34 trong khi beta = gamma = 0,5,
    tức dạng cộng bị cho ít trọng số không gian hơn hai thành phần kia — thua là
    tất yếu. Ở đây ta quét alpha ∈ {0,34; 0,5; 1,0} và thêm biến thể chuẩn hoá
    1/3 (alpha = beta = gamma = 1/3, tổng = 1) để dạng cộng được đặt ở điều kiện
    THUẬN LỢI NHẤT của nó. Nếu gating vẫn thắng ở mọi alpha thì kết luận mới
    vững; nếu không, phải báo cáo đúng như vậy.

    Cột so sánh chính là `max_diam_km` và `mean_diam_km_multi`: `mean_diam_km`
    tính cả singleton (đường kính 0) nên thưởng giả tạo cho phân hoạch vụn.
    """
    gt = [e.gt_cluster for e in events]
    variants = [
        ("additive (alpha=0.34)", "additive", 0.34),
        ("additive (alpha=0.5 = beta = gamma)", "additive", 0.5),
        ("additive (alpha=1.0)", "additive", 1.0),
        ("additive (chuẩn hoá 1/3)", "additive_norm", None),
        ("gating (nhân, đề xuất)", "gating", None),
    ]
    rows = []
    for label, mode, alpha in variants:
        w = build_weight_matrix(events, C.weight, mode=mode, alpha=alpha)
        ws = sparsify(w, C.weight)
        lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)
        q = cluster_quality(lab, gt)
        spread = geographic_spread(events, lab)
        rows.append({
            "variant": label,
            "ari": q["ari"],
            "nmi": q["nmi"],
            "mean_diam_km_multi": spread["mean_diameter_km_multi"],
            "max_diam_km": spread["max_diameter_km"],
            "mean_diam_km_all": spread["mean_diameter_km"],
            "n_clusters": spread["n_clusters"],
            "n_singletons": spread["n_singletons"],
            "s1_merged": _s1_same_cluster(events, mode, alpha),
        })
    return rows


def _s1_same_cluster(events, mode, alpha=None):
    """Nhóm S1_A (Huế) và S1_B (Hội An, xa ~107km) có bị gom chung cụm không?"""
    w = build_weight_matrix(events, C.weight, mode=mode, alpha=alpha)
    ws = sparsify(w, C.weight)
    lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)
    idx = {e.event_id: i for i, e in enumerate(events)}
    a, b = idx.get("S1_A_0"), idx.get("S1_B_0")
    if a is None or b is None:
        return None
    return lab[a] == lab[b]


def exp_b_normalization(events):
    """So sánh P(C_k) khi CÓ và KHÔNG chuẩn hóa dân số."""
    w = build_weight_matrix(events, C.weight, mode="gating")
    ws = sparsify(w, C.weight)
    lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)

    # Bản chuẩn hóa (đúng)
    sc_norm = score_clusters(events, lab, C.priority)
    # Bản KHÔNG chuẩn hóa: mô phỏng bằng cách tính core thô = wE*E + wF*F + wN*(sumN)
    groups = {}
    for e, l in zip(events, lab):
        groups.setdefault(l, []).append(e)
    raw_rows = []
    for cid, mem in groups.items():
        e_agg = sum(x.urgency * x.confidence for x in mem) / len(mem)
        f_max = max(x.flood for x in mem)
        n_raw = sum(x.n_trapped for x in mem)
        core_unnorm = C.priority.omega_e * e_agg + C.priority.omega_f * f_max + C.priority.omega_n * n_raw
        raw_rows.append((cid, core_unnorm, n_raw, e_agg, f_max))
    raw_rows.sort(key=lambda r: r[1], reverse=True)

    # Tương quan giữa thứ hạng KHÔNG chuẩn hóa và dân số thô (nếu ~1.0 => bị áp đảo)
    top_unnorm = raw_rows[0]
    n_values = [r[2] for r in raw_rows]
    top_is_largest_pop = top_unnorm[2] == max(n_values)

    return {
        "norm_top_cluster": sc_norm[0].cluster_id,
        "norm_top_priority": sc_norm[0].priority,
        "norm_top_core": sc_norm[0].core,
        "unnorm_top_cluster": top_unnorm[0],
        "unnorm_top_core_value": round(top_unnorm[1], 2),
        "unnorm_top_pop": round(top_unnorm[2], 1),
        "unnorm_dominated_by_population": top_is_largest_pop,
    }


def exp_c_v_multiplier(events):
    """S2 (cụm nhiều đối tượng yếu thế): V nhân đẩy ưu tiên bao nhiêu so với cộng?

    Phản biện 2.5: P_multiply và P_add có MIỀN GIÁ TRỊ khác nhau (nhân với V_agg
    ∈ [1, 2) vs cộng thêm một offset), nên so trực tiếp hai con số là so hai
    thang đo. Điều duy nhất so được — và cũng là điều bài báo tuyên bố — là THỨ
    HẠNG. Vì vậy ta thêm cột hạng của mỗi cụm theo từng dạng, cùng thang chuẩn
    hoá min-max để đọc được khoảng cách tương đối trong cùng một dạng.
    """
    w = build_weight_matrix(events, C.weight, mode="gating")
    ws = sparsify(w, C.weight)
    lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)

    sc_mult = {s.cluster_id: s for s in score_clusters(events, lab, C.priority, normalize_v=True)}
    sc_add = {s.cluster_id: s for s in score_clusters(events, lab, C.priority, normalize_v=False)}

    # tìm cụm chứa S2
    idx = {e.event_id: i for i, e in enumerate(events)}
    s2_cluster = lab[idx["S2_0"]] if "S2_0" in idx else None

    # hạng (0 = ưu tiên cao nhất) theo từng dạng
    rank_mult = {cid: i for i, cid in enumerate(
        sorted(sc_mult, key=lambda c: sc_mult[c].priority, reverse=True))}
    rank_add = {cid: i for i, cid in enumerate(
        sorted(sc_add, key=lambda c: sc_add[c].priority, reverse=True))}

    def _minmax(vals):
        lo, hi = min(vals), max(vals)
        span = hi - lo
        return (lambda x: round((x - lo) / span, 4)) if span > 0 else (lambda x: 0.0)

    norm_mult = _minmax([s.priority for s in sc_mult.values()])
    norm_add = _minmax([s.priority for s in sc_add.values()])

    rows = []
    for cid in sc_mult:
        m, a = sc_mult[cid], sc_add[cid]
        rows.append({
            "cluster": cid,
            "is_S2": cid == s2_cluster,
            "v_agg": m.v_agg,
            "core": m.core,
            "P_multiply": m.priority,
            "P_add": a.priority,
            "P_multiply_norm": norm_mult(m.priority),
            "P_add_norm": norm_add(a.priority),
            "rank_multiply": rank_mult[cid],
            "rank_add": rank_add[cid],
            "rank_shift": rank_add[cid] - rank_mult[cid],
        })
    rows.sort(key=lambda r: r["P_multiply"], reverse=True)
    return rows, s2_cluster


def exp_d_tanh_saturation():
    """Khả năng phân biệt cụm 1 vs 3 vs 10 vs 50 người yếu thế, có/không hệ số s."""
    rows = []
    for v_sum in (1, 3, 10, 30, 50):
        no_scale = 1 + math.tanh(v_sum)
        with_scale = 1 + math.tanh(v_sum / C.priority.v_scale)
        rows.append({
            "sum_V": v_sum,
            "V_agg_no_scale(tanh(V))": round(no_scale, 4),
            f"V_agg_with_s={C.priority.v_scale:.0f}": round(with_scale, 4),
        })
    return rows


def exp_e_confidence_gate(events):
    """S3: báo cáo giả 200 người. Gate C_i làm N_total của cụm giảm bao nhiêu?"""
    idx = {e.event_id: i for i, e in enumerate(events)}
    w = build_weight_matrix(events, C.weight, mode="gating")
    ws = sparsify(w, C.weight)
    lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)
    s3_cluster = lab[idx["S3_FAKE"]] if "S3_FAKE" in idx else None

    mem = [e for e, l in zip(events, lab) if l == s3_cluster]
    n_ungated = sum(e.n_trapped for e in mem)
    n_gated = sum(e.n_trapped * e.confidence for e in mem)
    fake = next((e for e in mem if e.is_fake), None)
    return {
        "s3_cluster": s3_cluster,
        "fake_report_id": fake.event_id if fake else None,
        "fake_confidence_Ci": round(fake.confidence, 4) if fake else None,
        "fake_claimed_N": fake.n_trapped if fake else None,
        "cluster_N_ungated": round(n_ungated, 1),
        "cluster_N_gated": round(n_gated, 1),
        "reduction_pct": round(100 * (1 - n_gated / n_ungated), 1) if n_ungated else 0,
    }


def exp_f_fmax_gate(events):
    """S3: báo cáo giả khai ngập cao (F lớn) nhưng C_i thấp.
    Gate C_i bên trong max có chặn được nó chiếm trọn F_max không?
    So sánh F_max của cụm chứa S3 khi gate và không gate."""
    idx = {e.event_id: i for i, e in enumerate(events)}
    w = build_weight_matrix(events, C.weight, mode="gating")
    ws = sparsify(w, C.weight)
    lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)
    s3_cluster = lab[idx["S3_FAKE"]] if "S3_FAKE" in idx else None

    sc_gated = {s.cluster_id: s for s in score_clusters(events, lab, C.priority, gate_fmax=True)}
    sc_ungated = {s.cluster_id: s for s in score_clusters(events, lab, C.priority, gate_fmax=False)}

    mem = [e for e, l in zip(events, lab) if l == s3_cluster]
    fake = next((e for e in mem if e.is_fake), None)
    return {
        "s3_cluster": s3_cluster,
        "fake_report_id": fake.event_id if fake else None,
        "fake_flood_F": round(fake.flood, 4) if fake else None,
        "fake_confidence_Ci": round(fake.confidence, 4) if fake else None,
        "cluster_Fmax_ungated": sc_ungated[s3_cluster].f_max if s3_cluster in sc_ungated else None,
        "cluster_Fmax_gated": sc_gated[s3_cluster].f_max if s3_cluster in sc_gated else None,
    }


def exp_g_ari_decomposition(events):
    """BẤT BIẾN dữ liệu — trần ARI không bị ghim bởi thiết kế dữ liệu.

    Lịch sử: ở bản dữ liệu trước, các nhóm kịch bản (gt 100–105) được đặt TRÙNG
    tọa độ với 6 ốc đảo (gt 0–5) nhưng mang nhãn khác. Mọi phương pháp dựa trên
    không gian đều buộc phải gộp điểm kịch bản vào ốc đảo chủ, nên ARI toàn tập
    bị ghim ở 0,892 vì THIẾT KẾ DỮ LIỆU chứ không vì chất lượng thuật toán — và
    do đó ARI không còn phân biệt được phương pháp (phản biện 2.2).

    Sau khi sinh lại dữ liệu, mỗi nhóm kịch bản cách tâm ốc đảo chủ ≥ 3 km
    (≫ sigma_geo = 700 m). Hàm này giữ lại phân rã ARI như một PHÉP KIỂM
    HỒI QUY: `n_colocated_narrative_groups` phải bằng 0 và ARI core-only,
    narrative-only, toàn tập phải xấp xỉ nhau. Nếu con số trùng-tọa-độ > 0 quay
    lại, phép kiểm này phát hiện ngay.
    """
    from sklearn.metrics import adjusted_rand_score

    w = build_weight_matrix(events, C.weight, mode="gating")
    ws = sparsify(w, C.weight)
    lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)

    gt = [e.gt_cluster for e in events]
    core_idx = [i for i, g in enumerate(gt) if 0 <= g <= 5]
    narr_idx = [i for i, g in enumerate(gt) if g >= 100]
    all_idx = [i for i, g in enumerate(gt) if g >= 0]

    def _ari(idxs):
        return round(float(adjusted_rand_score(
            [gt[i] for i in idxs], [lab[i] for i in idxs])), 4)

    # đếm nhóm kịch bản trùng tọa độ với TÂM ốc đảo thật (CLUSTER_CENTERS,
    # không phải điểm lõi đã bị jitter) — các điểm kịch bản được đặt đúng
    # tọa độ tâm nên lệch 0 m.
    from pipeline.attributes import haversine_m
    from data.generate import CLUSTER_CENTERS
    centers = [(clat, clng) for clat, clng, _ in CLUSTER_CENTERS]
    colocated = 0
    seen = set()
    for e, g in zip(events, gt):
        if g >= 100 and g not in seen:
            seen.add(g)
            dmin = min(haversine_m(e.lat, e.lng, cl[0], cl[1]) for cl in centers)
            if dmin < 1.0:
                colocated += 1

    return {
        "n_gt_labels": len({g for g in gt if g >= 0}),
        "ari_core_only": _ari(core_idx),
        "ari_narrative_only": _ari(narr_idx),
        "ari_all_labeled": _ari(all_idx),
        "n_core": len(core_idx),
        "n_narrative": len(narr_idx),
        "n_all_labeled": len(all_idx),
        "n_colocated_narrative_groups": colocated,
    }


def main():
    events = prepared_events()

    rows_a = exp_a_gating_vs_additive(events)
    print_table("A. w_ij: Cộng (quét alpha) vs Nhân/Gating — so trên đường kính "
                "cụm nhiều thành viên và trường hợp xấu nhất", rows_a)
    print("   Cột so sánh hợp lệ: max_diam_km và mean_diam_km_multi. "
          "mean_diam_km_all tính cả singleton (0 km) nên thưởng giả tạo cho "
          "phân hoạch vụn — chỉ để tham khảo.")
    print("   s1_merged = True nghĩa là hai nhóm S1 cách 107 km bị gộp làm một cụm "
          "(sai về mặt vận hành).")

    res_g = exp_g_ari_decomposition(events)
    print_table("G. BẤT BIẾN dữ liệu: nhãn kịch bản khả tách bằng không gian "
                "(n_colocated phải = 0)", [res_g])
    if res_g["n_colocated_narrative_groups"] != 0:
        print("   !! CẢNH BÁO: có nhóm kịch bản trùng tâm ốc đảo -> trần ARI bị "
              "ghim bởi thiết kế dữ liệu. Chạy lại data/generate.py.")
    else:
        print("   OK: không nhóm kịch bản nào trùng tâm ốc đảo; ARI phản ánh chất "
              "lượng thuật toán chứ không phải trần do dữ liệu.")

    res_b = exp_b_normalization(events)
    print_table("B. P(C_k): Tác động chuẩn hóa thang đo", [res_b])

    rows_c, s2c = exp_c_v_multiplier(events)
    print_table(f"C. V_agg nhân vs cộng (cụm S2 = {s2c})", rows_c[:6])

    rows_d = exp_d_tanh_saturation()
    print_table("D. Chống bão hòa tanh (khả năng phân biệt)", rows_d)

    res_e = exp_e_confidence_gate(events)
    print_table("E. Gate C_i hạ nhiệt tin giả (S3)", [res_e])

    res_f = exp_f_fmax_gate(events)
    print_table("F. Gate C_i cho F_max chặn tin giả khai ngập cao (S3)", [res_f])

    save_table("exp1_A_gating_vs_additive.json", rows_a)
    save_table("exp1_G_ari_decomposition.json", [res_g])
    save_table("exp1_B_normalization.json", [res_b])
    save_table("exp1_C_v_multiplier.json", rows_c)
    save_table("exp1_D_tanh_saturation.json", rows_d)
    save_table("exp1_E_confidence_gate.json", [res_e])
    save_table("exp1_F_fmax_gate.json", [res_f])
    print("\n[saved] exp1_*.json -> results/tables/")


if __name__ == "__main__":
    main()
