"""Thí nghiệm 1 — Kiểm chứng 4 fix của Mục 4.

A. w_ij: cộng (quét alpha) vs nhân/gating -> đường kính địa lý cụm; kèm phép kiểm
   hai nhóm cách hơn 100 km có bị gộp không. Quét alpha để dạng cộng không bị dựng
   thành người rơm.
B. P(C_k): chuẩn hóa vs không  -> chứng minh N_total áp đảo khi không chuẩn hóa.
C. V_agg: nhân vs cộng          -> 'khuếch đại' chỉ đúng khi nhân; neo vào cụm
   giàu-yếu-thế nhất, so trên thang đã chuẩn hoá để hai dạng cùng miền giá trị.
D. tanh bão hòa: có/không s     -> khả năng phân biệt cụm ít vs nhiều đối tượng yếu thế.
E. gate C_i cho N_total         -> tin giả khai N lớn nhất bị hạ nhiệt.
F. gate C_i cho F_max           -> tin giả khai ngập cao không chiếm trọn F_max.
G. Phân rã ARI theo LOẠI CẤU TRÚC KHÓ -> ARI toàn tập đến từ đâu: cặp chồng lấn
   không gian, cặp trùng tâm khác thời gian, nhãn multimodal, nhóm đơn. Cột nào
   thấp là chỗ phương pháp còn yếu.

Mọi phép kiểm ở đây neo ĐỘNG vào dữ liệu (chọn cụm/tin giả xấu nhất từ chính
dataset) thay vì tra ID kịch bản cứng như bản trước — generator P1 không còn dựng
kịch bản đặt tay, và neo động thì chặt hơn: generator đổi, phép kiểm vẫn nhắm đúng
trường hợp nguy hiểm nhất.
"""
from __future__ import annotations

import math

from scipy.stats import kendalltau as _kendalltau

from common import prepared_events, print_table, save_table
from pipeline.attributes import haversine_m
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
            "far_groups_merged": _far_groups_merged(events, mode, alpha),
        })
    return rows


def _far_groups_merged(events, mode, alpha=None):
    """Hai nhóm GT XA NHAU nhất có bị gom chung một cụm không?

    Trước đây hàm này tra hai ID kịch bản cứng (`S1_A_0`, `S1_B_0`) do generator
    cũ sinh ra. Bộ dữ liệu mới (P1) không còn kịch bản đặt tay nào, nên phép kiểm
    được viết lại theo CẤU TRÚC: tự tìm cặp nhãn GT có tâm cách nhau xa nhất rồi
    hỏi xem chúng có bị gộp không. Ý nghĩa vận hành giữ nguyên — dạng trọng số
    nào gộp hai vùng cách hàng trăm km là sai — nhưng phép kiểm không còn phụ
    thuộc vào ID nào cả, nên không âm thầm vô hiệu khi dữ liệu đổi.
    """
    w = build_weight_matrix(events, C.weight, mode=mode, alpha=alpha)
    ws = sparsify(w, C.weight)
    lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)

    # tâm từng nhãn GT
    cents: dict[int, list] = {}
    for e in events:
        if e.gt_cluster >= 0:
            cents.setdefault(e.gt_cluster, []).append((e.lat, e.lng))
    if len(cents) < 2:
        return None
    means = {g: (sum(p[0] for p in v) / len(v), sum(p[1] for p in v) / len(v))
             for g, v in cents.items()}

    # cặp nhãn xa nhau nhất
    keys = sorted(means)
    best = None
    for i, ga in enumerate(keys):
        for gb in keys[i + 1:]:
            d = haversine_m(*means[ga], *means[gb])
            if best is None or d > best[0]:
                best = (d, ga, gb)
    _, ga, gb = best

    # đại diện: điểm gần tâm nhãn nhất
    def _rep(g):
        cand = [(haversine_m(e.lat, e.lng, *means[g]), i)
                for i, e in enumerate(events) if e.gt_cluster == g]
        return min(cand)[1]

    return lab[_rep(ga)] == lab[_rep(gb)]


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

    # Cụm "giàu đối tượng yếu thế" — tức trường hợp mà V_agg nhân được kỳ vọng
    # khuếch đại. Bản trước neo vào ID kịch bản `S2_0` do generator cũ đặt tay;
    # dataset mới (P1) không còn kịch bản nào như vậy, nên ta chọn TỪ DỮ LIỆU:
    # cụm nhiều thành viên có tổng V lớn nhất. Đây cũng là phép kiểm chặt hơn vì
    # nó luôn nhắm đúng trường hợp mà tuyên bố của bài phải đúng.
    v_sum_by_cluster: dict[int, float] = {}
    size_by_cluster: dict[int, int] = {}
    for ev, l in zip(events, lab):
        v_sum_by_cluster[l] = v_sum_by_cluster.get(l, 0.0) + ev.vulnerability
        size_by_cluster[l] = size_by_cluster.get(l, 0) + 1
    multi = [c for c in v_sum_by_cluster if size_by_cluster[c] >= 2]
    s2_cluster = max(multi, key=lambda c: v_sum_by_cluster[c]) if multi else None

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
            "is_top_vuln": cid == s2_cluster,
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


