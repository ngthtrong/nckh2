#!/usr/bin/env python3
"""Kiểm hình trong bài báo có đúng là hình do suite này sinh ra hay không.

Lý do tồn tại: ở loop 13 phát hiện `paper/figures/fig7_ranking_stability.png` là
artifact tồn đọng từ một phiên bản code cũ (khác cả LOẠI biểu đồ: đường vs cột),
trong khi mục Reproducibility của bài khẳng định run_all.py sinh ra "every figure
in this paper". Lỗi đó thoát được 12 vòng phản biện vì không ai so checksum.

Script đọc danh sách hình THỰC SỰ được \\includegraphics trong paper/main.tex,
rồi so MD5 từng hình với bản trong demo/results/figures/. Chỉ kiểm hình bài dùng,
nên fig2_map/fig3_heatmap (artifact trực quan hoá của demo, không nằm trong bài)
không gây báo động giả.

Dùng:  ./.venv/bin/python3 verify_figures.py
Exit code: 0 = mọi hình khớp; 1 = có hình lệch/thiếu.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parent
GENERATED_DIR = DEMO_DIR / "results" / "figures"
PAPER_DIR = REPO_ROOT / "paper" / "figures"
MAIN_TEX = REPO_ROOT / "paper" / "main.tex"

# \includegraphics[...]{figures/fig1_ablation.png}
INCLUDE_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{figures/([^}]+)\}")


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def figures_used_by_paper() -> list[str]:
    if not MAIN_TEX.exists():
        print(f"LỖI: không tìm thấy {MAIN_TEX}")
        sys.exit(1)
    names = INCLUDE_RE.findall(MAIN_TEX.read_text(encoding="utf-8"))
    # giữ thứ tự xuất hiện, bỏ trùng
    seen, ordered = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            ordered.append(n)
    return ordered


def main() -> int:
    used = figures_used_by_paper()
    if not used:
        print("LỖI: không tìm thấy \\includegraphics nào trong main.tex")
        return 1

    print(f"Bài báo dùng {len(used)} hình. Đối chiếu với {GENERATED_DIR.relative_to(REPO_ROOT)}:\n")
    bad = 0
    for name in used:
        gen, paper = GENERATED_DIR / name, PAPER_DIR / name
        if not gen.exists():
            print(f"  MISSING-GEN  {name}  (bài dùng nhưng suite không sinh ra)")
            bad += 1
        elif not paper.exists():
            print(f"  MISSING      {name}  (thiếu trong paper/figures/)")
            bad += 1
        elif md5(gen) != md5(paper):
            print(f"  STALE        {name}  (paper/ lệch với bản suite sinh ra)")
            bad += 1
        else:
            print(f"  OK           {name}")

    # Hình suite sinh ra nhưng bài không dùng: thông tin, không phải lỗi.
    extra = sorted(p.name for p in GENERATED_DIR.glob("*.png") if p.name not in set(used))
    if extra:
        print(f"\nHình của demo không dùng trong bài (bình thường): {', '.join(extra)}")

    # Chiều NGƯỢC LẠI: hình MỒ CÔI trong paper/figures/ — có trong thư mục của bài
    # nhưng không \includegraphics ở đâu. Đây là cảnh báo, không phải lỗi: hình có
    # thể đang chờ được đưa vào bài (fig2_map/fig3_heatmap/fig8_lemma1 ở vòng 17).
    # Vẫn phải in ra, vì một hình mồ côi cũng có thể là dấu hiệu bài BỎ SÓT bằng
    # chứng đã sinh ra được, hoặc còn sót artifact của phiên bản cũ.
    orphans = sorted(p.name for p in PAPER_DIR.glob("*.png") if p.name not in set(used))
    if orphans:
        print(f"\nCẢNH BÁO — hình mồ côi trong paper/figures/ (không được tham chiếu):")
        for name in orphans:
            gen = GENERATED_DIR / name
            tag = ("suite sinh ra được — cân nhắc đưa vào bài" if gen.exists()
                   else "KHÔNG do suite sinh ra — có thể là artifact cũ, nên xoá")
            print(f"  {name}  ({tag})")

    if bad:
        print(f"\nTHẤT BẠI: {bad} hình lệch/thiếu. Chạy make_figures.py rồi copy sang paper/figures/.")
        return 1
    print("\nĐẠT: mọi hình trong bài khớp đúng bản do suite sinh ra.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
