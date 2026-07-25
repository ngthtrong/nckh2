# Loop 13 — Báo cáo Phản biện (Step 1)

**Vai trò:** Giáo sư chủ tịch hội đồng phản biện. Loops 9–12 đã dọn số liệu, công thức–mã, và học thuật vụ. Loop 13 soi tầng chưa ai chạm: **hình vẽ, bảng biểu, và tính tái lập của artifact trình bày**. Câu hỏi trung tâm: *hình trong bài có đúng là hình mà code hiện tại sinh ra không?*

Phạm vi: `paper/figures/`, `demo/results/figures/`, `make_figures.py`, caption và bảng trong `main.tex`, log build LaTeX.

---

## CHẤT VẤN 13.1 — Hình 7 trong bài là hình **CŨ**, không phải hình mà code sinh ra (NGHIÊM TRỌNG — phá vỡ tuyên bố tái lập)

**Bằng chứng bằng checksum:**

| File | MD5 | Kích thước |
|---|---|---|
| `demo/results/figures/fig7_ranking_stability.png` | `4fed5f9d…` | 50.749 B |
| `paper/figures/fig7_ranking_stability.png` | `9bae869d…` | 58.361 B |

Sáu hình còn lại (`fig1`, `fig2`, `fig3`, `fig4`, `fig5`, `fig6`) **khớp checksum tuyệt đối** giữa hai thư mục. Chỉ `fig7` lệch.

**Kiểm chứng bằng cách chạy lại code:** chạy `make_figures.py` với mã hiện tại → `demo/results/figures/fig7` giữ nguyên MD5 `4fed5f9d…`, tức **code hiện tại sinh ra đúng bản trong `demo/`**, còn bản trong `paper/` là artifact tồn đọng từ một phiên bản code trước.

**Khác biệt không phải cosmetic — hai hình khác hẳn loại biểu đồ:**
- Bản `demo/` (đúng, hiện hành): **biểu đồ cột** — nhóm cột theo ba mức nhiễu ±0,05 / ±0,10 / ±0,20, hiển thị mean τ và min τ, cộng nhãn "top-3: 100%" ở cả ba mức.
- Bản `paper/` (cũ, đang được biên dịch vào PDF): **biểu đồ đường** với trục và cách trình bày khác.

**Vì sao đây là lỗi nghiêm trọng:** mục Reproducibility (dòng 553) khẳng định `run_all.py` "writes one JSON file per experiment **plus every figure in this paper**" và "a reviewer re-running the suite obtains **identical values, not merely similar ones**". Nhưng một reviewer chạy lại suite sẽ nhận được **một hình khác** với hình in trong bài. Đây đúng là loại lỗi mà tuyên bố tái lập tồn tại để loại bỏ, và nó tự bác bỏ chính câu tuyên bố đó.

Thêm nữa, bản cũ có thể mang **số liệu cũ**: loop 10 đã ghi nhận Exp5 từng có bộ số cũ (τ 0,994/0,986/0,957, top-3 chỉ 76,5–99%) trước khi đồng bộ sang bộ hiện hành (0,9789/0,9552/0,9111, top-3 **100%** cả ba mức). Nếu `paper/fig7` là hình vẽ từ bộ số cũ thì bài đang **in một hình mâu thuẫn với Bảng 8 ngay bên cạnh nó**.

---

## CHẤT VẤN 13.2 — Caption Hình 7 nói "essentially unchanged", dữ liệu nói "100%" (TRUNG BÌNH, hệ quả 13.1)

`main.tex` dòng 463:
> "Ranking stability: Kendall's $\tau$ stays above $0.93$ at realistic perturbation ($\pm0.05$--$\pm0.10$), with the top-3 clusters **essentially unchanged**."

Hai vấn đề:
1. **"essentially unchanged" là hạ thấp kết quả thật.** `exp5_ranking_stability.json` ghi `top3_set_preserved_pct: 100.0` ở **cả ba** mức. Thân bài (dòng 466) nói đúng: "the top-3 clusters are preserved in **100% of all 600 trials**". Caption dùng chữ mơ hồ trong khi con số là tuyệt đối — caption nên nói thẳng 100%.
2. **"stays above 0.93"** đúng cho ±0,05 (0,9789) và ±0,10 (0,9552) ✓, nhưng ngưỡng 0,93 là con số của bộ dữ liệu **cũ** (mức min τ cũ là 0,937). Với bộ hiện hành, mức chặn tự nhiên là **0,91** (min τ ±0,10 = 0,9104) — và đó chính là con số Abstract và thân bài dùng. Caption vì thế lệch với ba chỗ khác trong cùng bài.

---

## CHẤT VẤN 13.3 — Hai hình được sinh ra nhưng **không dùng** trong bài, trong khi bài mô tả chúng (TRUNG BÌNH)

`demo/results/figures/` chứa 7 hình; `main.tex` chỉ `\includegraphics` **5** hình:

| Hình | Dùng trong main.tex? |
|---|---|
| fig1_ablation | ✅ |
| fig4_sigma_sweep | ✅ |
| fig5_resolution_sweep | ✅ |
| fig6_baselines | ✅ |
| fig7_ranking_stability | ✅ |
| **fig2_map** | ❌ **không dùng** |
| **fig3_heatmap** | ❌ **không dùng** |

