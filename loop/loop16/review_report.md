# Loop 16 — Báo cáo Phản biện (Step 1)

**Vai trò:** Giáo sư chủ tịch hội đồng phản biện. Loop 14 soi *cách đo* baseline, loop 15 soi *hàm ưu tiên*. Loop 16 soi tầng còn lại và là tầng nguy hiểm nhất: **điều kiện thí nghiệm của phép so sánh trung tâm của bài báo** — gating vs additive. Câu hỏi: *đóng góp chính của bài (Eq. 5) có thực sự được chứng minh, hay con số 151× đến từ một tham số chung đặt bất lợi cho baseline?*

Phạm vi: `pipeline/weighting.py::sparsify`, `config.py`, Exp1A, Bảng 2/3, và mọi mệnh đề dựa trên so sánh gating-vs-additive (Abstract, §5.2, Kết luận).

Phương pháp: chạy trực tiếp pipeline với các giá trị $\theta$ khác nhau. Mọi số dưới đây là output thật, không suy đoán.

---

## CHẤT VẤN 16.1 — Ngưỡng $\theta=0{,}05$ dùng chung cho hai hàm trọng số có MIỀN GIÁ TRỊ khác nhau; hiệu chỉnh lại thì dạng cộng ĐUỔI KỊP HOÀN TOÀN (NGHIÊM TRỌNG NHẤT trong 16 vòng — đe dọa chính đóng góp của bài)

**Vấn đề gốc.** Bảng 2 khai $\theta=0{,}05$ là một tham số **duy nhất**, áp cho mọi cấu hình. Nhưng hai dạng trọng số có phân bố giá trị hoàn toàn khác nhau:

| Dạng | max $w_{ij}$ | trung vị | phân vị 99 |
|---|---|---|---|
| gating | 0,9883 | **0,0000** | 0,5631 |
| additive $\alpha=1{,}0$ | 1,9883 | **0,3909** | 1,5351 |
| additive $\alpha=0{,}34$ | 1,3288 | 0,3903 | 0,9437 |
| additive $\frac13$-norm | 0,9924 | 0,2605 | 0,7220 |

Hệ quả trực tiếp, đo được:

```
Tỉ lệ cặp có w_ij > 0,05:
  gating            :  8,30%
  additive alpha=1  : 99,99%
```

Cùng một con số $\theta=0{,}05$ **lọc bỏ 91,7% cạnh** của gating nhưng **gần như không lọc gì** của dạng cộng (99,99% cạnh vượt ngưỡng). Với dạng cộng, số hạng $\beta\mathcal{S}_{temp}+\gamma\mathcal{S}_{context}$ có sàn dương không phụ thuộc khoảng cách, nên **mọi** cặp — kể cả hai điểm cách 200 km — đều có $w_{ij}\ge0{,}041 < \theta$ chỉ ở một số ít trường hợp. Nói cách khác: $\theta=0{,}05$ là ngưỡng **có ý nghĩa** với gating và **vô hiệu** với dạng cộng.

**Kiểm chứng quyết định: hiệu chỉnh $\theta$ theo miền giá trị của từng dạng.** Giữ nguyên mọi thứ khác (cùng dữ liệu, cùng $k$-NN $=12$, cùng Louvain seed 42), chỉ chọn $\theta$ cho dạng cộng sao cho số cạnh sau làm thưa **xấp xỉ bằng** số cạnh của gating (1969):

| Cấu hình | ARI | \# cụm | mean multi (km) | max (km) | hấp thụ nhiễu | cạnh |
|---|---|---|---|---|---|---|
| gating, $\theta=0{,}05$ (đã in) | 0,9957 | 74 | **0,85** | **1,41** | 0,0% | 1969 |
| additive $\alpha{=}1$, $\theta=0{,}05$ (đã in) | 0,9572 | 9 | 140,41 | 213,95 | 100% | 2819 |
| additive $\alpha{=}1$, $\theta=0{,}9$ | 0,9760 | 66 | 49,25 | 160,53 | 9,8% | 1975 |
| **additive $\alpha{=}1$, $\theta=1{,}0$** | **0,9957** | **74** | **0,85** | **1,41** | **0,0%** | 1939 |
| **additive $\alpha{=}1$, $\theta=1{,}1$** | **1,0000** | 75 | **0,76** | **1,41** | **0,0%** | 1915 |
| additive $\alpha{=}1$, $\theta=1{,}3$ | 0,9953 | 76 | 0,75 | 1,41 | 0,0% | 1699 |

