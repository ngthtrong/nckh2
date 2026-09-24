import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

import storage
from canonical import canonicalize, compute_payload_hash


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
            finally:
                storage.DB_FILE = old_db_file

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

                with self.assertRaises(sqlite3.IntegrityError):
                    storage.process_sync_messages([message])

                with storage.get_db_connection() as conn:
                    self.assertEqual(conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0], 0)
                    self.assertEqual(conn.execute("SELECT COUNT(*) FROM messages_dedup").fetchone()[0], 0)
            finally:
                storage.DB_FILE = old_db_file


if __name__ == "__main__":
    unittest.main()
