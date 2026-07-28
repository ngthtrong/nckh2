"""Thí nghiệm 8 — đánh giá đúng mức heuristic C_i.

Báo cáo AUC/AP biên, AUC/AP theo tầng mật độ láng giềng, từng đặc trưng đơn,
sweep (b1,b2), và chiến dịch tin giả có thật trong generator. C_i được xem như
quy ước tổng hợp có thể giải thích, không mặc nhiên là detector tốt hơn
`n_corrob`.
"""
from __future__ import annotations

import math

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

from common import prepared_events, print_table, save_table
from pipeline.config import DEFAULT_CONFIG as C


def _metrics_with_ci(y_true, y_score, n_boot=1000, seed=42):
    """AUC/AP + bootstrap phân tầng; trả None khi tầng chỉ có một lớp."""
    y_true = np.asarray(y_true, dtype=int)
    y_score = np.asarray(y_score, dtype=float)
    if len(y_true) == 0 or len(set(y_true.tolist())) < 2:
        return {
            "auc": None,
            "auc_ci95_lo": None,
            "auc_ci95_hi": None,
            "ap": None,
            "ap_ci95_lo": None,
            "ap_ci95_hi": None,
            "baseline_ap": round(float(y_true.mean()), 4) if len(y_true) else None,
            "n": int(len(y_true)),
            "n_fake": int(y_true.sum()),
        }
    auc = float(roc_auc_score(y_true, y_score))
    ap = float(average_precision_score(y_true, y_score))
    pos = np.flatnonzero(y_true == 1)
    neg = np.flatnonzero(y_true == 0)
    rng = np.random.default_rng(seed)
    aucs, aps = [], []
    for _ in range(n_boot):
        take = np.concatenate([
            rng.choice(pos, size=len(pos), replace=True),
            rng.choice(neg, size=len(neg), replace=True),
        ])
        aucs.append(float(roc_auc_score(y_true[take], y_score[take])))
        aps.append(float(average_precision_score(y_true[take], y_score[take])))
    return {
        "auc": round(auc, 4),
        "auc_ci95_lo": round(float(np.percentile(aucs, 2.5)), 4),
        "auc_ci95_hi": round(float(np.percentile(aucs, 97.5)), 4),
        "ap": round(ap, 4),
        "ap_ci95_lo": round(float(np.percentile(aps, 2.5)), 4),
        "ap_ci95_hi": round(float(np.percentile(aps, 97.5)), 4),
        "baseline_ap": round(float(y_true.mean()), 4),
        "n": int(len(y_true)),
        "n_fake": int(y_true.sum()),
    }


def _feature_rows(events):
    y = np.array([int(event.is_fake) for event in events])
    features = {
        "1-C_i (combined heuristic)": np.array(
            [1.0 - event.confidence for event in events]
        ),
        "-n_corrob": np.array([-float(event.n_corrob) for event in events]),
        "1-has_image": np.array(
            [1.0 - float(event.has_image) for event in events]
        ),
    }
    return [
        {"feature": name, **_metrics_with_ci(y, score)}
        for name, score in features.items()
    ]


def _conditional_density_rows(events):
    tiers = (
        ("n_corrob=0", lambda n: n == 0),
        ("n_corrob=1-5", lambda n: 1 <= n <= 5),
        ("n_corrob>5", lambda n: n > 5),
    )
    rows = []
    for name, predicate in tiers:
        selected = [event for event in events if predicate(event.n_corrob)]
        y = [int(event.is_fake) for event in selected]
        score = [1.0 - event.confidence for event in selected]
        rows.append({
            "density_tier": name,
            **_metrics_with_ci(y, score, seed=43),
        })
    return rows


def _parameter_sweep(events):
    """Độ nhạy của phần dân số giả còn lại theo hệ số do tác giả chọn."""
    fake = [event for event in events if event.is_fake]
    raw_population = sum(event.n_trapped for event in fake)
    rows = []
    for b1 in (0.7, 1.4, 2.1):
        for b2 in (0.45, 0.90, 1.35):
            confidences = []
            effective = 0.0
            for event in fake:
                z = (
                    C.confidence.b0
                    + b1 * float(event.has_image)
                    + b2 * math.log1p(event.n_corrob)
                )
                confidence = 1.0 / (1.0 + math.exp(-z))
                confidences.append(confidence)
                effective += event.n_trapped * confidence
            retained = effective / raw_population if raw_population else 0.0
            rows.append({
                "b1_image": b1,
                "b2_corrob": b2,
                "mean_Ci_fake": round(float(np.mean(confidences)), 4),
                "fake_population_retained_pct": round(100.0 * retained, 2),
                "fake_population_reduced_pct": round(100.0 * (1.0 - retained), 2),
            })
    return rows


def _campaign_summary(events):
    campaign = [event for event in events if event.note == "fake_campaign"]
    other_fake = [
        event for event in events
        if event.is_fake and event.note != "fake_campaign"
    ]
    real = [event for event in events if not event.is_fake]

    def _summary(name, values):
        return {
            "scenario": name,
            "n": len(values),
            "mean_n_corrob": round(float(np.mean([e.n_corrob for e in values])), 2),
            "mean_Ci": round(float(np.mean([e.confidence for e in values])), 4),
            "mean_fake_score_1_minus_Ci": round(
                float(np.mean([1.0 - e.confidence for e in values])), 4
            ),
        }

    return [
        _summary("fake_campaign", campaign),
        _summary("other_fake", other_fake),
        _summary("real_reports", real),
    ]


def main():
    events = prepared_events()
    feature_rows = _feature_rows(events)
    conditional_rows = _conditional_density_rows(events)
    sweep_rows = _parameter_sweep(events)
    campaign_rows = _campaign_summary(events)

    print_table("Exp8 — C_i cạnh từng đặc trưng đơn", feature_rows)
    print_table("Exp8 — AUC/AP có điều kiện theo mật độ n_corrob", conditional_rows)
    print_table("Exp8 — độ nhạy theo (b1,b2)", sweep_rows)
    print_table("Exp8 — failure mode: chiến dịch tin giả", campaign_rows)

    combined = next(
        row for row in feature_rows
        if row["feature"] == "1-C_i (combined heuristic)"
    )
    strongest = max(
        (row for row in feature_rows if row["auc"] is not None),
        key=lambda row: row["auc"],
    )
    output = [{
        "marginal_detector": combined,
        "single_features": feature_rows,
        "conditional_by_density": conditional_rows,
        "fake_campaign": campaign_rows,
        "parameter_sweep": sweep_rows,
        "strongest_feature_by_auc": strongest["feature"],
        "interpretation": (
            "C_i is an interpretable weighting convention, not a validated "
            "stand-alone misinformation detector."
        ),
    }]
    save_table("exp8_confidence_detector.json", output)
    save_table("exp8_confidence_parameter_sweep.json", sweep_rows)
    print("\n[saved] exp8_confidence_*.json -> results/tables/")


if __name__ == "__main__":
    main()
