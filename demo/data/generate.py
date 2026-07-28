"""Sinh bộ dữ liệu synthetic mô phỏng báo cáo cứu hộ bão lũ Miền Trung VN.

Vùng địa lý: Huế – Quảng Trị – Quảng Nam – Đà Nẵng (15.7–17.1°N, 107.0–108.6°E).

VÒNG 17 — THIẾT KẾ LẠI ĐỘ KHÓ (phản biện §2, §3, §4).
Generator cũ tự bảo đảm cho gating thắng: (a) `assert_gt_separable(min_sep=2000m)`
buộc mọi nhãn cách nhau > 2 km nên MỌI ngưỡng khoảng cách 1–2 km đều tách đúng;
(b) tin giả luôn đứng cô lập (`n_corrob = 0`) nên C_i chỉ đo "điểm có nằm trong
vùng dày đặc hay không" ≡ trùng biến đích; (c) spread và mật độ đồng đều nên
DBSCAN/HDBSCAN không gặp khó thật. Ba điều này khiến kết quả là ARTIFACT của
dữ liệu, không phải của phương pháp.

Thiết kế mới, ba trục khó:
  1. NHÓM CHỒNG LẤN KHÔNG GIAN, TÁCH ĐƯỢC BẰNG NGỮ CẢNH. Ba cặp nhóm có tâm cách
     nhau < 800 m (dưới sigma_geo = 700 m) nên địa lý KHÔNG tách được; nhưng mang
     flood/urgency tương phản mạnh (vd F≈0.85 "vỡ đê" vs F≈0.25 "ngập mưa") nên
     CHỈ S_context tách được. Đây là chỗ để §2 được trả lời thay vì thừa nhận.
  2. CẶP CÙNG VỊ TRÍ, KHÁC THỜI GIAN. Hai nhóm chồng tâm nhưng lệch ~3.5 h
     (≫ tau_temp = 45 min) để S_temp cũng có việc — trước đây beta chỉ được
     chứng minh trên đúng một cặp.
  3. MẬT ĐỘ & SPREAD KHÔNG ĐỒNG ĐỀU + NHÃN MULTIMODAL. spread ∈ {120..900} m,
     số điểm/nhóm ∈ {8..70}; một sự kiện vật lý có thể có HAI ổ điểm cách nhau
     (multimodal), nên KHÔNG ngưỡng khoảng cách nào đạt ARI = 1 — đó là định
     nghĩa của dataset đo được phương pháp.

Tin giả (phản biện §4): ~60% tin giả nằm TRONG nhóm thật (cùng vị trí + cửa sổ
thời gian) nên có `n_corrob` cao như tin thật; has_image chồng lấn (thật ~0.7,
giả ~0.45); và một "chiến dịch tin giả" 4 tin cùng toạ độ/giờ củng cố lẫn nhau —
đây là failure mode đã biết của C_i, phải báo cáo đúng như vậy.

`assert_gt_separable` bị BỎ (thay bằng `inter_group_separation` chỉ GHI LOG,
không raise) — chính assertion đó là thứ bảo đảm cho gating thắng.

Không dùng random không kiểm soát: mọi ngẫu nhiên qua numpy Generator có seed.
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.attributes import Event, haversine_m  # noqa: E402

# Tâm các "ốc đảo" ngập lụt quanh Miền Trung (lat, lng, tên tỉnh).
# Giữ 6 tâm để tương thích import của exp1; các nhóm mới neo quanh chúng.
CLUSTER_CENTERS = [
    (16.4637, 107.5909, "Thừa Thiên Huế"),   # 0 TP Huế
    (16.7500, 107.1900, "Quảng Trị"),         # 1 Đông Hà
    (15.8801, 108.3380, "Quảng Nam"),         # 2 Hội An
    (16.0678, 108.2208, "Đà Nẵng"),           # 3 Đà Nẵng
    (16.3500, 107.7000, "Thừa Thiên Huế"),    # 4 Phú Vang
    (17.0000, 107.0500, "Quảng Trị"),         # 5 Vĩnh Linh
]

BASE_TIME = datetime(2026, 10, 15, 8, 0, 0, tzinfo=timezone.utc)


def _offset(lat: float, lng: float, north_m: float, east_m: float) -> tuple[float, float]:
    """Dịch tọa độ theo mét (bắc dương, đông dương) — xấp xỉ phẳng cục bộ."""
    dlat = north_m / 111_000.0
    dlng = east_m / (111_000.0 * math.cos(math.radians(lat)))
    return lat + dlat, lng + dlng


def _jitter_coord(rng, lat, lng, spread_m):
    """Dịch tọa độ ngẫu nhiên trong bán kính ~spread_m mét (Gaussian 2D)."""
    dlat = rng.normal(0, spread_m / 111_000.0)
    dlng = rng.normal(0, spread_m / (111_000.0 * np.cos(np.radians(lat))))
    return lat + dlat, lng + dlng


# ---------------------------------------------------------------------------
# ĐẶC TẢ NHÓM (mỗi nhóm = một sự kiện vật lý = một nhãn ground-truth).
#
# Trường:
#   gt        : nhãn ground-truth (>=0). Hai blob CÙNG gt = sự kiện multimodal.
#   anchor    : chỉ số CLUSTER_CENTERS làm gốc.
#   north/east: dịch tâm nhóm so với anchor (mét).
#   n         : số điểm (mật độ KHÔNG đồng đều giữa các nhóm).
#   spread_m  : độ rải nội nhóm (KHÔNG đồng đều — thử thách HDBSCAN/DBSCAN).
#   flood/urg : ngữ cảnh trung bình (đuôi tương phản giữa các cặp chồng lấn).
#   t_off_min : dịch thời gian tâm nhóm so với BASE_TIME (phút).
#   tag       : nhãn mô tả.
#
# BA CẶP CHỒNG LẤN KHÔNG GIAN (tâm cách < 800 m, ngữ cảnh tương phản):
#   (0,1) @ Huế:   vỡ đê F0.85 E0.90  vs  ngập mưa F0.25 E0.30
#   (2,3) @ Hội An:vỡ đê F0.88 E0.85  vs  ngập mưa F0.22 E0.28
#   (4,5) @ Đà Nẵng:vỡ đê F0.82 E0.88 vs  ngập mưa F0.28 E0.32
# CẶP CÙNG VỊ TRÍ KHÁC THỜI GIAN (chồng tâm, lệch 3.5 h, ngữ cảnh giống nhau):
#   (6,7) @ Đông Hà: cả hai F0.6 E0.6, t = 0 vs 210 min  -> chỉ S_temp tách.
# NHÃN MULTIMODAL (một sự kiện, hai ổ điểm cách ~1.4 km):
#   gt 8 có hai blob (8a, 8b) -> không ngưỡng khoảng cách nào gộp đúng thành 1.
# CÁC NHÓM ĐƠN mật độ/spread biến thiên mạnh: gt 9..12.
# ---------------------------------------------------------------------------
_GROUP_SPECS = [
    # --- cặp chồng lấn 1 @ Huế (anchor 0), tâm cách ~640 m ---
    dict(gt=0, anchor=0, north=+320, east=0,    n=45, spread_m=180,
         flood=0.85, urg=0.90, t_off=0,   tag="vỡ đê Huế (ngập nóc)"),
    dict(gt=1, anchor=0, north=-320, east=0,    n=38, spread_m=220,
         flood=0.25, urg=0.30, t_off=8,   tag="ngập mưa Huế (nhẹ)"),
    # --- cặp chồng lấn 2 @ Hội An (anchor 2), tâm cách ~700 m ---
    dict(gt=2, anchor=2, north=0,    east=+350, n=55, spread_m=250,
         flood=0.88, urg=0.85, t_off=15,  tag="vỡ đê Hội An"),
    dict(gt=3, anchor=2, north=0,    east=-350, n=20, spread_m=150,
         flood=0.22, urg=0.28, t_off=20,  tag="ngập mưa Hội An"),
    # --- cặp chồng lấn 3 @ Đà Nẵng (anchor 3), tâm cách ~560 m ---
    dict(gt=4, anchor=3, north=+280, east=+140, n=35, spread_m=400,
         flood=0.82, urg=0.88, t_off=25,  tag="vỡ đê Đà Nẵng"),
    dict(gt=5, anchor=3, north=-280, east=-140, n=12, spread_m=120,
         flood=0.28, urg=0.32, t_off=30,  tag="ngập mưa Đà Nẵng"),
    # --- cặp cùng vị trí khác thời gian @ Đông Hà (anchor 1) ---
    dict(gt=6, anchor=1, north=0,    east=0,    n=28, spread_m=300,
         flood=0.60, urg=0.62, t_off=0,   tag="Đông Hà đợt 1 (sáng)"),
    dict(gt=7, anchor=1, north=+40,  east=+40,  n=24, spread_m=300,
         flood=0.58, urg=0.60, t_off=210, tag="Đông Hà đợt 2 (chiều, +3.5h)"),
    # --- nhãn multimodal gt=8: hai ổ điểm cách ~1.4 km @ Phú Vang (anchor 4) ---
    dict(gt=8, anchor=4, north=+700, east=0,    n=18, spread_m=200,
         flood=0.70, urg=0.68, t_off=40,  tag="tuyến ngập Phú Vang (ổ bắc)"),
    dict(gt=8, anchor=4, north=-700, east=0,    n=16, spread_m=200,
         flood=0.72, urg=0.70, t_off=48,  tag="tuyến ngập Phú Vang (ổ nam)"),
    # --- nhóm đơn, mật độ & spread biến thiên mạnh ---
    dict(gt=9,  anchor=5, north=0,    east=0,    n=70, spread_m=600,
         flood=0.55, urg=0.50, t_off=55,  tag="Vĩnh Linh (đông, rải rộng)"),
    dict(gt=10, anchor=5, north=+2600, east=+1800, n=8,  spread_m=120,
         flood=0.45, urg=0.48, t_off=60,  tag="Vĩnh Linh (nhỏ, đặc)"),
    dict(gt=11, anchor=0, north=+3200, east=+2600, n=30, spread_m=900,
         flood=0.50, urg=0.52, t_off=70,  tag="ngoại vi Huế (rất rải)"),
    dict(gt=12, anchor=3, north=+3000, east=-2400, n=22, spread_m=250,
         flood=0.65, urg=0.60, t_off=80,  tag="ngoại vi Đà Nẵng"),
]


def _group_center(spec: dict) -> tuple[float, float, str]:
    clat, clng, prov = CLUSTER_CENTERS[spec["anchor"]]
    lat, lng = _offset(clat, clng, spec["north"], spec["east"])
    return lat, lng, prov


def _perturb_spec(rng, spec: dict, geom_jitter: float) -> dict:
    """Xáo HÌNH HỌC LIÊN NHÓM của một đặc tả theo hạt giống (phản biện §8, điểm 3).

    Đa hạt giống chỉ jitter TOẠ ĐỘ ĐIỂM thì mọi hạt giống dùng lại đúng một bố cục
    liên nhóm: cùng độ chồng lấn, cùng spread, cùng mật độ. Khi đó sd của ARI chỉ
    đo nhiễu trong nhóm, không đo độ bền trước cấu hình khó dễ khác nhau — đúng
    như phản biện chỉ ra.

    `geom_jitter` ∈ [0, 1): hệ số biến thiên tương đối, áp riêng cho từng đại lượng
      - `north`/`east` cùng một hệ số  -> đổi KHOẢNG CÁCH TÂM–TÂM, tức đổi mức
        chồng lấn của các cặp (overlap_ratio hiệu dụng đổi theo hạt giống);
      - `spread_m`                     -> đổi mật độ nội nhóm;
      - `n`                            -> đổi độ lệch mật độ giữa các nhóm.
    `geom_jitter = 0` (mặc định) giữ nguyên đặc tả, nên dataset chính và các tiêu
    chí nghiệm thu của Thí nghiệm 0 KHÔNG đổi.
    """
    if geom_jitter <= 0.0:
        return spec
    lo, hi = 1.0 - geom_jitter, 1.0 + geom_jitter
    s = dict(spec)
    f_pos = float(rng.uniform(lo, hi))          # cùng hệ số cho north/east
    s["north"] = spec["north"] * f_pos
    s["east"] = spec["east"] * f_pos
    s["spread_m"] = spec["spread_m"] * float(rng.uniform(lo, hi))
    s["n"] = max(5, int(round(spec["n"] * float(rng.uniform(lo, hi)))))
    return s


def generate_core(rng, n_per_cluster: int | None = None, spread_m: float | None = None,
                  geom_jitter: float = 0.0) -> list[Event]:
    """Sinh lõi định lượng theo `_GROUP_SPECS`: nhóm chồng lấn + mật độ biến thiên.

    `n_per_cluster` / `spread_m` (tuỳ chọn): nếu truyền vào sẽ GHI ĐÈ mật độ/spread
    của MỌI nhóm (dùng cho exp scaling cần điều khiển kích thước); mặc định None để
    dùng đúng phân bố không đồng đều trong đặc tả — đây mới là chế độ "khó".

    `geom_jitter`: xáo hình học liên nhóm theo hạt giống — xem `_perturb_spec`.
    """
    events: list[Event] = []
    eid = 0
    for base_spec in _GROUP_SPECS:
        spec = _perturb_spec(rng, base_spec, geom_jitter)
        clat, clng, prov = _group_center(spec)
        n = n_per_cluster if n_per_cluster is not None else spec["n"]
        sp = spread_m if spread_m is not None else spec["spread_m"]
        base_flood = spec["flood"]
        base_urg = spec["urg"]
        t_center = BASE_TIME + timedelta(minutes=float(spec["t_off"]))
        for _ in range(n):
            lat, lng = _jitter_coord(rng, clat, clng, sp)
            # thời gian rải quanh tâm nhóm ±20 min (nhỏ hơn tau_temp nhiều)
            t = t_center + timedelta(minutes=float(rng.uniform(-20, 20)))
            # độ lệch ngữ cảnh nội nhóm ĐỦ RỘNG để phân bố các nhóm chồng lấn
            # nhau một phần — nếu quá hẹp thì (F,E) thành hàm của nhãn.
            flood = float(np.clip(rng.normal(base_flood, 0.10), 0, 1))
            urg = float(np.clip(rng.normal(base_urg, 0.10), 0, 1))
            n_trapped = int(max(1, rng.poisson(4)))
            vuln = 0.0
            if rng.random() < 0.15:
                vuln = float(rng.choice([1.0, 1.5, 2.0]))
            # tin thật có ảnh với xác suất ~0.70 (chồng lấn với tin giả ~0.45)
            has_img = bool(rng.random() < 0.70)
            events.append(
                Event(
                    event_id=f"C{eid:04d}",
                    lat=round(lat, 6),
                    lng=round(lng, 6),
                    created_at=t,
                    flood=round(flood, 3),
                    urgency=round(urg, 3),
                    n_trapped=n_trapped,
                    vulnerability=vuln,
                    has_image=has_img,
                    province=prov,
                    gt_cluster=spec["gt"],
                    note=spec["tag"],
                )
            )
            eid += 1
    return events


def generate_noise(rng, n_noise: int = 60, fake_rate: float = 0.5,
                   fake_image_rate: float = 0.45, in_cluster_frac: float = 0.62,
                   core: list[Event] | None = None) -> list[Event]:
    """Báo cáo nhiễu + tin giả — phần lớn tin giả NẰM TRONG nhóm thật (§4).

    Trước đây tin giả luôn rải rác nên `n_corrob = 0` cho MỌI tin giả, khiến C_i
    chỉ đo mật độ láng giềng ≡ trùng biến đích. Nay:
      - `in_cluster_frac` (~0.62) tin giả được đặt TRONG một nhóm thật ngẫu nhiên
        (cùng vị trí + cửa sổ thời gian) nên có `n_corrob` cao như tin thật;
      - phần còn lại rải rác toàn vùng;
      - `fake_image_rate` ~0.45 (tin thật ~0.70) -> has_image CHỒNG LẤN, không
        đặc trưng đơn nào tách được tin giả.
    `core` (tuỳ chọn): danh sách sự kiện lõi để lấy vị trí đặt tin giả trong cụm.
    """
    events: list[Event] = []
    lat_lo, lat_hi = 15.7, 17.1
    lng_lo, lng_hi = 107.0, 108.6
    core = core or []
    real_core = [e for e in core if e.gt_cluster is not None and e.gt_cluster >= 0]
    for i in range(n_noise):
        is_fake = bool(rng.random() < fake_rate)
        place_in_cluster = is_fake and real_core and (rng.random() < in_cluster_frac)
        if place_in_cluster:
            anchor = real_core[int(rng.integers(0, len(real_core)))]
            lat, lng = _jitter_coord(rng, anchor.lat, anchor.lng, 200.0)
            t = anchor.created_at + timedelta(minutes=float(rng.uniform(-15, 15)))
            prov = anchor.province
            note = "fake_in_cluster"
        else:
            lat = float(rng.uniform(lat_lo, lat_hi))
            lng = float(rng.uniform(lng_lo, lng_hi))
            t = BASE_TIME + timedelta(minutes=float(rng.uniform(0, 180)))
            prov = "N/A"
            note = "fake_report" if is_fake else "noise"
        if is_fake:
            has_img = bool(rng.random() < fake_image_rate)
        else:
            has_img = bool(rng.random() < 0.2)
        events.append(
            Event(
                event_id=f"NZ{i:03d}",
                lat=round(lat, 6),
                lng=round(lng, 6),
                created_at=t,
                flood=round(float(rng.uniform(0, 1)), 3),
                urgency=round(float(rng.uniform(0, 1)), 3),
                n_trapped=int(rng.integers(1, 60)) if is_fake else int(rng.integers(1, 5)),
                vulnerability=0.0,
                has_image=has_img,
                province=prov,
                gt_cluster=-1,
                is_fake=is_fake,
                note=note,
            )
        )
    return events


def generate_fake_campaign(rng, core: list[Event] | None = None,
                           n_campaign: int = 4) -> list[Event]:
    """"Chiến dịch tin giả": n_campaign tin giả CÙNG toạ độ/giờ, củng cố lẫn nhau.

    Đây là failure mode đã biết của C_i: các tin này có `n_corrob` cao (chúng
    corroborate lẫn nhau) nên heuristic mật-độ-láng-giềng cho C_i CAO dù chúng
    là giả. Bài báo phải báo cáo đúng trường hợp này, không giấu (phản biện §4).
    Đặt cạnh một nhóm thật để càng khó phân biệt.
    """
    core = core or []
    real_core = [e for e in core if e.gt_cluster is not None and e.gt_cluster >= 0]
    if real_core:
        anchor = real_core[int(rng.integers(0, len(real_core)))]
        base_lat, base_lng, prov = anchor.lat, anchor.lng, anchor.province
        t0 = anchor.created_at
    else:
        base_lat, base_lng, prov = 16.30, 107.90, "N/A"
        t0 = BASE_TIME + timedelta(minutes=90)
    events: list[Event] = []
    for k in range(n_campaign):
        lat, lng = _jitter_coord(rng, base_lat, base_lng, 60.0)
        events.append(
            Event(
                event_id=f"FC{k:02d}",
                lat=round(lat, 6),
                lng=round(lng, 6),
                created_at=t0 + timedelta(minutes=float(rng.uniform(-5, 5))),
                flood=round(float(np.clip(rng.normal(0.9, 0.05), 0, 1)), 3),
                urgency=round(float(np.clip(rng.normal(0.9, 0.05), 0, 1)), 3),
                n_trapped=int(rng.integers(20, 80)),
                vulnerability=0.0,
                has_image=bool(rng.random() < 0.5),
                province=prov,
                gt_cluster=-1,
                is_fake=True,
                note="fake_campaign",
            )
        )
    return events


def narrative_scenarios(rng=None, jitter_m: float = 40.0) -> list[Event]:
    """Tương thích ngược: các nhóm minh hoạ nay ĐÃ được hợp nhất vào `_GROUP_SPECS`
    (cặp chồng lấn = ca S5 cũ nhưng khó hơn; cặp thời gian = S1/S-temp).

    Giữ hàm để `make_events`/exp cũ gọi được; trả danh sách RỖNG vì mọi cấu trúc
    kịch bản đã nằm trong lõi. Tham số được nhận vào cho tương thích chữ ký.
    """
    del rng, jitter_m
    return []


def inter_group_separation(events: list[Event]) -> dict:
    """GHI LOG khoảng cách liên nhóm nhỏ nhất — KHÔNG assert (thay assert cũ).

    Phản biện §3: `assert_gt_separable(min_sep=2000m)` chính là thứ bảo đảm cho
    mọi ngưỡng khoảng cách thắng. Bỏ hẳn assertion; thay bằng đo và ghi lại để
    bài báo trích đúng: có bao nhiêu cặp nhãn có tâm gần hơn sigma_geo (700 m),
    và khoảng cách tâm–tâm nhỏ nhất giữa hai nhãn khác nhau là bao nhiêu.
    """
    labels = sorted({e.gt_cluster for e in events
                     if e.gt_cluster is not None and e.gt_cluster >= 0})

    def centroid(gt: int) -> tuple[float, float]:
        g = [e for e in events if e.gt_cluster == gt]
        return (sum(e.lat for e in g) / len(g), sum(e.lng for e in g) / len(g))

    cens = {g: centroid(g) for g in labels}
    min_pair = None
    n_below_sigma = 0
    n_below_800 = 0
    for i, ga in enumerate(labels):
        for gb in labels[i + 1:]:
            d = haversine_m(*cens[ga], *cens[gb])
            if d < 700.0:
                n_below_sigma += 1
            if d < 800.0:
                n_below_800 += 1
            if min_pair is None or d < min_pair[2]:
                min_pair = (ga, gb, d)
    overlap_pairs = {}
    for ga, gb in ((0, 1), (2, 3), (4, 5)):
        overlap_pairs[f"{ga}-{gb}"] = round(
            haversine_m(*cens[ga], *cens[gb]), 1
        )
    label_sizes = {
        gt: sum(1 for e in events if e.gt_cluster == gt) for gt in labels
    }
    return {
        "n_gt_labels": len(labels),
        "min_inter_centroid_m": round(min_pair[2], 1) if min_pair else None,
        "closest_label_pair": [min_pair[0], min_pair[1]] if min_pair else None,
        "n_label_pairs_below_sigma_geo": n_below_sigma,
        "n_label_pairs_below_800m": n_below_800,
        "spatial_overlap_pair_centroid_m": overlap_pairs,
        "gt_event_size_min": min(label_sizes.values()) if label_sizes else None,
        "gt_event_size_max": max(label_sizes.values()) if label_sizes else None,
        "source_blob_spread_m_min": min(s["spread_m"] for s in _GROUP_SPECS),
        "source_blob_spread_m_max": max(s["spread_m"] for s in _GROUP_SPECS),
        "same_location_time_gap_h": 3.5,
    }


def event_to_dict(ev: Event) -> dict:
    d = asdict(ev)
    d["created_at"] = ev.created_at.isoformat()
    return d


def make_events(seed: int = 42, n_per_cluster: int | None = None, n_noise: int = 60,
                jitter_narrative: bool = True, geom_jitter: float = 0.0) -> list[Event]:
    """Sinh danh sách Event TRONG BỘ NHỚ (không ghi file).

    `n_per_cluster` mặc định None = dùng mật độ không đồng đều trong đặc tả (chế
    độ khó). Truyền số cụ thể để ép mọi nhóm cùng kích thước (exp scaling).

    `geom_jitter` > 0: mỗi hạt giống sinh lại CẢ hình học liên nhóm (mức chồng lấn,
    spread, mật độ), không chỉ jitter điểm — dùng cho Thí nghiệm 12.
    """
    del jitter_narrative  # kịch bản đã hợp nhất vào lõi; giữ tham số cho tương thích
    rng = np.random.default_rng(seed)
    core = generate_core(rng, n_per_cluster=n_per_cluster, geom_jitter=geom_jitter)
    noise = generate_noise(rng, n_noise=n_noise, core=core)
    campaign = generate_fake_campaign(rng, core=core)
    return core + noise + campaign


def build_dataset(seed: int = 42, n_per_cluster: int | None = None,
                  n_noise: int = 60) -> dict:
    rng = np.random.default_rng(seed)
    core = generate_core(rng, n_per_cluster=n_per_cluster)
    noise = generate_noise(rng, n_noise=n_noise, core=core)
    campaign = generate_fake_campaign(rng, core=core)
    all_events = core + noise + campaign
    sep = inter_group_separation(all_events)

    gt_labels = sorted({e.gt_cluster for e in all_events if e.gt_cluster is not None
                        and e.gt_cluster >= 0})
    n_fake = sum(1 for e in all_events if e.is_fake)
    n_fake_in_cluster = sum(1 for e in all_events
                            if e.is_fake and e.note in ("fake_in_cluster", "fake_campaign"))
    return {
        "meta": {
            "seed": seed,
            "region": "Central Vietnam (Hue - Quang Tri - Quang Nam - Da Nang)",
            "bbox": "15.7-17.1N, 107.0-108.6E",
            "base_time": BASE_TIME.isoformat(),
            "n_core": len(core),
            "n_noise": len(noise),
            "n_campaign": len(campaign),
            "n_narrative": 0,
            "n_total": len(all_events),
            "n_gt_clusters": len(gt_labels),
            "gt_labels": gt_labels,
            "n_fake": n_fake,
            "n_fake_with_image": sum(1 for e in all_events if e.is_fake and e.has_image),
            "n_fake_in_cluster": n_fake_in_cluster,
            "frac_fake_in_cluster": round(n_fake_in_cluster / n_fake, 3) if n_fake else 0.0,
            "n_multimodal_labels": 1,   # gt=8 có hai ổ điểm
            **sep,
        },
        "events": [event_to_dict(e) for e in all_events],
    }


def load_events(path: str | Path) -> list[Event]:
    """Đọc dataset JSON -> list[Event]."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    events = []
    for d in data["events"]:
        d = dict(d)
        d["created_at"] = datetime.fromisoformat(d["created_at"])
        d.pop("confidence", None)
        events.append(Event(**d))
    return events


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent
    dataset = build_dataset()
    out_path = out_dir / "dataset.json"
    out_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    sealed_path = out_dir / "dataset-v3.json"
    sealed_path.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    m = dataset["meta"]
    print(f"Wrote {m['n_total']} events -> {out_path} + {sealed_path}")
    print(f"  core={m['n_core']} noise={m['n_noise']} campaign={m['n_campaign']}")
    print(f"  nhãn GT={m['n_gt_clusters']} {m['gt_labels']}")
    print(f"  tin giả={m['n_fake']} (có ảnh: {m['n_fake_with_image']}, "
          f"trong cụm: {m['n_fake_in_cluster']} = {m['frac_fake_in_cluster']:.0%})")
    print(f"  cặp nhãn có tâm < sigma_geo(700m): {m['n_label_pairs_below_sigma_geo']}")
    print(f"  cặp nhãn có tâm < 800m: {m['n_label_pairs_below_800m']}")
    print(f"  khoảng cách tâm–tâm nhỏ nhất giữa hai nhãn: {m['min_inter_centroid_m']} m "
          f"(cặp {m['closest_label_pair']})")
