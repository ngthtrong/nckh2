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

import argparse
import json
import math
import os
import shutil
import sys
import tempfile
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.attributes import Event, haversine_m  # noqa: E402
from data.schema import (  # noqa: E402
    DEFAULT_SEED_MANIFEST,
    GENERATOR_VERSION,
    SCHEMA_VERSION,
    canonical_json_bytes,
    observable_report,
    registered_seed_splits,
    registered_split_for_seed,
    sha256_bytes,
    validate_candidate_dataset,
)

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


# ---------------------------------------------------------------------------
# REVISION CANDIDATE GENERATOR (schema v4)
#
# The v3 functions above remain available solely for reproducing the historical
# result snapshot. Candidate runs call the functions below and never overwrite
# dataset.json/dataset-v3.json.
# ---------------------------------------------------------------------------

_CANDIDATE_INCIDENT_SPECS = [
    # family, anchor, north/east, reports, spread, flood, urgency, time offset
    dict(family="ordinary", anchor=0, north=-4500, east=-2500, n_reports=18,
         spread_m=260, flood=0.62, urg=0.58, t_off=20),
    dict(family="ordinary", anchor=3, north=-4200, east=3100, n_reports=14,
         spread_m=340, flood=0.48, urg=0.52, t_off=75),
    dict(family="spatial_overlap_context_supportive", anchor=2, north=300, east=80,
         n_reports=24, spread_m=300, flood=0.84, urg=0.86, t_off=35),
    dict(family="spatial_overlap_context_supportive", anchor=2, north=-300, east=-80,
         n_reports=20, spread_m=280, flood=0.25, urg=0.31, t_off=42),
    # Context-adversarial pair: same context/time and overlapping geography.
    dict(family="spatial_overlap_context_adversarial", anchor=3, north=230, east=50,
         n_reports=21, spread_m=250, flood=0.64, urg=0.63, t_off=90),
    dict(family="spatial_overlap_context_adversarial", anchor=3, north=-230, east=-50,
         n_reports=19, spread_m=250, flood=0.63, urg=0.64, t_off=94),
    dict(family="same_location_temporal", anchor=1, north=0, east=0,
         n_reports=17, spread_m=280, flood=0.56, urg=0.61, t_off=0),
    dict(family="same_location_temporal", anchor=1, north=30, east=-30,
         n_reports=17, spread_m=280, flood=0.57, urg=0.60, t_off=210),
    dict(family="distant_context_similar", anchor=0, north=5200, east=-3600,
         n_reports=16, spread_m=420, flood=0.72, urg=0.70, t_off=125),
    dict(family="distant_context_similar", anchor=5, north=-3800, east=4100,
         n_reports=16, spread_m=420, flood=0.72, urg=0.70, t_off=125),
    dict(family="multimodal", anchor=4, north=0, east=0, n_reports=26,
         spread_m=190, flood=0.67, urg=0.65, t_off=155, multimodal=True),
    dict(family="unequal_density", anchor=5, north=2800, east=-2200,
         n_reports=8, spread_m=120, flood=0.45, urg=0.49, t_off=180),
    dict(family="unequal_density", anchor=0, north=7000, east=5000,
         n_reports=42, spread_m=850, flood=0.52, urg=0.55, t_off=185),
    # These generic incidents are sampled independently instead of being
    # curated around any desired relation between geo/time/context.
    dict(family="independent_stress", independent=True),
    dict(family="independent_stress", independent=True),
    dict(family="independent_stress", independent=True),
]

