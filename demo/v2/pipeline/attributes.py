"""Vector thuộc tính đa chiều v_i = (L_i, T_i, F_i, E_i, N_i, V_i, C_i) — Mục 4.1."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime

from .config import ConfidenceParams


@dataclass
class Event:
    event_id: str
    lat: float                  # L_i (vĩ độ)
    lng: float                  # L_i (kinh độ)
    created_at: datetime        # T_i
    flood: float                # F_i in [0,1]
    urgency: float              # E_i in [0,1]
    n_trapped: int              # N_i
    vulnerability: float        # V_i >= 0 (tổng trọng số đối tượng yếu thế)
    has_image: bool             # tín hiệu cho C_i
    province: str = ""
    note: str = ""
    gt_cluster: int = -1        # nhãn cụm ground-truth (-1 nếu nhiễu)
    is_fake: bool = False       # đánh dấu báo cáo giả (để đánh giá tác động C_i)
    confidence: float = field(default=1.0)  # C_i (điền sau khi tính heuristic)


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Khoảng cách Haversine (mét) giữa hai tọa độ GPS."""
    radius = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_confidence(events: list[Event], params: ConfidenceParams) -> None:
    """Điền C_i cho từng sự kiện theo heuristic sigmoid (Mục 4.1).

    C_i = sigmoid(b0 + b1*1[có ảnh] + b2*log(1 + n_corrob))
    n_corrob = số báo cáo lân cận (cùng vùng không gian + cửa sổ thời gian).
    """
    for i, ev in enumerate(events):
        n_corrob = 0
        for j, other in enumerate(events):
            if i == j:
                continue
            dist = haversine_m(ev.lat, ev.lng, other.lat, other.lng)
            dt_min = abs((ev.created_at - other.created_at).total_seconds()) / 60.0
            if dist <= params.corrob_radius_m and dt_min <= params.corrob_window_min:
                n_corrob += 1
        z = params.b0 + params.b1 * (1.0 if ev.has_image else 0.0) + params.b2 * math.log1p(n_corrob)
        ev.confidence = 1.0 / (1.0 + math.exp(-z))
