# ĐẶC TẢ HỆ THỐNG V2 — REVIEW 2

**Dự án:** Hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI  
**Ngày cập nhật:** 2026-05-11  
**Phiên bản:** v2.1 (phục vụ Review 2)  
**Tham chiếu:** [Thuyết minh NCKH](./Thuyết%20minh%20NCKH.md) · [Review 1](./Review_1.md) · [Brainstorm](./Brainstorm_for_review_2.md)

---

## 1. Mục tiêu của Review 2

1. Chốt đặc tả chức năng cốt lõi ở mức có thể demo được.
2. Thể hiện rõ luồng xử lý trong điều kiện mạng mạnh / yếu / offline.
3. Chứng minh tính khả thi kỹ thuật của 3 khối: **Mobile Edge AI**, **Backend phân cụm**, **Dashboard thời gian thực**.
4. Trình bày bộ dataset đã chuẩn hóa và model có thể chạy inference.
5. Cung cấp bộ sơ đồ thiết kế: Use-case, Architecture, ERD.

---

## 2. Phạm vi hệ thống

### 2.1 In Scope

| # | Nội dung |
|---|---------|
| 1 | Thu thập dữ liệu cứu hộ: ảnh + văn bản + GPS từ Mobile App |
| 2 | Suy luận AI tại biên (offline): MobileNetV3 (TFLite) cho ảnh, DistilBERT/PhoBERT (ONNX) cho văn bản |
| 3 | Tính điểm khẩn cấp tổng hợp: `s = 0.4·v_image + 0.4·v_text + 0.2·c` |
| 4 | Truyền dữ liệu thích ứng theo chất lượng mạng (full payload / metadata gọn nhẹ) |
| 5 | Backend nhận dữ liệu, phân cụm không gian-thời gian (DBSCAN + PostGIS) |
| 6 | Dashboard bản đồ realtime với WebSocket |
| 7 | Hàng đợi offline và cơ chế đồng bộ lại tự động |

### 2.2 Out of Scope

- Triển khai vận hành thực tế ngoài môi trường thử nghiệm.
- Logic nghiệp vụ điều phối cứu hộ thực địa ở mức tổ chức.
- Dự báo khí tượng – thủy văn.

---

## 3. Tác nhân hệ thống

| Tác nhân | Nền tảng | Mô tả | Quyền chính |
|----------|----------|-------|-------------|
| Người bị nạn | Mobile App | Gửi yêu cầu cứu hộ | Tạo báo cáo, xem lịch sử gửi |
| Đội cứu hộ | Dashboard Web | Theo dõi sự kiện trên bản đồ | Xem bản đồ realtime, lọc theo mức ưu tiên/cụm |
| Quản trị viên | Dashboard Web | Quản lý hệ thống thử nghiệm | Quản lý cấu hình, người dùng, trạng thái hệ thống |

---

## 4. Danh sách Use Case

> Chi tiết đặc tả từng UC: xem [Review_2_UseCase.md](./Review_2_UseCase.md)

