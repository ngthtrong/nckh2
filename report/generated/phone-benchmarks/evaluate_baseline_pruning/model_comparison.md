# So sánh baseline và pruning: seed 159, seed 1024

Tiêu chí lựa chọn của phân tích: ưu tiên macro-F1 trung bình; nếu bằng nhau thì ưu tiên Accuracy. Macro-Precision, macro-Recall, chỉ số lớp high, MAE/RMSE thứ bậc, lỗi nặng và độ trễ được giữ riêng để đánh giá đánh đổi. Đây không phải tiêu chí đã đăng ký trước thực nghiệm. F1 đã cân bằng Precision/Recall; Accuracy chỉ dùng khi macro-F1 bằng nhau.

| Seed | Model | Accuracy (%) | Macro-Precision (%) | Macro-Recall (%) | Macro-F1 (%) | MAE (mức) | RMSE (mức) | Chọn trong seed |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 159 | baseline | 75.10 | 73.77 | 73.04 | 73.29 | 0.2686 | 0.5616 |  |
| 159 | pruning | 76.56 | 74.19 | 74.75 | 74.26 | 0.2500 | 0.5376 | Có |
| 1024 | baseline | 75.68 | 74.67 | 73.84 | 74.15 | 0.2520 | 0.5191 |  |
| 1024 | pruning | 76.66 | 74.50 | 74.87 | 74.58 | 0.2461 | 0.5210 | Có |

## Lớp ngập cao và hiệu năng

| Seed | Model | Precision high (%) | Recall high (%) | F1 high (%) | Lỗi nặng TB/256 | TB P50 ONNX (ms) | TB P50 PTE (ms) |
|---|---|---:|---:|---:|---:|---:|---:|
| 159 | baseline | 82.51 | 76.39 | 79.33 | 4.00 | 127.48 | 63.65 |
| 159 | pruning | 75.72 | 86.57 | 80.78 | 3.00 | 123.41 | 64.04 |
| 1024 | baseline | 86.01 | 76.85 | 81.17 | 2.25 | 122.95 | 58.85 |
| 1024 | pruning | 80.85 | 87.96 | 84.25 | 3.25 | 139.96 | 59.45 |

## Chọn theo hai bước

- within_seed_159: chọn **seed159_pruning** so với seed159_baseline; macro-F1 tăng 0.969 điểm phần trăm, Accuracy tăng 1.465 điểm phần trăm.
- within_seed_1024: chọn **seed1024_pruning** so với seed1024_baseline; macro-F1 tăng 0.422 điểm phần trăm, Accuracy tăng 0.977 điểm phần trăm.
- between_seed_winners: chọn **seed1024_pruning** so với seed159_pruning; macro-F1 tăng 0.314 điểm phần trăm, Accuracy tăng 0.098 điểm phần trăm.

## Cách đọc và giới hạn

