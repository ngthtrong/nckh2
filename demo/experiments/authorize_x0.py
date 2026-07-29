"""Create the immutable single-invocation authorization for held-out X0.

The command authenticates Gate 1, Gate 2, every promoted configuration, and
the complete released seed identity without opening a test dataset.  It then
captures the exact dirty source state and exclusively creates
``revision/x0-release.json``.  Exp23 refuses to read test data without this
record.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from demo.experiments.artifacts import _repository_capture, sha256_bytes
from demo.experiments.evaluation_data import (
    DEFAULT_GATE1_LOCK,
    DEFAULT_GATE2_LOCK,
    DEFAULT_SELECTED_CONFIGS,
    load_selected_configs,
)
from demo.experiments.evaluation_protocol import load_locked_test_seeds
from demo.experiments.exp23_heldout_evaluation import (
    DEFAULT_X0_RELEASE,
    EXPECTED_EXCLUSION_PAIR_COUNT,
    EXPECTED_SELECTED_PAIR_COUNT,
    EXPECTED_TEST_SEED_COUNT,
    SOURCE_FILES,
    _canonical_json_bytes,
    _source_hashes,
)
from demo.experiments.pre_gate2 import canonical_json_bytes
from demo.experiments.protocol import DEFAULT_PROTOCOL_DIR, file_sha256


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _git_diff_check(repository_root: Path) -> None:
    completed = subprocess.run(
        ["git", "diff", "--check"],
        cwd=repository_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = (
            completed.stdout + completed.stderr
        ).decode("utf-8", errors="replace")
        raise ValueError(f"git diff --check failed before X0 authorization: {detail}")


def build_authorization(
    *,
    repository_root: Path = REPOSITORY_ROOT,
) -> dict[str, Any]:
    """Build and self-check the authorization without reading test datasets."""

    _git_diff_check(repository_root)
    bundle = load_selected_configs(
        DEFAULT_SELECTED_CONFIGS,
        gate2_lock=DEFAULT_GATE2_LOCK,
        protocol_dir=DEFAULT_PROTOCOL_DIR,
        artifact_root=repository_root,
    )
    released = load_locked_test_seeds(DEFAULT_GATE2_LOCK, DEFAULT_PROTOCOL_DIR)
    if (
        len(released) != EXPECTED_TEST_SEED_COUNT
        or len(bundle.selections) != EXPECTED_SELECTED_PAIR_COUNT
        or len(bundle.exclusions) != EXPECTED_EXCLUSION_PAIR_COUNT
    ):
        raise ValueError("Gate-2 release does not match the complete X0 contract")
    gate2 = json.loads(DEFAULT_GATE2_LOCK.read_text(encoding="utf-8"))
    repository, _, _ = _repository_capture(repository_root)
    source_hashes = _source_hashes(repository_root)
    if set(source_hashes) != set(SOURCE_FILES):
        raise ValueError("X0 source-file capture is incomplete")
    authorization: dict[str, Any] = {
        "schema_version": "x0-release-v1",
        "status": "authorized",
        "authorized_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "one complete held-out candidate suite after Gate 2",
        "maximum_candidate_suite_invocations": 1,
        "expected_test_seed_count": EXPECTED_TEST_SEED_COUNT,
        "expected_test_seed_sha256": sha256_bytes(
            _canonical_json_bytes(list(released))
        ),
        "expected_selected_method_track_pairs": (
            EXPECTED_SELECTED_PAIR_COUNT
        ),
        "expected_no_feasible_method_track_pairs": (
            EXPECTED_EXCLUSION_PAIR_COUNT
        ),
        "gate1_lock_sha256": file_sha256(DEFAULT_GATE1_LOCK),
        "gate2_lock_sha256": file_sha256(DEFAULT_GATE2_LOCK),
        "protocol_sha256": gate2["protocol_sha256"],
        "selected_configs_sha256": file_sha256(DEFAULT_SELECTED_CONFIGS),
        "runner_sha256": file_sha256(
            repository_root
            / "demo"
            / "experiments"
            / "exp23_heldout_evaluation.py"
        ),
        "requirements_lock_sha256": file_sha256(
            repository_root / "requirements.lock"
        ),
        "source_files": source_hashes,
        "repository": {
            "commit": repository["commit"],
            "dirty": repository["dirty"],
            "status_sha256": repository["status_sha256"],
            "dirty_patch_sha256": repository["dirty_patch_sha256"],
            "dirty_patch_bytes": repository["dirty_patch_bytes"],
        },
        "candidate_command_contract": {
            "module": "demo.experiments.exp23_heldout_evaluation",
            "required_candidate_runner": (
                "demo.experiments.run_candidate"
            ),
            "only_supported_exp23_option": "--dataset-root",
            "seed_or_method_filter_available": False,
            "resume_available": False,
        },
        "seed_or_method_filter": None,
        "resume": False,
        "pre_read_audit": {
            "test_dataset_files_opened": 0,
            "test_metric_rows_emitted": 0,
            "candidate_suite_invocations_started": 0,
            "selected_config_validation": "pass",
            "git_diff_check": "pass",
        },
    }
    authorization["authorization_content_sha256"] = sha256_bytes(
        _canonical_json_bytes(authorization)
    )
    return authorization


def authorize(
    output: Path | str = DEFAULT_X0_RELEASE,
) -> Path:
    destination = Path(output).resolve()
    if destination != DEFAULT_X0_RELEASE.resolve():
        raise ValueError("X0 authorization target must be the canonical path")
    if destination.exists():
        raise FileExistsError("refusing to replace an existing X0 authorization")
    authorization = build_authorization()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        stream.write(canonical_json_bytes(authorization))
    return destination


def main(arguments: Sequence[str] | None = None) -> int:
    effective = list(sys.argv[1:] if arguments is None else arguments)
    if effective:
        raise ValueError("authorize_x0 accepts no command-line options")
    destination = authorize()
    print(
        json.dumps(
            {
                "x0_authorization": str(destination),
                "sha256": file_sha256(destination),
                "status": "authorized",
                "test_dataset_files_opened": 0,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["authorize", "build_authorization"]
