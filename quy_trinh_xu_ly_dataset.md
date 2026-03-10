**Lộ trình chuẩn bị dataset (thực thi được ngay)**

1. Chốt schema nhãn dùng xuyên suốt toàn bộ dự án.
2. Thu thập và hợp nhất dữ liệu ảnh từ 2 nguồn quốc tế + nguồn Việt Nam.
3. Thu thập và chuẩn hóa dữ liệu văn bản tiếng Việt cứu hộ.
4. Gán nhãn có kiểm soát chất lượng (2 người gán chéo + xử lý bất đồng).
5. Tiền xử lý theo chuẩn Edge AI.
6. Chia train/val/test theo chiến lược chống rò rỉ.
7. Xuất metadata + báo cáo thống kê dataset.
8. Chạy demo inference để kiểm tra pipeline trước khi huấn luyện.

**1) Chốt schema nhãn (quan trọng nhất trước khi crawl)**

* Ảnh: no_flood, low_flood, high_flood.
* Văn bản: urgent_rescue, need_supplies, safe_update, irrelevant.
* Bắt buộc có guideline 1 trang cho từng nhãn: định nghĩa, ví dụ đúng/sai, trường hợp biên.

**2) Nhánh ảnh: cách chuẩn bị bộ dữ liệu đặc thù Việt Nam**

1. Lấy dữ liệu nền:

* FloodNet: remap lớp về 3 lớp ngập.
* CrisisMMD: lọc flood events rồi remap theo damage severity.
* Bổ sung 1-2 bộ ảnh ground-level từ Kaggle để gần ảnh điện thoại thực tế.

2. Lấy dữ liệu Việt Nam (phần tạo tính đặc thù):

* Crawl ảnh theo sự kiện: lũ miền Trung 2020, Noru 2022, Yagi 2024.
* Nguồn: báo điện tử, nhóm cứu hộ công khai, nguồn cộng đồng.
* Mục tiêu tối thiểu: 300-500 ảnh VN cho giai đoạn 1; tốt hơn là 800-1200 ảnh VN đã gán nhãn sạch.

3. Chuẩn hóa:

* Resize 224x224 cho nhánh MobileNetV3.
* Lưu ảnh gốc riêng để truy vết.
* Tạo metadata mỗi ảnh: source, original_label, mapped_label, event, province, timestamp, is_vietnam, hash.

4. Cân bằng lớp:

* Nếu high_flood ít, dùng oversampling có kiểm soát hoặc class weights khi train.
* Không tăng cường dữ liệu quá mạnh làm mất ngữ cảnh thực địa.

**3) Nhánh văn bản: cách chuẩn bị dữ liệu cứu hộ tiếng Việt**

1. Dữ liệu nền:

* UIT-VSMEC để khởi tạo hiểu tiếng Việt mạng xã hội.

2. Dữ liệu đặc thù:

* Thu tin nhắn công khai về cứu hộ, ngập, tiếp tế, cập nhật an toàn.
* Mục tiêu ban đầu: 2000-5000 câu đã gán nhãn.

3. Chuẩn hóa text:

* lowercase, bỏ URL, chuẩn hóa số điện thoại và PII.
* Chuẩn hóa teencode và viết tắt phổ biến.
* Giữ lại tín hiệu khẩn cấp như cứu với, ngập nóc, kẹt trẻ em.

4. Lưu dữ liệu:

* Cột tối thiểu: id, raw_text, clean_text, urgency_label, source, event, location_hint.

**4) Kiểm soát chất lượng gán nhãn (điểm hay bị bỏ sót)**

1. 20-30 phần trăm mẫu phải được 2 người gán độc lập.
2. Tính agreement (Cohen kappa hoặc tỉ lệ đồng thuận).
3. Mẫu bất đồng đưa vào vòng adjudication bởi 1 người chốt.
4. Tạo file rulebook để lần sau không gán lệch.

**5) Chia tập dữ liệu đúng để không ảo kết quả**

1. Split 70/15/15, seed cố định 42.
2. Stratified theo nhãn.
3. Chống leakage theo sự kiện:

