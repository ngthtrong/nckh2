from __future__ import annotations

from pathlib import Path

from demo.verify_figures import file_sha256, verify_figures


def _write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def test_zero_figure_revision_passes_without_paper_directory(
    tmp_path: Path,
) -> None:
    main = tmp_path / "paper" / "main.tex"
    _write(main, b"Revised manuscript without figures.\n")

    report = verify_figures(
        main_tex=main,
        paper_figure_dir=tmp_path / "paper" / "figures",
        generated_dir=tmp_path / "demo" / "results" / "figures",
    )

    assert report["status"] == "pass"
    assert report["included_figure_count"] == 0


def test_matching_sha256_figure_passes(tmp_path: Path) -> None:
    main = tmp_path / "paper" / "main.tex"
    _write(main, b"\\includegraphics{figures/result.png}\n")
    paper = tmp_path / "paper" / "figures" / "result.png"
    generated = tmp_path / "demo" / "results" / "figures" / "result.png"
    _write(paper, b"locked pixels")
    _write(generated, b"locked pixels")

    report = verify_figures(
        main_tex=main,
        paper_figure_dir=paper.parent,
        generated_dir=generated.parent,
    )

    assert report["status"] == "pass"
    assert report["verified_figures"] == [
        {"path": "figures/result.png", "sha256": file_sha256(paper)}
    ]


def test_stale_and_orphan_figures_fail(tmp_path: Path) -> None:
    main = tmp_path / "paper" / "main.tex"
    _write(main, b"\\includegraphics{figures/result.png}\n")
    paper_dir = tmp_path / "paper" / "figures"
    generated_dir = tmp_path / "demo" / "results" / "figures"
    _write(paper_dir / "result.png", b"old")
    _write(generated_dir / "result.png", b"new")
    _write(paper_dir / "orphan.png", b"unused")

    report = verify_figures(
        main_tex=main,
        paper_figure_dir=paper_dir,
        generated_dir=generated_dir,
    )

    assert report["status"] == "fail"
    assert "stale manuscript figure: result.png" in report["validation_errors"]
    assert "orphan manuscript figure: orphan.png" in report["validation_errors"]


def test_path_escape_fails(tmp_path: Path) -> None:
    main = tmp_path / "paper" / "main.tex"
    _write(main, b"\\includegraphics{../outside.png}\n")

    report = verify_figures(
        main_tex=main,
        paper_figure_dir=tmp_path / "paper" / "figures",
        generated_dir=tmp_path / "demo" / "results" / "figures",
    )

    assert report["status"] == "fail"
    assert report["validation_errors"] == [
        "unsupported figure path: ../outside.png"
    ]
