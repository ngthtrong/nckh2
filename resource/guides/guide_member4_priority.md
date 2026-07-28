# Hướng dẫn Thành viên 4: Hàm Ưu tiên Cấp cụm $\mathcal{P}(C_k)$

> **Mục tiêu:** Hiểu cách tính điểm ưu tiên cho mỗi cụm để trả lời câu hỏi "cứu cụm nào trước?"

---

## 1. Bức tranh Tổng quan

Sau khi thuật toán Louvain chia các sự kiện thành các cụm $\{C_1, C_2, ..., C_k\}$, câu hỏi tiếp theo là: **cụm nào cần cứu trước?**

```
Cụm 1: 50 người, ngập nhẹ, không có người yếu thế
Cụm 2: 10 người, ngập nóc, có 3 trẻ sơ sinh
Cụm 3: 200 người, ngập vừa, có 1 người già

→ Xếp hạng như thế nào?
```

Hàm $\mathcal{P}(C_k)$ định lượng mức ưu tiên dựa trên:
- **Mức khẩn cấp** (người ta đang hoảng loạn cỡ nào?)
- **Mức ngập** (nước sâu bao nhiêu?)
- **Số người** (bao nhiêu sinh mạng?)
- **Đối tượng yếu thế** (có trẻ em, người già, phụ nữ mang thai?)

---

## 2. Công thức Chính

$$
\mathcal{P}(C_k) = \underbrace{\mathcal{V}_{agg}(C_k)}_{\text{Hệ số khuếch đại}} \cdot \underbrace{\Big( \omega_1 \widetilde{\mathcal{E}}_{agg} + \omega_2 \widetilde{\mathcal{F}}_{max} + \omega_3 \widetilde{\mathcal{N}} \Big)}_{\text{Lõi rủi ro (đã chuẩn hóa)}}
$$

### 2.1. Cấu trúc "Nhân × Cộng"

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   P(C_k) = V_agg  ×  (ω₁·Ẽ + ω₂·F̃ + ω₃·Ñ)         │
│            ─┬──      ────────────┬────────────      │
│             │                    │                  │
│        Thừa số              Lõi rủi ro              │
│        khuếch đại           [0, 1]                  │
│        [1, 2)                                       │
│                                                     │
│   → Kết quả: P ∈ [0, 2)                            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Tại sao thiết kế như vậy?**
- Lõi rủi ro đo "mức nguy hiểm khách quan"
- $\mathcal{V}_{agg}$ **khuếch đại** (nhân đôi) nếu có đối tượng yếu thế
- Cụm không có người yếu thế: $\mathcal{V}_{agg} = 1$ → giữ nguyên điểm
- Cụm nhiều người yếu thế: $\mathcal{V}_{agg} → 2$ → điểm gấp đôi

---

## 3. Ba Lỗi của Bản gốc và Cách Sửa

### 3.1. Lỗi (a): Sai lệch Thang đo

**Vấn đề:**
```python
# Bản gốc (SAI):
P = ω₁ × E_agg + ω₂ × F_max + ω₃ × N_total

# E_agg ∈ [0, 1]     (mức khẩn cấp)
# F_max ∈ [0, 1]     (mức ngập)
# N_total = 200      (số người - KHÔNG BỊ CHẶN!)

# Kết quả: N_total áp đảo hoàn toàn!
```

**Ví dụ số:**
| Cụm | $E_{agg}$ | $F_{max}$ | $N_{total}$ | $P$ (không chuẩn hóa) |
|:---:|:---------:|:---------:|:-----------:|:---------------------:|
| A | 0.9 | 0.95 | 10 | 0.3×0.9 + 0.3×0.95 + 0.4×10 = **4.56** |
| B | 0.5 | 0.50 | 200 | 0.3×0.5 + 0.3×0.50 + 0.4×200 = **80.30** |

→ Cụm B (ngập nhẹ, ít khẩn cấp) thắng chỉ vì đông người!

