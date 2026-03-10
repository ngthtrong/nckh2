# QUY TRÌNH ĐÁNH GIÁ, SO SÁNH VÀ LỰA CHỌN MODEL AI TẠI BIÊN

> Tài liệu hướng dẫn quy trình benchmark các model ứng viên cho đề tài  
> *"Hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI"*

---

## TỔNG QUAN QUY TRÌNH

```nckh
Phase 1: Chuẩn bị       → Phase 2: Huấn luyện     → Phase 3: Đánh giá
(Dữ liệu + Môi trường)    (Train + Fine-tune)        (Benchmark toàn diện)

                          → Phase 4: So sánh        → Phase 5: Lựa chọn
                            (Bảng tổng hợp)            (Quyết định + Báo cáo)
```

---

## PHASE 1 — CHUẨN BỊ

### 1.1. Chuẩn bị dữ liệu

| Hạng mục | Nhánh Ảnh | Nhánh Văn bản |
|---|---|---|
| **Dữ liệu chính** | FloodNet, CrisisMMD + ảnh thu thập VN | UIT-VSMEC + tin nhắn cứu hộ Zalo/Facebook |
| **Tỷ lệ chia** | 70% train / 15% val / 15% test | 70% train / 15% val / 15% test |
| **Augmentation** | Flip, rotate, color jitter, random crop | Back-translation, synonym replacement |

> [!IMPORTANT]  
> **Tập test phải cố định và giống nhau** cho tất cả các model để đảm bảo so sánh công bằng.  
> Lưu lại `random_seed` khi chia dữ liệu (ví dụ: `seed=42`).

**📋 Thông tin cần ghi lại cho báo cáo:**
- Tổng số mẫu cho mỗi tập (train/val/test)
- Phân bố nhãn (label distribution) — vẽ biểu đồ
- Các kỹ thuật augmentation đã dùng
- Random seed + phương pháp chia dữ liệu (stratified split)

### 1.2. Thiết lập môi trường

```
Huấn luyện:  Google Colab Pro / Kaggle (GPU T4/P100)
Đánh giá Edge: Thiết bị Android thực tế (ghi rõ: tên máy, RAM, chipset, Android version)
Framework:    TensorFlow Lite + ONNX Runtime Mobile
Tracking:     MLflow hoặc Weights & Biases (wandb) — ghi lại TẤT CẢ thí nghiệm
```

**📋 Thông tin cần ghi lại cho báo cáo:**
- Cấu hình máy huấn luyện (GPU, RAM, VRAM)
- Phiên bản framework (TensorFlow, PyTorch, ONNX, ...)
- Thông số thiết bị test thực tế (model điện thoại, chip, RAM)

---

## PHASE 2 — HUẤN LUYỆN (cho mỗi model ứng viên)

### 2.1. Nhánh Ảnh — Danh sách model thử nghiệm

| ID | Model | Pretrained trên | Kỹ thuật |
|---|---|---|---|
| IMG-01 | MobileNetV3-Small | ImageNet | Transfer Learning, freeze backbone → unfreeze dần |
| IMG-02 | MobileNetV3-Large | ImageNet | Transfer Learning |
| IMG-03 | EfficientNet-Lite0 | ImageNet | Transfer Learning |
| IMG-04 | ShuffleNetV2 (x1.0) | ImageNet | Transfer Learning |
| IMG-05 | YOLOv8n *(nếu cần detection)* | COCO | Fine-tune trên FloodNet |

### 2.2. Nhánh Văn bản — Danh sách model thử nghiệm

| ID | Model | Pretrained trên | Kỹ thuật |
|---|---|---|---|
| TXT-01 | DistilBERT-multilingual | Wikipedia 104 ngôn ngữ | Fine-tune trên UIT-VSMEC + dữ liệu cứu hộ |
| TXT-02 | PhoBERT-base | 20GB tiếng Việt | Fine-tune → Distillation → Quantization |
| TXT-03 | MobileBERT | English BookCorpus+Wiki | Fine-tune multilingual |
| TXT-04 | TinyBERT (4-layer) | Distilled từ BERT-base | Fine-tune |
| TXT-05 | XLM-RoBERTa-small | CC-100 đa ngôn ngữ | Fine-tune |

### 2.3. Hyperparameter ghi log cho mỗi thí nghiệm

