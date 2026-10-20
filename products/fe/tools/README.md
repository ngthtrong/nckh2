# Chạy benchmark MobileNetV3 seed 159

Hướng dẫn này dùng checkpoint và config đã train ở `model/Edge Ai/mobilenetv3_large_dataset_v4_seed159`, đồng thời lưu artifact trong `model/Edge Ai/seed159` và báo cáo trong `reports/seed159`.

## Chuẩn bị

Mở PowerShell tại thư mục `nckh2/products/fe/tools` trước khi chạy các lệnh. Các đường dẫn bên dưới đều tương đối với thư mục này. Lệnh được viết cho PowerShell; hãy dùng môi trường Python đã cài các thư viện của dự án.

Khai báo các đường dẫn một lần trong phiên PowerShell:

```powershell
$run = '..\model\Edge Ai\seed159'
$reports = '..\reports\seed159'
$model = '..\model\Edge Ai\mobilenetv3_large_dataset_v4_seed159\flood_mobilenetv3_large_best.pth'
$config = '..\model\Edge Ai\mobilenetv3_large_dataset_v4_seed159\config_mobilenetv3_large.json'
$split = '..\model\Edge Ai\split_train_val_test_mobilenetv3_large.csv'
$dataset = '..\model\Dataset_Flood'
$export = Join-Path $run 'Export'
$ptq = Join-Path $run 'PTQ'
$qat = Join-Path $run 'QAT'
$structured = Join-Path $run 'StructuredPruning_v1'
```

Checkpoint, config, split và dataset phải tồn tại. Split CSV là file dùng chung tại `model/Edge Ai`; không thay bằng CSV được tạo từ một seed khác. Các script xuất sẽ tự tạo thư mục con cần thiết dưới `$run` và `$reports`.

## 1. Xuất baseline FP32 và ExecuTorch

Tạo ONNX FP32 và manifest trước. Sau đó xuất PTE; lệnh thứ hai cập nhật cùng manifest để ghi nhận cả ONNX và PTE.

```powershell
python convert_model.py --checkpoint $model --config $config --output "$export\flood_mobilenetv3_large.onnx" --manifest "$export\model_manifest.json"
python export_executorch.py --checkpoint $model --config $config --output-dir $export --manifest "$export\model_manifest.json"
```

Artifact: `model/Edge Ai/seed159/Export/`.

## 2. Sàng lọc unstructured pruning

Đây là bước sàng lọc các mức sparsity trên validation; script không fine-tune và không xuất model. Kết quả ở `reports/seed159/pruning/`.

```powershell
python benchmark_pruning.py --checkpoint $model --config $config --split-csv $split --dataset-dir $dataset --source-manifest "$export\model_manifest.json" --output-dir "$reports\pruning"
```

## 3. Tạo model PTQ và QAT

PTQ hiệu chỉnh từ ONNX FP32 bằng ảnh trong train split. QAT fine-tune từ checkpoint seed 159, dùng đúng config, split và manifest FP32.

```powershell
python quantize_model.py --onnx "$export\flood_mobilenetv3_large.onnx" --config $config --split-csv $split --dataset-dir $dataset --source-manifest "$export\model_manifest.json" --out-dir $ptq --report-dir "$reports\quantization"
```

```powershell
python qat_finetune.py --checkpoint $model --config $config --split-csv $split --dataset-dir $dataset --fp32-onnx "$export\flood_mobilenetv3_large.onnx" --source-manifest "$export\model_manifest.json" --out-onnx "$qat\flood_mobilenetv3_large.qat.int8.onnx" --out-checkpoint "$qat\flood_mobilenetv3_large_qat_best.pth"
```

PTQ lưu model và manifest trong `model/Edge Ai/seed159/PTQ/`; báo cáo trong `reports/seed159/quantization/`. QAT lưu model, checkpoint và manifest trong `model/Edge Ai/seed159/QAT/`.

## 4. Structured pruning và xuất model

Lệnh pruning tạo checkpoint fine-tuned tại `$structured`. Sau đó export ONNX/PTE của model structured-pruned.

```powershell
python structured_pruning.py --checkpoint $model --config $config --split-csv $split --dataset-dir $dataset --output-dir $structured
```

```powershell
python export_structured_model.py --checkpoint "$structured\flood_mobilenetv3_large_structured_best.pt" --source-checkpoint $model --config $config --output-dir "$export\pruning_st" --manifest "$export\pruning_st\model_manifest.json"
```

