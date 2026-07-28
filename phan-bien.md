
# Báo cáo phản biện độc lập

**Khuyến nghị: Reject and Resubmit**
**Điểm tổng thể: 4/10**
**Độ tự tin: High**

Lý do chính không phải do số liệu trong bài bị bịa hoặc chép sai. Phần lớn số headline khớp JSON. Vấn đề nằm ở tính hợp lệ của đóng góp trung tâm: cận toán học đang được diễn giải rộng hơn điều thực sự chứng minh; so sánh đa-seed chưa công bằng sau hiệu chỉnh; dữ liệu synthetic được thiết kế theo đúng cấu trúc của phương pháp; và priority score có lỗi quan trọng khi confidence không tác động lên vulnerability.

## A. Tóm tắt bài báo và đóng góp được tuyên bố

Bài báo đề xuất pipeline gồm:

1. Biểu diễn mỗi báo cáo cứu hộ bằng \(L,T,F,E,N,V,C\).
2. Xây dựng đồ thị với trọng số\[
   w^\times_{ij}=S_{\mathrm{geo}}\left(\beta S_{\mathrm{temp}}+\gamma S_{\mathrm{ctx}}\right).
   \]
3. Cắt ngưỡng, giữ k-NN, rồi phân cụm bằng Louvain/Leiden.
4. Xếp hạng cụm bằng điểm ưu tiên có hệ số khuếch đại vulnerability.
5. Đánh giá trên 485 báo cáo synthetic và 20 hình học được tái sinh.

Bài không còn tuyên bố product kernel tự thân là mới; đóng góp chính được đặt vào:

* Bổ đề định vị cạnh và cận đường kính có điều kiện.
* Pipeline phân cụm–xếp hạng cho cứu hộ.
* Thực nghiệm synthetic với so sánh product/additive, baseline, confidence và dispatch.

Định vị “kernel form không mới” tại [main.tex (line 53)](/home/ngthtrong/nckh2/paper/main.tex:53) là trung thực và hợp lý.

## B. Đánh giá tổng quan

Bài đã được cải thiện đáng kể về tính tự phê bình: thừa nhận additive có thể đạt kết quả tốt sau calibration, confidence yếu, Edge AI chưa được đánh giá, và chưa có dữ liệu thật. Truy vết số liệu cũng tốt.

Tuy nhiên, đối với một ấn phẩm Springer/Springer Nature có phản biện nghiêm túc, bản hiện tại chưa sẵn sàng vì:

* Đóng góp toán học mới chỉ là một cận cạnh đơn giản; phần cận cụm không cho compactness ex ante nếu không khống chế hop-diameter \(h\).
* Phát biểu “additive không có guarantee tương tự” sai nếu hiểu cho mọi miền ngưỡng.
* So sánh product–additive đa-seed chỉ dùng chung \(\theta=0.05\), dù chính bài xác nhận ngưỡng này giữ gần như toàn bộ cạnh additive.
* Dữ liệu synthetic và tiêu chí “hardness” được đồng thiết kế với phương pháp.
* Priority score cộng dân số/vulnerability qua nhiều báo cáo mà không xử lý trùng nạn nhân; confidence bỏ qua vulnerability hoàn toàn.
* Kết quả dispatch sử dụng thước đo được xây từ chính các biến mà priority score tối ưu.
* Baseline và ablation chưa đủ để định vị so với phương pháp spatio-temporal/multiple-kernel phù hợp.
* Khả năng tái lập ở mức mã nguồn tốt hơn tài liệu hướng dẫn, nhưng README và môi trường phụ thuộc đang lỗi thời.

## C. Điểm mạnh

* Bổ đề cạnh \(w^\times>\theta\Rightarrow d<r_\theta\) là đúng dưới \(\beta+\gamma\le1\); chứng minh tại [main.tex (line 177)](/home/ngthtrong/nckh2/paper/main.tex:177) ngắn gọn và hợp lệ.
* Bài chủ động thu hẹp tuyên bố, đặc biệt tại [main.tex (line 470)](/home/ngthtrong/nckh2/paper/main.tex:470).
* Số liệu ARI/NMI/CI đa-seed khớp [exp12_multiseed_summary.json (line 3)](/home/ngthtrong/nckh2/demo/results/tables/exp12_multiseed_summary.json:3).
* Kết quả confidence được báo cáo trung thực: AUC 0.6919, AP 0.1546 và failure mode của fake campaign tại [exp8_confidence_detector.json (line 3)](/home/ngthtrong/nckh2/demo/results/tables/exp8_confidence_detector.json:3).
* Bài phân biệt hợp lý giữa ARI trên điểm có nhãn, noise absorption và đường kính cụm.
* Traceability tại [traceability.md](/home/ngthtrong/nckh2/loop/loop17/traceability.md) hữu ích.
* Kiểm tra độc lập cho thấy tám hình trong bài khớp checksum với tám hình trong `demo/results/figures`.
* Bản PDF hiện tại biên dịch thành công 12 trang, không có citation/reference thiếu; xem [main.log (line 634)](/home/ngthtrong/nckh2/paper/main.log:634).
* Phần thảo luận không biến kết quả synthetic thành bằng chứng triển khai thực địa.

