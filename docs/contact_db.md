# Hợp đồng Cơ sở Dữ liệu & Schema (`contact_db.md`)

Tài liệu quy định cấu trúc bảng dữ liệu, kiểu dữ liệu, ràng buộc (constraints), enum và quy tắc toàn vẹn cho tầng lưu trữ (SQLite cục bộ tại `be/data/rescue_reports.db` và tương thích PostgreSQL sau này).

---

## 1. Cấu Trúc Các Bảng (Tables Schema)

### 1.1 Bảng `reports` (Báo cáo cứu hộ)

Lưu trữ thông tin chi tiết từng ca cứu hộ do ứng dụng tạo ra.

```sql
CREATE TABLE IF NOT EXISTS reports (
    id                  TEXT PRIMARY KEY,              -- Mã báo cáo duy nhất, [A-Za-z0-9][A-Za-z0-9._:-]{0,127} (app: "sos-<ms>-<12 hex>")
    server_received_at  TEXT NOT NULL,                 -- Lần đầu server tiếp nhận (ISO 8601 UTC, hậu tố Z); không đổi khi gộp
    created_at          TEXT,                          -- Thời điểm tạo báo cáo trên client (ISO 8601 UTC)
    lat                 REAL,                          -- Vĩ độ GPS (WGS84, ví dụ: 16.4637)
    lng                 REAL,                          -- Kinh độ GPS (WGS84, ví dụ: 107.5909)
    trapped_count       INTEGER DEFAULT 0,             -- Số nạn nhân đang bị mắc kẹt (>= 0)
    injured_count       INTEGER DEFAULT 0,             -- Số nạn nhân bị thương (>= 0)
    vulnerable_groups   TEXT,                          -- JSON array các nhóm yếu thế: ["child", "elderly", ...]
    description         TEXT,                          -- Mô tả hiện trường, ghi chú khẩn cấp
    ai_tags             TEXT,                          -- JSON array kết quả AI: [{"label": "high", "confidence": 0.94}]
    send_mode           TEXT,                          -- Chế độ gửi (xem Enum SendMode)
    status              TEXT DEFAULT 'processing',     -- Trạng thái cứu hộ (xem Enum RescueStatus)
    status_version      INTEGER DEFAULT 1,             -- Phiên bản trạng thái (tăng dần khi update)
    image_filename      TEXT,                          -- Tên file do server đặt: "<id>_<12 hex SHA-256>.<jpg|png|webp>"
    image_local_path    TEXT,                          -- Đường dẫn tuyệt đối file ảnh trên ổ cứng server
    image_url           TEXT,                          -- URL tĩnh xem ảnh (ví dụ: "/uploads/rescue-10492_3f9a0c1d2e4b.jpg")
    image_sha256        TEXT,                          -- "sha256:" + hex SHA-256 nội dung nhị phân của ảnh
    image_size_bytes    INTEGER,                       -- Dung lượng ảnh tính theo byte
    raw_payload         TEXT NOT NULL,                 -- JSON gốc nhận lần đầu; lần gộp sau chỉ thêm key mới (vd. contactPhone, smsText từ SMS)
    -- Các cột phục vụ dashboard quản lý (không thuộc wire contract của app):
    first_received_at   TEXT,                          -- Lần đầu server nhận (ISO 8601 UTC); không đổi khi upsert, dùng tính thời gian phản ứng
    updated_seq         INTEGER DEFAULT 0,             -- Số thứ tự thay đổi (bộ đếm server_meta.seq) cho GET /api/reports/changes
    assigned_team_id    INTEGER,                       -- Đội phụ trách (teams.id), nullable
    location_source     TEXT,                          -- 'device' (GPS của app) | 'manual' (điều phối viên nhập) | NULL
    close_reason        TEXT,                          -- Lý do khi status = 'cancelled' (xem Enum CloseReason)
    status_updated_at   TEXT                           -- Lần đổi trạng thái gần nhất (ISO 8601 UTC)
);

CREATE INDEX IF NOT EXISTS idx_reports_received_at 
ON reports (server_received_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_updated_seq ON reports (updated_seq);
CREATE INDEX IF NOT EXISTS idx_reports_first_received ON reports (first_received_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports (status);
```

