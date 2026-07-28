# Hướng dẫn Thành viên 3: Thuật toán Phân cụm Louvain/Leiden

> **Mục tiêu:** Hiểu cách phân chia các sự kiện cứu hộ thành các "khu vực tác chiến" bằng thuật toán phát hiện cộng đồng trên đồ thị.

---

## 1. Bối cảnh: Tại sao cần Phân cụm?

### 1.1. Vấn đề thực tế

Trong một trận lũ, trung tâm chỉ huy nhận được **hàng trăm** lời kêu cứu. Không thể điều một ca nô đến từng điểm riêng lẻ. Cần **gom nhóm** các điểm gần nhau thành "khu vực tác chiến" để:
- Một đội cứu hộ phụ trách một khu vực
- Tối ưu quãng đường di chuyển
- Tránh bỏ sót hoặc trùng lặp

### 1.2. Tại sao không dùng K-Means?

| Vấn đề | K-Means | Louvain |
|:-------|:--------|:--------|
| Cần biết trước số cụm $K$ | ✗ Bắt buộc | ✓ Tự tìm |
| Hình dạng cụm | Chỉ hình cầu | Bất kỳ |
| Dùng được trọng số cạnh | ✗ Không | ✓ Có |
| Xử lý nhiễu | ✗ Kém | ✓ Tốt (đẩy thành cụm đơn lẻ) |

**Trong thảm họa:** Không ai biết trước sẽ có bao nhiêu "ốc đảo ngập". K-Means yêu cầu đoán $K$ — sai thì kết quả vô nghĩa.

---

## 2. Khái niệm Modularity $Q$

### 2.1. Ý tưởng trực giác

Modularity đo **chất lượng** của một cách chia cụm:
- **$Q$ cao:** Các cạnh nằm **trong** cụm nhiều hơn kỳ vọng ngẫu nhiên → chia tốt
- **$Q$ thấp:** Cạnh rải đều giữa các cụm → chia tệ

### 2.2. Công thức

$$
Q = \frac{1}{2m} \sum_{i,j} \left[ A_{ij} - \lambda \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)
$$

### 2.3. Giải thích từng thành phần

```
┌─────────────────────────────────────────────────────────────┐
│                    PHÂN TÍCH CÔNG THỨC Q                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   A_ij  ─────→  Trọng số cạnh thực tế (từ Mục 4.2)         │
│                 = w_ij đã tính bằng công thức gating        │
│                                                             │
│   k_i   ─────→  "Độ quan trọng" của đỉnh i                 │
│                 = Tổng trọng số các cạnh nối với i          │
│                 = Σⱼ A_ij                                   │
│                                                             │
│   m     ─────→  Tổng trọng số toàn đồ thị                  │
│                 = ½ Σᵢⱼ A_ij                                │
│                                                             │
│   k_i·k_j       Trọng số cạnh KỲ VỌNG nếu nối ngẫu nhiên   │
│   ─────── ───→  (Mô hình null - không có cấu trúc)         │
│     2m                                                      │
│                                                             │
│   δ(c_i,c_j) ─→  Hàm Kronecker delta:                      │
│                  = 1 nếu i,j CÙNG cụm                       │
│                  = 0 nếu i,j KHÁC cụm                       │
│                                                             │
│   λ     ─────→  Tham số độ phân giải (resolution)          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.4. Đọc công thức bằng lời

> "Tổng trọng số cạnh **thực tế** bên trong mỗi cụm, **trừ đi** trọng số **kỳ vọng** nếu các cạnh được nối ngẫu nhiên, rồi **chia** cho tổng trọng số để chuẩn hóa."

Nếu $Q > 0$: Cạnh trong cụm **dày hơn** ngẫu nhiên → có cấu trúc cộng đồng thật.

---

## 3. Tham số Độ phân giải $\lambda$

### 3.1. Ý nghĩa

$\lambda$ điều khiển **kích thước** cụm mong muốn:

| $\lambda$ | Hiệu ứng | Ví dụ |
|:----------|:---------|:------|
| $\lambda = 1$ | Chuẩn | Cân bằng |
| $\lambda > 1$ | Phạt nặng số hạng kỳ vọng → **chia nhỏ** | Phân rã phường → khu phố |
| $\lambda < 1$ | Giảm phạt → **gộp lớn** | Gom khu phố → quận |

### 3.2. Trực giác toán học

Nhìn vào biểu thức trong ngoặc vuông:
$$
A_{ij} - \lambda \frac{k_i k_j}{2m}
$$

- $\lambda$ **lớn**: Số hạng trừ lớn → cần $A_{ij}$ rất lớn (cạnh rất mạnh) mới dương → chỉ giữ liên kết chặt → cụm nhỏ
- $\lambda$ **nhỏ**: Số hạng trừ nhỏ → cạnh yếu cũng đủ giữ → cụm lớn

### 3.3. Khuyến nghị trong bài báo

```
λ ∈ [0.5, 2.0]  →  ARI ổn định = 0.9957
λ = 3.0        →  ARI sụp còn 0.8438 (chia vụn quá)

