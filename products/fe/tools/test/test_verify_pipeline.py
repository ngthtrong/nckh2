"""Chạy từ tools/: python -m unittest discover -s test."""
import contextlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import onnx
from onnx import TensorProto, helper
from PIL import Image

import verify_pipeline as verify


class VerificationTest(unittest.TestCase):
    def test_real_graph_and_failure_statuses(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = dict(class_order=["r", "g", "b"], image_size=16, dropout=0.25,
                          letterbox_fill=[124, 116, 104], preprocess="letterbox")
            config_path, labels_path = root / "config.json", root / "labels.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            labels_path.write_text(json.dumps(config["class_order"]), encoding="utf-8")
            checkpoint, graph_path = root / "model.pth", root / "model.onnx"
            checkpoint.write_bytes(b"fixture checkpoint; loading mocked separately")
            split = root / "split.csv"
            with split.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=["relative_path", "label", "split"])
                writer.writeheader()
                for i, name in enumerate(("train", "test")):
                    path = root / f"{name}.jpg"
                    Image.new("RGB", (20, 10), (20 + i * 40, 50, 100)).save(path)
                    writer.writerow(dict(relative_path=path.name, label="r", split=name))
            manifest_path = root / "manifest.json"

            def save_graph(softmax=True, size=16):
                nodes = [helper.make_node("ReduceMean", ["image"], ["pooled"], axes=[2, 3], keepdims=0)]
                if softmax:
                    nodes.append(helper.make_node("Softmax", ["pooled"], ["probabilities"], axis=1))
                graph = helper.make_graph(nodes, "tiny",
                                          [helper.make_tensor_value_info("image", TensorProto.FLOAT, ["batch", 3, size, size])],
                                          [helper.make_tensor_value_info("probabilities" if softmax else "pooled", TensorProto.FLOAT, ["batch", 3])])
                onnx.save(helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)]), graph_path)
                manifest = dict(checkpoint_sha256=verify.sha256(checkpoint), onnx_sha256=verify.sha256(graph_path),
                                input_size=16, letterbox_fill=config["letterbox_fill"], class_order=config["class_order"],
                                preprocess="letterbox_rgb_124_116_104")
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            def predict(array):
                values = array.mean(axis=(2, 3))
                exponents = np.exp(values - values.max(axis=1, keepdims=True))
                return exponents / exponents.sum(axis=1, keepdims=True)

            args = SimpleNamespace(config=config_path, labels=labels_path, checkpoint=checkpoint,
                                   onnx=graph_path, manifest=manifest_path, split_csv=split,
                                   dataset_dir=root, full_test=False, limit=3,
                                   onnx_engine="reference", atol=1e-5, rtol=1e-4)
            save_graph()
            with patch.object(verify, "pth_runner", return_value=predict):
                result = verify.run_verification(args)
            self.assertEqual(result["status"], "incomplete")
            self.assertEqual(result["exit_code"], 2)
            self.assertEqual(result["passed_checks"], 4)
            self.assertEqual(result["checks"]["graph_parity"]["status"], "pass")
            self.assertEqual(result["checks"]["execution_provider"]["status"], "not_tested")
            self.assertEqual(result["mobile"]["status"], "not_tested")
            with contextlib.redirect_stdout(io.StringIO()):
                verify.write_report(result, root / "report")
            saved = json.loads((root / "report/verification.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "incomplete")
            with patch.object(verify, "pth_runner", return_value=predict):
                labels_path.write_text(json.dumps(["b", "g", "r"]), encoding="utf-8")
                result = verify.run_verification(args)
                self.assertEqual(result["status"], "fail")
                self.assertEqual(result["exit_code"], 1)
                self.assertEqual(result["checks"]["label_mapping"]["status"], "fail")
                labels_path.write_text(json.dumps(config["class_order"]), encoding="utf-8")
                save_graph(softmax=False)
                result = verify.run_verification(args)
                self.assertEqual(result["checks"]["graph_parity"]["status"], "fail")
                self.assertIn("Softmax", result["checks"]["graph_parity"]["error"])
                save_graph(size=224)
                result = verify.run_verification(args)
                self.assertEqual(result["checks"]["precision"]["status"], "fail")
                self.assertEqual(result["status"], "fail")
                save_graph()
            with patch.object(verify, "pth_runner", return_value=lambda x: np.array([[0.8, 0.1, 0.1]], dtype=np.float32)):
                result = verify.run_verification(args)
                self.assertFalse(result["checks"]["graph_parity"]["probabilities_close"])
                self.assertEqual(result["status"], "fail")
            args.onnx_engine = "ort"
            with patch.object(verify, "session", side_effect=ModuleNotFoundError("No module named 'onnxruntime'")):
                result = verify.run_verification(args)
                self.assertEqual(result["checks"]["execution_provider"]["status"], "fail")
                self.assertEqual(result["checks"]["graph_parity"]["status"], "not_tested")
                self.assertEqual(result["status"], "fail")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["checkpoint_sha256"] = "wrong-hash"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = verify.run_verification(args)
            self.assertEqual(result["preflight"]["status"], "fail")
            self.assertEqual(result["exit_code"], 1)


if __name__ == "__main__":
    unittest.main()
