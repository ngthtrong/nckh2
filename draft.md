# Đánh giá Bài báo & Phân chia Công việc cho Nhóm 5 Thành viên

## Tổng quan Bài báo

Bài báo đề xuất một **khung giải pháp end-to-end** cho cứu hộ bão lũ với3 vấn đề chính:

```
┌────────────────────────────────┐
│                         LUỒNG XỬ LÝ CHÍNH                                   │
├────────────────────────────────┤
│                                             │
│   📱 Thiết bị biên          🕸️ Đồ thị trọng số        📊 Xếp hạng          │
│   ┌──────────────┐         ┌──────────────┐         ┌────────┐       │
│   │ Trích xuất   │   →     │ Xây dựng     │   →     │ Phân cụm     │       │
│   │ vector7D    │         │ cạnh gating  │         │ Louvain      │       │
│   │(L,T,F,E,N,V,C)│        │ w_ij         │              │       │
│   └────────────┘         └──┬────┘       │
│        §4.1                §4.2                       │               │
│                                            ↓               │
│                                   ┌──────────────┐         │
│                                                   │ Tính P(C_k)  │ → Danh  │
│                                                   │ ưu tiên cụm  │   sách  │
│                                                   └──────────────┘   cứu   │
│                                                        §4.4          hộ    │
└────────────────────────────────┘
```

## Đánh giá Nội dung

| Khía cạnh               | Nhận xét                                                                                      |
| ------------------------- | ----------------------------------------------------------------------------------------------- |
| **Độ phức tạp** | Trung bình-cao. 4 công thức toán học lõi, mỗi công thức có nhiều thành phần        |
| **Điểm mạnh**    | Có code demo đầy đủ, số liệu thực nghiệm chi tiết, giải thích công thức rõ ràng |
| **Thách thức**    | Cần hiểu đồng thời: lý thuyết đồ thị, thuật toán clustering, toán tối ưu         |

## Phân chia Công việc cho 5 Thành viên

### 👤 Thành viên 1: Edge AI & Vector Thuộc tính (Mục 4.1)

**Phạm vi tìm hiểu:**

* Vector 7 chiều $(L, T, F, E, N, V, C)$ —ý nghĩa từng thuộc tính
* Công thức độ tin cậy $C_i = \sigma(b_0 + b_1 \cdot \mathbb{1}[\text{có ảnh}] + b_2 \cdot \log(1 + n_i^{\text{corrob}}))$
* Khái niệm Edge AI: tại sao cần xử lý tại thiết bị thay vì đám mây

**File cần đọc:**

