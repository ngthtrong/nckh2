# Phản biện Nội bộ: Điểm Mơ hồ, Chưa rõ, và Lỗ hổng Lập luận

> **Mục đích.** Tài liệu này đóng vai một phản biện (reviewer) khó tính, rà soát `BaiBao_NoiDung.md` và `PaperV2.md` để tìm các điểm mơ hồ, phát biểu chưa được chứng minh, và lỗ hổng lập luận — trước khi nộp. Mỗi mục ghi: **vị trí**, **vấn đề**, **mức độ** (🔴 nghiêm trọng / 🟠 trung bình / 🟡 nhỏ), và **đề xuất khắc phục**. Đây là bản đọc độc lập, KHÔNG lặp lại Phụ lục B của `BaiBao_NoiDung.md` (dù có tham chiếu chéo khi trùng).
>
> Ngày lập: 2026-07-08.

---

## Tóm tắt điều hành (đọc trước)

Bài báo có phương pháp vững, thực nghiệm trung thực (đáng khen: tự thừa nhận exp3 không tạo được cụm đứt gãy thay vì bịa). Nhưng còn **năm nhóm điểm yếu cốt lõi** mà một phản biện hội nghị sẽ nhắm vào:

1. **Vòng lặp lý luận (circularity) giữa gom cụm và ưu tiên** — chưa được định lượng, mới chỉ thừa nhận bằng lời.
2. **Con số "100 km → 0,30 km" là hệ quả tất yếu của định nghĩa, không phải phát hiện** — dễ bị bắt lỗi phóng đại.
3. **Equity chưa có thước đo kết quả** — mới chứng minh $V$ *đổi* thứ hạng, chưa chứng minh thứ hạng mới *tốt hơn*.
4. **Toàn bộ kết luận dựa trên một bộ dữ liệu synthetic tự sinh** — nguy cơ đánh giá vòng tròn (self-fulfilling).
5. **Nhiều tham số tự do, chưa có quy trình định cỡ (calibration)** — $\sigma_{geo}, \tau_F, \tau_E, \beta, \gamma, s, b_0, b_1, b_2, \theta, k, \lambda, \omega$ — quá nhiều bậc tự do cho một bộ dữ liệu.

Chi tiết bên dưới.

---

## 1. Lỗ hổng lập luận (nghiêm trọng nhất)

### 1.1. 🔴 Circularity giữa $\mathcal{S}_{context}$ và $\mathcal{F}_{max}/\mathcal{E}_{agg}$ chưa được định lượng
**Vị trí:** BaiBao §4.4 (ghi chú cuối), PaperV2 §4.4 (đoạn "Ghi chú về việc dùng lại $F, E$").

**Vấn đề.** Bài đã *thừa nhận* rằng $F, E$ vừa quyết định gom cụm (qua $\mathcal{S}_{context}$) vừa quyết định thứ hạng (qua $\mathcal{F}_{max}, \mathcal{E}_{agg}$), và biện minh rằng "similarity ≠ absolute severity". Biện minh này **đúng về mặt khái niệm nhưng chưa đủ**: vì cụm được gom *vì* $F$ tương đồng, $\mathcal{F}_{max}$ của cụm gần như bị quyết định trước bởi tiêu chí gom. Hệ quả thực tế: điểm ưu tiên $\mathcal{P}$ có thể chỉ đang "đọc lại" cấu trúc mà chính nó tạo ra, thổi phồng vẻ mạch lạc của hệ thống.

**Vì sao là lỗ hổng.** Một reviewer sẽ hỏi: "Nếu tôi gom cụm *chỉ* bằng không gian–thời gian (bỏ $F, E$ khỏi $\mathcal{S}_{context}$), rồi vẫn tính $\mathcal{P}$ như cũ, thứ hạng có đổi nhiều không?" Nếu **không đổi**, thì việc đưa $F, E$ vào $\mathcal{S}_{context}$ là thừa; nếu **đổi nhiều**, thì cần chứng minh hướng đổi là *tốt hơn*. Hiện chưa có thí nghiệm nào trả lời.

