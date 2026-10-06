# Thực nghiệm end to end

**Trạng thái: đã chuẩn bị, chưa chạy E2E.** Đây là bản sao riêng của runner demo; code, CSV, ảnh và 80 gold run ở vị trí gốc vẫn được giữ nguyên.

Runner kiểm tra luồng app Flutter web → backend → dashboard với Playwright. Backend được nạp một bộ báo cáo bán tổng hợp từ `thucnghiem/data/gold/run_NNN/algorithm_input.json`. `run_manifest.json` của cùng run dùng để xác nhận danh tính, seed và xuất xứ bộ dữ liệu; nó **không** chứa các báo cáo được nạp. Ảnh của bài cứu hộ đến từ **một dòng** `split=val`, `label=high`, JPG/JPEG trong `../split_val_mobilenetv3_large.csv`; mặc định lấy dòng hợp lệ đầu tiên theo thứ tự CSV, kiểm tra MD5 rồi dùng cùng ảnh cho các chế độ mạng. Đây là phạm vi kiểm tra của runner E2E gốc, không phải đánh giá hết 257 ảnh validation.

## File và thư mục

```text
experiment_e2e/
  e2e_system.py       # bản sao runner gốc, điểm chạy chính; [CHỈNH SỬA]/[BỔ SUNG] đánh dấu thay đổi
  docker-compose.yml  # bản sao Compose gốc, dùng project và volume riêng mỗi RUN_ID
  requirements.txt    # bản sao dependency Playwright
  backend_requirements.txt, seed_demo.py, entrypoint.sh  # bản sao phụ thuộc khởi động backend
  docker/             # bản sao 3 Dockerfile mà Compose thực nghiệm sử dụng
  logs/               # console, Docker log, manifest, bản sao CSV
  results/            # từng tiêu chí CSV, summary JSON, ảnh màn hình
  checkpoints/        # JSON tiến độ từng kịch bản
  data/               # bản sao gold input, gold manifest, ảnh đã chọn của mỗi lần chạy
  uploads/            # ảnh gốc và ảnh nén backend đã nhận
```

Backend, dashboard và frontend là **hệ thống cần kiểm tra**. Compose dùng ba bản sao Dockerfile trong `docker/` và build context `../..` để đọc mã sản phẩm tại `../../products/`. Backend image dùng bản sao `seed_demo.py`, `entrypoint.sh` và `backend_requirements.txt` ở đây. Không sửa code sản phẩm hoặc 80 gold run. Các file nguồn app/backend còn lại vẫn là hệ thống được kiểm tra, không phải bộ điều khiển thực nghiệm nên không nhân bản toàn bộ.

## Chuẩn bị và chạy Chromium

Cần Python 3.10+, Docker Desktop đang chạy và Playwright. Mở PowerShell trong thư mục này:

```powershell
cd D:\nckh-flood-rescue\nckh2\thuc_nghiem_nq\experiment_e2e
python -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe e2e_system.py --check-inputs
```

Lệnh `playwright install chromium` tải Chromium dành riêng cho Playwright. Runner tự mở và đóng trình duyệt khi chạy; không cần tự gõ lệnh mở Chrome. Mặc định Chromium chạy ẩn (headless). Để nhìn trình duyệt thao tác, thêm `--headed` vào lệnh chạy ở dưới.

Nếu muốn dùng Google Chrome đã cài trên Windows, có thể lấy đường dẫn và kiểm tra nó trong PowerShell:

```powershell
$pf86 = (Get-Item 'Env:ProgramFiles(x86)' -ErrorAction SilentlyContinue).Value
$chromeCandidates = @()
if ($env:ProgramFiles) { $chromeCandidates += Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe' }
if ($pf86) { $chromeCandidates += Join-Path $pf86 'Google\Chrome\Application\chrome.exe' }
$chromeCandidates = $chromeCandidates | Where-Object { Test-Path $_ }
$chrome = $chromeCandidates | Select-Object -First 1
if (-not $chrome) { throw 'Không tìm thấy Google Chrome; dùng Chromium của Playwright thay thế.' }
$chrome
```

