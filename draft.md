
# Kế hoạch sửa toàn bộ vấn đề phản biện — paper/ + demo/

Phạm vi đã chốt: sửa **cả code demo và bài báo**. Sinh lại dữ liệu để bỏ trần ARI.
Hình mới: TikZ cho sơ đồ kiến trúc, Python/matplotlib cho hình có dữ liệu.

**Hệ quả bao trùm:** sinh lại dataset làm **mọi con số trong main.tex thay đổi**.
Vì vậy trình tự bắt buộc là: sửa code → chạy lại toàn bộ → mới cập nhật bài báo
theo JSON mới. Không viết số vào bài trước khi có kết quả thật.

---

## Giai đoạn 1 — Sửa bộ dữ liệu (gốc của vấn đề 1.1, 2.4, 2.3)

### 1.1 `demo/data/generate.py` — tách nhãn GT khỏi tâm đảo

Hiện `narrative_scenarios()` hard-code toạ độ **đúng bằng** tâm 6 đảo lõi (đã xác
minh: 6/6 nhóm lệch < 1 m), nên nhãn 100–105 buộc phải bị gộp vào nhãn 0–5.

Sửa: đặt mỗi nhóm kịch bản ở một **vệ tinh riêng**, cách tâm đảo chủ
`SAT_OFFSET_M = 3000` m (≫ σ_geo = 700 m, nên gating tách được; vẫn cùng vùng địa
lý nên kịch bản giữ nguyên ý nghĩa vận hành). Giữ nguyên mọi thuộc tính F/E/N/V và
ý nghĩa từng kịch bản:

- S1_A / S1_B: giữ khoảng cách ~103 km (chỉ dịch cả hai ra vệ tinh) → vẫn test gating.
- S2 (5 điểm, V=2.0): vệ tinh của Đông Hà, spread nội bộ ~150 m.
- S3 (4 điểm thật + S3_FAKE): vệ tinh của Đà Nẵng; S3_FAKE giữ nguyên vị trí cô lập.
- S4A (10 điểm, F=0.35) / S4B (3 điểm, F=0.97): vệ tinh của Phú Vang / Vĩnh Linh.

Thêm assert trong `build_dataset`: mọi nhóm gt ≥ 100 phải cách **mọi** tâm đảo

> 2000 m. Nếu vi phạm → raise. Đây là bảo hiểm để lỗi không tái xuất hiện.

### 1.2 Phá cộng tuyến ngữ cảnh ↔ địa lý (vấn đề 2.4)

Hiện mỗi đảo có `base_flood ~ U(0.35,0.9)` với σ mỗi sự kiện chỉ 0.08 → F gần như
là hàm của nhãn đảo, nên τ_F/τ_E hoàn toàn vô cảm.

Sửa hai việc:

- Tăng σ nội đảo: `flood_sigma 0.08 → 0.16`, `urg_sigma 0.10 → 0.18` (chồng lấp
  giữa các đảo, ngữ cảnh không còn suy ra được đảo).
- Thêm **S5 — kịch bản ngữ cảnh trái ngược**: hai nhóm 6 điểm nằm **cạnh nhau**
  (cách 900 m, cùng cửa sổ thời gian) nhưng F đối lập (0.30 vs 0.95), nhãn
  gt = 106 / 107. Đây là ca duy nhất mà S_context *phải* làm việc — nếu bỏ γ thì
  hai nhóm này gộp lại. Nó biến exp2 (τ_F/τ_E) và exp6 (ablation γ) từ "vô cảm"
  thành có tín hiệu thật.

Kết quả: 14 nhãn GT (0–5, 100–107).

### 1.3 Tăng công suất thống kê cho C_i (vấn đề 2.3)

`n_noise 20 → 60`, tỉ lệ fake 40% → ~24 fake. Trong số fake: **~40% có ảnh**
(hiện 1/6) để C_i không còn là bản sao của cờ `has_image`. Dự kiến AUC sẽ **giảm**
so với 0.9651 — đó là kết quả trung thực hơn, và AP sẽ có ý nghĩa với ~24 dương tính.

### 1.4 Tham số hoá seed để chạy đa hạt giống (vấn đề 2.6)

- `narrative_scenarios(rng)`: nhận rng, thêm jitter ±40 m cho từng điểm kịch bản
  (hiện hoàn toàn hard-code nên không thể đo bất định của chính các nhóm quan trọng).
- `build_dataset(seed=42)` và thêm `make_events(seed)` trả về list Event **trong bộ
  nhớ**, không ghi file — để các exp đa seed lặp không đụng `dataset.json`.
