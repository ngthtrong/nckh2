# So sánh model trên test split

Scope: full_test; số ảnh: 256.
Critical error: khoảng cách severity >= 2.
CPU máy tính, không phải benchmark mobile. PTH/ONNX: 1 luồng; PTE theo runtime.

| Model | Accuracy | Macro-F1 | Balanced acc | Critical errors | ECE | Brier | Median ms | MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| onnx_fp32 | 75.78% | 74.26% | 73.87% | 3 (1.17%) | 0.04124 | 0.34262 | 14.81 | 16.04 |
| ptq_int8 | 66.80% | 64.36% | 64.58% | 17 (6.64%) | 0.06248 | 0.43775 | 13.97 | 4.51 |
| qat_int8 | 46.48% | 42.91% | 46.10% | 45 (17.58%) | 0.01261 | 0.64491 | 53.11 | 4.57 |

## Thời gian suy luận

Batch=1; 3 warmup/model không tính vào thống kê. Không gồm load model, preprocessing, validation hay logging.
P95: khoảng 95% lượt chạy có latency không vượt mức này. Tổng chỉ cộng thời gian gọi predict, không phải toàn pipeline.

| Model | Mean ms | Median ms | P95 ms | Min ms | Max ms | Tổng inference s |
|---|---:|---:|---:|---:|---:|---:|
| onnx_fp32 | 16.94 | 14.81 | 25.29 | 11.14 | 107.82 | 4.337 |
| ptq_int8 | 16.06 | 13.97 | 25.51 | 10.84 | 40.20 | 4.110 |
| qat_int8 | 61.80 | 53.11 | 92.34 | 42.95 | 334.99 | 15.821 |

Sai số trên probabilities sau softmax; không phải raw logits hay kết quả Android.

| Cặp | Top-1 agreement | Max abs diff | MAE | RMSE | Cosine mean | Probabilities close |
|---|---:|---:|---:|---:|---:|---|
| onnx_fp32_vs_ptq_int8 | 77.34% | 0.60099655 | 0.090080835 | 0.14449276 | 0.9189519882 | False |
| onnx_fp32_vs_qat_int8 | 49.22% | 0.8215934 | 0.20838241 | 0.26776044 | 0.7417745590 | False |
| ptq_int8_vs_qat_int8 | 53.52% | 0.80508125 | 0.19123368 | 0.24923909 | 0.7701987028 | False |

Tolerance: atol=1e-05, rtol=0.0001. Agreement không đồng nghĩa xác suất giống hệt hoặc accuracy 100%.
Smoke subset không thay thế metric full test.
