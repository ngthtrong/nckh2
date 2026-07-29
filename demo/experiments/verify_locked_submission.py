"""Read-only verification of the locked revision submission.

This module validates already-promoted evidence and publication outputs.  It
never executes an experiment, opens a frozen dataset, or mutates a promoted
artifact.  The optional ``--report`` output is the only write operation and is
performed only when explicitly requested by the caller.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable, Mapping, Sequence

from demo.experiments.pre_gate2 import canonical_json_bytes
from demo.experiments.promote_results import (
    RAW_SECTION_PATHS,
    REQUIRED_DISCLOSURE_CLAIMS,
    _latex_macros,
    _resolve_pointer,
    validate_claim_catalog,
    validate_compact_summary,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY_PATH = Path("revision/submission-policy.json")
DEFAULT_RESULT_LOCK_PATH = Path("revision/result-lock.json")
DEFAULT_MANUSCRIPT_PATH = Path("paper/main.tex")
DEFAULT_TEX_LOG_PATH = Path("paper/main.log")
DEFAULT_BIBTEX_LOG_PATH = Path("paper/main.blg")
DEFAULT_FIGURE_ROOT = Path("paper/figures")

EXPECTED_PROMOTED_ARTIFACTS = {
    "claim-selectors.json": "loop/revision/claim-selectors.json",
    "data_distribution_report_v4.json": (
        "demo/results/tables/data_distribution_report_v4.json"
    ),
    "data_quality_summary_v4.json": (
        "demo/results/tables/data_quality_summary_v4.json"
    ),
    "exp22_runtime_repro.json": (
        "demo/results/tables/exp22_runtime_repro.json"
    ),
    "exp23_heldout_evaluation.json.gz": (
        "demo/results/tables/exp23_heldout_evaluation.json.gz"
    ),
    "exp23_heldout_selectors.json": (
        "demo/results/tables/exp23_heldout_selectors.json"
    ),
    "exp23_heldout_summary.json": (
        "demo/results/tables/exp23_heldout_summary.json"
    ),
    "revision_results.tex": "paper/generated/revision_results.tex",
    "traceability.md": "loop/revision/traceability.md",
}

EXPECTED_CLAIM_SOURCE_IDS = frozenset(
    {
        "heldout_summary",
        "heldout_complete_archive",
        "heldout_base_selectors",
        "runtime",
        "data_distribution",
        "data_quality",
        "gate1_lock",
        "gate2_lock",
        "gate3_lock",
    }
)

DEFAULT_STALE_TERM_PATTERNS = (
    (
        "legacy-dataset-cardinality",
        r"\b285\s+(?:events?|reports?|sự\s+kiện)\b",
    ),
    ("single-seed-42", r"\bseed\s*(?:[-:=]\s*)?42\b"),
    ("legacy-demo-v2-path", r"(?<![\w.-])demo/v2(?:/|\b)"),
    ("legacy-pdf-engine", r"\bpdflatex\b"),
    (
        "legacy-paper-title",
        (
            r"Clustering\s+and\s+Priority\s+Scoring\s+for\s+"
            r"Flood-Rescue\s+Coordination\s+Using\s+Edge\s+AI"
        ),
    ),
)

DEFAULT_STALE_SCAN_PATHS = (
    Path("README.md"),
    Path("demo/README.md"),
    DEFAULT_MANUSCRIPT_PATH,
)

SUPPORTED_FIGURE_EXTENSIONS = frozenset(
    {".eps", ".jpeg", ".jpg", ".pdf", ".png"}
)

_CLAIM_PATTERN = re.compile(
    r"\\RevisionClaim\s*\{\s*([^{}]+?)\s*\}",
    flags=re.DOTALL,
)
_INPUT_PATTERN = re.compile(
    r"\\(?:input|include)\s*\{\s*([^{}]+?)\s*\}",
    flags=re.DOTALL,
)
_INCLUDEGRAPHICS_PATTERN = re.compile(
    r"\\includegraphics\s*(?:\[[^\]]*\]\s*)?\{\s*([^{}]+?)\s*\}",
    flags=re.DOTALL,
)
_OUTPUT_PAGES_PATTERN = re.compile(
    r"Output written on\s+.+?\s+\((\d+)\s+pages?(?:,|\))",
    flags=re.IGNORECASE,
)
_OVERFULL_PATTERN = re.compile(
    r"Overfull\s+\\[hv]box\s+\(([-+]?\d+(?:\.\d+)?)pt\s+too\s+"
    r"(?:wide|high)\)",
    flags=re.IGNORECASE,
)


class VerificationError(ValueError):
    """A deterministic locked-submission validation failure."""


@dataclass(frozen=True)
class SubmissionPolicy:
    """Validated technical policy used by the verifier."""

    configured: bool
    profile: str
    status: str
    latex_engine: str
    bibliography_engine: str
    build_sequence: tuple[str, ...]
    expected_page_count: int | None
    maximum_overfull_points: float
    allow_underfull_boxes: bool
    require_no_undefined_citations: bool
    require_no_undefined_references: bool
    strict_tex_warnings: bool
    allowed_tex_warning_patterns: tuple[str, ...]
    figure_policy: str
    figure_root: Path
    allowed_orphan_figures: tuple[str, ...]
    stale_scan_paths: tuple[Path, ...]
    stale_term_patterns: tuple[tuple[str, str], ...]
    external_submission_inputs: Mapping[str, Any]


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _content_json_bytes(value: Any) -> bytes:
    """Canonical form used by Exp23 content hashes (not artifact bytes)."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _read_json_object(
    path: Path,
    *,
    label: str,
    require_canonical: bool = False,
) -> tuple[bytes, dict[str, Any]]:
    try:
        payload = path.read_bytes()
        value = json.loads(payload)
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise VerificationError(f"{label} is absent or invalid: {path}") from exc
    if not isinstance(value, dict):
        raise VerificationError(f"{label} must be a JSON object")
    if require_canonical and payload != canonical_json_bytes(value):
        raise VerificationError(f"{label} is not canonical JSON")
    return payload, value


def _locked_path(repository_root: Path, raw_path: Any, *, label: str) -> Path:
    if not isinstance(raw_path, str) or not raw_path:
        raise VerificationError(f"{label} path is absent")
    pure = PurePosixPath(raw_path)
    if pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
        raise VerificationError(f"{label} path is unsafe: {raw_path!r}")
    root = repository_root.resolve()
    resolved = (root / Path(*pure.parts)).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise VerificationError(
            f"{label} path escapes the repository: {raw_path!r}"
        ) from exc
    return resolved


def _relative_path(repository_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repository_root.resolve()).as_posix()
    except ValueError as exc:
        raise VerificationError(f"path is outside repository: {path}") from exc


