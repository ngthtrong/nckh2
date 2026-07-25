# Loop 9 — Báo cáo Phản biện (Step 1)

**Vai trò:** Giáo sư chủ tịch hội đồng phản biện. Loops 1–8 đã dọn miền giá trị, trích dẫn, xref, faithfulness số liệu và các mệnh đề nhân-quả. Nhưng bài báo **đã được viết lại rất nhiều** sau loop 8 (bộ dữ liệu mới 341 sự kiện / 14 nhãn, thêm Exp11, Exp12). Loop 9 vì thế soi lại **tính đối chiếu số liệu giữa `paper/main.tex` và `demo/results/tables/*.json`** trên toàn bộ phiên bản mới, cộng với tính nhất quán ba-artifact.

Phương pháp: đọc trực tiếp từng file JSON trong `demo/results/tables/` và đối chiếu từng con số trong bài. Không suy đoán.

---

## CHẤT VẤN 9.1 — Exp3 nói "20 seeds" nhưng code chỉ chạy **10 seeds** (NGHIÊM TRỌNG — số liệu không kiểm chứng được)

**Nơi xuất hiện:** `paper/main.tex` dòng 402:
> "Across **20 seeds**, both Louvain and Leiden yield zero badly-connected communities... leaving **13 evaluable communities per seed** (**130** over the 20 seeds)"

**Bằng chứng từ code:**
- `demo/experiments/exp3_louvain_vs_leiden.py` dòng 20: `SEEDS = [1, 7, 13, 42, 99, 123, 256, 512, 1024, 2026]` → **10 seed**, không phải 20.
- `demo/results/tables/exp3_per_seed.json` chứa đúng **10 bản ghi**.
- `exp3_summary.json`: `total_clusters_evaluated: 130`.

**Số học tự tố giác chính nó:** bài nói 13 cộng đồng/seed và tổng 130. Nhưng $13 \times 20 = 260 \neq 130$. Chính xác là $13 \times 10 = 130$. Vậy con số 130 (đúng, khớp JSON) **mâu thuẫn nội tại** với "20 seeds" trong cùng một câu.

**Câu hỏi gay gắt:** Tại sao lại khai 20 seed cho một thí nghiệm mà file kết quả chỉ có 10 dòng? Đây không phải lỗi làm tròn — đây là **phóng đại quy mô thực nghiệm gấp đôi**, đúng loại lỗi mà một phản biện coi là nghi vấn về tính trung thực. Nghi vấn hợp lý: khi Exp12 được thêm vào với `N_SEEDS = 20`, con số 20 đã bị "chảy" sang phần Exp3 mà không ai kiểm lại.

---

## CHẤT VẤN 9.2 — Exp11: mô tả bằng lời **trái ngược** với chính bảng số của nó (NGHIÊM TRỌNG)

**Nơi xuất hiện:** `main.tex` dòng 507:
> "the empirical growth of the build stage stays **below the quadratic prediction at every step** (e.g.\ a $20.2\times$ increase where quadratic scaling predicts $12.4\times$ is exceeded only in the smallest step, and by $n=7181$ the observed $5.6\times$ tracks the predicted $4.0\times$)"

**Bằng chứng từ `exp11_scaling.json`:**

| $n$ | quan sát (`build_time_ratio_vs_prev`) | dự đoán bậc hai (`expected_ratio_if_quadratic`) | quan sát so với dự đoán |
|---|---|---|---|
| 1201 | 20,15× | 12,4× | **CAO HƠN** |
| 3581 | 11,26× | 8,89× | **CAO HƠN** |
| 7181 | 5,55× | 4,02× | **CAO HƠN** |

Cả **ba** bước đều **vượt** dự đoán bậc hai, không bước nào nằm dưới. Câu trong bài nói "stays below the quadratic prediction at every step" là **sai ở mọi điểm dữ liệu**. Cụm "is exceeded only in the smallest step" cũng sai: nó bị vượt ở **cả ba** bước. Và "the observed $5.6\times$ **tracks** the predicted $4.0\times$" — 5,55 vs 4,02 là lệch **38%**, không thể gọi là "tracks".

**Mức độ nghiêm trọng:** đây là một khẳng định về **độ phức tạp tính toán** — điều mà bất kỳ phản biện kỹ thuật nào cũng kiểm ngay bằng cách nhìn hai cột số ngay bên dưới. Nó đảo ngược kết luận: dữ liệu cho thấy chi phí build tăng **nhanh hơn** $O(n^2)$ (do hiệu ứng cache/bộ nhớ của ma trận dày), không phải chậm hơn.

**Câu hỏi gay gắt:** Bài đang muốn kể chuyện "scaling tốt hơn lý thuyết", nhưng số liệu của chính bài nói ngược lại. Hãy sửa mệnh đề cho khớp dữ liệu, hoặc bỏ khẳng định.