**Đọc kỹ hai hàng in đậm.** Ở $\theta=1{,}0$, dạng cộng cho **kết quả trùng khít từng chữ số với gating**: ARI 0,9957, 74 cụm, mean multi 0,85 km, max 1,41 km, hấp thụ nhiễu 0,0%. Ở $\theta=1{,}1$ nó **vượt** gating (ARI **1,0000**, max vẫn 1,41 km).

Kết quả này giữ nguyên **cả khi tắt $k$-NN**: additive $\alpha{=}1$, không $k$-NN, $\theta=1{,}0$ → ARI 0,9957 / 74 cụm / 0,85 km / 1,41 km. Nên hiện tượng không phải hiệu ứng phụ của $k$-NN.

**Ý nghĩa toán học — và vì sao đây không phải "phát hiện làm sập bài".** Với $\theta$ đủ lớn, điều kiện $\alpha\mathcal{S}_{geo}+\beta\mathcal{S}_{temp}+\gamma\mathcal{S}_{context}>\theta$ **chỉ có thể** thỏa mãn khi $\mathcal{S}_{geo}$ lớn (vì $\beta\mathcal{S}_{temp}+\gamma\mathcal{S}_{context}\le1$, nên $\theta=1{,}0$ buộc $\alpha\mathcal{S}_{geo}>0$ đáng kể và thực tế buộc $\mathcal{S}_{geo}\to1$). Tức **ngưỡng cao đã tự biến số hạng cộng thành một cổng chặn địa lý** — nó thực hiện *đúng chức năng* của gating, chỉ bằng một cơ chế khác (lọc cứng thay vì điều biến mềm).

**Đây là chất vấn nghiêm trọng nhất vì bài báo đang tuyên bố sai nguồn gốc của ưu thế.** Câu ở dòng 330 nói "a factor of $151$ in the operationally decisive metric" và Abstract nói gating "cuts the worst-case cluster diameter from 214 km to 1.4 km". Cả hai đều **đúng như đã đo**, nhưng chúng so *gating ở $\theta$ hợp lý* với *dạng cộng ở $\theta$ vô hiệu*. Một phản biện chạy lại với $\theta$ hiệu chỉnh sẽ thấy hệ số 151× **biến mất hoàn toàn** — và đó là loại phát hiện làm rút bài (retraction-grade), không phải chỉnh sửa nhỏ.

**Câu hỏi gay gắt:** Vì sao $\theta$ được coi là tham số dùng chung khi hai hàm trọng số có miền giá trị lệch nhau 2 lần và trung vị lệch nhau vô hạn lần (0,0 vs 0,39)? Nhóm tác giả có chạy thử $\theta$ khác cho dạng cộng trước khi công bố hệ số 151× không? Nếu không, đó là **thiếu sót phương pháp luận**: một baseline không được phép thừa hưởng tham số đã tinh chỉnh cho phương pháp đề xuất.

---

## CHẤT VẤN 16.2 — $\theta$ được khai là "Tunable" nhưng KHÔNG hề được quét ở đâu (TRUNG BÌNH, là nguyên nhân gốc của 16.1)

Bảng 2 (dòng 331) khai:
```
theta   0.05   Edge-retention threshold   Tunable (sparsification)
```

Nhưng `demo/experiments/exp2_sensitivity.py` **không chứa** `edge_threshold` hay `theta` ở bất kỳ dòng nào — đã kiểm bằng grep, không có kết quả. Exp2 quét $\sigma_{geo}$, $\lambda$, $\tau_F/\tau_E$, $\beta/\gamma$, $s$ — **thiếu đúng $\theta$ và $k$**.

Đây không phải lỗi trình bày mà là **lỗ hổng dẫn trực tiếp tới 16.1**: nếu $\theta$ từng được quét, hiện tượng ở 16.1 đã lộ ra ngay. Bài báo dán nhãn "Tunable" cho một tham số chưa bao giờ được tune hay kiểm độ nhạy, trong khi §5.3 khẳng định *"$\sigma_{geo}$ and $\lambda$ are the two knobs a deployment must set with care"* — một khẳng định về **tính đầy đủ** của phân tích độ nhạy mà dữ liệu không chống lưng, vì $\theta$ chưa được xét.

Điều đáng nói: gating **thực sự bền** với $\theta$ (đã đo, xem dưới) — nên việc quét $\theta$ chỉ có lợi cho bài. Bỏ sót nó vừa tạo lỗ hổng vừa bỏ mất một kết quả tốt.

---

## CHẤT VẤN 16.3 — Thiếu công bố $k$-NN được áp cho baseline cộng (NHỎ, nhưng cùng họ với 16.1)

