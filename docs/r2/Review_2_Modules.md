# CHI TIẾT MODULE HỆ THỐNG — REVIEW 2

**Tham chiếu:** [Đặc tả v2](./Review_2_Spec.md) · [Kiến trúc](../architecture_design.md)

---

## 1. Tổng quan 14 Module

| # | Module | Tầng | Công nghệ chính |
|---|--------|------|-----------------|
| 1 | Camera & Ảnh | Mobile | Flutter camera/image_picker |
| 2 | AI phân loại ảnh | Mobile – Edge AI | TFLite, MobileNetV3 |
| 3 | Nhập & xử lý văn bản | Mobile | Flutter, Dart |
| 4 | AI phân loại văn bản | Mobile – Edge AI | ONNX Runtime, DistilBERT/PhoBERT |
| 5 | Tính điểm khẩn cấp | Mobile | Dart |
| 6 | Hàng đợi offline & Sync | Mobile | SQLite/Hive, Dart isolates |
| 7 | GPS & vị trí | Mobile | geolocator, geocoding |
| 8 | Giám sát kết nối | Mobile | connectivity_plus |
| 9 | REST API Client | Mobile | Dio/http |
| 10 | Backend API Server | Server | FastAPI, Uvicorn |
| 11 | Phân cụm không gian | Server | scikit-learn, PostGIS |
| 12 | Cơ sở dữ liệu | Server | PostgreSQL, PostGIS |
| 13 | Dashboard & Bản đồ | Web | Leaflet.js, HTML/CSS/JS |
| 14 | Xác thực người dùng | Cross | FastAPI jose, secure_storage |

---

## 2. Chi tiết từng Module

### Module 1: Camera & Ảnh
- **Chức năng:** Thu thập ảnh từ camera hoặc thư viện, nén trước khi xử lý AI.
- **Input:** Ảnh thô từ camera/gallery.
- **Output:** Ảnh đã nén, sẵn sàng cho pipeline AI.
- **Phụ trách:** NTT, CTH.

### Module 2: AI phân loại ảnh (on-device)
- **Chức năng:** Phân loại ảnh ngập lụt thành 3 mức: `none | low | high`.
- **Pipeline:** Ảnh → resize 224×224 → normalize → MobileNetV3 (TFLite INT8) → nhãn + confidence.
- **Chỉ tiêu:** < 100ms inference, model ≤ 5 MB.
- **Phụ trách:** LTNA, NNQ, NHT, CTH.

### Module 3: Nhập & xử lý văn bản
- **Chức năng:** Giao diện nhập tin nhắn tiếng Việt + tiền xử lý (chuẩn hóa Unicode, loại bỏ ký tự đặc biệt, tokenization).
- **Xử lý đặc biệt:** Viết tắt, viết sai chính tả, thiếu ký tự (ngữ cảnh khẩn cấp).
- **Phụ trách:** NTT, CTH.

### Module 4: AI phân loại văn bản (on-device)
- **Chức năng:** Phân loại tin nhắn thành 4 nhóm: `urgent_rescue | need_supplies | safe_update | irrelevant`.
- **Pipeline:** Text → tokenize → DistilBERT/PhoBERT distilled (ONNX) → nhãn + confidence.
- **Chỉ tiêu:** < 200ms inference, model ≤ 65 MB.
- **Phụ trách:** LTNA, NNQ, NHT, CTH.

### Module 5: Tính điểm khẩn cấp
- **Công thức:** `s = 0.4 × v_image + 0.4 × v_text + 0.2 × c`
- **Ngữ cảnh (c):** Thời gian trong ngày, mật độ báo cáo lân cận.
- **Output:** `urgency_score ∈ [0, 1]` → mức ưu tiên đỏ/vàng/xanh.
- **Phụ trách:** NTT, CTH.

### Module 6: Hàng đợi Offline & Đồng bộ
- **Chức năng:** Lưu dữ liệu cục bộ khi mất mạng, tự động đồng bộ khi mạng phục hồi.
- **Cơ chế:** Exponential backoff retry, 2 chế độ gửi (full/compact).
- **Phụ trách:** NTT, CTH.

### Module 7–9: GPS, Giám sát mạng, REST Client
- **GPS:** Lấy tọa độ + reverse geocoding, tối ưu pin.
- **Giám sát mạng:** Kiểm tra WiFi/4G/3G/2G/offline, đo băng thông thực tế, ngưỡng quyết định > 1 Mbps.
- **REST Client:** Multipart upload (ảnh), JSON request (metadata), retry logic.
- **Phụ trách:** NTT, CTH.

### Module 10: Backend API Server
- **Chức năng:** REST API + WebSocket server.
- **Endpoints chính:**
  - `POST /api/rescue-events` — nhận full payload
  - `POST /api/rescue-events/compact` — nhận metadata gọn nhẹ
  - `PUT /api/rescue-events/{id}/media` — upload ảnh bổ sung
  - `GET /api/clusters` — lấy danh sách cụm
  - `WS /ws/events` — cập nhật realtime
- **Phụ trách:** LTNA, NNQ.

### Module 11: Phân cụm không gian
- **Thuật toán:** DBSCAN (ε=500m, min_samples=2) + PostGIS `ST_DWithin`.
- **Ràng buộc thời gian:** Các báo cáo trong cùng khung 2 giờ.
- **Ưu tiên cụm:** `max(urgency_score)` của các báo cáo trong cụm.
- **Phụ trách:** NTT, NHT.

### Module 12: Cơ sở dữ liệu
- **Công nghệ:** PostgreSQL + PostGIS.
- **Bảng chính:** users, rescue_reports, clusters, cluster_reports.
- **Phụ trách:** NTT, CTH.

### Module 13: Dashboard & Bản đồ
- **Chức năng:** Bản đồ realtime + bảng quản lý sự kiện.
- **Hiển thị:** Marker theo mã màu (đỏ/vàng/xanh), popup chi tiết cụm.
- **Cập nhật:** WebSocket push mỗi 2–5 giây.
- **Phụ trách:** LTNA, NNQ.

### Module 14: Xác thực người dùng
- **Chức năng:** Đăng ký/đăng nhập JWT token-based.
- **Mobile:** flutter_secure_storage.
- **Server:** python-jose JWT.
- **Phụ trách:** LTNA, NNQ.

---

## 3. Bộ công nghệ tổng hợp

| Tầng | Công nghệ | Vai trò |
|------|-----------|---------|
| Frontend Mobile | Flutter/Dart | App di động cross-platform |
| Frontend Web | HTML/CSS/JS, Leaflet.js/Mapbox | Dashboard bản đồ |
| Edge AI | TensorFlow Lite, ONNX Runtime Mobile | Suy luận on-device |
| AI Models | MobileNetV3, DistilBERT/PhoBERT | Phân loại ảnh + văn bản |
| Backend | Python 3.11+, FastAPI, Uvicorn | API + WebSocket + phân cụm |
| Database | PostgreSQL, PostGIS, SQLite/Hive | Server DB + offline mobile |
| Communication | REST API, WebSocket, JSON | Truyền dữ liệu |
| DevOps | Git/GitHub, Docker, Google Colab | Quản lý mã nguồn, training |
