# Giải thích Công thức kèm Ví dụ Dữ liệu Cụ thể và Trích dẫn Nghiên cứu

Tài liệu này bổ trợ cho `GiaiThichCongThuc.md`. Điểm khác biệt: thay vì giải thích ký hiệu, ở đây mỗi công thức được minh họa bằng **số liệu thật** (rút từ bộ dữ liệu mô phỏng 285 sự kiện Miền Trung trong `demo/v2`, seed = 42) và được **neo vào các công trình khoa học** làm cơ sở lý luận cho việc lựa chọn dạng toán học.

Mục tiêu: đọc xong tài liệu này, người đọc trả lời được ba câu hỏi cho từng công thức:
1. Đưa một cặp/cụm sự kiện cụ thể vào thì các con số chạy ra sao?
2. Nếu dùng dạng công thức khác (cộng thay vì nhân, không chuẩn hóa, không gate...) thì hỏng ở đâu?
3. Nghiên cứu nào đã dùng ý tưởng này, và ta kế thừa/khác biệt điểm nào?

Tham số mặc định dùng xuyên suốt (khớp Mục 4bis của `PaperV2.md`):
$\sigma_{geo}=700$ m, $\tau_{temp}=45$ phút, $\tau_F=0{,}25$, $\tau_E=0{,}35$, $\beta=\gamma=0{,}5$, $\theta=0{,}05$, $k=12$, $\lambda=1{,}0$, $s=10$, $\omega=(0{,}34;\,0{,}33;\,0{,}33)$.

---

## 1. Độ tin cậy $C_i$ — heuristic sigmoid

$$
C_i = \sigma\!\big(b_0 + b_1 \cdot \mathbb{1}[\text{có ảnh}] + b_2 \cdot \log(1 + n_i^{\text{corrob}})\big)
$$

### 1.1. Ví dụ số (với $b_0=-0{,}5,\ b_1=1{,}5,\ b_2=0{,}8$)

| Báo cáo | Có ảnh? | Số báo cáo lân cận củng cố $n^{corrob}$ | Tính | $C_i$ |
| :--- | :---: | :---: | :--- | :---: |
| Chỉ văn bản, đơn độc | 0 | 0 | $\sigma(-0{,}5)$ | **0,377** |
| Kèm ảnh đã xác thực | 1 | 0 | $\sigma(-0{,}5+1{,}5)$ | **0,731** |
| Kèm ảnh + 3 nguồn củng cố | 1 | 3 | $\sigma(-0{,}5+1{,}5+0{,}8\ln 4)$ | **0,892** |
| Văn bản + 5 nguồn củng cố | 0 | 5 | $\sigma(-0{,}5+0{,}8\ln 6)$ | **0,718** |

Đọc bảng: một tin nhắn trơ trọi chỉ có chữ được tin ~38%; thêm một tấm ảnh mà mô hình thị giác xác nhận là cảnh ngập đẩy độ tin cậy lên 73%; có thêm hàng xóm cùng báo thì lên gần 90%. Nén log khiến báo cáo củng cố thứ 3 vẫn tăng đáng kể nhưng báo cáo thứ 50 gần như không thêm gì — chống spam một điểm.

### 1.2. Vì sao heuristic thay vì mô hình học?

Trong bộ dữ liệu demo, các tin giả (`is_fake=true`, ví dụ `NZ011`: khai 28 người kẹt, không ảnh, rơi lệch khỏi mọi ổ ngập) tự nhiên nhận $C_i$ thấp vì thiếu cả ảnh lẫn nguồn củng cố. Đây là tín hiệu khả thi ngay tại biên, không cần lịch sử tài khoản dài hạn.

### 1.3. Neo vào nghiên cứu