## D. Các vấn đề nghiêm trọng — Major Concerns

### MC1. Phạm vi đóng góp toán học bị diễn giải rộng hơn kết quả thực sự

* **Loại phát hiện:** Một phần là lỗi logic được chứng minh; một phần là tuyên bố chưa đủ bằng chứng.
* **Bằng chứng:** Bổ đề tại [main.tex (line 177)](/home/ngthtrong/nckh2/paper/main.tex:177); tuyên bố đóng góp tại [main.tex (line 63)](/home/ngthtrong/nckh2/paper/main.tex:63); phát biểu về additive tại [main.tex (line 199)](/home/ngthtrong/nckh2/paper/main.tex:199).
* **Vấn đề:**
  * Cận cạnh là đúng.
  * Cận cụm \(h r_\theta\) phụ thuộc hop-diameter \(h\), nhưng pipeline không cưỡng chế \(h\). Do đó không có một cận compactness hữu dụng biết trước dữ liệu, ngoài cận rất lỏng \(h\le n-1\).
  * Trên seed 42 tôi tính lại: \(r_\theta=1.713\) km, hop-diameter lớn nhất bằng 5, nên cận lớn nhất là 8.57 km, trong khi đường kính thực là 4.98 km. Nghĩa là default không bảo đảm tiêu chí vận hành 5 km mà Exp13 sử dụng.
  * Additive thực ra có cận khi \(\theta>\beta+\gamma\):\[
    w^+>\theta\Rightarrow
    d<\sigma\sqrt{2\ln\frac{\alpha}{\theta-(\beta+\gamma)}},
    \]khi vế phải xác định. Khác biệt đúng là additive không có cận hữu hạn cho toàn bộ miền \(0<\theta<1\), không phải “không có guarantee tương tự” trong mọi trường hợp.
  * Thí nghiệm đếm violation dùng cả \(\theta\ge1\), dù bổ đề chỉ định nghĩa \(0<\theta<1\). Hàm mã trả cutoff bằng 0 cho \(\theta\ge1\) tại [weighting.py (line 155)](/home/ngthtrong/nckh2/demo/pipeline/weighting.py:155). Với additive \(\alpha=.5\), 30/79 ngưỡng nằm ngoài miền; 22 ngưỡng như vậy bị tính là violation. Kết luận định tính vẫn đứng vì trong miền hợp lệ additive vi phạm 49/49, nhưng số “71/79” không phải phép kiểm thuần túy của bổ đề.
* **Vì sao nghiêm trọng:** Đây là đóng góp trung tâm mà abstract và conclusion dựa vào. Nếu chỉ còn cận cạnh Gaussian cùng triangle inequality, độ mới lý thuyết khá mỏng.
* **Mức độ:**  **High** .
* **Cách sửa:**
  * Đổi “cluster guarantee” thành “edge-localization guarantee”, trừ khi bổ sung ràng buộc hop-diameter/graph-diameter.
  * Nêu định lý additive theo từng miền ngưỡng.
  * Chỉ đánh giá violation trong \(0<\theta<1\), hoặc chuẩn hóa rõ miền trọng số.
  * Báo cáo \(h\), \(h r_\theta\), đường kính thực và độ chặt trên mọi seed.
* **Tiêu chí xác nhận:** Phát biểu mới đúng với mọi tham số cho phép; proof và mã dùng cùng bất đẳng thức/ngưỡng; không còn số violation ngoài miền định lý; nếu vẫn tuyên bố compact cluster thì pipeline phải cưỡng chế hoặc kiểm chứng một \(h_{\max}\) vận hành.

### MC2. So sánh product–additive đa-seed chưa công bằng sau calibration

