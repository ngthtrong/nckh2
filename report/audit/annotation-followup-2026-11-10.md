# Biên tập theo 13 annotations — 10/11/2026

Nguồn yêu cầu: 13 annotations của người dùng sau lần đối chiếu `tmp.md` với PDF 170 trang. Phạm vi là biên tập báo cáo, sửa ký hiệu/trình bày tài liệu tham khảo và cập nhật trạng thái; không chạy lại thực nghiệm nghiên cứu hoặc thay mô hình/dữ liệu.

## Nội dung đã chỉnh

- Rút các đoạn ở Mở đầu, khái niệm, kiến trúc, đồng bộ, yêu cầu phi chức năng, mô hình ảnh, lời dẫn kết quả và liên hệ hai pilot. Bỏ danh mục TN nội bộ khỏi lời dẫn, thay các giải thích lặp bằng tham chiếu. Sửa câu về LR để khớp đường adapter đã mô tả.
- Dùng **K** cho số láng giềng/top-K, **k** cho chỉ số cụm trong P_k. Đồng bộ định nghĩa, bảng tham số, giới hạn số cạnh nK và các đoạn nhắc lại; công thức tính điểm giữ nguyên.
- Bỏ ngày truy cập lặp ở model card DistilBERT; giữ liền phần giao thức `https://` khi ngắt URL trong danh mục IEEE.
- Đối chiếu thuyết minh DOCX và bản Markdown: DOCX yêu cầu đánh giá định lượng chất lượng, thời gian xử lý và đồng bộ; bản Markdown nêu Accuracy/F1. Không tìm thấy ngưỡng đạt định lượng trong các mục tiêu, phương pháp và yêu cầu sản phẩm đã đọc. Giữ các thước đo cùng đường dẫn đến định nghĩa/kết quả, không đặt ngưỡng hồi cứu.
- Cô đọng cuối Mở đầu và phần Giới hạn để bỏ hai trang chỉ còn vài dòng, giữ nguyên cỡ chữ, lề và kích thước sơ đồ.

## Xử lý từng annotation

| Annotation | Xử lý |
|---|---|
| 1 | Giữ chỗ ngày ký/nhận xét/chữ ký để hoàn thiện trên bản giấy sau in; trạng thái DEFERRED_TO_PRINTED_COPY. |
| 2 | Ưu tiên rút văn phong và đối chiếu tính chính xác; bảo toàn hình, bảng số liệu, phương trình và kết luận có giới hạn. |
| 3 | MC-01: SKIPPED_BY_USER; không bổ sung hồ sơ nguồn ảnh. |
| 4 | MC-02: SKIPPED_THIS_SESSION_BY_USER; không gán nhãn hoặc tính đồng thuận mới. |
| 5 | MC-09–10: bản dịch/nhãn AI được chấp nhận cho phạm vi dữ liệu hiện tại; không yêu cầu corpus mới. Nguồn gốc CrisisMMD dẫn xuất và giới hạn kết quả giữ nguyên. |
| 6 | MC-13–14: không bổ sung đánh giá phân cụm/xếp hạng trên dữ liệu thật trong phiên này; giữ cài đặt/kiểm hồi quy exact đã có. |
| 7 | MC-15: không tái lập thêm RQ2; giữ công khai ba raw p Spearman và năm Holm chưa khớp. |
| 8 | MC-17–18: không thử mạng di động/SMS thật trong phiên này; không tạo số đo hoặc log thiết bị. |
| 9 | MC-19: WAITING_FOR_PUBLICATION_INFORMATION; bổ sung khi người dùng có thông tin. |
| 10 | Thống nhất K/k như trên, kể cả bảng tham số và các đoạn mô tả kiểm hồi quy. |
| 11 | Đã tìm căn cứ thước đo trong thuyết minh và báo cáo; không tìm thấy ngưỡng đạt đã đăng ký nên bỏ qua việc đặt ngưỡng trong phiên này. |
| 12 | Đã sửa metadata ngày truy cập và điểm ngắt URL; kiểm bằng văn bản và ảnh PDF. |
| 13 | Giữ đối chứng/ablation fusion đã có; hoãn đánh giá bổ sung do chưa có dữ liệu ghép cặp/nhãn độc lập sẵn cho phép xác nhận mới. Không coi đó là điều kiện bổ sung dữ liệu cho phiên biên tập này. |

## Kết quả và kiểm tra

Hai bản in đều **165 trang**, thân bài **102 trang**, giảm từ **170/107 trang**. Giữ **50 hình, 52 bảng, 29 trích dẫn**, cùng 32 cấu hình/224 bản ghi benchmark điện thoại. Bản tin Việt/Anh vẫn một trang mỗi bản; tóm tắt Việt/Anh vẫn hai trang mỗi bản. Nội dung tóm tắt không được viết lại.

Các lệnh build/check một/hai mặt và kiểm tham chiếu hình/bảng đều đạt. Sáu PDF nhúng đủ font; log cuối không có tràn khung, nhãn lặp, thiếu ký tự hoặc tham chiếu/trích dẫn chưa giải quyết. Chỗ nhận xét người hướng dẫn còn trống theo annotation 1, không dùng kiểm hồ sơ phát hành để yêu cầu điền vào PDF.

Đã xem năm trang tổng quan phủ toàn bộ 165 trang và các trang trọng điểm ở độ phân giải cao, kiểm lại cuối Mở đầu/Giới hạn và tài liệu tham khảo. Raster một/hai mặt ở kích thước tối đa 330 px trùng nhau trên toàn bộ 165 trang; kết quả này chỉ đối chiếu bố cục ở độ phân giải đó. Bộ kiểm chữ viết tắt có coverage `partial` trên văn bản tiếng Việt trích từ PDF, chỉ dùng như chẩn đoán tham khảo.

Đối chiếu nguồn xác nhận các khối equation/align/figure, caption/label và đường dẫn hình được giữ nguyên; bảng chỉ đổi ký hiệu số láng giềng. Toàn bộ bảng/giá trị sinh và hình định lượng khớp hash trước sửa. `provenance.json` chỉ cập nhật `source_commit` do exporter. `tmp.md`, biểu mẫu đầu quyển, cấu hình chữ/lề và asset mô hình không được sửa. `git diff --check` đạt; không commit/push.

Hash PDF, nguồn thay đổi, căn cứ thước đo và kết quả kiểm được lưu trong [receipt](annotation-followup-2026-11-10.json). Trạng thái hiện hành ở [bảng theo dõi](../../docs/revision-plan/remaining-comments-20261110.md).