- Sửa metadata: `n_gt_clusters` tính động từ nhãn thực tế (hiện hard-code 6, sai).
- Sửa docstring vùng: 16–17°N → 15.7–17.1°N (khớp metadata và bài báo).

---

## Giai đoạn 2 — Sửa pipeline (vấn đề 1.2, 1.3)

### 2.1 `demo/pipeline/weighting.py` — bỏ α straw man

Hiện `alpha: float = 0.34` cứng trong chữ ký, trong khi β = γ = 0.5 → dạng cộng bị
hạ trọng số địa lý. Sửa:

- Thêm `alpha: float = 0.5` vào `WeightParams` (`config.py`), mặc định **đối xứng**
  với β, γ.
- `edge_weight_additive` đọc `p.alpha`; `build_weight_matrix` nhận `alpha_override`
  để exp1A quét được α.
- Đồng thời thêm biến thể **cộng chuẩn hoá** `α+β+γ = 1` (α=β=γ=1/3) làm baseline
  công bằng nhất.

### 2.2 `demo/pipeline/metrics.py` — đường kính không so số 0

Hiện singleton được gán `diameters.append(0.0)` rồi lấy trung bình không trọng số →
27 cụm nhiều singleton "thắng" 6 cụm không singleton một cách giả tạo.

`geographic_spread` trả thêm:

- `mean_diameter_km_multi` — chỉ tính cụm có ≥ 2 thành viên (**số dùng để so sánh**)
- `mean_diameter_km_weighted` — trung bình có trọng số theo số điểm
- `n_singletons`, `mean_diameter_km` (giữ để tương thích, đánh dấu là chỉ tham khảo)

Mọi exp so sánh chuyển sang dùng `max_diameter_km` + `mean_diameter_km_multi`.

### 2.3 `demo/pipeline/clustering.py` — không ẩn singleton

`count_disconnected_communities` hiện bỏ qua cụm ≤ 1 phần tử. Thêm trả về
`n_singletons` và `n_evaluated` để kết luận "zero badly-connected" nêu rõ mẫu số.

### 2.4 `demo/pipeline/priority.py` — công bố mốc chuẩn hoá

`n_max = max(n_totals.values())` luôn dùng mốc **động** (cụm lớn nhất luôn Ñ = 1.0),
bài báo không nói dùng mốc nào. Thêm tham số `n_ref: float | None = None`
(None = động, số = mốc tĩnh), ghi rõ mặc định vào output JSON để bài báo trích được.

---

## Giai đoạn 3 — Sửa và bổ sung thí nghiệm

### 3.1 Sửa các exp hiện có

| File                              | Việc                                                                                                                                                                                                                                                                                         |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `exp1_formula_validation.py`    | 1A: quét α ∈ {0.34, 0.5, 1.0, 1/3-chuẩn-hoá} × {gating}; báo cả 4. 1C: thêm cột chuẩn hoá để P_add/P_mult so được (hiện 1.66 vs 1.36 đọc ngược luận điểm). 1G: giữ phân rã ARI làm**bằng chứng đã sửa** (kỳ vọng colocated = 0, ARI toàn tập ↑). |
| `exp2_sensitivity.py`           | Thêm cột`mean_diam_multi`, `max_diam`; τ_F/τ_E giờ có S5 nên kỳ vọng không còn phẳng.                                                                                                                                                                                         |
| `exp4_baselines.py`             | Bỏ dòng`Spectral (K=n_gt true GT)` **hoặc** đưa vào bảng bài báo — chọn đưa vào bảng (thông tin thật, không nên ẩn). Thêm cột `mean_diam_multi`.                                                                                                              |
| `exp7_equity_outcome.py`        | Giữ code (đã trung thực), nhưng bổ sung metric**thứ ba trung lập**: thời-gian-đến trọng số ΣV·1[F>0.7] (không dùng dạng nhân làm hàm mục tiêu). Ghi rõ trong output rằng metric ΣV thuần **ủng hộ dạng cộng**.                                     |
| `exp8_confidence_detector.py`   | Thêm**AP** vào output đã có (đang tính nhưng bài không trích) + **bootstrap 95% CI** cho AUC và AP (1000 lần lấy mẫu lại).                                                                                                                                        |
| `exp9_discriminative_metric.py` | Chỉ cập nhật số sau khi sinh lại dữ liệu.                                                                                                                                                                                                                                              |

### 3.2 Hai thí nghiệm mới

