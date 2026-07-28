from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from demo.experiments.artifacts import (
    ArtifactError,
    ArtifactRun,
    validate_manifest,
)
from demo.experiments import run_candidate


SOURCE_ROOT = Path(__file__).resolve().parents[2]


class ArtifactRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repository = Path(self.temporary.name) / "repository"
        self.repository.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "tests@example.invalid")
        self._git("config", "user.name", "Foundation Tests")

        demo = self.repository / "demo"
        (demo / "pipeline").mkdir(parents=True)
        (demo / "data").mkdir()
        (demo / "protocol").mkdir()
        (demo / "pipeline" / "config.py").write_text(
            "CONFIG = {'fixture': True}\n", encoding="utf-8"
        )
        (demo / "data" / "dataset.json").write_text(
            '{"fixture": true}\n', encoding="utf-8"
        )
        for source in (SOURCE_ROOT / "demo" / "protocol").glob("*.json"):
            shutil.copy2(source, demo / "protocol" / source.name)
        (self.repository / "protected.txt").write_text("original\n", encoding="utf-8")
        self._git("add", ".")
        self._git("commit", "-qm", "fixture")

        self.protocol_dir = demo / "protocol"
        self.config_path = demo / "pipeline" / "config.py"
        self.dataset_path = demo / "data" / "dataset.json"
        self.runs_root = demo / "artifacts" / "runs"

    def _git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=self.repository,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _create(self, run_id: str = "unit-run") -> ArtifactRun:
        return ArtifactRun.create(
            run_id=run_id,
            command=(sys.executable, "-c", "pass"),
            runs_root=self.runs_root,
            repository_root=self.repository,
            protocol_dir=self.protocol_dir,
            config_path=self.config_path,
            dataset_paths=(self.dataset_path,),
        )

    def test_exclusive_run_and_output_writes(self) -> None:
        run = self._create()
        run.write_json("tables/result.json", {"value": 1})
        with self.assertRaises(ArtifactError):
            run.write_json("tables/result.json", {"value": 2})
        with self.assertRaises(ArtifactError):
            run.write_json("../escape.json", {})
        with self.assertRaises(ArtifactError):
            self._create()

        manifest_path = run.finalize(exit_code=0)
        manifest = validate_manifest(manifest_path)
        self.assertEqual(manifest["status"], "succeeded")
        self.assertEqual(manifest["exit_code"], 0)
        self.assertFalse(manifest["repository"]["dirty"])
        self.assertIn("hardware", manifest["environment"])
        self.assertIn("blas", manifest["environment"])
        self.assertIn("threads", manifest["environment"])
        self.assertIn("sha256", manifest["inputs"]["config"])
        self.assertIn("sha256", manifest["inputs"]["protocol"])
        self.assertIn("sha256", manifest["inputs"]["seed_manifest"])
        self.assertIn("tables/result.json", manifest["checksums"])
        with self.assertRaises(ArtifactError):
            run.finalize(exit_code=0)

    def test_checksum_validation_detects_post_finalize_change(self) -> None:
        run = self._create()
        output = run.write_json("tables/result.json", {"value": 1})
        manifest_path = run.finalize(exit_code=0)
        output.write_text('{"value": 2}\n', encoding="utf-8")
        with self.assertRaises(ArtifactError):
            validate_manifest(manifest_path)

    def test_checksum_validation_detects_file_added_after_finalize(self) -> None:
        run = self._create()
        manifest_path = run.finalize(exit_code=0)
        (run.path / "tables" / "unrecorded.json").write_text(
            "{}\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ArtifactError, "file set changed"):
            validate_manifest(manifest_path)

    def test_nested_output_named_manifest_is_checksummed(self) -> None:
        run = self._create()
        run.write_json("tables/manifest.json", {"nested": True})
        manifest = validate_manifest(run.finalize(exit_code=0))
        self.assertIn("tables/manifest.json", manifest["checksums"])

    def test_dirty_patch_and_untracked_identity_are_recorded(self) -> None:
        (self.repository / "protected.txt").write_text("changed\n", encoding="utf-8")
        (self.repository / "untracked.txt").write_text("new\n", encoding="utf-8")
        run = self._create("dirty-run")
        manifest = validate_manifest(run.finalize(exit_code=0))
        repository = manifest["repository"]
        self.assertTrue(repository["dirty"])
        self.assertGreater(repository["dirty_patch_bytes"], 0)
        self.assertEqual(len(repository["dirty_patch_sha256"]), 64)
        self.assertIn(
            "untracked.txt",
            {record["path"] for record in repository["untracked_files"]},
        )
        patch = (run.path / repository["dirty_patch_path"]).read_text(
            encoding="utf-8", errors="replace"
        )
        self.assertIn("protected.txt", patch)
        self.assertIn("untracked.txt", patch)

    @unittest.skipUnless(shutil.which("bwrap"), "Bubblewrap is required")
    def test_candidate_wrapper_writes_only_to_new_run(self) -> None:
        code = (
            "import json, os; from pathlib import Path; "
            "Path(os.environ['DEMO_TABLES_DIR'], 'candidate.json')"
            ".write_text(json.dumps({'ok': True}), encoding='utf-8')"
        )
        completed = self._run_candidate("sandbox-success", code)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        runs = list(self.runs_root.iterdir())
        self.assertEqual(len(runs), 1)
        manifest = validate_manifest(runs[0] / "manifest.json")
        self.assertEqual(manifest["status"], "succeeded")
        self.assertIn("tables/candidate.json", manifest["checksums"])
        self.assertEqual(
            (self.repository / "protected.txt").read_text(encoding="utf-8"),
            "original\n",
        )

    @unittest.skipUnless(shutil.which("bwrap"), "Bubblewrap is required")
    def test_candidate_wrapper_prevents_source_overwrite(self) -> None:
        protected = self.repository / "protected.txt"
        code = (
            "from pathlib import Path; "
            f"Path({str(protected)!r}).write_text('overwritten', encoding='utf-8')"
        )
        completed = self._run_candidate("sandbox-denial", code)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(protected.read_text(encoding="utf-8"), "original\n")
        runs = list(self.runs_root.iterdir())
        self.assertEqual(len(runs), 1)
        manifest = validate_manifest(runs[0] / "manifest.json")
        self.assertEqual(manifest["status"], "failed")

    @unittest.skipUnless(shutil.which("bwrap"), "Bubblewrap is required")
    def test_candidate_wrapper_seals_keyboard_interrupt_as_aborted(self) -> None:
        arguments = [
            "--label",
            "interrupted",
            "--runs-root",
            str(self.runs_root),
            "--repository-root",
            str(self.repository),
            "--protocol-dir",
            str(self.protocol_dir),
            "--config",
            str(self.config_path),
            "--dataset",
            str(self.dataset_path),
            "--",
            sys.executable,
            "-c",
            "pass",
        ]
        with mock.patch.object(
            run_candidate,
            "_bubblewrap_command",
            side_effect=KeyboardInterrupt,
        ):
            self.assertEqual(run_candidate.main(arguments), 130)

        runs = list(self.runs_root.iterdir())
        self.assertEqual(len(runs), 1)
        manifest = validate_manifest(runs[0] / "manifest.json")
        self.assertEqual(manifest["status"], "aborted")
        self.assertEqual(manifest["exit_code"], 130)
        self.assertIn("KeyboardInterrupt", manifest["error"])

    def _run_candidate(
        self, label: str, code: str
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(SOURCE_ROOT)
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "demo.experiments.run_candidate",
                "--label",
                label,
                "--runs-root",
                str(self.runs_root),
                "--repository-root",
                str(self.repository),
                "--protocol-dir",
                str(self.protocol_dir),
                "--config",
                str(self.config_path),
                "--dataset",
                str(self.dataset_path),
                "--",
                sys.executable,
                "-c",
                code,
            ],
            cwd=SOURCE_ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )


if __name__ == "__main__":
    unittest.main()
