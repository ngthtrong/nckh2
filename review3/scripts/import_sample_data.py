from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "sample_reports.csv"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'data' / 'review3.sqlite'}")


DDL = """
CREATE TABLE IF NOT EXISTS rescue_reports (
    report_id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    province TEXT NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lng DOUBLE PRECISION NOT NULL,
    text_content TEXT NOT NULL,
    image_label TEXT NOT NULL,
    text_label TEXT NOT NULL,
    urgency_score DOUBLE PRECISION NOT NULL,
    network_mode TEXT NOT NULL,
    sync_status TEXT NOT NULL,
    geom geometry(Point, 4326)
);

CREATE INDEX IF NOT EXISTS idx_rescue_reports_geom ON rescue_reports USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_rescue_reports_created_at ON rescue_reports (created_at);
CREATE INDEX IF NOT EXISTS idx_rescue_reports_province ON rescue_reports (province);
CREATE INDEX IF NOT EXISTS idx_rescue_reports_text_label ON rescue_reports (text_label);
CREATE INDEX IF NOT EXISTS idx_rescue_reports_image_label ON rescue_reports (image_label);
"""


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing dataset file: {DATA_PATH}. Run generate_sample_gps.py first.")

    df = pd.read_csv(DATA_PATH)
    engine = create_engine(DATABASE_URL)

    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            for statement in DDL.strip().split(";"):
                if statement.strip():
                    conn.execute(text(statement))
            conn.execute(text("TRUNCATE TABLE rescue_reports;"))
        else:
            conn.execute(text(
                """
                CREATE TABLE IF NOT EXISTS rescue_reports (
                    report_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    province TEXT NOT NULL,
                    lat REAL NOT NULL,
                    lng REAL NOT NULL,
                    text_content TEXT NOT NULL,
                    image_label TEXT NOT NULL,
                    text_label TEXT NOT NULL,
                    urgency_score REAL NOT NULL,
                    network_mode TEXT NOT NULL,
                    sync_status TEXT NOT NULL
                );
                """
            ))
            conn.execute(text("DELETE FROM rescue_reports;"))

    df.to_sql("rescue_reports", engine, if_exists="append", index=False, method="multi")

    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            conn.execute(text(
                """
                UPDATE rescue_reports
                SET geom = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
                WHERE geom IS NULL;
                """
            ))

    print(f"Imported {len(df)} rows into rescue_reports")


if __name__ == "__main__":
    main()
