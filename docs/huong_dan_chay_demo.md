# Hướng dẫn chạy demo: server `be/` + app `fe/app`

Tài liệu này hướng dẫn dựng và chạy hệ thống hỗ trợ cứu hộ lũ ở chế độ demo. Hệ thống gồm:

- **Mock server** FastAPI + SQLite (`be/`): nhận báo cáo, đồng bộ store-and-forward, phân cụm/xếp hạng ưu tiên, dashboard điều phối.
- **App Flutter** (`fe/app`): chụp ảnh, nhận diện mức ngập on-device, gửi thích ứng theo chất lượng mạng, hàng đợi offline, SMS fallback.

Đánh giá trạng thái hiện tại (cái gì chạy được, cái gì còn thiếu): [nghiem-thu/danh_gia_trang_thai_demo.md](nghiem-thu/danh_gia_trang_thai_demo.md).
Hợp đồng dữ liệu app ↔ server: [contact_connect.md](contact_connect.md). Schema DB: [contact_db.md](contact_db.md).

---

## 0. Chạy nhanh

Các script nằm trong [`scripts/demo/`](../scripts/demo/). Mọi lệnh chạy từ **thư mục gốc repo**.

| Mục đích | Linux / macOS / WSL | Windows PowerShell |
| --- | --- | --- |
| Server + dữ liệu mô phỏng + app (1 lệnh) | `scripts/demo/run_demo.sh -d <device>` | chạy 2 lệnh bên dưới ở 2 cửa sổ |
| Chỉ server + dashboard (không cần Flutter) | `scripts/demo/run_demo.sh --server-only` | `.\scripts\demo\run_server.ps1 -Demo -Seed` |
| Chỉ server, dữ liệu mẫu đã commit | `scripts/demo/run_server.sh` | `.\scripts\demo\run_server.ps1` |
| Chỉ app | `scripts/demo/run_app.sh -d <device>` | `.\scripts\demo\run_app.ps1 -Device <device>` |
| Chép model vào app | `scripts/demo/stage_model.sh` | xem §4.1 |
| Kiểm tra trước khi demo | `scripts/demo/check.sh --smoke` | chạy lệnh test ở §6 |

Sau khi server chạy:

- Dashboard điều phối: <http://localhost:8000/>
- Swagger API: <http://localhost:8000/docs>
- Probe đo mạng: <http://localhost:8000/probe>

Mỗi script đều có `--help` (bash). Các script bash cần quyền thực thi; nếu mất quyền sau khi clone trên Windows thì chạy `chmod +x scripts/demo/*.sh`.

---

## 0b. Chạy toàn bộ hệ thống bằng Docker

Cần Docker Engine + Docker Compose v2. Mọi lệnh chạy từ thư mục gốc repo.

| Container | Cổng | Nội dung |
| --- | --- | --- |
| `be` | <http://localhost:8000> | FastAPI + SQLite (volume `be-data`), Swagger `/docs`, `/probe`. App Android/emulator trỏ `SERVER_URL` vào cổng này |
| `dashboard` | <http://localhost:8080> | Dashboard điều phối (nginx), proxy `/api`, `/uploads`, `/docs` về `be` |
| `fe` | <http://localhost:8081> | App Flutter **bản web** (nginx), proxy `/api`, `/sync`, `/probe`, `/uploads` về `be` |

```bash
docker compose up -d --build     # build Flutter web trong Docker: tải Flutter SDK ~1,6 GB ở lần đầu
docker compose ps                # cả 3 service phải "healthy"
docker compose logs -f be
docker compose down              # dừng, giữ dữ liệu; thêm -v để xóa dữ liệu

# Mạng chậm: build web bằng Flutter trên máy rồi chỉ đóng gói vào nginx
scripts/demo/build_web.sh && FE_BUILD_TARGET=prebuilt docker compose up -d --build
```

Biến môi trường (đặt trước lệnh hoặc trong file `.env` ở gốc repo):

