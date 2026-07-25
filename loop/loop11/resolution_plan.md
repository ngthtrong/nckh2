# Loop 11 — Kế hoạch Giải quyết (Step 2)

**Vai trò:** Tác giả. Nguyên tắc bổ sung cho loop này: khi **văn bản** và **mã** lệch nhau, phải xác định bên nào là sự thật trước khi sửa. Với 11.1 sự thật là toán học (và JSON). Với 11.2/11.4 sự thật là **mã** (vì mã sinh ra mọi con số), nên **văn bản phải sửa**. Với 11.3 thì cả hai đều "đúng" nhưng không nhất quán — phải chọn.

---

## 11.1 — V-measure 0,9330 → **0,9933** — CHẤP NHẬN, SỬA NGAY

**Thừa nhận:** Đúng, và đây là lỗi tệ nhất còn lại trong bài vì nó **tự tố giác trên trang giấy**: lấy H = 0,9867 và C = 1,0 ở cùng hàng, trung bình điều hòa là 0,9933, không phải 0,9330. Thêm nữa bài tự khẳng định V-measure ≡ NMI đã in (0,9933 ở Bảng 1 và Bảng 4), nên cùng một đại lượng đang có hai giá trị trong cùng bài báo.

**Sửa `main.tex` dòng 497:** `0.9330` → `0.9933`.

Đã kiểm bốn hàng còn lại đều đúng trung bình điều hòa (HDBSCAN 1,0; Spectral 0,6927; K-Means 0,7378; DBSCAN 0,7369) → không đụng.

**Kiểm chéo bản Việt:** BaiBao §5.10 (đã viết lại ở loop 10) in `0,9933` cho hàng Louvain ✓ — **đúng rồi**, chỉ `main.tex` sai. Không đụng bản Việt.

---

## 11.2 — Công thức cộng: công bố $\beta,\gamma$ và bỏ nhãn "equal thirds" — CHẤP NHẬN, SỬA

**Thừa nhận:** Đúng hoàn toàn. `edge_weight_additive` giữ $\beta=\gamma=0{,}5$ từ config và chỉ đổi $\alpha$, nên:
- "$\alpha=0.34$ (equal thirds)" là **sai nhãn**: cấu hình đó là $(0{,}34;\,0{,}5;\,0{,}5)$, tổng $1{,}34$, không chia đều. Chia đều thật là hàng "Normalized $\frac13$-sum" — một hàng khác trong cùng bảng.
- Người đọc muốn tái lập sẽ đặt $\beta=\gamma=0{,}33$ và thu số khác.

**Không đổi mã, không chạy lại thực nghiệm.** Lý do: lựa chọn $\beta=\gamma=0{,}5$ cho baseline cộng là **có chủ ý và công bằng** — docstring `weighting.py:48-51` giải thích rõ là để "baseline không bị hạ trọng số địa lý một cách bất công". Vấn đề thuần là **công bố thiếu**. Sửa văn bản là đúng và không làm mất giá trị nào.

**Sửa cụ thể `main.tex`:**
1. Dòng 330: bỏ "(equal thirds)" sau $\alpha=0.34$, và thêm một câu công bố $\beta,\gamma$:
   > "...so we sweep it: $\alpha=0.34$, $\alpha=0.5$, $\alpha=1.0$ (geography weighted as strongly as the sum of the other two terms), and the fully normalized variant $\frac13(\dots)$. In all four the non-spatial coefficients are held at the defaults $\beta=\gamma=0.5$ — deliberately \emph{not} down-weighted, so the additive baseline is not handicapped — except in the $\frac13$-sum row, where all three coefficients are $1/3$."
2. Dòng 343 (bảng): sửa nhãn hàng `Additive, $\alpha=0.34$` → giữ nguyên tên nhưng bảng không cần nhãn "equal thirds" (nhãn đó chỉ ở thân bài).
3. Chú thích Bảng 1 (dòng 335): thêm "$\beta=\gamma=0.5$ in every additive row except the $\frac13$-sum".
4. Vế "$\alpha=1.0$ (geography weighted as strongly as the sum of the other two terms)" — **đúng** vì $0{,}5+0{,}5=1$, giữ nguyên (nay đã có câu công bố $\beta,\gamma$ ngay trước nên nó tự nhất quán).

**Bản Việt:** BaiBao §5.2 (1A) và Paper.md cũng liệt kê "chia đều ba phần" cho $\alpha=0{,}34$ → sửa tương tự.

