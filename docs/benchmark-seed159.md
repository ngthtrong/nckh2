# Chạy so sánh PTH, ONNX và PTE của MobileNetV3 seed 159

Hướng dẫn đối chiếu ngày 20/10/2026. Mục tiêu là lấy **cùng mô hình seed 159 đã train**, xuất sang ONNX/PTE, rồi cho ba bản dự đoán trên cùng tập test để so chất lượng, confidence, tốc độ và dung lượng. Không cần huấn luyện lại để làm phép so sánh này.

## 1. Những gì hiện có và cần tạo

Thư mục train thực sự nằm thêm một cấp bên trong thư mục bạn tải về:

```text
products/fe/model/models/Final/
  mobilenetv3_large_dataset_v4_seed159-20260929T075441Z-1-001/
    mobilenetv3_large_dataset_v4_seed159/
      flood_mobilenetv3_large_best.pth
      config_mobilenetv3_large.json
      test_metrics_mobilenetv3_large.json
      ...
```

Dùng `best.pth` cho phép so sánh chính. File `last.pth` là checkpoint cuối, có thể khác mô hình được chọn tốt nhất trên validation.

Chưa thấy ONNX/PTE/manifest của seed 159 trong thư mục này, nên cần xuất mới. Không lấy ONNX/PTE đang có của seed 42 hoặc 1024 để ghép vào seed 159.

**Dữ liệu:** chỉ dùng các dòng `split=test` trong [CSV chia tập](<D:/nckh-flood-rescue/nckh2/products/fe/model/Edge Ai/split_train_val_test_mobilenetv3_large.csv>), rồi đọc 256 ảnh tương ứng từ [Dataset_Flood](D:/nckh-flood-rescue/nckh2/products/fe/model/Dataset_Flood). File `records_after_clean...csv` của seed 159 không có cột split, nên không thay được CSV chia tập.

Checkpoint seed 159 có ghi đường dẫn Colab tới CSV chia tập dùng chung; 1.702 bản ghi sạch (đường dẫn, nhãn, MD5, nhóm ảnh) khớp CSV hiện có. Tuy vậy, chưa có hash CSV gốc của lần train để xác nhận tuyệt đối phân công train/val/test của lần đó. Phép chạy dưới đây đánh giá theo CSV đang lưu trong repo; muốn khẳng định tái lập đúng test ban đầu cần đối chiếu bản CSV gốc trên Drive.

## 2. Mở PowerShell và khai báo đường dẫn

Chạy các bước trong cùng cửa sổ PowerShell. Chạy lần lượt; nếu một lệnh báo lỗi, dừng để xử lý trước khi sang lệnh kế tiếp.

```powershell
$project = 'D:\nckh-flood-rescue\nckh2'
$fe = Join-Path $project 'products\fe'
$tools = Join-Path $fe 'tools'
$model159 = Join-Path $fe 'model\models\Final\mobilenetv3_large_dataset_v4_seed159-20260929T075441Z-1-001\mobilenetv3_large_dataset_v4_seed159'
$checkpoint = Join-Path $model159 'flood_mobilenetv3_large_best.pth'
$config = Join-Path $model159 'config_mobilenetv3_large.json'
$split = Join-Path $fe 'model\Edge Ai\split_train_val_test_mobilenetv3_large.csv'
$dataset = Join-Path $fe 'model\Dataset_Flood'
$runTag = Get-Date -Format 'yyyyMMdd-HHmmss'
$export159 = Join-Path $fe "model\Edge Ai\seed159\Export\$runTag"
$reports159 = Join-Path $fe "reports\seed159\$runTag"
$manifest = Join-Path $export159 'model_manifest.json'
$onnx159 = Join-Path $export159 'flood_mobilenetv3_large.onnx'
$pte159 = Join-Path $export159 'flood_mobilenetv3_large.pte'

Set-Location $project
foreach ($file in @($checkpoint, $config, $split)) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
        throw "Thiếu file: $file"
    }
}
$cfg = Get-Content -LiteralPath $config -Raw | ConvertFrom-Json
if ($cfg.seed -ne 159) { throw 'Config không phải seed 159' }
New-Item -ItemType Directory -Force -Path $export159, $reports159 | Out-Null
```

