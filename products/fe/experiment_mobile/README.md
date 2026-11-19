# Thực nghiệm mobile trong frontend

**Build APK ở `products/fe/app` bằng Flutter như bình thường.** APK admin chứa model PTE seed 1024 pruning và dữ liệu **cả run_001, run_002**. Không cần mở benchmark trước khi build, không copy APK theo mã lượt.

## 1. Build APK

Assets đã được chuẩn bị trong repo. Từ gốc dự án:

```powershell
cd products/fe/app
flutter pub get
flutter build apk --flavor admin --release --target-platform android-arm64 --dart-define=ALLOW_INSECURE_LAN=true --dart-define=SERVER_URL=http://192.168.137.1:18101
```

Thay IP ví dụ bằng IP máy tính mà điện thoại truy cập được. Khi máy tính phát Wi-Fi hotspot, IP thường là `192.168.137.1`.

Lấy file tại:

```text
products/fe/app/build/app/outputs/flutter-apk/app-admin-release.apk
```

Gửi APK qua Zalo rồi cài. Không cần USB. Bản admin tự có mục E2E, không cần thêm `ENABLE_MOBILE_E2E=true`. Chức năng này chỉ hiện sau khi đăng nhập admin; bản `--flavor user` vẫn dùng luồng người dùng thường.

**Khi đổi dữ liệu/model hoặc cần chuẩn bị lại assets**, tại `products/fe/app` chạy trước khi build:

```powershell
python ../experiment_mobile/prepare_assets.py
```

Script chỉ cần Python chuẩn, không cần môi trường thư viện E2E. Nó kiểm tra nguồn gold/CSV/ảnh, copy đúng model PTE seed1024 và tạo lại gói cố định của hai run. Lệnh sau chỉ kiểm tra, không ghi file:

```powershell
python ../experiment_mobile/prepare_assets.py --check
```

## 2. Mở backend và công cụ benchmark trên máy tính

Dùng Docker **flood-rescue** hiện có. Nếu backend còn cũ, cập nhật tại gốc repo:

```powershell
docker compose up -d --build be dashboard
```

Backend mặc định cổng 8000, dashboard 8080. Không xóa volume và không reset DB.

Chuẩn bị công cụ Python một lần, tại gốc repo:

Khởi động môi trường venv: .\products\fe\experiment_mobile\.venv\Scripts\Activate.ps1

```powershell
python -m venv products/fe/experiment_mobile/.venv
.\products\fe\experiment_mobile\.venv\Scripts\Activate.ps1
python -m pip install -r products/fe/experiment_mobile/requirements.txt
python -m playwright install chromium
```

Sau đó, mỗi cửa sổ PowerShell mới cần kích hoạt đúng môi trường trước khi chạy công cụ:

```powershell
.\products\fe\experiment_mobile\.venv\Scripts\Activate.ps1
python -X utf8 products/fe/experiment_mobile/coordinator.py start --lan-ip 192.168.137.1
```

Nhập mật khẩu admin hiện có của flood-rescue

Giữ cửa sổ mở. **Một lệnh start mở cả hai run**, mỗi run có tên lượt và checkpoint riêng. Ngày giờ được tạo lúc start, không được đóng vào assets/APK.

Trên điện thoại cùng mạng, mở `http://192.168.137.1:18101/healthz`. Phải thấy JSON có `serverId` trước khi thử app. Nếu cùng Wi-Fi công cộng mà không vào được, mạng có thể chặn thiết bị truy cập nhau; thử để máy tính phát hotspot rồi cho điện thoại kết nối.

## 3. Chạy trên điện thoại

1. Mở **Cứu hộ · Admin**, cấp quyền Vị trí và đăng nhập Admin trong Cài đặt.
2. Mở **Thực nghiệm E2E → Chọn run**: có sẵn `run_001` và `run_002` trong APK.
3. Bấm **Tải gói benchmark**. App mở dữ liệu từ assets, kiểm tra hash/model và ghép với lượt tương ứng trên máy tính. Không tải ảnh/gói E2E từ server; server chỉ cấp thông tin lượt và điều khiển bài thử.
4. Bấm **Chạy / Tiếp tục** cho từng case. Chọn run còn lại rồi mở gói để thực nghiệm run đó; tiến độ hai run tách riêng.

