# BÁO CÁO NGHIÊN CỨU KHOA HỌC SINH VIÊN

## Hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI

**Tên tiếng Anh:** *An Edge AI–Based System for Multimodal Analysis and Clustering of Flood Rescue Events*  
**Đơn vị:** Trường Công Nghệ Thông Tin & Truyền Thông, Đại học Cần Thơ  
**Chủ nhiệm đề tài:** Lê Thị Ngọc Ảnh (B2303861)  
**Cán bộ hướng dẫn:** TS. Nguyễn Thanh Khoa (MSCB: 2995)  
**Thời gian thực hiện:** 03/2026 – 08/2026  
**Lĩnh vực:** Khoa học Kỹ thuật & Công nghệ  
**Loại hình:** Nghiên cứu ứng dụng

---

## Tóm tắt

Đề tài nghiên cứu hệ thống **phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI** nhằm giải quyết bối cảnh hạ tầng viễn thông gián đoạn/quá tải khi thiên tai xảy ra.

- **Vấn đề:** Hệ thống cứu hộ tập trung phụ thuộc Internet ổn định, dễ tê liệt khi bão lũ.
- **Giải pháp đề xuất:** Hệ thống lai gồm:
  - Ứng dụng di động Flutter tích hợp AI tại biên (offline).
  - MobileNetV3 (TensorFlow Lite) phân loại ảnh ngập lụt.
  - DistilBERT (ONNX Runtime) phân loại văn bản khẩn cấp.
  - Cơ chế truyền dữ liệu thích ứng (full payload hoặc metadata gọn nhẹ).
  - Backend FastAPI + DBSCAN/HDBSCAN + PostGIS + WebSocket.
- **Đóng góp chính:**
  1. Bộ dữ liệu cứu hộ bão lũ Việt Nam (ảnh + văn bản).
  2. Mô hình AI nhẹ, tinh chỉnh theo bối cảnh địa phương.
  3. Hệ thống vẫn hoạt động hiệu quả trong mạng yếu/offline.

**Từ khóa:** Edge AI, đa phương thức, phân cụm không gian, cứu hộ thiên tai, MobileNetV3, DistilBERT, DBSCAN, Flutter.

---

## 1. Tổng quan nghiên cứu

### 1.1 Tính cấp thiết

Việt Nam hằng năm chịu ảnh hưởng nặng của bão lũ; thông tin cầu cứu thường rời rạc, trùng lặp, khó xác thực và khó xử lý nhanh trong điều kiện mạng suy giảm. Đề tài đề xuất AI nhẹ chạy ngay trên thiết bị di động để:

1. Phân loại sơ bộ mức độ khẩn cấp tại nguồn.
2. Chỉ truyền dữ liệu thiết yếu khi mạng yếu.
3. Gom nhóm sự kiện trùng lặp để tối ưu điều phối cứu hộ.

### 1.2 Tình hình nghiên cứu

**Trong nước:**

- Ước lượng mực nước lũ từ ảnh mạng xã hội (Flood Level Prediction via Human Pose Estimation).
- Lập bản đồ nguy cơ lũ lụt bằng Deep Learning + GIS.

**Ngoài nước:**

- CrisisMMD, FloodNet (dữ liệu đa phương thức chuẩn).
- Multimodal Deep Learning cho phản ứng thiên tai.
- EmergencyNet (CNN nhẹ cho drone/IoT).

**Khoảng trống:** Chưa có giải pháp tích hợp trọn vòng đời gồm xử lý tại biên, truyền thích ứng, phân cụm không gian-thời gian, và chấm điểm ưu tiên theo bối cảnh Việt Nam.

### 1.3 Mục tiêu đề tài

- Thu thập, phân tích và gom nhóm thông tin cứu hộ (ảnh, văn bản, vị trí).
- Đánh giá mức độ khẩn cấp trong điều kiện mạng không ổn định.
- Hỗ trợ điều phối nguồn lực, rút ngắn thời gian phản ứng.

---

## 2. Kiến trúc hệ thống

