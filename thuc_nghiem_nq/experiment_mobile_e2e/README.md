# Công cụ mobile đã chuyển vào frontend

Xem hướng dẫn mới tại [products/fe/experiment_mobile/README.md](../../products/fe/experiment_mobile/README.md).

- Code Python: `products/fe/experiment_mobile/`.
- Code Flutter: `products/fe/app/lib/`.
- Dữ liệu hai run: `products/fe/app/assets/benchmarks/mobile/`.
- Build APK trực tiếp trong `products/fe/app` bằng Flutter; không còn build theo từng benchmark.
- `coordinator.py` tại đây chỉ chuyển tiếp lệnh cũ tới công cụ mới.

Các thư mục `benchmarks/`, `results/`, `sessions/` và `.venv/` cũ được giữ nguyên để sao lưu/tra cứu. Chúng không phải assets và không được đóng vào APK. Lượt mới dùng `benchmarks/` và `results/` ở vị trí mới. Lượt cũ gắn schema trước vẫn giữ làm bằng chứng, không trộn checkpoint với gói assets mới.
