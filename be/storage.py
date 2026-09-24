import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from config import DB_FILE, UPLOADS_DIR
from canonical import compute_payload_hash

logger = logging.getLogger("rescue_mock_server")

VALID_RESCUE_STATUS_ORDER = {
    "processing": 1,
    "dispatched": 2,
    "resolved": 3,
}


@contextmanager
def get_db_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(DB_FILE), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def _create_reports_table(conn: sqlite3.Connection, table_name: str = "reports") -> None:
    if table_name not in {"reports", "reports_new"}:
        raise ValueError("Tên bảng reports không hợp lệ")
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
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
            status TEXT DEFAULT 'processing',
            status_version INTEGER DEFAULT 1,
            image_filename TEXT,
            image_local_path TEXT,
            image_url TEXT,
            image_sha256 TEXT,
            image_size_bytes INTEGER,
            raw_payload TEXT NOT NULL
        );
    """)


def _migrate_reports_status_default(conn: sqlite3.Connection) -> None:
    columns = {row["name"]: row for row in conn.execute("PRAGMA table_info(reports)")}
    status_default = str(columns["status"]["dflt_value"] or "").strip("()")
    if status_default == "'processing'":
        conn.execute("UPDATE reports SET status = 'processing' WHERE status IS NULL OR status = 'received'")
        return

    _create_reports_table(conn, "reports_new")
    conn.execute("""
        INSERT INTO reports_new (
            id, server_received_at, created_at, lat, lng,
            trapped_count, injured_count, vulnerable_groups,
            description, ai_tags, send_mode, status, status_version,
            image_filename, image_local_path, image_url, image_sha256,
            image_size_bytes, raw_payload
        )
        SELECT
            id, server_received_at, created_at, lat, lng,
            trapped_count, injured_count, vulnerable_groups,
            description, ai_tags, send_mode,
            CASE WHEN status IS NULL OR status = 'received' THEN 'processing' ELSE status END,
            COALESCE(status_version, 1),
            image_filename, image_local_path, image_url, image_sha256,
            image_size_bytes, raw_payload
        FROM reports
    """)
    conn.execute("DROP TABLE reports")
    conn.execute("ALTER TABLE reports_new RENAME TO reports")


def init_db() -> None:
    """Tạo bảng reports và messages_dedup nếu chưa có, migrate các cột mới."""
    with get_db_connection() as conn:
        _create_reports_table(conn)

        # Tự động migrate thêm cột nếu bảng đã tồn tại từ trước
        cursor = conn.execute("PRAGMA table_info(reports)")
        existing_cols = {row["name"] for row in cursor.fetchall()}
        if "status_version" not in existing_cols:
            conn.execute("ALTER TABLE reports ADD COLUMN status_version INTEGER DEFAULT 1")
        if "image_sha256" not in existing_cols:
            conn.execute("ALTER TABLE reports ADD COLUMN image_sha256 TEXT")
        if "image_size_bytes" not in existing_cols:
            conn.execute("ALTER TABLE reports ADD COLUMN image_size_bytes INTEGER")

        _migrate_reports_status_default(conn)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages_dedup (
                message_id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                sequence_number INTEGER NOT NULL,
                operation_type TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                status TEXT NOT NULL,
                error_code TEXT,
                result_data TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                processed_at TEXT NOT NULL
            );
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_reports_received_at 
            ON reports (server_received_at DESC);
        """)

        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_client_seq 
            ON messages_dedup (client_id, sequence_number);
        """)

        conn.commit()
    logger.info("Đã kiểm tra cấu trúc bảng SQLite (reports, messages_dedup).")


def save_image(filename: str, content: bytes) -> Tuple[str, str, str]:
    dest = UPLOADS_DIR / filename
    with open(dest, "wb") as f:
        f.write(content)
    local_path = str(dest.resolve())
    image_url = f"/uploads/{dest.name}"
    logger.info(f"[CRUD][SAVE_IMAGE] {filename} ({len(content)} bytes) -> {local_path}")
    return filename, local_path, image_url


def _safe_json(val: Any) -> str:
    if val is None:
        return "[]"
    if isinstance(val, (list, dict)):
        return json.dumps(val, ensure_ascii=False)
    return str(val)


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    try:
        raw_payload = json.loads(row["raw_payload"]) if row["raw_payload"] else {}
    except Exception:
        raw_payload = {}

    try:
        vulnerable = json.loads(row["vulnerable_groups"]) if row["vulnerable_groups"] else []
    except Exception:
        vulnerable = []

    try:
        ai_tags = json.loads(row["ai_tags"]) if row["ai_tags"] else []
    except Exception:
        ai_tags = []

    return {
        "id": row["id"],
        "serverReceivedAt": row["server_received_at"],
        "createdAt": row["created_at"],
        "lat": row["lat"],
        "lng": row["lng"],
        "trappedCount": row["trapped_count"],
        "injuredCount": row["injured_count"],
        "vulnerableGroups": vulnerable,
        "description": row["description"],
        "aiTags": ai_tags,
        "sendMode": row["send_mode"],
        "status": row["status"],
        "statusVersion": row["status_version"] if "status_version" in row.keys() else 1,
        "imageFilename": row["image_filename"],
        "imageLocalPath": row["image_local_path"],
        "imageUrl": row["image_url"],
        "imageSha256": row["image_sha256"] if "image_sha256" in row.keys() else None,
        "payload": raw_payload,
    }


def save_report(
    meta: Dict[str, Any],
    image_filename: Optional[str] = None,
    image_local_path: Optional[str] = None,
    image_url: Optional[str] = None,
    image_sha256: Optional[str] = None,
    image_size_bytes: Optional[int] = None,
    connection: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    if connection is None:
        with get_db_connection() as conn:
            return save_report(
                meta,
                image_filename,
                image_local_path,
                image_url,
                image_sha256,
                image_size_bytes,
                connection=conn,
            )

    conn = connection
    rec_id = str(meta.get("id") or f"rec_{int(datetime.now().timestamp() * 1000)}")
    server_received_at = datetime.now().isoformat()
    created_at = str(meta.get("createdAt") or meta.get("createdAtMs") or "")
    
    lat = meta.get("lat")
    lat_val = float(lat) if lat is not None else None
    lng = meta.get("lng")
    lng_val = float(lng) if lng is not None else None

    trapped = int(meta.get("trappedCount", 0) or 0)
    injured = int(meta.get("injuredCount", 0) or 0)
    vulnerable_json = _safe_json(meta.get("vulnerableGroups"))
    desc = meta.get("description") or meta.get("note") or ""
    
    ai_tags_val = meta.get("aiTags")
    if not ai_tags_val and meta.get("label"):
        ai_tags_val = [{"label": meta.get("label"), "confidence": meta.get("confidence", 0.0)}]
    ai_tags_json = _safe_json(ai_tags_val)
    
    send_mode = meta.get("sendMode") or meta.get("mode") or "unknown"
    status_val = meta.get("status") or "processing"
    raw_payload_json = json.dumps(meta, ensure_ascii=False)

    cur = conn.execute("SELECT id, status, status_version FROM reports WHERE id = ?", (rec_id,))
    existing = cur.fetchone()
    action = "UPDATE" if existing else "INSERT"

    conn.execute(
        """
        INSERT INTO reports (
            id, server_received_at, created_at, lat, lng,
            trapped_count, injured_count, vulnerable_groups,
            description, ai_tags, send_mode, status, status_version,
            image_filename, image_local_path, image_url, image_sha256,
            image_size_bytes, raw_payload
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            server_received_at=excluded.server_received_at,
            created_at=excluded.created_at,
            lat=COALESCE(excluded.lat, reports.lat),
            lng=COALESCE(excluded.lng, reports.lng),
            trapped_count=COALESCE(excluded.trapped_count, reports.trapped_count),
            injured_count=COALESCE(excluded.injured_count, reports.injured_count),
            vulnerable_groups=COALESCE(excluded.vulnerable_groups, reports.vulnerable_groups),
            description=COALESCE(excluded.description, reports.description),
            ai_tags=COALESCE(excluded.ai_tags, reports.ai_tags),
            send_mode=COALESCE(excluded.send_mode, reports.send_mode),
            image_filename=COALESCE(excluded.image_filename, reports.image_filename),
            image_local_path=COALESCE(excluded.image_local_path, reports.image_local_path),
            image_url=COALESCE(excluded.image_url, reports.image_url),
            image_sha256=COALESCE(excluded.image_sha256, reports.image_sha256),
            image_size_bytes=COALESCE(excluded.image_size_bytes, reports.image_size_bytes),
            raw_payload=excluded.raw_payload;
        """,
        (
            rec_id,
            server_received_at,
            created_at,
            lat_val,
            lng_val,
            trapped,
            injured,
            vulnerable_json,
            desc,
            ai_tags_json,
            send_mode,
            status_val,
            image_filename,
            image_local_path,
            image_url,
            image_sha256,
            image_size_bytes,
            raw_payload_json,
        ),
    )

    logger.info(
        f"[CRUD][{action}] Report ID={rec_id} | GPS=({lat_val}, {lng_val}) | "
        f"Kẹt={trapped}, Thương={injured} | Ảnh={image_filename or 'None'} | "
        f"SHA={image_sha256 or 'None'} | Size={image_size_bytes or 0}B"
    )

    row = conn.execute("SELECT * FROM reports WHERE id = ?", (rec_id,)).fetchone()
    return (_row_to_dict(row) if row else None) or {
        "id": rec_id,
        "serverReceivedAt": server_received_at,
        "imageUrl": image_url,
        "imageLocalPath": image_local_path,
        "payload": meta,
    }


def get_reports(limit: int = 100) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM reports ORDER BY server_received_at DESC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()
        logger.info(f"[CRUD][SELECT] Lấy danh sách báo cáo (limit={limit}) -> Tìm thấy {len(rows)} bản ghi")
        return [_row_to_dict(r) for r in rows]


def get_report_by_id(report_id: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
        row = cursor.fetchone()
        logger.info(f"[CRUD][SELECT] Tìm báo cáo ID={report_id} -> {'Tìm thấy' if row else 'Không tồn tại'}")
        return _row_to_dict(row) if row else None


def clear_reports() -> int:
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM reports")
        count = cursor.fetchone()[0]
        conn.execute("DELETE FROM reports")
        conn.execute("DELETE FROM messages_dedup")
        conn.commit()
    logger.info(f"[CRUD][DELETE] Đã xóa sạch {count} báo cáo và toàn bộ nhật ký messages_dedup.")
    return count


def process_sync_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Xử lý danh sách message theo contact_connect.md trong transaction an toàn."""
    results = []
    now_utc = datetime.now(timezone.utc)
    logger.info(f"[SYNC] Bắt đầu xử lý batch {len(messages)} messages")

    with get_db_connection() as conn:
        for msg in messages:
            msg_id = msg.get("message_id")
            client_id = msg.get("client_id")
            seq_num = msg.get("sequence_number")
            op_type = msg.get("operation_type")
            created_at = msg.get("created_at")
            expires_at = msg.get("expires_at")
            sent_hash = msg.get("payload_hash")
            payload = msg.get("payload")

            if not all([msg_id, client_id, seq_num is not None, op_type, created_at, sent_hash, payload is not None]):
                logger.warning(f"[SYNC][REJECTED] msg={msg_id or 'unknown'} code=INVALID_PAYLOAD")
                results.append({
                    "message_id": msg_id or "unknown",
                    "status": "rejected",
                    "retryable": False,
                    "code": "INVALID_PAYLOAD",
                    "result": None,
                })
                continue

            # 1. Kiểm tra canonical hash theo RFC 8785
            try:
                computed_hash = compute_payload_hash(payload)
            except (TypeError, ValueError):
                results.append({
                    "message_id": msg_id,
                    "status": "rejected",
                    "retryable": False,
                    "code": "INVALID_PAYLOAD",
                    "result": {"error": "payload không hợp lệ theo RFC 8785"},
                })
                continue
            if computed_hash != sent_hash:
                logger.warning(f"[SYNC][REJECTED] msg={msg_id} code=INVALID_PAYLOAD hash mismatch")
                results.append({
                    "message_id": msg_id,
                    "status": "rejected",
                    "retryable": False,
                    "code": "INVALID_PAYLOAD",
                    "result": {"error": "payload_hash không khớp canonical JCS"},
                })
                continue

            # 2. Kiểm tra hạn message
            if expires_at:
                try:
                    exp_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                    if exp_dt < now_utc:
                        logger.warning(f"[SYNC][REJECTED] msg={msg_id} code=EXPIRED")
                        results.append({
                            "message_id": msg_id,
                            "status": "rejected",
                            "retryable": False,
                            "code": "EXPIRED",
                            "result": None,
                        })
                        continue
                except Exception:
                    pass

            # 3. Kiểm tra idempotency message_id
            cursor = conn.execute(
                "SELECT payload_hash, status, result_data FROM messages_dedup WHERE message_id = ?",
                (msg_id,),
            )
            existing_msg = cursor.fetchone()
            if existing_msg:
                if existing_msg["payload_hash"] == sent_hash:
                    # Trùng ID + trùng hash -> duplicate + trả kết quả cũ
                    logger.debug(f"[SYNC][DUPLICATE] msg={msg_id}")
                    results.append({
                        "message_id": msg_id,
                        "status": "duplicate",
                        "retryable": False,
                        "code": None,
                        "result": json.loads(existing_msg["result_data"]) if existing_msg["result_data"] else None,
                    })
                    continue
                else:
                    # Trùng ID nhưng khác hash -> rejected
                    logger.warning(f"[SYNC][REJECTED] msg={msg_id} code=ID_REUSED_WITH_DIFFERENT_PAYLOAD")
                    results.append({
                        "message_id": msg_id,
                        "status": "rejected",
                        "retryable": False,
                        "code": "ID_REUSED_WITH_DIFFERENT_PAYLOAD",
                        "result": None,
                    })
                    continue

            # 4. Kiểm tra tái sử dụng (client_id, sequence_number)
            cursor = conn.execute(
                "SELECT message_id FROM messages_dedup WHERE client_id = ? AND sequence_number = ?",
                (client_id, seq_num),
            )
            existing_seq = cursor.fetchone()
            if existing_seq and existing_seq["message_id"] != msg_id:
                logger.warning(f"[SYNC][REJECTED] msg={msg_id} code=SEQUENCE_REUSED")
                results.append({
                    "message_id": msg_id,
                    "status": "rejected",
                    "retryable": False,
                    "code": "SEQUENCE_REUSED",
                    "result": None,
                })
                continue

            # 5. Xử lý nghiệp vụ theo operation_type
            if op_type == "CREATE_RESCUE_RECORD":
                rec_res = save_report(payload, connection=conn)
                res_data = {"record_id": rec_res["id"], "serverReceivedAt": rec_res["serverReceivedAt"]}
                
                conn.execute(
                    """
                    INSERT INTO messages_dedup (
                        message_id, client_id, sequence_number, operation_type,
                        payload_hash, status, error_code, result_data,
                        created_at, expires_at, processed_at
                    ) VALUES (?, ?, ?, ?, ?, 'accepted', NULL, ?, ?, ?, ?)
                    """,
                    (
                        msg_id, client_id, seq_num, op_type,
                        sent_hash, json.dumps(res_data),
                        created_at, expires_at, datetime.now(timezone.utc).isoformat(),
                    ),
                )
                conn.commit()
                logger.info(f"[SYNC][ACCEPTED] msg={msg_id} op=CREATE_RESCUE_RECORD record={res_data['record_id']}")

                results.append({
                    "message_id": msg_id,
                    "status": "accepted",
                    "retryable": False,
                    "code": None,
                    "result": res_data,
                })

            elif op_type == "UPDATE_RESCUE_STATUS":
                target_id = payload.get("id")
                new_status = payload.get("status")
                new_version = payload.get("statusVersion")

                if not target_id or new_status not in VALID_RESCUE_STATUS_ORDER or not isinstance(new_version, int):
                    logger.warning(f"[SYNC][REJECTED] msg={msg_id} op=UPDATE_RESCUE_STATUS code=INVALID_PAYLOAD")
                    results.append({
                        "message_id": msg_id,
                        "status": "rejected",
                        "retryable": False,
                        "code": "INVALID_PAYLOAD",
                        "result": None,
                    })
                    continue

                rep_cur = conn.execute("SELECT status, status_version FROM reports WHERE id = ?", (target_id,))
                current_rep = rep_cur.fetchone()
                if not current_rep:
                    logger.warning(f"[SYNC][REJECTED] msg={msg_id} code=REPORT_NOT_FOUND target={target_id}")
                    results.append({
                        "message_id": msg_id,
                        "status": "rejected",
                        "retryable": False,
                        "code": "REPORT_NOT_FOUND",
                        "result": {"error": f"Không tìm thấy báo cáo {target_id}"},
                    })
                    continue

                curr_status = current_rep["status"]
                curr_version = current_rep["status_version"] or 1

                # statusVersion phải lớn hơn version hiện tại
                if new_version <= curr_version:
                    logger.warning(f"[SYNC][REJECTED] msg={msg_id} code=INVALID_STATUS_VERSION v{new_version}<=v{curr_version}")
                    results.append({
                        "message_id": msg_id,
                        "status": "rejected",
                        "retryable": False,
                        "code": "INVALID_STATUS_VERSION",
                        "result": {"error": f"statusVersion {new_version} <= hiện tại {curr_version}"},
                    })
                    continue

                # Chỉ được tiến về phía trước: processing -> dispatched -> resolved
                curr_rank = VALID_RESCUE_STATUS_ORDER.get(curr_status, 1)
                new_rank = VALID_RESCUE_STATUS_ORDER.get(new_status, 1)
                if new_rank < curr_rank:
                    logger.warning(f"[SYNC][REJECTED] msg={msg_id} code=INVALID_STATUS_TRANSITION {curr_status}->{new_status}")
                    results.append({
                        "message_id": msg_id,
                        "status": "rejected",
                        "retryable": False,
                        "code": "INVALID_STATUS_TRANSITION",
                        "result": {"error": f"Không thể lùi trạng thái từ {curr_status} về {new_status}"},
                    })
                    continue

                conn.execute(
                    "UPDATE reports SET status = ?, status_version = ? WHERE id = ?",
                    (new_status, new_version, target_id),
                )

                res_data = {"id": target_id, "status": new_status, "statusVersion": new_version}

                conn.execute(
                    """
                    INSERT INTO messages_dedup (
                        message_id, client_id, sequence_number, operation_type,
                        payload_hash, status, error_code, result_data,
                        created_at, expires_at, processed_at
                    ) VALUES (?, ?, ?, ?, ?, 'accepted', NULL, ?, ?, ?, ?)
                    """,
                    (
                        msg_id, client_id, seq_num, op_type,
                        sent_hash, json.dumps(res_data),
                        created_at, expires_at, datetime.now(timezone.utc).isoformat(),
                    ),
                )
                conn.commit()
                logger.info(f"[SYNC][ACCEPTED] msg={msg_id} op=UPDATE_RESCUE_STATUS {target_id}: {curr_status}->v{new_version} {new_status}")

                results.append({
                    "message_id": msg_id,
                    "status": "accepted",
                    "retryable": False,
                    "code": None,
                    "result": res_data,
                })

            else:
                logger.warning(f"[SYNC][REJECTED] msg={msg_id} code=UNSUPPORTED_OPERATION op={op_type}")
                results.append({
                    "message_id": msg_id,
                    "status": "rejected",
                    "retryable": False,
                    "code": "UNSUPPORTED_OPERATION",
                    "result": None,
                })

    accepted = sum(1 for r in results if r["status"] == "accepted")
    rejected = sum(1 for r in results if r["status"] == "rejected")
    duped = sum(1 for r in results if r["status"] == "duplicate")
    logger.info(f"[SYNC] Batch xong: {accepted} accepted, {rejected} rejected, {duped} duplicate")
    return results
