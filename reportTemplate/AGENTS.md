# Hướng dẫn cho agent trong template

Template phải dùng được khi sao chép riêng ra dự án khác. Giữ nội dung
nghiên cứu trống cho đến khi người dùng yêu cầu điền; không lấy dữ liệu
từ báo cáo hoặc dự án cũ làm nội dung mẫu mặc định.

[HinhThucBC.pdf](HinhThucBC.pdf) là căn cứ ưu tiên về hình thức và trình
tự quyển. Chỉ đồng bộ thay đổi từ báo cáo đang dùng khi phù hợp với PDF
này; phân biệt quy định bắt buộc với lựa chọn dàn trang của dự án.

Khi vẽ/chỉnh sơ đồ dữ liệu CDM, LDM hoặc PDM, dùng skill
[cdm-ldm-pdm](.agents/skills/cdm-ldm-pdm/SKILL.md). Đọc skill trước khi
tạo đặc tả/hình; đặt đầu vào và hình của đề tài ở `assets/diagrams/`,
giữ dữ liệu minh họa trong skill. Nếu nhiệm vụ chỉ tạo skill hoặc xem
mẫu, sinh ảnh tạm dưới `build/` và không chèn vào báo cáo chính.

Quy tắc trình bày và đồng bộ mới nhất nằm trong [RULES.md](RULES.md).
Khi sửa khung trình bày, đọc tệp này, giữ cùng nguồn biểu mẫu giữa quyển
và bốn PDF riêng, rồi chạy `make all smoke` và `make check`. Hình/bảng
phải giữ đủ thông tin, bảng thân bài cỡ 13 bp; không thu nhỏ toàn bảng
để ép vừa trang. Nội dung minh họa chỉ nằm trong `examples/`.
