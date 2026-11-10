"""Optional fresh ImageNet initialization on the existing locked image split."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "products/fe/tools"))
from structured_pruning import FloodDataset, evaluate, seed_everything, train_epoch
from quantize_model import load_splits
from runtime import digest, write


def main():
    import torch
    from torchvision.models import mobilenet_v3_large
    parser = argparse.ArgumentParser()
    for arg in ["checkpoint", "config", "split-csv", "dataset-dir", "output-dir"]:
        parser.add_argument("--" + arg, type=Path, required=True)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required for optional baseline training")
    config = json.loads(args.config.read_text())
    target = args.output_dir
    target.mkdir(parents=True, exist_ok=False)
    seed_everything(config["seed"])
    device = torch.device("cuda")
    split = load_splits(args.split_csv, args.dataset_dir, config["class_order"])
    weights = ROOT / "thucnghiem/vi_rescue/cache/torch/checkpoints/mobilenet_v3_large-5c1a4163.pth"
    model = mobilenet_v3_large(weights=None)
    model.load_state_dict(torch.load(weights, map_location="cpu", weights_only=True), strict=True)
    model.classifier[-2] = torch.nn.Dropout(config["dropout"])
    model.classifier[-1] = torch.nn.Linear(model.classifier[-1].in_features, len(config["class_order"]))
    model.to(device)
    generator = torch.Generator().manual_seed(config["seed"])
    loaders = {name: torch.utils.data.DataLoader(FloodDataset(items, config, name == "train"),
              batch_size=config["batch_size"], shuffle=name == "train", num_workers=0,
              pin_memory=True, generator=generator if name == "train" else None)
              for name, items in split.items()}
    optimizer = torch.optim.AdamW([
        {"params": model.features.parameters(), "lr": config["backbone_lr"]},
        {"params": model.classifier.parameters(), "lr": config["head_lr"]}], weight_decay=config["weight_decay"])
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=.5, patience=3, min_lr=1e-7)
    scaler = torch.amp.GradScaler("cuda", enabled=config["use_amp"])
    history, best_accuracy, max_accuracy, best_critical, stale = [], -1., -1., float("inf"), 0
    best = target / "best.pth"
    for epoch in range(1, config["num_epochs"] + 1):
        frozen = epoch <= config["freeze_backbone_epochs"]
        for p in model.features.parameters():
            p.requires_grad = not frozen
        started = time.monotonic()
        loss = train_epoch(model, loaders["train"], optimizer, scaler, config, device, frozen)
        val = evaluate(model, loaders["val"], config, device)
        accuracy = val["accuracy"]
        max_accuracy = max(max_accuracy, accuracy)
        scheduler.step(accuracy)
        selected = (not best.exists() or accuracy > best_accuracy + config["accuracy_tie_tolerance"]
                    or (accuracy >= max_accuracy - config["accuracy_tie_tolerance"] and val["critical_error_count"] < best_critical))
        if selected:
            best_accuracy, best_critical, stale = accuracy, val["critical_error_count"], 0
            state = {k: v.detach().cpu() for k, v in model.state_dict().items()}
            torch.save({"model_state_dict": state, "class_names": config["class_order"], "config": config,
                        "epoch": epoch, "validation_metrics": val, "split_csv_sha256": digest(args.split_csv),
                        "config_sha256": digest(args.config), "initialization_sha256": digest(weights)}, best)
        else:
            stale += 1
        history.append({"epoch": epoch, "loss": loss, "validation": val, "selected": selected,
                        "seconds": time.monotonic() - started})
        write(target / "history.json", history)
        print("BASELINE", history[-1], flush=True)
        if stale >= config["patience"]:
            break
    model.load_state_dict(torch.load(best, map_location=device, weights_only=False)["model_state_dict"])
    test = evaluate(model, loaders["test"], config, device)
    write(target / "evaluation.json", {"test": test, "best_sha256": digest(best),
          "scope": "Optional fresh baseline on previously viewed split, not independent confirmation",
          "not_used_as_source_for_other_jobs": True})


if __name__ == "__main__":
    main()
