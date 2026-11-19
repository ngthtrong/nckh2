# Plan E2E Android thật: admin tải gói theo run

> Khi triển khai, dùng `superpowers:executing-plans` theo từng phần. Tài liệu này là kế hoạch, chưa có runner Android hoặc endpoint E2E mới được triển khai.

**Mục tiêu:** trên điện thoại thật, đăng nhập admin → chọn run → tải gói E2E → chạy/tiếp tục → xuất kết quả. Dùng model seed 1024 pruning/PTE và backend thử nghiệm riêng.

**Kiến trúc:** app chạy AI và luồng gửi/đồng bộ thật; máy tính điều phối backend, proxy mạng và Playwright kiểm tra dashboard. Tách gói E2E khỏi gói benchmark 256 ảnh test. Stack giữ Flutter/Dart, FastAPI/Python, Docker và Playwright hiện có.

**Căn cứ:** yêu cầu trong cuộc trao đổi ngày 22/10/2026; runner web tại `thuc_nghiem_nq/experiment_e2e/e2e_system.py`; hướng dẫn Android tại `thuc_nghiem_nq/docs_thuc_nghiem/experiment_mobile_app.md`.

## 1. Phần tái sử dụng

| Có sẵn | Dùng lại cho Android |
|---|---|
| `experiment_e2e/e2e_system.py` | Chọn/kiểm tra gold run, đối chiếu API, kiểm tra dashboard, manifest, checkpoint, cách tổng hợp kết quả |
| `experiment_weak_network/weak_network.py` | Tham khảo/tách phần `ThrottledProxy`; bổ sung đổi profile và ngắt/kết nối lại, không dùng runner gửi payload cố định thay cho app |
| `products/be/build_benchmark_package.py` | Cách đóng gói manifest + ảnh + hash; định dạng E2E riêng để không làm hỏng gói model benchmark |
| `model_benchmark_card.dart`, `AdminSession` | Đăng nhập admin, tải có Bearer token, tiến độ tải, cache, hủy và xuất kết quả |
| `app/integration_test/system_test.dart` | Luồng repository/use case, outbox và đối chiếu server; thay giả định desktop/đường ảnh trên máy tính khi chuyển sang Android |

**Không dùng lại nguyên phần Playwright/CDP để điều khiển Android.** Playwright giữ nhiệm vụ dashboard; giới hạn mạng Android thực hiện qua proxy mà app thật sự đi qua.

## 2. Các phần cần viết

### A. Gói dữ liệu và backend — hoàn thành trước
- [ ] Thêm `thuc_nghiem_nq/experiment_mobile_e2e/build_package.py`: đóng gói riêng từng `run_001…run_080`, gồm manifest kịch bản, thông tin gold/hash và ảnh fixture. Ban đầu dùng ảnh validation theo `thuc_nghiem_nq/experiment_e2e/run_images.json`: run_001 dùng `high/flood_4800.jpg`, run_002 dùng `medium/flood_6286.jpg`. Builder gói phải đọc đúng cấu hình này và kiểm tra nhãn/hash, không tự chọn lại ảnh; không gọi đây là đánh giá trên 257 ảnh.
- [ ] Thêm `products/be/mobile_e2e.py`, nối router trong `main.py`: đề xuất `GET /api/experiments/e2e/runs` và `GET /api/experiments/e2e/package?run=run_001`. Cả danh sách/gói đều kiểm tra quyền admin phía server, kiểm tra run hợp lệ và chỉ bật trong môi trường thực nghiệm.
- [ ] Mỗi lượt dùng DB/volume thử nghiệm riêng do coordinator tạo; seed gold thực hiện trên server, không cho app tự ghi gold vào DB. Manifest ghi `goldRun` và `sessionId` riêng, hash gói, ảnh, model/runtime dự kiến.
- [ ] Kiểm tra: người thường bị từ chối; sai run/hash/ảnh bị từ chối; gói tải dở không được coi là hợp lệ.

### B. Runner trong app và màn hình admin
- [ ] Thêm `lib/domain/services/mobile_e2e_runner.dart` và `lib/presentation/widgets/mobile_e2e_card.dart`; gắn card ở `settings_screen.dart` cạnh công cụ benchmark hiện có.
- [ ] Giao diện: **Chọn run → Tải gói → Kiểm tra sẵn sàng → Chạy/Tiếp tục → Xuất kết quả**. Chỉ admin được mở công cụ; không nhúng tài khoản/token vào gói hay file kết quả.
- [ ] Runner gọi đúng use case/model/outbox của app, không gọi API trực tiếp để thay hành vi cần kiểm tra. Khóa PTE và hash model; thiếu AI hoặc đổi runtime phải ghi FAIL/NOT_RUN, không âm thầm dùng nhãn giả.
- [ ] Checkpoint theo session/stage, lưu ID báo cáo trước khi retry; tiếp tục không tạo báo cáo trùng hoặc đổi gold run. Từ chối bắt đầu khi lẫn dữ liệu pending ngoài phiên thử; không tự xóa dữ liệu người dùng.
- [ ] Phân biệt tự động kiểm tra AI/gửi/đồng bộ với thao tác giao diện Android. Bước cần chạm UI, cấp/từ chối GPS hoặc thay mạng được hướng dẫn và ghi bằng chứng thủ công; không đánh dấu đã kiểm thử UI chỉ vì service chạy được.
- [ ] Thêm test Dart cho đọc gói, khóa runtime, checkpoint/resume và retry không trùng; kiểm tra nút công cụ không hiện khi chưa có quyền admin.

