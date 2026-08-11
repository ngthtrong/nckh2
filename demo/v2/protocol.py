"""Validate, expand, hash, and freeze the version-2 protocol bundle.

Only files explicitly listed by ``revision/v2/bundle.json`` are included in
the protocol digest.  In particular, result files are never discovered or
hashed.  The module performs no network access and never invents source-data
checksums.
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
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROTOCOL_DIR = REPOSITORY_ROOT / "revision" / "v2"
BUNDLE_NAME = "bundle.json"
SEED_NAME = "seed_partitions.json"
METHOD_NAME = "method_registry.json"
ANALYSIS_NAME = "analysis_contract.json"
SOURCE_NAME = "public_sources.json"
PUBLIC_ANCHOR_NAME = "public_anchor.json"
LOCK_NAME = "protocol-lock.json"

CANONICAL_ID_PATTERN = r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$"
CANONICAL_ID_RE = re.compile(CANONICAL_ID_PATTERN)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

EXPECTED_SPLITS = {
    "development": tuple(range(4100, 4120)),
    "calibration": tuple(range(4200, 4220)),
    "confirmation": tuple(range(4400, 4440)),
}
EXPECTED_RETIRED_CONFIRMATION = tuple(range(4300, 4340))
EXPECTED_GRID_COUNTS = {
    "comparison.product_vs_additive": 128,
    "grid.st_dbscan": 64,
    "grid.hdbscan": 96,
}
EXPECTED_COMPARISON_AXES = {
    "sigma_geo_m": [500, 700, 900, 1200],
    "tau_t_min": [30, 60],
    "threshold_quantile": [0.85, 0.90, 0.95, 0.98],
    "k": [8, 16],
    "resolution": [0.8, 1.2],
}
EXPECTED_COMPARISON_FIXED = {
    "tau_F": 0.25,
    "tau_E": 0.35,
    "alpha": 0.5,
    "beta": 0.5,
    "gamma": 0.5,
    "candidate_pool_min_neighbors": 64,
    "candidate_pool_k_multiplier": 4,
    "candidate_pool_rule": "spatial_knn_with_complete_boundary_tie_query_then_canonical_truncation_and_undirected_union",
    "threshold_population": "shared_geographically_pregated_candidate_pairs",
}
EXPECTED_ST_DBSCAN_AXES = {
    "spatial_eps_m": [250, 500, 750, 1000],
    "temporal_eps_min": [15, 30, 60, 120],
    "min_samples": [3, 5, 8, 12],
}
EXPECTED_HDBSCAN_AXES = {
    "min_cluster_size": [3, 5, 10, 20],
    "min_samples": [1, 3, 5, 10],
    "spatial_scale_m": [250, 500, 1000],
    "temporal_scale_min": [30, 60],
}
MANDATORY_FROZEN_MEMBERS = {
    SEED_NAME,
    METHOD_NAME,
    ANALYSIS_NAME,
    PUBLIC_ANCHOR_NAME,
    SOURCE_NAME,
}
REQUIRED_SOURCE_IDS = {
    "source.trec_is",
    "source.crisisfacts",
    "source.idrisi_re",
    "source.noaa_storm_events",
    "source.noaa_flash",
    "source.uk_water_rescue",
}
REQUIRED_PROVIDERS = {
    "provider.trec",
    "provider.crisisfacts",
    "provider.idrisi",
    "provider.noaa",
    "provider.uk_mhclg",
}
AUDITED_PUBLIC_SOURCE_IDS = {
    "source.idrisi_re",
    "source.noaa_storm_events",
    "source.uk_water_rescue",
}
BLOCKED_PUBLIC_SOURCE_IDS = {
    "source.crisisfacts",
    "source.trec_is",
}


class ProtocolV2Error(ValueError):
    """Raised when a v2 protocol invariant is violated."""


@dataclass(frozen=True)
class ExpandedConfiguration:
    """One deterministic grid member.

    ``parameters`` excludes bookkeeping identifiers.  For a paired comparison,
    :meth:`execution_payload` adds exactly one field, ``operator``.  This makes
    the controlled product/additive invariant directly testable.
    """

    configuration_id: str
    method_id: str
    parameters: Mapping[str, Any]
    pair_id: str | None = None
    operator: str | None = None

    def execution_payload(self) -> dict[str, Any]:
        payload = dict(self.parameters)
        if self.operator is not None:
            payload["operator"] = self.operator
        return payload


@dataclass(frozen=True)
class ProtocolV2:
    """Validated protocol summary and deterministic grid expansions."""

    development_seeds: tuple[int, ...]
    calibration_seeds: tuple[int, ...]
    confirmation_seeds: tuple[int, ...]
    retired_confirmation_seeds: tuple[int, ...]
    paired_configurations: tuple[ExpandedConfiguration, ...]
    independent_configurations: Mapping[str, tuple[ExpandedConfiguration, ...]]
    endpoint_ids: tuple[str, ...]
    holm_family_ids: tuple[str, ...]
    claim_gate_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    source_gate_ids: tuple[str, ...]
    member_sha256: Mapping[str, str]
    bundle_sha256: str


def _load_json(path: Path) -> Mapping[str, Any]:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        parsed: dict[str, Any] = {}
        for key, value in pairs:
            if key in parsed:
                raise ProtocolV2Error(f"duplicate JSON key {key!r} in {path}")
            parsed[key] = value
        return parsed

    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except FileNotFoundError as exc:
        raise ProtocolV2Error(f"missing protocol file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProtocolV2Error(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProtocolV2Error(f"protocol file must contain an object: {path}")
    return value


def _require_schema(value: Mapping[str, Any], expected: str, label: str) -> None:
    if value.get("schema_version") != expected:
        raise ProtocolV2Error(
            f"{label} schema must be {expected!r}; got {value.get('schema_version')!r}"
        )


def _canonical_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not CANONICAL_ID_RE.fullmatch(value):
        raise ProtocolV2Error(f"{label} is not a canonical id: {value!r}")
    return value


def _unique_ids(items: Sequence[Any], label: str) -> tuple[str, ...]:
    identifiers: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ProtocolV2Error(f"{label}[{index}] must be an object")
        identifiers.append(_canonical_id(item.get("id"), f"{label}[{index}].id"))
    if len(identifiers) != len(set(identifiers)):
        raise ProtocolV2Error(f"{label} contains duplicate ids")
    return tuple(identifiers)


def _iso_date(value: Any, label: str) -> date:
    if not isinstance(value, str):
        raise ProtocolV2Error(f"{label} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ProtocolV2Error(f"{label} must be an ISO date: {value!r}") from exc


def _json_scalar(value: Any, label: str) -> None:
    if value is None or isinstance(value, str):
        return
    if isinstance(value, bool):
        raise ProtocolV2Error(f"{label} may not use booleans as grid values")
    if isinstance(value, int):
        return
    if isinstance(value, float) and math.isfinite(value):
        return
    raise ProtocolV2Error(f"{label} must be a finite JSON scalar")


def _validate_seeds(manifest: Mapping[str, Any]) -> dict[str, tuple[int, ...]]:
    _require_schema(manifest, "v2.seed-partitions.1", "seed partition")
    _canonical_id(manifest.get("id"), "seed partition id")
    _iso_date(manifest.get("frozen_on"), "seed partition frozen_on")
    splits = manifest.get("splits")
    counts = manifest.get("expected_counts")
    if not isinstance(splits, dict) or not isinstance(counts, dict):
        raise ProtocolV2Error("seed partition requires splits and expected_counts")

    parsed: dict[str, tuple[int, ...]] = {}
    for name, expected in EXPECTED_SPLITS.items():
        raw = splits.get(name)
        if not isinstance(raw, list) or any(
            isinstance(seed, bool) or not isinstance(seed, int) for seed in raw
        ):
            raise ProtocolV2Error(f"split {name!r} must contain integer seeds")
        values = tuple(raw)
        if values != expected:
            raise ProtocolV2Error(
                f"split {name!r} must equal {expected[0]}-{expected[-1]}"
            )
        if counts.get(name) != len(values):
            raise ProtocolV2Error(f"split {name!r} expected count is inconsistent")
        parsed[name] = values

    if set(splits) != set(EXPECTED_SPLITS):
        raise ProtocolV2Error("seed partition has an unexpected split")
    if manifest.get("disjoint_required") is not True:
        raise ProtocolV2Error("seed splits must explicitly require disjointness")
    all_seeds = tuple(itertools.chain.from_iterable(parsed.values()))
    if len(all_seeds) != len(set(all_seeds)):
        raise ProtocolV2Error("development, calibration, and confirmation seeds overlap")

    retired = manifest.get("retired_confirmation")
    if not isinstance(retired, dict) or set(retired) != {
        "seeds",
        "expected_count",
        "reason",
        "eligible_for_selection_or_confirmation",
    }:
        raise ProtocolV2Error("retired_confirmation record is incomplete")
    retired_raw = retired.get("seeds")
    if not isinstance(retired_raw, list) or any(
        isinstance(seed, bool) or not isinstance(seed, int) for seed in retired_raw
    ):
        raise ProtocolV2Error("retired_confirmation seeds must be integers")
    retired_values = tuple(retired_raw)
    if retired_values != EXPECTED_RETIRED_CONFIRMATION:
        raise ProtocolV2Error("retired_confirmation must equal 4300-4339")
    if (
        retired.get("expected_count") != 40
        or retired.get("reason") != "opened_during_pre_freeze_code_audit"
        or retired.get("eligible_for_selection_or_confirmation") is not False
    ):
        raise ProtocolV2Error("retired_confirmation status/reason is not locked")
    if not set(retired_values).isdisjoint(all_seeds):
        raise ProtocolV2Error("retired confirmation seeds overlap an active split")
    parsed["retired_confirmation"] = retired_values

    release = manifest.get("release_policy")
    if (
        not isinstance(release, dict)
        or release.get("retired_confirmation")
        != "permanently excluded from selection and confirmation"
        or release.get("confirmation_feedback_to_selection") != "forbidden"
        or release.get("intermediate_confirmation_results")
        != "not released to selection code"
    ):
        raise ProtocolV2Error("confirmation release policy is incomplete")
    return parsed


def _expand_axes(
    axis_order: Any, axes: Any, label: str
) -> tuple[dict[str, Any], ...]:
    if (
        not isinstance(axis_order, list)
        or not axis_order
        or any(not isinstance(axis, str) or not axis for axis in axis_order)
        or len(axis_order) != len(set(axis_order))
    ):
        raise ProtocolV2Error(f"{label}.axis_order must contain unique names")
    if not isinstance(axes, dict) or set(axis_order) != set(axes):
        raise ProtocolV2Error(f"{label}.axes must match axis_order exactly")
    values_by_axis: list[list[Any]] = []
    for axis in axis_order:
        values = axes[axis]
        if not isinstance(values, list) or not values:
            raise ProtocolV2Error(f"{label}.axes.{axis} must be non-empty")
        for index, value in enumerate(values):
            _json_scalar(value, f"{label}.axes.{axis}[{index}]")
        canonical_values = [
            json.dumps(value, sort_keys=True, separators=(",", ":"))
            for value in values
        ]
        if len(canonical_values) != len(set(canonical_values)):
            raise ProtocolV2Error(f"{label}.axes.{axis} contains duplicates")
        values_by_axis.append(values)
    return tuple(
        dict(zip(axis_order, combination, strict=True))
        for combination in itertools.product(*values_by_axis)
    )


def _format_identifier(template: Any, label: str, **values: Any) -> str:
    if not isinstance(template, str) or not template:
        raise ProtocolV2Error(f"{label} must be a non-empty format string")
    try:
        identifier = template.format(**values)
    except (KeyError, ValueError) as exc:
        raise ProtocolV2Error(f"invalid identifier template {label}: {template!r}") from exc
    return _canonical_id(identifier, label)


def _validate_method_registry(
    registry: Mapping[str, Any],
) -> tuple[
    tuple[ExpandedConfiguration, ...],
    dict[str, tuple[ExpandedConfiguration, ...]],
    set[str],
    set[str],
]:
    _require_schema(registry, "v2.method-registry.1", "method registry")
    _canonical_id(registry.get("id"), "method registry id")
    if registry.get("canonical_id_pattern") != CANONICAL_ID_PATTERN:
        raise ProtocolV2Error("method registry canonical-id pattern is not locked")
    if registry.get("configuration_index_origin") != 0:
        raise ProtocolV2Error("configuration indices must start at zero")

    comparisons = registry.get("paired_comparisons")
    grids = registry.get("independent_grids")
    if not isinstance(comparisons, list) or not isinstance(grids, list):
        raise ProtocolV2Error("method registry requires comparison and grid lists")
    comparison_ids = set(_unique_ids(comparisons, "paired_comparisons"))
    grid_ids = set(_unique_ids(grids, "independent_grids"))
    if comparison_ids != {"comparison.product_vs_additive"}:
        raise ProtocolV2Error("exactly one controlled product/additive comparison is required")
    if grid_ids != {"grid.st_dbscan", "grid.hdbscan"}:
        raise ProtocolV2Error("ST-DBSCAN and HDBSCAN grids are required")

    comparison = comparisons[0]
    if (
        comparison.get("role")
        != "matched_search_space_for_symmetric_independent_selection"
        or comparison.get("confirmation_estimand")
        != "independently_selected_product_pipeline_vs_independently_selected_additive_pipeline"
    ):
        raise ProtocolV2Error(
            "product/additive confirmation must be scoped to independent symmetric selection"
        )
    if comparison.get("operator_is_only_differing_execution_field") is not True:
        raise ProtocolV2Error("paired comparison must differ only by operator")
    operators = comparison.get("operators")
    if not isinstance(operators, list) or len(operators) != 2:
        raise ProtocolV2Error("paired comparison requires exactly two operators")
    method_ids: set[str] = set()
    operator_values: set[str] = set()
    method_slugs: set[str] = set()
    for index, operator in enumerate(operators):
        if not isinstance(operator, dict):
            raise ProtocolV2Error(f"operator {index} must be an object")
        method_ids.add(_canonical_id(operator.get("method_id"), "operator method_id"))
        method_slugs.add(_canonical_id(operator.get("method_slug"), "operator method_slug"))
        value = operator.get("operator")
        if value not in {"product", "additive"}:
            raise ProtocolV2Error(f"unknown composition operator: {value!r}")
        operator_values.add(value)
    if method_ids != {"method.product_louvain", "method.additive_louvain"}:
        raise ProtocolV2Error("paired method ids are not canonical product/additive ids")
    if operator_values != {"product", "additive"} or len(method_slugs) != 2:
        raise ProtocolV2Error("paired operator definitions are duplicated")

    fixed = comparison.get("shared_fixed_parameters")
    if not isinstance(fixed, dict) or not fixed:
        raise ProtocolV2Error("paired comparison requires shared fixed parameters")
    if comparison.get("axis_order") != list(EXPECTED_COMPARISON_AXES):
        raise ProtocolV2Error("product/additive axis order does not match the v2 plan")
    if comparison.get("axes") != EXPECTED_COMPARISON_AXES:
        raise ProtocolV2Error("product/additive axes do not match the exact 128-pair grid")
    if any(fixed.get(key) != value for key, value in EXPECTED_COMPARISON_FIXED.items()):
        raise ProtocolV2Error("product/additive fixed tau/weight parameters are not locked")
    nuisance_rows = _expand_axes(
        comparison.get("axis_order"),
        comparison.get("axes"),
        "comparison.product_vs_additive",
    )
    expected_count = EXPECTED_GRID_COUNTS["comparison.product_vs_additive"]
    if (
        comparison.get("expected_pair_count") != expected_count
        or len(nuisance_rows) != expected_count
    ):
        raise ProtocolV2Error("product/additive nuisance grid must contain exactly 128 pairs")

    paired: list[ExpandedConfiguration] = []
    pair_ids: set[str] = set()
    configuration_ids: set[str] = set()
    for index, nuisance in enumerate(nuisance_rows):
        pair_id = _format_identifier(
            comparison.get("pair_id_template"),
            "paired nuisance id",
            index=index,
        )
        if pair_id in pair_ids:
            raise ProtocolV2Error(f"duplicate pair id: {pair_id}")
        pair_ids.add(pair_id)
        pair_members: list[ExpandedConfiguration] = []
        parameters = {**fixed, **nuisance}
        for operator in operators:
            configuration_id = _format_identifier(
                comparison.get("configuration_id_template"),
                "paired configuration id",
                index=index,
                method_slug=operator["method_slug"],
            )
            if configuration_id in configuration_ids:
                raise ProtocolV2Error(f"duplicate configuration id: {configuration_id}")
            configuration_ids.add(configuration_id)
            member = ExpandedConfiguration(
                configuration_id=configuration_id,
                method_id=operator["method_id"],
                pair_id=pair_id,
                operator=operator["operator"],
                parameters=dict(parameters),
            )
            pair_members.append(member)
            paired.append(member)
        payloads = [member.execution_payload() for member in pair_members]
        keys = set(payloads[0]) | set(payloads[1])
        differing = {key for key in keys if payloads[0].get(key) != payloads[1].get(key)}
        if differing != {"operator"}:
            raise ProtocolV2Error(
                f"pair {pair_id} differs in fields other than operator: {sorted(differing)}"
            )

    independent: dict[str, tuple[ExpandedConfiguration, ...]] = {}
    for grid in grids:
        grid_id = grid["id"]
        method_id = _canonical_id(grid.get("method_id"), f"{grid_id}.method_id")
        fixed_parameters = grid.get("fixed_parameters")
        if not isinstance(fixed_parameters, dict) or not fixed_parameters:
            raise ProtocolV2Error(f"{grid_id} requires fixed parameters")
        expected_axes = (
            EXPECTED_ST_DBSCAN_AXES
            if grid_id == "grid.st_dbscan"
            else EXPECTED_HDBSCAN_AXES
        )
        if grid.get("axis_order") != list(expected_axes) or grid.get("axes") != expected_axes:
            raise ProtocolV2Error(f"{grid_id} axes do not match the locked v2 grid")
        if grid_id == "grid.hdbscan" and fixed_parameters.get("feature_view") != "observable_geo_time":
            raise ProtocolV2Error("HDBSCAN feature view must exclude context")
        rows = _expand_axes(grid.get("axis_order"), grid.get("axes"), grid_id)
        expected = EXPECTED_GRID_COUNTS[grid_id]
        if (
            grid.get("expected_configuration_count") != expected
            or len(rows) != expected
        ):
            raise ProtocolV2Error(f"{grid_id} must contain exactly {expected} configurations")
        members: list[ExpandedConfiguration] = []
        ids: set[str] = set()
        for index, parameters in enumerate(rows):
            configuration_id = _format_identifier(
                grid.get("configuration_id_template"),
                f"{grid_id} configuration id",
                index=index,
            )
            if configuration_id in ids or configuration_id in configuration_ids:
                raise ProtocolV2Error(f"duplicate configuration id: {configuration_id}")
            ids.add(configuration_id)
            configuration_ids.add(configuration_id)
            members.append(
                ExpandedConfiguration(
                    configuration_id=configuration_id,
                    method_id=method_id,
                    parameters={**fixed_parameters, **parameters},
                )
            )
        independent[grid_id] = tuple(members)
        method_ids.add(method_id)

    budget = registry.get("budget_policy")
    if not isinstance(budget, dict) or any(
        budget.get(key) != expected
        for key, expected in {
            "paired_comparison_pairs": 128,
            "paired_comparison_total_executions": 256,
            "st_dbscan_configurations": 64,
            "hdbscan_configurations": 96,
        }.items()
    ):
        raise ProtocolV2Error("method-registry budget policy is inconsistent")
    if (
        budget.get("complete_grid_required") is not True
        or budget.get("early_stopping") != "forbidden"
        or budget.get("post_hoc_grid_expansion") != "forbidden"
    ):
        raise ProtocolV2Error("complete-grid and stopping rules are not locked")
    expected_method_ids = {
        "method.product_louvain",
        "method.additive_louvain",
        "method.st_dbscan",
        "method.hdbscan_geo_time",
    }
    if method_ids != expected_method_ids:
        raise ProtocolV2Error("method registry does not expose the four locked method ids")
    return tuple(paired), independent, method_ids, method_ids


def _validate_sources(manifest: Mapping[str, Any]) -> tuple[set[str], set[str]]:
    _require_schema(manifest, "v2.public-source-manifest.1", "public source manifest")
    _canonical_id(manifest.get("id"), "public source manifest id")
    snapshot_date = _iso_date(
        manifest.get("metadata_snapshot_date"), "metadata_snapshot_date"
    )
    policy = manifest.get("audit_policy")
    if (
        not isinstance(policy, dict)
        or policy.get("raw_data_downloads_performed_during_manifest_creation") is not False
        or policy.get("restricted_data_downloads_performed") is not False
    ):
        raise ProtocolV2Error("source audit must declare that no data were downloaded")
    checksum_rule = policy.get("checksum_rule")
    if not isinstance(checksum_rule, str) or "null" not in checksum_rule or "bytes" not in checksum_rule:
        raise ProtocolV2Error("source checksum rule must forbid invented digests")

    coverage_fields = manifest.get("required_coverage_fields")
    required_fields = {
        "event",
        "incident",
        "location",
        "time",
        "need",
        "urgency",
        "outcome",
        "language",
        "flood_relevance",
        "vietnamese",
    }
    if not isinstance(coverage_fields, list) or set(coverage_fields) != required_fields:
        raise ProtocolV2Error("public source coverage fields are incomplete")

    sources = manifest.get("sources")
    if not isinstance(sources, list):
        raise ProtocolV2Error("public source manifest requires a source list")
    source_ids = set(_unique_ids(sources, "sources"))
    if source_ids != REQUIRED_SOURCE_IDS:
        raise ProtocolV2Error("public source manifest does not contain the locked shortlist")
    providers: set[str] = set()
    gate_ids: set[str] = set()
    for source in sources:
        source_id = source["id"]
        providers.add(_canonical_id(source.get("provider_id"), f"{source_id}.provider_id"))
        if not isinstance(source.get("name"), str) or not source["name"].strip():
            raise ProtocolV2Error(f"{source_id} requires a name")
        urls = source.get("official_urls")
        if not isinstance(urls, dict) or not urls:
            raise ProtocolV2Error(f"{source_id} requires official URLs")
        for purpose, url in urls.items():
            if not isinstance(purpose, str) or not isinstance(url, str) or not url.startswith("https://"):
                raise ProtocolV2Error(f"{source_id} has a non-HTTPS official URL")

        license_record = source.get("license")
        if not isinstance(license_record, dict):
            raise ProtocolV2Error(f"{source_id} requires a license record")
        if not isinstance(license_record.get("status"), str) or not license_record["status"]:
            raise ProtocolV2Error(f"{source_id} license status is missing")
        identifier = license_record.get("identifier")
        if identifier is not None and (not isinstance(identifier, str) or not identifier):
            raise ProtocolV2Error(f"{source_id} license identifier is invalid")
        evidence_url = license_record.get("evidence_url")
        if not isinstance(evidence_url, str) or not evidence_url.startswith("https://"):
            raise ProtocolV2Error(f"{source_id} license evidence URL is invalid")

        metadata = source.get("metadata_snapshot")
        if not isinstance(metadata, dict):
            raise ProtocolV2Error(f"{source_id} requires metadata_snapshot")
        checked_on = _iso_date(metadata.get("checked_on"), f"{source_id}.checked_on")
        if checked_on > snapshot_date:
            raise ProtocolV2Error(f"{source_id} was checked after manifest snapshot date")
        modified = metadata.get("upstream_last_modified")
        if modified is not None:
            _iso_date(modified, f"{source_id}.upstream_last_modified")

        artifact = source.get("local_artifact")
        if not isinstance(artifact, dict) or not isinstance(artifact.get("downloaded"), bool):
            raise ProtocolV2Error(f"{source_id} requires a local artifact record")
        downloaded = artifact["downloaded"]
        path = artifact.get("path")
        checksum = artifact.get("sha256")
        checksum_status = artifact.get("sha256_status")
        if not isinstance(checksum_status, str) or not checksum_status:
            raise ProtocolV2Error(f"{source_id} checksum status is missing")
        if downloaded:
            if not isinstance(path, str) or not path or not isinstance(checksum, str):
                raise ProtocolV2Error(f"{source_id} downloaded artifact lacks path/checksum")
            if not SHA256_RE.fullmatch(checksum):
                raise ProtocolV2Error(f"{source_id} has an invalid SHA-256")
        elif path is not None or checksum is not None:
            raise ProtocolV2Error(
                f"{source_id} may not declare path/SHA-256 before download"
            )
        if downloaded:
            raise ProtocolV2Error(
                f"{source_id} conflicts with metadata-only audit declaration"
            )

        coverage = source.get("coverage")
        if not isinstance(coverage, dict) or set(coverage) != required_fields:
            raise ProtocolV2Error(f"{source_id} coverage record is incomplete")
        for key, value in coverage.items():
            if key == "vietnamese":
                if not isinstance(value, bool):
                    raise ProtocolV2Error(f"{source_id}.coverage.vietnamese must be boolean")
            elif not isinstance(value, str) or not value:
                raise ProtocolV2Error(f"{source_id}.coverage.{key} is empty")

        access_gate = source.get("access_gate")
        if not isinstance(access_gate, dict):
            raise ProtocolV2Error(f"{source_id} requires an access gate")
        access_id = _canonical_id(access_gate.get("id"), f"{source_id}.access_gate.id")
        if access_id in gate_ids:
            raise ProtocolV2Error(f"duplicate source gate: {access_id}")
        gate_ids.add(access_id)
        if access_gate.get("status") not in {"pass", "blocked", "fail", "not_assessed"}:
            raise ProtocolV2Error(f"{access_id} has an invalid status")
        requirements = access_gate.get("requirements")
        blockers = access_gate.get("blockers")
        if not isinstance(requirements, list) or not requirements:
            raise ProtocolV2Error(f"{access_id} requires explicit conditions")
        if access_gate.get("status") == "blocked" and (
            not isinstance(blockers, list) or not blockers
        ):
            raise ProtocolV2Error(f"{access_id} is blocked without a blocker")
        if not downloaded and access_gate.get("status") == "pass":
            raise ProtocolV2Error(f"{access_id} cannot pass before a hashed snapshot exists")

        coverage_gates = source.get("coverage_gates")
        if not isinstance(coverage_gates, list) or not coverage_gates:
            raise ProtocolV2Error(f"{source_id} requires coverage gates")
        for gate in coverage_gates:
            if not isinstance(gate, dict):
                raise ProtocolV2Error(f"{source_id} coverage gate must be an object")
            gate_id = _canonical_id(gate.get("id"), f"{source_id}.coverage_gate.id")
            if gate_id in gate_ids:
                raise ProtocolV2Error(f"duplicate source gate: {gate_id}")
            gate_ids.add(gate_id)
            if gate.get("status") not in {"pass", "blocked", "fail", "not_assessed"}:
                raise ProtocolV2Error(f"{gate_id} has an invalid status")
            if not isinstance(gate.get("limitations"), list) or not gate["limitations"]:
                raise ProtocolV2Error(f"{gate_id} must state limitations")

    if providers != REQUIRED_PROVIDERS:
        raise ProtocolV2Error("public source providers do not match TREC/CrisisFACTS/IDRISI/NOAA/UK")
    if any(source["coverage"]["vietnamese"] for source in sources):
        raise ProtocolV2Error("current public shortlist must not imply Vietnamese coverage")
    return source_ids, gate_ids


def _validate_public_anchor(
    anchor: Mapping[str, Any], source_ids: set[str]
) -> None:
    """Validate the frozen, aggregate-only public snapshot audit.

    The source manifest records the pre-download rights decision.  This
    separate member records only checksum-verified aggregate audits and keeps
    restricted sources explicitly blocked; it is not a generator-fitting or
    field-validation artifact.
    """

    _require_schema(anchor, "v2.public-anchor.1", "public anchor")
    _canonical_id(anchor.get("audit_id"), "public anchor audit_id")
    if anchor.get("audit_kind") != "descriptive_external_sanity_audit":
        raise ProtocolV2Error("public anchor must remain descriptive-only")
    _iso_date(anchor.get("audit_date"), "public anchor audit_date")

    audited = anchor.get("audited_sources")
    if not isinstance(audited, dict) or set(audited) != AUDITED_PUBLIC_SOURCE_IDS:
        raise ProtocolV2Error("public anchor audited-source set is not locked")
    if not set(audited).issubset(source_ids):
        raise ProtocolV2Error("public anchor references an unknown source")
    for source_id, row in audited.items():
        if not isinstance(row, dict) or row.get("audit_status") != "pass":
            raise ProtocolV2Error(f"{source_id} aggregate audit did not pass")
        snapshot = row.get("snapshot")
        if (
            not isinstance(snapshot, dict)
            or snapshot.get("checksum_verified_before_parse") is not True
            or not isinstance(snapshot.get("sha256"), str)
            or SHA256_RE.fullmatch(snapshot["sha256"]) is None
            or not isinstance(snapshot.get("exact_snapshot_url"), str)
            or not snapshot["exact_snapshot_url"].startswith("https://")
        ):
            raise ProtocolV2Error(f"{source_id} lacks a verified pinned snapshot")
        limits = row.get("claim_limits")
        if not isinstance(limits, list) or not limits:
            raise ProtocolV2Error(f"{source_id} lacks claim limits")

    blocked = anchor.get("blocked_sources")
    if not isinstance(blocked, list):
        raise ProtocolV2Error("public anchor requires blocked-source records")
    blocked_by_id: dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(blocked):
        if not isinstance(row, dict):
            raise ProtocolV2Error(f"blocked_sources[{index}] must be an object")
        source_id = _canonical_id(
            row.get("source_id"), f"blocked_sources[{index}].source_id"
        )
        if source_id in blocked_by_id:
            raise ProtocolV2Error("public anchor contains duplicate blocked sources")
        blocked_by_id[source_id] = row
    if set(blocked_by_id) != BLOCKED_PUBLIC_SOURCE_IDS:
        raise ProtocolV2Error("TREC-IS and CrisisFACTS must remain blocked")
    for source_id, row in blocked_by_id.items():
        if (
            row.get("audit_status") != "blocked"
            or row.get("usable_as_evidence") is not False
            or row.get("local_snapshot_present") is not False
            or row.get("sha256") is not None
            or row.get("data_or_counts_imputed") is not False
            or not isinstance(row.get("blockers"), list)
            or not row["blockers"]
        ):
            raise ProtocolV2Error(f"{source_id} blocked audit is not fail-closed")

    mapping = anchor.get("anchor_mapping")
    fit = mapping.get("generator_fit") if isinstance(mapping, dict) else None
    if (
        not isinstance(mapping, dict)
        or mapping.get("status") != "descriptive_only_not_generator_fitting"
        or not isinstance(fit, dict)
        or fit.get("performed") is not False
        or fit.get("parameters_estimated_from_public_sources") != []
        or not isinstance(mapping.get("unsupported_validation_targets"), list)
        or not mapping["unsupported_validation_targets"]
    ):
        raise ProtocolV2Error("public anchor overstates generator fitting or validation")

    seed_safety = anchor.get("seed_safety")
    if seed_safety != {
        "confirmation_seeds_generated": False,
        "forbidden_confirmation_seed_count": 40,
        "forbidden_confirmation_seed_interval": "4400-4439 inclusive",
        "generator_invoked": False,
    }:
        raise ProtocolV2Error("public audit must not open confirmation seeds")
    reproduction = anchor.get("reproduction")
    if (
        not isinstance(reproduction, dict)
        or reproduction.get("checksum_policy") != "fail_closed_before_parse"
        or reproduction.get("module") != "demo.v2.public_audit"
        or reproduction.get("network_access_required") is not False
    ):
        raise ProtocolV2Error("public anchor reproduction contract is incomplete")
    boundary = anchor.get("global_claim_boundary")
    if not isinstance(boundary, str) or "does not" not in boundary:
        raise ProtocolV2Error("public anchor lacks a global claim boundary")


def _validate_analysis_contract(
    contract: Mapping[str, Any], registry_scopes: set[str], source_gate_ids: set[str]
) -> tuple[set[str], set[str], set[str]]:
    _require_schema(contract, "v2.analysis-contract.3", "analysis contract")
    _canonical_id(contract.get("id"), "analysis contract id")
    if contract.get("analysis_unit") != "paired_confirmation_seed":
        raise ProtocolV2Error("analysis unit must be paired_confirmation_seed")
    if contract.get("observation_snapshot") != {
        "base_time": "2026-10-15T00:00:00Z",
        "cutoff_min_after_base_time": 150,
        "report_inclusion_rule": "received_at_at_or_before_cutoff",
        "missing_event_time_action": "retain_as_observed_then_route_to_manual_review",
        "incident_evaluation_rule": "evaluator_incident_start_at_or_before_cutoff",
        "batch_job_ready_rule": "all_predicted_jobs_ready_at_declared_cutoff",
        "late_report_action": "exclude_from_this_snapshot_without_imputation",
    }:
        raise ProtocolV2Error("observation snapshot semantics are not locked")
    if contract.get("operational_metric_parameters") != {
        "review_cluster_min_reports": 2,
        "review_mean_provenance_threshold": 0.4,
        "unresolved_report_review_units": "one_per_report",
        "false_destination_definition": "emitted_cluster_containing_only_noise_reports",
    }:
        raise ProtocolV2Error("operational metric parameters are not locked")

    rules = contract.get("selection_rules")
    endpoints = contract.get("endpoints")
    families = contract.get("holm_families")
    claims = contract.get("claim_gates")
    if not all(isinstance(value, list) for value in (rules, endpoints, families, claims)):
        raise ProtocolV2Error("analysis contract lists are incomplete")

    endpoint_ids = set(_unique_ids(endpoints, "endpoints"))
    endpoint_by_id = {endpoint["id"]: endpoint for endpoint in endpoints}
    for endpoint in endpoints:
        if endpoint.get("direction") not in {"higher", "lower"}:
            raise ProtocolV2Error(f"endpoint {endpoint['id']} has no direction")
        if endpoint.get("denominator_required") is not True:
            raise ProtocolV2Error(f"endpoint {endpoint['id']} must report denominator")
        if not isinstance(endpoint.get("confirmatory"), bool):
            raise ProtocolV2Error(f"endpoint {endpoint['id']} lacks confirmatory flag")
        if not isinstance(endpoint.get("unit"), str) or not isinstance(
            endpoint.get("population"), str
        ):
            raise ProtocolV2Error(f"endpoint {endpoint['id']} lacks unit/population")

    rule_ids = set(_unique_ids(rules, "selection_rules"))
    if rule_ids != {"selection.common.one_se"} or len(rules) != 1:
        raise ProtocolV2Error("exactly one common one-SE selection rule is required")
    rule = rules[0]
    applied_methods = rule.get("applies_to_method_ids")
    if (
        not isinstance(applied_methods, list)
        or applied_methods != sorted(registry_scopes)
        or set(applied_methods) != registry_scopes
    ):
        raise ProtocolV2Error("common selection rule must cover each method exactly once")
    if (
        rule.get("selection_scope") != "within_each_method_independently"
        or rule.get("selection_split") != "calibration"
        or rule.get("candidate_unit") != "configuration_id"
        or rule.get("one_configuration_per_method") is not True
        or rule.get("required_calibration_seed_count") != 20
        or rule.get("ranking_semantics")
        != "lexicographic_after_one_standard_error_filter"
    ):
        raise ProtocolV2Error("common per-method selection scope is not locked")
    eligibility = rule.get("eligibility")
    if not isinstance(eligibility, dict) or eligibility != {
        "complete_seed_coverage_required": True,
        "finite_required_endpoints": True,
        "positive_denominators_required": True,
        "failed_candidate_action": "mark_candidate_ineligible",
    }:
        raise ProtocolV2Error("selection eligibility rules are not locked")
    steps = rule.get("steps")
    expected_steps = [
        (
            1,
            "identify_best_mean_ari",
            "endpoint.clustering.ari_labeled_reports",
            "higher",
        ),
        (
            2,
            "retain_one_standard_error_set",
            "endpoint.clustering.ari_labeled_reports",
            None,
        ),
        (
            3,
            "rank_within_one_standard_error_set",
            "endpoint.operational.false_destinations_per_100_reports",
            "lower",
        ),
        (
            4,
            "rank_remaining_ties",
            "endpoint.secondary.noise_rejection_rate",
            "higher",
        ),
        (
            5,
            "rank_remaining_ties",
            "endpoint.operational.review_burden",
            "lower",
        ),
    ]
    if not isinstance(steps, list) or len(steps) != len(expected_steps):
        raise ProtocolV2Error("selection rule must contain the five locked steps")
    for step, (order, action, endpoint_id, direction) in zip(
        steps, expected_steps, strict=True
    ):
        if not isinstance(step, dict):
            raise ProtocolV2Error("selection step must be an object")
        if (
            step.get("order") != order
            or step.get("action") != action
            or step.get("endpoint_id") != endpoint_id
            or endpoint_id not in endpoint_by_id
        ):
            raise ProtocolV2Error(f"selection step {order} does not match the v2 plan")
        if direction is not None and step.get("direction") != direction:
            raise ProtocolV2Error(f"selection step {order} has the wrong direction")
        if direction is not None and step.get("direction") != endpoint_by_id[endpoint_id]["direction"]:
            raise ProtocolV2Error(f"selection step {order} reverses its endpoint")
    one_se = steps[1]
    if (
        one_se.get("formula")
        != "mean_ari_candidate >= mean_ari_best - standard_error_ari_best"
        or one_se.get("standard_error_definition")
        != "sample_standard_deviation_of_best_candidate_ari_over_sqrt_20"
        or one_se.get("inclusive") is not True
    ):
        raise ProtocolV2Error("one-standard-error set is not fully specified")
    if any(
        step.get("statistic") != "unweighted_mean_over_20_calibration_seeds"
        for step in (steps[0], steps[2], steps[3], steps[4])
    ):
        raise ProtocolV2Error("selection statistics must use all 20 calibration seeds")
    if (
        rule.get("final_tie_breaker") != "canonical_configuration_id_ascending"
        or rule.get("missing_metric_action") != "mark_candidate_ineligible"
        or rule.get("no_eligible_action")
        != "return_no_selection_without_relaxation"
        or rule.get("post_hoc_rule_changes") != "forbidden"
    ):
        raise ProtocolV2Error("selection failure/tie policy permits post-hoc changes")

    roles = contract.get("clustering_endpoint_roles")
    expected_primary_families = {"family.clustering.synthetic"}
    expected_secondary_endpoints = {
        "endpoint.clustering.incident_split_loss",
        "endpoint.clustering.incident_merge_loss",
        "endpoint.operational.review_burden",
        "endpoint.secondary.destination_geographic_diameter_m",
        "endpoint.secondary.noise_rejection_rate",
    }
    if (
        not isinstance(roles, dict)
        or set(roles.get("co_primary_family_ids", [])) != expected_primary_families
        or set(roles.get("key_secondary_endpoint_ids", []))
        != expected_secondary_endpoints
    ):
        raise ProtocolV2Error("clustering co-primary/secondary roles do not match the plan")

    family_ids = set(_unique_ids(families, "holm_families"))
    family_by_id = {family["id"]: family for family in families}
    expected_clustering_members = {
        "family.clustering.synthetic": {
            "endpoint.clustering.ari_labeled_reports",
            "endpoint.operational.false_destinations_per_100_reports",
        },
    }
    if any(
        family_id not in family_by_id
        or set(family_by_id[family_id].get("endpoint_ids", [])) != expected_members
        for family_id, expected_members in expected_clustering_members.items()
    ):
        raise ProtocolV2Error("clustering co-primary families do not match the plan")
    expected_priority_dispatch = {
        "endpoint.priority.ndcg_at_5",
        "endpoint.priority.normalized_drift",
        "endpoint.priority.top_k_churn",
        "endpoint.priority.false_priority_lift",
        "endpoint.dispatch.latent_harm",
        "endpoint.dispatch.deadline_miss_rate",
    }
    priority_dispatch = family_by_id.get("family.priority_dispatch.synthetic")
    if (
        not isinstance(priority_dispatch, dict)
        or set(priority_dispatch.get("endpoint_ids", []))
        != expected_priority_dispatch
    ):
        raise ProtocolV2Error(
            "priority/dispatch confirmatory family does not match the v2 plan"
        )
    membership: dict[str, int] = {endpoint_id: 0 for endpoint_id in endpoint_ids}
    for family in families:
        if family.get("procedure") != "holm" or family.get("alpha") != 0.05:
            raise ProtocolV2Error(f"family {family['id']} must use Holm at alpha 0.05")
        members = family.get("endpoint_ids")
        if not isinstance(members, list) or not members or len(members) != len(set(members)):
            raise ProtocolV2Error(f"family {family['id']} has invalid endpoints")
        for endpoint_id in members:
            if endpoint_id not in endpoint_by_id:
                raise ProtocolV2Error(f"family {family['id']} references unknown endpoint")
            if endpoint_by_id[endpoint_id]["confirmatory"] is not True:
                raise ProtocolV2Error(f"family {family['id']} contains a nonconfirmatory endpoint")
            membership[endpoint_id] += 1
    for endpoint_id, endpoint in endpoint_by_id.items():
        expected_memberships = 1 if endpoint["confirmatory"] else 0
        if membership[endpoint_id] != expected_memberships:
            raise ProtocolV2Error(
                f"endpoint {endpoint_id} has {membership[endpoint_id]} Holm memberships; "
                f"expected {expected_memberships}"
            )

    inference = contract.get("inference")
    if (
        not isinstance(inference, dict)
        or inference.get("multiplicity_scope") != "within_each_declared_family"
        or inference.get("unfavorable_and_null_results_retained") is not True
        or not isinstance(inference.get("minimum_reported_fields"), list)
        or "holm_adjusted_p_value" not in inference["minimum_reported_fields"]
        or "denominator" not in inference["minimum_reported_fields"]
    ):
        raise ProtocolV2Error("inference and retention policy is incomplete")

    claim_ids = set(_unique_ids(claims, "claim_gates"))
    for claim in claims:
        if claim.get("default_status") not in {"eligible_after_evidence", "blocked"}:
            raise ProtocolV2Error(f"claim {claim['id']} has an invalid default status")
        required_families = claim.get("required_family_ids")
        required_source_gates = claim.get("required_source_gate_ids")
        if not isinstance(required_families, list) or any(
            family_id not in family_ids for family_id in required_families
        ):
            raise ProtocolV2Error(f"claim {claim['id']} references unknown Holm family")
        if not isinstance(required_source_gates, list) or any(
            gate_id not in source_gate_ids for gate_id in required_source_gates
        ):
            raise ProtocolV2Error(f"claim {claim['id']} references unknown source gate")
        for key in ("required_conditions", "prohibited_inferences"):
            values = claim.get(key)
            if not isinstance(values, list) or not values:
                raise ProtocolV2Error(f"claim {claim['id']} must declare {key}")
        if not isinstance(claim.get("permitted_scope"), str) or not claim["permitted_scope"]:
            raise ProtocolV2Error(f"claim {claim['id']} lacks permitted scope")
        if required_source_gates and claim.get("default_status") != "blocked":
            raise ProtocolV2Error(f"external claim {claim['id']} must begin blocked")

    mandatory_blocked = {
        "claim.real_incident_clustering_accuracy",
        "claim.real_dispatch_benefit",
        "claim.vietnamese_transfer",
    }
    if not mandatory_blocked.issubset(claim_ids):
        raise ProtocolV2Error("real-incident, real-dispatch, and Vietnamese gates are required")
    if any(
        claim["default_status"] != "blocked"
        for claim in claims
        if claim["id"] in mandatory_blocked
    ):
        raise ProtocolV2Error("unsupported real-world claims must remain blocked")
    return endpoint_ids, family_ids, claim_ids


def _bundle_manifest(protocol_dir: Path) -> tuple[Mapping[str, Any], tuple[str, ...]]:
    bundle_path = protocol_dir / BUNDLE_NAME
    bundle = _load_json(bundle_path)
    _require_schema(bundle, "v2.protocol-bundle.1", "protocol bundle")
    _canonical_id(bundle.get("bundle_id"), "protocol bundle id")
    if bundle.get("hash_algorithm") != "sha256":
        raise ProtocolV2Error("protocol bundle hash algorithm must be sha256")
    members = bundle.get("frozen_members")
    if (
        not isinstance(members, list)
        or not members
        or any(not isinstance(member, str) or not member for member in members)
        or members != sorted(members)
        or len(members) != len(set(members))
    ):
        raise ProtocolV2Error("frozen member list must be unique and sorted")
    if set(members) != MANDATORY_FROZEN_MEMBERS:
        raise ProtocolV2Error("frozen member list must contain the five v2 contracts")
    excluded_prefixes = bundle.get("excluded_path_prefixes")
    excluded_files = bundle.get("excluded_files")
    if excluded_prefixes != ["results/"] or LOCK_NAME not in (excluded_files or []):
        raise ProtocolV2Error("result and lock exclusions are not explicit")
    policy = bundle.get("policy")
    if (
        not isinstance(policy, dict)
        or policy.get("results_are_never_protocol_inputs") is not True
        or policy.get("unlisted_files_are_not_hashed") is not True
        or policy.get("symlinked_frozen_member_is_forbidden") is not True
    ):
        raise ProtocolV2Error("protocol bundle exclusion policy is incomplete")

    for member in members:
        pure = PurePosixPath(member)
        if pure.is_absolute() or ".." in pure.parts or len(pure.parts) != 1:
            raise ProtocolV2Error(f"unsafe frozen member path: {member!r}")
        if member == LOCK_NAME or member.startswith("results/"):
            raise ProtocolV2Error(f"result/lock file cannot be frozen: {member}")
        path = protocol_dir / member
        if path.is_symlink():
            raise ProtocolV2Error(f"frozen member may not be a symlink: {member}")
        if not path.is_file():
            raise ProtocolV2Error(f"missing frozen member: {member}")
    return bundle, tuple(members)


def file_sha256(path: Path | str) -> str:
    """Compute the SHA-256 digest of an existing regular file."""

    source = Path(path)
    if not source.is_file():
        raise ProtocolV2Error(f"cannot hash missing file: {source}")
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def protocol_member_hashes(
    protocol_dir: Path | str = DEFAULT_PROTOCOL_DIR,
) -> dict[str, str]:
    """Return hashes for the bundle manifest and explicit frozen members only."""

    directory = Path(protocol_dir)
    _, members = _bundle_manifest(directory)
    names = (BUNDLE_NAME, *members)
    return {name: file_sha256(directory / name) for name in sorted(names)}


def protocol_bundle_sha256(
    protocol_dir: Path | str = DEFAULT_PROTOCOL_DIR,
) -> str:
    """Return a location-independent hash of the frozen protocol bundle."""

    member_hashes = protocol_member_hashes(protocol_dir)
    encoded = json.dumps(
        member_hashes,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def load_protocol(
    protocol_dir: Path | str = DEFAULT_PROTOCOL_DIR,
) -> ProtocolV2:
    """Load and validate every frozen v2 contract."""

    directory = Path(protocol_dir)
    _bundle_manifest(directory)
    seed_manifest = _load_json(directory / SEED_NAME)
    method_registry = _load_json(directory / METHOD_NAME)
    source_manifest = _load_json(directory / SOURCE_NAME)
    public_anchor = _load_json(directory / PUBLIC_ANCHOR_NAME)
    analysis_contract = _load_json(directory / ANALYSIS_NAME)

    seeds = _validate_seeds(seed_manifest)
    paired, independent, registry_scopes, _method_ids = _validate_method_registry(
        method_registry
    )
    source_ids, source_gate_ids = _validate_sources(source_manifest)
    _validate_public_anchor(public_anchor, source_ids)
    endpoint_ids, family_ids, claim_ids = _validate_analysis_contract(
        analysis_contract, registry_scopes, source_gate_ids
    )
    member_hashes = protocol_member_hashes(directory)
    bundle_hash = protocol_bundle_sha256(directory)
    return ProtocolV2(
        development_seeds=seeds["development"],
        calibration_seeds=seeds["calibration"],
        confirmation_seeds=seeds["confirmation"],
        retired_confirmation_seeds=seeds["retired_confirmation"],
        paired_configurations=paired,
        independent_configurations=independent,
        endpoint_ids=tuple(sorted(endpoint_ids)),
        holm_family_ids=tuple(sorted(family_ids)),
        claim_gate_ids=tuple(sorted(claim_ids)),
        source_ids=tuple(sorted(source_ids)),
        source_gate_ids=tuple(sorted(source_gate_ids)),
        member_sha256=member_hashes,
        bundle_sha256=bundle_hash,
    )


def _normalized_frozen_at(value: str | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z"
        )
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ProtocolV2Error("frozen_at must be an ISO-8601 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ProtocolV2Error("frozen_at is not a valid ISO-8601 timestamp") from exc
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ProtocolV2Error("frozen_at must use UTC")
    return parsed.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_freeze_record(
    protocol_dir: Path | str = DEFAULT_PROTOCOL_DIR,
    *,
    frozen_at: str | None = None,
) -> dict[str, Any]:
    """Build a freeze record without reading or hashing any result file."""

    protocol = load_protocol(protocol_dir)
    return {
        "schema_version": "v2.protocol-lock.1",
        "bundle_id": "protocol.flood_rescue.v2",
        "frozen_at": _normalized_frozen_at(frozen_at),
        "hash_algorithm": "sha256",
        "bundle_sha256": protocol.bundle_sha256,
        "members": [
            {"path": path, "sha256": digest}
            for path, digest in sorted(protocol.member_sha256.items())
        ],
        "results_excluded": True,
        "external_data_downloaded_by_freeze": False,
    }


def write_freeze_record(
    output_path: Path | str,
    protocol_dir: Path | str = DEFAULT_PROTOCOL_DIR,
    *,
    frozen_at: str | None = None,
) -> dict[str, Any]:
    """Atomically write a validated freeze record outside the frozen members."""

    directory = Path(protocol_dir)
    _, members = _bundle_manifest(directory)
    output = Path(output_path)
    output_resolved = output.resolve(strict=False)
    frozen_paths = {
        (directory / name).resolve(strict=False) for name in (BUNDLE_NAME, *members)
    }
    if output_resolved in frozen_paths:
        raise ProtocolV2Error("freeze output may not overwrite a frozen protocol member")
    record = build_freeze_record(directory, frozen_at=frozen_at)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=".tmp",
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(output)
    return record


def _summary(protocol: ProtocolV2) -> dict[str, Any]:
    return {
        "schema_version": "v2.protocol-validation.1",
        "status": "pass",
        "seed_counts": {
            "development": len(protocol.development_seeds),
            "calibration": len(protocol.calibration_seeds),
            "confirmation": len(protocol.confirmation_seeds),
            "retired_confirmation": len(protocol.retired_confirmation_seeds),
        },
        "configuration_counts": {
            "paired_nuisance_pairs": len(protocol.paired_configurations) // 2,
            "paired_executions": len(protocol.paired_configurations),
            "st_dbscan": len(protocol.independent_configurations["grid.st_dbscan"]),
            "hdbscan": len(protocol.independent_configurations["grid.hdbscan"]),
        },
        "endpoint_count": len(protocol.endpoint_ids),
        "holm_family_count": len(protocol.holm_family_ids),
        "claim_gate_count": len(protocol.claim_gate_ids),
        "source_count": len(protocol.source_ids),
        "bundle_sha256": protocol.bundle_sha256,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and freeze the flood-rescue v2 protocol bundle."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "hash"):
        child = subparsers.add_parser(command)
        child.add_argument(
            "--protocol-dir", type=Path, default=DEFAULT_PROTOCOL_DIR
        )
    freeze = subparsers.add_parser("freeze")
    freeze.add_argument("--protocol-dir", type=Path, default=DEFAULT_PROTOCOL_DIR)
    freeze.add_argument("--output", type=Path)
    freeze.add_argument("--frozen-at")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    if args.command == "validate":
        print(json.dumps(_summary(load_protocol(args.protocol_dir)), indent=2, sort_keys=True))
        return 0
    if args.command == "hash":
        load_protocol(args.protocol_dir)
        print(protocol_bundle_sha256(args.protocol_dir))
        return 0
    if args.command == "freeze":
        output = args.output or (args.protocol_dir / LOCK_NAME)
        record = write_freeze_record(
            output,
            args.protocol_dir,
            frozen_at=args.frozen_at,
        )
        print(json.dumps(record, indent=2, sort_keys=True))
        return 0
    raise AssertionError(f"unreachable command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ANALYSIS_NAME",
    "BUNDLE_NAME",
    "DEFAULT_PROTOCOL_DIR",
    "ExpandedConfiguration",
    "METHOD_NAME",
    "ProtocolV2",
    "ProtocolV2Error",
    "PUBLIC_ANCHOR_NAME",
    "SEED_NAME",
    "SOURCE_NAME",
    "build_freeze_record",
    "file_sha256",
    "load_protocol",
    "main",
    "protocol_bundle_sha256",
    "protocol_member_hashes",
    "write_freeze_record",
]
