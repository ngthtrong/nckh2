# Đối chiếu content.pdf với mã nguồn hiện tại

Ngày rà soát: 24/10/2026. Báo cáo được kiểm tra: `report/build/content/content.pdf`, 157 trang; SHA-256 `bb77f0a953444821bcde809ba12879aac0b64a62b6da6279da74636d77bda116`.

**Kết luận:** số liệu của các bảng chính đã kiểm tra khớp artifact hiện có. Sai khác tập trung ở các sơ đồ kiến trúc/nghiệp vụ mới và một số đoạn mô tả khả năng vận hành. Có **19 nhóm nội dung cần sửa/chuẩn hóa**, trong đó các mục 1–13 ảnh hưởng trực tiếp đến cách hiểu thuật toán, chức năng hoặc triển khai. Những hạn chế được báo cáo công bố đúng được tách riêng, không tính thành lỗi mới.

Quy ước trang bên dưới: **trang in trong báo cáo**, kèm trang vật lý PDF trong ngoặc. Ví dụ trang 64 (PDF 86). Chỉ đối chiếu mã nguồn và bằng chứng trong workspace hiện tại; không mặc định README cũ là đúng hơn mã đang chạy.

## 1. Hình 3.7 ghi sai công thức ưu tiên — cần sửa trước

- **Vị trí:** trang 64 (PDF 86), Hình 3.7.
- **Báo cáo ghi:** `P(c) = w1*Nc + w2*Vc + w3*Fc + w4*Uc`.
- **Mã thực tế:** điểm có chặn là tích của hệ số yếu thế với tổng có trọng số của E, F, N. N được nén bằng log, V đi qua tanh; có confidence và họ bằng chứng trước tổng hợp. V không phải một số hạng tuyến tính độc lập.
- **Căn cứ:** [priority.py:148](<D:/nckh-flood-rescue/nckh2/products/be/rescue_core/priority.py:148>), [priority.py:153](<D:/nckh-flood-rescue/nckh2/products/be/rescue_core/priority.py:153>). Phần công thức chi tiết ở mục 3.4.8 của báo cáo đã mô tả đúng.
- **Sửa:** thay khối công thức trên hình bằng `P_k = [1+(mu-1)tanh(V_bar/s)](0.34 E_bar + 0.33 F_bar + 0.33 N_bar)`; chỉ rõ các đầu vào là đại lượng đã tổng hợp theo họ bằng chứng.
- **Nguồn hình:** [flow_06_clustering_priority.drawio](<D:/nckh-flood-rescue/nckh2/report/assets/diagrams/flow_06_clustering_priority.drawio>); chuỗi sai còn nằm ở [generate_drawio_diagrams.py:1360](<D:/nckh-flood-rescue/nckh2/report/scripts/generate_drawio_diagrams.py:1360>).

## 2. Hình 3.6 sai số lượng ảnh và scheduler, lẫn bước chọn checkpoint với kết quả test

- **Vị trí:** trang 60 (PDF 82), Hình 3.6.
- **Báo cáo ghi:** train khoảng 1.192, validation khoảng 254; `AdamW + CosineAnnealing`; ô lưu checkpoint chứa Accuracy 75,78% và F1 74,26% trước ô đánh giá test.
- **Thực tế:** split lưu **1.189 train / 257 validation / 256 test**. Notebook dùng **ReduceLROnPlateau**, factor 0,5, patience 3, min_lr 1e-7. Hai số 75,78%/74,26% là kết quả test FP32 seed 1024, không phải tiêu chí chọn checkpoint trên validation.
- **Căn cứ:** [image-split.tex](<D:/nckh-flood-rescue/nckh2/report/generated/tables/image-split.tex>), [training_img.ipynb](<D:/nckh-flood-rescue/nckh2/products/fe/model/training_img.ipynb>), [image-design.tex](<D:/nckh-flood-rescue/nckh2/report/chapters/02-data-methods/sections/image-design.tex>). Bảng 3.6 và phần lời của báo cáo đã ghi đúng scheduler.
- **Sửa:** dùng số đếm chính xác; thay scheduler; đưa Accuracy/F1 xuống ô kết quả test. Dòng `Seed 42` cần chú thích là seed của split lịch sử nếu có bằng chứng, không để người đọc hiểu đó là seed huấn luyện của model 1024; notebook hiện đặt seed 599 và đọc lại split dùng chung nên không thể dùng riêng notebook hiện tại để khẳng định seed tạo split.
- **Nguồn hình:** [flow_09_ai_training_optimization.drawio](<D:/nckh-flood-rescue/nckh2/report/assets/diagrams/flow_09_ai_training_optimization.drawio>).

