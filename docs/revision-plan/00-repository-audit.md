# Audit repository và bằng chứng

## 1. Phạm vi, nguồn và trạng thái

Khảo sát ngày 07/11/2026 tại nhánh `main`, HEAD `379021d` (hash đầy đủ trong `evidence/audit-snapshot.json`). Đã đọc working tree, không giả định nó bằng HEAD. Có nhiều sửa đổi LaTeX/PDF và xóa sơ đồ từ trước; có `ISDS/`, `report/RULES.md`, audit layout và script kiểm float chưa track. Không checkout/reset/fetch/commit, không khôi phục những tệp đã bị người dùng xóa.

Nguồn nhận xét chính là `evidence/user-request.txt`: bản tổng hợp được người dùng cung cấp. **`tmp.md` ở gốc repo cũng lưu tổng hợp nhận xét 06–20**, tương ứng B1–B5/C1–C7/D1–D3, gồm cả phần diễn giải và số liệu đối chiếu của người tổng hợp. Tệp tự phân biệt nội dung được ghi lại với diễn giải, không xem toàn bộ là lời Hội đồng nguyên văn. Chưa tìm thấy biên bản có chữ ký hoặc phiếu A1–D3 gốc. `docs/src_review_1_2_3.md` là nhận xét bài báo, còn `thuc_nghiem_nq/docs_thuc_nghiem/nhan_xet.md` là ghi chú dashboard/E2E; không gán chúng thành nhận xét nghiệm thu chính thức.

Chỉ đạo bổ sung của người dùng: **A3 ảnh cá nhân sẽ được thêm sau**; giữ nguyên placeholder, `DEFERRED_BY_USER`, không tìm/chèn ảnh tiếp và không chặn các phase hiện tại.

Đường dẫn hướng dẫn lịch sử `report/ra-soat-va-bo-sung.md` hiện không tồn tại; đã dùng `report/README.md`, `report/RULES.md` và `report/audit/layout-2026-11-07.*` thay cho phần kiểm hình thức. Không tạo lại hay suy đoán nội dung tệp cũ.

Nguồn thuyết minh chỉnh sửa được: `resource/Thuyết minh NCKH -THS2026-68.docx`; có PDF cùng tên, `report/thuyet-minh.pdf` và bản deliverable. Đã đọc XML paragraph của DOCX. Các phần chính là **12** mục tiêu, **13** đối tượng/phạm vi, **14** cách tiếp cận/phương pháp, **15** nội dung/tiến độ và **16** sản phẩm. DOCX có cam kết mô hình ảnh + văn bản, MobileNetV3 + DistilBERT, quantization, dữ liệu tiếng Việt và thử điện thoại/mạng yếu. Không dùng số mục 15/16.2 của tài liệu đối chiếu cũ nếu không khớp bản DOCX hiện tại.

Trạng thái được ghi riêng: **Implemented** = có cài đặt; **Executed** = có dấu vết chạy; **Evaluated** = có đánh giá trong một phạm vi xác định; **Reported** = có trong báo cáo; **Missing** = chưa thấy bằng chứng trong phạm vi đã tìm; **Unverified** = tài liệu nói có nhưng chưa kiểm tra đủ. Một thành phần có thể mang nhiều trạng thái. Evaluated trên mô phỏng/nhãn thay thế không có nghĩa được xác nhận thực địa.

## 2. Bản đồ repository

