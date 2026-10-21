# Giải đáp thắc mắc về phần thực nghiệm

## 1. Thực nghiệm trên web và app di động có khác nhau không?

**Trả lời:** Có khác nhau.

- Bản **web** và bản **di động** dùng chung phần lớn mã Flutter và cùng gọi backend, nên có thể dùng bản web để kiểm tra luồng nghiệp vụ: gửi SOS, gửi báo cáo có ảnh, lưu hàng đợi khi mất mạng, đồng bộ lại, phân cụm và điều phối trên dashboard.
- Bản **web không kiểm tra được** các chức năng chỉ có trên Android: AI chạy trực tiếp trên thiết bị bằng ONNX/ExecuTorch, camera thật, quyền hệ thống, Workmanager chạy nền, gửi SMS qua SIM và hành vi trên mạng di động thật.
- Thực nghiệm end-to-end hiện có trong repo chạy bằng Chromium và chỉ chứng minh luồng **web → backend → dashboard**. Tài liệu cũ ghi kết quả 46/46; chưa có bằng chứng chạy end-to-end trên điện thoại Android thật.

Vì vậy, kết quả web và kết quả di động phải báo cáo riêng. Kết quả web không thay thế cho kiểm thử Android.

## 2. Thực nghiệm với dataset giả lập và khảo sát người dùng có phải là hai thực nghiệm khác nhau không? Khác nhau thế nào và tổng hợp kết quả ra sao?

**Trả lời:** Đây là hai loại thực nghiệm khác nhau.

### Thực nghiệm bằng dữ liệu giả lập

- Đối tượng đánh giá là **thuật toán hoặc hệ thống**.
- Đầu vào được kiểm soát, ví dụ 80 run bán tổng hợp trong `thucnghiem/data/gold`.
- Kết quả là các số đo khách quan như độ chính xác phân cụm, sai lệch xếp hạng, kết quả điều phối, tỷ lệ gửi thành công hoặc độ trễ.
- Có thể chạy lặp lại với cùng dữ liệu và cấu hình.

### Khảo sát người dùng

- Đối tượng đánh giá là **trải nghiệm của con người khi sử dụng ứng dụng**.
- Cần người tham gia, kịch bản thao tác và bảng câu hỏi.
- Có thể đo thời gian hoàn thành nhiệm vụ, tỷ lệ thao tác thành công, số lỗi, mức dễ sử dụng, mức hài lòng và ý kiến định tính.
- Kết quả phụ thuộc vào nhóm người tham gia và thiết kế khảo sát.

Repo hiện tại **chưa có** bảng câu hỏi, dữ liệu người tham gia hoặc kết quả khảo sát người dùng. Vì vậy chưa thể ghi rằng nghiên cứu đã thực hiện khảo sát.

### Cách tổng hợp trong báo cáo

Không cộng hoặc lấy trung bình hai loại kết quả. Nên tách thành các mục:

1. Đánh giá thuật toán/mô hình trên dataset.
2. Đánh giá hiệu năng mạng yếu.
3. Kiểm thử end-to-end của hệ thống.
4. Đánh giá người dùng, nếu sau này thực hiện khảo sát.

Phần thảo luận cuối cùng mới đối chiếu các kết quả: hệ thống có đúng về kỹ thuật hay không và người dùng có sử dụng thuận tiện hay không.

## 3. Thực nghiệm mạng yếu là gì? Xây dựng và đánh giá như thế nào?

**Trả lời:** Đây là thực nghiệm kiểm tra khả năng gửi báo cáo khi băng thông thấp và độ trễ cao. Nó không đánh giá độ chính xác của mô hình AI.

File `products/be/experiments/weak_network.py` tạo proxy TCP cục bộ để giả lập ba loại mạng:

| Cấu hình | Băng thông | RTT |
|---|---:|---:|
| 2G (EDGE) | 50 kbit/s | 600 ms |
| 3G | 400 kbit/s | 200 ms |
| 4G | 5.000 kbit/s | 50 ms |

Mỗi cấu hình mạng thử ba chế độ gửi:

1. `metadata`: chỉ gửi thông tin dạng JSON, không gửi ảnh.
2. `compressed`: gửi ảnh đã nén giống cấu hình của app, cạnh ngắn 1.024 px và JPEG quality 60.
3. `original`: gửi ảnh gốc.

