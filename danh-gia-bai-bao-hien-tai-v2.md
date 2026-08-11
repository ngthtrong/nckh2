# Báo cáo phản biện độc lập — bản thảo hiện hành v2

- **Hội nghị/chuẩn đánh giá:** ISDS 2026, Springer CCIS
- **Bản thảo thực tế được đánh giá:** *Stress-Testing Product-Gated Clustering and Bounded Priority Ranking for Flood-Rescue Reports*
- **Loại bài:** Short paper
- **Ngày đánh giá:** 11/08/2026
- **Nguồn chuẩn:** `paper/main.tex` → `paper/short.tex`
- **Commit:** `785031b7422f5d263cf23f8530b1168fc8a2e017`
- **SHA-256 của `paper/short.tex`:** `87ba2969e59368362129049376b9a13cf94c75a9aed5190b269e2204379c8e96`
- **Mức độ tin cậy của phản biện:** Cao
- **Khuyến nghị:** **Major Revision**
- **Điểm tổng thể:** **7.1/10**

> **Lưu ý định danh.** Tiêu đề trong yêu cầu và báo cáo cũ — *Product-Similarity
> Graph Clustering and Bounded Priority Heuristics for Flood-Rescue Reports: A
> Synthetic Held-Out Study* — không còn là tiêu đề của bản thảo hiện hành. Báo
> cáo này đánh giá đúng bản short paper v2 nêu trên, không đánh giá lại phiên bản
> cũ theo quán tính.

## 1. Phạm vi và cách kiểm tra

Báo cáo được lập từ:

- toàn bộ nội dung `paper/short.tex`, hai bảng trong
  `paper/short_results.tex`, Figure 1 và danh mục tài liệu tham khảo;
- protocol, generator, mã clustering/ranking/dispatch và bằng chứng xác nhận
  trong `revision/v2/` và `demo/v2/`;
- báo cáo cũ `danh-gia-bai-bao-hien-tai.md`, chỉ để xác định nhận xét nào đã lỗi
  thời;
- PDF hiện hành và log biên dịch;
- một lượt chạy độc lập quy trình re-analysis do artifact cung cấp trên các kết
  quả đã đóng băng tại workspace hiện tại.

Kết quả kiểm tra kỹ thuật:

- `python -m demo.v2.reproduce reproduce_core`: **PASS** khi chạy bằng môi
  trường khóa của dự án; analysis và generated TeX khớp byte-for-byte, không
  đọc oracle diagnostic và không tái sinh dữ liệu/chạy pipeline confirmation
  từ seed;
- `pytest -q demo/tests/test_v2_*.py`: **150 passed**;
- `paper/short.pdf`: **8 trang**, không có undefined citation/reference hoặc
  overfull box;
- checksum analysis và result lần lượt khớp
  `60550c2b...33ffb` và `a7497eaa...33cf8`.

`paper/generated/revision_results.tex` thuộc workflow Exp23 cũ và bị tài liệu
v2 loại khỏi nguồn bằng chứng hiện hành; báo cáo này không dùng các kết quả cũ
trong file đó. Tương tự, các snapshot `demo/data/dataset*.json` là dữ liệu lịch
sử, không phải confirmation evidence của short paper v2.

