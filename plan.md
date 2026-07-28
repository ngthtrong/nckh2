# Kế hoạch khắc phục toàn bộ phản biện vòng 17 — `paper/` + `demo/`

Nguồn: bản phản biện trong `draft.md` (10 mục + 3 việc bắt buộc ở cuối).
Trạng thái đối chiếu: `paper/main.tex` (641 dòng), `demo/` (13 thí nghiệm, 7 hình,
~30 bảng JSON). Kế hoạch cũ ở `draft.md:475-720` đã thực thi xong (dataset S5 +
vệ tinh + `n_noise=60`, Thí nghiệm 11/12/13, Bảng tham số) — **không lặp lại**.
Kế hoạch này chỉ giải quyết các vấn đề vòng mới.

## Trạng thái thực thi — cập nhật 28/07/2026

| Pha | Trạng thái | Kết quả kiểm chứng |
|---|---|---|
| P0 — bổ đề và thu hồi tuyên bố cũ | **Hoàn tất** | Bổ đề định vị và chứng minh đã có trong bài; bỏ tuyên bố cửa sổ `51×`. |
| P1 — thiết kế lại dữ liệu | **Hoàn tất phần chính** | Dataset v3 có 485 báo cáo, 13 sự kiện thật, ba cặp chồng lấn không gian, một cặp chồng vị trí khác thời gian, mật độ/spread không đều và tin giả trộn vào vùng sự kiện. Cả 5 cửa chặn độ khó đều đạt. |
| P1.5 — sanity check dữ liệu thật | **Chưa thực hiện, hạng mục phụ** | Workspace không có tập báo cáo lũ thật có đồng thời tọa độ và thời gian; giới hạn này đã được nêu trong bài. |
| P2 — sửa pipeline và quy ước đo | **Hoàn tất** | Thống nhất hình học trên cụm có nhãn, `N_ref=500` tĩnh và bị chặn, CI/bootstrap + Wilcoxon, kiểm tra `C_i` có điều kiện. |
| P3 — chạy lại thí nghiệm | **Hoàn tất** | `demo/run_all.py` chạy sạch 17/17 bước; các bảng JSON và 8 hình đã tái sinh. |
| P4 — văn liệu và định vị đóng góp | **Hoàn tất** | Bổ sung product/bilateral kernel, spatially constrained clustering và equity; dạng cộng được mô tả đúng là baseline tự dựng. |
| P5 — viết lại bài | **Hoàn tất phần có dữ liệu** | Tiêu đề/abstract/contributions đã viết lại; Edge AI hạ thành kiến trúc chưa đánh giá; PDF LNCS dài 12 trang. Email liên hệ đã thay bằng địa chỉ thật tìm thấy trong tài nguyên dự án. |
| P6 — xác minh | **Hoàn tất với một thay thế công cụ** | 8/8 hình khớp checksum, không hình mồ côi; số liệu có bảng truy vết; XeLaTeX + BibTeX biên dịch sạch, 0 lỗi/0 float-too-large/0 overfull trên 5 pt/0 tham chiếu thiếu. Dùng XeLaTeX vì TeX cục bộ thiếu `t5enc.def` cho tiếng Việt khi chạy pdfLaTeX. |

Hai đầu vào không thể tự suy đoán vẫn để mở trước khi nộp: ORCID thật của sáu
tác giả và, nếu có, tập dữ liệu lũ thực cho P1.5. Nhật ký thực thi và bảng truy
vết nằm tại `loop/loop17/execution_report.md` và
`loop/loop17/traceability.md`.

## 0. Quyết định phạm vi (đã chốt với tác giả)

| Hạng mục | Quyết định | Ảnh hưởng tới kế hoạch |
|---|---|---|
| Edge AI (MobileNetV3 + DistilBERT) | Đã train trên Colab, kết quả bổ sung sau. Là **nội dung phụ** (dùng model có sẵn, không có đóng góp khoa học). | Rút khỏi tiêu đề/abstract/contribution; giữ ở mức kiến trúc + Mục riêng chờ số đo. Xem P5.4. |
| Dữ liệu | **Generator khó hơn là chính**, dữ liệu thật là phụ. | P1.1 là đường găng; P1.5 (dữ liệu thật) là hạng mục "nếu kịp". |
| Đích nhắm | Full paper LNCS 12–16 trang. | Phải giành lại một tuyên bố dương tính (P0 + P1 + P3); phải gộp thí nghiệm (P5.3). |

## 0.1. Kiểm chứng lại phản biện trước khi lập kế hoạch

Đã chạy lại trên chính code/dữ liệu trong `demo/`. Kết quả xác nhận **9/10 mục
là đúng**, nhưng có ba chi tiết lệch so với bản phản biện, và một trong ba làm
đổi cách sửa:

1. **Mục 1 đúng, nhưng thước đo thay thế mà reviewer đề xuất cũng không cứu được
   tuyên bố.** Reviewer gợi ý dùng "tỉ lệ cạnh giữ lại". Đo thực tế tại hai đầu
   cửa sổ dùng được:

   | Dạng | θ_lo → θ_hi | Tỉ lệ cạnh giữ lại |
   |---|---|---|
   | gating | 0.01 → 0.51 | 8.31% → 1.53% |
   | additive α=1.0 | 0.96 → 1.46 | 7.40% → 1.60% |

   Gần như trùng nhau. θ chuẩn hoá theo `w_max` cho lợi thế **2×** (0.506 vs
   0.251), độ rộng tuyệt đối cho **1×**. Nghĩa là: không có đại lượng thực nghiệm
   nào biến "cửa sổ rộng hơn" thành một đóng góp. **Đường duy nhất còn lại là
   mệnh đề giải tích (P0.1)** — đúng như việc thứ 2 mà reviewer yêu cầu.

2. **Mục 10, cảnh báo LaTeX: sai với `main.log` hiện tại.** `grep -c Underfull`
   = **0**. Thực tế đang có 5 `Overfull \hbox` (dòng 39–40, 49–50, 225–226,
   262–263, 272–273) và **`Float too large for page by 104.75pt` ở dòng 86** —
   lỗi float nặng hơn overfull, phải sửa. Sửa theo hiện trạng log, không theo
   bản phản biện.

3. **Mục 10, hai hình:** `fig2_map.png` và `fig3_heatmap.png` **vẫn còn** trong
   `demo/results/figures/` nhưng **không có** trong `paper/figures/` và không
   được `\includegraphics` ở đâu trong `main.tex`. Đúng là bài đang thiếu hình
   phân bố dữ liệu — nhưng file chưa mất, chỉ cần đưa lại vào bài (P5.5).

