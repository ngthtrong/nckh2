"""Shared pre-Gate-2 experiment utilities.

This module deliberately exposes only the development and calibration views
returned by :mod:`demo.experiments.protocol`.  Evaluation-seed release remains
owned by the separate Gate-2 entry point.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Sequence

try:
    from .protocol import TuningProtocol, load_tuning_protocol
except ImportError:  # Direct script execution.
    from protocol import TuningProtocol, load_tuning_protocol  # type: ignore[no-redef]


PRE_GATE2_STAGES = ("development", "calibration")
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GATE1_LOCK = REPOSITORY_ROOT / "revision" / "gate1-lock.json"


def restricted_protocol_and_seeds(
    stages: Sequence[str],
) -> tuple[TuningProtocol, tuple[tuple[str, int], ...]]:
    """Return only locked development/calibration seeds.

    The returned public protocol object has no evaluation-seed attribute.
    Duplicate stages are rejected so a caller cannot silently double-weight a
    split in a paired analysis.
    """

    requested = tuple(str(stage) for stage in stages)
    if not requested:
        raise ValueError("at least one pre-Gate-2 stage is required")
    if len(set(requested)) != len(requested):
        raise ValueError("pre-Gate-2 stages must be unique")
    invalid = sorted(set(requested) - set(PRE_GATE2_STAGES))
    if invalid:
        raise ValueError(
            "only development/calibration are available before Gate 2: "
            + ", ".join(invalid)
        )
    protocol = load_tuning_protocol()
    selected = tuple(
        (stage, int(seed))
        for stage in requested
        for seed in protocol.seeds_for(stage)  # type: ignore[arg-type]
    )
    return protocol, selected


def protocol_record(
    protocol: TuningProtocol,
    selected: Sequence[tuple[str, int]],
) -> dict[str, object]:
    """Machine-readable provenance without exposing withheld seed values."""

    counts = {
        stage: sum(1 for selected_stage, _ in selected if selected_stage == stage)
        for stage in PRE_GATE2_STAGES
        if any(selected_stage == stage for selected_stage, _ in selected)
    }
    return {
        "access_scope": "development_and_calibration_only",
        "selected_stages": list(counts),
        "seed_counts": counts,
        "seed_manifest_sha256": protocol.seed_manifest_sha256,
        "metric_contract_sha256": protocol.metric_contract_sha256,
        "protocol_sha256": protocol.protocol_sha256,
        "evaluation_release_module_imported": False,
    }


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_frozen_dataset_root(
    dataset_root: Path | str | None = None,
    *,
    gate1_lock: Path | str = DEFAULT_GATE1_LOCK,
) -> tuple[Path, dict[str, object]]:
    """Bind a requested dataset root to the accepted Gate-1 artifact.

    Only the lock, outer run manifest, and bundle-manifest bytes are inspected
    here.  Individual split files are opened later by ``load_tuning_dataset``,
    which constructs exactly one allowed development/calibration path and
    never traverses another split directory.
    """

    lock_path = Path(gate1_lock).resolve()
    try:
        lock: Any = json.loads(lock_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid Gate-1 lock: {lock_path}") from exc
    if (
        not isinstance(lock, dict)
        or lock.get("gate") != "Gate 1"
        or lock.get("status") != "locked"
        or not isinstance(lock.get("accepted_run"), dict)
        or not isinstance(lock.get("data_contract"), dict)
    ):
        raise ValueError("a locked Gate-1 method/data record is required")

    accepted = lock["accepted_run"]
    data_contract = lock["data_contract"]
    manifest_relative = accepted.get("manifest")
    if not isinstance(manifest_relative, str) or not manifest_relative:
        raise ValueError("Gate-1 lock has no accepted run manifest")
    run_manifest = (REPOSITORY_ROOT / manifest_relative).resolve()
    if _file_sha256(run_manifest) != accepted.get("manifest_sha256"):
        raise ValueError("accepted Gate-1 run manifest checksum mismatch")
    expected_root = (run_manifest.parent / "work" / "datasets").resolve()
    requested_root = (
        expected_root if dataset_root is None else Path(dataset_root).resolve()
    )
    if requested_root != expected_root:
        raise ValueError(
            "dataset root is not the bundle bound by the accepted Gate-1 lock"
        )
    bundle_manifest = requested_root / "manifest.json"
    bundle_manifest_sha256 = _file_sha256(bundle_manifest)
    if bundle_manifest_sha256 != data_contract.get("dataset_manifest_sha256"):
        raise ValueError("frozen dataset manifest checksum mismatch")
    return requested_root, {
        "gate1_lock": str(lock_path.relative_to(REPOSITORY_ROOT)),
        "gate1_lock_sha256": _file_sha256(lock_path),
        "accepted_run_id": accepted.get("run_id"),
        "accepted_run_manifest": str(run_manifest.relative_to(REPOSITORY_ROOT)),
        "accepted_run_manifest_sha256": accepted.get("manifest_sha256"),
        "dataset_root": str(requested_root.relative_to(REPOSITORY_ROOT)),
        "dataset_manifest_sha256": bundle_manifest_sha256,
    }


def load_frozen_tuning_views(
    dataset_root: Path | str,
    *,
    stage: str,
    seed: int,
    tuning_protocol: TuningProtocol,
    gate1_lock: Path | str = DEFAULT_GATE1_LOCK,
) -> tuple[object, dict[str, Any]]:
    """Load inference and evaluator views from one exact frozen split file."""

    if stage not in PRE_GATE2_STAGES:
        raise ValueError("only development/calibration frozen views are available")
    # Import is local to keep this small artifact/protocol helper acyclic.
    from demo.experiments.calibration import load_tuning_dataset

    tuning_dataset = load_tuning_dataset(
        dataset_root,
        stage=stage,  # type: ignore[arg-type]
        seed=int(seed),
        tuning_protocol=tuning_protocol,
        calibration_labels=True,
        gate1_lock=gate1_lock,
    )
    source = Path(dataset_root) / stage / f"seed_{int(seed)}.json"
    payload = source.read_bytes()
    if hashlib.sha256(payload).hexdigest() != tuning_dataset.source_sha256:
        raise ValueError("frozen source changed between inference/evaluator reads")
    try:
        full: Any = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid frozen dataset JSON: {source}") from exc
    if not isinstance(full, dict):
        raise ValueError(f"frozen dataset must be an object: {source}")
    if full.get("seed") != int(seed) or full.get("split") != stage:
        raise ValueError(f"frozen dataset identity does not match {stage}/{seed}")
    report_ids = tuple(str(report["event_id"]) for report in full["reports"])
    inference_ids = tuple(str(event.event_id) for event in tuning_dataset.events)
    if report_ids != inference_ids:
        raise ValueError("frozen evaluator and inference views are misaligned")
    if tuning_dataset.ground_truth is None or not tuning_dataset.incidents:
        raise ValueError("frozen evaluator view is incomplete")
    return tuning_dataset, full


def canonical_json_bytes(value: object) -> bytes:
    """Deterministic JSON encoding used for immutable experiment outputs."""

    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def default_table_path(filename: str) -> Path:
    """Resolve an artifact table path without falling back to current results."""

    root = os.environ.get("DEMO_TABLES_DIR")
    if not root:
        raise RuntimeError(
            "DEMO_TABLES_DIR is required; run through the immutable artifact runner "
            "or pass --output explicitly"
        )
    return Path(root) / filename


def write_exclusive_json(path: Path | str, value: object) -> Path:
    """Write one result exactly once and refuse manual/result replacement."""

    destination = Path(path)
    artifact_tables = os.environ.get("DEMO_TABLES_DIR")
    if artifact_tables:
        resolved_tables = Path(artifact_tables).resolve()
        resolved_destination = destination.resolve()
        if (
            resolved_destination != resolved_tables
            and resolved_tables not in resolved_destination.parents
        ):
            raise ValueError(
                "candidate result output must remain below DEMO_TABLES_DIR"
            )
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json_bytes(value)
    with destination.open("xb") as stream:
        stream.write(payload)
    return destination


__all__ = [
    "PRE_GATE2_STAGES",
    "DEFAULT_GATE1_LOCK",
    "canonical_json_bytes",
    "default_table_path",
    "load_frozen_tuning_views",
    "protocol_record",
    "resolve_frozen_dataset_root",
    "restricted_protocol_and_seeds",
    "write_exclusive_json",
]
