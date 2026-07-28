# Hướng dẫn Thành viên 2: Đồ thị Trọng số & Công thức Gating

> **Phạm vi:** Mục 4.2 của bài báo — Xây dựng đồ thị trọng số không gian – ngữ nghĩa – vật lý

---

## 1. Ý tưởng Cốt lõi: Tại sao dùng Đồ thị?

### 1.1. Vấn đề với dữ liệu rời rạc

Sau khi thu thập, ta có **danh sách các sự kiện** độc lập:

```
Sự kiện 1: GPS(16.46, 107.59), ngập 0.8, khẩn cấp 0.9, 5 người
Sự kiện 2: GPS(16.47, 107.60), ngập 0.7, khẩn cấp 0.8, 3 người
Sự kiện 3: GPS(15.88, 108.32), ngập 0.9, khẩn cấp 0.95, 10 người
...
```

**Câu hỏi:** Sự kiện nào nên được gom vào cùng một "khu vực tác chiến"?

### 1.2. Đồ thị như công cụ mô hình hóa quan hệ

```
┌─────────────────────────────────────────────────────────────┐
│                    ĐỒ THỊ TRỌNG SỐ                          │
│                                                             │
│         (1)●━━━━━━━0.85━━━━━━━●(2)                          │
│            ╲                   ╱                            │
│             ╲                 ╱                             │
│           0.02             0.01                             │
│               ╲           ╱                                 │
│                ╲         ╱                                  │
│                 ╲       ╱                                   │
│                  ●(3)                                       │
│                                                             │
│    Trọng số cao (0.85): nên gom cùng cụm                   │
│    Trọng số thấp (0.01, 0.02): nên tách riêng              │
└─────────────────────────────────────────────────────────────┘
```

**Định nghĩa:**
- **Đỉnh (node):** Mỗi sự kiện cứu hộ là một đỉnh
- **Cạnh (edge):** Nối hai sự kiện nếu chúng "có liên quan"
- **Trọng số (weight):** Đo mức độ liên quan, càng cao càng nên gom cùng cụm

---

## 2. Công thức Trọng số Cạnh: Gating vs Cộng

### 2.1. Dạng Cộng (SAI - bản gốc)

$$
w_{ij} = \alpha \mathcal{S}_{geo} + \beta \mathcal{S}_{temp} + \gamma \mathcal{S}_{context}
$$

**Vấn đề minh họa:**

```
Sự kiện A: Huế (16.46°N)      ─────  90 km  ─────  Sự kiện B: Đà Nẵng (16.05°N)
           "ngập nóc nhà"                                   "ngập nóc nhà"

S_geo ≈ 0 (cách xa)
S_context ≈ 1 (ngữ cảnh giống nhau)

Với α = β = γ = 1/3:
w_AB = 0.33 × 0 + 0.33 × 0.5 + 0.33 × 1 = 0.50  ← vẫn khá cao!
```

**Hậu quả:** Thuật toán gom Huế và Đà Nẵng vào **cùng một cụm**, dù cách nhau 90km. Ca nô không thể phục vụ cả hai!

### 2.2. Dạng Nhân/Gating (ĐÚNG - đề xuất)

$$
w_{ij} = \mathcal{S}_{geo}(L_i, L_j) \cdot \Big( \beta \cdot \mathcal{S}_{temp}(T_i, T_j) + \gamma \cdot \mathcal{S}_{context}(v_i, v_j) \Big)
$$

**Cùng ví dụ:**

```
w_AB = 0 × (0.5 × 0.5 + 0.5 × 1) = 0 × 0.75 = 0  ← KHÔNG liên kết!
```

**Cơ chế Gating:**
- $\mathcal{S}_{geo}$ nằm **ngoài** làm **thừa số nhân** (cổng chặn)
- Khi khoảng cách lớn → $\mathcal{S}_{geo} \to 0$ → $w_{ij} \to 0$ **bất kể** ngữ cảnh giống đến đâu
- Địa lý trở thành **điều kiện tiên quyết** cho việc gom cụm

