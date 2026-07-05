# **Báo cáo Nghiên cứu Chuyên sâu: Khe hở Khoa học và Khung Giải pháp Đồ thị Trọng số Toàn diện trong Phân cụm và Ưu tiên Sự kiện Cứu hộ Bão lũ**

## **1\. Đặt vấn đề và Bối cảnh Nghiên cứu**

Trong bối cảnh biến đổi khí hậu toàn cầu đang diễn biến phức tạp, các hiện tượng thời tiết cực đoan, đặc biệt là bão lụt, đang gia tăng mạnh mẽ cả về tần suất lẫn cường độ, để lại những hệ lụy nặng nề đối với sinh mạng và hạ tầng cơ sở.[^1] Tại các quốc gia có đường bờ biển dài và chịu ảnh hưởng trực tiếp từ các hoàn lưu bão như Việt Nam, thiệt hại thường bị khuếch đại nghiêm trọng do sự chậm trễ trong công tác cứu hộ và sự phân bổ tài nguyên không đồng đều trong những giờ đầu tiên (golden hour) của thảm họa.[^3] Một trong những nguyên nhân cốt lõi dẫn đến sự đứt gãy trong công tác phản ứng khẩn cấp (emergency response) là sự gián đoạn của hạ tầng viễn thông. Khi lưới điện suy kiệt và các trạm thu phát sóng di động (BTS) bị cô lập hoặc phá hủy, các mô hình thu thập và xử lý dữ liệu tập trung (Cloud-centric) truyền thống hoàn toàn bị vô hiệu hóa, dẫn đến tình trạng các trung tâm chỉ huy mất kết nối với vùng tâm bão.[^3]
Nhằm giải quyết điểm nghẽn này, mạng xã hội và các nền tảng tin nhắn cộng đồng đã vươn lên trở thành một kênh cảm biến xã hội (social sensing) mang tính sinh tồn.[^7] Dữ liệu sinh ra từ các nền tảng này mang tính đa phương thức (multimodal) rất cao, bao gồm văn bản (text), hình ảnh (image), âm thanh/video (mp4) và siêu dữ liệu không gian \- thời gian (spatiotemporal metadata).[^3] Tuy nhiên, dòng chảy thông tin này thường rời rạc, trùng lặp, thiếu cấu trúc và chứa một lượng nhiễu (noise) khổng lồ, khiến các lực lượng chức năng dễ rơi vào trạng thái quá tải thông tin (information overload).[^9]
Để giải quyết bài toán phức hợp này, việc ứng dụng Trí tuệ Nhân tạo Đa phương thức (Multimodal AI) kết hợp với Điện toán Biên (Edge Computing) và Lý thuyết Đồ thị Trọng số (Weighted Graph Theory) đang nổi lên như một hướng tiếp cận học thuật và thực tiễn mang tính đột phá.[^3] Báo cáo nghiên cứu này được thực hiện nhằm mục đích bóc tách toàn diện các công trình khoa học hiện tại về quản lý thông tin cứu hộ bão lũ. Bằng cách phân tích sâu các thuật toán tạo lập đồ thị trọng số, phân cụm sự kiện (event clustering) và trích xuất cộng đồng (community detection), báo cáo sẽ định vị các khe hở khoa học (research gaps) cốt lõi. Từ nền tảng đó, một khung giải pháp toàn diện được đề xuất nhằm tận dụng cấu trúc đồ thị trọng số đa chiều, tích hợp các thuộc tính phức hợp của một sự kiện cứu hộ (bao gồm mức độ khẩn cấp, độ sâu ngập lụt, tọa độ, thời gian, số lượng người mắc kẹt và các thuộc tính nhân khẩu học) để phân cụm và tự động hóa quá trình đánh giá mức độ ưu tiên, hướng tới mục tiêu tối thượng là hỗ trợ ra quyết định cứu hộ kịp thời, công bằng và hiệu quả.

## **2\. Tổng quan Tình hình Nghiên cứu hiện tại (State-of-the-Art)**

### **2.1. Phân tích Đa phương thức (Multimodal Analysis) trong Khủng hoảng**

Trong những năm gần đây, sự dịch chuyển từ các mô hình học máy đơn phương thức (unimodal) sang đa phương thức (multimodal) đã đánh dấu một bước tiến lớn trong khả năng nhận thức tình huống (situational awareness) của các hệ thống quản lý thiên tai. Các bộ dữ liệu tiên phong như CrisisMMD và FloodNet đã cung cấp nền tảng quan trọng cho việc huấn luyện các mô hình AI nhận diện mức độ thiệt hại và phân loại thông tin khẩn cấp.[^3]
Các hệ thống tiên tiến hiện nay khai thác kiến trúc lai để xử lý đồng thời nhiều luồng dữ liệu. Đối với hình ảnh và video, các mạng nơ-ron tích chập (CNN) như ResNet, MobileNet, hoặc các mô hình phân đoạn ngữ nghĩa (Semantic Segmentation) như DeepLabv3+ được sử dụng để phân loại cảnh quan thảm họa, trích xuất vùng ngập lụt và ước lượng thiệt hại cơ sở hạ tầng.[^3] Chẳng hạn, một số nghiên cứu đã ứng dụng kỹ thuật ước lượng tư thế người (Human Pose Estimation) từ hình ảnh mạng xã hội để tính toán độ sâu mực nước lũ thực tế tại các khu vực mà hệ thống trạm quan trắc vật lý bị gián đoạn.[^3]
Đối với dữ liệu văn bản và âm thanh, các mô hình ngôn ngữ lớn (LLM) và cấu trúc Transformer (như BERT, DistilBERT, Bi-LSTM) được triển khai để trích xuất ngữ nghĩa, phân tích cảm xúc (sentiment analysis), và nhận diện thực thể (NER) nhằm xác định mức độ hoảng loạn hoặc các nhu cầu cấp thiết (như cần thức ăn, y tế, hoặc sơ tán).[^3] Các mô hình như CrisisSpot đã chứng minh rằng việc sử dụng mạng nơ-ron đồ thị (Graph Neural Networks \- GNN) để nắm bắt các mối quan hệ phức tạp giữa các phương thức văn bản và hình ảnh, kết hợp với các đặc trưng ngữ cảnh xã hội, có thể cải thiện đáng kể độ chính xác (F1-score tăng từ 5% đến 9.45%) trong việc phân loại nội dung liên quan đến thảm họa.[^9] Tương tự, mô hình SCBD (SSE-Cross-BERT-DenseNet) áp dụng module chú ý chéo (cross-attention) để lọc bỏ các thành phần không liên quan từ đầu vào văn bản và hình ảnh, giải quyết triệt để những hạn chế của các phương pháp đơn phương thức trong môi trường nhiễu.[^11]

### **2.2. Sự Dịch chuyển sang Điện toán Biên (Edge Computing)**

Mặc dù các mô hình đa phương thức mang lại độ chính xác cao, thách thức chí mạng của chúng nằm ở nhu cầu băng thông và năng lực tính toán. Trong kịch bản bão lũ, việc truyền tải các tệp video (mp4) hoặc hình ảnh độ phân giải cao lên các máy chủ đám mây (Cloud) để suy luận (inference) là hoàn toàn bất khả thi do mạng di động suy yếu hoặc sụp đổ.[^3] Để khắc phục điểm nghẽn này, cộng đồng nghiên cứu đã và đang thúc đẩy việc đưa Trí tuệ Nhân tạo xuống sát nguồn sinh dữ liệu thông qua Điện toán Biên (Edge AI).[^3]
Bằng cách áp dụng các kỹ thuật nén mô hình (Model Quantization, Knowledge Distillation) và tối ưu hóa kiến trúc mạng nơ-ron nhẹ, các thiết bị đầu cuối như điện thoại thông minh của nạn nhân, hoặc các thiết bị không người lái (UAV/Drone) của lực lượng cứu hộ, có thể tự thực thi các tác vụ học sâu ngay tại chỗ (on-device).[^3] Thay vì gửi toàn bộ video hoặc hình ảnh thô, thiết bị biên chỉ cần thực hiện phân tích và sau đó truyền tải một tệp siêu dữ liệu (metadata) gọn nhẹ (chỉ vài Kilobytes) chứa các thuộc tính đã được số hóa như: phân loại mức độ ngập, điểm số cảm xúc khẩn cấp, tọa độ GPS, và thời gian.[^17] Cách tiếp cận "băng thông thấp, độ trễ thấp" này đảm bảo rằng thông tin kêu cứu vẫn có thể thâm nhập qua các hạ tầng mạng bị tắc nghẽn, duy trì khả năng liên tục hoạt động (operational continuity) của hệ thống ngay cả khi không có kết nối internet băng thông rộng.[^5] Nền tảng ResQConnect là một minh chứng điển hình khi triển khai các mô hình ngôn ngữ thu gọn trực tiếp trên thiết bị di động, cung cấp khả năng điều hướng ngoại tuyến với độ trễ phản hồi dưới 500 mili-giây.[^16]

### **2.3. Khai phá Dữ liệu Không gian \- Thời gian dựa trên Đồ thị (Graph-based Spatiotemporal Analytics)**

