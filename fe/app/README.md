# NCKH Flood Rescue — Flutter Android và Web

`fe/app` là source frontend duy nhất. Android và Chrome dùng chung toàn bộ giao diện trong `lib/presentation` và cùng domain/controller.

## Chạy Android

```powershell
flutter run -d emulator-5554
```

Android dùng ONNX Runtime native, ExecuTorch PTE, Hive và WorkManager thật.

## Chạy Chrome tại localhost

Từ thư mục gốc repository:

```powershell
powershell -ExecutionPolicy Bypass -File web_fullstack/scripts/run_frontend.ps1
```

Hoặc chạy trực tiếp trong `fe/app`:

```powershell
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

Chrome dùng ONNX Runtime Web (WebGPU, fallback WASM), IndexedDB qua Hive và sự kiện online thật của browser.

## SMS

SMS không tự gửi. Người dùng phải xác nhận rõ ràng và cần cấu hình số nhận:

```powershell
flutter run -d chrome `
  --dart-define=API_BASE_URL=http://127.0.0.1:8000 `
  --dart-define=SMS_RECIPIENT=+84901234567
```

Backend đọc khóa Twilio từ `web_fullstack/backend/.env`. AI, chụp ảnh, lưu offline và upload báo cáo không sử dụng hoặc phát sinh phí Twilio.

## Kiểm tra

```powershell
flutter analyze
flutter test
flutter build apk --debug
flutter build web --release --dart-define=API_BASE_URL=http://127.0.0.1:8000
```
