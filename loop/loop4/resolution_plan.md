# VÒNG 4 — KẾ HOẠCH GIẢI QUYẾT (RESOLUTION PLAN)

**Ngày:** 2026-07-24
**Vai trò:** Tác giả (khách quan). Trả lời từng chất vấn Bước 1 và nêu phương án sửa cụ thể.

---

## A. LỖI MIỀN GIÁ TRỊ (A1, A2, A3) — CHẤP NHẬN, SỬA NGAY

Phản biện đúng hoàn toàn. Đây là lỗi hình thức toán học không thể chối, và tự mâu thuẫn nội bộ (A2 phụ thuộc A1). Sửa cả ba, đồng bộ 3 artifact.

### A1 — $\mathcal{V}_{agg}$: $(1,2) \to [1,2)$
- **main.tex dòng 203** (eq:vagg): `\mathcal{V}_{agg}\in(1,2)` → `\mathcal{V}_{agg}\in[1,2)`.
- **main.tex dòng 210** (eq:vagg-mu): `\mu\in[1,2]` giữ nguyên (đây là miền tham số chính sách, đúng — $\mu$ do người dùng đặt, đạt được cả 2 đầu). Nhưng miền GIÁ TRỊ hàm khi $\mu=2$: kết quả $\in[1,2)$. Không có ký hiệu range ở dòng này ngoài $\mu$, nên chỉ cần đảm bảo văn xuôi không nói "đạt 2×". Dòng 204 nói "up to $2\times$" — sửa thành "approaching $2\times$".
- **BaiBao_NoiDung.md**: tìm chỗ khai $\mathcal{V}_{agg}\in(1,2)$ → $[1,2)$; "nhân đôi" → "tiệm cận nhân đôi".
- **Paper.md**: đồng bộ tương tự nếu có.

### A2 — $\mathcal{P}(C_k)$: $(0,2] \to [0,2)$
- **main.tex dòng 215**: `\mathcal{P}(C_k)\in(0,2]` → `\mathcal{P}(C_k)\in[0,2)`. Sửa câu giải thích "bounds $\mathcal{P}(C_k)\in(0,2]$" cho khớp: lõi $\in[0,1]$, $\mathcal{V}_{agg}\in[1,2)$ ⇒ tích $\in[0,2)$.
- Đồng bộ BaiBao/Paper nếu có khai tương ứng.

### A3 — $C_i$: $(0,1] \to (0,1)$
- **main.tex dòng 119**: `C_i\in(0,1]` → `C_i\in(0,1)`.
- Kiểm BaiBao/Paper: mô tả $C_i$ — sửa nếu có `(0,1]`.

*Lưu ý nhất quán:* eq:confidence và định nghĩa $C_i$ ở dòng 117 (vector thuộc tính) — dòng 117 cũng ghi `C_i\in(0,1]`. Phải sửa CẢ HAI chỗ trong main.tex (117 và 119) + mọi bản VN.

---

## B. TRÍCH DẪN

### B1 — Sửa metadata CrisisSpot (CHẤP NHẬN)
Phản biện đúng. Sửa `references.bib` dòng 147–152: tác giả thật, đổi sang `@article` ESWA có DOI. Giữ tên khóa `madichetty2021crisisspot` để **không phải sửa 3 chỗ `\cite` trong main.tex** (đổi khóa rủi ro sót ref) — nhưng đây là đánh đổi: tên khóa vẫn gây hiểu lầm nội bộ. **Quyết định:** đổi luôn tên khóa thành `dar2024crisisspot` cho đúng liêm chính, VÀ sửa cả 3 `\cite{madichetty2021crisisspot}` trong main.tex (dòng 71, 93, và bảng positioning). An toàn hơn là đúng nửa vời.

```bibtex
@article{dar2024crisisspot,
  title={A social context-aware graph-based multimodal attentive learning framework for disaster content classification during emergencies},
  author={Dar, Shahid Shafi and Rehman, Mohammad Zia Ur and Bais, Karan and Haseeb, Mohammed Abdul and Kumara, Nagendra},
  journal={Expert Systems with Applications},
  volume={255},
  pages={125337},
  year={2024},
  publisher={Elsevier},
  doi={10.1016/j.eswa.2024.125337}
}
```
*(volume 255 theo ESWA 2024; nếu không chắc volume, để trống thay vì bịa — nhưng DOI là đủ định danh. Kiểm lại: dùng DOI làm định danh chính, volume/pages theo trang chính thức.)*

### B2 — Thêm nguồn thống kê bão (CHẤP NHẬN có điều kiện)
Con số "10–12 bão, 5–6 đổ bộ" là kiến thức phổ biến từ báo cáo khí tượng thủy văn VN. **Không có sẵn một `\cite` trong bib.** Theo ràng buộc "no hallucination", KHÔNG được bịa một reference. **Phương án:** (a) làm mềm câu chữ để không phải là thống kê cứng cần nguồn ("is among the most typhoon-exposed countries in Southeast Asia, hit by multiple storms and tropical depressions annually"), HOẶC (b) giữ số nhưng thêm cụm "(theo báo cáo của Tổng cục KTTV VN)" dưới dạng văn xuôi không-cite. **Chọn (a)** — an toàn nhất, không cần nguồn mới, không mất thông điệp. *(Đây là chỗ nếu người dùng có 1 nguồn chính thức thì tốt hơn — sẽ nêu trong phần cần-người-dùng.)*

