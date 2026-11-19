import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

# `import main` chạy init_db(): dùng DB tạm để không migrate be/data/rescue_reports.db (dữ liệu mẫu).
_TMP = tempfile.TemporaryDirectory()
os.environ.setdefault("RESCUE_DB_FILE", str(Path(_TMP.name) / "contract.db"))
os.environ.setdefault("RESCUE_UPLOADS_DIR", str(Path(_TMP.name) / "uploads"))

import storage  # noqa: E402
from canonical import canonicalize, compute_payload_hash  # noqa: E402


class ContractTest(unittest.TestCase):
    def test_rfc8785_number_serialization(self):
        self.assertEqual(canonicalize({"small": 1e-7, "threshold": 1e-6}), b'{"small":1e-7,"threshold":0.000001}')

    def test_legacy_schema_migrates_to_processing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            old_db_file = storage.DB_FILE
            storage.DB_FILE = Path(temp_dir) / "reports.db"
            try:
                with closing(sqlite3.connect(storage.DB_FILE)) as conn:
                    conn.execute("""
                        CREATE TABLE reports (
                            id TEXT PRIMARY KEY,
                            server_received_at TEXT NOT NULL,
                            created_at TEXT,
                            lat REAL,
                            lng REAL,
                            trapped_count INTEGER DEFAULT 0,
                            injured_count INTEGER DEFAULT 0,
                            vulnerable_groups TEXT,
                            description TEXT,
                            ai_tags TEXT,
                            send_mode TEXT,
                            status TEXT DEFAULT 'received',
                            image_filename TEXT,
                            image_local_path TEXT,
                            image_url TEXT,
                            raw_payload TEXT NOT NULL
                        )
                    """)
                    conn.execute("""
                        INSERT INTO reports (id, server_received_at, status, raw_payload)
                        VALUES ('legacy', '2026-09-22T00:00:00Z', 'received', '{}')
                    """)
                    conn.commit()

                storage.init_db()

                with storage.get_db_connection() as conn:
                    columns = {row["name"]: row for row in conn.execute("PRAGMA table_info(reports)")}
                    self.assertEqual(columns["status"]["dflt_value"], "'processing'")
                    self.assertEqual(conn.execute("SELECT status FROM reports WHERE id = 'legacy'").fetchone()[0], "processing")
                    self.assertIsNotNone(conn.execute("SELECT name FROM sqlite_master WHERE name = 'messages_dedup'").fetchone())
                    # Cột/bảng của dashboard quản lý được thêm và bù dữ liệu cho DB cũ.
                    legacy = conn.execute("SELECT first_received_at, updated_seq FROM reports WHERE id = 'legacy'").fetchone()
                    self.assertEqual(legacy["first_received_at"], "2026-09-22T00:00:00Z")
                    self.assertGreater(legacy["updated_seq"], 0)
                    for table in ("report_events", "teams", "sessions", "server_meta"):
                        self.assertIsNotNone(conn.execute("SELECT name FROM sqlite_master WHERE name = ?", (table,)).fetchone())
            finally:
                storage.DB_FILE = old_db_file

    def test_image_upload_keeps_first_created_at(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            old_db_file = storage.DB_FILE
            storage.DB_FILE = Path(temp_dir) / "reports.db"
            try:
                storage.init_db()
                storage.save_report({"id": "r1", "createdAt": "2026-09-27T01:00:00Z", "lat": 16.0, "lng": 108.0},
                                    client_id="dev-1")
                # Upload ảnh cho cùng meta.id với giờ địa phương không kèm múi giờ (app bản cũ).
                saved = storage.save_report(
                    {"id": "r1", "createdAt": "2026-09-27T08:00:00", "lat": 16.0, "lng": 108.0},
                    image_url="/uploads/r1.jpg", client_id="dev-1",
                )
                self.assertEqual(saved["createdAt"], "2026-09-27T01:00:00Z")
                self.assertEqual(saved["imageUrl"], "/uploads/r1.jpg")
            finally:
                storage.DB_FILE = old_db_file

    def test_report_statuses_for_app_polling(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            old_db_file = storage.DB_FILE
            storage.DB_FILE = Path(temp_dir) / "reports.db"
            try:
                storage.init_db()
                storage.save_report({"id": "a", "createdAt": "2026-09-27T01:00:00Z"})
                storage.save_report({"id": "b", "createdAt": "2026-09-27T01:00:00Z"})
                storage.update_report_status("b", "dispatched", 2)
                rows = {r["id"]: r for r in storage.get_report_statuses(["a", "b", "missing", "", "a"])}
                self.assertEqual(set(rows), {"a", "b"})
                self.assertEqual((rows["b"]["status"], rows["b"]["statusVersion"]), ("dispatched", 2))
                self.assertEqual(storage.get_report_statuses([]), [])
            finally:
                storage.DB_FILE = old_db_file

    def test_status_route_precedes_report_id_route(self):
        import main

        paths = [route.path for route in main.app.routes]
        self.assertLess(paths.index("/api/reports/status"), paths.index("/api/reports/{report_id}"))

    def test_create_message_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            old_db_file = storage.DB_FILE
            storage.DB_FILE = Path(temp_dir) / "reports.db"
            try:
                storage.init_db()
                payload = {
                    "id": "rescue-10492",
                    "createdAt": "2026-09-22T00:00:00Z",
                    "lat": 10.7769,
                    "lng": 106.7009,
                }
                message = {
                    "message_id": "message-1",
                    "client_id": "client-1",
                    "sequence_number": 1,
                    "operation_type": "CREATE_RESCUE_RECORD",
                    "created_at": "2026-09-22T00:00:00Z",
                    "payload_hash": compute_payload_hash(payload),
                    "payload": payload,
                }

                first = storage.process_sync_messages([message])
                second = storage.process_sync_messages([message])

                self.assertEqual(first[0]["status"], "accepted")
                self.assertEqual(second[0]["status"], "duplicate")
                with storage.get_db_connection() as conn:
                    self.assertEqual(conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0], 1)
                    self.assertEqual(conn.execute("SELECT COUNT(*) FROM messages_dedup").fetchone()[0], 1)
            finally:
                storage.DB_FILE = old_db_file

    def test_create_rolls_back_when_dedup_write_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            old_db_file = storage.DB_FILE
            storage.DB_FILE = Path(temp_dir) / "reports.db"
            try:
                storage.init_db()
                with storage.get_db_connection() as conn:
                    conn.execute("""
                        CREATE TRIGGER reject_dedup
                        BEFORE INSERT ON messages_dedup
                        BEGIN
                            SELECT RAISE(ABORT, 'forced dedup failure');
                        END
                    """)
                payload = {"id": "must-rollback", "lat": 10.0, "lng": 106.0}
                message = {
                    "message_id": "message-rollback",
                    "client_id": "client-1",
                    "sequence_number": 2,
                    "operation_type": "CREATE_RESCUE_RECORD",
                    "created_at": "2026-09-22T00:00:00Z",
                    "payload_hash": compute_payload_hash(payload),
                    "payload": payload,
                }

                # Lỗi bất ngờ chỉ rollback message đó và trả retry_later, không làm hỏng cả batch.
                result = storage.process_sync_messages([message])
                self.assertEqual((result[0]["status"], result[0]["retryable"]), ("retry_later", True))

                with storage.get_db_connection() as conn:
                    self.assertEqual(conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0], 0)
                    self.assertEqual(conn.execute("SELECT COUNT(*) FROM messages_dedup").fetchone()[0], 0)
            finally:
                storage.DB_FILE = old_db_file

    def test_dashboard_and_sync_share_status_rules(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            old_db_file = storage.DB_FILE
            storage.DB_FILE = Path(temp_dir) / "reports.db"
            try:
                storage.init_db()
                storage.save_report({"id": "r1", "lat": 16.0, "lng": 108.0})

                result = storage.update_report_status("r1", "dispatched", 2)
                self.assertEqual(result, {"id": "r1", "status": "dispatched", "statusVersion": 2})

                for status, version, code in (
                    ("resolved", 2, "INVALID_STATUS_VERSION"),
                    ("processing", 3, "INVALID_STATUS_TRANSITION"),
                    ("unknown", 3, "INVALID_PAYLOAD"),
                ):
                    with self.assertRaises(storage.StatusUpdateError) as ctx:
                        storage.update_report_status("r1", status, version)
                    self.assertEqual(ctx.exception.code, code)
                with self.assertRaises(storage.StatusUpdateError) as ctx:
                    storage.update_report_status("missing", "resolved", 2)
                self.assertEqual(ctx.exception.code, "REPORT_NOT_FOUND")

                payload = {"id": "r1", "status": "processing", "statusVersion": 3}
                rejected = storage.process_sync_messages([{
                    "message_id": "status-1",
                    "client_id": "client-1",
                    "sequence_number": 1,
                    "operation_type": "UPDATE_RESCUE_STATUS",
                    "created_at": "2026-09-22T00:00:00Z",
                    "payload_hash": compute_payload_hash(payload),
                    "payload": payload,
                }], operator="Điều phối A")
                self.assertEqual(rejected[0]["code"], "INVALID_STATUS_TRANSITION")
                self.assertEqual(storage.get_report_by_id("r1")["status"], "dispatched")
            finally:
                storage.DB_FILE = old_db_file


if __name__ == "__main__":
    unittest.main()
