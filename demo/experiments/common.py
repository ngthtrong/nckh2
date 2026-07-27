"""Tiện ích dùng chung cho các script thí nghiệm.

Ngoài I/O bảng, module này giữ HẠ TẦNG THỐNG KÊ dùng chung (P2.5 — phản biện §8:
"cả bài chỉ có một chỗ có CI"). Mọi thí nghiệm báo cáo một con số so sánh phải
lấy khoảng tin cậy từ đây, không tự cài lại.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable, Sequence

import numpy as np

V2_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(V2_ROOT))

from data.generate import load_events  # noqa: E402
from pipeline.attributes import compute_confidence  # noqa: E402
from pipeline.config import DEFAULT_CONFIG  # noqa: E402

DATASET = V2_ROOT / "data" / "dataset.json"
TABLES = V2_ROOT / "results" / "tables"
FIGURES = V2_ROOT / "results" / "figures"


def prepared_events():
    """Đọc dataset và điền C_i (dùng chung mọi thí nghiệm)."""
    events = load_events(DATASET)
    compute_confidence(events, DEFAULT_CONFIG.confidence)
    return events


def save_table(name: str, rows: list[dict]) -> Path:
    TABLES.mkdir(parents=True, exist_ok=True)
    path = TABLES / name
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def bootstrap_ci(
    values: Sequence[float],
    stat_fn: Callable[[np.ndarray], float] = np.mean,
    n: int = 2000,
    alpha: float = 0.05,
    seed: int = 42,
) -> tuple[float, float]:
    """Khoảng tin cậy bootstrap phần trăm (percentile) cho `stat_fn` của `values`.

    Lấy mẫu lại CÓ HOÀN LẠI `n` lần trên chính `values`, tính `stat_fn` mỗi lần,
    rồi trả về phân vị [alpha/2, 1-alpha/2]. Mặc định alpha = 0,05 -> CI 95%.

    Đây là phương pháp phi tham số: không giả định phân bố chuẩn, phù hợp với
    ARI/AUC/thời gian đến (các đại lượng bị chặn hoặc lệch mạnh). Với cỡ mẫu nhỏ
    (< 10) CI sẽ rất rộng — đó là thông tin đúng, không phải khuyết điểm; bài báo
    phải in CI rộng thay vì in 4 chữ số ý nghĩa không có bất định.
    """
    arr = np.asarray(list(values), dtype=float)
    if arr.size == 0:
        return (float("nan"), float("nan"))
    if arr.size == 1:
        v = float(stat_fn(arr))
        return (v, v)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, arr.size, size=(n, arr.size))
    stats = np.array([float(stat_fn(arr[row])) for row in idx])
    lo = float(np.percentile(stats, 100.0 * alpha / 2.0))
    hi = float(np.percentile(stats, 100.0 * (1.0 - alpha / 2.0)))
    return (round(lo, 4), round(hi, 4))


def paired_test(a: Sequence[float], b: Sequence[float], seed: int = 42) -> dict:
    """So sánh GHÉP CẶP hai phương pháp trên cùng tập hạt giống.

    Trả về:
      - `mean_diff`     : trung bình (a - b);
      - `diff_ci_lo/hi` : CI bootstrap 95% của hiệu — nếu CI CHỨA 0 thì kết luận
        đúng là "KHÔNG có bằng chứng khác biệt", không được báo cáo con số hiệu
        như một cải thiện;
      - `wilcoxon_stat` / `wilcoxon_p` : kiểm định dấu-hạng Wilcoxon (phi tham số,
        không giả định chuẩn). `None` nếu mọi hiệu đều bằng 0 hoặc cỡ mẫu quá nhỏ;
      - `n_pairs`, `n_a_better`, `contains_zero`.

    Ghép cặp là bắt buộc: gating và additive chạy trên CÙNG một hạt giống chia sẻ
    toàn bộ biến thiên của dữ liệu, nên kiểm định không ghép cặp sẽ đánh giá thấp
    hiệu lực một cách vô cớ.
    """
    x = np.asarray(list(a), dtype=float)
    y = np.asarray(list(b), dtype=float)
    if x.size != y.size:
        raise ValueError(f"paired_test cần cùng cỡ mẫu: {x.size} vs {y.size}")
    d = x - y
    lo, hi = bootstrap_ci(d, np.mean, seed=seed)
    stat: float | None = None
    pval: float | None = None
    if d.size >= 3 and np.any(d != 0):
        try:
            from scipy.stats import wilcoxon
            res = wilcoxon(x, y, zero_method="wilcox")
            stat, pval = float(res.statistic), float(res.pvalue)
        except Exception:
            stat, pval = None, None
    return {
        "n_pairs": int(d.size),
        "mean_a": round(float(np.mean(x)), 4),
        "mean_b": round(float(np.mean(y)), 4),
        "mean_diff": round(float(np.mean(d)), 4),
        "diff_ci_lo": lo,
        "diff_ci_hi": hi,
        "contains_zero": bool(lo <= 0.0 <= hi),
        "n_a_better": int(np.sum(d > 0)),
        "n_ties": int(np.sum(d == 0)),
        "wilcoxon_stat": None if stat is None else round(stat, 4),
        "wilcoxon_p": None if pval is None else round(pval, 6),
    }


def multi_seed(fn: Callable[[int], object], seeds: Sequence[int] = range(20)) -> list:
    """Chạy `fn(seed)` trên nhiều hạt giống, trả list kết quả (bỏ qua None).

    Cơ chế đa hạt giống dùng CHUNG cho Thí nghiệm 5/7/12 — trước đây chỉ Thí
    nghiệm 12 có, nên mọi con số khác chỉ đến từ một lần chạy (phản biện §8).
    """
    out = []
    for s in seeds:
        r = fn(int(s))
        if r is not None:
            out.append(r)
    return out


def print_table(title: str, rows: list[dict]) -> None:
    print(f"\n=== {title} ===")
    if not rows:
        print("(empty)")
        return
    cols = list(rows[0].keys())
    widths = {c: max(len(str(c)), max(len(str(r.get(c, ""))) for r in rows)) for c in cols}
    header = " | ".join(str(c).ljust(widths[c]) for c in cols)
    print(header)
    print("-" * len(header))
    for r in rows:
        print(" | ".join(str(r.get(c, "")).ljust(widths[c]) for c in cols))