- Precision/Recall/F1 từng lớp có sẵn trong classMetrics của JSON; macro-Precision, macro-Recall và MAE/RMSE được tính bổ sung từ dữ liệu đã lưu, không phải một lượt benchmark mới. JSON gốc được giữ nguyên.
- F1_c = 2 × Precision_c × Recall_c / (Precision_c + Recall_c). Macro-F1 là trung bình F1 của bốn lớp, không phải F1 tính từ macro-Precision và macro-Recall. Macro-Precision/Recall cũng lấy trung bình bằng trọng số bốn lớp; macro-Recall bằng balanced accuracy.
- Precision cao nghĩa là trong các ảnh được dự đoán thuộc một lớp, phần lớn đúng lớp đó; Recall cao nghĩa là nhận ra được phần lớn ảnh thật của lớp đó. Chọn F1 nếu coi hai loại lỗi quan trọng tương đương. Nếu muốn ưu tiên tránh bỏ sót lớp high thì cần xác định chi phí lỗi/ngưỡng chấp nhận, chọn trên validation rồi xác nhận trên dữ liệu độc lập; không tự chỉnh threshold từ test. Không thể dựng đầy đủ đường Precision–Recall cho từng lớp từ JSON chỉ có confidence của top-1, thiếu vector xác suất bốn lớp.
- Ánh xạ thứ bậc: non_flood=0, low=1, medium=2, high=3. MAE = mean(|dự đoán − nhãn thật|), RMSE = sqrt(mean((dự đoán − nhãn thật)^2)); thấp hơn tốt hơn, RMSE phạt lệch nhiều mức mạnh hơn. Không dùng label_idx theo thứ tự output [low, medium, high, non_flood]. Giả định mỗi mức cách nhau một đơn vị là quy ước đánh giá, không phải mét nước hay chi phí cứu hộ.
- summary.csv và CSV từng máy có MAE/RMSE riêng cho từng phiên 256 ảnh. Trong bảng bốn model, MAE/RMSE là trung bình chỉ số của tám phiên; RMSE trung bình này không phải sqrt(MSE gộp). Các phiên dùng lại ảnh nên không phải quan sát độc lập.
- Nguồn: summary.csv, class_metrics.csv và predictions.csv cùng thư mục; JSON gốc được truy từ source_json. Tái xuất: `python report/scripts/compare_phone_benchmarks.py`.
- Mỗi hàng là trung bình bằng trọng số của 8 phiên (4 máy × 2 runtime), cùng 256 ảnh test. Không gộp thành 2.048 ảnh độc lập. ONNX/PTE của mỗi cấu hình máy/model có dự đoán top-1 giống nhau; việc lấy trung bình hai runtime không tăng số ảnh độc lập.
- TB P50/P95 là trung bình các P50/P95 của bốn máy trong cùng runtime, không phải percentile của dữ liệu gộp hay độ trễ cho một máy bất kỳ. Đối chiếu từng máy ở summary.csv; không dùng trung bình này để khẳng định ưu thế trên mọi thiết bị.
- Lỗi nặng là lệch ít nhất hai mức theo thứ tự non_flood → low → medium → high, cùng định nghĩa trong compare_models.py; không phải số ca gây hậu quả cứu hộ.
- Pruning seed 159 thắng về macro-F1 trên 3/4 máy; Samsung S10e có macro-F1 baseline nhỉnh hơn. Pruning seed 1024 thắng baseline về macro-F1 trên cả 4 máy.
- Giữa hai bản pruning, seed 1024 có macro-F1 cao hơn trên realme 15 và Samsung S10e; seed 159 cao hơn trên Redmi Note 11 và Redmi Note 13. Vì thế kết luận cuối là ưu tiên theo trung bình bộ máy này, không phải thắng trên mọi máy.
- Seed 1024 pruning có ít lợi thế Accuracy so với seed 159 pruning và có lỗi nặng trung bình cao hơn (3,25 so với 3,00); so với baseline 1024, lỗi nặng tăng từ 2,25 lên 3,25. Nếu ưu tiên ít lỗi nặng thay vì macro-F1 thì lựa chọn có thể khác.
- Seed 1024 pruning có ONNX trên Redmi Note 13 P50 239,020 ms, cao hơn seed 159 pruning 176,095 ms. Chưa có lặp nhiều phiên hoặc kiểm soát nhiệt độ/tải để quy nguyên nhân; không coi pruning luôn nhanh hơn.
- Chọn **seed 1024 pruning** theo tiêu chí chất lượng trên benchmark hiện có. Chênh macro-F1 chỉ khoảng 0,314 điểm phần trăm; chưa kiểm định ý nghĩa thống kê. Lựa chọn dựa trên test nên cần dữ liệu độc lập nếu muốn xác nhận chất lượng cuối cùng sau lựa chọn. Không sửa model triển khai hoặc điền mục điện thoại đang để trống trong báo cáo.
