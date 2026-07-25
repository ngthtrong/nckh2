# Loop 8 — Báo cáo Phản biện (Step 1)

**Vai trò:** Giáo sư chủ tịch hội đồng phản biện, khắt khe về Toán/Thống kê/độ đo. Loops 4–7 đã dọn sạch miền giá trị, trích dẫn, xref, faithfulness số liệu, và nhất quán ba-artifact. Loop 8 soi **tính đúng đắn của lời giải thích cơ chế (causal claims)** — không phải con số, mà là *câu chuyện nhân-quả* gắn với con số. Đây là loại lỗi nguy hiểm nhất còn sót: số đúng nhưng diễn giải sai.

---

## CHẤT VẤN 8.1 — Diễn giải NGƯỢC về HDBSCAN: "gộp ốc đảo" là sai cơ chế (NGHIÊM TRỌNG)

**Nơi xuất hiện:**
- `main.tex` dòng 345 (Exp4): *"HDBSCAN reaches ARI 0.890 but finds fewer clusters (11 vs. 27) at 25 km mean diameter, **merging distinct islands**"*
- `main.tex` dòng 382 (Exp9): *"HDBSCAN drops to 0.929 **because it merges islands**"*
- `BaiBao_NoiDung.md` dòng 360: *"...đường kính trung bình 25 km — **gộp nhiều ốc đảo khác nhau vào cùng cụm**"*
- `BaiBao_NoiDung.md` dòng 390: *"HDBSCAN tụt xuống 0,929 **vì gộp các ốc đảo**"*
- `Paper.md` dòng 211: *"HDBSCAN tụt còn 0,929 **vì gộp các ốc đảo**"*

**Mâu thuẫn toán học nội tại:** Exp9 dùng bộ ba homogeneity/completeness/V-measure của sklearn. Theo định nghĩa:
- **Homogeneity** thấp ⟺ một cụm dự đoán chứa nhiều lớp ground-truth (tức **GỘP** lớp).
- **Completeness** thấp ⟺ một lớp ground-truth bị **XÉ LẺ** ra nhiều cụm dự đoán.

Bài báo nói completeness của HDBSCAN tụt (1,0 → 0,929) **vì nó gộp ốc đảo**. Nhưng gộp ốc đảo làm giảm *homogeneity*, không phải *completeness*. Nếu HDBSCAN thật sự gộp ốc đảo thì homogeneity của nó phải THẤP — trong khi số liệu cho thấy điều ngược lại.

**Kiểm chứng trực tiếp bằng code** (`demo/experiments/exp9_...`, chạy lại phân bố nhãn):

| | Homogeneity | Completeness |
|---|---|---|
| Louvain (gating) | 0,8639 | **1,0** |
| HDBSCAN (gating) | **0,9154** | 0,9285 |

HDBSCAN có homogeneity *cao hơn* Louvain (0,9154 > 0,8639) → cụm của nó **thuần hơn**, không phải bị gộp.

**Phân bố nhãn thực tế (HDBSCAN):**
```
GT 4 (n=40): 32 → bin nhiễu(-1), 4 → cụm 7, 4 → cụm 8   ← lớp bị XÉ LẺ
GT 1 (n=40): 36 → cụm 5, 4 → bin nhiễu(-1)               ← mất 4 điểm vào nhiễu
```
- **36 điểm có nhãn** bị HDBSCAN ném vào bin nhiễu `-1`.
- KHÔNG có cụm dự đoán nào chứa **hai ốc đảo lõi khác nhau** (cụm 0={0,100}, cụm 2={2,101}... chỉ trộn lõi với điểm kịch bản đồng-vị-trí, điều mọi phương pháp đều gặp). Chỗ duy nhất trộn hai lớp lõi (1 và 4) là **bin nhiễu**, tức phần dư gom lại — không phải một "mega-cụm gộp ốc đảo".

**Kết luận:** completeness tụt là do **PHÂN MẢNH** (xé lẻ lớp 1 và lớp 4, dồn 36 điểm vào nhiễu), đúng như định nghĩa completeness. "Gộp ốc đảo" là câu chuyện ngược. Một phản biện đọc kỹ sẽ bắt được mâu thuẫn logic này ngay.

---

## CHẤT VẤN 8.2 — "25 km mean diameter" đúng con số nhưng gán sai nguyên nhân (TRUNG BÌNH, hệ quả của 8.1)

Đường kính trung bình 25,08 km của HDBSCAN (khớp `exp4_baselines.json`) bị bài báo ngầm quy cho "gộp ốc đảo thành cụm lớn". Kiểm chứng đường kính từng cụm:
```
cụm -1 (nhiễu): n=36  diam=71,18 km   ← bin nhiễu bị tính như một "cụm"
cụm  1:         n=21  diam=196,18 km  ← cụm dư rải rác
các cụm khác:   diam 0,3–1,4 km       ← thực ra rất gắn kết
```
25 km trung bình bị **thổi lên bởi bin nhiễu (71 km) và một cụm dư rải rác (196 km)**, không phải bởi các cụm lớn gắn kết gộp nhiều ốc đảo. Con số 25 km giữ nguyên (đúng như code tính), nhưng lời giải thích cơ chế phải sửa cho khớp 8.1.

---

## ĐÃ KIỂM — KHÔNG PHẢI LỖI (giữ nguyên)

- `main.tex` dòng 236: *"any spatially-driven method necessarily merges each [narrative point] into its host island"* — ĐÚNG. Điểm kịch bản (nhãn 100–105) đồng vị trí với ốc đảo lõi nên bị gộp vào đó; đây là cơ chế trần-ARI hợp lệ, không đụng.
- Abstract (main.tex 43, BaiBao 9, Paper.md 230) và Conclusion (398, BaiBao 428): chỉ nêu con số "HDBSCAN 0,890 nhưng đường kính 25 km", KHÔNG có mệnh đề nhân-quả "gộp ốc đảo" → không cần sửa.
- Mọi headline number đã kiểm loops 4–6, khớp demo.

---

## TỔNG KẾT STEP 1

**1 lỗi diễn giải nghiêm trọng (8.1)** kéo theo **1 chỉnh hệ quả (8.2)**: lời giải thích "HDBSCAN gộp ốc đảo" đi ngược định nghĩa completeness và mâu thuẫn với chính số homogeneity đo được. Phải sửa mệnh đề nhân-quả ở `main.tex` (345, 382), `BaiBao` (360, 390), `Paper.md` (211) thành **"phân mảnh / xé lẻ ốc đảo + dồn điểm vào bin nhiễu"**, giữ nguyên mọi con số.
