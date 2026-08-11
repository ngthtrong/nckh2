from dataclasses import fields
from datetime import datetime, timezone

import pytest

from demo.v2.contracts import (
    IncidentTruthV2,
    ObservationMaskV2,
    ReportV2,
    TruthV2,
    validate_unique_report_ids,
)


def test_report_derives_mask_and_normalises_observations() -> None:
    report = ReportV2(
        report_id=" r-1 ",
        L=[16.0, 108.0],
        T="2026-08-11T09:30:00+07:00",
        F=0.0,
        E=None,
        N=12,
        V=None,
        source_id=" phone-7 ",
        source_family=" citizen ",
        provenance_quality=0.75,
    )

    assert report.report_id == "r-1"
    assert report.L == (16.0, 108.0)
    assert report.T == datetime(2026, 8, 11, 2, 30, tzinfo=timezone.utc)
    assert report.mask == ObservationMaskV2(
        L=True,
        T=True,
        F=True,
        E=False,
        N=True,
        V=False,
    )
    assert report.missing_fields == ("E", "V")
    assert report.source_id == "phone-7"
    assert report.source_family == "citizen"
    assert report.graph_eligible


def test_report_rejects_mask_that_disagrees_with_nullable_values() -> None:
    with pytest.raises(ValueError, match="mask must agree"):
        ReportV2(
            report_id="r-1",
            F=None,
            mask=ObservationMaskV2(
                L=False,
                T=False,
                F=True,
                E=False,
                N=False,
                V=False,
            ),
        )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"F": 1.01}, "F must lie"),
        ({"N": -1}, "N must be non-negative"),
        ({"L": (91, 0)}, "latitude"),
        ({"provenance_quality": 1.1}, "provenance_quality"),
    ],
)
def test_report_validates_observable_domains(kwargs: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        ReportV2(report_id="r-invalid", **kwargs)


def test_report_and_evaluator_truth_are_structurally_separate() -> None:
    report_fields = {item.name for item in fields(ReportV2)}
    evaluator_only = {"incident_id", "gt_cluster", "is_noise", "is_fake"}
    assert report_fields.isdisjoint(evaluator_only)

    report = ReportV2(report_id="r-1")
    truth = TruthV2(
        report_id="r-1",
        incident_id="incident-1",
        gt_cluster=3,
    )
    assert truth.report_id == report.report_id
    with pytest.raises((AttributeError, TypeError)):
        report.incident_id = "leak"  # type: ignore[attr-defined,misc]


def test_incident_truth_is_evaluator_only_and_validated() -> None:
    truth = IncidentTruthV2(
        incident_id="i-1",
        L=(16.1, 108.2),
        start_min=10,
        deadline_min=90,
        latent_need=0.8,
        service_demand_min=25,
        harm_grace_min=5,
        harm_slope=1.2,
        max_harm=100,
        n_true=30,
        v_true=7,
        latent_benefit=20,
    )
    assert truth.latitude == 16.1
    assert truth.longitude == 108.2

    with pytest.raises(ValueError, match="v_true cannot exceed"):
        IncidentTruthV2(
            incident_id="i-bad",
            L=(16.1, 108.2),
            start_min=10,
            deadline_min=90,
            latent_need=0.8,
            service_demand_min=25,
            harm_grace_min=5,
            harm_slope=1.2,
            max_harm=100,
            n_true=3,
            v_true=7,
        )


def test_report_ids_must_be_unique_for_joinable_batches() -> None:
    with pytest.raises(ValueError, match="duplicate report_id"):
        validate_unique_report_ids(
            [ReportV2(report_id="r-1"), ReportV2(report_id="r-1")]
        )

