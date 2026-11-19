# Lệnh export và benchmark seed 1024

Chạy bằng PowerShell trong môi trường Python đã dùng export, có ExecuTorch
1.4.1. Chạy từng lệnh và dừng nếu lệnh trước báo lỗi. Kết quả mới lưu vào
`products/fe/reports/seed1024`; các model tối ưu mới dùng thư mục riêng.

Đã có full test PTH/ONNX/PTE seed 1024: 256 ảnh, Accuracy 75,78125%,
macro-F1 74,2649179%, top-1 agreement 100%. Không cần chạy lại phần này
nếu checkpoint, export, split và môi trường chưa thay đổi.

## 1. Biến đường dẫn và kiểm tra checkpoint

```powershell
$project = 'E:\RHNA\1Visual\NCKH\nckh2'
$fe = "$project\products\fe"
$tools = "$fe\tools"
$edge = "$fe\model\Edge Ai"
$reports = "$fe\reports\seed1024"
$optimized = "$edge\seed1024"

$config = Get-Content -LiteralPath "$edge\config_mobilenetv3_large.json" -Raw | ConvertFrom-Json
if ($config.seed -ne 1024) { throw 'Config không phải seed 1024' }
$actual = (Get-FileHash -LiteralPath "$edge\flood_mobilenetv3_large_best.pth" -Algorithm SHA256).Hash
$expected = (Get-FileHash -LiteralPath "$edge\mobilenetv3_large_dataset_v4_seed1024\flood_mobilenetv3_large_best.pth" -Algorithm SHA256).Hash
if ($actual -ne $expected) { throw 'Checkpoint gốc không khớp bản seed 1024' }

New-Item -ItemType Directory -Force -Path "$reports", "$optimized\Quantize", "$optimized\QAT", "$optimized\StructuredPruning", "$optimized\Export\pruning_st" | Out-Null
```

## 2. Export và full test FP32 — chỉ chạy lại khi cần

```powershell
rtk proxy python "$tools\convert_model.py"
rtk proxy python "$tools\export_executorch.py"

rtk proxy python "$tools\verify_pipeline.py" --full-test --report-dir "$reports\verification"
rtk proxy python "$tools\compare_models.py" --report-dir "$reports\pth_onnx_pte"
```

Không dùng `--limit` hoặc `--skip-pte` cho kết quả đầy đủ ba runtime.
`verify_pipeline.py` kiểm tra kỹ thuật PTH/ONNX; `compare_models.py` đo cả
PTH/ONNX/PTE, metric phân loại, sai số xác suất, latency và dung lượng.

## 3. Tạo lại PTQ/QAT và benchmark lượng tử hóa

Chỉ cần phần này khi muốn thay các bảng lượng tử hóa lịch sử bằng seed 1024.
PTQ dùng calibration trên train; QAT có fine-tune, có thể tốn thời gian/GPU.

```powershell
rtk proxy python "$tools\quantize_model.py" `
  --onnx "$edge\Export\flood_mobilenetv3_large.onnx" `
  --config "$edge\config_mobilenetv3_large.json" `
  --split-csv "$edge\split_train_val_test_mobilenetv3_large.csv" `
  --out-dir "$optimized\Quantize" `
  --report-dir "$reports\quantization"

rtk proxy python "$tools\qat_finetune.py" `
  --out-onnx "$optimized\QAT\flood_mobilenetv3_large.qat.int8.onnx" `
  --out-checkpoint "$optimized\QAT\flood_mobilenetv3_large_qat_best.pth"

rtk proxy python "$tools\compare_fp32_ptq_qat.py" `
  --ptq "$optimized\Quantize\flood_mobilenetv3_large.int8.onnx" `
  --ptq-manifest "$optimized\Quantize\model_manifest_int8.json" `
  --qat "$optimized\QAT\flood_mobilenetv3_large.qat.int8.onnx" `
  --qat-checkpoint "$optimized\QAT\flood_mobilenetv3_large_qat_best.pth" `
  --qat-manifest "$optimized\QAT\model_manifest_qat.json" `
  --report-dir "$reports\fp32_ptq_qat"
```

Các đối số FP32/checkpoint/config/split không ghi ở trên dùng mặc định là
checkpoint seed 1024 và bộ export hiện tại tại gốc `Edge Ai`. Không dùng lại
PTQ/QAT seed 42 để so với FP32 seed 1024.

## 4. Tạo lại structured pruning, export và benchmark

Chỉ cần phần này khi muốn thay bảng pruning lịch sử. Script fine-tune dùng
train/validation; đánh giá cuối cùng vẫn dùng test cố định. Mặc định pruning
ratio 0,01 và tối đa 35 epoch theo cấu hình hiện tại.

```powershell
rtk proxy python "$tools\structured_pruning.py" `
  --output-dir "$optimized\StructuredPruning"

rtk proxy python "$tools\export_structured_model.py" `
  --checkpoint "$optimized\StructuredPruning\flood_mobilenetv3_large_structured_best.pt" `
  --output-dir "$optimized\Export\pruning_st" `
  --format all

