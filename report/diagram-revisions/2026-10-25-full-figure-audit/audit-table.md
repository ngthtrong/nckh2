# Rà soát đủ 46 hình trong báo cáo

Cỡ chữ lấy từ PDF ở zoom 1, đơn vị pt xấp xỉ (pdftohtml làm tròn). Đây là tập cỡ chữ vector **trên trang**, gồm cả caption, công thức và chỉ số; không phải phép OCR đo font bên trong ảnh raster. Các hình 3.1/3.8 còn chỉ số toán học 8 pt theo ký pháp gốc; chữ chính vẫn rõ. Ảnh giao diện được kiểm tra trực quan theo bố cục gốc. Các trang trong bảng là chỉ số trang PDF, không phải số trang in ở chân trang.

| Hình | Cỡ nhỏ trước / loại ảnh | Cỡ chữ vector trên trang sau (pt) | Trang PDF sau | Xử lý |
|---|---|---|---|---|
| 2.1 | 9 | 9, 10, 13 | 32 | Giữ nguyên: chữ và bố cục đủ rõ khi xem ở kích thước in; giữ concept gốc. |
| 2.2 | 9 | 9, 10, 13 | 34 | Giữ nguyên: chữ và bố cục đủ rõ khi xem ở kích thước in; giữ concept gốc. |
| 2.3 | 9 | 9, 10, 13 | 36 | Giữ nguyên: chữ và bố cục đủ rõ khi xem ở kích thước in; giữ concept gốc. |
| 2.4 | 9 | 9, 12, 13 | 38 | Giữ nguyên: chữ và bố cục đủ rõ khi xem ở kích thước in; giữ concept gốc. |
| 2.5 | 9 | 9, 10, 13 | 39 | Sửa ERD: 7 bảng, 70 cột; bỏ icon, Crow’s Foot đen trắng, PK/NN/UQ/CI/REF. |
| 2.6 | 4 | 9, 10, 11, 13 | 42 | Vẽ lại giữ hai vùng xanh/tím và ranh giới truth, tăng chữ; A4 ngang. |
| 2.7 | 4 | 9, 10, 11, 13 | 44 | UML đen trắng; 15 use case, actor ngoài hai subject; liên kết thẳng. |
| 2.8 | 5 | 9, 10, 11, 13 | 45 | UML đen trắng; đủ 8 use case; association và extend là đường thẳng. |
| 2.9 | 5 | 9, 10, 11, 13 | 46 | UML đen trắng; đủ 10 use case; include/extend đúng hướng, đường thẳng. |
| 2.10 | 8 | 9, 10, 11, 13 | 49 | Vẽ lại đen trắng: Hive/API, trạng thái, polling foreground; A4 ngang. |
| 2.11 | 11 | 11, 13 | 50 | Giữ nguyên: chữ và bố cục đủ rõ khi xem ở kích thước in; giữ concept gốc. |
| 2.12 | 9 | 9, 10, 13 | 52 | Giữ nguyên: chữ và bố cục đủ rõ khi xem ở kích thước in; giữ concept gốc. |
| 2.13 | 12 | 12, 13 | 54 | Giữ nguyên: chữ và bố cục đủ rõ khi xem ở kích thước in; giữ concept gốc. |
| 2.14 | 10 | 10, 13 | 55 | Giữ nguyên: chữ và bố cục đủ rõ khi xem ở kích thước in; giữ concept gốc. |
| 2.15 | 8 | 9, 10, 11, 13 | 56 | Vẽ lại đen trắng: ảnh/AI tùy chọn, khai báo, GPS, Outbox; A4 ngang. |
| 2.16 | 6 | 9, 10, 11, 13 | 58 | Vẽ lại đen trắng; giữ host, 3 container, volume, cổng, client/gateway; A4 ngang. |
| 2.17 | 7 | 9, 10, 11, 13 | 61 | Vẽ lại đen trắng; đủ data/SMS, ACK, chính sách ảnh, retry/rejected; A4 ngang. |
| 2.18 | 7 | 9, 10, 13 | 62 | Vẽ lại máy trạng thái đen trắng, tăng chữ; giữ bốn trạng thái và điều kiện đóng. |
| 2.19 | 9 | 9, 10, 13 | 63 | Giữ nguyên: chữ và bố cục đủ rõ khi xem ở kích thước in; giữ concept gốc. |
| 2.20 | 10 | 10, 13 | 65 | Giữ nguyên: chữ và bố cục đủ rõ khi xem ở kích thước in; giữ concept gốc. |
| 2.21 | Raster; xem trực quan | Raster; giữ bố cục gốc | 67 | Giữ nguyên tệp ảnh và bố cục gốc theo yêu cầu: nhóm 3 ảnh điện thoại / 2 ảnh dashboard; không tách trang hoặc thêm vùng phóng to. |
| 2.22 | Raster; xem trực quan | Raster; giữ bố cục gốc | 68 | Giữ nguyên tệp ảnh và bố cục gốc theo yêu cầu: nhóm 3 ảnh điện thoại / 2 ảnh dashboard; không tách trang hoặc thêm vùng phóng to. |
| 2.23 | Raster; xem trực quan | Raster; giữ bố cục gốc | 69 | Giữ nguyên tệp ảnh và bố cục gốc theo yêu cầu: nhóm 3 ảnh điện thoại / 2 ảnh dashboard; không tách trang hoặc thêm vùng phóng to. |
| 2.24 | Raster; xem trực quan | Raster; giữ bố cục gốc | 70 | Giữ nguyên tệp ảnh và bố cục gốc theo yêu cầu: nhóm 3 ảnh điện thoại / 2 ảnh dashboard; không tách trang hoặc thêm vùng phóng to. |
| 2.25 | Raster; xem trực quan | Raster; giữ bố cục gốc | 71 | Giữ nguyên tệp ảnh và bố cục gốc theo yêu cầu: nhóm 3 ảnh điện thoại / 2 ảnh dashboard; không tách trang hoặc thêm vùng phóng to. |
| 2.26 | Raster; xem trực quan | Raster; giữ bố cục gốc | 72 | Giữ nguyên tệp ảnh và bố cục gốc theo yêu cầu: nhóm 3 ảnh điện thoại / 2 ảnh dashboard; không tách trang hoặc thêm vùng phóng to. |
| 2.27 | Raster; xem trực quan | Raster; giữ bố cục gốc | 73 | Giữ nguyên tệp ảnh và bố cục gốc theo yêu cầu: nhóm 3 ảnh điện thoại / 2 ảnh dashboard; không tách trang hoặc thêm vùng phóng to. |
| 2.28 | Raster; xem trực quan | Raster; giữ bố cục gốc | 74 | Giữ nguyên tệp ảnh và bố cục gốc theo yêu cầu: nhóm 3 ảnh điện thoại / 2 ảnh dashboard; không tách trang hoặc thêm vùng phóng to. |
| 3.1 | 8 | 8, 9, 11, 12, 13 | 76 | Tăng font TikZ; giữ bố cục và nét đứt đánh giá, đen trắng. |
| 3.2 | 9 | 9, 12, 13 | 81 | Giữ nguyên: chữ và bố cục đủ rõ khi xem ở kích thước in; giữ concept gốc. |
| 3.3 | Raster; xem trực quan | 11, 12, 13, 14 | 84 | Vẽ lại cùng CSV 11 epoch, cùng hai đường và màu; PDF vector, tăng chữ. |
| 3.4 | Raster; xem trực quan | 11, 12, 13, 14 | 84 | Vẽ lại cùng CSV 11 epoch, cùng bốn đường và màu; PDF vector, tăng chữ. |
| 3.5 | Raster; xem trực quan | 9, 11, 12, 13, 14 | 85 | Vẽ lại recall cùng CSV, thứ tự lớp và màu; PDF vector, tăng chữ. |
| 3.6 | 5 | 9, 10, 11, 13 | 87 | Vẽ lại đen trắng; đủ split, huấn luyện, chọn checkpoint, test, nhánh nén; A4 ngang. |
| 3.7 | 8 | 9, 10, 11, 13 | 92 | Vẽ lại đen trắng; cache, eligibility, graph, Louvain, họ bằng chứng, P(c); A4 ngang. |
| 3.8 | 8 | 8, 9, 12, 13 | 93 | Giữ nguyên: chữ và bố cục đủ rõ khi xem ở kích thước in; giữ concept gốc. |
| 4.1 | Raster; xem trực quan | 10, 12, 13 | 109 | Vẽ lại ma trận raw từ CSV gốc; giữ nhãn, 16 ô, thang Viridis và tổng 256. |
| 4.2 | Raster; xem trực quan | 10, 12, 13 | 110 | Vẽ lại ma trận chuẩn hóa theo hàng; giữ cùng số liệu/thang màu, PDF vector. |
| 4.3 | Raster; xem trực quan | 10, 13 | 111 | Giữ đúng 12 ảnh lỗi và thứ tự confidence; tăng chú thích, A4 ngang. |
| 4.4 | 6 | 12, 13 | 113 | Giữ số liệu/bins, hai panel và màu; tăng legend, A4 ngang. |
| 4.5 | 8 | 13 | 120 | Giữ số liệu, hai panel và màu; A4 ngang để tăng chữ. |
| 4.6 | 7 | 9, 11, 12, 13 | 122 | Giữ ARI và CI, thứ tự và màu; tăng annotation và kích thước chữ khi in. |
| 4.7 | 10 | 10, 13 | 123 | Giữ nguyên: chữ và bố cục đủ rõ khi xem ở kích thước in; giữ concept gốc. |
| 4.8 | 10 | 12, 13 | 124 | Giữ NDCG@5 và CI, thứ tự/màu; tăng kích thước chữ khi in. |
| 4.9 | 9 | 9, 12, 13 | 125 | Giữ năm điều kiện, số liệu, cặp màu; tăng kích thước chữ khi in. |
| 4.10 | 6 | 10, 11, 13, 14 | 128 | Giữ nguyên PDF nguồn và hai panel; A4 ngang để chữ/số lớn hơn. |
