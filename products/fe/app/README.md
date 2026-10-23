# App cứu hộ Android

App Flutter gửi báo cáo/SOS tới backend Docker, lưu hàng đợi khi offline và đồng
bộ lại khi có mạng. Model PTE và Logistic Regression E_i được đóng gói trong APK.
Bản `user` chỉ chạy PTE; bản `admin` có thêm ONNX và công cụ benchmark.

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

Chạy từ thư mục gốc `nckh2`; dùng đường dẫn tương đối để vào thư mục ứng dụng:

```powershell
cd .\products\fe\app

flutter pub get
flutter analyze
flutter test --flavor user
flutter test --flavor admin test/admin_model_access_test.dart test/ai_model_test.dart test/model_benchmark_test.dart test/model_download_cleanup_test.dart
flutter build apk --flavor user --release --split-per-abi --target-platform android-arm64 --dart-define-from-file=.env.local --dart-define=SERVER_URL=https://TEN_MIEN_BACKEND
```

Lệnh trên tạo riêng APK ARM64 cho Redmi Note 11/13:
`build/app/outputs/flutter-apk/app-arm64-v8a-user-release.apk`. Nếu cần thêm
x86_64, dùng `--target-platform android-arm64,android-x64`. ExecuTorch AAR chỉ có
`arm64-v8a` và `x86_64`; không hỗ trợ ARM32 (`android-arm`/`armeabi-v7a`). Luôn
chỉ định `--target-platform` khi build bằng Flutter; mặc định của Flutter còn
gồm ARM32 nên Gradle sẽ từ chối để tránh tạo APK thiếu runtime PTE.

Thay `TEN_MIEN_BACKEND` bằng tên miền HTTPS thực tế có chứng chỉ hợp lệ. Bản mặc
định chỉ dùng địa chỉ này, không dò LAN hoặc dùng lại địa chỉ HTTP đã lưu.
Mã database giúp nhận đúng DB; nó không chứng thực máy chủ hay mã hóa kết nối.

Nếu chỉ trình diễn backend HTTP trong Wi-Fi tin cậy, mở PowerShell tại thư mục
gốc `nckh2` và chạy:

```powershell
cd .\products\fe\app

flutter build apk --flavor user --release --split-per-abi --target-platform android-arm64 --dart-define-from-file=.env.local --dart-define=ALLOW_INSECURE_LAN=true
```

Bản `user` mặc định không đóng gói `libonnxruntime.so` và không mở công cụ admin.
Để build bản admin, thay `--flavor user` bằng `--flavor admin` trong cùng lệnh;
APK có tên `app-arm64-v8a-admin-release.apk`, package `com.example.app.admin`,
cài song song với bản user `com.example.app`. Dữ liệu và phiên đăng nhập của
hai bản tách biệt. Bản user có thể cập nhật đè APK cũ nếu cùng chữ ký.

Tùy chọn demo bật HTTP cho IP nội
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
kiểm tra mở form báo cáo, xác nhận PTE nạp một lần theo yêu cầu. Benchmark model trên thiết bị và
so sánh ONNX/PTE chỉ hiện sau khi admin đăng nhập; nút benchmark ảnh logo kiểm
tra nạp/chạy model, không đánh giá accuracy/F1.

## Cài Và Kiểm Tra Trên Điện Thoại

Chuyển APK sang điện thoại và mở file để cài, hoặc bật USB debugging rồi chạy:

```powershell
flutter devices
flutter install --flavor user --release -d DEVICE_ID
```

Sau khi cài:

1. Cấp quyền vị trí; mở form tạo báo cáo để PTE bắt đầu nạp bất đồng bộ.
   Nếu đã từ chối quyền hoặc tắt dịch vụ vị trí, vào **Cài đặt > Vị trí** để
   xin lại quyền/mở cài đặt hệ thống. SOS vẫn gửi được khi chưa có GPS.
2. Gửi một báo cáo thử và kiểm tra báo cáo xuất hiện trên dashboard server.
3. Tắt Wi-Fi/data, gửi thêm báo cáo; xác nhận bản ghi nằm trong hàng đợi.
4. Bật lại Wi-Fi; xác nhận báo cáo được đồng bộ và hàng đợi giảm.
5. Đổi trạng thái trên dashboard; khi đang xem lịch sử/trạng thái, app hỏi mỗi
   15 giây sau khi lần trước hoàn tất, ở màn hình khác mỗi 60 giây. Không có
   mạng/báo cáo cần theo dõi hoặc app ra nền thì dừng timer; mở lại app cập nhật ngay.

