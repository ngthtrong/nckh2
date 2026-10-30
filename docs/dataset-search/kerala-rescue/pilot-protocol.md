# Pilot KeralaRescue trước khi chạy lại RQ

Phiên bản **đề xuất v0.1, chưa khóa/chưa chạy**. Phần này cụ thể hóa [protocol chung](../evaluation-protocol.md) cho nguồn Kerala; không tự thay các RQ hoặc công thức bài hiện tại. Chỉ bắt đầu lấy mẫu khi đã có tệp cấp yêu cầu, điều khoản sử dụng và data dictionary đủ để đọc trường.

## 1. Tiếp nhận và kiểm tra

- Giữ bản thô ngoài Git; điền [manifest](intake-manifest.template.json), thêm từng tệp với đường lưu cục bộ, bytes, SHA-256, nguồn và phạm vi. Giữ riêng bản trước/sau khử trùng, cùng processing log nếu có. Đối chiếu 45.322/39.950 do bài công bố, không ép tệp mới phải khớp khi phạm vi khác.
- Xác nhận grain: một hàng là một request hay một update/phiên bản. Không gộp nhiều update thành nhiều yêu cầu độc lập; cũng không xóa yêu cầu lặp tự nhiên trước khi khảo sát RQ1.
- Đo tỷ lệ thiếu, ID lặp, văn bản trùng, thời gian đọc được, sai số/phân giải địa điểm, loại nhu cầu và ngôn ngữ. Đọc mẫu 50–100 bản ghi có cả thiếu/trùng/người gửi hộ. Đây là kiểm tra mẫu, không tự là gold sự cố.
- Xác nhận `coordinate_accuracy` trong bài có tương ứng với `latlng_accuracy` của mã hay không. Giữ tách vị trí người gửi, vị trí yêu cầu trong nội dung và điểm suy ra. Tiêu chí vị trí cho RQ1 phải phù hợp khoảng cách giữa các sự cố, không lấy nguyên cổng 1.000 m dùng cho bản đồ của bài gốc.
- Xác nhận timezone từ nguồn; giữ chuỗi gốc, phương pháp chuyển đổi, và flag bất định. Không tự xem `dateadded` là UTC hay thay bằng `update_ts`.

Đầu ra giai đoạn này: `intake-manifest.json`, profile schema, bảng missingness và danh mục biến đổi. Chưa có các tệp này trong hồ sơ hiện tại vì **chưa nhận dữ liệu**.

## 2. Chọn pilot và giới hạn thống kê

Khung tham khảo là giai đoạn lũ 12–23/08/2018 mà bài phân tích; độ phủ cuối cùng phải theo snapshot đã nhận. Không mặc định mọi ngày đều có dữ liệu đầy đủ.

1. Lập danh mục cửa sổ theo địa bàn và thời gian từ metadata, ghi cách chọn trước khi xem kết quả thuật toán. Giữ báo cáo nằm trong cửa sổ theo dữ liệu nguồn, kể cả địa điểm chưa chắc; uncertainty được báo trong coverage.
2. Chọn tổng khoảng **100–200 báo cáo** trong cửa sổ trọn vẹn. Nếu quá lớn, thu hẹp cửa sổ theo một quy tắc đã ghi; không random bỏ bản lặp hoặc chọn riêng những cặp dễ nhận ra. Giữ cả nhu cầu không cứu người để người gán xác định lớp thông tin.
3. Đánh giá có đủ nhiều báo cáo về cùng sự cố và các sự cố gần nhau nhưng khác nhau hay không. Nếu không có chứng cứ, kết luận nguồn/pilot chưa phù hợp thay vì dùng ngưỡng L/T để tạo gold.
4. Tập pilot dùng sửa hướng dẫn/extractor là **development**, không đồng thời được gọi là test blind. Chỉ chọn test mới sau khi khóa protocol. Nếu chỉ đủ pilot, báo kết quả khả thi, chưa tuyên bố đánh giá xác nhận.

Kerala 2018 là **một sự kiện thiên tai**. Các ngày/địa bàn không mặc nhiên độc lập. Giữ cùng incident và họ bản sao ở cùng phía split, xử lý các chuỗi kéo qua ranh giới trước khi chọn test. Chỉ báo CI theo block khi biện minh được độ độc lập; nếu không đủ block, mô tả case study và kết quả từng block, không bootstrap từng request để suy luận giữa các thiên tai.

## 3. Gán nhãn độc lập

Dùng [hướng dẫn chung](../annotation-guide.md) và [mẫu trống](../annotation-template.csv); các phần ưu tiên D06 trong tài liệu đợt đầu không áp dụng cho pilot Kerala này.