Trong quản lý khủng hoảng, việc xem xét các lời kêu cứu như những điểm dữ liệu cô lập thường làm mất đi bối cảnh toàn cục. Lý thuyết đồ thị (Graph Theory) cung cấp một khung toán học mạnh mẽ để mô hình hóa sự tương tác, độ tương đồng, và sự lan truyền rủi ro giữa các sự kiện.[^22] Một sự kiện cứu hộ có thể được biểu diễn như một đỉnh (node/vertex) $V$ trong một đồ thị $G = (V, E, W)$, trong đó các cạnh (edges) $E$ đại diện cho mối liên hệ giữa các sự kiện, và trọng số (weights) $W$ phản ánh cường độ của mối liên hệ đó.[^13]
Các nghiên cứu tiên phong trong việc phát hiện sự kiện (event detection) từ mạng xã hội thường xây dựng đồ thị trọng số dựa trên sự tương đồng về không gian \- thời gian (spatiotemporal proximity) và sự đồng xuất hiện của từ khóa (word co-occurrence).[^25] Ví dụ, trong mô hình TwitterNews+, các nhà nghiên cứu đã sử dụng phương pháp TF-IDF (Term Frequency-Inverse Document Frequency) để đo lường độ tương đồng theo cặp giữa các bài đăng, từ đó tạo ra một đồ thị trọng số vô hướng, trong đó các đỉnh là các bài đăng và các cạnh đại diện cho điểm số tương đồng ngữ nghĩa.[^25] Các mô hình tiên tiến hơn kết hợp tính toán khoảng cách Euclidean hoặc Haversine để phạt (penalize) các liên kết giữa những sự kiện cách xa nhau về mặt địa lý, tạo ra các đồ thị tích hợp chặt chẽ cả đặc tính không gian và ngữ nghĩa (Geo-Semantic Graphs).[^28]

### **2.4. Thuật toán Phân cụm và Phát hiện Cộng đồng (Community Detection)**

Sau khi mạng lưới đồ thị được thiết lập, thách thức tiếp theo là gom nhóm (clustering) các đỉnh có độ gắn kết cao thành các cụm sự kiện (event clusters) hoặc cộng đồng (communities). Các thuật toán học không giám sát truyền thống như K-Means hay DBSCAN gặp nhiều hạn chế trong bài toán này. K-Means yêu cầu người dùng phải xác định trước số lượng cụm $K$ (điều bất khả thi trong kịch bản thảm họa luôn biến động) và thường giả định các cụm có hình dạng hình học đơn giản.[^30] DBSCAN tuy có thể tự động tìm số lượng cụm dựa trên mật độ và xử lý nhiễu tốt, nhưng lại nhạy cảm với các không gian đa chiều (high-dimensionality) và yêu cầu tinh chỉnh tham số khắt khe.[^32]
Vượt trội hơn cả, các thuật toán phát hiện cộng đồng dựa trên cấu trúc liên kết mạng (Network Topology), đặc biệt là thuật toán Louvain, đã trở thành tiêu chuẩn vàng (gold standard) để phân cụm đồ thị trọng số.[^35] Thuật toán Louvain được thiết kế để tối ưu hóa hàm Modularity ($Q$), một chỉ số đo lường mật độ của các cạnh bên trong một cộng đồng so với sự phân bố ngẫu nhiên của các cạnh giữa các cộng đồng khác nhau.[^35]
Đối với một đồ thị trọng số, Modularity $Q$ được định nghĩa nghiêm ngặt như sau:

$$
Q = \frac{1}{2m} \sum_{i,j} \left[ A_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)
$$

Trong đó:

* $A_{ij}$ là trọng số cạnh giữa đỉnh $i$ và đỉnh $j$.
* $k_i = \sum_j A_{ij}$ là tổng trọng số của tất cả các cạnh gắn với đỉnh $i$.
* $m = \frac{1}{2} \sum_{i,j} A_{ij}$ là tổng trọng số của toàn bộ đồ thị.
* $c_i$ là cộng đồng chứa đỉnh $i$. Hàm Kronecker delta $\delta(c_i, c_j)$ trả về giá trị $1$ nếu đỉnh $i$ và đỉnh $j$ nằm trong cùng một cộng đồng, và bằng $0$ nếu ngược lại.[^36]

Thuật toán Louvain hoạt động qua một quá trình tối ưu hóa tham lam (greedy optimization) gồm hai pha lặp lại liên tục. Pha đầu tiên đánh giá việc di chuyển từng đỉnh sang các cộng đồng lân cận để tìm kiếm mức tăng Modularity lớn nhất. Pha thứ hai tiến hành nén (aggregate) các cộng đồng vừa tìm được thành các "siêu đỉnh" (supernodes) để tạo ra một đồ thị mới ở quy mô vĩ mô hơn. Nhờ cách tiếp cận heuristic này, độ phức tạp tính toán của Louvain được duy trì ở mức $\mathcal{O}(N \log N)$, cực kỳ hiệu quả để xử lý các mạng lưới dữ liệu khổng lồ theo thời gian thực.[^35] Các biến thể tối ưu hơn như Leiden algorithm cũng được phát triển sau này để giải quyết hiện tượng các cộng đồng bị đứt gãy bên trong (badly connected communities) thỉnh thoảng xuất hiện ở Louvain.[^34]

## **3\. Xác định Khe hở Khoa học (Research Gaps)**

Thông qua việc đánh giá nghiêm ngặt các công trình nghiên cứu hiện hành, báo cáo đã tổng hợp và nhận diện được ba khe hở khoa học (research gaps) căn bản. Việc bóc tách các điểm mù này tạo tiền đề lý luận vững chắc cho sự cần thiết của đề tài nghiên cứu hiện tại.
The following table summarizes the identified scientific gaps by comparing existing methodologies against the complex requirements of disaster rescue:

| Khía cạnh Nghiên cứu                                     | Hạn chế của các phương pháp hiện hành                                                                                                                                | Khe hở khoa học (Research Gaps) được xác định                                                                                                                                        |
| :----------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Xây dựng Đồ thị Trọng số**                    | Hầu hết các mô hình chỉ dựa vào khoảng cách địa lý (Euclidean) hoặc độ tương đồng văn bản TF-IDF để thiết lập trọng số cạnh.[^13]                | Bỏ qua các đặc trưng vật lý sinh tồn. Cần một hàm trọng số đa chiều tích hợp độ sâu ngập lụt (từ hình ảnh) và mức độ đe dọa sinh mạng (từ văn bản/video). |
| **Kiến trúc Hệ thống (System Architecture)**       | Phụ thuộc nặng nề vào các mô hình học sâu triển khai trên Cloud. Khi hạ tầng viễn thông tê liệt, không thể truyền tải dữ liệu đa phương thức.[^3] | Thiếu một khung kiến trúc lai (hybrid) kết hợp trích xuất thuộc tính tại biên (Edge AI) và gửi siêu dữ liệu (metadata) nhẹ lên máy chủ để lập đồ thị.             |
| **Đánh giá và Ra quyết định (Decision Making)** | Định tuyến cứu hộ xem các nhu cầu là đồng nhất (homogeneous demand). Không định lượng được mức độ ưu tiên của một cụm so với cụm khác.[^41]     | Khoảng trống lớn trong việc thiết lập một "Hàm điểm số Ưu tiên Cấp độ Cụm" (Cluster-level Priority Scoring) tích hợp chỉ số tổn thương nhân khẩu học.             |

### **3.1. Khe hở 1: Sự thiếu hụt Thuộc tính Đặc thù trong Định lượng Trọng số Đồ thị**

Phần lớn các nghiên cứu về phát hiện sự kiện (event detection) trên mạng xã hội hiện nay xây dựng đồ thị trọng số dựa trên các tham số có sẵn và dễ xử lý như khoảng cách không gian (GPS) và tần suất xuất hiện của từ khóa.[^26] Tuy nhiên, trong bài toán cứu hộ bão lũ, bản chất của một sự kiện mang tính phức hợp vật lý rất cao. Việc hai sự kiện ở gần nhau về mặt địa lý không đồng nghĩa với việc chúng chịu cùng một mức độ rủi ro, bởi rủi ro còn bị chi phối bởi địa hình vi mô (micro-topography), kết cấu nhà ở, hoặc tình trạng sinh lý của nạn nhân.
Khe hở khoa học sâu sắc ở đây là sự vắng bóng của các thuộc tính vật lý và sinh học trong việc định lượng mối quan hệ giữa các sự kiện. Việc không tích hợp được biến số "độ sâu ngập lụt" (trích xuất từ phân tích hình ảnh) và "mức độ hoảng loạn/khẩn cấp" (trích xuất từ phân tích cảm xúc văn bản hoặc cường độ âm thanh) vào trong cùng một không gian nhúng (embedding space) để tính toán trọng số cạnh $w_{ij}$ khiến cho đồ thị mất đi khả năng phản ánh đúng thực trạng khốc liệt của thảm họa.[^3] Một đồ thị chỉ phản ánh không gian sẽ không thể giúp lực lượng cứu hộ phân biệt được một nhóm người đang kẹt trên mái nhà (nước dâng cao) với một nhóm người đang an toàn ở chung cư tầng cao dù họ có cùng chung tọa độ.

### **3.2. Khe hở 2: Điểm mù trong Việc Lượng hóa Rủi ro Nhân khẩu học (Vulnerability Blind Spot)**

