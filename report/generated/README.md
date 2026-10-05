# Bảng và số liệu sinh từ artifact

Chạy từ thư mục gốc repo:

```bash
python3 report/scripts/export_results.py
```

`make -C report content`, bản nội dung hai mặt và bốn sản phẩm riêng tự gọi bước xuất trước khi biên dịch. Không chỉnh tay `values.tex`, `tables/*.tex` hoặc `provenance.json`.

Bộ xuất sử dụng Python chuẩn, không huấn luyện hoặc thay đổi artifact gốc. Nó thực hiện:

- Đối chiếu toàn bộ ảnh với đường dẫn tương đối và MD5 trong split; kiểm tra nhóm MD5/perceptual/split không vượt train/validation/test.
- Kiểm tra hash config, hash split, số ảnh và scope của các summary ảnh.
- Kiểm tra CSV dự đoán dùng đúng tập test; tính lại ma trận nhầm lẫn, Accuracy và macro-F1.
- Xuất 14 bảng: chia ảnh, ma trận/lớp, định dạng FP32, PTQ/QAT, audit metric, pruning, RQ1 benchmark/stress, RQ2 alignment/robustness/sensitivity và RQ3 hiệu ghép cặp theo seed và benchmark ứng dụng.
- Ghi SHA-256 của 19 nguồn trực tiếp, commit đầu vào và kết quả audit trong `provenance.json`.

Snapshot hiện tại có 1.702 ảnh, train/validation/test = 1.189/257/256. Các ảnh và hash khớp split. FP32 và pruning có metric khớp CSV dự đoán. PTQ/QAT có khác biệt summary/CSV được công bố trong bảng `image-metric-audit.tex`; script in `REVIEW REQUIRED` nhưng vẫn xuất **cả số summary được gắn nhãn và bảng đối chiếu**, không sửa artifact gốc. Đây là trạng thái cần rà soát, không phải kiểm tra metric nén đạt.

Script dừng nếu ảnh/config/split hoặc danh sách ảnh test không khớp. `source_commit` là commit nguồn trước các chỉnh sửa báo cáo chưa commit, không chứng minh toàn bộ working tree sạch. Timing, runtime và metric vẫn thuộc những lần chạy đã lưu; không phải benchmark mới trên máy hiện tại hoặc Android.

RQ1 dùng `rq1_results` làm nguồn stress chính. `rq1_results_v2` được giữ là replication độc lập không gộp. RQ3 dùng bảng suy luận theo 40 seed, không dùng 120 hàng seed–điều kiện làm cỡ mẫu độc lập. Các renderer `paper/short_results.tex` và `paper/generated/revision_results.tex` không phải nguồn số liệu RQ1–RQ3 của bản thảo dài đang dùng.

## Hình và benchmark ứng dụng

`make -C report figures` sinh chín hình PDF/PNG từ artifact bằng `scripts/build_figures.py`. Môi trường mặc định là `report/build/visual-env/` nếu tồn tại, hoặc Python được cấu hình qua `FIGURE_PYTHON`; dependency ở `scripts/requirements-figures.txt`. Build nội dung dùng hình đã lưu, không tự cài dependency hoặc dựng lại hình.

`figure-provenance.json` giữ hash nguồn, script, hình, phiên bản thư viện/phông và các thống kê bổ sung. `make check` đối chiếu nguồn/hình và báo hình đã lỗi thời. Ảnh ví dụ được chọn bằng đường dẫn đầu tiên sau sắp xếp trong từng lớp/nhóm đúng–sai, không phải mẫu đại diện ngẫu nhiên.

`mobile_evidence.py` đọc hai object nối tiếp trong `samsung21se.json`, đối chiếu ID/nhãn test theo cách đóng gói package và tính lại confusion, Accuracy, macro-F1, từng lớp, mean/P50/P95. Hai runtime có đủ 256 ảnh và metric khớp dự đoán. Nguồn thiếu metadata thiết bị/asset/ngày đo; không được dùng để xác nhận một APK hoặc so trực tiếp latency với predict CPU.
