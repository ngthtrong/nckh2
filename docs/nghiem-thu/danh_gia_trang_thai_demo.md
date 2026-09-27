# Đánh giá trạng thái ứng dụng demo (`be/` + `fe/`)

Ngày đánh giá: 2026-09-27. Nhánh `feat/nghiem-thu`, sau commit `f752af4`.
Môi trường kiểm tra: Ubuntu 24.04 trên WSL2, Python 3.12.3, Flutter 3.47.5 stable. Máy này **không có Android SDK**, nên phần Android chưa được chạy thực tế.

Hướng dẫn chạy: [../huong_dan_chay_demo.md](../huong_dan_chay_demo.md).

> **Cập nhật 27/09/2026 (sau đánh giá này).** Một số kết luận bên dưới đã thay đổi; đối chiếu
> hiện hành nằm ở [doi_chieu_thuyet_minh.md](doi_chieu_thuyet_minh.md).
>
> - Hệ thống chạy được bằng Docker (`docker compose up -d --build`: `be`, `dashboard`, app bản web
>   `fe`); kiểm thử end-to-end `scripts/demo/e2e/e2e_system.py` đạt 46/46 (sau khi nâng cấp dashboard quản lý).
> - App đã nối **gửi thích ứng** (đo `/probe` → ảnh gốc / ảnh nén / chỉ thông tin), **SMS dự phòng**
>   (Android, số tổng đài qua `--emergency-phone`) và **theo dõi trạng thái điều phối** từ dashboard.
>   Trước đó các phần này có mã nhưng code đang chạy không gọi tới.
> - Đã sửa: báo cáo mang tọa độ giả TP.HCM khi không có GPS (nay gửi không kèm tọa độ, trung tâm
>   xem xét thủ công); `createdAt` của báo cáo có ảnh bị lệch 7 giờ; bỏ nhãn "TP. Hồ Chí Minh" gắn cứng.
> - Android SDK cài được trong WSL không cần sudo (`scripts/demo/setup_android_wsl.sh`); build APK
>   debug chạy trong WSL. Chưa chạy trên điện thoại thật.

## Kết luận nhanh

| Hạng mục | Trạng thái | Căn cứ |
| --- | --- | --- |
| Server `be/` | **Sẵn sàng demo** | 16/16 unit test; `test_client.py` đạt toàn bộ ca của `contact_connect.md`; seed 316 báo cáo → 50 cụm; dashboard và Swagger trả 200 |
| App `fe/app`: build, UI, gửi/đồng bộ | **Chạy được** (đã kiểm tra trên Linux desktop) | 12/12 `flutter test`; code đang dùng không có lỗi analyze; build Linux debug thành công và app mở được |
| App trên Android (nền tảng chính) | **Chưa kiểm chứng trong đợt này** | không có Android SDK trên máy đánh giá |
| AI on-device (ONNX / ExecuTorch) | **Chưa chạy được khi clone mới** | thiếu `model.onnx` và `model_manifest.json`; checkpoint + config mặc định không có trong repo (§3) |
| SMS fallback | **Chỉ có khung** | số tổng đài là số giả `+840000000000` |

Để demo trọn vẹn, cần làm theo thứ tự: (1) export và chép model (§3), (2) chạy thử trên 1 emulator và 1 điện thoại Android thật, (3) đặt số SMS thật cho buổi demo.

## 1. Server `be/`

**Đã kiểm chứng**

- `python -m unittest test_contract test_cluster_service` → 16 test OK: hợp đồng sync, migration, RFC 8785, phân cụm.
- Server chạy thật trên DB riêng (`RESCUE_DB_FILE`) và `test_client.py` đạt hết:
  - `/probe` trả 64 KB;
  - `POST /api/reports` multipart kèm kiểm tra SHA-256 ảnh (từ chối ảnh sai hash);
  - `/sync/messages` chặn contract version sai và xử lý đúng `duplicate`, `ID_REUSED_WITH_DIFFERENT_PAYLOAD`, `SEQUENCE_REUSED`;
  - chuyển trạng thái chỉ đi tiến.
- `seed_demo.py --reset` nạp run_001 (316 báo cáo bán tổng hợp). `GET /api/clusters` trả 50 cụm. Dashboard `/` và `/docs` trả HTTP 200.

**Hạn chế / lưu ý**

- Không có xác thực. CORS mở cho mọi origin. Chỉ phù hợp chạy trong LAN để demo.
- Cổng cố định 8000 khi chạy `main.py`. Script mới gọi `uvicorn` trực tiếp nên đổi cổng được.
- `be/README.md` còn nói dữ liệu lưu ở `data/reports.json`, nhưng thực tế là SQLite `data/rescue_reports.db`. `data/reports.json` là file cũ vẫn còn trong git.
- Chạy server không đặt `RESCUE_DB_FILE` thì mọi báo cáo sẽ ghi vào DB mẫu đã commit. Script `run_server --demo` tránh được việc này.

## 2. App `fe/app`

**Đã kiểm chứng**

