# So sánh model trên test split

Scope: full_test; số ảnh: 256.
Critical error: khoảng cách severity >= 2.
CPU máy tính, không phải benchmark mobile. PTH/ONNX: 1 luồng; PTE theo runtime.

| Model | Accuracy | Macro-F1 | Balanced acc | Critical errors | ECE | Brier | Median ms | MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fp32 | 76.17% | 74.54% | 74.07% | 5 (1.95%) | 0.06350 | 0.34483 | 31.26 | 16.04 |
| int8 | 71.88% | 70.33% | 70.07% | 5 (1.95%) | 0.08125 | 0.39027 | 32.20 | 4.51 |

## Thời gian suy luận

Batch=1; 3 warmup/model không tính vào thống kê. Không gồm load model, preprocessing, validation hay logging.
P95: khoảng 95% lượt chạy có latency không vượt mức này. Tổng chỉ cộng thời gian gọi predict, không phải toàn pipeline.

| Model | Mean ms | Median ms | P95 ms | Min ms | Max ms | Tổng inference s |
|---|---:|---:|---:|---:|---:|---:|
| fp32 | 43.63 | 31.26 | 98.94 | 24.36 | 317.67 | 11.170 |
| int8 | 48.09 | 32.20 | 134.03 | 23.19 | 382.03 | 12.312 |

Sai số trên probabilities sau softmax; không phải raw logits hay kết quả Android.

| Cặp | Top-1 agreement | Max abs diff | MAE | RMSE | Cosine mean | Probabilities close |
|---|---:|---:|---:|---:|---:|---|
| fp32_vs_int8 | 86.72% | 0.51784837 | 0.063072115 | 0.099901222 | 0.9642355442 | False |

Tolerance: atol=1e-05, rtol=0.0001. Agreement không đồng nghĩa xác suất giống hệt hoặc accuracy 100%.
Smoke subset không thay thế metric full test.
