"""Fail-closed LaTeX reporting for the accepted v2 confirmation.

The renderer consumes exactly three JSON artifacts: the terminal confirmation
manifest, its bound analysis, and the bound calibration selection.  It never
opens the raw confirmation rows, the oracle diagnostic, public data, or any
seed partition.  Rendering happens entirely in memory; an output file is
created only after every provenance, coverage, denominator, and retained-result
check succeeds.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import re
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from demo.v2.analysis import (
    CLUSTERING_ENDPOINTS,
    CLUSTERING_SECONDARY_ENDPOINTS,
    DEFAULT_DISPATCH_POLICIES,
    DEFAULT_METHODS,
    DEFAULT_PRIORITY_POLICIES,
    DEFAULT_REGIMES,
    DISPATCH_ENDPOINTS,
    DISPATCH_GUARDRAILS,
    PRIORITY_SECONDARY_ENDPOINTS,
    STRESS_ENDPOINTS,
    STRESS_SECONDARY_ENDPOINTS,
)
from demo.v2.evaluation import STRESS_FAMILIES_V2


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPOSITORY_ROOT / "revision" / "v2" / "results" / "confirmation_manifest.json"
DEFAULT_ANALYSIS = REPOSITORY_ROOT / "revision" / "v2" / "results" / "confirmation_analysis.json"
DEFAULT_SELECTION = REPOSITORY_ROOT / "revision" / "v2" / "results" / "calibration_selection.json"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "paper" / "short_results.tex"

EXPECTED_COUNTS = {
    "clustering_rows": 4 * 40 * 2,
    "priority_rows": 6 * 40 * 2,
    "priority_stress_rows": 10 * 6 * 40 * 2,
    "predicted_dispatch_rows": 7 * 3 * 40 * 2,
    "schedule_hashes": 7 * 3 * 40 * 2,
}
CONFIGURATION_ID = re.compile(r"^[A-Za-z0-9._-]+$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ConfirmationReportingError(ValueError):
    """Raised when evidence cannot safely be rendered into the manuscript."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ConfirmationReportingError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json(path: Path, label: str) -> tuple[dict[str, Any], str]:
    source = Path(path)
    if not source.is_file():
        raise ConfirmationReportingError(f"{label} file does not exist: {source}")
    raw = source.read_bytes()
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ConfirmationReportingError(f"non-finite JSON constant in {label}: {value}")
            ),
        )
    except UnicodeDecodeError as error:
        raise ConfirmationReportingError(f"{label} is not UTF-8 JSON") from error
    except json.JSONDecodeError as error:
        raise ConfirmationReportingError(f"{label} is invalid JSON") from error
    if not isinstance(payload, dict):
        raise ConfirmationReportingError(f"{label} root must be a JSON object")
    return payload, hashlib.sha256(raw).hexdigest()


def _sha(value: Any, path: str) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise ConfirmationReportingError(f"{path} must be a lowercase SHA-256 digest")
    return value


