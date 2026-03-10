# PROMPT 2 — Dataset Preparation & AI Model Demo Inference

> **Target**: AI Agent responsible for data engineering and model evaluation
> **Project**: "An Edge AI–Based System for Multimodal Analysis and Clustering of Flood Rescue Events"
> **Deliverable for**: Progress Report #1 to the supervising professor
> **Execution environment**: Google Colab (Free tier, T4 GPU) + Kaggle Notebooks (P100 GPU)

---

## YOUR ROLE

You are a senior ML/Data engineer. Your task is to:
1. **Prepare two complete datasets** (image + text) ready for future model training
2. **Run demo inference** with several pre-trained/off-the-shelf AI models to verify the pipeline works and produce initial qualitative results

This is for a **progress report** (not final evaluation), so the goal is to demonstrate that datasets are assembled and the inference pipeline is functional — NOT to train models from scratch.

---

## PROJECT CONTEXT

### Problem
A mobile app for flood rescue in **Central Vietnam** that runs AI on-device to:
- Classify flood images by severity (no flood / low flood / high flood) and damage level
- Classify Vietnamese rescue text messages by urgency (urgent_rescue / need_supplies / safe_update / irrelevant)

### Key datasets mentioned in the research proposal
- **FloodNet** (UAV images, post-Hurricane Harvey, USA)
- **CrisisMMD v2.0** (tweets + images from 7 disasters)
- **UIT-VSMEC** (Vietnamese social media emotion classification, 6,927 sentences)
- **Self-collected data** from Vietnamese social media (Facebook/Zalo groups during recent floods)

### Important context
- The system targets **Central Vietnam** (Huế, Đà Nẵng, Quảng Nam, Quảng Bình, Quảng Ngãi, etc.)
- Vietnamese housing architecture (low-rise concrete, tin roofs, narrow alleys) differs significantly from Western buildings
- Flood scenes include rice paddies, rivers overflowing, motorbikes submerged — visual features specific to Vietnam
- Text data includes Vietnamese slang, teencode, and dialectal expressions from Central Vietnam

---

## PART A: DATASET PREPARATION

### A.1. Image Dataset — PRIMARY FOCUS

**Goal**: Assemble a unified image dataset suitable for flood severity classification in the Vietnamese context. This is the primary focus for this progress report.

#### Step 1: Download and organize international base datasets

**Dataset 1: FloodNet**
- Source: https://github.com/BinaLab/FloodNet-Supervised_v1.0
- Download the classification subset
- Expected: ~2,343 UAV images with 10 classes
- **Remap labels** to our 3-class schema:
  - `Building-Flooded`, `Road-Flooded` → `high_flood`
  - `Water`, `Mud/Sand` (with partial structures visible) → `low_flood`
  - `Building-Non-Flooded`, `Road-Non-Flooded`, `Grass`, `Tree` → `no_flood`
  - `Vehicle`, `Pool` → discard or `no_flood` depending on context
- Document: number of images per remapped class, sample images

**Dataset 2: CrisisMMD v2.0**
- Source: https://crisisnlp.qcri.org/crisismmd OR Hugging Face
- Download the image portion
- Filter for **flood-related events only** (Hurricane Harvey, Hurricane Irma, Hurricane Maria, Sri Lanka Floods, etc.)
- **Remap labels** using their `damage_severity` annotation:
  - `severe` → `high_flood`
  - `mild` → `low_flood`  
  - `little_or_no_damage` → `no_flood`
- Document: number of images per class after filtering

**Dataset 3 (Kaggle supplements):**
- Search Kaggle for "flood classification", "flood detection", "flood images" datasets
- Download 1-2 additional datasets that contain **ground-level flood photos** (not satellite/UAV)
- These are critical because they resemble photos taken by phone users (similar to real app usage)
- Remap to same 3-class schema

#### Step 2: Collect Vietnam-specific flood images — CRITICAL FOR CENTRAL VN CONTEXT

This step is essential to make the dataset relevant to the project's geographic focus.

**Sources to crawl/collect from:**
1. **Vietnamese news websites** (search for "lũ lụt miền Trung", "bão Yagi", "ngập lụt Huế", "lũ Quảng Bình"):
   - VnExpress (vnexpress.net) — photo galleries of flood coverage
   - Tuổi Trẻ (tuoitre.vn)
   - Dân Trí (dantri.com.vn)
   - Thanh Niên (thanhnien.vn)
   
2. **Google Images** (search queries):
   - "lũ lụt miền Trung Việt Nam"
   - "ngập lụt Huế Đà Nẵng Quảng Nam"
   - "cứu hộ bão lũ Việt Nam"
   - "nhà ngập nước Việt Nam"
   - "flood Vietnam central"
   - "Vietnam flood rescue"