```python
# Mẫu config ghi lại — ÁP DỤNG CHO MỌI THÍ NGHIỆM
experiment_config = {
    "model_id": "IMG-01",
    "model_name": "MobileNetV3-Small",
    "pretrained_weights": "imagenet",
    "learning_rate": 1e-4,
    "batch_size": 32,
    "epochs": 50,
    "optimizer": "AdamW",
    "scheduler": "CosineAnnealingLR",
    "weight_decay": 1e-5,
    "early_stopping_patience": 5,
    "input_size": [224, 224],
    "augmentation": ["HorizontalFlip", "RandomRotation(15)", "ColorJitter"],
    "freeze_strategy": "freeze_backbone_10_epochs_then_unfreeze",
    "random_seed": 42,
    "training_time_minutes": None,     # ← ghi sau khi train xong
    "best_val_accuracy": None,         # ← ghi sau khi train xong
    "best_val_loss": None,             # ← ghi sau khi train xong
}
```

> [!TIP]  
> Sử dụng **MLflow** hoặc **Weights & Biases** để tự động log tất cả metrics theo epoch.  
> Nếu dùng thủ công, tạo file CSV cho mỗi thí nghiệm với format:  
> `epoch, train_loss, train_acc, val_loss, val_acc, learning_rate`

---

## PHASE 3 — ĐÁNH GIÁ (Benchmark toàn diện)

Đánh giá gồm **3 tầng**, từ accuracy thuần đến hiệu năng thực tế trên thiết bị.

### Tầng 1: Đánh giá Accuracy trên tập Test

Chạy inference trên **tập test cố định** và tính các chỉ số:

| Metric | Công thức / Ý nghĩa | Dùng cho |
|---|---|---|
| **Accuracy** | Tỷ lệ dự đoán đúng tổng thể | Cả ảnh + text |
| **Precision** | TP / (TP + FP) — Độ chính xác khi dự đoán positive | Cả ảnh + text |
| **Recall** | TP / (TP + FN) — Khả năng phát hiện đúng | Cả ảnh + text |
| **F1-Score (macro)** | Trung bình hài hòa Precision & Recall | **Metric chính cho báo cáo** |
| **F1-Score (weighted)** | F1 có trọng số theo số mẫu mỗi class | Khi dữ liệu mất cân bằng |
| **Confusion Matrix** | Ma trận nhầm lẫn giữa các lớp | Phân tích lỗi chi tiết |
| **ROC-AUC** | Diện tích dưới đường cong ROC | So sánh tổng thể |

```python
# Code mẫu đánh giá với sklearn
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import json, time

def evaluate_model(model, test_loader, model_id):
    """Đánh giá model và lưu kết quả."""
    y_true, y_pred, y_prob = [], [], []
    
    start_time = time.time()
    for batch in test_loader:
        # ... chạy inference ...
        pass
    total_inference_time = time.time() - start_time
    
    # Tính metrics
    report = classification_report(y_true, y_pred, output_dict=True)
    cm = confusion_matrix(y_true, y_pred)
    
    results = {
        "model_id": model_id,
        "accuracy": report["accuracy"],
        "f1_macro": report["macro avg"]["f1-score"],
        "f1_weighted": report["weighted avg"]["f1-score"],
        "precision_macro": report["macro avg"]["precision"],
        "recall_macro": report["macro avg"]["recall"],
        "confusion_matrix": cm.tolist(),
        "per_class_report": report,
        "total_inference_time_sec": total_inference_time,
        "num_test_samples": len(y_true),
        "avg_inference_time_ms": (total_inference_time / len(y_true)) * 1000
    }
    
    # Lưu ra file JSON
    with open(f"results/{model_id}_evaluation.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results
```

**📋 Thông tin cần lưu:**
- Classification report đầy đủ (per-class precision, recall, f1)
- Confusion matrix (dạng heatmap để đưa vào báo cáo)
- Biểu đồ training curves (loss + accuracy theo epoch) cho mỗi model

### Tầng 2: Đánh giá sau Quantization

Sau khi train xong model gốc (FP32), tiến hành **nén model** rồi đánh giá lại:

