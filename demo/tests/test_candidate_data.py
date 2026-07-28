from __future__ import annotations

import hashlib
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import pytest

from data.generate import (
    build_candidate_dataset,
    candidate_fake_truth,
    candidate_ground_truth,
    candidate_inference_events,
    write_candidate_bundle,
)
from data.schema import (
    FORBIDDEN_INFERENCE_FIELDS,
    _near_duplicate_ok,
    canonical_json_bytes,
    observable_report,
    registered_seed_splits,
    report_fingerprint,
    validate_candidate_dataset,
)
from pipeline.attributes import compute_confidence
from pipeline.attributes import Event
from pipeline.config import DEFAULT_CONFIG
from pipeline.priority import (
    are_near_duplicate_reports,
    observable_report_fingerprint,
)


def test_candidate_seed_is_byte_deterministic() -> None:
    first = build_candidate_dataset(1000, "development")
    second = build_candidate_dataset(1000, "development")
    assert canonical_json_bytes(first) == canonical_json_bytes(second)


def test_candidate_quality_and_inference_isolation() -> None:
    data = build_candidate_dataset(2000, "calibration")
    quality = validate_candidate_dataset(
        data, expected_seed=2000, expected_split="calibration"
    )
    assert quality["status"] == "pass"
    assert quality["n_incidents"] == 16
    assert quality["n_linked_reports"] > 0
    assert quality["n_unlinked_reports"] > 0
    assert quality["n_exact_duplicate_reports"] > 0
    assert quality["n_near_duplicate_reports"] > 0
    assert any(report["missing_fields"] for report in data["reports"])

    for report in data["reports"]:
        assert not (set(observable_report(report)) & FORBIDDEN_INFERENCE_FIELDS)
        assert report["event_id"].startswith("EV-")
        assert len(report["event_id"]) == 23
        assert report["note"] == "synthetic_report"
        assert "is_fake" not in report
        assert isinstance(report["evaluation_only"]["is_fake"], bool)

    events = candidate_inference_events(data)
    ground_truth = candidate_ground_truth(data)
    fake_truth = candidate_fake_truth(data)
    assert len(events) == len(ground_truth) == len(fake_truth) == quality["n_reports"]
    assert all(event.gt_cluster == -1 for event in events)
    assert all(event.is_fake is False for event in events)
    assert any(label >= 0 for label in ground_truth)
    assert any(fake_truth)


def test_exact_duplicate_payloads_are_identical() -> None:
    data = build_candidate_dataset(3000, "test")
    groups: dict[str, list[dict]] = {}
    for report in data["reports"]:
        evaluation = report["evaluation_only"]
        if evaluation["duplicate_kind"] == "exact":
            groups.setdefault(evaluation["duplicate_family_id"], []).append(report)
    assert groups
    for rows in groups.values():
        assert len(rows) == 2
        payloads = []
        for report in rows:
            payload = observable_report(report)
            payload.pop("event_id")
            payload.pop("note")
            payloads.append(payload)
        assert payloads[0] == payloads[1]


def test_generator_and_priority_duplicate_contracts_match() -> None:
    data = build_candidate_dataset(1000, "development")
    events = candidate_inference_events(data)
    compute_confidence(events, DEFAULT_CONFIG.confidence)

    exact: dict[str, list[int]] = {}
    near: dict[str, list[int]] = {}
    for index, report in enumerate(data["reports"]):
        evaluation = report["evaluation_only"]
        kind = evaluation["duplicate_kind"]
        if kind == "exact":
            exact.setdefault(evaluation["duplicate_family_id"], []).append(index)
        elif kind == "near":
            near.setdefault(evaluation["duplicate_family_id"], []).append(index)

        assert report_fingerprint(report) == observable_report_fingerprint(events[index])

    assert exact and near
    for indices in exact.values():
        assert len(indices) == 2
        assert events[indices[0]].confidence == pytest.approx(
            events[indices[1]].confidence
        )
    for indices in near.values():
        assert len(indices) == 2
        assert are_near_duplicate_reports(events[indices[0]], events[indices[1]])


