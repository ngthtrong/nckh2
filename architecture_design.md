# THIẾT KẾ KIẾN TRÚC HỆ THỐNG
## Hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI

---

### 1. Sơ đồ kiến trúc tổng quan hệ thống

#### 1.1. Mermaid

```mermaid
graph TB
    subgraph MOBILE["📱 ỨNG DỤNG DI ĐỘNG (Flutter/Dart)"]
        direction TB
        CAM["📷 Camera / Thư viện ảnh"]
        TXT["📝 Nhập văn bản cứu hộ"]
        GPS["📍 Dịch vụ GPS"]
        
        subgraph AI_ENGINE["🧠 Nhân xử lý AI tại biên"]
            IMG_AI["Phân loại ảnh ngập lụt<br/>(MobileNetV3 - TFLite)"]
            TXT_AI["Phân loại văn bản khẩn cấp<br/>(DistilBERT - ONNX)"]
            SCORE["Tính điểm khẩn cấp tổng hợp"]
        end
        
        LOCAL_DB["💾 Lưu trữ cục bộ<br/>(SQLite/Hive)"]
        SYNC["🔄 Quản lý đồng bộ<br/>& Hàng đợi offline"]
        NET_MON["📶 Giám sát kết nối mạng"]
    end

    subgraph SERVER["🖥️ MÁY CHỦ BACKEND (Python/FastAPI)"]
        direction TB
        API["🔌 REST API Server"]
        WS["🔗 WebSocket Server"]
        CLUSTER["📊 Phân cụm không gian<br/>(DBSCAN/HDBSCAN)"]
    end

    subgraph DATABASE["🗄️ CƠ SỞ DỮ LIỆU"]
        PG["PostgreSQL + PostGIS"]
    end

    subgraph DASHBOARD["🌐 BẢNG ĐIỀU KHIỂN WEB"]
        MAP["🗺️ Bản đồ thời gian thực<br/>(Leaflet.js / Mapbox)"]
        PANEL["📋 Bảng quản lý sự kiện cứu hộ"]
    end

    CAM --> IMG_AI
    TXT --> TXT_AI
    IMG_AI --> SCORE
    TXT_AI --> SCORE
    GPS --> SCORE
    SCORE --> SYNC
    SCORE --> LOCAL_DB

    NET_MON -->|"Kiểm tra<br/>kết nối"| SYNC

    SYNC -->|"✅ Mạng tốt:<br/>Gửi đầy đủ dữ liệu<br/>(ảnh + text + GPS + kết quả AI)"| API
    SYNC -->|"⚠️ Mạng yếu/mất:<br/>Gửi metadata JSON gọn nhẹ<br/>(vài KB: kết quả AI + GPS + điểm khẩn cấp)"| API

    LOCAL_DB -->|"Đồng bộ lại<br/>khi có mạng"| SYNC

    API --> CLUSTER
    API --> PG
    CLUSTER --> PG
    
    WS -->|"Cập nhật<br/>thời gian thực"| MAP
    PG --> WS
    PG --> MAP
    PG --> PANEL

    style MOBILE fill:#1a237e,stroke:#7c4dff,color:#fff,stroke-width:2px
    style AI_ENGINE fill:#4a148c,stroke:#e040fb,color:#fff,stroke-width:2px
    style SERVER fill:#004d40,stroke:#1de9b6,color:#fff,stroke-width:2px
    style DATABASE fill:#e65100,stroke:#ff9100,color:#fff,stroke-width:2px
    style DASHBOARD fill:#01579b,stroke:#40c4ff,color:#fff,stroke-width:2px
```

**Chú thích (Legend):**
| Ký hiệu | Ý nghĩa |
|---|---|
| 🟪 Tím đậm | Ứng dụng di động (Flutter/Dart) |
| 🟣 Tím nhạt | Nhân xử lý AI tại biên (Edge AI) |
| 🟩 Xanh lá | Máy chủ Backend (Python/FastAPI) |
| 🟧 Cam | Cơ sở dữ liệu (PostgreSQL + PostGIS) |
| 🔵 Xanh dương | Bảng điều khiển Web |
| ✅ Đường liền | Luồng dữ liệu khi mạng bình thường |
| ⚠️ Đường đứt | Luồng dữ liệu khi mạng yếu/mất kết nối |

#### 1.2. PlantUML

