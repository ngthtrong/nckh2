# Chuẩn bị hỏi đáp: ISDS 2026, Paper 6444 (bản 15 phút)

Số liệu lấy từ `paper/main.tex`. Bài nói trình bày **một bộ dữ liệu tổng hợp duy nhất**. Khi được hỏi trực tiếp về mẫu dữ liệu, cần trả lời đúng như bài báo (xem câu A3).

## A. Dữ liệu

1. **Vì sao dùng dữ liệu tổng hợp mà không dùng báo cáo thật?**
   Cần biết chắc sự cố nào là thật, báo cáo nào trùng hay giả. Cũng cần chủ động tạo nhiễu (sao chép, giả mạo, chiến dịch phối hợp) để tìm điểm gãy. Hiện chưa có bộ báo cáo cứu hộ thật nào được gán nhãn sự cố độc lập. Không khẳng định giá trị thực địa.
2. **Bộ sinh đã được kiểm chứng với dữ liệu thật chưa? EMSR848 đóng vai trò gì?**
   Chưa. EMSR848, OSM và WorldPop chỉ cung cấp bối cảnh địa lý. Sự cố, báo cáo, nhãn và kết cục đều do mô phỏng tạo ra. Đây là phép thử trong cùng bộ sinh (within-generator), không phải kiểm tra chuyển miền (OOD).
3. **RQ1, RQ2, RQ3 có dùng đúng cùng một tập báo cáo không?** *(câu nhạy cảm, trả lời trung thực)*
   Cả ba dùng cùng quy trình sinh, cùng ranh giới thông tin và cùng cách chia 80 run (20/20/40). Bài báo ghi rõ hai cấu hình được sinh riêng. Phép thử phân cụm dùng cấu hình neo EMSR848 (26.288 báo cáo). Xếp hạng và điều phối dùng cấu hình có hình học tổng hợp (30.229 báo cáo). Kết quả không gộp chung và không được trình bày như một phép thử end-to-end trên cùng mẫu. Slide 6 đã ghi rõ bối cảnh EMSR848 chỉ áp dụng cho phép thử phân cụm. Backup slide 18 cũng có ghi thông tin này.
4. **Nhóm tác giả tự viết bộ sinh, vậy có nguy cơ "tự chấm cho mình" không?**
   Có ba biện pháp. Một: cấu hình được chọn trên run hiệu chỉnh, còn 40 run kiểm tra được giữ riêng. Hai: thuật toán chỉ đọc `algorithm_input.json`, đáp án chỉ nối vào sau khi dự đoán đã cố định. Ba: artifact công khai [12]. Bằng chứng thêm là kết quả **không** có lợi cho phương pháp đề xuất (Product không hơn Additive, điểm mới không hơn ngẫu nhiên).
5. **16 sự cố mỗi run, 40 run kiểm tra có đủ không?**
   Đơn vị suy luận là 40 run (seed) ghép cặp. Nhóm dùng Wilcoxon có hiệu chỉnh Holm và CI bootstrap 95%. Cỡ mẫu chỉ đủ để phát hiện khác biệt vừa và lớn. Khác biệt cỡ 0,01 ARI không xác lập được, và bài báo nói rõ điều đó.
6. **Lợi ích, hạn đáp ứng, tổn hại sinh ra thế nào? Có phụ thuộc công thức ưu tiên không?**
   Bộ sinh tạo các giá trị này riêng và lưu ở phía bộ đánh giá. Công thức ưu tiên không đọc chúng, nên NDCG@5 đo mức phù hợp với một mục tiêu độc lập.

## B. Phương pháp

7. **Trực giác của Product là gì?** Khoảng cách đóng vai trò "cổng": hai báo cáo xa nhau có trọng số cạnh tiến về 0 dù thời gian và bằng chứng giống nhau. Ý tưởng gần với bilateral filter [2]. Additive vẫn giữ một nửa trọng số ở mọi khoảng cách.
8. **Tính chất của Product có phải là đảm bảo phân cụm đúng không?** Không. Đó chỉ là giới hạn trên từng cạnh trong điều kiện đã nêu. Ở mức 5× bản sao, ARI vẫn sụp còn khoảng 0,30, và vẫn có 16,49% điểm đến giả.
9. **Vì sao dùng Louvain mà không dùng Leiden?** Đã thử: Product Leiden đạt ARI 0,9165, Product Louvain đạt 0,9072, Holm p = 0,1120. Không có khác biệt có ý nghĩa.
10. **Các tham số σ = 700 m, α, β, γ, ngưỡng, top-k chọn thế nào?** Chọn trên 20 run hiệu chỉnh (run 21–40), riêng cho từng phương pháp, rồi khóa lại trước khi chạy tập kiểm tra. Phép thử stress không chỉnh lại tham số.
11. **Q_i (độ tin cậy) tính ra sao? Có phải xác suất không?** Q_i là một hàm sigmoid của các tín hiệu quan sát được (có ảnh hay không, mức xác nhận chéo). Đây là heuristic, không phải xác suất đã hiệu chuẩn.
12. **Vì sao chọn tanh, μ = 2, s = 10 và trọng số 0,34/0,33/0,33?** Các giá trị này là lựa chọn thiết kế cố định, không do dữ liệu suy ra. Phân tích độ nhạy thay từng hằng số một trên 21 cấu hình: biên độ NDCG@5 trung bình luôn dưới 0,01 (lớn nhất 0,00546).
13. **Nhóm bằng chứng (evidence family) xác định thế nào?** Các báo cáo trùng chính xác hoặc gần trùng trong một cụm được nối bằng thành phần liên thông. Mỗi nhóm chỉ đóng góp giá trị lớn nhất có trọng số Q_i, nên thêm bản sao chính xác không làm đổi điểm.
14. **Độ phức tạp tính toán và khả năng mở rộng?** Đồ thị dựng từ ma trận toàn bộ cặp, tức O(n²) theo số báo cáo mỗi run (288–424 báo cáo). Muốn mở rộng thì cần chỉ mục không gian hoặc cửa sổ thời gian. Bài báo không đo phần này.

