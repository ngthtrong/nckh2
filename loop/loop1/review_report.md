# BÁO CÁO PHẢN BIỆN KHOA HỌC (CRITICAL REVIEW)

> Vai trò: Giáo sư chủ tịch hội đồng phản biện.
> Phạm vi rà soát: `paper/` (main.tex, references.bib), `demo/` (code + results JSON), `resource/` (BaiBao_NoiDung.md, GiaiThichCongThuc.md).
> Ngày: 2026-07-24.
> Nguyên tắc: chỉ liệt kê lỗi **thực sự tồn tại**, mỗi lỗi kèm bằng chứng kiểm chứng được. Không tính các điểm đã đúng.

---

## A. LỖI SỐ LIỆU / TÁI LẬP (nghiêm trọng nhất)

### A1. Khoảng cách kịch bản S1 mâu thuẫn ở 3 nơi
- **Hiện trạng:** docstring generator ghi "40 km", comment ghi "90 km", paper ghi "$\sim$90 km".
- **Bằng chứng:** tọa độ thực trong `demo/data/generate.py` là Huế `(16.4637, 107.5909)` → Hội An `(15.8801, 108.3380)`. Chạy chính hàm `haversine` của demo cho **102,84 km**.
- **Chất vấn:** *Con số nào là đúng? Nếu tọa độ là nguồn sự thật thì cả ba nhãn văn bản đều sai lệch. Một bài báo không thể để ba giá trị khác nhau cho cùng một khoảng cách.*

### A2. Tuyên bố kích thước gói "112–137 byte" không có căn cứ
- **Hiện trạng:** paper (Discussion) khẳng định gói metadata "measures only 112--137 bytes".
- **Bằng chứng:** không tồn tại script nào tính con số này trong `demo/`. Đo bản ghi đầy đủ cho 179–304 byte — không khớp.
- **Chất vấn:** *Con số 112–137 lấy từ đâu? Đây là vi phạm trực tiếp ràng buộc "không bịa dữ liệu". Phải rút bỏ hoặc thay bằng con số đo được bằng script tái lập.*

---

## B. LỖI TRÍCH DẪN / HỌC THUẬT

### B1. Hai baseline được benchmark nhưng không trích dẫn
- **Hiện trạng:** HDBSCAN và Spectral Clustering là baseline định lượng trong bảng so sánh, nhưng `campello2013hdbscan` và `vonluxburg2007spectral` tuy có trong `references.bib` lại **không hề được `\cite`**.
- **Chất vấn:** *Sao lại đưa một phương pháp vào bảng benchmark mà không dẫn nguồn gốc phương pháp đó? Đây là khe hở trích dẫn cơ bản.*

---

## C. LỖI TRÌNH BÀY / FORMAT

### C1. Đếm số hình mâu thuẫn nội bộ (bản VN)
- **Hiện trạng:** một chỗ liệt kê 7 hình, ghi chú soạn thảo lại ghi "6 hình" kèm đường dẫn cũ `demo/v2/results/figures/`.
- **Chất vấn:** *Có 6 hay 7 hình? Đường dẫn `demo/v2/` còn tồn tại không?*

### C2. Làm tròn ARI không thống nhất (bản VN)
- **Hiện trạng:** abstract từng dùng "ARI = 0,89" lỏng trong khi thân bài dùng "0,892".
- **Chất vấn:** *Một con số kết quả cốt lõi phải nhất quán về độ chính xác trong toàn văn bản.*

### C3. `demo/run_all.py` không nhất quán sau khi thêm thí nghiệm
- **Hiện trạng:** sau khi chèn thí nghiệm mới, banner trộn lẫn `/12` và `/13`.
- **Chất vấn:** *Tổng số bước là bao nhiêu? Banner phải đồng bộ.*

---

## D. LỖI BIÊN DỊCH

### D1. Paper không build dưới `pdflatex`
- **Hiện trạng:** ký tự "ị" (U+1ECB) trong tên tác giả không được `inputenc` hỗ trợ; `lualatex` lỗi font metric.
- **Bằng chứng:** chỉ `xelatex` biên dịch thành công (19 trang).
- **Chất vấn:** *Engine biên dịch chính thức là gì? Ghi chú "pdflatex build" trong tài liệu nội bộ đã lỗi thời.*

---

## TÓM TẮT MỨC ĐỘ

| Nhóm | Số lỗi | Mức độ |
|------|--------|--------|
| A. Số liệu/tái lập | 2 | Nghiêm trọng (vi phạm no-hallucination) |
| B. Trích dẫn | 1 | Trung bình |
| C. Trình bày | 3 | Nhẹ nhưng bắt buộc sửa |
| D. Biên dịch | 1 | Tài liệu hóa |
