# Checklist sửa `short.pdf`

## Mục tiêu

Hoàn thiện bài theo hướng: **công thức đơn giản, có tính chất toán học rõ ràng, và được đánh giá bằng kết quả thực trên 80 synthetic runs**.

Nguồn đối chiếu:

- `short.pdf`: bản thảo cần sửa.
- `Test_Cij_vs_GroundTruth_Colab.ipynb`: notebook thực nghiệm hiện tại.
- `flood_hybrid_EMSR848_80_runs.zip`: 80 bộ dữ liệu dùng đánh giá.
- `main.pdf`: nguồn tham khảo cho phát biểu đầy đủ của các bound; không chuyển kết quả thực nghiệm từ bài này sang `short.pdf`.

---

## P0 — Các sửa đổi bắt buộc

### 1. Làm rõ vai trò của \(m_{ij}\) và \(a_i a_j\)

- [ ] Định nghĩa indicator quan sát chung:

  \[
  I_F(i,j)=\mathbf 1(F_i,F_j\text{ đều quan sát được}),
  \qquad
  I_E(i,j)=\mathbf 1(E_i,E_j\text{ đều quan sát được}).
  \]

- [ ] Định nghĩa:

  \[
  m_{ij}=I_F(i,j)+I_E(i,j).
  \]

- [ ] Giải thích ba trường hợp:

  - \(m_{ij}=2\): dùng đủ flood và urgency.
  - \(m_{ij}=1\): chỉ có một thuộc tính chung; similarity tối đa bị giảm còn \(1/2\).
  - \(m_{ij}=0\): không có thuộc tính chung; đặt \(C_{ij}=0\).

- [ ] Giải thích mục đích: không zero-impute dữ liệu thiếu và không cho cặp thiếu dữ liệu đạt context similarity quá cao.

- [ ] Định nghĩa admission indicator:

  \[
  a_i=\mathbf 1(L_i,T_i\text{ đều quan sát được}).
  \]

- [ ] Giải thích:

  \[
  a_i a_j=0 \Longrightarrow w_{ij}=0.
  \]

  Report thiếu location hoặc event time không được tự động đưa vào graph; nó phải đi vào review path.

- [ ] Nêu rõ \(m_{ij}\) và \(a_i a_j\) là **missing-data/fail-closed extensions**, không phải lý do tạo ra kết quả tốt trên tập 80 runs hiện tại.

- [ ] Nêu rõ trong `flood_hybrid_EMSR848_80_runs.zip` hiện tại:

  \[
  m_{ij}=2,\qquad a_i=a_j=1
  \]

  cho mọi report/cặp được đánh giá.

- [ ] Vì vậy, công thức thực sự được kiểm nghiệm trên 80 runs rút gọn thành:

  \[
  C_{ij}=\exp\left(
  -\frac{|F_i-F_j|}{\tau_F}
  -\frac{|E_i-E_j|}{\tau_E}
  \right).
  \]

- [ ] Không tuyên bố đã kiểm chứng missingness robustness nếu chưa có dữ liệu thiếu thật.

#### Đoạn văn đề xuất

> The observation factors make the formulation applicable to incomplete reports. The factor \(m_{ij}/2\) discounts pairs sharing only one contextual attribute, while \(a_i a_j\) excludes reports without both location and event time from automatic graph construction. In the present 80-run dataset, all reports contain location, event time, flood, and urgency observations; hence \(a_i a_j=1\), \(m_{ij}=2\), and the evaluated context expression reduces to the complete-observation form. Missing-data robustness is therefore not claimed as an empirical result of this study.

---

### 2. Phát biểu đầy đủ miền của product bound

- [ ] Giữ product similarity:

  \[
  w_{ij}^{\times}=a_i a_jG_{ij}(\beta T_{ij}+\gamma C_{ij}),
  \qquad B=\beta+\gamma.
  \]

- [ ] Phát biểu đầy đủ ba miền của threshold:

  \[
  r_\theta^{\times}=\sigma\sqrt{2\log(B/\theta)}.
  \]

  - \(0<\theta<B\): mọi retained edge thỏa \(d_{ij}<r_\theta^{\times}\).
  - \(\theta\ge B\): strict retained-edge set rỗng.
  - \(\theta\le0\): threshold không tạo ra finite geographic cutoff nói chung.

