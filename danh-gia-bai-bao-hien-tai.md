# Báo cáo phản biện độc lập — bản thảo hiện hành

- **Hội nghị/chuẩn đánh giá:** ISDS 2026, Springer CCIS
- **Bản thảo:** *Product-Similarity Graph Clustering and Bounded Priority Heuristics for Flood-Rescue Reports: A Synthetic Held-Out Study*
- **Ngày đánh giá:** 11/08/2026
- **Phiên bản được đánh giá:** `paper/main.tex`, commit `c904dc0ad04e637b63e215c988cd8eb84ce715b7`
- **Mức độ tin cậy của phản biện:** Cao
- **Khuyến nghị:** **Major Revision**
- **Điểm tổng thể:** **6.3/10**

## 1. Phạm vi và nguồn đánh giá

Báo cáo này đánh giá trực tiếp bản thảo hiện hành trong
[`paper/main.tex`](paper/main.tex), thư mục tài liệu tham khảo, mã phương pháp,
protocol hiệu chỉnh, bộ sinh dữ liệu synthetic và các kết quả đã khóa. Các file
[`phan-bien.md`](phan-bien.md), [`draft.md`](draft.md) và
[`revision-plan.md`](revision-plan.md) chỉ được dùng để hiểu lịch sử sửa đổi;
những nhận xét trong đó không được mặc định là còn đúng.

Nguồn bằng chứng hiện hành gồm:

- bản thảo và PDF 11 trang hiện tại;
- các giá trị được sinh cơ học trong
  [`paper/generated/revision_results.tex`](paper/generated/revision_results.tex);
- protocol 20 development/20 calibration/40 test seeds và một held-out run đã
  khóa;
- mã hiện hành trong `demo/data`, `demo/pipeline`, `demo/simulation` và
  `demo/experiments`;
- báo cáo khóa kết quả, clean-room và tái lập trong `revision/`.

Đây là phản biện khoa học, không phải xác nhận đạo đức nghiên cứu, quyền sử
dụng dữ liệu, tư cách tác giả hay phê duyệt chính sách cứu hộ.

## 2. Overall Assessment

Bản thảo hiện tại đã tiến bộ rất đáng kể so với phiên bản từng bị đề nghị
“Reject and Resubmit”. Các lỗi cũ về miền của cận toán học, threshold không
strict, confidence bypass đối với vulnerability, cộng trùng dân số, hiệu chỉnh
trên cùng dữ liệu, baseline yếu, metric chỉ dựa trên ARI và khả năng tái lập nội
bộ phần lớn đã được xử lý. Đặc biệt, tác giả giữ lại kết quả bất lợi thay vì chỉ
báo cáo kết quả có lợi; đây là điểm mạnh hiếm và đáng ghi nhận.

Tuy nhiên, bản thảo vẫn chưa đạt mức chấp nhận ở một hội nghị ISDS/CCIS có phản
biện nghiêm túc. Lý do chính không còn là lỗi thực thi cơ bản, mà là khoảng cách
giữa độ chặt chẽ của protocol với giá trị khoa học của đóng góp:

1. product similarity, Louvain/Leiden và bounded weighted score đều không mới;
   cận địa lý là một tính chất thiết kế khá trực tiếp của Gaussian gate;
2. toàn bộ bằng chứng vẫn là held-out **trong cùng một họ generator do tác giả
   thiết kế**, không phải external validation;
3. so sánh product–additive đã tốt hơn nhưng search space vẫn không cân xứng;
4. product Louvain có ARI cao nhưng noise rejection bằng 0 và tạo trung bình
   34.85 false destinations trên mỗi dataset;
5. priority heuristic không cho thấy lợi ích dispatch, thất bại trước chiến dịch
   high-confidence, và thí nghiệm dispatch sử dụng oracle incident grouping
   thay vì output phân cụm thực;
6. bài chưa self-contained về generator, cấu hình và simulator, không có hình
   minh họa, và PDF 11 trang không khớp quy định long/short paper của ISDS 2026.

Do đó, bài có nền tảng tốt cho một **rigorous synthetic stress-test study**, nhưng
chưa thuyết phục như một thuật toán cứu hộ mới hoặc một hệ thống có giá trị vận
hành đã được xác lập.

## 3. Scores

