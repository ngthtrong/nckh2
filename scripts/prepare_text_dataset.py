#!/usr/bin/env python3
"""Prepare text dataset splits from labeled CSV.

Expected input columns:
- id, raw_text, clean_text, urgency_label, source, event, location_hint
"""

from __future__ import annotations

import argparse
import csv
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

LABELS = {"urgent_rescue", "need_supplies", "safe_update", "irrelevant"}

TEENCODE_MAP = {
    "ko": "khong",
    "k": "khong",
    "dc": "duoc",
    "mn": "moi_nguoi",
    "mik": "minh",
}


@dataclass
class TextSample:
    sid: str
    raw_text: str
    clean_text: str
    label: str
    source: str
    event: str
    location_hint: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare text dataset splits")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=Path("dataset/text_data/rescue_text_samples_template.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("dataset/text_data/processed"),
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    return parser.parse_args()


def normalize_text(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"https?://\\S+", " ", t)
    t = re.sub(r"\\+?\\d[\\d\\s.-]{7,}", " <phone> ", t)
    t = re.sub(r"[^\\w\\s<>]", " ", t, flags=re.UNICODE)
    parts = []
    for tok in t.split():
        parts.append(TEENCODE_MAP.get(tok, tok))
    return " ".join(parts)


def load_samples(path: Path) -> List[TextSample]:
    if not path.exists():
        raise FileNotFoundError(f"Input CSV not found: {path}")

    out: List[TextSample] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = (row.get("urgency_label") or row.get("final_label") or "").strip()
            if label not in LABELS:
                continue
            raw = (row.get("raw_text") or "").strip()
            clean = (row.get("clean_text") or "").strip() or normalize_text(raw)
            sid = (row.get("id") or "").strip()
            if not sid or not raw:
                continue
            out.append(
                TextSample(
                    sid=sid,
                    raw_text=raw,
                    clean_text=clean,
                    label=label,
                    source=(row.get("source") or "unknown_source").strip() or "unknown_source",
                    event=(row.get("event") or "unknown_event").strip() or "unknown_event",
                    location_hint=(row.get("location_hint") or "unknown_location").strip() or "unknown_location",
                )
            )
    return out


def split_data(samples: List[TextSample], seed: int, train_ratio: float, val_ratio: float, test_ratio: float) -> Dict[str, List[TextSample]]:
    if abs((train_ratio + val_ratio + test_ratio) - 1.0) > 1e-6:
        raise ValueError("Split ratios must sum to 1.0")

    rng = random.Random(seed)
    by_label: Dict[str, List[TextSample]] = defaultdict(list)
    for s in samples:
        by_label[s.label].append(s)

    result: Dict[str, List[TextSample]] = {"train": [], "val": [], "test": []}
    for label, rows in by_label.items():
        rng.shuffle(rows)
        n = len(rows)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)

        result["train"].extend(rows[:n_train])
        result["val"].extend(rows[n_train : n_train + n_val])
        result["test"].extend(rows[n_train + n_val :])

    return result


def export_split_csv(split_rows: Dict[str, List[TextSample]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    headers = ["id", "raw_text", "clean_text", "urgency_label", "source", "event", "location_hint"]
    for split_name, rows in split_rows.items():
        out_file = out_dir / f"{split_name}.csv"
        with out_file.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for r in rows:
                writer.writerow([r.sid, r.raw_text, r.clean_text, r.label, r.source, r.event, r.location_hint])


def write_stats(split_rows: Dict[str, List[TextSample]], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    total = sum(len(v) for v in split_rows.values())

    lines = [
        "# Text Dataset Stats",
        "",
        f"- Total samples: {total}",
    ]

    for split_name in ("train", "val", "test"):
        c = Counter(r.label for r in split_rows[split_name])
        lines.extend([
            "",
            f"## Split: {split_name}",
            f"- samples: {len(split_rows[split_name])}",
            f"- urgent_rescue: {c.get('urgent_rescue', 0)}",
            f"- need_supplies: {c.get('need_supplies', 0)}",
            f"- safe_update: {c.get('safe_update', 0)}",
            f"- irrelevant: {c.get('irrelevant', 0)}",
        ])

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    input_csv = (repo_root / args.input_csv).resolve()
    output_dir = (repo_root / args.output_dir).resolve()

    samples = load_samples(input_csv)
    if not samples:
        raise RuntimeError("No valid text rows found. Check labels and required columns.")

    splits = split_data(samples, args.seed, args.train_ratio, args.val_ratio, args.test_ratio)
    export_split_csv(splits, output_dir)

    stats_path = repo_root / "dataset" / "reports" / "text_stats.md"
    write_stats(splits, stats_path)

    print(f"Prepared {sum(len(v) for v in splits.values())} text samples")
    print(f"Output directory: {output_dir}")
    print(f"Stats report: {stats_path}")


if __name__ == "__main__":
    main()
