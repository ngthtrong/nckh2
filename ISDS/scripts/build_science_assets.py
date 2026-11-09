#!/usr/bin/env python3
"""Reproducible slide visuals for ISDS paper 6444.

Read-only with respect to manuscript, benchmark data and exported results.
The only model execution is one held-out run replayed under its seven already
published fixed conditions, solely to draw the retained edges. Aggregate charts
are read directly from the exported CSV tables, never recomputed from a new run.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import math
from datetime import datetime
from pathlib import Path

import community as community_louvain
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
import networkx as nx
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.metrics import adjusted_rand_score

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ISDS/assets/science"
RESULTS = ROOT / "thucnghiem/results"
BLUE, TEAL, ORANGE, INK = "#0070C0", "#009988", "#D9822B", "#17212B"
GREY, LIGHT = "#657382", "#EAF2F8"
PALETTE = [BLUE, TEAL, ORANGE, "#A95C9D", "#7B9E36", "#7D6B56", "#3A7795", "#BC5A68"]
MANIFEST = {"schema": "isds-science-assets/1.0", "inputs": {}, "assets": {}, "numeric_values": {},
            "limitations": ["All study results are limited to the tested synthetic artifact suites.",
                            "A one-run graph replay is an explanatory reproduction, not an additional experiment.",
                            "GIF condition sequence is presentation order, not an observed event timeline."]}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def source(p):
    p = Path(p)
    MANIFEST["inputs"][str(p.relative_to(ROOT))] = sha(p)
    return p


def frame(fig):
    stream = io.BytesIO()
    fig.savefig(stream, dpi=160, facecolor="white")
    plt.close(fig)
    stream.seek(0)
    return Image.open(stream).convert("RGB")


def savefig(fig, name, caption, sources, kind="exported-result chart", values=None):
    image = frame(fig)
    p = OUT / (name + ".png")
    image.save(p, dpi=(300, 300))
    MANIFEST["assets"][p.name] = {"kind": kind, "dimensions_px": list(image.size),
                               "caption": caption, "source_files": sources, "sha256": sha(p)}
    if values is not None:
        MANIFEST["numeric_values"][name] = values


def style_axes(ax, xlabel=None, ylabel=None, xgrid=False):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#C4CFD8")
    ax.tick_params(colors=INK, labelsize=12)
    if xlabel:
        ax.set_xlabel(xlabel, labelpad=10, color=INK)
    if ylabel:
        ax.set_ylabel(ylabel, labelpad=10, color=INK)
    ax.set_axisbelow(True)
    if xgrid:
        ax.grid(axis="x", color="#E1E7EC", linewidth=.7)


def charts():
    f = source(RESULTS / "cij_baseline_benchmark_results/benchmark_summary.csv")
    data = pd.read_csv(f).set_index("method")
    names = ["additive_cij_louvain", "product_cij_leiden", "product_cij_louvain", "additive_cij_louvain_matched_density", "kmeans_coords", "geo_time_dbscan"]
    # Keep exact export identities; tolerate the established coordinate spelling.
    if "kmeans_coords" not in data.index:
        names = [x for x in names if x != "kmeans_coords"]
        coord = [x for x in data.index if "kmeans" in x]
        if coord:
            names.insert(-1, coord[0])
    labels = {"additive_cij_louvain": "Additive Louvain", "product_cij_leiden": "Product Leiden",
              "product_cij_louvain": "Product Louvain", "additive_cij_louvain_matched_density": "Matched-density Additive",
              "geo_time_dbscan": "Geo-time DBSCAN"}
    labels.update({x: "Coordinate K-means" for x in names if "kmeans" in x})
    fig, ax = plt.subplots(figsize=(10, 4.45))
    fig.subplots_adjust(left=.285, right=.91, top=.96, bottom=.18)
    for i, name in enumerate(names):
        r = data.loc[name]
        m, lo, hi = [float(r[c]) for c in ("ari_mean", "ari_ci95_low", "ari_ci95_high")]
        c = BLUE if name == "product_cij_louvain" else TEAL if name == "additive_cij_louvain" else GREY
        ax.errorbar(m, i, xerr=[[m-lo], [hi-m]], fmt="o", color=c, markersize=9, capsize=5, elinewidth=2)
        ax.text(1.035, i, f"{m:.4f}", va="center", fontsize=13, color=c, fontweight="bold")
    ax.set_yticks(range(len(names)), [labels[x] for x in names])
    ax.invert_yaxis(); ax.set_xlim(0, 1)
    style_axes(ax, "Adjusted Rand index (ARI)  ↑ higher is better", xgrid=True)
    savefig(fig, "rq1_ari_ci", "Selected RQ1 comparators; means and bootstrap 95% CIs across 40 held-out runs. The axis spans 0–1; selected comparators are not the complete benchmark.", [str(f.relative_to(ROOT))], values=data.loc[names, ["ari_mean", "ari_ci95_low", "ari_ci95_high"]].to_dict("index"))

    f = source(RESULTS / "rq1_results/aggregate/rq1_stress_paired_effects.csv")
    p = pd.read_csv(f); p = p[p.metric == "ari_original"]
    methods = ["product_cij_louvain", "additive_cij_louvain", "additive_cij_louvain_matched_density", "product_cij_leiden", "geo_time_dbscan"]
    conditions = ["gps_noise_100m", "gps_noise_300m", "time_noise_15min", "time_noise_60min", "exact_transport_copy_2x", "exact_transport_copy_5x"]
    values = np.array([[float(p[(p.method == m) & (p.scenario == s)].mean_stress_minus_baseline.iloc[0]) for s in conditions] for m in methods])
    fig, ax = plt.subplots(figsize=(10, 4.5)); fig.subplots_adjust(left=.25, right=.98, top=.96, bottom=.23)
    cmap = LinearSegmentedColormap.from_list("degradation", ["#F0C183", "#FFFDF8", "#2D83AC"])
    ax.imshow(values, cmap=cmap, vmin=-.65, vmax=.05, aspect="auto")
    ax.set_yticks(range(5), ["Product Louvain", "Additive Louvain", "MD Additive", "Product Leiden", "Geo-time DBSCAN"])
    ax.set_xticks(range(6), ["GPS\n100 m", "GPS\n300 m", "Time\n15 min", "Time\n60 min", "Copies\n2×", "Copies\n5×"])
    ax.tick_params(length=0, pad=8, labelsize=12)
    for i in range(5):
        for j in range(6): ax.text(j, i, f"{values[i,j]:+.3f}", ha="center", va="center", color=INK, fontsize=12, fontweight="bold")
    ax.set_xticks(np.arange(-.5, 6, 1), minor=True); ax.set_yticks(np.arange(-.5, 5, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=3); ax.tick_params(which="minor", bottom=False, left=False)
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.set_xlabel("Mean paired ΔARI (stress − control)", labelpad=12, color=INK)
    savefig(fig, "rq1_stress_heatmap", "Mean paired change in ARI from each method’s control across 40 held-out runs, using original incident-linked reports. Descriptive heatmap; no between-method test is implied.", [str(f.relative_to(ROOT))], values={m: dict(zip(conditions, row.tolist())) for m, row in zip(methods, values)})

    f = source(RESULTS / "rq2_results/rq2_summary.csv")
    d = pd.read_csv(f); a = d[(d.section == "alignment") & (d.metric == "ndcg_at_5")].set_index("method")
    methods = ["duplicate_aware_robust", "legacy_raw", "population_only", "urgency_only", "random"]
    methods = [m for m in methods if m in a.index]
    labels = {"duplicate_aware_robust": "Revised", "legacy_raw": "Legacy", "population_only": "Population only", "urgency_only": "Urgency only", "random": "Random ordering"}
    fig, ax = plt.subplots(figsize=(10, 4.45)); fig.subplots_adjust(left=.21, right=.91, top=.95, bottom=.19)
    for i, m in enumerate(methods):
        r = a.loc[m]; mean = float(r["mean"]); lo, hi = json.loads(r.paired_confidence_interval)
        c = BLUE if m == "duplicate_aware_robust" else TEAL if m == "random" else GREY
        ax.errorbar(mean, i, xerr=[[mean-lo], [hi-mean]], fmt="s" if m == "random" else "o", color=c, markersize=9, capsize=5, elinewidth=2)
        ax.text(1.025, i, f"{mean:.4f}", va="center", fontsize=13, fontweight="bold", color=c)
    ax.set_yticks(range(len(methods)), [labels[m] for m in methods]); ax.invert_yaxis(); ax.set_xlim(0, 1)
    style_axes(ax, "NDCG@5  ↑ higher is better", xgrid=True)
    savefig(fig, "rq2_ndcg_ci", "Benefit alignment under oracle incident grouping; means and bootstrap 95% CIs over 40 Candidate-4.1 held-out seeds. Point-estimate order is not a significance test.", [str(f.relative_to(ROOT))], values={m: {"mean": float(a.loc[m, "mean"]), "ci95": json.loads(a.loc[m, "paired_confidence_interval"])} for m in methods})

    r = d[(d.section == "robustness") & (d.metric == "priority_drift_abs_normalized")]
    print("robustness scenarios", sorted(r.scenario.unique()), flush=True)
    scenario_alias = {s: s for s in r.scenario.unique()}
    choose = []
    for token in ["exact_duplicate_2", "exact_duplicate_5", "exact_duplicate_10", "coordinated"]:
        matches = [s for s in scenario_alias if token in s]
        if not matches and token.startswith("exact_duplicate_"):
            n = token.split("_")[-1]; matches = [s for s in scenario_alias if ("exact" in s and (n+"x" in s or "_"+n == s[-len(n)-1:]))]
        if matches: choose.append(matches[0])
    if len(choose) != 4:
        raise RuntimeError(f"Identify four robustness scenarios manually from {sorted(r.scenario.unique())}")
    fig, ax = plt.subplots(figsize=(10, 4.45)); fig.subplots_adjust(left=.28, right=.98, top=.88, bottom=.18)
    y = np.arange(4)
    numeric = {}
    for offset, m, label, c, hatch in [(-.17, "duplicate_aware_robust", "Revised", BLUE, ""), (.17, "legacy_raw", "Legacy", ORANGE, "//")]:
        means = [float(r[(r.scenario == s) & (r.method == m)]["mean"].iloc[0]) for s in choose]
        numeric[m] = dict(zip(choose, means))
        ax.barh(y+offset, means, .29, color=c, alpha=.9, label=label, hatch=hatch)
        for yy, value in zip(y+offset, means):ax.text(value+.003, yy, f"{value:.4f}", va="center", fontsize=12, color=c, fontweight="bold")
    ax.set_yticks(y, ["Exact copies 2×", "Exact copies 5×", "Exact copies 10×", "Coordinated high-confidence"])
    ax.invert_yaxis(); ax.set_xlim(0, .2); ax.legend(ncol=2, loc="lower right", frameon=False)
    style_axes(ax, "Absolute normalized priority drift  ↓ lower is better", xgrid=True)
    savefig(fig, "rq2_priority_drift", "Controlled Candidate-4.1 perturbations; normalized absolute priority drift. Revised exact-copy invariance assumes fixed evidence grouping and score inputs. High-confidence campaign remains a failure case.", [str(f.relative_to(ROOT))], values=numeric)

    f = source(RESULTS / "rq3_results/rq3_dispatch_test.csv")
    d = pd.read_csv(f); d = d[d.partition == "product_cij"]
    scenarios = ["lean_hue", "nominal_dual_depot", "regional_surge"]
    print("rq3 conditions", sorted(d.resource_scenario.unique()), flush=True)
    if any(s not in d.resource_scenario.unique() for s in scenarios):
        scenarios = sorted(d.resource_scenario.unique())
    policies = [("revised_priority", "Revised", BLUE, "o"), ("legacy_priority", "Legacy", ORANGE, "s"), ("nearest_first", "Nearest-first", TEAL, "^")]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.6)); fig.subplots_adjust(left=.105, right=.98, top=.86, bottom=.24, wspace=.29)
    numeric = {}
    for ax, metric, ylabel, factor in [(axes[0], "latent_harm", "Mean simulated harm (model units)", 1), (axes[1], "deadline_miss_rate", "Deadline misses (%)", 100)]:
        for m, label, c, marker in policies:
            means = [float(d[(d.policy == m) & (d.resource_scenario == s)][metric].mean())*factor for s in scenarios]
            numeric[f"{metric}:{m}"] = dict(zip(scenarios, means))
            ax.plot(range(3), means, label=label, color=c, marker=marker, markersize=7, linewidth=2)
            # Revised and nearest-first labels explain the headline contrast;
            # legacy points stay drawn but its nearly overlapping numbers are
            # omitted rather than obscuring the data with a third text layer.
            if m != "legacy_priority":
                for i, value in enumerate(means):
                    offset = 13 if m == "revised_priority" else -23
                    ax.annotate(f"{value:.1f}", (i, value), xytext=(0, offset), textcoords="offset points", ha="center", fontsize=10, color=c)
        ax.set_xticks(range(3), ["Lean\nHue", "Nominal\ndual depot", "Regional\nsurge"])
        ax.set_xlim(-.18, 2.18); ax.set_ylim(0, 100 if factor == 100 else 1000)
        style_axes(ax, ylabel=ylabel)
        ax.grid(axis="y", color="#E1E7EC", linewidth=.7)
    handles, labels = axes[0].get_legend_handles_labels(); fig.legend(handles, labels, ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(.55, 1), fontsize=12)
    savefig(fig, "rq3_dispatch", "Product-partition means by resource condition; lower is better for harm and deadline misses. The three conditions are not additional independent samples; inferential analysis first averages conditions within seed.", [str(f.relative_to(ROOT))], values=numeric)


def load_replay_namespace():
    notebook = source(RESULTS / "RQ1_Reviewer_Stress_Colab.ipynb")
    protocol_path = source(RESULTS / "rq1_results/protocol.json")
    protocol = json.loads(protocol_path.read_text())
    n = json.loads(notebook.read_text())
    g = {"np": np, "nx": nx, "community_louvain": community_louvain, "math": math,
         "datetime": datetime, "hashlib": hashlib, "json": json, "Path": Path,
         "STRESS_RANDOM_SEED": protocol["stress_random_seed"], "SCENARIOS": protocol["scenarios"],
         "SELECTED": protocol["selected_configs"], "EARTH_RADIUS_M": 6371000.,
         "TAU_F": .25, "TAU_E": .35, "BETA": .5, "GAMMA": .5}
    allow = {"read_json", "load_input", "with_local_coordinates", "load_truth", "copy_x", "deterministic_rng", "transform_input",
             "pair_matrices", "threshold_knn", "louvain", "graph_for", "predict"}
    extracted = []
    for index in (6, 8):
        text = "".join(n["cells"][index]["source"])
        tree = ast.parse(text)
        nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in allow]
        extracted.extend(ast.unparse(node) for node in nodes)
        exec(compile(ast.Module(body=nodes, type_ignores=[]), f"{notebook.name}:cell{index}", "exec"), g)
    MANIFEST["replay"] = {"run_id": "run_041", "source_notebook": str(notebook.relative_to(ROOT)),
                          "cells": [6, 8], "function_names": sorted(allow),
                          "extracted_functions_sha256": hashlib.sha256("\n".join(extracted).encode()).hexdigest(),
                          "runtime_versions": {"numpy": np.__version__, "networkx": nx.__version__, "python_louvain": community_louvain.__version__},
                          "original_checkpoint_comparisons": []}
    return g


def graph_gif():
    g = load_replay_namespace()
    run_dir = ROOT / "thucnghiem/data/gold/run_041"
    source(run_dir / "algorithm_input.json"); source(run_dir / "ground_truth.json")
    base = g["load_input"](run_dir)
    scenes = [("baseline", "Control — no added perturbation"), ("gps_noise_100m", "GPS noise: σ = 100 m per axis"),
              ("gps_noise_300m", "GPS noise: σ = 300 m per axis"), ("time_noise_15min", "Timestamp noise: σ = 15 min"),
              ("time_noise_60min", "Timestamp noise: σ = 60 min"), ("exact_transport_copy_2x", "Exact transport copies: 2×"),
              ("exact_transport_copy_5x", "Exact transport copies: 5×")]
    # Initial geographic window from observable point density. Once the fixed
    # control partition exists, focus on its largest predicted community. No
    # truth label chooses the window or enters prediction.
    xy = np.column_stack([base["east"], base["north"]])/1000
    dist = ((xy[:, None, :] - xy[None, :, :])**2).sum(axis=2)
    center = xy[np.argmax(np.sum(dist < 16, axis=1))]
    radius = 4.7
    frames = []; info = []
    for scene, title in scenes:
        x, src, _ = g["transform_input"](base, scene)
        pairs = g["pair_matrices"](x)
        predictions = {}
        for method in ("product_cij_louvain", "additive_cij_louvain"):
            labels, weights, threshold = g["predict"](method, x, pairs)
            predictions[method] = (labels, weights, threshold)
        if scene == "baseline":
            labels = predictions["product_cij_louvain"][0]
            community_ids, counts = np.unique(labels, return_counts=True)
            chosen = community_ids[np.argmax(counts)]
            selected_xy = xy[labels == chosen]
            center = selected_xy.mean(axis=0)
            radius = max(1.25, min(2.3, np.max(np.abs(selected_xy-center)) + .9))
            MANIFEST["replay"]["geographic_window"] = {"selection":"largest predicted control community, without truth labels", "center_local_km":center.tolist(), "half_width_km":float(radius)}
        # Truth is joined only after both predictions have been fixed.
        truth = g["load_truth"](run_dir, base["event_id"])
        checkpoint_path = source(RESULTS / f"rq1_results/checkpoints/run_041__{scene}.json")
        checkpoint = json.loads(checkpoint_path.read_text())
        full_xy = np.column_stack([x["east"], x["north"]])/1000
        fig, axes = plt.subplots(1, 2, figsize=(10, 4.5)); fig.subplots_adjust(left=.07, right=.985, top=.78, bottom=.18, wspace=.14)
        fig.text(.5, .94, title, ha="center", fontsize=18, fontweight="bold", fontfamily=["K2D", "Readex Pro", "DejaVu Sans"], color=INK)
        fig.text(.5, .865, "One held-out run · separate batch conditions · cropped view / full-run ARI", ha="center", fontsize=11, color=GREY)
        scene_info = {"scenario": scene, "methods": {}}
        for ax, method, label, color in zip(axes, predictions, ["Product Louvain", "Additive Louvain"], [BLUE, TEAL]):
            labels, weights, threshold = predictions[method]
            original_labels = labels[:len(base["event_id"])]
            ari = float(adjusted_rand_score(truth[truth >= 0], original_labels[truth >= 0]))
            n_edges = int(np.count_nonzero(np.triu(weights, 1)))
            expected = next(r for r in checkpoint["rows"] if r["method"] == method)
            comparison = {"scenario": scene, "method": method, "ari_replay": ari, "ari_checkpoint": expected["ari_original"],
                          "n_edges_replay": n_edges, "n_edges_checkpoint": expected["n_edges"],
                          "ari_matches": bool(np.isclose(ari, expected["ari_original"], atol=1e-12)), "n_edges_match": n_edges == expected["n_edges"]}
            MANIFEST["replay"]["original_checkpoint_comparisons"].append(comparison)
            # Tie-order differences in 2x copies were already reported by the paper.
            # An honest reproduction is shown with its own metric, never the old label.
            if not comparison["ari_matches"] or not comparison["n_edges_match"]:
                print("REPLAY DIFFERENCE", comparison, flush=True)
            scene_info["methods"][method] = comparison
            left, right = np.nonzero(np.triu(weights, 1))
            in_view = (np.abs(full_xy[:, 0]-center[0]) <= radius) & (np.abs(full_xy[:, 1]-center[1]) <= radius)
            ok = in_view[left] & in_view[right]
            left, right = left[ok], right[ok]
            order = np.argsort(weights[left, right])[-450:]
            segments = np.stack([full_xy[left[order]], full_xy[right[order]]], axis=1)
            ax.add_collection(LineCollection(segments, colors=color, alpha=.23, linewidths=.6))
            visible = np.flatnonzero(in_view)
            ax.scatter(full_xy[visible,0], full_xy[visible,1], s=15, c=[PALETTE[int(labels[k])%len(PALETTE)] for k in visible], edgecolor="white", linewidth=.25, zorder=3)
            if "copy" in scene:
                ax.text(.98, .04, scene.split("_")[-1] + " identical positions", transform=ax.transAxes, ha="right", color=color, fontsize=10,
                        bbox={"facecolor":"white", "edgecolor": "none", "alpha": .9})
                # Ring glyphs communicate overplotted multiplicity without moving data.
                original_visible = np.flatnonzero(in_view[:len(base["event_id"])] )
                ax.scatter(full_xy[original_visible,0], full_xy[original_visible,1], s=45 if scene.endswith("2x") else 70, facecolors="none", edgecolors=color, linewidths=.65, alpha=.55, zorder=4)
            ax.set_xlim(center[0]-radius, center[0]+radius); ax.set_ylim(center[1]-radius, center[1]+radius)
            ax.set_aspect("equal"); ax.set_title(f"{label}   |   ARI {ari:.3f}", fontsize=13, color=color, fontweight="bold", pad=8)
            tick_step = .5 if radius < 1.5 else 1
            ax.set_xticks(np.arange(math.ceil((center[0]-radius)/tick_step)*tick_step, center[0]+radius, tick_step)); ax.set_yticks(np.arange(math.ceil((center[1]-radius)/tick_step)*tick_step, center[1]+radius, tick_step))
            style_axes(ax, "Local east (km)", "Local north (km)" if method.startswith("product") else None)
            ax.tick_params(labelsize=9); ax.grid(color="#E8EDF1", linewidth=.6)
        frames.append(frame(fig)); info.append(scene_info)
    # An eighth, explicitly separate frame supplies the full-cohort result at a
    # readable scale. It is read from the exported paired-effects CSV and is
    # never inferred from this one-run replay.
    aggregate_source = source(RESULTS / "rq1_results/aggregate/rq1_stress_paired_effects.csv")
    aggregate = pd.read_csv(aggregate_source)
    aggregate = aggregate[aggregate.metric == "ari_original"]
    aggregate_methods = ["product_cij_louvain", "additive_cij_louvain", "additive_cij_louvain_matched_density", "product_cij_leiden", "geo_time_dbscan"]
    aggregate_scenarios = ["gps_noise_100m", "gps_noise_300m", "time_noise_15min", "time_noise_60min", "exact_transport_copy_2x", "exact_transport_copy_5x"]
    aggregate_values = np.array([[float(aggregate[(aggregate.method == m) & (aggregate.scenario == s)].mean_stress_minus_baseline.iloc[0]) for s in aggregate_scenarios] for m in aggregate_methods])
    fig, ax = plt.subplots(figsize=(10, 4.5))
    fig.subplots_adjust(left=.25, right=.985, top=.73, bottom=.20)
    fig.text(.5, .94, "Aggregate stress response — 40 held-out runs", ha="center", fontsize=18, fontweight="bold", fontfamily=["K2D", "Readex Pro", "DejaVu Sans"], color=INK)
    fig.text(.5, .85, "40-run cohort summary · mean paired ΔARI · negative = degradation", ha="center", fontsize=11, color=GREY)
    cmap = LinearSegmentedColormap.from_list("degradation", ["#F0C183", "#FFFDF8", "#2D83AC"])
    ax.imshow(aggregate_values, cmap=cmap, vmin=-.65, vmax=.05, aspect="auto")
    ax.set_yticks(range(5), ["Product Louvain", "Additive Louvain", "MD Additive", "Product Leiden", "Geo-time DBSCAN"])
    ax.set_xticks(range(6), ["GPS\n100 m", "GPS\n300 m", "Time\n15 min", "Time\n60 min", "Copies\n2×", "Copies\n5×"])
    ax.tick_params(length=0, pad=8, labelsize=12)
    for i in range(5):
        for j in range(6):
            ax.text(j, i, f"{aggregate_values[i,j]:+.3f}", ha="center", va="center", color=INK, fontsize=12, fontweight="bold")
    ax.set_xticks(np.arange(-.5, 6, 1), minor=True)
    ax.set_yticks(np.arange(-.5, 5, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=3)
    ax.tick_params(which="minor", bottom=False, left=False)
    for sp in ax.spines.values():
        sp.set_visible(False)
    summary_frame = frame(fig)
    summary_path = OUT / "graph_stress_summary.png"
    summary_frame.save(summary_path, dpi=(300, 300))
    frames.append(summary_frame)
    first = OUT/"graph_stress.png"; frames[0].save(first, dpi=(300,300))
    durations = [2400] * len(scenes) + [6000]
    frames[0].save(OUT/"graph_stress.gif", save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True, disposal=2)
    MANIFEST["assets"]["graph_stress.gif"] = {"kind": "one-run original-method replay followed by exported cohort summary", "dimensions_px": list(frames[0].size), "frames":len(frames), "duration_ms":sum(durations), "frame_durations_ms":durations,
          "poster":"graph_stress.png", "sha256":sha(OUT/"graph_stress.gif"), "values": info,
          "aggregate_poster":"graph_stress_summary.png", "aggregate_source":str(aggregate_source.relative_to(ROOT)),
          "aggregate_values":{m:dict(zip(aggregate_scenarios, row.tolist())) for m,row in zip(aggregate_methods,aggregate_values)},
          "caption":"Observable geographic window of run041 under seven separate fixed conditions, drawn using the original notebook graph and stress functions. Two compositions use their independently locked settings. ARI uses original incident-linked reports over the full run. The final frame separately shows the exported mean paired ARI changes across 40 held-out runs; it is not inferred from the one-run reproduction. This is a reproduction for explanation, not an added experiment.",
          "limitations":["Up to 450 strongest visible edges are drawn per panel; graph and ARI use the full run.", "Node colors identify predicted communities locally and are not stable incident IDs.", "Copy reports share positions; rings show multiplicity."]}
    MANIFEST["assets"]["graph_stress.png"] = {"kind":"static first-frame poster", "dimensions_px":list(frames[0].size), "sha256":sha(first)}
    MANIFEST["assets"]["graph_stress_summary.png"] = {"kind":"static final-frame aggregate poster", "dimensions_px":list(summary_frame.size), "source_files":[str(aggregate_source.relative_to(ROOT))], "sha256":sha(summary_path)}
    (OUT/"graph_replay_values.json").write_text(json.dumps(info, indent=2)+"\n")


def louvain_gif():
    rng = np.random.default_rng(20)
    positions = np.vstack([rng.normal([-.9,.45], [.2,.23], (4,2)), rng.normal([.8,.5],[.22,.22], (4,2)), rng.normal([.1,-.65],[.24,.18],(4,2))])
    edges = [(i,j) for start in (0,4,8) for i in range(start,start+4) for j in range(i+1,start+4)] + [(2,4),(7,8),(0,10)]
    labels = np.repeat(np.arange(3), 4)
    frames=[]
    phases=[("1  Start with one community per node",0), ("2  Move nodes to improve modularity",1), ("3  Communities become super-nodes",2), ("4  Repeat until no further improvement",3)]
    for title, phase in phases:
        fig, ax=plt.subplots(figsize=(10,4.5));fig.subplots_adjust(left=.06,right=.96,top=.77,bottom=.10)
        fig.text(.5,.93,title,ha="center",fontsize=19,fontweight="bold",fontfamily=["K2D", "Readex Pro", "DejaVu Sans"],color=INK)
        fig.text(.5,.85,"Schematic explanation · not measured rescue data",ha="center",fontsize=12,color=GREY)
        if phase < 2:
            for i,j in edges:ax.plot(positions[[i,j],0],positions[[i,j],1],color="#ADBCC9",lw=1.5 if labels[i]==labels[j] else .8, zorder=1)
            initial_palette = PALETTE + ["#6D68A7", "#B69A2A", "#68864F", "#A05935"]
            colors = initial_palette if phase==0 else [PALETTE[k] for k in labels]
            ax.scatter(positions[:,0],positions[:,1],s=500,c=colors,edgecolors="white",linewidth=2,zorder=2)
            for i,p in enumerate(positions):ax.text(p[0],p[1],str(i+1),ha="center",va="center",color="white",fontsize=12,fontweight="bold")
        else:
            centers=np.array([positions[labels==k].mean(axis=0) for k in range(3)])
            for i,j in [(0,1),(1,2),(0,2)]:ax.plot(centers[[i,j],0],centers[[i,j],1],color="#ADBCC9",lw=2)
            ax.scatter(centers[:,0],centers[:,1],s=2800,c=PALETTE[:3],edgecolors="white",linewidth=3,zorder=2)
            for i,p in enumerate(centers):ax.text(p[0],p[1],f"C{i+1}",ha="center",va="center",color="white",fontsize=20,fontweight="bold")
        ax.set_xlim(-1.65,1.65);ax.set_ylim(-1.3,1.15);ax.axis("off")
        frames.append(frame(fig))
    frames[0].save(OUT/"louvain_schematic.png",dpi=(300,300))
    frames[0].save(OUT/"louvain_schematic.gif",save_all=True,append_images=frames[1:],duration=3000,loop=0,optimize=True,disposal=2)
    MANIFEST["assets"]["louvain_schematic.gif"]={"kind":"pedagogical schematic", "dimensions_px":list(frames[0].size), "frames":4,"duration_ms":12000,"poster":"louvain_schematic.png","sha256":sha(OUT/"louvain_schematic.gif"),"caption":"Schematic two-phase Louvain explanation: move nodes to improve modularity, aggregate communities, and repeat. Node placement and colors are illustrative rather than experimental observations.","source_reference":"Blondel et al. (2008), Fast unfolding of communities in large networks, doi:10.1088/1742-5468/2008/10/P10008"}
    MANIFEST["assets"]["louvain_schematic.png"]={"kind":"static first-frame schematic poster","dimensions_px":list(frames[0].size),"sha256":sha(OUT/"louvain_schematic.png")}


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--only", choices=["all","charts","graph","louvain"], default="all");args=parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    # Match the supplied CTU template: K2D headings, Readex Pro body. Variable
    # Readex files are intentionally excluded so the static weight selection is
    # deterministic. DejaVu Sans is used only for unsupported symbol glyphs.
    font_paths = sorted((ROOT / "ISDS/fonts").rglob("*.ttf"))
    registered_fonts = []
    for font_path in font_paths:
        if "[" in font_path.name:
            continue
        font_manager.fontManager.addfont(str(font_path))
        registered_fonts.append({"path":str(font_path.relative_to(ROOT)), "family":font_manager.FontProperties(fname=str(font_path)).get_name(), "sha256":sha(font_path)})
    plt.rcParams.update({"font.family":["Readex Pro", "K2D", "DejaVu Sans"], "font.size":13, "axes.labelsize":13, "text.color":INK, "axes.labelcolor":INK, "figure.facecolor":"white"})
    existing=OUT/"manifest.json"
    if args.only!="all" and existing.exists():
        old=json.loads(existing.read_text());MANIFEST.update(old)
    MANIFEST["typography"] = {"body":"Readex Pro", "gif_headings":"K2D", "symbol_fallback":"K2D for arrows, DejaVu Sans only for glyphs absent from both CTU families", "fonts":registered_fonts}
    MANIFEST["presentation_style"] = {"bottom_caption_footnotes":False, "provenance_placement":"manifest and speaker notes; essential visual qualifiers directly below GIF heading"}
    if args.only in ("all","charts"):charts()
    if args.only in ("all","graph"):graph_gif()
    if args.only in ("all","louvain"):louvain_gif()
    MANIFEST["build_script"]={"path":str(Path(__file__).relative_to(ROOT)),"sha256":sha(__file__),"command":"/tmp/isds-build-venv/bin/python ISDS/scripts/build_science_assets.py"}
    existing.write_text(json.dumps(MANIFEST,ensure_ascii=False,indent=2)+"\n")
    print("Wrote", len(MANIFEST["assets"]), "scientific assets to", OUT, flush=True)


if __name__=="__main__":main()
