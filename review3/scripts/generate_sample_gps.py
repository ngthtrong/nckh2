from __future__ import annotations

import csv
import math
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT = DATA_DIR / "sample_reports.csv"


@dataclass(frozen=True)
class Center:
    province: str
    lat: float
    lng: float


CENTERS = [
    Center("Ha Tinh", 18.355, 105.887),
    Center("Quang Binh", 17.468, 106.622),
    Center("Quang Tri", 16.744, 107.200),
    Center("Thua Thien Hue", 16.463, 107.590),
    Center("Da Nang", 16.054, 108.202),
    Center("Quang Nam", 15.539, 108.248),
    Center("Quang Ngai", 15.120, 108.792),
    Center("Binh Dinh", 13.782, 109.219),
    Center("Phu Yen", 13.088, 109.092),
]

NAME_POOL = [
    "Nguyen Van An",
    "Tran Thi Bich",
    "Le Hoang Nam",
    "Pham Thu Ha",
    "Vo Minh Khoa",
    "Dang Ngoc Anh",
    "Hoang Gia Bao",
    "Bui Thi Mai",
]

IMAGE_LABELS = ["none", "low", "medium", "high"]
TEXT_LABELS = ["urgent_rescue", "need_supplies", "safe_update", "irrelevant"]

IMAGE_SCORE = {"none": 0.0, "low": 0.33, "medium": 0.67, "high": 1.0}
TEXT_SCORE = {"irrelevant": 0.0, "safe_update": 0.25, "need_supplies": 0.65, "urgent_rescue": 1.0}


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def urgency_score(created_at: datetime, reference: datetime, lat: float, lng: float, cluster_events: list[dict], image_label: str, text_label: str) -> float:
    age_hours = max((reference - created_at).total_seconds() / 3600.0, 0.0)
    recency = math.exp(-age_hours / 12.0)

    time_neighbors = sum(1 for item in cluster_events if abs((item["created_at"] - created_at).total_seconds()) <= 2 * 3600)
    space_neighbors = sum(1 for item in cluster_events if haversine_km(lat, lng, item["lat"], item["lng"]) <= 1.0)

    density_time = math.log1p(time_neighbors) / math.log1p(12)
    density_space = math.log1p(space_neighbors) / math.log1p(12)
    image_value = IMAGE_SCORE[image_label]
    text_value = TEXT_SCORE[text_label]

    score = 0.25 * recency + 0.20 * density_time + 0.20 * density_space + 0.20 * image_value + 0.15 * text_value
    return round(min(max(score, 0.0), 1.0), 4)


def pick_text(province: str, image_label: str, rng: random.Random) -> str:
    if image_label == "high":
        return rng.choices(
            [
                "Cuu voi! Nuoc vao toi mai nha, can nguoi den ngay.",
                "Khu nay ngap nang, can cuu ho gap, co nguoi mac ket.",
                "Can ho tro khan cap vi nuoc dang len rat nhanh.",
            ],
            weights=[0.45, 0.35, 0.20],
            k=1,
        )[0]
    if image_label == "medium":
        return rng.choices(
            [
                "Nha dang bi ngap mot phan, can ho tro di chuyen.",
                "Xin cung cap thuc pham va nuoc sach cho khu vuc nay.",
                "Muc nuoc dang tang, can theo doi them.",
            ],
            weights=[0.4, 0.35, 0.25],
            k=1,
        )[0]
    if image_label == "low":
        return rng.choices(
            [
                "Duong vao con bi ngap nhe, hien tai van an toan.",
                "Gia dinh toi da di chuyen len cao hon.",
                "Vung nay co nuoc ngap nhung chua qua nghiem trong.",
            ],
            weights=[0.35, 0.35, 0.30],
            k=1,
        )[0]
    return rng.choices(
        [
            "Gia dinh toi da on dinh, khong can ho tro them.",
            "Thong tin cap nhat tinh hinh khu vuc, moi nguoi an toan.",
            "Thoi tiet hoi am uot nhung chua co ngap lu.",
        ],
        weights=[0.4, 0.35, 0.25],
        k=1,
    )[0]


