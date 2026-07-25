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


def noise_handling(labels: list[int], gt: list[int]) -> dict[str, float]:
    """Cách phương pháp XỬ LÝ nhiễu — thông tin mà ARI/NMI che mất.

    `cluster_quality` chỉ chấm trên các điểm có nhãn (gt >= 0), nên một phương
    pháp hút hết điểm nhiễu (gt = -1) vào các cụm thật vẫn có thể đạt ARI = 1,0.
    Đó là ưu thế giả: về vận hành, nhiễu bị hút vào cụm sẽ kéo giãn cụm và làm
    sai lệch toạ độ điều phối.

    Trả về:
      - `noise_absorbed_pct`: % điểm nhiễu bị đặt vào một cụm có ít nhất một
        điểm thật (càng thấp càng tốt).
      - `contaminated_clusters`: số cụm chứa lẫn cả điểm thật và điểm nhiễu.
      - `purity_labeled`: tỉ lệ điểm trong các cụm "thật" thực sự có nhãn.
    """
    groups: dict[int, list[int]] = {}
    for lab, g in zip(labels, gt):
        groups.setdefault(lab, []).append(g)

    n_noise = sum(1 for g in gt if g < 0)
    absorbed = 0
    contaminated = 0
    n_in_real = 0
    n_labeled_in_real = 0
    for members in groups.values():
        n_lab = sum(1 for g in members if g >= 0)
        n_noi = len(members) - n_lab
        if n_lab > 0:
            n_in_real += len(members)
            n_labeled_in_real += n_lab
            if n_noi > 0:
                absorbed += n_noi
                contaminated += 1
    return {
        "n_noise_points": n_noise,
        "noise_absorbed": absorbed,
        "noise_absorbed_pct": round(100.0 * absorbed / n_noise, 2) if n_noise else 0.0,
        "contaminated_clusters": contaminated,
        "purity_labeled": round(n_labeled_in_real / n_in_real, 4) if n_in_real else 0.0,
    }


def geographic_spread(events: list[Event], labels: list[int]) -> dict[str, float]:
    """Đường kính địa lý của cụm (km) — cụm gắn kết thì nhỏ.

    CẢNH BÁO SO SÁNH: `mean_diameter_km` tính cả cụm singleton với đường kính 0,
    nên một phân hoạch nhiều singleton được "thưởng" một cách giả tạo so với
    phân hoạch ít cụm. Khi so sánh hai phương pháp, dùng:
      - `max_diameter_km`         : trường hợp xấu nhất (so được tuyệt đối)
      - `mean_diameter_km_multi`  : chỉ tính cụm có >= 2 thành viên
      - `mean_diameter_km_weighted`: trung bình có trọng số theo số điểm
    `mean_diameter_km` được giữ để tương thích ngược, chỉ nên đọc như tham khảo.
    """
    groups: dict[int, list[Event]] = {}
    for ev, lab in zip(events, labels):
        groups.setdefault(lab, []).append(ev)

    diameters = []        # mọi cụm (singleton = 0.0)
    diam_multi = []       # chỉ cụm >= 2 thành viên
    sizes_multi = []      # số điểm tương ứng, cho bản có trọng số
    n_singletons = 0
    for members in groups.values():
        if len(members) < 2:
            diameters.append(0.0)
            n_singletons += 1
            continue
        max_d = 0.0
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                d = haversine_m(
                    members[i].lat, members[i].lng, members[j].lat, members[j].lng
                )
                max_d = max(max_d, d)
        diameters.append(max_d / 1000.0)
        diam_multi.append(max_d / 1000.0)
        sizes_multi.append(len(members))

    if diam_multi:
        w = np.array(sizes_multi, dtype=float)
        mean_multi = float(np.mean(diam_multi))
        mean_weighted = float(np.average(diam_multi, weights=w))
    else:
        mean_multi = 0.0
        mean_weighted = 0.0

    return {
        "mean_diameter_km": round(float(np.mean(diameters)), 4) if diameters else 0.0,
        "mean_diameter_km_multi": round(mean_multi, 4),
        "mean_diameter_km_weighted": round(mean_weighted, 4),
        "max_diameter_km": round(float(np.max(diameters)), 4) if diameters else 0.0,
        "n_clusters": len(groups),
        "n_singletons": n_singletons,
        "n_clusters_multi": len(diam_multi),
    }
