from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

import demo.v2.evaluation as evaluation_module
from demo.v2.contracts import IncidentTruthV2, ReportV2, TruthV2
from demo.v2.dispatch import (
    ResourceScenarioV2,
    build_jobs,
    schedule_hash,
    schedule_jobs,
)
from demo.v2.evaluation import (
    STRESS_FAMILIES_V2,
    PriorityEvaluationV2Error,
    attach_evaluator_truth_to_stress,
    build_observable_priority_stress,
    evaluate_predicted_priority,
    evaluate_priority_stress,
    score_predicted_priority,
)


BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _report(
    identifier: str,
    *,
    east_m: float,
    minute: float,
    flood: float,
    urgency: float,
    population: float,
    vulnerability: float,
    source_family: str,
) -> ReportV2:
    return ReportV2(
        report_id=identifier,
        L=(16.0, 108.0 + east_m / 106_000.0),
        T=BASE_TIME + timedelta(minutes=minute),
        F=flood,
        E=urgency,
        N=population,
        V=vulnerability,
        source_id=f"source-{identifier}",
        source_family=source_family,
        provenance_quality=0.72,
        has_image=identifier.endswith("1"),
    )


def _incident(identifier: str, benefit: float, east_m: float) -> IncidentTruthV2:
    return IncidentTruthV2(
        incident_id=identifier,
        L=(16.0, 108.0 + east_m / 106_000.0),
        start_min=0.0,
        deadline_min=60.0,
        latent_need=benefit,
        latent_benefit=benefit,
        service_demand_min=10.0,
        harm_grace_min=5.0,
        harm_slope=1.0,
        max_harm=100.0,
        n_true=20,
        v_true=4,
    )


def _fixture() -> tuple[
    list[ReportV2],
    list[int],
    list[TruthV2],
    list[IncidentTruthV2],
]:
    # Cluster 0 merges three A reports and one B report.  Cluster 1 is another
    # fragment of A, so the global one-to-one optimum must match cluster 0 to A
    # and leave cluster 1 unmatched.  Cluster 2 is noise-only; cluster 3 is C.
    reports = [
        _report(
            "a1",
            east_m=0,
            minute=1,
            flood=0.9,
            urgency=0.9,
            population=40,
            vulnerability=8,
            source_family="hotline",
        ),
        _report(
            "a2",
            east_m=20,
            minute=2,
            flood=0.88,
            urgency=0.86,
            population=38,
            vulnerability=7,
            source_family="field_team",
        ),
        _report(
            "a3",
            east_m=30,
            minute=3,
            flood=0.87,
            urgency=0.84,
            population=36,
            vulnerability=7,
            source_family="citizen_app",
        ),
        _report(
            "b1",
            east_m=45,
            minute=4,
            flood=0.5,
            urgency=0.55,
            population=14,
            vulnerability=2,
            source_family="social_media",
        ),
        _report(
            "a4",
            east_m=90,
            minute=5,
            flood=0.82,
            urgency=0.8,
            population=32,
            vulnerability=6,
            source_family="hotline",
        ),
        _report(
            "noise",
            east_m=180,
            minute=6,
            flood=0.99,
            urgency=0.99,
            population=100,
            vulnerability=20,
            source_family="anonymous",
        ),
        _report(
            "c1",
            east_m=300,
            minute=7,
            flood=0.4,
            urgency=0.45,
            population=8,
            vulnerability=1,
            source_family="field_team",
        ),
        ReportV2(
            "review",
            L=None,
            T=BASE_TIME,
            F=0.7,
            E=0.7,
            N=9,
            V=2,
            source_id="review-source",
            source_family="hotline",
            provenance_quality=0.8,
        ),
    ]
    labels = [0, 0, 0, 0, 1, 2, 3, -1]
    truth = [
        TruthV2("a1", "A", 0),
        TruthV2("a2", "A", 0),
        TruthV2("a3", "A", 0),
        TruthV2("b1", "B", 1),
        TruthV2("a4", "A", 0),
        TruthV2("noise", is_noise=True, is_fake=True),
        TruthV2("c1", "C", 2),
        TruthV2("review", "A", 0),
    ]
    incidents = [
        _incident("A", 10.0, 0),
        _incident("B", 5.0, 45),
        _incident("C", 2.0, 300),
    ]
    return reports, labels, truth, incidents


