# Đề xuất chạy lại, bổ sung thực nghiệm và hoàn thiện Chương 4

Ngày đánh giá: **19/10/2026**, theo giờ Việt Nam. Đây là ý kiến của tôi dựa trên nội dung báo cáo, bài báo và file kết quả đang có; các số lượt/số máy/số ảnh đề nghị dưới đây là thiết kế gợi ý, chưa phải thực nghiệm đã chạy hay ngưỡng đủ để chứng minh hiệu quả thực địa.

Đọc [danh mục thực nghiệm](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/docs_thuc_nghiem/all_experiments.md) để xem mục đích, dữ liệu, runner, kết quả thô và file đánh giá của từng phần. Tài liệu này giúp chọn việc cần làm, không thay cho kết quả chạy.

## 1. Ý kiến chính: chưa cần chạy lại tất cả

Nhóm đã có nhiều kết quả RQ1–RQ3 và mô hình ảnh. Chạy lại toàn bộ các notebook mà không đổi câu hỏi nghiên cứu sẽ tốn công nhưng chưa lấp được những khoảng trống lớn nhất: kết quả hệ thống mới chưa vào báo cáo, hồ sơ đo điện thoại thiếu thông tin, trường khẩn cấp app–backend chưa nối đúng, và dữ liệu kiểm tra độc lập còn thiếu.

Tôi ưu tiên theo thứ tự:

1. **Giữ và đưa các kết quả đã có vào báo cáo, sửa câu mô tả lỗi thời.** Đây là việc làm ngay, không cần đo lại để có được các số đang tồn tại.
2. **Chốt hồ sơ hai lượt E2E mới và bổ sung phép đo mạng yếu lặp nhiều phiên.** Đây là phần sát mục tiêu phần mềm/gửi thích ứng nhất.
3. **Chạy benchmark Android trên đúng model, đúng APK, có thông tin máy và hash asset.** Việc này trả lời mô hình thực sự chạy thế nào trên sản phẩm.
4. **Kiểm tra điểm khẩn cấp đi từ app tới thuật toán và độ bền hàng đợi khi đóng/mở app.** Đây là các khoảng trống tích hợp.
5. **Bổ sung dữ liệu độc lập và thử cải tiến thuật toán nếu còn nguồn lực.** Giữ nguyên kết quả âm hiện tại, không chạy chỉ để tìm số đẹp hơn.

## 2. Trạng thái cập nhật cần biết trước khi lên kế hoạch

### 2.1. Hai lượt E2E mới đã hoàn tất

Lượt [run_001](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_e2e/results/run_001__e2e-20261019-162957-186810/summary.json) và [run_002](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_e2e/results/run_002__e2e-20261019-170303-022823/summary.json) đều ghi `complete`, đủ năm stage; mỗi lượt có **45 PASS, 0 FAIL, 1 CHƯA CÓ**. Mục CHƯA CÓ là giao diện chưa giải thích trạng thái AI không khả dụng trên web.

Vì vậy, không cần chạy lại chỉ vì nghĩ cả hai lượt vẫn bị lỗi Swagger như lượt trước. Cũng không ghi “46/46 PASS”. Hai lượt dùng cùng một ảnh validation; run_001 seed 316 báo cáo, run_002 seed 334 báo cáo. Đây là hai bối cảnh dữ liệu, không phải 257 ảnh hay 80 run đã được thử qua UI.

**Khoảng trống hồ sơ:** trong lần rà soát, không tìm thấy manifest của hai lượt ở thư mục log chuẩn và không thấy log run_001 tại đó. Cần tìm bản sao và giữ file còn lại; đừng tự tạo manifest lịch sử từ trạng thái mã hôm nay rồi xem là minh chứng gốc. Có thể lập một bản ghi khôi phục riêng, ghi rõ thời điểm và giới hạn thông tin; nếu không truy lại được nguồn chạy thì nên có một lượt xác nhận mới với hồ sơ đầy đủ.

### 2.2. Mạng yếu đã có đủ kết quả một phiên

[weak_network.md](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_weak_network/results/20261005-102040/weak_network.md) và [checkpoint](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_weak_network/checkpoints/20261005-102040.json) ghi đủ 2.313/2.313 lượt; không phải chưa chạy. Chương 4 chưa tích hợp bộ này. Một lượt đo/ảnh/điều kiện đủ để báo cáo phép đo mô tả của phiên đó, nhưng còn yếu nếu muốn nói tốc độ ổn định qua nhiều lần đo hoặc nhiều thời điểm.

