"""exp10 — đo kích thước gói metadata biên (byte) một cách tất định.

Chứng minh tuyên bố "gói vài trăm byte thay vì ảnh/video hàng MB": với mỗi sự
kiện, ta dựng gói metadata tối thiểu gồm id, toạ độ, timestamp (epoch), và các
trường L,T,F,E,N,V,C rồi đo số byte UTF-8 của chuỗi JSON nén (không khoảng trắng).
Báo cáo min/median/max trên toàn bộ dataset (seed=42).
"""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data" / "dataset.json"
OUT = BASE / "results" / "tables" / "exp10_packet_size.json"


def packet_bytes(ev: dict) -> int:
    # gói tối thiểu: id, toạ độ, thời gian (epoch giây), L,T,F,E,N,V,C + cờ ảnh
    from datetime import datetime
    t_epoch = int(datetime.fromisoformat(ev["created_at"]).timestamp())
    pkt = {
        "id": ev["event_id"],
        "lat": round(ev["lat"], 5),
        "lng": round(ev["lng"], 5),
        "t": t_epoch,
        "F": ev["flood"],
        "E": ev["urgency"],
        "N": ev["n_trapped"],
        "V": ev["vulnerability"],
        "C": round(0.9, 2),  # placeholder độ tin cậy (1 chữ số thập phân)
        "img": 1 if ev.get("has_image") else 0,
    }
    return len(json.dumps(pkt, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    sizes = sorted(packet_bytes(e) for e in data["events"])
    n = len(sizes)
    result = [{
        "n_events": n,
        "min_bytes": sizes[0],
        "median_bytes": sizes[n // 2],
        "max_bytes": sizes[-1],
        "note": "gói JSON nén (separators sát), id+toạ độ+epoch+L,T,F,E,N,V,C+cờ ảnh",
    }]
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result[0], ensure_ascii=False))


if __name__ == "__main__":
    main()
