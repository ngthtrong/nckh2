# So sánh model trên test split

Scope: full_test; số ảnh: 256.
PTE status: executed.
Critical error: khoảng cách severity >= 2.
CPU máy tính, không phải benchmark mobile. PTH/ONNX: 1 luồng; PTE theo runtime.

| Model | Accuracy | Macro-F1 | Balanced acc | Critical errors | ECE | Brier | Median ms | MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline_pth | 75.78% | 74.26% | 73.87% | 3 (1.17%) | 0.04124 | 0.34262 | 37.92 | 48.51 |
| structured_pth | 80.08% | 78.26% | 78.38% | 4 (1.56%) | 0.04346 | 0.30145 | 24.18 | 16.06 |
| baseline_onnx | 75.78% | 74.26% | 73.87% | 3 (1.17%) | 0.04124 | 0.34262 | 10.28 | 16.04 |
| structured_onnx | 80.08% | 78.26% | 78.38% | 4 (1.56%) | 0.04346 | 0.30145 | 17.02 | 15.81 |
| baseline_pte | 75.78% | 74.26% | 73.87% | 3 (1.17%) | 0.04124 | 0.34262 | 30.28 | 16.06 |
| structured_pte | 80.08% | 78.26% | 78.38% | 4 (1.56%) | 0.04346 | 0.30145 | 59.20 | 15.83 |

## Thời gian suy luận

Batch=1; 3 warmup/model không tính vào thống kê. Không gồm load model, preprocessing, validation hay logging.
P95: khoảng 95% lượt chạy có latency không vượt mức này. Tổng chỉ cộng thời gian gọi predict, không phải toàn pipeline.

| Model | Mean ms | Median ms | P95 ms | Min ms | Max ms | Tổng inference s |
|---|---:|---:|---:|---:|---:|---:|
| baseline_pth | 39.44 | 37.92 | 63.34 | 18.11 | 108.92 | 10.098 |
| structured_pth | 26.88 | 24.18 | 39.76 | 18.31 | 86.50 | 6.880 |
| baseline_onnx | 11.30 | 10.28 | 17.72 | 9.07 | 29.59 | 2.892 |
| structured_onnx | 18.79 | 17.02 | 27.65 | 14.75 | 38.57 | 4.810 |
| baseline_pte | 35.25 | 30.28 | 62.65 | 19.11 | 78.47 | 9.025 |
| structured_pte | 58.56 | 59.20 | 86.80 | 22.12 | 97.73 | 14.991 |

Sai số trên probabilities sau softmax; không phải raw logits hay kết quả Android.

| Cặp | Top-1 agreement | Max abs diff | MAE | RMSE | Cosine mean | Probabilities close |
|---|---:|---:|---:|---:|---:|---|
| baseline_pth_vs_structured_pth | 82.42% | 0.76080841 | 0.10082239 | 0.16652456 | 0.9177383184 | False |
| baseline_pth_vs_baseline_onnx | 100.00% | 2.1457672e-06 | 2.2653224e-07 | 3.8056129e-07 | 1.0000000000 | True |
| baseline_pth_vs_structured_onnx | 82.42% | 0.76080924 | 0.10082246 | 0.1665246 | 0.9177383184 | False |
| baseline_pth_vs_baseline_pte | 100.00% | 2.9206276e-06 | 2.752551e-07 | 4.7177762e-07 | 1.0000000000 | True |
| baseline_pth_vs_structured_pte | 82.42% | 0.76081014 | 0.10082241 | 0.16652454 | 0.9177383780 | False |
| structured_pth_vs_baseline_onnx | 82.42% | 0.76080823 | 0.1008224 | 0.16652454 | 0.9177384377 | False |
| structured_pth_vs_structured_onnx | 100.00% | 1.0445714e-05 | 7.050557e-07 | 1.4867284e-06 | 1.0000000000 | True |
| structured_pth_vs_baseline_pte | 82.42% | 0.76080889 | 0.10082242 | 0.16652455 | 0.9177383184 | False |
| structured_pth_vs_structured_pte | 100.00% | 1.0848045e-05 | 7.4710863e-07 | 1.5556604e-06 | 1.0000000000 | True |
| baseline_onnx_vs_structured_onnx | 82.42% | 0.76080906 | 0.10082247 | 0.16652458 | 0.9177383184 | False |
| baseline_onnx_vs_baseline_pte | 100.00% | 4.529953e-06 | 2.7276602e-07 | 4.6922748e-07 | 1.0000000000 | True |
| baseline_onnx_vs_structured_pte | 82.42% | 0.76080996 | 0.10082242 | 0.16652452 | 0.9177384377 | False |
| structured_onnx_vs_baseline_pte | 82.42% | 0.76080972 | 0.10082247 | 0.16652459 | 0.9177383184 | False |
| structured_onnx_vs_structured_pte | 100.00% | 8.8512897e-06 | 7.7225758e-07 | 1.5827427e-06 | 1.0000000000 | True |
| baseline_pte_vs_structured_pte | 82.42% | 0.76081061 | 0.10082243 | 0.16652453 | 0.9177384377 | False |

Tolerance: atol=1e-05, rtol=0.0001. Agreement không đồng nghĩa xác suất giống hệt hoặc accuracy 100%.
Smoke subset không thay thế metric full test.