| Vùng | Vai trò và nguồn có thể chỉnh sửa |
|---|---|
| `report/main.tex`, `report/chapters/`, `frontmatter/`, `template/`, `config/` | Nguồn LaTeX báo cáo; main PDF 165 trang. Thứ tự chương do main.tex: cơ sở → hệ thống → phương pháp → đánh giá. Tên thư mục 02/03 không phải thứ tự hiển thị |
| `report/scripts/`, `report/generated/` | Xuất bảng/hình, provenance và kiểm báo cáo. Không sửa tay tệp generated |
| `report/RULES.md`, `report/audit/layout-2026-11-07.*` | Quy ước và audit hình thức mới; phải bảo toàn sửa đổi hiện có |
| `resource/`, `report/guideline/`, `report/evidence/` | Thuyết minh, mẫu hành chính, hồ sơ; nhiều mục chỉ là bản nháp/thông tin tham chiếu |
| `products/fe/app/` | Flutter; controller → use case → payload → repository/outbox; ONNX và ExecuTorch Android; code legacy không phải mọi đường chạy chính |
| `products/fe/model/`, `products/fe/tools/` | Notebook ảnh, split, checkpoint/export, QAT/PTQ/pruning và gói LR v5 |
| `products/fe/reports/seed{42,159,1024}/` | Kết quả model/CPU/mobile đã lưu; luôn giữ seed/runtime/split riêng |
| `products/be/` | FastAPI, SQLite, adapter cluster, `rescue_core`, dashboard trong templates/static; phân cụm chạy server |
| `products/fe/experiment_mobile/`, `thuc_nghiem_nq/` | Runner mobile/web/proxy, hướng dẫn và một số kết quả; mức lưu raw không đồng đều |
| `thucnghiem/data/`, `thucnghiem/results/` | Dữ liệu mô phỏng, RQ1–RQ3, notebook, CSV, manifest, checkpoints |
| `paper/`, `docs/camera-ready/`, `docs/checkpoints/` | Nguồn bài báo và lịch sử chuẩn bị; các bản ngắn/Việt/Anh không mặc nhiên cùng protocol |
| `docs/nghiem-thu/`, `CLAUDE.md` | Có mô tả lịch sử đã cũ: 1.621/1.625 ảnh, 224 px, thiếu INT8/mobile/split. Chỉ dùng làm dấu vết, không làm authority hiện tại |
| `ISDS/`, `presentation/`, `reportTemplate/` | Deck/hướng dẫn và template độc lập; không sửa trong nhiệm vụ này |

Đã liệt kê **20 ref** local/remote-tracking có sẵn (gồm alias origin/HEAD), đọc tree và tìm NLP trong code/notebook của từng ref; không cập nhật remote nên không tuyên bố đã thấy mọi nhánh trên máy chủ. Các ref gồm app, clean, dev, feat/nghiem-thu, main, paper, trong-edit-pic, backup và các origin/dev_hung, dev_quynh, nnq, rhna. Không thấy `DistilBERT`, `PhoBERT`, `AutoTokenizer`, `AutoModelForSequenceClassification`, `UIT.VSMEC` hoặc `from transformers` trong `.py/.dart/.ipynb` ngoài skill. Đã kiểm tra lịch sử commit/path theo NLP/BERT/VSMEC và mobile/quantization. **12 notebook** hiện có được parse, phân biệt notebook có output và notebook chỉ có code. Generator/benchmark lịch sử có thể ở commit `a6be3e9…`/`6ac75c2…` với `demo/` hoặc `src/`; không kết luận mất mã chỉ vì main đổi sang `thucnghiem/`.

## 3. Danh mục bằng chứng dùng chung

