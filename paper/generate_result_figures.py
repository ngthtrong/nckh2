#!/usr/bin/env python3
"""Build publication-ready PDF figures from the checked-in result CSVs.

The script deliberately uses only the Python standard library.  It reads the
CSV rows that supply the manuscript headline values, emits small PGFPlots
documents, and compiles them with XeLaTeX.  Re-running it is deterministic for
the same CSV inputs and does not modify the source notebooks or raw figures.
"""

from __future__ import annotations

import csv
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "demo" / "results"
OUT = ROOT / "paper" / "figures"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def tex_document(body: str) -> str:
    return r"""\documentclass[border=5pt]{standalone}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usepackage{amsmath}
\begin{document}
""" + body + r"""
\end{document}
"""


def compile_figure(name: str, body: str) -> None:
    with tempfile.TemporaryDirectory(prefix="flood-rescue-figures-") as tmp:
        tmpdir = Path(tmp)
        source = tmpdir / f"{name}.tex"
        source.write_text(tex_document(body), encoding="utf-8")
        result = subprocess.run(
            [
                "xelatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-output-directory",
                str(tmpdir),
                str(source),
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if result.returncode:
            raise RuntimeError(f"XeLaTeX failed for {name}:\n{result.stdout}")
        OUT.mkdir(parents=True, exist_ok=True)
        shutil.copy2(tmpdir / f"{name}.pdf", OUT / f"{name}.pdf")


def pgf_string(value: str) -> str:
    return value.replace("_", r"\_").replace("&", r"\&")


def rq1() -> None:
    data = rows(RESULTS / "cij_baseline_benchmark_results" / "benchmark_summary.csv")
    order = [
        "additive_cij_louvain",
        "product_cij_leiden",
        "convex_cij_louvain",
        "product_cij_louvain",
        "additive_cij_louvain_matched_density",
        "coordinate_kmeans",
        "spatial_agglomerative",
        "hdbscan_all",
        "geo_time_dbscan",
        "dbscan_all",
    ]
    labels = {
        "additive_cij_louvain": "Additive Louvain",
        "product_cij_leiden": "Product Leiden",
        "convex_cij_louvain": "Convex Louvain",
        "product_cij_louvain": "Product Louvain",
        "additive_cij_louvain_matched_density": "Matched-density Additive",
        "coordinate_kmeans": "Coordinate K-means",
        "spatial_agglomerative": "Spatial agglomerative",
        "hdbscan_all": "HDBSCAN",
        "geo_time_dbscan": "Geo-time DBSCAN",
        "dbscan_all": "DBSCAN, all features",
    }
    lookup = {row["method"]: row for row in data}
    coords = " ".join(
        f"({lookup[key]['ari_mean']},{key})" for key in order
    )
    ylabels = ",".join(pgf_string(labels[key]) for key in order)
    body = rf"""\begin{{tikzpicture}}
\begin{{axis}}[
  width=13.2cm,
  height=8.2cm,
  xbar,
  bar width=7pt,
  xmin=0.45, xmax=0.96,
  xlabel={{Adjusted Rand index (mean over 40 test runs)}},
  symbolic y coords={{{','.join(order)}}},
  ytick=data,
  yticklabels={{{ylabels}}},
  tick label style={{font=\scriptsize}},
  label style={{font=\small}},
  title={{RQ1: held-out clustering benchmark}},
  title style={{font=\small\bfseries}},
  grid=major,
  grid style={{dotted,gray!45}},
  enlarge y limits=0.04,
]
\addplot+[draw=black!55,fill=blue!55] coordinates {{{coords}}};
\end{{axis}}
\end{{tikzpicture}}
"""
    compile_figure("rq1_benchmark", body)


def rq2() -> None:
    data = rows(RESULTS / "rq2_results" / "rq2_summary.csv")
    lookup = {
        row["method"]: row["mean"]
        for row in data
        if row["section"] == "alignment" and row["scenario"] == "all_test" and row["metric"] == "ndcg_at_5"
    }
    order = [
        "random",
        "population_only",
        "duplicate_aware_robust",
        "legacy_raw",
        "simple_linear",
        "urgency_only",
    ]
    labels = {
        "random": "Random",
        "population_only": "Population only",
        "duplicate_aware_robust": "Revised duplicate-aware",
        "legacy_raw": "Legacy",
        "simple_linear": "Simple linear",
        "urgency_only": "Urgency only",
    }
    coords = " ".join(f"({lookup[key]},{key})" for key in order)
    ylabels = ",".join(pgf_string(labels[key]) for key in order)
    body = rf"""\begin{{tikzpicture}}
\begin{{axis}}[
  width=13.2cm,
  height=7.4cm,
  xbar,
  bar width=9pt,
  xmin=0.58, xmax=0.72,
  xlabel={{NDCG@5 (higher is better)}},
  symbolic y coords={{{','.join(order)}}},
  ytick=data,
  yticklabels={{{ylabels}}},
  tick label style={{font=\scriptsize}},
  label style={{font=\small}},
  title={{RQ2: priority alignment over 40 test runs}},
  title style={{font=\small\bfseries}},
  grid=major,
  grid style={{dotted,gray!45}},
  enlarge y limits=0.12,
]
\addplot+[draw=black!55,fill=teal!60] coordinates {{{coords}}};
\end{{axis}}
\end{{tikzpicture}}
"""
    compile_figure("rq2_priority", body)


def rq3() -> None:
    data = rows(RESULTS / "rq3_results" / "rq3_paired_comparisons.csv")
    wanted = [
        ("revised_priority", "legacy_priority", "latent_harm", "Legacy"),
        ("revised_priority", "nearest_first", "latent_harm", "Nearest-first"),
        ("product_cij", "additive_cij_matched_density", "latent_harm", "Matched-density Additive"),
    ]
    values: dict[str, str] = {}
    for row in data:
        if row["dimension"] == "policy" and row["candidate"] == "revised_priority" and row["fixed"] == '{"partition": "product_cij"}':
            for candidate, comparator, metric, label in wanted:
                if row["comparator"] == comparator and row["metric"] == metric:
                    values[label] = row["mean"]
        if row["dimension"] == "partition" and row["candidate"] == "product_cij" and row["fixed"] == '{"policy": "revised_priority"}':
            if row["comparator"] == "additive_cij_matched_density" and row["metric"] == "latent_harm":
                values["Matched-density Additive"] = row["mean"]
    order = ["Legacy", "Nearest-first", "Matched-density Additive"]
    keys = {"Legacy": "legacy", "Nearest-first": "nearest", "Matched-density Additive": "matched"}
    coords = " ".join(f"({values[label]},{keys[label]})" for label in order)
    body = rf"""\begin{{tikzpicture}}
\begin{{axis}}[
  width=13.2cm,
  height=6.7cm,
  xbar,
  bar width=10pt,
  xmin=-80, xmax=8,
  xlabel={{Oriented paired effect on latent harm (positive is better)}},
  symbolic y coords={{legacy,nearest,matched}},
  ytick=data,
  yticklabels={{Legacy,Nearest-first,Matched-density Additive}},
  tick label style={{font=\scriptsize}},
  label style={{font=\small}},
  title={{RQ3: predicted-cluster dispatch effects}},
  title style={{font=\small\bfseries}},
  grid=major,
  grid style={{dotted,gray!45}},
  enlarge y limits=0.22,
]
\addplot+[draw=black!55,fill=orange!70] coordinates {{{coords}}};
\end{{axis}}
\end{{tikzpicture}}
"""
    compile_figure("rq3_dispatch", body)


if __name__ == "__main__":
    rq1()
    rq2()
    rq3()
