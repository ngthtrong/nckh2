"""Compare original vs structured-pruned models using PTH/ONNX/PTE on test."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from compare_models import (
    CONFIG_JSON, DATASET_DIR, EDGE_DIR, EXPORT_DIR, REPORTS_DIR, SPLIT_CSV, artifact,
    check_hash, check_manifest, onnx_runner, pte_runner, pth_runner,
    prepare_test, write_comparison,
)
from compare_structured_pruning import load_structured_runner
from quantize_model import sha256


DEFAULT_CHECKPOINT = EDGE_DIR / "flood_mobilenetv3_large_best.pth"
DEFAULT_STRUCTURED_CHECKPOINT = EDGE_DIR / "flood_mobilenetv3_large_structured_best.pt"
DEFAULT_EXPORT_DIR = EDGE_DIR / "Export" / "pruning_st"
DEFAULT_MANIFEST = DEFAULT_EXPORT_DIR / "model_manifest.json"
DEFAULT_REPORT_DIR = REPORTS_DIR
LOGGER = logging.getLogger("benchmark_structured_exports")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--baseline-onnx", type=Path, default=EXPORT_DIR / "flood_mobilenetv3_large.onnx")
    parser.add_argument("--baseline-pte", type=Path, default=EXPORT_DIR / "flood_mobilenetv3_large.pte")
    parser.add_argument("--baseline-manifest", type=Path, default=EXPORT_DIR / "model_manifest.json")
    parser.add_argument("--structured-checkpoint", type=Path, default=DEFAULT_STRUCTURED_CHECKPOINT)
    parser.add_argument("--onnx", type=Path, default=DEFAULT_EXPORT_DIR / "flood_mobilenetv3_large_structured.onnx")
    parser.add_argument("--pte", type=Path, default=DEFAULT_EXPORT_DIR / "flood_mobilenetv3_large_structured.pte")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--config", type=Path, default=CONFIG_JSON)
    parser.add_argument("--split-csv", type=Path, default=SPLIT_CSV)
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--skip-pte", action="store_true", help="benchmark original/pruned PTH and ONNX only")
    parser.add_argument("--limit", type=int, help="smoke subset of test; not a final metric")
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not args.manifest.is_file():
        command = (
            f'python export_structured_model.py --checkpoint "{args.structured_checkpoint}" '
            f'--source-checkpoint "{args.checkpoint}" --config "{args.config}" '
            f'--output-dir "{args.manifest.parent}" --manifest "{args.manifest}" '
            f'--format {"onnx" if args.skip_pte else "all"}'
        )
        parser.error(f"Chưa có manifest model pruned: {args.manifest}\nHãy export trước:\n{command}")

    args.report_dir.mkdir(parents=True, exist_ok=True)
    log_path = args.report_dir / "benchmark.log"
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_path, mode="w", encoding="utf-8")],
        force=True,
    )
    LOGGER.info("Starting structured-export benchmark; log=%s", log_path.resolve())

    config, items, metadata = prepare_test(args.config, args.split_csv, args.dataset_dir, args.limit)
    baseline_manifest = json.loads(args.baseline_manifest.read_text(encoding="utf-8"))
    check_manifest(baseline_manifest, config)
    check_hash(args.checkpoint, baseline_manifest.get("checkpoint_sha256"))
    check_hash(args.baseline_onnx, baseline_manifest.get("onnx_sha256"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    check_manifest(manifest, config)
    baseline_sha256 = sha256(args.checkpoint)
    if manifest.get("model_type") != "structured_pruned":
        raise ValueError("Manifest không đánh dấu model_type=structured_pruned.")
    if manifest.get("source_checkpoint_sha256") != baseline_sha256:
        raise ValueError("Structured checkpoint và model gốc không cùng source checkpoint.")
    check_hash(args.structured_checkpoint, manifest.get("checkpoint_sha256"))
    check_hash(args.onnx, manifest.get("onnx_sha256"))
    if not args.skip_pte:
        if not manifest.get("artifacts_complete"):
            raise ValueError("Manifest chưa có cả ONNX/PTE; export đủ hai định dạng hoặc dùng --skip-pte.")
        check_hash(args.pte, manifest.get("pte_sha256"))
        check_hash(args.baseline_pte, baseline_manifest.get("pte_sha256"))

    import torch

    torch.set_num_threads(1)
    structured_predict, structured_details = load_structured_runner(
        args.structured_checkpoint, config, baseline_sha256,
    )
    runners = {
        "baseline_pth": pth_runner(args.checkpoint, config),
        "structured_pth": structured_predict,
        "baseline_onnx": onnx_runner(args.baseline_onnx, config),
        "structured_onnx": onnx_runner(args.onnx, config),
    }
    files = {
        "baseline_pth": args.checkpoint,
        "structured_pth": args.structured_checkpoint,
        "baseline_onnx": args.baseline_onnx,
        "structured_onnx": args.onnx,
    }
    if not args.skip_pte:
        runners["baseline_pte"] = pte_runner(args.baseline_pte, baseline_manifest.get("executorch_runtime"))
        runners["structured_pte"] = pte_runner(args.pte, manifest.get("executorch_runtime"))
        files["baseline_pte"] = args.baseline_pte
        files["structured_pte"] = args.pte

    metadata.update(
        comparison="original vs structured-pruned PTH/ONNX/PTE; compare speed within the same runtime",
        baseline_checkpoint_sha256=baseline_sha256,
        baseline_manifest=str(args.baseline_manifest.resolve()),
        baseline_manifest_sha256=sha256(args.baseline_manifest),
        structured_manifest=str(args.manifest.resolve()),
        structured_manifest_sha256=sha256(args.manifest),
        structured_model_training=structured_details,
        pte_status="skipped_by_user" if args.skip_pte else "executed",
        executorch_runtime=None if args.skip_pte else manifest.get("executorch_runtime"),
        pytorch_version=torch.__version__,
    )
    LOGGER.info("Running %d model(s) on %d test images; scope=%s",
                len(runners), len(items), metadata["evaluation_scope"])
    write_comparison(
        runners, items, config, {name: artifact(path) for name, path in files.items()},
        metadata, args.report_dir, args.no_plots,
    )
    LOGGER.info("Reports saved to %s", args.report_dir.resolve())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        LOGGER.warning("Benchmark interrupted; reports may be incomplete")
        raise SystemExit(130)
    except Exception:
        LOGGER.exception("Structured export benchmark failed; reports may be incomplete")
        raise SystemExit(1)
