# Sản phẩm: hệ thống hỗ trợ cứu hộ lũ

Thư mục này chứa phần mềm chạy được của đề tài:

| Thư mục | Nội dung |
| --- | --- |
| [`be/`](be/) | Server FastAPI + SQLite: nhận báo cáo, đồng bộ store-and-forward, phân cụm và xếp hạng ưu tiên, dashboard điều phối |
| [`fe/app/`](fe/app/) | App Flutter: gửi SOS/bài cứu hộ, nhận diện mức ngập on-device, gửi thích ứng theo mạng, hàng đợi offline, SMS dự phòng |
| [`fe/model/`](fe/model/), [`fe/tools/`](fe/tools/) | Huấn luyện và export model (ONNX, ExecuTorch `.pte`) |
| [`docker/`](docker/) | Dockerfile và cấu hình nginx cho 3 container `be`, `dashboard`, `fe` |
| [`scripts/demo/`](scripts/demo/) | Script chạy server/app, build web, chép model, kiểm tra, E2E |

> **Mọi lệnh bên dưới chạy từ thư mục gốc repo** (thư mục chứa `docker-compose.yml`), trừ khi ghi `cd`.
> Hướng dẫn chi tiết và xử lý sự cố: [`docs/huong_dan_chay_demo.md`](../docs/huong_dan_chay_demo.md).
> Hợp đồng API app ↔ server: [`docs/contact_connect.md`](../docs/contact_connect.md).

---

## 1. Yêu cầu

| Thành phần | Cần cho | Ghi chú |
| --- | --- | --- |
| Docker Engine + Compose v2 | Cách A | Windows: Docker Desktop, bật **Settings → Resources → WSL Integration** cho distro đang dùng |
| Python ≥ 3.10 | Cách B, test | Script tự tạo `products/be/.venv` |
| Flutter 3.47.5 (Dart ^3.12.2) | App, build web | `flutter doctor` phải qua mục của nền tảng cần chạy |
| Android SDK (`compileSdk 37`) | App Android | Nền tảng chính: AI ExecuTorch và SMS chỉ có trên Android. WSL: `products/scripts/demo/setup_android_wsl.sh` |

---

## 2. Cách A: chạy toàn bộ bằng Docker (khuyến nghị)

```bash
# Build bản web của app trên máy (nhanh), rồi đóng gói cùng backend và dashboard
products/scripts/demo/build_web.sh
FE_BUILD_TARGET=prebuilt docker compose up -d --build

docker compose ps          # cả 3 service phải "healthy"
docker compose logs -f be  # xem log backend
docker compose down        # dừng, giữ dữ liệu (thêm -v để xóa dữ liệu)
```

Không có Flutter trên máy thì bỏ bước build web và chạy `docker compose up -d --build`
(Docker tự tải Flutter SDK ~1,6 GB ở lần đầu).

| Địa chỉ | Nội dung |
| --- | --- |
| <http://localhost:8080> | Dashboard điều phối |
| <http://localhost:8081> | App bản web (không có AI on-device và SMS) |
| <http://localhost:8000> | Backend: Swagger `/docs`, `/probe`, `/healthz`; app Android trỏ vào cổng này |

Lần đầu, backend nạp 316 báo cáo **bán tổng hợp** (run_001 trong `thucnghiem/data/gold`, gắn
nhãn "Dữ liệu mô phỏng") khi DB còn trống. Biến môi trường thường dùng (đặt trước lệnh hoặc
trong file `.env` ở gốc repo):

| Biến | Mặc định | Ý nghĩa |
| --- | --- | --- |
| `SEED_RUN` | `1` | Run dữ liệu mô phỏng nạp lúc đầu; `SEED_RUN=` để không nạp |
| `SEED_RESET` | `0` | `1` = xóa DB và nạp lại mỗi lần khởi động |
| `BE_PORT`, `DASHBOARD_PORT`, `FE_PORT` | `8000`, `8080`, `8081` | Cổng trên máy host |
| `RESCUE_ADMIN_USERNAME`, `RESCUE_ADMIN_PASSWORD` | `admin`, `cuuho2026` | Tài khoản quản trị tạo lần đầu |
| `RESCUE_SMS_GATEWAY_TOKEN` | trống | Bật `POST /api/sms/inbound` cho SMS gateway |

Danh sách đầy đủ: mục 0b của [hướng dẫn chạy demo](../docs/huong_dan_chay_demo.md).

---

## 3. Cách B: chạy server trực tiếp (không Docker)

```bash
products/scripts/demo/run_demo.sh --server-only   # server + DB demo riêng + dữ liệu mô phỏng
products/scripts/demo/run_server.sh               # server với DB mẫu đã commit
products/scripts/demo/run_server.sh --help        # --demo, --seed, --run N, --port ...
```

