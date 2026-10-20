# Lượng tử hóa INT8 mô hình MobileNetV3-Large

Lượng tử hóa tĩnh QDQ (trọng số INT8 per-channel, kích hoạt UINT8), hiệu chỉnh trên
200 ảnh TRAIN phân tầng theo lớp; onnxruntime 1.30.0,
CPU 1 luồng.

| Chỉ số | FP32 | INT8 |
|---|---:|---:|
| Kích thước file | 16.0 MB | 4.5 MB |
| Độ trễ suy luận (trung vị, CPU máy tính) | 31.5 ms | 34.3 ms |
| Accuracy trên 256 ảnh TEST | 75.78% | 73.05% |
| Macro-F1 trên 256 ảnh TEST | 74.09% | 71.25% |
| Trùng nhãn INT8 so với FP32 | – | 83.59% |

Metric chỉ lấy test trong `..\model\Edge Ai\split_train_val_test_mobilenetv3_large.csv` (đúng CSV của checkpoint, không chia lại).
Seed calibration: 159; input: 256×256.
Độ trễ đo trên CPU máy tính sau 3 lượt warmup, không bao gồm preprocessing,
không phải trên điện thoại. Manifest INT8 riêng: `..\model\Edge Ai\seed159\PTQ\model_manifest_int8.json`; không thay đổi FP32/PTE.

FP32: `flood_mobilenetv3_large.onnx` sha256 `dd39078001ddcedc…`;
INT8: `flood_mobilenetv3_large.int8.onnx` sha256 `8926129aa6bbb4b1…`.