- [ ] Giữ từ **similarity** hoặc **edge-weight function**; không gọi đây là Mercer/PSD kernel nếu không có chứng minh tương ứng.

- [ ] Dùng retained-edge rule nhất quán trong bài và code: \(w_{ij}>\theta\), không phải \(w_{ij}\ge\theta\).

#### Theorem đề xuất

> **Theorem 1 (Product edge localization).** Let \(B=\beta+\gamma>0\). If \(0<\theta<B\), every edge retained under the strict rule \(w_{ij}^{\times}>\theta\) satisfies \(d_{ij}<\sigma\sqrt{2\log(B/\theta)}\). If \(\theta\ge B\), the strict retained-edge set is empty. If \(\theta\le0\), the threshold alone provides no non-trivial finite geographic cutoff in general.

---

### 3. Thêm conditional component corollary

- [ ] Định nghĩa \(h\) là unweighted hop diameter quan sát được của một connected component.

- [ ] Định nghĩa \(D\) là geographic diameter của component.

- [ ] Thêm hệ quả:

  \[
  D<hr_\theta^{\times}.
  \]

- [ ] Giải thích chứng minh dùng triangle inequality dọc theo đường đi nhiều nhất \(h\) cạnh.

- [ ] Xử lý singleton riêng: \(h=D=0\).

- [ ] Giữ cảnh báo bắt buộc:

> This is a conditional post-hoc component bound, not an ex-ante compactness guarantee; the pipeline does not control \(h\), and long transitive chains remain possible.

- [ ] Không diễn giải edge localization thành bảo đảm cluster compactness.

---

### 4. Thêm additive comparator và finite-region bound

- [ ] Thêm công thức đơn giản:

  \[
  w_{ij}^{+}=a_i a_j(\alpha G_{ij}+\beta T_{ij}+\gamma C_{ij}).
  \]

- [ ] Không thêm learned kernel, attention hoặc trọng số phức tạp.

- [ ] Với \(B=\beta+\gamma\), phát biểu đầy đủ:

  - Nếu \(\alpha>0\) và \(B<\theta<B+\alpha\):

    \[
    d_{ij}<r_\theta^{+}
    =\sigma\sqrt{2\log\left(\frac{\alpha}{\theta-B}\right)}.
    \]

  - Nếu \(\theta\ge B+\alpha\): strict retained-edge set rỗng.
  - Nếu \(\theta\le B\): không có finite geographic cutoff nói chung.

- [ ] Sửa claim thành:

> Product composition provides a finite geographic edge bound throughout its nonempty positive-threshold domain, whereas additive composition provides such a bound only when the threshold exceeds the maximum non-geographic contribution.

- [ ] Đưa chứng minh chi tiết sang appendix nếu giới hạn trang; thân bài giữ phát biểu và một đoạn chứng minh ngắn.

- [ ] Không chuyển số liệu additive từ `main.pdf` sang `short.pdf`; phải chạy lại trên đúng 80 runs.

---

### 5. Viết lại Experimental Design đúng dữ liệu 80 runs

- [ ] Thay mô tả paired ID/OOD bằng mô tả đúng của artifact hiện tại.

- [ ] Nêu chính xác:

  - 80 independently seeded synthetic datasets.
  - 16 latent incidents mỗi run.
  - 288–370 reports/run; trung bình hiện quan sát được là 328.6.
  - Exact và near duplicates do generator tạo.
  - 3 coordinated nonincident campaigns/run.
  - 20 reports/campaign, tức 60 attack reports/run.
  - Tất cả 80 runs dùng cùng một generator regime.

- [ ] Nêu rõ đây không phải OOD study vì mọi run dùng cùng cấu hình generator.

- [ ] Nêu rõ dữ liệu hybrid nghĩa là:

  - EMSR848, OSM và WorldPop cung cấp geographic/historical anchors.
  - Rescue incidents là synthetic.
  - Reports là synthetic.
  - Duplicates và coordinated campaigns là synthetic.
  - Ground-truth incident identities là synthetic.

- [ ] Không gọi đây là real-world rescue validation hoặc field validation.

- [ ] Nếu tiếp tục dùng tham số cố định của notebook, báo cáo đúng:

  - \(\sigma=700\) m.
  - \(\tau_t=45\) phút.
  - \(\tau_F=0.25\).
  - \(\tau_E=0.35\).
  - \(\beta=\gamma=0.5\).
  - Raw threshold \(0.05\).
  - \(k=12\).
  - Louvain resolution \(1.0\).
  - Random state \(42\).

