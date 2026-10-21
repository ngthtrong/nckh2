# Danh mục thực nghiệm được trình bày trong Chương 4

Ngày đối chiếu: **19/10/2026**, theo giờ Việt Nam. Tài liệu này giải thích để người trong nhóm biết thực nghiệm làm gì, đọc file nào và phần nào dùng lại từ bài báo.

Nguồn đối chiếu: [báo cáo content.pdf](D:/nckh-flood-rescue/nckh2/report/build/content/content.pdf), [bài báo tiếng Việt main_vi.pdf](D:/nckh-flood-rescue/nckh2/paper/main_vi.pdf), [nguồn Chương 4](D:/nckh-flood-rescue/nckh2/report/chapters/04-evaluation/sections/results.tex), [cấu hình chọn nguồn benchmark](D:/nckh-flood-rescue/nckh2/report/config/benchmark-sources.json) và các file kết quả liệt kê bên dưới. Đây là việc đọc, đối chiếu kết quả đã lưu; không phải một lần chạy lại các thực nghiệm.

## 1. Cách đọc danh mục

- **File chạy:** chương trình hoặc notebook thực hiện phép đo.
- **Kết quả thô:** dự đoán từng ảnh, phép đo từng request hoặc kết quả từng run/seed. Giữ file này để tính lại được các con số.
- **File đánh giá:** file đã tổng hợp chỉ số, đối chiếu các phương pháp, hoặc code tính các chỉ số đó. Một số thí nghiệm tính đánh giá ngay trong notebook, không có một script đánh giá riêng.
- **Dùng lại:** báo cáo và bài báo dùng cùng kết quả nghiên cứu. Không được tính là hai thực nghiệm độc lập.
- **Bổ sung ngoài bài báo:** có trong báo cáo nhưng không có trong bản `main_vi.pdf` hiện tại. Điều này không tự có nghĩa là vừa chạy mới trong lúc viết báo cáo.
- **Có trên máy, chưa đưa vào báo cáo:** đã có kết quả riêng trong `thuc_nghiem_nq`, nhưng Chương 4 chưa cập nhật các kết quả này.

Các notebook lịch sử có đường dẫn `src/...`; trong cây thư mục hiện tại, nhóm dữ liệu và kết quả tương ứng nằm ở `thucnghiem/...`. Package `demo/` được một số notebook gọi không có trong cây mã hiện tại. Muốn chạy lại phải lấy đúng snapshot mã và môi trường; không chỉ sửa tên thư mục rồi xem là đã tái lập cùng một thực nghiệm. Xem [hướng dẫn tái lập của báo cáo](D:/nckh-flood-rescue/nckh2/report/appendices/reproducibility.tex).

## 2. Bảng tổng quan


| Mã  | Mục báo cáo | Câu hỏi thực nghiệm muốn trả lời                                                                                                         | Quan hệ với bài báo                                          |
| ------ | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| TN01 | 4.2.1          | Nhìn một ảnh, mô hình nhận đúng mức ngập đến đâu? Hay nhầm mức nào?                                                            | Bổ sung ngoài bài báo                                        |
| TN02 | 4.2.2          | Khi mô hình nói mình rất chắc, nó có thường đúng không? Có cơ sở để chỉ gửi thông tin thay vì ảnh không?                | Bổ sung ngoài bài báo                                        |
| TN03 | 4.2.3          | Chuyển mô hình sang dạng chạy trong ứng dụng có làm đổi dự đoán, dung lượng và tốc độ không?                               | Bổ sung ngoài bài báo                                        |
| TN04 | 4.2.4          | Mô hình chạy ngay trong app mất bao lâu và có dự đoán đúng không?                                                                  | Bổ sung ngoài bài báo                                        |
| TN05 | 4.2.5          | Giảm số bit biểu diễn của mô hình để file nhỏ hơn có làm nó sai nhiều hơn hoặc chạy chậm hơn không?                        | Bổ sung ngoài bài báo                                        |
| TN06 | 4.2.6          | Bỏ bớt một phần cấu trúc tính toán rồi huấn luyện tinh chỉnh lại có giúp mô hình gọn, nhanh và vẫn đủ chính xác không? | Bổ sung ngoài bài báo                                        |
| TN07 | 4.2.7          | Điểm khẩn cấp từ năm lựa chọn có cấu trúc có khớp quy tắc nhãn mà nhóm đặt ra không?                                        | Bổ sung ngoài bài báo                                        |
| TN08 | 4.2.8          | Các cách gom báo cáo thành sự kiện khác nhau, cách nào gom đúng hơn?                                                               | Dùng chung kết quả RQ1 của bài báo                         |
| TN09 | 4.2.9          | GPS sai, thời gian lệch hoặc báo cáo bị lặp nhiều lần thì việc gom sự kiện hỏng đến đâu?                                      | Bổ sung ngoài bản main_vi.pdf hiện tại                      |
| TN10 | 4.2.10         | Danh sách ưu tiên có đưa những sự kiện có lợi ích mô phỏng cao lên đầu không?                                                 | Dùng chung kết quả RQ2                                        |
| TN11 | 4.2.11         | Bản sao, khai báo tăng và báo cáo phối hợp có làm thay đổi thứ tự ưu tiên không?                                               | Dùng chung kết quả RQ2; báo cáo trình bày thêm chi tiết |
| TN12 | 4.2.11         | Đổi nhẹ các hằng số của công thức có làm kết quả xếp hạng đổi nhiều không?                                                   | Dùng chung phân tích độ nhạy của bài báo                |
| TN13 | 4.2.12         | Khi dùng cụm dự đoán để lập lịch, đội cứu hộ mô phỏng có bị đưa tới điểm giả, trễ hạn hoặc bỏ sót không?           | Dùng chung kết quả RQ3                                        |
| TN14 | 4.2.13         | Luồng app → server → dashboard và gửi dữ liệu khi mạng yếu có hoạt động đúng không?                                             | Bài báo không có; báo cáo mới dẫn kiểm thử lịch sử   |

Hai bộ kết quả riêng **E2E mới và mạng yếu 2.313 lượt** được ghi ở mục 17–18 của tài liệu này. Chúng chưa được bảng tổng hợp của Chương 4 sử dụng.

## 3. TN01 — Kiểm tra mô hình nhận diện mức ngập từ ảnh

**Mục đích cụ thể:** biết ảnh không ngập, ngập thấp, ngập trung bình, ngập cao được nhận đúng bao nhiêu. Ví dụ, ảnh ngập cao bị đoán thành ngập thấp đáng chú ý hơn nhầm giữa hai mức liền nhau.

