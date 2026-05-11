# Báo cáo tiến độ lần 2

Date: May 9 → May 12
Prority: Now
Status: In progress
Parent item: NCKH 2

[bao_cao.pdf](./bao_cao.md)

xem mục 14 trong [Thuyết minh NCKH - Google Tài liệu](./Thuyết%20minh%20NCKH.md)

- Mobile App: Xây dựng ứng dụng trên nền tảng Flutter, tích hợp nhân xử lý AI để chạy suy luận offline.
- Backend: Phát triển Server sử dụng Python để xử lý các thuật toán phân cụm không gian – thời gian và hiển thị dữ liệu lên bản đồ số.

<aside>

# **Todo: for Review meeting**

- [ ] Bộ dataset
- [ ] Model sẽ chạy
- [ ] Thử các môi trường, công nghệ sẽ sử dụng
- [ ] Bản thiết kế database của hệ thống (backend)
- [ ] Báo cáo đặc tả hệ thống v1 (sẽ còn bổ sung và hoàn thiện)
  - [ ] Use-case Diagram for system
  - [ ] Architecture Diagram
  - [ ] ERD or Class diagram
- [ ] Docs files information of project for LLM

Later:

- [ ] Sequence Diagram
- [ ] Component Diagram

</aside>

<aside>

# draft tính năng hệ thống sản phẩm:

- Người dùng chụp ảnh (hoặc tải ảnh) và nhập một đoạn text mô tả tình trạng hiện tại của người dùng và gửi đi
  - Sau đó model tại biên sẽ sử lý image + text  để cho ra điểm số mức độ nguy cấp
  - Mặc định gửi đi tag result sau khi đã có kết quả từ model, đưa ảnh và image vào queue chờ xử lý
    - (Tính toán điểm số ở biên hay server?)
  - Kèm theo thông tin: Tên, Số điện thoại, GPS
  - Kiểm tra băng thông khi mạng đủ mạnh thì gửi đi image và đoạn text (trong trường hợp mạng mạnh thì việc gửi tag result và image + text sẽ gần như cùng lúc)
- Đội cứu hộ:
  - Xem bản độ báo cáo cứu hộ có phân cụm theo thời gian thực
  - Xem thông tin của từng cụm, từng trường hợp báo cáo
  - Nhận thông báo khi có sự kiện mới, nguy cấp,..
  - Xem bảng quản lý sự kiện: theo mức độ từng sự kiện hoặc mức độ của cụm
- Có bao nhiêu loại người dùng:
  - User chia làm 2 loại là Người bị nạn (Mobile App) và Đội cứu hộ (Dashboad)
  - Admin quản trị hệ thống
- Hệ thống:
  - Tính toán điểm số mức độ khẩn cấp: từ AI result + tham số ngữ cảnh (**thời gian, mật độ báo cáo lân cận,)**

</aside>

<aside>

# draft nội dung nghiên cứu:

- Tìm kiếm và xây dựng bộ dataset cho lũ lụt tại Việt Nam
- Nghiên cứu các model và phương pháp xử lý ngôn ngữ tự nhiên cụ thể cho Tiếng Việt với các trường hợp đặc biệt như: viết tắt, viết sai chính tả, thiếu ký tự,.v.v. Vì ngữ cảnh bài toán xảy ra trong trường hợp khẩn cấp
- Training hướng đến hiệu quả của model sao cho đảm bảo model đủ nhẹ cho thiết bị tại biên và độ chính xác cao
- Nghiên cứu tích hợp model vào ứng dụng di động
- Tìm hiểu các xử lý phân cụm các trường hợp cứu hộ: ví dụ bc1 bc4 bc1 gần nhau ⇒ cụm A,…; vì sao cần thiết?
- Tham số ngữ cảnh nên được tính dựa vào các yếu tố nào? và việc tính toán này nên được triển khai ở Thiết bị hay Server?

</aside>

<aside>

# Câu hỏi hỏi thầy:

- Hội đồng sẽ tập trung vào nội dung gì nếu không chú trọng vào độ hoàn thiện của ứng dụng?
- Cuốn báo cáo sẽ phải gồm những mục gì? Có giống với cuộc báo cáo luận văn hay không?
- Khi báo cáo có chú trọng nhiều vào logic nghiệp vụ của ứng dụng hay không?
  - Ví dụ như hỏi “Nếu một người dùng gửi nhiều lần thì sao?”  “Bảo mật đăng nhập, đăng ký,….”?
- Muốn viết bài báo khoa học thì phải bắt đầu như thế nào?
- Nếu sẽ phân cụm các sự kiện gần nhau thành một cụm thì có cần xem xét và tính toán mức độ nguy cấp của từng cụm hay không?
- Nếu mạng chập chờn, lúc mạnh lúc yếu thì xử lý như thế nào? ⇒ **luôn gửi trước AI results, đến khi mạng mạnh thì gửi Ảnh + Text**

</aside>

<aside>

# Scope:

- Giải quyết vấn đề ở phương diện kỹ thuật nhầm phục vụ cho nghiên cứu chứ không đi sâu vào logic nghiệp vụ khi triển khai thực tế cho các
- Phạm vi triển khai: ở mức thử nghiệm cho các nhóm nghiên cứu và sinh viên trong môi trường mô phỏng
- Thiên tai nhấm đến để training model là lũ lụt và hình ảnh sẽ cụ thể là ngoại cảnh, cảnh quan ở Việt Nam

</aside>

<aside>

# Out of Scope :

- Hệ thống chỉ được triển khai trong môi trường thử nghiệm, chưa sử dụng trong môi trường thực tế
- Hệ thống là một công cụ hỗ trợ đưa thông tin nhanh của sự kiện đến bên chịu trách nhiệm cứu hỗ, không chịu trách nhiệm với các giai đoạn sau của quá trình cứu hộ

</aside>

# Mobile App:

- Tích hợp 2 model phân tích ảnh và text
- Module 1: chụp ảnh (hoặc tải ảnh) → xử lý ảnh → nạp vào model → lấy kết quả
- Module 2: nhận input text về hoàn cảnh, ngữ cảnh → xử lý text → nạp vào model → kết quả mức độ
- Module 3: Tính điểm số mức độ khẩn cập dựa vào kết quả từ 2 model và công thức
- Module 4: Kiểm tra tốc độ  kết nối mạng để quyết định gửi bằng phương thức nào? (Mạnh/ Yếu) Lưu trữ ảnh và text cục bộ để gửi khi mạng mạnh trở lại
- Module 5: Quản lý đồng bộ, hàng đợi,…

# Backend:

- Module 1: Websocket Server để đồng bộ và cập nhật dữ liệu thời gian thực lên Dashboard
- Module 2: Rest API server for mobile app để nhận dữ liệu lấy từ ứng dụng
- Module 3 : Phân cụm không gian

# Frontend web:

- Module 1: bản đồ thời gian thực
- Module 2: quản lý sự kiện cứu hộ
- Các thông tin về cứu hộ

# **Model training:**

- List model
- Tại sao không giải quyết theo hướng 1 model duy nhất cho cả text và ảnh để đưa ra một kết quả duy nhất là lại chọn sử dụng 2 model tách biệt để rồi phải thêm một bước xử lý và tính lại score của mức độ nguy hiểm???
- Khi chọn một model cần trả lời các câu hỏi:
  - ý tưởng về cách hoạt động của model này là gì?
  - Tại sao chọn model này mà không phải các model khác? Ưu nhược điểm từng cái?
  - Tại sao phù hợp với bài toán của nghiên cứu đang giải quyết

# Dataset:

- Làm rõ định nghĩ của từng labels trong dataset: ví dụ ảnh "none" là như thế nào "medium" là như thế nào?
- 

# Docs:

- Đặc tả ứng dụng
  - Activity luồng xử lý các trường hợp (mạng Mạnh/Yếu)
- Cách team hoạt động, giao tiếp?
- Nơi lưu trữ docs
- Architecture diagram
- Functional Decomposition Diagram
- Thiết kế kiến trúc database (ERD)
- Sơ đồ use-case tổng thể
