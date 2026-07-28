"""Deterministic multi-boat dispatch with outcome-independent endpoints.

Operational policies may consume priority estimates, report availability,
travel distance, and a reported-demand workload proxy.  Outcome evaluation
uses only latent incident start/deadline/service/harm parameters and simulated
arrival times.  In particular, no reported flood or vulnerability field is
accepted by this module.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from statistics import mean
from typing import Iterable, Sequence

from demo.pipeline.attributes import haversine_m


@dataclass(frozen=True)
class DispatchIncident:
    incident_id: str
    lat: float
    lng: float
    province: str
    start_min: float
    ready_min: float
    deadline_min: float
    service_demand_min: float
    harm_grace_min: float
    harm_slope: float
    capacity_penalty: float
    n_true: int
    robust_priority: float
    legacy_priority: float
    workload_proxy: float


@dataclass(frozen=True)
class ResourceScenario:
    scenario_id: str
    depot_coordinates: tuple[tuple[float, float], ...]
    n_boats: int
    speed_kmh: float
    service_rate: float
    nominal_service_capacity_min: float

    def validate(self) -> None:
        if not self.scenario_id:
            raise ValueError("resource scenario requires an id")
        if not self.depot_coordinates:
            raise ValueError("resource scenario requires at least one depot")
        if self.n_boats <= 0:
            raise ValueError("resource scenario requires a positive boat count")
        if (
            not math.isfinite(self.speed_kmh)
            or self.speed_kmh <= 0
            or not math.isfinite(self.service_rate)
            or self.service_rate <= 0
            or not math.isfinite(self.nominal_service_capacity_min)
            or self.nominal_service_capacity_min < 0
        ):
            raise ValueError("resource scenario rates/capacity must be valid")


POLICY_IDS = (
    "revised_priority",
    "legacy_priority",
    "first_report_fifo",
    "nearest_first",
    "equity_aging",
    "workload_smoothing",
)


def default_resource_scenarios() -> tuple[ResourceScenario, ...]:
    """Locked illustrative resource assumptions used before Gate 2."""

    hue = (16.4637, 107.5909)
    da_nang = (16.0678, 108.2208)
    quang_tri = (16.7500, 107.1900)
    return (
        ResourceScenario(
            "lean_hue",
            (hue,),
            n_boats=2,
            speed_kmh=24.0,
            service_rate=0.85,
            nominal_service_capacity_min=28.0,
        ),
        ResourceScenario(
            "nominal_dual_depot",
            (hue, da_nang),
            n_boats=3,
            speed_kmh=30.0,
            service_rate=1.0,
            nominal_service_capacity_min=34.0,
        ),
        ResourceScenario(
            "regional_surge",
            (hue, da_nang, quang_tri),
            n_boats=5,
            speed_kmh=34.0,
            service_rate=1.25,
            nominal_service_capacity_min=42.0,
        ),
    )


def _travel_minutes(
    origin_lat: float,
    origin_lng: float,
    destination_lat: float,
    destination_lng: float,
    speed_kmh: float,
) -> float:
    return (
        haversine_m(
            origin_lat,
            origin_lng,
            destination_lat,
            destination_lng,
        )
        / 1000.0
        / speed_kmh
        * 60.0
    )


def _policy_value(
    policy_id: str,
    incident: DispatchIncident,
    *,
    decision_min: float,
    travel_min: float,
    max_workload_proxy: float,
    province_dispatch_counts: dict[str, int],
) -> tuple[float, float, float, str]:
    age = max(0.0, decision_min - incident.ready_min)
    age_score = min(1.0, age / 180.0)
    robust_score = min(1.0, max(0.0, incident.robust_priority / 2.0))
    legacy_score = min(1.0, max(0.0, incident.legacy_priority / 2.0))
    workload = (
        incident.workload_proxy / max_workload_proxy
        if max_workload_proxy > 0
        else 0.0
    )
    underserved = 1.0 / (
        1.0 + float(province_dispatch_counts.get(incident.province, 0))
    )

    if policy_id == "revised_priority":
        primary = robust_score
    elif policy_id == "legacy_priority":
        primary = legacy_score
    elif policy_id == "first_report_fifo":
        # FIFO remains strictly ordered even after waits exceed the normalized
        # 180-minute aging horizon used by the blended policies.
        primary = age
    elif policy_id == "nearest_first":
        primary = -travel_min / 180.0
    elif policy_id == "equity_aging":
        primary = 0.50 * robust_score + 0.30 * age_score + 0.20 * underserved
    elif policy_id == "workload_smoothing":
        primary = 0.65 * robust_score + 0.25 * age_score - 0.10 * workload
    else:
        raise ValueError(f"unknown dispatch policy: {policy_id}")
    # Stable secondary keys prefer lower travel and earlier reports.  The
    # incident id is the final deterministic tie breaker.
    return (primary, -travel_min, -incident.ready_min, incident.incident_id)


def _coefficient_of_variation(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    average = mean(values)
    if average <= 0:
        return 0.0
    return math.sqrt(mean((value - average) ** 2 for value in values)) / average


def _cvar(values: Sequence[float], tail_fraction: float = 0.10) -> float:
    if not values:
        return 0.0
    ordered = sorted(values, reverse=True)
    count = max(1, math.ceil(len(ordered) * tail_fraction))
    return mean(ordered[:count])


def simulate_dispatch(
    incidents: Iterable[DispatchIncident],
    scenario: ResourceScenario,
    policy_id: str,
) -> dict[str, object]:
    """Run one deterministic greedy dispatch policy and evaluate latent outcome."""

    jobs = tuple(incidents)
    if not jobs:
        raise ValueError("dispatch requires at least one incident")
    if len({job.incident_id for job in jobs}) != len(jobs):
        raise ValueError("incident ids must be unique")
    scenario.validate()
    if policy_id not in POLICY_IDS:
        raise ValueError(f"unknown dispatch policy: {policy_id}")
    max_workload_proxy = max(job.workload_proxy for job in jobs)

    boats: list[tuple[float, int, float, float]] = []
    for boat_id in range(scenario.n_boats):
        depot = scenario.depot_coordinates[
            boat_id % len(scenario.depot_coordinates)
        ]
        boats.append((0.0, boat_id, depot[0], depot[1]))
    heapq.heapify(boats)

    remaining = {job.incident_id: job for job in jobs}
    province_dispatch_counts: dict[str, int] = {}
    boat_workload = {boat_id: 0.0 for boat_id in range(scenario.n_boats)}
    assignments: list[dict[str, object]] = []
    while remaining:
        free_min, boat_id, boat_lat, boat_lng = heapq.heappop(boats)
        eligible = [
            job for job in remaining.values() if job.ready_min <= free_min
        ]
        decision_min = free_min
        if not eligible:
            decision_min = min(job.ready_min for job in remaining.values())
            eligible = [
                job
                for job in remaining.values()
                if job.ready_min <= decision_min
            ]

        choices: list[
            tuple[tuple[float, float, float, str], DispatchIncident, float]
        ] = []
        for job in eligible:
            travel_min = _travel_minutes(
                boat_lat,
                boat_lng,
                job.lat,
                job.lng,
                scenario.speed_kmh,
            )
            choices.append(
                (
                    _policy_value(
                        policy_id,
                        job,
                        decision_min=decision_min,
                        travel_min=travel_min,
                        max_workload_proxy=max_workload_proxy,
                        province_dispatch_counts=province_dispatch_counts,
                    ),
                    job,
                    travel_min,
                )
            )
        _, selected, travel_min = max(
            choices,
            key=lambda choice: choice[0],
        )

        arrival_min = decision_min + travel_min
        response_min = max(0.0, arrival_min - selected.start_min)
        service_min = selected.service_demand_min / scenario.service_rate
        overload_min = max(
            0.0,
            service_min - scenario.nominal_service_capacity_min,
        )
        lateness_after_grace = max(
            0.0,
            response_min - selected.deadline_min - selected.harm_grace_min,
        )
        latent_harm = (
            selected.harm_slope * lateness_after_grace
            + selected.capacity_penalty * overload_min
        )
        workload_min = travel_min + service_min
        assignments.append(
            {
                "incident_id": selected.incident_id,
                "province": selected.province,
                "boat_id": boat_id,
                "decision_min": round(decision_min, 8),
                "travel_min": round(travel_min, 8),
                "arrival_min": round(arrival_min, 8),
                "response_min": round(response_min, 8),
                "deadline_min": round(selected.deadline_min, 8),
                "deadline_missed": bool(response_min > selected.deadline_min),
                "service_min": round(service_min, 8),
                "latent_harm": round(latent_harm, 8),
                "n_true": selected.n_true,
            }
        )
        boat_workload[boat_id] += workload_min
        province_dispatch_counts[selected.province] = (
            province_dispatch_counts.get(selected.province, 0) + 1
        )
        del remaining[selected.incident_id]
        heapq.heappush(
            boats,
            (
                arrival_min + service_min,
                boat_id,
                selected.lat,
                selected.lng,
            ),
        )

    response_values = [float(row["response_min"]) for row in assignments]
    harm_values = [float(row["latent_harm"]) for row in assignments]
    province_means: dict[str, float] = {}
    for province in sorted({str(row["province"]) for row in assignments}):
        province_means[province] = mean(
            float(row["response_min"])
            for row in assignments
            if row["province"] == province
        )
    timely_population = sum(
        int(row["n_true"])
        for row in assignments
        if not bool(row["deadline_missed"])
    )
    total_population = sum(int(row["n_true"]) for row in assignments)
    workload_values = [
        float(boat_workload[boat_id]) for boat_id in sorted(boat_workload)
    ]
    metrics = {
        "n_incidents": len(assignments),
        "latent_harm": round(mean(harm_values), 8),
        "deadline_miss_rate": round(
            sum(bool(row["deadline_missed"]) for row in assignments)
            / len(assignments),
            8,
        ),
        "mean_arrival_min": round(mean(response_values), 8),
        "max_arrival_min": round(max(response_values), 8),
        "cvar90_arrival_min": round(_cvar(response_values), 8),
        "arrival_equity_gap_min": round(
            max(province_means.values()) - min(province_means.values()),
            8,
        ),
        "total_fleet_workload_min": round(sum(workload_values), 8),
        "boat_workload_cv": round(
            _coefficient_of_variation(workload_values),
            8,
        ),
        "unique_population_reached_by_deadline_rate": round(
            timely_population / total_population if total_population else 0.0,
            8,
        ),
    }
    return {
        "policy": policy_id,
        "resource_scenario": scenario.scenario_id,
        "metrics": metrics,
        "province_mean_arrival_min": {
            province: round(value, 8)
            for province, value in province_means.items()
        },
        "boat_workload_min": {
            str(boat_id): round(boat_workload[boat_id], 8)
            for boat_id in sorted(boat_workload)
        },
        "assignments": assignments,
    }


__all__ = [
    "DispatchIncident",
    "POLICY_IDS",
    "ResourceScenario",
    "default_resource_scenarios",
    "simulate_dispatch",
]