**Đề xuất.** Thêm một ablation: (i) đồ thị gating chỉ dùng $\mathcal{S}_{geo}\cdot\mathcal{S}_{temp}$ (bỏ $\mathcal{S}_{context}$) → đo lại ARI và tương quan thứ hạng $\mathcal{P}$ với phiên bản đầy đủ. Báo cáo Kendall's τ giữa hai bảng xếp hạng. Nếu τ cao → thừa nhận $\mathcal{S}_{context}$ đóng góp ít cho *ranking* (chỉ giúp *gom cụm*); nếu τ thấp → cần lập luận vì sao ranking mới đúng hơn.

### 1.2. 🔴 Equity: chứng minh "đổi" chưa phải chứng minh "đúng hơn"
**Vị trí:** BaiBao §5.2 (1C), PaperV2 §4bis (Thí nghiệm 1C).

**Vấn đề.** Thí nghiệm 1C cho thấy $\mathcal{V}_{agg}$ dạng nhân *thay đổi* thứ hạng so với dạng cộng và so với không có $V$. Nhưng đây là lập luận **mô tả (descriptive)**, không phải **chuẩn tắc (normative)**: nó không chứng minh thứ hạng có-equity là *đúng đắn hơn về mặt đạo đức cứu hộ*. Toàn bộ Khe hở 2 (đóng góp lớn thứ hai của bài) đang dựa trên một tiền đề chưa được bảo vệ.

**Vì sao là lỗ hổng.** "Khuếch đại nhóm yếu thế" nghe hợp lý, nhưng nếu khuếch đại quá tay, một cụm 2 người yếu thế có thể vượt một cụm 40 người khỏe mạnh đang ngập sâu hơn — đó có phải kết quả *mong muốn* không? Bài chưa định nghĩa "công bằng" một cách vận hành được (operational), nên không thể nói hàm $\mathcal{P}$ đạt được nó.

**Đề xuất.** Chọn một trong hai hướng: (a) **định nghĩa một thước đo kết quả** — ví dụ "thời gian trung bình mô phỏng đến nạn nhân yếu thế" dưới một chính sách điều phối tham lam theo $\mathcal{P}$ — rồi cho thấy dạng nhân giảm thời gian này so với baseline; hoặc (b) trích một **khung đạo đức chuẩn tắc** (ví dụ nguyên tắc ưu tiên người dễ tổn thương trong triage y tế/thảm họa) và ánh xạ tường minh $\mathcal{V}_{agg}$ vào khung đó, thừa nhận đây là *lựa chọn giá trị* chứ không phải kết quả tối ưu khách quan.

### 1.3. 🟠 "Số đông" vs "yếu thế" có thể xung đột — chưa phân tích trade-off
**Vị trí:** BaiBao §4.4 (trọng số $\omega$ + thừa số $\mathcal{V}_{agg}$).

**Vấn đề.** $\mathcal{V}_{agg}\in(1,2)$ nhân *toàn bộ* lõi. Một cụm có lõi rủi ro thấp nhưng nhiều người yếu thế có thể bị đẩy lên trên một cụm lõi cao ít người yếu thế. Bài không khảo sát khi nào sự đảo thứ hạng này xảy ra, cũng không cho ban chỉ huy công cụ kiểm soát mức khuếch đại tối đa (hiện cứng ở 2×).

**Đề xuất.** Thêm một tham số trần khuếch đại $\mu$ (ví dụ $\mathcal{V}_{agg}=1+(\mu-1)\tanh(\cdot)$, $\mu\in[1,2]$) để ban chỉ huy điều chỉnh; hoặc thêm một biểu đồ minh họa "vùng đảo thứ hạng" theo $(\text{lõi}, \sum V)$.

---

## 2. Phát biểu định lượng chưa được chống lưng / dễ bị bắt lỗi phóng đại

### 2.1. 🔴 "100 km → 0,30 km" bị đóng khung như phát hiện, thực ra là tautology
**Vị trí:** Abstract, §5.2 (1A), §8 của cả hai file.

**Vấn đề.** Với $\sigma_{geo}=700$ m, gating **định nghĩa** rằng cạnh giữa hai điểm cách nhau >2–3 km có trọng số ~0. Do đó cụm buộc phải nhỏ về đường kính — đây là *hệ quả toán học tất yếu của định nghĩa*, không phải một kết quả thực nghiệm bất ngờ. Đóng khung nó như thành tựu chính (lặp lại ở abstract và kết luận) làm reviewer nghi ngờ tính nghiêm túc.

