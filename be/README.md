# Flood Rescue Mock Server (`be`)

Server giả lập (Mock Server) viết bằng Python (FastAPI) phục vụ tiếp nhận dữ liệu báo cáo cứu hộ từ ứng dụng Frontend Flutter ([`fe/app`](../fe/app/)).

---

## 1. Khởi Động Server

### Cách 1: Dùng script tiện ích (khuyến nghị trên Windows)

- **PowerShell**:
  ```powershell
  cd be
  .\run.ps1
  ```
- **CMD**:
  ```cmd
  cd be
  run.bat
  ```

### Cách 2: Khởi chạy thủ công bằng venv

```powershell
cd be
.\.venv\Scripts\Activate.ps1
python main.py
```

Server sẽ lắng nghe trên cổng `8000` tại tất cả interface mạng (`0.0.0.0:8000`).

---

## 2. Các Địa Chỉ Truy Cập

- **Web Dashboard Giám Sát**: [http://localhost:8000/](http://localhost:8000/)  
  *(Hiển thị danh sách báo cáo, nạn nhân, tọa độ GPS, xem ảnh và JSON chi tiết theo thời gian thực)*
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Kiểm tra Probe**: [http://localhost:8000/probe](http://localhost:8000/probe)

---

## 3. Cấu Hình Kết Nối Từ Frontend Flutter (`fe/app`)

Tùy vào môi trường chạy Flutter app, cấu hình `kServerBaseUrl` trong file [`fe/app/lib/config.dart`](../fe/app/lib/config.dart):

1. **Android Emulator**:
   ```dart
   const String kServerBaseUrl = 'http://10.0.2.2:8000';
   ```
2. **Windows Desktop App**:
   ```dart
   const String kServerBaseUrl = 'http://localhost:8000';
   ```
3. **Điện thoại Android thật qua Wi-Fi / LAN**:
   ```dart
   // Thay bằng IP mạng LAN của máy tính đang chạy server (kiểm tra bằng ipconfig)
   const String kServerBaseUrl = 'http://192.168.1.xxx:8000';
   ```

---

## 4. API Endpoints Chi Tiết

### `GET /probe`
- **Mục đích**: Đo throughput tốc độ mạng trước khi gửi báo cáo (`measureKbps()`).
- **Phản hồi**: HTTP `200`, trả về đúng **65,536 bytes (64 KB)** payload nhị phân.

### `POST /api/reports`
- **Mục đích**: Nhận dữ liệu báo cáo cứu hộ.
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `meta`: Chuỗi JSON (`RescueRecord`) chứa thông tin báo cáo.
  - `image`: File ảnh JPEG chụp từ camera hoặc thư viện (tùy chọn, không bắt buộc nếu gửi text-only).
- **Phản hồi**: HTTP `201 Created`
  ```json
  {
    "status": "ok",
    "message": "Báo cáo cứu hộ đã được tiếp nhận thành công",
    "id": "rec_xxx",
    "imageUrl": "/uploads/rec_xxx.jpg",
    "receivedAt": "2026-09-22T09:30:00.000000"
  }
  ```

### `GET /api/reports`
- Lấy danh sách toàn bộ báo cáo đã lưu.

### `GET /api/reports/{id}`
- Lấy thông tin chi tiết của một báo cáo.

### `DELETE /api/reports`
- Xóa toàn bộ dữ liệu báo cáo (dùng để reset môi trường test).

---

## 5. Kiểm Thử Tự Động (Test Client)

Chạy script kiểm thử tự động để gửi dữ liệu mô phỏng từ FE lên server:

```powershell
cd be
.\.venv\Scripts\python.exe test_client.py
```

---

## 6. Nơi Lưu Trữ Dữ Liệu

- **Ảnh đính kèm**: Lưu tại thư mục [`be/uploads/`](uploads/) và có thể truy cập qua URL `http://localhost:8000/uploads/<tên_ảnh>`.
- **Dữ liệu JSON**: Lưu tại [`be/data/reports.json`](data/reports.json).
