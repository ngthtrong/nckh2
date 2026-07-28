"""Locked development/calibration protocol exposed to tuning code.

The public object returned by :func:`load_tuning_protocol` intentionally has
no test-seed field.  Test-seed release is implemented in the separate
``evaluation_protocol`` module and requires a matching Gate-2 lock file.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping


DEMO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL_DIR = DEMO_ROOT / "protocol"
SEED_MANIFEST_NAME = "seed_manifest.json"
METRIC_CONTRACT_NAME = "metric_contract.json"
MAX_CANDIDATES_PER_METHOD_TRACK = 128


class ProtocolError(ValueError):
    """Raised when a locked protocol file or a tuning request is invalid."""


@dataclass(frozen=True)
class TrackSpec:
    """One preregistered calibration track."""

    id: str
    calibration_labels: bool
    constraints: tuple[str, ...]


@dataclass(frozen=True)
class TuningProtocol:
    """The deliberately restricted protocol view available to tuners."""

    development_seeds: tuple[int, ...]
    calibration_seeds: tuple[int, ...]
    tracks: tuple[TrackSpec, ...]
    max_candidates_per_method_track: int
    seed_manifest_sha256: str
    metric_contract_sha256: str
    protocol_sha256: str

    def seeds_for(
        self, stage: Literal["development", "calibration"]
    ) -> tuple[int, ...]:
        """Return a tuning split; no evaluation split is accepted."""

        if stage == "development":
            return self.development_seeds
        if stage == "calibration":
            return self.calibration_seeds
        raise ProtocolError(
            "tuning may request only 'development' or 'calibration' seeds"
        )

    def validate_candidate_count(self, count: int) -> None:
        """Enforce the symmetric per-method, per-track search budget."""

        if isinstance(count, bool) or not isinstance(count, int):
            raise ProtocolError("candidate count must be an integer")
        if not 1 <= count <= self.max_candidates_per_method_track:
            raise ProtocolError(
                "candidate count must be between 1 and "
                f"{self.max_candidates_per_method_track}; got {count}"
            )


def _load_json(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProtocolError(f"missing locked protocol file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"invalid JSON in locked protocol file: {path}") from exc
    if not isinstance(value, dict):
        raise ProtocolError(f"protocol file must contain a JSON object: {path}")
    return value


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of a protocol source file."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def protocol_bundle_sha256(
    seed_manifest_path: Path, metric_contract_path: Path
) -> str:
    """Hash every JSON protocol member without depending on path location.

    The seed and metric files are mandatory.  Other frozen members (for
    example ``baselines.json``) automatically become part of the Gate-2 hash.
    """

    if seed_manifest_path.parent != metric_contract_path.parent:
        raise ProtocolError("locked protocol members must share one directory")
    required = (seed_manifest_path, metric_contract_path)
    for path in required:
        if not path.is_file():
            raise ProtocolError(f"missing locked protocol file: {path}")
    members = {
        path.name: file_sha256(path)
        for path in sorted(seed_manifest_path.parent.glob("*.json"))
        if path.is_file()
    }
    if SEED_MANIFEST_NAME not in members or METRIC_CONTRACT_NAME not in members:
        raise ProtocolError("protocol bundle is missing a required member")
    encoded = json.dumps(
        members, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _integer_seed_tuple(value: Any, split: str) -> tuple[int, ...]:
    if not isinstance(value, list) or any(
        isinstance(seed, bool) or not isinstance(seed, int) for seed in value
    ):
        raise ProtocolError(f"split {split!r} must be a list of integer seeds")
    result = tuple(value)
    if len(result) != len(set(result)):
        raise ProtocolError(f"split {split!r} contains duplicate seeds")
    return result


def _validate_seed_manifest(
    manifest: Mapping[str, Any],
) -> tuple[tuple[int, ...], tuple[int, ...], tuple[TrackSpec, ...], int]:
    if manifest.get("schema_version") != 1:
        raise ProtocolError("unsupported seed-manifest schema")
    splits = manifest.get("splits")
    expected = manifest.get("expected_counts")
    if not isinstance(splits, dict) or not isinstance(expected, dict):
        raise ProtocolError("seed manifest requires splits and expected_counts")

    required = ("development", "calibration", "test")
    parsed = {
        name: _integer_seed_tuple(splits.get(name), name) for name in required
    }
    for name in required:
        if expected.get(name) != len(parsed[name]):
            raise ProtocolError(
                f"split {name!r} has {len(parsed[name])} seeds, "
                f"expected {expected.get(name)!r}"
            )
    if (
        len(parsed["development"]) != 20
        or len(parsed["calibration"]) != 20
        or len(parsed["test"]) != 40
    ):
        raise ProtocolError("locked split counts must be 20 development/20 calibration/40 test")
    if not manifest.get("disjoint_required"):
        raise ProtocolError("seed manifest must require disjoint splits")
    if (
        set(parsed["development"]) & set(parsed["calibration"])
        or set(parsed["development"]) & set(parsed["test"])
        or set(parsed["calibration"]) & set(parsed["test"])
    ):
        raise ProtocolError("development, calibration, and test seeds must be disjoint")

    tuning = manifest.get("tuning")
    if not isinstance(tuning, dict):
        raise ProtocolError("seed manifest requires a tuning object")
    budget = tuning.get("max_candidate_configurations_per_method_per_track")
    if budget != MAX_CANDIDATES_PER_METHOD_TRACK:
        raise ProtocolError(
            f"locked tuning budget must be {MAX_CANDIDATES_PER_METHOD_TRACK}"
        )
    raw_tracks = tuning.get("tracks")
    if not isinstance(raw_tracks, list) or len(raw_tracks) != 2:
        raise ProtocolError("exactly two preregistered tuning tracks are required")
    tracks: list[TrackSpec] = []
    for raw in raw_tracks:
        if not isinstance(raw, dict):
            raise ProtocolError("each tuning track must be an object")
        identifier = raw.get("id")
        labels = raw.get("calibration_labels")
        constraints = raw.get("constraints")
        if (
            not isinstance(identifier, str)
            or not identifier
            or not isinstance(labels, bool)
            or not isinstance(constraints, list)
            or not constraints
            or any(not isinstance(item, str) or not item for item in constraints)
        ):
            raise ProtocolError(f"invalid tuning track: {raw!r}")
        tracks.append(TrackSpec(identifier, labels, tuple(constraints)))
    if len({track.id for track in tracks}) != len(tracks):
        raise ProtocolError("tuning-track identifiers must be unique")

    # The evaluation split is deliberately validated but not returned.
    return parsed["development"], parsed["calibration"], tuple(tracks), budget


def _validate_metric_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != 1:
        raise ProtocolError("unsupported metric-contract schema")
    families = contract.get("co_primary_families")
    if not isinstance(families, list) or not families:
        raise ProtocolError("metric contract requires co-primary families")
    family_ids: set[str] = set()
    endpoint_ids: set[str] = set()
    for family in families:
        if not isinstance(family, dict):
            raise ProtocolError("co-primary family must be an object")
        family_id = family.get("id")
        if not isinstance(family_id, str) or not family_id:
            raise ProtocolError("co-primary family requires an id")
        if family_id in family_ids:
            raise ProtocolError(f"duplicate co-primary family: {family_id}")
        family_ids.add(family_id)
        multiplicity = family.get("multiplicity")
        if (
            not isinstance(multiplicity, dict)
            or multiplicity.get("procedure") != "holm"
            or multiplicity.get("alpha") != 0.05
        ):
            raise ProtocolError(
                f"family {family_id!r} must preregister Holm correction at alpha=0.05"
            )
        endpoints = family.get("endpoints")
        if not isinstance(endpoints, list) or not endpoints:
            raise ProtocolError(f"family {family_id!r} has no endpoints")
        for endpoint in endpoints:
            if not isinstance(endpoint, dict):
                raise ProtocolError("endpoint must be an object")
            endpoint_id = endpoint.get("id")
            direction = endpoint.get("direction")
            if not isinstance(endpoint_id, str) or not endpoint_id:
                raise ProtocolError("endpoint requires an id")
            if endpoint_id in endpoint_ids:
                raise ProtocolError(f"duplicate co-primary endpoint: {endpoint_id}")
            endpoint_ids.add(endpoint_id)
            if direction not in {"higher", "lower"}:
                raise ProtocolError(
                    f"endpoint {endpoint_id!r} requires a declared direction"
                )
            if endpoint.get("denominator_required") is not True:
                raise ProtocolError(
                    f"co-primary endpoint {endpoint_id!r} must report its denominator"
                )
    inference = contract.get("inference")
    if (
        not isinstance(inference, dict)
        or inference.get("multiplicity_procedure") != "holm"
        or inference.get("confidence_interval") != "paired bootstrap"
        or inference.get("hypothesis_test") != "paired Wilcoxon signed-rank"
    ):
        raise ProtocolError("metric contract inference policy is incomplete")


def load_tuning_protocol(
    protocol_dir: Path | str = DEFAULT_PROTOCOL_DIR,
) -> TuningProtocol:
    """Load and validate the restricted development/calibration protocol."""

    directory = Path(protocol_dir)
    seed_path = directory / SEED_MANIFEST_NAME
    metric_path = directory / METRIC_CONTRACT_NAME
    seed_manifest = _load_json(seed_path)
    metric_contract = _load_json(metric_path)
    development, calibration, tracks, budget = _validate_seed_manifest(seed_manifest)
    _validate_metric_contract(metric_contract)
    return TuningProtocol(
        development_seeds=development,
        calibration_seeds=calibration,
        tracks=tracks,
        max_candidates_per_method_track=budget,
        seed_manifest_sha256=file_sha256(seed_path),
        metric_contract_sha256=file_sha256(metric_path),
        protocol_sha256=protocol_bundle_sha256(seed_path, metric_path),
    )


__all__ = [
    "MAX_CANDIDATES_PER_METHOD_TRACK",
    "ProtocolError",
    "TrackSpec",
    "TuningProtocol",
    "file_sha256",
    "load_tuning_protocol",
    "protocol_bundle_sha256",
]