### Mục “1. Kiểm thử luồng xử lý” trên app

App gọi trực tiếp các hàm xử lý trên điện thoại: nhận diện bằng PTE, gửi bài và đồng bộ với backend thật. Bộ chạy không tự chọn ảnh hay bấm Gửi trên các màn hình. PASS nghĩa là các điều kiện kiểm tra của case đã đạt; không chứng minh toàn bộ giao diện hoạt động đúng. Với case có ảnh, kết quả nhận diện được lưu nhưng PASS không yêu cầu nhãn dự đoán trùng nhãn chuẩn; độ chính xác model được đánh giá riêng.


| Case             | Thao tác                                                                                                                                              |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| online           | Mạng hoạt động bình thường; PTE nhận diện và gửi bài thật.                                                                                |
| offline_recovery | Proxy cố ý trả HTTP 503, app giữ hàng đợi rồi đồng bộ đúng một lần khi mở lại.                                                        |
| adaptive_300     | Tự thử giới hạn 300 kbit/s, RTT 150 ms.                                                                                                            |
| adaptive_20      | Tự thử giới hạn 20 kbit/s, RTT 150 ms.                                                                                                             |
| no_gps           | Trước khi chạy, vào Cài đặt Android và từ chối quyền Vị trí của app. Cấp lại quyền trước khi chạy online ở lượt/run tiếp theo. |
| feedback         | Đổi trạng thái bài online của đúng benchmark, app nhận lại trạng thái.                                                                     |

FAIL có thể thử lại case, hoặc chạy lại toàn bộ run; lần thử trước được giữ trong lịch sử. Bỏ qua giữ NOT_RUN, không tính PASS. Một bước có thể mất khoảng 90 giây.

### Mục “2. Kiểm thử thao tác trên giao diện thật” trên app

Sáu case ở trên kiểm tra luồng xử lý. Phần này cần bạn **thao tác trực tiếp và quan sát trên điện thoại** để kiểm tra nút bấm, nội dung hiển thị và trạng thái khi mất kết nối Wi-Fi/data thật. Case 7 dùng mạng bình thường để kiểm tra đường đi qua giao diện, không lặp lại phép kiểm tra hàm của Case 1. Nút ghi kết quả chỉ lưu xác nhận của người chạy. Nên làm sau các case luồng xử lý, khi coordinator vẫn mở và profile đã về online.

**Case 7 — Thao tác trên giao diện Android**

**Bấm theo thứ tự:** Trang chủ → Gửi bài cứu hộ → chọn ảnh/nhập mô tả → Gửi → Lịch sử → mở bài → đối chiếu dashboard → Cài đặt → Thực nghiệm E2E → Ghi kết quả Case 7.

1. Ghi lại run đang chọn (`run_001` hoặc `run_002`). Nếu đã từ chối quyền Vị trí ở case `no_gps`, cấp lại quyền trong Cài đặt Android.
2. Ra màn hình gửi bài thông thường, chọn ảnh, nhập mô tả dễ tìm, ví dụ `manual_ui_run_001_20261023_1600`, rồi gửi. Mở màn hình SOS để kiểm tra giao diện; **không kích hoạt gọi điện/SMS thật**.
3. Vào **Lịch sử**, mở bài vừa gửi và kiểm tra nội dung/ảnh/trạng thái hiển thị.
4. Mở dashboard máy tính (`http://127.0.0.1:8080` mặc định), tìm đúng bài theo mô tả hoặc ID, đối chiếu với điện thoại. Chụp màn hình gửi bài, Lịch sử và dashboard để lưu bằng chứng.
5. Quay lại **Cài đặt → Thực nghiệm E2E**, chọn đúng run đã ghi lại, bấm **Ghi kết quả Case 7 → Đạt (PASS)** nếu đạt, hoặc **Có lỗi (FAIL)** và nhập mô tả nếu gặp lỗi.