### B3 — Nêu tên AHP (CHẤP NHẬN, nhẹ)
main.tex dòng 215: "...via a decision matrix~\cite{saaty1980ahp}" → "...via an Analytic Hierarchy Process (AHP) decision matrix~\cite{saaty1980ahp}".

---

## C. THAM CHIẾU CHÉO

### C1 — Sửa "Item~1.2" (CHẤP NHẬN)
Thay bằng văn xuôi mô tả, không cần đánh số lại danh sách đóng góp. main.tex dòng 372:
"Item~1.2's deeper question is not whether..." → "The deeper question behind the vulnerability-amplifier contribution (Sect.~\ref{...}) is not whether the vulnerability index $V_i$ changes the ranking (it does, by construction) but whether...". Đơn giản nhất: "A deeper question is not whether the vulnerability index $V_i$ changes the ranking..." — bỏ hẳn "Item 1.2".

### C2, C3 — Nhẹ, làm nếu tiện
- C2: để nguyên số (4.1)–(4.4) — chúng đang khớp; rủi ro thấp. **Bỏ qua** vòng này (không đáng động vào để tránh lỗi mới).
- C3: nhãn eq thừa vô hại. **Bỏ qua** — xóa nhãn có thể vô tình làm hỏng ref tương lai; giữ lại là an toàn.

---

## D. TRÌNH BÀY

### D1 — Sửa 2 bảng tràn lề (CHẤP NHẬN)
- `tab:positioning` (dòng 85–100): bọc `\resizebox{\textwidth}{!}{...}` quanh `tabular`.
- `tab:baselines` (dòng 314–333): bọc `\resizebox{\textwidth}{!}{...}`.
Cần `\usepackage{graphicx}` — đã có (dòng 13). ✓

### D2 — Bung ARI/NMI trong abstract (CHẤP NHẬN, nhẹ)
Lần đầu xuất hiện ở abstract: "ARI $=0.892$" → "Adjusted Rand Index (ARI) $=0.892$". NMI xuất hiện lần đầu ở phần thân (không trong abstract hiện tại) — kiểm và bung ở lần đầu.

---

## E. CODE ↔ TÀI LIỆU

### E1 — Vá `modularity()` (CHẤP NHẬN)
Truyền `resolution` xuống. `community_louvain.modularity` **không** nhận tham số resolution (API python-louvain chỉ có modularity chuẩn). Vậy để trung thực với docstring RB, phải hoặc (a) tự tính Q theo công thức RB có $\lambda$, hoặc (b) sửa docstring + bỏ tham số để không hứa điều không làm.

**Quyết định:** Vì mọi kết quả công bố ở $\lambda=1$ (nơi RB ≡ modularity chuẩn) nên (b) là đủ và trung thực nhất: bỏ tham số `resolution` khỏi chữ ký `modularity()` HOẶC giữ nhưng thêm `assert resolution==1.0` + ghi chú "chỉ hỗ trợ λ=1; python-louvain.modularity không nhận resolution". Chọn: **thêm ghi chú rõ + raise nếu resolution≠1**, an toàn và không vờ như tính được RB tổng quát. Điều này không đổi bất kỳ số công bố nào.

### E2 — Sửa note "90km" → "103km" (CHẤP NHẬN)
`generate.py`: `'S1: ngập nóc tại Hội An (xa 90km)'` → `'S1: ngập nóc tại Hội An (xa ~103km)'`. Chỉ là chuỗi ghi chú, không đổi tọa độ/kết quả. Chạy lại generate để chắc dataset.json note cập nhật (tọa độ không đổi vì seed cố định).

### E3 — Đồng bộ GiaiThichCongThuc.md (CHẤP NHẬN, nhẹ)
Thêm một dòng nêu tổng quát hóa $\mu$ (eq:vagg-mu) vào mục 4.5 của `GiaiThichCongThuc.md` để nhất quán với bài. Không bắt buộc cho tính đúng của bài, nhưng giữ resource nhất quán theo ràng buộc.

---

## KẾ HOẠCH KIỂM CHỨNG SAU SỬA
1. `grep` xác nhận không còn `(1,2)`, `(0,2]`, `(0,1]` cho các đại lượng tương ứng trong main.tex + bản VN.
2. Biên dịch lại `xelatex → bibtex → xelatex ×2`; xác nhận **0 undefined citation** (đặc biệt sau đổi khóa `dar2024crisisspot`), và kiểm log 2 bảng không còn overfull >20pt.
3. Chạy lại `demo` phần liên quan (generate + 1 experiment) để chắc note cập nhật và không vỡ gì.
4. Xác nhận số trang & headline numbers không đổi.

## CẦN NGƯỜI DÙNG (nếu muốn mức tối đa)
- **B2:** Nếu có một nguồn chính thức cho "10–12 bão/năm, 5–6 đổ bộ" (ví dụ báo cáo Tổng cục KTTV hoặc một bài journal về khí hậu VN), cung cấp để thêm `\cite` thay vì làm mềm câu chữ. Hiện tại sẽ làm mềm để tránh bịa nguồn.
