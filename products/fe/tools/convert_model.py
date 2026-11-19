"""Export the trained Flood MobileNetV3 checkpoint to ONNX.

Run from products/fe/tools:
    python convert_model.py

Defaults: checkpoint/config in model/Edge Ai; ONNX/manifest in model/Edge Ai/Export.

Optional:
    python convert_model.py --checkpoint path/to/model_best.pth \
        --output "../model/Edge Ai/Export/flood_mobilenetv3_large.onnx"
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
EDGE_DIR = ROOT / "model" / "Edge Ai"
DEFAULT_CHECKPOINT = EDGE_DIR / "flood_mobilenetv3_large_best.pth"
DEFAULT_CONFIG = EDGE_DIR / "config_mobilenetv3_large.json"
DEFAULT_OUTPUT_DIR = EDGE_DIR / "Export"
DEFAULT_OUTPUT = DEFAULT_OUTPUT_DIR / "flood_mobilenetv3_large.onnx"
DEFAULT_MANIFEST = DEFAULT_OUTPUT_DIR / "model_manifest.json"


class ProbabilityModel(nn.Module):
    """Keep the ONNX output compatible with the Flutter inference service."""

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


def inference_contract(config: dict[str, Any]) -> dict[str, Any]:
    """Metadata chung mà cả ONNX và PTE phải khớp trước khi ghép manifest."""
    size = config.get("image_size", 256)
    fill = list(config.get("letterbox_fill", [124, 116, 104]))
    classes = config["class_order"]
    if config.get("preprocess", "letterbox") != "letterbox":
        raise ValueError("Exporter chỉ hỗ trợ preprocessing letterbox.")
    if type(size) is not int or size <= 0:
        raise ValueError("image_size phải là số nguyên > 0.")
    if len(fill) != 3 or any(type(value) is not int or not 0 <= value <= 255 for value in fill):
        raise ValueError("letterbox_fill phải có 3 giá trị RGB nguyên trong [0, 255].")
    if (not isinstance(classes, list) or len(classes) < 2
            or not all(isinstance(value, str) and value.strip() for value in classes)
            or len(set(classes)) != len(classes)):
        raise ValueError("class_order cần ít nhất hai nhãn không rỗng, không trùng.")
    return {
        "input_size": size,
        "preprocess": "letterbox_rgb_" + "_".join(map(str, fill)),
        "letterbox_fill": fill,
        "class_order": classes,
    }


def update_manifest(
    manifest_path: Path,
    checkpoint_path: Path,
    config: dict[str, Any],
    artifact_path: Path,
    *,
    artifact_type: str = "onnx",
    executorch_version: str | None = None,
) -> dict[str, Any]:
    """Chỉ ghép ONNX/PTE cùng checkpoint VÀ cùng contract đầu vào/nhãn."""
    if artifact_type not in ("onnx", "pte"):
        raise ValueError("Manifest chỉ hỗ trợ artifact ONNX hoặc PTE.")
    if artifact_type == "pte" and not executorch_version:
        raise ValueError("PTE cần khai báo version ExecuTorch runtime.")
    contract = inference_contract(config)
    checkpoint_sha = sha256_file(checkpoint_path)
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        current = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (current.get("checkpoint_sha256") == checkpoint_sha
                and all(current.get(key) == value for key, value in contract.items())):
            manifest = current

    manifest.update({
        "checkpoint_sha256": checkpoint_sha,
        **contract,
        f"{artifact_type}_sha256": sha256_file(artifact_path),
    })
    if artifact_type == "pte":
        manifest["executorch_runtime"] = executorch_version
    elif not manifest.get("pte_sha256") or not manifest.get("executorch_runtime"):
        manifest.pop("pte_sha256", None)
        manifest.pop("executorch_runtime", None)
    hashes = [manifest.get("onnx_sha256"), manifest.get("pte_sha256")]
    suffix = "-".join(value[:12] for value in hashes if value)
    model_version = config.get("model_version", "v2")
    # Padding/nhãn có thể đổi mà bytes model không đổi: version vẫn phải đổi.
    contract_sha = hashlib.sha256(
        json.dumps(contract, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:12]
    manifest["version"] = f"mobilenetv3-{model_version}-{contract_sha}-{suffix}"
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
    contract = inference_contract(config)  # Từ chối config lỗi trước khi ghi model.
    class_order = contract["class_order"]
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
        nested_classifier="classifier.3.1.weight" in state_dict,
    )
    missing, unexpected = model.load_state_dict(state_dict, strict=False)
    if missing or unexpected:
        raise RuntimeError(
            f"Checkpoint does not match MobileNetV3 architecture. "
            f"Missing: {missing}; unexpected: {unexpected}"
        )

    export_model = ProbabilityModel(model.eval())
    image_size = contract["input_size"]
    sample = torch.zeros(1, 3, image_size, image_size)
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
