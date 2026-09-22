# NCKH Flood Rescue — Web Full-stack

Frontend Android và Chrome dùng chung một Flutter package tại `fe/app`. Mọi chỉnh sửa giao diện chỉ thực hiện trong `fe/app/lib/presentation`; backend và công cụ model vẫn nằm trong `web_fullstack`.

## Cấu trúc

- `backend/`: FastAPI, SQLite, lưu ảnh và tích hợp Twilio có kiểm soát.
- `../fe/app/`: UI Flutter dùng chung, ONNX native/PTE trên Android và ONNX Runtime Web trên Chrome.
- `model_tools/`: công cụ xuất checkpoint PyTorch sang ONNX cho trình duyệt.
- `scripts/`: lệnh kiểm thử và chạy từng thành phần.
- `DESIGN.md`: kiến trúc, giới hạn nền tảng và tiêu chí hoàn thành.

## Chạy toàn bộ tại localhost

Yêu cầu: Flutter, Node.js/npm và Python 3.11+. Chạy:

```powershell
powershell -ExecutionPolicy Bypass -File web_fullstack/scripts/run_all.ps1
```

Sau đó mở `http://127.0.0.1:8080`. Backend chạy tại `http://127.0.0.1:8000`.

## Kiểm tra toàn bộ

```powershell
powershell -ExecutionPolicy Bypass -File web_fullstack/scripts/verify.ps1
```

Script kiểm tra backend, parity/export ONNX, Flutter tests, analyzer, APK debug và Web release từ cùng `fe/app`.

## API key cần điền sau

Sao chép `backend/.env.example` thành `backend/.env`, rồi điền:

```dotenv
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
SMS_ALERT_RECIPIENT=
```

Giữ `SMS_ENABLED=false` cho đến khi điền đủ. AI, ảnh và báo cáo không dùng các khóa này; chỉ thao tác gửi SMS đã xác nhận mới gọi Twilio.

Xem [backend/README.md](backend/README.md) để chạy API và biết tên các biến môi trường cần điền sau.