Trong lĩnh vực logistics nhân đạo và nghiên cứu phân bổ nguồn lực (resource allocation), các khung định tuyến truyền thống thường tiếp cận với giả định "nhu cầu đồng nhất" (homogenous demand). Điều này có nghĩa là mọi nạn nhân hoặc mọi yêu cầu cứu hộ đều được xem xét với mức độ ưu tiên ngang nhau, và mục tiêu tối thượng chỉ là tối thiểu hóa quãng đường hoặc thời gian di chuyển (efficiency).[^42]
Tuy nhiên, thực tế chứng minh thảm họa tác động cực kỳ bất bình đẳng lên các nhóm nhân khẩu học khác nhau. Sự vắng mặt của yếu tố tổn thương (demographic vulnerability) – chẳng hạn như người già, trẻ em, phụ nữ mang thai, hoặc người khuyết tật – trong quá trình gom cụm và xếp hạng là một thiếu sót nghiêm trọng.[^42] Khi một sự kiện cứu hộ chứa đựng các đối tượng yếu thế, tốc độ suy giảm thể trạng của họ diễn ra nhanh hơn rất nhiều so với người trưởng thành khỏe mạnh. Việc đồ thị trọng số không nắm bắt, đánh giá và khuếch đại (amplify) các sự kiện có chứa đối tượng yếu thế là một điểm nghẽn lớn cần được khai thông để đảm bảo tính công bằng (equity) trong đạo đức cứu hộ.[^41]

### **3.3. Khe hở 3: Hạn chế của Phân cụm Tĩnh và Tính toán Độ ưu tiên Cấp độ Cộng đồng**

Nhiều nghiên cứu hiện tại dừng lại ở việc áp dụng thuật toán Louvain để phân cụm đồ thị và xem việc "phát hiện ra các nhóm sự kiện" là kết quả cuối cùng của hệ thống.[^34] Trong bối cảnh cứu hộ thời gian thực, việc xác định được các cụm sự kiện (rescue communities) chỉ mới là bước phân tích cấu trúc vĩ mô. Khe hở nằm ở bước tiếp nối: Làm thế nào để định lượng và xếp hạng mức độ khẩn cấp (Emergency Level) của toàn bộ một cụm thay vì chỉ là của từng đỉnh riêng lẻ?
Sự vắng bóng của một cơ chế tính toán điểm số tổng hợp cấp độ cụm (Cluster-level Priority Scoring) làm giảm đi đáng kể khả năng ứng dụng thực tiễn của các thuật toán phân rã đồ thị. Lực lượng điều phối cần biết chính xác cụm nào trong số hàng chục cụm trên bản đồ cần được ưu tiên điều động trực thăng hay ca nô đầu tiên. Đánh giá này đòi hỏi sự tổng hợp phức tạp giữa mức độ ngập lụt tối đa, tổng số lượng người mắc kẹt, tỷ lệ đối tượng yếu thế, và mức độ khẩn cấp chung của toàn bộ quần thể trong cụm đó. Các chỉ số này chưa được mô hình hóa toán học một cách triệt để trong các công bố khoa học gần đây.

## **4\. Khung Giải pháp Đồ thị Trọng số Toàn diện trong Ra quyết định Cứu hộ**

Nhằm lấp đầy các khe hở khoa học đã nêu và đáp ứng trực tiếp yêu cầu của đề tài nghiên cứu, báo cáo đề xuất một khung giải pháp toàn diện. Giải pháp này kết hợp cơ chế xử lý tại biên (Edge AI) để trích xuất thuộc tính đa phương thức, xây dựng cấu trúc đồ thị trọng số tích hợp không gian \- ngữ nghĩa \- vật lý, phân rã cụm bằng thuật toán Louvain, và cuối cùng là tính toán điểm số ưu tiên cho từng quần thể sự kiện.

### **4.1. Khai phá và Tiền xử lý Thuộc tính Đa chiều (Multidimensional Attributes Matrix)**

Mỗi sự kiện cứu hộ $v_i$ được biểu diễn không chỉ bằng tọa độ tĩnh mà là một vector đa chiều, chứa các thuộc tính được tinh lọc thông qua các mô hình trí tuệ nhân tạo. Đề tài nghiên cứu hiện tại [^3] đã đề xuất một tập thuộc tính cốt lõi xuất sắc; báo cáo này sẽ chuẩn hóa và đề xuất bổ sung thêm các trường thông tin mang tính quyết định để tạo nên một bộ cấu trúc siêu dữ liệu (metadata) hoàn chỉnh nhất.

**Tập thuộc tính Cơ sở (Base Attributes):**

1. **Vị trí Không gian ($L_i$):** Tọa độ kinh độ và vĩ độ (GPS) trích xuất từ thiết bị di động hoặc được suy luận từ văn bản (Geo-tagging).[^46]
2. **Tem thời gian ($T_i$):** Thời điểm ghi nhận sự kiện, biến số cực kỳ quan trọng để mô hình hóa sự suy giảm ưu tiên theo thời gian hoặc tính toán tốc độ lan truyền của lũ.[^3]
3. **Mức độ ngập lụt vật lý ($F_i$):** Một biến số liên tục (ví dụ: chuẩn hóa từ 0.0 đến 1.0) định lượng rủi ro môi trường. Giá trị này được tự động trích xuất thông qua mô hình phân đoạn ngữ nghĩa (Semantic Segmentation) hoặc ước lượng tư thế người (Human Pose Estimation) từ hình ảnh/video tải lên.[^3] Kỹ thuật này đo lường tỷ lệ cơ thể người bị che khuất bởi nước để tính toán độ sâu tương đối.
4. **Mức độ khẩn cấp ($E_i$):** Đánh giá mức độ đe dọa sinh mạng thông qua phân tích cảm xúc (sentiment analysis) hoặc nhận diện từ khóa khẩn cấp từ văn bản (text), hoặc phân tích cường độ âm thanh (audio) từ các đoạn video mp4. Mô hình xử lý ngôn ngữ tự nhiên như DistilBERT hoặc UIT-VSMEC (cho tiếng Việt) sẽ phân loại và gán trọng số khẩn cấp.[^3]
5. **Số lượng người mắc kẹt ($N_i$):** Số nguyên đại diện cho quy mô sinh mạng cần giải cứu tại điểm $v_i$, được người dùng nhập trực tiếp hoặc AI dự đoán thông qua đếm số lượng người trong khung hình (Crowd Counting).

**Tập thuộc tính Đề xuất Bổ sung (Proposed Novel Attributes):**

6. **Chỉ số Tổn thương Nhân khẩu học ($V_i$):** Định lượng sự hiện diện của các đối tượng yếu thế (trẻ sơ sinh, người cao tuổi, phụ nữ mang thai, người khuyết tật) tại điểm $v_i$. Thay vì đòi hỏi một pipeline "NLP sâu" riêng biệt, thuộc tính này được trích xuất *ghép chung* (multi-task head) với chính bộ phân loại văn bản dùng cho $E_i$: mô hình DistilBERT/UIT-VSMEC đã lượng tử hóa được bổ sung một nhánh đầu ra phân loại đa nhãn (multi-label) để nhận diện các cụm từ như "có trẻ sơ sinh", "cụ già bị kiệt sức", "phụ nữ mang thai". Nhờ đó $V_i$ không phát sinh thêm mô hình nặng trên thiết bị biên. Giá trị $V_i$ được định nghĩa là *tổng trọng số của các đối tượng yếu thế* được phát hiện tại điểm đó (ví dụ mỗi nhãn đóng góp một trọng số $\ge 1$ theo mức độ ưu tiên nhân đạo), đóng vai trò hệ số điều chỉnh công bằng (equity) trong xếp hạng ưu tiên.[^42]
7. **Độ tin cậy của thông tin ($C_i$):** Trong khủng hoảng, hiện tượng tin giả hoặc báo cáo sai lệch thường xuyên xảy ra, do đó mỗi sự kiện được gán một hệ số tin cậy $C_i \in (0, 1]$. Trong phạm vi khả thi của một hệ thống chưa có hạ tầng tài khoản dài hạn hay mạng cảm biến vật lý, $C_i$ được ước lượng bằng một **heuristic tổng hợp nhẹ** dựa trên các tín hiệu sẵn có: (i) sự hiện diện của bằng chứng đa phương thức (báo cáo có kèm ảnh/video được xác thực bởi mô hình thị giác sẽ có $C_i$ cao hơn báo cáo chỉ có văn bản); (ii) mức đồng thuận không gian (số lượng báo cáo độc lập rơi vào cùng một vùng lân cận trong cùng cửa sổ thời gian). Công thức heuristic đề xuất là $C_i = \sigma\!\big(b_0 + b_1\,\mathbb{1}[\text{có ảnh}] + b_2\,\log(1 + n_i^{\text{corrob}})\big)$, với $\sigma$ là hàm sigmoid và $n_i^{\text{corrob}}$ là số báo cáo lân cận củng cố. Các cơ chế nâng cao hơn (lịch sử xác thực người dùng, đồng thuận với cảm biến vật lý) được ghi nhận là **hướng mở rộng tương lai** vượt ngoài phạm vi triển khai 6 tháng của đề tài.[^9]

