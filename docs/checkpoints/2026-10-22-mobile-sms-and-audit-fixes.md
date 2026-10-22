# Mobile: SMS và các lỗi audit — 2026-10-22

## Phạm vi và trạng thái

Đã sửa 11 mục audit của `products/fe/app`, cấu hình số nhận riêng, và các race
phát hiện trong lúc ghép luồng. Chỉ thay mã nguồn/tài liệu; chưa build APK, cài
điện thoại, gửi SMS thật, commit hoặc push. Giữ các thay đổi có sẵn của người dùng.

| Mục audit | Đã sửa | Cải thiện và bằng chứng |
| --- | --- | --- |
| 1. Lưu sau SMS | Lưu SOS trước GPS/dò mạng; lưu outbox trước xin quyền/SMS | Đóng app giữa chừng vẫn có bản ghi. Test kiểm tra thứ tự lưu và phục hồi sau mở lại. |
| 2. Wi-Fi nhưng server mất kết nối | Thử gửi metadata thật; thất bại tạm thời mới thử SMS một lần | Không dựa riêng vào biểu tượng mạng; không SMS khi metadata đã ACK hoặc bị từ chối vĩnh viễn. |
| 3. Báo SMS thành công sớm | Android gom callback gửi cho từng phần; chỉ `sent` khi tất cả thành công | Phân biệt `failed`/`unknown`; timeout 30 giây hoặc Activity đóng không coi là thành công. Có self-check Kotlin. |
| 4. Gọi số khẩn cấp | Một helper mở `tel:` trực tiếp cho cả ba nơi, báo số để gọi tay khi lỗi; thêm query manifest | Không im lặng khi kiểm tra khả năng mở app sai. Widget test kiểm tra gọi trực tiếp và thông báo lỗi. |
| 5. SOS mới đứng sau backlog | Ưu tiên metadata của báo cáo đang gửi; worker tiếp tục nhiều lô | Test SOS trước hơn 50 tin cũ, nhiều lô, dừng khi lỗi/backoff; tối đa 20 lô, kiểm tra 20 giây giữa thao tác. |
| 6. Demo ghi đè hồ sơ | Bỏ tài khoản đăng nhập demo và các gợi ý liên quan | Test tài khoản demo không ghi đè hồ sơ đã đăng ký. |
| 7. GPS cũ | Lấy lại vị trí cho báo cáo mới; lỗi thì để trống; kết quả GPS cũ đến muộn bị bỏ qua | Test vị trí thay đổi, GPS lỗi, kết quả bất đồng bộ sai thứ tự. |
| 8. SMS thiếu thông tin nguy cấp | Thêm `immobile`/`severe` trước `note`; backend đọc về `urgency_features` | Test SMS chỉ có dấu hiệu nguy cấp, gateway lưu đầy đủ, gửi trùng vẫn cùng báo cáo. Tương thích SMS cũ. |
| 9. Bấm SOS lặp | Trong 30 giây dùng cùng bản ghi lưu trên máy | Không tạo thêm báo cáo/SMS; hiệu lực sau mở lại app. Bản gián đoạn trước SMS được tiếp tục với cùng ID. |
| 10. Mật khẩu plaintext | PBKDF2-HMAC-SHA256, salt riêng, 200.000 vòng, chạy trong isolate | Tự chuyển hồ sơ cũ và compact Hive. Test vector Python, bytes file, đăng nhập/đổi mật khẩu/giữ hash khi sửa hồ sơ và race đăng xuất. |
| 11. Sort/schedule mỗi ACK | Giữ cache thứ tự khi ngày tạo không đổi; đối soát WorkManager một lần sau lượt cập nhật | Test 121 báo cáo chỉ cần hai lượt đọc toàn lịch sử (đọc pending và lịch nền), không phải mỗi ACK. |

## Thử lại SMS và bảo toàn kết quả

- SMS xác nhận lỗi có nút thử lại tại Trang chủ, dùng cùng ID báo cáo, cách ít nhất
  30 giây; người dùng xác nhận vì một số phần có thể đã gửi và có thể phát sinh phí.
- SMS đang gửi/chưa rõ kết quả không tự gửi lại. Worker chỉ đồng bộ data.
- `smsAttemptedAt` phân biệt lần thử mới với callback hoặc cập nhật nền cũ.
- Lưu cục bộ giữ ACK, trạng thái cứu hộ tiến hơn và kết quả SMS mới hơn trước
  các bản ghi đến muộn. Luồng gửi đọc lại record theo ID trước SMS và sau callback.
