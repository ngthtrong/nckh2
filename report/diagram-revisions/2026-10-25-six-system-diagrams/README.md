# Sáu sơ đồ hệ thống chi tiết — 25/10/2026

Bộ đang dùng thay Hình **2.1, 2.2, 2.3, 2.5, 2.12, 2.19** trong báo cáo trên nhánh `trong-edit-pic`. Bản bốn hình trước bị lược thông tin quá nhiều; lần này khôi phục chi tiết và dùng trang A4 ngang để đọc được các trường, lớp, endpoint và nhánh xử lý.

Mở [00-six-detailed-system-diagrams.drawio](00-six-detailed-system-diagrams.drawio) để chỉnh cả sáu trang. Nguồn PDF vector, SVG giữ chữ và Draw.io riêng ở `report/assets/diagrams/`. Icon được vẽ nguyên gốc bằng đường vector; không có ảnh hoặc icon tải ngoài cần giấy phép. Bản đồ là hình minh họa, không trình bày như bản đồ tác nghiệp hay kết quả thực nghiệm.

Xem nhanh [PDF riêng gồm sáu trang hình](six-diagrams-review.pdf), trích nguyên từ báo cáo, giữ caption và số trang in. Kết quả kiểm tra cuối nằm trong [VALIDATION.md](VALIDATION.md).

| Hình | Tệp | Chi tiết đã giữ/khôi phục và cách trình bày |
| --- | --- | --- |
| 2.1 | `functional_architecture` | Người gửi/đội cứu hộ, ảnh/GPS/N/V, MobileNetV3, ONNX/ExecuTorch, LR, Hive/Outbox, ID/hash/sequence, gửi thích ứng, SMS gateway, các tuyến HTTP, FastAPI, ClusterService/rescue_core, Louvain/P(c), L/T review, cache/ETag, SQLite/ảnh, Web GIS, quản trị và xuất dữ liệu. Ba vùng hệ thống có icon điện thoại, camera, vị trí, chip, CSDL, graph, bản đồ, đội cứu hộ và gateway. |
| 2.2 | `flowchart` | Bốn swimlane; tạo SOS/báo cáo, lựa chọn gửi, vòng retry/ACK, metadata khác ảnh, bốn nguồn tiếp nhận, chống trùng đúng kênh, cache snapshot và stale, vị trí/thời gian, đồ thị/Louvain/tổng hợp bằng chứng, polling dashboard, xác minh, giao đội/đổi trạng thái, thực địa, nhật ký và phản hồi. |
| 2.3 | `mobile_architecture` | Presentation, Domain, Data và nền tảng; các màn hình, AppController, cả năm use case cùng deliverRecord, policy/LR, entity, interface, implementation và datasource; Hive/JCS, ONNX/ExecuTorch, GPS/ImagePicker, HTTP/SMS, Workmanager. Mũi tên phân biệt lời gọi và implements; không vẽ domain gọi trực tiếp implementation. |
| 2.5 | `database_erd` | **Đầy đủ 7 bảng, 70 cột**, được phân tích trực tiếp từ DDL bằng AST và SQLite trong bộ nhớ. Có type, PK/NN/UQ, default, NOCASE, khóa duy nhất ghép client/sequence và các liên hệ do mã quản lý. Không đánh dấu FK giả, không lặp from_value, không gọi raw_payload là JCS. |
| 2.12 | `flow_05_backend_ingest_dedup` | Ba tuyến JSON sync, multipart/ảnh và SMS cùng hiện trên hình. Khôi phục giới hạn, TTL/hash/JCS, định danh, hai operation, quyền, commit/rollback, accepted/duplicate/rejected/retry_later và mã lỗi; tuyến ảnh có ownership, format/hash/size/ảnh đầu/merge, tuyến SMS có token, parse/id/hash/trusted/review và 201/200. |
| 2.19 | `flow_08_dispatch_lifecycle` | Xem ca theo report ID, ảnh/AI/N/V, xác minh vị trí và API location, chọn đội hoạt động, PUT team riêng PATCH status, thực địa, vòng theo dõi khi chưa hoàn tất, resolved/cancelled/lý do, kiểm soát version/quyền/trạng thái và audit/active clusters. GPS không bị trình bày như điều kiện chặn API; lỗi mạng không tự hủy ca. |

## Sinh lại và biên dịch

```bash
make -C report system-diagrams
make -C report content
make -C report check
git diff --check
```

`system-diagrams` dùng môi trường `report/build/visual-env/` và các phiên bản trong `report/scripts/requirements-figures.txt`. Generator là `report/scripts/build_detailed_system_diagrams.py`, sử dụng renderer chung trong `build_system_diagrams.py`. CLI cũ chuyển tiếp sang generator chi tiết để không đưa nhầm bản giản lược trở lại.

Canvas rộng 257 mm; báo cáo chèn bằng `width=\linewidth` trong `pdflscape`. Font nội dung tối thiểu 9 pt ở kích thước in. PDF giữ vector và font nhúng. Không dùng ảnh bitmap làm nguồn sơ đồ và không giảm cỡ chữ để nhét vào trang dọc.

Script kiểm tra bounding box, chữ nằm trong ô/canvas và giao nhau giữa các vùng chữ; lưu hash mã nguồn, script và ba định dạng đầu ra. Script ghi Draw.io trước PDF để workflow xuất hình không ghi đè ngược PDF Python mới sinh. Nếu chỉnh Draw.io bằng tay, xuất lại theo workflow hiện có; chạy `system-diagrams` sẽ phục hồi bố cục Python.

## Bằng chứng và phạm vi

- `before/`, `before-manifest.json`: bảo toàn 21 tệp hiện có, bao gồm bốn hình đã sửa lần trước, hai hình bổ sung và nguồn liên quan. Bản gốc trước lần sửa đầu vẫn ở thư mục `2026-10-25-report-four-figures/originals/`.
- `schema-from-ddl.json`: 7 bảng, 70 cột, ràng buộc ghép và kiểm tra không có FK khai báo; chỉ dùng SQLite in-memory, không import/khởi tạo backend hay chạm CSDL sản phẩm.
- `content-coverage.json`: đối chiếu thuật ngữ/thành phần cần giữ với chữ trích xuất từ PDF; đây là kiểm tra không bỏ sót nội dung, không phải chứng minh vận hành đúng.
- `validation.json`: font, kích thước, kiểm tra vùng chữ, hash nguồn/đầu ra.
- `previews/`: hình nguồn để rà bố cục; `pages/`: trang báo cáo đã render để kiểm tra thực tế.
- `VALIDATION.md`: kết quả cuối của build, kiểm tra, vị trí trang và giới hạn còn lại.

Đã cập nhật caption và thuyết minh tương ứng. Phát hiện liên quan được sửa ở phần mô tả: app gửi `E_i` nhưng adapter chưa sử dụng trực tiếp; giao đội không tự chuyển status. Nhãn chuyển `processing → dispatched` trong Hình 2.18 được sửa từ `assign_team` thành `PATCH status` để nhất quán với Hình 2.19; bố cục Hình 2.18 giữ nguyên.

Không thay mã sản phẩm, dữ liệu/tham số nghiên cứu, kết quả benchmark hoặc quyết định nghiên cứu. Không chạy app/SMS/huấn luyện để suy diễn thêm bằng chứng. Không commit/push hoặc thay commit của `main` trong công việc này.