```plantuml
@startuml system_architecture
!theme cerulean
skinparam backgroundColor #FAFAFA
skinparam componentStyle rectangle
skinparam defaultFontName "Segoe UI"

title Sơ đồ kiến trúc tổng quan hệ thống\nHệ thống cứu hộ bão lũ dựa trên Edge AI

legend right
  |= Màu |= Thành phần |
  |<#1a237e> | Ứng dụng di động |
  |<#4a148c> | Nhân AI tại biên |
  |<#004d40> | Máy chủ Backend |
  |<#e65100> | Cơ sở dữ liệu |
  |<#01579b> | Bảng điều khiển Web |
  | <color:green>──────</color> | Mạng bình thường |
  | <color:red>- - - -</color> | Mạng yếu/mất kết nối |
endlegend

package "📱 Ứng dụng di động (Flutter/Dart)" as MOBILE #1a237e {
    component "📷 Camera / Thư viện ảnh" as CAM
    component "📝 Nhập văn bản cứu hộ" as TXT
    component "📍 Dịch vụ GPS" as GPS
    
    package "🧠 Nhân xử lý AI tại biên" as AI_ENGINE #4a148c {
        component "Phân loại ảnh ngập lụt\n(MobileNetV3 - TFLite)" as IMG_AI
        component "Phân loại văn bản khẩn cấp\n(DistilBERT - ONNX)" as TXT_AI
        component "Tính điểm khẩn cấp\ntổng hợp" as SCORE
    }
    
    component "💾 Lưu trữ cục bộ\n(SQLite/Hive)" as LOCAL_DB
    component "🔄 Quản lý đồng bộ\n& Hàng đợi offline" as SYNC
    component "📶 Giám sát kết nối mạng" as NET_MON
}

package "🖥️ Máy chủ Backend (Python/FastAPI)" as SERVER #004d40 {
    component "🔌 REST API Server" as API
    component "🔗 WebSocket Server" as WS
    component "📊 Phân cụm không gian\n(DBSCAN/HDBSCAN)" as CLUSTER
}

database "🗄️ PostgreSQL + PostGIS" as PG #e65100

package "🌐 Bảng điều khiển Web (HTML/CSS/JS)" as DASHBOARD #01579b {
    component "🗺️ Bản đồ thời gian thực\n(Leaflet.js / Mapbox)" as MAP
    component "📋 Bảng quản lý\nsự kiện cứu hộ" as PANEL
}

CAM --> IMG_AI
TXT --> TXT_AI
IMG_AI --> SCORE
TXT_AI --> SCORE
GPS --> SCORE
SCORE --> LOCAL_DB
SCORE --> SYNC

NET_MON --> SYNC : Kiểm tra kết nối

SYNC -[#green,bold]-> API : <color:green>**Mạng tốt:** Gửi đầy đủ\n(ảnh + text + GPS + kết quả AI)</color>
SYNC -[#red,dashed]-> API : <color:red>**Mạng yếu:** Gửi metadata JSON\n(vài KB: kết quả AI + GPS + điểm)</color>

LOCAL_DB --> SYNC : Đồng bộ lại\nkhi có mạng

API --> CLUSTER
API --> PG
CLUSTER --> PG
PG --> WS
WS --> MAP : Cập nhật thời gian thực
PG --> MAP
PG --> PANEL

@enduml
```

#### 1.3. Mô tả

Kiến trúc hệ thống được thiết kế theo mô hình **lai (Hybrid)** gồm 4 tầng chính:

1. **Ứng dụng di động (Mobile App):** Được xây dựng bằng Flutter/Dart, chạy đa nền tảng (Android/iOS). Điểm cốt lõi là **nhân xử lý AI tại biên** chạy trực tiếp trên điện thoại người dùng, cho phép phân loại ảnh ngập lụt (TensorFlow Lite) và phân loại văn bản khẩn cấp (ONNX Runtime) mà **không cần kết nối Internet**. Hệ thống tự động tính điểm khẩn cấp tổng hợp từ kết quả AI và dữ liệu GPS.

2. **Cơ chế truyền dữ liệu thích ứng (Adaptive Data Transmission):**
   - **Khi mạng tốt (4G/WiFi):** Gửi toàn bộ dữ liệu bao gồm ảnh gốc, văn bản, tọa độ GPS và kết quả AI lên server.
   - **Khi mạng yếu/mất (2G/3G/offline):** Chỉ gửi gói metadata JSON gọn nhẹ (vài KB) chứa: kết quả phân loại AI, tọa độ GPS, điểm khẩn cấp và tóm tắt văn bản. Dữ liệu đầy đủ được lưu vào hàng đợi cục bộ (SQLite/Hive) và tự động đồng bộ khi kết nối được khôi phục.

3. **Máy chủ Backend:** Sử dụng Python với FastAPI, tiếp nhận dữ liệu từ ứng dụng di động, thực hiện phân cụm không gian các sự kiện cứu hộ bằng thuật toán DBSCAN/HDBSCAN kết hợp PostGIS để gom nhóm các báo cáo trùng lặp theo vị trí địa lý.

4. **Bảng điều khiển Web (Dashboard):** Hiển thị bản đồ thời gian thực với Leaflet.js/Mapbox, cập nhật liên tục qua WebSocket. Các sự kiện cứu hộ được phân cụm và hiển thị theo mã màu ưu tiên (đỏ = khẩn cấp, vàng = cần hỗ trợ, xanh = an toàn).

---

### 2. Sơ đồ kiến trúc chi tiết ứng dụng di động

#### 2.1. Mermaid

