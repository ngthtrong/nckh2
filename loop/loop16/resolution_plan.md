# Loop 16 — Kế hoạch Giải quyết (Step 2)

**Vai trò:** Tác giả. Loop này khó nhất trong 16 vòng, vì chất vấn 16.1 **không phải lỗi số liệu** — mọi con số đều đúng — mà là **lỗi thiết kế thí nghiệm** làm cho một kết luận trung tâm không được chứng minh bởi thí nghiệm đã chạy. Nguyên tắc: không được sửa bằng cách viết lại câu cho mơ hồ. Phải **chạy thí nghiệm đúng**, xem nó nói gì, rồi viết theo nó.

---

## 16.1 — $\theta$ dùng chung trên hai miền giá trị khác nhau — CHẤP NHẬN, và phải chạy thí nghiệm mới

**Thừa nhận:** Chất vấn đúng, và đây là lỗi nghiêm trọng nhất còn sót lại. Không thể biện hộ. Bằng chứng tự nói:

```
θ = 0,05 giữ  8,3% cặp trong ma trận gating   (median w = 0,0000)
θ = 0,05 giữ 99,99% cặp trong ma trận cộng    (median w = 0,3909)
```

Dạng cộng có sàn $\beta\mathcal{S}_{temp}+\gamma\mathcal{S}_{context} \ge 0{,}041 > \theta$, nên **ngưỡng không loại được cạnh nào vì lý do khoảng cách**. Cấu hình "additive $\alpha=1{,}0$" mà bài in không phải "dạng cộng", nó là "dạng cộng **cộng thêm** một ngưỡng vô hiệu lực". Và kiểm chứng trực tiếp: **cùng dạng cộng đó, chỉ đổi $\theta$ từ 0,05 sang 1,0, cho ARI 0,9957 / max 1,41 km — trùng khít gating**. Ở $\theta=1{,}1$ nó còn đạt **ARI 1,0**, cao hơn gating.

**Cách KHÔNG sửa:** giữ nguyên bảng rồi thêm một câu rào ("$\theta$ được giữ chung cho mọi cấu hình"). Đó là che lỗi bằng cách công bố nó, và một phản biện đọc kỹ sẽ hỏi đúng câu tôi vừa hỏi.

**Cách sửa — chạy `exp13_theta_calibration.py` (mới):** với **từng** dạng trọng số, quét $\theta$ trên toàn miền giá trị riêng của nó và ghi nhận: ARI, max diameter, số cụm, hấp thụ nhiễu, số cạnh. Sau đó so **kết quả tốt nhất mà mỗi dạng đạt được khi được hiệu chỉnh $\theta$ tử tế** — chứ không so ở một $\theta$ có lợi cho ta.

**Kết quả đã chạy trước để biết mình sẽ phải viết gì** (không viết bài trước khi biết số):

| dạng | cửa sổ $\theta$ cho max-diam $<5$ km & ARI $>0{,}95$ | tỉ lệ rộng | ARI tốt nhất |
|---|---|---|---|
| **gating** | $[0{,}02;\,0{,}50]$ | **25,0×** | 1,0 (tại $\theta=0{,}3$) |
| cộng $\alpha=0{,}34$ | **không tồn tại** | — | — |
| cộng $\alpha=0{,}5$ | $[0{,}96;\,1{,}02]$ | 1,1× | — |
| cộng $\alpha=1{,}0$ | $[0{,}96;\,1{,}46]$ | 1,5× | 1,0 (tại $\theta=1{,}1$) |
| cộng chuẩn-hoá $1/3$ | $[0{,}64;\,0{,}68]$ | 1,1× | — |

**Đây là kết quả cứu được luận điểm, nhưng bằng một luận điểm KHÁC và hẹp hơn.** Sự thật là:

1. Tuyên bố cũ — *"dạng cộng không thể tạo cụm gắn kết vì nó cho phép ngữ cảnh áp đảo khoảng cách"* — **SAI**. Với $\theta$ hiệu chỉnh, dạng cộng $\alpha=1{,}0$ đạt đúng kết quả của gating.
2. Tuyên bố đúng là về **độ bền của tham số**: gating gắn kết trên một cửa sổ $\theta$ **rộng 25×** và ở **mọi** $\theta$ nhỏ mà một người triển khai sẽ chọn theo trực giác; dạng cộng chỉ gắn kết trong một cửa sổ hẹp $1{,}1$–$1{,}5\times$ **quanh một giá trị không có ý nghĩa vật lý nào** ($\theta\approx1{,}0$, tức "loại mọi cặp có $\alpha\mathcal{S}_{geo}+\beta\mathcal{S}_{temp}+\gamma\mathcal{S}_{ctx}$ dưới 1,0" — không phải một đại lượng người điều phối biết cách đặt), và với $\alpha=0{,}34$ thì **không có $\theta$ nào** cứu được nó.
3. Vì sao đó vẫn là ưu thế thật, không phải giải thưởng an ủi: trong gating, tính gắn kết là **bất biến cấu trúc** — $\mathcal{S}_{geo}\to0$ ép $w_{ij}\to0$ nên cạnh xa biến mất *bất kể* $\theta$. Trong dạng cộng, tính gắn kết phải được **hiệu chỉnh vào** qua $\theta$, và giá trị đúng phụ thuộc $\alpha,\beta,\gamma$ cùng phân bố dữ liệu — thứ không biết trước khi thảm họa xảy ra. Đó chính là điều một hệ vận hành cần: bảo đảm theo cấu trúc, không phải theo tinh chỉnh.