## 3. Sơ đồ mô tả nhiều chức năng cho đội cứu hộ mà app chưa có

- **Vị trí:** Hình 2.1 trang 14 (PDF 36), Hình 2.7–2.8 trang 21–22 (PDF 43–44).
- **Báo cáo ghi:** tiếp nhận nhiệm vụ cứu nạn, danh sách ca/lộ trình/bản đồ; cập nhật tiến độ hiện trường; báo cáo kết quả/xin chi viện; tra cứu điểm trú và bản đồ vùng an toàn; hình tổng thể còn nhắc vị trí đội cứu hộ.
- **Mã thực tế:** app có các màn hình Home, Compose, History, Submitted, Guide, Settings và xác thực tài khoản cục bộ. Không có phân hệ tài khoản đội cứu hộ, danh sách nhiệm vụ được giao, lộ trình, bản đồ vùng trú an toàn, hay màn hình xin chi viện. Guide là nội dung hướng dẫn và số liên hệ. Đổi trạng thái và giao đội thực hiện tại dashboard có quyền.
- **Căn cứ:** [main_navigation_screen.dart](<D:/nckh-flood-rescue/nckh2/products/fe/app/lib/presentation/screens/main_navigation_screen.dart>), [main.py:653](<D:/nckh-flood-rescue/nckh2/products/be/main.py:653>), [main.py:699](<D:/nckh-flood-rescue/nckh2/products/be/main.py:699>).
- **Sửa:** bỏ các use case chưa triển khai hoặc đánh dấu rõ là hướng phát triển. Việc một người thuộc đội cứu hộ dùng app để gửi báo cáo không chứng minh app có phân hệ tác nghiệp cho đội.

## 4. Hình 2.15 gán non_flood khi không có ảnh là sai

- **Vị trí:** trang 30 (PDF 52), Hình 2.15.
- **Báo cáo ghi:** “Không có ảnh: Gán nhãn non_flood mặc định”.
- **Mã thực tế:** `generateAiTags` trả danh sách rỗng khi label hoặc confidence null; `RescueRecord` mặc định `aiTags=[]`, nhãn nullable. Adapter trả F=None khi không có nhãn, không tự gán F=0.
- **Căn cứ:** [inference_local_datasource_native.dart:389](<D:/nckh-flood-rescue/nckh2/products/fe/app/lib/data/datasources/inference_local_datasource_native.dart:389>), [cluster_service.py:114](<D:/nckh-flood-rescue/nckh2/products/be/cluster_service.py:114>).
- **Sửa:** “Không có ảnh hoặc AI chưa có kết quả: không tạo nhãn AI; mức ngập chưa quan sát”. Sai khác này ảnh hưởng trực tiếp đến nguyên tắc phân biệt thiếu dữ liệu với giá trị bằng không.

## 5. Hình SOS gán urgency=1.0 và đo probe không khớp luồng thật