def _require_mapping(value: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise VerificationError(f"{label} must be an object")
    return value


def _require_list(value: Any, *, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise VerificationError(f"{label} must be an array")
    return value


def _verify_file_record(
    repository_root: Path,
    record: Mapping[str, Any],
    *,
    label: str,
) -> Path:
    path = _locked_path(repository_root, record.get("path"), label=label)
    try:
        payload = path.read_bytes()
    except FileNotFoundError as exc:
        raise VerificationError(f"{label} is absent: {path}") from exc
    if record.get("bytes") != len(payload):
        raise VerificationError(f"{label} byte count differs")
    if record.get("sha256") != _sha256(payload):
        raise VerificationError(f"{label} SHA-256 differs")
    return path


def _verify_checksum_path(
    repository_root: Path,
    record: Mapping[str, Any],
    *,
    label: str,
) -> Path:
    path = _locked_path(repository_root, record.get("path"), label=label)
    try:
        payload = path.read_bytes()
    except FileNotFoundError as exc:
        raise VerificationError(f"{label} is absent: {path}") from exc
    if record.get("sha256") != _sha256(payload):
        raise VerificationError(f"{label} SHA-256 differs")
    return path


def _policy_string(
    value: Any,
    *,
    label: str,
    expected: str | None = None,
) -> str:
    if not isinstance(value, str) or not value:
        raise VerificationError(f"{label} must be a non-empty string")
    if expected is not None and value != expected:
        raise VerificationError(f"{label} must be {expected!r}")
    return value


def load_submission_policy(path: Path | str) -> SubmissionPolicy:
    """Load the local technical policy without inventing venue constraints."""

    source = Path(path).resolve()
    _, policy = _read_json_object(source, label="submission policy")
    if policy.get("schema_version") != 1:
        raise VerificationError("unsupported submission-policy schema")
    status = _policy_string(policy.get("status"), label="policy status")
    profile = _policy_string(policy.get("profile"), label="policy profile")
    paper = _require_mapping(
        policy.get("paper_policy"),
        label="paper policy",
    )
    artifact = _require_mapping(
        policy.get("artifact_policy"),
        label="artifact policy",
    )
    external = _require_mapping(
        policy.get("external_submission_inputs", {}),
        label="external submission inputs",
    )

    latex_engine = _policy_string(
        paper.get("latex_engine"),
        label="LaTeX engine",
        expected="xelatex",
    )
    bibliography_engine = _policy_string(
        paper.get("bibliography_engine"),
        label="bibliography engine",
        expected="bibtex",
    )
    build_sequence_raw = _require_list(
        paper.get("build_sequence"),
        label="paper build sequence",
    )
    if any(not isinstance(row, str) or not row for row in build_sequence_raw):
        raise VerificationError("paper build sequence is malformed")
    build_sequence = tuple(build_sequence_raw)
    if build_sequence != ("xelatex", "bibtex", "xelatex", "xelatex"):
        raise VerificationError("paper build sequence is not the locked sequence")

    expected_page_count = paper.get("expected_page_count")
    if expected_page_count is not None and (
        isinstance(expected_page_count, bool)
        or not isinstance(expected_page_count, int)
        or expected_page_count <= 0
    ):
        raise VerificationError("expected page count must be a positive integer")
    maximum_overfull = paper.get("maximum_overfull_points")
    if (
        isinstance(maximum_overfull, bool)
        or not isinstance(maximum_overfull, (int, float))
        or maximum_overfull < 0
    ):
        raise VerificationError(
            "maximum overfull points must be a non-negative number"
        )

    for key in (
        "allow_underfull_boxes",
        "require_no_undefined_citations",
        "require_no_undefined_references",
    ):
        if not isinstance(paper.get(key), bool):
            raise VerificationError(f"paper policy {key!r} must be boolean")

    if artifact.get("heldout_reexecution_permitted") is not False:
        raise VerificationError("submission policy must prohibit held-out reruns")
    if artifact.get("deterministic_json_comparison") != "byte-exact":
        raise VerificationError("submission policy must require byte-exact JSON")
    figure_value = artifact.get("figure_policy")
    if isinstance(figure_value, str):
        figure_policy = figure_value
        figure_root = DEFAULT_FIGURE_ROOT
        allowed_orphans: tuple[str, ...] = ()
    elif isinstance(figure_value, Mapping):
        figure_policy = _policy_string(
            figure_value.get("mode"),
            label="figure policy mode",
        )
        root_raw = figure_value.get(
            "root",
            DEFAULT_FIGURE_ROOT.as_posix(),
        )
        if not isinstance(root_raw, str) or not root_raw:
            raise VerificationError("figure root must be a relative path")
        figure_root = Path(root_raw)
        orphans_raw = figure_value.get("allowed_orphans", [])
        if not isinstance(orphans_raw, list) or any(
            not isinstance(row, str) or not row for row in orphans_raw
        ):
            raise VerificationError("allowed figure orphans are malformed")
        allowed_orphans = tuple(orphans_raw)
    else:
        raise VerificationError("artifact figure policy is absent")

    warning_patterns_raw = paper.get("allowed_warning_patterns", [])
    if not isinstance(warning_patterns_raw, list) or any(
        not isinstance(row, str) or not row for row in warning_patterns_raw
    ):
        raise VerificationError("allowed TeX warning patterns are malformed")
    for pattern in warning_patterns_raw:
        try:
            re.compile(pattern)
        except re.error as exc:
            raise VerificationError(
                f"invalid TeX warning allowlist regex: {pattern!r}"
            ) from exc

    stale_policy = policy.get("stale_term_policy", {})
    if not isinstance(stale_policy, Mapping):
        raise VerificationError("stale-term policy must be an object")
    stale_paths_raw = stale_policy.get(
        "paths",
        [path.as_posix() for path in DEFAULT_STALE_SCAN_PATHS],
    )
    if not isinstance(stale_paths_raw, list) or any(
        not isinstance(row, str) or not row for row in stale_paths_raw
    ):
        raise VerificationError("stale-term scan paths are malformed")
    patterns_raw = stale_policy.get("patterns")
    if patterns_raw is None:
        stale_patterns = DEFAULT_STALE_TERM_PATTERNS
    else:
        if not isinstance(patterns_raw, list):
            raise VerificationError("stale-term patterns must be an array")
        parsed_patterns: list[tuple[str, str]] = []
        for index, row in enumerate(patterns_raw):
            if not isinstance(row, Mapping):
                raise VerificationError(
                    f"stale-term pattern {index} must be an object"
                )
            identifier = row.get("id")
            pattern = row.get("pattern")
            if (
                not isinstance(identifier, str)
                or not identifier
                or not isinstance(pattern, str)
                or not pattern
            ):
                raise VerificationError(
                    f"stale-term pattern {index} is malformed"
                )
            try:
                re.compile(pattern, flags=re.IGNORECASE)
            except re.error as exc:
                raise VerificationError(
                    f"invalid stale-term regex: {identifier}"
                ) from exc
            parsed_patterns.append((identifier, pattern))
        stale_patterns = tuple(parsed_patterns)

    strict_warnings = paper.get("strict_tex_warnings", False)
    if not isinstance(strict_warnings, bool):
        raise VerificationError("strict_tex_warnings must be boolean")

    return SubmissionPolicy(
        configured=True,
        profile=profile,
        status=status,
        latex_engine=latex_engine,
        bibliography_engine=bibliography_engine,
        build_sequence=build_sequence,
        expected_page_count=expected_page_count,
        maximum_overfull_points=float(maximum_overfull),
        allow_underfull_boxes=bool(paper["allow_underfull_boxes"]),
        require_no_undefined_citations=bool(
            paper["require_no_undefined_citations"]
        ),
        require_no_undefined_references=bool(
            paper["require_no_undefined_references"]
        ),
        strict_tex_warnings=strict_warnings,
        allowed_tex_warning_patterns=tuple(warning_patterns_raw),
        figure_policy=figure_policy,
        figure_root=figure_root,
        allowed_orphan_figures=allowed_orphans,
        stale_scan_paths=tuple(Path(row) for row in stale_paths_raw),
        stale_term_patterns=tuple(stale_patterns),
        external_submission_inputs=dict(external),
    )


def _fallback_policy() -> SubmissionPolicy:
    return SubmissionPolicy(
        configured=False,
        profile="unconfigured",
        status="absent",
        latex_engine="xelatex",
        bibliography_engine="bibtex",
        build_sequence=("xelatex", "bibtex", "xelatex", "xelatex"),
        expected_page_count=None,
        maximum_overfull_points=5.0,
        allow_underfull_boxes=True,
        require_no_undefined_citations=True,
        require_no_undefined_references=True,
        strict_tex_warnings=False,
        allowed_tex_warning_patterns=(),
        figure_policy="all manuscript figures must be referenced",
        figure_root=DEFAULT_FIGURE_ROOT,
        allowed_orphan_figures=(),
        stale_scan_paths=DEFAULT_STALE_SCAN_PATHS,
        stale_term_patterns=DEFAULT_STALE_TERM_PATTERNS,
        external_submission_inputs={},
    )


def verify_result_lock(
    repository_root: Path | str,
    result_lock_path: Path | str = DEFAULT_RESULT_LOCK_PATH,
) -> dict[str, Any]:
    """Verify the G0 lock, every promoted file, and sealed gate bindings."""

    root = Path(repository_root).resolve()
    lock_path = (
        Path(result_lock_path).resolve()
        if Path(result_lock_path).is_absolute()
        else _locked_path(root, Path(result_lock_path).as_posix(), label="result lock")
    )
    lock_payload, lock = _read_json_object(
        lock_path,
        label="result lock",
        require_canonical=True,
    )
    if (
        lock.get("schema_version") != 1
        or lock.get("gate") != "G0 result promotion"
        or lock.get("status") != "locked"
    ):
        raise VerificationError("result lock is not a locked G0 record")

    promoted = _require_mapping(
        lock.get("promoted_artifacts"),
        label="promoted artifacts",
    )
    if set(promoted) != set(EXPECTED_PROMOTED_ARTIFACTS):
        raise VerificationError("promoted artifact set is not the G0 allowlist")
    promoted_paths: dict[str, str] = {}
    for name, expected_path in EXPECTED_PROMOTED_ARTIFACTS.items():
        record = _require_mapping(
            promoted.get(name),
            label=f"promoted artifact {name}",
        )
        if record.get("path") != expected_path:
            raise VerificationError(f"promoted path differs for {name}")
        _verify_file_record(root, record, label=f"promoted artifact {name}")
        promoted_paths[name] = expected_path

    script = _require_mapping(
        lock.get("promotion_script"),
        label="promotion script binding",
    )
    if script.get("path") != "demo/experiments/promote_results.py":
        raise VerificationError("promotion script path differs")
    _verify_checksum_path(root, script, label="promotion script")

    gate3_binding = _require_mapping(
        lock.get("gate3_binding"),
        label="Gate-3 binding",
    )
    gate3_path = _verify_checksum_path(
        root,
        gate3_binding,
        label="Gate-3 lock",
    )
    _, gate3 = _read_json_object(
        gate3_path,
        label="Gate-3 lock",
        require_canonical=True,
    )
    if (
        gate3.get("gate") != "Gate 3"
        or gate3.get("status") != "locked"
        or gate3.get("schema_version") != 1
    ):
        raise VerificationError("Gate-3 lock is not valid")
    accepted = _require_mapping(
        gate3.get("accepted_run"),
        label="Gate-3 accepted run",
    )
    accepted_result = _require_mapping(
        accepted.get("result"),
        label="Gate-3 accepted result",
    )
    accepted_selectors = _require_mapping(
        accepted.get("selectors"),
        label="Gate-3 accepted selectors",
    )
    accepted_invocation = _require_mapping(
        accepted.get("invocation"),
        label="Gate-3 invocation",
    )
    expected_binding = {
        "accepted_run_id": accepted.get("run_id"),
        "accepted_manifest_sha256": accepted.get("manifest_sha256"),
        "accepted_result_sha256": accepted_result.get("sha256"),
        "accepted_artifact_content_sha256": accepted_result.get(
            "artifact_content_sha256"
        ),
        "accepted_selector_sha256": accepted_selectors.get("sha256"),
        "accepted_selector_content_sha256": accepted_selectors.get(
            "selector_content_sha256"
        ),
    }
    for key, expected in expected_binding.items():
        if gate3_binding.get(key) != expected:
            raise VerificationError(f"result lock differs from Gate 3 at {key}")
    if (
        accepted.get("status") != "succeeded"
        or accepted.get("exit_code") != 0
        or accepted_result.get("status") != "succeeded"
        or accepted_invocation.get("candidate_suite_invocation") != 1
    ):
        raise VerificationError("accepted held-out run was not a single success")

    manifest_path = _locked_path(
        root,
        accepted.get("manifest"),
        label="accepted-run manifest",
    )
    try:
        manifest_payload = manifest_path.read_bytes()
        manifest = json.loads(manifest_payload)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise VerificationError("accepted-run manifest is absent or invalid") from exc
    if _sha256(manifest_payload) != accepted.get("manifest_sha256"):
        raise VerificationError("accepted-run manifest SHA-256 differs")
    if (
        not isinstance(manifest, Mapping)
        or manifest.get("run_id") != accepted.get("run_id")
        or manifest.get("status") != "succeeded"
        or manifest.get("exit_code") != 0
    ):
        raise VerificationError("accepted-run manifest status differs")

    ancillary = _require_mapping(
        lock.get("ancillary_bindings"),
        label="ancillary bindings",
    )
    for name in ("gate1_manifest", "runtime_manifest"):
        record = _require_mapping(
            ancillary.get(name),
            label=f"ancillary {name}",
        )
        _verify_checksum_path(root, record, label=f"ancillary {name}")

    rejected_record = _require_mapping(
        gate3.get("rejected_run_ledger"),
        label="rejected-run ledger",
    )
    rejected_path = _verify_checksum_path(
        root,
        rejected_record,
        label="rejected-run ledger",
    )
    _, rejected = _read_json_object(
        rejected_path,
        label="rejected-run ledger",
    )
    rejected_rows = _require_list(
        rejected.get("runs"),
        label="rejected runs",
    )
    rejected_ids = {
        row.get("run_id")
        for row in rejected_rows
        if isinstance(row, Mapping)
    }
    if rejected_record.get("run_count") != len(rejected_rows):
        raise VerificationError("rejected-run count differs")
    if accepted.get("run_id") in rejected_ids:
        raise VerificationError("accepted run appears in rejected-run ledger")

    validation = _require_mapping(
        lock.get("validation"),
        label="result-lock validation",
    )
    if validation.get("validation_errors") != [] or any(
        value != "pass"
        for key, value in validation.items()
        if key != "validation_errors"
    ):
        raise VerificationError("result lock does not record a clean validation")
    traceability = _require_mapping(
        lock.get("traceability"),
        label="result-lock traceability",
    )
    for flag in (
        "all_base_selectors_resolve",
        "all_claim_values_and_rounding_recomputed",
        "complete_archive_round_trip",
        "negative_tie_adverse_failure_and_exclusion_evidence_retained",
    ):
        if traceability.get(flag) is not True:
            raise VerificationError(f"result-lock traceability flag failed: {flag}")

    return {
        "result_lock_sha256": _sha256(lock_payload),
        "promoted_artifact_count": len(promoted),
        "accepted_run_id": accepted["run_id"],
        "rejected_run_count": len(rejected_rows),
        "promoted_paths": promoted_paths,
    }


def _read_gzip_limited(path: Path, *, byte_limit: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    try:
        with gzip.open(path, "rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > byte_limit:
                    raise VerificationError(
                        "held-out archive exceeds decompression safety limit"
                    )
                chunks.append(chunk)
    except (OSError, EOFError) as exc:
        raise VerificationError("held-out gzip archive is invalid") from exc
    return b"".join(chunks)


def _remove_raw_section(document: dict[str, Any], pointer: str) -> int:
    if not pointer.startswith("/"):
        raise VerificationError(f"raw-section pointer is invalid: {pointer}")
    tokens = [
        token.replace("~1", "/").replace("~0", "~")
        for token in pointer[1:].split("/")
    ]
    parent: Any = document
    try:
        for token in tokens[:-1]:
            parent = parent[token]
        removed = parent.pop(tokens[-1])
    except (KeyError, TypeError) as exc:
        raise VerificationError(f"raw section is absent: {pointer}") from exc
    if not isinstance(removed, list):
        raise VerificationError(f"raw section is not a list: {pointer}")
    return len(removed)


def verify_archive_projection_and_selectors(
    repository_root: Path | str,
) -> dict[str, Any]:
    """Recompute archive, compact-projection, and selector invariants."""

    root = Path(repository_root).resolve()
    _, lock = _read_json_object(
        root / DEFAULT_RESULT_LOCK_PATH,
        label="result lock",
        require_canonical=True,
    )
    promoted = _require_mapping(
        lock.get("promoted_artifacts"),
        label="promoted artifacts",
    )
    archive_record = _require_mapping(
        promoted.get("exp23_heldout_evaluation.json.gz"),
        label="held-out archive record",
    )
    compact_record = _require_mapping(
        promoted.get("exp23_heldout_summary.json"),
        label="held-out compact record",
    )
    selector_record = _require_mapping(
        promoted.get("exp23_heldout_selectors.json"),
        label="held-out selector record",
    )
    archive_path = _verify_file_record(
        root,
        archive_record,
        label="held-out archive",
    )
    compact_path = _verify_file_record(
        root,
        compact_record,
        label="held-out compact result",
    )
    selector_path = _verify_file_record(
        root,
        selector_record,
        label="held-out selectors",
    )

    archive_payload = archive_path.read_bytes()
    if (
        len(archive_payload) < 10
        or archive_payload[:3] != b"\x1f\x8b\x08"
        or int.from_bytes(archive_payload[4:8], "little") != 0
    ):
        raise VerificationError("held-out archive is not deterministic gzip")
    raw_payload = _read_gzip_limited(
        archive_path,
        byte_limit=256 * 1024 * 1024,
    )
    try:
        raw = json.loads(raw_payload)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise VerificationError("held-out archive JSON is invalid") from exc
    if not isinstance(raw, dict) or raw_payload != canonical_json_bytes(raw):
        raise VerificationError("held-out archive JSON is not canonical")
    if gzip.compress(raw_payload, compresslevel=9, mtime=0) != archive_payload:
        raise VerificationError("held-out gzip encoding is not reproducible")

    raw_content = dict(raw)
    recorded_raw_content_hash = raw_content.pop(
        "artifact_content_sha256",
        None,
    )
    computed_raw_content_hash = _sha256(_content_json_bytes(raw_content))
    if recorded_raw_content_hash != computed_raw_content_hash:
        raise VerificationError("held-out artifact content checksum differs")

    compact_payload, compact = _read_json_object(
        compact_path,
        label="held-out compact result",
        require_canonical=True,
    )
    selector_payload, selectors = _read_json_object(
        selector_path,
        label="held-out selectors",
        require_canonical=True,
    )
    selector_content = dict(selectors)
    recorded_selector_content_hash = selector_content.pop(
        "selector_content_sha256",
        None,
    )
    computed_selector_content_hash = _sha256(
        _content_json_bytes(selector_content)
    )
    if recorded_selector_content_hash != computed_selector_content_hash:
        raise VerificationError("selector content checksum differs")
    if selectors.get("source_artifact_content_sha256") != computed_raw_content_hash:
        raise VerificationError("selectors do not bind the raw held-out result")

    selector_rows = _require_list(
        selectors.get("selectors"),
        label="held-out selector rows",
    )
    if selectors.get("selector_count") != len(selector_rows) or len(
        selector_rows
    ) != 448:
        raise VerificationError("held-out selector count differs from 448")
    selector_ids: set[str] = set()
    for row in selector_rows:
        if not isinstance(row, Mapping):
            raise VerificationError("held-out selector row is malformed")
        identifier = row.get("id")
        pointer = row.get("json_pointer")
        if (
            not isinstance(identifier, str)
            or not identifier
            or identifier in selector_ids
            or not isinstance(row.get("kind"), str)
            or not isinstance(pointer, str)
        ):
            raise VerificationError("held-out selector row is malformed")
        selector_ids.add(identifier)
        raw_value = _resolve_pointer(raw, pointer)
        compact_value = _resolve_pointer(compact, pointer)
        if raw_value != compact_value:
            raise VerificationError(f"selector value differs: {identifier}")

    validate_compact_summary(compact, selectors=selectors)
    projection = copy.deepcopy(raw)
    omitted_counts = {
        pointer: _remove_raw_section(projection, pointer)
        for pointer in RAW_SECTION_PATHS
    }
    compact_projection = copy.deepcopy(compact)
    promotion = _require_mapping(
        compact_projection.pop("promotion", None),
        label="compact promotion",
    )
    if compact_projection != projection:
        raise VerificationError(
            "compact result differs beyond enumerated raw-row omissions"
        )
    omitted_records = _require_list(
        promotion.get("omitted_raw_sections"),
        label="compact omitted sections",
    )
    observed_omissions: dict[str, int] = {}
    for row in omitted_records:
        if (
            not isinstance(row, Mapping)
            or row.get("retained_in_complete_archive") is not True
            or not isinstance(row.get("json_pointer"), str)
            or isinstance(row.get("row_count"), bool)
            or not isinstance(row.get("row_count"), int)
        ):
            raise VerificationError("compact omission record is malformed")
        pointer = str(row["json_pointer"])
        if pointer in observed_omissions:
            raise VerificationError("compact omission pointers are duplicated")
        observed_omissions[pointer] = int(row["row_count"])
    if observed_omissions != omitted_counts:
        raise VerificationError("compact omission audit differs from raw rows")

    gate3_binding = _require_mapping(
        lock.get("gate3_binding"),
        label="Gate-3 binding",
    )
    source = _require_mapping(
        promotion.get("source"),
        label="compact source",
    )
    complete_archive = _require_mapping(
        promotion.get("complete_raw_archive"),
        label="compact complete archive",
    )
    source_expected = {
        "run_id": gate3_binding.get("accepted_run_id"),
        "manifest_sha256": gate3_binding.get("accepted_manifest_sha256"),
        "result_sha256": gate3_binding.get("accepted_result_sha256"),
        "artifact_content_sha256": gate3_binding.get(
            "accepted_artifact_content_sha256"
        ),
        "selector_sha256": gate3_binding.get("accepted_selector_sha256"),
        "selector_content_sha256": gate3_binding.get(
            "accepted_selector_content_sha256"
        ),
    }
    for key, expected in source_expected.items():
        if source.get(key) != expected:
            raise VerificationError(f"compact source differs at {key}")
    if (
        source.get("result_sha256") != _sha256(raw_payload)
        or source.get("artifact_content_sha256") != computed_raw_content_hash
        or source.get("selector_sha256") != _sha256(selector_payload)
        or source.get("selector_content_sha256")
        != computed_selector_content_hash
    ):
        raise VerificationError("compact source does not bind promoted bytes")

    expected_archive_fields = {
        "path": archive_record.get("path"),
        "sha256": archive_record.get("sha256"),
        "bytes": archive_record.get("bytes"),
        "decompressed_sha256": _sha256(raw_payload),
        "decompressed_bytes": len(raw_payload),
        "compression": "gzip level 9, mtime 0",
    }
    for key, expected in expected_archive_fields.items():
        if complete_archive.get(key) != expected:
            raise VerificationError(f"compact archive binding differs at {key}")
    if promotion.get("gate3_lock_sha256") != gate3_binding.get("sha256"):
        raise VerificationError("compact result binds a different Gate-3 lock")

    audit = _require_mapping(
        promotion.get("promotion_audit"),
        label="compact promotion audit",
    )
    registry = _require_mapping(
        raw.get("method_track_registry"),
        label="raw method-track registry",
    )
    selections = _require_list(
        registry.get("selections"),
        label="selected method-track pairs",
    )
    exclusions = _require_list(
        registry.get("exclusions"),
        label="excluded method-track pairs",
    )
    expected_audit = {
        "base_selector_count": 448,
        "selected_method_track_pairs": len(selections),
        "excluded_method_track_pairs": len(exclusions),
        "omitted_raw_row_count": sum(omitted_counts.values()),
        "all_base_selectors_resolvable": True,
        "negative_tie_adverse_and_failure_evidence_preserved": True,
    }
    for key, expected in expected_audit.items():
        if audit.get(key) != expected:
            raise VerificationError(f"compact promotion audit differs at {key}")

    traceability = _require_mapping(
        lock.get("traceability"),
        label="result-lock traceability",
    )
    coverage = _require_mapping(
        lock.get("coverage"),
        label="result-lock coverage",
    )
    if (
        traceability.get("base_selector_count") != len(selector_rows)
        or coverage.get("selected_method_track_pairs") != len(selections)
        or coverage.get("excluded_method_track_pairs") != len(exclusions)
    ):
        raise VerificationError("result-lock selector/registry counts differ")

    return {
        "raw_sha256": _sha256(raw_payload),
        "raw_content_sha256": computed_raw_content_hash,
        "raw_bytes": len(raw_payload),
        "gzip_sha256": _sha256(archive_payload),
        "compact_sha256": _sha256(compact_payload),
        "selector_sha256": _sha256(selector_payload),
        "selector_content_sha256": computed_selector_content_hash,
        "selector_count": len(selector_rows),
        "omitted_raw_rows": sum(omitted_counts.values()),
        "omitted_sections": omitted_counts,
    }


def _claim_source_documents(
    repository_root: Path,
    catalog: Mapping[str, Any],
    lock: Mapping[str, Any],
) -> tuple[dict[str, Mapping[str, Any]], list[Mapping[str, Any]]]:
    source_rows = _require_list(catalog.get("sources"), label="claim sources")
    if len(source_rows) != len(EXPECTED_CLAIM_SOURCE_IDS):
        raise VerificationError("claim source count differs")
    by_id: dict[str, Mapping[str, Any]] = {}
    source_paths: set[str] = set()
    for row in source_rows:
        if not isinstance(row, Mapping):
            raise VerificationError("claim source row is malformed")
        source_id = row.get("id")
        path = row.get("path")
        if (
            not isinstance(source_id, str)
            or source_id in by_id
            or not isinstance(path, str)
            or path in source_paths
        ):
            raise VerificationError("claim source ids/paths are not unique")
        by_id[source_id] = row
        source_paths.add(path)
        _verify_file_record(
            repository_root,
            row,
            label=f"claim source {source_id}",
        )
    if set(by_id) != EXPECTED_CLAIM_SOURCE_IDS:
        raise VerificationError("claim source set is not the locked allowlist")

    promoted = _require_mapping(
        lock.get("promoted_artifacts"),
        label="promoted artifacts",
    )
    promoted_by_path = {
        row.get("path"): row
        for row in promoted.values()
        if isinstance(row, Mapping)
    }
    for source_id in (
        "heldout_summary",
        "heldout_complete_archive",
        "heldout_base_selectors",
        "runtime",
        "data_distribution",
        "data_quality",
    ):
        row = by_id[source_id]
        locked = promoted_by_path.get(row.get("path"))
        if (
            not isinstance(locked, Mapping)
            or locked.get("sha256") != row.get("sha256")
            or locked.get("bytes") != row.get("bytes")
        ):
            raise VerificationError(
                f"claim source is not exclusively promoted: {source_id}"
            )

    gate3_binding = _require_mapping(
        lock.get("gate3_binding"),
        label="Gate-3 binding",
    )
    if (
        by_id["gate3_lock"].get("path") != gate3_binding.get("path")
        or by_id["gate3_lock"].get("sha256") != gate3_binding.get("sha256")
    ):
        raise VerificationError("claim catalog Gate-3 source differs")
    gate3_path = _locked_path(
        repository_root,
        by_id["gate3_lock"].get("path"),
        label="Gate-3 claim source",
    )
    _, gate3 = _read_json_object(
        gate3_path,
        label="Gate-3 lock",
        require_canonical=True,
    )
    upstream = _require_mapping(
        gate3.get("upstream_binding"),
        label="Gate-3 upstream binding",
    )
    for source_id, key in (
        ("gate1_lock", "gate1_lock_sha256"),
        ("gate2_lock", "gate2_lock_sha256"),
    ):
        if by_id[source_id].get("sha256") != upstream.get(key):
            raise VerificationError(
                f"claim catalog {source_id} differs from Gate 3"
            )

    claim_source_ids = {
        row.get("source_id")
        for row in _require_list(catalog.get("claims"), label="claim rows")
        if isinstance(row, Mapping)
    }
    forbidden_claim_sources = {
        "heldout_complete_archive",
        "heldout_base_selectors",
    }
    if claim_source_ids & forbidden_claim_sources:
        raise VerificationError("claim points to a raw transport artifact")

    documents: dict[str, Mapping[str, Any]] = {}
    for source_id in claim_source_ids:
        if not isinstance(source_id, str) or source_id not in by_id:
            raise VerificationError("claim source id is unresolved")
        source_path = _locked_path(
            repository_root,
            by_id[source_id].get("path"),
            label=f"claim document {source_id}",
        )
        _, document = _read_json_object(
            source_path,
            label=f"claim document {source_id}",
        )
        documents[source_id] = document
    return documents, source_rows


def verify_claim_catalog_and_macros(
    repository_root: Path | str,
) -> dict[str, Any]:
    """Validate exclusive claim sources, values, rounding, and TeX macros."""

    root = Path(repository_root).resolve()
    _, lock = _read_json_object(
        root / DEFAULT_RESULT_LOCK_PATH,
        label="result lock",
        require_canonical=True,
    )
    promoted = _require_mapping(
        lock.get("promoted_artifacts"),
        label="promoted artifacts",
    )
    catalog_record = _require_mapping(
        promoted.get("claim-selectors.json"),
        label="claim catalog record",
    )
    macros_record = _require_mapping(
        promoted.get("revision_results.tex"),
        label="revision macro record",
    )
    selector_record = _require_mapping(
        promoted.get("exp23_heldout_selectors.json"),
        label="base selector record",
    )
    catalog_path = _verify_file_record(
        root,
        catalog_record,
        label="claim catalog",
    )
    macros_path = _verify_file_record(
        root,
        macros_record,
        label="revision macros",
    )
    selector_path = _verify_file_record(
        root,
        selector_record,
        label="base selectors",
    )
    catalog_payload, catalog = _read_json_object(
        catalog_path,
        label="claim catalog",
        require_canonical=True,
    )
    _, base_selectors = _read_json_object(
        selector_path,
        label="base selectors",
        require_canonical=True,
    )
    documents, source_rows = _claim_source_documents(root, catalog, lock)
    validation = validate_claim_catalog(
        catalog,
        source_documents=documents,
    )

    required_list = catalog.get("required_disclosure_claims")
    if required_list != sorted(REQUIRED_DISCLOSURE_CLAIMS):
        raise VerificationError("required-disclosure list differs")
    if catalog.get("required_disclosure_count") != len(
        REQUIRED_DISCLOSURE_CLAIMS
    ):
        raise VerificationError("required-disclosure count differs")

    claims = _require_list(catalog.get("claims"), label="claim rows")
    claim_ids: set[str] = set()
    required_flags: set[str] = set()
    for row in claims:
        if not isinstance(row, Mapping):
            raise VerificationError("claim row is malformed")
        identifier = row.get("id")
        rendered = row.get("rendered_value")
        if (
            not isinstance(identifier, str)
            or not identifier
            or identifier in claim_ids
            or re.search(r"[\s\\%#{}]", identifier)
            or not isinstance(rendered, str)
            or re.search(r"[\\%#{}]", rendered)
        ):
            raise VerificationError("claim id/rendering is unsafe for TeX")
        claim_ids.add(identifier)
        flagged = row.get("required_disclosure")
        if not isinstance(flagged, bool):
            raise VerificationError("claim disclosure flag is not boolean")
        if flagged:
            required_flags.add(identifier)
    if required_flags != REQUIRED_DISCLOSURE_CLAIMS:
        raise VerificationError("required-disclosure flags differ")

    base_rows = _require_list(
        base_selectors.get("selectors"),
        label="base selector rows",
    )
    catalog_selector_rows = _require_list(
        catalog.get("selectors"),
        label="catalog selector roots",
    )
    catalog_selectors = {
        row.get("id"): row
        for row in catalog_selector_rows
        if isinstance(row, Mapping)
    }
    if len(catalog_selectors) != len(catalog_selector_rows):
        raise VerificationError("catalog selector roots are duplicated")
    for row in base_rows:
        if not isinstance(row, Mapping):
            raise VerificationError("base selector row is malformed")
        identifier = row.get("id")
        observed = catalog_selectors.get(identifier)
        expected = {
            "id": identifier,
            "kind": row.get("kind"),
            "source_id": "heldout_summary",
            "json_pointer": row.get("json_pointer"),
            "gate3_base_selector": identifier,
        }
        if observed != expected:
            raise VerificationError(
                f"catalog base-selector binding differs: {identifier}"
            )
    base_registry = _require_mapping(
        catalog.get("base_selector_registry"),
        label="catalog base-selector registry",
    )
    if (
        base_registry.get("path") != selector_record.get("path")
        or base_registry.get("selector_count")
        != base_selectors.get("selector_count")
        or base_registry.get("selector_content_sha256")
        != base_selectors.get("selector_content_sha256")
    ):
        raise VerificationError("catalog base-selector registry differs")

    macros_payload = macros_path.read_bytes()
    expected_macros = _latex_macros(
        catalog,
        catalog_sha256=_sha256(catalog_payload),
    )
    if macros_payload != expected_macros:
        raise VerificationError("generated revision macros differ from catalog")

    traceability = _require_mapping(
        lock.get("traceability"),
        label="result-lock traceability",
    )
    if (
        traceability.get("selector_root_count")
        != validation["selector_count"]
        or traceability.get("numeric_claim_count") != validation["claim_count"]
        or traceability.get("required_disclosure_count")
        != validation["required_disclosure_count"]
    ):
        raise VerificationError("result-lock claim counts differ")

    return {
        "source_count": len(source_rows),
        "selector_root_count": validation["selector_count"],
        "claim_count": validation["claim_count"],
        "required_disclosure_count": validation["required_disclosure_count"],
        "catalog_sha256": _sha256(catalog_payload),
        "macros_sha256": _sha256(macros_payload),
    }


def _strip_tex_comments(text: str) -> str:
    output: list[str] = []
    for line in text.splitlines(keepends=True):
        cut = len(line)
        for index, character in enumerate(line):
            if character != "%":
                continue
            backslashes = 0
            cursor = index - 1
            while cursor >= 0 and line[cursor] == "\\":
                backslashes += 1
                cursor -= 1
            if backslashes % 2 == 0:
                cut = index
                break
        retained = line[:cut]
        if line.endswith("\n") and not retained.endswith("\n"):
            retained += "\n"
        output.append(retained)
    return "".join(output)


def _tex_sources(main_path: Path, *, paper_root: Path) -> dict[Path, str]:
    pending = [main_path.resolve()]
    sources: dict[Path, str] = {}
    root = paper_root.resolve()
    while pending:
        source = pending.pop()
        if source in sources:
            continue
        try:
            source.relative_to(root)
            text = source.read_text(encoding="utf-8")
        except ValueError as exc:
            raise VerificationError(f"TeX input escapes paper root: {source}") from exc
        except (FileNotFoundError, UnicodeDecodeError) as exc:
            raise VerificationError(f"TeX input is absent or invalid: {source}") from exc
        stripped = _strip_tex_comments(text)
        sources[source] = stripped
        for match in _INPUT_PATTERN.finditer(stripped):
            raw = match.group(1).strip()
            if not raw or "\\" in raw or "#" in raw:
                raise VerificationError(f"dynamic TeX input is not auditable: {raw!r}")
            candidate = Path(raw)
            if candidate.suffix == "":
                candidate = candidate.with_suffix(".tex")
            resolved = (root / candidate).resolve()
            try:
                resolved.relative_to(root)
            except ValueError as exc:
                raise VerificationError(
                    f"TeX input escapes paper root: {raw!r}"
                ) from exc
            pending.append(resolved)
    return sources


def verify_manuscript_claims(
    repository_root: Path | str,
    manuscript_path: Path | str = DEFAULT_MANUSCRIPT_PATH,
) -> dict[str, Any]:
    """Ensure every manuscript claim resolves and all disclosures are present."""

    root = Path(repository_root).resolve()
    manuscript = (
        Path(manuscript_path).resolve()
        if Path(manuscript_path).is_absolute()
        else _locked_path(root, Path(manuscript_path).as_posix(), label="manuscript")
    )
    paper_root = (root / "paper").resolve()
    sources = _tex_sources(manuscript, paper_root=paper_root)
    generated_macros = (
        paper_root / "generated/revision_results.tex"
    ).resolve()
    manuscript_sources = {
        path: text
        for path, text in sources.items()
        if path != generated_macros
    }
    combined = "\n".join(manuscript_sources.values())

    _, catalog = _read_json_object(
        root / "loop/revision/claim-selectors.json",
        label="claim catalog",
        require_canonical=True,
    )
    claim_rows = _require_list(catalog.get("claims"), label="claim rows")
    catalog_ids = {
        row.get("id")
        for row in claim_rows
        if isinstance(row, Mapping) and isinstance(row.get("id"), str)
    }
    matches = list(_CLAIM_PATTERN.finditer(combined))
    raw_macro_count = len(re.findall(r"\\RevisionClaim\b", combined))
    if raw_macro_count != len(matches):
        raise VerificationError("manuscript contains a dynamic/malformed claim")
    used = [match.group(1).strip() for match in matches]
    unresolved = sorted(set(used) - catalog_ids)
    if unresolved:
        raise VerificationError(
            "manuscript claims are unresolved: " + ", ".join(unresolved)
        )
    missing_disclosures = sorted(REQUIRED_DISCLOSURE_CLAIMS - set(used))
    if missing_disclosures:
        raise VerificationError(
            "mandatory disclosures are absent from manuscript: "
            + ", ".join(missing_disclosures)
        )
    if re.search(r"\\(?:def|gdef|edef)\s*\\RevisionClaim\b", combined):
        raise VerificationError("manuscript redefines RevisionClaim")
    if "revisionclaim@" in combined.lower():
        raise VerificationError("manuscript bypasses the RevisionClaim API")

    main_text = sources[manuscript.resolve()]
    macro_inputs = [
        match.group(1).strip()
        for match in _INPUT_PATTERN.finditer(main_text)
        if match.group(1).strip()
        in {
            "generated/revision_results",
            "generated/revision_results.tex",
        }
    ]
    if len(macro_inputs) != 1:
        raise VerificationError(
            "manuscript must input generated revision macros exactly once"
        )

    return {
        "tex_source_count": len(sources),
        "claim_occurrence_count": len(used),
        "unique_claim_count": len(set(used)),
        "mandatory_disclosure_count": len(REQUIRED_DISCLOSURE_CLAIMS),
        "unresolved_claims": [],
    }


def verify_stale_terms(
    repository_root: Path | str,
    *,
    paths: Iterable[Path | str] = DEFAULT_STALE_SCAN_PATHS,
    patterns: Iterable[tuple[str, str]] = DEFAULT_STALE_TERM_PATTERNS,
) -> dict[str, Any]:
    """Reject explicitly enumerated legacy dataset/path/build statements."""

    root = Path(repository_root).resolve()
    compiled: list[tuple[str, re.Pattern[str]]] = []
    for identifier, pattern in patterns:
        try:
            compiled.append(
                (identifier, re.compile(pattern, flags=re.IGNORECASE))
            )
        except re.error as exc:
            raise VerificationError(
                f"invalid stale-term regex: {identifier}"
            ) from exc
    matches: list[dict[str, Any]] = []
    scanned: list[str] = []
    for raw_path in paths:
        path = (
            Path(raw_path).resolve()
            if Path(raw_path).is_absolute()
            else _locked_path(root, Path(raw_path).as_posix(), label="stale scan")
        )
        try:
            text = path.read_text(encoding="utf-8")
        except (FileNotFoundError, UnicodeDecodeError) as exc:
            raise VerificationError(f"stale-scan source is absent: {path}") from exc
        relative = _relative_path(root, path)
        scanned.append(relative)
        for identifier, pattern in compiled:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                snippet = " ".join(match.group(0).split())
                matches.append(
                    {
                        "id": identifier,
                        "path": relative,
                        "line": line,
                        "match": snippet[:160],
                    }
                )
    if matches:
        summary = ", ".join(
            f"{row['id']}@{row['path']}:{row['line']}" for row in matches[:12]
        )
        raise VerificationError(f"stale legacy terms found: {summary}")
    return {
        "scanned_paths": scanned,
        "pattern_count": len(compiled),
        "matches": [],
    }


def verify_figure_policy(
    repository_root: Path | str,
    *,
    manuscript_path: Path | str = DEFAULT_MANUSCRIPT_PATH,
    figure_root: Path | str = DEFAULT_FIGURE_ROOT,
    policy: str = "all manuscript figures must be referenced",
    allowed_orphans: Iterable[str] = (),
) -> dict[str, Any]:
    """Resolve literal includegraphics paths and reject missing/orphan assets."""

    root = Path(repository_root).resolve()
    manuscript = (
        Path(manuscript_path).resolve()
        if Path(manuscript_path).is_absolute()
        else _locked_path(root, Path(manuscript_path).as_posix(), label="manuscript")
    )
    paper_root = (root / "paper").resolve()
    sources = _tex_sources(manuscript, paper_root=paper_root)
    includes: list[str] = []
    for text in sources.values():
        raw_count = len(re.findall(r"\\includegraphics\b", text))
        matches = list(_INCLUDEGRAPHICS_PATTERN.finditer(text))
        if raw_count != len(matches):
            raise VerificationError("dynamic/malformed includegraphics is forbidden")
        includes.extend(match.group(1).strip() for match in matches)

    normalized_policy = policy.strip().lower()
    no_figures = normalized_policy in {
        "none",
        "no-figures",
        "no figures are included by the revised manuscript",
    }
    if no_figures and includes:
        raise VerificationError("figure policy forbids includegraphics")

    figure_directory = (
        Path(figure_root).resolve()
        if Path(figure_root).is_absolute()
        else _locked_path(root, Path(figure_root).as_posix(), label="figure root")
    )
    available: set[Path] = set()
    if figure_directory.exists():
        if not figure_directory.is_dir():
            raise VerificationError("figure root is not a directory")
        available = {
            path.resolve()
            for path in figure_directory.rglob("*")
            if path.is_file()
            and path.suffix.lower() in SUPPORTED_FIGURE_EXTENSIONS
        }

    referenced: set[Path] = set()
    for raw in includes:
        if (
            not raw
            or "\\" in raw
            or "#" in raw
            or PurePosixPath(raw).is_absolute()
            or ".." in PurePosixPath(raw).parts
        ):
            raise VerificationError(f"includegraphics path is unsafe: {raw!r}")
        candidate = (paper_root / Path(*PurePosixPath(raw).parts)).resolve()
        if Path(raw).suffix:
            choices = [candidate] if candidate.exists() else []
        else:
            choices = [
                candidate.with_suffix(extension)
                for extension in sorted(SUPPORTED_FIGURE_EXTENSIONS)
                if candidate.with_suffix(extension).exists()
            ]
        if len(choices) != 1:
            raise VerificationError(
                f"includegraphics path is missing or ambiguous: {raw!r}"
            )
        resolved = choices[0].resolve()
        try:
            resolved.relative_to(figure_directory)
        except ValueError as exc:
            raise VerificationError(
                f"includegraphics is outside the figure root: {raw!r}"
            ) from exc
        referenced.add(resolved)

    allowed: set[Path] = set()
    for raw in allowed_orphans:
        if PurePosixPath(raw).is_absolute() or ".." in PurePosixPath(raw).parts:
            raise VerificationError(f"allowed orphan path is unsafe: {raw!r}")
        candidate = (
            figure_directory / Path(*PurePosixPath(raw).parts)
        ).resolve()
        try:
            candidate.relative_to(figure_directory)
        except ValueError as exc:
            raise VerificationError(
                f"allowed orphan escapes figure root: {raw!r}"
            ) from exc
        allowed.add(candidate)

    orphans = available - referenced - allowed
    if not no_figures and orphans:
        relative = sorted(
            path.relative_to(figure_directory).as_posix() for path in orphans
        )
        raise VerificationError(
            "orphan manuscript figures found: " + ", ".join(relative)
        )
    if no_figures and available:
        raise VerificationError(
            "no-figure policy requires an empty paper figure root"
        )

    return {
        "policy": policy,
        "includegraphics_count": len(includes),
        "referenced_figure_count": len(referenced),
        "available_figure_count": len(available),
        "orphan_figure_count": 0,
    }


def verify_tex_log(
    tex_log_path: Path | str,
    *,
    expected_page_count: int | None,
    maximum_overfull_points: float,
    allow_underfull_boxes: bool,
    require_no_undefined_citations: bool,
    require_no_undefined_references: bool,
    strict_warnings: bool = False,
    allowed_warning_patterns: Iterable[str] = (),
) -> dict[str, Any]:
    """Parse a final XeLaTeX log under an explicit page/box policy."""

    path = Path(tex_log_path).resolve()
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError as exc:
        raise VerificationError(f"TeX log is absent: {path}") from exc
    fatal_markers = (
        "! LaTeX Error:",
        "Emergency stop.",
        "Fatal error occurred",
        "No pages of output.",
    )
    observed_fatal = [marker for marker in fatal_markers if marker in text]
    if observed_fatal:
        raise VerificationError(
            "TeX log contains fatal errors: " + ", ".join(observed_fatal)
        )

    lowered = text.lower()
    if require_no_undefined_citations and (
        re.search(r"citation[^\n]*undefined", lowered)
        or "there were undefined citations" in lowered
    ):
        raise VerificationError("TeX log contains undefined citations")
    if require_no_undefined_references and (
        re.search(r"reference[^\n]*undefined", lowered)
        or "there were undefined references" in lowered
    ):
        raise VerificationError("TeX log contains undefined references")
    rerun_markers = (
        "Label(s) may have changed",
        "Rerun to get cross-references right",
        "rerun LaTeX",
    )
    if any(marker.lower() in lowered for marker in rerun_markers):
        raise VerificationError("TeX log requests another cross-reference run")

    overfull_values = [
        float(match.group(1)) for match in _OVERFULL_PATTERN.finditer(text)
    ]
    maximum_observed = max(overfull_values, default=0.0)
    if maximum_observed > maximum_overfull_points:
        raise VerificationError(
            "TeX overfull box exceeds policy: "
            f"{maximum_observed:.5g}pt > {maximum_overfull_points:.5g}pt"
        )
    underfull_count = len(re.findall(r"Underfull\s+\\[hv]box", text))
    if not allow_underfull_boxes and underfull_count:
        raise VerificationError("TeX log contains forbidden underfull boxes")

    page_matches = [
        int(match.group(1)) for match in _OUTPUT_PAGES_PATTERN.finditer(text)
    ]
    if not page_matches:
        raise VerificationError("TeX log has no successful PDF page record")
    page_count = page_matches[-1]
    if expected_page_count is None:
        raise VerificationError("technical expected-page policy is unconfigured")
    if page_count != expected_page_count:
        raise VerificationError(
            f"PDF page count differs: {page_count} != {expected_page_count}"
        )

    warning_line_pattern = re.compile(
        r"^(?:Package|LaTeX|Class|pdfTeX|XeTeX|Font)\b.*\bWarning:",
        flags=re.IGNORECASE,
    )
    warning_lines = [
        line.strip()
        for line in text.splitlines()
        if warning_line_pattern.search(line.strip())
    ]
    allowlist = [re.compile(pattern) for pattern in allowed_warning_patterns]
    unallowed_warnings = [
        line
        for line in warning_lines
        if not any(pattern.search(line) for pattern in allowlist)
    ]
    if strict_warnings and unallowed_warnings:
        raise VerificationError(
            "TeX log contains unallowed warnings: "
            + "; ".join(unallowed_warnings[:8])
        )

    return {
        "page_count": page_count,
        "expected_page_count": expected_page_count,
        "overfull_box_count": len(overfull_values),
        "maximum_overfull_points": maximum_observed,
        "underfull_box_count": underfull_count,
        "warning_count": len(warning_lines),
        "unallowed_warning_count": len(unallowed_warnings),
    }


def verify_bibtex_log(path: Path | str) -> dict[str, Any]:
    source = Path(path).resolve()
    try:
        text = source.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError as exc:
        raise VerificationError(f"BibTeX log is absent: {source}") from exc
    bad_lines = [
        line.strip()
        for line in text.splitlines()
        if line.startswith("Warning--")
        or "I couldn't open database file" in line
        or "error message" in line.lower()
    ]
    if bad_lines:
        raise VerificationError(
            "BibTeX log contains warnings/errors: " + "; ".join(bad_lines[:8])
        )
    if "This is BibTeX" not in text or "Database file #1:" not in text:
        raise VerificationError("BibTeX log is incomplete")
    return {"warning_count": 0}


def verify_publication_freshness(
    repository_root: Path | str,
    *,
    manuscript_path: Path | str = DEFAULT_MANUSCRIPT_PATH,
    tex_log_path: Path | str = DEFAULT_TEX_LOG_PATH,
) -> dict[str, Any]:
    """Reject a PDF/log older than any authoritative publication input."""

    root = Path(repository_root).resolve()
    manuscript = (
        Path(manuscript_path).resolve()
        if Path(manuscript_path).is_absolute()
        else root / Path(manuscript_path)
    )
    log = (
        Path(tex_log_path).resolve()
        if Path(tex_log_path).is_absolute()
        else root / Path(tex_log_path)
    )
    pdf = manuscript.with_suffix(".pdf")
    inputs = (
        manuscript,
        root / "paper/references.bib",
        root / "paper/generated/revision_results.tex",
        root / "paper/main.bbl",
    )
    outputs = (log, pdf)
    for path in (*inputs, *outputs):
        if not path.is_file():
            raise VerificationError(f"publication file is absent: {path}")
    newest_input = max(path.stat().st_mtime_ns for path in inputs)
    stale = [
        _relative_path(root, path)
        for path in outputs
        if path.stat().st_mtime_ns < newest_input
    ]
    if stale:
        raise VerificationError(
            "publication outputs are stale: " + ", ".join(stale)
        )
    bibliography = root / "paper/references.bib"
    bbl = root / "paper/main.bbl"
    if bbl.stat().st_mtime_ns < bibliography.stat().st_mtime_ns:
        raise VerificationError("BibTeX output predates references.bib")
    return {
        "inputs": [_relative_path(root, path) for path in inputs],
        "outputs": [_relative_path(root, path) for path in outputs],
    }


def _manifest_file_rows(manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = manifest.get("files")
    if isinstance(rows, list):
        if any(not isinstance(row, Mapping) for row in rows):
            raise VerificationError("artifact manifest file row is malformed")
        return list(rows)
    if isinstance(rows, Mapping):
        normalized: list[Mapping[str, Any]] = []
        for path, record in rows.items():
            if not isinstance(path, str) or not isinstance(record, Mapping):
                raise VerificationError("artifact manifest file map is malformed")
            normalized.append({"path": path, **dict(record)})
        return normalized
    raise VerificationError("artifact manifest has no file registry")


def verify_artifact_package(
    repository_root: Path | str,
    *,
    package_path: Path | str | None,
    manifest_path: Path | str,
) -> dict[str, Any]:
    """Verify an extracted package file-set or an archive-level checksum."""

    root = Path(repository_root).resolve()
    manifest_source = (
        Path(manifest_path).resolve()
        if Path(manifest_path).is_absolute()
        else _locked_path(root, Path(manifest_path).as_posix(), label="artifact manifest")
    )
    _, manifest = _read_json_object(
        manifest_source,
        label="artifact-package manifest",
    )
    package = (
        root
        if package_path is None
        else Path(package_path).resolve()
        if Path(package_path).is_absolute()
        else (root / Path(package_path)).resolve()
    )
    if package.is_file():
        if (
            manifest.get("schema_version") == "locked-artifact-package-v1"
            and isinstance(manifest.get("members"), list)
        ):
            from demo.experiments.package_locked_artifacts import verify_package

            verified = verify_package(
                repository_root=root,
                archive_path=package,
                package_manifest_path=manifest_source,
            )
            return {
                "mode": "archive",
                "package_sha256": verified["archive_sha256"],
                "package_bytes": verified["archive_bytes"],
                "file_count": verified["member_count"],
                "contents_verified": True,
            }
        record = manifest.get("archive", manifest.get("package"))
        if not isinstance(record, Mapping):
            if all(key in manifest for key in ("sha256", "bytes")):
                record = manifest
            else:
                raise VerificationError(
                    "archive package has no archive-level checksum record"
                )
        payload = package.read_bytes()
        if (
            record.get("sha256") != _sha256(payload)
            or record.get("bytes") != len(payload)
        ):
            raise VerificationError("artifact archive checksum/size differs")
        return {
            "mode": "archive",
            "package_sha256": _sha256(payload),
            "package_bytes": len(payload),
            "contents_verified": False,
        }
    if not package.is_dir():
        raise VerificationError(f"artifact package is absent: {package}")

    rows = _manifest_file_rows(manifest)
    if not rows:
        raise VerificationError("artifact package manifest is empty")
    seen: set[str] = set()
    for row in rows:
        raw = row.get("path")
        if not isinstance(raw, str) or raw in seen:
            raise VerificationError("artifact package paths are absent/duplicated")
        seen.add(raw)
        pure = PurePosixPath(raw)
        if pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
            raise VerificationError(f"unsafe artifact package path: {raw!r}")
        path = (package / Path(*pure.parts)).resolve()
        try:
            path.relative_to(package.resolve())
            payload = path.read_bytes()
        except ValueError as exc:
            raise VerificationError(
                f"artifact package path escapes root: {raw!r}"
            ) from exc
        except FileNotFoundError as exc:
            raise VerificationError(f"artifact package file is absent: {raw}") from exc
        if row.get("sha256") != _sha256(payload) or row.get("bytes") != len(
            payload
        ):
            raise VerificationError(f"artifact package file differs: {raw}")
    return {
        "mode": "directory",
        "file_count": len(rows),
        "contents_verified": True,
    }


def _check(
    name: str,
    operation: Callable[[], Mapping[str, Any]],
) -> dict[str, Any]:
    try:
        details = dict(operation())
    except Exception as exc:
        return {
            "name": name,
            "status": "fail",
            "errors": [f"{type(exc).__name__}: {exc}"],
            "details": {},
        }
    return {
        "name": name,
        "status": "pass",
        "errors": [],
        "details": details,
    }


def verify_submission(
    root: Path | str = REPOSITORY_ROOT,
    policy_path: Path | str | None = None,
    *,
    phase: str = "all",
    artifact_package: Path | str | None = None,
    artifact_manifest: Path | str | None = None,
) -> dict[str, Any]:
    """Run pre/post-build verification and return a JSON-serializable report."""

    repository_root = Path(root).resolve()
    if phase not in {"pre", "post", "all"}:
        raise VerificationError("phase must be pre, post, or all")
    selected_policy_path = (
        repository_root / DEFAULT_POLICY_PATH
        if policy_path is None
        else Path(policy_path).resolve()
        if Path(policy_path).is_absolute()
        else repository_root / Path(policy_path)
    )
    policy_error: str | None = None
    try:
        policy = load_submission_policy(selected_policy_path)
    except (VerificationError, OSError) as exc:
        policy = _fallback_policy()
        policy_error = f"{type(exc).__name__}: {exc}"

    if policy_error is None:
        policy_check = {
            "name": "submission_policy",
            "status": "pass",
            "errors": [],
            "details": {
                "path": _relative_path(repository_root, selected_policy_path),
                "profile": policy.profile,
                "status": policy.status,
                "expected_page_count": policy.expected_page_count,
                "maximum_overfull_points": policy.maximum_overfull_points,
                "figure_policy": policy.figure_policy,
            },
        }
    else:
        policy_check = {
            "name": "submission_policy",
            "status": "incomplete",
            "errors": [policy_error],
            "details": {
                "path": str(selected_policy_path),
            },
        }

    checks = [
        policy_check,
        _check(
            "result_lock",
            lambda: verify_result_lock(repository_root),
        ),
        _check(
            "archive_compact_selectors",
            lambda: verify_archive_projection_and_selectors(repository_root),
        ),
        _check(
            "claim_catalog_macros",
            lambda: verify_claim_catalog_and_macros(repository_root),
        ),
        _check(
            "manuscript_claims",
            lambda: verify_manuscript_claims(repository_root),
        ),
        _check(
            "stale_legacy_terms",
            lambda: verify_stale_terms(
                repository_root,
                paths=policy.stale_scan_paths,
                patterns=policy.stale_term_patterns,
            ),
        ),
        _check(
            "figure_policy",
            lambda: verify_figure_policy(
                repository_root,
                figure_root=policy.figure_root,
                policy=policy.figure_policy,
                allowed_orphans=policy.allowed_orphan_figures,
            ),
        ),
    ]

    if artifact_manifest is not None:
        checks.append(
            _check(
                "artifact_package",
                lambda: verify_artifact_package(
                    repository_root,
                    package_path=artifact_package,
                    manifest_path=artifact_manifest,
                ),
            )
        )
    elif artifact_package is not None:
        checks.append(
            {
                "name": "artifact_package",
                "status": "fail",
                "errors": [
                    "VerificationError: --artifact-package requires "
                    "--artifact-manifest"
                ],
                "details": {},
            }
        )
    else:
        checks.append(
            {
                "name": "artifact_package",
                "status": "skip",
                "errors": [],
                "details": {"reason": "optional package was not supplied"},
            }
        )

    if phase in {"post", "all"}:
        checks.extend(
            [
                _check(
                    "tex_log",
                    lambda: verify_tex_log(
                        repository_root / DEFAULT_TEX_LOG_PATH,
                        expected_page_count=policy.expected_page_count,
                        maximum_overfull_points=(
                            policy.maximum_overfull_points
                        ),
                        allow_underfull_boxes=policy.allow_underfull_boxes,
                        require_no_undefined_citations=(
                            policy.require_no_undefined_citations
                        ),
                        require_no_undefined_references=(
                            policy.require_no_undefined_references
                        ),
                        strict_warnings=policy.strict_tex_warnings,
                        allowed_warning_patterns=(
                            policy.allowed_tex_warning_patterns
                        ),
                    ),
                ),
                _check(
                    "bibtex_log",
                    lambda: verify_bibtex_log(
                        repository_root / DEFAULT_BIBTEX_LOG_PATH
                    ),
                ),
                _check(
                    "publication_freshness",
                    lambda: verify_publication_freshness(repository_root),
                ),
            ]
        )
    else:
        for name in ("tex_log", "bibtex_log", "publication_freshness"):
            checks.append(
                {
                    "name": name,
                    "status": "skip",
                    "errors": [],
                    "details": {"reason": "pre-build phase"},
                }
            )

    statuses = {row["status"] for row in checks}
    if "fail" in statuses:
        status = "fail"
    elif "incomplete" in statuses:
        status = "incomplete"
    else:
        status = "pass"
    blockers = {
        key: value
        for key, value in policy.external_submission_inputs.items()
        if value is None
        or (
            isinstance(value, str)
            and "external-blocked" in value.lower()
        )
    }
    return {
        "schema_version": 1,
        "status": status,
        "phase": phase,
        "repository_root": str(repository_root),
        "policy": {
            "configured": policy.configured,
            "profile": policy.profile,
            "status": policy.status,
        },
        "external_submission_blockers": blockers,
        "checks": checks,
        "summary": {
            "pass": sum(row["status"] == "pass" for row in checks),
            "fail": sum(row["status"] == "fail" for row in checks),
            "incomplete": sum(
                row["status"] == "incomplete" for row in checks
            ),
            "skip": sum(row["status"] == "skip" for row in checks),
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=REPOSITORY_ROOT,
        help="repository root (default: inferred from this module)",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=None,
        help="submission policy (default: revision/submission-policy.json)",
    )
    parser.add_argument(
        "--phase",
        choices=("pre", "post", "all"),
        default="all",
        help="pre-build checks, post-build full checks, or all (default)",
    )
    parser.add_argument(
        "--artifact-package",
        type=Path,
        default=None,
        help="optional extracted package directory or archive file",
    )
    parser.add_argument(
        "--artifact-manifest",
        type=Path,
        default=None,
        help="optional checksum manifest for --artifact-package",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="optional JSON report path; stdout is always emitted",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    report = verify_submission(
        args.repository_root,
        args.policy,
        phase=args.phase,
        artifact_package=args.artifact_package,
        artifact_manifest=args.artifact_manifest,
    )
    payload = json.dumps(
        report,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"
    print(payload, end="")
    if args.report is not None:
        report_path = args.report.resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("x", encoding="utf-8") as stream:
            stream.write(payload)
    if report["status"] == "pass":
        return 0
    if report["status"] == "incomplete":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "SubmissionPolicy",
    "VerificationError",
    "load_submission_policy",
    "main",
    "verify_archive_projection_and_selectors",
    "verify_artifact_package",
    "verify_bibtex_log",
    "verify_claim_catalog_and_macros",
    "verify_figure_policy",
    "verify_manuscript_claims",
    "verify_publication_freshness",
    "verify_result_lock",
    "verify_stale_terms",
    "verify_submission",
    "verify_tex_log",
]
