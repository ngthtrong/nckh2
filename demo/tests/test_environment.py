from __future__ import annotations

import ast
import importlib.metadata
import json
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

from demo.environment.capture import (
    THREAD_ENVIRONMENT_VARIABLES,
    capture_environment,
    write_environment_capture,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEMO_ROOT = REPOSITORY_ROOT / "demo"


class EnvironmentLockTests(unittest.TestCase):
    def test_python_boundary_and_direct_dependencies_are_exact(self) -> None:
        project = tomllib.loads(
            (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]
        self.assertEqual(project["requires-python"], ">=3.12,<3.13")
        self.assertTrue(project["dependencies"])
        self.assertTrue(all("==" in requirement for requirement in project["dependencies"]))

    def test_full_lock_uses_exact_versions(self) -> None:
        requirements = [
            line.strip()
            for line in (REPOSITORY_ROOT / "requirements.lock")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertTrue(requirements)
        self.assertTrue(all(line.count("==") == 1 for line in requirements))
        installed = {
            distribution.metadata["Name"].casefold(): distribution.version
            for distribution in importlib.metadata.distributions()
            if distribution.metadata.get("Name")
        }
        for requirement in requirements:
            name, version = requirement.split("==", 1)
            with self.subTest(requirement=requirement):
                self.assertEqual(installed.get(name.casefold()), version)

    def test_environment_capture_has_required_provenance(self) -> None:
        capture = capture_environment()
        self.assertEqual(capture["schema_version"], 1)
        self.assertEqual(capture["python"]["implementation"], "CPython")
        self.assertTrue(capture["python"]["version"])
        self.assertGreater(capture["hardware"]["logical_cpu_count"], 0)
        self.assertIn("memory_bytes", capture["hardware"])
        self.assertIn("configuration", capture["blas"])
        self.assertEqual(
            set(capture["threads"]["environment"]),
            set(THREAD_ENVIRONMENT_VARIABLES),
        )
        self.assertTrue(capture["packages"])
        for tool in ("git", "bubblewrap", "xelatex", "bibtex"):
            self.assertIn(tool, capture["tools"])

    def test_environment_capture_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "environment.json"
            write_environment_capture(destination)
            with self.assertRaises(FileExistsError):
                write_environment_capture(destination)

    def test_every_third_party_demo_import_is_declared(self) -> None:
        distribution_for_import = {
            "community": "python-louvain",
            "igraph": "igraph",
            "leidenalg": "leidenalg",
            "matplotlib": "matplotlib",
            "networkx": "networkx",
            "numpy": "numpy",
            "pandas": "pandas",
            "pytest": "pytest",
            "scipy": "scipy",
            "sklearn": "scikit-learn",
            "threadpoolctl": "threadpoolctl",
        }
        imported_roots: set[str] = set()
        for source in DEMO_ROOT.rglob("*.py"):
            if ".venv" in source.parts:
                continue
            tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    imported_roots.add(node.module.split(".", 1)[0])

        known_local = {
            "artifacts",
            "common",
            "data",
            "demo",
            "environment",
            "evaluation_protocol",
            "pipeline",
            "protocol",
        }
        unknown = imported_roots - sys.stdlib_module_names - known_local - set(
            distribution_for_import
        )
        self.assertEqual(unknown, set())

        locked_names = {
            line.split("==", 1)[0].casefold()
            for line in (REPOSITORY_ROOT / "requirements.lock")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        missing = {
            distribution
            for imported, distribution in distribution_for_import.items()
            if imported in imported_roots and distribution.casefold() not in locked_names
        }
        self.assertEqual(missing, set())


if __name__ == "__main__":
    unittest.main()
