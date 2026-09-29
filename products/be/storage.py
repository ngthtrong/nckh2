import json
import logging
import math
import re
import secrets
import shutil
import sqlite3
import zipfile
from contextlib import closing, contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from config import DB_FILE, UPLOADS_DIR
from canonical import compute_payload_hash

logger = logging.getLogger("rescue_mock_server")

VALID_RESCUE_STATUS_ORDER = {
    "processing": 1,
    "dispatched": 2,
    "resolved": 3,
    "cancelled": 3,
}
# Trạng thái kết thúc: không đổi sang trạng thái nào khác (kể cả giữa hai trạng thái này).
TERMINAL_STATUSES = {"resolved", "cancelled"}
# Lý do đóng báo cáo (`cancelled`); dashboard bắt buộc chọn một lý do.
CLOSE_REASONS = {
    "duplicate": "Trùng với báo cáo khác",
    "false_alarm": "Báo giả / không xác minh được",
    "self_rescued": "Đã tự thoát hoặc được hỗ trợ khác",
    "no_contact": "Không liên lạc được, không tìm thấy hiện trường",
    "other": "Lý do khác",
}
NOTE_MAX_LENGTH = 1000
DESCRIPTION_MAX_LENGTH = 2000
PEOPLE_MAX = 10000
# id báo cáo là khóa idempotency, đồng thời là tên file ảnh: chỉ nhận ký tự an toàn.
REPORT_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def utc_now() -> str:
    """Thời điểm UTC dạng ISO 8601 có hậu tố Z (dùng cho các cột mới)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@contextmanager
def get_db_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(DB_FILE), check_same_thread=False, timeout=10.0)
    conn.row_factory = sqlite3.Row
    # WAL (bật trong init_db): đọc không chặn ghi. NORMAL đủ an toàn với WAL và ghi nhanh hơn.
    conn.execute("PRAGMA synchronous = NORMAL")
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
            raw_payload TEXT NOT NULL,
            first_received_at TEXT,
            updated_seq INTEGER DEFAULT 0,
            assigned_team_id INTEGER,
            location_source TEXT,
            close_reason TEXT,
            status_updated_at TEXT,
            owner_client_id TEXT
        );
    """)