### 2.3. So sánh trực quan

```
┌─────────────────────────────────────────────────────────────┐
│                    DẠNG CỘNG (SAI)                          │
│                                                             │
│    ●(Huế)━━━━━━━━━━━w=0.50━━━━━━━━━━●(Đà Nẵng)             │
│    "ngập nóc"                        "ngập nóc"             │
│                                                             │
│    → Gom vào CÙNG cụm! Đường kính cụm = 90 km              │
│    → Vô nghĩa cho điều phối ca nô                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    DẠNG GATING (ĐÚNG)                       │
│                                                             │
│    ●(Huế)         w=0          ●(Đà Nẵng)                  │
│    "ngập nóc"   (không liên kết)  "ngập nóc"               │
│                                                             │
│    → Hai cụm RIÊNG BIỆT                                    │
│    → Đường kính mỗi cụm < 2 km                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Thành phần Không gian: $\mathcal{S}_{geo}$

### 3.1. Công thức

$$
\mathcal{S}_{geo} = \exp\left( - \frac{\text{dist}(L_i, L_j)^2}{2\sigma_{geo}^2} \right)
$$

### 3.2. Giải thích

Đây là **nhân Gaussian (Gaussian kernel)**:

```
S_geo
  1.0 ┤●
      │ ●
      │  ●
  0.6 ┤   ●                    ← dist = σ_geo → S = 0.61
      │    ●
      │     ●
  0.4 ┤      ●
      │       ●
      │        ●●
  0.1 ┤          ●●●           ← dist = 2σ_geo → S = 0.14
      │             ●●●●●●●●●●●●●●●●●●●●
  0.0 └──────────────────────────────────→ dist (m)
      0    σ    2σ    3σ    4σ    5σ
```

### 3.3. Ý nghĩa các thành phần

| Thành phần | Ý nghĩa |
|:-----------|:--------|
| $\text{dist}(L_i, L_j)$ | Khoảng cách Haversine (mét) giữa hai tọa độ GPS |
| $\sigma_{geo}$ | Bán kính đặc trưng — tầm hoạt động của ca nô |
| $\text{dist}^2$ | Bình phương → suy giảm RẤT nhanh |

### 3.4. Công thức Haversine

```python
import numpy as np

