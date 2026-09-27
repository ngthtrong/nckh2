#!/usr/bin/env bash
# Kiểm tra nhanh trạng thái demo trước khi trình diễn / nghiệm thu.
#
#   scripts/demo/check.sh            # unit test BE + flutter test + flutter analyze (bỏ qua code legacy)
#   scripts/demo/check.sh --smoke    # thêm smoke test end-to-end: bật server tạm (DB riêng) + test_client + seed + /api/clusters
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BE="$ROOT/be"
APP="$ROOT/fe/app"
SMOKE=0
[[ "${1:-}" == "--smoke" ]] && SMOKE=1

# Code legacy không còn được main.dart import (xem CLAUDE.md); lỗi analyze ở đây không ảnh hưởng app.
LEGACY_RE='lib/(controller|home_screen|background_sync)\.dart|lib/services/'

declare -a RESULTS=()
record() { RESULTS+=("$1|$2"); }

echo "== [1] Backend unit test =="
PY="$BE/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "Chưa có be/.venv — chạy scripts/demo/run_server.sh một lần để tạo." >&2
  record "BE unit test" "SKIP (chưa có venv)"
else
  if (cd "$BE" && "$PY" -m unittest test_contract test_cluster_service test_dashboard_api); then
    record "BE unit test" "PASS"
  else
    record "BE unit test" "FAIL"
  fi
fi

if command -v flutter >/dev/null; then
  echo "== [2] flutter test =="
  if (cd "$APP" && flutter test); then record "flutter test" "PASS"; else record "flutter test" "FAIL"; fi

  echo "== [3] flutter analyze (code đang dùng) =="
  OUT="$(cd "$APP" && flutter analyze 2>&1 || true)"
  LIVE_ERR="$(grep -E '^\s*error •' <<<"$OUT" | grep -Ev "$LEGACY_RE" || true)"
  LEGACY_ERR="$(grep -E '^\s*error •' <<<"$OUT" | grep -Ec "$LEGACY_RE" || true)"
  if [[ -n "$LIVE_ERR" ]]; then
    echo "$LIVE_ERR"
    record "flutter analyze" "FAIL (lỗi trong code đang dùng)"
  else
    record "flutter analyze" "PASS (bỏ qua $LEGACY_ERR lỗi ở code legacy)"
  fi
else
  record "flutter test/analyze" "SKIP (không có flutter)"
fi

echo "== [4] Model trong fe/app/assets/models =="
if [[ -f "$APP/assets/models/model.onnx" && -f "$APP/assets/models/model.pte" && -f "$APP/assets/models/model_manifest.json" ]]; then
  record "Model assets" "OK"
else
  record "Model assets" "THIẾU (AI on-device sẽ tắt; xem stage_model.sh)"
fi

if [[ $SMOKE -eq 1 && -x "$PY" ]]; then
  echo "== [5] Smoke test end-to-end =="
  if (exec 3<>/dev/tcp/127.0.0.1/8000) 2>/dev/null; then
    # test_client.py gọi cứng http://localhost:8000
    record "Smoke test" "SKIP (cổng 8000 đang bận)"
  else
    SMOKE_DB="data/demo_check.db"; SMOKE_UP="uploads_check"
    (cd "$BE" && RESCUE_DB_FILE=$SMOKE_DB RESCUE_UPLOADS_DIR=$SMOKE_UP \
      exec "$PY" -m uvicorn main:app --host 127.0.0.1 --port 8000 >/dev/null 2>&1) &
    SPID=$!
    for _ in $(seq 1 60); do curl -sf -o /dev/null http://127.0.0.1:8000/healthz && break; sleep 0.5; done
    ok=1
    (cd "$BE" && "$PY" test_client.py) || ok=0
    (cd "$BE" && RESCUE_DB_FILE=$SMOKE_DB RESCUE_UPLOADS_DIR=$SMOKE_UP "$PY" seed_demo.py --reset) || ok=0
    # API dashboard cần đăng nhập (tài khoản quản trị tạo lần đầu, mật khẩu mặc định khi chưa đặt).
    ADMIN_PASS="${RESCUE_ADMIN_PASSWORD:-${RESCUE_DASHBOARD_PASSWORD:-cuuho2026}}"
    TOKEN=$(curl -sf -H 'Content-Type: application/json' \
      -d "{\"username\":\"${RESCUE_ADMIN_USERNAME:-admin}\",\"password\":\"$ADMIN_PASS\"}" \
      http://127.0.0.1:8000/api/auth/login | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["token"])') || ok=0
    curl -sf -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/api/clusters | "$PY" -c \
      'import json,sys; d=json.load(sys.stdin); print("clusters:", len(d["clusters"]), "reports:", d["totalReports"])' || ok=0
    curl -sf -o /dev/null http://127.0.0.1:8000/ || ok=0
    curl -sf -o /dev/null http://127.0.0.1:8000/static/js/main.js || ok=0
    kill "$SPID" 2>/dev/null; wait "$SPID" 2>/dev/null
    rm -rf "$BE/$SMOKE_DB" "$BE/$SMOKE_UP"
    if [[ $ok -eq 1 ]]; then record "Smoke test" "PASS"; else record "Smoke test" "FAIL"; fi
  fi
fi

echo
echo "================ TỔNG KẾT ================"
status=0
for r in "${RESULTS[@]}"; do
  printf '  %-22s %s\n' "${r%%|*}" "${r#*|}"
  [[ "${r#*|}" == FAIL* ]] && status=1
done
exit $status
