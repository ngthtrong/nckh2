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


def noise_handling(
    labels: list[int], gt: list[int], noise_label: int | None = -1
) -> dict[str, float]:
    """Cách phương pháp XỬ LÝ nhiễu — thông tin mà ARI/NMI che mất.

    `cluster_quality` chỉ chấm trên các điểm có nhãn (gt >= 0), nên một phương
    pháp hút hết điểm nhiễu (gt = -1) vào các cụm thật vẫn có thể đạt ARI = 1,0.
    Đó là ưu thế giả: về vận hành, nhiễu bị hút vào cụm sẽ kéo giãn cụm và làm
    sai lệch toạ độ điều phối.

    THÙNG NHIỄU (`noise_label`, mặc định -1): DBSCAN/HDBSCAN gán nhãn -1 cho
    "KHÔNG thuộc cụm nào". Nhóm đó KHÔNG phải một cụm, nên không được tính là
    nơi nhiễu "bị hấp thụ" — nếu tính, một phương pháp ném cả nhiễu lẫn vài
    điểm thật vào thùng -1 sẽ bị báo cáo sai thành "hấp thụ 100% nhiễu" trong
    khi thực tế nó không hấp thụ điểm nào. Đặt `noise_label=None` cho các thuật
    toán không sinh nhãn nhiễu (Louvain, Leiden, K-Means, Spectral,
    Agglomerative) — với chúng mọi nhãn đều là cụm thật.

    Trả về:
      - `noise_absorbed_pct`: % điểm nhiễu bị đặt vào một CỤM THẬT có ít nhất
        một điểm có nhãn (càng thấp càng tốt).
      - `contaminated_clusters`: số cụm thật chứa lẫn cả điểm thật và điểm nhiễu.
      - `purity_labeled`: tỉ lệ điểm trong các cụm "thật" thực sự có nhãn.
      - `n_unclustered`: số điểm nằm trong thùng nhiễu (chưa được gán cụm nào).
      - `labeled_dropped_to_noise`: số điểm CÓ NHÃN bị đẩy vào thùng nhiễu — lỗi
        đối ngẫu của hấp thụ. Một phương pháp có thể đạt hấp-thụ-nhiễu 0% bằng
        cách từ chối phân cụm phần lớn dữ liệu; cột này phơi bày cái giá đó.
    """
    groups: dict[int, list[int]] = {}
    for lab, g in zip(labels, gt):
        groups.setdefault(lab, []).append(g)

    noise_bin = groups.pop(noise_label, []) if noise_label is not None else []

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
        "n_unclustered": len(noise_bin),
        "labeled_dropped_to_noise": sum(1 for g in noise_bin if g >= 0),
    }