Các con số dùng làm mốc trong kế hoạch này (đã đo lại, không lấy từ bài):

```
C_i:  AUC biên = 0.9176 | AP = 0.3159 (23 fake / 341)
      AUC(-n_corrob) một mình = 0.9355   ← cao hơn cả C_i
      mean n_corrob: fake 0.00 | thật-trong-đảo 14.84 | thật-rải-rác 0.00
      chỉ trên 61 điểm rải rác (23 fake vs 38 thật):
          AUC = 0.4319 | AP = 0.3495 vs baseline 0.3770   ← kém đoán bừa
      has_image một mình: AUC = 0.5675
HDBSCAN 20 cụm = 14 cụm chứa nhãn (TB 6.46 km, max 81.2, 13/14 < 1.5 km)
               + 6 cụm toàn nhiễu (TB 147.22 km)  →  gộp = 48.69 km
Louvain+gating: 74 cụm = 13 cụm thật + 61 singleton ≡ đúng 61 điểm gt=-1
Ngưỡng khoảng cách ẩn: w>0.05 ⟹ d < 700·√(2 ln 20) = 1713 m
```

## 0.2. Thứ tự bắt buộc

```
P0 (lý thuyết, không cần chạy)  ─┐
P1 (dataset)  →  P2 (pipeline)  ─┴→  P3 (chạy lại)  →  P5 (viết bài)
P4 (văn liệu) chạy song song, độc lập
P6 (xác minh) sau cùng
```

Không sửa `main.tex` trước khi P3 xong: mọi con số trong bài sẽ đổi.

## 0.3. Truy vết phản biện → nhiệm vụ

| Mục phản biện | Nhiệm vụ | Loại xử lý |
|---|---|---|
| §1 cửa sổ 51× là artifact | P0.1, P0.2, P3.5 | Thu hồi + thay bằng bổ đề |
| §2 phương pháp = ngưỡng khoảng cách | P1.1, P1.2, P3.3 | Đổi dữ liệu để S_ctx có việc |
| §3 dataset quyết định kết quả | P1.1, P1.3, P1.4 | Đổi dữ liệu |
| §4 AUC 0.9176 là artifact | P1.2, P2.4, P3.4 | Thiết kế lại + báo cáo AUC có điều kiện |
| §5 trình bày HDBSCAN nghiêng | P2.2, P3.2 | Sửa quy ước đo |
| §6 thiếu dòng văn liệu | P4.1, P4.2, P5.2 | Trích dẫn + định vị lại |
| §7 Edge AI 0 bằng chứng | P5.4 | Rút tuyên bố (theo quyết định 0) |
| §8 độ chặt thống kê | P2.5, P3.6, P3.7 | Thêm CI + đa seed + giới hạn mô phỏng |
| §9 điểm kỹ thuật nhỏ | P5.6 (a–e) | Sửa văn bản + P2.3 cho N_max |
| §10 trình bày & venue | P5.1, P5.3, P5.5, P5.7 | Viết lại + gộp + typeset |

## P0 — Thay tuyên bố trung tâm bằng một bổ đề giải tích

Đây là hạng mục **giá trị cao nhất và không cần thực nghiệm nào** (đúng như
reviewer nói: "đó là đóng góp mạnh nhất mà bài đang có"). Làm trước, độc lập với
dataset.

### P0.1 Bổ đề 1 — cận trên của đường kính cụm theo θ

Viết mới một mục lý thuyết trong `paper/main.tex` (đặt vào Mục 4.2, sau định
nghĩa `w_ij`), phát biểu và chứng minh:

> **Bổ đề 1 (bảo đảm định vị của dạng nhân).** Với `w_ij = S_geo(d_ij) ·
> (β·S_temp + γ·S_ctx)`, `S_geo(d) = exp(−d²/2σ²)`, và `β + γ ≤ 1`, mọi cạnh còn
> lại sau khi làm thưa ở ngưỡng θ > 0 đều thoả
> `d_ij < σ·√(2·ln(1/θ))`.
> Do đó đường kính mọi cụm liên thông qua ≤ h cạnh bị chặn bởi
> `h·σ·√(2·ln(1/θ))`, **không phụ thuộc dữ liệu**.
>
> **Hệ quả (dạng cộng không có bảo đảm tương ứng).** Với
> `w_ij = α·S_geo + β·S_temp + γ·S_ctx`, ta có `w_ij ≥ β·S_temp + γ·S_ctx`, một
> sàn **dương và độc lập với `d_ij`**. Với mọi θ nhỏ hơn sàn đó, tập cạnh còn lại
> không bị chặn về khoảng cách: tồn tại cặp cách nhau tuỳ ý xa vẫn được giữ.

Cách viết chứng minh: `S_geo(d) > θ ⟺ exp(−d²/2σ²) > θ ⟺ d < σ√(2 ln(1/θ))`;
kết hợp `(β·S_temp + γ·S_ctx) ≤ 1` cho `w_ij ≤ S_geo(d_ij)`, nên
`w_ij > θ ⟹ S_geo > θ`. Kiểm số: σ = 700 m, θ = 0.05 → **d < 1713 m** (khớp con
số đo được ở 0.1).

Vì sao đây là cách sửa đúng cho §1: bổ đề nói lên **cùng một sự thật** mà "cửa sổ
51×" định nói, nhưng dưới dạng bất biến theo tái tham số hoá và không cần bất kỳ
seed/dataset nào. Nó cũng biến điểm yếu §2 ("thực chất là ngưỡng khoảng cách")
thành **tính chất được chứng minh có chủ đích**, thay vì một artifact bị bắt.

### P0.2 Thu hồi con số 51×

- Xoá "51×" khỏi abstract, Mục 1 (contributions), Mục 6.13, Mục 7 (kết luận).
- Trong bảng Thí nghiệm 13, **giữ** cột `usable_theta_lo/hi` nhưng **bỏ cột
  `usable_width_ratio`**, thay bằng hai cột bất biến: `θ/w_max` chuẩn hoá và
  `tỉ lệ cạnh giữ lại`. Kèm một câu thừa nhận thẳng: theo cả hai thước đo bất
  biến, lợi thế là 2× và 1× — **không phải 51×** — và lý do thật nằm ở Bổ đề 1
  (cửa sổ của gating chứa θ→0⁺).
- Thí nghiệm 13 chuyển vai: từ "bằng chứng đóng góp" thành **xác nhận thực nghiệm
  của Bổ đề 1** (dạng cộng không có θ nào cho đường kính bị chặn — khớp với
  `n_usable_theta = 0` của α=0.34 và cửa sổ hẹp 1.06× của α=0.5).

