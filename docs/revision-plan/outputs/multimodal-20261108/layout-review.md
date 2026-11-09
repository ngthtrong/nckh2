# Rà PDF và bố cục của đợt bổ sung

Ngày 08/11/2026, Asia/Taipei. Phạm vi là report và bốn sản phẩm được tái sinh từ nguồn có chỉnh sửa; không đánh giá hồ sơ nghiệm thu/release.

## Bản cuối

- Báo cáo một mặt/hai mặt: **176/176 trang**, 48 hình/41 bảng; 25 tài liệu trong nguồn bibliography.
- Bản tin Việt/Anh: **1/1 trang**; tóm tắt Việt/Anh: **2/3 trang**.
- `report-check-layout-final` và `report-check-twoside-layout-final` exit 0; checker kiểm source/caption/label/danh mục/PDF và overflow/ref/font logs. Còn một placeholder hành chính đã có, không được biến thành xác nhận hồ sơ nộp đủ.
- Font của cả sáu PDF được nhúng; main.pdf khớp PDF một mặt. Hash/text/font/render receipts nằm trong `report-checks/pdf-inspection.json`.
- Render 30 dpi: **176/176 trang hai biến thể giống pixel**, không có trang khác. Đây là đối chiếu kỹ thuật, không phải hai người phản biện độc lập.

## Phạm vi đã xem thực tế

Đã mở đủ năm overview sheets của bản 177 trang trước rút gọn, bao quát toàn quyển ở độ phân giải thumbnail. Đã xem native 95 dpi các trang vật lý **122, 124, 125, 134**: mở đầu pilot, bảng ablation, bảng CI, diễn giải và kết luận; đồng thời xem trực tiếp trang **124 bản hai mặt**. Hai bảng mới đọc được, đủ giá trị đối chứng, CI có dấu âm/dương đúng, không tràn lề hoặc mất nhãn.

Đã xem đủ tám trang của bốn sản phẩm trước rút gọn: bulletin Việt/Anh từng trang, summary Việt ba trang và Anh ba trang. Phát hiện summary Việt có trang cuối quá ngắn; đã rút gọn diễn giải lặp về LR/mạng/pilot, giữ số liệu và giới hạn, không giảm font/lề. Build lại đúng hai biến thể và sản phẩm đi kèm, rồi kiểm lại.

Sau rút gọn, đã mở trực tiếp bản cuối trang **15/16 của quyển** và **1/2 của summary Việt** ở 95 dpi. Hai trang tóm tắt đủ phần 1–8, bảng công bố và giới hạn; không còn trang thứ ba chỉ có một đoạn ngắn. Không sửa trạng thái published hoặc ảnh cá nhân đã có.

`layout-delta.json` đối chiếu toàn bộ render trước/sau: **169 trang giữ nguyên pixel ở cùng số trang**, các trang thay đổi là **15, 16, 172–176**, và trang cuối 177 bị loại khi summary Việt còn hai trang. Năm trang 172–176 nhúng summary Việt/Anh khớp pixel với PDF standalone tương ứng. Bốn trang nội dung mới đã xem và năm trang English summary/bulletin đã xem còn khớp pixel **ở 95 dpi** với render cuối; không lặp lại kiểm đọc cùng ảnh khi không đổi. Những ảnh đã xem của phiên trước rút gọn được giữ trong `report-checks-before-summary-trim/`, receipt cuối là `report-checks/`.

## Lỗi đã xử lý và giới hạn

Lần check đầu báo caption bảng pilot có macro số mẫu không khớp tên danh mục theo checker hiện có. Đã sửa **script sinh caption**, giữ số mẫu trong thân bài, tái sinh và build/check lại; không sửa checker hay số liệu để pass. Logs/exit đầu được giữ riêng. Một hình ngang RQ3 tiếp tục float ở trang 123 theo bố cục của chương; không thay lại sơ đồ lịch sử hoặc can thiệp font/lề.

Thumbnail cho phép rà phân bố trang và khối lớn, không thay đọc từng chữ. Rà chi tiết tập trung nội dung thay và các sản phẩm, không xác nhận đã đọc lại toàn văn phụ lục nguồn, giấy tờ scan hoặc đánh giá khoa học độc lập. Build/visual đạt không đóng khoảng trống tiếng Việt, chuyên gia, E2E hoặc eight discrepancies RQ2.