| Tiêu chí | Điểm /10 | Nhận định |
|---|---:|---|
| Relevance | **8.0** | Phù hợp với graph clustering, spatio-temporal data, data quality và intelligent decision support. Tính đặc thù “flood rescue” còn yếu vì perception, text processing và thực địa không được đánh giá. |
| Originality & Contribution | **4.5** | Product form và community detection là kỹ thuật đã biết; edge bound và score bound khá trực tiếp. Đóng góp mạnh nhất là protocol, stress testing và negative-result retention, không phải thuật toán mới. |
| Methodological Rigor | **6.5** | Leakage control, statistics, baselines và artifact audit tốt. Điểm bị trừ bởi generator nội sinh, grid tuning không cân xứng, oracle dispatch grouping, dense complexity và một điều kiện toán học còn thiếu. |
| Claims & Conclusions | **6.5** | Kết luận nhìn chung trung thực và không overclaim triển khai. Tuy nhiên, bằng chứng không chứng minh hiệu quả end-to-end; priority contribution hiện chủ yếu là một kết quả âm. |
| Language & Presentation | **6.0** | Tiếng Anh tốt và bảng sạch, nhưng bài quá đậm audit jargon, thiếu mô tả tự chứa, không có figures, related work mỏng và page count không hợp lệ. |

**Điểm bổ sung không tính vào trung bình:** khả năng truy vết/tái lập nội bộ
**8.5/10**; khả năng tái lập độc lập từ một public immutable artifact hiện chỉ
ở mức khoảng **5/10** vì chưa có URL/DOI công khai và workflow chính xác minh
held-out result thay vì tái chạy X0.

## 4. Summary of the Paper

Bài báo nghiên cứu một pipeline hợp nhất các báo cáo cứu hộ lũ có thể trùng,
thiếu hoặc mâu thuẫn. Mỗi báo cáo được biểu diễn bằng vị trí, thời gian, mức
ngập, mức khẩn cấp, demand/vulnerability evidence và một confidence heuristic.
Hệ thống xây dựng đồ thị bằng product similarity, trong đó geographic Gaussian
similarity nhân với tổ hợp temporal/contextual similarity, sau đó threshold,
k-NN sparsification và Louvain/Leiden được dùng để tạo incident candidates.

Bài cũng đề xuất một priority heuristic bị chặn trong khoảng hữu hạn. Exact
duplicates được loại theo fingerprint; near duplicates được gom theo các
tolerance quan sát được; các thành phần urgency, flood, demand và vulnerability
được confidence-gate và cap trước khi tổng hợp.

Về lý thuyết, bài chứng minh rằng trong miền ngưỡng hữu hạn, mỗi product edge
được giữ có một cận khoảng cách tường minh. Cận đường kính component phụ thuộc
thêm vào hop diameter quan sát được và vì vậy không phải compactness guarantee
ex ante. Bài cũng nêu đúng miền hữu hạn của additive similarity.

Về thực nghiệm, 80 synthetic datasets với 30,229 reports và 1,280 latent
incidents được chia thành 20 development, 20 calibration và 40 test seeds. Trên
label-aware track, product Louvain đạt ARI 0.9237, cao hơn additive Louvain
0.8921; chênh lệch additive-minus-product là -0.0316, 95% CI
[-0.0393, -0.0248]. Tuy nhiên, product Louvain không reject noise, tạo trung
bình 34.85 false destinations và có các trade-off bất lợi so với ST-DBSCAN.
Priority mới bất biến với exact duplicates nhưng tệ hơn legacy dưới coordinated
high-confidence campaign. Dispatch simulation không cho thấy lợi ích đáng tin
cậy so với legacy và ưu tiên nearest-first về harm/deadlines trong các kịch bản
được thử.

## 5. Major Strengths

### S1. Claim discipline và tính trung thực khoa học

Abstract, Discussion và Conclusion đều công khai các kết quả bất lợi: product
không reject noise; additive có đường kính nhỏ hơn; ST-DBSCAN có ưu thế về
split/noise; coordinated campaign đánh bại safeguard; priority không cải thiện
dispatch; và toàn bộ nghiên cứu không phải field validation. Đây là điểm mạnh
lớn nhất của bản thảo.

### S2. Protocol chống leakage tốt

Việc tách development/calibration/test, khóa protocol trước khi mở test, giữ
nguyên infeasible configurations, chạy một held-out suite duy nhất và không
tuning lại trên test là thiết kế đáng tin cậy trong phạm vi generator. Hai track
label-aware và label-free cũng giúp phân biệt benchmark performance với khả
năng chọn cấu hình khi không có nhãn.

