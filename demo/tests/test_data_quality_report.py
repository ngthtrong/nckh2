from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from data.generate import build_candidate_dataset
from data.schema import canonical_json_bytes, sha256_bytes
from experiments.data_quality_report import (
    REPORT_SCHEMA_VERSION,
    build_distribution_report,
    write_distribution_report,
)


def _mini_bundle(
    root: Path,
    seeds: tuple[tuple[str, int], ...] = (
        ("development", 1000),
        ("calibration", 2000),
        ("test", 3000),
    ),
) -> tuple[Path, dict]:
    bundle = root / "datasets"
    bundle.mkdir()
    entries: list[dict] = []
    for split, seed in seeds:
        data = build_candidate_dataset(seed, split)
        relative = Path(split) / f"seed_{seed}.json"
        destination = bundle / relative
        destination.parent.mkdir(exist_ok=True)
        payload = canonical_json_bytes(data)
        destination.write_bytes(payload)
        entries.append(
            {
                "seed": seed,
                "split": split,
                "path": relative.as_posix(),
                "sha256": sha256_bytes(payload),
                "quality_status": "pass",
            }
        )
    manifest = {
        "schema_version": "candidate-dataset-manifest-v2",
        "dataset_schema_version": "flood-rescue-synthetic-v4",
        "generator_version": "4.1.0",
        "generator_sha256": "1" * 64,
        "schema_sha256": "2" * 64,
        "seed_manifest_sha256": "3" * 64,
        "data_spec_sha256": "4" * 64,
        "entries": entries,
    }
    (bundle / "manifest.json").write_bytes(canonical_json_bytes(manifest))
    return bundle, manifest


def test_distribution_report_is_deterministic_complete_and_descriptive(
    tmp_path: Path,
) -> None:
    bundle, manifest = _mini_bundle(tmp_path)

    first = build_distribution_report(bundle, manifest)
    second = build_distribution_report(bundle, manifest)

    assert first["schema_version"] == REPORT_SCHEMA_VERSION
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert first["scope_policy"] == {
        "method_agnostic": True,
        "contains_method_performance_metrics": False,
        "contains_scientific_endpoints": False,
        "test_split_use": "descriptive_data_freeze_only",
        "test_split_available_to_tuning": False,
        "acceptance_depends_on_preferred_method": False,
    }
    assert first["source"]["n_datasets"] == 3
    assert set(first["by_split"]) == {"development", "calibration", "test"}
    assert len(first["by_incident_family"]) == 8
    assert len(first["by_split_and_incident_family"]["test"]) == 8
    assert len(first["per_seed_counts_and_rates"]) == 3

    overall = first["overall"]
    assert overall["scope"]["n_incidents"] == 48
    assert overall["scope"]["n_reports"] > 0
    assert overall["scope"]["n_unlinked_reports"] > 0
    assert overall["duplicates"]["exact"]["report_count"] > 0
    assert overall["duplicates"]["near"]["report_count"] > 0
    assert overall["reports_per_incident"]["n"] == 48
    assert overall["latent_incident_truth"]["n_true"]["p95"] is not None
    assert overall["latent_incident_truth"]["v_true"]["mad"] is not None
    assert overall["membership_overlap"][
        "pairwise_population_jaccard"
    ]["n"] > 0
    assert overall["coordinate_time_context_dispersion"][
        "coordinate_distance_to_latent_center_m"
    ]["p95"] > 0
    assert overall["latent_outcome_parameters"]["deadline_min"]["n"] == 48

    truth = overall["confidence_truth_overlap"]
    assert truth["truth_counts"]["real"] > 0
    assert truth["truth_counts"]["fake"] > 0
    assert 0 <= truth["histogram_overlap_coefficient"] <= 1
    assert truth["band_cut_role"].endswith("not_an_acceptance_or_tuning_threshold")

    # The report contains aggregate evidence, never row-level identifiers or
    # method outputs that could be reused as a scientific test endpoint.
    serialized = canonical_json_bytes(first).decode("utf-8")
    assert re.search(r"EV-[0-9a-f]{20}", serialized) is None
    assert re.search(r"I(?:D)?\d{4}-\d{2}", serialized) is None
    assert '"gt_cluster"' not in serialized
    assert '"predicted_labels"' not in serialized
    assert '"ari"' not in serialized
    assert '"p_value"' not in serialized


def test_measurement_missingness_uses_mask_not_imputed_zero(tmp_path: Path) -> None:
    bundle, manifest = _mini_bundle(
        tmp_path,
        seeds=(("development", 1000),),
    )
    data_path = bundle / manifest["entries"][0]["path"]
    data = json.loads(data_path.read_text(encoding="utf-8"))

    report = build_distribution_report(bundle, manifest)
    observed = report["overall"]["missingness"]["observable"]
    for field in ("flood", "urgency", "n_trapped", "vulnerability"):
        expected = sum(
            field in row["missing_fields"] for row in data["reports"]
        )
        assert observed[field]["missing_count"] == expected
        assert observed[field]["missing_rate"] == pytest.approx(
            expected / len(data["reports"]),
            abs=1e-6,
        )

    # Valid boundary zeros that were observed are not silently reclassified as
    # missing by the profiling code.
    for field in ("flood", "urgency", "n_trapped", "vulnerability"):
        observed_zero = sum(
            float(row[field]) == 0.0 and field not in row["missing_fields"]
            for row in data["reports"]
        )
        if observed_zero:
            assert observed[field]["missing_count"] < sum(
                float(row[field]) == 0.0 for row in data["reports"]
            )


def test_report_matches_frozen_counts_and_is_exclusive(tmp_path: Path) -> None:
    bundle, manifest = _mini_bundle(
        tmp_path,
        seeds=(("calibration", 2000),),
    )
    data = json.loads(
        (bundle / manifest["entries"][0]["path"]).read_text(encoding="utf-8")
    )
    destination = tmp_path / "tables" / "data_distribution_report.json"

    report, digest = write_distribution_report(bundle, destination, manifest)

    payload = destination.read_bytes()
    assert digest == sha256_bytes(payload)
    assert payload == canonical_json_bytes(report)
    assert report["overall"]["scope"]["n_reports"] == len(data["reports"])
    expected_unlinked = sum(
        row["evaluation_only"]["incident_id"] is None for row in data["reports"]
    )
    assert report["overall"]["scope"]["n_unlinked_reports"] == expected_unlinked
    with pytest.raises(FileExistsError):
        write_distribution_report(bundle, destination, manifest)


def test_report_refuses_manifest_or_dataset_checksum_mismatch(tmp_path: Path) -> None:
    bundle, manifest = _mini_bundle(
        tmp_path,
        seeds=(("test", 3000),),
    )
    changed_manifest = dict(manifest)
    changed_manifest["generator_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="differs"):
        build_distribution_report(bundle, changed_manifest)

    path = bundle / manifest["entries"][0]["path"]
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="checksum mismatch"):
        build_distribution_report(bundle, manifest)
