# Chỉnh sửa slide ISDS Paper 6444 — 11/11/2026

Đã cập nhật trực tiếp bộ 26 slide tiếng Anh. Giữ phong cách CTU, font, các chỉnh sửa thủ công ở bìa và vị trí danh sách Overview, hai slide tài liệu tham khảo và các biểu đồ/GIF khoa học hiện có. Không sửa bài báo hoặc chạy lại thực nghiệm.

Theo yêu cầu bổ sung cùng ngày, slide 03 đã thay hình bằng ba cảnh báo cáo ngập lụt; slide 06 được vẽ lại với icon, nhánh xem xét thủ công và luồng đánh giá riêng; slide 10 thay GIF bằng sơ đồ Louvain tĩnh có thể chỉnh sửa, hiện đầy đủ trên PDF. Lời thuyết trình đã được viết lại cho cả 26 slide, toàn bộ tiếng Anh trước rồi toàn bộ tiếng Việt, không có trích dẫn, đường dẫn nguồn hoặc thời gian gợi ý. Notes trong PowerPoint cũng song ngữ và chỉ có nội dung nói.

| Gợi ý | Thực hiện trong bộ hiện tại |
|---|---|
| Đưa câu hỏi nghiên cứu lên trước kỹ thuật | RQ1–RQ3 chuyển từ slide 11 lên slide 5. Pipeline, hai bộ dữ liệu và phương pháp theo sau; phần kết quả vẫn ở 16–20. |
| Nêu thông điệp khoa học sớm | Slide 5 nêu rằng bảo đảm ở một giai đoạn chưa thiết lập lợi ích cho giai đoạn sau; slide 22 kết luận theo cùng thông điệp. |
| Giải thích một run | Slide 7: một kịch bản sinh gồm 16 sự cố giả lập và 288–370 báo cáo; sơ đồ tách dữ liệu quan sát dùng suy luận khỏi nhãn dùng đánh giá. |
| Giải thích hai bộ sinh | Slide 8 vẽ hai nhánh độc lập: Generator 3.0 cho RQ1; Candidate 4.1 cho RQ2/RQ3, với benefit/deadline/service/harm riêng. Không trình bày chúng như một chuỗi kiểm chứng trên cùng mẫu. |
| Minh họa lý do thử Product | Slide 9 giữ hai công thức và thêm cặp báo cáo xa nhau nhưng giống thời gian/ngữ cảnh. Các số minh họa được ghi rõ là giả định giảng giải. |
| Phân biệt bản sao với gian lận khai báo | Slide 11 tách bất biến bản sao khi giữ cố định families/inputs khỏi việc xác thực số người khai báo; clipping chỉ giới hạn ảnh hưởng. |
| Giải thích cách đánh giá run | Slide 13: báo cáo → phân cụm → phân hoạch dự đoán; evaluator so sánh với nhãn giữ riêng → ARI. Sáu điểm màu chỉ là sơ đồ. Giữ diễn giải ARI và Pairwise F1. |
| Thể hiện địa điểm giả | Slide 16 bổ sung 16,49% false destinations của Product. Đây là tỷ lệ địa điểm dự đoán giả trong RQ1, không phải tỷ lệ báo cáo giả hoặc kết quả điều phối thực tế. |
| PDF phải thấy kết quả stress | Slide 17 giữ GIF và bổ sung heatmap tĩnh 40 run cùng ΔARI = −0,6108 và CI 95% [−0,6318; −0,5881] khi sao chép 5×. |
| Đóng góp và giới hạn rõ ràng | Slide 21 có ba dòng đóng góp và ba cột mức bằng chứng: chứng minh toán học, quan sát trong mô phỏng, chưa thiết lập. Slide 23 thêm xác thực nguồn/số người vào hướng tiếp theo. |
| Đồng bộ phần hỗ trợ | Cập nhật Notes nhúng, JSON, Markdown, chỉ số slide, manifest, README và các kiểm tra cấu trúc/nguồn/PDF. |

Các slide gốc 1–4 giữ thứ tự; gốc 11 thành 5; gốc 5–10 thành 6–11; 12–26 giữ số. Các slide không cần sửa tiếp tục dùng nội dung và bố cục hiện tại.

## Hình ảnh và số liệu

- Sơ đồ mới dùng shape, đường nối và chữ gốc trong PowerPoint; có thể chỉnh sửa từng thành phần. Không sử dụng ảnh tìm trên mạng. Các icon báo cáo và chấm sự cố chỉ là minh họa khái niệm.
- Ví dụ slide 9: a = 1; α = β = γ = 1; G = 0,02; T = C = 0,90. Product = 0,036; Additive = 1,820. Không có ngưỡng giữ cạnh, tham số đã hiệu chỉnh hay kết luận ưu thế thực nghiệm từ ví dụ này.
- [rq1_stress_static.png](../assets/science/rq1_stress_static.png) vẽ lại `thucnghiem/results/rq1_results/aggregate/rq1_stress_paired_effects.csv`, metric `ari_original`, cột `mean_stress_minus_baseline`: năm phương pháp, sáu điều kiện, 40 run. Không fit mô hình hoặc gộp rerun. Hash, danh sách điều kiện và toàn bộ ma trận được ghi trong `build-manifest.json`.
- Bài báo `paper/main.tex:441–469` xác định hai bộ dữ liệu và số báo cáo/run; `548–591` ghi ARI và 16,49% địa điểm giả; `593–618` ghi stress 5× và CI; `250–325`, `380–421`, `756–800` xác định các điều kiện và giới hạn kết luận.
- Slide 10 dùng sơ đồ Louvain tĩnh mới; GIF cũ được lưu trong assets. Giữ GIF replay ở slide 17. Thứ tự khung là trình tự thuyết trình các điều kiện cố định, không phải diễn biến trực tuyến của lũ. Việc xuất PDF không kiểm tra phát GIF trong Microsoft PowerPoint.
- Nguồn lời nói song ngữ là `research/talk-track.json`; file đọc trực tiếp là [speaker-notes.md](../speaker-notes.md). Hồ sơ nguồn tách riêng ở `research/slide-sources.json`.

## Kiểm tra

Kết quả kiểm tra được lưu ở [validation.json](../checks/validation.json), [layout-review.json](../checks/layout-review.json), [font-verification.json](../checks/font-verification.json) và [contact-sheet.png](../checks/contact-sheet.png). Không ghi thời gian gợi ý trong script hoặc Notes. Việc kiểm tra artifact không xác nhận hiệu quả cứu hộ thực địa hoặc sự phê duyệt của tác giả.