### P0.3 Sửa `demo/experiments/exp13_theta_calibration.py`

- Thêm vào mỗi dòng sweep: `theta_norm = theta / w_max(form)` và
  `retained_frac = (w_off > theta).mean()`.
- Thêm cột `usable_theta_norm_lo/hi`, `usable_retained_lo/hi`.
- Xoá `usable_width_ratio` khỏi output (hoặc giữ kèm chú thích "không bất biến —
  không dùng để tuyên bố").
- Thêm hàm `verify_lemma1()`: với mỗi θ trong sweep, kiểm
  `max{d_ij : w_ij > θ} < σ√(2 ln(1/θ))` cho gating (phải **luôn** đúng) và cho
  dạng cộng (phải **vi phạm** ở θ nhỏ). Lưu `exp13_lemma1_check.json`. Đây là
  bảng thay thế cho bảng 51× trong bài.

## P1 — Dataset khó hơn (gốc của §2, §3, §4)

Mọi thứ trong P1 làm trong `demo/data/generate.py`. Nguyên tắc: **giữ nguyên API
xuất `dataset.json`** để 13 exp hiện có chạy được không sửa; chỉ đổi phân bố sinh.

### P1.1 Nhóm chồng lấn về không gian + mật độ không đồng đều

Vấn đề hiện tại: 6 đảo `spread_m=250`, nhóm narrative trên vệ tinh cách tâm 3 km,
cộng `assert_gt_separable(min_sep_m=2000)`. Mọi phương pháp có ngưỡng cắt giữa
1–2 km đều thắng.

- **Bỏ `assert_gt_separable`** hoàn toàn (thay bằng ghi log khoảng cách liên nhóm
  nhỏ nhất, không assert). Assertion này chính là thứ khiến dataset "được bảo đảm
  cho gating thắng".
- Thêm tham số `overlap_ratio` (mặc định ~0.35): với mỗi cặp nhóm liền kề, đặt
  khoảng cách tâm–tâm `= (spread_i + spread_j) · (1 − overlap_ratio)` để **vỏ
  không gian của các nhóm giao nhau**. Mục tiêu: ≥ 3 cặp nhóm có khoảng cách tâm
  < 800 m (dưới σ_geo), tức địa lý **không thể** tách chúng.
- Mật độ không đồng đều: cho `spread_m` biến thiên theo nhóm (ví dụ
  {120, 180, 250, 400, 600, 900} m) và số điểm mỗi nhóm lệch mạnh
  (ví dụ {8, 12, 20, 35, 55, 70}). Đây là điều kiện làm DBSCAN/HDBSCAN
  gặp khó thật, đồng thời đo được liệu Louvain+gating có bền.
- **Điểm then chốt:** các nhóm chồng lấn phải **tách được bằng ngữ cảnh** — cặp
  nhóm chồng lấn về không gian mang `flood`/`urgency` khác biệt rõ (ví dụ nhóm A:
  F≈0.85, E≈0.9 — vỡ đê; nhóm B cùng vị trí: F≈0.25, E≈0.3 — ngập nhẹ do mưa).
  Chỉ khi đó `S_context` mới có cơ hội chứng minh giá trị và §2 mới trả lời được
  thay vì thừa nhận.
- Thêm ~2–3 cặp nhóm **cùng vị trí, khác thời gian** (lệch 3–4 h, tức ≫ τ_temp =
  45 min) để `S_temp` cũng có việc làm — hiện tại β chỉ được chứng minh trên đúng
  một cặp S5 923 m, đúng như §2 chỉ ra.

Tiêu chí nghiệm thu P1.1 (kiểm bằng script, đặt trước khi xem kết quả cuối):
1. Baseline **chỉ dùng toạ độ** (`run_kmeans(features="geo")`, và Agglomerative
   trên khoảng cách Haversine thuần) phải đạt **ARI < 0.75**.
2. Ablation `S_context` (Thí nghiệm 6) phải cho **ARI giảm ≥ 0.08** và phân hoạch
   **không** còn bit-identical (τ < 1.0).
3. Quét `τ_F, τ_E` (Thí nghiệm 2) phải cho ARI **biến thiên** — không còn trơ.

Nếu (1)(2)(3) không đạt, tăng `overlap_ratio` và độ tương phản ngữ cảnh rồi lặp.
**Không** điều chỉnh sau khi đã xem kết quả của phương pháp đề xuất.

### P1.2 Tin giả có phân bố `n_corrob` và `has_image` chồng lấn tin thật

Đây là gốc của §4 — vấn đề nặng nhất về tính đúng đắn. Số đo hiện tại:
`n_corrob` = 0.00 cho **mọi** tin giả và 14.84 cho tin thật trong đảo, nên `C_i`
chỉ đang đo "điểm có nằm trong vùng dày đặc hay không" ≡ trùng biến đích.

- **Tin giả phải nằm trong cụm.** Đặt ~60–70% tin giả **bên trong** các nhóm thật
  (cùng vị trí, cùng cửa sổ thời gian), chỉ ~30–40% rải rác. Khi đó tin giả có
  `n_corrob` cao — đúng như tin thật.
- **`has_image` chồng lấn:** tin thật có ảnh với xác suất ~0.7, tin giả ~0.45
  (hiện tại đang gần như tách hẳn: AUC của `has_image` một mình = 0.5675 nhưng
  `n_corrob` = 0.9355 gánh toàn bộ). Mục tiêu: **không đặc trưng đơn nào** đạt
  AUC > 0.75.
- **Tin giả củng cố lẫn nhau:** thêm kịch bản "chiến dịch tin giả" — 3–5 tin giả
  cùng toạ độ, cùng giờ, củng cố nhau → `n_corrob` cao mà vẫn là giả. Đây là
  trường hợp làm heuristic `C_i` **sai**, và phải báo cáo đúng như vậy.
- Tăng số tin giả lên ~45–60 (hiện 23) để bootstrap CI không quá rộng — §8.

Tiêu chí nghiệm thu P1.2: AUC biên của từng đặc trưng đơn (`n_corrob`,
`has_image`) đều < 0.75, và tỉ lệ tin giả nằm trong cụm ≥ 0.55.

### P1.3 Nhãn ground-truth độc lập với hình học sinh

Hiện `gt_cluster` gán theo tâm đảo, nên nhãn **là** hình học. Cần:
- Gán `gt_cluster` theo **sự kiện vật lý** (một đợt vỡ đê / một tuyến ngập) chứ
  không theo tâm cụm điểm. Cho phép một sự kiện có hai ổ điểm cách nhau
  (multi-modal), và hai sự kiện khác nhau chia sẻ một vùng không gian.
- Cho phép ARI đúng **không** đạt được bằng bất kỳ ngưỡng khoảng cách nào — đó là
  định nghĩa của một dataset đo được phương pháp.

### P1.4 Không dùng ARI làm tiêu chí "usable" của Thí nghiệm 13

`USABLE_MIN_ARI = 0.95` trong `exp13_theta_calibration.py:44` thừa hưởng nguyên
vấn đề §3 (ARI cao là do generator). Sửa:
- Đổi tiêu chí usable sang **thuần vận hành**: `max_diam < 5 km` **và**
  `frac_singletons < 0.5` **và** `n_clusters` trong khoảng hợp lý — không dùng
  nhãn GT.
- Giữ ARI như **cột báo cáo**, không như cột lọc. Ghi rõ lý do trong docstring:
  tiêu chí usable phải là thứ điều phối viên đo được **khi không có nhãn**.

### P1.5 Dữ liệu thật (hạng mục phụ, làm nếu kịp)

Theo quyết định 0, đây là phần bổ trợ. Phạm vi tối thiểu có ích:
- Lấy tập con CrisisMMD/FloodNet **có toạ độ**; nếu không có toạ độ đủ dày, dùng
  dữ liệu ngập lụt ĐBSCL từ `resource/` (kiểm trước xem có gì dùng được).
- Chỉ cần **một** bảng: ARI/NMI/đường kính của gating vs additive vs 5 baseline
  trên dữ liệu thật, kể cả khi kết quả xấu hơn. Một bảng dữ liệu thật đủ để
  chuyển bài từ "chỉ synthetic" sang "synthetic + sanity check thực địa".
- Nếu không kịp: nêu rõ trong Threats to Validity là **chưa** có, không hứa.

## P2 — Sửa pipeline và quy ước đo

### P2.1 `demo/pipeline/weighting.py` — công bố sàn của dạng cộng

Bổ đề 1 nói dạng cộng có sàn dương độc lập khoảng cách. Cần một hàm để bài báo
trích số thay vì lập luận suông:

- Thêm `additive_floor(params, alpha) -> float`: trả về
  `min{β·S_temp + γ·S_ctx}` trên toàn bộ cặp — chính là sàn trong Hệ quả của
  Bổ đề 1. Với dữ liệu hiện tại sàn = 0.041 (khớp `w_min` trong
  `exp13_theta_ranges.json`).
- Thêm `implied_distance_cutoff(params, theta) -> float`:
  `σ·√(2·ln(1/θ))`. Dùng cho bảng Bổ đề 1 và cho Mục 4.2.

### P2.2 `demo/pipeline/metrics.py` — quy ước đường kính không nghiêng bên nào

Đây là §5. `geographic_spread` hiện trả `mean_diameter_km` (gồm singleton = 0) và
`mean_diameter_km_multi`. Cả hai đều không phân biệt được **cụm chỉ gồm điểm
nhiễu**, nên HDBSCAN bị 6 cụm toàn nhiễu (TB 147 km) kéo trung bình lên 48.69 km.

- Thêm tham số `gt_labels` (tuỳ chọn) vào `geographic_spread`. Khi có, trả thêm:
  - `n_clusters_labeled` / `n_clusters_noise_only`,
  - `mean_diameter_km_labeled` — **chỉ** các cụm chứa ≥ 1 điểm có nhãn GT
    (`gt >= 0`),
  - `max_diameter_km_labeled`,
  - `frac_labeled_clusters_under_1p5km`.
- Quy ước báo cáo mới, áp dụng **cho mọi phương pháp như nhau** (ghi vào docstring
  và vào Mục 5 của bài): chỉ số hình học chính là `*_labeled`; chỉ số gộp và
  cụm-toàn-nhiễu báo cáo riêng ở cột phụ.
- Kết quả kỳ vọng sau khi sửa: HDBSCAN đọc là "phục hồi 14 nhóm, 13/14 dưới
  1.5 km, TB 6.46 km" — **không** phải "48.69 km, trải cả tỉnh". So sánh chính
  của Thí nghiệm 4/9 sẽ yếu đi; đó là kết quả đúng và phải báo cáo như vậy.

### P2.3 `demo/pipeline/priority.py` — `N_max` tĩnh làm mặc định

§9 (điểm 5): `Ñ` dùng tham chiếu động nên `P` không so sánh được qua thời gian —
một cụm tụt hạng chỉ vì nơi khác xuất hiện cụm lớn hơn. Với hệ điều phối trực
tuyến đây là hạn chế thiết kế thật.

- `score_clusters(..., n_ref=None)` đã có (dòng 52). Đổi **mặc định của cấu hình**
  sang `n_ref` tĩnh (thêm `PriorityParams.n_ref: float = 500.0`, công bố trong
  Bảng tham số) và ghi rõ: mọi số báo cáo dùng `n_ref` tĩnh.
- Thêm thí nghiệm nhỏ (gộp vào Thí nghiệm 5, không tạo exp mới): so `τ` của xếp
  hạng giữa `n_ref` động và tĩnh khi **thêm dần** cụm mới vào — định lượng chính
  xác mức bất ổn mà §9 nêu, thay vì chỉ thừa nhận bằng lời.

### P2.4 `demo/pipeline/attributes.py` — công bố `n_corrob` như đặc trưng riêng

§4 cho thấy `n_corrob` gánh toàn bộ AUC. Bài phải để người đọc thấy điều đó:
- Lưu `n_corrob` vào `Event` như một trường (hiện đang tính trong vòng lặp cục
  bộ), để Thí nghiệm 8 báo cáo được AUC của **từng** đặc trưng cạnh nhau.

### P2.5 `demo/experiments/common.py` — hạ tầng thống kê dùng chung

§8: cả bài chỉ có một chỗ có CI. Cần một chỗ duy nhất để mọi exp gọi:
- `bootstrap_ci(values, stat_fn, n=2000, alpha=0.05, seed=42) -> (lo, hi)`.
- `paired_test(a, b) -> dict`: Wilcoxon signed-rank + hiệu trung bình + CI của
  hiệu (dùng cho so sánh cùng seed giữa gating và additive).
- `multi_seed(fn, seeds=range(20)) -> list`: chạy `fn(seed)` và trả list, để
  Thí nghiệm 7 và 5 dùng chung cơ chế đa seed như Thí nghiệm 12.

## P3 — Chạy lại toàn bộ thực nghiệm với dữ liệu và quy ước mới

Thứ tự: sinh dữ liệu → kiểm tiêu chí nghiệm thu P1 → chạy exp → **rồi mới** viết
bài. Mọi con số trong `paper/` sẽ đổi; không sửa `main.tex` trước bước này.

### P3.1 Sinh và niêm phong dữ liệu

- `python demo/data/generate.py` với generator mới; giữ `dataset-backup.json` cũ
  làm đối chiếu, thêm `dataset-v3.json` để tái lập được cả hai chế độ.
- Chạy script kiểm 3 tiêu chí P1.1 + 2 tiêu chí P1.2. **Nếu không đạt, sửa
  generator, không sửa tiêu chí.** Ghi lại kết quả kiểm vào
  `demo/results/tables/exp0_dataset_hardness.json` và đưa thành **Bảng 2 của
  bài** — đây là bằng chứng dataset không tự cho phương pháp thắng, và là câu trả
  lời trực tiếp cho §3.

### P3.2 Thí nghiệm 4 và 9 — báo cáo lại theo quy ước `*_labeled`

- Thay cột hình học chính bằng `mean_diameter_km_labeled` cho **tất cả** baseline.
- Thêm cột `n_clusters_noise_only` để người đọc thấy sự khác biệt thật giữa các
  phương pháp là **cách xử lý thùng nhiễu**, không phải chất lượng hình học.
- Viết lại kết luận của hai exp: nếu HDBSCAN/Agglomerative vẫn khớp gating trên
  `*_labeled`, phải nói thẳng là **không phân biệt được** trên chỉ số hình học, và
  chuyển lập luận sang chỗ khác (số tham số phải hiệu chuẩn, xem P3.5).

### P3.3 Thí nghiệm 6 và 2 — cơ hội cuối cho `S_context`

Đây là bài kiểm quyết định cho §2. Trên dữ liệu mới:
- Thí nghiệm 6: ablation `S_context` phải cho ARI giảm đo được và τ < 1.0. Thêm
  cột **chỉ trên các cặp nhóm chồng lấn** (tập con mà ngữ cảnh là thứ duy nhất
  tách được) — đây là nơi hiệu ứng phải xuất hiện nếu nó tồn tại.
- Thí nghiệm 2: quét `τ_F, τ_E` phải cho bề mặt không phẳng. Vẽ lại `fig3_heatmap`
  và **đưa vào bài** (hiện đang không được tham chiếu).
- Sửa bất nhất §9 (điểm 3): Thí nghiệm 6 đang in `mean_diam 0.1491` (gồm
  singleton) trong khi chỗ khác dùng `0.8487` (multi-member). Đổi sang
  `*_labeled` cho khớp toàn bài.
- **Nếu `S_context` vẫn trơ trên dữ liệu chồng lấn:** kết luận đúng là bỏ
  `S_context` khỏi công thức đề xuất và định vị bài quanh `S_geo · S_temp` +
  hàm ưu tiên. Chuẩn bị sẵn nhánh này; không giữ một số hạng không có tác dụng
  chỉ để tiêu đề nghe rộng hơn.

### P3.4 Thí nghiệm 8 — báo cáo lại `C_i` cho đúng

- Bảng chính đổi thành **AUC/AP có điều kiện trên mật độ láng giềng** (chia
  `n_corrob` thành 3 tầng: 0, 1–5, >5), báo cáo trong từng tầng. AUC biên chỉ còn
  là một dòng phụ kèm cảnh báo nó bị confound bởi mật độ.
- Thêm bảng AUC của **từng đặc trưng đơn** (`n_corrob`, `has_image`) cạnh `C_i`,
  để người đọc tự thấy `C_i` có vượt đặc trưng mạnh nhất hay không. Trên dữ liệu
  cũ nó **không** (0.9176 < 0.9355) — nếu trên dữ liệu mới vẫn không, phải nói rõ:
  `C_i` là một **quy ước tổng hợp có thể giải thích**, không phải bộ phát hiện tốt
  hơn baseline một đặc trưng.
- Bỏ tuyên bố "giảm 55% dân số ảo" hoặc phát biểu lại đúng bản chất: đó là **hệ
  quả số học** của `C_i = 0.4502` nhân vào `Ñ`, do `(b_0,b_1,b_2)` tác giả chọn —
  không phải năng lực phát hiện. Thêm sweep `(b_1, b_2)` để thấy con số đó đổi thế
  nào theo tham số.
- Thêm bootstrap CI cho mọi AUC/AP (đã có sẵn cơ chế, mở rộng bằng P2.5).
- Báo cáo tách riêng kịch bản "chiến dịch tin giả" (P1.2): đây là **failure mode
  đã biết** của `C_i` và phải nằm trong bài.

### P3.5 Thí nghiệm 13 — chuyển thành xác nhận Bổ đề 1

- Chạy lại với các cột bất biến của P0.3 và tiêu chí usable không dùng ARI (P1.4).
- Bảng mới trong bài gồm: `θ` chuẩn hoá, tỉ lệ cạnh giữ lại, `max_diam`, và
  **kiểm Bổ đề 1** (gating: 0 vi phạm; additive: số θ vi phạm > 0).
- Thêm một chỉ số **có ý nghĩa vận hành** thay cho 51×: `θ_min_usable` — với
  gating, tồn tại θ nhỏ tuỳ ý dùng được (Bổ đề 1); với dạng cộng, mọi θ dưới sàn
  0.041 đều **không** dùng được. Đây là phát biểu bất biến và kiểm chứng được.

### P3.6 Thí nghiệm 7 — giới hạn mô phỏng và thêm CI

§8 (điểm 2): mô phỏng hiện phục vụ cả 74 cụm gồm 61 singleton là nhiễu/tin giả,
nên "mean arrival 2528 phút" (42 h) vô nghĩa vận hành.
- Giới hạn tập cụm được phục vụ: chỉ các cụm có ≥ `min_cluster_serve` (= 2) thành
  viên **và** có ít nhất một điểm không bị `C_i` loại — đúng như một điều phối
  viên làm. Ghi rõ quy tắc lọc trong bài.
- Đa seed (20 seed, dùng `multi_seed` của P2.5) + CI bootstrap cho cả 3 metric +
  Wilcoxon ghép cặp. Chênh lệch 2.9% (110.2 vs 113.5) hiện **không** kèm CI; nếu
  CI chứa 0 thì phải phát biểu là **không có bằng chứng khác biệt**, không báo cáo
  4 chữ số ý nghĩa.
- Đa depot: ≥ 3 vị trí depot khác nhau, báo cáo trung bình + khoảng.

### P3.7 Thí nghiệm 12 và 5 — làm rõ điều kiện của "100%"

- Thí nghiệm 12: mỗi seed phải sinh lại **cả hình học liên nhóm** (số nhóm,
  `overlap_ratio`, spread biến thiên), không chỉ jitter điểm — đúng phê bình §8
  (điểm 3). Thêm `overlap_ratio` vào biến thiên theo seed.
- Thêm CI + Wilcoxon cho từng metric, thay vì chỉ `wins_pct`.
- Thí nghiệm 5: thêm phần so `n_ref` động vs tĩnh (P2.3). Ghi rõ trong bài rằng
  `τ` đo **tự nhất quán**, không đo tính đúng — và với dataset dễ thì top-3 giữ
  nguyên là gần tất yếu.

### P3.8 `run_all.py` và hình

- Cập nhật `run_all.py` cho exp0 (kiểm độ khó dataset) và thứ tự mới.
- `make_figures.py`: vẽ lại toàn bộ 7 hình từ dữ liệu mới; thêm
  `fig8_lemma1.png` (đường `σ√(2 ln(1/θ))` so với `max d_ij` thực đo cho gating và
  additive — hình trực quan hoá đóng góp trung tâm mới).
- Copy hình sang `paper/figures/`, **bao gồm** `fig2_map.png` và `fig3_heatmap.png`
  đang bị bỏ (xem P5.5).
- `verify_figures.py`: mở rộng để kiểm mọi hình được `\includegraphics` trong
  `main.tex` đều tồn tại trong `paper/figures/`, và ngược lại cảnh báo hình có
  trong thư mục mà không được tham chiếu.

## P4 — Văn liệu và định vị tính mới (§6)

Chạy song song, không phụ thuộc P1–P3. Đây là hạng mục **rẻ nhất và bắt buộc**:
thiếu nó thì bài bị đánh giá là không biết dòng nghiên cứu của chính mình.

### P4.1 Thêm vào `paper/references.bib`

Hiện `references.bib` có 24 mục, **không** mục nào cho product kernel hay
spatially-constrained clustering. Cần bổ sung tối thiểu:

| Khoá | Công trình | Vì sao bắt buộc |
|---|---|---|
| `tomasi1998bilateral` | Tomasi & Manduchi, *Bilateral Filtering for Gray and Color Images*, ICCV 1998 | **Cùng dạng toán, cùng động lực** với `S_geo · S_ctx`. Không trích là thiếu nghiêm trọng. |
| `chavent2018clustgeo` | Chavent et al., *ClustGeo: hierarchical clustering with spatial constraints*, 2018 | Dòng "đảm bảo cụm liền mạch không gian" đã được nghiên cứu hệ thống. |
| `duque2007supervised` (hoặc tương đương) | Contiguity-constrained / regionalization trong địa thống kê | Cùng bài toán, cộng đồng khác. |
| `yuan2004spatial` / kernel tách được có ràng buộc không gian trong spectral clustering | | §6 nêu đích danh dòng thứ ba. |
| Nguồn cho **dạng cộng** | Bất kỳ công trình thực sự dùng `α·S_geo + β·S_temp + γ·S_ctx` | Nếu **không tìm được**, xem P4.3. |

### P4.2 Viết lại Mục 2 (Related Work) — thêm một tiểu mục

Thêm Mục 2.x *"Product kernels and spatially constrained clustering"*:
- Nêu thẳng: dạng nhân **không mới** như một kỹ thuật; bilateral filtering dùng
  đúng cấu trúc này từ 1998.
- Định vị lại phần mới: **(a)** Bổ đề 1 — chuyển tính chất "product kernel làm
  thưa đồ thị" thành một **bảo đảm định vị định lượng theo θ** cho bài toán điều
  phối (chưa thấy phát biểu ở dạng này trong bối cảnh triage); **(b)** hàm ưu tiên
  cấp cụm với hệ số khuếch đại công bằng `μ` và núm chính sách được quét đàng
  hoàng; **(c)** đóng gói toàn tuyến cho triage cứu hộ lũ.
- Cập nhật Bảng 1 (bảng so sánh công trình liên quan): thêm dòng cho bilateral
  filtering / ClustGeo; sửa dòng "Weighted graph ✓ (gating)" vì nó đang hàm ý
  gating là đóng góp mới của bài.

### P4.3 Xử lý straw man của dạng cộng (§6, đoạn cuối)

Mục 2.3 viết *"that additive penalty is precisely the design we compare against"*
nhưng **không dẫn công trình nào**. Hai lựa chọn, chọn theo kết quả tìm kiếm:
- **Nếu tìm được** công trình dùng dạng cộng: trích, và giữ nó làm baseline chính
  đáng.
- **Nếu không tìm được:** phát biểu lại trung thực — dạng cộng là một **baseline
  do chúng tôi dựng** để tách vai của cấu trúc nhân, **không** phải phương pháp
  của ai. Đồng thời bỏ mọi câu hàm ý "đánh bại tiếp cận hiện có". Kèm câu này:
  Thí nghiệm 13 cho thấy với θ hiệu chuẩn, baseline đó **không thua** ở đỉnh — nên
  đóng góp không nằm ở việc thắng nó mà ở Bổ đề 1.

### P4.4 Bổ sung trích dẫn cho `μ` và hàm ưu tiên

Phần còn lại thực sự của bài (theo chính reviewer) là hàm ưu tiên. Cần đặt nó
đúng bối cảnh: đã có `saaty1980ahp`, `vitoriano2011multicriteria`,
`gralla2014review` — thêm dòng văn liệu về **equity/fairness trong phân bổ nguồn
lực nhân đạo** (ví dụ các công trình về equity objectives trong humanitarian
logistics) để `μ` không đứng một mình như một hệ số tự phát minh.

## P5 — Viết lại `paper/main.tex`

Chỉ bắt đầu sau khi P3 xong. Nhắm 12–16 trang LNCS (full paper).

### P5.1 Abstract — viết lại từ đầu, ~200 từ

Hiện ~450 từ, gấp đôi chuẩn LNCS, và phần lớn liệt kê những gì **không** hoạt
động. §10: "abstract hiện tại thuyết phục reviewer rằng bài không có kết quả".

Cấu trúc mới, mỗi ý một câu:
1. Bối cảnh: điều phối cứu hộ lũ cần gom báo cáo rời rạc thành đơn vị điều phối
   được.
2. Đề xuất: đồ thị trọng số dạng **nhân** (product kernel) + hàm ưu tiên cấp cụm
   có hệ số công bằng `μ`.
3. **Kết quả lý thuyết (tuyên bố dương tính chính):** Bổ đề 1 — cận trên đường
   kính cụm `h·σ√(2 ln(1/θ))`, không phụ thuộc dữ liệu; dạng cộng không có bảo đảm
   tương ứng.
4. Xác nhận thực nghiệm trên dataset **có nhóm chồng lấn về không gian** (nêu con
   số ARI mới + CI, và mức ARI của baseline chỉ-toạ-độ để thấy dataset không tự
   cho đáp án).
5. Một câu hạn chế: synthetic, và các thành phần chưa được chứng minh.

**Không** đưa vào abstract: 51×, "wins on 100% of 20 seeds" (hoặc nếu giữ thì
kèm điều kiện ngay trong câu), tuyên bố phát hiện tin giả, Edge AI.

### P5.2 Mục 1 — viết lại Contributions

Thay 3 contribution hiện tại (C1 trích xuất tại biên — 0 bằng chứng; C3 `V_i`/`C_i`
edge-feasible — 0 bằng chứng) bằng:

1. **Bổ đề 1** và hệ quả: bảo đảm định vị của dạng nhân, và việc dạng cộng không
   có bảo đảm đó. Kèm xác nhận thực nghiệm (Thí nghiệm 13 + `fig8_lemma1`).
2. **Hàm ưu tiên cấp cụm** `P(C_k)` với `V_agg` khuếch đại có trần `μ`: núm chính
   sách tường minh, quét đầy đủ, có phân tích outcome (Thí nghiệm 7 với CI).
3. **Đóng gói và đánh giá toàn tuyến** cho triage cứu hộ lũ, kèm một dataset
   sinh có **độ khó được kiểm định** (Bảng 2 / exp0) và so sánh 5 baseline theo quy
   ước hình học không nghiêng bên nào.

### P5.3 Gộp thí nghiệm (§10, điểm 3)

13 thí nghiệm là quá nhiều cho 12–16 trang. Kế hoạch gộp:

| Hiện tại | Xử lý |
|---|---|
| 1B, 1C, 1D, 1H | Gộp thành **một** mục "kiểm tính chất công thức", trình bày dạng một bảng gọn — không gọi là "thí nghiệm". |
| 1A, 13 | Gộp thành **Thí nghiệm chính về dạng trọng số** (nhân vs cộng, có hiệu chuẩn θ, kèm kiểm Bổ đề 1). |
| 10 (kích thước gói tin) | Rút thành **một câu** trong Mục 4.1. §7 gọi đúng: đây là tautology đo `json.dumps` của 8 con số. |
| 3 (Louvain vs Leiden) | Rút thành một đoạn trong Mục 4.3 hoặc phụ lục. |
| 11 (scaling) | Giữ, nhưng gộp vào mục phân tích độ phức tạp cùng P5.6(b). |
| 2, 4, 5, 6, 7, 8, 9, 12 | Giữ làm thí nghiệm riêng. |

Đích: **6–7 thí nghiệm** được đánh số trong bài, phần còn lại thành bảng/đoạn.

### P5.4 Edge AI — hạ cấp theo quyết định 0

Nhóm đã train MobileNetV3 + DistilBERT trên Colab, số đo bổ sung sau, và **không**
coi đây là đóng góp khoa học. Xử lý:
- **Tiêu đề:** bỏ "Using Edge AI". Đề xuất: *"A Product-Kernel Weighted Graph for
  Flood-Rescue Event Clustering and Cluster-Level Priority Scoring"* (chốt lại sau
  khi biết `S_context` có sống không — P3.3).
