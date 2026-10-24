# Kết quả E2E web giả lập ngày 24/10/2026

Hai lượt dưới đây được chạy thực tế bằng Playwright/Chromium qua ứng dụng Flutter web, backend và dashboard trong Docker. Mỗi lượt dùng cơ sở dữ liệu và Docker volume riêng, với ảnh được khóa trong `run_images.json`.

| Gold run | Báo cáo seed | Ảnh đầu vào | Kịch bản hoàn tất | PASS | FAIL | CHƯA CÓ |
|---|---:|---|---:|---:|---:|---:|
| run_001 | 316 | `high/flood_4800.jpg` | 5/5 | 45 | 0 | 1 |
| run_002 | 334 | `medium/flood_6286.jpg` | 5/5 | 45 | 0 | 1 |

Mỗi run có 46 tiêu chí. Mục **CHƯA CÓ** là trang chủ web chưa giải thích rõ AI on-device không khả dụng trên web. Các kiểm tra chức năng không có FAIL, nhưng khoảng trống giao diện này vẫn còn.

## Đầu ra của từng run

- **run_001 — `e2e-20261024-001854-784012`**: [summary.json](results/run_001__e2e-20261024-001854-784012/summary.json), [checks.csv](results/run_001__e2e-20261024-001854-784012/checks.csv), [ảnh minh chứng](results/run_001__e2e-20261024-001854-784012/screenshots/), [manifest](logs/run_001__e2e-20261024-001854-784012/manifest.json).
- **run_002 — `e2e-20261024-002154-108497`**: [summary.json](results/run_002__e2e-20261024-002154-108497/summary.json), [checks.csv](results/run_002__e2e-20261024-002154-108497/checks.csv), [ảnh minh chứng](results/run_002__e2e-20261024-002154-108497/screenshots/), [manifest](logs/run_002__e2e-20261024-002154-108497/manifest.json).

Mỗi thư mục screenshot có bốn ảnh: dashboard, bài cứu hộ đã gửi, SOS trong hàng đợi offline và lịch sử sau khi được điều phối. Ảnh đầu vào và hai file gold được chụp lại trong `data/<GOLD_RUN>__<RUN_ID>/`; ảnh backend nhận được lưu trong `uploads/<GOLD_RUN>__<RUN_ID>/`. Cả hai log `exit_code.txt` đều bằng 0.

## Các kịch bản đã kiểm tra

1. Dashboard: đăng nhập và quyền truy cập, bản đồ, cụm ưu tiên, điều phối cụm, chi tiết và lịch sử báo cáo, thống kê, Swagger UI.
2. Ứng dụng: gửi SOS có GPS, bài cứu hộ kèm ảnh, quyền xem ảnh, SHA-256 trên server, tiếng Việt và thời gian UTC; hàng đợi offline, tự đồng bộ và phản hồi trạng thái điều phối.
3. Mạng 300 kbit/s: chọn `compressedImage`, server nhận ảnh nén nhỏ hơn ảnh ở chế độ mạng mạnh.
4. Mạng 20 kbit/s: chọn `textOnly`, không upload ảnh.
5. Từ chối GPS: SOS vẫn gửi được, không tạo tọa độ giả, backend đưa báo cáo vào danh sách cần xem xét.

Runner chờ hết cửa sổ chống gửi trùng SOS 30 giây trước khi bắt đầu ca SOS offline (đợi đến ít nhất 31 giây kể từ SOS online). Ca offline vì vậy kiểm tra một yêu cầu mới; các tiêu chí hàng đợi và tự đồng bộ không bị bỏ qua. Runner lưu thêm ảnh `app_offline_queued.png`. Bộ kiểm tra runner gồm 9 bài đã đạt.

## Đối chiếu ảnh

| Run | File đầu vào (byte) | Ảnh server nhận ở mạng mạnh (byte) | Ảnh nén ở 300 kbit/s (byte) |
|---|---:|---:|---:|
| run_001 | 162.727 | 86.993 | 66.239 |
| run_002 | 38.779 | 40.590 | 31.596 |

Ảnh ở chế độ `fullImage` là ảnh do pipeline trình duyệt gửi lên, có thể đã được chuyển mã nên không nhất thiết cùng số byte với file dataset. Kiểm tra nén so với ảnh mà server nhận trong cùng run, không so trực tiếp với kích thước file dataset. SHA-256 của ảnh dataset trong snapshot khớp `run_images.json` ở cả hai run; hash ảnh lưu trên backend được đối chiếu riêng trong tiêu chí upload.

## Môi trường và phạm vi kết luận

- Flutter 3.47.5, Dart 3.13.4, Python 3.11.0, Playwright 1.63.0, Docker Engine 29.7.2.
- Flutter web được build mới trên Windows bằng `flutter build web --release --no-wasm-dry-run --dart-define=SERVER_URL=`, sau đó chạy Docker với `FE_BUILD_TARGET=prebuilt`. Runner vẫn dùng `--run --seed-run 1` và `--run --seed-run 2`; ba dịch vụ và năm kịch bản kiểm tra giữ nguyên.
- SHA-256 của `build/web/main.dart.js`: `e38cf261e24a4b74f8052534469e3abf19a56cafc28573a119d3e9e556818a2f`.
- Trạng thái mã nguồn lúc bắt đầu nằm trong `git_head.txt` và `git_status.txt` của mỗi log; lượt chạy dùng cả các sửa chưa commit tại máy, không chỉ riêng commit HEAD.
- Các kết quả ngày 19/10 và các đầu ra thử khởi động chưa hoàn tất đã được loại khỏi các thư mục đầu ra. Hai run nêu trên là kết quả hiện hành.
- Đây là kiểm tra luồng E2E trên web với hai ảnh và hai kịch bản seed. Không suy ra chất lượng AI, kết quả Android/SMS thực, hay kết quả cho toàn bộ 257 ảnh validation hoặc 80 gold run.

Các thư mục đầu ra vẫn theo chính sách `.gitignore` hiện có. Nếu chia sẻ kết quả qua Git, cần đưa kèm các artifact được liên kết ở trên; chỉ commit tài liệu này không tự đưa các artifact lên GitHub.
