import json
import sqlite3
from pathlib import Path

from app.domain import ReportCreate, ReportRead, ReportStatus


class ReportRepository:
    def __init__(self, database_url: str) -> None:
        prefix = "sqlite:///"
        if not database_url.startswith(prefix):
            raise ValueError("Only sqlite:/// database URLs are supported")
        raw_path = database_url.removeprefix(prefix)
        self.database_path = Path(raw_path)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    description TEXT NOT NULL,
                    trapped_count INTEGER NOT NULL,
                    injured_count INTEGER NOT NULL,
                    vulnerable_groups TEXT NOT NULL,
                    ai_label TEXT,
                    ai_confidence REAL,
                    latitude REAL,
                    longitude REAL,
                    image_path TEXT,
                    image_name TEXT,
                    image_mime_type TEXT,
                    status TEXT NOT NULL
                )
                """
            )

    def create_or_get(
        self,
        report: ReportCreate,
        *,
        image_path: str | None,
        image_name: str | None,
        image_mime_type: str | None,
    ) -> tuple[ReportRead, bool]:
        values = (
            report.report_id,
            report.created_at,
            report.description,
            report.trapped_count,
            report.injured_count,
            json.dumps(report.vulnerable_groups, ensure_ascii=False),
            report.ai_label,
            report.ai_confidence,
            report.latitude,
            report.longitude,
            image_path,
            image_name,
            image_mime_type,
            ReportStatus.synced.value,
        )
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO reports (
                    id, created_at, description, trapped_count, injured_count,
                    vulnerable_groups, ai_label, ai_confidence, latitude, longitude,
                    image_path, image_name, image_mime_type, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
            row = connection.execute(
                "SELECT * FROM reports WHERE id = ?", (report.report_id,)
            ).fetchone()
        if row is None:
            raise RuntimeError("Report insert did not produce a row")
        return self._to_report(row), cursor.rowcount == 1

    def get_report(self, report_id: str) -> ReportRead | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM reports WHERE id = ?", (report_id,)
            ).fetchone()
        return self._to_report(row) if row is not None else None

    def list_reports(self) -> list[ReportRead]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM reports ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return [self._to_report(row) for row in rows]

    def delete(self, report_id: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM reports WHERE id = ?", (report_id,))

    @staticmethod
    def _to_report(row: sqlite3.Row) -> ReportRead:
        return ReportRead(
            id=row["id"],
            created_at=row["created_at"],
            description=row["description"],
            trapped_count=row["trapped_count"],
            injured_count=row["injured_count"],
            vulnerable_groups=json.loads(row["vulnerable_groups"]),
            ai_label=row["ai_label"],
            ai_confidence=row["ai_confidence"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            has_image=row["image_path"] is not None,
            image_name=row["image_name"],
            image_mime_type=row["image_mime_type"],
            status=ReportStatus(row["status"]),
        )