**Case 8 — Tắt/bật mạng vật lý**

**Bấm theo thứ tự:** tắt Wi-Fi + dữ liệu di động → Trang chủ → Gửi bài cứu hộ → Gửi → xem hàng đợi → bật Wi-Fi → kiểm tra Lịch sử/dashboard → Ghi kết quả Case 8.

1. Khi app đang kết nối bình thường, tắt **cả Wi-Fi lẫn dữ liệu di động trên điện thoại**. Nếu dùng hotspot máy tính thì chỉ ngắt Wi-Fi điện thoại, vẫn để hotspot và coordinator trên máy tính chạy.
2. Gửi một bài thông thường với mô tả riêng, ví dụ `manual_offline_run_001_20261023_1605`. Kiểm tra bài nằm trong hàng đợi/chưa đồng bộ và chụp màn hình. Không dùng gọi/SMS làm đường gửi thay thế.
3. Bật lại Wi-Fi điện thoại, kết nối đúng mạng cũ, chờ đồng bộ. Kiểm tra bài hết chờ gửi.
4. Tìm bài trên dashboard; xác nhận có **đúng một báo cáo** tương ứng, không phát sinh bản trùng. Lưu ảnh hàng đợi trước/sau phục hồi và bài trên dashboard.
5. Quay lại đúng run, bấm **Ghi kết quả Case 8 → Đạt (PASS)** nếu đạt, hoặc **Có lỗi (FAIL)** và nhập mô tả nếu gặp lỗi.

Case luồng xử lý `offline_recovery` chỉ dùng HTTP 503 nên **không thay thế Case 8**. Bài gửi thủ công cũng không thay thế các ID báo cáo của sáu case luồng xử lý.

### Mục “3. Kiểm thử hiển thị trên dashboard” trên app

**Case 9 — Dashboard**

Công cụ Playwright trên máy tính kiểm tra giao diện dashboard. Đây là kiểm tra giao diện web riêng, không phải thao tác thủ công trên điện thoại.

1. Trên máy tính, ở gốc repo, chạy `python -X utf8 products/fe/experiment_mobile/coordinator.py dashboard --run 1 --headed` (đổi thành `--run 2` nếu đang thử run 2). Dùng đúng môi trường Python đã cài thư viện và mật khẩu admin hiện có.
2. Chờ công cụ kiểm tra xong. Quay lại **Cài đặt → Thực nghiệm E2E**, mở đúng run.
3. Bấm **Xác nhận đã chạy dashboard**. App lấy kết quả kiểm tra từ máy tính: PASS nếu đạt, FAIL nếu có lỗi, NOT_RUN nếu chưa có bằng chứng hợp lệ. Nút này không tự đánh dấu PASS khi bạn chưa chạy lệnh. Nếu kiểm tra trình duyệt bị lỗi giữa chừng, công cụ cũng lưu FAIL cùng mô tả.

**Lưu bằng chứng ở đâu?** Chụp màn hình điện thoại bằng nút chụp của Android và chép sang máy tính. Có thể tự tạo thư mục `products/fe/experiment_mobile/benchmarks/<tên_lượt>/manual-evidence/` để đặt ảnh và ghi chú ID bài/mô tả/thời điểm/run. Nếu dùng USB, lệnh `collect --run 1/2 --device DEVICE_ID` ở cuối mục 4 thu thêm logcat và ảnh màn hình hiện tại.