Báo cáo mới luôn bắt đầu ở `status = 'processing'` (trạng thái client gửi bị bỏ qua).
Khi cùng `id` được gửi lại (upload ảnh sau metadata, SMS rồi app đồng bộ, gửi lại do
mất ACK), server **gộp**, không ghi đè:

- Giữ nguyên dữ liệu đã lưu; chỉ điền cột còn trống (`created_at`, số người khi đang
  là 0, `vulnerable_groups`, `description`, `ai_tags`, `send_mode` khi `unknown`).
- Ảnh chỉ gắn khi báo cáo chưa có ảnh (ảnh đầu tiên được giữ), ghi sự kiện `image`.
- Tọa độ chỉ điền khi đang trống; vị trí điều phối viên nhập tay
  (`location_source = 'manual'`) được thay khi thiết bị gửi GPS thật.
- `server_received_at`, `first_received_at` giữ lần nhận đầu.

Tiếp nhận dùng chế độ WAL (`PRAGMA journal_mode = WAL`, bật trong `init_db()`) để
dashboard đọc không chặn app ghi; file phụ `*.db-wal`, `*.db-shm` nằm cạnh file DB.

Khi khởi động, mock server tự migrate database cũ: default `received` được đổi
thành `processing`, các dòng legacy có trạng thái `received` cũng được chuẩn hóa
thành `processing`, không xóa dữ liệu báo cáo.

### 1.1b Bảng phục vụ dashboard quản lý

```sql
-- Nhật ký thao tác: tiếp nhận, đổi trạng thái, giao đội, ghi chú, cập nhật vị trí, nhận ảnh/SMS.
CREATE TABLE IF NOT EXISTS report_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id       TEXT NOT NULL,
    kind            TEXT NOT NULL,     -- 'received' | 'status' | 'assign' | 'note' | 'location' | 'image' | 'sms'
    from_value      TEXT,              -- Giá trị trước (trạng thái, id đội, "lat,lng")
    to_value        TEXT,              -- Giá trị sau
    status_version  INTEGER,           -- Với kind = 'status'
    actor           TEXT,              -- Tên điều phối viên (dashboard, UPDATE_RESCUE_STATUS qua sync)
    source          TEXT NOT NULL,     -- 'app' | 'sync' | 'sms' | 'dashboard' | 'seed'
    note            TEXT,              -- Ghi chú (tối đa 1000 ký tự); lý do đóng
    created_at      TEXT NOT NULL      -- ISO 8601 UTC
);
CREATE INDEX IF NOT EXISTS idx_report_events_report ON report_events (report_id, id);

CREATE TABLE IF NOT EXISTS teams (          -- Đội cứu hộ
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    phone       TEXT,
    members     INTEGER,
    note        TEXT,
    active      INTEGER NOT NULL DEFAULT 1,  -- Đội ngừng hoạt động không nhận giao việc mới
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (       -- Phiên đăng nhập dashboard
    token_hash  TEXT PRIMARY KEY,           -- SHA-256 của token, không lưu token gốc
    operator    TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    expires_at  TEXT NOT NULL
);

-- 'seq': bộ đếm thay đổi không bao giờ giảm; 'epoch': đổi khi xóa toàn bộ dữ liệu;
-- 'cluster_rev': tăng khi đầu vào phân cụm đổi (báo cáo mới/gộp, trạng thái, vị trí).
CREATE TABLE IF NOT EXISTS server_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
```

`init_db()` tự thêm các cột/bảng này cho DB cũ và bù `first_received_at`
(= `server_received_at`), `location_source = 'device'` (khi có tọa độ), `updated_seq`.
`DELETE /api/reports` xóa `reports`, `messages_dedup`, `report_events`, giữ `teams`.

### 1.2 Bảng `messages_dedup` (Nhật ký chống trùng & Outbox Store-and-Forward)

Lưu lịch sử tiếp nhận từng message gửi qua kênh đồng bộ batch `POST /sync/messages`.