_CANDIDATE_MISSINGNESS_PROBABILITIES = {
    "flood": 0.04,
    "urgency": 0.03,
    "n_trapped": 0.06,
    "vulnerability": 0.08,
}


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _candidate_center(rng: np.random.Generator, spec: dict) -> tuple[float, float, str]:
    if spec.get("independent"):
        return (
            float(rng.uniform(15.7, 17.1)),
            float(rng.uniform(107.0, 108.6)),
            "independent_stress_region",
        )
    lat, lng, province = CLUSTER_CENTERS[spec["anchor"]]
    # Seed-dependent geometry does not depend on a method or performance gate.
    scale = float(rng.uniform(0.85, 1.15))
    north = float(spec["north"]) * scale + float(rng.normal(0, 60))
    east = float(spec["east"]) * scale + float(rng.normal(0, 60))
    center_lat, center_lng = _offset(lat, lng, north, east)
    return center_lat, center_lng, province


def _candidate_incidents(rng: np.random.Generator, seed: int) -> list[dict]:
    incidents: list[dict] = []
    for gt, spec in enumerate(_CANDIDATE_INCIDENT_SPECS):
        center_lat, center_lng, province = _candidate_center(rng, spec)
        independent = bool(spec.get("independent"))
        n_true = int(rng.integers(18, 121))
        vulnerable_share = float(rng.beta(2.0, 5.0))
        v_true = int(np.clip(round(n_true * vulnerable_share), 0, n_true))
        vulnerable_members = sorted(
            int(value)
            for value in (
                rng.choice(n_true, size=v_true, replace=False)
                if v_true
                else np.array([], dtype=int)
            )
        )
        start = BASE_TIME + timedelta(
            minutes=(
                float(rng.uniform(-30, 260))
                if independent
                else float(spec["t_off"]) + float(rng.uniform(-12, 12))
            )
        )
        # Outcome parameters are latent draws. They are not algebraic transforms
        # of reported F/E/N/V or of any priority-score component.
        deadline_min = round(float(rng.uniform(65, 230)), 3)
        service_demand = round(
            max(8.0, 10.0 + 0.22 * n_true + float(rng.normal(0, 4))), 3
        )
        incidents.append({
            "incident_id": f"I{seed:04d}-{gt:02d}",
            "gt_cluster": gt,
            "scenario_family": spec["family"],
            "center_lat": round(center_lat, 7),
            "center_lng": round(center_lng, 7),
            "province": province,
            "start_at": _iso(start),
            "n_true": n_true,
            "v_true": v_true,
            "vulnerable_member_indices": vulnerable_members,
            "deadline_min": deadline_min,
            "service_demand_min": service_demand,
            "harm_curve": {
                "type": "piecewise_linear_lateness",
                "grace_min": round(float(rng.uniform(5, 25)), 3),
                "slope": round(float(rng.uniform(0.4, 1.6)), 4),
                "capacity_penalty": round(float(rng.uniform(0.05, 0.25)), 4),
            },
            "generator_profile": {
                "n_reports": (
                    int(rng.integers(8, 36))
                    if independent
                    else max(
                        6,
                        int(
                            round(
                                spec["n_reports"] * float(rng.uniform(0.85, 1.15))
                            )
                        ),
                    )
                ),
                "spread_m": round(
                    (
                        float(rng.uniform(120, 900))
                        if independent
                        else float(spec["spread_m"]) * float(rng.uniform(0.85, 1.15))
                    ),
                    3,
                ),
                "flood_latent": round(
                    (
                        float(rng.uniform(0, 1))
                        if independent
                        else float(
                            np.clip(spec["flood"] + rng.normal(0, 0.035), 0, 1)
                        )
                    ),
                    4,
                ),
                "urgency_latent": round(
                    (
                        float(rng.uniform(0, 1))
                        if independent
                        else float(
                            np.clip(spec["urg"] + rng.normal(0, 0.035), 0, 1)
                        )
                    ),
                    4,
                ),
                "multimodal": bool(spec.get("multimodal", False)),
            },
        })
    return incidents


