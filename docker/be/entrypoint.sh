#!/bin/sh
# Khởi động backend. Nạp dữ liệu BÁN TỔNG HỢP khi SEED_RUN được đặt và DB còn trống
# (hoặc SEED_RESET=1). Dữ liệu này có nhãn source=synthetic, không phải báo cáo thật.
set -eu

if [ -n "${SEED_RUN:-}" ]; then
  if [ ! -s "$RESCUE_DB_FILE" ] || [ "${SEED_RESET:-0}" = "1" ]; then
    echo ">> Nạp dữ liệu mô phỏng run_${SEED_RUN} vào $RESCUE_DB_FILE"
    python seed_demo.py --run "$SEED_RUN" --reset
  fi
fi

exec python -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" \
  --proxy-headers --forwarded-allow-ips='*'