```sql
CREATE TABLE IF NOT EXISTS messages_dedup (
    message_id          TEXT PRIMARY KEY,              -- UUID duy nhất của message outbox
    client_id           TEXT NOT NULL,                 -- ID thiết bị/client gửi
    sequence_number     INTEGER NOT NULL,              -- Số nguyên thứ tự message theo client
    operation_type      TEXT NOT NULL,                 -- Tên nghiệp vụ (xem Enum OperationType)
    payload_hash        TEXT NOT NULL,                 -- "sha256:" + hex SHA-256 canonical (RFC 8785)
    status              TEXT NOT NULL,                 -- Trạng thái xử lý (xem Enum MessageStatus)
    error_code          TEXT,                          -- Mã lỗi nếu bị từ chối (xem Enum ErrorCode)
    result_data         TEXT,                          -- JSON string kết quả trả về cho client
    created_at          TEXT NOT NULL,                 -- Thời điểm tạo message trên client (ISO 8601 UTC)
    expires_at          TEXT,                          -- Thời điểm hết hạn message (ISO 8601 UTC, nullable)
    processed_at        TEXT NOT NULL                  -- Thời điểm server xử lý (ISO 8601 UTC)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_client_seq 
ON messages_dedup (client_id, sequence_number);
```

### 1.3 Hive box `sync_outbox` trên mobile

App dùng một Hive box để lưu bền vững metadata và message. Hai key metadata là
`_meta:client_id` và `_meta:sequence_number`; các key còn lại là `message_id`.

Mỗi message lưu toàn bộ wire contract cùng các field cục bộ:

| Field cục bộ | Kiểu | Ý nghĩa |
|---|---|---|
| `delivery_status` | `String` | `pending`, `in_flight` hoặc `dead_letter` |
| `attempt_count` | `Integer` | Số lần gửi thất bại đã ghi nhận |
| `next_attempt_at` | ISO 8601 UTC | Thời điểm sớm nhất được retry |
| `last_error` | `String?` | Mã lỗi/HTTP gần nhất để chẩn đoán |

`sequence_number` và message mới được ghi trong cùng thao tác Hive `putAll`.
Message `in_flight` còn sót sau khi tiến trình bị dừng được đưa lại về `pending`
khi khởi tạo. Message chỉ bị xóa khi server trả `accepted` hoặc `duplicate`.

---

## 2. Danh Sách Enum & Miền Giá Trị Hợp Lệ

### 2.1 `RescueStatus` (Trạng thái cứu hộ nghiệp vụ)
Được ghi vào cột `reports.status`. Chỉ cho phép tiến theo một chiều:

```text
processing  -->  dispatched  -->  resolved
   (1)              (2)              (3)
     \                \
      +----------------+-->  cancelled (3)
```

| Giá trị | Thứ tự (Rank) | Ý nghĩa |
| :--- | :---: | :--- |
| `processing` | 1 | Báo cáo đã tiếp nhận, đang chờ xử lý/phân bổ lực lượng. |
| `dispatched` | 2 | Đã điều động đội cứu hộ/phương tiện tiếp cận hiện trường. |
| `resolved` | 3 | Đã hoàn thành cứu hộ hoặc xử lý xong hiện trường. **Kết thúc.** |
| `cancelled` | 3 | Điều phối viên đóng báo cáo (trùng, báo giả...), kèm `close_reason`. **Kết thúc.** |

> **Quy tắc bất biến:** Không cho phép cập nhật trạng thái có rank nhỏ hơn rank hiện tại (ví dụ: không được đổi từ `dispatched` về `processing`). Trạng thái kết thúc (`resolved`, `cancelled`) không chuyển sang trạng thái khác.

`CloseReason` (cột `close_reason`): `duplicate` (trùng báo cáo khác), `false_alarm`
(báo giả / không xác minh được), `self_rescued` (đã tự thoát hoặc được hỗ trợ khác),
`no_contact` (không liên lạc được, không tìm thấy hiện trường), `other`.