Nhờ ứng dụng công nghệ điện toán biên, các mô hình học máy dung lượng thấp được nhúng (embedded) trực tiếp vào ứng dụng di động.[^3] Nhờ đó, thay vì phải cố gắng tải lên các hình ảnh hay video dung lượng hàng Megabyte qua kết nối mạng yếu kém [^5], ứng dụng sẽ xử lý tại chỗ và chỉ gửi đi một chuỗi JSON chứa các tham số định lượng $(L_i, T_i, F_i, E_i, N_i, V_i, C_i)$ với kích thước chỉ vài Kilobyte.[^20] Cơ chế này tối ưu hóa băng thông truyền tải, đảm bảo tín hiệu cầu cứu luôn đến được trung tâm chỉ huy, giải quyết triệt để vấn đề mất kết nối.

> **Ghi chú về phạm vi (scope):** Trong tập thuộc tính trên, $L_i, T_i, E_i, N_i$ và $F_i$ bám sát cam kết của thuyết minh đề tài (ảnh qua MobileNetV3, văn bản qua DistilBERT đã lượng tử hóa). Hai thuộc tính bổ sung $V_i$ và $C_i$ được thiết kế theo nguyên tắc "khả thi tại biên": $V_i$ tái sử dụng bộ phân loại văn bản sẵn có, còn $C_i$ dùng heuristic nhẹ thay cho hạ tầng xác thực phức tạp. Những phiên bản đầy đủ hơn của hai thuộc tính này (crowd counting/pose estimation chuyên biệt cho $N_i$, mô hình tin cậy học từ lịch sử người dùng cho $C_i$) được định vị rõ ràng là *tầm nhìn mở rộng cho bài báo và các giai đoạn nghiên cứu tiếp theo*, không phải là ràng buộc bắt buộc của prototype 6 tháng.

### **4.2. Xây dựng Đồ thị Trọng số Không gian \- Ngữ nghĩa \- Vật lý**

Khâu đột phá tiếp theo của giải pháp nằm ở cách thức thiết lập ma trận kề (Adjacency Matrix) $A$ của đồ thị. Không giống như các hệ thống trước đây chỉ đánh giá trọng số $w_{ij}$ giữa hai sự kiện $v_i$ và $v_j$ dựa trên nghịch đảo khoảng cách địa lý đơn thuần [^29], báo cáo này đề xuất một hàm tính toán trọng số phức hợp đa phương thức (Multimodal Weighting Function).

Một thiết kế ngây thơ là lấy *tổ hợp tuyến tính (cộng)* của ba độ đo tương đồng không gian, thời gian và ngữ cảnh. Tuy nhiên cách cộng này chứa một khiếm khuyết cấu trúc nghiêm trọng đối với bài toán điều phối ca nô: hai sự kiện cách nhau hàng chục ki-lô-mét nhưng cùng mô tả "ngập lút mái nhà" ($F \approx 1.0$) sẽ có $\mathcal{S}_{context}$ rất cao, kéo $w_{ij}$ lên mức đáng kể *bất chấp* $\mathcal{S}_{geo} \approx 0$. Hệ quả là thuật toán phân cụm có thể gom hai điểm ở quá xa nhau vào cùng một "khu vực tác chiến" — điều vô nghĩa khi bán kính hoạt động của một ca nô là hữu hạn. Vì mục tiêu tối thượng là tạo ra các cụm *gắn kết về mặt địa lý*, khoảng cách không gian phải đóng vai trò một **cổng chặn (gate)** chứ không phải một số hạng cộng ngang hàng.

Do đó, báo cáo đề xuất dạng **nhân/gating** trong đó $\mathcal{S}_{geo}$ điều biến (modulate) toàn bộ độ tương đồng phi-không-gian:

$$
w_{ij} = \mathcal{S}_{geo}(L_i, L_j) \cdot \Big( \beta \cdot \mathcal{S}_{temp}(T_i, T_j) + \gamma \cdot \mathcal{S}_{context}(v_i, v_j) \Big)
$$

Với dạng này, khi khoảng cách lớn thì $\mathcal{S}_{geo} \to 0$ kéo theo $w_{ij} \to 0$ dù ngữ cảnh có giống nhau đến đâu, đảm bảo địa lý luôn chi phối cấu trúc cụm. Các thành phần được định nghĩa tường minh như sau:

* $\mathcal{S}_{geo}(L_i, L_j)$ là hàm tương đồng về không gian, đóng vai trò cổng chặn. Thay vì khoảng cách tuyến tính, phân phối Gaussian (hàm suy giảm mũ theo bình phương khoảng cách) được áp dụng để trừng phạt mạnh mẽ các khoảng cách lớn:

$$
\mathcal{S}_{geo} = \exp\left( - \frac{\text{dist}(L_i, L_j)^2}{2\sigma_{geo}^2} \right)
$$

  trong đó $\text{dist}(\cdot)$ là khoảng cách Haversine (mét) và $\sigma_{geo}$ là bán kính đặc trưng, đặt xấp xỉ theo tầm hoạt động thực tế của một đơn vị ca nô cứu hộ (ví dụ vài trăm mét đến 1–2 km). Điều này đảm bảo chỉ những sự kiện ở vùng lân cận thực sự mới có liên kết cấu trúc mạnh mẽ.[^46]

* $\mathcal{S}_{temp}(T_i, T_j)$ là hàm tương đồng về thời gian, cũng dùng suy giảm mũ để những sự kiện được báo cáo gần nhau về thời điểm có độ liên kết cao hơn, giúp hệ thống theo dõi tính động (dynamics) của lũ:

$$
\mathcal{S}_{temp} = \exp\left( - \frac{|T_i - T_j|}{\tau_{temp}} \right)
$$

  với $\tau_{temp}$ là hằng số thời gian đặc trưng (ví dụ 30–60 phút) phản ánh khoảng thời gian mà hai báo cáo còn được coi là cùng một diễn biến.[^26]

* $\mathcal{S}_{context}(v_i, v_j)$ là độ tương đồng ngữ cảnh, đại diện cho sự hội tụ của các rủi ro vật lý. Thay vì chỉ mô tả định tính, báo cáo định nghĩa nó tường minh dựa trên độ chênh lệch mức ngập $\Delta F = |F_i - F_j|$ và độ chênh lệch mức khẩn cấp $\Delta E = |E_i - E_j|$:

$$
\mathcal{S}_{context} = \exp\left( - \frac{|F_i - F_j|}{\tau_F} - \frac{|E_i - E_j|}{\tau_E} \right)
$$

  Nếu hai báo cáo cùng mô tả "nước ngập lút mái nhà" ($F \approx 1.0$) thì $\Delta F \approx 0$ và $\mathcal{S}_{context} \to 1$, khuếch đại liên kết để tạo thành một quần thể khẩn cấp đồng nhất. Trái lại, một người báo ngập nhẹ (an toàn ở tầng 3) và một người báo ngập nặng (đang bám trên mái nhà) sẽ có $\Delta F$ lớn, làm $\mathcal{S}_{context}$ co lại — phản ánh đúng rằng nhu cầu cứu hộ của hai đối tượng là khác biệt. Hai hằng số $\tau_F, \tau_E$ kiểm soát độ nhạy của hàm.
* $\beta, \gamma$ là các tham số cân bằng giữa yếu tố thời gian và ngữ cảnh, có thể do chuyên gia thiết lập hoặc học tự động thông qua tối ưu hóa (Graph Neural Networks).[^9] Lưu ý rằng $\alpha$ trong dạng cộng cũ không còn cần thiết vì $\mathcal{S}_{geo}$ đã trở thành thừa số điều biến toàn cục.

**Làm thưa đồ thị (Graph Sparsification).** Nếu xây dựng đồ thị đầy đủ (nối mọi cặp đỉnh), ma trận kề sẽ dày đặc và gần-hoàn-chỉnh, làm thuật toán tối ưu Modularity hoạt động kém và tốn kém. Vì $\mathcal{S}_{geo}$ suy giảm rất nhanh theo khoảng cách, phần lớn các cạnh xa mang trọng số không đáng kể. Do đó, báo cáo áp dụng một trong hai cơ chế làm thưa: (i) **ngưỡng $\epsilon$** — chỉ giữ cạnh khi $w_{ij} > \theta$; hoặc (ii) **đồ thị k lân cận gần nhất (k-NN graph)** — mỗi đỉnh chỉ nối với $k$ đỉnh có trọng số cao nhất. Cơ chế này vừa giảm độ phức tạp tính toán, vừa loại bỏ các liên kết giả tạo giữa các vùng địa lý cách biệt, tạo ra một đồ thị thưa và có cấu trúc rõ ràng cho bước phân rã cộng đồng.

Thiết kế mạng lưới này không chỉ tái tạo được không gian địa lý (topological space) mà còn phản ánh được hình thái tổn thương (vulnerability landscape), tạo ra một đồ thị trọng số đa chiều lý tưởng cho các thuật toán phân rã cấu trúc.

### **4.3. Phân cụm Sự kiện với Tối ưu hóa Modularity (Thuật toán Louvain)**

