# NCKH - Flood Rescue

Ứng dụng cứu hộ offline-first gồm:

- **Flutter UI**: chụp/chọn ảnh, nhận diện ngập trên thiết bị, lưu hàng đợi offline và gửi báo cáo khi có mạng.
- **Server API**: nhận báo cáo multipart và cung cấp file probe để đo throughput.
- **Model training**: notebook MobileNetV3 Large trong `model/1706.ipynb`.

## Cấu trúc chính

```text
app/                 Flutter application
model/1706.ipynb     Notebook train/evaluate model
model/Dataset_Flood/ Dataset ảnh train
models/              Config model
requirements.txt     Dependencies Python cho notebook
```

## 1. Cài đặt môi trường

### Flutter

Cài Flutter SDK phù hợp với Dart SDK trong `app/pubspec.yaml` (`^3.12.2`), Android Studio nếu chạy Android, và Visual Studio với workload **Desktop development with C++** nếu chạy Windows.

Kiểm tra:

```powershell
flutter doctor
```

Cài dependencies của app:

```powershell
cd app
flutter pub get
```

### Python và môi trường train

Khuyến nghị Python 3.10 hoặc mới hơn trong virtual environment:

```powershell
cd <thu-muc-repo>
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m ipykernel install --user --name nckh-flood
```

Mở `model/1706.ipynb` bằng VS Code/Jupyter và chọn kernel `nckh-flood`.

### Máy có NVIDIA GPU

Cài NVIDIA driver trước, sau đó kiểm tra driver:

```powershell
nvidia-smi
```

Trong virtual environment, cài PyTorch với CUDA wheel trước khi cài phần dependencies còn lại. Chọn CUDA wheel phù hợp với driver theo hướng dẫn chính thức của PyTorch; ví dụ:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
python -m pip install -r requirements.txt
```

Nếu `pip install -r requirements.txt` thay thế PyTorch bằng wheel khác, chạy lại lệnh cài CUDA ở trên sau cùng. Kiểm tra PyTorch đã nhận GPU:

```powershell
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA build:', torch.version.cuda); print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

