from __future__ import annotations

from datetime import datetime, timezone

from demo.v2.contracts import IncidentTruthV2, ReportV2, TruthV2
from demo.v2.dispatch import (
    POLICY_IDS,
    ResourceScenarioV2,
    build_jobs,
    evaluate_schedule,
    schedule_hash,
    schedule_jobs,
)


def _scores(value: float) -> dict[str, float]:
    return {policy: value for policy in POLICY_IDS if policy != "nearest_first"}


def test_truth_permutation_cannot_change_schedule_hash() -> None:
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    reports = [
        ReportV2("r1", L=(16.0, 108.0), T=base, N=10, source_id="s1"),
        ReportV2("r2", L=(16.1, 108.1), T=base, N=5, source_id="s2"),
    ]
    jobs = build_jobs(reports, [0, 1], {0: _scores(0.9), 1: _scores(0.1)}, base_time=base, snapshot_min=30.0).jobs
    scenario = ResourceScenarioV2("s", ((16.0, 108.0),), 1, 30.0, 1.0)
    schedule = schedule_jobs(jobs, scenario, "revised")
    before = schedule_hash(schedule)
    truth_a = [TruthV2("r1", "a", 0), TruthV2("r2", "b", 1)]
    truth_b = [TruthV2("r1", "b", 1), TruthV2("r2", "a", 0)]
    incident_truth = [
        IncidentTruthV2("a", (16.0, 108.0), 0, 60, 1, 10, 0, 1, 100, 5, 1, 1),
        IncidentTruthV2("b", (16.1, 108.1), 0, 60, 1, 10, 0, 1, 100, 5, 1, 1),
    ]
    evaluate_schedule(schedule, truth_a, incident_truth)
    evaluate_schedule(schedule, truth_b, incident_truth)
    assert schedule_hash(schedule) == before


def test_noise_only_cluster_costs_a_false_trip() -> None:
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    reports = [ReportV2("noise", L=(16.0, 108.0), T=base, N=1)]
    jobs = build_jobs(reports, [0], {0: _scores(0.5)}, base_time=base, snapshot_min=30.0).jobs
    scenario = ResourceScenarioV2("s", ((16.0, 108.0),), 1, 30.0, 1.0)
    result = evaluate_schedule(
        schedule_jobs(jobs, scenario, "revised"),
        [TruthV2("noise", is_noise=True, is_fake=True)],
        [],
    )
    assert result["false_trips"] == 1
    assert result["n_jobs"] == 1


def test_split_cluster_creates_duplicate_trip_and_missing_lt_is_reviewed() -> None:
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    reports = [
        ReportV2("r1", L=(16.0, 108.0), T=base, N=4),
        ReportV2("r2", L=(16.0, 108.0), T=base, N=4),
        ReportV2("missing", L=None, T=base, N=4),
    ]
    built = build_jobs(
        reports,
        [0, 1, -1],
        {0: _scores(0.9), 1: _scores(0.8)},
        base_time=base,
        snapshot_min=30.0,
    )
    assert built.review_report_ids == ("missing",)
    scenario = ResourceScenarioV2("s", ((16.0, 108.0),), 1, 30.0, 2.0)
    truth = [TruthV2("r1", "a", 0), TruthV2("r2", "a", 0), TruthV2("missing", "a", 0)]
    incidents = [IncidentTruthV2("a", (16.0, 108.0), 0, 60, 1, 10, 0, 1, 100, 5, 1, 1)]
    result = evaluate_schedule(schedule_jobs(built.jobs, scenario, "revised"), truth, incidents)
    assert result["duplicate_trips"] == 1


def test_batch_job_uses_declared_snapshot_and_membership_id_is_order_invariant() -> None:
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    early = ReportV2("early", L=(16.0, 108.0), T=base, N=2)
    late = ReportV2("late", L=(16.0, 108.0), T=base.replace(hour=2), N=2)
    forward = build_jobs(
        [early, late], [7, 7], {7: _scores(0.5)}, base_time=base, snapshot_min=90.0
    ).jobs[0]
    reverse = build_jobs(
        [late, early], [2, 2], {2: _scores(0.5)}, base_time=base, snapshot_min=90.0
    ).jobs[0]
    assert forward.ready_min == 90.0
    assert forward.job_id == reverse.job_id
    assert forward.report_ids == reverse.report_ids


def test_all_batch_jobs_wait_for_declared_snapshot_cutoff() -> None:
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    early = ReportV2("early", L=(16.0, 108.0), T=base, N=2)
    future = ReportV2("future", L=(17.0, 109.0), T=base.replace(hour=3), N=2)
    jobs = build_jobs(
        [early, future],
        [0, 1],
        {0: _scores(0.5), 1: _scores(0.4)},
        base_time=base,
        snapshot_min=75.0,
    ).jobs
    assert {job.ready_min for job in jobs} == {75.0}


def test_evaluator_fails_closed_on_missing_or_orphan_truth_join() -> None:
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    report = ReportV2("r", L=(16.0, 108.0), T=base, N=1)
    jobs = build_jobs([report], [0], {0: _scores(0.5)}, base_time=base, snapshot_min=30.0).jobs
    scenario = ResourceScenarioV2("s", ((16.0, 108.0),), 1, 30.0, 1.0)
    schedule = schedule_jobs(jobs, scenario, "revised")
    import pytest

    with pytest.raises(ValueError, match="lack evaluator linkage"):
        evaluate_schedule(schedule, [], [])
    with pytest.raises(ValueError, match="unknown incidents"):
        evaluate_schedule(schedule, [TruthV2("r", "missing", 0)], [])
