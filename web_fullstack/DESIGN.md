# Thiết kế Android + Web dùng chung cho NCKH Flood Rescue

Ngày cập nhật: 2026-09-22

## Mục tiêu

Android và Chrome chạy cùng một Flutter package tại `fe/app`. Vì hai nền tảng dùng chung toàn bộ `lib/presentation`, mọi chỉnh sửa giao diện tại đây sẽ xuất hiện trên cả app Android lẫn trang localhost.

Không có chức năng giả lập trong bản Web. Mỗi khác biệt nền tảng được đặt sau một interface chung và có cách triển khai thật phù hợp với nền tảng đó.

## Cấu trúc

```text
fe/app/
  lib/presentation/       UI và controller dùng chung
  lib/domain/             entity, repository contract và use case dùng chung
  lib/data/datasources/   adapter Android/Web chọn bằng conditional import
  assets/models/          model ONNX/PTE đóng gói cho Android
  web/models/             model ONNX cho Chrome
  web/vendor/ort/         ONNX Runtime Web tự phục vụ từ localhost
  web_runtime/            package npm chỉ dùng để chuẩn bị runtime ONNX

web_fullstack/
  backend/                FastAPI, SQLite, lưu ảnh và tích hợp Twilio
  model_tools/            xuất checkpoint PyTorch sang ONNX và kiểm tra parity
  scripts/                chạy backend, Flutter Web và kiểm tra toàn bộ
```

## Adapter theo nền tảng

| Chức năng | Android | Chrome |
|---|---|---|
| AI | ONNX Runtime native hoặc PTE | ONNX Runtime Web (WebGPU, fallback WASM) |
| Ảnh | camera/thư viện ảnh, bytes | camera/file picker của trình duyệt, bytes |
| Nén ảnh | `flutter_image_compress` | codec ảnh Dart chạy thật trong trình duyệt |
| Vị trí | dịch vụ vị trí Android | Geolocation API của trình duyệt |
| Lưu offline | Hive trên thiết bị | Hive trên IndexedDB |
| Đồng bộ | WorkManager và khi app hoạt động | sự kiện online và khi trang khởi động |
| SMS | native method channel sau khi cấp quyền | backend/Twilio sau xác nhận của người dùng |

Chrome không thể dùng SIM hoặc WorkManager của Android. Backend SMS và sự kiện online là cách triển khai thật tương ứng, không phải no-op.

## Luồng báo cáo

1. Người dùng chụp hoặc chọn ảnh.
2. Model chạy cục bộ và tạo kết quả AI.
3. App lấy GPS sau khi người dùng cấp quyền.
4. Báo cáo cùng bytes ảnh được lưu cục bộ trước.
5. Khi có mạng, app đo `/probe` và chọn ảnh gốc, ảnh nén hoặc chỉ metadata.
6. App gửi multipart tới `POST /api/reports`; report ID giúp backend chống tạo trùng.
7. Báo cáo được đánh dấu đã đồng bộ khi backend trả đúng ID.

Các yêu cầu đồng bộ đến cùng lúc được gộp thành một lượt đang chạy và nhiều nhất một lượt tiếp theo, tránh upload trùng.

## AI dùng chung artifact

Nguồn model là `fe/app/model.pth`. `web_fullstack/scripts/export_web_model.ps1` kiểm tra PyTorch/ONNX parity rồi xuất vào `fe/app/web/models`. Chỉ sau khi export thành công, script sao chép cùng model và manifest sang `fe/app/assets/models`, vì vậy Android và Chrome không bị lệch phiên bản.

Chrome nạp `fe/app/web/onnx_bridge.js` và runtime trong `fe/app/web/vendor/ort`. Runtime được cài từ package khóa phiên bản ở `fe/app/web_runtime`.

## Backend và SMS

FastAPI nhận báo cáo, lưu SQLite/ảnh và cung cấp capability cho frontend. SMS mặc định tắt; chỉ endpoint SMS mới dùng thông tin Twilio. AI, chụp ảnh, lưu offline và upload báo cáo không dùng khóa Twilio.

SMS chỉ chạy khi:

1. backend có cấu hình hợp lệ và `SMS_ENABLED=true`;
2. người dùng thấy người nhận đã che bớt và xác nhận lần cuối;
3. backend vượt qua rate limit và idempotency check.

Không cấu hình sẵn đầu số khẩn cấp thật làm số thử nghiệm.

## Quy tắc bảo trì

- Chỉnh giao diện duy nhất trong `fe/app/lib/presentation`.
- Không tạo thêm một Flutter frontend riêng cho Web.
- Tính năng phụ thuộc nền tảng phải có interface chung và adapter Android/Web chạy thật.
- Giữ secret trong `web_fullstack/backend/.env`; chỉ commit `.env.example`.
- Chạy `web_fullstack/scripts/verify.ps1` trước khi hợp nhất thay đổi lớn.

## Giới hạn nền tảng được hiển thị rõ

- Nếu người dùng từ chối camera hoặc GPS, app báo lỗi quyền thay vì tạo dữ liệu giả.
- Khi Chrome mất Internet, báo cáo vẫn được lưu offline nhưng backend và SMS phải chờ kết nối trở lại.
- Chrome không gửi SMS trực tiếp qua SIM; SMS Web cần backend và nhà cung cấp đã cấu hình.
- WebGPU không có thì inference chuyển sang WASM, vẫn dùng model thật.