- **Abstract:** bỏ hoàn toàn.
- **Contributions:** bỏ C1 và phần "edge-feasible" của C3.
- **Trong bài:** giữ một mục ngắn *"Deployment architecture"* mô tả đường trích
  xuất `(F, E)` từ ảnh/văn bản, nói rõ đây là **kiến trúc đề xuất**, các thuộc
  tính trong đánh giá là **cho trước từ generator**, và số đo trên thiết bị sẽ
  được báo cáo riêng. Để sẵn một `\begin{table}` rỗng có chú thích để cắm số
  latency/RAM khi có.
- **Bảng 1:** bỏ các dấu ✓ hàm ý đã hiện thực hoá Edge AI.

### P5.5 Hình vẽ

- **Đưa `fig2_map.png` vào bài** — bài về phân cụm không gian phải có hình phân bố
  dữ liệu, và hình mới sẽ cho thấy các nhóm **chồng lấn** (bằng chứng thị giác cho
  P1.1). Đặt trong Mục 5.1 (mô tả dataset).
- **Đưa `fig3_heatmap.png` vào bài** nếu P3.3 cho bề mặt `τ_F, τ_E` không phẳng —
  khi đó nó là bằng chứng `S_context` có tác dụng. Nếu vẫn phẳng, bỏ và nói rõ
  trong Threats to Validity.