def exp_h_mu_policy(events):
    """H. Núm chính sách mu: nó thực sự đổi được thứ hạng bao nhiêu?

    Bài báo trình bày mu như một "núm đạo đức" cho ban chỉ huy, nói rằng mu lớn
    có thể đẩy một cụm nhỏ nhiều người yếu thế lên trên một cụm lớn khoẻ mạnh.
    Đó là một tuyên bố THỰC NGHIỆM, và trước đây chưa có thí nghiệm nào chạy với
    mu != 2 — nghĩa là tuyên bố chưa được kiểm chứng trên chính bộ dữ liệu này.

    Ở đây ta quét mu qua toàn miền đã công bố [1, 2] và đo:
      - top3: tập ba cụm đầu (mu có đảo được nhóm dẫn đầu không?)
      - kendall_tau_vs_mu2: thứ hạng lệch bao nhiêu so với mặc định mu = 2
      - top1_v_agg / top1_size: cụm đầu bảng có phải cụm giàu-yếu-thế hay không

    Nếu top-3 không đổi trên toàn miền, phải báo cáo đúng như vậy: núm này có
    hiệu lực toán học nhưng KHÔNG đủ để đảo nhóm dẫn đầu trên dữ liệu này.
    """
    from dataclasses import replace

    w = build_weight_matrix(events, C.weight, mode="gating")
    ws = sparsify(w, C.weight)
    lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)

    sizes = {}
    for ev, l in zip(events, lab):
        sizes[l] = sizes.get(l, 0) + 1

    def _order(mu):
        p = replace(C.priority, v_cap_mu=mu)
        return score_clusters(events, lab, p)

    base = [s.cluster_id for s in _order(2.0)]
    pos_base = {cid: i for i, cid in enumerate(base)}

    rows = []
    for mu in (1.0, 1.25, 1.5, 1.75, 2.0):
        sc = _order(mu)
        order = [s.cluster_id for s in sc]
        x = [pos_base[c] for c in order]
        y = list(range(len(order)))
        tau, _ = _kendalltau(x, y)
        rows.append({
            "mu": mu,
            "top3_clusters": order[:3],
            "top3_same_as_mu2": order[:3] == base[:3],
            "kendall_tau_vs_mu2": round(float(tau), 4),
            "top1_cluster": order[0],
            "top1_v_agg": sc[0].v_agg,
            "top1_core": sc[0].core,
            "top1_priority": sc[0].priority,
            "top1_size": sizes[order[0]],
            "max_priority": max(s.priority for s in sc),
        })
    return rows


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


def _worst_fake_cluster(events, lab, key):
    """Tin giả TỆ NHẤT theo `key` và cụm chứa nó — chọn TỪ DỮ LIỆU, không hardcode ID.

    Bản trước neo vào `S3_FAKE`, một ID mà generator cũ dựng thủ công. Dataset mới
    (P1) không còn kịch bản đặt tay: tin giả được rải vào TRONG các cụm thật, nên
    phép kiểm phải tự tìm trường hợp xấu nhất. Làm vậy còn chặt hơn: nếu generator
    đổi, phép kiểm vẫn nhắm đúng tin giả nguy hiểm nhất.

    `key` chọn trục "nguy hiểm": mục E dùng N khai báo (bơm N_total), mục F dùng F
    khai báo (chiếm trọn F_max).
    """
    fakes = [(e, l) for e, l in zip(events, lab) if e.is_fake]
    if not fakes:
        return None, None
    fake, cid = max(fakes, key=lambda p: key(p[0]))
    return fake, cid


