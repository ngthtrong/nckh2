# So sánh model trên test split

Scope: full_test; số ảnh: 256.
PTE status: executed.
Critical error: khoảng cách severity >= 2.
CPU máy tính, không phải benchmark mobile. PTH/ONNX: 1 luồng; PTE theo runtime.

| Model | Accuracy | Macro-F1 | Balanced acc | Critical errors | ECE | Brier | Median ms | MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline_pth | 76.17% | 74.54% | 74.07% | 5 (1.95%) | 0.06350 | 0.34483 | 33.16 | 48.51 |
| structured_pth | 76.17% | 74.47% | 74.60% | 4 (1.56%) | 0.05488 | 0.33582 | 28.91 | 16.06 |
| baseline_onnx | 76.17% | 74.54% | 74.07% | 5 (1.95%) | 0.06350 | 0.34483 | 12.71 | 16.04 |
| structured_onnx | 76.17% | 74.47% | 74.60% | 4 (1.56%) | 0.05488 | 0.33582 | 20.32 | 15.81 |
| baseline_pte | 76.17% | 74.54% | 74.07% | 5 (1.95%) | 0.06350 | 0.34483 | 25.62 | 16.06 |
| structured_pte | 76.17% | 74.47% | 74.60% | 4 (1.56%) | 0.05488 | 0.33581 | 32.43 | 15.83 |

## Thời gian suy luận

Batch=1; 3 warmup/model không tính vào thống kê. Không gồm load model, preprocessing, validation hay logging.
P95: khoảng 95% lượt chạy có latency không vượt mức này. Tổng chỉ cộng thời gian gọi predict, không phải toàn pipeline.

| Model | Mean ms | Median ms | P95 ms | Min ms | Max ms | Tổng inference s |
|---|---:|---:|---:|---:|---:|---:|
| baseline_pth | 34.87 | 33.16 | 51.14 | 18.31 | 96.02 | 8.926 |
| structured_pth | 30.08 | 28.91 | 46.71 | 17.92 | 74.02 | 7.701 |
| baseline_onnx | 13.42 | 12.71 | 20.00 | 8.80 | 27.34 | 3.436 |
| structured_onnx | 21.78 | 20.32 | 31.83 | 14.74 | 59.46 | 5.576 |
| baseline_pte | 28.31 | 25.62 | 52.32 | 8.24 | 90.59 | 7.247 |
| structured_pte | 36.97 | 32.43 | 68.16 | 6.36 | 84.02 | 9.464 |

Sai số trên probabilities sau softmax; không phải raw logits hay kết quả Android.

| Cặp | Top-1 agreement | Max abs diff | MAE | RMSE | Cosine mean | Probabilities close |
|---|---:|---:|---:|---:|---:|---|
| baseline_pth_vs_structured_pth | 81.64% | 0.62684524 | 0.092759311 | 0.15177209 | 0.9291270375 | False |
| baseline_pth_vs_baseline_onnx | 100.00% | 3.0100346e-06 | 2.7510876e-07 | 5.060725e-07 | 1.0000000000 | True |
| baseline_pth_vs_structured_onnx | 81.64% | 0.62684643 | 0.092759296 | 0.15177205 | 0.9291270971 | False |
| baseline_pth_vs_baseline_pte | 100.00% | 5.0067902e-06 | 2.8638175e-07 | 5.1579728e-07 | 1.0000000000 | True |
| baseline_pth_vs_structured_pte | 81.64% | 0.62684548 | 0.092759281 | 0.15177213 | 0.9291269779 | False |
| structured_pth_vs_baseline_onnx | 81.64% | 0.62684488 | 0.092759296 | 0.15177206 | 0.9291270375 | False |
| structured_pth_vs_structured_onnx | 100.00% | 8.136034e-06 | 4.7644102e-07 | 9.9333856e-07 | 1.0000000000 | True |
| structured_pth_vs_baseline_pte | 81.64% | 0.62684536 | 0.092759341 | 0.15177212 | 0.9291269779 | False |
| structured_pth_vs_structured_pte | 100.00% | 1.7225742e-05 | 1.018437e-06 | 2.0542817e-06 | 1.0000000000 | True |
| baseline_onnx_vs_structured_onnx | 81.64% | 0.62684613 | 0.092759274 | 0.15177203 | 0.9291270971 | False |
| baseline_onnx_vs_baseline_pte | 100.00% | 3.3378601e-06 | 3.2284373e-07 | 5.5636666e-07 | 1.0000000000 | True |
| baseline_onnx_vs_structured_pte | 81.64% | 0.62684518 | 0.092759266 | 0.1517721 | 0.9291269779 | False |
| structured_onnx_vs_baseline_pte | 81.64% | 0.62684661 | 0.092759311 | 0.15177209 | 0.9291270375 | False |
| structured_onnx_vs_structured_pte | 100.00% | 1.3619661e-05 | 1.1177835e-06 | 2.2052739e-06 | 1.0000000000 | True |
| baseline_pte_vs_structured_pte | 81.64% | 0.62684566 | 0.092759311 | 0.15177216 | 0.9291269779 | False |

Tolerance: atol=1e-05, rtol=0.0001. Agreement không đồng nghĩa xác suất giống hệt hoặc accuracy 100%.
Smoke subset không thay thế metric full test.
