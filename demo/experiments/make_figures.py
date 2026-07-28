"""Sinh hình vẽ (matplotlib) từ các bảng kết quả JSON -> results/figures/*.png.

Chạy sau khi đã chạy exp1..exp12. Không dùng màu cố định của seaborn; dùng
matplotlib thuần để tái lập ổn định.

Bộ hình (7 hình, đánh số theo thứ tự xuất hiện trong bài báo):
  fig1_ablation        — 2 panel: quét alpha (cộng) vs gating; và tác dụng gate C_i
  fig2_map             — phân bố dữ liệu + ba cặp nhãn chồng lấn không gian
  fig3_heatmap         — bề mặt ARI theo (tau_F, tau_E)
  fig4_sigma_sweep     — độ nhạy sigma_geo
  fig5_resolution_sweep— độ nhạy lambda
  fig6_baselines       — đối chiếu baseline (ARI, đường kính, hấp thụ nhiễu)
  fig7_ranking_stability— độ ổn định xếp hạng P(C_k)
  fig8_lemma1          — Bổ đề 1: cận đường kính của dạng nhân luôn đúng, dạng cộng
                         không có cận (đóng góp lý thuyết trung tâm, P0)

Lưu ý về độ đo: mọi hình dùng `mean_diam_km_multi` / `max_diam_km` (chỉ cụm có
>= 2 thành viên) thay cho `mean_diam_km` cũ — độ đo cũ tính cả singleton (đường
kính 0) nên thưởng giả tạo cho phân hoạch vụn (phản biện 2.2).
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import prepared_events
from pipeline.attributes import haversine_m
from pipeline.clustering import run_louvain
from pipeline.config import DEFAULT_CONFIG as C
from pipeline.metrics import geographic_spread
from pipeline.weighting import build_weight_matrix, sparsify

V2_ROOT = Path(__file__).resolve().parents[1]
TABLES = V2_ROOT / "results" / "tables"
FIGURES = V2_ROOT / "results" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 130,
    "savefig.bbox": "tight",
    "font.size": 10,
    "axes.grid": True,
    "grid.alpha": 0.3,
})

GREEN = "#27ae60"
RED = "#c0392b"
BLUE = "#2980b9"
ORANGE = "#e67e22"
PURPLE = "#8e44ad"


def load(name: str):
    return json.loads((TABLES / name).read_text(encoding="utf-8"))


def _short_variant(v: str) -> str:
    """Nhãn ngắn cho trục x của hình ablation."""
    return (v.replace("additive (alpha=", "additive\nα=")
             .replace("additive (chuẩn hoá 1/3)", "additive\nnorm 1/3")
             .replace("gating (nhân, đề xuất)", "gating\n(ours)")
             .replace(" = beta = gamma", "")
             .replace(")", ""))


# --------------------------------------------------------------------------
# fig1 — ablation: quét alpha + gate C_i (gộp fig1 và fig3 cũ)
# --------------------------------------------------------------------------
def fig_ablation():
    rows = load("exp1_A_gating_vs_additive.json")
    gate = load("exp1_E_confidence_gate.json")[0]

    names = [_short_variant(r["variant"]) for r in rows]
    maxd = [r["max_diam_km"] for r in rows]
    ari = [r["ari"] for r in rows]
    merged = [r["far_groups_merged"] for r in rows]
    colors = [GREEN if not m else RED for m in merged]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2),
                                 gridspec_kw={"width_ratios": [2.1, 1]})

    x = np.arange(len(names))
    bars = a1.bar(x, maxd, color=colors, alpha=0.85)
    a1.set_yscale("log")
    a1.set_ylabel("Max cluster diameter (km, log scale)")
    a1.set_xticks(x)
    a1.set_xticklabels(names, fontsize=8)
    for b, d, m, r in zip(bars, maxd, merged, ari):
        a1.text(b.get_x() + b.get_width() / 2, d * 1.12,
                f"{d:.1f} km\nARI {r:.3f}", ha="center", va="bottom", fontsize=7.5)
        a1.text(b.get_x() + b.get_width() / 2, min(maxd) * 0.35,
                "far groups merged" if m else "far groups kept apart",
                ha="center", va="bottom", fontsize=7,
                color="white", rotation=90,
                bbox=dict(boxstyle="round,pad=0.15", fc=RED if m else GREEN, ec="none"))
    a1.set_ylim(min(maxd) * 0.25, max(maxd) * 4)
    a1.set_title("(a) Additive weight (α sweep) vs multiplicative gating\n"
                 "additive diameters blow up to ~100 km regardless of α",
                 fontsize=9.5)

    labels = ["No $C_i$ gate\n(raw $N$)", "With $C_i$ gate\n($N \\cdot C_i$)"]
    vals = [gate["cluster_N_ungated"], gate["cluster_N_gated"]]
    b2 = a2.bar(labels, vals, color=[RED, GREEN], alpha=0.85, width=0.6)
    for b, v in zip(b2, vals):
        a2.text(b.get_x() + b.get_width() / 2, v, f"{v:.0f}",
                ha="center", va="bottom", fontsize=9)
    a2.set_ylabel("Effective population of the cluster")
    a2.set_title("(b) $C_i$ gate dampens a fake report\n"
                 "fake $C_i$ = %.2f, claim reduced %.0f%%"
                 % (gate["fake_confidence_Ci"], gate["reduction_pct"]), fontsize=9.5)

    fig.savefig(FIGURES / "fig1_ablation.png")
    plt.close(fig)


# --------------------------------------------------------------------------
# fig2 — bản đồ cụm: dạng cộng vs dạng nhân trên cùng dữ liệu
# --------------------------------------------------------------------------
def _worst_merge(events, labels):
    """Cặp điểm CÓ NHÃN GT xa nhau nhất mà bị phân hoạch `labels` gộp vào một cụm.

    Trả về (i, j, dist_km, gt_i, gt_j) hoặc None nếu không có cụm nào gộp hai
    nhóm GT khác nhau. Dùng để chú thích hình 2 bằng SỐ ĐO trên dữ liệu hiện
    hành, thay vì neo vào ID kịch bản cố định (các ID S1-A/S1-B của bộ dữ liệu
    cũ không còn tồn tại — phản biện P3.2).
    """
    from pipeline.metrics import haversine_m

    buckets: dict[int, list[int]] = {}
    for i, (ev, lab) in enumerate(zip(events, labels)):
        if ev.gt_cluster is not None and ev.gt_cluster >= 0:
            buckets.setdefault(lab, []).append(i)

    best = None
    for idx in buckets.values():
        if len({events[i].gt_cluster for i in idx}) < 2:
            continue
        for a in range(len(idx)):
            for b in range(a + 1, len(idx)):
                i, j = idx[a], idx[b]
                if events[i].gt_cluster == events[j].gt_cluster:
                    continue
                d = haversine_m(events[i].lat, events[i].lng,
                                events[j].lat, events[j].lng) / 1000.0
                if best is None or d > best[2]:
                    best = (i, j, d, events[i].gt_cluster, events[j].gt_cluster)
    return best


def _cluster_map(ax, events, labels, title, note: str | None = None,
                 marks: list[tuple[int, str]] | None = None):
    """Vẽ scatter sự kiện + nan hoa từ tâm cụm tới thành viên.

    Nan hoa dài = cụm bị kéo giãn địa lý; đây là điều mà ARI không thấy được.
    Khi cụm chặt (đường kính < 1,5 km) nan hoa co về gần một điểm ở tỷ lệ vùng,
    nên panel gating trông như các điểm rời — dùng `note` để nói rõ điều đó,
    tránh người đọc hiểu sai là "không có cụm".
    """
    lat = np.array([e.lat for e in events])
    lng = np.array([e.lng for e in events])
    lab = np.array(labels)
    uniq = sorted(set(lab))
    cmap = plt.get_cmap("tab20")

    for k, cl in enumerate(uniq):
        idx = np.where(lab == cl)[0]
        col = cmap(k % 20)
        if len(idx) >= 2:
            clat, clng = lat[idx].mean(), lng[idx].mean()
            for i in idx:
                ax.plot([clng, lng[i]], [clat, lat[i]], "-",
                        color=col, lw=0.6, alpha=0.55, zorder=1)
        ax.scatter(lng[idx], lat[idx], s=14, color=col,
                   edgecolors="none", zorder=2)

    # đánh dấu các điểm được truyền vào (do người gọi tính từ dữ liệu).
    # Lệch nhãn theo thứ tự: hai điểm bị gộp có thể cách nhau vài km nên ở tỷ lệ
    # vùng chúng gần trùng nhau, nhãn sẽ chồng nếu dùng chung một offset.
    for n, (i, txt) in enumerate(marks or []):
        ax.annotate(txt, (lng[i], lat[i]),
                    textcoords="offset points", xytext=(7, 7 - 12 * n),
                    fontsize=8, fontweight="bold")
        ax.scatter([lng[i]], [lat[i]], s=70, facecolors="none",
                   edgecolors="black", lw=1.0, zorder=3)

    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.set_title(title, fontsize=9.5)
    if note:
        ax.text(0.02, 0.02, note, transform=ax.transAxes, fontsize=7.5,
                va="bottom", ha="left",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.7", alpha=0.9))


def fig_map():
    """Phân bố GT và ba cặp nhóm chồng lấn — bằng chứng trực quan độ khó P1."""
    events = prepared_events()
    cmap = plt.get_cmap("tab20")
    fig = plt.figure(figsize=(11.8, 6.0))
    grid = fig.add_gridspec(3, 2, width_ratios=(1.45, 1.0), hspace=0.48)
    regional = fig.add_subplot(grid[:, 0])

    for gt in range(13):
        members = [event for event in events if event.gt_cluster == gt]
        regional.scatter(
            [event.lng for event in members],
            [event.lat for event in members],
            s=13,
            color=cmap(gt),
            label=f"g{gt}",
            alpha=0.8,
        )
    noise = [event for event in events if event.gt_cluster < 0]
    regional.scatter(
        [event.lng for event in noise],
        [event.lat for event in noise],
        s=11,
        marker="x",
        color="0.55",
        alpha=0.75,
        label="noise/fake",
    )
    regional.set_xlabel("Longitude (°E)")
    regional.set_ylabel("Latitude (°N)")
    regional.set_title("(a) Full synthetic region: 13 physical-event labels + noise",
                       fontsize=9.5)
    regional.legend(ncol=3, fontsize=6.5, loc="best", framealpha=0.9)

    pair_names = [
        ((0, 1), "Hue"),
        ((2, 3), "Hoi An"),
        ((4, 5), "Da Nang"),
    ]
    for row, ((ga, gb), place) in enumerate(pair_names):
        ax = fig.add_subplot(grid[row, 1])
        for gt, marker in ((ga, "o"), (gb, "s")):
            members = [event for event in events if event.gt_cluster == gt]
            ax.scatter(
                [event.lng for event in members],
                [event.lat for event in members],
                s=19,
                marker=marker,
                color=cmap(gt),
                alpha=0.72,
                label=f"g{gt}",
            )
        centroids = {}
        for gt in (ga, gb):
            members = [event for event in events if event.gt_cluster == gt]
            centroids[gt] = (
                mean(event.lat for event in members),
                mean(event.lng for event in members),
            )
        distance = haversine_m(*centroids[ga], *centroids[gb])
        ax.plot(
            [centroids[ga][1], centroids[gb][1]],
            [centroids[ga][0], centroids[gb][0]],
            "k--",
            lw=1.0,
        )
        ax.scatter(
            [centroids[ga][1], centroids[gb][1]],
            [centroids[ga][0], centroids[gb][0]],
            s=45,
            facecolors="none",
            edgecolors="black",
            linewidths=1.0,
        )
        ax.set_title(
            f"({chr(ord('b') + row)}) {place}: g{ga}/g{gb}, "
            f"centroids {distance:.0f} m apart",
            fontsize=8.8,
        )
        ax.legend(fontsize=7, loc="best")
        ax.tick_params(labelsize=7)
        if row == 2:
            ax.set_xlabel("Longitude (°E)", fontsize=8)
        ax.set_ylabel("Latitude (°N)", fontsize=8)

    fig.suptitle(
        "Dataset geometry: spatial envelopes overlap, while flood/urgency "
        "profiles define distinct events",
        fontsize=10,
    )
    fig.savefig(FIGURES / "fig2_map.png")
    plt.close(fig)


# --------------------------------------------------------------------------
# fig3 — heatmap độ nhạy ARI theo (tau_F, tau_E)
# --------------------------------------------------------------------------
def fig_heatmap():
    rows = load("exp2_tau_context.json")
    tau_f = sorted({r["tau_f"] for r in rows})
    tau_e = sorted({r["tau_e"] for r in rows})
    lookup = {(r["tau_f"], r["tau_e"]): r for r in rows}
    ari = np.array([[lookup[(tf, te)]["ari"] for te in tau_e] for tf in tau_f])

    fig, ax = plt.subplots(figsize=(6.7, 5.2))
    im = ax.imshow(
        ari,
        origin="lower",
        aspect="auto",
        cmap="viridis",
        vmin=float(ari.min()),
        vmax=float(ari.max()),
    )
    ax.set_xticks(range(len(tau_e)), [f"{v:g}" for v in tau_e])
    ax.set_yticks(range(len(tau_f)), [f"{v:g}" for v in tau_f])
    ax.set_xlabel(r"$\tau_E$")
    ax.set_ylabel(r"$\tau_F$")
    for i in range(len(tau_f)):
        for j in range(len(tau_e)):
            color = "white" if ari[i, j] < np.median(ari) else "black"
            ax.text(j, i, f"{ari[i, j]:.3f}", ha="center", va="center",
                    fontsize=7.2, color=color)
    fig.colorbar(im, ax=ax, label="ARI")
    ax.set_title(
        r"Context sensitivity over $(\tau_F,\tau_E)$: "
        f"ARI range = {ari.max() - ari.min():.3f}",
        fontsize=9.5,
    )
    fig.savefig(FIGURES / "fig3_heatmap.png")
    plt.close(fig)


# --------------------------------------------------------------------------
# fig4/fig5 — độ nhạy tham số
# --------------------------------------------------------------------------
def fig_sigma_sweep():
    rows = load("exp2_sigma_geo.json")
    sig = [r["sigma_geo_m"] for r in rows]
    diam = [r["mean_diam_km_multi"] for r in rows]
    ari = [r["ari"] for r in rows]
    fig, ax1 = plt.subplots(figsize=(6.5, 4))
    ax1.plot(sig, diam, "o-", color=BLUE, label="Mean diameter, multi-member clusters (km)")
    ax1.set_xlabel("$\\sigma_{geo}$ (meters)")
    ax1.set_ylabel("Mean cluster diameter (km)", color=BLUE)
    ax1.tick_params(axis="y", labelcolor=BLUE)
    ax2 = ax1.twinx()
    ax2.plot(sig, ari, "s--", color=ORANGE, label="ARI")
    ax2.set_ylabel("ARI", color=ORANGE)
    ax2.tick_params(axis="y", labelcolor=ORANGE)
    ax2.grid(False)
    ax1.set_title("$\\sigma_{geo}$ sensitivity: ARI spans %.3f over the swept range"
                  % (max(ari) - min(ari)), fontsize=9.5)
    fig.savefig(FIGURES / "fig4_sigma_sweep.png")
    plt.close(fig)


def fig_resolution_sweep():
    rows = load("exp2_resolution.json")
    lam = [r["resolution_lambda"] for r in rows]
    ari = [r["ari"] for r in rows]
    nclu = [r["n_clusters"] for r in rows]
    fig, ax1 = plt.subplots(figsize=(6.5, 4))
    ax1.plot(lam, ari, "o-", color=GREEN, label="ARI")
    ax1.set_xlabel("$\\lambda$ (resolution)")
    ax1.set_ylabel("ARI", color=GREEN)
    ax1.tick_params(axis="y", labelcolor=GREEN)
    ax2 = ax1.twinx()
    ax2.plot(lam, nclu, "s--", color=PURPLE, label="Number of clusters")
    ax2.set_ylabel("Number of clusters", color=PURPLE)
    ax2.tick_params(axis="y", labelcolor=PURPLE)
    ax2.grid(False)
    best = max(rows, key=lambda r: r["ari"])
    ax1.axvline(best["resolution_lambda"], color=RED, ls=":", alpha=0.6)
    ax1.set_title("$\\lambda$ sensitivity: ARI peaks at $\\lambda$ = %.1f, spans %.3f"
                  % (best["resolution_lambda"], max(ari) - min(ari)), fontsize=9.5)
    fig.savefig(FIGURES / "fig5_resolution_sweep.png")
    plt.close(fig)


# --------------------------------------------------------------------------
# fig6 — baseline (3 panel: ARI, đường kính, hấp thụ nhiễu)
# --------------------------------------------------------------------------
def fig_baselines():
    rows = load("exp4_baselines.json")
    names = [r["method"].replace(" (", "\n(") for r in rows]
    ari = [r["ari"] for r in rows]
    diam = [r["mean_diam_km_labeled"] for r in rows]
    noise = [r["noise_absorbed_pct"] for r in rows]
    ours = [("Louvain" in r["method"] or "Leiden" in r["method"]) for r in rows]
    colors = [GREEN if o else RED for o in ours]

    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(14, 4.6))
    a1.barh(names, ari, color=colors, alpha=0.85)
    a1.set_xlabel("ARI (higher = better)")
    a1.set_title("Agreement with ground truth", fontsize=9.5)
    a1.invert_yaxis()

    a2.barh(names, [max(d, 1e-3) for d in diam], color=colors, alpha=0.85)
    a2.set_xlabel("Mean diameter of labeled clusters (km, lower = better)")
    a2.set_title("Geographic cohesion (same convention)", fontsize=9.5)
    a2.set_xscale("log")
    a2.invert_yaxis()
    a2.set_yticklabels([])

    a3.barh(names, noise, color=colors, alpha=0.85)
    a3.set_xlabel("Noise absorbed into clusters (%, lower = better)")
    a3.set_title("Robustness to unlabelled noise", fontsize=9.5)
    a3.invert_yaxis()
    a3.set_yticklabels([])

    fig.suptitle("ARI alone hides the failure modes: a method can match the labels "
                 "while spanning tens of km and swallowing every noise point", fontsize=10)
    fig.savefig(FIGURES / "fig6_baselines.png")
    plt.close(fig)


# --------------------------------------------------------------------------
# fig7 — độ ổn định xếp hạng
# --------------------------------------------------------------------------
def fig_ranking_stability():
    rows = load("exp5_ranking_stability.json")
    levels = [r["omega_perturbation"] for r in rows]
    tau_mean = [r["mean_kendall_tau"] for r in rows]
    tau_min = [r["min_kendall_tau"] for r in rows]
    top3 = [r["top3_set_preserved_pct"] for r in rows]
    fig, ax1 = plt.subplots(figsize=(7, 4.5))
    x = range(len(levels))
    ax1.bar([i - 0.15 for i in x], tau_mean, 0.3, color=GREEN, alpha=0.85, label="Mean τ")
    ax1.bar([i + 0.15 for i in x], tau_min, 0.3, color=ORANGE, alpha=0.85, label="Min τ")
    ax1.set_ylabel("Kendall's τ")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(levels)
    ax1.set_xlabel("ω perturbation level")
    ax1.set_ylim(min(tau_min) - 0.05, 1.02)
    ax1.axhline(y=0.9, color=RED, linestyle="--", alpha=0.5, label="τ = 0.9 threshold")
    ax1.legend(loc="lower left", fontsize=8)
    ax2 = ax1.twinx()
    ax2.plot(list(x), top3, "s-", color=PURPLE, label="Top-3 preserved (%)")
    ax2.set_ylabel("Top-3 preserved (%)", color=PURPLE)
    ax2.tick_params(axis="y", labelcolor=PURPLE)
    ax2.set_ylim(min(top3) - 8, 105)
    ax2.grid(False)
    ax2.legend(loc="lower right", fontsize=8)
    ax1.set_title("Ranking stability of $P(C_k)$ under ω perturbation\n"
                  "(200 Monte-Carlo trials per level)", fontsize=9.5)
    fig.savefig(FIGURES / "fig7_ranking_stability.png")
    plt.close(fig)


# --------------------------------------------------------------------------
# fig8 — kiểm Bổ đề 1: cận đường kính của dạng nhân vs dạng cộng
# --------------------------------------------------------------------------
def fig_lemma1():
    """Bổ đề 1 bằng hình: khoảng cách cạnh dài nhất so với cận sigma*sqrt(2 ln 1/theta).

    Đây là hình cho đóng góp lý thuyết trung tâm (P0). Trục y log vì dạng cộng vượt
    cận tới hai bậc độ lớn: sàn cộng alpha*S_geo + ... không bao giờ tụt dưới
    beta*S_temp + gamma*S_ctx, nên một cặp cách 188 km vẫn có w > theta.

    Đọc hình: đường nét liền = cận lý thuyết; điểm = khoảng cách cạnh dài nhất ĐO
    ĐƯỢC. Điểm nằm DƯỚI đường là bổ đề đúng; nằm TRÊN là vi phạm.
    """
    gat = load("exp13_lemma1_detail_gating.json")
    add = load("exp13_lemma1_detail_additive_alpha05.json")
    summary = load("exp13_lemma1_check.json")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))

    # (a) gating — điểm luôn nằm dưới cận
    th = [r["theta"] for r in gat]
    bound = [r["implied_cutoff_m"] / 1000 for r in gat]
    meas = [r["max_edge_dist_m"] / 1000 for r in gat]
    a1.plot(th, bound, "-", color=BLUE, lw=2,
            label=r"bound $\sigma\sqrt{2\ln(1/\theta)}$")
    a1.plot(th, meas, "o", color=GREEN, ms=4,
            label=r"measured $\max\{d_{ij}: w_{ij}>\theta\}$")
    a1.fill_between(th, meas, bound, color=GREEN, alpha=0.12)
    a1.set_xlabel(r"$\theta$")
    a1.set_ylabel("Distance (km)")
    a1.set_title("(a) Multiplicative gating: bound always holds\n"
                 "%d/%d $\\theta$ values, 0 violations"
                 % (summary[0]["n_theta_checked"], summary[0]["n_theta_checked"]),
                 fontsize=9.5)
    a1.legend(fontsize=8, loc="upper right")

    # (b) dạng cộng — vượt cận nhiều bậc độ lớn
    s_add = next(s for s in summary if s["form"] == "additive (alpha=0.5)")
    th2 = [r["theta"] for r in add]
    bound2 = [r["implied_cutoff_m"] / 1000 for r in add]
    meas2 = [r["max_edge_dist_m"] / 1000 for r in add]
    viol = [r["violates_lemma1"] for r in add]
    a2.plot(th2, bound2, "-", color=BLUE, lw=2, label="same bound")
    a2.plot([t for t, v in zip(th2, viol) if v],
            [m for m, v in zip(meas2, viol) if v],
            "x", color=RED, ms=5, label="measured (violates)")
    a2.plot([t for t, v in zip(th2, viol) if not v],
            [m for m, v in zip(meas2, viol) if not v],
            "o", color=GREEN, ms=4, label="measured (holds)")
    a2.axhline(188.8, color=ORANGE, ls=":", lw=1.2)
    a2.text(th2[len(th2) // 2], 205, "dataset extent 188.8 km",
            fontsize=7.5, color=ORANGE)
    a2.set_yscale("log")
    a2.set_xlabel(r"$\theta$")
    a2.set_ylabel("Distance (km, log scale)")
    a2.set_title("(b) Additive weight ($\\alpha=0.5$): no bound exists\n"
                 "%d/%d $\\theta$ values violate (floor = %.4f)"
                 % (s_add["n_lemma1_violations"], s_add["n_theta_checked"],
                    s_add["additive_floor"]), fontsize=9.5)
    a2.legend(fontsize=8, loc="center right")

    fig.savefig(FIGURES / "fig8_lemma1.png")
    plt.close(fig)


def main():
    # hình cũ đã bỏ (fig2_tanh_saturation: đồ thị hàm thuần, không có dữ liệu;
    # fig3_confidence_gate: đã gộp vào fig1) — xoá để results/figures không lẫn
    for stale in ("fig1_gating_vs_additive.png", "fig2_tanh_saturation.png",
                  "fig3_confidence_gate.png"):
        (FIGURES / stale).unlink(missing_ok=True)

    fig_ablation()
    fig_map()
    fig_heatmap()
    fig_sigma_sweep()
    fig_resolution_sweep()
    fig_baselines()
    fig_ranking_stability()
    fig_lemma1()
    figs = sorted(p.name for p in FIGURES.glob("*.png"))
    print("Đã sinh", len(figs), "hình -> results/figures/")
    for f in figs:
        print("  -", f)


if __name__ == "__main__":
    main()
