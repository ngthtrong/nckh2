# App cứu hộ Android

App Flutter gửi báo cáo/SOS tới backend Docker, lưu hàng đợi khi offline và đồng
bộ lại khi có mạng. Model ONNX, PTE và Logistic Regression E_i được đóng gói trong
APK để xử lý trên thiết bị.

## Server Docker trên laptop

Chạy tại thư mục gốc `nckh2`:

```powershell
docker compose up -d be
docker compose ps be
```

Backend được mở ra laptop ở cổng `8000`. Điện thoại và laptop phải cùng mạng Wi-Fi.
IP Wi-Fi dùng cho bản APK hiện tại: `192.168.6.143`.

Trên trình duyệt điện thoại, mở `http://192.168.6.143:8000/healthz` trước khi dùng
app. Nếu không truy cập được, kiểm tra Docker, IP laptop, Windows Firewall và việc
router có chặn kết nối giữa các thiết bị hay không. Không dùng `localhost`,
`10.0.2.2` hoặc tên container `be` làm địa chỉ server trên điện thoại thật.

## Build APK Release

Chạy trong thư mục có file `pubspec.yaml` này:

```powershell
flutter pub get
flutter analyze
flutter test
flutter build apk --release --dart-define=SERVER_URL=http://192.168.6.143:8000
```

Kết quả: `build/app/outputs/flutter-apk/app-release.apk`.

URL server được gắn vào APK lúc build. Nếu đổi IP hoặc chuyển mạng Wi-Fi, cập nhật
`SERVER_URL` trong lệnh build và domain LAN trong
`android/app/src/main/res/xml/network_security_config.xml`, rồi cài lại APK. Các
địa chỉ ngoài danh sách HTTP này phải dùng HTTPS.

Bản release nội bộ dùng signing debug sẵn có trong Gradle để cài thử trực tiếp;
chưa phải bản ký phát hành trên Play Store.

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

Nút benchmark hiện chỉ kiểm tra một lượt inference; benchmark lặp nhiều lần và
xuất thống kê sẽ được bổ sung ở giai đoạn sau.
