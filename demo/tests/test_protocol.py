from __future__ import annotations

import ast
import dataclasses
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from demo.experiments import protocol
from demo.experiments.calibration import load_calibration_contract
from demo.experiments.evaluation_protocol import load_locked_test_seeds


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_DIR = REPOSITORY_ROOT / "demo" / "protocol"
EXPERIMENTS_DIR = REPOSITORY_ROOT / "demo" / "experiments"


class ProtocolContractTests(unittest.TestCase):
    def test_locked_tuning_view_contains_only_development_and_calibration(self) -> None:
        locked = protocol.load_tuning_protocol()
        self.assertEqual(locked.development_seeds, tuple(range(1000, 1020)))
        self.assertEqual(locked.calibration_seeds, tuple(range(2000, 2020)))
        self.assertEqual(locked.max_candidates_per_method_track, 128)

        runtime_view = dataclasses.asdict(locked)
        self.assertNotIn("test_seeds", runtime_view)
        all_runtime_integers: set[int] = set()

        def collect(value: object) -> None:
            if isinstance(value, bool):
                return
            if isinstance(value, int):
                all_runtime_integers.add(value)
            elif isinstance(value, dict):
                for nested in value.values():
                    collect(nested)
            elif isinstance(value, (list, tuple)):
                for nested in value:
                    collect(nested)

        collect(runtime_view)
        self.assertTrue(all_runtime_integers.isdisjoint(range(3000, 3040)))
        self.assertFalse(
            any("test" in exported.casefold() for exported in protocol.__all__)
        )

    def test_seed_manifest_has_exact_disjoint_splits(self) -> None:
        manifest = json.loads(
            (PROTOCOL_DIR / "seed_manifest.json").read_text(encoding="utf-8")
        )
        splits = {key: tuple(value) for key, value in manifest["splits"].items()}
        self.assertEqual(splits["development"], tuple(range(1000, 1020)))
        self.assertEqual(splits["calibration"], tuple(range(2000, 2020)))
        self.assertEqual(splits["test"], tuple(range(3000, 3040)))
        self.assertFalse(set(splits["development"]) & set(splits["calibration"]))
        self.assertFalse(set(splits["development"]) & set(splits["test"]))
        self.assertFalse(set(splits["calibration"]) & set(splits["test"]))

    def test_candidate_budget_is_enforced_at_runtime(self) -> None:
        locked = protocol.load_tuning_protocol()
        locked.validate_candidate_count(1)
        locked.validate_candidate_count(128)
        for invalid in (0, 129, -1, True, 1.5):
            with self.subTest(invalid=invalid):
                with self.assertRaises(protocol.ProtocolError):
                    locked.validate_candidate_count(invalid)  # type: ignore[arg-type]

    def test_metric_directions_and_holm_families_are_declared(self) -> None:
        contract = json.loads(
            (PROTOCOL_DIR / "metric_contract.json").read_text(encoding="utf-8")
        )
        expected = {
            "clustering_ari": {"ari_labeled_reports": "higher"},
            "incident_integrity": {
                "incident_split_loss": "lower",
                "incident_merge_loss": "lower",
            },
            "operational_burden": {
                "false_operational_destinations": "lower",
                "operator_review_burden": "lower",
            },
            "dispatch_independent_outcomes": {
                "latent_harm": "lower",
                "deadline_miss_rate": "lower",
            },
        }
        observed: dict[str, dict[str, str]] = {}
        for family in contract["co_primary_families"]:
            self.assertEqual(family["multiplicity"], {"procedure": "holm", "alpha": 0.05})
            observed[family["id"]] = {
                endpoint["id"]: endpoint["direction"]
                for endpoint in family["endpoints"]
            }
            self.assertTrue(
                all(endpoint["denominator_required"] for endpoint in family["endpoints"])
            )
        self.assertEqual(observed, expected)
        self.assertEqual(
            contract["inference"]["multiplicity_scope"],
            "within each declared co-primary family",
        )

    def test_baseline_registry_has_hypotheses_and_audited_dependencies(self) -> None:
        registry = json.loads(
            (PROTOCOL_DIR / "baselines.json").read_text(encoding="utf-8")
        )
        self.assertEqual(registry["schema_version"], "baseline-registry-v2")
        self.assertEqual(registry["dependency_audit"]["status"], "pass")
        packages = registry["dependency_audit"]["packages"]
        literature = registry["literature_audit"]
        methods = registry["methods"]
        self.assertEqual(len(methods), 10)

        seen_ids: set[str] = set()
        for method in methods:
            with self.subTest(method=method["id"]):
                self.assertNotIn(method["id"], seen_ids)
                seen_ids.add(method["id"])
                self.assertTrue(method["hypothesis"].strip())
                self.assertIn("inputs", method)
                self.assertIn("preset_k", method)
                self.assertLessEqual(
                    method["configuration_count"],
                    registry["max_configurations_per_method_per_track"],
                )
                expanded_count = 1
                for values in method["search_space"].values():
                    expanded_count *= len(values)
                self.assertEqual(
                    expanded_count,
                    method["configuration_count"],
                )
                implementation = method["implementation"]
                self.assertTrue(implementation["entry_points"])
                self.assertIn(
                    implementation["status"],
                    {"available", "adapter_required_before_gate_2"},
                )
                for dependency in implementation["dependencies"]:
                    self.assertIn(dependency, packages)
                    self.assertTrue(packages[dependency]["version"])
                    self.assertTrue(packages[dependency]["license"])
                    self.assertTrue(packages[dependency]["review_outcome"])
                for literature_id in method["literature_ids"]:
                    self.assertIn(literature_id, literature)

        by_id = {method["id"]: method for method in methods}
        self.assertEqual(
            {method["implementation"]["status"] for method in methods},
            {"available"},
        )
        self.assertIn(
            "demo.pipeline.baselines.build_convex_similarity_matrix",
            by_id["multiple_similarity_louvain"]["implementation"]["entry_points"],
        )
        self.assertFalse(by_id["coordinate_kmeans"]["equivalent_competitor"])
        self.assertEqual(by_id["st_dbscan"]["role"], "direct_spatiotemporal")
        self.assertIn(
            "spatial_constraint",
            by_id["spatial_constrained_agglomerative"]["role"],
        )
        self.assertIn(
            "coordinate_kmeans",
            registry["noise_convention"]["all_points_methods"],
        )
        self.assertEqual(
            registry["factorial_ablations"]["clustering_effect_orders"],
            [1, 2, 3, 4],
        )

    def test_operational_calibration_contract_has_numeric_guardrails(self) -> None:
        contract = load_calibration_contract()
        self.assertEqual(contract.review_policy.id, "standard")
        self.assertEqual(
            contract.objectives["benchmark_label_aware"],
            ("ari_labeled_reports", "higher"),
        )
        self.assertEqual(
            contract.objectives["operational_label_free"],
            ("partition_stability", "higher"),
        )
        self.assertGreaterEqual(contract.minimum_partition_stability, 0.0)
        self.assertLessEqual(contract.maximum_review_rate, 1.0)
        self.assertGreater(contract.maximum_geographic_diameter_m, 0.0)

    def test_tuning_sources_have_no_static_test_seed_access(self) -> None:
        candidate_sources = sorted(
            path
            for path in EXPERIMENTS_DIR.glob("*.py")
            if "tun" in path.stem.casefold() or "calibrat" in path.stem.casefold()
        )
        self.assertTrue(candidate_sources, "static audit found no tuning modules")
        violations: list[str] = []
        for source in candidate_sources:
            tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, int):
                    if not isinstance(node.value, bool) and 3000 <= node.value <= 3039:
                        violations.append(f"{source.name}:{node.lineno}: test seed literal")
                if isinstance(node, ast.ImportFrom):
                    imported = node.module or ""
                    if imported.endswith("evaluation_protocol"):
                        violations.append(
                            f"{source.name}:{node.lineno}: evaluation-protocol import"
                        )
                if isinstance(node, ast.Subscript):
                    slice_value = node.slice
                    if (
                        isinstance(slice_value, ast.Constant)
                        and slice_value.value == "test"
                    ):
                        violations.append(
                            f"{source.name}:{node.lineno}: test split subscript"
                        )
        self.assertEqual(violations, [])

    def test_test_seed_release_requires_exact_gate2_lock(self) -> None:
        locked = protocol.load_tuning_protocol()
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            missing = temporary_path / "missing.json"
            with self.assertRaises(protocol.ProtocolError):
                load_locked_test_seeds(missing)

            gate2_lock = temporary_path / "gate2-lock.json"
            gate2_lock.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "gate": "Gate 2",
                        "status": "locked",
                        "protocol_sha256": locked.protocol_sha256,
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                load_locked_test_seeds(gate2_lock), tuple(range(3000, 3040))
            )

            copied_protocol = temporary_path / "protocol"
            shutil.copytree(PROTOCOL_DIR, copied_protocol)
            baseline_path = copied_protocol / "baselines.json"
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            baseline["tampered"] = True
            baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
            with self.assertRaises(protocol.ProtocolError):
                load_locked_test_seeds(gate2_lock, copied_protocol)


if __name__ == "__main__":
    unittest.main()
