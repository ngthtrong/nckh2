"""Từ tools/: python -m unittest discover -s test."""
import contextlib
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy as np
from PIL import Image

import compare_models as compare
import smoke_test_v2 as smoke


class SmokeTest(unittest.TestCase):
    def test_shared_pipeline_and_no_pass_on_incomplete_or_invalid_run(self):
        self.assertIs(smoke.evaluate_models, compare.evaluate_models)
        self.assertEqual(smoke.EDGE_DIR, compare.ROOT / "model" / "Edge Ai")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = dict(image_size=16, preprocess="letterbox", letterbox_fill=[124, 116, 104],
                          dropout=0.25, class_order=["low", "medium", "high"])
            config_path, checkpoint, split = root / "config.json", root / "model.pth", root / "split.csv"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            checkpoint.write_bytes(b"checkpoint fixture; runner mocked")
            rows = []
            for index, (partition, label) in enumerate((("train", "low"), ("test", "low"),
                                                        ("test", "low"), ("test", "medium"), ("test", "high"))):
                path = root / f"image{index}.jpg"
                exif = Image.Exif()
                exif[274] = 6
                Image.new("RGB", (20, 10), (index * 40, 50, 100)).save(path, exif=exif)
                rows.append(dict(relative_path=path.name, label=label, split=partition))

            def save_split(selected):
                with split.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(selected)

            save_split(rows)
            args = ["--config", str(config_path), "--checkpoint", str(checkpoint),
                    "--split-csv", str(split), "--dataset-dir", str(root)]
            valid = np.array([[0.8, 0.1, 0.1]], dtype=np.float32)
            runner = Mock(return_value=valid)
            output = io.StringIO()
            with patch.object(smoke, "pth_runner", return_value=runner), contextlib.redirect_stdout(output):
                smoke.main(args)
            text = output.getvalue()
            self.assertIn("smoke_test=PASS (3/3", text)
            self.assertIn("true=low", text)
            self.assertIn("true=medium", text)
            self.assertIn("true=high", text)
            self.assertNotIn("image2.jpg:", text)  # Ưu tiên ảnh khác lớp, không lấy 3 ảnh low đầu tiên.
            for call in runner.call_args_list:
                self.assertEqual(call.args[0].shape, (1, 3, 16, 16))
                self.assertEqual(call.args[0].dtype, np.float32)

            output = io.StringIO()
            with patch.object(smoke, "pth_runner", return_value=runner), \
                    patch.object(smoke, "evaluate_models", return_value=({}, {}, [])), contextlib.redirect_stdout(output):
                with self.assertRaisesRegex(RuntimeError, "không được bỏ qua"):
                    smoke.main(args)
            self.assertNotIn("smoke_test=PASS", output.getvalue())

            output = io.StringIO()
            runner = Mock(side_effect=[valid] * 3 + [np.full((1, 3), np.nan, dtype=np.float32)])
            with patch.object(smoke, "pth_runner", return_value=runner), contextlib.redirect_stdout(output):
                with self.assertRaisesRegex(ValueError, "probabilities"):
                    smoke.main(args)
            self.assertNotIn("smoke_test=PASS", output.getvalue())

            save_split(rows[:2])  # Chỉ còn một ảnh test, không được PASS thiếu 2 ảnh.
            output = io.StringIO()
            with patch.object(smoke, "pth_runner") as load, contextlib.redirect_stdout(output):
                with self.assertRaisesRegex(ValueError, "không đủ"):
                    smoke.main(args)
                load.assert_not_called()
            self.assertNotIn("smoke_test=PASS", output.getvalue())

            save_split(rows)
            (root / "image4.jpg").unlink()
            output = io.StringIO()
            with patch.object(smoke, "pth_runner") as load, contextlib.redirect_stdout(output):
                with self.assertRaisesRegex(ValueError, "Ảnh không có"):
                    smoke.main(args)
                load.assert_not_called()
            self.assertNotIn("smoke_test=PASS", output.getvalue())


if __name__ == "__main__":
    unittest.main()