- **Đa phương thức tăng độ tin cậy phân loại khủng hoảng.** Mô hình SCBD (SSE-Cross-BERT-DenseNet) và khung CrisisSpot [^9][^11] cho thấy kết hợp bằng chứng ảnh + văn bản qua chú ý chéo (cross-attention) làm tăng F1 5–9,45% so với đơn phương thức. Ta kế thừa nguyên lý "có ảnh xác thực ⇒ đáng tin hơn" nhưng đơn giản hóa thành một hạng tử chỉ thị $\mathbb{1}[\text{có ảnh}]$ thay vì một mạng融合 nặng, để chạy được trên điện thoại nạn nhân.
- **Đồng thuận không gian như tín hiệu tin cậy.** Các nghiên cứu phát hiện sự kiện dựa trên đồng xuất hiện không gian–thời gian [^25][^26] dùng số báo cáo độc lập rơi vào cùng vùng làm bằng chứng sự kiện thật. Hạng tử $\log(1+n^{corrob})$ chính là hình thức lượng hóa nhẹ của ý tưởng "corroboration" đó.
- **Nén log để chống bão hòa đếm.** Việc dùng $\log(1+n)$ thay vì $n$ tuyến tính là kỹ thuật quen thuộc trong IR (tương tự sublinear TF trong TF-IDF của TwitterNews+ [^25]): lần xuất hiện đầu quan trọng, các lần sau giảm dần biên đóng góp.

---

## 2. Trọng số cạnh $w_{ij}$ — nhân/gating thay vì cộng

$$
w_{ij} = \underbrace{\mathcal{S}_{geo}(L_i, L_j)}_{\text{cổng chặn}} \cdot \Big( \beta \cdot \mathcal{S}_{temp}(T_i, T_j) + \gamma \cdot \mathcal{S}_{context}(v_i, v_j) \Big)
$$

### 2.1. Ví dụ số — CẶP GẦN (cùng ổ ngập, thật sự nên nối)

Hai sự kiện lõi thuộc cùng cụm ground-truth 0 trong bộ dữ liệu:

- `C0000`: (16,46539 ; 107,593109), $F=0{,}672$, $E=0{,}554$
- `C0001`: (16,466239 ; 107,591998), $F=0{,}805$, $E=0{,}445$
- Khoảng cách Haversine: **151,5 m**; giả định lệch thời gian 5 phút.

| Thành phần | Công thức | Giá trị |
| :--- | :--- | :---: |
| $\mathcal{S}_{geo}$ | $\exp(-151{,}5^2/(2\cdot700^2))$ | **0,977** |
| $\mathcal{S}_{temp}$ | $\exp(-300/2700)$ | **0,895** |
| $\Delta F, \Delta E$ | $\lvert0{,}672-0{,}805\rvert,\ \lvert0{,}554-0{,}445\rvert$ | 0,133 ; 0,109 |
| $\mathcal{S}_{context}$ | $\exp(-0{,}133/0{,}25-0{,}109/0{,}35)$ | **0,430** |
| $w_{ij}$ (**gating**) | $0{,}977\cdot(0{,}5\cdot0{,}895+0{,}5\cdot0{,}430)$ | **0,647** |

Cạnh mạnh → hai điểm được gom chung, đúng như mong đợi.

### 2.2. Ví dụ số — CẶP XA (khác cụm, KHÔNG nên nối dù ngữ cảnh na ná)

- `C0000` (cụm 0, Huế) vs một sự kiện cụm 2 (Quảng Nam), khoảng cách **102,7 km**, cả hai đều mô tả ngập đáng kể ($\Delta F\approx0{,}27$).

| Thành phần | Giá trị |
| :--- | :---: |
| $\mathcal{S}_{geo}$ | $\approx 0$ ($e^{-102719^2/(2\cdot700^2)}$, dưới ngưỡng máy) |
| $\mathcal{S}_{temp}$ | 0,587 |
| $\mathcal{S}_{context}$ | 0,255 |
| $w_{ij}$ (**gating**) | $\approx \mathbf{0}$ |
| $w_{ij}$ (**cộng** $\alpha{=}\beta{=}\gamma{=}0{,}5$) | **0,421** ⚠️ |

Đây là điểm mấu chốt: **dạng cộng gán trọng số 0,42 cho hai điểm cách nhau 100 km** chỉ vì chúng cùng "ngập nặng". Louvain sẽ có xu hướng gom chúng thành một "khu vực tác chiến" trải dài hơn 100 km — vô nghĩa với ca nô. Dạng gating triệt tiêu cạnh này về 0.

