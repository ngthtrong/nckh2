# Revised report excerpts

## Acronym definitions

Acknowledgement (ACK).

Artificial Intelligence (AI).

Application Programming Interface (API).

Adjusted Rand Index (ARI).

Confidence Interval (CI).

Central Processing Unit (CPU).

Cơ sở dữ liệu (CSDL).

Compute Unified Device Architecture (CUDA).

Density-Based Spatial Clustering of Applications with Noise (DBSCAN).

Delay-Tolerant Networking (DTN).

End-to-End (E2E).

Expected Calibration Error (ECE).

Exchangeable Image File Format (EXIF).

Floating Point 32-bit (FP32).

Global Positioning System (GPS).

Graphics Processing Unit (GPU).

Hypertext Transfer Protocol (HTTP).

Interagency Integrated Triage Tool (IITT).

Integer 8-bit (INT8).

JSON Canonicalization Scheme (JCS).

JavaScript Object Notation (JSON).

Logistic Regression (LR).

Mean Absolute Error (MAE).

Mebibyte (MiB).

Batch, Channel, Height, Width (NCHW).

Normalized Discounted Cumulative Gain (NDCG).

Natural Language Processing (NLP).

Open Neural Network Exchange (ONNX).

Out-of-Distribution (OOD).

Đuôi tệp chương trình ExecuTorch phục vụ suy luận (PTE).

Post-Training Quantization (PTQ).

Quantization-Aware Training (QAT).

Research Question (RQ).

Round-Trip Time (RTT).

Short Message Service (SMS).

Time To Live (TTL).

Unmanned Aerial Vehicle (UAV).

Write-Ahead Logging (WAL).


## chapters/04-evaluation/sections/local-image-update.tex

Bổ sung kiểm định và thử mức cắt tỉa cao hơn
Phép bổ sung ngày 10/11/2026 giữ bộ ảnh và split 1.189/257/256, dùng checkpoint baseline seed 1024 đã có; không huấn luyện lại baseline hoặc QAT. Pruning chạy trên RTX 5060 Laptop, Python 3.11.9, PyTorch 2.13.0+cu130 và torchvision 0.28.0+cu130. Các số đo suy luận dưới đây dùng CPU một luồng, batch 1, ba lượt làm nóng, chỉ tính lời gọi dự đoán. Đây là lần chạy phát triển trên test đã được xem, khác các phiên CPU và điện thoại lịch sử ở phần trước.

Chọn mức cắt tỉa bằng validation. Ba tỷ lệ mục tiêu 5/10/20% được fine-tune với batch 8, tối đa 35 epoch và early stopping. Trong mỗi tỷ lệ, checkpoint được giữ theo quy tắc accuracy validation và lỗi nặng của script; giữa các tỷ lệ, chọn macro-F1 validation cao nhất, rồi accuracy và tỷ lệ thấp hơn khi hòa. Bảng~ chỉ dùng validation; các ứng viên đều hoãn đánh giá test. Tỷ lệ mục tiêu không bằng phần trăm tổng tham số bị loại do phụ thuộc giữa các nhóm kênh.


Mức 5% được chọn, giảm 8,70% tham số nhưng đạt macro-F1 test 68,14%, thấp hơn baseline 74,26%. Tệp ONNX cùng định dạng giảm từ 16,04 xuống 14,65 MiB (8,68%); không dùng chênh lệch byte giữa hai checkpoint có nội dung đóng gói khác nhau để thay mức giảm này. Model pruning 1% lịch sử trong Bảng~ vẫn là nguồn của benchmark nguyên mẫu; thí nghiệm mới không thay asset trong ứng dụng.

Kiểm định ghép cặp trước và sau pruning. Bảng~ ghép đúng 256 ID ảnh, giữ riêng pruning lịch sử và cấu hình mới. Đ$\to$S là số ảnh từ đúng sang sai, S$\to$Đ là từ sai sang đúng. McNemar exact kiểm thay đổi đúng/sai; CI macro-F1 lấy 2.000 bootstrap draw theo 252 nhóm split. Các CI chưa hiệu chỉnh và nhóm split chưa được chứng minh độc lập theo nguồn/sự kiện. Holm của lịch sử giữ họ 15 tương phản giữa sáu model/runtime đã lưu; lần mới chỉ có một tương phản pruning, không chọn lại họ kiểm định sau khi xem $p$.


