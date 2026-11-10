# Chạy trên Windows, dùng lại CUDA từ CT553H

Phiên hiện hành: `local-20261110-04`, hiện **PAUSED sau silver_fusion**.
Pruning, ONNX/PTQ, chẩn đoán lượng tử hóa và CrisisMMD đã hoàn tất.
Lỗi thiếu thư mục `vi_rescue/models` đã được phục hồi có lưu hồ sơ gốc;
cache đặc trưng được kiểm hash và tái sử dụng. Bước tiếp theo là `silver_t2`.
Dùng lệnh ở mục 4 để tiếp tục; không cần setup hoặc chạy lại phần ảnh.
Bằng chứng mới: [local-repair-20261110.json](local-repair-20261110.json).
Kiểm tra pause/resume trước đó: [local-validation-20261110.json](local-validation-20261110.json).

Đã kiểm tra metadata: Python 3.11.9, PyTorch 2.13.0+cu130 trong
`D:\thanhtrong\CT553H\.venv`; nvidia-smi báo RTX 5060 Laptop 8 GB.
Đã thực thi CUDA/pruning, ONNX/PTQ và pipeline public. Silver fine-tuning
và pipeline synthetic còn chờ chạy tiếp.

## 1. Chuẩn bị môi trường (người dùng tự chạy)

Mở PowerShell:

```powershell
cd D:\thanhtrong\notebook_bundle
& D:\thanhtrong\CT553H\.venv\Scripts\python.exe -X utf8 .\local_runner.py setup
& .\.venv-local\Scripts\python.exe -X utf8 .\local_runner.py doctor
```

`setup` tạo `.venv-local`, thêm đường dẫn đọc thư viện CT553H, cài các thư viện
của bộ notebook vào môi trường riêng. Không sửa CT553H, không cài lại Torch,
CUDA Toolkit hoặc driver. Có tải torchvision và các thư viện bổ sung; Internet
cần cho bước này. Resolver torchvision chạy `--no-deps`, kiểm yêu cầu Torch
khớp bản đang có rồi mới cài. Với Torch 2.13.0+cu130, script ghim torchvision
0.28.0+cu130 (đã kiểm metadata wheel Windows Python 3.11), tránh bản mới nhất
0.29.1 vốn yêu cầu Torch >=2.14.0. Có thể chỉ rõ phiên bản khác bằng
`setup --torchvision-version <phiên-bản-tương-thích>`; metadata vẫn được kiểm.
Không bỏ qua lỗi này bằng cách cài đè Torch vào CT553H.

`doctor` kiểm phiên bản, đường dẫn Torch, một phép tính CUDA nhỏ và toán tử
torchvision NMS. Đây là kiểm môi trường, không phải xác nhận toàn bộ pipeline
tương thích. Môi trường dùng lại Torch 2.13/cu130 khác profile gốc 2.7.1/cu128;
các bước ONNX/PTQ/QAT và adapter cũ vẫn cần được kiểm chứng khi chạy thực tế.
Nếu cần sửa dependency hoặc code sau lỗi, giữ run cũ và dùng RUN_ID mới.

## 2. Bắt đầu chạy

Dự phòng khoảng 30 GB ổ trống. Chưa cần mở Jupyter:

```powershell
& .\.venv-local\Scripts\python.exe -X utf8 .\local_runner.py run --run-id local-20261110-04
```

Lệnh này mới kiểm hash/giải nén ZIP vào `local-work/local-20261110-04`, khóa
cấu hình/môi trường, thực hiện các stage theo thứ tự notebook. Để terminal mở.
Giữ cấu hình gốc: pruning 5/10/20%, tối đa 35 epoch, batch 8; baseline mới,
QAT mới và PTE tắt; public, silver/T2 và synthetic frozen bật. Không chạy đồng
thời tác vụ GPU nặng từ CT553H để tránh tranh VRAM.

## 3. Dừng có lưu trạng thái

Mở **PowerShell thứ hai**:

```powershell
cd D:\thanhtrong\notebook_bundle
& .\.venv-local\Scripts\python.exe -X utf8 .\local_runner.py pause --run-id local-20261110-04
& .\.venv-local\Scripts\python.exe -X utf8 .\local_runner.py status --run-id local-20261110-04
```

Đây là yêu cầu dừng an toàn, không dừng tức thời:

- Trong pruning: đợi hết train + validation của epoch, ghi nguyên tử
  `last_training.pt` rồi dừng; lưu model, optimizer, scheduler, AMP scaler,
  RNG và lịch sử. Epoch cuối/early-stop sẽ hoàn tất ratio trước khi dừng.
- Các stage khác: đợi xong **toàn bộ stage hiện tại** rồi dừng. Silver T2 có
  thể cần chờ cả sáu phiên; script chưa thêm resume giữa epoch cho nhánh đó.
- Chờ terminal chạy kết thúc và trạng thái `PAUSED` trước khi tắt máy.
  Lệnh pause trả về chỉ xác nhận đã gửi yêu cầu. Không dùng Ctrl+C, đóng
  terminal hoặc End Task nếu cần tiếp tục an toàn. Mất điện/kill giữ được
  checkpoint đã ghi trước đó nhưng không tự biến run lỗi thành run resume.

## 4. Tiếp tục

Chạy lại đúng lệnh và RUN_ID:

```powershell
& .\.venv-local\Scripts\python.exe -X utf8 .\local_runner.py run --run-id local-20261110-04
```

Các stage/ratio hoàn tất được kiểm hash rồi bỏ qua. Stage pruning `PAUSED`
có thể tiếp tục từ checkpoint; receipt lần pause được lưu trong `local-control`.
Stage `FAILED` hoặc `RUNNING` còn sót vẫn bị từ chối tự retry theo quy tắc gốc.
Không sửa receipt, input hoặc config để ép tiếp tục. Thay đổi CT553H cũng có
thể đổi môi trường dùng chung; đừng cập nhật môi trường đó trong campaign này.

## Nơi lưu

- Trạng thái: `local-work/local-20261110-04/local-control/state.json`.
- Log/metrics: `local-work/local-20261110-04/bundle-results/`.
- Checkpoint: `bundle-results/image_pruning/ratio-0.050/last_training.pt`
  (tương tự `ratio-0.100`, `ratio-0.200`).
- ZIP kết quả: `local-work/local-20261110-04-results.zip`, cập nhật sau mỗi stage
  và khi dừng an toàn; giữ cả project để resume, không chỉ giữ ZIP.
- Nếu stage lỗi: xem `bundle-results/<stage>/stage.json` và các file `.log`.
  Không tự xóa lock khi còn process. Nếu bị kill và lock còn sót, cần kiểm
  tra PID trước; runner cố ý không tự phá khóa hoặc tự phục hồi run lỗi.

Kết quả synthetic vẫn chỉ là kiểm pipeline trên ảnh–câu ghép tùy ý, không phải
bằng chứng dữ liệu tiếng Việt gold hoặc hiệu quả cứu hộ thực tế.
