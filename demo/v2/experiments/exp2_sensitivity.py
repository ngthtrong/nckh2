"""Thí nghiệm 2 — Độ nhạy tham số.

Quét sigma_geo, lambda (resolution), s (chống bão hòa) để cho thấy hệ thống
ổn định và cách chọn tham số. Xuất bảng để vẽ đường cong trong bài báo.
"""
from __future__ import annotations

from common import prepared_events, print_table, save_table
from pipeline.config import ClusterParams, PriorityParams, WeightParams
from pipeline.clustering import run_louvain, modularity
from pipeline.metrics import cluster_quality, geographic_spread
from pipeline.priority import score_clusters
from pipeline.weighting import build_weight_matrix, sparsify


def sweep_sigma_geo(events):
    gt = [e.gt_cluster for e in events]
    rows = []
    for sigma in (200, 400, 700, 1000, 1500, 2500, 4000):
        wp = WeightParams(sigma_geo_m=float(sigma))
        w = build_weight_matrix(events, wp, mode="gating")
        ws = sparsify(w, wp)
        lab = run_louvain(ws, 1.0, 42)
        q = cluster_quality(lab, gt)
        sp = geographic_spread(events, lab)
        rows.append({
            "sigma_geo_m": sigma,
            "n_clusters": sp["n_clusters"],
            "ari": q["ari"],
            "nmi": q["nmi"],
            "mean_diam_km": sp["mean_diameter_km"],
            "modularity": round(modularity(ws, lab), 4),
        })
    return rows


def sweep_resolution(events):
    gt = [e.gt_cluster for e in events]
    wp = WeightParams()
    w = build_weight_matrix(events, wp, mode="gating")
    ws = sparsify(w, wp)
    rows = []
    for lam in (0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0):
        lab = run_louvain(ws, lam, 42)
        q = cluster_quality(lab, gt)
        sp = geographic_spread(events, lab)
        rows.append({
            "resolution_lambda": lam,
            "n_clusters": sp["n_clusters"],
            "ari": q["ari"],
            "nmi": q["nmi"],
            "mean_diam_km": sp["mean_diameter_km"],
        })
    return rows


def sweep_v_scale(events):
    wp = WeightParams()
    w = build_weight_matrix(events, wp, mode="gating")
    ws = sparsify(w, wp)
    lab = run_louvain(ws, 1.0, 42)
    rows = []
    for s in (1, 3, 5, 10, 20):
        pp = PriorityParams(v_scale=float(s))
        sc = score_clusters(events, lab, pp)
        # độ phân tán của V_agg trên các cụm (càng cao càng phân biệt tốt)
        v_aggs = [c.v_agg for c in sc]
        spread = max(v_aggs) - min(v_aggs)
        rows.append({
            "v_scale_s": s,
            "v_agg_min": round(min(v_aggs), 4),
            "v_agg_max": round(max(v_aggs), 4),
            "v_agg_spread": round(spread, 4),
        })
    return rows


def main():
    events = prepared_events()

    rows_sigma = sweep_sigma_geo(events)
    print_table("Quét sigma_geo (bán kính gating không gian)", rows_sigma)

    rows_res = sweep_resolution(events)
    print_table("Quét lambda (resolution parameter)", rows_res)

    rows_s = sweep_v_scale(events)
    print_table("Quét s (hệ số chống bão hòa tanh)", rows_s)

    save_table("exp2_sigma_geo.json", rows_sigma)
    save_table("exp2_resolution.json", rows_res)
    save_table("exp2_v_scale.json", rows_s)
    print("\n[saved] exp2_*.json -> results/tables/")


if __name__ == "__main__":
    main()
