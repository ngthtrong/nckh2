# Pilot tiếng Việt dịch và nhãn AI — 08/11/2026

Đã chạy và kiểm kỹ thuật: 179 train / 58 validation / 59 test từ 300 cặp CrisisMMD được AI dịch và gán nhãn, loại bốn ca chưa rõ nghĩa trước fit. Có 18 fit head và 6 phiên fine-tuning CPU; không phải corpus tiếng Việt gốc hoặc nhãn chuyên gia.

Fusion frozen đạt macro-F1 **64,91%**, recall request **33,33%** (2/6). Fine-tuning DistilBERT đạt macro-F1 trung bình **50,73%** qua ba seed tại learning rate chọn bằng validation. Các CI so sánh fusion chứa hoặc chạm 0.

- [Bàn giao và PDF](handoff.md), [analysis đầy đủ](analysis.md), [ma trận trạng thái](execution-status.csv).
- [Protocol frozen](protocol.json), [addendum T2](t2-protocol.json), [khóa corpus](dataset-lock.json).
- [Nguồn](source-search.md), [chỉ đạo](task-authorization.json), [mã/hướng dẫn](../../../../thucnghiem/vi_rescue/README.md).
- [Metric frozen](metrics.csv), [hiệu/CI](paired-effects.csv), [dự đoán](predictions.csv).
- [Bảy trường hợp fusion khác nhãn AI](fusion-error-cases.csv): 4 bỏ sót và 3 dương giả, giữ dự đoán các nhánh để đối chiếu; chưa phân xử bằng gold.
- [Metric T2 theo seed](t2-metrics.csv), [chọn mô hình](t2-model-selection.csv), [receipt T2](t2-evaluation.json).
- [Kiểm độc lập](verification.json), [encoder thực sự cập nhật](encoder-update-check.json), [CLI smoke](cli-smoke.json).
- [Lỗi wrapper và kiểm artifact](receipt-issue.md); không sửa receipt lịch sử.

Tất cả metric đối chiếu nhãn AI từ câu nguồn. Pilot không thay chương trình native/human-gold, phân loại nguy cấp, tích hợp app hoặc đánh giá thực địa. Quy trình PDF và giới hạn cuối nằm trong bàn giao.
