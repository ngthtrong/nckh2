# Bộ chuẩn bị gán nhãn tiếng Việt

## Material Passport

- Origin: academic-research-suite / experiment-agent, plan.
- Date: 2026-11-08, Asia/Taipei.
- Status: DRAFT_NOT_EXPERT_VALIDATED; chưa có người gán nhãn/chuyên gia theo xác nhận người dùng.

Hai CSV chỉ có header, **0 dữ liệu và 0 nhãn**. Không điền câu sinh tự động, bản dịch hay cờ biểu mẫu vào dữ liệu thật. Không coi benchmark tiếng Anh là đánh giá tiếng Việt.

## Nhiệm vụ cần xác nhận trước khi thu nhãn

Đề xuất: phân loại mức ưu tiên **người trực xem xét một báo cáo**, dựa trên ảnh và mô tả cùng nguồn. Đây chưa phải mức nguy hiểm thực tế, nhãn lâm sàng hay lệnh điều phối. Chuyên gia/đơn vị phụ trách phải xác nhận định nghĩa, thông tin đủ để phán đoán, các mức nhãn, xử lý thiếu thông tin và quyền dùng dữ liệu. Lưu quyết định có người chịu trách nhiệm; Agent không ký thay.

Nếu chọn nhiệm vụ hẹp hơn như “báo cáo có thông tin hữu ích cho ứng phó lũ”, cần định nghĩa và nhãn riêng. Không đổi tên informative thành khẩn cấp. Trường hợp không đủ bằng chứng phải được ghi nhận, không ép vào lớp ít khẩn cấp nhất.

## Thu nhận và nguồn

- Một `report_id` gắn mô tả và ảnh thực sự đi cùng báo cáo; có `event_id`, `source_id`, URL hoặc hồ sơ nguồn, thời điểm và cơ sở cho phép sử dụng.
- `usage_basis` ghi căn cứ sử dụng thực tế; CSV không tự cấp quyền. `privacy_review_ref` dẫn hồ sơ xử lý thông tin riêng tư. Giữ dữ liệu thô ở nơi được phép, không tự công khai tên, số điện thoại hoặc vị trí hộ gia đình.
- Chụp SHA256 ảnh; ghi bản nào đã biên tập/ẩn danh. Ảnh minh họa báo chí và ảnh người gửi không được mặc định có cùng mức chứng cứ.
- Giữ cả ảnh/text bất đồng, thiếu modality và nhãn không chắc chắn trong sổ thu nhận. Mẫu có cả hai nguồn để so ablation phải được định nghĩa trước; không chỉ chọn mẫu mô hình dễ đoán.

## Gán nhãn và kiểm chất lượng

1. Chốt guideline với chuyên gia; thực hiện pilot nhỏ để phát hiện định nghĩa mơ hồ. Số pilot là quyết định tổ chức, chưa phải cỡ mẫu khoa học đủ.
2. Hai người gán độc lập, không xem prediction, công thức fusion, nhãn của nhau hoặc giá trị xếp hạng hiện tại. `stage=independent`, `label_origin=human`; lưu uncertainty và dẫn chứng.
3. Tính tỷ lệ đồng thuận và Cohen kappa; nếu nhãn thứ bậc, báo weighted kappa cùng cách chọn trọng số. Báo phân bố lớp/bất đồng, không dùng một chỉ số duy nhất làm chứng nhận.
4. Phân xử bất đồng bằng người chịu trách nhiệm; thêm hàng `stage=adjudicated` và `evidence_ref`, không xóa hai nhãn độc lập. Các ca chưa phân xử vẫn còn trong inventory.
5. Tách theo sự kiện/nguồn, nối nhóm ảnh gần trùng và text lặp; khóa train/validation/test trước fit. Không đưa test cho nhóm phát triển để chỉnh guideline/model sau khi xem kết quả.
6. Chọn cỡ mẫu và số sự kiện theo phân bố nhãn, sai số chấp nhận và độ bất định của hiệu ứng fusion sau pilot. Không cam kết “vài trăm mẫu là đủ” khi chưa có cơ sở.

## Bằng chứng cần có để mở lại B1/B3/B4/B5

Target/guideline đã xác nhận; bản ghi ghép cặp được phép dùng; ít nhất hai nhãn độc lập và adjudication có truy vết; đánh giá đồng thuận; split/group manifest; các nhánh cùng target và cùng test IDs; protocol model/metric/CI khóa trước test. Cần đánh giá riêng nhánh text bằng nhãn từ text nếu muốn kết luận năng lực đọc văn bản, tránh bắt text đoán phần chỉ có trong ảnh.

Chạy gate cấu trúc (exit 2 hiện tại là kết quả NO_GO dự kiến):

```bash
thucnghiem/multimodal/.venv/bin/python thucnghiem/multimodal/validate_vi_intake.py \
  --records docs/revision-plan/outputs/multimodal-20261108/annotation-kit/records.csv \
  --annotations docs/revision-plan/outputs/multimodal-20261108/annotation-kit/annotations.csv
```

Gate đạt chỉ cho phép review protocol; chưa xác nhận giá trị nhãn hoặc cho phép triển khai cứu hộ. Có thể nghiên cứu baseline TF-IDF tiếng Việt trước; PhoBERT/DistilBERT là lựa chọn cần đối chiếu cam kết, tài nguyên và dữ liệu, không mặc định phải dùng mô hình lớn.
