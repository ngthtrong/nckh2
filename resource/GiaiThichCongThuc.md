# Báo cáo Giải thích Chi tiết Các Công thức trong Khung Giải pháp (Mục 4)

Tài liệu này giải thích cặn kẽ từng công thức toán học được sử dụng trong Mục 4 của báo cáo `PaperV2.md` sau khi đã áp dụng các chỉnh sửa. Với mỗi công thức, tài liệu trình bày: (1) ý nghĩa từng ký hiệu, (2) trực giác thiết kế, (3) lý do lựa chọn dạng toán học này thay vì dạng khác, và (4) hành vi tại các trường hợp biên.

---

## 1. Vector thuộc tính đa chiều của một sự kiện

Mỗi sự kiện cứu hộ $v_i$ được biểu diễn bằng bộ bảy thuộc tính:

$$
v_i = (L_i,\; T_i,\; F_i,\; E_i,\; N_i,\; V_i,\; C_i)
$$

| Ký hiệu | Tên | Miền giá trị | Nguồn trích xuất |
| :--- | :--- | :--- | :--- |
| $L_i$ | Vị trí không gian (GPS) | $(\text{lat}, \text{lon})$ | Thiết bị di động / geo-tagging |
| $T_i$ | Tem thời gian | dấu thời gian | Metadata báo cáo |
| $F_i$ | Mức độ ngập vật lý | $[0, 1]$ | Semantic segmentation / pose estimation (MobileNetV3) |
| $E_i$ | Mức độ khẩn cấp | $[0, 1]$ | Phân tích cảm xúc văn bản (DistilBERT/UIT-VSMEC) |
| $N_i$ | Số người mắc kẹt | $\mathbb{Z}^{+}$ | Nhập tay / crowd counting |
| $V_i$ | Chỉ số tổn thương nhân khẩu học | $\ge 0$ | Nhánh multi-label ghép chung bộ phân loại văn bản |
| $C_i$ | Độ tin cậy thông tin | $(0, 1]$ | Heuristic tổng hợp nhẹ |

**Trọng tâm khả thi (feasibility):** Điểm mấu chốt của phiên bản đã chỉnh sửa là $V_i$ và $C_i$ **không** phát sinh thêm mô hình học sâu nặng trên thiết bị biên.

### 1.1. Công thức độ tin cậy $C_i$

$$
C_i = \sigma\!\big(b_0 + b_1 \cdot \mathbb{1}[\text{có ảnh}] + b_2 \cdot \log(1 + n_i^{\text{corrob}})\big)
$$

- $\sigma(x) = \dfrac{1}{1 + e^{-x}}$ là hàm **sigmoid**, ép kết quả về khoảng $(0, 1)$ để $C_i$ luôn là một hệ số tin cậy hợp lệ.
- $\mathbb{1}[\text{có ảnh}]$ là **hàm chỉ thị (indicator)**: bằng $1$ nếu báo cáo kèm ảnh/video đã được mô hình thị giác xác thực, bằng $0$ nếu chỉ có văn bản. Bằng chứng đa phương thức làm tăng độ tin cậy.
- $n_i^{\text{corrob}}$ là **số báo cáo độc lập lân cận** (cùng vùng, cùng cửa sổ thời gian) củng cố cho báo cáo $i$. Nhiều nguồn độc lập cùng xác nhận thì tin cậy hơn.
- $\log(1 + n_i^{\text{corrob}})$ dùng **nén logarit**: báo cáo thứ 2 và thứ 3 làm tăng tin cậy mạnh, nhưng báo cáo thứ 50 gần như không thêm gì — tránh việc spam cùng một vị trí thổi phồng độ tin cậy.
- $b_0, b_1, b_2$ là các hệ số hiệu chỉnh (bias và trọng số), đặt bằng chuyên gia hoặc học từ dữ liệu.