- **Dữ liệu thực sự đưa vào TN01:** chỉ **256 ảnh thuộc tập test**, được chọn bằng các dòng có `split = test` trong [CSV chia tập cố định](<D:/nckh-flood-rescue/nckh2/products/fe/model/Edge Ai/split_train_val_test_mobilenetv3_large.csv>). CSV này liệt kê cả 1.702 ảnh, nhưng công cụ chỉ dùng danh sách test để đánh giá; 1.189 ảnh train và 257 ảnh validation không được đưa vào phép đo test này.
- **Nơi đọc các file ảnh:** [Dataset_Flood](D:/nckh-flood-rescue/nckh2/products/fe/model/Dataset_Flood). Thư mục chứa ảnh thực tế; CSV cung cấp đường dẫn tương đối và nhãn để tìm đúng 256 ảnh. CSV không chứa nội dung hình ảnh.
- **Mô hình và nguồn ảnh:** bảng chính dùng model seed 1024. Ảnh do nhóm thu thập/gán nhãn, không phải kết quả đánh giá trên FloodNet hoặc CrisisMMD.
- **File chạy:** [compare_models.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/compare_models.py), dùng Python/PyTorch; đây là công cụ đánh giá mô hình đã có, không huấn luyện lại từ đầu.
- **Kết quả dự đoán từng ảnh của bộ dtset 256 ảnh :** [all_predictions.csv](D:/nckh-flood-rescue/nckh2/products/fe/reports/seed1024/pth_onnx_pte/all_predictions.csv).
- **File đánh giá:** [summary.json](D:/nckh-flood-rescue/nckh2/products/fe/reports/seed1024/pth_onnx_pte/summary.json), [summary.md](D:/nckh-flood-rescue/nckh2/products/fe/reports/seed1024/pth_onnx_pte/summary.md). Hàm `classification_metrics` trong file chạy tính Accuracy, F1, ma trận nhầm lẫn và lỗi nặng. [export_results.py](D:/nckh-flood-rescue/nckh2/report/scripts/export_results.py) đối chiếu ma trận/Accuracy/F1 từ CSV để sinh bảng báo cáo.
- **Tiêu chí:** Accuracy = tỷ lệ đoán đúng; recall từng lớp = trong các ảnh thật thuộc lớp đó nhận ra được bao nhiêu; macro-F1 = chất lượng trung bình của bốn lớp; lỗi nặng = lệch ít nhất hai mức theo định nghĩa severity trong công cụ.
- **Kết quả đang dùng:** Accuracy 75,78%; macro-F1 74,26%; recall lớp high 74,07%; 3 lỗi nặng trên 256 ảnh.
- **Giới hạn:** đây là test trên split đã lưu. Checkpoint huấn luyện seed 1024 chưa có hồ sơ hash split đủ để xác nhận toàn bộ phân công mẫu ban đầu. Chạy lại đánh giá hôm nay không tự khôi phục được hồ sơ huấn luyện còn thiếu.
- **So với bài báo:** không có trong `main_vi.pdf`.

**Luồng TN01:** CSV chia tập → lọc `split = test` → đọc 256 ảnh tương ứng trong `Dataset_Flood` → mô hình dự đoán → lưu 256 dòng vào `all_predictions.csv` → tính các chỉ số trong `summary.json`. `all_predictions.csv` là đầu ra sau dự đoán, không phải file đầu vào để chọn tập test. Các phân tích/bảng sau đó có thể đọc lại đầu ra này để tính lại chỉ số mà không chạy suy luận mới.

## 4. TN02 — Kiểm tra độ đáng tin của confidence và việc chỉ gửi metadata

**Mục đích cụ thể:** nếu ảnh được mô hình gán xác suất 90% trở lên, nhóm muốn biết những ảnh đó có thật sự thường đúng để cân nhắc giảm lượng ảnh cần gửi. Metadata là thông tin báo cáo gửi dạng dữ liệu, thay vì truyền cả ảnh.

- **Dữ liệu:** cùng 256 ảnh test và dự đoán FP32 của TN01, không phải một bộ test mới.
- **File chạy/tính đánh giá:** [compare_models.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/compare_models.py) có `compute_ece` và `classification_metrics`; [build_figures.py](D:/nckh-flood-rescue/nckh2/report/scripts/build_figures.py) tạo hình từ kết quả đã lưu; [export_results.py](D:/nckh-flood-rescue/nckh2/report/scripts/export_results.py) tổng hợp số liệu.
- **Kết quả thô:** [all_predictions.csv](D:/nckh-flood-rescue/nckh2/products/fe/reports/seed1024/pth_onnx_pte/all_predictions.csv).
- **File đánh giá:** [summary.json](D:/nckh-flood-rescue/nckh2/products/fe/reports/seed1024/pth_onnx_pte/summary.json). Đọc ECE, Brier và phần phân tích ngưỡng trong báo cáo.
- **Tiêu chí:** so sánh mức tự tin với tỷ lệ đúng quan sát được; đồng thời đếm số ảnh đáp ứng ngưỡng. Confidence cao nhưng hiếm ảnh đáp ứng thì lợi ích tiết kiệm truyền tải có thể nhỏ.

ECE (Expected Calibration Error) lấy độ lệch của các nhóm, tính trung bình có trọng số theo số ảnh. ECE càng thấp càng tốt; 0 là khớp hoàn toàn theo cách chia nhóm đó.

-ECE tính dựa trên confidence

Brier tính tổng bình phương chênh lệch giữa hai hàng, rồi lấy trung bình trên các ảnh.

			Đoán đúng và tự tin cao → điểm thấp.

			Đoán sai nhưng rất tự tin → bị phạt nhiều.

-Brier lấy

- **Kết quả đang dùng:** ECE 0,04124; Brier 0,34262; ngưỡng confidence ≥ 0,90 có 62/256 ảnh, cả 62 dự đoán đúng trong tập này.
- **Giới hạn:** 62/62 không bảo đảm ảnh mới ngoài thực tế đều đúng. Phân tích này chưa trực tiếp đo số byte tiết kiệm hoặc việc thiếu ảnh gây khó khăn cho điều phối viên. Các bin minh họa trên hình và cấu hình ECE gốc được báo cáo phân biệt riêng.
- **So với bài báo:** không có.

## 5. TN03 — Kiểm tra tính nhất quán của dự đoán sau khi chuyển định dạng, đồng thời so sánh dung lượng file và thời gian suy luận trên CPU máy tính.

**Mục đích cụ thể:** mô hình huấn luyện bằng PyTorch cần chuyển sang định dạng phù hợp ứng dụng. Phép thử kiểm tra việc chuyển đổi có làm thay đổi nhãn dự đoán, và mỗi định dạng có file lớn/nhỏ, suy luận nhanh/chậm ra sao.

