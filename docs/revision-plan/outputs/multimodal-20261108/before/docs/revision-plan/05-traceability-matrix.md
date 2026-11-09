# Truy vết nhận xét → cam kết → bằng chứng → sửa đổi

Nguồn cam kết là DOCX `resource/Thuyết minh NCKH -THS2026-68.docx` mục 12–16. E01–E18 định nghĩa ở audit. Nguồn nhận xét ngoài bản người dùng cung cấp: `tmp.md`, Nhận xét 06–10 → B1–B5, 11–17 → C1–C7, 18–20 → D1–D3; các đoạn diễn giải của người tổng hợp không được gán thành lời Hội đồng nguyên văn. Task `Pxx.nn` là số bước trong prompt tương ứng. Bảng kế hoạch dưới đây giữ snapshot P00; trạng thái thực thi mới được bổ sung ở cuối tài liệu và final-review-status.csv. Không suy mọi thí nghiệm đã chạy từ tên output dự kiến.

| ID | Nội dung thuyết minh/nguồn nghĩa vụ | Thành phần và kết quả hiện có | Phase/tác vụ | Vị trí báo cáo cần chỉnh/kiểm | Đầu ra kiểm chứng dự kiến | Trạng thái audit → đích xử lý |
|---|---|---|---|---|---|---|
| A1 | Mục 15 tổng kết/công bố; mục16 ghi sản phẩm xuất bản, không suy ra trạng thái hiện tại | E13; paper source, shared research-body; external lookup chỉ cấp quyển | P07.02, P08.03 | frontmatter/research-body-vi.tex, research-body-en.tex; shared summary/bulletin | phase-07/publication-verification.md | Reported published → verified cấp bài hoặc OPEN provenance rõ |
| A2 | Yêu cầu hình thức Hội đồng/mẫu trường, không phải thí nghiệm | E12; layout patch 165 trang | P07.04, P08.02 | template/typography.tex, ctu-report.cls, source float và PDF toàn quyển | phase-07/layout-review.md | Đã xử lý nhiều phần → regression sau nội dung |
| A3 | Biểu mẫu sinh viên; người dùng chỉ đạo thêm ảnh sau | E14; StudentPhoto placeholder | P07.02 ghi hoãn, P08.03 | frontmatter/principal-investigator.tex, template/forms.tex giữ nguyên ô | phase-08/final-review-status.csv | DEFERRED_BY_USER, không chặn phase |
| A4 | Yêu cầu hình thức Hội đồng/mẫu trường | E12; 48 hình/37 bảng checker hiện đạt | P07.04, P08.02 | labels/captions, .lof/.lot, PDF và script check_float_references.py | phase-08/float-checks.json hoặc validation.md | Đạt tại snapshot → kiểm đủ sau thay đổi |
| A5 | Mẫu trường, report/RULES.md | E12; sáu PDF và template | P07.04–05, P08.02 | main.tex/template/config, deliverables qua nguồn shared | phase-08/validation.md | Có nền hình thức → toàn bộ đầu ra được kiểm |
| B1 | Mục12/13/14/15: văn bản cứu hộ tiếng Việt, DistilBERT; mục16 bộ model | E01/E03/E04; NLP search không có trained free-text | P01.01–03, P06.01 | introduction, data-methods/sections/scope.tex; conclusion | phase-01/scope-register.md; phase-06/feasibility.md | Missing evidence NLP → công khai hoàn thành một phần |
| B2 | Mục14/15: Model Quantization/tối ưu di động; mục16 model nhẹ | E05/E06; PTQ/QAT/pruning summaries, 32 phone runs | P02.03, P05.01–03 | image-design.tex, evaluation/results.tex optimization/phone; limitations | phase-02/compression-audit.csv; phase-05/provenance-audit.csv | Evaluated/Reported → giải thích trade-off/selection/scope |
| B3 | Mục12–16: đa phương thức/không gian–ngữ nghĩa | E04/E16; F và heuristic E; E_i chưa consumed | P01.02–03, P06.01–03 | architecture.tex, methods.tex, scope.tex; research-body và conclusion | phase-01/dataflow.md; phase-06/eligibility.csv | Implemented system integration ≠ learned fusion → wording đúng code |
| B4 | Mục13–15: xử lý ngôn ngữ tiếng Việt | E03/E04; structured LR + keywords | P01.01–03, P02.02 | scope/methods/results LR/conclusion | phase-01/claim-ledger.csv; phase-02/lr-audit.csv | Không có đánh giá NLP → không gán đóng góp ngôn ngữ đã được đo |
| B5 | Nhận xét bổ sung Hội đồng; hỗ trợ mục12/16, không mặc định cam kết ablation | E02/E03/E16; targets khác và không paired gold | P06.01–04 | scope/limitations/Future Work, không bảng kết quả giả | phase-06/no-go.md hoặc protocol riêng | NO_GO hiện tại → giải trình hoặc nghiên cứu riêng có gate |
| C1 | Mục14/15: thu thập/gán nhãn/chuẩn hóa dữ liệu | E02/E15; notebook/split1702; generator manifests | P02.01, P03.01 | data.tex/evaluation-design.tex/setup.tex | phase-02/data-card.md,image-profile.csv | Có dữ liệu/split → nêu đủ provenance/unknown/independence |
| C2 | Mục14: ảnh đầu vào/tiền xử lý; nhận xét Hội đồng chi tiết | E02; snapshot header formats/resolution | P02.01, P04.01–02 | data.tex/image-design.tex và bảng kỹ thuật | phase-02/image-profile.csv; phase-04/variant-manifest.csv | Metadata sẵn có → thống kê không cần model |
| C3 | Mục12/14/16: phân loại khẩn cấp; phương án LR hiện tại khác NLP đăng ký | E03/E04; 32 OR profiles, coefficients, payload E_i | P01.02, P02.02; P05.03 diagnostic nếu cần | methods.tex/results LR/scope/research-body | phase-02/lr-audit.csv; phase-01/dataflow.md | Surrogate evaluated; integration gap → đúng cơ chế/không clinical claim |
| C4 | Mục14/15: thực nghiệm/phân cụm; RQ cụ thể từ paper/current protocol | E09–11; RQ CSV/checkpoint/40 independent units | P03.01–05, P07.01 | results.tex RQ1–3, limitations.tex, conclusion và shared summary | phase-03/statistics.csv,rq-claims.csv,analysis.md | Evaluated/Reported → effect/CI/Holm/failures/kết luận đúng |
| C5 | Mục14: thử điện thoại/ảnh; nhận xét robustness bổ sung | E02/E06; chưa controlled quality result | P04.01–05 | image-design/evaluation-design/setup và results subsection mới | phase-04/protocol.json,predictions.csv,metrics.csv | Missing → data mới hợp lệ hoặc PARTIAL/OPEN; không limitations-only=done |
| C6 | Mục14: mobile thực tế và mạng yếu | E06/E07/E08; raw phone32/proxy2313; E2E chỉ narrative hiện có | P02.04, P05.01–05 | setup.tex/system-tests.tex/results phone/limitations.tex | phase-05/evidence-recovery.md,provenance-audit.csv,runs nếu có | Evaluated phone; E2E Unverified → recovery trước rerun; tách scope |
| C7 | Mục12/14: hỗ trợ quyết định khẩn cấp; tiêu chí do nhóm lựa chọn | E03/E10/E16; WHO mapped signs và sensitivity, heuristic constants | P01.03, P02.02, P03.04 | methods.tex/limitations.tex/conclusion | phase-02/criterion-source-map.csv; phase-03/analysis.md | Nguồn dấu hiệu ≠ xác nhận dispatch → giữ adaptation/unknown |
| D1 | Nhận xét Future Work, không nghĩa vụ triển khai mới | E15/E17; GPS nullable/manual review | P01.04, P07.03 | conclusion.tex Future Work | phase-01/future-work.md | Proposed: IP/Wi-Fi/network với uncertainty, không mặc định hơn GPS |
| D2 | Nhận xét Future Work, không nghĩa vụ triển khai mới | E15/E16; chưa speech evidence | P01.04, P07.03 | conclusion.tex Future Work | phase-01/future-work.md | Proposed ASR/audio+confirmation, không tạo kết quả |
| D3 | Mục12/14 mạng yếu và nhận xét Future Work complete outage/no phone | E17; outbox/SMS code, DTN dự kiến | P01.04, P05.04, P07.03 | synchronization/limitations/conclusion | phase-01/future-work.md; phase-05/run-plan.md nếu cần | Store≠deliver; DTN/SMS hạ tầng và báo hộ/đội tại chỗ rõ |