- Hai người hiểu ngôn ngữ của báo cáo gán riêng lớp thông tin, vai trò/độ hạt địa điểm, same/different/uncertain incident và quan hệ sao chép. Nếu cần dịch, giữ nguyên bản và phiên bản dịch, có người kiểm tra; không đưa nội dung cá nhân lên dịch vụ ngoài trong quy trình này.
- Gán dựa trên người/nhóm người cần giúp, địa chỉ/POI, diễn biến và chứng cứ nguồn. Cùng số liên kết người gửi không đủ để kết luận cùng sự cố; một số có thể đại diện nhiều hộ. Không cần tên hoặc điện thoại thô để tạo dữ liệu công bố.
- Có thể gán các nhóm sự cố độc lập rồi đối chiếu các cặp bất đồng; không bắt người gán quyết định mọi cặp chỉ theo danh sách ứng viên do thuật toán sinh. Ghi cách giới hạn phạm vi rà soát để tránh chỉ tìm thấy các bản sao dễ.
- Đo agreement **trước** thảo luận; báo uncertain và mẫu số. Chỉ tính ARI với phân hoạch đầy đủ, nhất quán trên tập đủ chứng cứ; báo tỷ lệ bị loại khỏi tập đó. Chỉ có nhãn cặp thì dùng pair metrics, không tạo phân hoạch giả.
- Trích F/E/N/V bằng rubric riêng; không sao chép nhãn ưu tiên vào E. Nhãn priority tham chiếu gán riêng trên cùng mốc thời gian và đơn vị, không xem score thuật toán. Giữ nhãn từng người và adjudication, không gọi sinh viên là chuyên gia cứu hộ.

Chỉ gán priority mới nếu thật sự cần nhánh RQ2 bổ trợ và có đủ thông tin. Nếu dữ liệu có `RequestUpdate.status`, trước hết xác minh người gán, ý nghĩa, mốc thời gian, độ phủ và sự thay đổi. Không tự map `cls/otr` thành low hoặc dùng nhãn tương lai làm đầu vào biết trước.

## 4. Tách đầu vào và tham chiếu

| Tệp dự kiến sau khi có dữ liệu | Nội dung | Quyền đọc |
|---|---|---|
| `algorithm_input.json` | ID, L/T/F/E/N/V, support fields thực có, missing flags và provenance phép suy ra | Thuật toán |
| `ground_truth.json` | incident/family tham chiếu, priority tham chiếu đã xác minh/gán mới, kết quả quan sát nếu có | Evaluator sau khi lưu prediction |
| `annotation/*.csv` | Nhãn độc lập, uncertain, lý do và adjudication | Người gán/evaluator |
| `run-manifest.json` | Hash nguồn, config, code revision, split, extractor và định nghĩa metric | Tái lập |

`Q` chỉ được tính theo đúng heuristic của bài khi có support fields cần thiết. `has_image` không có trong export chưa có nghĩa là không có ảnh. Không đủ trường thì chưa chạy score đầy đủ; một nhánh ablation hoặc kernel thiếu F/E phải có tên và giới hạn riêng.

## 5. Chạy thực nghiệm khi đủ điều kiện

Mã benchmark gốc được ghim ở `6ac75c202d04934deb46d84486132e54d42d735f` (RQ1) và `a6be3e988dad1aa442c8c8e158c2bba96b2b7fb9` (nguồn Candidate/RQ2/RQ3); cả hai object hiện tồn tại trong Git. Chưa tạo checkout hoặc sửa notebook vì chưa có schema/snapshot để tích hợp đúng. Khi đủ dữ liệu, phục hồi vào worktree riêng, tạo adapter theo schema đã xác nhận và output suite mới; không ghi đè artifact camera-ready.

- **RQ1:** cùng tập đủ điều kiện, cùng split; Product/Additive được hiệu chỉnh độc lập với ngân sách ngang nhau. Báo ARI, pairwise precision/recall/F1, tách/gộp và coverage. F/E thiếu phải đi đúng nhánh đã công bố, không điền giá trị để giữ kết quả đẹp.
- **RQ2:** giữ nhóm tham chiếu cố định khi kiểm tra tầng score. So với legacy, urgency-only, population-only, linear và random theo protocol chung. Chỉ tính NDCG/correlation khi có đầu vào đủ và nhãn đúng đơn vị; ưu tiên của yêu cầu đơn lẻ không tự là priority của nhóm sự cố. Nhãn người đánh giá chỉ đo phù hợp đánh giá; benefit mô phỏng phải giữ nhãn simulated.
- **Stress trùng lặp:** giữ báo cáo thực và bản perturbation riêng, ghi rõ bản sao nào được tạo. Exact-copy invariance với grouping/input cố định khác với kết quả sau khi chạy lại phân cụm.
- **RQ3:** giữ nguồn lực, scheduler và random draws cố định khi đo tác động lỗi phân cụm. Nếu travel/service/deadline/harm được mô phỏng, ghi riêng từng trường; `supplied` của hệ thống hỗ trợ không là số người được cứu.

Đầu ra cuối: config/split đã khóa, predictions, metric cùng mẫu số, chênh lệch ghép cặp và giới hạn suy luận. Product hoặc score không cần thắng. **Hiện chưa đủ dữ liệu để thực hiện các phép chạy này.**