```python
# TensorFlow Lite Quantization
import tensorflow as tf

def quantize_and_evaluate(saved_model_path, model_id):
    """Nén model và đo accuracy drop."""
    
    results = {}
    
    # --- Float16 Quantization ---
    converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_path)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]
    fp16_model = converter.convert()
    results["fp16_size_mb"] = len(fp16_model) / (1024 * 1024)
    
    # --- INT8 Quantization (full) ---
    converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_path)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_data_gen  # cần hàm gen data
    int8_model = converter.convert()
    results["int8_size_mb"] = len(int8_model) / (1024 * 1024)
    
    # Lưu model
    with open(f"models/{model_id}_fp16.tflite", "wb") as f:
        f.write(fp16_model)
    with open(f"models/{model_id}_int8.tflite", "wb") as f:
        f.write(int8_model)
    
    return results
```

| Metric cần đo | Cách đo |
|---|---|
| **Kích thước file model** `.tflite` | `os.path.getsize()` — đơn vị MB |
| **Accuracy drop** (so với FP32 gốc) | Chạy lại evaluate trên tập test |
| **F1 drop** | So sánh F1 trước/sau quantization |

**📋 Bảng so sánh cần lưu:**

| Model | FP32 Size | FP16 Size | INT8 Size | FP32 F1 | INT8 F1 | Accuracy Drop |
|---|---|---|---|---|---|---|
| IMG-01 | ? MB | ? MB | ? MB | ? | ? | ? % |
| ... | | | | | | |

### Tầng 3: Đánh giá trên thiết bị thực (On-device Benchmark)

> [!CAUTION]  
> Đây là bước **quan trọng nhất** vì kết quả trên Colab KHÔNG phản ánh hiệu năng thực tế trên điện thoại.

Cài app test lên **thiết bị Android thực tế**, đo:

| Metric | Cách đo | Đơn vị |
|---|---|---|
| **Inference latency** | Trung bình 100 lần chạy inference | ms |
| **Cold start time** | Thời gian load model lần đầu | ms |
| **RAM usage** | Android Profiler hoặc `Debug.getMemoryInfo()` | MB |
| **Kích thước APK tăng thêm** | So sánh APK có/không có model | MB |
| **Mức tiêu thụ pin** | Ước lượng qua Android Battery Historian | mAh/giờ |
| **Nhiệt độ thiết bị** | Đo sau 10 phút chạy liên tục | °C |

```dart
// Flutter — Code mẫu đo inference time
import 'package:tflite_flutter/tflite_flutter.dart';

Future<Map<String, double>> benchmarkModel(String modelPath, int numRuns) async {
  final interpreter = await Interpreter.fromAsset(modelPath);
  
  List<double> latencies = [];
  
  for (int i = 0; i < numRuns; i++) {
    final stopwatch = Stopwatch()..start();
    interpreter.run(inputData, outputData);
    stopwatch.stop();
    latencies.add(stopwatch.elapsedMicroseconds / 1000.0); // ms
  }
  
  latencies.sort();
  return {
    "mean_ms": latencies.reduce((a, b) => a + b) / latencies.length,
    "median_ms": latencies[latencies.length ~/ 2],
    "p95_ms": latencies[(latencies.length * 0.95).floor()],
    "min_ms": latencies.first,
    "max_ms": latencies.last,
  };
}
```

**📋 Bảng kết quả cần lưu:**

| Model | INT8 Size | Latency (mean) | Latency (P95) | RAM | F1-Score | Cold Start |
|---|---|---|---|---|---|---|
| IMG-01 | ? MB | ? ms | ? ms | ? MB | ? | ? ms |
| ... | | | | | | |

---

## PHASE 4 — SO SÁNH TỔNG HỢP

### 4.1. Bảng so sánh toàn diện (Master Comparison Table)

Tổng hợp tất cả kết quả vào **một bảng duy nhất** cho mỗi nhánh:

#### Nhánh Ảnh

| Model | F1 (FP32) | F1 (INT8) | Drop | Size (INT8) | Latency (ms) | RAM (MB) | Tổng điểm |
|---|---|---|---|---|---|---|---|
| MobileNetV3-Small | | | | | | | |
| MobileNetV3-Large | | | | | | | |
| EfficientNet-Lite0 | | | | | | | |
| ShuffleNetV2 | | | | | | | |

#### Nhánh Văn bản