Bản thân việc không dùng hết hình là hợp lệ (giới hạn trang LNCS). Nhưng:
- `paper/figures/` vẫn **chứa** cả `fig2_map.png` (238 KB) và `fig3_heatmap.png` (117 KB) — 355 KB artifact chết trong thư mục nộp bài.
- Nghiêm trọng hơn: **BaiBao §5.14** (đã viết ở loop 10) mô tả **bảy** hình như thể tất cả đều minh họa bài báo. Trong khi bản tiếng Anh — bản thực sự nộp — chỉ dùng 5. Bản Việt cũng nhắc "dashboard bản đồ Leaflet" nhưng `main.tex` **không hề đề cập** dashboard ở đâu cả. Đây là lệch nội dung giữa hai artifact mà loop 10 chưa bắt được.

---

## CHẤT VẤN 13.4 — Hình 1 caption mô tả panel (b) bằng con số nhưng thiếu ngữ cảnh gate (NHỎ)

Dòng 357: "(b) The confidence gate reduces the fake report's claimed population of 200 to an effective **90**."

Đúng số (`exp1_E`: 200 → 90,0, giảm 55,0%) ✓. Nhưng caption không nêu **55%** — con số mà Abstract, Kết luận và §1E đều dùng làm headline. Người đọc xem hình sẽ không nối được với con số 55% ở ba chỗ khác. Chỉnh nhẹ để nhất quán.

---

## CHẤT VẤN 13.5 — Hai overfull hbox còn tồn (NHỎ, trình bày)

Build log ghi đúng **2** overfull:
```
Overfull \hbox (4.56pt too wide) at lines 115--116   ← Gap 2, "travel distance/time [[]]"
Overfull \hbox (6.76pt too wide) at lines 175--175   ← nhãn TikZ (L,T,F,E,N,V,C)
```
Cả hai đều nhỏ (<7pt) và không gây tràn thấy được, nhưng LNCS yêu cầu bản sạch. Cái thứ hai nằm trong hình TikZ (nhãn `text width=20mm` quá chật cho công thức) — dễ sửa bằng cách nới `text width`.

---

## ĐÃ KIỂM — KHÔNG PHẢI LỖI (giữ nguyên)

- **Cân đối label/ref hoàn hảo:** 5 label hình + 10 label bảng, **tất cả** đều được `\ref` ít nhất một lần; không có label mồ côi, không có `\ref` treo. Build: **0 undefined reference**, **0 multiply-defined label** (lỗi trùng `sec:exp5` đã sửa ở loop 9).
- **6/7 hình khớp checksum** giữa `demo/results/figures/` và `paper/figures/` → quy trình đồng bộ hình về cơ bản hoạt động, chỉ `fig7` bị bỏ sót.
- **Số hình trong `demo/results/figures/` = 7**, khớp mô tả "Bảy hình PNG" ở BaiBao ✓ (đã kiểm ở loop 10, xác nhận lại).
- **Caption Hình 6** (`fig:baselines`): "HDBSCAN wins on ARI ($1.0$) but with a $55.7$ km mean diameter; Louvain/Leiden/Agglomerative … are the only methods that combine near-perfect ARI with sub-kilometre diameter, and only Louvain/Leiden achieve it without a preset $K$" — mọi mệnh đề khớp `exp4_baselines.json` ✓, và đã phản ánh đúng chỉnh sửa trung thực của loop 10 (thừa nhận HDBSCAN thắng ARI).
- **Caption Hình 5** (`fig:sweeps`): "ARI plateau over $[400,1000]$ m … $\lambda$ safe within $[0.5,2.0]$ and collapses at $\lambda=3.0$" ✓ khớp `exp2_sigma_geo.json` và `exp2_resolution.json` (đúng khoảng $[0{,}5;2{,}0]$ đã sửa, không phải $[0{,}5;1{,}5]$ cũ).
- **Mọi caption bảng** (Bảng 1–10) đã đối chiếu: chú thích "Mean diam. averages only clusters with $\ge2$ members", "Noise abs. is the fraction of `gt`$=-1$ events absorbed", "V-measure is their harmonic mean", "Wins is the percentage of seeds" — tất cả khớp định nghĩa trong `metrics.py` và JSON ✓.
- `\emergencystretch=1.5em` + `\hbadness=4000` đã được đặt để xử lý dòng math dài — lựa chọn hợp lý, giữ.
- PDF build: **25 trang**. LNCS thường giới hạn 12–18 trang cho full paper; đây là vấn đề **phạm vi nộp bài** cần nhóm tác giả quyết định theo call-for-papers cụ thể, **không phải lỗi kỹ thuật** → chỉ ghi nhận, không tự ý cắt.

---

## TỔNG KẾT STEP 1

1. **13.1** — `paper/figures/fig7_ranking_stability.png` là **hình cũ** (MD5 khác, khác cả loại biểu đồ: đường vs cột), không phải hình mà `make_figures.py` hiện tại sinh ra. **Phá vỡ trực tiếp** tuyên bố Reproducibility ("every figure in this paper", "identical values"). NGHIÊM TRỌNG.
2. **13.2** — Caption Hình 7 nói "top-3 essentially unchanged" (thực tế **100%**) và dùng ngưỡng **0,93** của bộ dữ liệu cũ (hiện hành là **0,91**), lệch với Abstract + thân bài + Kết luận. TRUNG BÌNH.
3. **13.3** — `fig2_map` và `fig3_heatmap` được sinh nhưng không dùng trong `main.tex`, vẫn nằm trong `paper/figures/` (355 KB chết); BaiBao §5.14 lại mô tả cả 7 hình + dashboard mà bản tiếng Anh không có. TRUNG BÌNH.
4. **13.4** — Caption Hình 1(b) thiếu con số **55%** vốn là headline ở ba chỗ khác. NHỎ.
5. **13.5** — 2 overfull hbox (4,56pt và 6,76pt) còn tồn. NHỎ.