### 2.2 `LocalDeliveryStatus` (Trạng thái vận chuyển cục bộ trên Client)
> **Lưu ý:** Chỉ dùng nội bộ trong client outbox / hàng đợi truyền tin, **KHÔNG** ghi vào `reports.status`:
- `pending`: Đang chờ gửi hoặc chờ retry scheduler.
- `in_flight`: Đang trong quá trình gửi HTTP request.
- `dead_letter`: Bị từ chối vĩnh viễn hoặc quá hạn, chờ điều tra.

`accepted`/`duplicate` không được lưu thành trạng thái `acked`: app xóa message
ngay sau ACK. `reports.status` vẫn là trạng thái cứu hộ nghiệp vụ, không được đổi
thành `dispatched` chỉ vì truyền HTTP thành công.

### 2.3 `OperationType` (Loại tác vụ message)
Quy định trong trường `operation_type` của message batch:

| Giá trị | Chiều | Mô tả |
| :--- | :---: | :--- |
| `CREATE_RESCUE_RECORD` | App -> Server | Tạo mới hoặc gửi lại một báo cáo cứu hộ (`payload.id` là ID báo cáo). |
| `UPDATE_RESCUE_STATUS` | Điều phối -> Server | Cập nhật trạng thái cứu hộ kèm `statusVersion` mới hơn. |

### 2.4 `MessageStatus` (Kết quả xử lý message)
Trả về trong mảng `results` của response `POST /sync/messages` và lưu tại `messages_dedup.status`:

| Giá trị | Ý nghĩa | Hành vi Client |
| :--- | :--- | :--- |
| `accepted` | Server đã commit transaction thành công. | Xóa message khỏi outbox. |
| `duplicate` | Message đã commit trước đó (cùng `message_id` và cùng `payload_hash`). | Xóa message khỏi outbox. |
| `rejected` | Bị từ chối do vi phạm quy tắc, lỗi cú pháp hoặc hết hạn. | Chuyển sang dead-letter (nếu `retryable=false`). |
| `retry_later` | Server tạm thời bận hoặc lỗi gián đoạn. | Chờ và retry theo exponential backoff. |

### 2.5 `ErrorCode` (Mã lỗi chuẩn hóa)
Quy định trong trường `code` khi status là `rejected`:

| Mã lỗi | Nguyên nhân | Retryable |
| :--- | :--- | :---: |
| `INVALID_PAYLOAD` | Thiếu trường bắt buộc hoặc `payload_hash` không khớp RFC 8785. | `false` |
| `EXPIRED` | Message có `expires_at < current_utc_time`. | `false` |
| `ID_REUSED_WITH_DIFFERENT_PAYLOAD` | Cùng `message_id` nhưng `payload_hash` khác với bản đã lưu. | `false` |
| `SEQUENCE_REUSED` | Cùng cặp `(client_id, sequence_number)` nhưng khác `message_id`. | `false` |
| `INVALID_STATUS_VERSION` | `UPDATE_RESCUE_STATUS` có `statusVersion <= version_hien_tai`. | `false` |
| `INVALID_STATUS_TRANSITION` | Thử lùi trạng thái cứu hộ (ví dụ: `dispatched` -> `processing`) hoặc đổi trạng thái đã kết thúc. | `false` |
| `REPORT_NOT_FOUND` | `UPDATE_RESCUE_STATUS` trỏ tới `id` không tồn tại. | `false` |
| `IMAGE_HASH_MISMATCH` | Ảnh upload qua `/api/reports` có SHA-256 khác `meta.imageSha256`. | `false` |
| `UNSUPPORTED_OPERATION` | `operation_type` không nằm trong danh sách định nghĩa. | `false` |
| `SERVER_BUSY` | Lỗi tạm thời phía máy chủ. | `true` |

### 2.6 `SendMode` (Chế độ gửi thích ứng)
- `rawImage`: Mạng mạnh, gửi ảnh JPEG gốc độ phân giải cao.
- `compressedImage`: Mạng trung bình, nén ảnh trước khi gửi.
- `textOnly`: Mạng rất yếu hoặc server tải cao, chỉ gửi text để tiết kiệm băng thông.
- `queuedOffline`: Tạo offline khi mất mạng hoàn toàn, gửi sau qua outbox.

