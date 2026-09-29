import hashlib
from typing import Any

import rfc8785


def canonicalize(obj: Any) -> bytes:
    """Chuẩn hóa JSON thành UTF-8 bytes theo RFC 8785 (JCS)."""
    return rfc8785.dumps(obj)


def compute_payload_hash(payload: Any) -> str:
    """Tính sha256:hex-encoded-hash từ payload canonical."""
    canonical_bytes = canonicalize(payload)
    digest = hashlib.sha256(canonical_bytes).hexdigest().lower()
    return f"sha256:{digest}"


def compute_bytes_sha256(data: bytes) -> str:
    """Tính sha256:hex-encoded-hash cho dữ liệu nhị phân (ảnh JPEG)."""
    digest = hashlib.sha256(data).hexdigest().lower()
    return f"sha256:{digest}"
