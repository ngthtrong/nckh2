# Demo v2 — Thực nghiệm Khung Giải pháp Đồ thị Trọng số (Mục 4, PaperV2)

Bộ mã này hiện thực hóa và kiểm chứng các công thức đã sửa ở Mục 4 của
`resource/PaperV2.md`, sinh kết quả thực nghiệm (bảng + hình) cho bài báo và
một dashboard trực quan trên bản đồ Miền Trung Việt Nam.

## Cấu trúc

```
demo/v2/
├── pipeline/              # Lõi thuật toán (ánh xạ 1-1 với Mục 4)
│   ├── config.py          #   tham số: sigma_geo, tau, omega, lambda, s...
│   ├── attributes.py      #   4.1 — vector (L,T,F,E,N,V,C) + heuristic C_i
│   ├── weighting.py       #   4.2 — w_ij dạng nhân/gating + làm thưa đồ thị
│   ├── clustering.py      #   4.3 — Louvain + Leiden + đo cụm đứt gãy
│   ├── priority.py        #   4.4 — P(C_k) chuẩn hóa, V_agg là thừa số nhân
│   ├── baselines.py       #   K-Means, DBSCAN để đối chiếu
│   └── metrics.py         #   ARI, NMI, đường kính địa lý cụm
├── data/
│   ├── generate.py        # Sinh dữ liệu synthetic (GPS Miền Trung + ground-truth)
│   └── dataset.json       # 285 sự kiện (240 lõi + 20 nhiễu + 25 kịch bản)
├── experiments/
│   ├── exp1_formula_validation.py   # kiểm chứng 4 fix
│   ├── exp2_sensitivity.py          # quét sigma_geo, lambda, s
│   ├── exp3_louvain_vs_leiden.py    # cụm đứt gãy, 10 seed
│   ├── exp4_baselines.py            # vs K-Means/DBSCAN
│   └── make_figures.py              # sinh 6 hình PNG
├── dashboard/
│   ├── build_dashboard.py # chạy pipeline -> HTML tự chứa
│   └── dashboard.html      # bản đồ Leaflet + bảng xếp hạng P(C_k)
├── results/
│   ├── tables/*.json       # số liệu thô của mọi thí nghiệm
│   └── figures/*.png       # hình cho bài báo
└── run_all.py             # chạy toàn bộ từ đầu tới cuối
```

## Chạy

```bash
cd demo/v2
./.venv/bin/python run_all.py          # chạy tất cả
# hoặc từng bước:
./.venv/bin/python data/generate.py
./.venv/bin/python experiments/exp1_formula_validation.py
./.venv/bin/python experiments/make_figures.py
./.venv/bin/python dashboard/build_dashboard.py
```

Mở `dashboard/dashboard.html` bằng trình duyệt để xem bản đồ tương tác.

## Bộ dữ liệu

Vùng: Miền Trung VN (Huế · Quảng Trị · Quảng Nam · Đà Nẵng), 15.7–17.1°N, 107.0–108.6°E.

- **Lõi định lượng (240):** 6 "ốc đảo" ngập, mỗi cụm có nhãn `gt_cluster` để đo ARI/NMI.
- **Nhiễu (20):** báo cáo rải rác, ~40% là tin giả.
- **Kịch bản minh họa (25):** mỗi kịch bản stress-test một fix —
  - S1: hai điểm ngập nóc cách 90 km (kiểm tra gating tách cụm).
  - S2: cụm nhiều đối tượng yếu thế (kiểm tra V_agg khuếch đại).
  - S3: tin giả cô lập thổi phồng 200 người (kiểm tra gate C_i).
  - S4: cụm đông-ngập nhẹ vs ít-ngập nóc (kiểm tra F_max & cân bằng).

## Kết quả chính (seed=42)

| Thí nghiệm | Phát hiện |
| :--- | :--- |
| **1A** gating vs cộng | Cùng ARI 0.89, nhưng đường kính cụm giảm từ **100 km → 0.31 km** |
| **1B** chuẩn hóa | Không chuẩn hóa: cụm dân số lớn nhất áp đảo bảng xếp hạng |
| **1C** V nhân vs cộng | Nhân giữ đúng vai trò "khuếch đại"; cộng chỉ là offset |
| **1D** chống bão hòa | `tanh(ΣV)` bão hòa ở ΣV=3; `tanh(ΣV/10)` phân biệt tới ΣV=50 |
| **1E** gate C_i | Tin giả C_i=0.45, tổng người của cụm giảm **55%** |
| **2** độ nhạy | ARI ổn định với λ≤1.5; σ_geo điều khiển đánh đổi bán kính/số cụm |
| **3** Louvain vs Leiden | 0 cụm đứt gãy ở cả hai — gating đã loại rủi ro; Leiden là bảo hiểm miễn phí |
| **4** baseline | Louvain/Leiden ARI **0.89** vs K-Means 0.69, DBSCAN 0.73; gắn kết địa lý vượt trội |

Tất cả tham số nằm trong `pipeline/config.py`. Dữ liệu sinh tất định (seed cố định).
