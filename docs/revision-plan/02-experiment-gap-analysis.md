# Khoảng trống bằng chứng và thực nghiệm đề xuất

**Không thực nghiệm nào trong tài liệu này đã được chạy trong lần lập kế hoạch.** Số liệu audit header/hash là thao tác kiểm tra, không phải kết quả nhận diện mới. Phân loại `Required` dưới đây là mức cần thiết cho một kết luận cụ thể; không phải lệnh triển khai mọi thí nghiệm. Chỉ thực thi bằng prompt phase riêng ở phiên sau. A3 được người dùng hoãn, không phải đầu vào thí nghiệm.

## Quyết định tổng quát

| Mã | Công việc | Mức cần thiết | Chi phí tương đối | Quyết định hiện tại |
|---|---|---|---|---|
| X01 | Kiểm thống kê RQ1–RQ3 trên artifact | Required để chốt kết luận | Thấp–vừa, CPU | Tái phân tích; không train/generate/re-run full benchmark |
| X02 | Chất lượng ảnh đầu vào và suy luận Android | Required nếu muốn trả lời đầy đủ C5 bằng định lượng | Vừa, inference + một điện thoại | Có gap thật; preflight model/split/runtime trước; không có device thì kết quả CPU và C5 vẫn PARTIAL |
| X03 | Khôi phục raw E2E/mobile và lặp phần đo còn thiếu | Required cho claim E2E/APK chưa xác minh; Recommended cho repeated latency | Thấp nếu khôi phục, vừa nếu đo | Khôi phục trước; không lặp đủ 32 tổ hợp theo mặc định |
| X04 | Ablation nguồn thông tin cùng nhiệm vụ | Optional, có điều kiện | Cao nếu tạo paired gold mới | Hiện NO-GO cho image/text/both; có thể sensitivity trên input mô phỏng với tên khác |
| X05 | Chẩn đoán suy giảm QAT/PTQ | Recommended phần phân tích prediction; Optional layer-debug | Thấp cho raw, vừa cho tensor debug | Giải thích trade-off được ngay; không cần train lại |
| X06 | Xác nhận chuyên gia/ảnh thực địa độc lập | Optional cho nghiệm thu hiện tại; cần cho claim giá trị thực địa mới | Cao, dữ liệu/nhãn mới | Đưa hạn chế/Future Work; chưa tổ chức người tham gia hoặc thu dữ liệu |

## X01 — Tái kiểm chứng thống kê và kết luận RQ1–RQ3