| ID | Tệp/điểm kiểm tra | Điều đã xác minh và giới hạn |
|---|---|---|
| E01 | `resource/Thuyết minh NCKH -THS2026-68.docx`, mục 12–16; paragraph XML 159–204, 279–305 | Có mục tiêu văn bản tự do, nén và sản phẩm đa phương thức; đoạn hứa hẹn không chứng minh đã thực hiện |
| E02 | `products/fe/model/training_img.ipynb`; `products/fe/model/Edge Ai/split_train_val_test_mobilenetv3_large.csv`; `…/mobilenetv3_large_dataset_v4_seed1024/test_metrics_mobilenetv3_large.json` | Notebook có 73 output; split 1.702 ảnh = 1.189/257/256; seed 1024 test Accuracy 75,78125%, macro-F1 74,2649%. Hash/nhóm không vượt split; chưa xác nhận độc lập nguồn/sự kiện hoặc manifest chia mẫu riêng tại lần train seed 1024 |
| E03 | `products/fe/model/urgency_ei/{data,model,audits,sources,reports}/`; `scripts/train_urgency_logistic.py` | 32 profile Boolean, nhãn OR tự sinh có cơ sở tham chiếu, 31 dương/1 âm; không nhãn chuyên gia/bệnh nhân. Intercept −1,0580446217; năm hệ số bằng 1,1087792041; threshold 0,5; fidelity toàn bảng 1. LR không NLP, không tốt hơn OR theo định nghĩa nhãn |
| E04 | `products/fe/app/lib/presentation/controllers/app_controller.dart:677`; `lib/domain/services/urgency_logistic_model.dart`; `lib/data/models/rescue_record_payload.dart:27`; `products/be/cluster_service.py:130` | App tính và gửi `E_i`; adapter lấy `payload.urgency` nếu có, nếu không dùng `_urgency_from_text(description)`; `ReportV2.E=urgency`. Tìm backend không thấy đọc E_i. Báo cáo nói kết hợp E_i/urgency là **thiết kế chưa được mã hiện tại chứng minh**, không phải fusion LR đã hoạt động end-to-end |
| E05 | `products/fe/reports/seed1024/{pth_onnx_pte,fp32_ptq_qat,prunning_st}/summary.json`, `all_predictions.csv`; `report/generated/tables/{fp32_ptq_qat,pruning_st}.tex` | Có Executed/Evaluated/Reported cho tối ưu. FP32/PTQ/QAT Accuracy 75,78/66,80/46,48%; macro-F1 74,26/64,36/42,91%; lỗi nặng 3/17/45; 16,04/4,51/4,57 MiB; CPU median 14,81/13,97/53,11 ms. Có giảm byte, có suy giảm chất lượng; chưa có chẩn đoán nhân quả QAT |
| E06 | `products/fe/reports/seed{159,1024}/mobile/**/benchmark_*.json`; `report/generated/phone-benchmarks/summary.csv` | Đủ 32 JSON, mỗi JSON 256 prediction, complete, 0 failed; audit này tính lại Accuracy/F1, đối chiếu ID/nhãn test và hash summary. Bốn máy × hai seed × baseline/pruning × ONNX/PTE. Timing classifyImage gồm decode/preprocess/inference, khác predict CPU. Chưa kiểm soát lặp/nhiệt hoặc hash APK |
| E07 | `thuc_nghiem_nq/experiment_weak_network/results/20261005-102040/weak_network.{csv,md}`, checkpoint và log manifest | CSV 2.313 lượt; ba mode × ba profile ×257 ảnh validation. Proxy máy tính, ép mode, không phải toàn luồng điện thoại hoặc đánh giá policy tự động |
| E08 | `report/chapters/04-evaluation/sections/{setup,system-tests}.tex`; `thuc_nghiem_nq/experiment_e2e/RESULTS.md`; `products/fe/experiment_mobile/{README.md,coordinator.py}` | Reported Android S10e hai run, 9 case/run; raw run_001 vẫn 8 PASS/1 FAIL theo nội dung báo cáo và xác nhận bổ sung về giữ/gửi lại. **Raw JSON/CSV/log mobile và web được trỏ tới chưa thấy tại checkout**; không xác minh độc lập số case/PASS. Runner có code không chứng minh chạy xong |
| E09 | `thucnghiem/results/cij_baseline_benchmark_results/{benchmark_test_40runs,benchmark_summary,paired_comparisons}.csv`; `rq1_results/{manifest.json,aggregate/}`; replication `rq1_results_v2/full/` | RQ1 có output/test 40 run. Additive ARI .9191 > Product .9072; Product−Additive −.01184; Holm p=.2560. Stress copy5x Product ΔARI −.6108. Không khẳng định thắng baseline; không gộp replication |
| E10 | `thucnghiem/results/rq2_results/{rq2_summary,rq2_rank_alignment_test,rq2_paired_comparisons,rq2_parameter_sensitivity_test}.csv` | RQ2 trên oracle grouping, 40 seed; NDCG@5 revised .6669, random .6763, legacy .6548. Bất biến bản sao exact ở grouping cố định không phải chống mọi tin giả hoặc độ bền toàn pipeline |
| E11 | `thucnghiem/results/rq3_results/{rq3_dispatch_test_seed,rq3_paired_comparisons_seed}.csv`, `recompute_seed_level.py`, provenance | 40 cặp seed sau trung bình ba resource scenarios; không n=120 độc lập. Revised kém nearest-first: Δ cải thiện harm −69,88; deadline −17,71 đpt; Holm p≈.000041/.000001. Chưa chứng minh lợi ích chung so legacy |
| E12 | `report/audit/layout-2026-11-07.{md,json}`, `report/RULES.md`, `report/scripts/check_float_references.py`, PDF và log hiện có | PDF chính 165 trang. Chạy lại checker float read-only ở hai bản: 48 hình/37 bảng, exit 0. Audit lịch sử mô tả sửa trắng/float, hai bản render giống 165/165; lần này không render lại toàn bộ và không build |
| E13 | `report/frontmatter/research-body-{vi,en}.tex`, `report/audit/layout-2026-11-07.md`; `evidence/external-verification.md` | Báo cáo ghi published theo xác nhận người dùng ở phiên trước; chưa có chapter DOI/minh chứng xuất bản độc lập trong hồ sơ khảo sát. Trang Springer cấp quyển không đủ xác nhận trạng thái riêng bài; DOI Zenodo trong CITATION.cff là artifact phần mềm |
| E14 | `report/template/forms.tex:84` và `frontmatter/principal-investigator.tex`; PDF trang vật lý 20 | Còn placeholder Ảnh 4×6. Link Drive trỏ PNG `HT34.PNG` 2.464.340 B, chỉ metadata; chưa xem/đối chiếu ảnh chủ nhiệm. Không tự chèn hoặc tạo chân dung |
| E15 | `report/chapters/02-data-methods/sections/{data,methods,image-design,evaluation-design,scope}.tex`; `report/chapters/conclusion.tex` | Nhiều phần đã phân biệt mô phỏng/LR/kết quả âm; kết luận/tóm tắt vẫn có khẳng định mạnh hơn bằng chứng. D1/D2 chưa đầy đủ; D3 có DTN dự kiến nhưng thiếu người không có điện thoại |
| E16 | `products/be/rescue_core/{clustering,priority,dedup}.py`; `products/fe/app/lib/domain/services/adaptive_send_policy.dart`; `docs/contact_connect.md` | Tích hợp đặc trưng đo/heuristic trong công thức server; chưa thấy mạng học fusion hoặc embedding văn bản tự do. F ảnh và E khẩn cấp có ý nghĩa khác nhau, không thể ghép metrics hai model thành ablation |
| E17 | `products/fe/app/lib/data/repositories/rescue_repository_impl.dart`; Android `MainActivity.kt`; `products/be/sms_intake.py` | Có hàng đợi/SMS gateway code; lưu offline không đồng nghĩa truyền thành công; chưa có kiểm chứng tỷ lệ giao SMS thực tế. Thiếu GPS cần hàng xem xét, không tọa độ giả |
| E18 | `tmp.md` (196 dòng, 16.363 byte, chưa track khi bắt đầu); headings Nhận xét 06–20 | Bản tổng hợp nghiệm thu B/C/D có diễn giải, phù hợp yêu cầu đính kèm; không chứng minh phát biểu nguyên văn/video. B1–B5=06–10; C1–C7=11–17; D1–D3=18–20. Hash tệp ban đầu có trong snapshot; không sửa tệp này |

