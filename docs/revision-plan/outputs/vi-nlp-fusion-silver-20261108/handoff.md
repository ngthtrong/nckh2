# Bàn giao thực nghiệm NLP/fusion tiếng Việt dịch — 08/11/2026

## Kết quả bàn giao

Đã hoàn thành pilot theo phạm vi người dùng điều chỉnh: tự dịch/gán nhãn AI trên cặp dữ liệu thật có sẵn, chạy mô hình CPU, lưu dự đoán, kiểm lại kết quả và đưa vào báo cáo. Không tuyên bố đã hoàn thành nghiên cứu xác nhận native/human-gold trong kế hoạch ban đầu.

- [PDF một mặt](../../../../report/main.pdf), [PDF hai mặt](../../../../report/build/content-twoside/content.pdf): đều **199 trang**, thân bài **135 trang**, **50 hình và 50 bảng**; 27 tài liệu trích dẫn có số hợp lệ.
- Mục **4.2.16**, trang in **121–123** / trang PDF **142–144**, trình bày dữ liệu, gán nhãn AI, mô hình, fine-tuning, đối chứng, CI và giới hạn. Hai bảng mới là **4.21–4.22**.
- Đã đồng bộ phương pháp, phạm vi, kết luận, phụ lục đối chiếu thuyết minh và biểu mẫu Việt–Anh. Bản tin vi/en vẫn 1/1 trang; tóm tắt vi/en 2/3 trang.
- [Analysis](analysis.md), [ma trận thực hiện](execution-status.csv), [mã và hướng dẫn](../../../../thucnghiem/vi_rescue/README.md), [kế hoạch gốc có cập nhật thực thi](../../vietnamese-nlp-fusion-experiment-plan.md).

## Thực nghiệm thực sự đã chạy

Chọn 300 cặp từ cohort CrisisMMD cũ theo hash và từ khóa, một cặp mỗi nhóm bản trùng. AI dịch và gán nhãn từ câu nguồn trong một lượt; không dùng ảnh để gán nhãn. Giữ riêng bốn ca uncertain trước fit, không lấy bù. Corpus cuối có **179 train / 58 validation / 59 test**, test gồm 6 request và 53 no_request thuộc một sự kiện Sri Lanka đã từng xem trong pilot trước.

Có **18 fit LR** cho TF-IDF, DistilBERT frozen, ảnh frozen và hai fusion; mọi lựa chọn bằng validation. Nhánh **fine-tuning toàn encoder DistilBERT** chạy 2 learning rate × 3 seed, tổng 23 epoch; chọn learning rate 2e-5 theo trung bình validation, báo cả ba seed tại learning rate đó. Không chọn seed tốt nhất theo test. Model, tokenizer, dữ liệu, source, receipt và dự đoán đều có hash. Đầu ra lớn giữ local và được ignore có chủ đích.

| Nhánh | Macro-F1 (%) | Recall request (%) |
|---|---:|---:|
| TF-IDF + LR | 45,87 | 0,00 |
| DistilBERT frozen + LR | 44,13 | 16,67 |
| DistilBERT fine-tuning, trung bình 3 seed | 50,73 | 16,67 |
| Ảnh frozen + LR | 54,89 | 16,67 |
| Fusion DistilBERT frozen + ảnh | 64,91 | 33,33 |

Fusion frozen nhận ra **2/6** request, bỏ sót bốn và có ba dương giả so với nhãn AI. Majority Accuracy 89,83% nhưng recall bằng 0. Hiệu fusion so với DistilBERT frozen +20,78 điểm phần trăm, CI 95% [-3,93; 42,65]; các CI so sánh đều chứa/chạm 0. Không kết luận ưu thế fusion hoặc giá trị nghiệp vụ từ bảng này. [Bảy trường hợp khác nhãn AI](fusion-error-cases.csv) giữ dự đoán các nhánh để xem lại, chưa được phân xử bằng gold.

## Kiểm chứng hoàn tất