Pruning lịch sử tăng Accuracy 4,30 điểm phần trăm nhưng $p$ exact bằng 0,1173 và CI chênh lệch macro-F1 chứa 0, chưa xác lập cải thiện. Với pruning 5% mới, macro-F1 giảm 6,12 điểm, CI $[-12{,}15;-0{,}18]$, trong khi McNemar cho $p=0{,}0704$. Hai thủ tục xét hai đại lượng khác nhau nên không mâu thuẫn; $p>0{,}05$ cũng không chứng minh hai model tương đương. Lỗi nặng tăng từ 3 lên 7, còn median PTH chỉ giảm từ 10,65 xuống 10,35 ms; chưa có phép đo lặp để xác nhận mức tăng tốc nhỏ này ổn định.

Đánh giá lại lượng tử hóa và chẩn đoán tensor. Bảng~ giữ riêng số liệu của phiên local. PTQ mới dùng 200 ảnh train phân tầng để calibration trên baseline ONNX FP32, không phải trên model pruning 5%. QAT là artifact có sẵn được suy luận lại. So tốc độ chỉ trong cùng runtime: FP32 ONNX và PTQ có median 6,55 và 5,01 ms, còn QAT là 19,53 ms. Đây không phải benchmark Android.


PTQ giảm dung lượng xuống 4,51 MiB nhưng macro-F1 còn 64,36%, lỗi nặng tăng 3$\to$17. Recall medium giảm từ 70,00% xuống 36,67%; 25/60 ảnh medium bị gán low. Hiệu macro-F1 PTQ trừ FP32 là $-9{,}90$ điểm, CI $[-15{,}75;-3{,}98]$; McNemar--Holm $p=0{,}0014$ trong họ ba tương phản lượng tử hóa. QAT lịch sử được đánh giá lại đạt macro-F1 41,37% và 49 lỗi nặng; không thay số này vào bảng lịch sử vốn đạt 42,91% và 45 lỗi nặng. Chưa có phân tích đủ để quy nguyên nhân khác biệt giữa hai lần đánh giá.

Chẩn đoán activation dùng một ảnh validation cố định, ghép được 123/416 tensor PTQ và 0/467 tensor QAT. Trong các tensor ghép được, MAE lớn nhất của PTQ nằm ở phép cộng thuộc khối features.10 (2,2818). Độ bao phủ thấp, thang đo activation khác nhau và chỉ một ảnh không đủ cô lập tầng gây giảm chất lượng. Không ghép được tensor QAT không có nghĩa sai số bằng không. Như vậy đã có chẩn đoán bước đầu; nguyên nhân suy giảm và chất lượng trên camera độc lập vẫn còn mở.


## chapters/04-evaluation/sections/vi-silver-pilot.tex

Pilot tiếng Việt dịch và nhãn AI cho yêu cầu hỗ trợ
Phép bổ sung này thực nghiệm nhận diện lời yêu cầu hoặc nhu cầu hỗ trợ thiên tai trên \textbf{văn bản dịch sang tiếng Việt và nhãn do AI gán}. Ảnh và văn bản gốc lấy từ cùng bài đăng CrisisMMD~; đây không phải corpus người dân Việt Nam gửi tin. Nhãn request bao gồm lời kêu gọi cứu, sơ tán, cung cấp vật phẩm, quyên góp hoặc nhu cầu hỗ trợ chưa được đáp ứng; không phải mức nguy cấp hay ưu tiên điều phối. Nhãn informative của pilot trước không được chuyển thành request.

Dữ liệu và cách tạo nhãn. Từ cohort CrisisMMD đã kiểm, chọn 300 cặp theo hash trong từng split sự kiện, một cặp cho mỗi nhóm bản trùng. Một nửa mỗi split được chọn từ các câu có từ khóa rộng về hỗ trợ, nửa còn lại từ các câu khác. Đây là lấy mẫu làm giàu chủ đề, không phản ánh prevalence tự nhiên. AI dịch và gán một nhãn cho từng câu nguồn trong một lượt, kèm lý do; không xem ảnh để gán nhãn. Các lượt được chia thành ba phần để xử lý, không phải ba người gán cùng mẫu và không tạo chỉ số đồng thuận. Bốn câu chưa rõ nghĩa được giữ trong inventory và loại trước fit, không lấy bù. Còn 179 train, 58 validation và 59 test; test có 6 request và 53 no\_request.

Giữ Sri Lanka làm test, Maria làm validation, năm sự kiện khác làm train; bản sao, ID, hash ảnh và câu dịch được kiểm không giao nhau giữa split. Tập sự kiện này từng được xem trong pilot informative nên đây là bằng chứng phát triển hồi cứu. Nguồn mô tả corpus tiếng Anh nhưng chưa kiểm ngôn ngữ từng hàng; lỗi encoding hoặc dịch có thể ảnh hưởng nhãn. Bản dịch và nhãn AI không phải gold do người độc lập hoặc chuyên gia xác nhận. Vì nhãn dựa vào câu nguồn, phép so sánh đo khớp nhãn văn bản AI của báo cáo, không chứng minh hiểu đúng cả ảnh và câu.