## Hợp đồng trạng thái và bằng chứng

- `DONE_WITH_EVIDENCE`: việc chỉnh/tính/đo thực sự được thực hiện, có tệp nguồn và check. Không đồng nghĩa Hội đồng đã chấp thuận.
- `PARTIAL`: một phần đủ bằng chứng, phần còn thiếu được nêu; ví dụ chỉ CPU robustness khi nhận xét hỏi mobile.
- `OPEN`: thiếu bằng chứng quan trọng hoặc thông tin chưa xác minh; ví dụ trạng thái riêng bài báo/raw E2E chưa phục hồi.
- `DEFERRED_WITH_REASON`: ngoài phạm vi, không khả thi hoặc chưa phù hợp task/nhãn; không gắn nghĩa “đã chạy”.
- `DEFERRED_BY_USER`: áp dụng A3 theo chỉ đạo trong `evidence/user-amendments.md`.

Final ledger dự kiến có cột ID, action/task, status, source/section, evidence path+hash, command/check result, residual gap, next owner/action. Các trạng thái audit tại đây là snapshot; không tự cập nhật thành DONE khi chỉ tạo prompt.

## Trạng thái thực thi sau P01–P08

**Snapshot trước followup 08/11/2026.** Trạng thái mới của P02/P03/P04/P05/P07 nằm ở [followup](outputs/followup-20261108/README.md): C5 hiện PARTIAL/CPU_ONLY nhờ 2.304 test predictions, chưa Android. Các trạng thái thiếu hồ sơ C1/C4/C6/C7/A1 vẫn giữ; receipt bố cục/build của PDF mới tách riêng trong followup, không tái dùng freeze dưới đây.