```mermaid
graph TB
    subgraph PRESENTATION["🎨 TẦNG TRÌNH BÀY (Presentation Layer)"]
        direction LR
        S1["Màn hình chính<br/>(Home)"]
        S2["Camera /<br/>Chọn ảnh"]
        S3["Nhập văn bản<br/>cứu hộ"]
        S4["Biểu mẫu<br/>yêu cầu cứu hộ"]
        S5["Lịch sử<br/>gửi báo cáo"]
        S6["Cài đặt"]
    end

    subgraph BLOC["⚙️ TẦNG NGHIỆP VỤ (Business Logic - BLoC)"]
        direction LR
        B1["ImageClassificationBloc"]
        B2["TextClassificationBloc"]
        B3["RescueRequestBloc"]
        B4["ConnectivityBloc"]
        B5["SyncBloc"]
        B6["HistoryBloc"]
    end

    subgraph AI_LAYER["🧠 TẦNG SUY LUẬN AI (AI Inference Layer)"]
        direction TB
        subgraph IMG_PIPE["Pipeline phân loại ảnh"]
            IP1["Tiền xử lý ảnh<br/>(resize, normalize)"]
            IP2["Mô hình TFLite<br/>(MobileNetV3)"]
            IP3["Kết quả: mức ngập<br/>(none/low/high)"]
        end
        subgraph TXT_PIPE["Pipeline phân loại văn bản"]
            TP1["Tokenization<br/>(Vietnamese)"]
            TP2["Mô hình ONNX<br/>(DistilBERT)"]
            TP3["Kết quả: loại tin<br/>(urgent/supplies/safe/irrelevant)"]
        end
        URGENCY["🔴 Tính điểm khẩn cấp<br/>tổng hợp (image + text + context)"]
    end

    subgraph DATA_LAYER["💾 TẦNG DỮ LIỆU (Data Layer)"]
        direction LR
        LOCAL["Lưu trữ cục bộ<br/>(SQLite / Hive)"]
        REST["REST API Client<br/>(Dio / http)"]
        WS_CLIENT["WebSocket Client"]
        SYNC_MGR["Quản lý đồng bộ<br/>(Queue → Retry → Send)"]
    end

    subgraph PLATFORM["📱 TẦNG NỀN TẢNG (Platform Layer)"]
        direction LR
        P_CAM["Camera Plugin"]
        P_GPS["Geolocator Plugin"]
        P_NET["Connectivity Plus"]
        P_BAT["Tối ưu pin<br/>(Battery Optimization)"]
        P_NOTIF["Thông báo đẩy<br/>(Local Notifications)"]
    end

    S1 --> B3
    S2 --> B1
    S3 --> B2
    S4 --> B3
    S5 --> B6
    S6 --> B4

    B1 --> IP1
    B2 --> TP1
    IP1 --> IP2 --> IP3
    TP1 --> TP2 --> TP3
    IP3 --> URGENCY
    TP3 --> URGENCY
    B3 --> URGENCY

    URGENCY --> LOCAL
    URGENCY --> SYNC_MGR
    B4 --> SYNC_MGR
    B5 --> SYNC_MGR
    B6 --> LOCAL

    SYNC_MGR --> REST
    SYNC_MGR --> WS_CLIENT
    LOCAL --> SYNC_MGR

    B1 --> P_CAM
    B3 --> P_GPS
    B4 --> P_NET
    SYNC_MGR --> P_BAT

    style PRESENTATION fill:#1565c0,stroke:#42a5f5,color:#fff,stroke-width:2px
    style BLOC fill:#6a1b9a,stroke:#ce93d8,color:#fff,stroke-width:2px
    style AI_LAYER fill:#b71c1c,stroke:#ef5350,color:#fff,stroke-width:2px
    style IMG_PIPE fill:#880e4f,stroke:#f06292,color:#fff,stroke-width:1px
    style TXT_PIPE fill:#880e4f,stroke:#f06292,color:#fff,stroke-width:1px
    style DATA_LAYER fill:#e65100,stroke:#ff9800,color:#fff,stroke-width:2px
    style PLATFORM fill:#1b5e20,stroke:#66bb6a,color:#fff,stroke-width:2px
```

#### 2.2. PlantUML

```plantuml
@startuml mobile_architecture
!theme cerulean
skinparam backgroundColor #FAFAFA
skinparam defaultFontName "Segoe UI"
skinparam packageStyle rectangle

title Sơ đồ kiến trúc chi tiết ứng dụng di động Flutter\n(Layered Architecture + BLoC Pattern)

package "🎨 Tầng trình bày (Presentation Layer)" as PRES #1565c0 {
    [Màn hình chính (Home)] as S1
    [Camera / Chọn ảnh] as S2
    [Nhập văn bản cứu hộ] as S3
    [Biểu mẫu yêu cầu cứu hộ] as S4
    [Lịch sử gửi báo cáo] as S5
    [Cài đặt] as S6
}

package "⚙️ Tầng nghiệp vụ (Business Logic - BLoC)" as BL #6a1b9a {
    [ImageClassificationBloc] as B1
    [TextClassificationBloc] as B2
    [RescueRequestBloc] as B3
    [ConnectivityBloc] as B4
    [SyncBloc] as B5
    [HistoryBloc] as B6
}

package "🧠 Tầng suy luận AI (AI Inference Layer)" as AI #b71c1c {
    package "Pipeline phân loại ảnh" as IMG_P #880e4f {
        [Tiền xử lý ảnh\n(resize, normalize)] as IP1
        [Mô hình TFLite\n(MobileNetV3)] as IP2
        [Kết quả: mức ngập\n(none/low/high)] as IP3
    }
    package "Pipeline phân loại văn bản" as TXT_P #880e4f {
        [Tokenization\n(Vietnamese)] as TP1
        [Mô hình ONNX\n(DistilBERT)] as TP2
        [Kết quả: loại tin\n(urgent/supplies/safe/irrelevant)] as TP3
    }
    [🔴 Tính điểm khẩn cấp tổng hợp] as URGENCY
}

package "💾 Tầng dữ liệu (Data Layer)" as DL #e65100 {
    [Lưu trữ cục bộ\n(SQLite / Hive)] as LOCAL
    [REST API Client\n(Dio / http)] as REST
    [WebSocket Client] as WSC
    [Quản lý đồng bộ\n(Queue → Retry → Send)] as SYNC_MGR
}

package "📱 Tầng nền tảng (Platform Layer)" as PL #1b5e20 {
    [Camera Plugin] as P_CAM
    [Geolocator Plugin] as P_GPS
    [Connectivity Plus] as P_NET
    [Tối ưu pin] as P_BAT
    [Thông báo đẩy] as P_NOTIF
}

S2 --> B1
S3 --> B2
S1 --> B3
S4 --> B3
S5 --> B6
S6 --> B4

B1 --> IP1
B2 --> TP1
IP1 --> IP2
IP2 --> IP3
TP1 --> TP2
TP2 --> TP3
IP3 --> URGENCY
TP3 --> URGENCY
B3 --> URGENCY

URGENCY --> LOCAL
URGENCY --> SYNC_MGR
B4 --> SYNC_MGR
B5 --> SYNC_MGR
B6 --> LOCAL
LOCAL --> SYNC_MGR

SYNC_MGR --> REST
SYNC_MGR --> WSC

B1 --> P_CAM
B3 --> P_GPS
B4 --> P_NET
SYNC_MGR --> P_BAT

@enduml
```