def _report_eval(
    incident: dict | None,
    *,
    duplicate_kind: str = "none",
    duplicate_family_id: str | None = None,
    coverage_n: float | None = None,
    coverage_v: float | None = None,
    population_member_indices: list[int] | None = None,
    vulnerable_member_indices: list[int] | None = None,
    is_fake: bool = False,
    adversary: str | None = None,
) -> dict:
    return {
        "incident_id": None if incident is None else incident["incident_id"],
        "gt_cluster": None if incident is None else incident["gt_cluster"],
        "scenario_family": "unlinked" if incident is None else incident["scenario_family"],
        "duplicate_kind": duplicate_kind,
        "duplicate_family_id": duplicate_family_id,
        "coverage_n": coverage_n,
        "coverage_v": coverage_v,
        "population_member_indices": population_member_indices,
        "vulnerable_member_indices": vulnerable_member_indices,
        "is_fake": bool(is_fake),
        "adversary": adversary,
    }


def _apply_candidate_missingness(
    rng: np.random.Generator,
    report: dict,
) -> dict:
    """Apply the preregistered source-missingness process and zero imputation."""
    missing = sorted(
        field
        for field, probability in _CANDIDATE_MISSINGNESS_PROBABILITIES.items()
        if rng.random() < probability
    )
    for field in missing:
        report[field] = 0 if field == "n_trapped" else 0.0
    report["missing_fields"] = missing
    return report


def _base_candidate_reports(
    rng: np.random.Generator, incidents: list[dict], seed: int
) -> list[dict]:
    reports: list[dict] = []
    counter = 0
    for incident in incidents:
        profile = incident["generator_profile"]
        start = datetime.fromisoformat(incident["start_at"])
        for report_index in range(int(profile["n_reports"])):
            if profile["multimodal"]:
                mode_north = 720.0 if report_index % 2 == 0 else -720.0
                mode_lat, mode_lng = _offset(
                    incident["center_lat"], incident["center_lng"], mode_north, 0
                )
            else:
                mode_lat, mode_lng = incident["center_lat"], incident["center_lng"]
            lat, lng = _jitter_coord(rng, mode_lat, mode_lng, profile["spread_m"])
            created_at = start + timedelta(minutes=float(rng.normal(0, 18)))
            flood = float(np.clip(rng.normal(profile["flood_latent"], 0.11), 0, 1))
            urgency = float(np.clip(rng.normal(profile["urgency_latent"], 0.11), 0, 1))

            # Reports observe overlapping subsets of one unique population. Their
            # sums intentionally over-count the incident truth.
            target_coverage = float(rng.beta(2.3, 3.0))
            member_count = int(
                np.clip(round(incident["n_true"] * target_coverage), 1, incident["n_true"])
            )
            population_members = sorted(
                int(value)
                for value in rng.choice(
                    incident["n_true"], size=member_count, replace=False
                )
            )
            vulnerable_members = sorted(
                set(population_members).intersection(
                    incident["vulnerable_member_indices"]
                )
            )
            coverage_n = member_count / incident["n_true"]
            coverage_v = (
                len(vulnerable_members) / incident["v_true"]
                if incident["v_true"] > 0
                else 0.0
            )
            n_reported = int(
                np.clip(
                    round(member_count + rng.normal(0, 2.0)),
                    0,
                    incident["n_true"],
                )
            )
            v_reported = float(
                np.clip(
                    len(vulnerable_members) + rng.normal(0, 0.5),
                    0,
                    max(n_reported, 0),
                )
            )
            source_type = str(
                rng.choice(
                    ["hotline", "citizen_app", "social_media", "field_team"],
                    p=[0.25, 0.35, 0.25, 0.15],
                )
            )
            has_image = bool(
                rng.random()
                < {
                    "hotline": 0.20,
                    "citizen_app": 0.78,
                    "social_media": 0.65,
                    "field_team": 0.85,
                }[source_type]
            )
            report = {
                "event_id": f"R{seed:04d}-{counter:04d}",
                "lat": round(lat, 7),
                "lng": round(lng, 7),
                "created_at": _iso(created_at),
                "flood": round(flood, 4),
                "urgency": round(urgency, 4),
                "n_trapped": n_reported,
                "vulnerability": round(v_reported, 4),
                "has_image": has_image,
                "source_type": source_type,
                "province": incident["province"],
                "note": "synthetic_report",
                "evaluation_only": _report_eval(
                    incident,
                    coverage_n=round(coverage_n, 6),
                    coverage_v=round(coverage_v, 6),
                    population_member_indices=population_members,
                    vulnerable_member_indices=vulnerable_members,
                    is_fake=False,
                ),
            }
            reports.append(_apply_candidate_missingness(rng, report))
            counter += 1
    return reports


