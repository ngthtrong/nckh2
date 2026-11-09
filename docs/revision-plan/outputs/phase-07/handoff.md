# P07 bàn giao cho kiểm cuối

Đã tích hợp các handoff thật P01–P06, giữ NOT_RUN/SKIP_RERUN/NO_GO. Summary/conclusion/bulletin Việt–Anh phản ánh LR khác NLP, E_i chưa consumed, NLP/fusion chưa chứng minh hoàn thành và các kết quả âm RQ. System-tests giữ Case8 FAIL lịch sử và supplementary confirmation riêng. D1–D3 chỉ proposed.

Danh sách/căn cứ tích hợp: integration-log.md, input-receipts.json và document-drift.md. Input receipt được ghép từ checkpoint trước theo path, không giả là một snapshot độc lập ngay trước P07. Publication-verification.md giữ xác nhận published cũ nhưng A1 OPEN cấp bài; A3 giữ placeholder.

PDF một mặt/hai mặt171trang, bulletin1/1, summary2/3. Commands/exit/log ở commands.json; PDF text/font/hash/render receipts ở pdf-inspection.json; phạm vi xem thực ở layout-review.md. Check và git diff --check cuối đạt. Source generated qua exporter; template, Draw.io và code sản phẩm giữ nguyên.

P08 chốt hash source/PDF, kiểm receipt còn khớp, đối chiếu20IDs, soạn phản hồi nội bộ và traceability. Phải giữ8 sai lệch RQ2, hash byte LR/CRLF và newline cuối RQ1, không gọi full verifier PASS. tmp.md được người dùng xác nhận chủ động xóa nội dung; giữ trạng thái hiện tại và ghi riêng, không tính là sửa báo cáo của agent. Không commit/push/gửi phản hồi.
