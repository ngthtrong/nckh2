"""Paired, group-aware development analyses; never change historical results."""
from __future__ import annotations

import csv
import itertools
import json
import math
from pathlib import Path

from runtime import csv_rows, digest, write


def mcnemar_exact(b, c):
    n = b + c
    return min(1.0, 2 * sum(math.comb(n, k) for k in range(min(b, c) + 1)) / 2**n) if n else 1.0


def holm(values):
    result, previous = {}, 0.0
    for rank, (name, p) in enumerate(sorted(values.items(), key=lambda item: item[1])):
        previous = max(previous, min(1.0, (len(values) - rank) * p))
        result[name] = previous
    return result


def basename(value):
    return str(value).replace("\\", "/").rsplit("/", 1)[-1]


def analyze_predictions(predictions, split_csv, output, draws=2000):
    import numpy as np
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, recall_score

    rows = csv_rows(predictions)
    if not rows:
        raise ValueError("Empty predictions")
    classes = ["low", "medium", "high", "non_flood"]
    ranks = {"non_flood": 0, "low": 1, "medium": 2, "high": 3}
    split = [r for r in csv_rows(split_csv) if r["split"] == "test"]
    identities = {(r["label"], r["file_name"]): r for r in split}
    keys = [(r["ground_truth"], basename(r["image_path"])) for r in rows]
    if len(set(keys)) != len(keys) or set(keys) != set(identities):
        raise ValueError("Predictions do not contain exactly the saved test IDs")
    models = sorted(k.removeprefix("pred_") for k in rows[0] if k.startswith("pred_"))
    gold = np.array([r["ground_truth"] for r in rows])
    predicted = {m: np.array([r["pred_" + m] for r in rows]) for m in models}
    group = [identities[k]["split_group"] for k in keys]
    unique = sorted(set(group))
    members = [np.flatnonzero(np.array(group) == key) for key in unique]
    metrics = {}
    for name, p in predicted.items():
        if any(x not in classes for x in p):
            raise ValueError("Unknown predicted class")
        distance = np.array([abs(ranks[a] - ranks[b]) for a, b in zip(gold, p)])
        metrics[name] = {"accuracy": float(accuracy_score(gold, p)),
                         "macro_f1": float(f1_score(gold, p, labels=classes, average="macro", zero_division=0)),
                         "recall_high": float(recall_score(gold, p, labels=["high"], average=None, zero_division=0)[0]),
                         "critical_errors": int((distance >= 2).sum()),
                         "mae_levels": float(distance.mean()),
                         "confusion_class_order": classes, "confusion": confusion_matrix(gold, p, labels=classes).tolist()}
    pairs = {}
    for left, right in itertools.combinations(models, 2):
        a, b = predicted[left] == gold, predicted[right] == gold
        wrong_to_correct = int((~a & b).sum())
        correct_to_wrong = int((a & ~b).sum())
        pairs[left + " -> " + right] = {
            "correct_to_wrong": correct_to_wrong, "wrong_to_correct": wrong_to_correct,
            "mcnemar_exact_p_unadjusted": mcnemar_exact(correct_to_wrong, wrong_to_correct),
            "delta_accuracy": metrics[right]["accuracy"] - metrics[left]["accuracy"],
            "delta_macro_f1": metrics[right]["macro_f1"] - metrics[left]["macro_f1"],
            "bootstrap": []}
    # Identical group resamples for all comparisons. Class IDs never define groups.
    rng = np.random.default_rng(20261109)
    for _ in range(draws):
        index = np.concatenate([members[i] for i in rng.integers(0, len(unique), len(unique))])
        scores = {name: float(f1_score(gold[index], p[index], labels=classes,
                                      average="macro", zero_division=0)) for name, p in predicted.items()}
        for name, item in pairs.items():
            left, right = name.split(" -> ")
            item["bootstrap"].append(scores[right] - scores[left])
    corrected = holm({name: item["mcnemar_exact_p_unadjusted"] for name, item in pairs.items()})
    for name, item in pairs.items():
        item["delta_macro_f1_ci95_unadjusted"] = np.quantile(item.pop("bootstrap"), [.025, .975]).tolist()
        item["mcnemar_holm_p"] = corrected[name]
    report = {"status": "DEVELOPMENT_REANALYSIS", "n_images": len(rows), "n_split_groups": len(unique),
              "predictions_sha256": digest(predictions), "split_sha256": digest(split_csv),
              "bootstrap_draws": draws, "metrics": metrics, "pairs": pairs,
              "limits": ["Exact McNemar assumes independent paired units; residual event/source dependence is unresolved",
                         "Bootstrap groups are recorded split groups, not proven independent events",
                         "Macro-F1 intervals unadjusted; Holm family covers all listed McNemar contrasts",
                         "Previously viewed test, no independent confirmation or field-effectiveness claim"]}
    write(output, report)
    return report


