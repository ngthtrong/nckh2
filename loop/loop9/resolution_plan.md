# Loop 9 — Kế hoạch Giải quyết (Step 2)

**Vai trò:** Tác giả (rời vai phản biện), giữ tính khách quan. Nguyên tắc xử lý: **JSON là nguồn sự thật**. Mọi con số trong văn bản phải chỉnh về khớp JSON, không được chỉnh JSON để khớp văn bản.

---

## 9.1 — Exp3 "20 seeds" → **10 seeds** — CHẤP NHẬN, SỬA

**Thừa nhận:** Đúng. `SEEDS` trong `exp3_louvain_vs_leiden.py` có 10 phần tử, `exp3_per_seed.json` có 10 bản ghi, và $13\times10=130$ khớp `total_clusters_evaluated`. Con số "20" gần như chắc chắn bị chảy sang từ Exp12 (`N_SEEDS = 20`) trong lần viết lại.

**Không chọn phương án "chạy lại Exp3 với 20 seed"** dù về mặt kỹ thuật khả thi: loop này là vòng sửa văn bản cho khớp dữ liệu đã có, và 10 seed đã đủ cho một khẳng định "0 cộng đồng đứt gãy". Sửa văn bản là cách trung thực và ít rủi ro nhất.

**Sửa `main.tex` dòng 402:**
- "Across \textbf{20 seeds}" → "Across \textbf{10 seeds}"
- "(130 over the 20 seeds)" → "(130 over the 10 seeds)"

Kiểm tra chỗ khác cùng chủ đề: dòng 526 và 560 nói "20 seeds" nhưng đó là **Exp12** (`N_SEEDS = 20` ✓) — **đúng, không đụng**. Abstract dòng 49 "across 20 seeds the gating form wins on 100% of seeds" cũng là Exp12 ✓.

---

## 9.2 — Exp11 mô tả scaling ngược dữ liệu — CHẤP NHẬN, SỬA (viết lại mệnh đề)

**Thừa nhận:** Đúng hoàn toàn, và đây là lỗi tệ nhất của loop này vì nó là khẳng định về **độ phức tạp**. Cả ba bước đều vượt dự đoán bậc hai (20,15 vs 12,4; 11,26 vs 8,89; 5,55 vs 4,02). Câu hiện tại vừa sai chiều, vừa dùng chữ "tracks" cho một sai lệch 38%.

**Diễn giải đúng (và vẫn là một phát hiện có giá trị):** chi phí build tăng **nhanh hơn** $O(n^2)$ thuần lý thuyết. Nguyên nhân hợp lý và nên nói thẳng: ma trận dày $n\times n$ vượt cache và tiến vào vùng giới hạn băng thông bộ nhớ, nên hằng số nhân xấu đi theo $n$. Điểm đáng chú ý là **tỉ số vượt đang thu hẹp** (20,15/12,4 = 1,63× → 11,26/8,89 = 1,27× → 5,55/4,02 = 1,38×) — nhưng không được kể như "hội tụ về bậc hai" vì bước cuối lại tăng nhẹ so với bước giữa. Cách trung thực: nêu số, nêu nguyên nhân, và nói rằng nó **củng cố** (không phải làm yếu) kết luận "phải thay ma trận dày bằng spatial index quá $\sim10^4$".

**Sửa `main.tex` dòng 507**, thay cụm mô tả scaling bằng:
> "Second, the build stage grows \emph{faster} than the $O(n^2)$ prediction at every step measured ($20.2\times$ observed vs.\ $12.4\times$ predicted, then $11.3\times$ vs.\ $8.9\times$, then $5.6\times$ vs.\ $4.0\times$): the dense $n\times n$ matrix leaves cache and becomes memory-bandwidth-bound, so the constant factor degrades with $n$. This strengthens rather than weakens the deployment conclusion below. The two graph stages, by contrast, stay cheap: ..."

Giữ nguyên: 37,7 s, 4,1 s sparsify, 9,0 s Louvain, $3{,}3$–$6{,}1\times$ speedup, $7{,}3\times10^{-11}$.

---

