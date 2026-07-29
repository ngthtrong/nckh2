"""Experiment 16: duplicate, adversarial, and missingness priority robustness.

The experiment is a pre-Gate-2 analysis.  It runs only on the restricted
development/calibration protocol view, evaluates every declared threat for
both locked priority estimators, and retains adverse and tied results.
"""
from __future__ import annotations

import argparse
import math
import sys
from collections import defaultdict
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from statistics import mean
from typing import Iterable, Sequence

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from demo.experiments.pre_gate2 import (  # noqa: E402
    DEFAULT_GATE1_LOCK,
    PRE_GATE2_STAGES,
    default_table_path,
    load_frozen_tuning_views,
    protocol_record,
    resolve_frozen_dataset_root,
    restricted_protocol_and_seeds,
    write_exclusive_json,
)
from demo.experiments.protocol import TuningProtocol, load_tuning_protocol  # noqa: E402
from demo.experiments.inference import (  # noqa: E402
    apply_holm,
    descriptive_summary,
    paired_comparison,
)
from demo.pipeline.attributes import Event, compute_confidence, haversine_m  # noqa: E402
from demo.pipeline.config import DEFAULT_CONFIG  # noqa: E402
from demo.pipeline.priority import (  # noqa: E402
    LEGACY_ESTIMATOR_NAME,
    REVISED_ESTIMATOR_NAME,
    NearDuplicatePolicy,
    are_near_duplicate_reports,
    priority_range,
    score_clusters,
)


ESTIMATORS = (REVISED_ESTIMATOR_NAME, LEGACY_ESTIMATOR_NAME)
EXACT_MULTIPLICITIES = (2, 5, 10)
SUMMARY_METRICS = (
    "priority_drift_abs_normalized",
    "mean_rank_drift_normalized",
    "top_k_churn",
    "n_error_relative_after",
    "v_error_relative_after",
)


def _incident_maps(data: dict) -> tuple[dict[str, dict], dict[int, str]]:
    by_id = {
        str(incident["incident_id"]): incident
        for incident in data["incidents"]
    }
    by_gt = {
        int(incident["gt_cluster"]): str(incident["incident_id"])
        for incident in data["incidents"]
    }
    return by_id, by_gt


def _group_operational_events(
    data: dict,
    events_by_id: dict[str, Event],
) -> tuple[dict[str, list[Event]], dict[str, list[Event]]]:
    """Return full linked groups and one-representative-per-duplicate groups."""

    full: dict[str, list[Event]] = defaultdict(list)
    duplicate_families: dict[tuple[str, str], list[str]] = defaultdict(list)
    ordinary_ids: dict[str, list[str]] = defaultdict(list)
    for report in data["reports"]:
        evaluation = report["evaluation_only"]
        incident_id = evaluation["incident_id"]
        if incident_id is None:
            continue
        incident_key = str(incident_id)
        event_id = str(report["event_id"])
        full[incident_key].append(events_by_id[event_id])
        family_id = evaluation["duplicate_family_id"]
        if family_id is None:
            ordinary_ids[incident_key].append(event_id)
        else:
            duplicate_families[(incident_key, str(family_id))].append(event_id)

    clean_ids: dict[str, list[str]] = defaultdict(list)
    for incident_id, event_ids in ordinary_ids.items():
        clean_ids[incident_id].extend(event_ids)
    for (incident_id, _), event_ids in duplicate_families.items():
        clean_ids[incident_id].append(min(event_ids))

    clean = {
        incident_id: [
            events_by_id[event_id] for event_id in sorted(clean_ids[incident_id])
        ]
        for incident_id in sorted(full)
    }
    full_sorted = {
        incident_id: sorted(events, key=lambda event: str(event.event_id))
        for incident_id, events in sorted(full.items())
    }
    return full_sorted, clean


def _copy_groups(groups: dict[str, list[Event]]) -> dict[str, list[Event]]:
    return {
        incident_id: list(events)
        for incident_id, events in groups.items()
    }