**Vậy viết lại như sau (thay cho câu cũ):**
- §Exp1A: giữ nguyên bảng hiện tại **nhưng thêm cột $\theta$** và **thêm khối dạng-cộng-đã-hiệu-chỉnh**, kèm câu thừa nhận thẳng: dạng cộng ở $\theta$ hiệu chỉnh **sánh ngang gating**, nên ưu thế của gating không phải "đạt được cụm gắn kết" mà là "đạt được nó mà không cần hiệu chỉnh".
- Sửa mệnh đề cơ chế ở dòng ~332: "S1 bị gộp ở **mọi** cấu hình cộng" phải thành "ở mọi cấu hình cộng **tại $\theta=0{,}05$**", vì tại $\theta=1{,}0$ nó **không** bị gộp.
- Abstract + Kết luận: đổi từ "cắt đường kính từ 214 km xuống 1,4 km" (đúng số nhưng gán cho dạng trọng số) sang phát biểu đúng: gating đạt gắn kết **theo cấu trúc, trên cửa sổ $\theta$ rộng 25×**, trong khi dạng cộng cần $\theta$ hiệu chỉnh trong cửa sổ 1,1–1,5× và thất bại hoàn toàn ở $\alpha=0{,}34$.

**Điều này làm yếu bài không?** Làm yếu *một* tuyên bố và làm mạnh *tính bảo vệ được* của cả bài. Tuyên bố cũ sẽ bị một phản biện phá trong mười phút bằng đúng thí nghiệm tôi vừa chạy. Tuyên bố mới thì đứng được, vì nó là điều dữ liệu thực sự cho thấy.

---

## 16.2 — $\theta$ và $k$ chưa bao giờ được quét — CHẤP NHẬN, gộp vào exp13

**Thừa nhận:** Đúng. Bảng tham số dán nhãn $\theta,k$ là "Tunable (sparsification)" nhưng Exp2 chỉ quét $\sigma_{geo},\lambda,\tau_F,\tau_E,\beta/\gamma,s$. Hai tham số **không** trơ — gating sụp từ ARI 0,9957 xuống **0,0842** giữa $\theta=0{,}5$ và $0{,}7$.

**Sửa:** exp13 quét $\theta$ cho gating (kết quả trên) và quét $k\in\{4,8,12,20,30,\text{off}\}$. Đưa vào §Exp2 một đoạn mới với khoảng an toàn thật: $\theta\in[0{,}02;\,0{,}30]$ (ARI $\ge0{,}9957$), và ghi rõ ngưỡng sụp ở $\theta\ge0{,}7$. Cập nhật cột "Provenance" trong Bảng tham số từ "Tunable (sparsification)" sang "Tunable (swept, §Exp13)".

---

## 16.3 — "Modularity kém trên đồ thị dày" không nguồn, và mâu thuẫn nội bộ — CHẤP NHẬN, sửa cách nói

**Thừa nhận:** Đúng hai vế. (a) Không có trích dẫn; điều gần nhất có nguồn là **giới hạn phân giải** của Modularity (Fortunato–Barthélemy), đã có trong `references.bib` qua `fortunato2010community` nhưng nói về chuyện khác. (b) Tự mâu thuẫn: dạng cộng ở $\theta=0{,}05$ **là** đồ thị gần-hoàn-chỉnh (99,99% cặp) mà vẫn đạt ARI 0,9572.

**Sửa:** thay mệnh đề nhân-quả tổng quát bằng phát biểu đúng phạm vi: làm thưa (i) giảm chi phí $O(n^2)$ và (ii) loại liên kết giả xuyên vùng; **không** khẳng định Modularity "kém trên đồ thị dày" như một quy luật. Nếu muốn giữ ý về giới hạn phân giải thì phải trích Fortunato–Barthélemy đúng nội dung — nhưng đơn giản hơn là bỏ mệnh đề không cần thiết này.

---

## 16.4 — Bảng tham số ghi $\alpha$ bị loại nhưng $\alpha$ vẫn tồn tại — CHẤP NHẬN, sửa nhỏ

Thêm $\alpha$ vào Bảng tham số với ghi chú "chỉ dùng cho baseline dạng cộng; quét $\{0{,}34;0{,}5;1{,}0\}$ ở §Exp1A", và giữ câu "$\alpha$ bị loại trong dạng gating" — đúng cho công thức đề xuất, chỉ cần không để người đọc tưởng $\alpha$ không tồn tại trong mã.

---

## KHÔNG SỬA — nêu rõ để loop sau không lật lại