Mặc định: λ = 1.0
```

---

## 4. Thuật toán Louvain

### 4.1. Ý tưởng hai pha

```
┌────────────────────────────────────────────────────────────┐
│                    THUẬT TOÁN LOUVAIN                      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   PHA 1: Di chuyển đỉnh (Local Moving)                     │
│   ┌──────────────────────────────────────────────────┐    │
│   │  Với mỗi đỉnh i:                                 │    │
│   │    - Thử chuyển i sang từng cụm láng giềng       │    │
│   │    - Tính ΔQ (thay đổi Modularity)               │    │
│   │    - Nếu ΔQ > 0: chuyển sang cụm cho Q tăng nhất │    │
│   │  Lặp đến khi không đỉnh nào muốn di chuyển       │    │
│   └──────────────────────────────────────────────────┘    │
│                          ↓                                 │
│   PHA 2: Nén đồ thị (Aggregation)                          │
│   ┌──────────────────────────────────────────────────┐    │
│   │  - Mỗi cụm → một SIÊU ĐỈNH                       │    │
│   │  - Trọng số cạnh giữa siêu đỉnh = tổng trọng số  │    │
│   │    các cạnh giữa các đỉnh gốc                    │    │
│   │  - Tạo đồ thị mới, nhỏ hơn                       │    │
│   └──────────────────────────────────────────────────┘    │
│                          ↓                                 │
│   Quay lại PHA 1 trên đồ thị nén                           │
│   Dừng khi Q không tăng nữa                                │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 4.2. Ví dụ minh họa

```
Ban đầu: 8 đỉnh, mỗi đỉnh là một cụm riêng

    A ── B        E ── F
    │    │        │    │
    C ── D        G ── H

Sau Pha 1:
    Cụm 1: {A,B,C,D}    Cụm 2: {E,F,G,H}

Sau Pha 2 (nén):
    [Cụm 1] ─── [Cụm 2]
    (siêu đỉnh)

Pha 1 lần 2: Không ai muốn chuyển → DỪNG
Kết quả: 2 cụm
```

### 4.3. Độ phức tạp

$$
O(N \log N) \quad \text{(thực nghiệm)}
$$

- **N = 341 sự kiện**: Chạy trong vài mili-giây
- **N = 10,000**: Vẫn chạy được real-time
- So với K-Means $O(NKI)$: Tương đương hoặc nhanh hơn

---

## 5. Vấn đề Cộng đồng Đứt gãy & Thuật toán Leiden

### 5.1. Lỗi của Louvain

Louvain đôi khi tạo ra **cộng đồng đứt gãy nội bộ (badly connected communities)**:

```
Cụm do Louvain tìm:

    A ─── B         C ─── D
    
    Cả 4 đỉnh được gán CÙNG MỘT cụm
    NHƯNG không có cạnh nối {A,B} với {C,D}
    
    → Cụm không liên thông!
```

### 5.2. Hậu quả với bài toán cứu hộ