| Model | F1 (FP32) | F1 (INT8) | Drop | Size (INT8) | Latency (ms) | RAM (MB) | Tổng điểm |
|---|---|---|---|---|---|---|---|
| DistilBERT-multi | | | | | | | |
| PhoBERT (distilled) | | | | | | | |
| MobileBERT | | | | | | | |
| TinyBERT | | | | | | | |

### 4.2. Hệ thống tính điểm tổng hợp (Weighted Scoring)

Dùng **weighted scoring** để lựa chọn model một cách khách quan:

```python
# Trọng số gợi ý — điều chỉnh tùy ưu tiên đề tài
weights = {
    "f1_score":      0.30,   # Accuracy là quan trọng nhất
    "model_size":    0.25,   # Nhẹ để chạy trên mobile
    "latency":       0.25,   # Phản hồi nhanh trong khẩn cấp
    "ram_usage":     0.10,   # Giảm tải bộ nhớ thiết bị
    "accuracy_drop": 0.10,   # Ít suy giảm sau quantization
}

def compute_score(model_metrics, all_models_metrics):
    """
    Tính điểm normalized (0-1) cho mỗi model.
    F1: cao hơn = tốt hơn → normalize thuận
    Size, Latency, RAM, Drop: thấp hơn = tốt hơn → normalize nghịch
    """
    score = 0
    for metric, weight in weights.items():
        values = [m[metric] for m in all_models_metrics]
        min_v, max_v = min(values), max(values)
        
        if max_v == min_v:
            normalized = 1.0
        elif metric == "f1_score":
            normalized = (model_metrics[metric] - min_v) / (max_v - min_v)
        else:  # metrics nghịch (thấp = tốt)
            normalized = 1 - (model_metrics[metric] - min_v) / (max_v - min_v)
        
        score += normalized * weight
    
    return round(score, 4)
```

### 4.3. Biểu đồ trực quan cho báo cáo

Tạo các biểu đồ sau để đưa vào báo cáo cuối:

| Loại biểu đồ | Nội dung | Mục đích |
|---|---|---|
| **Bar chart** | F1-Score các model cạnh nhau | So sánh accuracy trực quan |
| **Scatter plot** | F1 vs Latency (mỗi điểm = 1 model) | Trade-off accuracy ↔ tốc độ |
| **Radar chart** | Đa chiều: F1, Size, Speed, RAM | So sánh tổng thể |
| **Line chart** | Training curves (loss/acc theo epoch) | Quá trình hội tụ |
| **Heatmap** | Confusion Matrix cho model được chọn | Phân tích lỗi chi tiết |

```python
# Code mẫu tạo biểu đồ so sánh
import matplotlib.pyplot as plt
import numpy as np

def plot_comparison(models, f1_scores, latencies, sizes):
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # Bar chart — F1 Score
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(models)))
    axes[0].barh(models, f1_scores, color=colors)
    axes[0].set_xlabel("F1-Score (Macro)")
    axes[0].set_title("So sánh F1-Score các Model")
    
    # Scatter — F1 vs Latency
    axes[1].scatter(latencies, f1_scores, s=np.array(sizes)*50, c=colors, alpha=0.7)
    for i, m in enumerate(models):
        axes[1].annotate(m, (latencies[i], f1_scores[i]), fontsize=8)
    axes[1].set_xlabel("Latency (ms)")
    axes[1].set_ylabel("F1-Score")
    axes[1].set_title("Trade-off: Accuracy vs Tốc độ")
    
    # Bar chart — Model Size
    axes[2].barh(models, sizes, color=colors)
    axes[2].set_xlabel("Kích thước (MB)")
    axes[2].set_title("So sánh kích thước Model (INT8)")
    
    plt.tight_layout()
    plt.savefig("reports/model_comparison.png", dpi=150, bbox_inches='tight')
    plt.show()
```

---

## PHASE 5 — QUYẾT ĐỊNH LỰA CHỌN & GHI BÁO CÁO

### 5.1. Tiêu chí loại (Elimination Criteria)

Model bị **loại ngay** nếu vi phạm bất kỳ điều kiện nào:

| Tiêu chí cứng | Ngưỡng gợi ý |
|---|---|
| Kích thước model (INT8) | > 50 MB → Loại |
| Inference latency trên thiết bị | > 500 ms → Loại |
| F1-Score trên tập test | < 0.70 → Loại |
| RAM usage | > 200 MB → Loại |
| Accuracy drop sau quantization | > 5% → Cần xem xét kỹ |

### 5.2. Template kết luận cho báo cáo

```markdown
## Kết quả so sánh và lựa chọn Model

### Nhánh xử lý hình ảnh
- **Model được chọn:** [Tên model]
- **Lý do lựa chọn:** [F1 đạt X, kích thước Y MB, latency Z ms — cân bằng tốt nhất
  giữa accuracy và hiệu năng thiết bị]
- **So sánh với các ứng viên khác:** [Model A có F1 cao hơn nhưng nặng gấp 3 lần; 
  Model B nhẹ hơn nhưng F1 thấp hơn 5%]

### Nhánh xử lý văn bản
- **Model được chọn:** [Tên model]
- **Lý do lựa chọn:** [...]
- **So sánh:** [...]

### Bảng tổng hợp cuối cùng
[Đính kèm Master Comparison Table + biểu đồ]
```

---

## CHECKLIST GHI NHẬN CHO BÁO CÁO

> [!IMPORTANT]  
> Đảm bảo lưu lại **TẤT CẢ** các hạng mục dưới đây trong quá trình thực nghiệm.

### Dữ liệu
- [ ] Thống kê số lượng mẫu train/val/test
- [ ] Biểu đồ phân bố nhãn
- [ ] Danh sách kỹ thuật augmentation
- [ ] Random seed + phương pháp chia dữ liệu

### Huấn luyện
- [ ] Hyperparameters cho mỗi thí nghiệm (JSON/YAML)
- [ ] Training curves (loss + accuracy) cho mỗi model
- [ ] Thời gian huấn luyện (phút/giờ)
- [ ] Cấu hình phần cứng huấn luyện

### Đánh giá Accuracy
- [ ] Classification report cho mỗi model
- [ ] Confusion matrix (heatmap) cho mỗi model
- [ ] Bảng so sánh F1/Precision/Recall

### Đánh giá trên thiết bị
- [ ] Thông số thiết bị test (tên máy, chip, RAM, OS)
- [ ] Bảng latency (mean, median, P95)
- [ ] RAM usage
- [ ] Kích thước model trước/sau quantization
- [ ] Screenshots Android Profiler (nếu có)

### Biểu đồ cho báo cáo
- [ ] Bar chart so sánh F1-Score
- [ ] Scatter plot F1 vs Latency
- [ ] Radar chart tổng hợp đa chiều
- [ ] Training curves overlay các model

### Kết luận
- [ ] Bảng Master Comparison Table hoàn chỉnh
- [ ] Weighted scoring + thứ hạng
- [ ] Lập luận lựa chọn model cuối cùng
- [ ] Hạn chế + hướng cải tiến

---

## CẤU TRÚC THƯ MỤC GỢI Ý

```
nckh/
├── data/
│   ├── raw/                    # Dữ liệu gốc
│   ├── processed/              # Dữ liệu đã xử lý
│   └── splits/                 # Train/val/test splits (có seed)
├── experiments/
│   ├── IMG-01_mobilenetv3s/    # Mỗi thí nghiệm 1 folder
│   │   ├── config.json         # Hyperparameters
│   │   ├── training_log.csv    # Metrics theo epoch
│   │   ├── best_model.pth      # Model weights
│   │   ├── evaluation.json     # Kết quả đánh giá
│   │   └── confusion_matrix.png
│   ├── IMG-02_mobilenetv3l/
│   ├── TXT-01_distilbert/
│   └── ...
├── models/
│   ├── tflite/                 # Các model đã convert
│   │   ├── IMG-01_fp16.tflite
│   │   ├── IMG-01_int8.tflite
│   │   └── ...
│   └── onnx/                   # Nếu dùng ONNX
├── reports/
│   ├── comparison_table.csv    # Bảng tổng hợp
│   ├── model_comparison.png    # Biểu đồ so sánh
│   └── device_benchmark.csv    # Kết quả test trên thiết bị
└── scripts/
    ├── train.py
    ├── evaluate.py
    ├── quantize.py
    ├── benchmark_device.dart
    └── generate_reports.py     # Auto-generate biểu đồ + bảng
```
