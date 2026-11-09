# Rà PDF cuối — P07

Bản nội dung một mặt và hai mặt đều **171 trang**; main.pdf trùng byte content PDF. Hai bản giống nhau ở **171/171 trang render 36 dpi** và **20/20 cặp trang chi tiết render 110 dpi**. Đây là so sánh raster ở độ phân giải nêu trên, không chứng nhận mọi thành phần vector.

Đã xem sáu contact sheet của toàn bộ bản một mặt (trang vật lý 1–171); bản hai mặt có pixel comparison cho toàn quyển. Tập trang đổi và trang trước/sau được lưu trong pdf-inspection.json. Không phát hiện trang trắng, cắt chữ, chú thích bị tách sai hoặc tràn khung trong phạm vi xem. Khoảng chữ ký/nhận xét và trang sơ đồ ngang giữ theo chủ đích; không giảm font/lề, không tái tạo Draw.io manual.

Đã xem chi tiết bản cuối:

- Bản một mặt: trang vật lý 16 (bảng công bố/provenance), 74 (data profile, trung vị702,5 px), 121 (Case8 FAIL và raw absent).
- Bản hai mặt: trang83 (LR/runtime/source mapping),116 (RQ2 replay discrepancies),131 (D1–D3).
- Bốn sản phẩm riêng: toàn bộ bulletin Việt/Anh (1/1 trang), summary Việt (2 trang), summary Anh (3 trang). Đã xem tất cả bảy trang ở110 dpi và đối chiếu text/hash. Hai summary input cùng research-body, không sửa PDF riêng.
- Các trang RQ3 và Future Work cũng đã xem chi tiết ở lượt trước sửa định dạng; bản cuối có overview và so sánh raster hai variants. Tập 20 trang chi tiết đã render không đồng nghĩa mọi trang đều được đọc thủ công từng dòng.

Hai phát hiện trực quan đã sửa và dựng lại: giữ phân vị702,5 thay vì làm tròn702 trong bảng; rút đoạn đóng góp tiếng Anh lặp để tránh một trang cuối chỉ còn vài dòng. Bản171trang thay bản172trang của lượt trước. Khôi phục nhãn biểu mẫu “Ý nghĩa” trong bulletin Việt. Giữ audit165trang cũ riêng, không ghi đè lịch sử.

`content`, `content-twoside`, `deliverables`, `check`, checker hai mặt và `git diff --check` đều exit0 ở commands.json cuối. Float checker P08:48 hình/38 bảng, label/caption/LoF/LoT/refs khớp. Sáu PDF không có lỗi trích dẫn/tham chiếu/font/overflow theo checker/log; toàn bộ font được nhúng theo pdffonts. Không có lỗi pdftotext hoặc renderer. P08 lưu hash cuối.

Giới hạn: overview36 dpi, detail110 dpi, không đọc lại mọi dòng toàn quyển hoặc đánh giá hồ sơ hành chính/release. A3 placeholder giữ nguyên; A1 cấp bài và các gap khoa học vẫn mở. Build/visual-pass không scientific acceptance.