- **`exp11_scaling.py`** — đo thời gian chạy thật: n ∈ {285, 1000, 3000, 6000,
  10000} (sinh bằng `make_events` với `n_per_cluster` tăng dần), tách thời gian
  `build_weight_matrix` / `sparsify` / `run_louvain`, khớp hệ số O(n²) và báo
  ms/sự kiện. Bài báo tuyên bố khả thi thời gian thực mà không có phép đo nào.
  Kèm bản vector-hoá `build_weight_matrix_vec` (numpy broadcast) để cho thấy
  O(n²) Python thuần chỉ là chi tiết cài đặt, không phải giới hạn thuật toán.
- **`exp12_multiseed.py`** — 20 seed dữ liệu × các số headline (ARI, NMI,
  completeness, mean_diam_multi, max_diam, modularity, ARI của 4 baseline chính),
  báo **mean ± std** và min/max. Đây là số sẽ vào abstract thay cho điểm đơn.

### 3.3 Cập nhật `run_all.py`

Thêm exp11, exp12 vào trình tự (13 bước → 15 bước), sửa lại banner đánh số.

---

## Giai đoạn 4 — Hình vẽ (vấn đề mục 3)

### 4.1 Ba hình mới

- **fig_arch (TikZ, vẽ trực tiếp trong main.tex)** — sơ đồ kiến trúc 4 tầng:
  thiết bị biên (MobileNetV3 + DistilBERT lượng tử hoá) → gói metadata < 1 KB qua
  mesh/LoRa → server dựng đồ thị có trọng số (θ, k-NN) → Louvain/Leiden → xếp hạng
  P(C_k) → điều phối. Đã xác minh `tikz.sty` và `pgfplots.sty` có sẵn trong
  TeX Live của máy, không cần cài thêm.
- **fig_map (Python)** — bản đồ vùng 15.7–17.1°N: 2 panel cạnh nhau, cùng dữ liệu,
  tô màu theo cụm — dạng cộng (gộp xuyên tỉnh) vs dạng gating (vùng tác chiến gọn).
  Đây là hình chứng minh luận điểm chính trực quan nhất và hiện đang thiếu.
- **fig_heatmap (Python)** — heatmap w_ij theo (Δd, Δt) cho hai dạng công thức,
  cùng thang màu; giải thích "gating" bằng một hình thay cho nhiều đoạn văn.

### 4.2 Dọn hình mật độ thấp

- Bỏ `fig2_tanh_saturation` (chỉ là đồ thị của công thức, đã có Bảng `tab:tanh`).
- Gộp `fig1` (2 cột) + `fig3` (2 cột) thành **một hình 2 panel** `fig_ablation`.
- Kết quả: vẫn 7 hình, nhưng có sơ đồ kiến trúc + bản đồ + heatmap thay cho 3 hình
  ít thông tin. Không tăng số trang.

Sửa `make_figures.py` tương ứng; hình mới đặt tên `figXX_*.png`, copy sang
`paper/figures/`.

---

## Giai đoạn 5 — Sửa bài báo `paper/main.tex`

### 5.1 Nội dung dở dang / treo (bắt buộc)

- **main.tex:300** — tham chiếu "Table's ``domain'' group" trỏ tới bảng không tồn
  tại. Sửa bằng cách **thêm thật** `tab:params` (bảng tham số 2 nhóm domain-set /
  tunable). Bảng này đồng thời xử lý luôn đoạn tràn lề 45.11 pt ở dòng 229–230.
- Đồng bộ `tab:baselines` với fig6 (thêm dòng Spectral K = số nhãn GT).
- Thêm citation cho dòng "Event detection (TF-IDF)" trong `tab:positioning`.
- Email liên hệ → email tổ chức (@ctu.edu.vn hoặc @student.ctu.edu.vn).

### 5.2 Sửa các tuyên bố (nội dung phản biện)

- **Abstract + Conclusion**: thay "100 km → 0.30 km" bằng **max diameter
  213.95 → 1.42 km** (số cùng đơn vị so sánh, và vẫn rất mạnh); thay điểm đơn ARI
  bằng **mean ± std trên 20 seed** từ exp12; nêu α của dạng cộng ngay tại chỗ so
  sánh; **thêm Agglomerative** vào danh sách baseline được nhắc.
- **Định vị lại đóng góp**: nói thẳng rằng Agglomerative hoà điểm ⇒ đóng góp là
  **ma trận trọng số gating**, không phải bản thân Louvain. Lập luận này mạnh và
  trung thực hơn hiện tại (mục 2.5 phản biện).
- **Exp1A**: trình bày quét α, nêu rõ kết luận đứng vững ở α nào.
- **Exp2**: định khung lại — "vô cảm ≠ bền vững". Nói rõ ARI đứng yên vì bị chặn
  bởi cấu trúc, còn tín hiệu thật nằm ở đường kính; sau khi thêm S5 thì τ_F/τ_E
  mới có ảnh hưởng đo được.