---

## CHẤT VẤN 9.3 — Sai số liệu trong Bảng 11 (`Build (loop)` tại $n=341$) (TRUNG BÌNH)

`main.tex` dòng 517: `341 & 0.020 & 0.186 & $6.1\times$ ...`

`exp11_scaling.json` (n=341): `build_vec_s: 0.0195`, `build_pure_s: **0.1186**`, `speedup_vec: 6.1`.

Bài in **0.186**, JSON ghi **0.1186**. Kiểm tra tính nhất quán nội bộ: $0{,}186 / 0{,}0195 = 9{,}5\times$, **không** phải 6,1× như cột Speedup ghi. Với giá trị đúng: $0{,}1186/0{,}0195 = 6{,}08 \approx 6{,}1\times$ ✓. Vậy đây là lỗi rơi chữ số "1", và nó làm cột Speedup của chính hàng đó **không còn tự khớp**.

Ngoài ra dòng 519: bài in Louvain $2.194$ s tại $n=3581$; JSON ghi `louvain_s: 2.2551`. Lệch thật (2,194 vs 2,255) và `sparsify_s: 0.6429` bị in thành `0.702`. Cần kiểm và sửa cả hàng.

---

## CHẤT VẤN 9.4 — `max_abs_diff` sai con số (NHỎ nhưng là claim về độ chính xác số học)

`main.tex` dòng 507: "agreeing with it to $<10^{-10}$ (**max absolute difference $7.3\times10^{-11}$**)".

JSON: giá trị $7{,}258\times10^{-11}$ xuất hiện ở $n=3581$; ở $n=341$ là $5{,}83\times10^{-11}$, ở $n=1201$ là $6{,}86\times10^{-11}$. Vậy $7{,}3\times10^{-11}$ đúng là **max trên các n đã đo** — điểm này **KHÔNG sai**. Ghi nhận là đã kiểm, giữ nguyên.

---

## CHẤT VẤN 9.5 — Nhãn `\label{sec:exp5}` bị khai báo **hai lần** trên cùng một dòng (TRÌNH BÀY)

`main.tex` dòng 443:
```latex
\subsection{Experiment 5 --- Ranking Stability (Kendall's $\tau$)}\label{sec:exp5}\label{sec:exp5}
```
LaTeX sẽ phát cảnh báo `Label 'sec:exp5' multiply defined` và bản build hiện tại không sạch. Lỗi copy-paste, phải xóa một cái.

---

## CHẤT VẤN 9.6 — Đánh số thí nghiệm **nhảy** từ 9 sang 11: không có "Experiment 10" (TRÌNH BÀY, gây hoang mang)

Các mục trong bài: Experiment 1, 2, 3, 4, 5, 6, 7, 8, 9, **11**, 12. Không có mục nào tên "Experiment 10".

Thực tế `demo/experiments/exp10_packet_size.py` tồn tại và kết quả của nó **được dùng** trong bài (dòng 554: "105--111 bytes"), nhưng bị nhét vào phần Discussion thay vì thành một mục Experiment. Kết quả: người đọc thấy đánh số 9 → 11 và tưởng một mục bị xóa mất khi biên tập.

**Câu hỏi:** Nếu exp10 là một thí nghiệm thực thụ có JSON riêng (`exp10_packet_size.json`) và được trích dẫn trong bài, tại sao nó không có số mục? Hoặc đánh số lại liên tục, hoặc nói rõ vì sao 10 nằm ở Discussion.

---

## CHẤT VẤN 9.7 — Ba-artifact **lệch hoàn toàn**: bản tiếng Việt vẫn là bộ dữ liệu CŨ (NGHIÊM TRỌNG về nhất quán)

`resource/BaiBao_NoiDung.md` và `resource/Paper.md` vẫn mang toàn bộ số liệu của bộ dữ liệu **285 sự kiện** đã bị thay thế:

| Đại lượng | BaiBao/Paper.md (cũ) | main.tex + JSON (hiện tại) |
|---|---|---|
| Số sự kiện | **285** | **341** |
| ARI gating | **0,892** | **0,9957** |
| Số cụm | **27** | **74** |
| Đường kính TB | **0,30** km | **0,85** km (multi) |
| Additive tốt nhất | 0,892 / 100,07 km | 0,9572 / 140,41 km |
| HDBSCAN | 0,890 / 11 cụm / 25,08 km | **1,0** / 21 cụm / 55,72 km |
| Spectral | 0,339 | **0,1657** |
| K-Means (K=14) | 0,688 | **0,5016** |
| DBSCAN | 0,730 | **0,5234** |
| Exp6 ablation | ARI tụt 0,892→0,7855, τ=0,9829 | **không đổi gì**, τ=**1,0** |
| Exp3 | 10 seed, Q=0,8311 | 10 seed, Q=**0,861** |
| Trần ARI | "do GT áp đặt, nhóm neo tại tâm ốc đảo" | **đã sửa generator**, không còn trần |
| Kendall τ | 0,99 / 0,94 | 0,955 / 0,910 |
| Số nhãn GT | (không nêu) / 264 điểm có nhãn | 14 nhãn / 280 điểm có nhãn |

