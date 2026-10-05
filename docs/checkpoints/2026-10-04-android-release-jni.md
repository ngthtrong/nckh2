# Checkpoint: Android release JNI crash — 2026-10-04

## Vấn đề và thay đổi

- Log người dùng và lần mở app qua ADB đều ghi SIGABRT `ptr` trong
  `libfbjni`/ExecuTorch khi nạp PTE.
- Kết quả R8 trước sửa xóa lớp xử lý ngoại lệ và các thành phần `HybridData`
  của `com.facebook.jni`. AAR fbjni không có consumer keep rules.
- Thêm `products/fe/app/android/app/proguard-rules.pro` để giữ package JNI
  này; cập nhật README app với hướng dẫn kiểm tra. Không tắt R8 toàn app.

## Bằng chứng kiểm tra

| Kiểm tra | Trạng thái |
|---|---|
| Build APK release, giữ SERVER_URL của APK cũ | Đạt; APK khoảng 130 MB |
| Kiểm tra configuration/mapping/usage của R8 | Đạt; các lớp JNI cần thiết được giữ nguyên tên |
| Cài cập nhật bằng `adb install -r` | Đạt; không gỡ app hoặc xóa dữ liệu |
| Khởi động Activity, kiểm tra PID | Có tiến trình; chưa xác nhận UI/model |
| Nạp PTE và inference trên điện thoại | Chờ người dùng mở khóa và bấm benchmark |
| `git diff --check` | Đạt |

Điện thoại đang Dozing và từ chối input injection qua ADB (`INJECT_EVENTS`).
Vì vậy chưa kết luận lỗi crash đã hết hoặc PTE đã chạy thành công. APK mới
đã nằm ở `products/fe/app/build/app/outputs/flutter-apk/app-release.apk`.

## Tiếp theo

Mở app trên điện thoại, chọn AI on-device → ExecuTorch (.pte) → Benchmark
model trên thiết bị. Nếu còn crash, lấy log mới; nếu có kết quả, xác nhận
nạp/inference và cập nhật checkpoint mới. Benchmark ảnh logo không đo accuracy/F1.

Các thay đổi source/tài liệu trên chưa commit; không commit/push trong phiên này.
Các tài liệu trạng thái/checkpoint được AGENTS.md tham chiếu không tồn tại trong
checkout hiện tại; checkpoint này ghi trạng thái thực tế, không dựng lại lịch sử.
