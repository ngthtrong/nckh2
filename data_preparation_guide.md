# QUY TRÌNH CHUẨN BỊ DỮ LIỆU (DATA PREPARATION)

> Hướng dẫn chuẩn bị dữ liệu đa phương thức (Hình ảnh & Văn bản) cho đề tài:  
> *"Hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI"*

Một trong những phần quan trọng nhất quyết định độ chính xác của AI là chất lượng dữ liệu. Do đặc thù chạy trên biên (Edge) và ngữ cảnh Việt Nam, dữ liệu cần được tuyển chọn và tối ưu kỹ lưỡng.

---

## 1. NHÁNH HÌNH ẢNH (Image Classification)

### 1.1. Mục tiêu phân loại (Gợi ý Label)
Cần định nghĩa rõ ràng các nhãn (classes) mà hệ thống sẽ nhận diện. Khuyến nghị 2 tác vụ chính:
- **Tác vụ 1: Mức độ ngập lụt (Water Level)**
  - `no_flood` (Không ngập)
  - `low_flood` (Ngập nhẹ - dưới đầu gối / mặt đường)
  - `high_flood` (Ngập nặng - lút nhà, cần cứu hộ gấp)
- **Tác vụ 2: Mức độ thiệt hại (Damage Level)**
  - `none` (Không thiệt hại)
  - `mild` (Thiệt hại nhẹ - tốc mái một phần, cây cối ngã đổ)
  - `severe` (Thiệt hại nặng - sập nhà, sạt lở)

### 1.2. Nguồn thu thập
1. **Dữ liệu mở:** 
   - **FloodNet:** Chứa ảnh chụp từ trên cao, có nhãn ngập lụt. (Lưu ý: góc chụp từ trên cao có thể khác với ảnh người dân chụp ngang).
   - **CrisisMMD:** Dữ liệu đa phương thức từ Twitter về các thảm họa.
2. **Dữ liệu Việt Nam (Web Crawling):**
   - Thu thập ảnh từ các bài báo, mạng xã hội (Facebook, Zalo) trong các đợt bão lũ (VD: bão Yagi, lũ lụt miền Trung).
   - *Lý do:* Kiến trúc nhà cửa, bối cảnh nông thôn/đô thị Việt Nam khác với phương Tây, cần dữ liệu này để fine-tune.

### 1.3. Tiền xử lý (Preprocessing) phù hợp với Edge AI
Do model sẽ chạy trên điện thoại qua TFLite/ONNX:
- **Resize ảnh:** Resize toàn bộ ảnh về kích thước cố định mà model yêu cầu (VD: `224x224` hoặc `320x320`). Không nên để model trên mobile tự resize vì tốn computation.
- **Normalization:** Chuẩn hóa pixel value về `[0, 1]` hoặc `[-1, 1]` chuẩn ImageNet.
- **Data Augmentation (Rất quan trọng):**
  - *Mô phỏng đục mờ/mưa rào:* Thêm nhiễu (noise), làm mờ (blur) để mô phỏng ảnh chụp bằng điện thoại giá rẻ hoặc trong lúc trời đang mưa bão.
  - *Mô phỏng thiếu sáng:* Random brightness/contrast cho các ảnh chụp ban đêm hoặc cúp điện.
  - *Các phép biến đổi cơ bản:* Horizontal/Vertical Flip, Random Crop, Rotation.

---

## 2. NHÁNH VĂN BẢN (Text Classification)

### 2.1. Mục tiêu phân loại (Gợi ý Label)
- **Tác vụ: Phân loại mức độ khẩn cấp (Urgency / Intent)**
  - `urgent_rescue` (Cần cứu hộ KHẨN CẤP: có người già, trẻ em, nước lên nhanh, cạn kiệt thức ăn).
  - `need_supplies` (Cần tiếp tế: cần thức ăn, áo phao, sạc điện thoại - chưa đe dọa trực tiếp tính mạng).
  - `safe_update` (Thông báo an toàn, cập nhật tình hình địa phương).
  - `irrelevant` (Tin rác, không liên quan đến cứu hộ).

