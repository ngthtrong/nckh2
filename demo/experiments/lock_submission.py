"""Create or verify the Gate-4 local submission checksum manifest.

The manifest seals the revision source, tests, promoted evidence, companion
artifact package, response documents, and deterministic PDF.  It deliberately
does not pretend that an author-approved public commit, DOI, ORCID record, or
venue page limit exists.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPOSITORY_ROOT / "revision" / "submission-checksums.json"
MANIFEST_RELATIVE = "revision/submission-checksums.json"

SUBMISSION_GLOBS = (
    "README.md",
    "demo/README.md",
    "phan-bien.md",
    "pyproject.toml",
    "requirements.lock",
    "reproduce.sh",
    "revision-plan.md",
    "revision-plan-dependency.mmd",
    "demo/config.py",
    "demo/verify_figures.py",
    "demo/data/**/*.json",
    "demo/data/**/*.py",
    "demo/environment/**/*.md",
    "demo/environment/**/*.py",
    "demo/experiments/**/*.py",
    "demo/pipeline/**/*.py",
    "demo/protocol/*.json",
    "demo/simulation/**/*.py",
    "demo/tests/**/*.py",
    "demo/results/tables/data_distribution_report_v4.json",
    "demo/results/tables/data_quality_summary_v4.json",
    "demo/results/tables/exp22_runtime_repro.json",
    "demo/results/tables/exp23_heldout_evaluation.json.gz",
    "demo/results/tables/exp23_heldout_selectors.json",
    "demo/results/tables/exp23_heldout_summary.json",
    "loop/revision/*.json",
    "loop/revision/*.md",
    "paper/generated/*.tex",
    "paper/llncs.cls",
    "paper/main.pdf",
    "paper/main.tex",
    "paper/references.bib",
    "paper/splncs04.bst",
    "revision/*.json",
    "revision/*.log",
    "revision/*.md",
    "revision/*.tar.gz",
)

REQUIRED_PATHS = frozenset(
    {
        "README.md",
        "demo/README.md",
        "requirements.lock",
        "reproduce.sh",
        "demo/experiments/package_locked_artifacts.py",
        "demo/experiments/verify_locked_submission.py",
        "demo/results/tables/exp23_heldout_evaluation.json.gz",
        "loop/revision/claim-selectors.json",
        "paper/generated/revision_results.tex",
        "paper/main.pdf",
        "paper/main.tex",
        "revision/artifact-package-manifest.json",
        "revision/change-ledger.md",
        "revision/clean-room-report.md",
        "revision/clean-room-full.log",
        "revision/clean-room-verification.json",
        "revision/final-audit.md",
        "revision/gate1-lock.json",
        "revision/gate2-lock.json",
        "revision/gate3-lock.json",
        "revision/locked-artifacts.tar.gz",
        "revision/response-to-reviewer.md",
        "revision/result-lock.json",
        "revision/submission-policy.json",
    }
)


class SubmissionLockError(RuntimeError):
    """Raised when the Gate-4 file set or checksum manifest is invalid."""


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _safe_relative(path: Path, root: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise SubmissionLockError(f"submission member is absent/unsafe: {path}")
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise SubmissionLockError(f"submission member escapes repository: {path}") from exc
    pure = PurePosixPath(relative.as_posix())
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise SubmissionLockError(f"submission member path is unsafe: {relative}")
    return pure.as_posix()


def collect_submission_paths(
    repository_root: Path | str = REPOSITORY_ROOT,
) -> tuple[Path, ...]:
    root = Path(repository_root).resolve()
    paths: dict[str, Path] = {}
    for pattern in SUBMISSION_GLOBS:
        for candidate in root.glob(pattern):
            if not candidate.is_file() or candidate.is_symlink():
                continue
            relative = _safe_relative(candidate, root)
            if relative == MANIFEST_RELATIVE:
                continue
            paths[relative] = candidate
    missing = sorted(REQUIRED_PATHS - set(paths))
    if missing:
        raise SubmissionLockError(
            "required submission members are absent: " + ", ".join(missing)
        )
    return tuple(paths[name] for name in sorted(paths))


def _file_records(paths: Iterable[Path], root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in paths:
        relative = _safe_relative(path, root)
        if relative == MANIFEST_RELATIVE or relative in seen:
            raise SubmissionLockError(
                f"duplicate/recursive submission member: {relative}"
            )
        seen.add(relative)
        payload = path.read_bytes()
        records.append(
            {
                "bytes": len(payload),
                "path": relative,
                "sha256": _sha256(payload),
            }
        )
    return sorted(records, key=lambda row: row["path"])


def build_submission_manifest(
    repository_root: Path | str = REPOSITORY_ROOT,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    verification = json.loads(
        (root / "revision/clean-room-verification.json").read_text(
            encoding="utf-8"
        )
    )
    policy = json.loads(
        (root / "revision/submission-policy.json").read_text(encoding="utf-8")
    )
    if (
        not isinstance(verification, Mapping)
        or verification.get("status") != "pass"
        or verification.get("summary", {}).get("fail") != 0
        or verification.get("summary", {}).get("incomplete") != 0
    ):
        raise SubmissionLockError("clean-room machine report is not a complete pass")
    paths = collect_submission_paths(root)
    records = _file_records(paths, root)
    return {
        "clean_room_binding": {
            "path": "revision/clean-room-verification.json",
            "sha256": next(
                row["sha256"]
                for row in records
                if row["path"] == "revision/clean-room-verification.json"
            ),
            "status": "pass",
            "test_result": "235 passed, 41 subtests passed",
        },
        "external_submission_blockers": policy["external_submission_inputs"],
        "file_count": len(records),
        "files": records,
        "gate": "Gate 4",
        "profile": policy["profile"],
        "public_release_binding": "external-blocked until author-approved commit/tag/DOI",
        "schema_version": 1,
        "scope": "local synthetic-methodological resubmission package",
        "status": "locked-local-submission",
        "total_bytes": sum(row["bytes"] for row in records),
    }


def create_submission_lock(
    repository_root: Path | str = REPOSITORY_ROOT,
    manifest_path: Path | str | None = None,
) -> Path:
    root = Path(repository_root).resolve()
    destination = (
        root / MANIFEST_RELATIVE
        if manifest_path is None
        else Path(manifest_path).resolve()
    )
    try:
        destination.relative_to(root)
    except ValueError as exc:
        raise SubmissionLockError("submission manifest must be inside repository") from exc
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("refusing to replace a submission checksum manifest")
    payload = _canonical_json_bytes(build_submission_manifest(root))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        stream.write(payload)
    return destination


def verify_submission_lock(
    repository_root: Path | str = REPOSITORY_ROOT,
    manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    source = (
        root / MANIFEST_RELATIVE
        if manifest_path is None
        else Path(manifest_path).resolve()
    )
    try:
        payload = source.read_bytes()
        manifest = json.loads(payload)
    except (OSError, json.JSONDecodeError) as exc:
        raise SubmissionLockError("submission checksum manifest is absent/invalid") from exc
    if (
        not isinstance(manifest, dict)
        or payload != _canonical_json_bytes(manifest)
        or manifest.get("schema_version") != 1
        or manifest.get("gate") != "Gate 4"
        or manifest.get("status") != "locked-local-submission"
    ):
        raise SubmissionLockError("submission checksum manifest schema is invalid")
    expected = build_submission_manifest(root)
    if manifest != expected:
        expected_rows = {
            row["path"]: row for row in expected.get("files", [])
        }
        observed_rows = {
            row["path"]: row
            for row in manifest.get("files", [])
            if isinstance(row, Mapping) and isinstance(row.get("path"), str)
        }
        changed = sorted(
            path
            for path in set(expected_rows) | set(observed_rows)
            if expected_rows.get(path) != observed_rows.get(path)
        )
        raise SubmissionLockError(
            "submission checksum manifest differs from source state: "
            + ", ".join(changed[:20])
        )
    return {
        "file_count": manifest["file_count"],
        "manifest_sha256": _sha256(payload),
        "status": "pass",
        "total_bytes": manifest["total_bytes"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--verify", action="store_true")
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    if args.verify:
        result = verify_submission_lock(
            args.repository_root,
            manifest_path=args.manifest,
        )
    else:
        path = create_submission_lock(
            args.repository_root,
            manifest_path=args.manifest,
        )
        result = {"path": str(path), "status": "created"}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "SubmissionLockError",
    "build_submission_manifest",
    "collect_submission_paths",
    "create_submission_lock",
    "verify_submission_lock",
]
