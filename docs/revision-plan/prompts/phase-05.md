# Prompt Phase 05 — Khôi phục bằng chứng mobile/E2E và đo phần thật sự thiếu

Bạn làm việc tại `/home/ngthtrong/nckh2` cho đề tài **Xây dựng hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI (THS2026-68)**. Xử lý C6/B2 và diagnostic C3 theo X03. Bắt đầu bằng khôi phục artifact; không mặc định chạy lại campaign.

## A. Bối cảnh

Đã có 32 raw JSON image benchmark, mỗi phiên 256 test ảnh, bốn máy/seed159,1024/baseline,pruning/ONNX,PTE. Đã có 2.313 lượt proxy PC. Report mô tả hai run Android S10e ngày 24/10/2026 và tài liệu mô tả hai run web; raw E2E tương ứng chưa thấy trong checkout khảo sát. Vì vậy không thể kết luận “chưa đo điện thoại”, cũng không thể gọi mọi E2E claim đã xác minh độc lập. Người dùng thêm ảnh A3 sau: giữ nguyên ô ảnh, không tìm/chèn/hỏi ảnh.

## B. Nguồn và đầu vào

Đọc report README/RULES, `docs/revision-plan/{00-repository-audit.md,02-experiment-gap-analysis.md,04-phase-roadmap.md}` (X03), `outputs/phase-02/{measurement-scopes.csv,handoff.md}` và phase01 dataflow. Output bàn giao có thể chưa tồn tại; đọc raw/source và ghi prerequisite thực tế nếu thiếu.

Đọc `products/fe/reports/seed{159,1024}/mobile/`, `report/generated/phone-benchmarks/{summary.csv,selection_steps.csv}`; `products/fe/experiment_mobile/{README.md,coordinator.py,manual_errors.py,mobile_api.py}`; `thuc_nghiem_nq/experiment_mobile_e2e/`, `experiment_e2e/RESULTS.md`, `experiment_weak_network/results/20261005-102040/`; report `chapters/04-evaluation/sections/{setup,system-tests,limitations}.tex`.

Giữ nguồn narrative: run_001 Case8 raw được mô tả 8 PASS/1 FAIL, người chạy xác nhận giữ/gửi lại nhưng còn app thoát/mất phiên; chưa có log phân biệt crash. Không sửa JSON cũ từ FAIL thành PASS. Snapshot E_i app gửi nhưng adapter đọc urgency/description; probe chỉ kiểm hành vi, không sửa contract để pass.

## C. Mục tiêu và quyết định chạy

Khôi phục provenance đủ cho các claim cần giữ. Có raw đầy đủ thì **SKIP_RERUN** và tái tổng hợp. Chỉ chạy phần thiếu nếu exact artifact/device/DB test sẵn; không thiết bị thì tạo gói/run-plan và NOT_RUN, thu hẹp claim. Lặp timing là Recommended; không bắt buộc32 tổ hợp. Không chuyển cluster server sang mobile.

## D. Tác vụ

1. **P05.01:** status/hash rồi inventory 32 JSON, CSV nguồn và link E2E thiếu. Tìm cả working tree, refs/history, archive/backup local hoặc nguồn được kết nối sẵn có quyền, không liên hệ người khác. Tạo `evidence-recovery.md` nêu found/missing/search-bound/source, phân biệt recorded với independently verified.
2. **P05.02:** kiểm raw tìm được: manifest/hash/ID/model/APK/version/time/device/split và run association. Recompute metric/sample counts, tách manual UI/service calls/dashboard checks. Tạo `provenance-audit.csv`; raw đủ → tổng hợp và bỏ nhánh chạy. Không bịa hash APK từ version string hoặc model hash.
3. **P05.03:** nếu cần claim chưa đủ, khóa `run-plan.md`: một máy, model được chọn đã xác minh, fixtures validation run_001/run_002, isolated backend/DB/volume riêng. Ghi APK/model/package/backend hashes, input/created report IDs. Test online,503→retry,outbox/reconnect,proxy300/20kbit/s,missing GPS/status và E_i propagation diagnostic theo code hiện tại. Nếu chỉ latency, dùng 256 ảnh và một runtime/model cần thiết với phiên lặp kiểm thermal; không train.
4. **P05.04:** chỉ chạy khi thực có device/config an toàn; runner dùng app inference/use case/outbox thật, không direct-API thay luồng app. Lưu FAIL/NOT_RUN, logcat/observations, màn hình nếu thao tác thủ công; xác nhận giữ bài/gửi đúng một lần. Mất hoàn toàn kết nối: local queue≠delivery; proxy≠mạng cell; SMS cần gateway/cell và không tự nhắn số người khác. Không reset shared DB hoặc xóa pending người dùng.
5. **P05.05:** tổng hợp kết quả mới riêng historical rows, cập nhật subsection system-tests/setup/limitations đúng scope hoặc bàn giao P07. Kiểm source hash/count/metric/ID và logs; nếu sửa LaTeX build/check và inspect phần đổi. Tạo handoff.md ghi evidence recovered, SKIP_RERUN/MEASURED/NOT_RUN và claim còn OPEN.

## E. Nguyên tắc và rủi ro

Bảo toàn raw/results/checkpoints cũ, edits đang có và server data. Không đổi adapter E_i/urgency hoặc model/threshold để thuận thí nghiệm; mismatch phải report. Scripts/hướng dẫn cũ có thể chỉ là kế hoạch, xác minh actual implementation. Không dùng32 runs một phiên/tổ hợp làm chứng minh hiệu năng dài hạn, không cộng proxy rows thành mobile samples. Không commit/push/publish hoặc gửi tin nhắn.

## F. Deliverables

`docs/revision-plan/outputs/phase-05/{evidence-recovery.md,provenance-audit.csv,run-plan.md,handoff.md}`; nếu chạy thì `runs/<new-id>/{manifest.json,checks.csv,summary.json,logcat.txt,backend-observations.json}` và UI evidence thực có. Nếu không chạy: `NOT_RUN.md` + gói/protocol, không dummy metrics. Source report liên quan và check receipts nếu đổi.

## G. Acceptance criteria và chuyển phase

Đủ inventory/scope, mỗi claim có provenance hoặc unverified; không mất failure Case8; raw đủ thì không rerun thừa; raw mới có hashes/device/IDs và n đúng. C6 có thể PARTIAL nếu thiếu evidence; không gọi PASS cho NOT_RUN. Handoff rõ cho P07, không tự chạy phase khác.

## H. Final report

Báo hoàn thành/file, kiểm hoặc benchmark thực chạy, ID/device/scope, nhận xét xử lý, artifact còn thiếu, quyết định recovery-vs-rerun và thông tin bàn giao. Phân biệt việc chuẩn bị runner với việc đã đo trên điện thoại.
