"""Deterministic, observable-only deduplication and corroboration for v2."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Literal, Sequence

from .contracts import ReportV2, validate_unique_report_ids
from .similarity import haversine_m


def _finite_nonnegative(value: object, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be finite and non-negative") from exc
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")
    return result


def observable_payload(report: ReportV2) -> dict[str, object]:
    """Canonical exact-evidence payload, excluding transport/source identity.

    ``report_id`` and ``source_id`` are intentionally excluded: retransmission
    identifiers are not new evidence.  The broader ``source_family`` and
    observable provenance quality remain because they change the evidential
    provenance represented by a payload.  No evaluator-only type is accepted.
    """

    return {
        "L": None if report.L is None else list(report.L),
        "T": None if report.T is None else report.T.isoformat(),
        "F": report.F,
        "E": report.E,
        "N": report.N,
        "V": report.V,
        "mask": {
            "L": report.mask.L,
            "T": report.mask.T,
            "F": report.mask.F,
            "E": report.mask.E,
            "N": report.mask.N,
            "V": report.mask.V,
        },
        "source_family": report.source_family,
        "provenance_quality": report.provenance_quality,
        "has_image": report.has_image,
    }


def exact_fingerprint(report: ReportV2) -> str:
    """SHA-256 of the canonical inference-visible exact-evidence payload."""

    encoded = (
        json.dumps(
            observable_payload(report),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class NearDuplicatePolicyV2:
    distance_m: float = 100.0
    time_window_min: float = 10.0
    flood_abs: float = 0.10
    urgency_abs: float = 0.10
    n_abs_floor: float = 5.0
    n_relative: float = 0.25
    vulnerability_abs: float = 2.0
    provenance_quality_abs: float = 0.10
    require_same_source_family: bool = True
    require_same_image_state: bool = True

    def __post_init__(self) -> None:
        for name in (
            "distance_m",
            "time_window_min",
            "flood_abs",
            "urgency_abs",
            "n_abs_floor",
            "n_relative",
            "vulnerability_abs",
            "provenance_quality_abs",
        ):
            object.__setattr__(
                self,
                name,
                _finite_nonnegative(getattr(self, name), name),
            )
        if type(self.require_same_source_family) is not bool:
            raise ValueError("require_same_source_family must be boolean")
        if type(self.require_same_image_state) is not bool:
            raise ValueError("require_same_image_state must be boolean")


def _same_nullable_measurement(
    first: float | None,
    second: float | None,
    tolerance: float,
) -> bool:
    if first is None or second is None:
        return first is None and second is None
    return abs(first - second) <= tolerance


def are_near_duplicates(
    first: ReportV2,
    second: ReportV2,
    policy: NearDuplicatePolicyV2 = NearDuplicatePolicyV2(),
) -> bool:
    """Pairwise observable near-duplicate predicate.

    Masks must match exactly; a missing observation is never silently compared
    with a real zero.  L and T are mandatory because a near relation cannot be
    established safely without both.  Source IDs are transport identities and
    are deliberately ignored.
    """

    if not first.graph_eligible or not second.graph_eligible:
        return False
    if first.mask != second.mask:
        return False
    if (
        policy.require_same_source_family
        and first.source_family != second.source_family
    ):
        return False
    if policy.require_same_image_state and first.has_image != second.has_image:
        return False
    if haversine_m(first.L, second.L) > policy.distance_m:
        return False
    delta_min = abs((first.T - second.T).total_seconds()) / 60.0
    if delta_min > policy.time_window_min:
        return False
    if not _same_nullable_measurement(first.F, second.F, policy.flood_abs):
        return False
    if not _same_nullable_measurement(first.E, second.E, policy.urgency_abs):
        return False
    if first.N is not None and second.N is not None:
        n_tolerance = max(
            policy.n_abs_floor,
            policy.n_relative * max(first.N, second.N, 1.0),
        )
        if abs(first.N - second.N) > n_tolerance:
            return False
    elif first.N is not None or second.N is not None:
        return False
    if not _same_nullable_measurement(
        first.V, second.V, policy.vulnerability_abs
    ):
        return False
    if not _same_nullable_measurement(
        first.provenance_quality,
        second.provenance_quality,
        policy.provenance_quality_abs,
    ):
        return False
    return True


@dataclass(frozen=True, slots=True)
class ExactEvidenceUnitV2:
    fingerprint: str
    representative: ReportV2
    report_ids: tuple[str, ...]

    @property
    def multiplicity(self) -> int:
        return len(self.report_ids)


@dataclass(frozen=True, slots=True)
class EvidenceFamilyV2:
    """A complete-link family of exact-evidence units."""

    units: tuple[ExactEvidenceUnitV2, ...]

    @property
    def report_ids(self) -> tuple[str, ...]:
        return tuple(
            report_id
            for unit in self.units
            for report_id in unit.report_ids
        )

    @property
    def representatives(self) -> tuple[ReportV2, ...]:
        return tuple(unit.representative for unit in self.units)


@dataclass(frozen=True, slots=True)
class DeduplicationResultV2:
    exact_units: tuple[ExactEvidenceUnitV2, ...]
    families: tuple[EvidenceFamilyV2, ...]
    exact_duplicates_removed: int
    near_units_coalesced: int


def collapse_exact_duplicates(
    reports: Sequence[ReportV2],
) -> tuple[ExactEvidenceUnitV2, ...]:
    """Collapse exact observable payloads with a deterministic representative."""

    validate_unique_report_ids(reports)
    grouped: dict[str, list[ReportV2]] = {}
    for report in reports:
        grouped.setdefault(exact_fingerprint(report), []).append(report)
    units: list[ExactEvidenceUnitV2] = []
    for fingerprint in sorted(grouped):
        members = sorted(grouped[fingerprint], key=lambda item: item.report_id)
        units.append(
            ExactEvidenceUnitV2(
                fingerprint=fingerprint,
                representative=members[0],
                report_ids=tuple(member.report_id for member in members),
            )
        )
    return tuple(units)


def _cluster_signature(
    cluster: tuple[ExactEvidenceUnitV2, ...],
) -> tuple[str, ...]:
    return tuple(unit.fingerprint for unit in cluster)


def _complete_link_compatible(
    first: tuple[ExactEvidenceUnitV2, ...],
    second: tuple[ExactEvidenceUnitV2, ...],
    policy: NearDuplicatePolicyV2,
) -> bool:
    return all(
        are_near_duplicates(
            left.representative,
            right.representative,
            policy,
        )
        for left in first
        for right in second
    )


def _complete_link_units(
    units: Sequence[ExactEvidenceUnitV2],
    policy: NearDuplicatePolicyV2,
) -> tuple[EvidenceFamilyV2, ...]:
    """Agglomerate only when every cross-pair is near.

    Candidate merges are ordered by the fingerprint signature of their union,
    making the result invariant to input order.  The all-cross-pairs condition
    prevents A~B~C transitive chaining whenever A is not near C.
    """

    clusters: list[tuple[ExactEvidenceUnitV2, ...]] = [
        (unit,) for unit in sorted(units, key=lambda item: item.fingerprint)
    ]
    while True:
        candidates: list[
            tuple[tuple[str, ...], int, int, tuple[ExactEvidenceUnitV2, ...]]
        ] = []
        for left_index in range(len(clusters)):
            for right_index in range(left_index + 1, len(clusters)):
                left = clusters[left_index]
                right = clusters[right_index]
                if not _complete_link_compatible(left, right, policy):
                    continue
                merged = tuple(
                    sorted(left + right, key=lambda item: item.fingerprint)
                )
                candidates.append(
                    (
                        _cluster_signature(merged),
                        left_index,
                        right_index,
                        merged,
                    )
                )
        if not candidates:
            break
        _, left_index, right_index, merged = min(
            candidates, key=lambda item: item[0]
        )
        clusters = [
            cluster
            for index, cluster in enumerate(clusters)
            if index not in (left_index, right_index)
        ]
        clusters.append(merged)
        clusters.sort(key=_cluster_signature)
    return tuple(EvidenceFamilyV2(cluster) for cluster in clusters)


def complete_link_near_duplicate_families(
    reports: Sequence[ReportV2],
    policy: NearDuplicatePolicyV2 = NearDuplicatePolicyV2(),
) -> tuple[EvidenceFamilyV2, ...]:
    """Collapse exact copies, then form deterministic complete-link families."""

    return _complete_link_units(collapse_exact_duplicates(reports), policy)


def deduplicate_reports(
    reports: Sequence[ReportV2],
    policy: NearDuplicatePolicyV2 = NearDuplicatePolicyV2(),
) -> DeduplicationResultV2:
    exact_units = collapse_exact_duplicates(reports)
    families = _complete_link_units(exact_units, policy)
    return DeduplicationResultV2(
        exact_units=exact_units,
        families=families,
        exact_duplicates_removed=len(reports) - len(exact_units),
        near_units_coalesced=len(exact_units) - len(families),
    )


CorroborationKeyV2 = Literal["source_family", "source_id"]


@dataclass(frozen=True, slots=True)
class CorroborationPolicyV2:
    radius_m: float = 400.0
    time_window_min: float = 60.0
    cap: int = 3
    independence_key: CorroborationKeyV2 = "source_family"

    def __post_init__(self) -> None:
        for name in ("radius_m", "time_window_min"):
            object.__setattr__(
                self,
                name,
                _finite_nonnegative(getattr(self, name), name),
            )
        if type(self.cap) is not int or self.cap < 0:
            raise ValueError("cap must be a non-negative integer")
        if self.independence_key not in ("source_family", "source_id"):
            raise ValueError(
                "independence_key must be 'source_family' or 'source_id'"
            )


def _source_key(
    report: ReportV2,
    policy: CorroborationPolicyV2,
) -> str | None:
    value = getattr(report, policy.independence_key)
    if value is None:
        return None
    # Source IDs are namespaced by family so identical local IDs from different
    # channels cannot be mistaken for the same independent source.
    if policy.independence_key == "source_id":
        return f"{report.source_family or '<unknown>'}:{value}"
    return value


def capped_distinct_source_corroboration(
    reports: Sequence[ReportV2],
    policy: CorroborationPolicyV2 = CorroborationPolicyV2(),
) -> dict[str, int]:
    """Count nearby independent source keys, once per key and up to ``cap``.

    A target's own source key does not corroborate itself.  Reports with
    missing L/T enter the graph review queue and receive zero corroboration.
    Missing source keys are not counted as independent evidence.
    """

    validate_unique_report_ids(reports)
    result: dict[str, int] = {}
    for target in reports:
        if not target.graph_eligible or policy.cap == 0:
            result[target.report_id] = 0
            continue
        target_key = _source_key(target, policy)
        corroborating: set[str] = set()
        for candidate in reports:
            if candidate.report_id == target.report_id:
                continue
            if not candidate.graph_eligible:
                continue
            candidate_key = _source_key(candidate, policy)
            if candidate_key is None or candidate_key == target_key:
                continue
            if haversine_m(target.L, candidate.L) > policy.radius_m:
                continue
            delta_min = abs((target.T - candidate.T).total_seconds()) / 60.0
            if delta_min > policy.time_window_min:
                continue
            corroborating.add(candidate_key)
        result[target.report_id] = min(policy.cap, len(corroborating))
    return result


# Explicit compatibility names for callers that prefer the longer wording.
observable_report_fingerprint_v2 = exact_fingerprint
are_near_duplicate_reports_v2 = are_near_duplicates