### 2.3. Số QAT trong hai đoạn báo cáo đang mâu thuẫn

- Bảng 4.6 và [summary seed 1024](D:/nckh-flood-rescue/nckh2/products/fe/reports/seed1024/fp32_ptq_qat/summary.json): QAT Accuracy **46,48%**; phần 4.2.5 ghi summary khớp CSV.
- Mục 4.3.2 vẫn viết QAT summary **52,34%**, CSV **51,17%**, cần xử lý chênh lệch. Đoạn này có cả trong PDF đang đọc và [limitations.tex](D:/nckh-flood-rescue/nckh2/report/chapters/04-evaluation/sections/limitations.tex).

Không nên chạy lại QAT chỉ để xử lý mâu thuẫn biên soạn này. Trước hết phải chốt nguồn [benchmark-sources.json](D:/nckh-flood-rescue/nckh2/report/config/benchmark-sources.json), kiểm tra lại CSV của đúng phiên seed 1024, rồi cập nhật đoạn hạn chế theo nguồn thực sự đang dùng. Nếu muốn giữ chênh lệch của phiên cũ, đưa vào mục lịch sử và ghi rõ phiên đó.

## 3. Bảng quyết định: cần chạy lại phần nào?

| Nhóm | Đề xuất của tôi | Điều kiện/kết quả cần đạt |
|---|---|---|
| RQ1 cơ sở | **Chưa cần chạy lại toàn bộ** chỉ để viết báo cáo | Giữ nguồn, cấu hình, 40 run test và kết quả âm. Chạy lại nếu đổi thuật toán/dữ liệu hoặc thực sự cần một lần tái lập độc lập |
| RQ1 stress 1.400 fit | **Chưa cần lặp lại nguyên batch** | Có nguồn chính và lần lặp riêng. Nên dùng ngân sách cho cải tiến xử lý bản sao hoặc dữ liệu thực tế hơn |
| RQ2/RQ3 | **Chưa cần sinh/chạy lại toàn bộ** | Khôi phục nguồn `demo/`, cache Candidate 4.1 và môi trường trước. Kết quả đã có đủ để trình bày nghiên cứu tổng hợp |
| Phân tích thống kê RQ3 | Chỉ tính lại nếu sửa protocol hoặc phát hiện lỗi | Dùng 40 seed sau khi gộp ba điều kiện. Không đổi sang 120 mẫu độc lập để có p-value nhỏ hơn |
| Mô hình ảnh FP32 và chuyển runtime CPU | Giữ kết quả hiện tại; **đánh giá lại khi đổi model/tiền xử lý/asset** | Cần đúng model, split/config/manifest; so sánh với kết quả gốc trong thư mục riêng |
| PTQ/QAT | **Không ưu tiên chạy lại chỉ để mong tăng accuracy** | Nếu cần triển khai INT8, trước hết phân tích sai lớp, tiền xử lý, hiệu chỉnh và kernel. Phương án sửa phải đánh giá cùng test và tập xác nhận riêng |
| Bỏ bớt kênh tính toán của mô hình | Giữ kết quả như đánh đổi kỹ thuật; chưa chọn triển khai chỉ vì Accuracy cao hơn | Nếu muốn nói thao tác này giúp tốt hơn, cần đối chứng tinh chỉnh mô hình gốc với cùng ngân sách huấn luyện và xác nhận độc lập |
| LR 32 trạng thái | Không cần train lại liên tục trên cùng bảng | Ưu tiên kiểm tra đường dữ liệu app–backend; kiểm tra luật OR là baseline |
| E2E web | Dùng hai lượt mới; **thêm lượt xác nhận có đủ hồ sơ nếu manifest cũ không khôi phục được** | Đủ năm stage, giữ CHƯA CÓ, kết quả/log/hash/manifest/checkpoint cùng một phiên |
| Mạng yếu | Dùng phiên 2.313 lượt hiện tại; **nên bổ sung đo lặp** | Báo cáo tỷ lệ thành công + median/P95 + lỗi định dạng/mạng; giữ mọi thất bại hợp lệ |
| Android | **Ưu tiên chạy bổ sung** | Cùng model seed với CPU, đủ ảnh test, metadata máy/APK/asset, đo lặp |

## 4. Việc làm ngay: cập nhật báo cáo bằng kết quả đã có

### 4.1. Thêm bảng E2E mới vào mục 4.2.13

