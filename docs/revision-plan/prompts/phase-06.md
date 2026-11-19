# Prompt Phase 06 — Tính khả thi ablation ảnh/văn bản/nguồn thông tin

Bạn làm việc tại `/home/ngthtrong/nckh2` cho đề tài **Xây dựng hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI (THS2026-68)**. Xử lý B5, hỗ trợ B3/B4 bằng feasibility audit; không tự huấn luyện/triển khai multimodal mới.

## A. Bối cảnh

Hội đồng gợi ý image-only/text-only/both nhưng yêu cầu cùng nhiệm vụ, dữ liệu và phép so sánh có nghĩa. Hiện model ảnh dự đoán mức ngập; LR dùng 5 cờ Boolean với nhãn OR, không xử lý text tự do. Hai nhóm dữ liệu không có paired rows/gold chung. Thu nhận ảnh/mô tả/GPS không chứng minh learned fusion. **A3 ảnh cá nhân được người dùng thêm sau**; không tìm/chèn/hỏi ảnh.

## B. Nguồn, sự thật đã biết và bàn giao

Đọc report README/RULES; `docs/revision-plan/{00-repository-audit.md,01-review-matrix.md,02-experiment-gap-analysis.md,04-phase-roadmap.md}` (X04); `outputs/phase-01/{scope-register.md,dataflow.md}`, `outputs/phase-02/data-card.md`, `outputs/phase-03/{rq-claims.csv,analysis.md}` và handoff tương ứng. Đây là output dự kiến; thiếu thì đọc nguồn tối thiểu, không tự tưởng tượng paired dataset hoặc kết quả phase trước.

Nguồn trực tiếp: `resource/Thuyết minh NCKH -THS2026-68.docx` mục12–16; `products/fe/model/{training_img.ipynb,urgency_ei/}`; `products/be/{cluster_service.py,rescue_core/}`; `thucnghiem/data/`, `thucnghiem/results/rq2_results/`; `docs/dataset-search/` chỉ là dossier/intake, không mặc định chứa request records/gold. Audit20refs chưa thấy trained NLP/paired multimodal gold; tìm bổ sung có giới hạn trước NO_GO nếu checkout khác.

## C. Mục tiêu và phạm vi

Quyết định **GO_PROTOCOL** hoặc **NO_GO** bằng điều kiện khoa học, không phải tạo bảng điểm. Phase này không thực nghiệm model mới. Kết quả no-go có lý do là deliverable hợp lệ; không phải tuyên bố đã làm ablation hoặc hoàn thành NLP đăng ký. Source masking F/E simulated có thể là nghiên cứu khác nhưng phải đặt tên và claim đúng.

## D. Tác vụ

1. **P06.01:** lập `eligibility.csv`: common target, unit/report ID, paired source availability, gold independent of tested fusion, label provenance/reliability, group split/leakage, baseline comparability, license/privacy và missing-modality policy. Mỗi ô có path/evidence hoặc UNKNOWN, không đánh PASS chỉ vì có code nhận text/image.
2. **P06.02:** đối chiếu target ảnh low/medium/high/non_flood với target LR OR32 states và target grouping/ranking. Kiểm nhãn có do chính formula tạo không (circular evaluation). Xác định một nhiệm vụ chung chỉ nếu có nhãn/paired dữ liệu thật. Nếu chỉ masking F/E ở simulated reports, giải thích đó là information-source sensitivity trên trường có cấu trúc, không ablation mô hình image/text hoặc deep multimodal.
3. **P06.03:** tạo `feasibility.md` và `no-go.md` khi gate thiếu. Nêu missing data/labels, khả năng thu thập hợp lệ, annotator/expert need, chi phí/rủi ro và protocol nghiên cứu sau này. Nếu đủ điều kiện thật, chỉ tạo protocol (same test IDs, common target/baseline/metrics, grouped paired CI/Holm, controlled modality masking); không tự train/download corpus hoặc chạy experiment ngoài phase.
4. **P06.04:** viết đoạn giải trình B5 và Future Work/scope draft, hoặc cập nhật nguồn report đúng phạm vi nếu đủ ngữ cảnh; không nói từ chối ablation vì kết quả có thể kém. Kiểm tính độc lập labels và wording, chạy document checks/build nếu sửa LaTeX. Tạo `handoff.md` cho P07 ghi NO_GO/GO_PROTOCOL và điều kiện cần nếu mở rộng sau này.

## E. Nguyên tắc, phụ thuộc và rủi ro

Không ghép Accuracy ảnh với fidelity LR; không dùng nhãn cảm xúc UIT-VSMEC mặc định là urgency cứu hộ. Không gọi raw data mô phỏng là paired real-world evaluation. Không tự tạo expert labels/patient ground truth hoặc đổi target sau nhìn test. Giữ artifacts/code/model cũ; không chỉnh rescue_core hoặc hợp đồng; không commit/push hay gửi dữ liệu cho người/dịch vụ khác. Rủi ro chính là leakage/circular labels, scope creep và chưa có quyền sử dụng dữ liệu tin nhắn.

## F. Deliverables

`docs/revision-plan/outputs/phase-06/{eligibility.csv,feasibility.md,no-go.md,handoff.md}`; nếu GO_PROTOCOL thay no-go bằng `protocol.md`, vẫn không có performance results. Draft paragraph B5/Future Work có source locator. Không cần GPU/điện thoại cho feasibility.

## G. Acceptance criteria và chuyển phase

Mỗi gate có bằng chứng; NO_GO hiện tại được giữ trừ khi dữ liệu mới thực sự vượt gate. Có định nghĩa rõ target/unit/label nếu GO_PROTOCOL. Chưa có số thì không có bảng kết quả. P07 có thể nhận no-go và ghi DEFERRED_WITH_REASON; việc nghiệm thu/giao tiếp Hội đồng vẫn do người dùng quyết định. Không tự tiếp tục nghiên cứu NLP/fusion.

## H. Final report

Báo việc hoàn thành/file, các kiểm tra thực chạy, trạng thái B5/B3/B4, điều kiện còn thiếu, quyết định khoa học chính và handoff. Nói rõ đây là đánh giá tính khả thi, không phải thí nghiệm multimodal đã thực hiện.
