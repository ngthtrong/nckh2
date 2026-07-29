"""Deterministic development/calibration engine used before Gate 2.

This module intentionally imports only the restricted tuning protocol.  It has
no evaluation-seed release path and accepts only the two stages exposed by
``TuningProtocol.seeds_for``.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, Sequence

import numpy as np
from sklearn.metrics import adjusted_rand_score

from demo.experiments.inference import (
    apply_holm as _apply_holm,
    bootstrap_mean_ci as _bootstrap_mean_ci,
    holm_adjust as _shared_holm_adjust,
    paired_comparison as _paired_comparison,
)
from demo.experiments.protocol import (
    DEFAULT_PROTOCOL_DIR,
    ProtocolError,
    TuningProtocol,
    file_sha256,
    load_tuning_protocol,
)
from demo.pipeline.attributes import Event, compute_confidence
from demo.pipeline.config import DEFAULT_CONFIG
from demo.pipeline.metrics import ReviewPolicy, operator_review_burden


Stage = Literal["development", "calibration"]
Direction = Literal["higher", "lower"]
MetricRow = Mapping[str, float | int]
Evaluator = Callable[[Mapping[str, Any], int], MetricRow]

MATCHED_RETAINED_FRACTION_TOLERANCE = 0.01
MATCHED_MEAN_DEGREE_RELATIVE_TOLERANCE = 0.05
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GATE1_LOCK = REPOSITORY_ROOT / "revision" / "gate1-lock.json"
DEFAULT_CALIBRATION_CONTRACT = (
    DEFAULT_PROTOCOL_DIR / "calibration_contract.json"
)


@dataclass(frozen=True)
class OperationalCalibrationContract:
    """Strict machine-readable policy used by both calibration tracks."""

    review_policy: ReviewPolicy
    minimum_partition_stability: float
    maximum_review_rate: float
    maximum_geographic_diameter_m: float
    maximum_disconnected_communities: int
    minimum_retained_fraction: float
    maximum_retained_fraction: float
    retained_fraction_match_tolerance: float
    mean_degree_match_relative_tolerance: float
    objectives: Mapping[str, tuple[str, Direction]]
    source_sha256: str


def load_calibration_contract(
    path: Path | str = DEFAULT_CALIBRATION_CONTRACT,
) -> OperationalCalibrationContract:
    """Load numeric selection rules frozen as a protocol-bundle member."""

    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ProtocolError("calibration contract is absent or invalid") from exc
    try:
        if not isinstance(value, dict):
            raise TypeError("top-level contract must be an object")
        selection = value["selection"]
        stability = value["stability"]
        review = value["review_policy"]
        geography = value["geographic_constraint"]
        graph = value["graph_constraints"]
        matched = value["matched_composition_constraints"]
        if not all(
            isinstance(section, dict)
            for section in (
                selection,
                stability,
                review,
                geography,
                graph,
                matched,
            )
        ):
            raise TypeError("calibration contract sections must be objects")

        def finite_number(section: Mapping[str, Any], key: str) -> float:
            raw = section[key]
            if isinstance(raw, bool) or not isinstance(
                raw,
                (int, float),
            ):
                raise TypeError(f"{key} must be numeric")
            result = float(raw)
            if not math.isfinite(result):
                raise ValueError(f"{key} must be finite")
            return result

        review_unclustered = review["review_unclustered"]
        if not isinstance(review_unclustered, bool):
            raise TypeError("review_unclustered must be Boolean")
        raw_min_reports = review["min_destination_reports"]
        if isinstance(raw_min_reports, bool) or not isinstance(raw_min_reports, int):
            raise TypeError("min_destination_reports must be an integer")
        raw_max_disconnected = graph[
            "maximum_disconnected_communities_per_seed"
        ]
        if isinstance(raw_max_disconnected, bool) or not isinstance(
            raw_max_disconnected,
            int,
        ):
            raise TypeError(
                "maximum_disconnected_communities_per_seed must be an integer"
            )
        if not isinstance(review["id"], str) or not review["id"]:
            raise TypeError("review policy id must be a non-empty string")
        objectives = {
            track: (
                selection[track]["objective"],
                selection[track]["direction"],
            )
            for track in (
                "benchmark_label_aware",
                "operational_label_free",
            )
        }
        if any(
            not isinstance(objective, str)
            or not objective
            or direction not in {"higher", "lower"}
            for objective, direction in objectives.values()
        ):
            raise TypeError("calibration objectives/directions are invalid")
        contract = OperationalCalibrationContract(
            review_policy=ReviewPolicy(
                id=review["id"],
                min_destination_reports=raw_min_reports,
                min_mean_confidence=finite_number(
                    review,
                    "min_mean_confidence",
                ),
                review_unclustered=review_unclustered,
            ),
            minimum_partition_stability=finite_number(
                stability,
                "minimum_per_seed",
            ),
            maximum_review_rate=finite_number(
                review,
                "maximum_rate_per_seed",
            ),
            maximum_geographic_diameter_m=finite_number(
                geography,
                "maximum_metres_per_seed",
            ),
            maximum_disconnected_communities=raw_max_disconnected,
            minimum_retained_fraction=finite_number(
                graph,
                "minimum_retained_fraction_per_seed",
            ),
            maximum_retained_fraction=finite_number(
                graph,
                "maximum_retained_fraction_per_seed",
            ),
            retained_fraction_match_tolerance=finite_number(
                matched,
                "retained_fraction_absolute_tolerance",
            ),
            mean_degree_match_relative_tolerance=finite_number(
                matched,
                "mean_degree_relative_tolerance",
            ),
            objectives=objectives,
            source_sha256=file_sha256(source),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ProtocolError("calibration contract fields are malformed") from exc
    if (
        value.get("schema_version") != "calibration-contract-v1"
        or not 0.0 <= contract.minimum_partition_stability <= 1.0
        or not 0.0 <= contract.maximum_review_rate <= 1.0
        or not math.isfinite(contract.minimum_partition_stability)
        or not math.isfinite(contract.maximum_review_rate)
        or not math.isfinite(contract.maximum_geographic_diameter_m)
        or contract.maximum_geographic_diameter_m <= 0.0
        or contract.maximum_disconnected_communities < 0
        or not 0.0 <= contract.minimum_retained_fraction
        <= contract.maximum_retained_fraction
        <= 1.0
        or not math.isfinite(contract.minimum_retained_fraction)
        or not math.isfinite(contract.maximum_retained_fraction)
        or contract.retained_fraction_match_tolerance
        != MATCHED_RETAINED_FRACTION_TOLERANCE
        or contract.mean_degree_match_relative_tolerance
        != MATCHED_MEAN_DEGREE_RELATIVE_TOLERANCE
    ):
        raise ProtocolError("calibration contract violates locked domains")
    return contract


@dataclass(frozen=True)
class TuningDataset:
    """One frozen tuning split with inference and evaluator views separated."""

    seed: int
    stage: Stage
    events: tuple[Event, ...]
    ground_truth: tuple[int, ...] | None
    incidents: tuple[Mapping[str, Any], ...]
    source_sha256: str
    manifest_sha256: str


def _locked_tuning_entry_sha256(
    raw_manifest: bytes,
    *,
    stage: Stage,
    seed: int,
) -> str:
    """Extract one allowed entry without deserializing unrelated split entries."""

    target = (
        f'"path":"{stage}/seed_{seed}.json"'.encode("ascii")
    )
    position = raw_manifest.find(target)
    if position < 0 or raw_manifest.find(target, position + 1) >= 0:
        raise ValueError(f"frozen manifest has no unique entry for {stage}/{seed}")
    # The Gate-1 manifest is canonical JSON with sorted keys.  In each entry,
    # path precedes quality and the terminal fields are seed, sha256, split.
    tail = raw_manifest[position:]
    terminal = re.search(
        (
            rb',"seed":'
            + str(seed).encode("ascii")
            + rb',"sha256":"([0-9a-f]{64})","split":"'
            + stage.encode("ascii")
            + rb'"\}'
        ),
        tail,
    )
    if terminal is None:
        raise ValueError(f"frozen manifest entry is malformed for {stage}/{seed}")
    return terminal.group(1).decode("ascii")


def _gate1_dataset_binding(
    dataset_root: Path,
    *,
    stage: Stage,
    seed: int,
    gate1_lock: Path,
) -> tuple[str, str]:
    try:
        lock = json.loads(gate1_lock.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ProtocolError("a valid Gate-1 lock is required for tuning data") from exc
    data_contract = lock.get("data_contract")
    if (
        lock.get("gate") != "Gate 1"
        or lock.get("status") != "locked"
        or not isinstance(data_contract, dict)
        or not isinstance(data_contract.get("dataset_manifest_sha256"), str)
    ):
        raise ProtocolError("Gate-1 data contract is not locked")

    manifest_path = dataset_root / "manifest.json"
    try:
        raw_manifest = manifest_path.read_bytes()
    except FileNotFoundError as exc:
        raise ProtocolError("frozen dataset root has no manifest.json") from exc
    observed_manifest_sha = hashlib.sha256(raw_manifest).hexdigest()
    if observed_manifest_sha != data_contract["dataset_manifest_sha256"]:
        raise ProtocolError("frozen dataset manifest does not match Gate-1 lock")
    entry_sha = _locked_tuning_entry_sha256(
        raw_manifest,
        stage=stage,
        seed=seed,
    )
    return observed_manifest_sha, entry_sha


def load_tuning_dataset(
    dataset_root: Path | str,
    *,
    stage: Stage,
    seed: int,
    tuning_protocol: TuningProtocol | None = None,
    calibration_labels: bool = False,
    gate1_lock: Path | str = DEFAULT_GATE1_LOCK,
) -> TuningDataset:
    """Load exactly one allowed frozen dataset without traversing other splits."""

    locked = tuning_protocol or load_tuning_protocol()
    allowed = locked.seeds_for(stage)
    if isinstance(seed, bool) or not isinstance(seed, int) or seed not in allowed:
        raise ProtocolError(f"seed {seed!r} is not registered for tuning stage {stage!r}")
    root = Path(dataset_root)
    manifest_sha, expected_source_sha = _gate1_dataset_binding(
        root,
        stage=stage,
        seed=seed,
        gate1_lock=Path(gate1_lock),
    )
    source = root / stage / f"seed_{seed}.json"
    payload = source.read_bytes()
    observed_source_sha = hashlib.sha256(payload).hexdigest()
    if observed_source_sha != expected_source_sha:
        raise ProtocolError(
            f"frozen dataset checksum mismatch for {stage}/{seed}"
        )
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid frozen dataset JSON: {source}") from exc
    if (
        not isinstance(data, dict)
        or data.get("seed") != seed
        or data.get("split") != stage
        or not isinstance(data.get("reports"), list)
        or not isinstance(data.get("incidents"), list)
    ):
        raise ValueError(f"frozen dataset identity does not match {stage}/{seed}")

    events: list[Event] = []
    truth: list[int] | None = [] if calibration_labels else None
    for index, full_report in enumerate(data["reports"]):
        if not isinstance(full_report, dict):
            raise ValueError(f"report {index} is not an object")
        try:
            event = Event(
                event_id=str(full_report["event_id"]),
                lat=float(full_report["lat"]),
                lng=float(full_report["lng"]),
                created_at=datetime.fromisoformat(str(full_report["created_at"])),
                flood=float(full_report["flood"]),
                urgency=float(full_report["urgency"]),
                n_trapped=int(full_report["n_trapped"]),
                vulnerability=float(full_report["vulnerability"]),
                has_image=bool(full_report["has_image"]),
                source_type=str(full_report["source_type"]),
                province=str(full_report["province"]),
                note=str(full_report["note"]),
                missing_fields=tuple(full_report["missing_fields"]),
                # Evaluation truth is never attached to the inference object.
                gt_cluster=-1,
                is_fake=False,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"report {index} has an invalid observable view") from exc
        events.append(event)
        if truth is not None:
            evaluation = full_report.get("evaluation_only")
            if not isinstance(evaluation, dict):
                raise ValueError(f"report {index} has no evaluator view")
            gt_value = evaluation.get("gt_cluster")
            if gt_value is not None and (
                isinstance(gt_value, bool) or not isinstance(gt_value, int)
            ):
                raise ValueError(f"report {index} has invalid evaluator label")
            truth.append(-1 if gt_value is None else gt_value)
    compute_confidence(events, DEFAULT_CONFIG.confidence)
    return TuningDataset(
        seed=seed,
        stage=stage,
        events=tuple(events),
        ground_truth=None if truth is None else tuple(truth),
        incidents=tuple(data["incidents"]) if calibration_labels else (),
        source_sha256=observed_source_sha,
        manifest_sha256=manifest_sha,
    )


def operational_calibration_metrics(
    events: Sequence[Event],
    labels: Sequence[int],
    reverse_order_labels: Sequence[int],
    *,
    noise_label: int | None,
    contract: OperationalCalibrationContract | None = None,
) -> dict[str, float]:
    """Return one common label-free stability/workload convention.

    ``reverse_order_labels`` are predictions made on ``reversed(events)``.
    They are mapped back before partition agreement is measured; no evaluator
    label or incident identity is consumed.
    """

    locked = contract or load_calibration_contract()
    if (
        len(events) != len(labels)
        or len(events) != len(reverse_order_labels)
    ):
        raise ValueError("events and both prediction vectors must have equal length")
    mapped_reverse = list(reversed(reverse_order_labels))
    stability = (
        float(adjusted_rand_score(list(labels), mapped_reverse))
        if events
        else 1.0
    )
    review = operator_review_burden(
        labels,
        [float(event.confidence) for event in events],
        locked.review_policy,
        noise_label=noise_label,
    )
    rate = review["rate"]
    if rate is None:
        raise ValueError("operator review burden has no emitted-unit denominator")
    return {
        "partition_stability": stability,
        "operator_review_burden": float(review["queue_size"]),
        "operator_review_burden_rate": float(rate),
        "operator_review_burden_denominator": float(review["denominator"]),
    }


def canonical_config_json(config: Mapping[str, Any]) -> str:
    """Canonical JSON encoding used for config identity and tie-breaking."""

    try:
        encoded = json.dumps(
            dict(config),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("configuration must be finite JSON data") from exc
    decoded = json.loads(encoded)
    if not isinstance(decoded, dict):
        raise ValueError("configuration must be a JSON object")
    return encoded


def config_sha256(config: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_config_json(config).encode("ascii")).hexdigest()


def configuration_complexity(config: Mapping[str, Any]) -> int:
    """Count active leaves; used only after objective and burden ties."""

    def count(value: Any) -> int:
        if isinstance(value, Mapping):
            return sum(count(nested) for nested in value.values())
        if isinstance(value, (list, tuple)):
            return sum(count(nested) for nested in value)
        if value in (None, False, 0, 0.0, ""):
            return 0
        return 1

    return count(dict(config))


def expand_search_space(
    search_space: Mapping[str, Sequence[Any]],
    *,
    maximum: int = 128,
) -> list[dict[str, Any]]:
    """Expand a finite registry grid in a path/order-independent way."""

    if isinstance(maximum, bool) or not isinstance(maximum, int) or maximum < 1:
        raise ValueError("maximum must be a positive integer")
    keys = sorted(search_space)
    value_lists: list[tuple[Any, ...]] = []
    for key in keys:
        values = search_space[key]
        if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
            raise ValueError(f"search-space axis {key!r} must be a finite sequence")
        axis = tuple(values)
        if not axis:
            raise ValueError(f"search-space axis {key!r} is empty")
        value_lists.append(axis)
    count = math.prod(len(axis) for axis in value_lists)
    if not 1 <= count <= maximum:
        raise ProtocolError(
            f"grid has {count} configurations; allowed range is 1..{maximum}"
        )
    configs = [
        {key: value for key, value in zip(keys, values, strict=True)}
        for values in itertools.product(*value_lists)
    ]
    hashes = [config_sha256(config) for config in configs]
    if len(hashes) != len(set(hashes)):
        raise ValueError("search space contains duplicate canonical configurations")
    return sorted(configs, key=config_sha256)


@dataclass(frozen=True)
class SeedFailure:
    seed: int
    exception_type: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "exception_type": self.exception_type,
            "message": self.message,
        }


@dataclass(frozen=True)
class CandidateEvaluation:
    method_id: str
    track_id: str
    stage: Stage
    config: Mapping[str, Any]
    config_sha256: str
    status: Literal["succeeded", "failed"]
    seed_metrics: tuple[Mapping[str, float], ...]
    aggregate_metrics: Mapping[str, float]
    failures: tuple[SeedFailure, ...]
    configuration_evaluation_count: int
    seed_run_count: int
    wall_time_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "method_id": self.method_id,
            "track_id": self.track_id,
            "stage": self.stage,
            "config": dict(self.config),
            "config_sha256": self.config_sha256,
            "status": self.status,
            "seed_metrics": [dict(row) for row in self.seed_metrics],
            "aggregate_metrics": dict(self.aggregate_metrics),
            "failures": [failure.to_dict() for failure in self.failures],
            "configuration_evaluation_count": self.configuration_evaluation_count,
            "seed_run_count": self.seed_run_count,
            "wall_time_seconds": round(self.wall_time_seconds, 6),
        }


_LABEL_AWARE_TOKENS = (
    "ari",
    "nmi",
    "ground_truth",
    "latent",
    "incident_split",
    "incident_merge",
)


def _validate_metric_row(
    row: MetricRow,
    *,
    calibration_labels: bool,
) -> dict[str, float]:
    if not isinstance(row, Mapping) or not row:
        raise ValueError("evaluator must return a non-empty metric mapping")
    normalized: dict[str, float] = {}
    for name, raw_value in row.items():
        if not isinstance(name, str) or not name:
            raise ValueError("metric names must be non-empty strings")
        if not calibration_labels and any(
            token in name.casefold() for token in _LABEL_AWARE_TOKENS
        ):
            raise ProtocolError(
                f"label-free track cannot receive label-aware metric {name!r}"
            )
        if isinstance(raw_value, bool) or not isinstance(
            raw_value, (int, float, np.integer, np.floating)
        ):
            raise ValueError(f"metric {name!r} must be numeric")
        value = float(raw_value)
        if not math.isfinite(value):
            raise ValueError(f"metric {name!r} must be finite")
        normalized[name] = value
    return normalized


def _aggregate_seed_metrics(
    rows: Sequence[Mapping[str, float]],
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


def aggregate_seed_metrics(
    rows: Sequence[Mapping[str, float]],
) -> dict[str, float]:
    """Recompute the exact aggregate representation stored in artifacts."""

    return _aggregate_seed_metrics(rows)


def evaluate_candidates(
    method_id: str,
    track_id: str,
    stage: Stage,
    configs: Sequence[Mapping[str, Any]],
    evaluator: Evaluator,
    *,
    tuning_protocol: TuningProtocol | None = None,
    seed_limit: int | None = None,
) -> list[CandidateEvaluation]:
    """Evaluate a complete grid and retain every exception as a result row."""

    locked = tuning_protocol or load_tuning_protocol()
    locked.validate_candidate_count(len(configs))
    tracks = {track.id: track for track in locked.tracks}
    if track_id not in tracks:
        raise ProtocolError(f"unknown tuning track: {track_id!r}")
    seeds = locked.seeds_for(stage)
    if seed_limit is not None:
        if (
            isinstance(seed_limit, bool)
            or not isinstance(seed_limit, int)
            or not 1 <= seed_limit <= len(seeds)
        ):
            raise ValueError("seed_limit must select a non-empty tuning prefix")
        seeds = seeds[:seed_limit]

    canonical_hashes = [config_sha256(config) for config in configs]
    if len(canonical_hashes) != len(set(canonical_hashes)):
        raise ValueError("candidate list contains duplicate configurations")

    evaluations: list[CandidateEvaluation] = []
    for config in sorted(configs, key=config_sha256):
        started = time.perf_counter()
        rows: list[Mapping[str, float]] = []
        failures: list[SeedFailure] = []
        for seed in seeds:
            try:
                metrics = evaluator(dict(config), seed)
                normalized = _validate_metric_row(
                    metrics,
                    calibration_labels=tracks[track_id].calibration_labels,
                )
                rows.append({"seed": float(seed), **normalized})
            except Exception as exc:  # Every adverse/failure outcome is retained.
                failures.append(
                    SeedFailure(
                        seed=seed,
                        exception_type=type(exc).__name__,
                        message=str(exc),
                    )
                )
        duration = time.perf_counter() - started
        evaluations.append(
            CandidateEvaluation(
                method_id=method_id,
                track_id=track_id,
                stage=stage,
                config=dict(config),
                config_sha256=config_sha256(config),
                status="failed" if failures else "succeeded",
                seed_metrics=tuple(rows),
                aggregate_metrics=_aggregate_seed_metrics(rows),
                failures=tuple(failures),
                configuration_evaluation_count=1,
                seed_run_count=len(seeds),
                wall_time_seconds=duration,
            )
        )
    return evaluations


@dataclass(frozen=True)
class MetricConstraint:
    metric: str
    operator: Literal["<=", ">="]
    limit: float

    def violation(self, metrics: Mapping[str, float]) -> str | None:
        if self.metric not in metrics:
            return f"missing metric {self.metric}"
        value = metrics[self.metric]
        feasible = value <= self.limit if self.operator == "<=" else value >= self.limit
        if feasible:
            return None
        return f"{self.metric}={value} violates {self.operator}{self.limit}"


def operational_selection_constraints(
    contract: OperationalCalibrationContract,
    *,
    graph_method: bool,
) -> tuple[MetricConstraint, ...]:
    """Translate the frozen per-seed guardrails to aggregate extrema."""

    common = (
        MetricConstraint(
            "partition_stability__min",
            ">=",
            contract.minimum_partition_stability,
        ),
        MetricConstraint(
            "operator_review_burden_rate__max",
            "<=",
            contract.maximum_review_rate,
        ),
        MetricConstraint(
            "geographic_diameter__max",
            "<=",
            contract.maximum_geographic_diameter_m,
        ),
    )
    if not graph_method:
        return common
    return (
        *common,
        MetricConstraint(
            "disconnected_communities__max",
            "<=",
            float(contract.maximum_disconnected_communities),
        ),
        MetricConstraint(
            "retained_fraction__min",
            ">=",
            contract.minimum_retained_fraction,
        ),
        MetricConstraint(
            "retained_fraction__max",
            "<=",
            contract.maximum_retained_fraction,
        ),
    )


@dataclass(frozen=True)
class CalibrationSelection:
    method_id: str
    track_id: str
    objective: str
    direction: Direction
    status: Literal["selected", "no_feasible_candidate"]
    selected_config: Mapping[str, Any] | None
    selected_config_sha256: str | None
    selection_sha256: str
    considered_configurations: int
    succeeded_configurations: int
    feasible_configurations: int
    rejected: tuple[Mapping[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "method_id": self.method_id,
            "track_id": self.track_id,
            "objective": self.objective,
            "direction": self.direction,
            "status": self.status,
            "selected_config": (
                None if self.selected_config is None else dict(self.selected_config)
            ),
            "selected_config_sha256": self.selected_config_sha256,
            "selection_sha256": self.selection_sha256,
            "considered_configurations": self.considered_configurations,
            "succeeded_configurations": self.succeeded_configurations,
            "feasible_configurations": self.feasible_configurations,
            "rejected": [dict(row) for row in self.rejected],
        }


def _selection_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        dict(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def selection_identity_sha256(
    *,
    method_id: str,
    track_id: str,
    objective: str,
    direction: Direction,
    selected_config_sha256: str | None,
) -> str:
    """Hash exactly the fields that make one calibration choice immutable."""

    return _selection_digest(
        {
            "method_id": method_id,
            "track_id": track_id,
            "objective": objective,
            "direction": direction,
            "selected_config_sha256": selected_config_sha256,
        }
    )


def calibration_artifact_content_sha256(payload: Mapping[str, Any]) -> str:
    """Hash artifact content while excluding its self-authentication field."""

    content = dict(payload)
    content.pop("artifact_content_sha256", None)
    return _selection_digest(content)


def select_candidate(
    evaluations: Sequence[CandidateEvaluation],
    *,
    objective: str,
    direction: Direction,
    constraints: Sequence[MetricConstraint] = (),
    burden_metric: str = "operator_review_burden",
    complexity_metric: str = "complexity",
) -> CalibrationSelection:
    """Select deterministically: objective, burden, complexity, config hash."""

    if direction not in {"higher", "lower"}:
        raise ValueError("direction must be 'higher' or 'lower'")
    if not evaluations:
        raise ValueError("at least one candidate evaluation is required")
    identities = {(row.method_id, row.track_id, row.stage) for row in evaluations}
    if len(identities) != 1:
        raise ValueError("selection rows must share method, track, and stage")
    method_id, track_id, _ = next(iter(identities))

    feasible: list[CandidateEvaluation] = []
    rejected: list[Mapping[str, Any]] = []
    succeeded = 0
    for evaluation in evaluations:
        reasons: list[str] = []
        if evaluation.status != "succeeded":
            reasons.append("seed failure")
        else:
            succeeded += 1
        if objective not in evaluation.aggregate_metrics:
            reasons.append(f"missing objective {objective}")
        reasons.extend(
            reason
            for constraint in constraints
            if (reason := constraint.violation(evaluation.aggregate_metrics)) is not None
        )
        if reasons:
            rejected.append(
                {
                    "config_sha256": evaluation.config_sha256,
                    "reasons": reasons,
                }
            )
        else:
            feasible.append(evaluation)

    def order(evaluation: CandidateEvaluation) -> tuple[Any, ...]:
        metrics = evaluation.aggregate_metrics
        objective_value = metrics[objective]
        primary = -objective_value if direction == "higher" else objective_value
        burden = metrics.get(burden_metric, math.inf)
        complexity = metrics.get(
            complexity_metric,
            float(configuration_complexity(evaluation.config)),
        )
        return primary, burden, complexity, evaluation.config_sha256

    selected = min(feasible, key=order) if feasible else None
    selected_hash = None if selected is None else selected.config_sha256
    return CalibrationSelection(
        method_id=method_id,
        track_id=track_id,
        objective=objective,
        direction=direction,
        status="selected" if selected is not None else "no_feasible_candidate",
        selected_config=None if selected is None else dict(selected.config),
        selected_config_sha256=None if selected is None else selected.config_sha256,
        selection_sha256=selection_identity_sha256(
            method_id=method_id,
            track_id=track_id,
            objective=objective,
            direction=direction,
            selected_config_sha256=selected_hash,
        ),
        considered_configurations=len(evaluations),
        succeeded_configurations=succeeded,
        feasible_configurations=len(feasible),
        rejected=tuple(rejected),
    )


@dataclass(frozen=True)
class GraphDensity:
    n_nodes: int
    n_edges: int
    possible_edges: int
    retained_fraction: float
    mean_degree: float

    def to_dict(self) -> dict[str, float | int]:
        return {
            "n_nodes": self.n_nodes,
            "n_edges": self.n_edges,
            "possible_edges": self.possible_edges,
            "retained_fraction": self.retained_fraction,
            "mean_degree": self.mean_degree,
        }


def graph_density(weights: np.ndarray) -> GraphDensity:
    matrix = np.asarray(weights, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("graph matrix must be square")
    if not np.isfinite(matrix).all() or (matrix < 0.0).any():
        raise ValueError("graph matrix must be finite and non-negative")
    if not np.allclose(matrix, matrix.T, rtol=0.0, atol=1e-12):
        raise ValueError("graph matrix must be symmetric")
    n_nodes = matrix.shape[0]
    possible = n_nodes * (n_nodes - 1) // 2
    n_edges = int(np.count_nonzero(np.triu(matrix, 1) > 0.0))
    return GraphDensity(
        n_nodes=n_nodes,
        n_edges=n_edges,
        possible_edges=possible,
        retained_fraction=(n_edges / possible if possible else 0.0),
        mean_degree=(2.0 * n_edges / n_nodes if n_nodes else 0.0),
    )


def quantile_threshold(weights: np.ndarray, quantile: float) -> float:
    if not math.isfinite(quantile) or not 0.0 <= quantile <= 1.0:
        raise ValueError("quantile must lie in [0, 1]")
    matrix = np.asarray(weights, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("weight matrix must be square")
    values = matrix[np.triu_indices(matrix.shape[0], 1)]
    if values.size == 0:
        return 0.0
    if not np.isfinite(values).all() or (values < 0.0).any():
        raise ValueError("weights must be finite and non-negative")
    return float(np.quantile(values, quantile, method="linear"))


def sparsify_at_quantile(
    weights: np.ndarray,
    threshold_quantile: float,
    *,
    knn: int = 0,
) -> tuple[np.ndarray, float]:
    """Apply the locked strict-threshold/k-NN semantics at a scale-free quantile."""

    from demo.pipeline.config import WeightParams
    from demo.pipeline.weighting import sparsify

    threshold = quantile_threshold(weights, threshold_quantile)
    params = WeightParams(edge_threshold=threshold, knn=knn)
    return sparsify(np.asarray(weights, dtype=float), params), threshold


def density_match_diagnostics(
    reference: GraphDensity | Mapping[str, float],
    candidate: GraphDensity | Mapping[str, float],
) -> dict[str, float | bool]:
    def value(source: GraphDensity | Mapping[str, float], name: str) -> float:
        return (
            float(getattr(source, name))
            if isinstance(source, GraphDensity)
            else float(source[name])
        )

    ref_fraction = value(reference, "retained_fraction")
    candidate_fraction = value(candidate, "retained_fraction")
    ref_degree = value(reference, "mean_degree")
    candidate_degree = value(candidate, "mean_degree")
    fraction_error = abs(candidate_fraction - ref_fraction)
    if ref_degree == 0.0:
        degree_error = 0.0 if candidate_degree == 0.0 else math.inf
    else:
        degree_error = abs(candidate_degree - ref_degree) / ref_degree
    matched = (
        fraction_error <= MATCHED_RETAINED_FRACTION_TOLERANCE + 1e-15
        and degree_error <= MATCHED_MEAN_DEGREE_RELATIVE_TOLERANCE + 1e-15
    )
    return {
        "reference_retained_fraction": ref_fraction,
        "candidate_retained_fraction": candidate_fraction,
        "retained_fraction_absolute_error": fraction_error,
        "reference_mean_degree": ref_degree,
        "candidate_mean_degree": candidate_degree,
        "mean_degree_relative_error": degree_error,
        "matched": matched,
    }


@dataclass(frozen=True)
class DensityMatch:
    threshold: float
    knn: int
    density: GraphDensity
    diagnostics: Mapping[str, float | bool]


def find_density_match(
    weights: np.ndarray,
    reference: GraphDensity | Mapping[str, float],
    *,
    knn_candidates: Sequence[int] = (0,),
) -> DensityMatch:
    """Find the closest strict-threshold outcome by monotone edge-count search."""

    from demo.pipeline.config import WeightParams
    from demo.pipeline.weighting import sparsify

    matrix = np.asarray(weights, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("weight matrix must be square")
    upper = matrix[np.triu_indices(matrix.shape[0], 1)]
    thresholds = np.unique(np.concatenate((np.array([0.0]), upper))).tolist()
    valid_knn = sorted(set(knn_candidates))
    if not valid_knn or any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in valid_knn
    ):
        raise ValueError("knn_candidates must contain non-negative integers")

    reference_fraction = (
        float(reference.retained_fraction)
        if isinstance(reference, GraphDensity)
        else float(reference["retained_fraction"])
    )
    target_edges = reference_fraction * (matrix.shape[0] * (matrix.shape[0] - 1) // 2)
    candidates: list[DensityMatch] = []

    def evaluate(knn: int, threshold_index: int) -> DensityMatch:
        threshold = float(thresholds[threshold_index])
        sparse = sparsify(
            matrix,
            WeightParams(edge_threshold=threshold, knn=knn),
        )
        density = graph_density(sparse)
        return DensityMatch(
            threshold=threshold,
            knn=knn,
            density=density,
            diagnostics=density_match_diagnostics(reference, density),
        )

    for knn in valid_knn:
        low, high = 0, len(thresholds) - 1
        visited: set[int] = set()
        while low <= high:
            middle = (low + high) // 2
            row = evaluate(knn, middle)
            candidates.append(row)
            visited.add(middle)
            if row.density.n_edges > target_edges:
                low = middle + 1
            elif row.density.n_edges < target_edges:
                high = middle - 1
            else:
                low = middle + 1
        for index in range(max(0, high - 2), min(len(thresholds), low + 3)):
            if index not in visited:
                candidates.append(evaluate(knn, index))
    return min(
        candidates,
        key=lambda row: (
            float(row.diagnostics["retained_fraction_absolute_error"]),
            float(row.diagnostics["mean_degree_relative_error"]),
            row.knn,
            row.threshold,
        ),
    )


def paired_inference(
    candidate: Sequence[float],
    reference: Sequence[float],
    *,
    direction: Direction,
    bootstrap_samples: int = 5000,
    alpha: float = 0.05,
    random_seed: int = 42,
) -> dict[str, Any]:
    """Compatibility wrapper around the repository-wide inference contract."""

    if direction not in {"higher", "lower"}:
        raise ValueError("direction must be 'higher' or 'lower'")
    first = np.asarray(candidate, dtype=float)
    second = np.asarray(reference, dtype=float)
    if first.ndim != 1 or second.ndim != 1 or first.size != second.size:
        raise ValueError("paired samples must be one-dimensional and equal length")
    if first.size == 0 or not np.isfinite(first).all() or not np.isfinite(second).all():
        raise ValueError("paired samples must be non-empty and finite")
    if (
        isinstance(bootstrap_samples, bool)
        or not isinstance(bootstrap_samples, int)
        or bootstrap_samples < 1
    ):
        raise ValueError("bootstrap_samples must be a positive integer")

    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie strictly between zero and one")
    result = _paired_comparison(
        first,
        second,
        direction=direction,
        denominator=int(first.size),
        bootstrap_seed=random_seed,
    )
    if bootstrap_samples != 5000 or alpha != 0.05:
        favorable = first - second if direction == "higher" else second - first
        result["paired_confidence_interval"] = _bootstrap_mean_ci(
            favorable,
            confidence=1.0 - alpha,
            resamples=bootstrap_samples,
            seed=random_seed,
        )
    result["candidate_mean"] = float(np.mean(first))
    result["reference_mean"] = float(np.mean(second))
    return result


def holm_adjust(
    p_values: Mapping[str, float | None],
) -> dict[str, float | None]:
    """Delegate Holm adjustment to the locked shared inference helper."""

    return _shared_holm_adjust(p_values)


def paired_endpoint_family(
    candidate_rows: Sequence[Mapping[str, Any]],
    comparator_rows: Sequence[Mapping[str, Any]],
    *,
    endpoint_directions: Mapping[str, Direction],
    denominators: Mapping[str, int | float | Mapping[str, int | float]] | None = None,
    seed_key: str = "seed",
    bootstrap_seed: int = 20260729,
) -> dict[str, dict[str, Any]]:
    """Compare a preregistered endpoint family and apply Holm exactly once."""

    def indexed(
        rows: Sequence[Mapping[str, Any]], label: str
    ) -> dict[Any, Mapping[str, Any]]:
        result: dict[Any, Mapping[str, Any]] = {}
        for row in rows:
            if seed_key not in row:
                raise ValueError(f"{label} row has no {seed_key!r}")
            seed = row[seed_key]
            if seed in result:
                raise ValueError(f"{label} contains duplicate seed {seed!r}")
            result[seed] = row
        if not result:
            raise ValueError(f"{label} rows are empty")
        return result

    candidate_by_seed = indexed(candidate_rows, "candidate")
    comparator_by_seed = indexed(comparator_rows, "comparator")
    if set(candidate_by_seed) != set(comparator_by_seed):
        raise ValueError("candidate and comparator seed sets must match exactly")
    seeds = sorted(candidate_by_seed, key=str)
    comparisons: dict[str, Mapping[str, Any]] = {}
    for endpoint, direction in endpoint_directions.items():
        try:
            candidate = [
                float(candidate_by_seed[seed][endpoint]) for seed in seeds
            ]
            comparator = [
                float(comparator_by_seed[seed][endpoint]) for seed in seeds
            ]
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid paired endpoint {endpoint!r}") from exc
        denominator = (
            denominators[endpoint]
            if denominators is not None and endpoint in denominators
            else len(seeds)
        )
        comparisons[endpoint] = _paired_comparison(
            candidate,
            comparator,
            direction=direction,
            denominator=denominator,
            bootstrap_seed=bootstrap_seed,
        )
    return _apply_holm(comparisons)


def factorial_effect_summaries(
    rows: Sequence[Mapping[str, Any]],
    *,
    factors: Sequence[str],
    outcome: str,
    seed_key: str = "seed",
    bootstrap_samples: int = 5000,
    random_seed: int = 42,
) -> list[dict[str, Any]]:
    """Estimate all main and pairwise effects from a complete Boolean factorial."""

    factors = tuple(factors)
    if len(factors) < 1 or len(factors) != len(set(factors)):
        raise ValueError("factors must be unique and non-empty")
    expected_design = set(itertools.product((False, True), repeat=len(factors)))
    by_seed: dict[Any, dict[tuple[bool, ...], float]] = {}
    for row in rows:
        if seed_key not in row or outcome not in row:
            raise ValueError("factorial row is missing seed or outcome")
        design: list[bool] = []
        for factor in factors:
            value = row.get(factor)
            if not isinstance(value, bool):
                raise ValueError(f"factor {factor!r} must be Boolean")
            design.append(value)
        raw_outcome = row[outcome]
        if isinstance(raw_outcome, bool) or not isinstance(
            raw_outcome, (int, float, np.integer, np.floating)
        ):
            raise ValueError("factorial outcome must be numeric")
        numeric = float(raw_outcome)
        if not math.isfinite(numeric):
            raise ValueError("factorial outcome must be finite")
        key = tuple(design)
        seed_rows = by_seed.setdefault(row[seed_key], {})
        if key in seed_rows:
            raise ValueError("duplicate factorial cell for one seed")
        seed_rows[key] = numeric
    if not by_seed:
        raise ValueError("factorial rows are empty")
    for seed, design in by_seed.items():
        if set(design) != expected_design:
            raise ValueError(f"seed {seed!r} does not contain the complete factorial")

    effects: list[dict[str, Any]] = []

    def summarize(
        effect_id: str,
        effect_kind: str,
        involved: tuple[str, ...],
        values: Sequence[float],
        offset: int,
    ) -> None:
        inference = paired_inference(
            values,
            np.zeros(len(values), dtype=float),
            direction="higher",
            bootstrap_samples=bootstrap_samples,
            random_seed=random_seed + offset,
        )
        effects.append(
            {
                "effect_id": effect_id,
                "effect_kind": effect_kind,
                "factors": list(involved),
                **inference,
            }
        )

    sorted_seeds = sorted(by_seed, key=str)
    offset = 0
    for interaction_order in range(1, len(factors) + 1):
        for involved_indices in itertools.combinations(
            range(len(factors)),
            interaction_order,
        ):
            names = tuple(factors[index] for index in involved_indices)
            values = []
            for seed in sorted_seeds:
                design = by_seed[seed]
                contrast = 0.0
                for involved_levels in itertools.product(
                    (False, True),
                    repeat=interaction_order,
                ):
                    selected = [
                        value
                        for cell, value in design.items()
                        if all(
                            cell[index] is level
                            for index, level in zip(
                                involved_indices,
                                involved_levels,
                                strict=True,
                            )
                        )
                    ]
                    coefficient = (
                        -1.0
                        if sum(involved_levels) % 2
                        != interaction_order % 2
                        else 1.0
                    )
                    contrast += coefficient * float(np.mean(selected))
                values.append(contrast)
            if interaction_order == 1:
                effect_id = f"main:{names[0]}"
                effect_kind = "main"
            else:
                effect_id = "interaction:" + ":".join(names)
                effect_kind = f"{interaction_order}_way_interaction"
            summarize(effect_id, effect_kind, names, values, offset)
            offset += 1

    corrected = holm_adjust(
        {row["effect_id"]: row["raw_p_value"] for row in effects}
    )
    for row in effects:
        row["holm_adjusted_p_value"] = corrected[row["effect_id"]]
    return effects


def write_calibration_artifact(
    destination: Path | str,
    *,
    protocol: TuningProtocol,
    evaluations: Sequence[CandidateEvaluation],
    selections: Sequence[CalibrationSelection],
    metadata: Mapping[str, Any] | None = None,
) -> Path:
    """Write a hash-bound artifact without omitting failed/tied candidates."""

    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "calibration-artifact-v1",
        "protocol_sha256": protocol.protocol_sha256,
        "seed_manifest_sha256": protocol.seed_manifest_sha256,
        "metric_contract_sha256": protocol.metric_contract_sha256,
        "configuration_evaluation_count": sum(
            row.configuration_evaluation_count for row in evaluations
        ),
        "seed_run_count": sum(row.seed_run_count for row in evaluations),
        "failed_configuration_count": sum(
            row.status == "failed" for row in evaluations
        ),
        "evaluations": [row.to_dict() for row in evaluations],
        "selections": [row.to_dict() for row in selections],
        "metadata": dict(metadata or {}),
    }
    payload["artifact_content_sha256"] = calibration_artifact_content_sha256(
        payload
    )
    # Apply the same candidate-directory confinement and exclusive write as
    # the other pre-Gate-2 experiments.
    from demo.experiments.pre_gate2 import write_exclusive_json

    return write_exclusive_json(output, payload)


__all__ = [
    "CalibrationSelection",
    "CandidateEvaluation",
    "DensityMatch",
    "GraphDensity",
    "MATCHED_MEAN_DEGREE_RELATIVE_TOLERANCE",
    "MATCHED_RETAINED_FRACTION_TOLERANCE",
    "MetricConstraint",
    "OperationalCalibrationContract",
    "TuningDataset",
    "aggregate_seed_metrics",
    "calibration_artifact_content_sha256",
    "canonical_config_json",
    "config_sha256",
    "density_match_diagnostics",
    "evaluate_candidates",
    "expand_search_space",
    "factorial_effect_summaries",
    "find_density_match",
    "graph_density",
    "holm_adjust",
    "load_tuning_dataset",
    "load_calibration_contract",
    "operational_calibration_metrics",
    "operational_selection_constraints",
    "paired_inference",
    "paired_endpoint_family",
    "quantile_threshold",
    "select_candidate",
    "selection_identity_sha256",
    "SeedFailure",
    "sparsify_at_quantile",
    "write_calibration_artifact",
]