Đọc `checks.csv`, `summary.json` và checkpoint của hai lượt được liệt kê trong danh mục. Bảng nên có: ngày chạy, gold run, số báo cáo seed, ảnh dùng, năm stage hoàn tất, PASS, FAIL, CHƯA CÓ, tình trạng hồ sơ nguồn.

Phát biểu phù hợp: “Hai lượt trên run_001 và run_002 hoàn tất năm kịch bản; mỗi lượt có 45 tiêu chí đạt, không có tiêu chí FAIL và một tiêu chí giao diện CHƯA CÓ.” Giữ riêng số 46/46 của năm/ngày kiểm thử lịch sử nếu vẫn cần dẫn. Không dùng số mới để suy rằng AI Android hoặc SMS đã hoạt động.

### 4.2. Thêm bảng mạng yếu vào mục 4.2.13

Dùng [CSV thô](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_weak_network/results/20261005-102040/weak_network.csv) và [bảng tổng hợp](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_weak_network/results/20261005-102040/weak_network.md). Có thể đưa chín dòng mạng/chế độ vào bảng, cộng một biểu đồ thời gian và tỷ lệ thành công.

Ghi rõ 257 ảnh validation × 3 mạng × 3 chế độ × 1 lần, timeout, băng thông, RTT, máy đo và phiên mã. Nêu 27 NETWORK_ERROR, 3 UNSUPPORTED_IMAGE. Không xóa ba lượt AVIF bị từ chối và không gọi chúng là mạng lỗi. Metadata dùng payload cố định; không kết luận về khả năng mô hình AI tự chọn chế độ gửi từ phép đo này.

Sửa câu “chưa có results” ở cả [results.tex](D:/nckh-flood-rescue/nckh2/report/chapters/04-evaluation/sections/results.tex), [limitations.tex](D:/nckh-flood-rescue/nckh2/report/chapters/04-evaluation/sections/limitations.tex) và các chỗ liên quan nếu còn xuất hiện. Hạn chế mới nên là “đã có một phiên giả lập, chưa có lặp nhiều phiên/đo di động thật”.

### 4.3. Chốt số liệu và phát biểu về nguồn

Trong thiết lập Chương 4, nên có cột “nguồn/tình trạng” với ba loại: kết quả dùng chung với bài báo; thực nghiệm riêng bổ sung ngoài bài báo; kết quả hệ thống mới của lần chạy được ghi ngày cụ thể. RQ1/RQ2/RQ3 dùng lại không phải điều xấu; cần minh bạch để tránh bị hiểu là đã xác nhận độc lập lần thứ hai.

Sửa đoạn QAT nêu ở mục 2.3. Bổ sung E2E/mạng yếu mới vào bảng nguồn thực nghiệm và phụ lục tái lập. Hiện [export_results.py](D:/nckh-flood-rescue/nckh2/report/scripts/export_results.py) chưa tự đọc hai bộ kết quả mới để xuất bảng; nếu tích hợp, nên cập nhật công cụ xuất bảng hoặc có script tổng hợp tương ứng, thay vì chỉnh tay file trong `report/generated/tables` rồi bị ghi đè lần xuất kế tiếp.

## 5. Chạy bổ sung ưu tiên 1 — Mạng yếu có lặp và đối chiếu công bằng

### Câu hỏi cần trả lời

“Với cùng ảnh và cùng cấu hình mạng, gửi metadata/ảnh nén/ảnh gốc có khác nhau ổn định về tỷ lệ tới server, thời gian chờ và byte truyền không?”

### Thiết kế gợi ý

- Giữ 257 ảnh validation và ba cấu hình hiện có để so sánh với phiên cũ.
- Nếu đủ thời gian, chạy `--repeats 3`, tương ứng **6.939 lượt dự kiến**; đây là ba lần/ảnh/điều kiện, không phải ba bộ ảnh độc lập. Tốt hơn nữa có thêm phiên vào thời điểm khác và ghi lại điều kiện máy.
- Runner hiện thực hiện kế hoạch tuần tự. Ghi rõ thứ tự đó; nếu muốn kiểm soát ảnh hưởng nóng máy/tải theo thời gian tốt hơn, cần thiết kế thứ tự cân bằng/ngẫu nhiên có seed trong một phiên protocol mới. Đó là thay đổi cần làm thêm, chưa phải tính năng đã xác nhận có trong runner.
- Giữ lỗi mạng hợp lệ; không resume lặp lại các lỗi đó chỉ để biến chúng thành thành công. Giữ cùng timeout để so giữa các chế độ.
- Ngoài median/P95 của lượt thành công, báo cáo tỷ lệ thành công và số timeout. Muốn đánh giá “gửi được trong X giây”, đặt ngưỡng X trước khi xem kết quả và tính trên toàn bộ lượt của điều kiện.

