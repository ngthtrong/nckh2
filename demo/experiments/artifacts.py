"""Immutable candidate-run layout and provenance manifest support."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


DEMO_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = DEMO_ROOT.parent
DEFAULT_RUNS_ROOT = DEMO_ROOT / "artifacts" / "runs"
DEFAULT_PROTOCOL_DIR = DEMO_ROOT / "protocol"
DEFAULT_CONFIG_PATH = DEMO_ROOT / "pipeline" / "config.py"
DEFAULT_DATASET_PATH = DEMO_ROOT / "data" / "dataset.json"

if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

try:
    from demo.environment.capture import capture_environment
except ImportError:  # Direct use with demo on sys.path.
    from environment.capture import capture_environment  # type: ignore[no-redef]

try:
    from .protocol import (
        METRIC_CONTRACT_NAME,
        SEED_MANIFEST_NAME,
        file_sha256,
        protocol_bundle_sha256,
    )
except ImportError:  # Direct use with demo/experiments on sys.path.
    from protocol import (  # type: ignore[no-redef]
        METRIC_CONTRACT_NAME,
        SEED_MANIFEST_NAME,
        file_sha256,
        protocol_bundle_sha256,
    )


SAFE_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
LOCKED_RUN_ID = re.compile(
    r"^\d{8}T\d{6}Z-[0-9a-f]{7,12}-[0-9a-f]{8}"
    r"(?:-[a-z0-9][a-z0-9-]{0,31})?$"
)


class ArtifactError(RuntimeError):
    """Raised for an invalid or non-immutable candidate artifact operation."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _run_git(
    repository_root: Path,
    arguments: Sequence[str],
    *,
    accepted_exit_codes: tuple[int, ...] = (0,),
) -> bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode not in accepted_exit_codes:
        error = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ArtifactError(
            f"git {' '.join(arguments)} failed with {completed.returncode}: {error}"
        )
    return completed.stdout


def _repository_capture(repository_root: Path) -> tuple[dict[str, Any], bytes, bytes]:
    root = repository_root.resolve()
    top_level = Path(
        _run_git(root, ("rev-parse", "--show-toplevel"))
        .decode("utf-8", errors="strict")
        .strip()
    ).resolve()
    if top_level != root:
        raise ArtifactError(
            f"repository_root must be the Git top level: {root} != {top_level}"
        )

    commit = (
        _run_git(root, ("rev-parse", "HEAD"))
        .decode("ascii", errors="strict")
        .strip()
    )
    branch = (
        _run_git(root, ("rev-parse", "--abbrev-ref", "HEAD"))
        .decode("utf-8", errors="replace")
        .strip()
    )
    status = _run_git(
        root, ("status", "--porcelain=v1", "--untracked-files=all", "-z")
    )
    tracked_patch = _run_git(root, ("diff", "--binary", "HEAD", "--"))
    untracked_raw = _run_git(
        root, ("ls-files", "--others", "--exclude-standard", "-z")
    )
    untracked_names = [
        name
        for name in untracked_raw.decode("utf-8", errors="surrogateescape").split("\0")
        if name
    ]

    patch_parts = [tracked_patch]
    untracked_records: list[dict[str, Any]] = []
    for relative_name in sorted(untracked_names):
        source = root / relative_name
        if source.is_symlink():
            target = os.readlink(source)
            untracked_records.append(
                {
                    "path": relative_name,
                    "kind": "symlink",
                    "target": target,
                    "sha256": sha256_bytes(target.encode("utf-8")),
                }
            )
            continue
        if not source.is_file():
            continue
        payload_sha = file_sha256(source)
        untracked_records.append(
            {
                "path": relative_name,
                "kind": "file",
                "bytes": source.stat().st_size,
                "sha256": payload_sha,
            }
        )
        untracked_patch = _run_git(
            root,
            ("diff", "--binary", "--no-index", "--", "/dev/null", relative_name),
            accepted_exit_codes=(0, 1),
        )
        patch_parts.append(untracked_patch)

    patch = b"".join(patch_parts)
    status_text = status.decode("utf-8", errors="replace")
    capture = {
        "root": str(root),
        "commit": commit,
        "short_commit": commit[:12],
        "branch": branch,
        "dirty": bool(status),
        "status_sha256": sha256_bytes(status),
        "dirty_patch_sha256": sha256_bytes(patch),
        "dirty_patch_bytes": len(patch),
        "untracked_files": untracked_records,
    }
    return capture, patch, status_text.encode("utf-8")


