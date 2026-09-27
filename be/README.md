# Flood Rescue Mock Server (`be`)

Server giả lập (Mock Server) viết bằng Python (FastAPI) phục vụ tiếp nhận dữ liệu báo cáo cứu hộ từ ứng dụng Frontend Flutter ([`fe/app`](../fe/app/)).

> Chạy nhanh cả server + app (Linux/WSL/Windows) và dữ liệu demo: xem [`docs/huong_dan_chay_demo.md`](../docs/huong_dan_chay_demo.md) và [`scripts/demo/`](../scripts/demo/).

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

- **Web Dashboard điều phối**: [http://localhost:8000/](http://localhost:8000/)  
  Đăng nhập bằng tên điều phối viên (ghi vào nhật ký) và mật khẩu chung
  `RESCUE_DASHBOARD_PASSWORD` (mặc định `cuuho2026`, **đổi khi triển khai thật**).
  Chức năng: bản đồ (tô màu theo cụm/trạng thái, bản đồ nhiệt, hiện báo cáo đã kết thúc),
  xếp hạng cụm ưu tiên, hàng "Cần xem xét" cho báo cáo thiếu GPS (nhập vị trí trên bản
  đồ hoặc bằng tọa độ), bảng báo cáo có tìm kiếm/lọc/sắp xếp/phân trang và chọn nhiều,
  điều phối/hoàn tất/đóng báo cáo (có xác nhận, lý do, ghi chú, giao đội), quản lý đội
  cứu hộ, nhật ký thao tác từng báo cáo, thống kê thời gian phản ứng, báo cáo mới (nhãn,
  âm báo), xuất CSV/GeoJSON và tải bản sao lưu CSDL. Giao diện là HTML/CSS/JS tĩnh
  (`templates/dashboard.html`, `static/`), Leaflet đóng gói sẵn, không cần CDN.
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
  - `image`: Ảnh JPEG (hoặc PNG/WebP) chụp từ camera hoặc thư viện, tối đa 15 MB (tùy chọn, không bắt buộc nếu gửi text-only).
- `meta` được kiểm tra trước khi ghi (`400 INVALID_PAYLOAD` khi thiếu `id` hoặc sai kiểu). Gửi lại cùng
  `meta.id` chỉ bổ sung trường còn trống và gắn ảnh nếu chưa có ảnh, không ghi đè báo cáo.
- **Phản hồi**: HTTP `201 Created`
  ```json
  {
    "status": "ok",
    "message": "Báo cáo cứu hộ đã được tiếp nhận thành công",
    "id": "sos-1790472922834-3f9a0c1d2e4b",
    "imageUrl": "/uploads/sos-1790472922834-3f9a0c1d2e4b_8c1e2d3f4a5b.jpg",
    "receivedAt": "2026-09-22T09:30:00Z"
  }
  ```

### `GET /api/reports/status?ids=` (app)
- Trạng thái điều phối của tối đa 100 báo cáo; không cần đăng nhập.

### `POST /sync/messages`
- Batch store-and-forward của app. `UPDATE_RESCUE_STATUS` chỉ được xử lý khi request có phiên
  đăng nhập dashboard (cookie hoặc `Authorization: Bearer`), ngược lại `rejected UNAUTHENTICATED`.

### `POST /api/sms/inbound` (SMS gateway)
- Một điện thoại/dịch vụ SMS gateway chuyển tiếp tin tới tổng đài; bật bằng `RESCUE_SMS_GATEWAY_TOKEN`
  (gửi qua header `X-Gateway-Token` hoặc `?token=`).
- Tin `SOS|id:...` của app gộp vào báo cáo cùng id khi app đồng bộ sau; tin tự do thành báo cáo
  cần xác minh vị trí. Chi tiết: [`docs/contact_connect.md`](../docs/contact_connect.md#sms-gateway).
  ```bash
  curl -X POST "http://localhost:8000/api/sms/inbound" -H "X-Gateway-Token: $RESCUE_SMS_GATEWAY_TOKEN" \
       -H "Content-Type: application/json" -d '{"from": "0900000001", "text": "Nha toi bi ngap, co ba gia"}'
  ```

### API dashboard (cần đăng nhập)
Đăng nhập qua `POST /api/auth/login` `{"operator": "...", "password": "..."}`: server đặt
cookie HttpOnly và trả `token` để script gọi bằng `Authorization: Bearer <token>`.
Danh sách đầy đủ và mã lỗi: [`docs/contact_connect.md`](../docs/contact_connect.md#endpoint-dành-cho-dashboard-điều-phối).

| Endpoint | Mục đích |
|---|---|
| `GET /api/reports` | Lọc (`status`, `q`, `since`, `until`, `hasLocation`, `teamId`, `sendMode`, `label`, `vulnerable`, `source`, `ids`), `sort`, `page`/`pageSize` |
| `GET /api/reports/changes?since=&epoch=` | Chỉ báo cáo thay đổi (dashboard hỏi mỗi 5 s) |
| `POST /api/reports/manual` | Nhập báo cáo nhận qua điện thoại/tổng đài (nút "+ Báo cáo mới") |
| `GET /api/reports/{id}`, `GET /api/reports/{id}/history` | Chi tiết, nhật ký thao tác |
| `PATCH /api/reports/{id}/status`, `POST /api/reports/bulk-status` | Đổi trạng thái (một / nhiều báo cáo); `cancelled` cần `reason` |
| `PUT /api/reports/{id}/team`, `POST /api/reports/{id}/notes`, `PUT /api/reports/{id}/location` | Giao đội, ghi chú, vị trí thủ công |
| `GET /api/clusters` | Phân cụm + điểm ưu tiên (ETag); dữ liệu lớn thì tính nền, trả `stale: true` trong lúc chờ |
| `GET/POST /api/teams`, `PATCH /api/teams/{id}` | Đội cứu hộ |
| `GET /api/stats` | Số lượng theo trạng thái, thời gian phản ứng, lưu lượng 24 giờ |
| `GET /api/export?format=csv\|geojson` | Xuất theo bộ lọc (CSV có BOM cho Excel) |
| `GET /api/admin/backup` | Tải bản sao lưu SQLite nhất quán |
| `DELETE /api/reports` | Xóa toàn bộ dữ liệu, chỉ khi `RESCUE_ALLOW_WIPE=1` |

### Biến môi trường

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `RESCUE_DB_FILE`, `RESCUE_UPLOADS_DIR` | `data/rescue_reports.db`, `uploads` | DB và thư mục ảnh (tương đối theo `be/`) |
| `RESCUE_DASHBOARD_PASSWORD` | `cuuho2026` | Mật khẩu chung của điều phối viên |
| `RESCUE_SESSION_HOURS` | `12` | Thời hạn phiên đăng nhập |
| `RESCUE_COOKIE_SECURE` | tắt | Đặt `1` khi chạy sau HTTPS |
| `RESCUE_ALLOW_WIPE` | tắt | Đặt `1` để bật "Xóa toàn bộ dữ liệu" (chỉ demo) |
| `RESCUE_BACKUP_INTERVAL_MIN`, `RESCUE_BACKUP_DIR`, `RESCUE_BACKUP_KEEP` | `0` (tắt), `data/backups`, `24` | Sao lưu DB định kỳ |
| `RESCUE_TILE_URL`, `RESCUE_TILE_ATTRIBUTION` | OpenStreetMap | Tile bản đồ (đổi sang tile server nội bộ khi không có Internet) |
| `RESCUE_CORS_ORIGINS` | `*` | Origin được gọi API từ trình duyệt khác origin (không gửi cookie) |
| `RESCUE_MAX_IMAGE_MB` | `15` | Dung lượng ảnh tối đa của `POST /api/reports` |
| `RESCUE_SMS_GATEWAY_TOKEN` | trống (tắt) | Token của SMS gateway gọi `POST /api/sms/inbound` |
| `RESCUE_CLUSTER_SYNC_BUDGET_S`, `RESCUE_CLUSTER_MIN_INTERVAL_S` | `1`, `10` | Phân cụm lâu hơn ngưỡng thì chuyển sang tính nền, tối đa một lần mỗi khoảng |

---

## 5. Kiểm Thử Tự Động (Test Client)

Chạy script kiểm thử tự động để gửi dữ liệu mô phỏng từ FE lên server:

```powershell
cd be
.\.venv\Scripts\python.exe test_client.py
```

Unit test (chạy trên DB tạm, không đụng dữ liệu mẫu):

```bash
.venv/bin/python -m unittest test_contract test_cluster_service test_dashboard_api -v
```

---

## 6. Nơi Lưu Trữ Dữ Liệu

- **Ảnh đính kèm**: Lưu tại thư mục [`be/uploads/`](uploads/) và có thể truy cập qua URL `http://localhost:8000/uploads/<tên_ảnh>`.
- **Dữ liệu báo cáo**: SQLite tại [`be/data/rescue_reports.db`](data/rescue_reports.db) (dữ liệu mẫu đã commit). Đặt `RESCUE_DB_FILE` / `RESCUE_UPLOADS_DIR` để chạy trên DB riêng (`data/reports.json` là file cũ, không còn dùng).
