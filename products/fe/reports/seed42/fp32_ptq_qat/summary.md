# So sánh model trên test split

Scope: full_test; số ảnh: 256.
Critical error: khoảng cách severity >= 2.
CPU máy tính, không phải benchmark mobile. PTH/ONNX: 1 luồng; PTE theo runtime.

| Model | Accuracy | Macro-F1 | Balanced acc | Critical errors | ECE | Brier | Median ms | MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| onnx_fp32 | 76.17% | 74.54% | 74.07% | 5 (1.95%) | 0.06350 | 0.34483 | 31.90 | 16.04 |
| ptq_int8 | 71.88% | 70.33% | 70.07% | 5 (1.95%) | 0.08125 | 0.39027 | 35.37 | 4.51 |
| qat_int8 | 52.34% | 50.57% | 50.88% | 38 (14.84%) | 0.04753 | 0.61261 | 121.36 | 4.57 |

## Thời gian suy luận

Batch=1; 3 warmup/model không tính vào thống kê. Không gồm load model, preprocessing, validation hay logging.
P95: khoảng 95% lượt chạy có latency không vượt mức này. Tổng chỉ cộng thời gian gọi predict, không phải toàn pipeline.

| Model | Mean ms | Median ms | P95 ms | Min ms | Max ms | Tổng inference s |
|---|---:|---:|---:|---:|---:|---:|
| onnx_fp32 | 29.05 | 31.90 | 50.04 | 8.89 | 72.56 | 7.437 |
| ptq_int8 | 30.11 | 35.37 | 53.11 | 8.39 | 82.41 | 7.709 |
| qat_int8 | 100.66 | 121.36 | 165.02 | 33.30 | 222.37 | 25.768 |

Sai số trên probabilities sau softmax; không phải raw logits hay kết quả Android.

| Cặp | Top-1 agreement | Max abs diff | MAE | RMSE | Cosine mean | Probabilities close |
|---|---:|---:|---:|---:|---:|---|
| onnx_fp32_vs_ptq_int8 | 86.72% | 0.51784837 | 0.063072115 | 0.099901222 | 0.9642355442 | False |
| onnx_fp32_vs_qat_int8 | 54.69% | 0.79957533 | 0.19022298 | 0.24708506 | 0.7786277533 | False |
| ptq_int8_vs_qat_int8 | 53.52% | 0.81934762 | 0.17005345 | 0.22289787 | 0.8083149195 | False |

Tolerance: atol=1e-05, rtol=0.0001. Agreement không đồng nghĩa xác suất giống hệt hoặc accuracy 100%.
Smoke subset không thay thế metric full test.
