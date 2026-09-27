# Đối chiếu bản gốc, phản biện và bản hiện tại

Ngày kiểm tra: 2026-09-11 UTC. Phạm vi: đánh giá nội dung và bằng chứng; không sửa bản thảo, thuật toán hoặc dữ liệu thực nghiệm.

Nguồn đối chiếu trực tiếp:

- Phản biện: `docs/src_review_1_2_3.md`.
- Bản gốc do tác giả chỉ định: `docs/ISDS_2026_paper_6444.pdf`, 15 trang. Không thay bản PDF này bằng một Git tag khi xác định nội dung gốc.
- Bản hiện tại: `paper/main.tex` và `paper/main.pdf`, 15 trang; gồm cả thay đổi chưa commit tại thời điểm kiểm tra, HEAD `5fad10d`.
- CSV, checkpoint, manifest và trình kiểm tra trong `src/results/`.

## 1. Kết luận

Bản hiện tại vẫn đi đúng tinh thần bản gốc: kiểm tra một pipeline clustering → ranking → dispatch, làm rõ giới hạn toán học và thực nghiệm, công khai kết quả âm. Không có cơ sở kết luận rằng tác giả đã đổi mục tiêu từ một bài chứng minh hiệu quả sang một bài báo kết quả âm để né phản biện: ngay trang 2 bản gốc đã xác định giá trị khoa học nằm ở các kết quả âm và kết quả về giới hạn có thể kiểm tra được.

Các yêu cầu giải thích thuật ngữ, lựa chọn baseline, giá trị đóng góp và bổ sung stress-test được đáp ứng đáng kể. Tuy nhiên, giải thích rõ hạn chế không đồng nghĩa khắc phục hạn chế của phương pháp: chưa chứng minh ưu thế tổng quát, độ đại diện thực địa, khả năng chống thông tin sai lệch hoặc cải thiện điều phối.

## 2. Đối chiếu từng nhóm phản biện

| Ý phản biện | Bản gốc | Bản hiện tại và bằng chứng | Đánh giá |
|---|---|---|---|
| R1.1 / R3: phương pháp không vượt baseline nhất quán; cần nêu lợi ích | Abstract, Introduction và Conclusion đã thừa nhận không có ưu thế tổng quát, nhưng diễn giải lợi ích còn khái quát | Introduction nêu ba giá trị: chặn khoảng cách cạnh có thể kiểm tra, bất biến điểm khi sao chép chính xác dưới nhóm bằng chứng cố định, và kiểm tra hậu quả downstream (`main.tex:161–172`) | Đã làm rõ đóng góp; không khắc phục hiệu năng yếu |
| R1.2 / R3: tính thực tế và đại diện của dữ liệu synthetic | Đã phân biệt generator 3.0 và Candidate-4.1, nhưng mô tả nguồn neo địa lý ngắn | Experimental Design có bảng construction, phân biệt địa lý với báo cáo/nhãn/outcome mô phỏng; Discussion công khai thiếu snapshot nguồn, checksum và lineage (`main.tex:442–492`, `773–778`) | Đáp ứng giải trình tốt hơn; chưa xác lập representativeness |
| R1.3 / R3: bổ sung robustness dưới noise và duplication | Có ranking stress và sensitivity; chưa có RQ1 measurement/copy stress mới | Thêm control + GPS 100/300 m + thời gian 15/60 phút + copy 2x/5x; 5 phương pháp × 40 test runs × 7 điều kiện = 1.400 fits (`main.tex:494–507`, `607–631`) | Đã bổ sung thực nghiệm trực tiếp, phù hợp yêu cầu |
| R3: varying operational conditions | RQ3 đã sử dụng ba điều kiện nguồn lực, nhưng kết quả chủ yếu gộp | Thêm harm và deadline-miss từng điều kiện lean/nominal/surge; inference vẫn 40 seed-level pairs (`main.tex:677–701`) | Mở rộng báo cáo kết quả có sẵn; không phải một bộ chạy mới |
| R1 minor / R3: định nghĩa thuật ngữ | Liệt kê tên nhưng thiếu diễn giải ngay lúc xuất hiện | Introduction giải thích Product Louvain, Product Leiden, Additive Louvain và matched-density Additive (`main.tex:135–142`) | Đã xử lý trong phần mở đầu; Abstract vẫn có thể làm rõ ngắn hơn về Louvain/Leiden |
| R1 minor / R3: lý do chọn baseline | Danh sách baseline, ít nói vai trò từng nhóm | Giải thích composition, community detection, mật độ, hình học; ranking có multiplicity, single-factor, linear, random, nearest-first (`main.tex:418–422`, `509–529`) | Đã xử lý ở mức hợp lý cho bài 15 trang |
| R2.1 / R3: ARI tốt không kéo theo ranking/dispatch tốt | Đã là kết quả âm trung tâm của bài | Giữ RQ1 và Candidate-4.1 tách biệt; nêu RQ2 dùng oracle groups để cô lập ranking và RQ3 dùng predicted clusters; giữ các kết quả dispatch bất lợi (`main.tex:550–561`, `633–648`, `677–701`) | Đáp ứng phân tích và giới hạn suy luận; chưa cải thiện downstream alignment |
| R2.2 / R3: misinformation, policy, field readiness | Đã phủ nhận các tuyên bố sẵn sàng triển khai | Tiếp tục công khai high-confidence campaign, không có expert validation, không có field/OOD test (`main.tex:742–778`) | Trung thực và phù hợp phạm vi; hạn chế khoa học vẫn còn |

