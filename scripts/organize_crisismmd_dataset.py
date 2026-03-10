"""
organize_crisismmd_dataset.py
Organizes CrisisMMD v2.0 images into the project dataset structure.

PREREQUISITES:
  - CrisisMMD v2.0 images downloaded from https://crisisnlp.qcri.org/crisismmd
    and extracted to: dataset/image_data/raw/crisismmd/
    (The images folder should contain data_image/ with event subfolders)
  - Annotation TSVs already in: dataset/image_data/raw/crisismmd_annotations/

Label mapping to 3-class schema (task_damage split):
  severe_damage       → high_flood
  mild_damage         → low_flood
  little_or_no_damage → no_flood
  not_humanitarian    → SKIP (no flood content)

Expects TSV format:
  event_name  tweet_id  image_id  tweet_text  image  label

Where 'image' column contains paths like:
  data_image/hurricane_harvey/8_9_2017/<tweet_id>_0.jpg

Usage:
  python scripts/organize_crisismmd_dataset.py

Optional args:
  --annot-dir    Path to annotation TSVs  (default: dataset/image_data/raw/crisismmd_annotations)
  --image-dir    Path to CrisisMMD images (default: dataset/image_data/raw/crisismmd)
  --output-dir   Output root              (default: dataset/image_data)
"""
import os
import shutil
import argparse
from pathlib import Path

WORKSPACE = Path(r"C:\Users\jhiny\Desktop\nckh2")

DEFAULT_ANNOT_DIR  = WORKSPACE / "dataset" / "image_data" / "raw" / "crisismmd_annotations"
DEFAULT_IMAGE_DIR  = WORKSPACE / "dataset" / "image_data" / "raw" / "crisismmd"
DEFAULT_OUTPUT_DIR = WORKSPACE / "dataset" / "image_data"

LABEL_MAP = {
    "severe_damage":       "high_flood",
    "mild_damage":         "low_flood",
    "little_or_no_damage": "no_flood",
    # Skip these:
    "not_humanitarian":    None,
    "rescue_volunteering_or_donation_effort": None,
    "affected_individuals": None,
    "infrastructure_and_utility_damage": "high_flood",  # map as high
    "vehicle_damage":       "low_flood",                # map as low
    "other_relevant_information": None,
    "not_relevant_or_cant_judge": None,
}

# Only use 'all' split (not 'agreed') to maximize data
SPLIT_FILES = {
    "train": "crisismmd_datasplit_all/task_damage_text_img_train.tsv",
    "val":   "crisismmd_datasplit_all/task_damage_text_img_dev.tsv",
    "test":  "crisismmd_datasplit_all/task_damage_text_img_test.tsv",
}


def parse_tsv_split(tsv_path: Path):
    """Returns list of (image_relative_path, label) tuples."""
    entries = []
    header = None
    with open(tsv_path, encoding="utf-8") as f:
        for line in f:
            cols = line.rstrip("\n").split("\t")
            if header is None:
                header = cols
                continue
            if len(cols) < len(header):
                continue
            row = dict(zip(header, cols))
            img_rel = row.get("image", "").strip()
            label_raw = row.get("label", "").strip()
            if img_rel and label_raw:
                entries.append((img_rel, label_raw))
    return entries


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--annot-dir",  default=str(DEFAULT_ANNOT_DIR))
    parser.add_argument("--image-dir",  default=str(DEFAULT_IMAGE_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    annot_dir  = Path(args.annot_dir) / "all"
    image_dir  = Path(args.image_dir)
    output_dir = Path(args.output_dir)

    print(f"Annotation dir : {annot_dir}")
    print(f"Image dir      : {image_dir}")
    print(f"Output dir     : {output_dir}")

    if not image_dir.exists():
        print(f"\nERROR: Image directory not found: {image_dir}")
        print("Please download CrisisMMD v2.0 images from https://crisisnlp.qcri.org/crisismmd")
        print("and extract them so the path dataset/image_data/raw/crisismmd/data_image/ exists.")
        return

    total_copied = 0
    total_skipped = 0

    for split, tsv_rel in SPLIT_FILES.items():
        tsv_path = annot_dir / tsv_rel
        if not tsv_path.exists():
            print(f"\nWARN: TSV not found: {tsv_path}")
            continue

        entries = parse_tsv_split(tsv_path)
        print(f"\n{'='*50}")
        print(f"Split: {split}  ({len(entries)} rows)")

        copied = skipped = missing = 0
        for img_rel, label_raw in entries:
            label = LABEL_MAP.get(label_raw)
            if label is None:
                skipped += 1
                continue

            # img_rel looks like: data_image/hurricane_harvey/8_9_2017/1234567890_0.jpg
            src = image_dir / img_rel
            if not src.exists():
                missing += 1
                continue

            dst_dir = output_dir / split / label
            dst_dir.mkdir(parents=True, exist_ok=True)

            new_name = f"crisismmd_{src.name}"
            dst = dst_dir / new_name
            if dst.exists():
                skipped += 1
                continue

            shutil.copy2(str(src), str(dst))
            copied += 1

        print(f"  Copied: {copied}  |  Skipped (label/dup): {skipped}  |  Missing images: {missing}")
        total_copied += copied
        total_skipped += skipped

    print(f"\n{'='*50}")
    print(f"TOTAL COPIED: {total_copied}  |  TOTAL SKIPPED: {total_skipped}")

    # Summary per split/class
    print("\nFinal class distribution (STURM + CrisisMMD combined):")
    for split in ["train", "val", "test"]:
        print(f"\n  {split}:")
        for label in ["no_flood", "low_flood", "high_flood"]:
            d = output_dir / split / label
            if d.exists():
                n = len(list(d.glob("*.jpg")) + list(d.glob("*.jpeg")) + list(d.glob("*.png")))
                print(f"    {label}: {n}")


if __name__ == "__main__":
    main()