Mặc định mỗi cặp mạng × chế độ chạy 20 lượt, tức 3 × 3 × 20 = 180 lượt gửi. Ảnh được chọn từ `products/fe/model/Dataset_Flood`; nội dung báo cáo và GPS là dữ liệu cố định được viết trong script.

### Kết quả sinh ra

- `weak_network.csv`: dữ liệu thô của từng lượt gửi.
- `weak_network.md`: bảng tổng hợp.

### Chỉ số đánh giá

| Chỉ số | Ý nghĩa |
|---|---|
| Tỷ lệ/số lượt gửi thành công | Request nhận HTTP 2xx và hoàn thành trong timeout của app. |
| Độ trễ trung vị | Thời gian điển hình của các lượt gửi thành công. Trung vị ít bị ảnh hưởng bởi giá trị quá lớn. |
| Độ trễ p95 | 95% lượt thành công có độ trễ không vượt quá giá trị này; phản ánh các trường hợp chậm. |
| Số byte cần gửi | So sánh chi phí truyền của metadata, ảnh nén và ảnh gốc. |
| HTTP status | Phân biệt request thành công với request lỗi hoặc bị ngắt. |

Timeout được lấy theo hành vi của ứng dụng: 30 giây cho metadata và 60 giây cho upload ảnh. Đây là căn cứ kỹ thuật trực tiếp để định nghĩa một lượt thành công.

**Giới hạn về căn cứ:** các con số 50/400/5.000 kbit/s và RTT 600/200/50 ms đang được ghi cứng trong script, nhưng repo chưa dẫn tài liệu hoặc phép đo thực tế làm nguồn cho các cấu hình này. Trong báo cáo hiện tại chỉ nên gọi đây là **các cấu hình mạng giả lập do nhóm lựa chọn**. Nếu muốn gọi là cấu hình 2G/3G/4G đại diện, cần bổ sung nguồn tham khảo hoặc đo trên mạng thật.

### 3.1. Tool đánh giá mạng yếu cần gì?

Không chỉ cần viết code. Để chạy thực nghiệm hiện tại cần:

- Backend đang chạy, nên dùng database và thư mục upload riêng.
- Python cùng các thư viện trong `products/be/experiments/requirements.txt`.
- Script `products/be/experiments/weak_network.py`.
- Ảnh trong `products/fe/model/Dataset_Flood`; script yêu cầu đủ ảnh JPEG có cạnh dài từ 1.600 px.
- Cấu hình mạng, số lượt chạy và timeout được khóa trước khi chạy.
- Ghi lại môi trường máy, phiên bản source và thời điểm chạy để kết quả có thể kiểm tra lại.

Script Python gửi request giống app nên không cần mở Flutter. Tuy nhiên, kết quả này chỉ là giả lập trên máy tính, không chứng minh hiệu năng trên điện thoại hoặc mạng di động thật.

## 4. Thực nghiệm end-to-end là gì? Xây dựng như thế nào?

**Trả lời:** End-to-end kiểm tra một luồng hoàn chỉnh từ giao diện người dùng đến kết quả cuối cùng, thay vì kiểm tra từng hàm riêng lẻ.

File `products/scripts/demo/e2e/e2e_system.py` dùng Playwright điều khiển Chromium và kiểm tra chuỗi:

1. Người dùng mở app web.
2. Gửi SOS hoặc báo cáo có ảnh.
3. Backend nhận, lưu và phân cụm báo cáo.
4. Dashboard đăng nhập, hiển thị bản đồ/cụm và thực hiện điều phối.
5. Trạng thái điều phối được trả về app.
6. Khi mất mạng, báo cáo nằm trong hàng đợi và tự đồng bộ khi có mạng lại.
7. App chọn ảnh gốc, ảnh nén hoặc chỉ gửi thông tin theo băng thông.
8. Báo cáo thiếu GPS được đưa vào hàng xem xét thủ công.

Để chạy, cần app web, backend và dashboard cùng hoạt động. Có thể dùng Docker hoặc tự chạy ba thành phần riêng rồi truyền URL cho script.

### 4.1. Kết quả và tiêu chí đánh giá end-to-end

Script trả từng kiểm tra dưới dạng:

- `PASS`: chức năng cho kết quả mong đợi.
- `FAIL`: chức năng sai; script kết thúc với mã lỗi.
- `CHƯA CÓ`: tính năng được ghi nhận là chưa triển khai nhưng không làm toàn bộ bài kiểm tra thất bại.