### 2.3. Bằng chứng thực nghiệm (Thí nghiệm 1A)

Chạy toàn bộ pipeline với hai dạng công thức trên **cùng bộ dữ liệu**:

| Dạng | ARI | NMI | Đường kính cụm TB (km) | Đường kính max (km) | Số cụm |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Cộng (additive) | 0,892 | 0,927 | **100,07** | 213,95 | 6 |
| Nhân/gating | 0,892 | 0,927 | **0,30** | 1,42 | 27 |

Kết luận trung thực: **ARI như nhau (0,892)** — cả hai đều "phân loại đúng" theo nhãn — nhưng dạng cộng tạo ra các cụm khổng lồ trải 100 km, hoàn toàn không dùng được để điều ca nô. Gating co đường kính về 0,30 km mà không hy sinh độ chính xác. Giá trị của gating không nằm ở ARI mà ở **tính gắn kết không gian**.

### 2.4. Neo vào nghiên cứu

- **Gaussian kernel cho tương đồng không gian.** Việc dùng $\exp(-d^2/2\sigma^2)$ thay cho nghịch đảo khoảng cách tuyến tính bám theo các mô hình đồ thị địa–ngữ nghĩa (Geo-Semantic Graphs) phạt mạnh khoảng cách lớn [^28][^46]. Đây cũng là kernel chuẩn trong spectral clustering và diffusion trên đồ thị.
- **Suy giảm mũ thời gian.** Phát hiện sự kiện đa tầng trên mạng xã hội [^26] mô hình hóa "một diễn biến" bằng cửa sổ thời gian suy giảm; $\tau_{temp}$ chính là hằng số cửa sổ đó.
- **Vì sao KHÔNG cộng.** Các mô hình như TwitterNews+ [^25] dựng đồ thị chỉ trên tương đồng ngữ nghĩa TF-IDF, không có ràng buộc địa lý cứng — chấp nhận được cho phát hiện chủ đề, nhưng bài toán điều phối ca nô có **bán kính hoạt động hữu hạn** nên địa lý phải là điều kiện *cần* (gate), không phải một phiếu bầu ngang hàng. Đây chính là khe hở khoa học 1 mà báo cáo lấp (thiếu thuộc tính vật lý sinh tồn trong định lượng trọng số [^3][^13]).
- **Làm thưa đồ thị (k-NN / ngưỡng $\epsilon$).** Chuẩn trong xây dựng đồ thị tương đồng cho phân cụm phổ và phát hiện cộng đồng; đồ thị k-NN cho cấu trúc cụm rõ hơn đồ thị đầy đủ [^13][^34].

---

## 3. Modularity + Louvain/Leiden

$$
Q = \frac{1}{2m} \sum_{i,j} \left[ A_{ij} - \lambda \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)
$$

### 3.1. Ví dụ trực giác về $\lambda$

Với đồ thị demo, tăng $\lambda$ buộc thuật toán chia nhỏ hơn (phường ngập rộng → khu phố). Thí nghiệm 2 cho thấy ARI ổn định 0,892 khi $\lambda \le 1{,}5$; vượt ngưỡng này cụm bắt đầu vỡ vụn quá mức. Đây là cơ chế kiểm soát **giới hạn độ phân giải (resolution limit)** — nhược điểm lý thuyết cố hữu của Louvain.

### 3.2. Bằng chứng thực nghiệm (Thí nghiệm 3: Louvain vs Leiden)

Trên 10 seed khác nhau: **cả Louvain và Leiden đều cho 0 cộng đồng đứt gãy** (broken communities), cùng ARI 0,892 và $Q=0{,}8311$.

Kết luận trung thực (không phóng đại): chính đồ thị gating đã loại trước rủi ro đứt gãy, nên **Leiden là "bảo hiểm miễn phí"** — một đảm bảo lý thuyết tốt nhưng không bắt buộc trong bối cảnh này. Ta báo cáo đúng như quan sát thay vì dựng một ca bệnh lý giả tạo để "chứng minh" Leiden thắng.

