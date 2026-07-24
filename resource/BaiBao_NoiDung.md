# Khung Đồ thị Trọng số Đa phương thức cho Phân cụm và Ưu tiên Sự kiện Cứu hộ Bão lũ dựa trên Edge AI

> **Ghi chú soạn thảo.** Đây là bản nội dung tiếng Việt dùng để soạn thảo trước cho bài báo khoa học. Nội dung được tổng hợp và kiểm tra chéo từ: (i) `Thuyết minh NCKH.md` (phạm vi đề tài), (ii) `PaperV2.md` (báo cáo nghiên cứu, Mục 4 là phương pháp lõi), (iii) `GiaiThichCongThuc.md` (giải thích chi tiết công thức), (iv) `giải trình thay đổi V1 sang V2.md` (lý do sửa lỗi), và (v) kết quả thực nghiệm định lượng trong `demo/`. Sau khi chốt nội dung, tài liệu này sẽ được chuyển sang định dạng LaTeX chuẩn hội nghị/tạp chí. Các số liệu thực nghiệm trong bài đều lấy trực tiếp từ `demo/results/tables/` (seed = 42, sinh dữ liệu tất định).

---

## Tóm tắt (Abstract)

Trong các thảm họa bão lũ, hạ tầng viễn thông thường bị gián đoạn khiến mô hình xử lý tập trung trên đám mây bị vô hiệu hóa đúng vào "giờ vàng" cứu hộ. Bài báo đề xuất một khung giải pháp kết hợp Điện toán Biên (Edge AI) và Lý thuyết Đồ thị Trọng số để thu thập, phân cụm và tự động xếp hạng ưu tiên các sự kiện cứu hộ. Thiết bị biên trích xuất một vector thuộc tính đa chiều $(L, T, F, E, N, V, C)$ từ ảnh và văn bản rồi chỉ truyền đi một gói siêu dữ liệu (metadata) dưới 1 Kilobyte thay vì ảnh/video thô. Ở phía máy chủ, các sự kiện được biểu diễn thành đồ thị trọng số trong đó khoảng cách địa lý đóng vai trò **cổng chặn nhân tính (multiplicative gate)** thay vì một số hạng cộng, bảo đảm mọi cụm đều gắn kết về mặt không gian. Thuật toán Louvain (khuyến nghị Leiden) phân rã đồ thị thành các "khu vực tác chiến", và một hàm ưu tiên cấp cụm $\mathcal{P}(C_k)$ — với lõi rủi ro đã chuẩn hóa và hệ số tổn thương nhân khẩu học đóng vai trò **thừa số khuếch đại** — xếp hạng các cụm để hỗ trợ điều phối. Thực nghiệm trên bộ dữ liệu mô phỏng 285 sự kiện tại Miền Trung Việt Nam cho thấy: dạng nhân/gating giảm đường kính cụm trung bình từ **100 km xuống 0,30 km** trong khi vẫn giữ nguyên độ chính xác phân cụm (ARI = 0,892); cổng tin cậy $C_i$ chặn được báo cáo giả thổi phồng số nạn nhân (giảm **55%** quy mô dân số ảo); khung đề xuất đạt **ARI 0,892** so với K-Means (0,688), DBSCAN (0,730), và kể cả Spectral Clustering (0,339) và HDBSCAN (0,890 nhưng đường kính 25 km) chạy trên cùng đồ thị gating; xếp hạng ưu tiên ổn định với Kendall's τ ≥ 0,94 khi trọng số dao động ±0,10.

**Từ khóa:** Edge AI, phân cụm sự kiện, đồ thị trọng số, phát hiện cộng đồng, Louvain, ưu tiên cứu hộ, đa phương thức, thảm họa bão lũ.

---

## 1. Giới thiệu

Biến đổi khí hậu đang làm gia tăng tần suất và cường độ của các hiện tượng thời tiết cực đoan. Việt Nam — với đường bờ biển dài và địa hình chịu ảnh hưởng trực tiếp của hoàn lưu bão — mỗi năm hứng chịu khoảng 10–12 cơn bão và áp thấp nhiệt đới, trong đó 5–6 cơn ảnh hưởng trực tiếp đến đất liền, gây thiệt hại nặng nề về người và tài sản, đặc biệt tại miền Trung và miền Bắc.

Một nguyên nhân cốt lõi làm đứt gãy công tác phản ứng khẩn cấp là sự gián đoạn của hạ tầng viễn thông. Khi lưới điện suy kiệt và trạm thu phát sóng (BTS) bị cô lập, các mô hình thu thập – xử lý dữ liệu tập trung (cloud-centric) hoàn toàn thất bại, khiến trung tâm chỉ huy mất kết nối với vùng tâm bão đúng vào "giờ vàng". Trong bối cảnh đó, mạng xã hội và ứng dụng nhắn tin trở thành kênh **cảm biến xã hội (social sensing)** mang tính sinh tồn, sinh ra dòng dữ liệu **đa phương thức** (văn bản, hình ảnh, video, siêu dữ liệu không gian – thời gian) nhưng rời rạc, trùng lặp, nhiều nhiễu, dễ gây **quá tải thông tin**.

Bài báo này đề xuất một khung giải pháp end-to-end giải quyết đồng thời ba thách thức trên:

1. **Sống sót qua mạng yếu:** đưa AI xuống thiết bị biên; thay vì tải ảnh/video hàng Megabyte, ứng dụng xử lý tại chỗ và chỉ gửi gói siêu dữ liệu dưới 1 Kilobyte.
2. **Gom nhóm sự kiện trùng lặp có ý nghĩa vật lý:** xây đồ thị trọng số tích hợp không gian – thời gian – ngữ cảnh, rồi phân rã cộng đồng.
3. **Tự động xếp hạng ưu tiên:** định lượng mức khẩn cấp *cấp cụm* để trả lời câu hỏi điều phối "cứu cụm nào trước".

**Đóng góp chính:**

- Một **hàm trọng số cạnh dạng nhân/gating** trong đó độ tương đồng địa lý điều biến toàn cục độ tương đồng phi-không-gian, bảo đảm các cụm gắn kết về mặt địa lý — điều kiện tiên quyết để điều phối ca nô có bán kính hoạt động hữu hạn.
- Một **hàm ưu tiên cấp cụm** $\mathcal{P}(C_k)$ với lõi rủi ro chuẩn hóa và **hệ số tổn thương nhân khẩu học làm thừa số khuếch đại**, đưa yếu tố công bằng (equity) vào bài toán phân bổ nguồn lực.
- Hai thuộc tính bổ sung **khả thi tại biên**: chỉ số tổn thương $V_i$ (ghép chung bộ phân loại văn bản) và độ tin cậy $C_i$ (heuristic sigmoid nhẹ), có tác dụng chống tin giả.
- **Kiểm chứng thực nghiệm** toàn diện trên bộ dữ liệu mô phỏng đặc thù Miền Trung Việt Nam, chứng minh từng quyết định thiết kế bằng số liệu định lượng.

---

## 2. Tổng quan tình hình nghiên cứu

### 2.1. Phân tích đa phương thức trong khủng hoảng

Sự dịch chuyển từ học máy đơn phương thức sang đa phương thức đã nâng cao đáng kể khả năng nhận thức tình huống (situational awareness) của các hệ thống quản lý thiên tai. Các bộ dữ liệu tiên phong như **CrisisMMD** và **FloodNet** cung cấp nền tảng huấn luyện AI nhận diện mức độ thiệt hại và phân loại thông tin khẩn cấp. Với hình ảnh/video, các mạng tích chập (CNN) như ResNet, MobileNet hoặc mô hình phân đoạn ngữ nghĩa (DeepLabv3+) được dùng để trích xuất vùng ngập; một số nghiên cứu còn ứng dụng **ước lượng tư thế người (Human Pose Estimation)** để suy ra độ sâu mực nước tại nơi không có trạm quan trắc. Với văn bản/âm thanh, các kiến trúc Transformer (BERT, DistilBERT, Bi-LSTM) được dùng để phân tích cảm xúc, nhận diện thực thể và xác định nhu cầu cấp thiết. Các mô hình như CrisisSpot (dùng Graph Neural Network) và SCBD (cross-attention) chứng minh việc hợp nhất đa phương thức cải thiện rõ rệt độ chính xác phân loại nội dung thảm họa.

### 2.2. Dịch chuyển sang Điện toán Biên (Edge Computing)

Thách thức chí mạng của mô hình đa phương thức là nhu cầu băng thông và tính toán. Trong bão lũ, việc tải video/ảnh độ phân giải cao lên đám mây là bất khả thi. Cộng đồng nghiên cứu do đó thúc đẩy **Edge AI**: dùng nén mô hình (Quantization, Knowledge Distillation) và kiến trúc nhẹ để suy luận ngay trên thiết bị. Thiết bị biên chỉ truyền một gói metadata gọn nhẹ (dưới 1 KB, định lượng ở Mục Thảo luận) chứa các thuộc tính đã số hóa, bảo đảm tín hiệu cầu cứu vẫn thâm nhập qua hạ tầng tắc nghẽn. Nền tảng ResQConnect là minh chứng cho việc triển khai mô hình ngôn ngữ thu gọn phân loại/phân luồng (triage) trực tiếp trên thiết bị ở chế độ ngoại tuyến; các con số về độ trễ suy luận nhẹ trên biên (mức mili-giây) được dẫn từ EmergencyNet — kiến trúc CNN nhẹ chạy trên drone/thiết bị nhúng.

### 2.3. Phân tích không gian – thời gian dựa trên đồ thị

Xem mỗi lời kêu cứu như một điểm dữ liệu cô lập làm mất bối cảnh toàn cục. Lý thuyết đồ thị cung cấp khung toán học để mô hình hóa tương tác và lan truyền rủi ro: một sự kiện là một đỉnh trong đồ thị $G=(V,E,W)$, cạnh biểu diễn mối liên hệ, trọng số phản ánh cường độ liên hệ. Các nghiên cứu phát hiện sự kiện thường xây đồ thị dựa trên gần kề không gian – thời gian và đồng xuất hiện từ khóa (ví dụ TwitterNews+ dùng TF-IDF). Các mô hình tiên tiến kết hợp khoảng cách Euclidean/Haversine để **phạt** liên kết giữa các sự kiện cách xa nhau, tạo Geo-Semantic Graph.

### 2.4. Phát hiện cộng đồng (Community Detection)