- Thêm `fig8_lemma1.png` (P3.8) vào Mục 4.2 cạnh Bổ đề 1.
- Sửa **`Float too large for page by 104.75pt` ở dòng 86** (hiện là hình/bảng đầu
  bài): giảm `width`, hoặc chuyển sang `[htbp]`/`figure*`, hoặc tách bảng.

### P5.6 Các điểm kỹ thuật §9

| | Vấn đề | Sửa |
|---|---|---|
| a | Lý giải `S_temp` bậc nhất "vì lũ có quán tính" là non-sequitur | Quán tính biện minh cho `τ` **lớn hơn**, không cho việc đổi bậc số mũ. Viết lại: bậc nhất cho đuôi **nặng hơn**, phù hợp khi diễn biến kéo dài; hoặc bỏ lý giải và nêu là **quy ước** kèm sweep `τ_temp`. |
| b | Louvain "near-`O(N log N)`" là điểm bán, nhưng dựng ma trận là `O(N²)` | Nêu rõ **pipeline là `O(N²)`** do bước dựng ma trận và `matrix_to_graph`. Chuyển Thí nghiệm 11 thành phần chính của mục này, không phải thừa nhận ở cuối. Nêu hướng giảm: chỉ mục không gian (grid/ball-tree) cắt cặp xa nhờ **chính Bổ đề 1** — `d ≥ σ√(2 ln(1/θ))` thì `w < θ`, nên không cần tính. Đây là một hệ quả thực dụng đẹp của P0.1, nên viết vào bài. |
| c | Thí nghiệm 6 in `mean_diam 0.1491` (gồm singleton) vs `0.8487` chỗ khác | Dùng `*_labeled` thống nhất toàn bài (P2.2). |
| d | Bảng 3: "E nhiễu hơn F" không kiểm chứng được vì cả hai đều trơ | Nếu sau P3.3 vẫn trơ: nêu là **quy ước**, bỏ lý giải có căn cứ. Nếu không còn trơ: dẫn số từ sweep mới. |
| e | `P ∈ [0,2)` đúng nhưng `Ñ` động làm `P` không so sánh qua thời gian | Đổi mặc định sang `n_ref` tĩnh (P2.3), nêu hạn chế **đúng mức nặng** như §9 yêu cầu, kèm số đo bất ổn từ Thí nghiệm 5 mở rộng. |

