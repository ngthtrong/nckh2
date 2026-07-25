"""Sinh bộ dữ liệu synthetic mô phỏng báo cáo cứu hộ bão lũ Miền Trung VN.

Vùng địa lý: Huế – Quảng Trị – Quảng Nam – Đà Nẵng (15.7–17.1°N, 107.0–108.6°E).
Cấu trúc:
  - Lõi định lượng: nhiều cụm địa lý có nhãn ground-truth (gt_cluster) để đo
    ARI/NMI, modularity, và chạy ablation.
  - Kịch bản minh họa (narrative): các trường hợp được thiết kế thủ công để
    stress-test đúng các fix trong Mục 4 (gating địa lý, gate C_i, V_agg nhân...).

QUAN TRỌNG — sửa lỗi trần ARI (phản biện 1.1): trước đây các nhóm kịch bản được
neo ĐÚNG tọa độ tâm 6 ốc đảo lõi nhưng mang nhãn gt khác, nên mọi phương pháp dựa
trên không gian buộc phải gộp chúng vào ốc đảo chủ => ARI bị ghim ở 0,892 do THIẾT
KẾ DỮ LIỆU, không phải do thuật toán. Nay mỗi nhóm kịch bản được đặt ở một "vệ
tinh" cách tâm ốc đảo chủ SAT_OFFSET_M = 3000 m (≫ sigma_geo = 700 m) nên nhãn GT
trở nên KHẢ TÁCH; kịch bản vẫn nằm trong cùng vùng địa lý/tỉnh nên ý nghĩa vận
hành không đổi. Hàm `assert_gt_separable` chặn lỗi này tái xuất hiện.

Không dùng Date.now/random không kiểm soát: mọi ngẫu nhiên qua numpy Generator
có seed cố định để tái lập.
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

# Khoảng dịch của nhóm kịch bản so với tâm ốc đảo chủ (mét).
# Chọn 3000 m: lớn hơn nhiều sigma_geo = 700 m (S_geo ~ 1e-4 < theta = 0.05 nên
# gating tách được), nhưng vẫn cùng tỉnh/vùng tác chiến.
SAT_OFFSET_M = 3000.0
# Ngưỡng kiểm tra khả tách: mọi điểm kịch bản phải cách MỌI tâm ốc đảo > mức này.
MIN_GT_SEPARATION_M = 2000.0


def _offset(lat: float, lng: float, north_m: float, east_m: float) -> tuple[float, float]:
    """Dịch tọa độ theo mét (bắc dương, đông dương) — xấp xỉ phẳng cục bộ."""
    dlat = north_m / 111_000.0
    dlng = east_m / (111_000.0 * math.cos(math.radians(lat)))
    return lat + dlat, lng + dlng


def _jitter_coord(rng, lat, lng, spread_m):
    """Dịch tọa độ ngẫu nhiên trong bán kính ~spread_m mét."""
    # 1 độ vĩ ~ 111_000 m; kinh độ co theo cos(lat)
    dlat = rng.normal(0, spread_m / 111_000.0)
    dlng = rng.normal(0, spread_m / (111_000.0 * np.cos(np.radians(lat))))
    return lat + dlat, lng + dlng


def generate_core(rng, n_per_cluster=40, spread_m=250.0) -> list[Event]:
    """Sinh lõi định lượng: mỗi tâm là một cụm ground-truth gắn kết địa lý.

    Độ lệch chuẩn nội cụm của F/E được đặt ĐỦ RỘNG (0.16/0.18) để phân bố ngữ cảnh
    của các ốc đảo CHỒNG LẤP nhau — nếu quá hẹp thì (F,E) gần như là hàm của nhãn
    ốc đảo, khiến S_context chỉ nhắc lại thông tin không gian và mọi phép quét
    tau_F/tau_E trở nên vô nghĩa (phản biện 2.4).
    """
    events: list[Event] = []
    eid = 0
    for cid, (clat, clng, prov) in enumerate(CLUSTER_CENTERS):
        # mỗi cụm có "tính cách" ngập/khẩn cấp riêng
        base_flood = rng.uniform(0.35, 0.9)
        base_urg = rng.uniform(0.3, 0.85)
        for _ in range(n_per_cluster):
            lat, lng = _jitter_coord(rng, clat, clng, spread_m)
            t = BASE_TIME + timedelta(minutes=float(rng.uniform(0, 90)))
            flood = float(np.clip(rng.normal(base_flood, 0.16), 0, 1))
            urg = float(np.clip(rng.normal(base_urg, 0.18), 0, 1))
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


def generate_noise(rng, n_noise=60, fake_rate=0.4, fake_image_rate=0.4) -> list[Event]:
    """Báo cáo nhiễu rải rác (gt_cluster = -1), một phần là tin giả.

    n_noise mặc định 60 (trước là 20) để số tin giả đủ lớn cho phép đo phát hiện
    có ý nghĩa thống kê: với 6 dương tính thì ROC-AUC/AP không thể diễn giải
    (phản biện 2.3). Ngoài ra `fake_image_rate` cho phép ~40% tin giả CÓ ảnh, để
    C_i không còn là bản sao của cờ has_image.
    """
    events: list[Event] = []
    lat_lo, lat_hi = 15.7, 17.1
    lng_lo, lng_hi = 107.0, 108.6
    for i in range(n_noise):
        lat = float(rng.uniform(lat_lo, lat_hi))
        lng = float(rng.uniform(lng_lo, lng_hi))
        t = BASE_TIME + timedelta(minutes=float(rng.uniform(0, 120)))
        is_fake = bool(rng.random() < fake_rate)
        if is_fake:
            has_img = bool(rng.random() < fake_image_rate)
        else:
            has_img = bool(rng.random() < 0.2)   # nhiễu thật cũng ít ảnh
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
                province="N/A",
                gt_cluster=-1,
                is_fake=is_fake,
                note="fake_report" if is_fake else "noise",
            )
        )
    return events


# Vệ tinh của từng nhóm kịch bản: gt -> (chỉ số ốc đảo chủ, dịch bắc, dịch đông).
# Mỗi nhóm nằm cách tâm ốc đảo chủ SAT_OFFSET_M nên nhãn GT khả tách bằng không gian.
_SATELLITES = {
    100: (0, +SAT_OFFSET_M, 0.0),                  # S1_A — vệ tinh Huế
    101: (2, -SAT_OFFSET_M, 0.0),                  # S1_B — vệ tinh Hội An
    102: (1, 0.0, +SAT_OFFSET_M),                  # S2   — vệ tinh Đông Hà
    103: (3, 0.0, -SAT_OFFSET_M),                  # S3   — vệ tinh Đà Nẵng
    104: (4, +2121.0, +2121.0),                    # S4A  — vệ tinh Phú Vang
    105: (5, -2121.0, +2121.0),                    # S4B  — vệ tinh Vĩnh Linh
    106: (0, 0.0, +2 * SAT_OFFSET_M),              # S5A  — vệ tinh Huế (hướng đông)
    107: (0, 0.0, +2 * SAT_OFFSET_M),              # S5B  — sát S5A, xem dưới
}

# Khoảng cách giữa hai nhóm S5 (mét). Chọn 900 m: nhỏ so với sigma_geo = 700 m nên
# S_geo giữa hai nhóm vẫn đáng kể (~0.44) => CHỈ có S_context mới tách được chúng.
S5_GAP_M = 900.0


def _sat_center(gt: int) -> tuple[float, float, str]:
    idx, north, east = _SATELLITES[gt]
    clat, clng, prov = CLUSTER_CENTERS[idx]
    lat, lng = _offset(clat, clng, north, east)
    if gt == 107:
        lat, lng = _offset(lat, lng, 0.0, S5_GAP_M)
    return lat, lng, prov


def narrative_scenarios(rng=None, jitter_m: float = 40.0) -> list[Event]:
    """Kịch bản minh họa — mỗi nhóm chứng minh một quyết định thiết kế.

    S1: hai điểm CÙNG ngữ cảnh ngập nặng nhưng CÁCH XA ~100km -> gating phải tách.
    S2: một cụm nhỏ có nhiều đối tượng yếu thế -> V_agg (nhân) phải đẩy ưu tiên.
    S3: một báo cáo giả thổi phồng 200 người, C_i thấp -> gate C_i phải hạ nhiệt.
    S4: cụm đông người nhưng ngập nhẹ vs cụm ít người ngập nóc -> F_max & cân bằng.
    S5: HAI nhóm SÁT NHAU (900 m) nhưng ngữ cảnh NGƯỢC NHAU (F 0.30 vs 0.95) ->
        đây là ca duy nhất mà S_context bắt buộc phải làm việc; nếu bỏ gamma thì
        hai nhóm gộp lại. Nhóm này khiến phép quét tau_F/tau_E và ablation gamma
        có tín hiệu thật thay vì phẳng tuyệt đối (phản biện 2.4).

    `rng` (tùy chọn): nếu truyền vào, mỗi điểm được jitter +-jitter_m mét để các
    thí nghiệm đa hạt giống đo được cả bất định của chính các nhóm kịch bản
    (trước đây nhóm này hard-code hoàn toàn nên không có bất định — phản biện 2.6).
    """
    ev: list[Event] = []
    t0 = BASE_TIME

    def at(gt: int, k: int = 0, step_m: float = 150.0):
        """Tọa độ điểm thứ k của nhóm gt: rải theo đường chéo step_m mét/điểm."""
        lat, lng, prov = _sat_center(gt)
        lat, lng = _offset(lat, lng, k * step_m * 0.7071, k * step_m * 0.7071)
        if rng is not None and jitter_m > 0:
            lat, lng = _jitter_coord(rng, lat, lng, jitter_m / 2.0)
        return round(lat, 6), round(lng, 6), prov

    # S1 — HAI NHÓM ngập nóc (F≈0.95), ngữ cảnh gần như trùng khớp, nhưng cách
    # nhau ~100 km. Mỗi nhóm 3 điểm (không phải 1) để nhóm tạo thành cụm thực sự:
    # nếu chỉ 1 điểm/nhóm thì cụm là singleton và phép thử gating hầu như không
    # đóng góp vào ARI, tức bằng chứng yếu hơn tuyên bố (phản biện 2.3).
    for k in range(3):
        lat, lng, prov = at(100, k, step_m=90.0)
        ev.append(Event(f"S1_A_{k}", lat, lng, t0 + timedelta(minutes=k),
                        0.95, 0.9, 3, 0.0, True, prov,
                        "S1: ngập nóc tại Huế", gt_cluster=100))
    for k in range(3):
        lat, lng, prov = at(101, k, step_m=90.0)
        ev.append(Event(f"S1_B_{k}", lat, lng, t0 + timedelta(minutes=5 + k),
                        0.96, 0.92, 4, 0.0, True, prov,
                        "S1: ngập nóc tại Hội An (xa ~100km)", gt_cluster=101))

    # S2 — cụm nhỏ 5 điểm sát nhau, nhiều đối tượng yếu thế
    for k in range(5):
        lat, lng, prov = at(102, k, step_m=90.0)
        ev.append(Event(f"S2_{k}", lat, lng, t0 + timedelta(minutes=10 + k),
                        0.7, 0.75, 2, vulnerability=2.0, has_image=True, province=prov,
                        note="S2: cụm nhiều người yếu thế", gt_cluster=102))

    # S3 — cụm thật (có ảnh, củng cố lẫn nhau) + 1 tin giả ISOLATED thổi phồng 200
    # người: đứng lẻ (không lân cận củng cố), KHÔNG ảnh -> heuristic cho C_i thấp.
    for k in range(4):
        lat, lng, prov = at(103, k, step_m=80.0)
        ev.append(Event(f"S3_{k}", lat, lng, t0 + timedelta(minutes=20 + k),
                        0.6, 0.55, 3, 0.0, True, prov, "S3: cụm thật", gt_cluster=103))
    # tin giả đặt ở vị trí cô lập giữa các vùng, không báo cáo nào lân cận
    ev.append(Event("S3_FAKE", 16.5500, 107.9000, t0 + timedelta(minutes=25),
                    0.99, 0.99, 200, 0.0, has_image=False, province="N/A",
                    note="S3: tin giả cô lập thổi phồng 200 người", gt_cluster=-1, is_fake=True))

    # S4 — cụm A đông (10 điểm) ngập nhẹ; cụm B nhỏ (3) ngập nóc
    for k in range(10):
        lat, lng, prov = at(104, k, step_m=70.0)
        ev.append(Event(f"S4A_{k}", lat, lng, t0 + timedelta(minutes=30 + k),
                        0.35, 0.4, 5, 0.0, True, prov,
                        "S4A: đông người ngập nhẹ", gt_cluster=104))
    for k in range(3):
        lat, lng, prov = at(105, k, step_m=70.0)
        ev.append(Event(f"S4B_{k}", lat, lng, t0 + timedelta(minutes=40 + k),
                        0.97, 0.9, 2, 0.0, True, prov,
                        "S4B: ít người ngập nóc", gt_cluster=105))

    # S5 — hai nhóm SÁT NHAU nhưng ngữ cảnh ngược nhau: chỉ S_context tách được.
    # Cùng cửa sổ thời gian để S_temp KHÔNG phân biệt được hai nhóm.
    for k in range(6):
        lat, lng, prov = at(106, k, step_m=90.0)
        ev.append(Event(f"S5A_{k}", lat, lng, t0 + timedelta(minutes=50 + k),
                        0.30, 0.35, 3, 0.0, True, prov,
                        "S5A: ngập nhẹ, sát cạnh nhóm ngập nóc", gt_cluster=106))
    for k in range(6):
        lat, lng, prov = at(107, k, step_m=90.0)
        ev.append(Event(f"S5B_{k}", lat, lng, t0 + timedelta(minutes=50 + k),
                        0.95, 0.92, 3, 0.0, True, prov,
                        "S5B: ngập nóc, sát cạnh nhóm ngập nhẹ", gt_cluster=107))
    return ev


def assert_gt_separable(events: list[Event], min_sep_m: float = MIN_GT_SEPARATION_M) -> dict:
    """Chặn lỗi trần-ARI: nhóm kịch bản KHÔNG được trùng vị trí ốc đảo lõi.

    Nếu một điểm mang nhãn gt >= 100 nằm sát tâm một ốc đảo (nhãn 0..5), mọi
    phương pháp dựa trên không gian buộc phải gộp nó vào ốc đảo đó, ghim trần ARI
    xuống dưới 1,0 vì lý do THIẾT KẾ chứ không phải chất lượng thuật toán. Hàm này
    raise ngay khi sinh dữ liệu để lỗi không âm thầm quay lại.
    """
    centers = [(clat, clng) for clat, clng, _ in CLUSTER_CENTERS]
    worst = None
    for e in events:
        if e.gt_cluster is None or e.gt_cluster < 100:
            continue
        dmin = min(haversine_m(e.lat, e.lng, cl[0], cl[1]) for cl in centers)
        if worst is None or dmin < worst[1]:
            worst = (e.event_id, dmin, e.gt_cluster)
        if dmin < min_sep_m:
            raise AssertionError(
                f"Nhóm kịch bản {e.event_id} (gt={e.gt_cluster}) chỉ cách tâm ốc đảo "
                f"{dmin:.0f} m (< {min_sep_m:.0f} m). Nhãn ground-truth sẽ không khả "
                f"tách bằng không gian và trần ARI bị ghim dưới 1,0 do thiết kế dữ liệu."
            )
    return {
        "min_narrative_to_core_center_m": round(worst[1], 1) if worst else None,
        "closest_narrative_event": worst[0] if worst else None,
    }


def event_to_dict(ev: Event) -> dict:
    d = asdict(ev)
    d["created_at"] = ev.created_at.isoformat()
    return d


def make_events(seed: int = 42, n_per_cluster: int = 40, n_noise: int = 60,
                jitter_narrative: bool = True) -> list[Event]:
    """Sinh danh sách Event TRONG BỘ NHỚ (không ghi file).

    Dùng cho các thí nghiệm đa hạt giống / đo scaling: chúng cần nhiều bộ dữ liệu
    mà không được ghi đè data/dataset.json của luồng chính.
    """
    rng = np.random.default_rng(seed)
    core = generate_core(rng, n_per_cluster=n_per_cluster)
    noise = generate_noise(rng, n_noise=n_noise)
    narrative = narrative_scenarios(rng if jitter_narrative else None)
    events = core + noise + narrative
    assert_gt_separable(events)
    return events


def build_dataset(seed: int = 42, n_per_cluster: int = 40, n_noise: int = 60) -> dict:
    rng = np.random.default_rng(seed)
    core = generate_core(rng, n_per_cluster=n_per_cluster)
    noise = generate_noise(rng, n_noise=n_noise)
    narrative = narrative_scenarios(rng)
    all_events = core + noise + narrative
    sep = assert_gt_separable(all_events)

    gt_labels = sorted({e.gt_cluster for e in all_events if e.gt_cluster is not None
                        and e.gt_cluster >= 0})
    s1a = next(e for e in narrative if e.event_id == "S1_A_0")
    s1b = next(e for e in narrative if e.event_id == "S1_B_0")
    return {
        "meta": {
            "seed": seed,
            "region": "Central Vietnam (Hue - Quang Tri - Quang Nam - Da Nang)",
            "bbox": "15.7-17.1N, 107.0-108.6E",
            "base_time": BASE_TIME.isoformat(),
            "n_core": len(core),
            "n_noise": len(noise),
            "n_narrative": len(narrative),
            "n_total": len(all_events),
            # tính động từ nhãn thực tế (trước đây hard-code len(CLUSTER_CENTERS) = 6,
            # trong khi dữ liệu có 12 nhãn -> metadata sai lệch với bài báo)
            "n_gt_clusters": len(gt_labels),
            "gt_labels": gt_labels,
            "n_fake": sum(1 for e in all_events if e.is_fake),
            "n_fake_with_image": sum(1 for e in all_events if e.is_fake and e.has_image),
            "satellite_offset_m": SAT_OFFSET_M,
            "s5_gap_m": S5_GAP_M,
            "s1_pair_distance_km": round(
                haversine_m(s1a.lat, s1a.lng, s1b.lat, s1b.lng) / 1000.0, 2),
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
    m = dataset["meta"]
    print(f"Wrote {m['n_total']} events -> {out_path}")
    print(f"  core={m['n_core']} noise={m['n_noise']} narrative={m['n_narrative']}")
    print(f"  nhãn GT={m['n_gt_clusters']} {m['gt_labels']}")
    print(f"  tin giả={m['n_fake']} (có ảnh: {m['n_fake_with_image']})")
    print(f"  khoảng cách kịch bản->tâm ốc đảo gần nhất="
          f"{m['min_narrative_to_core_center_m']} m ({m['closest_narrative_event']})")
    print(f"  khoảng cách cặp S1={m['s1_pair_distance_km']} km")