- **$k$-NN đối xứng hoá OR**: đã công bố đúng ở dòng 236 (loop 11 sửa). Giữ.
- **Haversine hai dạng (loop/scalar vs vector)**: đã kiểm ở loop 11, tương đương $<10^{-10}$. Giữ.
- **`build_weight_matrix` $O(n^2)$**: đã công bố và đo ở Exp11, kèm hướng thay bằng spatial index. Giữ.
- **$\theta=0{,}05$ làm giá trị mặc định công bố**: **giữ nguyên** làm mặc định của gating — nó nằm giữa cửa sổ an toàn $[0{,}02;0{,}30]$. Không đổi mặc định, chỉ công bố cửa sổ.

---

## THỨ TỰ THỰC THI (Step 3)

1. Tạo `demo/experiments/exp13_theta_calibration.py`: quét $\theta$ cho cả 5 dạng trọng số + quét $k$; ghi `exp13_theta_calibration.json` và `exp13_knn.json`.
2. Chạy exp13, **đọc JSON**, không dùng số phỏng đoán.
3. `main.tex`:
   - Bảng 3 (Exp1A): thêm cột $\theta$, thêm khối "additive, calibrated $\theta$".
   - §Exp1A: thừa nhận dạng cộng hiệu chỉnh sánh ngang; sửa "mọi cấu hình cộng" → "mọi cấu hình cộng tại $\theta=0{,}05$".
   - §Exp2 hoặc mục mới §Exp13: đoạn về cửa sổ $\theta$ (25× vs 1,1–1,5×) và quét $k$.
   - §4.2 sparsification: bỏ mệnh đề "Modularity kém trên đồ thị dày" không nguồn.
   - Bảng tham số: thêm $\alpha$; đổi provenance của $\theta,k$.
   - Abstract + Kết luận: đổi khung tuyên bố gating.
4. Đồng bộ `BaiBao_NoiDung.md` + `Paper.md`.
5. `verify_figures.py`; chạy lại `make_figures.py` nếu cần.
6. Biên dịch `xelatex → bibtex → xelatex ×2`: 0 overfull, 0 undefined, 0 multiply-defined.

---

## NHẬT KÝ THỰC THI (Step 3 — đã hoàn tất)

| # | Việc | Trạng thái |
|---|---|---|
| 1 | Tạo `demo/experiments/exp13_theta_calibration.py`: quét θ riêng cho từng dạng, đo cửa sổ dùng được | ✅ |
| 2 | Đăng ký exp13 vào `run_all.py` (đánh số lại 15 → 16 bước) | ✅ |
| 3 | Sửa slug tên file sang ASCII tường minh (tránh `exp13_sweep_additive_chuẩn_hoá_13.json`) | ✅ |
| 4 | Chạy exp13 → 7 file JSON | ✅ |
| 5 | `main.tex` §5.2 (1A): công bố θ=0,05 dùng chung + trỏ tới §Exp13 | ✅ |
| 6 | `main.tex`: thêm §Experiment 13 + Bảng `tab:theta` | ✅ |
| 7 | `main.tex`: Abstract, Kết luận (2 chỗ), Threats-Internal | ✅ |
| 8 | `main.tex`: Reproducibility "Experiments 1--12" → "1--13" | ✅ |
| 9 | Đồng bộ `BaiBao_NoiDung.md` (§5.2 + §5.14 mới, đánh số lại tới §5.15) + `Paper.md` | ✅ |
| 10 | Biên dịch xelatex×2 + bibtex: **0 overfull, 0 undefined, 0 multiply-defined**, 30 trang | ✅ |

**Số liệu mới (từ `exp13_theta_calibration_best.json` và `exp13_theta_ranges.json`):**

| Dạng | ARI tốt nhất | θ tại đó | Max diam tại đó | Cửa sổ dùng được | Tỉ lệ |
|---|---|---|---|---|---|
| **Gating** | 1,0 | 0,29 | **1,41 km** | [0,01; 0,51] | **51,0×** |
| Cộng α=1,0 | **1,0** | 1,08 | **1,41 km** | [0,96; 1,46] | 1,52× |
| Cộng α=0,5 | 0,9989 | 0,92 | 116,41 km | [0,96; 1,02] | 1,06× |
| Cộng 1/3 | 0,9968 | 0,56 | 195,85 km | [0,64; 0,68] | 1,06× |
| Cộng α=0,34 | 0,9820 | 0,84 | 195,85 km | **không có** | — |

Miền giá trị: gating median **0,0000**, chỉ **8,3%** cặp vượt 0,05; dạng cộng sàn **0,041**, **99,99%** cặp vượt 0,05.

**Tuyên bố đã đổi (đây là thay đổi nội dung, không phải đổi số):** từ "dạng cộng *không thể* sinh cụm gắn kết (214 km)" sang "dạng cộng **đạt được** ngang gating (ARI 1,0 / 1,41 km) nhưng chỉ trong khe θ rộng 1,5×, tìm được **chỉ khi có nhãn ground-truth**; gating dùng được trên dải rộng **51×** bao gồm cả giá trị mặc định 0,05 — ưu thế là **tính dễ chỉnh (tunability)**, không phải khả năng đạt tới". Con số 151× vẫn đúng **tại θ dùng chung** và được giữ với điều kiện nêu rõ.
