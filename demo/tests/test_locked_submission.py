from __future__ import annotations

import ast
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from demo.experiments import lock_submission
from demo.experiments.pre_gate2 import canonical_json_bytes
from demo.experiments.promote_results import (
    REQUIRED_DISCLOSURE_CLAIMS,
    build_compact_summary,
)
from demo.experiments.verify_locked_submission import (
    DEFAULT_STALE_TERM_PATTERNS,
    EXPECTED_PROMOTED_ARTIFACTS,
    VerificationError,
    load_submission_policy,
    verify_archive_projection_and_selectors,
    verify_artifact_package,
    verify_figure_policy,
    verify_manuscript_claims,
    verify_result_lock,
    verify_stale_terms,
    verify_tex_log,
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _content_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _write_bytes(root: Path, relative: str, payload: bytes) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def _write_canonical(root: Path, relative: str, value: object) -> Path:
    return _write_bytes(root, relative, canonical_json_bytes(value))


def _record(relative: str, payload: bytes) -> dict[str, object]:
    return {
        "path": relative,
        "sha256": _sha256(payload),
        "bytes": len(payload),
    }


def _policy() -> dict[str, object]:
    return {
        "artifact_policy": {
            "deterministic_json_comparison": "byte-exact",
            "figure_policy": (
                "no figures are included by the revised manuscript"
            ),
            "heldout_reexecution_permitted": False,
        },
        "external_submission_inputs": {
            "public_repository_or_doi": "external-blocked",
            "venue_page_limit": None,
            "venue_page_limit_status": "external-blocked",
        },
        "paper_policy": {
            "allow_underfull_boxes": True,
            "bibliography_engine": "bibtex",
            "build_sequence": [
                "xelatex",
                "bibtex",
                "xelatex",
                "xelatex",
            ],
            "expected_page_count": 11,
            "latex_engine": "xelatex",
            "maximum_overfull_points": 5.0,
            "require_no_undefined_citations": True,
            "require_no_undefined_references": True,
        },
        "profile": "test-profile",
        "schema_version": 1,
        "status": "locked-local-policy",
    }


def test_load_submission_policy_preserves_external_blockers(
    tmp_path: Path,
) -> None:
    path = _write_canonical(
        tmp_path,
        "revision/submission-policy.json",
        _policy(),
    )
    policy = load_submission_policy(path)
    assert policy.expected_page_count == 11
    assert policy.maximum_overfull_points == 5.0
    assert policy.build_sequence == (
        "xelatex",
        "bibtex",
        "xelatex",
        "xelatex",
    )
    assert policy.external_submission_inputs["venue_page_limit"] is None


def _build_result_lock_fixture(root: Path) -> None:
    promoted: dict[str, dict[str, object]] = {}
    for name, relative in EXPECTED_PROMOTED_ARTIFACTS.items():
        payload = f"locked:{name}\n".encode()
        _write_bytes(root, relative, payload)
        promoted[name] = _record(relative, payload)

    script_payload = b"# sealed promoter\n"
    _write_bytes(
        root,
        "demo/experiments/promote_results.py",
        script_payload,
    )
    accepted_manifest = {
        "exit_code": 0,
        "run_id": "accepted",
        "status": "succeeded",
    }
    manifest_payload = json.dumps(accepted_manifest).encode()
    _write_bytes(
        root,
        "demo/artifacts/runs/accepted/manifest.json",
        manifest_payload,
    )
    _write_bytes(root, "demo/artifacts/runs/gate1/manifest.json", b"gate1")
    _write_bytes(root, "demo/artifacts/runs/runtime/manifest.json", b"runtime")
    rejected = {"runs": [], "schema_version": 1}
    rejected_payload = canonical_json_bytes(rejected)
    _write_bytes(root, "revision/rejected-runs.json", rejected_payload)

    gate3 = {
        "accepted_run": {
            "exit_code": 0,
            "invocation": {
                "candidate_suite_invocation": 1,
                "path": "work/x0-invocation.json",
                "sha256": "1" * 64,
            },
            "manifest": "demo/artifacts/runs/accepted/manifest.json",
            "manifest_sha256": _sha256(manifest_payload),
            "result": {
                "artifact_content_sha256": "2" * 64,
                "path": "tables/exp23_heldout_evaluation.json",
                "sha256": "3" * 64,
                "status": "succeeded",
            },
            "run_id": "accepted",
            "selectors": {
                "path": "tables/exp23_heldout_selectors.json",
                "selector_content_sha256": "4" * 64,
                "selector_count": 448,
                "sha256": "5" * 64,
            },
            "status": "succeeded",
        },
        "gate": "Gate 3",
        "rejected_run_ledger": {
            "path": "revision/rejected-runs.json",
            "run_count": 0,
            "sha256": _sha256(rejected_payload),
        },
        "schema_version": 1,
        "status": "locked",
    }
    gate3_payload = canonical_json_bytes(gate3)
    _write_bytes(root, "revision/gate3-lock.json", gate3_payload)
    result_lock = {
        "ancillary_bindings": {
            "gate1_manifest": {
                "path": "demo/artifacts/runs/gate1/manifest.json",
                "sha256": _sha256(b"gate1"),
            },
            "runtime_manifest": {
                "path": "demo/artifacts/runs/runtime/manifest.json",
                "sha256": _sha256(b"runtime"),
            },
        },
        "gate": "G0 result promotion",
        "gate3_binding": {
            "accepted_artifact_content_sha256": "2" * 64,
            "accepted_manifest_sha256": _sha256(manifest_payload),
            "accepted_result_sha256": "3" * 64,
            "accepted_run_id": "accepted",
            "accepted_selector_content_sha256": "4" * 64,
            "accepted_selector_sha256": "5" * 64,
            "path": "revision/gate3-lock.json",
            "sha256": _sha256(gate3_payload),
        },
        "promoted_artifacts": promoted,
        "promotion_script": {
            "path": "demo/experiments/promote_results.py",
            "sha256": _sha256(script_payload),
        },
        "schema_version": 1,
        "status": "locked",
        "traceability": {
            "all_base_selectors_resolve": True,
            "all_claim_values_and_rounding_recomputed": True,
            "complete_archive_round_trip": True,
            "negative_tie_adverse_failure_and_exclusion_evidence_retained": True,
        },
        "validation": {
            "claim_selector_and_rendering": "pass",
            "compact_selector_resolution": "pass",
            "complete_archive_round_trip": "pass",
            "exclusive_transaction": "pass",
            "gate1_ancillary_binding": "pass",
            "gate3_and_upstream_binding": "pass",
            "gate3_candidate_revalidation": "pass",
            "rejected_run_exclusion": "pass",
            "runtime_manifest_and_equivalence": "pass",
            "validation_errors": [],
        },
    }
    _write_canonical(root, "revision/result-lock.json", result_lock)


def test_result_lock_verifies_allowlist_and_rejects_tampering(
    tmp_path: Path,
) -> None:
    _build_result_lock_fixture(tmp_path)
    result = verify_result_lock(tmp_path)
    assert result["promoted_artifact_count"] == 9
    assert result["accepted_run_id"] == "accepted"

    target = tmp_path / EXPECTED_PROMOTED_ARTIFACTS["traceability.md"]
    target.write_bytes(b"tampered")
    with pytest.raises(VerificationError, match="byte count|SHA-256"):
        verify_result_lock(tmp_path)


def _build_archive_fixture(root: Path) -> None:
    raw: dict[str, object] = {
        "clustering": {
            "per_seed_rows": [{"seed": 3000}],
            "summary": {"mean": 0.5},
        },
        "dispatch_outcomes": {
            "per_seed_resource_policy_rows": [{"seed": 3000}]
        },
        "factorial_ablation": {
            "clustering": {"rows": [{"seed": 3000}]},
            "priority": {"rows": [{"seed": 3000}]},
        },
        "method_track_registry": {
            "exclusions": [{"method_id": "excluded"}],
            "selections": [{"method_id": "selected"}],
        },
        "priority_robustness": {"scenario_rows": [{"seed": 3000}]},
        "schema_version": "fixture",
    }
    raw["artifact_content_sha256"] = _sha256(_content_bytes(raw))
    raw_payload = canonical_json_bytes(raw)
    archive_payload = gzip.compress(raw_payload, compresslevel=9, mtime=0)
    archive_relative = (
        "demo/results/tables/exp23_heldout_evaluation.json.gz"
    )
    _write_bytes(root, archive_relative, archive_payload)

    selector_rows = [
        {
            "id": f"fixture.selector.{index}",
            "json_pointer": "/clustering/summary/mean",
            "kind": "fixture",
        }
        for index in range(448)
    ]
    selectors: dict[str, object] = {
        "schema_version": "fixture",
        "selector_count": 448,
        "selectors": selector_rows,
        "source_artifact_content_sha256": raw[
            "artifact_content_sha256"
        ],
        "source_schema_version": "fixture",
    }
    selectors["selector_content_sha256"] = _sha256(
        _content_bytes(selectors)
    )
    selector_payload = canonical_json_bytes(selectors)
    selector_relative = "demo/results/tables/exp23_heldout_selectors.json"
    _write_bytes(root, selector_relative, selector_payload)

    archive_record = {
        **_record(archive_relative, archive_payload),
        "compression": "gzip level 9, mtime 0",
        "decompressed_bytes": len(raw_payload),
        "decompressed_sha256": _sha256(raw_payload),
    }
    source_record = {
        "artifact_content_sha256": raw["artifact_content_sha256"],
        "manifest_path": "demo/artifacts/runs/accepted/manifest.json",
        "manifest_sha256": "1" * 64,
        "result_path": "demo/artifacts/runs/accepted/tables/result.json",
        "result_sha256": _sha256(raw_payload),
        "run_id": "accepted",
        "selector_content_sha256": selectors[
            "selector_content_sha256"
        ],
        "selector_path": (
            "demo/artifacts/runs/accepted/tables/selectors.json"
        ),
        "selector_sha256": _sha256(selector_payload),
    }
    compact = build_compact_summary(
        raw,
        source_record=source_record,
        raw_archive_record=archive_record,
        gate3_lock_sha256="6" * 64,
    )
    compact_payload = canonical_json_bytes(compact)
    compact_relative = "demo/results/tables/exp23_heldout_summary.json"
    _write_bytes(root, compact_relative, compact_payload)

    lock = {
        "coverage": {
            "excluded_method_track_pairs": 1,
            "selected_method_track_pairs": 1,
        },
        "gate3_binding": {
            "accepted_artifact_content_sha256": raw[
                "artifact_content_sha256"
            ],
            "accepted_manifest_sha256": "1" * 64,
            "accepted_result_sha256": _sha256(raw_payload),
            "accepted_run_id": "accepted",
            "accepted_selector_content_sha256": selectors[
                "selector_content_sha256"
            ],
            "accepted_selector_sha256": _sha256(selector_payload),
            "sha256": "6" * 64,
        },
        "promoted_artifacts": {
            "exp23_heldout_evaluation.json.gz": _record(
                archive_relative,
                archive_payload,
            ),
            "exp23_heldout_selectors.json": _record(
                selector_relative,
                selector_payload,
            ),
            "exp23_heldout_summary.json": _record(
                compact_relative,
                compact_payload,
            ),
        },
        "traceability": {"base_selector_count": 448},
    }
    _write_canonical(root, "revision/result-lock.json", lock)


def test_archive_projection_and_all_448_selectors(tmp_path: Path) -> None:
    _build_archive_fixture(tmp_path)
    result = verify_archive_projection_and_selectors(tmp_path)
    assert result["selector_count"] == 448
    assert result["omitted_raw_rows"] == 5
    assert set(result["omitted_sections"]) == {
        "/clustering/per_seed_rows",
        "/factorial_ablation/clustering/rows",
        "/factorial_ablation/priority/rows",
        "/priority_robustness/scenario_rows",
        "/dispatch_outcomes/per_seed_resource_policy_rows",
    }


def _write_claim_manuscript(root: Path, claim_ids: list[str]) -> None:
    catalog = {"claims": [{"id": identifier} for identifier in claim_ids]}
    _write_canonical(root, "loop/revision/claim-selectors.json", catalog)
    _write_bytes(
        root,
        "paper/generated/revision_results.tex",
        b"% fixture\n",
    )
    uses = "\n".join(
        f"\\RevisionClaim{{{identifier}}}" for identifier in claim_ids
    )
    _write_bytes(
        root,
        "paper/main.tex",
        (
            "\\input{generated/revision_results.tex}\n" + uses + "\n"
        ).encode(),
    )


def test_manuscript_requires_every_mandatory_disclosure(
    tmp_path: Path,
) -> None:
    required = sorted(REQUIRED_DISCLOSURE_CLAIMS)
    _write_claim_manuscript(tmp_path, required)
    result = verify_manuscript_claims(tmp_path)
    assert result["mandatory_disclosure_count"] == 10

    _write_claim_manuscript(tmp_path, required[:-1])
    with pytest.raises(VerificationError, match="mandatory disclosures"):
        verify_manuscript_claims(tmp_path)


def test_tex_log_checks_pages_overfull_and_undefined(tmp_path: Path) -> None:
    log = tmp_path / "main.log"
    log.write_text(
        "\n".join(
                [
                    "This is XeTeX",
                    r"Overfull \hbox (4.9pt too wide) in paragraph",
                "Package amsmath Warning: harmless fixture.",
                "Package: infwarerr Providing info/warning/error messages",
                "Output written on main.pdf (11 pages).",
            ]
        ),
        encoding="utf-8",
    )
    result = verify_tex_log(
        log,
        expected_page_count=11,
        maximum_overfull_points=5.0,
        allow_underfull_boxes=True,
        require_no_undefined_citations=True,
        require_no_undefined_references=True,
        strict_warnings=True,
        allowed_warning_patterns=(r"^Package amsmath Warning:",),
    )
    assert result["page_count"] == 11
    assert result["maximum_overfull_points"] == 4.9
    assert result["warning_count"] == 1
    assert result["unallowed_warning_count"] == 0

    log.write_text(
        r"Overfull \hbox (5.01pt too wide)" "\n"
        "Output written on main.pdf (11 pages).\n",
        encoding="utf-8",
    )
    with pytest.raises(VerificationError, match="overfull"):
        verify_tex_log(
            log,
            expected_page_count=11,
            maximum_overfull_points=5.0,
            allow_underfull_boxes=True,
            require_no_undefined_citations=True,
            require_no_undefined_references=True,
        )

    log.write_text(
        "LaTeX Warning: Citation `missing' undefined.\n"
        "Output written on main.pdf (11 pages).\n",
        encoding="utf-8",
    )
    with pytest.raises(VerificationError, match="undefined citations"):
        verify_tex_log(
            log,
            expected_page_count=11,
            maximum_overfull_points=5.0,
            allow_underfull_boxes=True,
            require_no_undefined_citations=True,
            require_no_undefined_references=True,
        )


def test_stale_terms_and_figure_orphans_are_rejected(
    tmp_path: Path,
) -> None:
    _write_bytes(tmp_path, "README.md", b"Current locked study.\n")
    verify_stale_terms(
        tmp_path,
        paths=(Path("README.md"),),
        patterns=DEFAULT_STALE_TERM_PATTERNS,
    )
    _write_bytes(tmp_path, "README.md", b"Run from demo/v2 with seed 42.\n")
    with pytest.raises(VerificationError, match="stale legacy terms"):
        verify_stale_terms(
            tmp_path,
            paths=(Path("README.md"),),
            patterns=DEFAULT_STALE_TERM_PATTERNS,
        )

    _write_bytes(
        tmp_path,
        "paper/main.tex",
        b"\\includegraphics{figures/used}\n",
    )
    _write_bytes(tmp_path, "paper/figures/used.png", b"png")
    result = verify_figure_policy(tmp_path)
    assert result["referenced_figure_count"] == 1

    _write_bytes(tmp_path, "paper/figures/orphan.png", b"png")
    with pytest.raises(VerificationError, match="orphan"):
        verify_figure_policy(tmp_path)


def test_no_figure_policy_rejects_includegraphics(tmp_path: Path) -> None:
    _write_bytes(
        tmp_path,
        "paper/main.tex",
        b"\\includegraphics{figures/used.png}\n",
    )
    _write_bytes(tmp_path, "paper/figures/used.png", b"png")
    with pytest.raises(VerificationError, match="forbids"):
        verify_figure_policy(
            tmp_path,
            policy="no figures are included by the revised manuscript",
        )


def test_artifact_package_rejects_tamper_and_traversal(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    payload = b"sealed"
    _write_bytes(package, "runs/a/manifest.json", payload)
    manifest = {
        "files": [
            {
                "bytes": len(payload),
                "path": "runs/a/manifest.json",
                "sha256": _sha256(payload),
            }
        ]
    }
    manifest_path = _write_canonical(
        tmp_path,
        "artifact-manifest.json",
        manifest,
    )
    result = verify_artifact_package(
        tmp_path,
        package_path=package,
        manifest_path=manifest_path,
    )
    assert result["contents_verified"] is True

    _write_bytes(package, "runs/a/manifest.json", b"changed")
    with pytest.raises(VerificationError, match="differs"):
        verify_artifact_package(
            tmp_path,
            package_path=package,
            manifest_path=manifest_path,
        )

    _write_canonical(
        tmp_path,
        "bad-manifest.json",
        {
            "files": [
                {"bytes": 1, "path": "../escape", "sha256": "0" * 64}
            ]
        },
    )
    with pytest.raises(VerificationError, match="unsafe"):
        verify_artifact_package(
            tmp_path,
            package_path=package,
            manifest_path=tmp_path / "bad-manifest.json",
        )


def test_verifier_has_no_experiment_execution_import_or_call() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "experiments"
        / "verify_locked_submission.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    forbidden_modules = {
        "demo.experiments.authorize_x0",
        "demo.experiments.exp23_heldout_evaluation",
        "demo.experiments.run_candidate",
    }
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert not (forbidden_modules & imported_modules)

    forbidden_calls = {
        "authorize",
        "load_locked_test_seeds",
        "load_x0_authorization",
        "run_once",
        "validate_candidate",
    }
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called.update(
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    )
    assert not (forbidden_calls & called)


def _minimal_submission_lock_fixture(root: Path) -> None:
    _write_canonical(
        root,
        "revision/clean-room-verification.json",
        {
            "schema_version": 1,
            "status": "pass",
            "summary": {"fail": 0, "incomplete": 0, "pass": 1},
        },
    )
    _write_canonical(
        root,
        "revision/submission-policy.json",
        {
            "external_submission_inputs": {
                "public_repository_or_doi": "external-blocked"
            },
            "profile": "test-profile",
        },
    )
    _write_bytes(root, "revision/clean-room-full.log", b"PASS\n")


def _minimal_lock_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        lock_submission,
        "SUBMISSION_GLOBS",
        ("revision/*.json", "revision/*.log"),
    )
    monkeypatch.setattr(
        lock_submission,
        "REQUIRED_PATHS",
        frozenset({"revision/clean-room-full.log"}),
    )