**Điểm giá trị thật** (Phụ lục B của BaiBao cũng đã nhận ra): gating co đường kính **mà KHÔNG làm giảm ARI (giữ 0,892)**. Vế sau mới là điều đáng nói — nó cho thấy việc ép gắn kết không gian không phá vỡ độ chính xác so với ground-truth.

**Đề xuất.** Viết lại mọi chỗ nhắc con số này theo dạng: "gating đạt cụm gắn kết không gian (đường kính 0,30 km) *mà không hy sinh* ARI (0,892 ở cả hai dạng)". Bỏ ngôn ngữ ngụ ý "phát hiện". Đã áp dụng đúng trong bản LaTeX (`paper/main.tex`) — cần đồng bộ ngược lại hai file nguồn.

### 2.2. 🟠 ARI 0,892 lặp lại y hệt ở quá nhiều cấu hình — nghi ngờ độ phân giải của thước đo
**Vị trí:** §5.2, §5.5 (bảng baseline).

**Vấn đề.** Additive, gating, Agglomerative, và nhiều mức $\sigma_{geo}/\lambda$ đều cho **đúng ARI = 0,892**. Sự trùng khớp tuyệt đối này gợi ý rằng ground-truth quá dễ tách, nên ARI đã bão hòa và không còn phân biệt được chất lượng phương pháp. Nói cách khác, ARI đang không làm việc như một thước đo phân biệt trong thiết lập này.

**Vì sao là lỗ hổng.** Nếu mọi phương pháp "đủ hợp lý" đều đạt 0,892, thì ARI không phải bằng chứng cho ưu thế của phương pháp đề xuất — ưu thế phải đến từ *đường kính cụm*, mà đường kính lại là tautology (mục 2.1). Đóng góp thực nghiệm bị kẹt giữa hai thước đo, một cái bão hòa một cái tất yếu.

**Đề xuất.** (i) Làm ground-truth **khó hơn** — cho các ốc đảo chồng lấn một phần, thêm nhiễu không gian — để ARI trải ra và phân biệt được phương pháp. (ii) Bổ sung thước đo thứ ba độc lập với cả hai: ví dụ độ tinh khiết cụm theo nhãn, hoặc một outcome-metric (mục 1.2).

### 2.3. 🟡 "MB → KB" và độ trễ mili-giây: claim mượn, không đo trong hệ thống này
**Vị trí:** Abstract, §2.2, bảng §6 của cả hai file.

**Vấn đề.** Con số "giảm từ MB xuống KB" và "độ trễ mili-giây" được dẫn từ EmergencyNet/tài liệu Edge AI khác, KHÔNG phải đo trên prototype của đề tài. Bài trình bày chúng như đặc tính của hệ thống đề xuất. Phụ lục B đã bắt lỗi claim 500 ms của ResQConnect; nhưng vấn đề rộng hơn: **toàn bộ nhánh "khả thi tại biên" chưa có một phép đo thực nào từ chính prototype**.

**Đề xuất.** Hoặc (a) đo thật: kích thước gói JSON metadata trung bình (dễ — chỉ cần serialize $(L,T,F,E,N,V,C)$), thời gian inference MobileNetV3+DistilBERT trên một điện thoại tầm trung; hoặc (b) phát biểu rõ ràng đây là *lập luận thiết kế dựa trên tài liệu*, chưa đo trên prototype, và chuyển sang thì tương lai/điều kiện.

### 2.4. 🟡 $\mathcal{O}(N\log N)$ chỉ là quan sát, không phải chứng minh
**Vị trí:** §2.4 cả hai file (BaiBao đã cẩn thận ghi "chưa có chứng minh cận trên hình thức").

**Vấn đề.** BaiBao đã xử lý đúng (nói "quan sát được"). Nhưng PaperV2 §2.4 vẫn ghi thẳng "$\mathcal{O}(N\log N)$" như một đặc tính. Cần đồng bộ: Louvain không có đảm bảo độ phức tạp hình thức; đây là hành vi thực nghiệm điển hình.

