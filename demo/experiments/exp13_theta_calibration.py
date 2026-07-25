"""Thí nghiệm 13 — Hiệu chuẩn ngưỡng theta: gating có thắng nhờ công thức, hay
nhờ một ngưỡng thuận lợi?

VÌ SAO CẦN THÍ NGHIỆM NÀY (một confound thật, phát hiện ở vòng phản biện 16).

Mọi so sánh cộng-vs-nhân trong Thí nghiệm 1A đều dùng CÙNG một ngưỡng làm thưa
theta = 0,05. Nhưng hai dạng trọng số có MIỀN GIÁ TRỊ khác nhau hẳn:

    gating       : w in [0; 0,988]   trung vị = 0,000
    cộng alpha=1 : w in [0,041; 1,988] trung vị = 0,391

Nguyên nhân: dạng cộng có S_temp và S_context là các số hạng ĐỘC LẬP, không bị
S_geo nhân vào, nên ngay cả một cặp cách nhau 200 km vẫn giữ w >= beta*S_temp +
gamma*S_context > 0. Hệ quả: cùng theta = 0,05 lọc 91,7% cặp của gating nhưng chỉ
lọc 0,01% cặp của dạng cộng. Nói cách khác, dạng cộng bị đưa vào Louvain dưới
dạng một đồ thị GẦN HOÀN CHỈNH — đúng chế độ mà chính bài báo nói Modularity hoạt
động kém.

Vậy phần nào của khoảng cách 214 km → 1,41 km là do công thức nhân, và phần nào
chỉ là do một ngưỡng vô tình bất lợi cho dạng cộng? Thí nghiệm này trả lời bằng
cách quét theta cho TỪNG dạng trọng số và báo cáo kết quả TỐT NHẤT mà mỗi dạng
đạt được — tức đặt dạng cộng vào điều kiện thuận lợi nhất của nó, thay vì giữ
một ngưỡng duy nhất rồi tuyên bố thắng.

Nếu dạng cộng với theta hiệu chuẩn đuổi kịp gating, phải báo cáo đúng như vậy và
phát biểu lại đóng góp cho chính xác. Đó chính là điều xảy ra.
"""
from __future__ import annotations

import numpy as np

from common import prepared_events, print_table, save_table
from pipeline.config import DEFAULT_CONFIG as C
from pipeline.clustering import run_louvain
from pipeline.metrics import cluster_quality, geographic_spread, noise_handling
from pipeline.weighting import build_weight_matrix, sparsify
from dataclasses import replace

# Ngưỡng "dùng được cho điều phối": cụm xấu nhất phải nằm trong tầm hoạt động
# thực tế của một ca nô. Đặt trước khi xem kết quả.
USABLE_MAX_DIAM_KM = 5.0
# Sàn độ khớp nhãn để một cấu hình được coi là hợp lệ (không chấp nhận đường
# kính nhỏ đạt được bằng cách băm vụn dữ liệu).
USABLE_MIN_ARI = 0.95

# Các dạng trọng số đưa vào so sánh, cùng miền quét theta của riêng nó.
# `slug` là tên file ASCII đặt TƯỜNG MINH: sinh slug tự động từ nhãn tiếng Việt
# tạo ra tên file có dấu (ví dụ `exp13_sweep_additive_chuẩn_hoá_13.json`), gây
# lỗi trên các hệ thống tệp không dùng UTF-8 và làm hỏng tính tái lập.
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