def _unit_with_report(result: object, report_id: str):
    return next(
        row
        for row in result.evaluated_units  # type: ignore[attr-defined]
        if report_id in row.report_ids
    )


def test_scoring_phase_cannot_call_evaluator_truth_join(monkeypatch: pytest.MonkeyPatch) -> None:
    reports, labels, _, _ = _fixture()

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("truth join entered during scoring")

    monkeypatch.setattr(evaluation_module, "_validated_truth", forbidden)
    scored = score_predicted_priority(reports, labels)
    assert len(scored.units) == 4
    assert set(scored.review_report_ids) == {"review"}


def test_membership_scores_and_dispatch_inputs_are_permutation_and_truth_invariant() -> None:
    reports, labels, truth, incidents = _fixture()
    forward = score_predicted_priority(reports, labels)
    reverse = score_predicted_priority(
        list(reversed(reports)),
        list(reversed(labels)),
    )
    assert forward.policy_score_maps == reverse.policy_score_maps
    assert [unit.unit_id for unit in forward.units] == [
        unit.unit_id for unit in reverse.units
    ]
    relabelled_values = {0: 11, 1: 7, 2: 19, 3: 5, -1: -1}
    relabelled_labels = [relabelled_values[label] for label in labels]
    relabelled = score_predicted_priority(reports, relabelled_labels)
    assert forward.policy_score_maps == relabelled.policy_score_maps
    assert {unit.unit_id for unit in forward.units} == {
        unit.unit_id for unit in relabelled.units
    }

    changed_truth = [
        replace(row, incident_id="B", gt_cluster=1)
        if row.incident_id == "A"
        else replace(row, incident_id="A", gt_cluster=0)
        if row.incident_id == "B"
        else row
        for row in truth
    ]
    original_evaluation = evaluate_predicted_priority(forward, truth, incidents)
    changed_evaluation = evaluate_predicted_priority(
        forward,
        changed_truth,
        incidents,
    )
    assert original_evaluation.policy_score_maps == changed_evaluation.policy_score_maps
    assert original_evaluation.gain_targets != changed_evaluation.gain_targets

    jobs_before = build_jobs(
        reports,
        labels,
        forward.cluster_score_payload,
        base_time=BASE_TIME,
        snapshot_min=30.0,
    ).jobs
    jobs_after = build_jobs(
        reports,
        labels,
        changed_evaluation.scored.cluster_score_payload,
        base_time=BASE_TIME,
        snapshot_min=30.0,
    ).jobs
    assert jobs_before == jobs_after
    relabelled_jobs = build_jobs(
        reports,
        relabelled_labels,
        relabelled.cluster_score_payload,
        base_time=BASE_TIME,
        snapshot_min=30.0,
    ).jobs
    assert jobs_before == relabelled_jobs
    scenario = ResourceScenarioV2(
        "fixture",
        ((16.0, 108.0),),
        1,
        30.0,
        1.0,
        5.0,
    )
    assert schedule_hash(schedule_jobs(jobs_before, scenario, "revised")) == schedule_hash(
        schedule_jobs(jobs_after, scenario, "revised")
    )


def test_one_to_one_max_overlap_keeps_split_merge_and_noise_explicit() -> None:
    reports, labels, truth, incidents = _fixture()
    scored = score_predicted_priority(reports, labels)
    result = evaluate_predicted_priority(scored, truth, incidents, k=3)

    merged = _unit_with_report(result, "a1")
    split_fragment = _unit_with_report(result, "a4")
    noise = _unit_with_report(result, "noise")
    c_unit = _unit_with_report(result, "c1")

    assert merged.matched_incident_id == "A"
    assert merged.matched_overlap_reports == 3
    assert merged.gain == 10.0
    assert merged.is_split and merged.is_merge
    assert merged.disposition == "matched_split_merge"

    assert split_fragment.matched_incident_id is None
    assert split_fragment.gain == 0.0
    assert split_fragment.disposition == "unmatched_linked_fragment"

    assert noise.matched_incident_id is None
    assert noise.gain == 0.0
    assert noise.disposition == "noise_only"
    assert c_unit.matched_incident_id == "C"
    assert result.unmatched_incident_ids == ("B",)
    assert set(result.gain_targets) == set(next(iter(result.policy_score_maps.values())))
    assert len(result.alignment_rows) == 6


