import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
# RESCUE_UPLOADS_DIR / RESCUE_DB_FILE cho phép chạy demo, thực nghiệm trên dữ liệu riêng,
# không ghi vào be/uploads/ và be/data/rescue_reports.db (đang được commit làm dữ liệu mẫu).
UPLOADS_DIR = BASE_DIR / os.environ.get("RESCUE_UPLOADS_DIR", "uploads")
DATA_DIR = BASE_DIR / "data"
_db_override = os.environ.get("RESCUE_DB_FILE")
DB_FILE = BASE_DIR / _db_override if _db_override else DATA_DIR / "rescue_reports.db"
TEMPLATES_DIR = BASE_DIR / "templates"

HOST = "0.0.0.0"
PORT = 8000

# 64 KB probe buffer size (65536 bytes) matching FE throughput benchmark requirements
PROBE_SIZE_BYTES = 64 * 1024

# Ensure directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
