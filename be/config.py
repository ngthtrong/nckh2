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
STATIC_DIR = BASE_DIR / "static"
# Sao lưu định kỳ DB (phút); 0 = tắt. Bản sao lưu cũ hơn RESCUE_BACKUP_KEEP bản bị xóa.
BACKUP_DIR = BASE_DIR / os.environ.get("RESCUE_BACKUP_DIR", "data/backups")
BACKUP_INTERVAL_MIN = float(os.environ.get("RESCUE_BACKUP_INTERVAL_MIN") or 0)
BACKUP_KEEP = int(os.environ.get("RESCUE_BACKUP_KEEP") or 24)

# Dashboard: cho phép nút "Xóa toàn bộ dữ liệu" (chỉ bật khi demo); URL tile bản đồ
# (đổi sang tile server nội bộ khi không có Internet).
ALLOW_WIPE = os.environ.get("RESCUE_ALLOW_WIPE") == "1"
TILE_URL = os.environ.get("RESCUE_TILE_URL") or "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
TILE_ATTRIBUTION = os.environ.get("RESCUE_TILE_ATTRIBUTION") or "&copy; OpenStreetMap contributors"
# Origin được gọi API từ trình duyệt khác origin (Flutter web chạy riêng). Không gửi cookie
# khác origin, nên dashboard chỉ dùng được cùng origin với API (trực tiếp hoặc qua nginx).
CORS_ORIGINS = [o.strip() for o in (os.environ.get("RESCUE_CORS_ORIGINS") or "*").split(",") if o.strip()]

HOST = "0.0.0.0"
PORT = 8000

# Giới hạn ảnh hiện trường của POST /api/reports (MB); nginx trước server cũng giới hạn 25 MB.
MAX_IMAGE_BYTES = int(float(os.environ.get("RESCUE_MAX_IMAGE_MB") or 15) * 1024 * 1024)

# Phân cụm: lần tính trước chậm hơn ngưỡng (giây) thì chuyển sang tính nền, trả kết quả gần
# nhất; khi tính nền, tối đa một lần mỗi RESCUE_CLUSTER_MIN_INTERVAL_S giây.
CLUSTER_SYNC_BUDGET_S = float(os.environ.get("RESCUE_CLUSTER_SYNC_BUDGET_S") or 1.0)
CLUSTER_MIN_INTERVAL_S = float(os.environ.get("RESCUE_CLUSTER_MIN_INTERVAL_S") or 10.0)

# Bản ghi chống trùng của /sync/messages giữ bao nhiêu ngày (message chưa hết hạn luôn được giữ).
DEDUP_RETENTION_DAYS = float(os.environ.get("RESCUE_DEDUP_RETENTION_DAYS") or 30)

# Token của SMS gateway gọi POST /api/sms/inbound; để trống thì endpoint tắt.
SMS_GATEWAY_TOKEN = os.environ.get("RESCUE_SMS_GATEWAY_TOKEN") or ""

# 64 KB probe buffer size (65536 bytes) matching FE throughput benchmark requirements
PROBE_SIZE_BYTES = 64 * 1024

# Ensure directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
