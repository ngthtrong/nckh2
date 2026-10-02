"""Screen unstructured magnitude-pruning levels on validation; does not fine-tune/export.

Run from tools/: python benchmark_pruning.py --limit 3
The dense CPU latency and reported state-tensor bytes do not imply mobile speed/size gains.
"""
from __future__ import annotations

import argparse
import csv
import copy
import json
import statistics
import time
from pathlib import Path

import numpy as np

from compare_models import CONFIG_JSON, DATASET_DIR, EDGE_DIR, SPLIT_CSV, check_manifest
from convert_model import build_model, load_checkpoint, remove_module_prefix
from quantize_model import load_splits, preprocess, sha256


def measure(model, items, config: dict) -> dict:
    import torch
    from compare_models import classification_metrics

    model.eval()
    tensors = [torch.from_numpy(preprocess(path, config["image_size"], config["letterbox_fill"]))
               for path, _ in items]
    labels = np.asarray([label for _, label in items])
    with torch.inference_mode():
        for _ in range(3):
            model(tensors[0])
        probabilities, timings = [], []
        for tensor in tensors:
            started = time.perf_counter()
            logits = model(tensor)
            timings.append((time.perf_counter() - started) * 1000)
            probability = torch.softmax(logits, dim=1).cpu().numpy()[0]
            if probability.shape != (len(config["class_order"]),) or not np.isfinite(probability).all():
                raise ValueError("Model trả output lỗi trong pruning screen.")
            probabilities.append(probability)
    scores = classification_metrics(np.asarray(probabilities), labels, config["class_order"],
                                    config.get("critical_distance", 2))
    storage_bytes = sum(value.numel() * value.element_size() for value in model.state_dict().values())
    return {**scores, "latency_ms_median_cpu": statistics.median(timings),
            "dense_state_tensor_bytes": storage_bytes}


def prune_candidate(model, amount: float) -> float:
    import torch.nn as nn
    import torch.nn.utils.prune as prune

    parameters = [(module, "weight") for module in model.modules()
                  if isinstance(module, (nn.Conv2d, nn.Linear))]
    if not parameters:
        raise ValueError("Không tìm thấy Conv2d/Linear weights để pruning.")
    prune.global_unstructured(parameters, pruning_method=prune.L1Unstructured, amount=amount)
    total, zeros = 0, 0
    for module, name in parameters:
        value = getattr(module, name)
        total += value.numel()
        zeros += int((value == 0).sum())
        prune.remove(module, name)  # Bake zeros into ordinary dense weights before timing/export.
    return zeros / total


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--checkpoint", type=Path, default=EDGE_DIR / "flood_mobilenetv3_large_best.pth")
    parser.add_argument("--config", type=Path, default=CONFIG_JSON)
    parser.add_argument("--split-csv", type=Path, default=SPLIT_CSV)
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--source-manifest", type=Path, default=EDGE_DIR / "Export" / "model_manifest.json")
    parser.add_argument("--sparsities", type=float, nargs="+", default=[0.1, 0.2, 0.3, 0.5])
    parser.add_argument("--limit", type=int, help="small validation smoke test; does not use test split")
    parser.add_argument("--output-dir", type=Path, default=EDGE_DIR.parent.parent / "reports" / "pruning")
    args = parser.parse_args()
    if not args.sparsities or any(not 0 < amount < 1 for amount in args.sparsities):
        raise ValueError("Mọi sparsity phải nằm trong khoảng (0, 1).")
    if len(set(args.sparsities)) != len(args.sparsities):
        raise ValueError("Không lặp sparsity.")
    if args.limit is not None and args.limit < 1:
        raise ValueError("--limit phải >= 1.")

    import torch
    torch.set_num_threads(1)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    source = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    if source.get("checkpoint_sha256") != sha256(args.checkpoint):
        raise ValueError("Manifest ONNX không thuộc checkpoint được chỉ định.")
    check_manifest(source, config)
    split = load_splits(args.split_csv, args.dataset_dir, config["class_order"])
    items = split["val"][:args.limit] if args.limit else split["val"]
    if not items:
        raise ValueError("Validation split rỗng; test split không dùng để chọn sparsity.")

    state, checkpoint = load_checkpoint(args.checkpoint)
    state = remove_module_prefix(state)
    if checkpoint.get("class_names") and list(checkpoint["class_names"]) != config["class_order"]:
        raise ValueError("class_names trong checkpoint không khớp config.")
    model = build_model(len(config["class_order"]), float(config.get("dropout", 0.25)),
                        nested_classifier="classifier.3.1.weight" in state)
    model.load_state_dict(state, strict=True)
    model.eval()
    torch.manual_seed(42)

    rows = [{"candidate": "baseline", "target_sparsity": 0.0, "actual_sparsity": 0.0,
             **measure(model, items, config)}]
    for amount in args.sparsities:
        candidate = copy.deepcopy(model)
        actual = prune_candidate(candidate, amount)
        rows.append({"candidate": f"global_l1_{amount:g}", "target_sparsity": amount,
                     "actual_sparsity": actual, **measure(candidate, items, config)})
        del candidate

    result = {
        "checkpoint_sha256": sha256(args.checkpoint),
        "split_csv_sha256": sha256(args.split_csv),
        "evaluation_split": "val",
        "n_images": len(items),
        "scope": "unstructured_global_magnitude_screen_before_finetuning",
        "prunable_layers": "Conv2d/Linear weights",
        "latency_note": "CPU desktop, batch=1, dense tensors; no mobile or sparse-kernel speed claim",
        "size_note": "state tensor payload bytes; unstructured zeros do not shrink dense tensor shapes",
        "deployment_ready": False,
        "results": rows,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "pruning_screen.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    with (args.output_dir / "pruning_screen.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Split: val; images: {len(items)}; test: not used")
    print("Unstructured screen only; no fine-tuning/export; dense CPU latency is not mobile speed.")
    print("candidate,target_sparsity,actual_sparsity,accuracy,macro_f1,critical_error_count,latency_ms_median_cpu")
    for row in rows:
        print(f"{row['candidate']},{row['target_sparsity']:.2f},{row['actual_sparsity']:.4f},"
              f"{row['accuracy']:.4f},{row['macro_f1']:.4f},{row.get('critical_error_count', '-')},"
              f"{row['latency_ms_median_cpu']:.2f}")
    print(f"Reports: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