Các thuật toán không giám sát truyền thống gặp hạn chế: **K-Means** cần biết trước số cụm $K$ (bất khả thi trong thảm họa biến động) và giả định cụm hình cầu; **DBSCAN** nhạy với không gian đa chiều và tham số. Vượt trội hơn là các thuật toán phát hiện cộng đồng dựa trên cấu trúc mạng, đặc biệt là **Louvain**, tiêu chuẩn vàng cho phân cụm đồ thị trọng số thông qua tối ưu hàm **Modularity** $Q$; thực nghiệm cho thấy thuật toán chạy trong thời gian *quan sát được* xấp xỉ $\mathcal{O}(N\log N)$ (chưa có chứng minh cận trên hình thức). Biến thể **Leiden** khắc phục hiện tượng cộng đồng đứt gãy nội bộ (badly connected communities) đôi khi xuất hiện ở Louvain.

### 2.5. Định vị nghiên cứu (Positioning)

Bảng dưới định vị công trình này so với các nghiên cứu tiêu biểu cùng lĩnh vực trên năm trục năng lực. Dấu ✓ = có, ✗ = không, ~ = một phần. Ô trống mà các cột khác không lấp chính là đóng góp của bài báo.

| Nghiên cứu                                    | Đa phương thức | Edge/on-device | Đồ thị trọng số |  Tổn thương (equity)  |  Ưu tiên cấp cụm  |
| :---------------------------------------------- | :----------------: | :------------: | :-------------------: | :----------------------: | :-------------------: |
| CrisisSpot (arXiv 2410.08814)                   |         ✓         |       ✗       |       ✓ (GNN)       |            ✗            |          ✗          |
| SCBD (SSE-Cross-BERT-DenseNet)                  |         ✓         |       ✗       |          ✗          |            ✗            |          ✗          |
| TwitterNews+ / Dong et al. (event detection)    |     ✗ (text)     |       ✗       |      ✓ (TF-IDF)      |            ✗            |          ✗          |
| EmergencyNet (Kyrkou & Theocharides)            |     ✗ (ảnh)     |       ✓       |          ✗          |            ✗            |          ✗          |
| ResQConnect                                     |         ✓         |       ~       |          ✗          |            ✗            |          ✗          |
| Disaster Knowledge Graph (spatiotemporal KG)    |         ✓         |       ✗       |          ✓          |            ✗            |          ✗          |
| Vulnerability-based prioritization (INFOR 2025) |         ✗         |       ✗       |          ✗          |            ✓            | ~ (điểm cấp vùng) |
| **Khung đề xuất (bài này)**          |    **✓**    |  **✓**  | **✓ (gating)** | **✓ (thừa số)** |     **✓**     |

Không nghiên cứu nào trong bảng đồng thời (i) chạy trích xuất đa phương thức tại biên, (ii) mã hóa vào đồ thị trọng số gating không gian – ngữ nghĩa – vật lý, (iii) tích hợp tổn thương nhân khẩu học như hệ số khuếch đại, và (iv) sinh xếp hạng ưu tiên cấp cụm. Đây là khoảng trống mà bài báo lấp.

---

## 3. Xác định khe hở khoa học (Research Gaps)

Rà soát tài liệu cho thấy ba khe hở căn bản, làm tiền đề lý luận cho khung giải pháp đề xuất.

| Khía cạnh                               | Hạn chế hiện hành                                                                              | Khe hở khoa học                                                                                                                |
| :---------------------------------------- | :------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------- |
| **Xây dựng đồ thị trọng số** | Đa số chỉ dùng khoảng cách địa lý hoặc tương đồng TF-IDF để đặt trọng số cạnh | Bỏ qua đặc trưng vật lý sinh tồn; cần hàm trọng số đa chiều tích hợp độ sâu ngập và mức đe dọa sinh mạng |
| **Kiến trúc hệ thống**          | Phụ thuộc mô hình học sâu trên đám mây; sụp đổ khi mạng tê liệt                    | Thiếu khung lai kết hợp trích xuất tại biên + gửi metadata nhẹ để lập đồ thị                                      |
| **Ra quyết định**                | Xem nhu cầu là đồng nhất; không định lượng ưu tiên giữa các cụm                     | Thiếu "Hàm điểm ưu tiên cấp cụm" tích hợp chỉ số tổn thương nhân khẩu học                                      |

**Khe hở 1 — Thiếu thuộc tính đặc thù trong định lượng trọng số.** Hai sự kiện gần nhau về địa lý không đồng nghĩa cùng mức rủi ro, vì rủi ro còn bị chi phối bởi địa hình vi mô, kết cấu nhà và tình trạng nạn nhân. Việc không tích hợp "độ sâu ngập" (từ ảnh) và "mức hoảng loạn/khẩn cấp" (từ văn bản) vào trọng số cạnh khiến đồ thị không phân biệt được nhóm kẹt trên mái nhà với nhóm an toàn ở chung cư tầng cao dù cùng tọa độ.

**Khe hở 2 — Điểm mù về tổn thương nhân khẩu học (Vulnerability Blind Spot).** Các khung logistics nhân đạo thường giả định "nhu cầu đồng nhất", chỉ tối thiểu hóa quãng đường/thời gian. Nhưng thảm họa tác động bất bình đẳng: người già, trẻ em, phụ nữ mang thai, người khuyết tật suy giảm thể trạng nhanh hơn. Việc không **khuếch đại** ưu tiên cho các sự kiện chứa đối tượng yếu thế là thiếu sót nghiêm trọng về đạo đức cứu hộ (equity).

**Khe hở 3 — Phân cụm tĩnh, thiếu ưu tiên cấp cộng đồng.** Nhiều nghiên cứu dừng ở việc "phát hiện nhóm sự kiện" và xem đó là kết quả cuối. Nhưng lực lượng điều phối cần biết cụm nào cần điều động ca nô/trực thăng *trước*. Cơ chế tổng hợp điểm ưu tiên cấp cụm — kết hợp mức ngập tối đa, tổng số người kẹt, tỷ lệ yếu thế và độ khẩn cấp chung — chưa được mô hình hóa toán học triệt để.

---

## 4. Khung giải pháp đề xuất

Khung giải pháp gồm bốn khối nối tiếp: (4.1) trích xuất vector thuộc tính đa chiều tại biên; (4.2) xây dựng đồ thị trọng số không gian – ngữ nghĩa – vật lý; (4.3) phân rã cụm bằng Louvain/Leiden; (4.4) tính điểm ưu tiên cấp cụm.

### 4.1. Vector thuộc tính đa chiều

Mỗi sự kiện cứu hộ $v_i$ được biểu diễn bằng bộ bảy thuộc tính:

$$
v_i = (L_i,\; T_i,\; F_i,\; E_i,\; N_i,\; V_i,\; C_i)
$$

| Ký hiệu | Tên                                    | Miền giá trị              | Nguồn trích xuất                                      |
| :-------- | :-------------------------------------- | :--------------------------- | :------------------------------------------------------- |
| $L_i$   | Vị trí GPS                            | $(\text{lat}, \text{lon})$ | Thiết bị di động / geo-tagging                       |
| $T_i$   | Tem thời gian                          | dấu thời gian              | Metadata báo cáo                                       |
| $F_i$   | Mức độ ngập vật lý                | $[0,1]$                    | Semantic segmentation / pose estimation (MobileNetV3)    |
| $E_i$   | Mức độ khẩn cấp                    | $[0,1]$                    | Phân tích cảm xúc văn bản (DistilBERT / UIT-VSMEC) |
| $N_i$   | Số người mắc kẹt                   | $\mathbb{Z}^{+}$           | Nhập tay / crowd counting                               |
| $V_i$   | Chỉ số tổn thương nhân khẩu học | $\ge 0$                    | Nhánh multi-label ghép chung bộ phân loại văn bản |
| $C_i$   | Độ tin cậy thông tin                | $(0,1]$                    | Heuristic tổng hợp nhẹ                                |

Nhờ Edge AI, thiết bị chỉ gửi một chuỗi JSON chứa $(L_i, T_i, F_i, E_i, N_i, V_i, C_i)$ với kích thước dưới 1 KB (đo được 100–111 byte, xem exp10) thay vì ảnh/video hàng MB.

**Thiết kế khả thi tại biên.** Bốn thuộc tính $L, T, E, N$ và $F$ bám sát cam kết của đề tài (ảnh qua MobileNetV3, văn bản qua DistilBERT đã lượng tử hóa). Hai thuộc tính bổ sung được thiết kế để **không phát sinh mô hình học sâu nặng**:

- $V_i$ được trích xuất bằng một **nhánh phân loại đa nhãn (multi-task head)** ghép chung chính bộ phân loại văn bản dùng cho $E_i$ — nhận diện các cụm từ như "có trẻ sơ sinh", "cụ già kiệt sức", "phụ nữ mang thai". $V_i$ là *tổng trọng số* các đối tượng yếu thế phát hiện được, đóng vai trò hệ số điều chỉnh công bằng.
- $C_i$ dùng heuristic sigmoid nhẹ (Mục 4.1.1) thay vì hạ tầng xác thực người dùng phức tạp.

Các phiên bản đầy đủ hơn (crowd counting/pose estimation chuyên biệt cho $N_i$, mô hình tin cậy học từ lịch sử người dùng cho $C_i$) được định vị rõ ràng là **hướng mở rộng tương lai**, không phải ràng buộc bắt buộc của prototype 6 tháng.

**Định nghĩa vận hành của $V_i$.** Trong các thực nghiệm, $V_i$ được gán một trọng số rời rạc theo nhóm đối tượng yếu thế mà nhánh phân loại phát hiện, rồi cộng lại trên mỗi báo cáo:

| Nhóm phát hiện                         | Trọng số $V$ |
| :---------------------------------------- | :-------------: |
| Không có đối tượng yếu thế       |       0       |
| Người già / trẻ em                    |       1       |
| Phụ nữ mang thai / người khuyết tật |      1,5      |
| Trẻ sơ sinh / người bệnh nặng     |       2       |

Cần nhấn mạnh: các thực nghiệm **giả định $V_i$ đã cho** (kiểm tra *cơ chế* hàm ưu tiên, không phải năng lực *trích xuất* $V_i$ từ văn bản); độ chính xác của bước trích xuất $V_i$ là một vấn đề NLP tách biệt, để dành cho kiểm chứng trên dữ liệu thật.

#### 4.1.1. Công thức độ tin cậy $C_i$

