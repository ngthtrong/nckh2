# So sánh model trên test split

Scope: full_test; số ảnh: 256.
PTE status: executed.
Critical error: khoảng cách severity >= 2.
CPU máy tính, không phải benchmark mobile. PTH/ONNX: 1 luồng; PTE theo runtime.

| Model | Accuracy | Macro-F1 | Balanced acc | Critical errors | ECE | Brier | Median ms | MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| pth | 76.17% | 74.54% | 74.07% | 5 (1.95%) | 0.06350 | 0.34483 | 65.87 | 48.51 |
| onnx | 76.17% | 74.54% | 74.07% | 5 (1.95%) | 0.06350 | 0.34483 | 25.93 | 16.04 |
| pte | 76.17% | 74.54% | 74.07% | 5 (1.95%) | 0.06350 | 0.34483 | 45.31 | 16.06 |

## Thời gian suy luận

Batch=1; 3 warmup/model không tính vào thống kê. Không gồm load model, preprocessing, validation hay logging.
P95: khoảng 95% lượt chạy có latency không vượt mức này. Tổng chỉ cộng thời gian gọi predict, không phải toàn pipeline.

| Model | Mean ms | Median ms | P95 ms | Min ms | Max ms | Tổng inference s |
|---|---:|---:|---:|---:|---:|---:|
| pth | 78.26 | 65.87 | 156.27 | 37.81 | 539.01 | 20.034 |
| onnx | 28.06 | 25.93 | 36.60 | 13.00 | 156.84 | 7.183 |
| pte | 48.44 | 45.31 | 65.87 | 27.16 | 155.30 | 12.401 |

Sai số trên probabilities sau softmax; không phải raw logits hay kết quả Android.

| Cặp | Top-1 agreement | Max abs diff | MAE | RMSE | Cosine mean | Probabilities close |
|---|---:|---:|---:|---:|---:|---|
| pth_vs_onnx | 100.00% | 3.0100346e-06 | 2.7510876e-07 | 5.060725e-07 | 1.0000000000 | True |
| pth_vs_pte | 100.00% | 5.0067902e-06 | 2.8638175e-07 | 5.1579728e-07 | 1.0000000000 | True |
| onnx_vs_pte | 100.00% | 3.3378601e-06 | 3.2284373e-07 | 5.5636666e-07 | 1.0000000000 | True |

Tolerance: atol=1e-05, rtol=0.0001. Agreement không đồng nghĩa xác suất giống hệt hoặc accuracy 100%.
Smoke subset không thay thế metric full test.
