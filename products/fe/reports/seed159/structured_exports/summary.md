# So sánh model trên test split

Scope: full_test; số ảnh: 256.
PTE status: executed.
Critical error: khoảng cách severity >= 2.
CPU máy tính, không phải benchmark mobile. PTH/ONNX: 1 luồng; PTE theo runtime.

| Model | Accuracy | Macro-F1 | Balanced acc | Critical errors | ECE | Brier | Median ms | MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline_pth | 75.78% | 74.09% | 73.67% | 4 (1.56%) | 0.09822 | 0.34120 | 41.42 | 48.51 |
| structured_pth | 77.34% | 75.19% | 75.34% | 1 (0.39%) | 0.05622 | 0.33108 | 26.26 | 16.07 |
| baseline_onnx | 75.78% | 74.09% | 73.67% | 4 (1.56%) | 0.09822 | 0.34120 | 10.11 | 16.04 |
| structured_onnx | 77.34% | 75.19% | 75.34% | 1 (0.39%) | 0.05622 | 0.33108 | 17.38 | 15.81 |
| baseline_pte | 75.78% | 74.09% | 73.67% | 4 (1.56%) | 0.09822 | 0.34120 | 26.37 | 16.06 |
| structured_pte | 77.34% | 75.19% | 75.34% | 1 (0.39%) | 0.05622 | 0.33108 | 47.74 | 15.84 |

## Thời gian suy luận

Batch=1; 3 warmup/model không tính vào thống kê. Không gồm load model, preprocessing, validation hay logging.
P95: khoảng 95% lượt chạy có latency không vượt mức này. Tổng chỉ cộng thời gian gọi predict, không phải toàn pipeline.

| Model | Mean ms | Median ms | P95 ms | Min ms | Max ms | Tổng inference s |
|---|---:|---:|---:|---:|---:|---:|
| baseline_pth | 40.02 | 41.42 | 56.89 | 17.48 | 76.80 | 10.246 |
| structured_pth | 28.05 | 26.26 | 42.31 | 17.40 | 72.56 | 7.182 |
| baseline_onnx | 12.33 | 10.11 | 19.28 | 8.80 | 30.46 | 3.156 |
| structured_onnx | 21.13 | 17.38 | 32.98 | 14.79 | 54.86 | 5.410 |
| baseline_pte | 30.90 | 26.37 | 53.97 | 7.76 | 65.05 | 7.911 |
| structured_pte | 47.15 | 47.74 | 73.26 | 6.09 | 84.03 | 12.071 |

Sai số trên probabilities sau softmax; không phải raw logits hay kết quả Android.

| Cặp | Top-1 agreement | Max abs diff | MAE | RMSE | Cosine mean | Probabilities close |
|---|---:|---:|---:|---:|---:|---|
| baseline_pth_vs_structured_pth | 81.25% | 0.75570822 | 0.10114802 | 0.16421394 | 0.9178050756 | False |
| baseline_pth_vs_baseline_onnx | 100.00% | 2.3245811e-06 | 2.5085433e-07 | 4.0402539e-07 | 1.0000000000 | True |
| baseline_pth_vs_structured_onnx | 81.25% | 0.75570881 | 0.1011479 | 0.16421376 | 0.9178053141 | False |
| baseline_pth_vs_baseline_pte | 100.00% | 3.2484531e-06 | 2.8162401e-07 | 4.6087052e-07 | 1.0000000000 | True |
| baseline_pth_vs_structured_pte | 81.25% | 0.75571072 | 0.10114796 | 0.16421397 | 0.9178051353 | False |
| structured_pth_vs_baseline_onnx | 81.25% | 0.7557084 | 0.10114802 | 0.16421396 | 0.9178050756 | False |
| structured_pth_vs_structured_onnx | 100.00% | 1.1920929e-05 | 5.9858246e-07 | 1.2619599e-06 | 1.0000000000 | True |
| structured_pth_vs_baseline_pte | 81.25% | 0.75570834 | 0.10114805 | 0.16421395 | 0.9178050756 | False |
| structured_pth_vs_structured_pte | 100.00% | 2.0951033e-05 | 1.347062e-06 | 2.7015365e-06 | 1.0000000000 | True |
| baseline_onnx_vs_structured_onnx | 81.25% | 0.75570893 | 0.10114792 | 0.16421378 | 0.9178053141 | False |
| baseline_onnx_vs_baseline_pte | 100.00% | 3.4868717e-06 | 2.8708951e-07 | 4.8474232e-07 | 1.0000000000 | True |
| baseline_onnx_vs_structured_pte | 81.25% | 0.7557109 | 0.10114797 | 0.16421399 | 0.9178051353 | False |
| structured_onnx_vs_baseline_pte | 81.25% | 0.75570887 | 0.10114793 | 0.16421377 | 0.9178053141 | False |
| structured_onnx_vs_structured_pte | 100.00% | 2.0056963e-05 | 1.2784695e-06 | 2.5879285e-06 | 1.0000000000 | True |
| baseline_pte_vs_structured_pte | 81.25% | 0.75571084 | 0.10114799 | 0.16421399 | 0.9178051949 | False |

Tolerance: atol=1e-05, rtol=0.0001. Agreement không đồng nghĩa xác suất giống hệt hoặc accuracy 100%.
Smoke subset không thay thế metric full test.