$$
C_i = \sigma\!\big(b_0 + b_1 \cdot \mathbb{1}[\text{có ảnh}] + b_2 \cdot \log(1 + n_i^{\text{corrob}})\big)
$$

- $\sigma(x) = 1/(1+e^{-x})$ là hàm **sigmoid**, ép $C_i$ về $(0,1)$ để luôn là hệ số tin cậy hợp lệ.
- $\mathbb{1}[\text{có ảnh}]$ là hàm chỉ thị: bằng 1 nếu báo cáo kèm ảnh/video đã được mô hình thị giác xác thực — bằng chứng đa phương thức làm tăng tin cậy.
- $n_i^{\text{corrob}}$ là số báo cáo độc lập lân cận củng cố báo cáo $i$, đếm trong **bán kính củng cố $r_{\text{corrob}}=400$ m** và **cửa sổ thời gian $\Delta t_{\text{corrob}}=60$ phút** (giữ tách biệt có chủ đích với các hằng số phân cụm $\sigma_{geo}, \tau_{temp}$ để tránh ghép chéo tham số).
- Nén logarit $\log(1+n_i^{\text{corrob}})$ khiến báo cáo thứ 2–3 tăng tin cậy mạnh nhưng báo cáo thứ 50 gần như không thêm gì — tránh spam cùng vị trí thổi phồng độ tin cậy.
- $b_0, b_1, b_2$ là hệ số hiệu chỉnh (bias và trọng số), đặt bởi chuyên gia hoặc học từ dữ liệu. Trong thực nghiệm dùng $b_0=-0{,}2$, $b_1=1{,}4$, $b_2=0{,}9$.
- Vì "tính độc lập" của báo cáo củng cố chỉ được xấp xỉ qua gần kề không-thời gian (không có hạ tầng tài khoản định danh), heuristic bền với spam đơn lẻ nhưng dễ bị tấn công phối hợp — ta phân tích lỗ hổng này ở phần đối kháng của Thí nghiệm 8 (Mục 5.9).

### 4.2. Đồ thị trọng số không gian – ngữ nghĩa – vật lý

Đây là công thức **được sửa lỗi thiết kế quan trọng nhất** so với bản gốc.

**Dạng cộng (thiết kế ngây thơ, có lỗi):**

$$
w_{ij} = \alpha \mathcal{S}_{geo} + \beta \mathcal{S}_{temp} + \gamma \mathcal{S}_{context}
$$

Vấn đề: các số hạng cộng ngang hàng. Hai sự kiện cách nhau **50 km** ($\mathcal{S}_{geo}\approx 0$) nhưng cùng mô tả "ngập lút mái nhà" ($\mathcal{S}_{context}\approx 1$) vẫn nhận $w_{ij}\approx\gamma$ đáng kể. Thuật toán sẽ gom hai điểm cách xa vào cùng một "khu vực tác chiến" — vô nghĩa với ca nô có bán kính hoạt động hữu hạn.

**Dạng nhân/gating (đề xuất):** $\mathcal{S}_{geo}$ nằm **ngoài** làm thừa số, đóng vai trò **cổng chặn (gate)**:

$$
w_{ij} = \mathcal{S}_{geo}(L_i, L_j) \cdot \Big( \beta \cdot \mathcal{S}_{temp}(T_i, T_j) + \gamma \cdot \mathcal{S}_{context}(v_i, v_j) \Big)
$$

Khi khoảng cách lớn $\Rightarrow \mathcal{S}_{geo}\to 0 \Rightarrow w_{ij}\to 0$ bất kể ngữ cảnh giống nhau đến đâu. Đây là ý nghĩa "địa lý chi phối cấu trúc cụm". Các thành phần:

**(a) Tương đồng không gian — nhân Gaussian:**

$$
\mathcal{S}_{geo} = \exp\!\left( - \frac{\text{dist}(L_i, L_j)^2}{2\sigma_{geo}^2} \right)
$$

$\text{dist}(\cdot)$ là khoảng cách **Haversine** (mét). $\sigma_{geo}$ là bán kính đặc trưng, đặt xấp xỉ tầm hoạt động của một ca nô (vài trăm mét đến 1–2 km). Bình phương khoảng cách khiến hàm suy giảm rất nhanh, phạt mạnh liên kết xa: khi $\text{dist}=\sigma_{geo}$ còn $\approx 0{,}61$; khi $\text{dist}=3\sigma_{geo}$ gần bằng 0.

**(b) Tương đồng thời gian — suy giảm mũ:**

$$
\mathcal{S}_{temp} = \exp\!\left( - \frac{|T_i - T_j|}{\tau_{temp}} \right)
$$

$\tau_{temp}$ là hằng số thời gian (ví dụ 30–60 phút). Dùng bậc nhất (không bình phương) vì diễn biến lũ có quán tính kéo dài, không cần phạt gắt như không gian.

**(c) Tương đồng ngữ cảnh — định nghĩa tường minh** (bản gốc chỉ mô tả bằng lời):

$$
\mathcal{S}_{context} = \exp\!\left( - \frac{|F_i - F_j|}{\tau_F} - \frac{|E_i - E_j|}{\tau_E} \right)
$$

Đo tương đồng tình trạng vật lý qua chênh lệch mức ngập $\Delta F$ và mức khẩn cấp $\Delta E$. Hai báo cáo giống nhau $\Rightarrow \mathcal{S}_{context}\to 1$; khác biệt lớn (một người an toàn tầng 3, một người bám mái nhà) $\Rightarrow \mathcal{S}_{context}$ co lại. Vì $\exp(-a-b)=\exp(-a)\exp(-b)$, hai điều kiện (giống về ngập VÀ giống về khẩn cấp) phải đồng thời thỏa thì $\mathcal{S}_{context}$ mới cao. Hai hằng số suy giảm $\tau_F, \tau_E$ điều khiển độ "khoan dung" khi so khớp: $\tau$ nhỏ phạt gắt mọi chênh lệch (chỉ báo cáo gần như trùng khớp mới coi là cùng ngữ cảnh), $\tau$ lớn nới lỏng. Ta đặt $\tau_E > \tau_F$ (mặc định $0{,}35$ vs $0{,}25$) vì mức khẩn cấp $E$ trích từ cảm xúc văn bản vốn nhiễu hơn mức ngập $F$ trích từ thị giác, nên cần khoan dung hơn khi so khớp. Thí nghiệm 2 (Mục 5.3) cho thấy phân cụm gần như bất biến với $\tau_F, \tau_E$, nên đây là tham số đặt theo miền chứ không phải nút hiệu chỉnh nhạy.

**(d) Tham số và làm thưa đồ thị.** $\beta, \gamma$ cân bằng thời gian và ngữ cảnh; $\alpha$ của dạng cộng bị loại vì $\mathcal{S}_{geo}$ nay là thừa số điều biến toàn cục. Vì $\mathcal{S}_{geo}$ suy giảm nhanh, hầu hết cạnh xa có trọng số không đáng kể; ta **làm thưa đồ thị** bằng (i) **ngưỡng $\epsilon$** — giữ cạnh khi $w_{ij}>\theta$, hoặc (ii) **k-NN graph** — mỗi đỉnh nối $k$ láng giềng trọng số cao nhất. Điều này giảm chi phí tính toán và loại liên kết giả giữa các vùng cách biệt, vì thuật toán Modularity hoạt động kém trên đồ thị dày đặc gần-hoàn-chỉnh.

### 4.3. Phân cụm bằng Louvain (khuyến nghị Leiden)

Mục tiêu là phân hoạch tập đỉnh thành các cụm không giao nhau $\{C_1,\dots,C_k\}$ cực đại hóa Modularity $Q$ (dạng Reichardt–Bornholdt với tham số phân giải):

$$
Q = \frac{1}{2m} \sum_{i,j} \left[ A_{ij} - \lambda \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)
$$

- $A_{ij}=w_{ij}$ là trọng số cạnh; $k_i=\sum_j A_{ij}$ là bậc trọng số của đỉnh $i$; $m=\tfrac12\sum_{i,j}A_{ij}$ là tổng trọng số đồ thị.
- $\delta(c_i,c_j)$ là **Kronecker delta**: bằng 1 nếu $i,j$ cùng cụm. $\tfrac{k_i k_j}{2m}$ là trọng số cạnh kỳ vọng theo mô hình ngẫu nhiên (null model).
- $\lambda$ là **tham số độ phân giải**: $\lambda=1$ là Modularity chuẩn; $\lambda>1$ chia nhỏ hơn (phân rã một phường ngập diện rộng thành các khu phố cụ thể); $\lambda<1$ khuyến khích cụm lớn.

**Vì sao chọn Louvain?** (1) Tự động tìm số cụm — không cần biết trước như K-Means; (2) khử nhiễu cấu trúc — báo cáo giả thiếu cạnh mạnh bị đẩy thành cụm đơn lẻ; (3) độ phức tạp $\mathcal{O}(N\log N)$, chạy thời gian thực; (4) khả thi với sinh viên qua `python-louvain`/`networkx`/`igraph`.

**Khuyến nghị Leiden.** Louvain đôi khi tạo **cộng đồng đứt gãy nội bộ** — các đỉnh cùng cụm nhưng không thực sự liên thông — khiến trọng tâm cụm sai lệch khi điều ca nô. Thuật toán **Leiden** bổ sung bước bảo đảm cộng đồng liên thông tốt, giữ nguyên hàm mục tiêu Modularity, nên dùng thay thế khi độ chính xác không gian là sống còn.

### 4.4. Ưu tiên cấp cụm $\mathcal{P}(C_k)$

Đây là công thức **được sửa ba lỗi toán học** so với bản gốc: (a) sai lệch thang đo, (b) $\mathcal{V}$ cộng thay vì nhân, (c) $\tanh$ bão hòa quá sớm.

$$
\mathcal{P}(C_k) = \mathcal{V}_{agg}(C_k) \cdot \Big( \omega_1 \widetilde{\mathcal{E}}_{agg}(C_k) + \omega_2 \widetilde{\mathcal{F}}_{max}(C_k) + \omega_3 \widetilde{\mathcal{N}}(C_k) \Big)
$$

**Lỗi (a) — sai lệch thang đo và chuẩn hóa.** $\mathcal{E}_{agg},\mathcal{F}_{max}\in[0,1]$ nhưng $\mathcal{N}_{total}=\sum N_i$ **không bị chặn** (có thể hàng trăm). Cộng trực tiếp thì dân số áp đảo, biến $\mathcal{P}$ gần như chỉ còn phản ánh số người. Cách sửa: chuẩn hóa mọi thành phần về $[0,1]$ *trước khi* nhân trọng số (ký hiệu $\widetilde{(\cdot)}$). Với dân số (phân phối lệch phải), nén log rồi min-max:

