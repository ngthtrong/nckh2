"""Chạy từ tools/: python -m unittest discover -s test (không cần ONNX Runtime)."""
import csv
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
from PIL import Image, ImageOps

import quantize_model as q


class QuantizePipelineTest(unittest.TestCase):
    def test_evaluation_rejects_invalid_outputs_before_argmax(self):
        config = dict(class_order=["low", "high"], image_size=16, letterbox_fill=[124, 116, 104])
        low = np.array([[0.75, 0.25]], dtype=np.float32)
        high = np.array([[0.25, 0.75]], dtype=np.float32)

        def runtime(outputs):
            return SimpleNamespace(get_inputs=lambda: [SimpleNamespace(name="image")],
                                   run=Mock(side_effect=[[output] for output in outputs]))

        invalid_outputs = [np.full((1, 2), np.nan, dtype=np.float32),
                           np.array([[np.inf, 0]], dtype=np.float32), low.astype(np.float64),
                           low[0], np.array([[0.5, 0.25, 0.25]], dtype=np.float32),
                           np.array([[-0.1, 1.1]], dtype=np.float32),
                           np.array([[0.2, 0.2]], dtype=np.float32)]
        with patch.object(q, "preprocess", return_value=np.zeros((1, 3, 16, 16), dtype=np.float32)):
            for invalid in invalid_outputs:
                for engine in (0, 1):  # FP32 và INT8 đều phải được kiểm tra.
                    for good_warmups in (0, 3):
                        with self.subTest(engine=engine, warmups=good_warmups, output=invalid):
                            sessions = [runtime([low] * 4), runtime([low] * 4)]
                            sessions[engine] = runtime([low] * good_warmups + [invalid])
                            with patch.object(q, "session", side_effect=sessions), patch.object(q.np, "argmax") as argmax:
                                with self.assertRaisesRegex(ValueError, "probabilities"):
                                    q.evaluate(Path("fp32.onnx"), Path("int8.onnx"), [(Path("test.jpg"), 0)], config)
                                argmax.assert_not_called()
            sessions = [runtime([low] * 3 + [low, high]), runtime([low] * 3 + [high, low])]
            with patch.object(q, "session", side_effect=sessions):
                result = q.evaluate(Path("fp32.onnx"), Path("int8.onnx"),
                                    [(Path("low.jpg"), 0), (Path("high.jpg"), 1)], config)
            self.assertEqual(result["n_images"], 2)
            self.assertEqual(result["fp32"]["accuracy"], 1)
            self.assertEqual(result["int8"]["accuracy"], 0)
            self.assertEqual(result["top1_agreement"], 0)
            with self.assertRaisesRegex(ValueError, "rỗng"):
                q.evaluate(Path("fp32.onnx"), Path("int8.onnx"), [], config)

    def test_uint8_quantized_probabilities_allow_rounding_error_only_for_int8(self):
        quantized = np.array([[0.5921569, 0.16862746, 0.1137255, 0.11764707]], dtype=np.float32)
        with self.assertRaisesRegex(ValueError, "probabilities"):
            q.validate_probabilities(quantized, 4)
        accepted = q.validate_probabilities(
            quantized, 4, sum_atol=q.quantized_probability_sum_atol(4))
        np.testing.assert_array_equal(accepted, quantized[0])
        invalid = quantized.copy()
        invalid[0, 0] = 0.55
        with self.assertRaisesRegex(ValueError, "probabilities"):
            q.validate_probabilities(invalid, 4, sum_atol=q.quantized_probability_sum_atol(4))

    def test_split_preprocessing_and_manifest(self):
        q.validate_input_shape(["batch", 3, 256, 256], 256)
        q.validate_input_shape([1, 3, 256, 256], 256)
        with self.assertRaises(ValueError):
            q.validate_input_shape([1, 3, 224, 224], 256)
        with self.assertRaises(ValueError):
            q.validate_input_shape([2, 3, 256, 256], 256)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = []
            for i, split in enumerate(("train", "val", "test")):
                path = root / f"{split}.jpg"
                image = Image.new("RGB", (20, 10), (20 + i * 60, 30, 50))
                exif = Image.Exif()
                exif[274] = 6
                image.save(path, exif=exif)
                rows.append(dict(relative_path=path.name, label="low", split=split,
                                 split_group=f"group{i}"))
            csv_path = root / "split.csv"

            def write_rows():
                with csv_path.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)

            write_rows()
            splits = q.load_splits(csv_path, root, ["low"])
            self.assertEqual(splits["train"], [(root / "train.jpg", 0)])
            self.assertEqual(splits["test"], [(root / "test.jpg", 0)])
            config = dict(seed=42, class_order=["low"], image_size=256,
                          letterbox_fill=[124, 116, 104])
            with patch.object(q, "preprocess", wraps=q.preprocess) as preprocess:
                reader = q.StratifiedReader(splits["train"], "input", 50, config)
                self.assertEqual(reader.count, 1)
                self.assertEqual(reader.get_next()["input"].shape, (1, 3, 256, 256))
                self.assertIsNone(reader.get_next())
                self.assertEqual(preprocess.call_args.args[0], root / "train.jpg")
            with Image.open(root / "test.jpg") as image:
                expected = ImageOps.pad(ImageOps.exif_transpose(image).convert("RGB"),
                                        (256, 256), method=Image.Resampling.BILINEAR,
                                        color=(124, 116, 104), centering=(0.5, 0.5))
                array = np.asarray(expected, dtype=np.float32) / 255.0
                expected_tensor = ((array - q.MEAN) / q.STD).transpose(2, 0, 1)[None]
            np.testing.assert_array_equal(q.preprocess(root / "test.jpg"), expected_tensor)
            rows[-1]["split_group"] = "group0"
            write_rows()
            with self.assertRaisesRegex(ValueError, "leakage"):
                q.load_splits(csv_path, root, ["low"])
            rows[-1]["split_group"] = "group2"
            (root / "test.jpg").write_bytes((root / "train.jpg").read_bytes())
            write_rows()
            with self.assertRaisesRegex(ValueError, "leakage"):
                q.load_splits(csv_path, root, ["low"])
            source = dict(checkpoint_sha256="checkpoint", onnx_sha256="fp32",
                          pte_sha256="pte", version="fp32-pte", input_size=256,
                          preprocess="letterbox_rgb_124_116_104",
                          letterbox_fill=[124, 116, 104], class_order=["low"])
            original = source.copy()
            int8 = root / "int8.onnx"
            int8.write_bytes(b"synthetic int8 model")
            manifest = q.int8_manifest(source, int8, csv_path)
            self.assertEqual(source, original)
            self.assertEqual(manifest["onnx_sha256"], q.sha256(int8))
            self.assertEqual(manifest["source_onnx_sha256"], "fp32")
            self.assertNotIn("pte_sha256", manifest)


if __name__ == "__main__":
    unittest.main()