**Đề xuất.** Sửa PaperV2 cho khớp cách diễn đạt thận trọng của BaiBao. Trong bản LaTeX đã dùng "observed near-$\mathcal{O}(N\log N)$" — đúng hướng.

---

## 3. Điểm mơ hồ / chưa rõ (cần định nghĩa lại)

### 3.1. 🟠 $V_i$: "tổng trọng số các đối tượng yếu thế" — thang đo và trọng số nhãn chưa định nghĩa
**Vị trí:** §4.1 cả hai file, bảng thuộc tính ($V_i \ge 0$).

**Vấn đề.** $V_i$ được mô tả là "tổng trọng số của các đối tượng yếu thế, mỗi nhãn đóng góp trọng số $\ge 1$ theo mức độ ưu tiên nhân đạo". Nhưng: (a) trọng số cụ thể của từng nhãn (trẻ sơ sinh vs người già vs phụ nữ mang thai vs khuyết tật) là bao nhiêu? (b) ai quyết định thang này? (c) dataset synthetic hiện chỉ dùng **4 mức rời rạc** cho `vulnerability` ($\{0{,}0;\,1{,}0;\,1{,}5;\,2{,}0\}$) ở cấp *sự kiện* — nhưng công thức nói $V_i$ là "tổng trọng số các nhãn phát hiện được" ở cấp *báo cáo*. Ánh xạ giữa 4 mức rời rạc này và tập nhãn (sơ sinh/già/mang thai/khuyết tật) không được nêu, nên không rõ giá trị 1,5 tương ứng tổ hợp nhãn nào.

**Vì sao quan trọng.** Toàn bộ đóng góp equity phụ thuộc $V_i$, nhưng định nghĩa vận hành của nó lỏng. Việc dataset dùng 4 mức đặt sẵn (thay vì suy ra từ nhãn văn bản như công thức mô tả) nghĩa là thực nghiệm đang kiểm *cơ chế nhân/khuếch đại của $\mathcal{V}_{agg}$*, KHÔNG kiểm *năng lực trích xuất $V_i$ từ văn bản* — cần nói rõ để tránh hiểu nhầm.

**Đề xuất.** Cung cấp một bảng trọng số nhãn tường minh (dù là đề xuất) và ánh xạ nó tới 4 mức trong dataset; nêu rõ rằng thực nghiệm giả định $V_i$ đã cho sẵn (ground-truth vulnerability), còn việc trích $V_i$ từ text là hướng mở rộng chưa kiểm.

### 3.2. 🟠 Hai chế độ $N_{\max}$ (động/cố định) — bài dùng chế độ nào trong thực nghiệm?
**Vị trí:** §4.4 chuẩn hóa $\widetilde{\mathcal{N}}$.

**Vấn đề.** Bài trình bày hai chế độ và thừa nhận chế độ động là non-stationary, nhưng **không nói thí nghiệm dùng chế độ nào**. Điều này ảnh hưởng trực tiếp đến diễn giải Kendall's τ ở exp5: nếu $N_{\max}$ động thay đổi khi $\omega$ đổi (do tập cụm không đổi nhưng... thực ra $N_{\max}$ không phụ thuộc $\omega$), cần xác nhận τ đo đúng cái ta nghĩ.

**Đề xuất.** Nêu rõ chế độ dùng trong mỗi thí nghiệm. Nếu dùng động, thêm một câu cảnh báo khi diễn giải bảng xếp hạng tuyệt đối.

### 3.3. 🟡 $n_i^{corrob}$: ngưỡng đã có trong code nhưng chưa đưa vào bài; "độc lập" chưa định nghĩa
**Vị trí:** §4.1.1 công thức $C_i$ (văn bản); `pipeline/config.py` (code).

**Vấn đề.** Văn bản bài báo chỉ nói "cùng vùng, cùng cửa sổ thời gian" mà không nêu số. Code *đã* cố định $r_{corrob}=400$ m và $\Delta t_{corrob}=60$ phút (tách biệt với $\sigma_{geo}=700$m, $\tau_{temp}=45$ phút — tốt, tránh phụ thuộc chéo). Nhưng hai con số này chưa xuất hiện trong bài, nên người đọc không tái lập được. Ngoài ra "độc lập" được xác định thế nào (cùng tài khoản? cùng thiết bị?) vẫn bỏ ngỏ — trong khi bài nói rõ không có hạ tầng tài khoản dài hạn, nên trên thực tế mọi báo cáo lân cận đều bị đếm là "độc lập", tạo lỗ hổng cho corroboration giả (xem §4.1).

