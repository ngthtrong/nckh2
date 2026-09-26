# Dataset_Flood — bộ ảnh phân loại mức ngập

Bộ ảnh dùng để huấn luyện mô hình nhận diện mức ngập chạy trên thiết bị
(MobileNetV3-Large, notebook [`../1706.ipynb`](../1706.ipynb)).

## Thành phần (đếm ngày 24/09/2026)

| Lớp | Số ảnh | Tiêu chí gán nhãn |
|---|---:|---|
| `non_flood` | 530 | Không có nước ngập rõ ràng; đường khô, ướt, mưa hoặc vũng nước nhỏ nhưng chưa phải ngập |
| `low` | 388 | Có nước ngập rõ nhưng dưới gối người, dưới thân thấp xe máy, dưới phần chính bánh xe ô tô |
| `medium` | 358 | Nước khoảng từ gối đến dưới ngực; tới hoặc gần yên xe máy; qua bánh xe ô tô |
| `high` | 345 | Nước từ ngực trở lên; qua tay lái xe máy; tới cửa kính hoặc mái xe; ngập sâu vào nhà, cửa sổ |
| **Tổng** | **1.621** | |

Tiêu chí lấy nguyên văn từ "Guideline relabel" trong notebook huấn luyện. Thứ tự lớp đầu ra
của mô hình là `low, medium, high, non_flood` (khớp `fe/app/assets/labels.json`).

Định dạng file: 1.409 `.jpg`, 167 `.webp`, 24 `.jpeg`, 16 `.png`, 5 `.avif`; một số file
đuôi `.webp` thực chất là JPEG. Kích thước file từ 2,5 KB đến 2,9 MB (trung vị khoảng 35 KB);
57 ảnh JPEG có cạnh dài từ 1600 px trở lên.

## Làm sạch và chia dữ liệu

Notebook thực hiện trước khi huấn luyện:

- Bỏ ảnh lỗi không đọc được; bỏ thư mục review (`uncertain`, `need_review`, ...).
- Phát hiện ảnh trùng bằng MD5; ảnh trùng nằm ở nhiều lớp khác nhau bị loại khỏi huấn luyện.
- Gom ảnh gần giống bằng dHash thành *perceptual group*; group có nhãn xung đột bị loại để
  review; một group chỉ nằm trong một tập (tránh rò rỉ dữ liệu giữa train/val/test).
- Chia phân tầng theo lớp, seed 42, tỉ lệ khoảng 70/15/15.

Lần chạy có output được lưu trong notebook (07/09/2026, khi bộ ảnh có 1.625 ảnh):

| Tập | low | medium | high | non_flood | Tổng |
|---|---:|---:|---:|---:|---:|
| train | 272 | 252 | 243 | 370 | 1.137 |
| val | 58 | 54 | 52 | 80 | 244 |
| test | 58 | 54 | 52 | 80 | 244 |

File chia tập (`split_train_val_test_*.csv`) được ghi vào `fe/model/models/`, thư mục này bị
`.gitignore` nên **không có trong repo**. Muốn đánh giá lại trên đúng tập test cần lấy lại
file này từ máy/Drive đã huấn luyện.

## Giới hạn

- Chưa có bản ghi nguồn gốc và giấy phép cho từng ảnh. Tên file cho thấy nhiều ảnh được thu
  thập từ web và báo điện tử (có cả ảnh chụp màn hình), nên chỉ dùng cho nghiên cứu, không
  phân phối lại khi chưa rà soát bản quyền.
- Ảnh chủ yếu là ảnh web đã nén, nhỏ hơn ảnh chụp trực tiếp bằng điện thoại; mô hình chưa
  được đánh giá riêng trên ảnh chụp thực địa.
- Ranh giới `low`/`medium` và `medium`/`high` phụ thuộc mốc tham chiếu (người, xe) trong ảnh;
  đây là các cặp lớp mô hình nhầm nhiều nhất (xem ma trận nhầm lẫn trong notebook).
- Bộ ảnh chỉ có phương thức ảnh; chưa có dữ liệu văn bản tin nhắn cầu cứu tiếng Việt như
  thuyết minh dự kiến.

## Dữ liệu liên quan

Bộ dữ liệu **bán tổng hợp** dùng cho thực nghiệm phân cụm và xếp hạng ưu tiên (80 run, neo
theo bối cảnh Copernicus EMSR848) nằm ở [`src/data/`](../../../src/data/README.md). Đó là báo
cáo mô phỏng, không phải ảnh hay báo cáo cứu hộ thật.