### 3.3. So sánh baseline (Thí nghiệm 4)

Chạy các thuật toán trên **cùng đồ thị gating** (công bằng):

| Thuật toán | ARI | Ghi chú |
| :--- | :---: | :--- |
| Louvain / Leiden | **0,892** | tự tìm số cụm, đường kính 0,30 km |
| Agglomerative | 0,892 | nhưng cần biết trước $K$ |
| HDBSCAN | 0,890 | gộp thành 11 cụm, đường kính **25 km** |
| Spectral Clustering | 0,339 | đồ thị thưa gây khó phân tách phổ |
| K-Means (tọa độ thô, đúng $K$) | 0,688 | cần biết $K$; hình học đơn giản |
| DBSCAN (tọa độ thô, tốt nhất) | 0,730 | nhạy tham số |

Kết luận: ưu thế đến từ **sự kết hợp** đồ thị gating + tối ưu Modularity (tự tìm $K$ + gắn kết không gian), không chỉ từ một thành phần đơn lẻ.

### 3.4. Neo vào nghiên cứu

- **Louvain là tiêu chuẩn vàng cho phân cụm đồ thị trọng số** [^35][^36], độ phức tạp $\mathcal{O}(N\log N)$ chạy được thời gian thực.
- **Leiden đảm bảo cộng đồng liên thông tốt** ("From Louvain to Leiden: guaranteeing well-connected communities") [^51] — cơ sở cho khuyến nghị dùng Leiden khi độ chính xác không gian của cụm là sống còn (trọng tâm cụm sai ⇒ dẫn ca nô sai chỗ).
- **Vì sao KHÔNG K-Means/DBSCAN** làm lõi: K-Means cần biết trước $K$ (bất khả thi khi không rõ bão chia thành phố thành bao nhiêu "ốc đảo"), DBSCAN nhạy tham số trong không gian đa chiều [^30][^32]. Kết quả baseline ở trên xác nhận định tính này bằng số.

---

## 4. Hàm ưu tiên cấp cụm $\mathcal{P}(C_k)$

$$
\mathcal{P}(C_k) = \mathcal{V}_{agg}(C_k) \cdot \Big( \omega_1 \widetilde{\mathcal{E}}_{agg} + \omega_2 \widetilde{\mathcal{F}}_{max} + \omega_3 \widetilde{\mathcal{N}} \Big)
$$

### 4.1. Ví dụ tính đầy đủ end-to-end cho hai cụm

**Cụm A** (có đối tượng yếu thế, chứa 1 tin giả khai 200 người):

| Sự kiện | $F$ | $E$ | $N$ | $V$ | $C$ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| a1 (thật) | 0,85 | 0,90 | 4 | 1,0 | 0,95 |
| a2 (thật) | 0,78 | 0,82 | 3 | 0,0 | 0,90 |
| a3 (**giả**) | 0,99 | 0,80 | **200** | 0,0 | **0,45** |

**Cụm B** (không có yếu thế, không tin giả): b1 (0,60; 0,55; 5; 0; 1,0), b2 (0,65; 0,50; 6; 0; 1,0).

Tính từng thành phần (có gate $C_i$ ở cả ba):

| Đại lượng | Cụm A | Cụm B |
| :--- | :---: | :---: |
| $\mathcal{E}_{agg}=\frac{1}{\lvert C\rvert}\sum E_i C_i$ | 0,651 | 0,525 |
| $\mathcal{F}_{max}=\max(F_i C_i)$ | **0,808** (tin giả 0,99·0,45=0,45 KHÔNG chiếm được max) | 0,650 |
| $\mathcal{N}_{total}=\sum N_i C_i$ | **96,5** (tin giả 200·0,45=90, không phải 200) | 11,0 |
| $\widetilde{\mathcal{N}}=\log(1{+}N)/\log(1{+}N_{\max})$ | 1,000 | 0,543 |
| $\sum V_i$ | 1,0 | 0,0 |
| $\mathcal{V}_{agg}=1+\tanh(\sum V_i/10)$ | 1,100 | 1,000 |
| lõi rủi ro $= \omega_1\mathcal{E}+\omega_2\mathcal{F}+\omega_3\widetilde{\mathcal{N}}$ | 0,818 | 0,572 |
| $\mathcal{P}$ | **0,899** | **0,572** |

