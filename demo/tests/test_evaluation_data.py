from __future__ import annotations

import ast
import hashlib
import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import data.schema as candidate_schema
from data.generate import build_candidate_dataset
from data.schema import (
    GENERATOR_VERSION,
    SCHEMA_VERSION,
    canonical_json_bytes,
)
from demo.experiments.evaluation_data import (
    EvaluationDataError,
    load_evaluation_dataset,
    load_selected_configs,
)
from demo.experiments.protocol import protocol_bundle_sha256


# These fixture-only seeds are outside every repository protocol split.  The
# tests therefore never generate, open, or derive a real held-out test dataset.
DEVELOPMENT_SEEDS = tuple(range(81_000, 81_020))
CALIBRATION_SEEDS = tuple(range(82_000, 82_020))
FIXTURE_TEST_SEEDS = tuple(range(91_000, 91_040))
FIXTURE_SEED = FIXTURE_TEST_SEEDS[0]
OTHER_FIXTURE_SEED = 99_001


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_digest(value: dict[str, Any]) -> str:
    return _sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    )


@lru_cache(maxsize=4)
def _fixture_dataset_payload(seed: int) -> bytes:
    # Build from another unregistered seed, then assign only the fixture's
    # top-level identity.  This remains independent of every locked split even
    # when the schema registration function is monkeypatched for loader tests.
    source_seed = seed + 1_000_000
    data = build_candidate_dataset(source_seed)
    assert data["split"] == "unregistered"
    data["seed"] = seed
    data["split"] = "test"
    return canonical_json_bytes(data)


