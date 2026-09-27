# Dựa trên demo/v2/dedup.py tại commit a6be3e9 (import tương đối). Đã chỉnh cho khớp
# bài báo ISDS 2026 (Mục 2.1, 2.3) theo bản cài đặt thực nghiệm demo/pipeline tại cùng
# commit: gom bản gần trùng bằng thành phần liên thông (không phải complete-link),
# ngưỡng so sánh độ tin cậy dẫn xuất Q_i, và n_corrob đếm payload quan sát phân biệt.
"""Deterministic, observable-only deduplication and corroboration for v2."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Mapping, Sequence

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
    """Observable near-duplicate envelope (demo/pipeline NearDuplicatePolicy).

    ``confidence_abs`` compares the derived confidence Q_i, not a raw payload
    field.  The two ``require_same_*`` guards are v2 extensions that the paper
    envelope does not contain, so they are disabled by default.
    """

    distance_m: float = 100.0
    time_window_min: float = 10.0
    flood_abs: float = 0.10
    urgency_abs: float = 0.10
    n_abs_floor: float = 5.0
    n_relative: float = 0.25
    vulnerability_abs: float = 2.0
    confidence_abs: float = 0.10
    require_same_source_family: bool = False
    require_same_image_state: bool = False

    def __post_init__(self) -> None:
        for name in (
            "distance_m",
            "time_window_min",
            "flood_abs",
            "urgency_abs",
            "n_abs_floor",
            "n_relative",
            "vulnerability_abs",
            "confidence_abs",
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
    confidence: Mapping[str, float] | None = None,
) -> bool:
    """Pairwise observable near-duplicate predicate.

    Masks must match exactly; a missing observation is never silently compared
    with a real zero.  L and T are mandatory because a near relation cannot be
    established safely without both.  Source IDs are transport identities and
    are deliberately ignored.  When ``confidence`` (report_id -> Q_i) is given,
    the derived confidences must also agree within ``confidence_abs``.
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
    if confidence is not None and (
        abs(confidence[first.report_id] - confidence[second.report_id])
        > policy.confidence_abs
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
    """A connected component of near-duplicate exact-evidence units."""

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


def _near_duplicate_components(
    units: Sequence[ExactEvidenceUnitV2],
    policy: NearDuplicatePolicyV2,
    confidence: Mapping[str, float] | None,
) -> tuple[EvidenceFamilyV2, ...]:
    """Deterministic connected components under observable near similarity.

    This is the transitive rule of the paper (A~B~C joins A and C even if A is
    not near C); it is intentionally not complete linkage.  Units are ordered
    by fingerprint, so the result does not depend on input order.
    """

    ordered = sorted(units, key=lambda item: item.fingerprint)
    parent = list(range(len(ordered)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(first: int, second: int) -> None:
        root_first, root_second = find(first), find(second)
        if root_first != root_second:
            parent[max(root_first, root_second)] = min(root_first, root_second)

    for first in range(len(ordered)):
        for second in range(first + 1, len(ordered)):
            if are_near_duplicates(
                ordered[first].representative,
                ordered[second].representative,
                policy,
                confidence,
            ):
                union(first, second)

    components: dict[int, list[ExactEvidenceUnitV2]] = {}
    for index, unit in enumerate(ordered):
        components.setdefault(find(index), []).append(unit)
    return tuple(
        EvidenceFamilyV2(
            tuple(sorted(members, key=lambda unit: unit.representative.report_id))
        )
        for _, members in sorted(components.items())
    )


def near_duplicate_families(
    reports: Sequence[ReportV2],
    policy: NearDuplicatePolicyV2 = NearDuplicatePolicyV2(),
    confidence: Mapping[str, float] | None = None,
) -> tuple[EvidenceFamilyV2, ...]:
    """Collapse exact copies, then form deterministic connected components."""

    return _near_duplicate_components(
        collapse_exact_duplicates(reports), policy, confidence
    )


def deduplicate_reports(
    reports: Sequence[ReportV2],
    policy: NearDuplicatePolicyV2 = NearDuplicatePolicyV2(),
    confidence: Mapping[str, float] | None = None,
) -> DeduplicationResultV2:
    exact_units = collapse_exact_duplicates(reports)
    families = _near_duplicate_components(exact_units, policy, confidence)
    return DeduplicationResultV2(
        exact_units=exact_units,
        families=families,
        exact_duplicates_removed=len(reports) - len(exact_units),
        near_units_coalesced=len(exact_units) - len(families),
    )


@dataclass(frozen=True, slots=True)
class ConfidencePolicyV2:
    """Eq. (1): Q_i = sigmoid(b0 + b1*1{image} + b2*log(1 + n_corrob)).

    Values follow demo/pipeline/config.py ConfidenceParams at commit a6be3e9.
    """

    b0: float = -0.2
    b1: float = 1.4
    b2: float = 0.9
    corrob_radius_m: float = 400.0
    corrob_window_min: float = 60.0

    def __post_init__(self) -> None:
        for name in ("b0", "b1", "b2"):
            value = float(getattr(self, name))
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
            object.__setattr__(self, name, value)
        for name in ("corrob_radius_m", "corrob_window_min"):
            object.__setattr__(
                self,
                name,
                _finite_nonnegative(getattr(self, name), name),
            )


def distinct_payload_corroboration(
    reports: Sequence[ReportV2],
    policy: ConfidencePolicyV2 = ConfidencePolicyV2(),
) -> dict[str, int]:
    """n_corrob: nearby observable payloads, counted by unique payload identity.

    Exact copies of the target's own payload are the same evidence unit and do
    not corroborate it; repeated copies of another payload count once.  Reports
    with missing L/T go to manual review and receive zero corroboration.
    """

    validate_unique_report_ids(reports)
    fingerprints = {report.report_id: exact_fingerprint(report) for report in reports}
    result: dict[str, int] = {}
    for target in reports:
        if not target.graph_eligible:
            result[target.report_id] = 0
            continue
        own = fingerprints[target.report_id]
        corroborating: set[str] = set()
        for candidate in reports:
            if candidate.report_id == target.report_id or not candidate.graph_eligible:
                continue
            fingerprint = fingerprints[candidate.report_id]
            if fingerprint == own:
                continue
            if haversine_m(target.L, candidate.L) > policy.corrob_radius_m:
                continue
            delta_min = abs((target.T - candidate.T).total_seconds()) / 60.0
            if delta_min > policy.corrob_window_min:
                continue
            corroborating.add(fingerprint)
        result[target.report_id] = len(corroborating)
    return result


def confidence_scores(
    reports: Sequence[ReportV2],
    policy: ConfidencePolicyV2 = ConfidencePolicyV2(),
) -> dict[str, float]:
    """Q_i for every report by Eq. (1); a pipeline rule, not a calibrated probability."""

    corroboration = distinct_payload_corroboration(reports, policy)
    result: dict[str, float] = {}
    for report in reports:
        z = (
            policy.b0
            + policy.b1 * (1.0 if report.has_image else 0.0)
            + policy.b2 * math.log1p(corroboration[report.report_id])
        )
        result[report.report_id] = 1.0 / (1.0 + math.exp(-z))
    return result


# Explicit compatibility names for callers that prefer the longer wording.
observable_report_fingerprint_v2 = exact_fingerprint
are_near_duplicate_reports_v2 = are_near_duplicates