* **Loại phát hiện:** Được chứng minh từ mã và JSON.
* **Bằng chứng:** Exp12 cố định product và additive \(\alpha=1\) tại cùng default trong [exp12_multiseed.py (line 52)](/home/ngthtrong/nckh2/demo/experiments/exp12_multiseed.py:52). Bài thừa nhận \(\theta=.05\) giữ 10.85% cạnh product nhưng 95.69–97.97% cạnh additive tại [main.tex (line 378)](/home/ngthtrong/nckh2/paper/main.tex:378).
* **Vấn đề:**
  * CI và Wilcoxon đa-seed chỉ trả lời “hai cấu hình default này có khác nhau không”, không trả lời “hai họ phương pháp có khác nhau sau hiệu chỉnh công bằng không”.
  * Calibration theo từng dạng chỉ chạy trên seed 42 và chọn `best_ari` trên toàn sweep tại [exp13_theta_calibration.py (line 211)](/home/ngthtrong/nckh2/demo/experiments/exp13_theta_calibration.py:211), không có train/test hoặc nested calibration.
  * Trong vùng “usable”, product tại \(\theta=.39\) có ARI 0.9731, NMI 0.9805, max diameter 3.583 km [exp13_sweep_gating.json (line 250)](/home/ngthtrong/nckh2/demo/results/tables/exp13_sweep_gating.json:250). Additive \(\alpha=.5\) tại \(\theta=.96\) có cùng ARI/NMI, nhưng max diameter nhỏ hơn, 3.290 km [exp13_sweep_additive_alpha05.json (line 614)](/home/ngthtrong/nckh2/demo/results/tables/exp13_sweep_additive_alpha05.json:614).
  * Bảng calibration trộn “best ARI trên toàn sweep” với “usable window”. Vì vậy additive \(\alpha=.5\) được ghi best ARI 0.9768 tại \(\theta=.90\), dù điểm đó có max diameter 40.72 km và không usable [exp13_theta_calibration_best.json (line 32)](/home/ngthtrong/nckh2/demo/results/tables/exp13_theta_calibration_best.json:32).
* **Vì sao nghiêm trọng:** Tất cả bằng chứng thống kê về ưu thế product hiện xuất phát từ một default đã được chứng minh là không cùng mật độ đồ thị.
* **Mức độ:**  **Critical** .
* **Cách sửa:**
  * Chia seed thành calibration/test hoặc dùng nested cross-seed calibration.
  * Tuning cùng ngân sách cho \(\theta,\alpha,\sigma,\tau,k,\) resolution.
  * So sánh thêm ở matched retained-edge fraction, matched average degree và cùng operational constraints.
  * Báo cáo phân phối test-seed sau calibration, không chọn best trên test.
* **Tiêu chí xác nhận:** Product vẫn có lợi ích trên seed chưa dùng để tuning; CI ghép cặp của chênh lệch test-seed loại 0, hoặc bài hạ tuyên bố xuống “không có khác biệt thực nghiệm sau calibration”.

### MC3. Synthetic benchmark có tính nội sinh cao và chưa có external validity

* **Loại phát hiện:** Thiếu bằng chứng độc lập; thiết kế nội sinh được chứng minh từ generator.
* **Bằng chứng:** Generator mô tả rõ các cặp được thiết kế để “chỉ \(S_{\rm context}\) tách được” và “chỉ \(S_{\rm temp}\) tách” tại [generate.py (line 91)](/home/ngthtrong/nckh2/demo/data/generate.py:91). Exp0 quy định nếu gate không đạt thì sửa generator tại [exp0_dataset_hardness.py (line 3)](/home/ngthtrong/nckh2/demo/experiments/exp0_dataset_hardness.py:3).
* **Vấn đề:**
  * Ground truth được tạo từ đúng các biến mà phương pháp sử dụng: địa lý, thời gian, \(F,E\).
  * “Context ablation matters” gần như là thuộc tính thiết kế của generator.
  * Việc lặp generator cho đến khi các gate đạt không tương đương preregistration độc lập. Không có protocol được đóng dấu thời gian hoặc tập benchmark bất biến trước lựa chọn phương pháp.
  * Multi-seed chỉ thay geometry, spread và group size trong cùng một họ generator; context profiles, fake mechanism, số sự kiện và quy tắc ground truth cơ bản không đổi.
  * Không có sanity check trên báo cáo lũ thật.
* **Vì sao nghiêm trọng:** Hai trụ cột “hard benchmark” và “flood-rescue application” chưa được kiểm chứng ngoài thế giới do tác giả tự tạo.
* **Mức độ:**  **Critical** .
* **Cách sửa:**
  * Thêm ít nhất một tập geolocated, time-resolved flood/crisis reports thật với annotation incident-level độc lập.
  * Nếu không thể công bố dữ liệu nhạy cảm, cung cấp protocol de-identification, annotation và thống kê aggregate.
  * Bổ sung generator ngoài mô hình của tác giả hoặc benchmark do nhóm khác tạo.
  * Đổi “pre-registered” thành “pre-specified in the released code” nếu không có preregistration thật.
