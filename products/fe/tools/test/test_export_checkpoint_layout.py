"""Run from tools/: python -m unittest discover -s test."""

import contextlib
import gc
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import torch
from torch import nn
from torchvision import models

import convert_model
import export_executorch


class CheckpointLayoutTest(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("executorch"), "ExecuTorch chưa được cài")
    def test_real_xnnpack_export_and_reject_zero_delegates_before_overwriting(self):
        import compare_models
        from importlib.metadata import version

        torch.set_num_threads(1)
        torch.manual_seed(42)
        reference = nn.Sequential(nn.Conv2d(3, 4, 3, padding=1), nn.ReLU(),
                                  nn.AdaptiveAvgPool2d(1), nn.Flatten()).eval()
        original_weights = {key: value.clone() for key, value in reference.state_dict().items()}
        config = dict(image_size=32, preprocess="letterbox", letterbox_fill=[124, 116, 104],
                      class_order=["low", "medium", "high", "non_flood"], dropout=0.25)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint, config_path, onnx = root / "tiny.pth", root / "config.json", root / "tiny.onnx"
            torch.save(dict(model_state_dict=original_weights, class_names=config["class_order"]), checkpoint)
            config_path.write_text(json.dumps(config), encoding="utf-8")
            onnx.write_bytes(b"ONNX fixture for manifest hash only")
            manifest_path = root / "output/model_manifest.json"
            before = convert_model.update_manifest(manifest_path, checkpoint, config, onnx)
            with patch.object(export_executorch, "build_model", return_value=reference), \
                    contextlib.redirect_stdout(io.StringIO()) as logs:
                pte = export_executorch.export_executorch(checkpoint, config_path, root / "output", manifest_path)
            self.assertIn("XNNPACK FP32 partitions:", logs.getvalue())
            metadata = json.loads((root / "output/model_metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["backend"], "xnnpack")
            self.assertEqual(metadata["precision"], "fp32")
            self.assertGreater(metadata["xnnpack_delegate_count"], 0)
            self.assertEqual(metadata["input_shape"], [1, 3, 32, 32])
            self.assertEqual(metadata["classes"], config["class_order"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["onnx_sha256"], before["onnx_sha256"])
            self.assertEqual(manifest["pte_sha256"], convert_model.sha256_file(pte))
            self.assertEqual(metadata["pte_sha256"], manifest["pte_sha256"])
            self.assertNotEqual(manifest["version"], before["version"])
            self.assertTrue(manifest["artifacts_complete"])
            for key, value in reference.state_dict().items():
                torch.testing.assert_close(value, original_weights[key], atol=0, rtol=0)

            predict = compare_models.pte_runner(pte, version("executorch"))
            for sample in (torch.zeros(1, 3, 32, 32), torch.randn(1, 3, 32, 32),
                           torch.linspace(-1, 1, 3 * 32 * 32).reshape(1, 3, 32, 32)):
                output = predict(sample.numpy())
                compare_models.validate_probabilities(output, 4)
                expected = export_executorch.ProbabilityModel(reference)(sample).detach().numpy()
                torch.testing.assert_close(torch.from_numpy(output), torch.from_numpy(expected), atol=1e-5, rtol=1e-4)
            del predict
            gc.collect()  # Release native file mapping before Windows cleanup.

            saved = {path: path.read_bytes() for path in (pte, manifest_path, root / "output/model_metadata.json")}
            empty_program = SimpleNamespace(executorch_program=SimpleNamespace(execution_plan=[]))
            no_delegate = SimpleNamespace(to_executorch=lambda: empty_program)
            with patch.object(export_executorch, "build_model", return_value=reference), \
                    patch("executorch.exir.to_edge_transform_and_lower", return_value=no_delegate), \
                    contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, "No XNNPACK partitions"):
                export_executorch.export_executorch(checkpoint, config_path, root / "output", manifest_path)
            for path, contents in saved.items():
                self.assertEqual(path.read_bytes(), contents)

    def test_manifest_pair_requires_matching_checkpoint_and_contract(self):
        config = dict(image_size=256, preprocess="letterbox", letterbox_fill=[124, 116, 104],
                      class_order=["low", "medium", "high", "non_flood"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint, onnx, pte = (root / name for name in ("model.pth", "model.onnx", "model.pte"))
            checkpoint.write_bytes(b"checkpoint one")
            onnx.write_bytes(b"ONNX fixture, not a real graph")
            pte.write_bytes(b"PTE fixture, not a real program")
            manifest_path = root / "model_manifest.json"

            def update(kind, cfg):
                if kind == "onnx":
                    result = convert_model.update_manifest(manifest_path, checkpoint, cfg, onnx)
                else:
                    result = export_executorch.update_manifest(manifest_path, checkpoint, cfg, pte, "1.4.1")
                self.assertEqual(result, json.loads(manifest_path.read_text(encoding="utf-8")))
                return result

            for first, second in (("onnx", "pte"), ("pte", "onnx")):
                with self.subTest(first=first):
                    manifest_path.unlink(missing_ok=True)
                    self.assertFalse(update(first, config)["artifacts_complete"])
                    complete = update(second, config)
                    self.assertTrue(complete["artifacts_complete"])
                    self.assertEqual(complete["executorch_runtime"], "1.4.1")
                    for field, value in (("image_size", 224), ("letterbox_fill", [0, 0, 0]),
                                         ("class_order", list(reversed(config["class_order"])))):
                        update(first, config)
                        original_version = update(second, config)["version"]
                        changed = {**config, field: value}
                        partial = update(first, changed)
                        self.assertFalse(partial["artifacts_complete"])
                        self.assertNotIn(f"{second}_sha256", partial)
                        self.assertEqual(partial["preprocess"],
                                         "letterbox_rgb_" + "_".join(map(str, changed["letterbox_fill"])))
                        self.assertNotIn(convert_model.sha256_file(onnx if second == "onnx" else pte)[:12],
                                         partial["version"])
                        if first == "onnx":
                            self.assertNotIn("executorch_runtime", partial)
                        # Export bản cũ sau bản mới cũng không được ghép hai contract.
                        self.assertFalse(update(second, config)["artifacts_complete"])
                        update(first, changed)
                        changed_pair = update(second, changed)
                        self.assertTrue(changed_pair["artifacts_complete"])
                        self.assertNotEqual(original_version, changed_pair["version"])

                    update(first, config)
                    update(second, config)
                    checkpoint.write_bytes(checkpoint.read_bytes() + b"changed")
                    self.assertFalse(update(first, config)["artifacts_complete"])
                    self.assertTrue(update(second, config)["artifacts_complete"])
                    # Manifest cũ thiếu metadata không đủ bằng chứng để giữ hash còn lại.
                    legacy = json.loads(manifest_path.read_text(encoding="utf-8"))
                    legacy.pop("letterbox_fill")
                    manifest_path.write_text(json.dumps(legacy), encoding="utf-8")
                    self.assertFalse(update(first, config)["artifacts_complete"])
                    before = manifest_path.read_bytes()
                    for invalid in ({**config, "preprocess": "center_crop"},
                                    {**config, "image_size": 0}, {**config, "letterbox_fill": [0, 0, 999]},
                                    {**config, "class_order": ["low", "low"]}):
                        with self.assertRaises(ValueError):
                            update(first, invalid)
                        self.assertEqual(before, manifest_path.read_bytes())
                    update("pte", config)
                    legacy = json.loads(manifest_path.read_text(encoding="utf-8"))
                    legacy.pop("executorch_runtime")
                    manifest_path.write_text(json.dumps(legacy), encoding="utf-8")
                    self.assertFalse(update("onnx", config)["artifacts_complete"])

    def test_exporters_preserve_both_checkpoint_layouts(self):
        source_dir = convert_model.ROOT / "model" / "Edge Ai"
        for exporter in (convert_model, export_executorch):
            self.assertEqual(exporter.DEFAULT_CHECKPOINT, source_dir / "flood_mobilenetv3_large_best.pth")
            self.assertEqual(exporter.DEFAULT_CONFIG, source_dir / "config_mobilenetv3_large.json")
            self.assertEqual(exporter.DEFAULT_OUTPUT_DIR, source_dir / "Export")
            self.assertEqual(exporter.DEFAULT_MANIFEST, source_dir / "Export" / "model_manifest.json")
        torch.set_num_threads(1)
        sample = torch.zeros(1, 3, 32, 32)
        for nested in (False, True):
            reference = models.mobilenet_v3_large(weights=None)
            in_features = reference.classifier[-1].in_features
            if nested:
                reference.classifier[-1] = nn.Sequential(
                    nn.Dropout(0.25), nn.Linear(in_features, 4)
                )
            else:
                reference.classifier[-2] = nn.Dropout(0.25)
                reference.classifier[-1] = nn.Linear(in_features, 4)
            reference.eval()
            state_dict = reference.state_dict()
            with torch.inference_mode():
                expected = reference(sample)
            for exporter in (convert_model, export_executorch):
                with self.subTest(exporter=exporter.__name__, nested=nested):
                    model = exporter.build_model(
                        4, 0.25,
                        nested_classifier="classifier.3.1.weight" in state_dict,
                    ).eval()
                    model.load_state_dict(state_dict, strict=True)
                    with torch.inference_mode():
                        torch.testing.assert_close(model(sample), expected)


if __name__ == "__main__":
    unittest.main()