Mô hình đã chạy. TF-IDF thử word unigram/bigram và char 3--5; vocabulary chỉ fit train. Nhánh văn bản frozen dùng DistilBERT đa ngôn ngữ~, mean pooling có attention mask và 768 chiều. Nhánh ảnh dùng MobileNetV3-Large ImageNet frozen, 960 chiều, khác encoder Small của pilot informative và khác classifier mức ngập trong ứng dụng. Các nhánh đơn và fusion frozen chuẩn hóa L2; fusion nối hai block rồi chia $\sqrt{2}$, học LR cân bằng lớp với $C\in\{0{,}1;1;10\}$. Có 18 fit head được chọn bằng macro-F1 validation; ngưỡng giữ 0,5. DistilBERT frozen được chọn làm đối chứng chính từ validation trước test, không chọn lại theo kết quả test.

Nhánh riêng fine-tuning DistilBERT cập nhật encoder và đầu hai lớp trên cùng nhãn AI. Protocol bổ sung khóa trước dự đoán test: hai learning rate $10^{-5}$ và $2\times10^{-5}$, ba seed 17/29/43, tối đa năm epoch, patience 2, batch hiệu dụng 16 và dropout 0,2. Chọn learning rate theo trung bình validation của ba seed, giữ cả ba checkpoint tương ứng; không chỉ báo seed có test tốt nhất. Bảng kết quả dùng lần tái chạy CUDA ngày 10/11/2026 trên RTX 5060 Laptop, chọn $2\times10^{-5}$; kiểm tra một tensor backbone ở mỗi checkpoint xác nhận trọng số thay đổi. Lần thực thi trước trên cùng dữ liệu đạt macro-F1 trung bình 50,73% và được giữ riêng trong hồ sơ tái lập, không coi hai lần là hai bộ test độc lập. Nhánh này không fine-tuning chung encoder ảnh--văn bản và không thay đổi tương phản chính của fusion frozen.

Bảng~ trình bày các kết quả đã chạy trên cùng 59 ID; recall $(+)$ là recall request. Hàng fine-tuning là trung bình ba seed, không tăng số cặp test độc lập lên ba lần. Hai hàng cuối chỉ che một block của fusion cố định, khác chuyển sang classifier đơn.


Fusion frozen đạt macro-F1 64,91% và recall request 33,33%; nó dự đoán đúng hai trong sáu nhãn request, bỏ sót bốn. Lớp đa số đạt Accuracy 89,83% nhưng recall request bằng không; vì vậy Accuracy riêng lẻ dễ che lỗi bỏ sót trong test lệch lớp. Fine-tuning DistilBERT đạt macro-F1 trung bình 52,29%, khoảng min--max giữa seed $[52,29Low;52,29High]$, recall request trung bình 22,22%; mỗi seed nhận đúng một hoặc hai trong sáu request. Đây là biến động huấn luyện trên cùng dữ liệu, không phải CI qua nhiều quần thể. Điểm T2 thấp hơn fusion frozen trong lần đánh giá này chưa phải một kiểm định chênh lệch giữa hai phương pháp.

Bảng~ dùng 2.000 bootstrap draw ghép cặp theo 59 nhóm test, cùng draw cho mọi cấu hình. Các CI 95% chưa hiệu chỉnh, có điều kiện trong một sự kiện và đối với nhãn AI; chúng không bao gồm sai số dịch hoặc sai nhãn. Hiệu fusion so với DistilBERT frozen là 20,78 điểm phần trăm, CI $[-3,93;42,65]$. Các CI đều chứa hoặc chạm 0, chưa xác lập ưu thế fusion. Không áp dụng tương phản này để so trực tiếp lợi ích fine-tuning với fusion có encoder cố định.


Khi che ảnh, fusion dự đoán lớp âm cho toàn bộ test và bỏ sót cả sáu request; classifier text đơn dự đoán đúng một request. Đây là dấu hiệu chính sách thiếu nguồn phải được đánh giá riêng, không được gọi việc che block là fallback đã hoạt động. Kết quả được kiểm lại từ dự đoán full precision và công thức confusion/F1 độc lập với hàm tính metric chính. Kiểm tính toán không xác nhận nhãn AI đúng nghiệp vụ. Pilot bổ sung bằng chứng đã chạy NLP, fine-tuning và fusion trên tiếng Việt dịch; corpus bản địa, nhãn người độc lập, trích xuất span có gold, tích hợp ứng dụng, Android và hiệu quả cứu hộ thực địa vẫn chưa được đánh giá.