### Công cụ và cách bắt đầu

Runner: [weak_network.py](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_weak_network/weak_network.py). Mở backend riêng theo [README](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_weak_network/README.md), dùng DB/uploads riêng như tài liệu. Sau khi backend ở cổng 8001 đã sẵn sàng, tại thư mục runner có thể dùng:

```powershell
cd D:\nckh-flood-rescue\nckh2\thuc_nghiem_nq\experiment_weak_network
.\.venv\Scripts\python.exe weak_network.py --check-inputs
.\.venv\Scripts\python.exe weak_network.py --run --repeats 3
```

Đây là lệnh đề xuất, chưa được thực thi trong lần lập tài liệu. Mỗi lần `--run` tạo RUN_ID riêng; không ghi đè `20261005-102040`. Xem phần hướng dẫn cài môi trường trong README nếu `.venv` chưa có đủ dependency.

**File cần nhận:** CSV từng request, Markdown tổng hợp, manifest, console, checkpoint. Nêu số lượt dự kiến/thực có, băng thông/RTT, phiên bản runner và backend. Khi tổng hợp thống kê, giữ cấu trúc cùng ảnh/điều kiện/lần đo, không coi mọi request là quan sát người dùng độc lập.

## 6. Chạy bổ sung ưu tiên 2 — Mô hình trên điện thoại Android đúng phiên bản

### Câu hỏi cần trả lời

“APK định nộp/thử nghiệm có chạy đúng model đang báo cáo không, kết quả có giữ nguyên và người dùng phải chờ bao lâu?”

### Thiết kế gợi ý

1. Chọn rõ model sẽ trình bày, ví dụ seed 1024 đang dùng ở các bảng CPU; không ghép benchmark app seed 42 vào như cùng model.
2. Ghi trước khi đo: tên máy/SoC/RAM, Android, APK hoặc commit mã, ngày giờ, SHA-256 model/config/manifest/split, runtime/provider/số luồng, pin/nhiệt và trạng thái cấp nguồn nếu thu được. Thiếu trường nào ghi thiếu trường đó.
3. Chạy đủ 256 ảnh test cho ONNX/PTE trên cùng máy. Giữ ảnh gốc, nhãn, thứ tự và tiền xử lý đã định nghĩa. Chạy vài ảnh kiểm tra đầu vào trước, nhưng kết quả vài ảnh không thay full test.
4. Đo lặp tối thiểu vài phiên trên một máy; nếu tiếp cận được, dùng thêm máy cấu hình khác. Đề xuất thực dụng là 2 máy × 3 phiên, nhưng một máy có hồ sơ tốt vẫn có giá trị hơn nhiều máy không biết asset nào đã chạy.
5. Giữ phạm vi timing rõ: `classifyImage` gồm tiền xử lý native; nếu muốn tách decode/resize/runtime thì cần bổ sung ghi thời gian từng bước. Không lấy thời gian app chia cho predict CPU để gọi speedup khi phạm vi khác nhau.

### File liên quan và đầu ra cần có

- Đóng gói ảnh: [build_benchmark_package.py](D:/nckh-flood-rescue/nckh2/products/be/build_benchmark_package.py).
- Đo trong app: [model_benchmark.dart](D:/nckh-flood-rescue/nckh2/products/fe/app/lib/domain/services/model_benchmark.dart).
- Hướng dẫn nhóm đã có: [experiment_mobile_app.md](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/docs_thuc_nghiem/experiment_mobile_app.md).
- Kiểm tra lại export: [mobile_evidence.py](D:/nckh-flood-rescue/nckh2/report/scripts/mobile_evidence.py). Module hiện đọc định dạng của nguồn mobile cũ; nếu export mới khác schema, cần cập nhật bộ đọc, không ép ghép file sai định dạng.
- Kết quả mới nên để trong thư mục riêng theo ngày/máy/model; đây là vị trí dự kiến, chưa có bộ kết quả mới cho protocol đề nghị này.

**Đánh giá:** Accuracy/macro-F1/recall high/lỗi nặng; nhãn khác CPU ở ảnh nào; mean/P50/P95; lỗi suy luận, ảnh không xử lý được; thời gian nạp model báo riêng. Nếu dự đoán khác nhau, đối chiếu pixel đầu vào và hash asset trước khi kết luận engine gây sai.