* [BaiBao_NoiDung.md](vscode-webview://1hfgd9snsqh6rhgshmoqu84dgu1sb6s00t01tpaigdek3310qd8i/resource/BaiBao_NoiDung.md) — Mục 4.1
* [GiaiThichCongThuc.md](vscode-webview://1hfgd9snsqh6rhgshmoqu84dgu1sb6s00t01tpaigdek3310qd8i/resource/GiaiThichCongThuc.md) — Mục 1
* [demo/pipeline/attributes.py](vscode-webview://1hfgd9snsqh6rhgshmoqu84dgu1sb6s00t01tpaigdek3310qd8i/demo/pipeline/attributes.py)

**Câu hỏi cần trả lời được:**

1. Tại sao chọn 7 thuộc tính này? Thuộc tính nào trích từảnh, thuộc tính nào từ văn bản?
2. Công thức $C_i$ chống spam như thế nào? (gợi ý: nén logarit)
3. Gói metadata dưới 1KB gồm những gì?

---

### 👤 Thành viên 2: Đồ thị Trọng số & Công thức Gating (Mục 4.2)

**Phạm vi tìm hiểu:**

* Công thức trọng số cạnh: $w_{ij} = S_{geo} \cdot (\beta S_{temp} + \gamma S_{context})$
* Ba thành phần: $S_{geo}$ (Gaussian), $S_{temp}$ (suy giảm mũ), $S_{context}$
* Tại sao dạng **nhân** (gating) tốt hơn dạng **cộng**

**File cần đọc:**

* [BaiBao_NoiDung.md](vscode-webview://1hfgd9snsqh6rhgshmoqu84dgu1sb6s00t01tpaigdek3310qd8i/resource/BaiBao_NoiDung.md) — Mục 4.2
* [GiaiThichCongThuc.md](vscode-webview://1hfgd9snsqh6rhgshmoqu84dgu1sb6s00t01tpaigdek3310qd8i/resource/GiaiThichCongThuc.md) — Mục 2
* [demo/pipeline/weighting.py](vscode-webview://1hfgd9snsqh6rhgshmoqu84dgu1sb6s00t01tpaigdek3310qd8i/demo/pipeline/weighting.py)

**Câu hỏi cần trả lời được:**

1. Hai điểm cách 50km nhưng ngữ cảnh giống nhau → trọng số $w_{ij}$ là bao nhiêu với dạng cộng vs dạng nhân?
2. Tham số $\sigma_{geo}$ có ý nghĩa gì? Đặt bằng bao nhiêu và tại sao?
3. "Làm thưa đồ thị" (sparsification) là gì, tại sao cần?

---

### 👤 Thành viên 3: Thuật toán Phân cụm Louvain/Leiden (Mục 4.3)

**Phạm vi tìm hiểu:**

* Khái niệm Modularity $Q$ — hàm mục tiêu của Louvain
* Tham số độ phân giải $\lambda$: $\lambda > 1$ chia nhỏ, $\lambda < 1$ gộp lớn
* Khác biệt Louvain vs Leiden (cộng đồng đứt gãy)

**File cần đọc:**

* [BaiBao_NoiDung.md](vscode-webview://1hfgd9snsqh6rhgshmoqu84dgu1sb6s00t01tpaigdek3310qd8i/resource/BaiBao_NoiDung.md) — Mục 4.3
* [GiaiThichCongThuc.md](vscode-webview://1hfgd9snsqh6rhgshmoqu84dgu1sb6s00t01tpaigdek3310qd8i/resource/GiaiThichCongThuc.md) — Mục 3
* [demo/pipeline/clustering.py](vscode-webview://1hfgd9snsqh6rhgshmoqu84dgu1sb6s00t01tpaigdek3310qd8i/demo/pipeline/clustering.py)

**Câu hỏi cần trả lời được:**

1. Tại sao chọn Louvain thay vì K-Means? (gợi ý: không cần biết trước số cụm $K$)
2. "Cộng đồng đứt gãy nội bộ" là gì? Tại sao Leiden tránh được?
3. Độ phức tạp $O(N \log N)$ có ý nghĩa gì cho bài toán thời gian thực?

---

### 👤 Thành viên 4: Hàm Ưu tiên Cấp cụm (Mục 4.4)

**Phạm vi tìm hiểu:**

* Công thức: $\mathcal{P}(C_k) = \mathcal{V}_{agg} \cdot (\omega_1 \tilde{E} + \omega_2 \tilde{F} + \omega_3 \tilde{N})$
* Ba lỗi của bản gốc: (a) sai thang đo, (b) $V$ cộng thay vì nhân, (c) $\tanh$ bão hòa sớm
* Chuẩn hóa $[0,1]$ và nén logarit cho $\mathcal{N}$

**File cần đọc:**

* [BaiBao_NoiDung.md](vscode-webview://1hfgd9snsqh6rhgshmoqu84dgu1sb6s00t01tpaigdek3310qd8i/resource/BaiBao_NoiDung.md) — Mục 4.4
* [GiaiThichCongThuc.md](vscode-webview://1hfgd9snsqh6rhgshmoqu84dgu1sb6s00t01tpaigdek3310qd8i/resource/GiaiThichCongThuc.md) — Mục 4
* [demo/pipeline/priority.py](vscode-webview://1hfgd9snsqh6rhgshmoqu84dgu1sb6s00t01tpaigdek3310qd8i/demo/pipeline/priority.py)

**Câu hỏi cần trả lời được:**

1. Tại sao $\mathcal{V}_{agg}$ phải là **thừa số nhân** chứ không phải số hạng cộng?
2. Cụm 200 người vs cụm 10 người —ếu không chuẩn hóa thì chuyện gì xảy ra?
3. $\tanh(\sum V_i)$ bão hòa ở $\sum V_i = 3$ nghĩa là gì? Cách sửa bằng $s=10$?

---

### 👤 Thành viên 5: Thực nghiệm & Đánh giá (Mục 5 + demo/)

**Phạm vi tìm hiểu:**

* Bộ dữ liệu: 341 sự kiện, 14 nhãn ground-truth, 5 kịch bản stress-test (S1–S5)
* Các độo: ARI, NMI, đường kính cụm, Kendall's τ
* Kết quả chính: gating giảm đường kính từ 214km xuống 1,4km

**File cần đọc:**

* [BaiBao_NoiDung.md](vscode-webview://1hfgd9snsqh6rhgshmoqu84dgu1sb6s00t01tpaigdek3310qd8i/resource/BaiBao_NoiDung.md) — Mục 5
* [demo/README.md](vscode-webview://1hfgd9snsqh6rhgshmoqu84dgu1sb6s00t01tpaigdek3310qd8i/demo/README.md)
* [demo/experiments/](vscode-webview://1hfgd9snsqh6rhgshmoqu84dgu1sb6s00t01tpaigdek3310qd8i/demo/experiments/) — các file exp1 đến exp12
* [demo/results/tables/](vscode-webview://1hfgd9snsqh6rhgshmoqu84dgu1sb6s00t01tpaigdek3310qd8i/demo/results/tables/) — số liệu JSON

**Câu hỏi cần trả lời được:**

1. Kịch bản S1 (hai điểm cách 106km) chứng minh điều gì?
2. ARI = 0,957 có nghĩa gì? Tại sao HDBSCAN đạt ARI = 1,0 nhưng vẫn không dùng được?
3. Kendall's τ = 0,955 khi nhiễu loạn $\omega$ ±0,10 — xếp hạng có ổn định không?

---

## Lịch trình Gợi ý

| Tuần             | Hoạt động                                                                |
| ----------------- | --------------------------------------------------------------------------- |
| **Tuần 1** | Mỗi người đọc hiểu phần được giao, chạy thử code liên quan     |
| **Tuần 2** | Họp nhóm: mỗi người trình bày 15 phút, giải đáp thắc mắc chéo |
| **Tuần 3** | Viết tóm tắt 1 trang cho phần mình, ghép thành tài liệu chung      |

## Mẹo Đọc hiểu

1. **Đọc [GiaiThichCongThuc.md](vscode-webview://1hfgd9snsqh6rhgshmoqu84dgu1sb6s00t01tpaigdek3310qd8i/resource/GiaiThichCongThuc.md) trước** — giải thích từng ký hiệu rõ ràng hơn bài báo chính
2. **Chạy demo** để thấy số liệu thực: `cd demo && python run_all.py`
3. **Xem bảng tổng kết V1→V2** ở cuối Mục 4.4 — liệt kê 9 thay đổi quan trọng

Nếu nhóm cần, tôi có thể tạo thêm tài liệu giải thích riêng cho từng phần, hoặc vẽ sơ đồ chi tiết hơn cho bất kỳ công thức nà