### P5.7 Giọng văn, tác giả, typesetting (§10)

- **Giọng văn:** bỏ mọi câu kiểu rebuttal khỏi abstract/contributions/conclusion:
  *"we were wrong to present it as"*, *"the result we must report first is the one
  that does not favor our method"*, *"we report rather than hide"*, *"an artifact
  in our favour"*. **Giữ** tinh thần đó, nhưng dồn vào Mục *Threats to Validity* —
  ở đó nó là điểm mạnh. Nguyên tắc: mỗi mục chỉ được có **một** giọng; phần thân
  bài phát biểu điều bài **khẳng định**.
- **Tác giả (`main.tex:43-44`):** thay email placeholder
  `corresponding.author@ctu.edu.vn` + `% TODO(authors)` bằng email thật; thêm
  ORCID cho 6 tác giả; tách affiliation đúng chuẩn LNCS.
- **Cảnh báo LaTeX (theo `main.log` hiện tại, không theo bản phản biện):**
  - `Float too large for page by 104.75pt` (dòng 86) — **ưu tiên cao** (P5.5).
  - 5 `Overfull \hbox`: dòng 39–40 (6.01pt), 49–50 (1.12pt), 225–226 (11.32pt),
    262–263 (12.70pt), 272–273 (9.32pt). Sửa bằng ngắt dòng/`\sloppy` cục
    bộ/viết lại câu. Đích: **0 overfull > 5pt**.
  - Không có `Underfull` nào — bỏ hạng mục này khỏi việc cần làm.

