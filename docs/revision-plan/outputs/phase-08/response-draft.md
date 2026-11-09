# Bản nháp phản hồi nội bộ — THS2026-68

Đã sửa báo cáo và tái phân tích artifact theo yêu cầu; chưa gửi Hội đồng. Trạng thái dưới đây nói mức xử lý nhận xét, không xác nhận Hội đồng chấp thuận. D1–D3 DONE là hoàn thành nội dung đề xuất, không triển khai chức năng. Giải trình B1/B3/B4 không hoàn thành thay cam kết NLP/fusion.

## A1 — OPEN

Đã xử lý: Giữ published theo xác nhận nhóm, thêm provenance và giới hạn cấp bài. Vị trí: `frontmatter/research-body-vi/en.tex`. Kiểm chứng: Tìm exact title/nguồn ISDS/Springer, đối chiếu title và tám tác giả.

Bằng chứng: `docs/revision-plan/outputs/phase-07/publication-verification.md` (SHA-256 trong final-review-status.csv). Giới hạn: Chưa có chapter DOI/online date/pages/volume/year. Bước tiếp: Bổ sung minh chứng cấp bài, không suy từ metadata quyển.

## A2 — DONE_WITH_EVIDENCE

Đã xử lý: Giữ nền layout; kiểm lại toàn quyển bằng thumbnail và phần đổi chi tiết. Vị trí: `PDF hai bản và nguồn float`. Kiểm chứng: Build/check, page overview và visual checklist.

Bằng chứng: `docs/revision-plan/outputs/phase-07/layout-review.md` (SHA-256 trong final-review-status.csv). Giới hạn: Khoảng trống biểu mẫu/kết thúc chương có chủ đích. Bước tiếp: Rà lại khi nội dung đổi.

## A3 — DEFERRED_BY_USER

Đã xử lý: Giữ nguyên placeholder theo chỉ đạo. Vị trí: `template/forms.tex; principal-investigator.tex`. Kiểm chứng: Hash StudentPhoto/forms không đổi trong preservation.

Bằng chứng: `docs/revision-plan/outputs/phase-01/claim-ledger.csv` (SHA-256 trong final-review-status.csv). Giới hạn: Ảnh chưa thêm. Bước tiếp: Người dùng thêm sau, không chặn.

## A4 — DONE_WITH_EVIDENCE

Đã xử lý: Đánh số tự động; bảng metadata mới có caption/label/ref. Vị trí: `labels/captions/LoF/LoT hai variants`. Kiểm chứng: Float checker hai bản:48 hình/38 bảng.

Bằng chứng: `docs/revision-plan/outputs/phase-08/float-checks.json` (SHA-256 trong final-review-status.csv). Giới hạn: Không xác nhận hồ sơ nghiệm thu. Bước tiếp: Chạy lại khi thêm hình/bảng.

## A5 — DONE_WITH_EVIDENCE

Đã xử lý: Build và kiểm source/PDF/log/font/visual. Vị trí: `RULES và sáu PDF`. Kiểm chứng: content/content-twoside/deliverables/check và diff đều đạt.

Bằng chứng: `docs/revision-plan/outputs/phase-07/commands.json` (SHA-256 trong final-review-status.csv). Giới hạn: Placeholder hành chính còn; không release approval. Bước tiếp: Hoàn thiện hồ sơ thật khi nộp chính thức.

## B1 — PARTIAL

Đã xử lý: Công khai NLP chưa chứng minh hoàn thành, LR không thay cam kết. Vị trí: `scope/introduction/conclusion/research-body`. Kiểm chứng: DOCX mục12–16, source và audit20refs.

Bằng chứng: `docs/revision-plan/outputs/phase-01/scope-register.md` (SHA-256 trong final-review-status.csv). Giới hạn: Chưa trained free-text NLP trong evidence hiện có. Bước tiếp: Nghiên cứu riêng hoặc bổ sung artifact thật nếu tồn tại.

## B2 — DONE_WITH_EVIDENCE

