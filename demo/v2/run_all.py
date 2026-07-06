"""Chạy toàn bộ pipeline v2 từ đầu tới cuối.

Trình tự:
  1. Sinh bộ dữ liệu synthetic (data/dataset.json)
  2. Thí nghiệm 1: kiểm chứng 4 fix của Mục 4
  3. Thí nghiệm 2: độ nhạy tham số
  4. Thí nghiệm 3: Louvain vs Leiden
  5. Thí nghiệm 4: đối chiếu baseline
  6. Sinh hình vẽ (results/figures/*.png)
  7. Dựng dashboard (dashboard/dashboard.html)

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
    run_module(V2_ROOT / "data" / "generate.py", "1/7  Sinh bộ dữ liệu synthetic")
    run_module(V2_ROOT / "experiments" / "exp1_formula_validation.py", "2/7  Thí nghiệm 1 — Kiểm chứng công thức")
    run_module(V2_ROOT / "experiments" / "exp2_sensitivity.py", "3/7  Thí nghiệm 2 — Độ nhạy tham số")
    run_module(V2_ROOT / "experiments" / "exp3_louvain_vs_leiden.py", "4/7  Thí nghiệm 3 — Louvain vs Leiden")
    run_module(V2_ROOT / "experiments" / "exp4_baselines.py", "5/7  Thí nghiệm 4 — Baseline")
    run_module(V2_ROOT / "experiments" / "make_figures.py", "6/7  Sinh hình vẽ")
    run_module(V2_ROOT / "dashboard" / "build_dashboard.py", "7/7  Dựng dashboard")
    print("\n" + "=" * 70)
    print("  HOÀN TẤT. Xem results/tables, results/figures, dashboard/dashboard.html")
    print("=" * 70)


if __name__ == "__main__":
    main()
