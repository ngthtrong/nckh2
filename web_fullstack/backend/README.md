# Flood Rescue Web Backend

Backend này là phần mới, độc lập với ứng dụng Android trong `fe/app`. Nó cung cấp API thật để lưu báo cáo cứu hộ, lưu ảnh vào ổ đĩa, đọc lịch sử và gửi SMS qua Twilio khi người dùng xác nhận.

## Thành phần đã thêm

- `app/config.py`: đọc cấu hình từ biến môi trường và `.env`.
- `app/database.py`: tạo và truy cập SQLite cho báo cáo và trạng thái SMS.
- `app/report_service.py`: kiểm tra loại, chữ ký và kích thước ảnh trước khi lưu.
- `app/sms.py`: tạo nội dung cảnh báo, kiểm soát idempotency/rate limit và gọi Twilio.
- `app/routes/`: các endpoint báo cáo và SMS.
- `tests/`: kiểm thử health, CORS, lưu báo cáo, idempotency, ảnh và an toàn SMS.

## Chạy kiểm thử

Yêu cầu Python 3.11 trở lên. Từ thư mục gốc repository:

```powershell
powershell -ExecutionPolicy Bypass -File web_fullstack/scripts/test_backend.ps1
```

## Chạy backend

```powershell
powershell -ExecutionPolicy Bypass -File web_fullstack/scripts/run_backend.ps1
```

API chạy tại `http://127.0.0.1:8000`; tài liệu tương tác ở `http://127.0.0.1:8000/docs`.

Các endpoint hiện có:

- `GET /health`
- `GET /api/capabilities`
- `GET /probe`
- `POST /api/reports`
- `GET /api/reports`
- `GET /api/reports/{id}`
- `POST /api/reports/{id}/sms`
- `GET /api/sms/status/{message_id}`

## Cấu hình SMS

Lần chạy đầu tạo `backend/.env` từ `.env.example`. Mặc định `SMS_ENABLED=false`, vì vậy backend không gọi Twilio.

Khi đã có tài khoản Twilio, điền các biến sau vào `.env`:

```dotenv
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
SMS_ALERT_RECIPIENT=
```

Sau đó mới đổi:

```dotenv
SMS_ENABLED=true
```

Không commit file `.env`. Báo cáo, ảnh và AI không gọi Twilio và không phát sinh phí SMS. Chỉ endpoint `/sms`, sau khi frontend yêu cầu xác nhận rõ ràng, mới có thể gửi tin và phát sinh phí nhà cung cấp. Không dùng `114` hoặc đầu số khẩn cấp làm số kiểm thử.

## Dữ liệu

- SQLite mặc định: `backend/data/flood_rescue.db`
- Ảnh mặc định: `backend/data/uploads/`
- Ảnh tối đa: 10 MiB
- Loại ảnh: JPEG, PNG, WebP

Các đường dẫn này có thể đổi trong `.env`. Thư mục `data/`, `.venv/` và `.env` không được đưa vào Git.