def _finite(value: Any, path: str) -> float:
    if isinstance(value, bool):
        raise ConfirmationReportingError(f"{path} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ConfirmationReportingError(f"{path} must be numeric") from error
    if not math.isfinite(number):
        raise ConfirmationReportingError(f"{path} must be finite")
    return number


def _positive_integer(value: Any, path: str, *, expected: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ConfirmationReportingError(f"{path} must be a positive integer")
    if expected is not None and value != expected:
        raise ConfirmationReportingError(f"{path} must equal {expected}, got {value}")
    return value


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ConfirmationReportingError(f"{path} must be an object")
    return value


def _exact_keys(mapping: Mapping[str, Any], expected: set[str], path: str) -> None:
    observed = set(mapping)
    missing = sorted(expected.difference(observed))
    extra = sorted(observed.difference(expected))
    if missing or extra:
        raise ConfirmationReportingError(
            f"{path} keys differ from the locked schema: "
            f"missing={missing[:5]}, extra={extra[:5]}"
        )


def _resolve_manifest_label(label: Any, manifest_path: Path, field: str) -> Path:
    if not isinstance(label, str) or not label:
        raise ConfirmationReportingError(f"manifest.{field} must be a non-empty path")
    path = Path(label)
    if not path.is_absolute():
        path = REPOSITORY_ROOT / path
    return path.resolve()


def _validate_terminal_header(manifest: Mapping[str, Any]) -> None:
    """Reject non-terminal state before opening any bound scientific artifact."""

    if manifest.get("schema_version") != "v2.confirmation-state.1":
        raise ConfirmationReportingError("unsupported confirmation manifest schema")
    if manifest.get("status") != "accepted":
        raise ConfirmationReportingError("confirmation state is not accepted")
    if manifest.get("coverage_complete") is not True:
        raise ConfirmationReportingError("confirmation manifest does not assert complete coverage")


def _validate_manifest(
    manifest: Mapping[str, Any],
    *,
    manifest_path: Path,
    analysis_path: Path,
    analysis_sha256: str,
    selection_sha256: str,
) -> None:
    _validate_terminal_header(manifest)
    if _resolve_manifest_label(
        manifest.get("analysis_file"), manifest_path, "analysis_file"
    ) != Path(analysis_path).resolve():
        raise ConfirmationReportingError("manifest analysis_file does not match the supplied file")
    if _sha(manifest.get("analysis_sha256"), "manifest.analysis_sha256") != analysis_sha256:
        raise ConfirmationReportingError("confirmation analysis SHA-256 mismatch")
    if _sha(manifest.get("selection_sha256"), "manifest.selection_sha256") != selection_sha256:
        raise ConfirmationReportingError("calibration selection SHA-256 mismatch")
    # These artifacts are deliberately not opened by the reporting boundary,
    # but an accepted terminal state must bind their names and digests.
    _resolve_manifest_label(manifest.get("result_file"), manifest_path, "result_file")
    _resolve_manifest_label(
        manifest.get("oracle_diagnostic_file"), manifest_path, "oracle_diagnostic_file"
    )
    _sha(manifest.get("result_sha256"), "manifest.result_sha256")
    _sha(manifest.get("oracle_diagnostic_sha256"), "manifest.oracle_diagnostic_sha256")
    for field in (
        "protocol_sha256",
        "implementation_sha256",
        "execution_freeze_sha256",
    ):
        _sha(manifest.get(field), f"manifest.{field}")
    for field in ("n_master_seeds", "n_id_datasets", "n_ood_datasets"):
        _positive_integer(manifest.get(field), f"manifest.{field}", expected=40)
    for field, expected in (
        ("n_clustering_rows", EXPECTED_COUNTS["clustering_rows"]),
        ("n_priority_rows", EXPECTED_COUNTS["priority_rows"]),
        ("n_stress_rows", EXPECTED_COUNTS["priority_stress_rows"]),
        ("n_dispatch_rows", EXPECTED_COUNTS["predicted_dispatch_rows"]),
    ):
        _positive_integer(manifest.get(field), f"manifest.{field}", expected=expected)


def _expected_comparison_contracts() -> dict[str, dict[str, tuple[str, str, str, str, str]]]:
    product, additive = DEFAULT_METHODS[:2]
    revised = "revised"
    clustering: dict[str, tuple[str, str, str, str, str]] = {}
    priority: dict[str, tuple[str, str, str, str, str]] = {}
    dispatch: dict[str, tuple[str, str, str, str, str]] = {}
    stress: dict[str, tuple[str, str, str, str, str]] = {}
    for regime in DEFAULT_REGIMES:
        for endpoint, direction in CLUSTERING_ENDPOINTS:
            identifier = f"clustering.{regime}.{endpoint}.product_vs_additive"
            clustering[identifier] = (product, additive, regime, endpoint, direction)
        for comparator in DEFAULT_PRIORITY_POLICIES:
            if comparator == revised:
                continue
            identifier = f"priority.{regime}.ndcg_at_k.revised_vs_{comparator}"
            priority[identifier] = (revised, comparator, regime, "ndcg_at_k", "higher")
        for comparator in DEFAULT_DISPATCH_POLICIES:
            if comparator == revised:
                continue
            for endpoint, direction in DISPATCH_ENDPOINTS:
                identifier = f"dispatch.{regime}.{endpoint}.revised_vs_{comparator}"
                dispatch[identifier] = (revised, comparator, regime, endpoint, direction)
        for family in STRESS_FAMILIES_V2:
            endpoints = list(STRESS_ENDPOINTS)
            if family == "coordinated_high_confidence_campaign":
                endpoints.append(("false_priority_lift", "lower"))
            for comparator in DEFAULT_PRIORITY_POLICIES:
                if comparator == revised:
                    continue
                for endpoint, direction in endpoints:
                    identifier = (
                        f"stress.{regime}.{family}.{endpoint}."
                        f"revised_vs_{comparator}"
                    )
                    stress[identifier] = (
                        revised,
                        comparator,
                        regime,
                        endpoint,
                        direction,
                    )
    return {
        "clustering": clustering,
        "priority": priority,
        "dispatch": dispatch,
        "stress": stress,
    }


def _expected_descriptive_keys() -> dict[str, set[str]]:
    clustering_endpoints = [endpoint for endpoint, _ in CLUSTERING_ENDPOINTS]
    clustering_endpoints.extend(CLUSTERING_SECONDARY_ENDPOINTS)
    clustering = {
        f"clustering.{regime}.{method}.{endpoint}"
        for regime in DEFAULT_REGIMES
        for method in DEFAULT_METHODS
        for endpoint in clustering_endpoints
    }
    priority_endpoints = ["ndcg_at_k", *PRIORITY_SECONDARY_ENDPOINTS]
    priority = {
        f"priority.{regime}.{policy}.{endpoint}"
        for regime in DEFAULT_REGIMES
        for policy in DEFAULT_PRIORITY_POLICIES
        for endpoint in priority_endpoints
    }
    dispatch_endpoints = [endpoint for endpoint, _ in DISPATCH_ENDPOINTS]
    dispatch_endpoints.extend(DISPATCH_GUARDRAILS)
    dispatch = {
        f"dispatch.{regime}.{policy}.{endpoint}.scenario_mean"
        for regime in DEFAULT_REGIMES
        for policy in DEFAULT_DISPATCH_POLICIES
        for endpoint in dispatch_endpoints
    }
    stress: set[str] = set()
    for regime in DEFAULT_REGIMES:
        for family in STRESS_FAMILIES_V2:
            endpoints = [endpoint for endpoint, _ in STRESS_ENDPOINTS]
            endpoints.extend(endpoint for endpoint, _ in STRESS_SECONDARY_ENDPOINTS)
            if family == "coordinated_high_confidence_campaign":
                endpoints.append("false_priority_lift")
            for policy, endpoint in itertools.product(DEFAULT_PRIORITY_POLICIES, endpoints):
                stress.add(f"stress.{regime}.{family}.{policy}.{endpoint}")
    return {
        "clustering": clustering,
        "priority": priority,
        "dispatch": dispatch,
        "stress": stress,
    }


def _validate_descriptive(identifier: str, row: Any) -> None:
    values = _mapping(row, f"descriptives.{identifier}")
    _positive_integer(values.get("n"), f"descriptives.{identifier}.n", expected=40)
    mean = _finite(values.get("mean"), f"descriptives.{identifier}.mean")
    deviation = _finite(
        values.get("standard_deviation"),
        f"descriptives.{identifier}.standard_deviation",
    )
    med = _finite(values.get("median"), f"descriptives.{identifier}.median")
    minimum = _finite(values.get("minimum"), f"descriptives.{identifier}.minimum")
    maximum = _finite(values.get("maximum"), f"descriptives.{identifier}.maximum")
    # Decimal summaries can differ by one binary-64 ulp after JSON round trips
    # (for example mean=0.99 and min=0.9900000000000001).  Preserve the
    # fail-closed range check while tolerating only machine-scale rounding.
    tolerance = 1e-12 * max(
        1.0,
        abs(mean),
        abs(med),
        abs(minimum),
        abs(maximum),
    )
    if (
        deviation < 0.0
        or med < minimum - tolerance
        or med > maximum + tolerance
        or mean < minimum - tolerance
        or mean > maximum + tolerance
    ):
        raise ConfirmationReportingError(f"invalid descriptive summary: {identifier}")


def _validate_comparison(
    identifier: str,
    row: Any,
    contract: tuple[str, str, str, str, str],
) -> None:
    values = _mapping(row, f"comparisons.{identifier}")
    candidate, comparator, regime, endpoint, direction = contract
    expected_fields = {
        "comparison_id": identifier,
        "candidate": candidate,
        "comparator": comparator,
        "regime": regime,
        "endpoint": endpoint,
        "direction": direction,
        "pairing_key": "master_seed",
    }
    for field, expected in expected_fields.items():
        if values.get(field) != expected:
            raise ConfirmationReportingError(
                f"comparison {identifier} has invalid {field}: {values.get(field)!r}"
            )
    _positive_integer(values.get("n_seed_pairs"), f"{identifier}.n_seed_pairs", expected=40)
    _positive_integer(values.get("pairing_key_count"), f"{identifier}.pairing_key_count", expected=40)
    better = values.get("n_candidate_better")
    worse = values.get("n_comparator_better")
    ties = values.get("n_ties")
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in (better, worse, ties)):
        raise ConfirmationReportingError(f"comparison {identifier} has invalid paired counts")
    if better + worse + ties != 40:
        raise ConfirmationReportingError(f"comparison {identifier} paired counts do not total 40")
    improvement = _finite(values.get("mean_improvement"), f"{identifier}.mean_improvement")
    interval = values.get("paired_confidence_interval")
    if isinstance(interval, (str, bytes)) or not isinstance(interval, Sequence) or len(interval) != 2:
        raise ConfirmationReportingError(f"comparison {identifier} lacks a two-sided CI")
    lower = _finite(interval[0], f"{identifier}.ci.lower")
    upper = _finite(interval[1], f"{identifier}.ci.upper")
    if lower > upper:
        raise ConfirmationReportingError(f"comparison {identifier} has reversed CI bounds")
    for field in ("raw_p_value", "holm_adjusted_p_value"):
        probability = _finite(values.get(field), f"{identifier}.{field}")
        if not 0.0 <= probability <= 1.0:
            raise ConfirmationReportingError(f"comparison {identifier} has invalid {field}")
    adverse = values.get("adverse_or_null")
    if not isinstance(adverse, bool) or adverse != (improvement <= 0.0):
        raise ConfirmationReportingError(
            f"comparison {identifier} has inconsistent adverse/null retention marker"
        )
    denominator = _mapping(values.get("denominator"), f"{identifier}.denominator")
    if (
        denominator.get("unit") != "master_seed"
        or denominator.get("n_master_seeds") != 40
        or denominator.get("regime") != regime
        or denominator.get("endpoint") != endpoint
        or denominator.get("candidate") != candidate
        or denominator.get("comparator") != comparator
    ):
        raise ConfirmationReportingError(f"comparison {identifier} denominator mismatch")


def _validate_analysis(
    analysis: Mapping[str, Any],
    manifest: Mapping[str, Any],
    selection_sha256: str,
) -> None:
    _exact_keys(
        analysis,
        {
            "schema_version",
            "coverage",
            "analysis_contract",
            "descriptives",
            "comparisons",
            "claim_gates",
            "evidence_gates",
            "source_confirmation",
        },
        "analysis",
    )
    if analysis.get("schema_version") != "confirmation-analysis-v2":
        raise ConfirmationReportingError("unsupported confirmation analysis schema")
    coverage = _mapping(analysis.get("coverage"), "analysis.coverage")
    if coverage.get("status") != "exact":
        raise ConfirmationReportingError("analysis coverage is not exact")
    _positive_integer(
        coverage.get("master_seed_count"),
        "analysis.coverage.master_seed_count",
        expected=40,
    )
    counts = _mapping(
        coverage.get("expected_and_observed_counts"),
        "analysis.coverage.expected_and_observed_counts",
    )
    if dict(counts) != EXPECTED_COUNTS:
        raise ConfirmationReportingError("analysis coverage counts differ from the locked 40-seed matrix")
    for field in ("duplicate_keys", "missing_keys", "extra_keys"):
        if coverage.get(field) != 0:
            raise ConfirmationReportingError(f"analysis coverage contains {field}")

    contract = _mapping(analysis.get("analysis_contract"), "analysis.analysis_contract")
    if contract.get("pairing_unit") != "master_seed" or contract.get("bootstrap_resamples") != 10_000:
        raise ConfirmationReportingError("analysis inference contract is not the locked seed-paired 10k bootstrap")
    if contract.get("adverse_and_null_results_retained") is not True:
        raise ConfirmationReportingError("analysis did not retain adverse/null results")

    descriptions = _mapping(analysis.get("descriptives"), "analysis.descriptives")
    comparisons = _mapping(analysis.get("comparisons"), "analysis.comparisons")
    expected_descriptions = _expected_descriptive_keys()
    expected_comparisons = _expected_comparison_contracts()
    _exact_keys(descriptions, set(expected_descriptions), "analysis.descriptives")
    _exact_keys(comparisons, set(expected_comparisons), "analysis.comparisons")
    for section, expected in expected_descriptions.items():
        rows = _mapping(descriptions[section], f"analysis.descriptives.{section}")
        _exact_keys(rows, expected, f"analysis.descriptives.{section}")
        for identifier, row in rows.items():
            _validate_descriptive(identifier, row)
    for section, expected in expected_comparisons.items():
        rows = _mapping(comparisons[section], f"analysis.comparisons.{section}")
        _exact_keys(rows, set(expected), f"analysis.comparisons.{section}")
        for identifier, row in rows.items():
            _validate_comparison(identifier, row, expected[identifier])

    holm = _mapping(contract.get("holm_families"), "analysis.analysis_contract.holm_families")
    _exact_keys(holm, {"synthetic_clustering", "synthetic_priority_dispatch"}, "holm_families")
    clustering_family = holm["synthetic_clustering"]
    priority_family = holm["synthetic_priority_dispatch"]
    if (
        isinstance(clustering_family, (str, bytes))
        or not isinstance(clustering_family, Sequence)
        or len(clustering_family) != len(set(clustering_family))
        or set(clustering_family) != set(expected_comparisons["clustering"])
    ):
        raise ConfirmationReportingError("synthetic clustering Holm family is incomplete")
    expected_priority_family = set().union(
        expected_comparisons["priority"],
        expected_comparisons["dispatch"],
        expected_comparisons["stress"],
    )
    if (
        isinstance(priority_family, (str, bytes))
        or not isinstance(priority_family, Sequence)
        or len(priority_family) != len(set(priority_family))
        or set(priority_family) != expected_priority_family
    ):
        raise ConfirmationReportingError("synthetic priority/dispatch Holm family is incomplete")

    source = _mapping(analysis.get("source_confirmation"), "analysis.source_confirmation")
    if source.get("schema_version") != "v2.confirmation-result.1":
        raise ConfirmationReportingError("analysis source result schema is not recognized")
    for field in (
        "protocol_sha256",
        "implementation_sha256",
        "execution_freeze_sha256",
        "selection_sha256",
    ):
        digest = _sha(source.get(field), f"analysis.source_confirmation.{field}")
        if digest != manifest.get(field):
            raise ConfirmationReportingError(f"analysis source {field} does not match manifest")
    if source.get("selection_sha256") != selection_sha256:
        raise ConfirmationReportingError("analysis source does not bind the supplied selection")
    _sha(
        source.get("confirmation_payload_sha256"),
        "analysis.source_confirmation.confirmation_payload_sha256",
    )

    gates = _mapping(analysis.get("claim_gates"), "analysis.claim_gates")
    expected_gates = {
        "claim.synthetic_controlled_clustering",
        "claim.synthetic_duplicate_invariance",
        "claim.synthetic_priority_alignment",
        "claim.external_priority_sanity",
        "claim.external_consolidation_sanity",
        "claim.external_location_sanity",
        "claim.external_flood_context_descriptive",
        "claim.real_incident_clustering_accuracy",
        "claim.real_dispatch_benefit",
        "claim.vietnamese_transfer",
    }
    _exact_keys(gates, expected_gates, "analysis.claim_gates")
    for identifier, gate in gates.items():
        row = _mapping(gate, f"analysis.claim_gates.{identifier}")
        if row.get("claim_id") != identifier:
            raise ConfirmationReportingError(f"claim-gate id mismatch: {identifier}")
        if row.get("status") not in {"eligible", "blocked"}:
            raise ConfirmationReportingError(f"invalid claim-gate status: {identifier}")
    for identifier in (
        "claim.external_priority_sanity",
        "claim.external_consolidation_sanity",
        "claim.external_location_sanity",
        "claim.external_flood_context_descriptive",
        "claim.real_incident_clustering_accuracy",
        "claim.real_dispatch_benefit",
        "claim.vietnamese_transfer",
    ):
        if _mapping(gates[identifier], identifier).get("status") != "blocked":
            raise ConfirmationReportingError(f"unsupported claim gate opened: {identifier}")
    evidence = _mapping(analysis.get("evidence_gates"), "analysis.evidence_gates")
    _exact_keys(evidence, {"predicted_cluster_dispatch"}, "analysis.evidence_gates")
    dispatch_gate = _mapping(
        evidence["predicted_cluster_dispatch"],
        "analysis.evidence_gates.predicted_cluster_dispatch",
    )
    if (
        dispatch_gate.get("claim_id")
        != "evidence.synthetic_predicted_cluster_dispatch"
        or dispatch_gate.get("status") not in {"eligible", "blocked"}
    ):
        raise ConfirmationReportingError("invalid predicted-cluster dispatch evidence gate")


def _validate_selection(
    selection: Mapping[str, Any], manifest: Mapping[str, Any]
) -> dict[str, str]:
    if selection.get("schema_version") != "v2.calibration-selection.1":
        raise ConfirmationReportingError("unsupported calibration selection schema")
    for field in ("protocol_sha256", "implementation_sha256"):
        digest = _sha(selection.get(field), f"selection.{field}")
        if digest != manifest.get(field):
            raise ConfirmationReportingError(f"selection {field} does not match manifest")
    rows = _mapping(selection.get("selections"), "selection.selections")
    _exact_keys(rows, set(DEFAULT_METHODS), "selection.selections")
    identifiers: dict[str, str] = {}
    for method, raw_row in rows.items():
        row = _mapping(raw_row, f"selection.selections.{method}")
        if row.get("status") != "selected":
            raise ConfirmationReportingError(f"method lacks a frozen selection: {method}")
        configuration = _mapping(
            row.get("configuration"),
            f"selection.selections.{method}.configuration",
        )
        identifier = configuration.get("configuration_id")
        if not isinstance(identifier, str) or CONFIGURATION_ID.fullmatch(identifier) is None:
            raise ConfirmationReportingError(f"invalid selected configuration id: {method}")
        if configuration.get("method_id") != method:
            raise ConfirmationReportingError(f"selected configuration method mismatch: {method}")
        identifiers[method] = identifier
    return identifiers


def _latex_text(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(character, character) for character in value)


def _plain_number(value: float, decimals: int, *, signed: bool = False) -> str:
    if abs(value) < 0.5 * 10 ** (-decimals):
        value = 0.0
    return f"{value:+.{decimals}f}" if signed else f"{value:.{decimals}f}"


def _effect_cell(
    row: Mapping[str, Any],
    decimals: int,
    *,
    scale: float = 1.0,
) -> str:
    effect = scale * _finite(
        row.get("mean_improvement"), "effect.mean_improvement"
    )
    interval = row["paired_confidence_interval"]
    lower = scale * _finite(interval[0], "effect.ci.lower")
    upper = scale * _finite(interval[1], "effect.ci.upper")
    return (
        r"\ShortEffectCell{" + _plain_number(effect, decimals, signed=True) + "}{"
        + _plain_number(lower, decimals, signed=True)
        + "}{"
        + _plain_number(upper, decimals, signed=True)
        + "}"
    )


def _render_clustering_table(analysis: Mapping[str, Any]) -> str:
    descriptions = analysis["descriptives"]["clustering"]
    labels = {
        "method.product_louvain": "Product",
        "method.additive_louvain": "Additive",
        "method.st_dbscan": "ST-DBSCAN",
        "method.hdbscan_geo_time": "HDBSCAN",
    }
    lines = [
        r"\newcommand{\ShortClusteringResultsTable}{%",
        r"\begin{table}[t]",
        r"\centering\small",
        r"\caption{Clustering descriptives over 40 paired master seeds. FD, NR, and Review denote false destinations per 100 reports, noise rejection, and review items per 100 reports; no adverse or null result is suppressed.}",
        r"\label{tab:short-clustering-results}",
        r"\begin{tabular}{llrrrr}",
        r"\toprule",
        r"Regime & Method & ARI & FD & NR & Review \\",
        r"\midrule",
    ]
    for regime in DEFAULT_REGIMES:
        for method in DEFAULT_METHODS:
            ari = descriptions[f"clustering.{regime}.{method}.ari_linked"]["mean"]
            false_destinations = descriptions[
                f"clustering.{regime}.{method}.false_destinations_per_100_reports"
            ]["mean"]
            noise_rejection = descriptions[
                f"clustering.{regime}.{method}.noise_rejection"
            ]["mean"]
            review_burden = descriptions[
                f"clustering.{regime}.{method}.review_items_per_100_reports"
            ]["mean"]
            lines.append(
                f"{regime.upper()} & {labels[method]} & "
                f"{_plain_number(float(ari), 2)} & "
                f"{_plain_number(float(false_destinations), 2)} & "
                f"{_plain_number(float(noise_rejection), 2)} & "
                f"{_plain_number(float(review_burden), 2)} \\\\"
            )
        if regime != DEFAULT_REGIMES[-1]:
            lines.append(r"\midrule")
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}%",
            r"}",
        ]
    )
    return "\n".join(lines)


