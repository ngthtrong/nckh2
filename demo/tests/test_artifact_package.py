from __future__ import annotations

import gzip
import hashlib
import io
import json
import shutil
import tarfile
from pathlib import Path
from typing import Any

import pytest

from demo.experiments import package_locked_artifacts as package


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _write_json(path: Path, value: Any) -> bytes:
    payload = package._canonical_json_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return payload


def _sealed_run(
    root: Path,
    *,
    run_id: str,
    result_name: str,
) -> tuple[str, str]:
    run_root = root / "demo" / "artifacts" / "runs" / run_id
    result_relative = f"tables/{result_name}"
    result_payload = package._canonical_json_bytes(
        {"result": result_name, "run_id": run_id}
    )
    result = run_root / result_relative
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_bytes(result_payload)
    log = run_root / "logs" / "stdout.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_bytes(b"fixture\n")
    manifest = {
        "checksums": {
            "logs/stdout.log": _sha256(b"fixture\n"),
            result_relative: _sha256(result_payload),
        },
        "command": ["python", "-m", f"fixture.{run_id}"],
        "environment": {
            "blas": {},
            "hardware": {},
            "threads": {},
        },
        "exit_code": 0,
        "inputs": {
            "config": {},
            "protocol": {},
            "seed_manifest": {},
        },
        "repository": {
            "commit": "a" * 40,
            "dirty_patch_sha256": "b" * 64,
            "root": "/historical/repository",
        },
        "run_id": run_id,
        "schema_version": 1,
        "status": "succeeded",
        "timestamps": {
            "ended_at_utc": "2026-01-01T00:00:01+00:00",
            "started_at_utc": "2026-01-01T00:00:00+00:00",
        },
    }
    manifest_path = run_root / "manifest.json"
    manifest_payload = _write_json(manifest_path, manifest)
    return (
        manifest_path.relative_to(root).as_posix(),
        _sha256(manifest_payload),
    )


def _fixture_repository(root: Path) -> Path:
    gate1_id = "gate1-fixture"
    gate1_root = root / "demo" / "artifacts" / "runs" / gate1_id
    development_fixture = package._canonical_json_bytes(
        {"reports": [], "seed": 1000, "split": "development"}
    )
    development_path = (
        gate1_root
        / "work"
        / "datasets"
        / "development"
        / "seed_1000.json"
    )
    development_path.parent.mkdir(parents=True, exist_ok=True)
    development_path.write_bytes(development_fixture)
    dataset_manifest = _write_json(
        gate1_root / "work" / "datasets" / "manifest.json",
        {
            "entries": [
                {
                    "path": "test/seed_3000.json",
                    "sha256": _sha256(b"raw-held-out-fixture"),
                },
            ],
            "schema_version": "fixture-dataset-manifest",
        },
    )
    distribution = _write_json(
        gate1_root / "tables" / "data_distribution_report.json",
        {"distribution": "fixture"},
    )
    quality = _write_json(
        gate1_root / "tables" / "data_quality_summary.json",
        {"quality": "pass"},
    )
    gate1_manifest = {
        "checksums": {
            "tables/data_distribution_report.json": _sha256(distribution),
            "tables/data_quality_summary.json": _sha256(quality),
            "work/datasets/manifest.json": _sha256(dataset_manifest),
            "work/datasets/development/seed_1000.json": _sha256(
                development_fixture
            ),
            "work/datasets/test/seed_3000.json": _sha256(
                b"raw-held-out-fixture"
            ),
        },
        "exit_code": 0,
        "run_id": gate1_id,
        "schema_version": 1,
        "status": "succeeded",
    }
    gate1_manifest_path = gate1_root / "manifest.json"
    gate1_manifest_payload = _write_json(
        gate1_manifest_path,
        gate1_manifest,
    )

    exp15_path, exp15_sha = _sealed_run(
        root,
        run_id="exp15-fixture",
        result_name="exp15.json",
    )
    exp18_path, exp18_sha = _sealed_run(
        root,
        run_id="exp18-fixture",
        result_name="exp18.json",
    )
    exp22_path, exp22_sha = _sealed_run(
        root,
        run_id="exp22-fixture",
        result_name="exp22.json",
    )
    x0_path, x0_sha = _sealed_run(
        root,
        run_id="x0-fixture",
        result_name="exp23.json",
    )

    gate1_lock = {
        "accepted_run": {
            "manifest": gate1_manifest_path.relative_to(root).as_posix(),
            "manifest_sha256": _sha256(gate1_manifest_payload),
            "run_id": gate1_id,
        },
        "data_contract": {
            "dataset_manifest_sha256": _sha256(dataset_manifest),
            "distribution_report_sha256": _sha256(distribution),
            "quality_summary_sha256": _sha256(quality),
        },
        "gate": "Gate 1",
        "schema_version": 1,
        "status": "locked",
    }
    gate1_lock_payload = _write_json(
        root / "revision" / "gate1-lock.json",
        gate1_lock,
    )
    gate2_lock = {
        "calibration_sources": [
            {
                "id": "exp15_composition_calibration",
                "manifest_path": exp15_path,
                "manifest_sha256": exp15_sha,
                "run_id": "exp15-fixture",
            },
            {
                "id": "exp18_baseline_calibration",
                "manifest_path": exp18_path,
                "manifest_sha256": exp18_sha,
                "run_id": "exp18-fixture",
            },
        ],
        "gate": "Gate 2",
        "gate1_binding": {
            "accepted_run_manifest_sha256": _sha256(
                gate1_manifest_payload
            ),
            "dataset_manifest_sha256": _sha256(dataset_manifest),
            "gate1_lock_sha256": _sha256(gate1_lock_payload),
        },
        "schema_version": 1,
        "status": "locked",
    }
    gate2_lock_payload = _write_json(
        root / "revision" / "gate2-lock.json",
        gate2_lock,
    )
    gate3_lock = {
        "accepted_run": {
            "manifest": x0_path,
            "manifest_sha256": x0_sha,
            "run_id": "x0-fixture",
        },
        "gate": "Gate 3",
        "schema_version": 1,
        "status": "locked",
        "upstream_binding": {
            "gate1_lock_sha256": _sha256(gate1_lock_payload),
            "gate2_lock_sha256": _sha256(gate2_lock_payload),
        },
    }
    gate3_lock_payload = _write_json(
        root / "revision" / "gate3-lock.json",
        gate3_lock,
    )
    result_lock = {
        "ancillary_bindings": {
            "runtime_manifest": {
                "path": exp22_path,
                "sha256": exp22_sha,
            },
        },
        "gate": "G0 result promotion",
        "gate3_binding": {
            "accepted_manifest_sha256": x0_sha,
            "sha256": _sha256(gate3_lock_payload),
        },
        "schema_version": 1,
        "status": "locked",
    }
    _write_json(root / "revision" / "result-lock.json", result_lock)
    return root