Truyền đường dẫn vừa tìm được bằng `--chrome` để runner dùng Chrome thay Chromium của Playwright. Thêm `--headed` nếu muốn cửa sổ Chrome hiện trên màn hình. `--check-inputs` chỉ đọc CSV, ảnh và gold run để kiểm tra đường dẫn, số báo cáo và checksum; lệnh này không khởi động Docker hay trình duyệt.

## Chạy thực nghiệm E2E

Mở Docker Desktop và chờ engine khởi động. Xác nhận các lệnh sau đều trả về thông tin phiên bản/trạng thái:

```powershell
docker --version
docker compose version
docker info
```

Chạy một thực nghiệm với Chromium của Playwright:
python -m venv .venv
.\.venv\Scripts\Activate.ps1


```powershell
.\.venv\Scripts\python.exe e2e_system.py --run --seed-run 1
```

Muốn quan sát Chromium hiện trên màn hình:

```powershell
.\.venv\Scripts\python.exe e2e_system.py --run --seed-run 1 --headed
```

Hoặc chạy bằng Google Chrome đã cài (sau khi chạy đoạn PowerShell tìm `$chrome` ở trên):

```powershell
.\.venv\Scripts\python.exe e2e_system.py --run --seed-run 1 --chrome "$chrome" --headed
```

Lệnh này tự tạo `RUN_ID`, build và mở ba dịch vụ trên cổng 18000/18080/18081, seed **đúng run_001** vào volume riêng, kiểm tra đủ ID báo cáo seed, rồi chạy tuần tự năm kịch bản: dashboard, app gồm online/offline, mạng 300 kbit/s, mạng 20 kbit/s, không GPS. Sau khi chạy xong, runner dừng container và **giữ volume** để vẫn có thể kiểm tra dữ liệu. Nếu đang lỗi, container được giữ để xem log và tiếp tục. Chỉ một lần chạy tại một thời điểm trên bộ cổng mặc định; có thể đổi bằng `--be-port`, `--dashboard-port`, `--fe-port` khi bắt đầu lần chạy mới.

Thông thường chỉ chạy lệnh `e2e_system.py --run`; runner tự gọi Docker Compose. Không cần mở thêm terminal để chạy `docker compose up`.

### Nếu Flutter build báo `Icons`, `Colors`, `Widget` không tồn tại

`docker/fe.Dockerfile` trong thư mục thực nghiệm xóa `.dart_tool` và cấu hình plugin được chép từ Windows rồi tạo lại package config bằng Flutter SDK Linux trong container. Nếu đã chạy Docker trước khi có thay đổi này, chạy lại lệnh E2E ở trên để build lại image. Thông báo `docker compose ps` không có container sau khi build lỗi là bình thường: dịch vụ chưa được tạo. Stack demo cũ dùng cổng 8000/8080/8081; E2E dùng 18000/18080/18081 nên không cần tắt stack đó.

Chọn run khác bằng `--seed-run N` với N từ 1 đến 80; ví dụ `--seed-run 40`. Mỗi lệnh `--run` sinh một `RUN_ID` và Docker volume riêng. Khi muốn chọn ảnh khác, `--image-relative-path "high/ten_anh.jpg"` chỉ chấp nhận một dòng high/JPG thuộc **chính CSV validation**. Các đường dẫn cần thay đổi về sau được ghi rõ ở đầu `e2e_system.py`: `GOLD_DIR`, `CSV_PATH`, `IMAGE_ROOT`, `LOGS_DIR`, `RESULTS_DIR`, `CHECKPOINTS_DIR`, `DATA_DIR`, `UPLOADS_DIR`.

Chạy 40 hay 80 gold run là quyết định thiết kế đánh giá của nhóm; runner không tự chạy hàng loạt và hiện chưa có kết quả của 40/80 run. Một run chỉ cho thấy chức năng E2E hoạt động trong một kịch bản seed. Nếu báo cáo nghiên cứu muốn đánh giá độ ổn định trên nhiều bộ dữ liệu bán tổng hợp, cần chạy nhiều run và tổng hợp tỷ lệ PASS/FAIL theo run; đừng diễn giải một run như kết quả của cả 80.

## Tiếp tục khi bị gián đoạn

Sau khi bắt đầu, RUN_ID được in trên màn hình và lưu tại `logs/<GOLD_RUN>__<RUN_ID>/manifest.json`. Ví dụ:

