# Thiết kế bản Web Full-stack cho NCKH Flood Rescue

Ngày: 2026-09-21

## 1. Mục tiêu

Tạo một bản web độc lập, chạy tại `localhost`, có giao diện và luồng nghiệp vụ tương đương ứng dụng Android hiện tại nhưng không sửa bất kỳ file nào trong `fe/app`.

Bản web phải cung cấp chức năng thật:

- chụp hoặc chọn ảnh trong trình duyệt;
- nhận diện ngập trực tiếp trên máy người dùng;
- lấy vị trí thật khi người dùng cấp quyền;
- lưu báo cáo khi offline và đồng bộ lại khi có mạng;
- đo kết nối tới backend và chọn chế độ gửi phù hợp;
- gửi báo cáo kèm ảnh tới backend;
- gửi SMS qua nhà cung cấp bên ngoài chỉ sau khi người dùng xác nhận;
- lưu và xem lịch sử báo cáo;
- hoạt động như PWA trên Chrome.

## 2. Phạm vi cách ly

Toàn bộ phần mới nằm trong thư mục `web_fullstack/`:

```text
web_fullstack/
  frontend/             Flutter Web/PWA độc lập
  backend/              FastAPI, SQLite, lưu ảnh và tích hợp SMS
  model_tools/          Xuất và kiểm tra model ONNX cho trình duyệt
  scripts/              Lệnh chạy frontend/backend và kiểm tra nhanh
  DESIGN.md             Đặc tả kiến trúc này
  README.md             Hướng dẫn chạy và mô tả những phần đã bổ sung
```

`fe/app` chỉ được đọc để tham chiếu giao diện, dữ liệu và quy tắc nghiệp vụ. Không sửa, di chuyển hoặc xóa source Android.

## 3. Các phương án đã cân nhắc

### Phương án A: Flutter Web + FastAPI, AI chạy trong Chrome

Đây là phương án được chọn. Giao diện được xây bằng Flutter Web riêng, AI dùng ONNX Runtime Web qua JavaScript interop, còn backend xử lý báo cáo, ảnh và SMS.

Ưu điểm:

- gần với giao diện Flutter Android hiện tại;
- AI chạy tại máy người dùng, giữ tính riêng tư và vẫn nhận diện khi offline;
- frontend và backend tách biệt, dễ triển khai;
- không ảnh hưởng bản Android.

Nhược điểm:

- cần lớp JavaScript interop cho ONNX Runtime Web;
- cần tải model ONNX và WASM/WebGPU khi dùng lần đầu;
- trình duyệt không thể dùng SIM trực tiếp như Android.

### Phương án B: Flutter Web + AI hoàn toàn trên backend

Đơn giản hơn nhưng mất khả năng nhận diện khi offline, tăng băng thông và đưa ảnh hiện trường lên server trước khi có kết quả. Không chọn.

### Phương án C: React/Vite + FastAPI

Tích hợp ONNX Runtime Web dễ hơn, nhưng phải viết lại toàn bộ giao diện bằng framework khác và khó giữ trải nghiệm nhất quán với Flutter Android. Không chọn.

## 4. Kiến trúc được chọn

```text
Camera / file / GPS
        |
        v
Flutter Web PWA ----> ONNX Runtime Web ----> kết quả AI cục bộ
        |
        +----> IndexedDB / hàng đợi offline
        |
        +----> FastAPI ----> SQLite + thư mục ảnh
                    |
                    +----> Twilio SMS API (chỉ khi xác nhận)
```

### 4.1 Frontend

Frontend là một Flutter project mới chỉ có nền tảng web. Nó tái tạo màn hình và luồng chính của ứng dụng Android mà không import các file phụ thuộc `dart:io`, `SmsManager`, ExecuTorch hoặc `path_provider`.

Các thành phần chính:

- `ImageCaptureService`: lấy ảnh camera hoặc file và luôn trả về bytes;
- `WebInferenceService`: gọi ONNX Runtime Web;
- `LocationService`: dùng Geolocation API qua plugin web;
- `OfflineReportStore`: lưu metadata và ảnh trong IndexedDB;
- `ReportApiClient`: gửi multipart tới backend;
- `SyncCoordinator`: thử gửi lại khi trình duyệt báo đã có mạng;
- `SmsRequestService`: chỉ gọi endpoint SMS sau hộp xác nhận;
- `CapabilityService`: hiển thị trạng thái backend, AI và SMS đã cấu hình hay chưa.

