# Hướng dẫn Thành viên 1: Edge AI & Vector Thuộc tính

> **Phạm vi:** Mục 4.1 của bài báo — Trích xuất đặc trưng tại thiết bị biên

---

## 1. Bối cảnh: Tại sao cần Edge AI?

### 1.1. Vấn đề của mô hình Cloud-centric

```
┌─────────────────────────────────────────────────────────────┐
│                    MÔ HÌNH TRUYỀN THỐNG                     │
│                                                             │
│   📱 Điện thoại          ☁️ Server đám mây                  │
│   ┌──────────┐          ┌──────────┐                       │
│   │ Ảnh 5MB  │ ──────→  │ Xử lý AI │                       │
│   │ Video    │  MẠNG    │ Phân tích│                       │
│   └──────────┘  YẾU ❌  └──────────┘                       │
│                                                             │
│   Khi bão lũ: trạm BTS sập → KHÔNG GỬI ĐƯỢC                │
└─────────────────────────────────────────────────────────────┘
```

**Trong bão lũ:**
- Trạm phát sóng (BTS) bị ngập/mất điện
- Băng thông còn lại rất thấp (vài KB/s)
- Gửi ảnh 5MB có thể mất **hàng giờ** hoặc thất bại hoàn toàn
- → Đúng lúc cần cứu hộ nhất thì hệ thống "chết"

### 1.2. Giải pháp Edge AI

```
┌─────────────────────────────────────────────────────────────┐
│                    MÔ HÌNH EDGE AI                          │
│                                                             │
│   📱 Điện thoại                      🖥️ Server              │
│   ┌──────────────────┐              ┌──────────┐           │
│   │ Ảnh 5MB          │              │          │           │
│   │      ↓           │   ~100 byte  │ Xây đồ   │           │
│   │ [AI tại chỗ]     │ ──────────→  │ thị, xếp │           │
│   │      ↓           │   MẠNG YẾU ✓ │ hạng     │           │
│   │ Vector 7 số      │              │          │           │
│   └──────────────────┘              └──────────┘           │
│                                                             │
│   Nén 5MB → 100 byte = giảm 50.000 lần!                    │
└─────────────────────────────────────────────────────────────┘
```

**Ý tưởng cốt lõi:**
- Chạy AI **ngay trên điện thoại** (không cần internet)
- Trích xuất **7 con số** đại diện cho tình huống
- Chỉ gửi 7 con số đó (< 1KB) thay vì ảnh gốc

---

## 2. Vector 7 chiều: $(L, T, F, E, N, V, C)$

### 2.1. Bảng tổng quan

| Ký hiệu | Tên đầy đủ | Miền giá trị | Nguồn | Trích xuất tại |
|:-------:|:-----------|:-------------|:------|:---------------|
| $L$ | Vị trí GPS | (lat, lon) | GPS điện thoại | Tự động |
| $T$ | Thời gian | timestamp | Đồng hồ hệ thống | Tự động |
| $F$ | Mức ngập (Flood) | [0, 1] | **Ảnh** → MobileNetV3 | Biên |
| $E$ | Mức khẩn cấp (Emergency) | [0, 1] | **Văn bản** → DistilBERT | Biên |
| $N$ | Số người | 0, 1, 2, ... | Nhập tay / crowd counting | Biên |
| $V$ | Chỉ số tổn thương | ≥ 0 | **Văn bản** → multi-label | Biên |
| $C$ | Độ tin cậy | (0, 1) | Heuristic tổng hợp | Biên |

### 2.2. Giải thích chi tiết từng thuộc tính

#### 📍 $L$ — Vị trí GPS

```
L = (16.4637, 107.5909)  ← Huế
```

- Lấy từ GPS điện thoại hoặc geo-tag của ảnh
- Dùng để tính khoảng cách Haversine giữa các sự kiện
- **Quan trọng nhất** cho việc gom cụm theo địa lý

#### ⏰ $T$ — Tem thời gian

```
T = 1699012800  ← Unix timestamp (giây từ 1/1/1970)
```

- Dùng để tính độ chênh lệch thời gian giữa các báo cáo
- Hai báo cáo cách nhau vài phút → có thể cùng một diễn biến
- Hai báo cáo cách nhau vài giờ → có thể là hai đợt lũ khác nhau

#### 🌊 $F$ — Mức độ ngập (Flood level)

```
F ∈ [0, 1]

F = 0.0  → Không ngập / khô ráo
F = 0.3  → Ngập nhẹ (ngang mắt cá chân)
F = 0.6  → Ngập vừa (ngang đầu gối)
F = 0.8  → Ngập nặng (ngang ngực)
F = 1.0  → Ngập nóc / chìm hoàn toàn
```

