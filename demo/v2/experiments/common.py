"""Tiện ích dùng chung cho các script thí nghiệm."""
from __future__ import annotations

import json
import sys
from pathlib import Path

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
