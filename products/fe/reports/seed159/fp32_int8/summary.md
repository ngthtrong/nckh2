# So sánh model trên test split

Scope: full_test; số ảnh: 256.
Critical error: khoảng cách severity >= 2.
CPU máy tính, không phải benchmark mobile. PTH/ONNX: 1 luồng; PTE theo runtime.

| Model | Accuracy | Macro-F1 | Balanced acc | Critical errors | ECE | Brier | Median ms | MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fp32 | 75.78% | 74.09% | 73.67% | 4 (1.56%) | 0.09822 | 0.34120 | 29.81 | 16.04 |
| int8 | 73.05% | 71.25% | 71.53% | 6 (2.34%) | 0.10924 | 0.38562 | 32.41 | 4.51 |

## Thời gian suy luận

Batch=1; 3 warmup/model không tính vào thống kê. Không gồm load model, preprocessing, validation hay logging.
P95: khoảng 95% lượt chạy có latency không vượt mức này. Tổng chỉ cộng thời gian gọi predict, không phải toàn pipeline.

| Model | Mean ms | Median ms | P95 ms | Min ms | Max ms | Tổng inference s |
|---|---:|---:|---:|---:|---:|---:|
| fp32 | 29.21 | 29.81 | 51.46 | 8.72 | 93.18 | 7.479 |
| int8 | 30.57 | 32.41 | 52.74 | 8.32 | 89.50 | 7.825 |

Sai số trên probabilities sau softmax; không phải raw logits hay kết quả Android.

| Cặp | Top-1 agreement | Max abs diff | MAE | RMSE | Cosine mean | Probabilities close |
|---|---:|---:|---:|---:|---:|---|
| fp32_vs_int8 | 83.59% | 0.48416591 | 0.07548742 | 0.11141752 | 0.9562227726 | False |

Tolerance: atol=1e-05, rtol=0.0001. Agreement không đồng nghĩa xác suất giống hệt hoặc accuracy 100%.
Smoke subset không thay thế metric full test.
