"""Build and safely materialize the minimal locked-artifact companion archive.

The package deliberately excludes every held-out Gate-1 seed dataset. It keeps
one development fixture required by the clean-clone test suite, the Gate-1
outer and frozen-dataset manifests, two ancillary tables, and the complete
sealed file sets of the accepted Exp15, Exp18, Exp22, and X0 runs. Source
identities are derived from the locked gate/result records rather than from
directory discovery.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import sys
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from demo.experiments.artifacts import ArtifactError, validate_manifest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARCHIVE = REPOSITORY_ROOT / "revision" / "locked-artifacts.tar.gz"
DEFAULT_PACKAGE_MANIFEST = (
    REPOSITORY_ROOT / "revision" / "artifact-package-manifest.json"
)
SCHEMA_VERSION = "locked-artifact-package-v1"
ARCHIVE_FORMAT = "tar+gzip"
GZIP_MTIME = 0
TAR_MODE = 0o644
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
MAX_MEMBER_BYTES = 128 * 1024 * 1024
MAX_UNPACKED_BYTES = 512 * 1024 * 1024

LOCK_PATHS = {
    "gate1": "revision/gate1-lock.json",
    "gate2": "revision/gate2-lock.json",
    "gate3": "revision/gate3-lock.json",
    "result": "revision/result-lock.json",
}
CALIBRATION_SOURCE_IDS = {
    "exp15": "exp15_composition_calibration",
    "exp18": "exp18_baseline_calibration",
}
SEALED_ROLES = ("exp15", "exp18", "exp22", "x0")
GATE1_ANCILLARY = {
    "dataset_manifest": (
        "work/datasets/manifest.json",
        "dataset_manifest_sha256",
    ),
    "distribution_report": (
        "tables/data_distribution_report.json",
        "distribution_report_sha256",
    ),
    "quality_summary": (
        "tables/data_quality_summary.json",
        "quality_summary_sha256",
    ),
}
GATE1_DEVELOPMENT_FIXTURE = "work/datasets/development/seed_1000.json"


class ArtifactPackageError(RuntimeError):
    """Raised when a locked package is unsafe, incomplete, or inconsistent."""


def _canonical_json_bytes(value: Any) -> bytes:
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


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _safe_relative_path(raw: Any, *, label: str) -> PurePosixPath:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise ArtifactPackageError(f"{label} is not a canonical relative path")
    path = PurePosixPath(raw)
    if (
        path.is_absolute()
        or raw != path.as_posix()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ArtifactPackageError(f"{label} is not a canonical relative path")
    return path


def _repository_path(
    repository_root: Path,
    raw: Any,
    *,
    label: str,
) -> Path:
    relative = _safe_relative_path(raw, label=label)
    root = repository_root.resolve()
    lexical = root
    for part in relative.parts:
        lexical = lexical / part
        if lexical.is_symlink():
            raise ArtifactPackageError(f"{label} traverses a symbolic link")
    resolved = lexical.resolve()
    if resolved != root and root not in resolved.parents:
        raise ArtifactPackageError(f"{label} escapes the repository")
    return lexical


def _relative_output(path: Path, repository_root: Path, *, label: str) -> str:
    root = repository_root.resolve()
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise ArtifactPackageError(f"{label} must be inside the repository") from exc
    return _safe_relative_path(relative, label=label).as_posix()


def _read_json_object(path: Path, *, label: str) -> tuple[bytes, dict[str, Any]]:
    try:
        payload = path.read_bytes()
        value = json.loads(payload)
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactPackageError(f"{label} is absent or invalid") from exc
    if not isinstance(value, dict):
        raise ArtifactPackageError(f"{label} must be a JSON object")
    return payload, value


def _require_locked_record(
    value: Mapping[str, Any],
    *,
    gate: str,
    label: str,
) -> None:
    if (
        value.get("schema_version") != 1
        or value.get("gate") != gate
        or value.get("status") != "locked"
    ):
        raise ArtifactPackageError(f"{label} is not the expected locked record")


def _run_binding(
    *,
    role: str,
    run_id: Any,
    manifest_path: Any,
    manifest_sha256: Any,
    mode: str = "sealed",
) -> dict[str, Any]:
    path = _safe_relative_path(
        manifest_path,
        label=f"{role} manifest path",
    )
    if (
        not isinstance(run_id, str)
        or not run_id
        or path.name != "manifest.json"
        or path.parts[:3] != ("demo", "artifacts", "runs")
        or len(path.parts) < 5
        or path.parent.name != run_id
        or not _is_sha256(manifest_sha256)
    ):
        raise ArtifactPackageError(f"{role} run binding is malformed")
    return {
        "manifest_path": path.as_posix(),
        "manifest_sha256": manifest_sha256,
        "mode": mode,
        "run_id": run_id,
    }


def _expected_source_bindings(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    lock_payloads: dict[str, bytes] = {}
    locks: dict[str, dict[str, Any]] = {}
    for name, relative in LOCK_PATHS.items():
        payload, value = _read_json_object(
            _repository_path(root, relative, label=f"{name} lock path"),
            label=f"{name} lock",
        )
        lock_payloads[name] = payload
        locks[name] = value

    _require_locked_record(
        locks["gate1"],
        gate="Gate 1",
        label="Gate-1 lock",
    )
    _require_locked_record(
        locks["gate2"],
        gate="Gate 2",
        label="Gate-2 lock",
    )
    _require_locked_record(
        locks["gate3"],
        gate="Gate 3",
        label="Gate-3 lock",
    )
    result = locks["result"]
    if (
        result.get("schema_version") != 1
        or result.get("gate") != "G0 result promotion"
        or result.get("status") != "locked"
    ):
        raise ArtifactPackageError("result lock is not the expected locked record")

    lock_hashes = {
        name: {
            "path": LOCK_PATHS[name],
            "sha256": _sha256(payload),
        }
        for name, payload in lock_payloads.items()
    }

    gate1 = locks["gate1"]
    gate2 = locks["gate2"]
    gate3 = locks["gate3"]
    gate1_accepted = gate1.get("accepted_run")
    gate1_data = gate1.get("data_contract")
    gate2_gate1 = gate2.get("gate1_binding")
    gate3_upstream = gate3.get("upstream_binding")
    result_gate3 = result.get("gate3_binding")
    if (
        not isinstance(gate1_accepted, Mapping)
        or not isinstance(gate1_data, Mapping)
        or not isinstance(gate2_gate1, Mapping)
        or not isinstance(gate3_upstream, Mapping)
        or not isinstance(result_gate3, Mapping)
    ):
        raise ArtifactPackageError("gate/result lock chain is incomplete")
    if (
        gate2_gate1.get("gate1_lock_sha256") != lock_hashes["gate1"]["sha256"]
        or gate2_gate1.get("accepted_run_manifest_sha256")
        != gate1_accepted.get("manifest_sha256")
        or gate2_gate1.get("dataset_manifest_sha256")
        != gate1_data.get("dataset_manifest_sha256")
        or gate3_upstream.get("gate1_lock_sha256")
        != lock_hashes["gate1"]["sha256"]
        or gate3_upstream.get("gate2_lock_sha256")
        != lock_hashes["gate2"]["sha256"]
        or result_gate3.get("sha256") != lock_hashes["gate3"]["sha256"]
    ):
        raise ArtifactPackageError("gate/result lock hash chain is inconsistent")

    gate1_binding = _run_binding(
        role="gate1",
        run_id=gate1_accepted.get("run_id"),
        manifest_path=gate1_accepted.get("manifest"),
        manifest_sha256=gate1_accepted.get("manifest_sha256"),
        mode="manifest_and_ancillary_only",
    )
    gate1_root = PurePosixPath(gate1_binding["manifest_path"]).parent
    ancillary: dict[str, dict[str, Any]] = {}
    for name, (suffix, hash_field) in GATE1_ANCILLARY.items():
        expected_sha = gate1_data.get(hash_field)
        if not _is_sha256(expected_sha):
            raise ArtifactPackageError(
                f"Gate-1 {name} checksum binding is malformed"
            )
        ancillary[name] = {
            "path": (gate1_root / PurePosixPath(suffix)).as_posix(),
            "sha256": expected_sha,
        }
    gate1_binding["ancillary"] = ancillary

    calibration_sources = gate2.get("calibration_sources")
    if not isinstance(calibration_sources, list):
        raise ArtifactPackageError("Gate-2 calibration sources are absent")
    calibration_by_id = {
        source.get("id"): source
        for source in calibration_sources
        if isinstance(source, Mapping) and isinstance(source.get("id"), str)
    }
    if set(calibration_by_id) != set(CALIBRATION_SOURCE_IDS.values()):
        raise ArtifactPackageError(
            "Gate-2 calibration source set differs from Exp15/Exp18"
        )
    runs: dict[str, dict[str, Any]] = {"gate1": gate1_binding}
    for role, source_id in CALIBRATION_SOURCE_IDS.items():
        source = calibration_by_id[source_id]
        runs[role] = _run_binding(
            role=role,
            run_id=source.get("run_id"),
            manifest_path=source.get("manifest_path"),
            manifest_sha256=source.get("manifest_sha256"),
        )

    gate3_accepted = gate3.get("accepted_run")
    if not isinstance(gate3_accepted, Mapping):
        raise ArtifactPackageError("Gate-3 accepted run is absent")
    runs["x0"] = _run_binding(
        role="x0",
        run_id=gate3_accepted.get("run_id"),
        manifest_path=gate3_accepted.get("manifest"),
        manifest_sha256=gate3_accepted.get("manifest_sha256"),
    )

    ancillary_bindings = result.get("ancillary_bindings")
    runtime = (
        ancillary_bindings.get("runtime_manifest")
        if isinstance(ancillary_bindings, Mapping)
        else None
    )
    if not isinstance(runtime, Mapping):
        raise ArtifactPackageError("result lock has no Exp22 runtime binding")
    runtime_path = _safe_relative_path(
        runtime.get("path"),
        label="Exp22 manifest path",
    )
    runs["exp22"] = _run_binding(
        role="exp22",
        run_id=runtime_path.parent.name,
        manifest_path=runtime_path.as_posix(),
        manifest_sha256=runtime.get("sha256"),
    )

    if (
        result_gate3.get("accepted_manifest_sha256")
        != runs["x0"]["manifest_sha256"]
    ):
        raise ArtifactPackageError(
            "result lock Gate-3 accepted manifest binding is inconsistent"
        )

    return {
        "locks": lock_hashes,
        "runs": runs,
    }


def _add_payload(
    payloads: dict[str, bytes],
    *,
    repository_root: Path,
    relative_path: str,
    expected_sha256: str,
) -> None:
    relative = _safe_relative_path(relative_path, label="package member path")
    path = _repository_path(
        repository_root,
        relative.as_posix(),
        label="package member path",
    )
    if path.is_symlink() or not path.is_file():
        raise ArtifactPackageError(
            f"package member is absent or unsafe: {relative.as_posix()}"
        )
    payload = path.read_bytes()
    if _sha256(payload) != expected_sha256:
        raise ArtifactPackageError(
            f"package member checksum mismatch: {relative.as_posix()}"
        )
    if relative.as_posix() in payloads:
        raise ArtifactPackageError(
            f"duplicate package member: {relative.as_posix()}"
        )
    if len(payload) > MAX_MEMBER_BYTES:
        raise ArtifactPackageError(
            f"package member is too large: {relative.as_posix()}"
        )
    payloads[relative.as_posix()] = payload


def _collect_payloads(
    repository_root: Path,
    bindings: Mapping[str, Any],
) -> dict[str, bytes]:
    root = repository_root.resolve()
    runs = bindings["runs"]
    payloads: dict[str, bytes] = {}

    gate1 = runs["gate1"]
    _add_payload(
        payloads,
        repository_root=root,
        relative_path=gate1["manifest_path"],
        expected_sha256=gate1["manifest_sha256"],
    )
    gate1_manifest_path = _repository_path(
        root,
        gate1["manifest_path"],
        label="Gate-1 manifest path",
    )
    _, gate1_manifest = _read_json_object(
        gate1_manifest_path,
        label="Gate-1 manifest",
    )
    gate1_checksums = gate1_manifest.get("checksums")
    fixture_sha = (
        gate1_checksums.get(GATE1_DEVELOPMENT_FIXTURE)
        if isinstance(gate1_checksums, Mapping)
        else None
    )
    if not _is_sha256(fixture_sha):
        raise ArtifactPackageError(
            "Gate-1 development fixture is not sealed by its manifest"
        )
    gate1_root = PurePosixPath(gate1["manifest_path"]).parent
    _add_payload(
        payloads,
        repository_root=root,
        relative_path=(gate1_root / GATE1_DEVELOPMENT_FIXTURE).as_posix(),
        expected_sha256=fixture_sha,
    )
    for record in gate1["ancillary"].values():
        _add_payload(
            payloads,
            repository_root=root,
            relative_path=record["path"],
            expected_sha256=record["sha256"],
        )

    for role in SEALED_ROLES:
        binding = runs[role]
        manifest_path = _repository_path(
            root,
            binding["manifest_path"],
            label=f"{role} manifest path",
        )
        if _file_sha256(manifest_path) != binding["manifest_sha256"]:
            raise ArtifactPackageError(f"{role} manifest checksum mismatch")
        try:
            sealed = validate_manifest(manifest_path)
        except ArtifactError as exc:
            raise ArtifactPackageError(f"{role} run is not sealed: {exc}") from exc
        if (
            sealed.get("run_id") != binding["run_id"]
            or sealed.get("status") != "succeeded"
            or sealed.get("exit_code") != 0
        ):
            raise ArtifactPackageError(f"{role} sealed-run identity is invalid")
        _add_payload(
            payloads,
            repository_root=root,
            relative_path=binding["manifest_path"],
            expected_sha256=binding["manifest_sha256"],
        )
        run_root = PurePosixPath(binding["manifest_path"]).parent
        checksums = sealed.get("checksums")
        if not isinstance(checksums, Mapping):
            raise ArtifactPackageError(f"{role} manifest checksums are absent")
        for relative_name, expected_sha in sorted(checksums.items()):
            relative = _safe_relative_path(
                relative_name,
                label=f"{role} sealed member path",
            )
            if not _is_sha256(expected_sha):
                raise ArtifactPackageError(
                    f"{role} sealed member checksum is malformed"
                )
            _add_payload(
                payloads,
                repository_root=root,
                relative_path=(run_root / relative).as_posix(),
                expected_sha256=expected_sha,
            )

    total = sum(len(payload) for payload in payloads.values())
    if total > MAX_UNPACKED_BYTES:
        raise ArtifactPackageError("package exceeds the unpacked-size limit")
    return dict(sorted(payloads.items()))


def _archive_bytes(payloads: Mapping[str, bytes]) -> bytes:
    output = io.BytesIO()
    with gzip.GzipFile(
        filename="",
        mode="wb",
        compresslevel=9,
        fileobj=output,
        mtime=GZIP_MTIME,
    ) as compressed:
        with tarfile.open(
            fileobj=compressed,
            mode="w",
            format=tarfile.USTAR_FORMAT,
        ) as archive:
            for name in sorted(payloads):
                relative = _safe_relative_path(name, label="package member path")
                payload = payloads[name]
                if not isinstance(payload, bytes):
                    raise ArtifactPackageError(
                        f"package member is not bytes: {name}"
                    )
                info = tarfile.TarInfo(relative.as_posix())
                info.size = len(payload)
                info.mtime = GZIP_MTIME
                info.mode = TAR_MODE
                info.uid = 0
                info.gid = 0
                info.uname = ""
                info.gname = ""
                info.type = tarfile.REGTYPE
                info.pax_headers = {}
                archive.addfile(info, io.BytesIO(payload))
    result = output.getvalue()
    if len(result) > MAX_ARCHIVE_BYTES:
        raise ArtifactPackageError("package exceeds the archive-size limit")
    return result


def _member_records(payloads: Mapping[str, bytes]) -> list[dict[str, Any]]:
    return [
        {
            "bytes": len(payloads[name]),
            "path": name,
            "sha256": _sha256(payloads[name]),
        }
        for name in sorted(payloads)
    ]


def create_package(
    *,
    repository_root: Path | str = REPOSITORY_ROOT,
    archive_path: Path | str | None = None,
    package_manifest_path: Path | str | None = None,
) -> tuple[Path, Path]:
    """Create the deterministic official package without replacing outputs."""

    root = Path(repository_root).resolve()
    archive = (
        root / "revision" / "locked-artifacts.tar.gz"
        if archive_path is None
        else Path(archive_path).resolve()
    )
    package_manifest = (
        root / "revision" / "artifact-package-manifest.json"
        if package_manifest_path is None
        else Path(package_manifest_path).resolve()
    )
    archive_relative = _relative_output(
        archive,
        root,
        label="archive destination",
    )
    manifest_relative = _relative_output(
        package_manifest,
        root,
        label="package-manifest destination",
    )
    if archive_relative == manifest_relative:
        raise ArtifactPackageError("archive and package manifest must differ")
    if archive.exists() or package_manifest.exists():
        raise FileExistsError("refusing to replace an artifact-package output")

    bindings = _expected_source_bindings(root)
    payloads = _collect_payloads(root, bindings)
    archive_payload = _archive_bytes(payloads)
    package_record = {
        "archive": {
            "bytes": len(archive_payload),
            "format": ARCHIVE_FORMAT,
            "gzip_mtime": GZIP_MTIME,
            "path": archive_relative,
            "sha256": _sha256(archive_payload),
            "tar_metadata": {
                "gid": 0,
                "gname": "",
                "mode": TAR_MODE,
                "mtime": GZIP_MTIME,
                "uid": 0,
                "uname": "",
            },
        },
        "member_count": len(payloads),
        "members": _member_records(payloads),
        "policy": {
            "gate1_development_fixture": GATE1_DEVELOPMENT_FIXTURE,
            "gate1_scope": (
                "manifest, dataset manifest, one development fixture, "
                "distribution report, quality summary"
            ),
            "gate1_test_seed_datasets_included": False,
            "sealed_run_roles": list(SEALED_ROLES),
        },
        "schema_version": SCHEMA_VERSION,
        "source_bindings": bindings,
    }
    manifest_payload = _canonical_json_bytes(package_record)

    archive.parent.mkdir(parents=True, exist_ok=True)
    package_manifest.parent.mkdir(parents=True, exist_ok=True)
    archive_created = False
    manifest_created = False
    try:
        with archive.open("xb") as stream:
            archive_created = True
            stream.write(archive_payload)
        with package_manifest.open("xb") as stream:
            manifest_created = True
            stream.write(manifest_payload)
    except Exception:
        if manifest_created:
            package_manifest.unlink()
        if archive_created:
            archive.unlink()
        raise
    return archive, package_manifest


def _load_package_manifest(
    package_manifest_path: Path,
    *,
    repository_root: Path,
    archive_path: Path,
) -> dict[str, Any]:
    payload, package = _read_json_object(
        package_manifest_path,
        label="artifact-package manifest",
    )
    if payload != _canonical_json_bytes(package):
        raise ArtifactPackageError(
            "artifact-package manifest is not canonical JSON"
        )
    if set(package) != {
        "archive",
        "member_count",
        "members",
        "policy",
        "schema_version",
        "source_bindings",
    } or package.get("schema_version") != SCHEMA_VERSION:
        raise ArtifactPackageError("artifact-package manifest schema is invalid")
    archive_record = package.get("archive")
    members = package.get("members")
    policy = package.get("policy")
    if (
        not isinstance(archive_record, dict)
        or set(archive_record) != {
            "bytes",
            "format",
            "gzip_mtime",
            "path",
            "sha256",
            "tar_metadata",
        }
        or archive_record.get("format") != ARCHIVE_FORMAT
        or archive_record.get("gzip_mtime") != GZIP_MTIME
        or not _is_sha256(archive_record.get("sha256"))
        or isinstance(archive_record.get("bytes"), bool)
        or not isinstance(archive_record.get("bytes"), int)
        or not 0 < archive_record["bytes"] <= MAX_ARCHIVE_BYTES
        or not isinstance(members, list)
        or package.get("member_count") != len(members)
        or not isinstance(policy, dict)
        or policy
        != {
            "gate1_development_fixture": GATE1_DEVELOPMENT_FIXTURE,
            "gate1_scope": (
                "manifest, dataset manifest, one development fixture, "
                "distribution report, quality summary"
            ),
            "gate1_test_seed_datasets_included": False,
            "sealed_run_roles": list(SEALED_ROLES),
        }
        or archive_record.get("tar_metadata")
        != {
            "gid": 0,
            "gname": "",
            "mode": TAR_MODE,
            "mtime": GZIP_MTIME,
            "uid": 0,
            "uname": "",
        }
    ):
        raise ArtifactPackageError("artifact-package metadata is invalid")
    expected_archive_relative = _relative_output(
        archive_path,
        repository_root,
        label="archive path",
    )
    if archive_record.get("path") != expected_archive_relative:
        raise ArtifactPackageError("artifact-package archive path is inconsistent")

    expected_bindings = _expected_source_bindings(repository_root)
    if package.get("source_bindings") != expected_bindings:
        raise ArtifactPackageError(
            "artifact-package source bindings differ from current locks"
        )

    previous = ""
    seen: set[str] = set()
    total = 0
    for record in members:
        if (
            not isinstance(record, dict)
            or set(record) != {"bytes", "path", "sha256"}
            or isinstance(record.get("bytes"), bool)
            or not isinstance(record.get("bytes"), int)
            or not 0 <= record["bytes"] <= MAX_MEMBER_BYTES
            or not _is_sha256(record.get("sha256"))
        ):
            raise ArtifactPackageError("artifact-package member record is invalid")
        name = _safe_relative_path(
            record.get("path"),
            label="artifact-package member path",
        ).as_posix()
        if name in seen or (previous and name <= previous):
            raise ArtifactPackageError(
                "artifact-package members are duplicated or unsorted"
            )
        seen.add(name)
        previous = name
        total += record["bytes"]
    if total > MAX_UNPACKED_BYTES:
        raise ArtifactPackageError("artifact-package unpacked size is excessive")
    return package


def _validate_tar_metadata(member: tarfile.TarInfo) -> None:
    if (
        not member.isfile()
        or member.issym()
        or member.islnk()
        or member.mtime != GZIP_MTIME
        or member.mode != TAR_MODE
        or member.uid != 0
        or member.gid != 0
        or member.uname != ""
        or member.gname != ""
        or bool(member.pax_headers)
    ):
        raise ArtifactPackageError(
            f"unsafe or nondeterministic tar member: {member.name}"
        )


def _parse_embedded_manifest(
    payload: bytes,
    *,
    role: str,
) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ArtifactPackageError(
            f"{role} embedded manifest is invalid"
        ) from exc
    if not isinstance(value, dict):
        raise ArtifactPackageError(f"{role} embedded manifest is not an object")
    return value


def _validate_member_policy(
    payloads: Mapping[str, bytes],
    records: Mapping[str, Mapping[str, Any]],
    bindings: Mapping[str, Any],
) -> None:
    runs = bindings["runs"]
    allowed: set[str] = set()

    gate1 = runs["gate1"]
    allowed.add(gate1["manifest_path"])
    allowed.update(
        record["path"] for record in gate1["ancillary"].values()
    )
    gate1_dataset_prefix = (
        PurePosixPath(gate1["manifest_path"]).parent
        / "work"
        / "datasets"
    )
    gate1_manifest_payload = payloads.get(gate1["manifest_path"])
    if gate1_manifest_payload is None:
        raise ArtifactPackageError("Gate-1 embedded manifest is missing")
    gate1_manifest = _parse_embedded_manifest(
        gate1_manifest_payload,
        role="gate1",
    )
    gate1_checksums = gate1_manifest.get("checksums")
    fixture_name = (
        PurePosixPath(gate1["manifest_path"]).parent
        / GATE1_DEVELOPMENT_FIXTURE
    ).as_posix()
    fixture_record = records.get(fixture_name)
    fixture_sha = (
        gate1_checksums.get(GATE1_DEVELOPMENT_FIXTURE)
        if isinstance(gate1_checksums, Mapping)
        else None
    )
    if (
        not _is_sha256(fixture_sha)
        or fixture_record is None
        or fixture_record.get("sha256") != fixture_sha
    ):
        raise ArtifactPackageError(
            "Gate-1 development fixture binding is incomplete"
        )
    allowed.add(fixture_name)
    for name in allowed:
        relative = PurePosixPath(name)
        if (
            gate1_dataset_prefix in relative.parents
            and name
            not in {
                gate1["ancillary"]["dataset_manifest"]["path"],
                fixture_name,
            }
        ):
            raise ArtifactPackageError(
                "non-fixture Gate-1 seed datasets are forbidden from the package"
            )

    for role in SEALED_ROLES:
        binding = runs[role]
        manifest_name = binding["manifest_path"]
        manifest_payload = payloads.get(manifest_name)
        if (
            manifest_payload is None
            or _sha256(manifest_payload) != binding["manifest_sha256"]
        ):
            raise ArtifactPackageError(f"{role} embedded manifest is missing")
        sealed = _parse_embedded_manifest(manifest_payload, role=role)
        checksums = sealed.get("checksums")
        if (
            sealed.get("schema_version") != 1
            or sealed.get("run_id") != binding["run_id"]
            or sealed.get("status") != "succeeded"
            or sealed.get("exit_code") != 0
            or not isinstance(checksums, dict)
        ):
            raise ArtifactPackageError(
                f"{role} embedded manifest identity is invalid"
            )
        allowed.add(manifest_name)
        run_root = PurePosixPath(manifest_name).parent
        for relative_name, expected_sha in checksums.items():
            relative = _safe_relative_path(
                relative_name,
                label=f"{role} embedded sealed path",
            )
            packaged_name = (run_root / relative).as_posix()
            record = records.get(packaged_name)
            if (
                not _is_sha256(expected_sha)
                or record is None
                or record.get("sha256") != expected_sha
            ):
                raise ArtifactPackageError(
                    f"{role} sealed member binding is incomplete"
                )
            allowed.add(packaged_name)

    if set(payloads) != allowed:
        unexpected = sorted(set(payloads) - allowed)
        missing = sorted(allowed - set(payloads))
        raise ArtifactPackageError(
            f"artifact-package allowlist mismatch: "
            f"unexpected={unexpected}, missing={missing}"
        )


def _verified_payloads(
    *,
    repository_root: Path,
    archive_path: Path,
    package_manifest_path: Path,
) -> tuple[dict[str, bytes], dict[str, Any]]:
    package = _load_package_manifest(
        package_manifest_path,
        repository_root=repository_root,
        archive_path=archive_path,
    )
    try:
        archive_payload = archive_path.read_bytes()
    except OSError as exc:
        raise ArtifactPackageError("artifact package archive is absent") from exc
    archive_record = package["archive"]
    if (
        len(archive_payload) != archive_record["bytes"]
        or _sha256(archive_payload) != archive_record["sha256"]
    ):
        raise ArtifactPackageError("artifact package archive checksum mismatch")
    if (
        len(archive_payload) < 10
        or archive_payload[:3] != b"\x1f\x8b\x08"
        or archive_payload[3] != 0
        or int.from_bytes(archive_payload[4:8], "little") != GZIP_MTIME
    ):
        raise ArtifactPackageError(
            "artifact package gzip header is not deterministic"
        )

    records = {record["path"]: record for record in package["members"]}
    payloads: dict[str, bytes] = {}
    seen: set[str] = set()
    observed_order: list[str] = []
    try:
        with tarfile.open(
            fileobj=io.BytesIO(archive_payload),
            mode="r:gz",
        ) as archive:
            for member in archive.getmembers():
                name = _safe_relative_path(
                    member.name,
                    label="tar member path",
                ).as_posix()
                if name in seen:
                    raise ArtifactPackageError(
                        f"duplicate tar member: {name}"
                    )
                seen.add(name)
                observed_order.append(name)
                _validate_tar_metadata(member)
                record = records.get(name)
                if record is None or member.size != record["bytes"]:
                    raise ArtifactPackageError(
                        f"unlisted or size-mismatched tar member: {name}"
                    )
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise ArtifactPackageError(
                        f"tar member cannot be read: {name}"
                    )
                payload = extracted.read()
                if (
                    len(payload) != record["bytes"]
                    or _sha256(payload) != record["sha256"]
                ):
                    raise ArtifactPackageError(
                        f"tar member checksum mismatch: {name}"
                    )
                payloads[name] = payload
    except (tarfile.TarError, OSError, EOFError) as exc:
        raise ArtifactPackageError("artifact package tar stream is invalid") from exc
    if seen != set(records):
        raise ArtifactPackageError(
            "artifact package tar member set is incomplete"
        )
    if observed_order != sorted(records):
        raise ArtifactPackageError(
            "artifact package tar members are not deterministically ordered"
        )
    _validate_member_policy(
        payloads,
        records,
        package["source_bindings"],
    )
    return payloads, package


def verify_package(
    *,
    repository_root: Path | str = REPOSITORY_ROOT,
    archive_path: Path | str | None = None,
    package_manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    """Verify archive bytes, members, allowlist, and the current lock chain."""

    root = Path(repository_root).resolve()
    archive = (
        root / "revision" / "locked-artifacts.tar.gz"
        if archive_path is None
        else Path(archive_path).resolve()
    )
    package_manifest = (
        root / "revision" / "artifact-package-manifest.json"
        if package_manifest_path is None
        else Path(package_manifest_path).resolve()
    )
    payloads, package = _verified_payloads(
        repository_root=root,
        archive_path=archive,
        package_manifest_path=package_manifest,
    )
    return {
        "archive_bytes": package["archive"]["bytes"],
        "archive_sha256": package["archive"]["sha256"],
        "member_count": len(payloads),
        "status": "pass",
    }


def _target_path(root: Path, relative_name: str) -> Path:
    relative = _safe_relative_path(
        relative_name,
        label="materialized member path",
    )
    return root.joinpath(*relative.parts)


def _check_parent_chain(root: Path, target: Path) -> None:
    current = root
    for part in target.relative_to(root).parts[:-1]:
        current = current / part
        if current.exists() or current.is_symlink():
            if current.is_symlink() or not current.is_dir():
                raise ArtifactPackageError(
                    f"unsafe materialization parent: {current}"
                )


def _create_parent_chain(root: Path, target: Path) -> None:
    current = root
    for part in target.relative_to(root).parts[:-1]:
        current = current / part
        if current.exists() or current.is_symlink():
            if current.is_symlink() or not current.is_dir():
                raise ArtifactPackageError(
                    f"unsafe materialization parent: {current}"
                )
        else:
            current.mkdir()


def _materialize_verified(
    payloads: Mapping[str, bytes],
    *,
    materialize_root: Path,
) -> dict[str, Any]:
    root = materialize_root.resolve()
    if root.is_symlink() or not root.is_dir():
        raise ArtifactPackageError("materialization root must be a real directory")

    missing: list[tuple[str, Path]] = []
    existing = 0
    for name, payload in payloads.items():
        target = _target_path(root, name)
        _check_parent_chain(root, target)
        if target.exists() or target.is_symlink():
            if (
                target.is_symlink()
                or not target.is_file()
                or target.stat().st_size != len(payload)
                or _file_sha256(target) != _sha256(payload)
            ):
                raise ArtifactPackageError(
                    f"existing materialized member differs: {name}"
                )
            existing += 1
        else:
            missing.append((name, target))

    created: list[Path] = []
    try:
        for name, target in missing:
            _create_parent_chain(root, target)
            with target.open("xb") as stream:
                created.append(target)
                stream.write(payloads[name])
    except Exception:
        for target in reversed(created):
            try:
                target.unlink()
            except FileNotFoundError:
                pass
        raise
    return {
        "created": len(missing),
        "existing": existing,
        "member_count": len(payloads),
        "status": "pass",
    }


def materialize_package(
    *,
    materialize_root: Path | str,
    archive_path: Path | str | None = None,
    package_manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    """Verify first, then restore missing allowlisted members below a repo root."""

    requested_root = Path(materialize_root)
    if requested_root.is_symlink():
        raise ArtifactPackageError(
            "materialization root must not be a symbolic link"
        )
    root = requested_root.resolve()
    archive = (
        root / "revision" / "locked-artifacts.tar.gz"
        if archive_path is None
        else Path(archive_path).resolve()
    )
    package_manifest = (
        root / "revision" / "artifact-package-manifest.json"
        if package_manifest_path is None
        else Path(package_manifest_path).resolve()
    )
    payloads, _ = _verified_payloads(
        repository_root=root,
        archive_path=archive,
        package_manifest_path=package_manifest,
    )
    return _materialize_verified(payloads, materialize_root=root)


def extract_package(
    *,
    repository_root: Path | str,
    destination: Path | str,
    archive_path: Path | str | None = None,
    package_manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    """Verify and extract into a new or existing empty directory."""

    source_root = Path(repository_root).resolve()
    archive = (
        source_root / "revision" / "locked-artifacts.tar.gz"
        if archive_path is None
        else Path(archive_path).resolve()
    )
    package_manifest = (
        source_root / "revision" / "artifact-package-manifest.json"
        if package_manifest_path is None
        else Path(package_manifest_path).resolve()
    )
    payloads, _ = _verified_payloads(
        repository_root=source_root,
        archive_path=archive,
        package_manifest_path=package_manifest,
    )

    output = Path(destination)
    if output.exists() or output.is_symlink():
        if output.is_symlink() or not output.is_dir() or any(output.iterdir()):
            raise ArtifactPackageError(
                "extraction destination must be an empty real directory"
            )
    else:
        output.mkdir(parents=True)
    return _materialize_verified(payloads, materialize_root=output)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--package-manifest", type=Path)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="verify the existing package instead of creating it",
    )
    parser.add_argument(
        "--materialize-root",
        type=Path,
        help=(
            "after verification, retain matching files and create only missing "
            "allowlisted members below this repository root"
        ),
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    try:
        if args.materialize_root is not None and not args.verify:
            raise ArtifactPackageError("--materialize-root requires --verify")

        root = (
            args.materialize_root
            if args.materialize_root is not None
            else (
                args.repository_root
                if args.repository_root is not None
                else REPOSITORY_ROOT
            )
        )
        archive = args.archive or root / "revision" / "locked-artifacts.tar.gz"
        package_manifest = (
            args.package_manifest
            or root / "revision" / "artifact-package-manifest.json"
        )
        if args.verify:
            if args.materialize_root is not None:
                report = materialize_package(
                    materialize_root=root,
                    archive_path=archive,
                    package_manifest_path=package_manifest,
                )
            else:
                report = verify_package(
                    repository_root=root,
                    archive_path=archive,
                    package_manifest_path=package_manifest,
                )
        else:
            created_archive, created_manifest = create_package(
                repository_root=root,
                archive_path=archive,
                package_manifest_path=package_manifest,
            )
            report = {
                "archive": str(created_archive),
                "package_manifest": str(created_manifest),
                "status": "created",
            }
    except (ArtifactPackageError, FileExistsError) as exc:
        print(f"artifact package failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ArtifactPackageError",
    "create_package",
    "extract_package",
    "materialize_package",
    "verify_package",
]