Các tiêu chí chính gồm:

- API yêu cầu đăng nhập đúng chỗ.
- Dashboard hiển thị cụm, bản đồ, chi tiết và lịch sử thao tác.
- SOS và báo cáo có ảnh tới được server.
- GPS, thời gian tạo, nội dung và SHA-256 ảnh được giữ đúng.
- Mất mạng không làm mất báo cáo; khi có mạng lại dữ liệu được đồng bộ và không trùng.
- Báo cáo được phân cụm và trạng thái điều phối quay lại app.
- Gửi thích ứng chọn đúng chế độ ở 300 kbit/s và 20 kbit/s.
- Báo cáo thiếu GPS không bị gắn tọa độ giả.
- App và dashboard không phát sinh lỗi JavaScript chưa xử lý.

Căn cứ của các tiêu chí này là yêu cầu chức năng và hợp đồng kết nối của chính hệ thống, đặc biệt trong `docs/contact_connect.md` và `docs/huong_dan_chay_demo.md`. Repo chưa dẫn một bài báo bên ngoài để định nghĩa bộ chỉ số end-to-end này.

Đây là **kiểm thử chấp nhận chức năng**, nên kết quả chính là số ca PASS/FAIL. Nó chưa phải thực nghiệm hiệu năng vì không thống kê thời gian phản hồi, tải đồng thời hoặc thông lượng.

### 4.2. Tool end-to-end cần gì? Có cần dataset không?

Cần:

- Python và các thư viện trong `products/scripts/demo/e2e/requirements.txt`.
- Playwright cùng Chrome/Chromium.
- App web, backend và dashboard đang chạy.
- Tài khoản dashboard.
- Một ảnh từ `products/fe/model/Dataset_Flood/high`.
- Dữ liệu seed từ `thucnghiem/data/gold/run_001` để dashboard có sẵn các cụm khi demo.

Không cần toàn bộ dataset để kiểm tra luồng gửi một báo cáo. Script dùng một ảnh, còn mô tả và tọa độ được ghi sẵn. Muốn kiểm tra Android thật phải xây dựng thêm bài end-to-end riêng trên emulator/điện thoại vì Playwright hiện chỉ điều khiển bản web.

## 5. Các file thực nghiệm mạng yếu và end-to-end, kết quả hiện có, mức đáp ứng và việc cần sửa

### Thực nghiệm mạng yếu

- File chạy: `products/be/experiments/weak_network.py`.
- Dependency: `products/be/experiments/requirements.txt`.
- Công cụ: Python, `requests`, Pillow và proxy TCP cục bộ.
- Dataset: ảnh trong `products/fe/model/Dataset_Flood`; metadata được ghi sẵn trong script.
- Kết quả hiện có: **chưa có** thư mục `products/be/experiments/results` trong source hiện tại, nên chưa có CSV/bảng độ trễ để đưa vào báo cáo.
- Đã đáp ứng: có thiết kế giả lập 2G/3G/4G, ba chế độ gửi, đo thành công, byte truyền, median và p95.
- Cần làm: chạy thực nghiệm và lưu kết quả; ghi commit/môi trường; bổ sung căn cứ cho profile mạng; tránh để chín nhóm chạy song song làm ảnh hưởng lẫn nhau hoặc phải chứng minh ảnh hưởng này đã được kiểm soát; bổ sung kiểm tra trên điện thoại/mạng thật nếu muốn kết luận về triển khai thực tế. Script cũng dùng `os.getloadavg()`, không phù hợp khi chạy Python trực tiếp trên Windows; nên chạy bằng WSL/Linux hoặc sửa cách đo tải máy.

### Thực nghiệm end-to-end

- File chạy: `products/scripts/demo/e2e/e2e_system.py`.
- Dependency: `products/scripts/demo/e2e/requirements.txt`.
- Công cụ: Python, Playwright và Chromium.
- Dataset: một ảnh từ `Dataset_Flood/high`; có thể dùng `run_001` để seed dashboard; dữ liệu báo cáo kiểm thử được script ghi sẵn.
- Kết quả hiện có: `docs/nghiem-thu/doi_chieu_thuyet_minh.md` ghi lần chạy trước đạt **46/46**, nhưng repo hiện không lưu log thô, JSON kết quả hoặc ảnh chụp của lần chạy đó.
- Đã đáp ứng: kiểm tra khá đầy đủ luồng app web → backend → dashboard, offline/online, ảnh, GPS, phân cụm, điều phối và gửi thích ứng.
- Cần làm: chạy lại trên commit dùng cho báo cáo; lưu log và ảnh chụp bằng tùy chọn `--screenshots`; ghi rõ môi trường; thêm output JSON/JUnit nếu cần tổng hợp tự động; xây dựng bài kiểm tra Android riêng cho AI on-device, Workmanager, camera và SMS.

