from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable

import pytest

from demo.v2 import reporting


def _write_json(path: Path, payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    path.write_bytes(encoded)
    return hashlib.sha256(encoded).hexdigest()


def _descriptive(identifier: str) -> dict[str, float | int]:
    if identifier.endswith("ari_linked"):
        value = 0.72
    elif identifier.endswith("false_destinations_per_100_reports"):
        value = 2.50
    elif identifier.endswith("noise_rejection"):
        value = 0.81
    elif identifier.endswith("review_items_per_100_reports"):
        value = 4.25
    else:
        value = 0.20
    return {
        "n": 40,
        "mean": value,
        "standard_deviation": 0.05,
        "median": value,
        "minimum": value - 0.05,
        "maximum": value + 0.05,
    }


def _comparison(
    identifier: str,
    contract: tuple[str, str, str, str, str],
) -> dict[str, Any]:
    candidate, comparator, regime, endpoint, direction = contract
    adverse = identifier == "priority.ood.ndcg_at_k.revised_vs_random"
    improvement = -0.10 if adverse else 0.20
    interval = [-0.18, -0.02] if adverse else [0.12, 0.28]
    return {
        "comparison_id": identifier,
        "candidate": candidate,
        "comparator": comparator,
        "regime": regime,
        "endpoint": endpoint,
        "direction": direction,
        "pairing_key": "master_seed",
        "pairing_key_count": 40,
        "n_seed_pairs": 40,
        "n_candidate_better": 8 if adverse else 32,
        "n_comparator_better": 32 if adverse else 8,
        "n_ties": 0,
        "mean_improvement": improvement,
        "paired_confidence_interval": interval,
        "raw_p_value": 0.01,
        "holm_adjusted_p_value": 0.04,
        "adverse_or_null": adverse,
        "denominator": {
            "unit": "master_seed",
            "n_master_seeds": 40,
            "regime": regime,
            "endpoint": endpoint,
            "candidate": candidate,
            "comparator": comparator,
        },
    }


def _gate_payload() -> dict[str, Any]:
    def gate(identifier: str, status: str) -> dict[str, Any]:
        return {
            "claim_id": identifier,
            "claim": "fixture",
            "scope": "synthetic fixture",
            "status": status,
            "conditions": {"fixture": status == "eligible"},
            "blocked_reasons": [] if status == "eligible" else ["fixture"],
        }

    return {
        "claim.synthetic_controlled_clustering": gate(
            "claim.synthetic_controlled_clustering", "eligible"
        ),
        "claim.synthetic_duplicate_invariance": gate(
            "claim.synthetic_duplicate_invariance", "eligible"
        ),
        "claim.synthetic_priority_alignment": gate(
            "claim.synthetic_priority_alignment", "blocked"
        ),
        **{
            identifier: gate(identifier, "blocked")
            for identifier in (
                "claim.external_priority_sanity",
                "claim.external_consolidation_sanity",
                "claim.external_location_sanity",
                "claim.external_flood_context_descriptive",
                "claim.real_incident_clustering_accuracy",
                "claim.real_dispatch_benefit",
                "claim.vietnamese_transfer",
            )
        },
    }


def _artifact_fixture(tmp_path: Path) -> dict[str, Any]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    protocol_sha = "a" * 64
    implementation_sha = "b" * 64
    freeze_sha = "c" * 64
    selection_path = tmp_path / "calibration_selection.json"
    analysis_path = tmp_path / "confirmation_analysis.json"
    manifest_path = tmp_path / "confirmation_manifest.json"
    output_path = tmp_path / "short_results.tex"

    selection = {
        "schema_version": "v2.calibration-selection.1",
        "protocol_sha256": protocol_sha,
        "implementation_sha256": implementation_sha,
        "selections": {
            method: {
                "status": "selected",
                "configuration": {
                    "configuration_id": f"config.{method.split('.', 1)[1]}.001",
                    "method_id": method,
                },
            }
            for method in reporting.DEFAULT_METHODS
        },
    }
    selection_sha = _write_json(selection_path, selection)

    comparison_contracts = reporting._expected_comparison_contracts()
    descriptive_keys = reporting._expected_descriptive_keys()
    comparisons = {
        section: {
            identifier: _comparison(identifier, contract)
            for identifier, contract in contracts.items()
        }
        for section, contracts in comparison_contracts.items()
    }
    descriptives = {
        section: {identifier: _descriptive(identifier) for identifier in identifiers}
        for section, identifiers in descriptive_keys.items()
    }
    clustering_holm = sorted(comparisons["clustering"])
    priority_dispatch_holm = sorted(
        set(comparisons["priority"])
        | set(comparisons["dispatch"])
        | set(comparisons["stress"])
    )
    analysis = {
        "schema_version": "confirmation-analysis-v2",
        "coverage": {
            "status": "exact",
            "master_seed_count": 40,
            "expected_and_observed_counts": dict(reporting.EXPECTED_COUNTS),
            "duplicate_keys": 0,
            "missing_keys": 0,
            "extra_keys": 0,
        },
        "analysis_contract": {
            "pairing_unit": "master_seed",
            "bootstrap_resamples": 10_000,
            "bootstrap_interval": 0.95,
            "adverse_and_null_results_retained": True,
            "holm_families": {
                "synthetic_clustering": clustering_holm,
                "synthetic_priority_dispatch": priority_dispatch_holm,
            },
        },
        "descriptives": descriptives,
        "comparisons": comparisons,
        "claim_gates": _gate_payload(),
        "evidence_gates": {
            "predicted_cluster_dispatch": {
                "claim_id": "evidence.synthetic_predicted_cluster_dispatch",
                "claim": "fixture dispatch evidence",
                "scope": "synthetic fixture",
                "status": "eligible",
                "conditions": {"fixture": True},
                "blocked_reasons": [],
            }
        },
        "source_confirmation": {
            "schema_version": "v2.confirmation-result.1",
            "protocol_sha256": protocol_sha,
            "implementation_sha256": implementation_sha,
            "execution_freeze_sha256": freeze_sha,
            "selection_sha256": selection_sha,
            "confirmation_payload_sha256": "d" * 64,
        },
    }
    analysis_sha = _write_json(analysis_path, analysis)
    manifest = {
        "schema_version": "v2.confirmation-state.1",
        "status": "accepted",
        "protocol_sha256": protocol_sha,
        "implementation_sha256": implementation_sha,
        "execution_freeze_sha256": freeze_sha,
        "selection_sha256": selection_sha,
        "result_file": str(tmp_path / "intentionally-absent-result.json.gz"),
        "result_sha256": "e" * 64,
        "analysis_file": str(analysis_path),
        "analysis_sha256": analysis_sha,
        "oracle_diagnostic_file": str(tmp_path / "intentionally-absent-oracle.json.gz"),
        "oracle_diagnostic_sha256": "f" * 64,
        "n_master_seeds": 40,
        "n_id_datasets": 40,
        "n_ood_datasets": 40,
        "n_clustering_rows": reporting.EXPECTED_COUNTS["clustering_rows"],
        "n_priority_rows": reporting.EXPECTED_COUNTS["priority_rows"],
        "n_stress_rows": reporting.EXPECTED_COUNTS["priority_stress_rows"],
        "n_dispatch_rows": reporting.EXPECTED_COUNTS["predicted_dispatch_rows"],
        "coverage_complete": True,
    }
    _write_json(manifest_path, manifest)
    return {
        "manifest_path": manifest_path,
        "analysis_path": analysis_path,
        "selection_path": selection_path,
        "output_path": output_path,
        "manifest": manifest,
        "analysis": analysis,
        "selection": selection,
    }


def _rewrite_analysis(fixture: dict[str, Any]) -> None:
    digest = _write_json(fixture["analysis_path"], fixture["analysis"])
    fixture["manifest"]["analysis_sha256"] = digest
    _write_json(fixture["manifest_path"], fixture["manifest"])


def _generate(fixture: dict[str, Any], *, overwrite: bool = False) -> dict[str, Any]:
    return reporting.generate_short_results(
        fixture["manifest_path"],
        fixture["analysis_path"],
        fixture["selection_path"],
        fixture["output_path"],
        overwrite=overwrite,
    )


def test_generates_two_compact_tables_from_three_bound_artifacts_only(
    tmp_path: Path,
) -> None:
    fixture = _artifact_fixture(tmp_path)
    metadata = _generate(fixture)
    rendered = fixture["output_path"].read_text(encoding="utf-8")
    assert metadata["oracle_diagnostic_read"] is False
    assert metadata["seed_generation_performed"] is False
    assert metadata["adverse_and_null_results_retained"] is True
    assert metadata["output_sha256"] == hashlib.sha256(
        fixture["output_path"].read_bytes()
    ).hexdigest()
    assert r"\shortresultsconfirmedtrue" in rendered
    assert r"\ShortClusteringResultsTable" in rendered
    assert r"\ShortPriorityDispatchResultsTable" in rendered
    assert "ARI & FD & NR & Review" in rendered
    assert "Legacy" in rendered and "Nearest first" in rendered
    # The deliberately adverse OOD priority result is rendered, not filtered.
    assert r"\ShortEffectCell{-0.10}{-0.18}{-0.02}" in rendered
    assert not Path(fixture["manifest"]["result_file"]).exists()
    assert not Path(fixture["manifest"]["oracle_diagnostic_file"]).exists()


def test_descriptive_range_allows_binary64_round_trip_ulp(
    tmp_path: Path,
) -> None:
    fixture = _artifact_fixture(tmp_path)
    identifier = (
        "stress.id.coordinated_high_confidence_campaign."
        "urgency_only.false_priority_lift"
    )
    fixture["analysis"]["descriptives"]["stress"][identifier] = {
        "n": 40,
        "mean": 0.99,
        "standard_deviation": 0.0,
        "median": 0.9900000000000001,
        "minimum": 0.9900000000000001,
        "maximum": 0.9900000000000001,
    }
    _rewrite_analysis(fixture)
    _generate(fixture)
    assert fixture["output_path"].is_file()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda fixture: fixture["manifest"].update(status="started"),
        lambda fixture: fixture["manifest"].update(n_master_seeds=39),
        lambda fixture: fixture["manifest"].update(coverage_complete=False),
        lambda fixture: fixture["manifest"].update(analysis_file="wrong.json"),
    ],
)
def test_manifest_state_and_coverage_fail_before_output(
    tmp_path: Path,
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    fixture = _artifact_fixture(tmp_path)
    mutate(fixture)
    _write_json(fixture["manifest_path"], fixture["manifest"])
    with pytest.raises(reporting.ConfirmationReportingError):
        _generate(fixture)
    assert not fixture["output_path"].exists()


def test_nonaccepted_manifest_stops_before_bound_artifacts_are_opened(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "manifest.json"
    _write_json(
        manifest,
        {
            "schema_version": "v2.confirmation-state.1",
            "status": "started",
            "coverage_complete": False,
        },
    )
    with pytest.raises(reporting.ConfirmationReportingError, match="not accepted"):
        reporting.generate_short_results(
            manifest,
            tmp_path / "absent-analysis.json",
            tmp_path / "absent-selection.json",
            tmp_path / "output.tex",
        )
    assert not (tmp_path / "output.tex").exists()


def test_analysis_and_selection_sha_tampering_are_rejected(tmp_path: Path) -> None:
    analysis_fixture = _artifact_fixture(tmp_path / "analysis")
    analysis_fixture["analysis_path"].write_bytes(
        analysis_fixture["analysis_path"].read_bytes() + b" "
    )
    with pytest.raises(reporting.ConfirmationReportingError, match="analysis SHA"):
        _generate(analysis_fixture)
    assert not analysis_fixture["output_path"].exists()

    selection_root = tmp_path / "selection"
    selection_root.mkdir()
    selection_fixture = _artifact_fixture(selection_root)
    selection_fixture["selection_path"].write_bytes(
        selection_fixture["selection_path"].read_bytes() + b" "
    )
    with pytest.raises(reporting.ConfirmationReportingError, match="selection SHA"):
        _generate(selection_fixture)
    assert not selection_fixture["output_path"].exists()


def test_incomplete_analysis_or_false_adverse_marker_is_rejected(tmp_path: Path) -> None:
    missing_root = tmp_path / "missing"
    missing_root.mkdir()
    missing = _artifact_fixture(missing_root)
    missing["analysis"]["comparisons"]["priority"].pop(
        "priority.ood.ndcg_at_k.revised_vs_random"
    )
    _rewrite_analysis(missing)
    with pytest.raises(reporting.ConfirmationReportingError, match="keys differ"):
        _generate(missing)
    assert not missing["output_path"].exists()

    marker_root = tmp_path / "marker"
    marker_root.mkdir()
    marker = _artifact_fixture(marker_root)
    marker["analysis"]["comparisons"]["priority"][
        "priority.ood.ndcg_at_k.revised_vs_random"
    ]["adverse_or_null"] = False
    _rewrite_analysis(marker)
    with pytest.raises(reporting.ConfirmationReportingError, match="adverse/null"):
        _generate(marker)
    assert not marker["output_path"].exists()


def test_coverage_and_provenance_binding_are_fail_closed(tmp_path: Path) -> None:
    coverage_root = tmp_path / "coverage"
    coverage_root.mkdir()
    coverage = _artifact_fixture(coverage_root)
    coverage["analysis"]["coverage"]["master_seed_count"] = 39
    _rewrite_analysis(coverage)
    with pytest.raises(reporting.ConfirmationReportingError, match="must equal 40"):
        _generate(coverage)

    provenance_root = tmp_path / "provenance"
    provenance_root.mkdir()
    provenance = _artifact_fixture(provenance_root)
    provenance["analysis"]["source_confirmation"]["selection_sha256"] = "0" * 64
    _rewrite_analysis(provenance)
    with pytest.raises(reporting.ConfirmationReportingError, match="selection_sha256"):
        _generate(provenance)


def test_real_claims_and_dispatch_evidence_are_separate_fail_closed_gates(
    tmp_path: Path,
) -> None:
    real_root = tmp_path / "real"
    real_root.mkdir()
    real = _artifact_fixture(real_root)
    real["analysis"]["claim_gates"]["claim.real_dispatch_benefit"][
        "status"
    ] = "eligible"
    _rewrite_analysis(real)
    with pytest.raises(reporting.ConfirmationReportingError, match="unsupported claim"):
        _generate(real)

    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    evidence = _artifact_fixture(evidence_root)
    evidence["analysis"]["evidence_gates"].pop("predicted_cluster_dispatch")
    _rewrite_analysis(evidence)
    with pytest.raises(reporting.ConfirmationReportingError, match="keys differ"):
        _generate(evidence)


def test_output_creation_is_exclusive_unless_overwrite_is_explicit(tmp_path: Path) -> None:
    fixture = _artifact_fixture(tmp_path)
    first = _generate(fixture)
    with pytest.raises(reporting.ConfirmationReportingError, match="output exists"):
        _generate(fixture)
    second = _generate(fixture, overwrite=True)
    assert second["output_sha256"] == first["output_sha256"]


def test_duplicate_json_keys_and_input_output_alias_are_rejected(tmp_path: Path) -> None:
    fixture = _artifact_fixture(tmp_path)
    fixture["manifest_path"].write_text(
        '{"status":"accepted","status":"started"}', encoding="utf-8"
    )
    with pytest.raises(reporting.ConfirmationReportingError, match="duplicate JSON key"):
        _generate(fixture)
    with pytest.raises(reporting.ConfirmationReportingError, match="output path"):
        reporting.generate_short_results(
            fixture["manifest_path"],
            fixture["analysis_path"],
            fixture["selection_path"],
            fixture["analysis_path"],
            overwrite=True,
        )


@pytest.mark.skipif(shutil.which("xelatex") is None, reason="XeLaTeX unavailable")
def test_generated_tables_compile_in_isolation(tmp_path: Path) -> None:
    fixture = _artifact_fixture(tmp_path)
    _generate(fixture)
    main = tmp_path / "main.tex"
    main.write_text(
        "\\documentclass{article}\n"
        "\\usepackage{booktabs}\n"
        "\\input{short_results.tex}\n"
        "\\begin{document}\n"
        "\\ShortClusteringResultsTable\n"
        "\\ShortPriorityDispatchResultsTable\n"
        "\\end{document}\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            "xelatex",
            "-halt-on-error",
            "-interaction=nonstopmode",
            "-output-directory",
            str(tmp_path),
            str(main),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout[-4000:]
