#!/usr/bin/env bash
# Chạy Flutter app (fe/app) trỏ tới mock server — Linux / macOS / WSL.
#
#   scripts/demo/run_app.sh                              # thiết bị mặc định, server http://localhost:8000
#   scripts/demo/run_app.sh -d emulator-5554             # emulator Android → tự dùng http://10.0.2.2:8000
#   scripts/demo/run_app.sh -d R58M... --server-url http://192.168.1.20:8000   # điện thoại thật
#   scripts/demo/run_app.sh -d linux
#
# Server URL truyền qua --dart-define=SERVER_URL (xem fe/app/lib/config.dart), không cần sửa code.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP="$ROOT/fe/app"

DEVICE=""
SERVER_URL=""
PORT="8000"
MODE="--debug"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -d|--device) DEVICE="$2"; shift ;;
    --server-url) SERVER_URL="$2"; shift ;;
    --port) PORT="$2"; shift ;;
    --release) MODE="--release" ;;
    --profile) MODE="--profile" ;;
    -h|--help) sed -n '2,9p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Tùy chọn không hợp lệ: $1" >&2; exit 2 ;;
  esac
  shift
done

command -v flutter >/dev/null || { echo "Không tìm thấy flutter trong PATH." >&2; exit 1; }

if [[ -z "$SERVER_URL" ]]; then
  case "$DEVICE" in
    emulator-*) SERVER_URL="http://10.0.2.2:$PORT" ;;
    ""|linux|windows|macos|chrome|web-server) SERVER_URL="http://localhost:$PORT" ;;
    *)
      # Điện thoại thật: cần IP LAN của máy chạy server (trên WSL phải là IP của Windows host).
      LAN_IP="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
      SERVER_URL="http://${LAN_IP:-localhost}:$PORT"
      echo "!! Thiết bị thật: tự đoán SERVER_URL=$SERVER_URL — sai thì truyền --server-url." ;;
  esac
fi

if [[ ! -f "$APP/assets/models/model.onnx" || ! -f "$APP/assets/models/model_manifest.json" ]]; then
  echo "!! Chưa có model trong fe/app/assets/models/ → app chạy được nhưng AI on-device tắt."
  echo "   Chạy scripts/demo/stage_model.sh sau khi export model (docs/huong_dan_chay_demo.md §4)."
fi

cd "$APP"
flutter pub get

ARGS=(run "$MODE" "--dart-define=SERVER_URL=$SERVER_URL")
[[ -n "$DEVICE" ]] && ARGS+=(-d "$DEVICE")
echo ">> flutter ${ARGS[*]}"
exec flutter "${ARGS[@]}"
