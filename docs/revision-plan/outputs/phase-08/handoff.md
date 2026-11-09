# Bàn giao cuối — chuỗi P01–P08

Đã thực hiện P01 → P02 → P03; đánh giá điều kiện P04–P06; tích hợp P07 và kiểm cuối P08. P04 không chạy suy luận ảnh, P05 không chạy E2E mới và không lặp benchmark ảnh đã đủ raw, P06 NO_GO cho ablation ảnh/văn bản. Các quyết định này có căn cứ riêng, không phải kết quả thí nghiệm mới.

Báo cáo một mặt và hai mặt đều **171 trang**; bản tin Việt/Anh **1/1 trang**, tóm tắt Việt/Anh **2/3 trang**. Nguồn LaTeX được sửa đúng phạm vi; tệp generated được sinh qua exporter. PDF chính ở `report/main.pdf`, bản hai mặt ở `report/build/content-twoside/content.pdf`.

Hồ sơ cần đọc:

- [Ledger đủ 20 nhận xét](final-review-status.csv): 8 DONE_WITH_EVIDENCE, 8 PARTIAL, 2 OPEN, 1 DEFERRED_WITH_REASON và 1 DEFERRED_BY_USER.
- [Phản hồi nội bộ](response-draft.md), chưa gửi Hội đồng.
- [Kiểm chứng](validation.md), [tái lập](reproducibility.md), [hash cuối](final-hashes.json) và [thay đổi so baseline](changed-files.json).
- [Lệnh/exit](../phase-07/commands.json), [phạm vi xem PDF](../phase-07/layout-review.md) và [float checks](float-checks.json).

Các kiểm tra kỹ thuật cuối đạt, gồm 48 hình/38 bảng và không có sai lệch hash đầu vào của các receipt phân tích. Có 3.576/3.584 kiểm tra số khớp; 8 sai lệch raw p/Holm RQ2 vẫn mở. Hash byte LR/CRLF và newline cuối RQ1 có disposition; không sửa dữ liệu hay manifest để làm kiểm tra đạt.

Còn cần minh chứng công bố cấp bài; provenance/license/IAA và tính độc lập sự kiện của ảnh; artifact chưa làm tròn để giải quyết sai lệch RQ2; xác nhận chuyên gia cho dispatch; runtime/clean parity/thiết bị cho X02; và raw E2E hoặc một phiên thử mới được cô lập khi đủ điều kiện. NLP/fusion chưa được chứng minh hoàn thành. D1–D3 chỉ là đề xuất; A3 do người dùng thêm sau.

Không đổi app/backend/model/trọng số/hợp đồng, không huấn luyện hoặc chạy lại campaign, không commit/push/gửi phản hồi. Sửa đổi sẵn có và raw được kiểm bảo toàn; riêng nội dung tmp.md do người dùng chủ động xóa và yêu cầu giữ nguyên. Artifact lớn và ảnh render giữ local theo `.gitignore`, có hash. Build/check/visual không phải scientific acceptance hoặc chấp thuận nghiệm thu.
