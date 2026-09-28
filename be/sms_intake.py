"""Tiếp nhận báo cáo qua SMS (gateway chuyển tiếp tin nhắn tới tổng đài) và qua tổng đài viên.

App gửi SMS dự phòng khi không có data, dạng (xem ``smsBody`` trong
``fe/app/lib/data/datasources/sender_remote_datasource.dart``)::

    SOS|id:<id báo cáo>|pos:<lat>,<lng>|trapped:<n>|injured:<n>|vuln:<a,b>|note:<mô tả>

``pos`` là ``unknown`` khi không có GPS; ``vuln`` và ``note`` có thể vắng; ``note`` luôn
đứng cuối nên được phép chứa ``|``. Tin theo định dạng này dùng đúng id của app, nên
khi app có mạng và đồng bộ lại, hai bản gộp thành một báo cáo (server chỉ điền trường
còn trống). Tin nhắn tự do (người dân nhắn tay) thành báo cáo mới không có vị trí, vào
hàng cần xác minh.
"""
from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import storage

logger = logging.getLogger("rescue_mock_server")

SMS_TEXT_MAX_LENGTH = 1600  # ~10 tin ghép


def parse_sos(text: str) -> Optional[Dict[str, Any]]:
    """Trường báo cáo trong tin ``SOS|...`` của app; None nếu không đúng định dạng."""
    text = text.strip()
    if not text.upper().startswith("SOS|"):
        return None
    head, _, note = text[4:].partition("|note:")
    if head.startswith("note:"):
        head, note = "", head[5:]
    fields: Dict[str, str] = {}
    for part in head.split("|"):
        key, sep, value = part.partition(":")
        if sep:
            fields[key.strip().lower()] = value.strip()

    meta: Dict[str, Any] = {}
    if storage.REPORT_ID_PATTERN.match(fields.get("id", "")):
        meta["id"] = fields["id"]
    lat_text, _, lng_text = fields.get("pos", "").partition(",")
    try:
        lat, lng = float(lat_text), float(lng_text)
        if abs(lat) <= 90 and abs(lng) <= 180:
            meta["lat"], meta["lng"] = lat, lng
    except ValueError:
        pass  # "unknown" hoặc tọa độ hỏng: để trống, điều phối viên xác minh
    for key, name in (("trapped", "trappedCount"), ("injured", "injuredCount")):
        if fields.get(key, "").isdigit() and int(fields[key]) <= storage.PEOPLE_MAX:
            meta[name] = int(fields[key])
    groups = [g.strip() for g in fields.get("vuln", "").split(",") if g.strip()]
    if groups:
        meta["vulnerableGroups"] = [g[:50] for g in groups[:20]]
    if note.strip():
        meta["description"] = note.strip()[: storage.DESCRIPTION_MAX_LENGTH]
    return meta


def _iso_or_none(value: Any) -> Optional[str]:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def save_sms(sender: str, text: str, received_at: Any = None) -> Tuple[Dict[str, Any], bool]:
    """Lưu một SMS thành báo cáo. Trả về (báo cáo, True nếu tạo mới).

    Idempotent: gateway gửi lại cùng tin thì cùng id, không tạo báo cáo trùng.
    """
    sender = " ".join(str(sender or "").split())[:30]
    text = str(text or "").strip()[:SMS_TEXT_MAX_LENGTH]
    if not text:
        raise storage.StatusUpdateError("INVALID_PAYLOAD", "Tin nhắn trống")
    received = _iso_or_none(received_at)
    parsed = parse_sos(text)

    meta: Dict[str, Any] = dict(parsed or {})
    if "id" not in meta:
        digest = hashlib.sha256(f"{sender}|{text}|{received or ''}".encode("utf-8")).hexdigest()
        meta["id"] = f"sms-{digest[:16]}"
    if parsed is None:
        meta["description"] = text[: storage.DESCRIPTION_MAX_LENGTH]
    # Tin của app: để createdAt trống, app đồng bộ sau sẽ điền thời điểm bấm gửi chính xác.
    if received and not (parsed and parsed.get("id")):
        meta["createdAt"] = received
    meta.update(sendMode="smsFallback", source="sms", contactPhone=sender or None, smsText=text)
    storage.validate_report_payload(meta)

    with storage.get_db_connection() as conn:
        existing = conn.execute("SELECT raw_payload FROM reports WHERE id = ?", (meta["id"],)).fetchone()
        report = storage.save_report(meta, connection=conn, source="sms")
        if existing and '"contactPhone"' not in (existing["raw_payload"] or ""):
            # App đã đồng bộ trước: ghi lại để điều phối viên biết có số liên hệ.
            storage._add_event(conn, meta["id"], "sms", source="sms", note=f"Nhận thêm SMS từ {sender or 'không rõ số'}")
        conn.commit()
    logger.info(f"[SMS] {sender or '?'} -> {meta['id']} ({'mới' if not existing else 'gộp'}, "
                f"{'định dạng SOS' if parsed else 'tin tự do'})")
    return report, existing is None


def create_manual_report(fields: Dict[str, Any], *, actor: str) -> Dict[str, Any]:
    """Báo cáo do điều phối viên nhập (cuộc gọi tổng đài, báo trực tiếp)."""
    now = datetime.now(timezone.utc)
    meta: Dict[str, Any] = {
        "id": f"hotline-{int(now.timestamp() * 1000)}-{secrets.token_hex(3)}",
        "createdAt": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "lat": fields.get("lat"),
        "lng": fields.get("lng"),
        "trappedCount": fields.get("trappedCount") or 0,
        "injuredCount": fields.get("injuredCount") or 0,
        "vulnerableGroups": fields.get("vulnerableGroups") or [],
        "description": (fields.get("description") or "").strip(),
        "sendMode": "hotline",
        "source": "hotline",
        "contactPhone": (fields.get("contactPhone") or "").strip()[:30] or None,
    }
    if not meta["description"]:
        raise storage.StatusUpdateError("INVALID_PAYLOAD", "Nhập mô tả tình huống")
    storage.validate_report_payload(meta)
    with storage.get_db_connection() as conn:
        storage.save_report(meta, connection=conn, source="dashboard", actor=actor)
        if meta["lat"] is not None:
            conn.execute("UPDATE reports SET location_source = 'manual' WHERE id = ?", (meta["id"],))
        conn.commit()
        row = conn.execute("SELECT * FROM reports WHERE id = ?", (meta["id"],)).fetchone()
    logger.info(f"[HOTLINE] {actor} tạo báo cáo {meta['id']}")
    return storage._row_to_dict(row)