- **Dữ liệu:** cùng 256 ảnh test seed 1024 của TN01.
- **Công cụ:** [compare_models.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/compare_models.py), với PyTorch, ONNX Runtime, ExecuTorch. [verify_pipeline.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/verify_pipeline.py) kiểm tra thêm tiền xử lý, provider, mapping nhãn và tương đương PTH/ONNX.
- **Kết quả thô:** [all_predictions.csv](D:/nckh-flood-rescue/nckh2/products/fe/reports/seed1024/pth_onnx_pte/all_predictions.csv).
- **Đánh giá:** [summary.json](D:/nckh-flood-rescue/nckh2/products/fe/reports/seed1024/pth_onnx_pte/summary.json), [verification.json](D:/nckh-flood-rescue/nckh2/products/fe/reports/seed1024/verification/verification.json), [verification.md](D:/nckh-flood-rescue/nckh2/products/fe/reports/seed1024/verification/verification.md). `pairwise_metrics` trong file chạy tính mức đồng thuận và sai khác xác suất.
- **Tiêu chí:** cùng ảnh có trùng nhãn không; xác suất lệch bao nhiêu; dung lượng MiB; trung vị thời gian gọi suy luận.
- **Kết quả đang dùng:** ba định dạng trùng top-1 100% trên 256 ảnh. Trung vị CPU lần lượt PTH 50,93 ms, ONNX 19,08 ms, PTE 34,39 ms.
- **Giới hạn:** số CPU này chỉ bao quanh suy luận, không gồm đọc ảnh/tiền xử lý/nạp model. Không dùng trực tiếp để kết luận runtime nào nhanh nhất trên điện thoại.
- **So với bài báo:** không có.

## 6. TN04 — Đo mô hình khi chạy bên trong ứng dụng

**Mục đích cụ thể:** biết người dùng phải chờ bao lâu cho một ảnh được xử lý trong app, thay vì chỉ đo hàm suy luận trên máy tính.

- **Dữ liệu:** 256 ảnh test/runtime; kết quả hiện tại gắn với model seed 42, khác seed 1024 của benchmark CPU chính.
- **Đóng gói ảnh test:** [build_benchmark_package.py](D:/nckh-flood-rescue/nckh2/products/be/build_benchmark_package.py); gói [benchmark_package.rhb](D:/nckh-flood-rescue/nckh2/products/be/benchmark_package.rhb).
- **File chạy phép đo:** [model_benchmark.dart](D:/nckh-flood-rescue/nckh2/products/fe/app/lib/domain/services/model_benchmark.dart), trong app Flutter. Giao diện benchmark nằm tại [model_benchmark_card.dart](D:/nckh-flood-rescue/nckh2/products/fe/app/lib/presentation/widgets/model_benchmark_card.dart).
- **Kết quả từng ảnh và đánh giá gốc:** [samsung21se.json](D:/nckh-flood-rescue/nckh2/report/evidence/benchmarks/seed42/mobile/samsung21se.json). File có hai object JSON nối tiếp; không đọc nguyên file bằng một lần `json.load` thông thường.
- **Code kiểm tra lại kết quả:** [mobile_evidence.py](D:/nckh-flood-rescue/nckh2/report/scripts/mobile_evidence.py), hàm `audit_mobile`; được [export_results.py](D:/nckh-flood-rescue/nckh2/report/scripts/export_results.py) gọi để kiểm tra sample ID/nhãn, ma trận, Accuracy/F1 và thời gian.
- **Tiêu chí:** Accuracy, macro-F1, thời gian trung bình, P50, P95. P95 mô tả mốc mà 95% ảnh có thời gian không vượt quá mốc đó theo cách tính của app.
- **Kết quả đang dùng:** ONNX và PTE đều Accuracy 75%, macro-F1 73,31%; P50 là 54,50 ms và 29,49 ms; P95 là 112,14 ms và 85,89 ms.
- **Giới hạn:** thiếu metadata thiết bị/APK/hash asset/ngày đo đủ rõ. Tên file không đủ chứng minh cấu hình điện thoại. Đồng hồ app tính `classifyImage`, gồm tiền xử lý native, nên khác phạm vi đồng hồ CPU.
- **So với bài báo:** không có.

## 7. TN05 — Làm mô hình nhỏ hơn bằng cách giảm độ chính xác biểu diễn số

**Tên kỹ thuật:** lượng tử hóa PTQ/QAT INT8.

PTQ: Post-Training Quantization là kỹ thuật chuyển đổi trọng số (weights) và đôi khi là giá trị kích hoạt (activations) của một mô hình học máy/AI từ độ chính xác cao (ví dụ: FP32 - 32-bit floating point) sang độ chính xác thấp hơn (ví dụ: INT8, INT4) **sau khi** mô hình đã được đào tạo xong

QTA: Quantization-Aware Training là kỹ thuật tích hợp quá trình giảm độ chính xác của trọng số mô hình (ví dụ từ FP32 xuống INT8 hoặc 4-bit) ngay trong giai đoạn huấn luyện hoặc tinh chỉnh (fine-tune), giúp mô hình thích nghi trước với sai số số học

**Mục đích cụ thể:** điện thoại có ít dung lượng và tài nguyên tính toán. Nhóm thử biểu diễn trọng số/phép tính bằng số ít bit hơn để file mô hình nhỏ hơn và có thể chạy nhanh hơn. Cần đo xem đổi lại có sai nhiều hơn không. PTQ chuyển đổi sau huấn luyện; QAT có thêm quá trình huấn luyện để mô hình thích nghi với cách biểu diễn mới.

- **Dữ liệu:** test cố định 256 ảnh. Ảnh hiệu chỉnh PTQ lấy từ train theo cấu hình; không dùng test để hiệu chỉnh.
- **File tạo phương án:** [quantize_model.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/quantize_model.py), [qat_finetune.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/qat_finetune.py).
- **File chạy so sánh:** [compare_fp32_ptq_qat.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/compare_fp32_ptq_qat.py); tái sử dụng logic đánh giá của [compare_models.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/compare_models.py).
- **Kết quả thô:** [all_predictions.csv](D:/nckh-flood-rescue/nckh2/products/fe/reports/seed1024/fp32_ptq_qat/all_predictions.csv), [model_disagreement.csv](D:/nckh-flood-rescue/nckh2/products/fe/reports/seed1024/fp32_ptq_qat/model_disagreement.csv).
- **File đánh giá:** [summary.json](D:/nckh-flood-rescue/nckh2/products/fe/reports/seed1024/fp32_ptq_qat/summary.json), [summary.md](D:/nckh-flood-rescue/nckh2/products/fe/reports/seed1024/fp32_ptq_qat/summary.md).


| Phương án | Accuracy | Lỗi nặng | Dung lượng | Trung vị suy luận CPU |
| -------------- | ---------: | -----------: | -------------: | ------------------------: |
| ONNX FP32    |   75,78% |          3 |    16,04 MiB |                14,81 ms |
| PTQ INT8     |   66,80% |         17 |     4,51 MiB |                13,97 ms |
| QAT INT8     |   46,48% |         45 |     4,57 MiB |                53,11 ms |

