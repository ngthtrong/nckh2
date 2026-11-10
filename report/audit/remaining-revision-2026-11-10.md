# Chỉnh sửa nhận xét còn lại — 10/11/2026

## Kết quả biên tập

Thân bài giảm từ 138 xuống 115 trang (giảm 23 trang); toàn quyển một/hai mặt đều 201 trang. Chi tiết CSDL/API, thao tác, giao diện và bốn lưu đồ được chuyển sang phụ lục, giữ đủ hình và nhãn. Kết luận được viết lại còn hai trang. Số trang toàn quyển tăng so với mốc 197 trang vì giữ nội dung chi tiết trong phụ lục và bổ sung tài liệu/minh chứng; đây là rút phần trình bày chính, không xóa dữ liệu.

Đã thêm AlleyFloodNet và EmergencyNet theo nguồn gốc, bảng chỉ tiêu đánh giá, đối chiếu đóng góp tích hợp với kết quả thuật toán, thống nhất top-k/số Việt–Anh/font URL. Bộ kiểm đối chiếu 50 hình, 55 bảng và 29/29 trích dẫn có số ở cả hai bản.

Ảnh được mô tả đúng theo xác nhận mới: nhóm tự chụp và thu thập web. Báo cáo ghi nhận NLP/fusion mobile đã được nhóm khác cập nhật; metric offline không gán cho APK chưa có trong hồ sơ. Bảng B.6 và các phần Việt–Anh dùng cùng phạm vi. Chẩn đoán PTQ/QAT bổ sung, đo lặp hiệu năng/pin/RAM nằm ngoài đợt này; điều phối xét chi phí và thí điểm chỉ ở hướng phát triển.

Ba trang minh chứng sản phẩm và trang đầu bản tác giả bài báo dùng số trang in 169–172 của quyển. Đã xem ảnh render để xác nhận số “1” của PDF sản phẩm cũ bị che và nội dung/chú thích còn nguyên. Văn bản trích xuất có thể vẫn chứa ký tự chân trang cũ nằm dưới lớp phủ; bản PDF gốc không bị sửa. Trang đầu bản tác giả không thay xác nhận công bố hoặc metadata chapter.

## Khắc phục và kiểm thử phần mềm

- Sáu ca gửi/SOS/đồng bộ sau dispose và probe mạng lỗi không đạt trước sửa, đều đạt sau sửa. Guard vòng đời giữ bản ghi đã lưu và không gọi giao diện đã đóng; probe lỗi đi theo fallback.
- Flutter: 284 đạt, 3 bỏ qua; phân tích tĩnh bốn tệp Dart thay đổi không phát hiện vấn đề.
- Backend: 78 phép kiểm thuộc các suite API/contract/cluster liên quan đạt. Có ba phép hồi quy khử bản sao exact trước quantile/top-k, gồm multiplicity 2/5, nội dung khác và hàng xem xét.
- Hai ca tích hợp app Linux–backend HTTP thật đạt với DB/uploads tạm riêng. Không có Android kết nối, không đo SMS/mạng di động thật. Không gán kết quả này thành raw Case 8 Android lịch sử hoặc khẳng định cùng nguyên nhân sự cố.

Hash nguồn và log được exporter xác minh từ [software-evidence.json](../../docs/revision-plan/outputs/remaining-revision-20261110/software-evidence.json). Không đổi lõi hoặc kết quả RQ1–RQ3; chưa có đánh giá sai gộp/sai tách đồ thị trên báo cáo thực.

## Kiểm tra báo cáo

| Kiểm tra | Kết quả |
|---|---|
| Build nội dung một/hai mặt | Đạt; 201/201 trang, thân bài 115/115 trang |
| Check báo cáo và đối chiếu float hai bản | Đạt; 50 hình, 55 bảng, 29/29 trích dẫn |
| Font và cảnh báo | Tất cả font được kiểm đều nhúng; không có overfull, nhãn lặp hoặc tham chiếu/trích dẫn chưa giải quyết |
| Bản tin Việt/Anh | 1/1 trang |
| Tóm tắt Việt/Anh | 2/3 trang |
| Ảnh render | Đã xem phần tổng quan, chỉ tiêu, tích hợp mobile, kiểm phần mềm, kết luận, tài liệu tham khảo, B.6, phụ lục, minh chứng và các phần tương ứng ở bản hai mặt/biểu mẫu |
| Kiểm acronym | Advisory trên trích đoạn, coverage partial; có tên viết tắt và cảnh báo do tiêu đề tiếng Việt. Không xem là kiểm toàn văn hoặc chứng nhận sạch |
| Dữ liệu/nhận xét gốc | tmp.md và 47 tệp nguồn notebook đã sao chụp được kiểm hash riêng; không sửa dữ liệu/checkpoint gốc |
| Whitespace/cú pháp/đường dẫn | Kết quả và hash cuối ở validation.json |

[Hồ sơ kiểm tra](../../docs/revision-plan/outputs/remaining-revision-20261110/README.md) lưu log, inventory PDF và receipt máy đọc. Không chạy check-release, không tự tạo nhận xét/chữ ký GVHD hoặc điền ngày ký. Phần hành chính và các bằng chứng còn thiếu được liệt kê theo từng mã tại [bảng đối chiếu hiện hành](../../docs/revision-plan/remaining-comments-20261110.md).