- [ ] Nếu chuyển sang calibration/grid search, mô tả lại và tách calibration/test trước khi xem kết quả cuối.

- [ ] Không giữ trong bài các claim chưa có dữ liệu/code hỗ trợ:

  - 40 paired ID/OOD confirmation seeds.
  - Incident count 8–30.
  - Mechanism-shift OOD.
  - Receipt-time snapshot 150 phút.
  - Missingness stress experiments.
  - Access delays và resource scenarios.
  - Dispatch harm/deadline results.
  - 8,320 calibration executions.

#### Đoạn mô tả dữ liệu đề xuất

> We evaluate 80 independently seeded synthetic datasets geographically anchored to the EMSR848 Central Viet Nam flood activation. Each dataset contains 16 latent rescue incidents, simulated reports, exact and near duplicates, and three coordinated nonincident campaigns of 20 reports each. EMSR848, OpenStreetMap, and WorldPop provide geographic or historical context; incident identities, rescue reports, duplicates, campaigns, and evaluation labels remain synthetic. All runs use one fixed generator regime, so the study measures within-generator variation rather than out-of-distribution transfer or field validity.

---

### 6. Đồng bộ notebook với protocol cuối

- [ ] Quyết định một trong hai protocol và dùng nhất quán trong notebook lẫn bài:

  1. Fixed-parameter evaluation; hoặc
  2. Development/calibration/test selection.

- [ ] Không mô tả quantile threshold trong bài nếu notebook vẫn dùng raw threshold `0.05`.

- [ ] Không mô tả \(k\in\{8,16\}\) nếu notebook vẫn dùng \(k=12\).

- [ ] Không mô tả resolution \(\{0.8,1.2\}\) nếu notebook vẫn dùng `1.0`.

- [ ] Thêm formula/config version vào mọi output row.

- [ ] Lưu selected parameters hoặc fixed parameters cùng kết quả.

- [ ] Giữ inference/evaluator separation:

  - Inference chỉ đọc `algorithm_input.json`.
  - Ground truth chỉ được đọc sau khi predictions đã tạo.

- [ ] Thêm test đảm bảo inference không đọc:

  - `gt_cluster`.
  - `is_fake`.
  - `duplicate_of`.
  - `attack_campaign_id`.

---

## P1 — Benchmark cần chạy

### 7. Bộ phương pháp tối thiểu

- [ ] Geography-only:

  \[
  w_{ij}^{G}=G_{ij}.
  \]

- [ ] Product + Louvain:

  \[
  w_{ij}^{\times}=G_{ij}(\beta T_{ij}+\gamma C_{ij}).
  \]

- [ ] Additive + Louvain:

  \[
  w_{ij}^{+}=\alpha G_{ij}+\beta T_{ij}+\gamma C_{ij}.
  \]

- [ ] ST-DBSCAN.

- [ ] HDBSCAN.

- [ ] Product + Leiden nếu chi phí triển khai thấp.

- [ ] Không thêm spectral hoặc mô hình học sâu nếu các baseline trên đã đủ trả lời câu hỏi nghiên cứu.

### 8. So sánh product–additive công bằng

- [ ] Dùng cùng report representation.

- [ ] Dùng cùng candidate pairs.

- [ ] Dùng cùng Louvain implementation và random-state policy.

- [ ] Không dùng cùng raw threshold cho product và additive vì hai thang weight khác nhau.

- [ ] Thực hiện matched-density comparison bằng một trong hai cách:

  - Cùng retained-edge fraction; hoặc
  - Cùng số cạnh/mean degree.

- [ ] Báo cáo retained-edge fraction và mean degree để người đọc kiểm tra matching.

- [ ] Nếu có independent tuning, phân biệt rõ:

  - **Pipeline comparison:** mỗi phương pháp được chọn cấu hình riêng.
  - **Operator comparison:** chỉ đổi product thành additive dưới graph density tương đương.

### 9. Metrics clustering bắt buộc

- [ ] ARI trên incident-linked reports.

- [ ] NMI hoặc pairwise F1; không cần giữ cả hai nếu giới hạn trang.

- [ ] Pairwise precision và recall nếu giữ pairwise F1.

- [ ] Incident split loss.

- [ ] Incident merge loss.

- [ ] False destinations trên 100 reports.

- [ ] Noise/fake rejection rate.

