"""Gate-2-only access to frozen evaluation data and selected configurations.

This module is deliberately separate from the development/calibration engine.
It releases no dataset path or seed until :func:`load_locked_test_seeds`
accepts the current Gate-2 lock.  Once released, each dataset is authenticated
through both the accepted Gate-1 run manifest and its frozen dataset manifest.

Selected configurations are likewise traced back to calibration tables in
sealed candidate runs.  The selected-config registry itself is a member of the
Gate-2 protocol bundle, so it records the *calibration* protocol hash rather
than attempting to contain the circular hash of the bundle that contains it.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np


DEMO_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = DEMO_ROOT.parent
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from data.schema import validate_candidate_dataset  # noqa: E402
from pipeline.attributes import Event, compute_confidence  # noqa: E402
from pipeline.config import DEFAULT_CONFIG  # noqa: E402

try:
    from .artifacts import ArtifactError, validate_manifest
    from .evaluation_protocol import load_locked_test_seeds
    from .protocol import DEFAULT_PROTOCOL_DIR, ProtocolError
except ImportError:  # Direct use with demo/experiments on sys.path.
    from artifacts import ArtifactError, validate_manifest  # type: ignore[no-redef]
    from evaluation_protocol import (  # type: ignore[no-redef]
        load_locked_test_seeds,
    )
    from protocol import (  # type: ignore[no-redef]
        DEFAULT_PROTOCOL_DIR,
        ProtocolError,
    )


DEFAULT_GATE1_LOCK = REPOSITORY_ROOT / "revision" / "gate1-lock.json"
DEFAULT_GATE2_LOCK = REPOSITORY_ROOT / "revision" / "gate2-lock.json"
DEFAULT_SELECTED_CONFIGS = DEFAULT_PROTOCOL_DIR / "selected_configs.json"
SELECTED_CONFIGS_NAME = "selected_configs.json"
SHA256_LENGTH = 64
COMPOSITION_METHODS = frozenset(
    {
        "product_louvain",
        "additive_louvain",
        "multiple_similarity_louvain",
    }
)
MATCHED_COMPOSITION_METHODS = frozenset(
    {
        "additive_louvain",
        "multiple_similarity_louvain",
    }
)
SAME_REPRESENTATION_METHODS = frozenset(
    {
        "product_leiden",
        "product_spectral",
    }
)


class EvaluationDataError(ProtocolError):
    """Raised when an evaluation-only identity or integrity check fails."""


@dataclass(frozen=True)
class EvaluatorReport:
    """Truth attached to one report, kept separate from inference events."""

    event_id: str
    incident_id: str | None
    gt_cluster: int
    scenario_family: str
    duplicate_kind: str
    duplicate_family_id: str | None
    coverage_n: float | None
    coverage_v: float | None
    population_member_indices: tuple[int, ...]
    vulnerable_member_indices: tuple[int, ...]
    is_fake: bool
    adversary: str | None


@dataclass(frozen=True)
class EvaluationDataset:
    """Authenticated inference and evaluator views for one locked test seed."""

    seed: int
    events: tuple[Event, ...]
    ground_truth: tuple[int, ...]
    fake_truth: tuple[bool, ...]
    evaluator_reports: tuple[EvaluatorReport, ...]
    incidents: tuple[Mapping[str, Any], ...]
    quality: Mapping[str, Any]
    source_sha256: str
    dataset_manifest_sha256: str
    gate1_run_id: str
    gate1_manifest_sha256: str


@dataclass(frozen=True)
class SelectedConfig:
    """One configuration promoted mechanically from a calibration artifact."""

    method_id: str
    track_id: str
    config: Mapping[str, Any]
    config_sha256: str
    source_artifact_id: str
    source_selection_sha256: str


@dataclass(frozen=True)
class SelectedConfigExclusion:
    """One method/track pair proven infeasible by sealed calibration."""

    method_id: str
    track_id: str
    status: str
    source_artifact_id: str
    source_selection_sha256: str


@dataclass(frozen=True)
class SelectedConfigSource:
    """Identity of one sealed calibration table used by the selection file."""

    id: str
    run_id: str
    manifest_path: str
    manifest_sha256: str
    table_path: str
    table_sha256: str
    artifact_content_sha256: str


@dataclass(frozen=True)
class SelectedConfigBundle:
    """Strict Gate-2 view of all selected method/track configurations."""

    calibration_protocol_sha256: str
    sources: tuple[SelectedConfigSource, ...]
    selections: tuple[SelectedConfig, ...]
    exclusions: tuple[SelectedConfigExclusion, ...]

    def selection_for(self, method_id: str, track_id: str) -> SelectedConfig:
        matches = [
            row
            for row in self.selections
            if row.method_id == method_id and row.track_id == track_id
        ]
        if len(matches) != 1:
            excluded = [
                row
                for row in self.exclusions
                if row.method_id == method_id and row.track_id == track_id
            ]
            if len(excluded) == 1:
                raise EvaluationDataError(
                    f"{method_id}/{track_id} has no feasible calibration candidate"
                )
            raise EvaluationDataError(
                f"expected one selected config for {method_id}/{track_id}"
            )
        return matches[0]

    def exclusion_for(
        self,
        method_id: str,
        track_id: str,
    ) -> SelectedConfigExclusion:
        matches = [
            row
            for row in self.exclusions
            if row.method_id == method_id and row.track_id == track_id
        ]
        if len(matches) != 1:
            raise EvaluationDataError(
                f"expected one infeasible calibration record for "
                f"{method_id}/{track_id}"
            )
        return matches[0]


@dataclass(frozen=True)
class _SelectionPolicy:
    objectives: Mapping[str, tuple[str, str]]
    common_constraints: tuple[tuple[str, str, float], ...]
    graph_constraints: tuple[tuple[str, str, float], ...]
    matched_fraction_tolerance: float
    matched_degree_relative_tolerance: float


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != SHA256_LENGTH:
        return False
    return all(character in "0123456789abcdef" for character in value)


def _json_object(payload: bytes, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvaluationDataError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise EvaluationDataError(f"{label} must contain a JSON object")
    return value


def _read_bytes(path: Path, *, label: str) -> bytes:
    try:
        return path.read_bytes()
    except (FileNotFoundError, OSError) as exc:
        raise EvaluationDataError(f"{label} is unavailable: {path}") from exc


def _safe_relative_path(
    root: Path,
    value: Any,
    *,
    label: str,
) -> Path:
    if not isinstance(value, str) or not value:
        raise EvaluationDataError(f"{label} must be a non-empty relative path")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise EvaluationDataError(f"{label} must remain within its artifact root")
    resolved_root = root.resolve()
    resolved = (resolved_root / relative).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise EvaluationDataError(f"{label} escapes its artifact root")
    return resolved


def _freeze_json(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType(
            {str(key): _freeze_json(nested) for key, nested in value.items()}
        )
    if isinstance(value, list):
        return tuple(_freeze_json(nested) for nested in value)
    return value


def _canonical_mapping_sha256(value: Mapping[str, Any]) -> str:
    try:
        encoded = json.dumps(
            dict(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise EvaluationDataError("configuration is not finite canonical JSON") from exc
    return _sha256(encoded)


def _gate2_data_binding(
    gate2_lock_path: Path,
    protocol_dir: Path,
) -> tuple[tuple[int, ...], Mapping[str, str]]:
    """Authenticate Gate 2 and return its exact Gate-1 data binding."""

    before = _read_bytes(gate2_lock_path, label="Gate-2 lock")
    try:
        released = load_locked_test_seeds(gate2_lock_path, protocol_dir)
    except ProtocolError as exc:
        raise EvaluationDataError(str(exc)) from exc
    after = _read_bytes(gate2_lock_path, label="Gate-2 lock")
    if before != after:
        raise EvaluationDataError("Gate-2 lock changed during authorization")
    lock = _json_object(after, label="Gate-2 lock")
    binding = lock.get("gate1_binding")
    required = {
        "gate1_lock_sha256",
        "accepted_run_manifest_sha256",
        "dataset_manifest_sha256",
    }
    if (
        not isinstance(binding, dict)
        or set(binding) != required
        or any(not _is_sha256(binding.get(field)) for field in required)
    ):
        raise EvaluationDataError(
            "Gate-2 lock lacks an exact Gate-1 dataset binding"
        )
    return released, binding


def _gate1_binding(
    dataset_root: Path,
    *,
    gate1_lock_path: Path,
    repository_root: Path,
    gate2_binding: Mapping[str, str],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    Mapping[str, Any],
    str,
    str,
    str,
    Path,
]:
    """Authenticate the accepted run, dataset manifest, and exact root."""

    lock_payload = _read_bytes(gate1_lock_path, label="Gate-1 lock")
    if _sha256(lock_payload) != gate2_binding["gate1_lock_sha256"]:
        raise EvaluationDataError("Gate-1 lock differs from the Gate-2 binding")
    lock = _json_object(lock_payload, label="Gate-1 lock")
    accepted = lock.get("accepted_run")
    data_contract = lock.get("data_contract")
    gate1_protocol = lock.get("protocol")
    if (
        lock.get("schema_version") != 1
        or lock.get("gate") != "Gate 1"
        or lock.get("status") != "locked"
        or not isinstance(accepted, dict)
        or not isinstance(data_contract, dict)
        or not isinstance(gate1_protocol, dict)
        or not isinstance(accepted.get("run_id"), str)
        or accepted.get("status") != "succeeded"
        or accepted.get("exit_code") != 0
        or accepted.get("manifest_validation") != "pass"
        or not _is_sha256(accepted.get("manifest_sha256"))
        or not _is_sha256(data_contract.get("dataset_manifest_sha256"))
        or not isinstance(data_contract.get("dataset_schema_version"), str)
        or not isinstance(data_contract.get("generator_version"), str)
        or not _is_sha256(data_contract.get("generator_sha256"))
        or not _is_sha256(data_contract.get("schema_sha256"))
        or not _is_sha256(data_contract.get("data_spec_sha256"))
        or not _is_sha256(gate1_protocol.get("seed_manifest_sha256"))
        or isinstance(data_contract.get("n_datasets"), bool)
        or not isinstance(data_contract.get("n_datasets"), int)
        or data_contract["n_datasets"] < 1
    ):
        raise EvaluationDataError("Gate-1 data contract is not fully locked")

    accepted_manifest_path = _safe_relative_path(
        repository_root,
        accepted.get("manifest"),
        label="Gate-1 accepted manifest path",
    )
    if accepted_manifest_path.name != "manifest.json":
        raise EvaluationDataError("Gate-1 accepted manifest path is malformed")
    accepted_manifest_payload = _read_bytes(
        accepted_manifest_path,
        label="Gate-1 accepted run manifest",
    )
    accepted_manifest_sha = _sha256(accepted_manifest_payload)
    if (
        accepted_manifest_sha != accepted["manifest_sha256"]
        or accepted_manifest_sha
        != gate2_binding["accepted_run_manifest_sha256"]
    ):
        raise EvaluationDataError("Gate-1 accepted run manifest checksum mismatch")
    accepted_manifest = _json_object(
        accepted_manifest_payload,
        label="Gate-1 accepted run manifest",
    )
    checksums = accepted_manifest.get("checksums")
    if (
        accepted_manifest.get("schema_version") != 1
        or accepted_manifest.get("run_id") != accepted["run_id"]
        or accepted_manifest.get("status") != "succeeded"
        or accepted_manifest.get("exit_code") != 0
        or not isinstance(checksums, dict)
    ):
        raise EvaluationDataError("Gate-1 accepted run identity/status mismatch")

    expected_root = (
        accepted_manifest_path.parent / "work" / "datasets"
    ).resolve()
    if dataset_root.resolve() != expected_root:
        raise EvaluationDataError(
            "dataset root is not the accepted Gate-1 run dataset root"
        )
    dataset_manifest_path = expected_root / "manifest.json"
    dataset_manifest_payload = _read_bytes(
        dataset_manifest_path,
        label="frozen dataset manifest",
    )
    dataset_manifest_sha = _sha256(dataset_manifest_payload)
    locked_dataset_manifest_sha = data_contract["dataset_manifest_sha256"]
    if (
        dataset_manifest_sha != locked_dataset_manifest_sha
        or dataset_manifest_sha != gate2_binding["dataset_manifest_sha256"]
        or checksums.get("work/datasets/manifest.json")
        != locked_dataset_manifest_sha
    ):
        raise EvaluationDataError(
            "frozen dataset manifest does not match both Gate-1 bindings"
        )
    dataset_manifest = _json_object(
        dataset_manifest_payload,
        label="frozen dataset manifest",
    )
    return (
        accepted_manifest,
        dataset_manifest,
        data_contract,
        gate1_protocol["seed_manifest_sha256"],
        accepted_manifest_sha,
        dataset_manifest_sha,
        expected_root,
    )


def _validate_dataset_manifest(
    manifest: Mapping[str, Any],
    *,
    data_contract: Mapping[str, Any],
    gate1_seed_manifest_sha256: str,
    released_test_seeds: Sequence[int],
    accepted_checksums: Mapping[str, Any],
) -> dict[tuple[str, int], Mapping[str, Any]]:
    expected_fields = {
        "dataset_schema_version": "dataset_schema_version",
        "generator_version": "generator_version",
        "generator_sha256": "generator_sha256",
        "schema_sha256": "schema_sha256",
        "data_spec_sha256": "data_spec_sha256",
    }
    if manifest.get("schema_version") != "candidate-dataset-manifest-v2":
        raise EvaluationDataError("unsupported frozen dataset-manifest schema")
    for manifest_field, lock_field in expected_fields.items():
        if manifest.get(manifest_field) != data_contract.get(lock_field):
            raise EvaluationDataError(
                f"dataset manifest {manifest_field} differs from Gate-1 lock"
            )
    if manifest.get("seed_manifest_sha256") != gate1_seed_manifest_sha256:
        raise EvaluationDataError(
            "dataset seed-manifest binding differs from Gate-1 lock"
        )

    seed_mapping = manifest.get("seed_mapping")
    entries = manifest.get("entries")
    if not isinstance(seed_mapping, dict) or not isinstance(entries, list):
        raise EvaluationDataError("dataset manifest mapping/entries are malformed")
    if set(seed_mapping) != {"development", "calibration", "test"}:
        raise EvaluationDataError("dataset manifest seed mapping is incomplete")
    for split, raw_seeds in seed_mapping.items():
        if (
            not isinstance(raw_seeds, list)
            or any(
                isinstance(seed, bool) or not isinstance(seed, int)
                for seed in raw_seeds
            )
            or len(raw_seeds) != len(set(raw_seeds))
        ):
            raise EvaluationDataError(
                f"dataset manifest seed mapping is malformed for {split}"
            )
    if tuple(seed_mapping.get("test", ())) != tuple(released_test_seeds):
        raise EvaluationDataError(
            "dataset manifest test mapping differs from the Gate-2 release"
        )
    if data_contract.get("n_datasets") != len(entries):
        raise EvaluationDataError("dataset manifest entry count differs from Gate-1")

    by_identity: dict[tuple[str, int], Mapping[str, Any]] = {}
    observed_by_split: dict[str, list[int]] = {
        "development": [],
        "calibration": [],
        "test": [],
    }
    seen_paths: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise EvaluationDataError("dataset manifest entry must be an object")
        split = entry.get("split")
        seed = entry.get("seed")
        path = entry.get("path")
        source_sha = entry.get("sha256")
        if (
            split not in observed_by_split
            or isinstance(seed, bool)
            or not isinstance(seed, int)
            or path != f"{split}/seed_{seed}.json"
            or not _is_sha256(source_sha)
            or entry.get("quality_status") != "pass"
        ):
            raise EvaluationDataError("dataset manifest entry identity is malformed")
        identity = (split, seed)
        if identity in by_identity or path in seen_paths:
            raise EvaluationDataError("dataset manifest contains a duplicate entry")
        sealed_path = f"work/datasets/{path}"
        if accepted_checksums.get(sealed_path) != source_sha:
            raise EvaluationDataError(
                f"dataset entry {path} differs from the sealed run checksum"
            )
        by_identity[identity] = entry
        seen_paths.add(path)
        observed_by_split[split].append(seed)

    for split, raw_seeds in seed_mapping.items():
        if sorted(observed_by_split[split]) != sorted(raw_seeds):
            raise EvaluationDataError(
                f"dataset entries do not match seed mapping for {split}"
            )
    return by_identity


def _event_from_report(report: Mapping[str, Any]) -> Event:
    return Event(
        event_id=str(report["event_id"]),
        lat=float(report["lat"]),
        lng=float(report["lng"]),
        created_at=datetime.fromisoformat(str(report["created_at"])),
        flood=float(report["flood"]),
        urgency=float(report["urgency"]),
        n_trapped=int(report["n_trapped"]),
        vulnerability=float(report["vulnerability"]),
        has_image=bool(report["has_image"]),
        source_type=str(report["source_type"]),
        province=str(report["province"]),
        note=str(report["note"]),
        missing_fields=tuple(report["missing_fields"]),
        # Evaluator truth must never be attached to the inference object.
        gt_cluster=-1,
        is_fake=False,
    )


def _optional_int_tuple(value: Any, *, field: str) -> tuple[int, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(
        isinstance(item, bool) or not isinstance(item, int) for item in value
    ):
        raise EvaluationDataError(f"evaluator field {field} is malformed")
    return tuple(value)


def _evaluator_report(report: Mapping[str, Any]) -> EvaluatorReport:
    evaluation = report.get("evaluation_only")
    if not isinstance(evaluation, dict):
        raise EvaluationDataError("validated report has no evaluator view")
    incident_id = evaluation.get("incident_id")
    raw_label = evaluation.get("gt_cluster")
    duplicate_family = evaluation.get("duplicate_family_id")
    adversary = evaluation.get("adversary")
    for name, value in (
        ("incident_id", incident_id),
        ("duplicate_family_id", duplicate_family),
        ("adversary", adversary),
    ):
        if value is not None and not isinstance(value, str):
            raise EvaluationDataError(f"evaluator field {name} is malformed")
    if raw_label is not None and (
        isinstance(raw_label, bool) or not isinstance(raw_label, int)
    ):
        raise EvaluationDataError("evaluator ground-truth label is malformed")
    if not isinstance(evaluation.get("is_fake"), bool):
        raise EvaluationDataError("evaluator fake label is malformed")

    def optional_float(field: str) -> float | None:
        value = evaluation.get(field)
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise EvaluationDataError(f"evaluator field {field} is malformed")
        result = float(value)
        if not math.isfinite(result):
            raise EvaluationDataError(f"evaluator field {field} is non-finite")
        return result

    return EvaluatorReport(
        event_id=str(report["event_id"]),
        incident_id=incident_id,
        gt_cluster=-1 if raw_label is None else raw_label,
        scenario_family=str(evaluation["scenario_family"]),
        duplicate_kind=str(evaluation["duplicate_kind"]),
        duplicate_family_id=duplicate_family,
        coverage_n=optional_float("coverage_n"),
        coverage_v=optional_float("coverage_v"),
        population_member_indices=_optional_int_tuple(
            evaluation.get("population_member_indices"),
            field="population_member_indices",
        ),
        vulnerable_member_indices=_optional_int_tuple(
            evaluation.get("vulnerable_member_indices"),
            field="vulnerable_member_indices",
        ),
        is_fake=evaluation["is_fake"],
        adversary=adversary,
    )


def load_evaluation_dataset(
    dataset_root: Path | str,
    *,
    seed: int,
    gate2_lock: Path | str = DEFAULT_GATE2_LOCK,
    gate1_lock: Path | str = DEFAULT_GATE1_LOCK,
    protocol_dir: Path | str = DEFAULT_PROTOCOL_DIR,
    repository_root: Path | str | None = None,
) -> EvaluationDataset:
    """Load one authenticated test seed after exact Gate-2 release.

    Gate-2 authorization is intentionally the first filesystem read performed
    by this function.  A missing/mismatched lock or an unregistered seed fails
    before either the Gate-1 artifact or any dataset file is opened.
    """

    released, gate2_binding = _gate2_data_binding(
        Path(gate2_lock),
        Path(protocol_dir),
    )
    if isinstance(seed, bool) or not isinstance(seed, int) or seed not in released:
        raise EvaluationDataError(
            f"seed {seed!r} is not in the locked Gate-2 test release"
        )

    gate1_path = Path(gate1_lock)
    root = (
        gate1_path.resolve().parent.parent
        if repository_root is None
        else Path(repository_root).resolve()
    )
    (
        accepted_manifest,
        dataset_manifest,
        data_contract,
        gate1_seed_manifest_sha,
        accepted_manifest_sha,
        dataset_manifest_sha,
        authenticated_root,
    ) = _gate1_binding(
        Path(dataset_root),
        gate1_lock_path=gate1_path,
        repository_root=root,
        gate2_binding=gate2_binding,
    )
    entries = _validate_dataset_manifest(
        dataset_manifest,
        data_contract=data_contract,
        gate1_seed_manifest_sha256=gate1_seed_manifest_sha,
        released_test_seeds=released,
        accepted_checksums=accepted_manifest["checksums"],
    )
    entry = entries.get(("test", seed))
    if entry is None:
        raise EvaluationDataError(f"frozen dataset has no test entry for seed {seed}")

    source = authenticated_root / str(entry["path"])
    payload = _read_bytes(source, label=f"frozen test dataset {seed}")
    source_sha = _sha256(payload)
    if source_sha != entry["sha256"]:
        raise EvaluationDataError(f"frozen test dataset checksum mismatch for {seed}")
    data = _json_object(payload, label=f"frozen test dataset {seed}")
    try:
        quality = validate_candidate_dataset(
            data,
            expected_seed=seed,
            expected_split="test",
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise EvaluationDataError(
            f"frozen test dataset schema validation failed for {seed}: {exc}"
        ) from exc

    reports = data["reports"]
    try:
        events = [_event_from_report(report) for report in reports]
        evaluator_reports = tuple(_evaluator_report(report) for report in reports)
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, EvaluationDataError):
            raise
        raise EvaluationDataError(
            f"validated test dataset view construction failed for {seed}"
        ) from exc
    compute_confidence(events, DEFAULT_CONFIG.confidence)
    gate1_run_id = str(accepted_manifest["run_id"])
    return EvaluationDataset(
        seed=seed,
        events=tuple(events),
        ground_truth=tuple(row.gt_cluster for row in evaluator_reports),
        fake_truth=tuple(row.is_fake for row in evaluator_reports),
        evaluator_reports=evaluator_reports,
        incidents=tuple(_freeze_json(row) for row in data["incidents"]),
        quality=_freeze_json(quality),
        source_sha256=source_sha,
        dataset_manifest_sha256=dataset_manifest_sha,
        gate1_run_id=gate1_run_id,
        gate1_manifest_sha256=accepted_manifest_sha,
    )


def build_evaluator_analysis_view(
    dataset: EvaluationDataset,
) -> dict[str, Any]:
    """Reconstruct the evaluator-only join used by post-Gate-2 analyses.

    Prediction code must continue to receive only ``dataset.events``.  This
    helper deliberately returns no observable report attributes: it supplies
    only stable report identities, evaluator annotations, and latent incident
    records after prediction has already been produced.
    """

    if len(dataset.events) != len(dataset.evaluator_reports):
        raise EvaluationDataError(
            "evaluation events and evaluator reports are not aligned"
        )
    event_ids = [str(event.event_id) for event in dataset.events]
    report_ids = [report.event_id for report in dataset.evaluator_reports]
    if (
        len(event_ids) != len(set(event_ids))
        or len(report_ids) != len(set(report_ids))
        or event_ids != report_ids
    ):
        raise EvaluationDataError(
            "evaluation event identities and evaluator reports are not aligned"
        )

    def thaw(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {str(key): thaw(nested) for key, nested in value.items()}
        if isinstance(value, tuple):
            return [thaw(nested) for nested in value]
        return value

    reports: list[dict[str, Any]] = []
    for report in dataset.evaluator_reports:
        reports.append(
            {
                "event_id": report.event_id,
                "evaluation_only": {
                    "incident_id": report.incident_id,
                    "gt_cluster": (
                        None if report.gt_cluster < 0 else report.gt_cluster
                    ),
                    "scenario_family": report.scenario_family,
                    "duplicate_kind": report.duplicate_kind,
                    "duplicate_family_id": report.duplicate_family_id,
                    "coverage_n": report.coverage_n,
                    "coverage_v": report.coverage_v,
                    "population_member_indices": list(
                        report.population_member_indices
                    ),
                    "vulnerable_member_indices": list(
                        report.vulnerable_member_indices
                    ),
                    "is_fake": report.is_fake,
                    "adversary": report.adversary,
                },
            }
        )
    return {
        "reports": reports,
        "incidents": [thaw(incident) for incident in dataset.incidents],
    }


def _artifact_content_sha256(artifact: Mapping[str, Any]) -> str:
    content = dict(artifact)
    recorded = content.pop("artifact_content_sha256", None)
    if not _is_sha256(recorded):
        raise EvaluationDataError(
            "calibration artifact has no valid artifact_content_sha256"
        )
    observed = _canonical_mapping_sha256(content)
    if observed != recorded:
        raise EvaluationDataError("calibration artifact content hash mismatch")
    return recorded


def _selection_sha256(selection: Mapping[str, Any]) -> str:
    required = (
        "method_id",
        "track_id",
        "objective",
        "direction",
        "selected_config_sha256",
    )
    if any(field not in selection for field in required):
        raise EvaluationDataError("calibration selection identity is incomplete")
    identity = {field: selection[field] for field in required}
    if (
        not isinstance(identity["method_id"], str)
        or not identity["method_id"]
        or not isinstance(identity["track_id"], str)
        or not identity["track_id"]
        or not isinstance(identity["objective"], str)
        or not identity["objective"]
        or identity["direction"] not in {"higher", "lower"}
        or (
            identity["selected_config_sha256"] is not None
            and not _is_sha256(identity["selected_config_sha256"])
        )
    ):
        raise EvaluationDataError("calibration selection identity is malformed")
    return _canonical_mapping_sha256(identity)


def _calibration_evaluation_index(
    artifact: Mapping[str, Any],
    *,
    calibration_seeds: Sequence[int],
) -> dict[tuple[str, str, str], Mapping[str, Any]]:
    """Validate retained candidate identities and aggregate audit counts."""

    evaluations = artifact.get("evaluations")
    metadata = artifact.get("metadata")
    if (
        not isinstance(evaluations, list)
        or not isinstance(metadata, dict)
        or metadata.get("stage") != "calibration"
        or metadata.get("complete_seed_set") is not True
        or metadata.get("seed_limit") is not None
    ):
        raise EvaluationDataError(
            "selected configs require a complete calibration artifact"
        )
    index: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    configuration_count = 0
    seed_run_count = 0
    failed_count = 0
    for row in evaluations:
        if not isinstance(row, dict):
            raise EvaluationDataError("calibration evaluation row is malformed")
        method_id = row.get("method_id")
        track_id = row.get("track_id")
        config = row.get("config")
        config_sha = row.get("config_sha256")
        status = row.get("status")
        row_config_count = row.get("configuration_evaluation_count")
        row_seed_count = row.get("seed_run_count")
        failures = row.get("failures")
        seed_metrics = row.get("seed_metrics")
        if (
            not isinstance(method_id, str)
            or not method_id
            or not isinstance(track_id, str)
            or not track_id
            or not isinstance(config, dict)
            or not _is_sha256(config_sha)
            or _canonical_mapping_sha256(config) != config_sha
            or row.get("stage") != "calibration"
            or status not in {"succeeded", "failed"}
            or row_config_count != 1
            or isinstance(row_seed_count, bool)
            or not isinstance(row_seed_count, int)
            or row_seed_count < 1
            or not isinstance(failures, list)
            or not isinstance(seed_metrics, list)
            or (status == "failed") != bool(failures)
        ):
            raise EvaluationDataError(
                "calibration evaluation identity/count is malformed"
            )
        metric_seeds: list[int] = []
        for metric_row in seed_metrics:
            if not isinstance(metric_row, dict):
                raise EvaluationDataError("calibration seed metric row is malformed")
            raw_seed = metric_row.get("seed")
            if (
                isinstance(raw_seed, bool)
                or not isinstance(raw_seed, (int, float))
                or not math.isfinite(float(raw_seed))
                or not float(raw_seed).is_integer()
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(float(value))
                    for name, value in metric_row.items()
                    if name != "seed"
                )
            ):
                raise EvaluationDataError("calibration seed metric row is malformed")
            metric_seeds.append(int(raw_seed))
        failure_seeds: list[int] = []
        for failure in failures:
            if (
                not isinstance(failure, dict)
                or isinstance(failure.get("seed"), bool)
                or not isinstance(failure.get("seed"), int)
            ):
                raise EvaluationDataError("calibration seed failure row is malformed")
            failure_seeds.append(failure["seed"])
        covered = metric_seeds + failure_seeds
        if (
            row_seed_count != len(calibration_seeds)
            or len(covered) != len(set(covered))
            or set(covered) != set(calibration_seeds)
        ):
            raise EvaluationDataError(
                "calibration evaluation does not cover the exact locked seed set"
            )
        aggregate = row.get("aggregate_metrics")
        expected_aggregate = _aggregate_seed_metrics(seed_metrics)
        if not isinstance(aggregate, dict) or aggregate != expected_aggregate:
            raise EvaluationDataError(
                "calibration aggregate metrics are not mechanically reproducible"
            )
        identity = (method_id, track_id, config_sha)
        if identity in index:
            raise EvaluationDataError("calibration artifact repeats an evaluation")
        index[identity] = row
        configuration_count += row_config_count
        seed_run_count += row_seed_count
        failed_count += int(status == "failed")
    if (
        artifact.get("configuration_evaluation_count") != configuration_count
        or artifact.get("seed_run_count") != seed_run_count
        or artifact.get("failed_configuration_count") != failed_count
    ):
        raise EvaluationDataError("calibration artifact audit totals are inconsistent")
    return index


def _aggregate_seed_metrics(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, float]:
    if not rows:
        return {}
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


def _configuration_complexity(config: Mapping[str, Any]) -> int:
    """Reproduce the calibration tie-break without importing tuning code."""

    def count(value: Any) -> int:
        if isinstance(value, Mapping):
            return sum(count(nested) for nested in value.values())
        if isinstance(value, (list, tuple)):
            return sum(count(nested) for nested in value)
        if value in (None, False, 0, 0.0, ""):
            return 0
        return 1

    return count(dict(config))


def _constraint_violation(
    metrics: Mapping[str, Any],
    constraint: tuple[str, str, float],
) -> str | None:
    metric, operator, limit = constraint
    if metric not in metrics:
        return f"missing metric {metric}"
    value = metrics[metric]
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
    ):
        return f"invalid metric {metric}"
    feasible = value <= limit if operator == "<=" else value >= limit
    if feasible:
        return None
    return f"{metric}={value} violates {operator}{limit}"


def _candidate_satisfies(
    evaluation: Mapping[str, Any],
    *,
    objective: str,
    constraints: Sequence[tuple[str, str, float]],
) -> bool:
    metrics = evaluation.get("aggregate_metrics")
    return (
        evaluation.get("status") == "succeeded"
        and isinstance(metrics, dict)
        and objective in metrics
        and all(
            _constraint_violation(metrics, constraint) is None
            for constraint in constraints
        )
    )


def _mechanical_selection(
    evaluations: Sequence[Mapping[str, Any]],
    *,
    objective: str,
    direction: str,
    constraints: Sequence[tuple[str, str, float]],
) -> dict[str, Any]:
    """Recompute ``select_candidate`` from authenticated candidate rows."""

    if direction not in {"higher", "lower"} or not evaluations:
        raise EvaluationDataError("calibration selection inputs are malformed")
    identities = {
        (
            row.get("method_id"),
            row.get("track_id"),
            row.get("stage"),
        )
        for row in evaluations
    }
    if len(identities) != 1:
        raise EvaluationDataError(
            "calibration selection rows do not share one method/track/stage"
        )
    method_id, track_id, stage = next(iter(identities))
    if (
        not isinstance(method_id, str)
        or not method_id
        or not isinstance(track_id, str)
        or not track_id
        or stage != "calibration"
    ):
        raise EvaluationDataError("calibration selection identity is malformed")

    feasible: list[Mapping[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    succeeded = 0
    for evaluation in evaluations:
        metrics = evaluation.get("aggregate_metrics")
        if not isinstance(metrics, dict):
            raise EvaluationDataError(
                "calibration selection metrics are malformed"
            )
        reasons: list[str] = []
        if evaluation.get("status") != "succeeded":
            reasons.append("seed failure")
        else:
            succeeded += 1
        if objective not in metrics:
            reasons.append(f"missing objective {objective}")
        reasons.extend(
            reason
            for constraint in constraints
            if (
                reason := _constraint_violation(metrics, constraint)
            )
            is not None
        )
        if reasons:
            rejected.append(
                {
                    "config_sha256": evaluation["config_sha256"],
                    "reasons": reasons,
                }
            )
        else:
            feasible.append(evaluation)

    def order(evaluation: Mapping[str, Any]) -> tuple[Any, ...]:
        metrics = evaluation["aggregate_metrics"]
        objective_value = metrics[objective]
        primary = -objective_value if direction == "higher" else objective_value
        burden = metrics.get("operator_review_burden", math.inf)
        complexity = metrics.get(
            "complexity",
            float(_configuration_complexity(evaluation["config"])),
        )
        return primary, burden, complexity, evaluation["config_sha256"]

    selected = min(feasible, key=order) if feasible else None
    selected_hash = None if selected is None else selected["config_sha256"]
    identity = {
        "method_id": method_id,
        "track_id": track_id,
        "objective": objective,
        "direction": direction,
        "selected_config_sha256": selected_hash,
    }
    return {
        **identity,
        "status": "selected" if selected is not None else "no_feasible_candidate",
        "selected_config": None if selected is None else selected["config"],
        "selection_sha256": _canonical_mapping_sha256(identity),
        "considered_configurations": len(evaluations),
        "succeeded_configurations": succeeded,
        "feasible_configurations": len(feasible),
        "rejected": rejected,
    }


def _density_constraints(
    reference: Mapping[str, Any],
    policy: _SelectionPolicy,
) -> tuple[tuple[str, str, float], ...]:
    metrics = reference.get("aggregate_metrics")
    if not isinstance(metrics, dict):
        raise EvaluationDataError("product density metrics are malformed")
    fraction = metrics.get("retained_fraction")
    degree = metrics.get("mean_degree")
    if (
        isinstance(fraction, bool)
        or not isinstance(fraction, (int, float))
        or not math.isfinite(float(fraction))
        or isinstance(degree, bool)
        or not isinstance(degree, (int, float))
        or not math.isfinite(float(degree))
        or fraction < 0.0
        or degree < 0.0
    ):
        raise EvaluationDataError(
            "product density metrics required by joint selection are absent"
        )
    fraction_value = float(fraction)
    degree_value = float(degree)
    return (
        (
            "retained_fraction",
            ">=",
            max(0.0, fraction_value - policy.matched_fraction_tolerance),
        ),
        (
            "retained_fraction",
            "<=",
            min(1.0, fraction_value + policy.matched_fraction_tolerance),
        ),
        (
            "mean_degree",
            ">=",
            degree_value * (1.0 - policy.matched_degree_relative_tolerance),
        ),
        (
            "mean_degree",
            "<=",
            degree_value * (1.0 + policy.matched_degree_relative_tolerance),
        ),
    )


def _selection_rows_by_pair(
    artifact: Mapping[str, Any],
) -> dict[tuple[str, str], Mapping[str, Any]]:
    raw_selections = artifact.get("selections")
    if not isinstance(raw_selections, list):
        raise EvaluationDataError("calibration selections are malformed")
    required = {
        "method_id",
        "track_id",
        "objective",
        "direction",
        "status",
        "selected_config",
        "selected_config_sha256",
        "selection_sha256",
        "considered_configurations",
        "succeeded_configurations",
        "feasible_configurations",
        "rejected",
    }
    result: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in raw_selections:
        if (
            not isinstance(row, dict)
            or set(row) != required
            or not isinstance(row.get("method_id"), str)
            or not isinstance(row.get("track_id"), str)
        ):
            raise EvaluationDataError("calibration selection row schema is malformed")
        pair = (row["method_id"], row["track_id"])
        if pair in result:
            raise EvaluationDataError("calibration artifact repeats a selection")
        result[pair] = row
    return result


def _verify_mechanical_selections(
    artifact: Mapping[str, Any],
    evaluation_index: Mapping[
        tuple[str, str, str],
        Mapping[str, Any],
    ],
    *,
    policy: _SelectionPolicy,
) -> None:
    """Verify every promoted winner independently from retained seed rows."""

    evaluations_by_pair: dict[
        tuple[str, str],
        list[Mapping[str, Any]],
    ] = {}
    for (method_id, track_id, _), evaluation in evaluation_index.items():
        evaluations_by_pair.setdefault((method_id, track_id), []).append(evaluation)
    selections_by_pair = _selection_rows_by_pair(artifact)
    if not evaluations_by_pair or set(selections_by_pair) != set(evaluations_by_pair):
        raise EvaluationDataError(
            "calibration selections do not cover their retained evaluations"
        )
    methods = {method_id for method_id, _ in evaluations_by_pair}
    composition_methods = methods & COMPOSITION_METHODS
    if composition_methods and methods != COMPOSITION_METHODS:
        raise EvaluationDataError(
            "composition calibration source must contain exactly all declared "
            "composition families"
        )

    expected: dict[tuple[str, str], dict[str, Any]] = {}
    if composition_methods:
        tracks = {track_id for _, track_id in evaluations_by_pair}
        graph_constraints = (
            *policy.common_constraints,
            *policy.graph_constraints,
        )
        for track_id in tracks:
            objective_direction = policy.objectives.get(track_id)
            if objective_direction is None:
                raise EvaluationDataError(
                    f"calibration track {track_id} has no locked objective"
                )
            objective, direction = objective_direction
            product_rows = evaluations_by_pair.get(
                ("product_louvain", track_id),
                [],
            )
            comparator_rows = {
                method_id: evaluations_by_pair.get((method_id, track_id), [])
                for method_id in MATCHED_COMPOSITION_METHODS
            }
            if not product_rows or any(not rows for rows in comparator_rows.values()):
                raise EvaluationDataError(
                    "composition calibration is missing a method/track grid"
                )

            joint_product_rows: list[Mapping[str, Any]] = []
            for product in product_rows:
                matchable = _candidate_satisfies(
                    product,
                    objective=objective,
                    constraints=graph_constraints,
                ) and all(
                    any(
                        _candidate_satisfies(
                            comparator,
                            objective=objective,
                            constraints=(
                                *graph_constraints,
                                *_density_constraints(product, policy),
                            ),
                        )
                        for comparator in rows
                    )
                    for rows in comparator_rows.values()
                )
                joint = dict(product)
                joint["aggregate_metrics"] = {
                    **product["aggregate_metrics"],
                    "joint_density_match_available": float(matchable),
                }
                joint_product_rows.append(joint)
            expected_product = _mechanical_selection(
                joint_product_rows,
                objective=objective,
                direction=direction,
                constraints=(
                    *graph_constraints,
                    ("joint_density_match_available", ">=", 1.0),
                ),
            )
            expected[("product_louvain", track_id)] = expected_product
            selected_product_hash = expected_product[
                "selected_config_sha256"
            ]
            selected_product = next(
                (
                    row
                    for row in product_rows
                    if row["config_sha256"] == selected_product_hash
                ),
                None,
            )
            for method_id, rows in comparator_rows.items():
                constraints = graph_constraints
                if selected_product is not None:
                    constraints = (
                        *graph_constraints,
                        *_density_constraints(selected_product, policy),
                    )
                expected[(method_id, track_id)] = _mechanical_selection(
                    rows,
                    objective=objective,
                    direction=direction,
                    constraints=constraints,
                )
    else:
        for pair, rows in evaluations_by_pair.items():
            method_id, track_id = pair
            objective_direction = policy.objectives.get(track_id)
            if objective_direction is None:
                raise EvaluationDataError(
                    f"calibration track {track_id} has no locked objective"
                )
            objective, direction = objective_direction
            constraints = policy.common_constraints
            if method_id in SAME_REPRESENTATION_METHODS:
                constraints = (
                    *policy.common_constraints,
                    *policy.graph_constraints,
                )
            expected[pair] = _mechanical_selection(
                rows,
                objective=objective,
                direction=direction,
                constraints=constraints,
            )

    for pair, expected_row in expected.items():
        if selections_by_pair.get(pair) != expected_row:
            method_id, track_id = pair
            raise EvaluationDataError(
                "calibration winner/audit is not mechanically reproducible for "
                f"{method_id}/{track_id}"
            )


def _validate_calibration_command(
    sealed: Mapping[str, Any],
    *,
    composition_source: bool,
) -> None:
    command = sealed.get("command")
    if (
        not isinstance(command, list)
        or not command
        or any(not isinstance(part, str) or not part for part in command)
    ):
        raise EvaluationDataError("calibration run command is malformed")
    expected = (
        "exp15_calibrated_comparison"
        if composition_source
        else "exp18_tuned_baselines"
    )
    if not any(
        part == f"demo.experiments.{expected}"
        or Path(part).name == f"{expected}.py"
        for part in command
    ):
        raise EvaluationDataError(
            f"calibration run was not produced by the locked {expected} entrypoint"
        )


def _calibration_seed_tuple(protocol_dir: Path) -> tuple[int, ...]:
    manifest = _json_object(
        _read_bytes(
            protocol_dir / "seed_manifest.json",
            label="locked seed manifest",
        ),
        label="locked seed manifest",
    )
    try:
        seeds = manifest["splits"]["calibration"]
    except (KeyError, TypeError) as exc:
        raise EvaluationDataError("locked calibration split is absent") from exc
    if (
        not isinstance(seeds, list)
        or not seeds
        or any(isinstance(seed, bool) or not isinstance(seed, int) for seed in seeds)
        or len(seeds) != len(set(seeds))
    ):
        raise EvaluationDataError("locked calibration split is malformed")
    return tuple(seeds)


def _selection_policy(
    protocol_dir: Path,
) -> _SelectionPolicy:
    contract = _json_object(
        _read_bytes(
            protocol_dir / "calibration_contract.json",
            label="locked calibration contract",
        ),
        label="locked calibration contract",
    )
    selection = contract.get("selection")
    seed_manifest = _json_object(
        _read_bytes(
            protocol_dir / "seed_manifest.json",
            label="locked seed manifest",
        ),
        label="locked seed manifest",
    )
    try:
        track_rows = seed_manifest["tuning"]["tracks"]
    except (KeyError, TypeError) as exc:
        raise EvaluationDataError("locked calibration tracks are absent") from exc
    if (
        not isinstance(track_rows, list)
        or not track_rows
        or any(
            not isinstance(row, dict)
            or not isinstance(row.get("id"), str)
            or not row["id"]
            for row in track_rows
        )
    ):
        raise EvaluationDataError("locked calibration tracks are malformed")
    track_ids = tuple(row["id"] for row in track_rows)
    expected_tie_break = [
        "lower operator_review_burden",
        "lower configuration complexity",
        "lexicographic config_sha256",
    ]
    if (
        contract.get("schema_version") != "calibration-contract-v1"
        or not isinstance(selection, dict)
        or len(track_ids) != len(set(track_ids))
        or set(selection) != {*track_ids, "tie_break"}
        or selection.get("tie_break") != expected_tie_break
    ):
        raise EvaluationDataError("locked calibration selection contract is malformed")
    objectives: dict[str, tuple[str, str]] = {}
    for track_id in track_ids:
        row = selection[track_id]
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("objective"), str)
            or not row["objective"]
            or row.get("direction") not in {"higher", "lower"}
        ):
            raise EvaluationDataError(
                "locked calibration objective/direction is malformed"
            )
        objectives[track_id] = (row["objective"], row["direction"])
    try:
        minimum_stability = float(contract["stability"]["minimum_per_seed"])
        maximum_review = float(
            contract["review_policy"]["maximum_rate_per_seed"]
        )
        maximum_diameter = float(
            contract["geographic_constraint"]["maximum_metres_per_seed"]
        )
        maximum_disconnected = float(
            contract["graph_constraints"][
                "maximum_disconnected_communities_per_seed"
            ]
        )
        minimum_retained = float(
            contract["graph_constraints"][
                "minimum_retained_fraction_per_seed"
            ]
        )
        maximum_retained = float(
            contract["graph_constraints"][
                "maximum_retained_fraction_per_seed"
            ]
        )
        matched_fraction = float(
            contract["matched_composition_constraints"][
                "retained_fraction_absolute_tolerance"
            ]
        )
        matched_degree = float(
            contract["matched_composition_constraints"][
                "mean_degree_relative_tolerance"
            ]
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise EvaluationDataError(
            "locked calibration constraints are incomplete"
        ) from exc
    limits = (
        minimum_stability,
        maximum_review,
        maximum_diameter,
        maximum_disconnected,
        minimum_retained,
        maximum_retained,
        matched_fraction,
        matched_degree,
    )
    if not all(math.isfinite(value) and value >= 0 for value in limits):
        raise EvaluationDataError("locked calibration constraints are invalid")
    return _SelectionPolicy(
        objectives=MappingProxyType(objectives),
        common_constraints=(
            ("partition_stability__min", ">=", minimum_stability),
            ("operator_review_burden_rate__max", "<=", maximum_review),
            ("geographic_diameter__max", "<=", maximum_diameter),
        ),
        graph_constraints=(
            (
                "disconnected_communities__max",
                "<=",
                maximum_disconnected,
            ),
            ("retained_fraction__min", ">=", minimum_retained),
            ("retained_fraction__max", "<=", maximum_retained),
        ),
        matched_fraction_tolerance=matched_fraction,
        matched_degree_relative_tolerance=matched_degree,
    )


def _registry_config_hashes(
    protocol_dir: Path,
) -> dict[str, set[str]]:
    registry = _json_object(
        _read_bytes(
            protocol_dir / "baselines.json",
            label="locked baseline registry",
        ),
        label="locked baseline registry",
    )
    methods = registry.get("methods")
    if not isinstance(methods, list) or not methods:
        raise EvaluationDataError("locked baseline registry has no methods")
    result: dict[str, set[str]] = {}
    for method in methods:
        if not isinstance(method, dict):
            raise EvaluationDataError("locked baseline method is malformed")
        method_id = method.get("id")
        search_space = method.get("search_space")
        declared = method.get("configuration_count")
        if (
            not isinstance(method_id, str)
            or not method_id
            or method_id in result
            or not isinstance(search_space, dict)
            or not search_space
            or isinstance(declared, bool)
            or not isinstance(declared, int)
            or not 1 <= declared <= 128
        ):
            raise EvaluationDataError("locked baseline search space is malformed")
        keys = sorted(search_space)
        axes: list[list[Any]] = []
        for key in keys:
            values = search_space[key]
            if not isinstance(key, str) or not isinstance(values, list) or not values:
                raise EvaluationDataError("locked baseline search axis is malformed")
            axes.append(values)
        hashes = {
            _canonical_mapping_sha256(
                {
                    key: value
                    for key, value in zip(keys, combination, strict=True)
                }
            )
            for combination in itertools.product(*axes)
        }
        if len(hashes) != declared:
            raise EvaluationDataError(
                f"locked baseline configuration count is wrong for {method_id}"
            )
        result[method_id] = hashes
    return result


def _protocol_member_digest(members: Mapping[str, str]) -> str:
    try:
        encoded = json.dumps(
            dict(members),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise EvaluationDataError("protocol member map is malformed") from exc
    return _sha256(encoded)


def _preselection_protocol_identity(protocol_dir: Path) -> tuple[str, set[str]]:
    members = {
        path.name: _sha256(_read_bytes(path, label=f"protocol member {path.name}"))
        for path in sorted(protocol_dir.glob("*.json"))
        if path.is_file() and path.name != SELECTED_CONFIGS_NAME
    }
    if "seed_manifest.json" not in members or "metric_contract.json" not in members:
        raise EvaluationDataError("pre-selection protocol lacks required members")
    return _protocol_member_digest(members), set(members)


def _sealed_protocol_identity(
    sealed: Mapping[str, Any],
    *,
    manifest_path: Path,
) -> tuple[str, set[str]]:
    """Recompute a calibration run's protocol from its sealed snapshots."""

    inputs = sealed.get("inputs")
    protocol = inputs.get("protocol") if isinstance(inputs, dict) else None
    files = protocol.get("files") if isinstance(protocol, dict) else None
    if not isinstance(files, dict) or not files:
        raise EvaluationDataError("calibration run lacks protocol snapshots")
    if SELECTED_CONFIGS_NAME in files:
        raise EvaluationDataError(
            "calibration run improperly includes post-selection protocol state"
        )
    required_names = {"seed_manifest.json", "metric_contract.json"}
    if not required_names.issubset(files):
        raise EvaluationDataError("calibration protocol snapshots are incomplete")

    member_hashes: dict[str, str] = {}
    for name, record in files.items():
        if (
            not isinstance(name, str)
            or Path(name).name != name
            or not name.endswith(".json")
            or not isinstance(record, dict)
            or record.get("snapshot") != f"inputs/protocol/{name}"
            or not _is_sha256(record.get("sha256"))
        ):
            raise EvaluationDataError("calibration protocol snapshot record is malformed")
        snapshot = _safe_relative_path(
            manifest_path.parent,
            record["snapshot"],
            label=f"sealed protocol snapshot {name}",
        )
        payload = _read_bytes(snapshot, label=f"sealed protocol snapshot {name}")
        observed_sha = _sha256(payload)
        if (
            observed_sha != record["sha256"]
            or sealed.get("checksums", {}).get(record["snapshot"]) != observed_sha
        ):
            raise EvaluationDataError(
                f"calibration protocol snapshot checksum mismatch for {name}"
            )
        member_hashes[name] = observed_sha

    snapshot_dir = manifest_path.parent / "inputs" / "protocol"
    actual_names = {
        path.name
        for path in snapshot_dir.glob("*.json")
        if path.is_file()
    }
    if actual_names != set(member_hashes):
        raise EvaluationDataError(
            "sealed protocol snapshot set differs from its semantic manifest"
        )
    digest = _protocol_member_digest(member_hashes)
    seed_record = inputs.get("seed_manifest")
    metric_record = inputs.get("metric_contract")
    if (
        protocol.get("sha256") != digest
        or not isinstance(seed_record, dict)
        or not isinstance(metric_record, dict)
        or seed_record.get("sha256") != member_hashes["seed_manifest.json"]
        or metric_record.get("sha256") != member_hashes["metric_contract.json"]
    ):
        raise EvaluationDataError(
            "calibration protocol digest/input aliases are inconsistent"
        )
    return digest, set(member_hashes)


