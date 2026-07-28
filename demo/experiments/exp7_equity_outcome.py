"""Thí nghiệm 7 — outcome của chính sách ưu tiên, đa seed và đa depot.

Chỉ phục vụ các cụm có ít nhất hai báo cáo và có ít nhất một báo cáo C_i >= 0.5.
Quy tắc này loại các singleton/nhiễu mà điều phối viên thực tế không đưa thẳng
vào hàng đợi ca nô. Ba chính sách được so trên cùng phân hoạch và cùng hàng đợi:
V khuếch đại dạng nhân, bỏ V, và V dạng cộng. Mỗi seed sinh lại hình học liên
nhóm; mỗi chính sách chạy từ ba depot.
"""
from __future__ import annotations

import heapq
from statistics import mean

from common import bootstrap_ci, multi_seed, paired_test, print_table, save_table
from data.generate import CLUSTER_CENTERS, make_events
from pipeline.attributes import compute_confidence, haversine_m
from pipeline.clustering import run_louvain
from pipeline.config import DEFAULT_CONFIG as C
from pipeline.priority import score_clusters
from pipeline.weighting import build_weight_matrix, sparsify

N_BOATS = 3
V_BOAT_KMH = 30.0
T_SERVE_MIN = 15.0
MIN_CLUSTER_SERVE = 2
MIN_CONFIDENCE_SERVE = 0.5
SEVERE_FLOOD_THRESHOLD = 0.7
N_SEEDS = 20


def _simulate_arrival_times(ordered, depot):
    dlat, dlng = depot
    boats = [(0.0, dlat, dlng) for _ in range(N_BOATS)]
    heapq.heapify(boats)
    arrival = {}
    for score in ordered:
        free_t, blat, blng = heapq.heappop(boats)
        dist_km = haversine_m(
            blat, blng, score.center_lat, score.center_lng
        ) / 1000.0
        arr = free_t + 60.0 * dist_km / V_BOAT_KMH
        arrival[score.cluster_id] = arr
        heapq.heappush(
            boats,
            (arr + T_SERVE_MIN, score.center_lat, score.center_lng),
        )
    return arrival


def _vulnerable_weight(score, events_by_cluster):
    return sum(
        event.vulnerability
        for event in events_by_cluster.get(score.cluster_id, [])
    )


def _harm_weight(score, events_by_cluster):
    return _vulnerable_weight(score, events_by_cluster) * score.core


def _severe_vulnerable_weight(score, events_by_cluster):
    members = events_by_cluster.get(score.cluster_id, [])
    if not members or max(event.flood for event in members) <= SEVERE_FLOOD_THRESHOLD:
        return 0.0
    return sum(event.vulnerability for event in members)


def _weighted_time(scores, arrival, weight_fn, events_by_cluster):
    weighted = [
        (weight_fn(score, events_by_cluster), arrival[score.cluster_id])
        for score in scores
    ]
    denominator = sum(weight for weight, _ in weighted)
    if denominator <= 0:
        return 0.0
    return sum(weight * time for weight, time in weighted) / denominator


def _eligible_cluster_ids(events_by_cluster):
    return {
        cid
        for cid, members in events_by_cluster.items()
        if len(members) >= MIN_CLUSTER_SERVE
        and any(event.confidence >= MIN_CONFIDENCE_SERVE for event in members)
    }


def _run_seed(seed: int):
    events = make_events(seed=seed, geom_jitter=0.20)
    compute_confidence(events, C.confidence)
    weights = build_weight_matrix(events, C.weight, mode="gating")
    labels = run_louvain(
        sparsify(weights, C.weight),
        C.cluster.resolution,
        seed,
    )
    events_by_cluster = {}
    for event, label in zip(events, labels):
        events_by_cluster.setdefault(label, []).append(event)

    eligible = _eligible_cluster_ids(events_by_cluster)
    scores_full_all = score_clusters(
        events, labels, C.priority, normalize_v=True
    )
    scores_add_all = score_clusters(
        events, labels, C.priority, normalize_v=False
    )
    scores_full = [s for s in scores_full_all if s.cluster_id in eligible]
    scores_add = [s for s in scores_add_all if s.cluster_id in eligible]
    scores_no_v = sorted(scores_full, key=lambda s: s.core, reverse=True)
    scores_add = sorted(scores_add, key=lambda s: s.priority, reverse=True)
    policies = {
        "P_full_multiplicative": scores_full,
        "P_no_vulnerability": scores_no_v,
        "P_additive_V": scores_add,
    }

    centroid = (
        mean(s.center_lat for s in scores_full),
        mean(s.center_lng for s in scores_full),
    )
    depots = {
        "regional_centroid": centroid,
        "Hue": CLUSTER_CENTERS[0][:2],
        "Da_Nang": CLUSTER_CENTERS[3][:2],
    }

    rows = []
    for depot_name, depot in depots.items():
        for policy_name, ordered in policies.items():
            arrival = _simulate_arrival_times(ordered, depot)
            rows.append({
                "seed": seed,
                "depot": depot_name,
                "policy": policy_name,
                "n_clusters_served": len(ordered),
                "time_to_vulnerable_min": round(
                    _weighted_time(
                        scores_full, arrival, _vulnerable_weight,
                        events_by_cluster,
                    ),
                    4,
                ),
                "harm_weighted_time_min": round(
                    _weighted_time(
                        scores_full, arrival, _harm_weight,
                        events_by_cluster,
                    ),
                    4,
                ),
                "severe_flood_vulnerable_time_min": round(
                    _weighted_time(
                        scores_full, arrival, _severe_vulnerable_weight,
                        events_by_cluster,
                    ),
                    4,
                ),
                "mean_arrival_all_min": round(mean(arrival.values()), 4),
            })
    return {
        "seed": seed,
        "n_clusters_total": len(events_by_cluster),
        "n_clusters_served": len(eligible),
        "rows": rows,
    }