Frontend không chứa khóa API hoặc secret.

### 4.2 AI chạy trực tiếp trong Chrome

Checkpoint nguồn hiện có là `fe/app/model.pth`. Công cụ trong `model_tools/` sẽ:

1. dựng đúng MobileNetV3 Large bốn lớp;
2. nạp checkpoint;
3. xuất ONNX opset 17 có softmax;
4. tạo manifest chứa class order, input size, preprocessing và SHA-256;
5. so sánh output PyTorch và ONNX trên ảnh kiểm thử;
6. sao chép artifact hợp lệ vào frontend.

ONNX Runtime Web dùng WebGPU khi Chrome hỗ trợ và tự chuyển sang WebAssembly khi WebGPU không khả dụng. Input giữ nguyên quy tắc Android: letterbox `224x224`, NCHW, ImageNet mean/std và thứ tự nhãn `low`, `medium`, `high`, `non_flood`.

Model, manifest, nhãn và WASM được cache như tài nguyên PWA để inference tiếp tục hoạt động khi mất mạng sau lần tải đầu tiên.

Tiêu chí parity: cùng ảnh và cùng preprocessing phải cho cùng nhãn; sai lệch xác suất tối đa được kiểm soát bằng bài kiểm tra tự động.

### 4.3 Backend

Backend sử dụng FastAPI và SQLite. Ảnh được lưu trong thư mục dữ liệu riêng; đường dẫn và database có thể đổi qua biến môi trường.

API dự kiến:

- `GET /health`: trạng thái dịch vụ;
- `GET /api/capabilities`: AI/SMS/storage đã sẵn sàng hay chưa;
- `GET /probe`: bytes tĩnh để đo throughput;
- `POST /api/reports`: nhận metadata và ảnh, idempotent theo report ID;
- `GET /api/reports`: lấy lịch sử báo cáo;
- `GET /api/reports/{id}`: lấy chi tiết;
- `POST /api/reports/{id}/sms`: gửi SMS sau yêu cầu xác nhận từ frontend;
- `GET /api/sms/status/{message_id}`: đọc trạng thái gửi nếu nhà cung cấp hỗ trợ.

Backend bật CORS chỉ cho các origin được cấu hình, kiểm tra loại/kích thước ảnh, giới hạn request và không ghi secret vào log.

### 4.4 Offline và đồng bộ

Khi mất mạng, frontend lưu báo cáo và ảnh trong IndexedDB với trạng thái `pending`. Khi kết nối trở lại, ứng dụng gửi lại theo report ID; backend xử lý idempotent để tránh tạo bản ghi trùng.

PWA đăng ký service worker để hỗ trợ retry request khi Chrome cho phép Background Sync. Vì Background Sync không được mọi trình duyệt bảo đảm, `SyncCoordinator` trong ứng dụng vẫn là cơ chế chính mỗi khi trang mở lại hoặc sự kiện online xuất hiện.

Nếu thiết bị mất Internet hoàn toàn, Chrome không thể gọi backend hoặc Twilio. Báo cáo vẫn được lưu và đồng bộ khi mạng trở lại. Đây là giới hạn nền tảng web, không phải hành vi giả lập.

## 5. SMS và kiểm soát chi phí

SMS không nằm trong luồng gửi báo cáo mặc định. Frontend chỉ gọi API SMS khi người dùng bấm `Gửi SMS khẩn cấp` và xác nhận lần cuối.

Backend áp dụng:

- `SMS_ENABLED=false` theo mặc định;
- kiểm tra cấu hình đầy đủ trước khi gửi;
- rate limit theo IP/report/recipient;
- chống gửi trùng bằng idempotency key;
- giới hạn số tin mỗi giờ và mỗi ngày;
- không cung cấp sẵn số `114` làm người nhận thử nghiệm;
- trả lỗi rõ ràng khi chưa có khóa hoặc vượt giới hạn.

