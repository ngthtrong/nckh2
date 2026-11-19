#!/usr/bin/env bash
# Build app Flutter bản web trên máy (không cần Docker tải Flutter SDK), cho target
# "prebuilt" của products/docker/fe/Dockerfile:
#
#   products/scripts/demo/build_web.sh && FE_BUILD_TARGET=prebuilt docker compose up -d --build
#
# SERVER_URL để trống = app gọi API cùng origin qua nginx của container fe.
set -euo pipefail
APP="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../fe/app" && pwd)"
command -v flutter >/dev/null || { echo "Không tìm thấy flutter trong PATH." >&2; exit 1; }
cd "$APP"
flutter pub get
flutter build web --release --no-wasm-dry-run --dart-define=SERVER_URL="${SERVER_URL:-}"
echo ">> Đã build $APP/build/web"
