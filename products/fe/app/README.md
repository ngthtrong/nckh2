# App cứu hộ Android

App Flutter gửi báo cáo/SOS tới backend Docker, lưu hàng đợi khi offline và đồng
bộ lại khi có mạng. Model ONNX, PTE và Logistic Regression E_i được đóng gói trong
APK để xử lý trên thiết bị.

## Server Docker trên laptop

Chạy tại thư mục gốc `nckh2`:

```powershell
docker compose up -d --build be
docker compose ps be
```

Backend được mở ra laptop ở cổng `8000`. Điện thoại và laptop phải cùng mạng Wi-Fi.
App Android tự tìm backend trong cùng mạng `/24` qua `GET /healthz` và nhớ mã
database của server. Nếu IP laptop đổi, app xác minh server ở IP mới trước khi
gửi báo cáo đang chờ. Nếu không tìm thấy đúng server, báo cáo tiếp tục nằm trong
hàng đợi; vào Cài đặt > Máy chủ cứu hộ để xem IP hiện tại hoặc bấm tìm lại.

Trên trình duyệt điện thoại, mở `http://IP_LAPTOP:8000/healthz` trước khi dùng
app. Nếu không truy cập được, kiểm tra Docker, Windows Firewall và việc router
có chặn kết nối giữa các thiết bị hay không. Không dùng `localhost`,
`10.0.2.2` hoặc tên container `be` làm địa chỉ server trên điện thoại thật.

## Build APK Release

Chạy trong thư mục có file `pubspec.yaml` này:

```powershell
flutter pub get
flutter analyze
flutter test
flutter build apk --release
```

Kết quả: `build/app/outputs/flutter-apk/app-release.apk`.

Không cần sửa APK khi IP laptop đổi trong cùng mạng `/24`. Có thể truyền
`--dart-define=SERVER_URL=http://IP_LAPTOP:8000` để app thử địa chỉ đó trước.
Mã database được giữ trong volume Docker; nếu xóa toàn bộ dữ liệu/volume và tạo
server mới, app sẽ không tự gửi hàng đợi cũ sang server khác.

Bản release nội bộ dùng signing debug sẵn có trong Gradle để cài thử trực tiếp;
chưa phải bản ký phát hành trên Play Store.

`android/app/proguard-rules.pro` giữ các lớp `com.facebook.jni` mà ExecuTorch
gọi từ native code. Flutter tự áp dụng file này khi build release. Không bỏ quy
tắc này: R8 có thể xóa lớp xử lý lỗi/`HybridData`, làm app crash lúc nạp PTE
(`SIGABRT` trong `libfbjni`). Sau khi sửa, cài APK cập nhật đè lên bản cũ và
kiểm tra mở app, chọn ExecuTorch (.pte), chạy "Benchmark model trên thiết bị".
Đây là kiểm tra nạp/chạy model bằng ảnh logo, không phải đánh giá accuracy/F1.

## Cài Và Kiểm Tra Trên Điện Thoại

Chuyển APK sang điện thoại và mở file để cài, hoặc bật USB debugging rồi chạy:

```powershell
flutter devices
flutter install --release -d DEVICE_ID
```

Sau khi cài:

1. Cấp quyền vị trí khi app yêu cầu; kiểm tra AI đã nạp.
2. Gửi một báo cáo thử và kiểm tra báo cáo xuất hiện trên dashboard server.
3. Tắt Wi-Fi/data, gửi thêm báo cáo; xác nhận bản ghi nằm trong hàng đợi.
4. Bật lại Wi-Fi; xác nhận báo cáo được đồng bộ và hàng đợi giảm.
5. Đổi trạng thái trên dashboard; xác nhận app cập nhật trong khoảng 15 giây.

SMS dự phòng chỉ hoạt động khi build với số tổng đài thật bằng
`--dart-define=EMERGENCY_PHONE=...` và đã cấp quyền SMS. Khi chưa cấu hình số này,
báo cáo offline vẫn được giữ để đồng bộ qua data sau.

Benchmark tập test được tải theo yêu cầu, không nằm trong APK. Trong Cài đặt,
đăng nhập server bằng tài khoản `rhna`, sau đó bấm **Tải gói benchmark**; server
chỉ cấp gói cho username này. Gói lưu trong bộ nhớ riêng của app, có thể xóa ở
mục benchmark. Benchmark chạy offline sau khi tải.

Gói server được tạo bằng `python products/be/build_benchmark_package.py` từ CSV
và ảnh thuộc test split, rồi được đóng gói cùng backend Docker image.
