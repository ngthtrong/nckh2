# Cập nhật báo cáo từ thực nghiệm local — 10/11/2026

## Nội dung đã thay đổi

- Thêm Mục 4.2.7 và ba bảng 4.12–4.14: grid pruning 5/10/20%, McNemar/CI, suy luận CPU mới và chẩn đoán tensor PTQ/QAT.
- Giữ nguyên model pruning 1% lịch sử, kết quả điện thoại và RQ1–RQ3. Thử mức nén cao hơn không được diễn giải thành cải thiện đã đạt.
- T2 chuyển sang số liệu tái chạy CUDA: macro-F1 trung bình 52,29%, recall request 22,22%. Nêu rõ lần trước 50,73% trên cùng dữ liệu; các kết quả frozen không đổi.
- Đồng bộ thiết kế đánh giá, Bảng B.6, Kết luận, thông tin kết quả, bản tin và tóm tắt Việt–Anh. Bổ sung giải thích CUDA/GPU/MAE trong danh mục từ viết tắt.
- Lưu hồ sơ nguồn và danh sách nhận xét còn lại; không sửa `tmp.md`, app, dữ liệu hoặc checkpoint gốc, không chạy thêm training/inference và không đưa synthetic vào báo cáo.

## Xác minh

| Hạng mục | Kết quả |
|---|---|
| Hash minh chứng sao chụp và nguồn gốc | 47/47 tệp khớp, nguồn gốc giữ nguyên |
| Tính lại metric | 23 cấu hình/seed khớp từ prediction; McNemar/Holm và ID ảnh được kiểm lại |
| CI bootstrap | Dùng artifact đã lưu, không phát lại trong bước biên tập |
| Checkpoint T2 seed 43 | Hai entry trong ZIP khớp SHA-256/CRC; hai file giải nén lệch hash được giữ nguyên và ghi riêng |
| Build một mặt/hai mặt | Thành công; cùng 197 trang, thân bài 138 trang |
| Kiểm báo cáo, float và trích dẫn | Đạt cả hai bản; 50 hình, 53 bảng; 27/27 trích dẫn có số |
| Font PDF | Mọi hàng font được kiểm đều embedded; không có cảnh báo font thiếu hoặc tràn hộp |
| Bản tin/tóm tắt | Bản tin Việt/Anh 1/1 trang; tóm tắt Việt/Anh 2/3 trang |
| Kiểm ảnh render | Đã xem bảng mới ở hai bản in, T2, Bảng B.6, phần truy vết, bản tin/tóm tắt và các trang kết luận thay đổi |
| `git diff --check` | Đạt |
| Acronym checker | Advisory, phạm vi trích đoạn, coverage partial; các cảnh báo còn lại chủ yếu là tên sản phẩm, đuôi tệp và thuật ngữ đã có. Không dùng kết quả này làm chứng nhận toàn văn |

`check-release` không được chạy; vẫn còn trường mẫu hành chính và các bằng chứng nghiên cứu/vận hành liệt kê riêng. Build/check không xác nhận đủ điều kiện nghiệm thu hoặc vận hành cứu hộ.

Hồ sơ máy đọc: [validation.json](../../docs/revision-plan/outputs/local-report-update-20261110/validation.json).

Danh sách đầy đủ theo mã BC/ND/MC: [remaining-comments-20261110.md](../../docs/revision-plan/remaining-comments-20261110.md).
