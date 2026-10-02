"""So sánh PTH / ONNX / ExecuTorch PTE trên cùng test split, không train/export.

Đo sai số probabilities sau softmax (không phải raw logits).
Chạy runtime thật trên CPU máy tính, không giả lập kết quả Android.
Thời gian: mean/median/P95/min/max/tổng inference; CSV lưu latency từng ảnh.

Chạy từ tools/: python compare_models.py
Log terminal + reports/pth_onnx_pte/compare.log (ghi mới mỗi lần chạy).
Chi tiết từng model/ảnh: python compare_models.py --verbose
Smoke test: python compare_models.py --limit 3 --skip-pte --no-plots
Thiếu PTE/runtime sẽ báo lỗi; chỉ bỏ PTE khi chọn --skip-pte.
FP32 vs INT8 dùng compare_fp32_int8.py riêng.
Báo cáo mặc định: products/fe/reports/pth_onnx_pte/.
"""
from __future__ import annotations

import argparse
import csv
import importlib.metadata
import itertools
import json
import logging
import time
from pathlib import Path

import numpy as np

from quantize_model import (DATASET_DIR, ROOT, load_splits, preprocess, quantized_probability_sum_atol,
                            session, sha256, validate_input_shape, validate_probabilities)

EDGE_DIR = ROOT / "model" / "Edge Ai"
CONFIG_JSON = EDGE_DIR / "config_mobilenetv3_large.json"
SPLIT_CSV = EDGE_DIR / "split_train_val_test_mobilenetv3_large.csv"
EXPORT_DIR = EDGE_DIR / "Export"
REPORTS_DIR = ROOT / "reports"
LOGGER = logging.getLogger(__name__)


def check_hash(path: Path, expected: str | None) -> None:
    LOGGER.debug("Checking SHA256: %s", path)
    if not path.is_file():
        raise FileNotFoundError(f"Thiếu file: {path}")
    if not expected or sha256(path) != expected:
        raise ValueError(f"Hash không khớp manifest: {path}")


def check_manifest(manifest: dict, config: dict) -> None:
    expected = "letterbox_rgb_" + "_".join(map(str, config["letterbox_fill"]))
    if (config.get("preprocess") != "letterbox"
            or manifest.get("preprocess") != expected
            or manifest.get("input_size") != config["image_size"]
            or manifest.get("letterbox_fill") != config["letterbox_fill"]
            or manifest.get("class_order") != config["class_order"]):
        raise ValueError("Config preprocessing/class_order không khớp manifest.")


def pth_runner(path: Path, config: dict):
    LOGGER.info("Loading PTH: %s", path)
    started = time.perf_counter()
    import torch
    from convert_model import build_model, load_checkpoint, remove_module_prefix

    torch.set_num_threads(1)
    state, checkpoint = load_checkpoint(path)
    state = remove_module_prefix(state)
    classes = checkpoint.get("class_names")
    if classes is not None and list(classes) != config["class_order"]:
        raise ValueError("class_names trong checkpoint không khớp config.")
    model = build_model(len(config["class_order"]), config["dropout"],
                        nested_classifier="classifier.3.1.weight" in state)
    model.load_state_dict(state, strict=True)
    model.eval()
    LOGGER.info("PTH ready (torch %s, CPU/1 thread, %.2fs)", torch.__version__, time.perf_counter() - started)

    def predict(array):
        with torch.inference_mode():
            return torch.softmax(model(torch.from_numpy(array)), dim=1).numpy()

    return predict


def onnx_runner(path: Path, config: dict):
    LOGGER.info("Loading ONNX: %s", path)
    started = time.perf_counter()
    runtime = session(path)  # CPUExecutionProvider, 1 luồng.
    if len(runtime.get_inputs()) != 1 or len(runtime.get_outputs()) != 1:
        raise ValueError("Cần graph có một input và một output.")
    info = runtime.get_inputs()[0]
    size = config["image_size"]
    # Exporter cho phép batch động; chỉ spatial dimensions phải cố định.
    validate_input_shape(info.shape, size)
    if info.type != "tensor(float)" or runtime.get_outputs()[0].type != "tensor(float)":
        raise ValueError(f"Input/output ONNX không khớp FP32 NCHW config: {info.shape}")
    LOGGER.info("ONNX ready (input=%s, CPU/1 thread, %.2fs)", info.shape, time.perf_counter() - started)
    return lambda array: runtime.run(None, {info.name: array})[0]


