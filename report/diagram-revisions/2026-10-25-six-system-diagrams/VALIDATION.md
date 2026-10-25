# Kiểm tra sáu sơ đồ chi tiết — 25/10/2026

## Kết quả

- `make -C report system-diagrams`: **PASS** cho cả sáu hình. PDF/SVG giữ vector, nguồn Draw.io có thể chỉnh sửa.
- Kiểm tra chữ trong khung, chữ trong canvas và giao nhau giữa các vùng chữ: **PASS**. Font nội dung tối thiểu **9 pt** ở kích thước in, xác nhận lại bằng `pdftohtml -xml -zoom 1` trên cả sáu hình và sáu trang báo cáo. Font được nhúng.
- Kiểm tra không bỏ sót thành phần qua trích xuất chữ PDF: **PASS**, xem `content-coverage.json`. ERD bao gồm **7 bảng, 70 cột** của DDL hiện tại; số cột từng bảng: reports 26, messages_dedup 11, report_events 10, operators 9, sessions 5, teams 7, server_meta 2.
- XML Draw.io: **PASS**, sáu trang có ID không trùng trong từng trang và source/target của các cạnh đều tồn tại.
- Hash source, script, output và 21 tệp được giữ trong `before/`: **PASS**.
- `make -C report content`: **PASS**, quyển **155 trang A4**. Sáu trang sơ đồ có PDF rotation 90°, tương ứng A4 ngang; nội dung/caption nằm trong vùng in.
- Log cuối `report/build/content/content.log` không có overfull hbox/vbox, float too large, undefined references/citations, duplicate labels hoặc missing characters.
- `git diff --check`: **PASS**.
- `report/main.pdf` và `report/build/content/content.pdf`: giống từng byte.
- Nhánh làm việc: **trong-edit-pic**. Commit `main` giữ nguyên **d6048206f35daef91962c6123821de1e8467e61c**. Chưa commit/push.

## Đã xem trực tiếp trong báo cáo

| Hình | Trang PDF, tính từ 1 | Trang in | Ảnh kiểm tra |
| --- | ---: | ---: | --- |
| 2.1 | 32 | 12 | [figure-2.1.png](pages/figure-2.1.png) |
| 2.2 | 34 | 14 | [figure-2.2.png](pages/figure-2.2.png) |
| 2.3 | 36 | 16 | [figure-2.3.png](pages/figure-2.3.png) |
| 2.5 | 39 | 19 | [figure-2.5.png](pages/figure-2.5.png) |
| 2.12 | 48 | 28 | [figure-2.12.png](pages/figure-2.12.png) |
| 2.19 | 57 | 37 | [figure-2.19.png](pages/figure-2.19.png) |

Đã xem cả sáu ảnh sau biên dịch. Lần rà đầu phát hiện chú giải chật/chồng ở ERD, hình phân lớp và tiếp nhận; đã sửa khoảng cách và kiểm tra lại. Không thấy chữ chạm biên hình thoi, chữ bị cắt hoặc đường nối xuyên qua chữ trong hộp. Các đường nối giữa lane đi qua vùng trống; nét đứt có chú giải. Icon bản đồ ghi rõ là minh họa.

[six-diagrams-review.pdf](six-diagrams-review.pdf) gồm sáu trang trích từ báo cáo bằng `mutool merge`, giữ nguyên nội dung/caption/số trang. Trích chữ sạch, đủ sáu caption; ảnh render trang đầu giống từng pixel với trang báo cáo tương ứng. Bản xem nhanh không mang cây bookmark và tham chiếu sang các trang khác của quyển đầy đủ.

## Kiểm tra toàn báo cáo còn chưa đạt

`make -C report check`: **FAIL với bốn hash nguồn biểu đồ kết quả đã cũ từ trước**:

- `products/fe/reports/seed1024/pth_onnx_pte/summary.json`
- `products/fe/reports/seed1024/pth_onnx_pte/all_predictions.csv`
- `products/fe/reports/seed1024/fp32_ptq_qat/summary.json`
- `products/fe/reports/seed1024/prunning_st/summary.json`

Đã kiểm tra rằng cả bốn source và hash lưu trong figure-provenance đều không đổi so với Git HEAD; xem `preexisting-figure-provenance.json`. Không thay hash để bỏ qua kiểm tra và không tái tạo biểu đồ kết quả ngoài phạm vi sáu sơ đồ. Một dòng placeholder trong thông tin kết quả vẫn được báo ở chế độ draft; không chạy check-release hoặc khẳng định đủ điều kiện nộp.

Workflow đã dựng lại bốn bản tin/tóm tắt riêng; trích xuất chữ không đổi so với bản trước nên giữ lại byte PDF ban đầu, tránh diff ngoài phạm vi. Thay đổi sản phẩm và dữ liệu nghiên cứu: **không có**. Đối chiếu nội dung là kiểm tra tĩnh với mã nguồn, không phải chạy app, SMS hoặc benchmark mới.
