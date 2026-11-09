# CSV đánh giá mô hình nhận diện trên điện thoại

Xuất ngày 22/10/2026 từ các JSON schema v2 tại `products/fe/reports/seed159/mobile/` và `products/fe/reports/seed1024/mobile/`. Không chạy lại suy luận. Không thay nguồn benchmark seed 42 lịch sử của báo cáo.

- `summary.csv`: 32 phiên máy × seed × biến thể × runtime; gồm Accuracy, macro-Precision/Recall/F1, Precision/Recall/F1 lớp high, MAE/RMSE thứ bậc, balanced accuracy, mean/P50/P95 (ms), cấu hình thiết bị, model/hash, thời điểm UTC, run ID và đường dẫn/hash JSON nguồn.
- `realme15.csv`, `redminote11.csv`, `redminote13.csv`, `samsungs10e.csv`: cùng cột với summary, tách theo mẫu máy.
- `class_metrics.csv`: 128 hàng, precision/recall/F1 và support của từng lớp trong mỗi phiên.
- `predictions.csv`: 8.192 hàng dự đoán từng ảnh; giữ ID, nhãn thật, dự đoán, confidence, latencyMs, đường dẫn ảnh và JSON nguồn.
- `coverage.csv`: đủ 32 tổ hợp AVAILABLE; đã bổ sung ONNX seed 1024 cắt tỉa trên Redmi Note 13, không còn tổ hợp MISSING.

Các tỷ lệ lưu dạng 0–1; thời gian tính bằng ms. P50/P95 dùng nearest-rank như app. `variant=pruning` chuẩn hóa cách viết tên thư mục `seed159-prunning`, không đổi nguồn.

Precision/Recall/F1 từng lớp có sẵn trong `classMetrics` của JSON. `macro_precision` và `macro_recall` lấy trung bình bằng trọng số bốn lớp; `macro_recall` bằng balanced accuracy. Macro-F1 lấy trung bình F1 từng lớp, không tính lại từ macro-Precision/Recall. F1 cân bằng Precision và Recall, trong khi Accuracy chỉ đo tỷ lệ đoán đúng tổng thể.

JSON gốc chưa ghi MAE/RMSE. Hai cột `ordinal_mae`, `ordinal_rmse` được tính bổ sung từ 256 dự đoán của mỗi phiên, không sửa JSON hay chạy lại model. Ánh xạ `non_flood=0, low=1, medium=2, high=3`; MAE là trung bình khoảng cách tuyệt đối, RMSE là căn trung bình khoảng cách bình phương. Đơn vị là mức thứ bậc quy ước, không phải mét nước; thấp hơn tốt hơn. Thứ tự này khác chỉ số output `[low, medium, high, non_flood]`, không dùng `label_idx` để tính sai số. CSV so sánh bốn model lấy trung bình MAE/RMSE của tám phiên (RMSE trung bình, không phải RMSE tính trên dữ liệu gộp).

Đã đối chiếu đủ 256 sample ID/nhãn của mỗi phiên với split test, hash split, trạng thái complete, số lỗi, ma trận nhầm lẫn, Accuracy, macro-F1, chỉ số từng lớp, mean/P50/P95 và hash artifact runtime trong provenance. Cột `validation=PASS` chỉ có nghĩa các kiểm tra tính nhất quán này đạt, không phải chứng nhận model phù hợp cứu hộ thực địa. Mỗi tổ hợp chỉ có một phiên lưu; chưa có SoC/RAM, nhiệt độ, hash APK hay commit build trong JSON. Hash model là thông tin ghi trong artifact, không tự xác nhận APK đã cài nếu thiếu hash APK.

Tái xuất từ thư mục gốc repo:

```powershell
python report/scripts/export_phone_benchmarks.py
```

Mục 4.2.4 của báo cáo đã có ba bảng chính và đánh giá lựa chọn; phụ lục công bố đủ 32 cấu hình và 128 hàng chỉ số từng lớp.

## So sánh và lựa chọn baseline/pruning

- `model_comparison.csv`: bảng đơn giản bốn phương án của seed 159 và 1024, chỉ số chất lượng, lỗi nặng, độ trễ theo runtime và cờ lựa chọn.
- `selection_steps.csv`: ba bước chọn — baseline/pruning trong seed 159, trong seed 1024, rồi so sánh hai phương án thắng.
- `model_comparison.md`: bảng dễ đọc, tiêu chí lựa chọn và các đánh đổi cần giữ khi diễn giải.

Tái xuất bằng `python report/scripts/compare_phone_benchmarks.py`. Tiêu chí của phân tích là macro-F1 trung bình cao nhất, sau đó Accuracy nếu bằng nhau; kết quả ưu tiên seed 1024 pruning trên bộ benchmark đã lưu. Đây là lựa chọn dựa trên test, chưa phải xác nhận độc lập cho model sau lựa chọn. Các cột tỷ lệ trong bảng so sánh mang hậu tố `_pct` dùng thang 0–100, khác thang 0–1 của `summary.csv`; chênh lệch `_pp` tính bằng điểm phần trăm. Các cột `mean_p50`/`mean_p95` là trung bình percentile của bốn máy trong cùng runtime, không phải percentile của dữ liệu gộp.

## Đối chiếu ONNX và ExecuTorch/PTE

- `onnx_pte_comparison.md`: bảng dễ đọc cho seed 1024 pruning, tốc độ từng máy, chất lượng và kết luận lựa chọn.
- `onnx_pte_comparison.csv`: 16 cặp máy/model của seed 159 và 1024, baseline/pruning. Các chỉ số có `_both` dùng chung cho hai runtime vì đã xác nhận trùng nhãn 256/256 ảnh trong mỗi cặp; thời gian mean/P50/P95 và đường dẫn JSON nguồn tách riêng cho ONNX/PTE.
- `runtime_summary.csv`: tám hàng seed/model/runtime; trung bình chỉ số chất lượng và thời gian trên bốn máy, cùng cờ lựa chọn seed 1024 pruning + PTE.

Tái xuất: `python report/scripts/compare_phone_runtimes.py`. PTE nhanh hơn ONNX về mean/P50/P95 ở cả 16 cặp đã lưu, với cùng dự đoán top-1; chưa phải bảo đảm ưu thế trên mọi thiết bị. Các phiên không được lặp nhiều lần hoặc kiểm soát đầy đủ nhiệt độ/tải. Độ trễ đo classifyImage (giải mã, tiền xử lý, suy luận), không đo toàn luồng gửi báo cáo.

## Bảng trong báo cáo LaTeX

Chạy `python report/scripts/build_phone_report_tables.py` để đối chiếu JSON gốc và sinh ba bảng chính, bốn bảng phụ lục tại `report/generated/tables/phone-*.tex`. Công cụ đọc CSV theo cấu trúc thư mục `evaluate_*` hiện tại, không di chuyển dữ liệu hoặc chạy lại model. `make -C report results` cũng thực hiện bước này.