def build_events(seed: int = 42, count: int = 240):
    rng = random.Random(seed)
    base_time = datetime(2026, 5, 20, 0, 0, 0, tzinfo=timezone.utc)
    clusters = []
    remaining = count

    for index, center in enumerate(CENTERS):
        center_count = count // len(CENTERS)
        if index < count % len(CENTERS):
            center_count += 1

        group_count = 2
        group_sizes = [center_count // group_count] * group_count
        for i in range(center_count % group_count):
            group_sizes[i] += 1

        for group_index, group_size in enumerate(group_sizes):
            if remaining <= 0:
                break

            anchor_time = base_time + timedelta(hours=rng.randint(0, 72), minutes=rng.randint(0, 59))
            anchor_lat = center.lat + rng.uniform(-0.006, 0.006)
            anchor_lng = center.lng + rng.uniform(-0.006, 0.006)
            group_bias = rng.choices(IMAGE_LABELS, weights=[0.10, 0.22, 0.30, 0.38], k=1)[0]

            for _ in range(group_size):
                if remaining <= 0:
                    break

                created_at = anchor_time + timedelta(minutes=rng.randint(-90, 90))
                lat = anchor_lat + rng.uniform(-0.0045, 0.0045)
                lng = anchor_lng + rng.uniform(-0.0045, 0.0045)

                image_label = rng.choices(
                    IMAGE_LABELS,
                    weights=[0.10, 0.18, 0.30, 0.42] if group_bias == "high" else [0.18, 0.30, 0.32, 0.20] if group_bias == "medium" else [0.28, 0.34, 0.22, 0.16],
                    k=1,
                )[0]
                if image_label == "high":
                    text_label = rng.choices(TEXT_LABELS, weights=[0.58, 0.18, 0.16, 0.08], k=1)[0]
                elif image_label == "medium":
                    text_label = rng.choices(TEXT_LABELS, weights=[0.26, 0.36, 0.30, 0.08], k=1)[0]
                elif image_label == "low":
                    text_label = rng.choices(TEXT_LABELS, weights=[0.08, 0.34, 0.45, 0.13], k=1)[0]
                else:
                    text_label = rng.choices(TEXT_LABELS, weights=[0.05, 0.12, 0.28, 0.55], k=1)[0]

                provisional = {
                    "province": center.province,
                    "created_at": created_at,
                    "lat": round(lat, 6),
                    "lng": round(lng, 6),
                }
                clusters.append(provisional)

                score = urgency_score(created_at, base_time + timedelta(hours=96), lat, lng, clusters, image_label, text_label)
                name = rng.choice(NAME_POOL)
                phone = f"0{rng.randint(3, 9)}{rng.randint(10000000, 99999999)}"

                yield_row = {
                    "report_id": str(uuid.uuid4()),
                    "created_at": created_at.isoformat(),
                    "user_id": str(uuid.uuid4()),
                    "name": name,
                    "phone": phone,
                    "province": center.province,
                    "lat": round(lat, 6),
                    "lng": round(lng, 6),
                    "text_content": pick_text(center.province, image_label, rng),
                    "image_label": image_label,
                    "text_label": text_label,
                    "urgency_score": score,
                    "network_mode": rng.choices(["full", "metadata"], weights=[0.72, 0.28], k=1)[0],
                    "sync_status": rng.choices(["pending", "synced"], weights=[0.35, 0.65], k=1)[0],
                }
                clusters[-1].update({"image_label": image_label, "text_label": text_label, "urgency_score": score})
                remaining -= 1
                yield yield_row

        if remaining <= 0:
            break


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rows = list(build_events())
    fieldnames = [
        "report_id",
        "created_at",
        "user_id",
        "name",
        "phone",
        "province",
        "lat",
        "lng",
        "text_content",
        "image_label",
        "text_label",
        "urgency_score",
        "network_mode",
        "sync_status",
    ]

    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} sample rows to {OUTPUT}")


if __name__ == "__main__":
    main()
