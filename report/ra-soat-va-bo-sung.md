# Rà soát và bổ sung report — 06/10/2026

Đã rà soát các chương, phụ lục, metadata, bảng sinh, mã ứng dụng/backend, notebook huấn luyện và artifact thực nghiệm. Bản trước đợt này đã có 50 trang thân bài nhưng nhiều nội dung mới ở mức mô tả. Việc bổ sung dùng kết quả đã lưu; không huấn luyện lại, không sửa artifact gốc hoặc triển khai thay đổi sản phẩm.

## Thiếu sót và thay đổi đã thực hiện

| Phần | Phát hiện | Nội dung bổ sung hoặc chỉnh sửa |
|---|---|---|
| Tổng quan | Nghiên cứu trong nước mới dẫn chung theo thuyết minh; thiếu so sánh bài toán | Hai công trình trong nước năm 2025, bảng so sánh tám hướng/công trình, phân biệt ảnh vệ tinh/ảnh mặt đất/cụm cứu hộ và BPv7/outbox HTTP |
| Mô hình ảnh | Chưa giải thích head, augmentation, hàm loss và chọn checkpoint | Sơ đồ mô hình, cấu hình augmentation, công thức CE + severity, AdamW/scheduler/freeze, quy tắc chọn checkpoint và đường cong 11 epoch đã lưu |
| Phiên bản huấn luyện | Notebook hiện đặt seed 599; artifact được dẫn dùng seed 42 | Ghi rõ vai trò notebook giải thích cơ chế và config/artifact xác định số liệu; không coi chạy notebook hiện tại là tái lập seed 42 |
| Phân cụm | Dễ nhầm chặn cạnh với chặn cụm; thiếu giải thích chi phí | Sơ đồ chuỗi cạnh, chi phí số cặp/dense matrix/top-k, tác động multiplicity và yêu cầu giữ lineage khi thử khử bản sao |
| Đồng bộ | Kiến trúc tổng thể chưa giải thích đầy đủ ca mất ACK | Sơ đồ trình tự mất ACK sau commit, ba định danh/hai trạng thái, bảng phản hồi và luồng nghiệp vụ người gửi–trung tâm |
| Kết quả ảnh | Bảng nhiều số, thiếu trực quan và ví dụ lỗi | Heatmap nhầm lẫn, tám ảnh đúng/sai chọn xác định, reliability/số mẫu confidence và đồ thị đánh đổi nén/cắt tỉa |
| Mobile | Report nói không có benchmark mobile, dù repo có tệp benchmark app | Đọc hai object JSON nối tiếp, kiểm tra đủ sample ID/nhãn với split, tính lại metric và percentile, bảng/boxplot ứng dụng và đối chiếu CPU |
| RQ1/RQ2 | Thiếu hình đọc chênh lệch nhỏ và hạn chế robustness | CI cho năm pipeline đồ thị; NDCG của sáu baseline; drift dưới exact/near/tăng khai báo/campaign, giữ bảng đầy đủ và kết quả âm |
| Hành chính | Phụ lục vẫn nói metadata chưa xác nhận | Đồng bộ theo thông tin đã xác nhận trong metadata/infoGroup; giữ riêng phần chờ mẫu và minh chứng thật |
| Tái lập/hình thức | Chưa có workflow sinh hình/truy nguyên nguồn | Chín hình PDF/PNG, script và dependency, provenance hash nguồn/hình, kiểm tra hình lỗi thời trong `make check`, cập nhật tóm tắt Việt–Anh |

## Minh chứng mobile được phát hiện

Nguồn: `products/fe/reports/mobile/samsung21se.json`. Tệp chứa hai JSON object nối tiếp, được đọc bằng `JSONDecoder.raw_decode`; không thay đổi nguồn để ép thành JSON khác.

- Cả ONNX và PTE xử lý đủ 256 ảnh, không lỗi, năm warmup không lỗi.
- Sample ID là 12 ký tự đầu SHA-1 của đường dẫn tương đối, đối chiếu theo `products/be/build_benchmark_package.py`; toàn bộ ID/nhãn khớp test split seed 42.
- Tính lại từ từng dự đoán: 192/256 đúng, accuracy **75,00%**, macro-F1 **73,31%** cho cả hai runtime. Ma trận và metric mỗi lớp đều khớp.
- ONNX và PTE trùng toàn bộ nhãn top-1. So với CPU FP32, 249/256 nhãn trùng; năm ca đúng→sai và hai ca sai→đúng.
- Mean/P50/P95 khớp cách tính nearest-rank của mã app. P50 ONNX **54,500 ms**, PTE **29,487 ms**; P95 **112,139/85,890 ms**.
- Timing bao quanh `classifyImage`, rộng hơn predict CPU. Tệp thiếu model thiết bị/OS/APK/commit/hash model/ngày đo; tên tệp không xác nhận cấu hình máy. Chưa dùng kết quả để xác nhận APK của checkpoint JNI ngày 04/10.