### S3. Metric coverage và statistical reporting tốt

Bài không còn dựa riêng vào ARI. Split/merge loss, false destinations, review
burden, noise rejection, diameter, rank drift, deadline, harm, equity và
workload được báo cáo. Paired bootstrap CI, Wilcoxon, effect size, denominator
và Holm correction được định nghĩa theo family. Ties, failures và adverse
comparisons được giữ lại.

### S4. Phạm vi toán học đã được thu hẹp đúng mức

Bản thảo không còn gọi product similarity là Mercer kernel hoặc tuyên bố product
form tự thân là mới. Additive finite-threshold region được nêu, strict threshold
đồng nhất với mã, và component bound được mô tả rõ là conditional trên observed
hop diameter.

### S5. Reproducibility engineering rất mạnh ở mức nội bộ

Dependency pins, manifest, checksums, result lock, generated claim macros,
negative-result retention, 242 tests cùng 41 subtests và clean-room PDF audit
tạo ra mức truy vết tốt hơn phần lớn bài hội nghị. Bản PDF build sạch, không có
undefined citation/reference và không có overfull box.

### S6. Baselines và ablations đã được mở rộng thực chất

Bản hiện tại có additive/convex similarity, ST-DBSCAN, standardized
DBSCAN/HDBSCAN, spatially constrained agglomerative, Leiden/spectral
diagnostics và full-factorial ablation. Điều này xử lý phần lớn phê bình cũ về
baseline quá yếu, dù một số vấn đề fairness và positioning vẫn còn.

## 6. Major Weaknesses / Concerns

### C1. Originality và scientific positioning chưa đủ mạnh — High

Product similarity được thừa nhận là không mới. Định lý edge localization chủ
yếu dùng \(T,C\leq1\), suy ra \(w_{ij}\leq B G(d_{ij})\), rồi đảo hàm Gaussian.
Component corollary là triangle inequality dọc theo path và không kiểm soát
hop diameter. Priority score là một tổ hợp hand-crafted của clipping, maxima,
weighted sum, log normalization và \(\tanh\); exact-duplicate invariance phần lớn
đúng by construction sau fingerprint collapsing.

Related Work hiện không trả lời thuyết phục câu hỏi “đóng góp này khác gì với
humanitarian event entity resolution, crisis-post aggregation, record linkage,
multi-view similarity fusion và robust humanitarian scheduling?”. Việc dùng
bilateral filtering làm tiền lệ gần nhất cho product structure là quá xa bài
toán. Bảng positioning bốn dòng cũng không đủ để chứng minh novelty.

**Yêu cầu sửa:** định vị giá trị chính là leakage-controlled synthetic stress
test và operational error analysis; bổ sung literature gần nhất về humanitarian
event/entity resolution, dynamic crisis-report graph, product fusion of
similarity matrices, record linkage và triage/dispatch. Không nên bán edge bound
như một đóng góp lý thuyết lớn.

### C2. Phát biểu toán học vẫn thiếu điều kiện miền — Medium–High

Trong `paper/main.tex:187–193`, \(T(\Delta t)\) và \(C(i,j)\) dùng các mẫu số
\(\tau_t,\tau_F,\tau_E\), nhưng bài chỉ nêu
\(\alpha,\beta,\gamma\geq0\) và \(\sigma>0\). Proof sau đó cần
\(T,C\in[0,1]\). Nếu một \(\tau\) bằng 0, công thức không xác định; nếu âm,
similarity có thể vượt 1 và proof không còn đúng. Mã đã validate các tham số
này, nhưng theorem trong bài chưa self-contained.

Priority bound cũng nên nêu tường minh \(s>0\), \(N_{\rm ref}>0\), caps dương,
\(1\leq\mu\leq2\), các weights không âm và tổng weights bằng 1. Ngoài ra,
\(C_i\) đang ký hiệu confidence trong khi \(C(i,j)\) là contextual similarity,
dễ gây nhầm.

**Yêu cầu sửa:** bổ sung toàn bộ assumptions trước theorem; đổi ký hiệu thành
chẳng hạn \(q_i\) cho confidence và \(S_{\rm ctx}(i,j)\) cho context similarity.

### C3. Synthetic held-out có internal rigor nhưng external validity rất yếu — High

