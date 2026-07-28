"""Gate-2-only release of the untouched evaluation seeds.

Tuning code must import :mod:`protocol`, not this module.  This module rejects
access unless a separate lock record states the exact current protocol hash.
The lock record is intentionally not created by B1: it is a Gate-2 artifact.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from .protocol import (
        DEFAULT_PROTOCOL_DIR,
        METRIC_CONTRACT_NAME,
        SEED_MANIFEST_NAME,
        ProtocolError,
        protocol_bundle_sha256,
    )
except ImportError:  # Direct script/module use with demo/experiments on sys.path.
    from protocol import (  # type: ignore[no-redef]
        DEFAULT_PROTOCOL_DIR,
        METRIC_CONTRACT_NAME,
        SEED_MANIFEST_NAME,
        ProtocolError,
        protocol_bundle_sha256,
    )


def load_locked_test_seeds(
    gate2_lock_path: Path | str,
    protocol_dir: Path | str = DEFAULT_PROTOCOL_DIR,
) -> tuple[int, ...]:
    """Release test seeds only for an exact, explicitly locked protocol."""

    lock_path = Path(gate2_lock_path)
    try:
        lock: Any = json.loads(lock_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProtocolError("Gate-2 lock is required before test-seed release") from exc
    except json.JSONDecodeError as exc:
        raise ProtocolError("Gate-2 lock is not valid JSON") from exc
    if not isinstance(lock, dict):
        raise ProtocolError("Gate-2 lock must contain a JSON object")

    directory = Path(protocol_dir)
    current_hash = protocol_bundle_sha256(
        directory / SEED_MANIFEST_NAME,
        directory / METRIC_CONTRACT_NAME,
    )
    if (
        lock.get("schema_version") != 1
        or lock.get("gate") != "Gate 2"
        or lock.get("status") != "locked"
        or lock.get("protocol_sha256") != current_hash
    ):
        raise ProtocolError("Gate-2 lock does not match the current protocol")

    try:
        manifest: Any = json.loads(
            (directory / SEED_MANIFEST_NAME).read_text(encoding="utf-8")
        )
        values = manifest["splits"]["test"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ProtocolError("test split is absent from the locked seed manifest") from exc
    if (
        not isinstance(values, list)
        or len(values) != 40
        or any(isinstance(seed, bool) or not isinstance(seed, int) for seed in values)
        or len(values) != len(set(values))
    ):
        raise ProtocolError("locked test split is malformed")
    return tuple(values)


__all__ = ["load_locked_test_seeds"]
