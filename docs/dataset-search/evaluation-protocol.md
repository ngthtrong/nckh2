# Protocol đề xuất bổ sung đánh giá RQ1–RQ3

Trạng thái: **đề xuất, chưa chạy**. Giữ nguyên RQ, công thức và artifact gốc. Protocol này chưa được xem là đã tiền đăng ký; phải khóa bản cấu hình và checksum trước khi mở kết quả test mới.

## 1. Cổng dữ liệu trước thí nghiệm

1. **Quyền truy cập/provenance:** có tệp dùng được, phiên bản/checksum, điều khoản và danh mục các phép chuyển đổi. Nguồn theo yêu cầu chưa nhận được không vượt cổng này.
2. **Đúng đơn vị:** phân biệt disaster, report, evidence family, rescue incident, reference fact và dispatch job. Một disaster chứa nhiều sự cố; nhiều tin không chắc là nhiều người hoặc nhiều sự cố.
3. **Vị trí/thời gian:** chỉ nhận vào phân tích vị trí chính các địa điểm address/POI đã được kiểm tra là nơi yêu cầu cứu, đủ phân giải; lưu độ bất định. Không dùng tâm city/state/country làm điểm cần cứu. `created_at` là thời gian đăng, không phải receipt time; thời gian suy từ platform ID phải được kiểm tra, ghi phương pháp và không gọi là quan sát độc lập mới.
4. **Đầu vào gốc:** lập bảng cho L/T/F/E/N/V/Q và support fields. Mỗi giá trị có vai trò observed/derived/missing/simulated, nguồn và phiên bản extractor. Nhãn tham chiếu không vào extractor hoặc score. `has_image` không biết thì giữ unknown; không coi thiếu cột là “không có ảnh”.
5. **Gold:** sự cố và mức ưu tiên do hai người đánh giá độc lập theo [hướng dẫn](annotation-guide.md), hoặc nhãn nguồn đã xác nhận đúng đơn vị. Chưa có gold thì chưa báo hiệu quả thuật toán.

Nếu bộ dữ liệu chỉ đủ một phần, ghi phần đó thành evidence bổ trợ. Ablation hoặc score sửa cho phù hợp dữ liệu thiếu là thí nghiệm riêng có tên/cấu hình rõ ràng, không báo như kết quả của công thức đầy đủ ban đầu.

## 2. Nguồn và đơn vị phân tích được chọn

**RQ1 pilot:** ưu tiên phần English Harvey IDRISI-D vì tệp thật có text/time/OSM; chỉ chọn sau kiểm tra vai trò và độ phân giải vị trí. D06 hiện chỉ kiểm tra train Harvey; phải mở rộng kiểm tra các event/partition công khai trước đánh giá ngoài sự kiện. DisasterLocDesc là dự phòng có điều kiện khôi phục full tweet; nhãn footprint không thay thế incident gold.

**RQ2:** TREC-IS là nguồn ưu tiên tham khảo ưu tiên thông tin. Chuẩn hóa mỗi `(event, postID)` thành một đơn vị; chỉ dùng văn bản không rỗng và priority đã xác định. Các bản lặp phải cùng reference priority và không mâu thuẫn văn bản; nếu mâu thuẫn, chuyển review và lưu nguyên artifact. Không flatten `multipleJudgements` thành thêm mẫu. Loại `Unknown` khỏi metric cần ordinal gold, ghi mẫu số và tỷ lệ bị loại.

`postPriority` không được gán vào E. Nhãn TREC chỉ hỗ trợ metric mức tin nhắn; đánh giá score mức cụm đòi gold nhóm sự cố và đánh giá ưu tiên cụm độc lập. Chưa có quy tắc ánh xạ nhãn tin → lợi ích cụm được xác nhận nên không tự dùng max/mean. Nếu không đủ F/E/N/V/Q hoặc không có cluster-level gold thì nhánh empirical ranking gốc giữ trạng thái chưa đủ dữ liệu.

**RQ3:** chỉ dùng cùng tập yêu cầu đã vượt các cổng của pilot. D05 là nguồn bổ trợ để chọn khoảng hợp lý cho nguồn lực, không ghép hàng England với Harvey như cùng một tình huống. Với dữ liệu banded, giữ khoảng hoặc chạy sensitivity theo biên; không coi code là số đo, không tự chọn midpoint làm truth.

## 3. Chia tập và khóa protocol