def _prepared_score_inputs(
    groups: dict[str, list[Event]],
    incidents: dict[str, dict],
    *,
    confidence_override: dict[str, float] | None = None,
) -> tuple[list[Event], list[int], dict[str, float]]:
    """Create a fresh inference-only view and recompute confidence per scenario."""

    events: list[Event] = []
    labels: list[int] = []
    for incident_id in sorted(groups):
        label = int(incidents[incident_id]["gt_cluster"])
        for event in sorted(groups[incident_id], key=lambda row: str(row.event_id)):
            events.append(replace(event))
            labels.append(label)
    if confidence_override is None:
        compute_confidence(events, DEFAULT_CONFIG.confidence)
    else:
        missing_ids = [
            str(event.event_id)
            for event in events
            if str(event.event_id) not in confidence_override
        ]
        if missing_ids:
            raise ValueError(
                "confidence override misses scenario event ids: "
                + ", ".join(missing_ids[:3])
            )
        for event in events:
            event.confidence = float(confidence_override[str(event.event_id)])
    confidence = {
        str(event.event_id): float(event.confidence) for event in events
    }
    return events, labels, confidence


def _score_bundle(
    groups: dict[str, list[Event]],
    incidents: dict[str, dict],
    incidents_by_gt: dict[int, str],
    *,
    confidence_override: dict[str, float] | None = None,
) -> dict[str, object]:
    events, labels, confidence = _prepared_score_inputs(
        groups,
        incidents,
        confidence_override=confidence_override,
    )
    return {
        "events": events,
        "labels": labels,
        "confidence": confidence,
        "scores": {
            estimator: _score_map(
                events,
                labels,
                incidents_by_gt,
                estimator,
            )
            for estimator in ESTIMATORS
        },
    }


def _score_map(
    events: list[Event],
    labels: list[int],
    incidents_by_gt: dict[int, str],
    estimator: str,
) -> dict[str, object]:
    scores = score_clusters(
        events,
        labels,
        DEFAULT_CONFIG.priority,
        estimator=estimator,
    )
    return {
        incidents_by_gt[int(score.cluster_id)]: score
        for score in scores
    }


def _rank_diagnostics(
    before: dict[str, object],
    after: dict[str, object],
    target_incident_id: str,
) -> dict[str, float | int]:
    def ranks(scores: dict[str, object]) -> dict[str, int]:
        ordered = sorted(
            scores,
            key=lambda incident_id: (
                -float(scores[incident_id].priority),  # type: ignore[attr-defined]
                incident_id,
            ),
        )
        return {incident_id: index + 1 for index, incident_id in enumerate(ordered)}

    before_ranks = ranks(before)
    after_ranks = ranks(after)
    count = len(before_ranks)
    denominator = max(1, count - 1)
    top_k = min(5, count)
    before_top = {
        incident_id
        for incident_id, rank in before_ranks.items()
        if rank <= top_k
    }
    after_top = {
        incident_id
        for incident_id, rank in after_ranks.items()
        if rank <= top_k
    }
    return {
        "target_rank_before": before_ranks[target_incident_id],
        "target_rank_after": after_ranks[target_incident_id],
        "target_rank_shift": (
            after_ranks[target_incident_id]
            - before_ranks[target_incident_id]
        ),
        "mean_rank_drift_normalized": round(
            mean(
                abs(after_ranks[incident_id] - before_ranks[incident_id])
                / denominator
                for incident_id in before_ranks
            ),
            8,
        ),
        "top_k": top_k,
        "top_k_churn": round(
            1.0 - len(before_top.intersection(after_top)) / top_k,
            8,
        ),
    }


def _relative_error(estimate: float, truth: float) -> float:
    return abs(estimate - truth) / max(abs(truth), 1.0)


