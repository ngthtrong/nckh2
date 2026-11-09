# Giải thích phạm vi protocol

Protocol có SHA256 `5f73e56e3cc5bb67b34bd201a5d63d321d3ffeb12b8c70f44b365c63509d86ab` được giữ nguyên sau selection lock. Không thay lưới C, split, target, threshold, cap hoặc cách loại trùng sau khi biết kết quả.

Chuỗi `LOCKED_BEFORE_DOWNLOAD_TRAINING_AND_TEST_PREDICTIONS` trong protocol nói đến **download ảnh đã chọn**, training và test predictions. Trước đó đã có các probe đọc card/API và một phần metadata train để xác minh source/schema/event names. Không coi đây là protocol khóa trước mọi tiếp xúc với metadata; chưa xem performance hay prediction test khi khóa.

Intake thực có 12.708 hàng agreed-label; sau chọn theo metadata còn 4.309; audit ảnh loại 48 hàng thuộc component xuyên split, còn 2.971 train/589 dev/701 test. Đúng quy tắc đã khóa, không bù thêm mẫu sau loại trùng. Test có 182 informative và 519 not_informative; train có 2.188 informative và 783 not_informative. Đây là dịch chuyển phân bố nhãn đáng kể giữa sự kiện, cần giữ khi đọc performance; không chỉnh prior/threshold theo test.

682 nhóm bản trùng của test không phải 682 sự kiện độc lập. Chỉ có một sự kiện test. 2.000 bootstrap draw dùng nhóm để giữ tương quan bản gần trùng và chỉ mô tả độ bất định có điều kiện trong sự kiện này. Không suy variance giữa các sự kiện hoặc chứng nhận dữ liệu độc lập hoàn toàn.
