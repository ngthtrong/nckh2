#!/usr/bin/env bash
# Chép model đã export vào fe/app/assets/models/ (thư mục git-ignore) để app bundle kèm.
#
#   scripts/demo/stage_model.sh                    # lấy từ "fe/model/Edge Ai"
#   scripts/demo/stage_model.sh --from /path/dir   # thư mục chứa file export khác
#
# App cần đủ 3 file: model.onnx, model.pte, model_manifest.json (có trường "version").
# Thiếu file nào thì app vẫn chạy nhưng AI on-device báo "chưa sẵn sàng".
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$ROOT/fe/model/Edge Ai"
DST="$ROOT/fe/app/assets/models"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from) SRC="$2"; shift ;;
    -h|--help) sed -n '2,8p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Tùy chọn không hợp lệ: $1" >&2; exit 2 ;;
  esac
  shift
done

ONNX="$SRC/flood_mobilenetv3_large.onnx"
PTE="$SRC/flood_mobilenetv3_large.pte"
MANIFEST="$SRC/model_manifest.json"

missing=0
for f in "$ONNX" "$PTE" "$MANIFEST"; do
  if [[ ! -f "$f" ]]; then
    echo "THIẾU: $f" >&2
    missing=1
  fi
done
if [[ $missing -eq 1 ]]; then
  cat >&2 <<EOF

Chưa đủ file model. Export lại (cần torch/torchvision/onnx/executorch, xem docs/huong_dan_chay_demo.md §4):
  python fe/tools/convert_model.py      --checkpoint <file .pth> --config <config .json>
  python fe/tools/export_executorch.py  --checkpoint <file .pth> --config <config .json>
Hai lệnh cùng ghi vào "fe/model/Edge Ai/" và cập nhật model_manifest.json.
EOF
  exit 1
fi

if ! python3 -c 'import json,sys; m=json.load(open(sys.argv[1])); assert m.get("version")' "$MANIFEST" 2>/dev/null; then
  echo "model_manifest.json không có trường \"version\" — app sẽ không nạp được model." >&2
  exit 1
fi

mkdir -p "$DST"
cp "$ONNX" "$DST/model.onnx"
cp "$PTE" "$DST/model.pte"
cp "$MANIFEST" "$DST/model_manifest.json"
echo "Đã chép model vào $DST:"
ls -la "$DST" | grep -v '\.gitkeep'
