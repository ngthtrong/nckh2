"""Channel-prune MobileNetV3, fine-tune on the saved train split, and evaluate once.

Requires torch-pruning==1.6.1. From tools/: python structured_pruning.py
Resume with: python structured_pruning.py --resume [--batch-size 2]
Output defaults to model/Edge Ai/StructuredPruning_v1; the source model is never changed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import logging
import random
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

from compare_models import CONFIG_JSON, DATASET_DIR, EDGE_DIR, SPLIT_CSV, classification_metrics
from convert_model import build_model, load_checkpoint, remove_module_prefix
from quantize_model import load_splits


LOGGER = logging.getLogger("structured_pruning")
DEFAULT_OUTPUT = EDGE_DIR / "StructuredPruning_v1"


def seed_everything(seed: int) -> None:
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


class FloodDataset:
    def __init__(self, items, config: dict, train: bool):
        from torchvision import transforms

        self.items = items
        size = int(config["image_size"])
        fill = tuple(config["letterbox_fill"])
        mean = [0.485, 0.456, 0.406]
        std = [0.229, 0.224, 0.225]
        steps = []
        if train:
            steps += [
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomAffine(degrees=4, translate=(0.03, 0.03),
                                        scale=(0.95, 1.05), fill=fill),
                transforms.ColorJitter(brightness=0.12, contrast=0.12,
                                       saturation=0.08, hue=0.02),
            ]
        steps += [transforms.ToTensor(), transforms.Normalize(mean, std)]
        self.transform = transforms.Compose(steps)
        self.size = size
        self.fill = fill

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        path, label = self.items[index]
        try:
            with Image.open(path) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
                image = ImageOps.pad(image, (self.size, self.size),
                                     method=Image.Resampling.BILINEAR,
                                     color=self.fill, centering=(0.5, 0.5))
            return self.transform(image), label
        except Exception as error:
            raise RuntimeError(f"Không đọc được ảnh {path}: {error}") from error


def evaluate(model, loader, config: dict, device):
    import torch
    from torch.nn import functional as F

    ranks_by_name = {"non_flood": 0, "low": 1, "medium": 2, "high": 3}
    ranks = torch.tensor([ranks_by_name[name] for name in config["class_order"]],
                         dtype=torch.float32, device=device)
    true_labels, probabilities = [], []
    total_loss = 0.0
    severity_weight = float(config.get("severity_loss_weight", 0.0))
    model.eval()
    with torch.inference_mode():
        for images, labels in loader:
            images = images.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)
            logits = model(images)
            loss = F.cross_entropy(logits, labels, label_smoothing=float(config.get("label_smoothing", 0.0)))
            probs = torch.softmax(logits, dim=1)
            severity = (probs * (ranks.unsqueeze(0) - ranks[labels].unsqueeze(1)).abs()).sum(1).mean()
            total_loss += float((loss + severity_weight * severity).item()) * labels.size(0)
            true_labels.extend(labels.cpu().tolist())
            probabilities.extend(probs.cpu().tolist())
    metrics = classification_metrics(np.asarray(probabilities), np.asarray(true_labels),
                                     config["class_order"], int(config.get("critical_distance", 2)))
    metrics["loss"] = total_loss / len(loader.dataset)
    return metrics


def train_epoch(model, loader, optimizer, scaler, config: dict, device, freeze_backbone: bool) -> float:
    import torch
    from torch.nn import functional as F

    ranks_by_name = {"non_flood": 0, "low": 1, "medium": 2, "high": 3}
    ranks = torch.tensor([ranks_by_name[name] for name in config["class_order"]],
                         dtype=torch.float32, device=device)
    model.train()
    if freeze_backbone:
        model.features.eval()
    total = 0.0
    seen = 0
    for images, labels in loader:
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)
        optimizer.zero_grad(set_to_none=True)
        with torch.autocast(device_type="cuda", dtype=torch.float16):
            logits = model(images)
            ce = F.cross_entropy(logits, labels, label_smoothing=float(config.get("label_smoothing", 0.0)))
            probs = torch.softmax(logits, dim=1)
            severity = (probs * (ranks.unsqueeze(0) - ranks[labels].unsqueeze(1)).abs()).sum(1).mean()
            loss = ce + float(config.get("severity_loss_weight", 0.0)) * severity
        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=3.0)
        scaler.step(optimizer)
        scaler.update()
        total += float(loss.item()) * labels.size(0)
        seen += labels.size(0)
    return total / seen


def atomic_save_model(model, path: Path, payload: dict, device) -> None:
    import torch

    temporary = path.with_suffix(path.suffix + ".tmp")
    model.to("cpu")
    try:
        torch.save({**payload, "model": model}, temporary)
        temporary.replace(path)
    finally:
        model.to(device)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=EDGE_DIR / "flood_mobilenetv3_large_best.pth")
    parser.add_argument("--config", type=Path, default=CONFIG_JSON)
    parser.add_argument("--split-csv", type=Path, default=SPLIT_CSV)
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--prune-ratio", type=float, default=0.01, help="Fraction of channels to prune.")
    parser.add_argument("--epochs", type=int, help="Defaults to the training config (35).")
    parser.add_argument("--batch-size", type=int, default=8, help="Default 8 for a 4 GB GPU.")
    parser.add_argument("--prune-only", action="store_true", help="Check pruning/forward on GPU without training or saving.")
    parser.add_argument("--resume", nargs="?", const="auto",
                        help="Resume from last_training.pt; omit path to find it in --output-dir.")
    args = parser.parse_args()
    if not 0 < args.prune_ratio < 0.8 or args.batch_size < 1:
        parser.error("--prune-ratio must be in (0, 0.8), and --batch-size must be positive.")
    if args.prune_only and args.resume:
        parser.error("--prune-only không dùng cùng --resume.")
    resume_path = None
    if args.resume:
        if args.resume == "auto":
            latest = args.output_dir / "last_training.pt"
            best = args.output_dir / "flood_mobilenetv3_large_structured_best.pt"
            resume_path = latest if latest.is_file() else best
        else:
            resume_path = Path(args.resume)
        if not resume_path.is_file():
            parser.error(f"Resume checkpoint không tồn tại: {resume_path}")
        if resume_path.resolve().parent != args.output_dir.resolve():
            parser.error("Resume cần dùng cùng --output-dir với checkpoint để giữ nguyên best model và log.")
    if (not args.prune_only and args.output_dir.exists() and any(args.output_dir.iterdir())
            and resume_path is None):
        parser.error(f"Output directory is not empty; use a new --output-dir: {args.output_dir}")

    import torch
    try:
        import torch_pruning as tp
    except ImportError as error:
        raise SystemExit("Missing torch-pruning. Install with: python -m pip install torch-pruning==1.6.1") from error
    if not torch.cuda.is_available():
        raise SystemExit("CUDA chưa khả dụng trong PyTorch; từ chối chạy giả trên CPU.")
    device = torch.device("cuda")
    torch.set_num_threads(1)

    config = json.loads(args.config.read_text(encoding="utf-8"))
    classes = config["class_order"]
    seed_everything(int(config.get("seed", 42)))
    splits = load_splits(args.split_csv, args.dataset_dir, classes)
    if not splits["val"] or any(not any(label == i for _, label in splits["train"])
                                for i in range(len(classes))):
        raise ValueError("Train cần đủ 4 lớp và validation không được rỗng.")
    LOGGER.info("Saved split loaded: train=%d val=%d test=%d; test is held out until final eval",
                len(splits["train"]), len(splits["val"]), len(splits["test"]))

    checkpoint_sha = hashlib.sha256(args.checkpoint.read_bytes()).hexdigest()
    state, source_checkpoint = load_checkpoint(args.checkpoint)
    state = remove_module_prefix(state)
    if source_checkpoint.get("class_names") and list(source_checkpoint["class_names"]) != classes:
        raise ValueError("Checkpoint class_names không khớp config.")
    for key in ("image_size", "preprocess", "letterbox_fill"):
        saved, configured = source_checkpoint.get(key), config.get(key)
        if key == "letterbox_fill" and saved is not None and configured is not None:
            saved, configured = list(saved), list(configured)
        if saved is not None and saved != configured:
            raise ValueError(f"Checkpoint/config không khớp trường {key}.")
    nested = "classifier.3.1.weight" in state
    model = build_model(len(classes), float(config.get("dropout", 0.25)), nested_classifier=nested)
    model.load_state_dict(state, strict=True)
    base_params = sum(parameter.numel() for parameter in model.parameters())

    loaders = {}
    generator = torch.Generator().manual_seed(int(config.get("seed", 42)))
    for name in ("train", "val", "test"):
        dataset = FloodDataset(splits[name], config, train=(name == "train"))
        loaders[name] = torch.utils.data.DataLoader(
            dataset, batch_size=args.batch_size, shuffle=(name == "train"),
            num_workers=0, pin_memory=True, generator=generator if name == "train" else None)

    baseline_val = evaluate(model.to(device), loaders["val"], config, device)
    pruner = None
    resume_payload = None
    initial_pruned_val = None
    pruning_info = None
    if resume_path is not None:
        resume_payload = torch.load(resume_path, map_location="cpu", weights_only=False)
        if not isinstance(resume_payload, dict) or not isinstance(resume_payload.get("model"), torch.nn.Module):
            raise ValueError("Resume checkpoint cần chứa full model trong trường 'model'.")
        if resume_payload.get("source_checkpoint_sha256") != checkpoint_sha:
            raise ValueError("Resume checkpoint được tạo từ source checkpoint khác.")
        if list(resume_payload.get("class_names", [])) != classes:
            raise ValueError("class_names trong resume checkpoint không khớp config.")
        saved_config = resume_payload.get("config", {})
        for key in ("image_size", "preprocess", "class_order", "letterbox_fill"):
            saved, configured = saved_config.get(key), config.get(key)
            if key == "letterbox_fill" and saved is not None and configured is not None:
                saved, configured = list(saved), list(configured)
            if saved != configured:
                raise ValueError(f"Config trong resume checkpoint không khớp trường {key}.")
        if resume_payload.get("training_state_version") == 1:
            expected_config_sha = hashlib.sha256(args.config.read_bytes()).hexdigest()
            expected_split_sha = hashlib.sha256(args.split_csv.read_bytes()).hexdigest()
            if (resume_payload.get("config_sha256") != expected_config_sha
                    or resume_payload.get("split_csv_sha256") != expected_split_sha):
                raise ValueError("Resume bị từ chối: config hoặc split CSV đã đổi kể từ checkpoint.")
        pruning_info = resume_payload.get("pruning")
        if not isinstance(pruning_info, dict) or pruning_info.get("method") != "global_group_magnitude_channel":
            raise ValueError("Resume checkpoint không có metadata structured pruning hợp lệ.")
        model = resume_payload["model"].cpu()
        pruned_params = sum(parameter.numel() for parameter in model.parameters())
        if pruned_params != int(pruning_info["parameter_count_after"]):
            raise ValueError("Số parameter trong resume checkpoint không khớp metadata.")
        initial_pruned_val = resume_payload.get("initial_pruned_validation")
        start_epoch = int(resume_payload.get("epoch", 0)) + 1
        if not (args.output_dir / "flood_mobilenetv3_large_structured_best.pt").is_file():
            raise FileNotFoundError("Thiếu best model trong output-dir; không thể resume an toàn.")
        LOGGER.info("Resume source: %s (next epoch=%d)", resume_path, start_epoch)
    else:
        model.cpu().eval()
        example = torch.zeros(1, 3, int(config["image_size"]), int(config["image_size"]))
        final_linear = model.classifier[-1]
        if isinstance(final_linear, torch.nn.Sequential):
            final_linear = final_linear[-1]
        pruner = tp.pruner.MagnitudePruner(
            model, example_inputs=example,
            importance=tp.importance.GroupMagnitudeImportance(p=2),
            pruning_ratio=args.prune_ratio, iterative_steps=1, global_pruning=True,
            ignored_layers=[final_linear], round_to=None)
        pruner.step()
        pruned_params = sum(parameter.numel() for parameter in model.parameters())
        if pruned_params >= base_params:
            raise RuntimeError("Pruner không giảm số tham số; không lưu model rỗng hiệu quả.")
        with torch.inference_mode():
            if tuple(model(example).shape) != (1, len(classes)):
                raise RuntimeError("Shape output sau pruning không khớp số lớp.")
        initial_pruned_val = evaluate(model.to(device), loaders["val"], config, device)
        pruning_info = {
            "method": "global_group_magnitude_channel", "target_ratio": args.prune_ratio,
            "round_to": None, "parameter_count_before": base_params,
            "parameter_count_after": pruned_params,
        }
        start_epoch = 1
    if args.prune_only:
        print(json.dumps({
            "gpu": torch.cuda.get_device_name(0), "torch": torch.__version__,
            "torch_pruning": importlib.metadata.version("torch-pruning"),
            "parameters_before": base_params, "parameters_after": pruned_params,
            "baseline_val_accuracy": baseline_val["accuracy"],
            "pruned_val_accuracy_before_finetune": initial_pruned_val["accuracy"],
            "training": "not run", "test inference": "not run",
        }, indent=2))
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(args.output_dir / "training.log", mode="a" if resume_path else "w",
                                                     encoding="utf-8"),
                                  logging.StreamHandler()])
    LOGGER.info("GPU: %s | torch=%s | torch-pruning=%s", torch.cuda.get_device_name(0),
                torch.__version__, importlib.metadata.version("torch-pruning"))
    LOGGER.info("Source checkpoint: %s", args.checkpoint)
    LOGGER.info("Starting fine-tune ratio=%.2f%s", pruning_info["target_ratio"],
                f" from epoch {start_epoch}" if resume_path else "")

    if initial_pruned_val is not None:
        LOGGER.info("Params: %d -> %d (%.1f%% fewer); pre-finetune val acc %.4f -> %.4f",
                    base_params, pruned_params, 100 * (1 - pruned_params / base_params),
                    baseline_val["accuracy"], initial_pruned_val["accuracy"])

    epochs = int(args.epochs or config.get("num_epochs", 35))
    patience = int(config.get("patience", 7))
    freeze_epochs = int(config.get("freeze_backbone_epochs", 3))
    for parameter in model.features.parameters():
        parameter.requires_grad = start_epoch > freeze_epochs
    optimizer = torch.optim.AdamW([
        {"params": model.features.parameters(), "lr": float(config.get("backbone_lr", 1e-5))},
        {"params": model.classifier.parameters(), "lr": float(config.get("head_lr", 2e-4))},
    ], weight_decay=float(config.get("weight_decay", 5e-4)))
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5,
                                                            patience=3, min_lr=1e-7)
    scaler = torch.amp.GradScaler("cuda", enabled=True)
    model.to(device)
    best_path = args.output_dir / "flood_mobilenetv3_large_structured_best.pt"
    latest_path = args.output_dir / "last_training.pt"
    best_metrics = (resume_payload or {}).get("validation_metrics") or {}
    best_accuracy = float((resume_payload or {}).get("best_accuracy", best_metrics.get("accuracy", -1.0)))
    best_critical = float((resume_payload or {}).get("best_critical", best_metrics.get("critical_error_count", float("inf"))))
    max_accuracy_seen = float((resume_payload or {}).get("max_accuracy_seen", best_accuracy))
    best_epoch = int((resume_payload or {}).get("best_epoch", (resume_payload or {}).get("epoch", 0)))
    stale_epochs = int((resume_payload or {}).get("stale_epochs", 0))
    history = list((resume_payload or {}).get("history", []))
    if resume_payload and resume_payload.get("training_state_version") == 1:
        optimizer.load_state_dict(resume_payload["optimizer_state"])
        scheduler.load_state_dict(resume_payload["scheduler_state"])
        scaler.load_state_dict(resume_payload["scaler_state"])
        if args.batch_size != int(resume_payload["batch_size"]):
            LOGGER.warning("Batch size changed %d -> %d; optimizer resumes, but batch trajectory differs.",
                           int(resume_payload["batch_size"]), args.batch_size)
        rng = resume_payload["rng_state"]
        random.setstate(rng["python"])
        np.random.set_state(rng["numpy"])
        torch.set_rng_state(rng["torch"])
        torch.cuda.set_rng_state_all(rng["cuda"])
        generator.set_state(rng["loader"])
        baseline_val = resume_payload["baseline_validation"]
        initial_pruned_val = resume_payload["initial_pruned_validation"]
        LOGGER.info("Restored optimizer, scheduler, scaler, and RNG state.")
    elif resume_payload:
        LOGGER.warning("Warm-resuming weights from best checkpoint at epoch %d; optimizer/RNG state was not saved by the old run.",
                       start_epoch - 1)

    for epoch in range(start_epoch, epochs + 1):
        started = time.perf_counter()
        frozen = epoch <= freeze_epochs
        if epoch == freeze_epochs + 1:
            for parameter in model.features.parameters():
                parameter.requires_grad = True
        train_loss = train_epoch(model, loaders["train"], optimizer, scaler, config, device, frozen)
        val = evaluate(model, loaders["val"], config, device)
        accuracy = val["accuracy"]
        max_accuracy_seen = max(max_accuracy_seen, accuracy)
        scheduler.step(accuracy)
        is_best = (best_epoch == 0 or accuracy > best_accuracy + float(config.get("accuracy_tie_tolerance", 0.005))
                   or (accuracy >= max_accuracy_seen - float(config.get("accuracy_tie_tolerance", 0.005))
                       and val.get("critical_error_count", float("inf")) < best_critical))
        if is_best:
            best_accuracy = accuracy
            best_critical = val.get("critical_error_count", float("inf"))
            best_epoch = epoch
            stale_epochs = 0
            best_metrics = val
            atomic_save_model(model, best_path, {
                "class_names": classes, "config": config, "epoch": epoch,
                "validation_metrics": val, "source_checkpoint_sha256": checkpoint_sha,
                "pruning": pruning_info,
            }, device)
        else:
            stale_epochs += 1
        row = {"epoch": epoch, "train_loss": train_loss, "val_accuracy": accuracy,
               "val_macro_f1": val["macro_f1"], "val_critical_error_count": val.get("critical_error_count"),
               "val_critical_error_rate": val.get("critical_error_rate"), "selected_best": is_best,
               "seconds": time.perf_counter() - started}
        history.append(row)
        LOGGER.info("epoch=%d/%d train_loss=%.4f val_acc=%.4f macro_f1=%.4f critical=%s best=%s time=%.1fs",
                    epoch, epochs, train_loss, accuracy, val["macro_f1"],
                    val.get("critical_error_count", "n/a"), is_best, row["seconds"])
        atomic_save_model(model, latest_path, {
            "training_state_version": 1, "class_names": classes, "config": config,
            "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
            "split_csv_sha256": hashlib.sha256(args.split_csv.read_bytes()).hexdigest(),
            "source_checkpoint_sha256": checkpoint_sha, "pruning": pruning_info,
            "epoch": epoch, "best_epoch": best_epoch, "best_accuracy": best_accuracy,
            "best_critical": best_critical, "max_accuracy_seen": max_accuracy_seen,
            "stale_epochs": stale_epochs, "validation_metrics": best_metrics,
            "baseline_validation": baseline_val,
            "initial_pruned_validation": initial_pruned_val, "history": history,
            "batch_size": args.batch_size, "optimizer_state": optimizer.state_dict(),
            "scheduler_state": scheduler.state_dict(), "scaler_state": scaler.state_dict(),
            "rng_state": {
                "python": random.getstate(), "numpy": np.random.get_state(),
                "torch": torch.get_rng_state(), "cuda": torch.cuda.get_rng_state_all(),
                "loader": generator.get_state(),
            },
        }, device)
        if stale_epochs >= patience:
            LOGGER.info("Early stop at epoch %d; best epoch=%d", epoch, best_epoch)
            break

    del model, optimizer, scheduler, scaler
    if pruner is not None:
        del pruner
    torch.cuda.empty_cache()
    best_payload = torch.load(best_path, map_location="cpu", weights_only=False)
    best_model = best_payload["model"].to(device).eval()
    test_metrics = evaluate(best_model, loaders["test"], config, device)
    report = {
        "evaluation_protocol": "train_and_select_on_saved_train_val; test evaluated once after best epoch",
        "device": torch.cuda.get_device_name(0), "torch_version": torch.__version__,
        "source_checkpoint": str(args.checkpoint.resolve()), "source_checkpoint_sha256": checkpoint_sha,
        "split_csv": str(args.split_csv.resolve()), "counts": {key: len(value) for key, value in splits.items()},
        "pruning": best_payload["pruning"], "baseline_validation": baseline_val,
        "pruned_before_finetune_validation": initial_pruned_val,
        "best_epoch": best_epoch, "best_validation": best_payload["validation_metrics"],
        "final_test": test_metrics, "history": history,
    }
    (args.output_dir / "metrics.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                                                     encoding="utf-8")
    if history:
        with (args.output_dir / "history.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=history[0].keys())
            writer.writeheader()
            writer.writerows(history)
    LOGGER.info("Final test: acc=%.4f macro_f1=%.4f critical=%s/%d",
                test_metrics["accuracy"], test_metrics["macro_f1"],
                test_metrics.get("critical_error_count", "n/a"), len(splits["test"]))
    LOGGER.info("Saved model=%s metrics=%s", best_path, args.output_dir / "metrics.json")


if __name__ == "__main__":
    main()
