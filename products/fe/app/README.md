# App cứu hộ Android

App Flutter gửi báo cáo/SOS tới backend Docker, lưu hàng đợi khi offline và đồng
bộ lại khi có mạng. Model PTE và Logistic Regression E_i được đóng gói trong APK;
ONNX chỉ tải sau khi admin đăng nhập.

## Server Docker trên laptop

Chạy tại thư mục gốc `nckh2`:

```powershell
docker compose up -d --build be
docker compose ps be
```

Backend được mở ra laptop ở cổng `8000`. Điện thoại và laptop phải cùng mạng Wi-Fi.
Khi build demo với `ALLOW_INSECURE_LAN=true`, app Android tự tìm backend trong cùng mạng `/24` qua `GET /healthz` và nhớ mã
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
flutter build apk --release --split-per-abi --target-platform android-arm64 --dart-define=SERVER_URL=https://TEN_MIEN_BACKEND
```

Lệnh trên tạo riêng APK ARM64 cho Redmi Note 11/13:
`build/app/outputs/flutter-apk/app-arm64-v8a-release.apk`. Nếu cần cả ARM32 và
x86_64, bỏ tùy chọn `--target-platform android-arm64`.

Thay `TEN_MIEN_BACKEND` bằng tên miền HTTPS thực tế có chứng chỉ hợp lệ. Bản mặc
định chỉ dùng địa chỉ này, không dò LAN hoặc dùng lại địa chỉ HTTP đã lưu.
Mã database giúp nhận đúng DB; nó không chứng thực máy chủ hay mã hóa kết nối.

Nếu chỉ trình diễn backend HTTP trong Wi-Fi tin cậy, dùng lệnh riêng:

```powershell
flutter build apk --release --split-per-abi --target-platform android-arm64 --dart-define=ALLOW_INSECURE_LAN=true
```

Đây vẫn là **một APK dùng chung User/Admin**. Tùy chọn này bật HTTP cho IP nội
bộ/loopback và tự tìm backend cổng 8000; có thể thêm
`--dart-define=SERVER_URL=http://IP_LAPTOP:8000` để thử IP đó trước. Không cần
build lại khi IP đổi trong cùng `/24`. HTTP demo không mã hóa mật khẩu/token,
không dùng qua mạng công cộng; bản triển khai phải dùng lệnh HTTPS ở trên.
Mã database được giữ trong volume Docker; nếu xóa toàn bộ dữ liệu/volume và tạo
server mới, app sẽ không tự gửi hàng đợi cũ sang server khác.

Bản release nội bộ dùng signing debug sẵn có trong Gradle để cài thử trực tiếp;
chưa phải bản ký phát hành trên Play Store.

`android/app/proguard-rules.pro` giữ các lớp `com.facebook.jni` mà ExecuTorch
gọi từ native code. Flutter tự áp dụng file này khi build release. Không bỏ quy
tắc này: R8 có thể xóa lớp xử lý lỗi/`HybridData`, làm app crash lúc nạp PTE
(`SIGABRT` trong `libfbjni`). Sau khi sửa, cài APK cập nhật đè lên bản cũ và
kiểm tra mở app, xác nhận PTE nạp mặc định. Benchmark model trên thiết bị và
so sánh ONNX/PTE chỉ hiện sau khi admin đăng nhập; nút benchmark ảnh logo kiểm
tra nạp/chạy model, không đánh giá accuracy/F1.

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
đăng nhập bằng tài khoản có quyền `admin` trên server. Model PTE được đóng gói
trong APK để AI chạy offline ngay; ONNX và tập benchmark chỉ tải sau khi admin
đăng nhập. App kiểm tra SHA-256 ONNX theo manifest đi kèm PTE trước khi nạp.
Gói benchmark lưu trong bộ nhớ riêng của app, có thể xóa ở mục benchmark và
chạy offline sau khi tải.

Trong Cài đặt → Benchmark, bấm **Xóa ONNX và tập benchmark đã tải** để giải phóng
dung lượng. App quay về PTE và báo số MB đã xóa; PTE, hồ sơ cứu hộ và kết quả JSON
được giữ. Nút tạm khóa khi đang nạp model, tải tài nguyên hoặc chạy benchmark.
Khi khởi động, app tự dọn ONNX của bản cũ, cache ONNX khác hash hiện tại và file
tải ONNX dở; ONNX đúng phiên bản đang dùng được giữ để admin nạp lại.

`integration_test` nằm trong `dev_dependencies`; Flutter loại native plugin này
khỏi bản release, còn các bài kiểm thử tích hợp vẫn có thể chạy trong môi trường phát triển.

Sau khi benchmark kết thúc trên Android, bấm **Tải JSON** tại từng kết quả
ONNX/PTE, chọn thư mục **Downloads** trong hộp thoại hệ thống rồi lưu. Mỗi
runtime có file `.json` riêng, gồm toàn bộ dự đoán, metric và latency; gửi file
gốc sang máy tính để tổng hợp báo cáo. Tránh dán JSON dài qua ứng dụng chat vì
nội dung có thể bị cắt. Nút sao chép vẫn được giữ để xem nhanh.

Gói server được tạo bằng `python products/be/build_benchmark_package.py` từ CSV
và ảnh thuộc test split. Backend Docker chứa model ONNX/PTE cùng manifest tại
`/app/model_exports`; build lại image sau khi thay model. Backend native dùng
thư mục `products/fe/model/Edge Ai/Export` mặc định hoặc cấu hình
`RESCUE_MODEL_EXPORT_DIR`.

Tên gói dùng fingerprint của CSV chia tập, không dùng seed huấn luyện. Manifest
có `splitCsvSha256`; cùng một split có thể đánh giá cả checkpoint seed 42 và
seed 1024. Sau khi dựng lại gói hoặc thay model, build/cài APK release mới nếu
asset model thay đổi, cập nhật gói trên backend và xóa/tải lại gói benchmark đã
lưu trên điện thoại. Khi lưu JSON kết quả, ghi kèm seed/hash model, hash APK,
hash split, thiết bị/Android và ngày đo; tên dataset không xác nhận seed model.
JSON schema 2 tự lưu manifest model/checkpoint, hash artifact theo runtime,
`splitCsvSha256`, phiên bản app, thiết bị/Android, run ID và thời điểm UTC.
Hash APK vẫn cần ghi từ file APK trên máy tính. Runtime bị khóa trong lúc đo;
nếu runtime hoặc loại kết quả thay đổi, phép đo bị hủy để tránh gắn nhãn sai.

Ảnh đính kèm được chép vào vùng lưu lâu dài trước khi xếp hàng. Nếu ảnh cũ bị
mất/không đọc được, app giữ trạng thái chưa gửi xong và báo lỗi ảnh; ACK nội dung
đã nhận được lưu riêng để không tạo lại message mỗi lần thử gửi ảnh.
Đăng xuất chỉ xóa trạng thái đăng nhập, giữ tài khoản/hồ sơ local để đăng nhập lại.

Foreground giữ quyền sở hữu Hive suốt phiên; Workmanager nhờ foreground đồng bộ
hoặc chỉ tự mở Hive khi không có chủ sở hữu. Nếu khởi động báo tác vụ cũ còn giữ
dữ liệu, bấm Thử lại; nếu isolate cũ đã chết nhưng mapping còn tồn tại, đóng hẳn
và mở lại app. App không cưỡng đoạt quyền khi hết thời gian chờ.