| Mã | Tên Use Case | Tác nhân | Kết quả đầu ra |
|----|-------------|----------|----------------|
| UC-01 | Đăng ký / Đăng nhập | Tất cả | Người dùng được xác thực, cấp JWT token |
| UC-02 | Gửi báo cáo cứu hộ | Người bị nạn | Sự kiện được ghi nhận kèm điểm khẩn cấp |
| UC-03 | Chụp / chọn ảnh ngập lụt | Người bị nạn | Ảnh sẵn sàng cho pipeline AI |
| UC-04 | Nhập văn bản cứu hộ | Người bị nạn | Text tiếng Việt đã tiền xử lý |
| UC-05 | Suy luận AI tại biên | Hệ thống AI (tự động) | Nhãn phân loại ảnh + văn bản + confidence |
| UC-06 | Tính điểm khẩn cấp | Hệ thống (tự động) | `urgency_score ∈ [0,1]` → mức đỏ/vàng/xanh |
| UC-07 | Gửi dữ liệu theo chế độ mạng | Người bị nạn | Full payload hoặc metadata được gửi |
| UC-08 | Đồng bộ khi có mạng | Hệ thống (tự động) | Dữ liệu hàng đợi được đẩy lên server |
| UC-09 | Xem lịch sử báo cáo | Người bị nạn | Danh sách báo cáo + trạng thái sync |
| UC-10 | Phân cụm sự kiện | Clustering Engine (tự động) | Cụm không gian-thời gian được tạo/cập nhật |
| UC-11 | Theo dõi bản đồ realtime | Đội cứu hộ / Admin | Bản đồ cập nhật sự kiện/cụm qua WebSocket |
| UC-12 | Quản lý sự kiện cứu hộ | Đội cứu hộ / Admin | Xem/lọc theo mức ưu tiên, cụm, trạng thái |
| UC-13 | Quản lý người dùng | Admin | Phân quyền, khóa/mở khóa tài khoản |
| UC-14 | Cấu hình hệ thống | Admin | Điều chỉnh tham số DBSCAN, trọng số score |

### Mối quan hệ chính giữa các Use Case

| Loại | UC gốc | UC liên quan | Mô tả |
|------|--------|-------------|-------|
| «include» | UC-02 | UC-03, UC-04, UC-05, UC-06, UC-07 | Gửi báo cáo bao gồm tất cả bước con |
| «extend» | UC-07 | UC-08 | Đồng bộ lại khi mạng yếu/offline → phục hồi |
| generalization | Admin | Đội cứu hộ | Admin kế thừa quyền xem bản đồ, quản lý sự kiện |

---

## 5. Yêu cầu chức năng

| Mã | Mô tả | Ưu tiên |
|----|-------|---------|
| FR-01 | App cho phép chụp ảnh hoặc chọn ảnh từ thư viện | Bắt buộc |
| FR-02 | App cho phép nhập mô tả văn bản tiếng Việt và lấy GPS | Bắt buộc |
| FR-03 | Ảnh được suy luận on-device → nhãn `none\|low\|medium\|high` | Bắt buộc |
| FR-04 | Văn bản suy luận on-device → nhãn `urgent_rescue\|need_supplies\|safe_update\|irrelevant` | Bắt buộc |
| FR-05 | App tính `urgency_score` tổng hợp (0–1) | Bắt buộc |
| FR-06 | Mạng tốt: gửi full payload (ảnh + text + GPS + AI result) | Bắt buộc |
| FR-07 | Mạng yếu/mất: gửi metadata JSON gọn nhẹ, lưu hàng đợi cục bộ | Bắt buộc |
| FR-08 | Retry/sync tự động khi kết nối phục hồi | Bắt buộc |
| FR-09 | Backend tiếp nhận dữ liệu qua REST API | Bắt buộc |
| FR-10 | Backend phân cụm DBSCAN (ε=500m, min_samples=2, time<2h) | Bắt buộc |
| FR-11 | Dashboard nhận cập nhật realtime qua WebSocket | Bắt buộc |
| FR-12 | Dashboard hiển thị bản đồ + bảng sự kiện theo mức ưu tiên (đỏ/vàng/xanh) | Bắt buộc |
| FR-13 | Xác thực JWT cho mobile và dashboard | Bắt buộc |
| FR-14 | Xem lịch sử báo cáo đã gửi trên mobile | Nên có |

---

## 6. Yêu cầu phi chức năng

| Mã | Chỉ tiêu | Mục tiêu |
|----|----------|----------|
| NFR-01 | Suy luận AI ảnh on-device | < 100 ms |
| NFR-02 | Suy luận AI văn bản on-device | < 200 ms |
| NFR-03 | Độ trễ end-to-end (mạng tốt) | < 5 giây |
| NFR-04 | Kích thước metadata khi mạng yếu | < 5 KB |
| NFR-05 | Tỷ lệ đồng bộ thành công từ hàng đợi | ≥ 95% |
| NFR-06 | Accuracy mô hình ảnh | ≥ 85% |
| NFR-07 | F1-score phân loại văn bản | ≥ 80% |
| NFR-08 | Kích thước model ảnh (TFLite) | ≤ 5 MB |
| NFR-09 | Kích thước model văn bản (ONNX) | ≤ 65 MB |

