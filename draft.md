
# Kế hoạch: Sửa lỗi & hoàn thiện bài báo theo PhanBien_BaiBao.md

## Phạm vi đã chốt với người dùng

- Xử lý **tất cả 🔴 + tất cả 🟠** (bỏ qua phần lớn 🟡 trừ khi rẻ và đi kèm).
- **1.2 (equity):** xây một **mô phỏng outcome-metric** (thời gian trung bình đến nạn nhân yếu thế dưới điều phối tham lam theo P) để chứng minh ranking có-equity *tốt hơn*, không chỉ *khác*.
- **2.2 (ARI bão hòa):** thêm **một độ đo phân biệt** (giữ nguyên dataset chính seed=42), không làm lại ground-truth.
- **Đồng bộ 3 artifact:** `paper/main.tex` + `resource/BaiBao_NoiDung.md` + `resource/PaperV2.md`.

## Sự thật đã xác minh (khác memory)

- Demo nằm ở `demo/` (KHÔNG phải `demo/v2/`). Chạy: `demo/.venv/bin/python run_all.py` (~10s, sạch).
- Mọi số liệu bài báo truy về `demo/results/tables/*.json`.
- **5.4 (khóa API rò rỉ): báo động giả** — không có chuỗi `sk-<20+ ký tự>` nào trong repo. Không cần xử lý.
- **5.1 (F_max gate sync): đã xong** — cả hai file .md dùng `max(F_i·C_i)`.
- Toggle bỏ S_context mà giữ gating: `WeightParams(gamma=0.0)` → `build_weight_matrix(..., mode="gating")`.
- `is_fake` (nhãn thật) và `confidence`/C_i (tính bằng heuristic) cùng tồn tại trên mỗi Event → tính AUC dễ.

---

## PHẦN A — Thí nghiệm mới (Python, trong `demo/`)

### exp6 — Ablation circularity (🔴 1.1)

File mới `demo/experiments/exp6_context_ablation.py`.

- Xây 2 đồ thị gating: (i) đầy đủ `S_geo·(β·S_temp+γ·S_context)`; (ii) bỏ context `WeightParams(gamma=0.0)` → thực chất `S_geo·β·S_temp`.
- Với mỗi đồ thị: Louvain → đo ARI/NMI/đường kính, rồi `score_clusters` → lấy thứ hạng P.
- Báo cáo: ARI hai bên + **Kendall's τ giữa hai bảng xếp hạng P** (dùng `_tau_vs_baseline` từ exp5, so trên tập cụm chung / hoặc so theo cụm khớp không gian).
- Diễn giải trung thực theo kết quả τ (cao → S_context đóng góp ít cho *ranking*, chủ yếu giúp *gom cụm*; thấp → cần lập luận).
- Lưu `results/tables/exp6_context_ablation.json`.

### exp7 — Outcome metric cho equity (🔴 1.2)

File mới `demo/experiments/exp7_equity_outcome.py`.

- Định nghĩa metric vận hành: **thời gian mô phỏng đến nạn nhân yếu thế** dưới chính sách điều phối *tham lam theo thứ hạng P* với một (vài) đội ca nô tốc độ cố định, phục vụ lần lượt trọng tâm cụm theo thứ tự P giảm dần; cộng dồn quãng đường Haversine → thời gian đến từng cụm; "thời gian tới nạn nhân yếu thế" = trung bình có trọng số theo ΣV của cụm.
- So 3 chính sách ranking: (a) P đầy đủ (V nhân), (b) P không có V, (c) P có V dạng cộng.
- Kỳ vọng/khả năng: (a) giảm thời-gian-đến-yếu-thế so với (b),(c). Nếu KHÔNG giảm → báo cáo trung thực + đóng khung V_agg là *lựa chọn giá trị chuẩn tắc* (map vào nguyên tắc triage ưu tiên người dễ tổn thương), theo đúng đề xuất (b) của phản biện.
- Lưu `results/tables/exp7_equity_outcome.json`.

### exp8 — C_i như bộ phát hiện tin giả + kịch bản đối kháng (🔴 4.1)

File mới `demo/experiments/exp8_confidence_detector.py`.