# Cột thêm sau phiên bản đầu (dashboard quản lý); init_db() tự ALTER TABLE cho DB cũ.
_ADDED_REPORT_COLUMNS = {
    "status_version": "INTEGER DEFAULT 1",
    "image_sha256": "TEXT",
    "image_size_bytes": "INTEGER",
    "first_received_at": "TEXT",
    "updated_seq": "INTEGER DEFAULT 0",
    "assigned_team_id": "INTEGER",
    "location_source": "TEXT",
    "close_reason": "TEXT",
    "status_updated_at": "TEXT",
    "owner_client_id": "TEXT",
}


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
    with closing(sqlite3.connect(str(DB_FILE))) as conn:
        # Chế độ WAL lưu trong file DB: dashboard đọc toàn bảng không chặn app gửi báo cáo.
        conn.execute("PRAGMA journal_mode = WAL")
    with get_db_connection() as conn:
        _create_reports_table(conn)

        # Tự động migrate thêm cột nếu bảng đã tồn tại từ trước
        cursor = conn.execute("PRAGMA table_info(reports)")
        existing_cols = {row["name"] for row in cursor.fetchall()}
        for column, ddl in _ADDED_REPORT_COLUMNS.items():
            if column not in existing_cols:
                conn.execute(f"ALTER TABLE reports ADD COLUMN {column} {ddl}")

        _migrate_reports_status_default(conn)

        # Bù dữ liệu cho các cột dashboard trên DB cũ (không đổi dữ liệu đã có).
        conn.execute("UPDATE reports SET first_received_at = server_received_at WHERE first_received_at IS NULL")
        conn.execute("""
            UPDATE reports SET location_source = 'device'
            WHERE location_source IS NULL AND lat IS NOT NULL AND lng IS NOT NULL
        """)
        conn.execute("UPDATE reports SET updated_seq = rowid WHERE updated_seq IS NULL OR updated_seq = 0")

        # Nhật ký thao tác trên báo cáo: tiếp nhận, đổi trạng thái, giao đội, ghi chú, sửa vị trí.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS report_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                from_value TEXT,
                to_value TEXT,
                status_version INTEGER,
                actor TEXT,
                source TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_report_events_report ON report_events (report_id, id)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                phone TEXT,
                members INTEGER,
                note TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
        """)

        # Tài khoản điều phối viên (xem accounts.py); mỗi phiên gắn với một tài khoản.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS operators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                display_name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'operator',
                active INTEGER NOT NULL DEFAULT 1,
                must_change_password INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                last_login_at TEXT
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                operator TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                operator_id INTEGER
            );
        """)
        session_cols = {row["name"] for row in conn.execute("PRAGMA table_info(sessions)")}
        if "operator_id" not in session_cols:
            # Phiên của bản mật khẩu chung cũ không gắn tài khoản: bỏ, người dùng đăng nhập lại.
            conn.execute("ALTER TABLE sessions ADD COLUMN operator_id INTEGER")
        conn.execute("DELETE FROM sessions WHERE operator_id IS NULL")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_operator ON sessions (operator_id)")

        # seq: bộ đếm thay đổi không bao giờ giảm (kể cả sau khi xóa dữ liệu);
        # epoch: đổi mỗi lần xóa toàn bộ để dashboard biết phải tải lại từ đầu.
        conn.execute("CREATE TABLE IF NOT EXISTS server_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        max_seq = conn.execute("SELECT COALESCE(MAX(updated_seq), 0) FROM reports").fetchone()[0]
        conn.execute("INSERT OR IGNORE INTO server_meta (key, value) VALUES ('seq', ?)", (str(max_seq),))
        conn.execute(
            "UPDATE server_meta SET value = ? WHERE key = 'seq' AND CAST(value AS INTEGER) < ?",
            (str(max_seq), max_seq),
        )
        conn.execute("INSERT OR IGNORE INTO server_meta (key, value) VALUES ('epoch', ?)", (secrets.token_hex(8),))
        # cluster_rev: tăng khi dữ liệu đầu vào của phân cụm đổi (xem get_cluster_version).
        conn.execute("INSERT OR IGNORE INTO server_meta (key, value) VALUES ('cluster_rev', '0')")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_updated_seq ON reports (updated_seq)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_first_received ON reports (first_received_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_status ON reports (status)")

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
        conn.execute("CREATE INDEX IF NOT EXISTS idx_dedup_processed ON messages_dedup (processed_at)")

        conn.commit()
    logger.info("Đã kiểm tra cấu trúc bảng SQLite (reports, messages_dedup, report_events, teams, sessions).")


def _next_seq(conn: sqlite3.Connection) -> int:
    conn.execute("UPDATE server_meta SET value = CAST(value AS INTEGER) + 1 WHERE key = 'seq'")
    return int(conn.execute("SELECT value FROM server_meta WHERE key = 'seq'").fetchone()[0])


def _bump_cluster_rev(conn: sqlite3.Connection) -> None:
    conn.execute("UPDATE server_meta SET value = CAST(value AS INTEGER) + 1 WHERE key = 'cluster_rev'")


def get_cluster_version() -> str:
    """Phiên bản dữ liệu đầu vào của phân cụm: đổi khi có báo cáo mới/bổ sung, đổi trạng
    thái hoặc vị trí, hay xóa toàn bộ; không đổi khi giao đội hay ghi chú."""
    with get_db_connection() as conn:
        meta = dict(conn.execute("SELECT key, value FROM server_meta WHERE key IN ('epoch', 'cluster_rev')").fetchall())
    return f"{meta.get('epoch')}:{meta.get('cluster_rev')}"


def _add_event(
    conn: sqlite3.Connection,
    report_id: str,
    kind: str,
    *,
    source: str,
    actor: Optional[str] = None,
    from_value: Any = None,
    to_value: Any = None,
    status_version: Optional[int] = None,
    note: Optional[str] = None,
) -> None:
    conn.execute(
        """
        INSERT INTO report_events (report_id, kind, from_value, to_value, status_version, actor, source, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report_id, kind,
            None if from_value is None else str(from_value),
            None if to_value is None else str(to_value),
            status_version, actor, source, note, utc_now(),
        ),
    )


def _safe_filename(filename: str) -> str:
    """Tên file an toàn trong UPLOADS_DIR: bỏ thư mục, chỉ giữ chữ/số/._- (chặn path traversal
    qua ``meta.id`` hoặc tên file do client gửi)."""
    name = re.sub(r"[^A-Za-z0-9._-]", "_", filename.replace("\\", "/").split("/")[-1]).lstrip(".")
    return name[:200] or "photo.jpg"


def save_image(filename: str, content: bytes) -> Tuple[str, str, str]:
    filename = _safe_filename(filename)
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
        "imageSizeBytes": row["image_size_bytes"],
        "firstReceivedAt": row["first_received_at"],
        "updatedSeq": row["updated_seq"],
        "assignedTeamId": row["assigned_team_id"],
        "locationSource": row["location_source"],
        "closeReason": row["close_reason"],
        "statusUpdatedAt": row["status_updated_at"],
        # Số gọi lại người báo (SMS, tổng đài); chỉ trả cho dashboard đã đăng nhập.
        "contactPhone": raw_payload.get("contactPhone") if isinstance(raw_payload, dict) else None,
        "payload": raw_payload,
    }


def _report_columns(meta: Dict[str, Any]) -> Dict[str, Any]:
    """Giá trị các cột nội dung của ``reports`` lấy từ payload (đã qua ``validate_report_payload``
    với dữ liệu từ app; dữ liệu nạp sẵn như seed có thêm vài tên trường cũ)."""
    lat, lng = meta.get("lat"), meta.get("lng")
    located = lat is not None and lng is not None
    ai_tags = meta.get("aiTags")
    if not ai_tags and meta.get("label"):
        ai_tags = [{"label": meta.get("label"), "confidence": meta.get("confidence", 0.0)}]
    return {
        "created_at": str(meta.get("createdAt") or meta.get("createdAtMs") or ""),
        "lat": float(lat) if located else None,
        "lng": float(lng) if located else None,
        "trapped_count": int(meta.get("trappedCount", 0) or 0),
        "injured_count": int(meta.get("injuredCount", 0) or 0),
        "vulnerable_groups": _safe_json(meta.get("vulnerableGroups")),
        "description": meta.get("description") or meta.get("note") or "",
        "ai_tags": _safe_json(ai_tags),
        "send_mode": meta.get("sendMode") or meta.get("mode") or "unknown",
        "location_source": "device" if located else None,
    }


def _is_blank(value: Any) -> bool:
    return value is None or value in ("", "[]", "unknown")


# Chủ báo cáo đặc biệt: báo cáo tạo từ nguồn không phải app, không thiết bị nào nhận làm của mình.
OWNER_DASHBOARD = "@dashboard"
OWNER_SMS = "@sms"
OWNER_SEED = "@seed"
CLIENT_ID_MAX_LENGTH = 128


def merge_allowed(owner: Optional[str], client_id: Optional[str], trusted: bool = False) -> bool:
    """Ai được bổ sung báo cáo đã có cùng id (docs/contact_connect.md, mục chủ báo cáo).

    Chỉ thiết bị đã tạo báo cáo (``client_id`` trùng chủ) hoặc nguồn tin cậy (SMS gateway có
    token, dashboard) mới được điền trường trống/gắn ảnh. Báo cáo chưa có chủ (tin SMS định
    dạng SOS của app, dữ liệu cũ) được thiết bị đầu tiên gửi kèm ``client_id`` nhận làm chủ.
    Nhờ vậy người ngoài biết id (vd. id đi trong SMS) không sửa được vị trí, số người, ảnh.
    """
    if trusted:
        return True
    if not client_id:
        return False
    return owner is None or owner == client_id


def report_owner(report_id: str) -> Tuple[bool, Optional[str]]:
    """(báo cáo đã tồn tại?, chủ báo cáo)."""
    with get_db_connection() as conn:
        row = conn.execute("SELECT owner_client_id FROM reports WHERE id = ?", (report_id,)).fetchone()
    return (row is not None, row["owner_client_id"] if row else None)


def save_report(
    meta: Dict[str, Any],
    image_filename: Optional[str] = None,
    image_local_path: Optional[str] = None,
    image_url: Optional[str] = None,
    image_sha256: Optional[str] = None,
    image_size_bytes: Optional[int] = None,
    connection: Optional[sqlite3.Connection] = None,
    source: str = "app",
    actor: Optional[str] = None,
    client_id: Optional[str] = None,
    trusted: bool = False,
) -> Dict[str, Any]:
    """Tạo báo cáo theo ``meta.id``, hoặc bổ sung cho báo cáo đã có.

    Báo cáo mới luôn bắt đầu ở ``processing`` (trạng thái do client gửi bị bỏ qua) và có
    chủ là ``client_id``. Khi ``meta.id`` đã tồn tại (upload ảnh sau metadata, SMS rồi app
    đồng bộ, gửi lại): chỉ chủ báo cáo hoặc nguồn ``trusted`` được bổ sung (xem
    ``merge_allowed``), người khác nhận ``REPORT_ID_CONFLICT``. Dữ liệu đã lưu được giữ
    nguyên, chỉ điền các trường còn trống (số người chỉ điền khi lần trước không gửi field
    đó, vì ``0`` là giá trị thật); ảnh chỉ gắn khi báo cáo chưa có ảnh; GPS của thiết bị
    thay vị trí điều phối viên nhập tay.
    """
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
                source=source,
                actor=actor,
                client_id=client_id,
                trusted=trusted,
            )

    conn = connection
    rec_id = str(meta.get("id") or "")
    if not rec_id:
        raise StatusUpdateError("INVALID_PAYLOAD", "Thiếu id báo cáo")
    columns = _report_columns(meta)
    image = {
        "image_filename": image_filename,
        "image_local_path": image_local_path,
        "image_url": image_url,
        "image_sha256": image_sha256,
        "image_size_bytes": image_size_bytes,
    }
    existing = conn.execute("SELECT * FROM reports WHERE id = ?", (rec_id,)).fetchone()

    if existing is None:
        now = utc_now()
        row = {
            "id": rec_id,
            "server_received_at": now,
            "first_received_at": now,
            "status": "processing",
            "status_version": 1,
            "raw_payload": json.dumps(meta, ensure_ascii=False),
            "owner_client_id": client_id,
            **columns,
            **image,
            "updated_seq": _next_seq(conn),
        }
        conn.execute(
            f"INSERT INTO reports ({', '.join(row)}) VALUES ({', '.join('?' * len(row))})",
            tuple(row.values()),
        )
        _add_event(conn, rec_id, "received", source=source, actor=actor, to_value="processing")
        _bump_cluster_rev(conn)
        action = "INSERT"
    else:
        owner = existing["owner_client_id"]
        if not merge_allowed(owner, client_id, trusted):
            logger.warning(f"[CRUD][CONFLICT] Report ID={rec_id}: client khác chủ báo cáo, không bổ sung")
            raise StatusUpdateError("REPORT_ID_CONFLICT", "id báo cáo đã thuộc về thiết bị/nguồn khác")
        try:
            stored_payload = json.loads(existing["raw_payload"] or "{}")
        except ValueError:
            stored_payload = {}
        if not isinstance(stored_payload, dict):
            stored_payload = {}
        updates: Dict[str, Any] = {}
        if owner is None and client_id and not trusted:
            updates["owner_client_id"] = client_id
        for column in ("created_at", "vulnerable_groups", "description", "ai_tags", "send_mode"):
            if _is_blank(existing[column]) and not _is_blank(columns[column]):
                updates[column] = columns[column]
        for column, key in (("trapped_count", "trappedCount"), ("injured_count", "injuredCount")):
            if key not in stored_payload and key in meta:
                updates[column] = columns[column]
        if columns["lat"] is not None and (existing["lat"] is None or existing["location_source"] == "manual"):
            updates.update(lat=columns["lat"], lng=columns["lng"], location_source="device")
        if image_url and not existing["image_url"]:
            updates.update(image)
            _add_event(conn, rec_id, "image", source=source, note=f"{image_size_bytes or 0} bytes")
        merged_payload = {**meta, **stored_payload}
        if merged_payload != stored_payload:
            updates["raw_payload"] = json.dumps(merged_payload, ensure_ascii=False)
        if updates:
            _bump_cluster_rev(conn)
            updates["updated_seq"] = _next_seq(conn)
            conn.execute(
                f"UPDATE reports SET {', '.join(f'{k} = ?' for k in updates)} WHERE id = ?",
                (*updates.values(), rec_id),
            )
        action = f"MERGE({', '.join(k for k in updates if k != 'updated_seq') or 'không đổi'})"

    logger.info(
        f"[CRUD][{action}] Report ID={rec_id} | GPS=({columns['lat']}, {columns['lng']}) | "
        f"Ảnh={image_filename or 'None'} | Size={image_size_bytes or 0}B"
    )
    return _row_to_dict(conn.execute("SELECT * FROM reports WHERE id = ?", (rec_id,)).fetchone())


def get_reports(limit: Optional[int] = None, active_only: bool = False) -> List[Dict[str, Any]]:
    """Báo cáo mới nhận trước. Mặc định lấy tất cả; ``active_only`` bỏ báo cáo đã kết thúc
    (đầu vào của phân cụm), để báo cáo cũ chưa xử lý không bị cắt mất khi dữ liệu nhiều."""
    sql = "SELECT * FROM reports"
    if active_only:
        sql += f" WHERE status NOT IN ({', '.join('?' * len(TERMINAL_STATUSES))})"
    sql += " ORDER BY first_received_at DESC, id"
    params: List[Any] = sorted(TERMINAL_STATUSES) if active_only else []
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    with get_db_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    logger.debug(f"[CRUD][SELECT] Lấy danh sách báo cáo (active_only={active_only}) -> {len(rows)} bản ghi")
    return [_row_to_dict(r) for r in rows]


def get_report_by_id(report_id: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
        row = cursor.fetchone()
        logger.debug(f"[CRUD][SELECT] Tìm báo cáo ID={report_id} -> {'Tìm thấy' if row else 'Không tồn tại'}")
        return _row_to_dict(row) if row else None


STATUS_QUERY_LIMIT = 100


def get_report_statuses(report_ids: List[str]) -> List[Dict[str, Any]]:
    """Trạng thái điều phối của nhiều báo cáo; id không tồn tại bị bỏ qua."""
    ids = list(dict.fromkeys(i for i in report_ids if i))[:STATUS_QUERY_LIMIT]
    if not ids:
        return []
    placeholders = ",".join("?" * len(ids))
    with get_db_connection() as conn:
        rows = conn.execute(
            f"SELECT id, status, status_version FROM reports WHERE id IN ({placeholders})",
            ids,
        ).fetchall()
    return [
        {"id": row["id"], "status": row["status"], "statusVersion": row["status_version"]}
        for row in rows
    ]


def get_changes_since(seq: int, limit: int = 5000) -> Dict[str, Any]:
    """Báo cáo đổi sau ``seq`` (tạo mới, đổi trạng thái, giao đội, ghi chú, sửa vị trí).

    ``cursor`` là giá trị gửi lại ở lần hỏi sau; ``epoch`` đổi khi dữ liệu bị xóa toàn bộ.
    ``hasMore`` bật khi còn báo cáo vượt ``limit``.
    """
    with get_db_connection() as conn:
        meta = {row["key"]: row["value"] for row in conn.execute("SELECT key, value FROM server_meta")}
        rows = conn.execute(
            "SELECT * FROM reports WHERE updated_seq > ? ORDER BY updated_seq LIMIT ?",
            (max(0, seq), limit + 1),
        ).fetchall()
    has_more = len(rows) > limit
    rows = rows[:limit]
    # Đọc seq trước rồi mới đọc báo cáo: thay đổi xen giữa sẽ được gửi lại lần sau, không bị bỏ sót.
    last = rows[-1]["updated_seq"] if rows else 0
    cursor = last if has_more else max(int(meta.get("seq", 0)), last, seq)
    return {
        "epoch": meta.get("epoch"),
        "cursor": cursor,
        "hasMore": has_more,
        "reports": [_row_to_dict(r) for r in rows],
    }


def clear_reports() -> int:
    """Xóa toàn bộ báo cáo, nhật ký chống trùng và nhật ký thao tác; giữ danh sách đội."""
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM reports")
        count = cursor.fetchone()[0]
        conn.execute("DELETE FROM reports")
        conn.execute("DELETE FROM messages_dedup")
        conn.execute("DELETE FROM report_events")
        conn.execute("UPDATE server_meta SET value = ? WHERE key = 'epoch'", (secrets.token_hex(8),))
        conn.commit()
    logger.info(f"[CRUD][DELETE] Đã xóa sạch {count} báo cáo, messages_dedup và report_events.")
    return count


class StatusUpdateError(Exception):
    """Cập nhật trạng thái bị từ chối; ``code`` theo docs/contact_connect.md."""

    def __init__(self, code: str, message: Optional[str] = None) -> None:
        super().__init__(message or code)
        self.code = code
        self.message = message


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _is_count(value: Any) -> bool:
    return _is_number(value) and float(value).is_integer() and 0 <= value <= PEOPLE_MAX


def _short_text(value: Any, limit: int) -> bool:
    return isinstance(value, str) and len(value) <= limit


def validate_report_payload(meta: Any) -> None:
    """Kiểm tra payload ``CREATE_RESCUE_RECORD`` (và ``meta`` của ``/api/reports``) trước khi ghi.

    Dữ liệu sai kiểu bị từ chối ``INVALID_PAYLOAD`` (không retry) thay vì gây HTTP 500,
    vì app coi 5xx là lỗi tạm và sẽ gửi lại message hỏng mãi.
    """
    def invalid(message: str) -> None:
        raise StatusUpdateError("INVALID_PAYLOAD", message)

    if not isinstance(meta, dict):
        invalid("payload phải là JSON object")
    if not isinstance(meta.get("id"), str) or not REPORT_ID_PATTERN.match(meta["id"]):
        invalid("id phải là chuỗi 1-128 ký tự gồm chữ, số, '.', '_', ':', '-'")
    lat, lng = meta.get("lat"), meta.get("lng")
    if (lat is None) != (lng is None):
        invalid("lat và lng phải cùng có giá trị hoặc cùng null")
    if lat is not None and not (_is_number(lat) and _is_number(lng) and abs(lat) <= 90 and abs(lng) <= 180):
        invalid("lat/lng phải là số trong phạm vi [-90, 90] / [-180, 180]")
    for name in ("trappedCount", "injuredCount"):
        if meta.get(name) is not None and not _is_count(meta[name]):
            invalid(f"{name} phải là số nguyên 0-{PEOPLE_MAX}")
    groups = meta.get("vulnerableGroups")
    if groups is not None and not (
        isinstance(groups, list) and len(groups) <= 20 and all(_short_text(g, 50) for g in groups)
    ):
        invalid("vulnerableGroups phải là mảng chuỗi")
    for name in ("description", "note"):
        if meta.get(name) is not None and not _short_text(meta[name], DESCRIPTION_MAX_LENGTH):
            invalid(f"{name} phải là chuỗi tối đa {DESCRIPTION_MAX_LENGTH} ký tự")
    tags = meta.get("aiTags")
    if tags is not None and not (
        isinstance(tags, list) and len(tags) <= 20 and all(
            isinstance(t, dict)
            and (t.get("label") is None or _short_text(t["label"], 50))
            and (t.get("confidence") is None or _is_number(t["confidence"]))
            for t in tags
        )
    ):
        invalid("aiTags phải là mảng {label, confidence}")
    created = meta.get("createdAt")
    if created is not None and not (_short_text(created, 64) or (_is_number(created) and not isinstance(created, float))):
        invalid("createdAt phải là chuỗi ISO 8601 hoặc epoch ms")
    for name, limit in (("sendMode", 32), ("imageSha256", 80), ("label", 50), ("clientId", CLIENT_ID_MAX_LENGTH)):
        if meta.get(name) is not None and not _short_text(meta[name], limit):
            invalid(f"{name} không hợp lệ")
    if meta.get("confidence") is not None and not _is_number(meta["confidence"]):
        invalid("confidence phải là số")


def _clean_note(note: Any) -> Optional[str]:
    if note is None:
        return None
    text = str(note).strip()
    if len(text) > NOTE_MAX_LENGTH:
        raise StatusUpdateError("INVALID_PAYLOAD", f"Ghi chú dài quá {NOTE_MAX_LENGTH} ký tự")
    return text or None


def _require_active_team(conn: sqlite3.Connection, team_id: Any) -> Dict[str, Any]:
    if not isinstance(team_id, int) or isinstance(team_id, bool):
        raise StatusUpdateError("INVALID_PAYLOAD", "teamId phải là số nguyên")
    row = conn.execute("SELECT * FROM teams WHERE id = ?", (team_id,)).fetchone()
    if not row:
        raise StatusUpdateError("TEAM_NOT_FOUND", f"Không có đội {team_id}")
    if not row["active"]:
        raise StatusUpdateError("TEAM_INACTIVE", f"Đội {row['name']} đang ngừng hoạt động")
    return dict(row)


def apply_status_update(
    conn: sqlite3.Connection,
    target_id: Any,
    new_status: Any,
    new_version: Any,
    *,
    actor: Optional[str] = None,
    source: str = "sync",
    note: Any = None,
    reason: Any = None,
    team_id: Any = None,
) -> Tuple[Dict[str, Any], str]:
    """Kiểm tra và ghi chuyển trạng thái (chưa commit). Trả về (kết quả, trạng thái cũ).

    Quy tắc dùng chung cho ``UPDATE_RESCUE_STATUS`` và dashboard:
    ``processing -> dispatched -> resolved``, hoặc đóng ``cancelled`` từ trạng thái
    chưa kết thúc. ``resolved``/``cancelled`` là trạng thái kết thúc.
    """
    if not target_id or new_status not in VALID_RESCUE_STATUS_ORDER or not isinstance(new_version, int):
        raise StatusUpdateError("INVALID_PAYLOAD")
    if reason is not None and reason not in CLOSE_REASONS:
        raise StatusUpdateError("INVALID_PAYLOAD", f"Lý do đóng không hợp lệ: {reason}")
    note = _clean_note(note)

    current_rep = conn.execute(
        "SELECT status, status_version, assigned_team_id FROM reports WHERE id = ?", (target_id,)
    ).fetchone()
    if not current_rep:
        raise StatusUpdateError("REPORT_NOT_FOUND", f"Không tìm thấy báo cáo {target_id}")

    curr_status = current_rep["status"]
    curr_version = current_rep["status_version"] or 1

    # statusVersion phải lớn hơn version hiện tại
    if new_version <= curr_version:
        raise StatusUpdateError(
            "INVALID_STATUS_VERSION", f"statusVersion {new_version} <= hiện tại {curr_version}"
        )

    # Chỉ được tiến về phía trước; trạng thái kết thúc không đổi sang trạng thái khác.
    curr_rank = VALID_RESCUE_STATUS_ORDER.get(curr_status, 1)
    new_rank = VALID_RESCUE_STATUS_ORDER.get(new_status, 1)
    if new_rank < curr_rank or (curr_status in TERMINAL_STATUSES and new_status != curr_status):
        raise StatusUpdateError(
            "INVALID_STATUS_TRANSITION", f"Không thể chuyển trạng thái từ {curr_status} sang {new_status}"
        )

    team = _require_active_team(conn, team_id) if team_id is not None else None
    close_reason = reason if new_status == "cancelled" else None

    conn.execute(
        """
        UPDATE reports SET status = ?, status_version = ?, status_updated_at = ?, updated_seq = ?,
            close_reason = COALESCE(?, close_reason),
            assigned_team_id = COALESCE(?, assigned_team_id)
        WHERE id = ?
        """,
        (new_status, new_version, utc_now(), _next_seq(conn), close_reason,
         team["id"] if team else None, target_id),
    )
    _bump_cluster_rev(conn)
    event_note = note
    if close_reason:
        event_note = CLOSE_REASONS[close_reason] + (f": {note}" if note else "")
    _add_event(conn, target_id, "status", source=source, actor=actor, from_value=curr_status,
               to_value=new_status, status_version=new_version, note=event_note)
    if team and team["id"] != current_rep["assigned_team_id"]:
        _add_event(conn, target_id, "assign", source=source, actor=actor,
                   from_value=current_rep["assigned_team_id"], to_value=team["id"], note=team["name"])
    return {"id": target_id, "status": new_status, "statusVersion": new_version}, curr_status


def update_report_status(
    report_id: str,
    new_status: str,
    new_version: int,
    *,
    actor: Optional[str] = None,
    note: Any = None,
    reason: Any = None,
    team_id: Any = None,
) -> Dict[str, Any]:
    """Cập nhật trạng thái từ dashboard điều phối (cùng quy tắc với UPDATE_RESCUE_STATUS)."""
    with get_db_connection() as conn:
        result, curr_status = apply_status_update(
            conn, report_id, new_status, new_version,
            actor=actor, source="dashboard", note=note, reason=reason, team_id=team_id,
        )
        conn.commit()
    logger.info(f"[CRUD][STATUS] {report_id}: {curr_status} -> v{new_version} {new_status} ({actor or '-'})")
    return result


def update_statuses_bulk(
    items: List[Dict[str, Any]],
    new_status: str,
    *,
    actor: Optional[str] = None,
    note: Any = None,
    reason: Any = None,
    team_id: Any = None,
) -> List[Dict[str, Any]]:
    """Đổi trạng thái đúng danh sách báo cáo điều phối viên đã xác nhận.

    Mỗi phần tử ``{"id", "statusVersion"}`` được xử lý độc lập; lỗi của một báo cáo
    không chặn các báo cáo khác. Trả về kết quả theo thứ tự đầu vào.
    """
    results: List[Dict[str, Any]] = []
    with get_db_connection() as conn:
        for item in items:
            report_id = item.get("id")
            try:
                result, _ = apply_status_update(
                    conn, report_id, new_status, item.get("statusVersion"),
                    actor=actor, source="dashboard", note=note, reason=reason, team_id=team_id,
                )
                results.append({"id": report_id, "ok": True, **result})
            except StatusUpdateError as err:
                results.append({"id": report_id, "ok": False, "code": err.code, "error": err.message})
        conn.commit()
    done = sum(1 for r in results if r["ok"])
    logger.info(f"[CRUD][STATUS][BULK] {done}/{len(results)} -> {new_status} ({actor or '-'})")
    return results


def _touch(conn: sqlite3.Connection, report_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    if not row:
        raise StatusUpdateError("REPORT_NOT_FOUND", f"Không tìm thấy báo cáo {report_id}")
    return row


def assign_team(report_id: str, team_id: Optional[int], *, actor: Optional[str]) -> Dict[str, Any]:
    """Giao (hoặc bỏ giao khi ``team_id`` là None) báo cáo cho một đội cứu hộ."""
    with get_db_connection() as conn:
        row = _touch(conn, report_id)
        team = _require_active_team(conn, team_id) if team_id is not None else None
        if row["status"] in TERMINAL_STATUSES:
            raise StatusUpdateError("REPORT_CLOSED", "Báo cáo đã kết thúc, không giao đội được")
        new_team_id = team["id"] if team else None
        if new_team_id != row["assigned_team_id"]:
            conn.execute(
                "UPDATE reports SET assigned_team_id = ?, updated_seq = ? WHERE id = ?",
                (new_team_id, _next_seq(conn), report_id),
            )
            _add_event(conn, report_id, "assign", source="dashboard", actor=actor,
                       from_value=row["assigned_team_id"], to_value=new_team_id,
                       note=team["name"] if team else "Bỏ giao đội")
        conn.commit()
        return _row_to_dict(_touch(conn, report_id))


def add_note(report_id: str, text: Any, *, actor: Optional[str]) -> Dict[str, Any]:
    note = _clean_note(text)
    if not note:
        raise StatusUpdateError("INVALID_PAYLOAD", "Ghi chú trống")
    with get_db_connection() as conn:
        _touch(conn, report_id)
        conn.execute("UPDATE reports SET updated_seq = ? WHERE id = ?", (_next_seq(conn), report_id))
        _add_event(conn, report_id, "note", source="dashboard", actor=actor, note=note)
        conn.commit()
    return {"id": report_id, "note": note}


def set_manual_location(
    report_id: str, lat: Any, lng: Any, *, actor: Optional[str], note: Any = None
) -> Dict[str, Any]:
    """Điều phối viên nhập vị trí (ví dụ báo cáo không có GPS, xác minh qua điện thoại)."""
    try:
        lat_val, lng_val = float(lat), float(lng)
    except (TypeError, ValueError):
        raise StatusUpdateError("INVALID_PAYLOAD", "lat/lng phải là số")
    if not (-90.0 <= lat_val <= 90.0 and -180.0 <= lng_val <= 180.0):
        raise StatusUpdateError("INVALID_PAYLOAD", "lat/lng ngoài phạm vi")
    note = _clean_note(note)
    with get_db_connection() as conn:
        row = _touch(conn, report_id)
        old = None if row["lat"] is None else f"{row['lat']:.6f},{row['lng']:.6f}"
        conn.execute(
            "UPDATE reports SET lat = ?, lng = ?, location_source = 'manual', updated_seq = ? WHERE id = ?",
            (lat_val, lng_val, _next_seq(conn), report_id),
        )
        _bump_cluster_rev(conn)
        _add_event(conn, report_id, "location", source="dashboard", actor=actor,
                   from_value=old, to_value=f"{lat_val:.6f},{lng_val:.6f}", note=note)
        conn.commit()
        return _row_to_dict(_touch(conn, report_id))


def get_report_events(report_id: str) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM report_events WHERE report_id = ? ORDER BY id", (report_id,)
        ).fetchall()
    return [_event_to_dict(r) for r in rows]


def get_all_events(kinds: Tuple[str, ...] = ("status",)) -> List[Dict[str, Any]]:
    placeholders = ",".join("?" * len(kinds))
    with get_db_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM report_events WHERE kind IN ({placeholders}) ORDER BY id", kinds
        ).fetchall()
    return [_event_to_dict(r) for r in rows]


def _event_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "reportId": row["report_id"],
        "kind": row["kind"],
        "from": row["from_value"],
        "to": row["to_value"],
        "statusVersion": row["status_version"],
        "actor": row["actor"],
        "source": row["source"],
        "note": row["note"],
        "at": row["created_at"],
    }


# ---------------------------------------------------------------- Đội cứu hộ

def _team_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "phone": row["phone"],
        "members": row["members"],
        "note": row["note"],
        "active": bool(row["active"]),
        "createdAt": row["created_at"],
        "activeAssignments": row["active_assignments"] if "active_assignments" in row.keys() else 0,
    }


def list_teams() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT t.*, (
                SELECT COUNT(*) FROM reports r
                WHERE r.assigned_team_id = t.id AND r.status IN ('processing', 'dispatched')
            ) AS active_assignments
            FROM teams t ORDER BY t.active DESC, t.name COLLATE NOCASE
        """).fetchall()
    return [_team_to_dict(r) for r in rows]


def _team_fields(data: Dict[str, Any], partial: bool) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    if "name" in data or not partial:
        name = str(data.get("name") or "").strip()
        if not name or len(name) > 80:
            raise StatusUpdateError("INVALID_PAYLOAD", "Tên đội phải có 1-80 ký tự")
        fields["name"] = name
    if "phone" in data:
        phone = str(data.get("phone") or "").strip()
        if len(phone) > 30:
            raise StatusUpdateError("INVALID_PAYLOAD", "Số điện thoại quá dài")
        fields["phone"] = phone or None
    if "members" in data:
        members = data.get("members")
        if members is not None and (not isinstance(members, int) or isinstance(members, bool) or not 0 <= members <= 1000):
            raise StatusUpdateError("INVALID_PAYLOAD", "Số thành viên không hợp lệ")
        fields["members"] = members
    if "note" in data:
        fields["note"] = _clean_note(data.get("note"))
    if "active" in data:
        fields["active"] = 1 if data.get("active") else 0
    return fields


def create_team(data: Dict[str, Any]) -> Dict[str, Any]:
    fields = _team_fields(data, partial=False)
    fields.setdefault("active", 1)
    fields["created_at"] = utc_now()
    columns = ", ".join(fields)
    with get_db_connection() as conn:
        try:
            cur = conn.execute(
                f"INSERT INTO teams ({columns}) VALUES ({', '.join('?' * len(fields))})",
                tuple(fields.values()),
            )
        except sqlite3.IntegrityError:
            raise StatusUpdateError("TEAM_NAME_TAKEN", f"Đã có đội tên {fields['name']}")
        conn.commit()
        team_id = cur.lastrowid
    return next(t for t in list_teams() if t["id"] == team_id)


def update_team(team_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    fields = _team_fields(data, partial=True)
    with get_db_connection() as conn:
        if not conn.execute("SELECT 1 FROM teams WHERE id = ?", (team_id,)).fetchone():
            raise StatusUpdateError("TEAM_NOT_FOUND", f"Không có đội {team_id}")
        if fields:
            assignments = ", ".join(f"{k} = ?" for k in fields)
            try:
                conn.execute(f"UPDATE teams SET {assignments} WHERE id = ?", (*fields.values(), team_id))
            except sqlite3.IntegrityError:
                raise StatusUpdateError("TEAM_NAME_TAKEN", f"Đã có đội tên {fields.get('name')}")
            conn.commit()
    return next(t for t in list_teams() if t["id"] == team_id)


# ---------------------------------------------------------------- Phiên đăng nhập

def create_session(token_hash: str, operator_id: int, operator: str, expires_at: str) -> None:
    with get_db_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (utc_now(),))
        conn.execute(
            "INSERT INTO sessions (token_hash, operator, operator_id, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
            (token_hash, operator, operator_id, utc_now(), expires_at),
        )
        conn.commit()


def get_session(token_hash: str) -> Optional[Dict[str, Any]]:
    """Phiên còn hạn của tài khoản đang hoạt động (tài khoản bị khóa thì phiên mất hiệu lực)."""
    with get_db_connection() as conn:
        row = conn.execute(
            """
            SELECT s.expires_at, o.id, o.username, o.display_name, o.role, o.must_change_password
            FROM sessions s JOIN operators o ON o.id = s.operator_id
            WHERE s.token_hash = ? AND s.expires_at > ? AND o.active = 1
            """,
            (token_hash, utc_now()),
        ).fetchone()
    if not row:
        return None
    return {
        "operator": row["display_name"],
        "operatorId": row["id"],
        "username": row["username"],
        "role": row["role"],
        "mustChangePassword": bool(row["must_change_password"]),
        "expiresAt": row["expires_at"],
    }


def delete_session(token_hash: str) -> None:
    with get_db_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
        conn.commit()


# ---------------------------------------------------------------- Dọn dữ liệu

def cleanup(dedup_retention_days: float) -> Dict[str, int]:
    """Xóa phiên hết hạn và bản ghi chống trùng cũ hơn ``dedup_retention_days`` ngày.

    Bản ghi chống trùng chưa hết hạn (``expires_at`` trong tương lai) được giữ. Nếu app gửi
    lại message đã bị dọn, kết quả vẫn đúng: báo cáo gộp theo id (không tạo trùng), đổi
    trạng thái cũ bị chặn bởi ``statusVersion``.
    """
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=dedup_retention_days)).isoformat()
    now_z = now.isoformat(timespec="seconds").replace("+00:00", "Z")
    with get_db_connection() as conn:
        sessions = conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now_z,)).rowcount
        dedup = conn.execute(
            "DELETE FROM messages_dedup WHERE processed_at < ? AND (expires_at IS NULL OR expires_at < ?)",
            (cutoff, now_z),
        ).rowcount
        conn.commit()
    return {"sessions": sessions, "messagesDedup": dedup}