## frontmatter/research-body-en.tex


\FormIndented{Project code: \ProjectCode}
\FormIndented{Project title: \ProjectTitleEnglish}
\FormIndented{Project coordinator: \PrincipalName}
\FormIndented{Implementing institution: \PrincipalUnit}
\FormIndented{Duration: \ProjectPeriodEnglish{} (six months).}


Develop an AI-based mobile system to receive and analyze flood rescue information and support decision-making under unstable network conditions, with the aim of reducing loss of life and property damage.


The project proposes an integrated approach combining multimodal data analysis, Edge AI and intelligent rescue-event clustering within a unified system.

Instead of relying entirely on centralized server processing, the proposed system aims to perform AI inference directly on mobile devices using optimized lightweight deep learning models, thereby reducing computational requirements and the transmission of large data files.

Furthermore, the integration of location, time and rescue information for identifying and grouping related events is intended to reduce duplicate reports and support visualization of rescue situations on a digital map.


On 256 test images, the seed-1024 baseline achieved 75.78% accuracy and 74.26% macro-F1 with three critical errors. Historical pruning reached 80.08% accuracy with 4 critical errors; exact McNemar $p=0.1173$ did not establish improvement. An additional 5/10/20% pruning grid selected 5% using validation, but test macro-F1 fell to 68,14%. Partial PTQ/QAT tensor diagnostics have not isolated the cause of degradation.

Additional ONNX CPU screening of the pruned model used the same 256 images and eight synthetic corruptions. Macro-F1 decreased from 78,26% on clean images to 68,04% at 0.4 brightness. This does not establish robustness on Android or field camera images; inherited corruption labels have not been re-adjudicated.

The app sends image labels and the LR score for storage; the adapter uses urgency or description keywords for clustering/ranking. Five-flag LR fitted to synthetic OR labels is not free-text NLP. The English CrisisMMD informativeness pilot reaches text/fusion macro-F1 of 76,60%/78,35%; effect CIs include zero.

A separate AI-translated Vietnamese/AI-silver pilot uses 179 training, 58 development and 59 test pairs. Frozen fusion reaches 64,91% macro-F1 and 33,33% request recall. A CUDA DistilBERT fine-tuning replay averages 52,29% macro-F1 and 22,22% request recall across three seeds on the same test set. Native-Vietnamese data, independent human gold, information extraction and application fusion remain unvalidated.

In weak-network simulations with bandwidth of 50 kbit/s and a round-trip time of 600 ms, both metadata-only and compressed-image modes succeeded in 257/257 attempts (100%), compared with 230/257 (89.49%) for original images. The two modes transmitting less data achieved higher transmission success rates than original images under the tested conditions. Each mode was measured separately on a computer; transmission over real mobile networks requires further validation.

RQ1 does not establish Product superiority over independently selected Additive (ARI 0.9072 versus 0.9191; Holm p=0.2560). RQ2 supports exact-copy invariance under fixed grouping, without establishing general alignment gains (revised NDCG@5 0.6669 versus random 0.6763). Across 40 seed-level pairs, revised priority performs worse than nearest-first on simulated harm and deadline misses. Three raw Spearman p-values and five related Holm values remain unreconciled in RQ2 replay.

The available results demonstrate the feasibility of selected prototype components in a research environment. They do not yet establish improvements in real-world rescue coordination or disaster response effectiveness.


The project registers three main scientific and technological products:
\FormIndented{-- A mobile application supporting disaster rescue, integrating AI models and rescue request submission functions.}
\FormIndented{-- A web-based rescue information management system featuring a digital map for visualizing rescue locations and clustering related events.}
\FormIndented{-- A trained and optimized multimodal AI model package for analyzing rescue information and supporting deployment on mobile devices.}
\par\noindent The model package is registered; the image model, structured LR and separate CrisisMMD pilot do not establish completion of Vietnamese NLP and rescue fusion in the application.
\par\noindent In addition, the project registers a research bulletin, a research summary and a demonstration video of no more than two minutes, in accordance with Can Tho University's requirements. The paper ``Stress-Testing Product-Gated Clustering and Bounded Priority Ranking for Flood-Rescue Reports: A Synthetic Study'' has been published in the ISDS 2026 proceedings, Part II, in Communications in Computer and Information Science (CCIS), volume 3253, Springer Nature, 2026.


The outputs support education and research in edge image inference and rescue information management, with planned transfer to Can Tho University's School of Information and Communication Technology. Before field pilots, text processing, fusion, device and network behavior, synchronization and event clustering require validation with rescue professionals. Real-world rescue effectiveness and socioeconomic benefits remain unmeasured.
