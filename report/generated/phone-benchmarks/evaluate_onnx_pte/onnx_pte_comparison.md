# Đối chiếu ONNX và ExecuTorch/PTE trên điện thoại

## Bảng chính: seed 1024 pruning

| Điện thoại | ONNX P50 (ms) | PTE P50 (ms) | ONNX P95 (ms) | PTE P95 (ms) | Tăng tốc P50 | Macro-F1 cả hai (%) |
|---|---:|---:|---:|---:|---:|---:|
| realme15 | 74.471 | 39.344 | 135.131 | 103.338 | 1.89× | 74.89 |
| redminote11 | 172.819 | 90.892 | 274.626 | 202.812 | 1.90× | 74.10 |
| redminote13 | 239.020 | 73.147 | 335.798 | 180.651 | 3.27× | 74.40 |
| samsungs10e | 73.526 | 34.401 | 163.776 | 103.429 | 2.14× | 74.90 |

## Chất lượng và thời gian trung bình của seed 1024 pruning

| Runtime | Accuracy (%) | Precision macro (%) | Recall macro (%) | F1 macro (%) | MAE (mức) | RMSE (mức) | TB P50 (ms) | TB P95 (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| onnx | 76.66 | 74.50 | 74.87 | 74.58 | 0.2461 | 0.5210 | 139.959 | 227.333 |
| pte | 76.66 | 74.50 | 74.87 | 74.58 | 0.2461 | 0.5210 | 59.446 | 147.558 |

## Lựa chọn và phạm vi kết luận

- Chọn **MobileNetV3-Large seed 1024 pruning + ExecuTorch/PTE** cho bước triển khai nguyên mẫu tiếp theo: macro-F1 cao nhất trong bốn cấu hình model đã so sánh, và PTE nhanh hơn ONNX trên cả bốn máy trong các phiên đã lưu.
- Trong toàn bộ 16 cặp máy/model (hai seed × hai biến thể × bốn máy), PTE có mean/P50/P95 thấp hơn ONNX ở 16/16 cặp. Dự đoán top-1 ONNX/PTE trùng 256/256 trong mỗi cặp, nên các chỉ số chất lượng liệt kê bằng nhau. Không khẳng định vector xác suất giống tuyệt đối.
- Với seed 1024 pruning, PTE có Precision high 80,85%, Recall high 87,96% và F1 high 84,25%, bằng ONNX trên bộ ảnh đã kiểm tra. Lựa chọn model theo macro-F1 không có nghĩa thắng mọi metric; baseline 1024 có RMSE và số lỗi nặng trung bình thấp hơn.
- Thời gian bao gồm giải mã ảnh, tiền xử lý và suy luận trong classifyImage, loại trừ đọc ảnh package; đây không phải thời gian toàn luồng gửi báo cáo. Có năm warmup và 256 ảnh test mỗi phiên.
- Tăng tốc P50 = ONNX P50 / PTE P50 trong cùng máy/model. TB P50/P95 là trung bình percentile của bốn máy, không phải percentile gộp hoặc thời gian cho mọi điện thoại.
- Chỉ có một phiên cho mỗi máy/model/runtime, thời điểm chạy khác nhau, chưa kiểm soát đầy đủ nhiệt độ/tải. Chưa có kiểm định thống kê, kết quả pin/RAM hay dữ liệu camera độc lập. Không suy ra PTE luôn nhanh hơn trên thiết bị khác.
- MAE/RMSE dùng non_flood=0, low=1, medium=2, high=3, đơn vị mức phân loại; thấp hơn tốt hơn. Trong bảng tổng hợp, đây là trung bình MAE/RMSE từng máy, không gộp các lần dùng lại ảnh thành mẫu độc lập.
- onnx_pte_comparison.csv: 16 cặp đầy đủ, các cột *_both là chỉ số chung của hai runtime đã xác nhận trùng dự đoán; thời gian và nguồn JSON tách riêng. runtime_summary.csv: tám hàng seed/model/runtime, gồm cả chỉ số lớp high và mean/P50/P95.
- Nguồn: summary.csv và predictions.csv, truy về JSON qua source_json. Tái xuất bằng `python report/scripts/compare_phone_runtimes.py`. Không chạy lại suy luận, không đổi model triển khai, không điền mục điện thoại đang để trống trong báo cáo.
