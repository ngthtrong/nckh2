# Loop 15 — Kế hoạch Giải quyết (Step 2)

**Vai trò:** Tác giả (giữ tính khách quan). Nguyên tắc loop này: với 15.1 phải chọn **một** dạng cộng và làm cho bài nhất quán với mã ở **cả hai** chỗ; với 15.2/15.4 phải **công bố** quyết định phương pháp đã ngầm dùng; với 15.5 phải **chạy thêm số** thay vì để một mệnh đề không có bằng chứng.

---

## 15.1 — Dạng cộng in ≠ dạng cộng chạy — CHẤP NHẬN, sửa bài theo mã

**Thừa nhận:** Đúng. Bài có hai mô tả khác nhau cho cùng một đối chứng:
- §4.4 dòng 272: "An additive term bounded in $[1,2]$ would only add a near-constant offset" → ngụ ý $\mathcal{V}_{agg}$ cộng nguyên.
- Exp7 dòng 482: "$\mathcal{P}=\mathcal{V}_{agg}+(\dots)$" → cộng nguyên $\mathcal{V}_{agg}\in[1,2)$.
- Mã: $\text{core}+(\mathcal{V}_{agg}-1)$, tức cộng phần **khuếch đại** $\in[0,1]$.

**Chọn dạng nào?** Giữ **dạng của mã** và sửa bài. Lý do không phải "cho tiện" mà là toán học: cộng nguyên $\mathcal{V}_{agg}$ thêm một hằng số $1$ vào **mọi** cụm, nên nó tuyệt đối không ảnh hưởng thứ hạng — một đối chứng cộng nguyên là *cùng một hàm xếp hạng* với dạng $\text{core}+(\mathcal{V}_{agg}-1)$, chỉ dịch gốc toạ độ. Dạng trong mã là dạng **đã bỏ hằng số vô nghĩa**, tức dạng cộng *có ý nghĩa nhất* để so. Kiểm chứng: $\tau$ giữa hai dạng $=1{,}000000$ trên cả 74 cụm.

**Nói thẳng điều này trong bài** thay vì im lặng sửa số — nó biến một lỗi thành một luận điểm đúng: *dạng cộng thất bại không vì chọn hằng số dở, mà vì bất kỳ dạng cộng nào cũng chỉ dịch, không khuếch đại.*

**Sửa cụ thể:**

1. **`main.tex` dòng 482** (Exp7):
   - Cũ: "an additive variant $\mathcal{P}=\mathcal{V}_{agg}+(\dots)$"
   - Mới: "an additive variant $\mathcal{P}=(\mathcal{V}_{agg}-1)+(\dots)$, i.e.\ the amplification term $\mathcal{V}_{agg}-1\in[0,1)$ added to the core instead of multiplying it (adding $\mathcal{V}_{agg}$ itself would merely shift every cluster by the constant $1$ and yield an identical ranking, Kendall's $\tau=1.0$, so this is the additive form worth comparing against)"

2. **`main.tex` dòng 272** (§4.4): làm rõ để không mâu thuẫn:
   - Cũ: "An additive term bounded in $[1,2]$ would only add a near-constant offset---amplifying nothing."
   - Mới: "An additive term would only shift the core: adding $\mathcal{V}_{agg}\in[1,2)$ shifts every cluster by a constant plus the amplification term, and adding just $\mathcal{V}_{agg}-1\in[0,1)$ shifts each cluster by an amount independent of its risk. Neither amplifies: a cluster with no risk at all still gains the full vulnerability bonus."

3. **`main.tex` dòng 364** (Exp1C): thêm định nghĩa cạnh con số để 1,37 tái lập được: "$\mathcal{P}_{add}=\text{core}+(\mathcal{V}_{agg}-1)=1.37$".

**Không đụng con số nào** — tất cả đã đúng với mã (S2: $0{,}6045+0{,}7616=1{,}3661\to1{,}37$ ✓).

---

## 15.2 — Chế độ $N_{\max}$ động không công bố — CHẤP NHẬN, công bố + đưa vào bảng tham số

**Thừa nhận:** Đúng, và đây là lỗi tái lập thật: bài mô tả hai chế độ, dùng một chế độ, không nói cái nào, và Bảng 2 tự nhận "Complete parameter set" mà thiếu nó.

**Sửa:**
1. **`main.tex` dòng 258**: thêm câu công bố dứt khoát: "\textbf{All results in this paper use the dynamic reference}, so exactly one cluster per run attains $\widetilde{\mathcal{N}}=1$ and every $\mathcal{P}$ value below is a within-run relative score, not comparable across runs."
2. **Bảng 2 (`tab:params`)**: thêm hàng $N_{\max}$ / "dynamic (largest cluster in window)" / "Population normalization reference" / "Domain (within-run ranking)".

---