## 7. Chạy bổ sung ưu tiên 3 — Điểm khẩn cấp có đi đúng từ app đến cụm không?

### Câu hỏi cần trả lời

“Người dùng chọn một dấu hiệu khẩn cấp trong app, điểm LR đó có thực sự đi vào thuật toán phân cụm/xếp hạng không?”

Hiện [cluster_service.py](D:/nckh-flood-rescue/nckh2/products/be/cluster_service.py) ưu tiên trường `urgency` hoặc từ khóa mô tả; báo cáo ghi app gửi `E_i`. Việc LR đúng 32 profile chưa chứng minh điểm đã đi tới backend đúng cách.

### Việc cần làm trước và phép thử gợi ý

- Chốt hợp đồng trường giữa app/API/DB/adapter: tên trường, thang điểm, giá trị thiếu, độ ưu tiên khi đồng thời có dữ liệu cấu trúc và mô tả. Nếu đổi code, chạy kiểm tra tích hợp trên đúng phiên mã mới.
- Gửi các trường hợp không có cờ; từng cờ riêng; nhiều cờ; không nhập/không biết; mô tả mâu thuẫn với lựa chọn; gửi lại sau offline. Các trường hợp mẫu này là đề nghị mới, chưa có runner chuyên biệt đã được xác nhận.
- Ghi trong cùng một ca: input người dùng → điểm app → payload gửi → giá trị lưu DB → `ReportV2.E` → điểm cụm. Đối chiếu giá trị kỳ vọng theo hợp đồng, không chỉ nhìn màn hình app.

**Tiêu chí đạt:** trường giá trị đến đúng tầng, không bị mất/đổi thang/điền 0 nhầm khi thiếu. Thay trường không liên quan không được làm sai giá trị khẩn cấp. Đây là kiểm tra toàn vẹn dữ liệu, chưa phải kiểm định chất lượng y khoa của score.

## 8. Chạy bổ sung ưu tiên 4 — E2E web có hồ sơ đầy đủ và hàng đợi Android

### E2E web

Giữ hai run đã hoàn tất. Nếu manifest/log không truy lại được, chạy một lượt xác nhận mới với cùng protocol và lưu đủ hồ sơ; nếu code/ảnh thay đổi thì ghi là phiên khác. Không gọi đây là khôi phục chính lần chạy cũ.

```powershell
cd D:\nckh-flood-rescue\nckh2\thuc_nghiem_nq\experiment_e2e
.\.venv\Scripts\python.exe e2e_system.py --check-inputs
.\.venv\Scripts\python.exe e2e_system.py --run --seed-run 3
```

Lệnh gợi ý chọn thêm run_003 để tăng độ đa dạng dữ liệu, chưa được thực thi ở đây. Runner: [e2e_system.py](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_e2e/e2e_system.py), [hướng dẫn](D:/nckh-flood-rescue/nckh2/thuc_nghiem_nq/experiment_e2e/README.md). Chỉ chạy tuần tự trên bộ cổng mặc định; mỗi lượt có volume/ID riêng. Trước khi đóng gói, xác nhận có manifest trong log, CSV/summary, ảnh chụp và checkpoint.

Nếu chỉ muốn minh họa luồng chức năng, không bắt buộc chạy đủ 80 run. Nếu muốn báo độ ổn định theo bối cảnh dữ liệu, có thể chọn trước 5–10 run đa dạng để làm pilot, công bố tất cả; số này là gợi ý thực dụng, không phải cỡ mẫu bảo đảm thống kê. Muốn nói về ảnh đầu vào, phải thay ảnh qua `--image-relative-path`, giữ điều kiện CSV val/high/JPG của runner hiện tại và ghi ảnh nào cho từng lượt. Runner này chưa có nghĩa là tự kiểm tra mọi lớp/định dạng.

### Hàng đợi trên Android

E2E web chưa thay được kiểm tra tiến trình nền của Android. Nên có một ma trận ca: tạo offline → đóng/mở app; offline → kill app; offline → reboot; có mạng lại; server đã lưu nhưng client không nhận ACK; gửi lại cùng báo cáo; bổ sung ảnh sau metadata. Kiểm tra cả log app và server.