## 9.3 — Bảng 11 sai số — CHẤP NHẬN, SỬA về đúng JSON

| Ô | Bài in | JSON | Sửa thành |
|---|---|---|---|
| $n{=}341$, Build (loop) | 0.186 | 0.1186 | **0.119** |
| $n{=}3581$, Sparsify | 0.702 | 0.6429 | **0.643** |
| $n{=}3581$, Louvain | 2.194 | 2.2551 | **2.255** |

Kiểm lại các ô khác của bảng so với JSON: $n{=}341$ vec 0.020 (0.0195 ✓), sparsify 0.004 (0.0036 ✓), louvain 0.036 (0.0363 ✓), total 0.060 (0.0595 ✓), 74 cụm ✓. $n{=}1201$: 0.394/1.499/3.8×/0.045/0.300/0.739/213 ✓ toàn bộ. $n{=}3581$: 4.435/14.856/3.3×/7.331/579 ✓. $n{=}7181$: 24.623/4.143/8.973/37.738/1097 ✓. Vậy chỉ 3 ô phải sửa.

Sau khi sửa, cột Speedup tự khớp: $0{,}119/0{,}020 = 6{,}0\approx6{,}1$ ✓.

---

## 9.9 — Bảng 12 Modularity — CHẤP NHẬN, SỬA về đúng JSON

`main.tex` dòng 543 → `Modularity $Q$ & $0.8612\pm0.0004$ & $0.7748\pm0.0076$ & 100\%`

Kiểm lại 6 hàng còn lại của Bảng 12 so với `exp12_multiseed_summary.json`: ARI $0{,}9957\pm0$ / $0{,}9415\pm0{,}0141$ ✓; NMI $0{,}9933\pm0$ / $0{,}9500\pm0{,}0073$ ✓; mean diam $0{,}83\pm0{,}04$ / $149{,}19\pm11{,}25$ ✓; max diam $1{,}57\pm0{,}25$ / $196{,}82\pm8{,}09$ ✓; noise $0{,}41\pm0{,}90$ / $93{,}61\pm10{,}30$ ✓; #clusters $73{,}3\pm0{,}8$ / $8{,}6\pm0{,}7$ ✓ (JSON 8,55 → 8,6 làm tròn hợp lệ). Chỉ hàng Modularity sai.

Lưu ý: hàng `n_singletons` (gating $59{,}85\pm1{,}39$) có trong JSON nhưng không có trong bảng — đó là lựa chọn trình bày hợp lệ, không phải lỗi. Không thêm.

---

## 9.5 — `\label` trùng — CHẤP NHẬN, SỬA

Xóa một `\label{sec:exp5}` ở dòng 443.

---

## 9.6 — Nhảy số Experiment 10 — CHẤP NHẬN, sửa bằng cách **thêm mục Experiment 10**

Hai phương án:
- (a) Đánh số lại 11→10, 12→11. Nhưng khi đó số mục bài báo lệch với tên file code (`exp11_scaling.py`, `exp12_multiseed.py`), phá vỡ tính truy vết "mỗi số trong bài truy về một field trong file JSON" mà mục Reproducibility đã hứa.
- (b) **Chọn (b):** tạo mục `\subsection{Experiment 10 --- Metadata Packet Size}` ngay trước Exp11, chuyển phần đo gói (105–111 byte) từ Discussion sang đây. Vừa lấp lỗ đánh số, vừa khớp tên file code, vừa cho một thí nghiệm có JSON riêng đúng chỗ của nó.

**Thực thi:**
1. Thêm sau Exp9 (sau dòng 504):
```latex
\subsection{Experiment 10 --- Metadata Packet Size}\label{sec:exp10}
The premise of the edge design is that the uplink can carry kilobytes but not megabytes, so the packet size is a load-bearing number rather than an incidental one. We serialize each of the 341 events as a compact JSON descriptor (event id, coordinates, an epoch timestamp, the $L,T,F,E,N,V,C$ fields, and an image flag) with whitespace stripped, and measure the encoded length of every one. The result is deterministic and tightly bounded: \textbf{105--111 bytes} (min $105$, median $110$, max $111$), i.e.\ every event fits in a single small datagram, versus the megabyte-scale multimedia post it summarizes. That MB$\rightarrow$sub-KB reduction is what keeps a congested mesh/LoRa uplink viable, and it is the quantitative form of the claim made in Sect.~\ref{sec:intro-contrib}.
```
   (Nếu `sec:intro-contrib` chưa tồn tại thì bỏ vế cuối — không tạo xref treo. **Sẽ bỏ vế đó** vì Introduction hiện không có label; viết gọn lại.)
