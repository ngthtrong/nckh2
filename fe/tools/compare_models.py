"""Kiểm thử & So sánh Chi tiết Model A (best.pth) vs Model B (ONNX Mobile - model.onnx)
Theo quy trình chuẩn NCKH / USENIX 2023 Framework.

Tạo báo cáo toàn diện tại: reports/model_comparison/
  - summary.json
  - summary.md
  - all_predictions.csv
  - model_disagreement.csv
  - confusion_model_a.png
  - confusion_model_b.png
  - calibration_model_a.png
  - calibration_model_b.png

Run:
    .venv\\Scripts\\python.exe tools/compare_models.py
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import onnxruntime as ort
import pandas as pd
import seaborn as sns
from scipy.spatial.distance import jensenshannon
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
import torch
from torch import nn
from torchvision import models, transforms
from PIL import Image, ImageOps, ImageStat

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_A = (
    ROOT
    / "model"
    / "models"
    / "mobilenetv3_large_relabel_v2"
    / "flood_mobilenetv3_large_relabel_v2_best.pth"
)
CHECKPOINT_ONNX = ROOT / "app" / "assets" / "models" / "model.onnx"
CONFIG_JSON = (
    ROOT / "model" / "models" / "mobilenetv3_large_relabel_v2" / "config_mobilenetv3_large_v2.json"
)
SPLIT_CSV = (
    ROOT / "model" / "models" / "mobilenetv3_large_relabel_v2"
    / "split_train_val_test_mobilenetv3_large_v2.csv"
)
DATASET_DIR = ROOT / "model" / "Dataset_Flood"
REPORTS_DIR = ROOT / "reports" / "model_comparison_v2"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def build_model(num_classes: int, dropout: float) -> nn.Module:
    model = models.mobilenet_v3_large(weights=None)
    classifier = list(model.classifier.children())[:-1]
    in_features = model.classifier[-1].in_features
    model.classifier = nn.Sequential(
        *classifier,
        nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(in_features, num_classes),
        ),
    )
    return model


def load_checkpoint(path: Path) -> tuple[dict[str, torch.Tensor], dict]:
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    if isinstance(checkpoint, dict):
        for key in ("model_state_dict", "state_dict", "model"):
            state_dict = checkpoint.get(key)
            if isinstance(state_dict, dict):
                return state_dict, checkpoint
        if all(isinstance(value, torch.Tensor) for value in checkpoint.values()):
            return checkpoint, checkpoint
    raise ValueError(f"Unsupported checkpoint format: {path}")


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 1.0
    return float(np.dot(a, b) / denom)


def compute_ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    confidences = np.max(probs, axis=1)
    predictions = np.argmax(probs, axis=1)
    accuracies = predictions == labels

    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = np.mean(in_bin)

        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(accuracies[in_bin])
            avg_confidence_in_bin = np.mean(confidences[in_bin])
            ece += np.abs(accuracy_in_bin - avg_confidence_in_bin) * prop_in_bin

    return float(ece)


def compute_brier_score(probs: np.ndarray, labels: np.ndarray, num_classes: int) -> float:
    one_hot = np.zeros((len(labels), num_classes))
    for i, l in enumerate(labels):
        one_hot[i, l] = 1.0
    return float(np.mean(np.sum((probs - one_hot) ** 2, axis=1)))


def extract_image_stats(img: Image.Image) -> dict:
    img_rgb = img.convert("RGB")
    w, h = img_rgb.size
    aspect_ratio = float(w) / float(h)

    gray = img_rgb.convert("L")
    stat = ImageStat.Stat(gray)
    brightness = stat.mean[0]
    contrast = stat.stddev[0]

    hsv = img_rgb.convert("HSV")
    s_stat = ImageStat.Stat(hsv)
    saturation = s_stat.mean[1]

    arr = np.array(gray, dtype=np.float32)
    gy, gx = np.gradient(arr)
    sharpness = float(np.mean(gx**2 + gy**2))

    return {
        "width": w,
        "height": h,
        "aspect_ratio": aspect_ratio,
        "brightness": brightness,
        "contrast": contrast,
        "saturation": saturation,
        "sharpness": sharpness,
    }


def main() -> None:
    print("=" * 80)
    print("🔬 SO SÁNH MODEL A (BEST.PTH) VS MODEL B (ONNX MOBILE - MODEL.ONNX)")
    print("=" * 80)

    # 1. Load Config & Devices
    config = json.loads(CONFIG_JSON.read_text(encoding="utf-8"))
    class_order = config["class_order"]
    class_to_idx = {c: i for i, c in enumerate(class_order)}
    num_classes = len(class_order)
    dropout = float(config.get("dropout", 0.35))
    image_size = int(config.get("image_size", 224))
    letterbox_fill = tuple(config.get("letterbox_fill", [124, 116, 104]))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"• Classes ({num_classes}): {class_order}")
    print(f"• PyTorch Device: {device}")
    print(f"• ONNX File: {CHECKPOINT_ONNX.name}")

    # 2. Build Model A (PyTorch best.pth) & Load Model B (ONNX Mobile)
    model_a = build_model(num_classes, dropout)
    state_a, _ = load_checkpoint(CHECKPOINT_A)
    model_a.load_state_dict({k.removeprefix("module."): v for k, v in state_a.items()}, strict=False)
    model_a.to(device).eval()

    onnx_session = ort.InferenceSession(str(CHECKPOINT_ONNX))
    onnx_input_name = onnx_session.get_inputs()[0].name

    transform = transforms.Compose([
        transforms.Lambda(lambda image: ImageOps.pad(
            image,
            (image_size, image_size),
            method=Image.Resampling.BICUBIC,
            color=letterbox_fill,
        )),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # 3. Collect Dataset Images
    split_df = pd.read_csv(SPLIT_CSV)
    test_df = split_df[split_df["split"] == "test"].copy()
    all_image_paths = [Path(path) for path in test_df["path"]]
    all_gt_labels = test_df["label"].tolist()
    all_gt_indices = [class_to_idx[label] for label in all_gt_labels]

    missing = [str(path) for path in all_image_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Test split contains {len(missing)} missing files; first={missing[0]}")

    total_images = len(all_image_paths)
    print(f"✓ Chỉ đánh giá {total_images} ảnh thuộc test split độc lập\n")

    # 4. Evaluation Loop
    results = []
    probs_a_list = []
    probs_b_list = []
    image_stats_list = []

    with torch.no_grad():
        for i, (img_path, gt_label, gt_idx) in enumerate(zip(all_image_paths, all_gt_labels, all_gt_indices)):
            try:
                raw_img = Image.open(img_path).convert("RGB")
                stats = extract_image_stats(raw_img)
                image_stats_list.append(stats)

                tensor_input = transform(raw_img).unsqueeze(0)

                # Model A (PyTorch best.pth)
                out_a = model_a(tensor_input.to(device))
                prob_a = torch.softmax(out_a, dim=1)[0].cpu().numpy()
                sorted_indices_a = np.argsort(prob_a)[::-1]
                pred_a_idx = int(sorted_indices_a[0])
                top2_a_idx = int(sorted_indices_a[1])
                conf_a = float(prob_a[pred_a_idx])
                top2_conf_a = float(prob_a[top2_a_idx])
                margin_a = conf_a - top2_conf_a

                # Model B (ONNX Mobile)
                onnx_out = onnx_session.run(None, {onnx_input_name: tensor_input.numpy()})[0][0]
                prob_b = onnx_out
                sorted_indices_b = np.argsort(prob_b)[::-1]
                pred_b_idx = int(sorted_indices_b[0])
                top2_b_idx = int(sorted_indices_b[1])
                conf_b = float(prob_b[pred_b_idx])
                top2_conf_b = float(prob_b[top2_b_idx])
                margin_b = conf_b - top2_conf_b

                probs_a_list.append(prob_a)
                probs_b_list.append(prob_b)

                # Pairwise distribution metrics
                cos_sim = cosine_similarity(prob_a, prob_b)
                l1_dist = float(np.sum(np.abs(prob_a - prob_b)))
                l2_dist = float(np.sqrt(np.sum((prob_a - prob_b) ** 2)))
                max_abs_diff = float(np.max(np.abs(prob_a - prob_b)))
                js_div = float(jensenshannon(prob_a, prob_b) ** 2)

                is_agree = pred_a_idx == pred_b_idx
                a_correct = pred_a_idx == gt_idx
                b_correct = pred_b_idx == gt_idx

                results.append({
                    "image_path": str(img_path.relative_to(ROOT)),
                    "ground_truth": gt_label,
                    "gt_idx": gt_idx,
                    "pred_model_a": class_order[pred_a_idx],
                    "pred_a_idx": pred_a_idx,
                    "confidence_model_a": conf_a,
                    "top2_model_a": class_order[top2_a_idx],
                    "margin_model_a": margin_a,
                    "pred_model_b": class_order[pred_b_idx],
                    "pred_b_idx": pred_b_idx,
                    "confidence_model_b": conf_b,
                    "top2_model_b": class_order[top2_b_idx],
                    "margin_model_b": margin_b,
                    "a_correct": a_correct,
                    "b_correct": b_correct,
                    "is_agree": is_agree,
                    "cosine_similarity": cos_sim,
                    "l1_distance": l1_dist,
                    "l2_distance": l2_dist,
                    "max_abs_diff": max_abs_diff,
                    "js_divergence": js_div,
                    "prob_a_raw": prob_a.tolist(),
                    "prob_b_raw": prob_b.tolist(),
                })

            except Exception as e:
                print(f"Error processing {img_path}: {e}")

    df_all = pd.DataFrame(results)
    probs_a_arr = np.array(probs_a_list)
    probs_b_arr = np.array(probs_b_list)
    gt_arr = df_all["gt_idx"].values

    # Export all_predictions.csv
    df_all.to_csv(REPORTS_DIR / "all_predictions.csv", index=False)

    # --------------------------------------------------------------------------
    # 1. PREDICTION AGREEMENT
    # --------------------------------------------------------------------------
    agree_count = int(df_all["is_agree"].sum())
    disagree_count = total_images - agree_count
    agree_rate = agree_count / total_images
    disagree_rate = disagree_count / total_images

    # --------------------------------------------------------------------------
    # 2. DISAGREEMENT ANALYSIS
    # --------------------------------------------------------------------------
    df_disagree = df_all[~df_all["is_agree"]].copy()
    df_disagree.to_csv(REPORTS_DIR / "model_disagreement.csv", index=False)

    a_correct_b_wrong = int((df_disagree["a_correct"] & ~df_disagree["b_correct"]).sum())
    a_wrong_b_correct = int((~df_disagree["a_correct"] & df_disagree["b_correct"]).sum())
    both_wrong_diff = int((~df_disagree["a_correct"] & ~df_disagree["b_correct"]).sum())

    # --------------------------------------------------------------------------
    # 3. CONFIDENCE & MARGIN ANALYSIS
    # --------------------------------------------------------------------------
    conf_a_mean = float(df_all["confidence_model_a"].mean())
    conf_a_median = float(df_all["confidence_model_a"].median())
    conf_b_mean = float(df_all["confidence_model_b"].mean())
    conf_b_median = float(df_all["confidence_model_b"].median())

    margin_a_mean = float(df_all["margin_model_a"].mean())
    margin_a_median = float(df_all["margin_model_a"].median())
    margin_b_mean = float(df_all["margin_model_b"].mean())
    margin_b_median = float(df_all["margin_model_b"].median())

    margin_a_005 = int((df_all["margin_model_a"] < 0.05).sum())
    margin_a_010 = int((df_all["margin_model_a"] < 0.10).sum())
    margin_b_005 = int((df_all["margin_model_b"] < 0.05).sum())
    margin_b_010 = int((df_all["margin_model_b"] < 0.10).sum())

    # Disagreement subset confidence & margin
    if not df_disagree.empty:
        dis_conf_a_mean = float(df_disagree["confidence_model_a"].mean())
        dis_conf_b_mean = float(df_disagree["confidence_model_b"].mean())
        dis_margin_a_mean = float(df_disagree["margin_model_a"].mean())
        dis_margin_b_mean = float(df_disagree["margin_model_b"].mean())
    else:
        dis_conf_a_mean = dis_conf_b_mean = dis_margin_a_mean = dis_margin_b_mean = 0.0

    # --------------------------------------------------------------------------
    # 4. PROBABILITY DISTRIBUTION COMPARISON
    # --------------------------------------------------------------------------
    dist_metrics = {}
    for metric_col in ["cosine_similarity", "l1_distance", "l2_distance", "max_abs_diff", "js_divergence"]:
        dist_metrics[metric_col] = {
            "mean": float(df_all[metric_col].mean()),
            "median": float(df_all[metric_col].median()),
            "p95": float(np.percentile(df_all[metric_col], 95)),
            "max": float(df_all[metric_col].max()),
        }

    # --------------------------------------------------------------------------
    # 5. CLASSIFICATION METRICS
    # --------------------------------------------------------------------------
    preds_a = df_all["pred_a_idx"].values
    preds_b = df_all["pred_b_idx"].values

    acc_a = float(accuracy_score(gt_arr, preds_a))
    acc_b = float(accuracy_score(gt_arr, preds_b))

    bal_acc_a = float(balanced_accuracy_score(gt_arr, preds_a))
    bal_acc_b = float(balanced_accuracy_score(gt_arr, preds_b))

    macro_f1_a = float(f1_score(gt_arr, preds_a, average="macro"))
    macro_f1_b = float(f1_score(gt_arr, preds_b, average="macro"))

    p_a, r_a, f1_a, _ = precision_recall_fscore_support(gt_arr, preds_a, labels=list(range(num_classes)))
    p_b, r_b, f1_b, _ = precision_recall_fscore_support(gt_arr, preds_b, labels=list(range(num_classes)))

    per_class_metrics = {}
    for idx, cls in enumerate(class_order):
        per_class_metrics[cls] = {
            "precision_a": float(p_a[idx]),
            "precision_b": float(p_b[idx]),
            "recall_a": float(r_a[idx]),
            "recall_b": float(r_b[idx]),
            "f1_a": float(f1_a[idx]),
            "f1_b": float(f1_b[idx]),
            "diff_recall": float(r_b[idx] - r_a[idx]),
        }

    cm_a = confusion_matrix(gt_arr, preds_a, labels=list(range(num_classes)))
    cm_b = confusion_matrix(gt_arr, preds_b, labels=list(range(num_classes)))

    # Save Confusion Matrix Plots
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(cm_a, annot=True, fmt="d", cmap="Reds", xticklabels=class_order, yticklabels=class_order, ax=ax)
    ax.set_title("Confusion Matrix - Model A (PyTorch Best.pth)")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Ground Truth")
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "confusion_model_a.png", dpi=200)
    plt.close()

    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(cm_b, annot=True, fmt="d", cmap="Blues", xticklabels=class_order, yticklabels=class_order, ax=ax)
    ax.set_title("Confusion Matrix - Model B (ONNX Mobile)")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Ground Truth")
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "confusion_model_b.png", dpi=200)
    plt.close()

    # --------------------------------------------------------------------------
    # 8. IMAGE STATISTICAL DISTRIBUTION
    # --------------------------------------------------------------------------
    df_stats = pd.DataFrame(image_stats_list)
    image_dist_stats = {}
    for col in ["brightness", "contrast", "sharpness", "saturation", "aspect_ratio"]:
        image_dist_stats[col] = {
            "mean": float(df_stats[col].mean()),
            "std": float(df_stats[col].std()),
            "median": float(df_stats[col].median()),
            "p5": float(np.percentile(df_stats[col], 5)),
            "p95": float(np.percentile(df_stats[col], 95)),
        }

    # --------------------------------------------------------------------------
    # 9. CALIBRATION (ECE & Brier Score)
    # --------------------------------------------------------------------------
    ece_a = compute_ece(probs_a_arr, gt_arr)
    ece_b = compute_ece(probs_b_arr, gt_arr)

    brier_a = compute_brier_score(probs_a_arr, gt_arr, num_classes)
    brier_b = compute_brier_score(probs_b_arr, gt_arr, num_classes)

    # Plot Calibration Reliability Diagrams
    fig, ax = plt.subplots(figsize=(6, 6))
    conf_a_max = np.max(probs_a_arr, axis=1)
    acc_a_corr = (preds_a == gt_arr).astype(float)
    bin_bounds = np.linspace(0, 1, 11)
    bin_accs_a = []
    bin_confs_a = []
    for b in range(10):
        mask = (conf_a_max > bin_bounds[b]) & (conf_a_max <= bin_bounds[b+1])
        if np.sum(mask) > 0:
            bin_accs_a.append(np.mean(acc_a_corr[mask]))
            bin_confs_a.append(np.mean(conf_a_max[mask]))
        else:
            bin_accs_a.append(0)
            bin_confs_a.append((bin_bounds[b] + bin_bounds[b+1])/2)
    ax.plot([0, 1], [0, 1], "k--", label="Perfect Calibration")
    ax.plot(bin_confs_a, bin_accs_a, "s-", color="red", label=f"Model A PyTorch (ECE={ece_a:.4f})")
    ax.set_title("Reliability Diagram - Model A (PyTorch Best.pth)")
    ax.set_xlabel("Confidence")
    ax.set_ylabel("Accuracy")
    ax.legend()
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "calibration_model_a.png", dpi=200)
    plt.close()

    fig, ax = plt.subplots(figsize=(6, 6))
    conf_b_max = np.max(probs_b_arr, axis=1)
    acc_b_corr = (preds_b == gt_arr).astype(float)
    bin_accs_b = []
    bin_confs_b = []
    for b in range(10):
        mask = (conf_b_max > bin_bounds[b]) & (conf_b_max <= bin_bounds[b+1])
        if np.sum(mask) > 0:
            bin_accs_b.append(np.mean(acc_b_corr[mask]))
            bin_confs_b.append(np.mean(conf_b_max[mask]))
        else:
            bin_accs_b.append(0)
            bin_confs_b.append((bin_bounds[b] + bin_bounds[b+1])/2)
    ax.plot([0, 1], [0, 1], "k--", label="Perfect Calibration")
    ax.plot(bin_confs_b, bin_accs_b, "o-", color="blue", label=f"Model B ONNX (ECE={ece_b:.4f})")
    ax.set_title("Reliability Diagram - Model B (ONNX Mobile)")
    ax.set_xlabel("Confidence")
    ax.set_ylabel("Accuracy")
    ax.legend()
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "calibration_model_b.png", dpi=200)
    plt.close()

    # --------------------------------------------------------------------------
    # 13. CASE CLASSIFICATION DECISION
    # --------------------------------------------------------------------------
    if agree_rate >= 0.999 and abs(acc_a - acc_b) < 0.001:
        case_decision = "CASE A — Hai model thực sự tương đương 100% (High Agreement & Identical Distribution)"
    elif agree_rate < 0.98:
        case_decision = "CASE B — Decision Behavior có sự khác biệt (Disagreement Detected)"
    else:
        case_decision = "CASE A — Tương đương cao"

    # Save Summary
    summary_data = {
        "metadata": {
            "checkpoint_model_a": str(CHECKPOINT_A),
            "checkpoint_model_b_onnx": str(CHECKPOINT_ONNX),
            "dataset_path": str(DATASET_DIR),
            "total_samples": total_images,
            "class_ordering": class_order,
            "pytorch_version": torch.__version__,
            "device": str(device),
        },
        "agreement": {
            "total_images": total_images,
            "agree_count": agree_count,
            "disagree_count": disagree_count,
            "agree_rate": agree_rate,
            "disagree_rate": disagree_rate,
        },
        "disagreement_breakdown": {
            "a_correct_b_wrong": a_correct_b_wrong,
            "a_wrong_b_correct": a_wrong_b_correct,
            "both_wrong_diff_class": both_wrong_diff,
        },
        "confidence_margin": {
            "model_a_pytorch": {
                "conf_mean": conf_a_mean,
                "conf_median": conf_a_median,
                "margin_mean": margin_a_mean,
                "margin_median": margin_a_median,
            },
            "model_b_onnx": {
                "conf_mean": conf_b_mean,
                "conf_median": conf_b_median,
                "margin_mean": margin_b_mean,
                "margin_median": margin_b_median,
            },
        },
        "probability_distribution_metrics": dist_metrics,
        "classification_metrics": {
            "model_a_pytorch": {"accuracy": acc_a, "balanced_accuracy": bal_acc_a, "macro_f1": macro_f1_a, "ece": ece_a, "brier_score": brier_a},
            "model_b_onnx": {"accuracy": acc_b, "balanced_accuracy": bal_acc_b, "macro_f1": macro_f1_b, "ece": ece_b, "brier_score": brier_b},
            "per_class": per_class_metrics,
        },
        "image_distribution_stats": image_dist_stats,
        "case_decision": case_decision,
    }

    with open(REPORTS_DIR / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    summary_md = f"""# Báo Cáo So Sánh Chi Tiết Model A (PyTorch Best.pth) vs Model B (ONNX Mobile)

