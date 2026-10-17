# So sánh model trên test split

Scope: full_test; số ảnh: 256.
Critical error: khoảng cách severity >= 2.
CPU máy tính, không phải benchmark mobile. PTH/ONNX: 1 luồng; PTE theo runtime.

| Model | Accuracy | Macro-F1 | Balanced acc | Critical errors | ECE | Brier | Median ms | MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 75.78% | 74.26% | 73.87% | 3 (1.17%) | 0.04124 | 0.34262 | 82.20 | 48.51 |
| structured_pruned | 80.08% | 78.26% | 78.38% | 4 (1.56%) | 0.04346 | 0.30145 | 69.57 | 16.06 |

## Thời gian suy luận

Batch=1; 3 warmup/model không tính vào thống kê. Không gồm load model, preprocessing, validation hay logging.
P95: khoảng 95% lượt chạy có latency không vượt mức này. Tổng chỉ cộng thời gian gọi predict, không phải toàn pipeline.

| Model | Mean ms | Median ms | P95 ms | Min ms | Max ms | Tổng inference s |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 83.82 | 82.20 | 107.53 | 56.29 | 204.21 | 21.458 |
| structured_pruned | 69.65 | 69.57 | 83.27 | 51.33 | 110.77 | 17.830 |

Sai số trên probabilities sau softmax; không phải raw logits hay kết quả Android.

| Cặp | Top-1 agreement | Max abs diff | MAE | RMSE | Cosine mean | Probabilities close |
|---|---:|---:|---:|---:|---:|---|
| baseline_vs_structured_pruned | 82.42% | 0.76080841 | 0.10082239 | 0.16652456 | 0.9177383184 | False |

Tolerance: atol=1e-05, rtol=0.0001. Agreement không đồng nghĩa xác suất giống hệt hoặc accuracy 100%.
Smoke subset không thay thế metric full test.