## P6 — Xác minh trước khi nộp

Chạy theo thứ tự, mỗi mục là một cửa chặn:

1. `python demo/run_all.py` chạy sạch, không exception.
2. Kiểm 5 tiêu chí nghiệm thu dataset (P1.1 × 3 + P1.2 × 2) — **đạt tất cả**.
   Nếu không, dataset chưa đủ khó và mọi kết luận sau đó không dùng được.
3. `python demo/verify_figures.py` — mọi hình được tham chiếu đều tồn tại, không
   còn hình mồ côi trong `paper/figures/`.
4. Đối chiếu **từng con số** trong `main.tex` với JSON trong
   `demo/results/tables/`. Không con số nào trong bài mà không truy được về một
   file JSON. Ghi bảng truy vết (số trong bài → file JSON → khoá).
5. `pdflatex` + `bibtex` 2 lượt: 0 lỗi, 0 float-too-large, 0 overfull > 5pt,
   0 tham chiếu `??`.
6. Đếm trang: 12–16 trang LNCS kể cả tài liệu tham khảo.
7. Rà lần cuối 3 danh sách:
   - Mọi tuyên bố trong abstract có **đúng một** bảng/hình/bổ đề chống lưng.
   - Không còn: "51×", "Using Edge AI" trong tiêu đề, tuyên bố phát hiện tin giả
     không kèm AUC có điều kiện, "giảm 55%" không kèm giải thích số học.
   - Mọi mục §1–§10 của phản biện có một chỗ trong bài trả lời (dùng bảng truy vết
     0.3).
