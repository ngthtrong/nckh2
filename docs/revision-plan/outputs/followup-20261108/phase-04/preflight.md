# Preflight P04 bổ sung — CPU_ONLY

Môi trường riêng `report/build/robustness-env`, packages khóa ở requirements-lock.txt. Chỉ cài ONNX Runtime/NumPy/Pillow/SciPy trong venv mới; không cài đè môi trường báo cáo hoặc RQ.

Exact model ONNX app SHA256 `2ec932a12e4730811597d297edc4de4566cdd6b381e871bc65c658ec8d794d27` khớp structured_onnx seed1024 lịch sử. Class order [low,medium,high,non_flood], config hash và split hash khớp summary lịch sử. Kiểm đủ MD5/group/cross-split cho1702ảnh bằng helper gốc; không chia lại test. Preprocess gọi nguyên helper quantize_model.preprocess, không dùng quantize entrypoint.

Ba ảnh validation smoke chạy thành công trước test, không tune corruption. Clean256 khớp100%top1; max abs probability diff8.344650268554688e-7; allclose atol1e-5/rtol1e-4 đã khóa, không nới tolerance. Clean tensor từ PNG dẫn xuất bitwise equal với preprocess ảnh gốc.

Android/PTE vẫn NOT_RUN: không có adb/device/session/APK receipt và không thay target để tuyên bố hiệu năng Android. Xem protocol/environment/source-hashes và clean-parity.json.