Cụm A xếp trên B nhờ rủi ro thực cao hơn *và* có đối tượng yếu thế khuếch đại — đúng mục tiêu công bằng. Đáng chú ý: **nếu KHÔNG gate $C_i$**, tin giả sẽ đẩy $\mathcal{N}_{total}$ từ 96,5 lên 207 và $\widetilde{\mathcal{N}}$ chạm trần 1,0 một cách gian lận.

### 4.2. Lỗi (a) — Sai lệch thang đo (Thí nghiệm 1B)

Không chuẩn hóa, cụm dân số lớn nhất (**216 người**, core value 71,65) chiếm ngôi đầu bảng chỉ vì đông, áp đảo mọi yếu tố khác. Sau khi nén log + min-max, cụm có **lõi rủi ro cân bằng** (0,8165) lên đầu với $\mathcal{P}=1{,}520$. Con số 216 vs các mức khẩn cấp $\in[0,1]$ minh họa vì sao cộng trực tiếp là sai.

### 4.3. Lỗi (b) — $\mathcal{V}$ phải NHÂN, không CỘNG (Thí nghiệm 1C)

Bảng dưới cho vài cụm (rút từ kết quả thật), so $\mathcal{P}$ khi $\mathcal{V}$ làm thừa số nhân vs làm số hạng cộng:

| Cụm | $\mathcal{V}_{agg}$ | lõi | $\mathcal{P}$ (nhân) | $\mathcal{P}$ (cộng) |
| :---: | :---: | :---: | :---: | :---: |
| 1 | 1,862 | 0,817 | 1,520 | 1,678 |
| 2 (yếu thế cao) | 1,971 | 0,691 | 1,362 | 1,662 |
| 0 (không yếu thế) | 1,000 | 0,577 | 0,577 | 0,577 |

Điểm cốt lõi: với dạng **nhân**, hệ số $\mathcal{V}_{agg}$ co giãn *theo* lõi rủi ro — cụm rủi ro cao được khuếch đại nhiều hơn cụm rủi ro thấp (khuếch đại thật). Với dạng **cộng**, $\mathcal{V}$ chỉ cộng thêm một offset gần như hằng số, không "khuếch đại" gì. Chú ý cụm 0 (không yếu thế): $\mathcal{V}_{agg}=1$ nên hai cách cho cùng kết quả — đúng như kỳ vọng.

### 4.4. Lỗi (c) — $\tanh$ bão hòa sớm (Thí nghiệm 1D)

| $\sum V_i$ | $1+\tanh(\sum V_i)$ | $1+\tanh(\sum V_i/10)$ |
| :---: | :---: | :---: |
| 1 | 1,762 | 1,100 |
| 3 | **1,995** (đã sát trần) | 1,291 |
| 10 | 2,000 | 1,762 |
| 50 | 2,000 | 1,999 |

Không chia $s$: chỉ **3 đối tượng yếu thế** đã đưa $\tanh$ sát 1 ⇒ cụm 3 người yếu thế và cụm 50 người yếu thế nhận điểm gần như nhau, triệt tiêu khả năng phân biệt. Chia $s=10$ giãn vùng tuyến tính, phân biệt được tới $\sum V_i \approx 50$.

### 4.5. Gate $C_i$ chống tin giả (Thí nghiệm 1E, 1F)

- **Trên $\mathcal{N}_{total}$ (1E):** tin giả S3 khai 200 người với $C_i=0{,}45$ → $\mathcal{N}$ của cụm bị hạ từ 200 xuống **90 (giảm 55%)**.
- **Trên $\mathcal{F}_{max}$ (1F):** cùng tin giả khai $F=0{,}99$ → $\mathcal{F}_{max}$ bị hạ từ 0,99 xuống **0,446** (vì nhân $C_i$ *bên trong* $\max$). Điều này khôi phục tính nhất quán: cả ba thành phần lõi ($\mathcal{E}, \mathcal{F}, \mathcal{N}$) đều gate $C_i$, nên một báo cáo giả không thể tự chiếm bất kỳ thành phần nào.