**Đánh giá:** bản nhỏ hơn chưa đủ để gọi là tốt hơn. PTQ giảm chất lượng và chỉ nhanh hơn ít trong phiên này; QAT hiện vừa giảm chất lượng vừa chậm hơn FP32. Phải so tốc độ trong cùng phiên/cùng runtime.

**So với bài báo:** không có. **Điểm báo cáo cần sửa:** mục 4.3.2 còn nhắc QAT 52,34%/51,17% của một nguồn cũ, trong khi bảng 4.6 hiện dùng seed 1024 với 46,48%. Xem file đề xuất đi kèm.

## 8. TN06 — Bỏ bớt cấu trúc tính toán của mô hình rồi tinh chỉnh lại

**Tên kỹ thuật:** cắt tỉa có cấu trúc (structured pruning).

**Mục đích cụ thể:** thử loại bớt một số kênh/nhóm tính toán của mạng để mô hình cần ít tham số và có thể chạy nhẹ hơn. Sau khi bỏ, mô hình được tinh chỉnh lại để phục hồi chất lượng. Đây là thay cấu trúc tính toán, khác với chỉ lưu các con số bằng ít bit ở TN05.

- **Dữ liệu:** cùng 256 ảnh test; không chọn phương án theo cách chia lại test.
- **File tạo mô hình:** [structured_pruning.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/structured_pruning.py), [export_structured_model.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/export_structured_model.py).
- **File đo so sánh đang dùng:** [compare_structured_pruning.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/compare_structured_pruning.py). Tên thư mục nguồn `prunning_st` có cách viết như hiện tại trong repo; không nhầm với các thư mục benchmark khác.
- **Kết quả thô:** [all_predictions.csv](D:/nckh-flood-rescue/nckh2/products/fe/reports/seed1024/prunning_st/all_predictions.csv), [model_disagreement.csv](D:/nckh-flood-rescue/nckh2/products/fe/reports/seed1024/prunning_st/model_disagreement.csv).
- **File đánh giá:** [summary.json](D:/nckh-flood-rescue/nckh2/products/fe/reports/seed1024/prunning_st/summary.json), [summary.md](D:/nckh-flood-rescue/nckh2/products/fe/reports/seed1024/prunning_st/summary.md).
- **Tiêu chí:** Accuracy/F1, recall, lỗi nặng, số tham số, dung lượng, thời gian trên từng runtime.
- **Kết quả đang dùng:** tham số giảm 1,46%; Accuracy tăng 75,78% → 80,08%; macro-F1 tăng 74,26% → 78,26%; lỗi nặng tăng 3 → 4. PTH nhanh hơn, nhưng ONNX/PTE chậm hơn trong phiên so sánh.
- **Đánh giá:** chưa có một phương án thắng mọi tiêu chí. Mức tăng Accuracy sau thay cấu trúc và tinh chỉnh không chứng minh riêng thao tác bỏ kênh gây ra cải thiện; cần đối chứng tinh chỉnh mô hình gốc tương đương nếu muốn kết luận cơ chế này.
- **So với bài báo:** không có.

## 9. TN07 — Điểm khẩn cấp từ năm dấu hiệu do người dùng chọn

**Mục đích cụ thể:** từ năm lựa chọn như bất tỉnh, khó thở, chảy máu nặng…, tạo một điểm khẩn cấp nhất quán để app lưu và hiển thị. Phép thử hiện tại kiểm tra mô hình có học đúng quy tắc nhãn mà nhóm đặt ra không; không kiểm tra khả năng đọc hiểu tin nhắn tiếng Việt.

- **Dữ liệu huấn luyện:** [urgency_training_SOURCE_FINAL.csv](D:/nckh-flood-rescue/nckh2/products/fe/model/urgency_ei/data/urgency_training_SOURCE_FINAL.csv), đủ 32 tổ hợp của năm cờ. Nhãn là quy tắc OR: có bất kỳ cờ nào thì nhãn dương; 31 tổ hợp dương, một tổ hợp âm.
- **Nguồn và cơ sở nhãn:** [bảng master](D:/nckh-flood-rescue/nckh2/products/fe/model/urgency_ei/data/urgency_reference_master_SOURCE_FINAL.csv), [source_registry.csv](D:/nckh-flood-rescue/nckh2/products/fe/model/urgency_ei/sources/source_registry.csv).
- **File sinh dữ liệu/chạy:** [build_source_aligned_dataset.py](D:/nckh-flood-rescue/nckh2/products/fe/model/urgency_ei/scripts/build_source_aligned_dataset.py), [train_urgency_logistic.py](D:/nckh-flood-rescue/nckh2/products/fe/model/urgency_ei/scripts/train_urgency_logistic.py), [notebook huấn luyện](D:/nckh-flood-rescue/nckh2/products/fe/model/urgency_ei/train_urgency_logistic_colab.ipynb).
- **Mô hình kết quả:** [urgency_logistic_SOURCE_FINAL.json](D:/nckh-flood-rescue/nckh2/products/fe/model/urgency_ei/model/urgency_logistic_SOURCE_FINAL.json).
- **Đánh giá cụ thể:** [đối chiếu quy tắc trên 32 profile](D:/nckh-flood-rescue/nckh2/products/fe/model/urgency_ei/audits/04_rule_baseline_comparison_32_profiles.csv), [sanity 10 vòng](D:/nckh-flood-rescue/nckh2/products/fe/model/urgency_ei/audits/03_model_sanity_10_rounds_unique_profiles.csv), [quality gate](D:/nckh-flood-rescue/nckh2/products/fe/model/urgency_ei/audits/05_final_quality_gate_10_rounds.csv), [FINAL_QUALITY_SUMMARY.md](D:/nckh-flood-rescue/nckh2/products/fe/model/urgency_ei/reports/FINAL_QUALITY_SUMMARY.md). Các CSV audit là kết quả đã lưu; không mặc định script train tái sinh toàn bộ chúng.
- **Kết quả:** khớp quy tắc toàn bảng 100%; một số vòng giữ lại profile dương có recall 0,75 hoặc 0,667.
- **Giới hạn:** không có dữ liệu bệnh nhân, nhãn chuyên gia hay corpus tin nhắn. Quy tắc OR trực tiếp cũng đúng 100% theo chính định n
- ghĩa nhãn, nên chưa chứng minh LR tốt hơn quy tắc. [Adapter backend](D:/nckh-flood-rescue/nckh2/products/be/cluster_service.py) hiện đọc `urgency`/từ khóa, chưa đọc trực tiếp `E_i` mà app gửi; điểm LR chưa được xác nhận xuyên suốt tới phân cụm.
- **So với bài báo:** không có.

## 10. TN08 — Gom các báo cáo cùng một sự kiện: so sánh phương pháp

**Tên trong nghiên cứu:** RQ1 cơ sở.

