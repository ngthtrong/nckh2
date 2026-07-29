#!/usr/bin/env python3
r"""Verify the revised manuscript's figure set and provenance.

The current revision intentionally contains no figures.  That is a valid,
auditable state: ``paper/main.tex`` must contain no ``\includegraphics`` call
and ``paper/figures`` must contain no orphan image.  If a later gate-approved
revision adds figures, each ``figures/<name>`` inclusion must have a
byte-identical SHA-256 counterpart in ``demo/results/figures``.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Sequence


DEMO_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = DEMO_DIR.parent
GENERATED_DIR = DEMO_DIR / "results" / "figures"
PAPER_FIGURE_DIR = REPOSITORY_ROOT / "paper" / "figures"
MAIN_TEX = REPOSITORY_ROOT / "paper" / "main.tex"

INCLUDE_RE = re.compile(
    r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}",
)
IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".pdf", ".svg"})


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def figures_used_by_paper(main_tex: Path = MAIN_TEX) -> list[str]:
    """Return unique figure arguments in manuscript order."""

    source = main_tex.read_text(encoding="utf-8")
    seen: set[str] = set()
    ordered: list[str] = []
    for raw_name in INCLUDE_RE.findall(source):
        name = raw_name.strip()
        if name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def verify_figures(
    *,
    main_tex: Path = MAIN_TEX,
    paper_figure_dir: Path = PAPER_FIGURE_DIR,
    generated_dir: Path = GENERATED_DIR,
) -> dict[str, object]:
    """Validate every inclusion and reject stale/orphan paper assets."""

    used = figures_used_by_paper(main_tex)
    failures: list[str] = []
    verified: list[dict[str, str]] = []

    for argument in used:
        relative = Path(argument)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or relative.parts[:1] != ("figures",)
            or len(relative.parts) != 2
        ):
            failures.append(f"unsupported figure path: {argument}")
            continue
        name = relative.name
        paper_path = paper_figure_dir / name
        generated_path = generated_dir / name
        if not paper_path.is_file():
            failures.append(f"missing manuscript figure: {argument}")
            continue
        if not generated_path.is_file():
            failures.append(f"missing generated provenance figure: {name}")
            continue
        paper_sha = file_sha256(paper_path)
        generated_sha = file_sha256(generated_path)
        if paper_sha != generated_sha:
            failures.append(f"stale manuscript figure: {name}")
            continue
        verified.append({"path": argument, "sha256": paper_sha})

    used_names = {
        Path(argument).name
        for argument in used
        if Path(argument).parts[:1] == ("figures",)
    }
    paper_assets = (
        sorted(
            path.name
            for path in paper_figure_dir.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )
        if paper_figure_dir.is_dir()
        else []
    )
    orphans = sorted(set(paper_assets) - used_names)
    failures.extend(f"orphan manuscript figure: {name}" for name in orphans)

    return {
        "status": "pass" if not failures else "fail",
        "included_figure_count": len(used),
        "verified_figures": verified,
        "orphan_figures": orphans,
        "validation_errors": failures,
    }


def main(arguments: Sequence[str] | None = None) -> int:
    del arguments
    report = verify_figures()
    if report["status"] == "pass":
        count = report["included_figure_count"]
        print(f"PASS: {count} manuscript figure(s), no stale or orphan assets.")
        return 0
    for error in report["validation_errors"]:
        print(f"FAIL: {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["figures_used_by_paper", "verify_figures"]
