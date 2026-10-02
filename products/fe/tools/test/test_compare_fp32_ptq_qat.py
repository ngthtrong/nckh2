"""Run from tools/: python -m unittest discover -s test."""
import tempfile
import unittest
from pathlib import Path

from compare_fp32_ptq_qat import verify_lineage
from compare_models import classification_metrics, sha256


class QatComparisonTest(unittest.TestCase):
    def test_comparison_metrics_include_severe_flood_class_errors(self):
        import numpy as np

        labels = np.asarray([2, 3, 0])
        predictions = np.asarray([0, 1, 3])
        probabilities = np.eye(4, dtype=np.float32)[predictions]
        metrics = classification_metrics(probabilities, labels,
                                        ["low", "medium", "high", "non_flood"])
        self.assertEqual(metrics["critical_error_count"], 2)
        self.assertAlmostEqual(metrics["critical_error_rate"], 2 / 3)
        self.assertAlmostEqual(metrics["mean_severity_distance"], 5 / 3)

    def test_rejects_ptq_from_another_split(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fp32, ptq, qat, qat_checkpoint, split = [root / name for name in (
                "fp32.onnx", "ptq.onnx", "qat.onnx", "qat.pth", "split.csv")]
            for path, content in ((fp32, b"fp32"), (ptq, b"ptq"), (qat, b"qat"),
                                  (qat_checkpoint, b"qat checkpoint"), (split, b"split")):
                path.write_bytes(content)
            config = {"preprocess": "letterbox", "image_size": 16,
                      "letterbox_fill": [124, 116, 104], "class_order": ["low", "high"]}
            source = {"checkpoint_sha256": "checkpoint", "onnx_sha256": sha256(fp32),
                      "preprocess": "letterbox_rgb_124_116_104", "input_size": 16,
                      "letterbox_fill": [124, 116, 104], "class_order": ["low", "high"]}
            ptq_manifest = {**source, "onnx_sha256": sha256(ptq), "source_onnx_sha256": source["onnx_sha256"],
                            "split_csv_sha256": "different-split", "precision": "int8"}
            qat_manifest = {**source, "onnx_sha256": sha256(qat), "source_onnx_sha256": source["onnx_sha256"],
                            "split_csv_sha256": sha256(split), "qat_checkpoint_sha256": sha256(qat_checkpoint),
                            "precision": "int8_qat"}

            with self.assertRaisesRegex(ValueError, "split CSV"):
                verify_lineage(fp32, ptq, qat, qat_checkpoint, source, ptq_manifest,
                               qat_manifest, config, split)


if __name__ == "__main__":
    unittest.main()
