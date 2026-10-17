# So sánh model trên test split

Scope: full_test; số ảnh: 256.
PTE status: executed.
Critical error: khoảng cách severity >= 2.
CPU máy tính, không phải benchmark mobile. PTH/ONNX: 1 luồng; PTE theo runtime.

| Model | Accuracy | Macro-F1 | Balanced acc | Critical errors | ECE | Brier | Median ms | MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| pth | 75.78% | 74.26% | 73.87% | 3 (1.17%) | 0.04124 | 0.34262 | 66.47 | 48.51 |
| onnx | 75.78% | 74.26% | 73.87% | 3 (1.17%) | 0.04124 | 0.34262 | 28.58 | 16.04 |
| pte | 75.78% | 74.26% | 73.87% | 3 (1.17%) | 0.04124 | 0.34262 | 30.73 | 16.06 |

## Thời gian suy luận

Batch=1; 3 warmup/model không tính vào thống kê. Không gồm load model, preprocessing, validation hay logging.
P95: khoảng 95% lượt chạy có latency không vượt mức này. Tổng chỉ cộng thời gian gọi predict, không phải toàn pipeline.

| Model | Mean ms | Median ms | P95 ms | Min ms | Max ms | Tổng inference s |
|---|---:|---:|---:|---:|---:|---:|
| pth | 59.11 | 66.47 | 95.41 | 19.32 | 141.46 | 15.133 |
| onnx | 24.15 | 28.58 | 38.46 | 8.90 | 58.77 | 6.182 |
| pte | 35.82 | 30.73 | 63.06 | 17.94 | 90.77 | 9.170 |

Sai số trên probabilities sau softmax; không phải raw logits hay kết quả Android.

| Cặp | Top-1 agreement | Max abs diff | MAE | RMSE | Cosine mean | Probabilities close |
|---|---:|---:|---:|---:|---:|---|
| pth_vs_onnx | 100.00% | 2.1457672e-06 | 2.2653224e-07 | 3.8056129e-07 | 1.0000000000 | True |
| pth_vs_pte | 100.00% | 2.9206276e-06 | 2.752551e-07 | 4.7177762e-07 | 1.0000000000 | True |
| onnx_vs_pte | 100.00% | 4.529953e-06 | 2.7276602e-07 | 4.6922748e-07 | 1.0000000000 | True |

Tolerance: atol=1e-05, rtol=0.0001. Agreement không đồng nghĩa xác suất giống hệt hoặc accuracy 100%.
Smoke subset không thay thế metric full test.