def _per_seed_means(runs):
    metrics = (
        "time_to_vulnerable_min",
        "harm_weighted_time_min",
        "severe_flood_vulnerable_time_min",
        "mean_arrival_all_min",
    )
    out = []
    for run in runs:
        policies = sorted({row["policy"] for row in run["rows"]})
        for policy in policies:
            selected = [row for row in run["rows"] if row["policy"] == policy]
            out.append({
                "seed": run["seed"],
                "policy": policy,
                "n_clusters_served": run["n_clusters_served"],
                **{
                    metric: round(mean(row[metric] for row in selected), 4)
                    for metric in metrics
                },
            })
    return out


def _summarize(per_seed):
    metrics = (
        "time_to_vulnerable_min",
        "harm_weighted_time_min",
        "severe_flood_vulnerable_time_min",
        "mean_arrival_all_min",
    )
    policies = sorted({row["policy"] for row in per_seed})
    rows = []
    for policy in policies:
        selected = [row for row in per_seed if row["policy"] == policy]
        summary = {"policy": policy, "n_seeds": len(selected)}
        for metric in metrics:
            values = [row[metric] for row in selected]
            lo, hi = bootstrap_ci(values)
            summary[f"{metric}_mean"] = round(mean(values), 2)
            summary[f"{metric}_ci95_lo"] = round(lo, 2)
            summary[f"{metric}_ci95_hi"] = round(hi, 2)
        rows.append(summary)
    return rows


def _comparisons(per_seed):
    primary = "severe_flood_vulnerable_time_min"
    by_policy = {}
    for row in per_seed:
        by_policy.setdefault(row["policy"], []).append(row)
    for values in by_policy.values():
        values.sort(key=lambda row: row["seed"])
    full = [row[primary] for row in by_policy["P_full_multiplicative"]]
    out = []
    for baseline in ("P_no_vulnerability", "P_additive_V"):
        other = [row[primary] for row in by_policy[baseline]]
        test = paired_test(full, other)
        out.append({
            "metric": primary,
            "comparison": f"P_full_multiplicative minus {baseline}",
            **test,
            "interpretation": (
                "negative favors multiplicative; evidence only if CI excludes 0"
            ),
        })
    return out


def main():
    runs = multi_seed(_run_seed, seeds=range(N_SEEDS))
    detail = [row for run in runs for row in run["rows"]]
    per_seed = _per_seed_means(runs)
    summary = _summarize(per_seed)
    comparisons = _comparisons(per_seed)

    print_table("Exp7 — trung bình theo seed (đã lấy trung bình 3 depot)", per_seed)
    print_table("Exp7 — outcome đa seed, bootstrap CI 95%", summary)
    print_table("Exp7 — Wilcoxon ghép cặp trên metric trung lập", comparisons)

    output = [{
        "config": {
            "n_boats": N_BOATS,
            "v_boat_kmh": V_BOAT_KMH,
            "t_serve_min": T_SERVE_MIN,
            "min_cluster_serve": MIN_CLUSTER_SERVE,
            "min_confidence_serve": MIN_CONFIDENCE_SERVE,
            "n_seeds": N_SEEDS,
            "depots": ["regional_centroid", "Hue", "Da_Nang"],
            "geom_jitter": 0.20,
        },
        "summary": summary,
        "paired_comparisons": comparisons,
        "primary_metric": "severe_flood_vulnerable_time_min",
        "metric_bias_note": {
            "time_to_vulnerable_min":
                "thiên vị dạng cộng (trọng số phẳng theo sum V)",
            "harm_weighted_time_min":
                "thiên vị dạng nhân (dùng lại core của P)",
            "severe_flood_vulnerable_time_min":
                "trung lập hơn: ngưỡng F>0.7 nằm ngoài công thức P",
        },
    }]
    save_table("exp7_equity_outcome.json", output)
    save_table("exp7_equity_per_seed.json", per_seed)
    save_table("exp7_equity_per_seed_depot.json", detail)
    print("\n[saved] exp7_equity_*.json -> results/tables/")


if __name__ == "__main__":
    main()
