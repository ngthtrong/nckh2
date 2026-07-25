# Loop 15 — Báo cáo Phản biện (Step 1)

**Vai trò:** Giáo sư chủ tịch hội đồng phản biện. Loop 14 đã soi `metrics.py`/`baselines.py` (tầng **đo lường**). Loop 15 đi vào tầng còn lại chưa ai soi kỹ: **`priority.py` — hàm ưu tiên $\mathcal{P}(C_k)$**, tức chính đóng góp phương pháp thứ hai của bài. Câu hỏi trung tâm: *công thức ưu tiên được in trong bài có phải công thức được chạy, và những tuyên bố về miền giá trị / chế độ chuẩn hoá có đúng không?*

Phạm vi: `demo/pipeline/priority.py`, `config.py`, `exp1_formula_validation.py` (mục 1B/1C), `exp5_ranking_stability.py`, `exp7_equity_outcome.py`, và §4.4 + Exp1C + Exp7 của `main.tex`.

Phương pháp: chạy trực tiếp `score_clusters()` với từng cấu hình rồi đối chiếu từng mệnh đề trong bài. Không suy đoán.

---

## CHẤT VẤN 15.1 — Dạng cộng in trong bài KHÔNG phải dạng cộng được chạy (NGHIÊM TRỌNG — tái lập)

**Bài báo, `main.tex` dòng 482** (Exp7) định nghĩa ba chính sách so sánh:
> "...compare three priority policies: the full multiplicative $\mathcal{P}=\mathcal{V}_{agg}\cdot(\dots)$, an additive variant $\mathcal{P}=\mathcal{V}_{agg}+(\dots)$, and a vulnerability-blind policy."

**Mã thực thi, `priority.py`:**
```python
if normalize_v:
    priority = v_agg * core
else:
    # dạng cộng ngây thơ (ablation): V góp một số hạng cộng
    priority = core + (v_agg - 1.0)
```

Dạng cộng được chạy là $\mathcal{P}_{add} = \text{core} + (\mathcal{V}_{agg}-1)$, **không** phải $\mathcal{V}_{agg} + \text{core}$. Hai biểu thức lệch nhau đúng một hằng số $1$:

| | Biểu thức | Miền giá trị đo được |
|---|---|---|
| Bài in (dòng 482) | $\mathcal{V}_{agg} + \text{core}$ | $[1{,}1067;\ 2{,}6893]$ |
| Mã chạy | $\text{core} + (\mathcal{V}_{agg}-1)$ | $[0{,}1067;\ 1{,}6893]$ |

**Kiểm chứng số cụ thể** (cụm S2, `exp1_C_v_multiplier.json`: `v_agg=1,7616`, `core=0,6045`):
- Mã: $0{,}6045 + 0{,}7616 = 1{,}3661$ ✓ khớp `P_add` trong JSON và con số **1,37** in ở dòng 364.
- Bài in: $1{,}7616 + 0{,}6045 = 2{,}3661$ ✗ không khớp gì cả.