Các đường dẫn đầu ra có thời gian riêng để phân biệt từng lần đo. `$config` lấy ngay trong thư mục seed 159; không dùng config mặc định ở gốc `Edge Ai`.

## 3. Chuẩn bị môi trường Python

Python mặc định đã kiểm tra trên máy hiện có torch/torchvision, nhưng chưa có `onnx`, `onnxruntime`, `executorch`. Nên dùng môi trường riêng để cài các công cụ này.

```powershell
python -m venv "$project\.venv-seed159"
$py = Join-Path $project '.venv-seed159\Scripts\python.exe'
& $py -m pip install --upgrade pip
& $py -m pip install 'torch>=2.4' 'torchvision>=0.19' 'numpy>=1.26' 'Pillow>=10.0' 'scikit-learn>=1.4' 'matplotlib>=3.8' 'onnx>=1.16' 'onnxruntime>=1.18'
& $py -m pip install 'executorch==1.4.1'
```

Các yêu cầu trên lấy từ [requirements của mô hình](D:/nckh-flood-rescue/nckh2/products/fe/requirements.txt). Exporter PTE hiện kiểm tra **đúng ExecuTorch 1.4.1**. Chưa cài hoặc chạy export trong lần viết hướng dẫn này, nên chưa xác nhận việc cài dependency trên môi trường của bạn sẽ thành công.

Nếu riêng lệnh cài ExecuTorch báo không có wheel phù hợp/lỗi dependency, giữ lỗi để xử lý môi trường PTE; có thể làm phép so sánh hai bản PTH/ONNX theo mục 7 sau khi các dependency của hai bản này đã cài thành công. Không dùng bản PTE cũ của seed khác để thay thế.

Nếu pip thay đổi torch khi cài ExecuTorch, dùng môi trường sau khi cài xong để thực hiện toàn bộ bước export và benchmark, không trộn các bước từ môi trường chưa hoàn chỉnh. Lưu phiên bản đã cài:

```powershell
& $py -m pip freeze | Set-Content -LiteralPath "$reports159\environment.txt" -Encoding utf8
```

## 4. Xuất seed 159 sang ONNX

File chạy: [convert_model.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/convert_model.py).

```powershell
& $py "$tools\convert_model.py" `
  --checkpoint "$checkpoint" `
  --config "$config" `
  --output "$onnx159" `
  --manifest "$manifest"
```

Kết quả cần có: `flood_mobilenetv3_large.onnx` và `model_manifest.json` trong `$export159`. Manifest ghi hash mô hình và hợp đồng đầu vào/nhãn để các bước sau kiểm tra chúng có khớp nhau không.

## 5. Xuất cùng checkpoint sang PTE

File chạy: [export_executorch.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/export_executorch.py). Bước này yêu cầu ExecuTorch 1.4.1 đã cài thành công.

```powershell
& $py "$tools\export_executorch.py" `
  --checkpoint "$checkpoint" `
  --config "$config" `
  --output-dir "$export159" `
  --manifest "$manifest"
```

Kết quả cần có: `flood_mobilenetv3_large.pte`, `model_metadata.json`; manifest được bổ sung hash PTE và phiên bản runtime. Hai bước export phải dùng đúng cùng `$checkpoint`, `$config` và `$manifest`.

## 6. Chạy đánh giá đầy đủ cả ba bản trên 256 ảnh test

File chạy: [compare_models.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/compare_models.py).

```powershell
& $py "$tools\compare_models.py" `
  --checkpoint "$checkpoint" `
  --onnx "$onnx159" `
  --pte "$pte159" `
  --manifest "$manifest" `
  --config "$config" `
  --split-csv "$split" `
  --dataset-dir "$dataset" `
  --report-dir "$reports159\pth_onnx_pte"
```

Không thêm `--limit` nếu muốn kết quả đủ 256 ảnh; không thêm `--skip-pte` khi báo cáo cả ba runtime. Công cụ đọc ảnh theo CSV, không tự dùng toàn bộ folder ảnh. Đây là benchmark CPU trên máy tính, chưa phải thời gian xử lý trong ứng dụng Android.

