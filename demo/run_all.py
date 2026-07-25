"""Chạy toàn bộ pipeline v2 từ đầu tới cuối.

Trình tự:
   1. Sinh bộ dữ liệu synthetic (data/dataset.json)
   2. Thí nghiệm 1: kiểm chứng 6 fix của Mục 4
   3. Thí nghiệm 2: độ nhạy tham số (mở rộng: tau_F/tau_E, beta/gamma)
   4. Thí nghiệm 3: Louvain vs Leiden
   5. Thí nghiệm 4: đối chiếu baseline
   6. Thí nghiệm 5: độ ổn định xếp hạng (Kendall's τ; mở rộng: s, cấu trúc)
   7. Thí nghiệm 6: ablation circularity (S_context ↔ ranking)
   8. Thí nghiệm 7: outcome metric cho equity
   9. Thí nghiệm 8: C_i như bộ phát hiện tin giả + kịch bản đối kháng
  10. Thí nghiệm 9: độ đo phân biệt hơn ARI
  11. Thí nghiệm 10: đo kích thước gói metadata biên (byte)
  12. Thí nghiệm 11: chi phí tính toán theo quy mô (O(n^2) thực nghiệm)
  13. Thí nghiệm 12: đa hạt giống — mean ± sd cho mọi số tiêu đề
  14. Sinh hình vẽ (results/figures/*.png)
  15. Dựng dashboard (dashboard/dashboard.html)

Dùng:  ./.venv/bin/python run_all.py
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

V2_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(V2_ROOT))
sys.path.insert(0, str(V2_ROOT / "experiments"))


def run_module(path: Path, banner: str) -> None:
    print("\n" + "=" * 70)
    print(f"  {banner}")
    print("=" * 70)
    runpy.run_path(str(path), run_name="__main__")


def main() -> None:
    run_module(V2_ROOT / "data" / "generate.py", "1/15  Sinh bộ dữ liệu synthetic")
    run_module(V2_ROOT / "experiments" / "exp1_formula_validation.py", "2/15  Thí nghiệm 1 — Kiểm chứng công thức")
    run_module(V2_ROOT / "experiments" / "exp2_sensitivity.py", "3/15  Thí nghiệm 2 — Độ nhạy tham số")
    run_module(V2_ROOT / "experiments" / "exp3_louvain_vs_leiden.py", "4/15  Thí nghiệm 3 — Louvain vs Leiden")
    run_module(V2_ROOT / "experiments" / "exp4_baselines.py", "5/15  Thí nghiệm 4 — Baseline")
    run_module(V2_ROOT / "experiments" / "exp5_ranking_stability.py", "6/15  Thí nghiệm 5 — Độ ổn định xếp hạng")
    run_module(V2_ROOT / "experiments" / "exp6_context_ablation.py", "7/15  Thí nghiệm 6 — Ablation circularity")
    run_module(V2_ROOT / "experiments" / "exp7_equity_outcome.py", "8/15  Thí nghiệm 7 — Outcome metric equity")
    run_module(V2_ROOT / "experiments" / "exp8_confidence_detector.py", "9/15  Thí nghiệm 8 — C_i phát hiện tin giả")
    run_module(V2_ROOT / "experiments" / "exp9_discriminative_metric.py", "10/15  Thí nghiệm 9 — Độ đo phân biệt")
    run_module(V2_ROOT / "experiments" / "exp10_packet_size.py", "11/15  Thí nghiệm 10 — Kích thước gói metadata")
    run_module(V2_ROOT / "experiments" / "exp11_scaling.py", "12/15  Thí nghiệm 11 — Chi phí theo quy mô")
    run_module(V2_ROOT / "experiments" / "exp12_multiseed.py", "13/15  Thí nghiệm 12 — Đa hạt giống (mean ± sd)")
    run_module(V2_ROOT / "experiments" / "make_figures.py", "14/15  Sinh hình vẽ")
    run_module(V2_ROOT / "dashboard" / "build_dashboard.py", "15/15  Dựng dashboard")
    print("\n" + "=" * 75)
    print("  HOÀN TẤT. Xem results/tables, results/figures, dashboard/dashboard.html")
    print("=" * 75)


if __name__ == "__main__":
    main()
