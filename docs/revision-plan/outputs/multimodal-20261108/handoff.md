# Bàn giao P09–P14 trong phạm vi được chọn

## Kết quả

Đã nghiên cứu nguồn, triển khai và chạy benchmark công khai theo lựa chọn của người dùng khi **chưa có người gán nhãn/chuyên gia**. Đây là kết quả mới về mô hình và thực nghiệm, có raw predictions/artifacts, khác đợt chỉ sửa giải trình trước đó.

Từ 12.708 hàng agreed-label CrisisMMD, chọn 4.309 cặp theo protocol rồi loại 48 mẫu thuộc component xuyên split. Giữ **2.971 train / 589 validation / 701 test**; test là sự kiện lũ Sri Lanka, validation là Maria. Tải/giải mã 0 lỗi. Nhánh text học từ câu TF-IDF, nhánh ảnh MobileNetV3 Small ImageNet frozen, nhánh fusion là LR học trên nối đặc trưng. Không huấn luyện lại encoder.

Macro-F1 text **76,60%**, ảnh **76,19%**, fusion **78,35%**, trung bình xác suất **77,12%**. Hiệu fusion–text **+1,75 đpt**, CI **[-2,06; +5,46]**; fusion–ảnh **+2,16 đpt**, CI **[-0,41; +4,80]**. Cả ba CI chứa 0; chưa xác lập ưu thế hoặc tương đương. Khi che ảnh, recall informative fusion chỉ **6,04%**; không bỏ kết quả bất lợi hoặc tune lại sau test.

## Trạng thái từng phase

| Phase | Trạng thái thực tế |
|---|---|
| P09 | DONE_PUBLIC_PROTOCOL; target cứu hộ tiếng Việt vẫn DRAFT, cần chuyên gia |
| P10 | DONE_PUBLIC_INTAKE; bộ chuẩn bị gán nhãn tiếng Việt có 0 bản ghi/0 nhãn, gate NO_GO |
| P11 | DONE_PUBLIC_BASELINES; chưa có đánh giá tiếng Việt hoặc DistilBERT như cam kết |
| P12 | DONE_PUBLIC_ABLATION; cùng target/test IDs, paired group CI; chưa cứu hộ Việt Nam |
| P13 | PARTIAL_LOCAL_CLI_ONLY; inference local đã smoke, chưa đưa vào app/backend/Android |
| P14 | DONE_SCOPED_REPORT_AND_VALIDATION; chưa chấp thuận nghiên cứu/nghiệm thu |

**B1/B3/B4/B5 vẫn PARTIAL** đối với cam kết cứu hộ tiếng Việt và ứng dụng. B5 hiện đã có ablation bổ trợ trên nguồn công khai; không giữ phát biểu tuyệt đối rằng chưa chạy ablation nào. CLI trả task informative, không ánh xạ xác suất đó vào urgency/E_i/rank. Điểm LR năm cờ cũ vẫn chưa được adapter dùng.

## Artifact và kiểm chứng

- [Phân tích đầy đủ](analysis.md), [protocol](protocol.json), [chọn C bằng validation](model-selection.csv), [metrics](metrics.csv), [dự đoán full precision](test-predictions.csv), [CI](paired-effects.csv).
- [Pipeline tái kiểm và CLI](../../../../thucnghiem/multimodal/README.md); cached embeddings và fitted model giữ local dưới `thucnghiem/multimodal/`, không đưa ảnh/text/weights vào Git.
- [Kit tiếng Việt](annotation-kit/README.md): mẫu dữ liệu, nhãn độc lập/adjudication và target approval draft; chưa có nhãn thật.
- 24/24 kiểm artifact/split/hash/metric/reload đạt; 3/3 CI replay khớp; 3/3 route inference trên một fixture test khớp; 10/10 kiểm chặn rò rỉ/phạm vi/nhãn đạt. Inference smoke không phải E2E cứu hộ.
- [Báo cáo chính](../../../../report/main.pdf) và [bản hai mặt](../../../../report/build/content-twoside/content.pdf) **176 trang**; 48 hình/41 bảng. Bản tin Việt/Anh 1/1 trang, tóm tắt 2/3 trang. Build/check cuối đều exit 0; font/visual và phạm vi xem thực ở [layout-review.md](layout-review.md).
- Command/exit/timeout/source hashes tại `commands/`; `final-validation.json` và `final-hashes.json` chốt source/PDF/evidence sau bàn giao. Các receipt lỗi caption và render trước rút gọn được giữ, không dùng thay freeze cuối.

## Bảo toàn và giới hạn

HEAD giữ nguyên so với authorization. Kiểm **9.404 tệp baseline**: 9.388 nguyên byte, 16 thay đổi thuộc nguồn/PDF báo cáo và tài liệu kế hoạch được phép, **0 thay đổi ngoài phạm vi**. Không sửa app/backend, model/dataset/kết quả gốc, giấy tờ nguồn hoặc ảnh cá nhân. `preservation.json` là checkpoint bảo toàn raw; hash của các tệp báo cáo được phép sửa tiếp trong lượt rút gọn được chốt ở manifest cuối. `session-source-diff.patch` tách chỉnh sửa phiên này khỏi dirty worktree có sẵn.

Không đổi RQ1–RQ3, không tạo nhãn từ công thức/LLM, không che eight discrepancies RQ2, không thay dữ liệu cũ để pass. Chưa có đa ngôn ngữ, expert urgency/dispatch validation, E2E/device benchmark mới hoặc giá trị cứu hộ thực địa. Không commit, push, publish hay gửi tin nhắn ra ngoài.

## Điều kiện tiếp theo

Để chuyển từ pilot sang đáp ứng cam kết, cần người phụ trách/chuyên gia chốt target và guideline, dữ liệu ảnh–mô tả Việt Nam được phép dùng, hai nhãn độc lập và adjudication, đánh giá IAA, split theo sự kiện/nguồn và protocol đã khóa. Khi đó mới huấn luyện/đánh giá tiếng Việt, fusion cùng nhiệm vụ rồi xác nhận ngữ nghĩa để tích hợp và đo E2E. Không cần tiếp tục train benchmark tiếng Anh để thay thế các hồ sơ còn thiếu này.
