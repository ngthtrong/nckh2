# Kiểm chứng cuối

Các lệnh `content`, `content-twoside`, `deliverables`, `check`, checker hai mặt, float checker hai bản và `git diff --check` đều exit 0 ở trạng thái cuối. Đã đối chiếu nguồn, danh mục, caption/label/ref, log, font và text PDF. Phạm vi xem thực tế ở `../phase-07/layout-review.md`; hash source/PDF ở `final-hashes.json`.

Hai bản nội dung đều 171 trang, có 48 hình/38 bảng. Toàn bộ font được nhúng; không phát hiện lỗi overflow, tham chiếu/trích dẫn hoặc renderer. Hai bản giống nhau ở 171/171 trang render 36 dpi và 20/20 cặp trang chi tiết 110 dpi. Bốn sản phẩm Việt–Anh đã được xem đủ bảy trang. Đây là kiểm tra kỹ thuật có giới hạn độ phân giải, không đọc lại mọi dòng hoặc đánh giá hồ sơ release.

Ledger đủ 20 ID: 8 DONE_WITH_EVIDENCE, 8 PARTIAL, 2 OPEN, 1 DEFERRED_WITH_REASON và 1 DEFERRED_BY_USER. Không gọi toàn bộ nhận xét đã khắc phục hoặc NLP/fusion đã được thực nghiệm.

Các giới hạn còn giữ rõ:

- 8 sai lệch raw p/Holm RQ2; hash byte LR khác bản lịch sử CRLF; CSV RQ1 thiếu newline cuối. Các số/byte gốc không được sửa để làm kiểm tra đạt.
- A1 OPEN ở cấp bài, C5 OPEN vì chưa có suy luận robustness; raw E2E chưa khôi phục. A3 hoãn theo người dùng.
- Không chạy train/tune, inference robustness, mobile/E2E/SMS/thực địa mới, fusion/ASR/định vị mới hoặc full RQ campaign. Không chạy check-release vì chưa đánh giá hồ sơ nghiệm thu chính thức.

Bảo toàn 5.347 mục baseline: 5.316 không đổi, 30 tệp thay đổi thuộc phạm vi báo cáo/kế hoạch, 1 tệp tmp.md do người dùng xác nhận chủ động sửa; không có thay đổi ngoài phạm vi chưa giải trình. Các receipt nguồn P02/P03/P05/P06 không có hash mismatch. HEAD không đổi.

Các lỗi kỹ thuật trong phiên đã được khắc phục: hai đoạn tràn hbox, dòng trống cuối tệp, phân vị bị làm tròn và một trang tiếng Anh chỉ còn ít dòng. Một lượt P02 check/text chạy khi PDF đang build đã bị loại; chỉ dùng lượt kiểm sau khi build kết thúc. Receipt P01–P03 là checkpoint lịch sử, không thay receipt cuối sau sửa P07.
