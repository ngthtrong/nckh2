# NLP/fusion trên tiếng Việt dịch và nhãn AI

Pipeline CPU thực nghiệm riêng cho task `vi_translated_silver_request_v1`. Văn bản CrisisMMD được Codex assistant/native subagents dịch và gán một nhãn request/no_request/uncertain từ câu nguồn; ảnh giữ cùng cặp. Không gọi đây là dữ liệu người Việt gửi tin, nhãn người độc lập hoặc gold chuyên gia. Không sửa gate tiếng Việt có người gán của pipeline cũ.

Kết quả và protocol: [gói bằng chứng](../../docs/revision-plan/outputs/vi-nlp-fusion-silver-20261108/analysis.md). Raw/bản dịch/nhãn/trọng số/cache giữ local dưới các đường dẫn được ignore; không tự công bố hoặc commit/push.

## Môi trường

`.venv/` là venv riêng có Transformers 4.46.3 và tokenizer; thư viện CPU đã có được dùng qua `.pth` chỉ đọc từ môi trường `multimodal/.venv/`. Không phải môi trường hermetic độc lập hoàn toàn. `requirements-lock.txt` và environment receipt ghi phiên thực tế; không cài hoặc thay dependency sản phẩm/report. Model được tải một lần từ repo chính thức, pin revision/hash; inference CLI dùng local_files_only và weight đã kiểm.

## Các bước đã triển khai

- `assemble.py`: kiểm ID/bản dịch/nhãn, hash ảnh, giữ uncertain và khóa corpus trước fit.
- `features.py`: frozen DistilBERT 768 + MobileNetV3-Large 960 chiều, CPU 4 threads, L2; không fine-tuning ở bước này.
- `train.py`: 18 fit head với train-only vocabulary và dev-only selection; T0/T1/I0/F0/F1.
- `fine_tune.py`: addendum riêng, 2 learning rate × 3 seed, tối đa 5 epoch/patience 2; full encoder; freeze trước test.
- `evaluate.py`: 9 cấu hình frozen cùng ID, giữ probability full precision rồi tính metric/CI 2.000 draw.
- `verify_encoder_update.py`: đối chiếu tensor backbone của ba checkpoint được chọn với pretrained; xác nhận có cập nhật encoder.
- `verify.py`: công thức confusion/metric độc lập, replay CI và kiểm T2 nếu đã đủ receipt.
- `test_contracts.py`: fixture tạm chỉ kiểm kỹ thuật, không phải corpus hoặc hiệu năng nghiên cứu.
- `predict.py`: chọn frozen F1 khi đủ ảnh/câu, T1 hoặc I0 khi thiếu một nguồn. Output LOCAL_AI_SILVER_RESEARCH_ONLY, không trả trường urgency/E/priority. Chính sách chọn nhánh chưa xác nhận vận hành.

Từ gốc repo, lệnh thực tế (chỉ chạy trên workspace mới hoặc phiên có output mới; các artifact đã tồn tại sẽ bị từ chối ghi đè):

```bash
thucnghiem/vi_rescue/.venv/bin/python thucnghiem/vi_rescue/run_step.py verify_dataset -- thucnghiem/vi_rescue/.venv/bin/python -c 'import sys; sys.path.insert(0,"thucnghiem/vi_rescue"); from common import load_data; print(len(load_data()))'
thucnghiem/vi_rescue/.venv/bin/python thucnghiem/vi_rescue/test_contracts.py
HF_HUB_DISABLE_XET=1 thucnghiem/vi_rescue/.venv/bin/python thucnghiem/vi_rescue/run_step.py features -- thucnghiem/vi_rescue/.venv/bin/python thucnghiem/vi_rescue/features.py
thucnghiem/vi_rescue/.venv/bin/python thucnghiem/vi_rescue/run_step.py train -- thucnghiem/vi_rescue/.venv/bin/python thucnghiem/vi_rescue/train.py
thucnghiem/vi_rescue/.venv/bin/python thucnghiem/vi_rescue/run_step.py --timeout 1800 fine_tune_cpu -- thucnghiem/vi_rescue/.venv/bin/python thucnghiem/vi_rescue/fine_tune.py
thucnghiem/vi_rescue/.venv/bin/python thucnghiem/vi_rescue/run_step.py evaluate -- thucnghiem/vi_rescue/.venv/bin/python thucnghiem/vi_rescue/evaluate.py
thucnghiem/vi_rescue/.venv/bin/python thucnghiem/vi_rescue/run_step.py encoder_update -- thucnghiem/vi_rescue/.venv/bin/python thucnghiem/vi_rescue/verify_encoder_update.py
thucnghiem/vi_rescue/.venv/bin/python thucnghiem/vi_rescue/run_step.py verify -- thucnghiem/vi_rescue/.venv/bin/python thucnghiem/vi_rescue/verify.py
```

Trong lần gốc, addendum T2 đã được ghi trước dự đoán test frozen; T2 chạy sau khi head frozen đã được chọn, không thay tương phản chính. Lệnh có `--timeout` phải đặt cờ trước tên bước do argparse REMAINDER. Hai wrapper đầu có lỗi receipt sau khi child tạo artifact; xem receipt-issue.md. Receipt cũ được giữ, artifact được kiểm riêng, không gọi mọi command lịch sử đều exit0.

Các script cố định scope/path của phiên pilot này. Đây chưa phải pipeline tổng quát `--task/--data-root/--output-dir` của nghiên cứu native-gold; mở phiên khác phải tạo protocol/path mới, không sửa state/hash để vượt khóa.