```powershell
.\.venv\Scripts\python.exe e2e_system.py --resume e2e-20261004-120000-123456
```

Checkpoint ghi sau khi **mỗi kịch bản** hoàn tất. Resume bỏ qua kịch bản đã đạt và chạy lại kịch bản bị dừng giữa chừng. Những báo cáo E2E đã gửi trong kịch bản dở có thể còn trong DB; runner ghi nhận ID đã có trước thao tác để chỉ đối chiếu báo cáo mới ở lần thử lại. Không xóa volume Docker giữa `--run` và `--resume`. Runner so sánh SHA256 của runner, Compose, các bản sao file phụ thuộc, CSV, ảnh và hai file gold; nếu đầu vào đã đổi hoặc DB thiếu báo cáo seed, nó dừng và yêu cầu tạo lần chạy mới. Khi dùng mật khẩu quản trị tùy chỉnh, truyền lại cùng `--password` hoặc biến môi trường trên lệnh `--resume`. Nếu không có cụm chờ xử lý sau một lần thử dashboard dở, cần bắt đầu RUN_ID mới.

## Đọc kết quả

```text
logs/<GOLD_RUN>__<RUN_ID>/manifest.json       # gold run, ảnh CSV, checksum, cổng, project
logs/<GOLD_RUN>__<RUN_ID>/console.txt         # từng tiêu chí PASS/FAIL/CHƯA CÓ và lỗi
logs/<GOLD_RUN>__<RUN_ID>/docker_up_attempt_N.txt   # build/khởi động Docker, giữ từng lần thử
logs/<GOLD_RUN>__<RUN_ID>/docker_logs_attempt_N.txt # log 3 container theo lần thử
logs/<GOLD_RUN>__<RUN_ID>/docker_ps_attempt_N.txt   # trạng thái container theo lần thử
logs/<GOLD_RUN>__<RUN_ID>/input_validation.csv      # bản sao CSV nguồn
logs/<GOLD_RUN>__<RUN_ID>/git_head.txt, git_status.txt # trạng thái mã nguồn khi bắt đầu
logs/<GOLD_RUN>__<RUN_ID>/exit_code.txt       # 0 hoàn tất, 1 lỗi/dừng
results/<GOLD_RUN>__<RUN_ID>/checks.csv      # mỗi tiêu chí đã hoàn tất
results/<GOLD_RUN>__<RUN_ID>/summary.json    # tổng PASS/FAIL/CHƯA CÓ và 5 stage
results/<GOLD_RUN>__<RUN_ID>/screenshots/   # ảnh minh chứng giao diện
checkpoints/<GOLD_RUN>__<RUN_ID>.json # stage đã hoàn tất và kích thước ảnh gốc
data/<GOLD_RUN>__<RUN_ID>/           # snapshot hai file gold và ảnh CSV
uploads/<GOLD_RUN>__<RUN_ID>/        # ảnh server nhận ở chế độ full/compressed
```

Thư mục kết quả có dạng `results/run_001__e2e-<thời_gian>/`, nên tên đã thể hiện gold run nào được dùng; `RUN_ID` vẫn được dùng cho log, checkpoint, snapshot dữ liệu và lệnh resume. `summary.json` chỉ tính các kịch bản **đã hoàn tất**. Muốn kết luận một lần chạy đạt toàn bộ, cần `status=complete`, `stage_count=5`, mọi stage có mặt và `FAIL=0`; `CHƯA CÓ` là chức năng còn thiếu được tách riêng. Số `46/46` trong đối chiếu trước là số tiêu chí lịch sử, không tự động là kết quả của runner này; phải đọc `checks.csv` thực tế của lần chạy và ghi rõ gold run, ảnh, code, môi trường. Không sử dụng `--check-inputs` như bằng chứng E2E đạt.

Dataset gold chứa **báo cáo JSON bán tổng hợp** được seed vào DB; `has_image`/`image_id` trong gold là mô tả giả định và không tạo bitmap ảnh. Ảnh validation là đầu vào độc lập dùng riêng cho bước upload qua app. Vì vậy hãy ghi hai nguồn dữ liệu riêng trong báo cáo.