- **Vị trí:** trang 29 (PDF 51), Hình 2.14; đối chiếu thêm Hình 2.2.
- **Báo cáo ghi:** RescueRecord có `urgency: 1.0`, lấy GPS rồi mới lưu, sau đó đo `/probe`.
- **Mã thực tế:** SOS không gán urgencyScore hay trường `urgency`; payload E_i là null. Backend suy mức 0,9 từ mô tả “CỨU HỘ KHẨN CẤP ...”. Bản ghi được lưu **trước** thao tác lấy GPS để tránh mất yêu cầu. SOS không có ảnh nên chính sách trả textOnly khi có kết nối, bỏ qua throughput probe.
- **Căn cứ:** [send_sos_usecase.dart:42](<D:/nckh-flood-rescue/nckh2/products/fe/app/lib/domain/usecases/send_sos_usecase.dart:42>), [adaptive_send_policy.dart:24](<D:/nckh-flood-rescue/nckh2/products/fe/app/lib/domain/services/adaptive_send_policy.dart:24>), [app_controller.dart:626](<D:/nckh-flood-rescue/nckh2/products/fe/app/lib/presentation/controllers/app_controller.dart:626>), [cluster_service.py](<D:/nckh-flood-rescue/nckh2/products/be/cluster_service.py>).
- **Sửa:** vẽ lưu yêu cầu trước GPS; bỏ `urgency:1.0`; tách kiểm tra có kết nối khỏi đo throughput, chỉ probe khi cần chọn chế độ ảnh.

## 6. Hình Docker ghi sai công nghệ dashboard và volume/path

- **Vị trí:** trang 31 (PDF 53), Hình 2.16.
- **Báo cáo ghi:** React + Leaflet SPA; hai volume `sqlite_data`, `uploads_data`; DB `/app/data/rescue.db`, ảnh `/app/uploads/`.
- **Mã thực tế:** dashboard là HTML/CSS/ES modules + Leaflet. Compose có ba service `be`, `dashboard`, `fe`, dùng **một volume `be-data:/var/lib/rescue`**. DB là `/var/lib/rescue/rescue_reports.db`, ảnh `/var/lib/rescue/uploads`, backup `/var/lib/rescue/backups`.
- **Căn cứ:** [docker-compose.yml](<D:/nckh-flood-rescue/nckh2/docker-compose.yml>), [Dockerfile](<D:/nckh-flood-rescue/nckh2/products/docker/be/Dockerfile>), [dashboard.html](<D:/nckh-flood-rescue/nckh2/products/be/templates/dashboard.html>).
- **Sửa:** thay React bằng HTML/JavaScript ES modules; cập nhật service, volume và đường dẫn thật. Các tên `rescue-backend`… nếu giữ chỉ nên ghi là tên thành phần minh họa, không phải tên container đã cấu hình.

## 7. Mô tả cả ONNX/PTE đóng sẵn trong app không còn đúng

- **Vị trí:** mục 2.6.2 trang 31–32 (PDF 53–54); mục 4.1.3 trang 74 (PDF 96) cũng nói đóng gói `model.onnx` và `model.pte`.
- **Mã hiện tại:** APK khai báo asset PTE, manifest và JSON LR. **ONNX được tải bởi admin đã xác thực**, kiểm tra hash ghép cặp với PTE; bản user không có quyền so sánh. PTE là runtime mặc định.
- **Căn cứ:** [pubspec.yaml:42](<D:/nckh-flood-rescue/nckh2/products/fe/app/pubspec.yaml:42>), [admin_model_download_native.dart:69](<D:/nckh-flood-rescue/nckh2/products/fe/app/lib/data/datasources/admin_model_download_native.dart:69>), [inference_local_datasource_native.dart:94](<D:/nckh-flood-rescue/nckh2/products/fe/app/lib/data/datasources/inference_local_datasource_native.dart:94>).
- **Sửa:** mô tả riêng đóng gói hiện tại và phiên APK benchmark lịch sử. APK benchmark từng có hai model không có nghĩa APK hiện tại vẫn đóng cả hai.

## 8. Đoạn cho phép điều phối viên chỉnh trọng số chưa có hiện thực

- **Vị trí:** mục 2.1.6 trang 19 (PDF 41).
- **Báo cáo ghi:** điều phối viên can thiệp trực tiếp để hiệu chỉnh các trọng số trong quá trình vận hành.
- **Mã thực tế:** `DEFAULT_GRAPH_CONFIG` và `PriorityPolicyV2` chứa hằng số trong mã. API/dashboard không có chức năng sửa trọng số hoặc ánh xạ nhãn. `/api/clusters` chỉ trả kết quả/cấu hình hiện có.
- **Căn cứ:** [cluster_service.py:37](<D:/nckh-flood-rescue/nckh2/products/be/cluster_service.py:37>), [priority.py:28](<D:/nckh-flood-rescue/nckh2/products/be/rescue_core/priority.py:28>), [main.py:620](<D:/nckh-flood-rescue/nckh2/products/be/main.py:620>).
- **Sửa:** “Các trọng số hiện được cấu hình trong mã nguồn; chưa cung cấp chức năng hiệu chỉnh tại dashboard”.

