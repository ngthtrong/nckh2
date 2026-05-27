# 📋 TỔNG QUAN DỰ ÁN NGHIÊN CỨU KHOA HỌC SINH VIÊN

> **Cập nhật lần cuối:** 2026-05-25  
> **Nguồn tham chiếu:** [Thuyết minh NCKH](./Thuyết%20minh%20NCKH.md) · [Review 2 Meeting Note](./r2/Review_2_FINAL_MEETING_NOTE.md)

---

## 1. THÔNG TIN CHUNG

| Mục | Nội dung |
|-----|----------|
| **Tên đề tài** | Hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI |
| **Tên tiếng Anh** | An Edge AI–Based System for Multimodal Analysis and Clustering of Flood Rescue Events |
| **Đơn vị** | Trường CNTT&TT, Đại học Cần Thơ |
| **GVHD** | TS. Nguyễn Thanh Khoa (MSCB: 2995) |
| **Thời gian** | 03/2026 – 08/2026 (6 tháng) |
| **Kinh phí** | 15.000.000 VNĐ (ĐHCT cấp) |
| **Lĩnh vực** | Công nghệ thông tin và chuyển đổi số |
| **Loại hình** | Nghiên cứu ứng dụng |

### Nhóm nghiên cứu (5 thành viên)

| # | Họ và tên | MSSV | Viết tắt | Vai trò chính |
|---|-----------|------|----------|---------------|
| 1 | Lê Thị Ngọc Ảnh | B2303861 | LTNA | **Chủ nhiệm** — Tổng quan, dataset, huấn luyện model, Backend/Dashboard, báo cáo |
| 2 | Nguyễn Như Quỳnh | B2303777 | NNQ | Huấn luyện model, Backend/Dashboard, thực nghiệm, báo cáo |
| 3 | Nguyễn Thanh Trọng | B2305615 | NTT | Kiến trúc hệ thống, CSDL, phân cụm, mobile app, thực nghiệm |
| 4 | Ngô Hưng Thịnh | B2303904 | NHT | Dataset, tối ưu model, phân cụm |
| 5 | Cao Tường Hưng | B2303873 | CTH | Kiến trúc, tối ưu model, mobile app |

---

## 2. BÀI TOÁN VÀ GIẢI PHÁP

### 2.1 Vấn đề cần giải quyết

- Khi bão lũ xảy ra, **hạ tầng viễn thông bị gián đoạn/quá tải**
- Thông tin cầu cứu từ người dân qua MXH rời rạc, trùng lặp, khó kiểm chứng
- Hệ thống cứu hộ hiện tại **phụ thuộc Internet ổn định** → tê liệt khi mất mạng
- Thiếu cơ chế **gom nhóm sự kiện trùng lặp** và **ưu tiên cứu hộ** theo mức độ khẩn cấp

### 2.2 Giải pháp đề xuất — Hệ thống lai (Hybrid)

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  📱 Mobile App   │────▶│  🖥️ Backend Server │────▶│  🗺️ Dashboard Web    │
│  (Flutter+EdgeAI)│     │  (FastAPI+Louvain)│     │  (Leaflet+WebSocket)│
│  Offline-first   │     │  Phân cụm KG-TG   │     │  Bản đồ realtime    │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
```

1. **Mobile App** — AI chạy offline trên điện thoại, phân loại ảnh + văn bản ngay tại thiết bị
2. **Backend** — Nhận dữ liệu, phân cụm sự kiện theo không gian-thời gian
3. **Dashboard** — Bản đồ realtime hiển thị cụm sự kiện theo mức ưu tiên

### 2.3 Đóng góp khoa học chính

1. Bộ dữ liệu cứu hộ bão lũ đặc thù Việt Nam (ảnh + văn bản)
2. AI nhẹ triển khai trên thiết bị biên, hoạt động offline
3. Cơ chế truyền dữ liệu thích ứng (full payload khi mạng tốt / metadata khi mạng yếu)
4. **⭐ MỚI:** Công thức tính mức độ khẩn cấp dựa trên phân cụm community detection + trọng số ngữ cảnh

---

## 3. KIẾN TRÚC KỸ THUẬT

### 3.1 Tech Stack

| Tầng | Công nghệ | Vai trò |
|------|-----------|---------|
| Mobile | Flutter/Dart | App di động cross-platform |
| Edge AI | TFLite (MobileNetV3), ONNX (DistilBERT/PhoBERT) | Suy luận on-device |
| Backend | Python 3.11+, FastAPI, Uvicorn | API + WebSocket + phân cụm |
| Database | PostgreSQL + PostGIS, SQLite/Hive | Server DB + offline mobile |
| Dashboard | HTML/CSS/JS, Leaflet.js | Bản đồ realtime |
| DevOps | Git/GitHub, Docker, Google Colab | Quản lý mã nguồn, training |

### 3.2 Dataset & Model

**Dữ liệu ảnh (~23K ảnh):** FloodNet + CrisisMMD + thu thập VN → 3 nhãn: `none | low | high`

**Dữ liệu văn bản (~17K câu):** UIT-VSMEC + crawl MXH VN → 4 nhãn: `urgent_rescue | need_supplies | safe_update | irrelevant`

**Model AI:**
| Model | Kiến trúc | Format | Kích thước | Latency mục tiêu |
|-------|-----------|--------|------------|-------------------|
| Ảnh | MobileNetV3-Large | TFLite INT8 | ≤ 5 MB | < 100 ms |
| Văn bản | DistilBERT/PhoBERT | ONNX | ≤ 65 MB | < 200 ms |

### 3.3 Hệ thống 14 Module

| # | Module | Tầng | Trạng thái |
|---|--------|------|------------|
| 1 | Camera & Ảnh | Mobile | ⬜ Chưa |
| 2 | AI phân loại ảnh (MobileNetV3) | Mobile | 🔄 Đang nghiên cứu |
| 3 | Nhập & xử lý văn bản | Mobile | ⬜ Chưa |
| 4 | AI phân loại văn bản (DistilBERT) | Mobile | 🔄 Đang nghiên cứu |
| 5 | Tính điểm khẩn cấp | Mobile | 🔄 Đang thiết kế lại |
| 6 | Hàng đợi Offline & Sync | Mobile | ⬜ Chưa |
| 7–9 | GPS, Giám sát mạng, REST Client | Mobile | ⬜ Chưa |
| 10 | Backend API Server | Server | ⬜ Chưa |
| 11 | Phân cụm không gian | Server | 🔄 Chuyển sang Louvain |
| 12 | Cơ sở dữ liệu | Server | ⬜ Chưa |
| 13 | Dashboard & Bản đồ | Web | ⬜ Chưa |
| 14 | Xác thực người dùng | Cross | ⬜ Chưa |

---

## 4. TIẾN ĐỘ THỰC HIỆN

### 4.1 Timeline tổng thể (03/2026 – 08/2026)

```
 03/2026    04/2026    05/2026    06/2026    07/2026    08/2026
 ├──────────┼──────────┼──────────┼──────────┼──────────┤
 │ Tổng quan│ Huấn luyện model + Phân cụm   │ App+Web  │ Test+BC │
 │ Dataset  │ Tối ưu model                   │          │         │
 │ Kiến trúc│                                │          │         │
 ├──R1──────┼────R2────┤                     │          │         │
                        ▲ HIỆN TẠI (25/05)
