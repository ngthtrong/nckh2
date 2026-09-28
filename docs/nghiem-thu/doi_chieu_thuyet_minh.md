# Đối chiếu sản phẩm với Thuyết minh đề tài

Đề tài: *Hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI*
(thuyết minh ngày 25/12/2025, thực hiện 03/2026–08/2026). Tài liệu đối chiếu từng cam kết trong
mục 16.2 (tiến độ) và mục 17 (sản phẩm) của thuyết minh với bằng chứng có trong repository,
trạng thái ngày 27/09/2026. Chỉ ghi những gì kiểm tra được trong mã nguồn, kết quả đã lưu và
kiểm thử đã chạy.

Ký hiệu: **Đạt** = có sản phẩm và bằng chứng; **Một phần** = có nhưng thiếu so với cam kết hoặc
chưa kiểm chứng được phần cốt lõi; **Chưa** = chưa có trong repo.

Kiểm thử đã chạy ngày 27/09/2026 (Ubuntu 24.04 trên WSL2, Docker 29.8, Flutter 3.47.5):

| Kiểm thử | Kết quả | Lệnh |
|---|---|---|
| Unit test backend (hợp đồng đồng bộ, migration, RFC 8785, phân cụm theo bài báo, API dashboard quản lý) | 44/44 | `be/.venv/bin/python -m unittest test_contract test_cluster_service test_dashboard_api` |
| Unit test app (chọn chế độ gửi, gửi thích ứng, SMS, trạng thái, hash) | 26/26 | `cd fe/app && flutter test` |
| Hợp đồng app ↔ server trên container | Đạt hết | `be/test_client.py` |
| End-to-end hệ thống Docker (app web → backend → dashboard có đăng nhập, Chromium headless) | 46/46 | `scripts/demo/e2e/e2e_system.py` |
| Build APK Android (debug) | APK_BUILD | `flutter build apk --debug` |

## 1. Sản phẩm đăng ký (mục 17)

| Mục | Sản phẩm | Trạng thái | Bằng chứng | Ghi chú |
|---|---|---|---|---|
| 3.1 | Ứng dụng di động tích hợp AI, gửi thông tin cầu cứu về trung tâm | **Một phần** | `fe/app/` (Flutter); 26/26 unit test; E2E 46/46 trên bản web | **Đã kiểm chứng (bản web):** SOS 1 chạm, gửi bài kèm ảnh, gửi thích ứng theo mạng (đo `/probe` → ảnh gốc / ảnh nén / chỉ thông tin), hàng đợi offline tự đồng bộ khi có mạng, theo dõi trạng thái điều phối từ trung tâm, báo cáo thiếu GPS vào hàng xem xét. **Chưa kiểm chứng trên điện thoại Android:** AI on-device (repo thiếu `model.onnx` và `model_manifest.json`, xem mục 3), SMS dự phòng (cần số tổng đài thật qua `EMERGENCY_PHONE`), camera, Workmanager |
| 3.2 | Website có bản đồ vị trí kêu cứu và phân cụm sự kiện theo thời gian thực | **Đạt** | `be/templates/dashboard.html`, `GET /api/clusters`, container `dashboard`; E2E; ảnh chụp [dashboard.png](dashboard.png) | Bản đồ Leaflet/OSM (tô theo cụm hoặc trạng thái, bản đồ nhiệt), cụm cập nhật mỗi 5 s, xếp hạng ưu tiên theo Eq. 4 của bài báo, điều phối từng báo cáo, nhiều báo cáo hoặc cả cụm (xác nhận đúng danh sách), đóng báo cáo kèm lý do, giao đội cứu hộ, ghi chú và nhật ký thao tác, nhập vị trí cho báo cáo thiếu GPS, thống kê thời gian phản ứng, xuất CSV/GeoJSON, sao lưu CSDL, đăng nhập điều phối viên; hiển thị cách app đã gửi (ảnh gốc/nén/chỉ thông tin/SMS) |
| 3.3 | Bộ mô hình AI đa phương thức, đã nén cho thiết bị di động | **Một phần** | `fe/model/1706.ipynb`, `fe/model/Edge Ai/flood_mobilenetv3_large.pte` | Chỉ có mô hình **ảnh**, chưa có mô hình văn bản. Chưa có kết quả nén (INT8) trong repo; bản `.pte` là FP32. Xem mục 3 |
| 4.1 | Bản tin | **Bản nháp** | [ban_tin.md](ban_tin.md) (Việt + Anh) | Cần chép vào mẫu Word của ĐHCT, bổ sung mã đề tài và email GVHD |
| 4.2 | Báo cáo tóm tắt | Ngoài phạm vi đợt này | – | Nhóm tự soạn |
| 4.3 | Video demo ≤ 2 phút | Ngoài phạm vi đợt này | – | Nhóm tự làm |
| I | Xuất bản phẩm (thuyết minh ghi "Không") | **Vượt** | `paper/main.tex` | Bài *Stress-Testing Product-Gated Clustering and Bounded Priority Ranking for Flood-Rescue Reports: A Synthetic Study*, ISDS 2026, mã bài 6444 (bản camera-ready) |

