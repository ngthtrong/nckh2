from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import Package, portable_source, synthetic_source, safe_name, notebook
from runtime import Run, write, verify_files, digest
from analysis import mcnemar_exact, holm, analyze_predictions
from synthetic_data import create_payload, validate_payload, TAG, REMOVED_PREFIX


class BundleTests(unittest.TestCase):
    def test_zip_paths_and_undeclared_names(self):
        for name in ["../bad", "/etc/passwd", "a/../../bad", "a\\bad", "C:/bad"]:
            with self.assertRaises(ValueError):
                safe_name(name)
        self.assertEqual(safe_name("a/b.csv"), "a/b.csv")

    def test_manifest_detects_corruption(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            f = root / "input.txt"
            f.write_text("original")
            manifest = {"input.txt": digest(f)}
            verify_files(root, manifest)
            f.write_text("changed")
            with self.assertRaises(ValueError):
                verify_files(root, manifest)
            with self.assertRaises(ValueError):
                verify_files(root, {"../escape": "x"})

    def test_resume_rejects_config_or_output_drift(self):
        class FixtureRun(Run):
            def do_fixture(self, folder):
                write(folder / "result.json", {"value": 1})
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write(root / "bundle-inputs.json", {"fixture": True})
            run = FixtureRun(root, {})
            self.assertEqual(run.stage("fixture")["status"], "COMPLETED")
            self.assertEqual(run.stage("fixture")["status"], "COMPLETED")
            with self.assertRaises(ValueError):
                FixtureRun(root, {"pruning_epochs": 1})
            write(root / "bundle-results/fixture/result.json", {"value": 2})
            with self.assertRaises(ValueError):
                run.stage("fixture")

    def test_failed_step_is_not_automatically_retried(self):
        class FixtureRun(Run):
            def do_fixture(self, folder):
                raise RuntimeError("deliberate test failure")
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write(root / "bundle-inputs.json", {})
            run = FixtureRun(root, {})
            with self.assertRaises(RuntimeError):
                run.stage("fixture")
            self.assertEqual(json.loads((root / "bundle-results/fixture/stage.json").read_text())["status"], "FAILED")
            with self.assertRaisesRegex(RuntimeError, "no automatic retry"):
                run.stage("fixture")

    def test_native_gold_never_becomes_available_from_silver(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write(root / "bundle-inputs.json", {"silver_present": True})
            run = Run(root, {})
            self.assertEqual(run.stage("native_gold")["status"], "DATA_NOT_READY")
            self.assertEqual(run.stage("device_tests")["status"], "REQUIRES_DEVICE")

    def synthetic_fixture(self, root):
        rows = []
        for split in ["train", "val", "test"]:
            for i in range(6):
                relative = f"high/{split}-{i}.jpg"
                path = root / "products/fe/model/Dataset_Flood" / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((split + str(i)).encode())
                rows.append({"relative_path": relative, "label": "high", "split": split,
                             "split_group": split + "-" + str(i // 2)})
        return rows

    def test_synthetic_ready_is_deterministic_and_not_native_gold(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rows = self.synthetic_fixture(root)
            payload = create_payload(root, rows)
            self.assertEqual(payload, create_payload(root, rows))
            status = validate_payload(payload, root=root)
            self.assertEqual(status["status"], "DATA_READY")
            self.assertEqual(status["evidence_class"], TAG)
            self.assertFalse(status["native_gold"])
            self.assertEqual(status["human_labels"], 0)
            self.assertTrue(all(REMOVED_PREFIX not in r["text_vi"] for r in payload["records"]))
            self.assertTrue(all("MẪU TỰ SOẠN" not in r["text_vi"] for r in payload["records"]))
            self.assertIsNone(payload["text_prefix"])
            other = create_payload(root, [{**r, "label": "low"} for r in rows])
            self.assertEqual([(r["label"], r["text_vi"]) for r in payload["records"]],
                             [(r["label"], r["text_vi"]) for r in other["records"]])
            payload["native_gold"] = True
            with self.assertRaises(ValueError):
                validate_payload(payload, root=root)

    def test_synthetic_detects_image_or_origin_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            payload = create_payload(root, self.synthetic_fixture(root))
            payload["records"][0]["human_annotators"] = 2
            with self.assertRaises(ValueError):
                validate_payload(payload, root=root)
            payload["records"][0]["human_annotators"] = 0
            (root / payload["records"][0]["image_path"]).write_bytes(b"changed")
            with self.assertRaises(ValueError):
                validate_payload(payload, root=root)

    def test_synthetic_sources_are_isolated_and_json_outputs_disclose_origin(self):
        root = Path(__file__).resolve().parents[2]
        for module in ["common", "features", "train", "fine_tune", "evaluate", "verify", "verify_encoder_update"]:
            name = "thucnghiem/vi_rescue/" + module + ".py"
            adapted, _ = portable_source(name, (root / name).read_text())
            synthetic = synthetic_source(module, adapted)
            compile(synthetic, name, "exec")
            self.assertNotIn("label_ai", synthetic)
        with tempfile.TemporaryDirectory() as d:
            source = "thucnghiem/vi_rescue/common.py"
            adapted, _ = portable_source(source, (root / source).read_text())
            space = {"__file__": str(Path(d) / "thucnghiem/vi_synthetic/common.py")}
            exec(synthetic_source("common", adapted), space)
            output = Path(d) / "metric.json"
            space["write_json"](output, {"status": "COMPLETED"})
            result = json.loads(output.read_text())
            self.assertEqual(result["evidence_class"], TAG)
            self.assertFalse(result["native_gold"])
            self.assertEqual(result["purpose"], "TECHNICAL_PIPELINE_TEST_ONLY")

    def test_mcnemar_and_holm_known_values(self):
        self.assertEqual(mcnemar_exact(0, 0), 1)
        self.assertEqual(mcnemar_exact(3, 3), 1)
        self.assertEqual(mcnemar_exact(0, 6), .03125)
        self.assertEqual(holm({"a": .01, "b": .04, "c": .03}), {"a": .03, "c": .06, "b": .06})

    def test_paired_analysis_preserves_ids_and_group_units(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            split = [{"label": "high", "file_name": f"{i}.jpg", "split": "test", "split_group": str(i // 2)} for i in range(8)]
            prediction = [{"ground_truth": "high", "image_path": f"C:\\data\\high\\{i}.jpg",
                           "pred_a": "low", "pred_b": "high"} for i in range(8)]
            for path, rows in [(root / "split.csv", split), (root / "pred.csv", prediction)]:
                with path.open("w", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
            result = analyze_predictions(root / "pred.csv", root / "split.csv", root / "result.json", draws=20)
            self.assertEqual(result["n_images"], 8)
            self.assertEqual(result["n_split_groups"], 4)
            self.assertEqual(result["pairs"]["a -> b"]["wrong_to_correct"], 8)
            self.assertEqual(result["metrics"]["a"]["critical_errors"], 8)
            with (root / "pred.csv").open("a") as f:
                f.write("high,C:/data/high/0.jpg,low,high\n")
            with self.assertRaises(ValueError):
                analyze_predictions(root / "pred.csv", root / "split.csv", root / "bad.json", draws=20)

    def test_source_adapters_are_bounded_and_originals_untouched(self):
        base = Path(__file__).resolve().parents[2]
        names = ["products/fe/tools/structured_pruning.py", "products/fe/tools/qat_finetune.py",
                 "thucnghiem/vi_rescue/features.py", "thucnghiem/vi_rescue/fine_tune.py"]
        for name in names:
            path = base / name
            old = digest(path)
            patched, changes = portable_source(name, path.read_text())
            self.assertTrue(changes)
            compile(patched, name, "exec")
            self.assertEqual(digest(path), old)
        source = (base / names[0]).read_text()
        with self.assertRaises(ValueError):
            portable_source(names[0], source.replace('    parser.add_argument("--prune-ratio",', "changed"))

    def test_notebook_code_compiles_without_hidden_outputs(self):
        value = notebook([])
        for i, item in enumerate(value["cells"]):
            if item["cell_type"] == "code":
                compile("".join(item["source"]), f"cell-{i}", "exec")
                self.assertEqual(item["outputs"], [])
                self.assertIsNone(item["execution_count"])


if __name__ == "__main__":
    unittest.main()
