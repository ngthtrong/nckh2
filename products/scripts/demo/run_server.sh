#!/usr/bin/env bash
# Khởi chạy FastAPI mock server (be/) — Linux / macOS / WSL.
#
#   scripts/demo/run_server.sh                 # dữ liệu mẫu đã commit (be/data/rescue_reports.db)
#   scripts/demo/run_server.sh --demo --seed   # DB demo riêng + nạp run_001 bán tổng hợp
#   scripts/demo/run_server.sh --port 8001 --no-reload
#
# --demo dùng be/data/demo.db + be/uploads_demo/ (git-ignore) để không làm bẩn dữ liệu mẫu.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BE="$ROOT/be"

HOST="0.0.0.0"
PORT="8000"
DEMO=0
SEED=0
SEED_RUN=1
RELOAD=1

usage() {
  sed -n '2,8p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  cat <<'EOF'

Tùy chọn:
  --demo            dùng DB/thư mục ảnh demo riêng (data/demo.db, uploads_demo/)
  --seed            nạp dữ liệu bán tổng hợp vào DB demo trước khi chạy (ngụ ý --demo, xóa DB demo cũ)
  --run N           run số N trong thucnghiem/data/gold khi --seed (mặc định 1)
  --host HOST       địa chỉ lắng nghe (mặc định 0.0.0.0 để điện thoại trong LAN truy cập được)
  --port PORT       cổng (mặc định 8000)
  --no-reload       tắt auto-reload khi sửa code
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --demo) DEMO=1 ;;
    --seed) DEMO=1; SEED=1 ;;
    --run) SEED_RUN="$2"; shift ;;
    --host) HOST="$2"; shift ;;
    --port) PORT="$2"; shift ;;
    --no-reload) RELOAD=0 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Tùy chọn không hợp lệ: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

cd "$BE"

PY="$BE/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo ">> Tạo môi trường ảo be/.venv ..."
  python3 -m venv .venv
fi
# Cài lại dependencies khi requirements.txt mới hơn lần cài trước.
STAMP="$BE/.venv/.requirements.stamp"
if [[ ! -f "$STAMP" || requirements.txt -nt "$STAMP" ]]; then
  echo ">> Cài dependencies từ be/requirements.txt ..."
  "$PY" -m pip install -q --upgrade pip
  "$PY" -m pip install -q -r requirements.txt
  touch "$STAMP"
fi

if [[ $DEMO -eq 1 ]]; then
  export RESCUE_DB_FILE="data/demo.db"
  export RESCUE_UPLOADS_DIR="uploads_demo"
  echo ">> Chế độ DEMO: DB=be/$RESCUE_DB_FILE, ảnh=be/$RESCUE_UPLOADS_DIR/"
fi

if [[ $SEED -eq 1 ]]; then
  echo ">> Nạp dữ liệu BÁN TỔNG HỢP run_$(printf '%03d' "$SEED_RUN") (gắn nhãn source=synthetic) ..."
  "$PY" seed_demo.py --run "$SEED_RUN" --reset
fi

LAN_IP="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
echo "================================================="
echo " Flood Rescue Mock Server"
echo "  Dashboard : http://localhost:$PORT/"
echo "  Đăng nhập : tài khoản ${RESCUE_ADMIN_USERNAME:-admin} / mật khẩu ${RESCUE_ADMIN_PASSWORD:-${RESCUE_DASHBOARD_PASSWORD:-cuuho2026}} (lần đầu; đặt RESCUE_ADMIN_PASSWORD để đổi)"
echo "  Swagger   : http://localhost:$PORT/docs"
[[ -n "$LAN_IP" ]] && echo "  LAN       : http://$LAN_IP:$PORT  (dùng cho điện thoại thật)"
echo "  Emulator  : http://10.0.2.2:$PORT"
echo " Nhấn Ctrl+C để dừng."
echo "================================================="

ARGS=(main:app --host "$HOST" --port "$PORT")
[[ $RELOAD -eq 1 ]] && ARGS+=(--reload)
exec "$PY" -m uvicorn "${ARGS[@]}"
