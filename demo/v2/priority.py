"""Bounded, duplicate-aware ranking and simple comparators for protocol v2."""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Mapping, Sequence

from demo.v2.contracts import ReportV2
from demo.v2.dedup import (
    CorroborationPolicyV2,
    NearDuplicatePolicyV2,
    capped_distinct_source_corroboration,
    deduplicate_reports,
)


@dataclass(frozen=True, slots=True)
class PriorityPolicyV2:
    weight_E: float = 0.40
    weight_F: float = 0.35
    weight_N: float = 0.25
    n_ref: float = 500.0
    n_claim_cap: float = 500.0
    v_claim_cap: float = 50.0
    vulnerability_mu: float = 1.75
    vulnerability_scale: float = 20.0
    near_duplicate: NearDuplicatePolicyV2 = NearDuplicatePolicyV2()
    corroboration: CorroborationPolicyV2 = CorroborationPolicyV2()

    def __post_init__(self) -> None:
        weights = (self.weight_E, self.weight_F, self.weight_N)
        if any(not math.isfinite(value) or value < 0.0 for value in weights):
            raise ValueError("priority weights must be finite and non-negative")
        if not math.isclose(sum(weights), 1.0, abs_tol=1e-12):
            raise ValueError("priority weights must sum to one")
        for name in ("n_ref", "n_claim_cap", "v_claim_cap", "vulnerability_scale"):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        if not math.isfinite(self.vulnerability_mu) or not 1.0 <= self.vulnerability_mu <= 2.0:
            raise ValueError("vulnerability_mu must lie in [1, 2]")

    @property
    def revised_upper_bound(self) -> float:
        return self.vulnerability_mu


@dataclass(frozen=True, slots=True)
class ClusterPriorityV2:
    cluster_id: int
    report_ids: tuple[str, ...]
    revised: float
    legacy: float
    urgency_only: float
    population_only: float
    simple_linear: float
    random: float
    e_agg: float
    f_max: float
    n_norm: float
    v_agg: float
    provenance_mean: float
    exact_duplicates_removed: int
    near_units_coalesced: int

    def dispatch_scores(self) -> dict[str, float]:
        return {
            "revised": self.revised,
            "legacy": self.legacy,
            "urgency_only": self.urgency_only,
            "population_only": self.population_only,
            "simple_linear": self.simple_linear,
            "random": self.random,
        }


def _clip(value: float, low: float, high: float) -> float:
    return min(high, max(low, float(value)))


def report_provenance_scores(
    reports: Sequence[ReportV2],
    policy: PriorityPolicyV2 = PriorityPolicyV2(),
) -> dict[str, float]:
    """Combine direct provenance with capped distinct-source corroboration.

    Nearby report multiplicity alone contributes nothing: the corroboration
    term counts distinct source keys, excludes the report's own key, and is
    capped by ``CorroborationPolicyV2``.
    """

    corroboration = capped_distinct_source_corroboration(reports, policy.corroboration)
    cap = max(1, policy.corroboration.cap)
    result: dict[str, float] = {}
    for report in reports:
        direct = report.provenance_quality if report.provenance_quality is not None else 0.25
        image = 1.0 if report.has_image else 0.0
        cross_source = corroboration[report.report_id] / cap
        result[report.report_id] = _clip(0.72 * direct + 0.10 * image + 0.18 * cross_source, 0.0, 1.0)
    return result


def _measurement_max(
    reports: Sequence[ReportV2],
    provenance: Mapping[str, float],
    field: str,
    cap: float,
) -> float:
    return max(
        (
            provenance[report.report_id]
            * min(cap, max(0.0, float(getattr(report, field))))
            for report in reports
            if getattr(report, field) is not None
        ),
        default=0.0,
    )


def _stable_random_score(report_ids: Sequence[str]) -> float:
    digest = hashlib.sha256("|".join(sorted(report_ids)).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64 - 1)


