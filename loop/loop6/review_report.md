# Loop 6 — Báo cáo Phản biện (Step 1)

**Vai trò:** Giáo sư chủ tịch hội đồng phản biện, khắt khe về Toán/Kỹ thuật/dữ liệu.
**Phạm vi:** Sau loops 4–5 (miền giá trị, trích dẫn, xref, code faithfulness, NMI≡V-measure), loop 6 soi **địa lý dữ liệu**, các con số chưa kiểm ở loop trước, và độ chính xác câu chữ mô tả bộ dữ liệu.

---

## 6.1 — LỖI DỮ LIỆU (nghiêm trọng vừa): tuyên bố "0 m offset / cùng tọa độ" SAI cho 18/24 điểm kịch bản

**Chất vấn:** Bài báo (main.tex dòng 226 và 236; BaiBao dòng 290, 309; Paper.md dòng 193) khẳng định **cả 24 điểm kịch bản** (nhãn 100–105) *"sit at the same coordinates as the six islands"* với *"0 m offset"* / *"trùng tọa độ … lệch 0 m"*. Đây là bằng chứng cốt lõi cho lập luận "trần ARI 0,892 là do cấu trúc ground-truth". Nhưng kiểm tra trực tiếp `demo/data/generate.py` (hàm `narrative_scenarios`) cho thấy tuyên bố này **không đúng với đa số điểm**:

| Nhãn | Số điểm | Offset so với tâm ốc đảo chủ (haversine) |
|------|---------|------------------------------------------|
| 100 (S1_A) | 1 | 0 m |
| 101 (S1_B) | 1 | 0 m |
| 102 (S2)   | 5 | 0 → **492,6 m** |
| 103 (S3 thật) | 4 | 0 → **323,8 m** |
| 104 (S4A)  | 10 | 0 → **832,2 m** |
| 105 (S4B)  | 3 | 0 → **184,6 m** |

Chỉ **6 điểm mỏ neo** (k=0 của mỗi nhóm) nằm đúng tâm (0 m); **18 điểm còn lại** trải tới **832 m**. Mã sinh dùng offset tăng dần `k * 0.0006`…`k * 0.0008` độ (xem generate.py dòng 135, 143, 153, 157). Vậy "0 m offset cho cả 24 điểm" là **sai số liệu**.

**Vì sao vẫn quan trọng:** Con số `n_colocated_narrative_groups = 6` trong `exp1_G` là ĐÚNG — nhưng nó chỉ đếm **mỗi nhóm có mỏ neo trùng tâm** (điều kiện `g not in seen` → chỉ xét điểm ĐẦU của mỗi nhóm, ngưỡng `<1.0 m`). Bài báo đã phóng đại điều này thành "cả 24 điểm lệch 0 m". Một phản biện tinh ý mở file dữ liệu sẽ bắt được ngay mâu thuẫn, làm suy giảm niềm tin vào toàn bộ phần thực nghiệm.

**Điều gì THỰC SỰ đúng:** Các nhóm kịch bản được **neo tại tâm 6 ốc đảo và trải trong bán kính ~0–832 m — cùng cỡ với độ jitter ~250 m của chính các điểm lõi** (generate.py `spread_m=250`). Vì nằm gọn trong "vùng phủ không gian" của ốc đảo chủ, mọi phương pháp phân cụm theo không gian buộc phải gộp chúng vào ốc đảo đó → trần ARI 0,892. Cơ chế đúng; chỉ **cách mô tả "0 m" là sai**.

---

## 6.2 — Kiểm chứng số liệu chưa soi ở loop 4–5 (KẾT QUẢ: tất cả KHỚP, không lỗi)

Đã đối chiếu trực tiếp mọi con số headline với JSON trong `demo/results/tables/`:

- **exp1_A** (gating vs additive): ARI 0,892 / NMI 0,927 / diam 100,07→0,30 km / 6 vs 27 cụm — khớp `tab:gating`. ✅
- **exp1_B** (chuẩn hóa): top thô cụm 216 người / core 71,65; sau chuẩn hóa top core 0,82 / P 1,52 — khớp dòng 253. ✅
- **exp1_C** (S2): V_agg 1,97 / P_mult 1,36 / P_add 1,66 — khớp dòng 256. ✅
- **exp1_D** (tanh): 1,76/2,00/2,00 vs 1,10/1,29/1,76/2,00/2,00 — khớp `tab:tanh`. ✅
- **exp1_E/F** (C_i gate): 200→90 (−55%), F 0,99→0,45 — khớp. ✅
- **exp2** (λ, σ_geo, τ, β/γ, s): mọi dòng khớp (λ=2,0→0,8303 làm tròn 0,83; σ=200m→0,28km; σ=4000m→1,59km; τ bất biến; β≥0,9→0,7855; s spread). ✅
- **exp3**: 10 seeds, 0 broken, ARI 0,892, Q 0,8311. ✅
- **exp4** (baselines): mọi hàng `tab:baselines` khớp JSON (Spectral 0,339; HDBSCAN 0,890/25,08km/11 cụm; K-Means 0,688; DBSCAN 0,730). ✅
- **exp5**: τ 0,9857→"0,99", min 0,9373→"0,94", top-3 99% — khớp. ✅
- **exp7**: 146,5/163,57 → 10,43% "10,4%", harm 8,7% — khớp. ✅
- **exp8**: AUC 0,9651; adversarial 0,45/0,77/0,74/0,92 — khớp. ✅
- **exp9**: hoàn thành ở loop 5. ✅
- **exp10** (packet): 100–111 B — khớp "100–111 bytes". ✅

**Trích dẫn ngoài:** CrisisSpot F1 5,01–9,45% — xác minh đúng (arXiv abstract: 9,45% CrisisMMD, 5,01% TSEqD). Storm 6–8/năm, ~11 Biển Đông — xác minh khớp (Wikipedia: 6–8 landfall, 11–13 vào Biển Đông). ✅

**Kết:** Ngoài lỗi câu chữ 6.1, **toàn bộ số liệu định lượng của bài trung thực và tái lập được**.

---

## 6.3 — Kiểm tra toàn vẹn tham chiếu & hình (KẾT QUẢ: sạch)

- 7/7 hình `fig1`–`fig7` tồn tại trong `paper/figures/`. ✅
- Mọi `\ref` có `\label` tương ứng; không có ref treo. ✅
- 22 khóa `\cite` đều có mục trong `references.bib`; không có khóa mồ côi/thiếu. ✅
- Không còn placeholder `[grant number]`, TODO, XXX. ✅
- Recompile: 20 trang, 0 undefined refs (kiểm cuối loop 5). ✅

---

## Tổng kết loop 6

**1 lỗi cần sửa:** 6.1 — tuyên bố "0 m offset / cùng tọa độ" cho cả 24 điểm kịch bản là sai; đúng ra chỉ 6 mỏ neo trùng tâm, 18 điểm trải tới 832 m. Cần sửa câu chữ ở **main.tex (226, 236), BaiBao (290, 309), Paper.md (193)** cho chính xác, giữ nguyên cơ chế "trần ARI do cấu trúc".

**Không có lỗi số liệu mới.** Bài đã rất chắc sau loops 4–5.
