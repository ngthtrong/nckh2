from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from demo.v2.contracts import ReportV2
from demo.v2.priority import PriorityPolicyV2, report_provenance_scores, score_cluster


def _report(identifier: str, east: float = 0.0, source: str = "s1") -> ReportV2:
    longitude = 108.0 + east / 106_000.0
    return ReportV2(
        identifier,
        L=(16.0, longitude),
        T=datetime(2026, 1, 1, tzinfo=timezone.utc),
        F=0.8,
        E=0.7,
        N=20,
        V=4,
        source_id=source,
        source_family="hotline",
        provenance_quality=0.7,
    )


def test_revised_priority_is_bounded_and_exact_duplicate_invariant() -> None:
    report = _report("r1")
    duplicate = replace(report, report_id="r2")
    policy = PriorityPolicyV2()
    one_provenance = report_provenance_scores([report], policy)
    two_provenance = report_provenance_scores([report, duplicate], policy)
    one = score_cluster(0, [report], one_provenance, policy)
    two = score_cluster(0, [report, duplicate], two_provenance, policy)
    assert one.revised == pytest.approx(two.revised)
    assert 0.0 <= two.revised <= policy.revised_upper_bound
    assert two.exact_duplicates_removed == 1
    assert two.legacy > one.legacy


def test_same_source_multiplicity_does_not_increase_corroboration_quality() -> None:
    first = _report("r1", source="same")
    second = replace(first, report_id="r2", L=(16.0, 108.0001))
    alone = report_provenance_scores([first])["r1"]
    repeated = report_provenance_scores([first, second])["r1"]
    assert repeated == pytest.approx(alone)


def test_distinct_source_corroboration_is_capped() -> None:
    base = _report("r0", source="base")
    reports = [base]
    for index in range(8):
        reports.append(
            replace(
                base,
                report_id=f"r{index + 1}",
                source_id=f"source-{index}",
                source_family=f"family-{index}",
                T=base.T + timedelta(minutes=index),
            )
        )
    quality = report_provenance_scores(reports)
    assert quality["r0"] <= 1.0


def test_missing_priority_fields_remain_missing_not_zero_imputed() -> None:
    complete = _report("r1")
    missing = replace(complete, report_id="r2", E=None, F=None, N=None, V=None, mask=None)
    provenance = report_provenance_scores([missing])
    score = score_cluster(0, [missing], provenance)
    assert score.e_agg == 0.0
    assert score.f_max == 0.0
    assert score.n_norm == 0.0
    assert score.v_agg == 0.0