Đã xử lý: Tính lại12cấu hình; giải thích byte/params/timing và QAT xấu. Vị trí: `image-design/results optimization`. Kiểm chứng: Confusion/Accuracy/F1/high recall/critical/median/hash khớp.

Bằng chứng: `docs/revision-plan/outputs/phase-02/compression-audit.csv` (SHA-256 trong final-review-status.csv). Giới hạn: Chưa causal QAT diagnosis hoặc quantized Android validation. Bước tiếp: Chẩn đoán/đo thêm khi có mục tiêu mới.

## B3 — PARTIAL

Đã xử lý: Luồng computed→sent→stored, adapter chưa consumed E_LR. Vị trí: `methods/results/architecture/research-body`. Kiểm chứng: Đọc score/payload/storage/to_report_v2/core.

Bằng chứng: `docs/revision-plan/outputs/phase-01/dataflow.md` (SHA-256 trong final-review-status.csv). Giới hạn: Khoảng trống nối E_i; chưa learned fusion. Bước tiếp: Chỉ tích hợp code theo nhiệm vụ riêng sau xác nhận semantics.

## B4 — PARTIAL

Đã xử lý: Phân biệt tiếp nhận mô tả/keywords với trained NLP. Vị trí: `scope/conclusion/research-body`. Kiểm chứng: Source/code và cam kết DOCX.

Bằng chứng: `docs/revision-plan/outputs/phase-01/claim-ledger.csv` (SHA-256 trong final-review-status.csv). Giới hạn: Đóng góp NLP/fusion chưa được đo. Bước tiếp: Không gán surrogate thành NLP; giữ gap.

## B5 — DEFERRED_WITH_REASON

Đã xử lý: NO_GO image/text/both vì target/paired gold chưa đủ. Vị trí: `scope/conclusion limitations`. Kiểm chứng: eligibility.csv10gates; kiểm source label lineage.

Bằng chứng: `docs/revision-plan/outputs/phase-06/no-go.md` (SHA-256 trong final-review-status.csv). Giới hạn: Chưa thực hiện ablation. Bước tiếp: Định nghĩa common target/paired data/gold trước GO_PROTOCOL.

## C1 — PARTIAL

Đã xử lý: Data card/split/counts/source unknown minh bạch. Vị trí: `data/evaluation-design/setup`. Kiểm chứng: 1702header/MD5; split1189/257/256, no recorded group overlap.

Bằng chứng: `docs/revision-plan/outputs/phase-02/data-card.md` (SHA-256 trong final-review-status.csv). Giới hạn: URL/license/IAA/source-event independence và train-split lineage chưa đủ. Bước tiếp: Thu hồi provenance và đánh giá độc lập có thẩm quyền.

## C2 — DONE_WITH_EVIDENCE

Đã xử lý: Thống kê20nhóm header theo lớp/split, phân vị kích thước/tỷ lệ/byte. Vị trí: `data table image-profile`. Kiểm chứng: Format/mode từ header, tổng1702khớp split.

Bằng chứng: `docs/revision-plan/outputs/phase-02/image-profile.csv` (SHA-256 trong final-review-status.csv). Giới hạn: Không phải robustness evaluation. Bước tiếp: Dùng profile làm đầu vào protocol ảnh, không suy nhận diện.

## C3 — PARTIAL

Đã xử lý: OR32states,31:1,threshold/hệ số/count equivalence và sanity failures. Vị trí: `methods/results LR`. Kiểm chứng: Tính score JSON, đối chiếu32profiles; lr-hash-discrepancy.json.

Bằng chứng: `docs/revision-plan/outputs/phase-02/lr-audit.csv` (SHA-256 trong final-review-status.csv). Giới hạn: Raw byte lineage mismatch CRLF; chưa expert/clinical và chưa backend consumption. Bước tiếp: Giữ surrogate scope; giải quyết lineage/integration ở task riêng.

## C4 — PARTIAL

