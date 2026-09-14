"""Export trained Flood MobileNetV3 model to ExecuTorch format (.pte) for mobile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torchvision import models
from executorch.exir import to_edge


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHECKPOINT = (
    ROOT
    / "model"
    / "models"
    / "mobilenetv3_large_relabel"
    / "flood_mobilenetv3_large_relabel_best.pth"
)
DEFAULT_CONFIG = (
    ROOT
    / "model"
    / "models"
    / "mobilenetv3_large_relabel"
    / "config_mobilenetv3_large.json"
)
DEFAULT_OUTPUT_DIR = ROOT / "model" / "Edge Ai"


class ProbabilityModel(nn.Module):
    """Wrap model to output probabilities via softmax."""

    def __init__(self, model: nn.Module) -> None:
        super().__init__()
        self.model = model

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        return torch.softmax(self.model(image), dim=1)


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


def load_checkpoint(path: Path) -> dict[str, torch.Tensor]:
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    if isinstance(checkpoint, dict):
        for key in ("model_state_dict", "state_dict", "model"):
            state_dict = checkpoint.get(key)
            if isinstance(state_dict, dict):
                return {k.removeprefix("module."): v for k, v in state_dict.items()}
        if all(isinstance(v, torch.Tensor) for v in checkpoint.values()):
            return {k.removeprefix("module."): v for k, v in checkpoint.items()}
    raise ValueError(f"Unsupported checkpoint: {path}")


def export_executorch(
    checkpoint_path: Path,
    config_path: Path,
    output_dir: Path,
) -> Path:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    class_order = config["class_order"]
    image_size = int(config.get("image_size", 224))
    dropout = float(config.get("dropout", 0.35))

    state_dict = load_checkpoint(checkpoint_path)
    model = build_model(num_classes=len(class_order), dropout=dropout)
    missing, unexpected = model.load_state_dict(state_dict, strict=False)
    if missing or unexpected:
        raise RuntimeError(f"Missing: {missing}, Unexpected: {unexpected}")
    model.eval()

    export_model = ProbabilityModel(model)
    sample_input = (torch.randn(1, 3, image_size, image_size),)

    print("Tracing and exporting with torch.export...")
    exported_prog = torch.export.export(export_model, sample_input)

    print("Lowering to Edge IR...")
    edge_prog = to_edge(exported_prog)

    print("Compiling to ExecuTorch runtime program...")
    exec_prog = edge_prog.to_executorch()

    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "flood_mobilenetv3_large.pte"
    with open(out_file, "wb") as f:
        f.write(exec_prog.buffer)

    print(f"[OK] Exported ExecuTorch model to: {out_file}")
    print(f"     Size: {out_file.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"     Classes: {class_order}")
    print(f"     Input shape: {sample_input[0].shape}")

    # Also save metadata for mobile integration
    meta_file = output_dir / "model_metadata.json"
    meta = {
        "model_name": "flood_mobilenetv3_large",
        "format": "executorch_pte",
        "file": out_file.name,
        "input_shape": list(sample_input[0].shape),
        "classes": class_order,
        "image_size": image_size,
        "normalization": {
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225],
        },
    }
    meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"[OK] Saved metadata to: {meta_file}")
    return out_file


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    export_executorch(args.checkpoint, args.config, args.output_dir)


if __name__ == "__main__":
    main()