**Vì sao là heuristic thay vì mô hình học?** Đề tài 6 tháng không có hạ tầng tài khoản dài hạn (để tính lịch sử xác thực người dùng) hay mạng cảm biến vật lý (để đối chiếu). Heuristic này chỉ dùng tín hiệu sẵn có nên khả thi ngay; các cơ chế nâng cao được ghi nhận là hướng mở rộng.

---

## 2. Hàm trọng số cạnh $w_{ij}$ (Mục 4.2)

Đây là công thức được **sửa lỗi thiết kế quan trọng nhất**. Phiên bản gốc dùng tổ hợp cộng; phiên bản mới dùng dạng nhân/gating.

$$
w_{ij} = \mathcal{S}_{geo}(L_i, L_j) \cdot \Big( \beta \cdot \mathcal{S}_{temp}(T_i, T_j) + \gamma \cdot \mathcal{S}_{context}(v_i, v_j) \Big)
$$

### 2.1. Vì sao chuyển từ CỘNG sang NHÂN?

**Dạng cũ (sai):**

$$
w_{ij} = \alpha \mathcal{S}_{geo} + \beta \mathcal{S}_{temp} + \gamma \mathcal{S}_{context}
$$

Vấn đề: các số hạng cộng ngang hàng nhau. Hai sự kiện cách nhau **50 km** ($\mathcal{S}_{geo} \approx 0$) nhưng cùng mô tả "ngập lút mái nhà" ($\mathcal{S}_{context} \approx 1$) vẫn nhận $w_{ij} \approx \gamma$ — một trọng số đáng kể. Thuật toán phân cụm sẽ gom hai điểm cách xa nhau vào cùng một cụm, tạo ra "khu vực tác chiến" trải dài vô nghĩa cho việc điều ca nô.

**Dạng mới (đúng):** $\mathcal{S}_{geo}$ nằm **ngoài** làm thừa số nhân, đóng vai trò **cổng chặn (gate)**:

- Khoảng cách lớn $\Rightarrow \mathcal{S}_{geo} \to 0 \Rightarrow w_{ij} \to 0$, bất kể ngữ cảnh giống nhau đến đâu.
- Chỉ khi hai sự kiện vừa gần về địa lý *và* tương đồng về thời gian/ngữ cảnh thì cạnh mới mạnh.

Đây chính là ý nghĩa "địa lý chi phối cấu trúc cụm" — phù hợp bản chất bài toán điều phối ca nô có bán kính hoạt động hữu hạn.

### 2.2. Thành phần không gian $\mathcal{S}_{geo}$

$$
\mathcal{S}_{geo} = \exp\left( - \frac{\text{dist}(L_i, L_j)^2}{2\sigma_{geo}^2} \right)
$$

- Đây là **nhân Gaussian (Gaussian kernel)**. Khi $\text{dist} = 0$ thì $\mathcal{S}_{geo} = 1$ (trùng vị trí, tương đồng tối đa); khi $\text{dist} \to \infty$ thì $\mathcal{S}_{geo} \to 0$.
- $\text{dist}(L_i, L_j)$ là **khoảng cách Haversine** (mét) — công thức tính khoảng cách trên mặt cầu giữa hai tọa độ GPS, chính xác hơn khoảng cách Euclidean cho tọa độ địa lý.
- $\sigma_{geo}$ là **bán kính đặc trưng**: kiểm soát tốc độ suy giảm. Đặt xấp xỉ tầm hoạt động của một ca nô (vài trăm mét đến 1–2 km). Khi $\text{dist} = \sigma_{geo}$, giá trị giảm còn $e^{-1/2} \approx 0.61$; khi $\text{dist} = 3\sigma_{geo}$, giá trị gần như bằng 0.
- Bình phương khoảng cách ($\text{dist}^2$) khiến hàm suy giảm rất nhanh — phạt mạnh các liên kết xa.

### 2.3. Thành phần thời gian $\mathcal{S}_{temp}$

$$
\mathcal{S}_{temp} = \exp\left( - \frac{|T_i - T_j|}{\tau_{temp}} \right)
$$

