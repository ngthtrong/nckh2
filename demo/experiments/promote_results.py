"""Promote the Gate-3 result into a self-contained, traceable publication bundle.

The promoter never opens a held-out dataset.  It independently revalidates the
single sealed X0 result, creates a compact selector-compatible projection for
human review, archives the complete result losslessly, copies the accepted
ancillary Gate-1/Exp22 evidence byte-for-byte, and generates the claim catalog
and LaTeX lookup table used by the manuscript.

All destinations are canonical and created exclusively.  A failure removes
only files created by this invocation; an existing destination is never
replaced.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

from demo.experiments.artifacts import validate_manifest
from demo.experiments.pre_gate2 import canonical_json_bytes
from demo.experiments.promote_gate3 import validate_candidate
from demo.experiments.protocol import file_sha256


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_GATE1_LOCK = REPOSITORY_ROOT / "revision" / "gate1-lock.json"
DEFAULT_GATE2_LOCK = REPOSITORY_ROOT / "revision" / "gate2-lock.json"
DEFAULT_GATE3_LOCK = REPOSITORY_ROOT / "revision" / "gate3-lock.json"
DEFAULT_REJECTED_RUNS = REPOSITORY_ROOT / "revision" / "rejected-runs.json"
DEFAULT_SELECTED_CONFIGS = (
    REPOSITORY_ROOT / "demo" / "protocol" / "selected_configs.json"
)

DEFAULT_RUNTIME_RESULT = (
    REPOSITORY_ROOT
    / "demo"
    / "artifacts"
    / "runs"
    / "20260728T205453Z-85f2a6686a1b-0060e5dc-gate2-exp22-runtime"
    / "tables"
    / "exp22_runtime_repro.json"
)
EXPECTED_RUNTIME_MANIFEST_SHA256 = (
    "429d82f4897c2c52313e7bc38d0109949d256cb8e5484988d9f47bff2bd46de6"
)

DEFAULT_SUMMARY = (
    REPOSITORY_ROOT
    / "demo"
    / "results"
    / "tables"
    / "exp23_heldout_summary.json"
)
DEFAULT_RAW_ARCHIVE = (
    REPOSITORY_ROOT
    / "demo"
    / "results"
    / "tables"
    / "exp23_heldout_evaluation.json.gz"
)
DEFAULT_BASE_SELECTORS = (
    REPOSITORY_ROOT
    / "demo"
    / "results"
    / "tables"
    / "exp23_heldout_selectors.json"
)
DEFAULT_RUNTIME_PROMOTED = (
    REPOSITORY_ROOT
    / "demo"
    / "results"
    / "tables"
    / "exp22_runtime_repro.json"
)
DEFAULT_DISTRIBUTION_PROMOTED = (
    REPOSITORY_ROOT
    / "demo"
    / "results"
    / "tables"
    / "data_distribution_report_v4.json"
)
DEFAULT_QUALITY_PROMOTED = (
    REPOSITORY_ROOT
    / "demo"
    / "results"
    / "tables"
    / "data_quality_summary_v4.json"
)
DEFAULT_CLAIM_SELECTORS = (
    REPOSITORY_ROOT / "loop" / "revision" / "claim-selectors.json"
)
DEFAULT_TRACEABILITY = (
    REPOSITORY_ROOT / "loop" / "revision" / "traceability.md"
)
DEFAULT_LATEX_MACROS = (
    REPOSITORY_ROOT / "paper" / "generated" / "revision_results.tex"
)
DEFAULT_RESULT_LOCK = REPOSITORY_ROOT / "revision" / "result-lock.json"

PROMOTED_TARGETS = (
    DEFAULT_SUMMARY,
    DEFAULT_RAW_ARCHIVE,
    DEFAULT_BASE_SELECTORS,
    DEFAULT_RUNTIME_PROMOTED,
    DEFAULT_DISTRIBUTION_PROMOTED,
    DEFAULT_QUALITY_PROMOTED,
    DEFAULT_CLAIM_SELECTORS,
    DEFAULT_TRACEABILITY,
    DEFAULT_LATEX_MACROS,
    DEFAULT_RESULT_LOCK,
)

RAW_SECTION_PATHS = (
    "/clustering/per_seed_rows",
    "/factorial_ablation/clustering/rows",
    "/factorial_ablation/priority/rows",
    "/priority_robustness/scenario_rows",
    "/dispatch_outcomes/per_seed_resource_policy_rows",
)

NUMERIC_WALK_SKIP_KEYS = frozenset(
    {
        "observations",
        "pairs",
        "raw_repeats",
        "scenario_rows",
        "per_seed_rows",
        "per_seed_resource_policy_rows",
        "rows",
        "unavailable",
    }
)

REQUIRED_DISCLOSURE_CLAIMS = frozenset(
    {
        (
            "clustering.summary.benchmark_label_aware.product_louvain."
            "false_operational_destinations.mean"
        ),
        (
            "clustering.summary.benchmark_label_aware.product_louvain."
            "operator_review_burden.mean"
        ),
        (
            "clustering.summary.benchmark_label_aware.product_louvain."
            "noise_rejection_rate.mean"
        ),
        "factorial.priority.main:confidence.mean",
        "factorial.priority.main:confidence.holm_adjusted_p_value",
        (
            "priority.summary.coordinated_high_confidence_campaign."
            "duplicate_aware_robust.priority_drift_abs_normalized.mean"
        ),
        (
            "priority.paired.coordinated_high_confidence_campaign."
            "priority_drift_abs_normalized.mean"
        ),
        (
            "dispatch.paired.nominal_dual_depot.revised_priority.vs."
            "nearest_first.latent_harm.mean"
        ),
        (
            "dispatch.paired.lean_hue.revised_priority.vs."
            "equity_aging.arrival_equity_gap_min.mean"
        ),
        "gate3.retention.factorial_density_match_failures",
    }
)


def _relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError as exc:
        raise ValueError(f"path is outside the repository: {resolved}") from exc


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_object(
    path: Path,
    *,
    label: str,
) -> tuple[bytes, dict[str, Any]]:
    try:
        payload = path.read_bytes()
        value = json.loads(payload)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is absent or invalid: {path}") from exc
    if not isinstance(value, dict) or payload != canonical_json_bytes(value):
        raise ValueError(f"{label} must be a canonical JSON object")
    return payload, value


def _sealed_json_object(
    path: Path,
    *,
    label: str,
) -> tuple[bytes, dict[str, Any]]:
    """Read a manifest/checksum-sealed JSON object without re-encoding it."""

    try:
        payload = path.read_bytes()
        value = json.loads(payload)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is absent or invalid: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload, value


def _pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _resolve_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise ValueError(f"JSON pointer must start with '/': {pointer}")
    current = document
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            if not token.isdigit() or int(token) >= len(current):
                raise ValueError(f"unresolved list pointer: {pointer}")
            current = current[int(token)]
        elif isinstance(current, Mapping) and token in current:
            current = current[token]
        else:
            raise ValueError(f"unresolved JSON pointer: {pointer}")
    return current


def _join_pointer(base: str, relative: str) -> str:
    if not relative:
        return base
    if not base:
        return relative
    return f"{base}{relative}"


def _json_pointer_tokens(pointer: str) -> list[str]:
    if not pointer:
        return []
    return [
        token.replace("~1", "/").replace("~0", "~")
        for token in pointer[1:].split("/")
    ]


def _validate_gate3_binding(
    gate3_lock: Mapping[str, Any],
    validated: Mapping[str, Any],
) -> None:
    if (
        gate3_lock.get("gate") != "Gate 3"
        or gate3_lock.get("status") != "locked"
    ):
        raise ValueError("Gate 3 is not locked")
    accepted = gate3_lock.get("accepted_run")
    if not isinstance(accepted, Mapping):
        raise ValueError("Gate-3 accepted run is absent")
    expected = {
        "run_id": validated["run_id"],
        "manifest_sha256": validated["manifest_sha256"],
    }
    for key, value in expected.items():
        if accepted.get(key) != value:
            raise ValueError(f"Gate-3 accepted run differs at {key}")
    result = accepted.get("result")
    selectors = accepted.get("selectors")
    invocation = accepted.get("invocation")
    if not all(isinstance(row, Mapping) for row in (result, selectors, invocation)):
        raise ValueError("Gate-3 accepted artifact records are malformed")
    if (
        result.get("sha256") != validated["result_sha256"]
        or result.get("artifact_content_sha256")
        != validated["artifact_content_sha256"]
        or selectors.get("sha256") != validated["selector_sha256"]
        or selectors.get("selector_content_sha256")
        != validated["selector_content_sha256"]
        or selectors.get("selector_count") != validated["selector_count"]
        or invocation.get("sha256") != validated["invocation_sha256"]
        or invocation.get("candidate_suite_invocation") != 1
    ):
        raise ValueError("Gate-3 artifact binding differs from revalidation")
    upstream = gate3_lock.get("upstream_binding")
    if not isinstance(upstream, Mapping):
        raise ValueError("Gate-3 upstream binding is absent")
    current_upstream = {
        "gate1_lock_sha256": file_sha256(DEFAULT_GATE1_LOCK),
        "gate2_lock_sha256": file_sha256(DEFAULT_GATE2_LOCK),
        "selected_configs_sha256": file_sha256(DEFAULT_SELECTED_CONFIGS),
    }
    for key, value in current_upstream.items():
        if upstream.get(key) != value:
            raise ValueError(f"Gate-3 upstream binding changed at {key}")
    rejected_record = gate3_lock.get("rejected_run_ledger")
    if (
        not isinstance(rejected_record, Mapping)
        or rejected_record.get("sha256") != file_sha256(DEFAULT_REJECTED_RUNS)
    ):
        raise ValueError("Gate-3 rejected-run ledger binding changed")
    try:
        rejected = json.loads(DEFAULT_REJECTED_RUNS.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ValueError("rejected-run ledger is absent or invalid") from exc
    if not isinstance(rejected, Mapping):
        raise ValueError("rejected-run ledger must be a JSON object")
    rejected_ids = {
        row.get("run_id")
        for row in rejected.get("runs", [])
        if isinstance(row, Mapping)
    }
    if validated["run_id"] in rejected_ids:
        raise ValueError("Gate-3 accepted run also appears in the rejected ledger")


def _validate_runtime_result(
    result_path: Path,
) -> tuple[bytes, dict[str, Any], Path]:
    result_source = result_path.resolve()
    if result_source.name != "exp22_runtime_repro.json":
        raise ValueError("Exp22 result must use its canonical table name")
    run_root = result_source.parent.parent
    manifest_path = run_root / "manifest.json"
    if file_sha256(manifest_path) != EXPECTED_RUNTIME_MANIFEST_SHA256:
        raise ValueError("Exp22 manifest is not the Gate-2-audited runtime run")
    manifest = validate_manifest(manifest_path)
    if (
        manifest.get("status") != "succeeded"
        or manifest.get("exit_code") != 0
        or manifest.get("run_id") != run_root.name
    ):
        raise ValueError("Exp22 runtime run did not succeed cleanly")
    command = manifest.get("command")
    if (
        not isinstance(command, list)
        or "demo.experiments.exp22_runtime_repro" not in command
    ):
        raise ValueError("Exp22 manifest command is not the runtime experiment")
    payload, result = _sealed_json_object(
        result_source,
        label="Exp22 runtime result",
    )
    if manifest.get("checksums", {}).get(
        "tables/exp22_runtime_repro.json"
    ) != _sha256(payload):
        raise ValueError("Exp22 manifest does not seal its result table")
    contract = result.get("benchmark_contract")
    sizes = result.get("sizes")
    conclusion = result.get("spatial_conclusion")
    if (
        result.get("schema_version") != "runtime-repro-v1"
        or result.get("test_seed_access") is not False
        or not isinstance(contract, Mapping)
        or contract.get("warmup_repeats") != 1
        or contract.get("measured_repeats") != 5
        or contract.get("thread_limit") != 1
        or contract.get("one_core_claim_eligible") is not True
        or not isinstance(sizes, list)
        or [row.get("n_events") for row in sizes] != [373, 735, 1494]
        or any(
            not isinstance(row.get("equivalence"), Mapping)
            or row["equivalence"].get("exact_equivalence_pass") is not True
            for row in sizes
        )
        or not isinstance(conclusion, Mapping)
        or conclusion.get("candidate_pruning_implemented") is not True
        or conclusion.get("exact_equivalence_pass") is not True
        or conclusion.get("fully_sparse_memory_implemented") is not False
    ):
        raise ValueError("Exp22 runtime contract/equivalence audit failed")
    return payload, result, manifest_path


def _gate1_ancillary_sources() -> tuple[
    tuple[bytes, dict[str, Any], Path],
    tuple[bytes, dict[str, Any], Path],
    Path,
]:
    _, gate1 = _sealed_json_object(DEFAULT_GATE1_LOCK, label="Gate-1 lock")
    accepted = gate1.get("accepted_run")
    data_contract = gate1.get("data_contract")
    if not isinstance(accepted, Mapping) or not isinstance(data_contract, Mapping):
        raise ValueError("Gate-1 ancillary binding is malformed")
    manifest_path = REPOSITORY_ROOT / str(accepted["manifest"])
    if (
        file_sha256(manifest_path) != accepted.get("manifest_sha256")
        or validate_manifest(manifest_path).get("status") != "succeeded"
    ):
        raise ValueError("Gate-1 accepted manifest validation failed")
    run_root = manifest_path.parent
    distribution_path = run_root / "tables" / "data_distribution_report.json"
    quality_path = run_root / "tables" / "data_quality_summary.json"
    distribution_payload, distribution = _sealed_json_object(
        distribution_path,
        label="Gate-1 distribution report",
    )
    quality_payload, quality = _sealed_json_object(
        quality_path,
        label="Gate-1 quality summary",
    )
    if (
        _sha256(distribution_payload)
        != data_contract.get("distribution_report_sha256")
        or _sha256(quality_payload) != data_contract.get("quality_summary_sha256")
        or quality.get("all_quality_gates_pass") is not True
        or quality.get("method_performance_gate_count") != 0
        or quality.get("n_datasets") != 80
    ):
        raise ValueError("Gate-1 ancillary table binding failed")
    return (
        (distribution_payload, distribution, distribution_path),
        (quality_payload, quality, quality_path),
        manifest_path,
    )


def _remove_path(document: dict[str, Any], pointer: str) -> tuple[int, Any]:
    tokens = _json_pointer_tokens(pointer)
    if not tokens:
        raise ValueError("cannot remove document root")
    parent: Any = document
    for token in tokens[:-1]:
        parent = parent[token]
    value = parent.pop(tokens[-1])
    if not isinstance(value, list):
        raise ValueError(f"compact omission is not a row list: {pointer}")
    return len(value), value


def build_compact_summary(
    result: Mapping[str, Any],
    *,
    source_record: Mapping[str, Any],
    raw_archive_record: Mapping[str, Any],
    gate3_lock_sha256: str,
) -> dict[str, Any]:
    """Return a lossless-for-selectors projection without raw seed-row blocks."""

    compact = copy.deepcopy(dict(result))
    omitted: list[dict[str, Any]] = []
    for pointer in RAW_SECTION_PATHS:
        count, _ = _remove_path(compact, pointer)
        omitted.append(
            {
                "json_pointer": pointer,
                "row_count": count,
                "retained_in_complete_archive": True,
            }
        )
    registry = compact.get("method_track_registry")
    if not isinstance(registry, Mapping):
        raise ValueError("held-out method-track registry is absent")
    compact["promotion"] = {
        "document_role": "selector-compatible compact projection",
        "gate3_lock_sha256": gate3_lock_sha256,
        "source": dict(source_record),
        "complete_raw_archive": dict(raw_archive_record),
        "omitted_raw_sections": omitted,
        "promotion_audit": {
            "base_selector_count": 448,
            "selected_method_track_pairs": len(registry.get("selections", [])),
            "excluded_method_track_pairs": len(registry.get("exclusions", [])),
            "omitted_raw_row_count": sum(row["row_count"] for row in omitted),
            "all_base_selectors_resolvable": True,
            "negative_tie_adverse_and_failure_evidence_preserved": True,
        },
    }
    content = copy.deepcopy(compact)
    compact["promotion"]["promoted_content_sha256"] = _sha256(
        canonical_json_bytes(content)
    )
    return compact


def validate_compact_summary(
    compact: Mapping[str, Any],
    *,
    selectors: Mapping[str, Any],
) -> dict[str, Any]:
    promotion = compact.get("promotion")
    if not isinstance(promotion, Mapping):
        raise ValueError("compact promotion record is absent")
    content = copy.deepcopy(dict(compact))
    mutable_promotion = dict(content["promotion"])
    recorded = mutable_promotion.pop("promoted_content_sha256", None)
    content["promotion"] = mutable_promotion
    if recorded != _sha256(canonical_json_bytes(content)):
        raise ValueError("compact promoted-content checksum mismatch")
    for pointer in RAW_SECTION_PATHS:
        try:
            _resolve_pointer(compact, pointer)
        except ValueError:
            pass
        else:
            raise ValueError(f"raw row section leaked into compact result: {pointer}")
    rows = selectors.get("selectors")
    if (
        not isinstance(rows, list)
        or selectors.get("selector_count") != len(rows)
        or len(rows) != 448
    ):
        raise ValueError("base selector registry does not contain 448 rows")
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("base selector row is malformed")
        _resolve_pointer(compact, str(row["json_pointer"]))
    return {
        "status": "pass",
        "base_selector_count": len(rows),
        "promoted_content_sha256": recorded,
    }


def _walk_numeric(
    value: Any,
    *,
    pointer: str = "",
) -> Iterator[tuple[str, int | float]]:
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, int):
        yield pointer, value
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("claim source contains a non-finite number")
        yield pointer, value
        return
    if isinstance(value, Mapping):
        for key in sorted(value):
            if key in NUMERIC_WALK_SKIP_KEYS:
                continue
            child = f"{pointer}/{_pointer_escape(str(key))}"
            yield from _walk_numeric(value[key], pointer=child)
        return
    if isinstance(value, list):
        for index, child_value in enumerate(value):
            yield from _walk_numeric(
                child_value,
                pointer=f"{pointer}/{index}",
            )


def _claim_suffix(pointer: str) -> str:
    tokens = _json_pointer_tokens(pointer)
    return ".".join(token.replace(" ", "_") for token in tokens)


def _render_number(value: int | float) -> tuple[str, str]:
    if isinstance(value, int):
        return str(value), "integer"
    if value == 0:
        return "0", "exact-zero"
    absolute = abs(value)
    if absolute >= 100:
        rendered = f"{value:.2f}"
        rule = "round-half-even:2-decimals"
    elif absolute >= 1:
        rendered = f"{value:.3f}"
        rule = "round-half-even:3-decimals"
    elif absolute >= 0.01:
        rendered = f"{value:.4f}"
        rule = "round-half-even:4-decimals"
    elif absolute >= 0.001:
        rendered = f"{value:.5f}"
        rule = "round-half-even:5-decimals"
    else:
        rendered = f"{value:.2e}"
        rule = "scientific:3-significant-digits"
    return rendered, rule


def _base_selector_records(
    selectors: Mapping[str, Any],
) -> list[dict[str, str]]:
    rows = selectors.get("selectors")
    if not isinstance(rows, list):
        raise ValueError("base selector rows are absent")
    records: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("base selector row is malformed")
        records.append(
            {
                "id": str(row["id"]),
                "kind": str(row["kind"]),
                "source_id": "heldout_summary",
                "json_pointer": str(row["json_pointer"]),
                "gate3_base_selector": str(row["id"]),
            }
        )
    return records


def _extension_selectors(
    runtime: Mapping[str, Any],
) -> list[dict[str, str]]:
    sizes = runtime.get("sizes")
    if not isinstance(sizes, list) or len(sizes) != 3:
        raise ValueError("runtime size summaries are absent")
    return [
        {
            "id": "gate1.protocol",
            "kind": "gate_lock_extension",
            "source_id": "gate1_lock",
            "json_pointer": "/protocol",
        },
        {
            "id": "gate1.data_contract",
            "kind": "gate_lock_extension",
            "source_id": "gate1_lock",
            "json_pointer": "/data_contract",
        },
        {
            "id": "gate2.selection",
            "kind": "gate_lock_extension",
            "source_id": "gate2_lock",
            "json_pointer": "/selected_configs",
        },
        {
            "id": "gate3.coverage",
            "kind": "gate_lock_extension",
            "source_id": "gate3_lock",
            "json_pointer": "/coverage",
        },
        {
            "id": "gate3.retention",
            "kind": "gate_lock_extension",
            "source_id": "gate3_lock",
            "json_pointer": "/retention_audit",
        },
        {
            "id": "promotion.audit",
            "kind": "promotion_extension",
            "source_id": "heldout_summary",
            "json_pointer": "/promotion/promotion_audit",
        },
        {
            "id": "data.quality",
            "kind": "data_extension",
            "source_id": "data_quality",
            "json_pointer": "",
        },
        {
            "id": "data.distribution.overall",
            "kind": "data_extension",
            "source_id": "data_distribution",
            "json_pointer": "/overall",
        },
        {
            "id": "runtime.contract",
            "kind": "runtime_extension",
            "source_id": "runtime",
            "json_pointer": "/benchmark_contract",
        },
        {
            "id": "runtime.packet",
            "kind": "runtime_extension",
            "source_id": "runtime",
            "json_pointer": "/packet",
        },
        *[
            {
                "id": f"runtime.size.{row['n_events']}",
                "kind": "runtime_extension",
                "source_id": "runtime",
                "json_pointer": f"/sizes/{index}",
            }
            for index, row in enumerate(sizes)
        ],
    ]


def build_claim_catalog(
    *,
    compact: Mapping[str, Any],
    base_selectors: Mapping[str, Any],
    source_documents: Mapping[str, Mapping[str, Any]],
    source_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build every paper-eligible numeric leaf from locked selector roots."""

    selector_rows = _base_selector_records(base_selectors)
    selector_rows.extend(_extension_selectors(source_documents["runtime"]))
    claims: list[dict[str, Any]] = []
    selector_ids: set[str] = set()
    claim_ids: set[str] = set()
    documents: dict[str, Mapping[str, Any]] = dict(source_documents)
    documents["heldout_summary"] = compact
    for selector in selector_rows:
        selector_id = selector["id"]
        if selector_id in selector_ids:
            raise ValueError(f"duplicate selector id: {selector_id}")
        selector_ids.add(selector_id)
        source_id = selector["source_id"]
        if source_id not in documents:
            raise ValueError(f"selector source is absent: {source_id}")
        selected = _resolve_pointer(
            documents[source_id],
            selector["json_pointer"],
        )
        for relative_pointer, value in _walk_numeric(selected):
            suffix = _claim_suffix(relative_pointer)
            claim_id = selector_id if not suffix else f"{selector_id}.{suffix}"
            if claim_id in claim_ids:
                raise ValueError(f"duplicate claim id: {claim_id}")
            claim_ids.add(claim_id)
            rendered, rounding = _render_number(value)
            claims.append(
                {
                    "id": claim_id,
                    "selector_id": selector_id,
                    "source_id": source_id,
                    "json_pointer": _join_pointer(
                        selector["json_pointer"],
                        relative_pointer,
                    ),
                    "raw_value": value,
                    "rendered_value": rendered,
                    "rounding": rounding,
                    "required_disclosure": (
                        claim_id in REQUIRED_DISCLOSURE_CLAIMS
                    ),
                    "consumer_contract": (
                        "paper values must use "
                        f"\\RevisionClaim{{{claim_id}}}"
                    ),
                }
            )
    missing = sorted(REQUIRED_DISCLOSURE_CLAIMS - claim_ids)
    if missing:
        raise ValueError(
            "required adverse/neutral disclosure claims are absent: "
            + ", ".join(missing)
        )
    claims.sort(key=lambda row: row["id"])
    selector_rows.sort(key=lambda row: row["id"])
    payload: dict[str, Any] = {
        "schema_version": "revision-claim-selectors-v1",
        "scope": (
            "numeric leaves reachable from Gate-3 base selectors and "
            "locked data/runtime/gate extensions"
        ),
        "sources": list(source_records),
        "base_selector_registry": {
            "path": _relative(DEFAULT_BASE_SELECTORS),
            "selector_count": base_selectors["selector_count"],
            "selector_content_sha256": base_selectors[
                "selector_content_sha256"
            ],
        },
        "selectors": selector_rows,
        "selector_count": len(selector_rows),
        "claims": claims,
        "claim_count": len(claims),
        "required_disclosure_claims": sorted(REQUIRED_DISCLOSURE_CLAIMS),
        "required_disclosure_count": len(REQUIRED_DISCLOSURE_CLAIMS),
        "consumer_contract": {
            "latex_lookup": r"\RevisionClaim{claim.id}",
            "unregistered_quantitative_manuscript_values_forbidden": True,
            "raw_seed_rows_available_in_complete_archive": True,
        },
    }
    content = copy.deepcopy(payload)
    payload["claim_catalog_content_sha256"] = _sha256(
        canonical_json_bytes(content)
    )
    return payload