### 2.1 Kiến trúc tổng quan (Hybrid)

Hệ thống gồm 4 tầng chính:

1. **Mobile App (Flutter):** AI tại biên chạy offline.
2. **Adaptive Transmission:** chuyển chế độ gửi dữ liệu theo chất lượng mạng.
3. **Backend (FastAPI):** tiếp nhận dữ liệu, phân cụm DBSCAN/HDBSCAN + PostGIS.
4. **Dashboard Web:** hiển thị bản đồ realtime qua WebSocket.

### 2.2 Cơ chế truyền dữ liệu thích ứng

- **Ngưỡng quyết định:** băng thông > 1 Mbps.
- **Mạng tốt:** gửi full payload ~2–5 MB (ảnh + text + GPS + AI result).
- **Mạng yếu/offline:** gửi metadata ~2–5 KB (JSON gọn); lưu hàng đợi cục bộ và đồng bộ lại khi mạng phục hồi.

### 2.3 Kiến trúc ứng dụng di động

5 tầng chính:

1. **Trình bày:** 6 màn hình (Trang chủ, Camera/Ảnh, Văn bản, Biểu mẫu cứu hộ, Lịch sử, Cài đặt).
2. **Nghiệp vụ:** 6 BLoC cho inference/sync/kết nối/lịch sử.
3. **AI Inference:** pipeline ảnh + pipeline văn bản.
4. **Dữ liệu:** SQLite/Hive, REST client, WebSocket client, Sync manager.
5. **Nền tảng:** camera, geolocator, connectivity, tối ưu pin.

### 2.4 Pipeline AI tại biên và điểm khẩn cấp

- **Pipeline ảnh:** Ảnh -> tiền xử lý (224x224, normalize) -> MobileNetV3 -> nhãn `none|low|high`.
- **Pipeline văn bản:** Text tiếng Việt -> tokenize -> DistilBERT -> nhãn `urgent|supplies|safe|irrelevant`.
- **Tổng hợp ưu tiên:**

\[
s = 0.4 \cdot v_{\text{image}} + 0.4 \cdot v_{\text{text}} + 0.2 \cdot c,\quad s \in [0,1]
\]

Trong đó:

- \(v_{\text{image}}\): điểm mức ngập từ mô hình ảnh.
- \(v_{\text{text}}\): điểm từ mô hình văn bản.
- \(c\): điểm ngữ cảnh (thời gian, mật độ báo cáo lân cận).

| Mức ưu tiên | Ngưỡng | Ý nghĩa |
|---|---|---|
| Đỏ | \(s > 0.7\) | Khẩn cấp, cần cứu hộ ngay |
| Vàng | \(0.4 \le s \le 0.7\) | Cần hỗ trợ, theo dõi/can thiệp |
| Xanh | \(s < 0.4\) | An toàn, chưa cần ưu tiên |

---

## 3. Bộ dữ liệu và mô hình AI

### 3.1 Dữ liệu hình ảnh

| Bộ dữ liệu | Kích thước | Nội dung | Xử lý bổ sung |
|---|---|---|---|
| FloodNet | ~2.3K ảnh | Ảnh UAV hậu lũ, nhãn semantic | Fine-tune theo địa hình Việt Nam |
| CrisisMMD | ~16K tweet | Ảnh + text mạng xã hội | Lọc nhãn flood, dịch text |
| Thu thập nội bộ | ~5K ảnh | Facebook/Zalo VN, bão lũ 2023–2024 | Gán nhãn thủ công |
| **Tổng** | **~23K** |  |  |

**Nhãn ảnh:** `none`, `low`, `high`.

### 3.2 Dữ liệu văn bản

| Bộ dữ liệu | Kích thước | Nội dung | Xử lý bổ sung |
|---|---|---|---|
| UIT-VSMEC | ~6.9K câu | Dữ liệu cảm xúc tiếng Việt | Điều chỉnh nhãn cứu hộ |
| Crawl mạng xã hội | ~10K câu | Facebook/Zalo bão lũ 2020–2024 | Làm sạch, chuẩn hóa Unicode |
| **Tổng** | **~17K** |  |  |