`sparsify()` áp $k=12$ cho **mọi** dạng. Với gating, $k$-NN gần như không ràng buộc gì thêm (ngưỡng đã lọc xong). Với dạng cộng ở $\theta=0{,}05$, $k$-NN là **cơ chế lọc duy nhất còn hiệu lực** (vì ngưỡng vô hiệu): 57.970 cạnh → 2.819. Nghĩa là cấu trúc cụm của baseline cộng trong Bảng 3 **hoàn toàn do $k$-NN quyết định**, một sự thật không được nêu ở đâu trong bài.

Đo được: additive $\alpha{=}1$, tắt $k$-NN, $\theta=0{,}05$ → ARI **0,8070**, 6 cụm, 57.965 cạnh (so với 0,9572 / 9 cụm khi có $k$-NN). Nên $k$-NN đang *giúp* baseline cộng, không phải hại nó — điều này nên nói rõ để không bị nghi ngờ ngược lại.

---

## ĐÃ KIỂM — KHÔNG PHẢI LỖI (giữ nguyên)

- **Gating bền vững thật với $\theta$** — và đây là tin tốt cho bài: ARI giữ **0,9957** và max diameter giữ **1,41 km** trên toàn dải $\theta\in[0{,}01;\,0{,}2]$ (số cạnh chỉ đổi 1969→1955), đạt 1,0000 tại $\theta=0{,}3$, và chỉ suy giảm ở $\theta\ge0{,}5$. Vì trung vị $w_{ij}$ của gating **bằng 0**, ngưỡng nhỏ nào cũng cho cùng một kết quả. Đây là bằng chứng $\theta=0{,}05$ **không phải** giá trị được tinh chỉnh cho gating — nên bài không bị cáo buộc cherry-picking cho chính mình, chỉ bị cáo buộc **không hiệu chỉnh cho baseline**. Phân biệt này quan trọng và có lợi cho nhóm tác giả.
- **Công thức `sparsify` OR-symmetrization**: đã sửa ở loop 11, mô tả ở dòng 236 khớp mã. ✓
- **`build_weight_matrix_vec` vs bản vòng lặp**: cùng công thức, sai số $7{,}3\times10^{-11}$ (exp11). ✓ Đã kiểm lại, khớp.
- **Miền giá trị các thành phần** $\mathcal{S}_{geo},\mathcal{S}_{temp},\mathcal{S}_{context}\in(0,1]$: đúng, đã kiểm ở loop 4.
- **`alpha` mặc định $=0{,}5=\beta=\gamma$**: đã công bố ở dòng 301 (loop 11 sửa). ✓ Không phải người-rơm về hệ số.

---

## TỔNG KẾT STEP 1

1. **16.1** — $\theta=0{,}05$ dùng chung cho hai hàm trọng số có miền giá trị khác nhau: nó lọc 91,7% cạnh của gating nhưng chỉ 0,01% cạnh của dạng cộng. **Hiệu chỉnh $\theta$ cho dạng cộng ($\theta=1{,}0$) làm nó trùng khít gating trên MỌI chỉ số (0,9957 / 74 cụm / 0,85 km / 1,41 km / 0,0% nhiễu), và $\theta=1{,}1$ cho ARI 1,0000.** Hệ số "151×" mà bài dùng làm kết quả headline **không tồn tại** khi baseline được hiệu chỉnh công bằng. **NGHIÊM TRỌNG NHẤT — ảnh hưởng Abstract, §5.2, Kết luận.**
2. **16.2** — $\theta$ khai "Tunable" nhưng không có trong bất kỳ phép quét nào; §5.3 lại khẳng định chỉ $\sigma_{geo},\lambda$ cần đặt cẩn thận. Lỗ hổng này chính là nguyên nhân 16.1 không bị phát hiện suốt 15 vòng. TRUNG BÌNH.
3. **16.3** — Không công bố rằng với baseline cộng ở $\theta=0{,}05$, $k$-NN là cơ chế làm thưa **duy nhất** còn hiệu lực (tắt $k$-NN: ARI tụt 0,9572→0,8070). NHỎ.

**Điểm giảm nhẹ, phải nêu cho cân bằng:** gating bền với $\theta$ trên hai bậc độ lớn ($[0{,}01;\,0{,}2]$ cho kết quả y hệt), nên $\theta=0{,}05$ **không** phải con số được tinh chỉnh có lợi cho phương pháp đề xuất. Lỗi ở đây là **bỏ sót hiệu chỉnh cho baseline**, không phải gian lận tham số cho mình.
