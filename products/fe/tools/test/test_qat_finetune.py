"""Run from tools/: python -m unittest discover -s test -p test_qat_finetune.py."""
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import numpy as np
import onnx
import torch
from torch import nn
from torch.ao.quantization import FakeQuantizeBase, FusedMovingAvgObsFakeQuantize, enable_observer
from torch.utils.data import DataLoader, TensorDataset

import qat_finetune
from qat_finetune import evaluate, export_qdq, prepare_qat_model
from quantize_model import session, validate_probabilities


class TinyResidual(nn.Module):
    def __init__(self):
        super().__init__()
        self.stem = nn.Sequential(nn.Conv2d(3, 4, 3, padding=1), nn.BatchNorm2d(4), nn.ReLU())
        self.block = nn.Sequential(nn.Conv2d(4, 4, 3, padding=1), nn.BatchNorm2d(4), nn.ReLU())
        self.head = nn.Sequential(nn.Hardswish(), nn.Hardsigmoid(), nn.AdaptiveAvgPool2d(1),
                                  nn.Flatten(), nn.Linear(4, 4))

    def forward(self, image):
        features = self.stem(image)
        return self.head(features + self.block(features))


class QatExportTest(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1)
        torch.manual_seed(42)
        self.config = {"class_order": ["low", "medium", "high", "non_flood"]}
        self.model = prepare_qat_model(TinyResidual(), 16, "x86")
        with torch.no_grad():
            self.model(torch.randn(3, 3, 16, 16))  # Initialize train-only observer statistics.

    def fake_quantizers(self):
        return [module for module in self.model.modules() if isinstance(module, FakeQuantizeBase)]

    def test_validation_freezes_children_and_training_can_enable_them_again(self):
        self.assertTrue(self.fake_quantizers())
        self.assertFalse(any(isinstance(module, FusedMovingAvgObsFakeQuantize)
                             for module in self.fake_quantizers()))
        before = {key: value.clone() for key, value in self.model.state_dict().items()
                  if not key.endswith("observer_enabled")}
        loader = DataLoader(TensorDataset(torch.randn(2, 3, 16, 16) * 100,
                                         torch.tensor([0, 2])), batch_size=2)
        with self.assertLogs(qat_finetune.LOGGER, level="INFO") as logs:
            evaluate(self.model, loader, torch.device("cpu"), self.config)
        self.assertTrue(any("Validation batch 1/1" in line for line in logs.output))
        self.assertTrue(any("Validation completed" in line for line in logs.output))
        for module in self.fake_quantizers():
            self.assertEqual(int(module.observer_enabled[0]), 0)
            self.assertEqual(int(module.fake_quant_enabled[0]), 1)
        for key, expected in before.items():
            torch.testing.assert_close(self.model.state_dict()[key], expected, rtol=0, atol=0)
        self.model.apply(enable_observer)
        self.assertTrue(all(int(module.observer_enabled[0]) == 1 for module in self.fake_quantizers()))

    def test_real_qdq_export_matches_frozen_qat_and_keeps_weights(self):
        weights = {name: value.detach().clone() for name, value in self.model.named_parameters()}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "qat.onnx"
            checks = export_qdq(self.model, path, 16)
            self.assertTrue(checks["reference_probabilities_close"])
            self.assertEqual(checks["reference_optimization"], "ORT_DISABLE_ALL")
            self.assertEqual(checks["runtime_optimization"], "ORT_ENABLE_ALL")
            self.assertTrue(all(not module.training for module in self.model.modules()))
            graph = onnx.load(str(path))
            onnx.checker.check_model(graph)
            self.assertTrue({"QuantizeLinear", "DequantizeLinear"}.issubset(
                {node.op_type for node in graph.graph.node}))
            initializers = {value.name: value for value in graph.graph.initializer}
            quantized_weights = [node for node in graph.graph.node if node.op_type == "DequantizeLinear"
                                 and "weight_fake_quant" in node.name]
            self.assertTrue(quantized_weights)
            self.assertTrue(all(initializers[node.input[0]].data_type == onnx.TensorProto.INT8 for node in quantized_weights))
            self.assertTrue(all(int(module.observer_enabled[0]) == 0 for module in self.fake_quantizers()))
            runtime = session(path)
            for sample in (torch.zeros(1, 3, 16, 16), torch.randn(1, 3, 16, 16),
                           torch.randn(2, 3, 16, 16)):
                with torch.inference_mode():
                    expected = torch.softmax(self.model(sample), dim=1).numpy()
                actual = runtime.run(None, {runtime.get_inputs()[0].name: sample.numpy()})[0]
                for row in actual:
                    validate_probabilities(row[None, :], 4)
                np.testing.assert_allclose(actual, expected, rtol=1e-4, atol=1e-5)
            for name, parameter in self.model.named_parameters():
                torch.testing.assert_close(parameter, weights[name], rtol=0, atol=0)

    def test_pooling_does_not_share_boundary_observer(self):
        pool = next(node for node in self.model.graph.nodes
                    if node.op == "call_module" and
                    isinstance(self.model.get_submodule(str(node.target)), nn.AdaptiveAvgPool2d))
        before = self.model.get_submodule(str(pool.args[0].target))
        after_node = next(iter(pool.users))
        # The native FX mapping may defer the new observer past Flatten.
        if isinstance(self.model.get_submodule(str(after_node.target)), nn.Flatten):
            after_node = next(iter(after_node.users))
        after = self.model.get_submodule(str(after_node.target))
        self.assertIsInstance(before, FakeQuantizeBase)
        self.assertIsInstance(after, FakeQuantizeBase)
        self.assertIsNot(before, after)
        self.assertIsNone(self.model.get_submodule(str(pool.target)).qconfig)

    def test_invalid_reference_output_cannot_overwrite_existing_artifact(self):
        import onnxruntime as ort
        create_session = ort.InferenceSession

        def corrupt_reference(path, options, **kwargs):
            runtime = create_session(path, options, **kwargs)
            if options.graph_optimization_level == ort.GraphOptimizationLevel.ORT_DISABLE_ALL:
                runtime.run = lambda *args, **kwargs: [np.array([[np.nan, 0.03, 0.03, 0.04]], dtype=np.float32)]
            return runtime

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "qat.onnx"
            path.write_bytes(b"previous verified artifact")
            with patch.object(ort, "InferenceSession", side_effect=corrupt_reference):
                with self.assertRaisesRegex(ValueError, "probabilities"):
                    export_qdq(self.model, path, 16)
            self.assertEqual(path.read_bytes(), b"previous verified artifact")
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_rejects_fp32_graph_without_overwriting_existing_qat(self):
        model = nn.Sequential(nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(3, 4))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "qat.onnx"
            path.write_bytes(b"existing QAT artifact")
            with self.assertRaisesRegex(RuntimeError, "Q/DQ"):
                export_qdq(model, path, 16)
            self.assertEqual(path.read_bytes(), b"existing QAT artifact")
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_zero_weight_bias_does_not_overflow_int32_in_runtime(self):
        conv = nn.Conv2d(3, 4, 1)
        with torch.no_grad():
            conv.weight.zero_()
            conv.bias.copy_(torch.tensor([0.5, -0.4, 0.1, 0.03]))
        model = prepare_qat_model(nn.Sequential(conv, nn.AdaptiveAvgPool2d(1), nn.Flatten()), 16, "x86").eval()
        sample = torch.zeros(1, 3, 16, 16)
        with torch.no_grad():
            model(sample)  # Zero input/weights cause both observer scales to reach epsilon.
        original = {key: value.clone() for key, value in model.state_dict().items()
                    if not key.endswith("observer_enabled")}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "zero_weights.onnx"
            export_qdq(model, path, 16)
            with torch.inference_mode():
                expected = torch.softmax(model(sample), dim=1).numpy()
            runtime = session(path)
            actual = runtime.run(None, {"image": sample.numpy()})[0]
            np.testing.assert_allclose(actual, expected, atol=1e-5, rtol=1e-4)
            graph = onnx.load(str(path))
            self.assertTrue(any("__bias_safe_scale" in value.name for value in graph.graph.initializer))
            for key, value in original.items():
                torch.testing.assert_close(model.state_dict()[key], value, rtol=0, atol=0)

    def test_bias_overflow_cannot_change_nonzero_weights_or_existing_artifact(self):
        conv = nn.Conv2d(3, 4, 1)
        with torch.no_grad():
            conv.weight.fill_(0.01)
            conv.bias.fill_(0.5)
        model = prepare_qat_model(nn.Sequential(conv, nn.AdaptiveAvgPool2d(1), nn.Flatten()), 16, "x86").eval()
        with torch.no_grad():
            model(torch.zeros(1, 3, 16, 16))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "qat.onnx"
            path.write_bytes(b"existing model")
            with self.assertRaisesRegex(RuntimeError, "nonzero weight channels"):
                export_qdq(model, path, 16)
            self.assertEqual(path.read_bytes(), b"existing model")
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_cli_logs_stage_and_failure_without_training(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log_path = root / "logs" / "qat.log"
            result = subprocess.run(
                [sys.executable, str(Path(qat_finetune.__file__)), "--config", str(root / "missing.json"),
                 "--log-file", str(log_path), "--log-every", "1"],
                capture_output=True, text=True, timeout=60,
            )
            self.assertNotEqual(result.returncode, 0)
            log = log_path.read_text(encoding="utf-8")
            for message in ("Starting QAT", "Loading config", "[ERROR]", "QAT failed", "FileNotFoundError"):
                self.assertIn(message, log)
                self.assertIn(message, result.stderr)
            self.assertNotIn("starting fine-tuning", log)


if __name__ == "__main__":
    unittest.main()