**Cách sửa:** Chuẩn hóa tất cả về $[0, 1]$

$$
\widetilde{\mathcal{N}}(C_k) = \frac{\log(1 + \mathcal{N}_{total})}{\log(1 + N_{max})}
$$

```python
# Giả sử N_max = 200 (cụm đông nhất)
# Cụm A: N = 10
N_tilde_A = log(1 + 10) / log(1 + 200) = 2.40 / 5.30 = 0.45

# Cụm B: N = 200  
N_tilde_B = log(1 + 200) / log(1 + 200) = 5.30 / 5.30 = 1.00

# Chênh lệch: 1.00 vs 0.45 (thay vì 200 vs 10 = 20 lần!)
```

**Tại sao dùng log?**
- Phân phối số người **lệch phải** (có vài cụm rất đông)
- Log nén khoảng cách: 10→20 người quan trọng hơn 500→510 người
- Không bị "một cụm siêu đông áp đảo tất cả"

---

### 3.2. Lỗi (b): $\mathcal{V}$ Cộng thay vì Nhân

**Vấn đề:**
```python
# Bản gốc (SAI):
P = ω₁·E + ω₂·F + ω₃·N + ω₄·V_agg

# V_agg ∈ [1, 2] → chỉ là một số hạng cộng thêm
# Không "khuếch đại" gì cả, chỉ là offset!
```

**So sánh hai cách:**

| Cụm | Lõi rủi ro | $V_{agg}$ | Cộng: Lõi + $V$ | Nhân: Lõi × $V$ |
|:---:|:----------:|:---------:|:---------------:|:---------------:|
| X (không yếu thế) | 0.80 | 1.0 | 0.80 + 1.0 = **1.80** | 0.80 × 1.0 = **0.80** |
| Y (nhiều yếu thế) | 0.50 | 1.8 | 0.50 + 1.8 = **2.30** | 0.50 × 1.8 = **0.90** |
| Z (ít yếu thế) | 0.50 | 1.2 | 0.50 + 1.2 = **1.70** | 0.50 × 1.2 = **0.60** |

**Phân tích:**
- **Dạng cộng:** Cụm Y thắng (2.30 > 1.80) — nhưng $V_{agg}$ đóng góp 78% điểm của Y! Yếu thế **áp đảo** thay vì **khuếch đại**.
- **Dạng nhân:** Cụm X thắng (0.80 > 0.90) — rủi ro cao hơn vẫn quan trọng hơn, yếu thế chỉ **nâng thêm** điểm cho cụm có rủi ro.

**Ý nghĩa thực tế:**
- Dạng nhân: "Cụm nguy hiểm có người yếu thế → ưu tiên cao hơn cụm nguy hiểm không có người yếu thế"
- Dạng cộng: "Cụm an toàn nhưng nhiều người yếu thế → có thể thắng cụm nguy hiểm" (SAI!)

---

### 3.3. Lỗi (c): $\tanh$ Bão hòa Quá Sớm

**Vấn đề:**
```python
# Bản gốc (SAI):
V_agg = 1 + tanh(sum(V_i))

# tanh(1) = 0.76
# tanh(2) = 0.96
# tanh(3) = 0.995  ← GẦN NHƯ BÃO HÒA!
# tanh(10) = 0.9999999...

# → Cụm có 3 người yếu thế và cụm có 50 người yếu thế 
#   nhận điểm GẦN NHƯ NHAU!
```

**Đồ thị bão hòa:**
```
V_agg
  2.0 ─────────────────────────────── ← Trần
      │                    ┌─────────
      │                 ┌──┘
  1.5 │              ┌──┘
      │           ┌──┘
      │        ┌──┘
  1.0 ─────────┴───────────────────── ← Sàn
      0    1    2    3    5   10   50
                    ↑
               Bão hòa từ đây!
                   ΣV
```

**Cách sửa:** Thêm hệ số chia $s$

$$
\mathcal{V}_{agg} = 1 + \tanh\left(\frac{\sum V_i}{s}\right), \quad s = 10
$$