def _render_headline_table(analysis: Mapping[str, Any]) -> str:
    priority = analysis["comparisons"]["priority"]
    dispatch = analysis["comparisons"]["dispatch"]
    labels = {
        "legacy": "Legacy",
        "urgency_only": "Urgency only",
        "population_only": "Population only",
        "simple_linear": "Simple linear",
        "random": "Random",
        "nearest_first": "Nearest first",
    }
    priority_comparators = tuple(
        policy for policy in DEFAULT_PRIORITY_POLICIES if policy != "revised"
    )
    dispatch_comparators = tuple(
        policy for policy in DEFAULT_DISPATCH_POLICIES if policy != "revised"
    )
    lines = [
        r"\newcommand{\ShortPriorityDispatchResultsTable}{%",
        r"\begin{table}[t]",
        r"\centering\footnotesize",
        r"\setlength{\tabcolsep}{2pt}",
        r"\caption{Paired headline effects with 95\% bootstrap confidence intervals. Every $\Delta$ is improvement-oriented, so positive favors the revised heuristic; adverse and null effects remain visible. Dispatch values first average the three locked scenarios within each master seed; H is harm and D is deadline-miss percentage points.}",
        r"\label{tab:short-priority-dispatch-results}",
        r"\begin{tabular}{@{}llcc@{}}",
        r"\toprule",
        r"\multicolumn{4}{l}{\textit{Panel A: Priority alignment (revised minus baseline)}} \\",
        r"\multicolumn{2}{l}{Baseline} & ID $\Delta$NDCG@5 & OOD $\Delta$NDCG@5 \\",
        r"\midrule",
    ]
    for comparator in priority_comparators:
        id_row = priority[f"priority.id.ndcg_at_k.revised_vs_{comparator}"]
        ood_row = priority[f"priority.ood.ndcg_at_k.revised_vs_{comparator}"]
        lines.append(
            f"\\multicolumn{{2}}{{l}}{{{labels[comparator]}}} & "
            f"{_effect_cell(id_row, 2)} & {_effect_cell(ood_row, 2)} \\\\"
        )
    lines.extend(
        [
            r"\midrule",
            r"\multicolumn{4}{l}{\textit{Panel B: Predicted-cluster dispatch (revised versus policy)}} \\",
            r"Policy & Endp. & ID $\Delta$ & OOD $\Delta$ \\",
            r"\midrule",
        ]
    )
    for comparator in dispatch_comparators:
        for index, (endpoint, endpoint_label, scale) in enumerate(
            (("total_harm", "H", 1.0), ("deadline_miss_rate", "D", 100.0))
        ):
            cells = [
                _effect_cell(
                    dispatch[
                        f"dispatch.{regime}.{endpoint}.revised_vs_{comparator}"
                    ],
                    2,
                    scale=scale,
                )
                for regime in DEFAULT_REGIMES
            ]
            policy_label = labels[comparator] if index == 0 else ""
            lines.append(
                f"{policy_label} & {endpoint_label} & "
                + " & ".join(cells)
                + r" \\"
            )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}%",
            r"}",
        ]
    )
    return "\n".join(lines)