2. Trong Discussion (dòng 554), rút gọn phần trong ngoặc đang lặp lại số byte, trỏ về `Sect.~\ref{sec:exp10}` thay vì in lại số.
3. Cập nhật dòng 80 (Related Work) đang trỏ `Sect.~\ref{sec:discussion}` cho số byte → trỏ `Sect.~\ref{sec:exp10}`. Tương tự dòng 184.
4. Cập nhật câu Reproducibility (dòng 550): "runs Experiments 1--12" — vẫn đúng, không đụng.

---

## 9.7 — Ba-artifact lệch bộ dữ liệu — CHẤP NHẬN, nhưng **chia việc**

**Thừa nhận:** Đúng, và đây là lỗi tồn đọng lớn nhất. `BaiBao_NoiDung.md` + `Paper.md` đang mô tả thực nghiệm 285-sự-kiện đã bị thay thế; tệ nhất là **Exp6 bị khẳng định ngược** ("bỏ ngữ cảnh làm ARI tụt 0,892→0,7855") trong khi dữ liệu hiện tại cho thấy ablation **không đổi gì** (τ=1,0).

**Đánh giá khối lượng:** đồng bộ trọn vẹn hai file Việt = viết lại toàn bộ phần 5 (Thực nghiệm) + Tóm tắt + Kết luận + Threats, khoảng 30+ vị trí số liệu. Đây là việc lớn và **không nên nhồi vào cùng loop với 6 sửa lỗi `main.tex`**, vì trộn hai loại thay đổi làm khó kiểm chứng từng cái.

**Kế hoạch:** xử lý theo hai bước qua hai vòng:
- **Loop 9 (ngay):** sửa các lỗi trong `main.tex` (9.1, 9.2, 9.3, 9.9, 9.5, 9.6) + thêm **cảnh báo trạng thái** ở đầu hai file Việt nêu rõ chúng đang mô tả bộ dữ liệu cũ và `paper/main.tex` là bản chuẩn hiện hành, để không ai vô tình dùng số sai trong khi chờ đồng bộ. Đồng thời sửa ngay **hai chỗ sai nặng nhất về kết luận** (không chỉ số): mệnh đề Exp6 đảo chiều, và câu "mười thí nghiệm exp1–exp10" → mười hai.
- **Loop 10:** đồng bộ toàn bộ số liệu hai file Việt về bộ 341-sự-kiện, có hệ thống, theo bảng đối chiếu ở 9.7.

Lý do tách: sửa mệnh đề *kết luận sai* là cấp bách (người đọc rút ra điều trái dữ liệu); sửa *con số cũ* thì đã có cảnh báo trạng thái che tạm và cần làm gọn một lượt.

---

## THỨ TỰ THỰC THI (Step 3)

1. `main.tex` 402: 20 → 10 seeds (×2 chỗ).
2. `main.tex` 507: viết lại mệnh đề scaling.
3. `main.tex` 517/519: sửa 3 ô Bảng 11.
4. `main.tex` 543: sửa hàng Modularity Bảng 12.
5. `main.tex` 443: xóa `\label` trùng.
6. `main.tex`: thêm mục Experiment 10 + chỉnh 3 xref về nó.
7. `BaiBao_NoiDung.md` + `Paper.md`: thêm khối cảnh báo trạng thái; sửa mệnh đề Exp6; sửa "mười thí nghiệm" → "mười hai".
8. Biên dịch bằng **xelatex** (fontspec — KHÔNG pdflatex): `xelatex → bibtex → xelatex ×2`. Yêu cầu: 0 undefined reference, 0 multiply-defined label.
9. Ghi nhận trạng thái, chuyển loop 10.
