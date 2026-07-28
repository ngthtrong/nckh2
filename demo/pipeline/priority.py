"""Cluster-level priority estimation.

Two deliberately named estimators are available:

``legacy_raw``
    Reproduces the pre-revision implementation.  It is retained only for
    historical comparisons and ablations: report-level ``N`` is summed after
    confidence gating while ``V`` is summed without a confidence gate.

``duplicate_aware_robust``
    Revised default.  It uses only inference-visible report fields, removes
    exact duplicate payloads, coalesces tightly defined near duplicates, gates
    every priority input by confidence, and caps the influence of a report.

The revised estimator intentionally calls ``N`` and ``V`` *reported evidence*.
Without observable person-level identifiers it cannot recover unique incident
population truth.  In particular, neither estimator may inspect
``incident_id``, ``N_true``, ``V_true``, duplicate lineage, or outcome labels.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol, TypeAlias, runtime_checkable

from .attributes import Event, haversine_m
from .config import PriorityParams


LEGACY_ESTIMATOR_NAME = "legacy_raw"
REVISED_ESTIMATOR_NAME = "duplicate_aware_robust"


@dataclass(frozen=True)
class NearDuplicatePolicy:
    """Observable tolerances used to coalesce near-duplicate reports.

    These values match the candidate-data quality gate for spatial, temporal,
    ``F/E/N/V`` drift.  The confidence tolerance is additional: a pair with a
    materially different provenance/confidence assessment is not silently
    coalesced by priority inference.

    The preregistered stress-test requirement is that adding one report which
    satisfies every tolerance changes priority by at most
    ``max_priority_drift_fraction`` of the estimator's declared range.  This is
    an acceptance threshold for C3, not a claim about reports outside this
    near-duplicate envelope.
    """

    distance_m: float = 100.0
    time_window_min: float = 10.0
    flood_abs: float = 0.10
    urgency_abs: float = 0.10
    n_abs_floor: float = 5.0
    n_relative: float = 0.25
    vulnerability_abs: float = 2.0
    confidence_abs: float = 0.10
    # Gate-1 boundary audit found a maximum default-policy single-addition
    # drift of 0.235816 over the declared envelope.  The preregistered ceiling
    # is rounded upward to 0.30 before release of any locked test result.
    max_priority_drift_fraction: float = 0.30


@dataclass(frozen=True)
class RobustEstimatorPolicy:
    """Influence caps for the revised estimator.

    ``n_claim_cap=None`` resolves to the positive static ``params.n_ref`` and
    otherwise falls back to 500.  ``v_claim_cap`` is a per-evidence-unit cap;
    the outer ``tanh`` and ``v_cap_mu`` provide a second, score-level bound.
    """

    n_claim_cap: float | None = None
    v_claim_cap: float = 50.0
    near_duplicate: NearDuplicatePolicy = field(default_factory=NearDuplicatePolicy)


DEFAULT_ROBUST_POLICY = RobustEstimatorPolicy()


@dataclass(frozen=True)
class PriorityEvidence:
    """Unrounded evidence returned by a cluster estimator."""

    e_agg: float
    f_max: float
    n_raw: float
    v_raw: float
    center_lat: float
    center_lng: float
    evidence_units: int
    exact_duplicates_removed: int = 0
    near_duplicates_coalesced: int = 0


@dataclass
class ClusterScore:
    cluster_id: int
    size: int
    e_agg: float
    f_max: float
    # Compatibility name: legacy mode stores sum(N_i*C_i); revised mode stores
    # the strongest capped, confidence-gated reported-demand evidence.
    n_total_raw: float
    n_norm: float
    # V evidence before the tanh policy multiplier.  This field did not exist
    # in the historical API but makes the C=0/duplicate invariants auditable.
    v_total_raw: float
    v_agg: float
    core: float
    priority: float
    center_lat: float
    center_lng: float
    member_ids: list[str]
    estimator: str
    evidence_units: int
    exact_duplicates_removed: int
    near_duplicates_coalesced: int
    priority_lower_bound: float
    priority_upper_bound: float


@runtime_checkable
class PriorityEstimator(Protocol):
    """Estimator interface used by :func:`score_clusters`."""

    name: str

    def aggregate(
        self,
        members: list[Event],
        params: PriorityParams,
        *,
        gate_confidence: bool,
        gate_fmax: bool,
    ) -> PriorityEvidence:
        """Aggregate observable report evidence for one cluster."""


def _cluster_members(events: list[Event], labels: list[int]) -> dict[int, list[Event]]:
    if len(events) != len(labels):
        raise ValueError(
            f"events và labels phải cùng độ dài: {len(events)} != {len(labels)}"
        )
    groups: dict[int, list[Event]] = {}
    for ev, lab in zip(events, labels):
        groups.setdefault(lab, []).append(ev)
    return groups


def _canonical_created_at(value: datetime | str) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def observable_report_payload(event: Event) -> dict[str, object]:
    """Return the exact-duplicate payload allowed at inference time.

    This adapter intentionally matches ``demo/data/schema.py``.  Identity,
    narrative, confidence-derived corroboration, fake/evaluation labels, and
    every latent field are absent.  Attribute access is explicit so a future
    ``incident_id`` attached to an Event can never enter the fingerprint by
    accident.
    """

    return {
        "lat": event.lat,
        "lng": event.lng,
        "created_at": _canonical_created_at(event.created_at),
        "flood": event.flood,
        "urgency": event.urgency,
        "n_trapped": event.n_trapped,
        "vulnerability": event.vulnerability,
        "has_image": event.has_image,
        "source_type": getattr(event, "source_type", "unknown"),
        "province": event.province,
        "missing_fields": list(getattr(event, "missing_fields", ())),
    }


def observable_report_fingerprint(event: Event) -> str:
    """SHA-256 fingerprint of an inference-visible report payload."""

    encoded = (
        json.dumps(
            observable_report_payload(event),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _finite(value: object, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} phải là số hữu hạn") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field_name} phải là số hữu hạn")
    return number


def _clip(value: object, low: float, high: float, field_name: str) -> float:
    number = _finite(value, field_name)
    return min(high, max(low, number))


def _confidence(event: Event, enabled: bool) -> float:
    if not enabled:
        return 1.0
    return _clip(event.confidence, 0.0, 1.0, "confidence")


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def are_near_duplicate_reports(
    first: Event,
    second: Event,
    policy: NearDuplicatePolicy = NearDuplicatePolicy(),
) -> bool:
    """Whether two reports fit the preregistered near-duplicate envelope.

    Only deployment-visible measurements and the derived confidence score are
    read.  No hidden duplicate-family or incident label is used.
    """

    n_first = max(0.0, _finite(first.n_trapped, "n_trapped"))
    n_second = max(0.0, _finite(second.n_trapped, "n_trapped"))
    n_tolerance = max(
        policy.n_abs_floor,
        policy.n_relative * max(n_first, n_second, 1.0),
    )
    time_delta = abs(
        (_as_utc(first.created_at) - _as_utc(second.created_at)).total_seconds()
    ) / 60.0
    return (
        haversine_m(first.lat, first.lng, second.lat, second.lng)
        <= policy.distance_m
        and time_delta <= policy.time_window_min
        and abs(_finite(first.flood, "flood") - _finite(second.flood, "flood"))
        <= policy.flood_abs
        and abs(
            _finite(first.urgency, "urgency")
            - _finite(second.urgency, "urgency")
        )
        <= policy.urgency_abs
        and abs(n_first - n_second) <= n_tolerance
        and abs(
            _finite(first.vulnerability, "vulnerability")
            - _finite(second.vulnerability, "vulnerability")
        )
        <= policy.vulnerability_abs
        and abs(
            _clip(first.confidence, 0.0, 1.0, "confidence")
            - _clip(second.confidence, 0.0, 1.0, "confidence")
        )
        <= policy.confidence_abs
        and tuple(first.missing_fields) == tuple(second.missing_fields)
    )


@dataclass(frozen=True)
class _EvidenceUnit:
    """One exact-payload unit after exact duplicates have been removed."""

    event: Event
    confidence: float
    multiplicity: int


def _exact_units(
    members: list[Event],
    *,
    gate_confidence: bool,
) -> tuple[list[_EvidenceUnit], int]:
    by_fingerprint: dict[str, list[Event]] = {}
    for event in members:
        by_fingerprint.setdefault(observable_report_fingerprint(event), []).append(event)

    units: list[_EvidenceUnit] = []
    removed = 0
    for fingerprint in sorted(by_fingerprint):
        duplicates = by_fingerprint[fingerprint]
        # Confidence is derived after the raw-payload fingerprint and is not a
        # fingerprint field.  Valid exact copies receive exactly the same C
        # because confidence corroboration counts unique payloads.  Silently
        # taking max/min here would let a conflicting duplicate alter priority,
        # so an inconsistent derived C fails closed as a data/provenance error.
        confidences = [
            _confidence(event, gate_confidence) for event in duplicates
        ]
        confidence = confidences[0]
        if any(value != confidence for value in confidences[1:]):
            raise ValueError(
                "exact duplicate fingerprint has inconsistent derived "
                f"confidence: {fingerprint[:12]}..."
            )
        representative = min(duplicates, key=lambda event: str(event.event_id))
        removed += len(duplicates) - 1
        if confidence > 0.0:
            units.append(
                _EvidenceUnit(
                    event=representative,
                    confidence=confidence,
                    multiplicity=len(duplicates),
                )
            )
    return units, removed


def _near_duplicate_families(
    units: list[_EvidenceUnit],
    policy: NearDuplicatePolicy,
) -> list[list[_EvidenceUnit]]:
    """Deterministic connected components under observable near similarity."""

    if not units:
        return []
    parent = list(range(len(units)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(first: int, second: int) -> None:
        root_first, root_second = find(first), find(second)
        if root_first != root_second:
            parent[max(root_first, root_second)] = min(root_first, root_second)

    for first in range(len(units)):
        for second in range(first + 1, len(units)):
            if are_near_duplicate_reports(
                units[first].event,
                units[second].event,
                policy,
            ):
                union(first, second)

    families: dict[int, list[_EvidenceUnit]] = {}
    for index, unit in enumerate(units):
        families.setdefault(find(index), []).append(unit)
    return [
        sorted(family, key=lambda unit: str(unit.event.event_id))
        for _, family in sorted(families.items())
    ]


def _weighted_center(
    families: list[list[_EvidenceUnit]],
    fallback_members: list[Event],
) -> tuple[float, float]:
    representatives: list[tuple[Event, float]] = []
    for family in families:
        unit = max(
            family,
            key=lambda candidate: (
                candidate.confidence,
                str(candidate.event.event_id),
            ),
        )
        representatives.append((unit.event, unit.confidence))
    total_weight = sum(weight for _, weight in representatives)
    if total_weight > 0.0:
        return (
            sum(event.lat * weight for event, weight in representatives)
            / total_weight,
            sum(event.lng * weight for event, weight in representatives)
            / total_weight,
        )
    # No reliable evidence exists.  The location is retained only as routing
    # metadata; all priority components and priority itself remain zero.
    return (
        sum(event.lat for event in fallback_members) / len(fallback_members),
        sum(event.lng for event in fallback_members) / len(fallback_members),
    )


@dataclass(frozen=True)
class LegacyRawEstimator:
    """Historical implementation, preserved exactly for regression checks."""

    name: str = LEGACY_ESTIMATOR_NAME

    def aggregate(
        self,
        members: list[Event],
        params: PriorityParams,
        *,
        gate_confidence: bool,
        gate_fmax: bool,
    ) -> PriorityEvidence:
        del params
        size = len(members)
        e_agg = sum(event.urgency * event.confidence for event in members) / size
        if gate_fmax:
            f_max = max(event.flood * event.confidence for event in members)
        else:
            f_max = max(event.flood for event in members)
        if gate_confidence:
            n_raw = sum(
                event.n_trapped * event.confidence for event in members
            )
        else:
            n_raw = sum(event.n_trapped for event in members)
        # Intentional legacy inconsistency: V bypasses confidence.
        v_raw = sum(event.vulnerability for event in members)
        return PriorityEvidence(
            e_agg=e_agg,
            f_max=f_max,
            n_raw=n_raw,
            v_raw=v_raw,
            center_lat=sum(event.lat for event in members) / size,
            center_lng=sum(event.lng for event in members) / size,
            evidence_units=size,
        )


@dataclass(frozen=True)
class DuplicateAwareRobustEstimator:
    """Inference-feasible, confidence-consistent revised estimator."""

    policy: RobustEstimatorPolicy = field(default_factory=RobustEstimatorPolicy)
    name: str = REVISED_ESTIMATOR_NAME

    def aggregate(
        self,
        members: list[Event],
        params: PriorityParams,
        *,
        gate_confidence: bool,
        gate_fmax: bool,
    ) -> PriorityEvidence:
        _validate_revised_params(params, self.policy)
        units, exact_removed = _exact_units(
            members,
            gate_confidence=gate_confidence,
        )
        families = _near_duplicate_families(
            units,
            self.policy.near_duplicate,
        )
        n_cap = _resolved_n_claim_cap(params, self.policy)

        family_evidence: list[tuple[float, float]] = []
        family_f: list[float] = []
        family_n: list[float] = []
        family_v: list[float] = []
        for family in families:
            confidence_mass = max(unit.confidence for unit in family)
            family_evidence.append(
                (
                    max(
                        unit.confidence
                        * _clip(unit.event.urgency, 0.0, 1.0, "urgency")
                        for unit in family
                    ),
                    confidence_mass,
                )
            )
            family_f.append(
                max(
                    (
                        unit.confidence if gate_fmax else 1.0
                    )
                    * _clip(unit.event.flood, 0.0, 1.0, "flood")
                    for unit in family
                )
            )
            family_n.append(
                max(
                    unit.confidence
                    * _clip(unit.event.n_trapped, 0.0, n_cap, "n_trapped")
                    for unit in family
                )
            )
            family_v.append(
                max(
                    unit.confidence
                    * _clip(
                        unit.event.vulnerability,
                        0.0,
                        self.policy.v_claim_cap,
                        "vulnerability",
                    )
                    for unit in family
                )
            )

        if family_evidence:
            # A reliability-mass floor of one keeps a lone low-C report low:
            # E_hat = sum(C*E) / max(1, sum C).  Once evidence mass exceeds one
            # this becomes a confidence-weighted robust mean across independent
            # near-duplicate families.
            e_numerator = sum(value for value, _ in family_evidence)
            e_denominator = max(
                1.0,
                sum(confidence for _, confidence in family_evidence),
            )
            e_agg = e_numerator / e_denominator
            f_max = max(family_f)
            # N and V are overlapping partial observations.  Summing them would
            # silently assume disjoint people, so the revised estimator retains
            # the strongest capped/gated evidence rather than double-counting.
            n_raw = max(family_n)
            v_raw = max(family_v)
        else:
            e_agg = f_max = n_raw = v_raw = 0.0

        center_lat, center_lng = _weighted_center(families, members)
        return PriorityEvidence(
            e_agg=e_agg,
            f_max=f_max,
            n_raw=n_raw,
            v_raw=v_raw,
            center_lat=center_lat,
            center_lng=center_lng,
            evidence_units=len(families),
            exact_duplicates_removed=exact_removed,
            near_duplicates_coalesced=max(0, len(units) - len(families)),
        )


LEGACY_RAW_ESTIMATOR = LegacyRawEstimator()
DEFAULT_PRIORITY_ESTIMATOR = DuplicateAwareRobustEstimator()

EstimatorSpec: TypeAlias = str | PriorityEstimator | None


def resolve_priority_estimator(estimator: EstimatorSpec) -> PriorityEstimator:
    """Resolve public estimator aliases without consulting data or labels."""

    if estimator is None:
        return DEFAULT_PRIORITY_ESTIMATOR
    if isinstance(estimator, str):
        key = estimator.strip().lower().replace("-", "_")
        if key in {"legacy", "raw", "legacy_raw"}:
            return LEGACY_RAW_ESTIMATOR
        if key in {
            "revised",
            "robust",
            "duplicate_aware",
            "duplicate_aware_robust",
        }:
            return DEFAULT_PRIORITY_ESTIMATOR
        raise ValueError(
            f"estimator không hợp lệ: {estimator!r}; "
            "chọn 'legacy_raw' hoặc 'duplicate_aware_robust'"
        )
    if not isinstance(estimator, PriorityEstimator):
        raise TypeError("estimator phải là tên hoặc object theo PriorityEstimator")
    return estimator


def _resolved_n_claim_cap(
    params: PriorityParams,
    policy: RobustEstimatorPolicy,
) -> float:
    if policy.n_claim_cap is not None:
        return float(policy.n_claim_cap)
    configured = getattr(params, "n_ref", 500.0)
    if isinstance(configured, (int, float)) and configured > 0:
        return float(configured)
    return 500.0


def _validate_revised_params(
    params: PriorityParams,
    policy: RobustEstimatorPolicy,
) -> None:
    weights = (params.omega_e, params.omega_f, params.omega_n)
    if any(not math.isfinite(weight) or weight < 0.0 for weight in weights):
        raise ValueError("omega_e/omega_f/omega_n phải hữu hạn và không âm")
    if (
        not math.isfinite(params.v_cap_mu)
        or not 1.0 <= params.v_cap_mu <= 2.0
    ):
        raise ValueError("v_cap_mu phải thuộc policy range [1, 2]")
    if not math.isfinite(params.v_scale) or params.v_scale <= 0.0:
        raise ValueError("v_scale phải là số hữu hạn dương")
    n_cap = _resolved_n_claim_cap(params, policy)
    if not math.isfinite(n_cap) or n_cap <= 0.0:
        raise ValueError("n_claim_cap phải là số hữu hạn dương")
    if not math.isfinite(policy.v_claim_cap) or policy.v_claim_cap <= 0.0:
        raise ValueError("v_claim_cap phải là số hữu hạn dương")


def priority_range(
    params: PriorityParams,
    *,
    normalize_v: bool = True,
) -> tuple[float, float]:
    """Declared closed score range under valid report domains.

    With normalized non-negative weights and ``mu <= 2`` this is ``[0, 2]`` for
    multiplicative V and ``[0, 2]`` for the additive ablation.  The function
    also handles non-unit non-negative weight sums transparently.
    """

    weights = (params.omega_e, params.omega_f, params.omega_n)
    if any(not math.isfinite(weight) or weight < 0.0 for weight in weights):
        raise ValueError("priority range cần các omega hữu hạn, không âm")
    if not math.isfinite(params.v_cap_mu) or params.v_cap_mu < 1.0:
        raise ValueError("priority range cần v_cap_mu >= 1")
    core_upper = sum(weights)
    if normalize_v:
        upper = params.v_cap_mu * core_upper
    else:
        upper = core_upper + (params.v_cap_mu - 1.0)
    return 0.0, upper


def aggregate_cluster_evidence(
    members: list[Event],
    params: PriorityParams,
    *,
    estimator: EstimatorSpec = None,
    gate_confidence: bool = True,
    gate_fmax: bool = True,
) -> PriorityEvidence:
    """Public one-cluster estimator API used by unit/adversarial tests."""

    if not members:
        raise ValueError("members không được rỗng")
    resolved = resolve_priority_estimator(estimator)
    return resolved.aggregate(
        members,
        params,
        gate_confidence=gate_confidence,
        gate_fmax=gate_fmax,
    )


def score_clusters(
    events: list[Event],
    labels: list[int],
    params: PriorityParams,
    gate_confidence: bool = True,
    normalize_v: bool = True,
    gate_fmax: bool = True,
    n_ref: float | str | None = None,
    estimator: EstimatorSpec = None,
) -> list[ClusterScore]:
    """Compute priority for all clusters through an explicit estimator API.

    ``estimator=None`` selects the revised ``duplicate_aware_robust`` policy.
    Historical results must request ``estimator="legacy_raw"`` explicitly.

    The three legacy ablation flags remain source-compatible.  The revised
    invariants (all-field confidence gating and C=0 no contribution) apply to
    their default values; disabling a gate is an explicitly non-contractual
    ablation.

    ``n_ref`` retains its historical semantics: a positive static reference,
    or ``"dynamic"`` for within-run normalization.  Dynamic normalization is
    unsuitable for longitudinal score comparison and is kept only for the
    declared stability ablation.
    """

    groups = _cluster_members(events, labels)
    resolved = resolve_priority_estimator(estimator)
    evidence = {
        cluster_id: resolved.aggregate(
            members,
            params,
            gate_confidence=gate_confidence,
            gate_fmax=gate_fmax,
        )
        for cluster_id, members in groups.items()
    }

    if n_ref is None:
        n_ref = getattr(params, "n_ref", None)
    if isinstance(n_ref, str):
        if n_ref != "dynamic":
            raise ValueError(f"n_ref không hợp lệ: {n_ref!r} (chỉ nhận 'dynamic')")
        n_max = max(
            (estimate.n_raw for estimate in evidence.values()),
            default=1.0,
        )
    elif n_ref is not None and n_ref > 0:
        n_max = float(n_ref)
    else:
        n_max = max(
            (estimate.n_raw for estimate in evidence.values()),
            default=1.0,
        )
    log_nmax = math.log1p(n_max) if n_max > 0 else 1.0
    lower_bound, upper_bound = priority_range(
        params,
        normalize_v=normalize_v,
    )

    scores: list[ClusterScore] = []
    for cluster_id, members in groups.items():
        estimate = evidence[cluster_id]
        n_norm = (
            min(1.0, math.log1p(estimate.n_raw) / log_nmax)
            if log_nmax > 0
            else 0.0
        )
        v_agg = 1.0 + (params.v_cap_mu - 1.0) * math.tanh(
            estimate.v_raw / params.v_scale
        )
        core = (
            params.omega_e * estimate.e_agg
            + params.omega_f * estimate.f_max
            + params.omega_n * n_norm
        )
        if normalize_v:
            priority = v_agg * core
        else:
            # Historical additive ablation: same origin and declared range as
            # the multiplicative form when weights sum to one.
            priority = core + (v_agg - 1.0)

        # Fail closed if a custom estimator violates the public range contract.
        tolerance = 1e-12
        if not (
            lower_bound - tolerance <= priority <= upper_bound + tolerance
        ):
            raise ValueError(
                f"estimator {resolved.name!r} tạo priority ngoài miền "
                f"[{lower_bound}, {upper_bound}]: {priority}"
            )

        scores.append(
            ClusterScore(
                cluster_id=cluster_id,
                size=len(members),
                e_agg=round(estimate.e_agg, 4),
                f_max=round(estimate.f_max, 4),
                n_total_raw=round(estimate.n_raw, 2),
                n_norm=round(n_norm, 4),
                v_total_raw=round(estimate.v_raw, 4),
                v_agg=round(v_agg, 4),
                core=round(core, 4),
                priority=round(priority, 4),
                center_lat=round(estimate.center_lat, 6),
                center_lng=round(estimate.center_lng, 6),
                member_ids=[event.event_id for event in members],
                estimator=resolved.name,
                evidence_units=estimate.evidence_units,
                exact_duplicates_removed=estimate.exact_duplicates_removed,
                near_duplicates_coalesced=estimate.near_duplicates_coalesced,
                priority_lower_bound=round(lower_bound, 4),
                priority_upper_bound=round(upper_bound, 4),
            )
        )

    scores.sort(key=lambda score: score.priority, reverse=True)
    return scores
