from __future__ import annotations

from sqlalchemy import create_engine, text

from .config import get_database_url


def get_engine():
    return create_engine(get_database_url(), future=True)


def fetch_reports() -> list[dict]:
    engine = get_engine()
    query = text(
        """
        SELECT report_id, created_at, user_id, name, phone, province, lat, lng,
               text_content, image_label, text_label, urgency_score, network_mode, sync_status
        FROM rescue_reports
        ORDER BY created_at ASC
        """
    )
    with engine.begin() as conn:
        rows = conn.execute(query).mappings().all()
    return [dict(row) for row in rows]
