"""Export the trained Flood MobileNetV3 checkpoint to ONNX.

Run from the repository root:
    python tools/convert_model.py

Optional:
    python tools/convert_model.py --checkpoint path/to/model_best.pth \
        --output "model/Edge Ai/flood_mobilenetv3_large.onnx"
"""

from __future__ import annotations

import argparse
import hashlib
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
    / "mobilenetv3_large_relabel_v2"
    / "flood_mobilenetv3_large_relabel_v2_best.pth"
)
DEFAULT_CONFIG = (
    ROOT / "model" / "models" / "mobilenetv3_large_relabel_v2" / "config_mobilenetv3_large_v2.json"
)
DEFAULT_OUTPUT_DIR = ROOT / "model" / "Edge Ai"
DEFAULT_OUTPUT = DEFAULT_OUTPUT_DIR / "flood_mobilenetv3_large.onnx"
DEFAULT_MANIFEST = DEFAULT_OUTPUT_DIR / "model_manifest.json"


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def update_manifest(
    manifest_path: Path,
    checkpoint_path: Path,
    config: dict[str, Any],
    onnx_path: Path,
) -> dict[str, Any]:
    """Record only artifacts exported from the same source checkpoint."""
    checkpoint_sha = sha256_file(checkpoint_path)
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        current = json.loads(manifest_path.read_text(encoding="utf-8"))
        if current.get("checkpoint_sha256") == checkpoint_sha:
            manifest = current

    onnx_sha = sha256_file(onnx_path)
    manifest.update({
        "checkpoint_sha256": checkpoint_sha,
        "onnx_sha256": onnx_sha,
        "input_size": int(config.get("image_size", 224)),
        "preprocess": "letterbox_rgb_124_116_104",
        "letterbox_fill": list(config.get("letterbox_fill", [124, 116, 104])),
        "class_order": config["class_order"],
    })
    hashes = [manifest.get("onnx_sha256"), manifest.get("pte_sha256")]
    suffix = "-".join(value[:12] for value in hashes if value)
    model_version = config.get("model_version", "v2")
    manifest["version"] = f"mobilenetv3-{model_version}-{suffix}"
    manifest["artifacts_complete"] = all(hashes)

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
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

    manifest = update_manifest(args.manifest, args.checkpoint, config, args.output)

    print(f"Exported: {args.output}")
    print(f"Classes ({len(class_order)}): {class_order}")
    print(f"Input: {tuple(sample.shape)}")
    print("Output: probabilities (softmax)")
    print(f"Manifest: {args.manifest} ({manifest['version']})")


if __name__ == "__main__":
    main()