Có thể kiểm tra kỹ thuật PTH/ONNX riêng bằng [verify_pipeline.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/verify_pipeline.py). Đây là phép kiểm tra bổ sung, không thay benchmark ba bản:

```powershell
& $py "$tools\verify_pipeline.py" `
  --checkpoint "$checkpoint" `
  --onnx "$onnx159" `
  --manifest "$manifest" `
  --config "$config" `
  --split-csv "$split" `
  --dataset-dir "$dataset" `
  --full-test `
  --report-dir "$reports159\verification"
```

## 7. Phương án chỉ so PTH/ONNX khi PTE chưa sẵn sàng

Chạy mục 2–4, rồi dùng lệnh sau thay cho mục 5–6. Đây là kết quả hai runtime; ghi rõ PTE chưa thử.

```powershell
& $py "$tools\compare_models.py" `
  --checkpoint "$checkpoint" `
  --onnx "$onnx159" `
  --manifest "$manifest" `
  --config "$config" `
  --split-csv "$split" `
  --dataset-dir "$dataset" `
  --skip-pte `
  --report-dir "$reports159\pth_onnx_only"
```

## 8. Đọc các file sau khi chạy

Trong `$reports159\pth_onnx_pte` (hoặc `pth_onnx_only`) sẽ có:

| File | Dùng để biết điều gì? |
|---|---|
| `all_predictions.csv` | Mỗi ảnh được đoán thành lớp gì, confidence/xác suất từng lớp và thời gian ở từng runtime |
| `summary.json` | Chỉ số đầy đủ, seed, số ảnh, hash nguồn, runtime, độ đồng thuận và dung lượng |
| `summary.md` | Bảng kết quả dễ đọc |
| `compare.log` | Tiến trình chạy và chi tiết nếu lỗi |
| `confusion_*.png` | Các lớp nào bị nhầm với nhau |
| `calibration_*.png` | Mức tự tin có phù hợp tỷ lệ dự đoán đúng không |

Kiểm tra metadata có `seed=159`, `evaluation_scope=full_test`, `n_images=256`. Đọc Accuracy/macro-F1/recall high/lỗi nặng; ECE/Brier; top-1 agreement giữa PTH–ONNX/PTE; latency và dung lượng. Trùng nhãn 100% là điều cần kiểm tra, không phải giả định trước.

File train cũ [test_metrics_mobilenetv3_large.json](D:/nckh-flood-rescue/nckh2/products/fe/model/models/Final/mobilenetv3_large_dataset_v4_seed159-20260929T075441Z-1-001/mobilenetv3_large_dataset_v4_seed159/test_metrics_mobilenetv3_large.json) ghi Accuracy 75,78%, macro-F1 khoảng 74,09%, 4 lỗi nặng/256 ảnh. Đây là mốc lịch sử để đối chiếu, không phải kết quả của lệnh vừa hướng dẫn. Nếu đánh giá lại khác số, kiểm tra split/tiền xử lý/model trước, không sửa CSV cho khớp mốc cũ.

## 9. Nếu sau này muốn so INT8 hoặc mô hình đã bớt kênh tính toán

Đó là các phép thử tiếp theo, cần tạo phương án mới **từ seed 159**: PTQ dùng `quantize_model.py`; QAT dùng `qat_finetune.py`; thay cấu trúc dùng `structured_pruning.py`. Sau đó mới chạy các công cụ so sánh tương ứng. Không dùng INT8/pruning có sẵn từ seed 42/1024 làm ứng viên seed 159. Phần hướng dẫn này tập trung vào phép so PTH/ONNX/PTE FP32 của cùng checkpoint.

Không đổi [cấu hình nguồn báo cáo](D:/nckh-flood-rescue/nckh2/report/config/benchmark-sources.json) sang seed 159 trước khi có đủ kết quả đã kiểm tra. Giữ nguyên các bộ seed 42/1024 để còn đối chiếu phiên cũ và mới.
