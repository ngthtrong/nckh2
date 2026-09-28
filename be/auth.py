"""Đăng nhập dashboard điều phối bằng tài khoản riêng (xem ``accounts.py``).

Phiên lưu trong SQLite (chỉ lưu SHA-256 của token), gửi qua cookie HttpOnly hoặc header
``Authorization: Bearer <token>`` (script, kiểm thử). Tên hiển thị của tài khoản được ghi
vào nhật ký thao tác.

Chặn dò mật khẩu theo cả địa chỉ IP và tên đăng nhập. IP lấy từ kết nối TCP; chỉ khi kết
nối đến từ proxy tin cậy (``RESCUE_TRUSTED_PROXIES``: IP, dải CIDR hoặc tên máy như
``dashboard,fe`` trong docker compose) mới đọc ``X-Forwarded-For``, lấy địa chỉ gần nhất
không phải proxy, nên client không tự giả IP được.

Các endpoint của app (``/probe``, ``/sync/messages``, ``POST /api/reports``,
``GET /api/reports/status``) không cần đăng nhập, đúng docs/contact_connect.md.
"""
from __future__ import annotations

import hashlib
import ipaddress
import logging
import os
import secrets
import socket
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Deque, Dict, List, Optional, Tuple

from fastapi import HTTPException, Request, status

import accounts
import storage

logger = logging.getLogger("rescue_mock_server")

SESSION_HOURS = float(os.environ.get("RESCUE_SESSION_HOURS") or 12)
COOKIE_NAME = "rescue_session"
# Đặt RESCUE_COOKIE_SECURE=1 khi dashboard chạy sau HTTPS.
COOKIE_SECURE = os.environ.get("RESCUE_COOKIE_SECURE") == "1"
TRUSTED_PROXIES = [p.strip() for p in (os.environ.get("RESCUE_TRUSTED_PROXIES") or "").split(",") if p.strip()]

# Chặn dò mật khẩu trong cửa sổ 5 phút: 5 lần sai cho một tên đăng nhập, 20 lần sai từ một IP.
FAILURE_WINDOW_S = 300.0
MAX_FAILURES_PER_USER = 5
MAX_FAILURES_PER_IP = 20
_failures: Dict[str, Deque[float]] = defaultdict(deque)
_failures_lock = threading.Lock()

_proxy_cache: Tuple[float, List[ipaddress._BaseNetwork]] = (0.0, [])
_PROXY_CACHE_S = 60.0


def warn_if_default_password() -> None:
    if accounts.uses_default_password():
        logger.warning(
            "Tài khoản quản trị đang dùng mật khẩu mặc định; đặt RESCUE_ADMIN_PASSWORD hoặc đổi mật khẩu "
            "trên dashboard trước khi triển khai thật."
        )


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _trusted_networks() -> List[ipaddress._BaseNetwork]:
    """Mạng của các proxy tin cậy; tên máy được phân giải lại mỗi phút (IP container có thể đổi)."""
    global _proxy_cache
    now = time.monotonic()
    if now - _proxy_cache[0] < _PROXY_CACHE_S:
        return _proxy_cache[1]
    networks: List[ipaddress._BaseNetwork] = []
    for entry in TRUSTED_PROXIES:
        try:
            networks.append(ipaddress.ip_network(entry, strict=False))
            continue
        except ValueError:
            pass
        try:
            for info in socket.getaddrinfo(entry, None):
                networks.append(ipaddress.ip_network(info[4][0]))
        except OSError:
            logger.debug(f"[AUTH] Chưa phân giải được proxy tin cậy '{entry}'")
    _proxy_cache = (now, networks)
    return networks


def _is_trusted(address: str, networks: List[ipaddress._BaseNetwork]) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return any(ip in network for network in networks)


def client_ip(request: Request) -> str:
    peer = request.client.host if request.client else "unknown"
    networks = _trusted_networks() if TRUSTED_PROXIES else []
    if not networks or not _is_trusted(peer, networks):
        return peer
    # nginx nối địa chỉ nó thấy vào cuối X-Forwarded-For; phần client tự gửi nằm bên trái.
    hops = [h.strip() for h in (request.headers.get("x-forwarded-for") or "").split(",") if h.strip()]
    for hop in reversed(hops):
        if not _is_trusted(hop, networks):
            return hop
    return peer


def _recent(key: str, now: float) -> Deque[float]:
    window = _failures[key]
    while window and now - window[0] > FAILURE_WINDOW_S:
        window.popleft()
    return window


def prune_failures() -> None:
    """Bỏ bộ đếm đã hết cửa sổ (gọi định kỳ để bộ nhớ không tăng mãi)."""
    now = time.monotonic()
    with _failures_lock:
        for key in [k for k, v in _failures.items() if not _recent(k, now)]:
            _failures.pop(key, None)


def login(request: Request, username: str, password: str) -> Dict[str, object]:
    """Kiểm tra tài khoản; trả về token và thông tin phiên. Ném HTTPException khi sai."""
    ip = client_ip(request)
    user = str(username or "").strip().lower()
    ip_key, user_key = f"ip:{ip}", f"user:{user}"
    now = time.monotonic()
    with _failures_lock:
        if (len(_recent(ip_key, now)) >= MAX_FAILURES_PER_IP
                or len(_recent(user_key, now)) >= MAX_FAILURES_PER_USER):
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, detail={
                "code": "TOO_MANY_ATTEMPTS", "error": "Sai mật khẩu quá nhiều lần, thử lại sau 5 phút",
            })

    operator = accounts.authenticate(user, password)
    if not operator:
        with _failures_lock:
            _recent(ip_key, now).append(now)
            _recent(user_key, now).append(now)
        logger.warning(f"[AUTH] Đăng nhập sai từ {ip} (tài khoản: {user[:40]})")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={
            "code": "INVALID_CREDENTIALS", "error": "Sai tên đăng nhập hoặc mật khẩu",
        })

    with _failures_lock:
        _failures.pop(user_key, None)
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)
    expires_at = expires.isoformat(timespec="seconds").replace("+00:00", "Z")
    storage.create_session(_hash(token), operator["id"], operator["displayName"], expires_at)
    logger.info(f"[AUTH] {operator['username']} đăng nhập từ {ip}")
    return {"token": token, **storage.get_session(_hash(token))}


def _token_from(request: Request) -> Optional[str]:
    header = request.headers.get("authorization") or ""
    if header.lower().startswith("bearer "):
        return header[7:].strip() or None
    return request.cookies.get(COOKIE_NAME)


def token_hash(request: Request) -> Optional[str]:
    token = _token_from(request)
    return _hash(token) if token else None


def session_for(request: Request) -> Optional[Dict[str, object]]:
    hashed = token_hash(request)
    return storage.get_session(hashed) if hashed else None


def logout(request: Request) -> None:
    hashed = token_hash(request)
    if hashed:
        storage.delete_session(hashed)


def require_session(request: Request) -> Dict[str, object]:
    """Dependency FastAPI: phiên hiện tại, 401 nếu chưa đăng nhập."""
    session = session_for(request)
    if not session:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={
            "code": "UNAUTHENTICATED", "error": "Cần đăng nhập dashboard",
        })
    return session


def require_operator(request: Request) -> str:
    """Dependency FastAPI: tên hiển thị của người đang đăng nhập (ghi vào nhật ký)."""
    return str(require_session(request)["operator"])


def require_admin(request: Request) -> Dict[str, object]:
    session = require_session(request)
    if session["role"] != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail={
            "code": "FORBIDDEN", "error": "Chỉ quản trị viên được thực hiện thao tác này",
        })
    return session