rtk proxy python "$tools\benchmark_structured_exports.py" `
  --structured-checkpoint "$optimized\StructuredPruning\flood_mobilenetv3_large_structured_best.pt" `
  --onnx "$optimized\Export\pruning_st\flood_mobilenetv3_large_structured.onnx" `
  --pte "$optimized\Export\pruning_st\flood_mobilenetv3_large_structured.pte" `
  --manifest "$optimized\Export\pruning_st\model_manifest.json" `
  --report-dir "$reports\pruning_st"
```

Không cần chạy thêm `benchmark_pruning.py` để sinh bảng structured pruning:
đó là bước sàng lọc mask không fine-tune, không thay benchmark trên đây.

## 5. Đưa model vào APK và đo trên điện thoại

```powershell
Copy-Item -LiteralPath "$edge\Export\flood_mobilenetv3_large.onnx" -Destination "$fe\app\assets\models\model.onnx"
Copy-Item -LiteralPath "$edge\Export\flood_mobilenetv3_large.pte" -Destination "$fe\app\assets\models\model.pte"
Copy-Item -LiteralPath "$edge\Export\model_manifest.json" -Destination "$fe\app\assets\models\model_manifest.json"
Copy-Item -LiteralPath "$edge\Export\model_metadata.json" -Destination "$fe\app\assets\models\model_metadata.json"

rtk proxy python "$project\products\be\build_benchmark_package.py"

Push-Location "$fe\app"
rtk proxy flutter build apk --release
rtk proxy flutter devices
rtk proxy flutter install --release
Pop-Location
```

`flutter install` yêu cầu chọn thiết bị nếu có nhiều thiết bị. Có thể cài
thủ công APK ở `app/build/app/outputs/flutter-apk/app-release.apk`.

Gói `products/be/benchmark_package.rhb` phải được cập nhật vào backend đang
phục vụ app. Nếu chạy backend native của repo, mở terminal riêng:

```powershell
rtk proxy powershell -NoProfile -File "$project\products\scripts\demo\run_server.ps1" -NoReload
```

Nếu backend đã chạy theo cách khác, dùng quy trình khởi động lại hiện có để
đọc gói mới. Không chạy hai server cùng cổng.

Trên app: Cài đặt → đăng nhập tài khoản có quyền `admin` → tải ONNX nếu cần
so sánh hai runtime → xóa gói cũ và tải lại gói → chọn **Cả hai** → **Chạy benchmark thật**. Sau khi chạy xong,
bấm **Tải JSON** ở từng kết quả ONNX/PTE, chọn thư mục Downloads và lưu file
gốc; tránh dán JSON dài qua ứng dụng chat. Chạy ít nhất ba lượt trên cùng
máy, giữ file riêng cho từng runtime/lượt. Ghi kèm seed/hash
model, hash APK/split, thiết bị/SoC/Android, ngày đo và điều kiện nhiệt độ.
Tên dataset là fingerprint split, không xác nhận seed của model.

Để bộ xuất báo cáo đọc một lượt đo: lưu hai object JSON ONNX và PTE nối tiếp
trong cùng file UTF-8, ví dụ
`products/fe/reports/seed1024/mobile/run01.json`. Không ghép các lượt thành
một object trung bình; giữ toàn bộ file gốc để truy nguyên.

## 6. Cập nhật report bằng dữ liệu mới

`report/config/benchmark-sources.json` hiện chọn FP32, PTQ/QAT, pruning và
verification seed 1024. Mobile còn giữ bản seed 42 tại
`report/evidence/benchmarks/seed42/` trong khi chờ ba file seed 1024 đầy đủ;
các bản hiện tại bị cắt ở 20.000 ký tự và chưa được chọn vào báo cáo.
Chỉ đổi nhóm nào đã chạy xong và được đối chiếu:

| Trường | Giá trị sau khi có đủ kết quả seed 1024 |
|---|---|
| `quantization` | `products/fe/reports/seed1024/fp32_ptq_qat` |
| `pruning` | `products/fe/reports/seed1024/pruning_st` |
| `mobile.file` | `products/fe/reports/seed1024/mobile/run01.json` |
| `mobile.seed` | `1024` |

```powershell
rtk proxy python "$project\report\scripts\export_results.py"

# Môi trường riêng cho việc sinh hình, không thay thư viện môi trường model.
rtk proxy python -m venv "$project\report\build\visual-env"
rtk proxy "$project\report\build\visual-env\Scripts\python.exe" -m pip install -r "$project\report\scripts\requirements-figures.txt"
rtk proxy "$project\report\build\visual-env\Scripts\python.exe" "$project\report\scripts\build_figures.py"

rtk proxy python "$project\report\scripts\build.py" content
rtk proxy python "$project\report\scripts\check_report.py"
```

Bộ kiểm tra cuối cần `pdftotext` và `pdfinfo` trên PATH. PDF đầu ra ở
`report/build/content/content.pdf`. Không cần chạy lại RQ1–RQ3 nếu giữ
nguyên dữ liệu mô phỏng đã lưu; chỉ chạy lại khi thay đầu vào thí nghiệm.
