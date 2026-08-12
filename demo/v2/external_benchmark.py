"""Read-only external sanity run for the geographically anchored ``dataV2``.

This module is deliberately outside the frozen v2 confirmation workflow.  It
adapts the five-table ``dataV2`` run schema through an explicit inference
allow-list, verifies evaluator/latent/manifest joins, executes the
already-selected v2 clustering configurations, and retains adverse
noise/campaign and duplicate results.  It never calibrates, generates data,
mutates accepted artifacts, or claims confirmatory/real-data validation.

The input bundle has report-level cluster/noise labels but no independent
incident outcome table.  Priority alignment, dispatch benefit, confidence
intervals, and hypothesis tests are therefore intentionally unsupported.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile
import traceback
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np

from demo.v2.clustering import ClusterRunV2, clustering_endpoints
from demo.v2.contracts import ReportV2, TruthV2, validate_unique_report_ids
from demo.v2.dedup import (
    are_near_duplicates,
    deduplicate_reports,
    exact_fingerprint,
)
from demo.v2.experiment import all_configurations, execute_configuration
from demo.v2.priority import report_provenance_scores
from demo.v2.protocol import ExpandedConfiguration, file_sha256, load_protocol


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = REPOSITORY_ROOT / "demo" / "dataV2"
DEFAULT_RUN_ROOT = DEFAULT_DATA_ROOT / "gold" / "run_001"
DEFAULT_REPORTS = DEFAULT_RUN_ROOT / "algorithm_input.json"
DEFAULT_TRUTH = DEFAULT_RUN_ROOT / "ground_truth.json"
DEFAULT_SELECTION = (
    REPOSITORY_ROOT / "revision" / "v2" / "results" / "calibration_selection.json"
)
DEFAULT_EXPECTED_RUNS = 80

OBSERVABLE_ROW_FIELDS = frozenset(
    {
        "event_id",
        "lat",
        "lng",
        "created_at",
        "flood",
        "urgency",
        "n_trapped",
        "vulnerability",
        "has_image",
        "province",
        "note",
        "confidence",
        "n_corrob",
        # Known evaluator fields are accepted only so their exposure can be
        # audited.  They are never forwarded into ReportV2.
        "gt_cluster",
        "is_fake",
    }
)
ALGORITHM_ROW_FIELDS = frozenset(
    {
        "event_id",
        "lat",
        "lng",
        "created_at",
        "flood",
        "urgency",
        "n_trapped",
        "vulnerability",
        "has_image",
        "province",
        "note",
        "confidence",
        "n_corrob",
    }
)
INFERENCE_ALLOWLIST = frozenset(
    {
        "event_id",
        "lat",
        "lng",
        "created_at",
        "flood",
        "urgency",
        "n_trapped",
        "vulnerability",
        "has_image",
        "confidence",
    }
)
EXPOSED_EVALUATOR_FIELDS = frozenset({"gt_cluster", "is_fake"})
TRUTH_ROW_FIELDS = frozenset(
    {
        "event_id",
        "gt_cluster",
        "is_fake",
        "report_class",
        "duplicate_type",
        "duplicate_of",
        "attack_campaign_id",
    }
)
LATENT_ROW_FIELDS = frozenset(
    {
        "latent_event_id",
        "activation_id",
        "anchor_id",
        "aoi_name",
        "center",
        "event_time",
        "F_true",
        "E_true",
        "N_reference",
        "N_true",
        "trapped_ratio",
        "V_reference",
        "vulnerability_source",
    }
)
MANIFEST_FIELDS = frozenset(
    {
        "dataset_id",
        "seed",
        "generator_version",
        "historical_context",
        "input_mode",
        "parameters",
        "sources",
        "silver_anchor_count",
        "important_notes",
    }
)
METHOD_ORDER = (
    "method.product_louvain",
    "method.additive_louvain",
    "method.st_dbscan",
    "method.hdbscan_geo_time",
)


class ExternalBenchmarkError(ValueError):
    """Raised when the external bundle cannot be adapted without ambiguity."""


@dataclass(frozen=True, slots=True)
class ExternalAnnotationV2:
    report_id: str
    gt_cluster: int
    is_fake: bool
    report_class: str
    duplicate_type: str
    duplicate_of: str | None
    attack_campaign_id: str | None


@dataclass(frozen=True, slots=True)
class ExternalDatasetV2:
    dataset_id: str
    reports: tuple[ReportV2, ...]
    report_truth: tuple[TruthV2, ...]
    annotations: tuple[ExternalAnnotationV2, ...]
    historical_context: Mapping[str, str]
    report_payload_sha256: str
    truth_payload_sha256: str
    algorithm_payload_sha256: str | None = None
    observable_payload_sha256: str | None = None
    latent_payload_sha256: str | None = None
    manifest_payload_sha256: str | None = None
    run_manifest: Mapping[str, Any] | None = None
    latent_incidents: tuple[Mapping[str, Any], ...] = ()
    input_mode: str = "legacy"
    auxiliary_stats: Mapping[str, Any] | None = None


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ExternalBenchmarkError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json_object(path: Path, label: str) -> Mapping[str, Any]:
    source = Path(path)
    if not source.is_file() or source.is_symlink():
        raise ExternalBenchmarkError(f"missing or unsafe {label}: {source}")
    try:
        value = json.loads(
            source.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ExternalBenchmarkError(f"non-finite JSON constant in {label}: {token}")
            ),
        )
    except json.JSONDecodeError as exc:
        raise ExternalBenchmarkError(f"invalid JSON in {label}: {exc}") from exc
    if not isinstance(value, Mapping):
        raise ExternalBenchmarkError(f"{label} must be a JSON object")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str] | frozenset[str], label: str) -> None:
    actual = set(value)
    if actual != set(expected):
        missing = sorted(set(expected).difference(actual))
        extra = sorted(actual.difference(expected))
        raise ExternalBenchmarkError(
            f"{label} schema mismatch; missing={missing}, extra={extra}"
        )


def _nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExternalBenchmarkError(f"{label} must be a non-empty string")
    return value.strip()


def _integer(value: object, label: str) -> int:
    if type(value) is not int:
        raise ExternalBenchmarkError(f"{label} must be an integer")
    return int(value)


def _boolean(value: object, label: str) -> bool:
    if type(value) is not bool:
        raise ExternalBenchmarkError(f"{label} must be boolean")
    return bool(value)


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExternalBenchmarkError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ExternalBenchmarkError(f"{label} must be finite")
    return result


def _optional_identifier(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _nonempty_string(value, label)


def _truth_annotation(row: Mapping[str, Any], index: int) -> ExternalAnnotationV2:
    label = f"ground_truth.report_labels[{index}]"
    _exact_keys(row, TRUTH_ROW_FIELDS, label)
    duplicate_type = _nonempty_string(row["duplicate_type"], f"{label}.duplicate_type")
    report_class = _nonempty_string(row["report_class"], f"{label}.report_class")
    if duplicate_type not in {"none", "exact", "near"}:
        raise ExternalBenchmarkError(f"unsupported {label}.duplicate_type: {duplicate_type}")
    if report_class not in {"genuine", "duplicate", "coordinated_fake"}:
        raise ExternalBenchmarkError(f"unsupported {label}.report_class: {report_class}")
    annotation = ExternalAnnotationV2(
        report_id=_nonempty_string(row["event_id"], f"{label}.event_id"),
        gt_cluster=_integer(row["gt_cluster"], f"{label}.gt_cluster"),
        is_fake=_boolean(row["is_fake"], f"{label}.is_fake"),
        report_class=report_class,
        duplicate_type=duplicate_type,
        duplicate_of=_optional_identifier(row["duplicate_of"], f"{label}.duplicate_of"),
        attack_campaign_id=_optional_identifier(
            row["attack_campaign_id"], f"{label}.attack_campaign_id"
        ),
    )
    if annotation.gt_cluster < -1:
        raise ExternalBenchmarkError(f"{label}.gt_cluster must be -1 or non-negative")
    if (annotation.gt_cluster == -1) != annotation.is_fake:
        raise ExternalBenchmarkError(
            f"{label} must use gt_cluster=-1 exactly for fake/noise reports"
        )
    is_duplicate = annotation.duplicate_type != "none"
    if is_duplicate != (annotation.report_class == "duplicate"):
        raise ExternalBenchmarkError(f"{label} duplicate class/type disagree")
    if is_duplicate != (annotation.duplicate_of is not None):
        raise ExternalBenchmarkError(f"{label} duplicate lineage is incomplete")
    if (annotation.report_class == "coordinated_fake") != (
        annotation.attack_campaign_id is not None
    ):
        raise ExternalBenchmarkError(f"{label} attack campaign annotation is inconsistent")
    return annotation


def _parse_context(value: object, label: str) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ExternalBenchmarkError(f"{label} must be an object")
    required = {"activation_id", "event_name", "event_time"}
    if not required.issubset(value):
        raise ExternalBenchmarkError(
            f"{label} is missing required keys: {sorted(required.difference(value))}"
        )
    context = {
        key: _nonempty_string(value[key], f"{label}.{key}")
        for key in ("activation_id", "event_name", "event_time")
    }
    try:
        parsed_event_time = datetime.fromisoformat(
            context["event_time"].replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ExternalBenchmarkError(f"{label}.event_time is not ISO-8601") from exc
    if parsed_event_time.tzinfo is None:
        raise ExternalBenchmarkError(f"{label}.event_time must include a timezone")
    if "country" in value:
        context["country"] = _nonempty_string(value["country"], f"{label}.country")
    return context


def _optional_finite_number(value: object, label: str) -> float | None:
    if value is None:
        return None
    return _finite_number(value, label)


def _load_annotations(evaluator: Mapping[str, Any]) -> tuple[ExternalAnnotationV2, ...]:
    _exact_keys(evaluator, {"dataset_id", "report_labels"}, "ground-truth root")
    raw_truth = evaluator["report_labels"]
    if not isinstance(raw_truth, list):
        raise ExternalBenchmarkError("ground_truth.report_labels must be an array")
    annotations = tuple(
        _truth_annotation(row, index)
        if isinstance(row, Mapping)
        else (_ for _ in ()).throw(
            ExternalBenchmarkError(f"ground_truth.report_labels[{index}] must be an object")
        )
        for index, row in enumerate(raw_truth)
    )
    if len({row.report_id for row in annotations}) != len(annotations):
        raise ExternalBenchmarkError("ground-truth event_id values must be unique")
    return annotations


def _build_reports(
    input_payload: Mapping[str, Any],
) -> tuple[str, tuple[ReportV2, ...], dict[str, str], str]:
    input_keys = set(input_payload)
    if "excluded_evaluator_fields" in input_payload:
        _exact_keys(
            input_payload,
            {"dataset_id", "seed", "historical_context", "excluded_evaluator_fields", "reports"},
            "algorithm-input root",
        )
        excluded = input_payload["excluded_evaluator_fields"]
        if excluded != ["gt_cluster", "is_fake"]:
            raise ExternalBenchmarkError(
                "algorithm_input.excluded_evaluator_fields must be ['gt_cluster', 'is_fake']"
            )
        seed = _integer(input_payload["seed"], "algorithm_input.seed")
        if seed < 1:
            raise ExternalBenchmarkError("algorithm_input.seed must be positive")
        input_mode = "algorithm_input"
    else:
        _exact_keys(input_payload, {"dataset_id", "historical_context", "reports"}, "input root")
        input_mode = "legacy_observable"
    dataset_id = _nonempty_string(input_payload["dataset_id"], "input.dataset_id")
    context = _parse_context(input_payload["historical_context"], "input.historical_context")
    raw_reports = input_payload["reports"]
    if not isinstance(raw_reports, list):
        raise ExternalBenchmarkError("input.reports must be an array")
    reports: list[ReportV2] = []
    observed_ids: set[str] = set()
    for index, raw_row in enumerate(raw_reports):
        label = f"input.reports[{index}]"
        if not isinstance(raw_row, Mapping):
            raise ExternalBenchmarkError(f"{label} must be an object")
        if set(raw_row) == set(OBSERVABLE_ROW_FIELDS):
            row = {key: raw_row[key] for key in ALGORITHM_ROW_FIELDS}
        else:
            _exact_keys(raw_row, ALGORITHM_ROW_FIELDS, label)
            row = raw_row
        report_id = _nonempty_string(row["event_id"], f"{label}.event_id")
        if report_id in observed_ids:
            raise ExternalBenchmarkError(f"duplicate input event_id: {report_id}")
        observed_ids.add(report_id)
        n_corrob = _integer(row["n_corrob"], f"{label}.n_corrob")
        if n_corrob < 0:
            raise ExternalBenchmarkError(f"{label}.n_corrob must be non-negative")
        lat = _optional_finite_number(row["lat"], f"{label}.lat")
        lng = _optional_finite_number(row["lng"], f"{label}.lng")
        if (lat is None) != (lng is None):
            raise ExternalBenchmarkError(f"{label}.lat/lng must be both present or both null")
        created_at = row["created_at"]
        if created_at is not None:
            created_at = _nonempty_string(created_at, f"{label}.created_at")
        reports.append(
            ReportV2(
                report_id=report_id,
                L=None if lat is None else (lat, lng),
                T=created_at,
                received_at=created_at,
                F=_optional_finite_number(row["flood"], f"{label}.flood"),
                E=_optional_finite_number(row["urgency"], f"{label}.urgency"),
                N=_optional_finite_number(row["n_trapped"], f"{label}.n_trapped"),
                V=_optional_finite_number(row["vulnerability"], f"{label}.vulnerability"),
                provenance_quality=_optional_finite_number(
                    row["confidence"], f"{label}.confidence"
                ),
                has_image=_boolean(row["has_image"], f"{label}.has_image"),
                source_id=None,
                source_family=None,
            )
        )
    validate_unique_report_ids(reports)
    return dataset_id, tuple(reports), context, input_mode


def _validate_observable_payload(
    observable: Mapping[str, Any],
    dataset_id: str,
    annotation_by_id: Mapping[str, ExternalAnnotationV2],
    input_ids: set[str],
) -> dict[str, Any]:
    _exact_keys(observable, {"dataset_id", "historical_context", "reports"}, "observable root")
    if observable["dataset_id"] != dataset_id:
        raise ExternalBenchmarkError("observable and algorithm_input dataset_id values differ")
    _parse_context(observable["historical_context"], "observable.historical_context")
    raw_reports = observable["reports"]
    if not isinstance(raw_reports, list):
        raise ExternalBenchmarkError("observable.reports must be an array")
    observed_ids: set[str] = set()
    for index, raw_row in enumerate(raw_reports):
        label = f"observable.reports[{index}]"
        if not isinstance(raw_row, Mapping):
            raise ExternalBenchmarkError(f"{label} must be an object")
        _exact_keys(raw_row, OBSERVABLE_ROW_FIELDS, label)
        report_id = _nonempty_string(raw_row["event_id"], f"{label}.event_id")
        if report_id in observed_ids:
            raise ExternalBenchmarkError(f"duplicate observable event_id: {report_id}")
        observed_ids.add(report_id)
        annotation = annotation_by_id.get(report_id)
        if annotation is None:
            raise ExternalBenchmarkError(f"observable report lacks evaluator row: {report_id}")
        if (
            _integer(raw_row["gt_cluster"], f"{label}.gt_cluster") != annotation.gt_cluster
            or _boolean(raw_row["is_fake"], f"{label}.is_fake") != annotation.is_fake
        ):
            raise ExternalBenchmarkError(
                f"exposed evaluator fields disagree with ground truth: {report_id}"
            )
    if observed_ids != input_ids:
        raise ExternalBenchmarkError(
            "algorithm_input and observable report IDs differ: "
            f"missing={sorted(input_ids - observed_ids)[:5]}, "
            f"extra={sorted(observed_ids - input_ids)[:5]}"
        )
    return {"n_rows": len(raw_reports), "evaluator_fields_exposed": sorted(EXPOSED_EVALUATOR_FIELDS)}


def _validate_latent_payload(
    latent: Mapping[str, Any], dataset_id: str
) -> tuple[tuple[Mapping[str, Any], ...], dict[str, Any]]:
    _exact_keys(latent, {"dataset_id", "incidents"}, "latent-incidents root")
    if latent["dataset_id"] != dataset_id:
        raise ExternalBenchmarkError("latent_incidents and input dataset_id values differ")
    rows = latent["incidents"]
    if not isinstance(rows, list):
        raise ExternalBenchmarkError("latent_incidents.incidents must be an array")
    ids: set[str] = set()
    validated: list[Mapping[str, Any]] = []
    for index, row in enumerate(rows):
        label = f"latent_incidents.incidents[{index}]"
        if not isinstance(row, Mapping):
            raise ExternalBenchmarkError(f"{label} must be an object")
        _exact_keys(row, LATENT_ROW_FIELDS, label)
        incident_id = _nonempty_string(row["latent_event_id"], f"{label}.latent_event_id")
        if incident_id in ids:
            raise ExternalBenchmarkError(f"duplicate latent_event_id: {incident_id}")
        ids.add(incident_id)
        center = row["center"]
        if not isinstance(center, Mapping) or set(center) != {"lat", "lng"}:
            raise ExternalBenchmarkError(f"{label}.center must contain lat and lng")
        latitude = _finite_number(center["lat"], f"{label}.center.lat")
        longitude = _finite_number(center["lng"], f"{label}.center.lng")
        if not -90.0 <= latitude <= 90.0 or not -180.0 <= longitude <= 180.0:
            raise ExternalBenchmarkError(f"{label}.center is outside WGS84 bounds")
        event_time = _nonempty_string(row["event_time"], f"{label}.event_time")
        try:
            parsed_time = datetime.fromisoformat(event_time.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ExternalBenchmarkError(f"{label}.event_time is not ISO-8601") from exc
        if parsed_time.tzinfo is None:
            raise ExternalBenchmarkError(f"{label}.event_time must include a timezone")
        for field in (
            "F_true",
            "E_true",
            "N_reference",
            "N_true",
            "trapped_ratio",
            "V_reference",
        ):
            _finite_number(row[field], f"{label}.{field}")
        _nonempty_string(row["activation_id"], f"{label}.activation_id")
        _nonempty_string(row["anchor_id"], f"{label}.anchor_id")
        _nonempty_string(row["aoi_name"], f"{label}.aoi_name")
        _nonempty_string(row["vulnerability_source"], f"{label}.vulnerability_source")
        validated.append(row)
    return tuple(validated), {"n_incidents": len(validated), "unique_latent_event_ids": len(ids)}


def _validate_manifest(
    manifest: Mapping[str, Any], dataset_id: str, seed: int | None
) -> None:
    _exact_keys(manifest, MANIFEST_FIELDS, "run_manifest")
    if manifest["dataset_id"] != dataset_id:
        raise ExternalBenchmarkError("run_manifest and input dataset_id values differ")
    if seed is not None and _integer(manifest["seed"], "run_manifest.seed") != seed:
        raise ExternalBenchmarkError("run_manifest.seed and algorithm_input.seed differ")
    _nonempty_string(manifest["generator_version"], "run_manifest.generator_version")
    _parse_context(manifest["historical_context"], "run_manifest.historical_context")
    if not isinstance(manifest["parameters"], Mapping):
        raise ExternalBenchmarkError("run_manifest.parameters must be an object")
    if not isinstance(manifest["sources"], Mapping):
        raise ExternalBenchmarkError("run_manifest.sources must be an object")
    if not isinstance(manifest["important_notes"], list):
        raise ExternalBenchmarkError("run_manifest.important_notes must be an array")


def _load_dataset_payloads(
    input_payload: Mapping[str, Any],
    evaluator: Mapping[str, Any],
    *,
    input_path: Path,
    truth_path: Path,
    observable: Mapping[str, Any] | None = None,
    observable_path: Path | None = None,
    latent: Mapping[str, Any] | None = None,
    latent_path: Path | None = None,
    manifest: Mapping[str, Any] | None = None,
    manifest_path: Path | None = None,
) -> ExternalDatasetV2:
    dataset_id, reports, context, input_mode = _build_reports(input_payload)
    annotations = _load_annotations(evaluator)
    annotation_by_id = {row.report_id: row for row in annotations}
    input_ids = {row.report_id for row in reports}
    if set(annotation_by_id) != input_ids:
        raise ExternalBenchmarkError(
            "input and ground truth event IDs differ: "
            f"missing={sorted(input_ids - set(annotation_by_id))[:5]}, "
            f"extra={sorted(set(annotation_by_id) - input_ids)[:5]}"
        )
    observable_audit = None
    if observable is not None:
        observable_audit = _validate_observable_payload(
            observable, dataset_id, annotation_by_id, input_ids
        )
    for annotation in annotations:
        if annotation.duplicate_of is None:
            continue
        if annotation.duplicate_of == annotation.report_id:
            raise ExternalBenchmarkError(f"self-referential duplicate: {annotation.report_id}")
        target = annotation_by_id.get(annotation.duplicate_of)
        if target is None:
            raise ExternalBenchmarkError(
                f"duplicate target is absent: {annotation.duplicate_of}"
            )
        if target.report_class != "genuine" or target.gt_cluster != annotation.gt_cluster:
            raise ExternalBenchmarkError(
                f"duplicate target class/cluster mismatch: {annotation.report_id}"
            )
    latent_rows: tuple[Mapping[str, Any], ...] = ()
    if latent is not None:
        latent_rows, _ = _validate_latent_payload(latent, dataset_id)
    seed = None
    if "seed" in input_payload:
        seed = _integer(input_payload["seed"], "algorithm_input.seed")
    if manifest is not None:
        _validate_manifest(manifest, dataset_id, seed)
    raw_input_rows = input_payload.get("reports", [])
    n_corrob_values = [
        int(row["n_corrob"])
        for row in raw_input_rows
        if isinstance(row, Mapping) and isinstance(row.get("n_corrob"), int)
    ]
    auxiliary_stats: dict[str, Any] = {
        "n_corrob_min": min(n_corrob_values) if n_corrob_values else None,
        "n_corrob_max": max(n_corrob_values) if n_corrob_values else None,
        "n_corrob_mean": (
            sum(n_corrob_values) / len(n_corrob_values) if n_corrob_values else None
        ),
        "n_corrob_unique": sorted(set(n_corrob_values)),
        "n_rows": len(raw_input_rows) if isinstance(raw_input_rows, list) else 0,
    }
    truth = tuple(
        TruthV2(report_id=row.report_id, is_noise=True, is_fake=row.is_fake)
        if row.gt_cluster == -1
        else TruthV2(
            report_id=row.report_id,
            incident_id=f"external-incident-{row.gt_cluster:03d}",
            gt_cluster=row.gt_cluster,
            is_fake=row.is_fake,
        )
        for row in annotations
    )
    return ExternalDatasetV2(
        dataset_id=dataset_id,
        reports=reports,
        report_truth=truth,
        annotations=annotations,
        historical_context=context,
        report_payload_sha256=file_sha256(input_path),
        truth_payload_sha256=file_sha256(truth_path),
        algorithm_payload_sha256=file_sha256(input_path),
        observable_payload_sha256=(
            file_sha256(observable_path) if observable_path is not None else None
        ),
        latent_payload_sha256=file_sha256(latent_path) if latent_path is not None else None,
        manifest_payload_sha256=file_sha256(manifest_path) if manifest_path is not None else None,
        run_manifest=manifest,
        latent_incidents=latent_rows,
        input_mode=input_mode,
        auxiliary_stats=auxiliary_stats,
    )


def load_external_run(run_dir: Path) -> ExternalDatasetV2:
    """Load one current ``dataV2/gold/run_NNN`` directory.

    ``algorithm_input.json`` is the only payload passed to inference.  The
    observable table, ground truth, latent incidents, and manifest are loaded
    separately for audit and evaluator joins.
    """

    directory = Path(run_dir)
    if not directory.is_dir() or directory.is_symlink():
        raise ExternalBenchmarkError(f"unsafe or missing run directory: {directory}")
    required = {
        "algorithm_input.json",
        "ground_truth.json",
        "observable_reports.json",
        "latent_incidents.json",
        "run_manifest.json",
    }
    actual = {path.name for path in directory.iterdir() if path.is_file()}
    if actual != required:
        raise ExternalBenchmarkError(
            f"{directory} file set mismatch; missing={sorted(required - actual)}, "
            f"extra={sorted(actual - required)}"
        )
    input_path = directory / "algorithm_input.json"
    truth_path = directory / "ground_truth.json"
    observable_path = directory / "observable_reports.json"
    latent_path = directory / "latent_incidents.json"
    manifest_path = directory / "run_manifest.json"
    input_payload = _read_json_object(input_path, "algorithm input")
    if "excluded_evaluator_fields" not in input_payload:
        raise ExternalBenchmarkError(
            "algorithm_input.json must declare excluded_evaluator_fields; "
            "observable/legacy rows cannot be used as run inference input"
        )
    evaluator = _read_json_object(truth_path, "ground truth")
    observable = _read_json_object(observable_path, "observable report table")
    latent = _read_json_object(latent_path, "latent incident table")
    manifest = _read_json_object(manifest_path, "run manifest")
    return _load_dataset_payloads(
        input_payload,
        evaluator,
        input_path=input_path,
        truth_path=truth_path,
        observable=observable,
        observable_path=observable_path,
        latent=latent,
        latent_path=latent_path,
        manifest=manifest,
        manifest_path=manifest_path,
    )


def load_external_dataset(
    reports_path: Path = DEFAULT_REPORTS,
    truth_path: Path = DEFAULT_TRUTH,
) -> ExternalDatasetV2:
    """Load a legacy pair or a clean ``algorithm_input``/truth pair."""

    reports_path = Path(reports_path)
    truth_path = Path(truth_path)
    input_payload = _read_json_object(reports_path, "input report table")
    evaluator = _read_json_object(truth_path, "ground-truth table")
    observable = None
    if set(input_payload) == {"dataset_id", "historical_context", "reports"}:
        rows = input_payload.get("reports")
        if isinstance(rows, list) and rows and set(rows[0]) == set(OBSERVABLE_ROW_FIELDS):
            observable = input_payload
    return _load_dataset_payloads(
        input_payload,
        evaluator,
        input_path=reports_path,
        truth_path=truth_path,
        observable=observable,
        observable_path=reports_path if observable is not None else None,
    )


def _safe_ratio(numerator: int | float, denominator: int | float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def _union_find_components(
    report_ids: Iterable[str], annotations: Sequence[ExternalAnnotationV2]
) -> dict[str, str]:
    parent = {report_id: report_id for report_id in report_ids}

    def find(value: str) -> str:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(left: str, right: str) -> None:
        left_root, right_root = find(left), find(right)
        if left_root == right_root:
            return
        first, second = sorted((left_root, right_root))
        parent[second] = first

    for row in annotations:
        if row.duplicate_of is not None:
            union(row.report_id, row.duplicate_of)
    return {report_id: find(report_id) for report_id in parent}


def _identifier_blocks(annotations: Sequence[ExternalAnnotationV2]) -> dict[str, Any]:
    rows: list[tuple[int, str]] = []
    for row in annotations:
        match = re.fullmatch(r"[A-Za-z_-]*?(\d+)", row.report_id)
        if match is None:
            return {
                "numeric_suffix_available": False,
                "truth_categories_form_disjoint_contiguous_blocks": False,
                "blocks": {},
            }
        # Audit the generation class as a whole.  Splitting exact/near here
        # would hide the fact that the numeric suffix itself separates the
        # three evaluator classes.
        category = row.report_class
        rows.append((int(match.group(1)), category))
    categories: dict[str, list[int]] = {}
    for value, category in rows:
        categories.setdefault(category, []).append(value)
    blocks = {
        category: {"count": len(values), "minimum": min(values), "maximum": max(values)}
        for category, values in sorted(categories.items())
    }
    intervals = sorted(
        (entry["minimum"], entry["maximum"], category)
        for category, entry in blocks.items()
    )
    nonoverlap = all(
        intervals[index][1] < intervals[index + 1][0]
        for index in range(len(intervals) - 1)
    )
    contiguous = all(
        entry["maximum"] - entry["minimum"] + 1 == entry["count"]
        for entry in blocks.values()
    )
    return {
        "numeric_suffix_available": True,
        "truth_categories_form_disjoint_contiguous_blocks": nonoverlap and contiguous,
        "blocks": blocks,
    }


def duplicate_audit(dataset: ExternalDatasetV2) -> dict[str, Any]:
    """Compare observable complete-link families with declared duplicate lineage."""

    report_by_id = {row.report_id: row for row in dataset.reports}
    deduplication = deduplicate_reports(dataset.reports)
    predicted_family = {
        report_id: family_index
        for family_index, family in enumerate(deduplication.families)
        for report_id in family.report_ids
    }
    gold_family = _union_find_components(report_by_id, dataset.annotations)

    true_positive = false_positive = false_negative = 0
    ordered_ids = sorted(report_by_id)
    for left_index, left in enumerate(ordered_ids):
        for right in ordered_ids[left_index + 1 :]:
            gold_same = gold_family[left] == gold_family[right]
            predicted_same = predicted_family[left] == predicted_family[right]
            if gold_same and predicted_same:
                true_positive += 1
            elif predicted_same:
                false_positive += 1
            elif gold_same:
                false_negative += 1

    exact_rows = [row for row in dataset.annotations if row.duplicate_type == "exact"]
    near_rows = [row for row in dataset.annotations if row.duplicate_type == "near"]
    exact_fingerprint_matches = sum(
        exact_fingerprint(report_by_id[row.report_id])
        == exact_fingerprint(report_by_id[row.duplicate_of])
        for row in exact_rows
        if row.duplicate_of is not None
    )
    exact_rows_matching_near = sum(
        are_near_duplicates(report_by_id[row.report_id], report_by_id[row.duplicate_of])
        for row in exact_rows
        if row.duplicate_of is not None
    )
    near_rows_matching_near = sum(
        are_near_duplicates(report_by_id[row.report_id], report_by_id[row.duplicate_of])
        for row in near_rows
        if row.duplicate_of is not None
    )
    return {
        "declared_exact_rows": len(exact_rows),
        "declared_exact_fingerprint_matches": exact_fingerprint_matches,
        "declared_exact_rows_matching_near_envelope": exact_rows_matching_near,
        "declared_near_rows": len(near_rows),
        "declared_near_rows_matching_near_envelope": near_rows_matching_near,
        "observable_exact_duplicates_removed": deduplication.exact_duplicates_removed,
        "observable_near_units_coalesced": deduplication.near_units_coalesced,
        "observable_evidence_families": len(deduplication.families),
        "pairwise": {
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "precision": _safe_ratio(true_positive, true_positive + false_positive),
            "recall": _safe_ratio(true_positive, true_positive + false_negative),
            "f1": _safe_ratio(
                2 * true_positive,
                2 * true_positive + false_positive + false_negative,
            ),
        },
    }


def dataset_audit(dataset: ExternalDatasetV2) -> dict[str, Any]:
    annotations = {row.report_id: row for row in dataset.annotations}
    reports = dataset.reports
    values = {
        "F": [float(row.F) for row in reports if row.F is not None],
        "E": [float(row.E) for row in reports if row.E is not None],
        "N": [float(row.N) for row in reports if row.N is not None],
        "V": [float(row.V) for row in reports if row.V is not None],
        "provenance_quality": [
            float(row.provenance_quality)
            for row in reports
            if row.provenance_quality is not None
        ],
    }
    ranges = {
        field: {
            "minimum": min(field_values),
            "maximum": max(field_values),
            "mean": sum(field_values) / len(field_values),
        }
        for field, field_values in values.items()
    }
    report_times = [row.T for row in reports if row.T is not None]
    issue_rows = [
        {
            "code": "public_source_lineage_not_reproducible",
            "severity": "high",
            "detail": "no source manifest, pinned raw snapshots, per-row linkage, or build notebook is bundled",
        },
        {
            "code": "source_identity_missing",
            "severity": "high",
            "detail": "source_id/source_family are absent, so distinct-source corroboration cannot be evaluated",
        },
        {
            "code": "vulnerability_unit_undocumented",
            "severity": "high",
            "detail": "all values lie in [0,1], while v2 priority expects vulnerability-mass evidence",
        },
        {
            "code": "incident_outcome_truth_missing",
            "severity": "high",
            "detail": "no independent latent benefit/deadline/service/harm table exists",
        },
        {
            "code": "single_dataset_descriptive_only",
            "severity": "high",
            "detail": "one run cannot support paired uncertainty or confirmatory inference",
        },
        {
            "code": "receipt_time_unavailable",
            "severity": "medium",
            "detail": "created_at is mapped to both event and receipt time; the frozen 150-minute snapshot is not applied",
        },
    ]
    if dataset.observable_payload_sha256 is not None:
        issue_rows.insert(
            0,
            {
                "code": "oracle_fields_exposed_in_observable_file",
                "severity": "high",
                "detail": "gt_cluster and is_fake are present in observable_reports.json; the adapter drops them",
            },
        )
    identifiers = _identifier_blocks(dataset.annotations)
    if identifiers["truth_categories_form_disjoint_contiguous_blocks"]:
        issue_rows.append(
            {
                "code": "identifier_encodes_generation_class",
                "severity": "high",
                "detail": "numeric event_id ranges perfectly separate genuine, duplicate, and campaign classes",
            }
        )
    return {
        "classification": "geographically_anchored_semi_synthetic",
        "n_reports": len(reports),
        "n_linked_reports": sum(row.gt_cluster >= 0 for row in dataset.annotations),
        "n_noise_fake_reports": sum(row.gt_cluster == -1 for row in dataset.annotations),
        "n_incidents": len(
            {row.gt_cluster for row in dataset.annotations if row.gt_cluster >= 0}
        ),
        "n_campaigns": len(
            {
                row.attack_campaign_id
                for row in dataset.annotations
                if row.attack_campaign_id is not None
            }
        ),
        "n_genuine_rows": sum(row.report_class == "genuine" for row in dataset.annotations),
        "n_duplicate_rows": sum(row.report_class == "duplicate" for row in dataset.annotations),
        "n_latent_incidents": len(dataset.latent_incidents),
        "all_graph_eligible": all(row.graph_eligible for row in reports),
        "missing_observation_counts": {
            field: sum(field in row.missing_fields for row in reports)
            for field in ("L", "T", "F", "E", "N", "V")
        },
        "ranges": ranges,
        "n_claims_above_priority_cap_500": sum(
            row.N is not None and row.N > 500.0 for row in reports
        ),
        "all_vulnerability_values_in_unit_interval": all(
            row.V is not None and 0.0 <= row.V <= 1.0 for row in reports
        ),
        "time_min": min(report_times).isoformat() if report_times else None,
        "time_max": max(report_times).isoformat() if report_times else None,
        "identifier_audit": identifiers,
        "input_mode": dataset.input_mode,
        "generator_version": (
            dataset.run_manifest.get("generator_version")
            if dataset.run_manifest is not None
            else None
        ),
        "latent_v_reference_null_count": sum(
            row.get("V_reference") is None for row in dataset.latent_incidents
        ),
        "auxiliary_stats": dict(dataset.auxiliary_stats or {}),
        "evaluator_fields_exposed_in_observable": sorted(EXPOSED_EVALUATOR_FIELDS),
        "inference_allowlist": sorted(INFERENCE_ALLOWLIST),
        "issues": issue_rows,
        "annotation_lookup_complete": set(annotations)
        == {row.report_id for row in reports},
    }


def _external_cluster_metrics(
    dataset: ExternalDatasetV2, run: ClusterRunV2
) -> dict[str, Any]:
    annotation = {row.report_id: row for row in dataset.annotations}
    groups: dict[int, list[str]] = {}
    for report, label in zip(dataset.reports, run.labels, strict=True):
        if label != -1:
            groups.setdefault(int(label), []).append(report.report_id)

    mixed_noise_reports = 0
    assigned_noise_reports = 0
    weighted_purity_numerator = 0
    weighted_purity_denominator = 0
    for members in groups.values():
        rows = [annotation[report_id] for report_id in members]
        noise_count = sum(row.gt_cluster == -1 for row in rows)
        linked = [row.gt_cluster for row in rows if row.gt_cluster >= 0]
        assigned_noise_reports += noise_count
        if linked and noise_count:
            mixed_noise_reports += noise_count
        if linked:
            counts: dict[int, int] = {}
            for value in linked:
                counts[value] = counts.get(value, 0) + 1
            weighted_purity_numerator += max(counts.values())
            weighted_purity_denominator += len(rows)

    campaigns: dict[str, list[str]] = {}
    for row in dataset.annotations:
        if row.attack_campaign_id is not None:
            campaigns.setdefault(row.attack_campaign_id, []).append(row.report_id)
    report_index = {row.report_id: index for index, row in enumerate(dataset.reports)}
    campaign_rows = {}
    for campaign_id, members in sorted(campaigns.items()):
        labels = [run.labels[report_index[report_id]] for report_id in members]
        destinations = sorted({int(label) for label in labels if label != -1})
        campaign_rows[campaign_id] = {
            "n_reports": len(members),
            "n_rejected": sum(label == -1 for label in labels),
            "n_operational_destinations": len(destinations),
            "destination_labels": destinations,
        }
    n_noise = sum(row.gt_cluster == -1 for row in dataset.annotations)
    return {
        "assigned_noise_reports": assigned_noise_reports,
        "mixed_noise_reports": mixed_noise_reports,
        "mixed_noise_absorption_rate": _safe_ratio(mixed_noise_reports, n_noise),
        "linked_destination_weighted_purity": _safe_ratio(
            weighted_purity_numerator, weighted_purity_denominator
        ),
        "campaigns": campaign_rows,
    }


def _configuration_payload(configuration: ExpandedConfiguration) -> dict[str, Any]:
    return {
        "configuration_id": configuration.configuration_id,
        "method_id": configuration.method_id,
        "operator": configuration.operator,
        "pair_id": configuration.pair_id,
        "parameters": dict(configuration.parameters),
    }


def _selected_configurations(selection_path: Path) -> tuple[Mapping[str, Any], dict[str, ExpandedConfiguration]]:
    selection = _read_json_object(selection_path, "calibration selection")
    if selection.get("schema_version") != "v2.calibration-selection.1":
        raise ExternalBenchmarkError("unsupported calibration-selection schema")
    protocol = load_protocol()
    if selection.get("protocol_sha256") != protocol.bundle_sha256:
        raise ExternalBenchmarkError("selection does not match the frozen protocol")
    available = {
        configuration.configuration_id: configuration
        for configuration in all_configurations(protocol)
    }
    rows = selection.get("selections")
    if not isinstance(rows, Mapping) or set(rows) != set(METHOD_ORDER):
        raise ExternalBenchmarkError("selection must cover the four frozen methods")
    selected: dict[str, ExpandedConfiguration] = {}
    for method_id in METHOD_ORDER:
        row = rows[method_id]
        if not isinstance(row, Mapping) or row.get("status") != "selected":
            raise ExternalBenchmarkError(f"method lacks a frozen selection: {method_id}")
        payload = row.get("configuration")
        if not isinstance(payload, Mapping):
            raise ExternalBenchmarkError(f"selection lacks configuration: {method_id}")
        identifier = payload.get("configuration_id")
        if not isinstance(identifier, str) or identifier not in available:
            raise ExternalBenchmarkError(f"unknown selected configuration: {identifier}")
        configuration = available[identifier]
        if configuration.method_id != method_id:
            raise ExternalBenchmarkError(f"method/configuration mismatch: {method_id}")
        if dict(payload) != _configuration_payload(configuration):
            raise ExternalBenchmarkError(f"selected configuration payload drifted: {identifier}")
        selected[method_id] = configuration
    return selection, selected


def _payload_sha256(value: object) -> str:
    encoded = (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _execute_external_dataset(
    dataset: ExternalDatasetV2,
    *,
    selection_path: Path,
    random_state: int,
    source_paths: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    """Execute one descriptive run after the inference/evaluator boundary."""

    if type(random_state) is not int:
        raise ExternalBenchmarkError("random_state must be an integer")
    selection_path = Path(selection_path)
    selection, selected = _selected_configurations(selection_path)
    provenance = report_provenance_scores(dataset.reports)
    method_rows: dict[str, Any] = {}
    runs: dict[str, ClusterRunV2] = {}
    for method_id in METHOD_ORDER:
        configuration = selected[method_id]
        run = execute_configuration(
            dataset.reports,
            configuration,
            seed=random_state,
        )
        runs[method_id] = run
        assignments = [
            {"report_id": report.report_id, "label": int(label)}
            for report, label in zip(dataset.reports, run.labels, strict=True)
        ]
        method_rows[method_id] = {
            "configuration_id": configuration.configuration_id,
            "configuration": _configuration_payload(configuration),
            "assignment_sha256": _payload_sha256(assignments),
            "assignment_coverage": {
                "n_reports": len(dataset.reports),
                "n_labels": len(run.labels),
                "n_unique_report_ids": len({row["report_id"] for row in assignments}),
                "all_reports_assigned": len(run.labels) == len(dataset.reports),
            },
            "threshold_weight": run.threshold_weight,
            "candidate_pairs": run.candidate_pairs,
            "retained_edges": run.retained_edges,
            "metrics": clustering_endpoints(
                dataset.reports,
                dataset.report_truth,
                run,
                provenance_scores=provenance,
            ),
            "external_metrics": _external_cluster_metrics(dataset, run),
        }

    product = method_rows["method.product_louvain"]["metrics"]
    additive = method_rows["method.additive_louvain"]["metrics"]
    contrast_endpoints = (
        "ari_linked",
        "false_destinations_per_100_reports",
        "noise_rejection",
        "review_items_per_100_reports",
        "split_loss",
        "merge_loss",
        "max_diameter_m",
    )
    readme_path = (
        Path(source_paths["readme"])
        if source_paths is not None and "readme" in source_paths
        else None
    )
    duplicate_results = duplicate_audit(dataset)
    audit = dataset_audit(dataset)
    if duplicate_results["declared_exact_fingerprint_matches"] != duplicate_results[
        "declared_exact_rows"
    ]:
        audit["issues"].append(
            {
                "code": "declared_exact_duplicates_fail_v2_fingerprint",
                "severity": "high",
                "detail": "all declared exact copies differ in inference-visible event time",
            }
        )
    if duplicate_results["pairwise"]["false_positive"]:
        audit["issues"].append(
            {
                "code": "observable_dedup_false_merges",
                "severity": "high",
                "detail": "missing source-family evidence permits many complete-link false-positive pairs",
            }
        )
    return {
        "schema_version": "v2.external-sanity-run.1",
        "status": "completed_descriptive_only",
        "scope": {
            "dataset_class": "geographically_anchored_semi_synthetic",
            "frozen_confirmation_modified": False,
            "calibration_or_tuning_performed": False,
            "generator_invoked": False,
            "supported": [
                "report-level clustering endpoints",
                "noise/campaign destination diagnostics",
                "observable duplicate-family diagnostics",
            ],
            "unsupported": [
                "confirmatory uncertainty or hypothesis testing",
                "priority alignment/NDCG",
                "dispatch benefit/harm",
                "real rescue-report validation",
            ],
        },
        "inputs": {
            "dataset_id": dataset.dataset_id,
            "reports_file": str(
                source_paths.get("algorithm_input", source_paths.get("reports", ""))
                if source_paths is not None
                else ""
            ),
            "reports_sha256": dataset.algorithm_payload_sha256
            or dataset.report_payload_sha256,
            "truth_file": str(source_paths.get("truth", "") if source_paths else ""),
            "truth_sha256": dataset.truth_payload_sha256,
            "observable_file": str(source_paths.get("observable", "") if source_paths else ""),
            "observable_sha256": dataset.observable_payload_sha256,
            "latent_file": str(source_paths.get("latent", "") if source_paths else ""),
            "latent_sha256": dataset.latent_payload_sha256,
            "manifest_file": str(source_paths.get("manifest", "") if source_paths else ""),
            "manifest_sha256": dataset.manifest_payload_sha256,
            "readme_sha256": file_sha256(readme_path) if readme_path and readme_path.is_file() else None,
            "selection_file": str(selection_path),
            "selection_sha256": file_sha256(selection_path),
            "protocol_sha256": selection["protocol_sha256"],
            "random_state": random_state,
        },
        "adapter": {
            "observable_mapping": {
                "event_id": "report_id",
                "[lat,lng]": "L",
                "created_at": "T and received_at (explicit proxy assumption)",
                "flood": "F",
                "urgency": "E",
                "n_trapped": "N",
                "vulnerability": "V (raw value; unit not validated)",
                "confidence": "provenance_quality (direct mapping; not validated)",
                "has_image": "has_image",
            },
            "dropped_evaluator_fields": sorted(EXPOSED_EVALUATOR_FIELDS),
            "ignored_observable_fields": ["n_corrob", "note", "province"],
            "truth_join": "independent report_id lookup; row-order alignment is never used",
            "source_id": None,
            "source_family": None,
            "snapshot": "full supplied batch; no 150-minute proxy cutoff applied",
            "input_file": "algorithm_input.json when loading a run directory",
        },
        "dataset_audit": audit,
        "duplicate_audit": duplicate_results,
        "clustering": method_rows,
        "product_minus_additive": {
            endpoint: float(product[endpoint]) - float(additive[endpoint])
            for endpoint in contrast_endpoints
        },
        "interpretation": {
            "result_role": "exploratory external sanity evidence only",
            "adverse_results_retained": True,
            "high_linked_ari_does_not_imply_noise_safety": True,
            "promotion_into_frozen_v2_evidence_permitted": False,
        },
    }


def run_external_benchmark(
    *,
    reports_path: Path = DEFAULT_REPORTS,
    truth_path: Path = DEFAULT_TRUTH,
    selection_path: Path = DEFAULT_SELECTION,
    random_state: int = 42,
) -> dict[str, Any]:
    """Execute one deterministic descriptive run with frozen configs."""

    reports_path, truth_path, selection_path = map(
        Path, (reports_path, truth_path, selection_path)
    )
    dataset = load_external_dataset(reports_path, truth_path)
    return _execute_external_dataset(
        dataset,
        selection_path=selection_path,
        random_state=random_state,
        source_paths={"reports": reports_path, "truth": truth_path},
    )


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write JSON with a same-directory replace so a checkpoint is complete."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _best_effort_git_sha() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = completed.stdout.strip()
    return value if re.fullmatch(r"[0-9a-f]{40}", value) else None


def _summary_statistics(values: Sequence[float]) -> dict[str, float | int]:
    if not values:
        return {"n": 0}
    array = np.asarray(values, dtype=float)
    return {
        "n": int(array.size),
        "mean": float(array.mean()),
        "sd": float(array.std(ddof=1)) if array.size > 1 else 0.0,
        "median": float(np.median(array)),
        "iqr": float(np.quantile(array, 0.75) - np.quantile(array, 0.25)),
        "min": float(array.min()),
        "max": float(array.max()),
    }


def bootstrap_paired_delta(
    left: Sequence[float],
    right: Sequence[float],
    *,
    n_bootstrap: int = 10_000,
    seed: int = 2_026_081_2,
) -> dict[str, Any]:
    """Return a deterministic percentile CI for paired ``left - right``."""

    if len(left) != len(right):
        raise ExternalBenchmarkError("paired bootstrap inputs must have equal length")
    if not left:
        return {"n": 0, "mean_delta": None, "ci95": [None, None], "deltas": []}
    if type(n_bootstrap) is not int or n_bootstrap <= 0:
        raise ExternalBenchmarkError("n_bootstrap must be a positive integer")
    observed = np.asarray(left, dtype=float) - np.asarray(right, dtype=float)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, observed.size, size=(n_bootstrap, observed.size))
    samples = observed[indices].mean(axis=1)
    return {
        "n": int(observed.size),
        "mean_delta": float(observed.mean()),
        "median_delta": float(np.median(observed)),
        "ci95": [float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))],
        "deltas": [float(value) for value in observed],
    }


def aggregate_batch_results(
    results: Sequence[Mapping[str, Any]],
    *,
    bootstrap_seed: int = 2_026_081_2,
    n_bootstrap: int = 10_000,
) -> dict[str, Any]:
    """Aggregate successful per-run JSON without introducing p-values."""

    successful = [row for row in results if row.get("status") == "completed_descriptive_only"]
    summaries: dict[str, Any] = {}
    endpoint_names = (
        "ari_linked",
        "false_destinations_per_100_reports",
        "noise_rejection",
        "review_items_per_100_reports",
        "split_loss",
        "merge_loss",
        "max_diameter_m",
        "singleton_rate",
    )
    for method_id in METHOD_ORDER:
        summaries[method_id] = {
            endpoint: _summary_statistics(
                [
                    float(row["clustering"][method_id]["metrics"][endpoint])
                    for row in successful
                    if endpoint in row.get("clustering", {}).get(method_id, {}).get("metrics", {})
                ]
            )
            for endpoint in endpoint_names
        }
    paired: dict[str, Any] = {}
    for endpoint in endpoint_names:
        product_values = []
        additive_values = []
        for row in successful:
            product = row.get("clustering", {}).get("method.product_louvain", {}).get("metrics", {})
            additive = row.get("clustering", {}).get("method.additive_louvain", {}).get("metrics", {})
            if endpoint in product and endpoint in additive:
                product_values.append(float(product[endpoint]))
                additive_values.append(float(additive[endpoint]))
        paired[endpoint] = bootstrap_paired_delta(
            product_values,
            additive_values,
            n_bootstrap=n_bootstrap,
            seed=bootstrap_seed,
        )
    campaign_rows: list[dict[str, Any]] = []
    dedup_rows: list[dict[str, Any]] = []
    for row in successful:
        dataset_id = row.get("inputs", {}).get("dataset_id")
        for method_id in METHOD_ORDER:
            external = row["clustering"][method_id].get("external_metrics", {})
            for campaign_id, values in external.get("campaigns", {}).items():
                campaign_rows.append(
                    {
                        "dataset_id": dataset_id,
                        "method_id": method_id,
                        "campaign_id": campaign_id,
                        "assigned_noise_reports": external.get("assigned_noise_reports", 0),
                        "mixed_noise_reports": external.get("mixed_noise_reports", 0),
                        "mixed_noise_absorption_rate": external.get(
                            "mixed_noise_absorption_rate", 0.0
                        ),
                        "linked_destination_weighted_purity": external.get(
                            "linked_destination_weighted_purity", 0.0
                        ),
                        **values,
                    }
                )
        dedup = dict(row.get("duplicate_audit", {}))
        dedup["dataset_id"] = dataset_id
        dedup_rows.append(dedup)
    return {
        "n_results": len(results),
        "n_success": len(successful),
        "n_failures": len(results) - len(successful),
        "method_summaries": summaries,
        "paired_product_minus_additive": paired,
        "campaign_rows": campaign_rows,
        "dedup_rows": dedup_rows,
        "bootstrap": {
            "seed": bootstrap_seed,
            "n_bootstrap": n_bootstrap,
            "ci": "percentile_95",
            "unit": "run",
            "p_values": False,
        },
    }


def _resolve_batch_root(data_root: Path) -> Path:
    root = Path(data_root)
    if (root / "gold").is_dir():
        root = root / "gold"
    if not root.is_dir() or root.is_symlink():
        raise ExternalBenchmarkError(f"missing or unsafe dataV2 root: {data_root}")
    return root


def run_external_batch(
    data_root: Path = DEFAULT_DATA_ROOT,
    output_dir: Path = REPOSITORY_ROOT / "demo" / "dataV2" / "results" / "external_sanity",
    *,
    expected_runs: int = DEFAULT_EXPECTED_RUNS,
    random_state: int = 42,
    selection_path: Path = DEFAULT_SELECTION,
    resume: bool = True,
    git_sha: str | None = None,
    progress_callback: Callable[[str, int, int, str], None] | None = None,
) -> dict[str, Any]:
    """Run all dataV2 directories with immutable, resumable checkpoints."""

    if type(expected_runs) is not int or expected_runs <= 0:
        raise ExternalBenchmarkError("expected_runs must be a positive integer")
    if type(random_state) is not int:
        raise ExternalBenchmarkError("random_state must be an integer")
    data_root = _resolve_batch_root(Path(data_root))
    output_dir = Path(output_dir)
    run_dirs = {
        path.name: path
        for path in data_root.iterdir()
        if path.is_dir() and re.fullmatch(r"run_\d{3}", path.name)
    }
    expected_names = {f"run_{index:03d}" for index in range(1, expected_runs + 1)}
    if set(run_dirs) != expected_names:
        raise ExternalBenchmarkError(
            "run directory set mismatch; "
            f"missing={sorted(expected_names - set(run_dirs))}, "
            f"extra={sorted(set(run_dirs) - expected_names)}"
        )
    selection_path = Path(selection_path)
    if not selection_path.is_file():
        raise ExternalBenchmarkError(f"missing selection file: {selection_path}")
    selection_payload = _read_json_object(selection_path, "calibration selection")
    selection_sha = file_sha256(selection_path)
    protocol_sha = load_protocol().bundle_sha256
    if selection_payload.get("protocol_sha256") != protocol_sha:
        raise ExternalBenchmarkError(
            "calibration selection protocol_sha256 does not match the frozen protocol"
        )
    current_git_sha = git_sha or _best_effort_git_sha()
    auxiliary_root = data_root.parent
    auxiliary_hashes = {
        name: file_sha256(auxiliary_root / name)
        for name in ("generation_summary.csv", "activation_metadata.json", "enriched_anchors.parquet")
        if (auxiliary_root / name).is_file()
    }
    immutable = {
        "data_root": str(data_root.resolve()),
        "expected_runs": expected_runs,
        "random_state": random_state,
        "selection_sha256": selection_sha,
        "protocol_sha256": protocol_sha,
        "git_sha": current_git_sha,
        "auxiliary_input_sha256": auxiliary_hashes,
    }
    manifest_path = output_dir / "batch_manifest.json"
    existing_manifest: Mapping[str, Any] | None = None
    if manifest_path.exists():
        if not resume:
            raise ExternalBenchmarkError(
                f"output already has a batch manifest; choose a new directory: {output_dir}"
            )
        existing_manifest = _read_json_object(manifest_path, "batch manifest")
        if existing_manifest.get("immutable") != immutable:
            raise ExternalBenchmarkError(
                "resume metadata mismatch; use a new output directory or restore the same inputs"
            )
    elif any(output_dir.iterdir()) if output_dir.exists() else False:
        raise ExternalBenchmarkError(
            f"output directory is non-empty without a batch manifest: {output_dir}"
        )
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
    if existing_manifest is None:
        existing_manifest = {
            "schema_version": "v2.external-sanity-batch.1",
            "status": "started",
            "immutable": immutable,
            "completed_runs": [],
            "failed_runs": [],
        }
        _atomic_write_json(manifest_path, existing_manifest)

    per_run_dir = output_dir / "per_run"
    per_run_dir.mkdir(parents=True, exist_ok=True)
    result_payloads: list[Mapping[str, Any]] = []
    failures: list[Mapping[str, Any]] = []
    total_runs = len(expected_names)
    for run_index, name in enumerate(sorted(expected_names), start=1):
        run_dir = run_dirs[name]
        result_path = per_run_dir / f"{name}.json"
        if result_path.exists():
            cached = _read_json_object(result_path, f"cached result {name}")
            cached_inputs = cached.get("inputs", {})
            expected_dataset = _read_json_object(
                run_dir / "algorithm_input.json", f"algorithm input {name}"
            ).get("dataset_id")
            current_hashes = {
                "algorithm": file_sha256(run_dir / "algorithm_input.json"),
                "truth": file_sha256(run_dir / "ground_truth.json"),
                "observable": file_sha256(run_dir / "observable_reports.json"),
                "latent": file_sha256(run_dir / "latent_incidents.json"),
                "manifest": file_sha256(run_dir / "run_manifest.json"),
            }
            cached_algorithm_sha = cached_inputs.get(
                "reports_sha256", cached_inputs.get("algorithm_input_sha256")
            )
            if (
                cached.get("status") not in {"completed_descriptive_only", "failed"}
                or cached_inputs.get("dataset_id") != expected_dataset
                or cached_inputs.get("random_state") != random_state
                or cached_inputs.get("selection_sha256") != selection_sha
                or cached_algorithm_sha != current_hashes["algorithm"]
                or cached_inputs.get("truth_sha256") != current_hashes["truth"]
                or cached_inputs.get("observable_sha256") != current_hashes["observable"]
                or cached_inputs.get("latent_sha256") != current_hashes["latent"]
                or cached_inputs.get("manifest_sha256") != current_hashes["manifest"]
            ):
                raise ExternalBenchmarkError(
                    f"cached result provenance mismatch for {name}: {result_path}"
                )
            result_payloads.append(cached)
            if cached.get("status") == "failed":
                failures.append(cached)
            if progress_callback is not None:
                progress_callback(name, run_index, total_runs, "cached")
            continue
        try:
            dataset = load_external_run(run_dir)
            result = _execute_external_dataset(
                dataset,
                selection_path=selection_path,
                random_state=random_state,
                source_paths={
                    "algorithm_input": run_dir / "algorithm_input.json",
                    "reports": run_dir / "algorithm_input.json",
                    "truth": run_dir / "ground_truth.json",
                    "observable": run_dir / "observable_reports.json",
                    "latent": run_dir / "latent_incidents.json",
                    "manifest": run_dir / "run_manifest.json",
                    "readme": data_root.parent / "README.md",
                },
            )
        except Exception as exc:  # retain failures as first-class evidence
            result = {
                "schema_version": "v2.external-sanity-run.1",
                "status": "failed",
                "inputs": {
                    "dataset_id": name,
                    "random_state": random_state,
                    "selection_sha256": selection_sha,
                    "algorithm_input_sha256": file_sha256(run_dir / "algorithm_input.json"),
                    "truth_sha256": file_sha256(run_dir / "ground_truth.json"),
                    "observable_sha256": file_sha256(run_dir / "observable_reports.json"),
                    "latent_sha256": file_sha256(run_dir / "latent_incidents.json"),
                    "manifest_sha256": file_sha256(run_dir / "run_manifest.json"),
                },
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
            }
            failures.append(result)
        _atomic_write_json(result_path, result)
        result_payloads.append(result)
        if progress_callback is not None:
            progress_callback(
                name,
                run_index,
                total_runs,
                "completed" if result.get("status") == "completed_descriptive_only" else "failed",
            )
        completed = [
            row.get("inputs", {}).get("dataset_id")
            for row in result_payloads
            if row.get("status") == "completed_descriptive_only"
        ]
        failed = [
            row.get("inputs", {}).get("dataset_id")
            for row in result_payloads
            if row.get("status") == "failed"
        ]
        existing_manifest = {
            **dict(existing_manifest),
            "completed_runs": sorted(filter(None, completed)),
            "failed_runs": sorted(filter(None, failed)),
            "status": "started",
        }
        _atomic_write_json(manifest_path, existing_manifest)

    aggregate = aggregate_batch_results(result_payloads)
    _atomic_write_json(output_dir / "aggregate_results.json", aggregate)
    _atomic_write_json(
        output_dir / "failures.json",
        {
            "schema_version": "v2.external-sanity-failures.1",
            "failures": failures,
        },
    )
    final_manifest = {
        **dict(existing_manifest),
        "status": "completed" if not failures else "completed_with_failures",
        "completed_runs": sorted(
            row.get("inputs", {}).get("dataset_id")
            for row in result_payloads
            if row.get("status") == "completed_descriptive_only"
        ),
        "failed_runs": sorted(
            row.get("inputs", {}).get("dataset_id")
            for row in result_payloads
            if row.get("status") == "failed"
        ),
        "aggregate_file": str(output_dir / "aggregate_results.json"),
    }
    _atomic_write_json(manifest_path, final_manifest)
    return {
        "status": final_manifest["status"],
        "output_dir": str(output_dir),
        "manifest": final_manifest,
        "aggregate": aggregate,
        "failures": failures,
        "results": result_payloads,
    }


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    encoded = (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    )
    Path(path).write_text(encoded, encoding="utf-8")


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the frozen v2 clustering configurations on external dataV2."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--reports", type=Path, default=DEFAULT_REPORTS)
    mode.add_argument(
        "--all-runs",
        action="store_true",
        help="run every run_NNN directory under --data-root",
    )
    parser.add_argument("--truth", type=Path, default=DEFAULT_TRUTH)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--expected-runs", type=int, default=DEFAULT_EXPECTED_RUNS)
    parser.add_argument("--resume", dest="resume", action="store_true", default=True)
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    arguments = parser.parse_args(argv)
    if arguments.all_runs:
        if arguments.output is not None:
            parser.error("--output is only valid for the legacy single-run mode")
        if arguments.truth != DEFAULT_TRUTH:
            parser.error("--truth is only valid for the legacy single-run mode")
        output_dir = arguments.output_dir or (
            Path(arguments.data_root) / "results" / "external_sanity"
        )
        report = run_external_batch(
            data_root=arguments.data_root,
            output_dir=output_dir,
            expected_runs=arguments.expected_runs,
            random_state=arguments.random_state,
            selection_path=arguments.selection,
            resume=arguments.resume,
        )
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "output_dir": report["output_dir"],
                    "n_success": report["aggregate"]["n_success"],
                    "n_failures": report["aggregate"]["n_failures"],
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if report["status"] == "completed" else 2
    report = run_external_benchmark(
        reports_path=arguments.reports,
        truth_path=arguments.truth,
        selection_path=arguments.selection,
        random_state=arguments.random_state,
    )
    if arguments.output is None:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _write_json(arguments.output, report)
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "output": str(arguments.output),
                    "output_sha256": file_sha256(arguments.output),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through the CLI
    raise SystemExit(_main())


__all__ = [
    "DEFAULT_DATA_ROOT",
    "DEFAULT_EXPECTED_RUNS",
    "DEFAULT_REPORTS",
    "DEFAULT_RUN_ROOT",
    "DEFAULT_SELECTION",
    "DEFAULT_TRUTH",
    "ExternalAnnotationV2",
    "ExternalBenchmarkError",
    "ExternalDatasetV2",
    "METHOD_ORDER",
    "aggregate_batch_results",
    "bootstrap_paired_delta",
    "dataset_audit",
    "duplicate_audit",
    "file_sha256",
    "load_external_run",
    "load_external_dataset",
    "run_external_batch",
    "run_external_benchmark",
]