**Nhãn văn bản:**

- `urgent_rescue`: cầu cứu khẩn cấp.
- `need_supplies`: cần nhu yếu phẩm.
- `safe_update`: cập nhật an toàn.
- `irrelevant`: không liên quan cứu hộ.

### 3.3 Mô hình và tối ưu hóa

**Ảnh (MobileNetV3):**

- Kiến trúc gốc: MobileNetV3-Large pretrained.
- Transfer learning: fine-tune 2 lớp cuối.
- Quantization: INT8 -> TFLite.
- Kích thước: ~5 MB.
- Suy luận: <100 ms (thiết bị tầm trung).

**Văn bản (DistilBERT/PhoBERT distilled):**

- Fine-tune trên UIT-VSMEC + crawl.
- Dynamic quantization -> ONNX Runtime Mobile.
- Kích thước: ~65 MB.
- Suy luận: <200 ms.

**Pipeline triển khai mô hình:** Pretrained -> Fine-tune -> Đánh giá (Accuracy/F1) -> Quantization -> Chuyển đổi (TFLite/ONNX) -> Deploy mobile.

---

## 4. Thuật toán phân cụm sự kiện cứu hộ

### 4.1 Bài toán

Mục tiêu gom các báo cáo gần nhau để tránh trùng lặp điều phối:

- Cùng cụm nếu trong **bán kính 500 m** và **khung thời gian 2 giờ**.
- Độ ưu tiên cụm: \(\max(\text{urgency\_score})\).
- Giảm nhiễu và phân tán nguồn lực.

### 4.2 DBSCAN kết hợp PostGIS

**Lý do chọn DBSCAN:**

- Không cần biết trước số cụm.
- Bắt cụm hình dạng bất kỳ.
- Tự phát hiện nhiễu.

**Tham số chính:**

- \(\varepsilon = 500\) m.
- `min_samples = 2`.
- Truy vấn không gian: `ST_DWithin(point, 500m)` (PostGIS).

### 4.3 Luồng xử lý yêu cầu cứu hộ (9 bước)

1. Người dùng gửi ảnh + text + GPS.
2. AI ảnh phân loại mức ngập.
3. AI văn bản phân loại loại tin.
4. Tính điểm khẩn cấp \(s\).
5. Lưu cục bộ và kiểm tra mạng.
6. Mạng tốt -> gửi full payload 2–5 MB.
7. Mạng yếu/offline -> gửi metadata 2–5 KB, đồng bộ ảnh sau.
8. Backend phân cụm DBSCAN + PostGIS (500m/2h).
9. Dashboard cập nhật realtime qua WebSocket (2–5 giây).

---

## 5. Bộ công nghệ sử dụng

| Tầng | Công nghệ chính | Vai trò |
|---|---|---|
| Frontend | Flutter/Dart, HTML/CSS/JS, Leaflet.js/Mapbox | App di động + dashboard bản đồ |
| Edge AI | TensorFlow Lite, ONNX Runtime, MobileNetV3, DistilBERT/PhoBERT | Suy luận ảnh + văn bản trên thiết bị |
| Backend | Python 3.11, FastAPI, Uvicorn, scikit-learn | API, WebSocket, phân cụm |
| Dữ liệu | PostgreSQL, PostGIS, SQLite/Hive | Lưu trữ chính + offline mobile |
| Giao tiếp | REST API, WebSocket, JSON | Truyền dữ liệu và cập nhật realtime |
| DevOps | Git/GitHub, Docker, Google Colab | Quản lý mã nguồn, triển khai, huấn luyện |

---

## 6. Các module hệ thống (14 module)