3. **Key flood events to search for**:
   - Bão Yagi (2024) — Quảng Ninh, Hải Phòng, northern provinces
   - Lũ lụt miền Trung 2020 — Huế, Quảng Trị, Quảng Bình (worst in decades)
   - Bão Noru (2022) — Đà Nẵng, Quảng Nam
   - Bão Molave (2020) — Quảng Ngãi, Quảng Nam

**Target volume**: 300-500 images minimum for Vietnam-specific subset

**Label schema for Vietnam images:**

| Label | Description | Visual cues (Central Vietnam specific) |
|---|---|---|
| `no_flood` | Normal scene, no flooding | Dry roads, normal river levels, intact houses |
| `low_flood` | Minor flooding, ankle-to-knee level | Water on roads, partially submerged motorbikes, muddy water in streets |
| `high_flood` | Severe flooding, waist level or higher | Houses submerged to windows/roof, people on rooftops, boats in streets, rescue operations |

**IMPORTANT notes for Vietnam context:**
- Vietnamese houses in Central region are typically low-rise concrete with flat or tin roofs
- Common flood indicators: motorbikes/bicycles partially submerged, water level marks on walls
- Rice paddies completely submerged = common rural scene during floods
- Narrow alleyways (hẻm) filled with water
- Rescue boats (thuyền cứu hộ) in residential areas

#### Step 3: Merge and standardize the complete image dataset

1. **Merge all sources** into a unified directory structure:
```
dataset/
├── image_data/
│   ├── train/        (70%)
│   │   ├── no_flood/
│   │   ├── low_flood/
│   │   └── high_flood/
│   ├── val/          (15%)
│   │   ├── no_flood/
│   │   ├── low_flood/
│   │   └── high_flood/
│   └── test/         (15%)
│       ├── no_flood/
│       ├── low_flood/
│       └── high_flood/
├── metadata.csv      (filename, source, original_label, mapped_label, is_vietnam)
└── dataset_report.md
```

2. **Preprocessing**:
   - Resize all images to 224×224 (MobileNetV3 input size)
   - Keep original images as backup before resize
   - Normalize to [0, 1] range
   - Record image dimensions, file sizes before/after

3. **Stratified split** with `random_seed=42`, ensuring Vietnam images are proportionally distributed

4. **Generate statistics report** (`dataset_report.md`):
   - Total images per class (table)
   - Images per source (FloodNet, CrisisMMD, Kaggle, Vietnam-collected)
   - Label distribution bar chart (save as PNG)
   - Sample grid: 3×3 grid of random images from each class (save as PNG)
   - Proportion of Vietnam vs. international images
   - Note any class imbalance issues and mitigation strategies

---

### A.2. Text Dataset — Secondary

**Goal**: Assemble a text dataset for Vietnamese rescue message classification.

#### Step 1: Download base dataset

**UIT-VSMEC**
- Source: https://github.com/uitnlp (search for VSMEC)
- Download and inspect the dataset
- Document: number of samples, label distribution, sample texts
- **Remap labels** relevant to rescue context:
  - `Fear`, `Sadness` → candidates for `urgent_rescue` or `need_supplies`
  - `Anger` → could indicate `urgent_rescue` (frustration at lack of help)
  - `Other` → likely `irrelevant` or `safe_update`
  - Note: This remapping is approximate; the real value is pre-training Vietnamese language understanding

#### Step 2: Collect Vietnamese rescue text samples

Create a **synthetic + real** text dataset:

1. **Real samples**: Search Facebook/Zalo public posts with keywords:
   - "cứu với", "ngập lút", "nước dâng", "kẹt trong nhà", "cần cứu hộ"
   - "hết thức ăn", "cần áo phao", "mất điện", "cần tiếp tế"
   - "đã an toàn", "nước đã rút", "tình hình ổn"

2. **Create a labeled sample file** (`text_samples.csv`) with columns:
   ```
   id, raw_text, clean_text, urgency_label, source
   ```
   
   Target: at least 100-200 Vietnamese text samples with labels:
   - `urgent_rescue`: "Cứu với! Nước dâng nóc nhà rồi, có người già và trẻ nhỏ"
   - `need_supplies`: "Nhà em ở Quảng Trị, cần gạo và nước uống, nước ngập nhưng chưa nguy hiểm"
   - `safe_update`: "Gia đình em đã sơ tán an toàn, cảm ơn mọi người"
   - `irrelevant`: "Dự báo thời tiết ngày mai trời nắng"