Windows PowerShell: `.\products\scripts\demo\run_server.ps1 -Demo -Seed`, hoặc
`products\be\run.bat` (DB mẫu, cổng 8000).

Chạy tay:

```bash
cd products/be
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export RESCUE_DB_FILE=data/demo.db RESCUE_UPLOADS_DIR=uploads_demo   # không làm bẩn DB mẫu đã commit
.venv/bin/python seed_demo.py --reset                                # tùy chọn: nạp dữ liệu mô phỏng
.venv/bin/python main.py                                             # http://localhost:8000
```

Dashboard ở <http://localhost:8000/>.

---

## 4. Đăng nhập dashboard

Tài khoản quản trị mặc định: `admin` / `cuuho2026`. Quản trị viên tạo tài khoản riêng cho
từng điều phối viên ở mục "Tài khoản". **Đổi mật khẩu mặc định trước khi triển khai thật.**

---

## 5. Chạy app Flutter

URL server truyền lúc build bằng `--dart-define=SERVER_URL=...`; script `run_app` tự chọn theo thiết bị.

```bash
flutter devices                                               # xem id thiết bị
products/scripts/demo/run_app.sh -d emulator-5554             # emulator: tự dùng http://10.0.2.2:8000
products/scripts/demo/run_app.sh -d <id-dien-thoai> --server-url http://<IP-LAN>:8000
products/scripts/demo/run_app.sh -d linux                     # Linux desktop / WSLg
products/scripts/demo/run_app.sh -d <id> --emergency-phone +84xxxxxxxxx   # bật SMS dự phòng (Android)
```

Chạy tay: `cd products/fe/app && flutter pub get && flutter run -d <id> --dart-define=SERVER_URL=http://10.0.2.2:8000`.

- **Điện thoại thật**: cùng mạng LAN với máy chạy server, mở firewall cổng 8000. Server chạy
  trong WSL/Docker thì dùng IP của Windows (xem mục 3.1 của hướng dẫn chi tiết).
- **Model AI on-device**: thư mục `products/fe/app/assets/models/` bị git-ignore; chép model
  đã export bằng `products/scripts/demo/stage_model.sh`. Thiếu model, app vẫn chạy nhưng tắt AI.
- **Khả năng theo nền tảng**: Android đủ tính năng; desktop không có ExecuTorch, SMS và đồng bộ
  nền Workmanager; web không có AI on-device và SMS.

---

## 6. Kiểm thử

```bash
# Unit test backend + Flutter
(cd products/be && .venv/bin/python -m unittest test_contract test_cluster_service test_dashboard_api)
(cd products/fe/app && flutter test && flutter analyze)   # analyze: chỉ còn lỗi trong code legacy lib/services, lib/controller.dart...
products/scripts/demo/check.sh --smoke                    # gộp các bước trên + smoke test server tạm
```

Kiểm thử **toàn hệ thống không cần điện thoại** (cần stack Docker ở mục 2 đang chạy):

```bash
# App web → backend → dashboard bằng Chromium headless (SOS, bài có ảnh, mạng yếu, mất mạng, không GPS)
python3 -m venv .venv-e2e && .venv-e2e/bin/pip install -r products/scripts/demo/e2e/requirements.txt
.venv-e2e/bin/playwright install chromium
.venv-e2e/bin/python products/scripts/demo/e2e/e2e_system.py

# App native trên Linux desktop: outbox Hive, mất mạng → có mạng lại, upload ảnh,
# chặn sửa giả mạo báo cáo, nhận trạng thái điều phối
cd products/fe/app
flutter test integration_test/system_test.dart -d linux \
  --dart-define=SERVER_URL=http://127.0.0.1:8099 \
  --dart-define=E2E_IMAGE=$PWD/../model/Dataset_Flood/high/flood_4791.jpg
```

Hai bài test này ghi báo cáo thật vào volume `be-data`; dọn bằng `docker compose down -v`.

---

## 7. Sự cố thường gặp

| Triệu chứng | Cách xử lý |
| --- | --- |
| `The command 'docker' could not be found in this WSL 2 distro` | Bật WSL Integration trong Docker Desktop (mục 1) |
| Build Linux báo `CMakeCache.txt directory ... is different` | Cache cũ từ trước khi dời thư mục: `rm -rf products/fe/app/build/linux` |
| Cổng 8000 đang bận | Đã có server khác chạy: `docker compose down` hoặc dừng `main.py`; hoặc đổi `BE_PORT` / `--port` |
| App không kết nối được server | Sai `SERVER_URL`: mở `<SERVER_URL>/probe` trên chính thiết bị đó để kiểm tra |
| Dashboard trống | DB chưa có dữ liệu: `SEED_RESET=1 docker compose up -d`, hoặc `run_server.sh --demo --seed` |
| Log `org.freedesktop.NetworkManager` trên Linux/WSL | WSL không có NetworkManager; app vẫn chạy bình thường |
