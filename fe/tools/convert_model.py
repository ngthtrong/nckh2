"""Export the trained Flood MobileNetV3 checkpoint to ONNX.

Run from the repository root:
    python tools/convert_model.py

Optional:
    python tools/convert_model.py --checkpoint path/to/model_best.pth \
        --output app/assets/models/model.onnx
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torchvision import models


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHECKPOINT = (
    ROOT
    / "model"
    / "models"
    / "mobilenetv3_large_relabel"
    / "flood_mobilenetv3_large_relabel_best.pth"
)
DEFAULT_CONFIG = (
    ROOT / "model" / "models" / "mobilenetv3_large_relabel" / "config_mobilenetv3_large.json"
)
DEFAULT_OUTPUT = ROOT / "app" / "assets" / "models" / "model.onnx"


class ProbabilityModel(nn.Module):
    """Keep the ONNX output compatible with the Flutter inference service."""

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


def load_checkpoint(path: Path) -> tuple[dict[str, torch.Tensor], dict[str, Any]]:
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    if isinstance(checkpoint, dict):
        for key in ("model_state_dict", "state_dict", "model"):
            state_dict = checkpoint.get(key)
            if isinstance(state_dict, dict):
                return state_dict, checkpoint
        if all(isinstance(value, torch.Tensor) for value in checkpoint.values()):
            return checkpoint, checkpoint
    raise ValueError(f"Unsupported checkpoint format: {path}")


def remove_module_prefix(state_dict: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    return {
        key.removeprefix("module."): value
        for key, value in state_dict.items()
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    class_order = config["class_order"]
    state_dict, checkpoint = load_checkpoint(args.checkpoint)
    state_dict = remove_module_prefix(state_dict)

    checkpoint_classes = checkpoint.get("class_names")
    if checkpoint_classes is not None and list(checkpoint_classes) != class_order:
        raise ValueError(
            "Class order mismatch: "
            f"config={class_order!r}, checkpoint={list(checkpoint_classes)!r}"
        )

    model = build_model(
        num_classes=len(class_order),
        dropout=float(config.get("dropout", 0.35)),
    )
    missing, unexpected = model.load_state_dict(state_dict, strict=False)
    if missing or unexpected:
        raise RuntimeError(
            f"Checkpoint does not match MobileNetV3 architecture. "
            f"Missing: {missing}; unexpected: {unexpected}"
        )

    export_model = ProbabilityModel(model.eval())
    sample = torch.zeros(1, 3, int(config.get("image_size", 224)), int(config.get("image_size", 224)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(
        export_model,
        sample,
        args.output,
        input_names=["image"],
        output_names=["probabilities"],
        dynamic_axes={"image": {0: "batch"}, "probabilities": {0: "batch"}},
        opset_version=17,
        dynamo=False,
    )

    print(f"Exported: {args.output}")
    print(f"Classes ({len(class_order)}): {class_order}")
    print(f"Input: {tuple(sample.shape)}")
    print("Output: probabilities (softmax)")


if __name__ == "__main__":
    main()