def _inject_candidate_duplicates(
    rng: np.random.Generator, reports: list[dict], seed: int
) -> list[dict]:
    by_incident: dict[str, list[dict]] = {}
    for report in reports:
        incident_id = report["evaluation_only"]["incident_id"]
        by_incident.setdefault(str(incident_id), []).append(report)

    additions: list[dict] = []
    serial = 0
    for incident_index, (incident_id, rows) in enumerate(sorted(by_incident.items())):
        if len(rows) < 3:
            continue
        if incident_index % 2 == 0:
            original = rows[0]
            family_id = f"DX-{seed}-{incident_index}"
            original["evaluation_only"]["duplicate_kind"] = "exact"
            original["evaluation_only"]["duplicate_family_id"] = family_id
            duplicate = deepcopy(original)
            duplicate["event_id"] = f"DX{seed:04d}-{serial:03d}"
            additions.append(duplicate)
            serial += 1
        else:
            original = rows[1]
            family_id = f"DN-{seed}-{incident_index}"
            original["evaluation_only"]["duplicate_kind"] = "near"
            original["evaluation_only"]["duplicate_family_id"] = family_id
            duplicate = deepcopy(original)
            duplicate["event_id"] = f"DN{seed:04d}-{serial:03d}"
            duplicate["lat"], duplicate["lng"] = (
                round(value, 7)
                for value in _offset(
                    duplicate["lat"],
                    duplicate["lng"],
                    float(rng.uniform(-30, 30)),
                    float(rng.uniform(-30, 30)),
                )
            )
            shifted = datetime.fromisoformat(duplicate["created_at"]) + timedelta(
                minutes=float(rng.uniform(-4, 4))
            )
            duplicate["created_at"] = _iso(shifted)
            duplicate["flood"] = round(
                float(np.clip(duplicate["flood"] + rng.normal(0, 0.025), 0, 1)), 4
            )
            duplicate["urgency"] = round(
                float(np.clip(duplicate["urgency"] + rng.normal(0, 0.025), 0, 1)), 4
            )
            duplicate["n_trapped"] = max(
                0, int(duplicate["n_trapped"] + rng.integers(-3, 4))
            )
            duplicate["vulnerability"] = round(
                max(0.0, duplicate["vulnerability"] + float(rng.normal(0, 0.35))), 4
            )
            for field, original_value in (
                ("flood", 0.0),
                ("urgency", 0.0),
                ("n_trapped", 0),
                ("vulnerability", 0.0),
            ):
                if field in duplicate["missing_fields"]:
                    duplicate[field] = original_value
            additions.append(duplicate)
            serial += 1
    return reports + additions


