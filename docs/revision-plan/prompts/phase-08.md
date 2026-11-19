# Prompt Phase 08 — Kiểm chứng cuối và hồ sơ phản hồi có truy vết

Bạn làm việc tại `/home/ngthtrong/nckh2` cho đề tài **Xây dựng hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI (THS2026-68)**. Đánh giá bản báo cáo cuối và mức xử lý20 nhận xét A1–D3; không tạo thực nghiệm/model mới để làm check pass.

## A. Bối cảnh

Các phase trước sửa phạm vi, dữ liệu/LR/compression, tái phân tích RQ và có thể bổ sung image-quality/mobile evidence. Audit gốc chỉ là snapshot; không lấy mọi prompt là công việc đã hoàn thành. Negative results, synthetic-data limits và missing artifact phải còn hiện rõ. **A3 ảnh cá nhân được người dùng thêm sau**: DEFERRED_BY_USER, giữ ô ảnh, không tìm/chèn/hỏi, không lấy làm điều kiện chặn các phase hiện tại.

## B. Nguồn và đầu vào

Đọc report README/RULES, `docs/revision-plan/{README.md,00-repository-audit.md,01-review-matrix.md,02-experiment-gap-analysis.md,04-phase-roadmap.md,05-traceability-matrix.md}`; request/amendment/snapshot; `outputs/phase-01…phase-07/` và handoff/source hashes. Output phase trước là dự kiến nếu chưa có: liệt kê MISSING, không tự suy ra completed; kiểm source thực và xử lý độc lập phần đủ điều kiện.

Nguồn cuối: report/main.tex và nguồn LaTeX; main.pdf, build/content/content.pdf, content-twoside/content.pdf và bốn summary/bulletin Việt–Anh; generated/provenance và figure-provenance; input model/split/phone/RQ raw; publication-verification.md. Snapshot gốc có 1.702 ảnh,32 phone JSON,585 hash và E_i adapter mismatch; xác minh current state trước viện dẫn. Full verifier RQ đường dẫn/pin cũ cần harness của phase03, không chạy mù.

## C. Mục tiêu và phạm vi

Hồ sơ tự chứa cho người dùng: những gì đã sửa/đo/kiểm, số liệu tái lập thế nào, nhận xét còn thiếu và vì sao. Không phán đoán Hội đồng sẽ chấp thuận, không gọi technical build là validation cứu hộ. Có thể sửa lỗi tài liệu nhỏ trực tiếp thuộc kiểm chứng; thay đổi nội dung nghiên cứu lớn phải ghi phát hiện và quay lại phase phù hợp, không âm thầm đổi thuật toán/số liệu.

## D. Tác vụ

1. **P08.01:** ghi status/HEAD/dirty scope và source/PDF hashes. Đối chiếu mọi handoff với input/output hiện tại; stale hash làm receipt stale, không kế thừa PASS. Tạo `reproducibility.md` phân biệt dữ liệu thật/synthetic, model/code/executed/evaluated/reported, environment/commands/seed và artifact hiện có/missing.
2. **P08.02:** chạy check phù hợp trên final state: `make -C report check`; `python3 report/scripts/check_float_references.py --build-dir build/content` và content-twoside; `git diff --check`; build lại chỉ nếu cần hoặc receipt thiếu/stale. Kiểm LoF/LoT/labels/refs/captions, citations, metric units/n và font/overflow/log. Đọc PDF text và render visual phần sửa ở cả hai bản/bốn deliverables; lưu page-review scope. `make check-release` chỉ khi đánh giá hồ sơ chính thức, báo riêng blockers và không tự lấp bằng chứng hành chính.
3. **P08.03:** đối chiếu toàn bộ20ID với source section/evidence+hash/check; tạo `final-review-status.csv` gồm task/status/evidence/remaining/next-action. Dùng DONE_WITH_EVIDENCE/PARTIAL/OPEN/DEFERRED_WITH_REASON/DEFERRED_BY_USER. A3 hoãn; A1 thiếu chapter evidence vẫn OPEN; C5 chỉ CPU vẫn PARTIAL; B5 no-go không được gọi đã thực hiện ablation; E2E raw thiếu giữ Unverified.
4. **P08.04:** audit claim consistency: RQ1 Additive/Product/Holm; RQ2 revised/random/oracle/boundedness limits; RQ3 n=40 và adverse nearest-first comparisons; quantization loss và CPU/mobile scopes; LR 32 OR states, không clinical/NLP; E_i actual consumption theo current code; D1–D3 proposed. Mọi suy luận chưa được kiểm nêu rõ. Nếu lệch số, báo discrepancy trước khi sửa, không chạm manifest để pass.
5. **P08.05:** cập nhật traceability với đầu ra thật; soạn `response-draft.md` phản hồi từng nhận xét bằng việc đã làm/vị trí/bằng chứng/giới hạn. Đây là bản nháp nội bộ cho người dùng, không gửi email/hội đồng. Tạo validation.md và handoff.md, liệt kê blockers, deferred A3 và các bước còn lại theo evidence, không gọi 100% hoàn thành khi còn OPEN.

## E. Nguyên tắc và rủi ro

Giữ raw/results/checkpoints/old failures và working-tree edits. Không retrain/benchmark mới, không thay baseline/protocol/seed/weights, không publish/commit/push hoặc gửi phản hồi. Không làm tròn khiến đổi kết luận; không n=120 từ40seed×3conditions; không gộp replication/duplicates/device repeats vào n độc lập. Một report compiled/visual-pass không xác nhận clinical/operational effectiveness hoặc status công bố. A3 không cản workflow nhưng vẫn chưa hoàn thành ảnh.

## F. Deliverables

`docs/revision-plan/outputs/phase-08/{validation.md,final-review-status.csv,reproducibility.md,response-draft.md,handoff.md}`; float-checks.json nếu dùng tùy chọn output, PDF hashes/command logs/visual checklist; cập nhật05-traceability-matrix.md bằng nguồn thật. Không tạo bảng kết quả cho phần NOT_RUN.

## G. Acceptance criteria và kết thúc

Đủ 20ID, mỗi DONE có check/evidence locator; mỗi OPEN/PARTIAL/deferred có lý do và bước kế; A3 đúng chỉ đạo. Mọi checks nêu command/exit/env/scope, final files/hash xác định, không dùng receipt stale. Nội dung Việt–Anh nhất quán, unresolved không bị che. Kết thúc bằng bàn giao; không tự gửi/xuất bản hoặc tuyên bố nghiệm thu đã được chấp thuận.

## H. Final report

Báo 7 mục: việc hoàn thành; file/PDF; checks thực chạy/không chạy; nhận xét đã xử lý; unresolved/deferred; quyết định khoa học/kỹ thuật; handoff và việc còn cần người dùng thực hiện sau. Câu trả lời tự chứa và nêu rõ A3 được thêm sau theo người dùng.