Đã xử lý: Trả lời RQ và giữ kết quả âm; replay949rows,3584numericchecks. Vị trí: `results RQ1–3/evaluation-design/limitations`. Kiểm chứng: 3576khớp; RQ1stress576CI+24empty; RQ3n=40.

Bằng chứng: `docs/revision-plan/outputs/phase-03/validation.txt` (SHA-256 trong final-review-status.csv). Giới hạn: 8RQ2rawp/Holm discrepancies còn; original full base check final-LF failed. Bước tiếp: Thu hồi unrounded metrics/tie handling; không sửa số để pass.

## C5 — OPEN

Đã xử lý: Không claim robustness khi chưa chạy inference. Vị trí: `limitations/conclusion`. Kiểm chứng: Model/split/preprocess preflight;9validationderivedinputs,0predictions.

Bằng chứng: `docs/revision-plan/outputs/phase-04/NOT_RUN.md` (SHA-256 trong final-review-status.csv). Giới hạn: Chưa clean/degraded performance hoặc Android sessions. Bước tiếp: Runtime/clean parity/device gate trước thí nghiệm.

## C6 — PARTIAL

Đã xử lý: 32phoneJSON verified; E2E raw chưa khôi phục, giữ Case8FAIL. Vị trí: `setup/system-tests/limitations`. Kiểm chứng: Recovery20refs/5historycommits/local/Drive; package check0.

Bằng chứng: `docs/revision-plan/outputs/phase-05/provenance-audit.csv` (SHA-256 trong final-review-status.csv). Giới hạn: APK hash/repeats/thermal/E2E raw và SMS delivery thiếu. Bước tiếp: Khôi phục raw; nếu cần dùng isolated one-device plan.

## C7 — PARTIAL

Đã xử lý: Ánh xạ IITT/VN Điều26 có phạm vi; numerical weights vẫn heuristic. Vị trí: `methods/conclusion`. Kiểm chứng: WHO official poster/reference; luật scannedp1/23/24 đã xem.

Bằng chứng: `docs/revision-plan/outputs/phase-02/criterion-source-map.csv` (SHA-256 trong final-review-status.csv). Giới hạn: Chưa chuyên gia xác nhận dispatch policy; không full legal/clinical conformance. Bước tiếp: Expert-led target/weights validation trước thí điểm.

## D1 — DONE_WITH_EVIDENCE

Đã xử lý: Định vị đa nguồn có nguồn/thời điểm/uncertainty, IP không mặc định hơn GPS. Vị trí: `conclusion Future Work`. Kiểm chứng: Đọc source/PDF; proposed-only.

Bằng chứng: `docs/revision-plan/outputs/phase-01/future-work.md` (SHA-256 trong final-review-status.csv). Giới hạn: Chưa triển khai hoặc đo positioning mới. Bước tiếp: Protocol định vị và quyền riêng tư khi có nhiệm vụ.

## D2 — DONE_WITH_EVIDENCE

Đã xử lý: Audio→ASR→trích thông tin→xác nhận; nêu rủi ro tiếng ồn/giọng/latency. Vị trí: `conclusion Future Work`. Kiểm chứng: Đọc source/PDF; proposed-only.

Bằng chứng: `docs/revision-plan/outputs/phase-01/future-work.md` (SHA-256 trong final-review-status.csv). Giới hạn: Chưa model/measurement ASR. Bước tiếp: Dữ liệu/nhãn/confirmation protocol trước nghiên cứu.

## D3 — DONE_WITH_EVIDENCE

Đã xử lý: Store≠deliver; SMS/DTN phụ thuộc hạ tầng; báo hộ/hotline/đội tại chỗ. Vị trí: `conclusion Future Work`. Kiểm chứng: Đọc source/PDF; proposed-only.

Bằng chứng: `docs/revision-plan/outputs/phase-01/future-work.md` (SHA-256 trong final-review-status.csv). Giới hạn: Chưa đo complete outage/no-phone workflow. Bước tiếp: Diễn tập có đơn vị chuyên môn, không hứa delivery vô điều kiện.
