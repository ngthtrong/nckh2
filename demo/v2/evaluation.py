"""Truth-isolated priority evaluation on predicted clusters.

The module deliberately separates two phases:

1. :func:`score_predicted_priority` consumes observable reports and predicted
   labels only.  It creates stable membership-hash units and policy score maps.
2. :func:`evaluate_predicted_priority` is evaluator-only.  It joins report and
   incident truth *after* scoring, performs a deterministic one-to-one
   maximum-overlap match, assigns gains, and computes ranking metrics.

This boundary prevents oracle incident grouping from becoming an input to the
priority heuristic.  Split fragments, merged destinations, and noise-only
destinations remain explicit evaluator outcomes rather than being repaired with
ground truth before scoring.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, replace
from datetime import timedelta
from numbers import Integral
from typing import Any, Literal, Mapping, Sequence

import numpy as np
from scipy.optimize import linear_sum_assignment

from demo.v2.contracts import (
    IncidentTruthV2,
    ReportV2,
    TruthV2,
    validate_unique_report_ids,
)
from demo.v2.priority import PriorityPolicyV2, score_clusters
from demo.v2.statistics import perturbation_drift, ranking_metrics

StressFamilyV2 = Literal[
    "exact_duplicate",
    "near_duplicate",
    "gradual_chain_duplicate",
    "low_confidence_E",
    "low_confidence_F",
    "low_confidence_N",
    "low_confidence_V",
    "missingness",
    "contradictory_reports",
    "coordinated_high_confidence_campaign",
]

STRESS_FAMILIES_V2: tuple[StressFamilyV2, ...] = (
    "exact_duplicate",
    "near_duplicate",
    "gradual_chain_duplicate",
    "low_confidence_E",
    "low_confidence_F",
    "low_confidence_N",
    "low_confidence_V",
    "missingness",
    "contradictory_reports",
    "coordinated_high_confidence_campaign",
)

DispositionV2 = Literal[
    "matched",
    "matched_split",
    "matched_merge",
    "matched_split_merge",
    "unmatched_linked_fragment",
    "noise_only",
]


class PriorityEvaluationV2Error(ValueError):
    """Raised when scoring or evaluator joins would be ambiguous."""


def _membership_unit_id(report_ids: Sequence[str]) -> str:
    members = tuple(sorted(str(identifier) for identifier in report_ids))
    if not members or len(members) != len(set(members)):
        raise PriorityEvaluationV2Error(
            "a priority unit requires non-empty unique report ids"
        )
    encoded = json.dumps(
        members,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"priority-unit-{hashlib.sha256(encoded).hexdigest()}"


def _score_tuple(scores: Mapping[str, float]) -> tuple[tuple[str, float], ...]:
    rows: list[tuple[str, float]] = []
    for policy, raw_value in sorted(scores.items()):
        value = float(raw_value)
        if not policy or not math.isfinite(value):
            raise PriorityEvaluationV2Error("policy scores must be finite and named")
        rows.append((str(policy), value))
    if not rows:
        raise PriorityEvaluationV2Error("a priority unit requires policy scores")
    return tuple(rows)


@dataclass(frozen=True, slots=True)
class PredictedPriorityUnitV2:
    """One scored predicted cluster, identified only by observable membership."""

    unit_id: str
    cluster_label: int
    report_ids: tuple[str, ...]
    policy_scores: tuple[tuple[str, float], ...]

    @property
    def score_map(self) -> dict[str, float]:
        return dict(self.policy_scores)


@dataclass(frozen=True, slots=True)
class PredictedPriorityScoresV2:
    """Truth-free scoring output suitable for dispatch and later evaluation."""

    observable_report_ids: tuple[str, ...]
    units: tuple[PredictedPriorityUnitV2, ...]
    review_report_ids: tuple[str, ...]
    noise_label: int

    @property
    def policy_ids(self) -> tuple[str, ...]:
        if not self.units:
            return ()
        return tuple(policy for policy, _ in self.units[0].policy_scores)

    @property
    def policy_score_maps(self) -> dict[str, dict[str, float]]:
        result = {policy: {} for policy in self.policy_ids}
        for unit in self.units:
            scores = unit.score_map
            if tuple(sorted(scores)) != self.policy_ids:
                raise PriorityEvaluationV2Error(
                    "predicted units expose inconsistent policy sets"
                )
            for policy in self.policy_ids:
                result[policy][unit.unit_id] = scores[policy]
        return result

    @property
    def cluster_score_payload(self) -> dict[int, dict[str, float]]:
        """Score mapping accepted by :func:`demo.v2.dispatch.build_jobs`."""

        return {unit.cluster_label: unit.score_map for unit in self.units}


@dataclass(frozen=True, slots=True)
class EvaluatedPriorityUnitV2:
    """Evaluator-only match and gain attached after observable scoring."""

    unit_id: str
    report_ids: tuple[str, ...]
    matched_incident_id: str | None
    gain: float
    matched_overlap_reports: int
    linked_incident_ids: tuple[str, ...]
    noise_report_count: int
    is_split: bool
    is_merge: bool
    disposition: DispositionV2


@dataclass(frozen=True, slots=True)
class PredictedPriorityEvaluationV2:
    """Score maps, evaluator gains, matching audit, and alignment rows."""

    scored: PredictedPriorityScoresV2
    evaluated_units: tuple[EvaluatedPriorityUnitV2, ...]
    alignment_rows: tuple[Mapping[str, Any], ...]
    unmatched_incident_ids: tuple[str, ...]
    matching_rule: str = "one_to_one_global_maximum_report_overlap"

    @property
    def policy_score_maps(self) -> dict[str, dict[str, float]]:
        return self.scored.policy_score_maps

    @property
    def gain_targets(self) -> dict[str, float]:
        return {row.unit_id: row.gain for row in self.evaluated_units}

    @property
    def summary(self) -> dict[str, int]:
        rows = self.evaluated_units
        return {
            "n_predicted_units": len(rows),
            "n_matched_units": sum(row.matched_incident_id is not None for row in rows),
            "n_noise_only_units": sum(row.disposition == "noise_only" for row in rows),
            "n_unmatched_linked_units": sum(
                row.disposition == "unmatched_linked_fragment" for row in rows
            ),
            "n_split_units": sum(row.is_split for row in rows),
            "n_merged_units": sum(row.is_merge for row in rows),
            "n_unmatched_incidents": len(self.unmatched_incident_ids),
        }


def _normalise_labels(
    reports: Sequence[ReportV2],
    predicted_labels: Sequence[int],
    noise_label: int,
) -> tuple[int, ...]:
    if len(reports) != len(predicted_labels):
        raise PriorityEvaluationV2Error(
            "reports and predicted labels must align exactly"
        )
    if isinstance(noise_label, bool) or not isinstance(noise_label, Integral):
        raise PriorityEvaluationV2Error("noise_label must be an integer")
    labels: list[int] = []
    for raw_label in predicted_labels:
        if isinstance(raw_label, bool) or not isinstance(raw_label, Integral):
            raise PriorityEvaluationV2Error("predicted labels must be integers")
        label = int(raw_label)
        if label != int(noise_label) and label < 0:
            raise PriorityEvaluationV2Error(
                "predicted labels must be non-negative or the declared noise label"
            )
        labels.append(label)
    return tuple(labels)


def score_predicted_priority(
    reports: Sequence[ReportV2],
    predicted_labels: Sequence[int],
    policy: PriorityPolicyV2 = PriorityPolicyV2(),
    *,
    noise_label: int = -1,
) -> PredictedPriorityScoresV2:
    """Score predicted clusters without accepting any evaluator truth object."""

    validate_unique_report_ids(reports)
    labels = _normalise_labels(reports, predicted_labels, noise_label)
    cluster_scores = score_clusters(
        reports,
        labels,
        policy,
        noise_label=noise_label,
    )
    units: list[PredictedPriorityUnitV2] = []
    for cluster_label, row in cluster_scores.items():
        report_ids = tuple(sorted(row.report_ids))
        units.append(
            PredictedPriorityUnitV2(
                unit_id=_membership_unit_id(report_ids),
                cluster_label=int(cluster_label),
                report_ids=report_ids,
                policy_scores=_score_tuple(row.dispatch_scores()),
            )
        )
    units.sort(key=lambda row: row.unit_id)
    if units:
        expected = tuple(policy for policy, _ in units[0].policy_scores)
        if any(
            tuple(policy for policy, _ in unit.policy_scores) != expected
            for unit in units
        ):
            raise PriorityEvaluationV2Error(
                "predicted units expose inconsistent policy sets"
            )
    review = tuple(
        sorted(
            report.report_id
            for report, label in zip(reports, labels, strict=True)
            if not report.graph_eligible or label == noise_label
        )
    )
    return PredictedPriorityScoresV2(
        observable_report_ids=tuple(sorted(report.report_id for report in reports)),
        units=tuple(units),
        review_report_ids=review,
        noise_label=int(noise_label),
    )


def _validated_truth(
    scored: PredictedPriorityScoresV2,
    report_truth: Sequence[TruthV2],
    incident_truth: Sequence[IncidentTruthV2],
) -> tuple[dict[str, TruthV2], dict[str, IncidentTruthV2]]:
    links = {row.report_id: row for row in report_truth}
    if len(links) != len(report_truth):
        raise PriorityEvaluationV2Error("report truth ids must be unique")
    if set(links) != set(scored.observable_report_ids):
        raise PriorityEvaluationV2Error(
            "report truth must cover every observable report exactly once"
        )
    incidents = {row.incident_id: row for row in incident_truth}
    if len(incidents) != len(incident_truth):
        raise PriorityEvaluationV2Error("incident truth ids must be unique")
    for row in report_truth:
        if row.incident_id is None:
            if not row.is_noise:
                raise PriorityEvaluationV2Error(
                    "unlinked evaluator rows must be explicitly marked as noise"
                )
        else:
            if row.is_noise:
                raise PriorityEvaluationV2Error(
                    "an incident-linked evaluator row cannot also be noise"
                )
            if row.incident_id not in incidents:
                raise PriorityEvaluationV2Error(
                    f"report truth references unknown incident: {row.incident_id}"
                )
    return links, incidents


def _maximum_overlap_matching(
    units: Sequence[PredictedPriorityUnitV2],
    links: Mapping[str, TruthV2],
    incident_ids: Sequence[str],
) -> tuple[dict[str, str], dict[str, dict[str, int]]]:
    """Return a deterministic global one-to-one maximum-overlap assignment.

    Rows and columns are canonically sorted before SciPy's deterministic
    assignment routine.  Zero-overlap assignments are discarded, so a unit is
    never granted gain from an incident absent from its reports.
    """

    ordered_units = tuple(sorted(units, key=lambda row: row.unit_id))
    ordered_incidents = tuple(sorted(incident_ids))
    counts: dict[str, dict[str, int]] = {}
    for unit in ordered_units:
        row_counts: dict[str, int] = {}
        for report_id in unit.report_ids:
            incident_id = links[report_id].incident_id
            if incident_id is not None:
                row_counts[incident_id] = row_counts.get(incident_id, 0) + 1
        counts[unit.unit_id] = row_counts
    if not ordered_units or not ordered_incidents:
        return {}, counts
    overlap = np.asarray(
        [
            [counts[unit.unit_id].get(incident_id, 0) for incident_id in ordered_incidents]
            for unit in ordered_units
        ],
        dtype=np.int64,
    )
    row_indices, column_indices = linear_sum_assignment(overlap, maximize=True)
    matching: dict[str, str] = {}
    for row_index, column_index in zip(row_indices, column_indices, strict=True):
        if int(overlap[row_index, column_index]) <= 0:
            continue
        matching[ordered_units[int(row_index)].unit_id] = ordered_incidents[
            int(column_index)
        ]
    return matching, counts


def _incident_gain(incident: IncidentTruthV2) -> float:
    value = (
        incident.latent_benefit
        if incident.latent_benefit is not None
        else incident.latent_need
    )
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise PriorityEvaluationV2Error(
            f"incident gain must be finite and non-negative: {incident.incident_id}"
        )
    return result


def evaluate_predicted_priority(
    scored: PredictedPriorityScoresV2,
    report_truth: Sequence[TruthV2],
    incident_truth: Sequence[IncidentTruthV2],
    *,
    k: int = 5,
) -> PredictedPriorityEvaluationV2:
    """Attach evaluator gains only after predicted clusters have been scored."""

    if not scored.units:
        raise PriorityEvaluationV2Error(
            "priority alignment is undefined without predicted operational units"
        )
    links, incidents = _validated_truth(scored, report_truth, incident_truth)
    matching, overlap_counts = _maximum_overlap_matching(
        scored.units,
        links,
        tuple(incidents),
    )
    incident_presence: dict[str, int] = {identifier: 0 for identifier in incidents}
    for row_counts in overlap_counts.values():
        for incident_id, count in row_counts.items():
            if count > 0:
                incident_presence[incident_id] += 1
    evaluated: list[EvaluatedPriorityUnitV2] = []
    matched_incidents: set[str] = set()
    for unit in scored.units:
        row_counts = overlap_counts[unit.unit_id]
        linked_ids = tuple(sorted(row_counts))
        matched_incident_id = matching.get(unit.unit_id)
        if matched_incident_id is not None:
            matched_incidents.add(matched_incident_id)
        is_merge = len(linked_ids) > 1
        is_split = any(incident_presence[identifier] > 1 for identifier in linked_ids)
        if matched_incident_id is None:
            disposition: DispositionV2 = (
                "noise_only" if not linked_ids else "unmatched_linked_fragment"
            )
            gain = 0.0
            matched_overlap = 0
        else:
            if is_split and is_merge:
                disposition = "matched_split_merge"
            elif is_split:
                disposition = "matched_split"
            elif is_merge:
                disposition = "matched_merge"
            else:
                disposition = "matched"
            gain = _incident_gain(incidents[matched_incident_id])
            matched_overlap = row_counts[matched_incident_id]
        evaluated.append(
            EvaluatedPriorityUnitV2(
                unit_id=unit.unit_id,
                report_ids=unit.report_ids,
                matched_incident_id=matched_incident_id,
                gain=gain,
                matched_overlap_reports=matched_overlap,
                linked_incident_ids=linked_ids,
                noise_report_count=sum(
                    links[report_id].incident_id is None for report_id in unit.report_ids
                ),
                is_split=is_split,
                is_merge=is_merge,
                disposition=disposition,
            )
        )
    gains = {row.unit_id: row.gain for row in evaluated}
    alignment_rows: list[Mapping[str, Any]] = []
    for policy, score_map in sorted(scored.policy_score_maps.items()):
        alignment_rows.append(
            {
                "policy": policy,
                "evaluation_partition": "predicted_clusters_one_to_one_max_overlap",
                "metrics": ranking_metrics(score_map, gains, k=k),
            }
        )
    return PredictedPriorityEvaluationV2(
        scored=scored,
        evaluated_units=tuple(evaluated),
        alignment_rows=tuple(alignment_rows),
        unmatched_incident_ids=tuple(sorted(set(incidents).difference(matched_incidents))),
    )


@dataclass(frozen=True, slots=True)
class ObservablePriorityStressCaseV2:
    """Observable-only perturbation; evaluator linkage is attached separately."""

    family: StressFamilyV2
    original_report_ids: tuple[str, ...]
    reports: tuple[ReportV2, ...]
    predicted_labels: tuple[int, ...]
    target_unit_id: str
    target_cluster_label: int
    source_report_id: str
    injected_linkage_sources: tuple[tuple[str, str | None], ...]
    modified_report_ids: tuple[str, ...]

    @property
    def injected_report_ids(self) -> tuple[str, ...]:
        return tuple(identifier for identifier, _ in self.injected_linkage_sources)

    @property
    def campaign_report_ids(self) -> tuple[str, ...]:
        if self.family != "coordinated_high_confidence_campaign":
            return ()
        return self.injected_report_ids


def _east_offset(location: tuple[float, float], east_m: float) -> tuple[float, float]:
    latitude, longitude = location
    cosine = max(1e-6, math.cos(math.radians(latitude)))
    return latitude, longitude + east_m / (111_000.0 * cosine)


def _stress_identifier(
    family: StressFamilyV2,
    target_unit_id: str,
    index: int,
) -> str:
    return f"stress-{family.lower()}-{target_unit_id[-16:]}-{index}"


def build_observable_priority_stress(
    reports: Sequence[ReportV2],
    predicted_labels: Sequence[int],
    family: StressFamilyV2,
    policy: PriorityPolicyV2 = PriorityPolicyV2(),
    *,
    noise_label: int = -1,
    base_scored: PredictedPriorityScoresV2 | None = None,
) -> ObservablePriorityStressCaseV2:
    """Build one priority stress case without accepting or consulting truth.

    The target is the lexicographically first membership-hash unit, an entirely
    observable deterministic rule.  All non-campaign injections remain in that
    predicted cluster.  A coordinated campaign forms a new predicted unit and
    is marked for evaluator-side noise linkage.
    """

    if family not in STRESS_FAMILIES_V2:
        raise PriorityEvaluationV2Error(f"unsupported stress family: {family}")
    labels = _normalise_labels(reports, predicted_labels, noise_label)
    if base_scored is None:
        base_scored = score_predicted_priority(
            reports,
            labels,
            policy,
            noise_label=noise_label,
        )
    elif (
        base_scored.observable_report_ids
        != tuple(sorted(report.report_id for report in reports))
        or base_scored.noise_label != noise_label
    ):
        raise PriorityEvaluationV2Error(
            "precomputed base scores do not match the observable stress input"
        )
    if not base_scored.units:
        raise PriorityEvaluationV2Error(
            "cannot construct a priority stress case without a predicted unit"
        )
    target = min(base_scored.units, key=lambda row: row.unit_id)
    report_by_id = {report.report_id: report for report in reports}
    base = report_by_id[min(target.report_ids)]
    if base.L is None or base.T is None:
        raise PriorityEvaluationV2Error("stress target must have observable L and T")
    existing_ids = set(report_by_id)
    records: dict[str, tuple[ReportV2, int]] = {
        report.report_id: (report, label)
        for report, label in zip(reports, labels, strict=True)
    }
    injected: list[tuple[str, str | None]] = []
    modified: list[str] = []

    def add(report: ReportV2, label: int, source_report_id: str | None) -> None:
        if report.report_id in existing_ids or report.report_id in records:
            raise PriorityEvaluationV2Error(
                f"stress report id collision: {report.report_id}"
            )
        records[report.report_id] = (report, label)
        injected.append((report.report_id, source_report_id))

    if family == "exact_duplicate":
        identifier = _stress_identifier(family, target.unit_id, 0)
        add(replace(base, report_id=identifier), target.cluster_label, base.report_id)
    elif family == "near_duplicate":
        identifier = _stress_identifier(family, target.unit_id, 0)
        add(
            replace(
                base,
                report_id=identifier,
                L=_east_offset(base.L, 25.0),
                T=base.T + timedelta(minutes=1),
                F=None if base.F is None else min(1.0, base.F + 0.01),
                E=None if base.E is None else min(1.0, base.E + 0.01),
            ),
            target.cluster_label,
            base.report_id,
        )
    elif family == "gradual_chain_duplicate":
        for index in range(1, 5):
            identifier = _stress_identifier(family, target.unit_id, index)
            add(
                replace(
                    base,
                    report_id=identifier,
                    L=_east_offset(base.L, 65.0 * index),
                    T=base.T + timedelta(minutes=index),
                ),
                target.cluster_label,
                base.report_id,
            )
    elif family.startswith("low_confidence_"):
        field = family.rsplit("_", 1)[1]
        identifier = _stress_identifier(family, target.unit_id, 0)
        replacements: dict[str, Any] = {
            "report_id": identifier,
            "provenance_quality": 0.01,
            "has_image": False,
            "mask": None,
            field: 1.0 if field in {"E", "F"} else (500.0 if field == "N" else 50.0),
        }
        add(
            replace(base, **replacements),
            target.cluster_label,
            base.report_id,
        )
    elif family == "missingness":
        for report_id in target.report_ids[::2]:
            report, label = records[report_id]
            records[report_id] = (
                replace(report, E=None, F=None, N=None, V=None, mask=None),
                label,
            )
            modified.append(report_id)
    elif family == "contradictory_reports":
        identifier = _stress_identifier(family, target.unit_id, 0)
        add(
            replace(
                base,
                report_id=identifier,
                F=None if base.F is None else 1.0 - base.F,
                E=None if base.E is None else 1.0 - base.E,
                provenance_quality=0.70,
            ),
            target.cluster_label,
            base.report_id,
        )
    elif family == "coordinated_high_confidence_campaign":
        campaign_label = max(
            (label for label in labels if label != noise_label),
            default=-1,
        ) + 1
        for index in range(5):
            identifier = _stress_identifier(family, target.unit_id, index)
            add(
                replace(
                    base,
                    report_id=identifier,
                    source_id=f"campaign-source-{index}",
                    source_family=f"campaign-family-{index}",
                    provenance_quality=0.98,
                    has_image=True,
                    L=_east_offset(base.L, 8.0 * index),
                    T=base.T + timedelta(seconds=20 * index),
                    F=0.99,
                    E=0.99,
                    N=500.0,
                    V=50.0,
                    mask=None,
                ),
                campaign_label,
                None,
            )
    else:  # pragma: no cover - Literal plus membership check makes this unreachable.
        raise AssertionError(f"unhandled stress family: {family}")

    ordered = [records[identifier] for identifier in sorted(records)]
    return ObservablePriorityStressCaseV2(
        family=family,
        original_report_ids=tuple(sorted(existing_ids)),
        reports=tuple(report for report, _ in ordered),
        predicted_labels=tuple(label for _, label in ordered),
        target_unit_id=target.unit_id,
        target_cluster_label=target.cluster_label,
        source_report_id=base.report_id,
        injected_linkage_sources=tuple(sorted(injected)),
        modified_report_ids=tuple(sorted(modified)),
    )


def attach_evaluator_truth_to_stress(
    case: ObservablePriorityStressCaseV2,
    report_truth: Sequence[TruthV2],
) -> tuple[TruthV2, ...]:
    """Attach truth after perturbation scoring; campaigns remain explicit noise."""

    truth_by_id = {row.report_id: row for row in report_truth}
    if len(truth_by_id) != len(report_truth):
        raise PriorityEvaluationV2Error("report truth ids must be unique")
    if set(truth_by_id) != set(case.original_report_ids):
        raise PriorityEvaluationV2Error(
            "stress truth must cover the original observable reports exactly"
        )
    output = dict(truth_by_id)
    for report_id, source_report_id in case.injected_linkage_sources:
        if source_report_id is None:
            output[report_id] = TruthV2(
                report_id=report_id,
                incident_id=None,
                gt_cluster=None,
                is_noise=True,
                is_fake=True,
            )
        else:
            if source_report_id not in truth_by_id:
                raise PriorityEvaluationV2Error(
                    f"stress linkage source is absent: {source_report_id}"
                )
            output[report_id] = replace(
                truth_by_id[source_report_id],
                report_id=report_id,
            )
    expected = {report.report_id for report in case.reports}
    if set(output) != expected:
        raise PriorityEvaluationV2Error(
            "stress truth extension does not match perturbed reports"
        )
    return tuple(output[identifier] for identifier in sorted(output))


@dataclass(frozen=True, slots=True)
class PriorityStressEvaluationV2:
    case: ObservablePriorityStressCaseV2
    base: PredictedPriorityEvaluationV2
    stressed: PredictedPriorityEvaluationV2
    stressed_report_truth: tuple[TruthV2, ...]
    stress_rows: tuple[Mapping[str, Any], ...]


def _alignment_by_policy(
    evaluation: PredictedPriorityEvaluationV2,
) -> dict[str, Mapping[str, Any]]:
    return {str(row["policy"]): row for row in evaluation.alignment_rows}


def evaluate_priority_stress(
    reports: Sequence[ReportV2],
    predicted_labels: Sequence[int],
    report_truth: Sequence[TruthV2],
    incident_truth: Sequence[IncidentTruthV2],
    family: StressFamilyV2,
    policy: PriorityPolicyV2 = PriorityPolicyV2(),
    *,
    noise_label: int = -1,
    k: int = 5,
    base_scored: PredictedPriorityScoresV2 | None = None,
    base_evaluation: PredictedPriorityEvaluationV2 | None = None,
) -> PriorityStressEvaluationV2:
    """Score both observable states before any evaluator truth is attached.

    The convenience function accepts truth for the final evaluation, but the
    first four operations below are deliberately truth-free.  Tests can inspect
    the returned score sets and schedule payloads to enforce this boundary.
    """

    if base_scored is None:
        base_scored = score_predicted_priority(
            reports,
            predicted_labels,
            policy,
            noise_label=noise_label,
        )
    case = build_observable_priority_stress(
        reports,
        predicted_labels,
        family,
        policy,
        noise_label=noise_label,
        base_scored=base_scored,
    )
    stressed_scored = score_predicted_priority(
        case.reports,
        case.predicted_labels,
        policy,
        noise_label=noise_label,
    )

    # Evaluator-only phase starts here.
    stressed_truth = attach_evaluator_truth_to_stress(case, report_truth)
    if base_evaluation is None:
        base_evaluation = evaluate_predicted_priority(
            base_scored,
            report_truth,
            incident_truth,
            k=k,
        )
    elif base_evaluation.scored != base_scored:
        raise PriorityEvaluationV2Error(
            "precomputed base evaluation does not match the base scores"
        )
    stressed_evaluation = evaluate_predicted_priority(
        stressed_scored,
        stressed_truth,
        incident_truth,
        k=k,
    )
    base_by_label = {unit.cluster_label: unit for unit in base_scored.units}
    stressed_by_label = {unit.cluster_label: unit for unit in stressed_scored.units}
    if not set(base_by_label).issubset(stressed_by_label):
        raise PriorityEvaluationV2Error(
            "stress perturbation removed an original predicted unit"
        )
    before_alignment = _alignment_by_policy(base_evaluation)
    after_alignment = _alignment_by_policy(stressed_evaluation)
    campaign_ids = set(case.campaign_report_ids)
    campaign_units = [
        unit
        for unit in stressed_scored.units
        if campaign_ids.intersection(unit.report_ids)
    ]
    rows: list[Mapping[str, Any]] = []
    for policy_id in base_scored.policy_ids:
        original = {
            unit.unit_id: unit.score_map[policy_id] for unit in base_scored.units
        }
        perturbed = {
            unit.unit_id: stressed_by_label[unit.cluster_label].score_map[policy_id]
            for unit in base_scored.units
        }
        campaign_score = max(
            (unit.score_map[policy_id] for unit in campaign_units),
            default=0.0,
        )
        scale = max(
            1.0,
            campaign_score,
            max((abs(value) for value in original.values()), default=0.0),
        )
        rows.append(
            {
                "family": family,
                "policy": policy_id,
                "target_selection": "observable_minimum_membership_hash",
                "drift": perturbation_drift(original, perturbed, k=k),
                "false_priority_lift": {
                    "applicable": family
                    == "coordinated_high_confidence_campaign",
                    "raw_campaign_score": campaign_score,
                    "normalization_scale": scale,
                    "normalized_score_change": campaign_score / scale,
                    "n_campaign_units": len(campaign_units),
                },
                "alignment_before": before_alignment[policy_id]["metrics"],
                "alignment_after": after_alignment[policy_id]["metrics"],
            }
        )
    return PriorityStressEvaluationV2(
        case=case,
        base=base_evaluation,
        stressed=stressed_evaluation,
        stressed_report_truth=stressed_truth,
        stress_rows=tuple(rows),
    )


__all__ = [
    "EvaluatedPriorityUnitV2",
    "ObservablePriorityStressCaseV2",
    "PredictedPriorityEvaluationV2",
    "PredictedPriorityScoresV2",
    "PredictedPriorityUnitV2",
    "PriorityEvaluationV2Error",
    "PriorityStressEvaluationV2",
    "STRESS_FAMILIES_V2",
    "StressFamilyV2",
    "attach_evaluator_truth_to_stress",
    "build_observable_priority_stress",
    "evaluate_predicted_priority",
    "evaluate_priority_stress",
    "score_predicted_priority",
]
