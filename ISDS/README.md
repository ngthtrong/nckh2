# ISDS 2026 · Paper 6444

Mở **[PowerPoint chính thức](ISDS2026_Paper_6444_Conference_Deck.pptx)** để chỉnh sửa hoặc trình chiếu. Có [bản PDF](ISDS2026_Paper_6444_Conference_Deck.pdf), [ảnh tổng quan](checks/contact-sheet.png) và [script song ngữ](speaker-notes.md).

Bộ hiện tại gồm **21 slide chính và 1 slide backup**, tổng cộng 22 slide. Louvain nằm sau trang hỏi đáp, được đánh dấu **Hidden Slide** để không chạy trong bài nói chính. PDF vẫn xuất cả trang backup để tra cứu.

| Nội dung trong bộ 26 slide trước | Vị trí hiện tại |
|---|---|
| Slide 7 + 8: hai bộ dữ liệu | Slide 7: giữ bố cục so sánh, thêm Copernicus EMSR848, OpenStreetMap và WorldPop 2025 |
| Slide 13 + 14 + 15: độ đo | Slide 11: ARI, NDCG@5 và Simulated harm trên một trang |
| Slide 22 + 23: Conclusion / Future work | Slide 18: kết luận bên trái, bốn hướng tiếp theo trong cột nhỏ bên phải |
| Slide 10: Louvain | Slide 22: backup, ẩn khi trình chiếu |

Hai slide tài liệu tham khảo ở 19–20; trang cảm ơn/hỏi đáp ở 21. Số trang, Notes, [slide-index.json](slide-index.json) và script đã đồng bộ. Script gồm toàn bộ tiếng Anh trước rồi toàn bộ tiếng Việt, với phần backup đánh dấu riêng; không kèm trích dẫn hoặc thời gian gợi ý.

## Bố cục và hình

- Giữ master CTU, font K2D cho tiêu đề và Readex Pro cho nội dung. Font tĩnh và giấy phép nằm trong [fonts/](fonts/).
- Giữ các chỉnh sửa thủ công hiện có ở bìa, mục lục và hình stress. Những trang không gộp giữ nguyên chữ, hình và vị trí các thành phần, ngoài việc đổi số trang và nhãn backup. Giảm cỡ năm tiêu đề mục lục và nhãn ΔARI để tránh xuống dòng chồng chữ trong khung đã chỉnh thủ công.
- Slide 3 có ba cảnh báo cáo ngập lụt; slide 6 là pipeline quan sát/đánh giá riêng. Các sơ đồ và khối chữ có thể chỉnh sửa trực tiếp trong PowerPoint.
- Slide 13 có GIF stress một run và heatmap tĩnh 40 run, với ΔARI = −0,6108 khi sao chép 5×. Bản PDF hiển thị đủ kết quả chính dù GIF chỉ hiện khung đầu.
- GIF stress giữ nguyên byte gốc. Chưa kiểm tra phát bằng Microsoft PowerPoint trong môi trường này. Chuỗi điều kiện cố định không phải diễn biến lũ trực tuyến.
- Slide backup 22 dùng sơ đồ Louvain tĩnh gồm chuyển nút và gộp thành siêu nút. GIF Louvain cũ chỉ là asset lưu lịch sử.
- Không thêm footnote nguồn hoặc dải tổng kết cuối trang. Giữ chân trang thương hiệu CTU. Hồ sơ nguồn nằm riêng trong [content-audit.md](research/content-audit.md) và [slide-sources.json](research/slide-sources.json).

## Tái tạo và kiểm tra

Chạy từ gốc repository bằng Python có các thư viện trong [requirements.txt](requirements.txt):

```bash
python3 ISDS/scripts/build_deck.py
python3 ISDS/scripts/render_deck.py --soffice /path/to/soffice
python3 ISDS/scripts/validate_deck.py
```

`build_deck.py` gọi `compact_deck.py` để cập nhật PPTX đang có trong repository. Chạy lại không nhân đôi trang hoặc dòng neo địa lý. Cần giữ file PPTX chính thức làm đầu vào; script không dựng lại các chỉnh sửa thủ công từ một mẫu trống. Công cụ dựng bộ đầy đủ trước đây được giữ làm lịch sử.

`research/revision-content.json` lưu thứ tự và các nhóm gộp. [research/talk-track.json](research/talk-track.json) là nội dung song ngữ; `research/write_notes.py` xuất script và JSON Notes theo chỉ số slide hiện tại. Notes nhúng trong PowerPoint có tiếng Anh rồi tiếng Việt cho từng trang. `research/references.json` phục vụ hai slide tài liệu tham khảo.

Script xuất PDF dùng các font tĩnh đi kèm qua Fontconfig tạm, bao gồm slide ẩn khi xuất. Ảnh kiểm tra dư của bộ cũ được dọn để tránh nhầm số trang. Kết quả kiểm tra ở [validation.json](checks/validation.json), [layout-review.json](checks/layout-review.json) và [compaction-preservation.json](checks/compaction-preservation.json).

Không sửa bài báo, dữ liệu hoặc kết quả thực nghiệm; không fit lại mô hình hay replay benchmark. Generator 3.0 vẫn là bộ bán tổng hợp, Candidate 4.1 là bộ tổng hợp riêng. Giữ các điều kiện của bảo đảm toán học và tách kết quả mô phỏng khỏi hiệu quả thực địa.