```python
# Với s = 10:
# tanh(1/10) = 0.10  → V_agg = 1.10
# tanh(3/10) = 0.29  → V_agg = 1.29
# tanh(10/10) = 0.76 → V_agg = 1.76
# tanh(30/10) = 0.995 → V_agg = 1.995

# → Phân biệt được từ 1 đến 30 người yếu thế!
```

**Bảng so sánh:**

| $\sum V_i$ | Không chia (bão hòa) | Chia $s=10$ |
|:----------:|:--------------------:|:-----------:|
| 1 | 1.76 | 1.10 |
| 3 | **2.00** | 1.29 |
| 10 | **2.00** | 1.76 |
| 30 | **2.00** | 1.99 |
| 50 | **2.00** | **2.00** |

---

## 4. Các Thành phần Lõi Rủi ro

### 4.1. Khẩn cấp Trung bình $\mathcal{E}_{agg}$

$$
\mathcal{E}_{agg}(C_k) = \frac{1}{|C_k|} \sum_{v_i \in C_k} E_i \cdot C_i
$$

```python
# Ví dụ cụm có 3 sự kiện:
# Sự kiện 1: E=0.9, C=0.95 (tin cậy cao)
# Sự kiện 2: E=0.8, C=0.90
# Sự kiện 3: E=0.7, C=0.40 (tin cậy thấp - có thể giả)

E_agg = (0.9×0.95 + 0.8×0.90 + 0.7×0.40) / 3
      = (0.855 + 0.720 + 0.280) / 3
      = 0.618

# Sự kiện 3 đóng góp ít hơn vì C_i thấp!
```

**Tại sao nhân $C_i$?** Báo cáo đáng tin đóng góp nhiều hơn vào mức khẩn cấp chung.

### 4.2. Ngập Tối đa $\mathcal{F}_{max}$

$$
\mathcal{F}_{max}(C_k) = \max_{v_i \in C_k}(F_i \cdot C_i)
$$

```python
# Cùng cụm 3 sự kiện:
# Sự kiện 1: F=0.6, C=0.95 → F×C = 0.57
# Sự kiện 2: F=0.8, C=0.90 → F×C = 0.72
# Sự kiện 3: F=0.99, C=0.40 → F×C = 0.40 (tin giả khai ngập cao!)

F_max = max(0.57, 0.72, 0.40) = 0.72

# Nếu KHÔNG nhân C_i:
# F_max = max(0.6, 0.8, 0.99) = 0.99 ← Tin giả chiếm trọn!
```

**Tại sao dùng max thay vì trung bình?**
- **Nguyên lý bình thông nhau:** Trong một vùng địa lý, điểm ngập sâu nhất quyết định rủi ro của cả khu vực
- Trung bình sẽ làm loãng cảnh báo khi chỉ vài điểm ngập nặng

**Tại sao nhân $C_i$ bên trong max?**
- Bản gốc: $\max F_i$ — tin giả khai $F=0.99$ sẽ chiếm trọn
- Bản sửa: $\max(F_i \cdot C_i)$ — tin giả bị "hạ nhiệt" bởi $C_i$ thấp

### 4.3. Quy mô Sinh mạng $\mathcal{N}_{total}$

$$
\mathcal{N}_{total}(C_k) = \sum_{v_i \in C_k} N_i \cdot C_i
$$

```python
# Ví dụ:
# Sự kiện 1: N=10, C=0.95 → đóng góp 9.5
# Sự kiện 2: N=20, C=0.90 → đóng góp 18.0
# Sự kiện 3: N=500, C=0.40 → đóng góp 200 (tin giả thổi phồng!)

N_total = 9.5 + 18.0 + 200 = 227.5

# Nếu KHÔNG nhân C_i:
# N_total = 10 + 20 + 500 = 530 ← Tin giả chiếm 94%!

# Giảm từ 530 xuống 227.5 = giảm 57%
```

---

## 5. Hệ số Khuếch đại $\mathcal{V}_{agg}$

