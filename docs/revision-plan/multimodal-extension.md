# Chuỗi bổ sung P09–P14: mô hình và thực nghiệm

Ngày bắt đầu 08/11/2026, Asia/Taipei. Người dùng yêu cầu nghiên cứu và triển khai kế hoạch sau kiểm tra P00–P08; sau đó xác nhận **chưa có người gán nhãn/chuyên gia, làm benchmark công khai và chuẩn bị bộ gán nhãn**. Đây là phạm vi được thực hiện trong đợt này. Không thay quyết định khoa học bằng giả định đã có chuyên gia hoặc dữ liệu Việt Nam.

| Phase | Phạm vi thực hiện | Điều kiện chưa thể thay thế |
|---|---|---|
| P09 | Chốt protocol pilot informative trên nguồn công khai; đề xuất target Việt Nam riêng | Target khẩn cấp cần người phụ trách/chuyên gia xác nhận |
| P10 | Intake paired CrisisMMD, provenance/license/hash/group split; kit tiếng Việt | Kit trống không phải corpus Việt Nam đã gán nhãn |
| P11 | Text TF-IDF + LR và ảnh frozen + LR trên common target | Không tự suy năng lực tiếng Việt, DistilBERT hoặc NLP nguy cấp |
| P12 | Learned feature fusion và ablation ảnh/text/both, same-test paired CI | Pilot tiếng Anh không đóng ablation cứu hộ Việt Nam |
| P13 | CLI inference local, kiểm tải lại artifact và task boundary | Chưa triển khai app/backend/Android; informative khác E/urgency |
| P14 | Tích hợp kết quả có giới hạn, ledger và kiểm bản báo cáo mới | Build/check không phải chấp thuận nghiệm thu |

Đầu ra và trạng thái cuối của đợt: [multimodal-20261108](outputs/multimodal-20261108/README.md). Protocol phải khóa trước chọn mô hình/test; mọi sai số, nguồn bất đồng hoặc gate chưa đạt được giữ công khai. Không sửa kết quả lịch sử, bộ ảnh cũ, model cũ hoặc thuật toán RQ để tạo vẻ đã hoàn thành.

Đây là nhánh nghiên cứu bổ sung, không thay handoff lịch sử của P00–P08 và không tự tạo RQ4 trong bài đã công bố. Nghiên cứu đầy đủ tiếng Việt/ưu tiên cứu hộ tiếp tục sau dữ liệu ghép cặp, nhãn độc lập, chuyên gia và phép đánh giá tương ứng. Chưa mở nhánh đa ngôn ngữ.