**Cách trích xuất từ ảnh:**
1. Chạy MobileNetV3 (mô hình nhẹ, chạy được trên điện thoại)
2. Semantic segmentation: phân vùng ảnh thành "nước" vs "không phải nước"
3. Tính tỷ lệ vùng nước / tổng ảnh → quy đổi thành $F$

**Hoặc dùng Human Pose Estimation:**
- Nếu thấy người trong ảnh, ước lượng mực nước so với cơ thể
- Nước ngang đầu gối → $F \approx 0.5$

#### 🚨 $E$ — Mức độ khẩn cấp (Emergency)

```
E ∈ [0, 1]

E = 0.2  → "Nước lên chậm, đang theo dõi"
E = 0.5  → "Cần hỗ trợ khi có thể"
E = 0.8  → "Cứu với! Sắp chết đuối!"
E = 1.0  → "SOS! Khẩn cấp tuyệt đối!"
```

**Cách trích xuất từ văn bản:**
1. Chạy DistilBERT (hoặc UIT-VSMEC cho tiếng Việt)
2. Phân tích cảm xúc: lo lắng, hoảng sợ, tuyệt vọng...
3. Quy đổi thành điểm $E$ từ 0 đến 1

**Ví dụ:**
| Văn bản | $E$ |
|:--------|:---:|
| "Nước đang lên, mọi người cẩn thận" | 0.3 |
| "Nhà tôi ngập hết rồi, không biết làm sao" | 0.6 |
| "Cứu! Ông bà tôi kẹt trên mái, nước lên nhanh lắm!" | 0.9 |

#### 👥 $N$ — Số người mắc kẹt

```
N ∈ {0, 1, 2, 3, ...}

N = 1   → Một mình
N = 5   → Một gia đình nhỏ
N = 50  → Cả xóm / khu tập thể
N = 200 → Nghi ngờ là tin giả (cần kiểm tra C)
```

**Nguồn:**
- Người dùng tự nhập khi gửi báo cáo
- Hoặc dùng crowd counting từ ảnh (nếu có nhiều người)

#### 👶👴 $V$ — Chỉ số tổn thương nhân khẩu học

```
V ≥ 0, không có giới hạn trên

V = 0    → Không có đối tượng yếu thế
V = 1    → Có người già hoặc trẻ em
V = 1.5  → Có phụ nữ mang thai / người khuyết tật
V = 2    → Có trẻ sơ sinh / người bệnh nặng
V = 4.5  → Có cả người già (1) + phụ nữ mang thai (1.5) + trẻ sơ sinh (2)
```

**Bảng trọng số:**

| Nhóm đối tượng | Trọng số |
|:---------------|:--------:|
| Không có đối tượng yếu thế | 0 |
| Người già / trẻ em | 1 |
| Phụ nữ mang thai / người khuyết tật | 1.5 |
| Trẻ sơ sinh / người bệnh nặng | 2 |

**Cách trích xuất:**
- Dùng **nhánh multi-label** ghép chung với DistilBERT (cùng mô hình với $E$)
- Phát hiện các cụm từ: "có bà cụ 80 tuổi", "con tôi mới 2 tháng", "vợ tôi đang mang thai"...
- Cộng dồn trọng số của các nhóm phát hiện được

**Tại sao cần $V$?**
- Thảm họa tác động **bất bình đẳng**: người yếu thế suy giảm thể trạng nhanh hơn
- $V$ giúp **khuếch đại ưu tiên** cho những cụm có nhiều đối tượng cần chăm sóc đặc biệt
- Đây là yếu tố **công bằng (equity)** trong cứu hộ

#### ✅ $C$ — Độ tin cậy

```
C ∈ (0, 1)

C = 0.45 → Nghi ngờ tin giả (chỉ có text, không ai xác nhận)
C = 0.70 → Tin cậy trung bình (có ảnh đi kèm)
C = 0.92 → Rất tin cậy (có ảnh + nhiều người xung quanh cũng báo)
```

---

## 3. Công thức Độ tin cậy $C_i$

### 3.1. Công thức

$$
C_i = \sigma\Big(b_0 + b_1 \cdot \mathbb{1}[\text{có ảnh}] + b_2 \cdot \log(1 + n_i^{\text{corrob}})\Big)
$$

### 3.2. Giải thích từng thành phần

#### Hàm Sigmoid $\sigma(x)$

$$
\sigma(x) = \frac{1}{1 + e^{-x}}
$$