# ---------------------------------------------------------------- Sao lưu

def ping() -> None:
    """Ném lỗi nếu DB không đọc được hoặc thư mục ảnh không tồn tại (dùng cho /healthz)."""
    with get_db_connection() as conn:
        conn.execute("SELECT value FROM server_meta WHERE key = 'epoch'").fetchone()
    if not UPLOADS_DIR.is_dir():
        raise RuntimeError(f"Không thấy thư mục ảnh {UPLOADS_DIR}")


def mirror_uploads(dest_dir: Path) -> int:
    """Chép ảnh chưa có (hoặc khác dung lượng) sang ``dest_dir``. Trả về số file đã chép."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for source in UPLOADS_DIR.iterdir():
        if not source.is_file():
            continue
        target = dest_dir / source.name
        if target.exists() and target.stat().st_size == source.stat().st_size:
            continue
        tmp = target.with_name(target.name + ".part")
        shutil.copyfile(source, tmp)
        tmp.replace(target)
        copied += 1
    return copied


def zip_backup(db_file: Path, dest: Path) -> Path:
    """ZIP gồm bản sao DB và thư mục ``uploads/`` (ảnh đã nén sẵn nên lưu không nén lại)."""
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        archive.write(db_file, f"data/{db_file.name}")
        for source in sorted(UPLOADS_DIR.iterdir()):
            if source.is_file():
                archive.write(source, f"uploads/{source.name}")
    return dest


def backup_to(dest: Path) -> Path:
    """Chụp một bản sao nhất quán của DB (SQLite online backup) vào ``dest``."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(str(DB_FILE))
    try:
        with closing(sqlite3.connect(str(dest))) as out:
            src.backup(out)
    finally:
        src.close()
    return dest


