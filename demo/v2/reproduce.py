"""Read-only reproduction of the accepted synthetic v2 analysis.

This entrypoint never invokes the generator, calibration, confirmation, or the
oracle diagnostic.  It verifies the accepted artifact chain, recomputes the
complete analysis from the stored synthetic confirmation rows, and renders the
short-paper TeX projection into a temporary directory for a byte comparison.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any, Mapping, Sequence

from demo.v2.analysis import ConfirmationAnalysisSpec, analyze_confirmation_payload
from demo.v2.experiment import implementation_sha256
from demo.v2.generator import canonical_json_bytes
from demo.v2.protocol import build_freeze_record, file_sha256, load_protocol
from demo.v2.reporting import generate_short_results


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_LOCK = REPOSITORY_ROOT / "revision" / "v2" / "protocol-lock.json"
RESULT_DIRECTORY = REPOSITORY_ROOT / "revision" / "v2" / "results"
MANIFEST = RESULT_DIRECTORY / "confirmation_manifest.json"
RESULT = RESULT_DIRECTORY / "confirmation_result.json.gz"
ANALYSIS = RESULT_DIRECTORY / "confirmation_analysis.json"
SELECTION = RESULT_DIRECTORY / "calibration_selection.json"
PAPER_RESULTS = REPOSITORY_ROOT / "paper" / "short_results.tex"


class CoreReproductionError(RuntimeError):
    """Raised when an accepted artifact cannot be reproduced exactly."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CoreReproductionError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json(path: Path) -> Mapping[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise CoreReproductionError(f"missing or unsafe artifact: {path}")
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
    )
    if not isinstance(value, Mapping):
        raise CoreReproductionError(f"artifact is not a JSON object: {path}")
    return value


def _read_gzip_json(path: Path) -> Mapping[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise CoreReproductionError(f"missing or unsafe artifact: {path}")
    with gzip.open(path, mode="rt", encoding="utf-8") as stream:
        value = json.load(stream, object_pairs_hook=_reject_duplicate_keys)
    if not isinstance(value, Mapping):
        raise CoreReproductionError(f"artifact is not a JSON object: {path}")
    return value


def _payload_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def reproduce_core(
    *,
    protocol_lock_path: Path = PROTOCOL_LOCK,
    manifest_path: Path = MANIFEST,
    result_path: Path = RESULT,
    analysis_path: Path = ANALYSIS,
    selection_path: Path = SELECTION,
    paper_results_path: Path = PAPER_RESULTS,
) -> dict[str, Any]:
    """Recompute accepted v2 analysis and reporting without generating data."""

    protocol = load_protocol()
    lock = _read_json(Path(protocol_lock_path))
    frozen_at = lock.get("frozen_at")
    if not isinstance(frozen_at, str) or lock != build_freeze_record(
        frozen_at=frozen_at
    ):
        raise CoreReproductionError("protocol lock does not match frozen members")

    manifest = _read_json(Path(manifest_path))
    if (
        manifest.get("schema_version") != "v2.confirmation-state.1"
        or manifest.get("status") != "accepted"
        or manifest.get("coverage_complete") is not True
    ):
        raise CoreReproductionError("confirmation manifest is not accepted and complete")
    if manifest.get("protocol_sha256") != protocol.bundle_sha256:
        raise CoreReproductionError("manifest protocol hash mismatch")
    current_implementation = implementation_sha256()
    if manifest.get("implementation_sha256") != current_implementation:
        raise CoreReproductionError("implementation hash drifted after confirmation")
    if file_sha256(result_path) != manifest.get("result_sha256"):
        raise CoreReproductionError("confirmation result SHA-256 mismatch")
    if file_sha256(analysis_path) != manifest.get("analysis_sha256"):
        raise CoreReproductionError("confirmation analysis SHA-256 mismatch")
    if file_sha256(selection_path) != manifest.get("selection_sha256"):
        raise CoreReproductionError("calibration selection SHA-256 mismatch")

    result = _read_gzip_json(Path(result_path))
    seeds = tuple(result.get("confirmation_master_seeds", ()))
    if seeds != protocol.confirmation_seeds:
        raise CoreReproductionError("result does not use the frozen confirmation seeds")
    recomputed = analyze_confirmation_payload(
        result,
        ConfirmationAnalysisSpec(seeds=seeds),
    )
    recomputed_with_source = {
        **recomputed,
        "source_confirmation": {
            "schema_version": result["schema_version"],
            "protocol_sha256": result["protocol_sha256"],
            "implementation_sha256": result["implementation_sha256"],
            "execution_freeze_sha256": result["execution_freeze_sha256"],
            "selection_sha256": result["selection_sha256"],
            "confirmation_payload_sha256": _payload_sha256(result),
        },
    }
    stored_analysis = _read_json(Path(analysis_path))
    if canonical_json_bytes(recomputed_with_source) != canonical_json_bytes(
        stored_analysis
    ):
        raise CoreReproductionError("recomputed analysis differs from accepted analysis")

    with tempfile.TemporaryDirectory(prefix="flood-rescue-v2-reproduce-") as raw:
        rendered_path = Path(raw) / "short_results.tex"
        rendering = generate_short_results(
            Path(manifest_path),
            Path(analysis_path),
            Path(selection_path),
            rendered_path,
        )
        if rendered_path.read_bytes() != Path(paper_results_path).read_bytes():
            raise CoreReproductionError(
                "regenerated short-results TeX differs from the manuscript include"
            )

    return {
        "schema_version": "v2.core-reproduction.1",
        "status": "pass",
        "protocol_sha256": protocol.bundle_sha256,
        "implementation_sha256": current_implementation,
        "result_sha256": manifest["result_sha256"],
        "analysis_sha256": manifest["analysis_sha256"],
        "selection_sha256": manifest["selection_sha256"],
        "short_results_sha256": rendering["output_sha256"],
        "n_master_seeds": len(seeds),
        "analysis_exact": True,
        "short_results_exact": True,
        "oracle_diagnostic_read": False,
        "seed_generation_performed": False,
        "restricted_data_required": False,
    }


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reproduce accepted flood-rescue v2 analysis without generating seeds."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "reproduce_core",
        help="verify artifacts, recompute analysis, and compare generated TeX",
    )
    arguments = parser.parse_args(argv)
    if arguments.command != "reproduce_core":  # pragma: no cover
        raise AssertionError("unreachable command")
    print(json.dumps(reproduce_core(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through CLI
    raise SystemExit(_main())


__all__ = ["CoreReproductionError", "reproduce_core"]
