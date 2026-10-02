"""So sánh ONNX FP32 / INT8 đã xuất trên test độc lập; không quantize lại.

Chạy từ tools/: python compare_fp32_int8.py
Smoke test: python compare_fp32_int8.py --limit 3 --no-plots
Báo cáo mặc định: products/fe/reports/fp32_int8/.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path

from compare_models import (CONFIG_JSON, DATASET_DIR, EDGE_DIR, EXPORT_DIR, REPORTS_DIR, SPLIT_CSV,
                            artifact, check_hash, check_manifest, onnx_runner, prepare_test,
                            sha256, write_comparison)


def verify_int8_pair(fp32: Path, int8: Path, source: dict, quantized: dict,
                     config: dict, split_csv: Path) -> None:
    if fp32.resolve() == int8.resolve():
        raise ValueError("FP32 và INT8 không được là cùng một file.")
    check_manifest(source, config)
    check_manifest(quantized, config)
    check_hash(fp32, source.get("onnx_sha256"))
    check_hash(int8, quantized.get("onnx_sha256"))
    if (not source.get("checkpoint_sha256")
            or source["checkpoint_sha256"] != quantized.get("checkpoint_sha256")
            or source["onnx_sha256"] != quantized.get("source_onnx_sha256")
            or quantized.get("precision") != "int8"
            or quantized.get("split_csv_sha256") != sha256(split_csv)):
        raise ValueError("INT8 không có cùng nguồn FP32/checkpoint/split CSV trong manifest.")
    import onnx
    graph = onnx.load(str(int8))
    operations = {node.op_type for node in graph.graph.node}
    if not {"QuantizeLinear", "DequantizeLinear"}.issubset(operations):
        raise ValueError("Graph INT8 thiếu Q/DQ; cần model QDQ từ quantize_model.py.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fp32", type=Path, default=EXPORT_DIR / "flood_mobilenetv3_large.onnx")
    parser.add_argument("--int8", type=Path, default=EDGE_DIR / "Quantize" / "flood_mobilenetv3_large.int8.onnx")
    parser.add_argument("--manifest", type=Path, default=EXPORT_DIR / "model_manifest.json")
    parser.add_argument("--int8-manifest", type=Path, default=EDGE_DIR / "Quantize" / "model_manifest_int8.json")
    parser.add_argument("--config", type=Path, default=CONFIG_JSON)
    parser.add_argument("--split-csv", type=Path, default=SPLIT_CSV)
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--report-dir", type=Path, default=REPORTS_DIR / "fp32_int8")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()
    config, items, metadata = prepare_test(args.config, args.split_csv, args.dataset_dir, args.limit)
    source = json.loads(args.manifest.read_text(encoding="utf-8"))
    quantized = json.loads(args.int8_manifest.read_text(encoding="utf-8"))
    verify_int8_pair(args.fp32, args.int8, source, quantized, config, args.split_csv)
    metadata.update(manifest_sha256=sha256(args.manifest), int8_manifest_sha256=sha256(args.int8_manifest),
                    quantization=quantized.get("quantization"), calibration_split="train",
                    onnxruntime=importlib.metadata.version("onnxruntime"))
    runners = {"fp32": onnx_runner(args.fp32, config), "int8": onnx_runner(args.int8, config)}
    write_comparison(runners, items, config, {"fp32": artifact(args.fp32), "int8": artifact(args.int8)},
                     metadata, args.report_dir, args.no_plots)


if __name__ == "__main__":
    main()