- Màn hình gửi xong đọc lại bản ghi sau ACK, kể cả trạng thái vẫn `processing`.
- Bản SOS đang lấy GPS được đánh dấu bằng tập ID trong repository; đồng bộ đang
  chạy không được đóng băng payload khi GPS còn trống. Khi app chết, tập này mất
  và bản ghi đã lưu được phục hồi ở phiên tiếp theo, có thể thiếu GPS để xác minh.

## Cấu hình riêng

Số nhận được lưu trong `products/fe/app/.env.local`, bị Git bỏ qua. Không ghi giá trị
vào checkpoint, README, code hoặc test. Kiểm tra tệp không được Git track và không
có số thật trong các nguồn/tài liệu liên quan, gồm các tệp mới chưa track.

Khi tự build từ `products/fe/app`, thêm `--dart-define-from-file=.env.local` vào
lệnh Flutter đang dùng. `run.bat` của backend không cấp cấu hình build cho APK.
Tệp không được đóng gói như asset; giá trị cấu hình vẫn nằm trong APK sau build.

## Giữ code gọn

- Dùng chung `deliverRecord` cho SOS/báo cáo và gửi lại SMS.
- Dùng chung `openEmergencyDialer` tại Trang chủ, hướng dẫn và màn hình gửi xong.
- Dùng chung `smsStatusMessage` cho thông báo trạng thái; giữ repository và datasource
  hiện tại, thêm đọc record theo ID để tái sử dụng lookup sẵn có của Hive.
- Chỉ thêm dependency `cryptography` để dùng PBKDF2 đã có triển khai chuẩn;
  không tự viết thuật toán mật mã. `pub get` điều chỉnh bốn dependency gián tiếp
  theo SDK Flutter hiện cài (matcher/meta/test_api/vector_math).
- Giữ PTE, tiền xử lý ảnh và cặp ONNX/PTE hiện tại; không có kết quả benchmark
  model hoặc số phần trăm tiết kiệm pin/dung lượng APK mới trong lượt này.

## Kiểm tra đã đạt

- Toàn bộ Flutter test bản `user`: **151 passed** sau các sửa cuối.
- Bản `admin`, `admin_model_access_test.dart` và `model_benchmark_test.dart`:
  **12 passed**. Đây là kiểm tra quyền/logic benchmark, không đo mô hình trên máy.
- API SMS dùng database tạm: **3 passed**: dấu hiệu nguy cấp, gộp SMS với data sync,
  và xác thực token gateway. Chưa kiểm tra gateway thật.
- `dart analyze lib test`: **No issues found**.
- Kotlin: biên dịch riêng MainActivity với thư viện có sẵn; assertion self-check
  được lưu tại `android/app/src/test/kotlin/com/example/app/SmsPartResultsCheck.kt`
  kiểm tra một/nhiều phần, lỗi một phần, sai thứ tự, trùng hoặc thiếu callback.
- `git diff --check`: đạt.
- Kiểm tra số nhận trong source/tài liệu: **0 chỗ lộ**, `.env.local` bị bỏ qua.

## Cần kiểm tra sau khi người dùng tự build

1. Cấp/từ chối quyền SMS, SIM hết tiền/mất sóng, thiết bị hai SIM và chưa chọn
   SIM SMS mặc định. App cần SIM mặc định hợp lệ, không tự chọn SIM khác.
2. Gửi tới điện thoại nhận; đối chiếu “đã gửi” với thực tế. Callback gửi không
   xác nhận điện thoại nhận hoặc trung tâm đã tiếp nhận.
3. Wi-Fi còn kết nối nhưng backend không tới được; kiểm tra SMS chỉ được thử một
   lần và sau đó data sync dùng cùng mã báo cáo.
4. Bấm SOS nhanh, đóng/mở app trong 30 giây, app đóng khi xin quyền/GPS/gửi SMS,
   và thử lại SMS lỗi bằng cùng mã sau 30 giây.
5. GPS khi di chuyển, tắt định vị; không có GPS thì báo cáo phải đi vào luồng xác minh.
6. Kiểm tra mở trình gọi ở ba màn hình và WorkManager dưới hạn chế pin của hãng.
7. Nếu muốn hiện SMS trên dashboard, máy/dịch vụ nhận phải chuyển tiếp vào
   `/api/sms/inbound` bằng token gateway phía server. Token không được đưa vào app.

Giới hạn 20 giây của đồng bộ được kiểm tra giữa thao tác; request đang chạy vẫn
chịu timeout mạng. Chưa đo pin, dung lượng APK hoặc độ trễ hash mật khẩu trên máy.
Migration chỉ dọn plaintext trong file hồ sơ đang dùng, không xóa được bản backup cũ.
