"""Chạy từ tools/: python -m unittest discover -s test."""
import contextlib
import csv
import gc
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from PIL import Image

import compare_models as compare
import compare_fp32_int8 as quant_compare


class ComparisonTest(unittest.TestCase):
    def test_independent_predictions_reports_and_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = [root / "a.jpg", root / "b.jpg"]
            for path in paths:
                Image.new("RGB", (20, 10), (100, 40, 90)).save(path)
            config = dict(class_order=["low", "high"], image_size=16,
                          letterbox_fill=[124, 116, 104], preprocess="letterbox")
            items = list(zip(paths, [0, 1]))
            pth_calls = 0

            def pth(x):
                nonlocal pth_calls
                pth_calls += 1
                x.fill(0)
                return np.array([[0.8, 0.2]], dtype=np.float32)

            def onnx(x):
                self.assertTrue(np.any(x != 0), "Runtime trước đã sửa input chung")
                return np.array([[0.7, 0.3]], dtype=np.float32)

            runners = dict(pth=pth, onnx=onnx, pte=lambda x: np.array([[0.1, 0.9]], dtype=np.float32))
            artifacts = {name: dict(bytes=10) for name in runners}
            with self.assertLogs(compare.LOGGER, level="DEBUG") as logs, contextlib.redirect_stdout(io.StringIO()):
                result = compare.write_comparison(runners, items, config, artifacts,
                                                  dict(evaluation_scope="test_subset_smoke"), root / "report")
            messages = "\n".join(logs.output)
            for expected in ("Warmup pte 3/3 done", "[1/2] Processing a.jpg", "[2/2] Inference pte starting",
                             "[2/2] Done", "ETA=0.0s", "Computing classification", "Writing JSON/CSV/Markdown",
                             "Writing confusion/calibration plots", "Comparison complete: 2 images"):
                self.assertIn(expected, messages)
            self.assertEqual(result["metadata"]["n_images"], 2)
            self.assertEqual(pth_calls, 5)  # 3 warmup + 2 test; chỉ 2 latency được ghi.
            pairs = result["pairwise_comparison"]
            self.assertEqual(pairs["pth_vs_onnx"]["top1_agreement"], 1)
            self.assertFalse(pairs["pth_vs_onnx"]["probabilities_close"])
            self.assertAlmostEqual(pairs["pth_vs_onnx"]["mean_abs_diff"], 0.1)
            self.assertAlmostEqual(pairs["pth_vs_onnx"]["rmse"], 0.1)
            self.assertEqual(pairs["onnx_vs_pte"]["top1_agreement"], 0)
            self.assertEqual(result["classification_metrics"]["pth"]["accuracy"], 0.5)
            self.assertEqual(result["metadata"]["output_type"], "probabilities")
            report = (root / "report/summary.md").read_text(encoding="utf-8")
            self.assertIn("| MAE | RMSE | Cosine mean |", report)
            self.assertIn("không phải raw logits hay kết quả Android", report)
            self.assertIn("| Mean ms | Median ms | P95 ms | Min ms | Max ms | Tổng inference s |", report)
            with (root / "report/all_predictions.csv").open(encoding="utf-8-sig", newline="") as stream:
                predictions = list(csv.DictReader(stream))
            self.assertEqual(len(predictions), 2)
            for name in runners:
                latency = np.array([float(row[f"latency_ms_{name}"]) for row in predictions])
                self.assertTrue((latency >= 0).all())
                values = result["classification_metrics"][name]
                for key, expected in (("mean", np.mean(latency)), ("median", np.median(latency)),
                                      ("p95", np.percentile(latency, 95)), ("min", np.min(latency)),
                                      ("max", np.max(latency)), ("total", np.sum(latency))):
                    self.assertAlmostEqual(values[f"latency_ms_{key}"], expected)
            self.assertTrue((root / "report/model_disagreement.csv").is_file())
            self.assertTrue((root / "report/confusion_pte.png").is_file())
            self.assertTrue((root / "report/calibration_onnx.png").is_file())
            self.assertEqual(json.loads((root / "report/summary.json").read_text(encoding="utf-8"))["metadata"]["evaluation_scope"], "test_subset_smoke")
            shared = np.array([[0.8, 0.2]], dtype=np.float32)
            copied = compare.validate_probabilities(shared, 2)
            shared.fill(0)
            np.testing.assert_array_equal(copied, np.array([0.8, 0.2], dtype=np.float32))
            with self.assertRaises(ValueError):
                compare.validate_probabilities(np.array([[1.2, -0.2]], dtype=np.float32), 2)
            with self.assertLogs(compare.LOGGER, level="ERROR") as logs, self.assertRaises(ValueError):
                compare.evaluate_models({"bad": lambda x: np.array([[np.nan, 0]], dtype=np.float32)}, items, config)
            self.assertIn("Warmup failed: model=bad, step=1/3", logs.output[-1])
            outputs = iter([np.array([[0.8, 0.2]], dtype=np.float32)] * 4
                           + [np.array([[np.nan, 0]], dtype=np.float32)])
            with self.assertLogs(compare.LOGGER, level="INFO") as logs, self.assertRaises(ValueError):
                compare.evaluate_models({"bad": lambda x: next(outputs)}, items, config)
            self.assertIn("Inference failed: model=bad, image=b.jpg (2/2)", logs.output[-1])
            self.assertFalse(any("[2/2] Done" in message for message in logs.output))
            fake = SimpleNamespace(get_inputs=lambda: [SimpleNamespace(name="image", type="tensor(float)", shape=["batch", 3, 16, 16])],
                                   get_outputs=lambda: [SimpleNamespace(type="tensor(float)")],
                                   run=lambda _, feed: [np.array([[0.5, 0.5]], dtype=np.float32)])
            with patch.object(compare, "session", return_value=fake):
                compare.onnx_runner(root / "fake.onnx", config)(np.zeros((1, 3, 16, 16), dtype=np.float32))
                fake.get_inputs = lambda: [SimpleNamespace(name="image", type="tensor(float)", shape=[1, 3, 224, 224])]
                with self.assertRaisesRegex(ValueError, "config"):
                    compare.onnx_runner(root / "fake.onnx", config)
            fp32, int8, split = root / "fp32.onnx", root / "int8.onnx", root / "split.csv"
            fp32.write_bytes(b"fp32")
            int8.write_bytes(b"int8")
            split.write_text("split", encoding="utf-8")
            source = dict(input_size=16, letterbox_fill=config["letterbox_fill"], class_order=config["class_order"],
                          preprocess="letterbox_rgb_124_116_104", checkpoint_sha256="checkpoint",
                          onnx_sha256=compare.sha256(fp32))
            quantized = {**source, "checkpoint_sha256": "wrong-checkpoint", "onnx_sha256": compare.sha256(int8),
                         "precision": "int8", "source_onnx_sha256": source["onnx_sha256"], "split_csv_sha256": compare.sha256(split)}
            with self.assertRaisesRegex(ValueError, "nguồn"):
                quant_compare.verify_int8_pair(fp32, int8, source, quantized, config, split)

    def test_pairwise_errors_are_measured_not_fixed_conclusions(self):
        a = np.array([[0.7, 0.2, 0.1], [0.4, 0.4, 0.2]], dtype=np.float32)
        b = np.array([[0.6, 0.3, 0.1], [0.2, 0.5, 0.3]], dtype=np.float32)
        measured = compare.pairwise_metrics(a, b, atol=1e-5, rtol=1e-4)
        self.assertAlmostEqual(measured["max_abs_diff"], 0.2)
        self.assertAlmostEqual(measured["mean_abs_diff"], 0.1)
        self.assertAlmostEqual(measured["rmse"], np.sqrt(0.08 / 6))
        self.assertAlmostEqual(measured["l1_mean"], 0.3)
        self.assertAlmostEqual(measured["l2_mean"], (np.sqrt(0.02) + np.sqrt(0.06)) / 2)
        self.assertLess(measured["cosine_similarity_mean"], 1)
        self.assertGreater(measured["js_divergence_mean"], 0)
        self.assertEqual(measured["top1_agreement"], 0.5)
        self.assertFalse(measured["probabilities_close"])
        identical = compare.pairwise_metrics(a, a.copy(), atol=1e-5, rtol=1e-4)
        self.assertEqual(identical["rmse"], 0)
        self.assertTrue(identical["probabilities_close"])

    def test_cli_writes_progress_and_traceback_to_log_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            completed = subprocess.run(
                [sys.executable, str(Path(compare.__file__).resolve()), "--config", str(root / "missing.json"),
                 "--report-dir", str(root / "reports"), "--limit", "3", "--verbose", "--no-plots"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
            self.assertEqual(completed.returncode, 1)
            log = (root / "reports/compare.log").read_text(encoding="utf-8")
            for expected in ("[INFO]", "Starting comparison", "Reading config", "[ERROR]", "Traceback", "FileNotFoundError"):
                self.assertIn(expected, log)
                self.assertIn(expected, completed.stderr)
            self.assertNotIn("Comparison complete", log)
            self.assertFalse((root / "reports/summary.json").exists())

    @unittest.skipUnless(importlib.util.find_spec("executorch"), "ExecuTorch chưa được cài")
    def test_real_pte_runtime_with_tiny_temporary_program(self):
        import torch
        from executorch.exir import to_edge
        from importlib.metadata import version

        class TinyModel(torch.nn.Module):
            def forward(self, x):
                return torch.softmax(x.mean(dim=(2, 3)), dim=1)

        torch.set_num_threads(1)
        model = TinyModel().eval()
        x = torch.arange(1 * 3 * 16 * 16, dtype=torch.float32).reshape(1, 3, 16, 16) / 255
        with tempfile.TemporaryDirectory() as directory:
            pte = Path(directory) / "tiny.pte"
            pte.write_bytes(to_edge(torch.export.export(model, (x,))).to_executorch().buffer)
            predict = compare.pte_runner(pte, version("executorch"))
            for _ in range(2):
                output = predict(x.numpy())
                compare.validate_probabilities(output, 3)
                np.testing.assert_allclose(output, model(x).numpy(), atol=1e-5, rtol=1e-4)
            with self.assertRaisesRegex(ValueError, "runtime"):
                compare.pte_runner(pte, "0.0.0")
            del predict  # Windows giữ file mapping tới khi native Program được giải phóng.
            gc.collect()


if __name__ == "__main__":
    unittest.main()
