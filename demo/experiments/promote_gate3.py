"""Independently validate the single held-out candidate and lock Gate 3."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from demo.experiments.artifacts import validate_manifest
from demo.experiments.evaluation_data import (
    DEFAULT_GATE1_LOCK,
    DEFAULT_GATE2_LOCK,
    DEFAULT_SELECTED_CONFIGS,
    load_selected_configs,
)
from demo.experiments.evaluation_protocol import load_locked_test_seeds
from demo.experiments.exp23_heldout_evaluation import (
    DEFAULT_X0_RELEASE,
    RESULT_NAME,
    SELECTOR_NAME,
    SOURCE_FILES,
    build_provenance_record,
    load_x0_authorization,
    validate_result,
    validate_selectors,
)
from demo.experiments.pre_gate2 import (
    canonical_json_bytes,
    resolve_frozen_dataset_root,
)
from demo.experiments.protocol import DEFAULT_PROTOCOL_DIR, file_sha256


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GATE3_LOCK = REPOSITORY_ROOT / "revision" / "gate3-lock.json"
DEFAULT_GATE3_AUDIT = REPOSITORY_ROOT / "revision" / "gate3-audit.md"
DEFAULT_REJECTED_RUNS = REPOSITORY_ROOT / "revision" / "rejected-runs.json"
EXPECTED_MODULE = "demo.experiments.exp23_heldout_evaluation"


def _relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError as exc:
        raise ValueError(f"Gate-3 path is outside the repository: {resolved}") from exc


def _canonical_object(path: Path, *, label: str) -> tuple[bytes, dict[str, Any]]:
    try:
        payload = path.read_bytes()
        value = json.loads(payload)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is absent or invalid") from exc
    if not isinstance(value, dict) or payload != canonical_json_bytes(value):
        raise ValueError(f"{label} must be a canonical JSON object")
    return payload, value


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_normalized_bundle(bundle: Any) -> Any:
    """Match the canonical JSON representation used by the sealed result."""

    return replace(
        bundle,
        selections=tuple(
            replace(
                selection,
                config=json.loads(
                    json.dumps(
                        dict(selection.config),
                        sort_keys=True,
                        ensure_ascii=True,
                        allow_nan=False,
                    )
                ),
            )
            for selection in bundle.selections
        ),
    )


def _expected_dataset_inputs() -> dict[str, str]:
    gate1 = json.loads(DEFAULT_GATE1_LOCK.read_text(encoding="utf-8"))
    accepted = gate1["accepted_run"]
    dataset_manifest = (
        REPOSITORY_ROOT
        / Path(accepted["manifest"]).parent
        / "work"
        / "datasets"
        / "manifest.json"
    )
    return {
        _relative(dataset_manifest): file_sha256(dataset_manifest),
        _relative(DEFAULT_GATE1_LOCK): file_sha256(DEFAULT_GATE1_LOCK),
        _relative(DEFAULT_GATE2_LOCK): file_sha256(DEFAULT_GATE2_LOCK),
        _relative(DEFAULT_X0_RELEASE): file_sha256(DEFAULT_X0_RELEASE),
        "requirements.lock": file_sha256(REPOSITORY_ROOT / "requirements.lock"),
    }


def _validate_manifest_inputs(manifest: Mapping[str, Any]) -> None:
    inputs = manifest.get("inputs")
    if not isinstance(inputs, Mapping):
        raise ValueError("held-out manifest has no input registry")
    datasets = inputs.get("datasets")
    if not isinstance(datasets, list):
        raise ValueError("held-out manifest has no explicit dataset inputs")
    observed: dict[str, str] = {}
    for row in datasets:
        if (
            not isinstance(row, Mapping)
            or not isinstance(row.get("source"), str)
            or not isinstance(row.get("sha256"), str)
        ):
            raise ValueError("held-out manifest dataset input is malformed")
        observed[row["source"]] = row["sha256"]
    expected = _expected_dataset_inputs()
    if observed != expected:
        raise ValueError(
            "held-out manifest did not snapshot every Gate/data/lock input"
        )

    protocol = inputs.get("protocol")
    if not isinstance(protocol, Mapping):
        raise ValueError("held-out manifest protocol snapshot is absent")
    files = protocol.get("files")
    if not isinstance(files, Mapping):
        raise ValueError("held-out manifest protocol members are absent")
    current_members = {
        path.name: file_sha256(path)
        for path in sorted(DEFAULT_PROTOCOL_DIR.glob("*.json"))
        if path.is_file()
    }
    observed_members = {
        name: row.get("sha256")
        for name, row in files.items()
        if isinstance(row, Mapping)
    }
    if observed_members != current_members:
        raise ValueError("held-out manifest protocol snapshot changed")


def _validate_command(
    manifest: Mapping[str, Any],
    *,
    gate1_lock: Mapping[str, Any],
) -> None:
    repository = manifest.get("repository")
    historical_root_raw = (
        repository.get("root")
        if isinstance(repository, Mapping)
        else None
    )
    accepted = gate1_lock.get("accepted_run")
    accepted_manifest_raw = (
        accepted.get("manifest")
        if isinstance(accepted, Mapping)
        else None
    )
    if (
        not isinstance(historical_root_raw, str)
        or not historical_root_raw
        or not isinstance(accepted_manifest_raw, str)
        or not accepted_manifest_raw
    ):
        raise ValueError(
            "held-out manifest lacks its historical repository/dataset binding"
        )
    historical_root = Path(historical_root_raw)
    accepted_manifest = Path(accepted_manifest_raw)
    if (
        not historical_root.is_absolute()
        or ".." in historical_root.parts
        or historical_root_raw != str(historical_root)
        or accepted_manifest.is_absolute()
        or ".." in accepted_manifest.parts
        or accepted_manifest_raw != accepted_manifest.as_posix()
        or accepted_manifest.name != "manifest.json"
        or accepted_manifest.parts[:3] != ("demo", "artifacts", "runs")
    ):
        raise ValueError(
            "held-out manifest historical repository/dataset binding is malformed"
        )
    historical_dataset_root = (
        historical_root
        / accepted_manifest.parent
        / "work"
        / "datasets"
    )

    command = manifest.get("command")
    if (
        not isinstance(command, list)
        or any(not isinstance(part, str) or not part for part in command)
    ):
        raise ValueError("held-out candidate command is malformed")
    try:
        module_index = command.index("-m")
    except ValueError as exc:
        raise ValueError("held-out command did not use a Python module") from exc
    expected_tail = [
        "-m",
        EXPECTED_MODULE,
        "--dataset-root",
        str(historical_dataset_root),
    ]
    if command[module_index:] != expected_tail:
        raise ValueError(
            "held-out command differs from the complete no-filter contract"
        )
    if any(
        forbidden in command
        for forbidden in (
            "--seed",
            "--seed-limit",
            "--method",
            "--track",
            "--resume",
            "--output",
        )
    ):
        raise ValueError("held-out command contains a forbidden selection option")


def validate_candidate(
    result_path: Path | str,
) -> dict[str, Any]:
    """Validate a sealed run without reopening a test dataset."""

    result_source = Path(result_path).resolve()
    if result_source.name != RESULT_NAME or result_source.parent.name != "tables":
        raise ValueError("Gate-3 result path is not the canonical Exp23 table")
    run_root = result_source.parent.parent
    manifest_path = run_root / "manifest.json"
    selector_path = result_source.with_name(SELECTOR_NAME)
    invocation_path = run_root / "work" / "x0-invocation.json"

    manifest = validate_manifest(manifest_path)
    if (
        manifest.get("status") != "succeeded"
        or manifest.get("exit_code") != 0
        or manifest.get("run_id") != run_root.name
    ):
        raise ValueError("held-out candidate run did not succeed cleanly")
    _validate_manifest_inputs(manifest)
    gate1 = json.loads(DEFAULT_GATE1_LOCK.read_text(encoding="utf-8"))
    _validate_command(
        manifest,
        gate1_lock=gate1,
    )

    result_payload, result = _canonical_object(
        result_source,
        label="held-out result",
    )
    selector_payload, selectors = _canonical_object(
        selector_path,
        label="held-out selectors",
    )
    invocation_payload, invocation = _canonical_object(
        invocation_path,
        label="X0 invocation ledger",
    )
    checksums = manifest.get("checksums", {})
    for path, payload in (
        (result_source, result_payload),
        (selector_path, selector_payload),
        (invocation_path, invocation_payload),
    ):
        relative = path.relative_to(run_root).as_posix()
        if checksums.get(relative) != _sha256(payload):
            raise ValueError(f"held-out manifest does not seal {relative}")

    released = load_locked_test_seeds(DEFAULT_GATE2_LOCK, DEFAULT_PROTOCOL_DIR)
    authorization = load_x0_authorization(released_seeds=released)
    bundle = load_selected_configs(
        DEFAULT_SELECTED_CONFIGS,
        gate2_lock=DEFAULT_GATE2_LOCK,
        protocol_dir=DEFAULT_PROTOCOL_DIR,
        artifact_root=REPOSITORY_ROOT,
    )
    validation = validate_result(
        result,
        _json_normalized_bundle(bundle),
        released_seeds=released,
    )
    selector_validation = validate_selectors(selectors, result)
    if (
        invocation.get("schema_version") != "x0-invocation-v1"
        or invocation.get("status") != "authorized_pre_read"
        or invocation.get("run_id") != manifest["run_id"]
        or invocation.get("candidate_suite_invocation") != 1
        or invocation.get("released_seed_count") != len(released)
        or invocation.get("gate2_lock_sha256")
        != file_sha256(DEFAULT_GATE2_LOCK)
        or invocation.get("selected_configs_sha256")
        != file_sha256(DEFAULT_SELECTED_CONFIGS)
        or invocation.get("x0_authorization_sha256")
        != file_sha256(DEFAULT_X0_RELEASE)
        or invocation.get("authorization_content_sha256")
        != authorization["authorization_content_sha256"]
        or invocation.get("seed_or_method_filter") is not None
        or invocation.get("resume") is not False
    ):
        raise ValueError("X0 invocation ledger differs from its authorization")

    current_provenance = build_provenance_record()
    result_protocol = result.get("protocol")
    if not isinstance(result_protocol, Mapping):
        raise ValueError("held-out result protocol record is absent")
    for key in (
        "gate1_lock",
        "gate2_lock",
        "selected_configs",
        "protocol_members",
        "dataset_contract",
        "source_files",
    ):
        if result_protocol.get(key) != current_provenance.get(key):
            raise ValueError(f"held-out source provenance changed at {key}")
    _, frozen_record = resolve_frozen_dataset_root(
        gate1_lock=DEFAULT_GATE1_LOCK
    )
    if result_protocol.get("frozen_dataset_root") != frozen_record:
        raise ValueError("held-out frozen-dataset root binding changed")
    expected_authorization = {
        "path": _relative(DEFAULT_X0_RELEASE),
        "sha256": file_sha256(DEFAULT_X0_RELEASE),
        "authorization_content_sha256": authorization[
            "authorization_content_sha256"
        ],
        "maximum_candidate_suite_invocations": 1,
    }
    if result_protocol.get("x0_authorization") != expected_authorization:
        raise ValueError("held-out X0 authorization provenance changed")
    if set(result_protocol["source_files"]) != set(SOURCE_FILES):
        raise ValueError("held-out source-file binding is incomplete")
    if result_protocol.get("run_id") != manifest["run_id"]:
        raise ValueError("held-out result run id differs from its manifest")

    return {
        "status": "pass",
        "run_id": manifest["run_id"],
        "manifest_path": manifest_path,
        "manifest_sha256": file_sha256(manifest_path),
        "result_path": result_source,
        "result_sha256": _sha256(result_payload),
        "artifact_content_sha256": result["artifact_content_sha256"],
        "result_status": result["status"],
        "selector_path": selector_path,
        "selector_sha256": _sha256(selector_payload),
        "selector_content_sha256": selectors["selector_content_sha256"],
        "selector_count": selector_validation["selector_count"],
        "invocation_path": invocation_path,
        "invocation_sha256": _sha256(invocation_payload),
        "validation": validation,
        "selected_prediction_failure_count": result["retention_policy"][
            "selected_prediction_failure_count"
        ],
        "scientific_seed_failure_count": result["retention_policy"][
            "scientific_seed_failure_count"
        ],
        "clustering_retention_counts": result["clustering"][
            "retention_counts"
        ],
        "priority_retention_counts": result["priority_robustness"][
            "retention_counts"
        ],
        "dispatch_retention_counts": result["dispatch_outcomes"][
            "retention_counts"
        ],
        "factorial_density_match_failures": result["factorial_ablation"][
            "clustering"
        ]["density_match_failures"],
        "validation_errors": [],
    }


def _gate3_lock(audit: Mapping[str, Any]) -> dict[str, Any]:
    gate2 = json.loads(DEFAULT_GATE2_LOCK.read_text(encoding="utf-8"))
    rejected = json.loads(DEFAULT_REJECTED_RUNS.read_text(encoding="utf-8"))
    return {
        "schema_version": 1,
        "gate": "Gate 3",
        "status": "locked",
        "locked_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "single complete held-out result and selector registry",
        "upstream_binding": {
            "gate1_lock_sha256": file_sha256(DEFAULT_GATE1_LOCK),
            "gate2_lock_sha256": file_sha256(DEFAULT_GATE2_LOCK),
            "protocol_sha256": gate2["protocol_sha256"],
            "selected_configs_sha256": file_sha256(DEFAULT_SELECTED_CONFIGS),
            "x0_authorization_sha256": file_sha256(DEFAULT_X0_RELEASE),
        },
        "accepted_run": {
            "run_id": audit["run_id"],
            "manifest": _relative(audit["manifest_path"]),
            "manifest_sha256": audit["manifest_sha256"],
            "status": "succeeded",
            "exit_code": 0,
            "result": {
                "path": audit["result_path"].relative_to(
                    audit["manifest_path"].parent
                ).as_posix(),
                "sha256": audit["result_sha256"],
                "artifact_content_sha256": audit[
                    "artifact_content_sha256"
                ],
                "status": audit["result_status"],
            },
            "selectors": {
                "path": audit["selector_path"].relative_to(
                    audit["manifest_path"].parent
                ).as_posix(),
                "sha256": audit["selector_sha256"],
                "selector_content_sha256": audit[
                    "selector_content_sha256"
                ],
                "selector_count": audit["selector_count"],
            },
            "invocation": {
                "path": audit["invocation_path"].relative_to(
                    audit["manifest_path"].parent
                ).as_posix(),
                "sha256": audit["invocation_sha256"],
                "candidate_suite_invocation": 1,
            },
        },
        "coverage": {
            "test_seed_count": audit["validation"]["seed_count"],
            "selected_method_seed_rows": audit["validation"][
                "selected_method_seed_rows"
            ],
            "exclusion_seed_rows": audit["validation"]["exclusion_seed_rows"],
            "selected_prediction_failures": audit[
                "selected_prediction_failure_count"
            ],
            "scientific_seed_failures": audit[
                "scientific_seed_failure_count"
            ],
        },
        "retention_audit": {
            "clustering": audit["clustering_retention_counts"],
            "priority": audit["priority_retention_counts"],
            "dispatch": audit["dispatch_retention_counts"],
            "factorial_density_match_failures": audit[
                "factorial_density_match_failures"
            ],
            "negative_tie_adverse_and_failure_rows_retained": True,
        },
        "validation": {
            "manifest": "pass",
            "input_snapshots": "pass",
            "source_and_protocol_binding": "pass",
            "result_schema_and_content_hash": "pass",
            "aggregate_and_inference_recomputation": "pass",
            "selector_resolution_and_checksum": "pass",
            "invocation_authorization": "pass",
            "validation_errors": [],
        },
        "rejected_run_ledger": {
            "path": _relative(DEFAULT_REJECTED_RUNS),
            "sha256": file_sha256(DEFAULT_REJECTED_RUNS),
            "run_count": len(rejected.get("runs", [])),
        },
        "reopen_conditions": [
            "accepted run manifest or file-set checksum mismatch",
            "Gate-1/Gate-2/selected-config/X0 authorization binding change",
            "result, selector, or invocation checksum mismatch",
            "mechanical recomputation or selector resolution failure",
            "confirmed method-independent implementation bug requiring a complete rerun",
        ],
    }


def _audit_markdown(lock: Mapping[str, Any]) -> str:
    accepted = lock["accepted_run"]
    coverage = lock["coverage"]
    retention = lock["retention_audit"]
    return "\n".join(
        (
            "# Gate 3 result-lock audit",
            "",
            f"- Status: **{lock['status']}**",
            f"- Accepted run: `{accepted['run_id']}`",
            f"- Manifest SHA-256: `{accepted['manifest_sha256']}`",
            (
                "- Result content SHA-256: "
                f"`{accepted['result']['artifact_content_sha256']}`"
            ),
            (
                "- Selector content SHA-256: "
                f"`{accepted['selectors']['selector_content_sha256']}`"
            ),
            (
                "- Coverage: "
                f"{coverage['test_seed_count']} test seeds, "
                f"{coverage['selected_method_seed_rows']} selected rows, "
                f"{coverage['exclusion_seed_rows']} retained exclusion rows."
            ),
            (
                "- Retained failures: "
                f"{coverage['selected_prediction_failures']} selected predictions, "
                f"{coverage['scientific_seed_failures']} scientific seed runs."
            ),
            (
                "- Factorial density-unmatched cells retained: "
                f"{retention['factorial_density_match_failures']}."
            ),
            (
                "- Negative/tie/adverse/failure retention: "
                f"`{retention['negative_tie_adverse_and_failure_rows_retained']}`."
            ),
            "- Independent manifest/input/source/result/inference/selector audit: pass.",
            "- Test candidate-suite invocations accepted: 1.",
            "",
            "Paper/result promotion is permitted only from this locked run.",
            "",
        )
    )


def promote(
    result_path: Path | str,
    *,
    gate3_lock: Path | str = DEFAULT_GATE3_LOCK,
    gate3_audit: Path | str = DEFAULT_GATE3_AUDIT,
) -> tuple[Path, Path]:
    lock_path = Path(gate3_lock).resolve()
    audit_path = Path(gate3_audit).resolve()
    if (
        lock_path != DEFAULT_GATE3_LOCK.resolve()
        or audit_path != DEFAULT_GATE3_AUDIT.resolve()
    ):
        raise ValueError("Gate-3 promotion targets must be canonical")
    if lock_path.exists() or audit_path.exists():
        raise FileExistsError("refusing to replace an existing Gate-3 lock")
    validated = validate_candidate(result_path)
    lock = _gate3_lock(validated)
    lock_candidate = lock_path.with_name(f".{lock_path.name}.candidate")
    audit_candidate = audit_path.with_name(f".{audit_path.name}.candidate")
    try:
        with lock_candidate.open("xb") as stream:
            stream.write(canonical_json_bytes(lock))
        with audit_candidate.open("x", encoding="utf-8") as stream:
            stream.write(_audit_markdown(lock))
        os.replace(audit_candidate, audit_path)
        os.replace(lock_candidate, lock_path)
    except Exception:
        for provisional in (lock_candidate, audit_candidate):
            try:
                provisional.unlink()
            except FileNotFoundError:
                pass
        raise
    return lock_path, audit_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, required=True)
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    lock, audit = promote(args.result)
    print(
        json.dumps(
            {
                "gate3_lock": str(lock),
                "gate3_audit": str(audit),
                "status": "locked",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["promote", "validate_candidate"]
