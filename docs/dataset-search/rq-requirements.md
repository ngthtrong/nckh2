# Ma trận yêu cầu dữ liệu và giới hạn kết luận

Nguồn phát biểu RQ: [paper/main.tex](../../paper/main.tex), phần Introduction và Experimental Design. RQ1 dùng Generator 3.0; RQ2/RQ3 dùng Candidate 4.1 riêng. Kết quả mới phải ghi suite riêng, không nối quy mô hay chất lượng của hai suite cũ thành một thực nghiệm chung.

## RQ1: Product so với Additive khi hiệu chỉnh độc lập

| Thành phần | Yêu cầu cho đánh giá trực tiếp | Sai lầm cần ngăn |
|---|---|---|
| Đơn vị | Báo cáo, cùng sự cố cứu hộ nhỏ lẻ, trong một cửa sổ quan sát xác định | Dùng tên trận bão hoặc humanitarian class làm `incident_gold` |
| L | Địa điểm mà báo cáo cần cứu đề cập, với độ phân giải và bất định được ghi nhận | Dùng GPS của người đăng hoặc tâm thành phố như địa chỉ nạn nhân |
| T | Thời gian báo cáo được tạo; phân biệt với thời gian sự cố và thời gian hệ thống nhận | Lấy ngày đầu thiên tai làm thời gian của mọi tin |
| F/E | Chứng cứ mức ngập/khẩn cấp quan sát hoặc trích xuất có nguồn gốc | Tạo bằng label của bộ sinh, điền zero cho thiếu hoặc lấy `postPriority` làm E |
| Gold | Nhãn cùng/khác sự cố có lý do và chứng cứ, gán độc lập với thuật toán | Tạo gold bằng DBSCAN/ngưỡng khoảng cách đang so sánh |
| Trùng lặp | Phân biệt bản sao nội dung, chuyển tiếp và nhiều quan sát độc lập | Coi ID lặp do cách lưu annotations là transport-copy tự nhiên |

Đầu ra: ARI, pairwise precision/recall/F1 cho cùng sự cố, lỗi split/merge, tỷ lệ đưa vào manual review và độ bao phủ. Không báo ARI như phần trăm báo cáo đúng. Nếu gold chỉ gồm pair rời rạc, chỉ đánh giá pair được gán; chưa tính ARI khi chưa có phân hoạch đầy đủ, nhất quán.

## RQ2: Điểm theo họ bằng chứng và mục tiêu độc lập

Đầu vào của score gốc gồm E/F/N/V/Q cùng nhóm bằng chứng. Cần bảng ánh xạ nêu rõ mỗi trường là quan sát, suy ra, thiếu hay mô phỏng. `confidence` của người gán địa danh IDRISI (1/2/3), model confidence, và Q heuristic trong bài là ba khái niệm khác nhau.

Gold xếp hạng phải cùng đơn vị với danh sách được xếp hạng. `postPriority` của TREC hỗ trợ mức **tin nhắn**; chưa có phép chuyển tự động đã được xác nhận sang lợi ích hoặc ưu tiên ở mức **cụm sự cố**. Không lấy max/mean nhãn TREC của cụm rồi gọi đó là gold cứu hộ.

Hai nhánh cần báo riêng:

- **Benefit alignment hiện tại:** vẫn dùng lợi ích do evaluator mô phỏng, giữ nguyên ý nghĩa và giới hạn RQ2 của bài.
- **Bằng chứng ngoài bộ sinh:** xếp hạng theo đánh giá thông tin của con người, chỉ sau khi có đầu vào score và nhãn cùng đơn vị. Nếu thiếu, chỉ làm audit/chọn pilot, chưa báo NDCG của score gốc.

Exact-copy invariance kiểm tra khi grouping và score inputs cố định. Khi gom lại cụm sau perturbation, đó là phép thử end-to-end khác. Nhãn không phải “fake” không được suy thành nhãn thật; không quan sát tin giả không có nghĩa đã kiểm chứng độ bền trước tin giả.

## RQ3: Lỗi phân cụm truyền sang điều phối

| Phần | Có thể lấy từ quan sát | Khi thiếu |
|---|---|---|
| Nhu cầu | Báo cáo và sự cố được gán nhãn; thời gian/vị trí đã xác minh | Ghi độ bao phủ, đưa bản ghi mơ hồ sang review |
| Nguồn lực | Vị trí, ca trực, năng lực, thời điểm sẵn sàng của đội/phương tiện | Mô phỏng với giả định khóa trước, không mượn số xe sau cứu hộ làm nguồn lực biết trước |
| Di chuyển/phục vụ | Mạng đường, ngập/chặn đường theo thời gian; thời gian xử lý | Phân tích độ nhạy theo mô hình đã công bố; dữ liệu đường thật không biến travel time giả định thành quan sát |
| Kết quả | Nhật ký dispatch/arrival/completion được liên kết, deadline/harm có nguồn định nghĩa | Chỉ báo các metric mô phỏng; không tự tạo “số người thực được cứu” |

England D05 là nguồn quan sát nguồn lực/kết quả ở mức incident đã ẩn danh, hữu ích tham khảo phân bố. Không nối các hàng của nó vào yêu cầu Harvey như cùng sự kiện, không coi năm tài chính là release time, không lấy `EVACUATIONS_CODE` làm số người mắc kẹt N. Các code và band phải đọc bằng data dictionary.

Lịch sử chính sách thật không cung cấp kết quả phản thực tế của mọi chính sách khác. Đánh giá lại mô phỏng trên yêu cầu thực vẫn là nghiên cứu mô phỏng có đầu vào thực.

## Mức bằng chứng và cổng lựa chọn

Mỗi ô RQ trong [datasets.csv](datasets.csv) dùng một trong bốn mức: `đánh giá trực tiếp`, `bằng chứng bổ trợ`, `cần bổ sung nhãn`, `không phù hợp`. Mức phù hợp và quyền truy cập là hai cột độc lập. Hiện **không có nguồn đạt mức đánh giá trực tiếp toàn bộ RQ** ở trạng thái đã kiểm tra.

Thứ tự xét là: đúng đơn vị/bài toán → nhãn độc lập → quyền truy cập và truy vết → chất lượng/độ bao phủ → công sức. Điều kiện loại không bị che bởi điểm tổng cao. Chỉ một điểm L tồn tại hoặc nhiều hàng không đủ vượt cổng khoa học.

Giữ nguyên hiện trạng và công bố mọi cổng chưa đạt. Các điều kiện này là protocol đề xuất cho nghiên cứu tiếp theo, không phải kết quả nghiên cứu đã xảy ra.