**Ghi lỗi Case 7/8:** bấm **Ghi kết quả Case 7/8**, nhập **Mô tả lỗi / ghi chú**, thêm ID bài và tên ảnh/video bằng chứng nếu có, rồi chọn **Có lỗi (FAIL)**. App bắt buộc có mô tả khi ghi FAIL. Chọn **Chưa kiểm tra** để đóng mà không thay đổi kết quả. Chỉ chọn **Đạt (PASS)** khi đã kiểm tra và lưu bằng chứng; lựa chọn này vẫn là xác nhận của người chạy, không tự chứng minh thao tác đã đúng.

Ghi nhận được lưu vào checkpoint trước, sau đó app gửi lên máy tính. Nếu mất kết nối lúc lưu, kết nối lại rồi bấm **Lưu JSON/CSV lên máy tính**. Không cần nhập lại lỗi. Tên ảnh/video là tham chiếu, không tự đính kèm file; bạn cần chép ảnh/video sang thư mục bằng chứng.

**CSV lỗi:** [loi_thu_cong_example.csv](loi_thu_cong_example.csv) là mẫu cột với ba dòng **VÍ DỤ, không phải lỗi thực tế**. Khi app lưu kết quả, công cụ tự tạo `results/<điện_thoại>/<tên_lượt>/loi_thu_cong.csv` cạnh JSON/CSV tổng hợp. Mỗi lỗi có các cột: mã ghi nhận, thời điểm UTC, benchmark, run, thiết bị, case, hạng mục, trạng thái, kết quả mong đợi, lỗi thực tế, ID báo cáo, tên file bằng chứng.

File `loi_thu_cong.csv` ghi các lần FAIL của Case 7/8 và lỗi kiểm tra dashboard Case 9. Xuất lại không tạo dòng trùng. Kiểm tra lại đạt sẽ cập nhật trạng thái hiện tại thành PASS nhưng vẫn giữ lỗi cũ trong lịch sử/CSV để truy vết. File mẫu không phải file nhập dữ liệu; sửa file mẫu không cập nhật kết quả app. Các lỗi app không được người chạy ghi nhận hoặc không qua công cụ dashboard thì không tự xuất hiện trong CSV.

Làm và ghi kết quả riêng cho từng run, sau đó bấm **Lưu JSON/CSV lên máy tính**.

## 4. Dashboard và kết quả

Ở PowerShell thứ hai tại gốc repo, kích hoạt môi trường như bước 2 rồi:

```powershell
python -X utf8 products/fe/experiment_mobile/coordinator.py dashboard --run 1 --headed
python -X utf8 products/fe/experiment_mobile/coordinator.py dashboard --run 2 --headed
```

Chạy sau khi từng run đã có báo cáo mobile. Trên app, chọn từng run và bấm **Xác nhận đã chạy dashboard** để cập nhật Case 9 và lưu kết quả mới nhất. Có thể xuất thêm JSON trên điện thoại.

Kết quả mới nằm tại:

```text
products/fe/experiment_mobile/
  results/<tên_điện_thoại>/<ngày_giờ_tênbenchmark>/
    <ngày_giờ_tênbenchmark>.json
    <ngày_giờ_tênbenchmark>.csv
    manifest.json
    loi_thu_cong.csv        # Lỗi thực tế, tự ghi khi lưu kết quả
    attempts/<thời_điểm_xuất>.json
  benchmarks/<ngày_giờ_tênbenchmark>/
    package.rhe, manifest.json, inputs/
    profiles.jsonl, traffic.jsonl, dashboard-checks.json
```

Giữ cả `results` và `benchmarks`. Bấm lưu nhiều lần cập nhật bản tổng hợp và giữ bản lịch sử trong `attempts`. File tồn tại không có nghĩa đã PASS toàn bộ; xem từng case và `automaticComplete`. `complete_with_gaps` vẫn còn NOT_RUN.