Nguồn quyết định/check/hash cuối: [P08 ledger](outputs/phase-08/final-review-status.csv), [validation](outputs/phase-08/validation.md), [response draft](outputs/phase-08/response-draft.md).

| ID | Status | Evidence | Gap / next action |
|---|---|---|---|
| A1 | OPEN | [publication-verification.md](outputs/phase-07/publication-verification.md) | Chưa có chapter DOI/online date/pages/volume/year; Bổ sung minh chứng cấp bài, không suy từ metadata quyển |
| A2 | DONE_WITH_EVIDENCE | [layout-review.md](outputs/phase-07/layout-review.md) | Khoảng trống biểu mẫu/kết thúc chương có chủ đích; Rà lại khi nội dung đổi |
| A3 | DEFERRED_BY_USER | [claim-ledger.csv](outputs/phase-01/claim-ledger.csv) | Ảnh chưa thêm; Người dùng thêm sau, không chặn |
| A4 | DONE_WITH_EVIDENCE | [float-checks.json](outputs/phase-08/float-checks.json) | Không xác nhận hồ sơ nghiệm thu; Chạy lại khi thêm hình/bảng |
| A5 | DONE_WITH_EVIDENCE | [commands.json](outputs/phase-07/commands.json) | Placeholder hành chính còn; không release approval; Hoàn thiện hồ sơ thật khi nộp chính thức |
| B1 | PARTIAL | [scope-register.md](outputs/phase-01/scope-register.md) | Chưa trained free-text NLP trong evidence hiện có; Nghiên cứu riêng hoặc bổ sung artifact thật nếu tồn tại |
| B2 | DONE_WITH_EVIDENCE | [compression-audit.csv](outputs/phase-02/compression-audit.csv) | Chưa causal QAT diagnosis hoặc quantized Android validation; Chẩn đoán/đo thêm khi có mục tiêu mới |
| B3 | PARTIAL | [dataflow.md](outputs/phase-01/dataflow.md) | Khoảng trống nối E_i; chưa learned fusion; Chỉ tích hợp code theo nhiệm vụ riêng sau xác nhận semantics |
| B4 | PARTIAL | [claim-ledger.csv](outputs/phase-01/claim-ledger.csv) | Đóng góp NLP/fusion chưa được đo; Không gán surrogate thành NLP; giữ gap |
| B5 | DEFERRED_WITH_REASON | [no-go.md](outputs/phase-06/no-go.md) | Chưa thực hiện ablation; Định nghĩa common target/paired data/gold trước GO_PROTOCOL |
| C1 | PARTIAL | [data-card.md](outputs/phase-02/data-card.md) | URL/license/IAA/source-event independence và train-split lineage chưa đủ; Thu hồi provenance và đánh giá độc lập có thẩm quyền |
| C2 | DONE_WITH_EVIDENCE | [image-profile.csv](outputs/phase-02/image-profile.csv) | Không phải robustness evaluation; Dùng profile làm đầu vào protocol ảnh, không suy nhận diện |
| C3 | PARTIAL | [lr-audit.csv](outputs/phase-02/lr-audit.csv) | Raw byte lineage mismatch CRLF; chưa expert/clinical và chưa backend consumption; Giữ surrogate scope; giải quyết lineage/integration ở task riêng |
| C4 | PARTIAL | [validation.txt](outputs/phase-03/validation.txt) | 8RQ2rawp/Holm discrepancies còn; original full base check final-LF failed; Thu hồi unrounded metrics/tie handling; không sửa số để pass |
| C5 | OPEN | [NOT_RUN.md](outputs/phase-04/NOT_RUN.md) | Chưa clean/degraded performance hoặc Android sessions; Runtime/clean parity/device gate trước thí nghiệm |
| C6 | PARTIAL | [provenance-audit.csv](outputs/phase-05/provenance-audit.csv) | APK hash/repeats/thermal/E2E raw và SMS delivery thiếu; Khôi phục raw; nếu cần dùng isolated one-device plan |
| C7 | PARTIAL | [criterion-source-map.csv](outputs/phase-02/criterion-source-map.csv) | Chưa chuyên gia xác nhận dispatch policy; không full legal/clinical conformance; Expert-led target/weights validation trước thí điểm |
| D1 | DONE_WITH_EVIDENCE | [future-work.md](outputs/phase-01/future-work.md) | Chưa triển khai hoặc đo positioning mới; Protocol định vị và quyền riêng tư khi có nhiệm vụ |
| D2 | DONE_WITH_EVIDENCE | [future-work.md](outputs/phase-01/future-work.md) | Chưa model/measurement ASR; Dữ liệu/nhãn/confirmation protocol trước nghiên cứu |
| D3 | DONE_WITH_EVIDENCE | [future-work.md](outputs/phase-01/future-work.md) | Chưa đo complete outage/no-phone workflow; Diễn tập có đơn vị chuyên môn, không hứa delivery vô điều kiện |
