# Hình 3-11 → 3-14 (lược đồ v8)

Mỗi hình có hai bản:

- `.svg`: bản vector, dùng để chèn vào Word (Insert → Pictures). Phóng to không vỡ chữ.
- `.png`: bản 300 dpi, dùng khi cần ảnh bitmap.

| Hình | Nội dung | Hộp | Quan hệ |
|---|---|---|---|
| 3-11 | LDM-1 Tenant and Authorization | 11 | 29 |
| 3-12 | LDM-2 Vocabulary + LDM-3 Collection | 12 + 3 tham chiếu | 34 |
| 3-13 | LDM-4 Governance and Lifecycle | 11 + 3 tham chiếu | 17 |
| 3-14 | PDM tổng quan v8 | 63 bảng | 45 đường (47 FK) + [T] 39 + [U] 46 = **132 FK** |

Bộ kiểm hình học chạy trên cả bốn hình và báo 0 lỗi cho cả ba loại:

- đường chồng lên đường;
- đoạn xiên;
- nhãn va chạm.

## Đã lược khỏi hình (phải ghi trong chú thích hoặc Phụ lục A)

- **3-11:** chỉ vẽ quan hệ nội bộ của 11 thực thể. Quan hệ giữa Tenant/User và các module khác nằm ở 3-12 và 3-13.
- **3-12:**
  - Lược 5 thực thể phụ: Dialect Merge, Dialect Template, Recognition Profile Template, Template Version, Signer Merge.
  - Lược 4 quan hệ dấu vết thao tác: User creates Dialect, User approves Dialect, User creates Registry Version, User reviews Sample.
  - Quan hệ với Training Job / Training Job Class chuyển sang LDM-5 ở Phụ lục A.
- **3-13:** không lược gì. Legal Document Event, SOT Writer Key và Tenant Purge đứng riêng ở hàng cuối vì lược đồ không có khoá ngoại nào nối chúng.
- **3-14:**
  - FK tới `tenants` và `users` không vẽ thành đường mà thay bằng nhãn [T]/[U]. Chú giải nằm ngay dưới hình.
  - Nhiều FK giữa cùng một cặp bảng được gộp thành một đường, ghi ×n.

## Chú thích tiếng Anh để dán dưới hình

> **Figure 3-11.** Logical data model, module 1: tenant and authorization. Relationships between Tenant or User and entities of other modules are shown in Figures 3-12 and 3-13; platform-service entities are given in Appendix A.
>
> **Figure 3-12.** Logical data model, module 2: vocabulary, registry and collection. Five auxiliary entities (dialect merges, templates and signer merges) and four audit-trail relationships (User creates/approves Dialect, creates Registry Version, reviews Sample) are omitted for readability; the complete model is given in Appendix A.
>
> **Figure 3-13.** Logical data model, module 3: legal governance, consent, audit and data lifecycle.
>
> **Figure 3-14.** Overview of the physical data model (schema version 8): 63 tables in eight groups. Foreign keys to `tenants` and `users` are indicated by the [T] and [U] tags instead of lines.

## Dựng lại

Các tệp sinh hình nằm ở thư mục cha.

```
python ve_hinh.py          # 3-11, 3-12, 3-13 — đọc dac_ta_CDM_LDM_PDM.md, dùng lưới đã lưu luoi_*.json
python ve_pdm.py           # 3-14 — đọc evidence/pdm_v8_*.csv của repo
python ve_hinh.py --toi-uu # tìm lại bố cục (ghi đè luoi_*.json)
```