## 3. Những thay đổi giữ đúng hướng và sửa được vấn đề cũ

1. **Giữ nguyên câu hỏi và kết quả nền.** Ba RQ, hai bộ dữ liệu tách biệt, ranh giới observable/evaluator, Product/Additive và điểm ưu tiên có chặn đều còn. Các số chủ chốt không đổi: ARI Additive .9191, Product Louvain .9072, Product Leiden .9165; NDCG@5 revised .6669 so với random .6763; dispatch không có ưu thế tổng quát so với legacy và bất lợi so với nearest-first.
2. **Sửa giả mã sparsification.** Trang 6 bản gốc ghi hợp của toàn bộ cạnh qua threshold với top-k của chính tập đó; biểu thức này giữ toàn bộ cạnh qua threshold và làm top-k mất tác dụng. Bản mới chọn top-k có hướng sau threshold rồi hợp đối xứng. Điều này phù hợp `threshold_knn` trong builder của stress notebook (`src/results/build_rq1_reviewer_stress_notebook.py:422–439`). Đây là sửa cách mô tả, không phải bằng chứng đổi thuật toán để đạt kết quả khác.
3. **Bỏ diễn giải nhân quả quá mạnh.** Trang 5 bản gốc vừa nói cùng grid, vừa nói separate quantile grids; còn mô tả matched-density như cô lập composition operator. Bản mới ghi grid riêng rõ ràng và thừa nhận density-matching không cô lập hiệu ứng nhân quả của operator.
4. **Thu hẹp đúng phạm vi bất biến duplicate.** Bản gốc nói exact-duplicate invariance khá rộng. Bản mới gắn với score, grouping và inputs cố định; đồng thời cho thấy copy 5x làm ARI graph variants xuống khoảng .30. Hai kết quả này không mâu thuẫn vì một kết quả xét score với nhóm cố định, kết quả kia xét clustering khi đầu vào graph thay đổi.
5. **Bổ sung kết quả âm phù hợp tiêu đề stress-testing.** Product Louvain ở copy 5x giảm .6108 ARI, CI chưa hiệu chỉnh [-.6318, -.5881]. Đây là bằng chứng mới trực tiếp về giới hạn, không phải bằng chứng rằng Product tốt hơn hoặc robust hơn.

Sensitivity 21 configurations × 40 seeds = 840 observations đã có trong PDF gốc trang 12–13. Không nên tính đây là thực nghiệm mới sau phản biện. Tương tự, việc trình bày đủ 11 scenario RQ2 và ba điều kiện RQ3 là mở rộng báo cáo; thực nghiệm mới nổi bật là RQ1 fixed stress.

## 4. Điểm còn cần xử lý

### 4.1. Lỗi nhỏ trong hệ quả toán học, có từ bản gốc — đã sửa

Phiên bản được audit ban đầu phát biểu `D < h r` cho connected component rồi ghi singleton có `h = D = 0`, khiến áp dụng bất đẳng thức nghiêm cho singleton thành `0 < 0`. Bản camera-ready sau audit đã giới hạn bound nghiêm cho component có ít nhất hai đỉnh và tách riêng singleton có `D=h=0`. Định lý chặn độ dài cạnh và kết quả thực nghiệm không thay đổi.

