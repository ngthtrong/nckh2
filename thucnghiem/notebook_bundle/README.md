# Bộ notebook và ZIP dữ liệu NCKH2

## Material Passport

- Origin: repository-native experiment packaging, academic-research-suite guidance.
- Status: **PACKAGING / chưa chạy huấn luyện trên GPU**. Xem `validation.json` trong bộ phát hành để biết các kiểm tra thực sự đã thực hiện.
- Scope: tạo một notebook điều khiển, các ZIP dữ liệu/trọng số và mã chạy cách ly. Không sửa báo cáo, app, dữ liệu hoặc kết quả nghiên cứu gốc; không upload hay công bố.
- Native Vietnamese/human gold: **DATA_NOT_READY**. Kiến nghị phát triển của Hội đồng: **CONTENT_ONLY**, không thực thi.
- Bộ ảnh ghép tùy ý với câu tự soạn: **DATA_READY / SYNTHETIC_UNPAIRED**, chỉ phục vụ kiểm tra kỹ thuật theo yêu cầu bổ sung của người dùng.

## Tệp bàn giao

Chạy bộ sinh sẽ tạo trong `dist/`:

| Tệp | Nội dung |
|---|---|
| `NCKH2_All_In_One.ipynb` | Notebook duy nhất, gồm cấu hình, kiểm ZIP/hash, môi trường riêng, các bước chạy và xuất kết quả |
| `00_runtime.zip` | Bản sao mã nguồn được whitelist, protocol đầu vào, dự đoán lịch sử và các adapter |
| `01_flood_images.zip` | 1.702 ảnh, split 1.189/257/256, config seed 1024 |
| `02_crisis_public.zip` | 4.261 cặp CrisisMMD, 4.309 ảnh tải lịch sử và metadata cần kiểm lại nguồn; split 2.971/589/701 |
| `03_vi_silver.zip` | 300 cặp được chọn, 296 dùng học (179/58/59), bốn ca uncertain, bản dịch/nhãn AI và hồ sơ nguồn |
| `04_models.zip` | Baseline ảnh seed 1024, ONNX FP32/PTQ/QAT lịch sử, checkpoint QAT, DistilBERT và hai encoder ImageNet đã ghim hash |
| `05_vi_synthetic.zip` | 1.702 cặp ảnh–câu tự soạn; dùng lại ảnh ở ZIP 01, nhãn từ khuôn câu; trạng thái DATA_READY cho kiểm tra kỹ thuật |
| `bundle-index.json` | SHA-256 và kích thước ZIP; cùng giá trị đã nhúng trong notebook |
| `synthetic-readiness.json` | Số cặp/lớp/split và phạm vi SYNTHETIC_UNPAIRED; không phải xác nhận native gold |

ZIP chỉ được tạo local. Ảnh mức ngập chưa có giấy phép từng ảnh; các gói không phải bản phát hành dữ liệu mở. Chỉ chuyển sang môi trường khác trong phạm vi quyền sử dụng thực tế; không đăng ZIP chứa dữ liệu thành Kaggle Dataset công khai.

## Cách chạy

1. Dùng Python 3.10–3.12. Dự phòng khoảng 30 GB ổ đĩa cho môi trường CUDA, inputs, checkpoint và ZIP kết quả; lượng thực tế phụ thuộc số checkpoint được chọn.
2. **Kaggle:** đính kèm sáu ZIP dưới dạng input riêng tư, chọn GPU, bật Internet để cài thư viện. **Colab:** chép ZIP vào `/content` hoặc một thư mục Drive được mount; đặt `ARCHIVE_DIR` tới thư mục chứa ZIP. **Laptop:** đặt notebook và ZIP cùng thư mục; khuyến nghị WSL2/Linux với driver CUDA phù hợp.
3. Mở notebook. Xem ô `CONFIG`; tỷ lệ cắt tỉa đề xuất là 5/10/20%, tối đa 35 epoch. Cấu hình được khóa theo `RUN_ID` trước chạy. Các tỷ lệ này chưa phải một protocol nghiên cứu được Hội đồng phê duyệt.
4. `Run all`. Notebook tạo môi trường riêng `gpu-env-torch271-cu128-v1`, cài PyTorch 2.7.1 + torchvision 0.22.1 từ cu128 và các dependency đã pin; không cài vào môi trường báo cáo/app. Cần Internet cho pip, không cần tải lại model/dataset.
5. Kết quả được lưu trong `<WORK_ROOT>/<RUN_ID>/bundle-results/`; `<RUN_ID>-results.zip` được cập nhật sau mỗi bước, kể cả khi bước lỗi. Tải ZIP kết quả và notebook đã chạy.