def exp_e_confidence_gate(events):
    """Gate C_i làm N_total của cụm chứa tin giả khai N lớn nhất giảm bao nhiêu?"""
    w = build_weight_matrix(events, C.weight, mode="gating")
    ws = sparsify(w, C.weight)
    lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)
    fake, fake_cluster = _worst_fake_cluster(events, lab, key=lambda e: e.n_trapped)
    if fake is None:
        return {"note": "dataset không có tin giả"}

    mem = [e for e, l in zip(events, lab) if l == fake_cluster]
    n_ungated = sum(e.n_trapped for e in mem)
    n_gated = sum(e.n_trapped * e.confidence for e in mem)
    return {
        "fake_cluster": fake_cluster,
        "fake_report_id": fake.event_id if fake else None,
        "fake_confidence_Ci": round(fake.confidence, 4) if fake else None,
        "fake_claimed_N": fake.n_trapped if fake else None,
        "cluster_size": len(mem),
        "cluster_N_ungated": round(n_ungated, 1),
        "cluster_N_gated": round(n_gated, 1),
        "reduction_pct": round(100 * (1 - n_gated / n_ungated), 1) if n_ungated else 0,
    }


def exp_f_fmax_gate(events):
    """Tin giả khai NGẬP CAO (F lớn) nhưng C_i thấp: gate C_i bên trong max có
    chặn được nó chiếm trọn F_max của cụm không?

    Neo động giống mục E, nhưng chọn tin giả theo F cao nhất (đây là tin giả gây
    hại nhất cho F_max) thay vì theo N.
    """
    w = build_weight_matrix(events, C.weight, mode="gating")
    ws = sparsify(w, C.weight)
    lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)

    fake, target = _worst_fake_cluster(events, lab, key=lambda e: e.flood)
    if fake is None:
        return {"note": "dataset không có tin giả"}

    sc_gated = {s.cluster_id: s for s in score_clusters(events, lab, C.priority, gate_fmax=True)}
    sc_ungated = {s.cluster_id: s for s in score_clusters(events, lab, C.priority, gate_fmax=False)}

    mem = [e for e, l in zip(events, lab) if l == target]
    return {
        "target_cluster": int(target),
        "cluster_size": len(mem),
        "fake_report_id": fake.event_id,
        "fake_flood_F": round(fake.flood, 4),
        "fake_confidence_Ci": round(fake.confidence, 4),
        "cluster_Fmax_ungated": sc_ungated[target].f_max if target in sc_ungated else None,
        "cluster_Fmax_gated": sc_gated[target].f_max if target in sc_gated else None,
    }


def exp_g_ari_decomposition(events):
    """Phân rã ARI theo BA CẤU TRÚC KHÓ mà dataset P1 cố tình dựng.

    Lịch sử: bản trước phân rã theo "core" (gt 0–5) vs "kịch bản" (gt >= 100) và
    kiểm hồi quy `n_colocated_narrative_groups == 0`. Dataset P1 đã bỏ hoàn toàn
    các nhóm kịch bản đặt tay, nên hai con số đó nay luôn rỗng/0 — tức phép kiểm
    cũ không còn kiểm gì cả. Thay vào đó ta phân rã theo đúng ba cấu trúc khiến
    dataset khó, mỗi cấu trúc cô lập MỘT thành phần của w_ij:

      - chồng lấn không gian (gt 0–5): ba cặp tâm cách < 800 m nhưng NGƯỢC ngữ
        cảnh (F ~0,85 vs ~0,25) -> chỉ S_ctx tách được. ARI thấp ở đây nghĩa là
        thành phần ngữ cảnh không làm việc.
      - cùng vị trí khác thời gian (gt 6–7): chồng tâm, lệch 3,5 h -> chỉ S_temp
        tách được.
      - multimodal (gt 8): một nhãn, hai ổ điểm cách ~1,4 km -> không ngưỡng
        khoảng cách đơn nào gộp đúng; đây là trần khó có thật, không phải lỗi.

    Đọc bảng theo hướng: nếu một dòng tụt hẳn so với các dòng khác thì thành phần
    tương ứng của w_ij là chỗ yếu, và đó là thông tin hữu ích chứ không phải điều
    cần che.
    """
    from sklearn.metrics import adjusted_rand_score

    w = build_weight_matrix(events, C.weight, mode="gating")
    ws = sparsify(w, C.weight)
    lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)

    gt = [e.gt_cluster for e in events]

    def _idx(pred):
        return [i for i, g in enumerate(gt) if pred(g)]

    overlap_idx = _idx(lambda g: 0 <= g <= 5)     # 3 cặp chồng lấn không gian
    sametime_idx = _idx(lambda g: g in (6, 7))    # cặp cùng vị trí khác thời gian
    multimodal_idx = _idx(lambda g: g == 8)       # nhãn hai ổ điểm
    single_idx = _idx(lambda g: 9 <= g <= 12)     # nhóm đơn, mật độ biến thiên
    all_idx = _idx(lambda g: g >= 0)

    def _ari(idxs):
        if len(idxs) < 2:
            return None
        return round(float(adjusted_rand_score(
            [gt[i] for i in idxs], [lab[i] for i in idxs])), 4)

    return {
        "n_gt_labels": len({g for g in gt if g >= 0}),
        "ari_spatial_overlap_gt0_5": _ari(overlap_idx),
        "ari_same_loc_diff_time_gt6_7": _ari(sametime_idx),
        "ari_multimodal_gt8": _ari(multimodal_idx),
        "ari_single_groups_gt9_12": _ari(single_idx),
        "ari_all_labeled": _ari(all_idx),
        "n_spatial_overlap": len(overlap_idx),
        "n_same_loc_diff_time": len(sametime_idx),
        "n_multimodal": len(multimodal_idx),
        "n_single_groups": len(single_idx),
        "n_all_labeled": len(all_idx),
    }


