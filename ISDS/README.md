# ISDS 2026 · Paper 6444

Mở **[ISDS2026_Paper_6444_Conference_Deck.pptx](ISDS2026_Paper_6444_Conference_Deck.pptx)** để chỉnh sửa và trình chiếu.
**[Bản PDF](ISDS2026_Paper_6444_Conference_Deck.pdf)** và **[ảnh tổng quan](checks/contact-sheet.png)** phục vụ xem nhanh.

- 26 slide tiếng Anh; Overview ở slide 2; hai slide tài liệu tham khảo ở 24–25; hỏi đáp ở slide 26.
- Đã chỉnh theo gợi ý ngày 11/11/2026: RQ1–RQ3 ở slide 5, trước pipeline; slide 7–9 giải thích đơn vị một run, vai trò hai bộ sinh và ví dụ Product/Additive. Slide 21 phân biệt đóng góp, điều đã chứng minh, kết quả mô phỏng và phần chưa được xác thực. Chi tiết ở [bản đối chiếu chỉnh sửa](research/revision-summary.md).
- Giữ riêng bối cảnh, khoảng trống, kết luận và hướng tiếp theo. [Script thuyết trình](speaker-notes.md) gồm toàn bộ 26 slide tiếng Anh trước, sau đó toàn bộ 26 slide tiếng Việt; chỉ có nội dung nói và số slide, không kèm trích dẫn hoặc thời gian gợi ý.
- Sử dụng trực tiếp slide master/layout và artwork của `CTU_PowerPoint_Template_English.pptx`; bố cục tham khảo deck Paper 8253.
- Đúng font của mẫu: **K2D** cho tiêu đề và **Readex Pro** cho nội dung. Font và giấy phép OFL nằm trong [fonts/](fonts/); cài các bản Regular/Bold khi máy chưa có font. Barlow là font phụ của mẫu. PDF đã nhúng font để xem ổn định.
- Đã xóa hẳn footnote và các dải ghi chú/tổng kết ở cuối slide; các box không có dải màu viền trái. Giữ chân trang thương hiệu và số trang của mẫu CTU. Notes trong PowerPoint chỉ có lời thuyết trình tiếng Anh rồi tiếng Việt. Hồ sơ kiểm chứng nằm riêng trong [content-audit.md](research/content-audit.md) và [slide-sources.json](research/slide-sources.json).
- Văn bản, sơ đồ và các khối bố cục chính có thể sửa trực tiếp trong PowerPoint; công thức, biểu đồ và GIF được nhúng thành ảnh.

## Hình và GIF

- Slide 03: ba cảnh ngập lụt vẽ bằng shape, phân biệt nhiều báo cáo cho một sự cố, hai sự cố gần nhau và cụm báo cáo giả. Nhà, người, báo cáo và liên kết đều có thể chỉnh sửa.
- Slide 06: pipeline có icon cho năm giai đoạn; nhánh thiếu vị trí/thời gian dẫn sang xem xét thủ công; dữ liệu chuẩn chỉ nối vào bộ đánh giá sau khi cố định đầu ra.
- Slide 10: sơ đồ Louvain tĩnh có đủ đồ thị ban đầu, chuyển nút và gộp thành siêu nút; cạnh khuyên biểu diễn trọng số nội bộ. Toàn bộ sơ đồ có thể chỉnh sửa và hiện đủ trong PDF. GIF Louvain cũ vẫn nằm trong thư mục assets để lưu lịch sử, không còn là hình trên slide 10.
- Slide 17: [graph_stress.gif](assets/science/graph_stress.gif), bảy điều kiện thử nghiệm riêng trên cùng một lượt test và khung cuối là heatmap tổng hợp 40 lượt. Đây không phải thí nghiệm cập nhật trực tuyến hay diễn biến lũ theo thời gian.
- ARI và số cạnh của 7 điều kiện × 2 phương pháp đều khớp checkpoint gốc khi tái hiện để vẽ. Phần bản đồ là khung nhìn chi tiết; chỉ số dùng toàn bộ lượt thử. Không chạy lại chiến dịch benchmark.
- Slide 17 đồng thời có [heatmap tĩnh mới](assets/science/rq1_stress_static.png), đọc trực tiếp CSV kết quả 40 run, và số nổi bật **ΔARI = −0,6108 khi sao chép 5×**. PDF hiển thị được kết quả chính mà không cần phát GIF.
- GIF được nhúng nguyên bản để phát trong **Slide Show** của PowerPoint; chưa kiểm tra phát bằng Microsoft PowerPoint trong môi trường này. PDF và ảnh tổng quan hiển thị khung đầu của GIF, cùng heatmap tĩnh bên cạnh.
- Các sơ đồ bổ sung (một run, hai bộ sinh, hai báo cáo xa nhau, bản sao/khai báo, so sánh phân hoạch với nhãn chuẩn, bảng mức bằng chứng) là shape và chữ có thể chỉnh sửa trong PowerPoint. Ví dụ số ở slide 9 được ghi rõ là minh họa, không phải kết quả thực nghiệm. Không sử dụng ảnh thiên tai hoặc sơ đồ từ các liên kết minh họa không rõ nguồn trong gợi ý.
- Biểu đồ đọc các CSV kết quả hiện có. [Manifest hình](assets/science/manifest.json) ghi số liệu, hash nguồn, phép đối chiếu và các giới hạn.

