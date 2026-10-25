# Flowchart bản sao đã rà soát — 25/10/2026

Mở **`00-flowcharts-reviewed.drawio`** để xem toàn bộ 12 sơ đồ, gồm 22 trang. Các tab bên dưới tên cửa sổ giúp chuyển giữa các sơ đồ và các phần chi tiết.

- `edited/`: 12 file Draw.io đã sửa, giữ tên tương ứng với file nguồn.
- `previews/`: ảnh PNG được xuất bằng Draw.io Desktop cho từng trang.
- `originals/`: bản sao nguyên trạng của 12 file Draw.io và PDF nguồn tại lúc bắt đầu.
- `checks/source-manifest.json`: SHA-256 của toàn bộ file trong thư mục sơ đồ nguồn lúc bắt đầu.
- `checks/page-index.json`: danh mục trang trong từng file.
- `checks/`: dữ liệu kiểm tra và công cụ tái tạo các bản sao; không phải đầu vào biên dịch báo cáo.

**Các bản đang dùng trong `report/assets/diagrams/` không được ghi đè.** Các lệnh chèn hình trong báo cáo, use case và PDF báo cáo cũng không được thay bằng bộ này. Chưa commit hoặc push các bản sao.

## Nội dung sửa

| File | Thay đổi chính |
| --- | --- |
| `flowchart.drawio` | Tổng quan bốn làn; tách quy trình con khỏi luồng tổng thể; giữ rõ hoạt động ngoài thực địa; theo dõi tới khi ca kết thúc; không coi gửi SMS là ACK HTTP. |
| `flow_01_sos_one_touch.drawio` | Lưu SOS trước khi lấy GPS; không đo `/probe` cho SOS không ảnh; giữ vị trí trống khi không lấy được; xử lý SOS lặp trong 30 giây; bỏ gán urgency cố định. |
| `flow_02_create_report_edge_ai.drawio` | Ảnh và AI là tùy chọn; thiếu ảnh/AI không gán non_flood; kiểm tra khả năng lưu ảnh; tính điểm khẩn cấp khi mô hình sẵn sàng. |
| `flow_03_adaptive_network_send.drawio` | Ba trang: gửi metadata, hoàn tất ảnh, chính sách mạng. ACK metadata khác đồng bộ xong ảnh; tách lỗi tạm thời và từ chối; SMS chỉ được thử khi đủ điều kiện. |
| `flow_04_track_rescue_status.drawio` | Chỉ mô tả dữ liệu app hiện nhận; bỏ tên/vị trí/liên hệ đội và lý do đóng chưa được API trả; giữ cập nhật tiến; nêu lịch 15/60 giây và điều kiện hoạt động. |
| `flow_05_backend_ingest_dedup.drawio` | Ba trang riêng cho batch, multipart và SMS Gateway; đúng cách chống trùng theo kênh; phân biệt lỗi HTTP request và kết quả từng message. |
| `flow_06_clustering_priority.drawio` | Hai trang cho cache/API và tính cụm; kiểm tra vị trí lẫn thời gian; có yếu tố thời gian trong đồ thị; đúng công thức ưu tiên có hệ số nhóm yếu thế; ETag thuộc snapshot. |
| `flow_07_manual_intake_location.drawio` | Tách cuộc gọi/nhập tay khỏi SMS tự động; tọa độ tùy chọn; đúng nguồn hotline và nhật ký người thao tác; cập nhật cụm qua bộ nhớ đệm. |
| `flow_08_dispatch_lifecycle.drawio` | Giao đội và đổi trạng thái là hai thao tác; bổ sung vị trí không được trình bày như điều kiện bắt buộc của API; thực địa nằm ngoài phần mềm; giữ ca chưa kết thúc và lý do đóng. |
| `flow_09_ai_training_optimization.drawio` | Hai trang huấn luyện và tối ưu; dùng ReduceLROnPlateau; có vòng lặp epoch/validation; chọn checkpoint trước đánh giá test; không trộn seed/metric; các nhánh tối ưu được so sánh riêng. |
| `flowchart_adaptive_mobile.drawio` | Bản phụ đồng bộ với ba trang đã sửa của flow_03. |
| `flowchart_backend_dedup.drawio` | Bản phụ đồng bộ với ba trang đã sửa của flow_05. |

## Cách đọc

- Hình thoi: câu hỏi/điều kiện; đường ra có nhãn.
- Chữ nhật có hai vạch đứng: quy trình con, được giải thích ở trang hoặc flowchart chi tiết.
- Khung xám nét đứt: hoạt động ngoài phần mềm.
- Đường liền có mũi tên: luồng xử lý hoặc trao đổi dữ liệu được ghi rõ trên đường nối.
- Đường đứt ở sơ đồ tổng thể: thông báo thay đổi dữ liệu, cập nhật nền hoặc nhánh kết quả riêng; không tự có nghĩa là `include`/`extend`.
- Ghi chú cuối trang chứa tham số/căn cứ kỹ thuật để nội dung trong ô ngắn hơn.

## Phạm vi xác minh

Đối chiếu tĩnh với `products/fe/app/lib/`, `products/be/`, notebook `products/fe/model/training_img.ipynb`, config mô hình và số liệu chia tập đã lưu. Đã kiểm tra cấu trúc XML, nguồn/đích đường nối và xuất ảnh bằng Draw.io để rà bố cục. Không chạy lại app, SMS, huấn luyện hoặc benchmark.

Đây là các bản chỉnh sửa để xem xét. Chưa tự động đưa vào báo cáo hoặc xác nhận kết quả vận hành mới.