def _archive_payloads(archive_path: Path) -> dict[str, bytes]:
    with tarfile.open(archive_path, "r:gz") as archive:
        return {
            member.name: archive.extractfile(member).read()
            for member in archive.getmembers()
            if member.isfile()
        }


def _replace_archive(
    root: Path,
    archive_payload: bytes,
) -> None:
    archive_path = root / "revision" / "locked-artifacts.tar.gz"
    manifest_path = root / "revision" / "artifact-package-manifest.json"
    package_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    package_manifest["archive"]["bytes"] = len(archive_payload)
    package_manifest["archive"]["sha256"] = _sha256(archive_payload)
    archive_path.write_bytes(archive_payload)
    manifest_path.write_bytes(package._canonical_json_bytes(package_manifest))


def _malicious_archive(
    entries: list[tuple[tarfile.TarInfo, bytes | None]],
) -> bytes:
    output = io.BytesIO()
    with gzip.GzipFile(
        filename="",
        mode="wb",
        compresslevel=9,
        fileobj=output,
        mtime=0,
    ) as compressed:
        with tarfile.open(
            fileobj=compressed,
            mode="w",
            format=tarfile.USTAR_FORMAT,
        ) as archive:
            for info, payload in entries:
                info.mtime = 0
                info.mode = 0o644
                info.uid = 0
                info.gid = 0
                info.uname = ""
                info.gname = ""
                info.pax_headers = {}
                archive.addfile(
                    info,
                    None if payload is None else io.BytesIO(payload),
                )
    return output.getvalue()