| Trường | Protocol đề xuất |
|---|---|
| 1. Tên/mục tiêu | Kiểm tính nhất quán, tái tạo các phép so sánh đã đăng ký và lập claim ledger cho ba RQ |
| 2. Nhận xét | C4; hỗ trợ B3, C7 |
| 3. Vì sao hiện có chưa đủ | Bảng đã có nhưng kết luận tổng thể chưa phản ánh hết kết quả âm; verifier hardcode src/results và version khác local; chưa replay trong audit |
| 4. RQ/giả thuyết | RQ1 Product có hơn Additive/khớp density và chịu stress? RQ2 bounded score có phù hợp benefit và giữ bất biến hẹp? RQ3 dùng score có giảm harm/deadline? Giữ hypothesis gốc, không chọn mới theo p-value |
| 5. Dataset | RQ1 40 test run Generator 3.0; RQ2/3 40 test seed Candidate 4.1; không gộp hai generator hoặc stress replication |
| 6. Model/thuật toán | Product/Additive Louvain, Product Leiden, baselines; revised/legacy score; fixed scheduler/partitions |
| 7. Baseline | Additive độc lập và matched-density, geo-time DBSCAN theo protocol; random/count/urgency/linear/legacy RQ2; nearest-first/legacy và partition baselines RQ3 |
| 8. Biến/kiểm soát | So sánh theo cặp cùng run/seed; phân tầng stress/resource; giữ selected configs/split/generator; không tune test |
| 9. Metric/thống kê | ARI, fake-destination diagnostics, NDCG@5/rank drift/lift, harm/deadline. Reproduce paired deltas, direction, bootstrap và Wilcoxon/Holm với đúng family. RQ3 n=40 sau averaging 3 resource scenarios; CI bootstrap chưa hiệu chỉnh không thay thế Holm p |
| 10. Quy trình | Kiểm hash → lập adapter chỉ đọc cho cây hiện tại → môi trường đúng pin nếu cần → tái tính từ CSV/predictions/checkpoint → đối chiếu tolerance → thống kê mô tả điều kiện xấu → ghi discrepancy/claim decisions |
| 11. Tái sử dụng | `thucnghiem/results/verify_camera_ready_evidence.py`, `rq3_results/recompute_seed_level.py`, CSV paired/aggregate; notebook executed chỉ đọc. Verifier/recompute gốc có đường dẫn cũ: không chạy mù hoặc sửa manifest |
| 12. Tài nguyên | CPU, pandas/NumPy/SciPy đúng phiên bản; không GPU; ưu tiên môi trường có sẵn/isolated; không cài đè env dùng chung |
| 13. Lưu/kiểm chứng | `outputs/phase-03/{protocol.json,source-hashes.json,rq-claims.csv,statistics.csv,analysis.md,validation.txt}`; command/version/seed; round-trip số bảng; lưu output mới tách artifact gốc |
| 14. Báo cáo | `chapters/04-evaluation/sections/results.tex`, `limitations.tex`; conclusion/tóm tắt tích hợp P07 |
| 15. Cần thiết/chi phí | Required; thấp–vừa. Bảng mô tả từ CSV đủ cho nhiều ý; replay chỉ phần đang thiếu kiểm chứng |
| 16. Go/no-go | GO nếu hash/schema/paired units/config xác minh; nếu thiếu pin hoặc raw thì ghi NOT_REPLAYED và dùng kết quả đã lưu với giới hạn. Không chạy lại model để ép mọi so sánh có ý nghĩa |

## X02 — Độ nhạy ảnh đầu vào trên model cố định