def activation_debug(root, ptq, qat, output):
    """One locked validation image per model; report match coverage honestly."""
    import numpy as np
    import onnx
    from onnxruntime.quantization import CalibrationDataReader
    from onnxruntime.quantization.qdq_loss_debug import (
        modify_model_output_intermediate_tensors, collect_activations, create_activation_matching)
    import sys
    sys.path.insert(0, str(root / "products/fe/tools"))
    from quantize_model import preprocess

    output.mkdir(parents=True, exist_ok=False)
    config = json.loads((root / "products/fe/model/Edge Ai/seed1024/config_mobilenetv3_large.json").read_text())
    row = sorted((r for r in csv_rows(root / "products/fe/model/Edge Ai/split_train_val_test_mobilenetv3_large.csv")
                  if r["split"] == "val"), key=lambda r: r["relative_path"])[0]
    image = root / "products/fe/model/Dataset_Flood" / row["relative_path"]
    value = preprocess(image, config["image_size"], config["letterbox_fill"])
    class Reader(CalibrationDataReader):
        def __init__(self, name):
            self.name, self.done = name, False
        def get_next(self):
            if self.done:
                return None
            self.done = True
            return {self.name: value.copy()}
    import onnxruntime as ort
    baseline = root / "products/fe/model/Edge Ai/seed1024/export/baseline/flood_mobilenetv3_large.onnx"
    paths = {"fp32": baseline, "ptq": ptq / "flood_mobilenetv3_large.int8.onnx",
             "qat": qat / "flood_mobilenetv3_large.qat.int8.onnx"}
    options = ort.SessionOptions()
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
    options.intra_op_num_threads = 1
    def collect(name, path):
        temporary = output / (name + "-augmented.onnx")
        modify_model_output_intermediate_tensors(str(path), str(temporary))
        graph = onnx.load(str(path))
        input_name = graph.graph.input[0].name
        try:
            return collect_activations(str(temporary), Reader(input_name), session_options=options,
                                       execution_providers=["CPUExecutionProvider"])
        finally:
            temporary.unlink(missing_ok=True)
    reference = collect("fp32", baseline)
    reports = {}
    for name in ["ptq", "qat"]:
        observed = collect(name, paths[name])
        matches = create_activation_matching(observed, reference)
        errors = []
        for tensor, item in matches.items():
            left, right = item.get("float"), item.get("post_qdq")
            if left is None or right is None or len(left) != len(right):
                continue
            for a, b in zip(left, right):
                if a.shape == b.shape:
                    errors.append({"tensor": tensor, "shape": list(a.shape),
                                   "mean_abs_error": float(np.abs(a - b).mean()),
                                   "max_abs_error": float(np.abs(a - b).max())})
        reports[name] = {"status": "PARTIAL_MATCH" if errors else "NO_MATCHED_TENSORS",
                         "n_quantized_tensors": len(observed), "n_matched": len(errors),
                         "top_errors": sorted(errors, key=lambda r: r["mean_abs_error"], reverse=True)[:30],
                         "onnx_sha256": digest(paths[name])}
        del observed, matches
    write(output / "activation-errors.json", {"status": "VALIDATION_DIAGNOSTIC_ONLY", "reports": reports,
          "image_id": row["relative_path"], "image_sha256": digest(image), "n_validation_images": 1,
          "limits": "Tensor-name matching may be partial, especially QAT; this does not isolate a causal root cause or tune test"})