- **Exp3**: nêu mẫu số (số cụm ≥ 2 phần tử) khi nói "zero badly-connected".
- **Exp7**: định khung V_agg là **lựa chọn giá trị chuẩn tắc (triage)**, không phải
  tối ưu khách quan; nói rõ metric ΣV thuần *không* ủng hộ dạng nhân — đúng như
  docstring code đã tự nhận.
- **Exp8**: báo **AP + CI cạnh AUC**, nêu rõ n_fake; mô tả C_i đúng bản chất là
  **bộ phát hiện báo cáo cô lập**, đưa phần đối kháng lên trước.
- **Setup/Dataset**: viết lại theo dataset mới (14 nhãn, ~325 sự kiện, S5, khoảng
  cách vệ tinh 3 km, ~24 fake); **xoá** đoạn giải thích trần ARI do co-location
  (đã sửa gốc, không còn đúng).
- **Threats to Validity**: xoá mục "0.892 là trần by-construction" (đã sửa); bổ
  sung mục multi-seed đã làm; giữ và làm rõ hạn chế "một bộ dữ liệu tự sinh".
- **Discussion**: thêm 1 đoạn về exp11 (độ phức tạp + thời gian chạy thật), đồng
  thời tách đoạn "Cross-disciplinary impact" đang tràn lề 26.37 pt.
- Thêm mục **Reproducibility**: seed, phiên bản thư viện, lệnh `run_all.py`.

### 5.3 `paper/references.bib`

- `campello2013hdbscan`: `@article` → `@inproceedings` (trường `journal` đang là
  tên hội nghị).
- `macqueen1967some`: thêm publisher.
- Thay `isponre2009varcc` (2009) bằng nguồn gần đây cho phát biểu thời hiện tại về
  tần suất bão (IPCC AR6 hoặc báo cáo quốc gia mới) — giữ nguồn cũ nếu cần cho số
  liệu lịch sử, nhưng chuyển câu sang thời quá khứ/nêu năm.
- Thêm 1 citation cho event detection dùng TF-IDF.

### 5.4 Typesetting

Sau khi biên dịch, quét lại `main.log`. Mục tiêu: **0 overfull > 5 pt**. Các chỗ
nặng đã biết (229–230: 45.11 pt và 23.56 pt; 386–387: 26.37 pt và 10.09 pt;
110–111: 17.06 pt; underfull badness 2126 ở 59–63) được xử lý bằng chính các sửa
đổi cấu trúc ở 5.1/5.2, phần còn lại bằng ngắt dòng/`\sloppy` cục bộ.

---

## Giai đoạn 6 — Chạy lại và xác minh

1. `demo/.venv/bin/python run_all.py` — sinh lại dataset + 12 exp + hình + dashboard.
2. Kiểm tra bất biến: `n_colocated_narrative_groups == 0`; `ari_core_only == 1.0`;
   assert khoảng cách vệ tinh không raise.
3. `latexmk -pdf main.tex` trong `paper/` (đã xác minh có `pdflatex` + `bibtex`).
4. **Đối chiếu từng số**: lập checklist mọi con số trong main.tex ↔ JSON tương ứng
   trong `demo/results/tables/`. Không để lại số cũ.
5. Quét `main.log` cho overfull/underfull và cảnh báo tham chiếu treo
   (`LaTeX Warning: Reference`).
6. Ghi báo cáo `loop/loop9/` theo đúng dạng 8 vòng trước (review_report.md +
   resolution_plan.md) để giữ nhật ký phản biện liên tục.

---

## Rủi ro cần biết trước

- **Số sẽ xấu đi ở một số chỗ.** Sau khi sửa dữ liệu: ARI có thể lên (~0.95+, do bỏ
  trần) nhưng **AUC của C_i sẽ giảm** (fake có ảnh), và **khoảng cách gating vs
  cộng theo mean diameter sẽ hẹp lại** (bỏ số 0 của singleton). Đây là mục đích của
  việc sửa — số trung thực hơn, không phải số đẹp hơn. Tôi sẽ báo cáo đúng những gì
  chạy ra, kể cả khi ngược với bài báo hiện tại.
- **Nếu α = 0.5 làm dạng cộng tốt lên đáng kể**, luận điểm 1A phải viết yếu đi
  (gating tốt hơn ở đường kính lớn nhất, chứ không phải "cộng vô dụng"). Sẽ dựa
  vào số thật để quyết định câu chữ.
- Khối lượng: ~10 file code sửa, 2 file code mới, ~3 hình mới, main.tex sửa diện
  rộng. Thứ tự trên đảm bảo mỗi bước có thể kiểm tra được trước khi đi tiếp.

