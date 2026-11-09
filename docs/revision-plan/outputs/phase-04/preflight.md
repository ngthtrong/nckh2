# P04 preflight — NOT_RUN inference

Exact app ONNX/PTE hash nối với seed1024 pruning bundle (environment.json/P02 compression-audit.csv). Test split256/ID/class/preprocess có nguồn. Missing: deployed PTE CPU/Android runner tại môi trường hiện tại, onnxruntime/torch/executorch, adb/device session receipt/APK hash. Có ONNX artifact không đồng nghĩa clean parity đã đạt.

Đã chuẩn bị9 đầu vào (clean và 8 corruption) trên đúng một ảnh validation và kiểm số biến thể/hash/kích thước, không trên test và không chạy model. variant-manifest.csv chỉ ghi VALIDATION_PREPARATION_ONLY. Không có predictions/metrics vì chưa đo.

Quyết định dùng nhánh không chạy được user cho phép: chưa mở thêm môi trường suy luận hoặc thay target để lấp C5. CPU ONNX screening là khả năng sau khi runtime/clean agreement được xác nhận, không khẳng định không thể cài runtime. Android gate thiếu device vẫn chưa đạt. C5 OPEN, C2 metadata đã có.