Một phân tích mô tả bổ sung từ CSV FP32 cho thấy 52/256 ảnh có confidence ≥0,90, cả 52 đều đúng. Không chọn lại ngưỡng từ test và không coi nhóm này là bảo đảm cho ảnh camera hoặc các nguồn mới.

## Nguồn bên ngoài đã đọc trực tiếp

| Nguồn gốc | Nội dung sử dụng | Nơi đưa vào report |
|---|---|---|
| [Doan & Le-Thi, JAIT 2025](https://www.jait.us/articles/2025/JAIT-V16N1-57.pdf) | Phát hiện ngập bằng cặp ảnh SAR/Siamese/Swin-Transformer | Tổng quan trong nước và bảng so sánh |
| [Ngô Thanh Vũ và cộng sự, ĐH Đà Nẵng 2025](https://jst-ud.vn/jst-ud/article/download/9674/6473) | Quan trắc ngập từ ảnh biển báo và tham chiếu hình học | Tổng quan trong nước và khác biệt với lớp thị giác tương đối |
| [MobileNetV3, ICCV 2019](https://openaccess.thecvf.com/content_ICCV_2019/html/Howard_Searching_for_MobileNetV3_ICCV_2019_paper.html) | Cơ sở thiết kế backbone cho mobile | Phần thiết kế mô hình; cài đặt cụ thể lấy từ repo |
| [CrisisMMD, ICWSM 2018](https://ojs.aaai.org/index.php/ICWSM/article/view/14983) | Dữ liệu ảnh–văn bản thiên tai | Đối chiếu nhiệm vụ; không coi là tập train của đề tài |
| [FloodNet, bản tác giả](https://arxiv.org/abs/2012.02951) | Hiểu cảnh hậu ngập từ ảnh UAV | Bảng so sánh và giới hạn chuyển góc nhìn |
| [RFC 9171](https://www.rfc-editor.org/rfc/rfc9171.html) | BPv7 và store-carry-forward | Phân biệt chuẩn DTN với outbox HTTP đã triển khai |
| [ONNX Runtime: Quantization](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html) | PTQ/calibration và phân tích sai lệch tensor | Cơ sở tối ưu và kế hoạch phân tích QAT |
| [Guo và cộng sự, ICML 2017](https://proceedings.mlr.press/v70/guo17a.html) | Calibration, reliability và temperature scaling | Confidence/chính sách metadata; không tuyên bố đã hiệu chuẩn lại |

Các nguồn mới có entry/trích dẫn trong `bibliography/articles.bib`; những nguồn đã có được kiểm tra lại. Nội dung không sao chép bảng/ảnh của bài báo ngoài. Sơ đồ được viết từ hợp đồng/mã nguồn; biểu đồ được sinh từ artifact của repo.

## Phần còn thiếu bằng chứng để khép lại

| Ưu tiên | Khoảng trống | Bằng chứng cần có |
|---|---|---|
| 1 | PTQ/QAT summary chưa khớp CSV | Một lần tái sinh metric và prediction cùng phiên, checkpoint/config/split/hash khớp. Không tự chọn nguồn có số đẹp hơn |
| 1 | App gửi `E_i`, adapter dùng `urgency`/từ khóa | Quy tắc schema/ưu tiên nguồn và kiểm thử end-to-end sau thay đổi sản phẩm |
| 1 | NLP tiếng Việt chưa hoàn thành | Corpus tin nhắn, quy trình gán nhãn, model và đánh giá giữ riêng |
| 2 | Mobile thiếu provenance và đo lặp | Thiết bị/SoC/OS, APK/commit, hash asset, số luồng, ngày đo, pixel parity; các phiên lặp trên nhiều máy |
| 2 | SMS, mạng yếu, nền và pin | Log thiết bị–gateway–backend, bộ kết quả mạng có nhiều lượt, kill/reboot/background và năng lượng |
| 2 | Dữ liệu ảnh và tổng hợp thiếu kiểm chứng thực địa | Lineage/giấy phép ảnh, tập camera độc lập, nhãn sự kiện và mục tiêu có xác nhận phù hợp |
| 3 | Hồ sơ nộp | Mẫu chính thức, thuyết minh có ký/dấu, PDF minh chứng sản phẩm, video; không thể suy ra từ mã nguồn |

Các mục này được trình bày như hạn chế hoặc công việc tiếp theo trong report. Đợt này không tạo dữ liệu bệnh nhân, đánh giá thực địa, log thiết bị, chữ ký/dấu hay kết quả thí nghiệm chưa thực hiện.

## Kiểm tra

PDF một mặt/hai mặt đều 94 trang, gồm 68 trang thân bài và 19 hình; kết quả kiểm tra chi tiết được ghi trong `README.md`. Quy trình đã chạy gồm xuất bảng/audit 1.702 ảnh, kiểm tra hai benchmark app, sinh hình, build nội dung và các sản phẩm Việt–Anh, `make check` và kiểm tra diff. Không chạy lại training, notebook Colab, E2E hoặc điện thoại.
