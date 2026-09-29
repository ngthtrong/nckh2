"""Tài khoản điều phối viên: mỗi người một tên đăng nhập, mật khẩu riêng và vai trò.

- ``admin``: mọi thao tác, thêm quản lý tài khoản, tải sao lưu, xóa dữ liệu demo.
- ``operator``: điều phối (trạng thái, đội, ghi chú, vị trí, báo cáo tổng đài, xuất dữ liệu).

Mật khẩu lưu dạng PBKDF2-SHA256 có salt riêng. Khi chưa có tài khoản nào, server tạo
tài khoản quản trị từ ``RESCUE_ADMIN_USERNAME`` (mặc định ``admin``) và
``RESCUE_ADMIN_PASSWORD`` (mặc định lấy ``RESCUE_DASHBOARD_PASSWORD`` cũ, rồi ``cuuho2026``).
Tài khoản do quản trị viên tạo hoặc đặt lại mật khẩu phải đổi mật khẩu ở lần đăng nhập sau.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import secrets
import sqlite3
from typing import Any, Dict, List, Optional

from storage import StatusUpdateError, get_db_connection, utc_now

logger = logging.getLogger("rescue_mock_server")

ROLES = ("admin", "operator")
DEFAULT_PASSWORD = "cuuho2026"
PASSWORD_MIN_LENGTH = 8
USERNAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,31}$")
PBKDF2_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, iterations, salt, expected = stored.split("$")
        if scheme != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), expected)


# Băm giả cho tên đăng nhập không tồn tại: thời gian trả lời như khi sai mật khẩu.
_DUMMY_HASH = hash_password(secrets.token_hex(8))


def ensure_admin() -> None:
    """Tạo tài khoản quản trị đầu tiên nếu chưa có tài khoản nào."""
    with get_db_connection() as conn:
        if conn.execute("SELECT 1 FROM operators LIMIT 1").fetchone():
            return
        username = (os.environ.get("RESCUE_ADMIN_USERNAME") or "admin").strip().lower()
        password = (os.environ.get("RESCUE_ADMIN_PASSWORD") or os.environ.get("RESCUE_DASHBOARD_PASSWORD")
                    or DEFAULT_PASSWORD)
        conn.execute(
            "INSERT INTO operators (username, display_name, password_hash, role, created_at) VALUES (?, ?, ?, 'admin', ?)",
            (username, "Quản trị viên", hash_password(password), utc_now()),
        )
        conn.commit()
    logger.info(f"[AUTH] Đã tạo tài khoản quản trị '{username}'.")


def uses_default_password() -> bool:
    """Còn tài khoản quản trị dùng mật khẩu mặc định (cảnh báo khi triển khai thật)."""
    with get_db_connection() as conn:
        rows = conn.execute("SELECT password_hash FROM operators WHERE role = 'admin' AND active = 1").fetchall()
    return any(verify_password(DEFAULT_PASSWORD, row["password_hash"]) for row in rows)


def _to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "username": row["username"],
        "displayName": row["display_name"],
        "role": row["role"],
        "active": bool(row["active"]),
        "mustChangePassword": bool(row["must_change_password"]),
        "createdAt": row["created_at"],
        "lastLoginAt": row["last_login_at"],
    }


def authenticate(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Tài khoản nếu đúng tên đăng nhập + mật khẩu và đang hoạt động, ngược lại None."""
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM operators WHERE username = ?", (str(username or "").strip(),)).fetchone()
        if not verify_password(str(password or ""), row["password_hash"] if row else _DUMMY_HASH) or not row:
            return None
        if not row["active"]:
            return None
        conn.execute("UPDATE operators SET last_login_at = ? WHERE id = ?", (utc_now(), row["id"]))
        conn.commit()
    return _to_dict(row)


def list_operators() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM operators ORDER BY active DESC, role, username").fetchall()
    return [_to_dict(r) for r in rows]


def get_operator(operator_id: int) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM operators WHERE id = ?", (operator_id,)).fetchone()
    return _to_dict(row) if row else None


def _check_password(password: Any) -> str:
    if not isinstance(password, str) or len(password) < PASSWORD_MIN_LENGTH or len(password) > 200:
        raise StatusUpdateError("INVALID_PAYLOAD", f"Mật khẩu phải có {PASSWORD_MIN_LENGTH}-200 ký tự")
    return password


def _check_display_name(name: Any) -> str:
    name = " ".join(str(name or "").split())
    if not 1 <= len(name) <= 60:
        raise StatusUpdateError("INVALID_PAYLOAD", "Tên hiển thị phải có 1-60 ký tự")
    return name