#### 2.3. Mô tả

Ứng dụng di động được thiết kế theo **kiến trúc phân tầng (Layered Architecture)** kết hợp **BLoC (Business Logic Component)** pattern để quản lý trạng thái. Lý do chọn BLoC:

- **Tách biệt rõ ràng** giữa UI và logic nghiệp vụ, phù hợp với ứng dụng có nhiều luồng xử lý phức tạp (AI inference, sync, connectivity monitoring).
- **Reactive programming** với Stream giúp UI tự động cập nhật khi trạng thái thay đổi (ví dụ: kết quả AI hoàn thành, trạng thái mạng thay đổi).
- **Testability cao** — mỗi BLoC có thể được unit test độc lập.
- **Được Flutter community hỗ trợ mạnh mẽ** với thư viện `flutter_bloc`.

**Các tầng chi tiết:**

1. **Tầng trình bày:** Gồm 6 màn hình chính — Trang chủ, Chụp/chọn ảnh, Nhập văn bản, Biểu mẫu cứu hộ, Lịch sử, Cài đặt. Mỗi màn hình kết nối với BLoC tương ứng.

2. **Tầng nghiệp vụ (BLoC):** 6 BLoC quản lý các luồng xử lý — phân loại ảnh, phân loại văn bản, tạo yêu cầu cứu hộ, giám sát kết nối, đồng bộ dữ liệu, lịch sử.

3. **Tầng suy luận AI:** Hai pipeline xử lý song song:
   - **Pipeline ảnh:** Tiền xử lý (resize 224×224, normalize) → MobileNetV3 TFLite → Phân loại mức ngập (none/low/high).
   - **Pipeline văn bản:** Tokenization tiếng Việt → DistilBERT ONNX → Phân loại tin nhắn (urgent_rescue/need_supplies/safe_update/irrelevant).
   - **Tính điểm khẩn cấp tổng hợp** từ cả hai pipeline kết hợp ngữ cảnh (vị trí, thời gian).

4. **Tầng dữ liệu:** Lưu trữ cục bộ bằng SQLite/Hive cho hàng đợi offline. Quản lý đồng bộ tự động retry với exponential backoff khi mạng yếu.

5. **Tầng nền tảng:** Tích hợp các plugin native — Camera, GPS (Geolocator), giám sát kết nối (Connectivity Plus), tối ưu pin để AI inference không tiêu hao quá nhiều tài nguyên.

---

### 3. Bảng mô tả các module chính