* **Tiêu chí xác nhận:** Kết quả chính được tái hiện trên ít nhất một nguồn dữ liệu ngoài generator; annotation không sử dụng trực tiếp công thức product kernel; có inter-annotator agreement và phân tích lỗi.

### MC4. Priority score có lỗi confidence-bypass và giả định cộng báo cáo không hợp lệ

* **Loại phát hiện:** Lỗi được chứng minh trong mã; construct validity chưa có.
* **Bằng chứng:** \(E,F,N\) được nhân confidence, nhưng `v_sum` cộng vulnerability thô tại [priority.py (line 93)](/home/ngthtrong/nckh2/demo/pipeline/priority.py:93). Bài lại nói confidence “downweights inputs to the priority score” tại [main.tex (line 152)](/home/ngthtrong/nckh2/paper/main.tex:152).
* **Vấn đề:**
  * Một báo cáo confidence thấp vẫn có thể đặt \(V_i\) lớn và khuếch đại toàn bộ priority.
  * Generator đặt vulnerability của mọi fake report bằng 0 tại [generate.py (line 265)](/home/ngthtrong/nckh2/demo/data/generate.py:265) và [generate.py (line 304)](/home/ngthtrong/nckh2/demo/data/generate.py:304), nên thí nghiệm không thể phát hiện lỗ hổng này.
  * \(\sum_i N_iC_i\) và \(\sum_iV_i\) coi nhiều báo cáo về cùng một physical event là các nhóm nạn nhân không trùng nhau. Đây là giả định đặc biệt nguy hiểm trong bài toán mà mục tiêu ban đầu chính là hợp nhất báo cáo trùng.
  * Generator gán `n_trapped` Poisson độc lập cho từng báo cáo tại [generate.py (line 193)](/home/ngthtrong/nckh2/demo/data/generate.py:193), nhưng không có ground-truth unique population ở cấp incident.
  * \(\widetilde E=|C|^{-1}\sum E_iC_i\) không phải weighted mean theo confidence; spam confidence thấp có thể làm giảm urgency trung bình do mẫu số vẫn tăng.
* **Vì sao nghiêm trọng:** Priority score là một đóng góp được tuyên bố riêng. Sai số đếm trùng và confidence-bypass có thể đảo thứ tự dispatch.
* **Mức độ:**  **Critical** .
* **Cách sửa:**
  * Mô hình hóa population/vulnerability ở cấp incident với deduplication hoặc khoảng bất định.
  * Confidence phải tác động nhất quán lên mọi thuộc tính do báo cáo cung cấp, hoặc tác giả phải chứng minh vì sao \(V\) đáng tin tuyệt đối.
  * Thêm adversarial tests cho inflated \(V,N,F,E\), duplicate reports và fake campaign.
  * Xác lập \(\omega,\mu,s,N_{\rm ref}\) bằng expert elicitation hoặc outcome calibration.
* **Tiêu chí xác nhận:** Không báo cáo confidence thấp nào có thể tăng priority không giới hạn qua \(V\); unique population được định nghĩa; kết quả priority ổn định dưới duplicate/adversarial reports; công thức được chuyên gia nghiệp vụ xác nhận.

### MC5. Dispatch simulation chưa phải bằng chứng khoa học cho tính đúng của priority score

* **Loại phát hiện:** Thiếu construct validity; có dấu hiệu báo cáo trade-off chưa đầy đủ.
* **Bằng chứng:** Thước đo chính dùng vulnerability và ngưỡng flood tại [exp7_equity_outcome.py (line 61)](/home/ngthtrong/nckh2/demo/experiments/exp7_equity_outcome.py:61), trong khi hai biến này cũng nằm trong priority score.
* **Vấn đề:**
  * Metric “severe-flood vulnerable time” thưởng trực tiếp việc xếp vulnerability và flood cao lên trước. Nó không độc lập về khái niệm với công thức đang được đánh giá.
  * Product cải thiện metric này 14.82 phút so với bỏ vulnerability, nhưng mean arrival all tăng từ 374.38 lên 399.18 phút, tức xấu hơn 24.80 phút [exp7_equity_outcome.json (line 37)](/home/ngthtrong/nckh2/demo/results/tables/exp7_equity_outcome.json:37).
  * Product cũng kém additive trên `time_to_vulnerable` — 297.44 so với 288.80 phút — trong khi không khác biệt trên metric chính giữa hai cách dùng \(V\).
  * Bài chỉ nhấn mạnh lợi ích 14.82 phút tại [main.tex (line 434)](/home/ngthtrong/nckhtrong/nckh2/paper/main.tex:434) mà không trình bày đầy đủ chi phí hiệu quả tổng thể.
  * Không có casualties avoided, service completion, capacity, route feasibility, waterway accessibility hoặc stochastic travel time.