| Biến | Mặc định | Ý nghĩa |
| --- | --- | --- |
| `SEED_RUN` | `1` | Nạp run bán tổng hợp `src/data/gold/run_00N` khi DB còn trống; `SEED_RUN=` để không nạp |
| `SEED_RESET` | `0` | `1` = xóa DB và nạp lại mỗi lần khởi động |
| `BE_PORT`, `DASHBOARD_PORT`, `FE_PORT` | `8000`, `8080`, `8081` | Cổng trên máy host |
| `FE_BUILD_TARGET` | `runtime` | `prebuilt` = dùng `fe/app/build/web` có sẵn |
| `FE_SERVER_URL` | trống | Trống = app web gọi API cùng origin qua nginx |

Bản web của app **không có** AI on-device (onnxruntime cần `dart:ffi`) và SMS; màn hình chính ghi rõ điều này. Để demo đủ tính năng AI, chạy app Android bằng `scripts/demo/run_app.sh -d <device> --server-url http://<IP-máy-chạy-Docker>:8000`.

Kiểm thử end-to-end hệ thống Docker (Chromium headless đóng vai người dùng ở Đà Nẵng: SOS, gửi bài kèm ảnh, mất mạng rồi đồng bộ lại, không có GPS, dashboard điều phối):

```bash
python3 -m venv .venv-e2e && .venv-e2e/bin/pip install -r scripts/demo/e2e/requirements.txt
.venv-e2e/bin/playwright install chromium
.venv-e2e/bin/python scripts/demo/e2e/e2e_system.py --screenshots /tmp/e2e-shots
```

Test ghi báo cáo thật vào DB của container; dọn bằng `docker compose down -v`. Mục `CHƯA CÓ` trong kết quả là tính năng còn thiếu, không phải lỗi.

---

## 1. Yêu cầu môi trường

| Thành phần | Phiên bản | Ghi chú |
| --- | --- | --- |
| Python | ≥ 3.10 (đã thử 3.12) | chỉ cần cho server; script tự tạo `be/.venv` |
| Flutter SDK | Dart `^3.12.2` (đã thử Flutter 3.47.5 stable) | `flutter doctor` phải qua mục của nền tảng cần chạy |
| Android Studio + Android SDK | có `compileSdk 37` | bắt buộc nếu chạy Android, **nền tảng chính**: ExecuTorch và SMS chỉ có trên Android |
| Visual Studio (Desktop C++) + Developer Mode | | chỉ khi chạy app Windows desktop |
| `curl` | | dùng trong `run_demo.sh` / `check.sh` |

