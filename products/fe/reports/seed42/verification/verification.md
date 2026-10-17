# Xác minh pipeline PTH/ONNX FP32

Local status: pass_local (exit 0).
PASS: 5; FAIL: 0; NOT TESTED: 0.
Scope: test_subset_smoke; ảnh: 3; engine: ort.

Preflight: pass.
Config/hash/split độc lập khớp; không tự chia lại dataset.

| Check | Status | Chi tiết |
|---|---|---|
| preprocessing | pass | Xem thông số trong verification.json. |
| precision | pass | Xem thông số trong verification.json. |
| execution_provider | pass | Xem thông số trong verification.json. |
| graph_parity | pass | Sai số đo thực tế trên test, không phải accuracy hay chứng nhận toàn bộ dữ liệu. |
| label_mapping | pass | Đồng thuận trên ảnh đã kiểm tra; không đồng nghĩa accuracy 100%. |

Mobile: NOT TESTED. Không chạy Flutter/device; chưa kiểm tra pixel preprocessing, partition hoặc latency mobile.
Đây là kiểm tra kỹ thuật cục bộ, không phải full-test accuracy hay nghiệm thu trên điện thoại.