def _render_short_results(
    manifest: Mapping[str, Any],
    analysis: Mapping[str, Any],
    *,
    selected_configuration_ids: Mapping[str, str],
) -> str:
    """Render validated evidence; callers must run the file-level validator."""

    gates = analysis["claim_gates"]
    evidence = analysis["evidence_gates"]
    macros = {
        "ShortClusteringClaimGate": gates[
            "claim.synthetic_controlled_clustering"
        ]["status"],
        "ShortPriorityClaimGate": gates["claim.synthetic_priority_alignment"][
            "status"
        ],
        "ShortDuplicateClaimGate": gates[
            "claim.synthetic_duplicate_invariance"
        ]["status"],
        "ShortDispatchEvidenceGate": evidence["predicted_cluster_dispatch"][
            "status"
        ],
        "ShortProductConfiguration": selected_configuration_ids[
            "method.product_louvain"
        ],
        "ShortAdditiveConfiguration": selected_configuration_ids[
            "method.additive_louvain"
        ],
        "ShortSTDBSCANConfiguration": selected_configuration_ids[
            "method.st_dbscan"
        ],
        "ShortHDBSCANConfiguration": selected_configuration_ids[
            "method.hdbscan_geo_time"
        ],
    }
    lines = [
        "% GENERATED FILE: accepted confirmation evidence only. DO NOT EDIT.",
        "% Raw confirmation rows and oracle diagnostics are outside this renderer.",
        r"\newif\ifshortresultsconfirmed",
        r"\shortresultsconfirmedtrue",
        r"\newcommand{\ShortUnavailable}{\textsc{Confirmed results available}}",
        r"\newcommand{\ShortResult}[1]{\PackageError{short_results}{Unknown result selector `#1'}{Use only generated named result macros or tables.}}",
        r"\newcommand{\ShortAdverseNullRetained}{true}",
        (
            r"\newcommand{\ShortConfirmationAnalysisSHA}{\texttt{"
            + str(manifest["analysis_sha256"])
            + "}}"
        ),
        (
            r"\newcommand{\ShortConfirmationResultSHA}{\texttt{"
            + str(manifest["result_sha256"])
            + "}}"
        ),
        (
            r"\newcommand{\ShortConfirmationPayloadSHA}{\texttt{"
            + str(analysis["source_confirmation"]["confirmation_payload_sha256"])
            + "}}"
        ),
        (
            r"\newcommand{\ShortCalibrationSelectionSHA}{\texttt{"
            + str(manifest["selection_sha256"])
            + "}}"
        ),
        (
            r"\newcommand{\ShortProtocolSHA}{\texttt{"
            + str(manifest["protocol_sha256"])
            + "}}"
        ),
        r"\newcommand{\ShortEffectCell}[3]{$#1\,[#2,#3]$}",
    ]
    for name, value in macros.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{_latex_text(str(value))}}}")
    lines.extend(
        [
            "",
            _render_clustering_table(analysis),
            "",
            _render_headline_table(analysis),
            "",
        ]
    )
    return "\n".join(lines)


