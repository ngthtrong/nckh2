# Pilot NLP/fusion trên tiếng Việt dịch và nhãn AI

## Material Passport

- Origin: academic-research-suite / experiment-agent, run + validate.
- Date: 08/11/2026, Asia/Taipei.
- Scope: phát triển hồi cứu trên bản dịch và nhãn AI, không phải corpus cứu hộ tiếng Việt gốc hoặc gold chuyên gia.
- Status: **EXECUTED_AND_TECHNICALLY_VERIFIED_WITHIN_AI_SILVER_SCOPE**; 18 fit head và 6 phiên fine-tuning đã chạy CPU. Xem receipt riêng cho biên dịch/kiểm PDF trong handoff.

## Chỉ đạo và thay đổi phạm vi

Người dùng yêu cầu thực hiện kế hoạch, xác nhận chưa có dữ liệu/người gán, sau đó cho phép tự gán lại hoặc tìm nhãn để hoàn thành báo cáo. Vì vậy mở pilot silver riêng; không đổi gate human-gold hoặc ghi giả chuyên gia phê duyệt. Đã thông báo cách dùng CrisisMMD dịch tiếng Việt và nhãn AI. Protocol gốc và addendum T2 được khóa trước mọi dự đoán test của phiên này; không thay cấu hình sau khi thấy hiệu năng test. Test sự kiện đã từng được xem trong pilot trước nên không gọi đây là xác nhận độc lập.

## Dữ liệu thực dùng

Từ 4.261 cặp đã tải/kiểm của pilot CrisisMMD trước, chọn 300 cặp theo hash trong split cũ: 180 train, 60 validation, 60 test. Mỗi split có một nửa từ pool câu có từ khóa rộng help/need/donation/etc, nửa còn lại từ các câu khác, một cặp mỗi nhóm bản trùng. Không dùng nhãn informative để quyết định request. Sampling làm giàu từ khóa trên cohort gốc đã lọc agreed-informative nên không đại diện tỷ lệ yêu cầu tự nhiên.

Codex assistant và native subagents chia ba phần, mỗi phần 100 câu, tạo bản dịch tiếng Việt, nhãn request/no_request/uncertain và lý do trong một lượt. Đây là chia công việc, không phải nhiều người gán cùng mẫu; không có IAA, người gán độc lập hoặc expert approval. Nhãn chỉ dựa trên câu nguồn, không ảnh. Request gồm lời kêu gọi hoặc nhu cầu hỗ trợ chưa đáp ứng như cứu, sơ tán, vật phẩm, quyên góp và tình nguyện. Không chuyển nhãn informative thành request, mức nguy cấp hoặc thứ tự cứu hộ. Không kiểm ngôn ngữ từng hàng; corpus được nguồn mô tả tiếng Anh nhưng có thể có câu ngôn ngữ khác/lỗi encoding.

Bốn uncertain được giữ local và loại trước fit, không lấy bù: còn 179 train (17 request/162 no_request), 58 validation (13/45), 59 test (6/53). Giữ Sri Lanka làm test, Maria làm validation, năm sự kiện khác làm train. Test có 59 nhóm bản trùng, chỉ một sự kiện, không phải 59 sự kiện. Kiểm ID, tweet, group, hash ảnh và câu dịch không giao nhau giữa split. Bản gốc/bản dịch/nhãn ở `thucnghiem/vi_rescue/data/` và `label-batches/`, được ignore có chủ đích; nguồn/hash ở dataset-lock và protocol. Annotation-kit human-gold gốc vẫn giữ nguyên.

## Nhánh frozen đã chạy

DistilBERT multilingual mean-pool 768 chiều và MobileNetV3-Large ImageNet 960 chiều giữ cố định, CPU 4 threads, L2 từng block. TF-IDF và DistilBERT cùng dùng NFKC, bỏ URL/mention, chuẩn hóa khoảng trắng, giữ dấu/phủ định/hoa thường. Ảnh dùng EXIF-RGB và transform chính thức của trọng số ImageNet; đây không phải encoder Small của pilot cũ hoặc model mức ngập của app. Không có câu bị cắt ở max_length 128.

Có 18 fit LR: 6 T0 word/char, 3 T1, 3 I0, 3 F0, 3 F1. Vocabulary chỉ fit train. T0 chọn word 654 chiều, C=10; T1 C=1; I0/F0/F1 C=10. Chọn bằng macro-F1 validation, ngưỡng 0,5; đối chứng chính T1 được chọn từ validation trước test. B0 là lớp đa số; P0 trung bình xác suất T1/I0; hai hàng mask dùng fusion cố định với một block bằng 0, không phải classifier đơn.

Đã lưu 531 dự đoán của 9 cấu hình trên cùng 59 ID, không phải 531 mẫu độc lập. Toàn bộ kết quả so với nhãn AI:

| Cấu hình | Accuracy (%) | Macro-F1 (%) | Recall request (%) | TN/FP/FN/TP |
|---|---:|---:|---:|---|
| B0 | 89,83 | 47,32 | 0,00 | 53/0/6/0 |
| T0 | 84,75 | 45,87 | 0,00 | 50/3/6/0 |
| T1 | 66,10 | 44,13 | 16,67 | 38/15/5/1 |
| I0 | 84,75 | 54,89 | 16,67 | 49/4/5/1 |
| F0 | 86,44 | 46,36 | 0,00 | 51/2/6/0 |
| F1 | 88,14 | 64,91 | 33,33 | 50/3/4/2 |
| P0 | 86,44 | 56,30 | 16,67 | 50/3/5/1 |
| F1_mask_image | 89,83 | 47,32 | 0,00 | 53/0/6/0 |
| F1_mask_text | 83,05 | 59,48 | 33,33 | 47/6/4/2 |
| T2 seed 17 | 81,36 | 52,45 | 16,67 | 47/6/5/1 |
| T2 seed 29 | 76,27 | 49,39 | 16,67 | 44/9/5/1 |
| T2 seed 43 | 77,97 | 50,36 | 16,67 | 45/8/5/1 |

Fusion frozen macro-F1 64,91%, Accuracy 88,14%, recall request 33,33%: nhận ra 2/6, bỏ sót 4. Majority Accuracy 89,83% nhưng recall 0; TF-IDF cũng recall 0. Không chỉ báo các hàng thuận lợi.

Hiệu macro-F1 fusion so với T1 +20,78 điểm phần trăm, CI 95% [-3,93; +42,65]; so với ảnh +10,03 [0,00; +26,80]; so với trung bình xác suất +8,61 [0,00; +25,86]. Bootstrap 2.000 draw ghép cặp theo 59 nhóm, cùng draw cho mọi cấu hình, một sự kiện; CI chưa hiệu chỉnh và không bao gồm sai nhãn/dịch. Các CI chứa hoặc chạm 0, chưa xác lập ưu thế. Che ảnh khiến fusion dự đoán âm toàn bộ; chính sách fallback cần đánh giá riêng.

## Fine-tuning T2 đã chạy

Addendum riêng khóa 2 learning rate × 3 seed, tối đa 5 epoch, patience 2, weighted cross-entropy từ train, batch vật lý 4/hiệu dụng 16, AdamW, dropout 0,2, CPU 4 threads. Toàn bộ encoder và head được cập nhật: 134.735.618 tham số trainable. Sáu phiên thực chạy tổng 23 epoch. Thời gian đến hết dự đoán test khoảng 894 giây; đây là thời gian riêng của bước T2, không phải toàn bộ quy trình hoặc benchmark điện thoại.

Learning rate 2e-5 được chọn bằng trung bình validation macro-F1 0,63544 so với 0,46699 ở 1e-5. Giữ cả ba seed 17/29/43, checkpoint epoch 2/4/4. Receipt chọn mô hình được đóng trước khi tokenize hoặc dự đoán test của T2. Đã lưu 177 dự đoán (3 × 59), không chọn seed theo test. Macro-F1 trung bình 50,73%, min–max 49,39–52,45%; Accuracy trung bình 78,53%; recall request 16,67% ở cả ba seed (mỗi seed nhận ra 1/6). Min–max giữa seed không phải CI. Fine-tuning không cho điểm cao hơn frozen fusion trong bảng này; không có phép kiểm xác nhận riêng về lợi ích fine-tuning. Không fine-tuning chung encoder ảnh–văn bản.

## Kiểm tra và giới hạn

- 24/24 test kỹ thuật bằng fixture tạm: rò rỉ split, đổi hash, sai task, ghi đè và scaling; không phải mẫu nghiên cứu.
- Feature cache: 296 hàng đúng ID/chiều/hash, hữu hạn và chuẩn L2.
- `verification.json`: 10/10 kiểm đạt, tính lại confusion/Accuracy/precision/recall/macro-F1 bằng công thức độc lập, replay cả 2.000 draw CI, kiểm receipt/checkpoint và chọn LR T2 theo validation.
- `encoder-update-check.json`: một tensor backbone thực sự thay đổi so với pretrained trong từng checkpoint của ba seed được chọn; không chỉ huấn luyện head.
- CLI frozen nạp lại thành công ba nhánh T1/I0/F1 trên một cặp validation, sai lệch probability so với cache dưới 1e-5. Đây chỉ là smoke kỹ thuật, không xác nhận fallback hoặc hiệu năng thực địa.

Kiểm tính toán không xác nhận AI silver là nhãn đúng. Hai wrapper đầu lỗi khi chốt receipt sau khi child đã tạo artifact; artifact được kiểm riêng, receipt cũ được giữ, không chạy lại để thay kết quả. Xem `receipt-issue.md`; không tuyên bố mọi command lịch sử đều exit 0. Môi trường mới dùng thư viện CPU sẵn có qua `.pth` chỉ đọc, không hermetic hoàn toàn.

Corpus bản địa, nhãn người độc lập, quality dịch/IAA, gold span/nghiệp vụ, joint encoder fusion, adapter app/backend, Android/E2E và thực địa vẫn mở. Không sửa trọng số serving, raw RQ1–RQ3 hoặc tám sai lệch RQ2. Phép thực nghiệm này hoàn thành một pilot theo phạm vi được điều chỉnh, không chứng nhận toàn bộ VN-00–VN-07 native/human-gold đã đạt.

PDF cuối một mặt/hai mặt đều 199 trang, 50 hình/50 bảng, 27 trích dẫn hợp lệ; build/check, font, bảo toàn và xem trực quan được chốt trong [bàn giao](handoff.md).