### 2.2. Nguồn thu thập
1. **Dữ liệu nền tảng:** Bộ **UIT-VSMEC** (giúp model hiểu cách diễn đạt cảm xúc, từ ngữ tiếng Việt chung).
2. **Dữ liệu mạng xã hội (Cốt lõi):**
   - Lọc và thu thập các post, comment có chứa từ khóa: *"cứu với", "ngập lút", "mất điện", "trẻ em", "hết thức ăn"*,...
   - Có thể sử dụng các file tổng hợp Excel của các nhóm tình nguyện viên cứu trợ mùa lũ.

### 2.3. Tiền xử lý (Preprocessing) cho Tiếng Việt
Tin nhắn cứu hộ thường rất lộn xộn, viết vội, sai chính tả:
- **Chuẩn hóa Text:**
  - Chuyển `lower_case`.
  - Loại bỏ PII (Personal Identifiable Information) như SĐT, số tài khoản ngân hàng để bảo mật.
  - Loại bỏ các Emoji không mang ý nghĩa, HTML tags, Links.
- **Xử lý ngôn ngữ mạng / Teencode / Viết tắt:**
  - Xây dựng từ điển quy đổi: `ko, k -> không`, `dc -> được`, `cc -> cấp cứu`, `mn -> mọi người`.
- **Word Segmentation (Tách từ):**
  - RẤT QUAN TRỌNG cho tiếng Việt. Sử dụng `pyvi` hoặc `VnCoreNLP` (hoặc tokenizer tích hợp sẵn của PhoBERT là bpe/sentencepiece) để ghép các từ ghép (VD: `cứu_hộ`, `lũ_lụt`).

### 2.4. Data Augmentation cho Text (Khó nhưng cần thiết)
- Tính đa dạng của text cứu hộ khá thấp, dễ overfit.
- **Kỹ thuật:**
  - *Synonym Replacement:* Thay thế ngẫu nhiên bằng từ đồng nghĩa (VD: `nước ngập` -> `nước dâng`).
  - *Back-translation:* Dịch Việt -> Anh -> Việt để tạo ra câu mới cùng ngữ nghĩa. (Dùng Google Translate API).
  - *Mô phỏng sai chính tả:* Xóa dấu ngẫu nhiên (VD: `cứu mọi người` -> `cuu moi nguoi`) để model quen với tin nhắn gõ vội không dấu.

---

## 3. CẤU TRÚC LƯU TRỮ DỮ LIỆU ĐỂ HUẤN LUYỆN

Sắp xếp thư mục chuẩn chỉnh giúp việc code DataLoader dễ dàng hơn:

```text
dataset/
│
├── image_data/
│   ├── train/
│   │   ├── high_flood/ (chứa các file img_001.jpg, ...)
│   │   ├── low_flood/
│   │   └── no_flood/
│   ├── val/
│   └── test/
│
└── text_data/
    ├── train.csv (các cột: id, raw_text, clean_text, urgency_label)
    ├── val.csv
    └── test.csv
```

---

## 4. CÔNG CỤ HỖ TRỢ GÁN NHÃN (ANNOTATION)

Nhóm nghiên cứu có thể dùng các tool sau để tăng tốc độ gán nhãn:
- **Label Studio (Khuyên dùng):** Hỗ trợ gán nhãn cho cả Image và Text trên cùng một nền tảng. Có thể cài đặt local miễn phí.
- **CVAT:** Nếu sau này muốn mở rộng làm Object Detection.
- **Google Sheets:** Cách đơn giản, hiệu quả nhất để các thành viên cùng phân loại Text.

## 5. MỘT SỐ LƯU Ý KHI LÀM BÁO CÁO NCKH VỀ DATA

Khi viết báo cáo, Hội đồng đánh giá sẽ rất quan tâm đến các điểm sau, hãy ghi chú lại:
1. **Quy mô bộ dữ liệu (Size):** Bao nhiêu ảnh? Bao nhiêu câu text?
2. **Kịch bản mất cân bằng dữ liệu (Imbalanced Data):** Thường số tin rác/không ngập luôn nhiều hơn tin khẩn cấp. Bạn xử lý thế nào? (Dùng Class Weights trong hàm Loss, Focal Loss, hay Oversampling?).
3. **Độ tin cậy của nhãn (Inter-annotator agreement):** Nếu cùng 1 bức ảnh/tin nhắn mà 2 thành viên gán nhãn khác nhau thì giải quyết ra sao? (Nên có cơ chế majority voting nếu gán nhãn chéo).