## 6. Confusion matrix của MobileNetV3 và `urgency_ei` là những đánh giá gì?

Đây là hai đánh giá mô hình khác nhau và nên trình bày thành hai tiểu mục riêng trong báo cáo.

### 6.1. MobileNetV3 và confusion matrix

MobileNetV3-Large phân loại ảnh thành bốn lớp:

- `low`: ngập thấp.
- `medium`: ngập trung bình.
- `high`: ngập cao.
- `non_flood`: không ngập.

Confusion matrix đối chiếu **nhãn thật** với **nhãn mô hình dự đoán**. Các ô trên đường chéo là dự đoán đúng; các ô ngoài đường chéo cho biết mô hình thường nhầm lớp nào với lớp nào. Nó giúp phát hiện trường hợp accuracy tổng thể có vẻ tốt nhưng một lớp cụ thể có recall thấp.

Ba file ZIP trong `products/fe/model/models/Final` chứa kết quả của ba seed trên tập test 256 ảnh:

| Seed | Accuracy | Macro-F1 | Balanced accuracy | Critical error rate |
|---:|---:|---:|---:|---:|
| 42 | 76,17% | 74,54% | 74,07% | 1,95% |
| 159 | 75,78% | 74,09% | 73,67% | 1,56% |
| 1024 | 75,78% | 74,26% | 73,87% | 1,17% |
| **Trung bình** | **75,91%** | **74,30%** | **73,87%** | **1,56%** |

Ý nghĩa các chỉ số:

- **Accuracy:** tỷ lệ ảnh được phân loại đúng.
- **Macro-F1:** tính F1 riêng cho từng lớp rồi lấy trung bình; các lớp có trọng số ngang nhau.
- **Balanced accuracy:** trung bình recall của bốn lớp; phù hợp khi số ảnh mỗi lớp không cân bằng.
- **Critical error rate:** tỷ lệ nhầm nghiêm trọng giữa các mức cách xa nhau theo định nghĩa trong notebook.

Lưu ý: tài liệu nghiệm thu cũ ghi 73,77% accuracy và 72,21% macro-F1 trên 244 ảnh, còn ba ZIP `Final` mới dùng 256 ảnh và cho số liệu ở bảng trên. Báo cáo cuối phải chọn một phiên bản chính và ghi rõ dataset/split/version; không trộn hai bộ số liệu. Số 86,58% trong `products/fe/reports/model_comparison` đo trên toàn bộ dataset có cả ảnh train, chỉ dùng để kiểm tra PyTorch và ONNX tương đương, không dùng làm độ chính xác tổng quát hóa.

### 6.2. `urgency_ei`

`products/fe/model/urgency_ei` là Logistic Regression tạo điểm bằng chứng khẩn cấp `E_i` từ năm dấu hiệu Boolean:

1. Không phản ứng.
2. Khó thở hoặc tím tái.
3. Chảy máu nặng.
4. Co giật đang diễn ra.
5. Chấn thương nguy cơ cao.

Dataset gồm đủ 32 tổ hợp của năm biến Boolean, được tạo theo quy tắc tham chiếu nguồn. Đây là **bảng trạng thái giao thức tổng hợp**, không phải dữ liệu bệnh nhân thật và không có nhãn chuyên gia.

Các audit hiện có kiểm tra:

- Nguồn và ý nghĩa của từng đặc trưng.
- Dataset đủ 32 tổ hợp, không trùng profile.
- Model khớp với luật trực tiếp trên 32/32 profile tại ngưỡng 0,5.
- Mười vòng giữ lại một số profile dương để kiểm tra kỹ thuật khi model gặp tổ hợp chưa huấn luyện.
- Artifact và checksum có nhất quán hay không.