**Đánh giá:** không mất báo cáo đã cam kết lưu, không sinh bản trùng khi gửi lại, trạng thái ACK phản ánh đúng server, metadata và ảnh gắn đúng báo cáo; đo thời gian từ có mạng đến ACK. Các bảo đảm này phải bám hợp đồng hiện tại, không giả định app đã bảo đảm mọi tình huống.

Đây là phép thử mới cần thiết kế runner hoặc checklist/log riêng; chưa có công cụ Android tự động đầy đủ được xác nhận trong lần rà soát này. SMS/gateway thực cũng là một phép thử riêng nếu nhóm muốn tuyên bố tin đã tới nơi tiếp nhận; việc Android nhận lệnh gửi SMS chưa đủ.

## 9. Chạy thêm nếu muốn tăng chất lượng khoa học

### 9.1. Ảnh độc lập với bộ đã dùng nhiều lần

**Lý do:** các nhánh FP32/PTQ/QAT/bớt kênh đều đã xem cùng test. Chọn phương án tốt nhất rồi công bố trên chính test đó chưa phải xác nhận độc lập cho phương án cuối.

**Đề nghị:** giữ nguyên test cũ; thu thêm ảnh có nguồn/sự kiện rõ, tránh cùng cảnh hoặc bản gần trùng với train/val/test. Có thể bắt đầu một pilot cân bằng các lớp, chẳng hạn 20–30 ảnh/lớp; kích thước này là gợi ý khởi đầu, chưa đủ để hứa khả năng tổng quát. Nhờ người gán nhãn độc lập và ghi cách xử lý bất đồng. Không dùng bộ mới để tinh chỉnh model trước khi đánh giá model đã khóa.

**Đánh giá:** recall lớp high, nhầm high → low/non_flood, macro-F1 và ma trận nhầm lẫn, khoảng tin cậy và số ảnh mỗi lớp. So FP32 với đúng phương án định triển khai. Nếu thiếu nguồn ảnh hoặc nhãn tốt, chưa nên gọi pilot là đánh giá thực địa.

### 9.2. Loại bản sao truyền tải trước khi tạo đồ thị

**Lý do:** TN09 cho thấy ARI giảm mạnh ở bản sao 5×. Chống bản sao ở công thức điểm chưa ngăn bản sao làm hỏng bước gom cụm.

**Đề nghị:** một nhánh mới loại đúng bản sao truyền tải theo ID/fingerprint trước dựng đồ thị, giữ báo cáo củng cố độc lập; so với pipeline gốc trên cùng 40 run, đặc biệt điều kiện gốc/2×/5×. Sau khi protocol và code sẵn sàng mới dùng notebook stress làm khung thử; hiện chưa có runner hoàn chỉnh cho biến thể đề nghị này.

**Đánh giá:** ARI/F1 trên báo cáo gốc, số báo cáo bị loại, loại nhầm báo cáo độc lập, runtime và fake destinations. Không chỉ đo điểm priority có đổi không. Nếu chọn tham số mới phải chọn bằng development/calibration, giữ test cho đánh giá cuối.

### 9.3. Thử điều phối có xét chi phí đi lại

**Lý do:** gần nhất trước tốt hơn score theo nhu cầu trong mô phỏng hiện tại. Điều đó gợi ý cần cân bằng nhu cầu với thời gian/khả năng đi tới nơi, chứ không chỉ làm score lớn hơn.

**Đề nghị:** thiết kế một đối chứng có xét nhu cầu và chi phí di chuyển/năng lực phục vụ quan sát được. Giữ legacy, nearest-first, oracle và các phân hoạch đối chứng; dùng Candidate đã khóa. Đây là hướng cải tiến mới, chưa có phương án chứng minh hiệu quả.

**Đánh giá:** harm, trễ hạn, số sự kiện được phục vụ, thời gian tới nơi, chuyến đi lặp/giả và chênh lệch phục vụ giữa các nhóm. Không cho scheduler đọc deadline/harm/nhãn truth nếu protocol cũ quy định chỉ evaluator được dùng. Lập lại so sánh theo seed và hiệu chỉnh nhiều chỉ số như protocol đã chốt.

### 9.4. Đánh giá với người dùng hoặc chuyên gia

Nếu nhóm muốn nói app dễ dùng hoặc danh sách ưu tiên có ích cho điều phối viên, cần phép thử riêng, không suy từ PASS của Playwright. Có thể pilot một số tác vụ cố định với người tham gia: gửi báo cáo, hiểu trạng thái đang chờ/đã nhận, tìm điểm trên dashboard và xử lý thiếu thông tin. Đo tỷ lệ hoàn thành, thời gian, lỗi thao tác và phản hồi có cấu trúc.