### C. Điều phối và lưu bằng chứng
- [ ] Thêm `thuc_nghiem_nq/experiment_mobile_e2e/coordinator.py`: dùng lại phần chuẩn bị/kiểm tra gold và Docker của web, cung cấp backend qua LAN/proxy, thay đổi profile theo stage và chạy kiểm tra dashboard bằng Playwright. Trước mỗi stage, app/coordinator phải xác nhận cùng session/gold/hash.
- [ ] Dashboard/API kiểm tra trực tiếp backend; app gửi qua proxy để đo đúng mạng đã giới hạn. Thử offline không chỉ đặt cờ “offline” trong runner. Bản đầu hỗ trợ đổi profile qua coordinator và thao tác mạng thủ công có ghi nhận.
- [ ] Thêm `app/integration_test/mobile_e2e_test.dart` để tự động hóa các màn hình quan trọng trên Android sau khi luồng tải/chạy trong app đã hoạt động; không dùng Playwright web làm bằng chứng UI Android.
- [ ] Lưu `checks.csv`, `summary.json`, manifest, checkpoint, logcat và ảnh chụp trong `experiment_mobile_e2e/results/<device>/<goldRun>__<sessionId>/`. Ghi mã máy/Android, hash APK/model/gói, thời điểm, profile, ID báo cáo và phương thức kiểm tra tự động/thủ công. Tổng hợp PASS/FAIL/NOT_RUN; không tính NOT_RUN thành PASS.
- [ ] Chạy kiểm tra nhỏ: một máy, run_001, online; sau đó đủ stage, resume, run_002, rồi mới mở rộng các máy còn lại.

## 3. Các stage của một lượt

| Stage | Thao tác chính | Điều kiện đạt |
|---|---|---|
| Chuẩn bị | Admin tải gói, đối chiếu backend/gold/model | Đúng run, đủ dữ liệu, hash khớp |
| AI + online | Chạy PTE trên ảnh trong gói; gửi bài/SOS theo luồng app | Có nhãn/confidence hợp lệ; server nhận đúng ảnh/metadata; dashboard thấy báo cáo |
| Offline → online | Ngắt kết nối; gửi; nối lại | Outbox giữ báo cáo, server chưa nhận khi offline; sau nối lại nhận đúng một lần, hàng đợi hết |
| Mạng yếu | Thử 300 và 20 kbit/s qua proxy | Ghi profile thực áp, chế độ gửi, byte và độ trễ; đối chiếu với policy thật của app |
| Thiếu GPS + phản hồi | Người chạy từ chối quyền vị trí; dashboard đổi trạng thái | Không tạo tọa độ giả, vào hàng xem xét; app nhận cập nhật trạng thái |

Lưu ý: Android có AI thật nên không mặc định ép mọi ảnh sang ảnh nén ở 300 kbit/s như web; confidence có thể làm policy chọn metadata. Ghi dự đoán/confidence và kiểm tra theo policy hiện hành, không sửa threshold từ test. Nếu cần phủ nhánh gửi ảnh, thêm fixture đã xác định từ validation và ghi rõ cơ sở chọn. Chất lượng AI vẫn do benchmark model đánh giá, không suy Accuracy từ một ảnh E2E.

## 4. Hướng dẫn chạy sau khi triển khai

1. **Máy tính:** mở Docker, nối cùng LAN với điện thoại, cắm USB/cho phép USB debugging. Coordinator khởi tạo backend/DB riêng, dashboard và proxy cho run_001; xác nhận app truy cập được URL LAN. Chưa chạy trên server đang có dữ liệu thật.
2. **Build/cài APK thử nghiệm:** dùng đúng asset 1024 pruning/PTE, cấu hình `SERVER_URL` qua proxy LAN; ghi hash APK/model. Cài lên điện thoại, kiểm tra quyền ảnh/vị trí. Giữ chế độ chạy APK nhất quán khi so nhiều máy.
3. **Đăng nhập admin:** vào Cài đặt → E2E di động → chọn run_001 → Tải gói. Chờ kiểm tra hash, xác nhận đúng model và cùng session với coordinator.
4. **Nhấn Chạy:** runner thực hiện online; người chạy làm các thao tác UI/quyền được yêu cầu. Coordinator/Playwright đối chiếu báo cáo trên dashboard và API.
5. **Chạy tiếp các stage:** offline → online, mạng 300/20 kbit/s, thiếu GPS và phản hồi. Chỉ chuyển bước khi đã lưu trạng thái/bằng chứng của bước trước; bước không thực hiện được ghi NOT_RUN kèm lý do.
6. **Nếu gián đoạn:** giữ backend/DB, checkpoint và gói; chọn Tiếp tục đúng session. Không seed/reset lại DB hoặc gửi lại toàn bộ kịch bản từ đầu.
7. **Xuất kết quả:** trên app xuất JSON/CSV; coordinator gom cùng log/screenshot, kiểm tra đủ stage và không FAIL trước khi coi lượt hoàn tất. NOT_RUN vẫn phải công bố.
8. **Đổi run/máy:** hoàn tất, lưu bộ cũ rồi tạo session/DB riêng cho run_002 hoặc máy kế tiếp. Trước mắt chạy hai run trên một máy; chưa cần chạy cả 80 run.

**Đầu ra cần bàn giao khi viết code:** runner/app card, endpoint/gói E2E, coordinator, các test ở trên và `experiment_mobile_e2e/README.md` chứa lệnh thực tế đã kiểm chứng. Chưa coi các tên endpoint/file đề xuất trong plan là chức năng hiện có.