| # | Tên Module | Mô tả chức năng | Công nghệ sử dụng | Người phụ trách |
| --- | --- | --- | --- | --- |
| 1 | Module Camera & Chụp ảnh | Thu thập ảnh từ camera thiết bị hoặc thư viện ảnh. Hỗ trợ chụp ảnh trực tiếp với giao diện tùy chỉnh, nén ảnh trước khi xử lý AI. | Flutter (camera, image_picker plugin) | Nguyễn Thanh Trọng, Cao Tường Hưng |
| 2 | Module AI Phân loại ảnh (on-device) | Chạy mô hình AI ngay trên điện thoại để phân loại ảnh ngập lụt thành 3 mức: không ngập (none), ngập nhẹ (low), ngập nặng (high). Tiền xử lý ảnh (resize 224×224, normalize) trước khi đưa vào mô hình. | TensorFlow Lite, MobileNetV3 / EfficientNet-Lite | Lê Thị Ngọc Ảnh, Nguyễn Như Quỳnh, Ngô Hưng Thịnh, Cao Tường Hưng |
| 3 | Module Nhập & Xử lý văn bản | Cung cấp giao diện nhập tin nhắn cứu hộ bằng tiếng Việt. Thực hiện tiền xử lý văn bản: chuẩn hóa Unicode, loại bỏ ký tự đặc biệt, tokenization. | Flutter (TextInput), Dart | Nguyễn Thanh Trọng, Cao Tường Hưng |
| 4 | Module AI Phân loại văn bản (on-device) | Chạy mô hình NLP trên thiết bị để phân loại tin nhắn thành 4 nhóm: cứu hộ khẩn cấp (urgent_rescue), cần vật tư (need_supplies), cập nhật an toàn (safe_update), không liên quan (irrelevant). | ONNX Runtime Mobile, DistilBERT / PhoBERT distilled | Lê Thị Ngọc Ảnh, Nguyễn Như Quỳnh, Ngô Hưng Thịnh, Cao Tường Hưng |
| 5 | Module Tính điểm khẩn cấp | Kết hợp kết quả từ module phân loại ảnh và văn bản cùng thông tin ngữ cảnh (thời gian, vị trí) để tính điểm khẩn cấp tổng hợp (0.0 – 1.0). Công thức có trọng số cho từng yếu tố. | Dart (thuật toán tự xây dựng) | Nguyễn Thanh Trọng, Cao Tường Hưng |
| 6 | Module Hàng đợi Offline & Đồng bộ dữ liệu | Lưu trữ dữ liệu cứu hộ vào hàng đợi cục bộ khi mất kết nối. Tự động đồng bộ với server khi mạng được khôi phục với cơ chế retry (exponential backoff). Hỗ trợ 2 chế độ gửi: đầy đủ (mạng tốt) và gọn nhẹ (mạng yếu). | SQLite / Hive (Flutter), Dart Isolates | Nguyễn Thanh Trọng, Cao Tường Hưng |
| 7 | Module GPS & Dịch vụ vị trí | Lấy tọa độ GPS chính xác của thiết bị. Hỗ trợ reverse geocoding để hiển thị địa chỉ. Tối ưu pin khi thu thập vị trí liên tục. | Flutter (geolocator, geocoding plugin) | Nguyễn Thanh Trọng, Cao Tường Hưng |
| 8 | Module Giám sát kết nối mạng | Liên tục kiểm tra trạng thái mạng (WiFi/4G/3G/2G/offline). Đo lường băng thông thực tế để quyết định chế độ gửi dữ liệu (đầy đủ hoặc gọn nhẹ). Phát sự kiện khi trạng thái mạng thay đổi. | Flutter (connectivity_plus plugin) | Nguyễn Thanh Trọng, Cao Tường Hưng |
| 9 | Module REST API Client | Gửi dữ liệu cứu hộ lên server qua HTTP. Hỗ trợ multipart upload (ảnh), JSON request (metadata). Xử lý authentication, retry logic, error handling. | Dart (Dio / http package) | Nguyễn Thanh Trọng, Cao Tường Hưng |
| 10 | Module Backend API Server | Tiếp nhận và xử lý dữ liệu cứu hộ từ ứng dụng di động. Cung cấp REST API endpoints và WebSocket server cho cập nhật thời gian thực. Xác thực và phân quyền người dùng. | Python, FastAPI, Uvicorn | Lê Thị Ngọc Ảnh, Nguyễn Như Quỳnh |
| 11 | Module Phân cụm không gian (Spatial Clustering Engine) | Gom nhóm các sự kiện cứu hộ trùng lặp dựa trên vị trí địa lý và ngữ nghĩa. Sử dụng thuật toán DBSCAN/HDBSCAN kết hợp truy vấn không gian PostGIS. Cập nhật cụm theo thời gian thực khi có dữ liệu mới. | Python, scikit-learn (DBSCAN/HDBSCAN), PostGIS | Nguyễn Thanh Trọng, Ngô Hưng Thịnh |
| 12 | Module Cơ sở dữ liệu | Lưu trữ dữ liệu sự kiện cứu hộ, kết quả phân cụm, thông tin người dùng. Hỗ trợ truy vấn không gian (spatial queries) cho bản đồ và phân cụm. | PostgreSQL, PostGIS | Nguyễn Thanh Trọng, Cao Tường Hưng |
| 13 | Module Bảng điều khiển Web & Bản đồ | Hiển thị bản đồ thời gian thực với các sự kiện cứu hộ đã phân cụm. Mã màu theo mức độ khẩn cấp (đỏ/vàng/xanh). Cập nhật tự động qua WebSocket. Bảng quản lý danh sách sự kiện với bộ lọc. | HTML/CSS/JavaScript, Leaflet.js / Mapbox GL JS | Lê Thị Ngọc Ảnh, Nguyễn Như Quỳnh |
| 14 | Module Xác thực người dùng | Đăng ký, đăng nhập, quản lý phiên làm việc cho người dùng ứng dụng di động và quản trị viên dashboard. Hỗ trợ JWT token-based authentication. | FastAPI (python-jose), Flutter (secure_storage) | Lê Thị Ngọc Ảnh, Nguyễn Như Quỳnh |

---

### 4. Sơ đồ tổng hợp công nghệ sử dụng

#### 4.1. Mermaid

