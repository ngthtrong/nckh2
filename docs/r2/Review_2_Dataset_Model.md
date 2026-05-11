# ĐẶC TẢ DATASET & MODEL — REVIEW 2

**Tham chiếu:** [Đặc tả v2](./Review_2_Spec.md) · [Data Preparation Guide](../data_preparation_guide.md)

---

## 1. Dữ liệu hình ảnh

### 1.1 Nguồn dữ liệu

| Bộ dữ liệu | Kích thước | Nội dung | Xử lý bổ sung |
|------------|-----------|---------|---------------|
| FloodNet | ~2.3K ảnh | Ảnh UAV hậu lũ, nhãn semantic | Remap 10 class → 3 class, fine-tune theo địa hình VN |
| CrisisMMD | ~16K tweet | Ảnh + text mạng xã hội | Lọc nhãn flood, remap damage_severity → 3 class |
| Thu thập nội bộ (VN) | ~5K ảnh | Facebook/Zalo VN, bão lũ 2023–2024 | Gán nhãn thủ công |
| **Tổng** | **~23K** | | |

### 1.2 Label Schema (3 class)

| Nhãn | Định nghĩa | Ví dụ |
|------|-----------|-------|
| `none` | Không có dấu hiệu ngập lụt | Đường phố khô ráo, nhà cửa bình thường |
| `low` | Ngập nhẹ, nước chưa vào nhà | Nước ngập mặt đường, mức nước dưới đầu gối |
| `high` | Ngập nặng, nước dâng cao | Nước ngập nóc nhà, đường phố chìm trong nước |

### 1.3 Tiền xử lý

- Resize: 224 × 224 pixels
- Normalize: ImageNet mean/std
- Augmentation: flip, rotation, color jitter, random crop
- Split: 70% train / 15% val / 15% test (stratified, seed=42)

---

## 2. Dữ liệu văn bản

### 2.1 Nguồn dữ liệu

| Bộ dữ liệu | Kích thước | Nội dung | Xử lý bổ sung |
|------------|-----------|---------|---------------|
| UIT-VSMEC | ~6.9K câu | Dữ liệu cảm xúc tiếng Việt | Remap → 4 nhãn cứu hộ |
| Crawl mạng xã hội | ~10K câu | Facebook/Zalo bão lũ 2020–2024 | Làm sạch, chuẩn hóa Unicode |
| **Tổng** | **~17K** | | |

### 2.2 Label Schema (4 class)

| Nhãn | Định nghĩa | Ví dụ |
|------|-----------|-------|
| `urgent_rescue` | Cầu cứu khẩn cấp, cần giải cứu ngay | "Cứu với! Nước ngập nóc nhà rồi, có 3 người mắc kẹt!" |
| `need_supplies` | Cần nhu yếu phẩm, vật tư cứu trợ | "Cần gạo, mì tôm, nước sạch cho 20 hộ dân" |
| `safe_update` | Cập nhật tình trạng an toàn | "Gia đình tôi đã di chuyển đến nơi an toàn" |
| `irrelevant` | Không liên quan đến cứu hộ | "Thời tiết hôm nay đẹp quá" |

### 2.3 Tiền xử lý văn bản

1. Chuẩn hóa Unicode (NFC)
2. Lowercasing
3. Loại bỏ URL, email
4. Masking số điện thoại → `[PHONE]`
5. Chuẩn hóa teencode cơ bản (vd: "ko" → "không", "dc" → "được")
6. Loại bỏ ký tự đặc biệt thừa
7. Tokenization (Vietnamese word segmentation)

---

## 3. Mô hình AI

### 3.1 Mô hình phân loại ảnh

| Thuộc tính | Giá trị |
|-----------|---------|
| Kiến trúc gốc | MobileNetV3-Large (ImageNet pretrained) |
| Phương pháp | Transfer Learning, fine-tune 2 lớp cuối |
| Quantization | INT8 → TensorFlow Lite |
| Kích thước mục tiêu | ≤ 5 MB |
| Thời gian suy luận | < 100 ms (thiết bị tầm trung) |
| Chỉ tiêu Accuracy | ≥ 85% |

**Tại sao chọn MobileNetV3?**
- Thiết kế tối ưu cho mobile (depthwise separable conv + squeeze-and-excitation)
- Nhẹ hơn ResNet (5 MB vs 44 MB) nhưng accuracy tương đương trên ImageNet
- Hỗ trợ tốt TFLite quantization
- So sánh: EfficientNet-Lite0 nặng hơn (~15 MB) nhưng accuracy chỉ tốt hơn ~1-2%

### 3.2 Mô hình phân loại văn bản

| Thuộc tính | Giá trị |
|-----------|---------|
| Kiến trúc gốc | DistilBERT hoặc PhoBERT distilled |
| Phương pháp | Fine-tune trên UIT-VSMEC + crawl VN |
| Quantization | Dynamic quantization → ONNX Runtime Mobile |
| Kích thước mục tiêu | ≤ 65 MB |
| Thời gian suy luận | < 200 ms |
| Chỉ tiêu F1-score | ≥ 80% |

**Tại sao chọn DistilBERT/PhoBERT?**
- PhoBERT được pre-train trên corpus tiếng Việt → hiểu ngữ cảnh VN tốt hơn
- DistilBERT nhẹ hơn BERT gốc 40% nhưng giữ 97% performance
- Hỗ trợ ONNX export cho mobile deployment
- So sánh: BERT-base quá nặng (~440 MB), không phù hợp edge

### 3.3 Tại sao dùng 2 model riêng biệt?

| Tiêu chí | 2 Model riêng | 1 Model multimodal |
|----------|--------------|-------------------|
| Kích thước | ~70 MB tổng | > 200 MB |
| Linh hoạt | Chạy độc lập khi chỉ có 1 loại input | Cần cả 2 input |
| Quantization | Dễ tối ưu riêng từng model | Khó quantize đồng bộ |
| Chạy song song | ✅ Giảm latency | ❌ Sequential |
| Edge deployment | Phù hợp thiết bị tầm trung | Cần thiết bị mạnh |

### 3.4 Pipeline triển khai

```
Pretrained → Fine-tune → Đánh giá (Accuracy/F1) → Quantization → Convert (TFLite/ONNX) → Deploy mobile
```

---

## 4. Benchmark models được so sánh

### 4.1 Ảnh

| Model | Params | Size | Vai trò |
|-------|--------|------|---------|
| MobileNetV3-Small | 2.5M | ~3 MB | Nhẹ nhất, backup |
| MobileNetV3-Large | 5.4M | ~5 MB | **Ứng viên chính** |
| EfficientNet-Lite0 | 4.7M | ~15 MB | So sánh |
| ResNet-18 | 11.7M | ~44 MB | Baseline nặng |

### 4.2 Văn bản

| Model | Params | Vai trò |
|-------|--------|---------|
| PhoBERT-base | 135M | Vietnamese feature extraction |
| XLM-RoBERTa XNLI | 278M | Zero-shot baseline |
| DistilBERT | 66M | **Ứng viên chính** (sau distillation) |
