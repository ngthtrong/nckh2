# Hồ sơ đính kèm

`manifest.yaml` dùng cú pháp JSON (hợp lệ trong YAML 1.2), đọc bằng thư viện chuẩn Python, không cần PyYAML.

Thay mục mẫu bằng các sản phẩm thực sự đăng ký ở nhóm I–III trong thuyết minh đã duyệt. Mỗi mục cần `title`, `group`, `commitment`, `path`, `verified`. Đường dẫn tính từ `report/`, chỉ chấp nhận PDF bên trong `evidence/`. `commitments_confirmed` xác nhận danh sách đã được đối chiếu đủ với bản ký/dấu; `verified` xác nhận con người đã kiểm tra tính phù hợp của từng minh chứng. Các cờ này không thay thế việc xem chữ ký/dấu.

`approved_proposal` chỉ được trỏ tới bản scan/copy phê duyệt chính thức. Không tạo hồ sơ hoặc chữ ký giả để vượt kiểm tra. Chưa cung cấp PDF nào trong khung ban đầu.

Trang PDF đính kèm giữ khổ giấy gốc với `fitpaper=true`, không thêm chân trang lên scan. Chỉ phần trước hồ sơ có số trang của báo cáo; scan giữ số trang gốc. Mục lục/bookmark trỏ tới trang đầu mỗi tệp. Cần xem thủ công chiều trang, chữ ký/dấu và khả năng đọc sau khi ghép.

## Danh sách sơ bộ theo thuyết minh trong repo

Manifest đã ghi ba cam kết nhóm III ở mục 17: ứng dụng di động (3.1), website quản lý (3.2) và bộ mô hình AI đa phương thức đã tối ưu (3.3). Nhóm I/II ghi không đăng ký nên không tạo mục lấp chỗ; bản thảo ISDS 2026 được mô tả là sản phẩm bổ sung trong nội dung.

Các đường dẫn `products/mobile-app.pdf`, `products/dashboard.pdf`, `products/ai-models.pdf` và `approved-proposal.pdf` **chỉ là vị trí dành cho minh chứng sẽ cung cấp**, chưa có tệp. Danh sách hiện tham chiếu bản thuyết minh Markdown, chưa đối chiếu bản ký/dấu; vì vậy mọi cờ xác nhận giữ `false`. Chỉ đổi cờ và ghép khi có hồ sơ thật đã được kiểm tra.