Structured artifacts nằm trong `model/Edge Ai/seed159/StructuredPruning_v1/` và `model/Edge Ai/seed159/Export/pruning_st/`.

**Chạy lại structured pruning:** script từ chối ghi đè một output directory đã có nội dung để bảo toàn checkpoint và log. Nếu checkpoint `flood_mobilenetv3_large_structured_best.pt` đã tồn tại và muốn dùng lại, bỏ qua lệnh `structured_pruning.py`. Nếu muốn train một lượt mới, đổi `$structured` sang một thư mục mới, ví dụ `Join-Path $run 'StructuredPruning_v2'`, rồi dùng cùng biến đó ở các lệnh compare và export.

## 5. Kiểm tra và so sánh trên test

Chạy sau khi đã tạo các artifact tương ứng. Không dùng kết quả test để chọn tham số hay tiếp tục fine-tune; dùng validation cho việc đó.

Xác minh pipeline PTH/ONNX:

```powershell
python verify_pipeline.py --checkpoint $model --onnx "$export\flood_mobilenetv3_large.onnx" --manifest "$export\model_manifest.json" --config $config --split-csv $split --dataset-dir $dataset --report-dir "$reports\verification"
```

So sánh PTH, ONNX và PTE:

```powershell
python compare_models.py --checkpoint $model --onnx "$export\flood_mobilenetv3_large.onnx" --pte "$export\flood_mobilenetv3_large.pte" --manifest "$export\model_manifest.json" --config $config --split-csv $split --dataset-dir $dataset --report-dir "$reports\pth_onnx_pte"
```

So sánh checkpoint structured-pruned với baseline:

```powershell
python compare_structured_pruning.py --checkpoint $model --pruned "$structured\flood_mobilenetv3_large_structured_best.pt" --config $config --split-csv $split --dataset-dir $dataset --report-dir "$reports\structured_pruning_compare"
```

So sánh FP32 với PTQ INT8:

```powershell
python compare_fp32_int8.py --fp32 "$export\flood_mobilenetv3_large.onnx" --int8 "$ptq\flood_mobilenetv3_large.int8.onnx" --manifest "$export\model_manifest.json" --int8-manifest "$ptq\model_manifest_int8.json" --config $config --split-csv $split --dataset-dir $dataset --report-dir "$reports\fp32_int8"
```

So sánh FP32, PTQ và QAT:

```powershell
python compare_fp32_ptq_qat.py --fp32 "$export\flood_mobilenetv3_large.onnx" --ptq "$ptq\flood_mobilenetv3_large.int8.onnx" --qat "$qat\flood_mobilenetv3_large.qat.int8.onnx" --qat-checkpoint "$qat\flood_mobilenetv3_large_qat_best.pth" --manifest "$export\model_manifest.json" --ptq-manifest "$ptq\model_manifest_int8.json" --qat-manifest "$qat\model_manifest_qat.json" --config $config --split-csv $split --dataset-dir $dataset --report-dir "$reports\fp32_ptq_qat"
```

So sánh baseline và structured-pruned qua PTH/ONNX/PTE:

```powershell
python benchmark_structured_exports.py --checkpoint $model --baseline-onnx "$export\flood_mobilenetv3_large.onnx" --baseline-pte "$export\flood_mobilenetv3_large.pte" --baseline-manifest "$export\model_manifest.json" --structured-checkpoint "$structured\flood_mobilenetv3_large_structured_best.pt" --onnx "$export\pruning_st\flood_mobilenetv3_large_structured.onnx" --pte "$export\pruning_st\flood_mobilenetv3_large_structured.pte" --manifest "$export\pruning_st\model_manifest.json" --config $config --split-csv $split --dataset-dir $dataset --report-dir "$reports\structured_exports"
```

## Ghi chú

- Các lệnh compare mặc định chạy toàn bộ test split; không thêm `--limit` nếu cần số liệu benchmark cuối cùng. `--limit` chỉ phù hợp để kiểm tra nhanh.
- `benchmark_pruning.py` dùng validation để sàng lọc; các script compare dùng test để báo cáo kết quả cuối. `structured_pruning.py` cũng đánh giá test split một lần khi kết thúc; không chọn cấu hình dựa trên các metric test.
- `structured_pruning.py` cần `torch-pruning` và môi trường PyTorch phù hợp. QAT cũng cần các thư viện huấn luyện và export theo cấu hình của repo.
- `sample_input.npy` là file dữ liệu mẫu, không phải script benchmark.