@pytest.mark.parametrize("family", STRESS_FAMILIES_V2)
def test_all_stress_families_score_before_truth_and_preserve_complete_join(
    family: str,
) -> None:
    reports, labels, truth, incidents = _fixture()
    result = evaluate_priority_stress(
        reports,
        labels,
        truth,
        incidents,
        family,  # type: ignore[arg-type]
        k=3,
    )
    assert len(result.stress_rows) == 6
    assert {row["policy"] for row in result.stress_rows} == {
        "legacy",
        "population_only",
        "random",
        "revised",
        "simple_linear",
        "urgency_only",
    }
    assert {row.report_id for row in result.stressed_report_truth} == {
        row.report_id for row in result.case.reports
    }
    if family == "coordinated_high_confidence_campaign":
        campaign_truth = [
            row
            for row in result.stressed_report_truth
            if row.report_id in result.case.campaign_report_ids
        ]
        assert len(campaign_truth) == 5
        assert all(row.incident_id is None for row in campaign_truth)
        assert all(row.is_noise and row.is_fake for row in campaign_truth)
        campaign_units = [
            row
            for row in result.stressed.evaluated_units
            if set(row.report_ids).intersection(result.case.campaign_report_ids)
        ]
        assert len(campaign_units) == 1
        assert campaign_units[0].disposition == "noise_only"
        assert campaign_units[0].gain == 0.0
        revised = next(
            row for row in result.stress_rows if row["policy"] == "revised"
        )
        assert revised["false_priority_lift"]["applicable"] is True
        assert revised["false_priority_lift"]["raw_campaign_score"] > 0.0
        assert 0.0 < revised["false_priority_lift"]["normalized_score_change"] <= 1.0


def test_campaign_case_is_observable_only_and_truth_attachment_is_noise() -> None:
    reports, labels, truth, _ = _fixture()
    case = build_observable_priority_stress(
        reports,
        labels,
        "coordinated_high_confidence_campaign",
    )
    changed_truth = [
        replace(row, incident_id="C", gt_cluster=2)
        if row.incident_id is not None
        else row
        for row in truth
    ]
    # Observable perturbation is already fixed before either truth view exists.
    assert case == build_observable_priority_stress(
        reports,
        labels,
        "coordinated_high_confidence_campaign",
    )
    first = attach_evaluator_truth_to_stress(case, truth)
    second = attach_evaluator_truth_to_stress(case, changed_truth)
    for rows in (first, second):
        campaign = [
            row for row in rows if row.report_id in case.campaign_report_ids
        ]
        assert campaign
        assert all(row.incident_id is None and row.is_noise for row in campaign)


def test_exact_duplicate_has_zero_revised_drift_but_legacy_can_move() -> None:
    reports, labels, truth, incidents = _fixture()
    result = evaluate_priority_stress(
        reports,
        labels,
        truth,
        incidents,
        "exact_duplicate",
        k=3,
    )
    rows = {row["policy"]: row for row in result.stress_rows}
    assert rows["revised"]["drift"]["max_absolute_score_drift"] == pytest.approx(0.0)
    assert rows["legacy"]["drift"]["max_absolute_score_drift"] > 0.0


def test_evaluator_fails_closed_on_incomplete_or_duplicate_truth() -> None:
    reports, labels, truth, incidents = _fixture()
    scored = score_predicted_priority(reports, labels)
    with pytest.raises(PriorityEvaluationV2Error, match="cover every observable"):
        evaluate_predicted_priority(scored, truth[:-1], incidents)
    with pytest.raises(PriorityEvaluationV2Error, match="ids must be unique"):
        evaluate_predicted_priority(scored, [*truth, truth[0]], incidents)