## 📌 Kết Luận Phân Loại Trường Hợp (Case Decision)
> **{case_decision}**

---

## 1. Prediction Agreement
- **Tổng số ảnh kiểm thử:** {total_images}
- **Số ảnh đồng thuận (Agreement count):** {agree_count}
- **Số ảnh bất đồng (Disagreement count):** {disagree_count}
- **Tỷ lệ đồng thuận (Agreement rate):** **{agree_rate * 100:.4f}%**
- **Tỷ lệ bất đồng (Disagreement rate):** **{disagree_rate * 100:.4f}%**

---

## 2. Phân Tích Bất Đồng (Disagreement Breakdown)
- **Model A (PyTorch) đúng, Model B (ONNX) sai:** {a_correct_b_wrong} ảnh
- **Model A (PyTorch) sai, Model B (ONNX) đúng:** {a_wrong_b_correct} ảnh
- **Cả hai cùng sai (khác class):** {both_wrong_diff} ảnh

---

## 3. So Sánh Metric Phân Loại (Classification Metrics)

| Chỉ số (Metric) | Model A (PyTorch Best.pth) | Model B (ONNX Mobile) | Chênh lệch (ONNX - PyTorch) |
| :--- | :---: | :---: | :---: |
| **Accuracy** | {acc_a * 100:.2f}% | {acc_b * 100:.2f}% | {(acc_b - acc_a) * 100:+.2f}% |
| **Balanced Accuracy** | {bal_acc_a * 100:.2f}% | {bal_acc_b * 100:.2f}% | {(bal_acc_b - bal_acc_a) * 100:+.2f}% |
| **Macro F1 Score** | {macro_f1_a * 100:.2f}% | {macro_f1_b * 100:.2f}% | {(macro_f1_b - macro_f1_a) * 100:+.2f}% |
| **ECE (Calibration Error)** | {ece_a:.4f} | {ece_b:.4f} | {ece_b - ece_a:+.4f} |
| **Brier Score** | {brier_a:.4f} | {brier_b:.4f} | {brier_b - brier_a:+.4f} |