def score_cluster(
    cluster_id: int,
    reports: Sequence[ReportV2],
    provenance: Mapping[str, float],
    policy: PriorityPolicyV2 = PriorityPolicyV2(),
) -> ClusterPriorityV2:
    if not reports:
        raise ValueError("cannot score an empty cluster")
    if set(provenance).isdisjoint(report.report_id for report in reports):
        raise ValueError("provenance map does not cover the cluster")
    if any(report.report_id not in provenance for report in reports):
        raise ValueError("provenance map must cover every cluster report")
    dedup = deduplicate_reports(reports, policy.near_duplicate)
    family_representatives = [family.representatives for family in dedup.families]

    e_numerator = 0.0
    e_denominator = 0.0
    family_f: list[float] = []
    family_n: list[float] = []
    family_v: list[float] = []
    for members in family_representatives:
        observed_e = [report for report in members if report.E is not None]
        if observed_e:
            e_numerator += max(provenance[row.report_id] * float(row.E) for row in observed_e)
            e_denominator += max(provenance[row.report_id] for row in observed_e)
        family_f.append(_measurement_max(members, provenance, "F", 1.0))
        family_n.append(_measurement_max(members, provenance, "N", policy.n_claim_cap))
        family_v.append(_measurement_max(members, provenance, "V", policy.v_claim_cap))
    e_agg = _clip(e_numerator / max(1.0, e_denominator), 0.0, 1.0)
    f_max = _clip(max(family_f, default=0.0), 0.0, 1.0)
    n_evidence = max(family_n, default=0.0)
    n_norm = _clip(math.log1p(n_evidence) / math.log1p(policy.n_ref), 0.0, 1.0)
    v_agg = min(policy.v_claim_cap, max(family_v, default=0.0))
    vulnerability_multiplier = 1.0 + (policy.vulnerability_mu - 1.0) * math.tanh(
        v_agg / policy.vulnerability_scale
    )
    core = policy.weight_E * e_agg + policy.weight_F * f_max + policy.weight_N * n_norm
    revised = vulnerability_multiplier * core

    # Historical multiplicity-sensitive comparator.  It remains finite here
    # solely for ranking comparability; it is not presented as a boundedness
    # result for the legacy estimator.
    legacy_n = sum(
        provenance[row.report_id] * min(policy.n_claim_cap, float(row.N))
        for row in reports
        if row.N is not None
    )
    legacy_v = sum(min(policy.v_claim_cap, float(row.V)) for row in reports if row.V is not None)
    legacy_n_norm = math.log1p(max(0.0, legacy_n)) / math.log1p(policy.n_ref)
    legacy = (
        policy.weight_E * e_agg
        + policy.weight_F * f_max
        + policy.weight_N * legacy_n_norm
    ) * (1.0 + (policy.vulnerability_mu - 1.0) * math.tanh(legacy_v / policy.vulnerability_scale))
    urgency_only = e_agg
    population_only = n_norm
    v_norm = math.tanh(v_agg / policy.vulnerability_scale)
    simple_linear = 0.35 * e_agg + 0.30 * f_max + 0.25 * n_norm + 0.10 * v_norm
    return ClusterPriorityV2(
        cluster_id=int(cluster_id),
        report_ids=tuple(sorted(report.report_id for report in reports)),
        revised=revised,
        legacy=legacy,
        urgency_only=urgency_only,
        population_only=population_only,
        simple_linear=simple_linear,
        random=_stable_random_score([report.report_id for report in reports]),
        e_agg=e_agg,
        f_max=f_max,
        n_norm=n_norm,
        v_agg=v_agg,
        provenance_mean=mean_or_zero([provenance[row.report_id] for row in reports]),
        exact_duplicates_removed=dedup.exact_duplicates_removed,
        near_units_coalesced=dedup.near_units_coalesced,
    )


def mean_or_zero(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def score_clusters(
    reports: Sequence[ReportV2],
    predicted_labels: Sequence[int],
    policy: PriorityPolicyV2 = PriorityPolicyV2(),
    *,
    noise_label: int = -1,
) -> dict[int, ClusterPriorityV2]:
    if len(reports) != len(predicted_labels):
        raise ValueError("reports and predicted labels must align")
    provenance = report_provenance_scores(reports, policy)
    groups: dict[int, list[ReportV2]] = {}
    for report, label in zip(reports, predicted_labels, strict=True):
        if label == noise_label or not report.graph_eligible:
            continue
        groups.setdefault(int(label), []).append(report)
    return {
        cluster_id: score_cluster(cluster_id, members, provenance, policy)
        for cluster_id, members in sorted(groups.items())
    }


__all__ = [
    "ClusterPriorityV2",
    "PriorityPolicyV2",
    "report_provenance_scores",
    "score_cluster",
    "score_clusters",
]
