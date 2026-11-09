# ISDS 2026 · Paper 6444

Mở **[ISDS2026_Paper_6444_Conference_Deck.pptx](ISDS2026_Paper_6444_Conference_Deck.pptx)** để chỉnh sửa và trình chiếu.
**[Bản PDF](ISDS2026_Paper_6444_Conference_Deck.pdf)** và **[ảnh tổng quan](checks/contact-sheet.png)** phục vụ xem nhanh.

- 26 slide tiếng Anh; Overview ở slide 2; hai slide tài liệu tham khảo ở 24–25; hỏi đáp ở slide 26.
- Giữ riêng bối cảnh, khoảng trống, kết luận và hướng tiếp theo. Thời lượng phân bổ trong ghi chú khoảng 20 phút; chưa phải thời gian tập dượt đã đo.
- Sử dụng trực tiếp slide master/layout và artwork của `CTU_PowerPoint_Template_English.pptx`; bố cục tham khảo deck Paper 8253.
- Đúng font của mẫu: **K2D** cho tiêu đề và **Readex Pro** cho nội dung. Font và giấy phép OFL nằm trong [fonts/](fonts/); cài các bản Regular/Bold khi máy chưa có font. Barlow là font phụ của mẫu. PDF đã nhúng font để xem ổn định.
- Đã xóa hẳn footnote và các dải ghi chú/tổng kết ở cuối slide; các box không có dải màu viền trái. Giữ chân trang thương hiệu và số trang của mẫu CTU. Nguồn chi tiết nằm trong Notes của PowerPoint, [ghi chú thuyết trình](speaker-notes.md) và [hồ sơ nguồn](research/content-audit.md).
- Văn bản, sơ đồ và các khối bố cục chính có thể sửa trực tiếp trong PowerPoint; công thức, biểu đồ và GIF được nhúng thành ảnh.

## Hình và GIF

- Slide 9: [louvain_schematic.gif](assets/science/louvain_schematic.gif), minh họa khái niệm Louvain; không phải dữ liệu thực nghiệm.
- Slide 17: [graph_stress.gif](assets/science/graph_stress.gif), bảy điều kiện thử nghiệm riêng trên cùng một lượt test và khung cuối là heatmap tổng hợp 40 lượt. Đây không phải thí nghiệm cập nhật trực tuyến hay diễn biến lũ theo thời gian.
- ARI và số cạnh của 7 điều kiện × 2 phương pháp đều khớp checkpoint gốc khi tái hiện để vẽ. Phần bản đồ là khung nhìn chi tiết; chỉ số dùng toàn bộ lượt thử. Không chạy lại chiến dịch benchmark.
- GIF chạy trong chế độ **Slide Show** của PowerPoint. PDF và ảnh tổng quan hiển thị khung tĩnh; poster tổng hợp bổ sung ở [graph_stress_summary.png](assets/science/graph_stress_summary.png).
- Biểu đồ đọc các CSV kết quả hiện có. [Manifest hình](assets/science/manifest.json) ghi số liệu, hash nguồn, phép đối chiếu và các giới hạn.

## Tái tạo

Chạy từ gốc repository với Python có các thư viện trong [requirements.txt](requirements.txt):

```bash
python3 ISDS/scripts/build_science_assets.py
python3 ISDS/scripts/build_deck.py
python3 ISDS/scripts/render_deck.py --soffice /path/to/soffice
python3 ISDS/scripts/validate_deck.py
```

`research/speaker-notes.json` là nguồn ghi chú được nhúng vào PPTX; `research/references.json` là nguồn hai slide tài liệu tham khảo. Phải cài font trước khi xuất lại bằng LibreOffice/PowerPoint.

## Phạm vi bằng chứng

Generator 3.0 bán tổng hợp ở lớp bối cảnh địa lý; Candidate 4.1 là bộ tổng hợp riêng. Giữ điều kiện của giới hạn cạnh và bất biến bản sao; không diễn giải ARI như phần trăm đúng, không đồng nhất tính ổn định với lợi ích cứu hộ. Suy luận chính RQ3 dùng 40 cặp seed sau khi gộp ba điều kiện nguồn lực.

Codex hỗ trợ chuyển nội dung, đối chiếu nguồn, tạo sơ đồ/GIF và định dạng bằng skill [academic-research-suite](../.agents/skills/academic-research-suite/SKILL.md). Đây là bản trình bày để tác giả duyệt; việc tạo/kiểm tra file không xác nhận hiệu quả thực địa hoặc sự phê duyệt của tác giả. Bài báo và các artifact nghiên cứu gốc không được sửa.