---

## 4. Bảng Chỉ Số Phân Bố Xác Suất (Distribution Comparison)

- **Cosine Similarity (Mean):** **{dist_metrics['cosine_similarity']['mean']:.8f}**
- **L1 Distance (Mean):** {dist_metrics['l1_distance']['mean']:.8f}
- **Max Absolute Difference (Mean):** {dist_metrics['max_abs_diff']['mean']:.8f}
- **Jensen-Shannon Divergence (Mean):** {dist_metrics['js_divergence']['mean']:.8f}

---

## 📁 Tệp Báo Cáo Đã Xuất:
- `reports/model_comparison/summary.json`
- `reports/model_comparison/summary.md`
- `reports/model_comparison/all_predictions.csv`
- `reports/model_comparison/model_disagreement.csv`
- `reports/model_comparison/confusion_model_a.png`
- `reports/model_comparison/confusion_model_b.png`
- `reports/model_comparison/calibration_model_a.png`
- `reports/model_comparison/calibration_model_b.png`
"""

    with open(REPORTS_DIR / "summary.md", "w", encoding="utf-8") as f:
        f.write(summary_md)

    print("=" * 80)
    print("✅ HOÀN THÀNH SO SÁNH MODEL A (PyTorch) VS MODEL B (ONNX Mobile)!")
    print(f"👉 Kết luận: {case_decision}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
