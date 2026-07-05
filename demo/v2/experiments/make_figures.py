"""Sinh hình vẽ (matplotlib) từ các bảng kết quả JSON -> results/figures/*.png.

Chạy sau khi đã chạy exp1..exp4. Không dùng màu cố định của seaborn; dùng
matplotlib thuần để tái lập ổn định.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

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


def load(name: str):
    return json.loads((TABLES / name).read_text(encoding="utf-8"))


def fig_gating_vs_additive():
    rows = load("exp1_A_gating_vs_additive.json")
    modes = [r["mode"] for r in rows]
    diam = [r["mean_diam_km"] for r in rows]
    ari = [r["ari"] for r in rows]
    fig, ax1 = plt.subplots(figsize=(6, 4))
    x = range(len(modes))
    bars = ax1.bar(x, diam, color=["#c0392b", "#27ae60"], alpha=0.85)
    ax1.set_ylabel("Đường kính cụm trung bình (km)")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(["Cộng (additive)", "Nhân/Gating"])
    ax1.set_yscale("log")
    for b, d in zip(bars, diam):
        ax1.text(b.get_x() + b.get_width() / 2, d, f"{d:.2f} km",
                 ha="center", va="bottom", fontsize=9)
    ax1.set_title("Tác động của gating không gian tới độ gắn kết địa lý cụm\n(ARI giữ nguyên ≈ %.2f)" % ari[0])
    fig.savefig(FIGURES / "fig1_gating_vs_additive.png")
    plt.close(fig)


def fig_tanh_saturation():
    rows = load("exp1_D_tanh_saturation.json")
    v = [r["sum_V"] for r in rows]
    no_scale = [r["V_agg_no_scale(tanh(V))"] for r in rows]
    key_scaled = [k for k in rows[0] if k.startswith("V_agg_with_s")][0]
    scaled = [r[key_scaled] for r in rows]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(v, no_scale, "o-", color="#c0392b", label="tanh(ΣV)  — bão hòa sớm")
    ax.plot(v, scaled, "s-", color="#27ae60", label="tanh(ΣV/s), s=10 — phân biệt tốt")
    ax.set_xlabel("Tổng tổn thương trong cụm  ΣV")
    ax.set_ylabel("Hệ số V_agg")
    ax.set_title("Chống bão hòa tanh: giữ khả năng phân biệt\ncụm ít vs nhiều đối tượng yếu thế")
    ax.legend()
    fig.savefig(FIGURES / "fig2_tanh_saturation.png")
    plt.close(fig)


def fig_confidence_gate():
    row = load("exp1_E_confidence_gate.json")[0]
    labels = ["Không gate C_i\n(N thô)", "Có gate C_i\n(N·C_i)"]
    vals = [row["cluster_N_ungated"], row["cluster_N_gated"]]
    fig, ax = plt.subplots(figsize=(5.5, 4))
    bars = ax.bar(labels, vals, color=["#c0392b", "#27ae60"], alpha=0.85)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.0f}", ha="center", va="bottom")
    ax.set_ylabel("Tổng số người quy đổi của cụm chứa tin giả")
    ax.set_title("Gate C_i hạ nhiệt tin giả (S3)\nC_i tin giả = %.2f, giảm %.0f%%"
                 % (row["fake_confidence_Ci"], row["reduction_pct"]))
    fig.savefig(FIGURES / "fig3_confidence_gate.png")
    plt.close(fig)


def fig_sigma_sweep():
    rows = load("exp2_sigma_geo.json")
    sig = [r["sigma_geo_m"] for r in rows]
    diam = [r["mean_diam_km"] for r in rows]
    nclu = [r["n_clusters"] for r in rows]
    fig, ax1 = plt.subplots(figsize=(6.5, 4))
    ax1.plot(sig, diam, "o-", color="#2980b9", label="Đường kính cụm TB (km)")
    ax1.set_xlabel("σ_geo (mét)")
    ax1.set_ylabel("Đường kính cụm TB (km)", color="#2980b9")
    ax1.tick_params(axis="y", labelcolor="#2980b9")
    ax2 = ax1.twinx()
    ax2.plot(sig, nclu, "s--", color="#e67e22", label="Số cụm")
    ax2.set_ylabel("Số cụm", color="#e67e22")
    ax2.tick_params(axis="y", labelcolor="#e67e22")
    ax2.grid(False)
    ax1.set_title("Độ nhạy σ_geo: đánh đổi bán kính gating vs số cụm")
    fig.savefig(FIGURES / "fig4_sigma_sweep.png")
    plt.close(fig)


def fig_resolution_sweep():
    rows = load("exp2_resolution.json")
    lam = [r["resolution_lambda"] for r in rows]
    ari = [r["ari"] for r in rows]
    nclu = [r["n_clusters"] for r in rows]
    fig, ax1 = plt.subplots(figsize=(6.5, 4))
    ax1.plot(lam, ari, "o-", color="#27ae60", label="ARI")
    ax1.set_xlabel("λ (resolution)")
    ax1.set_ylabel("ARI", color="#27ae60")
    ax1.tick_params(axis="y", labelcolor="#27ae60")
    ax2 = ax1.twinx()
    ax2.plot(lam, nclu, "s--", color="#8e44ad", label="Số cụm")
    ax2.set_ylabel("Số cụm", color="#8e44ad")
    ax2.tick_params(axis="y", labelcolor="#8e44ad")
    ax2.grid(False)
    ax1.set_title("Độ nhạy λ: tăng λ ⇒ chia cụm sâu hơn (ARI ổn định tới λ≈1.5)")
    fig.savefig(FIGURES / "fig5_resolution_sweep.png")
    plt.close(fig)


def fig_baselines():
    rows = load("exp4_baselines.json")
    names = [r["method"].replace(" (", "\n(") for r in rows]
    ari = [r["ari"] for r in rows]
    diam = [r["mean_diam_km"] for r in rows]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.5))
    colors = ["#27ae60" if ("Louvain" in r["method"] or "Leiden" in r["method"])
              else "#c0392b" for r in rows]
    a1.barh(names, ari, color=colors, alpha=0.85)
    a1.set_xlabel("ARI (cao hơn = tốt hơn)")
    a1.set_title("Chất lượng cụm vs ground-truth")
    a1.invert_yaxis()
    a2.barh(names, diam, color=colors, alpha=0.85)
    a2.set_xlabel("Đường kính cụm TB (km, thấp hơn = gắn kết hơn)")
    a2.set_title("Độ gắn kết địa lý")
    a2.set_xscale("log")
    a2.invert_yaxis()
    fig.suptitle("Louvain/Leiden (đồ thị gating) vs K-Means / DBSCAN")
    fig.savefig(FIGURES / "fig6_baselines.png")
    plt.close(fig)


def main():
    fig_gating_vs_additive()
    fig_tanh_saturation()
    fig_confidence_gate()
    fig_sigma_sweep()
    fig_resolution_sweep()
    fig_baselines()
    figs = sorted(p.name for p in FIGURES.glob("*.png"))
    print("Đã sinh", len(figs), "hình -> results/figures/")
    for f in figs:
        print("  -", f)


if __name__ == "__main__":
    main()
