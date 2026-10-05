"""Compare the original checkpoint with a fine-tuned structured-pruned model.

Run after structured_pruning.py. Uses the saved independent test split and the
same preprocessing, metrics, latency measurement, and reports as compare_models.py.
CPU batch=1 timings are desktop measurements, not mobile benchmarks.
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np

from compare_models import (
    CONFIG_JSON, DATASET_DIR, EDGE_DIR, REPORTS_DIR, SPLIT_CSV, artifact,
    pth_runner, prepare_test, write_comparison,
)
from quantize_model import sha256


LOGGER = logging.getLogger("compare_structured_pruning")
DEFAULT_PRUNED = (EDGE_DIR / "StructuredPruning_v1"
                  / "flood_mobilenetv3_large_structured_best.pt")


def load_structured_model(path: Path, config: dict, source_checkpoint_sha256: str):
    import torch

    if not path.is_file():
        raise FileNotFoundError(f"Chưa có model structured-pruned: {path}; hãy chạy structured_pruning.py trước.")
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict) or not isinstance(payload.get("model"), torch.nn.Module):
        raise ValueError("Checkpoint pruning phải chứa full model trong trường 'model'.")
    if payload.get("source_checkpoint_sha256") != source_checkpoint_sha256:
        raise ValueError("Model pruning không được tạo từ checkpoint gốc đang so sánh.")
    pruning = payload.get("pruning")
    if not isinstance(pruning, dict) or pruning.get("method") != "global_group_magnitude_channel":
        raise ValueError("Checkpoint không có metadata structured-pruning hợp lệ.")
    if list(payload.get("class_names", [])) != config["class_order"]:
        raise ValueError("class_names trong checkpoint pruning không khớp config.")
    saved_config = payload.get("config", {})
    for key in ("image_size", "preprocess", "class_order", "letterbox_fill"):
        saved, expected = saved_config.get(key), config.get(key)
        if key == "letterbox_fill" and saved is not None and expected is not None:
            saved, expected = list(saved), list(expected)
        if saved != expected:
            raise ValueError(f"Config model pruning không khớp trường {key}.")

    model = payload["model"].cpu().eval()
    parameters = sum(parameter.numel() for parameter in model.parameters())
    recorded = payload.get("pruning", {}).get("parameter_count_after")
    if recorded is not None and int(recorded) != parameters:
        raise ValueError("Số parameter trong metadata không khớp model pruning.")

    details = {
        "pruning": pruning,
        "best_epoch": payload.get("epoch"),
        "validation_metrics_at_best_epoch": payload.get("validation_metrics"),
        "parameter_count": parameters,
    }
    return model, details


def load_structured_runner(path: Path, config: dict, source_checkpoint_sha256: str):
    import torch

    model, details = load_structured_model(path, config, source_checkpoint_sha256)

    def predict(array: np.ndarray) -> np.ndarray:
        with torch.inference_mode():
            logits = model(torch.from_numpy(array))
            return torch.softmax(logits, dim=1).numpy()

    return predict, details


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=EDGE_DIR / "flood_mobilenetv3_large_best.pth")
    parser.add_argument("--pruned", type=Path, default=DEFAULT_PRUNED)
    parser.add_argument("--config", type=Path, default=CONFIG_JSON)
    parser.add_argument("--split-csv", type=Path, default=SPLIT_CSV)
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--report-dir", type=Path, default=REPORTS_DIR / "structured_pruning_compare")
    parser.add_argument("--limit", type=int, help="Smoke subset of test only; not a final metric.")
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    args.report_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(args.report_dir / "compare.log", mode="w", encoding="utf-8")],
        force=True,
    )
    import torch

    torch.set_num_threads(1)

    config, items, metadata = prepare_test(args.config, args.split_csv, args.dataset_dir, args.limit)
    baseline_sha256 = sha256(args.checkpoint)
    pruned_predict, pruned_details = load_structured_runner(args.pruned, config, baseline_sha256)
    runners = {
        "baseline": pth_runner(args.checkpoint, config),
        "structured_pruned": pruned_predict,
    }
    metadata.update(
        comparison="original checkpoint vs fine-tuned structured pruning",
        source_checkpoint_sha256=baseline_sha256,
        structured_model=str(args.pruned.resolve()),
        structured_model_sha256=sha256(args.pruned),
        structured_model_training=pruned_details,
        parameter_count_before=pruned_details["pruning"].get("parameter_count_before"),
        parameter_count_after=pruned_details["parameter_count"],
        pytorch_version=torch.__version__,
    )
    write_comparison(
        runners, items, config,
        {"baseline": artifact(args.checkpoint), "structured_pruned": artifact(args.pruned)},
        metadata, args.report_dir, args.no_plots,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        LOGGER.warning("Benchmark interrupted; reports may be incomplete")
        raise SystemExit(130)
    except Exception:
        LOGGER.exception("Benchmark failed; reports may be incomplete")
        raise SystemExit(1)
