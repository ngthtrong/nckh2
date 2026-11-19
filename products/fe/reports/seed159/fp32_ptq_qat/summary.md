# So sánh model trên test split

Scope: full_test; số ảnh: 256.
Critical error: khoảng cách severity >= 2.
CPU máy tính, không phải benchmark mobile. PTH/ONNX: 1 luồng; PTE theo runtime.

| Model | Accuracy | Macro-F1 | Balanced acc | Critical errors | ECE | Brier | Median ms | MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| onnx_fp32 | 75.78% | 74.09% | 73.67% | 4 (1.56%) | 0.09822 | 0.34120 | 30.12 | 16.04 |
| ptq_int8 | 73.05% | 71.25% | 71.53% | 6 (2.34%) | 0.10924 | 0.38562 | 32.62 | 4.51 |
| qat_int8 | 47.27% | 42.95% | 44.83% | 42 (16.41%) | 0.05186 | 0.63656 | 105.56 | 4.57 |

## Thời gian suy luận

Batch=1; 3 warmup/model không tính vào thống kê. Không gồm load model, preprocessing, validation hay logging.
P95: khoảng 95% lượt chạy có latency không vượt mức này. Tổng chỉ cộng thời gian gọi predict, không phải toàn pipeline.

| Model | Mean ms | Median ms | P95 ms | Min ms | Max ms | Tổng inference s |
|---|---:|---:|---:|---:|---:|---:|
| onnx_fp32 | 27.72 | 30.12 | 41.67 | 9.09 | 60.84 | 7.096 |
| ptq_int8 | 29.37 | 32.62 | 44.15 | 8.54 | 53.44 | 7.520 |
| qat_int8 | 96.94 | 105.56 | 144.44 | 32.55 | 230.94 | 24.817 |

Sai số trên probabilities sau softmax; không phải raw logits hay kết quả Android.

| Cặp | Top-1 agreement | Max abs diff | MAE | RMSE | Cosine mean | Probabilities close |
|---|---:|---:|---:|---:|---:|---|
| onnx_fp32_vs_ptq_int8 | 83.59% | 0.48416591 | 0.07548742 | 0.11141752 | 0.9562227726 | False |
| onnx_fp32_vs_qat_int8 | 51.17% | 0.8212831 | 0.20098384 | 0.25832291 | 0.7592620850 | False |
| ptq_int8_vs_qat_int8 | 53.52% | 0.77322996 | 0.16212846 | 0.21154408 | 0.8151662350 | False |

Tolerance: atol=1e-05, rtol=0.0001. Agreement không đồng nghĩa xác suất giống hệt hoặc accuracy 100%.
Smoke subset không thay thế metric full test.