## 9. Gắn nhãn dữ liệu mô phỏng chưa bảo đảm không ảnh hưởng dữ liệu thật

- **Vị trí:** cuối mục 2.1.1 trang 14 (PDF 36).
- **Báo cáo ghi:** gắn cờ mô phỏng “đảm bảo ... không ảnh hưởng đến các yêu cầu cứu hộ thực tế”.
- **Mã thực tế:** seed gắn `source=synthetic`, dashboard hiển thị cảnh báo, nhưng phân cụm lấy mọi báo cáo chưa resolved/cancelled, không lọc synthetic; KPI cũng đếm chung các báo cáo trong state. Không có cơ chế phân vùng dữ liệu theo nguồn trong lõi này.
- **Căn cứ:** [seed_demo.py:41](<D:/nckh-flood-rescue/nckh2/products/be/seed_demo.py:41>), [cluster_service.py:189](<D:/nckh-flood-rescue/nckh2/products/be/cluster_service.py:189>), [main.js:266](<D:/nckh-flood-rescue/nckh2/products/be/static/js/main.js:266>).
- **Sửa:** chỉ khẳng định phân biệt nhãn hiển thị; muốn khẳng định không ảnh hưởng phải dùng DB/instance thử nghiệm riêng hoặc có bộ lọc cách ly đã được kiểm tra.

## 10. Giao đội không tự đổi trạng thái sang dispatched

- **Vị trí:** Hình 2.2, 2.18, 2.19, trang 14, 34–35 (PDF 36, 56–57).
- **Báo cáo ghi:** `PUT /api/reports/{id}/team` hoặc `assign_team` làm status thành dispatched và tăng statusVersion.
- **Mã thực tế:** `assign_team` chỉ đổi `assigned_team_id`, `updated_seq` và ghi event. Đổi status/version là thao tác khác qua PATCH status hoặc bulk-status; dashboard có thể gửi kèm teamId trong chính thao tác đổi trạng thái.
- **Căn cứ:** [storage.py:869](<D:/nckh-flood-rescue/nckh2/products/be/storage.py:869>), [actions.js:67](<D:/nckh-flood-rescue/nckh2/products/be/static/js/actions.js:67>).
- **Sửa:** phân biệt “gán đội” với “xác nhận điều phối”. Nếu vẽ một bước kết hợp, ghi đúng API đổi trạng thái có kèm teamId.
- **Chi tiết bổ sung:** hình máy trạng thái chỉ vẽ processing→dispatched→resolved. Code kiểm tra thứ tự tăng và còn cho phép processing→resolved, hoặc cùng status với version cao hơn. Nếu mô tả hình là toàn bộ chuyển hợp lệ thì thiếu; nếu là quy trình chính thì cần ghi rõ giới hạn đó. Xem [storage.py:779](<D:/nckh-flood-rescue/nckh2/products/be/storage.py:779>).

## 11. Hình theo dõi hứa hiển thị thông tin đội/lý do hủy mà app chưa nhận

- **Vị trí:** Hình 2.10 trang 24 (PDF 46); Hình 2.7 trang 21 nhắc vị trí đội.
- **Báo cáo ghi:** dispatched hiển thị tên đội/liên hệ, cancelled hiển thị lý do hủy; request dùng `report_ids`.
- **Mã thực tế:** endpoint nhận query **`ids`**, trả `id`, `status`, `statusVersion`. Flutter chuyển phản hồi thành map ID→status; RescueRecord không giữ thông tin đội hay closeReason. StatusTracker hiển thị thông báo đóng chung, không có lý do cụ thể.
- **Căn cứ:** [storage.py:588](<D:/nckh-flood-rescue/nckh2/products/be/storage.py:588>), [sync_remote_datasource.dart:44](<D:/nckh-flood-rescue/nckh2/products/fe/app/lib/data/datasources/sync_remote_datasource.dart:44>), [status_tracker.dart](<D:/nckh-flood-rescue/nckh2/products/fe/app/lib/presentation/widgets/status_tracker.dart>).
- **Sửa:** giới hạn hiện tại là hiển thị trạng thái nghiệp vụ; đổi tên query thành `ids`; đưa tên đội, liên hệ, vị trí và lý do cụ thể sang phần phát triển nếu chưa triển khai.

