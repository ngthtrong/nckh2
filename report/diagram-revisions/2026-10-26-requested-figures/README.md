# Chỉnh đúng 11 hình theo yêu cầu ngày 26/10/2026

Bản PDF: [report/main.pdf](../../main.pdf), đồng nhất với [content.pdf](../../build/content/content.pdf), 167 trang. Chỉ sửa các hình trong bảng; giữ nguyên số liệu thực nghiệm và các hình ngoài danh sách. Phần chú thích và đoạn giải thích trực tiếp ERD 2.5 được cập nhật để khớp sơ đồ thiết kế. Bản lưu trước sửa ở `before/`; các trang PDF được render ở `pdf-pages/`.

| Hình | Trang in / trang PDF | Nội dung sửa |
|---|---|---|
| 2.2 | 14 / 34 | Đen trắng; rút gọn nội dung ô; tách tuyến gửi, ACK và phản hồi nghiệp vụ |
| 2.5 | 19 / 39 | ERD mức thiết kế: người gửi/thiết bị, báo cáo, đội, điều phối viên, sự kiện; thuộc tính chính và Crow's Foot |
| 2.6 | 22 / 42 | Hai luồng dọc: suy luận quan sát và đánh giá độc lập; giữ hai vùng xanh/tím |
| 2.10 | 29 / 49 | Nối dọc các bước cùng cột; tuyến riêng cho đọc cục bộ, API và điều kiện dừng |
| 2.12 | 32 / 52 | Chuyển sang đen trắng; giữ nội dung và các đường tiếp nhận |
| 2.15 | 36 / 56 | Nối dọc nội bộ; tách nhánh có AI và nhập tay, hai điểm nhập độc lập |
| 2.16 | 38 / 58 | Vẽ lại bằng Python/vector; biểu tượng thiết bị và logo công nghệ; ranh giới Compose, gateway ngoài, ba container và volume |
| 2.17 | 41 / 61 | Tách đường bỏ qua ảnh, chỉ text, lỗi tạm và rejected; không chồng/cắt đường nối |
| 2.19 | 43 / 63 | Đường tới khối kết quả vào cạnh trên; đường tiếp tục tác nghiệp trở về qua làn riêng |
| 3.6 | 67 / 87 | Nối thẳng từ cạnh dưới tới cạnh trên cho các bước cùng cột; vòng epoch riêng |
| 4.5 | 100 / 120 | Bỏ landscape; trang A4 dọc, rotation 0; giữ nguyên tệp biểu đồ và dữ liệu |

Nguồn sinh: [build_requested_figure_revisions.py](../../scripts/build_requested_figure_revisions.py). PDF/SVG/Draw.io trong `assets/diagrams/` là nguồn chèn vào báo cáo; generator cũ cũng gọi các factory mới khi chạy `readable-diagrams`. Để tái tạo riêng đúng mười sơ đồ đã sửa:

```bash
report/build/visual-env/bin/python report/scripts/build_requested_figure_revisions.py
python3 report/scripts/build.py content
make -C report check
git diff --check
```

Sơ đồ triển khai đối chiếu `docker-compose.yml`, hai cấu hình Nginx trong `products/docker/`, Dockerfile backend và chính sách gửi trong ứng dụng. Logo Docker, Flutter, ONNX, FastAPI, Nginx và SQLite lấy từ [Simple Icons 16.0.0](https://github.com/simple-icons/simple-icons/tree/16.0.0/icons), bộ sưu tập cấp phép [CC0](https://github.com/simple-icons/simple-icons/blob/16.0.0/LICENSE.md); tên và quyền thương hiệu vẫn thuộc chủ sở hữu. Tệp SVG nguyên bản, license và URL/hash nằm trong [tech-icons](../../assets/diagrams/tech-icons/sources.json). Biểu tượng điện thoại, màn hình và SMS là vector tự vẽ.

Kiểm tra: [diagram-validation.json](diagram-validation.json) ghi khung chữ/chồng chữ và hình học liên kết. Chín sơ đồ qua kiểm tra không giao cắt, chồng đoạn hoặc đi qua ô khác; hình 2.12 chỉ đổi màu, giữ tuyến gom ACK có chủ đích. Hai hình 2.2 và 2.12 được kiểm tra ba kênh RGB trùng nhau. Đã xem preview toàn bộ sơ đồ và các trang PDF quan trọng; `make check`, biên dịch và `git diff --check` đạt, log không có tràn lề hay tham chiếu/trích dẫn chưa giải quyết. Font PDF được nhúng.

[scope-validation.json](scope-validation.json) đối chiếu hash trước/sau: các tệp hiện hữu bị đổi đều nằm trong phạm vi trên hoặc là PDF tổng hợp/generator liên quan. Các bản tin và tóm tắt riêng, provenance số liệu, hình khác và dữ liệu nguồn được giữ nguyên. Không commit hoặc push.