def geographic_spread(
    events: list[Event],
    labels: list[int],
    noise_label: int | None = -1,
    gt_labels: list[int] | None = None,
) -> dict[str, float]:
    """Đường kính địa lý của cụm (km) — cụm gắn kết thì nhỏ.

    QUY ƯỚC BÁO CÁO CHÍNH (áp dụng NHƯ NHAU cho mọi phương pháp, xem Mục 5 của
    bài): chỉ số hình học chính là các cột `*_labeled`, tính TRÊN CÁC CỤM CHỨA ÍT
    NHẤT MỘT ĐIỂM CÓ NHÃN GROUND-TRUTH (gt >= 0). Lý do: các cụm gồm TOÀN điểm
    nhiễu không phải là nhóm mà phương pháp được yêu cầu phục hồi, nhưng chúng
    trải rộng khắp vùng (hàng trăm km) nên chi phối trung bình và làm một phương
    pháp bị đọc sai thành "trải cả tỉnh". Ví dụ đo được: HDBSCAN 20 cụm = 14 cụm
    có nhãn (TB 6,46 km) + 6 cụm toàn nhiễu (TB 147,22 km) => trung bình gộp
    48,69 km. Con số 48,69 km là artifact của quy ước đo, không phải chất lượng
    hình học. Chỉ số gộp và các cụm-toàn-nhiễu được báo cáo RIÊNG ở cột phụ.

    Cần truyền `gt_labels` (cùng thứ tự với `events`) để có các cột `*_labeled`;
    nếu không truyền, các cột đó bằng None và chỉ còn quy ước gộp cũ.

    Các cột gộp (giữ để tương thích ngược, đọc như tham khảo):
      - `mean_diameter_km`         : mọi cụm, singleton tính là 0 — THIÊN VỊ phân
        hoạch nhiều singleton, không dùng để so sánh.
      - `max_diameter_km`          : trường hợp xấu nhất.
      - `mean_diameter_km_multi`   : chỉ cụm có >= 2 thành viên.
      - `mean_diameter_km_weighted`: trung bình có trọng số theo số điểm.

    THÙNG NHIỄU (`noise_label`, mặc định -1): nhãn -1 của DBSCAN/HDBSCAN nghĩa là
    "không thuộc cụm nào", nên KHÔNG được tính như một cụm. Nếu tính, thùng nhiễu
    gom các điểm rải khắp vùng sẽ tạo ra một "cụm" đường kính hàng trăm km và
    chi phối cả `max_diameter_km` lẫn `mean_diameter_km_multi` — một artifact đo
    lường, không phải nhược điểm thật của thuật toán. Số điểm trong thùng được
    báo cáo riêng qua `n_unclustered`. Lưu ý: thùng nhiễu (nhãn -1 do thuật toán
    gán) khác với cụm-toàn-nhiễu (một cụm THẬT nhưng mọi thành viên có gt < 0).
    """
    groups: dict[int, list[Event]] = {}
    gt_groups: dict[int, list[int]] = {}
    gt_seq = list(gt_labels) if gt_labels is not None else [None] * len(events)
    for ev, lab, g in zip(events, labels, gt_seq):
        groups.setdefault(lab, []).append(ev)
        gt_groups.setdefault(lab, []).append(g)

    noise_bin = groups.pop(noise_label, []) if noise_label is not None else []
    if noise_label is not None:
        gt_groups.pop(noise_label, None)

    def _diameter_km(members: list[Event]) -> float:
        max_d = 0.0
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                d = haversine_m(
                    members[i].lat, members[i].lng, members[j].lat, members[j].lng
                )
                max_d = max(max_d, d)
        return max_d / 1000.0

    diameters = []        # mọi cụm (singleton = 0.0)
    diam_multi = []       # chỉ cụm >= 2 thành viên
    sizes_multi = []      # số điểm tương ứng, cho bản có trọng số
    diam_labeled = []     # cụm chứa >= 1 điểm có nhãn GT
    diam_noise_only = []  # cụm gồm TOÀN điểm nhiễu
    n_singletons = 0
    for lab, members in groups.items():
        diam = 0.0 if len(members) < 2 else _diameter_km(members)
        diameters.append(diam)
        if len(members) < 2:
            n_singletons += 1
        else:
            diam_multi.append(diam)
            sizes_multi.append(len(members))
        if gt_labels is not None:
            has_label = any(g is not None and g >= 0 for g in gt_groups[lab])
            (diam_labeled if has_label else diam_noise_only).append(diam)

    if diam_multi:
        w = np.array(sizes_multi, dtype=float)
        mean_multi = float(np.mean(diam_multi))
        mean_weighted = float(np.average(diam_multi, weights=w))
    else:
        mean_multi = 0.0
        mean_weighted = 0.0

    out: dict[str, float] = {
        "mean_diameter_km": round(float(np.mean(diameters)), 4) if diameters else 0.0,
        "mean_diameter_km_multi": round(mean_multi, 4),
        "mean_diameter_km_weighted": round(mean_weighted, 4),
        "max_diameter_km": round(float(np.max(diameters)), 4) if diameters else 0.0,
        "n_clusters": len(groups),
        "n_singletons": n_singletons,
        "n_clusters_multi": len(diam_multi),
        "n_unclustered": len(noise_bin),
    }
    if gt_labels is None:
        out.update({
            "n_clusters_labeled": None,
            "n_clusters_noise_only": None,
            "mean_diameter_km_labeled": None,
            "max_diameter_km_labeled": None,
            "mean_diameter_km_noise_only": None,
            "frac_labeled_clusters_under_1p5km": None,
        })
        return out

    n_lab_cl = len(diam_labeled)
    out.update({
        "n_clusters_labeled": n_lab_cl,
        "n_clusters_noise_only": len(diam_noise_only),
        "mean_diameter_km_labeled": (
            round(float(np.mean(diam_labeled)), 4) if diam_labeled else 0.0),
        "max_diameter_km_labeled": (
            round(float(np.max(diam_labeled)), 4) if diam_labeled else 0.0),
        "mean_diameter_km_noise_only": (
            round(float(np.mean(diam_noise_only)), 4) if diam_noise_only else 0.0),
        "frac_labeled_clusters_under_1p5km": (
            round(sum(1 for d in diam_labeled if d < 1.5) / n_lab_cl, 4)
            if n_lab_cl else 0.0),
    })
    return out
