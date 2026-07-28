"""Thí nghiệm 13 — Xác nhận thực nghiệm của Bổ đề 1 (bảo đảm định vị của dạng nhân).

VÒNG 17 — CHUYỂN VAI (phản biện §1).

Bản trước dùng thí nghiệm này để tuyên bố "cửa sổ theta dùng được rộng 51×". Đo
lại cho thấy con số 51× là ARTIFACT của một thước đo KHÔNG BẤT BIẾN: nó là tỉ số
theta_hi/theta_lo của độ rộng TUYỆT ĐỐI, mà độ rộng tuyệt đối phụ thuộc thang giá
trị của w (gating dùng theta→0 được, dạng cộng thì không vì có sàn dương). Theo
hai thước đo BẤT BIẾN (theta chuẩn hoá theo w_max, và tỉ lệ cạnh giữ lại), lợi thế
chỉ còn 2× và 1× — KHÔNG phải 51×.

Đóng góp thật KHÔNG nằm ở "cửa sổ rộng hơn" mà ở BỔ ĐỀ 1 (Mục 4.2):

    Với w_ij = S_geo(d_ij)·(beta·S_temp + gamma·S_ctx) và beta+gamma <= 1, mọi cạnh
    sống sót sau khi cắt ở theta > 0 đều thoả d_ij < sigma·sqrt(2·ln(1/theta)).
    => đường kính cụm bị chặn bởi h·sigma·sqrt(2·ln(1/theta)), KHÔNG phụ thuộc dữ liệu.

    Hệ quả: dạng CỘNG w_ij = alpha·S_geo + beta·S_temp + gamma·S_ctx có sàn dương
    độc lập khoảng cách (= min beta·S_temp+gamma·S_ctx). Với mọi theta dưới sàn đó,
    tập cạnh còn lại KHÔNG bị chặn về khoảng cách — tồn tại cặp cách nhau tuỳ ý xa
    vẫn được giữ.

Thí nghiệm này giờ làm ba việc:
  (1) Đo miền giá trị của từng dạng để thấy vì sao cùng một theta không công bằng.
  (2) Quét theta cho từng dạng, báo cáo các cột BẤT BIẾN (theta/w_max, tỉ lệ cạnh
      giữ lại) thay cho tỉ số độ rộng tuyệt đối. Tiêu chí "dùng được" là THUẦN VẬN
      HÀNH (không dùng nhãn GT — điều phối viên thật không có nhãn).
  (3) `verify_lemma1`: với mỗi theta trong sweep, kiểm max{d_ij : w_ij > theta} so
      với cận sigma·sqrt(2·ln(1/theta)). Gating phải LUÔN thoả; dạng cộng phải VI
      PHẠM ở theta nhỏ hơn sàn. Đây là bảng thay thế cho bảng 51× cũ.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np

from common import prepared_events, print_table, save_table
from pipeline.config import DEFAULT_CONFIG as C
from pipeline.clustering import run_louvain
from pipeline.metrics import cluster_quality, geographic_spread, noise_handling
from pipeline.weighting import (
    build_weight_matrix,
    sparsify,
    max_weight,
    implied_distance_cutoff,
    additive_floor,
    max_edge_distance_above,
    retained_fraction,
)

# --- Tiêu chí "dùng được cho điều phối" — THUẦN VẬN HÀNH (P1.4) --------------
# Bản trước lọc theo `ari >= 0.95`, nhưng ARI cần nhãn ground-truth, mà điều phối
# viên trong thảm hoạ thật KHÔNG có nhãn. Tiêu chí usable phải là thứ đo được KHI
# KHÔNG có nhãn: đường kính cụm xấu nhất trong tầm ca nô, không quá vụn, số cụm
# hợp lý. ARI vẫn được BÁO CÁO (cột tham khảo) nhưng KHÔNG dùng để lọc.
#
# Ba điều kiện dưới đây đều đo được KHÔNG cần nhãn:
#   - `max_diameter_km` lấy trên MỌI cụm (kể cả cụm toàn tin nhiễu), vì điều phối
#     viên không biết cụm nào là nhiễu — cụm rộng vẫn là cụm rộng với họ.
#   - phân vụn đo theo TỈ LỆ SỰ KIỆN nằm trong cụm đơn lẻ, không phải tỉ lệ CỤM:
#     tin giả cô lập đúng ra tạo nhiều cụm đơn (dấu hiệu TỐT), nên đếm theo cụm
#     sẽ phạt oan chính hành vi ta muốn.
#   - đếm cụm dùng `n_clusters_multi` (cụm >= 2 thành viên) — số cụm THỰC SỰ cần
#     điều một ca nô tới.
USABLE_MAX_DIAM_KM = 5.0
USABLE_MAX_FRAC_EVENTS_SINGLETON = 0.5
USABLE_MIN_CLUSTERS = 5
USABLE_MAX_CLUSTERS = 40

# Các dạng trọng số đưa vào so sánh, cùng miền quét theta của riêng nó.
# Mỗi phần tử: (nhãn hiển thị, slug ASCII cho tên file, mode, alpha, dải theta).
FORMS = [
    ("gating", "gating", "gating", None, np.arange(0.01, 0.76, 0.02)),
    ("additive (alpha=0.34)", "additive_alpha034", "additive", 0.34,
     np.arange(0.02, 1.40, 0.02)),
    ("additive (alpha=0.5)", "additive_alpha05", "additive", 0.5,
     np.arange(0.02, 1.60, 0.02)),
    ("additive (alpha=1.0)", "additive_alpha10", "additive", 1.0,
     np.arange(0.02, 2.00, 0.02)),
    ("additive (chuẩn hoá 1/3)", "additive_norm13", "additive_norm", None,
     np.arange(0.02, 1.00, 0.02)),
]


def _evaluate(events, gt, mode, alpha, theta, wmax):
    wp = replace(C.weight, edge_threshold=float(theta))
    w = build_weight_matrix(events, wp, mode=mode, alpha=alpha)
    ws = sparsify(w, wp)
    lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)
    q = cluster_quality(lab, gt)
    sp = geographic_spread(events, lab, gt_labels=gt)
    nz = noise_handling(lab, gt, noise_label=None)
    n_sing = sp["n_singletons"]
    # Phân vụn theo TỈ LỆ SỰ KIỆN (mỗi cụm đơn lẻ = 1 sự kiện), không theo tỉ lệ cụm.
    frac_ev_sing = round(n_sing / len(events), 4) if len(events) else 0.0
    return {
        "theta": round(float(theta), 3),
        # --- cột BẤT BIẾN (thay cho độ rộng tuyệt đối 51×) ---
        "theta_norm": round(float(theta) / wmax, 4) if wmax > 0 else None,
        "retained_frac": round(retained_fraction(events, wp, float(theta),
                                                  mode=mode, alpha=alpha), 4),
        # --- cột vận hành (tiêu chí usable) — KHÔNG dùng nhãn GT ---
        "max_diam_km": sp["max_diameter_km"],
        "frac_events_singleton": frac_ev_sing,
        "n_clusters_multi": sp["n_clusters_multi"],
        # --- cột tham khảo (KHÔNG dùng để lọc usable) ---
        "max_diam_km_labeled": sp["max_diameter_km_labeled"],
        "n_clusters": sp["n_clusters"],
        "ari": q["ari"],
        "nmi": q["nmi"],
        "n_edges": int(np.count_nonzero(ws) // 2),
    }


def _is_usable(r) -> bool:
    """Tiêu chí thuần vận hành — không đụng nhãn GT.

    Ba điều kiện đều là thứ điều phối viên đọc được ngay trên bản đồ: cụm xấu nhất
    còn trong tầm triển khai một ca nô, phần lớn sự kiện không bị bỏ rơi lẻ loi, và
    số cụm NHIỀU THÀNH VIÊN nằm trong tầm điều phối được của một ca trực.
    """
    return (
        r["max_diam_km"] is not None
        and r["max_diam_km"] < USABLE_MAX_DIAM_KM
        and r["frac_events_singleton"] < USABLE_MAX_FRAC_EVENTS_SINGLETON
        and USABLE_MIN_CLUSTERS <= r["n_clusters_multi"] <= USABLE_MAX_CLUSTERS
    )


def verify_lemma1(events, gt):
    """Kiểm Bổ đề 1 bằng thực nghiệm cho từng dạng, trên toàn dải theta.

    Với mỗi theta: so `max{d_ij : w_ij > theta}` (đo) với cận `sigma·sqrt(2 ln 1/theta)`.
    - gating: cận phải LUÔN đúng (0 vi phạm) — đó là nội dung Bổ đề 1.
    - dạng cộng: cận bị VI PHẠM ở theta nhỏ hơn sàn (`additive_floor`), vì sàn dương
      độc lập khoảng cách giữ lại các cạnh xa tuỳ ý.

    Trả về (bảng tóm tắt mỗi dạng, chi tiết vi phạm theo theta).
    """
    summary = []
    detail = {}
    for label, slug, mode, alpha, thetas in FORMS:
        floor = (additive_floor(
                    events, C.weight, alpha=alpha, mode=mode)
                 if mode in ("additive", "additive_norm") else None)
        rows = []
        n_violations = 0
        first_violation_theta = None
        for t in thetas:
            wp = replace(C.weight, edge_threshold=float(t))
            cutoff = implied_distance_cutoff(wp, float(t))
            max_d, n_edges = max_edge_distance_above(events, wp, float(t),
                                                     mode=mode, alpha=alpha)
            violates = bool(max_d > cutoff + 1e-6)   # dung sai số học nhỏ
            if violates:
                n_violations += 1
                if first_violation_theta is None:
                    first_violation_theta = round(float(t), 3)
            rows.append({
                "theta": round(float(t), 3),
                "implied_cutoff_m": round(cutoff, 1),
                "max_edge_dist_m": round(max_d, 1),
                "n_edges": n_edges,
                "violates_lemma1": violates,
            })
        detail[slug] = rows
        summary.append({
            "form": label,
            "additive_floor": round(floor, 4) if floor is not None else None,
            "n_theta_checked": len(rows),
            "n_lemma1_violations": n_violations,
            "first_violation_theta": first_violation_theta,
            "lemma1_holds": n_violations == 0,
        })
    return summary, detail


def main():
    events = prepared_events()
    gt = [e.gt_cluster for e in events]

    # --- Phần 1: miền giá trị của từng dạng, để thấy confound bằng con số ---
    range_rows = []
    wmax_by_slug = {}
    for label, slug, mode, alpha, _ in FORMS:
        w = build_weight_matrix(events, C.weight, mode=mode, alpha=alpha)
        off = w[~np.eye(len(events), dtype=bool)]
        wmax = float(off.max())
        wmax_by_slug[slug] = wmax
        range_rows.append({
            "form": label,
            "w_min": round(float(off.min()), 4),
            "w_median": round(float(np.median(off)), 4),
            "w_max": round(wmax, 4),
            "frac_pairs_above_0.05": round(float((off > 0.05).mean()), 4),
        })
    print_table("Miền giá trị w_ij theo từng dạng — VÌ SAO cùng một theta không "
                "phải một so sánh công bằng", range_rows)
    print("   Cùng theta = 0,05 giữ lại ~100% cặp của dạng cộng nhưng chỉ ~8% cặp")
    print("   của gating: dạng cộng bị đưa vào Louvain như đồ thị gần hoàn chỉnh.")

    # --- Phần 2: quét theta, báo cáo cột BẤT BIẾN + usable thuần vận hành ---
    best_rows = []
    all_sweeps = {}
    for label, slug, mode, alpha, thetas in FORMS:
        wmax = wmax_by_slug[slug]
        sweep = [_evaluate(events, gt, mode, alpha, t, wmax) for t in thetas]
        all_sweeps[slug] = sweep

        usable = [r for r in sweep if _is_usable(r)]
        best_ari = max(sweep, key=lambda r: r["ari"])
        if usable:
            lo = min(r["theta"] for r in usable)
            hi = max(r["theta"] for r in usable)
            # cột BẤT BIẾN thay cho width_ratio: theta chuẩn hoá tại hai đầu cửa sổ
            norm_lo = min(r["theta_norm"] for r in usable)
            norm_hi = max(r["theta_norm"] for r in usable)
            ret_lo = min(r["retained_frac"] for r in usable)
            ret_hi = max(r["retained_frac"] for r in usable)
        else:
            lo = hi = norm_lo = norm_hi = ret_lo = ret_hi = None

        best_rows.append({
            "form": label,
            "best_ari": best_ari["ari"],
            "theta_at_best_ari": best_ari["theta"],
            "max_diam_at_best_ari": best_ari["max_diam_km"],
            "n_usable_theta": len(usable),
            "usable_theta_lo": lo,
            "usable_theta_hi": hi,
            # BẤT BIẾN: thay cột usable_width_ratio (không bất biến) bị bỏ
            "usable_theta_norm_lo": norm_lo,
            "usable_theta_norm_hi": norm_hi,
            "usable_retained_lo": ret_lo,
            "usable_retained_hi": ret_hi,
            "ari_at_published_theta_0.05": next(
                (r["ari"] for r in sweep if abs(r["theta"] - 0.05) < 1e-9), None),
        })

    print_table("Kết quả TỐT NHẤT của từng dạng khi theta hiệu chuẩn riêng — "
                "TIÊU CHÍ USABLE THUẦN VẬN HÀNH (không dùng nhãn GT): "
                f"max_diam(mọi cụm) < {USABLE_MAX_DIAM_KM} km VÀ "
                f"frac_events_singleton < {USABLE_MAX_FRAC_EVENTS_SINGLETON} VÀ "
                f"{USABLE_MIN_CLUSTERS} <= n_clusters_multi <= "
                f"{USABLE_MAX_CLUSTERS}", best_rows)
    print("   Đọc theo hai cột BẤT BIẾN (theta_norm, retained_frac), KHÔNG theo tỉ")
    print("   số độ rộng tuyệt đối: con số 51× cũ là artifact của thước đo không")
    print("   bất biến. Lợi thế thật của gating là Bổ đề 1 (bảng dưới), không phải")
    print("   một cửa sổ rộng hơn.")

    # --- Phần 3: KIỂM BỔ ĐỀ 1 (bảng thay thế bảng 51×) ---
    lemma_summary, lemma_detail = verify_lemma1(events, gt)
    print_table("KIỂM BỔ ĐỀ 1: max{d_ij : w_ij>theta} so với cận sigma·sqrt(2 ln 1/theta) "
                "— gating: 0 vi phạm; dạng cộng: vi phạm ở theta < sàn", lemma_summary)
    print("   Đây là bằng chứng đóng góp trung tâm: bảo đảm định vị của dạng nhân")
    print("   là BẤT BIẾN theo tái tham số hoá và không cần nhãn/seed nào.")

    save_table("exp13_theta_calibration_best.json", best_rows)
    save_table("exp13_theta_ranges.json", range_rows)
    save_table("exp13_lemma1_check.json", lemma_summary)
    for slug, sweep in all_sweeps.items():
        save_table(f"exp13_sweep_{slug}.json", sweep)
    for slug, rows in lemma_detail.items():
        save_table(f"exp13_lemma1_detail_{slug}.json", rows)
    print("\n[saved] exp13_*.json + exp13_lemma1_*.json -> results/tables/")


if __name__ == "__main__":
    main()
