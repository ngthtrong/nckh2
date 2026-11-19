# Bốn sơ đồ đã sửa cho báo cáo — 25/10/2026

**Bản lịch sử, đã được thay thế.** Người dùng yêu cầu khôi phục chi tiết và bổ sung Hình 2.3, 2.19. Bộ đang dùng là [sáu sơ đồ chi tiết](../2026-10-25-six-system-diagrams/README.md); các ảnh/check trong thư mục bốn hình ghi nhận lần sửa trước. CLI `build_system_diagrams.py` hiện chuyển tiếp sang generator chi tiết để tránh ghi đè ngược bộ đang dùng.

Bộ này thay trực tiếp Hình **2.1, 2.2, 2.5 và 2.12** trong báo cáo theo yêu cầu chỉnh sửa ngày 25/10/2026. Khác với thư mục `2026-10-25-flowcharts/` chỉ để xem xét trước đây, bốn hình trong bộ này được đưa vào `report/assets/diagrams/` và biên dịch vào báo cáo.

Mở [00-four-report-figures.drawio](00-four-report-figures.drawio) để chỉnh sửa cả bốn trang trong Draw.io. Mỗi hình cũng có PDF vector, SVG giữ đối tượng chữ và Draw.io riêng trong `report/assets/diagrams/`. Ảnh xem nhanh nằm trong `previews/`.

## Nội dung đã sửa

| Hình | Tệp | Nội dung |
| --- | --- | --- |
| 2.1 | `functional_architecture` | Phân biệt HTTP metadata/ảnh, SMS gateway và API điều phối; nối API với ClusterService; tách lưu trữ bền vững khỏi cache kết quả. |
| 2.2 | `flowchart` | Bốn dải ngang; SOS không yêu cầu ảnh/AI; ảnh trong báo cáo chi tiết là tùy chọn; phân biệt ACK metadata với gửi xong ảnh; phân công và đổi trạng thái là thao tác riêng; hiển thị cả resolved/cancelled. |
| 2.5 | `database_erd` | Chỉ giữ cột chính; UNIQUE áp dụng cho cặp client/sequence; bỏ trường from_value bị lặp; không gọi raw_payload là JSON chuẩn tắc; nét đứt và chú giải phân biệt liên hệ ứng dụng với FK trong DDL; không vẽ FK giả từ dedup tới reports. |
| 2.12 | `flow_05_backend_ingest_dedup` | Phạm vi JSON `/sync/messages`; tách lỗi HTTP request khỏi ACK từng message; có so hash, kiểm tra TTL/định danh, duplicate, rejected, accepted và rollback/retry_later; kết quả batch trả HTTP 200. |

Phần thuyết minh/caption được đồng bộ trong `architecture.tex` và `synchronization.tex`; giữ nguyên label hình để không làm hỏng tham chiếu.

## Tái tạo

Từ gốc repository:

```bash
report/build/visual-env/bin/python report/scripts/build_system_diagrams.py
make -C report content
make -C report check
git diff --check
```

Script dùng matplotlib và font DejaVu Sans. Canvas rộng 160 mm, đúng chiều rộng thân bài; chữ tối thiểu 9 pt khi chèn `width=\textwidth`. Không dùng `bbox_inches='tight'` nên không phát sinh thay đổi tỷ lệ do cắt ảnh. PDF có font nhúng, không biến sơ đồ thành bitmap. Script kiểm tra bounding box của chữ và ghi hash nguồn/hình trong `validation.json`.

Script ghi Draw.io trước PDF, để bước xuất Draw.io thông thường không ghi đè PDF Python vừa sinh. Có thể sửa Draw.io bằng tay và xuất lại theo workflow hiện có; chạy lại script sẽ thay các chỉnh sửa tay bằng bố cục Python. File tổng hợp bốn trang là bản tiện chỉnh sửa, không phải đầu vào LaTeX trực tiếp.

## Bản gốc và bằng chứng

- `originals/`: bản sao sơ đồ/PDF/SVG và hai tệp TeX tại thời điểm bắt đầu.
- `original-manifest.json`: SHA-256 của các tệp gốc; đã đối chiếu lại sau sao lưu.
- `validation.json`: kích thước, cỡ chữ tối thiểu, kiểm tra vùng chữ và hash mã nguồn đã đối chiếu.
- `VALIDATION.md`: kết quả biên dịch, kiểm tra và rà soát PDF hoàn chỉnh.

Đối chiếu tĩnh với `products/be/{main,storage,cluster_service,sms_intake}.py` và các use case/repository Flutter được ghi trong manifest. Không thay đổi sản phẩm, công thức nghiên cứu hay artifact kết quả; không chạy lại ứng dụng, SMS, huấn luyện hoặc benchmark.

FigJam cần người dùng chọn team/organization trong widget của Figma trước khi công cụ có thể tạo file. Các PDF/Draw.io/SVG cục bộ không phụ thuộc bước này.