def _sealed_dataset_input_matches(
    sealed: Mapping[str, Any],
    *,
    manifest_path: Path,
    expected_sha256: str,
) -> bool:
    inputs = sealed.get("inputs")
    datasets = inputs.get("datasets") if isinstance(inputs, dict) else None
    if not isinstance(datasets, list) or len(datasets) != 1:
        return False
    for record in datasets:
        if (
            not isinstance(record, dict)
            or not isinstance(record.get("snapshot"), str)
            or not _is_sha256(record.get("sha256"))
            or Path(record["snapshot"]).parts[:2] != ("inputs", "datasets")
        ):
            raise EvaluationDataError(
                "calibration run dataset input record is malformed"
            )
        snapshot = _safe_relative_path(
            manifest_path.parent,
            record["snapshot"],
            label="sealed calibration dataset input",
        )
        observed_sha = _sha256(
            _read_bytes(snapshot, label="sealed calibration dataset input")
        )
        if (
            observed_sha != record["sha256"]
            or sealed.get("checksums", {}).get(record["snapshot"]) != observed_sha
        ):
            raise EvaluationDataError(
                "calibration run dataset input checksum mismatch"
            )
        return observed_sha == expected_sha256
    return False


def _expected_method_track_pairs(
    protocol_dir: Path,
) -> set[tuple[str, str]]:
    seed_manifest = _json_object(
        _read_bytes(
            protocol_dir / "seed_manifest.json",
            label="locked seed manifest",
        ),
        label="locked seed manifest",
    )
    baselines = _json_object(
        _read_bytes(
            protocol_dir / "baselines.json",
            label="locked baseline registry",
        ),
        label="locked baseline registry",
    )
    try:
        raw_tracks = seed_manifest["tuning"]["tracks"]
        raw_methods = baselines["methods"]
    except (KeyError, TypeError) as exc:
        raise EvaluationDataError(
            "locked protocol lacks methods or calibration tracks"
        ) from exc
    if (
        not isinstance(raw_tracks, list)
        or not isinstance(raw_methods, list)
        or not raw_tracks
        or not raw_methods
    ):
        raise EvaluationDataError("locked methods/tracks are malformed")
    tracks = [
        row.get("id")
        for row in raw_tracks
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    ]
    methods = [
        row.get("id")
        for row in raw_methods
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    ]
    if (
        len(tracks) != len(raw_tracks)
        or len(methods) != len(raw_methods)
        or len(set(tracks)) != len(tracks)
        or len(set(methods)) != len(methods)
    ):
        raise EvaluationDataError("locked method/track identifiers are malformed")
    return {(method, track) for method in methods for track in tracks}