Với đồ thị trọng số đã hình thành, hệ thống cần cô lập các nhóm sự kiện có tính cục bộ cao thành các khu vực tác chiến cứu hộ riêng biệt. Giải pháp tối ưu nhất để định tuyến bài toán này là áp dụng thuật toán Louvain.[^35]
Mục tiêu là phân hoạch tập đỉnh $V$ thành tập hợp các cụm (clusters) không giao nhau $\{C_1, C_2, \dots, C_k\}$ sao cho giá trị hàm Modularity $Q$ đạt cực đại.[^35] Việc lựa chọn Louvain mang lại các lợi thế kỹ thuật vô cùng to lớn đối với dữ liệu thảm họa:

1. **Tính tự trị trong phân cụm:** Không giống như K-Means, thuật toán Louvain tự động khám phá số lượng cộng đồng ẩn bên trong cấu trúc đồ thị mà không cần tham số hóa trước số cụm. Điều này cực kỳ quan trọng vì cơ quan điều phối không thể biết trước bão sẽ chia cắt thành phố thành bao nhiêu "ốc đảo".[^35]
2. **Khả năng Khử nhiễu Cấu trúc (Structural Denoising):** Các tin nhắn rác, báo động giả, hoặc báo cáo sai lệch sẽ thiếu đi các cạnh có trọng số lớn liên kết với phần còn lại của mạng lưới. Do đó, thuật toán sẽ tự động đẩy chúng ra thành các cụm đơn lẻ (singleton clusters) hoặc loại trừ, giúp tăng cường độ tin cậy của thông tin.[^26]
3. **Kiểm soát Giới hạn Độ phân giải (Resolution Limit):** Một nhược điểm lý thuyết của thuật toán Louvain là giới hạn độ phân giải, đôi khi khiến nó vô tình hợp nhất các cộng đồng nhỏ lại với nhau thành một cụm quá lớn.[^51] Tuy nhiên, để giải quyết vấn đề này, ta có thể tinh chỉnh tham số độ phân giải (resolution parameter $\lambda$) trong hàm mục tiêu:

$$
Q = \frac{1}{2m} \sum_{i,j} \left[ A_{ij} - \lambda \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)
$$

   Việc tăng giá trị $\lambda$ sẽ buộc thuật toán phân chia sâu hơn để tìm ra các cụm vi mô (micro-communities) cực kỳ dày đặc. Trong thực tiễn cứu hộ, thao tác này tương đương với việc phân rã một phường bị ngập diện rộng thành các khu phố cụ thể, giúp định hướng lộ trình chính xác cho từng mũi ca nô.[^35]

Cần lưu ý một rủi ro chất lượng đặc thù khi cụm được dùng để điều động ca nô: thuật toán Louvain đôi khi tạo ra các cộng đồng **đứt gãy nội bộ (badly connected communities)** — tức các đỉnh được gán chung một cụm nhưng thực chất không liên thông chặt chẽ trong đồ thị con của cụm đó. Nếu một "khu vực tác chiến" bị đứt gãy như vậy, lực lượng điều phối có thể được dẫn đến một trọng tâm (centroid) không phản ánh đúng vị trí thực của các nạn nhân. Vì lý do này, báo cáo khuyến nghị sử dụng biến thể **Leiden** [^51] — vốn bổ sung một bước tinh chỉnh đảm bảo mọi cộng đồng đều liên thông tốt (well-connected) — như một lựa chọn thay thế trực tiếp cho Louvain trong các kịch bản mà độ chính xác không gian của cụm là yếu tố sống còn, đồng thời vẫn giữ nguyên hàm mục tiêu Modularity đã trình bày ở trên.

### **4.4. Đánh giá Mức độ Ưu tiên Cấp độ Cụm (Cluster-level Prioritization)**

Để lấp đầy hoàn toàn khe hở khoa học thứ ba, hệ thống không thể chỉ cung cấp bản đồ các cụm sự kiện mà cần phải thiết lập một cơ chế định lượng để ưu tiên chúng. Điều này trực tiếp hỗ trợ bài toán điều phối: Ca nô cứu hộ nên đi đến cụm A hay cụm B trước?
Thay vì điều phối cảm tính, báo cáo đề xuất một "Hàm Đánh giá Ưu tiên" (Priority Scoring Function) $\mathcal{P}(C_k)$ được thiết lập cho từng cụm $C_k$ sau khi thuật toán Louvain hoàn tất. Việc thiết kế hàm này đòi hỏi xử lý cẩn trọng hai vấn đề toán học then chốt mà một tổ hợp tuyến tính ngây thơ dễ mắc phải: **(a) sai lệch thang đo** giữa các hạng tử, và **(b) sự khác biệt bản chất giữa "cộng" và "nhân"** khi mô hình hóa yếu tố công bằng.

**Vấn đề thang đo và bước chuẩn hóa.** Các đại lượng thành phần có miền giá trị rất khác nhau: điểm khẩn cấp và mức ngập nằm trong $[0, 1]$, nhưng tổng số người mắc kẹt $\sum N_i$ *không bị chặn* và có thể lên tới hàng trăm. Nếu cộng trực tiếp, số hạng dân số sẽ áp đảo toàn bộ, khiến $\mathcal{P}$ gần như chỉ còn phản ánh số người và vô hiệu hóa các yếu tố còn lại. Do đó, mỗi thành phần bắt buộc phải được **chuẩn hóa về cùng khoảng $[0, 1]$** *trước khi* nhân trọng số. Ta ký hiệu $\widetilde{(\cdot)}$ cho đại lượng đã chuẩn hóa. Với dân số, do phân phối lệch phải, ta dùng nén log trước khi min-max:

$$
\widetilde{\mathcal{N}}(C_k) = \frac{\log(1 + \mathcal{N}_{total}(C_k))}{\log(1 + N_{\max})}
$$

trong đó $N_{\max}$ là mốc dân số tham chiếu (ví dụ tổng dân số của cụm lớn nhất trong cửa sổ hiện tại). Các thành phần $\widetilde{\mathcal{E}}, \widetilde{\mathcal{F}}$ vốn đã nằm trong $[0, 1]$ nên có thể giữ nguyên hoặc min-max theo lô cụm.

**Cộng lõi rủi ro, nhân hệ số công bằng.** Điểm thiết kế cốt lõi là: yếu tố tổn thương nhân khẩu học $\mathcal{V}$ mang bản chất *khuếch đại (amplify)* chứ không phải một nguồn rủi ro độc lập cộng thêm. Nếu đưa $\mathcal{V}$ vào như một số hạng cộng $\omega_4 \mathcal{V}_{agg}$, nó chỉ tạo ra một offset gần như hằng số và hoàn toàn không "khuếch đại" gì cả. Vì vậy, báo cáo tách $\mathcal{V}_{agg}$ ra **ngoài** làm thừa số nhân cho toàn bộ lõi rủi ro đã chuẩn hóa:

$$
\mathcal{P}(C_k) = \mathcal{V}_{agg}(C_k) \cdot \Big( \omega_1 \cdot \widetilde{\mathcal{E}}_{agg}(C_k) + \omega_2 \cdot \widetilde{\mathcal{F}}_{max}(C_k) + \omega_3 \cdot \widetilde{\mathcal{N}}(C_k) \Big)
$$

Chi tiết các thành phần toán học như sau:

* **Điểm Khẩn cấp Trung bình $\mathcal{E}_{agg}(C_k)$**: Bằng $\frac{1}{|C_k|} \sum_{v_i \in C_k} E_i \cdot C_i$. Trung bình mức độ khẩn cấp của các sự kiện trong cụm, có tính đến độ tin cậy của thông tin ($C_i$). Một cụm có nhiều báo cáo nguy cấp từ các nguồn đáng tin cậy sẽ đẩy điểm số này lên cao, trong khi các báo cáo có độ tin cậy thấp bị giảm nhẹ ảnh hưởng.
* **Mức độ Ngập Tối đa $\mathcal{F}_{max}(C_k)$**: Bằng $\max_{v_i \in C_k}(F_i)$. Đây là một quyết định chuyên môn quan trọng: việc sử dụng hàm $\max$ thay vì hàm trung bình bởi vì rủi ro môi trường tuân theo nguyên lý bình thông nhau; điểm ngập sâu nhất quyết định rủi ro sinh tồn cao nhất của cả quần thể trong cụm đó.[^43]
* **Quy mô Sinh mạng $\mathcal{N}_{total}(C_k)$**: Bằng $\sum_{v_i \in C_k} N_i \cdot C_i$. Tính tổng số lượng sinh mạng đang bị đe dọa, có **trọng số theo độ tin cậy $C_i$** để một báo cáo giả thổi phồng số người kẹt không thể tự động đẩy cụm lên đầu danh sách. Sau đó đại lượng này được nén log và chuẩn hóa thành $\widetilde{\mathcal{N}}$ như trên. Biến số này tuân thủ nguyên tắc tối đa hóa hiệu suất cứu hộ (Efficiency/Effectiveness) bằng cách hướng nguồn lực đến các khu vực đông người nhất.[^42]
* **Khuếch đại Tổn thương $\mathcal{V}_{agg}(C_k)$**: Bằng $1 + \tanh\!\left( \dfrac{1}{s} \sum_{v_i \in C_k} V_i \right)$, nằm trong khoảng $(1, 2)$. Đây là hệ số *nhân* rủi ro nhân khẩu học, đúng với vai trò "khuếch đại": một cụm không có đối tượng yếu thế nhận hệ số $\approx 1$ (không thay đổi lõi rủi ro), còn cụm có nhiều đối tượng yếu thế được đẩy điểm lên tối đa gấp đôi. Hệ số tỉ lệ $s$ (ví dụ $s = 10$) được thêm vào để **chống bão hòa sớm**: nếu dùng $\tanh(\sum V_i)$ trực tiếp thì chỉ 2–3 đối tượng yếu thế đã đưa $\tanh$ sát 1, khiến một cụm có 1 người yếu thế và một cụm có 50 người yếu thế nhận điểm gần như nhau — triệt tiêu khả năng phân biệt và đi ngược mục tiêu công bằng. Chia cho $s$ giãn vùng tuyến tính của $\tanh$ để hệ số tăng dần một cách có ý nghĩa theo số lượng đối tượng yếu thế. (Một lựa chọn thay thế tương đương về mặt chống bão hòa là dùng $1 + \log(1 + \sum V_i)$ kèm chuẩn hóa.) Hàm $\tanh$ vẫn giữ vai trò chặn trên để tránh điểm số bùng nổ vô cực, đảm bảo tính công bằng (Equity) mà không phá vỡ thang đo.[^42]
* Các trọng số quyết định $\omega_1, \omega_2, \omega_3$ (với $\sum \omega = 1$) được thiết lập linh hoạt bởi ban chỉ huy thông qua một Ma trận Quyết định (Decision Matrix).[^54] Việc tinh chỉnh các trọng số này cho phép hệ thống chuyển đổi trạng thái chiến thuật (ví dụ: ưu tiên cứu số đông vs. ưu tiên khu vực ngập sâu nhất). Vì lõi rủi ro đã được chuẩn hóa về $[0, 1]$ và $\sum \omega = 1$, giá trị lõi cũng nằm trong $[0, 1]$, nên $\mathcal{P}(C_k)$ bị chặn gọn trong khoảng $(0, 2]$ — thuận tiện cho việc xếp hạng và diễn giải.

