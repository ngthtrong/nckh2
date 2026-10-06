# Thực nghiệm mạng yếu với 257 ảnh validation

**Trạng thái: đã chuẩn bị, chưa chạy thực nghiệm.**

Runner ở đây là bản sao đã sửa của `products/be/experiments/weak_network.py`. File code gốc được giữ nguyên. CSV và ảnh nguồn cũng được giữ nguyên.

Đầu vào mặc định là `../split_val_mobilenetv3_large.csv`. Runner đọc toàn bộ 257 dòng `val`, tra ảnh bằng `relative_path` trong `../../products/fe/model/Dataset_Flood`. Không dùng đường dẫn `/content/...` của Colab và không lọc bỏ ảnh nhỏ.

## Thư mục đã chuẩn bị

```text
experiment_weak_network/
├── weak_network.py
├── requirements.txt
├── README.md
├── logs/          # output màn hình, manifest, bản sao CSV đầu vào
├── results/       # CSV đo và báo cáo tổng hợp
├── checkpoints/   # tiến độ để chạy tiếp
├── data/          # database riêng của backend thực nghiệm
├── uploads/       # ảnh backend nhận trong thực nghiệm
└── tests/         # kiểm tra code cục bộ; không gửi request
```

`logs`, `results`, `checkpoints`, `data`, `uploads` hiện chỉ có file giữ chỗ `.gitkeep`. Chưa có dữ liệu đo hoặc checkpoint của một lần chạy.

## 1. Chuẩn bị môi trường — làm một lần

Dùng Python 3.10 trở lên. Mở cửa sổ PowerShell mới và chạy đủ các dòng dưới đây. Nếu terminal hiện tại đang kích hoạt `.venv` của `products/be`, cửa sổ mới giúp dùng đúng môi trường riêng của thực nghiệm.

Lệnh `python weak_network.py` tìm file trong thư mục đang đứng. Hãy đứng ở `thuc_nghiem_nq/experiment_weak_network`, không phải `products/be`; đồng thời cài `requirements.txt` của thư mục thực nghiệm để có Pillow.

```powershell
cd D:\nckh-flood-rescue\nckh2\thuc_nghiem_nq\experiment_weak_network
python -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe weak_network.py --check-inputs
```

`--check-inputs` chỉ kiểm tra CSV, MD5 nếu có, khả năng đọc ảnh và tạo bản nén trong bộ nhớ. Nó không mở backend/proxy, không gửi request và không tạo log/kết quả/checkpoint. Kết quả dự kiến: đọc đủ 257 ảnh, kế hoạch gồm 2.313 lượt.

Nếu máy chỉ có lệnh `py`, dùng `py -3 -m venv .venv` thay cho dòng tạo môi trường. Không cần kích hoạt môi trường vì các lệnh gọi trực tiếp Python trong `.venv`.

## 2. Mở backend — chỉ khi sẵn sàng chạy thực nghiệm

Trong PowerShell thứ nhất, vẫn ở thư mục này:

```powershell
cd D:\nckh-flood-rescue\nckh2\thuc_nghiem_nq\experiment_weak_network
- Chọn nơi lưu db của thực nghiệm
- PWD là thư mục đang đứng hiện tại
$env:RESCUE_DB_FILE = "$PWD\data\weak_network.db"

- Chọn nơi lưu ảnh server nhận được
$env:RESCUE_UPLOADS_DIR = "$PWD\uploads"
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir ..\..\products\be --host 127.0.0.1 --port 8001
```

Giữ cửa sổ này mở. Backend dùng database và thư mục upload riêng vừa chỉ định.

## 3. Chạy và xem kết quả — chỉ khi đã mở backend

Mở PowerShell thứ hai trong cùng thư mục:

```powershell
cd D:\nckh-flood-rescue\nckh2\thuc_nghiem_nq\experiment_weak_network
.\.venv\Scripts\python.exe weak_network.py --run
```

Runner tự tạo `RUN_ID`, in đường dẫn kết quả, ghi log và checkpoint. Không cần tự tạo manifest hoặc chép RUN_ID giữa các bước. Chạy không có tham số chỉ hiện hướng dẫn; không bắt đầu đo.

