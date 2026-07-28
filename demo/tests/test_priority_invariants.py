from __future__ import annotations

import math
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from demo.data.schema import report_fingerprint
from demo.pipeline.attributes import Event
from demo.pipeline.config import PriorityParams
from demo.pipeline.priority import (
    NearDuplicatePolicy,
    REVISED_ESTIMATOR_NAME,
    aggregate_cluster_evidence,
    are_near_duplicate_reports,
    observable_report_fingerprint,
    priority_range,
    score_clusters,
)


BASE_TIME = datetime(2026, 10, 15, 8, 0, tzinfo=timezone.utc)
PARAMS = PriorityParams()


def _event(
    event_id: str,
    *,
    lat: float = 16.46,
    lng: float = 107.59,
    minute: float = 0.0,
    flood: float = 0.70,
    urgency: float = 0.80,
    n_trapped: int = 100,
    vulnerability: float = 5.0,
    confidence: float = 0.80,
    source_type: str = "citizen_app",
    province: str = "Thừa Thiên Huế",
    note: str = "observable narrative excluded from fingerprint",
) -> Event:
    return Event(
        event_id=event_id,
        lat=lat,
        lng=lng,
        created_at=BASE_TIME + timedelta(minutes=minute),
        flood=flood,
        urgency=urgency,
        n_trapped=n_trapped,
        vulnerability=vulnerability,
        has_image=True,
        source_type=source_type,
        province=province,
        note=note,
        gt_cluster=-1,
        is_fake=False,
        confidence=confidence,
    )


def _priority_components(score) -> tuple[float, ...]:
    return (
        score.e_agg,
        score.f_max,
        score.n_total_raw,
        score.n_norm,
        score.v_total_raw,
        score.v_agg,
        score.core,
        score.priority,
        score.center_lat,
        score.center_lng,
    )


def test_default_is_revised_estimator() -> None:
    score = score_clusters([_event("r1")], [0], PARAMS)[0]
    assert score.estimator == REVISED_ESTIMATOR_NAME


def test_fingerprint_matches_candidate_schema_and_excludes_forbidden_fields() -> None:
    event = _event("transport-id", note="first wording")
    report = {
        "event_id": event.event_id,
        "lat": event.lat,
        "lng": event.lng,
        "created_at": event.created_at.isoformat(),
        "flood": event.flood,
        "urgency": event.urgency,
        "n_trapped": event.n_trapped,
        "vulnerability": event.vulnerability,
        "has_image": event.has_image,
        "source_type": event.source_type,
        "province": event.province,
        "note": event.note,
        "evaluation_only": {"incident_id": "latent-a"},
    }
    assert observable_report_fingerprint(event) == report_fingerprint(report)

    changed_only_outside_allow_list = replace(
        event,
        event_id="different-transport-id",
        note="different free text",
        gt_cluster=999,
        is_fake=True,
    )
    changed_only_outside_allow_list.incident_id = "latent-b"  # type: ignore[attr-defined]
    changed_only_outside_allow_list.n_true = 99999  # type: ignore[attr-defined]
    assert (
        observable_report_fingerprint(event)
        == observable_report_fingerprint(changed_only_outside_allow_list)
    )


def test_exact_duplicate_is_strictly_invariant_without_incident_id() -> None:
    original = _event("r1")
    duplicate = replace(
        original,
        event_id="r1-copy",
        note="transport text may differ",
        gt_cluster=123,
        is_fake=True,
    )
    duplicate.incident_id = "must-not-be-read"  # type: ignore[attr-defined]

    before = score_clusters([original], [7], PARAMS)[0]
    after = score_clusters([original, duplicate], [7, 7], PARAMS)[0]

    assert _priority_components(after) == _priority_components(before)
    assert after.exact_duplicates_removed == 1
    assert after.evidence_units == before.evidence_units == 1
    # Received-traffic metadata is intentionally not an evidence estimate.
    assert after.size == 2
    assert after.member_ids == ["r1", "r1-copy"]


def test_exact_duplicate_with_inconsistent_confidence_fails_closed() -> None:
    original = _event("r1", confidence=0.80)
    conflicting = replace(
        original,
        event_id="r1-conflicting-copy",
        confidence=0.81,
    )
    assert (
        observable_report_fingerprint(original)
        == observable_report_fingerprint(conflicting)
    )

    with pytest.raises(ValueError, match="inconsistent derived confidence"):
        score_clusters([original, conflicting], [0, 0], PARAMS)


def test_zero_confidence_report_changes_no_priority_component() -> None:
    reliable = _event("reliable")
    zero_confidence = _event(
        "zero",
        lat=17.0,
        lng=108.5,
        minute=180,
        flood=1.0,
        urgency=1.0,
        n_trapped=10**9,
        vulnerability=10**9,
        confidence=0.0,
        source_type="unverified",
    )

    before = score_clusters([reliable], [0], PARAMS)[0]
    after = score_clusters(
        [reliable, zero_confidence],
        [0, 0],
        PARAMS,
    )[0]

    assert _priority_components(after) == _priority_components(before)
    assert after.evidence_units == before.evidence_units == 1