8. Ghi báo cáo `loop/loop10/` gồm `review_report.md` + `resolution_plan.md` theo
   đúng dạng 9 vòng trước, để giữ nhật ký phản biện liên tục.

## Rủi ro cần biết trước

| Rủi ro | Xác suất | Xử lý đã chuẩn bị |
|---|---|---|
| **`S_context` vẫn trơ trên dữ liệu chồng lấn** | Trung bình | Nhánh dự phòng P3.3: bỏ `S_context`, định vị quanh `S_geo · S_temp` + hàm ưu tiên. Bổ đề 1 **không** phụ thuộc `S_context` nên đóng góp chính vẫn còn. |
| **`C_i` vẫn kém hơn `n_corrob` một mình** | Cao | P3.4 đã định nghĩa cách phát biểu trung thực: `C_i` là quy ước tổng hợp giải thích được, không phải detector tốt hơn. Cân nhắc rút hẳn khỏi tuyên bố, giữ như thành phần hệ thống. |
| **ARI tụt mạnh trên dữ liệu khó** | Cao (và là **mong đợi**) | Đây là dấu hiệu dataset đã đo được phương pháp. Chuẩn bị viết bài quanh Bổ đề 1 + so sánh **tương đối** với baseline, không quanh ARI tuyệt đối. |
| **HDBSCAN/Agglomerative khớp gating trên `*_labeled`** | Cao | P3.2: chuyển lập luận sang số tham số phải hiệu chuẩn (HDBSCAN cần `min_cluster_size`, Agglomerative cần `n_clusters` — gating chỉ cần θ trong một dải rộng theo Bổ đề 1). |
| **Không tìm được trích dẫn cho dạng cộng** | Trung bình | P4.3 nhánh 2: phát biểu lại là baseline tự dựng, bỏ mọi hàm ý "đánh bại hiện có". |
| **Không kịp dữ liệu thật** | Trung bình | P1.5 là hạng mục phụ theo quyết định 0. Nêu rõ trong Threats to Validity, không hứa. |
| **Vượt 16 trang** | Trung bình | P5.3 đã có kế hoạch gộp; nếu vẫn vượt, chuyển 1B–1H và Thí nghiệm 3/11 sang phụ lục trực tuyến. |

## Đường găng

```
P0.1 Bổ đề 1  ──────────────────────────────┐
                                            ├─→ P5 viết bài ─→ P6
P1.1 + P1.2 generator ─→ P3.1 kiểm độ khó ──┤
        (nếu không đạt: lặp lại P1)          │
P2.2 quy ước đường kính ─→ P3.2 ─────────────┤
P4 văn liệu (song song) ─────────────────────┘
```

Việc **phải làm đầu tiên** và cũng rẻ nhất: P0.1 (Bổ đề 1) và P4.1 (thêm trích
dẫn). Hai việc này không cần chạy lại gì, và chúng quyết định bài có một tuyên bố
dương tính hay không. P1 là hạng mục dài nhất và mọi con số phụ thuộc vào nó.