### 5.1. Công thức

$$
\mathcal{V}_{agg}(C_k) = 1 + \tanh\left(\frac{1}{s} \sum_{v_i \in C_k} V_i\right)
$$

### 5.2. Định nghĩa $V_i$

| Nhóm phát hiện | Trọng số $V_i$ |
|:---------------|:--------------:|
| Không có đối tượng yếu thế | 0 |
| Người già / trẻ em | 1 |
| Phụ nữ mang thai / người khuyết tật | 1.5 |
| Trẻ sơ sinh / người bệnh nặng | 2 |

```python
# Ví dụ cụm có:
# - 2 người già: 2 × 1 = 2
# - 1 phụ nữ mang thai: 1 × 1.5 = 1.5
# - 1 trẻ sơ sinh: 1 × 2 = 2

sum_V = 2 + 1.5 + 2 = 5.5
V_agg = 1 + tanh(5.5 / 10) = 1 + 0.50 = 1.50

# Điểm ưu tiên được nhân 1.5 lần!
```

### 5.3. Trần Khuếch đại $\mu$

$$
\mathcal{V}_{agg} = 1 + (\mu - 1) \cdot \tanh\left(\frac{\sum V_i}{s}\right)
$$

- $\mu = 1$: Tắt hoàn toàn ưu tiên yếu thế
- $\mu = 2$: Cho phép nhân đôi tối đa (mặc định)
- $\mu$ là **núm chính sách** do ban chỉ huy đặt

---

## 6. Trọng số $\omega$ và Ma trận Quyết định

### 6.1. Ràng buộc

$$
\omega_1 + \omega_2 + \omega_3 = 1
$$

### 6.2. Ý nghĩa Chiến thuật

| Tình huống | $\omega_1$ (Khẩn cấp) | $\omega_2$ (Ngập) | $\omega_3$ (Số người) |
|:-----------|:---------------------:|:-----------------:|:---------------------:|
| Bình thường | 0.34 | 0.33 | 0.33 |
| Nước dâng nhanh | 0.20 | **0.50** | 0.30 |
| Nhiều điểm hoảng loạn | **0.50** | 0.25 | 0.25 |
| Tập trung đông | 0.25 | 0.25 | **0.50** |

### 6.3. Độ Ổn định Xếp hạng

Thí nghiệm 5 cho thấy: khi nhiễu loạn $\omega$ ±10%, Kendall's τ vẫn đạt **0.955** — xếp hạng khá ổn định với lựa chọn $\omega$ của ban chỉ huy.

---

## 7. Ví dụ Tính toán Đầy đủ

### Dữ liệu: Cụm gồm 4 sự kiện

| Sự kiện | $E_i$ | $F_i$ | $N_i$ | $V_i$ | $C_i$ |
|:-------:|:-----:|:-----:|:-----:|:-----:|:-----:|
| 1 | 0.8 | 0.7 | 15 | 1 (người già) | 0.92 |
| 2 | 0.9 | 0.85 | 20 | 0 | 0.88 |
| 3 | 0.7 | 0.6 | 10 | 2 (trẻ sơ sinh) | 0.95 |
| 4 | 0.6 | 0.5 | 8 | 0 | 0.85 |

### Bước 1: Tính các thành phần

```python
# E_agg (khẩn cấp trung bình có trọng số)
E_agg = (0.8×0.92 + 0.9×0.88 + 0.7×0.95 + 0.6×0.85) / 4
      = (0.736 + 0.792 + 0.665 + 0.510) / 4
      = 0.676

# F_max (ngập tối đa có trọng số)
F_max = max(0.7×0.92, 0.85×0.88, 0.6×0.95, 0.5×0.85)
      = max(0.644, 0.748, 0.570, 0.425)
      = 0.748

# N_total (dân số có trọng số)
N_total = 15×0.92 + 20×0.88 + 10×0.95 + 8×0.85
        = 13.8 + 17.6 + 9.5 + 6.8
        = 47.7

# V_agg (hệ số khuếch đại)
sum_V = 1 + 0 + 2 + 0 = 3
V_agg = 1 + tanh(3/10) = 1 + 0.291 = 1.291
```

