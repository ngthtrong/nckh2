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
- Xuất 13 bảng: chia ảnh, ma trận/lớp, định dạng FP32, PTQ/QAT, audit metric, pruning, RQ1 benchmark/stress, RQ2 alignment/robustness/sensitivity và RQ3 hiệu ghép cặp theo seed.
- Ghi SHA-256 của 18 nguồn trực tiếp, commit đầu vào và kết quả audit trong `provenance.json`.

Snapshot hiện tại có 1.702 ảnh, train/validation/test = 1.189/257/256. Các ảnh và hash khớp split. FP32 và pruning có metric khớp CSV dự đoán. PTQ/QAT có khác biệt summary/CSV được công bố trong bảng `image-metric-audit.tex`; script in `REVIEW REQUIRED` nhưng vẫn xuất **cả số summary được gắn nhãn và bảng đối chiếu**, không sửa artifact gốc. Đây là trạng thái cần rà soát, không phải kiểm tra metric nén đạt.

Script dừng nếu ảnh/config/split hoặc danh sách ảnh test không khớp. `source_commit` là commit nguồn trước các chỉnh sửa báo cáo chưa commit, không chứng minh toàn bộ working tree sạch. Timing, runtime và metric vẫn thuộc những lần chạy đã lưu; không phải benchmark mới trên máy hiện tại hoặc Android.

RQ1 dùng `rq1_results` làm nguồn stress chính. `rq1_results_v2` được giữ là replication độc lập không gộp. RQ3 dùng bảng suy luận theo 40 seed, không dùng 120 hàng seed–điều kiện làm cỡ mẫu độc lập. Các renderer `paper/short_results.tex` và `paper/generated/revision_results.tex` không phải nguồn số liệu RQ1–RQ3 của bản thảo dài đang dùng.