def generate_short_results(
    manifest_path: Path,
    analysis_path: Path,
    selection_path: Path,
    output_path: Path,
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Validate three bound artifacts and atomically create the LaTeX include."""

    manifest_path = Path(manifest_path)
    analysis_path = Path(analysis_path)
    selection_path = Path(selection_path)
    output_path = Path(output_path)
    inputs = {path.resolve() for path in (manifest_path, analysis_path, selection_path)}
    if output_path.resolve() in inputs:
        raise ConfirmationReportingError("output path cannot overwrite an input artifact")
    manifest, manifest_sha256 = _read_json(manifest_path, "confirmation manifest")
    _validate_terminal_header(manifest)
    analysis, analysis_sha256 = _read_json(analysis_path, "confirmation analysis")
    selection, selection_sha256 = _read_json(selection_path, "calibration selection")
    _validate_manifest(
        manifest,
        manifest_path=manifest_path,
        analysis_path=analysis_path,
        analysis_sha256=analysis_sha256,
        selection_sha256=selection_sha256,
    )
    selected = _validate_selection(selection, manifest)
    _validate_analysis(analysis, manifest, selection_sha256)
    rendered = _render_short_results(
        manifest,
        analysis,
        selected_configuration_ids=selected,
    )
    encoded = rendered.encode("utf-8")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.", dir=output_path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        if overwrite:
            os.replace(temporary, output_path)
        else:
            try:
                os.link(temporary, output_path)
            except FileExistsError as error:
                raise ConfirmationReportingError(
                    f"output exists; pass overwrite=True explicitly: {output_path}"
                ) from error
            temporary.unlink()
    finally:
        if temporary.exists():
            temporary.unlink()
    return {
        "schema_version": "v2.short-results-render.1",
        "output_file": str(output_path.resolve()),
        "output_sha256": hashlib.sha256(encoded).hexdigest(),
        "manifest_sha256": manifest_sha256,
        "protocol_sha256": manifest["protocol_sha256"],
        "result_sha256": manifest["result_sha256"],
        "confirmation_payload_sha256": analysis["source_confirmation"][
            "confirmation_payload_sha256"
        ],
        "analysis_sha256": analysis_sha256,
        "selection_sha256": selection_sha256,
        "adverse_and_null_results_retained": True,
        "oracle_diagnostic_read": False,
        "seed_generation_performed": False,
    }


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render accepted v2 confirmation results into a LaTeX include."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--analysis", type=Path, default=DEFAULT_ANALYSIS)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="explicitly replace an existing output (for example the pre-confirmation stub)",
    )
    arguments = parser.parse_args(argv)
    metadata = generate_short_results(
        arguments.manifest,
        arguments.analysis,
        arguments.selection,
        arguments.output,
        overwrite=arguments.overwrite,
    )
    print(json.dumps(metadata, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through the public API
    raise SystemExit(_main())


__all__ = [
    "ConfirmationReportingError",
    "DEFAULT_ANALYSIS",
    "DEFAULT_MANIFEST",
    "DEFAULT_OUTPUT",
    "DEFAULT_SELECTION",
    "EXPECTED_COUNTS",
    "generate_short_results",
]