def _check_role(role: Any) -> str:
    if role not in ROLES:
        raise StatusUpdateError("INVALID_PAYLOAD", f"Vai trò phải là {' hoặc '.join(ROLES)}")
    return role


def create_operator(data: Dict[str, Any]) -> Dict[str, Any]:
    username = str(data.get("username") or "").strip().lower()
    if not USERNAME_PATTERN.match(username):
        raise StatusUpdateError("INVALID_PAYLOAD", "Tên đăng nhập 3-32 ký tự: chữ thường không dấu, số, '.', '_', '-'")
    fields = (
        username,
        _check_display_name(data.get("displayName")),
        hash_password(_check_password(data.get("password"))),
        _check_role(data.get("role") or "operator"),
        utc_now(),
    )
    with get_db_connection() as conn:
        try:
            cur = conn.execute(
                """INSERT INTO operators (username, display_name, password_hash, role, must_change_password, created_at)
                   VALUES (?, ?, ?, ?, 1, ?)""",
                fields,
            )
        except sqlite3.IntegrityError:
            raise StatusUpdateError("OPERATOR_TAKEN", "Tên đăng nhập hoặc tên hiển thị đã được dùng")
        conn.commit()
        operator_id = cur.lastrowid
    return get_operator(operator_id)


def _active_admins(conn: sqlite3.Connection, excluding: int) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM operators WHERE role = 'admin' AND active = 1 AND id != ?", (excluding,)
    ).fetchone()[0]


def update_operator(operator_id: int, data: Dict[str, Any], *, acting_id: int) -> Dict[str, Any]:
    """Quản trị viên sửa tên, vai trò, khóa/mở khóa hoặc đặt lại mật khẩu (buộc đổi lần sau)."""
    updates: Dict[str, Any] = {}
    if "displayName" in data:
        updates["display_name"] = _check_display_name(data["displayName"])
    if "role" in data:
        updates["role"] = _check_role(data["role"])
    if "active" in data:
        updates["active"] = 1 if data["active"] else 0
    if data.get("password") is not None:
        updates["password_hash"] = hash_password(_check_password(data["password"]))
        updates["must_change_password"] = 1
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM operators WHERE id = ?", (operator_id,)).fetchone()
        if not row:
            raise StatusUpdateError("OPERATOR_NOT_FOUND", f"Không có tài khoản {operator_id}")
        losing_admin = row["role"] == "admin" and (updates.get("role", "admin") != "admin" or updates.get("active", 1) == 0)
        if losing_admin and not _active_admins(conn, operator_id):
            raise StatusUpdateError("LAST_ADMIN", "Phải còn ít nhất một quản trị viên đang hoạt động")
        if operator_id == acting_id and updates.get("active", 1) == 0:
            raise StatusUpdateError("LAST_ADMIN", "Không tự khóa tài khoản đang dùng")
        if updates:
            try:
                conn.execute(
                    f"UPDATE operators SET {', '.join(f'{k} = ?' for k in updates)} WHERE id = ?",
                    (*updates.values(), operator_id),
                )
            except sqlite3.IntegrityError:
                raise StatusUpdateError("OPERATOR_TAKEN", "Tên hiển thị đã được dùng")
            if "password_hash" in updates or updates.get("active") == 0:
                # Khóa tài khoản hoặc đặt lại mật khẩu: đăng xuất mọi phiên của người đó.
                conn.execute("DELETE FROM sessions WHERE operator_id = ?", (operator_id,))
            conn.commit()
    return get_operator(operator_id)


def change_own_password(operator_id: int, current: str, new: str, *, keep_token_hash: str) -> None:
    with get_db_connection() as conn:
        row = conn.execute("SELECT password_hash FROM operators WHERE id = ?", (operator_id,)).fetchone()
        if not row or not verify_password(str(current or ""), row["password_hash"]):
            raise StatusUpdateError("INVALID_CREDENTIALS", "Mật khẩu hiện tại không đúng")
        if current == new:
            raise StatusUpdateError("INVALID_PAYLOAD", "Mật khẩu mới phải khác mật khẩu hiện tại")
        conn.execute(
            "UPDATE operators SET password_hash = ?, must_change_password = 0 WHERE id = ?",
            (hash_password(_check_password(new)), operator_id),
        )
        # Đăng xuất các phiên khác của người này (máy khác có thể đã lộ mật khẩu cũ).
        conn.execute("DELETE FROM sessions WHERE operator_id = ? AND token_hash != ?", (operator_id, keep_token_hash))
        conn.commit()