**Đề xuất.** Đưa $(r_{corrob}, \Delta t_{corrob}) = (400\text{m}, 60\text{ph})$ vào bảng tham số §5.1; thảo luận cách (không) phân biệt độc lập khi thiếu ID người dùng và rủi ro kèm theo.

### 3.4. 🟡 $\tau_F=0{,}25$ vs $\tau_E=0{,}35$ — vì sao khác nhau? Chưa giải thích
**Vị trí:** §5.1 tham số mặc định.

**Vấn đề.** Hai hằng số nhạy khác nhau ngụ ý "chênh lệch ngập" được coi trọng hơn "chênh lệch khẩn cấp" trong gom cụm, nhưng không có câu nào biện minh. Đây là lựa chọn tham số tùy ý chưa được lý giải.

**Đề xuất.** Hoặc giải thích (ví dụ: $F$ chính xác hơn $E$ nên phạt gắt hơn), hoặc đặt bằng nhau để loại một bậc tự do, và đưa vào phân tích độ nhạy.

---

## 4. Vấn đề về thiết kế thực nghiệm & tính hợp lệ

### 4.1. 🔴 Toàn bộ bằng chứng đến từ một bộ dữ liệu tự sinh — nguy cơ self-fulfilling
**Vị trí:** §5.1, §7.1 (đã thừa nhận trong Threats to Validity).

**Vấn đề.** Dữ liệu synthetic được sinh với chính mô hình sinh mà phương pháp giả định (ốc đảo Gaussian, nhiễu, tin giả). Điểm đáng khen: pipeline **thực sự tính $C_i$ từ heuristic** (`attributes.py`: sigmoid theo có-ảnh + số báo cáo củng cố trong bán kính 400m/60 phút), KHÔNG hard-code — nên $C_i=0{,}45$ của tin giả S3 xuất hiện *vì* nó cô lập (không có báo cáo củng cố) và không kèm ảnh. Đây là bằng chứng tốt hơn tôi lo ngại ban đầu. **Tuy nhiên**, vòng tròn nằm ở chỗ khác: dataset được thiết kế để tin giả *đúng là* cô lập + không ảnh, nên heuristic tất nhiên gán điểm thấp. Trong thực tế, một tin giả tinh vi (có ảnh giả, hoặc nhiều tài khoản phối hợp tạo "corroboration" giả) sẽ đánh lừa được heuristic — kịch bản này chưa được kiểm.

**Vì sao vẫn là lỗ hổng.** Thí nghiệm 1E/1F chứng minh *cơ chế gate hoạt động khi $C_i$ đã thấp*, nhưng chưa chứng minh *heuristic gán $C_i$ thấp cho tin giả trong tình huống đối kháng*. Reviewer sẽ hỏi: "heuristic của các bạn chịu được adversary phối hợp không?"

**Đề xuất.** (i) Đo trực tiếp: heuristic $C_i$ tương quan thế nào với nhãn `is_fake` — báo cáo AUC/precision như một "bộ phát hiện tin giả yếu". (ii) Thêm kịch bản đối kháng: tin giả *có ảnh* hoặc *có corroboration giả*, xem 1E/1F còn giữ không. (iii) Nhấn mạnh (đã có ở §7.1) đây là kiểm chứng *cơ chế công thức*, và bổ sung rõ giới hạn: heuristic $C_i$ chỉ mạnh với tin giả *ngây thơ* (cô lập, không ảnh).

### 4.2. 🟠 Quá nhiều tham số tự do so với một bộ dữ liệu
**Vị trí:** §5.1.

