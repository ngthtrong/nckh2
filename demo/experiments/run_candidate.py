"""Run one candidate command in a read-only source sandbox."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

try:
    from .artifacts import (
        DEFAULT_CONFIG_PATH,
        DEFAULT_DATASET_PATH,
        DEFAULT_PROTOCOL_DIR,
        DEFAULT_RUNS_ROOT,
        REPOSITORY_ROOT,
        ArtifactError,
        ArtifactRun,
        generate_run_id,
    )
except ImportError:  # Direct script use.
    from artifacts import (  # type: ignore[no-redef]
        DEFAULT_CONFIG_PATH,
        DEFAULT_DATASET_PATH,
        DEFAULT_PROTOCOL_DIR,
        DEFAULT_RUNS_ROOT,
        REPOSITORY_ROOT,
        ArtifactError,
        ArtifactRun,
        generate_run_id,
    )


def _parse_args(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", help="optional lowercase-safe run-id suffix")
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    parser.add_argument("--repository-root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--protocol-dir", type=Path, default=DEFAULT_PROTOCOL_DIR)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument(
        "--dataset",
        action="append",
        type=Path,
        dest="datasets",
        help="dataset input to snapshot; repeat for multiple inputs",
    )
    parser.add_argument(
        "--working-directory",
        type=Path,
        help="repository-contained command cwd (default: repository root)",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="command after --; it is executed directly, never through a shell",
    )
    args = parser.parse_args(arguments)
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("a command is required after --")
    return args


def _bubblewrap_command(run: ArtifactRun, command: Sequence[str]) -> list[str]:
    bubblewrap = shutil.which("bwrap")
    if bubblewrap is None:
        raise ArtifactError(
            "Bubblewrap is required: candidate execution refuses an unsandboxed "
            "fallback that could overwrite source results"
        )
    wrapped = [
        bubblewrap,
        "--die-with-parent",
        "--new-session",
        "--ro-bind",
        "/",
        "/",
        "--dev",
        "/dev",
        "--proc",
        "/proc",
    ]
    for directory in run.writable_directories:
        wrapped.extend(("--bind", str(directory), str(directory)))
    wrapped.extend(("--chdir", str(run.working_directory), "--"))
    wrapped.extend(command)
    return wrapped


def _candidate_environment(run: ArtifactRun) -> dict[str, str]:
    environment = os.environ.copy()
    work = run.path / "work"
    environment.update(
        {
            "DEMO_RUN_ID": run.run_id,
            "DEMO_ARTIFACT_DIR": str(run.path),
            "DEMO_TABLES_DIR": str(run.path / "tables"),
            "DEMO_FIGURES_DIR": str(run.path / "figures"),
            "DEMO_WORK_DIR": str(work),
            "TMPDIR": str(work),
            "XDG_CACHE_HOME": str(work / "cache"),
            "MPLCONFIGDIR": str(work / "matplotlib"),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    return environment


def main(arguments: Sequence[str] | None = None) -> int:
    args = _parse_args(arguments)
    if shutil.which("bwrap") is None:
        print(
            "candidate run refused: Bubblewrap (bwrap) is required for "
            "read-only source isolation",
            file=sys.stderr,
        )
        return 125

    datasets = args.datasets or [DEFAULT_DATASET_PATH]
    try:
        run_id = generate_run_id(
            repository_root=args.repository_root,
            protocol_dir=args.protocol_dir,
            label=args.label,
        )
        run = ArtifactRun.create(
            run_id=run_id,
            command=args.command,
            runs_root=args.runs_root,
            repository_root=args.repository_root,
            protocol_dir=args.protocol_dir,
            config_path=args.config,
            dataset_paths=datasets,
            working_directory=args.working_directory,
        )
    except ArtifactError as exc:
        print(f"candidate run refused: {exc}", file=sys.stderr)
        return 125

    stdout_path = run.path / "logs" / "stdout.log"
    stderr_path = run.path / "logs" / "stderr.log"
    exit_code = 125
    launch_error: str | None = None
    try:
        wrapped = _bubblewrap_command(run, args.command)
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            completed = subprocess.run(
                wrapped,
                cwd=run.repository_root,
                env=_candidate_environment(run),
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                check=False,
            )
        exit_code = completed.returncode
    except (ArtifactError, OSError) as exc:
        launch_error = f"{type(exc).__name__}: {exc}"
        if not stderr_path.exists():
            with stderr_path.open("x", encoding="utf-8") as stream:
                stream.write(launch_error + "\n")

    try:
        manifest_path = run.finalize(exit_code=exit_code, error=launch_error)
    except ArtifactError as exc:
        print(f"candidate manifest failed: {exc}", file=sys.stderr)
        return 125

    print(f"candidate run: {run.path}")
    print(f"manifest: {manifest_path}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

