"""Smoke test PTH trên 3 ảnh test thật, ưu tiên khác lớp; không train/export.

Từ tools/: python test/smoke_test_v2.py
Mặc định lấy checkpoint/config/split trong model/Edge Ai.
PASS chỉ xác nhận inference hợp lệ, không phải accuracy 100% hay full-test metric.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Cho phép chạy trực tiếp file trong test/ từ bất kỳ working directory nào.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from compare_models import (CONFIG_JSON, DATASET_DIR, EDGE_DIR, SPLIT_CSV,
                            evaluate_models, prepare_test, pth_runner)
from convert_model import inference_contract


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--checkpoint", type=Path, default=EDGE_DIR / "flood_mobilenetv3_large_best.pth")
    parser.add_argument("--config", type=Path, default=CONFIG_JSON)
    parser.add_argument("--split-csv", type=Path, default=SPLIT_CSV)
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args(argv)
    if args.limit <= 0:
        parser.error("--limit phải > 0.")

    config, test, _ = prepare_test(args.config, args.split_csv, args.dataset_dir, None)
    contract = inference_contract(config)
    by_label = {}
    for item in test:
        by_label.setdefault(item[1], item)
    representatives = [by_label[label] for label in range(len(config["class_order"])) if label in by_label]
    samples = (representatives + [item for item in test if item not in representatives])[:args.limit]
    if len(samples) != args.limit:
        raise ValueError(f"Test chỉ có {len(samples)} ảnh, không đủ --limit={args.limit}.")

    # Dùng đúng builder/load strict và EXIF -> letterbox BILINEAR -> ImageNet.
    _, _, rows = evaluate_models({"pth": pth_runner(args.checkpoint, config)}, samples, config)
    if len(rows) != len(samples):
        raise RuntimeError(f"Chỉ xử lý {len(rows)}/{len(samples)} ảnh; không được bỏ qua ảnh lỗi.")
    for row in rows:
        print(f"{row['image_path']}: true={row['ground_truth']}, pred={row['pred_pth']}, "
              f"confidence={row['confidence_pth']:.4f}, input=(1, 3, {contract['input_size']}, {contract['input_size']})")
    print(f"checkpoint={args.checkpoint.resolve()}")
    print(f"smoke_test=PASS ({len(rows)}/{len(samples)} inference hợp lệ; không phải full-test accuracy)")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("smoke_test=FAIL", file=sys.stderr)
        raise
