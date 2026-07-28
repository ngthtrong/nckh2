"""Experiment 17: independent dispatch outcomes and Pareto trade-offs.

Dispatch policies are evaluated on latent deadlines, service demands, and harm
curves that are not algebraic transforms of priority, flood, or vulnerability.
Only development/calibration seeds are available through this entry point.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Sequence

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from demo.experiments.inference import (  # noqa: E402
    apply_holm,
    descriptive_summary,
    paired_comparison,
)
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
from demo.pipeline.attributes import compute_confidence  # noqa: E402
from demo.pipeline.config import DEFAULT_CONFIG  # noqa: E402
from demo.pipeline.priority import (  # noqa: E402
    LEGACY_ESTIMATOR_NAME,
    REVISED_ESTIMATOR_NAME,
    score_clusters,
)
from demo.simulation.dispatch import (  # noqa: E402
    POLICY_IDS,
    DispatchIncident,
    default_resource_scenarios,
    simulate_dispatch,
)


ENDPOINT_DIRECTIONS = {
    "latent_harm": "lower",
    "deadline_miss_rate": "lower",
    "mean_arrival_min": "lower",
    "max_arrival_min": "lower",
    "cvar90_arrival_min": "lower",
    "arrival_equity_gap_min": "lower",
    "total_fleet_workload_min": "lower",
    "boat_workload_cv": "lower",
    "unique_population_reached_by_deadline_rate": "higher",
}
PRIMARY_ENDPOINTS = ("latent_harm", "deadline_miss_rate")
PARETO_ENDPOINTS = (
    "latent_harm",
    "deadline_miss_rate",
    "mean_arrival_min",
    "arrival_equity_gap_min",
    "total_fleet_workload_min",
)
TRADEOFF_ENDPOINTS = (
    "mean_arrival_min",
    "max_arrival_min",
    "cvar90_arrival_min",
    "arrival_equity_gap_min",
    "total_fleet_workload_min",
    "boat_workload_cv",
    "unique_population_reached_by_deadline_rate",
)
REFERENCE_POLICY = "revised_priority"


def _linked_scores(
    data: dict,
    inference_events: Sequence[object],
) -> tuple[dict[int, object], dict[int, object], dict[str, list[object]]]:
    events = list(inference_events)
    # Recompute from the sanitized frozen inference view so this experiment
    # never consumes serialized/evaluator confidence.
    compute_confidence(events, DEFAULT_CONFIG.confidence)
    events_by_id = {str(event.event_id): event for event in events}
    linked_events = []
    labels = []
    events_by_incident: dict[str, list[object]] = defaultdict(list)
    for report in data["reports"]:
        evaluation = report["evaluation_only"]
        if evaluation["incident_id"] is None:
            continue
        event = events_by_id[str(report["event_id"])]
        linked_events.append(event)
        labels.append(int(evaluation["gt_cluster"]))
        events_by_incident[str(evaluation["incident_id"])].append(event)
    robust = {
        int(score.cluster_id): score
        for score in score_clusters(
            linked_events,
            labels,
            DEFAULT_CONFIG.priority,
            estimator=REVISED_ESTIMATOR_NAME,
        )
    }
    legacy = {
        int(score.cluster_id): score
        for score in score_clusters(
            linked_events,
            labels,
            DEFAULT_CONFIG.priority,
            estimator=LEGACY_ESTIMATOR_NAME,
        )
    }
    return robust, legacy, events_by_incident


def _dispatch_incidents(
    data: dict,
    inference_events: Sequence[object],
) -> tuple[DispatchIncident, ...]:
    robust, legacy, events_by_incident = _linked_scores(
        data,
        inference_events,
    )
    starts = [
        datetime.fromisoformat(str(incident["start_at"]))
        for incident in data["incidents"]
    ]
    origin = min(starts)
    jobs: list[DispatchIncident] = []
    for incident in sorted(
        data["incidents"],
        key=lambda row: str(row["incident_id"]),
    ):
        incident_id = str(incident["incident_id"])
        gt = int(incident["gt_cluster"])
        linked = events_by_incident[incident_id]
        # Routing uses an observable, policy-independent report centroid.  The
        # latent center is not made available to the scheduling policy.
        route_lat = mean(float(event.lat) for event in linked)
        route_lng = mean(float(event.lng) for event in linked)
        start_at = datetime.fromisoformat(str(incident["start_at"]))
        ready_at = min(event.created_at for event in linked)
        harm_curve = incident["harm_curve"]
        jobs.append(
            DispatchIncident(
                incident_id=incident_id,
                lat=route_lat,
                lng=route_lng,
                province=str(incident["province"]),
                start_min=(start_at - origin).total_seconds() / 60.0,
                ready_min=(ready_at - origin).total_seconds() / 60.0,
                deadline_min=float(incident["deadline_min"]),
                service_demand_min=float(incident["service_demand_min"]),
                harm_grace_min=float(harm_curve["grace_min"]),
                harm_slope=float(harm_curve["slope"]),
                capacity_penalty=float(harm_curve["capacity_penalty"]),
                n_true=int(incident["n_true"]),
                robust_priority=float(robust[gt].priority),
                legacy_priority=float(legacy[gt].priority),
                workload_proxy=float(robust[gt].n_total_raw),
            )
        )
    return tuple(jobs)


def _dominates(first: dict[str, float], second: dict[str, float]) -> bool:
    no_worse = all(
        first[endpoint] <= second[endpoint] for endpoint in PARETO_ENDPOINTS
    )
    strictly_better = any(
        first[endpoint] < second[endpoint] for endpoint in PARETO_ENDPOINTS
    )
    return no_worse and strictly_better


def _mark_pareto(rows: list[dict[str, object]]) -> None:
    metrics_by_policy = {
        str(row["policy"]): {
            endpoint: float(row[endpoint]) for endpoint in PARETO_ENDPOINTS
        }
        for row in rows
    }
    for row in rows:
        policy = str(row["policy"])
        dominators = sorted(
            other
            for other in metrics_by_policy
            if other != policy
            and _dominates(metrics_by_policy[other], metrics_by_policy[policy])
        )
        row["pareto_nondominated"] = not dominators
        row["dominated_by_policies"] = dominators


def _run_seed_from_frozen_root(
    dataset_root: Path,
    seed: int,
    stage: str,
    protocol: TuningProtocol,
    gate1_lock: Path | str,
) -> list[dict[str, object]]:
    """Run every policy/resource combination from one frozen split file."""

    if stage not in PRE_GATE2_STAGES:
        raise ValueError("run_seed accepts only development/calibration")
    tuning_dataset, data = load_frozen_tuning_views(
        dataset_root,
        stage=stage,
        seed=int(seed),
        tuning_protocol=protocol,
        gate1_lock=gate1_lock,
    )
    jobs = _dispatch_incidents(data, tuning_dataset.events)
    rows: list[dict[str, object]] = []
    for scenario in default_resource_scenarios():
        scenario_rows: list[dict[str, object]] = []
        for policy in POLICY_IDS:
            simulation = simulate_dispatch(jobs, scenario, policy)
            metrics = simulation["metrics"]
            row: dict[str, object] = {
                "seed": int(seed),
                "stage": stage,
                "policy": policy,
                "resource_scenario": scenario.scenario_id,
                **metrics,  # type: ignore[arg-type]
                "province_mean_arrival_min": simulation[
                    "province_mean_arrival_min"
                ],
                "boat_workload_min": simulation["boat_workload_min"],
                "assignments": simulation["assignments"],
            }
            scenario_rows.append(row)
        _mark_pareto(scenario_rows)
        rows.extend(scenario_rows)
    for row in rows:
        row["dataset_source_sha256"] = tuning_dataset.source_sha256
    return rows


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


def _summary(
    rows: Sequence[dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[
        tuple[str, str, str],
        list[dict[str, object]],
    ] = defaultdict(list)
    for row in rows:
        grouped[
            (
                str(row["stage"]),
                str(row["resource_scenario"]),
                str(row["policy"]),
            )
        ].append(row)
    output: list[dict[str, object]] = []
    for (stage, resource, policy), selected in sorted(grouped.items()):
        summary: dict[str, object] = {
            "stage": stage,
            "resource_scenario": resource,
            "policy": policy,
            "n_seed_resource_runs": len(selected),
            "pareto_frontier_frequency": round(
                sum(bool(row["pareto_nondominated"]) for row in selected)
                / len(selected),
                8,
            ),
        }
        denominator = {
            "seed_resource_runs": len(selected),
            "incident_outcomes": sum(
                int(row["n_incidents"]) for row in selected
            ),
        }
        for endpoint in ENDPOINT_DIRECTIONS:
            summary[endpoint] = descriptive_summary(
                [float(row[endpoint]) for row in selected],
                denominator=denominator,
            )
        output.append(summary)
    return output


def _paired_policy_comparisons(
    rows: Sequence[dict[str, object]],
) -> list[dict[str, object]]:
    indexed = {
        (
            str(row["stage"]),
            str(row["resource_scenario"]),
            int(row["seed"]),
            str(row["policy"]),
        ): row
        for row in rows
    }
    stages = sorted({str(row["stage"]) for row in rows})
    resources = sorted({str(row["resource_scenario"]) for row in rows})
    comparisons: list[dict[str, object]] = []
    for stage in stages:
        for resource in resources:
            seeds = sorted(
                {
                    int(row["seed"])
                    for row in rows
                    if row["stage"] == stage
                    and row["resource_scenario"] == resource
                }
            )
            denominator = {
                "paired_seed_resource_runs": len(seeds),
                "incident_outcomes_per_policy": sum(
                    int(
                        indexed[
                            (stage, resource, seed, REFERENCE_POLICY)
                        ]["n_incidents"]
                    )
                    for seed in seeds
                ),
            }
            for comparator in POLICY_IDS:
                if comparator == REFERENCE_POLICY:
                    continue
                for family_name, endpoints in (
                    ("independent_outcome", PRIMARY_ENDPOINTS),
                    ("dispatch_tradeoff", TRADEOFF_ENDPOINTS),
                ):
                    family: dict[str, dict[str, object]] = {}
                    for endpoint in endpoints:
                        candidate_values = [
                            float(
                                indexed[
                                    (
                                        stage,
                                        resource,
                                        seed,
                                        REFERENCE_POLICY,
                                    )
                                ][endpoint]
                            )
                            for seed in seeds
                        ]
                        comparator_values = [
                            float(
                                indexed[
                                    (stage, resource, seed, comparator)
                                ][endpoint]
                            )
                            for seed in seeds
                        ]
                        family[endpoint] = paired_comparison(
                            candidate_values,
                            comparator_values,
                            direction=ENDPOINT_DIRECTIONS[endpoint],
                            denominator=denominator,
                        )
                    adjusted = apply_holm(family)
                    for endpoint, comparison in adjusted.items():
                        comparisons.append(
                            {
                                "stage": stage,
                                "resource_scenario": resource,
                                "candidate_policy": REFERENCE_POLICY,
                                "comparator_policy": comparator,
                                "endpoint": endpoint,
                                "holm_family": (
                                    f"{family_name}:{stage}:{resource}:"
                                    f"{REFERENCE_POLICY}:vs:{comparator}"
                                ),
                                **comparison,
                            }
                        )
    return comparisons


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
    comparisons = _paired_policy_comparisons(rows)
    retention_counts = {
        "reference_policy_favorable": sum(
            int(row["n_candidate_better"]) for row in comparisons
        ),
        "tied": sum(int(row["n_ties"]) for row in comparisons),
        "reference_policy_adverse": sum(
            int(row["n_comparator_better"]) for row in comparisons
        ),
    }
    return {
        "schema_version": "exp17-independent-dispatch-outcomes-v1",
        "scientific_scope": (
            "illustrative synthetic dispatch simulation; policy weights and "
            "resource assumptions are not expert-validated"
        ),
        "protocol": {
            **protocol_record(protocol, selected),
            "frozen_dataset": frozen_record,
        },
        "outcome_independence_contract": {
            "primary_endpoints": list(PRIMARY_ENDPOINTS),
            "latent_outcome_inputs": [
                "incident start",
                "deadline",
                "service demand",
                "harm grace",
                "harm slope",
                "capacity penalty",
                "simulated travel and arrival",
            ],
            "reported_priority_components_used_in_outcome": [],
            "reported_flood_used_in_outcome": False,
            "reported_vulnerability_used_in_outcome": False,
            "priority_is_used_only_for_policy_ordering": True,
        },
        "dispatch_assumptions": {
            "partition": (
                "oracle incident grouping isolates dispatch-policy behavior from "
                "clustering error"
            ),
            "incident_location": (
                "policy-independent centroid of linked observable report coordinates"
            ),
            "availability": "earliest linked report timestamp",
            "fleet": [
                {
                    "resource_scenario": scenario.scenario_id,
                    "depot_coordinates": [
                        list(coordinate)
                        for coordinate in scenario.depot_coordinates
                    ],
                    "n_boats": scenario.n_boats,
                    "speed_kmh": scenario.speed_kmh,
                    "service_rate": scenario.service_rate,
                    "nominal_service_capacity_min": (
                        scenario.nominal_service_capacity_min
                    ),
                }
                for scenario in default_resource_scenarios()
            ],
            "all_incidents_eventually_served": True,
            "tie_breaking": (
                "policy value, shorter travel, earlier report, stable incident id"
            ),
            "randomness_in_dispatch_simulator": False,
        },
        "policy_registry": {
            "revised_priority": "locked duplicate-aware priority descending",
            "legacy_priority": "locked legacy raw priority descending",
            "first_report_fifo": "longest observable wait first",
            "nearest_first": "shortest current boat travel first",
            "equity_aging": (
                "0.50 revised priority + 0.30 wait age + "
                "0.20 inverse province dispatch count"
            ),
            "workload_smoothing": (
                "0.65 revised priority + 0.25 wait age - "
                "0.10 normalized reported-demand workload proxy"
            ),
        },
        "endpoint_directions": ENDPOINT_DIRECTIONS,
        "pareto_endpoint_set": list(PARETO_ENDPOINTS),
        "retention_policy": {
            "policy_selection_performed": False,
            "all_policies_and_resource_scenarios_retained": True,
            "unfavorable_and_tied_results_retained": True,
            "paired_direction_counts": retention_counts,
        },
        "per_seed_resource_policy_rows": rows,
        "summary": _summary(rows),
        "paired_policy_comparisons": comparisons,
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
        "exp17_dispatch_outcomes.json"
    )
    write_exclusive_json(output, result)
    print(
        "exp17 wrote "
        f"{len(result['per_seed_resource_policy_rows'])} "
        f"policy-resource rows to {output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
