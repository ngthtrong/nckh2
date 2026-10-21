# Kết quả giả lập mạng yếu

RUN_ID: 20261005-102040. Đã có 2313/2313 lượt hợp lệ duy nhất; 2313 dòng đo thô. **Đủ lượt.**

Đầu vào: 257 ảnh val × 3 mạng × 3 chế độ × 1 lượt/ảnh. Chạy tuần tự.
CSV đầu vào SHA256: cdef5620b7e4d6d7ec48c18f06bab9323e76f4360c9847120f4e02684865c497.

Metadata cố định như runner gốc; nhãn CSV chỉ dùng truy vết, không chạy MobileNetV3. Ảnh original giữ nguyên byte; compressed là JPEG quality 60, giảm cạnh ngắn về 1024 px khi ảnh đủ lớn, không phóng to ảnh nhỏ. Ảnh nhỏ có thể lớn hơn sau khi nén lại.

Các mức 2G/3G/4G là cấu hình do nhóm đặt, không phải phép đo mạng di động thật. Timeout metadata 30 s, upload 60 s. Độ trễ dưới đây chỉ tính lượt thành công.
wire_bytes_up là byte proxy chuyển vào socket backend (có header HTTP), không bao gồm overhead TCP/IP và không thay thế kích thước toàn bộ payload khi timeout.

Có 0 dòng quá tải không đưa vào bảng; vẫn giữ trong CSV. Resume chạy phần chưa có lượt hợp lệ, không chạy lại thất bại mạng hợp lệ.
2313 dòng không có load average (ví dụ trên Windows); để trống, không giả thành 0 và không áp dụng bộ lọc tải cho các dòng đó.

| Mạng | Chế độ | Thành công / lượt | Thành công (%) | Ảnh gửi trung vị (B) | Byte proxy trung vị (B) | Median thành công (s) | p95 thành công (s) | Lỗi định dạng |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2G (EDGE) | metadata | 257/257 | 100.00 | 0 | 1011 | 1.488 | 1.524 | 0 |
| 2G (EDGE) | compressed | 257/257 | 100.00 | 25457 | 26558 | 5.666 | 25.230 | 0 |
| 2G (EDGE) | original | 230/257 | 89.49 | 40103 | 41202 | 5.526 | 38.973 | 1 |
| 3G | metadata | 257/257 | 100.00 | 0 | 1011 | 0.476 | 0.495 | 0 |
| 3G | compressed | 257/257 | 100.00 | 25457 | 26558 | 1.056 | 3.798 | 0 |
| 3G | original | 255/257 | 99.22 | 40103 | 41202 | 1.350 | 14.117 | 1 |
| 4G | metadata | 257/257 | 100.00 | 0 | 1011 | 0.145 | 0.165 | 0 |
| 4G | compressed | 257/257 | 100.00 | 25457 | 26558 | 0.211 | 0.532 | 0 |
| 4G | original | 256/257 | 99.61 | 40103 | 41202 | 0.259 | 1.762 | 1 |

## Nguyên nhân thất bại

- NETWORK_ERROR: 27 lượt.
- UNSUPPORTED_IMAGE: 3 lượt.

Tỷ lệ thành công tính mọi nguyên nhân. UNSUPPORTED_IMAGE/HTTP 415 là lỗi định dạng, không kết luận là lỗi mạng. Backend hiện nhận JPEG, PNG, WebP và từ chối AVIF original; vẫn thử ảnh AVIF và giữ kết quả, không tự đổi hoặc bỏ ảnh.