- **Dừng:** Ctrl+C ở cửa sổ công cụ. Docker flood-rescue vẫn chạy.
- **Tiếp tục lượt gần nhất:** `python -X utf8 products/fe/experiment_mobile/coordinator.py resume`.
- **Lượt mới:** chạy `start` lại; không phải build APK mới nếu model/dữ liệu không đổi. Thêm `--benchmark ten_khong_dau` nếu muốn tự đặt tên; ngày giờ tự thêm phía trước.
- **Cổng khác:** thêm `--backend-port`, `--dashboard-port`, `--proxy-port` vào start. APK phải kết nối đúng proxy khi đo mạng.
- **Lượt cũ:** thêm `--benchmark <tên_đầy_đủ>` vào dashboard/resume/collect. `--run 1` hoặc `--run 2` chọn run trong lượt.
- **ADB tùy chọn:** `python -X utf8 products/fe/experiment_mobile/coordinator.py collect --run 1 --device DEVICE_ID` lấy thông tin máy/logcat/ảnh màn hình. Chỉ bước này cần USB debugging và Android platform-tools.

## Cấu trúc và giới hạn

- `products/fe/experiment_mobile/`: script chuẩn bị assets, coordinator/proxy, tests và hướng dẫn.
- `products/fe/app/lib/`: code Dart/giao diện được Flutter biên dịch.
- `products/fe/app/assets/benchmarks/mobile/`: catalog, hai gói RHE1 schema 2, algorithm_input và run_manifest của hai run; không có timestamp, IP, mật khẩu hay ground truth.
- Run 1 dùng `high/flood_4800.jpg`, run 2 dùng `medium/flood_6286.jpg`; cùng dữ liệu nguồn với thực nghiệm web. Gói schema 2 cố định; tên lượt chỉ ghép vào bộ nhớ/checkpoint khi mở trên điện thoại.
- Model nhận diện vẫn là PTE seed1024 pruning, hash đối chiếu với assets/models/model_manifest.json. ONNX/tập benchmark model vẫn theo luồng riêng hiện có.
- Python/proxy vẫn chạy trên máy tính để giả lập mạng, kiểm chứng backend và lưu kết quả. Không đóng hoặc chạy Python trong APK. Dữ liệu trong assets không thay thế kết nối backend khi gửi bài.
- Database dùng chung vẫn giữ các báo cáo cũ. Bài mới được lọc theo tên benchmark; kết quả cụm/xếp hạng có thể chịu ảnh hưởng dữ liệu khác trong DB. Dashboard chỉ đọc các bài đúng lượt, feedback chỉ đổi bài online tương ứng.
- Offline HTTP 503 không chứng minh tắt Wi-Fi/4G thật. Traffic đo HTTP body, không phải mọi byte mạng. Đây là kiểm tra luồng hệ thống, không tính Accuracy từ hai ảnh.
- Kết quả/APK/venv cũ tại `thuc_nghiem_nq/experiment_mobile_e2e/` được giữ làm bằng chứng. Không trộn checkpoint cũ gắn gói schema 1 với lượt assets mới. Nếu đổi DB, sao lưu và xử lý hết pending trước khi xóa dữ liệu chỉ app Admin thử nghiệm; cài đè APK không xóa dữ liệu.

## Kiểm tra code

```powershell
python -X utf8 -m unittest discover -s products/fe/experiment_mobile/tests -v
cd products/fe/app
flutter test --flavor admin test/mobile_e2e_bundle_test.dart test/mobile_e2e_runner_test.dart test/mobile_e2e_card_test.dart
```

Kiểm thử code không thay thế lượt chạy E2E trên điện thoại thật.

## Cách mô tả phạm vi trong báo cáo

Phân biệt **kiểm thử luồng xử lý trên Android đến backend** (Case 1–6), **kiểm thử thao tác trên giao diện Android thật** (Case 7–8, do người chạy thực hiện) và **kiểm thử hiển thị trên dashboard** (Case 9, bằng Playwright). Tự động/thủ công chỉ mô tả cách thực hiện, không phải phạm vi kiểm thử. Bộ chạy hiện tại chưa tự động thao tác toàn bộ giao diện Android từ chọn ảnh đến xem trạng thái, nên không gọi là E2E tự động toàn bộ giao diện Android.
