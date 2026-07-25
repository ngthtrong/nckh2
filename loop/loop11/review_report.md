# Loop 11 — Báo cáo Phản biện (Step 1)

**Vai trò:** Giáo sư chủ tịch hội đồng phản biện, chuyên môn Toán. Loops 9–10 đã đối chiếu **văn bản ↔ JSON**. Loop 11 đi xuống một tầng sâu hơn, chỗ chưa ai soi: **công thức in trong bài ↔ mã nguồn thực thi trong `demo/pipeline/`**. Một bài báo có thể có mọi con số khớp file JSON mà vẫn sai, nếu **công thức được in không phải công thức được chạy**.

Phạm vi đọc: `weighting.py`, `priority.py`, `attributes.py`, `metrics.py`, `config.py`, `exp7_equity_outcome.py`.

---

## CHẤT VẤN 11.1 — Bảng 9 (phân rã) có V-measure của Louvain **SAI SỐ HỌC** (NGHIÊM TRỌNG)

**Nơi xuất hiện:** `paper/main.tex` dòng 497, Bảng~\ref{tab:decomp}:
```
Louvain / Leiden / Agglom. & 74 & 0.9957 & 0.9867 & 1.0 & 0.9330
```

**Vấn đề:** Chú thích bảng và thân bài đều khẳng định "V-measure is their **harmonic mean**". Kiểm bằng chính định nghĩa đó:
$$V = \frac{2\cdot H\cdot C}{H+C} = \frac{2\times0{,}9867\times1{,}0}{0{,}9867+1{,}0} = \mathbf{0{,}9933}$$

Bài in **0,9330** — đảo hai chữ số của 0,9933. Và `exp9_discriminative_metric.json` ghi `"v_measure": 0.9933` cho cả ba hàng Louvain/Leiden/Agglomerative.

**Mức độ nghiêm trọng cao gấp đôi bình thường**, vì hai lý do:
1. Con số này **tự kiểm chứng được ngay trên trang giấy**: bất kỳ ai lấy H và C ở cùng hàng bấm máy tính đều thấy sai. Đây là loại lỗi làm mất uy tín cả bảng.
2. Bài báo còn khẳng định (dòng 484) V-measure **chính bằng** NMI đã in ở Bảng 1 và Bảng 4 — nơi NMI của Louvain là **0,9933**. Vậy cùng một đại lượng xuất hiện hai giá trị khác nhau trong cùng bài báo: 0,9933 (Bảng 1, Bảng 4) và 0,9330 (Bảng 9). **Tự mâu thuẫn nội tại.**

Kiểm các hàng còn lại của Bảng 9: HDBSCAN 1,0 ✓; Spectral $2(0{,}9978)(0{,}5305)/(1{,}5283)=0{,}6927$ ✓; K-Means $2(0{,}7466)(0{,}7293)/(1{,}4759)=0{,}7378$ ✓; DBSCAN $2(0{,}6277)(0{,}8922)/(1{,}5199)=0{,}7369$ ✓. Vậy **chỉ đúng một ô sai** — nhưng là ô của chính phương pháp đề xuất.

---

## CHẤT VẤN 11.2 — Công thức dạng cộng in trong bài **KHÔNG PHẢI** công thức được chạy (NGHIÊM TRỌNG về tính tái lập)

**Bài in** (`main.tex` dòng 219):
$$w_{ij} = \alpha \mathcal{S}_{geo} + \beta \mathcal{S}_{temp} + \gamma \mathcal{S}_{context}$$
và Bảng 1 liệt kê bốn cấu hình: $\alpha=0{,}34$ / $0{,}5$ / $1{,}0$ / "Normalized $\frac13$-sum".

**Mã nguồn** (`weighting.py` dòng 53–57): `edge_weight_additive` dùng `a_w * geo + p.beta * temp + p.gamma * ctx`, với $\beta=\gamma=0{,}5$ **cố định từ config**, chỉ $\alpha$ thay đổi.

**Hệ quả toán học mà bài không nói:** khi bài ghi "Additive, $\alpha=0{,}34$", công thức thực chạy là
$$w_{ij}=0{,}34\,\mathcal{S}_{geo}+0{,}5\,\mathcal{S}_{temp}+0{,}5\,\mathcal{S}_{context}$$
tức tổng hệ số $=1{,}34\neq1$, và **không phải** "equal thirds" như bài mô tả (dòng 330: "$\alpha=0.34$ (equal thirds)"). Chia đều ba phần thật sẽ là $\alpha=\beta=\gamma=1/3$ — đó lại chính là hàng "Normalized $\frac13$-sum" (hàm `edge_weight_additive_normalized`), một hàng **khác**.

Vậy nhãn "(equal thirds)" ở dòng 330 là **sai**: cấu hình $\alpha=0{,}34$ có $\beta=\gamma=0{,}5$, không chia đều. Tương tự "$\alpha=1.0$ (geography weighted as strongly as the sum of the other two terms)" — đúng, vì $0{,}5+0{,}5=1{,}0$ ✓; câu này không sai, nhưng nó chỉ đúng **nhờ** $\beta=\gamma=0{,}5$, điều mà bài không nêu ở chỗ đó.

