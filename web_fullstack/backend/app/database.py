import json
import sqlite3
from pathlib import Path

from app.domain import ReportCreate, ReportRead, ReportStatus, SmsMessageRead, SmsStatus


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
        connection.execute("PRAGMA foreign_keys = ON")
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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sms_messages (
                    id TEXT PRIMARY KEY,
                    report_id TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    client_key TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    provider_message_id TEXT,
                    status TEXT NOT NULL,
                    error_code TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (report_id) REFERENCES reports(id)
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

    def get_sms_by_idempotency_key(self, key: str) -> SmsMessageRead | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM sms_messages WHERE idempotency_key = ?", (key,)
            ).fetchone()
        return self._to_sms(row) if row is not None else None

    def get_sms(self, message_id: str) -> SmsMessageRead | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM sms_messages WHERE id = ?", (message_id,)
            ).fetchone()
        return self._to_sms(row) if row is not None else None

    def reserve_sms(
        self,
        *,
        message_id: str,
        report_id: str,
        recipient: str,
        client_key: str,
        idempotency_key: str,
        now: str,
    ) -> tuple[SmsMessageRead, bool]:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO sms_messages (
                    id, report_id, recipient, client_key, idempotency_key,
                    provider_message_id, status, error_code, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, NULL, ?, NULL, ?, ?)
                """,
                (
                    message_id,
                    report_id,
                    recipient,
                    client_key,
                    idempotency_key,
                    SmsStatus.pending.value,
                    now,
                    now,
                ),
            )
            row = connection.execute(
                "SELECT * FROM sms_messages WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
        if row is None:
            raise RuntimeError("SMS reservation did not produce a row")
        return self._to_sms(row), cursor.rowcount == 1

    def update_sms(
        self,
        message_id: str,
        *,
        status: SmsStatus,
        updated_at: str,
        provider_message_id: str | None = None,
        error_code: str | None = None,
    ) -> SmsMessageRead:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE sms_messages
                SET status = ?, updated_at = ?, provider_message_id = ?, error_code = ?
                WHERE id = ?
                """,
                (status.value, updated_at, provider_message_id, error_code, message_id),
            )
            row = connection.execute(
                "SELECT * FROM sms_messages WHERE id = ?", (message_id,)
            ).fetchone()
        if row is None:
            raise RuntimeError("SMS message disappeared during update")
        return self._to_sms(row)

    def count_recent_sms(
        self,
        *,
        recipient: str,
        report_id: str,
        client_key: str,
        since: str,
    ) -> int:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM sms_messages
                WHERE created_at >= ?
                  AND status IN ('pending', 'queued', 'sent', 'delivered')
                  AND (recipient = ? OR report_id = ? OR client_key = ?)
                """,
                (since, recipient, report_id, client_key),
            ).fetchone()
        return int(row["total"])

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

    @staticmethod
    def _to_sms(row: sqlite3.Row) -> SmsMessageRead:
        return SmsMessageRead(
            id=row["id"],
            report_id=row["report_id"],
            recipient=row["recipient"],
            provider_message_id=row["provider_message_id"],
            status=SmsStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

