"""Nạp một run dữ liệu BÁN TỔNG HỢP (src/data/gold) vào DB để demo dashboard.

Dữ liệu được neo theo bối cảnh EMSR848 nhưng báo cáo là mô phỏng; mỗi bản ghi
được gắn ``source: "synthetic"`` để dashboard hiển thị nhãn "Dữ liệu mô phỏng".
Không dùng làm bằng chứng dữ liệu thật (xem src/data/README.md).

Ví dụ:
    python seed_demo.py              # nạp run_001
    python seed_demo.py --run 5 --reset
"""
from __future__ import annotations

import argparse
import json

import storage
from config import BASE_DIR

GOLD_DIR = BASE_DIR.parent / "src" / "data" / "gold"


def load_run(run: int) -> list[dict]:
    path = GOLD_DIR / f"run_{run:03d}" / "algorithm_input.json"
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)["reports"]


def to_meta(row: dict, run: int) -> dict:
    return {
        "id": f"sim-r{run:03d}-{row['event_id']}",
        "createdAt": row["created_at"],
        "lat": row["lat"],
        "lng": row["lng"],
        "trappedCount": int(row["n_trapped"] or 0),
        "injuredCount": 0,
        "vulnerableGroups": [],
        "description": row.get("note") or "",
        "sendMode": "synthetic",
        "source": "synthetic",
        # Trường của thuật toán, cluster_service dùng trực tiếp.
        "flood": row["flood"],
        "urgency": row["urgency"],
        "n_trapped": row["n_trapped"],
        "vulnerability": row["vulnerability"],
        "confidence": row["confidence"],
        "has_image": row["has_image"],
        "province": row.get("province"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", type=int, default=1, help="số run trong src/data/gold (1-80)")
    parser.add_argument("--reset", action="store_true", help="xóa toàn bộ báo cáo trước khi nạp")
    args = parser.parse_args()

    storage.init_db()
    if args.reset:
        storage.clear_reports()
    rows = load_run(args.run)
    with storage.get_db_connection() as conn:
        for row in rows:
            storage.save_report(to_meta(row, args.run), connection=conn)
        conn.commit()
    print(f"Đã nạp {len(rows)} báo cáo mô phỏng từ run_{args.run:03d} vào {storage.DB_FILE}")


if __name__ == "__main__":
    main()