| Trường | Protocol đề xuất |
|---|---|
| 1. Tên/mục tiêu | Quantify ảnh nén/nhỏ/mờ/tối ảnh hưởng nhận diện và latency; phân biệt image classification với chất lượng upload |
| 2. Nhận xét | C5, C2, C6; hỗ trợ B2 |
| 3. Vì sao thiếu | Có ảnh nhiều độ phân giải nhưng chưa có corruptions có kiểm soát; phép sai khác ảnh gửi E2E không đo Accuracy/F1 |
| 4. RQ/giả thuyết | Với một artifact cố định, Δmacro-F1/recall-high/lỗi lệch ≥2 mức thay đổi thế nào so clean khi chất lượng giảm? Không giả định mô hình bền |
| 5. Dataset | 256 ảnh test hiện có với ID/hash; mỗi biến thể dẫn xuất từ đúng ảnh đó. Không dùng biến thể test để train/calibrate/tune. Gold giữ nhãn gốc là surrogate; ảnh mất hết dấu hiệu cần đánh dấu không thể đánh giá rõ nghĩa |
| 6. Model | Một checkpoint/runtime đã xác minh, ưu tiên seed1024 pruning/PTE đang dùng; ONNX cùng hash model family chỉ để CPU preflight, không trộn output hai runtime |
| 7. Baseline | Ảnh clean qua cùng decode/preprocess và cùng thiết bị/runtime; không so clean CPU với corrupted Android |
| 8. Biến/kiểm soát | Đề xuất khóa trước: JPEG q=50/20, cạnh ngắn 128/64 giữ aspect, blur σ=1/2, exposure ×0,7/0,4; từng tác động riêng. Giữ resize 256, class order, EXIF, seed, model, thread, mode nguồn điện. Tham số là đề xuất cần preflight validation, không chọn dựa trên test |
| 9. Metrics/thống kê | Accuracy, macro-F1, recall-high, lỗi nặng theo mapping non_flood=0/low=1/medium=2/high=3, abstention/confidence và latency mean/P50/P95. Bootstrap cặp theo split_group/ảnh gốc, tái tính macro-F1 trong resample; tám contrast định trước, nếu test giả thuyết thì Holm. Lặp thiết bị không làm tăng số ảnh độc lập |
| 10. Quy trình | (a) model/split/runtime checks; (b) smoke trên validation để bảo đảm code không sai, chốt protocol; (c) CPU clean +8 biến thể = tối đa 2.304 inference/model; (d) Android clean +4 mức nặng =1.280 inference/phiên, tối đa 3 phiên có nghỉ/ghi thermal; (e) paired analysis. Có thể giảm phiên khi chỉ kết luận chất lượng, phải nêu latency chưa lặp đủ |
| 11. Tái sử dụng | `products/fe/tools/verify_pipeline.py`, `compare_models.py`; `products/be/build_benchmark_package.py`; Flutter `model_benchmark.dart` (tìm đúng path bằng rg), exporter phone; bổ sung runner/gói riêng, không ghi đè test package hoặc model hiện tại |
| 12. Tài nguyên | CPU cho screening, một Android hỗ trợ PTE/ONNX; storage ảnh dẫn xuất trong thư mục mới; không GPU/train. Nếu artifact exact hash không có local, tìm bản export đã lưu trước; không tự train để thay thế |
| 13. Lưu/kiểm chứng | `outputs/phase-04/{protocol.json,variant-manifest.csv,predictions.csv,metrics.csv,analysis.md,environment.json}` và log device/APK/model hash; dataset derivation hash, sample IDs, condition/level, failure count; preserve parent clean predictions |
| 14. Báo cáo | data/image-design bổ sung phương pháp; results mục image-quality riêng; limitations về synthetic corruption/domain gap |
| 15. Cần thiết/chi phí | Required để đóng C5 bằng số mới; vừa. Nếu chỉ thừa nhận chưa đánh giá thì có thể không chạy nhưng C5 giữ PARTIAL/OPEN |
| 16. Go/no-go | GO khi có exact model, label map, nhãn/ID, khả năng decode và runner thực; gate Android fail → CPU-only với nhãn rõ. Không dùng placeholder dự đoán hay tăng test để chọn model tốt nhất; kết quả xấu vẫn giữ |

## X03 — Khôi phục hồ sơ và benchmark Android có mục tiêu