- Nhóm ID, bản sao và các phiên bản cùng nội dung vào một phía của split. Lập ledger giao thoa theo ID và nội dung chuẩn hóa giữa tất cả nguồn được dùng; số overlap 0 ở một cặp/tập con không chứng minh toàn bộ nguồn độc lập.
- Ưu tiên chia theo disaster event cho development/calibration/test; không random-split các tweet cùng sự cố qua test. Với một sự kiện, chỉ làm case study, chia block thời gian và giữ incident/family cùng phía.
- Official IDRISI-D test không phát hành. Không gọi train/dev công khai là official held-out test. Gold mới có thể blind đối với nhóm phát triển sau khi khóa, nhưng không xóa lịch sử các partition từng được sử dụng.
- Khóa cùng tập đủ điều kiện, danh sách baseline, feature extraction, ngân sách calibration, metrics, tie handling, random seed và quy tắc loại trước test. Product/Additive có ngân sách hiệu chỉnh ngang nhau; cấu hình được chọn độc lập trên calibration.
- Inference chỉ đọc `algorithm_input.json`; `ground_truth.json` chứa incident IDs/reference priority/outcomes. Lưu dự đoán/lịch và checksum trước khi evaluator nối gold. Adapter dữ liệu ở giai đoạn sau; không đưa gold vào graph hoặc scheduler.

## 4. Phép so sánh và thống kê

| Nhánh | Thiết kế | Đầu ra chính |
|---|---|---|
| RQ1 | Product/Additive trên cùng tập, cùng phân chia; baseline hiện có được giữ | ARI, pairwise F1, split/merge, coverage/manual-review, runtime |
| RQ2 alignment | Nhóm gold cố định, đầu vào đủ và nhãn cùng đơn vị; legacy/urgency-only/population-only/linear/random | NDCG@5, Spearman, overlap top-5; xác định rõ reference là thông tin hay benefit mô phỏng |
| RQ2 stress | Copy 2/5/10 lần; grouping/score inputs khóa cho invariance; tách phép thử gom lại cụm | Score/rank drift, churn; perturbation được tạo phải gắn nhãn synthetic |
| RQ3 | Graph/destinations/priority → scheduler khóa; oracle grouping là đối chứng chẩn đoán | Arrival, unmet demand, duplicate/false dispatch; harm/deadline chỉ khi có định nghĩa/nguồn thích hợp |

Đối chứng RQ3 gồm legacy, urgency-only, population-only, linear, random, nearest-first và oracle chẩn đoán. Giữ cùng nguồn lực, mạng đường, service model và random draws khi so sánh các pipeline. Điều kiện nguồn lực lặp trong cùng sự kiện không làm tăng số sự kiện độc lập.

Đánh giá ghép cặp theo sự kiện/đơn vị độc lập được định trước. Báo hiệu số và CI bootstrap 95% với 5.000 lần lấy lại theo sự kiện, seed 42; không bootstrap từng tweet. Với ít sự kiện, nhấn mạnh phân bố/case studies và CI không ổn định; một event không được dùng để suy luận quần thể event. Kiểm định Wilcoxon ghép cặp chỉ dùng khi đủ đơn vị và giả định phù hợp; Holm áp trong các họ baseline/endpoint đã khóa, không chọn metric có lợi sau khi xem kết quả.

Nếu relevance toàn zero hoặc không đủ đối tượng/biến thiên cho metric, đánh dấu undefined và báo mẫu số; không đổi thành điểm tốt. NDCG dùng gain tuyến tính và xử lý tie có ghi nhận, tương thích ý nghĩa scorer trong artifact hiện tại; không so số của hai định nghĩa gain khác nhau.

## 5. Tiêu chí nghiệm thu và tình huống kiểm tra

- Bản ghi không có vị trí cần cứu đủ chính xác → review; tọa độ city centroid không được lặng lẽ đưa vào RQ1.
- Không nhắc số người → N missing; người đã sơ tán hoặc code của số xe không được điền làm N.
- Có nhãn ưu tiên tham chiếu → chỉ evaluator đọc; audit không thấy trường đó trong đầu vào E/Q.
- Một ID có nhiều annotations → một đơn vị đã hợp nhất hợp lệ; annotation disagreements không bị xem là tin giả hoặc thêm tweet.
- Có clone được tạo trong stress → tách khỏi natural duplicates; không đổi kích thước tập độc lập khi clone tăng.
- Bộ nhãn same-incident không nhất quán → chưa tính ARI; báo tỷ lệ thiếu/không chắc, giữ quyết định adjudication.
- RQ3 dùng travel/service/deadline/harm giả định → tất cả bảng/hình ghi simulated, kể cả khi nhu cầu hoặc bản đồ thực.
- Chọn tham số bằng test mới, source checksum đổi, ID/family qua hai split, hoặc scheduler đọc truth → dừng công bố kết quả của lượt đó và sửa protocol/run có phiên bản mới.

Điều kiện thành công là phép đánh giá đúng câu hỏi và báo cả kết quả bất lợi. Product/score không cần thắng để nghiên cứu có giá trị. Kết quả quan sát và mô phỏng được báo riêng; không suy ra field readiness từ ARI, NDCG hoặc bất biến copy.
