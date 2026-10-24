# Hồ sơ đính kèm

`manifest.yaml` dùng cú pháp JSON (hợp lệ trong YAML 1.2), đọc bằng thư viện chuẩn Python, không cần PyYAML.

Thay mục mẫu bằng các sản phẩm thực sự đăng ký ở nhóm I–III trong thuyết minh đã duyệt. Mỗi mục cần `title`, `group`, `commitment`, `path`, `verified`. Đường dẫn tính từ `report/`, chỉ chấp nhận PDF bên trong `evidence/`. `commitments_confirmed` xác nhận danh sách đã được đối chiếu đủ với bản ký/dấu; `verified` xác nhận con người đã kiểm tra tính phù hợp của từng minh chứng. Các cờ này không thay thế việc xem chữ ký/dấu.

`approved_proposal` chỉ được trỏ tới bản scan/copy phê duyệt chính thức. Không tạo hồ sơ hoặc chữ ký giả để vượt kiểm tra. Chưa cung cấp PDF nào trong khung ban đầu.

Trang PDF đính kèm giữ khổ giấy gốc với `fitpaper=true`, không thêm chân trang lên scan. Chỉ phần trước hồ sơ có số trang của báo cáo; scan giữ số trang gốc. Mục lục/bookmark trỏ tới trang đầu mỗi tệp. Cần xem thủ công chiều trang, chữ ký/dấu và khả năng đọc sau khi ghép.

## Danh sách sơ bộ theo thuyết minh trong repo

Manifest ghi ba cam kết nhóm III ở mục 16 của thuyết minh DOCX: ứng dụng di động (3.1), website quản lý (3.2) và bộ mô hình AI đa phương thức đã tối ưu (3.3). Nhóm I/II không đăng ký nên không tạo mục lấp chỗ.

Ba PDF `products/mobile-app.pdf`, `products/dashboard.pdf` và `products/ai-models.pdf` được biên soạn từ các nguồn TeX cùng tên. Hai PDF đầu dùng ảnh giao diện đã có trong báo cáo; PDF mô hình liệt kê bốn tệp ONNX/PTE trong `products/fe/model/Edge Ai/seed1024/export/{baseline,pruning_st}/`, với kích thước và SHA-256 đối chiếu manifest. Phần mô hình chỉ minh chứng nhận diện ảnh, không xác nhận đã hoàn thành mô hình phân tích tin nhắn tiếng Việt.

Bản `content` ghép ba PDF này sau phụ lục và trước sản phẩm nhóm IV. Bản `full` dùng danh sách minh chứng đã xác nhận, bao gồm thuyết minh phê duyệt trước các sản phẩm. Các cờ xác nhận vẫn giữ `false` cho đến khi hồ sơ được kiểm tra; không dùng ảnh giao diện để xác nhận nghiệm thu hoặc chữ ký/dấu. `approved-proposal.pdf` vẫn cần bản có ký và đóng dấu.

Khi sửa nguồn minh chứng, biên dịch từ thư mục `report/` trước khi build báo cáo:

```powershell
rtk proxy ./tectonic.exe -Z search-path=. -o evidence/products evidence/products/mobile-app.tex
rtk proxy ./tectonic.exe -Z search-path=. -o evidence/products evidence/products/dashboard.tex
rtk proxy ./tectonic.exe -Z search-path=. -o evidence/products evidence/products/ai-models.tex
```
