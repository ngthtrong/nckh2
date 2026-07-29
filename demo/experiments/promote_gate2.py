"""Mechanically promote sealed calibration outcomes and lock Gate 2.

The command validates complete Exp15/Exp18 calibration artifacts without
opening any evaluation dataset.  It promotes feasible configurations, retains
authenticated ``no_feasible_candidate`` records, writes the final protocol
member, and only then creates the Gate-2 lock that releases the test loader.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from demo.experiments import evaluation_data as release
from demo.experiments.artifacts import validate_manifest
from demo.experiments.pre_gate2 import (
    canonical_json_bytes,
    resolve_frozen_dataset_root,
)
from demo.experiments.protocol import (
    DEFAULT_PROTOCOL_DIR,
    file_sha256,
    load_tuning_protocol,
    protocol_bundle_sha256,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GATE1_LOCK = REPOSITORY_ROOT / "revision" / "gate1-lock.json"
DEFAULT_GATE2_LOCK = REPOSITORY_ROOT / "revision" / "gate2-lock.json"
DEFAULT_SELECTED_CONFIGS = DEFAULT_PROTOCOL_DIR / "selected_configs.json"
COMPOSITION_METHODS = {
    "product_louvain",
    "additive_louvain",
    "multiple_similarity_louvain",
}


@dataclass(frozen=True)
class CalibrationSource:
    id: str
    manifest: Mapping[str, Any]
    manifest_path: Path
    artifact: Mapping[str, Any]
    table_path: Path
    evaluation_index: Mapping[
        tuple[str, str, str],
        Mapping[str, Any],
    ]


def _relative_to_repository(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError as exc:
        raise ValueError(f"path is outside the repository: {resolved}") from exc


def _canonical_object(path: Path, *, label: str) -> tuple[bytes, dict[str, Any]]:
    try:
        payload = path.read_bytes()
        value = json.loads(payload)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is absent or invalid") from exc
    if not isinstance(value, dict) or payload != canonical_json_bytes(value):
        raise ValueError(f"{label} must be a canonical JSON object")
    return payload, value


def _gate1_binding(gate1_lock: Path) -> dict[str, str]:
    try:
        lock = json.loads(gate1_lock.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ValueError("Gate-1 lock is absent or invalid") from exc
    accepted = lock.get("accepted_run")
    data_contract = lock.get("data_contract")
    if (
        lock.get("gate") != "Gate 1"
        or lock.get("status") != "locked"
        or not isinstance(accepted, dict)
        or not isinstance(data_contract, dict)
        or not isinstance(accepted.get("manifest_sha256"), str)
        or not isinstance(data_contract.get("dataset_manifest_sha256"), str)
    ):
        raise ValueError("Gate-1 lock has no authenticated data binding")
    return {
        "gate1_lock_sha256": file_sha256(gate1_lock),
        "accepted_run_manifest_sha256": accepted["manifest_sha256"],
        "dataset_manifest_sha256": data_contract["dataset_manifest_sha256"],
    }


def _validate_source(
    table_path: Path,
    *,
    source_id: str,
    composition_source: bool,
    protocol_dir: Path,
    gate1_lock: Path,
) -> CalibrationSource:
    source = table_path.resolve()
    if source.parent.name != "tables":
        raise ValueError(f"{source_id} table is not below a candidate tables directory")
    run_root = source.parent.parent
    manifest_path = run_root / "manifest.json"
    manifest = validate_manifest(manifest_path)
    if manifest.get("status") != "succeeded" or manifest.get("exit_code") != 0:
        raise ValueError(f"{source_id} candidate run did not succeed")

    payload, artifact = _canonical_object(
        source,
        label=f"{source_id} calibration table",
    )
    relative_table = source.relative_to(run_root).as_posix()
    table_sha = hashlib.sha256(payload).hexdigest()
    if manifest.get("checksums", {}).get(relative_table) != table_sha:
        raise ValueError(f"{source_id} table is not sealed by its run manifest")

    protocol = load_tuning_protocol(protocol_dir)
    preselection_sha, preselection_members = (
        release._preselection_protocol_identity(protocol_dir)
    )
    sealed_sha, sealed_members = release._sealed_protocol_identity(
        manifest,
        manifest_path=manifest_path,
    )
    if (
        preselection_sha != protocol.protocol_sha256
        or sealed_sha != preselection_sha
        or sealed_members != preselection_members
        or artifact.get("protocol_sha256") != preselection_sha
        or artifact.get("seed_manifest_sha256")
        != protocol.seed_manifest_sha256
        or artifact.get("metric_contract_sha256")
        != protocol.metric_contract_sha256
        or release._artifact_content_sha256(artifact)
        != artifact.get("artifact_content_sha256")
    ):
        raise ValueError(f"{source_id} protocol/content binding is invalid")

    _, frozen_record = resolve_frozen_dataset_root(gate1_lock=gate1_lock)
    metadata = artifact.get("metadata")
    if (
        artifact.get("schema_version") != "calibration-artifact-v1"
        or not isinstance(metadata, dict)
        or metadata.get("frozen_dataset") != frozen_record
        or not release._sealed_dataset_input_matches(
            manifest,
            manifest_path=manifest_path,
            expected_sha256=frozen_record["dataset_manifest_sha256"],
        )
    ):
        raise ValueError(f"{source_id} frozen-dataset binding is invalid")

    calibration_seeds = release._calibration_seed_tuple(protocol_dir)
    evaluation_index = release._calibration_evaluation_index(
        artifact,
        calibration_seeds=calibration_seeds,
    )
    methods = {method_id for method_id, _, _ in evaluation_index}
    if composition_source:
        expected_methods = COMPOSITION_METHODS
    else:
        expected_methods = (
            set(release._registry_config_hashes(protocol_dir))
            - COMPOSITION_METHODS
        )
    if methods != expected_methods:
        raise ValueError(
            f"{source_id} method scope differs from its locked registry scope"
        )
    release._validate_calibration_command(
        manifest,
        composition_source=composition_source,
    )
    release._verify_mechanical_selections(
        artifact,
        evaluation_index,
        policy=release._selection_policy(protocol_dir),
    )

    registry_hashes = release._registry_config_hashes(protocol_dir)
    pair_hashes: dict[tuple[str, str], set[str]] = {}
    for method_id, track_id, config_sha in evaluation_index:
        pair_hashes.setdefault((method_id, track_id), set()).add(config_sha)
    expected_tracks = set(release._selection_policy(protocol_dir).objectives)
    expected_pairs = {
        (method_id, track_id)
        for method_id in expected_methods
        for track_id in expected_tracks
    }
    if set(pair_hashes) != expected_pairs or any(
        hashes != registry_hashes[method_id]
        for (method_id, _), hashes in pair_hashes.items()
    ):
        raise ValueError(f"{source_id} does not contain every registered grid")

    return CalibrationSource(
        id=source_id,
        manifest=manifest,
        manifest_path=manifest_path,
        artifact=artifact,
        table_path=source,
        evaluation_index=evaluation_index,
    )


def _source_record(source: CalibrationSource) -> dict[str, Any]:
    manifest_payload = source.manifest_path.read_bytes()
    table_payload = source.table_path.read_bytes()
    return {
        "id": source.id,
        "run_id": source.manifest["run_id"],
        "manifest_path": _relative_to_repository(source.manifest_path),
        "manifest_sha256": hashlib.sha256(manifest_payload).hexdigest(),
        "table_path": source.table_path.relative_to(
            source.manifest_path.parent
        ).as_posix(),
        "table_sha256": hashlib.sha256(table_payload).hexdigest(),
        "artifact_content_sha256": source.artifact[
            "artifact_content_sha256"
        ],
    }


def _promotion_registry(
    sources: Sequence[CalibrationSource],
    *,
    calibration_protocol_sha256: str,
    gate1_binding: Mapping[str, str],
) -> dict[str, Any]:
    selections: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    observed_pairs: set[tuple[str, str]] = set()
    for source in sources:
        for row in source.artifact["selections"]:
            pair = (row["method_id"], row["track_id"])
            if pair in observed_pairs:
                raise ValueError(f"calibration sources overlap at {pair}")
            observed_pairs.add(pair)
            if row["status"] == "selected":
                selected_hash = row["selected_config_sha256"]
                evaluation = source.evaluation_index.get(
                    (row["method_id"], row["track_id"], selected_hash)
                )
                if (
                    evaluation is None
                    or evaluation.get("status") != "succeeded"
                    or evaluation.get("config") != row["selected_config"]
                ):
                    raise ValueError(f"selected calibration row is invalid at {pair}")
                selections.append(
                    {
                        "method_id": row["method_id"],
                        "track_id": row["track_id"],
                        "config": row["selected_config"],
                        "config_sha256": selected_hash,
                        "source_artifact_id": source.id,
                        "source_selection_sha256": row["selection_sha256"],
                    }
                )
            elif row["status"] == "no_feasible_candidate":
                if (
                    row["selected_config"] is not None
                    or row["selected_config_sha256"] is not None
                    or row["feasible_configurations"] != 0
                ):
                    raise ValueError(f"infeasible calibration row is invalid at {pair}")
                exclusions.append(
                    {
                        "method_id": row["method_id"],
                        "track_id": row["track_id"],
                        "status": "no_feasible_candidate",
                        "source_artifact_id": source.id,
                        "source_selection_sha256": row["selection_sha256"],
                    }
                )
            else:
                raise ValueError(f"unsupported calibration status at {pair}")

    expected_pairs = release._expected_method_track_pairs(DEFAULT_PROTOCOL_DIR)
    if observed_pairs != expected_pairs:
        raise ValueError("calibration sources do not cover the method/track registry")
    configuration_count = sum(
        int(source.artifact["configuration_evaluation_count"])
        for source in sources
    )
    seed_run_count = sum(
        int(source.artifact["seed_run_count"]) for source in sources
    )
    failure_count = sum(
        int(source.artifact["failed_configuration_count"])
        for source in sources
    )
    return {
        "schema_version": "selected-configs-v1",
        "calibration_protocol_sha256": calibration_protocol_sha256,
        "sources": [_source_record(source) for source in sources],
        "selections": sorted(
            selections,
            key=lambda row: (row["method_id"], row["track_id"]),
        ),
        "exclusions": sorted(
            exclusions,
            key=lambda row: (row["method_id"], row["track_id"]),
        ),
        "audit": {
            "expected_method_track_pairs": len(expected_pairs),
            "selected_method_track_pairs": len(selections),
            "no_feasible_method_track_pairs": len(exclusions),
            "complete_method_track_coverage": True,
            "all_calibration_failures_retained": True,
            "configuration_evaluation_count": configuration_count,
            "seed_run_count": seed_run_count,
            "failed_configuration_count": failure_count,
            "gate1_binding": dict(gate1_binding),
            "test_dataset_accessed": False,
        },
    }


def promote(
    composition_artifact: Path | str,
    baseline_artifact: Path | str,
    *,
    selected_configs: Path | str = DEFAULT_SELECTED_CONFIGS,
    gate2_lock: Path | str = DEFAULT_GATE2_LOCK,
    gate1_lock: Path | str = DEFAULT_GATE1_LOCK,
    protocol_dir: Path | str = DEFAULT_PROTOCOL_DIR,
) -> tuple[Path, Path]:
    """Validate, promote, transactionally self-check, and lock Gate 2."""

    protocol_path = Path(protocol_dir).resolve()
    if protocol_path != DEFAULT_PROTOCOL_DIR.resolve():
        raise ValueError("Gate-2 promotion must use the repository protocol directory")
    selected_path = Path(selected_configs).resolve()
    lock_path = Path(gate2_lock).resolve()
    gate1_path = Path(gate1_lock).resolve()
    if (
        selected_path != DEFAULT_SELECTED_CONFIGS.resolve()
        or lock_path != DEFAULT_GATE2_LOCK.resolve()
        or gate1_path != DEFAULT_GATE1_LOCK.resolve()
    ):
        raise ValueError("Gate-2 promotion targets must be the canonical paths")
    if selected_path.exists() or lock_path.exists():
        raise FileExistsError("refusing to replace an existing Gate-2 protocol lock")

    preselection_protocol = load_tuning_protocol(protocol_path)
    binding = _gate1_binding(gate1_path)
    sources = (
        _validate_source(
            Path(composition_artifact),
            source_id="exp15_composition_calibration",
            composition_source=True,
            protocol_dir=protocol_path,
            gate1_lock=gate1_path,
        ),
        _validate_source(
            Path(baseline_artifact),
            source_id="exp18_baseline_calibration",
            composition_source=False,
            protocol_dir=protocol_path,
            gate1_lock=gate1_path,
        ),
    )
    registry = _promotion_registry(
        sources,
        calibration_protocol_sha256=preselection_protocol.protocol_sha256,
        gate1_binding=binding,
    )
    lock_candidate = lock_path.with_name(f".{lock_path.name}.candidate")
    selected_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with selected_path.open("xb") as stream:
            stream.write(canonical_json_bytes(registry))
        final_protocol_sha = protocol_bundle_sha256(
            protocol_path / "seed_manifest.json",
            protocol_path / "metric_contract.json",
        )
        seed_manifest = json.loads(
            (protocol_path / "seed_manifest.json").read_text(encoding="utf-8")
        )
        lock = {
            "schema_version": 1,
            "gate": "Gate 2",
            "status": "locked",
            "locked_at_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "protocol and calibration selections frozen before test",
            "protocol_sha256": final_protocol_sha,
            "calibration_protocol_sha256": (
                preselection_protocol.protocol_sha256
            ),
            "gate1_binding": binding,
            "selected_configs": {
                "path": _relative_to_repository(selected_path),
                "sha256": file_sha256(selected_path),
                "source_count": len(registry["sources"]),
                "selection_count": len(registry["selections"]),
                "no_feasible_count": len(registry["exclusions"]),
            },
            "calibration_sources": registry["sources"],
            "test_release": {
                "status": "released_after_gate_2_lock",
                "seed_count": seed_manifest["expected_counts"]["test"],
                "dataset_reads_before_lock": 0,
                "evaluation_runs_started": 0,
            },
            "reopen_conditions": [
                "change to any protocol JSON member",
                "change to a promoted or excluded method/track record",
                "calibration source manifest/checksum validation failure",
                "Gate-1 data binding change",
            ],
        }
        with lock_candidate.open("xb") as stream:
            stream.write(canonical_json_bytes(lock))
        release.load_selected_configs(
            selected_path,
            gate2_lock=lock_candidate,
            protocol_dir=protocol_path,
            artifact_root=REPOSITORY_ROOT,
        )
        os.replace(lock_candidate, lock_path)
    except Exception:
        for provisional in (lock_candidate, selected_path):
            try:
                provisional.unlink()
            except FileNotFoundError:
                pass
        raise
    return selected_path, lock_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--composition-artifact", type=Path, required=True)
    parser.add_argument("--baseline-artifact", type=Path, required=True)
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    selected, lock = promote(
        args.composition_artifact,
        args.baseline_artifact,
    )
    print(
        json.dumps(
            {
                "selected_configs": str(selected),
                "gate2_lock": str(lock),
                "status": "locked",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["promote"]