def _standalone_false_priority(
    attack_events: Sequence[Event],
) -> dict[str, float] | None:
    if not attack_events:
        return None
    events = [replace(event) for event in attack_events]
    compute_confidence(events, DEFAULT_CONFIG.confidence)
    lower, upper = priority_range(DEFAULT_CONFIG.priority)
    return {
        estimator: round(
            (
                score_clusters(
                    events,
                    [0] * len(events),
                    DEFAULT_CONFIG.priority,
                    estimator=estimator,
                )[0].priority
                - lower
            )
            / (upper - lower),
            8,
        )
        for estimator in ESTIMATORS
    }


def _evaluate_scenario(
    *,
    seed: int,
    stage: str,
    scenario: str,
    target_incident_id: str,
    before_groups: dict[str, list[Event]],
    after_groups: dict[str, list[Event]],
    incidents: dict[str, dict],
    incidents_by_gt: dict[int, str],
    attack_events: Sequence[Event] = (),
    false_attack: bool = False,
    metadata: dict[str, object] | None = None,
    before_bundle: dict[str, object] | None = None,
    after_bundle: dict[str, object] | None = None,
    before_confidence_override: dict[str, float] | None = None,
) -> list[dict[str, object]]:
    before_bundle = before_bundle or _score_bundle(
        before_groups,
        incidents,
        incidents_by_gt,
        confidence_override=before_confidence_override,
    )
    after_bundle = after_bundle or _score_bundle(
        after_groups,
        incidents,
        incidents_by_gt,
    )
    after_confidence = after_bundle["confidence"]
    attack_confidences = [
        after_confidence[str(event.event_id)]  # type: ignore[index]
        for event in attack_events
        if str(event.event_id) in after_confidence
    ]
    truth = incidents[target_incident_id]
    lower, upper = priority_range(DEFAULT_CONFIG.priority)
    declared_width = upper - lower
    rows: list[dict[str, object]] = []
    standalone_false = (
        _standalone_false_priority(attack_events) if false_attack else None
    )
    for estimator in ESTIMATORS:
        before_scores = before_bundle["scores"][estimator]  # type: ignore[index]
        after_scores = after_bundle["scores"][estimator]  # type: ignore[index]
        before = before_scores[target_incident_id]
        after = after_scores[target_incident_id]
        n_truth = float(truth["n_true"])
        v_truth = float(truth["v_true"])
        n_error_before = _relative_error(float(before.n_total_raw), n_truth)
        n_error_after = _relative_error(float(after.n_total_raw), n_truth)
        v_error_before = _relative_error(float(before.v_total_raw), v_truth)
        v_error_after = _relative_error(float(after.v_total_raw), v_truth)
        signed_drift = float(after.priority) - float(before.priority)
        row: dict[str, object] = {
            "seed": int(seed),
            "stage": stage,
            "scenario": scenario,
            "estimator": estimator,
            "target_incident_id": target_incident_id,
            "target_scenario_family": str(truth["scenario_family"]),
            "n_true": int(truth["n_true"]),
            "v_true": int(truth["v_true"]),
            "priority_before": float(before.priority),
            "priority_after": float(after.priority),
            "priority_drift_signed": round(signed_drift, 8),
            "priority_drift_abs_normalized": round(
                abs(signed_drift) / declared_width,
                8,
            ),
            "n_evidence_before": float(before.n_total_raw),
            "n_evidence_after": float(after.n_total_raw),
            "v_evidence_before": float(before.v_total_raw),
            "v_evidence_after": float(after.v_total_raw),
            "n_error_relative_before": round(n_error_before, 8),
            "n_error_relative_after": round(n_error_after, 8),
            "n_error_relative_delta": round(
                n_error_after - n_error_before,
                8,
            ),
            "v_error_relative_before": round(v_error_before, 8),
            "v_error_relative_after": round(v_error_after, 8),
            "v_error_relative_delta": round(
                v_error_after - v_error_before,
                8,
            ),
            "evidence_units_before": int(before.evidence_units),
            "evidence_units_after": int(after.evidence_units),
            "exact_duplicates_removed_after": int(
                after.exact_duplicates_removed
            ),
            "near_duplicates_coalesced_after": int(
                after.near_duplicates_coalesced
            ),
            "attack_report_count": len(attack_events),
            "attack_confidence_mean": (
                None
                if not attack_confidences
                else round(mean(attack_confidences), 8)
            ),
            "attack_confidence_max": (
                None
                if not attack_confidences
                else round(max(attack_confidences), 8)
            ),
            "false_priority_lift_normalized": (
                standalone_false[estimator]
                if standalone_false is not None
                else None
            ),
            **_rank_diagnostics(
                before_scores,
                after_scores,
                target_incident_id,
            ),
            "metadata": metadata or {},
        }
        rows.append(row)
    return rows