Đối với score khẩn cấp/ưu tiên, cần nhãn hoặc đánh giá chuyên gia phù hợp mục tiêu trước khi tuyên bố đúng về nghiệp vụ. Đây là công việc bổ sung, chưa có corpus/runner/kết quả được xác nhận trong repo hiện tại.

## 10. Đánh giá nội dung Chương 4 hiện tại

### Điểm nên giữ

1. **Tách từng tầng đánh giá.** Phân loại ảnh, tính đúng khi chuyển định dạng, phân cụm, xếp hạng và điều phối là các câu hỏi khác nhau; việc này giúp kết luận đúng phạm vi.
2. **Giữ kết quả âm.** PTQ/QAT giảm chất lượng; Product chưa thắng Additive; điểm có chặn chưa thắng baseline; điều phối có thể kém nearest-first. Những kết quả này có giá trị và giải thích hướng cải tiến.
3. **Nêu nguồn và đơn vị thống kê.** Chọn cấu hình trước test, ghép cặp theo seed, phân biệt 40 seed và 120 hàng điều kiện, có CSV/provenance là điểm tốt.
4. **Không biến mô phỏng thành hiệu quả cứu hộ thật.** Cần giữ cách trình bày này xuyên suốt kết luận.

### Điểm nên sửa hoặc làm rõ

| Vấn đề | Vì sao cần sửa | Việc cụ thể |
|---|---|---|
| E2E/mạng yếu chỉ dẫn lịch sử, bỏ sót output mới | Người đọc hiểu nhầm nhóm chưa có thực nghiệm hệ thống | Thêm hai lượt E2E và bảng 2.313 lượt; ghi rõ hồ sơ E2E còn thiếu và phạm vi mạng giả lập |
| QAT 4.3.2 khác số của 4.2.5 | Làm mất tính nhất quán và khó truy nguồn | Chốt seed 1024 hoặc ghi rõ lịch sử phiên cũ; đồng bộ PDF/TeX/bảng |
| RQ1–RQ3 chưa được người đọc phổ thông phân biệt với ảnh/app | Dễ hiểu rằng tất cả cùng một bộ đa phương thức | Thêm bảng nguồn dữ liệu, phương thức, đơn vị đo; giải thích RQ3 không phải E2E UI |
| Benchmark app thiếu metadata và khác seed CPU | Chưa so được cùng model hoặc kết luận tốc độ triển khai | Thêm phiên Android đầy đủ nguồn, giữ bảng cũ là lịch sử |
| “Tối ưu” có thể bị hiểu là tốt hơn toàn diện | Nhỏ file nhưng có thể sai/chậm hơn | Dùng diễn giải “đánh đổi dung lượng–chất lượng–tốc độ”; nêu rõ phương án nào đạt/không đạt mục tiêu |
| LR chỉ kiểm tra nhãn do nhóm tạo, adapter còn khoảng trống | Dễ bị hiểu thành đã hoàn tất mô hình văn bản/đánh giá nghiệp vụ | Ghi đây là tính nhất quán kỹ thuật của 32 trạng thái; thêm kiểm tra đường dữ liệu |
| Nhiều bảng kỹ thuật, thiếu câu trả lời câu hỏi ban đầu | Người đọc khó biết nên dùng phương án nào | Đầu mỗi nhóm nêu một câu hỏi, cuối nhóm nêu đáp án có điều kiện và lựa chọn triển khai còn mở |
| Dữ liệu tổng hợp và ảnh cùng test được dùng lặp | Giới hạn tính khái quát/chọn phương án sau khi xem test | Giữ hạn chế, thêm dữ liệu xác nhận độc lập khi có điều kiện |
| Tên/đường dẫn lịch sử `src`, thiếu `demo`, verifier còn hard-code `src/results` | Có file notebook chưa đồng nghĩa clone là chạy được | Lập bản hướng dẫn đúng snapshot/môi trường hoặc chuyển workflow có đối chiếu hash; ghi rõ phần chưa khôi phục |

### Bố cục tôi đề nghị cho Chương 4

Giữ số mục hiện tại nếu cần tránh đổi tham chiếu, nhưng làm rõ bốn khối: (A) thiết lập và nguồn; (B) ảnh/thiết bị; (C) thuật toán RQ1–RQ3; (D) hệ thống E2E/mạng yếu và bàn luận. Đầu mỗi khối nêu dữ liệu đầu vào, mục tiêu, công cụ, kết quả và giới hạn bằng câu dễ hiểu. Không đưa các sơ đồ thiết kế hoặc ảnh dashboard thành bằng chứng độ chính xác thuật toán.