PyTorch 2.7 giới thiệu hỗ trợ Blackwell/CUDA 12.8; cặp wheel 2.7.1/0.22.1 có trong [hướng dẫn chính thức](https://pytorch.org/get-started/previous-versions/), [release note](https://pytorch.org/blog/pytorch-2-7/). Có CUDA driver không đồng nghĩa model đã chạy GPU: preflight thực thi một phép tính CUDA nhỏ và ghi device/capability/VRAM thực tế.

## Các bước và giới hạn

- **Ảnh:** dùng nguyên split/hash; ba cấu hình cắt tỉa chỉ được xem validation khi lựa chọn. Sau khi khóa cấu hình mới xuất ONNX và so sánh baseline với model được chọn trên test cũ. McNemar, macro-F1/CI theo nhóm split và lỗi nặng được lưu riêng.
- **PTQ:** calibration từ train; test chỉ đánh giá cấu hình đã khóa. **QAT mới** mặc định `run_qat=False`: chỉ bật khi chẩn đoán cho thấy cần huấn luyện lại. Nếu tắt, phần phân tích vẫn dùng QAT lịch sử và ghi rõ nguồn.
- **Chẩn đoán lượng tử hóa:** confusion/lỗi từng lớp từ test, cộng kiểm tensor trên một ảnh validation xác định trước. Báo số tensor ghép được; QAT có thể không ghép được tên tensor. Đây là diagnostic có phạm vi, không tự chứng minh nguyên nhân nhân quả hay độ an toàn triển khai. API theo [ONNX Runtime](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html).
- **Baseline ảnh mới** mặc định `run_baseline=False`: bộ đã có checkpoint baseline. Khi bật, khởi tạo từ ImageNet, dùng split hiện tại; kết quả ở nhánh riêng, không âm thầm thay source của pruning/PTQ/QAT.
- **CrisisMMD:** features frozen + TF-IDF/LR + fusion, cùng target informative. **Silver:** frozen DistilBERT/Large + LR/fusion, sáu phiên fine-tuning DistilBERT trên CUDA, kiểm backbone thực sự đổi trọng số, metrics/CI từ prediction đã lưu.
- Các pilot cũ giữ nguyên số mẫu, nhãn và nhiệm vụ. Test cũ đã được xem: các phiên chạy lại là **development replay**, không phải xác nhận độc lập.
- **Bộ tự soạn mới:** dùng toàn bộ 1.702 ảnh trong split cũ (1.189/257/256), xáo trộn tất định rồi ghép câu tiếng Việt từ các khuôn tự soạn, không xem nội dung ảnh để viết câu hoặc gán request/no_request. Nội dung câu không gắn tiền tố đánh dấu; nguồn gốc được giữ trong metadata và hồ sơ chạy. Giữ nhóm ảnh; dùng khuôn câu riêng cho train/dev/test. Các trường `event_name` chỉ chứa ID phân vùng giả lập, không phải sự kiện thiên tai. Không có người gán độc lập hay IAA.
- **Trạng thái DATA_READY của bộ tự soạn** chỉ xác nhận tệp, ID, hash, nhãn khuôn câu và split sẵn sàng cho kiểm tra pipeline. `run_synthetic=True` mặc định chạy features frozen và các head NLP/fusion trong thư mục riêng; `run_synthetic_t2=False` mặc định để tránh thêm sáu phiên GPU, có thể bật trong CONFIG. Các JSON đầu ra đều giữ `SYNTHETIC_UNPAIRED`, `TECHNICAL_PIPELINE_TEST_ONLY`, `native_gold=false`. Metric của bộ này không xác nhận NLP hoặc fusion cứu hộ thực tế.
- **NLP/fusion tiếng Việt gốc và test camera độc lập:** chưa có dữ liệu/nhãn, được ghi `DATA_NOT_READY`; `native_templates/` chỉ chứa schema trống. Chưa có runner native-gold được phê duyệt; thêm file vào template không tự mở nhánh đó.
- **Android/SMS/mạng thật/pin/RAM:** `REQUIRES_DEVICE`. Notebook không tạo bằng chứng giả lập thay thiết bị thật.
- **PTE:** ONNX được xuất trong nhánh chính. `run_pte=False` mặc định. Nếu cần PTE, chuẩn bị interpreter riêng có ExecuTorch 1.4.1 tương thích và đặt `pte_python`; notebook không cài ExecuTorch đè lên môi trường GPU. PTE mới vẫn cần kiểm thử trên điện thoại.
- Không chạy thiết kế lịch điều phối có chi phí di chuyển, không thu ảnh thực địa hoặc tổ chức thử nghiệm thực địa: các mục này chỉ thuộc Hướng phát triển theo chỉ đạo người dùng.

## Chạy lại, lỗi và provenance

- Mỗi `RUN_ID` là một project mới; dữ liệu/mô hình lịch sử được giải nén vào project đó, không ghi vào checkout gốc.
- Dùng lại cùng `RUN_ID` và CONFIG để bỏ qua các bước đã `COMPLETED` sau khi kiểm hash output. Đổi dữ liệu hoặc cấu hình cần `RUN_ID` mới.
- Không tự retry một bước `FAILED`/`RUNNING` còn sót. Giữ log/checkpoint/ZIP; chọn `RUN_ID` mới để chạy lại sau khi xử lý nguyên nhân. Script pruning gốc vẫn có checkpoint `last_training.pt` và `--resume` cho phục hồi thủ công trong đúng môi trường; notebook không nhận đó là một bước hoàn thành.
- Nhật ký chứa command, exit code, timeout, môi trường, hash input/code/output. Không trộn số liệu của nhiều run hoặc thay số trong báo cáo tự động.
- Các adapter nằm **trong ZIP**, không sửa script gốc: thêm `--defer-test` cho pruning; ghim snapshot DistilBERT local; chuyển T2 sang CUDA; nối seed QAT mới với config; tạo namespace riêng cho pipeline tự soạn. `toolkit/source-adaptations.json` giữ hash trước/sau và mô tả từng đổi.
- McNemar cần các đơn vị cặp độc lập; phụ thuộc nguồn/sự kiện của bộ ảnh vẫn chưa xác minh. CI theo `split_group` không biến chúng thành sự kiện độc lập; Holm áp dụng cho họ tương phản McNemar đã liệt kê, CI macro-F1 chưa hiệu chỉnh.

## Tái tạo bộ bàn giao và kiểm tra local

Từ gốc repo:

```bash
python3 -m unittest discover -s thucnghiem/notebook_bundle -p 'test_*.py'
# Nếu Python chuẩn không có NumPy/sklearn, dùng venv nghiên cứu hiện có cho unit tests.
python3 thucnghiem/notebook_bundle/build.py
python3 thucnghiem/notebook_bundle/validate.py --bundle-dir thucnghiem/notebook_bundle/dist
```

`build.py` từ chối thư mục output đã tồn tại; dùng `--output` khác cho một phiên bản mới. `validate.py` chỉ đọc ZIP/hash, giải nén vào thư mục tạm và chạy preflight file; không cài thư viện, không inference, không training, không dựng PDF và không upload.
