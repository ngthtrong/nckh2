# Nhật ký tìm kiếm và sàng lọc

Ngày khảo sát: 29/10/2026. Mục tiêu là tìm bằng chứng/dữ liệu độc lập cho RQ1–RQ3, ưu tiên lũ và yêu cầu cứu hộ; không yêu cầu kết quả phải có lợi cho phương pháp hiện tại.

## Cách tìm thực tế

Đã chạy 10 batch, tổng cộng **40 truy vấn**, bằng công cụ tìm kiếm web. Chuỗi truy vấn nguyên văn nằm trong [search-log.json](search-log.json). Nguồn phát hiện gồm bài xuất bản, kho tác giả/trường, arXiv, TREC, QCRI, GitHub, Figshare và cơ quan thống kê. Crossref được truy vấn bổ sung để xác nhận năm/DOI bài PetaJakarta (bài năm 2019, DOI có `2018`).

Không tuyên bố đã truy vấn trực tiếp đầy đủ Google Scholar, Semantic Scholar hoặc OpenAlex, cũng không tuyên bố độ bao phủ của một systematic review. Không dùng kết quả ở mirror/Kaggle thay cho tài liệu nguồn khi nguồn gốc có thể xác minh.

| Batch | Mục đích | Đầu mối giữ lại để kiểm tra |
|---|---|---|
| Q01–Q04 | Bốn hướng tìm của kế hoạch | TREC-IS, Harvey, England water rescue, 112 calls |
| Q05–Q08 | Mở rộng báo cáo cứu hộ và dữ liệu cộng đồng | VictimFinder, Harvey urgent help, Khallouli, PetaJakarta |
| Q09–Q12 | Truy nguyên các corpus phổ biến | CrisisBench, CrisisMMD, CrisisNLP, CrisisLex |
| Q13–Q16 | Benchmark fact/timeline và phân biệt dữ liệu ảnh | CrisisFACTS, FloodNet, RescueNet |
| Q17–Q20 | Gold địa điểm/sự cố và dữ liệu điều phối | Harvey location descriptions, DisasterLocDesc, Shenzhen case study |
| Q21–Q24 | Xác nhận bài/dataset và năm công bố | HumAID, CrisisBench, DisasterLocDesc 2026, CrisisLexT26 |
| Q25–Q28 | Địa danh có liên kết tọa độ và nguồn ontology | IDRISI, các paper TREC-IS |
| Q29–Q32 | Kiểm tra nhãn urgency, khả dụng dữ liệu vận hành | CrisisTS, 112 calls, Shenzhen |
| Q33–Q36 | Khả dụng archive, hạn chế tiếp cận | PetaBencana API, nguồn IDRISI |
| Q37–Q40 | Xác nhận bản gốc và phiên bản xuất bản | Lifeline, CrisisMMD, PetaJakarta, Harvey 2023 |

Các batch trả kết quả gộp; không có số hit chính xác cho từng query. Không báo số kết quả loại trùng ở cấp toàn bộ công cụ tìm kiếm vì không có export đầy đủ. Con số **34** là số công trình có hàng trong registry sau lựa chọn, không phải tổng mọi hit đã xuất hiện.

## Quy tắc sàng lọc

1. Ghi một hàng cho mỗi công trình, hợp nhất preprint và bản xuất bản khi cùng nghiên cứu. Ví dụ Harvey arXiv 2021 và journal 2023 là P16, không đếm đôi.
2. Kiểm tra đúng đơn vị nhãn: disaster/event, humanitarian class, location mention, fact, rescue incident, hoặc dispatch outcome. Tên dataset không quyết định mức phù hợp.
3. Giữ các nguồn có vai trò bổ trợ nhưng ghi rõ vai trò. Loại FloodNet/RescueNet khỏi benchmark trực tiếp của ba RQ; không kết luận dữ liệu ảnh không có ích cho mô-đun ảnh của hệ thống.
4. Xác minh public download bằng phản hồi và nội dung tệp. Bài ghi “upon request” là conditional; code public không nâng thành data public.
5. Ghi lại cả dữ liệu thiếu, kết quả kiểm tra bất lợi và giới hạn nguồn. Không chọn bộ dựa trên hiệu quả Product hoặc điểm ưu tiên.

Mức đọc trong [papers.csv](papers.csv): `targeted_full_text_review` nghĩa là đã đọc phần liên quan đến dữ liệu/phương pháp/đánh giá/availability; không có nghĩa đã tái lập kết quả. Mức còn lại chỉ là sàng lọc tiêu đề/abstract hoặc mô tả từ nguồn chính. Một bài tổng quan P33 chỉ dùng tìm nguồn, không thay thế các paper/kho gốc làm bằng chứng về dữ liệu.

## Truy nguyên ngoài tìm kiếm

- Theo liên kết chính thức tới tệp HumAID/TREC, downloader và gold facts CrisisFACTS, data DOI của DisasterLocDesc, workbook England.
- Theo P26 và kho IDRISI tới các tệp train/dev English Harvey và P34. Root README của IDRISI có dòng cũ “LMD will be available soon”, nhưng thư mục LMD và tệp dữ liệu hiện tải được; kiểm tra tệp là bằng chứng khả dụng cụ thể.
- Kiểm tra HTTP range trên archive DisasterLocDesc: đọc một batch 200 hàng, không dùng metadata 7.149 tweet làm quy mô đã audit.
- Nguồn yêu cầu API key hoặc thông tin tổ chức chưa được mở quyền; không gửi thông tin cá nhân/tổ chức hoặc liên hệ tác giả trong khảo sát này.
