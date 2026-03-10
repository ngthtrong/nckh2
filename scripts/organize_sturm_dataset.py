"""
organize_sturm_dataset.py
Organizes STURM-FloodDepth images into the project dataset structure.

Level mapping to 3-class schema:
  Level0            → no_flood     (no visible water on vehicle)
  Level1 + Level2   → low_flood    (water up to tire/chassis)
  Level3 + Level4   → high_flood   (water at window level or above)

Output:
  dataset/image_data/
    train/  no_flood/  low_flood/  high_flood/
    val/    no_flood/  low_flood/  high_flood/
    test/   no_flood/  low_flood/  high_flood/
"""
import os
import shutil
from pathlib import Path

WORKSPACE = Path(r"C:\Users\jhiny\Desktop\nckh2")
STURM_ROOT = WORKSPACE / "dataset" / "image_data" / "raw" / "sturm_flood_depth"
IMAGE_ROOT = STURM_ROOT / "upscaled_images"
SPLITS = {
    "train": STURM_ROOT / "train.txt",
    "val":   STURM_ROOT / "val.txt",
    "test":  STURM_ROOT / "test.txt",
}
OUTPUT_ROOT = WORKSPACE / "dataset" / "image_data"

SOURCE = "sturm"  # prefix for files to avoid name collisions

LEVEL_MAP = {
    "Level0": "no_flood",
    "Level1": "low_flood",
    "Level2": "low_flood",
    "Level3": "high_flood",
    "Level4": "high_flood",
}


def get_class(filepath_str: str) -> str | None:
    """Extract class label from a split file line like 'Level2\\car-xxx.jpg'."""
    for level, label in LEVEL_MAP.items():
        if f"\\{level}\\" in filepath_str or f"/{level}/" in filepath_str \
                or filepath_str.startswith(f"{level}\\") or filepath_str.startswith(f"{level}/"):
            return label
    return None


def get_level(filepath_str: str) -> str | None:
    for level in LEVEL_MAP:
        if level in filepath_str:
            return level
    return None


def main():
    total_copied = 0
    summary = {}

    for split, split_file in SPLITS.items():
        print(f"\n{'='*50}")
        print(f"Processing split: {split}")
        with open(split_file) as f:
            lines = [l.strip() for l in f if l.strip()]

        copied = 0
        skipped = 0
        for line in lines:
            label = get_class(line)
            level = get_level(line)
            if label is None or level is None:
                print(f"  WARN: cannot parse label from '{line}'")
                skipped += 1
                continue

            # Construct source path - the split file uses e.g. "Level2\car-xxx.jpg"
            # Normalize path separators
            clean_line = line.replace("\\", os.sep).replace("/", os.sep)
            src = IMAGE_ROOT / clean_line

            if not src.exists():
                print(f"  MISS: {src}")
                skipped += 1
                continue

            dst_dir = OUTPUT_ROOT / split / label
            dst_dir.mkdir(parents=True, exist_ok=True)

            # Rename: sturm_<level>_<original_filename>
            new_name = f"sturm_{src.name}"
            dst = dst_dir / new_name

            if dst.exists():
                skipped += 1
                continue

            shutil.copy2(str(src), str(dst))
            copied += 1

        print(f"  Copied: {copied}  |  Skipped/missing: {skipped}")
        summary[split] = copied
        total_copied += copied

    print(f"\n{'='*50}")
    print(f"TOTAL COPIED: {total_copied}")

    # Print class distribution per split
    print("\nClass distribution in output:")
    for split in ["train", "val", "test"]:
        print(f"\n  {split}:")
        for label in ["no_flood", "low_flood", "high_flood"]:
            d = OUTPUT_ROOT / split / label
            if d.exists():
                n = len(list(d.glob("sturm_*.jpg")))
                print(f"    {label}: {n}")


if __name__ == "__main__":
    main()
