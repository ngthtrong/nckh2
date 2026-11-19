"""Run from tools/: python -m unittest discover -s test -p test_structured_exports.py."""
import importlib.util
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import torch
from torch import nn

from compare_structured_pruning import load_structured_model
from convert_model import sha256_file
from export_structured_model import export_onnx, export_pte, update_pruned_manifest


def tiny_model():
    torch.manual_seed(42)
    torch.set_num_threads(1)
    return nn.Sequential(nn.Conv2d(3, 4, 3, padding=1), nn.ReLU(),
                         nn.AdaptiveAvgPool2d(1), nn.Flatten()).eval()


class StructuredExportsTest(unittest.TestCase):
    def test_missing_manifest_fails_before_split_audit(self):
        import benchmark_structured_exports as benchmark

        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing/model_manifest.json"
            with patch.object(sys, "argv", ["benchmark_structured_exports.py", "--manifest", str(missing)]), \
                    patch.object(benchmark, "prepare_test") as audit, \
                    contextlib.redirect_stderr(io.StringIO()) as stderr, \
                    self.assertRaises(SystemExit) as raised:
                benchmark.main()
            self.assertEqual(raised.exception.code, 2)
            audit.assert_not_called()
            self.assertIn("export_structured_model.py", stderr.getvalue())
            self.assertIn("--format all", stderr.getvalue())
            self.assertFalse(missing.parent.exists())

    def test_full_module_export_and_source_validation(self):
        model = tiny_model()
        config = dict(image_size=32, preprocess="letterbox", letterbox_fill=[124, 116, 104],
                      class_order=["low", "medium", "high", "non_flood"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, checkpoint = root / "baseline.pth", root / "structured.pt"
            source.write_bytes(b"source fixture for checksum only")
            source_sha = sha256_file(source)
            parameters = sum(parameter.numel() for parameter in model.parameters())
            torch.save(dict(model=model, class_names=config["class_order"], config=config,
                            source_checkpoint_sha256=source_sha, epoch=2,
                            pruning=dict(method="global_group_magnitude_channel",
                                         parameter_count_after=parameters)), checkpoint)
            loaded, details = load_structured_model(checkpoint, config, source_sha)
            self.assertEqual(sum(p.numel() for p in loaded.parameters()), parameters)
            with self.assertRaisesRegex(ValueError, "checkpoint gốc"):
                load_structured_model(checkpoint, config, "wrong-source")
            with self.assertRaisesRegex(ValueError, "image_size"):
                load_structured_model(checkpoint, {**config, "image_size": 16}, source_sha)
            before = {key: value.clone() for key, value in loaded.state_dict().items()}
            output = root / "structured.onnx"
            error = export_onnx(loaded, torch.randn(1, 3, 32, 32), output, 4)
            self.assertLess(error, 1e-4)
            manifest = update_pruned_manifest(root / "model_manifest.json", checkpoint, config,
                                              output, "onnx", source_sha, details)
            self.assertEqual(manifest["model_type"], "structured_pruned")
            self.assertEqual(manifest["source_checkpoint_sha256"], source_sha)
            self.assertEqual(manifest["checkpoint_sha256"], sha256_file(checkpoint))
            self.assertFalse(manifest["artifacts_complete"])
            for key, value in loaded.state_dict().items():
                torch.testing.assert_close(value, before[key], atol=0, rtol=0)

    @unittest.skipUnless(importlib.util.find_spec("executorch"), "ExecuTorch chưa được cài")
    def test_real_xnnpack_pte_export(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "structured.pte"
            version, delegates, error = export_pte(tiny_model(), torch.randn(1, 3, 32, 32), output, 4)
            self.assertTrue(version)
            self.assertGreater(delegates, 0)
            self.assertLess(error, 1e-4)
            self.assertGreater(output.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
