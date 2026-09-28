#!/usr/bin/env bash
# Chạy trọn bộ demo: server (nền, DB demo riêng) + Flutter app. Ctrl+C / thoát app sẽ tắt server.
#
#   scripts/demo/run_demo.sh                   # server + dữ liệu mô phỏng run_001, app trên thiết bị mặc định
#   scripts/demo/run_demo.sh -d emulator-5554  # app trên emulator Android
#   scripts/demo/run_demo.sh --no-seed -d linux
#   scripts/demo/run_demo.sh --server-only     # chỉ server + dashboard (không cần Flutter)
#
# Các tham số còn lại (-d, --server-url, --release, ...) được chuyển tiếp cho run_app.sh.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
PORT="8000"
SEED_FLAG="--seed"
SERVER_ONLY=0
APP_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-seed) SEED_FLAG="--demo" ;;
    --server-only) SERVER_ONLY=1 ;;
    --port) PORT="$2"; APP_ARGS+=(--port "$2"); shift ;;
    -h|--help) sed -n '2,10p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) APP_ARGS+=("$1") ;;
  esac
  shift
done

if [[ $SERVER_ONLY -eq 1 ]]; then
  exec "$HERE/run_server.sh" "$SEED_FLAG" --port "$PORT"
fi

if (exec 3<>"/dev/tcp/127.0.0.1/$PORT") 2>/dev/null; then
  echo "Cổng $PORT đang bận (server khác đang chạy?). Dừng nó hoặc dùng --port." >&2
  exit 1
fi

LOG="$ROOT/be/server_demo.log"
"$HERE/run_server.sh" "$SEED_FLAG" --port "$PORT" --no-reload >"$LOG" 2>&1 &
SERVER_PID=$!
cleanup() {
  kill "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
  echo ">> Đã tắt server."
}
trap cleanup EXIT
trap 'exit 130' INT TERM

echo ">> Đang khởi động server (log: be/server_demo.log) ..."
for _ in $(seq 1 120); do
  if curl -sf -o /dev/null "http://127.0.0.1:$PORT/probe"; then
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "Server dừng bất thường, xem log:" >&2
    tail -n 30 "$LOG" >&2
    exit 1
  fi
  sleep 1
done
curl -sf -o /dev/null "http://127.0.0.1:$PORT/probe" || { echo "Server không phản hồi sau 120 s." >&2; exit 1; }
echo ">> Server sẵn sàng — dashboard: http://localhost:$PORT/"
echo "   Đăng nhập dashboard: tài khoản ${RESCUE_ADMIN_USERNAME:-admin} / mật khẩu ${RESCUE_ADMIN_PASSWORD:-${RESCUE_DASHBOARD_PASSWORD:-cuuho2026}} (lần đầu; tạo tài khoản điều phối viên ở mục \"Tài khoản\")"

"$HERE/run_app.sh" "${APP_ARGS[@]}"