| Trường | Protocol đề xuất |
|---|---|
| 1. Tên/mục tiêu | Làm đủ provenance E2E, tách các scope timing và lặp phần còn thiếu, không nhân bản toàn bộ campaign |
| 2. Nhận xét | C6; B2; C3 nếu có kiểm tra truyền E_i |
| 3. Vì sao thiếu | 32 raw image runs có thật, nhưng thiếu APK/thermal/lặp. E2E Android/web chỉ thấy report/tài liệu, raw/log còn thiếu; Case 8 có sự cố cần giữ |
| 4. RQ/giả thuyết | Luồng app hiện tại có giữ/gửi đúng một lần khi nối lại? Runtime exact artifact nào chạy? Kết quả latency ổn định giữa phiên trong phạm vi máy được thử? Không suy ra hiệu quả điều phối |
| 5. Dataset | Giữ 256 test ảnh cho timing nếu cần; fixtures validation run_001/run_002 cho chức năng, không diễn giải hai ảnh thành accuracy model; dùng DB/volume thử riêng |
| 6. Model/thuật toán | App hiện tại với PTE seed1024 pruning nếu hash đúng; adaptive policy/outbox thật; server giữ vai trò phân cụm |
| 7. Baseline | Hồ sơ phone cũ là historical comparator; paired ONNX/PTE nếu thực sự cần cùng session; online làm đối chứng offline/reconnect trong app |
| 8. Biến/kiểm soát | Device/Android/APK/model/package/split/hash/runtime, warmup, thermal/battery, charger, threads; profile 300/20 kbit/s và 503 là proxy, không gọi mạng cell thực; không reset DB người dùng |
| 9. Metrics/thống kê | Functional PASS/FAIL/NOT_RUN theo case và crash/session logs; delivery count/outbox/order; latency theo phiên, CI mô tả với rất ít máy; không coi 256 lần đo trên cùng máy là n=256 thiết bị |
| 10. Quy trình | Tìm raw theo paths/ID ở máy chạy/backup đã có quyền → kiểm manifest → nếu đủ, chỉ tổng hợp → nếu không, protocol tối thiểu một máy/two fixtures hoặc repeated latency model được chọn; ghi mới run ID, APK hash; đối chiếu app→payload E_i→ReportV2.E như diagnostic, không âm thầm đổi code |
| 11. Tái sử dụng | `products/fe/experiment_mobile/{coordinator.py,manual_errors.py,mobile_api.py}`, `thuc_nghiem_nq/experiment_mobile_e2e/coordinator.py`, `experiment_e2e/e2e_system.py`; kiểm phiên bản trước dùng vì kế hoạch cũ có path không còn đúng |
| 12. Tài nguyên | Một Android + PC/LAN; backend/DB test riêng; không cần chuyển graph/server sang phone; không bắt buộc SMS thật hoặc trả phí |
| 13. Lưu/kiểm chứng | `outputs/phase-05/evidence-recovery.md`; `runs/<new-id>/{manifest.json,checks.csv,summary.json,logcat.txt,backend-observations.json}`; không sửa JSON run_001 từ FAIL thành PASS |
| 14. Báo cáo | setup/system-tests/limitations, phone section; chỉ đổi bảng nếu nguồn mới so sánh hợp lệ và historical rows giữ riêng |
| 15. Cần thiết/chi phí | Required có điều kiện cho claim chưa có raw; Recommended repeated timing; thấp nếu khôi phục, vừa nếu chạy. Không device → chuẩn bị gói/handoff và ghi NOT_RUN |
| 16. Go/no-go | Đủ raw cũ → SKIP_RERUN. Không raw và không muốn giữ claim mạnh → thu hẹp kết luận. Chỉ GO chạy khi có thiết bị, isolated DB, exact hashes; không coi thời gian chờ là chấp thuận hoặc lần chạy thành công |

## X04 — Ablation nguồn thông tin

| Trường | Protocol đề xuất |
|---|---|
| 1. Tên/mục tiêu | Đánh giá liệu thêm nguồn thông tin cải thiện **cùng** nhiệm vụ |
| 2. Nhận xét | B3/B4/B5 |
| 3. Vì sao thiếu | Image model dự đoán mức ngập, LR dự đoán nhãn OR có cấu trúc; không paired ảnh–text có gold chung |
| 4. RQ/giả thuyết | Chỉ sau gate: image-only/text-only/both có khác nhau trên một target độc lập? Nếu dùng F/E simulated thì RQ đổi thành sensitivity nguồn thông tin, không ablation mô hình đa phương thức |
| 5. Dataset | Cần paired report-level input và nhãn do người gán theo guideline độc lập với công thức fusion; group split theo nguồn/sự kiện. Chưa có dataset này tại checkout; KeralaRescue dossier hiện chỉ intake, không mặc định có request/gold |
| 6. Model | Chỉ model từng nguồn thực có và hàm fusion định nghĩa trước; không tự viết/train text model trong phase feasibility |
| 7. Baseline | Cùng test IDs, same target/metric/label availability; majority/rule và từng modality; missing-modality policy rõ |
| 8. Biến/kiểm soát | Mask modality, giữ architecture/hyperparameters/split/budget tương đương; không leakage từ gold dùng dựng nhãn |
| 9. Metrics/thống kê | Chọn theo target trước: macro-F1/recall hoặc ARI/NDCG nếu đúng task; paired/grouped bootstrap, Holm; cost/availability; không so trực tiếp Accuracy ảnh với fidelity LR |
| 10. Quy trình | Eligibility checklist → data/licensing/annotation feasibility → protocol/cost → no-go hoặc proposal riêng. Chỉ execution nếu có dữ liệu/nhãn hợp lệ và người dùng thực sự yêu cầu phần mở rộng |
| 11. Tái sử dụng | RQ notebooks/core và dataset dossiers để tham khảo; code ảnh/LR chỉ dùng nếu target chung có nghĩa |
| 12. Tài nguyên | Feasibility CPU/read-only; nghiên cứu thật có thể cần annotation, GPU và thiết bị — chưa ước thời gian chính xác khi data chưa có |
| 13. Lưu/kiểm chứng | `outputs/phase-06/{feasibility.md,eligibility.csv,no-go.md}` hoặc protocol+dataset manifest+label provenance dự kiến; không tạo bảng điểm nếu không chạy |
| 14. Báo cáo | scope/architecture/limitations, Future Work; chỉ kết quả mới sau authorization mở rộng |
| 15. Cần thiết/chi phí | Optional, cao; không thiết yếu nếu giải trình đúng phạm vi nghiên cứu hiện tại |
| 16. Go/no-go | Hiện NO-GO: thiếu paired data/common independent target. Nếu chỉ simulated F/E, ghi tên/phạm vi đúng, không thay thế NLP/multimodal registered outcome |

