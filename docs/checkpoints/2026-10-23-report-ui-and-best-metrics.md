# Báo cáo: giao diện và chỉ số tốt nhất — 23/10/2026

- Đã cập nhật `report/build/content/content.pdf` (142 trang). Giữ bản trước chỉnh sửa tại `report/build/ui-review/content-before.pdf` (132 trang, file build không theo dõi).
- Mục 2.7 nằm tại trang in 40–48 (trang PDF 60–68), gồm hai actor người dân và quản trị viên ứng dụng di động. Đưa đủ 20 ảnh user, 6 ảnh admin vào 9 hình, mỗi ảnh xuất hiện đúng một lần và có mô tả (a)/(b)/(c).
- In đậm giá trị mô tả tốt nhất ở các bảng so sánh chương 4, gồm đồng hạng. Nhóm so sánh theo runtime, điều kiện stress, cặp R/L, máy và cấu hình mạng. Giữ nguyên các số liệu; không xếp hạng cỡ mẫu, ma trận đếm, CI, đường kính cụm và p-value; RQ3 là tương phản đối chứng khác nhau nên không gắn nhãn phương án tối ưu.
- Định dạng bảng sinh được duy trì qua `scripts/highlight_results.py`, dùng từ hai bộ xuất bảng hiện có. Sáu kiểm tra mới đạt; đối chiếu bảng với HEAD sau loại bỏ textbf xác nhận mọi giá trị giữ nguyên.
- XeLaTeX/BibTeX biên dịch thành công; đã xem trang giao diện và bảng kết quả, xác nhận chữ đậm trong font PDF. Log cuối không overfull, undefined references/citations hoặc nhãn trùng. `git diff --check -- report` đạt.
- `check_report.py` chưa đạt do bốn nguồn đồ thị đã lệch hash provenance: seed1024/pth_onnx_pte/summary.json, all_predictions.csv; fp32_ptq_qat/summary.json; prunning_st/summary.json. Giữ nguyên đồ thị theo phạm vi yêu cầu. Còn hai ghi chú hành chính cũ.
- Không chạy lại huấn luyện, benchmark hoặc E2E; không commit/push. Không chỉnh các thay đổi sản phẩm đang có trong workspace.
