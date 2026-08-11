"""Predicted-cluster dispatch with an explicit post-scheduling truth join.

Job construction and scheduling accept only observable reports, predicted
labels, and fixed policy scores.  Incident truth is accepted exclusively by
``evaluate_schedule``.  Consequently, permuting evaluator-only identifiers or
outcomes cannot change a schedule hash.
"""
from __future__ import annotations

import hashlib
import heapq
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Mapping, Sequence

from demo.v2.contracts import IncidentTruthV2, ReportV2, TruthV2
from demo.v2.similarity import haversine_m


POLICY_IDS = (
    "revised",
    "legacy",
    "urgency_only",
    "population_only",
    "simple_linear",
    "random",
    "nearest_first",
)


@dataclass(frozen=True, slots=True)
class ObservableJobV2:
    job_id: str
    report_ids: tuple[str, ...]
    L: tuple[float, float]
    ready_min: float
    workload_proxy: float
    scores: Mapping[str, float]

    def __post_init__(self) -> None:
        if not self.job_id or not self.report_ids or len(set(self.report_ids)) != len(self.report_ids):
            raise ValueError("job requires a unique id and non-empty unique report ids")
        if not all(math.isfinite(float(value)) for value in (*self.L, self.ready_min, self.workload_proxy)):
            raise ValueError("job geometry/time/workload must be finite")
        if self.workload_proxy < 0.0:
            raise ValueError("workload_proxy cannot be negative")
        if set(self.scores) != set(POLICY_IDS).difference({"nearest_first"}):
            raise ValueError("job must provide every non-routing policy score")
        if not all(math.isfinite(float(value)) for value in self.scores.values()):
            raise ValueError("job scores must be finite")