Đây không phải lệch làm tròn mà là **hai bộ kết quả khác nhau hoàn toàn**. Nghiêm trọng nhất:
1. **Exp6 đảo chiều kết luận.** Bản Việt viết "Bỏ ngữ cảnh **có** làm đổi phân cụm — ARI tụt từ 0,892 xuống 0,7855... khẳng định $\mathcal{S}_{context}$ thực sự hỗ trợ việc gom nhóm". Nhưng `exp6_context_ablation.json` hiện tại: `graph_full_ari = graph_ablate_ari = 0.9957`, `kendall_tau_ranking = 1.0` → ablation **không đổi gì cả**. main.tex đã ghi đúng điều này. Bản Việt đang khẳng định một kết luận **trái ngược** với dữ liệu.
2. **Câu chuyện "trần ARI"** trong bản Việt (§5.2, Threats) dựa trên generator cũ có nhóm kịch bản neo tại tâm ốc đảo. Generator hiện tại đặt mỗi nhóm trên satellite 3 km và có assertion `assert_gt_separable`; `exp1_G_ari_decomposition.json` ghi `n_colocated_narrative_groups: 0`. Toàn bộ lập luận đó đã lỗi thời.
3. **BaiBao dòng 296** nói "mười thí nghiệm `exp1`–`exp10`" — nay thực tế có **mười hai** (`exp1`–`exp12`). Lỗi đếm lặp lại đúng kiểu đã bắt ở loop 7 (khi đó là "chín" vs 10).
4. **BaiBao dòng 394** nói "**Bảy** hình PNG" và liệt kê 7 — con số này vẫn đúng (`demo/results/figures/` có 7 file). Đã kiểm, không sai.

**Câu hỏi gay gắt:** Bản tiếng Việt được tuyên bố là "nguồn sự thật tiếng Việt" của dự án, nhưng hiện nó mô tả một thực nghiệm **không còn tồn tại**. Nếu ai đó đọc bản Việt để hiểu công trình, họ sẽ nhận thông tin sai về gần như mọi con số và **sai cả kết luận của Exp6**. Đây là lỗi nhất quán nặng nhất trong toàn dự án ở thời điểm này.

---

## CHẤT VẤN 9.8 — Abstract nói "cuts diameter" nhưng dùng chỉ số **khác** với bảng (NHỎ, dễ gây nhầm)

`main.tex` dòng 49 (Abstract): "cuts the *worst-case* cluster diameter from **214 km to 1.4 km**".

Đối chiếu: 213,95 km là `max_diam_km` của additive $\alpha=1{,}0$ ✓, và 1,4122 km là `max_diam_km` của gating ✓. **Đúng.** Đã kiểm, giữ nguyên. (Ghi lại để khỏi soi lại vòng sau.)

---

## ĐÃ KIỂM — KHÔNG PHẢI LỖI (giữ nguyên, khỏi soi lại)