**Vấn đề.** Đếm nhanh: $\sigma_{geo}, \tau_{temp}, \tau_F, \tau_E, \beta, \gamma, \theta, k, \lambda, s, \omega_1, \omega_2, \omega_3, b_0, b_1, b_2$ — **16 tham số** tinh chỉnh trên một bộ dữ liệu seed=42. Nguy cơ overfitting tham số vào chính bộ test là rõ ràng. Phân tích độ nhạy (exp2) chỉ quét 3 trong 16.

**Đề xuất.** (i) Quét độ nhạy cho các tham số còn lại (ít nhất $\tau_F, \tau_E, \beta/\gamma, \theta, k$). (ii) Nêu rõ tham số nào là "đặt theo miền" (như $\sigma_{geo}$ theo tầm ca nô) vs "tinh chỉnh trên dữ liệu". (iii) Tốt nhất: chia train/validation để đặt tham số, test trên phần giữ lại.

### 4.3. 🟠 exp5 (ổn định xếp hạng) chỉ nhiễu $\omega$ — bỏ qua 13 tham số khác
**Vị trí:** §5.6.

**Vấn đề.** Kendall's τ chỉ đo độ nhạy với $\omega$. Nhưng thứ hạng $\mathcal{P}$ còn phụ thuộc $s$ (qua $\mathcal{V}_{agg}$), $\lambda/\sigma_{geo}$ (qua chính cấu trúc cụm), $b_*$ (qua $C_i$ gate mọi thành phần). Ổn định với $\omega$ không suy ra ổn định tổng thể.

**Đề xuất.** Mở rộng nhiễu loạn sang $s$ và (quan trọng hơn) sang cấu trúc cụm: nếu $\sigma_{geo}$ đổi làm cụm đổi, bảng xếp hạng có còn ổn định không? Đây mới là phép thử robustness thật.

### 4.4. 🟡 Spectral Clustering ARI 0,339 — có thể do cấu hình kém, không phải bản chất
**Vị trí:** §5.5 phân tích baseline.

**Vấn đề.** ARI 0,339 của Spectral thấp bất thường (thấp hơn cả K-Means tọa độ thô). Bài giải thích "đồ thị thưa gây khó phân tách phổ" — hợp lý, nhưng cũng có thể do số cụm $K=27$ ép cho Spectral không tối ưu, hoặc Laplacian chưa chuẩn hóa đúng. Một baseline yếu bất thường làm giảm sức thuyết phục của so sánh.

**Đề xuất.** Kiểm tra cấu hình Spectral (normalized Laplacian? affinity đúng?), thử vài $K$. Nếu vẫn thấp, nêu rõ đã thử tối ưu để tránh mang tiếng "dựng baseline rơm (strawman)".

---

## 5. Vấn đề trình bày & nhất quán giữa hai file

### 5.1. 🟠 PaperV2 §4.4 và BaiBao §4.4: kiểm tra đồng bộ $\mathcal{F}_{max}$
**Trạng thái:** Cả hai file đã dùng $\max(F_i\cdot C_i)$ (đã xác nhận). `GiaiThichCongThuc.md` trước đây còn $\max(F_i)$ — **đã được cập nhật trong phiên này**. ✅

### 5.2. 🟡 Abstract dùng "ARI = 0,89" nhưng thân bài dùng "0,892"
**Vị trí:** Abstract vs §5.

**Vấn đề.** Làm tròn không nhất quán (0,89 vs 0,892; 0,34 vs 0,339; 0,69 vs 0,688). Nhỏ nhưng reviewer kỹ tính sẽ để ý.

**Đề xuất.** Chọn một quy tắc (2 hoặc 3 chữ số thập phân) và áp dụng nhất quán, hoặc nói rõ abstract làm tròn.

### 5.3. 🟡 Phụ lục B (review nội bộ) vẫn nằm trong file nội dung
**Vị trí:** BaiBao §Phụ lục B.

**Vấn đề.** Phụ lục B liệt kê điểm yếu chưa sửa (baseline chưa công bằng, framing 100km...) nhưng phần thân bài §5.5 lại *đã* thêm baseline công bằng. Hai chỗ mâu thuẫn: Phụ lục B nói "cần làm" việc đã làm rồi. Đọc giả nội bộ sẽ bối rối về trạng thái thực.