def load_selected_configs(
    selected_configs_path: Path | str = DEFAULT_SELECTED_CONFIGS,
    *,
    gate2_lock: Path | str = DEFAULT_GATE2_LOCK,
    protocol_dir: Path | str = DEFAULT_PROTOCOL_DIR,
    artifact_root: Path | str = REPOSITORY_ROOT,
) -> SelectedConfigBundle:
    """Load configs only when each one traces to a sealed calibration table."""

    directory = Path(protocol_dir).resolve()
    selected_path = Path(selected_configs_path).resolve()
    if selected_path != (directory / "selected_configs.json").resolve():
        raise EvaluationDataError(
            "selected configs must be the Gate-2-locked protocol member"
        )
    # This authenticates the complete current protocol bundle, including the
    # selected-config file, before any calibration artifact is consulted.
    released_seeds, gate1_binding = _gate2_data_binding(
        Path(gate2_lock),
        directory,
    )

    selected_payload = _read_bytes(selected_path, label="selected-config registry")
    registry = _json_object(selected_payload, label="selected-config registry")
    required_top = {
        "schema_version",
        "calibration_protocol_sha256",
        "sources",
        "selections",
        "exclusions",
    }
    allowed_top = required_top | {"audit"}
    if (
        registry.get("schema_version") != "selected-configs-v1"
        or set(registry) - allowed_top
        or not required_top.issubset(registry)
        or not _is_sha256(registry.get("calibration_protocol_sha256"))
        or not isinstance(registry.get("sources"), list)
        or not isinstance(registry.get("selections"), list)
        or not isinstance(registry.get("exclusions"), list)
    ):
        raise EvaluationDataError("selected-config registry schema is malformed")
    if "audit" in registry and not isinstance(registry["audit"], dict):
        raise EvaluationDataError("selected-config audit must be an object")
    calibration_protocol_sha = registry["calibration_protocol_sha256"]
    current_preselection_sha, current_preselection_members = (
        _preselection_protocol_identity(directory)
    )
    if current_preselection_sha != calibration_protocol_sha:
        raise EvaluationDataError(
            "current pre-selection protocol differs from calibration artifacts"
        )
    calibration_seeds = _calibration_seed_tuple(directory)
    selection_policy = _selection_policy(directory)
    selection_objectives = selection_policy.objectives
    registry_config_hashes = _registry_config_hashes(directory)

    root = Path(artifact_root).resolve()
    source_records: list[SelectedConfigSource] = []
    artifacts: dict[str, dict[str, Any]] = {}
    evaluation_indexes: dict[
        str,
        dict[tuple[str, str, str], Mapping[str, Any]],
    ] = {}
    source_ids: set[str] = set()
    source_locations: set[tuple[str, str]] = set()
    required_source_fields = {
        "id",
        "run_id",
        "manifest_path",
        "manifest_sha256",
        "table_path",
        "table_sha256",
        "artifact_content_sha256",
    }
    for raw_source in registry["sources"]:
        if (
            not isinstance(raw_source, dict)
            or set(raw_source) != required_source_fields
        ):
            raise EvaluationDataError("selected-config source schema is malformed")
        source_id = raw_source["id"]
        run_id = raw_source["run_id"]
        if (
            not isinstance(source_id, str)
            or not source_id
            or source_id in source_ids
            or not isinstance(run_id, str)
            or not run_id
            or any(
                not _is_sha256(raw_source[field])
                for field in (
                    "manifest_sha256",
                    "table_sha256",
                    "artifact_content_sha256",
                )
            )
        ):
            raise EvaluationDataError("selected-config source identity is malformed")
        manifest_path = _safe_relative_path(
            root,
            raw_source["manifest_path"],
            label=f"calibration manifest path for {source_id}",
        )
        if manifest_path.name != "manifest.json":
            raise EvaluationDataError("calibration manifest path is malformed")
        manifest_payload = _read_bytes(
            manifest_path,
            label=f"calibration manifest for {source_id}",
        )
        if _sha256(manifest_payload) != raw_source["manifest_sha256"]:
            raise EvaluationDataError(
                f"calibration manifest checksum mismatch for {source_id}"
            )
        try:
            sealed = validate_manifest(manifest_path)
        except ArtifactError as exc:
            raise EvaluationDataError(
                f"calibration run is not sealed for {source_id}: {exc}"
            ) from exc
        if (
            sealed.get("run_id") != run_id
            or sealed.get("status") != "succeeded"
            or sealed.get("exit_code") != 0
        ):
            raise EvaluationDataError(
                f"calibration run identity/status mismatch for {source_id}"
            )
        sealed_protocol_sha, sealed_protocol_members = _sealed_protocol_identity(
            sealed,
            manifest_path=manifest_path,
        )
        if (
            sealed_protocol_sha != calibration_protocol_sha
            or sealed_protocol_members != current_preselection_members
        ):
            raise EvaluationDataError(
                f"calibration protocol provenance mismatch for {source_id}"
            )

        raw_table_path = raw_source["table_path"]
        if (
            not isinstance(raw_table_path, str)
            or Path(raw_table_path).parts[:1] != ("tables",)
        ):
            raise EvaluationDataError(
                f"calibration table path is malformed for {source_id}"
            )
        source_location = (str(manifest_path), raw_table_path)
        if source_location in source_locations:
            raise EvaluationDataError("calibration artifact source is duplicated")
        table_path = _safe_relative_path(
            manifest_path.parent,
            raw_table_path,
            label=f"calibration table path for {source_id}",
        )
        if sealed["checksums"].get(raw_table_path) != raw_source["table_sha256"]:
            raise EvaluationDataError(
                f"sealed table checksum differs for {source_id}"
            )
        table_payload = _read_bytes(
            table_path,
            label=f"calibration table for {source_id}",
        )
        if _sha256(table_payload) != raw_source["table_sha256"]:
            raise EvaluationDataError(
                f"calibration table checksum mismatch for {source_id}"
            )
        artifact = _json_object(
            table_payload,
            label=f"calibration table for {source_id}",
        )
        if (
            artifact.get("schema_version") != "calibration-artifact-v1"
            or artifact.get("protocol_sha256") != calibration_protocol_sha
            or _artifact_content_sha256(artifact)
            != raw_source["artifact_content_sha256"]
            or not isinstance(artifact.get("selections"), list)
        ):
            raise EvaluationDataError(
                f"calibration artifact binding mismatch for {source_id}"
            )
        metadata = artifact.get("metadata")
        frozen_dataset = (
            metadata.get("frozen_dataset")
            if isinstance(metadata, dict)
            else None
        )
        if (
            not isinstance(frozen_dataset, dict)
            or any(
                frozen_dataset.get(field) != gate1_binding[field]
                for field in (
                    "gate1_lock_sha256",
                    "accepted_run_manifest_sha256",
                    "dataset_manifest_sha256",
                )
            )
            or not _sealed_dataset_input_matches(
                sealed,
                manifest_path=manifest_path,
                expected_sha256=gate1_binding["dataset_manifest_sha256"],
            )
        ):
            raise EvaluationDataError(
                f"calibration dataset provenance mismatch for {source_id}"
            )
        evaluation_index = _calibration_evaluation_index(
            artifact,
            calibration_seeds=calibration_seeds,
        )
        methods_in_source = {
            method_id for method_id, _, _ in evaluation_index
        }
        _validate_calibration_command(
            sealed,
            composition_source=bool(methods_in_source & COMPOSITION_METHODS),
        )
        _verify_mechanical_selections(
            artifact,
            evaluation_index,
            policy=selection_policy,
        )
        evaluation_indexes[source_id] = evaluation_index
        artifacts[source_id] = artifact
        source_ids.add(source_id)
        source_locations.add(source_location)
        source_records.append(
            SelectedConfigSource(
                id=source_id,
                run_id=run_id,
                manifest_path=raw_source["manifest_path"],
                manifest_sha256=raw_source["manifest_sha256"],
                table_path=raw_table_path,
                table_sha256=raw_source["table_sha256"],
                artifact_content_sha256=raw_source["artifact_content_sha256"],
            )
        )
    if not source_records:
        raise EvaluationDataError("selected-config registry has no artifact sources")

    selected_records: list[SelectedConfig] = []
    selected_pairs: set[tuple[str, str]] = set()
    referenced_sources: set[str] = set()
    required_selection_fields = {
        "method_id",
        "track_id",
        "config",
        "config_sha256",
        "source_artifact_id",
        "source_selection_sha256",
    }
    for raw_selection in registry["selections"]:
        if (
            not isinstance(raw_selection, dict)
            or set(raw_selection) != required_selection_fields
        ):
            raise EvaluationDataError("selected-config row schema is malformed")
        method_id = raw_selection["method_id"]
        track_id = raw_selection["track_id"]
        config = raw_selection["config"]
        config_sha = raw_selection["config_sha256"]
        source_id = raw_selection["source_artifact_id"]
        source_selection_sha = raw_selection["source_selection_sha256"]
        if (
            not isinstance(method_id, str)
            or not method_id
            or not isinstance(track_id, str)
            or not track_id
            or not isinstance(config, dict)
            or not _is_sha256(config_sha)
            or not isinstance(source_id, str)
            or source_id not in artifacts
            or not _is_sha256(source_selection_sha)
        ):
            raise EvaluationDataError("selected-config row identity is malformed")
        pair = (method_id, track_id)
        if pair in selected_pairs:
            raise EvaluationDataError(
                f"duplicate selected config for {method_id}/{track_id}"
            )
        if _canonical_mapping_sha256(config) != config_sha:
            raise EvaluationDataError(
                f"selected config checksum mismatch for {method_id}/{track_id}"
            )

        matching = [
            row
            for row in artifacts[source_id]["selections"]
            if isinstance(row, dict)
            and row.get("method_id") == method_id
            and row.get("track_id") == track_id
        ]
        if len(matching) != 1:
            raise EvaluationDataError(
                f"calibration source has no unique selection for "
                f"{method_id}/{track_id}"
            )
        source_selection = matching[0]
        expected_objective = selection_objectives.get(track_id)
        source_evaluation = evaluation_indexes[source_id].get(
            (method_id, track_id, config_sha)
        )
        pair_evaluations = [
            row
            for (candidate_method, candidate_track, _), row in
            evaluation_indexes[source_id].items()
            if candidate_method == method_id and candidate_track == track_id
        ]
        if (
            source_selection.get("status") != "selected"
            or source_selection.get("selected_config") != config
            or source_selection.get("selected_config_sha256") != config_sha
            or source_selection.get("selection_sha256") != source_selection_sha
            or _selection_sha256(source_selection) != source_selection_sha
            or expected_objective is None
            or (
                source_selection.get("objective"),
                source_selection.get("direction"),
            )
            != expected_objective
            or source_evaluation is None
            or source_evaluation.get("status") != "succeeded"
            or source_evaluation.get("config") != config
            or source_selection.get("considered_configurations")
            != len(pair_evaluations)
            or source_selection.get("succeeded_configurations")
            != sum(row.get("status") == "succeeded" for row in pair_evaluations)
            or {
                str(row.get("config_sha256")) for row in pair_evaluations
            }
            != registry_config_hashes.get(method_id)
        ):
            raise EvaluationDataError(
                f"selected config differs from calibration source for "
                f"{method_id}/{track_id}"
            )
        selected_pairs.add(pair)
        referenced_sources.add(source_id)
        selected_records.append(
            SelectedConfig(
                method_id=method_id,
                track_id=track_id,
                config=_freeze_json(config),
                config_sha256=config_sha,
                source_artifact_id=source_id,
                source_selection_sha256=source_selection_sha,
            )
        )

    excluded_records: list[SelectedConfigExclusion] = []
    excluded_pairs: set[tuple[str, str]] = set()
    required_exclusion_fields = {
        "method_id",
        "track_id",
        "status",
        "source_artifact_id",
        "source_selection_sha256",
    }
    for raw_exclusion in registry["exclusions"]:
        if (
            not isinstance(raw_exclusion, dict)
            or set(raw_exclusion) != required_exclusion_fields
        ):
            raise EvaluationDataError("selected-config exclusion schema is malformed")
        method_id = raw_exclusion["method_id"]
        track_id = raw_exclusion["track_id"]
        status = raw_exclusion["status"]
        source_id = raw_exclusion["source_artifact_id"]
        source_selection_sha = raw_exclusion["source_selection_sha256"]
        if (
            not isinstance(method_id, str)
            or not method_id
            or not isinstance(track_id, str)
            or not track_id
            or status != "no_feasible_candidate"
            or not isinstance(source_id, str)
            or source_id not in artifacts
            or not _is_sha256(source_selection_sha)
        ):
            raise EvaluationDataError(
                "selected-config exclusion identity is malformed"
            )
        pair = (method_id, track_id)
        if pair in selected_pairs or pair in excluded_pairs:
            raise EvaluationDataError(
                f"duplicate selected/excluded config for {method_id}/{track_id}"
            )
        matching = [
            row
            for row in artifacts[source_id]["selections"]
            if isinstance(row, dict)
            and row.get("method_id") == method_id
            and row.get("track_id") == track_id
        ]
        if len(matching) != 1:
            raise EvaluationDataError(
                f"calibration source has no unique exclusion for "
                f"{method_id}/{track_id}"
            )
        source_selection = matching[0]
        pair_evaluations = [
            row
            for (candidate_method, candidate_track, _), row in
            evaluation_indexes[source_id].items()
            if candidate_method == method_id and candidate_track == track_id
        ]
        expected_objective = selection_objectives.get(track_id)
        if (
            source_selection.get("status") != "no_feasible_candidate"
            or source_selection.get("selected_config") is not None
            or source_selection.get("selected_config_sha256") is not None
            or source_selection.get("selection_sha256") != source_selection_sha
            or _selection_sha256(source_selection) != source_selection_sha
            or expected_objective is None
            or (
                source_selection.get("objective"),
                source_selection.get("direction"),
            )
            != expected_objective
            or source_selection.get("considered_configurations")
            != len(pair_evaluations)
            or source_selection.get("succeeded_configurations")
            != sum(row.get("status") == "succeeded" for row in pair_evaluations)
            or source_selection.get("feasible_configurations") != 0
            or not isinstance(source_selection.get("rejected"), list)
            or len(source_selection["rejected"]) != len(pair_evaluations)
            or {
                str(row.get("config_sha256")) for row in pair_evaluations
            }
            != registry_config_hashes.get(method_id)
        ):
            raise EvaluationDataError(
                f"infeasible calibration record differs from source for "
                f"{method_id}/{track_id}"
            )
        excluded_pairs.add(pair)
        referenced_sources.add(source_id)
        excluded_records.append(
            SelectedConfigExclusion(
                method_id=method_id,
                track_id=track_id,
                status=status,
                source_artifact_id=source_id,
                source_selection_sha256=source_selection_sha,
            )
        )

    expected_pairs = _expected_method_track_pairs(directory)
    expected_tracks = {track for _, track in expected_pairs}
    if set(selection_objectives) != expected_tracks:
        raise EvaluationDataError(
            "calibration contract tracks differ from the seed protocol"
        )
    covered_pairs = selected_pairs | excluded_pairs
    if covered_pairs != expected_pairs:
        missing = sorted(expected_pairs - covered_pairs)
        unexpected = sorted(covered_pairs - expected_pairs)
        raise EvaluationDataError(
            "selected/excluded configs do not cover the locked method/track "
            "cross-product; "
            f"missing={missing}, unexpected={unexpected}"
        )
    if referenced_sources != source_ids:
        raise EvaluationDataError("selected-config registry contains an unused source")

    by_pair = {
        (row.method_id, row.track_id): row for row in selected_records
    }
    for row in selected_records:
        if row.method_id not in {"product_leiden", "product_spectral"}:
            continue
        metadata = artifacts[row.source_artifact_id].get("metadata")
        dependency_hashes = (
            metadata.get("product_selection_hashes")
            if isinstance(metadata, dict)
            else None
        )
        product = by_pair.get(("product_louvain", row.track_id))
        if (
            not isinstance(dependency_hashes, dict)
            or product is None
            or dependency_hashes.get(row.track_id) != product.config_sha256
        ):
            raise EvaluationDataError(
                f"{row.method_id}/{row.track_id} is not bound to the promoted "
                "product representation"
            )

    end_released, end_gate1_binding = _gate2_data_binding(
        Path(gate2_lock),
        directory,
    )
    end_preselection_sha, end_preselection_members = (
        _preselection_protocol_identity(directory)
    )
    if (
        tuple(end_released) != tuple(released_seeds)
        or dict(end_gate1_binding) != dict(gate1_binding)
        or _read_bytes(selected_path, label="selected-config registry")
        != selected_payload
        or end_preselection_sha != current_preselection_sha
        or end_preselection_members != current_preselection_members
    ):
        raise EvaluationDataError(
            "Gate-2 protocol or selected-config registry changed during validation"
        )

    return SelectedConfigBundle(
        calibration_protocol_sha256=calibration_protocol_sha,
        sources=tuple(sorted(source_records, key=lambda row: row.id)),
        selections=tuple(
            sorted(selected_records, key=lambda row: (row.method_id, row.track_id))
        ),
        exclusions=tuple(
            sorted(excluded_records, key=lambda row: (row.method_id, row.track_id))
        ),
    )


__all__ = [
    "DEFAULT_GATE1_LOCK",
    "DEFAULT_GATE2_LOCK",
    "DEFAULT_SELECTED_CONFIGS",
    "EvaluationDataError",
    "EvaluationDataset",
    "EvaluatorReport",
    "SelectedConfig",
    "SelectedConfigBundle",
    "SelectedConfigExclusion",
    "SelectedConfigSource",
    "build_evaluator_analysis_view",
    "load_evaluation_dataset",
    "load_selected_configs",
]