## 4. Kiểm tra trực tiếp trong lần audit này

`evidence/audit-snapshot.json` ghi chi tiết từng đường dẫn/hash, không chỉ trích lại README:

- **585/585 mục hash** khớp trong bốn manifest RQ1 primary/replication, RQ2, RQ3. Manifest khớp chứng minh tính toàn vẹn byte theo manifest hiện có; không xác nhận thiết kế thống kê hay nguồn dữ liệu ngoài.
- **26/26 nguồn** trong `report/generated/provenance.json` khớp SHA-256 hiện tại. 12 prediction audit đã lưu đều consistent; kiểm này chưa chạy lại exporter (vì nó ghi generated).
- **1.702/1.702 ảnh** tồn tại và MD5 khớp split; không nhóm MD5/perceptual/split vượt tập. Đọc header bằng Pillow có sẵn, không chỉnh/resize ảnh: JPEG 1.521, PNG 24, WEBP 152, AVIF 5; RGB 1.687, RGBA 14, L 1. Width min/median/max 168/512/5.472 px; height 100/384/3.648 px; bytes 2.481/41.564/2.900.796. Đây là thống kê audit mới, **chưa phải thí nghiệm nhận diện** hoặc dữ liệu đã đưa vào báo cáo. Cần bảng chéo split/lớp và phân vị trong phase 02.
- **32/32 JSON mobile** có 256 prediction; ID theo SHA1(relative_path)[:12] và nhãn khớp test; Accuracy/macro-F1 tính lại khớp JSON; hash tệp raw khớp summary.csv. Không coi 8.192 prediction lặp trên 256 ảnh là 8.192 mẫu độc lập.
- Hai checker float read-only đều đạt 48 hình/37 bảng. PDF chính trùng hash content PDF; PDF 165 trang và placeholder ảnh được kiểm từ text. Không tuyên bố một lượt build/kiểm tổng thể mới.
- Full verifier `thucnghiem/results/verify_camera_ready_evidence.py` còn hardcode `ROOT/src/results`, trong khi cây hiện tại là `thucnghiem/results`; đòi NumPy 2.5.1/matplotlib 3.11.0, visual-env hiện là 2.5.3/3.10.8. **Chưa chạy/replay verifier**; phase 03 xử lý adapter đường dẫn/môi trường trong công cụ riêng trước khi tái tính. Không sửa script gốc trong audit.

