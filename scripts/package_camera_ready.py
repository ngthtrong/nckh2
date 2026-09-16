"""Create the minimal EasyChair source ZIP and matching PDF copy."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
DEFAULT_OUTPUT = PAPER / "submission"
FIXED_FILES = ("main.tex", "references.bib", "main.bbl", "llncs.cls", "splncs04.bst")
FORBIDDEN_SUFFIXES = {".aux", ".log", ".out", ".blg", ".synctex.gz"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def referenced_figures(main_text: str) -> list[Path]:
    names = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", main_text)
    figures: list[Path] = []
    for name in names:
        candidate = PAPER / "figures" / name
        if not candidate.suffix:
            candidate = candidate.with_suffix(".pdf")
        assert candidate.is_file(), f"missing referenced figure: {candidate}"
        figures.append(candidate)
    assert {path.name for path in figures} == {
        "pipeline_v2.pdf",
        "rq1_stress_delta_ari.pdf",
        "rq3_dispatch_conditions.pdf",
    }, figures
    return figures


def create_package(output_dir: Path) -> tuple[Path, Path]:
    main_path = PAPER / "main.tex"
    assert main_path.name == "main.tex"
    assert not re.search(r"[\s\\/><,;'\"|]", main_path.name)
    main_text = main_path.read_text(encoding="utf-8")
    figures = referenced_figures(main_text)
    for name in FIXED_FILES:
        assert (PAPER / name).is_file(), f"missing submission source: paper/{name}"
    final_pdf = PAPER / "main.pdf"
    assert final_pdf.read_bytes().startswith(b"%PDF-"), "paper/main.pdf is missing or invalid"

    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / "paper-6444-camera-ready-source.zip"
    pdf_path = output_dir / "paper-6444-camera-ready.pdf"
    with tempfile.TemporaryDirectory(prefix="paper-6444-camera-ready-") as temporary:
        stage = Path(temporary)
        for name in FIXED_FILES:
            shutil.copy2(PAPER / name, stage / name)
        (stage / "figures").mkdir()
        for figure in figures:
            shutil.copy2(figure, stage / "figures" / figure.name)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    assert path.suffix.lower() not in FORBIDDEN_SUFFIXES
                    archive.write(path, path.relative_to(stage).as_posix())
    shutil.copy2(final_pdf, pdf_path)

    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        assert "main.tex" in names and not any(name.startswith("paper/") for name in names)
        assert len(names) == len(FIXED_FILES) + len(figures)
        assert not any(name.startswith("src/") or name.startswith("docs/") for name in names)
    return zip_path, pdf_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    zip_path, pdf_path = create_package(args.output_dir)
    for path in (zip_path, pdf_path):
        print(f"WROTE {path} sha256={digest(path)}")


if __name__ == "__main__":
    main()
