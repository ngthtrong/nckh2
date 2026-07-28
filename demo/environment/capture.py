"""Capture a JSON-serializable execution-environment inventory."""
from __future__ import annotations

import argparse
import contextlib
import importlib.metadata
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import sysconfig
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


THREAD_ENVIRONMENT_VARIABLES = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "BLIS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


def _read_first_matching_line(path: Path, prefix: str) -> str | None:
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith(prefix):
                _, _, value = line.partition(":")
                return value.strip()
    except OSError:
        return None
    return None


def _command_version(command: str, arguments: Sequence[str]) -> dict[str, Any]:
    executable = shutil.which(command)
    if executable is None:
        return {"available": False, "executable": None, "version": None}
    try:
        completed = subprocess.run(
            [executable, *arguments],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
        )
        first_line = completed.stdout.splitlines()[0] if completed.stdout else ""
        return {
            "available": completed.returncode == 0,
            "executable": executable,
            "version": first_line,
            "exit_code": completed.returncode,
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "available": False,
            "executable": executable,
            "version": None,
            "error": type(exc).__name__,
        }


def _installed_distributions() -> list[dict[str, str]]:
    packages: list[dict[str, str]] = []
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata.get("Name")
        if name:
            packages.append({"name": name, "version": distribution.version})
    return sorted(packages, key=lambda item: item["name"].casefold())


def _numpy_and_blas() -> dict[str, Any]:
    try:
        import numpy as np
    except ImportError:
        return {"numpy_available": False, "numpy_version": None, "configuration": None}

    output = io.StringIO()
    with warnings.catch_warnings(), contextlib.redirect_stdout(output):
        warnings.simplefilter("ignore")
        np.show_config()
    result: dict[str, Any] = {
        "numpy_available": True,
        "numpy_version": np.__version__,
        "configuration": output.getvalue(),
    }
    try:
        from threadpoolctl import threadpool_info
    except ImportError:
        result["threadpools"] = []
    else:
        result["threadpools"] = threadpool_info()
    return result


def _memory_bytes() -> int | None:
    value = _read_first_matching_line(Path("/proc/meminfo"), "MemTotal:")
    if value is None:
        return None
    parts = value.split()
    if len(parts) != 2 or parts[1].lower() != "kb":
        return None
    try:
        return int(parts[0]) * 1024
    except ValueError:
        return None


def capture_environment() -> dict[str, Any]:
    """Return environment, hardware, BLAS, thread, and tool provenance."""

    return {
        "schema_version": 1,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "version_detail": sys.version,
            "executable": sys.executable,
            "prefix": sys.prefix,
            "abi_flags": getattr(sys, "abiflags", ""),
            "platform_tag": sysconfig.get_platform(),
        },
        "operating_system": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "platform": platform.platform(),
        },
        "hardware": {
            "machine": platform.machine(),
            "processor": platform.processor() or None,
            "cpu_model": _read_first_matching_line(
                Path("/proc/cpuinfo"), "model name"
            ),
            "logical_cpu_count": os.cpu_count(),
            "memory_bytes": _memory_bytes(),
        },
        "blas": _numpy_and_blas(),
        "threads": {
            "environment": {
                name: os.environ.get(name)
                for name in THREAD_ENVIRONMENT_VARIABLES
            },
            "declared_core_limit": None,
        },
        "packages": _installed_distributions(),
        "tools": {
            "git": _command_version("git", ("--version",)),
            "bubblewrap": _command_version("bwrap", ("--version",)),
            "xelatex": _command_version("xelatex", ("--version",)),
            "bibtex": _command_version("bibtex", ("--version",)),
        },
    }


def write_environment_capture(path: Path | str) -> Path:
    """Write one capture with exclusive creation; never replace a prior record."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        capture_environment(), indent=2, sort_keys=True, ensure_ascii=False
    )
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(payload)
        stream.write("\n")
    return destination


def _parse_args(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="write JSON exclusively to this path; stdout is used when omitted",
    )
    return parser.parse_args(arguments)


def main(arguments: Sequence[str] | None = None) -> int:
    args = _parse_args(arguments)
    if args.output is not None:
        try:
            write_environment_capture(args.output)
        except FileExistsError:
            print(f"refusing to overwrite environment capture: {args.output}", file=sys.stderr)
            return 2
        return 0
    json.dump(
        capture_environment(),
        sys.stdout,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
