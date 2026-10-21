1/ Cách xuất file apk cho đt
- Copy file cấu hình model onnx, pte, mainfest và metadata(nếu có) vào app/asset/models và đổi tên như sau:
với model onnx: đổi thành model.onnx
với pte: đổi thành model.pte
- Với chạy mô hình cắt tỉa (pruning): thì bỏ file metadata cũng được

lệnh chạy xuất apk:
cd fe/app
flutter pub get
flutter build apk --release --split-per-abi --target-platform android-arm64 --dart-define=ALLOW_INSECURE_LAN=true --dart-define=SERVER_URL=http://192.168.1.73:8000


2/ Thay ONNX + PTE + model_manifest.json trong Edge Ai/Export bằng đúng bộ của APK đó.
- Chạy định dạng seed nào, có cắt tỉa không: thì copy file định dạng model của cái đó đưa vào fe/model/Edge Ai/Export để tiến hành lấy model onnx
- nhớ đổi tên model thành để be kiếm
flood_mobilenetv3_large.onnx
flood_mobilenetv3_large.pte


3/ lệnh chạy backend từ terminal
cd products/be
.\run.bat