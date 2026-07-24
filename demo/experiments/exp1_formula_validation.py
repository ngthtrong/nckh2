"""Thí nghiệm 1 — Kiểm chứng 4 fix của Mục 4.

A. w_ij: cộng vs nhân/gating  -> đo đường kính địa lý cụm (S1: hai điểm xa cùng ngữ cảnh).
B. P(C_k): chuẩn hóa vs không  -> chứng minh N_total áp đảo khi không chuẩn hóa.
C. V_agg: nhân vs cộng          -> chứng minh 'khuếch đại' chỉ đúng khi nhân (S2).
D. tanh bão hòa: có/không s     -> khả năng phân biệt cụm ít vs nhiều đối tượng yếu thế.
E. gate C_i cho N_total         -> tin giả S3 bị hạ nhiệt.
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
    gt = [e.gt_cluster for e in events]
    rows = []
    for mode in ("additive", "gating"):
        w = build_weight_matrix(events, C.weight, mode=mode)
        ws = sparsify(w, C.weight)
        lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)
        q = cluster_quality(lab, gt)
        spread = geographic_spread(events, lab)
        rows.append({
            "mode": mode,
            "ari": q["ari"],
            "nmi": q["nmi"],
            "mean_diam_km": spread["mean_diameter_km"],
            "max_diam_km": spread["max_diameter_km"],
            "n_clusters": spread["n_clusters"],
        })
    return rows


def _s1_same_cluster(events, mode):
    """S1_A (Huế) và S1_B (Hội An, xa ~90km) có bị gom chung cụm không?"""
    w = build_weight_matrix(events, C.weight, mode=mode)
    ws = sparsify(w, C.weight)
    lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)
    idx = {e.event_id: i for i, e in enumerate(events)}
    a, b = idx.get("S1_A"), idx.get("S1_B")
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
    """S2 (cụm nhiều đối tượng yếu thế): V nhân đẩy ưu tiên bao nhiêu so với cộng?"""
    w = build_weight_matrix(events, C.weight, mode="gating")
    ws = sparsify(w, C.weight)
    lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)

    sc_mult = {s.cluster_id: s for s in score_clusters(events, lab, C.priority, normalize_v=True)}
    sc_add = {s.cluster_id: s for s in score_clusters(events, lab, C.priority, normalize_v=False)}

    # tìm cụm chứa S2
    idx = {e.event_id: i for i, e in enumerate(events)}
    s2_cluster = lab[idx["S2_0"]] if "S2_0" in idx else None

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


def main():
    events = prepared_events()

    rows_a = exp_a_gating_vs_additive(events)
    print_table("A. w_ij: Cộng vs Nhân/Gating (chất lượng + gắn kết địa lý)", rows_a)
    print(f"   S1 (Huế & Hội An cách 90km) gom chung cụm? "
          f"additive={_s1_same_cluster(events,'additive')}  "
          f"gating={_s1_same_cluster(events,'gating')}")

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
    save_table("exp1_B_normalization.json", [res_b])
    save_table("exp1_C_v_multiplier.json", rows_c)
    save_table("exp1_D_tanh_saturation.json", rows_d)
    save_table("exp1_E_confidence_gate.json", [res_e])
    save_table("exp1_F_fmax_gate.json", [res_f])
    print("\n[saved] exp1_*.json -> results/tables/")


if __name__ == "__main__":
    main()