- `flutter test`: 12/12 pass (send mode, payload hash RFC 8785, AI model settings).
- `flutter analyze`: 22 **lỗi** + 7 info. Toàn bộ 22 lỗi nằm trong code legacy mà `main.dart` không import (`lib/controller.dart`, `lib/home_screen.dart`, `lib/background_sync.dart`, `lib/services/*`). Code đang dùng có 0 lỗi, chỉ còn info (`withOpacity` deprecated, …).
- `flutter build linux --debug` thành công. `run_demo.sh -d linux` bật server, build và mở app. Ctrl+C tắt cả app lẫn server.
- Khi chạy trên Linux/WSL, log có các lỗi **không làm dừng app**:
  - `MissingPluginException` của `permission_handler` (plugin không hỗ trợ Linux; `app_controller.dart:158` không bắt lỗi này);
  - `connectivity_plus` không tìm thấy NetworkManager (WSL không có D-Bus NetworkManager);
  - assertion debug "ListTile … wrapped in a DecoratedBox" ở `settings_screen.dart:692`. Lỗi này thuần hiển thị (hiệu ứng ripple bị che) và sẽ xuất hiện trên mọi nền tảng ở chế độ debug.

**Chưa kiểm chứng trong đợt này**: luồng gửi báo cáo từ app tới server bằng thao tác UI, camera, GPS, Workmanager, ExecuTorch, SMS. Tất cả cần Android.

**Hạn chế / lưu ý**

- Dependency trong `pubspec.yaml` khai báo `any`, nên mỗi lần `flutter pub get` có thể nâng phiên bản. Commit `f752af4` đã kéo theo 4 package nâng bản nhỏ trong `pubspec.lock`, và test vẫn pass.
- Nhãn vị trí "TP. Hồ Chí Minh" và địa chỉ mặc định "Quận 1" được hard-code trong `app_controller.dart`. Khi demo ở tỉnh khác, nhãn sẽ sai dù tọa độ GPS đúng.
- `kEmergencyPhone` là số giả, nên SMS fallback không tới đâu.
- File thừa trong git: `fe/app/lib.zip`, `fe/app/android.zip`, `fe/app/wm_*.txt`, `fe/app/model.pth` (≈ 50 MB, chưa rõ có phải checkpoint cuối không). `fe/app/README.md` vẫn là mẫu mặc định của Flutter. `fe/README.md` ghi URL mặc định là `10.0.2.2`, trong khi code dùng `localhost`.

## 3. Model AI on-device

- App cần `assets/models/{model.onnx, model.pte, model_manifest.json}`. `loadModel()` đọc manifest và ONNX trước, nên thiếu một trong hai thì **cả ONNX lẫn ExecuTorch đều không được nạp**. App vẫn chạy, nhưng `isModelReady = false`.
- Hiện repo có `fe/model/Edge Ai/flood_mobilenetv3_large.pte` và `model_metadata.json` (không có trường `version`). **Không có** ONNX, không có `model_manifest.json`, không có thư mục checkpoint/config mặc định `fe/model/models/mobilenetv3_large_relabel_v2/` (bị git-ignore). Máy đánh giá cũng không cài `torch`, nên chưa export lại được.
- Số liệu nên trích: test độc lập trong notebook đạt Accuracy 73.77% / macro-F1 72.21% (244 ảnh). Không trích 86.58%, vì con số đó đo trên toàn bộ dataset, gồm cả ảnh train.

## 4. Thay đổi trong đợt đánh giá

| Thay đổi | Lý do |
| --- | --- |
| `pubspec.yaml` thêm `assets/models/` + `fe/app/assets/models/.gitkeep` + ngoại lệ trong `fe/.gitignore` | Flutter **không** bundle thư mục con của `assets/`. Trước đây, dù đã chép model vào thì app vẫn báo không tìm thấy asset. |
| `config.dart`: `kServerBaseUrl` đọc `--dart-define=SERVER_URL` (mặc định vẫn `http://localhost:8000`) | Đổi server theo thiết bị mà không phải sửa code. |
| `scripts/demo/`: `run_server`, `run_app` (bản `.sh` và `.ps1`), `run_demo.sh`, `stage_model.sh`, `check.sh` | Khởi chạy và kiểm tra bằng một lệnh. `check.sh --smoke` tái hiện toàn bộ phần kiểm chứng của §1–§2. |
| `docs/huong_dan_chay_demo.md` | Hướng dẫn chạy. |

Các script `.sh` đã được chạy thực tế trên WSL. Hai script `.ps1` mới chỉ được kiểm tra cú pháp bằng parser của Windows PowerShell 5.1, **chưa chạy thật trên Windows**.

## 5. Việc nên làm tiếp (theo mức ưu tiên)

1. Export ONNX + manifest từ checkpoint đã train rồi `stage_model.sh`. Kiểm tra lại bằng `fe/tools/verify_pipeline.py`.
2. Chạy `run_app` trên emulator và điện thoại thật: gửi báo cáo có ảnh, thử offline → outbox → đồng bộ lại, thử ExecuTorch và SMS.
3. Thay `kEmergencyPhone` bằng số demo thật. Bỏ nhãn "TP. Hồ Chí Minh" hard-code.
4. Bắt lỗi quanh `Permission...request()` và `connectivity_plus` để desktop không in lỗi unhandled. Bọc `ListTile` ở `settings_screen.dart:692` trong `Material`.
5. Dọn code legacy (`lib/controller.dart`, `lib/home_screen.dart`, `lib/background_sync.dart`, `lib/services/`), các file thừa, và `be/data/reports.json`. Cập nhật `be/README.md` và `fe/README.md`.
6. Ghim phiên bản dependency trong `pubspec.yaml` thay cho `any` để build tái lập được.