Việc xếp hạng các giá trị $\mathcal{P}(C_k)$ theo thứ tự giảm dần sẽ cung cấp ngay lập tức một danh sách ưu tiên hành động. Danh sách này, kết hợp với tọa độ trọng tâm (centroid) của các cụm, chính là bộ dữ liệu đầu vào hoàn hảo cho các thuật toán tối ưu hóa định tuyến nâng cao (như A\* cost-aware hoặc các mô hình Adaptive Event-Triggered multi-commodity routing) nhằm điều phối hiệu quả tàu thuyền và vật tư y tế.[^4]

## **5\. Thảo luận về Ý nghĩa và Tác động của Giải pháp**

Sự liên kết chặt chẽ từ bước thu thập thuộc tính vi mô đến phân rã cấu trúc vĩ mô mang lại một tác động cộng hưởng (synergistic impact) to lớn đối với khoa học quản lý thảm họa.
The following table highlights the broader impacts of the proposed weighted-graph architecture across multiple disciplines:

| Lĩnh vực Tác động                            | Giá trị mang lại của giải pháp Đồ thị Trọng số và Điện toán Biên                                                                                                                                                                                                                                           |
| :------------------------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Hạ tầng Viễn thông & Edge Computing** | Hệ thống duy trì sự sống còn (resilience) ngay trong kịch bản sụp đổ mạng. Khối lượng dữ liệu giao tiếp giữa vùng lũ và trung tâm giảm thiểu triệt để từ Megabytes xuống mức Kilobytes thông qua việc chuyển hóa dữ liệu đa phương thức thành metadata tại biên.[^3]           |
| **Khoa học Dữ liệu & AI**                | Mở rộng biên giới của phân tích không gian-thời gian bằng cách chuyển đổi một bài toán phân loại tĩnh thành bài toán Khai phá Cấu trúc Mạng Lưới (Network Topology Mining), nơi các hiệu ứng phi tuyến và rủi ro lan truyền được định lượng chính xác bằng toán học.[^39] |
| **Đạo đức Cứu hộ & Xã hội học**    | Tích hợp chỉ số rủi ro nhân khẩu học vào hàm điểm số ưu tiên giúp tái định hình sự công bằng (Equity). Đảm bảo nguồn lực cứu trợ quý giá không bị lãng phí, giải cứu đúng người, đúng thời điểm (golden hour), mang đậm tính nhân văn.[^41]                            |

Hơn nữa, kiến trúc lai (hybrid architecture) này có khả năng ứng dụng vượt ra ngoài bối cảnh bão lũ. Các nguyên lý thiết lập đồ thị trọng số và thuật toán Louvain có thể được chuyển đổi để lập bản đồ rủi ro hỏa hoạn đô thị, xác định khu vực bùng phát dịch bệnh, hay phân tích chuỗi cung ứng trong các đợt đứt gãy.[^40] Sự kết hợp giữa khả năng suy luận phi tập trung và sức mạnh phân tích cấu trúc tập trung chính là xu hướng không thể đảo ngược của mạng lưới Internet vạn vật phục vụ khẩn cấp (Internet of Emergency Services \- IoES).[^62]

## **6\. Kết luận**

Nghiên cứu về ứng dụng trí tuệ nhân tạo và phân tích dữ liệu đa phương thức trong thảm họa thiên tai đang bước vào một cuộc cách mạng mang tính chuyển giao mô hình (paradigm shift). Thay vì tiếp tục phụ thuộc vào điện toán đám mây tập trung và phân tích các báo cáo dưới dạng các thực thể đơn lẻ rời rạc, xu hướng tất yếu của các hệ thống tình báo nhân đạo là chuyển dịch sang điện toán biên (Edge AI) và tư duy hệ thống dựa trên lý thuyết đồ thị mạng phức hợp (Complex Network Graph Theory).
Báo cáo này đã tiến hành một quá trình mổ xẻ học thuật sâu sắc đối với các công trình hiện tại. Kết quả đã làm nổi bật các khe hở khoa học cốt lõi bao gồm: sự thiếu hụt các thuộc tính vật lý đặc thù (như độ sâu ngập lụt, số lượng người, thông tin nhân khẩu học) trong quá trình thiết lập trọng số cạnh của đồ thị; điểm mù nghiêm trọng trong việc đánh giá mức độ tổn thương của các nhóm đối tượng yếu thế; và sự thiếu liên kết thực tiễn giữa thuật toán phát hiện cộng đồng vĩ mô với quy trình định lượng thứ tự ưu tiên chiến thuật.
Khung giải pháp toàn diện được đề xuất—tích hợp khả năng trích xuất thuộc tính tại biên (biến đổi hình ảnh, văn bản, GPS thành metadata), thiết lập ma trận đồ thị trọng số đa chiều (không gian \- thời gian \- ngữ cảnh khẩn cấp), tối ưu hóa hàm Modularity thông qua thuật toán phân rã Louvain, và cuối cùng là áp dụng cơ chế đánh giá ưu tiên cấp độ cộng đồng (Cluster-level Priority Scoring)—đã giải quyết trọn vẹn các thách thức nêu trên. Phương pháp tiếp cận này không chỉ bảo đảm tính bền vững về mặt truyền tải thông tin trong các điều kiện hạ tầng viễn thông suy kiệt, mà còn mang lại khả năng ra quyết định chính xác, linh hoạt, và cực kỳ công bằng. Kết quả cuối cùng là một hệ thống cung cấp bức tranh nhận thức tình huống (situational awareness) sắc nét theo thời gian thực, có khả năng tự động cô lập các "điểm nóng" (hotspots) cần can thiệp khẩn cấp nhất. Từ đó, khung giải pháp này trực tiếp hỗ trợ các trung tâm chỉ huy trong nỗ lực tối thượng nhằm giảm thiểu tối đa thiệt hại về nhân mạng và tài sản trong các kịch bản thiên tai khốc liệt, định hình một chuẩn mực kiến trúc mới cho các nền tảng ứng phó thảm họa thông minh trong tương lai.

#### **Nguồn trích dẫn**