def haversine(lat1, lon1, lat2, lon2):
    """Khoảng cách giữa 2 điểm trên mặt cầu (mét)."""
    R = 6_371_000  # Bán kính Trái Đất (m)
    
    φ1, φ2 = np.radians(lat1), np.radians(lat2)
    Δφ = np.radians(lat2 - lat1)
    Δλ = np.radians(lon2 - lon1)
    
    a = np.sin(Δφ/2)**2 + np.cos(φ1) * np.cos(φ2) * np.sin(Δλ/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    
    return R * c
```

**Tại sao Haversine thay vì Euclidean?**
- Euclidean coi lat/lon như tọa độ Descartes phẳng → sai số lớn
- Haversine tính trên mặt cầu → chính xác cho khoảng cách địa lý

### 3.5. Chọn $\sigma_{geo}$

| $\sigma_{geo}$ | Ý nghĩa | Phù hợp với |
|:--------------:|:--------|:------------|
| 200m | Rất chặt | Xuồng nhỏ, khu vực đô thị dày đặc |
| **700m** | Mặc định | Ca nô cứu hộ điển hình |
| 1500m | Rộng | Vùng nông thôn, phương tiện lớn |

**Bảng giá trị $\mathcal{S}_{geo}$ với $\sigma_{geo} = 700m$:**

| Khoảng cách | $\mathcal{S}_{geo}$ | Diễn giải |
|:-----------:|:-------------------:|:----------|
| 0m | 1.00 | Trùng vị trí |
| 350m | 0.88 | Rất gần |
| 700m | 0.61 | Ở mức $\sigma$ |
| 1400m | 0.14 | Xa |
| 2100m | 0.01 | Rất xa |
| 3000m | 0.00 | Không liên kết |

---

## 4. Thành phần Thời gian: $\mathcal{S}_{temp}$

### 4.1. Công thức

$$
\mathcal{S}_{temp} = \exp\left( - \frac{|T_i - T_j|}{\tau_{temp}} \right)
$$

### 4.2. Giải thích

Đây là **suy giảm mũ (exponential decay)**:

```
S_temp
  1.0 ┤●
      │ ●
      │  ●
  0.6 ┤   ●
      │    ●
      │     ●
  0.4 ┤      ●                 ← Δt = τ → S = 0.37
      │       ●
      │        ●
  0.2 ┤         ●●
      │           ●●●
  0.0 ┤              ●●●●●●●●●●●●●●●●●●●●●●●●●
      └────────────────────────────────────────→ Δt (phút)
      0    τ    2τ    3τ    4τ    5τ
```

### 4.3. So sánh với $\mathcal{S}_{geo}$

| Đặc điểm | $\mathcal{S}_{geo}$ | $\mathcal{S}_{temp}$ |
|:---------|:-------------------:|:--------------------:|
| Dạng | Gaussian ($x^2$) | Exponential ($x$) |
| Tốc độ suy giảm | RẤT nhanh | Chậm hơn |
| Lý do | Địa lý cần phạt gắt | Thời gian có quán tính |

**Tại sao thời gian dùng bậc 1 thay vì bậc 2?**
- Diễn biến lũ có **quán tính**: tình huống không thay đổi tức thì
- Hai báo cáo cách 1 giờ vẫn có thể liên quan đến cùng đợt lũ
- → Không cần phạt gắt như không gian

### 4.4. Chọn $\tau_{temp}$

| $\tau_{temp}$ | Ý nghĩa |
|:-------------:|:--------|
| 15 phút | Lũ quét, thay đổi nhanh |
| **45 phút** | Mặc định, lũ sông điển hình |
| 120 phút | Ngập úng đô thị, thay đổi chậm |

**Bảng giá trị $\mathcal{S}_{temp}$ với $\tau_{temp} = 45$ phút:**

| Chênh lệch thời gian | $\mathcal{S}_{temp}$ |
|:--------------------:|:--------------------:|
| 0 phút | 1.00 |
| 15 phút | 0.72 |
| 45 phút | 0.37 |
| 90 phút | 0.14 |
| 180 phút | 0.02 |

---

## 5. Thành phần Ngữ cảnh: $\mathcal{S}_{context}$

### 5.1. Công thức

$$
\mathcal{S}_{context} = \exp\left( - \frac{|F_i - F_j|}{\tau_F} - \frac{|E_i - E_j|}{\tau_E} \right)
$$

### 5.2. Giải thích

Đo **sự tương đồng về tình trạng vật lý** giữa hai sự kiện:

```
Sự kiện A: F = 0.85 (ngập nặng), E = 0.90 (rất khẩn cấp)
Sự kiện B: F = 0.80 (ngập nặng), E = 0.85 (khẩn cấp)

ΔF = |0.85 - 0.80| = 0.05
ΔE = |0.90 - 0.85| = 0.05

S_context = exp(-0.05/0.25 - 0.05/0.35) = exp(-0.34) = 0.71  ← Tương đồng cao
```

```
Sự kiện A: F = 0.90 (ngập nặng), E = 0.95 (cực kỳ khẩn cấp)
Sự kiện C: F = 0.20 (ngập nhẹ), E = 0.30 (bình thường)

ΔF = |0.90 - 0.20| = 0.70
ΔE = |0.95 - 0.30| = 0.65

S_context = exp(-0.70/0.25 - 0.65/0.35) = exp(-4.66) = 0.01  ← Rất khác biệt
```

### 5.3. Tại sao $\tau_E > \tau_F$?

| Tham số | Giá trị | Lý do |
|:--------|:-------:|:------|
| $\tau_F$ | 0.25 | Mức ngập từ ảnh → **ít nhiễu**, phạt gắt hơn |
| $\tau_E$ | 0.35 | Mức khẩn cấp từ văn bản → **nhiễu hơn**, khoan dung hơn |

### 5.4. Tính chất nhân của exp

$$
\exp(-a - b) = \exp(-a) \cdot \exp(-b)
$$

**Ý nghĩa:** Hai điều kiện phải **ĐỒNG THỜI** thỏa mãn:
- Giống về mức ngập (ΔF nhỏ) **VÀ**
- Giống về mức khẩn cấp (ΔE nhỏ)

Nếu một trong hai khác biệt lớn → $\mathcal{S}_{context}$ vẫn thấp.

---

## 6. Công thức Tổng hợp

### 6.1. Công thức đầy đủ

$$
w_{ij} = \underbrace{\exp\left( - \frac{\text{dist}^2}{2\sigma_{geo}^2} \right)}_{\text{Cổng địa lý}} \cdot \left( \beta \cdot \underbrace{\exp\left( - \frac{|\Delta T|}{\tau_{temp}} \right)}_{\text{Thời gian}} + \gamma \cdot \underbrace{\exp\left( - \frac{|\Delta F|}{\tau_F} - \frac{|\Delta E|}{\tau_E} \right)}_{\text{Ngữ cảnh}} \right)
$$

### 6.2. Tham số mặc định

| Tham số | Giá trị | Ý nghĩa |
|:--------|:-------:|:--------|
| $\sigma_{geo}$ | 700m | Bán kính hoạt động ca nô |
| $\tau_{temp}$ | 45 phút | Quán tính diễn biến lũ |
| $\tau_F$ | 0.25 | Độ gắt so khớp mức ngập |
| $\tau_E$ | 0.35 | Độ khoan dung so khớp khẩn cấp |
| $\beta$ | 0.5 | Trọng số thời gian |
| $\gamma$ | 0.5 | Trọng số ngữ cảnh |

### 6.3. Ví dụ tính toán đầy đủ

**Hai sự kiện:**
- A: GPS(16.4637, 107.5909), T=10:00, F=0.85, E=0.90
- B: GPS(16.4650, 107.5920), T=10:20, F=0.80, E=0.85

**Bước 1: Tính khoảng cách**
```
dist = haversine(16.4637, 107.5909, 16.4650, 107.5920) ≈ 180m
```

**Bước 2: Tính $\mathcal{S}_{geo}$**
```
S_geo = exp(-180² / (2 × 700²)) = exp(-0.033) = 0.97
```

**Bước 3: Tính $\mathcal{S}_{temp}$**
```
ΔT = 20 phút
S_temp = exp(-20 / 45) = exp(-0.44) = 0.64
```

**Bước 4: Tính $\mathcal{S}_{context}$**
```
ΔF = |0.85 - 0.80| = 0.05
ΔE = |0.90 - 0.85| = 0.05
S_context = exp(-0.05/0.25 - 0.05/0.35) = exp(-0.34) = 0.71
```

**Bước 5: Tổng hợp**
```
w_AB = 0.97 × (0.5 × 0.64 + 0.5 × 0.71)
     = 0.97 × 0.675
     = 0.65
```

→ Trọng số **0.65**: hai sự kiện này nên được gom cùng cụm.

---

## 7. Làm thưa Đồ thị (Sparsification)

### 7.1. Vấn đề với đồ thị dày đặc

Với $N = 341$ sự kiện:
- Số cạnh tiềm năng: $\frac{N(N-1)}{2} = 58,140$ cạnh
- Đa số cạnh có trọng số gần 0 (các điểm xa nhau)
- Giữ hết → đồ thị **gần hoàn chỉnh** → Louvain hoạt động kém

### 7.2. Hai cách làm thưa

#### Cách 1: Ngưỡng $\epsilon$ (threshold)

```
Chỉ giữ cạnh nếu w_ij > θ

Ví dụ với θ = 0.05:
- w = 0.65 → GIỮ
- w = 0.03 → BỎ
- w = 0.00001 → BỎ
```

#### Cách 2: k-NN graph

```
Mỗi đỉnh chỉ giữ k láng giềng có trọng số cao nhất

Ví dụ với k = 12:
- Đỉnh A giữ 12 cạnh mạnh nhất của nó
- Đỉnh B giữ 12 cạnh mạnh nhất của nó
- Cạnh được giữ nếu NẰM TRONG top-k của ÍT NHẤT MỘT đầu
```

### 7.3. Hiệu quả

| Cấu hình | Số cạnh | Tỷ lệ giữ |
|:---------|:-------:|:---------:|
| Đồ thị đầy đủ | 58,140 | 100% |
| Ngưỡng θ = 0.05 | ~4,800 | 8.3% |
| k-NN, k = 12 | ~4,100 | 7.0% |

---

## 8. Code minh họa

### 8.1. Tính trọng số cạnh

```python
import numpy as np

def compute_edge_weight(event_i, event_j, 
                        sigma_geo=700, tau_temp=45,
                        tau_F=0.25, tau_E=0.35,
                        beta=0.5, gamma=0.5):
    """
    Tính trọng số cạnh w_ij theo công thức gating.
    
    Args:
        event_i, event_j: dict với keys 'lat', 'lon', 'T', 'F', 'E'
    
    Returns:
        w_ij: trọng số cạnh
    """
    # Khoảng cách địa lý (Haversine)
    dist = haversine(event_i['lat'], event_i['lon'],
                     event_j['lat'], event_j['lon'])
    
    # S_geo (Gaussian kernel)
    S_geo = np.exp(-dist**2 / (2 * sigma_geo**2))
    
    # S_temp (exponential decay)
    delta_T = abs(event_i['T'] - event_j['T']) / 60  # chuyển sang phút
    S_temp = np.exp(-delta_T / tau_temp)
    
    # S_context
    delta_F = abs(event_i['F'] - event_j['F'])
    delta_E = abs(event_i['E'] - event_j['E'])
    S_context = np.exp(-delta_F / tau_F - delta_E / tau_E)
    
    # Gating formula
    w_ij = S_geo * (beta * S_temp + gamma * S_context)
    
    return w_ij
```

### 8.2. Xây dựng đồ thị thưa

```python
import networkx as nx

def build_sparse_graph(events, threshold=0.05):
    """
    Xây đồ thị trọng số với ngưỡng làm thưa.
    """
    G = nx.Graph()
    
    # Thêm đỉnh
    for i, event in enumerate(events):
        G.add_node(i, **event)
    
    # Thêm cạnh (chỉ giữ nếu w > threshold)
    n = len(events)
    for i in range(n):
        for j in range(i+1, n):
            w = compute_edge_weight(events[i], events[j])
            if w > threshold:
                G.add_edge(i, j, weight=w)
    
    return G
```

### 8.3. Xem code thực tế

Mở file `demo/pipeline/weighting.py` để xem implementation đầy đủ.

---

## 9. Thí nghiệm Kiểm chứng

### 9.1. Kịch bản S1: Hai điểm ngữ cảnh giống, cách xa 106km

```
Điểm S1a (Huế):      F=0.95, E=0.92  ─── 106.8 km ───  Điểm S1b: F=0.94, E=0.91
                     "ngập nóc nhà"                    "ngập nóc nhà"
```

| Dạng công thức | $w_{ij}$ | Kết quả phân cụm |
|:---------------|:--------:|:-----------------|
| Cộng ($\alpha=0.5$) | 0.42 | Gom cùng cụm ❌ |
| **Gating** | 0.00 | Tách riêng ✓ |

### 9.2. Kết quả tổng thể (Thí nghiệm 1A)

| Dạng | ARI | Đường kính TB | Đường kính max |
|:-----|:---:|:-------------:|:--------------:|
| Cộng (tốt nhất) | 0.957 | 140 km | 214 km |
| **Gating** | **0.996** | **0.85 km** | **1.41 km** |

**Hệ số cải thiện đường kính: 151×**

---

## 10. Câu hỏi Tự kiểm tra

### Câu hỏi cơ bản

1. **Tại sao dạng nhân (gating) tốt hơn dạng cộng?**
   <details>
   <summary>Đáp án</summary>
   Vì dạng nhân đặt $S_{geo}$ làm thừa số ngoài. Khi khoảng cách lớn, $S_{geo} \to 0$ nên $w_{ij} \to 0$ bất kể ngữ cảnh. Còn dạng cộng cho phép ngữ cảnh "bù" cho khoảng cách, gây ra cụm trải dài vô nghĩa.
   </details>

2. **$\sigma_{geo} = 700m$ có ý nghĩa gì?**
   <details>
   <summary>Đáp án</summary>
   Đó là bán kính đặc trưng, xấp xỉ tầm hoạt động của một ca nô cứu hộ. Tại khoảng cách này, $S_{geo} = 0.61$. Xa hơn 2-3 lần $\sigma_{geo}$ thì gần như không liên kết.
   </details>

3. **Tại sao $\mathcal{S}_{geo}$ dùng $\text{dist}^2$ còn $\mathcal{S}_{temp}$ chỉ dùng $|\Delta T|$?**
   <details>
   <summary>Đáp án</summary>
   Địa lý cần phạt GẮT (hai nơi cách xa thì chắc chắn không liên quan về mặt điều phối). Thời gian có QUÁN TÍNH (lũ diễn biến chậm, hai báo cáo cách 1 giờ vẫn có thể liên quan), nên phạt nhẹ hơn.
   </details>

### Câu hỏi nâng cao

4. **Tính $w_{ij}$ cho hai sự kiện: A(cách 500m, cách 30 phút, F=0.7, E=0.8) và B(F=0.75, E=0.85)?**
   <details>
   <summary>Đáp án</summary>
   
   ```
   S_geo = exp(-500²/(2×700²)) = exp(-0.255) = 0.775
   S_temp = exp(-30/45) = exp(-0.667) = 0.513
   ΔF = 0.05, ΔE = 0.05
   S_context = exp(-0.05/0.25 - 0.05/0.35) = exp(-0.343) = 0.710
   
   w = 0.775 × (0.5 × 0.513 + 0.5 × 0.710)
     = 0.775 × 0.612
     = 0.474
   ```
   </details>

5. **Tại sao cần làm thưa đồ thị?**
   <details>
   <summary>Đáp án</summary>
   Vì thuật toán Louvain (tối ưu Modularity) hoạt động kém trên đồ thị dày đặc gần-hoàn-chỉnh. Các cạnh xa có trọng số gần 0 chỉ gây nhiễu, không mang thông tin. Làm thưa giúp Louvain tập trung vào các liên kết thực sự có ý nghĩa.
   </details>

---

## 11. Liên kết với các Phần khác

| Thành phần | Nguồn từ | Đưa đến |
|:-----------|:---------|:--------|
| $L_i, L_j$ (GPS) | Mục 4.1 | → Tính $\mathcal{S}_{geo}$ |
| $T_i, T_j$ (time) | Mục 4.1 | → Tính $\mathcal{S}_{temp}$ |
| $F_i, E_i$ | Mục 4.1 | → Tính $\mathcal{S}_{context}$ |
| **Đồ thị $G(V,E,W)$** | **Mục này** | → **Mục 4.3** (Louvain) |

---

## 12. Tài liệu Tham khảo Thêm

- [Haversine formula](https://en.wikipedia.org/wiki/Haversine_formula) — công thức tính khoảng cách trên mặt cầu
- [Gaussian kernel](https://en.wikipedia.org/wiki/Radial_basis_function_kernel) — nhân RBF trong machine learning
- [NetworkX documentation](https://networkx.org/documentation/stable/) — thư viện đồ thị Python