**Mục đích cụ thể:** nhiều người có thể báo cùng một nơi ngập; ngược lại hai sự kiện gần nhau có thể là hai địa điểm khác nhau. Thực nghiệm đo khả năng gom đúng người báo cùng sự kiện, tránh tách một sự kiện thành nhiều cụm hoặc gộp nhầm hai sự kiện.

- **Dữ liệu:** [thucnghiem/data/gold](D:/nckh-flood-rescue/nckh2/thucnghiem/data/gold), Generator 3.0, 80 run. Run 1–20 phát triển; 21–40 chọn cấu hình; 41–80 test. Mỗi run có `algorithm_input.json` để thuật toán đọc và `ground_truth.json` chỉ dành cho đánh giá.
- **File chạy và đánh giá:** [Benchmark_Cij_Baselines_Colab.ipynb](D:/nckh-flood-rescue/nckh2/thucnghiem/results/Benchmark_Cij_Baselines_Colab.ipynb). Notebook thực hiện chọn tham số, chạy các phương pháp và tính chỉ số/so sánh. Muốn tái lập dùng snapshot `6ac75c202d04934deb46d84486132e54d42d735f` theo phụ lục, giữ đúng protocol.
- **Cấu hình đã chọn:** [selected_configs.json](D:/nckh-flood-rescue/nckh2/thucnghiem/results/cij_baseline_benchmark_results/selected_configs.json).
- **Kết quả từng run:** [benchmark_test_40runs.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/cij_baseline_benchmark_results/benchmark_test_40runs.csv).
- **File đánh giá:** [benchmark_summary.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/cij_baseline_benchmark_results/benchmark_summary.csv), [paired_comparisons.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/cij_baseline_benchmark_results/paired_comparisons.csv), [matched_density_test_diagnostics.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/cij_baseline_benchmark_results/matched_density_test_diagnostics.csv).
- **Tiêu chí:** ARI và pairwise F1 đo mức khớp cụm với nhãn sự kiện; đường kính cụm mô tả mức trải rộng; tỷ lệ điểm đến giả cho biết báo cáo giả còn tạo ra địa điểm điều phối riêng không. Khoảng tin cậy và kiểm định ghép cặp đánh giá độ chắc chắn của chênh lệch.
- **Kết quả:** Additive Louvain ARI 0,9191; Product Leiden 0,9165; Product Louvain 0,9072. Chưa xác lập ưu thế Product sau Holm. Product có tỷ lệ điểm đến giả 16,49%, dù không hút tin giả vào điểm thật.
- **So với bài báo:** dùng chung Bảng 1 và các tương phản RQ1, trang 10–11 của `main_vi.pdf`. Không phải lần đo độc lập mới của báo cáo.

## 11. TN09 — Kiểm tra gom cụm khi GPS sai, thời gian lệch, báo cáo bị nhân bản

**Tên trong nghiên cứu:** RQ1 stress.

**Mục đích cụ thể:** một thuật toán gom đúng trên dữ liệu sạch có thể hỏng khi người dùng báo sai vị trí, gửi muộn hoặc hệ thống nhận bản sao. Phép thử đo mức giảm chất lượng dưới từng lỗi đầu vào cố định.

- **Dữ liệu:** cùng 40 run test của TN08. Bảy điều kiện: gốc; GPS Gaussian 100/300 m; thời gian Gaussian 15/60 phút; bản sao exact tổng số 2×/5×. Cùng nhiễu được áp cho các phương pháp trong một run; không chọn lại tham số theo nhiễu.
- **File chạy:** [RQ1_Reviewer_Stress_Colab.ipynb](D:/nckh-flood-rescue/nckh2/thucnghiem/results/RQ1_Reviewer_Stress_Colab.ipynb).
- **Notebook đã có đầu ra:** [RQ1_Reviewer_Stress_Colab.executed.ipynb](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq1_results/RQ1_Reviewer_Stress_Colab.executed.ipynb).
- **Kết quả từng run:** [rq1_stress_per_run.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq1_results/aggregate/rq1_stress_per_run.csv); checkpoint tại [checkpoints](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq1_results/checkpoints).
- **Đánh giá:** [rq1_stress_summary.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq1_results/aggregate/rq1_stress_summary.csv), [rq1_stress_paired_effects.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq1_results/aggregate/rq1_stress_paired_effects.csv), [duplicate mapping](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq1_results/aggregate/rq1_stress_duplication_mapping.csv). Phép tính nằm trong notebook.
- **Tiêu chí:** ARI/F1 trên báo cáo gốc để các mức sao chép cùng đơn vị đánh giá; hiệu ghép cặp so với điều kiện gốc; tổng batch 40 × 7 × 5 = 1.400 lần fit.
- **Kết quả Product:** ARI gốc 0,9072; GPS 300 m còn 0,7816; thời gian 60 phút còn 0,7442; bản sao 5× còn 0,2964.
- **Giới hạn:** các mức này do nhóm đặt, chưa phải phân bố sai số thực địa. Cơ chế gây suy giảm chưa được cô lập. Không gộp nguồn chính `rq1_results` với lần lặp `rq1_results_v2`.
- **So với bài báo:** bộ bảng GPS/thời gian/bản sao 5× này không có trong `main_vi.pdf` hiện tại; đây là bổ sung so với PDF đó.

## 12. TN10 — Kiểm tra danh sách ưu tiên có xếp đúng sự kiện cần ưu tiên không

**Tên trong nghiên cứu:** RQ2 alignment.

**Mục đích cụ thể:** một công thức điểm có vẻ hợp lý vẫn có thể xếp sai. Phép thử kiểm tra năm sự kiện đầu danh sách có phù hợp với lợi ích được bộ sinh định nghĩa độc lập hay không.

- **Dữ liệu:** Candidate 4.1 riêng, test seed 3000–3039. Bộ này khác Generator 3.0 của TN08. Dùng nhóm sự kiện đúng do evaluator cung cấp (oracle grouping) để tách lỗi xếp hạng khỏi lỗi gom cụm.
- **File chạy và đánh giá:** [RQ2_Priority_Robustness_Colab.ipynb](D:/nckh-flood-rescue/nckh2/thucnghiem/results/RQ2_Priority_Robustness_Colab.ipynb).
- **Vị trí dữ liệu khi chạy notebook:** cache `candidate_v4_locked.zip` và file `.sha256` trên Drive/thư mục làm việc, được sinh/đọc bằng package `demo.data.generate`. Chưa tìm thấy cache và package này trong cây hiện tại; cần lấy đúng nguồn trước khi chạy lại.
- **Kết quả từng seed:** [rq2_rank_alignment_test.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq2_results/rq2_rank_alignment_test.csv).
- **File đánh giá:** [rq2_summary.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq2_results/rq2_summary.csv), [rq2_paired_comparisons.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq2_results/rq2_paired_comparisons.csv).
- **Tiêu chí:** NDCG@5 đo mức phù hợp của top 5 với lợi ích mô phỏng; Spearman đo tương quan thứ hạng; overlap top-5 đo phần giao hai danh sách top 5. Lợi ích mô phỏng không phải lợi ích cứu hộ đã được quan sát ngoài thực tế.
- **Kết quả:** điểm có chặn NDCG@5 0,6669; legacy 0,6548; chỉ số người 0,6709; ngẫu nhiên 0,6763. Spearman của điểm có chặn khoảng −0,0304. Chưa xác lập lợi thế tổng quát sau Holm; cũng không được nói ngẫu nhiên chắc chắn tốt hơn chỉ từ trung bình.
- **So với bài báo:** dùng chung kết quả RQ2 trang 10–13, Bảng 2/Hình 3.