## 2. Nội dung và tiến độ (mục 16.2)

| TT | Nội dung | Sản phẩm cam kết | Trạng thái | Bằng chứng |
|---|---|---|---|---|
| 1 | Tổng quan trích xuất đặc trưng đa phương thức, tính toán biên | Thuyết minh, nghiên cứu liên quan | **Đạt** | `resource/Thuyết minh NCKH.md`; phần Related Work của `paper/main.tex` |
| 2 | Xây dựng bộ dữ liệu huấn luyện cho bài toán cứu hộ tại Việt Nam | Bộ dữ liệu đã chuẩn hóa | **Một phần** | [Dataset_Flood](../../fe/model/Dataset_Flood/README.md): 1.621 ảnh, 4 mức ngập, có tiêu chí gán nhãn; [src/data](../../src/data/README.md): 80 run báo cáo bán tổng hợp. Chưa có dữ liệu văn bản tin nhắn |
| 3 | Thiết kế kiến trúc hệ thống, cơ sở dữ liệu | Tài liệu thiết kế, sơ đồ CSDL | **Đạt** | [system_design.md](../system_design.md), [contact_db.md](../contact_db.md), [contact_connect.md](../contact_connect.md) |
| 4 | Huấn luyện, tinh chỉnh mô hình phân loại ảnh và văn bản | Các file mô hình | **Một phần** | MobileNetV3-Large (ảnh), test độc lập 244 ảnh: Accuracy 73,77%, macro-F1 72,21%. Chưa có mô hình văn bản |
| 5 | Nén và tối ưu mô hình cho thiết bị di động | Mô hình AI bản nhẹ | **Một phần** | Đã chuyển sang ExecuTorch/XNNPACK (`.pte`) và ONNX; chưa có kết quả lượng tử hóa. Xem mục 3 |
| 6 | Thuật toán phân cụm sự kiện theo vị trí địa lý | Mã nguồn thuật toán | **Đạt** | `be/rescue_core/` (product C_ij + Louvain, Q_i theo Eq. 1, điểm ưu tiên có chặn; khớp cài đặt thực nghiệm của bài trên 80 run gold), `be/cluster_service.py`, 16 unit test; đánh giá trong bài ISDS 2026 |
| 7 | Ứng dụng di động cho người dùng cuối | Ứng dụng di động | **Một phần** | `fe/app/`; như mục 3.1: đủ chức năng và đã kiểm thử trên bản web, chưa chạy trên điện thoại Android thật |
| 8 | Backend và dashboard bản đồ | Website quản lý thông tin cứu hộ | **Đạt** | `be/` (FastAPI, SQLite), dashboard bản đồ; chạy bằng `docker compose up` (3 container `be`, `dashboard`, `fe`) |
| 9 | Thực nghiệm hiệu năng trong điều kiện giả lập mạng yếu | Bảng kết quả độ trễ, độ chính xác | **Một phần** | Xem mục 4. Có script và kiểm thử chức năng; chưa có bảng kết quả độ trễ lưu trong repo |
| 10 | Báo cáo tổng kết, công bố | Quyển báo cáo, bài báo | Công bố **Đạt**; báo cáo do nhóm làm | `paper/` |

## 3. Mô hình AI và nén mô hình

| Hạng mục | Có trong repo | Ghi chú |
|---|---|---|
| Kiến trúc, huấn luyện | `fe/model/1706.ipynb` | MobileNetV3-Large, 4 lớp `low`, `medium`, `high`, `non_flood`, đầu vào 224×224 |
| Độ chính xác | Output đã lưu của notebook | Test độc lập 244 ảnh: Accuracy 73,77%, macro-F1 72,21%. File chia train/val/test không có trong repo |
| ONNX tương đương PyTorch | `fe/reports/model_comparison/summary.md` | 100% nhãn trùng trên 1.625 ảnh. Số 86,58% trong báo cáo này đo trên toàn bộ bộ ảnh (gồm ảnh train), chỉ chứng minh tương đương, **không** dùng làm độ chính xác |
| Bản ExecuTorch | `fe/model/Edge Ai/flood_mobilenetv3_large.pte` (17 MB) | Backend XNNPACK, trọng số FP32 (chưa nén) |
| Lượng tử hóa INT8 | `fe/tools/quantize_model.py` | Có script, **chưa có kết quả** (kích thước, độ chính xác sau nén) trong repo |
| File app cần | `fe/app/assets/models/` (git-ignore) | App cần `model.onnx`, `model.pte`, `model_manifest.json`. Repo **chưa có** `model.onnx` và `model_manifest.json`, nên bản clone mới chạy app mà AI on-device báo "không khả dụng". Export bằng `fe/tools/convert_model.py` rồi chép bằng `scripts/demo/stage_model.sh` |