3. **Design the full label schema** (for future data collection):

| Label | Description | Example keywords |
|---|---|---|
| `urgent_rescue` | Life-threatening, immediate rescue needed | cứu, kẹt, nước dâng nóc, trẻ em, người già, sắp chết |
| `need_supplies` | Needs help but not life-threatening | cần gạo, áo phao, thuốc, mất điện, hết thức ăn |
| `safe_update` | Status update, safe | an toàn, đã sơ tán, nước rút, ổn rồi |
| `irrelevant` | Not related to rescue | thời tiết, chính trị, quảng cáo |

#### Step 3: Organize text dataset

```
dataset/
└── text_data/
    ├── uit_vsmec_original/    (raw UIT-VSMEC data)
    ├── uit_vsmec_remapped.csv (remapped labels)
    ├── rescue_text_samples.csv (collected Vietnamese text)
    ├── label_schema.md         (full label definitions)
    └── text_dataset_report.md  (statistics)
```

---

## PART B: AI MODEL DEMO INFERENCE

### Goal
Run **demo inference** (NOT training) with pre-trained models on sample images and texts to verify the pipeline works. Produce qualitative results (visual examples with predictions) for the progress report.

### Environment Setup

**Google Colab (Free) notebook** — for quick demos:
```python
# Cell 1: Check GPU
import torch
print(f"GPU available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
```

**Kaggle Notebook** — for heavier workloads:
- Enable GPU (P100) in notebook settings
- Same code, more stable runtime

### B.1. Image Model Demo Inference

Run inference with **pre-trained image classification models** on sample flood images (from the dataset you prepared in Part A).

#### Models to demo:

**Model 1: MobileNetV3-Small (ImageNet pre-trained)**
```python
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import torch

# Load pre-trained MobileNetV3-Small
model = models.mobilenet_v3_small(pretrained=True)
model.eval()

# Preprocessing (ImageNet standard)
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

# Run on sample flood images
# Show: input image + top-5 ImageNet predictions
# Purpose: Demonstrate what a pre-trained model "sees" in flood images
# (e.g., it might predict "lakeside", "dam", "seashore" for flood scenes)
```

**Model 2: EfficientNet-Lite0**
- Similar demo as MobileNetV3
- Compare: inference time, top predictions on same images

**Model 3: ResNet-18 (as baseline reference)**
- Heavier model, not suitable for mobile but useful as accuracy reference
- Compare predictions with lightweight models

#### Demo output for each model:
For **10 sample images** (mix of no_flood, low_flood, high_flood from your dataset):

```
┌─────────────────────────────┬────────────────────┬──────────────┐
│ Input Image (thumbnail)      │ Top-3 Predictions  │ Inference ms │
├─────────────────────────────┼────────────────────┼──────────────┤
│ [flood_vietnam_001.jpg]      │ 1. lakeside (0.42) │ 12.3 ms      │
│ Label: high_flood            │ 2. dam (0.18)      │              │
│ Source: Vietnam-collected    │ 3. seashore (0.09) │              │
├─────────────────────────────┼────────────────────┼──────────────┤
│ ...                          │ ...                │ ...          │
└─────────────────────────────┴────────────────────┴──────────────┘
```

#### Key metrics to record:
- Average inference time per image (ms) on Colab T4 GPU
- Average inference time on CPU (to simulate mobile)
- Model file size (MB)
- Number of parameters
- Qualitative observation: Do the pre-trained ImageNet features capture flood-relevant concepts?

#### Model size comparison table:
| Model | Parameters | Size (MB) | Avg Inference (GPU) | Avg Inference (CPU) |
|---|---|---|---|---|
| MobileNetV3-Small | ? | ? MB | ? ms | ? ms |
| MobileNetV3-Large | ? | ? MB | ? ms | ? ms |
| EfficientNet-Lite0 | ? | ? MB | ? ms | ? ms |
| ResNet-18 (baseline) | ? | ? MB | ? ms | ? ms |

### B.2. Text Model Demo Inference

Run inference with **pre-trained Vietnamese NLP models** on sample rescue text messages.

#### Models to demo:

**Model 1: PhoBERT-base**
```python
from transformers import AutoModel, AutoTokenizer

# PhoBERT — best Vietnamese language model
tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
model = AutoModel.from_pretrained("vinai/phobert-base")

# Run on sample Vietnamese rescue messages
# Show: input text → token embeddings → (no classification head yet, just verify loading)
# Purpose: Verify PhoBERT loads correctly and can tokenize Vietnamese rescue text
```

