"""Build the downloadable on-device benchmark package from the test split."""

import csv
import hashlib
import json
import struct
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
FE = ROOT / "products" / "fe"
MODEL = FE / "model" / "Edge Ai"
IMAGE_ROOT = FE / "model" / "Dataset_Flood"
SPLIT_CSV = MODEL / "split_train_val_test_mobilenetv3_large.csv"
OUTPUT = Path(__file__).with_name("benchmark_package.rhb")
LABELS = ("low", "medium", "high", "non_flood")
MAGIC = b"RHB1"


def main() -> None:
    files = []
    for row in csv.DictReader(SPLIT_CSV.open(encoding="utf-8-sig", newline="")):
        if row["split"].strip().lower() != "test":
            continue
        label = row["label"].strip().lower()
        relative = PurePosixPath(row["relative_path"].replace("\\", "/"))
        if (label not in LABELS or relative.is_absolute() or not relative.parts
                or relative.parts[0] != label or ".." in relative.parts):
            raise ValueError(f"Unsafe or unsupported test row: {row['relative_path']}")
        source = IMAGE_ROOT.joinpath(*relative.parts)
        if not source.is_file():
            raise FileNotFoundError(source)
        if source.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise ValueError(f"Unsupported image: {relative}")
        files.append((source, {
            "id": hashlib.sha1(relative.as_posix().encode("utf-8")).hexdigest()[:12],
            "label": label,
            "length": source.stat().st_size,
        }))

    if not files or {sample["label"] for _, sample in files} != set(LABELS):
        raise ValueError("CSV test split is empty or missing a class")

    manifest = {
        "datasetName": "MobileNetV3 dataset v4, seed 42",
        "split": "test",
        "labels": list(LABELS),
        "samples": [sample for _, sample in files],
    }
    previous_header_length = -1
    while True:
        position = 8 + previous_header_length
        for _, sample in files:
            sample["offset"] = position
            position += sample["length"]
        header = json.dumps(manifest, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(header) == previous_header_length:
            break
        previous_header_length = len(header)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("wb") as package:
        package.write(MAGIC)
        package.write(struct.pack(">I", len(header)))
        package.write(header)
        for source, _ in files:
            with source.open("rb") as image:
                while chunk := image.read(1024 * 1024):
                    package.write(chunk)
    with OUTPUT.open("rb") as package:
        if package.read(4) != MAGIC:
            raise RuntimeError("Benchmark package magic is invalid")
        header_length = struct.unpack(">I", package.read(4))[0]
        built_manifest = json.loads(package.read(header_length))
        package_length = OUTPUT.stat().st_size
        if any(sample["offset"] + sample["length"] > package_length
               for sample in built_manifest["samples"]):
            raise RuntimeError("Benchmark package contains an out-of-range image")
    print(f"Built {OUTPUT.name}: {len(files)} images, {OUTPUT.stat().st_size / 1048576:.1f} MiB")


if __name__ == "__main__":
    main()