def test_submission_lock_rejects_missing_clean_room_transcript(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _minimal_lock_settings(monkeypatch)
    _minimal_submission_lock_fixture(tmp_path)
    manifest = lock_submission.build_submission_manifest(tmp_path)
    _write_bytes(
        tmp_path,
        lock_submission.MANIFEST_RELATIVE,
        lock_submission._canonical_json_bytes(manifest),
    )
    (tmp_path / "revision/clean-room-full.log").unlink()

    with pytest.raises(
        lock_submission.SubmissionLockError,
        match="clean-room-full[.]log",
    ):
        lock_submission.verify_submission_lock(tmp_path)


def test_submission_lock_detects_crlf_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _minimal_lock_settings(monkeypatch)
    _minimal_submission_lock_fixture(tmp_path)
    manifest = lock_submission.build_submission_manifest(tmp_path)
    _write_bytes(
        tmp_path,
        lock_submission.MANIFEST_RELATIVE,
        lock_submission._canonical_json_bytes(manifest),
    )
    _write_bytes(
        tmp_path,
        "revision/clean-room-full.log",
        b"first\r\nsecond\r\n",
    )

    with pytest.raises(
        lock_submission.SubmissionLockError,
        match="not canonical LF",
    ):
        lock_submission.verify_submission_lock(tmp_path)


def test_submission_lock_rejects_present_untracked_required_member(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _minimal_lock_settings(monkeypatch)
    _minimal_submission_lock_fixture(tmp_path)
    subprocess.run(
        ["git", "init", "-q", str(tmp_path)],
        check=True,
        capture_output=True,
    )

    with pytest.raises(
        lock_submission.SubmissionLockError,
        match="not Git-tracked",
    ):
        lock_submission.build_submission_manifest(tmp_path)


def test_required_submission_paths_exist_and_are_git_tracked() -> None:
    root = Path(__file__).resolve().parents[2]
    missing = sorted(
        relative
        for relative in lock_submission.REQUIRED_PATHS
        if not (root / relative).is_file()
    )
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    tracked = {
        raw.decode("utf-8", errors="surrogateescape")
        for raw in completed.stdout.split(b"\0")
        if raw
    }
    untracked = sorted(lock_submission.REQUIRED_PATHS - tracked)

    assert not missing
    assert not untracked


def test_submission_text_and_json_are_canonical_lf() -> None:
    root = Path(__file__).resolve().parents[2]
    paths = lock_submission.collect_submission_paths(root)
    lock_submission.verify_canonical_lf(paths, root)
    json_paths = [
        path for path in paths if path.suffix.lower() == ".json"
    ] + [root / lock_submission.MANIFEST_RELATIVE]
    assert json_paths
    assert all(b"\r" not in path.read_bytes() for path in json_paths)


def test_checked_in_submission_lock_verifies() -> None:
    root = Path(__file__).resolve().parents[2]
    result = lock_submission.verify_submission_lock(root)
    assert result["status"] == "pass"
    assert result["file_count"] >= len(lock_submission.REQUIRED_PATHS)


def test_reproduce_verifies_final_lock_without_running_x0() -> None:
    root = Path(__file__).resolve().parents[2]
    script = (root / "reproduce.sh").read_text(encoding="utf-8")
    post_verifier = script.rindex(
        "-m demo.experiments.verify_locked_submission"
    )
    final_lock = script.index(
        "-m demo.experiments.lock_submission",
        post_verifier,
    )
    final_pass = script.index("PASS:", final_lock)
    lock_step = script[final_lock:final_pass]

    assert "--verify" in lock_step
    assert post_verifier < final_lock < final_pass
    for forbidden in (
        "demo.experiments.authorize_x0",
        "demo.experiments.exp23_heldout_evaluation",
        "demo.experiments.run_candidate",
    ):
        assert forbidden not in script