```
         1.0 ─────────────────────────────●●●●●
             │                        ●●●
             │                     ●●●
         0.5 │- - - - - - - - - -●- - - - - - -
             │                ●●●
             │             ●●●
         0.0 ●●●●●─────────────────────────────
            -6  -4  -2   0   2   4   6    x
```

**Tác dụng:** Ép mọi giá trị về khoảng (0, 1)
- $x = -\infty$ → $\sigma = 0$
- $x = 0$ → $\sigma = 0.5$
- $x = +\infty$ → $\sigma = 1$

#### Hàm chỉ thị $\mathbb{1}[\text{có ảnh}]$

```
𝟙[có ảnh] = {
    1  nếu báo cáo kèm ảnh/video đã xác thực
    0  nếu chỉ có văn bản
}
```

**Ý nghĩa:** Bằng chứng đa phương thức (ảnh + text) đáng tin hơn chỉ có text

#### Số báo cáo củng cố $n_i^{\text{corrob}}$

```
n_corrob = số báo cáo độc lập trong:
    - Bán kính 400m xung quanh
    - Cửa sổ thời gian 60 phút
```

**Ý nghĩa:** Nhiều người ở cùng khu vực, cùng thời điểm, cùng báo cáo → tin cậy hơn

#### Nén logarit $\log(1 + n)$

```
n_corrob │ log(1+n) │ Tăng so với n trước
─────────┼──────────┼────────────────────
    0    │   0.00   │  -
    1    │   0.69   │  +0.69 (mạnh)
    2    │   1.10   │  +0.41
    3    │   1.39   │  +0.29
   10    │   2.40   │  +0.10/mỗi cái
   50    │   3.93   │  +0.02/mỗi cái (yếu)
```

**Tác dụng:** 
- Báo cáo thứ 2, 3 tăng tin cậy **mạnh**
- Báo cáo thứ 50 gần như **không thêm** gì
- → **Chống spam**: không thể thổi phồng $C$ bằng cách gửi 100 báo cáo giả cùng vị trí

### 3.3. Ví dụ tính toán

**Tham số:** $b_0 = -0.2$, $b_1 = 1.4$, $b_2 = 0.9$

**Trường hợp 1: Tin giả điển hình**
- Chỉ có text, không ảnh: $\mathbb{1} = 0$
- Không ai xung quanh xác nhận: $n = 0$

$$
C = \sigma(-0.2 + 1.4 \times 0 + 0.9 \times \log(1)) = \sigma(-0.2) = 0.45
$$

**Trường hợp 2: Báo cáo thật điển hình**
- Có ảnh đi kèm: $\mathbb{1} = 1$
- 3 hàng xóm cũng báo: $n = 3$

$$
C = \sigma(-0.2 + 1.4 \times 1 + 0.9 \times \log(4)) = \sigma(-0.2 + 1.4 + 1.25) = \sigma(2.45) = 0.92
$$

### 3.4. Tại sao dùng Heuristic thay vì Machine Learning?

| Phương án | Yêu cầu | Khả thi trong 6 tháng? |
|:----------|:--------|:----------------------:|
| Học từ lịch sử người dùng | Hệ thống tài khoản, database dài hạn | ❌ |
| Đối chiếu cảm biến vật lý | Trạm đo mực nước IoT | ❌ |
| **Heuristic sigmoid** | Chỉ cần GPS + timestamp | ✅ |

---

## 4. Kích thước Gói Metadata

### 4.1. Cấu trúc JSON

```json
{
  "lat": 16.4637,
  "lon": 107.5909,
  "ts": 1699012800,
  "F": 0.85,
  "E": 0.72,
  "N": 5,
  "V": 2.5,
  "C": 0.88
}
```

### 4.2. Tính toán kích thước

| Trường | Kích thước |
|:-------|:-----------|
| lat, lon | ~20 ký tự |
| timestamp | ~10 ký tự |
| F, E, C | ~12 ký tự |
| N, V | ~6 ký tự |
| Dấu ngoặc, dấu phẩy | ~30 ký tự |
| **Tổng** | **~100 byte** |

**So sánh:**
- Ảnh JPEG trung bình: **2-5 MB** = 2,000,000 - 5,000,000 byte
- Gói metadata: **100 byte**
- **Tỷ lệ nén: 20,000 - 50,000 lần!**

---

## 5. Code minh họa

### 5.1. Tính $C_i$ trong Python