- Dạng **suy giảm mũ (exponential decay)** theo độ chênh lệch thời gian tuyệt đối.
- $\tau_{temp}$ là **hằng số thời gian** (ví dụ 30–60 phút): sau khoảng thời gian này độ liên kết giảm còn $1/e \approx 0.37$.
- Trực giác: hai báo cáo cách nhau vài phút nhiều khả năng cùng một diễn biến lũ; cách nhau vài giờ thì có thể là hai đợt/hai tình huống khác nhau.
- Dùng $|T_i - T_j|$ bậc nhất (không bình phương) vì thời gian không cần phạt gắt như không gian — diễn biến lũ có quán tính kéo dài.

### 2.4. Thành phần ngữ cảnh $\mathcal{S}_{context}$

Phiên bản gốc chỉ mô tả bằng lời; phiên bản mới **định nghĩa tường minh**:

$$
\mathcal{S}_{context} = \exp\left( - \frac{|F_i - F_j|}{\tau_F} - \frac{|E_i - E_j|}{\tau_E} \right)
$$

- Đo **sự tương đồng về tình trạng vật lý** giữa hai sự kiện qua hai chênh lệch: mức ngập $\Delta F = |F_i - F_j|$ và mức khẩn cấp $\Delta E = |E_i - E_j|$.
- Khi hai báo cáo giống nhau ($\Delta F \approx 0, \Delta E \approx 0$): $\mathcal{S}_{context} \to 1$ (liên kết mạnh, tạo quần thể đồng nhất).
- Khi khác biệt lớn (một người ngập nhẹ an toàn tầng 3, một người bám mái nhà): $\Delta F$ lớn $\Rightarrow \mathcal{S}_{context}$ co lại — phản ánh nhu cầu cứu hộ khác nhau nên không nên gom chung.
- $\tau_F, \tau_E$ kiểm soát độ nhạy: giá trị nhỏ thì hàm phạt gắt hơn với chênh lệch nhỏ.
- Cộng hai số hạng trong hàm mũ tương đương **nhân hai hàm mũ riêng**: $\exp(-a-b) = \exp(-a)\exp(-b)$, nghĩa là hai điều kiện (giống về ngập VÀ giống về khẩn cấp) phải đồng thời thỏa mãn thì $\mathcal{S}_{context}$ mới cao.

### 2.5. Tham số cân bằng và làm thưa đồ thị

- $\beta, \gamma$ cân bằng đóng góp giữa thời gian và ngữ cảnh. $\alpha$ (của dạng cộng cũ) bị loại vì $\mathcal{S}_{geo}$ nay là thừa số điều biến toàn cục.
- **Làm thưa đồ thị (sparsification):** vì $\mathcal{S}_{geo}$ suy giảm nhanh, hầu hết cạnh xa có trọng số không đáng kể. Ta giữ đồ thị thưa bằng một trong hai cách:
  - **Ngưỡng $\epsilon$:** chỉ giữ cạnh khi $w_{ij} > \theta$.
  - **k-NN graph:** mỗi đỉnh chỉ nối với $k$ láng giềng trọng số cao nhất.
- Lý do: thuật toán tối ưu Modularity hoạt động kém trên đồ thị dày đặc gần-hoàn-chỉnh, và các cạnh xa yếu chỉ gây nhiễu.

---

## 3. Hàm Modularity và thuật toán Louvain (Mục 4.3)

$$
Q = \frac{1}{2m} \sum_{i,j} \left[ A_{ij} - \lambda \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)
$$