def _candidate_unlinked_reports(
    rng: np.random.Generator, incidents: list[dict], seed: int
) -> list[dict]:
    reports: list[dict] = []
    counter = 0

    # Method-independent background/noise reports.
    for _ in range(32):
        fake = bool(rng.random() < 0.35)
        report = {
            "event_id": f"U{seed:04d}-{counter:03d}",
            "lat": round(float(rng.uniform(15.7, 17.1)), 7),
            "lng": round(float(rng.uniform(107.0, 108.6)), 7),
            "created_at": _iso(
                BASE_TIME + timedelta(minutes=float(rng.uniform(-30, 260)))
            ),
            "flood": round(float(rng.uniform(0, 1)), 4),
            "urgency": round(float(rng.uniform(0, 1)), 4),
            "n_trapped": int(rng.integers(0, 65 if fake else 8)),
            "vulnerability": round(float(rng.uniform(0, 15 if fake else 3)), 4),
            "has_image": bool(rng.random() < (0.45 if fake else 0.30)),
            "source_type": "anonymous" if fake else "hotline",
            "province": "N/A",
            "note": "synthetic_report",
            "evaluation_only": _report_eval(
                None,
                is_fake=fake,
                adversary="background_fake" if fake else None,
            ),
        }
        reports.append(_apply_candidate_missingness(rng, report))
        counter += 1

    # Four low-confidence, single-field inflation cases. They are deliberately
    # outside corroboration windows and have no image.
    target = incidents[0]
    inflation = {
        "N": {"n_trapped": 500},
        "V": {"vulnerability": 120.0},
        "F": {"flood": 1.0},
        "E": {"urgency": 1.0},
    }
    for offset_index, (field, patch) in enumerate(inflation.items()):
        lat, lng = _offset(
            target["center_lat"],
            target["center_lng"],
            1500 + 700 * offset_index,
            650 * offset_index,
        )
        report = {
            "event_id": f"AL{seed:04d}-{field}",
            "lat": round(lat, 7),
            "lng": round(lng, 7),
            "created_at": _iso(
                datetime.fromisoformat(target["start_at"])
                + timedelta(minutes=100 + 75 * offset_index)
            ),
            "flood": 0.25,
            "urgency": 0.25,
            "n_trapped": 2,
            "vulnerability": 0.0,
            "has_image": False,
            "source_type": "anonymous",
            "province": target["province"],
            "note": "synthetic_report",
            "missing_fields": [],
            "evaluation_only": _report_eval(
                None,
                is_fake=True,
                adversary=f"low_conf_inflate_{field}",
            ),
        }
        report.update(patch)
        reports.append(report)

    # Coordinated campaign: clustered, image-rich, mutually corroborating.
    campaign_target = incidents[2]
    campaign_start = datetime.fromisoformat(campaign_target["start_at"])
    for k in range(5):
        lat, lng = _jitter_coord(
            rng, campaign_target["center_lat"], campaign_target["center_lng"], 45
        )
        reports.append({
            "event_id": f"AC{seed:04d}-{k:02d}",
            "lat": round(lat, 7),
            "lng": round(lng, 7),
            "created_at": _iso(
                campaign_start + timedelta(minutes=float(rng.uniform(-3, 3)))
            ),
            "flood": round(float(rng.uniform(0.86, 1.0)), 4),
            "urgency": round(float(rng.uniform(0.86, 1.0)), 4),
            "n_trapped": int(rng.integers(80, 180)),
            "vulnerability": round(float(rng.uniform(20, 55)), 4),
            "has_image": True,
            "source_type": "social_media",
            "province": campaign_target["province"],
            "note": "synthetic_report",
            "missing_fields": [],
            "evaluation_only": _report_eval(
                None,
                is_fake=True,
                adversary="coordinated_high_conf_campaign",
            ),
        })
    return reports


def _replace_with_opaque_event_ids(reports: list[dict], seed: int) -> None:
    """Remove source/scenario/lineage prefixes from every inference-visible ID."""
    identifiers = [
        "EV-"
        + sha256_bytes(
            f"candidate-event-v1:{int(seed)}:{index}".encode("utf-8")
        )[:20]
        for index in range(len(reports))
    ]
    if len(set(identifiers)) != len(identifiers):
        raise RuntimeError("opaque event-id collision")
    for report, event_id in zip(reports, identifiers, strict=True):
        report["event_id"] = event_id