def validate_claim_catalog(
    catalog: Mapping[str, Any],
    *,
    source_documents: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    content = copy.deepcopy(dict(catalog))
    recorded = content.pop("claim_catalog_content_sha256", None)
    if recorded != _sha256(canonical_json_bytes(content)):
        raise ValueError("claim-catalog content checksum mismatch")
    claims = catalog.get("claims")
    selectors = catalog.get("selectors")
    if (
        not isinstance(claims, list)
        or not isinstance(selectors, list)
        or catalog.get("claim_count") != len(claims)
        or catalog.get("selector_count") != len(selectors)
    ):
        raise ValueError("claim catalog counts are inconsistent")
    selector_ids = {
        row.get("id")
        for row in selectors
        if isinstance(row, Mapping)
    }
    if len(selector_ids) != len(selectors):
        raise ValueError("claim catalog selector ids are not unique")
    claim_ids: set[str] = set()
    for row in claims:
        if not isinstance(row, Mapping):
            raise ValueError("claim row is malformed")
        claim_id = row.get("id")
        if not isinstance(claim_id, str) or claim_id in claim_ids:
            raise ValueError("claim ids are absent or duplicated")
        claim_ids.add(claim_id)
        if row.get("selector_id") not in selector_ids:
            raise ValueError(f"claim selector is unresolved: {claim_id}")
        source_id = row.get("source_id")
        pointer = row.get("json_pointer")
        if (
            not isinstance(source_id, str)
            or source_id not in source_documents
            or not isinstance(pointer, str)
        ):
            raise ValueError(f"claim source is unresolved: {claim_id}")
        observed = _resolve_pointer(source_documents[source_id], pointer)
        if (
            isinstance(observed, bool)
            or not isinstance(observed, (int, float))
            or observed != row.get("raw_value")
        ):
            raise ValueError(f"claim raw value differs at {claim_id}")
        rendered, rounding = _render_number(observed)
        if (
            row.get("rendered_value") != rendered
            or row.get("rounding") != rounding
        ):
            raise ValueError(f"claim rendering differs at {claim_id}")
    if not REQUIRED_DISCLOSURE_CLAIMS.issubset(claim_ids):
        raise ValueError("required adverse/neutral claim coverage is incomplete")
    return {
        "status": "pass",
        "selector_count": len(selectors),
        "claim_count": len(claims),
        "required_disclosure_count": len(REQUIRED_DISCLOSURE_CLAIMS),
        "claim_catalog_content_sha256": recorded,
    }


def _latex_macros(catalog: Mapping[str, Any], *, catalog_sha256: str) -> bytes:
    lines = [
        "% Generated exclusively by demo.experiments.promote_results.",
        f"% Claim selector file SHA-256: {catalog_sha256}",
        r"\providecommand{\RevisionClaim}[1]{%",
        r"  \ifcsname revisionclaim@#1\endcsname",
        r"    \csname revisionclaim@#1\endcsname",
        r"  \else",
        r"    \PackageError{revision-results}{Untraced claim #1}{}%",
        r"  \fi}",
    ]
    for row in catalog["claims"]:
        lines.append(
            "\\expandafter\\def\\csname revisionclaim@"
            f"{row['id']}\\endcsname{{{row['rendered_value']}}}"
        )
    lines.append("")
    return "\n".join(lines).encode("utf-8")


def _traceability_markdown(
    *,
    source_records: Sequence[Mapping[str, Any]],
    catalog: Mapping[str, Any],
    compact_validation: Mapping[str, Any],
    gate3_lock: Mapping[str, Any],
) -> bytes:
    claims_by_id = {row["id"]: row for row in catalog["claims"]}
    lines = [
        "# Revision result traceability",
        "",
        "This document is generated by `demo.experiments.promote_results`; "
        "the promoted JSON, selector catalogs, macro file, and result lock "
        "must not be edited manually.",
        "",
        "## Locked sources",
        "",
        "| Source | Path | SHA-256 |",
        "|---|---|---|",
    ]
    for source in source_records:
        lines.append(
            f"| `{source['id']}` | `{source['path']}` | "
            f"`{source['sha256']}` |"
        )
    lines.extend(
        [
            "",
            "## Coverage",
            "",
            f"- Gate-3 base selectors: "
            f"{compact_validation['base_selector_count']}.",
            f"- Selector roots including locked extensions: "
            f"{catalog['selector_count']}.",
            f"- Mechanically resolvable numeric claims: "
            f"{catalog['claim_count']}.",
            f"- Mandatory adverse/neutral disclosures: "
            f"{catalog['required_disclosure_count']}.",
            (
                "- Held-out coverage: "
                f"{gate3_lock['coverage']['test_seed_count']} test seeds, "
                f"{gate3_lock['coverage']['selected_method_seed_rows']} "
                "selected method-seed rows, and "
                f"{gate3_lock['coverage']['exclusion_seed_rows']} retained "
                "exclusion rows."
            ),
            (
                "- Factorial density-unmatched cells retained: "
                f"{gate3_lock['retention_audit']['factorial_density_match_failures']}."
            ),
            "- The complete 61-MB-class canonical X0 JSON is preserved "
            "losslessly in the promoted `.json.gz` archive; the compact JSON "
            "omits only enumerated raw-row blocks and resolves all 448 base "
            "selectors.",
            "",
            "## Mandatory adverse and neutral evidence",
            "",
            "| Claim ID | Raw value | Paper rendering |",
            "|---|---:|---:|",
        ]
    )
    for claim_id in sorted(REQUIRED_DISCLOSURE_CLAIMS):
        row = claims_by_id[claim_id]
        lines.append(
            f"| `{claim_id}` | `{row['raw_value']}` | "
            f"`{row['rendered_value']}` |"
        )
    lines.extend(
        [
            "",
            "## Manuscript contract",
            "",
            "Every empirical number in `paper/main.tex` must be emitted as "
            "`\\RevisionClaim{claim.id}` from "
            "`paper/generated/revision_results.tex`. The final audit resolves "
            "every used ID against `claim-selectors.json`; a literal, "
            "unregistered result is a Gate-4 failure. Mathematical constants, "
            "equation labels, citation years, and explicitly identified "
            "protocol constants are audited separately against their source "
            "files.",
            "",
            "No selector points to a rejected run. Negative, tied, adverse, "
            "failed, and infeasible outcomes remain represented in the locked "
            "source and promotion audit.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def _artifact_record(path: Path, payload: bytes) -> dict[str, Any]:
    return {
        "path": _relative(path),
        "sha256": _sha256(payload),
        "bytes": len(payload),
    }


def _exclusive_transaction(payloads: Sequence[tuple[Path, bytes]]) -> None:
    destinations = [path.resolve() for path, _ in payloads]
    if len(destinations) != len(set(destinations)):
        raise ValueError("promotion transaction contains duplicate destinations")
    existing = [path for path in destinations if path.exists()]
    if existing:
        raise FileExistsError(
            "refusing to replace existing promoted outputs: "
            + ", ".join(_relative(path) for path in existing)
        )
    created: list[Path] = []
    try:
        for destination, payload in payloads:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(payload)
            created.append(destination)
        for destination, payload in payloads:
            if destination.read_bytes() != payload:
                raise ValueError(f"post-write verification failed: {destination}")
    except Exception:
        for destination in reversed(created):
            try:
                destination.unlink()
            except FileNotFoundError:
                pass
        raise


def promote(
    *,
    runtime_result: Path | str = DEFAULT_RUNTIME_RESULT,
) -> tuple[Path, ...]:
    """Validate and exclusively create the complete G0 promotion transaction."""

    if any(path.exists() for path in PROMOTED_TARGETS):
        existing = [path for path in PROMOTED_TARGETS if path.exists()]
        raise FileExistsError(
            "refusing to replace an existing result promotion: "
            + ", ".join(_relative(path) for path in existing)
        )

    gate3_payload, gate3 = _canonical_object(
        DEFAULT_GATE3_LOCK,
        label="Gate-3 lock",
    )
    accepted = gate3.get("accepted_run")
    if not isinstance(accepted, Mapping):
        raise ValueError("Gate-3 accepted run is absent")
    manifest_path = REPOSITORY_ROOT / str(accepted["manifest"])
    result_path = manifest_path.parent / str(accepted["result"]["path"])
    validated = validate_candidate(result_path)
    _validate_gate3_binding(gate3, validated)

    raw_result_payload, raw_result = _canonical_object(
        Path(validated["result_path"]),
        label="held-out source result",
    )
    base_selector_payload, base_selectors = _canonical_object(
        Path(validated["selector_path"]),
        label="held-out source selectors",
    )
    if (
        _sha256(raw_result_payload) != validated["result_sha256"]
        or _sha256(base_selector_payload) != validated["selector_sha256"]
    ):
        raise ValueError("held-out source bytes changed after Gate-3 validation")

    raw_archive_payload = gzip.compress(
        raw_result_payload,
        compresslevel=9,
        mtime=0,
    )
    if gzip.decompress(raw_archive_payload) != raw_result_payload:
        raise ValueError("complete held-out archive does not round-trip")
    raw_archive_record = {
        **_artifact_record(DEFAULT_RAW_ARCHIVE, raw_archive_payload),
        "compression": "gzip level 9, mtime 0",
        "decompressed_sha256": _sha256(raw_result_payload),
        "decompressed_bytes": len(raw_result_payload),
    }
    source_record = {
        "run_id": validated["run_id"],
        "manifest_path": _relative(Path(validated["manifest_path"])),
        "manifest_sha256": validated["manifest_sha256"],
        "result_path": _relative(Path(validated["result_path"])),
        "result_sha256": validated["result_sha256"],
        "artifact_content_sha256": validated["artifact_content_sha256"],
        "selector_path": _relative(Path(validated["selector_path"])),
        "selector_sha256": validated["selector_sha256"],
        "selector_content_sha256": validated["selector_content_sha256"],
    }
    compact = build_compact_summary(
        raw_result,
        source_record=source_record,
        raw_archive_record=raw_archive_record,
        gate3_lock_sha256=_sha256(gate3_payload),
    )
    compact_validation = validate_compact_summary(
        compact,
        selectors=base_selectors,
    )
    compact_payload = canonical_json_bytes(compact)

    runtime_payload, runtime, runtime_manifest_path = _validate_runtime_result(
        Path(runtime_result)
    )
    (
        (distribution_payload, distribution, distribution_path),
        (quality_payload, quality, quality_path),
        gate1_manifest_path,
    ) = _gate1_ancillary_sources()
    gate1_payload, gate1 = _sealed_json_object(
        DEFAULT_GATE1_LOCK,
        label="Gate-1 lock",
    )
    gate2_payload, gate2 = _sealed_json_object(
        DEFAULT_GATE2_LOCK,
        label="Gate-2 lock",
    )

    source_records: list[dict[str, Any]] = [
        {
            "id": "heldout_summary",
            **_artifact_record(DEFAULT_SUMMARY, compact_payload),
            "origin": source_record,
        },
        {
            "id": "heldout_complete_archive",
            **raw_archive_record,
        },
        {
            "id": "heldout_base_selectors",
            **_artifact_record(DEFAULT_BASE_SELECTORS, base_selector_payload),
            "source_selector_content_sha256": validated[
                "selector_content_sha256"
            ],
        },
        {
            "id": "runtime",
            **_artifact_record(DEFAULT_RUNTIME_PROMOTED, runtime_payload),
            "origin_manifest": _relative(runtime_manifest_path),
            "origin_manifest_sha256": file_sha256(runtime_manifest_path),
        },
        {
            "id": "data_distribution",
            **_artifact_record(
                DEFAULT_DISTRIBUTION_PROMOTED,
                distribution_payload,
            ),
            "origin": _relative(distribution_path),
            "origin_manifest": _relative(gate1_manifest_path),
        },
        {
            "id": "data_quality",
            **_artifact_record(DEFAULT_QUALITY_PROMOTED, quality_payload),
            "origin": _relative(quality_path),
            "origin_manifest": _relative(gate1_manifest_path),
        },
        {
            "id": "gate1_lock",
            "path": _relative(DEFAULT_GATE1_LOCK),
            "sha256": _sha256(gate1_payload),
            "bytes": len(gate1_payload),
        },
        {
            "id": "gate2_lock",
            "path": _relative(DEFAULT_GATE2_LOCK),
            "sha256": _sha256(gate2_payload),
            "bytes": len(gate2_payload),
        },
        {
            "id": "gate3_lock",
            "path": _relative(DEFAULT_GATE3_LOCK),
            "sha256": _sha256(gate3_payload),
            "bytes": len(gate3_payload),
        },
    ]
    claim_documents = {
        "heldout_summary": compact,
        "runtime": runtime,
        "data_distribution": distribution,
        "data_quality": quality,
        "gate1_lock": gate1,
        "gate2_lock": gate2,
        "gate3_lock": gate3,
    }
    catalog = build_claim_catalog(
        compact=compact,
        base_selectors=base_selectors,
        source_documents=claim_documents,
        source_records=source_records,
    )
    catalog_validation = validate_claim_catalog(
        catalog,
        source_documents=claim_documents,
    )
    catalog_payload = canonical_json_bytes(catalog)
    latex_payload = _latex_macros(
        catalog,
        catalog_sha256=_sha256(catalog_payload),
    )
    traceability_payload = _traceability_markdown(
        source_records=source_records,
        catalog=catalog,
        compact_validation=compact_validation,
        gate3_lock=gate3,
    )

    promoted_payloads = (
        (DEFAULT_SUMMARY, compact_payload),
        (DEFAULT_RAW_ARCHIVE, raw_archive_payload),
        (DEFAULT_BASE_SELECTORS, base_selector_payload),
        (DEFAULT_RUNTIME_PROMOTED, runtime_payload),
        (DEFAULT_DISTRIBUTION_PROMOTED, distribution_payload),
        (DEFAULT_QUALITY_PROMOTED, quality_payload),
        (DEFAULT_CLAIM_SELECTORS, catalog_payload),
        (DEFAULT_TRACEABILITY, traceability_payload),
        (DEFAULT_LATEX_MACROS, latex_payload),
    )
    promoted_records = {
        path.name: _artifact_record(path, payload)
        for path, payload in promoted_payloads
    }
    result_lock = {
        "schema_version": 1,
        "gate": "G0 result promotion",
        "status": "locked",
        "locked_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": (
            "single Gate-3-approved held-out source plus audited "
            "Gate-1/Exp22 ancillary evidence"
        ),
        "promotion_script": {
            "path": _relative(Path(__file__)),
            "sha256": file_sha256(Path(__file__)),
        },
        "gate3_binding": {
            "path": _relative(DEFAULT_GATE3_LOCK),
            "sha256": _sha256(gate3_payload),
            "accepted_run_id": validated["run_id"],
            "accepted_manifest_sha256": validated["manifest_sha256"],
            "accepted_result_sha256": validated["result_sha256"],
            "accepted_artifact_content_sha256": validated[
                "artifact_content_sha256"
            ],
            "accepted_selector_sha256": validated["selector_sha256"],
            "accepted_selector_content_sha256": validated[
                "selector_content_sha256"
            ],
        },
        "ancillary_bindings": {
            "gate1_manifest": {
                "path": _relative(gate1_manifest_path),
                "sha256": file_sha256(gate1_manifest_path),
            },
            "runtime_manifest": {
                "path": _relative(runtime_manifest_path),
                "sha256": file_sha256(runtime_manifest_path),
            },
        },
        "promoted_artifacts": promoted_records,
        "coverage": {
            **gate3["coverage"],
            "selected_method_track_pairs": len(
                raw_result["method_track_registry"]["selections"]
            ),
            "excluded_method_track_pairs": len(
                raw_result["method_track_registry"]["exclusions"]
            ),
            "factorial_density_match_failures": gate3["retention_audit"][
                "factorial_density_match_failures"
            ],
        },
        "traceability": {
            "base_selector_count": compact_validation["base_selector_count"],
            "selector_root_count": catalog_validation["selector_count"],
            "numeric_claim_count": catalog_validation["claim_count"],
            "required_disclosure_count": catalog_validation[
                "required_disclosure_count"
            ],
            "all_base_selectors_resolve": True,
            "all_claim_values_and_rounding_recomputed": True,
            "complete_archive_round_trip": True,
            "negative_tie_adverse_failure_and_exclusion_evidence_retained": True,
        },
        "validation": {
            "gate3_candidate_revalidation": "pass",
            "gate3_and_upstream_binding": "pass",
            "rejected_run_exclusion": "pass",
            "compact_selector_resolution": "pass",
            "complete_archive_round_trip": "pass",
            "gate1_ancillary_binding": "pass",
            "runtime_manifest_and_equivalence": "pass",
            "claim_selector_and_rendering": "pass",
            "exclusive_transaction": "pass",
            "validation_errors": [],
        },
        "reopen_conditions": [
            "Gate-3 accepted source or upstream binding changes",
            "promoted artifact checksum mismatch",
            "complete archive decompression mismatch",
            "base or extension selector resolution failure",
            "claim rendering or mandatory adverse-disclosure coverage failure",
            "confirmed upstream scientific defect requiring a gate reopen",
        ],
    }
    result_lock_payload = canonical_json_bytes(result_lock)
    _exclusive_transaction(
        (*promoted_payloads, (DEFAULT_RESULT_LOCK, result_lock_payload))
    )
    return PROMOTED_TARGETS


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime-result",
        type=Path,
        default=DEFAULT_RUNTIME_RESULT,
        help="accepted Exp22 table (default is the Gate-2-audited run)",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    outputs = promote(runtime_result=args.runtime_result)
    print(
        json.dumps(
            {
                "status": "locked",
                "result_lock": _relative(DEFAULT_RESULT_LOCK),
                "outputs": [_relative(path) for path in outputs],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "build_claim_catalog",
    "build_compact_summary",
    "promote",
    "validate_claim_catalog",
    "validate_compact_summary",
]