---

## 7. Đặc tả dữ liệu

### 7.1 Rescue Report (đầu vào từ mobile)

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `report_id` | UUID | Mã định danh duy nhất |
| `created_at` | timestamp | Thời điểm tạo |
| `user_id` | UUID | Mã người dùng |
| `name` | string | Tên người gửi |
| `phone` | string | Số điện thoại |
| `lat`, `lng` | float | Tọa độ GPS |
| `text_content` | text | Nội dung văn bản mô tả |
| `image_uri` | string | Đường dẫn ảnh (cục bộ hoặc đã upload) |
| `image_label` | enum | `none \| low \| high` |
| `text_label` | enum | `urgent_rescue \| need_supplies \| safe_update \| irrelevant` |
| `urgency_score` | float(0..1) | Điểm khẩn cấp tổng hợp |
| `network_mode` | enum | `full \| metadata` |
| `sync_status` | enum | `pending \| synced \| failed` |

### 7.2 Cluster Event (đầu ra backend)

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `cluster_id` | int | Mã cụm |
| `center_lat`, `center_lng` | float | Tâm cụm |
| `report_count` | int | Số báo cáo trong cụm |
| `max_urgency_score` | float | Điểm khẩn cấp cao nhất |
| `priority_level` | enum | `red \| yellow \| green` |
| `time_window_start` | timestamp | Thời điểm bắt đầu cụm |
| `time_window_end` | timestamp | Thời điểm kết thúc cụm |

### 7.3 Mức ưu tiên

| Mức | Ngưỡng | Ý nghĩa |
|-----|--------|---------|
| 🔴 Đỏ | s > 0.7 | Khẩn cấp, cần cứu hộ ngay |
| 🟡 Vàng | 0.4 ≤ s ≤ 0.7 | Cần hỗ trợ, theo dõi |
| 🟢 Xanh | s < 0.4 | An toàn, chưa cần ưu tiên |

---

## 8. Luồng nghiệp vụ cốt lõi (9 bước)

1. Người dùng nhập ảnh + văn bản + GPS trên mobile.
2. Pipeline AI ảnh: tiền xử lý (224×224, normalize) → MobileNetV3 → nhãn mức ngập.
3. Pipeline AI văn bản: tokenize tiếng Việt → DistilBERT → nhãn loại tin.
4. Tính `urgency_score = 0.4·v_image + 0.4·v_text + 0.2·context`.
5. Lưu cục bộ (SQLite/Hive) và kiểm tra băng thông.
6. **Mạng tốt (>1 Mbps):** gửi full payload ~2–5 MB.
7. **Mạng yếu/offline:** gửi metadata ~2–5 KB, lưu hàng đợi, đồng bộ ảnh sau.
8. Backend nhận dữ liệu → phân cụm DBSCAN + PostGIS (500m/2h).
9. Dashboard cập nhật realtime qua WebSocket (2–5 giây).

---

## 9. Tiêu chí nghiệm thu cho Review 2

| # | Tiêu chí | Minh chứng |
|---|---------|-----------|
| 1 | Tài liệu đặc tả v2 hoàn chỉnh | File này + sơ đồ thiết kế |
| 2 | Bộ dataset đã chuẩn hóa | Báo cáo thống kê + label schema |
| 3 | Model chạy được demo inference | Notebook + kết quả số liệu |
| 4 | Thiết kế hệ thống | Use-case diagram, Architecture diagram, ERD |
| 5 | Demo luồng hoàn chỉnh | Mobile → Backend → Dashboard |
| 6 | Trình bày rõ giới hạn và hướng phát triển | Slide review |