$$
\widetilde{\mathcal{N}}(C_k) = \frac{\log(1 + \mathcal{N}_{total}(C_k))}{\log(1 + N_{\max})}
$$

với $N_{\max}$ là mốc dân số tham chiếu. Ta phân biệt hai chế độ: (i) **mốc động** — tổng dân số của cụm lớn nhất trong cửa sổ hiện tại, cho *xếp hạng tương đối tức thời* giữa các cụm đồng thời; (ii) **mốc cố định** — một hằng số dân số tham chiếu theo địa bàn, cần thiết nếu muốn so sánh điểm $\mathcal{P}$ *across-time* (điểm của cùng một cụm không đổi khi các cụm khác xuất hiện/biến mất). Chế độ động tiện cho điều phối tức thời nhưng có tính **không dừng (non-stationary)**: cùng một cụm nhận $\mathcal{P}$ khác nhau tùy bối cảnh — cần nêu rõ khi diễn giải.

**Các thành phần lõi rủi ro** (mọi thành phần đều gate độ tin cậy $C_i$ để nhất quán chống tin giả):

- **Khẩn cấp trung bình có trọng số tin cậy:** $\mathcal{E}_{agg}(C_k) = \frac{1}{|C_k|}\sum_{v_i\in C_k} E_i\cdot C_i$. Báo cáo đáng tin đóng góp nhiều hơn.
- **Ngập tối đa có trọng số tin cậy:**

$$
\mathcal{F}_{max}(C_k) = \max_{v_i\in C_k} \big(F_i \cdot C_i\big)
$$

  Dùng $\max$ (không phải trung bình) theo **nguyên lý bình thông nhau** — điểm ngập sâu nhất quyết định rủi ro sinh tồn cao nhất của cả quần thể; trung bình sẽ làm loãng cảhnh báo. Quan trọng: nhân $C_i$ **bên trong** $\max$ để một báo cáo giả khai $F=1{,}0$ với $C_i$ thấp không tự chiếm trọn $\mathcal{F}_{max}$ — đây là lỗ hổng của bản chỉ dùng $\max F_i$ thuần (khi đó $\mathcal{E}$ và $\mathcal{N}$ đã gate $C_i$ nhưng $\mathcal{F}$ thì không, thiếu nhất quán).

- **Quy mô sinh mạng có trọng số tin cậy:** $\mathcal{N}_{total}(C_k) = \sum_{v_i\in C_k} N_i\cdot C_i$, sau đó nén log và chuẩn hóa. Nhân $C_i$ để báo cáo giả thổi phồng "500 người" với $C_i$ thấp không tự đẩy cụm lên đầu.

**Lỗi (b) và (c) — hệ số khuếch đại tổn thương:**

$$
\mathcal{V}_{agg}(C_k) = 1 + \tanh\!\left( \frac{1}{s} \sum_{v_i \in C_k} V_i \right), \qquad \mathcal{V}_{agg}\in(1,2)
$$

- **Lỗi (b) — cộng vs nhân:** bản gốc đặt $\mathcal{V}$ như số hạng cộng $\omega_4\mathcal{V}_{agg}$. Một số hạng bị chặn trong $[1,2]$ chỉ tạo offset gần hằng số, **không khuếch đại gì**. Cách sửa: tách $\mathcal{V}_{agg}$ ra ngoài làm **thừa số nhân**. Cụm không có đối tượng yếu thế: $\mathcal{V}_{agg}\approx 1$ (giữ nguyên lõi); cụm nhiều đối tượng yếu thế: $\mathcal{V}_{agg}\to 2$ (nhân đôi điểm) — đúng nghĩa "amplify equity".
- **Lỗi (c) — bão hòa sớm:** nếu dùng $\tanh(\sum V_i)$ trực tiếp, chỉ 2–3 đối tượng yếu thế đã đưa $\tanh$ sát 1, khiến cụm 1 người và cụm 50 người yếu thế nhận điểm gần như nhau — mất khả năng phân biệt. Cách sửa: thêm **hệ số tỉ lệ** $s$ (ví dụ $s=10$) chia trong đối số $\tanh$, giãn vùng tuyến tính. $\tanh$ vẫn giữ vai trò chặn trên tránh điểm bùng nổ vô cực. (Lựa chọn tương đương: $1+\log(1+\sum V_i)$ kèm chuẩn hóa.)

**Trần khuếch đại tổng quát $\mu$.** Chặn trên "nhân đôi" ($\mathcal{V}_{agg}\in(1,2)$) là một *lựa chọn chính sách* chứ không phải hằng số bất biến. Ta tổng quát hóa thành

$$
\mathcal{V}_{agg}(C_k) = 1 + (\mu - 1)\tanh\!\left( \frac{1}{s} \sum_{v_i \in C_k} V_i \right), \qquad \mu\in[1,2], \quad \mathcal{V}_{agg}\in(1,\mu)
$$

trong đó $\mu$ là **trần khuếch đại** do ban chỉ huy đặt: $\mu=1$ tắt hoàn toàn ưu tiên tổn thương (quay về thuần rủi ro), $\mu=2$ cho phép nhân đôi tối đa. Việc phơi bày $\mu$ tường minh giúp yếu tố công bằng trở thành một *núm điều khiển chính sách có thể kiểm toán* thay vì một hằng số ẩn. Mọi số liệu báo cáo trong bài dùng $\mu=2$.

**Trọng số và miền giá trị.** $\omega_1,\omega_2,\omega_3$ với ràng buộc $\sum\omega=1$, do ban chỉ huy đặt qua **Ma trận Quyết định** để chuyển trạng thái chiến thuật (ưu tiên số đông vs ưu tiên ngập sâu). Vì lõi đã chuẩn hóa $[0,1]$ và $\sum\omega=1$, lõi rủi ro $\in[0,1]$; nhân $\mathcal{V}_{agg}\in(1,2)$ cho $\mathcal{P}(C_k)\in(0,2]$ — chặn gọn, dễ xếp hạng.

Xếp hạng $\mathcal{P}(C_k)$ giảm dần cho ngay danh sách ưu tiên hành động; kết hợp tọa độ trọng tâm cụm, đây là đầu vào lý tưởng cho các thuật toán tối ưu định tuyến (A\* cost-aware, multi-commodity routing).

