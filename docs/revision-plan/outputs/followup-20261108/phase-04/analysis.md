# Phân tích P04 bổ sung — CPU_ONLY

## Material Passport

- Origin: academic-research-suite / experiment-agent, authorized fixed-model CPU screening.
- Date: 2026-11-08, Asia/Taipei.
- Verification status: VERIFIED for the new raw CPU measurements and structural/hash checks; not a reproduction of an Android experiment.
- Scope: CPU_ONLY_ONNX, seed1024 structured pruning; no training, model export or test tuning.

## Kết quả từ raw

| Điều kiện | Accuracy % | Macro-F1 % | Recall high % | Lỗi ≥2 mức |
|---|---:|---:|---:|---:|
| clean | 80.08 | 78.26 | 85.19 | 4 |
| jpeg_q50 | 77.34 | 75.27 | 79.63 | 5 |
| jpeg_q20 | 75.78 | 74.14 | 79.63 | 4 |
| short_edge_128 | 76.56 | 75.17 | 75.93 | 5 |
| short_edge_64 | 67.19 | 64.86 | 55.56 | 12 |
| blur_sigma_1 | 76.17 | 74.12 | 79.63 | 4 |
| blur_sigma_2 | 70.31 | 68.31 | 70.37 | 7 |
| exposure_0.7 | 76.95 | 74.85 | 85.19 | 4 |
| exposure_0.4 | 71.09 | 68.04 | 79.63 | 9 |

## Chênh lệch ghép cặp với clean

| Điều kiện | Δ macro-F1 (đpt) | CI 95% (đpt) |
|---|---:|---:|
| jpeg_q50 | -2.99 | [-6.58; +0.38] |
| jpeg_q20 | -4.12 | [-8.21; -0.20] |
| short_edge_128 | -3.10 | [-7.37; +1.17] |
| short_edge_64 | -13.40 | [-19.69; -7.08] |
| blur_sigma_1 | -4.15 | [-8.45; -0.07] |
| blur_sigma_2 | -9.95 | [-16.00; -4.13] |
| exposure_0.7 | -3.42 | [-7.03; +0.07] |
| exposure_0.4 | -10.22 | [-16.21; -4.21] |

## Giới hạn và trạng thái

**C5 PARTIAL / CPU_ONLY.** Không chạy Android/PTE hoặc E2E; không có thiết bị/adb/session receipt. Không suy CPU timing thành mobile. 2.304 prediction rows chỉ có 256 ảnh gốc, không phải 2.304 ảnh độc lập. Có 252 split_group (249 nhóm đơn, hai nhóm đôi, một nhóm ba); đây là đơn vị lấy mẫu lại để giữ quan hệ gần trùng, chưa chứng minh 252 nguồn/sự kiện độc lập. Tên trường `independent_unit`/`independent_images` trong receipt mô tả đơn vị phân tích, không xác nhận tính độc lập khoa học theo nguồn/sự kiện.

Nhãn gốc được kế thừa cho corruption, chưa có chuyên gia thẩm định lại tính giữ nguyên ngữ nghĩa. Mọi ảnh/condition giữ trong mẫu số; không có failure trong lần này. Ordinal non_flood=0, low=1, medium=2, high=3; lỗi nặng là lệch ≥2 mức. Không bật abstention, không chọn ngưỡng sau test; confidence và số mẫu confidence<.5 chỉ mô tả.

CI là percentile bootstrap ghép cặp theo 252 nhóm, 5.000 draw seed20261107; cùng draw cho clean và tám conditions, macro-F1 tính lại từ confusion mỗi draw. 32 CI hiệu ứng không hiệu chỉnh đa so sánh; không có p-value hoặc kết luận familywise significance. Báo đủ tám điều kiện, không chọn riêng CI loại trừ0 để kết luận robust.

Timing gồm predict và preprocess+predict riêng, CPU một luồng, một phiên/scope. Ảnh đưa vào runner là PNG không mất mát của biến đổi đã giải mã; không gồm chi phí JPEG encode, tạo biến thể, hash, load model hoặc IO benchmark package. Phiên degraded nạp lại runtime và không warmup riêng. Không dùng timing để so speedup với Android hoặc phiên lịch sử. Corruption nhân tạo không thay ảnh mưa, camera hay thử nghiệm cứu hộ thực địa.

## Kiểm diễn giải: 11/11 loại sai lệch được rà trong scope phép bổ sung

| Loại | Disposition |
|---|---|
| Simpson | Báo riêng chín conditions và metric high; không suy xu hướng từng lớp từ macro-F1. |
| Ecological | Đơn vị là ảnh/nhóm split, không ngoại suy sang người được cứu hoặc sự kiện độc lập. |
| Berkson / selection | Bộ ảnh web có chọn lọc, source/event independence chưa biết; giữ giới hạn chuyển miền. |
| Collider | Không fit mô hình có biến điều chỉnh hay chọn nhóm theo outcome; không áp dụng trong so sánh pixel này. |
| Base rate | Giữ support test low56/medium60/high54/non_flood86; recall high không phải predictive value lâm sàng. |
| Regression to mean | Cùng toàn bộ ảnh test, không chọn ảnh cực đoan theo performance để đánh giá lại. |
| Survivorship | Đủ2304/2304 rows,0failure; không loại ảnh khó hoặc condition xấu. |
| Look elsewhere | Đủ8contrasts/4metrics và CI chưa hiệu chỉnh được công bố; không gọi significance. |
| Forking paths | Mức suy giảm khóa trong protocol cũ và trước inference mới; model cố định, không tune test. |
| Correlation / causation | Chỉ đối chiếu biến đổi pixel có kiểm soát; không suy nguyên nhân vận hành hay hiệu quả cứu hộ. |
| Reverse causality | Không có phân tích nhân quả quan sát người/sự kiện; không áp dụng cho phép biến đổi pixel đã chỉ định. |