* Cùng một sự kiện bão lũ không để tràn qua cả train và test nếu ảnh quá giống nhau.

4. Với văn bản, chống near-duplicate giữa các tập.

**6) Cấu trúc thư mục khuyến nghị**

* Dùng đúng tinh thần trong [data_preparation_guide.md](vscode-file://vscode-app/c:/Users/jhiny/AppData/Local/Programs/Microsoft%20VS%20Code/ce099c1ed2/resources/app/out/vs/code/electron-browser/workbench/workbench.html) và [model_evaluation_workflow.md](vscode-file://vscode-app/c:/Users/jhiny/AppData/Local/Programs/Microsoft%20VS%20Code/ce099c1ed2/resources/app/out/vs/code/electron-browser/workbench/workbench.html):

1. dataset/image_data/train|val|test/no_flood|low_flood|high_flood
2. dataset/text_data/train.csv, val.csv, test.csv
3. dataset/metadata.csv
4. dataset/dataset_report.md
5. dataset/text_data/text_dataset_report.md

**7) Tiêu chí hoàn thành Bộ dữ liệu đặc thù cứu hộ bão lũ Việt Nam**

1. Có đủ 2 nhánh ảnh và văn bản, cùng schema nhãn thống nhất.
2. Tỷ lệ dữ liệu Việt Nam đủ lớn để fine-tune (khuyến nghị ít nhất 30-40 phần trăm ở nhánh ảnh giai đoạn đầu).
3. Có metadata đầy đủ để truy xuất nguồn và kiểm toán.
4. Có báo cáo phân bố lớp, nguồn dữ liệu, tỷ lệ Việt Nam/quốc tế, vấn đề mất cân bằng.
5. Có tập test sạch và cố định để benchmark mọi mô hình về sau.

**8) Cách triển khai ngay trong repo hiện tại**

1. Chạy [dataset_preparation.ipynb](vscode-file://vscode-app/c:/Users/jhiny/AppData/Local/Programs/Microsoft%20VS%20Code/ce099c1ed2/resources/app/out/vs/code/electron-browser/workbench/workbench.html) để sinh dữ liệu chuẩn hóa, split và báo cáo.
2. Chạy [model_demo_inference.ipynb](vscode-file://vscode-app/c:/Users/jhiny/AppData/Local/Programs/Microsoft%20VS%20Code/ce099c1ed2/resources/app/out/vs/code/electron-browser/workbench/workbench.html) để xác nhận pipeline inference hoạt động.
3. Đối chiếu kết quả với checklist trong [model_evaluation_workflow.md](vscode-file://vscode-app/c:/Users/jhiny/AppData/Local/Programs/Microsoft%20VS%20Code/ce099c1ed2/resources/app/out/vs/code/electron-browser/workbench/workbench.html) trước khi chuyển qua giai đoạn huấn luyện.

---

## Trạng thái thực thi trong repo

Đã tạo sẵn các thành phần vận hành:

- Cây thư mục dataset chuẩn tại `dataset/`
- Template metadata ảnh: `dataset/metadata_template.csv`
- Template text gán nhãn: `dataset/text_data/rescue_text_samples_template.csv`
- Guideline nhãn ảnh: `dataset/label_guidelines.md`
- Protocol gán nhãn + QA: `dataset/annotation_protocol.md`
- Schema nhãn text: `dataset/text_data/label_schema.md`
- Template báo cáo thống kê: `dataset/reports/dataset_report_template.md`
- Script chuẩn hóa/split ảnh: `scripts/prepare_image_dataset.py`
- Script chuẩn hóa/split text: `scripts/prepare_text_dataset.py`
- Runbook thao tác: `scripts/RUN_DATASET_PIPELINE.md`

### Việc cần làm tiếp theo (ngắn gọn)

1. Điền dữ liệu thật vào `dataset/metadata_template.csv`, lưu thành `dataset/metadata.csv`.
2. Điền dữ liệu thật vào `dataset/text_data/rescue_text_samples_template.csv`, lưu thành `dataset/text_data/rescue_text_samples.csv`.
3. Chạy lệnh trong `scripts/RUN_DATASET_PIPELINE.md` để sinh split và báo cáo.
