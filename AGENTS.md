# Hướng dẫn tiếp tục dự án

## Bắt đầu mỗi cuộc hội thoại

1. Kiểm tra `git status --short` và `git log -5 --oneline` trước khi sửa. Giữ nguyên thay đổi sẵn có của người dùng.
2. Đọc `docs/PROJECT_STATUS.md`, checkpoint được liên kết trong đó và `docs/DELIVERY_PLAN.md`.
3. Chọn công việc tiếp theo theo trạng thái thực tế và yêu cầu mới nhất của người dùng. Kiểm tra file/entrypoint tồn tại trước khi chạy lệnh từ tài liệu cũ.

## Phạm vi hiện tại

- Giai đoạn viết bài báo đã hoàn thành theo xác nhận của người dùng ngày 2026-09-07. Tập trung hoàn thiện sản phẩm bàn giao; không tự mở lại nghiên cứu hoặc viết lại bài báo.
- Repo phụ trách backend Python, xử lý trọng số/phân cụm/tính điểm, web dashboard và hồ sơ bàn giao. Mobile do nhóm khác phát triển; chỉ làm hợp đồng API, dữ liệu mẫu và kiểm thử tích hợp phía server tại đây.
- Mã nguồn ứng dụng đặt trong `apps/`: `apps/backend/` chứa backend và lõi xử lý; `apps/web/` chứa web dashboard. Đây là cấu trúc triển khai đã thống nhất, tạo khi bắt đầu xây ứng dụng.
- Stack đã chọn: FastAPI/Pydantic, PostgreSQL/PostGIS, SQLAlchemy/Alembic; React/TypeScript/Vite, Ant Design, TanStack Query, Leaflet/React Leaflet; REST + SSE, worker Python riêng và Docker Compose. Đọc `docs/decisions/001-application-stack.md` trước khi triển khai; phiên bản thư viện và thư viện thuật toán còn cần kiểm tra, không tự đổi stack hoặc mở lại bước chọn stack.
- Đối chiếu sản phẩm với `resource/Thuyết minh NCKH.md`, mục 16–18. Bộ mô hình AI vẫn là sản phẩm cần kiểm kê/phối hợp bàn giao, dù không phát triển mobile trong repo.
- `resource/DTN_Rescue_System_Spec.md` là tài liệu tham khảo mở rộng; không tự triển khai DTN, BLE, UAV hoặc simulator khi chưa có yêu cầu đưa vào phạm vi.
- Giữ nguyên artifact nghiên cứu trong `paper/` và `demo/` khi làm sản phẩm. Không coi dữ liệu bán tổng hợp là dữ liệu cứu hộ thực hoặc kết quả kiểm thử local là nghiệm thu chính thức. Không bịa kết quả, mẫu biểu, chữ ký hay trạng thái chấp nhận bài báo.
- Công thức trong tài liệu giải thích có thể khác phiên bản bài báo/notebook. Đối chiếu và ghi quyết định trước khi chuyển thành logic sản phẩm; không tự đổi trọng số nghiên cứu.

## Sau mỗi thay đổi lớn và khi dừng việc

- Theo `docs/CHECKPOINTS.md`: cập nhật bảng công việc, trạng thái, bằng chứng kiểm tra và bước tiếp theo.
- Tạo checkpoint mới cho mốc lớn; ghi rõ phần còn dở và file chưa commit. Không ghi đè lịch sử checkpoint cũ để mô tả một trạng thái mới.
- Không tự commit/push chỉ để tạo checkpoint; báo cáo tài liệu chưa commit chính xác. Không đưa secret hoặc dữ liệu cá nhân vào checkpoint/log.
- Chỉ đánh dấu hoàn thành khi có đầu ra và kiểm tra phù hợp. Khi bàn giao, nêu thay đổi, kiểm tra đã chạy, giới hạn và việc tiếp theo.
