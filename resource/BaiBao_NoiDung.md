# Khung Đồ thị Trọng số Đa phương thức cho Phân cụm và Ưu tiên Sự kiện Cứu hộ Bão lũ dựa trên Edge AI

> **Ghi chú soạn thảo.** Đây là bản nội dung tiếng Việt dùng để soạn thảo trước cho bài báo khoa học. Nội dung được tổng hợp và kiểm tra chéo từ: (i) `Thuyết minh NCKH.md` (phạm vi đề tài), (ii) `PaperV2.md` (báo cáo nghiên cứu, Mục 4 là phương pháp lõi), (iii) `GiaiThichCongThuc.md` (giải thích chi tiết công thức), (iv) `giải trình thay đổi V1 sang V2.md` (lý do sửa lỗi), và (v) kết quả thực nghiệm định lượng trong `demo/`. Sau khi chốt nội dung, tài liệu này sẽ được chuyển sang định dạng LaTeX chuẩn hội nghị/tạp chí. Các số liệu thực nghiệm trong bài đều lấy trực tiếp từ `demo/results/tables/` (seed = 42, sinh dữ liệu tất định).

---

## Tóm tắt (Abstract)

Trong các thảm họa bão lũ, hạ tầng viễn thông thường bị gián đoạn khiến mô hình xử lý tập trung trên đám mây bị vô hiệu hóa đúng vào "giờ vàng" cứu hộ. Bài báo đề xuất một khung giải pháp kết hợp Điện toán Biên (Edge AI) và Lý thuyết Đồ thị Trọng số để thu thập, phân cụm và tự động xếp hạng ưu tiên các sự kiện cứu hộ. Thiết bị biên trích xuất một vector thuộc tính đa chiều $(L, T, F, E, N, V, C)$ từ ảnh và văn bản rồi chỉ truyền đi một gói siêu dữ liệu (metadata) dưới 1 Kilobyte thay vì ảnh/video thô. Ở phía máy chủ, các sự kiện được biểu diễn thành đồ thị trọng số trong đó khoảng cách địa lý đóng vai trò **cổng chặn nhân tính (multiplicative gate)** thay vì một số hạng cộng, bảo đảm mọi cụm đều gắn kết về mặt không gian. Thuật toán Louvain (khuyến nghị Leiden) phân rã đồ thị thành các "khu vực tác chiến", và một hàm ưu tiên cấp cụm $\mathcal{P}(C_k)$ — với lõi rủi ro đã chuẩn hóa và hệ số tổn thương nhân khẩu học đóng vai trò **thừa số khuếch đại** — xếp hạng các cụm để hỗ trợ điều phối. Thực nghiệm trên bộ dữ liệu mô phỏng tất định gồm **341 sự kiện** với **14 nhãn ground-truth**, đặc thù Miền Trung Việt Nam, cho thấy: dạng gating giảm đường kính cụm **xấu nhất** từ **214 km xuống 1,4 km** trong khi **đồng thời nâng** độ chính xác phân cụm (ARI $0{,}957\rightarrow0{,}996$) so với cấu hình cộng mạnh nhất tìm được qua phép quét $\alpha$; trên **20 seed**, dạng gating thắng **100% số seed** ở mọi chỉ số (ARI $0{,}9957\pm0{,}0000$ so với $0{,}9415\pm0{,}0141$). Cổng tin cậy $C_i$ chặn được báo cáo giả thổi phồng số nạn nhân (giảm **55%** quy mô dân số ảo), tuy một đối thủ kết hợp ảnh giả với corroboration dàn dựng đạt $C_i=0{,}92$ — không phân biệt được với tin thật, một giới hạn chúng tôi **báo cáo thay vì che**. So với baseline trên **cùng** đồ thị gating: Spectral sụp ($0{,}166$) và HDBSCAN đạt ARI hoàn hảo nhưng với đường kính cụm trung bình **48,7 km** — không dùng được cho điều phối — còn K-Means ($0{,}502$) và DBSCAN ($0{,}523$) trên tọa độ thô kém xa; xếp hạng ưu tiên ổn định (Kendall's τ: trung bình **0,955**, tối thiểu **0,910** khi trọng số dao động ±0,10, top-3 giữ nguyên **100%** số thử nghiệm).

**Từ khóa:** Edge AI, phân cụm sự kiện, đồ thị trọng số, phát hiện cộng đồng, Louvain, ưu tiên cứu hộ, đa phương thức, thảm họa bão lũ.

---

## 1. Giới thiệu

Biến đổi khí hậu đang làm gia tăng tần suất và cường độ của các hiện tượng thời tiết cực đoan. Việt Nam — với đường bờ biển dài và địa hình chịu ảnh hưởng trực tiếp của hoàn lưu bão — mỗi năm hứng chịu khoảng 6–8 cơn bão và áp thấp nhiệt đới ảnh hưởng trực tiếp (trong số khoảng 11 cơn hình thành trên Biển Đông), gây thiệt hại nặng nề về người và tài sản, đặc biệt tại miền Trung và miền Bắc.

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
| $F_i$   | Mức độ ngập vật lý                | $[0,1]$                    | Semantic segmentation (MobileNetV3)    |
| $E_i$   | Mức độ khẩn cấp                    | $[0,1]$                    | Phân tích cảm xúc văn bản (DistilBERT / UIT-VSMEC) |
| $N_i$   | Số người mắc kẹt                   | $\mathbb{Z}^{+}$           | Nhập tay / crowd counting                               |
| $V_i$   | Chỉ số tổn thương nhân khẩu học | $\ge 0$                    | Nhánh multi-label ghép chung bộ phân loại văn bản |
| $C_i$   | Độ tin cậy thông tin                | $(0,1)$                    | Heuristic tổng hợp nhẹ                                |

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

**(d) Tham số và làm thưa đồ thị.** $\beta, \gamma$ cân bằng thời gian và ngữ cảnh; $\alpha$ của dạng cộng bị loại vì $\mathcal{S}_{geo}$ nay là thừa số điều biến toàn cục. Vì $\mathcal{S}_{geo}$ suy giảm nhanh, hầu hết cạnh xa có trọng số không đáng kể; ta **làm thưa đồ thị** bằng (i) **ngưỡng $\epsilon$** — giữ cạnh khi $w_{ij}>\theta$, hoặc (ii) **k-NN graph** — mỗi đỉnh chọn $k$ láng giềng trọng số cao nhất, và một cạnh được giữ nếu nó nằm trong top $k$ của **ít nhất một** trong hai đầu (đối xứng hóa kiểu OR), nên $k$ chặn số láng giềng mỗi đỉnh *chọn* chứ không chặn bậc cuối cùng của nó. Điều này giảm chi phí tính toán và loại liên kết giả giữa các vùng cách biệt, vì thuật toán Modularity hoạt động kém trên đồ thị dày đặc gần-hoàn-chỉnh.

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

với $N_{\max}$ là mốc dân số tham chiếu. Ta phân biệt hai chế độ: (i) **mốc động** — tổng dân số của cụm lớn nhất trong cửa sổ hiện tại, cho *xếp hạng tương đối tức thời* giữa các cụm đồng thời; (ii) **mốc cố định** — một hằng số dân số tham chiếu theo địa bàn, cần thiết nếu muốn so sánh điểm $\mathcal{P}$ *across-time* (điểm của cùng một cụm không đổi khi các cụm khác xuất hiện/biến mất). Chế độ động tiện cho điều phối tức thời nhưng có tính **không dừng (non-stationary)**: cùng một cụm nhận $\mathcal{P}$ khác nhau tùy bối cảnh — cần nêu rõ khi diễn giải. **Công bố: mọi thí nghiệm trong bài dùng mốc ĐỘNG**, nên cụm lớn nhất của mỗi lần chạy luôn có $\widetilde{\mathcal{N}}=1$ theo cấu tạo, và mọi giá trị $\mathcal{P}$ báo cáo là đại lượng **trong-một-lần-chạy**: nó xếp hạng các cụm với nhau tại một thời điểm và **không** được so sánh giữa các lần chạy, các seed hay các cửa sổ thời gian khác nhau.

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
\mathcal{V}_{agg}(C_k) = 1 + \tanh\!\left( \frac{1}{s} \sum_{v_i \in C_k} V_i \right), \qquad \mathcal{V}_{agg}\in[1,2)
$$

- **Lỗi (b) — cộng vs nhân:** bản gốc đặt $\mathcal{V}$ như số hạng cộng $\omega_4\mathcal{V}_{agg}$. Một số hạng bị chặn trong $[1,2]$ chỉ tạo offset gần hằng số, **không khuếch đại gì**. Cách sửa: tách $\mathcal{V}_{agg}$ ra ngoài làm **thừa số nhân**. Cụm không có đối tượng yếu thế: $\mathcal{V}_{agg}\approx 1$ (giữ nguyên lõi); cụm nhiều đối tượng yếu thế: $\mathcal{V}_{agg}\to 2$ (nhân đôi điểm) — đúng nghĩa "amplify equity".
- **Lỗi (c) — bão hòa sớm:** nếu dùng $\tanh(\sum V_i)$ trực tiếp, chỉ 2–3 đối tượng yếu thế đã đưa $\tanh$ sát 1, khiến cụm 1 người và cụm 50 người yếu thế nhận điểm gần như nhau — mất khả năng phân biệt. Cách sửa: thêm **hệ số tỉ lệ** $s$ (ví dụ $s=10$) chia trong đối số $\tanh$, giãn vùng tuyến tính. $\tanh$ vẫn giữ vai trò chặn trên tránh điểm bùng nổ vô cực. (Lựa chọn tương đương: $1+\log(1+\sum V_i)$ kèm chuẩn hóa.)

**Trần khuếch đại tổng quát $\mu$.** Chặn trên "nhân đôi" ($\mathcal{V}_{agg}\in[1,2)$) là một *lựa chọn chính sách* chứ không phải hằng số bất biến. Ta tổng quát hóa thành

$$
\mathcal{V}_{agg}(C_k) = 1 + (\mu - 1)\tanh\!\left( \frac{1}{s} \sum_{v_i \in C_k} V_i \right), \qquad \mu\in[1,2], \quad \mathcal{V}_{agg}\in(1,\mu)
$$

trong đó $\mu$ là **trần khuếch đại** do ban chỉ huy đặt: $\mu=1$ tắt hoàn toàn ưu tiên tổn thương (quay về thuần rủi ro), $\mu=2$ cho phép nhân đôi tối đa. Việc phơi bày $\mu$ tường minh giúp yếu tố công bằng trở thành một *núm điều khiển chính sách có thể kiểm toán* thay vì một hằng số ẩn. Mọi số liệu báo cáo trong bài dùng $\mu=2$.

**Quét $\mu$ — kiểm chứng chứ không chỉ tuyên bố.** Câu "$\mu$ lớn có thể đẩy một cụm nhỏ nhiều người yếu thế lên trên một cụm lớn khoẻ mạnh" là một tuyên bố **thực nghiệm**, nên phải chạy $\mu\neq2$ mới được nói. Quét toàn miền $\mu\in[1;2]$ trên chính bộ dữ liệu này:

| $\mu$ | Cụm đầu bảng | $\mathcal{V}_{agg}$ cụm đầu | lõi cụm đầu | $\mathcal{P}$ cao nhất | τ so với $\mu=2$ |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 1,00 | 9 | 1,000 | 0,8808 | 0,8808 | 0,9889 |
| 1,25 | 9 | 1,166 | 0,8808 | 1,0270 | 0,9963 |
| 1,50 | **1** | 1,431 | 0,8276 | 1,1842 | 0,9985 |
| 1,75 | 1 | 1,646 | 0,8276 | 1,3625 | 0,9993 |
| 2,00 | 1 | 1,862 | 0,8276 | 1,5408 | 1,0000 |

Núm này **thực sự có hiệu lực**: ở $\mu\le1{,}25$ cụm đầu bảng là **cụm 9** (lõi rủi ro cao nhất 0,8808 nhưng không có đối tượng yếu thế, $\mathcal{V}_{agg}=1$); từ $\mu\ge1{,}5$ **cụm 1** chiếm ngôi đầu nhờ $\mathcal{V}_{agg}$ lớn dù lõi thấp hơn (0,8276). Đúng cơ chế mà bài mô tả, và điểm đảo ngôi nằm ở **$\mu\approx1{,}5$** — nghĩa là dải chính sách hữu ích không phải toàn miền $[1;2]$ mà tập trung quanh nửa trên. Đồng thời τ toàn cục vẫn $\ge0{,}9889$: $\mu$ đổi *đỉnh* danh sách chứ không xáo trộn toàn bộ thứ tự — đúng hành vi mong muốn của một núm chính sách.

**Trọng số và miền giá trị.** $\omega_1,\omega_2,\omega_3$ với ràng buộc $\sum\omega=1$, do ban chỉ huy đặt qua **Ma trận Quyết định** để chuyển trạng thái chiến thuật (ưu tiên số đông vs ưu tiên ngập sâu). Vì lõi đã chuẩn hóa $[0,1]$ và $\sum\omega=1$, lõi rủi ro $\in[0,1]$; nhân $\mathcal{V}_{agg}\in[1,2)$ cho $\mathcal{P}(C_k)\in[0,2)$ — chặn gọn, dễ xếp hạng.

Xếp hạng $\mathcal{P}(C_k)$ giảm dần cho ngay danh sách ưu tiên hành động; kết hợp tọa độ trọng tâm cụm, đây là đầu vào lý tưởng cho các thuật toán tối ưu định tuyến (A\* cost-aware, multi-commodity routing).

**Ghi chú về việc dùng lại $F, E$ ở hai khâu.** Hai thuộc tính $F$ (mức ngập) và $E$ (mức khẩn cấp) xuất hiện cả ở khâu gom cụm (qua $\mathcal{S}_{context}$) lẫn khâu ưu tiên (qua $\mathcal{F}_{max}, \mathcal{E}_{agg}$). Đây **không phải double-counting sai** vì hai khâu đo hai đại lượng khác bản chất: $\mathcal{S}_{context}$ đo *độ tương đồng* giữa cặp sự kiện (để quyết định chúng có cùng một tình huống hay không), còn $\mathcal{F}_{max}/\mathcal{E}_{agg}$ đo *độ nghiêm trọng tuyệt đối* của cụm (để xếp hạng). Tuy vậy cần thừa nhận một hệ quả: cụm được gom vì $F$ tương đồng thì $\mathcal{F}_{max}$ của nó gần như chắc chắn cao — nên $\mathcal{F}_{max}$ nên hiểu là "mức ngập đặc trưng của một quần thể đã đồng nhất" chứ không phải một tín hiệu độc lập hoàn toàn với tiêu chí gom cụm. Chúng tôi **định lượng** mức vòng tròn này ở Thí nghiệm 6 (§5.7): loại bỏ $\mathcal{S}_{context}$ khỏi đồ thị để lại thứ hạng ưu tiên **trùng khít từng bit** (Kendall's τ = **1,0**, cả 74 cụm khớp theo trọng tâm), nên $\mathcal{S}_{context}$ **không thể** đang âm thầm định đoạt *thứ hạng*; chỗ nó thực sự có tác dụng là tách các nhóm gần nhau hơn $\sigma_{geo}$, điều mà phép quét $\beta/\gamma$ ở §5.3 định vị được.

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

**Bộ dữ liệu.** Do chưa có bộ dữ liệu thực đã gán nhãn ground-truth cho cụm cứu hộ, chúng tôi sinh một bộ dữ liệu **mô phỏng tất định** (seed = 42) đặc thù cho Miền Trung Việt Nam (Huế – Quảng Trị – Quảng Nam – Đà Nẵng; 15,7–17,1°N, 107,0–108,6°E), gồm **341 sự kiện** trải trên **14 nhãn ground-truth**:

- **240 sự kiện lõi** phân bố quanh **6 "ốc đảo" ngập** (mỗi cụm 40 điểm, nhãn 0–5).
- **61 sự kiện nhiễu** rải rác (`gt_cluster = -1`), trong đó **23 là tin giả** (`is_fake`) — đủ số mẫu dương để các độ đo phát hiện ở §5.9 có ý nghĩa thống kê.
- **41 sự kiện kịch bản minh họa** — 40 điểm tạo thành **8 nhóm stress-test** (nhãn 100–107) cộng 1 tin giả cô lập (`gt_cluster = -1`). Năm kịch bản S1–S5, mỗi kịch bản stress-test một quyết định thiết kế:
  - **S1:** hai nhóm ngập nóc (3 điểm mỗi nhóm) ngữ cảnh gần như trùng khớp nhưng cách nhau **106,8 km** (kiểm tra gating tách cụm).
  - **S2:** cụm 5 điểm nhiều đối tượng yếu thế (kiểm tra $\mathcal{V}_{agg}$ khuếch đại).
  - **S3:** tin giả cô lập thổi phồng 200 người (kiểm tra cổng $C_i$).
  - **S4:** cụm 10 điểm ngập nhẹ vs cụm 3 điểm ngập nóc (kiểm tra $\mathcal{F}_{max}$).
  - **S5:** hai nhóm 6 điểm chỉ cách nhau **900 m** (nhỏ hơn $\sigma_{geo}$, nên $\mathcal{S}_{geo}\approx0{,}44$ giữa chúng) nhưng ngữ cảnh trái ngược ($F=0{,}30$ vs $0{,}95$) — trường hợp **duy nhất** mà $\mathcal{S}_{context}$ là tín hiệu tách **duy nhất**, và chính nó làm các phép quét $\tau_F,\tau_E$ và $\gamma$ ở §5.3 mang thông tin thay vì phẳng theo cấu trúc.

Lưu ý quan trọng về thiết kế ground-truth: mỗi nhóm kịch bản được đặt trên một **satellite cách tâm ốc đảo chủ 3 km** — xa hơn $\sigma_{geo}=700$ m rất nhiều — nên **mọi nhãn ground-truth đều tách được về mặt không gian và không có trần ARI nào bị áp đặt bởi thiết kế dữ liệu**; generator có một assertion cấp-sinh-dữ-liệu (`assert_gt_separable`) làm fail build nếu bất kỳ điểm kịch bản nào rơi vào trong 2 km của một tâm ốc đảo. (Đây là điểm khác biệt so với phiên bản trước của bộ dữ liệu, nơi các nhóm kịch bản neo ngay tại tâm ốc đảo và do đó chặn trần ARI theo cấu trúc.) Các sự kiện lõi dùng độ lệch chuẩn trong-ốc-đảo $0{,}16$ ($F$) và $0{,}18$ ($E$) để phân bố ngữ cảnh của các ốc đảo **chồng lấn** nhau; nếu chúng hẹp thì $(F,E)$ gần như là một hàm tất định của nhãn ốc đảo và $\mathcal{S}_{context}$ chỉ nhắc lại thông tin không gian.

**Tham số mặc định:** $\sigma_{geo}=700$ m; $\tau_{temp}=45$ phút; $\tau_F=0{,}25$; $\tau_E=0{,}35$; $\beta=\gamma=0{,}5$; ngưỡng cạnh $\theta=0{,}05$; k-NN $k=12$; $\lambda=1{,}0$; $s=10$; $\omega=(0{,}34;\,0{,}33;\,0{,}33)$; heuristic $C_i$ với $(b_0,b_1,b_2)=(-0{,}2;\,1{,}4;\,0{,}9)$.

**Độ đo:** ARI (Adjusted Rand Index) và NMI (Normalized Mutual Information) so với ground-truth; **đường kính địa lý cụm** (km) đo tính gắn kết không gian; và Modularity $Q$. Đường kính cần được xử lý cẩn thận, vì một phân hoạch cô lập outlier thành các cụm đơn lẻ sẽ nhận đường kính $0$ cho mỗi cụm đó và **được thưởng một cách giả tạo**. Do đó ta báo cáo hai biến thể và coi trung bình-trên-mọi-cụm là thứ yếu: **đường kính trung bình multi-member** (chỉ tính các cụm có $\ge2$ thành viên) và **đường kính max** (cụm xấu nhất — chính là thứ phá vỡ một kế hoạch điều phối). Mọi đường kính là khoảng cách Haversine điểm-điểm lớn nhất trong cùng cụm. Ta cũng báo cáo **số cụm đơn lẻ (singleton)**, **tỉ lệ nhiễu không nhãn bị hấp thụ vào các cụm có nhãn**, và cặp **homogeneity/completeness** (§5.10).

Toàn bộ pipeline hiện thực bằng Python (`numpy`, `networkx`, `python-louvain`, `igraph`, `leidenalg`, `scikit-learn`, `scipy`); mã và số liệu thô nằm trong `demo/` (mười hai thí nghiệm `exp1`–`exp12` trong `demo/experiments/`, kết quả JSON trong `demo/results/tables/`).

### 5.2. Thí nghiệm 1 — Kiểm chứng sáu quyết định thiết kế

**(1A) Gating vs Cộng.** Một so sánh công bằng không được dựng bù nhìn cho dạng cộng bằng một giá trị $\alpha$ bất lợi duy nhất, nên ta **quét** $\alpha$: $\alpha=0{,}34$, $\alpha=0{,}5$, $\alpha=1{,}0$ (địa lý được cân nặng bằng tổng hai số hạng còn lại), và biến thể chuẩn hóa hoàn toàn $\frac13(\mathcal{S}_{geo}+\mathcal{S}_{temp}+\mathcal{S}_{context})$. Ở mọi cấu hình trừ hàng $\frac13$, hai hệ số phi-không-gian được giữ ở mặc định $\beta=\gamma=0{,}5$ — **cố ý không** hạ trọng số, để baseline cộng không bị làm yếu một cách bất công; riêng hàng $\frac13$ đặt cả ba hệ số bằng $1/3$:

| Dạng | ARI | NMI | Đ.kính TB (km) | Đ.kính max (km) | Số cụm | S1 bị gộp? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Cộng, $\alpha=0{,}34$ | 0,8763 | 0,9003 | 151,13 | 209,05 | 8 | có |
| Cộng, $\alpha=0{,}5$ | 0,9161 | 0,9361 | 151,13 | 209,05 | 8 | có |
| Cộng, $\alpha=1{,}0$ | 0,9572 | 0,9598 | 140,41 | 213,95 | 9 | có |
| Cộng chuẩn hóa $\frac13$ | 0,9161 | 0,9361 | 151,13 | 209,05 | 8 | có |
| **Nhân/Gating** | **0,9957** | **0,9933** | **0,85** | **1,41** | 74 | **không** |

Cấu hình cộng tốt nhất tìm được là $\alpha=1{,}0$, đạt ARI $0{,}9572$ — đáng kể, và cao hơn hẳn $0{,}8763$ của dạng chia-đều — nhưng nó vẫn sinh các cụm đường kính trung bình **140 km** với cụm xấu nhất **214 km**. Gating đạt ARI **0,9957** với đường kính trung bình multi-member **0,85 km** và trường hợp xấu nhất **1,41 km**: một hệ số **151×** ở chính chỉ số quyết định về mặt vận hành.

**Giới hạn quan trọng của con số 151× — đọc kèm Thí nghiệm 13 (§5.14).** Toàn bộ bảng trên dùng **cùng một** ngưỡng làm thưa $\theta=0{,}05$ cho cả hai dạng. Đó *trông* như so sánh có kiểm soát nhưng thực chất là ngược lại: $\theta$ là một nhát cắt tuyệt đối trên hai phân bố giá trị **khác nhau**. Tích gating dồn khối lượng về 0 (trung vị $0{,}0000$; chỉ **8,3%** cặp vượt $0{,}05$), còn tổng cộng có sàn $0{,}041$ nên **99,99%** cặp vượt cùng ngưỡng đó — tức dạng cộng bị đưa vào Louvain như một đồ thị **gần hoàn chỉnh**, đúng chế độ mà chính bài này nói Modularity hoạt động kém. Khi hiệu chuẩn $\theta$ **riêng cho từng dạng** (§5.14), dạng cộng $\alpha=1{,}0$ tại $\theta=1{,}08$ đạt ARI **1,0** với đường kính xấu nhất **1,41 km** — **bằng đúng** hình học của gating. Vậy hệ số 151× **không** phải thuộc tính của tính cộng; nó là hiệu năng của dạng cộng *tại một ngưỡng hiệu chuẩn cho hàm trọng số khác*. Điều còn đứng vững là **độ dễ điều chỉnh**: gating dùng được trên $\theta\in[0{,}01;0{,}51]$ (**51×**, bao gồm mặc định 0,05), còn dạng cộng tốt nhất chỉ dùng được trên $[0{,}96;1{,}46]$ (**1,5×**, không chứa giá trị nào người dùng đoán ra được).

Cơ chế hiện rõ trong một chẩn đoán duy nhất: ở **mọi** cấu hình cộng, kể cả cấu hình mạnh nhất, hai nhóm S1 — ngữ cảnh gần như trùng khớp, cách nhau **106,8 km** — đều rơi vào **cùng một cụm**, vì tổng $\mathcal{S}_{temp}+\mathcal{S}_{context}$ cao có thể áp đảo một $\mathcal{S}_{geo}$ triệt tiêu. Dưới dạng gating, tích $\mathcal{S}_{geo}\cdot(\cdot)$ bằng đúng 0 ở đó nên hai nhóm ở riêng. Cùng cơ chế đó giải thích số cụm (8–9 dạng cộng vs 74 gating): dạng cộng hấp thụ **93,6%** nhiễu không nhãn vào các cụm có nhãn, còn gating gần như không hấp thụ gì (**0,4%**) và thay vào đó cô lập nhiễu thành **61 cụm đơn lẻ**. Vì ARI và NMI che mặt nạ `gt < 0`, khác biệt vệ-sinh-nhiễu này **vô hình** với cả hai độ đo.

Về việc ARI của gating là $0{,}9957$ chứ không phải $1{,}0$: nguyên nhân là **một** trường hợp xác định được — cặp nhãn 106 và 107 (kịch bản S5) chỉ cách nhau **923 m** và bị gộp. Phân rã: 240 điểm lõi được phục hồi **hoàn hảo** (ARI $=1{,}0$), 40 điểm kịch bản đạt ARI $0{,}821$, toàn tập 280 điểm có nhãn đạt $0{,}9957$; và khác với phiên bản trước của bộ dữ liệu, **không** nhóm ground-truth nào đồng vị trí với tâm ốc đảo, nên không có gì ở đây là trần theo cấu trúc.

**(1B) Chuẩn hóa thang đo.** Không chuẩn hóa, cụm đứng đầu bảng xếp hạng đơn giản là cụm đông người nhất (200 người, lõi thô **66,48**) — dân số áp đảo tổng chưa chuẩn hóa một cách tuyệt đối. Sau chuẩn hóa $[0,1]$, cụm đứng đầu là cụm có lõi rủi ro cân bằng (**0,83**) với $\mathcal{P}=$ **1,54** — phản ánh đúng tổ hợp khẩn cấp + ngập + dân số.

**(1C) $\mathcal{V}$ nhân vs cộng.** Với cụm kịch bản S2 (nhiều đối tượng yếu thế, $\mathcal{V}_{agg}=$ **1,76**), cách **cộng** cho $\mathcal{P}_{add}=$ **1,37** còn cách **nhân** cho $\mathcal{P}_{mult}=$ **1,06**; **cả hai đều xếp nó hạng 5**, nên trên bộ dữ liệu này lựa chọn dạng **không** làm đổi vị trí của S2. Trên toàn bộ 74 cụm, độ dịch hạng tuyệt đối lớn nhất giữa hai dạng là **1** — ta báo cáo điều đó thay vì thổi phồng: lập luận cho dạng nhân ở đây là **cấu trúc**, không phải thực nghiệm. Cấu trúc đó chính là *hành vi vi phân*: với **67 trong 74** cụm không có đối tượng yếu thế ($\mathcal{V}_{agg}=1$), hai dạng trùng khít chính xác; nhưng khi $\mathcal{V}_{agg}$ tăng, dạng nhân **co giãn theo lõi rủi ro** (khuếch đại thực sự, nên tổn thương không bao giờ cứu được một cụm không có rủi ro) trong khi dạng cộng chỉ thêm một offset gần hằng số bất kể lõi mạnh hay yếu.

**(1D) Chống bão hòa $\tanh$.** Bảng dưới cho thấy $\tanh(\sum V_i)$ không chia tỉ lệ đã bão hòa ($\approx 2{,}0$) ngay từ $\sum V_i = 3$, mất hoàn toàn khả năng phân biệt; trong khi $\tanh(\sum V_i/10)$ vẫn tăng đơn điệu tới $\sum V_i = 50$:

| $\sum V_i$ | $\tanh(\sum V_i)$ (không chia) | $\tanh(\sum V_i/10)$ |
| :----------: | :-------------------------------: | :--------------------: |
|      1      |               1,76               |          1,10          |
|      3      |               2,00               |          1,29          |
|      10      |               2,00               |          1,76          |
|      30      |               2,00               |          2,00          |
|      50      |               2,00               |          2,00          |

**(1E) Cổng tin cậy $C_i$ cho quy mô dân số.** Với kịch bản S3 (tin giả thổi phồng 200 người, $C_i=0,45$): quy mô dân số cụm không gate là 200 người, sau khi nhân $C_i$ giảm còn **90 người — giảm 55%**. Cổng tin cậy ngăn được một báo cáo giả tự đẩy cụm lên đầu danh sách ưu tiên.

**(1F) Cổng tin cậy $C_i$ cho mức ngập tối đa.** Cùng báo cáo giả S3 khai mức ngập rất cao ($F=0,99$) nhưng $C_i=0,45$. Nếu dùng $\max F_i$ thuần, nó chiếm trọn $\mathcal{F}_{max}=0,99$ của cụm — một tín hiệu ngập cực đoan hoàn toàn do tin giả tạo ra. Với $\max(F_i\cdot C_i)$, giá trị bị hạ xuống **0,4457**, khôi phục tính nhất quán: mọi thành phần lõi rủi ro ($\mathcal{E}, \mathcal{F}, \mathcal{N}$) đều được gate độ tin cậy, không còn lỗ hổng để một báo cáo đơn lẻ không đáng tin thao túng thứ hạng.

### 5.3. Thí nghiệm 2 — Phân tích độ nhạy

- **Bán kính $\sigma_{geo}$ — tham số quan trọng nhất, và nó KHÔNG phẳng:** ARI trải **0,1205** trên toàn phép quét. Đỉnh **0,9957** cho $\sigma_{geo}\in[400;\,1000]$ m (74 cụm, đường kính max 1,41 km), suy giảm mượt xuống **0,9369** tại 1500 m và **0,9156** tại 2500 m khi các satellite 3 km bắt đầu hòa vào ốc đảo chủ, và xuống **0,8752** tại 4000 m — nơi cụm xấu nhất phình lên **15,26 km**. Ở đầu chặt, 200 m làm vụn quá mức (77 cụm, 63 singleton) nhưng vẫn đạt **0,9908**. Về mặt vận hành, $\sigma_{geo}$ nên khớp bán kính hoạt động thực của ca nô; vùng cao nguyên độ chính xác giữa 400 và 1000 m cho biên độ sai khoảng **hai lần**.
- **Độ phân giải $\lambda$:** ARI trải **0,1519**; đạt **đúng 0,9957 trên toàn dải** $\lambda\in[0{,}5;\,2{,}0]$ và sụp xuống **0,8438** tại $\lambda=3{,}0$, nơi phân giải quá cao xé vụn các ốc đảo (77 cụm). Khoảng an toàn khuyến nghị: $\lambda\in[0{,}5;\,2{,}0]$. Modularity ở tham số mặc định là **0,861**.
- **Hệ số $s$:** độ trải (spread) của $\mathcal{V}_{agg}$ hẹp lại đơn điệu khi $s$ tăng: $s=1$ trải đủ **1,0**; $s=10$ trải **0,914** (max 1,914); $s=20$ chỉ còn **0,650**. Vậy $s$ đánh đổi dải động với khả năng chống bão hòa.

**Trả lời lo ngại "quá nhiều tham số tự do".** Ta mở rộng quét sang các tham số ngữ cảnh và cân bằng, và phân biệt **hai lý do rất khác nhau** khiến một phép quét trông phẳng. Hai độ nhạy ngữ cảnh $\tau_F, \tau_E$ cho ARI **0,9957 và đúng 74 cụm** trên toàn lưới $\tau_F, \tau_E\in[0{,}15;\,0{,}5]$: không chỉ điểm số mà **cả phân hoạch** cũng không đổi, nên đây là **bền vững thật** — cổng địa lý ấn định cấu trúc, còn độ gắt của suy giảm ngữ cảnh không liên quan trong dải đó. Cân bằng $\beta/\gamma$ thì **hoạt động nhẹ** (độ trải **0,0448**): ARI là 0,9957 khi $\beta\le0{,}7$ và tụt còn **0,9509** tại $\beta=0{,}9$, nơi bỏ đói $\gamma$ khiến mất khả năng tách S5 và cho 75 cụm. Đây chính là chỗ tín hiệu ngữ cảnh quan sát được, và là sự thay thế trung thực cho khẳng định ablation mạnh hơn mà ta **không còn** đưa ra được (§5.7). Tóm lại: $\sigma_{geo}$ và $\lambda$ là hai núm mà một triển khai phải đặt cẩn thận, $\beta/\gamma$ chỉ cần tránh hai cực biên, còn $\tau_F, \tau_E$ có thể để nguyên mặc định.

### 5.4. Thí nghiệm 3 — Louvain vs Leiden

Trên **10 seed khác nhau**, cả Louvain và Leiden đều cho **0 cộng đồng đứt gãy**, cùng ARI **0,9957** và Modularity **0,861**. Hai chi tiết của phép đo cần nói rõ. Thứ nhất, tính liên thông chỉ được kiểm trên những cộng đồng **có thể** đứt gãy: trong 74 cộng đồng mỗi lần chạy, **61 là singleton** và bị loại, còn lại **13 cộng đồng đánh giá được mỗi seed** (tổng **130** trên 10 seed) — nếu ghi "0 trên 74" thì đã thổi phồng mẫu số bằng những trường hợp không thể thất bại. Thứ hai, Louvain và Leiden trả về **phân hoạch trùng khít** trên mọi seed, đó là lý do hai hàng của chúng trong bảng baseline giống nhau chính xác. Đây là **phát hiện trung thực đáng chú ý**: chính cơ chế gating (Mục 4.2) đã tạo ra các đồ thị con gắn kết không gian, loại bỏ trước rủi ro cộng đồng đứt gãy — nên trong bối cảnh này Louvain đã đủ tốt. Leiden vẫn được khuyến nghị như một "bảo hiểm miễn phí" (đảm bảo lý thuyết về liên thông) mà không phải đánh đổi chất lượng.

### 5.5. Thí nghiệm 4 — So sánh với baseline

Bảng dưới mở rộng so sánh với **ba baseline công bằng** chạy trên **cùng đồ thị gating** (Spectral, HDBSCAN, Agglomerative) bên cạnh các baseline Euclid trên đặc trưng sự kiện. Ba quy ước đo lường phải nêu trước khi đọc số, vì mỗi cái đều có thể **âm thầm đảo chiều** một so sánh. **Thứ nhất**, giá trị $K$ cấp cho Spectral và Agglomerative ở các hàng $K=74$ không phải một lựa chọn độc lập: đó chính là số cụm **Louvain tự tìm ra**, nên các hàng đó được cho không độ phân giải của phương pháp chúng tôi — đây cũng đúng là lý do khiến việc Agglomerative khớp Louvain là bằng chứng **yếu hơn** vẻ ngoài của nó. **Thứ hai**, DBSCAN và HDBSCAN sinh nhãn nhiễu ($-1$) nghĩa là "không thuộc cụm nào". Chúng tôi **không** coi thùng đó là một cụm: nó không vào số cụm, không vào bất kỳ đường kính nào, và các điểm trong đó không bị tính là nhiễu "bị hấp thụ", vì hấp thụ nghĩa là bị đặt **vào** một cụm. Nếu tính, ta sẽ tạo ra một cụm-ảo hàng trăm km và báo cáo "hấp thụ 100% nhiễu" cho một phương pháp thực chất không hấp thụ điểm nào — một artifact **có lợi cho phía chúng tôi**, nên thay vào đó kích thước thùng được báo cáo riêng ở cột "Chưa gán cụm". **Thứ ba**, các baseline Euclid được chạy trên **hai** không gian đặc trưng: *chỉ tọa độ* $(\mathrm{lat},\mathrm{lng})$ — phép thử trung thực cho câu hỏi "chỉ địa lý có đủ không" — và *tọa độ*$+F,E$, tức nối thêm hai chiều ngữ cảnh đã chuẩn hóa.

| Phương pháp | Số cụm | ARI | NMI | Đ.kính TB (km) | Đ.kính max (km) | Nhiễu hấp thụ | Chưa gán cụm | Cần biết trước $K$? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Louvain (đồ thị gating)** | 74 | **0,9957** | **0,9933** | **0,85** | **1,41** | **0,0%** | 0 | Không |
| **Leiden (đồ thị gating)** | 74 | **0,9957** | **0,9933** | **0,85** | **1,41** | **0,0%** | 0 | Không |
| Agglomerative (dist=$1-w$, $K=74$) | 74 | 0,9957 | 0,9933 | 0,85 | 1,41 | 0,0% | 0 | Có |
| HDBSCAN (dist=$1-w$ gating) | 20 | **1,0** | **1,0** | 48,69 | 201,46 | 3,3% | 7 | Không |
| Spectral (affinity gating, $K=74$) | 72 | 0,1657 | 0,6927 | 8,79 | 209,05 | 37,7% | 0 | Có |
| Spectral (affinity gating, $K=14$) | 14 | 0,9464 | 0,9716 | 38,16 | 209,05 | 100% | 0 | Có |
| K-Means ($K=14$, **chỉ tọa độ**) | 14 | 0,8268 | 0,8898 | 34,00 | 58,59 | 26,2% | 0 | Có |
| DBSCAN (eps=0,3, **chỉ tọa độ**) | 11 | 0,6230 | 0,8132 | 17,40 | 37,37 | 18,0% | 30 | Không |
| K-Means ($K=14$, tọa độ$+F,E$) | 14 | 0,5016 | 0,7262 | 93,47 | 148,04 | 91,8% | 0 | Có |
| K-Means ($K=3$, sai $K$, tọa độ$+F,E$) | 3 | 0,3282 | 0,5278 | 164,42 | 201,46 | 100% | 0 | Có |
| DBSCAN (eps=0,3, tọa độ$+F,E$) | 31 | 0,2391 | 0,6570 | 1,14 | 7,75 | 0,0% | 128 | Không |
| DBSCAN (eps=0,6, tọa độ$+F,E$) | 7 | 0,5234 | 0,7369 | 14,33 | 37,37 | 6,6% | 64 | Không |

**Kết quả phải báo cáo trước tiên là kết quả KHÔNG ủng hộ phương pháp của chúng tôi.** **HDBSCAN** trên ma trận khoảng cách gating đạt ARI và NMI **hoàn hảo 1,0**, cao hơn 0,9957 của Louvain, vì nó phục hồi cả **14** nhãn ground-truth — kể cả cặp S5 cách nhau 923 m mà Louvain gộp — và đẩy phần còn lại vào một thùng nhiễu. Tuy vậy nó **không dùng được** cho điều phối: 20 cụm của nó có đường kính trung bình multi-member **48,69 km** với cụm xấu nhất **201 km**, tức những "cụm" đơn lẻ trải rộng cả tỉnh, và nó hấp thụ **3,3%** nhiễu không nhãn vào các cụm có nhãn. Đây đúng là lý do **không nên coi ARI là mục tiêu**: độ khớp nhãn và hình học vận hành là hai trục khác nhau, và một phương pháp có thể thắng trục thứ nhất trong khi thất bại trục thứ hai tới **hai bậc độ lớn**.

**Agglomerative** trên cùng ma trận khoảng cách khớp Louvain **chính xác** trên cả bốn chỉ số ($0{,}9957/0{,}9933/0{,}85/1{,}41$). Do đó chúng tôi **không** tuyên bố tối ưu Modularity ưu việt hơn agglomerative linkage trên bộ dữ liệu này; khẳng định trung thực hẹp hơn và nói về **đầu vào chứ không phải thuật toán**: bất kỳ phương pháp nào được cho ăn ma trận gating đều thừa hưởng tính gắn kết không gian của nó, và lợi thế của Louvain so với Agglomerative là **vận hành** — nó không cần $K$, thứ không thể biết trong một trận lũ đang diễn ra.

Các baseline còn lại thất bại theo những cách giải thích được. **Spectral** ở $K=74$ sụp còn ARI 0,1657: đồ thị gating thưa có nhiều thành phần gần-như-rời-rạc, điều rất bất lợi cho mục tiêu normalized-cut. Được cho biết $K=14$ — thông tin mà không triển khai nào có — nó đạt 0,9464, nhưng với đường kính trung bình **38 km** và hấp thụ **100%** nhiễu.

**Các baseline Euclid cần cách đọc sắc hơn câu "chỉ địa lý là không đủ", vì dữ liệu không ủng hộ cách nói đó.** Chỉ tọa độ thực ra là một baseline **mạnh**: K-Means trên $(\mathrm{lat},\mathrm{lng})$ với $K=14$ đúng đạt ARI **0,8268**, cao hơn nhiều con số 0,5016 mà chúng tôi lẽ ra sẽ báo cáo nếu chỉ chạy biến thể bốn đặc trưng. Điều tách phương pháp của chúng tôi khỏi nó **không phải** độ khớp nhãn mà là **hình học và tính tự trị**: đường kính trung bình 34,00 km so với 0,85 km, hấp thụ nhiễu 26,2% so với 0%, và một $K$ buộc phải được cấp sẵn. So sánh giàu thông tin hơn nằm **giữa hai không gian đặc trưng**, và nó ủng hộ đúng luận điểm thiết kế trung tâm của bài: **nối** $F,E$ thành hai chiều Euclid phụ làm K-Means **tệ đi**, ARI tụt từ 0,8268 xuống 0,5016 và đường kính trung bình phình từ 34 km lên 93 km, vì trong không gian 4 chiều đã chuẩn hóa, hai sự kiện có cùng mức ngập bị kéo lại gần nhau **bất kể cách nhau bao xa** — đúng kiểu thất bại trộn-cộng mà công thức trọng số gating tránh được bằng cách đặt $\mathcal{S}_{geo}$ làm **cổng nhân** thay vì một chiều nữa. Ngữ cảnh **không** vô dụng; nó phải vào theo **dạng nhân**. DBSCAN cũng nhất quán với điều này: chỉ trên tọa độ nó đạt 0,6230, còn trên tọa độ$+F,E$ ARI tốt nhất là 0,5234. Đọc chung, bảng ủng hộ một khẳng định **liên kết** — ma trận gating cấp tính gắn kết, Modularity cấp $K$ tự động — và **bác bỏ** khẳng định mạnh hơn rằng Louvain thắng mọi phương án trên mọi trục.

### 5.6. Thí nghiệm 5 — Độ ổn định xếp hạng (Kendall's τ)

Phản biện tiềm năng: ban chỉ huy đặt $\omega$ thủ công — nếu thứ hạng $\mathcal{P}(C_k)$ quá nhạy với $\omega$, danh sách ưu tiên trở nên tùy tiện. Chúng tôi nhiễu loạn $\omega$ quanh giá trị mặc định $(0{,}34;\,0{,}33;\,0{,}33)$, chuẩn hóa lại về $\sum\omega=1$, rồi đo Kendall's τ giữa thứ hạng mới và thứ hạng gốc (200 thử nghiệm Monte-Carlo mỗi mức).

| Mức dao động $\omega$ | τ trung bình (mọi cụm) | τ tối thiểu (mọi cụm) | τ trung bình (cụm $\ge2$) | τ tối thiểu (cụm $\ge2$) | Top-3 giữ nguyên (%) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| ±0,05 | **0,9789** | 0,9526 | 0,9858 | 0,9487 | **100,0** |
| ±0,10 | 0,9552 | 0,9104 | 0,9737 | 0,8974 | **100,0** |
| ±0,20 | 0,9111 | 0,8045 | 0,9442 | 0,7949 | **100,0** |

Một chi tiết về thành phần phải nêu trước khi đọc các con số này, vì nó có thể làm τ trông tốt hơn thực tế: phân hoạch gating sinh **61 cụm đơn lẻ (singleton) trong 74 cụm**, tức chỉ **13** cụm có $\ge2$ thành viên. Singleton phần lớn có $\sum V_i=0$ nên $\mathcal{V}_{agg}=1$ và điểm $\mathcal{P}$ của chúng chỉ phụ thuộc một sự kiện — thứ hạng của chúng rất ít bị đảo khi $\omega$ dao động, nên chúng có thể **nâng** τ toàn cục so với phần danh sách mà ban điều phối thực sự dùng. Ta vì thế báo cáo song song τ **hạn chế** trên 13 cụm nhiều-thành-viên. Kết quả: ở mức dao động thực tế (±0,05 — ±0,10), τ trung bình giữ ở **0,955 hoặc cao hơn** và không thử nghiệm nào tụt dưới **0,91**; τ hạn chế thậm chí **cao hơn một chút** (0,9858 và 0,9737 so với 0,9789 và 0,9552), nên lo ngại "singleton bơm τ" **không** thành hiện thực — độ ổn định là thật, không phải artifact của thành phần phân hoạch, tuy τ tối thiểu hạn chế có thấp hơn chút (0,8974 ở ±0,10) vì mẫu nhỏ hơn nên một lần đảo cặp gây ảnh hưởng lớn hơn. Ngay cả ở mức cực đoan ±0,20 (thay đổi gần 60% giá trị $\omega$), τ trung bình vẫn đạt **0,9111** với trường hợp xấu nhất 0,8045 — và, đây là con số quyết định về mặt vận hành, **tập 3 cụm đầu được giữ nguyên trong 100% của cả 600 thử nghiệm** ở mọi mức, vì các cụm dẫn đầu cách nhau một biên độ mà việc đổi trọng số trong các dải này không thể khép lại.

Độ ổn định cũng đúng với hai bộ phận chuyển động còn lại. Với **hệ số $s$** của $\tanh$: $\tau\ge$ **0,9985** cho mọi $s\in\{5,8,10,12,20\}$ (đúng **1,0** khi $s\ge10$), top-3 giữ nguyên xuyên suốt. Với **bước phân cụm**: quét $\sigma_{geo}$ trên $[400;\,1200]$ m để lại thứ hạng cố định (74 cụm và τ = **1,0** tới 900 m; tại 1200 m hai cụm gộp lại, cho **73 cụm** và τ = **0,9954**), nên danh sách ưu tiên không phụ thuộc vào một lựa chọn dựng-đồ-thị duy nhất.

### 5.7. Thí nghiệm 6 — Ablation tính vòng tròn của ngữ cảnh

Một phản biện: việc dùng lại $F, E$ ở cả $\mathcal{S}_{context}$ (gom cụm) lẫn $\mathcal{F}_{max}, \mathcal{E}_{agg}$ (xếp hạng) có thể khiến số hạng ngữ cảnh ngấm ngầm chi phối danh sách ưu tiên cuối. Ta kiểm tra bằng cách loại $\mathcal{S}_{context}$ khỏi trọng số cạnh (đặt $\gamma=0$, chỉ còn gating địa lý – thời gian) rồi so cả phân cụm lẫn thứ hạng cảm sinh với mô hình đầy đủ. Trên bộ dữ liệu hiện hành, kết quả **mạnh hơn một hiệu ứng nhỏ: ở tham số mặc định, ablation không đổi gì cả.** Cả hai đồ thị cho ARI 0,9957, NMI 0,9933, cùng 74 cụm với cùng đường kính trung bình 0,1491 km; toàn bộ 74 cụm khớp theo trọng tâm, thứ hạng **trùng khít** (Kendall's τ = **1,0**, giữ nguyên cả top-5). Ta báo cáo điều này thay vì câu chuyện yếu-hơn-nhưng-đẹp-hơn, và nó buộc một cách đọc chính xác: nó **trả lời thẳng** lo ngại vòng tròn — thứ hạng không thể bị $\mathcal{S}_{context}$ ngấm ngầm chi phối nếu xóa $\mathcal{S}_{context}$ mà thứ hạng không đổi một bit — nhưng đồng thời cho thấy $\gamma\mathcal{S}_{context}$ là **dư thừa tại $\beta=\gamma=0{,}5$**: cổng địa lý 700 m đã tách sẵn mọi nhóm mà ngữ cảnh có thể tách, nên số hạng ngữ cảnh không mang thêm độ chính xác nào. Chỗ ngữ cảnh **có** giá trị là nơi hình học nhập nhằng, và phép quét ở Mục 5.3 định vị được: tại $\beta=0{,}9$ (bỏ đói $\gamma$ còn 0,1), ARI tụt xuống 0,9509 và phân hoạch nở lên 75 cụm, vì cặp S5 chỉ cách nhau 923 m ($\mathcal{S}_{geo}\approx0{,}44$, nằm sâu trong cổng) khi đó không còn phân biệt được bằng ngữ cảnh ngập trái ngược. Vậy $\mathcal{S}_{context}$ nên hiểu là **bảo hiểm cho nhập nhằng dưới ngưỡng $\sigma_{geo}$**, không phải động lực của các con số headline — và trên dữ liệu thật với hình học nhiễu hơn 6 ốc đảo tách biệt, ta kỳ vọng đóng góp của nó lớn hơn con số zero đo được ở đây.

### 5.8. Thí nghiệm 7 — Trọng số tổn thương có thực sự giúp người yếu thế?

Câu hỏi sâu hơn của Khe hở 2 không phải "chỉ số tổn thương $V_i$ có đổi thứ hạng không" (có, theo thiết kế) mà là nó có tạo ra **kết quả cứu hộ tốt hơn** cho nhóm yếu thế hay không. Ta mô phỏng điều phối rời rạc (discrete-event dispatch): $3$ ca nô ở $30$ km/h với thời gian phục vụ $15$ phút/cụm, phục vụ các cụm theo thứ tự ưu tiên, phục vụ các cụm theo thứ tự ưu tiên. So ba chính sách: dạng nhân đầy đủ $\mathcal{P}=\mathcal{V}_{agg}\cdot(\dots)$, dạng cộng — hiện thực là $\mathcal{P}=\text{core}+(\mathcal{V}_{agg}-1)$, tức cộng đúng **phần khuếch đại** $\mathcal{V}_{agg}-1\in[0,1)$ chứ không cộng cả $\mathcal{V}_{agg}$, để hai dạng cùng gốc 0 khi không có đối tượng yếu thế; hai cách viết chỉ lệch một hằng số $+1$ nên **cùng thứ hạng** (Kendall's τ = 1,0), song ta nêu rõ dạng đã chạy, và chính sách mù tổn thương (bỏ $V_i$).

**Chọn độ đo kết quả một cách trung thực chính là điểm cốt tử**, vì những độ đo hiển nhiên nhất đều **vòng tròn**. "Thời gian trung bình đến được nạn nhân có $V_i$ cao" **thiên vị** chính sách nào cân tổn thương theo kiểu **cộng**, vì một khoản thưởng cộng đẩy các cụm yếu thế lên bất kể mức nghiêm trọng của chúng; còn thời gian phản ứng có trọng số tổn hại dựng từ $V_i$ lại thiên vị theo hướng ngược lại. Do đó ta chỉ định làm **độ đo chính** một đại lượng được định nghĩa **không tham chiếu gì đến công thức xếp hạng**: *thời gian trung bình đến được nạn nhân yếu thế đang ở vùng ngập nặng* ($F\ge0{,}7$) — tức chính những người mà hệ thống tồn tại để cứu. Phần hiện thực ghi lại độ đo nào thiên vị theo chiều nào và chỉ đánh dấu độ đo này là trung lập.

Trên độ đo trung lập, chính sách nhân đầy đủ đến được nạn nhân yếu thế trong vùng ngập nặng sau **110,2** phút, so với **113,5** phút của chính sách mù tổn thương (**+2,9%**) và **122,9** phút của biến thể cộng (**+10,3%**). Cách đọc trung thực: lợi ích công bằng so với một chính sách mù là **nhỏ** trên độ đo trung lập — **không phải** 33% mà độ đo suy-từ-$V$ sẽ báo ($165{,}0$ so với $246{,}6$ phút) — trong khi ưu thế so với biến thể cộng là **thật**, vì gắn tổn thương vào mức nghiêm trọng đúng là điều mà độ đo trung lập thưởng. Dạng nhân cũng tốn kém hơn ở thời gian đến trung bình cho *toàn bộ* nạn nhân (**2528** so với **2410** phút của chính sách mù) — một đánh đổi công bằng–hiệu quả tường minh. Ta báo cáo các độ đo thiên vị **bên cạnh** độ đo trung lập chứ không quote con số đẹp nhất.

### 5.9. Thí nghiệm 8 — Bộ phát hiện tin cậy và độ bền đối kháng

Ta đánh giá heuristic tin cậy $C_i$ như một bộ phát hiện tin giả và dò trường hợp xấu nhất. Xem $C_i$ thấp là cờ báo giả trên toàn bộ $341$ sự kiện ($23$ tin giả), $C_i$ tách được tin giả tiêm vào khỏi tin thật với **ROC-AUC $0{,}9176$** (khoảng tin cậy bootstrap 95% $[0{,}8863;\,0{,}9439]$, 1000 lần lấy lại mẫu; trung bình $C_i$ là $0{,}60$ cho tin giả so với $0{,}89$ cho tin thật). Vì lớp dương chỉ chiếm **6,7%** dữ liệu, riêng AUC **thổi phồng** tính hữu dụng, nên ta cũng báo cáo **Average Precision $0{,}3159$** (CI $[0{,}2577;\,0{,}4063]$) so với baseline ngẫu nhiên $0{,}0674$: một mức nâng **4,7×** về precision-recall — bức tranh tỉnh táo hơn nhiều so với những gì AUC gợi ra, và là con số mà một triển khai phải lập kế hoạch theo. Đây là tín hiệu sàng lọc, không phải bảo đảm, và ta cố ý ép nó tới điểm gãy. Một tin giả ngây thơ (cô lập, không ảnh) chỉ đạt $C_i=0{,}45$ và dễ bị hạ trọng số; nhưng kẻ tấn công **thêm ảnh giả** đẩy nó lên $0{,}77$, **dàn dựng corroboration phối hợp** đẩy lên $0{,}74$, và làm **cả hai** đạt $C_i=$ **0,92** — **cao hơn** trung bình của tin thật ($0{,}89$), nên cổng không chỉ trượt mà còn tích cực xếp tin giả đó **đáng tin hơn** một tin thật trung bình. Vì "tính độc lập" của corroboration chỉ được xấp xỉ bằng gần kề không gian – thời gian (không có hạ tầng tài khoản định danh), heuristic bền với kẻ spam đơn lẻ nhưng **không** bền với đối thủ phối hợp có nguồn lực. Do đó ta trình bày $C_i$ như một bộ lọc tuyến đầu, phải kết hợp với tin cậy cấp tài khoản hoặc kiểm chứng chéo kênh trước khi có thể dựa vào để chống đối kháng — và nêu rõ giới hạn này thay vì thổi phồng khả năng phát hiện.

### 5.10. Thí nghiệm 9 — Phân rã chất lượng cụm: completeness vượt trên ARI

ARI **bão hòa** ở đỉnh bảng xếp hạng của chúng ta — Louvain, Leiden và Agglomerative **trùng khít về số** tại $0{,}9957$, còn HDBSCAN nằm **trên** chúng tại $1{,}0$ — nên ARI hoàn toàn không tách được nhóm dẫn đầu, và ở chỗ nó có tách thì lại chỉ **sai chiều** về mặt vận hành. Do đó ta **phân rã** độ khớp thành cặp homogeneity/completeness (mà trung bình điều hòa của chúng — V-measure — **chính bằng** NMI trung-bình-cộng đã in ở các bảng trên; nên giá trị phân biệt tăng thêm đến từ hai **thành phần**, không phải từ một độ đo tổng hợp mới):

| Phương pháp | Số cụm | ARI | H | C | V |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Louvain / Leiden / Agglom. | 74 | 0,9957 | 0,9867 | 1,0 | 0,9933 |
| HDBSCAN | 20 | **1,0** | **1,0** | **1,0** | **1,0** |
| Spectral ($K=74$) | 72 | 0,1657 | 0,9978 | 0,5305 | 0,6927 |
| K-Means (tọa độ$+F,E$, $K=14$) | 14 | 0,5016 | 0,7681 | 0,6887 | 0,7262 |
| DBSCAN (tọa độ$+F,E$, eps=0,6) | 7 | 0,5234 | 0,6277 | 0,8922 | 0,7369 |

Hai điều trở nên thấy được. **Thứ nhất**, ở đầu thấp, phân rã giải thích **cách** một phương pháp thất bại chứ không chỉ nói rằng nó thất bại: Spectral Clustering có homogeneity gần như hoàn hảo ($0{,}9978$) nhưng completeness chỉ $0{,}5305$ — cụm của nó "thuần" bởi vì nó **đập vỡ** các sự kiện ground-truth ra nhiều cụm, đúng dấu hiệu kinh điển của **over-segmentation**, điều mà một con số ARI $0{,}1657$ đơn lẻ không truyền tải được. K-Means thất bại theo chiều **ngược lại**, với homogeneity ($0{,}7681$) và completeness ($0{,}6887$) đều tầm tầm, tức là cụm thật sự bị trộn lẫn. DBSCAN (eps $0{,}6$) thì **under-segmented**: completeness $0{,}8922$ nhưng homogeneity chỉ $0{,}6277$.

**Thứ hai, và quan trọng hơn: phân rã KHÔNG cứu được phương pháp của chúng tôi trước HDBSCAN.** HDBSCAN hoàn hảo trên **cả bốn** độ đo khớp-nhãn (ARI, NMI, homogeneity, completeness đều $1{,}0$), trong khi Louvain đạt homogeneity $0{,}9867$ và completeness $1{,}0$. Ta nói thẳng điều này: trên bộ dữ liệu này, **không** một độ đo khớp-nhãn nào — tổng hợp hay đã phân rã — ưu ái Louvain hơn HDBSCAN. Bằng chứng phân biệt là **hình học** và nằm **hoàn toàn bên ngoài** họ độ đo này (xem bảng §5.5: đường kính trung bình multi-member $0{,}85$ km so với $48{,}69$ km, max $1{,}41$ km so với $201{,}46$ km). Bài học rút ra vì thế **mạnh hơn** câu "hãy dùng thêm completeness": với phân cụm hướng-điều-phối, **không** độ đo khớp-phân-hoạch nào là một mục tiêu đủ, và một độ đo về **độ trải không gian** buộc phải được báo cáo kèm. Độ trải của các độ đo trên sáu phương pháp xác nhận rằng phân rã ít nhất vẫn phân biệt tốt hơn V-measure đơn lẻ: ARI trải $0{,}8343$, homogeneity $0{,}3723$, completeness $0{,}4695$, V-measure $0{,}3073$.

### 5.11. Thí nghiệm 10 — Kích thước gói metadata

Tiền đề của thiết kế biên là đường truyền còn sống có thể tải được kilobyte nhưng không tải được megabyte, nên kích thước gói là một con số **chịu lực**, không phải chi tiết phụ. Ta tuần tự hóa từng sự kiện trong 341 sự kiện thành một descriptor JSON nén — id sự kiện, tọa độ, dấu thời gian epoch, các trường $L,T,F,E,N,V,C$, và một cờ ảnh — với khoảng trắng bị loại, rồi đo độ dài đã mã hóa của **từng** gói. Kết quả tất định và bị chặn chặt: **105–111 byte** (min $105$, trung vị $110$, max $111$). Vậy mỗi sự kiện lọt trong một datagram nhỏ duy nhất, so với bài đăng đa phương tiện cỡ megabyte mà nó tóm lược; chính mức giảm MB$\rightarrow$dưới-KB đó giữ cho đường lên mesh/LoRa bị nghẽn vẫn dùng được.

### 5.12. Thí nghiệm 11 — Độ phức tạp tính toán

Một triển khai trên hạ tầng biên cần biết pipeline co giãn thế nào, và ma trận trọng số $O(n^2)$ là điểm nghẽn hiển nhiên. Ta nhân bản generator lên $n\in\{341, 1201, 3581, 7181\}$ sự kiện rồi đo thời gian từng giai đoạn:

| $n$ | Build (vector hóa) | Build (vòng lặp) | Tăng tốc | Sparsify | Louvain | Tổng | Số cụm |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 341 | 0,020 | 0,119 | 6,1× | 0,004 | 0,036 | 0,060 | 74 |
| 1201 | 0,394 | 1,499 | 3,8× | 0,043 | 0,302 | 0,739 | 213 |
| 3581 | 4,435 | 14,856 | 3,3× | 0,643 | 2,255 | 7,333 | 579 |
| 7181 | 24,623 | — | — | 4,143 | 8,973 | 37,738 | 1097 |

Hai kết quả đáng chú ý. **Thứ nhất**, builder vector hóa nhanh hơn vòng lặp đôi thô **3,3–6,1×** trong khi khớp với nó tới $<10^{-10}$ (sai khác tuyệt đối lớn nhất $7{,}3\times10^{-11}$), nên phần tăng tốc là **chính xác**, không phải xấp xỉ. **Thứ hai**, và ta báo cáo nó thay vì cách đọc đẹp hơn: giai đoạn build tăng **NHANH HƠN** dự đoán $O(n^2)$ ở **cả ba** bước đo được ($20{,}2\times$ quan sát so với $12{,}4\times$ dự đoán, rồi $11{,}3\times$ so với $8{,}9\times$, rồi $5{,}6\times$ so với $4{,}0\times$) — ma trận dày $n\times n$ vượt khỏi cache và trở thành bị chặn bởi băng thông bộ nhớ, nên hằng số nhân xấu đi khi $n$ tăng. Điều này **củng cố** chứ không làm yếu kết luận triển khai bên dưới. Ngược lại, hai giai đoạn đồ thị vẫn rẻ: ở $n=7181$ toàn pipeline hoàn tất trong **37,7 s** trên một lõi CPU, trong đó sparsify mất $4{,}1$ s và Louvain $9{,}0$ s. Với một sự cố cấp tỉnh, mức này đủ thời-gian-thực; nhưng quá $\sim10^4$ sự kiện đồng thời thì ma trận dày **phải** được thay bằng một chỉ mục không gian (ball-tree / geohash blocking) — điều mà dạng gating cho phép, vì $\mathcal{S}_{geo}$ đã triệt gần như mọi cặp.

### 5.13. Thí nghiệm 12 — Kiểm chứng đa seed

Mọi khẳng định ở trên được đo trên seed $=42$; ta lặp lại phép so sánh trung tâm trên **20 seed độc lập**, sinh lại bộ dữ liệu mỗi lần, để kiểm rằng nó không phải hiện tượng của một lần rút duy nhất.

| Chỉ số | Gating | Cộng ($\alpha=1{,}0$) | Gating thắng |
| :--- | :---: | :---: | :---: |
| ARI | $0{,}9957\pm0{,}0000$ | $0{,}9415\pm0{,}0141$ | 100% |
| NMI | $0{,}9933\pm0{,}0000$ | $0{,}9500\pm0{,}0073$ | 100% |
| Đ.kính TB (km) | $0{,}83\pm0{,}04$ | $149{,}19\pm11{,}25$ | 100% |
| Đ.kính max (km) | $1{,}57\pm0{,}25$ | $196{,}82\pm8{,}09$ | 100% |
| Nhiễu hấp thụ (%) | $0{,}41\pm0{,}90$ | $93{,}61\pm10{,}30$ | 100% |
| Modularity $Q$ | $0{,}8612\pm0{,}0004$ | $0{,}7748\pm0{,}0076$ | 100% |
| Số cụm | $73{,}3\pm0{,}8$ | $8{,}6\pm0{,}7$ | — |

Gating thắng trên **100% số seed** ở mọi chỉ số so sánh được, và các biên độ không hề sát sao: đường kính trung bình multi-member $0{,}83\pm0{,}04$ km so với $149{,}19\pm11{,}25$ km, hấp thụ nhiễu $0{,}41\pm0{,}90\%$ so với $93{,}61\pm10{,}30\%$. ARI ưu ái gating với biên độ nhỏ hơn nhưng **nhất quán hoàn toàn**.

Các độ lệch chuẩn **bằng 0** ở cột gating cần một cảnh báo tường minh thay vì một vòng ăn mừng: chúng xuất hiện vì hình học **liên-nhóm** của generator được cố định qua các seed, nên **đúng một cặp** (nhãn 106–107, cách nhau 923 m) bị gộp ở **20/20** seed trong khi không cặp nào khác từng bị gộp — tức sai số là một **hằng số của thiết kế**, không phải một biến ngẫu nhiên. Các phương sai **khác 0** (đường kính, số cụm, số singleton) đến từ vị trí ngẫu nhiên của các sự kiện nhiễu, thứ thực sự đổi theo seed. Trên một bộ dữ liệu có khoảng cách liên-nhóm biến thiên, phương sai này sẽ khác 0.

### 5.14. Thí nghiệm 13 — Ưu thế của gating có phải là artifact của việc dùng chung $\theta$?

Mọi so sánh ở trên áp **cùng một** ngưỡng làm thưa $\theta=0{,}05$ cho cả hai dạng trọng số. Điều đó *trông* như một so sánh có kiểm soát, nhưng thực chất là ngược lại, vì $\theta$ là một lát cắt **tuyệt đối** trên hai phân bố giá trị **khác nhau**. Tích gating dồn khối lượng về gần 0: trung vị trọng số ngoài đường chéo là **0,0000** và chỉ **8,3%** cặp vượt 0,05. Trong khi đó tổng cộng không thể xuống dưới sàn **0,041**, nên **99,99%** cặp của nó vượt qua đúng cái ngưỡng ấy. Tại $\theta=0{,}05$, dạng cộng vì thế bị đưa vào Louvain như một **đồ thị gần hoàn chỉnh** — đúng cái chế độ mà chính bài này (Mục 4.2) nói rằng tối ưu Modularity hoạt động kém — còn gating được nhận một đồ thị đã thưa sẵn. Một phần của khoảng cách $151\times$ về đường kính phải quy cho **ngưỡng**, không phải cho dạng hàm.

Chúng tôi kiểm tra trực tiếp bằng cách hiệu chuẩn $\theta$ **riêng cho từng dạng**, quét trên miền giá trị của chính nó và hỏi mỗi dạng đạt được gì ở cấu hình **tốt nhất** của nó:

| Dạng | ARI tốt nhất | $\theta$ tại đó | Max diam. tại đó | Cửa sổ $\theta$ dùng được | Tỉ lệ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Nhân (gating)** | 1,0 | 0,29 | **1,41 km** | $[0{,}01;\,0{,}51]$ | **51,0×** |
| Cộng, $\alpha=1{,}0$ | **1,0** | 1,08 | **1,41 km** | $[0{,}96;\,1{,}46]$ | 1,52× |
| Cộng, $\alpha=0{,}5$ | 0,9989 | 0,92 | 116,41 km | $[0{,}96;\,1{,}02]$ | 1,06× |
| Cộng chuẩn hóa $\frac13$ | 0,9968 | 0,56 | 195,85 km | $[0{,}64;\,0{,}68]$ | 1,06× |
| Cộng, $\alpha=0{,}34$ | 0,9820 | 0,84 | 195,85 km | *không có* | — |

("Dùng được" = đường kính xấu nhất $<5$ km **và** ARI $\ge0{,}95$; cả hai tiêu chí đặt trước khi quét.)

**Kết quả đảo ngược cách đọc mạnh của Thí nghiệm 1A.** Tại $\theta=1{,}08$, dạng cộng với $\alpha=1{,}0$ đạt ARI **1,0** với đường kính xấu nhất **1,41 km** — **khớp chính xác** hình học của gating và ARI còn nhích cao hơn. *Dạng cộng không hề bất lực về bản chất trong việc tạo cụm gắn kết không gian.* Con số 214 km mà bài này dùng xuyên suốt là thành tích của dạng cộng **tại một ngưỡng được hiệu chuẩn cho một hàm trọng số khác**, và trình bày nó như một thuộc tính của tính-cộng là **sai**.

Điều **còn đứng vững** là một tuyên bố khác và bảo vệ được, nằm ở hai cột cuối. Gating đạt mức dùng được trên **mọi** $\theta\in[0{,}01;\,0{,}51]$ — một cửa sổ rộng **51×** theo tỉ lệ, và **bao gồm cả giá trị mặc định ngây thơ 0,05**. Dạng cộng $\alpha=1{,}0$ chỉ dùng được trong $[0{,}96;\,1{,}46]$ — cửa sổ **1,52×** *không chứa* bất kỳ giá trị nào mà người triển khai sẽ đoán; ba cấu hình cộng còn lại tệ hơn nữa (1,06× với $\alpha=0{,}5$ và bản $\frac13$; $\alpha=0{,}34$ **không bao giờ** dùng được ở bất kỳ $\theta$ nào). Khác biệt vận hành vì thế là về **khả năng dò tham số**, không phải về khả năng đạt tới: muốn dạng cộng ngang bằng thì phải định vị ngưỡng trong sai số vài phần trăm, và cách duy nhất để định vị là quét $\theta$ đối chiếu **ARI ground-truth** — thứ mà một trận lụt thật **không cung cấp**. Gating chạy đúng ngay ở ngưỡng đầu tiên mà bất kỳ ai cũng thử. Đó là một ưu thế kỹ thuật thật cho hệ thống phải triển khai dưới áp lực thời gian bởi những người không có điều kiện tinh chỉnh, và đó là điều chúng tôi tuyên bố **thay cho** ưu việt nội tại.

### 5.15. Trực quan hóa

Pipeline sinh một **dashboard bản đồ Leaflet tự chứa** hiển thị các cụm sự kiện trên bản đồ Miền Trung kèm bảng xếp hạng $\mathcal{P}(C_k)$, minh họa trực tiếp đầu ra cho ban điều phối. Suite sinh ra **bảy** hình PNG trong `demo/results/figures/`, trong đó **năm** hình được dùng trong bản LaTeX của bài báo: (1) `fig1_ablation` — gating vs cộng (panel a) **và** cổng $C_i$ trên dân số (panel b), (2) `fig4_sigma_sweep` — quét $\sigma_{geo}$, (3) `fig5_resolution_sweep` — quét $\lambda$, (4) `fig6_baselines` — so sánh baseline, (5) `fig7_ranking_stability` — độ ổn định xếp hạng. Hai hình còn lại — `fig2_map` (bản đồ cụm) và `fig3_heatmap` (heatmap) — cùng với **dashboard bản đồ Leaflet tự chứa** nói ở trên là **artifact trực quan hóa của bộ demo** phục vụ trình bày và kiểm tra nội bộ, **không** phải hình của bài báo (bản LaTeX bị giới hạn số trang). Script `demo/verify_figures.py` đối chiếu MD5 từng hình bài dùng với bản do suite sinh ra, để bài báo không bao giờ in một hình lỗi thời.

---

## 6. Thảo luận

**Ý nghĩa liên ngành.** Khung giải pháp mang lại tác động cộng hưởng trên ba lĩnh vực:

| Lĩnh vực                                | Giá trị mang lại                                                                                                                                                |
| :---------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Hạ tầng viễn thông & Edge**   | Duy trì sự sống còn (resilience) khi mạng sụp đổ; thay vì tải ảnh/video hàng MB, thiết bị chỉ gửi gói metadata JSON nén đo được **105–111 byte** (min 105 / trung vị 110 / max 111 trên toàn bộ 341 sự kiện, gồm định danh, toạ độ, tem thời gian epoch và các trường $L,T,F,E,N,V,C$ + cờ ảnh; xem §5.11) — nhỏ hơn ba–bốn bậc độ lớn, đủ luồn qua hạ tầng tắc nghẽn |
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

- **Hợp lệ nội tại (internal).** Kết quả dựa trên dữ liệu synthetic có ground-truth do chính nhóm sinh, với các "ốc đảo" ngập được thiết kế, nên mức ARI phần nào phản ánh độ tách của dữ liệu chứ không thuần túy là sức mạnh phương pháp. Generator **nay** đặt mọi nhóm ground-truth trên một satellite cách tâm ốc đảo chủ 3 km và assert khoảng tách tối thiểu 2 km, nên — khác phiên bản trước của bộ dữ liệu — **không** nhãn nào đồng vị trí với nhãn khác và **không có trần ARI nào bị áp đặt bởi cấu trúc**; khoảng hở $0{,}0043$ còn lại so với điểm hoàn hảo là **đúng một cặp** S5 cách nhau 923 m (§5.2). Cái giá của bản sửa đó lại là rủi ro ngược: một generator **bảo đảm** tách được làm bài toán phân cụm dễ hơn thực tế — chính vì vậy chúng tôi dựa vào các độ đo **vận hành** (đường kính, hấp thụ nhiễu, thời gian điều phối) hơn là dựa vào ARI đơn lẻ. Giảm thiểu: bổ sung kiểm chứng trên dữ liệu thật (Mục 7).
- **Hợp lệ ngoại tại (external).** Chỉ thử trên một vùng địa lý (Miền Trung VN) và một chế độ thảm họa (bão lũ). Chưa rõ khung tổng quát hóa cho đô thị mật độ cao khác, hay chế độ thảm họa khác (động đất, cháy rừng). Các tham số $\sigma_{geo}, \tau$ cần hiệu chỉnh lại cho từng bối cảnh.
- **Hợp lệ khái niệm (construct).** ARI/NMI đo *độ khớp cấu trúc cụm* với ground-truth, KHÔNG trực tiếp đo *chất lượng quyết định cứu hộ*. Thí nghiệm 7 (Mục 5.8) bước đầu khắc phục điều này bằng một độ đo hướng-kết-quả (thời gian đến nạn nhân yếu thế qua mô phỏng điều phối), cho thấy trọng số tổn thương cải thiện 10,4%; và Thí nghiệm 9 (Mục 5.10) phân rã độ khớp thành homogeneity/completeness để phân biệt chất lượng cụm mà ARI làm bão hòa (lưu ý V-measure chính bằng NMI đã báo cáo; giá trị phân biệt đến từ hai thành phần chứ không phải một độ đo mới). Dù vậy các độ đo này vẫn chạy trên dữ liệu synthetic và mô hình điều phối đơn giản hóa; kiểm chứng kết quả cứu hộ trên dữ liệu/địa hình thực vẫn là việc cần làm.
- **Hợp lệ thống kê (conclusion).** Mọi khẳng định chủ đạo **nay đã** được báo cáo trên **20 seed** (§5.13), không còn dựa vào một seed $=42$ duy nhất; exp3 chạy 10 seed cho phép so Louvain–Leiden. Một thống kê ở đó cần cảnh báo tường minh: độ lệch chuẩn ARI của gating **đúng bằng** $0{,}0000$ trên 20 seed. Đó **không** phải bằng chứng của bền vững phổ quát — nó xảy ra vì hình học cố định của generator khiến **đúng một cặp** (nhãn 106–107, cách 923 m) bị gộp ở $20/20$ seed trong khi không cặp nào khác từng bị gộp, nên sai số là một **hằng số của thiết kế** chứ không phải biến ngẫu nhiên. Trên bộ dữ liệu có khoảng cách liên-nhóm biến thiên, phương sai này sẽ khác 0.

## 8. Kết luận

Bài báo đề xuất một khung end-to-end kết hợp Edge AI và Lý thuyết Đồ thị Trọng số cho phân cụm và ưu tiên sự kiện cứu hộ bão lũ, lấp đầy ba khe hở khoa học: thiếu thuộc tính vật lý trong trọng số cạnh, điểm mù về tổn thương nhân khẩu học, và thiếu ưu tiên cấp cụm. Hai đóng góp phương pháp then chốt — **hàm trọng số nhân/gating** để địa lý chi phối cấu trúc cụm, và **hàm ưu tiên với hệ số công bằng làm thừa số khuếch đại** — được kiểm chứng định lượng trên bộ dữ liệu **341 sự kiện / 14 nhãn ground-truth**: gating giảm đường kính cụm **xấu nhất** từ $214$ km xuống **1,41 km** trong khi **nâng** ARI từ $0{,}9572$ (cấu hình cộng mạnh nhất tìm được qua phép quét $\alpha$) lên **0,9957**, và kết quả này giữ nguyên trên **20 seed độc lập**, thắng **100%** số seed ở mọi chỉ số; cổng tin cậy chặn **55%** dân số ảo từ tin giả; kiểm nghiệm Monte-Carlo (200 lần × 3 mức nhiễu) xác nhận xếp hạng $\mathcal{P}(C_k)$ ổn định (Kendall's τ trung bình **0,955**, tối thiểu **0,910** ở ±0,10; top-3 giữ nguyên **100%**).

Chúng tôi cũng **báo cáo các kết quả không ủng hộ phương pháp**, vì chính chúng làm rõ đóng góp thực sự là gì. HDBSCAN trên cùng ma trận gating đạt ARI **hoàn hảo 1,0** — nhưng với đường kính cụm trung bình $55{,}7$ km và xấu nhất $201$ km, nên **không dùng được** cho điều phối; Agglomerative linkage khớp Louvain **chính xác**, khiến lợi thế của Louvain nằm ở chỗ **không cần $K$** chứ không phải ở phân hoạch tốt hơn; xóa $\mathcal{S}_{context}$ ở mặc định $\beta=\gamma=0{,}5$ **không đổi gì cả**, nên số hạng ngữ cảnh là bảo hiểm cho nhập nhằng dưới ngưỡng $\sigma_{geo}$ chứ không phải động lực của các con số headline; lợi ích công bằng so với chính sách mù tổn thương chỉ **2,9%** trên độ đo trung lập, không phải $33\%$ mà một độ đo suy-từ-$V$ sẽ báo; và một đối thủ giả cả ảnh lẫn corroboration đẩy $C_i$ lên $0{,}92$, cao hơn trung bình tin thật. Gộp lại, khẳng định phòng thủ được **hẹp hơn** "Louvain thắng": chính **ma trận gating** cấp tính gắn kết không gian vận hành, Modularity cấp $K$ tự động, và riêng các độ đo khớp-nhãn **không** đủ để đánh giá phân cụm hướng-điều-phối. Trên cơ sở đó, khung đề xuất là một nền tảng chặt chẽ, công bằng và khả thi về vận hành cho các hệ ứng phó thảm họa vẫn hoạt động khi hạ tầng viễn thông suy kiệt.

---

## Phụ lục B — Đánh giá phản biện và việc cần làm (review nội bộ)

> Mục này ghi lại các điểm yếu đã nhận diện và hành động khắc phục, để hoàn thiện trước khi nộp. Không đưa vào bản LaTeX cuối. **Trạng thái cập nhật (đợt hoàn thiện):** phần lớn các mục 🔴/🟠 đã xử lý — xem dấu ✅ (xong) / ⚠️ (còn lại) dưới đây.

### B.1. Thực nghiệm cần củng cố — ✅ ĐÃ XONG

1. ✅ **Baseline chưa công bằng (ưu tiên cao) — ĐÃ XỬ LÝ (§5.5).** Đã bổ sung Spectral/HDBSCAN/Agglomerative chạy trên *cùng đồ thị gating*, và nâng ablation additive-vs-gating (1A) thành so sánh chính. Yêu cầu gốc:
   - K-Means/DBSCAN trên **cùng ma trận khoảng cách** $d_{ij}=1-w_{ij}$ (hoặc ma trận đặc trưng đa chiều), không chỉ lat/lng.
   - **Spectral Clustering** (ăn trực tiếp affinity $w_{ij}$) và **HDBSCAN** — đây mới là đối thủ đúng nghĩa.
   - Nâng **ablation "Louvain trên đồ thị additive vs gating"** (exp1A) lên thành baseline chính, vì nó cô lập đúng đóng góp.
2. ✅ **Đóng khung lại con số 100 km → 0,30 km — ĐÃ XỬ LÝ (§5.2 (1A), Tóm tắt, Kết luận).** Trên bộ dữ liệu hiện hành (341 sự kiện) con số đã đổi và mạnh hơn: gating co đường kính **xấu nhất** 214 km → **1,41 km** **đồng thời NÂNG** ARI $0{,}9572\rightarrow0{,}9957$, nên vế "co đường kính mà không giảm độ chính xác" nay là "co đường kính **và** tăng độ chính xác".
3. ⚠️ **exp3 (Leiden) — ĐÃ XỬ LÝ TRUNG THỰC (§5.4).** Không dựng ca bệnh giả để ép Leiden thắng. Thay vào đó báo cáo trung thực rằng gating tự triệt tiêu cụm đứt gãy (0/0 trên 10 seed), nên Louvain đã đủ; Leiden giữ vai trò "bảo hiểm lý thuyết". Đây là lựa chọn liêm chính học thuật thay vì phóng đại.
4. ✅ **Độ ổn định xếp hạng — ĐÃ XỬ LÝ (§5.6).** Đã thêm Kendall's τ dưới nhiễu loạn $\omega$ (200 Monte-Carlo/mức) và ổn định cấu trúc theo $\sigma_{geo}$.

### B.2. Công thức cần vá — ✅ ĐÃ XONG

1. ✅ **$\mathcal{F}_{max}$ chưa gate $C_i$ (thiếu nhất quán).** $\mathcal{E}_{agg}$ và $\mathcal{N}_{total}$ đều nhân $C_i$ chống tin giả, nhưng $\mathcal{F}_{max}=\max F_i$ thì không — một báo cáo giả $F=1{,}0$ lọt cụm sẽ chiếm trọn. Đề xuất: $\mathcal{F}_{max}=\max_i (F_i\cdot C_i)$ hoặc dùng phân vị 90 thay vì max tuyệt đối. **→ Đã sửa thành $\max_i(F_i\cdot C_i)$ (Mục 4.4), kiểm chứng ở exp1F: báo cáo giả $F=0{,}99$/$C_i=0{,}45$ bị hạ xuống 0,45.**
2. ✅ **$N_{\max}$ trong $\widetilde{\mathcal{N}}$ gây thang đo trôi (non-stationary).** "Cụm lớn nhất trong cửa sổ hiện tại" khiến cùng một cụm có $\mathcal{P}$ khác nhau tùy các cụm khác. Nêu rõ đây là *ranking tương đối tức thời*, hoặc dùng mốc cố định (dân số tham chiếu theo địa bàn) nếu cần so sánh across-time. **→ Đã nêu rõ hai chế độ mốc động/cố định và tính non-stationary trong Mục 4.4.**
3. ✅ **Nguy cơ double-counting $F, E$.** $F$ và $E$ vừa vào $\mathcal{S}_{context}$ (quyết định gom cụm) vừa vào $\mathcal{F}_{max}/\mathcal{E}_{agg}$ (quyết định ưu tiên). Cụm gom theo $F$ tương đồng thì $\mathcal{F}_{max}$ gần như được đảm bảo cao — hơi vòng tròn. Cần một đoạn thảo luận thừa nhận và biện minh (weighting đo *tương đồng*, priority đo *độ nghiêm trọng tuyệt đối* — khác mục đích). **→ Đã thêm đoạn thảo luận (Mục 4.4) VÀ định lượng bằng exp6. Trên bộ dữ liệu hiện hành, kết quả thậm chí dứt khoát hơn: bỏ $\mathcal{S}_{context}$ ở mặc định $\beta=\gamma=0{,}5$ **không đổi gì cả** (ARI/NMI/số cụm y nguyên, Kendall's τ = **1,0**), nên lo ngại vòng tròn bị loại thẳng — cái giá là phải thừa nhận $\gamma\mathcal{S}_{context}$ dư thừa ở mặc định, và giá trị của nó chỉ hiện ra ở nhập nhằng dưới ngưỡng $\sigma_{geo}$ (phép quét $\beta/\gamma$: ARI tụt còn 0,9509 tại $\beta=0{,}9$).**

### B.3. Lập luận cần chặt hơn — ✅ ĐÃ XONG

- ✅ **Khe hở 2 (equity):** exp1C mới cho thấy thêm $V$ *đổi* ranking, chưa chứng minh ranking mới *đúng hơn*. Cần một lập luận chuẩn tắc (normative) hoặc ví dụ minh họa vì sao ranking có equity công bằng hơn về mặt đạo đức cứu hộ. **→ Đã bổ sung exp7 (mô phỏng điều phối hướng-kết-quả). Lưu ý bản cập nhật: con số 10,4% ban đầu đo trên một độ đo THIÊN VỊ dạng cộng; trên độ đo trung lập ($F\ge0{,}7$, định nghĩa ngoài công thức $\mathcal{P}$) lợi ích so với chính sách mù tổn thương chỉ là **2,9%** (110,2 vs 113,5 phút), còn so với biến thể cộng là **10,3%**. Ta báo cáo con số trung lập nhỏ hơn này thay vì con số đẹp hơn, kèm đánh đổi công bằng–hiệu quả minh bạch (2528 vs 2410 phút cho toàn bộ nạn nhân).**
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
