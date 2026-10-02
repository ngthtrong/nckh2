"""Compare ONNX FP32, post-training INT8 (PTQ), and QAT ONNX on one saved test split.

Run from tools/: python compare_fp32_ptq_qat.py
Smoke test: python compare_fp32_ptq_qat.py --limit 3 --no-plots
Reports: products/fe/reports/fp32_ptq_qat/.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from compare_models import (CONFIG_JSON, DATASET_DIR, EDGE_DIR, EXPORT_DIR, REPORTS_DIR,
                            SPLIT_CSV, artifact, check_hash, check_manifest, onnx_runner,
                            prepare_test, sha256, write_comparison)

PTQ_DIR = EDGE_DIR / "Quantize"
QAT_DIR = EDGE_DIR / "QAT"


def require_qdq(path: Path) -> None:
    import onnx

    graph = onnx.load(str(path))
    onnx.checker.check_model(graph)
    operations = {node.op_type for node in graph.graph.node}
    if not {"QuantizeLinear", "DequantizeLinear"}.issubset(operations):
        raise ValueError(f"Model thiếu Q/DQ nodes: {path}")


def verify_lineage(fp32: Path, ptq: Path, qat: Path, qat_checkpoint: Path, source: dict, ptq_manifest: dict,
                   qat_manifest: dict, config: dict, split_csv: Path) -> None:
    if len({fp32.resolve(), ptq.resolve(), qat.resolve()}) != 3:
        raise ValueError("FP32, PTQ và QAT phải là ba file khác nhau.")
    for path, manifest in ((fp32, source), (ptq, ptq_manifest), (qat, qat_manifest)):
        check_manifest(manifest, config)
        check_hash(path, manifest.get("onnx_sha256"))

    split_hash = sha256(split_csv)
    source_checkpoint = source.get("checkpoint_sha256")
    source_hash = source.get("onnx_sha256")
    if not source_checkpoint or not source_hash:
        raise ValueError("Manifest FP32 thiếu hash checkpoint/ONNX.")
    if (ptq_manifest.get("checkpoint_sha256") != source_checkpoint
            or ptq_manifest.get("source_onnx_sha256") != source_hash
            or ptq_manifest.get("split_csv_sha256") != split_hash
            or ptq_manifest.get("precision") != "int8"):
        raise ValueError("PTQ không thuộc cùng checkpoint, ONNX FP32 và split CSV.")
    if (qat_manifest.get("checkpoint_sha256") != source_checkpoint
            or qat_manifest.get("source_onnx_sha256") != source_hash
            or qat_manifest.get("split_csv_sha256") != split_hash
            or qat_manifest.get("precision") != "int8_qat"):
        raise ValueError("QAT không thuộc cùng checkpoint, ONNX FP32 và split CSV.")
    check_hash(qat_checkpoint, qat_manifest.get("qat_checkpoint_sha256"))
    require_qdq(ptq)
    require_qdq(qat)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fp32", type=Path, default=EXPORT_DIR / "flood_mobilenetv3_large.onnx")
    parser.add_argument("--ptq", type=Path, default=PTQ_DIR / "flood_mobilenetv3_large.int8.onnx")
    parser.add_argument("--qat", type=Path, default=QAT_DIR / "flood_mobilenetv3_large.qat.int8.onnx")
    parser.add_argument("--qat-checkpoint", type=Path, default=QAT_DIR / "flood_mobilenetv3_large_qat_best.pth")
    parser.add_argument("--manifest", type=Path, default=EXPORT_DIR / "model_manifest.json")
    parser.add_argument("--ptq-manifest", type=Path, default=PTQ_DIR / "model_manifest_int8.json")
    parser.add_argument("--qat-manifest", type=Path, default=QAT_DIR / "model_manifest_qat.json")
    parser.add_argument("--config", type=Path, default=CONFIG_JSON)
    parser.add_argument("--split-csv", type=Path, default=SPLIT_CSV)
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--report-dir", type=Path, default=REPORTS_DIR / "fp32_ptq_qat")
    parser.add_argument("--limit", type=int, help="smoke subset only; not final evaluation")
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()

    config, items, metadata = prepare_test(args.config, args.split_csv, args.dataset_dir, args.limit)
    source = json.loads(args.manifest.read_text(encoding="utf-8"))
    ptq_manifest = json.loads(args.ptq_manifest.read_text(encoding="utf-8"))
    qat_manifest = json.loads(args.qat_manifest.read_text(encoding="utf-8"))
    verify_lineage(args.fp32, args.ptq, args.qat, args.qat_checkpoint, source, ptq_manifest, qat_manifest,
                   config, args.split_csv)

    metadata.update(
        evaluation="same held-out test split for ONNX FP32, PTQ INT8, and QAT INT8",
        fp32_manifest_sha256=sha256(args.manifest),
        ptq_manifest_sha256=sha256(args.ptq_manifest),
        qat_manifest_sha256=sha256(args.qat_manifest),
        ptq_quantization=ptq_manifest.get("quantization"),
        qat_quantization=qat_manifest.get("quantization"),
        qat_best_epoch=qat_manifest.get("qat_best_epoch"),
        qat_validation_metrics=qat_manifest.get("validation_metrics"),
    )
    runners = {
        "onnx_fp32": onnx_runner(args.fp32, config),
        "ptq_int8": onnx_runner(args.ptq, config),
        "qat_int8": onnx_runner(args.qat, config),
    }
    write_comparison(
        runners, items, config,
        {"onnx_fp32": artifact(args.fp32), "ptq_int8": artifact(args.ptq),
         "qat_int8": artifact(args.qat)},
        metadata, args.report_dir, args.no_plots,
    )


if __name__ == "__main__":
    main()