Generator v4 tốt hơn rõ rệt so với bản cũ: có overlapping incidents,
multimodality, missingness, duplicates, background noise, low-confidence attacks,
coordinated campaign và latent outcomes độc lập đại số. Tuy nhiên, mỗi seed vẫn
gồm 13 incident templates được curate và chỉ 3 independent-stress incidents;
tổng số incident cố định là 16. Mỗi dataset cũng có cấu trúc adversarial gần như
cố định: 32 background reports, 4 low-confidence inflation cases và 5 coordinated
campaign reports. Test seeds chỉ thay đổi các draw trong cùng generator family.

Bộ sinh không mô hình hóa raw text, semantic ambiguity, lỗi geocoding, missing
location/time, source correlation, delayed/batched reporting, concept drift,
communication outage, route accessibility hoặc thay đổi phân bố giữa các trận
lũ. Các feature \(F,E,N,V,C\) được cung cấp trực tiếp; perception/NLP error không
được truyền vào clustering. Vì vậy “chaos” hiện mới là chaos do tác giả khai
báo, không phải bằng chứng rằng generator khớp dữ liệu cứu hộ thực.

Missing values hiện được zero-impute dù context similarity so sánh trực tiếp
\(|F_i-F_j|\) và \(|E_i-E_j|\), không dùng missingness mask trong distance.
Hai báo cáo cùng thiếu một trường có thể vì thế trông tương đồng, còn “missing”
có thể bị lẫn với một quan sát thật sự thấp. Bài chưa có ablation riêng cho sai
lệch do cơ chế này.

Held-out seeds kiểm soát parameter leakage, nhưng không kiểm soát **generator
family bias**. CIs chỉ đo variation trong simulator này, không phải uncertainty
về real floods.

**Yêu cầu sửa:** ít nhất cần một out-of-generator stress set với cơ chế sinh và
parameter ranges không dùng trong development; tốt nhất là một real-data sanity
check có incident-level annotation độc lập. Nếu không có dữ liệu thật, phải dùng
cụm từ “within-generator held-out” nhất quán và trình bày một bảng generator
parameters/scenario frequencies ngay trong bài.

### C4. Fair calibration vẫn chưa hoàn toàn công bằng — High

Product và additive hiện dùng threshold quantiles và matched retained
fraction/mean degree, đây là cải tiến quan trọng. Tuy nhiên, registry cho product
128 configurations với bốn giá trị \(\sigma\) và hai giá trị \(\tau_t\); additive
chỉ có 96 configurations, hai giá trị \(\sigma\), không tune \(\tau_t\) và dùng
default 45 phút; convex similarity cũng không tune đầy đủ các length scales.
“Cùng search ceiling” không đồng nghĩa với “cùng effective search space”.

Density/degree matching chỉ kiểm soát độ dày đồ thị, không kiểm soát khác biệt do
temporal/context bandwidth hoặc độ linh hoạt của mỗi family. Vì vậy kết quả
product hơn additive khoảng 0.032 ARI là có thật cho **hai frozen grids đã chọn**,
nhưng chưa đủ để kết luận product composition tốt hơn additive family nói chung.

**Yêu cầu sửa:** dùng cùng grid cho mọi hyperparameter chung
\(\sigma,\tau_t,\tau_F,\tau_E,k\) và resolution, ngân sách evaluation thực sự
cân bằng và chỉ để composition-specific weights khác nhau. Nếu protocol phải
thay đổi, cần khóa calibration mới và dùng test seeds mới; không được tiếp tục
tuning trên 40 test seeds đã mở.

### C5. ARI cao không chuyển thành output vận hành tốt — High

Trên label-aware track, product Louvain đạt ARI 0.9237, nhưng noise rejection
bằng 0, tạo trung bình 34.85 false destinations và khoảng 35.4 review items mỗi
dataset. Trong cùng bộ test, ST-DBSCAN có ARI thấp hơn (0.8789) nhưng noise
rejection 0.8671, false destinations bằng 0 và split loss gần bằng 0. Additive
cũng cho destination diameter nhỏ hơn product.

Các kết quả này không phải lỗi báo cáo; tác giả đã trình bày trung thực. Tuy
nhiên, chúng cho thấy ARI-optimized product graph chưa phải lựa chọn vận hành
hợp lý. Với 16 latent incidents mỗi dataset, khoảng 35 false destinations là
một burden rất lớn, không phải một limitation phụ.