## 4. Thực nghiệm mạng yếu

| Hạng mục | Có trong repo | Ghi chú |
|---|---|---|
| Giả lập 2G/3G/4G bằng proxy giới hạn băng thông | `be/experiments/weak_network.py` | Có script; kết quả (`be/experiments/results/`) **chưa lưu** trong repo |
| Gửi thích ứng chọn đúng chế độ theo băng thông | `scripts/demo/e2e/e2e_system.py` (Chrome DevTools giới hạn băng thông) | Mạng không giới hạn → ảnh gốc (53,6 KB); 300 kbit/s → ảnh nén (42,4 KB); 20 kbit/s → chỉ gửi thông tin, không upload ảnh. Đây là kiểm thử chức năng, không phải bảng độ trễ |
| Mất mạng rồi có lại | `scripts/demo/e2e/e2e_system.py` | Báo cáo vào hàng đợi, tự đồng bộ khi có mạng, server nhận đủ, không trùng |
| Đo trên điện thoại thật trong 2G/3G | – | Chưa làm |

## 5. Khác biệt so với thuyết minh (cần giải trình với hội đồng)

1. **Chưa có mô hình văn bản tiếng Việt.** Thuyết minh dự kiến DistilBERT và dữ liệu UIT-VSMEC,
   tin nhắn Zalo/Facebook; repo không có dữ liệu hay mô hình văn bản nào. Hiện mức khẩn cấp từ
   mô tả được suy bằng quy tắc từ khóa trong `be/cluster_service.py` (heuristic, chưa kiểm định).
2. **Không dùng FloodNet, CrisisMMD.** Hai bộ này chỉ được trích dẫn trong tổng quan. Mô hình ảnh
   học trên `Dataset_Flood`, bộ ảnh do nhóm thu thập và gán nhãn theo 4 mức ngập.
3. **Dữ liệu cho phân cụm là bán tổng hợp.** Thuật toán phân cụm và xếp hạng được đánh giá trên
   80 run mô phỏng neo theo bối cảnh Copernicus EMSR848, không phải báo cáo cứu hộ thật.
4. **Thực nghiệm mạng yếu là giả lập trên máy tính** (proxy giới hạn băng thông và Chrome DevTools),
   chưa cài app lên điện thoại thật trong môi trường 2G/3G như phương pháp ở mục 15.2 của thuyết minh.
5. **Nguồn gốc số liệu mô hình.** File chia train/val/test không có trong repo; kết quả test độc
   lập lấy từ output đã lưu của notebook (lần chạy 07/09/2026). Báo cáo 86,58% trong
   `fe/reports/model_comparison/` đo trên toàn bộ bộ ảnh gồm cả ảnh huấn luyện, không dùng làm
   độ chính xác.
6. **Chưa có kết quả nén mô hình.** Mô hình triển khai là FP32 (`.pte` 17 MB); script lượng tử hóa
   INT8 có nhưng chưa lưu kết quả.
7. **SMS dự phòng chỉ kiểm chứng ở mức mã nguồn và unit test.** App gửi SMS qua `SmsManager` của
   Android khi không có data; kênh trả thành công khi Android nhận lệnh gửi, không có xác nhận tin
   đã tới tổng đài. Tổng đài tiếp nhận SMS thủ công; server không nhận SMS.
8. **Bản web của app (container `fe`) không có AI on-device và SMS** (onnxruntime cần `dart:ffi`).
   Bản web dùng để trình diễn luồng gửi/đồng bộ/điều phối; AI và SMS cần app Android.

## 6. Cách chạy lại để trình diễn

```bash
docker compose up -d --build     # be :8000, dashboard :8080, app web :8081; nạp 316 báo cáo mô phỏng
# kiểm thử end-to-end (cần Playwright, xem docs/huong_dan_chay_demo.md mục 0b)
.venv-e2e/bin/python scripts/demo/e2e/e2e_system.py
```

Không dùng Docker: xem [huong_dan_chay_demo.md](../huong_dan_chay_demo.md). App Android build
trên WSL bằng `scripts/demo/setup_android_wsl.sh` rồi `scripts/demo/run_app.sh`.
