# Prompt Phase 04 — Đánh giá ảnh đầu vào chất lượng kém

Bạn làm việc tại `/home/ngthtrong/nckh2` cho đề tài **Xây dựng hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI (THS2026-68)**. Thực hiện X02 để xử lý C5, hỗ trợ C2/C6, chỉ suy luận model cố định. Không train hoặc thay checkpoint để tăng kết quả.

## A. Bối cảnh

Đã có MobileNetV3 test và 32 phiên nhận diện trên bốn mẫu Android, nhưng chưa thấy thí nghiệm kiểm soát blur/downsample/nén/tối. Phép so sánh ảnh truyền trong E2E không đánh giá nhận diện. Cần định lượng robustness với target/nhãn/metric cố định. **A3 ảnh cá nhân sẽ thêm sau** theo người dùng; giữ nguyên placeholder, không tìm/chèn/hỏi ảnh.

## B. Đầu vào và sự thật cần kiểm lại

Đọc report README/RULES, `docs/revision-plan/{00-repository-audit.md,02-experiment-gap-analysis.md,04-phase-roadmap.md}`; `outputs/phase-02/{data-card.md,image-profile.csv,measurement-scopes.csv,handoff.md}`. Các output02 là artifact dự kiến; thiếu thì làm preflight tương ứng từ raw và ghi chưa đủ, không tự nhận đã hoàn thành P02.

Raw: `products/fe/model/Edge Ai/split_train_val_test_mobilenetv3_large.csv` (test256); `products/fe/model/Dataset_Flood`; model/export configs trong `Edge Ai/` và app assets; `products/fe/reports/seed1024/mobile/`; `products/be/build_benchmark_package.py`; `products/fe/app/lib/domain/services/model_benchmark.dart` (dùng rg tìm nếu path đổi); `products/fe/tools/verify_pipeline.py`, compare_models.py. Model ưu tiên là seed1024 pruning/PTE theo ứng dụng hiện tại, **phải xác nhận hash thực tế**, không lấy tên folder làm bằng chứng. 32 phiên cũ đo classifyImage gồm decode/preprocess/inference, không dùng predict CPU làm clean baseline cho Android.

## C. Mục tiêu, phụ thuộc và gate

Tạo experiment paired clean/degraded trên cùng test IDs, báo cả suy giảm và thất bại decode. Cần exact asset, class map, preprocessing và runner. On-device kết luận cần thiết bị thật. Nếu thiếu model/device, tạo protocol/harness sẵn sàng và NOT_RUN/CPU_ONLY trung thực; C5 vẫn PARTIAL/OPEN, không đánh dấu giải quyết đầy đủ. Không tự train hoặc lấy model khác thay thế.

## D. Tác vụ

1. **P04.01:** ghi status/model/checkpoint/runtime/split/asset hashes và environment; kiểm class order `[low,medium,high,non_flood]`, EXIF→RGB→letterbox256/ImageNet. Kiểm ID theo package SHA1 relative_path[:12], đủ256. Chạy smoke code trên validation, không tune degradation theo test. Tạo preflight và protocol.json trước full inference.
2. **P04.02:** tạo dẫn xuất trong thư mục experiment mới, không ghi đè ảnh gốc. Khóa độc lập tám điều kiện: JPEG q50/q20, cạnh ngắn128/64 giữ aspect, blurσ1/2, exposure×0,7/0,4; clean cùng pipeline. Ghi manifest gồm parent ID/hash, công thức/version/seed/variant hash. Ảnh mất ngữ nghĩa/không decode ghi failure/uncertainty, không âm thầm bỏ khỏi n.
3. **P04.03:** CPU screening tối đa clean+8 variants×256=2.304 inference/model; kiểm clean agreement với artifact đúng runtime. Android nếu có: clean+4 mức nặng×256=1.280/phiên, tối đa 3 phiên ghi nhiệt/pin/charger/warmup/thứ tự có kiểm soát và nghỉ. Dùng model/runner thật, không mock prediction hoặc suy CPU latency thành mobile. Không chỉnh default production inference để phục vụ benchmark.
4. **P04.04:** tính Accuracy/macro-F1/recall-high, lỗi lệch≥2 mức theo ordinal `non_flood=0,low=1,medium=2,high=3`, confidence/abstention và mean/P50/P95. Bootstrap cặp theo ảnh gốc hoặc split_group, tính lại macro-F1 từng resample; nếu kiểm giả thuyết dùng Holm cho contrasts định trước. Không n=variants×ảnh hoặc n=thiết bị×256 độc lập. Tách quality và timing, ghi domain gap synthetic corruption/ảnh camera.
5. **P04.05:** lưu predictions/metrics/raw device logs/source hashes và analysis; thêm phương pháp/kết quả trong subsection riêng hoặc bàn giao P07, không viết lại toàn chương. Chạy coverage/hash/metric checks, build/check/inspect phần LaTeX nếu đổi. Tạo handoff.md với GO/CPU_ONLY/NOT_RUN và ảnh hưởng trạng thái C5.

## E. Nguyên tắc và rủi ro

Giữ model/test split/các artifact trước nguyên byte; không dùng test để chọn mức hoặc model mới. Không claim blur là ảnh mưa thực địa hoặc corruption giữ nhãn đúng tuyệt đối. Không loại ảnh khó âm thầm. Không đổi thuật toán server; không reset DB; không commit/push hoặc gửi dữ liệu bên ngoài. Thiếu thiết bị là gap thực nghiệm, không ngăn tạo gói/protocol; không giả định có phép đo khi chưa thực hiện.

## F. Deliverables

`docs/revision-plan/outputs/phase-04/{protocol.json,preflight.md,variant-manifest.csv,predictions.csv,metrics.csv,analysis.md,environment.json,handoff.md}`; runner/gói riêng và raw logs nếu chạy; `NOT_RUN.md` nếu không chạy. Dữ liệu nặng để trong output riêng có manifest, không force-add vào Git.

## G. Acceptance criteria và chuyển phase

ID/hash/split/clean baseline xác minh; số mẫu/condition/failure rõ; metric paired và scope CPU/Android đúng; nhãn uncertainty/thiếu device công khai. Chỉ gắn trạng thái measured khi raw thực tồn tại. P07 nhận output hoặc disposition có lý do; không tự thực hiện P05/P07.

## H. Final report

Báo việc hoàn thành, file/script, inference/test thực chạy và tài nguyên, C5 xử lý tới mức nào, những gì chưa đo, quyết định protocol/labels/statistics và handoff. Không báo model robust khi dữ liệu chưa chứng minh.