- $A_{ij}$ = trọng số cạnh giữa đỉnh $i$ và $j$ (chính là $w_{ij}$ đã tính ở Mục 2).
- $k_i = \sum_j A_{ij}$ = tổng trọng số các cạnh gắn với đỉnh $i$ (bậc trọng số).
- $m = \frac{1}{2}\sum_{i,j} A_{ij}$ = tổng trọng số toàn đồ thị.
- $\delta(c_i, c_j)$ = **hàm Kronecker delta**: bằng $1$ nếu $i, j$ cùng cụm, $0$ nếu khác cụm. Nghĩa là tổng chỉ tính các cặp trong cùng cộng đồng.
- $\dfrac{k_i k_j}{2m}$ = trọng số cạnh **kỳ vọng** giữa $i, j$ nếu các cạnh được nối ngẫu nhiên (mô hình null). Modularity đo phần **vượt trội** của mật độ cạnh thực tế so với ngẫu nhiên.
- $\lambda$ = **tham số độ phân giải (resolution parameter)**. Đây là dạng **Reichardt–Bornholdt**:
  - $\lambda = 1$: Modularity chuẩn.
  - $\lambda > 1$: phạt mạnh số hạng kỳ vọng $\Rightarrow$ thuật toán chia nhỏ hơn, tìm ra các cụm vi mô dày đặc (phân rã phường thành khu phố).
  - $\lambda < 1$: khuyến khích cụm lớn.

**Vì sao chọn Louvain?** (1) Tự động tìm số cụm — không cần biết trước như K-Means; (2) khử nhiễu cấu trúc — báo cáo giả thiếu cạnh mạnh nên bị đẩy thành cụm đơn lẻ; (3) độ phức tạp $\mathcal{O}(N \log N)$, chạy được thời gian thực; (4) khả thi với sinh viên qua thư viện `python-louvain`/`networkx`/`igraph`.

**Khuyến nghị Leiden:** Louvain đôi khi tạo cộng đồng **đứt gãy nội bộ** (các đỉnh cùng cụm nhưng không thực sự liên thông). Khi cụm dùng để điều ca nô, điều này khiến trọng tâm cụm sai lệch. Thuật toán **Leiden** bổ sung bước đảm bảo cộng đồng liên thông tốt, giữ nguyên hàm mục tiêu Modularity — nên dùng thay thế khi độ chính xác không gian là sống còn.

---

## 4. Hàm ưu tiên cấp cụm $\mathcal{P}(C_k)$ (Mục 4.4)

Đây là công thức thứ hai được **sửa lỗi toán học nghiêm trọng**. Bốn điểm sửa của bản gốc: (a) sai lệch thang đo, (b) $\mathcal{V}$ cộng thay vì nhân, (c) $\tanh$ bão hòa quá nhanh, và (d) $\mathcal{F}_{max}$ chưa gate $C_i$ (thiếu nhất quán chống tin giả — xem Mục 4.3).

$$
\mathcal{P}(C_k) = \mathcal{V}_{agg}(C_k) \cdot \Big( \omega_1 \widetilde{\mathcal{E}}_{agg}(C_k) + \omega_2 \widetilde{\mathcal{F}}_{max}(C_k) + \omega_3 \widetilde{\mathcal{N}}(C_k) \Big)
$$

### 4.1. Lỗi (a): Sai lệch thang đo và bước chuẩn hóa

**Vấn đề bản gốc:** $\mathcal{E}_{agg} \in [0,1]$, $\mathcal{F}_{max} \in [0,1]$, nhưng $\mathcal{N}_{total} = \sum N_i$ **không bị chặn** (có thể hàng trăm). Cộng trực tiếp thì $\mathcal{N}_{total}$ áp đảo, biến $\mathcal{P}$ gần như chỉ còn phản ánh số người, vô hiệu hóa các yếu tố khác.

**Cách sửa:** chuẩn hóa mọi thành phần về $[0,1]$ *trước khi* nhân trọng số (ký hiệu $\widetilde{(\cdot)}$). Với dân số, do phân phối lệch phải, dùng nén log rồi min-max:

$$
\widetilde{\mathcal{N}}(C_k) = \frac{\log(1 + \mathcal{N}_{total}(C_k))}{\log(1 + N_{\max})}
$$

- $N_{\max}$ = mốc dân số tham chiếu (tổng dân số của cụm lớn nhất trong cửa sổ hiện tại).
- $\log$ nén khoảng cách giữa các cụm rất đông và cụm vừa: chênh lệch 10 vs 20 người quan trọng hơn 500 vs 510 người.
- Chia cho $\log(1+N_{\max})$ ép về $[0,1]$.