def test_single_near_duplicate_stays_within_declared_drift_policy() -> None:
    original = _event("r1")
    near = _event(
        "r2",
        lat=16.46020,
        lng=107.59020,
        minute=4,
        flood=0.76,
        urgency=0.86,
        n_trapped=110,
        vulnerability=6.0,
        confidence=0.85,
    )
    assert are_near_duplicate_reports(original, near)

    before = score_clusters([original], [0], PARAMS)[0]
    after = score_clusters([original, near], [0, 0], PARAMS)[0]
    lower, upper = priority_range(PARAMS)
    drift_fraction = abs(after.priority - before.priority) / (upper - lower)

    assert after.near_duplicates_coalesced == 1
    assert drift_fraction <= NearDuplicatePolicy().max_priority_drift_fraction
    assert 0.0 <= after.e_agg <= 1.0
    assert 0.0 <= after.f_max <= 1.0
    assert 0.0 <= after.n_norm <= 1.0


@pytest.mark.parametrize(
    ("original_values", "near_values", "minimum_expected_drift"),
    [
        # Deterministic worst boundary found by the Gate-1 grid/optimization:
        # absolute-N floor 0 -> 5 plus simultaneous C/E/F/V boundaries.
        (
            {"flood": 0.9, "urgency": 0.9, "n_trapped": 0,
             "vulnerability": 9.5, "confidence": 0.9},
            {"flood": 1.0, "urgency": 1.0, "n_trapped": 5,
             "vulnerability": 11.5, "confidence": 1.0},
            0.23,
        ),
        # Relative-N boundary: 375 -> 500 is exactly the 25% envelope limit.
        (
            {"flood": 0.9, "urgency": 0.9, "n_trapped": 375,
             "vulnerability": 5.16, "confidence": 0.9},
            {"flood": 1.0, "urgency": 1.0, "n_trapped": 500,
             "vulnerability": 7.16, "confidence": 1.0},
            0.19,
        ),
    ],
)
def test_adversarial_near_duplicate_boundaries_obey_revised_ceiling(
    original_values: dict[str, float],
    near_values: dict[str, float],
    minimum_expected_drift: float,
) -> None:
    original = _event("boundary-a", **original_values)
    near = _event("boundary-b", **near_values)
    policy = NearDuplicatePolicy()
    assert are_near_duplicate_reports(original, near, policy)

    before = score_clusters([original], [0], PARAMS)[0]
    after = score_clusters([original, near], [0, 0], PARAMS)[0]
    lower, upper = priority_range(PARAMS)
    drift_fraction = abs(after.priority - before.priority) / (upper - lower)

    # These cases deliberately falsify the superseded 10% draft threshold.
    assert drift_fraction >= minimum_expected_drift
    assert drift_fraction <= policy.max_priority_drift_fraction
    assert after.near_duplicates_coalesced == 1


def test_extreme_finite_claims_are_clipped_and_priority_is_bounded() -> None:
    extreme = _event(
        "extreme",
        flood=10**6,
        urgency=10**6,
        n_trapped=10**12,
        vulnerability=10**12,
        confidence=10**6,
    )
    score = score_clusters([extreme], [0], PARAMS)[0]
    lower, upper = priority_range(PARAMS)

    assert score.e_agg == 1.0
    assert score.f_max == 1.0
    assert score.n_total_raw == PARAMS.n_ref
    assert score.n_norm == 1.0
    assert score.v_total_raw == 50.0
    assert lower <= score.priority <= upper
    assert score.priority_upper_bound == upper


def test_legacy_raw_reproduces_pre_revision_equations() -> None:
    events = [
        _event(
            "a",
            lat=16.0,
            lng=107.0,
            flood=0.9,
            urgency=0.7,
            n_trapped=40,
            vulnerability=3.0,
            confidence=0.8,
        ),
        _event(
            "b",
            lat=16.2,
            lng=107.4,
            flood=0.4,
            urgency=0.5,
            n_trapped=10,
            vulnerability=2.0,
            confidence=0.3,
        ),
    ]
    score = score_clusters(
        events,
        [5, 5],
        PARAMS,
        estimator="legacy_raw",
    )[0]

    e_agg = sum(event.urgency * event.confidence for event in events) / 2
    f_max = max(event.flood * event.confidence for event in events)
    n_raw = sum(event.n_trapped * event.confidence for event in events)
    n_norm = min(
        1.0,
        math.log1p(n_raw) / math.log1p(PARAMS.n_ref),
    )
    v_raw = sum(event.vulnerability for event in events)
    v_agg = 1.0 + (PARAMS.v_cap_mu - 1.0) * math.tanh(
        v_raw / PARAMS.v_scale
    )
    core = (
        PARAMS.omega_e * e_agg
        + PARAMS.omega_f * f_max
        + PARAMS.omega_n * n_norm
    )
    expected_priority = v_agg * core

    assert score.estimator == "legacy_raw"
    assert score.e_agg == pytest.approx(round(e_agg, 4))
    assert score.f_max == pytest.approx(round(f_max, 4))
    assert score.n_total_raw == pytest.approx(round(n_raw, 2))
    assert score.n_norm == pytest.approx(round(n_norm, 4))
    assert score.v_total_raw == pytest.approx(round(v_raw, 4))
    assert score.v_agg == pytest.approx(round(v_agg, 4))
    assert score.core == pytest.approx(round(core, 4))
    assert score.priority == pytest.approx(round(expected_priority, 4))
    assert score.center_lat == pytest.approx(16.1)
    assert score.center_lng == pytest.approx(107.2)


def test_public_estimator_api_rejects_empty_cluster_and_label_mismatch() -> None:
    with pytest.raises(ValueError, match="members"):
        aggregate_cluster_evidence([], PARAMS)
    with pytest.raises(ValueError, match="cùng độ dài"):
        score_clusters([_event("r1")], [], PARAMS)