Track “label-free” cũng chỉ tối ưu reverse-order partition stability. Đây là
thước đo tính nhạy với thứ tự chạy, không phải incident validity; một partition
ổn định vẫn có thể ổn định theo cách sai hoặc có burden cao.

**Yêu cầu sửa:** đặt false destinations/noise/review burden ngang hàng với ARI
trong selection hoặc trình bày Pareto frontier. Cần đánh giá product graph kết
hợp một noise/outlier handling stage, nhưng mọi thay đổi phải được hiệu chỉnh
trên calibration mới chứ không trên held-out test cũ.

### C6. Priority và dispatch chưa có construct/end-to-end validity — High

Priority mới đã sửa confidence bypass và linear double counting, nhưng dùng
maximum cho \(N,V\) có thể bỏ sót nhiều nhóm người thực sự disjoint. Near
duplicates được tạo thành connected components bằng union-find; vì quan hệ
tolerance không bắc cầu, transitive chaining có thể gom hai endpoint không còn
nằm trong tolerance. Các tolerance, caps, weights và utility chưa được chuyên
gia xác nhận.

Confidence hiện chủ yếu là một proximity-density/provenance heuristic: các
payload hơi khác nhau trong cùng cửa sổ địa lý–thời gian có thể tự củng cố mà
không chứng minh source independence hay semantic consistency. Campaign
failure là hệ quả phù hợp với construct này; thuật ngữ “corroboration” cần được
giới hạn để không gợi ý một misinformation detector.

Quan trọng hơn, dispatch experiment không dùng output của graph clustering.
Trong `demo/experiments/exp17_dispatch_outcomes.py:83–121`, mã đọc
`evaluation_only.incident_id/gt_cluster`, loại mọi unlinked report và tính
priority trên các ground-truth incident groups. Do đó false destinations,
split/merge errors, background fake reports và coordinated campaign không được
truyền vào dispatch. Đây là oracle-grouping diagnostic, không phải đánh giá
pipeline end-to-end; bản thảo hiện chưa nói rõ điểm này.

Kết quả âm vẫn có giá trị: ngay cả với grouping lý tưởng, revised priority không
cho lợi ích harm đáng tin so với legacy, kém nearest-first về harm/deadlines,
chỉ xuất hiện trên Pareto frontier 0.275 so với 1.0 của nearest-first trong
nominal dual-depot, và coordinated high-confidence drift tệ hơn legacy trên cả
40 seeds. Nhưng chính các kết quả đó khiến “priority heuristic” chưa phải một
đóng góp hiệu quả tích cực.

Các deadline, harm slopes và capacity penalties còn chủ yếu là latent random
draws, trong khi travel/lateness chi phối outcome. Điều này tránh được metric
tự lặp lại công thức priority, nhưng chưa chứng minh harm model có construct
validity và có thể tạo lợi thế cấu trúc cho nearest-first.

Main paper cũng chưa tóm tắt đủ các stress cases đã đăng ký. Claim catalog cho
thấy direction-adjusted revised-versus-legacy priority-drift improvement là
-0.0556 ở low-confidence \(N\) inflation (revised tệ hơn 40/40 seeds) và
-0.0684 ở low-confidence \(V\) inflation (tệ hơn 30/40). Một bảng compact cho
toàn bộ threat matrix cần được đưa vào main paper hoặc supplement dễ thấy.

**Yêu cầu sửa:** gọi thí nghiệm hiện tại là oracle-grouping priority diagnostic;
bổ sung một end-to-end dispatch experiment dùng predicted clusters và mọi
unlinked/false destination, đồng thời báo cáo chênh lệch oracle–predicted. Thực
hiện sensitivity analysis cho caps/weights/tolerances, báo đủ mọi stress case,
và expert validation hoặc giảm vai trò priority trong title/contribution.

### C7. Complexity và scalability chưa đủ cho rescue stream — Medium–High

Graph construction và storage hiện vẫn dense \(O(n^2)\). BallTree chỉ giảm số
cặp phải tính trong một cấu hình finite-bound, nhưng vẫn materialize dense
compatibility matrix. Near-duplicate grouping cũng so mọi cặp trong cluster,
tức \(O(m^2)\); confidence/corroboration và một số bước chuyển matrix sang graph
cũng quét cặp. Runtime audit lớn nhất chỉ khoảng 1,494 reports, chưa đại diện
cho high-volume stream, và benchmark dùng default raw-threshold configuration
chứ không phải toàn bộ calibrated held-out pipeline.