WorkManager chỉ được giữ khi còn tin/ảnh chờ gửi **hoặc** báo cáo chưa kết thúc.
Lịch kiểm tra nền 15 phút có điều kiện có mạng; Android quyết định thời điểm chạy
thực tế. Hết việc thì hủy, lưu báo cáo mới thì đăng ký lại. SOS/gửi báo cáo thử
ngay, độc lập với lịch nền và trạng thái AI. Buộc dừng app có thể ngăn chạy nền
cho đến lần mở tiếp theo; cần kiểm tra thêm hạn chế pin riêng của hãng điện thoại.

Các lần tìm LAN tự động thất bại chờ 1 → 2 → 5 phút, tiếp tục giới hạn 5 phút.
Luôn thử địa chỉ đã biết trước; gửi mới, bấm tìm lại hoặc đổi loại kết nối có thể
tìm lại ngay. Worker nền chỉ thử địa chỉ đã biết, không quét LAN.
Kiểm tra địa chỉ cấu hình/đã lưu chờ tối đa 5 giây kết nối và 5 giây phản hồi;
quét từng IP LAN giữ mức 400 ms kết nối và 700 ms phản hồi.
Tin quá hạn chưa gửi được chờ ít nhất 30 giây trước lần thử tự động kế tiếp;
không hẹn retry khi app ra nền hoặc không có mạng. Tránh vòng lặp 0 giây khi
server mất kết nối nhưng thời điểm retry của message chưa được cập nhật.

SMS dự phòng lấy `EMERGENCY_PHONE` từ `.env.local` qua cờ build
`--dart-define-from-file=.env.local`. Tệp này bị Git bỏ qua; không đưa vào assets,
README, test hay log. Số nhận vẫn tồn tại trong APK sau build và không phải secret
đối với người phân tích APK. Thiếu cấu hình/quyền/SIM gửi được thì báo cáo vẫn lưu
trong hàng đợi; ứng dụng hiển thị SMS thất bại thay vì báo đã gửi.

SOS được lưu trước khi lấy GPS/dò mạng/xin quyền SMS. Mỗi báo cáo lấy GPS mới trong
tối đa 3 giây; thất bại thì để trống vị trí. Các lần bấm SOS lặp trong 30 giây dùng
cùng báo cáo, không tạo SMS mới; trạng thái này được đọc từ dữ liệu đã lưu nên vẫn
có hiệu lực khi mở lại app. Sau 30 giây có thể tạo SOS mới. Gửi lại dữ liệu dùng
cùng mã báo cáo; WorkManager không tự gửi SMS. Wi-Fi có kết nối nhưng server không
nhận được metadata sẽ thử SMS một lần; lỗi từ chối vĩnh viễn hoặc metadata đã ACK
không kích hoạt SMS. Nội dung SMS có dấu hiệu nguy cấp và khả năng di chuyển.
Sai số vị trí được lưu cùng báo cáo và gửi qua data (`locationAccuracyMeters`)
hoặc SMS (`acc`, đơn vị mét, làm tròn lên). App hiển thị sai số và cảnh báo
**vị trí gần đúng** khi lớn hơn 100 m; không tự coi vị trí đó là GPS chính xác.
Bluetooth, VPN và các kết nối khác cũng được thử gửi data; khả năng tới được
backend được xác định bằng yêu cầu thực tế thay vì chỉ dựa vào loại kết nối.
Xếp hàng, gửi metadata và SMS của SOS không phải chờ ảnh của báo cáo khác hoặc
lượt hỏi trạng thái đang chạy. Các yêu cầu upload cùng một báo cáo dùng chung
một lượt upload để tránh gửi ảnh trùng.
Khi SMS đã xác nhận lỗi, nút **Thử lại SMS cho SOS đã lưu** ở Trang chủ cho phép
gửi lại cùng mã sau ít nhất 30 giây và xác nhận phí/tin nhiều phần. SMS chưa rõ
kết quả không có nút gửi lại tự động để tránh trùng tin.

Android chỉ báo SMS đã gửi khi mọi phần có callback gửi thành công. Hết thời gian
chờ hoặc app đóng khi đang gửi hiển thị chưa rõ kết quả và không tự gửi SMS lặp.
Máy hai SIM cần cấu hình SIM SMS mặc định trong Android. Trạng thái gửi không xác
nhận điện thoại nhận/trung tâm đã tiếp nhận. Muốn tin xuất hiện trên dashboard,
máy/dịch vụ gateway phải chuyển tiếp tới `/api/sms/inbound` bằng token phía server;
không đưa token gateway vào app.

Hồ sơ cục bộ lưu mật khẩu bằng PBKDF2-HMAC-SHA256 với salt ngẫu nhiên. Khi cập nhật
app, dữ liệu mật khẩu cũ được chuyển đổi một lần và compact file Hive, giữ nguyên
hồ sơ/phiên. Đã bỏ đăng nhập demo. Việc hash chạy trong isolate để giao diện phản hồi.

