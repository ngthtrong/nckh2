# Shared Flutter Android/Web UI Design

## Mục tiêu

`fe/app` là ứng dụng Flutter duy nhất và là nguồn giao diện duy nhất. Mọi thay đổi trong `fe/app/lib/presentation/` phải xuất hiện trên cả Android và Chrome. Chrome được dùng để xem, kiểm tra và chỉnh GUI nhẹ hơn Android Emulator, nhưng các luồng dữ liệu vẫn dùng implementation thật, không mock hoặc no-op.

Hai lệnh đích sau phải chạy cùng một source:

```powershell
cd fe/app
flutter run -d emulator-5554
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

## Hiện trạng đã xác minh

### Source Android

- `flutter analyze` không phát hiện import tương đối bị sai hoặc file Dart bị thiếu.
- Analyzer hiện có năm cảnh báo lint không chặn build.
- `pubspec.yaml` khai báo `assets/models/`, nhưng thư mục này chưa tồn tại.
- Build Android thất bại khi bật Kotlin incremental vì Pub cache nằm trên ổ `C:` còn repository nằm trên ổ `D:`. Cấu hình `kotlin.incremental=false` phải được giữ lại cho môi trường hiện tại.
- Model thật đang tồn tại ở các vị trí khác:
  - ONNX: `web_fullstack/frontend/web/models/flood_mobilenetv3_large.onnx`
  - PTE: `fe/model/Edge Ai/flood_mobilenetv3_large.pte`
  - manifest web: `web_fullstack/frontend/web/models/model_manifest.json`

### Build Chrome của `fe/app`

Build thất bại có thể tái hiện được tại chuỗi import:

```text
main.dart
→ inference_local_datasource.dart
→ package:onnxruntime 1.4.1
→ dart:ffi
```

`dart:ffi` không có trên Chrome. Các điểm phụ thuộc nền tảng khác gồm:

- `main.dart`: WorkManager.
- `app_controller.dart`: `dart:io` và permission Android.
- `inference_local_datasource.dart`: `dart:io`, path provider, ONNX FFI và MethodChannel ExecuTorch.
- `rescue_repository_impl.dart`, `compose_screen.dart`, `post_card.dart`: truy cập ảnh bằng `File`.

Đây là lỗi phân tách nền tảng, không phải lỗi đường dẫn import. Không được sửa bằng cách tắt AI hoặc bỏ chức năng trên web.

## Các phương án

### Phương án chọn: một Flutter app với adapter theo nền tảng

Giữ UI, controller, domain và use case trong `fe/app`. Những phần chạm trực tiếp Android hoặc trình duyệt được đặt sau interface chung và chọn bằng conditional import/export.

Ưu điểm:

- Chỉ có một giao diện để sửa.
- Android và Chrome dùng cùng navigation, màn hình, widget và trạng thái.
- Native Android vẫn giữ ONNX FFI, ExecuTorch và WorkManager.
- Chrome dùng ONNX Runtime Web, IndexedDB và browser events thật.
- Có thể kiểm thử độc lập từng adapter.

### Không chọn: package UI dùng chung cho hai app

Tách UI thành package riêng rồi để `fe/app` và `web_fullstack/frontend` cùng phụ thuộc. Cách này vẫn để lại hai entrypoint, hai controller và hai dependency graph; dễ lệch hành vi và tăng công bảo trì.

### Loại bỏ: hai frontend độc lập

Đây là cấu trúc hiện tại của `web_fullstack/frontend`. Nó làm giao diện web và Android lệch nhau, trái với mục tiêu dùng Chrome để chỉnh giao diện Android.

## Kiến trúc đích

```text
fe/app/lib
├── main.dart
├── presentation/                 # dùng chung hoàn toàn
├── domain/                       # entity, repository contract, use case dùng chung
├── data/
│   ├── repositories/             # orchestration dùng chung
│   └── datasources/
│       ├── inference/            # facade + native/web adapter
│       ├── image/                # XFile/bytes, không để UI dùng dart:io
│       ├── location/             # Android và browser permission thật
│       ├── storage/              # Hive native / IndexedDB-backed Hive web
│       ├── sender/               # API upload dùng chung
│       └── background_sync/      # WorkManager / browser online events
└── platform/                     # conditional exports và bootstrap
```

`web_fullstack/backend` và `web_fullstack/model_tools` vẫn là các thành phần độc lập cần thiết. `web_fullstack/frontend` chỉ là nguồn tạm để chuyển adapter, test và asset web vào `fe/app`; sau khi parity được xác minh, frontend trùng này sẽ bị xóa.

## Ranh giới dùng chung và theo nền tảng

### Dùng chung 100%

- Tất cả màn hình và widget trong `presentation/`.
- `AppController` và trạng thái hiển thị, sau khi loại bỏ truy cập `File`/permission trực tiếp.
- Entity, repository contract và use case.
- Navigation, theme, validation form, lịch sử, đăng nhập và cài đặt.
- HTTP contract với backend.

### Adapter Android thật

- ONNX bằng `onnxruntime` FFI.
- PTE bằng MethodChannel/ExecuTorch.
- WorkManager cho đồng bộ nền.
- Permission Android và file persistence native.

### Adapter Chrome thật

- ONNX Runtime Web bằng JavaScript interop và WASM/WebGPU đã có.
- Hive CE/IndexedDB cho dữ liệu offline.
- `online`/`offline` browser events để đồng bộ khi tab đang hoạt động.
- Geolocator và ImagePicker web với permission thật của trình duyệt.
- Gửi báo cáo và SMS qua FastAPI/Twilio; secret chỉ nằm trong backend.

Không tạo adapter rỗng. Nếu trình duyệt không hỗ trợ một năng lực native cụ thể, UI vẫn giữ nguyên bố cục nhưng phải hiển thị trạng thái khả dụng trung thực. PTE native không được giả lập thành PTE trên web; web tiếp tục chạy ONNX thật và phần so sánh PTE chỉ khả dụng trên Android cho tới khi có runtime PTE web thật.

## Ảnh dùng chung

UI không được import `dart:io` hoặc gọi `Image.file`. ImagePicker trả về `XFile`; controller đọc `Uint8List` bằng `XFile.readAsBytes()` trên cả Android và web. Một model dữ liệu ảnh trung lập nền tảng chứa bytes, tên file và MIME type sẽ được dùng cho:

- preview bằng `Image.memory`;
- AI inference;
- lưu offline;
- upload multipart.

Cách này loại bỏ các import `dart:io` khỏi `presentation/` và giữ hành vi UI giống nhau.

## Khởi động và đồng bộ

`main.dart` chỉ dựng dependency graph dùng chung. Bootstrap nền tảng được chọn bằng conditional import:

- Android đăng ký WorkManager callback.
- Web đăng ký listener online/offline và gọi cùng `syncPending` khi kết nối trở lại trong lúc ứng dụng đang mở.

Cả hai đường đều gọi cùng repository/use case. Web không khai báo rằng có background execution khi trình duyệt đã đóng nếu trình duyệt không bảo đảm khả năng đó.

## Model AI

Model và metadata phải được chuẩn hóa dưới `fe/app/assets/models/`:

- `model.onnx`
- `model.pte`
- `model_manifest.json`

ONNX Android và Chrome phải dùng cùng preprocessing, class order, mean/std và cùng model version từ manifest. Test parity hiện có trong `web_fullstack/model_tools` được giữ và cập nhật đích output sang `fe/app`.

## Xử lý lỗi

- Lỗi tải model không được làm ứng dụng crash; controller đưa ra trạng thái model unavailable có thể hiển thị trên UI.
- Lỗi permission camera/location phải trả thông báo rõ ràng thay vì nuốt exception.
- Báo cáo gửi thất bại vẫn được lưu pending và đồng bộ lại khi có mạng.
- Backend chưa chạy phải tạo lỗi kết nối có thể hiểu được, không làm mất báo cáo.
- SMS chỉ được gọi sau bước xác nhận và chỉ khi backend công bố capability tương ứng.

## Kiểm thử và tiêu chí hoàn thành

### Import và phân tích

- `flutter analyze` không có `uri_does_not_exist`, `dart:ffi` trên web hoặc `dart:io` trong code được Chrome kéo vào.
- Sửa năm lint hiện có trong khi chạm vào các file liên quan.

### Android

- Khôi phục workaround Kotlin incremental và build APK debug thành công.
- `flutter test` thành công.
- Chạy trên một AVD hiện có và đi qua splash, đăng nhập/guest, trang chủ, tạo báo cáo và lịch sử.
- ONNX load model thật; PTE bridge load model thật trên Android.

### Chrome

- `flutter build web --release` từ chính `fe/app` thành công.
- `flutter run -d chrome` hiển thị đúng cùng navigation và màn hình Android.
- Test thật việc chọn ảnh, preview, ONNX inference, lưu offline và đồng bộ với backend.
- Artifact ONNX, manifest, bridge và WASM tồn tại trong `build/web`.

### Backend

- Backend pytest thành công.
- Health, báo cáo, ảnh và SMS capability hoạt động với frontend trong `fe/app`.
- SMS vẫn disabled khi chưa có khóa Twilio.

### Parity giao diện

- Không tồn tại màn hình thay thế riêng cho web.
- Widget test dùng cùng widget tree cho Android và Chrome.
- Mọi chỉnh sửa trong `fe/app/lib/presentation/` được nhìn thấy trên cả hai target mà không sao chép file.

## Trình tự triển khai

1. Sửa baseline Android: Kotlin incremental, model assets và năm lint hiện có.
2. Đưa ảnh về kiểu dữ liệu platform-neutral để loại `dart:io` khỏi UI/controller.
3. Tách inference native/web bằng conditional export và chuyển ONNX web bridge/assets.
4. Tách location, background sync và các bootstrap platform-specific.
5. Chuyển offline store, API client, browser online events và test từ frontend web cũ.
6. Cập nhật script web để chạy `fe/app` thay cho `web_fullstack/frontend`.
7. Chạy toàn bộ test/build/runtime parity.
8. Chỉ sau khi parity đạt mới xóa `web_fullstack/frontend` trùng lặp.

## Ngoài phạm vi

- Không thiết kế lại giao diện.
- Không thay theme, navigation hoặc nội dung màn hình Android hiện tại.
- Không giả lập PTE trên web.
- Không bật SMS thật nếu chưa có khóa và xác nhận của người dùng.
