## 14. Kết luận và kiến nghị của Hội đồng

### Đánh giá về tổng quan tình hình nghiên cứu, lý do chọn đề tài, mục tiêu đề tài, phương pháp nghiên cứu, nội dung khoa học

- **Tổng quan và lý do chọn đề tài:** Lý do chọn đề tài có tính thực tiễn cao, xuất phát từ bối cảnh cứu hộ bão lũ khi mạng viễn thông chập chờn, gián đoạn. Đã trình bày khá tốt tổng quan về Edge AI và phân cụm đồ thị. Tuy nhiên, phần tổng quan tài liệu còn mỏng (chỉ 20 tài liệu), chưa sát nhất với bài toán và chưa dẫn các công trình ước lượng ngập lụt hay hệ thống cứu hộ hiện có (như AlleyFloodNet, EmergencyNet) để làm rõ điểm mới.
- **Mục tiêu đề tài:** Trình bày rõ ràng 3 mục tiêu cụ thể và 3 câu hỏi nghiên cứu (RQ1-RQ3). Tuy nhiên, có sự sai lệch giữa thuyết minh và thực hiện: mục tiêu nêu "phân tích từ văn bản và hình ảnh" nhưng thực tế không xử lý văn bản tiếng Việt (bỏ mô hình DistilBERT). Việc dùng từ "đa phương thức" chưa thật sự phù hợp vì nhánh ảnh và biểu mẫu được đánh giá độc lập. Một số mục tiêu quá rộng không đo lường được ("giảm thiểu thiệt hại về người và tài sản") và chưa có chỉ tiêu định lượng cụ thể.
- **Phương pháp nghiên cứu:** Phương pháp tiếp cận bài bản, kết hợp tốt giữa lý thuyết (Edge AI, phân cụm, xếp hạng, truyền thích ứng) và thực nghiệm định lượng trên thiết bị di động thật (4 điện thoại). Cách chia dữ liệu, thiết lập mô hình và kiểm định thống kê (Wilcoxon) hợp lý.
- **Nội dung khoa học:** Đề tài có khối lượng nghiên cứu lớn, xây dựng thành công nguyên mẫu ứng dụng Flutter chạy suy luận AI trên thiết bị, máy chủ FastAPI và Web GIS. Việc triển khai mô hình MobileNetV3 trên thiết bị di động với ExecuTorch cho tốc độ nhanh hơn ONNX (1,89 - 3,27 lần) là một điểm sáng. Tuy nhiên, chất lượng nhận diện ảnh ngập còn thấp (Accuracy ~75.78%), giảm đáng kể khi lượng tử hóa và có lỗi sai lệch 2 mức. Bộ dữ liệu ảnh 1702 tấm thu thập từ web chưa có ảnh chụp thực địa, chưa kiểm định độ đồng thuận của người gán nhãn. Kết quả của các thuật toán phân cụm (RQ1) và xếp hạng (RQ2, RQ3) chưa mang lại sự cải thiện rõ rệt so với đối chứng đơn giản.

### Đóng góp về mặt kinh tế - xã hội, giáo dục và đào tạo, an ninh, quốc phòng

- Đề tài mang lại giá trị cao trong giáo dục và nghiên cứu, là nền tảng thực hành tốt về Edge AI, tối ưu hóa mô hình và hệ thống thông tin cứu hộ.
- Sản phẩm có tiềm năng ứng dụng thực tế để hỗ trợ công tác cứu hộ, phòng chống thiên tai bão lũ tại ĐBSCL và miền Trung.
- Đề tài đã có 01 bài báo được chấp nhận tại hội nghị ISDS 2026 (Springer CCIS) và có cung cấp mã nguồn, dữ liệu mở.
- Về an ninh, quốc phòng, đề tài liên quan gián tiếp qua công tác phòng chống thiên tai và cứu hộ cứu nạn.

### Các nội dung cần sửa chữa, bổ sung, hoàn chỉnh

- **Về hình thức báo cáo:** Báo cáo khá tốt nhưng quá dài (hơn 120 trang), sử dụng nhiều tên nội bộ, lặp câu cảnh báo gây khó đọc. Cần chỉnh sửa: chèn ảnh thẻ, ghi ngày tháng, điền nhận xét của người hướng dẫn, đánh số lại trang minh chứng bài báo, rút gọn Chương 2 và Phần Kết luận. Khắc phục các lỗi về định dạng tài liệu tham khảo (ngoặc kép, thống nhất font/khoảng trắng) và ký hiệu (thống nhất K và k).
- **Về thuật toán:** Bổ sung/hợp nhất nhánh xử lý văn bản tiếng Việt để đúng với phạm vi "đa phương thức" và thống nhất lại Bảng B.6. Cần làm chặt chẽ việc đánh giá mô hình ảnh: sử dụng tập validation/test độc lập, kiểm định McNemar cho quá trình cắt tỉa, tìm nguyên nhân giảm chất lượng khi lượng tử hóa (PTQ/QAT) và thử tỷ lệ cắt tỉa cao hơn. Khử trùng lặp bản sao trong pipeline phân cụm đồ thị.
- **Về dữ liệu và kiểm thử:** Đánh giá lại thuật toán phân cụm và xếp hạng trên dữ liệu thật hoặc kịch bản thực tế hơn (thay vì dữ liệu tổng hợp). Sửa lỗi ứng dụng văng/thoát khi gửi lúc mất mạng, kiểm thử tính năng SMS thật và mạng yếu trên điện thoại thay vì chỉ giả lập trên máy tính.

### Kiến nghị về khả năng ứng dụng kết quả nghiên cứu của đề tài

- Phù hợp dùng làm nền tảng nghiên cứu và đào tạo về Edge AI và tối ưu mô hình tại Trường CNTT&TT.
- Hiện tại chưa nên triển khai vận hành thực tế; chỉ nên thí điểm sau khi đã khắc phục lỗi phần mềm, kiểm thử thiết bị/mạng thật và cần có đơn vị cứu hộ chuyên trách tham gia quyết định. Cần lưu ý việc sai số của AI có thể làm lệch thứ tự ưu tiên cứu hộ, và dữ liệu người yếu thế cần được bảo mật.

### Kiến nghị về khả năng phát triển của đề tài

- Mở rộng bộ ảnh bằng ảnh chụp thực địa từ điện thoại, có nguồn và giấy phép rõ ràng.
- Bổ sung nhánh phân tích tin nhắn tiếng Việt và thiết kế lịch biểu điều phối có chi phí di chuyển.
- Thực hiện thử nghiệm thực địa với mạng viễn thông thật và mạng SMS thật.

## 15. Xếp loại

**XUẤT SẮC**