## 15.4 — 61/74 cụm được xếp hạng là singleton, không công bố — CHẤP NHẬN, công bố + đo thêm

**Thừa nhận:** Đúng. Đây là quyết định phương pháp ngầm, và nó làm loãng ý nghĩa $\tau$: một hoán vị giữa hai singleton nhiễu ở hạng 60–61 được tính bằng hoán vị giữa hai cụm thật ở hạng 1–2.

**Phương án — không chọn cách dễ.** Cách dễ là thêm một câu "singletons are included". Cách đúng là **đo $\tau$ trên riêng các cụm nhiều-thành-viên** và báo cả hai, vì đó chính là con số phản biện muốn thấy. Nếu $\tau$ hạn chế **thấp hơn** $\tau$ toàn phần, ta phải báo cáo đúng như vậy — đó là rủi ro thật của phương án này và ta chấp nhận.

**Sửa mã `demo/experiments/exp5_ranking_stability.py`:** thêm cột `mean_kendall_tau_multi` / `min_kendall_tau_multi` — tính $\tau$ chỉ trên các cụm có $\ge2$ thành viên. Chạy lại, ghi JSON, đưa vào Bảng 8.

**Sửa `main.tex` §Exp5:** công bố rõ danh sách ưu tiên gồm 74 cụm trong đó 61 singleton (đúng những điểm nhiễu mà gating cô lập), và báo $\tau$ hạn chế bên cạnh $\tau$ toàn phần.

---

## 15.3 — Miền $[0,2)$ vs miền đạt được — CHẤP NHẬN, thêm miền quan sát

**Sửa `main.tex` dòng 282:** sau tuyên bố chặn, thêm: "On this dataset the attained range is narrower---$\mathcal{P}\in[0.11,1.54]$ with a maximum core of $0.88$---because no cluster maximizes all three risk components at once; the bound matters for guaranteeing comparability, not as a claim that the upper half of the interval is reachable."

Không sửa chặn lý thuyết (nó đúng).

---

## 15.5 — $\mu$ có tác dụng nhưng bài không đưa số — CHẤP NHẬN, chạy thêm và báo cáo

**Thừa nhận:** Bài khẳng định "$\mu=1$ disables amplification… A larger $\mu$ can push a small vulnerable-rich cluster above a large healthy one" mà **không có bằng chứng**. Số đã có sẵn và ủng hộ mệnh đề — không đưa vào là bỏ mất một luận điểm hợp lệ, và để lại một khẳng định không nguồn.

**Thêm vào `demo/experiments/exp1_formula_validation.py`** một mục quét $\mu\in\{1{,}0;\ 1{,}25;\ 1{,}5;\ 1{,}75;\ 2{,}0\}$, ghi `exp1_H_mu_policy.json`: với mỗi $\mu$ báo $\mathcal{V}_{agg}$ của cụm dẫn đầu, $\mathcal{P}$ đỉnh, top-3 và Kendall's $\tau$ so với $\mu=2$.

**Số đã kiểm trước** (JSON sẽ xác nhận): $\mu=1$ → top-3 $=[9,1,7]$; $\mu=1{,}5$ → $[1,9,7]$; $\mu=2$ → $[1,7,9]$. Tức $\mu$ **thật sự đảo thứ hạng trong top-3** — đúng như bài nói.

**Sửa `main.tex` §4.4 (đoạn "Adjustable amplification cap")**: thêm một câu với số thật, biến khẳng định thành kết quả.

---

## KHÔNG SỬA — nêu rõ để loop sau không lật lại

- **Vẫn chấm điểm cả singleton** (không loại chúng khỏi $\mathcal{P}$). Lý do: một singleton *có thể* là một sự kiện thật chưa được củng cố, và loại nó khỏi danh sách ưu tiên bằng quy tắc cứng là một quyết định vận hành nguy hiểm (bỏ sót người). Cách xử lý đúng là **công bố** và đo thêm (15.4), không phải lọc âm thầm.
- **Trọng tâm cụm bằng trung bình cộng** (không dùng trung vị / trọng tâm có trọng số theo $N_i$): hợp lý ở quy mô sub-km của cụm gating, và đổi nó sẽ đổi Exp7. Không có lỗi để sửa.
- **Chặn $\mathcal{P}\in[0,2)$**: đúng toán học, giữ; chỉ bổ sung miền đạt được.

---

## THỨ TỰ THỰC THI (Step 3)

