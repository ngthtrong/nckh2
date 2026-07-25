# Loop 5 — Kế hoạch Giải quyết (Step 2)

**Vai trò:** Tác giả (rời vai phản biện, giữ khách quan). Trả lời trung thực từng chất vấn Step 1, đề xuất sửa cụ thể.

---

## 5.1 — Sai "Spectral chỉ cách 0,003" (Paper.md) — CHẤP NHẬN, SỬA NGAY

**Thừa nhận:** Đây là lỗi số liệu thực, không thể biện minh. Spectral ARI = 0,339, cách nhóm dẫn đầu ~0,55, không phải 0,003. Câu còn tự mâu thuẫn (dùng Spectral làm ví dụ đầu THẤP nhưng lại nói "gần hòa"). Bản main.tex và BaiBao đã đúng; chỉ Paper.md (bản Việt cũ) sai.

**Sửa:** Viết lại dòng 211 Paper.md khớp với main.tex/BaiBao — mô tả đúng cấu trúc "hai loại lỗi ARI làm mờ": (1) đầu thấp Spectral vỡ vụn (completeness 0,595); (2) nhóm dẫn đầu chênh trong 0,002 ARI nhưng completeness vẫn tách (Louvain 1,0 vs HDBSCAN 0,929).

**Trạng thái:** ✅ ĐÃ SỬA trong lúc điều tra (Paper.md dòng 211 đã được cập nhật, bỏ hẳn cụm "0,003", thay bằng mô tả đúng khớp ba artifact).

---

## 5.2 — V-measure ≡ NMI (overclaim tính mới của độ đo) — CHẤP NHẬN, SỬA CÂU CHỮ

**Thừa nhận:** Phản biện đúng. Với `average_method='arithmetic'` (mặc định sklearn, đúng cái `metrics.py` dùng), `normalized_mutual_info_score` **là** `v_measure_score` — cùng một hàm, cùng module. Con số NMI 0,927 in ở `tab:gating`/`tab:baselines` và V-measure 0,927 ở exp9 là **cùng một số**. Tiêu đề "A Discriminative Metric Beyond ARI" + câu "We add … V-measure … report V-measure throughout" ngụ ý V-measure là độ đo MỚI vượt trên bộ đã có — điều này sai vì NMI đã có mặt xuyên suốt.

**Điều gì THỰC SỰ đúng (giữ lại):** Giá trị phân biệt của Thí nghiệm 9 là có thật, nhưng nó đến từ **phân rã** V-measure/NMI thành **homogeneity** và **completeness** riêng lẻ — hai trục mà bảng ARI/NMI không hiển thị. Cụ thể completeness tách nhóm dẫn đầu (Louvain 1,0 vs HDBSCAN 0,929) nơi ARI chỉ hiện 0,002. Đây mới là đóng góp; docstring exp9 (dòng 91–99) vốn đã nói đúng như vậy.

**Sửa (câu chữ, không đụng số):**
1. **main.tex dòng 381 (tiêu đề):** đổi "A Discriminative Metric Beyond ARI" → nhấn vào phân rã, ví dụ *"Decomposing Cluster Quality: Homogeneity and Completeness Beyond ARI"*.
2. **main.tex dòng 382:** thêm một mệnh đề nói rõ V-measure (arithmetic-averaged) **chính là** NMI đã báo cáo ở các bảng, nên đóng góp phân biệt đến từ hai thành phần homogeneity/completeness, không phải từ V-measure như một độ đo tách biệt. Đổi câu kết "We therefore report V-measure alongside ARI throughout" → "we therefore report the homogeneity/completeness decomposition (V-measure equals the arithmetic NMI already tabulated)".
3. **main.tex dòng 392 (Construct limitation):** câu "Because ARI saturates … we also report homogeneity/completeness" đã đúng hướng — giữ, chỉ đảm bảo không gọi V-measure là độ đo mới.
4. **BaiBao dòng 390 & 423:** chỉnh song song — nói V-measure = NMI đã báo cáo, quy công cho completeness/homogeneity.
5. **Paper.md dòng 211:** đã sửa ở 5.1; bổ sung một cụm ngắn nói completeness (không phải V-measure) là cái tách.

**Không đụng:** mọi con số (0,927; 1,0; 0,929; 0,595; 0,339) và mọi bảng — chúng đều đúng. Chỉ sửa cách diễn đạt tính mới.

**Trạng thái:** ⏳ Sẽ thực thi ở Step 3.

---

## KHÔNG SỬA (đã kiểm, đúng)

- 55% phantom, 10,4% exp7, AUC 0,9651, τ 0,99/0,94, completeness gap 0,07, packet 100–111B: tất cả khớp demo. Không đụng.
- exp7 "additive nhanh hơn": đã tự công bố minh bạch trong main.tex dòng 376 — không phải lỗi, giữ nguyên.

---

## THỨ TỰ THỰC THI (Step 3)

1. main.tex: tiêu đề mục 9 (dòng 381) + văn xuôi (dòng 382).
2. BaiBao_NoiDung.md: dòng 388 (tiêu đề mục 5.10) + 390 + 423.
3. Paper.md: dòng 211 (đã xong 5.1; thêm làm rõ completeness).
4. Recompile main.tex → xác nhận 0 undefined refs, số trang ổn định.
5. Cập nhật memory (paper_latex_lncs.md, demo_v2_experiments.md) với phát hiện NMI≡V-measure.