def test_schema_and_priority_share_relative_n_near_boundary() -> None:
    created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    first = Event(
        event_id="a",
        lat=16.0,
        lng=108.0,
        created_at=created_at,
        flood=0.5,
        urgency=0.5,
        n_trapped=300,
        vulnerability=2.0,
        has_image=True,
        confidence=0.8,
    )
    second = deepcopy(first)
    second.event_id = "b"
    second.n_trapped = 400
    first_payload = {
        "lat": first.lat,
        "lng": first.lng,
        "created_at": first.created_at.isoformat(),
        "flood": first.flood,
        "urgency": first.urgency,
        "n_trapped": first.n_trapped,
        "vulnerability": first.vulnerability,
    }
    second_payload = {
        **first_payload,
        "n_trapped": second.n_trapped,
    }
    assert _near_duplicate_ok(first_payload, second_payload)
    assert are_near_duplicate_reports(first, second)


def test_exact_duplicate_does_not_inflate_confidence_corroboration() -> None:
    first = Event(
        event_id="a",
        lat=16.0,
        lng=108.0,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        flood=0.7,
        urgency=0.8,
        n_trapped=10,
        vulnerability=2.0,
        has_image=True,
        source_type="citizen_app",
    )
    second = Event(
        event_id="b",
        lat=16.0005,
        lng=108.0005,
        created_at=datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc),
        flood=0.6,
        urgency=0.7,
        n_trapped=8,
        vulnerability=1.0,
        has_image=False,
        source_type="hotline",
    )
    baseline = [deepcopy(first), deepcopy(second)]
    compute_confidence(baseline, DEFAULT_CONFIG.confidence)

    duplicate = deepcopy(first)
    duplicate.event_id = "a-copy"
    attacked = [deepcopy(first), duplicate, deepcopy(second)]
    compute_confidence(attacked, DEFAULT_CONFIG.confidence)

    assert attacked[0].confidence == pytest.approx(baseline[0].confidence)
    assert attacked[1].confidence == pytest.approx(baseline[0].confidence)
    assert attacked[2].confidence == pytest.approx(baseline[1].confidence)


def test_registered_seed_cannot_be_relabelled() -> None:
    with pytest.raises(ValueError, match="belongs to split"):
        build_candidate_dataset(1000, "calibration")
    smoke = build_candidate_dataset(999_999)
    assert smoke["split"] == "unregistered"


def test_low_confidence_attacks_have_no_corroboration() -> None:
    data = build_candidate_dataset(1000, "development")
    events = candidate_inference_events(data)
    compute_confidence(events, DEFAULT_CONFIG.confidence)
    selected = [
        event
        for report, event in zip(data["reports"], events, strict=True)
        if str(report["evaluation_only"].get("adversary", "")).startswith(
            "low_conf_inflate_"
        )
    ]
    assert len(selected) == 4
    assert all(event.n_corrob == 0 for event in selected)
    assert all(event.confidence == pytest.approx(0.45016600268752216) for event in selected)


def _assert_mutation_rejected(data: dict) -> None:
    data["quality"] = {}
    with pytest.raises(ValueError):
        validate_candidate_dataset(data)


