# Thực nghiệm mạng yếu với 257 ảnh validation

**Trạng thái: bộ chạy đã được chuẩn bị; chưa chạy thực nghiệm.**

Dùng bản sao [weak_network.py](../experiment_weak_network/weak_network.py) trong `thuc_nghiem_nq/experiment_weak_network/`. Runner gốc `products/be/experiments/weak_network.py` được giữ nguyên.

Đầu vào mặc định: [split_val_mobilenetv3_large.csv](../split_val_mobilenetv3_large.csv). Runner đọc đúng 257 dòng val, tra ảnh bằng cột `relative_path` trong `products/fe/model/Dataset_Flood`, không sửa CSV hoặc ảnh nguồn.

## Cách làm

Các lệnh dưới đây dùng PowerShell. Cả hai cửa sổ đều đứng trong thư mục `experiment_weak_network`; lệnh backend dùng `--app-dir` để tìm code ở `products/be`.

### Bước 1. Chuẩn bị một lần

Tạo môi trường Python, cài thư viện và kiểm tra 257 ảnh:

```powershell
cd D:\nckh-flood-rescue\nckh2\thuc_nghiem_nq\experiment_weak_network
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe weak_network.py --check-inputs
```

Dùng Python 3.10 trở lên. Nếu máy dùng lệnh `py`, thay dòng tạo môi trường bằng `py -3 -m venv .venv`. Bước này không gửi request hoặc tạo kết quả thực nghiệm.

### Bước 2. Bật backend ở cửa sổ thứ nhất

Chỉ thực hiện khi sẵn sàng chạy thực nghiệm:

```powershell
cd D:\nckh-flood-rescue\nckh2\thuc_nghiem_nq\experiment_weak_network
$env:RESCUE_DB_FILE = "$PWD\data\weak_network.db"
$env:RESCUE_UPLOADS_DIR = "$PWD\uploads"
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir ..\..\products\be --host 127.0.0.1 --port 8001
```

Giữ cửa sổ này mở. Backend nhận dữ liệu tại cổng 8001 và lưu vào database/thư mục upload riêng của thực nghiệm.

### Bước 3. Chạy thực nghiệm ở cửa sổ thứ hai

Sau khi backend đã bật, mở một cửa sổ PowerShell khác:

```powershell
cd D:\nckh-flood-rescue\nckh2\thuc_nghiem_nq\experiment_weak_network
.\.venv\Scripts\python.exe weak_network.py --run
```

Runner gửi dữ liệu đến backend và tự tạo RUN_ID, manifest, log, CSV, báo cáo và checkpoint. Đường dẫn kết quả được in trên màn hình.

### Khi cần dừng hoặc chạy tiếp

Nhấn `Ctrl+C` trong cửa sổ runner để dừng. Thay `RUN_ID` dưới đây bằng tên lần chạy đã in trên màn hình; bật backend trước khi chạy tiếp:

```powershell
cd D:\nckh-flood-rescue\nckh2\thuc_nghiem_nq\experiment_weak_network
.\.venv\Scripts\python.exe weak_network.py --resume RUN_ID
```

Nếu chỉ muốn tạo lại bảng tổng hợp từ kết quả đã có, không cần bật backend:

```powershell
.\.venv\Scripts\python.exe weak_network.py --summarize-only RUN_ID
```

Xem thêm [hướng dẫn của bộ chạy](../experiment_weak_network/README.md) nếu cần chi tiết.

Không cần tự viết manifest, tạo nhiều biến hoặc chép RUN_ID giữa các bước. Chạy runner không có tham số chỉ hiện hướng dẫn.

## Kế hoạch và nơi lưu

Mặc định: **257 ảnh × 3 mạng × 3 chế độ × 1 lần/ảnh = 2.313 lượt**, chạy tuần tự. Metadata không gửi ảnh nhưng kết quả vẫn ghi ảnh tương ứng.

257 ảnh từ bộ dataset split: chỉ lấy tập dành cho validation

3 kiểu mạng: 2g, 3g, 4g

3 chế độ gửi:

	+chỉ gửi metadata: gửi thông tin báo cáo: vị trí GPS, thời gian, mô tả ngập,...,

	+gửi ảnh gốc: gửi thông tin báo cáo + file ảnh gốc lấy từ dataset, giữ nguyên định dạng và nội 			dung ảnh

	+gửi ảnh nén: Gửi thông tin báo cáo + bản ảnh đã nén sang JPEG chất lượng 60; ảnh lớn được giảm kích thước, ảnh nhỏ không phóng to.

- `experiment_weak_network/logs/<RUN_ID>/`: console, môi trường/cấu hình, bản sao CSV đầu vào và exit code.
- `experiment_weak_network/results/<RUN_ID>/weak_network.csv`: dữ liệu từng lượt.
- `experiment_weak_network/results/<RUN_ID>/weak_network.md`: bảng tổng hợp.
- `experiment_weak_network/checkpoints/<RUN_ID>.json`: tiến độ để tiếp tục.
- `experiment_weak_network/data/` và `uploads/`: dữ liệu riêng của backend thực nghiệm.

Hiện các thư mục lưu trữ chỉ có file giữ chỗ, chưa có kết quả đo.

## Lưu ý khi đọc kết quả

- `--resume RUN_ID` giữ dòng đo thô và chạy phần chưa có lượt hợp lệ; không chạy lại lỗi mạng đã đo hợp lệ.
- `--summarize-only RUN_ID` tạo lại báo cáo từ kết quả đã lưu, không cần backend hoặc ảnh nguồn.
- Dataset có một ảnh AVIF. Backend hiện từ chối AVIF gốc; runner vẫn thử và ghi lỗi định dạng riêng, không tự đổi hoặc bỏ ảnh.
- Median/p95 chỉ tính lượt thành công; tỷ lệ thành công bao gồm mọi nguyên nhân. Không diễn giải HTTP 415 là lỗi mạng.
- Đây là giả lập TCP trên máy tính, không chạy giao diện Flutter, MobileNetV3 hoặc mạng di động thật.
- Điều kiện hoàn tất: đủ 2.313 lượt hợp lệ duy nhất, checkpoint `complete`, exit code `0`. Resume lượt quá tải có thể làm số dòng đo thô lớn hơn 2.313.
