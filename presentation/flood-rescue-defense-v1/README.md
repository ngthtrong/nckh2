# Bản trình bày bảo vệ bài báo · v1

Mở **[index.html](index.html)** trực tiếp bằng trình duyệt. Bản HTML tự chứa font, biểu đồ và sơ đồ, dùng ngoại tuyến. **[slides.pdf](slides.pdf)** là bản xem/in tĩnh, gồm phần chính và dự phòng.

- 23 slide chính, 5 slide dự phòng; tiếng Việt, giữ tên thuật toán và metric tiếng Anh.
- Thời lượng giả định 20–25 phút, chưa gồm hỏi đáp; đây là bản đầu để duyệt nội dung và bố cục.
- Mạch trình bày: vấn đề → RQ/đóng góp → dữ liệu và giới hạn → thiết kế/phương pháp → kết quả RQ1–RQ3 → thảo luận/kiểm chứng tiếp theo.
- Slide 5–7 trình bày riêng: hai loại dữ liệu; lý do phương pháp luận cho lựa chọn; bất lợi và giới hạn kết luận. Slide 21 gắn giới hạn với hướng bổ sung bằng chứng, không trình bày các đề xuất như kết quả đã thực hiện.
- Slide 23 là điểm dừng để hỏi đáp; A1–A5 phục vụ phản biện.

## Điều khiển

← / →, Page Up / Down, Space: chuyển slide. `Home`/`End`: đầu/cuối. `O`: mục lục. `N`: ghi chú thuyết trình. `F`: toàn màn hình. `Esc`: đóng bảng. Có thể vuốt trên màn hình cảm ứng. Bấm vào nền không chuyển slide.

Thanh điều khiển ở cuối màn hình hiện rõ khi di chuyển con trỏ hoặc nhận focus. Nút **In / PDF** xuất toàn bộ 28 slide. Ghi chú không xuất lên mặt slide/PDF; có bản văn bản tại [speaker-notes.md](speaker-notes.md).

## Nội dung và nguồn

Bài gốc: `paper/main.tex` và `paper/main.pdf`. Biểu đồ đọc CSV hiện có trong `thucnghiem/results/`; không chạy lại thực nghiệm. [sources.json](sources.json) lưu đường dẫn, SHA-256 nguồn, số liệu biểu đồ và các lưu ý đối chiếu.

Hình thức tham khảo HTML PLM + MCNN do người dùng cung cấp: nền kem, bìa xanh đậm, màu xanh/cam, hình lớn và kết luận ngắn cuối slide. Bố cục/mã trình bày mới; không sao chép ảnh nhúng hoặc nội dung khoa học từ bản tham khảo. Font Lato được nhúng theo SIL OFL 1.1; xem [FONT-LICENSE.txt](FONT-LICENSE.txt).

Quy ước số liệu:

- Generator 3.0 chỉ bán tổng hợp ở lớp bối cảnh địa lý; tin báo, sự cố và nhãn được sinh. Candidate 4.1 hoàn toàn tổng hợp.
- Hai bundle độc lập về artifact, không phải hai kiểm chứng thực địa độc lập, không phải một mẫu xuyên cả ba RQ.
- RQ2 oracle grouping chỉ cô lập đánh giá điểm; RQ3 dùng predicted clusters.
- `Δ = candidate − comparator`: harm/trễ hạn âm là tốt hơn. Không dùng nhầm effect đã định hướng lợi ích.
- Các thanh CI của ARI/NDCG là bootstrap 95%; không suy kiểm định giữa phương pháp từ độ chồng lấn CI. Biểu đồ điều phối theo scenario chỉ mô tả trung bình; suy luận dùng 40 cặp seed sau gộp điều kiện.
- Holm p cho deadline revised-vs-nearest trong CSV cấp seed khoảng `1.1745e-6`, còn prose bài khoảng `1.3e-6`; slide 19 dùng số CSV. Kết luận kiểm định không thay đổi.
- Lý do sử dụng dữ liệu được trình bày là lý do phương pháp luận theo thiết kế; không tự gán lịch sử quyết định chưa được ghi nhận. Không khẳng định không có dữ liệu thực ở bất kỳ đâu.

## Tái tạo và kiểm tra

Chạy từ gốc repository:

```bash
.venv/bin/python presentation/flood-rescue-defense-v1/build.py
.venv/bin/python presentation/flood-rescue-defense-v1/validate.py
```

`build.py` dùng thư viện chuẩn Python và font Lato tại `/usr/share/fonts/truetype/lato`; `validate.py` dùng Playwright đã có trong `.venv`. Nếu Chromium chưa được tìm thấy tự động, truyền `--browser /duong/dan/chrome-headless-shell`.

Kiểm tra ghi vào [checks/validation.json](checks/validation.json): lỗi JavaScript, yêu cầu mạng ngoài, layout, font, điều hướng và fit ở ba viewport. [checks/contact-sheet.png](checks/contact-sheet.png) tổng hợp ảnh 28 slide; ảnh từng slide nằm cùng thư mục. PDF xuất từ Chromium theo kích thước 16:9.

Bản này không chỉnh bài báo/báo cáo, không thay quyết định nghiên cứu và không xuất bản lên dịch vụ ngoài.