**Ghi chú về việc dùng lại $F, E$ ở hai khâu.** Hai thuộc tính $F$ (mức ngập) và $E$ (mức khẩn cấp) xuất hiện cả ở khâu gom cụm (qua $\mathcal{S}_{context}$) lẫn khâu ưu tiên (qua $\mathcal{F}_{max}, \mathcal{E}_{agg}$). Đây **không phải double-counting sai** vì hai khâu đo hai đại lượng khác bản chất: $\mathcal{S}_{context}$ đo *độ tương đồng* giữa cặp sự kiện (để quyết định chúng có cùng một tình huống hay không), còn $\mathcal{F}_{max}/\mathcal{E}_{agg}$ đo *độ nghiêm trọng tuyệt đối* của cụm (để xếp hạng). Tuy vậy cần thừa nhận một hệ quả: cụm được gom vì $F$ tương đồng thì $\mathcal{F}_{max}$ của nó gần như chắc chắn cao — nên $\mathcal{F}_{max}$ nên hiểu là "mức ngập đặc trưng của một quần thể đã đồng nhất" chứ không phải một tín hiệu độc lập hoàn toàn với tiêu chí gom cụm. Chúng tôi **định lượng** mức vòng tròn này ở Thí nghiệm 6 (Mục 5.8): loại bỏ $\mathcal{S}_{context}$ khỏi đồ thị làm *đổi kết quả phân cụm* (ARI giảm) nhưng gần như *không đổi thứ hạng ưu tiên* (Kendall's τ = 0,9829), cho thấy $\mathcal{S}_{context}$ chủ yếu hỗ trợ *gom nhóm* chứ không âm thầm định đoạt *thứ hạng*.

#### 4.4.1. Bảng tổng kết các thay đổi so với bản gốc (V1 → V2)

| Vị trí                    | Công thức gốc (V1)                         | Công thức sửa (V2)                                             | Lý do                                                          |
| :-------------------------- | :-------------------------------------------- | :---------------------------------------------------------------- | :-------------------------------------------------------------- |
| 4.1$V_i$                  | "NLP sâu" riêng biệt                       | Nhánh multi-label ghép chung DistilBERT                         | Khả thi tại biên, không thêm mô hình nặng               |
| 4.1$C_i$                  | Lịch sử người dùng / cảm biến vật lý | Heuristic sigmoid nhẹ                                            | Hạ tầng gốc không tồn tại trong đề tài 6 tháng        |
| 4.2$w_{ij}$               | Cộng:$\alpha S_g + \beta S_t + \gamma S_c$ | Nhân/gating:$S_g\cdot(\beta S_t+\gamma S_c)$                   | Địa lý phải là cổng chặn để cụm gắn kết không gian |
| 4.2$S_{temp},S_{context}$ | Chỉ mô tả bằng lời                       | Công thức mũ tường minh                                      | Cần định nghĩa rõ để cài đặt được                  |
| 4.2 sparsification          | (không có)                                  | Thêm ngưỡng$\epsilon$ / k-NN                                 | Louvain hoạt động kém trên đồ thị dày đặc            |
| 4.3 Leiden                  | Nhắc thoáng qua                             | Nhấn mạnh chống đứt gãy cụm                                | Trọng tâm cụm sai làm điều ca nô sai                     |
| 4.4$\mathcal{P}$          | Cộng 4 hạng tử chưa chuẩn hóa           | Chuẩn hóa$[0,1]$ + tách $\mathcal{V}_{agg}$ làm thừa số | Sửa sai lệch thang đo và ý nghĩa "khuếch đại"          |
| 4.4$\mathcal{N}$          | $\sum N_i$                                  | $\sum N_i\cdot C_i$ rồi nén log                               | Chống báo giả thổi phồng số người                       |
| 4.4$\mathcal{V}_{agg}$    | $\tanh(\sum V_i)$                           | $\tanh(\tfrac1s\sum V_i)$                                       | Chống bão hòa sớm, giữ khả năng phân biệt              |

---

## 5. Thực nghiệm và kết quả

### 5.1. Thiết lập thực nghiệm

**Bộ dữ liệu.** Do chưa có bộ dữ liệu thực đã gán nhãn ground-truth cho cụm cứu hộ, chúng tôi sinh một bộ dữ liệu **mô phỏng tất định** (seed = 42) đặc thù cho Miền Trung Việt Nam (Huế – Quảng Trị – Quảng Nam – Đà Nẵng; 15,7–17,1°N, 107,0–108,6°E), gồm **285 sự kiện**:

- **240 sự kiện lõi** phân bố quanh **6 "ốc đảo" ngập** (mỗi cụm ~40 điểm, có nhãn `gt_cluster` để đo ARI/NMI).
- **20 sự kiện nhiễu** rải rác, khoảng 40% là tin giả.
- **25 sự kiện kịch bản minh họa** (S1–S4), mỗi kịch bản stress-test một quyết định thiết kế:
  - **S1:** hai điểm ngập nóc cách nhau ~103 km (kiểm tra gating tách cụm).
  - **S2:** cụm nhiều đối tượng yếu thế (kiểm tra $\mathcal{V}_{agg}$ khuếch đại).
  - **S3:** tin giả cô lập thổi phồng 200 người (kiểm tra cổng $C_i$).
  - **S4:** cụm đông-ngập nhẹ vs ít-ngập nóc (kiểm tra $\mathcal{F}_{max}$).

**Tham số mặc định:** $\sigma_{geo}=700$ m; $\tau_{temp}=45$ phút; $\tau_F=0{,}25$; $\tau_E=0{,}35$; $\beta=\gamma=0{,}5$; ngưỡng cạnh $\theta=0{,}05$; k-NN $k=12$; $\lambda=1{,}0$; $s=10$; $\omega=(0{,}34;\,0{,}33;\,0{,}33)$; heuristic $C_i$ với $(b_0,b_1,b_2)=(-0{,}2;\,1{,}4;\,0{,}9)$.

**Độ đo:** ARI (Adjusted Rand Index) và NMI (Normalized Mutual Information) so với ground-truth; **đường kính địa lý cụm** (km) — khoảng cách lớn nhất giữa hai điểm trong cùng cụm, đo tính gắn kết không gian; Modularity $Q$.

Toàn bộ pipeline hiện thực bằng Python (`numpy`, `networkx`, `python-louvain`, `igraph`, `leidenalg`, `scikit-learn`, `scipy`); mã và số liệu thô nằm trong `demo/` (chín thí nghiệm `exp1`–`exp9` trong `demo/experiments/`, kết quả JSON trong `demo/results/tables/`).

### 5.2. Thí nghiệm 1 — Kiểm chứng sáu quyết định thiết kế

**(1A) Gating vs Cộng.** Cả hai dạng cho **cùng ARI = 0,892 và NMI = 0,927**, nhưng khác biệt căn bản về gắn kết không gian:

| Dạng            |  ARI  | Đường kính TB (km) | Đường kính max (km) | Số cụm |
| :--------------- | :---: | :--------------------: | :---------------------: | :------: |
| Cộng (additive) | 0,892 |    **100,07**    |         213,95         |    6    |
| Nhân/Gating     | 0,892 |     **0,30**     |          1,42          |    27    |

Dạng cộng tạo ra các cụm có đường kính trung bình **100 km** — vô nghĩa cho điều phối ca nô. Dạng gating kéo đường kính xuống **0,30 km**, đúng tầm hoạt động thực tế. Điểm mấu chốt: gating **không** hy sinh độ chính xác phân cụm mà chỉ sửa hình học không gian của cụm. Sự trùng khớp ARI được giải thích minh bạch: hai dạng cho **cùng một phân hoạch trên 264 điểm có nhãn ground-truth** (thành 6 nhóm địa lý); khác biệt 6 vs 27 cụm hoàn toàn nằm ở 21 điểm nhiễu (`gt_cluster = -1`) mà cổng gating tách thành các cụm đơn lẻ còn dạng cộng gộp vào các cụm lớn — và các điểm nhiễu này bị mặt nạ loại bỏ *trước khi* tính ARI/NMI. Vậy tương phản "6 vs 27 cụm" chứng minh lợi ích của gating về **độ gắn kết địa lý và cô lập nhiễu**, không phải về ARI (vốn giống hệt theo cấu trúc bài toán).

**(1B) Chuẩn hóa thang đo.** Không chuẩn hóa, cụm đứng đầu bảng xếp hạng là cụm có tổng dân số lớn nhất (216 người, lõi thô 71,65) — dân số áp đảo mọi yếu tố khác. Sau chuẩn hóa $[0,1]$, cụm đứng đầu là cụm có lõi rủi ro cân bằng (0,82) với $\mathcal{P}=1,52$ — phản ánh đúng tổ hợp khẩn cấp + ngập + dân số.

**(1C) $\mathcal{V}$ nhân vs cộng.** Với cụm kịch bản S2 (nhiều đối tượng yếu thế, $\mathcal{V}_{agg}=1,97$), cách **cộng** cho $\mathcal{P}_{add}=1,66$ còn cách **nhân** cho $\mathcal{P}_{mult}=1,36$. Quan trọng hơn là *hành vi vi phân*: với các cụm không có đối tượng yếu thế ($\mathcal{V}_{agg}=1$), cả hai cách cho kết quả giống hệt nhau; nhưng khi $\mathcal{V}_{agg}$ tăng, cách nhân **co giãn theo lõi rủi ro** (khuếch đại thực sự) trong khi cách cộng chỉ thêm một offset gần hằng số bất kể lõi mạnh hay yếu.

**(1D) Chống bão hòa $\tanh$.** Bảng dưới cho thấy $\tanh(\sum V_i)$ không chia tỉ lệ đã bão hòa ($\approx 2{,}0$) ngay từ $\sum V_i = 3$, mất hoàn toàn khả năng phân biệt; trong khi $\tanh(\sum V_i/10)$ vẫn tăng đơn điệu tới $\sum V_i = 50$:

| $\sum V_i$ | $\tanh(\sum V_i)$ (không chia) | $\tanh(\sum V_i/10)$ |
| :----------: | :-------------------------------: | :--------------------: |
|      1      |               1,76               |          1,10          |
|      3      |               2,00               |          1,29          |
|      10      |               2,00               |          1,76          |
|      30      |               2,00               |          2,00          |
|      50      |               2,00               |          2,00          |

**(1E) Cổng tin cậy $C_i$ cho quy mô dân số.** Với kịch bản S3 (tin giả thổi phồng 200 người, $C_i=0,45$): quy mô dân số cụm không gate là 200 người, sau khi nhân $C_i$ giảm còn **90 người — giảm 55%**. Cổng tin cậy ngăn được một báo cáo giả tự đẩy cụm lên đầu danh sách ưu tiên.

**(1F) Cổng tin cậy $C_i$ cho mức ngập tối đa.** Cùng báo cáo giả S3 khai mức ngập rất cao ($F=0,99$) nhưng $C_i=0,45$. Nếu dùng $\max F_i$ thuần, nó chiếm trọn $\mathcal{F}_{max}=0,99$ của cụm — một tín hiệu ngập cực đoan hoàn toàn do tin giả tạo ra. Với $\max(F_i\cdot C_i)$, giá trị bị hạ xuống **0,45**, khôi phục tính nhất quán: mọi thành phần lõi rủi ro ($\mathcal{E}, \mathcal{F}, \mathcal{N}$) đều được gate độ tin cậy, không còn lỗ hổng để một báo cáo đơn lẻ không đáng tin thao túng thứ hạng.

### 5.3. Thí nghiệm 2 — Phân tích độ nhạy

- **Độ phân giải $\lambda$:** ARI ổn định ở 0,892 với $\lambda\le 1{,}5$; tăng lên $\lambda=2{,}0$ (ARI 0,83) và $\lambda=3{,}0$ (ARI 0,67) thì cụm bị chia vụn. Khoảng an toàn khuyến nghị: $\lambda\in[0{,}5;\,1{,}5]$.
- **Bán kính $\sigma_{geo}$:** điều khiển trực tiếp đánh đổi bán kính/số cụm. ARI giữ 0,892 trên dải rộng, nhưng đường kính trung bình tăng từ 0,28 km ($\sigma_{geo}=200$ m) lên 1,59 km ($\sigma_{geo}=4000$ m). Modularity cũng tăng nhẹ và bão hòa (~0,83). Cần đặt $\sigma_{geo}$ theo tầm hoạt động thực tế của đơn vị cứu hộ.
- **Hệ số $s$:** độ trải (spread) của $\mathcal{V}_{agg}$ giảm khi $s$ tăng: $s=1$ cho spread đầy đủ ($1{,}0\to 2{,}0$), $s=20$ chỉ còn $1{,}0\to 1{,}78$. $s=10$ cho vùng phân biệt tốt tới $\sum V_i\approx 50$.

**Trả lời lo ngại "quá nhiều tham số tự do".** Ta mở rộng quét sang các tham số ngữ cảnh và cân bằng. Hai độ nhạy ngữ cảnh $\tau_F, \tau_E$ **trơ (inert)** với độ chính xác phân cụm: ARI giữ nguyên 0,892 trên toàn lưới $\tau_F, \tau_E\in[0{,}15;\,0{,}5]$, vì cổng địa lý chi phối cấu trúc cụm bất kể độ tương đồng ngữ cảnh suy giảm gắt hay thoải. Cân bằng $\beta/\gamma$ chỉ ảnh hưởng ở cực biên: ARI giữ 0,892 khi $\beta\le 0{,}5$ (còn đủ ngữ cảnh) nhưng tụt xuống 0,7855 một khi $\beta\ge 0{,}9$ bỏ đói số hạng ngữ cảnh — nhất quán với ablation ở Mục 5.7 (Thí nghiệm 6). Điều này cho thấy phần lớn tham số hoặc **đặt theo miền** (nhóm "domain" trong Bảng 4.4.1) hoặc **trơ có kiểm chứng** trên bộ dữ liệu này, chỉ còn $\lambda, \sigma_{geo}, \beta/\gamma$ là các núm tinh chỉnh thực sự ảnh hưởng độ chính xác — cả ba đều có khoảng an toàn đã báo cáo ở trên.

### 5.4. Thí nghiệm 3 — Louvain vs Leiden

Trên **10 seed khác nhau**, cả Louvain và Leiden đều cho **0 cộng đồng đứt gãy**, cùng ARI 0,892 và Modularity 0,8311. Đây là **phát hiện trung thực đáng chú ý**: chính cơ chế gating (Mục 4.2) đã tạo ra các đồ thị con gắn kết không gian, loại bỏ trước rủi ro cộng đồng đứt gãy — nên trong bối cảnh này Louvain đã đủ tốt. Leiden vẫn được khuyến nghị như một "bảo hiểm miễn phí" (đảm bảo lý thuyết về liên thông) mà không phải đánh đổi chất lượng.

### 5.5. Thí nghiệm 4 — So sánh với baseline

Bảng dưới mở rộng so sánh với **ba baseline công bằng** chạy trên **cùng đồ thị gating** (Spectral, HDBSCAN, Agglomerative) bên cạnh các baseline hình học thuần túy (K-Means, DBSCAN trên tọa độ thô).

| Phương pháp                              | Số cụm |       ARI       |       NMI       | Đường kính TB (km) | Cùng đồ thị? | Cần biết trước$K$? |
| :------------------------------------------ | :------: | :-------------: | :-------------: | :--------------------: | :--------------: | :----------------------: |
| **Louvain (đồ thị gating)**        |    27    | **0,892** | **0,927** |     **0,30**     |        ✓        |          Không          |
| **Leiden (đồ thị gating)**         |    27    | **0,892** | **0,927** |     **0,30**     |        ✓        |          Không          |
| Spectral (affinity gating,$K=27$)         |    27    |      0,339      |      0,727      |         14,11         |        ✓        |           Có           |
| HDBSCAN (dist=$1-w$ gating)               |    11    |      0,890      |      0,922      |         25,08         |        ✓        |          Không          |
| Agglomerative (dist=$1-w$, $K=27$)      |    27    |      0,892      |      0,927      |          0,30          |        ✓        |           Có           |
| K-Means ($K=12$, đúng $K$, tọa độ) |    12    |      0,688      |      0,834      |         49,21         |        ✗        |           Có           |
| K-Means ($K=3$, sai $K$, tọa độ)     |    3    |      0,433      |      0,630      |         102,04         |        ✗        |           Có           |
| DBSCAN (eps=0,3, tọa độ)                 |    15    |      0,644      |      0,783      |         15,12         |        ✗        |          Không          |
| DBSCAN (eps=0,6, tọa độ)                 |    7    |      0,730      |      0,873      |         32,27         |        ✗        |          Không          |

**Phân tích baseline công bằng.** Khi chạy trên cùng ma trận affinity/khoảng cách, Louvain/Leiden vẫn vượt trội: (i) **Spectral Clustering** cho ARI chỉ 0,339 — đồ thị gating thưa và không liên thông đầy đủ gây khó cho phân tách phổ; (ii) **HDBSCAN** đạt ARI 0,890 (gần bằng Louvain) nhưng tìm được ít cụm hơn (11 vs 27) và đường kính trung bình 25 km — gộp nhiều ốc đảo khác nhau vào cùng cụm; (iii) **Agglomerative** (average linkage) khớp hoàn hảo với Louvain về ARI và NMI, nhưng yêu cầu biết trước $K$ — điều bất khả thi trong thảm họa. Kết quả xác nhận rằng ưu thế không chỉ đến từ đồ thị gating (vì HDBSCAN cũng dùng cùng đồ thị) mà từ sự kết hợp giữa đồ thị gating và cơ chế tối ưu Modularity (tự tìm K, gắn kết không gian).

### 5.6. Thí nghiệm 5 — Độ ổn định xếp hạng (Kendall's τ)

Phản biện tiềm năng: ban chỉ huy đặt $\omega$ thủ công — nếu thứ hạng $\mathcal{P}(C_k)$ quá nhạy với $\omega$, danh sách ưu tiên trở nên tùy tiện. Chúng tôi nhiễu loạn $\omega$ quanh giá trị mặc định $(0{,}34;\,0{,}33;\,0{,}33)$, chuẩn hóa lại về $\sum\omega=1$, rồi đo Kendall's τ giữa thứ hạng mới và thứ hạng gốc (200 thử nghiệm Monte-Carlo mỗi mức).

| Mức dao động$\omega$ | τ trung bình | τ tối thiểu | Top-3 giữ nguyên (%) |
| :-----------------------: | :-------------: | :------------: | :--------------------: |
|          ±0,05          | **0,994** |     0,977     |    **100,0**    |
|          ±0,10          |      0,986      |     0,937     |          99,0          |
|          ±0,20          |      0,957      |     0,841     |          76,5          |

Kết quả: ở mức dao động thực tế (±0,05 — ±0,10), Kendall's τ luôn trên **0,93** và tập 3 cụm ưu tiên cao nhất gần như không đổi (99–100%). Ngay cả ở mức cực đoan ±0,20 (thay đổi gần 60% giá trị $\omega$), τ trung bình vẫn đạt 0,957. Điều này chứng minh hàm $\mathcal{P}(C_k)$ cho **xếp hạng ổn định**, giảm thiểu rủi ro "danh sách ưu tiên tùy tiện" khi ban chỉ huy hiệu chỉnh trọng số.

Ngoài nhiễu loạn $\omega$, ta còn kiểm tra **ổn định cấu trúc** khi thay đổi tham số dựng đồ thị $\sigma_{geo}$: với $\sigma_{geo}\in\{400, 550, 700, 900\}$ m, phân hoạch giữ nguyên 27 cụm và thứ hạng khớp hoàn hảo (Kendall's τ = 1,0); chỉ tới $\sigma_{geo}=1200$ m mới gộp còn 26 cụm (τ = 0,9815). Nghĩa là danh sách ưu tiên bền vững cả với dao động của tham số hình học lẫn trọng số chính sách.

### 5.7. Thí nghiệm 6 — Ablation tính vòng tròn của ngữ cảnh

Một phản biện: việc dùng lại $F, E$ ở cả $\mathcal{S}_{context}$ (gom cụm) lẫn $\mathcal{F}_{max}, \mathcal{E}_{agg}$ (xếp hạng) có thể khiến số hạng ngữ cảnh ngấm ngầm chi phối danh sách ưu tiên cuối. Ta kiểm tra bằng cách loại $\mathcal{S}_{context}$ khỏi trọng số cạnh (đặt $\gamma=0$, chỉ còn gating địa lý – thời gian) rồi so cả phân cụm lẫn thứ hạng cảm sinh với mô hình đầy đủ. Bỏ ngữ cảnh **có** làm đổi phân cụm — ARI tụt từ 0,892 xuống 0,7855, NMI từ 0,927 xuống 0,8741, số cụm vỡ từ 27 lên 30 — khẳng định $\mathcal{S}_{context}$ thực sự hỗ trợ việc gom nhóm. Nhưng thứ hạng ưu tiên gần như không đổi: trên 27 cụm khớp theo trọng tâm, Kendall's τ giữa thứ hạng mô hình-đầy-đủ và mô hình-bỏ-ngữ-cảnh đạt **0,9829**, và cả top-5 cụm được giữ nguyên. Sự phân ly này cho thấy $\mathcal{S}_{context}$ chủ yếu cải thiện *ai được gom với ai*, chứ không phải *cụm nào xếp đầu*; thứ hạng được dẫn dắt bởi các số hạng nghiêm-trọng-tuyệt-đối $\mathcal{F}_{max}, \mathcal{E}_{agg}$ đúng như thiết kế — nên việc dùng lại không phải double-counting độc hại.

### 5.8. Thí nghiệm 7 — Trọng số tổn thương có thực sự giúp người yếu thế?

Câu hỏi sâu hơn của Khe hở 2 không phải "chỉ số tổn thương $V_i$ có đổi thứ hạng không" (có, theo thiết kế) mà là nó có tạo ra **kết quả cứu hộ tốt hơn** cho nhóm yếu thế hay không. Ta mô phỏng điều phối rời rạc (discrete-event dispatch): $3$ ca nô ở $30$ km/h với thời gian phục vụ $15$ phút/cụm, phục vụ các cụm theo thứ tự ưu tiên, rồi đo thời gian đến được nạn nhân yếu thế (nhóm $V_i$ cao). So ba chính sách: dạng nhân đầy đủ $\mathcal{P}=\mathcal{V}_{agg}\cdot(\dots)$, dạng cộng $\mathcal{P}=\mathcal{V}_{agg}+(\dots)$, và chính sách mù tổn thương (bỏ $V_i$). Bỏ $V_i$ làm trễ thời gian trung bình đến người yếu thế từ $146{,}5$ lên $163{,}6$ phút — **cải thiện 10,4%** nhờ trọng số tổn thương — và giảm thời gian phản ứng có trọng số tổn hại $8{,}7\%$. Dạng nhân đổi lấy phần công bằng này bằng một chi phí khiêm tốn ở thời gian đến trung bình cho *toàn bộ* nạn nhân ($942{,}9$ so với $719{,}6$ phút của chính sách mù) — một đánh đổi công bằng–hiệu quả tường minh và biện minh được, chứ không chỉ là xáo thứ hạng. Dạng cộng đến người yếu thế nhanh hơn chút ($133{,}3$ phút) nhưng làm yếu liên kết giữa tổn thương và mức nghiêm trọng mà cổng nhân được thiết kế để giữ; ta báo cáo cả hai để đánh đổi minh bạch.

### 5.9. Thí nghiệm 8 — Bộ phát hiện tin cậy và độ bền đối kháng

Ta đánh giá heuristic tin cậy $C_i$ như một bộ phát hiện tin giả và dò trường hợp xấu nhất. Xem $C_i$ thấp là cờ báo giả trên toàn bộ $285$ sự kiện, $C_i$ tách được tin giả tiêm vào khỏi tin thật với **ROC-AUC $0{,}9651$** (trung bình $C_i$ là $0{,}50$ cho tin giả so với $0{,}92$ cho tin thật). Đây là tín hiệu sàng lọc, không phải bảo đảm, và ta cố ý ép nó tới điểm gãy. Một tin giả ngây thơ (cô lập, không ảnh) chỉ đạt $C_i=0{,}45$ và dễ bị hạ trọng số; nhưng kẻ tấn công **thêm ảnh giả** đẩy nó lên $0{,}77$, **dàn dựng corroboration phối hợp** đẩy lên $0{,}74$, và làm **cả hai** đạt $C_i=0{,}92$ — không phân biệt được với trung bình tin thật. Vì "tính độc lập" của corroboration chỉ được xấp xỉ bằng gần kề không gian – thời gian (không có hạ tầng tài khoản định danh), heuristic bền với kẻ spam đơn lẻ nhưng **không** bền với đối thủ phối hợp có nguồn lực. Do đó ta trình bày $C_i$ như một bộ lọc tuyến đầu, phải kết hợp với tin cậy cấp tài khoản hoặc kiểm chứng chéo kênh trước khi có thể dựa vào để chống đối kháng — và nêu rõ giới hạn này thay vì thổi phồng khả năng phát hiện.

### 5.10. Thí nghiệm 9 — Một độ đo phân biệt vượt trên ARI

ARI bão hòa ở đỉnh bảng xếp hạng (Louvain, Leiden, Agglomerative, và cả HDBSCAN đều quanh $0{,}89$–$0{,}892$), có nguy cơ che các khác biệt chất lượng thật. Ta bổ sung bộ ba homogeneity/completeness/V-measure, phân rã chất lượng cụm thành hai trục diễn giải được. Phân rã này phân biệt tốt hơn hẳn ở đúng loại lỗi quan trọng ở đây — **completeness**, tức một sự kiện ground-truth có bị xé lẻ ra nhiều cụm không. Nó phơi bày hai loại lỗi mà ARI làm mờ. Thứ nhất, ở đầu thấp, Spectral Clustering làm vỡ vụn sự kiện: completeness chỉ $0{,}595$ (V-measure $0{,}727$) so với $1{,}0$ của Louvain (V-measure $0{,}927$). Thứ hai, và đáng nói hơn, trong bốn phương pháp dẫn đầu mà ARI gộp thành gần-hòa (Louvain, Leiden, Agglomerative, HDBSCAN — chênh nhau trong $0{,}002$ ARI), completeness vẫn tách được: Louvain/Leiden/Agglomerative đạt hoàn hảo $1{,}0$ trong khi HDBSCAN tụt xuống $0{,}929$ vì gộp các ốc đảo — một khoảng cách completeness $0{,}07$ ở nơi ARI chỉ hiện $0{,}002$. (Độ trải ARI toàn dải $0{,}55$ là thật nhưng dồn hết ở đầu thấp — Spectral $0{,}339$, K-Means $0{,}688$ — nên không xếp hạng nổi nhóm dẫn đầu.) Do đó ta báo cáo V-measure kèm ARI xuyên suốt.

### 5.11. Trực quan hóa

Pipeline sinh một **dashboard bản đồ Leaflet tự chứa** hiển thị các cụm sự kiện trên bản đồ Miền Trung kèm bảng xếp hạng $\mathcal{P}(C_k)$, minh họa trực tiếp đầu ra cho ban điều phối. Bảy hình PNG (`demo/results/figures/`) minh họa từng thí nghiệm: (1) gating vs cộng, (2) bão hòa $\tanh$, (3) cổng $C_i$, (4) quét $\sigma_{geo}$, (5) quét $\lambda$, (6) so sánh baseline, (7) độ ổn định xếp hạng.

---

## 6. Thảo luận

**Ý nghĩa liên ngành.** Khung giải pháp mang lại tác động cộng hưởng trên ba lĩnh vực:

| Lĩnh vực                                | Giá trị mang lại                                                                                                                                                |
| :---------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Hạ tầng viễn thông & Edge**   | Duy trì sự sống còn (resilience) khi mạng sụp đổ; thay vì tải ảnh/video hàng MB, thiết bị chỉ gửi gói metadata JSON nén đo được **100–111 byte** (min/median/max trên toàn bộ 285 sự kiện, gồm định danh, toạ độ, tem thời gian epoch và các trường $L,T,F,E,N,V,C$ + cờ ảnh; xem exp10) — nhỏ hơn ba–bốn bậc độ lớn, đủ luồn qua hạ tầng tắc nghẽn |
| **Khoa học dữ liệu & AI**        | Chuyển bài toán phân loại tĩnh thành khai phá cấu trúc mạng (network topology mining), định lượng rủi ro lan truyền bằng toán học              |
| **Đạo đức cứu hộ & xã hội** | Tích hợp chỉ số tổn thương vào hàm ưu tiên, tái định hình sự công bằng (equity), cứu đúng người đúng thời điểm                         |

**Khả năng chuyển giao.** Các nguyên lý đồ thị trọng số + Louvain có thể chuyển sang lập bản đồ rủi ro hỏa hoạn đô thị, xác định khu vực bùng phát dịch bệnh, hay phân tích đứt gãy chuỗi cung ứng — hướng tới mạng lưới Internet of Emergency Services (IoES).

**Về scope so với thuyết minh.** Thuyết minh đề tài mô tả phạm vi phân cụm khiêm tốn ("phân cụm sự kiện dựa trên vị trí địa lý", "gom nhóm theo không gian và thời gian"). Khung Mục 4 tham vọng hơn (đồ thị trọng số đa chiều + hàm ưu tiên cấp cụm + hai thuộc tính mới $V_i, C_i$). Đây là **tầm nhìn mở rộng cho bài báo**; phần lõi $L, T, F, E, N$ + Louvain bám sát cam kết 6 tháng, còn các thành phần nâng cao được định vị rõ là hướng mở rộng.

## 7. Hạn chế và hướng mở rộng

- **Dữ liệu mô phỏng.** Kết quả hiện dựa trên bộ dữ liệu synthetic tất định, cho phép có ground-truth để đo ARI/NMI nhưng chưa phản ánh đầy đủ độ nhiễu của dữ liệu mạng xã hội thật. Hướng tiếp theo: kiểm chứng trên dữ liệu thực (Zalo/Facebook trong các đợt bão gần đây, kết hợp CrisisMMD/FloodNet).
- **$C_i$ và $V_i$ dạng heuristic/nhẹ.** Phiên bản đầy đủ (mô hình tin cậy học từ lịch sử người dùng, crowd counting/pose estimation chuyên biệt) vượt ngoài hạ tầng 6 tháng, để dành cho giai đoạn sau.
- **Tham số đặt thủ công.** $\sigma_{geo}, \tau, \omega, s$ hiện đặt bởi chuyên gia. Có thể học tự động qua tối ưu hóa hoặc Graph Neural Network trong tương lai.
- **Chưa tích hợp định tuyến.** Bài báo dừng ở xếp hạng ưu tiên + trọng tâm cụm; bước điều phối tối ưu (A\* cost-aware, multi-commodity routing) là công việc tiếp nối.

### 7.1. Các mối đe dọa đến tính hợp lệ (Threats to Validity)

- **Hợp lệ nội tại (internal).** Kết quả dựa trên dữ liệu synthetic có ground-truth do chính nhóm sinh; các "ốc đảo" ngập được thiết kế tách biệt nên độ chính xác cao (ARI 0,892) một phần phản ánh độ tách của dữ liệu, không thuần túy là sức mạnh phương pháp. Giảm thiểu: bổ sung kiểm chứng trên dữ liệu thật (Mục 7).
- **Hợp lệ ngoại tại (external).** Chỉ thử trên một vùng địa lý (Miền Trung VN) và một chế độ thảm họa (bão lũ). Chưa rõ khung tổng quát hóa cho đô thị mật độ cao khác, hay chế độ thảm họa khác (động đất, cháy rừng). Các tham số $\sigma_{geo}, \tau$ cần hiệu chỉnh lại cho từng bối cảnh.
- **Hợp lệ khái niệm (construct).** ARI/NMI đo *độ khớp cấu trúc cụm* với ground-truth, KHÔNG trực tiếp đo *chất lượng quyết định cứu hộ*. Thí nghiệm 7 (Mục 5.8) bước đầu khắc phục điều này bằng một độ đo hướng-kết-quả (thời gian đến nạn nhân yếu thế qua mô phỏng điều phối), cho thấy trọng số tổn thương cải thiện 10,4%; và Thí nghiệm 9 (Mục 5.10) bổ sung V-measure để phân biệt chất lượng cụm mà ARI làm bão hòa. Dù vậy các độ đo này vẫn chạy trên dữ liệu synthetic và mô hình điều phối đơn giản hóa; kiểm chứng kết quả cứu hộ trên dữ liệu/địa hình thực vẫn là việc cần làm.
- **Hợp lệ thống kê (conclusion).** exp3 chạy 10 seed cho kết quả ổn định, nhưng các thí nghiệm khác chủ yếu ở seed = 42. Nên báo cáo trung bình ± độ lệch chuẩn qua nhiều seed cho mọi con số chính.

## 8. Kết luận

Bài báo đề xuất một khung end-to-end kết hợp Edge AI và Lý thuyết Đồ thị Trọng số cho phân cụm và ưu tiên sự kiện cứu hộ bão lũ, lấp đầy ba khe hở khoa học: thiếu thuộc tính vật lý trong trọng số cạnh, điểm mù về tổn thương nhân khẩu học, và thiếu ưu tiên cấp cụm. Hai đóng góp phương pháp then chốt — **hàm trọng số nhân/gating** để địa lý chi phối cấu trúc cụm, và **hàm ưu tiên với hệ số công bằng làm thừa số khuếch đại** — được kiểm chứng định lượng: gating giảm đường kính cụm từ 100 km xuống 0,30 km mà giữ nguyên ARI 0,892; cổng tin cậy chặn 55% dân số ảo từ tin giả. So sánh công bằng trên cùng đồ thị gating cho thấy Louvain vượt Spectral Clustering (ARI 0,339) và HDBSCAN (ARI 0,890 nhưng đường kính 25 km), đồng thời không cần biết trước $K$ như Agglomerative. Kiểm nghiệm Monte-Carlo (200 lần, 3 mức nhiễu) xác nhận xếp hạng $\mathcal{P}(C_k)$ ổn định (Kendall's τ ≥ 0,94 ở ±0,10; top-3 cụm giữ nguyên 99%). Kết quả định hình một chuẩn mực kiến trúc mới cho nền tảng ứng phó thảm họa thông minh, hoạt động bền vững ngay cả khi hạ tầng viễn thông suy kiệt.

---

## Phụ lục B — Đánh giá phản biện và việc cần làm (review nội bộ)

> Mục này ghi lại các điểm yếu đã nhận diện và hành động khắc phục, để hoàn thiện trước khi nộp. Không đưa vào bản LaTeX cuối. **Trạng thái cập nhật (đợt hoàn thiện):** phần lớn các mục 🔴/🟠 đã xử lý — xem dấu ✅ (xong) / ⚠️ (còn lại) dưới đây.

### B.1. Thực nghiệm cần củng cố — ✅ ĐÃ XONG

1. ✅ **Baseline chưa công bằng (ưu tiên cao) — ĐÃ XỬ LÝ (§5.5).** Đã bổ sung Spectral/HDBSCAN/Agglomerative chạy trên *cùng đồ thị gating*, và nâng ablation additive-vs-gating (1A) thành so sánh chính. Yêu cầu gốc:
   - K-Means/DBSCAN trên **cùng ma trận khoảng cách** $d_{ij}=1-w_{ij}$ (hoặc ma trận đặc trưng đa chiều), không chỉ lat/lng.
   - **Spectral Clustering** (ăn trực tiếp affinity $w_{ij}$) và **HDBSCAN** — đây mới là đối thủ đúng nghĩa.
   - Nâng **ablation "Louvain trên đồ thị additive vs gating"** (exp1A) lên thành baseline chính, vì nó cô lập đúng đóng góp.
2. ✅ **Đóng khung lại con số 100 km → 0,30 km — ĐÃ XỬ LÝ (§5.2 (1A), Tóm tắt, Kết luận).** Đã nhấn mạnh vế "co đường kính mà KHÔNG giảm ARI (giữ 0,892)" thay vì trình bày như một phát hiện.
3. ⚠️ **exp3 (Leiden) — ĐÃ XỬ LÝ TRUNG THỰC (§5.4).** Không dựng ca bệnh giả để ép Leiden thắng. Thay vào đó báo cáo trung thực rằng gating tự triệt tiêu cụm đứt gãy (0/0 trên 10 seed), nên Louvain đã đủ; Leiden giữ vai trò "bảo hiểm lý thuyết". Đây là lựa chọn liêm chính học thuật thay vì phóng đại.
4. ✅ **Độ ổn định xếp hạng — ĐÃ XỬ LÝ (§5.6).** Đã thêm Kendall's τ dưới nhiễu loạn $\omega$ (200 Monte-Carlo/mức) và ổn định cấu trúc theo $\sigma_{geo}$.

### B.2. Công thức cần vá — ✅ ĐÃ XONG

1. ✅ **$\mathcal{F}_{max}$ chưa gate $C_i$ (thiếu nhất quán).** $\mathcal{E}_{agg}$ và $\mathcal{N}_{total}$ đều nhân $C_i$ chống tin giả, nhưng $\mathcal{F}_{max}=\max F_i$ thì không — một báo cáo giả $F=1{,}0$ lọt cụm sẽ chiếm trọn. Đề xuất: $\mathcal{F}_{max}=\max_i (F_i\cdot C_i)$ hoặc dùng phân vị 90 thay vì max tuyệt đối. **→ Đã sửa thành $\max_i(F_i\cdot C_i)$ (Mục 4.4), kiểm chứng ở exp1F: báo cáo giả $F=0{,}99$/$C_i=0{,}45$ bị hạ xuống 0,45.**
2. ✅ **$N_{\max}$ trong $\widetilde{\mathcal{N}}$ gây thang đo trôi (non-stationary).** "Cụm lớn nhất trong cửa sổ hiện tại" khiến cùng một cụm có $\mathcal{P}$ khác nhau tùy các cụm khác. Nêu rõ đây là *ranking tương đối tức thời*, hoặc dùng mốc cố định (dân số tham chiếu theo địa bàn) nếu cần so sánh across-time. **→ Đã nêu rõ hai chế độ mốc động/cố định và tính non-stationary trong Mục 4.4.**
3. ✅ **Nguy cơ double-counting $F, E$.** $F$ và $E$ vừa vào $\mathcal{S}_{context}$ (quyết định gom cụm) vừa vào $\mathcal{F}_{max}/\mathcal{E}_{agg}$ (quyết định ưu tiên). Cụm gom theo $F$ tương đồng thì $\mathcal{F}_{max}$ gần như được đảm bảo cao — hơi vòng tròn. Cần một đoạn thảo luận thừa nhận và biện minh (weighting đo *tương đồng*, priority đo *độ nghiêm trọng tuyệt đối* — khác mục đích). **→ Đã thêm đoạn thảo luận (Mục 4.4) VÀ định lượng bằng exp6: bỏ $\mathcal{S}_{context}$ đổi phân cụm (ARI 0,892→0,7855) nhưng gần như không đổi thứ hạng (Kendall's τ = 0,9829).**

### B.3. Lập luận cần chặt hơn — ✅ ĐÃ XONG

- ✅ **Khe hở 2 (equity):** exp1C mới cho thấy thêm $V$ *đổi* ranking, chưa chứng minh ranking mới *đúng hơn*. Cần một lập luận chuẩn tắc (normative) hoặc ví dụ minh họa vì sao ranking có equity công bằng hơn về mặt đạo đức cứu hộ. **→ Đã bổ sung exp7 (mô phỏng điều phối hướng-kết-quả): bỏ $V_i$ làm trễ thời gian đến người yếu thế 10,4% — chứng minh ranking có equity cho kết quả TỐT HƠN, kèm đánh đổi công bằng–hiệu quả minh bạch.**
- ✅ **Thiếu mục "Threats to Validity"** — chuẩn mực bài báo ML/hệ thống. Nên thêm: internal (dữ liệu synthetic), external (chỉ 1 vùng địa lý), construct (ARI đo cấu trúc ≠ chất lượng cứu hộ). **→ Đã thêm Mục 7.1 đầy đủ bốn trục internal/external/construct/conclusion.**

### B.4. Kiểm tra trích dẫn của `PaperV2.md` (đã đối chiếu nguồn thật)

**Không có trích dẫn bịa hoàn toàn** — mọi URL đều tồn tại. Nhưng ba nhóm vấn đề:

**(a) Claim bị thổi phồng — phải sửa:**

- **[^16] ResQConnect:** paper thật, nhưng claim "mô hình nén trên di động, độ trễ **< 500 ms**" KHÔNG có trong nguồn (nguồn chỉ nói "on-device offline triage"). → Bỏ con số 500 ms hoặc lấy từ EmergencyNet.

**(b) Đã xác minh chắc chắn ✓:** [^9]/[^11] CrisisSpot (F1 +5,01% và +9,45% — khớp), [^2] GNN-SAGE, [^47] CaST, [^35] Louvain (lưu ý O(N log N) là ước lượng thực nghiệm), [^51] Leiden (Louvain tới 25% cụm đứt gãy), [^42] vulnerability prioritization, [^25] TF-IDF weighted graph, [^26] Dong et al., [^13] ConvGraph.

**(c) Nguồn KHÔNG đạt chuẩn học thuật (12 refs — nên thay bằng peer-reviewed):**

| Ref hiện tại                              | Loại                                    | Thay bằng                                                                                                     |
| :------------------------------------------ | :--------------------------------------- | :------------------------------------------------------------------------------------------------------------- |
| [^36] Wikipedia, [^37] Xilinx, [^52] Medium | định nghĩa Modularity/Louvain         | **Blondel et al. 2008** (J. Stat. Mech. P1008); **Newman & Girvan 2004** (Phys. Rev. E 69, 026113) |
| [^31] Stack Overflow                        | K-Means vs community detection           | **Fortunato 2010** (Physics Reports); **Fortunato & Hric 2016**                                    |
| [^30] (claim không thấy ở abstract)      | giới hạn K-Means/DBSCAN                | **MacQueen 1967**; **Ester et al. 1996** (DBSCAN); **Schubert et al. 2017**                  |
| [^54] Meegle (SEO)                          | ma trận quyết định MCDM              | **Saaty 1980** (AHP); **Triantaphyllou 2000**                                                      |
| [^5],[^6],[^17],[^21] blog/vendor           | Edge AI cho thảm họa                   | **Kyrkou & Theocharides 2020** (EmergencyNet); **Merenda et al. 2020** (Sensors)                   |
| [^57] Scribd (mini-project SV)              | flood management AI                      | **Munawar et al. 2022**; hoặc survey peer-reviewed                                                      |
| [^19] IDGA (trade press)                    | embedded AI/drone                        | thay bằng paper IEEE về UAV edge inference                                                                   |
| [^18] UN-SPIDER                             | (URL có ký tự thừa`%C2%A0` → 404) | sửa URL; giữ như nguồn institutional cho motivation                                                        |

**Nguyên tắc:** blog/vendor chấp nhận được cho phần *motivation*, nhưng mọi claim **định lượng** (500 ms, MB→KB, F1, O(N log N)) và mọi **định nghĩa toán học** phải trỏ về nguồn peer-reviewed.

**(d) Cần tự kiểm tra:** [^34] GraphHDBSCAN* — DOI prefix `10.64898` hợp lệ (bioRxiv 2026), nhưng không xác nhận được paper cụ thể; mở URL kiểm tra, nếu không load thì thay.

---

## Phụ lục A — Ghi chú soạn thảo và việc cần làm khi chuyển LaTeX

- **Trích dẫn:** `PaperV2.md` đã có sẵn danh mục ~62 nguồn (`[^1]`–`[^62]`). Khi chuyển LaTeX, ánh xạ các trích dẫn trong bài này về BibTeX (repo đã có `splncs04.bst` — style Springer LNCS, gợi ý bài định dạng theo LNCS/hội nghị).
- **Hình và bảng:** nhúng 7 hình từ `demo/results/figures/` và các bảng số liệu từ `results/tables/*.json`. Mọi con số trong Mục 5 đã đối chiếu trực tiếp với các file JSON đó (seed = 42).
- **Công thức:** tất cả công thức đã ở dạng LaTeX inline/display, chuyển thẳng sang môi trường `equation`.
- **Ngôn ngữ:** bản này bằng tiếng Việt; nếu cần bản song ngữ hoặc tiếng Anh cho hội nghị quốc tế, dịch sau khi chốt nội dung.
- **Cần bổ sung khi có:** tên nhóm tác giả + đơn vị (ĐH Cần Thơ, Trường CNTT&TT), phần Acknowledgements, và mã số đề tài.

> ⚠️ **Cảnh báo bảo mật:** file nguồn `resource/giải trình thay đổi V1 sang V2.md` (dòng cuối) chứa một chuỗi trông giống **khóa bí mật/API key bị lộ** (tiền tố `sk-...`). Chuỗi này KHÔNG được đưa vào bài báo. Nên xóa khỏi file nguồn và thu hồi (rotate) khóa nếu nó là khóa thật đang dùng.
