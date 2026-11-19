# Bố cục báo cáo ngày 22/10/2026

## Đã thực hiện theo xác nhận của người dùng

- Chương 2: Thiết kế và xây dựng hệ thống; chương 3: Dữ liệu và phương pháp nghiên cứu. `report/main.tex` quyết định thứ tự; giữ đường dẫn nguồn và khóa nhãn hiện có.
- Ba mục vai trò/Use Case, yêu cầu phi chức năng và xử lý dữ liệu không hoàn chỉnh đã chuyển từ chương 1 sang chương hệ thống. Đổi mục vai trò/Use Case thành Yêu cầu chức năng; xóa mục Đóng góp được kiểm tra ở từng tầng theo yêu cầu riêng.
- Chuyển nguyên văn phần kết quả/kịch bản/ma trận kiểm thử từ `report/chapters/03-system/sections/implementation.tex` sang `report/chapters/04-evaluation/sections/system-tests.tex`, mục 4.3. Phần triển khai ở chương 2 dẫn đến mục này.
- Bổ sung câu dẫn giữa các chương, thay dẫn chiếu viết cứng Chương 2 bằng `\ref`, đồng bộ bố cục trong README và tài liệu hướng dẫn báo cáo.

## Bằng chứng biên soạn

- Tectonic/BibTeX biên dịch thành công bản xem lại `report/build/template-review/content/content.pdf`: 111 trang, 82 trang thân bài.
- Chương 2 bắt đầu ở trang PDF 36, chương 3 ở trang 59, chương 4 ở trang 77. Kiểm thử hệ thống ở trang 95; các bảng đã thành 4.14 và 4.15.
- Đối chiếu văn bản kiểm thử đã chuyển với bản nguồn Git: không đổi nội dung. Log không có overfull, nhãn lặp hoặc dẫn chiếu chưa giải quyết; đã xem ảnh render mục lục, đầu chương và hai trang kiểm thử.
- Còn cảnh báo môi trường đọc font Windows và phiên bản PDF hình nhúng như các lần biên dịch trước.

## Giới hạn và việc tiếp theo

- Các thay đổi chưa commit; có thêm các tệp phần mục của chương hệ thống và `system-tests.tex`. Không stage/commit tự động.
- Chưa sửa các đoạn mô tả triển khai lẫn trong cơ sở lý thuyết; người dùng đã yêu cầu để sau. Chưa chỉnh cỡ chữ sơ đồ hoặc xử lý các phát hiện nội dung cũ trong bản rà soát.
- Không chạy lại huấn luyện, benchmark hay các bộ kiểm thử phần mềm. Các số kiểm thử trong báo cáo vẫn là kết quả đã lưu, không phải phép chạy mới trong đợt đổi bố cục.