File `backend/.env.example` sẽ chứa tên biến, không chứa secret:

```dotenv
APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000
DATABASE_URL=sqlite:///./data/flood_rescue.db
UPLOAD_DIR=./data/uploads
ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

SMS_ENABLED=false
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
SMS_ALERT_RECIPIENT=
SMS_MAX_PER_HOUR=3
SMS_MAX_PER_DAY=10
```

Người dùng sẽ tự điền khóa sau khi tạo tài khoản. `.env` thật bị loại khỏi Git; chỉ `.env.example` được commit.

## 6. Luồng dữ liệu chính

### Gửi báo cáo bình thường

1. Người dùng chụp/chọn ảnh.
2. Trình duyệt xử lý ảnh và chạy ONNX cục bộ.
3. Trình duyệt lấy GPS nếu được cấp quyền.
4. Báo cáo được lưu vào IndexedDB trước.
5. Nếu có mạng, frontend đo `/probe` rồi chọn ảnh gốc, ảnh nén hoặc text-only.
6. Backend lưu metadata và ảnh.
7. Frontend đánh dấu báo cáo đã đồng bộ.

Luồng này không gọi Twilio và không phát sinh phí SMS.

### Gửi SMS khẩn cấp

1. Người dùng mở báo cáo đã có.
2. Người dùng bấm gửi SMS và xác nhận nội dung, người nhận.
3. Backend kiểm tra `SMS_ENABLED`, cấu hình, rate limit và idempotency.
4. Backend gọi Twilio.
5. Backend lưu message ID và trạng thái để truy vết.

## 7. Xử lý lỗi

- Model chưa tải: frontend hiển thị tiến trình và cho thử lại, không tạo kết quả giả.
- WebGPU lỗi: chuyển sang WebAssembly.
- GPS bị từ chối: báo rõ và cho phép gửi không có vị trí hoặc nhập vị trí thủ công.
- Backend mất kết nối: giữ báo cáo `pending` trong IndexedDB.
- Upload bị lặp: backend trả lại bản ghi cùng report ID.
- SMS chưa cấu hình: endpoint trả mã lỗi cấu hình, không gọi nhà cung cấp.
- SMS thất bại: giữ trạng thái `failed` và không tự động gửi lại nếu chưa có thao tác hoặc chính sách rõ ràng.
- Dữ liệu/ảnh không hợp lệ: backend từ chối với thông báo cụ thể.

## 8. Kiểm thử và tiêu chí hoàn thành

### AI

- export ONNX thành công từ checkpoint hiện có;
- ONNX checker vượt qua;
- parity test PyTorch/ONNX vượt qua trên bộ ảnh mẫu;
- WebGPU và WebAssembly đều chạy được ít nhất một inference thật.

### Frontend

- unit test preprocessing, queue và lựa chọn chế độ gửi;
- widget test các trạng thái AI/backend/SMS;
- chạy được `flutter build web`;
- chạy tại `http://localhost:8080`;
- offline sau lần tải đầu vẫn mở giao diện, xem lịch sử và chạy AI;
- báo cáo pending đồng bộ khi có mạng trở lại.

### Backend

- pytest cho validation, idempotency, lưu ảnh, danh sách báo cáo và rate limit;
- endpoint SMS không gọi Twilio khi `SMS_ENABLED=false`;
- kiểm thử Twilio dùng số thử nghiệm do người dùng cấu hình, không dùng đầu số khẩn cấp;
- CORS chỉ cho origin cấu hình;
- khởi động được bằng một lệnh script.

### Bảo toàn Android

- `git diff -- fe/app` không có thay đổi do dự án web;
- các file mới chỉ nằm trong `web_fullstack/`;
- tài liệu `README.md` liệt kê file đã thêm, mục đích, lệnh chạy và biến môi trường.

## 9. Không thuộc phạm vi phiên bản đầu

- triển khai production/cloud;
- mua hoặc đăng ký tài khoản SMS;
- tự động gửi tới cơ quan khẩn cấp thật;
- dashboard điều phối đa đơn vị;
- xác thực production, phân quyền nhiều vai trò;
- thay đổi source Android hiện có.