def pte_runner(path: Path, expected_version: str | None):
    LOGGER.info("Loading PTE: %s", path)
    started = time.perf_counter()
    import torch

    try:
        version = importlib.metadata.version("executorch")
    except importlib.metadata.PackageNotFoundError as error:
        raise RuntimeError("Thiếu ExecuTorch. Cài đúng version trong manifest hoặc dùng --skip-pte.") from error
    if not expected_version or version != expected_version:
        raise ValueError(f"ExecuTorch runtime không khớp manifest: {version} != {expected_version}")
    LOGGER.info("ExecuTorch %s: importing runtime and loading forward", version)
    from executorch.runtime import Runtime

    program = Runtime.get().load_program(path)
    forward = program.load_method("forward")
    LOGGER.info("PTE ready (%.2fs)", time.perf_counter() - started)

    def predict(array, _program=program):
        # Giữ program sống cùng method; tuyệt đối không lấy lại output ONNX.
        output = forward.execute((torch.from_numpy(array),))
        if len(output) != 1 or not isinstance(output[0], torch.Tensor):
            raise ValueError("PTE cần trả một tensor probabilities.")
        return output[0].detach().cpu().numpy().copy()

    return predict


def compute_ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    confidence, correct = probs.max(axis=1), probs.argmax(axis=1) == labels
    bounds = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for lower, upper in zip(bounds[:-1], bounds[1:]):
        mask = (confidence > lower) & (confidence <= upper)
        if mask.any():
            ece += abs(correct[mask].mean() - confidence[mask].mean()) * mask.mean()
    return float(ece)


def classification_metrics(probs: np.ndarray, labels: np.ndarray, class_order: list[str],
                           critical_distance: int = 2) -> dict:
    from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix
    from sklearn.metrics import f1_score, precision_recall_fscore_support

    predictions = probs.argmax(axis=1)
    classes = list(range(len(class_order)))
    precision, recall, f1, support = precision_recall_fscore_support(
        labels, predictions, labels=classes, zero_division=0)
    result = {
        "accuracy": float(accuracy_score(labels, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(labels, predictions)),
        "macro_f1": float(f1_score(labels, predictions, labels=classes, average="macro", zero_division=0)),
        "ece": compute_ece(probs, labels),
        "brier_score": float(np.square(probs - np.eye(len(classes))[labels]).sum(axis=1).mean()),
        "confusion_matrix": confusion_matrix(labels, predictions, labels=classes).tolist(),
        "per_class": {name: dict(precision=float(precision[i]), recall=float(recall[i]),
                                 f1=float(f1[i]), support=int(support[i]))
                      for i, name in enumerate(class_order)},
    }
    severity_rank = {"non_flood": 0, "low": 1, "medium": 2, "high": 3}
    if all(name in severity_rank for name in class_order):
        distances = np.abs(np.asarray([severity_rank[name] for name in class_order])[labels]
                           - np.asarray([severity_rank[name] for name in class_order])[predictions])
        result.update(
            critical_error_count=int((distances >= critical_distance).sum()),
            critical_error_rate=float((distances >= critical_distance).mean()),
            mean_severity_distance=float(distances.mean()),
        )
    return result


def pairwise_metrics(a: np.ndarray, b: np.ndarray, atol: float, rtol: float) -> dict:
    from scipy.special import rel_entr

    difference = np.abs(a - b)
    cosine = (a * b).sum(axis=1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1))
    p, q = a.astype(np.float64), b.astype(np.float64)
    p, q = p / p.sum(axis=1, keepdims=True), q / q.sum(axis=1, keepdims=True)
    midpoint = (p + q) / 2
    # JS >= 0; clamp roundoff trước khi báo cáo, tránh NaN khi hai vector rất gần.
    js = np.maximum((rel_entr(p, midpoint).sum(axis=1) + rel_entr(q, midpoint).sum(axis=1)) / 2, 0)
    return {
        "top1_agreement": float((a.argmax(axis=1) == b.argmax(axis=1)).mean()),
        "max_abs_diff": float(difference.max()),
        "mean_abs_diff": float(difference.mean()),
        "rmse": float(np.sqrt(np.square(difference.astype(np.float64)).mean())),
        "l1_mean": float(difference.sum(axis=1).mean()),
        "l2_mean": float(np.linalg.norm(a - b, axis=1).mean()),
        "cosine_similarity_mean": float(cosine.mean()),
        "js_divergence_mean": float(js.mean()),
        "probabilities_close": bool(np.allclose(a, b, atol=atol, rtol=rtol)),
        "atol": atol, "rtol": rtol,
    }


