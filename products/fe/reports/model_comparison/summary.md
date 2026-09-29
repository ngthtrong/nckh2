# Báo Cáo So Sánh Chi Tiết Model A (PyTorch Best.pth) vs Model B (ONNX Mobile)

## 📌 Kết Luận Phân Loại Trường Hợp (Case Decision)
> **CASE A — Hai model thực sự tương đương 100% (High Agreement & Identical Distribution)**

---

## 1. Prediction Agreement
- **Tổng số ảnh kiểm thử:** 1625
- **Số ảnh đồng thuận (Agreement count):** 1625
- **Số ảnh bất đồng (Disagreement count):** 0
- **Tỷ lệ đồng thuận (Agreement rate):** **100.0000%**
- **Tỷ lệ bất đồng (Disagreement rate):** **0.0000%**

---

## 2. Phân Tích Bất Đồng (Disagreement Breakdown)
- **Model A (PyTorch) đúng, Model B (ONNX) sai:** 0 ảnh
- **Model A (PyTorch) sai, Model B (ONNX) đúng:** 0 ảnh
- **Cả hai cùng sai (khác class):** 0 ảnh

---

## 3. So Sánh Metric Phân Loại (Classification Metrics)

| Chỉ số (Metric) | Model A (PyTorch Best.pth) | Model B (ONNX Mobile) | Chênh lệch (ONNX - PyTorch) |
| :--- | :---: | :---: | :---: |
| **Accuracy** | 86.58% | 86.58% | +0.00% |
| **Balanced Accuracy** | 85.29% | 85.29% | +0.00% |
| **Macro F1 Score** | 85.46% | 85.46% | +0.00% |
| **ECE (Calibration Error)** | 0.0370 | 0.0370 | -0.0000 |
| **Brier Score** | 0.2079 | 0.2079 | -0.0000 |

---

## 4. Bảng Chỉ Số Phân Bố Xác Suất (Distribution Comparison)

- **Cosine Similarity (Mean):** **0.99999774**
- **L1 Distance (Mean):** 0.00163993
- **Max Absolute Difference (Mean):** 0.00080658
- **Jensen-Shannon Divergence (Mean):** 0.00000136

---

## 📁 Tệp Báo Cáo Đã Xuất:
- `reports/model_comparison/summary.json`
- `reports/model_comparison/summary.md`
- `reports/model_comparison/all_predictions.csv`
- `reports/model_comparison/model_disagreement.csv`
- `reports/model_comparison/confusion_model_a.png`
- `reports/model_comparison/confusion_model_b.png`
- `reports/model_comparison/calibration_model_a.png`
- `reports/model_comparison/calibration_model_b.png`