@dataclass(frozen=True, slots=True)
class JobBuildResultV2:
    jobs: tuple[ObservableJobV2, ...]
    review_report_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ResourceScenarioV2:
    scenario_id: str
    depots: tuple[tuple[float, float], ...]
    n_boats: int
    speed_kmh: float
    service_rate_people_per_min: float
    access_delay_scale_min: float = 0.0

    def __post_init__(self) -> None:
        if not self.scenario_id or not self.depots:
            raise ValueError("resource scenario requires an id and depot")
        if isinstance(self.n_boats, bool) or not isinstance(self.n_boats, int) or self.n_boats < 1:
            raise ValueError("n_boats must be a positive integer")
        for name in ("speed_kmh", "service_rate_people_per_min"):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        if not math.isfinite(self.access_delay_scale_min) or self.access_delay_scale_min < 0.0:
            raise ValueError("access_delay_scale_min must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class AssignmentV2:
    job_id: str
    boat_id: int
    decision_min: float
    arrival_min: float
    service_end_min: float
    travel_min: float
    access_delay_min: float


@dataclass(frozen=True, slots=True)
class ScheduleV2:
    policy_id: str
    scenario_id: str
    jobs: tuple[ObservableJobV2, ...]
    assignments: tuple[AssignmentV2, ...]
    boat_workload_min: tuple[float, ...]


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def build_jobs(
    reports: Sequence[ReportV2],
    predicted_labels: Sequence[int],
    cluster_scores: Mapping[int, Mapping[str, float]],
    *,
    base_time: datetime,
    snapshot_min: float,
    noise_label: int = -1,
) -> JobBuildResultV2:
    """Create one observable job per predicted cluster and queue unresolved rows."""

    if len(reports) != len(predicted_labels):
        raise ValueError("reports and predicted labels must align exactly")
    _as_utc(base_time)  # validate/normalise the declared epoch for callers
    if not math.isfinite(float(snapshot_min)) or float(snapshot_min) < 0.0:
        raise ValueError("snapshot_min must be finite and non-negative")
    groups: dict[int, list[ReportV2]] = {}
    review: list[str] = []
    for report, label in zip(reports, predicted_labels, strict=True):
        if not report.graph_eligible or label == noise_label:
            review.append(report.report_id)
            continue
        groups.setdefault(int(label), []).append(report)
    # This experiment uses one explicitly declared batch snapshot.  Reports
    # have already been filtered by observable receipt time, so every job is
    # released at the same cutoff without looking ahead to later stream rows.
    snapshot_ready_min = float(snapshot_min)
    jobs: list[ObservableJobV2] = []
    required_scores = set(POLICY_IDS).difference({"nearest_first"})
    for label in sorted(groups):
        members = groups[label]
        if label not in cluster_scores or set(cluster_scores[label]) != required_scores:
            raise ValueError(f"missing policy scores for cluster {label}")
        assert all(member.L is not None and member.T is not None for member in members)
        latitude = mean(member.L[0] for member in members if member.L is not None)
        longitude = mean(member.L[1] for member in members if member.L is not None)
        ready_min = snapshot_ready_min
        # A bounded observable workload estimator; report multiplicity is not
        # summed because overlapping people cannot be identified.
        workload = max(
            (
                min(500.0, float(member.N))
                * (member.provenance_quality if member.provenance_quality is not None else 0.5)
                for member in members
                if member.N is not None
            ),
            default=1.0,
        )
        member_ids = tuple(sorted(member.report_id for member in members))
        membership_digest = hashlib.sha256("|".join(member_ids).encode("utf-8")).hexdigest()[:20]
        jobs.append(
            ObservableJobV2(
                job_id=f"cluster-{membership_digest}",
                report_ids=member_ids,
                L=(latitude, longitude),
                ready_min=ready_min,
                workload_proxy=workload,
                scores={key: float(cluster_scores[label][key]) for key in sorted(required_scores)},
            )
        )
    return JobBuildResultV2(
        tuple(sorted(jobs, key=lambda job: job.job_id)),
        tuple(sorted(review)),
    )


def _travel_minutes(origin: tuple[float, float], destination: tuple[float, float], speed_kmh: float) -> float:
    return haversine_m(origin, destination) / 1000.0 / speed_kmh * 60.0


def _stable_access_delay(job_id: str, scenario: ResourceScenarioV2) -> float:
    if scenario.access_delay_scale_min == 0.0:
        return 0.0
    digest = hashlib.sha256(f"{scenario.scenario_id}:{job_id}".encode("utf-8")).digest()
    unit = int.from_bytes(digest[:8], "big") / float(2**64 - 1)
    return scenario.access_delay_scale_min * unit


def _policy_key(
    policy_id: str,
    job: ObservableJobV2,
    *,
    decision_min: float,
    travel_min: float,
) -> tuple[float, float, float, str]:
    primary = -travel_min if policy_id == "nearest_first" else float(job.scores[policy_id])
    return primary, -travel_min, -max(0.0, decision_min - job.ready_min), job.job_id


def schedule_jobs(
    jobs: Sequence[ObservableJobV2],
    scenario: ResourceScenarioV2,
    policy_id: str,
) -> ScheduleV2:
    """Schedule jobs without accepting incident identifiers or outcome truth."""

    if policy_id not in POLICY_IDS:
        raise ValueError(f"unknown policy: {policy_id}")
    if not jobs:
        return ScheduleV2(policy_id, scenario.scenario_id, (), (), tuple(0.0 for _ in range(scenario.n_boats)))
    if len({job.job_id for job in jobs}) != len(jobs):
        raise ValueError("job ids must be unique")
    boats: list[tuple[float, int, tuple[float, float]]] = []
    for boat_id in range(scenario.n_boats):
        boats.append((0.0, boat_id, scenario.depots[boat_id % len(scenario.depots)]))
    heapq.heapify(boats)
    remaining = {job.job_id: job for job in jobs}
    assignments: list[AssignmentV2] = []
    workload = [0.0 for _ in range(scenario.n_boats)]
    while remaining:
        free_min, boat_id, origin = heapq.heappop(boats)
        eligible = [job for job in remaining.values() if job.ready_min <= free_min]
        decision_min = free_min
        if not eligible:
            decision_min = min(job.ready_min for job in remaining.values())
            eligible = [job for job in remaining.values() if job.ready_min <= decision_min]
        choices: list[tuple[tuple[float, float, float, str], ObservableJobV2, float]] = []
        for job in eligible:
            travel = _travel_minutes(origin, job.L, scenario.speed_kmh)
            choices.append((_policy_key(policy_id, job, decision_min=decision_min, travel_min=travel), job, travel))
        _, selected, travel_min = max(choices, key=lambda row: row[0])
        access_delay = _stable_access_delay(selected.job_id, scenario)
        arrival = decision_min + travel_min + access_delay
        service = max(1.0, selected.workload_proxy / scenario.service_rate_people_per_min)
        service_end = arrival + service
        assignments.append(
            AssignmentV2(
                selected.job_id,
                boat_id,
                decision_min,
                arrival,
                service_end,
                travel_min,
                access_delay,
            )
        )
        workload[boat_id] += travel_min + access_delay + service
        del remaining[selected.job_id]
        heapq.heappush(boats, (service_end, boat_id, selected.L))
    return ScheduleV2(policy_id, scenario.scenario_id, tuple(jobs), tuple(assignments), tuple(workload))


def schedule_hash(schedule: ScheduleV2) -> str:
    payload = {
        "policy_id": schedule.policy_id,
        "scenario_id": schedule.scenario_id,
        "jobs": [asdict(job) for job in schedule.jobs],
        "assignments": [asdict(row) for row in schedule.assignments],
        "boat_workload_min": schedule.boat_workload_min,
    }
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _coefficient_of_variation(values: Sequence[float]) -> float:
    if not values or mean(values) <= 0.0:
        return 0.0
    average = mean(values)
    return math.sqrt(mean((value - average) ** 2 for value in values)) / average


def _cvar(values: Sequence[float], tail_fraction: float = 0.10) -> float:
    if not values:
        return 0.0
    count = max(1, math.ceil(len(values) * tail_fraction))
    return mean(sorted(values, reverse=True)[:count])


def evaluate_schedule(
    schedule: ScheduleV2,
    report_truth: Sequence[TruthV2],
    incident_truth: Sequence[IncidentTruthV2],
    *,
    service_radius_m: float = 1000.0,
) -> dict[str, Any]:
    """Join truth after scheduling and propagate false/split/merge outcomes."""

    if not math.isfinite(service_radius_m) or service_radius_m <= 0.0:
        raise ValueError("service_radius_m must be finite and positive")
    links = {row.report_id: row for row in report_truth}
    if len(links) != len(report_truth):
        raise ValueError("report truth ids must be unique")
    incidents = {row.incident_id: row for row in incident_truth}
    if len(incidents) != len(incident_truth):
        raise ValueError("incident truth ids must be unique")
    jobs = {job.job_id: job for job in schedule.jobs}
    if len(jobs) != len(schedule.jobs):
        raise ValueError("scheduled job ids must be unique")
    assigned_job_ids = [row.job_id for row in schedule.assignments]
    if len(assigned_job_ids) != len(set(assigned_job_ids)) or set(assigned_job_ids) != set(jobs):
        raise ValueError("assignments must cover every scheduled job exactly once")
    scheduled_report_ids = {
        report_id for job in schedule.jobs for report_id in job.report_ids
    }
    missing_links = sorted(scheduled_report_ids.difference(links))
    if missing_links:
        raise ValueError(f"scheduled reports lack evaluator linkage: {missing_links[:5]}")
    orphan_incident_ids = sorted(
        {
            links[report_id].incident_id
            for report_id in scheduled_report_ids
            if links[report_id].incident_id is not None
        }.difference(incidents)
    )
    if orphan_incident_ids:
        raise ValueError(
            f"scheduled report links reference unknown incidents: {orphan_incident_ids[:5]}"
        )
    reached_at: dict[str, float] = {}
    false_trips = 0
    duplicate_trips = 0
    merged_candidate_losses = 0
    trip_rows: list[dict[str, Any]] = []
    for assignment in sorted(schedule.assignments, key=lambda row: (row.arrival_min, row.job_id)):
        job = jobs[assignment.job_id]
        linked = {
            links[report_id].incident_id
            for report_id in job.report_ids
            if report_id in links and links[report_id].incident_id is not None
        }
        qualifying = [
            incidents[incident_id]
            for incident_id in linked
            if incident_id in incidents
            and haversine_m(job.L, incidents[incident_id].L) <= service_radius_m
        ]
        qualifying.sort(key=lambda row: (haversine_m(job.L, row.L), row.incident_id))
        unreached = [row for row in qualifying if row.incident_id not in reached_at]
        if unreached:
            selected = unreached[0]
            reached_at[selected.incident_id] = assignment.arrival_min
            merged_candidate_losses += max(0, len(unreached) - 1)
            outcome = "first_reach"
            incident_id: str | None = selected.incident_id
        elif qualifying:
            selected = qualifying[0]
            duplicate_trips += 1
            outcome = "duplicate_trip"
            incident_id = selected.incident_id
        else:
            false_trips += 1
            outcome = "false_trip"
            incident_id = None
        trip_rows.append({"job_id": job.job_id, "incident_id": incident_id, "outcome": outcome})

    response_values: list[float] = []
    harm_values: list[float] = []
    deadline_misses = 0
    unreached_ids: list[str] = []
    for incident in incident_truth:
        if incident.incident_id not in reached_at:
            unreached_ids.append(incident.incident_id)
            deadline_misses += 1
            harm_values.append(incident.max_harm)
            response_values.append(
                incident.deadline_min
                + incident.harm_grace_min
                + incident.max_harm / max(incident.harm_slope, 1e-12)
            )
            continue
        response = max(0.0, reached_at[incident.incident_id] - incident.start_min)
        response_values.append(response)
        deadline_misses += int(response > incident.deadline_min)
        lateness = max(0.0, response - incident.deadline_min - incident.harm_grace_min)
        harm_values.append(min(incident.max_harm, incident.harm_slope * lateness))
    n_incidents = len(incident_truth)
    return {
        "policy": schedule.policy_id,
        "scenario": schedule.scenario_id,
        "total_harm": float(sum(harm_values)),
        "missed_deadlines": deadline_misses,
        "deadline_miss_rate": deadline_misses / n_incidents if n_incidents else 0.0,
        "unreached_incidents": len(unreached_ids),
        "false_trips": false_trips,
        "duplicate_trips": duplicate_trips,
        "merged_candidate_losses": merged_candidate_losses,
        "max_response_min": max(response_values, default=0.0),
        "cvar90_response_min": _cvar(response_values),
        "workload_cv": _coefficient_of_variation(schedule.boat_workload_min),
        "n_jobs": len(schedule.jobs),
        "n_incidents": n_incidents,
        "service_radius_m": service_radius_m,
        "unreached_incident_ids": sorted(unreached_ids),
        "trip_outcomes": trip_rows,
    }


__all__ = [
    "AssignmentV2",
    "JobBuildResultV2",
    "ObservableJobV2",
    "POLICY_IDS",
    "ResourceScenarioV2",
    "ScheduleV2",
    "build_jobs",
    "evaluate_schedule",
    "schedule_hash",
    "schedule_jobs",
]
