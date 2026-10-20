# So sánh model trên test split

Scope: full_test; số ảnh: 256.
PTE status: executed.
Critical error: khoảng cách severity >= 2.
CPU máy tính, không phải benchmark mobile. PTH/ONNX: 1 luồng; PTE theo runtime.

| Model | Accuracy | Macro-F1 | Balanced acc | Critical errors | ECE | Brier | Median ms | MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| pth | 75.78% | 74.09% | 73.67% | 4 (1.56%) | 0.09822 | 0.34120 | 39.65 | 48.51 |
| onnx | 75.78% | 74.09% | 73.67% | 4 (1.56%) | 0.09822 | 0.34120 | 13.97 | 16.04 |
| pte | 75.78% | 74.09% | 73.67% | 4 (1.56%) | 0.09822 | 0.34120 | 32.76 | 16.06 |

## Thời gian suy luận

Batch=1; 3 warmup/model không tính vào thống kê. Không gồm load model, preprocessing, validation hay logging.
P95: khoảng 95% lượt chạy có latency không vượt mức này. Tổng chỉ cộng thời gian gọi predict, không phải toàn pipeline.

| Model | Mean ms | Median ms | P95 ms | Min ms | Max ms | Tổng inference s |
|---|---:|---:|---:|---:|---:|---:|
| pth | 37.49 | 39.65 | 51.64 | 18.83 | 80.19 | 9.598 |
| onnx | 14.18 | 13.97 | 20.34 | 8.75 | 28.38 | 3.631 |
| pte | 33.76 | 32.76 | 56.48 | 10.42 | 67.76 | 8.643 |

Sai số trên probabilities sau softmax; không phải raw logits hay kết quả Android.

| Cặp | Top-1 agreement | Max abs diff | MAE | RMSE | Cosine mean | Probabilities close |
|---|---:|---:|---:|---:|---:|---|
| pth_vs_onnx | 100.00% | 2.3245811e-06 | 2.5085433e-07 | 4.0402539e-07 | 1.0000000000 | True |
| pth_vs_pte | 100.00% | 3.2484531e-06 | 2.8162401e-07 | 4.6087052e-07 | 1.0000000000 | True |
| onnx_vs_pte | 100.00% | 3.4868717e-06 | 2.8708951e-07 | 4.8474232e-07 | 1.0000000000 | True |

Tolerance: atol=1e-05, rtol=0.0001. Agreement không đồng nghĩa xác suất giống hệt hoặc accuracy 100%.
Smoke subset không thay thế metric full test.
