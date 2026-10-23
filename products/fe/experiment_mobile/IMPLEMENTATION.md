# Benchmark mobile đóng cùng app Flutter

- Assets schema 2 cố định của run_001/run_002; không chứa timestamp, server hay tên lượt. prepare_assets.py dùng Python stdlib, kiểm tra gold/CSV/ảnh và giữ PTE seed1024 pruning.
- Flutter admin mặc định có E2E, người dùng thường không thấy công cụ. Chọn run từ assets; khi mở gói lấy tên lượt/controlPath từ coordinator, đối chiếu hash, rồi ghép tên vào checkpoint mà không đổi gói.
- Build trực tiếp ở products/fe/app, không cần coordinator hay venv khi Flutter build.
- Coordinator/proxy vẫn dùng Docker flood-rescue hiện có; start/resume phục vụ cả hai run, chia sẻ profile mạng nhưng lưu tiến độ/kết quả riêng.
- Dashboard/collect có --run 1/2; JSON/CSV dùng ngày giờ Việt Nam + tên benchmark. Không lưu token/mật khẩu.
- Nguồn Python chính và tests chuyển vào products/fe/experiment_mobile. Entry point cũ chỉ chuyển tiếp; giữ nguyên runtime artifacts cũ.
- Gói/checkpoint schema 1 vẫn đọc được để kiểm thử tương thích, nhưng app mới chỉ chọn các gói schema 2 trong assets.