def _nearest_incident_id(
    event: Event,
    incidents: dict[str, dict],
) -> str:
    return min(
        incidents,
        key=lambda incident_id: (
            haversine_m(
                event.lat,
                event.lng,
                float(incidents[incident_id]["center_lat"]),
                float(incidents[incident_id]["center_lng"]),
            ),
            incident_id,
        ),
    )


def _oracle_complete_event(
    event: Event,
    report: dict,
    incident: dict,
) -> Event:
    missing = set(event.missing_fields)
    evaluation = report["evaluation_only"]
    return replace(
        event,
        flood=(
            float(incident["generator_profile"]["flood_latent"])
            if "flood" in missing
            else event.flood
        ),
        urgency=(
            float(incident["generator_profile"]["urgency_latent"])
            if "urgency" in missing
            else event.urgency
        ),
        n_trapped=(
            len(evaluation["population_member_indices"])
            if "n_trapped" in missing
            else event.n_trapped
        ),
        vulnerability=(
            float(len(evaluation["vulnerable_member_indices"]))
            if "vulnerability" in missing
            else event.vulnerability
        ),
        missing_fields=(),
    )


def evaluate_loaded_priority_seed(
    *,
    seed: int,
    stage: str,
    inference_events: Sequence[Event],
    evaluator_data: dict,
    source_sha256: str,
) -> list[dict[str, object]]:
    """Run every C3 scenario after an authenticated view has been loaded.

    The caller supplies sanitized inference events separately from evaluator
    annotations.  This pure post-load entry point is shared by the restricted
    calibration runner and the one-shot held-out runner.
    """

    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    if not isinstance(stage, str) or not stage:
        raise ValueError("stage must be a non-empty string")
    if not isinstance(evaluator_data, dict):
        raise ValueError("evaluator_data must be an object")
    if not isinstance(source_sha256, str) or len(source_sha256) != 64:
        raise ValueError("source_sha256 must be a SHA-256 identity")
    inference_events = list(inference_events)
    if any(
        event.gt_cluster != -1 or event.is_fake is not False
        for event in inference_events
    ):
        raise ValueError("evaluator-only fields leaked into priority inputs")
    data = evaluator_data
    events_by_id = {
        str(event.event_id): event for event in inference_events
    }
    reports_by_id = {
        str(report["event_id"]): report for report in data["reports"]
    }
    incidents, incidents_by_gt = _incident_maps(data)
    _, clean_groups = _group_operational_events(data, events_by_id)
    clean_bundle = _score_bundle(
        clean_groups,
        incidents,
        incidents_by_gt,
    )
    clean_confidence = clean_bundle["confidence"]
    rows: list[dict[str, object]] = []

    exact_target = min(clean_groups)
    exact_anchor = min(
        clean_groups[exact_target],
        key=lambda event: str(event.event_id),
    )
    for multiplicity in EXACT_MULTIPLICITIES:
        attacked = _copy_groups(clean_groups)
        artificial = [
            replace(
                exact_anchor,
                event_id=(
                    f"{exact_anchor.event_id}-exact-{multiplicity}-{copy_index}"
                ),
            )
            for copy_index in range(1, multiplicity)
        ]
        attacked[exact_target].extend(artificial)
        rows.extend(
            _evaluate_scenario(
                seed=seed,
                stage=stage,
                scenario=f"exact_duplicate_{multiplicity}x",
                target_incident_id=exact_target,
                before_groups=clean_groups,
                after_groups=attacked,
                incidents=incidents,
                incidents_by_gt=incidents_by_gt,
                attack_events=artificial,
                before_bundle=clean_bundle,
                metadata={
                    "total_observable_multiplicity": multiplicity,
                    "counterfactual": "same observable payload; new transport ids",
                },
            )
        )

    near_families: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for report in data["reports"]:
        evaluation = report["evaluation_only"]
        if (
            evaluation["incident_id"] is not None
            and evaluation["duplicate_kind"] == "near"
        ):
            near_families[
                (
                    str(evaluation["incident_id"]),
                    str(evaluation["duplicate_family_id"]),
                )
            ].append(report)
    for (incident_id, family_id), reports in sorted(near_families.items()):
        reports = sorted(reports, key=lambda report: str(report["event_id"]))
        representative = events_by_id[str(reports[0]["event_id"])]
        additions = [
            events_by_id[str(report["event_id"])] for report in reports[1:]
        ]
        attacked = _copy_groups(clean_groups)
        attacked[incident_id].extend(additions)
        recognized = all(
            are_near_duplicate_reports(representative, addition)
            for addition in additions
        )
        rows.extend(
            _evaluate_scenario(
                seed=seed,
                stage=stage,
                scenario="near_duplicate",
                target_incident_id=incident_id,
                before_groups=clean_groups,
                after_groups=attacked,
                incidents=incidents,
                incidents_by_gt=incidents_by_gt,
                attack_events=additions,
                before_bundle=clean_bundle,
                metadata={
                    "duplicate_family_id": family_id,
                    "observable_near_policy_recognized_before_confidence_recompute": (
                        recognized
                    ),
                },
            )
        )

    adversary_reports: dict[str, list[dict]] = defaultdict(list)
    for report in data["reports"]:
        adversary = report["evaluation_only"]["adversary"]
        if adversary is not None:
            adversary_reports[str(adversary)].append(report)
    for field in ("N", "V", "F", "E"):
        adversary = f"low_conf_inflate_{field}"
        attack_reports = sorted(
            adversary_reports[adversary],
            key=lambda report: str(report["event_id"]),
        )
        attack_events = [
            events_by_id[str(report["event_id"])] for report in attack_reports
        ]
        target = _nearest_incident_id(attack_events[0], incidents)
        attacked = _copy_groups(clean_groups)
        attacked[target].extend(attack_events)
        rows.extend(
            _evaluate_scenario(
                seed=seed,
                stage=stage,
                scenario=f"low_confidence_inflate_{field}",
                target_incident_id=target,
                before_groups=clean_groups,
                after_groups=attacked,
                incidents=incidents,
                incidents_by_gt=incidents_by_gt,
                attack_events=attack_events,
                false_attack=True,
                before_bundle=clean_bundle,
                metadata={
                    "association_assumption": (
                        "worst-case false association to nearest incident"
                    ),
                    "inflated_field": field,
                },
            )
        )

    campaign_reports = sorted(
        adversary_reports["coordinated_high_conf_campaign"],
        key=lambda report: str(report["event_id"]),
    )
    campaign_events = [
        events_by_id[str(report["event_id"])] for report in campaign_reports
    ]
    campaign_target = _nearest_incident_id(campaign_events[0], incidents)
    campaign_attacked = _copy_groups(clean_groups)
    campaign_attacked[campaign_target].extend(campaign_events)
    rows.extend(
        _evaluate_scenario(
            seed=seed,
            stage=stage,
            scenario="coordinated_high_confidence_campaign",
            target_incident_id=campaign_target,
            before_groups=clean_groups,
            after_groups=campaign_attacked,
            incidents=incidents,
            incidents_by_gt=incidents_by_gt,
            attack_events=campaign_events,
            false_attack=True,
            before_bundle=clean_bundle,
            metadata={
                "association_assumption": (
                    "worst-case false association to nearest incident"
                ),
                "known_failure_mode": (
                    "distinct corroborating high-confidence claims can alter rank"
                ),
            },
        )
    )

    for incident_id in sorted(clean_groups):
        missing_ids = [
            str(event.event_id)
            for event in clean_groups[incident_id]
            if event.missing_fields
        ]
        if not missing_ids:
            continue
        oracle = _copy_groups(clean_groups)
        oracle[incident_id] = [
            (
                _oracle_complete_event(
                    event,
                    reports_by_id[str(event.event_id)],
                    incidents[incident_id],
                )
                if str(event.event_id) in missing_ids
                else event
            )
            for event in clean_groups[incident_id]
        ]
        rows.extend(
            _evaluate_scenario(
                seed=seed,
                stage=stage,
                scenario="source_missingness_zero_imputation",
                target_incident_id=incident_id,
                before_groups=oracle,
                after_groups=clean_groups,
                incidents=incidents,
                incidents_by_gt=incidents_by_gt,
                attack_events=[
                    events_by_id[event_id] for event_id in missing_ids
                ],
                after_bundle=clean_bundle,
                before_confidence_override=clean_confidence,  # type: ignore[arg-type]
                metadata={
                    "n_missing_reports": len(missing_ids),
                    "comparator": (
                        "evaluator-only oracle completion from latent membership "
                        "and incident context; never used for method selection"
                    ),
                },
            )
        )
    for row in rows:
        row["dataset_source_sha256"] = source_sha256
    return rows


