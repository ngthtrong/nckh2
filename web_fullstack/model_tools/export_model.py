from __future__ import annotations

import argparse
import hashlib
import json
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import onnx
import onnxruntime as ort
import torch
from PIL import Image, ImageOps
from torch import nn
from torchvision import models


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHECKPOINT = REPOSITORY_ROOT / "fe" / "app" / "model.pth"
DEFAULT_CONFIG = Path(__file__).resolve().with_name("model_config.json")
DEFAULT_MODEL = (
    REPOSITORY_ROOT
    / "fe"
    / "app"
    / "web"
    / "models"
    / "model.onnx"
)
DEFAULT_MANIFEST = DEFAULT_MODEL.with_name("model_manifest.json")


class ProbabilityModel(nn.Module):
    def __init__(self, model: nn.Module) -> None:
        super().__init__()
        self.model = model

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        return torch.softmax(self.model(image), dim=1)


def remove_module_prefix(
    state_dict: dict[str, torch.Tensor],
) -> dict[str, torch.Tensor]:
    return {key.removeprefix("module."): value for key, value in state_dict.items()}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(
    checkpoint_path: Path,
    onnx_path: Path,
    config: dict[str, Any],
) -> dict[str, Any]:
    onnx_sha = sha256_file(onnx_path)
    return {
        "version": f"mobilenetv3-{config['model_version']}-{onnx_sha[:12]}",
        "checkpoint_sha256": sha256_file(checkpoint_path),
        "onnx_sha256": onnx_sha,
        "input_size": int(config["input_size"]),
        "class_order": list(config["class_order"]),
        "mean": list(config["mean"]),
        "std": list(config["std"]),
        "letterbox_fill": list(config["letterbox_fill"]),
        "input_name": "image",
        "output_name": "probabilities",
    }


def load_checkpoint(path: Path) -> tuple[dict[str, torch.Tensor], dict[str, Any]]:
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    if isinstance(checkpoint, dict):
        for key in ("model_state_dict", "state_dict", "model"):
            candidate = checkpoint.get(key)
            if isinstance(candidate, dict):
                return remove_module_prefix(candidate), checkpoint
        if checkpoint and all(isinstance(value, torch.Tensor) for value in checkpoint.values()):
            return remove_module_prefix(checkpoint), checkpoint
    raise ValueError(f"Unsupported checkpoint format: {path}")


def build_model(num_classes: int, dropout: float) -> nn.Module:
    model = models.mobilenet_v3_large(weights=None)
    classifier = list(model.classifier.children())[:-1]
    in_features = model.classifier[-1].in_features
    model.classifier = nn.Sequential(
        *classifier,
        nn.Sequential(nn.Dropout(p=dropout), nn.Linear(in_features, num_classes)),
    )
    return model


def preprocess_image(image: Image.Image, config: dict[str, Any]) -> np.ndarray:
    size = int(config["input_size"])
    padded = ImageOps.pad(
        image.convert("RGB"),
        (size, size),
        method=Image.Resampling.BICUBIC,
        color=tuple(config["letterbox_fill"]),
    )
    pixels = np.asarray(padded, dtype=np.float32) / 255.0
    mean = np.asarray(config["mean"], dtype=np.float32)
    std = np.asarray(config["std"], dtype=np.float32)
    normalized = (pixels - mean) / std
    return np.transpose(normalized, (2, 0, 1))[None, ...].astype(np.float32)


def parity_input(config: dict[str, Any]) -> np.ndarray:
    width, height = 311, 173
    x = np.linspace(0, 255, width, dtype=np.uint8)
    y = np.linspace(255, 0, height, dtype=np.uint8)[:, None]
    rgb = np.stack(
        [
            np.broadcast_to(x, (height, width)),
            np.broadcast_to(y, (height, width)),
            np.full((height, width), 127, dtype=np.uint8),
        ],
        axis=-1,
    )
    return preprocess_image(Image.fromarray(rgb, mode="RGB"), config)


def verify_parity(
    model: nn.Module,
    onnx_path: Path,
    config: dict[str, Any],
) -> float:
    model_input = parity_input(config)
    with torch.inference_mode():
        torch_output = model(torch.from_numpy(model_input)).cpu().numpy()
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    onnx_output = session.run(["probabilities"], {"image": model_input})[0]
    np.testing.assert_allclose(torch_output, onnx_output, rtol=1e-4, atol=1e-5)
    if int(torch_output.argmax()) != int(onnx_output.argmax()):
        raise AssertionError("PyTorch and ONNX predicted different labels")
    return float(np.max(np.abs(torch_output - onnx_output)))


def export(
    checkpoint_path: Path,
    config_path: Path,
    output_path: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    state_dict, checkpoint = load_checkpoint(checkpoint_path)
    checkpoint_classes = checkpoint.get("class_order") or checkpoint.get("class_names")
    if checkpoint_classes is not None and list(checkpoint_classes) != list(config["class_order"]):
        raise ValueError(
            f"Class order mismatch: checkpoint={checkpoint_classes!r}, "
            f"config={config['class_order']!r}"
        )

    base_model = build_model(int(config["num_classes"]), float(config["dropout"]))
    base_model.load_state_dict(state_dict, strict=True)
    probability_model = ProbabilityModel(base_model.eval()).eval()

    size = int(config["input_size"])
    sample = torch.zeros(1, 3, size, size, dtype=torch.float32)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="You are using the legacy TorchScript-based ONNX export.*",
            category=DeprecationWarning,
        )
        torch.onnx.export(
            probability_model,
            sample,
            output_path,
            input_names=["image"],
            output_names=["probabilities"],
            dynamic_axes={"image": {0: "batch"}, "probabilities": {0: "batch"}},
            opset_version=int(config["onnx_opset"]),
            dynamo=False,
        )
    onnx.checker.check_model(onnx.load(output_path))
    max_delta = verify_parity(probability_model, output_path, config)

    manifest = build_manifest(checkpoint_path, output_path, config)
    manifest["parity_max_abs_delta"] = max_delta
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export the flood checkpoint for browser inference.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = export(args.checkpoint, args.config, args.output, args.manifest)
    print(f"Exported ONNX: {args.output}")
    print(f"Manifest: {args.manifest}")
    print(f"Version: {manifest['version']}")
    print(f"Parity max absolute delta: {manifest['parity_max_abs_delta']:.8f}")


if __name__ == "__main__":
    main()
