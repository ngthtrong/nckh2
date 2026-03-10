#!/usr/bin/env python3
"""Prepare image dataset from metadata CSV.

Steps:
1. Validate metadata rows.
2. Resize images to target size.
3. Split into train/val/test with event-group aware split.
4. Export split_manifest.csv and simple stats report.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import random
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

LABELS = {"no_flood", "low_flood", "high_flood"}


@dataclass
class Sample:
    sample_id: str
    file_path: Path
    mapped_label: str
    event: str
    source: str
    is_vietnam: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare image dataset splits from metadata")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Project root")
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("dataset/metadata.csv"),
        help="Path to metadata CSV relative to repo root",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("dataset/image_data/processed"),
        help="Output processed dir relative to repo root",
    )
    parser.add_argument("--image-size", type=int, default=224, help="Output image size")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    return parser.parse_args()


def load_samples(repo_root: Path, metadata_path: Path) -> List[Sample]:
    samples: List[Sample] = []
    full_metadata = repo_root / metadata_path
    if not full_metadata.exists():
        raise FileNotFoundError(f"Metadata file not found: {full_metadata}")

    with full_metadata.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = (row.get("mapped_label") or "").strip()
            quality = (row.get("quality_flag") or "ok").strip().lower()
            if label not in LABELS:
                continue
            if quality in {"bad", "unusable", "drop"}:
                continue

            rel_path = Path((row.get("file_path") or "").strip())
            sample = Sample(
                sample_id=(row.get("sample_id") or "").strip(),
                file_path=repo_root / rel_path,
                mapped_label=label,
                event=(row.get("event") or "unknown_event").strip() or "unknown_event",
                source=(row.get("source") or "unknown_source").strip() or "unknown_source",
                is_vietnam=(row.get("is_vietnam") or "0").strip(),
            )
            if sample.sample_id and sample.file_path.exists():
                samples.append(sample)
    return samples


def grouped_split(
    samples: List[Sample],
    seed: int,
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
) -> Dict[str, List[Sample]]:
    if abs((train_ratio + val_ratio + test_ratio) - 1.0) > 1e-6:
        raise ValueError("Split ratios must sum to 1.0")

    rng = random.Random(seed)
    by_label_events: Dict[str, Dict[str, List[Sample]]] = defaultdict(lambda: defaultdict(list))
    for s in samples:
        by_label_events[s.mapped_label][s.event].append(s)

    result: Dict[str, List[Sample]] = {"train": [], "val": [], "test": []}

    for label, event_map in by_label_events.items():
        events = list(event_map.keys())
        rng.shuffle(events)

        total = sum(len(event_map[e]) for e in events)
        train_target = int(total * train_ratio)
        val_target = int(total * val_ratio)

        train_count = 0
        val_count = 0

        for event in events:
            block = event_map[event]
            if train_count < train_target:
                result["train"].extend(block)
                train_count += len(block)
            elif val_count < val_target:
                result["val"].extend(block)
                val_count += len(block)
            else:
                result["test"].extend(block)

    return result


def clear_existing_outputs(out_dir: Path) -> None:
    for split in ("train", "val", "test"):
        for label in LABELS:
            target = out_dir / split / label
            if target.exists():
                for f in target.glob("*"):
                    if f.is_file():
                        f.unlink()


def write_image(src: Path, dst: Path, image_size: int) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        rgb = img.convert("RGB")
        resized = rgb.resize((image_size, image_size), Image.Resampling.LANCZOS)
        resized.save(dst, format="JPEG", quality=92)


def short_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def export_processed(
    splits: Dict[str, List[Sample]],
    out_dir: Path,
    image_size: int,
    manifest_path: Path,
) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "sample_id",
            "split",
            "label",
            "event",
            "source",
            "is_vietnam",
            "src_path",
            "dst_path",
        ])

        for split_name, items in splits.items():
            for item in items:
                base_name = f"{item.sample_id}_{short_hash(str(item.file_path))}.jpg"
                dst = out_dir / split_name / item.mapped_label / base_name
                write_image(item.file_path, dst, image_size)
                writer.writerow(
                    [
                        item.sample_id,
                        split_name,
                        item.mapped_label,
                        item.event,
                        item.source,
                        item.is_vietnam,
                        str(item.file_path),
                        str(dst),
                    ]
                )


def write_stats_report(splits: Dict[str, List[Sample]], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    total = sum(len(v) for v in splits.values())
    overall = Counter(s.mapped_label for items in splits.values() for s in items)

    lines = [
        "# Image Dataset Stats",
        "",
        f"- Total samples: {total}",
        "",
        "## Overall label counts",
    ]
    for label in sorted(LABELS):
        lines.append(f"- {label}: {overall.get(label, 0)}")

    for split_name in ("train", "val", "test"):
        counts = Counter(s.mapped_label for s in splits[split_name])
        lines.extend([
            "",
            f"## Split: {split_name}",
            f"- samples: {len(splits[split_name])}",
            f"- no_flood: {counts.get('no_flood', 0)}",
            f"- low_flood: {counts.get('low_flood', 0)}",
            f"- high_flood: {counts.get('high_flood', 0)}",
        ])

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    metadata = args.metadata
    out_dir = (repo_root / args.output_dir).resolve()

    samples = load_samples(repo_root, metadata)
    if not samples:
        raise RuntimeError("No valid samples found. Check metadata paths and labels.")

    splits = grouped_split(
        samples,
        seed=args.seed,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
    )

    clear_existing_outputs(out_dir)

    manifest = repo_root / "dataset" / "reports" / "image_split_manifest.csv"
    export_processed(splits, out_dir, args.image_size, manifest)

    stats_report = repo_root / "dataset" / "reports" / "image_stats.md"
    write_stats_report(splits, stats_report)

    print(f"Prepared {sum(len(v) for v in splits.values())} images")
    print(f"Manifest: {manifest}")
    print(f"Report: {stats_report}")


if __name__ == "__main__":
    main()
