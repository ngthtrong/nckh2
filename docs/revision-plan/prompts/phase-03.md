# Prompt Phase 03 — Kiểm chứng và tái phân tích RQ1–RQ3

Bạn làm việc tại `/home/ngthtrong/nckh2` cho đề tài **Xây dựng hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI (THS2026-68)**. Xử lý C4 bằng artifact có sẵn, hỗ trợ B3/C7. Không chạy lại generator/huấn luyện/full clustering campaign.

## A. Bối cảnh

Hội đồng yêu cầu kết luận từng RQ, baseline, thống kê, điều kiện thất bại và kết quả âm. Report hiện có bảng/discussion, nhưng kết luận/tóm tắt chưa đồng đều. RQ1 dùng bán tổng hợp Generator 3.0; RQ2/3 dùng bộ tổng hợp Candidate 4.1 riêng; không chuỗi validation thực địa. Người dùng sẽ thêm ảnh cá nhân A3 sau: giữ ô ảnh, không hỏi/tìm/chèn.

## B. Nguồn và trạng thái

Đọc report README/RULES, `docs/revision-plan/{00-repository-audit.md,02-experiment-gap-analysis.md,04-phase-roadmap.md}` (X01), `outputs/phase-01/handoff.md`, `outputs/phase-02/{data-card.md,measurement-scopes.csv,handoff.md}`. Đây là handoff dự kiến; thiếu thì audit nguồn gốc và ghi scope/prerequisite thay vì giả định phase trước đã chạy.

Nguồn: `thucnghiem/results/cij_baseline_benchmark_results/`; `rq1_results/{protocol.json,manifest.json,aggregate/,checkpoints/}`; replication `rq1_results_v2/full/`; `rq2_results/{rq2_summary.csv,rq2_paired_comparisons.csv,rq2_rank_alignment_test.csv,rq2_parameter_sensitivity_test.csv}`; `rq3_results/{rq3_dispatch_test_seed.csv,rq3_paired_comparisons_seed.csv,recompute_seed_level.py,rq3_seed_level_reanalysis_provenance.json}`; notebook executed, `paper/main.tex` và report results/evaluation-design.

Snapshot: Additive ARI.9191, Product.9072, Product−Additive −.01184, Holm.2560; Product copy5x ΔARI−.6108. RQ2 revised NDCG@5 .6669 vs random.6763; không general benefit established. RQ3 n40 seed, trung bình ba resource conditions; revised kém nearest-first về harm/deadline. Các số này cần đối chiếu raw. Audit đã kiểm585 hash, chưa replay statistics. Verifier hardcode `src/results`, yêu cầu NumPy2.5.1/matplotlib3.11.0; visual-env hiện khác. Không chạy mù script gốc.

## C. Mục tiêu và phạm vi

Lập kết luận hỗ trợ/không hỗ trợ/chưa đủ cho từng hypothesis, giữ protocol và evidence âm. Được viết harness phân tích riêng và sửa RQ report sections. Không đổi formulas/rescue_core, model/config hoặc historical result files.

## D. Tác vụ

1. **P03.01:** hash/source/manifest audit; định nghĩa independent unit, development/calibration/test, primary/replication và evaluator-only labels. Tạo `outputs/phase-03/protocol.json` cùng source-hashes. Không gộp hai generators hoặc replication; không coi copy/scenario là independent samples.
2. **P03.02:** đọc verifier/recompute trước chạy. Tạo adapter/harness chỉ đọc dưới outputs03, giải đường dẫn cũ bằng mapping rõ; nếu cần pin, dùng isolated environment không cài đè env chung. Replay từ CSV/checkpoint cần thiết, ghi command/version/bootstrap seed/tolerance và family definition. Nếu môi trường không đáp ứng, ghi NOT_REPLAYED và phạm vi số đã kiểm, không ghi PASS giả.
3. **P03.03:** RQ1: contrasts Product vs independently selected Additive, matched-density và Leiden; delta/CI/raw-p/Holm/win-tie-loss/density/fake destinations; stress từng condition và non-monotonic copy2x/5x. RQ2: oracle grouping, NDCG/random/legacy; exact-copy invariance so với coordinated attacks; coefficient sensitivity hiện có. Tạo statistics.csv và condition analysis, không tune test.
4. **P03.04:** RQ3: dùng 40 seed đã averaging 3 scenarios, direction-oriented harm/deadline/benefit và đúng 14-endpoint Holm family theo provenance. Phân tích nearest-first/legacy/partition losses; không n=120 hoặc cherry-pick scenario. Kết nối trade-off mục tiêu ranking với scheduling, nêu cơ chế khả dĩ là interpretation, không causal diagnosis chưa cô lập. Tạo `rq-claims.csv`, `analysis.md` với status/metric/baseline/delta/CI/p/scope/source/section.
5. **P03.05:** cập nhật RQ1–3 trong `report/chapters/04-evaluation/sections/results.tex`, evaluation-design/limitations nếu cần, không sửa numeric generated tay. Handoff kết luận cho P07 đồng bộ summary/conclusion. Chạy compare/tolerance/coverage, content build/check nếu đổi LaTeX và inspect PDF/log. Lưu validation.txt và handoff.md; không tiếp phase04.

## E. Nguyên tắc và rủi ro

Không đổi số để thắng, không che thất bại, không thay bản cũ bằng kết quả mới không so sánh được. CI bootstrap chưa hiệu chỉnh và Holm Wilcoxon có thể khác do estimand/procedure; không chọn phép nào thuận lợi hoặc gọi mâu thuẫn khi chưa phân tích. p>.05 không chứng minh tương đương. Boundedness score không bảo đảm graph robustness, ranking alignment hoặc dispatch benefit. Không claim simulated harm là người được cứu. Không commit/push/gửi nguồn cho API ngoài.

## F. Deliverables

`docs/revision-plan/outputs/phase-03/{protocol.json,source-hashes.json,statistics.csv,rq-claims.csv,analysis.md,validation.txt,handoff.md}`; harness đọc artifact nếu cần; report RQ sources. Giữ CSV/notebook/checkpoint/manifest gốc nguyên byte.

## G. Acceptance criteria và chuyển phase

Mỗi RQ có formal question, baseline, independent n, effect/uncertainty/test family, điều kiện tốt/xấu và kết luận đúng. RQ1 không superiority chung, RQ2 không benefit alignment chung, RQ3 adverse comparisons nêu rõ. Số tính lại khớp hoặc discrepancy có disposition, không replay thì ghi rõ. Output đủ cho P06/P07; không cần đợi điện thoại/ảnh mới.

## H. Final report

Báo hoàn thành, file, kiểm thực chạy/exit/env, nhận xét đã xử lý, unresolved discrepancies, quyết định thống kê và handoff. Nêu phần nào chỉ đối chiếu/tái phân tích, không nói đã chạy lại thực nghiệm khoa học.