## 13. TN11 — Kiểm tra thứ tự ưu tiên khi có bản sao hoặc khai báo thao túng

**Mục đích cụ thể:** người gửi nhiều bản sao hoặc nhiều báo cáo phối hợp có đẩy một điểm lên đầu danh sách không? Việc kiểm tra này giúp tránh nhầm “công thức có giới hạn điểm” với “tin tức đáng tin”.

- **Dữ liệu/công cụ:** cùng Candidate 4.1 và notebook RQ2 của TN10. Các tình huống gồm exact 2×/5×/10×, gần trùng, mâu thuẫn mức ngập/khẩn cấp, thiếu dữ liệu, khai tăng số người/yếu thế và chiến dịch phối hợp confidence cao.
- **Kết quả từng tình huống:** [rq2_robustness_test.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq2_results/rq2_robustness_test.csv).
- **Đánh giá:** [rq2_summary.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq2_results/rq2_summary.csv), [rq2_paired_comparisons.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq2_results/rq2_paired_comparisons.csv); tính trong notebook RQ2.
- **Tiêu chí:** drift điểm = điểm đổi bao nhiêu; drift thứ hạng = vị trí đổi bao nhiêu; churn = danh sách ưu tiên đầu bị thay thành viên bao nhiêu; false-priority lift = mức bị đẩy ưu tiên của đối tượng giả theo định nghĩa evaluator.
- **Kết quả:** exact copy cho drift 0 khi grouping cố định. Chiến dịch confidence cao gây drift 0,1688, trong khi legacy là 0,0309. Một số trường hợp khai tăng số người/yếu thế cũng làm điểm có chặn nhạy hơn legacy.
- **Giới hạn:** bất biến khi nhóm cố định không bảo đảm cả pipeline bất biến: TN09 cho thấy bản sao vẫn có thể làm thay đổi phân cụm.
- **So với bài báo:** dùng chung kết quả robustness RQ2; Chương 4 trình bày nhiều dòng chi tiết hơn Bảng 2 của bài báo.

## 14. TN12 — Thử thay nhẹ các hệ số của công thức ưu tiên

**Mục đích cụ thể:** xem kết luận có quá phụ thuộc vào một bộ hằng số do nhóm chọn hay không. Mỗi lần đổi một hằng số, giữ các phần còn lại theo protocol rồi tính lại chất lượng top 5.

- **Dữ liệu/công cụ:** notebook RQ2; 21 cấu hình trên 40 seed test, tức 840 quan sát seed/cấu hình.
- **Kết quả từng seed/cấu hình:** [rq2_parameter_sensitivity_test.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq2_results/rq2_parameter_sensitivity_test.csv).
- **Đánh giá:** [rq2_parameter_sensitivity_summary.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq2_results/rq2_parameter_sensitivity_summary.csv).
- **Tiêu chí/kết quả:** khoảng min–max NDCG@5 trung bình giữa các mức của từng hằng số đều dưới 0,01; lớn nhất khoảng 0,00546.
- **Giới hạn:** ít thay đổi nhưng chất lượng xếp hạng vẫn yếu. Ổn định trong một lân cận không chứng minh các trọng số là lựa chọn đúng cho chính sách cứu hộ.
- **So với bài báo:** dùng chung mục 4.1/Bảng 3, trang 11–12.

## 15. TN13 — Đo hệ quả điều phối sau khi dùng cụm dự đoán

**Tên trong nghiên cứu:** RQ3 dispatch. Chữ EndToEnd trong tên notebook này chỉ chuỗi thuật toán đến mô phỏng điều phối; không phải E2E trình duyệt ở mục 17.

**Mục đích cụ thể:** một sự kiện bị tách thành hai cụm có thể làm đội đi lặp; hai sự kiện bị gộp có thể làm bỏ sót một nơi; báo cáo giả có thể làm đội đi tới nơi không có nhu cầu thật. Phép thử đo các hệ quả đó trong bộ mô phỏng đã định nghĩa.

- **Dữ liệu:** Candidate 4.1, 40 seed test và ba điều kiện nguồn lực/seed. Bộ lập lịch chỉ nhìn cụm dự đoán và thông tin cho phép; nhãn sự kiện, deadline và harm dùng cho evaluator sau khi đã có lịch.
- **File chạy:** [RQ3_EndToEnd_Dispatch_Colab.ipynb](D:/nckh-flood-rescue/nckh2/thucnghiem/results/RQ3_EndToEnd_Dispatch_Colab.ipynb), cần cùng cache và nguồn `demo/` như TN10.
- **Kết quả theo điều kiện:** [rq3_dispatch_test.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq3_results/rq3_dispatch_test.csv).
- **Chẩn đoán chi tiết:** [rq3_destination_assignments.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq3_results/rq3_destination_assignments.csv), [rq3_partition_losses.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq3_results/rq3_partition_losses.csv).
- **File tính đánh giá chính:** [recompute_seed_level.py](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq3_results/recompute_seed_level.py). Lấy trung bình ba điều kiện trong mỗi seed rồi so 40 cặp seed, bootstrap 5.000 và Holm.
- **File kết quả đánh giá chính:** [rq3_dispatch_test_seed.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq3_results/rq3_dispatch_test_seed.csv), [rq3_paired_comparisons_seed.csv](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq3_results/rq3_paired_comparisons_seed.csv), [provenance tái phân tích](D:/nckh-flood-rescue/nckh2/thucnghiem/results/rq3_results/rq3_seed_level_reanalysis_provenance.json).
- **Tiêu chí:** harm mô phỏng, tỷ lệ trễ hạn, thời gian tới nơi, số chuyến lặp/đến điểm giả, số sự kiện thật chưa được phục vụ và các chỉ số phụ theo protocol. Harm thấp và tỷ lệ trễ thấp là tốt; không gọi harm là số người chết.
- **Kết quả báo cáo dùng:** so với legacy trên phân hoạch Product, điểm có chặn làm harm tăng 14,34, nhưng giảm trễ hạn 1,88 điểm phần trăm; cả hai chưa có ý nghĩa sau Holm. Kém hơn gần nhất trước về các chỉ số chính trong mô phỏng.
- **Chú ý đơn vị:** effect ở bảng được đổi hướng để số dương nghĩa là cải thiện. Không diễn giải dấu âm thành giảm harm khi bảng đang dùng quy ước này. Không tăng cỡ mẫu từ 40 seed lên 120 quan sát độc lập.
- **So với bài báo:** dùng chung kết quả RQ3 Bảng 2/Hình 4; không phải kết quả chạy mới của báo cáo.