Lưu ý khi dùng **chung một thư mục repo cho cả WSL và Windows**: `be/.venv` do WSL tạo (`.venv/bin/`) và do Windows tạo (`.venv\Scripts\`) không dùng lẫn được. Hãy dùng một môi trường cố định, hoặc clone riêng cho mỗi bên.

---

## 2. Server (`be/`)

### 2.1 Chạy bằng script

```bash
scripts/demo/run_server.sh                    # dữ liệu mẫu: be/data/rescue_reports.db + be/uploads/
scripts/demo/run_server.sh --demo             # DB riêng: be/data/demo.db + be/uploads_demo/
scripts/demo/run_server.sh --seed             # = --demo, xóa DB demo rồi nạp run_001 (316 báo cáo mô phỏng)
scripts/demo/run_server.sh --seed --run 5     # nạp run_005
scripts/demo/run_server.sh --port 8001 --no-reload
```

```powershell
.\scripts\demo\run_server.ps1 -Demo -Seed -Run 1 -Port 8000
```

Script tự tạo `be/.venv`, cài `be/requirements.txt` (chỉ cài lại khi file này thay đổi), rồi chạy `uvicorn main:app` trên `0.0.0.0:<port>`, nên thiết bị khác trong LAN truy cập được.

**Nên dùng `--demo` / `--seed` khi trình diễn.** `be/data/rescue_reports.db` và `be/uploads/` đang được commit làm dữ liệu mẫu. Chạy không có `--demo` thì mọi báo cáo gửi lên sẽ ghi vào đó và làm bẩn git. `demo.db`, `uploads_demo/` và `server_demo.log` đều đã được git-ignore.

### 2.2 Chạy thủ công

```bash
cd be
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export RESCUE_DB_FILE=data/demo.db RESCUE_UPLOADS_DIR=uploads_demo   # tùy chọn, đường dẫn tương đối với be/
.venv/bin/python seed_demo.py --reset                                  # tùy chọn
.venv/bin/python main.py                                               # cổng 8000 cố định, có auto-reload
```

Windows: `be\run.ps1` hoặc `be\run.bat` (luôn dùng DB mẫu, cổng 8000).

### 2.3 Về dữ liệu mô phỏng

`seed_demo.py` nạp `src/data/gold/run_NNN/algorithm_input.json`. Đây là dữ liệu **bán tổng hợp** neo theo bối cảnh Copernicus EMSR848, không phải báo cáo cứu hộ thật. Mỗi bản ghi mang `source: "synthetic"`, và dashboard tự hiện banner "Dữ liệu mô phỏng". Khi trình bày, **không** giới thiệu đây là dữ liệu thực tế.

---

## 3. App Flutter (`fe/app`)

### 3.1 Địa chỉ server (`SERVER_URL`)

URL server được truyền lúc build bằng `--dart-define=SERVER_URL=...`, xem [`fe/app/lib/config.dart`](../fe/app/lib/config.dart). Mặc định là `http://localhost:8000`. Script `run_app` tự chọn theo thiết bị:

| Thiết bị | `SERVER_URL` tự chọn | Ghi chú |
| --- | --- | --- |
| Android emulator (`emulator-*`) | `http://10.0.2.2:8000` | `10.0.2.2` là loopback của máy host |
| `windows`, `linux`, `macos`, `chrome` | `http://localhost:8000` | |
| Điện thoại thật | `http://<IP LAN đầu tiên>:8000` | **nên truyền `--server-url` tường minh** |

Với điện thoại thật:

1. Điện thoại và máy chạy server phải cùng mạng Wi-Fi/LAN.
2. Lấy IP LAN của máy chạy server (`ipconfig` trên Windows, `ip addr` trên Linux).
3. Trên Windows, mở firewall cho cổng 8000 (inbound TCP).
4. Nếu server chạy **trong WSL**, IP của WSL (`172.x.x.x`) không truy cập được từ điện thoại. Dùng IP của Windows host và chuyển tiếp cổng (`netsh interface portproxy add v4tov4 listenport=8000 connectport=8000 connectaddress=<IP WSL>`), hoặc bật networking mode `mirrored` của WSL.

### 3.2 Chạy

```bash
flutter devices                                     # xem id thiết bị
scripts/demo/run_app.sh -d emulator-5554
scripts/demo/run_app.sh -d <id-dien-thoai> --server-url http://192.168.1.20:8000
scripts/demo/run_app.sh -d linux                    # desktop, chỉ để xem UI (xem §3.3)
scripts/demo/run_app.sh -d <id> --release           # build release
```

```powershell
.\scripts\demo\run_app.ps1 -Device emulator-5554
.\scripts\demo\run_app.ps1 -Device windows
```

Chạy thủ công: `cd fe/app && flutter pub get && flutter run -d <id> --dart-define=SERVER_URL=http://10.0.2.2:8000`.

SMS dự phòng chỉ gửi khi đặt số tổng đài: `run_app.sh ... --emergency-phone +84xxxxxxxxx` (hoặc
`--dart-define=EMERGENCY_PHONE=+84xxxxxxxxx`). Thiếu số này, khi mất mạng app chỉ xếp báo cáo vào hàng đợi.

### 3.2b Android SDK trên WSL2 (không cần Android Studio)

```bash
scripts/demo/setup_android_wsl.sh             # ~2,5 GB: platform-tools, android-37.0, build-tools 36, NDK
cd fe/app && flutter build apk --debug --dart-define=SERVER_URL=http://<IP-LAN-Windows>:8000
```

- **Build APK**: chạy được hoàn toàn trong WSL, không cần sudo.
- **Cài lên điện thoại thật**: WSL không thấy thiết bị USB. Cách đơn giản nhất là chép
  `fe/app/build/app/outputs/flutter-apk/app-debug.apk` sang Windows (`/mnt/c/...`) rồi cài bằng
  `adb.exe install` phía Windows, hoặc bật *Wireless debugging* (Android 11+) và dùng
  `adb pair`/`adb connect` từ WSL (cần WSL networking mode `mirrored`). Có thể dùng `usbipd-win` để
  chuyển USB vào WSL.
- **Emulator trong WSL**: cần `/dev/kvm` và user thuộc nhóm `kvm` (`sudo usermod -aG kvm $USER`, rồi
  `wsl --shutdown`), cộng khoảng 3–4 GB RAM trống; chạy `scripts/demo/setup_android_wsl.sh --emulator`.
  Máy ít RAM nên dùng emulator của Android Studio phía Windows.
- Server chạy trong WSL/Docker: điện thoại cần IP Windows + port proxy (§3.1 bước 4).

### 3.3 Khả năng theo nền tảng

| Tính năng | Android | Windows / Linux desktop | Web |
| --- | --- | --- | --- |
| Gửi báo cáo, outbox, đồng bộ | ✔ | ✔ | ✔ |
| Suy luận ONNX | ✔ (cần model, §4) | ✔ (cần model) | ✘ |
| Suy luận ExecuTorch `.pte` | ✔ | ✘ | ✘ |
| Gửi thích ứng (đo `/probe` → ảnh gốc / nén / chỉ thông tin) | ✔ | ✔ | ✔ |
| SMS fallback | ✔ (cần `--emergency-phone`, §3.2) | ✘ (xếp hàng đợi) | ✘ (xếp hàng đợi) |
| Theo dõi trạng thái điều phối (15 s) | ✔ | ✔ | ✔ |
| Đồng bộ nền 15 phút (Workmanager) | ✔ | ✘ | ✘ |
| GPS | ✔ | tùy máy; không có GPS thì báo cáo gửi không kèm tọa độ, trung tâm xem xét thủ công | ✔ (trình duyệt hỏi quyền) |

Trên **Linux/WSL**, `connectivity_plus` cần NetworkManager qua D-Bus. WSL không có nên log in lỗi `org.freedesktop.NetworkManager`, nhưng app vẫn chạy.

---

## 4. Model AI on-device

App nạp 3 file từ `fe/app/assets/models/`: `model.onnx`, `model.pte`, `model_manifest.json` (phải có trường `"version"`). Thư mục này bị git-ignore (chỉ giữ `.gitkeep`). **Thiếu bất kỳ file nào thì app vẫn chạy, nhưng AI on-device bị tắt** (log `Notice loading AI model: Unable to load asset ...`), và báo cáo được gửi không kèm phân loại mức ngập.

Thứ tự nhãn trong `fe/app/assets/labels.json` (`low, medium, high, non_flood`) phải khớp đầu ra của model. Tiền xử lý: 224×224, NCHW, mean/std ImageNet.

### 4.1 Đã có file export → chép vào app

Nếu `fe/model/Edge Ai/` có đủ `flood_mobilenetv3_large.onnx`, `flood_mobilenetv3_large.pte` và `model_manifest.json`:

```bash
scripts/demo/stage_model.sh                      # hoặc --from <thư mục khác>
```

Trên Windows, chép tay 3 file trên vào `fe\app\assets\models\` và đổi tên thành `model.onnx`, `model.pte`, `model_manifest.json`.

### 4.2 Chưa có file export → export từ checkpoint

Tại thời điểm viết, repo **chỉ có** `fe/model/Edge Ai/flood_mobilenetv3_large.pte` và `model_metadata.json`. Chưa có ONNX, chưa có `model_manifest.json`. Cần export lại:

```bash
python3 -m venv .venv-model && . .venv-model/bin/activate
pip install -r fe/requirements.txt onnx onnxruntime executorch   # torch/torchvision: chọn wheel CPU/CUDA phù hợp
python fe/tools/convert_model.py     --checkpoint <file.pth> --config <config.json>
python fe/tools/export_executorch.py --checkpoint <file.pth> --config <config.json>
scripts/demo/stage_model.sh
```

- Đường dẫn mặc định của hai script là `fe/model/models/mobilenetv3_large_relabel_v2/{flood_mobilenetv3_large_relabel_v2_best.pth, config_mobilenetv3_large_v2.json}`, nhưng thư mục này **không có trong repo** (bị ignore). Lấy từ máy đã train, hoặc chạy lại notebook `fe/model/1706.ipynb`.
- File config tối thiểu cần `class_order` (ví dụ `["low","medium","high","non_flood"]`). Tùy chọn thêm `image_size`, `dropout`, `letterbox_fill`, `model_version`.
- `fe/app/model.pth` (≈ 50 MB, có trong git) *có thể* là checkpoint đã train, nhưng chưa được đối chiếu. Kiểm tra lớp và độ chính xác trước khi dùng (`fe/tools/verify_pipeline.py`, `fe/tools/compare_models.py`).
- Số liệu model nên trích khi trình bày: tập test độc lập trong notebook đạt **Accuracy 73.77% / macro-F1 72.21% (244 ảnh)**. Con số 86.58% trong `fe/reports/model_comparison/summary.md` đo trên toàn bộ dataset (gồm cả ảnh train), chỉ dùng để chứng minh ONNX ≈ PyTorch.

---

## 5. Kịch bản demo gợi ý

1. `scripts/demo/run_demo.sh --server-only` (hoặc `run_server.ps1 -Demo -Seed`) rồi mở dashboard. Bản đồ hiện 316 báo cáo mô phỏng gom thành khoảng 50 cụm, sắp theo mức ưu tiên, kèm banner "Dữ liệu mô phỏng".
2. Trên dashboard, đổi trạng thái một báo cáo `processing → dispatched → resolved`. Server không cho đi lùi trạng thái.
3. Chạy app trên emulator/điện thoại (`run_app.sh -d ...`). Tạo báo cáo có ảnh; báo cáo hiện trên dashboard trong vòng khoảng 5 giây (dashboard poll mỗi 5 giây).
4. **Offline/store-and-forward**: tắt server hoặc bật chế độ máy bay, tạo báo cáo, và báo cáo nằm trong outbox. Bật lại, app đồng bộ, và server chống trùng theo `message_id` + `payload_hash`.
5. **Gửi thích ứng**: app đo `/probe` (64 KB) rồi chọn gửi text / ảnh nén / ảnh gốc. Mạng yếu có thể mô phỏng bằng `be/experiments/weak_network.py` (proxy giới hạn băng thông 2G/3G/4G; xem `be/README.md`).

Reset DB demo: `scripts/demo/run_server.sh --seed` (nạp lại), hoặc `curl -X DELETE http://localhost:8000/api/reports` (xóa sạch DB đang chạy).

---

## 6. Kiểm tra trước khi demo

```bash
scripts/demo/check.sh            # unit test BE (23) + flutter test (12) + flutter analyze + kiểm tra model
scripts/demo/check.sh --smoke    # thêm: server tạm trên DB riêng + test_client.py + seed + /api/clusters + dashboard
```

`check.sh` bỏ qua lỗi analyze trong code legacy không còn dùng (`lib/controller.dart`, `lib/home_screen.dart`, `lib/background_sync.dart`, `lib/services/`), vì app không import các file này. Lỗi ở code khác sẽ làm lệnh fail.

Tương đương thủ công (Windows):

```powershell
cd be;  .\.venv\Scripts\python.exe -m unittest test_contract test_cluster_service -v
cd ..\fe\app;  flutter test;  flutter analyze
# smoke test: bật server ở cửa sổ khác rồi
cd ..\..\be;  .\.venv\Scripts\python.exe test_client.py
```

---

## 7. Xử lý sự cố

| Triệu chứng | Nguyên nhân / cách xử lý |
| --- | --- |
| App báo không kết nối được server | Sai `SERVER_URL` (xem §3.1). Mở `<SERVER_URL>/probe` bằng trình duyệt trên chính thiết bị đó để kiểm tra. |
| `Cổng 8000 đang bận` | Đã có server khác chạy. `ss -ltnp \| grep 8000` (Linux) / `netstat -ano \| findstr 8000` (Windows), hoặc dùng `--port`. |
| `Unable to load asset: assets/models/...` | Chưa chép model, xem §4. |
| `Building with plugins requires symlink support` (Windows) | Bật Developer Mode: `start ms-settings:developers`. |
| `.ps1 cannot be loaded because running scripts is disabled` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. |
| Dashboard trống | Đang dùng DB mẫu hoặc DB demo rỗng. Chạy với `--seed`. |
| SMS fallback không tới ai | Chưa đặt số tổng đài: chạy app với `--emergency-phone +84...` (§3.2). App cũng cần quyền SMS (Android hỏi lần đầu). |
