# Đối chiếu sản phẩm với Thuyết minh đề tài

Đề tài: *Hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI*
(thuyết minh ngày 25/12/2025, thực hiện 03/2026–08/2026). Tài liệu đối chiếu từng cam kết trong
mục 16.2 (tiến độ) và mục 17 (sản phẩm) của thuyết minh với bằng chứng có trong repository,
trạng thái ngày 24/09/2026. Chỉ ghi những gì kiểm tra được trong mã nguồn và kết quả đã lưu.

Ký hiệu: **Đạt** = có sản phẩm và bằng chứng; **Một phần** = có nhưng thiếu so với cam kết;
**Chưa** = chưa có trong repo.

## 1. Sản phẩm đăng ký (mục 17)

| Mục | Sản phẩm | Trạng thái | Bằng chứng | Ghi chú |
|---|---|---|---|---|
| 3.1 | Ứng dụng di động tích hợp AI, gửi thông tin cầu cứu về trung tâm | **Đạt** | `fe/app/` (Flutter); 12/12 unit test pass | Suy luận ảnh trên máy (ONNX, ExecuTorch), outbox lưu bền, gửi thích ứng theo mạng, SMS dự phòng |
| 3.2 | Website có bản đồ vị trí kêu cứu và phân cụm sự kiện theo thời gian thực | **Đạt** | `be/templates/dashboard.html`, `GET /api/clusters`; ảnh chụp [dashboard.png](dashboard.png) | Bản đồ Leaflet/OSM, cụm cập nhật mỗi 5 s, xếp hạng ưu tiên, đổi trạng thái điều phối |
| 3.3 | Bộ mô hình AI đa phương thức, đã nén cho thiết bị di động | **Một phần** | `fe/model/1706.ipynb`, `fe/model/Edge Ai/`, `fe/reports/quantization/` | Chỉ có mô hình **ảnh**; chưa có mô hình văn bản. Kết quả nén: xem mục 3 |
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
| 5 | Nén và tối ưu mô hình cho thiết bị di động | Mô hình AI bản nhẹ | **Một phần** | Xem mục 3 |
| 6 | Thuật toán phân cụm sự kiện theo vị trí địa lý | Mã nguồn thuật toán | **Đạt** | `be/rescue_core/` (product C_ij + Louvain, điểm ưu tiên có chặn), `be/cluster_service.py`, 11 unit test; đánh giá trong bài ISDS 2026 |
| 7 | Ứng dụng di động cho người dùng cuối | Ứng dụng di động | **Đạt** | `fe/app/` |
| 8 | Backend và dashboard bản đồ | Website quản lý thông tin cứu hộ | **Đạt** | `be/` (FastAPI, SQLite), dashboard bản đồ |
| 9 | Thực nghiệm hiệu năng trong điều kiện giả lập mạng yếu | Bảng kết quả độ trễ, độ chính xác | **Một phần** | Xem mục 4. Giả lập trên máy tính, chưa đo trên điện thoại thật |
| 10 | Báo cáo tổng kết, công bố | Quyển báo cáo, bài báo | Công bố **Đạt**; báo cáo do nhóm làm | `paper/` |

## 3. Mô hình AI và nén mô hình

KẾT_QUẢ_MÔ_HÌNH

## 4. Thực nghiệm mạng yếu

KẾT_QUẢ_MẠNG_YẾU

## 5. Khác biệt so với thuyết minh (cần giải trình với hội đồng)

1. **Chưa có mô hình văn bản tiếng Việt.** Thuyết minh dự kiến DistilBERT và dữ liệu UIT-VSMEC,
   tin nhắn Zalo/Facebook; repo không có dữ liệu hay mô hình văn bản nào. Hiện mức khẩn cấp từ
   mô tả được suy bằng quy tắc từ khóa trong `be/cluster_service.py` (heuristic, chưa kiểm định).
2. **Không dùng FloodNet, CrisisMMD.** Hai bộ này chỉ được trích dẫn trong tổng quan. Mô hình ảnh
   học trên `Dataset_Flood`, bộ ảnh do nhóm thu thập và gán nhãn theo 4 mức ngập.
3. **Dữ liệu cho phân cụm là bán tổng hợp.** Thuật toán phân cụm và xếp hạng được đánh giá trên
   80 run mô phỏng neo theo bối cảnh Copernicus EMSR848, không phải báo cáo cứu hộ thật.
4. **Thực nghiệm mạng yếu là giả lập trên máy tính** (proxy giới hạn băng thông), chưa cài app lên
   điện thoại thật trong môi trường 2G/3G như phương pháp ở mục 15.2 của thuyết minh.
5. **Nguồn gốc số liệu mô hình.** File chia train/val/test không có trong repo; kết quả test độc
   lập lấy từ output đã lưu của notebook (lần chạy 07/09/2026). Báo cáo 86,58% trong
   `fe/reports/model_comparison/` đo trên toàn bộ bộ ảnh gồm cả ảnh huấn luyện, không dùng làm
   độ chính xác.

## 6. Cách chạy lại để trình diễn

```bash
cd be
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export RESCUE_DB_FILE=data/demo.db RESCUE_UPLOADS_DIR=uploads_demo
.venv/bin/python seed_demo.py --reset      # nạp 316 báo cáo mô phỏng (có nhãn "Dữ liệu mô phỏng")
.venv/bin/python main.py                   # mở http://localhost:8000
.venv/bin/python -m unittest test_contract test_cluster_service -v
```
