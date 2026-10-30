# Hướng dẫn pilot gán nhãn bổ sung

Trạng thái: **chưa gán nhãn**. Hướng dẫn dành cho hai người gán độc lập trong nhóm; chưa có xác nhận tham gia của chuyên gia cứu hộ. [annotation-template.csv](annotation-template.csv) chỉ có header, không chứa nhãn giả định.

## 1. Mẫu và tổ chức công việc

Ưu tiên thử trên nguồn D06 sau kiểm tra độ chính xác và vai trò địa điểm. Mục tiêu pilot 150 báo cáo, chấp nhận 100–200 nếu tập đủ điều kiện cho phép. Không dùng số hàng làm điều kiện phải điền đủ khi quá ít báo cáo thực sự nói về yêu cầu cứu hộ.

Chọn cửa sổ địa bàn/thời gian trước khi xem kết quả clustering; lấy toàn bộ bản ghi có trong bản phát hành trong cửa sổ đó. Nếu quá 200 hàng, thu hẹp cửa sổ theo quy tắc thời gian đã ghi, không lựa theo việc phương pháp gom đúng/sai. Đây vẫn là sample đã được nguồn lọc, không phải toàn bộ luồng báo cáo của thiên tai.

Trước pilot, dùng một tập nhỏ riêng để cùng hiểu rubric, chỉnh hướng dẫn và ghi phiên bản; loại tập hướng dẫn khỏi đánh giá blind. Hai người gán pilot trong hai tệp riêng; không xem đầu ra thuật toán, `postPriority` hoặc nhãn của nhau. Không gửi báo cáo cá nhân lên dịch vụ bên ngoài để hỗ trợ gán nhãn trong quy trình này.

## 2. Phân biệt lớp thông tin

- `rescue_request`: đang yêu cầu hỗ trợ cứu/di chuyển người ở nơi nguy hiểm.
- `needs_supplies`: cần đồ ăn/nước/thuốc/chỗ ở, chưa khẳng định cần cứu người mắc kẹt.
- `offers_help`: đề nghị nguồn lực/tình nguyện/quyên góp.
- `status_update`: đã được cứu, đang xử lý hoặc hủy yêu cầu.
- `background_or_news`: thông tin chung, tin tức, cảnh báo hoặc hỗ trợ tinh thần.
- `uncertain`: không đủ chứng cứ để chọn.

Humanitarian class của nguồn là gợi ý tra cứu, không bắt người gán phải sao chép lớp đó. `requests_or_urgent_needs` không đồng nghĩa mọi tin đều là rescue_request.

## 3. Nhãn địa điểm, sự cố và bản sao

**Vai trò địa điểm:** `rescue_destination`, `resource_location`, `background_location`, `poster_location`, `uncertain`. Một tin có thể có nhiều địa danh; chỉ chọn nơi yêu cầu cứu nếu nội dung hỗ trợ. Ghi độ phân giải `address_or_precise_poi`, `street`, `neighborhood`, `city_or_coarser`, `uncertain`, cùng nguồn kiểm tra. Không lấy điểm đại diện của polygon lớn làm địa chỉ chính xác.

**Cùng sự cố:** hai tin đề cập cùng một nhóm người/nhu cầu cứu ở cùng một địa điểm trong cùng diễn biến, có chứng cứ nội dung hoặc nguồn đối chiếu. Nhãn pair là `same`, `different`, `uncertain`; ghi lý do và reference, không dùng threshold L/T của thuật toán làm định nghĩa. Cùng địa chỉ có thể là các yêu cầu ở thời điểm khác nhau; cùng câu chữ có thể bị chuyển tiếp qua nhiều địa điểm.

**Họ bằng chứng:** phân biệt `exact_copy`, `near_copy_or_forward`, `independent_observation`, `uncertain`. Mỗi họ bằng chứng và incident là hai lớp nhãn khác nhau. ID lặp trong cách lưu dữ liệu TREC không tự trở thành một họ retweet.

Chỉ tạo `incident_ref`/`evidence_family_ref` sau đối soát các pair và quan hệ bắc cầu. Nếu A cùng B, B cùng C nhưng A khác C, phải giải quyết mâu thuẫn; chưa có phân hoạch nhất quán thì giữ unknown thay vì ép gold để tính ARI.

## 4. Trường đầu vào và ưu tiên tham chiếu

Người trích xuất F/E/N/V ghi nội dung chứng cứ, phép chuyển và trạng thái thiếu; không tự đặt giá trị vì score cần. Số người phải được mô tả là đang cần cứu/mắc kẹt, không là số người đã sơ tán. Mức ngập từ lời kể không là số đo mét nếu nguồn không đo. Không có bằng chứng vulnerability thì missing.

Ưu tiên do người gán đánh giá gồm `low`, `medium`, `high`, `critical`, `uncertain`, hiểu là mức cần chú ý của thông tin cho bài toán khảo sát. Nếu đánh giá ở mức cụm, hai người chỉ xem các báo cáo đã khử bản sao trong cụm tham chiếu và cùng một mốc thời gian; không xem điểm thuật toán hoặc nhãn TREC để quyết định. Không gọi các mức này là deadline y khoa, harm, số mạng người được cứu hoặc đánh giá của chuyên gia.

Người gán phải tách vai trò **trích đầu vào** và **đánh giá reference priority**; bản input không chứa reference labels. Nhãn tham chiếu của TREC chỉ được mở khi chấm nhánh dùng gold của nguồn.

## 5. Độ đồng thuận và nghiệm thu

Tính agreement **trước** thảo luận: tỷ lệ đồng thuận, confusion table, Cohen kappa cho pair same/different có đủ chứng cứ; weighted kappa tuyến tính cho mức ưu tiên có thứ bậc; tỷ lệ uncertain báo riêng. Không đổi uncertain thành low/different. Nếu có phân hoạch đầy đủ từ cả hai người, báo thêm ARI giữa hai phân hoạch với đúng mẫu số.

Sau đó thảo luận bất đồng, lưu cả hai nhãn ban đầu, nhãn adjudicated và lý do. Khi không giải quyết được, giữ uncertain. Nếu agreement thấp, sửa rubric trên tập hướng dẫn và làm pilot phiên bản mới; không lấy agreement sau đồng thuận làm bằng chứng độ tin cậy ban đầu. Agreement cao cũng không chứng minh giá trị chính sách cứu hộ.

Nghiệm thu pilot khi từng nhãn có người gán, phiên bản hướng dẫn, chứng cứ, lịch sử bất đồng; địa điểm mơ hồ và gold thiếu được báo đủ. Pilot có quá ít sự cố/địa điểm phù hợp là kết quả khả thi bất lợi cần giữ, không được bù bằng nhãn máy rồi gọi là gold con người.