Mặc định: **257 ảnh × 3 mạng × 3 chế độ × 1 lần/ảnh = 2.313 lượt đo**, chạy tuần tự. Chế độ metadata không truyền ảnh nhưng vẫn ghi ảnh tương ứng để đối chiếu. Muốn đổi số lần lặp, thêm `--repeats N` ngay từ lần chạy mới và giữ nguyên khi resume.

Các cấu hình là do nhóm lựa chọn: 2G (50 kbit/s, RTT 600 ms), 3G (400 kbit/s, RTT 200 ms), 4G (5.000 kbit/s, RTT 50 ms). Timeout metadata 30 s; ảnh nén và ảnh gốc 60 s. Đây là giả lập trên máy tính; runner không chạy Flutter hoặc MobileNetV3.

Sau khi thực sự chạy, dữ liệu nằm ở:

```text
logs/<RUN_ID>/
  console.txt            # toàn bộ output của runner
  manifest.json          # cấu hình, môi trường, SHA256 source/CSV/ảnh
  input_validation.csv   # bản sao nguyên byte của CSV nguồn
  git_status.txt
  exit_code.txt
results/<RUN_ID>/
  weak_network.csv       # từng lượt đo, gồm cả thất bại và lượt quá tải
  weak_network.md        # tỷ lệ thành công, median, p95, các loại lỗi
checkpoints/<RUN_ID>.json
```

`exit_code = 0` và checkpoint `status = complete` nghĩa là đã có đủ lượt hợp lệ, không có nghĩa mọi request đều thành công. Báo cáo còn ghi số lượt thực tế/số lượt cần có. Lần chạy đầu đầy đủ có 2.313 dòng dữ liệu; resume các lượt quá tải có thể thêm dòng `attempt`, nhưng bảng chỉ lấy một lượt hợp lệ cho mỗi điều kiện.

## Dừng, chạy tiếp, tổng hợp lại

Nhấn `Ctrl+C` để dừng và giữ phần đã ghi. Dùng đúng RUN_ID đã in trên màn hình:

```powershell
cd D:\nckh-flood-rescue\nckh2\thuc_nghiem_nq\experiment_weak_network
.\.venv\Scripts\python.exe weak_network.py --resume RUN_ID
.\.venv\Scripts\python.exe weak_network.py --summarize-only RUN_ID
```

Resume đọc CSV kết quả để xác định phần còn thiếu, kiểm tra cấu hình và checksum trước khi ghép dữ liệu. Nó không xóa dòng đo thô hoặc chạy lại một lỗi mạng đã được đo hợp lệ. Nếu đổi CSV/ảnh/source/server/cấu hình, tạo lần chạy mới. Tổng hợp lại không cần backend hoặc ảnh đầu vào.

## Cách đọc đúng kết quả

- `original` gửi nguyên byte và đúng định dạng ảnh; `compressed` tạo JPEG quality 60. Không phóng to ảnh nhỏ; nén lại có thể làm một số ảnh nhỏ tăng dung lượng.
- Dataset có 224 JPEG, 6 PNG, 26 WebP và 1 AVIF theo định dạng thực tế. Backend hiện từ chối AVIF gốc: vẫn thử và ghi `UNSUPPORTED_IMAGE`/HTTP 415 riêng. Không đổi ảnh AVIF gốc thành JPEG hoặc tự bỏ ảnh để làm đẹp tỷ lệ thành công.
- Metadata chỉ thành công khi backend ACK đúng message và trạng thái nhận hợp lệ, trong thời hạn; không chỉ dựa vào HTTP 200.
- `image_bytes` là dung lượng ảnh cần gửi. `wire_bytes_up` là byte proxy đã chuyển vào socket backend, có cả header HTTP; khi timeout nó có thể chỉ là một phần request.
- Median/p95 chỉ tính lượt thành công. Tỷ lệ thành công tính mọi nguyên nhân; lỗi định dạng không được diễn giải thành lỗi mạng.
- Windows không có `os.getloadavg()`: cột `load1` để trống, không giả thành 0. WSL/Linux có số đo này thì loại lượt quá tải khỏi bảng và dùng resume để đo lại; dữ liệu thô vẫn được giữ.

Yêu cầu Pillow để đọc ảnh AVIF được chọn theo [tài liệu Pillow](https://pillow.readthedocs.io/en/stable/releasenotes/11.3.0.html#avif-support-in-wheels). Môi trường và byte ảnh nén được ghi vào manifest khi chạy để kiểm tra tính nhất quán.