- **24/24 test kỹ thuật** bằng fixture tạm; kiểm không giao split, task, hash, ghi đè và scaling. [Log](contracts.log).
- **10/10 kiểm độc lập**: tính lại confusion/Accuracy/precision/recall/macro-F1 từ dự đoán, replay 2.000 bootstrap draw, xác minh T2 dùng chung ID và chọn LR đúng protocol. [Receipt](verification.json).
- Ba checkpoint T2 được chọn đều có tensor backbone thay đổi so với pretrained; [kiểm cập nhật encoder](encoder-update-check.json). Không chỉ huấn luyện head.
- CLI frozen nạp lại đúng cả ba nhánh text/ảnh/cả hai trên một cặp validation; [smoke](cli-smoke.json), chỉ xác nhận kỹ thuật.
- `make -C report content`, `content-twoside`, `make -C report check`, kiểm `build/content-twoside` và `git diff --check` đều đạt ở bản cuối. Receipt cuối: `commands/build_content_numbered.json`, `build_twoside_final.json`, `check_one_final.json`, `check_two_final.json`, `diff_final.json`.
- Đối chiếu nguồn/danh mục/nhãn/PDF đủ 50 hình + 50 bảng ở cả hai bản; phông đều nhúng; không có lỗi tràn khung, float quá lớn, tham chiếu/trích dẫn chưa giải quyết, nhãn trùng hoặc font cảnh báo trong log cuối. [PDF/hash/font](report-checks/delivery-pdfs.json), [floats một mặt](report-checks/floats-one.json), [hai mặt](report-checks/floats-two.json).
- Đã xem tổng thể và các trang đổi cùng trang lân cận ở cả hai bản. Kết luận kết thúc trọn trên trang PDF 156; trang 157 mở tài liệu tham khảo. Trang ký VI vẫn PDF 17, EN kết thúc PDF 20, ảnh chủ nhiệm PDF 21. Sáu trang biểu mẫu PDF 16–21 giống pixel giữa hai bản. Thuyết minh 12 trang ở PDF 178–189, cấu hình scale 1,05 giữ nguyên. [Hồ sơ trực quan](report-checks/visual-review.json), [so pixel](report-checks/form-pixel-comparison.json).
- Giữ nguyên **21 đầu vào cũ** đã khóa: dữ liệu/feature/mã pilot trước và annotation-kit người. Hai PDF báo cáo trong manifest cũ thay đổi đúng phạm vi. `main.pdf` giống byte với bản content một mặt. [Bảo toàn](report-checks/preservation.json), [diff nguồn](report-checks/report-source-diff.patch).

Trong rà PDF đã sửa ba chỗ tràn dòng, trang kết luận chỉ vài dòng và hai tài liệu DistilBERT hiện số [0]. Nguyên nhân trích dẫn là thiếu keyword của nhóm thư mục; đã bổ sung keyword, làm mới auxiliary cache đánh số và thêm kiểm ngăn tái diễn. Bộ kiểm mới bắt đúng hai khóa lỗi trước sửa (receipt `check_citation_regression`), rồi đạt 27/27 ở hai bản cuối. Không sửa tay generated table hoặc kết quả để vượt kiểm.

## Giới hạn còn lại

Dữ liệu là tiếng Việt dịch; nhãn AI chỉ đọc câu nguồn, không có người gán độc lập, IAA, thẩm định dịch hoặc expert approval. Lấy mẫu làm giàu từ khóa và test một sự kiện quen thuộc giới hạn suy luận. Ba seed vẫn cùng 59 ID; 708 hàng dự đoán không phải 708 mẫu độc lập. CI không bao gồm sai nhãn/dịch; min–max seed không phải CI.

Corpus tiếng Việt gốc/gold độc lập, gold span, joint encoder fusion, tích hợp app/backend, Android/E2E và thực địa vẫn chưa hoàn tất. Annotation-kit human-gold vẫn 0 bản ghi/0 nhãn. Không đổi raw RQ hoặc trọng số serving; tám trường RQ2 còn OPEN. Báo cáo vẫn có một trường nhận xét GVHD dạng placeholder, nên kiểm biên soạn không chứng nhận hồ sơ đủ điều kiện nộp.

Hai lỗi wrapper đầu và một lệnh launch T2 sai thứ tự cờ được giữ nguyên trong lịch sử; artifact hợp lệ được kiểm riêng, không chạy lại để thay kết quả. [Chi tiết](receipt-issue.md). Không commit, push hoặc công bố dữ liệu/model.
