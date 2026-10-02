"""Export trained Flood MobileNetV3 model to ExecuTorch format (.pte) for mobile.

From products/fe/tools: python export_executorch.py
Defaults: checkpoint/config in model/Edge Ai; PTE/manifest in model/Edge Ai/Export.
Exports FP32 with the XNNPACK CPU delegate; no training or INT8 quantization.
Fails before writing output if no XNNPACK partition was produced.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import sys
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torchvision import models

from convert_model import inference_contract, update_manifest as update_export_manifest


ROOT = Path(__file__).resolve().parents[1]
EDGE_DIR = ROOT / "model" / "Edge Ai"
DEFAULT_CHECKPOINT = EDGE_DIR / "flood_mobilenetv3_large_best.pth"
DEFAULT_CONFIG = EDGE_DIR / "config_mobilenetv3_large.json"
DEFAULT_OUTPUT_DIR = EDGE_DIR / "Export"
DEFAULT_MANIFEST = DEFAULT_OUTPUT_DIR / "model_manifest.json"
EXPECTED_EXECUTORCH_VERSION = "1.4.1"


class ProbabilityModel(nn.Module):
    """Wrap model to output probabilities via softmax."""

    def __init__(self, model: nn.Module) -> None:
        super().__init__()
        self.model = model

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        return torch.softmax(self.model(image), dim=1)


def build_model(
    num_classes: int, dropout: float, *, nested_classifier: bool = True
) -> nn.Module:
    model = models.mobilenet_v3_large(weights=None)
    in_features = model.classifier[-1].in_features
    if nested_classifier:
        # Older checkpoints store the final Linear at classifier.3.1.
        model.classifier[-1] = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(in_features, num_classes),
        )
    else:
        # Current notebooks replace the existing Dropout and Linear directly.
        model.classifier[-2] = nn.Dropout(p=dropout)
        model.classifier[-1] = nn.Linear(in_features, num_classes)
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


def update_manifest(
    manifest_path: Path,
    checkpoint_path: Path,
    config: dict[str, Any],
    pte_path: Path,
    executorch_version: str,
) -> dict[str, Any]:
    return update_export_manifest(
        manifest_path, checkpoint_path, config, pte_path,
        artifact_type="pte", executorch_version=executorch_version,
    )


def export_executorch(
    checkpoint_path: Path,
    config_path: Path,
    output_dir: Path,
    manifest_path: Path,
) -> Path:
    from executorch.exir import to_edge_transform_and_lower
    from executorch.backends.xnnpack.partition.xnnpack_partitioner import XnnpackFloatingPointPartitioner
    from executorch.backends.xnnpack.utils.configs import get_transform_passes

    executorch_version = importlib.metadata.version("executorch")
    if executorch_version != EXPECTED_EXECUTORCH_VERSION:
        raise RuntimeError(
            "ExecuTorch exporter/runtime version mismatch: "
            f"expected {EXPECTED_EXECUTORCH_VERSION}, installed {executorch_version}"
        )

    # Windows wheel has flatc.exe; allow invoking venv Python without activation.
    flatc = Path(sys.executable).with_name("flatc.exe")
    if os.name == "nt" and flatc.is_file():
        os.environ.setdefault("FLATC_EXECUTABLE", str(flatc))

    config = json.loads(config_path.read_text(encoding="utf-8"))
    contract = inference_contract(config)  # Từ chối config lỗi trước khi ghi model.
    class_order = contract["class_order"]
    image_size = contract["input_size"]
    dropout = float(config.get("dropout", 0.35))

    state_dict, checkpoint = load_checkpoint(checkpoint_path)
    checkpoint_classes = checkpoint.get("class_names")
    if checkpoint_classes is not None and list(checkpoint_classes) != class_order:
        raise ValueError(
            "Class order mismatch: "
            f"config={class_order!r}, checkpoint={list(checkpoint_classes)!r}"
        )
    model = build_model(
        num_classes=len(class_order),
        dropout=dropout,
        nested_classifier="classifier.3.1.weight" in state_dict,
    )
    model.load_state_dict(state_dict, strict=True)
    model.eval()

    export_model = ProbabilityModel(model).eval()
    sample_input = (torch.randn(1, 3, image_size, image_size),)

    print("Tracing and exporting with torch.export...")
    exported_prog = torch.export.export(export_model, sample_input)

    print("Lowering to XNNPACK (FP32, no quantization)...")
    edge_prog = to_edge_transform_and_lower(
        exported_prog,
        partitioner=[XnnpackFloatingPointPartitioner()],
        transform_passes=get_transform_passes(),
    )

    print("Compiling to ExecuTorch runtime program...")
    exec_prog = edge_prog.to_executorch()
    delegate_count = sum(
        delegate.id == "XnnpackBackend"
        for plan in exec_prog.executorch_program.execution_plan
        for delegate in plan.delegates
    )
    if delegate_count == 0:
        raise RuntimeError("No XNNPACK partitions produced; refusing to export an unoptimized portable PTE.")
    print(f"[OK] XNNPACK FP32 partitions: {delegate_count} (unsupported ops may use portable fallback)")

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
        "backend": "xnnpack",
        "precision": "fp32",
        "xnnpack_delegate_count": delegate_count,
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