### 2.7 `AiLabel` (Nhãn nhận diện ngập on-device)
- `low`: Ngập nhẹ (mức mắt cá / dưới đầu gối).
- `medium`: Ngập trung bình (ngang hông / ngực).
- `high`: Ngập sâu nguy hiểm (trên ngực / mái nhà).
- `non_flood`: Khu vực an toàn / không ngập.

---

## 3. Quy Tắc Toàn Vẹn Dữ Liệu (Invariants & Business Rules)

1. **Tính Idempotent của `message_id`**:
   - Khóa chính `message_id` bảo vệ chống trùng lặp.
   - Khi nhận lại `message_id` cũ: nếu cùng `payload_hash` thì trả kết quả cũ (status `duplicate`); nếu khác `payload_hash` bắt buộc từ chối `ID_REUSED_WITH_DIFFERENT_PAYLOAD`.
2. **Quy tắc `sequence_number`**:
   - Client cấp số tăng đơn điệu theo từng `client_id`.
   - Cặp `(client_id, sequence_number)` là duy nhất (`UNIQUE INDEX idx_client_seq`).
   - Server chấp nhận message đến sai thứ tự hoặc có gap; không báo lỗi gap.
3. **Chuẩn băm `payload_hash` (RFC 8785)**:
   - Server tự canonicalize `payload` theo RFC 8785 (sắp xếp key từ điển, không khoảng trắng, UTF-8) rồi băm SHA-256.
   - Backend Python dùng package `rfc8785` phiên bản `0.1.x`, không dùng `json.dumps(sort_keys=True)` thay thế.
   - Không tin tưởng chuỗi hash client gửi lên mà phải đối chiếu chéo.
4. **Quy tắc đồng bộ ảnh qua `/api/reports`**:
   - Khóa idempotent của báo cáo có ảnh là `meta.id`.
   - Nếu client gửi lại cùng `meta.id`, server không tạo dòng mới trong bảng `reports`; ảnh chỉ được gắn khi báo cáo chưa có ảnh (ảnh đầu tiên được giữ), nội dung chỉ được bổ sung trường còn trống (xem 1.1).
5. **Tính nguyên tử khi tạo báo cáo qua batch**:
   - `CREATE_RESCUE_RECORD` ghi `reports` và `messages_dedup` bằng cùng một SQLite
     connection/transaction; không được commit báo cáo nếu chưa ghi được dedup.
   - Mỗi message trong batch có transaction riêng: lỗi bất ngờ ở một message chỉ
     rollback message đó (kết quả `retry_later`, `SERVER_ERROR`), không làm hỏng batch.

---

## 4. Trạng Thái Triển Khai Thực Tế (Implementation Status)

- **Database file**: [`be/data/rescue_reports.db`](file:///e:/RHNA/1Visual/NCKH/nckh2/be/data/rescue_reports.db)
- **Mã nguồn**: [`be/storage.py`](file:///e:/RHNA/1Visual/NCKH/nckh2/be/storage.py)
- **Tình trạng**: Đã triển khai đầy đủ cả 2 bảng `reports` và `messages_dedup`.
  - Cột `status` dùng mặc định `'processing'`.
  - Đã có đầy đủ các cột: `status_version`, `image_sha256`, `image_size_bytes`.
  - Dashboard quản lý: bảng `report_events`, `teams`, `sessions`, `server_meta` và
    các cột `first_received_at`, `updated_seq`, `assigned_team_id`, `location_source`,
    `close_reason`, `status_updated_at`; kiểm thử tại `be/test_dashboard_api.py`.
  - Bảng `messages_dedup` và index `idx_client_seq` đã hoạt động.
  - Mobile đã có Hive box `sync_outbox`, partial ACK, retry metadata và retry ảnh.
  - Contract test tự động nằm tại `be/test_contract.py` và
    `fe/app/test/sync_contract_test.dart`.