[^1]: Full article: Automated extraction of spatiotemporal disaster knowledge for urban floods: a multimodal framework based on LLMs and agent \- Taylor & Francis, truy cập vào tháng 7 4, 2026, [https://www.tandfonline.com/doi/full/10.1080/17538947.2026.2640706](https://www.tandfonline.com/doi/full/10.1080/17538947.2026.2640706)
    
[^2]: A New Graph-Based Deep Learning Model to Predict Flooding with Validation on a Case Study on the Humber River \- MDPI, truy cập vào tháng 7 4, 2026, [https://www.mdpi.com/2073-4441/15/10/1827](https://www.mdpi.com/2073-4441/15/10/1827)
    
[^3]: Thuyết minh NCKH
    
[^4]: Performance Optimization of Multi-Criteria Route Planning Algorithms: A Case Study in HAZMAT Emergency Response \- Preprints.org, truy cập vào tháng 7 4, 2026, [https://www.preprints.org/manuscript/202602.0136](https://www.preprints.org/manuscript/202602.0136)
    
[^5]: Edge AI for natural disasters: Faster, smarter response in critical moments \- Latent AI, truy cập vào tháng 7 4, 2026, [https://latentai.com/blog/edge-ai-faster-disaster-response/](https://latentai.com/blog/edge-ai-faster-disaster-response/)
    
[^6]: Moving AI to the edge: Benefits, challenges and solutions \- Red Hat, truy cập vào tháng 7 4, 2026, [https://www.redhat.com/en/blog/moving-ai-edge-benefits-challenges-and-solutions](https://www.redhat.com/en/blog/moving-ai-edge-benefits-challenges-and-solutions)
    
[^7]: Constructing Spatio-temporal Disaster Knowledge Graph from Social Media \- AGILE-GISS, truy cập vào tháng 7 4, 2026, [https://agile-giss.copernicus.org/articles/5/37/2024/agile-giss-5-37-2024.pdf](https://agile-giss.copernicus.org/articles/5/37/2024/agile-giss-5-37-2024.pdf)
    
[^8]: Enhancing Disaster Situation Awareness Through Multimodal Social Media Data: Evidence from Typhoon Haikui \- MDPI, truy cập vào tháng 7 4, 2026, [https://www.mdpi.com/2076-3417/15/1/465](https://www.mdpi.com/2076-3417/15/1/465)
    
[^9]: \[2410.08814\] A social context-aware graph-based multimodal attentive learning framework for disaster content classification during emergencies: a benchmark dataset and method \- arXiv, truy cập vào tháng 7 4, 2026, [https://arxiv.org/abs/2410.08814](https://arxiv.org/abs/2410.08814)
    
[^10]: Making Sense of Microposts (\#Microposts2015) \- CEUR-WS.org, truy cập vào tháng 7 4, 2026, [https://ceur-ws.org/Vol-1395/microposts2015\_proceedings.pdf](https://ceur-ws.org/Vol-1395/microposts2015_proceedings.pdf)
    
[^11]: A Social Context-aware Graph-based Multimodal Attentive Learning Framework for Disaster Content Classification during Emergencie \- arXiv, truy cập vào tháng 7 4, 2026, [https://arxiv.org/pdf/2410.08814](https://arxiv.org/pdf/2410.08814)
    
[^12]: Edge-AI-Powered Hazard Detection: A Real-Time Approach for Identifying Obstructions in Emergency Evacuations \- Diva-Portal.org, truy cập vào tháng 7 4, 2026, [https://www.diva-portal.org/smash/get/diva2:1978420/FULLTEXT02.pdf](https://www.diva-portal.org/smash/get/diva2:1978420/FULLTEXT02.pdf)
    
[^13]: ConvGraph: Community Detection of Homogeneous Relationships in Weighted Graphs, truy cập vào tháng 7 4, 2026, [https://www.mdpi.com/2227-7390/9/4/367](https://www.mdpi.com/2227-7390/9/4/367)
    
[^14]: DisasterReliefGPT: Multimodal AI for Autonomous Disaster Impact Assessment and Crisis Communication \- MDPI, truy cập vào tháng 7 4, 2026, [https://www.mdpi.com/2227-7080/14/3/179](https://www.mdpi.com/2227-7080/14/3/179)
    
[^15]: Graph Convolution-Based Decoupling and Consistency-Driven Fusion for Multimodal Emotion Recognition \- MDPI, truy cập vào tháng 7 4, 2026, [https://www.mdpi.com/2079-9292/14/15/3047](https://www.mdpi.com/2079-9292/14/15/3047)
    
[^16]: ResQConnect: An AI-Powered Multi-Agentic Platform for Human ..., truy cập vào tháng 7 4, 2026, [https://www.mdpi.com/2071-1050/18/2/1014](https://www.mdpi.com/2071-1050/18/2/1014)
    
[^17]: Multi-modal AI for control rooms: use cases & architecture \- visionplatform.ai, truy cập vào tháng 7 4, 2026, [https://visionplatform.ai/multi-modal-ai-for-control-rooms/](https://visionplatform.ai/multi-modal-ai-for-control-rooms/)
    
[^18]: AI-Enabled Onboard Edge Computing for Satellite Intelligence in Disaster Management, truy cập vào tháng 7 4, 2026, [https://un-spider.org/news-and-events/news/ai-enabled-onboard-edge-computing-satellite-intelligence-disaster-management%C2%A0](https://un-spider.org/news-and-events/news/ai-enabled-onboard-edge-computing-satellite-intelligence-disaster-management%C2%A0)
    
[^19]: Embedded AI in Military Drones Is Redefining Autonomy and Operations \- IDGA, truy cập vào tháng 7 4, 2026, [https://www.idga.org/government-defense-it-communications/articles/embedded-ai-in-military-drones-is-redefining-autonomy-and-operations](https://www.idga.org/government-defense-it-communications/articles/embedded-ai-in-military-drones-is-redefining-autonomy-and-operations)
    
[^20]: Edge AI Bridge: A Micro-Layer Intrusion Detection Architecture for Smart-City IoT Networks, truy cập vào tháng 7 4, 2026, [https://www.mdpi.com/2624-831X/7/2/33](https://www.mdpi.com/2624-831X/7/2/33)
    
[^21]: How On-Device Edge Processing Cuts Latency & Boosts Traffic Safety \- Omnisight, truy cập vào tháng 7 4, 2026, [https://omnisightusa.com/blog/how-on-device-edge-processing-cuts-latency-boosts-traffic-safety](https://omnisightusa.com/blog/how-on-device-edge-processing-cuts-latency-boosts-traffic-safety)
    
[^22]: EVENT GRAPH CONSTRUCTION METHOD ON NATURAL DISASTER RESEARCH, truy cập vào tháng 7 4, 2026, [https://isprs-annals.copernicus.org/articles/X-3-W1-2022/125/2022/isprs-annals-X-3-W1-2022-125-2022.pdf](https://isprs-annals.copernicus.org/articles/X-3-W1-2022/125/2022/isprs-annals-X-3-W1-2022-125-2022.pdf)
    
[^23]: Graph Theory Applications in Optimizing Emergency Response Logistics \- Canadian Center of Science and Education, truy cập vào tháng 7 4, 2026, [https://ccsenet.org/journal/index.php/jmr/article/download/0/0/50585/54803](https://ccsenet.org/journal/index.php/jmr/article/download/0/0/50585/54803)
    
[^24]: Community Detection by Information Flow Simulation \- arXiv, truy cập vào tháng 7 4, 2026, [https://arxiv.org/pdf/1805.04920](https://arxiv.org/pdf/1805.04920)
    
[^25]: A Review on the Trends in Event Detection by Analyzing Social Media Platforms' Data, truy cập vào tháng 7 4, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC9231398/](https://pmc.ncbi.nlm.nih.gov/articles/PMC9231398/)
    
[^26]: Multiscale event detection in social media \- MIT Media Lab, truy cập vào tháng 7 4, 2026, [https://web.media.mit.edu/\~xdong/paper/dmkd15.pdf](https://web.media.mit.edu/~xdong/paper/dmkd15.pdf)
    
[^27]: Clustering Big Spatiotemporal-Interval Data \- GitHub Pages, truy cập vào tháng 7 4, 2026, [https://swsamleo.github.io/wei\_shao.github.io/files/paper5.pdf](https://swsamleo.github.io/wei_shao.github.io/files/paper5.pdf)
    
[^28]: Disaster Prediction Knowledge Graph Based on Multi-Source Spatio-Temporal Information, truy cập vào tháng 7 4, 2026, [https://www.researchgate.net/publication/358964513\_Disaster\_Prediction\_Knowledge\_Graph\_Based\_on\_Multi-Source\_Spatio-Temporal\_Information](https://www.researchgate.net/publication/358964513_Disaster_Prediction_Knowledge_Graph_Based_on_Multi-Source_Spatio-Temporal_Information)
    
[^29]: A spatiotemporal displacement prediction method for InSAR-detected landslides using a graph neural network coupling spatial and temporal features \- Taylor & Francis, truy cập vào tháng 7 4, 2026, [https://www.tandfonline.com/doi/full/10.1080/19475705.2025.2596362](https://www.tandfonline.com/doi/full/10.1080/19475705.2025.2596362)
    
[^30]: Natural Disaster Clustering Using K-Means, DBSCAN, SOM, GMM, and Mean Shift: An Analysis of Fema Disaster Statistics \- The Science and Information (SAI) Organization, truy cập vào tháng 7 4, 2026, [https://thesai.org/Downloads/Volume15No9/Paper\_68-Natural\_Disaster\_Clustering\_Using\_K\_means.pdf](https://thesai.org/Downloads/Volume15No9/Paper_68-Natural_Disaster_Clustering_Using_K_means.pdf)
    
[^31]: R: K Means Clustering vs Community Detection Algorithms (Weighted Correlation Network) \- Have I overcomplicated this question? \- Stack Overflow, truy cập vào tháng 7 4, 2026, [https://stackoverflow.com/questions/64849921/r-k-means-clustering-vs-community-detection-algorithms-weighted-correlation-ne](https://stackoverflow.com/questions/64849921/r-k-means-clustering-vs-community-detection-algorithms-weighted-correlation-ne)
    
[^32]: An improved spatio-temporal clustering method for extracting fire footprints based on MCD64A1 in the Daxing'anling Area of north-eastern China \- ConnectSci, truy cập vào tháng 7 4, 2026, [https://connectsci.au/wf/article/32/5/679/21934/An-improved-spatio-temporal-clustering-method-for](https://connectsci.au/wf/article/32/5/679/21934/An-improved-spatio-temporal-clustering-method-for)
    
[^33]: Spatiotemporal Clustering : A Review \- ResearchGate, truy cập vào tháng 7 4, 2026, [https://www.researchgate.net/profile/Shehroz-Khan-3/publication/334476277\_Spatiotemporal\_clustering\_a\_review/links/5d39343ea6fdcc370a5d852a/Spatiotemporal-clustering-a-review.pdf](https://www.researchgate.net/profile/Shehroz-Khan-3/publication/334476277_Spatiotemporal_clustering_a_review/links/5d39343ea6fdcc370a5d852a/Spatiotemporal-clustering-a-review.pdf)
    
[^34]: GraphHDBSCAN\*: Graph-based Hierarchical Clustering on High Dimensional Single-cell RNA Sequencing Data | bioRxiv, truy cập vào tháng 7 4, 2026, [https://www.biorxiv.org/content/10.64898/2026.03.24.713924v1.full-text](https://www.biorxiv.org/content/10.64898/2026.03.24.713924v1.full-text)
    
[^35]: Louvain method for community detection, truy cập vào tháng 7 4, 2026, [https://perso.uclouvain.be/vincent.blondel/research/louvain.html](https://perso.uclouvain.be/vincent.blondel/research/louvain.html)
    
[^36]: Louvain method \- Wikipedia, truy cập vào tháng 7 4, 2026, [https://en.wikipedia.org/wiki/Louvain\_method](https://en.wikipedia.org/wiki/Louvain_method)
    
[^37]: Xilinx Louvain Modularity Alveo Product Overview, truy cập vào tháng 7 4, 2026, [https://xilinx.github.io/graphanalytics/louvainmod/overview.html](https://xilinx.github.io/graphanalytics/louvainmod/overview.html)
    
[^38]: Exploring the Landscape of Distributed Graph Clustering on Leadership Supercomputers \- OSTI, truy cập vào tháng 7 4, 2026, [https://www.osti.gov/servlets/purl/2538195](https://www.osti.gov/servlets/purl/2538195)
    
[^39]: MUST: Multi-Scale Structural-Temporal Link Prediction Model for UAV Ad Hoc Networks, truy cập vào tháng 7 4, 2026, [https://www.computer.org/csdl/journal/tk/2026/06/11455940/2f9bYpcJuEw](https://www.computer.org/csdl/journal/tk/2026/06/11455940/2f9bYpcJuEw)
    
[^40]: Community Analysis of a Crisis Response Network \- PMC \- NIH, truy cập vào tháng 7 4, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC7206567/](https://pmc.ncbi.nlm.nih.gov/articles/PMC7206567/)
    
[^41]: Optimization of emergency logistics for urban flooding with consideration of rainfall effects \- PMC, truy cập vào tháng 7 4, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC12365076/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12365076/)
    
[^42]: Full article: Vulnerability based prioritization in disaster planning efforts: benefits and trade-offs \- Taylor & Francis, truy cập vào tháng 7 4, 2026, [https://www.tandfonline.com/doi/full/10.1080/03155986.2025.2486230](https://www.tandfonline.com/doi/full/10.1080/03155986.2025.2486230)
    
[^43]: Enhanced Spatiotemporal Landslide Displacement Prediction Using Dynamic Graph-Optimized GNSS Monitoring \- PMC, truy cập vào tháng 7 4, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC12349391/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12349391/)
    
[^44]: The Role of Multimodal Generative AI in Older Adults' Health Management: Systematic Scoping Review \- JMIR AI, truy cập vào tháng 7 4, 2026, [https://ai.jmir.org/2026/1/e84695](https://ai.jmir.org/2026/1/e84695)
    
[^45]: A novel graph-based k-partitioning approach improves the detection of gene-gene correlations by single-cell RNA sequencing \- PMC, truy cập vào tháng 7 4, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC8740455/](https://pmc.ncbi.nlm.nih.gov/articles/PMC8740455/)
    
[^46]: Spatial-Temporal Assessment of Natural Disaster Losses Using Comb- ined AHP-Entropy Weight Method \- EarthArXiv, truy cập vào tháng 7 4, 2026, [https://eartharxiv.org/repository/object/12393/download/22134/](https://eartharxiv.org/repository/object/12393/download/22134/)
    
[^47]: CaST: Causal Discovery via Spatio-Temporal Graphs in Disaster Tweets \- arXiv, truy cập vào tháng 7 4, 2026, [https://arxiv.org/pdf/2602.02601](https://arxiv.org/pdf/2602.02601)
    
[^48]: Analyzing the spatial–temporal dynamics of disaster risk based on social media data: a case study of Weibo during the Typhoon Yagi period \- PMC, truy cập vào tháng 7 4, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC12122763/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12122763/)
    
[^49]: A Disconnection-Pattern-Based Approach for Mapping Spatial Configurations of Vulnerability in Urban Road Networks \- MDPI, truy cập vào tháng 7 4, 2026, [https://www.mdpi.com/2073-445X/15/3/420](https://www.mdpi.com/2073-445X/15/3/420)
    
[^50]: Spatiotemporal Graph Convolutional Network-Based Long Short-Term Memory Model with A\* Search Path Navigation and Explainable Artificial Intelligence for Carbon Monoxide Prediction in Northern Cape Province, South Africa \- MDPI, truy cập vào tháng 7 4, 2026, [https://www.mdpi.com/2073-4433/16/9/1107](https://www.mdpi.com/2073-4433/16/9/1107)
    
[^51]: \[1810.08473\] From Louvain to Leiden: guaranteeing well-connected communities \- arXiv, truy cập vào tháng 7 4, 2026, [https://arxiv.org/abs/1810.08473](https://arxiv.org/abs/1810.08473)
    
[^52]: The Louvain Algorithm: A Powerful Tool for Community Detection in Large Networks, truy cập vào tháng 7 4, 2026, [https://dharvi02mittal.medium.com/the-louvain-algorithm-a-powerful-tool-for-community-detection-in-large-networks-de4ac2091bc3](https://dharvi02mittal.medium.com/the-louvain-algorithm-a-powerful-tool-for-community-detection-in-large-networks-de4ac2091bc3)
    
[^53]: Clique Graphs and Overlapping Communities \- Imperial College London, truy cập vào tháng 7 4, 2026, [https://plato.tp.ph.ic.ac.uk/\~time/TSEpaper/cg.pdf](https://plato.tp.ph.ic.ac.uk/~time/TSEpaper/cg.pdf)
    
[^54]: Decision Matrix For Disaster Management \- Meegle, truy cập vào tháng 7 4, 2026, [https://www.meegle.com/en\_us/topics/decision-matrix/decision-matrix-for-disaster-management](https://www.meegle.com/en_us/topics/decision-matrix/decision-matrix-for-disaster-management)
    
[^55]: Multi-resource scheduling and routing for emergency recovery operations \- PMC, truy cập vào tháng 7 4, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC7456293/](https://pmc.ncbi.nlm.nih.gov/articles/PMC7456293/)
    
[^56]: Reliable Rescue Routing Optimization for Urban Emergency Logistics under Travel Time Uncertainty \- MDPI, truy cập vào tháng 7 4, 2026, [https://www.mdpi.com/2220-9964/7/2/77](https://www.mdpi.com/2220-9964/7/2/77)
    
[^57]: AI Flood Management and Rescue Planning | PDF | Cluster Analysis | Machine Learning, truy cập vào tháng 7 4, 2026, [https://www.scribd.com/document/949728106/AIML-Mini-Project-Report](https://www.scribd.com/document/949728106/AIML-Mini-Project-Report)
    
[^58]: Spatio-temporal clustering | Request PDF \- ResearchGate, truy cập vào tháng 7 4, 2026, [https://www.researchgate.net/publication/225212470\_Spatio-temporal\_clustering](https://www.researchgate.net/publication/225212470_Spatio-temporal_clustering)
    
[^59]: A.I Enabled Disaster Response \- Esri, truy cập vào tháng 7 4, 2026, [https://www.esri.com/arcgis-blog/products/arcgis-enterprise/public-safety/a-i-enabled-disaster-response](https://www.esri.com/arcgis-blog/products/arcgis-enterprise/public-safety/a-i-enabled-disaster-response)
    
[^60]: A dynamic emergency response decision-making method considering the scenario evolution of maritime emergencies | Request PDF \- ResearchGate, truy cập vào tháng 7 4, 2026, [https://www.researchgate.net/publication/372347030\_A\_dynamic\_emergency\_response\_decision-making\_method\_considering\_the\_scenario\_evolution\_of\_maritime\_emergencies](https://www.researchgate.net/publication/372347030_A_dynamic_emergency_response_decision-making_method_considering_the_scenario_evolution_of_maritime_emergencies)
    
[^61]: Disease Outbreak Prevention | RelationalAI Docs, truy cập vào tháng 7 4, 2026, [https://docs.relational.ai/build/templates/disease-outbreak-prevention/](https://docs.relational.ai/build/templates/disease-outbreak-prevention/)
    
[^62]: Integration of artificial intelligence in user experience and interface visual design \- earthquake simulation and multimodal optimization, truy cập vào tháng 7 4, 2026, [https://www.ijsmdo.org/articles/smdo/full\_html/2025/01/smdo250104/smdo250104.html](https://www.ijsmdo.org/articles/smdo/full_html/2025/01/smdo250104/smdo250104.html)
