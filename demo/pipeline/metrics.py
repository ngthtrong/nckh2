"""Chỉ số đánh giá chất lượng cụm so với ground-truth."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    adjusted_rand_score,
    normalized_mutual_info_score,
)

from .attributes import Event, haversine_m


def cluster_quality(labels: list[int], gt: list[int]) -> dict[str, float]:
    """ARI và NMI so với nhãn ground-truth (bỏ qua các điểm nhiễu gt = -1)."""
    pred = np.array(labels)
    truth = np.array(gt)
    mask = truth >= 0
    if mask.sum() == 0:
        return {"ari": 0.0, "nmi": 0.0, "n_eval": 0}
    return {
        "ari": round(float(adjusted_rand_score(truth[mask], pred[mask])), 4),
        "nmi": round(float(normalized_mutual_info_score(truth[mask], pred[mask])), 4),
        "n_eval": int(mask.sum()),
    }


def geographic_spread(events: list[Event], labels: list[int]) -> dict[str, float]:
    """Đường kính địa lý trung bình của cụm (km) — cụm gắn kết thì nhỏ."""
    groups: dict[int, list[Event]] = {}
    for ev, lab in zip(events, labels):
        groups.setdefault(lab, []).append(ev)

    diameters = []
    for members in groups.values():
        if len(members) < 2:
            diameters.append(0.0)
            continue
        max_d = 0.0
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                d = haversine_m(
                    members[i].lat, members[i].lng, members[j].lat, members[j].lng
                )
                max_d = max(max_d, d)
        diameters.append(max_d / 1000.0)
    return {
        "mean_diameter_km": round(float(np.mean(diameters)), 4) if diameters else 0.0,
        "max_diameter_km": round(float(np.max(diameters)), 4) if diameters else 0.0,
        "n_clusters": len(groups),
    }