def evaluate_models(runners: dict, items: list, config: dict) -> tuple[dict, dict, list]:
    if not items:
        raise ValueError("Test không được rỗng.")
    num_classes = len(config["class_order"])
    probabilities = {name: [] for name in runners}
    latencies = {name: [] for name in runners}
    rows = []
    LOGGER.info("Preparing warmup image: %s", items[0][0].name)
    sample = np.ascontiguousarray(preprocess(items[0][0], config["image_size"], config["letterbox_fill"]))
    for name, predict in runners.items():
        for step in range(1, 4):
            LOGGER.info("Warmup %s %d/3 starting", name, step)
            try:
                tolerance = quantized_probability_sum_atol(num_classes) if "int8" in name else 1e-4
                validate_probabilities(predict(sample.copy()), num_classes, sum_atol=tolerance)
            except Exception:
                LOGGER.error("Warmup failed: model=%s, step=%d/3", name, step)
                raise
            LOGGER.info("Warmup %s %d/3 done", name, step)
    started = time.perf_counter()
    LOGGER.info("Evaluating %d test images; models=%s", len(items), ", ".join(runners))
    for index, (path, label) in enumerate(items, 1):
        LOGGER.info("[%d/%d] Processing %s", index, len(items), path.name)
        tensor = np.ascontiguousarray(preprocess(path, config["image_size"], config["letterbox_fill"]))
        outputs, timings = {}, {}
        for name, predict in runners.items():
            x = tensor.copy()  # Không chia sẻ input có thể bị runtime sửa.
            LOGGER.debug("[%d/%d] Inference %s starting", index, len(items), name)
            try:
                start = time.perf_counter()
                output = predict(x)
                timings[name] = (time.perf_counter() - start) * 1000
                tolerance = quantized_probability_sum_atol(num_classes) if "int8" in name else 1e-4
                outputs[name] = validate_probabilities(output, num_classes, sum_atol=tolerance)
            except Exception:
                LOGGER.error("Inference failed: model=%s, image=%s (%d/%d)", name, path.name, index, len(items))
                raise
            LOGGER.debug("[%d/%d] Inference %s done: %.2fms", index, len(items), name, timings[name])
        # Chỉ ghi nhận sau khi TẤT CẢ model thành công; không skip ảnh lỗi.
        row = {"image_path": str(path), "ground_truth": config["class_order"][label], "gt_idx": label}
        for name, prob in outputs.items():
            probabilities[name].append(prob)
            latencies[name].append(timings[name])
            order = np.argsort(prob)[::-1]
            row.update({f"pred_{name}": config["class_order"][int(order[0])],
                        f"confidence_{name}": float(prob[order[0]]),
                        f"latency_ms_{name}": timings[name],
                        f"margin_{name}": float(prob[order[0]] - prob[order[1]]),
                        f"probabilities_{name}": json.dumps(prob.tolist())})
        rows.append(row)
        elapsed = time.perf_counter() - started
        predictions = "; ".join(f"{name}={row[f'pred_{name}']} ({row[f'confidence_{name}']:.3f}, {timings[name]:.2f}ms)"
                                for name in runners)
        LOGGER.info("[%d/%d] Done | %s | elapsed=%.1fs | ETA=%.1fs", index, len(items), predictions,
                    elapsed, elapsed / index * (len(items) - index))
    return {name: np.stack(values) for name, values in probabilities.items()}, latencies, rows