Trong bản `admin`, benchmark tập test được tải theo yêu cầu, không nằm trong APK. Trong Cài đặt,
đăng nhập bằng tài khoản có quyền `admin` trên server. Model PTE được đóng gói
trong APK để AI chạy offline; ONNX và tập benchmark chỉ tải sau khi admin
đăng nhập. App kiểm tra SHA-256 ONNX theo manifest đi kèm PTE trước khi nạp.
Gói benchmark lưu trong bộ nhớ riêng của app, có thể xóa ở mục benchmark.
Trước mỗi lần chạy, app phải gọi `/api/auth/me` qua mạng để xác thực lại quyền
admin, kể cả khi model và gói benchmark đã tải. Sau bước này, phép đo dùng dữ
liệu/model trên máy; không thể bắt đầu benchmark khi offline.

Ở cả hai bản, trong Cài đặt → Khác, bấm **Dọn ONNX và dữ liệu benchmark đã tải**
để giải phóng dung lượng. Bản admin còn có nút xóa trong mục Benchmark.
App quay về PTE và báo dung lượng đã xóa; PTE, hồ sơ cứu hộ, ảnh và kết quả JSON
được giữ. Nút tạm khóa khi đang nạp model, tải tài nguyên hoặc chạy benchmark.
Khi nạp PTE, app tự dọn ONNX của bản cũ, cache ONNX khác hash hiện tại và file
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
`/app/model_exports`; build lại image sau khi thay model. Backend native mặc định
dùng cặp seed159 tại `products/fe/model/Edge Ai/seed159/Export/pruning_st` hoặc
cấu hình thư mục khác bằng `RESCUE_MODEL_EXPORT_DIR`.

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
Lỗi HTTP 408/429/5xx và lỗi kết nối được thử lại; HTTP 4xx còn lại được ghi lỗi
vĩnh viễn thay vì tạo message mới vô hạn. HTTP 413 được thử bằng batch nhỏ hơn;
nếu một message riêng vẫn quá lớn, chỉ báo cáo đó nhận lỗi `REQUEST_TOO_LARGE`.
Đăng xuất chỉ xóa trạng thái đăng nhập, giữ tài khoản/hồ sơ local để đăng nhập lại.

Form giới hạn mỗi mục số người từ 0 đến 10.000; mô tả tối đa 300 từ và 2.000
ký tự Unicode, từ được tách bằng khoảng trắng/xuống dòng. Bộ đếm hiển thị cả hai
giới hạn; vượt giới hạn thì không gửi. Luồng tạo báo cáo cũng kiểm tra lại trước
khi chép ảnh/lưu dữ liệu. Ảnh không đọc/lưu được sẽ hiện lỗi trên form, giữ nội
dung để người dùng bỏ ảnh hoặc chọn lại; chưa tạo báo cáo trong trường hợp này.
SMS dự phòng chỉ gửi tóm tắt gồm mã báo cáo, vị trí, số người và các trường nguy
cấp; không gửi mô tả tự do. Mô tả đầy đủ và ảnh được giữ để đồng bộ khi có mạng.
Các trường khẩn cấp vẫn có thể tạo SMS nhiều phần và phát sinh phí; callback chỉ
xác nhận khi mọi phần đã gửi. Gateway vẫn nhận được mô tả từ SMS của app cũ.

SOS/báo cáo mới chụp số điện thoại từ hồ sơ local vào record, giữ qua lần mở lại
app và gửi `contactPhone` cùng metadata. Khách chưa có hồ sơ và báo cáo cũ không
có số liên hệ vẫn gửi được. Không lấy số từ hồ sơ hiện tại để ghi ngược vào các
báo cáo cũ.

Metadata đã ACK nhưng ảnh còn chờ thì foreground hẹn thử lại sau 30 giây, kể cả
outbox metadata đã trống. Timer dừng khi offline/app ra nền hoặc đã gửi xong;
WorkManager tiếp tục phụ trách lịch nền như trên.
Outbox lưu mã báo cáo có ảnh vừa được thử gửi để luân phiên lượt tiếp theo,
kể cả khi worker khởi động lại; ảnh chậm không đứng đầu mọi lượt. Ngân sách
20 giây vẫn được kiểm tra giữa các thao tác, không ngắt upload đang chạy.

Foreground giữ quyền sở hữu Hive suốt phiên; Workmanager nhờ foreground đồng bộ
hoặc chỉ tự mở Hive khi không có chủ sở hữu. Nếu khởi động báo tác vụ cũ còn giữ
dữ liệu, bấm Thử lại; nếu isolate cũ đã chết nhưng mapping còn tồn tại, đóng hẳn
và mở lại app. App không cưỡng đoạt quyền khi hết thời gian chờ.