### 4.6. Độ ổn định xếp hạng (Thí nghiệm 5)

Nhiễu loạn $\omega$ quanh mặc định (200 thử/mức), đo Kendall's τ của thứ hạng $\mathcal{P}(C_k)$:

| Biên độ dao động $\omega$ | Kendall's τ | Top-3 giữ nguyên |
| :---: | :---: | :---: |
| ±0,05 | **0,994** | 100% |
| ±0,10 | 0,986 | 99–100% |
| ±0,20 | 0,957 | (giảm nhẹ) |

Kết luận: thứ hạng ưu tiên **ổn định**, không tùy tiện theo lựa chọn $\omega$ của ban chỉ huy trong khoảng dao động thực tế.

### 4.7. Neo vào nghiên cứu

- **Ưu tiên dựa trên tổn thương (vulnerability-based prioritization).** Nền tảng lý luận cho hệ số khuếch đại $\mathcal{V}_{agg}$: thảm họa tác động bất bình đẳng, cần khuếch đại các nhóm yếu thế (người già, trẻ em, phụ nữ mang thai, người khuyết tật) thay vì giả định "nhu cầu đồng nhất" [^41][^42]. Đây là khe hở khoa học 2 mà báo cáo lấp.
- **Nguyên lý $\max$ cho rủi ro môi trường.** Dùng $\max$ (không phải trung bình) cho mức ngập theo "nguyên lý bình thông nhau" — điểm ngập sâu nhất quyết định rủi ro sinh tồn của cả quần thể trong một cụm gắn kết [^43].
- **Ma trận quyết định cho trọng số $\omega$.** Việc để ban chỉ huy đặt $\omega_1,\omega_2,\omega_3$ ($\sum\omega=1$) để chuyển trạng thái chiến thuật dựa trên khung Decision Matrix trong quản lý thảm họa [^54].
- **Nén log cho đại lượng lệch phải.** Chuẩn hóa $\widetilde{\mathcal{N}}$ bằng $\log$ trước min-max là kỹ thuật chuẩn cho biến đếm phân phối đuôi dài; cùng họ với chuẩn hóa AHP-Entropy trong đánh giá tổn thất thảm họa [^46].
- **Đầu ra là input cho định tuyến.** Danh sách $\mathcal{P}(C_k)$ + trọng tâm cụm là đầu vào hoàn hảo cho các thuật toán định tuyến cứu hộ đa tiêu chí (A\* cost-aware, multi-commodity routing) [^4][^41] — khép kín khe hở khoa học 3 (thiếu liên kết giữa phát hiện cộng đồng vĩ mô và định lượng ưu tiên chiến thuật).

---

## 5. Bảng tổng hợp: Công thức ↔ Ví dụ ↔ Nghiên cứu

| Công thức | Con số minh họa chính | Nghiên cứu nền tảng |
| :--- | :--- | :--- |
| $C_i$ sigmoid | 0,38 (chữ) → 0,73 (ảnh) → 0,89 (ảnh+3 nguồn) | SCBD/CrisisSpot [^9][^11], event detection [^25][^26] |
| $w_{ij}$ gating | cặp gần w=0,65; cặp xa 100km w≈0 (cộng: 0,42) | Geo-Semantic Graph [^28][^46], TwitterNews+ [^25] |
| Gating vs cộng (exp1A) | đường kính 100 km → 0,30 km, ARI giữ 0,892 | khe hở [^3][^13] |
| Louvain/Leiden | ARI 0,892 vs Spectral 0,34, K-Means 0,69 | Louvain [^35][^36], Leiden [^51] |
| $\widetilde{\mathcal{N}}$ chuẩn hóa | cụm 216 người hết áp đảo sau nén log | AHP-Entropy [^46] |
| $\mathcal{V}_{agg}$ nhân | cụm yếu thế được khuếch đại theo lõi rủi ro | vulnerability prioritization [^41][^42] |
| $\tanh(\sum V/s)$ | phân biệt tới ΣV=50 thay vì bão hòa ở ΣV=3 | — (đóng góp kỹ thuật của báo cáo) |
| Gate $C_i$ | tin giả 200 người → 90 (−55%); F 0,99 → 0,45 | robustness với tin giả [^9] |
| Ổn định $\omega$ | Kendall τ ≥ 0,99 ở ±0,05 | Decision Matrix [^54] |