- [ ] Fake absorption rate.

- [ ] Số predicted clusters.

- [ ] Số retained edges hoặc mean degree.

- [ ] Runtime.

- [ ] Geographic diameter của emitted components nếu dùng localization claim trong discussion.

- [ ] Observed hop diameter \(h\) nếu muốn kiểm tra component corollary.

- [ ] Kiểm tra thực nghiệm:

  \[
  \frac{D}{hr_\theta^{\times}}<1
  \]

  cho mọi non-singleton component trong miền hữu hạn.

### 10. Xử lý fake reports trong đánh giá

- [ ] Giữ ARI/NMI chỉ trên `gt_cluster >= 0` và ghi rõ denominator.

- [ ] Không dùng ARI làm bằng chứng noise rejection.

- [ ] Tính riêng:

  - Tỷ lệ fake bị đánh dấu noise/review.
  - Tỷ lệ fake bị hấp thụ vào genuine clusters.
  - Số fake-only destinations.
  - Tổng false destinations.

- [ ] Giữ kết quả adverse/null; không loại run xấu.

---

## P1 — Phân tích thống kê

### 11. Đơn vị phân tích và paired effects

- [ ] Dùng run/seed làm đơn vị phân tích, không coi từng report là quan sát độc lập.

- [ ] Với metric \(M\), tính paired difference theo seed:

  \[
  \Delta_s=M_{\text{product},s}-M_{\text{additive},s}.
  \]

- [ ] Định nghĩa chiều tốt/xấu rõ ràng cho từng metric.

- [ ] Báo cáo:

  - Mean.
  - Standard deviation.
  - Median.
  - Paired bootstrap 95% CI.
  - Paired Wilcoxon signed-rank test.
  - Effect size.
  - Số run hợp lệ và số ties.

- [ ] Holm correction trong family endpoint đã khai báo.

- [ ] Không chỉ báo cáo \(p\)-value.

- [ ] Nếu dùng normal-approximation CI hiện tại (`1.96 * SE`), đổi nhãn cho đúng hoặc thay bằng paired bootstrap CI như bài mô tả.

---

## P1 — Viết lại từng phần của `short.pdf`

### 12. Title

- [ ] Tránh title ngụ ý product thắng nếu kết quả thật không cho thấy điều đó.

- [ ] Title trung lập đề xuất:

> Comparing Product and Additive Similarities for Synthetic Flood-Rescue Report Clustering

hoặc:

> Stress-Testing Simple Similarity Graphs for Synthetic Flood-Rescue Report Consolidation

### 13. Abstract

- [ ] Thay toàn bộ placeholder bằng output thực.

- [ ] Nêu rõ 80 runs thuộc cùng generator regime.

- [ ] Nêu rõ dữ liệu synthetic được geographically anchored.

- [ ] Báo cáo product–additive paired effect.

- [ ] Báo cáo ít nhất một operational metric ngoài ARI.

- [ ] Không claim OOD, dispatch hoặc missingness nếu chưa chạy.

- [ ] Kết luận theo kết quả thật; không mặc định product hoặc additive thắng.

### 14. Introduction và Research Questions

- [ ] Sửa RQ1 thành so sánh product, additive và direct baselines trên 80 synthetic runs.

- [ ] Nếu chưa chạy priority/dispatch, bỏ RQ2–RQ3 tương ứng.

- [ ] Không tuyên bố product similarity là công thức mới.

- [ ] Định vị đóng góp ở:

  - Complete edge-localization analysis.
  - Conditional component bound.
  - Fair product–additive benchmark.
  - Noise-aware evaluation trên 80 runs.

### 15. Methods

- [ ] Phân biệt complete-observation formula và missing-data extension.

- [ ] Trình bày product và additive cạnh nhau.

- [ ] Phát biểu đầy đủ threshold domains.

- [ ] Tách graph construction khỏi evaluator-only ground truth.

- [ ] Đồng bộ mọi tham số với notebook cuối.

### 16. Experimental Design

- [ ] Viết lại đúng 80-run artifact.

- [ ] Mô tả fixed generator regime.

- [ ] Mô tả số incident, report, duplicates và campaigns.

- [ ] Mô tả parameter selection thật sự đã dùng.

- [ ] Mô tả baseline implementation và version.

- [ ] Đăng ký primary/secondary endpoints trước khi đọc benchmark cuối nếu còn khả thi.