def _run_seed_from_frozen_root(
    dataset_root: Path,
    seed: int,
    stage: str,
    protocol: TuningProtocol,
    gate1_lock: Path | str,
) -> list[dict[str, object]]:
    """Load one restricted split and run the shared C3 evaluator."""

    if stage not in PRE_GATE2_STAGES:
        raise ValueError("run_seed accepts only development/calibration")
    tuning_dataset, data = load_frozen_tuning_views(
        dataset_root,
        stage=stage,
        seed=int(seed),
        tuning_protocol=protocol,
        gate1_lock=gate1_lock,
    )
    return evaluate_loaded_priority_seed(
        seed=int(seed),
        stage=stage,
        inference_events=tuning_dataset.events,
        evaluator_data=data,
        source_sha256=tuning_dataset.source_sha256,
    )


def run_seed(
    seed: int,
    stage: str,
    *,
    dataset_root: Path | str | None = None,
    gate1_lock: Path | str = DEFAULT_GATE1_LOCK,
    protocol: TuningProtocol | None = None,
) -> list[dict[str, object]]:
    """Public one-seed entry point bound to the accepted Gate-1 bundle."""

    root, _ = resolve_frozen_dataset_root(
        dataset_root,
        gate1_lock=gate1_lock,
    )
    locked = protocol or load_tuning_protocol()
    return _run_seed_from_frozen_root(
        root,
        seed,
        stage,
        locked,
        gate1_lock,
    )


