"""Sinh bộ dữ liệu synthetic mô phỏng báo cáo cứu hộ bão lũ Miền Trung VN.

Vùng địa lý: Huế – Quảng Trị – Quảng Nam (16–17°N, 107–108.5°E).
Cấu trúc:
  - Lõi định lượng: nhiều cụm địa lý có nhãn ground-truth (gt_cluster) để đo
    ARI/NMI, modularity, và chạy ablation.
  - Kịch bản minh họa (narrative): các trường hợp được thiết kế thủ công để
    stress-test đúng các fix trong Mục 4 (gating địa lý, gate C_i, V_agg nhân...).

Không dùng Date.now/random không kiểm soát: mọi ngẫu nhiên qua numpy Generator
có seed cố định để tái lập.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.attributes import Event  # noqa: E402

# Tâm các "ốc đảo" ngập lụt quanh Miền Trung (lat, lng, tên tỉnh)
CLUSTER_CENTERS = [
    (16.4637, 107.5909, "Thừa Thiên Huế"),   # TP Huế
    (16.7500, 107.1900, "Quảng Trị"),         # Đông Hà
    (15.8801, 108.3380, "Quảng Nam"),         # Hội An
    (16.0678, 108.2208, "Đà Nẵng"),           # Đà Nẵng
    (16.3500, 107.7000, "Thừa Thiên Huế"),    # Phú Vang
    (17.0000, 107.0500, "Quảng Trị"),         # Vĩnh Linh
]

BASE_TIME = datetime(2026, 10, 15, 8, 0, 0, tzinfo=timezone.utc)


def _jitter_coord(rng, lat, lng, spread_m):
    """Dịch tọa độ ngẫu nhiên trong bán kính ~spread_m mét."""
    # 1 độ vĩ ~ 111_000 m; kinh độ co theo cos(lat)
    dlat = rng.normal(0, spread_m / 111_000.0)
    dlng = rng.normal(0, spread_m / (111_000.0 * np.cos(np.radians(lat))))
    return lat + dlat, lng + dlng


def generate_core(rng, n_per_cluster=40, spread_m=250.0) -> list[Event]:
    """Sinh lõi định lượng: mỗi tâm là một cụm ground-truth gắn kết địa lý."""
    events: list[Event] = []
    eid = 0
    for cid, (clat, clng, prov) in enumerate(CLUSTER_CENTERS):
        # mỗi cụm có "tính cách" ngập/khẩn cấp riêng
        base_flood = rng.uniform(0.35, 0.9)
        base_urg = rng.uniform(0.3, 0.85)
        for _ in range(n_per_cluster):
            lat, lng = _jitter_coord(rng, clat, clng, spread_m)
            t = BASE_TIME + timedelta(minutes=float(rng.uniform(0, 90)))
            flood = float(np.clip(rng.normal(base_flood, 0.08), 0, 1))
            urg = float(np.clip(rng.normal(base_urg, 0.1), 0, 1))
            n_trapped = int(max(1, rng.poisson(4)))
            # ~15% báo cáo chứa đối tượng yếu thế
            vuln = 0.0
            if rng.random() < 0.15:
                vuln = float(rng.choice([1.0, 1.5, 2.0]))
            has_img = bool(rng.random() < 0.6)
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
                    gt_cluster=cid,
                    note="core",
                )
            )
            eid += 1
    return events


def generate_noise(rng, n_noise=20) -> list[Event]:
    """Báo cáo nhiễu rải rác (gt_cluster = -1), một phần là tin giả."""
    events: list[Event] = []
    lat_lo, lat_hi = 15.7, 17.1
    lng_lo, lng_hi = 107.0, 108.6
    for i in range(n_noise):
        lat = float(rng.uniform(lat_lo, lat_hi))
        lng = float(rng.uniform(lng_lo, lng_hi))
        t = BASE_TIME + timedelta(minutes=float(rng.uniform(0, 120)))
        is_fake = bool(rng.random() < 0.4)
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
                has_image=bool(rng.random() < 0.2),  # nhiễu ít ảnh hơn
                province="N/A",
                gt_cluster=-1,
                is_fake=is_fake,
                note="fake_report" if is_fake else "noise",
            )
        )
    return events


def narrative_scenarios() -> list[Event]:
    """Kịch bản minh họa thủ công — mỗi cụm chứng minh một fix của Mục 4.

    S1: hai điểm CÙNG ngữ cảnh ngập nặng nhưng CÁCH XA ~103km -> gating phải tách.
    S2: một cụm nhỏ có nhiều đối tượng yếu thế -> V_agg (nhân) phải đẩy ưu tiên.
    S3: một báo cáo giả thổi phồng 200 người, C_i thấp -> gate C_i phải hạ nhiệt.
    S4: cụm đông người nhưng ngập nhẹ vs cụm ít người ngập nóc -> F_max & cân bằng.
    """
    ev: list[Event] = []
    t0 = BASE_TIME

    # S1 — hai điểm ngập nóc (F≈0.95) nhưng cách xa: Huế vs Hội An (~103km)
    ev.append(Event("S1_A", 16.4637, 107.5909, t0, 0.95, 0.9, 3, 0.0, True,
                    "Thừa Thiên Huế", "S1: ngập nóc tại Huế", gt_cluster=100))
    ev.append(Event("S1_B", 15.8801, 108.3380, t0 + timedelta(minutes=5), 0.96, 0.92, 4, 0.0, True,
                    "Quảng Nam", "S1: ngập nóc tại Hội An (xa 103km)", gt_cluster=101))

    # S2 — cụm nhỏ 5 điểm sát nhau, nhiều đối tượng yếu thế
    for k in range(5):
        ev.append(Event(f"S2_{k}", 16.7500 + k * 0.0008, 107.1900 + k * 0.0008,
                        t0 + timedelta(minutes=10 + k), 0.7, 0.75, 2,
                        vulnerability=2.0, has_image=True, province="Quảng Trị",
                        note="S2: cụm nhiều người yếu thế", gt_cluster=102))

    # S3 — cụm thật (có ảnh, củng cố lẫn nhau) + 1 tin giả ISOLATED thổi phồng 200
    # người: đứng lẻ (không lân cận củng cố), KHÔNG ảnh -> heuristic cho C_i thấp.
    for k in range(4):
        ev.append(Event(f"S3_{k}", 16.0678 + k * 0.0007, 108.2208 + k * 0.0007,
                        t0 + timedelta(minutes=20 + k), 0.6, 0.55, 3,
                        0.0, True, "Đà Nẵng", "S3: cụm thật", gt_cluster=103))
    # tin giả đặt ở vị trí cô lập giữa các vùng, không báo cáo nào lân cận
    ev.append(Event("S3_FAKE", 16.5500, 107.9000, t0 + timedelta(minutes=25),
                    0.99, 0.99, 200, 0.0, has_image=False, province="N/A",
                    note="S3: tin giả cô lập thổi phồng 200 người", gt_cluster=-1, is_fake=True))

    # S4 — cụm A đông (10 điểm) ngập nhẹ; cụm B nhỏ (3) ngập nóc
    for k in range(10):
        ev.append(Event(f"S4A_{k}", 16.3500 + k * 0.0006, 107.7000 + k * 0.0006,
                        t0 + timedelta(minutes=30 + k), 0.35, 0.4, 5,
                        0.0, True, "Thừa Thiên Huế", "S4A: đông người ngập nhẹ", gt_cluster=104))
    for k in range(3):
        ev.append(Event(f"S4B_{k}", 17.0000 + k * 0.0006, 107.0500 + k * 0.0006,
                        t0 + timedelta(minutes=40 + k), 0.97, 0.9, 2,
                        0.0, True, "Quảng Trị", "S4B: ít người ngập nóc", gt_cluster=105))
    return ev


def event_to_dict(ev: Event) -> dict:
    d = asdict(ev)
    d["created_at"] = ev.created_at.isoformat()
    return d


def build_dataset(seed: int = 42, n_per_cluster: int = 40, n_noise: int = 20) -> dict:
    rng = np.random.default_rng(seed)
    core = generate_core(rng, n_per_cluster=n_per_cluster)
    noise = generate_noise(rng, n_noise=n_noise)
    narrative = narrative_scenarios()
    all_events = core + noise + narrative
    return {
        "meta": {
            "seed": seed,
            "region": "Central Vietnam (Hue - Quang Tri - Quang Nam - Da Nang)",
            "base_time": BASE_TIME.isoformat(),
            "n_core": len(core),
            "n_noise": len(noise),
            "n_narrative": len(narrative),
            "n_total": len(all_events),
            "n_gt_clusters": len(CLUSTER_CENTERS),
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
    print(f"Wrote {dataset['meta']['n_total']} events -> {out_path}")
    print(f"  core={dataset['meta']['n_core']} "
          f"noise={dataset['meta']['n_noise']} "
          f"narrative={dataset['meta']['n_narrative']}")