## 5. Phân biệt trạng thái theo thành phần

| Thành phần | Implemented | Executed | Evaluated | Reported | Missing/Unverified |
|---|---|---|---|---|---|
| MobileNetV3 + export | Có | Notebook, checkpoint, prediction | Test 256; giới hạn split/selection | Có | Độc lập event/source và xác nhận sau chọn model |
| PTQ/QAT/pruning | Có | Summary/predictions | Có, giữ kết quả xấu | Có | QAT causal diagnosis; quantized Android nếu muốn claim |
| LR v5 | Có | JSON/model/audit | Fidelity OR/sanity trong 32 trạng thái | Có | Chuyên gia/clinical/field, không NLP |
| LR vào điểm server | App gửi E_i | Có code đường gửi, không có E2E receipt | Chưa xác minh | Báo cáo mô tả kết hợp | Adapter không đọc E_i; cần sửa mô tả trước |
| NLP tự do/fusion học | Không tìm thấy trong phạm vi tìm | Không thấy | Không thấy | Là cam kết/định hướng, LR không thay thế bằng chứng NLP | Missing evidence; nguồn ngoài repo Unverified |
| RQ1–RQ3 | Có notebooks/core | Có outputs/CSV/checkpoint | Có trên mô phỏng | Có, Discussion khá chi tiết | Không ngoại suy cứu hộ thực địa; chưa replay kiểm thống kê lần này |
| Mobile image benchmark | Có | 32 raw runs | Đã đối chiếu metric | Có | Repeated timing, APK hash, uncontrolled thermal |
| Android/web E2E | Có runners | Được tài liệu ghi nhận | Unverified raw tại checkout | Có | Khôi phục raw/log, giữ lỗi Case 8 |
| Proxy mạng yếu | Có | 2.313 raw rows | Có trong cấu hình proxy | Có | Không viễn thông thật, không end-to-end adaptive policy |
| Robustness chất lượng ảnh | Chưa thấy protocol/result riêng | Không tìm thấy | Missing | Giới hạn/future | Chất lượng ảnh input khác lỗi nén truyền tải |

## 6. Kết quả có thể dùng ngay, khoảng trống và ưu tiên

Không cần train lại để giải thích LR/OR, mô tả integration, lập bảng compression, phân tích ba RQ hoặc thêm D1–D3. Có thể tạo bảng lỗi/chất lượng/CI từ prediction hiện có. Các CSV phụ mà README phone nhắc (`predictions.csv`, `coverage.csv`, `model_comparison.md`, `onnx_pte_comparison.md`…) **không có trong checkout**; chỉ `README.md`, `summary.csv`, `selection_steps.csv` đang hiện diện ở thư mục đó. Raw phone đầy đủ nên tái xuất được, không phải mất thực nghiệm.

C7: đã đọc căn cứ tham chiếu dấu hiệu trong gói LR và phạm vi WHO IITT; chưa khảo sát đầy đủ quy định/nghiệp vụ cứu hộ Việt Nam. Phase02 cần tra nguồn chính thức khi viện dẫn, ghi điều khoản/phạm vi áp dụng hoặc xác nhận chưa thấy căn cứ cho trọng số. Không suy rằng luật/hướng dẫn quy định chính xác ω/μ/s của đề tài.

Required trước khi chốt: giải trình khác thuyết minh/NLP, sửa claim E_i, kiểm trạng thái công bố, thống kê nguồn/đơn vị và giữ kết quả âm. Thực nghiệm mới chỉ Required nếu muốn giữ claim bị thiếu: C5 về độ bền ảnh trên thiết bị; C6 về phiên E2E/APK hoặc hiệu năng lặp khi raw không khôi phục được. Các kết luận có thể thu hẹp minh bạch nếu không đủ tài nguyên. B5 hiện **no-go ablation image/text**: thiếu cùng nhiệm vụ, paired inputs và gold độc lập. Nghiên cứu NLP/fusion hoàn chỉnh là mở rộng riêng, không tự thêm để làm báo cáo giống thuyết minh.