## 12. Hình 2.12 gom sai mã HTTP, ACK và các kênh tiếp nhận

- **Vị trí:** trang 26 (PDF 48), Hình 2.12.
- **Báo cáo ghi:** xung đột ID/sequence trả HTTP 409; vượt kích thước trả HTTP 400; đầu vào Sync/Multipart/SMS đều qua header hợp đồng và cùng quy trình dedup; phản hồi thành công accepted/201.
- **Mã thực tế:** `/sync/messages` trả HTTP 200 với `results` từng message; xung đột ID/sequence là ACK `rejected` trong batch. Request quá 256 KiB trả **413**. Multipart trả 201 và kiểm tra quyền gộp report riêng. SMS dùng **token gateway**, không yêu cầu header hợp đồng v1 và không đi qua bảng messages_dedup theo cách JSON sync.
- **Căn cứ:** [main.py:322](<D:/nckh-flood-rescue/nckh2/products/be/main.py:322>), [storage.py:1222](<D:/nckh-flood-rescue/nckh2/products/be/storage.py:1222>), [main.py:374](<D:/nckh-flood-rescue/nckh2/products/be/main.py:374>).
- **Sửa:** tách ba đường tiếp nhận trước khi nhập chung bước lưu/gộp. Ghi rõ HTTP của cả request và ACK cấp message. Giới hạn 256 KiB áp cho sync JSON, không áp cho request multipart có ảnh 15 MiB.

## 13. “Cạnh tối đa 1.024 pixel” không đúng tham số nén thực tế

- **Vị trí:** mục 2.6.3 trang 32 (PDF 54), Hình 2.17 trang 33 (PDF 55).
- **Báo cáo ghi:** max side 1.024 px.
- **Mã thực tế:** truyền `minWidth=1024`, `minHeight=1024` vào flutter_image_compress. Mã Android của dependency đã cài dùng `scale=max(1,min(w/1024,h/1024))`, nên ảnh đủ lớn được giảm **cạnh ngắn** về 1024; cạnh dài có thể lớn hơn 1024. Ví dụ 4000×3000 thành khoảng 1365×1024. Runner mạng yếu dùng cùng quy tắc cạnh ngắn.
- **Căn cứ:** [sender_remote_datasource.dart:152](<D:/nckh-flood-rescue/nckh2/products/fe/app/lib/data/datasources/sender_remote_datasource.dart:152>), [weak_network.py:164](<D:/nckh-flood-rescue/nckh2/products/be/experiments/weak_network.py:164>). Phần thiết lập mạng yếu trong báo cáo đã mô tả đúng cạnh ngắn.
- **Sửa:** thống nhất “JPEG quality 60; tham số kích thước tối thiểu 1024×1024 theo plugin; ảnh đủ lớn giảm cạnh ngắn về 1024, không phóng to ảnh nhỏ”. Không suy từ tên biến `maxSide` rằng cạnh dài bị chặn.

## 14. LR không dùng đặc trưng nhân khẩu

- **Vị trí:** mục 2.6.2 trang 32 (PDF 54); Kết luận trang 105 (PDF 127).
- **Báo cáo ghi:** “năm đặc trưng nhân khẩu”; kết luận nói LR dựa trên “đặc trưng nhân khẩu và dấu hiệu lâm sàng”.
- **Mã thực tế:** năm đầu vào là không phản ứng, khó thở/tím tái, chảy máu nhiều, co giật, chấn thương nguy cơ cao. Không có tuổi, giới, số người, nhóm yếu thế hay nhân khẩu trong vector LR.
- **Căn cứ:** [urgency_logistic_model.dart:6](<D:/nckh-flood-rescue/nckh2/products/fe/app/lib/domain/services/urgency_logistic_model.dart:6>), [urgency_logistic.json](<D:/nckh-flood-rescue/nckh2/products/fe/app/assets/models/urgency_logistic.json>).
- **Sửa:** “năm cờ dấu hiệu nguy cấp có cấu trúc”. Cụm “hỗ trợ đắc lực ... tại hiện trường” cũng nên hạ thành chức năng tính điểm kỹ thuật; chưa có đánh giá thực địa chứng minh hiệu quả đó.