def _evaluate(events, gt, mode, alpha, theta):
    wp = replace(C.weight, edge_threshold=float(theta))
    w = build_weight_matrix(events, wp, mode=mode, alpha=alpha)
    ws = sparsify(w, wp)
    lab = run_louvain(ws, C.cluster.resolution, C.cluster.random_state)
    q = cluster_quality(lab, gt)
    sp = geographic_spread(events, lab)
    nz = noise_handling(lab, gt, noise_label=None)
    return {
        "theta": round(float(theta), 3),
        "ari": q["ari"],
        "nmi": q["nmi"],
        "n_clusters": sp["n_clusters"],
        "mean_diam_km_multi": sp["mean_diameter_km_multi"],
        "max_diam_km": sp["max_diameter_km"],
        "noise_absorbed_pct": nz["noise_absorbed_pct"],
        "n_edges": int(np.count_nonzero(ws) // 2),
    }


def main():
    events = prepared_events()
    gt = [e.gt_cluster for e in events]

    # --- Phần 1: miền giá trị của từng dạng, để thấy confound bằng con số ---
    range_rows = []
    for label, _slug, mode, alpha, _ in FORMS:
        w = build_weight_matrix(events, C.weight, mode=mode, alpha=alpha)
        off = w[~np.eye(len(events), dtype=bool)]
        range_rows.append({
            "form": label,
            "w_min": round(float(off.min()), 4),
            "w_median": round(float(np.median(off)), 4),
            "w_max": round(float(off.max()), 4),
            "frac_pairs_above_0.05": round(float((off > 0.05).mean()), 4),
        })
    print_table("Miền giá trị w_ij theo từng dạng — VÌ SAO cùng một theta không "
                "phải một so sánh công bằng", range_rows)
    print("   Cùng theta = 0,05 giữ lại 100% cặp của dạng cộng nhưng chỉ ~8% cặp")
    print("   của gating: dạng cộng bị đưa vào Louvain như đồ thị gần hoàn chỉnh.")

    # --- Phần 2: quét theta riêng cho từng dạng, lấy cấu hình TỐT NHẤT ---
    best_rows = []
    all_sweeps = {}
    for label, slug, mode, alpha, thetas in FORMS:
        sweep = [_evaluate(events, gt, mode, alpha, t) for t in thetas]
        all_sweeps[slug] = sweep

        usable = [r for r in sweep
                  if r["max_diam_km"] < USABLE_MAX_DIAM_KM and r["ari"] >= USABLE_MIN_ARI]
        best_ari = max(sweep, key=lambda r: r["ari"])
        if usable:
            lo = min(r["theta"] for r in usable)
            hi = max(r["theta"] for r in usable)
            width_ratio = round(hi / lo, 2) if lo > 0 else None
        else:
            lo = hi = width_ratio = None

        best_rows.append({
            "form": label,
            "best_ari": best_ari["ari"],
            "theta_at_best_ari": best_ari["theta"],
            "max_diam_at_best_ari": best_ari["max_diam_km"],
            "n_usable_theta": len(usable),
            "usable_theta_lo": lo,
            "usable_theta_hi": hi,
            "usable_width_ratio": width_ratio,
            "ari_at_published_theta_0.05": next(
                (r["ari"] for r in sweep if abs(r["theta"] - 0.05) < 1e-9), None),
        })

    print_table("Kết quả TỐT NHẤT của từng dạng khi theta được hiệu chuẩn riêng "
                f"(dùng được = max_diam < {USABLE_MAX_DIAM_KM} km VÀ ARI >= {USABLE_MIN_ARI})",
                best_rows)
    print("   Đọc bảng này theo CHIỀU RỘNG cửa sổ dùng được, không theo đỉnh ARI:")
    print("   với theta hiệu chuẩn, dạng cộng ĐUỔI KỊP gating ở đỉnh. Khác biệt")
    print("   thật nằm ở chỗ gating giữ được chất lượng đó trên một dải theta rộng")
    print("   hàng chục lần, còn dạng cộng chỉ đạt trong một khe rất hẹp mà không")
    print("   thể tìm ra nếu không có nhãn ground-truth — thứ mà thảm họa thật")
    print("   không có. Đó mới là phát biểu đóng góp đúng.")

    save_table("exp13_theta_calibration_best.json", best_rows)
    save_table("exp13_theta_ranges.json", range_rows)
    for slug, sweep in all_sweeps.items():
        # slug là ASCII khai tường minh trong FORMS: tên file phải chuyển được
        # giữa các hệ thống, không phụ thuộc dấu tiếng Việt trong nhãn hiển thị.
        save_table(f"exp13_sweep_{slug}.json", sweep)
    print("\n[saved] exp13_*.json -> results/tables/")


if __name__ == "__main__":
    main()
