"""Render the camera-ready RQ1 paired-delta ARI heatmap.

The default input is the independently audited first RQ1 stress run.  The
replication run is deliberately not pooled with it.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = (
    ROOT / "src/results/rq1_results/aggregate/rq1_stress_paired_effects.csv"
)
DEFAULT_OUTPUT = ROOT / "paper/figures/rq1_stress_delta_ari.pdf"

SCENARIOS = (
    ("gps_noise_100m", "GPS 100 m"),
    ("gps_noise_300m", "GPS 300 m"),
    ("time_noise_15min", "Time 15 min"),
    ("time_noise_60min", "Time 60 min"),
    ("exact_transport_copy_2x", "Copies 2x"),
    ("exact_transport_copy_5x", "Copies 5x"),
)
METHODS = (
    ("product_cij_louvain", "Product\nLouvain"),
    ("additive_cij_louvain", "Additive\nLouvain"),
    ("additive_cij_louvain_matched_density", "MD\nAdditive"),
    ("product_cij_leiden", "Product\nLeiden"),
    ("geo_time_dbscan", "Geo-time\nDBSCAN"),
)


def load_matrix(path: Path) -> list[list[float]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected = [row for row in rows if row["metric"] == "ari_original"]
    index: dict[tuple[str, str], float] = {}
    for row in selected:
        key = (row["scenario"], row["method"])
        assert key not in index, f"duplicate heatmap cell: {key}"
        assert int(row["paired_runs"]) == 40, key
        assert int(row["bootstrap_resamples"]) == 5000, key
        value = float(row["mean_stress_minus_baseline"])
        assert math.isfinite(value), key
        index[key] = value

    expected = {(scenario, method) for scenario, _ in SCENARIOS for method, _ in METHODS}
    assert set(index) == expected, (
        f"expected exactly 30 ARI cells; missing={sorted(expected - set(index))}, "
        f"unexpected={sorted(set(index) - expected)}"
    )
    return [[index[(scenario, method)] for method, _ in METHODS] for scenario, _ in SCENARIOS]


def render(matrix: list[list[float]], output: Path) -> None:
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import TwoSlopeNorm

    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            # The figure is scaled to about 62% in the LNCS text block.  These
            # source sizes keep every rendered label at or above 7 pt.
            "font.size": 12,
            "axes.labelsize": 12,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "pdf.fonttype": 42,
        }
    )
    fig, ax = plt.subplots(figsize=(7.0, 2.4), constrained_layout=True)
    norm = TwoSlopeNorm(vmin=-0.65, vcenter=0.0, vmax=0.04)
    image = ax.imshow(matrix, cmap="PuOr", norm=norm, aspect="auto")
    ax.set_xticks(range(len(METHODS)), labels=[label for _, label in METHODS])
    ax.set_yticks(range(len(SCENARIOS)), labels=[label for _, label in SCENARIOS])
    ax.tick_params(axis="both", length=0)

    for row_index, row in enumerate(matrix):
        for column_index, value in enumerate(row):
            foreground = "white" if value < -0.20 else "black"
            ax.text(
                column_index,
                row_index,
                f"{value:+.4f}",
                ha="center",
                va="center",
                color=foreground,
                fontsize=12,
                fontweight="semibold",
            )

    colorbar = fig.colorbar(image, ax=ax, fraction=0.030, pad=0.02)
    colorbar.set_label(r"Mean paired $\Delta$ARI", fontsize=12)
    colorbar.ax.tick_params(labelsize=12)
    for spine in ax.spines.values():
        spine.set_visible(False)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        output,
        format="pdf",
        bbox_inches="tight",
        metadata={"Creator": "plot_rq1_stress_heatmap.py", "CreationDate": None},
    )
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate and print the 30 source cells without writing a figure",
    )
    args = parser.parse_args()
    matrix = load_matrix(args.input)
    print(f"PASS 30 paired ARI cells from {args.input}")
    for (scenario, _), row in zip(SCENARIOS, matrix):
        print(scenario, " ".join(f"{value:+.4f}" for value in row))
    if not args.check:
        render(matrix, args.output)
        print(f"WROTE {args.output}")


if __name__ == "__main__":
    main()