* **Vì sao nghiêm trọng:** Một heuristic được đánh giá bằng metric xây từ cùng biến đầu vào có nguy cơ tự xác nhận.
* **Mức độ:**  **High** .
* **Cách sửa:**
  * Xác định utility/outcome độc lập trước thí nghiệm.
  * Báo cáo Pareto frontier giữa equity, severe-vulnerability arrival và mean/makespan.
  * Sử dụng nhiều kịch bản travel/service stochastic và demand capacity.
  * Điều chỉnh multiple comparisons hoặc công bố rõ một primary endpoint preregistered.
* **Tiêu chí xác nhận:** Lợi ích tồn tại trên outcome độc lập; trade-off tổng thể được báo cáo; kết luận không dựa duy nhất vào metric đồng cấu với score.

### MC6. Baseline và ablation chưa đủ mạnh

* **Loại phát hiện:** Thiếu bằng chứng.
* **Bằng chứng:** Baseline chỉ chạy seed 42 tại [exp4_baselines.py (line 23)](/home/ngthtrong/nckh2/demo/experiments/exp4_baselines.py:23); DBSCAN chỉ có vài giá trị eps, HDBSCAN chỉ có `min_cluster_size=3`.
* **Vấn đề:**
  * HDBSCAN/Spectral/Agglomerative “same graph” dùng chính representation product-gating, nên chỉ kiểm tra thuật toán phân hoạch chứ không kiểm tra đóng góp representation.
  * K-Means/DBSCAN tọa độ hoặc tọa độ+\(F,E\) bỏ thời gian và không được tuning tương xứng.
  * ClustGeo/regionalization được trích dẫn nhưng không chạy.
  * Thiếu baseline spatio-temporal trực tiếp như [ST-DBSCAN](https://doi.org/10.1016/j.datak.2006.01.013).
  * Thiếu học/hiệu chỉnh tổ hợp kernel. Multiple-kernel clustering là một dòng phương pháp lớn, ví dụ [Fusion Multiple Kernel K-means, AAAI 2022](https://ojs.aaai.org/index.php/AAAI/article/view/20896).
  * Không có ablation bỏ hoàn toàn geography, bỏ time, hoặc factorial ablation. Context ablation chỉ ở một seed; confidence không được ablate trên dispatch outcome.
* **Vì sao nghiêm trọng:** Không thể xác định lợi ích đến từ product form, scale/threshold, k-NN, Louvain hay thiết kế feature.
* **Mức độ:**  **High** .
* **Cách sửa:** Tuning baseline với cùng ngân sách; đánh giá đa-seed; thêm ST-DBSCAN/ClustGeo hoặc spatially constrained baseline; factorial ablation cho geo/time/context/kNN/confidence; báo cáo chi phí và noise convention thống nhất.
* **Tiêu chí xác nhận:** Baseline mạnh được tuning trên train và chấm trên test; mỗi thành phần có effect size và CI; không baseline nào bị bất lợi chỉ vì thang trọng số/ngưỡng.

### MC7. ARI cao che khuất output fragmentation và noise burden

* **Loại phát hiện:** Kết quả được chứng minh nhưng chưa được diễn giải đầy đủ.
* **Bằng chứng:** Proposed Louvain tạo 52 cụm cho 13 physical events, gồm 39 singleton, 38 noise-only clusters, và hấp thụ 40.62% noise vào cụm có nhãn tại [exp4_baselines.json (line 3)](/home/ngthtrong/nckh2/demo/results/tables/exp4_baselines.json:3).
* **Vấn đề:**
  * ARI/NMI loại toàn bộ 64 điểm `gt=-1`.
  * “Automatic \(K\)” là 52, không phải 13; con số này phần lớn phản ánh noise handling.
  * Đa-seed trung bình tạo 55.15 cụm và 41.85 singleton [exp12_multiseed_summary.json (line 129)](/home/ngthtrong/nckh2/demo/results/tables/exp12_multiseed_summary.json:129).
  * Nhãn multimodal có ARI 0 trên seed 42 tại [exp1_G_ari_decomposition.json (line 6)](/home/ngthtrong/nckh2/demo/results/tables/exp1_G_ari_decomposition.json:6).
  * Từ `exp12_multiseed_per_seed.json`, tôi đếm được 19/20 seed có ít nhất một ground-truth group bị split; cặp 4–5 bị merge ở 12/20 seed. Những error signatures này chưa được đưa vào bài.
* **Vì sao nghiêm trọng:** Hệ thống có thể tạo hàng chục “điểm đến” giả hoặc bỏ sót incident multimodal dù ARI tổng thể rất cao.
* **Mức độ:**  **High** .
* **Cách sửa:** Báo cáo event-level precision/recall, split/merge rates, false dispatch destinations, noise rejection, số cụm cần operator xem xét; đưa error structure đa-seed vào bài.
* **Tiêu chí xác nhận:** Đánh giá bao phủ toàn bộ báo cáo, không chỉ điểm có nhãn; output burden và split/merge có CI; tuyên bố “automatic K” được diễn giải đúng.

### MC8. Tái lập chưa đạt chuẩn artifact công bố

* **Loại phát hiện:** Lỗi tài liệu và thiếu provenance.
* **Bằng chứng:** Root README vẫn mô tả dataset 285 báo cáo và ARI 0.892 tại [README.md (line 35)](/home/ngthtrong/nckh2/README.md:35). `demo/README.md` dùng đường dẫn `demo/v2`, file `PaperV2.md` không tồn tại và dataset cũ tại [demo/README.md (line 1)](/home/ngthtrong/nckh2/demo/README.md:1).
* **Vấn đề:**
  * Không có `requirements.txt`, lockfile, container hoặc version pin.
  * Paper không có code/data availability URL, commit hash hoặc DOI.
  * README nói chạy 10 nhóm thí nghiệm và sinh 7 hình, nhưng `run_all.py` chạy 14 nhóm/17 bước và bài dùng 8 hình.
  * Hướng dẫn biên dịch dùng pdfLaTeX, trong khi PDF hiện hành được tạo bằng XeLaTeX.
  * `paper/log_final.txt` là log cũ 20 trang/285 events; log hiện hành là `main.log`.
  * Tuyên bố “one CPU core” tại [main.tex (line 454)](/home/ngthtrong/nckh2/paper/main.tex:454) không được mã ép số thread, và JSON không lưu CPU/RAM/BLAS, số lần lặp hoặc warm-up.
  * Packet 105–111 byte dùng confidence placeholder 0.9 tại [exp10_packet_size.py (line 18)](/home/ngthtrong/nckh2/demo/experiments/exp10_packet_size.py:18).
* **Vì sao nghiêm trọng:** Reviewer độc lập khó bảo đảm tạo đúng artifacts trên môi trường mới.
* **Mức độ:**  **Medium–High** .
* **Cách sửa:** Đồng bộ README; pin dependency; lưu environment/hardware; thêm một lệnh clean-room; public repository/DOI/commit; tạo manifest kết quả và checksum.
* **Tiêu chí xác nhận:** Một môi trường sạch chạy toàn pipeline, tái tạo JSON/hình trong dung sai xác định và biên dịch PDF theo đúng hướng dẫn.

## E. Các vấn đề nhỏ — Minor Concerns

* Mã threshold dùng `out[out < theta]=0`, tức giữ cạnh bằng đúng \(\theta\), trong khi bài và proof dùng \(w>\theta\); xem [weighting.py (line 265)](/home/ngthtrong/nckh2/demo/pipeline/weighting.py:265).
* “Product kernel” có thể bị hiểu là Mercer/PSD kernel. Bài chưa chứng minh tính PSD của Gaussian dùng Haversine; nên gọi “product similarity” hoặc làm rõ nghĩa của “kernel”.
* \(\beta+\gamma<1\) cho một cận chặt hơn cận đang viết; nên nêu bản tổng quát.
* `N_ref=500` làm mọi cluster trên mốc này có cùng population contribution; cần thảo luận saturation.
* Centroid được tính bằng trung bình lat/lng, chưa phù hợp khi cụm lớn hoặc lệch dạng.
* Bootstrap dùng cùng seed 42 cho nhiều phép phân tích; tái lập được nhưng cần ghi rõ.
* Các kiểm định trên nhiều metric chưa có điều chỉnh family-wise/FDR.
* “Mean \(\pm\) SD” và “95% CI” xuất hiện sát nhau; cần tránh để người đọc nhầm SD với CI.
* Bảng positioning có ký hiệu `\sim` chủ quan và chưa định nghĩa.
* Phần related work chưa đủ sâu để chứng minh novelty của lemma so với similarity-graph sparsification và spatial-constrained clustering.
* Packet-size experiment chưa gồm schema version, provenance, uncertainty, authentication hoặc transport overhead.
* Một số comment mã vẫn nói dataset/cấu trúc cũ; không ảnh hưởng số chạy nhưng làm giảm độ tin cậy bảo trì.

## F. Đánh giá chi tiết theo sáu tiêu chí

| Tiêu chí                                     | Điểm         | Đánh giá                                                                                                                                                                 |
| ---------------------------------------------- | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tính mới và ý nghĩa đóng góp           | **4/10** | Product form được thừa nhận là kỹ thuật đã có. Cận cạnh đúng nhưng đơn giản; cận cụm có điều kiện và chưa tạo compactness guarantee hữu dụng. |
| Độ chặt chẽ kỹ thuật và toán học      | **4/10** | Proof cạnh đúng; phát biểu additive quá rộng, violation sweep lẫn miền\(\theta\ge1\), priority có confidence-bypass và double-counting.                          |
| Chất lượng thiết kế thực nghiệm         | **4/10** | Có multi-seed, CI và Wilcoxon, nhưng so sánh chính chưa calibrated, baseline/ablation yếu và benchmark nội sinh.                                                   |
| Khả năng tái lập                           | **5/10** | Code, JSON, traceability và checksum hình tốt; README, dependency pinning, environment và public artifact chưa đạt.                                                  |
| Giá trị ứng dụng và tác động thực tế | **3/10** | Chưa có dữ liệu thật; score/dispatch mang tính policy heuristic và giả định nghiệp vụ chưa được xác nhận.                                                 |
| Chất lượng trình bày học thuật          | **7/10** | Bài viết rõ, có tự giới hạn; nhưng bỏ sót trade-off, fragmentation, error signatures và trình bày calibration dễ gây hiểu sai.                              |

## G. Kiểm tra nhất quán giữa bài báo, mã nguồn và JSON

| Hạng mục                                    | Kết quả                                                                                                                       |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Dataset 485/421/60/4/13                       | **Khớp**[dataset.json (line 7)](/home/ngthtrong/nckh2/demo/data/dataset.json:7)                                           |
| 39 fake, 66.7% trong vùng                    | **Khớp**[dataset.json (line 28)](/home/ngthtrong/nckh2/demo/data/dataset.json:28)                                         |
| ARI đa-seed 0.9616 vs 0.9348 và CI hiệu    | **Khớp**[exp12_multiseed_summary.json (line 3)](/home/ngthtrong/nckh2/demo/results/tables/exp12_multiseed_summary.json:3) |
| Đường kính 1.54 vs 98.53 km               | **Khớp JSON** , nhưng là shared-default không công bằng                                                             |
| Context ARI drop 0.174/overlap 0.396          | **Khớp** , nhưng chủ yếu single-seed và generator được thiết kế cho hiệu ứng này                             |
| Calibration product/additive                  | **Số khớp** , nhưng bảng trộn best-overall với usable-window                                                        |
| Violation 0/38, 71/79, 95/99                  | **Khớp JSON** , nhưng additive counts gồm\(\theta\ge1\), ngoài miền lemma                                            |
| Priority stability                            | **Khớp**JSON                                                                                                             |
| Dispatch −14.82 và −1.43 phút             | **Khớp** , nhưng paper không nêu chi phí mean arrival all                                                            |
| Confidence AUC/AP/campaign                    | **Khớp**JSON                                                                                                             |
| Scaling 7200/46.06 s                          | **Khớp JSON** ; “one CPU core” và hardware không truy vết được                                                   |
| Packet 105–111 byte                          | **Khớp mã** , nhưng dùng placeholder confidence                                                                       |
| Hình paper vs demo                           | **Khớp checksum 8/8**                                                                                                    |
| PDF hiện hành                               | **Biên dịch sạch 12 trang**                                                                                            |
| Root/demo README                              | **Sai/lỗi thời nghiêm trọng**                                                                                         |
| Confidence áp dụng lên mọi input priority | **Không khớp:** \(V\)không được gate                                                                                |
| `log_final.txt`                             | **Lỗi thời:**khác`main.log`hiện hành                                                                                     |

## H. Thí nghiệm hoặc sửa đổi bắt buộc trước khi nộp

1. Sửa định lý và claim additive; báo cáo hop-diameter/bound tightness.
2. Chạy calibrated multi-seed evaluation có train/test hoặc nested calibration.
3. Thêm matched-density/matched-degree comparison.
4. Thêm real-data sanity check với annotation incident-level.
5. Thiết kế lại \(N,V,C\) ở cấp incident, xử lý duplicate reports.
6. Thử fake/adversarial vulnerability và coordinated duplicate campaigns.
7. Factorial ablation cho geography, time, context, confidence và k-NN.
8. Tuning đa-seed cho ST-DBSCAN, ClustGeo/spatial constraint, HDBSCAN/DBSCAN và multiple-kernel baseline.
9. Báo cáo split/merge, noise rejection, false destinations và operator workload.
10. Đánh giá dispatch bằng outcome độc lập và Pareto trade-off.
11. Ghi hardware/RAM/BLAS, lặp timing, peak memory và triển khai spatial indexing thật.
12. Đồng bộ README, khóa dependency và cung cấp public immutable artifact.

## I. Câu hỏi dành cho tác giả

1. \(h\) được kiểm soát bằng cơ chế nào trước khi thấy dữ liệu? Nếu không, vì sao gọi cận cụm là operational guarantee?
2. Tác giả có đồng ý additive có cận khi \(\theta>\beta+\gamma\) không?
3. Vì sao các threshold \(\theta\ge1\) được tính vào violation count của lemma có miền \(0<\theta<1\)?
4. Vì sao Exp12 không hiệu chỉnh \(\theta\) riêng hoặc khớp retained-edge fraction?
5. Tại sao additive \(\alpha=.5,\theta=.96\), vốn tie product trong vùng usable và có max diameter nhỏ hơn, không được thảo luận?
6. “Pre-registered” được đăng ký ở đâu, ngày nào và bất biến bằng cơ chế nào?
7. Một cụm gồm nhiều báo cáo về cùng 10 người thì \(\sum N_iC_i\) tránh đếm 10 người nhiều lần bằng cách nào?
8. Vì sao \(V_i\) không được nhân \(C_i\), trong khi fake vulnerability không được tạo trong benchmark?
9. Tại sao metric dispatch chính được coi là external khi nó dùng chính \(V\) và \(F\) của priority formula?
10. Tác giả đánh giá thế nào việc mean arrival all xấu hơn gần 25 phút so với no-vulnerability?
11. Tại sao failure trên nhãn multimodal và split/merge đa-seed không xuất hiện trong phần Results/Threats?
12. Code/data sẽ được công bố tại URL/DOI và commit nào?

## J. Kết luận và khuyến nghị

Bài có nền tảng kỹ thuật tương đối tốt, tác giả đã thể hiện tinh thần khoa học khi công khai nhiều kết quả bất lợi. Tuy nhiên, bằng chứng hiện tại phù hợp hơn với một **technical proof-of-concept trên synthetic data** hơn là một nghiên cứu đã sẵn sàng cho công bố uy tín về hệ thống hỗ trợ cứu hộ.

**Khuyến nghị cuối cùng: Reject and Resubmit.**

Không nên Reject vĩnh viễn vì cận cạnh đúng, code có cấu trúc tốt, truy vết số liệu tốt và các vấn đề có thể sửa. Nhưng khối lượng sửa liên quan đến định lý, protocol tuning, priority semantics và dữ liệu thật lớn hơn phạm vi một vòng Major Revision thông thường.

### Danh sách công việc ưu tiên

**P0 — ảnh hưởng tính đúng đắn khoa học**

* Thu hẹp/sửa định lý và phát biểu additive.
* Loại threshold ngoài miền lemma khỏi violation count.
* Sửa confidence-bypass đối với vulnerability.
* Giải quyết double-counting \(N,V\) giữa báo cáo trùng.
* Chạy calibrated out-of-sample product–additive comparison.
* Bổ sung real-data sanity check hoặc hạ bài thành nghiên cứu phương pháp thuần synthetic.
* Báo cáo đầy đủ trade-off dispatch, không chỉ metric có lợi.

**P1 — cần để thuyết phục reviewer**

* Baseline spatio-temporal/spatial constraint/multiple-kernel mạnh và được tuning.
* Factorial ablation đa-seed.
* Split/merge/noise/operator-burden metrics.
* Independent dispatch outcome và sensitivity theo policy parameters.
* Error analysis cho multimodal labels.
* Runtime lặp lại, hardware/memory và spatial-index implementation.
* Public repository, commit/DOI và dependency lock.

**P2 — hoàn thiện trình bày**

* Đồng bộ hai README.
* Làm rõ “kernel” là similarity hay PSD kernel.
* Sửa caption/bảng calibration để phân biệt best-overall và best-usable.
* Bỏ `log_final.txt` lỗi thời hoặc tạo lại.
* Chuẩn hóa XeLaTeX instructions.
* Làm rõ SD/CI, multiple comparisons, packet assumptions và giới hạn của \(N_{\rm ref}\).