def main():
    events = prepared_events()

    rows_a = exp_a_gating_vs_additive(events)
    print_table("A. w_ij: Cộng (quét alpha) vs Nhân/Gating — so trên đường kính "
                "cụm nhiều thành viên và trường hợp xấu nhất", rows_a)
    print("   Cột so sánh hợp lệ: max_diam_km và mean_diam_km_multi. "
          "mean_diam_km_all tính cả singleton (0 km) nên thưởng giả tạo cho "
          "phân hoạch vụn — chỉ để tham khảo.")
    print("   far_groups_merged = True nghĩa là hai nhóm cách hơn 100 km bị gộp làm "
          "một cụm (sai về mặt vận hành).")

    res_g = exp_g_ari_decomposition(events)
    print_table("G. Phân rã ARI theo LOẠI CẤU TRÚC KHÓ — ARI toàn tập đến từ đâu",
                [res_g])
    print("   ari_overlap_pairs: 3 cặp chồng lấn không gian, chỉ tách được bằng "
          "ngữ cảnh.")
    print("   ari_same_place_diff_time: cặp trùng tâm, chỉ tách được bằng thời gian.")
    print("   ari_multimodal: nhãn có hai ổ điểm cách ~1,4 km (không ngưỡng khoảng "
          "cách nào gộp đúng).")
    print("   Cột nào THẤP là chỗ phương pháp còn yếu — đọc thẳng, không tô hồng.")

    res_b = exp_b_normalization(events)
    print_table("B. P(C_k): Tác động chuẩn hóa thang đo", [res_b])

    rows_c, vc = exp_c_v_multiplier(events)
    print_table(f"C. V_agg nhân vs cộng (cụm giàu-yếu-thế nhất = {vc})", rows_c[:6])

    rows_d = exp_d_tanh_saturation()
    print_table("D. Chống bão hòa tanh (khả năng phân biệt)", rows_d)

    res_e = exp_e_confidence_gate(events)
    print_table("E. Gate C_i hạ nhiệt tin giả khai N lớn nhất", [res_e])

    res_f = exp_f_fmax_gate(events)
    print_table("F. Gate C_i cho F_max chặn tin giả khai ngập cao nhất", [res_f])

    rows_h = exp_h_mu_policy(events)
    print_table("H. Núm chính sách mu: quét toàn miền [1, 2] đã công bố", rows_h)
    if all(r["top3_same_as_mu2"] for r in rows_h):
        print("   LƯU Ý TRUNG THỰC: top-3 KHÔNG đổi trên toàn miền mu. Núm này có")
        print("   hiệu lực toán học (tau < 1, thứ hạng dưới có đổi) nhưng KHÔNG đủ")
        print("   để đảo nhóm dẫn đầu trên bộ dữ liệu này. Phải báo cáo đúng vậy.")
    else:
        print("   mu ĐỔI ĐƯỢC nhóm dẫn đầu — xem cột top3_clusters.")

    save_table("exp1_A_gating_vs_additive.json", rows_a)
    save_table("exp1_G_ari_decomposition.json", [res_g])
    save_table("exp1_B_normalization.json", [res_b])
    save_table("exp1_C_v_multiplier.json", rows_c)
    save_table("exp1_D_tanh_saturation.json", rows_d)
    save_table("exp1_E_confidence_gate.json", [res_e])
    save_table("exp1_F_fmax_gate.json", [res_f])
    save_table("exp1_H_mu_policy.json", rows_h)
    print("\n[saved] exp1_*.json -> results/tables/")


if __name__ == "__main__":
    main()