def build_candidate_dataset(seed: int, split: str | None = None) -> dict:
    """Build one deterministic candidate dataset without writing current data."""
    registered_split = registered_split_for_seed(int(seed))
    derived_split = registered_split or "unregistered"
    if split is not None and str(split) != derived_split:
        raise ValueError(
            f"seed {seed} belongs to split {derived_split!r}, not {split!r}"
        )
    split = derived_split
    rng = np.random.default_rng(int(seed))
    incidents = _candidate_incidents(rng, int(seed))
    reports = _base_candidate_reports(rng, incidents, int(seed))
    reports = _inject_candidate_duplicates(rng, reports, int(seed))
    reports.extend(_candidate_unlinked_reports(rng, incidents, int(seed)))
    _replace_with_opaque_event_ids(reports, int(seed))
    dataset = {
        "schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "seed": int(seed),
        "split": str(split),
        "incidents": incidents,
        "reports": reports,
        "quality": {},
    }
    dataset["quality"] = validate_candidate_dataset(
        dataset, expected_seed=int(seed), expected_split=str(split)
    )
    validate_candidate_dataset(
        dataset, expected_seed=int(seed), expected_split=str(split)
    )
    return dataset


def load_candidate_dataset(source: str | Path | dict) -> dict:
    """Load and validate a full candidate dataset for evaluation code."""
    if isinstance(source, dict):
        data = deepcopy(source)
    else:
        data = json.loads(Path(source).read_text(encoding="utf-8"))
    validate_candidate_dataset(
        data,
        expected_seed=int(data["seed"]),
        expected_split=str(data["split"]),
    )
    return data


def candidate_inference_events(source: str | Path | dict) -> list[Event]:
    """Return sanitized Events with no incident, label, duplicate, or fake truth."""
    data = load_candidate_dataset(source)
    events: list[Event] = []
    for full_report in data["reports"]:
        report = observable_report(full_report)
        events.append(
            Event(
                event_id=str(report["event_id"]),
                lat=float(report["lat"]),
                lng=float(report["lng"]),
                created_at=datetime.fromisoformat(str(report["created_at"])),
                flood=float(report["flood"]),
                urgency=float(report["urgency"]),
                n_trapped=int(report["n_trapped"]),
                vulnerability=float(report["vulnerability"]),
                has_image=bool(report["has_image"]),
                source_type=str(report["source_type"]),
                province=str(report["province"]),
                note=str(report["note"]),
                missing_fields=tuple(report["missing_fields"]),
                gt_cluster=-1,
                is_fake=False,
            )
        )
    return events


def candidate_ground_truth(source: str | Path | dict) -> list[int]:
    """Return evaluator-only incident labels aligned with inference events."""
    data = load_candidate_dataset(source)
    return [
        -1
        if report["evaluation_only"]["gt_cluster"] is None
        else int(report["evaluation_only"]["gt_cluster"])
        for report in data["reports"]
    ]


def candidate_fake_truth(source: str | Path | dict) -> list[bool]:
    """Return evaluator-only fake-report labels aligned with inference events."""
    data = load_candidate_dataset(source)
    return [
        bool(report["evaluation_only"].get("is_fake", False))
        for report in data["reports"]
    ]