@pytest.mark.parametrize(
    "mutation",
    [
        "remove_unlinked",
        "incident_gt_mismatch",
        "missing_fake_truth",
        "undeclared_exact",
        "exact_declared_near",
        "null_event_id",
        "naive_timestamp",
        "semantic_value_leak",
        "top_level_latent_key",
        "empty_linked_membership",
        "boolean_vulnerable_member",
        "missing_duplicate_kind",
        "missing_duplicate_family_id",
        "missing_generator_profile",
        "invalid_generator_profile",
        "missing_incident_province",
        "linked_vulnerability_exceeds_n",
    ],
)
def test_quality_gate_rejects_structural_mutations(mutation: str) -> None:
    data = build_candidate_dataset(1000, "development")
    if mutation == "remove_unlinked":
        data["reports"] = [
            row
            for row in data["reports"]
            if row["evaluation_only"]["incident_id"] is not None
        ]
    elif mutation == "incident_gt_mismatch":
        linked = next(
            row for row in data["reports"] if row["evaluation_only"]["incident_id"]
        )
        linked["evaluation_only"]["gt_cluster"] = 999
    elif mutation == "missing_fake_truth":
        for row in data["reports"]:
            row["evaluation_only"].pop("is_fake")
    elif mutation == "undeclared_exact":
        original = next(
            row
            for row in data["reports"]
            if row["evaluation_only"]["duplicate_kind"] == "none"
        )
        duplicate = deepcopy(original)
        duplicate["event_id"] = "undeclared-copy"
        data["reports"].append(duplicate)
    elif mutation == "exact_declared_near":
        exact_family = next(
            row["evaluation_only"]["duplicate_family_id"]
            for row in data["reports"]
            if row["evaluation_only"]["duplicate_kind"] == "exact"
        )
        for row in data["reports"]:
            if row["evaluation_only"]["duplicate_family_id"] == exact_family:
                row["evaluation_only"]["duplicate_kind"] = "near"
    elif mutation == "null_event_id":
        data["reports"][0]["event_id"] = None
    elif mutation == "naive_timestamp":
        data["reports"][0]["created_at"] = "2026-10-15T08:00:00"
    elif mutation == "semantic_value_leak":
        data["reports"][0]["province"] = "independent_stress_region"
    elif mutation == "top_level_latent_key":
        data["reports"][0]["incident_id"] = "leaked-incident"
    elif mutation == "empty_linked_membership":
        linked = next(
            row for row in data["reports"] if row["evaluation_only"]["incident_id"]
        )
        linked["evaluation_only"]["population_member_indices"] = []
        linked["evaluation_only"]["vulnerable_member_indices"] = []
        linked["evaluation_only"]["coverage_n"] = 0.0
        linked["evaluation_only"]["coverage_v"] = 0.0
    elif mutation == "boolean_vulnerable_member":
        linked = next(
            row
            for row in data["reports"]
            if row["evaluation_only"]["vulnerable_member_indices"]
        )
        linked["evaluation_only"]["vulnerable_member_indices"][0] = True
    elif mutation == "missing_duplicate_kind":
        data["reports"][0]["evaluation_only"].pop("duplicate_kind")
    elif mutation == "missing_duplicate_family_id":
        data["reports"][0]["evaluation_only"].pop("duplicate_family_id")
    elif mutation == "missing_generator_profile":
        data["incidents"][0].pop("generator_profile")
    elif mutation == "invalid_generator_profile":
        data["incidents"][0]["generator_profile"]["spread_m"] = -1.0
    elif mutation == "missing_incident_province":
        data["incidents"][0].pop("province")
    elif mutation == "linked_vulnerability_exceeds_n":
        linked = next(
            row for row in data["reports"] if row["evaluation_only"]["incident_id"]
        )
        linked["n_trapped"] = 1
        linked["vulnerability"] = 2.0
        linked["missing_fields"] = []
    _assert_mutation_rejected(data)


def test_quality_gate_rejects_stale_embedded_quality() -> None:
    data = build_candidate_dataset(1000, "development")
    data["quality"]["latent_n_total"] = -999
    with pytest.raises(ValueError, match="embedded quality is stale"):
        validate_candidate_dataset(data)


def test_bundle_refuses_overwrite_and_preserves_historical_dataset(
    tmp_path: Path,
) -> None:
    historical = Path(__file__).resolve().parents[1] / "data" / "dataset.json"
    before = hashlib.sha256(historical.read_bytes()).hexdigest()
    target = tmp_path / "datasets"
    with pytest.raises(ValueError, match="exact locked"):
        write_candidate_bundle(target, {"development": [1000]})
    assert not target.exists()

    manifest = write_candidate_bundle(target)
    assert len(manifest["entries"]) == 80
    assert len({row["seed"] for row in manifest["entries"]}) == 80
    assert all(row["quality_status"] == "pass" for row in manifest["entries"])
    assert manifest["seed_mapping"] == {
        split: list(seeds) for split, seeds in registered_seed_splits().items()
    }
    assert manifest["schema_sha256"]
    assert manifest["seed_manifest_sha256"]
    assert manifest["data_spec_sha256"]
    with pytest.raises((FileExistsError, ValueError)):
        write_candidate_bundle(target)
    after = hashlib.sha256(historical.read_bytes()).hexdigest()
    assert before == after