Bài đã thừa nhận phần lớn hạn chế này, nhưng không thể gọi kiến trúc là tối ưu
hoặc deployment-ready. Ngoài ra chưa có incremental update, sliding window,
streaming community maintenance hay peak-memory scaling đủ lớn.

**Yêu cầu sửa:** nêu complexity theo từng stage; triển khai sparse adjacency
end-to-end hoặc hạ claim thành reference implementation; benchmark thời gian và
memory trên nhiều bậc cỡ dữ liệu, bao gồm selected configuration và update cost
trong streaming setting.

### C8. Presentation, self-containment và venue compliance chưa đạt — High

Bản thảo dùng nhiều thuật ngữ audit như Gate 1/2/3, G0, selectors, promotion và
hash nhưng lại thiếu các thông tin khoa học cần để tự hiểu phương pháp: selected
\(\sigma,\tau,k\), resolution, near-duplicate tolerances, policy weights/caps,
quy tắc k-NN symmetrization, metric definitions và chi tiết simulator. Artifact
tốt không thay thế mô tả self-contained trong paper.

Bản hiện tại có bốn bảng nhưng không có figure hoặc algorithm diagram. Table
factorial thiếu cột Endpoint; dispatch table thiếu đơn vị và định nghĩa resource
scenario; các bảng lớn dùng `\scriptsize`/`\resizebox`. Related Work chỉ trích
18 nguồn, không có nguồn nào sau 2021, dù một entry 2024 đã có trong `.bib` nhưng
không được dùng. Nhiều acronym/proper name trong bibliography chưa được bảo vệ
capitalization.

