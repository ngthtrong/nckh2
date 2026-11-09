# Tra cứu nguồn và lựa chọn pilot

Ngày 08/11/2026, Asia/Taipei. Tra cứu có giới hạn về corpus cứu hộ đa phương thức tiếng Việt; không kết luận không tồn tại corpus khác.

| Nguồn đã truy cập/tìm | Phạm vi được nguồn mô tả | Quyết định |
|---|---|---|
| [CrisisMMD/QCRI](https://qcai.qcri.org/datasets/crisismmd), [CrisisNLP](https://crisisnlp.qcri.org/crisismmd) | Cặp ảnh–tweet thiên tai, nhãn informative/humanitarian/damage; corpus được mô tả tiếng Anh | Đã có 4.261 cặp và nguồn/hash local từ đợt trước. Dùng tập con 300 theo hash + keyword enrichment, giữ split sự kiện; dịch và gán lại bằng AI theo quyền người dùng mới. Không dùng informative làm nhãn request. |
| [UCI Multimodal Damage Identification](https://archive.ics.uci.edu/dataset/456/multimodal%2Bdamage%2Bidentification%2Bfor%2Bhumanitarian%2Bcomputing) | Ảnh có caption, nhãn loại thiệt hại | Không xác minh là corpus tin cứu hộ tiếng Việt với target request; không tải thay corpus chính. |
| [MEDIC](https://crisisnlp.qcri.org/medic/) | Ảnh, nhãn thiên tai/humanitarian/thiệt hại | Không thay nhãn request trên cặp tiếng Việt. |
| [ViMACSA, bài gốc](https://arxiv.org/abs/2405.00543) | Cặp ảnh–văn bản tiếng Việt trong miền khách sạn và nhãn sentiment | Có đa phương thức tiếng Việt nhưng sai miền/nhiệm vụ; không dùng để gọi đã đánh giá cứu hộ. |

Quyết định theo chỉ đạo mới: chạy pilot *tiếng Việt dịch + nhãn AI*, không tạo hồ sơ chuyên gia/human approval. Bản ghi native tiếng Việt và nhãn độc lập vẫn chưa có. License/dataset source revision tiếp tục giữ từ `outputs/multimodal-20261108/protocol.json` và QCRI README đã tải; raw/ảnh/trọng số/bản dịch giữ local, không tự công bố hoặc commit/push.

Các trang nguồn được nguồn mô tả tiếng Anh không chứng minh mọi tweet thực tế đều tiếng Anh; chưa audit ngôn ngữ từng hàng. Có thể có câu tiếng Tây Ban Nha/lỗi encoding; bản gốc, bản dịch và uncertainty giữ để kiểm. Đây không phải validation chất lượng dịch hoặc IAA.