- (i) **AUC/precision**: `roc_auc_score([is_fake],[1-confidence])` trên toàn dataset — C_i như "bộ phát hiện tin giả yếu". Báo cáo AUC.
- (ii) **Kịch bản đối kháng**: thêm ít nhất 2 tin giả tinh vi vào dataset thí nghiệm này (không đụng dataset chính): một *có ảnh*, một *có corroboration giả* (vài tin giả phối hợp cùng vùng/cửa sổ). Đo lại C_i của chúng + kiểm tra 1E/1F còn giữ được không.
- Diễn giải: nêu rõ giới hạn — heuristic C_i mạnh với tin giả *ngây thơ*, yếu với adversary phối hợp.
- Lưu `results/tables/exp8_confidence_detector.json`.
- **Lưu ý:** tự chứa việc sinh tin giả đối kháng *trong exp8* (không sửa `data/generate.py` để giữ dataset chính & mọi exp khác bất biến).

### exp9 — Độ đo phân biệt (🟠 2.2)

File mới `demo/experiments/exp9_discriminative_metric.py`.

- Giữ nguyên dataset. Thêm **một độ đo phân biệt hơn ARI** để tách các phương pháp đang cùng ~0.892. Ứng viên (chọn cái phân biệt tốt nhất, báo cáo ≥1):
  - **Đường kính cụm** đã có (nhưng là tautology) — không dùng làm chính.
  - **Số cụm tìm được vs 6 ground-truth "ốc đảo"** + **độ tinh khiết/homogeneity, completeness, V-measure** (sklearn) — các độ đo này phân biệt Louvain(27) vs HDBSCAN(11) vs Spectral rõ hơn ARI.
  - **ARI chỉ trên tập lõi khó** (bỏ narrative) nếu cần.
- Mục tiêu: cho thấy có độ đo mà các phương pháp KHÔNG cùng điểm → ARI bão hòa không phải bằng chứng duy nhất.
- Lưu `results/tables/exp9_discriminative_metric.json`.

### exp2b — Mở rộng độ nhạy (🟠 4.2, 4.3)

Sửa/ mở rộng `demo/experiments/exp2_sensitivity.py` (hoặc thêm exp2 quét bổ sung) + mở rộng exp5.

- exp2: thêm quét `τ_F, τ_E, β/γ, θ, k` (ít nhất τ_F,τ_E,β/γ) — báo cáo ARI/đường kính ổn định ra sao.
- exp5: thêm nhiễu loạn `s` và (quan trọng) **cấu trúc cụm**: đổi `σ_geo` làm cụm đổi → bảng xếp hạng còn ổn định? Báo cáo τ.
- Lưu bảng bổ sung (ví dụ `exp2_tauF_tauE.json`, `exp2_beta_gamma.json`, `exp5_structural_stability.json`).

### 4.4 — Kiểm/tinh chỉnh Spectral (🟡 nhưng rẻ)

- Trong `pipeline/baselines.py`: thử `assign_labels="kmeans"` thay `"discretize"`, xác nhận affinity đúng. Chạy vài K. Nếu vẫn thấp → giữ nguyên + thêm câu "đã thử tối ưu" trong bài. Ghi kết quả vào exp4 hoặc note.

### Cập nhật wiring

- `run_all.py`: thêm exp6, exp7, exp8, exp9 (và exp2 mở rộng) vào chuỗi.
- `make_figures.py`: nếu muốn hình cho exp7 (outcome) hoặc exp9 — thêm nếu rẻ; không bắt buộc.
- Chạy lại toàn bộ suite, thu số liệu mới từ JSON.

---

## PHẦN B — Sửa văn bản (3 artifact đồng bộ)

Áp cho **cả 3**: `paper/main.tex`, `resource/BaiBao_NoiDung.md`, `resource/PaperV2.md` (PaperV2 chưa đọc kỹ — sẽ đọc phần liên quan trước khi sửa).

### 🔴 2.1 — Re-frame "100km→0,30km"

- Mọi chỗ (Abstract, §5.2/1A, §8/Conclusion): đổi sang "gating đạt cụm gắn kết không gian (đường kính 0,30 km) **mà không hy sinh** ARI (0,892)". Bỏ ngôn ngữ "phát hiện". (LaTeX đã gần đúng — rà lại Abstract/Conclusion.)

### 🔴 1.1 / 1.2 / 4.1 — Thêm nội dung thí nghiệm mới