Formal blocker: `paper/main.log` xác nhận PDF hiện có **11 trang**, trong khi
[hướng dẫn ISDS 2026](https://isds.ctu.edu.vn/2026/) yêu cầu **12–15 trang cho
long paper hoặc 6–8 trang cho short paper**. Bản hiện tại không thuộc category
nào và có nguy cơ bị desk screening. Author block, funding và competing-interest
declarations cũng vẫn ở trạng thái pending.

**Yêu cầu sửa:** chọn long-paper track và thêm ít nhất một trang nội dung thực
chất, không kéo giãn hình thức. Một workflow figure cùng bảng generator/config
compact có thể đồng thời giải quyết page count và self-containment. Chuyển hash,
selector và promotion details sang supplement/artifact appendix.

## 7. Detailed Feedback & Suggestions

### 7.1 Title and Abstract

- Đổi “Heuristics” thành số ít nếu chỉ có một revised heuristic.
- Cân nhắc title trung thực hơn: *A Synthetic Stress Test of Product-Gated
  Graph Clustering and a Duplicate-Aware Priority Heuristic for Flood-Rescue
  Reports*.
- Đổi “product rejects no noise” thành “product has a zero noise-rejection
  rate”.
- Đổi “independent dispatch outcomes” thành “simulated outcomes defined
  algebraically independently of the score”; từ “independent” hiện có thể bị
  hiểu nhầm là external validation.
- Dùng “within-generator held-out” khi mô tả kết quả.
- Nói rõ dispatch dùng ground-truth/oracle incident groups, nếu chưa có
  end-to-end result.

### 7.2 Introduction and Related Work

- Viết lại contribution statement để ưu tiên protocol, operational metrics và
  stress-test evidence thay vì hàm product như một algorithmic novelty.
- Bổ sung closest prior work về humanitarian event entity resolution, crisis
  report deduplication, dynamic semantic graphs, record linkage, multi-view
  similarity fusion và humanitarian triage/scheduling.
- Các điểm khởi đầu trực tiếp nên được đối chiếu gồm
  [Structured Event Entity Resolution in Humanitarian Domains](https://doi.org/10.1007/978-3-030-00671-6_14),
  [dynamic semantic graphs for crisis subevents](https://aclanthology.org/2021.wnut-1.28/)
  và tổng quan [(Almost) All of Entity Resolution](https://doi.org/10.1126/sciadv.abi8021).
- Bảng positioning cần so sánh data type, online/batch mode, duplicate handling,
  noise model, spatial control, real/synthetic validation và complexity; cột
  “Bound” hiện quá giản lược.
- Các nguồn perception như CrisisMMD/FloodNet/MobileNet/DistilBERT chỉ là
  deployment context, không thay cho related work về incident consolidation.

### 7.3 Method

- Bổ sung mọi domain assumptions cho theorem và priority bound.
- Đổi ký hiệu confidence/context để không dùng \(C\) cho hai khái niệm.
- Thêm pseudocode hoặc một workflow figure.
- Nêu rõ threshold quantile được chuyển thành threshold raw như thế nào ở mỗi
  dataset, cách k-NN được symmetrize, isolate/noise được xử lý ra sao và
  complexity của từng bước.
- Mô tả exact fingerprint fields, near-duplicate tolerances và tác động của
  transitive closure.
- Giải thích tại sao max aggregation là lựa chọn policy chấp nhận được, không chỉ
  vì nó tránh overcounting; nêu rủi ro undercounting disjoint groups.

### 7.4 Synthetic Data and Experimental Design

- Thêm bảng tóm tắt số incidents/reports, template/random families, spatial/time
  dispersion, missingness, duplicates, noise và adversarial counts.
- Nêu rõ latent/observable separation và feature nào được giả định đã trích xuất
  hoàn hảo.
- Dùng distance mask-aware hoặc thêm missingness indicator vào similarity; báo
  ablation cho missingness độc lập và missingness tương quan.
- Thêm generator-shift benchmark; nếu có thể, real incident-level sample với
  annotation agreement.
- Cân bằng search space cho common hyperparameters và công bố selected configs
  trong main paper/supplement.
- Phân biệt effect uncertainty trong generator với external uncertainty.

### 7.5 Results and Discussion

- Trình bày một Pareto plot ARI–false destinations–noise rejection–review burden.
- Đưa false destinations/nghiệp vụ thành headline result, không chỉ limitation.
- Thêm per-family error analysis, đặc biệt multimodal, spatial-overlap adversarial
  và independent-stress families.
- Với dispatch, báo cả oracle-grouped và predicted-cluster end-to-end result.
- Công bố công thức latent target của priority factorial; không coi correlation
  với một target được dựng từ các biến gần giống score là external validation.
- Nêu effect size/practical magnitude trước p-value; tránh “direction-adjusted
  improvement” khi có thể viết trực tiếp phương pháp nào tốt hơn.
- Giữ nguyên toàn bộ adverse results; không nên tuning thêm trên test để tìm một
  kết quả thuận lợi.

### 7.6 Presentation and Bibliography

- Thêm một architecture/workflow figure và một result trade-off plot.
- Bổ sung cột Endpoint cho factorial table và units/scenario definition cho
  dispatch table.
- Di chuyển packet-size paragraph khỏi Observable Representation sang Runtime.
- Chuẩn hóa BibTeX cho HDBSCAN, DOI còn thiếu và capitalization của CrisisMMD,
  MobileNetV3, EmergencyNet, FloodNet, DistilBERT, Louvain và Leiden.
- Xác nhận blind-review policy, author metadata, funding và competing interests
  trước submission/camera-ready.

## 8. Trạng thái các nhận xét cũ

| Concern trong `phan-bien.md` | Trạng thái hiện tại | Nhận định |
|---|---|---|
| MC1 — theorem/additive domain | **Phần lớn đã xử lý** | Product/additive regions, strict threshold và conditional component bound đã đúng; còn thiếu positivity assumptions cho các \(\tau\). |
| MC2 — unfair product/additive comparison | **Đã xử lý đáng kể nhưng chưa hoàn tất** | Có split, quantile threshold và density/degree matching; common hyperparameter grids vẫn không cân xứng. |
| MC3 — endogenous synthetic data | **Chỉ xử lý một phần** | Generator giàu failure modes hơn và được khóa, nhưng held-out vẫn cùng generator; không có real/external source. |
| MC4 — confidence bypass/double counting | **Lỗi code đã xử lý; construct validity còn mở** | Gating nhất quán, duplicate-aware max aggregation; weights/tolerances/unique-demand semantics chưa được chuyên gia xác nhận. |
| MC5 — self-confirming dispatch metric | **Algebraic circularity đã xử lý; end-to-end chưa xử lý** | Latent outcome không tái dùng score inputs, nhưng dispatch dùng oracle grouping và bỏ unlinked reports. |
| MC6 — baselines/ablation | **Phần lớn đã xử lý** | Có direct/spatial baselines và factorial; learned multi-kernel chưa có, grid fairness và closest literature còn yếu. |
| MC7 — ARI hides burden | **Metric reporting đã xử lý** | Split/merge/noise/false destinations/review burden đã hiện diện; kết quả cho thấy proposed method vẫn yếu về vận hành. |
| MC8 — reproducibility | **Đã xử lý mạnh ở mức local** | Pins, manifests, clean-room và claim trace tốt; public DOI/repository, X0 re-execution và submission metadata còn thiếu. |

## 9. Các sửa đổi/thí nghiệm cần thiết trước khi chấp nhận

### Bắt buộc

1. Sửa toàn bộ domain assumptions và xung đột ký hiệu trong phần Method.
2. Công khai và cân bằng search spaces cho product/additive/convex compositions;
   nếu thay protocol, dùng một test split mới đã khóa.
3. Gọi đúng dispatch hiện tại là oracle-grouping diagnostic và bổ sung đánh giá
   end-to-end dùng predicted clusters cùng unlinked/false reports.
4. Đưa false destinations, noise rejection và review burden vào quyết định
   multi-objective/Pareto, không dùng ARI làm tín hiệu ưu thế chính.
5. Bổ sung out-of-generator validation; lý tưởng là real-data sanity check có
   annotation độc lập. Nếu không thể, hạ framing nhất quán xuống within-generator
   synthetic stress test.
6. Viết lại novelty/Related Work dựa trên closest event-resolution và crisis
   aggregation literature.
7. Làm paper self-contained bằng generator/config table, workflow figure, metric
   definitions và simulator disclosure.
8. Sửa page count thành long paper 12–15 trang và hoàn thiện metadata.

### Khuyến nghị mạnh

1. Expert elicitation/sensitivity analysis cho priority weights, caps và
   near-duplicate tolerances.
2. Kiểm tra transitive-chain failure của near-duplicate connected components.
3. Per-family analysis cho multimodal và independent-stress cases.
4. Sparse end-to-end implementation cùng streaming/time-memory benchmark lớn
   hơn.
5. Public immutable repository/archive với DOI, English reproducibility guide
   và một entrypoint có thể tái chạy experiment trong output mới.

## 10. Questions for the Authors

1. Đóng góp khoa học trung tâm là một algorithm mới hay một synthetic stress-test
   protocol? Nếu là algorithm, novelty so với humanitarian event entity
   resolution gần nhất nằm ở đâu?
2. Vì sao product được tune \(\tau_t\) và bốn \(\sigma\), còn additive không tune
   \(\tau_t\) và chỉ dùng hai \(\sigma\)?
3. Vì sao việc dùng ground-truth incident labels và loại unlinked reports trong
   dispatch không được nêu rõ trong Experimental Design?
4. Một hệ thống có zero noise rejection và khoảng 35 false destinations cho 16
   incidents có thể đáp ứng operational burden nào?
5. Near-duplicate transitive closure xử lý thế nào khi A gần B, B gần C nhưng A
   không gần C?
6. Có nguồn dữ liệu hoặc generator độc lập nào để kiểm tra transfer ngoài họ
   generator v4 hay không?
7. Tác giả dự định nộp long paper hay short paper, khi PDF hiện có 11 trang?
8. Vì priority không thắng legacy/nearest-first trên outcomes chính, tại sao nó
   vẫn được đặt ngang hàng với clustering trong title?

## 11. Final Recommendation

### **Major Revision**

Bài không nên được Accept hoặc Minor Revision ở trạng thái hiện tại, vì các sửa
đổi cần thiết liên quan đến novelty positioning, calibration fairness,
out-of-generator validity, end-to-end dispatch và venue compliance — không chỉ
là chỉnh câu chữ.

Tôi chưa đề nghị Reject vì bản thảo có ba nền tảng khoa học đáng giữ: protocol
held-out tương đối chặt, traceability/reproducibility nội bộ rất mạnh, và tác giả
báo cáo trung thực các kết quả bất lợi. Nếu xử lý các vấn đề bắt buộc nêu trên,
bài có thể trở thành một nghiên cứu synthetic stress-test có giá trị. Nếu không
có external/end-to-end evidence, bài cần giảm mạnh vai trò “rescue system” và
“priority contribution”, thay vì diễn giải tiếp kết quả within-generator như
bằng chứng hiệu quả ứng dụng.
