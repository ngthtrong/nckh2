# Tài nguyên trình bày

`../logo-ctu.png` là logo dùng chung trên bìa và biểu mẫu. Logo được giữ
nguyên byte từ bộ báo cáo gốc. Không sao chép hình hay sơ đồ nghiên cứu.

`template-headers.pdf` chứa chín đầu trang vector của bìa và các biểu
mẫu CTU; `cover-frame.pdf` chứa hai khung bìa. Các tài nguyên này chỉ
có nội dung trình bày chung, không có thông tin đã điền của đề tài.
Nguồn mẫu, vùng cắt và hash nằm trong `template-layout-provenance.json`.
Chúng là tài nguyên nội bộ của template; build không đọc báo cáo gốc.
Khi thay cơ quan, cập nhật cả logo, hai PDF và metadata.

Đặt hình của đề tài mới vào `figures/`, sơ đồ vào `diagrams/`; hai thư mục
đã được cấu hình trong `template/packages.tex`. Hình PDF/PNG/JPG dùng
được trực tiếp với XeLaTeX. Xuất SVG hoặc draw.io sang PDF trước khi chèn.