## Tái tạo

Chạy từ gốc repository với Python có các thư viện trong [requirements.txt](requirements.txt):

```bash
python3 ISDS/scripts/build_deck.py
python3 ISDS/scripts/render_deck.py --soffice /path/to/soffice
python3 ISDS/scripts/validate_deck.py
```

`build_deck.py` cập nhật bộ hiện tại tại chỗ, giữ trang bìa và bố cục Overview đã sửa thủ công; chạy lại giữ nguyên thứ tự và không cộng dồn hình hoặc Notes. Các slide được nhận diện bằng chỉ số gốc lưu trong XML. Không chạy lại benchmark hoặc replay đồ thị khi thực hiện ba lệnh trên. `build_science_assets.py` là công cụ lịch sử để dựng lại toàn bộ hình khoa học, có thực hiện replay một run; không cần chạy để áp dụng bản sửa này.

`research/revision-content.json` lưu thứ tự và cấu hình trình bày; [research/talk-track.json](research/talk-track.json) là nội dung thuyết trình song ngữ cho cả 26 slide. `research/write_notes.py` tạo lại [speaker-notes.md](speaker-notes.md) theo thứ tự toàn bộ tiếng Anh rồi toàn bộ tiếng Việt và tạo JSON Notes cho từng slide. Chạy `build_deck.py` để đồng bộ cả Notes nhúng trong PPTX. Không đưa nguồn, đường dẫn nội bộ hoặc thời gian gợi ý vào lời thuyết trình. `research/references.json` tiếp tục phục vụ hai slide tài liệu tham khảo.

Script xuất PDF dùng các font tĩnh đi kèm qua cấu hình Fontconfig tạm, không cần cài font toàn hệ thống. Microsoft PowerPoint vẫn cần các font tương ứng để chỉnh sửa ổn định. Mẫu CTU nằm tại `templateCTU/ctu-slides/assets/CTU_PowerPoint_Template_English.pptx`, khớp hash mẫu gốc. PPTX tham khảo Paper 8253 không có trong checkout hiện tại; bản PDF tham khảo vẫn có ở `checks/reference/` và hash PPTX lịch sử được giữ trong manifest.

## Phạm vi bằng chứng

Generator 3.0 bán tổng hợp ở lớp bối cảnh địa lý; Candidate 4.1 là bộ tổng hợp riêng. Giữ điều kiện của giới hạn cạnh và bất biến bản sao; không diễn giải ARI như phần trăm đúng, không đồng nhất tính ổn định với lợi ích cứu hộ. Suy luận chính RQ3 dùng 40 cặp seed sau khi gộp ba điều kiện nguồn lực.

Codex hỗ trợ chuyển nội dung, đối chiếu nguồn, tạo sơ đồ/GIF và định dạng bằng skill [academic-research-suite](../.agents/skills/academic-research-suite/SKILL.md). Đây là bản trình bày để tác giả duyệt; việc tạo/kiểm tra file không xác nhận hiệu quả thực địa hoặc sự phê duyệt của tác giả. Bài báo và các artifact nghiên cứu gốc không được sửa.