## X05 — Phân tích lỗi tối ưu hóa, không huấn luyện lại

| Trường | Protocol đề xuất |
|---|---|
| 1. Tên/mục tiêu | Tìm nhóm lỗi và nguồn bất tương đương FP32/PTQ/QAT/pruning |
| 2. Nhận xét | B2/C5; hỗ trợ C2 |
| 3. Vì sao thiếu | Có kết quả suy giảm rõ; chưa có cô lập nguyên nhân QAT. Không cần biết nguyên nhân chính xác để báo cáo rằng nhánh chưa được chọn |
| 4. RQ/giả thuyết | Lỗi có tập trung ở class/low confidence, preprocessing, tie hoặc export? Các cơ chế chỉ là giả thuyết cho tới kiểm tra |
| 5. Dataset | all_predictions.csv test256 đã lưu; calibration/val chỉ để debug nếu phải chạy tensor; không tune test |
| 6. Model | Exact FP32/PTQ/QAT artifact cùng seed/split; các nhánh seed42 lịch sử tách khỏi 1024 |
| 7. Baseline | FP32 trong cùng phiên/model family; không dùng FP32 từ CPU runtime khác làm chứng cứ tốc độ |
| 8. Biến/kiểm soát | Loại model/format, giữ IDs/class order/preprocess; debug export giữ validation fixtures cố định |
| 9. Metrics/thống kê | Confusion/lỗi nặng, agreement, per-class recall, ECE nếu có probabilities, paired differences; test và CI theo ảnh, không tuyên bố causal từ correlation |
| 10. Quy trình | Recompute confusion/metrics → đối chiếu summary → error taxonomy → inspect config/QAT best_epoch/quantization schema → chỉ nếu cần, tensor comparison nhỏ trên validation, không QAT finetune |
| 11. Tái sử dụng | `products/fe/tools/{compare_fp32_ptq_qat.py,quantize_model.py,qat_finetune.py}` chỉ đọc cấu hình; không gọi entrypoint train/quantize; output mới trong P02 |
| 12. Tài nguyên | CPU cho CSV; tùy chọn inference nhỏ khi model có; không GPU/train |
| 13. Lưu/kiểm chứng | `outputs/phase-02/{compression-audit.csv,error-taxonomy.md}`; nếu debug mới thêm raw/log/command/hash riêng |
| 14. Báo cáo | image-design và results optimization; giữ kết quả âm và giới hạn |
| 15. Cần thiết/chi phí | Recommended phân tích raw (thấp), Optional layer-debug (vừa) |
| 16. Go/no-go | CSV đủ giải trình trade-off → không debug sâu; thiếu tensor/runtime exact → ghi nguyên nhân Unverified, không viết phỏng đoán thành kết luận |