## 16. TN14 — E2E và mạng yếu mà bản báo cáo hiện tại đã trình bày

Nguồn báo cáo đang dùng là [đối chiếu nghiệm thu 27/09/2026](D:/nckh-flood-rescue/nckh2/docs/nghiem-thu/doi_chieu_thuyet_minh.md), không phải bộ kết quả mới trong `thuc_nghiem_nq`.

- **Mục đích:** kiểm tra thao tác trên app web được server tiếp nhận và dashboard xử lý; mất mạng thì lưu hàng đợi, có mạng thì đồng bộ; mạng khác nhau chọn ảnh gốc/ảnh nén/metadata.
- **File chạy lịch sử tương ứng hiện có:** [products/scripts/demo/e2e/e2e_system.py](D:/nckh-flood-rescue/nckh2/products/scripts/demo/e2e/e2e_system.py), Docker + Playwright/Chromium. Bản thực nghiệm riêng của bạn là file khác tại mục 17.
- **File ghi nhận đánh giá lịch sử:** tài liệu nghiệm thu nêu 46/46. Đây là ghi nhận lịch sử, không phải `checks.csv` mới được tái tạo trong lần biên soạn báo cáo.
- **Chương 4 nêu:** mạng không giới hạn gửi ảnh gốc khoảng 53,6 KB; 300 kbit/s gửi ảnh nén khoảng 42,4 KB; 20 kbit/s chỉ gửi thông tin. Đây là một ảnh/kịch bản cụ thể, không phải mức giảm trung bình toàn bộ dữ liệu.
- **Công cụ mạng yếu gốc:** [products/be/experiments/weak_network.py](D:/nckh-flood-rescue/nckh2/products/be/experiments/weak_network.py). Bản riêng có kết quả mới được liệt kê ở mục 18.
- **Phạm vi chưa cập nhật:** mục 4.2.13 và 4.3.4 còn ghi chưa có bộ kết quả độ trễ mạng yếu, trong khi thư mục riêng hiện có đủ 2.313 lượt. Báo cáo cũng chưa đưa hai lượt E2E mới vào bảng.
- **So với bài báo:** `main_vi.pdf` không có E2E hệ thống, mạng yếu, Android/SMS.

## 17. Kết quả E2E mới hiện có trên máy — chưa được đưa vào Chương 4

**Mục đích cụ thể:** tự động mở app web và dashboard, thực hiện các thao tác như người dùng, rồi đối chiếu với API và dữ liệu backend để biết cả luồng có hoạt động đúng không.

- **Runner:** [e2e_system.py](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_e2e/e2e_system.py).
- **Môi trường:** [docker-compose.yml](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_e2e/docker-compose.yml), [requirements.txt](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_e2e/requirements.txt), Docker Desktop, Python, Playwright/Chromium. [README](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_e2e/README.md) giải thích chạy/resume.
- **Dữ liệu:** gold `algorithm_input.json` của run đã chọn; [CSV validation](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/split_val_mobilenetv3_large.csv); một ảnh high/JPG, hiện là `high/floods_cambodia_avid_w.jpg`. 257 là số dòng CSV cho phép chọn ảnh, không phải số ảnh được chạy qua UI trong mỗi lượt.
- **Đánh giá nằm ngay trong runner:** hàm `write_summary` tổng hợp PASS/FAIL/CHƯA CÓ thành `checks.csv` và `summary.json`; checkpoint lưu stage đã hoàn tất.


| Lượt đã đọc   |     Dữ liệu seed | Kết quả từng tiêu chí                                                                                                    | Đánh giá tổng hợp                                                                                                            |
| --------------------- | -------------------: | ------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| run_001, 19/10/2026 | 316 báo cáo gold | [checks.csv](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_e2e/results/run_001__e2e-20261019-162957-186810/checks.csv) | [summary.json](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_e2e/results/run_001__e2e-20261019-162957-186810/summary.json) |
| run_002, 19/10/2026 | 334 báo cáo gold | [checks.csv](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_e2e/results/run_002__e2e-20261019-170303-022823/checks.csv) | [summary.json](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_e2e/results/run_002__e2e-20261019-170303-022823/summary.json) |

**Cả hai summary hiện ghi:** `complete`, đủ năm stage `dashboard`, `app`, `adaptive_300`, `adaptive_20`, `no_gps`; mỗi lượt có **45 PASS, 0 FAIL, 1 CHƯA CÓ**. Mục CHƯA CÓ là thông báo cho người dùng giải thích trạng thái AI không khả dụng trên web. Không được đổi cách ghi thành “46/46 PASS”.

**Tiêu chí đọc kết quả:** trạng thái hoàn tất + đủ năm mục trong `completed_stages` + không FAIL; vẫn công bố CHƯA CÓ. `stage_count=5` riêng lẻ chưa đủ vì runner ghi sẵn tổng số stage ngay cả khi bị ngắt.

**Checkpoint:** [run_001](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_e2e/checkpoints/run_001__e2e-20261019-162957-186810.json), [run_002](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_e2e/checkpoints/run_002__e2e-20261019-170303-022823.json).

**Giới hạn hồ sơ lúc rà soát:** kết quả/checkpoint của cả hai lượt có trên máy, nhưng không tìm thấy `manifest.json` của hai lượt tại đường dẫn log chuẩn; thư mục log hiện chỉ thấy log run_002. Không coi hồ sơ truy vết là đầy đủ chỉ vì summary complete. Cần giữ các file còn lại và xác minh bản sao manifest/log nếu có; không tự viết lại manifest như thể được tạo ở thời điểm chạy.

**Giới hạn kết luận:** hai run dùng cùng một ảnh; chưa chứng minh chất lượng AI, SMS hay độ bền Android. Đây là hai kịch bản dữ liệu, không phải 80 run hoặc 257 lượt thử ảnh độc lập. Kết quả đang khác thông tin “interrupted” ở lượt cũ được trao đổi trước đó; bảng này ghi trạng thái mới đã đọc từ file.

## 18. Kết quả mạng yếu hiện có — chưa được đưa vào Chương 4

**Mục đích cụ thể:** so xem gửi chỉ thông tin, ảnh nén và ảnh gốc mất bao lâu, có tới server đúng trong thời hạn không, và truyền bao nhiêu byte khi băng thông bị giới hạn.

