BỘ GIÁO DỤC VÀ ĐÀO TẠO	**CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM**

## **ĐẠI HỌC CẦN THƠ	Độc lập – Tự do – Hạnh phúc**

**PHIẾU GIẢI TRÌNH CHỈNH SỬA**
**THEO GÓP Ý CỦA HỘI ĐỒNG NGHIỆM THU**
**ĐỀ TÀI NGHIÊN CỨU KHOA HỌC CỦA SINH VIÊN**

1\. Mã số đề tài: THS2026-68

2\. Tên đề tài: Xây dựng hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI

3\. Sinh viên chủ nhiệm đề tài: Lê Thị Ngọc Ảnh

4\. Các nội dung được góp ý và giải trình:

| TT | Nội dung được hội đồng góp ý | Giải trình của chủ nhiệm đề tài |
| :--: | --- | --- |
| 1 | Bổ sung nghiên cứu liên quan về nhận diện ngập và các hệ thống ứng phó khẩn cấp. | Mục 1.2 và Bảng 1.1 đối chiếu nghiên cứu ảnh vệ tinh, ảnh mặt đất và ảnh–văn bản. Phần này bổ sung phương pháp của Quan và cộng sự, AlleyFloodNet, EmergencyNet, cùng vai trò cảnh báo của Google Flood Hub và lập bản đồ ứng phó của Copernicus EMS. Xem PDF 22–24. |
| 2 | Làm rõ nhánh xử lý văn bản tiếng Việt, phân tích đa phương thức và phạm vi thực hiện so với thuyết minh. | Mục 3.4–3.5 mô tả xử lý văn bản và kết hợp ảnh–văn bản. Mục 4.2.16–4.2.17 trình bày hai thử nghiệm ngoại tuyến, so sánh mô hình chỉ ảnh, chỉ văn bản và kết hợp cả hai trên cùng tập kiểm thử của từng nhiệm vụ. Mục 3.8.1 trình bày phạm vi thực hiện trong thân báo cáo, với bảng đối chiếu tại B.2. Xem PDF 55–57, 69, 94–98 và 113. |
| 3 | Làm rõ nguồn, cách gán nhãn, đặc điểm và phân chia bộ ảnh. | Mục 3.2 trình bày 1.702 ảnh. Các ảnh đô thị được chọn từ AlleyFloodNet và FloodNet, bổ sung ảnh tự chụp và ảnh báo chí Việt Nam dùng nội bộ. Hai người gán nhãn rồi đối chiếu để thống nhất nhãn cuối. Bảng 3.3–3.5 trình bày phân bố tập, tiêu chí gán nhãn, kích thước và dung lượng ảnh. Xem PDF 45–48. |
| 4 | Làm rõ kết quả lượng tử hóa, cắt tỉa và lựa chọn mô hình cho nguyên mẫu. | Mục 3.3.5 và 4.2.5–4.2.7 trình bày PTQ, QAT, so sánh cắt tỉa bằng kiểm định McNemar và thử mức 5%, 10%, 20%. Báo cáo giải thích lựa chọn phiên bản mô hình cho nguyên mẫu dựa trên kết quả đã đo. Xem PDF 52–54 và 82–86. |
| 5 | Trình bày phạm vi thực nghiệm nhận diện trên điện thoại và đánh giá ảnh suy giảm. | Mục 4.1 và 4.2.4 trình bày 32 cấu hình nhận diện trên bốn mẫu điện thoại. Mục 4.2.8 trình bày riêng các biến đổi nhân tạo trên ảnh kiểm thử bằng ONNX trên CPU. Xem PDF 71–73 và 80–87. |
| 6 | Giải thích cách tính điểm từ các dấu hiệu trên biểu mẫu và cơ chế xếp hạng. | Mục 3.6 trình bày hồi quy logistic học từ 32 tổ hợp dấu hiệu với nhãn tạo theo quy tắc OR, cách xây dựng đồ thị và điểm ưu tiên. Bảng 3.10 trình bày các chỉ tiêu theo từng thành phần và điều kiện đo. Xem PDF 57–65. |
| 7 | Diễn giải kết quả RQ1–RQ3 so với các phương pháp đối chứng. | Mục 4.2.10–4.2.15 và Kết luận trình bày kết quả trên dữ liệu mô phỏng. RQ1 ghi ARI 0.9072 của Product và 0.9191 của Additive. RQ2 ghi NDCG@5 0.6669 của phương án đề xuất và 0.6763 của đối chứng ngẫu nhiên. RQ3 trình bày kết quả tổn thất và trễ hạn khi so với chiến lược gần nhất trước. Xem PDF 87–94 và 103. |
| 8 | Làm rõ việc lưu, gửi lại và đồng bộ khi gián đoạn kết nối, cùng kết quả kiểm thử phần mềm. | Mục 4.3.1 trình bày các lượt kiểm thử Android. Mục 4.3.2 ghi kết quả 6 ca hồi quy lỗi gửi và đồng bộ, 284 ca Flutter đạt, 78 ca máy chủ đạt và hai kịch bản tích hợp Linux–máy chủ. Mục 4.3.4 trình bày phép đo truyền tải qua proxy mạng yếu. Xem PDF 99–102. |
| 9 | Cập nhật thông tin công bố khoa học. | Bổ sung ngày công bố trực tuyến 13/11/2026, tập CCIS 3253, trang 326–340 và [DOI 10.1007/978-981-92-7408-6_22](https://link.springer.com/chapter/10.1007/978-981-92-7408-6_22) trong biểu mẫu và bản tóm tắt Việt–Anh. Xem PDF 14, 16, 145 và 147. |
| 10 | Trình bày hướng nghiên cứu và hoàn thiện hệ thống. | Phần Hướng nghiên cứu tiếp theo đề xuất đánh giá phân cụm, xếp hạng và điều phối trên báo cáo cứu hộ thực tế, kiểm thử SMS đầu cuối và đo truyền tải trên mạng di động thật. Phần này cũng nêu định vị đa nguồn, tiếp nhận thông tin cầu cứu bằng âm thanh và phương án báo hộ. Xem PDF 103. |
| 11 | Rà soát biểu mẫu, bảng, hình, tài liệu tham khảo và minh chứng. | Bản PDF hoàn thiện còn 147 trang. Danh mục từ viết tắt gọn trong một trang, mục lục có thêm mục Nhận xét của người hướng dẫn và biểu mẫu chủ nhiệm có ảnh thẻ. Bảng được đặt giữa các đoạn và giữ tiêu đề lặp khi sang trang. Thuyết minh đặt trước Minh chứng sản phẩm, tiêu đề minh chứng nằm cùng trang ứng dụng di động và các hình minh chứng được đánh số liên tục. Xem PDF 12, 15, 17, 64–65, 104–107 và 127–141. |

*Cần Thơ, ngày … tháng … năm 2026*

**Thư ký Hội đồng  Chủ tịch Hội đồng  Cán bộ hướng dẫn  Chủ nhiệm đề tài**

## GHI CHÚ ĐÃ CHỈNH SỬA CHỖ NÀO

Các số dưới đây là số trang PDF. Bản gốc là [report-origin.pdf](report-origin.pdf) gồm 167 trang. Bản cuối là [main.pdf](../report/main.pdf) gồm 147 trang.

| Vị trí ở bản gốc | Vị trí ở bản cuối | Thay đổi |
| --- | --- | --- |
| PDF 13–14, danh mục từ viết tắt | PDF 12 | Thu hẹp cột từ viết tắt, nới cột diễn giải và gộp danh mục vào một trang. |
| PDF 15–20, thông tin kết quả và thông tin chủ nhiệm | PDF 13–17 | Thêm dòng chấm và liên kết mục lục cho phần nhận xét GVHD, chèn ảnh thẻ chủ nhiệm, thống nhất cỡ chữ nội dung tiếng Anh, bổ sung DOI và dải trang công bố. |
| PDF 21–25, Mở đầu | PDF 18–20 | Rút gọn mục tiêu và phạm vi, bỏ đoạn cuối Phạm vi nghiên cứu và tóm lược phạm vi đánh giá ảnh, văn bản và biểu mẫu. |
| PDF 26–30, Chương 1 | PDF 21–24 | Bổ sung đối chiếu với Quan và cộng sự, AlleyFloodNet, EmergencyNet, Google Flood Hub và Copernicus EMS. |
| PDF 31–74, Chương 2 | PDF 25–43 | Rút gọn phần thiết kế, chuyển chi tiết và ảnh giao diện xuống phụ lục. Các hình 2.7–2.10 và 2.15 dùng trang dọc. Ba hình use case 2.8–2.10 nằm trên hai trang PDF 33–34. |
| PDF 75–99, Chương 3 | PDF 44–69 | Làm rõ nguồn và cách gán nhãn ảnh, bổ sung thiết kế xử lý văn bản tiếng Việt và kết hợp ảnh–văn bản. Đưa phần phạm vi thực hiện so với thuyết minh vào Mục 3.8.1. |
| PDF 100–136, Chương 4 | PDF 70–102 | Bổ sung McNemar, các mức cắt tỉa 5/10/20%, thử biến đổi ảnh trên CPU, hai thử nghiệm ảnh–văn bản ngoại tuyến và kiểm thử hồi quy. Trình bày rõ kết quả RQ1–RQ3 và các đối chứng theo từng phép đo. |
| Các bảng trong Chương 3, Chương 4 và phụ lục | Ví dụ Bảng 3.10 ở PDF 65, danh mục bảng ở đầu báo cáo | Đặt các bảng một trang tại vị trí giữa các đoạn văn. Bảng dài tiếp tục qua trang cùng tiêu đề cột. Bảng 3.10 đi ngay sau đoạn dẫn về thước đo. |
| PDF 137–138, Kết luận và hướng phát triển | PDF 103 | Gộp phần kết luận và hướng phát triển vào một trang. Bổ sung định hướng đánh giá trên báo cáo cứu hộ thực tế và kiểm thử SMS đầu cuối, mạng di động thật. |
| PDF 139–141, Tài liệu tham khảo | PDF 104–107 | Chuẩn hóa ngoặc kép quanh tên bài và bổ sung tài liệu cho phần tổng quan. Thống nhất dấu chấm thập phân và ký hiệu top-K trong nội dung báo cáo. |
| PDF 142–157, phụ lục, và PDF 158–160, minh chứng | PDF 108–141 | Rút gọn phụ lục, chuyển bảng đối chiếu thuyết minh từ B.6 thành B.5. Ghép thuyết minh ở PDF 127–138, đặt tiêu đề Minh chứng sản phẩm cùng mục ứng dụng di động ở PDF 139. Hình minh chứng ở PDF 139–140 mang số 1–3. |
| PDF 161–167, bản tin và tóm tắt | PDF 142–147 | Đồng bộ văn bản Việt–Anh với các kết quả, phạm vi đánh giá và thông tin công bố trong báo cáo cuối. |
