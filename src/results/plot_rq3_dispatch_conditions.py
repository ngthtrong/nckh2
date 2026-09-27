"""Render descriptive RQ3 dispatch means for the Product partition.

The figure reads the locked 40-seed test artifact. It does not recompute,
pool, or infer additional experimental results.
"""

from __future__ import annotations

import argparse
import csv
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "src/results/rq3_results/rq3_dispatch_test.csv"
DEFAULT_OUTPUT = ROOT / "paper/figures/rq3_dispatch_conditions.pdf"

SCENARIOS = (
    ("lean_hue", "Lean Hue"),
    ("nominal_dual_depot", "Nominal dual depot"),
    ("regional_surge", "Regional surge"),
)
POLICIES = (
    ("revised_priority", "Revised", "#0072B2", "o"),
    ("legacy_priority", "Legacy", "#D55E00", "s"),
    ("nearest_first", "Nearest-first", "#009E73", "^"),
)
METRICS = ("latent_harm", "deadline_miss_rate")


def load_means(path: Path) -> dict[tuple[str, str, str], float]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected = [
        row
        for row in rows
        if row["stage"] == "test"
        and row["partition"] == "product_cij"
        and row["resource_scenario"] in {item[0] for item in SCENARIOS}
        and row["policy"] in {item[0] for item in POLICIES}
    ]
    index: dict[tuple[str, str, str], float] = {}
    for scenario, _ in SCENARIOS:
        for policy, *_ in POLICIES:
            group = [
                row
                for row in selected
                if row["resource_scenario"] == scenario and row["policy"] == policy
            ]
            assert len(group) == 40, (scenario, policy, len(group))
            assert len({row["seed"] for row in group}) == 40, (scenario, policy)
            for metric in METRICS:
                index[(scenario, policy, metric)] = statistics.mean(
                    float(row[metric]) for row in group
                )
    assert len(index) == 18, len(index)
    return index


def render(means: dict[tuple[str, str, str], float], output: Path) -> None:
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "pdf.fonttype": 42,
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.20), constrained_layout=True)
    offsets = (-0.20, 0.0, 0.20)
    specifications = (
        ("latent_harm", "Simulated harm", 1.0, lambda value: f"{value:.2f}"),
        ("deadline_miss_rate", "Deadline-miss rate (%)", 100.0, lambda value: f"{value:.1f}"),
    )
    scenario_positions = range(len(SCENARIOS))
    for ax, (metric, title, scale, formatter) in zip(axes, specifications):
        # Separate labels vertically as well as horizontally when policy means
        # are close (especially the lean-condition harm and miss-rate points).
        annotation_offsets = ((-3, 7, "right"), (3, 7, "left"), (0, -14, "center"))
        for offset, (policy, label, color, marker), (dx, dy, alignment) in zip(
            offsets, POLICIES, annotation_offsets
        ):
            values = [means[(scenario, policy, metric)] * scale for scenario, _ in SCENARIOS]
            positions = [position + offset for position in scenario_positions]
            ax.scatter(
                positions,
                values,
                label=label,
                color=color,
                edgecolor="black",
                linewidth=0.4,
                marker=marker,
                s=34,
                zorder=3,
            )
            for position, value in zip(positions, values):
                ax.annotate(
                    formatter(value),
                    (position, value),
                    xytext=(dx, dy),
                    textcoords="offset points",
                    ha=alignment,
                    fontsize=7,
                )
        ax.set_title(title)
        ax.set_xticks(list(scenario_positions), [label for _, label in SCENARIOS])
        ax.set_xlim(-0.45, len(SCENARIOS) - 0.55)
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", color="0.85", linewidth=0.6, zorder=0)
        ax.spines[["top", "right"]].set_visible(False)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside upper center", ncol=3, frameon=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        output,
        format="pdf",
        bbox_inches="tight",
        metadata={"Creator": "plot_rq3_dispatch_conditions.py", "CreationDate": None},
    )
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate and print the 18 source means without writing a figure",
    )
    args = parser.parse_args()
    means = load_means(args.input)
    print(f"PASS 18 RQ3 means from {args.input}")
    for scenario, _ in SCENARIOS:
        for metric in METRICS:
            values = [means[(scenario, policy, metric)] for policy, *_ in POLICIES]
            print(scenario, metric, " ".join(f"{value:.8f}" for value in values))
    if not args.check:
        render(means, args.output)
        print(f"WROTE {args.output}")


if __name__ == "__main__":
    main()
