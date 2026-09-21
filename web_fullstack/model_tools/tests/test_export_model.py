import hashlib
from pathlib import Path

import torch

from export_model import build_manifest, remove_module_prefix


def test_remove_module_prefix_only_changes_prefixed_keys():
    state = {
        "module.features.0.0.weight": torch.zeros(1),
        "classifier.0.weight": torch.ones(1),
    }

    normalized = remove_module_prefix(state)

    assert list(normalized) == ["features.0.0.weight", "classifier.0.weight"]
    assert normalized["features.0.0.weight"] is state["module.features.0.0.weight"]


def test_manifest_records_runtime_contract_and_real_hashes(tmp_path: Path):
    checkpoint = tmp_path / "model.pth"
    onnx_model = tmp_path / "model.onnx"
    checkpoint.write_bytes(b"checkpoint")
    onnx_model.write_bytes(b"onnx")
    config = {
        "model_version": "web-v1",
        "input_size": 224,
        "class_order": ["low", "medium", "high", "non_flood"],
        "mean": [0.485, 0.456, 0.406],
        "std": [0.229, 0.224, 0.225],
        "letterbox_fill": [124, 116, 104],
    }

    manifest = build_manifest(checkpoint, onnx_model, config)

    assert manifest == {
        "version": f"mobilenetv3-web-v1-{hashlib.sha256(b'onnx').hexdigest()[:12]}",
        "checkpoint_sha256": hashlib.sha256(b"checkpoint").hexdigest(),
        "onnx_sha256": hashlib.sha256(b"onnx").hexdigest(),
        "input_size": 224,
        "class_order": ["low", "medium", "high", "non_flood"],
        "mean": [0.485, 0.456, 0.406],
        "std": [0.229, 0.224, 0.225],
        "letterbox_fill": [124, 116, 104],
        "input_name": "image",
        "output_name": "probabilities",
    }