Kết quả cần có `CUDA available: True`. Khi đó notebook tự chọn:

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
```

Nếu kết quả là `False`, thường là do driver không tương thích, cài nhầm CPU wheel, hoặc kernel Jupyter đang dùng Python environment khác. Trong VS Code, chọn đúng interpreter `.venv` và chọn lại kernel `nckh-flood`.

`nvidia-smi` hiển thị phiên bản CUDA driver tối đa được hỗ trợ, không nhất thiết phải cài CUDA Toolkit riêng cho pip wheel. Không cài `torch` bản CPU sau khi đã cài CUDA wheel.

## 2. Chạy UI Flutter

### Windows desktop

```powershell
cd app
flutter devices
flutter run -d windows
```

Nếu gặp lỗi `Building with plugins requires symlink support`, bật Windows Developer Mode:

```powershell
start ms-settings:developers
```

Trong cửa sổ Settings, bật **Developer Mode**, đóng/mở lại terminal rồi chạy lại:

```powershell
cd app
flutter clean
flutter pub get
flutter run -d windows
```

Tài khoản Windows cần có quyền tạo symbolic link. Nếu máy thuộc chính sách quản trị của công ty/trường học và không bật được Developer Mode, hãy nhờ quản trị viên cấp quyền hoặc chạy VS Code/terminal với tài khoản được cấp quyền phù hợp.

### Android emulator

Khởi động emulator, sau đó:

```powershell
cd app
flutter devices
flutter run -d <device-id>
```

Trong Android emulator, server chạy trên máy host được tham chiếu bằng `10.0.2.2`. Giá trị mặc định hiện tại là:

```dart
// app/lib/config.dart
const String kServerBaseUrl = 'http://10.0.2.2:8000';
```

### Điện thoại thật

Đây là cách kiểm thử gần với thiết bị thực tế nhất. Cần cài Android Studio và Android SDK trước, sau đó chạy:

```powershell
flutter doctor --android-licenses
flutter doctor
```

Trên điện thoại Android:

1. Mở **Settings > About phone**.
2. Nhấn **Build number** 7 lần để bật Developer options.
3. Vào **Developer options**, bật **USB debugging**.
4. Kết nối điện thoại với máy tính bằng cáp USB và chấp nhận hộp thoại cho phép debugging.

Kiểm tra thiết bị:

```powershell
cd app
flutter devices
```

Sau khi thấy tên điện thoại, chạy bằng device ID:

```powershell
flutter run -d <device-id>
```

Điện thoại và máy chạy server phải ở cùng mạng LAN. Đổi `kServerBaseUrl` trong `app/lib/config.dart` thành IP LAN của máy server, ví dụ:

```dart
const String kServerBaseUrl = 'http://192.168.1.20:8000';
```

Server cần lắng nghe trên `0.0.0.0:8000` và Windows Firewall phải cho phép cổng `8000`. Sau đó chạy lại app. Không dùng `localhost` trên điện thoại vì nó trỏ về chính điện thoại.

### Model dùng trong UI

App tìm model tại:

```text
app/assets/models/model.onnx
app/assets/labels.json
```

Nếu thiếu `model.onnx`, app vẫn mở để kiểm thử flow lưu/gửi, nhưng inference sẽ trả về `null`. Sau khi export model, tạo thư mục `app/assets/models/`, chép file ONNX vào đó và chạy lại `flutter pub get`/`flutter run`.

`labels.json` phải có thứ tự lớp đúng với output của ONNX. Hiện file đang có:

```json
["low", "medium", "high", "non_flood"]
```

Preprocessing của app là resize `224x224`, tensor `NCHW`, normalize theo ImageNet mean/std. Khi train/export phải giữ đúng preprocessing này.

## 3. Chạy server

Hiện repository **chưa có source server**. App chỉ quy định API contract sau; cần chạy server backend riêng tại `kServerBaseUrl`.

### API contract bắt buộc

#### `GET /probe`

- Trả về HTTP `200`.
- Body là file hoặc bytes tĩnh khoảng 64 KB.
- App dùng endpoint này một lần trước khi gửi để đo throughput.

Ví dụ kiểm tra:

```powershell
curl http://localhost:8000/probe -o $null
```

#### `POST /api/reports`

Request là `multipart/form-data`:

- `meta`: chuỗi JSON của một `RescueRecord`.
- `image`: file JPEG, tùy chọn. Không có `image` là trường hợp gửi text-only hoặc server yếu.

Các trường chính trong `meta` gồm `id`, `createdAtMs`, `label`, `confidence`, `lat`, `lng`, `note`, `mode`, `status`, `bytesOriginal`, `bytesSent`, `durationUploadMs`, `durationInferenceMs`, `networkType`, `throughputKbps` và `attempts`.

Server nên trả HTTP `2xx` khi lưu thành công. App coi lỗi mạng hoặc status ngoài `2xx` là upload thất bại và giữ bản ghi ở trạng thái pending để retry.

Ví dụ kiểm tra endpoint sau khi server đã chạy:

```powershell
curl http://localhost:8000/probe -Method GET
```

Đối với Android emulator, server cần lắng nghe trên `0.0.0.0:8000`, không chỉ `127.0.0.1:8000`, nếu app không kết nối được.

## 4. Train model

1. Đặt dataset theo cấu trúc notebook yêu cầu. Dataset hiện có các thư mục:

   ```text
   model/Dataset_Flood/high/
   model/Dataset_Flood/low/
   model/Dataset_Flood/medium/
   model/Dataset_Flood/non_flood/
   ```

2. Mở `model/1706.ipynb` và chạy lần lượt các cell từ config, làm sạch/chia dataset, train, evaluate đến export.
3. Kiểm tra các kết quả cần lưu: checkpoint, class order, transform, classification report và confusion matrix.
4. Convert checkpoint PyTorch (`.pth`) sang ONNX với input shape `[1, 3, 224, 224]` và output xác suất theo đúng class order.
5. Chép file export vào `app/assets/models/model.onnx`.
6. Cập nhật `app/assets/labels.json` nếu class order của model khác file hiện tại.
7. Chạy lại UI và kiểm tra một ảnh mẫu ở cả trường hợp offline và online.

Notebook đã thiết kế để lưu metadata của split, transform và class order. Không nên chỉ đổi tên `.pth` thành `.onnx`; cần thực hiện export thật bằng PyTorch/ONNX và kiểm tra output trước khi đưa vào app.

## 5. Kiểm tra nhanh

Chạy unit test Dart:

```powershell
cd app
flutter test
```

Phân tích mã nguồn:

```powershell
cd app
flutter analyze
```

Build Windows:

```powershell
cd app
flutter build windows
```

## 6. Luồng hoạt động

1. UI nhận ảnh từ camera/thư viện.
2. Model ONNX phân loại ngay trên thiết bị, không cần mạng.
3. App đo loại mạng và throughput qua `/probe`.
4. App chọn gửi text-only, ảnh nén hoặc ảnh gốc tùy confidence và chất lượng mạng.
5. App gửi multipart tới `/api/reports`.
6. Khi mất mạng, bản ghi được lưu local bằng Hive và retry khi có mạng.
7. Android có thể dùng SMS fallback nếu upload không thực hiện được.

## Lưu ý triển khai

- Thay `kEmergencyPhone` trong `app/lib/config.dart` bằng số tổng đài thật trước khi thử SMS fallback.
- Không commit secret, token hoặc thông tin kết nối production vào source code.
- Với production, dùng HTTPS và xác thực request ở server.
- Kiểm tra lại mapping class giữa dataset, ONNX output và `labels.json`; sai mapping sẽ cho kết quả hiển thị sai dù model vẫn chạy.