```mermaid
graph TB
    subgraph L1["🎨 Tầng trình bày (Frontend)"]
        direction LR
        F1["Flutter (Dart)"]
        F2["HTML / CSS / JavaScript"]
        F3["Leaflet.js / Mapbox GL JS"]
    end

    subgraph L2["🧠 Tầng xử lý AI tại biên (Edge AI)"]
        direction LR
        A1["TensorFlow Lite"]
        A2["ONNX Runtime Mobile"]
        A3["MobileNetV3 / EfficientNet-Lite"]
        A4["DistilBERT / PhoBERT distilled"]
    end

    subgraph L3["⚙️ Tầng nghiệp vụ (Backend)"]
        direction LR
        B1["Python 3.11+"]
        B2["FastAPI"]
        B3["Uvicorn"]
        B4["scikit-learn<br/>(DBSCAN/HDBSCAN)"]
    end

    subgraph L4["💾 Tầng dữ liệu (Data)"]
        direction LR
        D1["PostgreSQL"]
        D2["PostGIS"]
        D3["SQLite (mobile)"]
        D4["Hive (mobile)"]
    end

    subgraph L5["🔗 Tầng giao tiếp (Communication)"]
        direction LR
        C1["REST API<br/>(HTTP/HTTPS)"]
        C2["WebSocket"]
        C3["JSON"]
    end

    subgraph L6["🛠️ Công cụ phát triển (DevOps)"]
        direction LR
        T1["Git / GitHub"]
        T2["Docker"]
        T3["Google Colab<br/>(huấn luyện model)"]
        T4["Flutter DevTools"]
    end

    L1 --> L2
    L2 --> L3
    L3 --> L4
    L1 --> L5
    L3 --> L5
    L5 --> L4

    style L1 fill:#1565c0,stroke:#42a5f5,color:#fff,stroke-width:2px
    style L2 fill:#b71c1c,stroke:#ef5350,color:#fff,stroke-width:2px
    style L3 fill:#004d40,stroke:#1de9b6,color:#fff,stroke-width:2px
    style L4 fill:#e65100,stroke:#ff9800,color:#fff,stroke-width:2px
    style L5 fill:#4a148c,stroke:#ce93d8,color:#fff,stroke-width:2px
    style L6 fill:#37474f,stroke:#90a4ae,color:#fff,stroke-width:2px
```

#### 4.2. PlantUML

```plantuml
@startuml tech_stack
!theme cerulean
skinparam backgroundColor #FAFAFA
skinparam defaultFontName "Segoe UI"
skinparam packageStyle rectangle

title Sơ đồ tổng hợp công nghệ sử dụng theo tầng

package "🎨 Tầng trình bày (Frontend)" as L1 #1565c0 {
    [Flutter (Dart)] as F1
    [HTML / CSS / JavaScript] as F2
    [Leaflet.js / Mapbox GL JS] as F3
}

package "🧠 Tầng xử lý AI tại biên (Edge AI)" as L2 #b71c1c {
    [TensorFlow Lite] as A1
    [ONNX Runtime Mobile] as A2
    [MobileNetV3 / EfficientNet-Lite] as A3
    [DistilBERT / PhoBERT distilled] as A4
}

package "⚙️ Tầng nghiệp vụ (Backend)" as L3 #004d40 {
    [Python 3.11+] as B1
    [FastAPI] as B2
    [Uvicorn] as B3
    [scikit-learn (DBSCAN/HDBSCAN)] as B4
}

package "💾 Tầng dữ liệu (Data)" as L4 #e65100 {
    [PostgreSQL] as D1
    [PostGIS] as D2
    [SQLite (mobile)] as D3
    [Hive (mobile)] as D4
}

package "🔗 Tầng giao tiếp (Communication)" as L5 #4a148c {
    [REST API (HTTP/HTTPS)] as C1
    [WebSocket] as C2
    [JSON] as C3
}

package "🛠️ Công cụ phát triển (DevOps)" as L6 #37474f {
    [Git / GitHub] as T1
    [Docker] as T2
    [Google Colab] as T3
    [Flutter DevTools] as T4
}

L1 --> L2
L2 --> L3
L3 --> L4
L1 --> L5
L3 --> L5

@enduml
```

---

### 5. Sơ đồ tuần tự luồng xử lý yêu cầu cứu hộ

#### 5.1. Mermaid