### Bước 2: Chuẩn hóa (giả sử $N_{max} = 100$)

```python
E_tilde = 0.676  # đã trong [0,1]
F_tilde = 0.748  # đã trong [0,1]
N_tilde = log(1 + 47.7) / log(1 + 100)
        = 3.89 / 4.62
        = 0.842
```

### Bước 3: Tính điểm ưu tiên

```python
# Với ω = (0.34, 0.33, 0.33)
loi_rui_ro = 0.34×0.676 + 0.33×0.748 + 0.33×0.842
           = 0.230 + 0.247 + 0.278
           = 0.755

P = V_agg × loi_rui_ro
  = 1.291 × 0.755
  = 0.975
```

**Kết quả:** Cụm này có điểm ưu tiên **P = 0.975** (trên thang 0-2).

---

## 8. Code Tham khảo

File: [demo/pipeline/priority.py](../../demo/pipeline/priority.py)

```python
def compute_priority(cluster_events, N_max, omega=(0.34, 0.33, 0.33), s=10):
    """
    Tính điểm ưu tiên P(C_k) cho một cụm.
    
    Args:
        cluster_events: List các sự kiện trong cụm, mỗi sự kiện có E, F, N, V, C
        N_max: Mốc dân số tham chiếu (cụm đông nhất)
        omega: Tuple (ω1, ω2, ω3) trọng số
        s: Hệ số chống bão hòa tanh
    
    Returns:
        P: Điểm ưu tiên trong khoảng [0, 2)
    """
    # Tính các thành phần lõi
    E_agg = np.mean([e.E * e.C for e in cluster_events])
    F_max = max(e.F * e.C for e in cluster_events)
    N_total = sum(e.N * e.C for e in cluster_events)
    
    # Chuẩn hóa N
    N_tilde = np.log(1 + N_total) / np.log(1 + N_max)
    
    # Tính V_agg
    sum_V = sum(e.V for e in cluster_events)
    V_agg = 1 + np.tanh(sum_V / s)
    
    # Tính P
    core = omega[0] * E_agg + omega[1] * F_max + omega[2] * N_tilde
    P = V_agg * core
    
    return P
```

---

## 9. Câu hỏi Tự kiểm tra

1. **Tại sao $\mathcal{V}_{agg}$ phải là thừa số nhân?**
   - Gợi ý: So sánh hành vi khi lõi rủi ro = 0 vs lõi rủi ro = 0.8

2. **Nếu một cụm có 500 người nhưng tất cả $C_i = 0.2$ (tin giả), điểm $\widetilde{\mathcal{N}}$ thay đổi thế nào?**
   - Tính: $N_{total} = 500 \times 0.2 = 100$ thay vì 500

3. **$s = 10$ có ý nghĩa gì? Nếu đặt $s = 1$ thì sao?**
   - Gợi ý: Xem bảng so sánh bão hòa ở mục 3.3

4. **Tại sao $\mathcal{F}_{max}$ dùng max thay vì mean?**
   - Gợi ý: Nguyên lý bình thông nhau

5. **Ban chỉ huy muốn ưu tiên cứu điểm ngập sâu trước, đặt $\omega$ như thế nào?**
   - Gợi ý: Tăng $\omega_2$, giảm $\omega_1$ và $\omega_3$

---

## 10. Tài liệu Liên quan

- **Mục 4.4** trong [BaiBao_NoiDung.md](../BaiBao_NoiDung.md)
- **Mục 4** trong [GiaiThichCongThuc.md](../GiaiThichCongThuc.md)
- **Thí nghiệm 1** (1B, 1C, 1D, 1E, 1F) và **Thí nghiệm 5** trong bài báo
- Code: [demo/pipeline/priority.py](../../demo/pipeline/priority.py)
