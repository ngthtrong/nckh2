"""Offline checks only: never starts a backend, proxy, or HTTP request."""
import csv
import hashlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / "weak_network.py"


class RunnerTests(unittest.TestCase):
    def load_runner(self):
        spec = importlib.util.spec_from_file_location("validation_network_runner", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
        except ModuleNotFoundError as error:
            self.fail(f"Offline input checks must not require HTTP dependencies: {error}")
        return module

    def fixture(self, folder, entries=None):
        root = folder / "images"
        (root / "low").mkdir(parents=True)
        (root / "high").mkdir()
        for relative in ("low/ảnh.png", "high/b.webp"):
            image_format = "PNG" if relative.endswith("png") else "WEBP"
            Image.new("RGB", (8, 12), (40, 90, 120)).save(root / relative, format=image_format)
        rows = entries or [
            {"relative_path": "high/b.webp", "label": "high", "split": "val"},
            {"relative_path": "low/ảnh.png", "label": "low", "split": "val"},
        ]
        csv_path = folder / "val.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["relative_path", "label", "split"])
            writer.writeheader()
            writer.writerows(rows)
        return csv_path, root

    def test_csv_order_and_small_non_jpeg_images_are_preserved(self):
        runner = self.load_runner()
        self.assertTrue(callable(getattr(runner, "load_inputs", None)), "CSV input loader is missing")
        with tempfile.TemporaryDirectory() as temporary:
            csv_path, root = self.fixture(Path(temporary))
            before = csv_path.read_bytes()
            inputs = runner.load_inputs(csv_path, root)
            self.assertEqual([item.relative_path for item in inputs], ["high/b.webp", "low/ảnh.png"])
            self.assertEqual([item.mime_type for item in inputs], ["image/webp", "image/png"])
            self.assertEqual(inputs[0].original, (root / "high/b.webp").read_bytes())
            self.assertEqual(csv_path.read_bytes(), before)
            with Image.open(io.BytesIO(inputs[0].compressed)) as compressed:
                self.assertEqual(compressed.format, "JPEG")

    def test_rejects_non_validation_rows_duplicates_and_path_escape(self):
        runner = self.load_runner()
        self.assertTrue(callable(getattr(runner, "load_inputs", None)))
        cases = [
            [{"relative_path": "low/ảnh.png", "label": "low", "split": "train"}],
            [{"relative_path": "low/ảnh.png", "label": "low", "split": "val"}] * 2,
            [{"relative_path": "../outside.png", "label": "low", "split": "val"}],
            [{"relative_path": "low/missing.png", "label": "low", "split": "val"}],
        ]
        for entries in cases:
            with self.subTest(entries=entries), tempfile.TemporaryDirectory() as temporary:
                csv_path, root = self.fixture(Path(temporary), entries)
                with self.assertRaises(ValueError):
                    runner.load_inputs(csv_path, root)

    def test_every_input_has_all_nine_conditions_and_repeats(self):
        runner = self.load_runner()
        self.assertTrue(callable(getattr(runner, "build_plan", None)), "Measurement plan is missing")
        with tempfile.TemporaryDirectory() as temporary:
            csv_path, root = self.fixture(Path(temporary))
            inputs = runner.load_inputs(csv_path, root)
            plan = runner.build_plan(inputs, 2)
            self.assertEqual(len(plan), 36)
            self.assertEqual(len({task.key for task in plan}), 36)
            for relative_path in ("high/b.webp", "low/ảnh.png"):
                self.assertEqual(sum(task.image.relative_path == relative_path for task in plan), 18)

    def test_http_200_with_rejected_message_is_not_success(self):
        runner = self.load_runner()
        self.assertTrue(callable(getattr(runner, "interpret_response", None)), "Backend ACK validation is missing")
        result = runner.interpret_response(200, {
            "results": [{"message_id": "m1", "status": "rejected", "retryable": False,
                         "code": "INVALID_PAYLOAD", "result": None}]
        }, "metadata", "m1")
        self.assertFalse(result.accepted)
        self.assertEqual(result.error_code, "INVALID_PAYLOAD")
        accepted = runner.interpret_response(200, {
            "results": [{"message_id": "m1", "status": "accepted", "retryable": False,
                         "code": None, "result": {"record_id": "exp-1"}}]
        }, "metadata", "m1")
        self.assertTrue(accepted.accepted)
        mismatched = runner.interpret_response(200, {
            "results": [{"message_id": "another", "status": "accepted", "retryable": False,
                         "code": None, "result": {"record_id": "exp-1"}}]
        }, "metadata", "m1")
        self.assertFalse(mismatched.accepted)

    def test_unsupported_original_is_reported_as_format_error(self):
        runner = self.load_runner()
        self.assertTrue(callable(getattr(runner, "interpret_response", None)))
        result = runner.interpret_response(415, {
            "detail": {"code": "UNSUPPORTED_IMAGE", "error": "Ảnh phải là JPEG, PNG hoặc WebP"}
        }, "original")
        self.assertFalse(result.accepted)
        self.assertEqual(result.error_code, "UNSUPPORTED_IMAGE")

    def test_resume_uses_recorded_rows_not_a_stale_checkpoint(self):
        runner = self.load_runner()
        self.assertTrue(callable(getattr(runner, "effective_rows", None)), "Resume selection is missing")
        rows = [
            {"profile": "3G", "mode": "original", "relative_path": "low/ảnh.png", "repeat": 1,
             "attempt": 1, "load1": None, "success": False},
            {"profile": "3G", "mode": "original", "relative_path": "low/ảnh.png", "repeat": 1,
             "attempt": 2, "load1": 999999, "success": True},
        ]
        chosen = runner.effective_rows(rows)
        self.assertEqual(len(chosen), 1)
        self.assertEqual(next(iter(chosen.values()))["attempt"], 1)
        self.assertFalse(next(iter(chosen.values()))["success"])
        self.assertEqual(len(rows), 2)

    def test_missing_load_average_is_unknown_not_zero(self):
        runner = self.load_runner()
        self.assertTrue(callable(getattr(runner, "read_load_average", None)))
        with patch.object(runner.os, "getloadavg", create=True, side_effect=OSError("not supported")):
            self.assertIsNone(runner.read_load_average())

    def test_no_arguments_does_not_create_run_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run([sys.executable, "-B", str(SCRIPT)], cwd=temporary,
                                    capture_output=True, text=True, encoding="utf-8", timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("--check-inputs", result.stdout)
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_check_inputs_with_small_images_does_not_create_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            csv_path, root = self.fixture(folder)
            source_hash = hashlib.sha256(csv_path.read_bytes()).hexdigest()
            before = {path.relative_to(folder) for path in folder.rglob("*")}
            result = subprocess.run([
                sys.executable, "-B", str(SCRIPT), "--check-inputs", "--images-csv", str(csv_path),
                "--dataset-root", str(root),
            ], cwd=folder, capture_output=True, text=True, encoding="utf-8", timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("18 lượt đo", result.stdout)
            self.assertEqual({path.relative_to(folder) for path in folder.rglob("*")}, before)
            self.assertEqual(hashlib.sha256(csv_path.read_bytes()).hexdigest(), source_hash)

    def test_changed_configuration_cannot_be_resumed(self):
        runner = self.load_runner()
        self.assertTrue(callable(getattr(runner, "validate_resume", None)))
        runner.validate_resume({"csv_sha256": "same", "repeats": 1}, {"csv_sha256": "same", "repeats": 1})
        with self.assertRaises(ValueError):
            runner.validate_resume({"csv_sha256": "old", "repeats": 1}, {"csv_sha256": "new", "repeats": 1})
        with self.assertRaises(ValueError):
            runner.validate_resume({"csv_sha256": "same", "repeats": 1}, {"csv_sha256": "same", "repeats": 2})

    def test_result_csv_round_trip_preserves_failure_and_unknown_load(self):
        runner = self.load_runner()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "results.csv"
            row = {field: "" for field in runner.FIELDS}
            row.update({
                "profile": "3G", "mode": "original", "run": 1, "image_bytes": 100,
                "wire_bytes_up": 45, "http_status": 415, "input_index": 1, "repeat": 1,
                "attempt": 1, "elapsed_s": 0.5, "success": False, "backend_accepted": False,
                "relative_path": "low/ảnh.png", "error_code": "UNSUPPORTED_IMAGE",
            })
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=runner.FIELDS)
                writer.writeheader()
                writer.writerow(row)
            loaded = runner.load_rows(path)
            self.assertIsNone(loaded[0]["load1"])
            self.assertFalse(loaded[0]["success"])
            self.assertEqual(loaded[0]["relative_path"], "low/ảnh.png")
            self.assertEqual(len(runner.effective_rows(loaded)), 1)

    def test_report_uses_saved_load_limit_and_shows_format_failures(self):
        runner = self.load_runner()
        manifest = {
            "run_id": "offline-test", "expected_measurements": 2,
            "configuration": {
                "load1_limit": 2, "images": [{"relative_path": "low/a.avif"}], "repeats": 1,
                "profiles": [{"name": "3G", "kbps": 400, "rtt_ms": 200}],
                "modes": ["original", "compressed"], "csv_sha256": "fixture",
            },
        }
        rows = [{
            "profile": "3G", "mode": "original", "relative_path": "low/a.avif", "repeat": 1,
            "load1": None, "success": False, "elapsed_s": 0.5, "image_bytes": 100,
            "wire_bytes_up": 150, "error_code": "UNSUPPORTED_IMAGE",
        }, {
            "profile": "3G", "mode": "compressed", "relative_path": "low/a.avif", "repeat": 1,
            "load1": 3, "success": True, "elapsed_s": 0.2, "image_bytes": 80,
            "wire_bytes_up": 130, "error_code": "",
        }]
        with tempfile.TemporaryDirectory() as temporary:
            runner.write_report(rows, manifest, Path(temporary))
            text = (Path(temporary) / "weak_network.md").read_text(encoding="utf-8")
            self.assertIn("1/2 lượt hợp lệ", text)
            self.assertIn("UNSUPPORTED_IMAGE: 1", text)
            self.assertNotIn("| 3G | compressed |", text)


if __name__ == "__main__":
    unittest.main()