```
Trọng tâm cụm = trung bình tọa độ (A,B,C,D)
             = điểm giữa, KHÔNG có ai ở đó!

Ca nô được điều đến trọng tâm → Đến nhầm chỗ!
```

### 5.3. Thuật toán Leiden

Leiden bổ sung **bước kiểm tra liên thông** sau Pha 1:

```
┌────────────────────────────────────────────────────────────┐
│              LEIDEN = LOUVAIN + REFINEMENT                 │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   Sau Pha 1 (di chuyển đỉnh):                              │
│                                                            │
│   ┌──────────────────────────────────────────────────┐    │
│   │  BƯỚC TINH CHỈNH (Refinement):                   │    │
│   │    - Kiểm tra mỗi cụm có liên thông không        │    │
│   │    - Nếu đứt gãy: tách thành các thành phần      │    │
│   │      liên thông riêng biệt                       │    │
│   └──────────────────────────────────────────────────┘    │
│                                                            │
│   → BẢO ĐẢM: Mọi cụm đều liên thông                        │
│   → Trọng tâm cụm luôn có ý nghĩa địa lý                   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 5.4. So sánh trên dữ liệu bài báo

| Thuật toán | ARI | Modularity | Cụm đứt gãy | Khuyến nghị |
|:-----------|:---:|:----------:|:-----------:|:------------|
| **Louvain** | 0.9957 | 0.861 | 0/130 | Dùng được |
| **Leiden** | 0.9957 | 0.861 | 0/130 | Bảo hiểm tốt hơn |

**Phát hiện quan trọng:** Trên bộ dữ liệu này, cả hai cho kết quả **giống hệt nhau** vì:
> Cơ chế **gating** ở Mục 4.2 đã tạo ra đồ thị với các thành phần gắn kết không gian → Louvain không có cơ hội tạo cụm đứt gãy.

Leiden vẫn được khuyến nghị như **"bảo hiểm miễn phí"** — không tốn thêm chi phí, đảm bảo an toàn.

---

## 6. Liên hệ với các Mục khác

### 6.1. Đầu vào từ Mục 4.2

```
Mục 4.2 cung cấp:
┌─────────────────────────────────────────┐
│  Ma trận trọng số W = [w_ij]            │
│  với w_ij = S_geo · (β·S_temp + γ·S_ctx)│
└─────────────────────────────────────────┘
                    ↓
            Louvain/Leiden
                    ↓
┌─────────────────────────────────────────┐
│  Phân hoạch: {C_1, C_2, ..., C_k}       │
│  Mỗi C_k là một "khu vực tác chiến"     │
└─────────────────────────────────────────┘
```

### 6.2. Đầu ra cho Mục 4.4

```
Mục 4.4 nhận:
- Danh sách các cụm C_1, C_2, ..., C_k
- Thành viên của mỗi cụm
- Tọa độ trọng tâm mỗi cụm

→ Tính P(C_k) để xếp hạng "cứu cụm nào trước"
```

---

## 7. Thực hành với Code

### 7.1. File cần đọc

```
demo/pipeline/clustering.py
```

### 7.2. Đoạn code quan trọng

```python
import community as community_louvain  # python-louvain
import networkx as nx

def run_louvain(G, resolution=1.0):
    """
    G: đồ thị NetworkX với trọng số cạnh 'weight'
    resolution: tham số λ
    
    Returns: dict {node_id: cluster_id}
    """
    partition = community_louvain.best_partition(
        G, 
        weight='weight',
        resolution=resolution
    )
    return partition

def run_leiden(G, resolution=1.0):
    """Dùng thư viện leidenalg + igraph"""
    import igraph as ig
    import leidenalg
    
    # Chuyển từ NetworkX sang igraph
    G_ig = ig.Graph.from_networkx(G)
    
    # Chạy Leiden
    partition = leidenalg.find_partition(
        G_ig,
        leidenalg.RBConfigurationVertexPartition,
        weights='weight',
        resolution_parameter=resolution
    )
    return partition
```

### 7.3. Chạy thử

```bash
cd demo
python -c "
from pipeline.clustering import run_louvain, run_leiden
from pipeline.weighting import build_graph
from data.generate import load_dataset