def _ack(
    message_id: Any, status: str, code: Optional[str] = None, result: Any = None, retryable: bool = False
) -> Dict[str, Any]:
    return {"message_id": message_id or "unknown", "status": status, "retryable": retryable, "code": code, "result": result}


def _record_dedup(conn: sqlite3.Connection, msg: Dict[str, Any], result: Dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO messages_dedup (
            message_id, client_id, sequence_number, operation_type,
            payload_hash, status, error_code, result_data,
            created_at, expires_at, processed_at
        ) VALUES (?, ?, ?, ?, ?, 'accepted', NULL, ?, ?, ?, ?)
        """,
        (
            msg["message_id"], msg["client_id"], msg["sequence_number"], msg["operation_type"],
            msg["payload_hash"], json.dumps(result), msg["created_at"], msg.get("expires_at"),
            datetime.now(timezone.utc).isoformat(),
        ),
    )


def _process_message(
    conn: sqlite3.Connection, msg: Any, now_utc: datetime, operator: Optional[str]
) -> Dict[str, Any]:
    """Xử lý một message (chưa commit). Trả về kết quả theo docs/contact_connect.md."""
    if not isinstance(msg, dict):
        return _ack(None, "rejected", "INVALID_PAYLOAD", {"error": "message phải là JSON object"})
    msg_id = msg.get("message_id")
    client_id = msg.get("client_id")
    seq_num = msg.get("sequence_number")
    op_type = msg.get("operation_type")
    expires_at = msg.get("expires_at")
    sent_hash = msg.get("payload_hash")
    payload = msg.get("payload")

    if not (
        isinstance(msg_id, str) and msg_id and isinstance(client_id, str) and 0 < len(client_id) <= CLIENT_ID_MAX_LENGTH
        and isinstance(seq_num, int) and not isinstance(seq_num, bool)
        and isinstance(op_type, str) and msg.get("created_at") and isinstance(sent_hash, str)
        and isinstance(payload, dict)
    ):
        logger.warning(f"[SYNC][REJECTED] msg={msg_id or 'unknown'} code=INVALID_PAYLOAD")
        return _ack(msg_id if isinstance(msg_id, str) else None, "rejected", "INVALID_PAYLOAD")

    # 1. Kiểm tra canonical hash theo RFC 8785
    try:
        computed_hash = compute_payload_hash(payload)
    except (TypeError, ValueError):
        return _ack(msg_id, "rejected", "INVALID_PAYLOAD", {"error": "payload không hợp lệ theo RFC 8785"})
    if computed_hash != sent_hash:
        logger.warning(f"[SYNC][REJECTED] msg={msg_id} code=INVALID_PAYLOAD hash mismatch")
        return _ack(msg_id, "rejected", "INVALID_PAYLOAD", {"error": "payload_hash không khớp canonical JCS"})

    # 2. Kiểm tra hạn message
    if isinstance(expires_at, str) and expires_at:
        try:
            exp_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if exp_dt < now_utc:
                logger.warning(f"[SYNC][REJECTED] msg={msg_id} code=EXPIRED")
                return _ack(msg_id, "rejected", "EXPIRED")
        except (ValueError, TypeError):
            pass

    # 3. Kiểm tra idempotency message_id
    existing_msg = conn.execute(
        "SELECT payload_hash, result_data FROM messages_dedup WHERE message_id = ?", (msg_id,)
    ).fetchone()
    if existing_msg:
        if existing_msg["payload_hash"] == sent_hash:
            logger.debug(f"[SYNC][DUPLICATE] msg={msg_id}")
            previous = json.loads(existing_msg["result_data"]) if existing_msg["result_data"] else None
            return _ack(msg_id, "duplicate", result=previous)
        logger.warning(f"[SYNC][REJECTED] msg={msg_id} code=ID_REUSED_WITH_DIFFERENT_PAYLOAD")
        return _ack(msg_id, "rejected", "ID_REUSED_WITH_DIFFERENT_PAYLOAD")

    # 4. Kiểm tra tái sử dụng (client_id, sequence_number)
    existing_seq = conn.execute(
        "SELECT message_id FROM messages_dedup WHERE client_id = ? AND sequence_number = ?",
        (client_id, seq_num),
    ).fetchone()
    if existing_seq and existing_seq["message_id"] != msg_id:
        logger.warning(f"[SYNC][REJECTED] msg={msg_id} code=SEQUENCE_REUSED")
        return _ack(msg_id, "rejected", "SEQUENCE_REUSED")

    # 5. Xử lý nghiệp vụ theo operation_type
    if op_type == "CREATE_RESCUE_RECORD":
        try:
            validate_report_payload(payload)
        except StatusUpdateError as err:
            logger.warning(f"[SYNC][REJECTED] msg={msg_id} code=INVALID_PAYLOAD ({err.message})")
            return _ack(msg_id, "rejected", err.code, {"error": err.message})
        try:
            rec_res = save_report(payload, connection=conn, source="sync", client_id=client_id)
        except StatusUpdateError as err:
            logger.warning(f"[SYNC][REJECTED] msg={msg_id} code={err.code}")
            return _ack(msg_id, "rejected", err.code, {"error": err.message})
        res_data = {"record_id": rec_res["id"], "serverReceivedAt": rec_res["serverReceivedAt"]}
        _record_dedup(conn, msg, res_data)
        logger.info(f"[SYNC][ACCEPTED] msg={msg_id} op=CREATE_RESCUE_RECORD record={res_data['record_id']}")
        return _ack(msg_id, "accepted", result=res_data)

    if op_type == "UPDATE_RESCUE_STATUS":
        # Chỉ điều phối viên đã đăng nhập mới được đổi trạng thái (app không gửi operation này).
        if not operator:
            logger.warning(f"[SYNC][REJECTED] msg={msg_id} op=UPDATE_RESCUE_STATUS code=UNAUTHENTICATED")
            return _ack(msg_id, "rejected", "UNAUTHENTICATED",
                        {"error": "UPDATE_RESCUE_STATUS cần phiên đăng nhập điều phối"})
        try:
            res_data, curr_status = apply_status_update(
                conn, payload.get("id"), payload.get("status"), payload.get("statusVersion"),
                actor=operator, source="sync", reason=payload.get("reason"),
            )
        except StatusUpdateError as err:
            logger.warning(f"[SYNC][REJECTED] msg={msg_id} op=UPDATE_RESCUE_STATUS code={err.code}")
            return _ack(msg_id, "rejected", err.code, {"error": err.message} if err.message else None)
        _record_dedup(conn, msg, res_data)
        logger.info(
            f"[SYNC][ACCEPTED] msg={msg_id} op=UPDATE_RESCUE_STATUS {res_data['id']}: "
            f"{curr_status}->v{res_data['statusVersion']} {res_data['status']}"
        )
        return _ack(msg_id, "accepted", result=res_data)

    logger.warning(f"[SYNC][REJECTED] msg={msg_id} code=UNSUPPORTED_OPERATION op={op_type}")
    return _ack(msg_id, "rejected", "UNSUPPORTED_OPERATION")


def process_sync_messages(messages: List[Any], operator: Optional[str] = None) -> List[Dict[str, Any]]:
    """Xử lý danh sách message theo contact_connect.md.

    Mỗi message có transaction riêng: nghiệp vụ và bản ghi chống trùng commit cùng nhau.
    Lỗi bất ngờ ở một message chỉ rollback message đó và trả ``retry_later`` cho riêng
    nó, không làm hỏng cả batch. ``operator`` là tên điều phối viên khi request có phiên
    đăng nhập dashboard (bắt buộc cho ``UPDATE_RESCUE_STATUS``).
    """
    results = []
    now_utc = datetime.now(timezone.utc)
    logger.info(f"[SYNC] Bắt đầu xử lý batch {len(messages)} messages")

    with get_db_connection() as conn:
        for msg in messages:
            try:
                result = _process_message(conn, msg, now_utc, operator)
                conn.commit()
            except Exception:
                conn.rollback()
                msg_id = msg.get("message_id") if isinstance(msg, dict) else None
                logger.exception(f"[SYNC][ERROR] msg={msg_id}: lỗi server, đã rollback message này")
                result = _ack(msg_id, "retry_later", "SERVER_ERROR", retryable=True)
            results.append(result)

    counts = {status: sum(1 for r in results if r["status"] == status)
              for status in ("accepted", "rejected", "duplicate", "retry_later")}
    logger.info(
        f"[SYNC] Batch xong: {counts['accepted']} accepted, {counts['rejected']} rejected, "
        f"{counts['duplicate']} duplicate, {counts['retry_later']} retry_later"
    )
    return results
