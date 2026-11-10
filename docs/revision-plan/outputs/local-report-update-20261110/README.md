# Cập nhật báo cáo từ kết quả local ngày 10/11/2026

Người dùng đã yêu cầu chỉnh sửa, bổ sung các nhận xét có bằng chứng hiện có, rồi liệt kê phần còn cần thực hiện hoặc bổ sung bằng chứng. Phạm vi đợt này là báo cáo và công cụ xuất số liệu; không huấn luyện/suy luận mới, sửa app/backend, thay model nguyên mẫu, sửa nhận xét chính thức hoặc thực hiện các nhánh thực địa.

- Nguồn: `thuc_nghiem_nq/notebook_bundle/local-work/local-20261110-04`.
- Bản sao chụp gọn: [source-manifest.json](source-manifest.json), 47 tệp, không sao chép trọng số.
- Hai checkpoint T2 seed 43 đang giải nén lệch hash được giữ nguyên; bản ZIP khớp SHA-256/CRC được ghi trong [checkpoint-audit.json](checkpoint-audit.json).
- Script [export_local_experiments.py](../../../../report/scripts/export_local_experiments.py) kiểm hash, ID và công thức metric; xuất ba bảng. CI bootstrap lấy từ artifact đã lưu, không phát lại trong bước biên tập.
- T2 local trở thành nguồn bảng silver hiện tại; số T2 cũ 50,73% vẫn lưu trong nguồn lịch sử và được nêu rõ trong nội dung. Frozen silver/public giữ nguyên và không được coi là dữ liệu xác nhận mới.
- Các biến pruning lịch sử, asset nguyên mẫu và kết quả điện thoại không bị thay bằng model 5% mới.
- Synthetic không được đưa vào nội dung báo cáo.

Nội dung bổ sung: MC-05, MC-07; một phần MC-06/MC-10/MC-11; đồng bộ ND-07–ND-11 và ND-16 trong phạm vi kết quả local. Danh sách còn lại: [remaining-comments-20261110.md](../../remaining-comments-20261110.md).

Kiểm cuối đã hoàn tất: PDF một mặt/hai mặt đều 197 trang, 50 hình/53 bảng, 27/27 trích dẫn có số; bản tin Việt/Anh 1/1 trang, tóm tắt 2/3 trang. Đã kiểm nguồn, metric, float, font, text, ảnh render và `git diff --check`. Kết quả máy đọc và hash PDF ở [validation.json](validation.json), biên bản ở [report/audit](../../../../report/audit/local-experiments-2026-11-10.md). Acronym checker chỉ có coverage partial trên trích đoạn, không chứng nhận toàn văn. Đây là xác minh artifact báo cáo, không phải xác nhận khoa học, nghiệm thu hoặc sẵn sàng triển khai.
