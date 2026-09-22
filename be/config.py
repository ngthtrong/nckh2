from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
DATA_DIR = BASE_DIR / "data"
DB_FILE = DATA_DIR / "rescue_reports.db"
TEMPLATES_DIR = BASE_DIR / "templates"

HOST = "0.0.0.0"
PORT = 8000

# 64 KB probe buffer size (65536 bytes) matching FE throughput benchmark requirements
PROBE_SIZE_BYTES = 64 * 1024

# Ensure directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
