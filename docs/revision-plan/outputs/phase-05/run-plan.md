# Kế hoạch tối thiểu khi mở lại — chưa thực thi

1. Xác minh một Android thật, OS/model, hash APK/commit/model/package/backend/split. Dùng fixtures run_001/run_002 đã kiểm package; không dùng 316/334 seeded rows làm số bài app gửi.
2. Tạo backend, SQLite, uploads và Docker volume riêng ở cổng LAN thử nghiệm. Kiểm coordinator trỏ instance này trước mở app. Coordinator mặc định dùng DB chung nên chưa chạy trong phiên này. Không reset shared DB hoặc xóa pending người dùng.
3. Mỗi run lưu manifest, thời điểm, input/report IDs, checks.csv, logcat và backend-observations. Kiểm online; 503→retry/outbox đúng một bài; proxy 300/20 kbit/s; missing GPS→review; status feedback; manual UI; physical offline/reconnect. Dashboard là scope riêng.
4. Diagnostic E_i: ghi giá trị computed, payload, stored và ReportV2.E. Adapter hiện dùng urgency/description; không sửa code để phép thử đạt.
5. Giữ FAIL/NOT_RUN, retry history và sự cố crash/session Case 8. Xác nhận manual tách khỏi service assertions. Nếu cần latency: một model/runtime đã chốt, 256 ảnh, năm warmup và tối đa ba phiên có thermal/battery/charger/rest; ảnh lặp không tạo thêm thiết bị độc lập.
6. HTTP 503/proxy khác physical outage/cell. Local queue không bảo đảm delivery; SMS cần cell/gateway. Chưa gửi SMS hoặc nhắn số người khác.

Gói sẵn có đã kiểm read-only bằng `python3 products/fe/experiment_mobile/prepare_assets.py --check`. Hash runner trong source-hashes.json. Chuẩn bị protocol/package không phải phép đo mới.