```mermaid
sequenceDiagram
    actor User as 👤 Người dùng
    participant App as 📱 Ứng dụng Flutter
    participant ImgAI as 🖼️ AI Phân loại ảnh<br/>(TFLite - MobileNetV3)
    participant TxtAI as 📝 AI Phân loại văn bản<br/>(ONNX - DistilBERT)
    participant Score as 🔴 Tính điểm khẩn cấp
    participant NetMon as 📶 Giám sát mạng
    participant LocalDB as 💾 SQLite/Hive<br/>(Hàng đợi cục bộ)
    participant Sync as 🔄 Quản lý đồng bộ
    participant API as 🖥️ Backend FastAPI
    participant Cluster as 📊 Phân cụm không gian<br/>(DBSCAN)
    participant DB as 🗄️ PostgreSQL<br/>+ PostGIS
    participant WS as 🔗 WebSocket Server
    participant Dashboard as 🌐 Bảng điều khiển Web<br/>(Leaflet.js)

    Note over User,Dashboard: 🚨 LUỒNG XỬ LÝ YÊU CẦU CỨU HỘ THIÊN TAI

    rect rgb(25, 118, 210)
        Note over User,App: Bước 1: Người dùng nhập dữ liệu
        User->>App: Mở ứng dụng
        User->>App: Chụp ảnh vùng ngập lụt
        User->>App: Nhập tin nhắn cứu hộ<br/>("Nước ngập nóc nhà,<br/>cần cứu hộ gấp!")
        App->>App: Lấy tọa độ GPS tự động
    end

    rect rgb(183, 28, 28)
        Note over App,Score: Bước 2-4: AI suy luận tại biên (ON-DEVICE)
        par Xử lý song song trên thiết bị
            App->>ImgAI: Gửi ảnh đã tiền xử lý<br/>(resize 224x224, normalize)
            ImgAI-->>Score: Kết quả: flood_level = "high"<br/>(confidence: 0.92)
        and
            App->>TxtAI: Gửi văn bản đã tokenize
            TxtAI-->>Score: Kết quả: category = "urgent_rescue"<br/>(confidence: 0.95)
        end
        Score->>Score: Tính điểm khẩn cấp tổng hợp<br/>urgency_score = 0.94<br/>(weighted: 0.4*image + 0.4*text + 0.2*context)
    end

    rect rgb(74, 20, 140)
        Note over Score,Sync: Bước 5: Kiểm tra kết nối mạng
        Score->>LocalDB: Lưu bản sao cục bộ<br/>(phòng mất dữ liệu)
        Score->>NetMon: Kiểm tra trạng thái mạng
    end

    alt ✅ Mạng tốt (4G/WiFi - bandwidth > 1 Mbps)
        rect rgb(27, 94, 32)
            Note over Sync,API: Bước 6: Gửi đầy đủ dữ liệu
            NetMon-->>Sync: status = "connected"
            Sync->>API: POST /api/rescue-events<br/>📦 Full payload (~2-5 MB):<br/>• Ảnh gốc (JPEG)<br/>• Văn bản đầy đủ<br/>• GPS (lat, lng)<br/>• Kết quả AI<br/>• urgency_score: 0.94
            API-->>Sync: 201 Created ✅
            Sync->>LocalDB: Đánh dấu "đã đồng bộ"
        end
    else ⚠️ Mạng yếu/mất kết nối (2G/3G/offline)
        rect rgb(230, 81, 0)
            Note over Sync,API: Bước 7: Gửi metadata gọn nhẹ
            NetMon-->>Sync: status = "degraded" hoặc "offline"
            Sync->>LocalDB: Lưu dữ liệu đầy đủ vào hàng đợi
            Note over Sync: Chỉ gửi metadata JSON (~2-5 KB)
            Sync->>API: POST /api/rescue-events/compact<br/>📄 Compact payload (~2-5 KB):<br/>{"flood_level": "high",<br/>"category": "urgent_rescue",<br/>"urgency_score": 0.94,<br/>"lat": 16.054, "lng": 108.223,<br/>"text_summary": "Ngập nóc nhà, cứu hộ gấp",<br/>"has_pending_media": true}
            API-->>Sync: 201 Created ✅
            Note over LocalDB,Sync: ⏳ Khi mạng khôi phục
            LocalDB->>Sync: Lấy dữ liệu chờ đồng bộ
            Sync->>API: PUT /api/rescue-events/{id}/media<br/>📦 Upload ảnh gốc bổ sung
        end
    end

    rect rgb(0, 77, 64)
        Note over API,DB: Bước 8: Server xử lý & phân cụm
        API->>DB: INSERT sự kiện cứu hộ mới
        API->>Cluster: Kích hoạt phân cụm
        Cluster->>DB: Truy vấn PostGIS:<br/>ST_DWithin(point, 500m)<br/>+ thời gian < 2h
        Cluster->>Cluster: Chạy DBSCAN<br/>(eps=500m, min_samples=2)
        Cluster->>DB: UPDATE cluster_id<br/>cho các sự kiện gần nhau
        Cluster->>DB: UPDATE cluster priority<br/>= MAX(urgency_score)
    end

    rect rgb(1, 87, 155)
        Note over WS,Dashboard: Bước 9: Cập nhật Dashboard thời gian thực
        DB->>WS: Trigger: sự kiện mới / cụm cập nhật
        WS->>Dashboard: WebSocket push:<br/>{"type": "cluster_update",<br/>"cluster_id": 42,<br/>"priority": "critical",<br/>"event_count": 5,<br/>"center": [16.054, 108.223]}
        Dashboard->>Dashboard: 🗺️ Cập nhật bản đồ:<br/>• Marker đỏ = khẩn cấp (score > 0.7)<br/>• Marker vàng = cần hỗ trợ (0.4-0.7)<br/>• Marker xanh = an toàn (< 0.4)<br/>• Popup: chi tiết cụm sự kiện
    end

    Note over User,Dashboard: ✅ Toàn bộ luồng hoàn tất<br/>Từ khi người dùng gửi tin → Hiển thị trên bản đồ: ~2-5 giây (mạng tốt)
```

#### 5.2. PlantUML

