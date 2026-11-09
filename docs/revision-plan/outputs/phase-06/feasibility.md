# P06 — tính khả thi ablation ảnh/văn bản/both

Quyết định: **NO_GO cho thí nghiệm hiện tại**. Đây là kết quả feasibility, không phải ablation đã thực hiện và không hoàn thành cam kết NLP/fusion. Đã đọc P01 scope/dataflow, P02 data card và P03 rq-claims/analysis.

Ba target khác nhau: model ảnh dự đoán bốn mức ngập; LR nhận năm cờ và tái hiện OR; graph/ranking dùng các trường quan sát và evaluator mô phỏng. Không có hàm so sánh Accuracy ảnh với fidelity OR để đo đóng góp của modality. Tin nhắn được thu nhận không tự trở thành nhánh text model đã huấn luyện.

Tìm bổ sung trong working tree products/thucnghiem (code Python/Dart/notebook), tiếp nối audit 20 refs mới, chưa thấy trained free-text NLP hoặc paired image/text gold có common target. Dataset-search có dossier và dữ liệu text nhãn chủ đề; không mặc định có record ảnh–tin nhắn–sự kiện hoặc gold urgency/dispatch. Kết luận có giới hạn repo/refs, không phủ nhận nghiên cứu ngoài repo.

Nếu mask F/E của các report mô phỏng, đó là information-source sensitivity trên trường có cấu trúc. Không gọi đó là ablation image-only/text-only của một mô hình đa phương thức. Nhãn target do chính fusion formula tạo sẽ dẫn đến đánh giá vòng tròn; latent benefit trong Candidate 4.1 tuy do evaluator khác sinh vẫn là mô phỏng, không paired clinical/field gold.

Protocol tương lai chỉ có thể GO_PROTOCOL sau khi xác định cùng target, report IDs, paired inputs, nhãn độc lập với formula, quyền sử dụng và group split. Cần người gán theo guideline và chuyên gia cứu hộ xác nhận target/dispatch policy; ghi missing-modality, consent/privacy, chi phí thu thập và lỗi thiên lệch. Chưa có ngân sách hoặc nhân lực được xác nhận, không tự tổ chức người tham gia.

Đề xuất sau gate: giữ cùng test IDs và common target; baseline majority/rule và từng modality; cấu hình/budget đã khóa trước test; grouped paired bootstrap theo sự kiện/nguồn, định nghĩa Holm family trước; đánh giá riêng mất modality. Chưa train, tải corpus hoặc triển khai fusion mới.

Đoạn giải trình B5 đưa vào scope/conclusion ở P07: chưa đủ điều kiện khoa học cho phép so image/text/both hiện tại; đề tài giữ gap NLP và paired gold công khai, thay vì tạo bảng performance không cùng nhiệm vụ.
