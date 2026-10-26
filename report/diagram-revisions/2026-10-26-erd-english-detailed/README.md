# ERD 2.5 — detailed English domain model

Theo yêu cầu bổ sung ngày 26/10/2026, chỉ vẽ lại hình 2.5 và cập nhật đoạn giải thích/chú thích trực tiếp của hình. Sơ đồ đen trắng, toàn bộ chữ trong hình bằng tiếng Anh; nguồn sửa được gồm PDF, SVG và Draw.io tại `report/assets/diagrams/database_erd.*`. Factory tái tạo là `erd()` trong [build_requested_figure_revisions.py](../../scripts/build_requested_figure_revisions.py).

Sơ đồ có **5 thực thể miền nghiệp vụ và 3 đối tượng giá trị**, tổng cộng 8 khối, 7 quan hệ:

| Group | Role |
|---|---|
| Reporting Client | Installation identity and optional report ownership |
| Rescue Report | Identifier, timestamps, contact, state/version and delivery mode |
| Rescue Team | Team identity, contact, member count and active state |
| Operator | Unique account names, role and account state |
| Report Event | Event identity, time, before/after values, actor and source |
| Report Location | Coordinates, accuracy and location source; optional value object |
| Situation Assessment | Victim counts, vulnerability, severe signs and optional LR/AI evidence |
| Stored Photo | Retained attachment, storage information and integrity metadata; optional value object |

Crow's Foot mô tả các quan hệ bắt buộc/tùy chọn và số lượng tham gia. Mỗi báo cáo có tối đa một đội hiện tại và một ảnh được backend giữ lại; báo cáo mới tạo có sự kiện tiếp nhận. Liên kết Operator–Event ở mức khái niệm vì hiện thực lưu actor dưới dạng nhãn. Reporting Client không phải tài khoản đăng nhập của người dân. Location, Assessment và Photo là các nhóm thuộc tính nhúng trong thiết kế; sơ đồ không đề xuất thêm bảng SQLite.

Đối chiếu thuộc tính và quy tắc với `products/fe/app/lib/domain/entities/rescue_record.dart`, `products/be/storage.py` và `products/be/accounts.py`. Cấu hình, logic ứng dụng, dữ liệu và các hình khác được giữ nguyên.

Canvas vector 960 × 590 pt được chèn vào bề ngang 257 mm của trang A4 ngang; chữ nhỏ nhất khi in khoảng **9,1 pt**. [validation-diagram.json](validation-diagram.json) ghi kiểm tra tràn ô, chồng chữ, đường cắt/chồng nhau, nhãn tiếng Anh và ba kênh RGB bằng nhau. `before/` lưu bản trước sửa; `pdf-page.png` là trang PDF sau biên dịch. Kết quả kiểm tra cuối và đối chiếu phạm vi nằm trong `validation-final.json`.