# Kế hoạch sửa toàn bộ vấn đề phản biện — paper/ + demo/

Phạm vi đã chốt: sửa **cả code demo và bài báo**. Sinh lại dữ liệu để bỏ trần ARI.
Hình mới: TikZ cho sơ đồ kiến trúc, Python/matplotlib cho hình có dữ liệu.

**Hệ quả bao trùm:** sinh lại dataset làm **mọi con số trong main.tex thay đổi**.
Vì vậy trình tự bắt buộc là: sửa code → chạy lại toàn bộ → mới cập nhật bài báo
theo JSON mới. Không viết số vào bài trước khi có kết quả thật.

---

## Giai đoạn 1 — Sửa bộ dữ liệu (gốc của vấn đề 1.1, 2.4, 2.3)

### 1.1 `demo/data/generate.py` — tách nhãn GT khỏi tâm đảo

Hiện `narrative_scenarios()` hard-code toạ độ **đúng bằng** tâm 6 đảo lõi (đã xác
minh: 6/6 nhóm lệch < 1 m), nên nhãn 100–105 buộc phải bị gộp vào nhãn 0–5.

Sửa: đặt mỗi nhóm kịch bản ở một **vệ tinh riêng**, cách tâm đảo chủ
`SAT_OFFSET_M = 3000` m (≫ σ_geo = 700 m, nên gating tách được; vẫn cùng vùng địa
lý nên kịch bản giữ nguyên ý nghĩa vận hành). Giữ nguyên mọi thuộc tính F/E/N/V và
ý nghĩa từng kịch bản:

- S1_A / S1_B: giữ khoảng cách ~103 km (chỉ dịch cả hai ra vệ tinh) → vẫn test gating.
- S2 (5 điểm, V=2.0): vệ tinh của Đông Hà, spread nội bộ ~150 m.
- S3 (4 điểm thật + S3_FAKE): vệ tinh của Đà Nẵng; S3_FAKE giữ nguyên vị trí cô lập.
- S4A (10 điểm, F=0.35) / S4B (3 điểm, F=0.97): vệ tinh của Phú Vang / Vĩnh Linh.

Thêm assert trong `build_dataset`: mọi nhóm gt ≥ 100 phải cách **mọi** tâm đảo

> 2000 m. Nếu vi phạm → raise. Đây là bảo hiểm để lỗi không tái xuất hiện.

### 1.2 Phá cộng tuyến ngữ cảnh ↔ địa lý (vấn đề 2.4)

Hiện mỗi đảo có `base_flood ~ U(0.35,0.9)` với σ mỗi sự kiện chỉ 0.08 → F gần như
là hàm của nhãn đảo, nên τ_F/τ_E hoàn toàn vô cảm.

Sửa hai việc:

- Tăng σ nội đảo: `flood_sigma 0.08 → 0.16`, `urg_sigma 0.10 → 0.18` (chồng lấp
  giữa các đảo, ngữ cảnh không còn suy ra được đảo).
- Thêm **S5 — kịch bản ngữ cảnh trái ngược**: hai nhóm 6 điểm nằm **cạnh nhau**
  (cách 900 m, cùng cửa sổ thời gian) nhưng F đối lập (0.30 vs 0.95), nhãn
  gt = 106 / 107. Đây là ca duy nhất mà S_context *phải* làm việc — nếu bỏ γ thì
  hai nhóm này gộp lại. Nó biến exp2 (τ_F/τ_E) và exp6 (ablation γ) từ "vô cảm"
  thành có tín hiệu thật.

Kết quả: 14 nhãn GT (0–5, 100–107).

### 1.3 Tăng công suất thống kê cho C_i (vấn đề 2.3)

`n_noise 20 → 60`, tỉ lệ fake 40% → ~24 fake. Trong số fake: **~40% có ảnh**
(hiện 1/6) để C_i không còn là bản sao của cờ `has_image`. Dự kiến AUC sẽ **giảm**
so với 0.9651 — đó là kết quả trung thực hơn, và AP sẽ có ý nghĩa với ~24 dương tính.

### 1.4 Tham số hoá seed để chạy đa hạt giống (vấn đề 2.6)

- `narrative_scenarios(rng)`: nhận rng, thêm jitter ±40 m cho từng điểm kịch bản
  (hiện hoàn toàn hard-code nên không thể đo bất định của chính các nhóm quan trọng).
- `build_dataset(seed=42)` và thêm `make_events(seed)` trả về list Event **trong bộ
  nhớ**, không ghi file — để các exp đa seed lặp không đụng `dataset.json`.