---

## 11.3 — $\mu$ in trong bài nhưng không có trong mã — CHẤP NHẬN, chọn phương án (a): **cài $\mu$ vào mã**

Hai phương án đã nêu ở review. Chọn **(a) cài $\mu$ thật**, không chọn (b) hạ cấp thành "đề xuất chưa hiện thực". Lý do:
- Bài lập luận rất mạnh rằng để lộ $\mu$ là **vấn đề đạo đức** ("makes that ethical dial explicit rather than hard-coded"). Hạ $\mu$ xuống thành ghi chú sẽ làm yếu một đóng góp có thật.
- Chi phí cài đặt gần bằng 0: thêm một field vào `PriorityParams` và một hệ số vào một dòng. Với $\mu=2$ mặc định, **mọi con số hiện tại không đổi** (vì $(\mu-1)=1$), nên không phải chạy lại bất kỳ thực nghiệm nào — đây là điều kiện then chốt khiến (a) an toàn.
- Sau khi cài, Bảng 2 liệt kê $\mu$ là **hợp lệ** thay vì gây nhầm.

**Sửa `demo/pipeline/config.py`:** thêm vào `PriorityParams`:
```python
v_cap_mu: float = 2.0           # mu: trần khuếch đại tổn thương, mu in [1,2]
```
**Sửa `demo/pipeline/priority.py` dòng 93:**
```python
v_agg = 1.0 + (params.v_cap_mu - 1.0) * math.tanh(v_sum / params.v_scale)
```
Cập nhật docstring đầu file cho khớp.

**Xác minh bắt buộc:** chạy lại `exp1` và `exp5` rồi so JSON trước/sau — phải **giống hệt từng con số** (vì $\mu=2$). Nếu lệch dù một chữ số thì rollback, vì nghĩa là hiểu sai công thức.

---

## 11.4 — $k$ không phải "degree cap" — CHẤP NHẬN, sửa văn bản

**Thừa nhận:** Đúng. `mask = mask | mask.T` là đối xứng hóa **OR**, nên bậc thực có thể vượt $k$. Cách cài này chuẩn và tốt hơn AND (giữ liên thông), nên **không đổi mã**, chỉ sửa mô tả.

**Sửa `main.tex`:**
- Dòng 236: "(ii) a $k$-NN graph (each vertex keeps its $k$ highest-weight neighbors)" → thêm: "...retaining an edge when it is among the top $k$ of \emph{either} endpoint (OR-symmetrization), so $k$ bounds each vertex's out-selection rather than its final degree."
- Bảng 2 dòng 316: `$k$-NN degree cap` → `$k$-NN neighbors kept per vertex`.

**Bản Việt:** BaiBao Mục 4.2 nếu có mô tả tương tự thì sửa; kiểm bằng grep "k-NN".

---

## 11.5 — Haversine hai dạng tương đương — thêm một câu, không sửa mã

Không phải lỗi ($\arcsin\sqrt a \equiv \operatorname{atan2}(\sqrt a,\sqrt{1-a})$ trên $a\in[0,1]$, cùng $R=6{,}371\times10^6$ m). Nhưng thêm một mệnh đề trong Exp11 để claim $7{,}3\times10^{-11}$ không bị nghi là che lỗi:
- Dòng 507: sau "agreeing with it to $<10^{-10}$..." thêm: "(the two implementations use algebraically equivalent forms of the same Haversine expression, $\arcsin\sqrt{a}$ versus $\operatorname{atan2}(\sqrt{a},\sqrt{1-a})$, so the residual is pure floating-point noise rather than a modelling difference)".

---

## THỨ TỰ THỰC THI (Step 3)

1. `main.tex` 497: V-measure → 0.9933. **(ưu tiên cao nhất)**
2. `main.tex` 330 + chú thích Bảng 1: công bố $\beta=\gamma=0{,}5$, bỏ "equal thirds".
3. `main.tex` 236 + Bảng 2: sửa mô tả $k$-NN.
4. `main.tex` 507: thêm mệnh đề Haversine.
5. `config.py` + `priority.py`: cài $\mu$ (`v_cap_mu`).
6. **Chạy lại exp1 + exp5, diff JSON trước/sau — phải bằng nhau tuyệt đối.**
7. Bản Việt: sửa nhãn "chia đều ba phần" và mô tả $k$-NN.
8. Biên dịch xelatex ×2, xác nhận 0 undefined / 0 multiply-defined.