| # | Module | Chức năng chính | Công nghệ |
|---|---|---|---|
| 1 | Camera & Ảnh | Thu thập ảnh, nén trước AI | Flutter camera/image_picker |
| 2 | AI phân loại ảnh | Phân loại `none/low/high` | TFLite, MobileNetV3 |
| 3 | Nhập văn bản | Nhập và tiền xử lý Unicode/tokenize | Flutter, Dart |
| 4 | AI phân loại văn bản | Phân loại 4 nhóm cứu hộ | ONNX Mobile, DistilBERT |
| 5 | Tính điểm khẩn cấp | Hợp nhất ảnh + text + GPS | Dart |
| 6 | Hàng đợi offline & Sync | Lưu khi mất mạng, retry đồng bộ | SQLite/Hive, Dart isolates |
| 7 | GPS | Lấy tọa độ, reverse geocoding | geolocator, geocoding |
| 8 | Giám sát kết nối | Theo dõi WiFi/4G/3G/offline | connectivity_plus |
| 9 | REST API Client | Gửi multipart, retry logic | Dio/http |
| 10 | Backend API Server | REST + WebSocket | Python, FastAPI, Uvicorn |
| 11 | Phân cụm không gian | DBSCAN + PostGIS realtime | scikit-learn, PostGIS |
| 12 | Cơ sở dữ liệu | Lưu sự kiện/cụm/người dùng | PostgreSQL, PostGIS |
| 13 | Dashboard & Bản đồ | Bản đồ realtime + quản trị | Leaflet.js, HTML/CSS/JS |
| 14 | Xác thực người dùng | Đăng ký/đăng nhập/JWT | FastAPI jose, secure_storage |

---

## 7. Phương pháp nghiên cứu và tiến độ

### 7.1 Phương pháp

1. Thu thập + gán nhãn dữ liệu (FloodNet, CrisisMMD, UIT-VSMEC, crawl VN).
2. Thiết kế kiến trúc hệ thống và CSDL không gian.
3. Huấn luyện/tinh chỉnh mô hình + quantization.
4. Phát triển ứng dụng Flutter và backend FastAPI.
5. Kiểm thử Accuracy/F1 trên validation.
6. Thực nghiệm trong điều kiện mạng yếu/offline.

### 7.2 Tiến độ thực hiện

| STT | Nội dung | Thời gian | Người thực hiện |
|---|---|---|---|
| 1 | Nghiên cứu tổng quan | 3–4/2026 | LTNA, NNQ |
| 2 | Xây dựng bộ dữ liệu | 3–4/2026 | LTNA, NHT |
| 3 | Thiết kế kiến trúc & CSDL | 3/2026 | NTT, CTH |
| 4 | Huấn luyện mô hình | 4–7/2026 | LTNA, NNQ |
| 5 | Tối ưu hóa mô hình | 4–7/2026 | NHT, CTH |
| 6 | Thuật toán phân cụm | 4–7/2026 | NTT, NHT |
| 7 | Ứng dụng di động | 6–7/2026 | NTT, CTH |
| 8 | Backend & Dashboard | 6–7/2026 | LTNA, NNQ |
| 9 | Thực nghiệm đánh giá | 8/2026 | NTT, NNQ |
| 10 | Viết báo cáo & công bố | 8/2026 | LTNA, NNQ |

Viết tắt: LTNA (Lê Thị Ngọc Ảnh), NNQ (Nguyễn Như Quỳnh), NTT (Nguyễn Thanh Trọng), NHT (Ngô Hưng Thịnh), CTH (Cao Tường Hưng).

---

## 8. Kết quả dự kiến và đánh giá

### 8.1 Sản phẩm dự kiến

1. Ứng dụng di động cứu hộ tích hợp Edge AI, chạy offline.
2. Dashboard web bản đồ realtime, có phân cụm ưu tiên.
3. Bộ mô hình MobileNetV3-TFLite + DistilBERT-ONNX tối ưu.
4. Bộ dữ liệu ảnh + văn bản cứu hộ bão lũ Việt Nam.

### 8.2 Chỉ tiêu đánh giá