def _seed_aggregates(
    rows: Sequence[dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[
        tuple[str, int, str, str],
        list[dict[str, object]],
    ] = defaultdict(list)
    for row in rows:
        grouped[
            (
                str(row["stage"]),
                int(row["seed"]),
                str(row["scenario"]),
                str(row["estimator"]),
            )
        ].append(row)
    result: list[dict[str, object]] = []
    for (stage, seed, scenario, estimator), selected in sorted(grouped.items()):
        aggregate: dict[str, object] = {
            "stage": stage,
            "seed": seed,
            "scenario": scenario,
            "estimator": estimator,
            "n_scenario_rows": len(selected),
        }
        for metric in SUMMARY_METRICS:
            aggregate[metric] = round(
                mean(float(row[metric]) for row in selected),
                8,
            )
        false_values = [
            float(row["false_priority_lift_normalized"])
            for row in selected
            if row["false_priority_lift_normalized"] is not None
        ]
        aggregate["false_priority_lift_normalized"] = (
            None if not false_values else round(mean(false_values), 8)
        )
        result.append(aggregate)
    return result


def _summaries(
    seed_rows: Sequence[dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[
        tuple[str, str, str],
        list[dict[str, object]],
    ] = defaultdict(list)
    for row in seed_rows:
        grouped[
            (
                str(row["stage"]),
                str(row["scenario"]),
                str(row["estimator"]),
            )
        ].append(row)
    summaries: list[dict[str, object]] = []
    for (stage, scenario, estimator), selected in sorted(grouped.items()):
        summary: dict[str, object] = {
            "stage": stage,
            "scenario": scenario,
            "estimator": estimator,
            "n_seed_units": len(selected),
        }
        for metric in SUMMARY_METRICS:
            summary[metric] = descriptive_summary(
                [float(row[metric]) for row in selected],
                denominator={
                    "seed_units": len(selected),
                    "scenario_rows": sum(
                        int(row["n_scenario_rows"]) for row in selected
                    ),
                },
            )
        false_values = [
            float(row["false_priority_lift_normalized"])
            for row in selected
            if row["false_priority_lift_normalized"] is not None
        ]
        summary["false_priority_lift_normalized"] = (
            None
            if not false_values
            else descriptive_summary(
                false_values,
                denominator={
                    "seed_units": len(false_values),
                    "false_attack_scenario_rows": sum(
                        int(row["n_scenario_rows"]) for row in selected
                    ),
                },
            )
        )
        summaries.append(summary)
    return summaries


def _paired_estimator_effects(
    seed_rows: Sequence[dict[str, object]],
) -> list[dict[str, object]]:
    by_key = {
        (
            str(row["stage"]),
            int(row["seed"]),
            str(row["scenario"]),
            str(row["estimator"]),
        ): row
        for row in seed_rows
    }
    scenarios = sorted({str(row["scenario"]) for row in seed_rows})
    stages = sorted({str(row["stage"]) for row in seed_rows})
    effects: list[dict[str, object]] = []
    for stage in stages:
        for scenario in scenarios:
            seeds = sorted(
                {
                    int(row["seed"])
                    for row in seed_rows
                    if row["stage"] == stage and row["scenario"] == scenario
                }
            )
            metrics = list(SUMMARY_METRICS)
            if all(
                by_key[(stage, seed, scenario, REVISED_ESTIMATOR_NAME)][
                    "false_priority_lift_normalized"
                ]
                is not None
                for seed in seeds
            ):
                metrics.append("false_priority_lift_normalized")
            comparison_family: dict[str, dict[str, object]] = {}
            for metric in metrics:
                robust = [
                    float(
                        by_key[
                            (stage, seed, scenario, REVISED_ESTIMATOR_NAME)
                        ][metric]
                    )
                    for seed in seeds
                ]
                legacy = [
                    float(
                        by_key[
                            (stage, seed, scenario, LEGACY_ESTIMATOR_NAME)
                        ][metric]
                    )
                    for seed in seeds
                ]
                comparison_family[metric] = paired_comparison(
                    robust,
                    legacy,
                    direction="lower",
                    denominator={
                        "paired_seed_units": len(seeds),
                        "stage": stage,
                        "scenario": scenario,
                    },
                )
            adjusted = apply_holm(comparison_family)
            for metric, comparison in adjusted.items():
                effects.append(
                    {
                        "stage": stage,
                        "scenario": scenario,
                        "metric": metric,
                        "candidate_estimator": REVISED_ESTIMATOR_NAME,
                        "comparator_estimator": LEGACY_ESTIMATOR_NAME,
                        "holm_family": (
                            f"priority_robustness:{stage}:{scenario}"
                        ),
                        **comparison,
                    }
                )
    return effects


def build_result(
    stages: Sequence[str] = PRE_GATE2_STAGES,
    *,
    dataset_root: Path | str | None = None,
    gate1_lock: Path | str = DEFAULT_GATE1_LOCK,
) -> dict[str, object]:
    protocol, selected = restricted_protocol_and_seeds(stages)
    frozen_root, frozen_record = resolve_frozen_dataset_root(
        dataset_root,
        gate1_lock=gate1_lock,
    )
    rows = [
        row
        for stage, seed in selected
        for row in _run_seed_from_frozen_root(
            frozen_root,
            seed,
            stage,
            protocol,
            gate1_lock,
        )
    ]
    seed_rows = _seed_aggregates(rows)
    robust_exact = [
        row
        for row in rows
        if row["estimator"] == REVISED_ESTIMATOR_NAME
        and str(row["scenario"]).startswith("exact_duplicate_")
    ]
    robust_near = [
        row
        for row in rows
        if row["estimator"] == REVISED_ESTIMATOR_NAME
        and row["scenario"] == "near_duplicate"
    ]
    paired = _paired_estimator_effects(seed_rows)
    retained_counts = {
        "revised_favorable": sum(
            int(effect["n_candidate_better"])
            for effect in paired
        ),
        "tied": sum(
            int(effect["n_ties"])
            for effect in paired
        ),
        "revised_adverse": sum(
            int(effect["n_comparator_better"])
            for effect in paired
        ),
    }
    return {
        "schema_version": "exp16-priority-robustness-v1",
        "scientific_scope": (
            "pre-Gate-2 synthetic development/calibration robustness; "
            "no real-world misinformation validation"
        ),
        "protocol": {
            **protocol_record(protocol, selected),
            "frozen_dataset": frozen_record,
        },
        "estimators": list(ESTIMATORS),
        "scenario_registry": {
            "exact_duplicate_multiplicities": list(EXACT_MULTIPLICITIES),
            "near_duplicate": True,
            "low_confidence_single_field_attacks": ["N", "V", "F", "E"],
            "coordinated_high_confidence_campaign": True,
            "source_missingness_zero_imputation": True,
        },
        "policy_contract_checks": {
            "exact_duplicate_revised_max_normalized_drift": round(
                max(
                    float(row["priority_drift_abs_normalized"])
                    for row in robust_exact
                ),
                8,
            ),
            "exact_duplicate_invariance_pass": all(
                float(row["priority_drift_abs_normalized"]) == 0.0
                for row in robust_exact
            ),
            "near_duplicate_revised_max_normalized_drift": round(
                max(
                    float(row["priority_drift_abs_normalized"])
                    for row in robust_near
                ),
                8,
            ),
            "near_duplicate_declared_single_addition_ceiling": (
                NearDuplicatePolicy().max_priority_drift_fraction
            ),
            "near_duplicate_rows_within_ceiling": sum(
                float(row["priority_drift_abs_normalized"])
                <= NearDuplicatePolicy().max_priority_drift_fraction
                for row in robust_near
            ),
            "near_duplicate_row_denominator": len(robust_near),
        },
        "retention_policy": {
            "method_selection_performed": False,
            "unfavorable_and_tied_results_retained": True,
            "paired_direction_counts_across_reported_endpoints": retained_counts,
            "known_high_confidence_campaign_failure_not_reframed": True,
        },
        "per_scenario_rows": rows,
        "per_seed_aggregates": seed_rows,
        "summary": _summaries(seed_rows),
        "paired_estimator_effects": paired,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        action="append",
        choices=PRE_GATE2_STAGES,
        dest="stages",
        help="restricted protocol stage; repeat to run both",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="exclusive JSON output (defaults below DEMO_TABLES_DIR)",
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        help="accepted Gate-1 work/datasets root",
    )
    parser.add_argument(
        "--gate1-lock",
        type=Path,
        default=DEFAULT_GATE1_LOCK,
        help="Gate-1 lock binding the immutable dataset bundle",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    stages = tuple(args.stages or PRE_GATE2_STAGES)
    result = build_result(
        stages,
        dataset_root=args.dataset_root,
        gate1_lock=args.gate1_lock,
    )
    output = args.output or default_table_path(
        "exp16_priority_robustness.json"
    )
    write_exclusive_json(output, result)
    print(
        f"exp16 wrote {len(result['per_scenario_rows'])} scenario rows to {output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
