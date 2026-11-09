# Prompt Phase 07 — Tích hợp kết quả và hoàn thiện báo cáo

Bạn làm việc tại `/home/ngthtrong/nckh2` cho đề tài **Xây dựng hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI (THS2026-68)**. Hoàn thiện nội dung nhất quán và hình thức từ evidence đã xác minh, xử lý A1/A2/A4/A5 và tổng hợp B–D. Không chạy nghiên cứu mới.

## A. Bối cảnh

Audit đã thấy report có sửa layout chưa commit: main/content hai bản 165 trang, 48 hình/37 bảng; source LaTeX/PDF/template đang bẩn. Phần phương pháp/kết quả nhiều nội dung đã tốt; kết luận/tóm tắt phải phản ánh kết quả âm, scope NLP/fusion/LR và giới hạn dữ liệu. **Người dùng xác nhận ảnh cá nhân A3 sẽ thêm sau**: giữ nguyên ô ảnh, ghi DEFERRED_BY_USER, không tìm/xác minh/chèn/hỏi ảnh và không xem đây là blocker.

## B. Đầu vào, nguồn và giả định phải kiểm lại

Đọc quy tắc repo, `report/{README.md,RULES.md}`, `report/audit/layout-2026-11-07.*`, `docs/revision-plan/{00-repository-audit.md,01-review-matrix.md,04-phase-roadmap.md,05-traceability-matrix.md}`, `evidence/{user-amendments.md,external-verification.md}`. `report/ra-soat-va-bo-sung.md` là đường dẫn lịch sử đang vắng, chỉ đọc nếu đã được khôi phục. Đọc handoff trong `docs/revision-plan/outputs/phase-01…phase-06/` và data cards/claim ledgers. Các output này là dự kiến; không có thì không giả định thí nghiệm đã chạy. Lập missing-handoff register và tiếp tục phần độc lập. P04/P05/P06 được phép NOT_RUN/CPU_ONLY/SKIP_RERUN/NO_GO có lý do, giữ C5/C6 PARTIAL khi cần.

Nguồn report: `main.tex`, `chapters/`, `frontmatter/research-body-{vi,en}.tex`, `deliverables/`, `config/benchmark-sources.json`, `generated/provenance.json`, `scripts/`. Thuyết minh DOCX trong resource. Report hiện ghi published theo xác nhận cũ, chưa điền tập/năm; tra cứu cấp quyển Springer chưa đủ xác minh chapter. Không lấy DOI Zenodo phần mềm làm DOI bài hoặc ngày print dự kiến làm trạng thái online. Shared sources phải sửa một lần cho các bản tóm tắt/bản tin, không chỉnh từng PDF.

## C. Mục tiêu và phạm vi

Một bản báo cáo thống nhất về dataset/model/scope/n/số liệu/claim trong Việt–Anh và kết luận, giữ kết quả lịch sử tách số mới. Chỉ chỉnh source cần thiết và generated qua script; build/inspect đúng variants. Không train/inference/rerun để lấp handoff thiếu.

## D. Tác vụ

1. **P07.01:** status/hash baseline, kiểm handoff/protocol/source/input hash; lập integration-log.md. Chọn nguồn theo protocol, không chọn số tốt nhất. Đối chiếu nhãn seed/split/units; giữ RQ1 primary/replication riêng, RQ3 n40, Android classifyImage≠CPU predict. Tệp generated chỉ sinh qua exporter có source audit, không sửa tay.
2. **P07.02:** xác minh A1 ở cấp paper/chapter từ nguồn chính thức/minh chứng có sẵn: title/authors/venue/chapter DOI/online date/pages/volume/year và phạm vi copyright/print. Ghi `publication-verification.md` với ngày/nguồn, xác nhận cũ và unresolved conflict. Chưa đủ thì giữ trạng thái có provenance/OPEN, không tự nâng/hạ hoặc điền dữ liệu quyển chưa xác định. **A3 chỉ ghi hoãn; không truy cập link ảnh hoặc sửa StudentPhoto.**
3. **P07.03:** tích hợp conclusion/introduction/research-body Việt–Anh/summary/bulletin: LR có cấu trúc không NLP; E_i consumed chỉ khi code/evidence chứng minh (snapshot cũ không có); system integration≠learned fusion; dataset mô phỏng không real validation. RQ1 không superiority chung, RQ2 alignment không established, RQ3 nearest-first tốt hơn outcomes đã xét. Kết quả mới P04/05 chỉ thêm nếu raw đủ; D1–D3 có feasibility và proposed status, không lời hứa triển khai.
4. **P07.04:** rà A2/A4/A5 sau nội dung ổn định: RULES/mẫu chính thức, font/lề/spacing, caption/labels/refs/LoF/LoT, float và hình ngang. Giữ chi tiết hình, không giảm font/lề, không rút sơ đồ để ép trang; không chạy generator đè Draw.io manual. Kiểm docs drift liên quan với timeline; không sửa hồi tố ghi chép lịch sử thành kết quả mới. Tạo layout-review.md và danh sách trang đã xem.
5. **P07.05:** build `make -C report content`, `content-twoside`, `deliverables`; sau đó `make -C report check`, checker từng build và `git diff --check`. Dùng pdftotext/log/ảnh render kiểm phần đổi ở cả hai bản và bốn sản phẩm Việt–Anh; kiểm font/overflow/references. Nếu dependency thiếu ghi rõ failed/not-run; không dùng PDF cũ giả build mới. Tạo handoff.md để P08 kiểm freeze.

## E. Nguyên tắc và rủi ro

Bảo toàn sửa đổi người dùng, raw/model/results/figures cũ và manifest. Không che negative results hoặc E2E failures, không công nhận hiệu quả lâm sàng/thực địa từ surrogate. Không đổi thuật toán/weights/contract/publication state khi thiếu căn cứ. Không tự commit/push/full-release/gửi phản hồi bên ngoài. Build pass không đồng nghĩa readiness/acceptance. A1 thiếu nguồn vẫn OPEN, A3 hoãn có chủ ý.

## F. Deliverables

Report LaTeX/generated sources/PDF đúng target; `docs/revision-plan/outputs/phase-07/{integration-log.md,publication-verification.md,layout-review.md,handoff.md}` cùng command/exit/log/hash và page-review evidence. Liệt kê tệp đổi thực tế, không ghi artifact dự kiến như đã tạo.

## G. Acceptance criteria và chuyển phase

Claims/số liệu/nguồn nhất quán toàn quyển và Việt–Anh; từng số có lineage; unresolved không bị xóa. Hai bản nội dung+bốn deliverables build/check/visual được kiểm hoặc limitation nêu rõ. Không sửa A3. Freeze source/hash để P08 audit, không chạy P08 tự động.

## H. Final report

Báo việc hoàn thành/file/PDF; checks thực chạy/exit và phạm vi visual; A1/A2/A4/A5/tổng hợp B–D xử lý đến đâu; gaps/open/deferred; quyết định nguồn/claim/format; handoff cho P08. Nêu A3 người dùng thêm sau, không yêu cầu ảnh.