- §5 (Experiments): thêm tiểu mục cho exp6 (ablation circularity), exp7 (equity outcome), exp8 (C_i detector + adversarial), exp9 (discriminative metric).
- §4.4 ghi chú circularity: thay "mới thừa nhận bằng lời" bằng dẫn số liệu exp6 (τ).
- Khe hở 2 / §5 (equity): dẫn exp7; nếu outcome không cải thiện, đóng khung chuẩn tắc rõ ràng.
- §7.1 Threats / §5: tách bạch "kiểm chứng *cơ chế công thức*" khỏi "*năng lực trích xuất C_i/V_i*"; thêm giới hạn adversarial từ exp8.

### 🟠 1.3 — Trần khuếch đại μ

- §4.4: giới thiệu `V_agg = 1+(μ−1)·tanh(·)`, μ∈[1,2] để ban chỉ huy điều chỉnh mức khuếch đại tối đa; nêu trade-off số-đông vs yếu-thế. (Chỉ sửa văn bản + có thể thêm tham số vào `PriorityParams` với mặc định μ=2 để không đổi số hiện có.)

### 🟠 2.2 — ARI bão hòa

- §5: thêm thảo luận + dẫn exp9 (độ đo phân biệt) → thừa nhận ARI bão hòa, bổ sung độ đo phân biệt.

### 🟠 3.1 — Định nghĩa vận hành V_i

- §4.1: thêm **bảng trọng số nhãn** đề xuất (sơ sinh/già/mang thai/khuyết tật → trọng số) và ánh xạ tới 4 mức {0;1;1,5;2} trong dataset; nêu rõ thực nghiệm giả định V_i cho sẵn (ground-truth), trích V_i từ text là hướng mở rộng.

### 🟠 3.2 — Chế độ N_max

- §4.4 + §5.1: nêu rõ thực nghiệm dùng **mốc động** (đã xác nhận trong code: `n_max = max` tổng dân số gated của cụm hiện tại); thêm câu cảnh báo diễn giải.

### 🟠 4.2 / 4.3 — Tham số & robustness

- §5.1/§5.3: phân loại tham số "đặt theo miền" vs "tinh chỉnh"; dẫn quét độ nhạy mở rộng (exp2b) + robustness cấu trúc (exp5 mở rộng).

### 🟡 (rẻ, làm kèm)

- 2.3: hạ giọng claim MB→KB / mili-giây thành "lập luận thiết kế dựa trên tài liệu, chưa đo trên prototype" (Abstract/§2.2/§6). Hoặc đo kích thước JSON metadata (rất rẻ) — sẽ đo `len(json)` của 1 event để có 1 con số thật.
- 2.4: đồng bộ PaperV2 dùng "quan sát được ~O(N log N)" như BaiBao/LaTeX.
- 3.3: đưa (r_corrob, Δt_corrob)=(400m,60ph) vào bảng tham số §5.1; bàn "độc lập" khi thiếu ID.
- 3.4: giải thích τ_F=0,25 vs τ_E=0,35 (hoặc đặt bằng nhau + đưa vào độ nhạy).
- 5.2: thống nhất làm tròn số (0,89 vs 0,892) — chọn 3 chữ số, hoặc ghi rõ abstract làm tròn.
- 5.3: cập nhật Phụ lục B trong BaiBao — đánh dấu mục đã xong.

---

## Thứ tự thực hiện

1. Viết & chạy exp6–exp9 + mở rộng exp2/exp5; cập nhật run_all.py; chạy full suite; thu JSON.
2. Rà Spectral config (4.4).
3. Đọc kỹ PaperV2.md phần cần sửa.
4. Sửa văn bản 3 artifact theo số liệu mới (🔴 → 🟠 → 🟡).
5. Biên dịch lại `paper/main.tex` (`pdflatex→bibtex→pdflatex×2`), xác nhận 0 lỗi ref.
6. Cập nhật memory (sửa đường dẫn demo/v2→demo; ghi các exp mới & kết luận thật).

## Rủi ro / lưu ý

- Kết quả exp mới **có thể không như kỳ vọng** (equity không cải thiện outcome; C_i AUC thấp). Cam kết **báo cáo trung thực** theo đúng tinh thần dự án; văn bản sẽ phản ánh số thật, không tô hồng.
- Không đụng dataset chính (seed=42) để mọi số hiện có bất biến; kịch bản đối kháng tự chứa trong exp8.
- Thêm tham số μ với mặc định =2 để không thay đổi các số P đã công bố.