Kết quả này chỉ chứng minh mô hình tái hiện hợp lý một quy tắc đã định nghĩa. Không được gọi là độ chính xác lâm sàng, dự đoán tử vong, hiệu quả điều phối hoặc mô hình đã được WHO/chuyên gia xác nhận. Luật trực tiếp vẫn là baseline chính xác cho nhãn rút gọn, nên không tuyên bố Logistic Regression tốt hơn luật.

### Cách đưa vào báo cáo cuối

Nên chia phần thực nghiệm thành các nhóm độc lập:

1. **Mô hình ảnh:** MobileNetV3, confusion matrix, Accuracy, Macro-F1, Balanced accuracy, recall từng lớp và critical error rate.
2. **Điểm khẩn cấp:** mô tả dataset 32 trạng thái, so sánh Logistic Regression với luật và nêu rõ giới hạn không phải dữ liệu lâm sàng.
3. **Mạng yếu:** tỷ lệ gửi thành công, byte truyền, median và p95.
4. **End-to-end:** số ca chức năng PASS/FAIL và phạm vi web/Android.
5. **Khảo sát người dùng:** chỉ thêm khi đã có người tham gia và dữ liệu khảo sát thật.

## 7. Thực nghiệm mạng yếu và end-to-end trên web có đánh giá đúng không, hay phải chạy trên app di động? Khảo sát 10–20 người bằng APK có đủ không?

**Trả lời:** Kết quả trên web vẫn đúng trong phạm vi của nó, nhưng chưa đủ để kết luận cho ứng dụng di động.

- **End-to-end trên web** đánh giá đúng luồng dùng chung: giao diện Flutter, gửi request, backend lưu dữ liệu, phân cụm, dashboard điều phối, mất mạng và đồng bộ lại trong trình duyệt.
- **Mạng yếu bằng proxy Python/Chrome** đánh giá đúng ảnh hưởng của băng thông, RTT và kích thước payload đối với giao thức gửi hiện tại.
- Hai thực nghiệm trên không đo được đặc tính riêng của điện thoại: hiệu năng CPU/RAM, AI on-device, camera/GPS, quyền Android, Workmanager khi app chạy nền, SMS qua SIM, chuyển đổi Wi-Fi/4G và cơ chế tiết kiệm pin.

Vì đề tài đăng ký **ứng dụng di động** và **hiệu năng trong điều kiện mạng yếu**, nên nên giữ thực nghiệm web hiện có và bổ sung ít nhất:

1. Chạy end-to-end trên một emulator Android để kiểm tra build và luồng phần mềm.
2. Chạy trên ít nhất một điện thoại Android thật để kiểm tra camera, GPS, AI on-device, chạy nền và SMS.
3. Thử ba mức mạng đã khóa trước; với mỗi mức đo số lượt thành công, median, p95 và byte gửi. Nếu không có mạng 2G/3G thật, có thể cho điện thoại đi qua Wi-Fi được giới hạn băng thông và ghi rõ đây vẫn là giả lập.
4. Lưu model máy, phiên bản Android, commit source, cấu hình mạng, số lượt lặp và file kết quả.

### Khảo sát 10–20 người có thay thế được không?

Không. Khảo sát người dùng và thực nghiệm kỹ thuật trả lời hai câu hỏi khác nhau:

- Thực nghiệm kỹ thuật trả lời: app có gửi thành công không, mất bao lâu, có mất/trùng dữ liệu không và chức năng Android có hoạt động không.
- Khảo sát trả lời: người dùng có hiểu giao diện, thao tác được và cảm thấy dễ sử dụng hay không.

Khoảng 10–20 người có thể dùng cho một **khảo sát thăm dò/pilot**, nhưng không nên tuyên bố đại diện cho toàn bộ người dùng. Mỗi người nên thực hiện cùng một số nhiệm vụ, chẳng hạn gửi SOS, gửi báo cáo có ảnh, xử lý khi mất mạng và xem trạng thái cứu hộ. Nên ghi thời gian hoàn thành, tỷ lệ hoàn thành, số lỗi và bảng hỏi mức dễ sử dụng; phản hồi tự do dùng làm dữ liệu định tính.

Phương án phù hợp cho báo cáo cuối là trình bày ba lớp bằng chứng riêng:

1. Web E2E tự động: kiểm tra luồng hệ thống dùng chung.
2. Android/emulator và điện thoại thật: kiểm tra chức năng native và mạng yếu.
3. Khảo sát 10–20 người: đánh giá khả dụng ở mức thăm dò.
