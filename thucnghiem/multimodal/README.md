# Benchmark đa phương thức bổ trợ, tách biệt khỏi nguyên mẫu cứu hộ

Pipeline CPU cho CrisisMMD agreed-label informativeness: một event test riêng, một event validation riêng, cùng test IDs cho ảnh/text/fusion. Nhánh ảnh dùng MobileNetV3 Small ImageNet frozen; nhánh text dùng TF-IDF từ câu tự do; classifier kết hợp là LR học trên nối đặc trưng. Không dùng nhãn OR của biểu mẫu, không đổi RQ1–RQ3, không nối informativeness vào urgency.

Protocol, số liệu và trạng thái thực chạy: [gói bằng chứng](../../docs/revision-plan/outputs/multimodal-20261108/README.md). Thông tin nguồn/giới hạn: [research.md](../../docs/revision-plan/outputs/multimodal-20261108/research.md). Các script cố ý từ chối ghi đè selection, cache, model hoặc test result có sẵn; tái lập ở checkout/thư mục dữ liệu riêng, giữ raw lần đầu.

## Môi trường đã dùng

Python 3.12; `requirements.txt` và `requirements-lock.txt`; PyTorch CPU 2.5.1, torchvision 0.20.1. Không cài dependency vào môi trường report hoặc sửa dependency sản phẩm.

```bash
python3 -m venv thucnghiem/multimodal/.venv
thucnghiem/multimodal/.venv/bin/python -m pip install -r thucnghiem/multimodal/requirements.txt
thucnghiem/multimodal/.venv/bin/python -m pip install torch==2.5.1+cpu torchvision==0.20.1+cpu --index-url https://download.pytorch.org/whl/cpu
```

## Thứ tự thực hiện

Chỉ `prepare.py` tải nguồn và ảnh công khai; các bước sau dùng dữ liệu local. `features.py` có thể tải trọng số từ PyTorch nếu cache trống. Không upload nội dung.

```bash
thucnghiem/multimodal/.venv/bin/python thucnghiem/multimodal/prepare.py
thucnghiem/multimodal/.venv/bin/python thucnghiem/multimodal/features.py
thucnghiem/multimodal/.venv/bin/python thucnghiem/multimodal/train.py
thucnghiem/multimodal/.venv/bin/python thucnghiem/multimodal/evaluate.py
thucnghiem/multimodal/.venv/bin/python thucnghiem/multimodal/verify.py
thucnghiem/multimodal/.venv/bin/python thucnghiem/multimodal/test_contracts.py
```

Để có receipt command/exit/timeout/hash tại thời điểm chạy, bọc từng lệnh bằng `run_step.py STEP_NAME -- COMMAND...`. Timeout mặc định 60 phút; không tự thử lại một bước thí nghiệm lỗi. Khi lỗi, giữ log/receipt, xác định nguyên nhân và đặt tên bước sửa riêng.

```bash
thucnghiem/multimodal/.venv/bin/python thucnghiem/multimodal/predict.py \
  --language en --text 'Local research example; no operational claim' \
  --image /absolute/path/to/an/authorized/image.jpg
```

CLI chọn classifier text/image/fusion theo đầu vào còn có; nhánh đơn không được xem là đã xác nhận khả năng chịu thiếu modality của fusion. `--language vi` bị chặn vì artifact chưa có đánh giá tiếng Việt. Đầu ra gắn task `public_crisis_informativeness`, `LOCAL_RESEARCH_ONLY` và không cung cấp trường E/urgency/rank. Chưa có HTTP service hay ứng dụng được triển khai mới.

## Dữ liệu và artifacts

`data/`, `cache/`, `features/`, `models/`, `.venv/` đều ignore; giữ local, không tự công bố. Gói evidence giữ hash, split/selection, metrics, full-precision predictions, CI và provenance. Models dùng joblib của chính lần chạy, kiểm hash trước nạp. Không nạp model từ nguồn không xác định.

Bộ tiếng Việt nằm trong [annotation-kit](../../docs/revision-plan/outputs/multimodal-20261108/annotation-kit/README.md). Mẫu gán nhãn hiện trống; gate `validate_vi_intake.py` trả NO_GO khi chưa có dữ liệu/nhãn/target approval. Tests dùng fixture tổng hợp trong thư mục tạm, không đưa vào dữ liệu huấn luyện hoặc bảng kết quả.