### 4.2. Thành phần Khẩn cấp trung bình $\mathcal{E}_{agg}$

$$
\mathcal{E}_{agg}(C_k) = \frac{1}{|C_k|} \sum_{v_i \in C_k} E_i \cdot C_i
$$

- Trung bình mức khẩn cấp, **có trọng số theo độ tin cậy** $C_i$: báo cáo đáng tin đóng góp nhiều hơn, báo cáo nghi ngờ bị giảm ảnh hưởng.
- $|C_k|$ = số sự kiện trong cụm.

### 4.3. Thành phần Ngập tối đa $\mathcal{F}_{max}$

$$
\mathcal{F}_{max}(C_k) = \max_{v_i \in C_k}\big(F_i \cdot C_i\big)
$$

- Dùng $\max$ **không phải** trung bình — quyết định chuyên môn theo **nguyên lý bình thông nhau**: trong một cụm địa lý gắn kết, điểm ngập sâu nhất quyết định rủi ro sinh tồn cao nhất của cả quần thể. Lấy trung bình sẽ làm loãng cảnh báo khi chỉ vài điểm ngập nặng.
- **Gate $C_i$ bên trong $\max$** (bổ sung so với bản gốc): nhân $C_i$ *bên trong* hàm $\max$ để một báo cáo giả khai $F=1{,}0$ với $C_i$ thấp không tự chiếm trọn $\mathcal{F}_{max}$ của cả cụm. Nếu chỉ dùng $\max F_i$ thuần thì $\mathcal{E}_{agg}$ và $\mathcal{N}_{total}$ đã gate $C_i$ nhưng $\mathcal{F}_{max}$ thì không — thiếu nhất quán, tạo lỗ hổng để một báo cáo đơn lẻ không đáng tin thao túng thứ hạng. Với $\max(F_i \cdot C_i)$, cả ba thành phần lõi rủi ro ($\mathcal{E}, \mathcal{F}, \mathcal{N}$) đều nhất quán chống tin giả.

### 4.4. Thành phần Quy mô sinh mạng $\mathcal{N}_{total}$

$$
\mathcal{N}_{total}(C_k) = \sum_{v_i \in C_k} N_i \cdot C_i
$$

- Tổng số người, **nhân trọng số tin cậy** $C_i$ (bổ sung so với bản gốc): một báo cáo giả thổi phồng "500 người mắc kẹt" với $C_i$ thấp không thể tự động đẩy cụm lên đầu danh sách.
- Sau đó nén log và chuẩn hóa thành $\widetilde{\mathcal{N}}$ như Mục 4.1.

### 4.5. Lỗi (b) và (c): Hệ số khuếch đại tổn thương $\mathcal{V}_{agg}$

$$
\mathcal{V}_{agg}(C_k) = 1 + \tanh\!\left( \frac{1}{s} \sum_{v_i \in C_k} V_i \right)
$$

**Lỗi (b) — cộng vs nhân:** Bản gốc đặt $\mathcal{V}$ như số hạng cộng $\omega_4 \mathcal{V}_{agg}$. Nhưng văn bản gọi $V$ là "hệ số nhân/khuếch đại" — mâu thuẫn. Một số hạng cộng bị chặn trong $[1,2]$ chỉ tạo offset gần hằng số, **không khuếch đại gì**. Cách sửa: tách $\mathcal{V}_{agg}$ ra **ngoài làm thừa số nhân** cho toàn bộ lõi rủi ro. Khi đó:
- Cụm không có đối tượng yếu thế: $\mathcal{V}_{agg} \approx 1$ → lõi rủi ro giữ nguyên.
- Cụm nhiều đối tượng yếu thế: $\mathcal{V}_{agg} \to 2$ → điểm ưu tiên được nhân đôi. Đây mới đúng nghĩa "amplify equity".