## 15. Chu kỳ polling 15 giây trên hình thiếu điều kiện

- **Vị trí:** Hình 2.3, 2.10, 2.14, 2.17: trang 16, 24, 29, 33 (PDF 38, 46, 51, 55).
- **Báo cáo ghi:** timer/polling 15 giây như một chu kỳ chung sau gửi.
- **Mã thực tế:** khi đang xem màn theo dõi thì 15 giây; các màn khác 60 giây; dừng khi app không ở foreground, mất kết nối, hoặc không còn báo cáo cần theo dõi. Đây là timer có điều kiện, không phải cam kết luôn polling mỗi 15 giây.
- **Căn cứ:** [app_controller.dart:438](<D:/nckh-flood-rescue/nckh2/products/fe/app/lib/presentation/controllers/app_controller.dart:438>), [main_navigation_screen.dart:41](<D:/nckh-flood-rescue/nckh2/products/fe/app/lib/presentation/screens/main_navigation_screen.dart:41>).
- **Sửa:** chú thích đủ điều kiện; tách polling foreground khỏi worker nền khoảng 15 phút.

## 16. Hình tiếp nhận thủ công ghi sai field/source

- **Vị trí:** Hình 2.20 trang 37 (PDF 59).
- **Báo cáo ghi:** nhập tên, địa chỉ; `source='manual'`; ghi `operator_id` thực hiện.
- **Mã thực tế:** schema ManualReport có description, contactPhone, lat/lng, counts và vulnerableGroups; không có field tên hay địa chỉ/geocoding riêng. Payload có `source='hotline'`, `sendMode='hotline'`; event ghi `source='dashboard'`, `actor` là tên điều phối viên. `manual` là `location_source` khi có tọa độ, không phải source của báo cáo. `report_events` không có cột operator_id.
- **Căn cứ:** [main.py:579](<D:/nckh-flood-rescue/nckh2/products/be/main.py:579>), [sms_intake.py](<D:/nckh-flood-rescue/nckh2/products/be/sms_intake.py>), [actions.js:154](<D:/nckh-flood-rescue/nckh2/products/be/static/js/actions.js:154>).
- **Sửa:** dùng đúng field, tách source của payload/event/vị trí. Tên hoặc địa chỉ nếu cần chỉ có thể đưa vào mô tả; không vẽ như các trường đã có chức năng tự định vị.

## 17. ERD gọi raw_payload là Canonical RFC 8785 chưa đúng cách lưu

- **Vị trí:** Hình 2.5 trang 19 (PDF 41).
- **Báo cáo ghi:** `raw_payload TEXT NOT NULL (Canonical RFC 8785)`; send_mode chú thích HTTP/Sync/SMS.
- **Mã thực tế:** raw_payload lưu bằng `json.dumps(meta, ensure_ascii=False)` rồi gộp dictionary; không phải chuỗi JCS chuẩn tắc. JCS được dùng ở bước tính hash payload của sync. send_mode là fullImage, compressedImage, textOnly, smsFallback, hotline, synthetic…; app/sync/dashboard là nguồn thao tác, không phải toàn bộ miền send_mode.
- **Căn cứ:** [storage.py:503](<D:/nckh-flood-rescue/nckh2/products/be/storage.py:503>), [rescue_record_payload.dart](<D:/nckh-flood-rescue/nckh2/products/fe/app/lib/data/models/rescue_record_payload.dart>), [sms_intake.py](<D:/nckh-flood-rescue/nckh2/products/be/sms_intake.py>).
- **Sửa:** “JSON payload gốc/đã gộp”; mô tả riêng canonicalization khi hash, và dùng đúng các chế độ gửi.