## X06 — Xác nhận ngoài mẫu/chuyên gia (Future Work)

| Trường | Protocol đề xuất |
|---|---|
| 1. Tên/mục tiêu | Đánh giá giá trị ngoại tại của ảnh/ưu tiên trong bối cảnh cứu hộ có nhãn độc lập |
| 2. Nhận xét | C1/C3/C5/C7, B5 nếu phát triển thêm |
| 3. Vì sao thiếu | Nhãn OR và generator không phải outcome thực địa; ảnh web không đại diện camera; heuristic chưa xác nhận chuyên môn |
| 4. RQ/giả thuyết | Điểm/nhãn có khớp đánh giá chuyên gia và dữ liệu ngoài sự kiện huấn luyện? Chưa đặt giả thuyết phương pháp thắng |
| 5. Dataset | Ảnh hiện trường có quyền dùng và report được khử nhận dạng, guideline gán nhãn chuyên môn; cần xác định quy trình pháp lý/đạo đức phù hợp trước thu thập |
| 6. Model | Freeze model/score hiện tại trước đánh giá; không chuyển model mới vào cùng kết quả lịch sử |
| 7. Baseline | Expert consensus/rule minh bạch, nearest-first/operational policy phù hợp target; không tự đồng nhất triage bệnh viện với dispatch |
| 8. Biến/kiểm soát | Group split theo disaster/site/time, blinded independent annotation, giữ uncertainty/missingness |
| 9. Metrics/thống kê | IAA (kappa hoặc alpha tùy thiết kế), macro-F1/recall và ranking agreement; CI theo incident/site; dispatch outcome chỉ nếu có ground truth và causal design thích hợp |
| 10. Quy trình | Thiết kế hợp tác/nguồn quyền dùng → protocol/annotation pilot → adjudication → predefine endpoint/split → đánh giá riêng; chưa tuyển người/liên hệ cơ quan trong kế hoạch này |
| 11. Tái sử dụng | Data card, source-map LR, dataset-search dossiers, exporter; không mặc định có quyền lấy tin nhắn Zalo/Facebook |
| 12. Tài nguyên | Chuyên gia, thời gian gán nhãn/thu thập, thiết bị; chi phí chưa thể chốt khi nguồn chưa có |
| 13. Lưu/kiểm chứng | Proposal/provenance/license/annotation guide, blinded labels, agreement và split manifests riêng; chưa tạo kết quả |
| 14. Báo cáo | Hạn chế/Future Work hiện tại; nghiên cứu mới sau này |
| 15. Cần thiết/chi phí | Optional cho hoàn thiện hiện tại, cao; bắt buộc trước claim hiệu quả lâm sàng/thực địa mới |
| 16. Go/no-go | Chỉ GO khi có dữ liệu hợp pháp, nhãn đủ tin cậy và thỏa thuận người tham gia/chuyên gia phù hợp; không lấy dữ liệu giả gắn nhãn “thực” |

## Không nên làm để xử lý nhận xét hiện tại

- Không train DistilBERT trên nhãn cảm xúc UIT-VSMEC rồi gọi đó là cứu hộ/urgency nếu target không được chứng minh phù hợp.
- Không train lại QAT/ảnh chỉ để thay bảng có kết quả xấu; không ghép nhiều seed sau khi xem test mà không nói về selection.
- Không chạy lại Generator/RQ1–3 khi artifact đã đủ, không tăng n bằng copy/scenario/device repetition, không gộp primary và replication.
- Không chuyển thuật toán phân cụm server sang Android để có dòng “mobile benchmark”.
- Không làm image/text/both với hai đầu ra khác nhau hoặc nhãn được tính từ chính fusion đang đánh giá.
- Không xây IP/Wi-Fi/ASR/DTN ngay để đóng D1–D3; chúng được viết dưới Future Work, có giới hạn khả thi.
- Không chạy thử lên DB đang có dữ liệu người dùng; không gửi SMS/cuộc gọi tới người khác trong thử nghiệm không được yêu cầu.