**Lỗi (c) — bão hòa sớm:** Nếu dùng $\tanh(\sum V_i)$ trực tiếp, chỉ 2–3 đối tượng yếu thế đã đưa $\sum V_i \gtrsim 3$, làm $\tanh$ sát 1. Hệ quả: cụm có 1 người yếu thế và cụm có 50 người yếu thế nhận điểm gần như nhau — mất khả năng phân biệt, đi ngược mục tiêu công bằng. Cách sửa: thêm **hệ số tỉ lệ** $s$ (ví dụ $s=10$) chia trong đối số $\tanh$, giãn vùng tuyến tính để hệ số tăng dần có ý nghĩa theo số lượng.

**Vai trò $\tanh$:** vẫn giữ để chặn trên (đối số lớn thì $\tanh \to 1$, nên $\mathcal{V}_{agg} < 2$), tránh điểm số bùng nổ vô cực. Miền giá trị: $\mathcal{V}_{agg} \in (1, 2)$.

**Lựa chọn thay thế:** $1 + \log(1 + \sum V_i)$ kèm chuẩn hóa cũng chống bão hòa tương đương.

### 4.6. Trọng số quyết định và miền giá trị cuối

- $\omega_1, \omega_2, \omega_3$ với ràng buộc $\sum \omega = 1$, do ban chỉ huy đặt qua **Ma trận Quyết định**. Tinh chỉnh để chuyển trạng thái chiến thuật (ưu tiên số đông vs ưu tiên ngập sâu).
- Vì lõi đã chuẩn hóa $[0,1]$ và $\sum\omega = 1$, lõi rủi ro $\in [0,1]$; nhân với $\mathcal{V}_{agg} \in (1,2)$ cho $\mathcal{P}(C_k) \in (0, 2]$ — chặn gọn, dễ xếp hạng và diễn giải.

---

## 5. Tổng kết các thay đổi so với bản gốc

| Vị trí | Công thức gốc | Công thức sửa | Lý do |
| :--- | :--- | :--- | :--- |
| 4.1 $V_i$ | "NLP sâu" riêng biệt | Nhánh multi-label ghép chung DistilBERT | Khả thi tại biên, không thêm mô hình nặng |
| 4.1 $C_i$ | Lịch sử người dùng / cảm biến vật lý | Heuristic sigmoid nhẹ | Hạ tầng gốc không tồn tại trong đề tài 6 tháng |
| 4.2 $w_{ij}$ | Cộng: $\alpha S_g + \beta S_t + \gamma S_c$ | Nhân/gating: $S_g \cdot (\beta S_t + \gamma S_c)$ | Địa lý phải là cổng chặn để cụm gắn kết không gian |
| 4.2 $S_{temp}, S_{context}$ | Chỉ mô tả bằng lời | Công thức mũ tường minh | Cần định nghĩa rõ để cài đặt được |
| 4.2 | (không có) | Thêm sparsification (ε / k-NN) | Louvain hoạt động kém trên đồ thị dày đặc |
| 4.3 | Nhắc Leiden thoáng qua | Nhấn mạnh Leiden chống đứt gãy cụm | Trọng tâm cụm sai làm điều ca nô sai |
| 4.4 | Cộng 4 hạng tử chưa chuẩn hóa | Chuẩn hóa $[0,1]$ + tách $\mathcal{V}_{agg}$ làm thừa số | Sửa sai lệch thang đo và ý nghĩa "khuếch đại" |
| 4.4 $\mathcal{N}$ | $\sum N_i$ | $\sum N_i \cdot C_i$ rồi nén log | Chống báo giả thổi phồng số người |
| 4.4 $\mathcal{F}_{max}$ | $\max F_i$ | $\max(F_i \cdot C_i)$ | Gate $C_i$ cho nhất quán chống tin giả với $\mathcal{E}, \mathcal{N}$ |
| 4.4 $\mathcal{V}_{agg}$ | $\tanh(\sum V_i)$ | $\tanh(\frac{1}{s}\sum V_i)$ | Chống bão hòa sớm, giữ khả năng phân biệt |