### 4.2. Đừng coi toàn bộ phản biện đã được khắc phục ở cấp phương pháp

Downstream alignment, misinformation robustness và field representativeness vẫn chưa đạt. Cách trả lời chính xác là đã phân tích thêm, bổ sung stress-test và thu hẹp kết luận. Không thể ghi rằng phương pháp nay đã giải quyết điều phối cứu hộ hay đáp ứng triển khai thực tế.

### 4.3. Hồ sơ tái lập và đường dẫn công bố chưa đóng hoàn toàn

Verifier đạt kiểm tra số học và tính nhất quán nội bộ, nhưng vẫn báo thiếu ZIP gốc/xác nhận runtime-resume của hai lượt và executed notebook v2. Bản thảo đã ghi notebook v2 còn pending. Không nên gọi đây là tái lập đầy đủ xuyên môi trường.

Remote được kiểm tra sau audit: nhánh công khai `clean` trỏ tới commit `5fad10d` và chứa hai artifact stress; tag `v1.0.1` vẫn trỏ tới `be95d4c`. Bản camera-ready liên kết commit công khai chính xác và nói rõ kết quả stress mới không thuộc release `v1.0.1`.

### 4.4. Hai cải thiện diễn giải nhỏ

- Bảng RQ2 cho thấy low-confidence urgency inflation cũng bất lợi cho revised (.0034 so với .0012 về priority drift), ngoài population, vulnerability và coordinated campaign. Bản sau audit đã bổ sung urgency vào đoạn tóm tắt.
- Abstract trước đây xuất hiện Louvain/Leiden trước phần định nghĩa ở Introduction. Bản sau audit đã gọi rõ chúng là community detectors và Product/Additive là graph-affinity constructions ngay lần xuất hiện đầu.

Không có cơ sở từ lần kiểm tra này để yêu cầu thiết kế lại phương pháp hoặc chạy thêm một batch lớn. Việc xác lập field readiness sẽ cần nghiên cứu khác, không phải một chỉnh sửa diễn đạt của camera-ready.

## 5. Kiểm tra đã thực hiện và giới hạn

- Trích xuất và đọc nội dung hai PDF bằng PyMuPDF; cả hai có 15 trang. Đối chiếu các đoạn liên quan trong nguồn LaTeX. Không rebuild hoặc đánh giá lại toàn bộ layout ở lần audit này.
- Chạy `PYTHONPATH=/home/ngthtrong/.local/share/nckh2-rq1-audit/site-packages python3 src/results/verify_camera_ready_evidence.py`, exit 0.
- PASS manifest RQ2/RQ3 và provenance RQ3 40 seeds; snapshot/config/data RQ1 và 400 benchmark rows.
- Primary: 288 hashes, 280 checkpoints, 1.400 fits, 92.617 mappings, 35 summaries và 300 bootstrap rows được tính lại.
- V2: 287 hashes, cùng số checkpoint/fit/mapping/summary/bootstrap; 7 smoke checkpoints/35 fits khớp full trừ runtime.
- So sánh 1.400 khóa primary/v2: 43 thay đổi ARI chỉ thuộc graph methods tại copy 2x. Không gộp hai lượt thành cỡ mẫu lớn hơn, không quy nguyên nhân cho Python.
- PASS manuscript quotations, formula labels và heatmap integration. Đây là kiểm tra những claim mà verifier bao phủ, không phải chứng minh mọi câu hoặc định lý trong bài đều đúng.
- `git diff --check` đạt trước khi tạo báo cáo. Không chạy lại clustering hoặc tạo dữ liệu nghiên cứu mới.

SHA-256 để nhận diện đúng phiên bản đã đọc:

```text
original PDF  2e28876edc652b8322dd6fd5d8e404fce939a5a21cade7be444f72c5e47c6aa7
current PDF   917d83a4be423f5a96d2bc257903107cdc08f9dcda9b4d3f0753fe646875f623
current TeX   4652f1c5b8565e02178bc459ea730ba684b96c4b35b94801c341895d32a2aaaf
review file   8d3df7b535fe27735229cc3da693c31519732c50850bad6f8a2feeecf946c422
```