def _safe_child(root: Path, relative_path: Path | str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ArtifactError(f"artifact path must be relative and contained: {relative}")
    destination = (root / relative).resolve()
    resolved_root = root.resolve()
    if destination != resolved_root and resolved_root not in destination.parents:
        raise ArtifactError(f"artifact path escapes the run directory: {relative}")
    return destination


def _exclusive_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except FileExistsError as exc:
        raise ArtifactError(f"refusing to overwrite artifact: {path}") from exc


def _relative_source(path: Path, repository_root: Path) -> str:
    try:
        return path.resolve().relative_to(repository_root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _snapshot_input(
    source: Path,
    destination: Path,
    repository_root: Path,
) -> dict[str, Any]:
    if not source.is_file():
        raise ArtifactError(f"input file does not exist: {source}")
    payload = source.read_bytes()
    _exclusive_write(destination, payload)
    return {
        "source": _relative_source(source, repository_root),
        "snapshot": destination.name,
        "bytes": len(payload),
        "sha256": sha256_bytes(payload),
    }


def _collect_checksums(run_dir: Path) -> tuple[dict[str, str], list[str]]:
    checksums: dict[str, str] = {}
    violations: list[str] = []
    for path in sorted(run_dir.rglob("*")):
        relative = path.relative_to(run_dir).as_posix()
        if path.name == "manifest.json":
            continue
        if path.is_symlink():
            violations.append(f"symbolic links are not allowed in a run: {relative}")
        elif path.is_file():
            checksums[relative] = file_sha256(path)
    return checksums, violations


@dataclass
class ArtifactRun:
    """One exclusively created candidate-run directory."""

    run_id: str
    path: Path
    repository_root: Path
    command: tuple[str, ...]
    working_directory: Path
    started_at_utc: str
    repository: dict[str, Any]
    environment: dict[str, Any]
    inputs: dict[str, Any]
    _finalized: bool = field(default=False, init=False, repr=False)

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        command: Sequence[str],
        runs_root: Path | str = DEFAULT_RUNS_ROOT,
        repository_root: Path | str = REPOSITORY_ROOT,
        protocol_dir: Path | str = DEFAULT_PROTOCOL_DIR,
        config_path: Path | str = DEFAULT_CONFIG_PATH,
        dataset_paths: Iterable[Path | str] = (DEFAULT_DATASET_PATH,),
        working_directory: Path | str | None = None,
    ) -> "ArtifactRun":
        if not SAFE_RUN_ID.fullmatch(run_id):
            raise ArtifactError(
                "run_id must contain only letters, digits, '.', '_', and '-' "
                "and be at most 128 characters"
            )
        if not command or any(not isinstance(part, str) or not part for part in command):
            raise ArtifactError("command must be a non-empty sequence of strings")

        root = Path(runs_root).resolve()
        if (root / run_id).exists():
            raise ArtifactError(f"refusing existing run_id: {run_id}")
        repository_path = Path(repository_root).resolve()
        working_path = (
            repository_path
            if working_directory is None
            else Path(working_directory).resolve()
        )
        if working_path != repository_path and repository_path not in working_path.parents:
            raise ArtifactError("working directory must be inside the repository")

        # Capture source identity before creating an ignored runtime directory.
        repository, dirty_patch, git_status = _repository_capture(repository_path)
        environment = capture_environment()

        root.mkdir(parents=True, exist_ok=True)
        run_path = root / run_id
        try:
            run_path.mkdir()
        except FileExistsError as exc:
            raise ArtifactError(f"refusing existing run_id: {run_id}") from exc

        for relative in (
            "figures",
            "inputs",
            "logs",
            "provenance",
            "tables",
            "work",
        ):
            (run_path / relative).mkdir()

        _exclusive_write(run_path / "provenance" / "dirty.patch", dirty_patch)
        _exclusive_write(run_path / "provenance" / "git-status.txt", git_status)
        _exclusive_write(
            run_path / "provenance" / "environment.json",
            _json_bytes(environment),
        )

        protocol_path = Path(protocol_dir).resolve()
        seed_source = protocol_path / SEED_MANIFEST_NAME
        metric_source = protocol_path / METRIC_CONTRACT_NAME
        protocol_files: dict[str, Any] = {}
        for source in sorted(protocol_path.glob("*.json")):
            if not source.is_file():
                continue
            destination = run_path / "inputs" / "protocol" / source.name
            record = _snapshot_input(source, destination, repository_path)
            record["snapshot"] = destination.relative_to(run_path).as_posix()
            protocol_files[source.name] = record
        if (
            SEED_MANIFEST_NAME not in protocol_files
            or METRIC_CONTRACT_NAME not in protocol_files
        ):
            raise ArtifactError("protocol directory is missing required JSON files")

        config_source = Path(config_path).resolve()
        config_suffix = "".join(config_source.suffixes) or ".bin"
        config_destination = run_path / "inputs" / f"config{config_suffix}"
        config_record = _snapshot_input(
            config_source, config_destination, repository_path
        )
        config_record["snapshot"] = config_destination.relative_to(run_path).as_posix()

        dataset_records: list[dict[str, Any]] = []
        for index, raw_source in enumerate(dataset_paths):
            source = Path(raw_source).resolve()
            destination = (
                run_path / "inputs" / "datasets" / f"{index:02d}-{source.name}"
            )
            record = _snapshot_input(source, destination, repository_path)
            record["snapshot"] = destination.relative_to(run_path).as_posix()
            dataset_records.append(record)

        protocol_hash = protocol_bundle_sha256(seed_source, metric_source)
        inputs = {
            "config": config_record,
            "seed_manifest": protocol_files[SEED_MANIFEST_NAME],
            "metric_contract": protocol_files[METRIC_CONTRACT_NAME],
            "protocol": {
                "sha256": protocol_hash,
                "files": protocol_files,
            },
            "datasets": dataset_records,
        }
        started_at = utc_now()
        start_record = {
            "schema_version": 1,
            "run_id": run_id,
            "started_at_utc": started_at,
            "command": list(command),
            "working_directory": _relative_source(
                working_path, repository_path
            ),
            "repository": repository,
            "input_hashes": {
                "config": config_record["sha256"],
                "seed_manifest": protocol_files[SEED_MANIFEST_NAME]["sha256"],
                "metric_contract": protocol_files[METRIC_CONTRACT_NAME]["sha256"],
                "protocol": protocol_hash,
                "datasets": [record["sha256"] for record in dataset_records],
            },
        }
        _exclusive_write(
            run_path / "provenance" / "run-start.json",
            _json_bytes(start_record),
        )

        return cls(
            run_id=run_id,
            path=run_path,
            repository_root=repository_path,
            command=tuple(command),
            working_directory=working_path,
            started_at_utc=started_at,
            repository=repository,
            environment=environment,
            inputs=inputs,
        )

    @property
    def writable_directories(self) -> tuple[Path, ...]:
        return tuple(self.path / name for name in ("figures", "tables", "work"))

    def output_path(self, relative_path: Path | str) -> Path:
        """Resolve a candidate output below figures, tables, or work."""

        if self._finalized:
            raise ArtifactError("run is already finalized")
        relative = Path(relative_path)
        if not relative.parts or relative.parts[0] not in {
            "figures",
            "tables",
            "work",
        }:
            raise ArtifactError("candidate outputs must be below figures/, tables/, or work/")
        return _safe_child(self.path, relative)

    def write_bytes(self, relative_path: Path | str, payload: bytes) -> Path:
        """Write an output once, refusing path escape and replacement."""

        destination = self.output_path(relative_path)
        _exclusive_write(destination, payload)
        return destination

    def write_json(self, relative_path: Path | str, value: Any) -> Path:
        return self.write_bytes(relative_path, _json_bytes(value))

    def finalize(
        self,
        *,
        exit_code: int,
        status: str | None = None,
        error: str | None = None,
    ) -> Path:
        """Seal the run with a final manifest and content checksums."""

        if self._finalized:
            raise ArtifactError("run is already finalized")
        if isinstance(exit_code, bool) or not isinstance(exit_code, int):
            raise ArtifactError("exit_code must be an integer")
        effective_status = status or ("succeeded" if exit_code == 0 else "failed")
        if effective_status not in {"succeeded", "failed", "aborted"}:
            raise ArtifactError(f"invalid run status: {effective_status}")

        checksums, violations = _collect_checksums(self.path)
        if violations:
            effective_status = "failed"
            exit_code = exit_code if exit_code != 0 else 125
            error = "; ".join(filter(None, (error, *violations)))

        manifest = {
            "schema_version": 1,
            "run_id": self.run_id,
            "status": effective_status,
            "exit_code": exit_code,
            "timestamps": {
                "started_at_utc": self.started_at_utc,
                "ended_at_utc": utc_now(),
            },
            "command": list(self.command),
            "working_directory": _relative_source(
                self.working_directory, self.repository_root
            ),
            "repository": {
                **self.repository,
                "dirty_patch_path": "provenance/dirty.patch",
                "git_status_path": "provenance/git-status.txt",
            },
            "environment": self.environment,
            "inputs": self.inputs,
            "output_directories": {
                "tables": "tables",
                "figures": "figures",
                "work": "work",
                "logs": "logs",
            },
            "checksums": checksums,
            "error": error,
        }
        manifest_path = self.path / "manifest.json"
        _exclusive_write(manifest_path, _json_bytes(manifest))
        self._finalized = True
        return manifest_path


def generate_run_id(
    *,
    repository_root: Path | str = REPOSITORY_ROOT,
    protocol_dir: Path | str = DEFAULT_PROTOCOL_DIR,
    label: str | None = None,
    now: datetime | None = None,
) -> str:
    """Build the required UTC/commit/protocol candidate-run identifier."""

    root = Path(repository_root).resolve()
    commit = (
        _run_git(root, ("rev-parse", "HEAD"))
        .decode("ascii", errors="strict")
        .strip()
    )
    directory = Path(protocol_dir).resolve()
    protocol_hash = protocol_bundle_sha256(
        directory / SEED_MANIFEST_NAME,
        directory / METRIC_CONTRACT_NAME,
    )
    timestamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    result = (
        f"{timestamp.strftime('%Y%m%dT%H%M%SZ')}-"
        f"{commit[:12]}-{protocol_hash[:8]}"
    )
    if label:
        normalized = re.sub(r"[^a-z0-9]+", "-", label.casefold()).strip("-")
        if not normalized:
            raise ArtifactError("run label must contain at least one letter or digit")
        result = f"{result}-{normalized[:32].rstrip('-')}"
    if not LOCKED_RUN_ID.fullmatch(result):
        raise ArtifactError(f"generated run_id does not satisfy the lock format: {result}")
    return result


def validate_manifest(path: Path | str) -> dict[str, Any]:
    """Validate required final-manifest fields and all recorded checksums."""

    manifest_path = Path(path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ArtifactError(f"invalid run manifest: {manifest_path}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ArtifactError("unsupported run-manifest schema")
    required = (
        "run_id",
        "status",
        "exit_code",
        "timestamps",
        "command",
        "repository",
        "environment",
        "inputs",
        "checksums",
    )
    missing = [name for name in required if name not in manifest]
    if missing:
        raise ArtifactError(f"run manifest is missing fields: {', '.join(missing)}")
    repository = manifest["repository"]
    environment = manifest["environment"]
    inputs = manifest["inputs"]
    if (
        not isinstance(repository, dict)
        or not isinstance(environment, dict)
        or not isinstance(inputs, dict)
        or "commit" not in repository
        or "dirty_patch_sha256" not in repository
        or "hardware" not in environment
        or "blas" not in environment
        or "threads" not in environment
        or "config" not in inputs
        or "protocol" not in inputs
        or "seed_manifest" not in inputs
    ):
        raise ArtifactError("run manifest provenance is incomplete")
    run_dir = manifest_path.parent
    checksums = manifest["checksums"]
    if not isinstance(checksums, dict):
        raise ArtifactError("manifest checksums must be an object")
    for relative, expected in checksums.items():
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise ArtifactError("invalid checksum record")
        source = _safe_child(run_dir, relative)
        if source.is_symlink() or not source.is_file():
            raise ArtifactError(f"checksummed artifact is absent or unsafe: {relative}")
        actual = file_sha256(source)
        if actual != expected:
            raise ArtifactError(
                f"checksum mismatch for {relative}: expected {expected}, got {actual}"
            )
    return manifest


__all__ = [
    "ArtifactError",
    "ArtifactRun",
    "DEFAULT_CONFIG_PATH",
    "DEFAULT_DATASET_PATH",
    "DEFAULT_PROTOCOL_DIR",
    "DEFAULT_RUNS_ROOT",
    "LOCKED_RUN_ID",
    "generate_run_id",
    "sha256_bytes",
    "validate_manifest",
]