## 18. Phụ lục mô tả nguồn sơ đồ là TikZ chưa đầy đủ

- **Vị trí:** A.4 trang 111 (PDF 133).
- **Báo cáo ghi:** các sơ đồ kiến trúc/nghiệp vụ được viết bằng TikZ trong nguồn chương.
- **Thực tế:** nhiều sơ đồ hiện được lưu bằng `.drawio`, xuất PDF, rồi nhúng bằng includegraphics; chỉ một số sơ đồ/công thức minh họa dùng TikZ trực tiếp.
- **Căn cứ:** [reproducibility.tex:39](<D:/nckh-flood-rescue/nckh2/report/appendices/reproducibility.tex:39>), [generate_drawio_diagrams.py](<D:/nckh-flood-rescue/nckh2/report/scripts/generate_drawio_diagrams.py>), [architecture.tex](<D:/nckh-flood-rescue/nckh2/report/chapters/03-system/sections/architecture.tex>).
- **Sửa:** bổ sung nguồn Draw.io và quy trình export. Khi chỉnh hình phải chỉnh cả file nguồn và script sinh tương ứng nếu script còn được dùng, tránh lần sinh sau đưa lỗi cũ trở lại.

## 19. Tên endpoint trên Hình 2.1 dùng đường dẫn không tồn tại

- **Vị trí:** trang 14 (PDF 36), Hình 2.1.
- **Báo cáo ghi:** `POST /sync, /reports`, `GET /reports/status`, polling `/changes, /clusters`.
- **Mã thực tế:** `/sync/messages`, `/api/reports`, `/api/reports/status`, `/api/reports/changes`, `/api/clusters`.
- **Căn cứ:** [main.py:238](<D:/nckh-flood-rescue/nckh2/products/be/main.py:238>), [main.py:322](<D:/nckh-flood-rescue/nckh2/products/be/main.py:322>), [main.py:597](<D:/nckh-flood-rescue/nckh2/products/be/main.py:597>).
- **Sửa:** ghi đầy đủ đường dẫn, hoặc ghi rõ đây là tên chức năng rút gọn và bỏ cú pháp HTTP khiến người đọc hiểu là endpoint thật.

## Những điểm tích hợp cần lưu ý, không tính thành lỗi báo cáo mới

1. **E_i từ LR chưa vào thuật toán backend:** đúng là app gửi E_i nhưng adapter chỉ đọc urgency/từ khóa. Báo cáo đã nêu rõ tại mục 3.4.1, 4.2.7 và 4.4.2; không nên báo lại như phát hiện chưa được công bố. Cần giữ hạn chế này khi sửa sơ đồ/kết luận.
2. **Model bàn giao/app và backend mặc định chưa đồng bộ:** manifest PTE đóng trong app khớp bản cắt tỉa seed1024; model_assets.py và Dockerfile backend mặc định lấy seed159. Cả hash ONNX lẫn PTE đều khác. Code tải ONNX của admin yêu cầu ghép đúng hash với PTE nên cấu hình mặc định này sẽ bị từ chối bởi bước kiểm tra, trừ khi cấu hình/đóng gói lại model server. Đây là khoảng trống triển khai cần phản ánh bên cạnh mô tả lựa chọn seed1024; không phải bằng chứng phép benchmark lịch sử sai. Báo cáo đã thận trọng nói kết luận lựa chọn không xác nhận APK hiện tại.
3. **Tiền xử lý CPU và app không đồng nhất theo từng pixel:** CPU dùng Pillow bilinear/ImageOps.pad; Flutter dùng Canvas với FilterQuality.high và kích thước đích số thực. Không nên mô tả toàn bộ đường mobile là Pillow bilinear hoặc tuyên bố parity tensor đã được chứng minh. Báo cáo hiện đã lưu ý giới hạn parity; nên giữ ranh giới này.
4. **“Có ảnh” trong Q_i cần định nghĩa theo đường truyền:** app gửi `image_attached`, còn adapter kiểm tra `imageUrl` hoặc `has_image`. Với metadata-only trước khi ảnh đến, Q_i có thể không xem là có ảnh dù thiết bị đã phân tích ảnh. Báo cáo chưa cần đổi công thức, nhưng nên ghi rõ Q_i dựa trên thông tin backend thực nhận, khác confidence tại thiết bị.
5. **Công thức E_bar với dữ liệu thiếu:** mã chỉ cộng các report có E quan sát vào cả tử và mẫu; công thức ở mục 3.4.8 nên ghi rõ tập chỉ số quan sát E, tránh để E=null xuất hiện trong max hoặc hiểu nhầm report thiếu E vẫn góp vào mẫu số.
6. **Case 8 run_001:** JSON gốc FAIL, báo cáo dùng xác nhận bổ sung để ghi PASS có chú thích và vẫn công bố lỗi thoát app. Đây là khác biệt đã được giải thích minh bạch, không phải một kết quả chạy lại; không tự đổi thành “hai run không có lỗi”.