def write_candidate_bundle(
    output_dir: str | Path,
    seeds_by_split: dict[str, list[int]] | None = None,
    *,
    seed_manifest: str | Path = DEFAULT_SEED_MANIFEST,
) -> dict:
    """Atomically freeze the exact registered 20/20/40 candidate bundle."""
    destination = Path(output_dir)
    manifest_path = Path(seed_manifest)
    locked = {
        split: list(values)
        for split, values in registered_seed_splits(manifest_path).items()
    }
    supplied = (
        locked
        if seeds_by_split is None
        else {
            str(split): [int(seed) for seed in seeds]
            for split, seeds in seeds_by_split.items()
        }
    )
    if supplied != locked:
        raise ValueError("candidate bundle requires the exact locked 20/20/40 seed mapping")
    if destination.exists():
        raise FileExistsError(f"refusing existing candidate bundle: {destination}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.partial-",
            dir=destination.parent,
        )
    )
    try:
        entries: list[dict] = []
        for split, seeds in locked.items():
            split_dir = staging / split
            split_dir.mkdir()
            for seed in seeds:
                data = build_candidate_dataset(seed, split)
                payload = canonical_json_bytes(data)
                relative_path = Path(split) / f"seed_{seed}.json"
                (staging / relative_path).write_bytes(payload)
                entries.append({
                    "seed": seed,
                    "split": split,
                    "path": relative_path.as_posix(),
                    "sha256": sha256_bytes(payload),
                    "n_incidents": data["quality"]["n_incidents"],
                    "n_reports": data["quality"]["n_reports"],
                    "quality_status": data["quality"]["status"],
                    "quality": data["quality"],
                })

        split_summaries: dict[str, dict] = {}
        for split in locked:
            selected = [row for row in entries if row["split"] == split]
            report_counts = [row["n_reports"] for row in selected]
            fake_rates = [
                row["quality"]["n_fake_reports"] / row["n_reports"] for row in selected
            ]
            exact_rates = [row["quality"]["exact_duplicate_rate"] for row in selected]
            near_rates = [row["quality"]["near_duplicate_rate"] for row in selected]
            overlap_rates = [row["quality"]["population_overlap_rate"] for row in selected]
            split_summaries[split] = {
                "n_seeds": len(selected),
                "n_reports_min": min(report_counts),
                "n_reports_max": max(report_counts),
                "n_reports_total": sum(report_counts),
                "fake_rate_min": round(min(fake_rates), 6),
                "fake_rate_max": round(max(fake_rates), 6),
                "exact_duplicate_rate_min": round(min(exact_rates), 6),
                "exact_duplicate_rate_max": round(max(exact_rates), 6),
                "near_duplicate_rate_min": round(min(near_rates), 6),
                "near_duplicate_rate_max": round(max(near_rates), 6),
                "population_overlap_rate_min": round(min(overlap_rates), 6),
                "population_overlap_rate_max": round(max(overlap_rates), 6),
                "all_quality_gates_pass": all(
                    row["quality_status"] == "pass" for row in selected
                ),
            }

        schema_path = Path(__file__).with_name("schema.py")
        data_spec_path = Path(__file__).resolve().parents[2] / "revision" / "data-spec.md"
        manifest = {
            "schema_version": "candidate-dataset-manifest-v2",
            "dataset_schema_version": SCHEMA_VERSION,
            "generator_version": GENERATOR_VERSION,
            "generator_sha256": sha256_bytes(Path(__file__).read_bytes()),
            "schema_sha256": sha256_bytes(schema_path.read_bytes()),
            "seed_manifest_sha256": sha256_bytes(manifest_path.read_bytes()),
            "data_spec_sha256": sha256_bytes(data_spec_path.read_bytes()),
            "seed_mapping": locked,
            "split_summaries": split_summaries,
            "entries": entries,
        }
        (staging / "manifest.json").write_bytes(canonical_json_bytes(manifest))
        if destination.exists():
            raise FileExistsError(f"refusing existing candidate bundle: {destination}")
        os.replace(staging, destination)
        return manifest
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def _candidate_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Freeze candidate datasets without touching historical datasets."
    )
    parser.add_argument("--candidate-output-dir", type=Path, required=True)
    parser.add_argument(
        "--seed-manifest",
        type=Path,
        default=DEFAULT_SEED_MANIFEST,
    )
    return parser


def main(arguments: list[str] | None = None) -> int:
    args = _candidate_parser().parse_args(arguments)
    manifest = write_candidate_bundle(
        args.candidate_output_dir,
        seed_manifest=args.seed_manifest,
    )
    print(f"frozen {len(manifest['entries'])} candidate datasets")
    print(f"manifest: {args.candidate_output_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
