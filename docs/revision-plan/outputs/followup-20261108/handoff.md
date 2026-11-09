# Bàn giao followup P02/P03/P04/P05/P07

**Đã hoàn tất phần thực hiện đủ điều kiện; hồ sơ thật còn thiếu không được đánh dấu đã xử lý xong.** Người dùng xác nhận chưa có tài liệu ngoài repo. Xem README.md, phase-04/handoff.md, evidence/README.md và P03 followup để truy vết.

- **P02 PARTIAL:** có truy vết records/checkpoint/split mới; URL/license/IAA/expert và checksum split lúc train còn thiếu. Không tạo provenance từ tên ảnh hoặc đường dẫn checkpoint.
- **P03 PARTIAL:** xác định3rawpSpearman kéo theo5Holm;15/15Holm lịch sử nhất quán với rawp lịch sử.8trường vẫnOPEN vì không có vector chưa làm tròn. Không tăng tolerance, sửa số hoặc rerun ranking/generator.
- **P04 CPU_ONLY / C5 PARTIAL:** chạy3validation smoke,256clean và2.048degraded trên exact ONNX app asset seed1024 cắt tỉa;0failure. Bootstrap252nhóm/256ảnh,5.000draw; CI không hiệu chỉnh. Chưa Android/PTE/camera độc lập hoặc label re-adjudication.
- **P05 C6 PARTIAL:** tìm thêm refs/Drive vẫn chưa rawE2E. SKIP_RERUN benchmark32JSON; NOT_RUN E2E mới vì thiếu thiết bị/receipt/isolation thực chạy. Case8run001 lịch sử vẫnFAIL được báo cáo; không resetDB hoặc gửiSMS.
- **P07:** tích hợp CPU, split lineage, RQ2 và danh tính bài trong chương trình ISDS. A1OPEN về publication chapter; giữ published theo xác nhận cũ. Shared source Việt–Anh nhất quán; đã build/check/visual. A3hoãn không bị chạm.

PDF một mặt/hai mặt174trang;48hình,39bảng. Bản tin1/1,tóm tắt3/3. Tám command build/check/float/diff exit0; có hash/text/fonts/render và phạm vi xem thật trong layout-review.md.3.818tệp sản phẩm/model/data/raw giữ nguyên SHA256, kiểm ở preservation.json. PNG dẫn xuất951MiB giữ trong output riêng vàignore, không force-add.

`final-validation.json`/`final-hashes.json` chốt kết quả đợt này; source/PDF cũ của P08 không dùng làm freeze hiện tại. Source diff riêng phiên được lưu session-source-diff.patch, tách khỏi working tree đã có thay đổi trước đó. Không tự commit/push/publish hoặc coi build là nghiệm thu.
