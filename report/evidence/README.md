# Hồ sơ đính kèm

`manifest.yaml` dùng cú pháp JSON (hợp lệ trong YAML 1.2), đọc bằng thư viện chuẩn Python, không cần PyYAML.

Thay mục mẫu bằng các sản phẩm thực sự đăng ký ở nhóm I–III trong thuyết minh đã duyệt. Mỗi mục cần `title`, `group`, `commitment`, `path`, `verified`. Đường dẫn tính từ `report/`, chỉ chấp nhận PDF bên trong `evidence/`. `commitments_confirmed` xác nhận danh sách đã được đối chiếu đủ với bản ký/dấu; `verified` xác nhận con người đã kiểm tra tính phù hợp của từng minh chứng. Các cờ này không thay thế việc xem chữ ký/dấu.

`approved_proposal` chỉ được trỏ tới bản scan/copy phê duyệt chính thức. Không tạo hồ sơ hoặc chữ ký giả để vượt kiểm tra. Chưa cung cấp PDF nào trong khung ban đầu.

Trang PDF đính kèm giữ khổ giấy gốc với `fitpaper=true`, không thêm chân trang lên scan. Chỉ phần trước hồ sơ có số trang của báo cáo; scan giữ số trang gốc. Mục lục/bookmark trỏ tới trang đầu mỗi tệp. Cần xem thủ công chiều trang, chữ ký/dấu và khả năng đọc sau khi ghép.
