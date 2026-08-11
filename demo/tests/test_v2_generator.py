from __future__ import annotations

from dataclasses import fields

import pytest

from demo.v2.contracts import TruthV2
from demo.v2.generator import (
    BASE_TIME,
    SNAPSHOT_CUTOFF_MIN_V2,
    GeneratedDatasetV2,
    dataset_hashes,
    generate_dataset,
    observation_snapshot,
)


def test_generator_is_deterministic_and_truth_is_separate() -> None:
    first = generate_dataset(4100, "id")
    second = generate_dataset(4100, "id")
    assert dataset_hashes(first) == dataset_hashes(second)
    assert {row.report_id for row in first.reports} == {
        row.report_id for row in first.report_truth
    }
    report_field_names = {item.name for item in fields(first.reports[0])}
    assert "incident_id" not in report_field_names
    assert "deadline_min" not in report_field_names
    assert "latent_benefit" not in report_field_names


def test_id_and_ood_change_mechanism_not_only_seed() -> None:
    in_distribution = generate_dataset(4101, "id")
    shifted = generate_dataset(4101, "ood")
    assert in_distribution.metadata["n_incidents"] == 16
    assert shifted.metadata["ood_mechanism_changes"]
    assert "source_and_severity_correlated_mnar" in shifted.metadata[
        "ood_mechanism_changes"
    ]
    assert any(
        row.family == "coordinated_high_confidence_campaign"
        for row in shifted.stress_annotations
    )
    assert any(
        row.family == "gradual_chain_duplicate" for row in shifted.stress_annotations
    )


def test_missing_location_or_time_is_explicitly_graph_ineligible() -> None:
    dataset = generate_dataset(4102, "ood")
    incomplete = [report for report in dataset.reports if not report.graph_eligible]
    assert incomplete
    assert all("L" in report.missing_fields or "T" in report.missing_fields for report in incomplete)


def test_public_anchor_is_fail_closed_until_source_audit() -> None:
    dataset = generate_dataset(4103, "id")
    assert dataset.metadata["public_anchor_audit_id"] == "audit.public_external_anchor.v2"
    assert dataset.metadata["public_anchor_role"] == "descriptive_plausibility_check_only"
    assert dataset.metadata["public_parameters_fitted"] == []
    assert dataset.metadata["public_marginal_anchor"].startswith("no_parameters_fitted")


def test_observation_snapshot_uses_receipt_time_and_retains_missing_event_time() -> None:
    full = generate_dataset(4100, "ood")
    snapshot = observation_snapshot(full)
    cutoff = BASE_TIME.timestamp() + SNAPSHOT_CUTOFF_MIN_V2 * 60.0
    assert len(snapshot.reports) < len(full.reports)
    assert all(
        report.received_at is not None and report.received_at.timestamp() <= cutoff
        for report in snapshot.reports
    )
    assert all(
        incident.start_min <= SNAPSHOT_CUTOFF_MIN_V2
        for incident in snapshot.incident_truth
    )
    assert any(report.T is None for report in snapshot.reports)
    incident_ids = {row.incident_id for row in snapshot.incident_truth}
    assert all(
        row.incident_id is None or row.incident_id in incident_ids
        for row in snapshot.report_truth
    )
    assert snapshot.metadata["snapshot_rule"] == "received_at_at_or_before_cutoff"


def test_generated_dataset_rejects_duplicate_truth_rows() -> None:
    dataset = generate_dataset(4104, "id")
    duplicated = (dataset.report_truth[0], *dataset.report_truth)
    with pytest.raises(ValueError, match="do not align"):
        GeneratedDatasetV2(
            dataset.regime,
            dataset.master_seed,
            dataset.reports,
            duplicated,
            dataset.incident_truth,
            dataset.stress_annotations,
            dataset.metadata,
        )


def test_truth_contract_rejects_ambiguous_unlinked_state() -> None:
    with pytest.raises(ValueError, match="explicitly marked noise"):
        TruthV2("ambiguous")


def test_confirmation_and_retired_seeds_fail_closed_before_generation() -> None:
    with pytest.raises(ValueError, match="managed single-release"):
        generate_dataset(4400, "id")
    with pytest.raises(ValueError, match="permanently unavailable"):
        generate_dataset(4300, "id")
