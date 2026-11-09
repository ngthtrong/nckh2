# Data card — P02

Dataset_Flood: 1.702 ảnh, 4 lớp low/medium/high/non_flood; đầu vào tensor256. Metadata được đọc header trong snapshot refresh, đối chiếu lại hash split trước dùng. Không train hoặc inference.

| Split | low | medium | high | non_flood | Tổng |
|---|---:|---:|---:|---:|---:|
| train | 264 | 278 | 245 | 402 | 1189 |
| val | 57 | 61 | 53 | 86 | 257 |
| test | 56 | 60 | 54 | 86 | 256 |

Đã đối chiếu MD5 từng ảnh; không cross-split theo md5/perceptual_group/split_group đã ghi. Không suy ra độc lập sự kiện/nguồn; URL/license từng ảnh, số annotator, IAA, event/source IDs: UNKNOWN. Nhãn là mức thị giác theo người/xe, không độ sâu đo thực. Không phân phối ảnh lại dựa trên giả định có license.

image-profile.csv chứa 20 nhóm all/split × all/class: n, quantile0/25/50/75/95/100 của width/height/ratio/bytes, format và mode theo header. 1.521JPEG/24PNG/152WEBP/5AVIF; RGB1.687/RGBA14/L1. Metadata mới không phải robustness evaluation.

Split hiện tại khớp predictions/test hashes trong ba bundle seed1024; manifest chia tập chính xác tại lần train seed1024 vẫn chưa đủ. Notebook là nguồn mô tả quy trình, không chứng minh byte từng lần train. Nhiều model được so trên cùng test, lựa chọn sau xem test chưa có independent confirmation. Seed42 lịch sử giữ riêng.

LR: 32 profile,31 dương/1 âm OR; không patient/clinical/text gold; hash byte mismatch có disposition trong lr-hash-discrepancy.json. Cùng số cờ → cùng score, OR và LR nhãn khớp toàn bảng; 10 sanity rounds có recall0,75 và0,667, không tổng quát hoàn hảo. Chỉ tính lại JSON score, không train.

Mô phỏng RQ1 Generator3.0 và RQ2/3 Candidate4.1 khác bộ; không ghép ảnh/LR thành paired multimodal gold.