**Câu hỏi gay gắt:** Một người đọc muốn tái lập Bảng 1 sẽ đặt $\alpha=0{,}34$ **và** $\beta=\gamma=0{,}33$ (vì bài nói "equal thirds"), rồi thu được con số khác 0,8763. Bài phải công bố rằng mọi cấu hình cộng đều giữ $\beta=\gamma=0{,}5$, và sửa nhãn "equal thirds".

---

## CHẤT VẤN 11.3 — Công thức $\mathcal{V}_{agg}$ với $\mu$ được in nhưng **KHÔNG tồn tại trong mã** (TRUNG BÌNH — claim không kiểm chứng được)

**Bài in** (dòng 276–279, Eq.~\ref{eq:vagg-mu}):
$$\mathcal{V}_{agg}(C_k) = 1 + (\mu-1)\tanh\!\Big(\tfrac1s\textstyle\sum V_i\Big),\qquad \mu\in[1,2]$$
kèm khẳng định "so $\mu=1$ disables amplification and $\mu=2$ recovers the default. All reported numbers use $\mu=2$", và Bảng 2 (tham số) liệt kê `$\mu$ | 2 | Vulnerability amplification cap | Policy (command staff)`.

**Mã nguồn** (`priority.py` dòng 93): `v_agg = 1.0 + math.tanh(v_sum / params.v_scale)` — **không có $\mu$**. `PriorityParams` (config.py) chỉ có `omega_e, omega_f, omega_n, v_scale`; grep toàn `demo/pipeline/` không tìm thấy `mu`, `v_cap`, hay biến khuếch đại nào.

**Đánh giá công bằng:** với $\mu=2$ thì $(\mu-1)=1$ nên công thức tổng quát **thu về đúng** công thức đã cài. Vậy **mọi con số báo cáo vẫn đúng** — đây không phải lỗi số liệu. Nhưng nó là một vấn đề thật về tính trung thực của phần trình bày: bài giới thiệu $\mu$ như một **núm điều khiển chính sách** ("exposing $\mu$ makes that ethical dial explicit rather than hard-coded"), liệt kê nó trong bảng tham số như thể nó là một tham số của hệ thống, trong khi **nó bị hard-code chính xác theo cách bài nói là không nên**. Một phản biện đọc code sẽ hỏi: núm này ở đâu?

**Hai lựa chọn trung thực:** (a) cài $\mu$ vào `PriorityParams` để nó thành núm thật, hoặc (b) trình bày $\mu$ rõ ràng là một **tổng quát hóa đề xuất chưa hiện thực**, và loại nó khỏi bảng tham số hoặc ghi chú rõ. Không được để nguyên trạng.

---

## CHẤT VẤN 11.4 — Mô tả sparsification thiếu một chi tiết làm thay đổi ý nghĩa $k$ (TRUNG BÌNH)

**Bài in** (dòng 236): "(ii) a $k$-NN graph (each vertex keeps its $k$ highest-weight neighbors)", và Bảng 2 ghi `$k$ | 12 | $k$-NN degree cap`.

**Mã nguồn** (`weighting.py` dòng 156): `mask = mask | mask.T` — "giữ cạnh nếu là k-NN của ít nhất một đầu".

Tức đồ thị được đối xứng hóa bằng **OR**, nên bậc thực của một đỉnh **có thể vượt $k$**: đỉnh $u$ giữ được cạnh $(u,v)$ nếu $u\in kNN(v)$ **hoặc** $v\in kNN(u)$. Gọi $k$ là "**degree cap**" (trần bậc) là **sai**: nó không chặn trên bậc. Đây là lựa chọn cài đặt tiêu chuẩn và hợp lý (đồ thị OR-symmetrized giữ liên thông tốt hơn AND), nhưng mô tả trong bài phải khớp — đặc biệt khi bài dùng $k$ để lập luận về chi phí tính toán.

---

## CHẤT VẤN 11.5 — Haversine: hai hàm, hai công thức, hai bán kính Trái Đất (NHỎ, nhưng liên quan trực tiếp claim "sai khác $7{,}3\times10^{-11}$")

- `attributes.haversine_m` (dòng 31): `radius = 6_371_000.0`, dùng `2*R*atan2(sqrt(a), sqrt(1-a))`.
- `weighting.build_weight_matrix_vec` (dòng 115–120): `r = 6.371e6` với comment "cùng R với attributes.haversine_m" ✓ (bằng nhau), nhưng dùng `2*R*arcsin(sqrt(clip(h,0,1)))`.