def _write_protocol(
    root: Path,
    *,
    selected_configs: dict[str, Any] | None = None,
) -> tuple[Path, Path]:
    protocol_dir = root / "demo" / "protocol"
    protocol_dir.mkdir(parents=True, exist_ok=True)
    seed_manifest = {
        "schema_version": 1,
        "splits": {
            "development": list(DEVELOPMENT_SEEDS),
            "calibration": list(CALIBRATION_SEEDS),
            "test": list(FIXTURE_TEST_SEEDS),
        },
        "expected_counts": {
            "development": 20,
            "calibration": 20,
            "test": 40,
        },
        "disjoint_required": True,
        "tuning": {
            "max_candidate_configurations_per_method_per_track": 128,
            "tracks": [
                {
                    "id": "fixture_label_track",
                    "calibration_labels": True,
                    "constraints": ["fixture"],
                },
                {
                    "id": "fixture_operational_track",
                    "calibration_labels": False,
                    "constraints": ["fixture"],
                },
            ],
        },
    }
    (protocol_dir / "seed_manifest.json").write_text(
        json.dumps(seed_manifest, sort_keys=True),
        encoding="utf-8",
    )
    (protocol_dir / "metric_contract.json").write_text(
        json.dumps({"schema_version": 1}, sort_keys=True),
        encoding="utf-8",
    )
    (protocol_dir / "baselines.json").write_text(
        json.dumps(
            {
                "schema_version": "fixture",
                "methods": [
                    {
                        "id": "fixture_method",
                        "search_space": {
                            "theta": [0.125, 0.25],
                            "weights": [[0.2, 0.3, 0.5]],
                        },
                        "configuration_count": 2,
                    }
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (protocol_dir / "calibration_contract.json").write_text(
        json.dumps(
            {
                "schema_version": "calibration-contract-v1",
                "selection": {
                    "fixture_label_track": {
                        "objective": "ari_labeled_reports",
                        "direction": "higher",
                    },
                    "fixture_operational_track": {
                        "objective": "partition_stability",
                        "direction": "higher",
                    },
                    "tie_break": [
                        "lower operator_review_burden",
                        "lower configuration complexity",
                        "lexicographic config_sha256",
                    ],
                },
                "stability": {"minimum_per_seed": 0.0},
                "review_policy": {"maximum_rate_per_seed": 1.0},
                "geographic_constraint": {
                    "maximum_metres_per_seed": 1_000_000.0,
                },
                "graph_constraints": {
                    "maximum_disconnected_communities_per_seed": 0,
                    "minimum_retained_fraction_per_seed": 0.0,
                    "maximum_retained_fraction_per_seed": 1.0,
                },
                "matched_composition_constraints": {
                    "retained_fraction_absolute_tolerance": 0.01,
                    "mean_degree_relative_tolerance": 0.05,
                    "joint_selection_rule": "fixture",
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    if selected_configs is not None:
        (protocol_dir / "selected_configs.json").write_text(
            json.dumps(selected_configs, sort_keys=True),
            encoding="utf-8",
        )
    protocol_sha = protocol_bundle_sha256(
        protocol_dir / "seed_manifest.json",
        protocol_dir / "metric_contract.json",
    )
    gate2_lock = root / "revision" / "gate2-lock.json"
    gate2_lock.parent.mkdir(parents=True, exist_ok=True)
    gate2_lock.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "gate": "Gate 2",
                "status": "locked",
                "protocol_sha256": protocol_sha,
                "gate1_binding": {
                    "gate1_lock_sha256": "a" * 64,
                    "accepted_run_manifest_sha256": "b" * 64,
                    "dataset_manifest_sha256": "c" * 64,
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return protocol_dir, gate2_lock


def _gate1_hash_binding(gate1_lock: Path) -> dict[str, str]:
    gate1_payload = gate1_lock.read_bytes()
    gate1 = json.loads(gate1_payload)
    return {
        "gate1_lock_sha256": _sha256(gate1_payload),
        "accepted_run_manifest_sha256": gate1["accepted_run"][
            "manifest_sha256"
        ],
        "dataset_manifest_sha256": gate1["data_contract"][
            "dataset_manifest_sha256"
        ],
    }


def _bind_gate2_to_gate1(gate2_lock: Path, gate1_lock: Path) -> None:
    gate2 = json.loads(gate2_lock.read_text(encoding="utf-8"))
    gate2["gate1_binding"] = _gate1_hash_binding(gate1_lock)
    gate2_lock.write_text(
        json.dumps(gate2, sort_keys=True),
        encoding="utf-8",
    )


def _manifest_entries(selected_payload: bytes) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    selected_sha = _sha256(selected_payload)
    for split, seeds in (
        ("development", DEVELOPMENT_SEEDS),
        ("calibration", CALIBRATION_SEEDS),
        ("test", FIXTURE_TEST_SEEDS),
    ):
        for seed in seeds:
            entries.append(
                {
                    "path": f"{split}/seed_{seed}.json",
                    "quality_status": "pass",
                    "seed": seed,
                    "sha256": (
                        selected_sha
                        if (split, seed) == ("test", FIXTURE_SEED)
                        else _sha256(f"fixture:{split}:{seed}".encode())
                    ),
                    "split": split,
                }
            )
    return entries


def _write_gate1_fixture(
    root: Path,
    *,
    selected_payload: bytes | None = None,
) -> tuple[Path, Path, Path]:
    payload = selected_payload or _fixture_dataset_payload(FIXTURE_SEED)
    run_id = "gate1-fixture"
    run_dir = root / "demo" / "artifacts" / "runs" / run_id
    dataset_root = run_dir / "work" / "datasets"
    source = dataset_root / "test" / f"seed_{FIXTURE_SEED}.json"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(payload)

    entries = _manifest_entries(payload)
    generator_sha = "1" * 64
    schema_sha = "2" * 64
    dataset_manifest = {
        "schema_version": "candidate-dataset-manifest-v2",
        "dataset_schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "generator_sha256": generator_sha,
        "schema_sha256": schema_sha,
        "seed_manifest_sha256": "3" * 64,
        "data_spec_sha256": "4" * 64,
        "seed_mapping": {
            "development": list(DEVELOPMENT_SEEDS),
            "calibration": list(CALIBRATION_SEEDS),
            "test": list(FIXTURE_TEST_SEEDS),
        },
        "split_summaries": {},
        "entries": entries,
    }
    dataset_manifest_payload = canonical_json_bytes(dataset_manifest)
    (dataset_root / "manifest.json").write_bytes(dataset_manifest_payload)
    dataset_manifest_sha = _sha256(dataset_manifest_payload)

    checksums = {
        f"work/datasets/{entry['path']}": entry["sha256"] for entry in entries
    }
    checksums["work/datasets/manifest.json"] = dataset_manifest_sha
    accepted_manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "status": "succeeded",
        "exit_code": 0,
        "checksums": checksums,
    }
    accepted_manifest_payload = (
        json.dumps(accepted_manifest, sort_keys=True) + "\n"
    ).encode()
    accepted_manifest_path = run_dir / "manifest.json"
    accepted_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    accepted_manifest_path.write_bytes(accepted_manifest_payload)

    gate1_lock = root / "revision" / "gate1-lock.json"
    gate1_lock.parent.mkdir(parents=True, exist_ok=True)
    gate1_lock.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "gate": "Gate 1",
                "status": "locked",
                "accepted_run": {
                    "run_id": run_id,
                    "manifest": (
                        "demo/artifacts/runs/gate1-fixture/manifest.json"
                    ),
                    "manifest_sha256": _sha256(accepted_manifest_payload),
                    "manifest_validation": "pass",
                    "status": "succeeded",
                    "exit_code": 0,
                },
                "protocol": {"seed_manifest_sha256": "3" * 64},
                "data_contract": {
                    "dataset_manifest_sha256": dataset_manifest_sha,
                    "dataset_schema_version": SCHEMA_VERSION,
                    "generator_version": GENERATOR_VERSION,
                    "generator_sha256": generator_sha,
                    "schema_sha256": schema_sha,
                    "data_spec_sha256": "4" * 64,
                    "n_datasets": 80,
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return dataset_root, source, gate1_lock


@pytest.fixture
def fixture_seed_registration(monkeypatch: pytest.MonkeyPatch) -> None:
    original = candidate_schema.registered_split_for_seed

    def registered_split(seed: int, *args: Any, **kwargs: Any) -> str | None:
        if seed in FIXTURE_TEST_SEEDS:
            return "test"
        return original(seed, *args, **kwargs)

    monkeypatch.setattr(
        candidate_schema,
        "registered_split_for_seed",
        registered_split,
    )


def test_evaluation_loader_releases_separated_views_only_after_gate2(
    tmp_path: Path,
    fixture_seed_registration: None,
) -> None:
    protocol_dir, gate2_lock = _write_protocol(tmp_path)
    dataset_root, _, gate1_lock = _write_gate1_fixture(tmp_path)
    _bind_gate2_to_gate1(gate2_lock, gate1_lock)

    loaded = load_evaluation_dataset(
        dataset_root,
        seed=FIXTURE_SEED,
        gate2_lock=gate2_lock,
        gate1_lock=gate1_lock,
        protocol_dir=protocol_dir,
        repository_root=tmp_path,
    )

    assert loaded.seed == FIXTURE_SEED
    assert loaded.events
    assert len(loaded.events) == len(loaded.evaluator_reports)
    assert loaded.ground_truth == tuple(
        row.gt_cluster for row in loaded.evaluator_reports
    )
    assert loaded.fake_truth == tuple(
        row.is_fake for row in loaded.evaluator_reports
    )
    assert all(event.gt_cluster == -1 for event in loaded.events)
    assert all(event.is_fake is False for event in loaded.events)
    assert any(label >= 0 for label in loaded.ground_truth)
    assert any(loaded.fake_truth)
    assert loaded.gate1_run_id == "gate1-fixture"
    assert len(loaded.source_sha256) == 64
    with pytest.raises(TypeError):
        loaded.incidents[0]["incident_id"] = "mutated"  # type: ignore[index]


def test_missing_or_mismatched_gate2_and_wrong_seed_fail_before_gate1(
    tmp_path: Path,
) -> None:
    protocol_dir, gate2_lock = _write_protocol(tmp_path)
    missing_gate1 = tmp_path / "revision" / "absent-gate1.json"
    missing_root = tmp_path / "absent-datasets"

    with pytest.raises(EvaluationDataError, match="Gate-2 lock"):
        load_evaluation_dataset(
            missing_root,
            seed=FIXTURE_SEED,
            gate2_lock=tmp_path / "revision" / "absent-gate2.json",
            gate1_lock=missing_gate1,
            protocol_dir=protocol_dir,
            repository_root=tmp_path,
        )

    lock = json.loads(gate2_lock.read_text(encoding="utf-8"))
    lock["protocol_sha256"] = "0" * 64
    gate2_lock.write_text(json.dumps(lock), encoding="utf-8")
    with pytest.raises(EvaluationDataError, match="Gate-2 lock"):
        load_evaluation_dataset(
            missing_root,
            seed=FIXTURE_SEED,
            gate2_lock=gate2_lock,
            gate1_lock=missing_gate1,
            protocol_dir=protocol_dir,
            repository_root=tmp_path,
        )

    _, valid_gate2 = _write_protocol(tmp_path)
    with pytest.raises(EvaluationDataError, match="not in the locked"):
        load_evaluation_dataset(
            missing_root,
            seed=OTHER_FIXTURE_SEED,
            gate2_lock=valid_gate2,
            gate1_lock=missing_gate1,
            protocol_dir=protocol_dir,
            repository_root=tmp_path,
        )


def test_gate2_release_rejects_seed_overlap_even_with_matching_hash(
    tmp_path: Path,
) -> None:
    protocol_dir, gate2_lock = _write_protocol(tmp_path)
    seed_path = protocol_dir / "seed_manifest.json"
    manifest = json.loads(seed_path.read_text(encoding="utf-8"))
    manifest["splits"]["development"][0] = FIXTURE_TEST_SEEDS[0]
    seed_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    lock = json.loads(gate2_lock.read_text(encoding="utf-8"))
    lock["protocol_sha256"] = protocol_bundle_sha256(
        seed_path,
        protocol_dir / "metric_contract.json",
    )
    gate2_lock.write_text(json.dumps(lock, sort_keys=True), encoding="utf-8")

    with pytest.raises(EvaluationDataError, match="disjoint"):
        load_evaluation_dataset(
            tmp_path / "absent-datasets",
            seed=FIXTURE_SEED,
            gate2_lock=gate2_lock,
            gate1_lock=tmp_path / "revision" / "absent-gate1.json",
            protocol_dir=protocol_dir,
            repository_root=tmp_path,
        )


def test_gate2_binding_rejects_replaced_gate1_lock_before_dataset_access(
    tmp_path: Path,
) -> None:
    protocol_dir, gate2_lock = _write_protocol(tmp_path)
    dataset_root, _, gate1_lock = _write_gate1_fixture(tmp_path)
    _bind_gate2_to_gate1(gate2_lock, gate1_lock)
    gate1_lock.write_bytes(gate1_lock.read_bytes() + b"\n")

    with pytest.raises(EvaluationDataError, match="differs from the Gate-2"):
        load_evaluation_dataset(
            dataset_root,
            seed=FIXTURE_SEED,
            gate2_lock=gate2_lock,
            gate1_lock=gate1_lock,
            protocol_dir=protocol_dir,
            repository_root=tmp_path,
        )


def test_evaluation_loader_rejects_wrong_root_and_file_checksum(
    tmp_path: Path,
    fixture_seed_registration: None,
) -> None:
    protocol_dir, gate2_lock = _write_protocol(tmp_path)
    dataset_root, source, gate1_lock = _write_gate1_fixture(tmp_path)
    _bind_gate2_to_gate1(gate2_lock, gate1_lock)

    with pytest.raises(EvaluationDataError, match="dataset root"):
        load_evaluation_dataset(
            tmp_path / "copied-datasets",
            seed=FIXTURE_SEED,
            gate2_lock=gate2_lock,
            gate1_lock=gate1_lock,
            protocol_dir=protocol_dir,
            repository_root=tmp_path,
        )

    source.write_bytes(_fixture_dataset_payload(OTHER_FIXTURE_SEED))
    with pytest.raises(EvaluationDataError, match="checksum mismatch"):
        load_evaluation_dataset(
            dataset_root,
            seed=FIXTURE_SEED,
            gate2_lock=gate2_lock,
            gate1_lock=gate1_lock,
            protocol_dir=protocol_dir,
            repository_root=tmp_path,
        )


def test_authenticated_swap_or_relabel_is_rejected_by_schema(
    tmp_path: Path,
    fixture_seed_registration: None,
) -> None:
    protocol_dir, gate2_lock = _write_protocol(tmp_path)
    # Seal a different arbitrary fixture payload under FIXTURE_SEED's path and
    # checksums.  Authentication passes, then identity-aware schema validation
    # must reject the swapped/relabelled payload.
    swapped = _fixture_dataset_payload(OTHER_FIXTURE_SEED)
    dataset_root, _, gate1_lock = _write_gate1_fixture(
        tmp_path,
        selected_payload=swapped,
    )
    _bind_gate2_to_gate1(gate2_lock, gate1_lock)
    with pytest.raises(EvaluationDataError, match="schema validation failed"):
        load_evaluation_dataset(
            dataset_root,
            seed=FIXTURE_SEED,
            gate2_lock=gate2_lock,
            gate1_lock=gate1_lock,
            protocol_dir=protocol_dir,
            repository_root=tmp_path,
        )


def _aggregate_fixture_metrics(
    rows: list[dict[str, float]],
) -> dict[str, float]:
    names = sorted(set.intersection(*(set(row) for row in rows)))
    aggregate: dict[str, float] = {}
    for name in names:
        values = np.asarray([row[name] for row in rows], dtype=float)
        aggregate[name] = float(np.mean(values))
        aggregate[f"{name}__sd"] = (
            float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
        )
        aggregate[f"{name}__median"] = float(np.median(values))
        aggregate[f"{name}__min"] = float(np.min(values))
        aggregate[f"{name}__max"] = float(np.max(values))
        aggregate[f"{name}__denominator"] = float(len(values))
    return aggregate


def _write_calibration_source(
    root: Path,
    protocol_dir: Path,
    gate1_lock: Path,
    *,
    select_nonoptimal: bool = False,
    no_feasible_operational: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    run_id = "calibration-fixture"
    run_dir = root / "demo" / "artifacts" / "runs" / run_id
    protocol_snapshots: dict[str, dict[str, Any]] = {}
    protocol_hashes: dict[str, str] = {}
    checksums: dict[str, str] = {}
    for source_path in sorted(protocol_dir.glob("*.json")):
        if source_path.name == "selected_configs.json":
            continue
        payload = source_path.read_bytes()
        relative = f"inputs/protocol/{source_path.name}"
        snapshot = run_dir / relative
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes(payload)
        payload_sha = _sha256(payload)
        protocol_hashes[source_path.name] = payload_sha
        protocol_snapshots[source_path.name] = {
            "snapshot": relative,
            "sha256": payload_sha,
        }
        checksums[relative] = payload_sha
    calibration_protocol_sha = _canonical_digest(protocol_hashes)
    gate1_binding = _gate1_hash_binding(gate1_lock)
    gate1 = json.loads(gate1_lock.read_text(encoding="utf-8"))
    gate1_run_manifest = (
        gate1_lock.resolve().parent.parent / gate1["accepted_run"]["manifest"]
    ).resolve()
    dataset_manifest_source = (
        gate1_run_manifest.parent / "work" / "datasets" / "manifest.json"
    )
    dataset_snapshot_relative = "inputs/datasets/00-manifest.json"
    dataset_snapshot = run_dir / dataset_snapshot_relative
    dataset_snapshot.parent.mkdir(parents=True, exist_ok=True)
    dataset_snapshot.write_bytes(dataset_manifest_source.read_bytes())
    checksums[dataset_snapshot_relative] = gate1_binding[
        "dataset_manifest_sha256"
    ]

    configs = [
        {"theta": 0.125, "weights": [0.2, 0.3, 0.5]},
        {"theta": 0.25, "weights": [0.2, 0.3, 0.5]},
    ]
    selected_config = configs[0] if select_nonoptimal else configs[1]
    selected_config_sha = _canonical_digest(selected_config)
    selections: list[dict[str, Any]] = []
    evaluations: list[dict[str, Any]] = []
    promoted_rows: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, Any]] = []
    for track_id, objective in (
        ("fixture_label_track", "ari_labeled_reports"),
        ("fixture_operational_track", "partition_stability"),
    ):
        excluded = (
            no_feasible_operational
            and track_id == "fixture_operational_track"
        )
        effective_selected_config = None if excluded else selected_config
        effective_selected_sha = None if excluded else selected_config_sha
        selection_identity = {
            "method_id": "fixture_method",
            "track_id": track_id,
            "objective": objective,
            "direction": "higher",
            "selected_config_sha256": effective_selected_sha,
        }
        selection_sha = _canonical_digest(selection_identity)
        selections.append(
            {
                **selection_identity,
                "status": (
                    "no_feasible_candidate" if excluded else "selected"
                ),
                "selected_config": effective_selected_config,
                "selection_sha256": selection_sha,
                "considered_configurations": 2,
                "succeeded_configurations": 2,
                "feasible_configurations": 0 if excluded else 2,
                "rejected": (
                    [
                        {
                            "config_sha256": _canonical_digest(config),
                            "reasons": [
                                "geographic_diameter__max=2000000.0 "
                                "violates <=1000000.0"
                            ],
                        }
                        for config in configs
                    ]
                    if excluded
                    else []
                ),
            }
        )
        for config in configs:
            objective_value = 0.5 if config["theta"] == 0.125 else 0.9
            seed_metrics = []
            for seed in CALIBRATION_SEEDS:
                metrics = {
                    "seed": float(seed),
                    "partition_stability": (
                        objective_value
                        if objective == "partition_stability"
                        else 1.0
                    ),
                    "operator_review_burden_rate": 0.0,
                    "geographic_diameter": (
                        2_000_000.0 if excluded else 0.0
                    ),
                    "operator_review_burden": 0.0,
                    "complexity": 2.0,
                }
                metrics[objective] = objective_value
                seed_metrics.append(metrics)
            evaluations.append(
                {
                    "method_id": "fixture_method",
                    "track_id": track_id,
                    "stage": "calibration",
                    "config": config,
                    "config_sha256": _canonical_digest(config),
                    "status": "succeeded",
                    "seed_metrics": seed_metrics,
                    "aggregate_metrics": _aggregate_fixture_metrics(
                        seed_metrics
                    ),
                    "failures": [],
                    "configuration_evaluation_count": 1,
                    "seed_run_count": len(CALIBRATION_SEEDS),
                    "wall_time_seconds": 0.1,
                }
            )
        if excluded:
            excluded_rows.append(
                {
                    "method_id": "fixture_method",
                    "track_id": track_id,
                    "status": "no_feasible_candidate",
                    "source_artifact_id": "calibration_source",
                    "source_selection_sha256": selection_sha,
                }
            )
        else:
            promoted_rows.append(
                {
                    "method_id": "fixture_method",
                    "track_id": track_id,
                    "config": selected_config,
                    "config_sha256": selected_config_sha,
                    "source_artifact_id": "calibration_source",
                    "source_selection_sha256": selection_sha,
                }
            )
    artifact = {
        "schema_version": "calibration-artifact-v1",
        "protocol_sha256": calibration_protocol_sha,
        "seed_manifest_sha256": protocol_hashes["seed_manifest.json"],
        "metric_contract_sha256": protocol_hashes["metric_contract.json"],
        "configuration_evaluation_count": len(evaluations),
        "seed_run_count": len(evaluations) * len(CALIBRATION_SEEDS),
        "failed_configuration_count": 0,
        "evaluations": evaluations,
        "selections": selections,
        "metadata": {
            "stage": "calibration",
            "complete_seed_set": True,
            "seed_limit": None,
            "frozen_dataset": {
                "gate1_lock_sha256": gate1_binding["gate1_lock_sha256"],
                "accepted_run_manifest_sha256": gate1_binding[
                    "accepted_run_manifest_sha256"
                ],
                "dataset_manifest_sha256": gate1_binding[
                    "dataset_manifest_sha256"
                ],
            },
        },
    }
    artifact["artifact_content_sha256"] = _canonical_digest(artifact)
    table_payload = (
        json.dumps(artifact, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode()

    table_relative = "tables/calibration.json"
    table_path = run_dir / table_relative
    table_path.parent.mkdir(parents=True, exist_ok=True)
    table_path.write_bytes(table_payload)
    table_sha = _sha256(table_payload)
    checksums[table_relative] = table_sha
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "status": "succeeded",
        "exit_code": 0,
        "timestamps": {},
        "command": [
            "python",
            "-m",
            "demo.experiments.exp18_tuned_baselines",
        ],
        "repository": {"commit": "fixture", "dirty_patch_sha256": "8" * 64},
        "environment": {"hardware": {}, "blas": {}, "threads": {}},
        "inputs": {
            "config": {},
            "protocol": {
                "sha256": calibration_protocol_sha,
                "files": protocol_snapshots,
            },
            "seed_manifest": {
                "sha256": protocol_hashes["seed_manifest.json"],
            },
            "metric_contract": {
                "sha256": protocol_hashes["metric_contract.json"],
            },
            "datasets": [
                {
                    "snapshot": dataset_snapshot_relative,
                    "sha256": gate1_binding["dataset_manifest_sha256"],
                }
            ],
        },
        "checksums": checksums,
    }
    manifest_payload = (
        json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    ).encode()
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_bytes(manifest_payload)

    source = {
        "id": "calibration_source",
        "run_id": run_id,
        "manifest_path": (
            "demo/artifacts/runs/calibration-fixture/manifest.json"
        ),
        "manifest_sha256": _sha256(manifest_payload),
        "table_path": table_relative,
        "table_sha256": table_sha,
        "artifact_content_sha256": artifact["artifact_content_sha256"],
    }
    selected = {
        "schema_version": "selected-configs-v1",
        "calibration_protocol_sha256": calibration_protocol_sha,
        "sources": [source],
        "selections": promoted_rows,
        "exclusions": excluded_rows,
        "audit": {
            "all_calibration_failures_retained": True,
            "configuration_evaluation_count": len(evaluations),
        },
    }
    return selected, source


def test_selected_configs_trace_to_a_sealed_calibration_table(
    tmp_path: Path,
) -> None:
    protocol_dir, _ = _write_protocol(tmp_path)
    _, _, gate1_lock = _write_gate1_fixture(tmp_path)
    selected, _ = _write_calibration_source(
        tmp_path,
        protocol_dir,
        gate1_lock,
    )
    protocol_dir, gate2_lock = _write_protocol(
        tmp_path,
        selected_configs=selected,
    )
    _bind_gate2_to_gate1(gate2_lock, gate1_lock)
    bundle = load_selected_configs(
        protocol_dir / "selected_configs.json",
        gate2_lock=gate2_lock,
        protocol_dir=protocol_dir,
        artifact_root=tmp_path,
    )
    loaded = bundle.selection_for("fixture_method", "fixture_label_track")
    assert loaded.config["theta"] == selected["selections"][0]["config"]["theta"]
    assert list(loaded.config["weights"]) == selected["selections"][0]["config"][
        "weights"
    ]
    assert loaded.config_sha256 == selected["selections"][0]["config_sha256"]
    assert bundle.sources[0].run_id == "calibration-fixture"


def test_selected_configs_preserve_authenticated_no_feasible_pair(
    tmp_path: Path,
) -> None:
    protocol_dir, _ = _write_protocol(tmp_path)
    _, _, gate1_lock = _write_gate1_fixture(tmp_path)
    selected, _ = _write_calibration_source(
        tmp_path,
        protocol_dir,
        gate1_lock,
        no_feasible_operational=True,
    )
    protocol_dir, gate2_lock = _write_protocol(
        tmp_path,
        selected_configs=selected,
    )
    _bind_gate2_to_gate1(gate2_lock, gate1_lock)
    bundle = load_selected_configs(
        protocol_dir / "selected_configs.json",
        gate2_lock=gate2_lock,
        protocol_dir=protocol_dir,
        artifact_root=tmp_path,
    )
    exclusion = bundle.exclusion_for(
        "fixture_method",
        "fixture_operational_track",
    )
    assert exclusion.status == "no_feasible_candidate"
    assert len(bundle.selections) == 1
    assert len(bundle.exclusions) == 1
    with pytest.raises(
        EvaluationDataError,
        match="no feasible calibration candidate",
    ):
        bundle.selection_for(
            "fixture_method",
            "fixture_operational_track",
        )


def test_selected_configs_reject_sealed_nonoptimal_calibration_winner(
    tmp_path: Path,
) -> None:
    protocol_dir, _ = _write_protocol(tmp_path)
    _, _, gate1_lock = _write_gate1_fixture(tmp_path)
    selected, _ = _write_calibration_source(
        tmp_path,
        protocol_dir,
        gate1_lock,
        select_nonoptimal=True,
    )
    protocol_dir, gate2_lock = _write_protocol(
        tmp_path,
        selected_configs=selected,
    )
    _bind_gate2_to_gate1(gate2_lock, gate1_lock)

    with pytest.raises(
        EvaluationDataError,
        match="winner/audit is not mechanically reproducible",
    ):
        load_selected_configs(
            protocol_dir / "selected_configs.json",
            gate2_lock=gate2_lock,
            protocol_dir=protocol_dir,
            artifact_root=tmp_path,
        )


def test_selected_configs_reject_protocol_or_artifact_hash_mutation(
    tmp_path: Path,
) -> None:
    protocol_dir, _ = _write_protocol(tmp_path)
    _, _, gate1_lock = _write_gate1_fixture(tmp_path)
    selected, source_record = _write_calibration_source(
        tmp_path,
        protocol_dir,
        gate1_lock,
    )
    protocol_dir, gate2_lock = _write_protocol(
        tmp_path,
        selected_configs=selected,
    )
    _bind_gate2_to_gate1(gate2_lock, gate1_lock)
    table = (
        tmp_path
        / "demo"
        / "artifacts"
        / "runs"
        / "calibration-fixture"
        / source_record["table_path"]
    )
    table.write_bytes(table.read_bytes() + b" ")
    with pytest.raises(EvaluationDataError, match="not sealed|checksum"):
        load_selected_configs(
            protocol_dir / "selected_configs.json",
            gate2_lock=gate2_lock,
            protocol_dir=protocol_dir,
            artifact_root=tmp_path,
        )

    fresh_root = tmp_path / "fresh"
    fresh_protocol, _ = _write_protocol(fresh_root)
    _, _, fresh_gate1 = _write_gate1_fixture(fresh_root)
    selected, _ = _write_calibration_source(
        fresh_root,
        fresh_protocol,
        fresh_gate1,
    )
    fresh_protocol, fresh_lock = _write_protocol(
        fresh_root,
        selected_configs=selected,
    )
    _bind_gate2_to_gate1(fresh_lock, fresh_gate1)
    registry_path = fresh_protocol / "selected_configs.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["selections"][0]["config"]["theta"] = 0.5
    registry_path.write_text(json.dumps(registry, sort_keys=True), encoding="utf-8")
    # Refreshing the fixture lock proves the independent config/source binding,
    # rather than merely exercising the enclosing protocol checksum.
    _, fresh_lock = _write_protocol(
        fresh_root,
        selected_configs=registry,
    )
    _bind_gate2_to_gate1(fresh_lock, fresh_gate1)
    with pytest.raises(EvaluationDataError, match="config checksum mismatch"):
        load_selected_configs(
            registry_path,
            gate2_lock=fresh_lock,
            protocol_dir=fresh_protocol,
            artifact_root=fresh_root,
        )


def test_evaluation_module_has_no_tuning_loader_import_or_export() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "experiments"
        / "evaluation_data.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.add(node.module or "")
    assert not any(
        module == "calibration" or module.endswith(".calibration")
        for module in imported_modules
    )

    import demo.experiments.evaluation_data as evaluation_data

    assert "load_tuning_dataset" not in evaluation_data.__all__
    assert not hasattr(evaluation_data, "load_tuning_dataset")


def test_pre_gate2_entrypoints_do_not_import_evaluation_release_modules() -> None:
    experiments = Path(__file__).resolve().parents[1] / "experiments"
    pre_gate2_entrypoints = (
        "calibration.py",
        "exp15_calibrated_comparison.py",
        "exp16_priority_robustness.py",
        "exp17_dispatch_outcomes.py",
        "exp18_tuned_baselines.py",
        "exp19_factorial_ablation.py",
        "exp20_output_burden.py",
        "exp22_runtime_repro.py",
        "pre_gate2.py",
    )
    forbidden = {"evaluation_data", "evaluation_protocol"}
    violations: list[str] = []
    for filename in pre_gate2_entrypoints:
        tree = ast.parse(
            (experiments / filename).read_text(encoding="utf-8"),
            filename=filename,
        )
        for node in ast.walk(tree):
            imported: list[str] = []
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported = [node.module or ""]
            for module in imported:
                if module.split(".")[-1] in forbidden:
                    violations.append(f"{filename}:{node.lineno}:{module}")
    assert violations == []