Trang chính thức ISDS 2026 yêu cầu short paper dài 6–8 trang, định dạng một cột
LNCS/CCIS; PDF hiện tại đáp ứng điều kiện hình thức này. Hướng dẫn proceedings
của Springer xác nhận bộ template/instruction áp dụng cho cả CCIS:
[ISDS 2026](https://isds.ctu.edu.vn/2026/) và
[Springer Computer Science Proceedings](https://link.springer.com/series/558/information-for-authors-and-editors).

## 2. Overall Assessment

Đây là một bản thảo tốt hơn rõ rệt so với phiên bản được đánh giá trước. Các
lỗi lớn cũ về miền của định lý, zero-imputation, search space product–additive
không cân xứng, near-duplicate chaining, oracle grouping trong dispatch, thiếu
hình và sai giới hạn trang đã được sửa đúng. Bản hiện tại cũng có một phẩm chất
khoa học đáng ghi nhận: tác giả giữ nguyên kết quả bất lợi và thu hẹp kết luận
theo đúng phạm vi bằng chứng.

Trong phạm vi generator đã khóa, kết luận chính được hỗ trợ khá chắc: product
clustering kém additive về ARI ở cả ID và OOD; OOD còn tạo thêm false
destinations; priority mới không thắng các baseline đơn giản mạnh; nearest-first
có mean harm và deadline-miss thấp hơn trong các so sánh headline, dù không phải
mọi harm contrast đều Holm-significant; và boundedness không ngăn được
coordinated nonincident campaign có confidence cao.

Tuy nhiên, bản thảo chưa đạt mức **Accept/Minor Revision** theo một vòng phản
biện khắt khe. Nút thắt hiện nay không còn là lỗi thực thi cơ bản mà là giá trị
khoa học và khả năng diễn giải:

1. novelty thuật toán còn thấp; đóng góp thực nằm ở protocol stress test và
   negative evidence nhưng Related Work chưa định vị đủ;
2. toàn bộ bằng chứng vẫn do một generator của tác giả tạo ra, chưa có
   out-of-generator, real-data hoặc expert validation;
3. các perturbation priority giữ cố định/ấn định predicted labels, nên chỉ kiểm
   tra ranking có điều kiện chứ chưa phải robustness end-to-end;
4. simulator dispatch gần bão hòa deadline miss và còn đơn giản, trong khi các
   giá trị tuyệt đối quan trọng không xuất hiện trong bài;
5. pointwise CI và Holm-adjusted inference chưa được phân biệt rõ, trong khi bài
   còn dùng ngôn ngữ gần với equivalence khi chưa có equivalence test;
6. bài chưa phân tích độ phức tạp và chưa có benchmark scalability cho v2.

Vì các điểm trên cần bổ sung bằng chứng, phân tích hoặc thay đổi đáng kể cách
định vị đóng góp, quyết định phù hợp là **Major Revision**. Kết quả âm tự thân
không phải lý do hạ điểm; ngược lại, việc báo cáo trung thực kết quả âm là một
điểm mạnh.

## 3. Scores

| Tiêu chí | Điểm /10 | Nhận định ngắn |
|---|---:|---|
| Relevance | **8.5** | Phù hợp rõ với spatio-temporal data science, graph clustering và intelligent decision support. Phạm vi thực tế là tầng quyết định trên feature đã cấu trúc, chưa phải xử lý report thô end-to-end. |
| Originality & Contribution | **5.0** | Product composition, Louvain và bounded weighted score không mới; định lý khá trực tiếp. Giá trị mới đáng kể nhất là protocol truth-isolated, stress testing và negative-result diagnosis. |
| Methodological Rigor | **7.0** | Leakage control, matched calibration, paired confirmation và artifact discipline tốt. Điểm trừ lớn đến từ generator nội sinh, stress cố định partition, simulator đơn giản và thiếu scalability evidence. |
| Claims & Conclusions | **8.0** | Phần lớn kết luận trung thực, đúng hướng và có giới hạn rõ. Một số câu cần phân biệt pointwise CI với Holm-adjusted inference và tránh ngôn ngữ equivalence. |
| Language & Presentation | **7.2** | Tiếng Anh tốt, cấu trúc rõ, PDF sạch và đúng 8 trang. Related Work, self-containment, đơn vị bảng, cỡ chữ figure và bibliography còn cần sửa. |

Điểm trung bình không phải tiêu chí quyết định duy nhất. Originality và external
validity là hai “bottleneck criteria” khiến bài vẫn cần major revision dù nhiều
thành phần kỹ thuật được thực hiện tốt.

## 4. Summary of the Paper

Bài báo khảo sát một pipeline batch, fail-closed cho báo cáo cứu hộ lũ đã được
biểu diễn thành các trường có cấu trúc. Báo cáo có location và event time được
đưa vào một đồ thị tương đồng thưa; báo cáo thiếu hai trường này được chuyển
sang review. Product similarity

\[
G_{ij}(\beta T_{ij}+\gamma C_{ij})
\]

được so sánh với additive similarity

\[
\alpha G_{ij}+\beta T_{ij}+\gamma C_{ij}.
\]

Sau spatial candidate pooling, empirical quantile threshold, endpoint-wise
top-\(k\) union và Louvain tạo predicted clusters. Bài chứng minh một cận
khoảng cách cho từng retained product edge, đồng thời nói rõ cận đó không bảo
đảm component compactness nếu tồn tại chuỗi bắc cầu dài.

Mỗi predicted cluster sau đó được chấm bằng một heuristic priority hữu hạn.
Exact duplicates được collapse bằng fingerprint; near duplicates dùng complete
linkage; demand và vulnerability được provenance-gate rồi lấy maxima để tránh
cộng trùng không có bằng chứng. Điểm cuối bị chặn trong \([0,1.75]\). Các
predicted clusters, chứ không phải oracle incidents, trở thành jobs cho bộ lập
lịch. Incident truth, benefit, deadline và harm chỉ được join sau khi score và
schedule đã hình thành.

Nghiên cứu dùng 20 development seeds, 20 calibration seeds và 40 confirmation
master seeds; mỗi confirmation seed sinh một dataset ID và một dataset OOD theo
cơ chế thay đổi. Product và additive dùng cùng grid 128 điểm và cùng quy tắc
one-standard-error nhưng được chọn độc lập. ST-DBSCAN và geo-time HDBSCAN là
direct baselines. Phân tích dùng paired bootstrap, paired Wilcoxon và Holm
adjustment.

Kết quả xác nhận là kết quả âm:

- product thấp hơn additive **0.172 ARI ở ID** và **0.100 ở OOD**;
- OOD product tạo thêm **4.11 false destinations/100 reports**;
- revised priority thấp hơn legacy về mean NDCG@5 và không hơn simple linear;
- exact-copy score invariance đạt, nhưng coordinated high-confidence campaign
  đạt normalized false-priority lift bằng 1.0, tức đạt hoặc vượt scale cực đại
  dùng để chuẩn hóa, không phải xác suất tấn công hay mức tăng harm;
- nearest-first có mean harm và deadline miss thấp hơn revised policy trong các
  headline comparisons, nhưng OOD harm không Holm-significant.

Thông điệp trung tâm mà reviewer hiểu là: các safeguard toán học như edge
localization, boundedness và duplicate invariance không tự động suy ra incident
accuracy, policy validity hoặc rescue benefit.

## 5. Major Strengths

### S1. Relevance và câu hỏi nghiên cứu có ý nghĩa

Bài nối ba tầng thường bị đánh giá rời rạc: incident consolidation, priority
ranking và dispatch outcome. Việc truyền split/merge/noise từ clustering vào
scheduling phù hợp với tinh thần Data Science và Intelligent Systems hơn một
benchmark ARI đơn lẻ. Bối cảnh cứu hộ lũ cũng làm rõ chi phí của false
destination, missed incident và deadline miss.

### S2. Claim discipline và tính trung thực khoa học rất tốt

Bài không gọi product kernel là phát minh mới, không suy bounded score thành
policy đã được xác nhận, không che adverse/null results, và nói rõ không có bằng
chứng deployment, misinformation robustness hoặc real-world harm reduction.
Abstract, Results, Discussion và Conclusion nhìn chung nhất quán. Đây là điểm
mạnh nổi bật nhất của bản thảo.

### S3. Ranh giới observable–evaluator được thiết kế tốt

Figure 1 và mã v2 tách rõ dữ liệu được phép dùng để inference khỏi incident ID,
benefit và outcome truth. Priority và dispatch thực sự chạy trên predicted
product clusters; oracle grouping chỉ nằm trong diagnostic artifact và không
tham gia inference chính. Điều này khắc phục hoàn toàn một lỗi lớn của phiên bản
cũ.

### S4. So sánh product–additive hiện công bằng hơn nhiều

Hai composition family dùng cùng 128-point nuisance grid, cùng spatial
candidate universe và cùng selection rule. Trong từng matched registry pair,
composition operator là trường thực thi duy nhất khác nhau; tuy nhiên, hai
selected final configurations có thể khác nhau do mỗi family được chọn độc lập.
Bài cũng phát biểu đúng estimand: đây là so sánh hai independently selected
pipelines, không phải causal effect thuần của phép nhân.

### S5. Phương pháp toán học và missingness đã được giới hạn đúng

Các scale dương được nêu rõ; theorem xử lý đúng các miền của threshold và chỉ
claim edge localization. Context similarity dùng shared-observation mask và
coverage penalty thay vì xem missing như một quan sát bằng 0. Complete linkage
tránh near-duplicate transitive chaining kiểu \(A\sim B\sim C\) khi
\(A\not\sim C\).

### S6. Thiết kế xác nhận và traceability nội bộ mạnh

Seed partitions, protocol hash, implementation hash, calibration selection,
confirmation manifest và generated tables liên kết chặt. Analysis unit là paired
master seed, không phải report hoặc scenario giả độc lập. Tái phân tích độc lập
trên workspace hiện tại cho kết quả khớp hoàn toàn và 150 v2 tests đều đạt.

### S7. Metric coverage tốt hơn đáng kể so với phiên bản cũ

Ngoài ARI, artifact có false destinations, noise rejection, split/merge,
review burden, diameter, ranking metrics, stress drift, harm, deadline miss,
unreached incidents, false/duplicate trips, tail response và workload. Việc coi
false destinations là co-primary endpoint là một lựa chọn hợp lý về mặt vận
hành.

### S8. Hình thức short paper đã hợp lệ

PDF đúng 8 trang LNCS/CCIS, có workflow figure, hai bảng kết quả, không có lỗi
reference/citation khi build. Trạng thái anonymous phù hợp cho review PDF nếu
ISDS xác nhận chính sách blind tương ứng.

## 6. Major Weaknesses / Concerns

### C1. Originality và scholarly positioning còn yếu — High

Product composition, Gaussian gate, Louvain, clipping, max aggregation,
log-normalization và \(\tanh\) multiplier đều là các thành phần quen thuộc.
Product edge bound suy trực tiếp từ
\(w_{ij}\leq(\beta+\gamma)G_{ij}\); exact-copy invariance phần lớn đúng by
construction sau fingerprint collapsing. Đây là các safeguard hợp lệ nhưng
khó xem là đóng góp thuật toán/lý thuyết mạnh.

Đóng góp thuyết phục hơn là **một protocol synthetic stress test có kiểm soát
leakage, giữ kết quả âm và truyền lỗi tới dispatch**. Bản thảo đã bắt đầu định
vị theo hướng này nhưng Related Work chỉ gồm hai đoạn ngắn và 17 nguồn được
trích, không có nguồn sau 2021. Chưa có đối chiếu đủ gần với humanitarian
event/entity resolution, crisis-report deduplication, record linkage,
multi-view similarity fusion, dynamic crisis graphs, robust triage hoặc
synthetic/OOD validation hiện đại.

**Yêu cầu sửa:** định vị đóng góp chính là diagnostic methodology/negative
evidence; mở rộng closest-related-work và chỉ ra rõ protocol này bổ sung điều gì
so với các benchmark event resolution và humanitarian scheduling gần nhất.
Không nên trình bày edge bound như một đóng góp lý thuyết lớn.

### C2. Synthetic held-out có internal validity tốt nhưng external validity rất yếu — High

ID và OOD đều được sinh bởi cùng một codebase và cùng giả thuyết thiết kế của
tác giả. OOD thay đổi cơ chế thật sự, không chỉ đổi seed, nhưng vẫn là
author-designed mechanism shift chứ không phải external distribution. Public
anchor hiện chỉ là descriptive plausibility check; không có tham số generator
nào được fit từ dữ liệu công khai.

Generator cấp trực tiếp \(F,E,N,V,L,T\), nên không truyền lỗi của raw text,
image processing, location extraction/geocoding, semantic ambiguity hoặc source
authentication vào pipeline. Network outage, correlated sources, road/flood
physics, multilingual/Vietnamese transfer và human decision behavior cũng chưa
được mô hình hóa. Ngoài ra, trong generator hiện tại `received_at` bằng chính
timestamp dùng làm \(T\), nên event time và receipt time chưa thực sự tách biệt;
“late order” chưa tương đương delayed/out-of-order arrival ngoài thực tế.

Cỡ dữ liệu sau snapshot cũng nhỏ hơn câu “ID data contain 16 authored
incidents” có thể khiến người đọc hình dung. Trong 40 confirmation seeds, số
report còn lại sau khi áp dụng cutoff — tức được quan sát tại snapshot — là
19–126 ở ID và 23–307 ở OOD; số incident thực sự có report tại snapshot lần
lượt là 2–11 và 2–14. Các số này được kiểm tra từ
`revision/v2/results/confirmation_result.json.gz`, trường denominator trong
product clustering rows. Confidence intervals vì vậy chỉ đo biến thiên bên
trong simulator ở quy mô này.

**Yêu cầu sửa:** thêm bảng compact mô tả phân bố **sau snapshot**, các tham số
generator, stress frequencies và khác biệt ID/OOD; sửa mô tả arrival process;
thêm ít nhất một independently specified/out-of-generator benchmark hoặc một
real-data sanity check có annotation độc lập. Nếu chưa thể có dữ liệu thật,
phải dùng nhất quán cụm “within author-designed synthetic regimes” và không gọi
held-out seed là external validation.

### C3. Stress tests của priority chưa phải robustness end-to-end — High

Mười stress family không chạy lại graph clustering. Với exact/near/chain,
injected reports được gán trực tiếp vào target predicted cluster; campaign được
gán một predicted label mới. Do đó kết quả exact-duplicate zero score drift chỉ
chứng minh **score-level invariance khi partition được giữ/ấn định**, không chứng
minh duplicate injection không thay threshold quantile, topology, Louvain
partition, downstream ranking units hoặc schedule. Campaign lift tương tự là
một conditional ranking counterexample, không phải xác suất misinformation
thành công trong full pipeline.

Main paper cũng chỉ báo hai trong mười family: exact duplicate và coordinated
campaign. Kết quả của near duplicate, gradual chain, bốn low-confidence fields,
missingness và contradiction không xuất hiện, dù RQ2 hỏi trực tiếp về chúng.
Mức perturbation và quy tắc chọn target cluster cũng không được mô tả.

**Yêu cầu sửa:** ghi rõ “conditional on the frozen predicted partition”; thêm
một threat matrix compact cho cả mười family; nếu muốn claim pipeline
robustness, phải chạy lại toàn bộ graph → clustering → ranking → dispatch sau
perturbation trên một split mới hoặc một protocol đã khóa phù hợp.

### C4. Construct của provenance và priority chưa được xác nhận — High

Weights, caps, \(N_{\rm ref}\), vulnerability scale và near-duplicate tolerance
không learned, không expert-validated và chưa có sensitivity analysis trong bài.
Max aggregation tránh overcount nhưng có thể undercount nhiều nhóm người thực
sự độc lập trong cùng incident. Capped corroboration đếm source families gần
nhau theo không gian–thời gian nhưng không kiểm tra semantic agreement hoặc xác
thực independence; các source family/provenance claims cũng có thể bị giả mạo.

Campaign đạt lift tối đa là một phản ví dụ có giá trị, nhưng đồng thời cho thấy
score hiện không thể được xem là misinformation-robust. Bài đã tránh claim này,
song giá trị tích cực của heuristic ngoài boundedness và exact-copy invariance
vẫn còn hạn chế; trên NDCG và dispatch, heuristic không thắng các baseline đơn
giản mạnh.

**Yêu cầu sửa:** công bố đầy đủ công thức \(Q_i\), caps, scales và duplicate
envelope; thêm sensitivity analysis; giải thích trade-off max aggregation;
thực hiện expert elicitation/validation hoặc tiếp tục gọi score là illustrative
heuristic, không phải rescue policy.

### C5. Dispatch simulator và đường review chưa đủ vững — High

Mọi job được release tại snapshot phút 150. Deadline lại tính từ incident onset
và bị chặn trong 18–180 phút, trong khi không gian hoạt động rộng và chỉ có 2–5
boats. Kết quả tuyệt đối trong frozen analysis gần bão hòa
(`revision/v2/results/confirmation_analysis.json`, các key
`dispatch.{id,ood}.{policy}.deadline_miss_rate.scenario_mean`):

- revised deadline-miss mean: **95.2% ID** và **98.6% OOD**;
- nearest-first: **81.5% ID** và **91.1% OOD**.

Đây là mean qua seed của unweighted mean trên ba resource scenarios, không phải
tỷ lệ gộp theo report hoặc trip.

Table 2 chỉ báo chênh lệch, nên người đọc không thấy simulator đang hoạt động ở
regime rất khắc nghiệt. Trong thiết kế này, nearest-first có lợi thế cấu trúc do
travel time chi phối. Service time dùng observable reported-demand proxy, trong
khi latent `service_demand_min` đã được generator tạo nhưng không dùng trong
dispatch. Điều này không làm kết quả âm sai, nhưng giới hạn mạnh khả năng diễn
giải “policy failure”.

Đường review cũng chưa nhất quán hoàn toàn. Metric review burden đếm singleton
và low-provenance clusters ngoài report thiếu \(L/T\), nhưng `build_jobs` vẫn
đưa mọi non-noise predicted cluster vào dispatch; chỉ report thiếu \(L/T\) hoặc
label `-1` thực sự bị giữ lại. Vì Louvain không emit noise label, product/additive
có noise rejection bằng 0 theo thiết kế. Reviewer chưa rõ “Review” trong Table 1
là actual routing hay hypothetical human workload (`demo/v2/clustering.py`,
`clustering_endpoints`; `demo/v2/dispatch.py`, `build_jobs`).

**Yêu cầu sửa:** báo absolute harm/deadline/unreached/false-trip metrics, mô tả
ba resource scenarios, thêm sensitivity theo cutoff, fleet, geography, service
time và horizon; định nghĩa rõ review gate và áp dụng nhất quán trước dispatch
nếu đó là một thành phần thật của pipeline.

### C6. Statistical reporting chưa phân biệt rõ các tầng suy luận — High

Phân tích seed-paired, bootstrap và Wilcoxon là hợp lý. Vấn đề nằm ở cách trình
bày. Table 2 báo ordinary 95% bootstrap CIs, trong khi Holm family của
priority/dispatch/stress có **244 hypotheses**. Vì vậy một CI riêng lẻ có thể
loại 0 nhưng Holm-adjusted test không significant. Ví dụ:

- OOD NDCG revised–legacy: CI loại 0, raw \(p=0.00139\), nhưng Holm-adjusted
  \(p=0.234\);
- OOD harm revised–nearest-first: CI loại 0, raw \(p=0.00583\), nhưng
  Holm-adjusted \(p=0.910\).

Trong khi đó, ID harm và cả hai ID/OOD deadline contrasts với nearest-first là
Holm-significant; OOD harm thì không. Abstract/Conclusion nói nearest-first
“reduced harm and deadline misses” hoặc “outperformed” mà không phân biệt effect
estimate, unadjusted interval và familywise-adjusted inference. Các giá trị trên
được lấy từ `revision/v2/results/confirmation_analysis.json`, các comparison key
`priority.ood.ndcg_at_k.revised_vs_legacy` và
`dispatch.{id,ood}.{endpoint}.revised_vs_nearest_first`.

Cụm “statistically indistinguishable from the simple linear score” cũng không
đúng về logic kiểm định: không bác bỏ khác biệt không chứng minh equivalence.
Không có power/minimum detectable effect rationale cho 40 seeds. ST-DBSCAN và
HDBSCAN chỉ được so sánh mô tả, nhưng Discussion viết product “clustered worse
than ... direct density baselines” mà thiếu từ “descriptively”.

**Yêu cầu sửa:** đưa adjusted \(p\) hoặc ký hiệu inferential status cạnh các
headline effects; ghi rõ CI là pointwise/unadjusted; thay “statistically
indistinguishable” bằng “no adjusted evidence of a difference”; thêm precision
hoặc power rationale; mọi nhận xét về density baselines phải mang nhãn
descriptive trừ khi có contrast đã đăng ký. Không được tái cấu trúc family hậu
nghiệm trên confirmation results hiện tại để tìm significance thuận lợi.

### C7. Độ phức tạp và scalability chưa được chứng minh — Medium–High

Graph stage hiện dùng BallTree và candidate pool. Riêng candidate construction
trong trường hợp thông thường có thể gần \(O(n\log n+nK)\) time và \(O(nK)\)
storage với \(K=\max(64,4k)\); đây không phải bound cho toàn graph stage hoặc
Louvain. Boundary ties/fallback cùng bước sắp xếp có thể đưa worst case lên gần
\(O(n^2\log n)\). Các bước khác vẫn nặng:

- global corroboration quét cặp report: \(O(n^2)\);
- pairwise compatibility work của deterministic complete-link có thể đạt
  \(O(u^3)\) theo số evidence units trong cluster, chưa kể overhead tạo và so
  sánh candidate signatures;
- scheduler quét các job còn lại ở mỗi lượt: \(O(J^2)\);
- one-to-one evaluator matching dùng rectangular Hungarian assignment:
  \(O(\min(J,I)^2\max(J,I))\), và trở thành cubic khi số jobs \(J\) và incident
  truth \(I\) cùng bậc.

Các nhận định này dựa trên implementation hiện hành trong
`demo/v2/clustering.py`, `demo/v2/dedup.py`, `demo/v2/dispatch.py` và
`demo/v2/evaluation.py`, không dựa trên runtime artifact Exp23 cũ.

Không có complexity statement, runtime/memory benchmark hoặc incremental update
trong short paper. Confirmation batch lớn nhất chỉ 307 reports, chưa đủ để gọi
kiến trúc là tối ưu hoặc phù hợp crisis stream quy mô lớn. Runtime evidence trong
workflow Exp23 cũ không thể dùng cho v2.

**Yêu cầu sửa:** nêu complexity theo stage; benchmark time và peak memory cho
selected v2 pipeline trên nhiều bậc \(n\), kể cả worst-case/tied locations;
phân biệt batch reference implementation với streaming deployment; nếu giữ
claim “sparse”, báo candidate/edge fraction và peak memory thực tế.

### C8. Metric coverage tốt nhưng còn blind spots — Medium

ARI trên incident-linked reports được bổ sung bằng false destinations và noise
rejection, đây là cải tiến đúng. Tuy nhiên false destination chỉ đếm cluster
toàn noise; noise bị hấp thụ vào một incident cluster không bị phạt bởi metric
này. NDCG@5 được tính trên emitted predicted units sau one-to-one match; incident
không tạo được operational unit không đi trực tiếp vào ideal ranking. Dispatch
phần nào bù lại bằng unreached incidents, nhưng các định nghĩa và trade-off chưa
tự chứa trong bài.

Product thực tế có destination diameter nhỏ hơn additive trong artifact, phù
hợp với edge-localization motivation, nhưng secondary result này không được
trình bày. Ngược lại, split loss của product cao và false/duplicate trips không
được đưa vào main table. Việc chỉ giữ headline metrics làm mất một phần giá trị
diagnostic của nghiên cứu âm.

**Yêu cầu sửa:** giải thích/sensitivity-check one-to-one matching và \(k=5\);
bổ sung mixed-noise contamination/purity; báo compact trade-off giữa ARI,
split/merge, diameter, review burden và dispatch errors.

### C9. Self-containment, bibliography và responsible-use presentation còn thiếu — Medium–High

Bài chưa cho biết selected configurations, duplicate tolerances, công thức đầy
đủ của \(Q_i\), \(s\), \(N_{\rm ref}\), caps, ba resource scenarios, harm unit
và định nghĩa chính xác của false destination/review item. Artifact không thể
thay hoàn toàn phần mô tả khoa học tự chứa.

Một số lỗi trình bày cụ thể:

- `ARI` và `NDCG@5` chưa được mở rộng đầy đủ;
- Table 2 ghi deadline effect theo percentage points (`-13.68`, `-7.54`), còn
  prose dùng các giá trị tương đương trên thang proportion (`-0.137`, `-0.075`)
  nhưng không ghi rõ đơn vị, gây bất nhất trình bày;
- Figure 1 rõ về logic nhưng chữ nhỏ nhất sau khi scale xuống `\textwidth` ước
  tính khoảng 5 pt, dưới mức tối thiểu 6 pt được Springer khuyến nghị; cần tăng
  cỡ chữ và tăng khả năng đọc grayscale;
- BibTeX làm mất capitalization của CrisisMMD, FloodNet, Twitter, Louvain và
  Leiden; DOI/metadata còn thiếu ở nhiều mục;
- các từ “accepted manifest”, “gate remained blocked”, “locked family” mang màu
  sắc QA nội bộ; “accepted” dễ bị hiểu nhầm là venue đã chấp nhận;
- manuscript nói có “accompanying artifact” nhưng không cho access route/DOI
  trong nội dung. Nếu artifact không được đính kèm trực tiếp trong anonymous
  review package, reviewer sẽ không thể kiểm tra claim này. Tái lập hiện tại chủ
  yếu là re-analysis stored rows, không phải tái thực thi confirmation end-to-end.

Với một hệ thống liên quan quyết định cứu hộ, nên có một đoạn responsible-use
ngắn về privacy của location/time/provenance, human override, false negatives,
fairness với nhóm dễ tổn thương và điều kiện governance trước field trial. Bản
camera-ready còn phải hoàn tất author/affiliation, funding và conflict-of-interest
metadata theo yêu cầu của venue/publisher.

**Yêu cầu sửa:** thêm một bảng method/data/scenario compact hoặc supplement
được dẫn rõ; sửa unit/acronym/BibTeX/figure; cung cấp anonymous artifact link ở
review hoặc immutable DOI ở camera-ready; thêm responsible-use statement.

## 7. Detailed Feedback & Suggestions

### 7.1 Title and Abstract

- Tiêu đề hiện tại đã trung thực hơn nhờ từ “Stress-Testing”, nhưng nên thêm
  “Synthetic” để phạm vi bằng chứng hiển thị ngay từ tiêu đề, chẳng hạn:
  *A Synthetic ID/OOD Stress Test of Product-Gated Clustering and Bounded
  Priority Ranking for Flood-Rescue Reports*.
- Mở rộng “Adjusted Rand Index (ARI)” và “normalized discounted cumulative gain
  at 5 (NDCG@5)” ở lần xuất hiện đầu.
- Thêm qualifier “within the author-designed synthetic regimes” cho các con số
  chính.
- Phân biệt “separately specified latent benefit” với “statistically independent
  benefit”; outcome vẫn chia sẻ latent flood/demand/vulnerability factors.
- Nói rõ exact-duplicate result là score invariance conditional on the fixed
  predicted partition.
- Với nearest-first, dùng “had lower mean harm/deadline-miss values” và nêu
  adjusted status, thay vì một câu có thể bị hiểu là confirmatory superiority ở
  mọi endpoint/regime.

### 7.2 Introduction and Related Work

- Giữ RQ1–RQ3; cấu trúc hiện tại rõ.
- Viết contribution statement theo thứ tự: truth-isolated protocol → operational
  propagation analysis → negative evidence → mathematical audit properties.
- Bổ sung closest work về incident/entity resolution, crisis deduplication,
  record linkage, dynamic graphs, robust humanitarian triage và OOD/synthetic
  benchmark design.
- Nêu rõ input là **structured report features**. Bài không đánh giá NLP,
  multimodal perception hoặc geocoding.

### 7.3 Methods

- Thêm pseudocode ngắn cho candidate pool → quantile → top-k union → Louvain.
- Nối theorem với pipeline thực tế: báo empirical \(\theta\), bound radius và
  observed destination diameter của selected product configuration.
- Định nghĩa exact fingerprint, complete-link envelope, corroboration window,
  source-independence key và mọi cap/scale.
- Nêu complexity kỳ vọng và worst case của từng stage.
- Giải thích trường hợp report vào review và tác động của review tới schedule.

### 7.4 Synthetic Data and Experimental Design

- Thêm bảng ID/OOD gồm post-snapshot report/incident counts, spatial/time noise,
  missingness, duplicates, campaign size, resource scenarios và outcome ranges.
- Tách event time khỏi receipt time trong generator nếu muốn nghiên cứu delayed
  hoặc out-of-order reports.
- Mô tả 20 development seeds đã được dùng cho quyết định nào.
- Cho biết selected config IDs/parameters của product, additive, ST-DBSCAN và
  HDBSCAN.
- Thêm independently specified/out-of-generator benchmark hoặc real annotated
  sanity set; nếu không thể, nêu đây là process-held-out trong cùng generator
  family.
- Cho rationale của 40 confirmation seeds và độ chính xác kỳ vọng của effect
  estimates.

### 7.5 Results and Discussion

- Thêm adjusted p-value/marker và denominator cho headline results.
- Thay mọi ngôn ngữ equivalence dựa trên non-significance.
- Báo absolute dispatch metrics và per-scenario sensitivity, không chỉ deltas.
- Báo compact toàn bộ mười stress families.
- Giữ ST-DBSCAN/HDBSCAN ở mức descriptive hoặc dùng một future frozen split cho
  inferential contrasts; không đăng ký lại hậu nghiệm trên split đã mở.
- Thêm Pareto/trade-off view cho ARI, split, false destinations, noise rejection,
  diameter và review burden.
- Nhấn mạnh campaign result như một safety finding và yêu cầu human override,
  không chỉ như limitation.

### 7.6 Language, Tables, Figure and Bibliography

- Đồng nhất deadline effect thành percentage points trong bảng lẫn prose.
- Định nghĩa harm unit/normalization và ba resource scenarios trong caption hoặc
  text.
- Table 1 cần ghi rõ các ô là mean; thêm ký hiệu hướng tốt/xấu nếu còn chỗ.
- Tăng cỡ chữ Figure 1; kiểm tra bản in grayscale và accessibility text.
- Bảo vệ capitalization trong BibTeX; kiểm tra metadata/DOI, đặc biệt HDBSCAN.
- Sắp các nhóm citation theo thứ tự số tăng dần; hiện có `[14,3,12]`, `[8,6,4]`
  và `[7,2]`.
- Thay “accepted manifest/analysis” bằng “frozen/verified manifest/analysis”.
- Dẫn rõ anonymous supplement/artifact trong review package.

## 8. Trạng thái các nhận xét trong báo cáo cũ

| Nhận xét cũ | Trạng thái ở v2 | Bằng chứng/nhận định |
|---|---|---|
| PDF 11 trang, không thuộc long/short track | **Đã lỗi thời** | PDF hiện đúng 8 trang, hợp lệ short paper. |
| Không có architecture figure | **Đã lỗi thời** | Figure 1 mô tả observable, review và evaluator paths. |
| Dispatch dùng oracle incident grouping | **Đã sửa** | Main inference dùng predicted product clusters; oracle chỉ diagnostic. |
| Missing \(F/E\) bị zero-impute | **Đã sửa** | Context similarity dùng shared-observation mask và coverage factor. |
| Product/additive grids không cân xứng | **Đã sửa** | Cùng 128-point nuisance grid; chọn độc lập theo cùng rule. |
| Near duplicates dùng transitive union-find | **Đã sửa** | Deterministic complete linkage. |
| Định lý thiếu miền dương/claim component quá rộng | **Đã sửa** | Positive scales, threshold endpoint cases và edge-only scope được nêu rõ. |
| Dense graph implementation | **Đã sửa một phần** | Graph candidate stage thưa; corroboration, matching, scheduling và worst case vẫn quadratic/cubic. |
| ARI che operational burden | **Đã sửa đáng kể** | FD là co-primary; NR/review/dispatch có báo cáo. Mixed-noise và full trade-off vẫn thiếu. |
| Generator-family bias/no external validation | **Vẫn còn** | OOD là author-designed mechanism shift trong cùng generator. |
| Priority weights/caps không được xác nhận | **Vẫn còn** | Bài thừa nhận không learned/expert-validated. |
| Related Work và self-containment yếu | **Chỉ sửa một phần** | Có workflow/grid/weights, nhưng thiếu closest work và nhiều tham số/định nghĩa. |
| Artifact public URL/DOI chưa rõ | **Vẫn còn** | Local evidence tốt; manuscript không cho access route bất biến. |

## 9. Required Revisions Before Acceptance

### Bắt buộc

1. **Định vị lại novelty** quanh diagnostic stress-test và negative evidence;
   bổ sung closest related work.
2. **Làm rõ dữ liệu synthetic** bằng post-snapshot distributions, generator
   parameters và alternate-generator/real sanity validation; nếu không có, hạ
   scope nhất quán xuống author-designed synthetic regimes.
3. **Giới hạn hoặc mở rộng stress claims:** nói rõ fixed-partition conditional
   test; báo cả mười family; muốn claim end-to-end thì phải rerun full pipeline
   theo protocol mới.
4. **Sửa statistical reporting:** pointwise CI, Holm-adjusted p và ngôn ngữ
   inferential phải nhất quán; không dùng “statistically indistinguishable” như
   bằng chứng equivalence.
5. **Làm rõ simulator:** báo absolute outcomes, per-scenario/sensitivity,
   review routing và deadline saturation.
6. **Bổ sung complexity/runtime-memory scaling** cho chính pipeline v2.
7. **Công bố đầy đủ priority/dedup/scenario parameters** và expert/sensitivity
   status.
8. **Hoàn thiện self-containment và presentation:** units, acronyms, Figure 1,
   bibliography, artifact access và responsible-use statement.

### Khuyến nghị mạnh

1. Thêm mixed-noise contamination/purity và Pareto view cho clustering.
2. Thêm sensitivity của one-to-one gain matching và NDCG@5.
3. Tách event time khỏi receipt time, mô phỏng delayed/out-of-order arrival.
4. Tối ưu global corroboration, complete-link và scheduler trước khi nói tới
   high-volume stream.
5. Không tune hoặc tái định nghĩa Holm family trên 40 confirmation seeds đã mở;
   mọi hypothesis mới nên dùng future frozen split.

## 10. Questions for the Authors

1. Đóng góp trung tâm mà tác giả muốn hội nghị đánh giá là thuật toán mới hay
   một negative synthetic stress-test methodology?
2. Vì sao priority stress injections giữ/ấn định predicted labels thay vì chạy
   lại graph clustering? Claim exact-duplicate invariance được giới hạn ở score
   level như thế nào?
3. “Review” trong Table 1 có thực sự chặn singleton/low-provenance clusters khỏi
   dispatch không? Nếu có, vì sao `build_jobs` vẫn schedule chúng?
4. Các weights, caps, source-family independence và duplicate tolerances được
   chọn từ expert knowledge, development seeds hay heuristic judgment?
5. Với deadline-miss tuyệt đối khoảng 95–99% cho revised policy, kết quả có ổn
   định khi đổi cutoff, fleet, geography và service model không?
6. Tại sao event time và receipt time chưa được tách trong generator trong khi
   bài nhấn mạnh late order/receipt-time snapshot?
7. Tác giả muốn người đọc diễn giải pointwise bootstrap CI thế nào khi Holm
   family có 244 tests và một số adjusted p-values không significant?
8. Artifact nào sẽ được reviewer truy cập, và phần nào là re-analysis stored
   rows so với full end-to-end reproduction?

## 11. Final Recommendation

### **Major Revision**

Bản thảo hiện tại chưa nên được Accept hoặc Minor Revision, vì các sửa đổi cần
thiết liên quan tới novelty, external validity/independent validation,
conditional stress design,
dispatch construct, inferential reporting và scalability — không chỉ là chỉnh
văn phong.

Reviewer không đề nghị Reject vì bài có giá trị khoa học rõ dưới dạng một
**rigorous negative synthetic stress test**: protocol nội bộ chặt, truth boundary
tốt, product–additive comparison công bằng, adverse results được giữ nguyên và
deployment claims được giới hạn đúng. Nếu tác giả bổ sung bằng chứng độc lập hoặc
làm rõ nghiêm ngặt phạm vi synthetic, hoàn thiện stress/simulator/statistical
reporting và củng cố positioning, bài có thể trở thành một short paper có giá
trị cho ISDS/CCIS.