---

## Nguồn trích dẫn

Các nguồn dưới đây dùng lại hệ thống trích dẫn của `PaperV2.md` (giữ nguyên số hiệu `[^n]` để đối chiếu chéo).

[^3]: Thuyết minh NCKH (đề tài gốc).

[^4]: Performance Optimization of Multi-Criteria Route Planning Algorithms: A Case Study in HAZMAT Emergency Response — Preprints.org. https://www.preprints.org/manuscript/202602.0136

[^9]: A social context-aware graph-based multimodal attentive learning framework for disaster content classification during emergencies (CrisisSpot) — arXiv 2410.08814. https://arxiv.org/abs/2410.08814

[^11]: A Social Context-aware Graph-based Multimodal Attentive Learning Framework (SCBD) — arXiv. https://arxiv.org/pdf/2410.08814

[^13]: ConvGraph: Community Detection of Homogeneous Relationships in Weighted Graphs — MDPI Mathematics 9(4):367. https://www.mdpi.com/2227-7390/9/4/367

[^25]: A Review on the Trends in Event Detection by Analyzing Social Media Platforms' Data (TwitterNews+) — PMC9231398. https://pmc.ncbi.nlm.nih.gov/articles/PMC9231398/

[^26]: Multiscale event detection in social media — MIT Media Lab. https://web.media.mit.edu/~xdong/paper/dmkd15.pdf

[^28]: Disaster Prediction Knowledge Graph Based on Multi-Source Spatio-Temporal Information — ResearchGate. https://www.researchgate.net/publication/358964513

[^30]: Natural Disaster Clustering Using K-Means, DBSCAN, SOM, GMM, and Mean Shift — SAI IJACSA 15(9). https://thesai.org/Downloads/Volume15No9/Paper_68-Natural_Disaster_Clustering_Using_K_means.pdf

[^32]: An improved spatio-temporal clustering method for extracting fire footprints — ConnectSci. https://connectsci.au/wf/article/32/5/679/21934/

[^34]: GraphHDBSCAN*: Graph-based Hierarchical Clustering on High Dimensional scRNA-seq Data — bioRxiv. https://www.biorxiv.org/content/10.64898/2026.03.24.713924v1.full-text

[^35]: Louvain method for community detection — Blondel et al. https://perso.uclouvain.be/vincent.blondel/research/louvain.html

[^36]: Louvain method — Wikipedia. https://en.wikipedia.org/wiki/Louvain_method

[^41]: Optimization of emergency logistics for urban flooding with consideration of rainfall effects — PMC12365076. https://pmc.ncbi.nlm.nih.gov/articles/PMC12365076/

[^42]: Vulnerability based prioritization in disaster planning efforts: benefits and trade-offs — Taylor & Francis. https://www.tandfonline.com/doi/full/10.1080/03155986.2025.2486230

[^43]: Enhanced Spatiotemporal Landslide Displacement Prediction Using Dynamic Graph-Optimized GNSS Monitoring — PMC12349391. https://pmc.ncbi.nlm.nih.gov/articles/PMC12349391/

[^46]: Spatial-Temporal Assessment of Natural Disaster Losses Using Combined AHP-Entropy Weight Method — EarthArXiv. https://eartharxiv.org/repository/object/12393/

[^51]: From Louvain to Leiden: guaranteeing well-connected communities — Traag et al., arXiv 1810.08473. https://arxiv.org/abs/1810.08473

[^54]: Decision Matrix For Disaster Management — Meegle. https://www.meegle.com/en_us/topics/decision-matrix/decision-matrix-for-disaster-management