Đối chiếu từng con số main.tex ↔ JSON, tất cả khớp:
- Exp1A: bảng 5 dòng (0,8763/0,9161/0,9572/0,9161/0,9957; 151,13/140,41/0,85; 213,95/1,41; 8/9/74) ✓ `exp1_A`.
- Exp1B: 200 người, core thô 66,48, sau chuẩn hóa core 0,83 & $\mathcal{P}=1{,}54$ ✓ `exp1_B` (1,5408).
- Exp1C: S2 $\mathcal{V}_{agg}=1{,}76$, $\mathcal{P}_{add}=1{,}37$, $\mathcal{P}_{mult}=1{,}06$, cùng hạng 5, max rank shift = 1, **67** cụm có $\mathcal{V}_{agg}=1$ trên 74 ✓ (đã đếm lại từ JSON: đúng 67).
- Exp1D: bảng $\tanh$ (1,76/2,00/2,00/2,00/2,00 và 1,10/1,29/1,76/2,00/2,00) ✓.
- Exp1E: $C_i=0{,}4502$, 200→90,0, giảm 55,0% ✓. Exp1F: 0,99→0,4457 ✓.
- Exp1G: ARI lõi 1,0 / kịch bản 0,821 / toàn bộ 0,9957; 240 lõi, 40 kịch bản, 280 có nhãn, 0 nhóm đồng vị trí ✓.
- Exp2: $\sigma_{geo}$ range 0,1205, đỉnh 0,9957 tại [400,1000], 0,9369@1500, 0,9156@2500, 0,8752@4000 (max diam 15,26 km), 200 m → 77 cụm/63 singleton/0,9908 ✓; $\lambda$ range 0,1519, 0,8438@3,0 → 77 cụm ✓; $\beta/\gamma$ range 0,0448, 0,9509@$\beta$=0,9 → 75 cụm ✓; $\tau$ grid phẳng 0,9957 & **74 cụm** toàn lưới ✓; $s$: spread 1,0/0,914 (max 1,914)/0,650 ✓.
- Exp4: toàn bộ 10 hàng bảng baseline ✓ `exp4_baselines`.
- Exp5: 0,9789/0,9526, 0,9552/0,9104, 0,9111/0,8045, top-3 100% × 3 mức × 200 = 600 trials ✓; $s$: $\tau\ge0{,}9985$, =1,0 khi $s\ge10$ ✓; $\sigma_{geo}$: 74 cụm & τ=1,0 đến 900 m, 1200 m → 73 cụm & τ=0,9954 ✓.
- Exp6: 0,9957/0,9933/74/0,1491 hai bên, τ=1,0, top-5 ✓.
- Exp7: 110,2 / 113,5 (+2,9%) / 122,9 (+10,3%), 165,0 vs 246,6 (33%), 2528 vs 2410 ✓.
- Exp8: AUC 0,9176 CI [0,8863; 0,9439], AP 0,3159 CI [0,2577; 0,4063], baseline 0,0674, lift 4,7×, 23 fake/341, mean $C_i$ 0,60 vs 0,89, adversarial 0,45/0,77/0,74/0,92 ✓.
- Exp9: bảng phân rã 5 hàng + spread (0,834/0,372/0,470/0,307) ✓.
- Exp12: toàn bộ 7 hàng bảng multiseed ✓ (lưu ý Modularity additive: JSON 0,7748; bài in **0,7480** → **xem 9.9 dưới**).
- Exp10: 105/110/111 byte ✓.
- Dataset: 341 sự kiện, 14 nhãn ≥0, 240 lõi (6×40), 61 noise `gt=-1` với 23 fake, 41 điểm kịch bản 8 nhóm (100–107) + 1 fake lẻ ✓ — trùng khớp `dataset.json`.

---

## CHẤT VẤN 9.9 — Modularity của additive trong Bảng 12 bị đảo chữ số (TRUNG BÌNH)

`main.tex` dòng 543: `Modularity $Q$ & $0.8612\pm0.0040$ & $0.7480\pm0.0076$ & 100\%`

`exp12_multiseed_summary.json`: gating `0.8612 ± 0.0004`; additive `**0.7748** ± 0.0076`.

Hai lỗi trong một hàng:
1. Additive: bài in **0,7480**, JSON ghi **0,7748** → đảo chữ số (7748 → 7480).
2. Gating sd: bài in **0,0040**, JSON ghi **0,0004** → sai một bậc mười (thổi phồng độ biến động gating lên 10×).

Cả hai đều là số trong bảng chính của thí nghiệm multiseed — nơi phản biện kiểm trước nhất.

---

## TỔNG KẾT STEP 1

**Bốn lỗi số liệu/dữ kiện nghiêm trọng đến trung bình trong `main.tex`** (tất cả kiểm chứng trực tiếp bằng JSON):
1. **9.1** — Exp3 khai "20 seeds", code chạy **10**; tự mâu thuẫn với chính con số 130 trong cùng câu. NGHIÊM TRỌNG.
2. **9.2** — Exp11 mô tả scaling "dưới dự đoán bậc hai ở mọi bước", trong khi cả 3 bước đều **vượt**. NGHIÊM TRỌNG (đảo ngược kết luận về độ phức tạp).
3. **9.3** — Bảng 11 sai `Build (loop)` 0,186 vs **0,1186** (làm cột Speedup tự phá vỡ), cộng `sparsify`/`louvain` hàng $n{=}3581$.
4. **9.9** — Bảng 12 sai Modularity additive 0,7480 vs **0,7748**, và sd gating 0,0040 vs **0,0004**.

**Hai lỗi trình bày:**
5. **9.5** — `\label{sec:exp5}` trùng lặp → cảnh báo LaTeX.
6. **9.6** — đánh số mục nhảy 9 → 11.

**Một lỗi nhất quán ba-artifact rất nặng:**
7. **9.7** — `BaiBao_NoiDung.md` + `Paper.md` vẫn mô tả bộ dữ liệu 285-sự-kiện đã bị thay thế; đặc biệt **kết luận Exp6 bị đảo chiều** so với dữ liệu hiện tại, và câu chuyện "trần ARI do GT" đã lỗi thời.