**Đề xuất.** Cập nhật Phụ lục B: đánh dấu mục nào đã hoàn thành (baseline công bằng ✅, exp5 ổn định ✅, $\mathcal{F}_{max}$ gate ✅), mục nào còn tồn (framing 100km chưa sửa ở §8, exp3 chưa tạo cụm đứt gãy). Đây là công cụ quản lý tiến độ nên phải phản ánh đúng thực tế.

### 5.4. 🟡 Cảnh báo bảo mật trong Phụ lục A vẫn còn hiệu lực
**Vị trí:** BaiBao cuối file.

**Vấn đề.** File `giải trình thay đổi V1 sang V2.md` được ghi là chứa chuỗi giống API key (`sk-...`). Nếu chưa xử lý, đây là rủi ro thật. (Ngoài phạm vi phản biện học thuật nhưng cần nhắc lại.)

**Đề xuất.** Kiểm tra và thu hồi khóa nếu là thật; xóa khỏi file nguồn.

---

## 6. Bảng ưu tiên hành động (cho nhóm tác giả)

| # | Điểm | Mức | Chi phí sửa | Ưu tiên |
| :--- | :--- | :---: | :---: | :---: |
| 1.1 | Ablation circularity ($\mathcal{S}_{context}$ ↔ ranking) | 🔴 | Trung bình | **Cao** |
| 1.2 | Equity cần thước đo kết quả (normative/outcome) | 🔴 | Cao | **Cao** |
| 2.1 | Re-frame "100km→0,30km" (nhấn "giữ ARI") | 🔴 | Thấp | **Cao** |
| 4.1 | Tách "cơ chế công thức" khỏi "năng lực phát hiện $C_i$" | 🔴 | Trung bình | **Cao** |
| 2.2 | ARI bão hòa — làm ground-truth khó hơn | 🟠 | Cao | Trung bình |
| 4.2 | Giảm/khảo sát 16 tham số tự do | 🟠 | Cao | Trung bình |
| 3.1 | Định nghĩa vận hành $V_i$ + khớp với dataset | 🟠 | Thấp | Trung bình |
| 4.3 | Mở rộng exp5 sang $s$ + cấu trúc cụm | 🟠 | Trung bình | Trung bình |
| 1.3 | Trần khuếch đại $\mu$ + phân tích trade-off | 🟠 | Thấp | Trung bình |
| 2.3 | Đo thật (hoặc hạ giọng) claim MB→KB, độ trễ | 🟡 | Thấp | Thấp |
| 3.2–3.4 | Làm rõ $N_{\max}$, $n^{corrob}$, $\tau_F\ne\tau_E$ | 🟡 | Thấp | Thấp |
| 5.1–5.4 | Đồng bộ số liệu, cập nhật Phụ lục B, xử lý khóa | 🟡 | Thấp | Thấp |

---

## 7. Điểm mạnh cần giữ (để không sửa hỏng)

Để cân bằng, các điểm sau đã làm tốt và **không nên** thay đổi:

- **Trung thực về exp3 (Leiden).** Việc thừa nhận không tạo được cụm đứt gãy và diễn giải Leiden là "bảo hiểm miễn phí" thay vì bịa ca bệnh lý là chuẩn mực khoa học tốt. Giữ nguyên.
- **Baseline công bằng trên cùng đồ thị** (§5.5) đã trả lời đúng phản biện "thắng nhờ đồ thị chứ không nhờ thuật toán" — HDBSCAN cùng đồ thị nhưng kém hơn là bằng chứng thuyết phục.
- **Mục Threats to Validity** (§7.1) đã có bốn trục chuẩn — hiếm thấy ở báo cáo sinh viên, là điểm cộng lớn.
- **Sửa lỗi công thức có động cơ rõ ràng** (gating, chuẩn hóa, $\mathcal{V}$ nhân, $\tanh$ chống bão hòa, $\mathcal{F}_{max}$ gate) — mỗi sửa đổi đều gắn một lỗi cụ thể của bản gốc và một thí nghiệm kiểm chứng. Đây là xương sống của đóng góp.

---

*Hết. Tài liệu này nên được đọc cùng Phụ lục B của `BaiBao_NoiDung.md`; các mục trùng đã được ghi chú. Ưu tiên xử lý bốn mục 🔴 trước khi nộp.*