## C. Kết quả

15. **Tiêu đề nói Product-gated nhưng Additive đạt ARI cao nhất. Vậy đóng góp là gì?** Đóng góp là *phép kiểm tra*, không phải một thuật toán thắng cuộc. Kết quả cho thấy tính chất cục bộ của Product chưa chuyển thành lợi ích phân cụm.
16. **CI bootstrap không chứa 0 mà Wilcoxon lại không có ý nghĩa, có mâu thuẫn không?** Hai thủ tục khác nhau. CI [−0,0226; −0,0024] là CI chưa hiệu chỉnh. Wilcoxon có raw p = 0,0987, sau Holm p = 0,2560. Nhóm chọn cách thận trọng là không tuyên bố ưu thế.
17. **Vì sao 5× bản sao làm ARI sụp mà 2× lại tăng nhẹ?** Bản sao chính xác tạo thành các cụm rất đặc. Bước làm thưa (ngưỡng phân vị + top-k) bị chiếm bởi cạnh nối giữa các bản sao, nên cấu trúc cộng đồng bị bóp méo. Hướng khắc phục là khử trùng lặp trước khi dựng đồ thị (ví dụ gộp theo fingerprint).
18. **Thứ tự ngẫu nhiên có NDCG@5 cao hơn điểm mới. Vậy dùng công thức để làm gì?** Chênh lệch giữa các ước lượng điểm không có ý nghĩa thống kê. Điều này cho thấy các trường báo cáo mô phỏng mang ít thông tin về lợi ích thật. Kết luận là chưa xác lập lợi ích của điểm mới, không phải ngẫu nhiên tốt hơn.
19. **Nearest-first tốt hơn hẳn về tổn hại và trễ hạn. Có phải ưu tiên theo nhu cầu là vô ích?** Trong mô phỏng này, thời gian di chuyển chi phối kết cục. Điểm ưu tiên không tính đến di chuyển và phục vụ. Hướng tiếp theo là tối ưu đồng thời ưu tiên và lộ trình. Kết quả không chứng minh nearest-first phù hợp ngoài thực tế.
20. **Tổn hại (harm) có đơn vị gì?** Đơn vị mô hình, là chi phí trong mô phỏng. Không phải thương vong đo được.
21. **Lỗi gom nhóm có thực sự ảnh hưởng đến điều phối không?** Có, và đây là ô thứ ba của slide 13. Với điểm mới, phân hoạch Product cho tổn hại cao hơn Additive cùng mật độ +18,34 (Holm p = 0,000168). So với phân hoạch chuẩn (oracle), tổn hại cao hơn +36,69 (Holm p = 0,0020) và trễ hạn cao hơn 5,21 điểm phần trăm (Holm p = 0,0030). Tách nhầm, gộp nhầm và cụm toàn báo cáo giả đều để lại hậu quả đo được trong lịch.
22. **Chống chiến dịch báo cáo giả phối hợp thế nào?** Điểm có chặn trên không giải quyết được vấn đề này: độ lệch 0,1688 so với 0,0309. Cần kiểm tra nguồn và kiểm tra chéo đa kênh, điều mà Q_i hiện chưa mô hình hóa. Đây là hướng tương lai.
23. **Làm sao phát hiện cụm chỉ gồm báo cáo giả (16,49%)?** Phương pháp hiện tại chưa làm được. Có thể dùng tín hiệu nguồn độc lập, ảnh, lịch sử thiết bị hoặc xác minh qua hotline. Phần này chưa được đánh giá.

## D. Ứng dụng và đạo đức

24. **Bao giờ dùng được ngoài thực tế? Kế hoạch kiểm chứng là gì?** Cần báo cáo thật được gán nhãn độc lập, đánh giá cùng chuyên gia điều phối, và thử xếp hạng đồng thời với ràng buộc di chuyển. Trước khi có những bước này, nhóm không khẳng định lợi ích cứu hộ thực tế.
25. **Có xử lý văn bản tiếng Việt hay ảnh không?** Bài báo giả định các trường F/E/N/V đã được trích xuất. Phần trích xuất (NLP, ảnh) nằm ngoài phạm vi và là một nguồn lỗi cần đánh giá sau.
26. **Hình minh họa ở slide 3, 4, 6 lấy từ đâu?** Đó là hình minh họa khái niệm do AI tạo. Chúng không phải dữ liệu, ảnh thực địa hay kết quả. Thông tin này có ghi trong Notes và alt text.
27. **Có tái lập được không?** Có. Artifact công khai (v1.0.1) có manifest SHA-256 và mã đánh giá theo nguyên tắc fail-closed [12].

## E. Tính mới

28. **Điểm mới so với các nghiên cứu trước là gì?** Các nghiên cứu trước thường đánh giá riêng lẻ: trích xuất thông tin, phân cụm, hoặc điều phối. Bài này kiểm tra mối nối giữa các bước trong cùng một giao thức có đáp án ẩn, cho thấy bảo đảm ở bước trước không tự chuyển thành lợi ích ở bước sau.
29. **Kết quả "âm tính" có đáng công bố không?** Có. Kết quả này ngăn việc suy diễn quá mức từ tính chất toán học sang hiệu quả cứu hộ, và cung cấp bộ thử để các phương pháp sau phải vượt qua.