| Chỉ tiêu | Mục tiêu |
|---|---|
| Accuracy mô hình ảnh | \(\ge 85\%\) |
| F1-score phân loại văn bản | \(\ge 80\%\) |
| Suy luận AI ảnh | <100 ms |
| Suy luận AI văn bản | <200 ms |
| Độ trễ end-to-end (mạng tốt) | <5 s |
| Kích thước gói metadata | <5 KB |
| Tỷ lệ đồng bộ thành công | \(\ge 95\%\) |

### 8.3 Tác động và lợi ích

- **Giáo dục:** tài liệu thực tiễn về Edge AI + Multimodal.
- **Khoa học:** chuyển dịch xử lý tập trung sang xử lý tại biên kết hợp phân cụm thông minh.
- **Kinh tế xã hội:** tăng tốc cứu hộ, giảm lãng phí nguồn lực.
- **Tổ chức dữ liệu:** tạo nền dữ liệu thiên tai Việt Nam cho nghiên cứu tiếp nối.

---

## 9. Kết luận

Đề tài đề xuất kiến trúc lai hỗ trợ cứu hộ bão lũ dựa trên Edge AI, giải quyết điểm nghẽn phụ thuộc kết nối mạng ổn định trong các hệ thống tập trung truyền thống.

Điểm nhấn:

1. AI offline trên thiết bị di động (MobileNetV3 + DistilBERT).
2. Truyền dữ liệu thích ứng (2–5 MB khi mạng tốt, 2–5 KB khi mạng yếu).
3. Phân cụm DBSCAN + PostGIS để giảm trùng lặp và ưu tiên cứu hộ.
4. Tinh chỉnh mô hình theo dữ liệu và ngữ cảnh Việt Nam.

---

## 10. Tài liệu tham khảo chính

1. Quan et al. (2020), *Flood Level Prediction via Human Pose Estimation from Social Media Images*.
2. Nguyen et al. (2022), *Flood susceptibility mapping in Quang Ngai province, Vietnam*.
3. Alam et al. (2018), *CrisisMMD: Multimodal Twitter Datasets from Natural Disasters*.
4. Rahnemoonfar et al. (2021), *FloodNet: Aerial Imagery Dataset for Post Flood Scene Understanding*.
5. Ofli et al. (2020), *Multimodal Deep Learning for Disaster Response*.
6. Kyrkou & Theocharides (2020), *EmergencyNet*.

---

## Phụ lục A. Thông tin nhóm nghiên cứu

| # | Họ và tên | MSSV – Lớp | Nhiệm vụ chính |
|---|---|---|---|
| 1 | Lê Thị Ngọc Ảnh | B2303861 – DI2396F1 | Tổng quan, dữ liệu, huấn luyện, Backend/Dashboard, báo cáo |
| 2 | Nguyễn Như Quỳnh | B2303777 – DI2396F1 | Tổng quan, huấn luyện, Backend/Dashboard, thực nghiệm, báo cáo |
| 3 | Nguyễn Thanh Trọng | B2305615 – DI2396F1 | Kiến trúc, CSDL, phân cụm, mobile, thực nghiệm |
| 4 | Ngô Hưng Thịnh | B2303904 – DI2396F2 | Dữ liệu, tối ưu mô hình, phân cụm |
| 5 | Cao Tường Hưng | B2303873 – DI2396F1 | Kiến trúc, tối ưu mô hình, mobile |

**Cán bộ hướng dẫn:** TS. Nguyễn Thanh Khoa (MSCB: 2995), Khoa CNTT&TT, ĐH Cần Thơ.

---

## Phụ lục B. Kinh phí thực hiện

| STT | Khoản chi | Kinh phí (đồng) | Nguồn |
|---|---|---:|---|
| 1 | Thù lao tham gia thực hiện đề tài | 12.100.000 | ĐHCT |
| 2 | Mua vật tư, nguyên liệu | 0 | -- |
| 3 | Văn phòng phẩm, in ấn | 175.000 | ĐHCT |
| 4 | Họp hội đồng đánh giá, nghiệm thu | 2.725.000 | ĐHCT |
|  | **Tổng cộng** | **15.000.000** | **ĐHCT** |