## Số liệu đã đối chiếu và chưa thấy lệch

- **Bộ ảnh:** kiểm tra 1.702 file ảnh/MD5 và nhóm chia tập; 1.189/257/256. Tổng 80 gold run là **26.288 báo cáo**.
- **Các bảng chính:** chạy lại bộ xuất kết quả vào thư mục riêng; 14 bảng sinh ra giống bảng đang dùng. Bộ kiểm tra báo **0 sai khác summary–CSV dự đoán** trong các nguồn hiện chọn.
- **FP32 seed1024:** Accuracy 75,78%, macro-F1 74,26%, 3 lỗi nặng; ma trận nhầm lẫn có 194/256 đúng.
- **PTQ/QAT seed1024:** Accuracy 66,80% / 46,48%; QAT macro-F1 42,91%, 45 lỗi nặng. Không áp lại các cảnh báo lệch metric của seed42 lịch sử cho các artifact này.
- **Cắt tỉa seed1024:** 4.207.156 → 4.145.694 tham số, giảm 1,46%; Accuracy CPU 80,08%, F1 78,26%, 4 lỗi nặng. Số điện thoại có thể khác CPU vì phiên/pipeline, báo cáo đã phân biệt.
- **Benchmark điện thoại:** kiểm tra lại 32 JSON, 8.192 dự đoán và 128 hàng chỉ số lớp; không thiếu cấu hình. Ba bảng chính và bốn bảng phụ lục sinh lại khớp bảng hiện có.
- **RQ1/RQ2/RQ3:** các bảng được xuất lại từ CSV nguồn và khớp bảng hiện có, gồm ARI Product 0,9072 / Additive 0,9191 và tương phản RQ3 theo 40 seed. Đây là kiểm tra artifact, không chạy lại notebook mô phỏng.
- **Mạng yếu:** CSV có 2.313 lượt; từng nhóm có 257 lượt. Ảnh gốc thành công 230/257, 255/257, 256/257 ở 2G/3G/4G; metadata và ảnh nén đều 257/257; 27 NETWORK_ERROR và 3 UNSUPPORTED_IMAGE, khớp báo cáo.

## Phạm vi và giới hạn của lần rà soát

Đã trích xuất toàn bộ PDF (bao gồm phần đầu, chương, phụ lục, minh chứng, bản tin và tóm tắt), đọc các phần kỹ thuật và đối chiếu những khẳng định có thể kiểm chứng với mã/config/artifact; xem bản render của các hình trọng điểm. Không sửa PDF, TeX, mã sản phẩm hay artifact gốc. Các đầu ra kiểm tra nằm riêng trong `report/audit/`.

Không huấn luyện/suy luận lại mô hình, chạy lại notebook Colab, Docker E2E, Android hoặc SMS; không xác nhận độc lập thông tin hành chính, tình trạng công bố, giấy phép ảnh hay nguồn khoa học bên ngoài. Vì vậy “khớp số liệu” ở đây là khớp các bằng chứng đã lưu, không phải bảo đảm tái lập toàn bộ kết quả từ đầu hay hệ thống đã vận hành đúng ngoài thực địa.