- Sửa metadata: `n_gt_clusters` tính động từ nhãn thực tế (hiện hard-code 6, sai).
- Sửa docstring vùng: 16–17°N → 15.7–17.1°N (khớp metadata và bài báo).

---

## Giai đoạn 2 — Sửa pipeline (vấn đề 1.2, 1.3)

### 2.1 `demo/pipeline/weighting.py` — bỏ α straw man

Hiện `alpha: float = 0.34` cứng trong chữ ký, trong khi β = γ = 0.5 → dạng cộng bị
hạ trọng số địa lý. Sửa:

- Thêm `alpha: float = 0.5` vào `WeightParams` (`config.py`), mặc định **đối xứng**
  với β, γ.
- `edge_weight_additive` đọc `p.alpha`; `build_weight_matrix` nhận `alpha_override`
  để exp1A quét được α.
- Đồng thời thêm biến thể **cộng chuẩn hoá** `α+β+γ = 1` (α=β=γ=1/3) làm baseline
  công bằng nhất.

### 2.2 `demo/pipeline/metrics.py` — đường kính không so số 0

Hiện singleton được gán `diameters.append(0.0)` rồi lấy trung bình không trọng số →
27 cụm nhiều singleton "thắng" 6 cụm không singleton một cách giả tạo.

`geographic_spread` trả thêm:

- `mean_diameter_km_multi` — chỉ tính cụm có ≥ 2 thành viên (**số dùng để so sánh**)
- `mean_diameter_km_weighted` — trung bình có trọng số theo số điểm
- `n_singletons`, `mean_diameter_km` (giữ để tương thích, đánh dấu là chỉ tham khảo)

Mọi exp so sánh chuyển sang dùng `max_diameter_km` + `mean_diameter_km_multi`.

### 2.3 `demo/pipeline/clustering.py` — không ẩn singleton

`count_disconnected_communities` hiện bỏ qua cụm ≤ 1 phần tử. Thêm trả về
`n_singletons` và `n_evaluated` để kết luận "zero badly-connected" nêu rõ mẫu số.

### 2.4 `demo/pipeline/priority.py` — công bố mốc chuẩn hoá

`n_max = max(n_totals.values())` luôn dùng mốc **động** (cụm lớn nhất luôn Ñ = 1.0),
bài báo không nói dùng mốc nào. Thêm tham số `n_ref: float | None = None`
(None = động, số = mốc tĩnh), ghi rõ mặc định vào output JSON để bài báo trích được.

---

## Giai đoạn 3 — Sửa và bổ sung thí nghiệm

### 3.1 Sửa các exp hiện có

| File                              | Việc                                                                                                                                                                                                                                                                                         |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `exp1_formula_validation.py`    | 1A: quét α ∈ {0.34, 0.5, 1.0, 1/3-chuẩn-hoá} × {gating}; báo cả 4. 1C: thêm cột chuẩn hoá để P_add/P_mult so được (hiện 1.66 vs 1.36 đọc ngược luận điểm). 1G: giữ phân rã ARI làm**bằng chứng đã sửa** (kỳ vọng colocated = 0, ARI toàn tập ↑). |
| `exp2_sensitivity.py`           | Thêm cột`mean_diam_multi`, `max_diam`; τ_F/τ_E giờ có S5 nên kỳ vọng không còn phẳng.                                                                                                                                                                                         |
| `exp4_baselines.py`             | Bỏ dòng`Spectral (K=n_gt true GT)` **hoặc** đưa vào bảng bài báo — chọn đưa vào bảng (thông tin thật, không nên ẩn). Thêm cột `mean_diam_multi`.                                                                                                              |
| `exp7_equity_outcome.py`        | Giữ code (đã trung thực), nhưng bổ sung metric**thứ ba trung lập**: thời-gian-đến trọng số ΣV·1[F>0.7] (không dùng dạng nhân làm hàm mục tiêu). Ghi rõ trong output rằng metric ΣV thuần **ủng hộ dạng cộng**.                                     |
| `exp8_confidence_detector.py`   | Thêm**AP** vào output đã có (đang tính nhưng bài không trích) + **bootstrap 95% CI** cho AUC và AP (1000 lần lấy mẫu lại).                                                                                                                                        |
| `exp9_discriminative_metric.py` | Chỉ cập nhật số sau khi sinh lại dữ liệu.                                                                                                                                                                                                                                              |

### 3.2 Hai thí nghiệm mới

