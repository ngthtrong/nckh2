# So sánh model trên test split

Scope: full_test; số ảnh: 256.
Critical error: khoảng cách severity >= 2.
CPU máy tính, không phải benchmark mobile. PTH/ONNX: 1 luồng; PTE theo runtime.

| Model | Accuracy | Macro-F1 | Balanced acc | Critical errors | ECE | Brier | Median ms | MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fp32 | 75.78% | 74.26% | 73.87% | 3 (1.17%) | 0.04124 | 0.34262 | 11.07 | 16.04 |
| int8 | 66.80% | 64.36% | 64.58% | 17 (6.64%) | 0.06248 | 0.43775 | 10.01 | 4.51 |

## Thời gian suy luận

Batch=1; 3 warmup/model không tính vào thống kê. Không gồm load model, preprocessing, validation hay logging.
P95: khoảng 95% lượt chạy có latency không vượt mức này. Tổng chỉ cộng thời gian gọi predict, không phải toàn pipeline.

| Model | Mean ms | Median ms | P95 ms | Min ms | Max ms | Tổng inference s |
|---|---:|---:|---:|---:|---:|---:|
| fp32 | 16.87 | 11.07 | 38.85 | 8.97 | 69.07 | 4.320 |
| int8 | 16.35 | 10.01 | 41.66 | 8.32 | 62.35 | 4.186 |

Sai số trên probabilities sau softmax; không phải raw logits hay kết quả Android.

| Cặp | Top-1 agreement | Max abs diff | MAE | RMSE | Cosine mean | Probabilities close |
|---|---:|---:|---:|---:|---:|---|
| fp32_vs_int8 | 77.34% | 0.60099655 | 0.090080835 | 0.14449276 | 0.9189519882 | False |

Tolerance: atol=1e-05, rtol=0.0001. Agreement không đồng nghĩa xác suất giống hệt hoặc accuracy 100%.
Smoke subset không thay thế metric full test.