```plantuml
@startuml sequence_rescue_flow
!theme cerulean
skinparam backgroundColor #FAFAFA
skinparam defaultFontName "Segoe UI"
skinparam sequenceMessageAlign center

title Sơ đồ tuần tự luồng xử lý yêu cầu cứu hộ thiên tai

actor "👤 Người dùng" as User
participant "📱 Ứng dụng\nFlutter" as App
participant "🖼️ AI Ảnh\n(TFLite)" as ImgAI
participant "📝 AI Văn bản\n(ONNX)" as TxtAI
participant "🔴 Tính điểm\nkhẩn cấp" as Score
participant "📶 Giám sát\nmạng" as NetMon
participant "💾 SQLite/Hive\n(Cục bộ)" as LocalDB
participant "🔄 Đồng bộ" as Sync
participant "🖥️ Backend\nFastAPI" as API
participant "📊 Phân cụm\n(DBSCAN)" as Cluster
participant "🗄️ PostgreSQL\n+ PostGIS" as DB
participant "🌐 Dashboard\nWeb" as Dashboard

== Bước 1: Người dùng nhập dữ liệu ==
User -> App : Mở ứng dụng
User -> App : Chụp ảnh vùng ngập lụt
User -> App : Nhập tin nhắn cứu hộ
App -> App : Lấy tọa độ GPS tự động

== Bước 2-4: AI suy luận tại biên (ON-DEVICE) ==
App -> ImgAI : Ảnh đã tiền xử lý\n(resize 224x224)
App -> TxtAI : Văn bản đã tokenize
ImgAI --> Score : flood_level = "high"\n(confidence: 0.92)
TxtAI --> Score : category = "urgent_rescue"\n(confidence: 0.95)
Score -> Score : Tính điểm tổng hợp\nurgency_score = 0.94

== Bước 5: Kiểm tra kết nối ==
Score -> LocalDB : Lưu bản sao cục bộ
Score -> NetMon : Kiểm tra mạng

alt Mạng tốt (4G/WiFi)
    == Bước 6: Gửi đầy đủ dữ liệu ==
    NetMon --> Sync : status = "connected"
    Sync -> API : POST /api/rescue-events\nFull payload (~2-5 MB)\nẢnh + Text + GPS + AI results
    API --> Sync : 201 Created
    Sync -> LocalDB : Đánh dấu "đã đồng bộ"

else Mạng yếu/mất (2G/3G/offline)
    == Bước 7: Gửi metadata gọn nhẹ ==
    NetMon --> Sync : status = "degraded"
    Sync -> LocalDB : Lưu đầy đủ vào hàng đợi
    Sync -> API : POST /api/rescue-events/compact\nCompact JSON (~2-5 KB)\nAI results + GPS + urgency_score
    API --> Sync : 201 Created
    note over LocalDB, Sync : Khi mạng khôi phục
    LocalDB -> Sync : Dữ liệu chờ đồng bộ
    Sync -> API : PUT /api/rescue-events/{id}/media\nUpload ảnh bổ sung
end

== Bước 8: Server xử lý & phân cụm ==
API -> DB : INSERT sự kiện mới
API -> Cluster : Kích hoạt phân cụm
Cluster -> DB : Truy vấn PostGIS\nST_DWithin(500m) + time < 2h
Cluster -> Cluster : DBSCAN clustering
Cluster -> DB : UPDATE cluster assignments

== Bước 9: Cập nhật Dashboard ==
DB -> Dashboard : WebSocket push:\ncluster_update event
Dashboard -> Dashboard : Cập nhật bản đồ\nĐỏ = khẩn cấp\nVàng = cần hỗ trợ\nXanh = an toàn

@enduml
```

#### 5.3. Mô tả

Sơ đồ tuần tự mô tả **toàn bộ vòng đời của một yêu cầu cứu hộ** từ khi người dùng gửi thông tin đến khi hiển thị trên bản đồ dashboard. Các bước chính:

1. **Thu thập dữ liệu (Bước 1):** Người dùng mở ứng dụng, chụp ảnh vùng ngập lụt và/hoặc nhập tin nhắn cứu hộ bằng tiếng Việt. Hệ thống tự động lấy tọa độ GPS.

2. **Suy luận AI tại biên (Bước 2–4):** Đây là điểm **khác biệt cốt lõi** của hệ thống. Hai pipeline AI chạy **song song ngay trên điện thoại**:
   - MobileNetV3 (TFLite) phân loại mức ngập: none/low/high
   - DistilBERT (ONNX) phân loại tin nhắn: urgent_rescue/need_supplies/safe_update/irrelevant
   - Điểm khẩn cấp tổng hợp được tính với công thức có trọng số (0.4 × image + 0.4 × text + 0.2 × context)

3. **Truyền dữ liệu thích ứng (Bước 5–7):** Hệ thống kiểm tra kết nối mạng và chọn chế độ gửi phù hợp:
   - **Mạng tốt:** Gửi payload đầy đủ (~2–5 MB) bao gồm ảnh gốc.
   - **Mạng yếu/offline:** Chỉ gửi gói JSON gọn nhẹ (~2–5 KB) chứa kết quả AI và metadata. Ảnh gốc được lưu trong hàng đợi cục bộ và tự động upload khi mạng khôi phục.

4. **Phân cụm trên server (Bước 8):** Backend sử dụng DBSCAN kết hợp PostGIS để gom nhóm các sự kiện cứu hộ trong bán kính 500m và khung thời gian 2 giờ, loại bỏ trùng lặp.

5. **Hiển thị Dashboard (Bước 9):** Bản đồ cập nhật thời gian thực qua WebSocket với mã màu ưu tiên:
   - 🔴 Đỏ: Khẩn cấp (urgency_score > 0.7)
   - 🟡 Vàng: Cần hỗ trợ (0.4 – 0.7)
   - 🟢 Xanh: An toàn (< 0.4)

**Thời gian phản hồi dự kiến:** ~2–5 giây từ khi người dùng gửi đến khi hiển thị trên bản đồ (trong điều kiện mạng bình thường).