$\arcsin\sqrt{a}$ và $\operatorname{atan2}(\sqrt a,\sqrt{1-a})$ **đồng nhất về giải tích** trên $a\in[0,1]$, nên hai bản không lệch về mặt toán — điều này **giải thích** vì sao sai khác quan sát được chỉ ở mức $10^{-11}$ (nhiễu dấu phẩy động), và do đó **củng cố** claim của Exp11 chứ không phá nó. Ghi nhận là **đã kiểm, không phải lỗi**. Chỉ nên thêm một câu trong bài nói rõ hai bản dùng hai dạng đại số tương đương của cùng công thức Haversine, để người đọc không nghi ngờ khi so hai hàm.

---

## ĐÃ KIỂM — MÃ KHỚP CÔNG THỨC (giữ nguyên)

- $\mathcal{S}_{geo}=\exp(-d^2/2\sigma^2)$ ✓ (`weighting.py:21`).
- $\mathcal{S}_{temp}=\exp(-|\Delta t|/\tau_{temp})$, $\Delta t$ tính bằng **phút** khớp $\tau_{temp}=45$ phút ✓.
- $\mathcal{S}_{context}=\exp(-|\Delta F|/\tau_F-|\Delta E|/\tau_E)$ ✓.
- $w_{ij}=\mathcal{S}_{geo}(\beta\mathcal{S}_{temp}+\gamma\mathcal{S}_{context})$ ✓ đúng dạng nhân đã in.
- $C_i=\sigma(b_0+b_1\mathbb{1}[\text{ảnh}]+b_2\log(1+n^{corrob}))$ ✓ (`attributes.py:54`), bán kính 400 m / cửa sổ 60 phút ✓ tách khỏi $\sigma_{geo},\tau_{temp}$ đúng như bài khẳng định.
- $\mathcal{E}_{agg}=\frac1{|C|}\sum E_iC_i$ ✓; $\mathcal{F}_{max}=\max(F_iC_i)$ ✓ ($C_i$ **bên trong** max, đúng như dòng 266 nhấn mạnh); $\mathcal{N}_{total}=\sum N_iC_i$ ✓.
- $\widetilde{\mathcal{N}}=\log(1+\mathcal{N})/\log(1+N_{\max})$ ✓, và **hai chế độ** $N_{\max}$ động/tĩnh (`n_ref`) đúng như dòng 258 mô tả, kèm cảnh báo non-stationary trong docstring ✓.
- $\mathcal{P}=\mathcal{V}_{agg}\cdot\text{core}$ ✓; ablation cộng dùng `core + (v_agg - 1)` — đúng là "thêm offset trong $[0,1)$", khớp lập luận dòng 272 ✓.
- $\omega=(0{,}34;0{,}33;0{,}33)$, $s=10$, $\lambda=1{,}0$, $\theta=0{,}05$, $k=12$ ✓ khớp Bảng 2.
- **Diameter**: `mean_diameter_km_multi` (chỉ cụm $\ge2$) và `max_diameter_km` ✓, kèm cảnh báo trong docstring rằng trung bình-mọi-cụm thưởng singleton một cách giả tạo — **đúng** như bài trình bày ở phần Metrics.
- **noise_absorbed_pct** ✓ định nghĩa khớp: % điểm `gt<0` bị đặt vào cụm có ít nhất một điểm có nhãn.
- **ARI/NMI mask `gt>=0`** ✓ khớp khẳng định "ARI and NMI mask out gt<0, so that noise-hygiene difference is invisible".
- **Exp7 độ đo trung lập** ✓: `SEVERE_FLOOD_THRESHOLD = 0.7`, hàm `_severe_vulnerable_weight` có docstring ghi rõ "TRUNG LẬP, đăng ký trước... dùng tiêu chí NGOÀI công thức P", và JSON đánh dấu `primary_metric` — khớp chính xác lập luận ở dòng 476.

---

## TỔNG KẾT STEP 1

1. **11.1** — Bảng 9: V-measure Louvain in **0,9330**, đúng phải là **0,9933** (trung bình điều hòa của 0,9867 và 1,0; cũng bằng NMI đã in ở hai bảng khác). Tự mâu thuẫn nội tại, **tự kiểm chứng được trên trang giấy**. NGHIÊM TRỌNG.
2. **11.2** — Mọi cấu hình "additive $\alpha=\dots$" thực chạy với $\beta=\gamma=0{,}5$ (tổng hệ số $\neq1$), nên nhãn "$\alpha=0.34$ (equal thirds)" là **sai** và bài thiếu công bố $\beta,\gamma$ cho các hàng đó. Ảnh hưởng **tính tái lập**. NGHIÊM TRỌNG.
3. **11.3** — $\mu$ được in như một núm chính sách và liệt kê trong bảng tham số, nhưng **không tồn tại trong mã** (hard-code $\mu=2$). Số liệu vẫn đúng; phần trình bày phải sửa. TRUNG BÌNH.
4. **11.4** — $k$ không phải "degree cap": đồ thị đối xứng hóa bằng OR nên bậc có thể vượt $k$. TRUNG BÌNH.
5. **11.5** — Hai dạng Haversine tương đương, **không phải lỗi**; nên thêm một câu giải thích để claim $10^{-11}$ của Exp11 không bị nghi ngờ. NHỎ.