- **File chạy và tính đánh giá:** [weak_network.py](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_weak_network/weak_network.py). Có chế độ `--run`, `--resume`, `--summarize-only`. [README](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_weak_network/README.md) hướng dẫn backend riêng; đoạn trạng thái “chưa chạy” trong README không phản ánh lượt kết quả đã tồn tại.
- **Dữ liệu:** [257 ảnh validation](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/split_val_mobilenetv3_large.csv) từ [Dataset_Flood](D:/nckh-flood-rescue/nckh2/products/fe/model/Dataset_Flood). 257 × 3 mạng × 3 chế độ × 1 lần = 2.313 lượt. Metadata dùng payload cố định; runner không chạy MobileNetV3/Flutter.
- **Mạng giả lập:** 50/400/5.000 kbit/s, RTT 600/200/50 ms; timeout metadata 30 giây, upload 60 giây. Tên 2G/3G/4G là tên cấu hình của nhóm, không phải quan sát mạng viễn thông thực.
- **Kết quả từng request:** [weak_network.csv](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_weak_network/results/20261005-102040/weak_network.csv).
- **File đánh giá tổng hợp:** [weak_network.md](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_weak_network/results/20261005-102040/weak_network.md).
- **Hồ sơ:** [checkpoint](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_weak_network/checkpoints/20261005-102040.json), [manifest](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_weak_network/logs/20261005-102040/manifest.json), [console](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_weak_network/logs/20261005-102040/console.txt).


| Mạng        | Gửi      |      Thành công | Median thành công | P95 thành công |
| -------------- | ----------- | ------------------: | --------------------: | -----------------: |
| 2G giả lập | Metadata  |   257/257 — 100% |             1,488 s |          1,524 s |
| 2G giả lập | Ảnh nén |   257/257 — 100% |             5,666 s |         25,230 s |
| 2G giả lập | Ảnh gốc | 230/257 — 89,49% |             5,526 s |         38,973 s |
| 3G giả lập | Metadata  |   257/257 — 100% |             0,476 s |          0,495 s |
| 3G giả lập | Ảnh nén |   257/257 — 100% |             1,056 s |          3,798 s |
| 3G giả lập | Ảnh gốc | 255/257 — 99,22% |             1,350 s |         14,117 s |
| 4G giả lập | Metadata  |   257/257 — 100% |             0,145 s |          0,165 s |
| 4G giả lập | Ảnh nén |   257/257 — 100% |             0,211 s |          0,532 s |
| 4G giả lập | Ảnh gốc | 256/257 — 99,61% |             0,259 s |          1,762 s |

**Kết quả trạng thái:** checkpoint complete; đủ 2.313 lượt hợp lệ. Có 27 NETWORK_ERROR và 3 UNSUPPORTED_IMAGE; ba lỗi định dạng tương ứng ảnh AVIF gốc bị từ chối ở ba cấu hình mạng. Hoàn tất kế hoạch đo không có nghĩa tất cả request thành công.

**Cách đánh giá đúng:** luôn đọc tỷ lệ thành công cùng median/P95. Các thời gian này chỉ tính request thành công; ảnh gốc 2G có median thấp hơn ảnh nén không chứng minh ảnh gốc tốt hơn vì có nhiều lượt thất bại. Mỗi ảnh/điều kiện chỉ đo một lần, chưa có lặp nhiều phiên. Byte proxy không phải toàn bộ overhead TCP/IP, và lỗi HTTP 415 không phải lỗi mạng.

## 19. Đối chiếu ngắn với bài báo và cách dùng lại kết quả


| Nội dung                                                             | Trong main_vi.pdf                              | Trong báo cáo          | Cách mô tả nguồn                                                        |
| ----------------------------------------------------------------------- | ------------------------------------------------ | -------------------------- | ----------------------------------------------------------------------------- |
| RQ1 cơ sở                                                           | Bảng 1, trang 10–11                          | 4.2.8                    | Dùng chung artifact RQ1                                                    |
| RQ2 xếp hạng và robustness                                         | Trang 10–13, Bảng 2                          | 4.2.10–4.2.11           | Dùng chung artifact Candidate 4.1                                          |
| Độ nhạy hệ số                                                    | 4.1/Bảng 3                                    | Bảng 4.12               | Dùng chung phân tích 21 cấu hình/40 seed                               |
| RQ3 điều phối                                                      | Bảng 2/Hình 4                                | 4.2.12                   | Dùng chung phân tích 40 cặp seed                                        |
| RQ1 nhiễu GPS/thời gian/bản sao 5×                                | Không có bộ bảng này trong PDF hiện tại | 4.2.9                    | Bổ sung so với bản main_vi.pdf                                           |
| Mô hình ảnh, confidence, runtime, nén, bớt kênh tính toán, LR | Không                                         | 4.2.1–4.2.7             | Kết quả riêng của phần mô hình/ứng dụng                            |
| E2E và mạng yếu                                                    | Không                                         | Dẫn lịch sử ở 4.2.13 | Phân biệt dữ liệu lịch sử và hai bộ kết quả mới chưa cập nhật |

Báo cáo dùng [export_results.py](D:/nckh-flood-rescue/nckh2/report/scripts/export_results.py) đọc các JSON/CSV gốc để sinh bảng tại [report/generated/tables](D:/nckh-flood-rescue/nckh2/report/generated/tables). [provenance.json](D:/nckh-flood-rescue/nckh2/report/generated/provenance.json) ghi nguồn trực tiếp. Việc xuất lại bảng hoặc vẽ lại hình không phải một lượt suy luận/huấn luyện/mô phỏng mới.

Các bảo đảm toán học trong bài báo, ví dụ chặn khoảng cách cạnh hay bất biến điểm với bản sao exact khi grouping cố định, là kết quả lý thuyết có điều kiện. Không đếm chúng thành thực nghiệm thiết bị hoặc bằng chứng cứu hộ ngoài thực địa.

## 20. Lưu kết quả để tránh thất lạc

[Gitignore E2E](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_e2e/.gitignore) bỏ qua output trong logs/results/checkpoints/data/uploads; việc checkout hoặc chép file từ nhánh không bảo đảm có các file chạy cục bộ. Hiện cả thư mục `thuc_nghiem_nq` còn hiển thị untracked trên nhánh đang làm việc.

Mỗi lần chạy nên giữ một bộ gồm kết quả thô, đánh giá, checkpoint, manifest/hash, log và mã nguồn tương ứng; lưu cả bản không đạt. Sao lưu có kiểm soát hoặc đưa các artifact cần lưu vào Git bằng lựa chọn cụ thể. Không xóa/ghi đè bộ cũ chỉ để giữ một kết quả thuận lợi.

Đọc tiếp [đề xuất chạy lại, chạy thêm và đánh giá Chương 4](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/docs_thuc_nghiem/recommendations_chapter4.md) để chọn việc nên làm trước.