### 17. Results

- [ ] Xóa mọi số ước tính.

- [ ] Sinh bảng trực tiếp từ CSV cuối.

- [ ] Table chính nên chứa:

  - ARI.
  - Split/merge hoặc pairwise F1.
  - False destinations.
  - Noise rejection.
  - Mean degree/edge fraction.

- [ ] Báo cáo paired difference product–additive.

- [ ] Không gọi một phương pháp “superior” nếu CI/prespecified endpoints không hỗ trợ.

- [ ] Giữ kết quả bất lợi và ties.

### 18. Discussion

- [ ] Phân biệt mathematical guarantee với empirical accuracy.

- [ ] Nếu additive thắng, viết rõ additive đơn giản nhưng hiệu quả hơn trong regime đã thử.

- [ ] Nếu product thắng, vẫn báo cáo noise/operational trade-offs.

- [ ] Nêu rõ product edge bound không bảo đảm compact components nếu \(h\) lớn.

- [ ] Nêu rõ chưa kiểm chứng missingness extension.

- [ ] Nêu rõ chưa có external validity hoặc field validation.

### 19. Conclusion

- [ ] Kết luận chỉ dựa trên kết quả thực.

- [ ] Không claim deployment-ready.

- [ ] Không claim real-world harm reduction.

- [ ] Không claim misinformation robustness nếu coordinated campaigns vẫn bị gom thành destinations.

---

## P2 — Artifact và khả năng tái lập

### 20. Kết quả cần lưu

- [ ] CSV summary theo run và method.

- [ ] Assignment theo report, run và method.

- [ ] Selected/fixed parameters.

- [ ] Edge counts và mean degree.

- [ ] Raw false-destination/noise metrics.

- [ ] Paired statistical-analysis output.

- [ ] Figures được sinh trực tiếp từ accepted CSV.

### 21. Reproducibility package

- [ ] Lưu notebook sạch, có thể `Run all`.

- [ ] Khóa dependency versions hợp lý; tránh yêu cầu phiên bản tương lai hoặc không tồn tại trên Colab tại thời điểm công bố.

- [ ] Lưu environment/version report.

- [ ] Tạo SHA-256 manifest cho:

  - Dataset ZIP.
  - Notebook/code.
  - Raw results.
  - Final tables.

- [ ] Có một lệnh hoặc một notebook run tái tạo bảng/figure.

- [ ] Không yêu cầu người chạy chỉnh thủ công tên ZIP có hậu tố `(1)`; dùng tên ổn định hoặc tìm file theo pattern có kiểm tra hash.

---

## Những kết quả hiện tại chỉ dùng để kiểm tra pipeline

Notebook hiện ghi nhận trên product + Louvain với fixed parameters:

- ARI trung bình: `0.830577`.
- NMI trung bình: `0.946684`.
- Pairwise F1 trung bình: `0.843339`.
- 80 runs.
- Missing flood rate: `0`.
- Missing urgency rate: `0`.
- Pair fraction \(m_{ij}=2\): `1.0`.

Không đưa các số này thành kết luận cuối trước khi:

- [ ] Chạy additive.
- [ ] Chạy geography-only.
- [ ] Chạy direct baselines.
- [ ] Thêm noise/false-destination metrics.
- [ ] Chốt matching/selection protocol.
- [ ] Sinh paired statistical comparisons.

---

## Điều kiện xem bài gần hoàn thiện

- [ ] Công thức và ký hiệu nhất quán.
- [ ] Product bound có đủ ba miền.
- [ ] Component corollary có cảnh báo đúng mức.
- [ ] Additive bound được phát biểu chính xác.
- [ ] Vai trò \(m_{ij}\) và \(a_i a_j\) được giải thích.
- [ ] Experimental Design khớp hoàn toàn với 80-run artifact.
- [ ] Benchmark tối thiểu hoàn tất.
- [ ] Mọi placeholder được thay bằng số thực.
- [ ] Paired statistics hoàn tất.
- [ ] Abstract, tables, discussion và conclusion đồng bộ.
- [ ] Artifact tái lập được.
- [ ] Authors, funding, conflicts và venue formatting hoàn tất.

Khi toàn bộ P0 và P1 hoàn tất, bài đạt trạng thái gần hoàn thiện về nội dung khoa học. P2 cùng biên tập cuối là điều kiện để phát hành hoặc nộp bài.
