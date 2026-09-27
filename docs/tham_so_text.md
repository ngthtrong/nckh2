| Tham số | Được xác định/tính từ |
|---|---|
| \(L_i\) | Tọa độ GPS của báo cáo \(i\): vĩ độ và kinh độ |
| \(T_i\) | Thời điểm tạo báo cáo `created_at` |
| \(F_i\) | Bằng chứng ngập quan sát được, chuẩn hóa về \([0,1]\); bài báo không quy định model trích xuất cụ thể |
| \(E_i\) | Bằng chứng khẩn cấp quan sát được, chuẩn hóa về \([0,1]\); bài báo không quy định model tính cụ thể |
| \(N_i\) | Số người mắc kẹt do người gửi khai báo |
| \(V_i\) | Bằng chứng về nhóm dễ tổn thương do người gửi khai báo |
| \(Q_i\) | Sự hiện diện của ảnh và số payload corroboration duy nhất: \(Q_i=\operatorname{sigmoid}(-0.2+1.4\,\mathbf1\{\text{có ảnh}\}+0.9\log(1+n_i^{corrob}))\) |



MOBILE / EDGE
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  1. IMAGE                                                │
│     ↓                                                    │
│  MobileNetV3                                             │
│     ↓                                                    │
│  Flood evidence F_i ∈ [0,1]                              │
│                                                          │
│                                                          │
│  2. STRUCTURED FORM                                      │
│                                                          │
│  Số người mắc kẹt ───────────────────────────────→ N_i   │
│                                                          │
│  Người già / trẻ em / mang thai / khuyết tật ───→ V_i   │
│                                                          │
│  Tình trạng hiện tại                                     │
│  + số người bị thương                                    │
│  + cần hỗ trợ y tế ngay                                  │
│  + không thể tự di chuyển                                │
│  + không thể tự sơ tán / bị cô lập                       │
│               ↓                                          │
│       Lightweight Tabular AI                             │
│       Logistic Regression                                │
│               ↓                                          │
│       Urgency evidence E_i ∈ [0,1]                       │
│                                                          │
│                                                          │
│  3. GHI CHÚ                                              │
│     ↓                                                    │
│  Optional raw context                                    │
│  Không bắt buộc nhập                                     │
│  Không chạy NLP model trên critical path                 │
│                                                          │
│                                                          │
│  4. METADATA                                             │
│                                                          │
│  GPS ─────────────────────────────────────────────→ L_i   │
│  Timestamp ───────────────────────────────────────→ T_i   │
│                                                          │
└──────────────────────────────────────────────────────────┘
                           │
                           │
                           ▼
               COMPACT RESCUE PAYLOAD
                           │
                           │
         (L_i, T_i, F_i, E_i, N_i, V_i)
                           │
                           ▼
────────────────────────────────────────────────────────────
                           │
                         SERVER
                           │
                           ▼
                     Compute Q_i
                           │
                           ▼
            Complete rescue representation
                           │
        (L_i,T_i,F_i,E_i,N_i,V_i,Q_i)
                           │
                           ▼
                   Similarity Graph
                           │
                           ▼
                      Clustering
                           │
                           ▼
              Duplicate-family Handling
                           │
                           ▼
                Duplicate-aware Ranking
                           │
                           ▼
                       Scheduler
                           │
                           ▼
                  Dashboard / Map
────────────────────────────
────────────────────────────────


IMAGE
→ image_inference
→ F_i

FORM urgency
→ urgency_inference
→ E_i

FORM trapped
→ trapped_count
→ N_i

FORM vulnerability
→ vulnerability_encoder
→ V_i

GPS
→ location
→ L_i

Timestamp
→ event_time
→ T_i

SERVER
→ confidence_service
→ Q_i

SERVER
→ similarity_graph
→ clustering
→ duplicate_handler
→ priority_ranking
→ scheduler