def test_package_is_deterministic_exclusive_and_omits_gate1_test_data(
    tmp_path: Path,
) -> None:
    first = _fixture_repository(tmp_path / "first")
    second = _fixture_repository(tmp_path / "second")
    first_archive, first_manifest = package.create_package(
        repository_root=first
    )
    second_archive, second_manifest = package.create_package(
        repository_root=second
    )

    assert first_archive.read_bytes() == second_archive.read_bytes()
    assert first_manifest.read_bytes() == second_manifest.read_bytes()
    assert package.verify_package(repository_root=first)["status"] == "pass"
    with pytest.raises(FileExistsError):
        package.create_package(repository_root=first)

    names = set(_archive_payloads(first_archive))
    gate1_prefix = "demo/artifacts/runs/gate1-fixture/work/datasets/"
    assert f"{gate1_prefix}manifest.json" in names
    assert f"{gate1_prefix}development/seed_1000.json" in names
    assert not any(
        name.startswith(f"{gate1_prefix}test/")
        or name.startswith(f"{gate1_prefix}calibration/")
        or (
            name.startswith(f"{gate1_prefix}development/")
            and name != f"{gate1_prefix}development/seed_1000.json"
        )
        for name in names
    )


def test_verify_rejects_archive_tamper_and_missing_member(
    tmp_path: Path,
) -> None:
    root = _fixture_repository(tmp_path / "repository")
    archive_path, _ = package.create_package(repository_root=root)
    original = archive_path.read_bytes()
    archive_path.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
    with pytest.raises(
        package.ArtifactPackageError,
        match="archive checksum mismatch",
    ):
        package.verify_package(repository_root=root)

    archive_path.write_bytes(original)
    payloads = _archive_payloads(archive_path)
    payloads.pop(sorted(payloads)[-1])
    _replace_archive(root, package._archive_bytes(payloads))
    with pytest.raises(
        package.ArtifactPackageError,
        match="member set is incomplete",
    ):
        package.verify_package(repository_root=root)


@pytest.mark.parametrize("kind", ["parent", "absolute", "symlink", "duplicate"])
def test_verify_rejects_unsafe_or_duplicate_tar_members(
    tmp_path: Path,
    kind: str,
) -> None:
    root = _fixture_repository(tmp_path / kind)
    archive_path, _ = package.create_package(repository_root=root)
    payloads = _archive_payloads(archive_path)
    valid_name = sorted(payloads)[0]
    valid_payload = payloads[valid_name]

    if kind == "duplicate":
        first = tarfile.TarInfo(valid_name)
        first.size = len(valid_payload)
        second = tarfile.TarInfo(valid_name)
        second.size = len(valid_payload)
        entries = [(first, valid_payload), (second, valid_payload)]
    elif kind == "symlink":
        link = tarfile.TarInfo("demo/artifacts/runs/unsafe-link")
        link.type = tarfile.SYMTYPE
        link.linkname = "../../escape"
        link.size = 0
        entries = [(link, None)]
    else:
        name = "../escape" if kind == "parent" else "/absolute"
        unsafe = tarfile.TarInfo(name)
        unsafe.size = 1
        entries = [(unsafe, b"x")]

    _replace_archive(root, _malicious_archive(entries))
    with pytest.raises(package.ArtifactPackageError):
        package.verify_package(repository_root=root)


def test_materialize_keeps_exact_creates_missing_and_refuses_mismatch(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _fixture_repository(tmp_path / "repository")
    package.create_package(repository_root=root)
    manifest = json.loads(
        (root / "revision" / "artifact-package-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    member_names = [record["path"] for record in manifest["members"]]
    shutil.rmtree(root / "demo" / "artifacts")

    assert package.main(
        ["--verify", "--materialize-root", str(root)]
    ) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["created"] == first["member_count"]
    assert package.materialize_package(materialize_root=root)["created"] == 0
    assert not (
        root
        / "demo"
        / "artifacts"
        / "runs"
        / "gate1-fixture"
        / "work"
        / "datasets"
        / "test"
        / "seed_3000.json"
    ).exists()

    mismatch = root / member_names[0]
    missing = root / member_names[-1]
    mismatch.write_bytes(b"tampered")
    missing.unlink()
    with pytest.raises(
        package.ArtifactPackageError,
        match="existing materialized member differs",
    ):
        package.materialize_package(materialize_root=root)
    assert not missing.exists()


def test_extract_requires_empty_destination(tmp_path: Path) -> None:
    root = _fixture_repository(tmp_path / "repository")
    package.create_package(repository_root=root)
    nonempty = tmp_path / "nonempty"
    nonempty.mkdir()
    (nonempty / "keep.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(
        package.ArtifactPackageError,
        match="empty real directory",
    ):
        package.extract_package(
            repository_root=root,
            destination=nonempty,
        )

    empty = tmp_path / "empty"
    report = package.extract_package(
        repository_root=root,
        destination=empty,
    )
    assert report["created"] == report["member_count"]