def write_plots(report_dir: Path, probabilities: dict, metrics: dict, labels, class_order):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    for name, probs in probabilities.items():
        cm = np.array(metrics[name]["confusion_matrix"])
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.imshow(cm, cmap="Blues")
        ax.set(xticks=range(len(class_order)), yticks=range(len(class_order)),
               xticklabels=class_order, yticklabels=class_order,
               xlabel="Predicted", ylabel="Ground truth", title=f"Confusion matrix: {name}")
        for i, j in np.ndindex(cm.shape):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center")
        fig.tight_layout()
        fig.savefig(report_dir / f"confusion_{name}.png", dpi=160)
        plt.close(fig)
        confidence, correct = probs.max(axis=1), probs.argmax(axis=1) == labels
        bin_confidence, bin_accuracy = [], []
        bounds = np.linspace(0, 1, 11)
        for lower, upper in zip(bounds[:-1], bounds[1:]):
            mask = (confidence > lower) & (confidence <= upper)
            if mask.any():
                bin_confidence.append(confidence[mask].mean())
                bin_accuracy.append(correct[mask].mean())
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.plot([0, 1], [0, 1], "k--")
        ax.plot(bin_confidence, bin_accuracy, "o-")
        ax.set(xlim=(0, 1), ylim=(0, 1), xlabel="Confidence", ylabel="Accuracy",
               title=f"{name}: ECE={metrics[name]['ece']:.4f}")
        fig.tight_layout()
        fig.savefig(report_dir / f"calibration_{name}.png", dpi=160)
        plt.close(fig)