- **`exp11_scaling.py`** — đo thời gian chạy thật: n ∈ {285, 1000, 3000, 6000,
  10000} (sinh bằng `make_events` với `n_per_cluster` tăng dần), tách thời gian
  `build_weight_matrix` / `sparsify` / `run_louvain`, khớp hệ số O(n²) và báo
  ms/sự kiện. Bài báo tuyên bố khả thi thời gian thực mà không có phép đo nào.
  Kèm bản vector-hoá `build_weight_matrix_vec` (numpy broadcast) để cho thấy
  O(n²) Python thuần chỉ là chi tiết cài đặt, không phải giới hạn thuật toán.
- **`exp12_multiseed.py`** — 20 seed dữ liệu × các số headline (ARI, NMI,
  completeness, mean_diam_multi, max_diam, modularity, ARI của 4 baseline chính),
  báo **mean ± std** và min/max. Đây là số sẽ vào abstract thay cho điểm đơn.

### 3.3 Cập nhật `run_all.py`

Thêm exp11, exp12 vào trình tự (13 bước → 15 bước), sửa lại banner đánh số.

---

## Giai đoạn 4 — Hình vẽ (vấn đề mục 3)

### 4.1 Ba hình mới

- **fig_arch (TikZ, vẽ trực tiếp trong main.tex)** — sơ đồ kiến trúc 4 tầng:
  thiết bị biên (MobileNetV3 + DistilBERT lượng tử hoá) → gói metadata < 1 KB qua
  mesh/LoRa → server dựng đồ thị có trọng số (θ, k-NN) → Louvain/Leiden → xếp hạng
  P(C_k) → điều phối. Đã xác minh `tikz.sty` và `pgfplots.sty` có sẵn trong
  TeX Live của máy, không cần cài thêm.
- **fig_map (Python)** — bản đồ vùng 15.7–17.1°N: 2 panel cạnh nhau, cùng dữ liệu,
  tô màu theo cụm — dạng cộng (gộp xuyên tỉnh) vs dạng gating (vùng tác chiến gọn).
  Đây là hình chứng minh luận điểm chính trực quan nhất và hiện đang thiếu.
- **fig_heatmap (Python)** — heatmap w_ij theo (Δd, Δt) cho hai dạng công thức,
  cùng thang màu; giải thích "gating" bằng một hình thay cho nhiều đoạn văn.

### 4.2 Dọn hình mật độ thấp

- Bỏ `fig2_tanh_saturation` (chỉ là đồ thị của công thức, đã có Bảng `tab:tanh`).
- Gộp `fig1` (2 cột) + `fig3` (2 cột) thành **một hình 2 panel** `fig_ablation`.
- Kết quả: vẫn 7 hình, nhưng có sơ đồ kiến trúc + bản đồ + heatmap thay cho 3 hình
  ít thông tin. Không tăng số trang.

Sửa `make_figures.py` tương ứng; hình mới đặt tên `figXX_*.png`, copy sang
`paper/figures/`.

---

## Giai đoạn 5 — Sửa bài báo `paper/main.tex`

### 5.1 Nội dung dở dang / treo (bắt buộc)

- **main.tex:300** — tham chiếu "Table's ``domain'' group" trỏ tới bảng không tồn
  tại. Sửa bằng cách **thêm thật** `tab:params` (bảng tham số 2 nhóm domain-set /
  tunable). Bảng này đồng thời xử lý luôn đoạn tràn lề 45.11 pt ở dòng 229–230.
- Đồng bộ `tab:baselines` với fig6 (thêm dòng Spectral K = số nhãn GT).
- Thêm citation cho dòng "Event detection (TF-IDF)" trong `tab:positioning`.
- Email liên hệ → email tổ chức (@ctu.edu.vn hoặc @student.ctu.edu.vn).

### 5.2 Sửa các tuyên bố (nội dung phản biện)

- **Abstract + Conclusion**: thay "100 km → 0.30 km" bằng **max diameter
  213.95 → 1.42 km** (số cùng đơn vị so sánh, và vẫn rất mạnh); thay điểm đơn ARI
  bằng **mean ± std trên 20 seed** từ exp12; nêu α của dạng cộng ngay tại chỗ so
  sánh; **thêm Agglomerative** vào danh sách baseline được nhắc.
- **Định vị lại đóng góp**: nói thẳng rằng Agglomerative hoà điểm ⇒ đóng góp là
  **ma trận trọng số gating**, không phải bản thân Louvain. Lập luận này mạnh và
  trung thực hơn hiện tại (mục 2.5 phản biện).
- **Exp1A**: trình bày quét α, nêu rõ kết luận đứng vững ở α nào.
- **Exp2**: định khung lại — "vô cảm ≠ bền vững". Nói rõ ARI đứng yên vì bị chặn
  bởi cấu trúc, còn tín hiệu thật nằm ở đường kính; sau khi thêm S5 thì τ_F/τ_E
  mới có ảnh hưởng đo được.