**Mức độ ảnh hưởng — cần nói chính xác, không thổi phồng:** tôi đã kiểm, hai dạng **cho cùng thứ hạng** (Kendall's $\tau = 1{,}000000$ giữa chúng trên cả 74 cụm), vì chúng chỉ lệch một phép dịch hằng số. Nên **mọi con số Exp7 và Exp1C vẫn đúng** — đây là lỗi **công bố công thức**, không phải lỗi số liệu. Nhưng nó vẫn nghiêm trọng vì:
1. Một reviewer cài lại theo đúng công thức in trong bài sẽ được $\mathcal{P}_{add}$ khác (dịch $+1$), và tuy thứ hạng trùng, **con số 1,37 in ở dòng 364 sẽ không tái lập được**.
2. Tệ hơn về mặt lập luận: chính bài ở dòng 272 lập luận *"An additive term bounded in $[1,2]$ would only add a near-constant offset---amplifying nothing."* Dạng thực chạy $(\mathcal{V}_{agg}-1)\in[0,1]$ **đúng là** một offset — nên lập luận này khớp mã. Nhưng công thức in ở dòng 482 lại là dạng $[1,2]$, tức bài **tự mô tả sai chính cái mà nó phê phán**, ở hai chỗ khác nhau, bằng hai công thức khác nhau.

**Câu hỏi gay gắt:** Dạng cộng dùng làm đối chứng cho toàn bộ luận điểm "khuếch đại nhân" là dạng nào? Bài in một dạng ở §4.4 (offset $[0,1]$, ngầm định), một dạng khác ở Exp7 ($[1,2]$), và mã chạy dạng thứ nhất. Một trong hai câu trong bài phải sai.

---

## CHẤT VẤN 15.2 — Chế độ chuẩn hoá $N_{\max}$ dùng cho mọi kết quả KHÔNG được công bố (TRUNG BÌNH — tái lập)

`main.tex` dòng 258 mô tả hai chế độ nhưng **không nói dùng cái nào**:
> "where $N_{\max}$ is a reference. A \emph{dynamic} reference (largest current-window cluster) gives instantaneous relative ranking; a \emph{fixed} reference is needed for across-time comparison. The dynamic mode is non-stationary and must be interpreted accordingly."

Mã: `n_ref: float | None = None`, và mặc định `None` → **chế độ ĐỘNG** ($N_{\max}$ = dân số cụm lớn nhất trong lần chạy). Kiểm chứng: đúng **1 trong 74** cụm có $\widetilde{\mathcal{N}} = 1{,}0$ — dấu hiệu đặc trưng của mốc động.

**Vì sao quan trọng:** bài tự nói chế độ động là "non-stationary and must be interpreted accordingly", rồi **báo cáo toàn bộ số liệu ưu tiên bằng chính chế độ đó mà không nói ra**. Mọi giá trị $\mathcal{P}$ in trong bài (1,54 ở §1B; 1,06/1,37 ở §1C; toàn bộ Exp5, Exp7) là số của chế độ động. Reviewer nào cài mốc tĩnh sẽ ra số khác. Đây là tham số bắt buộc phải công bố, và bài thậm chí **không liệt kê nó trong Bảng 2** (bảng "Complete parameter set" — tự nhận là đầy đủ).

---

## CHẤT VẤN 15.3 — Tuyên bố $\mathcal{P}(C_k)\in[0,2)$ đúng về mặt chặn nhưng gây hiểu sai về thang đo thực (NHỎ–TRUNG BÌNH)

`main.tex` dòng 282: *"multiplying by $\mathcal{V}_{agg}\in[1,2)$ bounds $\mathcal{P}(C_k)\in[0,2)$---convenient for ranking."*

Chặn toán học **đúng** (đã kiểm: $\sum\omega = 1{,}0000$, core $\in[0,1]$). Nhưng giá trị thực tế đạt được:
```
core:  max = 0,8808  (không phải ~1)
P:     min = 0,1067   max = 1,5408  (không phải ~2)
```
Bài in "$[0,2)$" ba lần như một tính chất hữu ích, trong khi nửa trên của khoảng **không bao giờ được dùng tới**. Không sai, nhưng một phản biện sẽ hỏi: nếu miền $[0,2)$ là "convenient for ranking", tại sao giá trị lớn nhất quan sát được chỉ 1,54? Nên nêu miền **đạt được** bên cạnh chặn lý thuyết.

---

## CHẤT VẤN 15.4 — 61 singleton được tính điểm ưu tiên như cụm thật, không ai nói (TRUNG BÌNH)

`score_clusters()` chấm điểm **mọi** nhãn, kể cả 61 singleton mà chính bài mô tả là "fake reports lack strong edges and become singletons" (dòng 245) và "gating … isolates noise as 61 singletons" (dòng 332).

Hệ quả đo được:
- 61/74 cụm được xếp hạng là singleton — tức **82% danh sách ưu tiên là điểm nhiễu bị cô lập**.
- Singleton xếp cao nhất đứng **hạng 11/74**, và $\widetilde{\mathcal{N}}$ của chúng trải $[0{,}0726;\ 0{,}8815]$ — không hề bị loại tự nhiên bởi công thức.
- Bảng ổn định Exp5 và mô phỏng điều phối Exp7 đều chạy trên toàn bộ 74 cụm này, nên **Kendall's $\tau$ được tính trên một danh sách mà 82% phần tử là nhiễu**.

**Đây không phải lỗi tính toán** — top-3 đều là cụm 40 thành viên, nên kết luận không đổi. Nhưng nó là một **quyết định phương pháp chưa được công bố**, và nó làm loãng ý nghĩa của $\tau$: hoán vị giữa hai singleton nhiễu ở hạng 60 và 61 được tính bằng hoán vị giữa hai cụm thật ở hạng 1 và 2. Bài cần nói rõ danh sách ưu tiên gồm những gì, và tốt nhất là báo thêm $\tau$ chỉ trên các cụm nhiều-thành-viên.

---

## CHẤT VẤN 15.5 — Núm $\mu$ đã có trong mã nhưng chưa ai kiểm nó có tác dụng như bài nói (NHỎ)

Loop 11 đã bắt lỗi "$\mu$ không tồn tại trong mã" và nó đã được thêm (`PriorityParams.v_cap_mu`). Nhưng chưa ai **kiểm chứng** mệnh đề ở dòng 279: *"$\mu=1$ disables amplification (pure risk core) and $\mu=2$ recovers the default. A larger $\mu$ can push a small vulnerable-rich cluster above a large healthy one."*

Tôi kiểm:
```
mu=1,0: top P=0,8808  V_agg(top)=1,0    top-3 = [9, 1, 7]
mu=1,5: top P=1,1842  V_agg(top)=1,4309 top-3 = [1, 9, 7]
mu=2,0: top P=1,5408  V_agg(top)=1,8617 top-3 = [1, 7, 9]
```
Mệnh đề **đúng**: $\mu=1$ cho $\mathcal{V}_{agg}=1$ đúng như hứa, và $\mu$ **thật sự đảo thứ hạng** (cụm 9 tụt từ hạng 1 xuống hạng 2 rồi 3 khi $\mu$ tăng). Đây là bằng chứng tốt cho luận điểm "núm đạo đức" — và bài **không dùng nó**. Không phải lỗi, mà là **cơ hội bị bỏ**: bài khẳng định $\mu$ có tác dụng mà không đưa số, trong khi số đã có sẵn và ủng hộ nó.

---

## ĐÃ KIỂM — KHÔNG PHẢI LỖI (giữ nguyên)

- **$\widetilde{\mathcal{N}}$, $\mathcal{E}_{agg}$, $\mathcal{F}_{max}$**: mã khớp chính xác Eq. (11)–(15). $\mathcal{F}_{max}$ nhân $C_i$ **bên trong** `max` ✓ đúng như dòng 266 nhấn mạnh.
- **$\mathcal{V}_{agg} = 1 + (\mu-1)\tanh(\sum V_i / s)$**: khớp Eq. (18) ✓; $s$ mặc định $10$ ✓; $\mu$ mặc định $2$ ✓.
- **$\sum\omega = 0{,}34+0{,}33+0{,}33 = 1{,}0000$** ✓ đúng ràng buộc đã công bố.
- **"67 clusters with no vulnerable individuals ($\mathcal{V}_{agg}=1$)"** (dòng 364) — đếm lại: đúng **67**/74 ✓.
- **"maximum absolute rank shift between the two forms is 1"** (dòng 364) — đo lại: đúng **1** ✓.
- **Sắp xếp giảm dần theo `priority`** ✓ khớp dòng 282.
- **Trọng tâm cụm** = trung bình cộng lat/lng — hợp lý cho điều phối, khớp mô tả "cluster centroid".
- **Exp7 `_severe_vulnerable_weight`**: đã kiểm lại lần nữa, ngưỡng $F>0{,}7$ thật sự độc lập với $V$ và `core` → tuyên bố "neutral metric" đứng vững ✓.

---

## TỔNG KẾT STEP 1

1. **15.1** — Dòng 482 in dạng cộng là $\mathcal{V}_{agg}+\text{core}$; mã chạy $\text{core}+(\mathcal{V}_{agg}-1)$. Thứ hạng trùng ($\tau=1{,}0$) nên **số liệu vẫn đúng**, nhưng con số 1,37 không tái lập được theo công thức in, và bài tự mâu thuẫn với §4.4. NGHIÊM TRỌNG (tái lập).
2. **15.2** — Chế độ $N_{\max}$ **động** được dùng cho mọi kết quả nhưng không công bố, và không có trong Bảng 2 "Complete parameter set". TRUNG BÌNH.
3. **15.4** — 61/74 cụm được xếp hạng là singleton nhiễu; Exp5/Exp7 chạy trên danh sách 82% nhiễu mà bài không nói. TRUNG BÌNH.
4. **15.3** — Miền $[0,2)$ đúng về chặn nhưng thực tế chỉ đạt $[0{,}11;\ 1{,}54]$. NHỎ–TRUNG BÌNH.
5. **15.5** — $\mu$ có tác dụng đo được (đảo top-3) nhưng bài không đưa số. Cơ hội bị bỏ, không phải lỗi. NHỎ.