```python
import numpy as np

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def compute_confidence(has_image: bool, n_corroboration: int,
                       b0=-0.2, b1=1.4, b2=0.9) -> float:
    """
    Tính độ tin cậy C_i theo công thức heuristic.
    
    Args:
        has_image: Báo cáo có kèm ảnh không
        n_corroboration: Số báo cáo độc lập lân cận củng cố
        b0, b1, b2: Hệ số hiệu chỉnh
    
    Returns:
        C_i trong khoảng (0, 1)
    """
    indicator = 1.0 if has_image else 0.0
    log_term = np.log(1 + n_corroboration)
    
    z = b0 + b1 * indicator + b2 * log_term
    return sigmoid(z)

# Ví dụ
print(f"Tin giả (no image, no corrob): C = {compute_confidence(False, 0):.2f}")
print(f"Có ảnh, 3 người xác nhận:      C = {compute_confidence(True, 3):.2f}")
```

Output:
```
Tin giả (no image, no corrob): C = 0.45
Có ảnh, 3 người xác nhận:      C = 0.92
```

### 5.2. Xem code thực tế

Mở file `demo/pipeline/attributes.py` để xem implementation đầy đủ.

---

## 6. Câu hỏi Tự kiểm tra

### Câu hỏi cơ bản

1. **Tại sao cần Edge AI thay vì gửi ảnh lên cloud?**
   <details>
   <summary>Đáp án</summary>
   Vì trong bão lũ, trạm BTS có thể sập, băng thông rất thấp. Gửi ảnh 5MB có thể mất hàng giờ hoặc thất bại. Edge AI xử lý tại chỗ, chỉ gửi 100 byte metadata.
   </details>

2. **Thuộc tính nào trích từ ảnh, thuộc tính nào từ văn bản?**
   <details>
   <summary>Đáp án</summary>
   - Từ ảnh: F (mức ngập) — dùng MobileNetV3
   - Từ văn bản: E (mức khẩn cấp), V (tổn thương) — dùng DistilBERT
   - Tự động: L (GPS), T (timestamp)
   - Nhập tay: N (số người)
   - Tổng hợp: C (tin cậy)
   </details>

3. **$V = 3.5$ có nghĩa gì?**
   <details>
   <summary>Đáp án</summary>
   Có thể là: người già (1) + phụ nữ mang thai (1.5) + trẻ em (1) = 3.5. Hoặc tổ hợp khác với tổng = 3.5.
   </details>

### Câu hỏi nâng cao

4. **Tại sao dùng $\log(1+n)$ thay vì chỉ $n$ trong công thức $C_i$?**
   <details>
   <summary>Đáp án</summary>
   Để chống spam. Nếu dùng $n$ trực tiếp, kẻ xấu có thể gửi 100 báo cáo giả cùng vị trí để thổi phồng $C$. Với log, báo cáo thứ 2-3 tăng mạnh nhưng thứ 50-100 gần như không thêm gì.
   </details>

5. **Một báo cáo có ảnh giả (deepfake) + 5 đồng phạm gửi báo cáo giả xung quanh. $C$ là bao nhiêu?**
   <details>
   <summary>Đáp án</summary>
   $C = \sigma(-0.2 + 1.4 \times 1 + 0.9 \times \log(6)) = \sigma(2.81) = 0.94$
   
   Rất cao! Đây là **giới hạn của hệ thống**: không phân biệt được tấn công phối hợp có tổ chức. Bài báo thừa nhận điều này ở phần đối kháng (Mục 5.9).
   </details>

---

## 7. Liên kết với các Phần khác

| Thuộc tính | Dùng ở đâu tiếp theo |
|:-----------|:---------------------|
| $L$ (GPS) | Mục 4.2 — tính $\mathcal{S}_{geo}$ (khoảng cách không gian) |
| $T$ (time) | Mục 4.2 — tính $\mathcal{S}_{temp}$ (chênh lệch thời gian) |
| $F, E$ | Mục 4.2 — tính $\mathcal{S}_{context}$ (tương đồng ngữ cảnh) |
| $F, E$ | Mục 4.4 — tính $\mathcal{F}_{max}$, $\mathcal{E}_{agg}$ (lõi rủi ro) |
| $N$ | Mục 4.4 — tính $\mathcal{N}_{total}$ (quy mô sinh mạng) |
| $V$ | Mục 4.4 — tính $\mathcal{V}_{agg}$ (hệ số khuếch đại) |
| $C$ | Mục 4.4 — gate cho $\mathcal{E}, \mathcal{F}, \mathcal{N}$ (chống tin giả) |

---

## 8. Tài liệu Tham khảo Thêm

- [MobileNetV3 paper](https://arxiv.org/abs/1905.02244) — kiến trúc CNN nhẹ cho mobile
- [DistilBERT paper](https://arxiv.org/abs/1910.01108) — BERT thu gọn 60%, nhanh gấp đôi
- [UIT-VSMEC](https://github.com/UIT-NLP/UIT-ViSMEC) — phân tích cảm xúc tiếng Việt