- **Exp3**: nêu mẫu số (số cụm ≥ 2 phần tử) khi nói "zero badly-connected".
- **Exp7**: định khung V_agg là **lựa chọn giá trị chuẩn tắc (triage)**, không phải
  tối ưu khách quan; nói rõ metric ΣV thuần *không* ủng hộ dạng nhân — đúng như
  docstring code đã tự nhận.
- **Exp8**: báo **AP + CI cạnh AUC**, nêu rõ n_fake; mô tả C_i đúng bản chất là
  **bộ phát hiện báo cáo cô lập**, đưa phần đối kháng lên trước.
- **Setup/Dataset**: viết lại theo dataset mới (14 nhãn, ~325 sự kiện, S5, khoảng
  cách vệ tinh 3 km, ~24 fake); **xoá** đoạn giải thích trần ARI do co-location
  (đã sửa gốc, không còn đúng).
- **Threats to Validity**: xoá mục "0.892 là trần by-construction" (đã sửa); bổ
  sung mục multi-seed đã làm; giữ và làm rõ hạn chế "một bộ dữ liệu tự sinh".
- **Discussion**: thêm 1 đoạn về exp11 (độ phức tạp + thời gian chạy thật), đồng
  thời tách đoạn "Cross-disciplinary impact" đang tràn lề 26.37 pt.
- Thêm mục **Reproducibility**: seed, phiên bản thư viện, lệnh `run_all.py`.

### 5.3 `paper/references.bib`

- `campello2013hdbscan`: `@article` → `@inproceedings` (trường `journal` đang là
  tên hội nghị).
- `macqueen1967some`: thêm publisher.
- Thay `isponre2009varcc` (2009) bằng nguồn gần đây cho phát biểu thời hiện tại về
  tần suất bão (IPCC AR6 hoặc báo cáo quốc gia mới) — giữ nguồn cũ nếu cần cho số
  liệu lịch sử, nhưng chuyển câu sang thời quá khứ/nêu năm.
- Thêm 1 citation cho event detection dùng TF-IDF.

### 5.4 Typesetting

Sau khi biên dịch, quét lại `main.log`. Mục tiêu: **0 overfull > 5 pt**. Các chỗ
nặng đã biết (229–230: 45.11 pt và 23.56 pt; 386–387: 26.37 pt và 10.09 pt;
110–111: 17.06 pt; underfull badness 2126 ở 59–63) được xử lý bằng chính các sửa
đổi cấu trúc ở 5.1/5.2, phần còn lại bằng ngắt dòng/`\sloppy` cục bộ.

---

## Giai đoạn 6 — Chạy lại và xác minh

1. `demo/.venv/bin/python run_all.py` — sinh lại dataset + 12 exp + hình + dashboard.
2. Kiểm tra bất biến: `n_colocated_narrative_groups == 0`; `ari_core_only == 1.0`;
   assert khoảng cách vệ tinh không raise.
3. `latexmk -pdf main.tex` trong `paper/` (đã xác minh có `pdflatex` + `bibtex`).
4. **Đối chiếu từng số**: lập checklist mọi con số trong main.tex ↔ JSON tương ứng
   trong `demo/results/tables/`. Không để lại số cũ.
5. Quét `main.log` cho overfull/underfull và cảnh báo tham chiếu treo
   (`LaTeX Warning: Reference`).
6. Ghi báo cáo `loop/loop9/` theo đúng dạng 8 vòng trước (review_report.md +
   resolution_plan.md) để giữ nhật ký phản biện liên tục.

---

## Rủi ro cần biết trước

- **Số sẽ xấu đi ở một số chỗ.** Sau khi sửa dữ liệu: ARI có thể lên (~0.95+, do bỏ
  trần) nhưng **AUC của C_i sẽ giảm** (fake có ảnh), và **khoảng cách gating vs
  cộng theo mean diameter sẽ hẹp lại** (bỏ số 0 của singleton). Đây là mục đích của
  việc sửa — số trung thực hơn, không phải số đẹp hơn. Tôi sẽ báo cáo đúng những gì
  chạy ra, kể cả khi ngược với bài báo hiện tại.
- **Nếu α = 0.5 làm dạng cộng tốt lên đáng kể**, luận điểm 1A phải viết yếu đi
  (gating tốt hơn ở đường kính lớn nhất, chứ không phải "cộng vô dụng"). Sẽ dựa
  vào số thật để quyết định câu chữ.
- Khối lượng: ~10 file code sửa, 2 file code mới, ~3 hình mới, main.tex sửa diện
  rộng. Thứ tự trên đảm bảo mỗi bước có thể kiểm tra được trước khi đi tiếp.
