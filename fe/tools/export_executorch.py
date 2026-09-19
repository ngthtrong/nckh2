"""Export trained Flood MobileNetV3 model to ExecuTorch format (.pte) for mobile."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
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
    / "mobilenetv3_large_relabel_v2"
    / "flood_mobilenetv3_large_relabel_v2_best.pth"
)
DEFAULT_CONFIG = (
    ROOT
    / "model"
    / "models"
    / "mobilenetv3_large_relabel_v2"
    / "config_mobilenetv3_large_v2.json"
)
DEFAULT_OUTPUT_DIR = ROOT / "model" / "Edge Ai"
DEFAULT_MANIFEST = DEFAULT_OUTPUT_DIR / "model_manifest.json"
EXPECTED_EXECUTORCH_VERSION = "1.4.1"


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


def load_checkpoint(path: Path) -> tuple[dict[str, torch.Tensor], dict[str, Any]]:
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    if isinstance(checkpoint, dict):
        for key in ("model_state_dict", "state_dict", "model"):
            state_dict = checkpoint.get(key)
            if isinstance(state_dict, dict):
                clean = {k.removeprefix("module."): v for k, v in state_dict.items()}
                return clean, checkpoint
        if all(isinstance(v, torch.Tensor) for v in checkpoint.values()):
            clean = {k.removeprefix("module."): v for k, v in checkpoint.items()}
            return clean, checkpoint
    raise ValueError(f"Unsupported checkpoint: {path}")


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
    pte_path: Path,
    executorch_version: str,
) -> dict[str, Any]:
    """Record only artifacts exported from the same source checkpoint."""
    checkpoint_sha = sha256_file(checkpoint_path)
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        current = json.loads(manifest_path.read_text(encoding="utf-8"))
        if current.get("checkpoint_sha256") == checkpoint_sha:
            manifest = current

    pte_sha = sha256_file(pte_path)
    manifest.update({
        "checkpoint_sha256": checkpoint_sha,
        "pte_sha256": pte_sha,
        "executorch_runtime": executorch_version,
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


def export_executorch(
    checkpoint_path: Path,
    config_path: Path,
    output_dir: Path,
    manifest_path: Path,
) -> Path:
    executorch_version = importlib.metadata.version("executorch")
    if executorch_version != EXPECTED_EXECUTORCH_VERSION:
        raise RuntimeError(
            "ExecuTorch exporter/runtime version mismatch: "
            f"expected {EXPECTED_EXECUTORCH_VERSION}, installed {executorch_version}"
        )

    config = json.loads(config_path.read_text(encoding="utf-8"))
    class_order = config["class_order"]
    image_size = int(config.get("image_size", 224))
    dropout = float(config.get("dropout", 0.35))

    state_dict, checkpoint = load_checkpoint(checkpoint_path)
    checkpoint_classes = checkpoint.get("class_names")
    if checkpoint_classes is not None and list(checkpoint_classes) != class_order:
        raise ValueError(
            "Class order mismatch: "
            f"config={class_order!r}, checkpoint={list(checkpoint_classes)!r}"
        )
    model = build_model(num_classes=len(class_order), dropout=dropout)
    model.load_state_dict(state_dict, strict=True)
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

    manifest = update_manifest(
        manifest_path,
        checkpoint_path,
        config,
        out_file,
        executorch_version,
    )

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
        "checkpoint_sha256": manifest["checkpoint_sha256"],
        "pte_sha256": manifest["pte_sha256"],
        "executorch_runtime": executorch_version,
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
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    export_executorch(args.checkpoint, args.config, args.output_dir, args.manifest)


if __name__ == "__main__":
    main()