1. `exp5_ranking_stability.py`: thêm $\tau$ hạn chế trên cụm $\ge2$ thành viên.
2. `exp1_formula_validation.py`: thêm mục quét $\mu$ → `exp1_H_mu_policy.json`.
3. Chạy lại `exp5`, `exp1`. Đọc JSON mới, **không đoán số**.
4. `main.tex`: dòng 258 (+công bố mốc động), Bảng 2 (+hàng $N_{\max}$), dòng 272, 282 (+miền đạt được), 364, §4.4 $\mu$ (+số thật), 482, §Exp5 (+$\tau$ hạn chế + công bố 61 singleton), Bảng 8.
5. Đồng bộ `resource/BaiBao_NoiDung.md` + `resource/Paper.md`.
6. `verify_figures.py`; chạy lại `make_figures.py` nếu hình đổi.
7. Biên dịch `xelatex → bibtex → xelatex ×2`: yêu cầu 0 overfull, 0 undefined ref, 0 multiply-defined.

---

## NHẬT KÝ THỰC THI (Step 3 — đã hoàn tất)

| # | Việc | Trạng thái |
|---|---|---|
| 1 | `priority.py`: viết lại chú thích nhánh cộng, nêu rõ nó là `core + (V_agg-1)` **không** phải `V_agg + core`, và hai dạng **tương đương thứ hạng** | ✅ |
| 2 | `exp1_formula_validation.py`: thêm `exp_h_mu_policy()` quét $\mu\in\{1;1{,}25;1{,}5;1{,}75;2\}$ → `exp1_H_mu_policy.json` | ✅ |
| 3 | `exp5_ranking_stability.py`: thêm $\tau$ **hạn chế** trên cụm $\ge2$ thành viên (`subset=multi`) | ✅ |
| 4 | Chạy lại `exp1`, `exp5` — cả hai exit 0, JSON mới đã ghi | ✅ |
| 5 | `main.tex`: 6 chỗ công bố (mốc $N_{\max}$ động, dạng cộng thật, miền $\mathcal{P}$ đạt được, $\mu$ có số thật + bảng mới, Bảng 8 + 2 cột $\tau$ hạn chế, §Exp5 công bố 61 singleton) | ✅ |
| 6 | Đồng bộ `BaiBao_NoiDung.md` (3 chỗ) + `Paper.md` (4 chỗ) | ✅ |
| 7 | `verify_figures.py` → **ĐẠT** (5/5 hình khớp MD5) | ✅ |
| 8 | Biên dịch xelatex×3 + bibtex: **0 overfull, 0 undefined, 0 multiply-defined**, 27 trang | ✅ |

**Số liệu MỚI đưa vào bài (đều từ JSON vừa sinh, không con số nào bịa):**

| | Giá trị |
|---|---|
| $\mu=1$: top-1 / $\mathcal{P}$ | cụm **9** / **0,8808** |
| $\mu=1{,}5$: top-1 / $\mathcal{P}$ | cụm **1** / **1,1842** |
| $\mu=2$: top-1 / $\mathcal{P}$ | cụm **1** / **1,5408** |
| $\tau$ vs $\mu{=}2$ | 0,9889 ($\mu{=}1$) → 1,0 ($\mu{=}2$) |
| $\tau$ hạn chế ±0,05 / ±0,10 / ±0,20 | **0,9858 / 0,9737 / 0,9442** (min 0,9487 / 0,8974 / 0,7949) |
| Số cụm $\ge2$ thành viên | **13** trong 74 |
| Miền $\mathcal{P}$ đạt được | **[0,1067; 1,5408]** (không phải cả $[0,2)$) |

**Phát hiện đáng chú ý — hai kết quả đi NGƯỢC kỳ vọng của chính báo cáo phản biện, và ta báo cáo đúng như đo được:**

1. **$\mu$ THỰC SỰ đảo được đỉnh bảng.** Chất vấn 15.4 dự đoán $\mu$ có thể là núm vô hiệu. Ngược lại: tại $\mu\le1{,}25$ cụm dẫn đầu là **cụm 9** (lõi rủi ro cao nhất 0,8808, $\mathcal{V}_{agg}=1$); từ $\mu\ge1{,}5$ **cụm 1** vượt lên (lõi thấp hơn 0,8276 nhưng $\mathcal{V}_{agg}$ tới 1,8617). Đây đúng là hành vi bài báo tuyên bố cho núm đạo đức, và giờ **đã có bằng chứng** thay vì chỉ có lời.
2. **$\tau$ hạn chế CAO hơn $\tau$ toàn cục** (0,9737 vs 0,9552 ở ±0,10), không thấp hơn như chất vấn 15.3 lo. Nghĩa là đám 61 singleton **không** thổi phồng độ ổn định; phần danh sách điều phối thực dùng còn bền hơn tổng thể. Vẫn phải công bố cả hai + con số 13 cụm, vì người đọc có quyền biết "74 cụm" gồm 82% singleton.

**Không đổi (đã xác nhận):** mọi con số ARI/NMI/đường kính; `exp5_scale_stability`, `exp5_structural_stability`; toàn bộ exp4/exp9/exp12; hạng của S2 (vẫn hạng 5); độ dịch hạng tối đa (vẫn 1).