# Load dữ liệu
events = load_dataset()

# Xây đồ thị (Mục 4.2)
G = build_graph(events)

# Chạy Louvain
partition = run_louvain(G, resolution=1.0)
print(f'Số cụm: {len(set(partition.values()))}')

# Đếm cụm đứt gãy
from pipeline.metrics import count_disconnected_communities
n_bad = count_disconnected_communities(G, partition)
print(f'Cụm đứt gãy: {n_bad}')
"
```

---

## 8. Câu hỏi Tự kiểm tra

### Mức cơ bản
1. Modularity $Q$ đo cái gì?
2. $\lambda = 2$ sẽ cho cụm lớn hơn hay nhỏ hơn $\lambda = 1$?
3. Tại sao Louvain không cần biết trước số cụm $K$?

### Mức nâng cao
4. Nếu tất cả $w_{ij} = 1$ (đồ thị không trọng số), công thức $Q$ trở thành gì?
5. Tại sao Louvain chạy nhanh $O(N \log N)$ trong thực tế?
6. "Cộng đồng đứt gãy" có thể xảy ra khi nào? Tại sao gating giảm thiểu rủi ro này?

### Mức liên hệ
7. Nếu $\sigma_{geo}$ (Mục 4.2) quá lớn, số cụm sẽ tăng hay giảm?
8. Một báo cáo giả cô lập (không có cạnh mạnh với ai) sẽ bị Louvain xử lý thế nào?

---

## 9. Đáp án Gợi ý

<details>
<summary>Nhấn để xem đáp án</summary>

1. **Modularity đo:** Mật độ cạnh trong cụm so với kỳ vọng ngẫu nhiên. $Q$ cao = chia tốt.

2. **$\lambda = 2$:** Cụm **nhỏ hơn** vì phạt nặng hơn → chỉ giữ liên kết rất chặt.

3. **Không cần $K$:** Louvain tối ưu $Q$ — dừng khi $Q$ không tăng nữa. Số cụm là kết quả, không phải đầu vào.

4. **Đồ thị không trọng số:** $A_{ij} \in \{0,1\}$, $k_i$ = bậc (số cạnh), $m$ = số cạnh. Công thức vẫn hoạt động, đo số cạnh trong cụm vs kỳ vọng.

5. **Tại sao nhanh:** 
   - Pha 1 chỉ xét láng giềng, không xét toàn bộ đồ thị
   - Pha 2 nén đồ thị → kích thước giảm nhanh sau mỗi vòng
   - Thường hội tụ sau 2-3 vòng

6. **Cộng đồng đứt gãy:** Xảy ra khi Pha 1 di chuyển đỉnh dựa trên $\Delta Q$ cục bộ mà không kiểm tra liên thông. Gating giảm rủi ro vì: hai điểm xa nhau có $w_{ij} \approx 0$ → không có cạnh → không thể cùng cụm.

7. **$\sigma_{geo}$ lớn:** Số cụm **giảm** vì nhiều cặp có $S_{geo}$ cao hơn → nhiều cạnh mạnh → gom thành cụm lớn.

8. **Báo cáo giả cô lập:** Bị đẩy thành **cụm đơn lẻ** (singleton). Louvain không có lợi khi gộp nó vào cụm khác vì không có cạnh mạnh → $\Delta Q \le 0$.

</details>

---

## 10. Tài liệu Tham khảo Thêm

1. **Bài gốc Louvain:** Blondel et al., "Fast unfolding of communities in large networks" (2008)
2. **Bài gốc Leiden:** Traag et al., "From Louvain to Leiden: guaranteeing well-connected communities" (2019)
3. **Thư viện Python:**
   - `python-louvain`: https://github.com/taynaud/python-louvain
   - `leidenalg`: https://github.com/vtraag/leidenalg
4. **Video giải thích:** Search "Louvain algorithm explained" trên YouTube

---

*Tài liệu này là một phần của bộ hướng dẫn cho nhóm 5 thành viên. Xem thêm các guide khác trong thư mục `resource/guides/`.*