def write_comparison(runners, items, config, artifacts, metadata, report_dir,
                     no_plots=False, atol=1e-5, rtol=1e-4) -> dict:
    started = time.perf_counter()
    probabilities, timings, rows = evaluate_models(runners, items, config)
    LOGGER.info("Computing classification and pairwise metrics")
    labels = np.array([label for _, label in items])
    metrics = {name: {**classification_metrics(prob, labels, config["class_order"],
                                               config.get("critical_distance", 2)),
                      "latency_ms_mean": float(np.mean(timings[name])),
                      "latency_ms_median": float(np.median(timings[name])),
                      "latency_ms_p95": float(np.percentile(timings[name], 95)),
                      "latency_ms_min": float(np.min(timings[name])),
                      "latency_ms_max": float(np.max(timings[name])),
                      "latency_ms_total": float(np.sum(timings[name])),
                      **artifacts[name]} for name, prob in probabilities.items()}
    pairs = {f"{a}_vs_{b}": pairwise_metrics(probabilities[a], probabilities[b], atol, rtol)
             for a, b in itertools.combinations(runners, 2)}
    result = {"metadata": {**metadata, "evaluation_split": "test", "n_images": len(items),
                            "class_order": config["class_order"], "input_size": config["image_size"],
                            "output_type": "probabilities",
                            "preprocess": "EXIF -> RGB -> letterbox BILINEAR -> ImageNet NCHW",
                            "timing": "CPU máy tính; batch=1; 3 warmup/model không tính vào latency; "
                                      "không gồm load model, preprocessing, validation, logging; "
                                      "tổng là tổng thời gian gọi predict, không phải wall-clock toàn pipeline; "
                                      "không phải latency mobile"},
              "classification_metrics": metrics, "pairwise_comparison": pairs}
    result["metadata"]["critical_distance"] = config.get("critical_distance", 2)
    LOGGER.info("Writing JSON/CSV/Markdown reports: %s", report_dir.resolve())
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "summary.json").write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    with (report_dir / "all_predictions.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    disagreement = [row for row in rows if len({row[f"pred_{name}"] for name in runners}) > 1]
    if disagreement:
        with (report_dir / "model_disagreement.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(disagreement)
    else:
        (report_dir / "model_disagreement.csv").unlink(missing_ok=True)
    lines = ["# So sánh model trên test split", "", f"Scope: {metadata['evaluation_scope']}; số ảnh: {len(items)}.",
             f"Critical error: khoảng cách severity >= {config.get('critical_distance', 2)}.",
             "CPU máy tính, không phải benchmark mobile. PTH/ONNX: 1 luồng; PTE theo runtime.", "",
             "| Model | Accuracy | Macro-F1 | Balanced acc | Critical errors | ECE | Brier | Median ms | MB |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    if "pte_status" in metadata:
        lines.insert(3, f"PTE status: {metadata['pte_status']}.")
    for name, values in metrics.items():
        critical = (f"{values['critical_error_count']} ({values['critical_error_rate']:.2%})"
                    if "critical_error_count" in values else "-")
        lines.append(f"| {name} | {values['accuracy']:.2%} | {values['macro_f1']:.2%} | {values['balanced_accuracy']:.2%} | "
                     f"{critical} | {values['ece']:.5f} | {values['brier_score']:.5f} | {values['latency_ms_median']:.2f} | {values['bytes']/1024**2:.2f} |")
    lines += ["", "## Thời gian suy luận", "",
              "Batch=1; 3 warmup/model không tính vào thống kê. Không gồm load model, preprocessing, validation hay logging.",
              "P95: khoảng 95% lượt chạy có latency không vượt mức này. Tổng chỉ cộng thời gian gọi predict, không phải toàn pipeline.", "",
              "| Model | Mean ms | Median ms | P95 ms | Min ms | Max ms | Tổng inference s |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for name, values in metrics.items():
        lines.append(f"| {name} | {values['latency_ms_mean']:.2f} | {values['latency_ms_median']:.2f} | "
                     f"{values['latency_ms_p95']:.2f} | {values['latency_ms_min']:.2f} | {values['latency_ms_max']:.2f} | "
                     f"{values['latency_ms_total']/1000:.3f} |")
    lines += ["", "Sai số trên probabilities sau softmax; không phải raw logits hay kết quả Android.", "",
              "| Cặp | Top-1 agreement | Max abs diff | MAE | RMSE | Cosine mean | Probabilities close |",
              "|---|---:|---:|---:|---:|---:|---|"]
    for name, values in pairs.items():
        lines.append(f"| {name} | {values['top1_agreement']:.2%} | {values['max_abs_diff']:.8g} | "
                     f"{values['mean_abs_diff']:.8g} | {values['rmse']:.8g} | {values['cosine_similarity_mean']:.10f} | "
                     f"{values['probabilities_close']} |")
    lines += ["", f"Tolerance: atol={atol}, rtol={rtol}. Agreement không đồng nghĩa xác suất giống hệt hoặc accuracy 100%.",
              "Smoke subset không thay thế metric full test."]
    report = "\n".join(lines) + "\n"
    (report_dir / "summary.md").write_text(report, encoding="utf-8")
    if not no_plots:
        LOGGER.info("Writing confusion/calibration plots")
        write_plots(report_dir, probabilities, metrics, labels, config["class_order"])
    LOGGER.info("Comparison complete: %d images, %.2fs; reports=%s", len(items),
                time.perf_counter() - started, report_dir.resolve())
    print(report)
    print(f"Reports: {report_dir.resolve()}")
    return result


def artifact(path: Path) -> dict:
    return {"file": str(path.resolve()), "sha256": sha256(path), "bytes": path.stat().st_size}


def prepare_test(config_path: Path, split_csv: Path, dataset_dir: Path, limit: int | None):
    LOGGER.info("Reading config: %s", config_path)
    if limit is not None and limit <= 0:
        raise ValueError("--limit phải > 0.")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if len(config["class_order"]) < 2 or len(set(config["class_order"])) != len(config["class_order"]):
        raise ValueError("class_order cần ít nhất hai lớp, không trùng.")
    LOGGER.info("Auditing saved train/val/test split (paths, hashes, leakage): %s", split_csv)
    test = load_splits(split_csv, dataset_dir, config["class_order"])["test"]
    items = test if limit is None else test[:limit]
    metadata = {"config": str(config_path.resolve()), "config_sha256": sha256(config_path),
                "split_csv": str(split_csv.resolve()), "split_csv_sha256": sha256(split_csv),
                "dataset_dir": str(dataset_dir.resolve()), "full_test_count": len(test), "seed": config.get("seed"),
                "evaluation_scope": "full_test" if len(items) == len(test) else "test_subset_smoke"}
    LOGGER.info("Split audit passed; selected %d/%d test images; scope=%s; input=1x3x%dx%d",
                len(items), len(test), metadata["evaluation_scope"], config["image_size"], config["image_size"])
    return config, items, metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--checkpoint", type=Path, default=EDGE_DIR / "flood_mobilenetv3_large_best.pth")
    parser.add_argument("--onnx", type=Path, default=EXPORT_DIR / "flood_mobilenetv3_large.onnx")
    parser.add_argument("--pte", type=Path, default=EXPORT_DIR / "flood_mobilenetv3_large.pte")
    parser.add_argument("--manifest", type=Path, default=EXPORT_DIR / "model_manifest.json")
    parser.add_argument("--config", type=Path, default=CONFIG_JSON)
    parser.add_argument("--split-csv", type=Path, default=SPLIT_CSV)
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--report-dir", type=Path, default=REPORTS_DIR / "pth_onnx_pte")
    parser.add_argument("--skip-pte", action="store_true", help="chỉ PTH/ONNX; báo cáo ghi rõ PTE không chạy")
    parser.add_argument("--limit", type=int, help="smoke test vài ảnh, không phải full test")
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--verbose", action="store_true", help="log chi tiết từng model/ảnh")
    args = parser.parse_args()
    args.report_dir.mkdir(parents=True, exist_ok=True)
    log_path = args.report_dir / "compare.log"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S", force=True,
                        handlers=[logging.StreamHandler(), logging.FileHandler(log_path, mode="w", encoding="utf-8")])
    LOGGER.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    LOGGER.info("Starting comparison; log=%s", log_path.resolve())
    config, items, metadata = prepare_test(args.config, args.split_csv, args.dataset_dir, args.limit)
    LOGGER.info("Checking manifest and model hashes: %s", args.manifest)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    check_manifest(manifest, config)
    check_hash(args.checkpoint, manifest.get("checkpoint_sha256"))
    check_hash(args.onnx, manifest.get("onnx_sha256"))
    if not args.skip_pte:
        if not args.pte.is_file():
            raise FileNotFoundError(f"Chưa có PTE: {args.pte}. Export PTE trước, hoặc chọn --skip-pte.")
        check_hash(args.pte, manifest.get("pte_sha256"))
    LOGGER.info("Manifest/model hashes passed")
    if args.skip_pte:
        LOGGER.warning("PTE skipped by user (--skip-pte)")
    runners = {"pth": pth_runner(args.checkpoint, config), "onnx": onnx_runner(args.onnx, config)}
    files = {"pth": args.checkpoint, "onnx": args.onnx}
    if not args.skip_pte:
        runners["pte"] = pte_runner(args.pte, manifest.get("executorch_runtime"))
        files["pte"] = args.pte
    metadata.update(manifest=str(args.manifest.resolve()), manifest_sha256=sha256(args.manifest),
                    pte_status="skipped_by_user" if args.skip_pte else "executed",
                    pytorch_version=importlib.metadata.version("torch"),
                    onnxruntime_version=importlib.metadata.version("onnxruntime"),
                    executorch_runtime=manifest.get("executorch_runtime") if not args.skip_pte else None)
    write_comparison(runners, items, config, {name: artifact(path) for name, path in files.items()},
                     metadata, args.report_dir, args.no_plots)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        LOGGER.warning("Comparison interrupted by user; reports may be incomplete")
        raise SystemExit(130)
    except Exception:
        LOGGER.exception("Comparison failed; reports may be incomplete")
        raise SystemExit(1)