## 11. Kế hoạch thực dụng nếu gần hạn nộp

| Thứ tự | Việc | Sản phẩm cần nhận |
|---|---|---|
| 1 | Sao lưu output hiện có, tìm manifest/log E2E còn thiếu | Một bộ bằng chứng không bị mất khi chuyển nhánh; ghi rõ thiếu gì |
| 2 | Sửa đoạn QAT, thêm bảng nguồn và cập nhật E2E/mạng yếu | Chương 4 thống nhất với dữ liệu hiện tại |
| 3 | Chạy một lượt E2E có hồ sơ đầy đủ nếu không truy được hồ sơ cũ | CSV/summary/checkpoint/manifest/log/screenshot cùng phiên |
| 4 | Đo mạng yếu lặp nếu đủ thời gian | Bộ kết quả mới có repeats, không thay bộ 05/10 |
| 5 | Benchmark Android cùng model với CPU | JSON từng ảnh + đánh giá + thông tin máy/APK/asset |
| 6 | Kiểm tra điểm LR tới backend và hàng đợi Android | Ma trận ca, kỳ vọng, log app/server, giá trị so sánh |
| 7 | Có thêm thời gian thì ảnh độc lập và cải tiến bản sao/điều phối | Protocol mới + baseline cũ + toàn bộ kết quả tốt/xấu |

Không bắt buộc hoàn thành tất cả đề xuất để viết một báo cáo trung thực về nguyên mẫu. Điều cần chốt là các tuyên bố nào có bằng chứng và những phần nào vẫn đang là hướng phát triển.

## 12. Khi thực sự chạy lại, lưu và kiểm tra như thế nào?

- Chốt mục đích trước: đo lại tốc độ, kiểm tra bản APK mới hay thay thuật toán. Một lần xuất lại bảng không giải quyết được thiếu phép đo thiết bị.
- Giữ model/config/split/nhãn đúng nguồn. Với công cụ ảnh, đọc `--help` và truyền đủ các đường dẫn model đang so; mặc định hiện tại có thể không trỏ đúng checkpoint lịch sử seed 1024. Dùng `--report-dir` trỏ output mới. Công cụ [compare_models.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/compare_models.py), [compare_fp32_ptq_qat.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/compare_fp32_ptq_qat.py), [compare_structured_pruning.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/compare_structured_pruning.py) đều có lựa chọn thư mục output.
- Với notebook RQ1, dùng snapshot `6ac75c202d04934deb46d84486132e54d42d735f`; với RQ2/RQ3 cần nguồn `demo/`/cache Candidate và môi trường tương ứng. Đọc [phụ lục tái lập](D:/nckh-flood-rescue/nckh2/report/appendices/reproducibility.tex) trước khi chạy. [verify_camera_ready_evidence.py](D:/nckh-flood-rescue/nckh2/thucnghiem/results/verify_camera_ready_evidence.py) còn tham chiếu `src/results`; chưa nên chạy trực tiếp trong cây hiện tại rồi xem lỗi đường dẫn là kết quả thí nghiệm sai.
- Lưu riêng output cũ và mới. Không sửa JSON/CSV gốc để khớp câu trong báo cáo; sửa câu hoặc sửa quy trình, và ghi lại nguồn thay đổi.
- Bảo toàn cả thất bại và CHƯA CÓ. Chỉ ghi complete/PASS theo định nghĩa runner, không dựa vào việc cửa sổ trình duyệt đã đóng hoặc có file CSV.
- Đóng gói CSV/JSON thô, bảng đánh giá, log, checkpoint, manifest/hash, ngày/máy/runtime và mã nguồn tương ứng. Git đang bỏ qua nhiều output và `thuc_nghiem_nq` chưa được theo dõi trên nhánh hiện tại; cần có bước sao lưu/commit artifact chọn lọc rõ ràng.

Sau khi nguồn bảng thay đổi, dùng công cụ xuất bảng/hình và build báo cáo để tạo lại PDF; kiểm tra các đoạn mô tả viết tay vì chúng không tự thay theo CSV. Những công cụ biên soạn này chỉ kiểm tra/sinh tài liệu, không thay cho việc chạy lại các thực nghiệm nêu trên.