```

### 4.2 Review 1 (03-04/2026) — ✅ Hoàn thành

- ✅ Thuyết minh đề tài
- ✅ Nghiên cứu tổng quan
- ✅ Xác định kiến trúc hệ thống hybrid
- ✅ Lựa chọn tech stack và model AI

### 4.3 Review 2 (09-12/05/2026) — ✅ Hoàn thành (một phần)

**Đã làm được:**
- ✅ Đặc tả hệ thống v2 (14 UC, 14 FR, 9 NFR)
- ✅ Tài liệu use case chi tiết (14 UC)
- ✅ Tài liệu module chi tiết (14 module)
- ✅ Dataset & Model report
- ✅ Sơ đồ kiến trúc (4 diagrams: system, mobile, tech stack, sequence)
- ✅ Kế hoạch thực hiện + phân công

**Chưa hoàn thành:**
- ❌ ERD / Class diagram
- ❌ Demo inference chạy được
- ❌ Demo end-to-end (mobile → backend → dashboard)
- ❌ Slide review

### 4.4 ⭐ QUYẾT ĐỊNH QUAN TRỌNG TỪ BUỔI HỌP GVHD

> Buổi họp với GVHD đã **thay đổi đáng kể hướng đi**. Nghiên cứu được chia thành **2 phần song song**:

#### PHẦN 1: Viết bài báo khoa học (ƯU TIÊN CAO — làm trước)

Tập trung vào **phân cụm community detection** và **công thức tính mức độ khẩn cấp**:

1. **Chuyển từ DBSCAN → Louvain Algorithm** (hoặc thuật toán community detection khác, sẽ chốt sau khi thực thi)
2. **Xây dựng đồ thị có trọng số:**
   - Mỗi sự kiện cứu hộ = 1 node (GPS, thời gian, thông tin người gửi, tag mức ngập, tag khẩn cấp)
   - Liên kết giữa các sự kiện gần nhau (ví dụ: trong bán kính 1km)
   - Trọng số dựa trên khoảng cách địa lý, nội dung tương đồng
3. **Đề xuất công thức tính mức độ khẩn cấp** hoàn chỉnh:
   - Điểm từ AI (ảnh + văn bản)
   - Biến ngữ cảnh: thời gian gửi, mật độ vị trí gửi tại thời điểm đó
   - Mật độ cụm (community) càng cao → khẩn cấp càng cao
4. **Sử dụng bộ dữ liệu mô phỏng** (mỗi sự kiện: thời gian, GPS, thông tin người gửi, tag ngập lụt, tag khẩn cấp)
5. **Tìm bài báo liên quan:** lũ lụt, community detection, đồ thị có trọng số

#### PHẦN 2: Hoàn thiện đề tài + Báo cáo hội đồng trường

1. Hoàn thiện dataset ảnh ngập lụt
2. Lựa chọn và training model nhận diện ảnh ngập lụt
3. Tìm hiểu model/phương thức gán nhãn cho ngôn ngữ tự nhiên (tiếng Việt)
4. **Điện toán biên:** MobileNetV3, giải quyết bài toán biên → dữ liệu nhỏ → gửi hết

---

## 5. CÔNG VIỆC TIẾP THEO

### 5.1 🔴 Ưu tiên CAO — Bài báo khoa học

| # | Công việc | Ghi chú |
|---|-----------|---------|
| 1 | Tìm hiểu thuật toán Louvain — cài đặt thử, chạy demo | Cốt lõi của bài báo |
| 2 | Tạo bộ dữ liệu mô phỏng cho phân cụm | Thời gian, GPS, tag ngập, tag khẩn cấp |
| 3 | Xây dựng đồ thị có trọng số từ dữ liệu mô phỏng | Gán trọng số theo khoảng cách |
| 4 | Thiết kế + lý giải công thức trọng số | Tại sao trọng số A > B? |
| 5 | Tìm kiếm bài báo khoa học liên quan | Lũ lụt + community + weighted graph |
| 6 | Viết bài báo | Càng sớm càng tốt |

### 5.2 🟡 Ưu tiên TRUNG BÌNH — Sản phẩm

| # | Công việc | Trạng thái |
|---|-----------|------------|
| 1 | Hoàn thiện dataset ảnh ngập lụt VN | 🔄 Đang làm |
| 2 | Training model MobileNetV3 cho ảnh ngập | ⬜ Chưa |
| 3 | Tìm hiểu model NLP cho tiếng Việt | ⬜ Chưa |
| 4 | Triển khai Edge AI trên mobile | ⬜ Chưa |
| 5 | Xây dựng Backend API (FastAPI) | ⬜ Chưa |
| 6 | Xây dựng Dashboard bản đồ | ⬜ Chưa |
| 7 | Xây dựng Mobile App (Flutter) — đơn giản | ⬜ Chưa |

### 5.3 🟢 Tài liệu cần bổ sung

- [ ] ERD / Class diagram
- [ ] Sequence Diagram chi tiết
- [ ] Component Diagram
- [ ] Thiết kế database schema

---

## 6. THAY ĐỔI SO VỚI KẾ HOẠCH BAN ĐẦU

| Hạng mục | Ban đầu (R1-R2) | Sau họp GVHD |
|----------|-----------------|--------------|
| **Thuật toán phân cụm** | DBSCAN/HDBSCAN | **Louvain** (community detection) |
| **Trọng tâm** | Hệ thống end-to-end | **Bài báo khoa học** (ưu tiên) + Hệ thống |
| **Công thức khẩn cấp** | `s = 0.4·img + 0.4·text + 0.2·ctx` | Phức tạp hơn, dựa trên mật độ cụm |
| **Dữ liệu phân cụm** | Dữ liệu thực | **Dữ liệu mô phỏng** trước |
| **App mobile** | Nhiều tính năng | **Đơn giản** — tập trung nghiên cứu |

---

## 7. CẤU TRÚC THƯ MỤC

```
nckh2/
├── docs/
│   ├── Thuyết minh NCKH.md              ← Đề cương gốc
│   ├── Brainstorm_for_review_2.md        ← Brainstorm
│   ├── PROJECT_OVERVIEW.md               ← ⭐ FILE NÀY
│   ├── r1/
│   │   └── Review_1.md                   ← Báo cáo R1
│   ├── r2/
│   │   ├── Review_2_FINAL_MEETING_NOTE.md ← ⭐ Ghi chú họp GVHD
│   │   ├── Review_2_Spec.md              ← Đặc tả v2
│   │   ├── Review_2_Plan.md              ← Kế hoạch R2
│   │   ├── Review_2_Modules.md           ← 14 module
│   │   ├── Review_2_Dataset_Model.md     ← Dataset & Model
│   │   ├── Review_2_UseCase.md           ← 14 use case
│   │   └── Review_2_Index.md             ← Mục lục R2
│   └── r3/
│       └── r3-req.md                     ← (trống)
├── diagrams/                             ← 4 sơ đồ kiến trúc (Mermaid + PlantUML + PNG)
└── .git/
```

---

## 8. SẢN PHẨM CUỐI CÙNG CẦN GIAO

| # | Sản phẩm | Trạng thái |
|---|----------|------------|
| 1 | **Bài báo khoa học** (⭐ MỚI, ưu tiên) | ⬜ Chưa |
| 2 | Ứng dụng di động cứu hộ tích hợp Edge AI | ⬜ Chưa |
| 3 | Website Dashboard bản đồ realtime | ⬜ Chưa |
| 4 | Bộ mô hình AI đã huấn luyện + tối ưu | ⬜ Chưa |
| 5 | Quyển báo cáo tổng kết | ⬜ Chưa |
| 6 | Bản tin + Báo cáo tóm tắt | ⬜ Chưa |
| 7 | Video demo (≤ 2 phút) | ⬜ Chưa |

---

> **Ghi chú:** File này là tài liệu sống (living document), nên được cập nhật sau mỗi buổi họp nhóm hoặc họp GVHD.
