# So sánh model trên test split

Scope: full_test; số ảnh: 256.
Critical error: khoảng cách severity >= 2.
CPU máy tính, không phải benchmark mobile. PTH/ONNX: 1 luồng; PTE theo runtime.

| Model | Accuracy | Macro-F1 | Balanced acc | Critical errors | ECE | Brier | Median ms | MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 75.78% | 74.09% | 73.67% | 4 (1.56%) | 0.09822 | 0.34120 | 39.31 | 48.51 |
| structured_pruned | 77.34% | 75.19% | 75.34% | 1 (0.39%) | 0.05622 | 0.33108 | 34.65 | 16.07 |

## Thời gian suy luận

Batch=1; 3 warmup/model không tính vào thống kê. Không gồm load model, preprocessing, validation hay logging.
P95: khoảng 95% lượt chạy có latency không vượt mức này. Tổng chỉ cộng thời gian gọi predict, không phải toàn pipeline.

| Model | Mean ms | Median ms | P95 ms | Min ms | Max ms | Tổng inference s |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 51.16 | 39.31 | 108.97 | 18.36 | 197.52 | 13.097 |
| structured_pruned | 43.60 | 34.65 | 83.88 | 17.58 | 201.94 | 11.161 |

Sai số trên probabilities sau softmax; không phải raw logits hay kết quả Android.

| Cặp | Top-1 agreement | Max abs diff | MAE | RMSE | Cosine mean | Probabilities close |
|---|---:|---:|---:|---:|---:|---|
| baseline_vs_structured_pruned | 81.25% | 0.75570822 | 0.10114802 | 0.16421394 | 0.9178050756 | False |

Tolerance: atol=1e-05, rtol=0.0001. Agreement không đồng nghĩa xác suất giống hệt hoặc accuracy 100%.
Smoke subset không thay thế metric full test.