**Model 2: DistilBERT-multilingual**
```python
from transformers import pipeline

# Zero-shot classification demo (no training needed!)
classifier = pipeline("zero-shot-classification", 
                       model="joeddav/xlm-roberta-large-xnli")

text = "Cứu với! Nước dâng nóc nhà rồi, có người già và trẻ nhỏ"
labels = ["urgent rescue", "need supplies", "safe update", "irrelevant"]
result = classifier(text, labels)
```

**Model 3: Sentiment analysis (UIT-VSMEC based)**
- Use a pre-trained Vietnamese sentiment model if available on HuggingFace
- Or demonstrate the UIT-VSMEC dataset loading and basic statistics

#### Demo output for text models:
For **10 sample Vietnamese rescue messages**:

```
┌─────────────────────────────────────────┬───────────────────┬──────────────┐
│ Input Text                               │ Model Prediction   │ Inference ms │
├─────────────────────────────────────────┼───────────────────┼──────────────┤
│ "Cứu với! Nước ngập nóc nhà, có bà     │ urgent rescue (0.82)│ 45.2 ms     │
│  già 80 tuổi không di chuyển được"       │                    │              │
├─────────────────────────────────────────┼───────────────────┼──────────────┤
│ "Nhà em cần gạo và nước uống, nước      │ need supplies (0.71)│ 43.1 ms     │
│  ngập đến bụng nhưng chưa nguy hiểm"    │                    │              │
├─────────────────────────────────────────┼───────────────────┼──────────────┤
│ ...                                      │ ...                │ ...          │
└─────────────────────────────────────────┴───────────────────┴──────────────┘
```

#### Key metrics to record:
- Model loading time
- Average inference time per text sample (ms)
- Model file size (MB)
- Tokenizer vocabulary size
- Qualitative: Does zero-shot classification produce reasonable results on Vietnamese flood text?

### B.3. TFLite Conversion Demo (Bonus)

If time permits, demonstrate converting one image model to TFLite:

```python
import tensorflow as tf

# Convert MobileNetV3 to TFLite
converter = tf.lite.TFLiteConverter.from_saved_model("mobilenetv3_saved")
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

# Report: original size vs TFLite size
print(f"Original: {original_size_mb:.1f} MB")
print(f"TFLite FP16: {fp16_size_mb:.1f} MB")
print(f"TFLite INT8: {int8_size_mb:.1f} MB")
```

---

## OUTPUT FORMAT

Produce **2 Jupyter Notebooks** (one for Colab, one for Kaggle) + **1 summary report**:

### Notebook 1: `dataset_preparation.ipynb` (Colab or Kaggle)
- Cell-by-cell execution for downloading, organizing, and statistics
- All charts/visualizations inline
- Final output: organized dataset in the directory structure specified above

### Notebook 2: `model_demo_inference.ipynb` (Colab with GPU)
- Cell-by-cell execution for all model demos
- Visual outputs: input images with predictions overlaid
- Tables comparing model sizes and inference times
- Works on both Colab Free (T4) and Kaggle (P100)

### Summary Report: `progress_report_data_models.md`
A concise markdown report containing:
1. **Dataset Summary** — tables + charts showing what was collected
2. **Image Dataset** — distribution, Vietnam proportion, sample grid
3. **Text Dataset** — distribution, label schema, sample texts
4. **Model Demo Results** — comparison tables, qualitative observations
5. **Next Steps** — what needs to be done for actual model training

---

## QUALITY REQUIREMENTS

1. **Reproducibility**: All code must run without errors on Google Colab Free and Kaggle. Include `!pip install` cells for all dependencies.
2. **Vietnam focus**: The image dataset MUST contain a meaningful proportion (≥20%) of Vietnam-specific flood images, particularly from Central Vietnam.
3. **No training required**: This is demo inference only. Use pre-trained weights, zero-shot classification, or feature extraction — do NOT train any model.
4. **Visual evidence**: Every claim must be backed by a screenshot, chart, or table.
5. **Metadata**: Every image and text sample must have traceable metadata (source, original URL if applicable, date if known).
6. **Seed everything**: Use `random_seed=42` for all random operations.

---

## CONSTRAINTS

- Do NOT train any model from scratch — this is for Progress Report #1 only.
- Do NOT use paid APIs (Google Cloud Vision, OpenAI, etc.) — stick to free/open-source tools.
- Do NOT collect personally identifiable information (PII) — blur faces, remove phone numbers.
- Runtime limit: Each notebook should complete within **2 hours** on Colab Free.
- Total storage: Keep total dataset under **5 GB** (Colab Free limit ~15 GB, Kaggle ~20 GB).
- If a dataset is too large to download in the notebook, provide clear manual download instructions.
