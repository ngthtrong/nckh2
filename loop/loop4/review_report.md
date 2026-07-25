# BÁO CÁO PHẢN BIỆN KHOA HỌC — VÒNG 4 (CRITICAL REVIEW)

**Ngày:** 2026-07-24
**Phạm vi:** `paper/main.tex` (bản LNCS tiếng Anh), `resource/BaiBao_NoiDung.md`, `resource/Paper.md`, `demo/` (mã nguồn + JSON kết quả), `paper/references.bib`.
**Phương pháp:** Kiểm chứng chéo trực tiếp từng con số headline với JSON trong `demo/results/tables/`, tính lại bằng tay các công thức/tỉ lệ, đối chiếu `\cite`/`\ref`/`\label`, biên dịch LaTeX kiểm log, và tra cứu độc lập metadata trích dẫn.

> **Bối cảnh:** Vòng 1–3 đã xử lý các lỗi vĩ mô (dạng gating vs cộng, gate $C_i$, cấu trúc ground-truth 12 nhãn, cận $\tau$, tỉ lệ tin giả). Vòng 4 tập trung soi lớp lỗi còn lại: **tính đúng đắn toán học của khai báo miền giá trị (range)**, **tính trung thực của trích dẫn**, **tính vẹn toàn của tham chiếu chéo & trình bày**, và **độ trung thực code↔docstring**. Đây là các lỗi vi mô nhưng đúng loại mà một phản biện khắt khe của hội đồng sẽ bắt.

---

## A. LỖI TOÁN HỌC — KHAI BÁO MIỀN GIÁ TRỊ SAI (nghiêm trọng về mặt hình thức)

Ba khai báo miền giá trị trong bài đều sai ở đầu mút. Với một bài nhấn mạnh "tính chính xác toán học" làm điểm bán hàng, đây là loại lỗi phản biện sẽ khoanh tròn ngay.

### A1. $\mathcal{V}_{agg} \in (1,2)$ — SAI ở cận dưới; đúng phải là $[1,2)$
`main.tex` dòng 203 (eq:vagg) và dòng 210 (eq:vagg-mu) khai báo $\mathcal{V}_{agg}\in(1,2)$ (mở ở 1).

**Chất vấn:** Khi một cụm không có đối tượng yếu thế, $\sum V_i = 0$, mà $\tanh(0)=0$ **chính xác**, nên $\mathcal{V}_{agg} = 1 + \tanh(0) = 1$ **đúng bằng 1**. Trường hợp này KHÔNG hiếm — theo `exp1_C`, phần lớn cụm (18/27) có $\mathcal{V}_{agg}=1{,}0$ đúng bằng 1. Vậy 1 là giá trị **đạt được**, không phải cận mở. Cận trên 2 thì đúng là mở ($\tanh<1$ mọi hữu hạn). Miền đúng: $\boxed{[1,2)}$.

*Bằng chứng:* `exp1_C_v_multiplier.json` — 18 cụm có `"v_agg": 1.0`.

### A2. $\mathcal{P}(C_k) \in (0,2]$ — SAI ở CẢ HAI đầu mút; đúng phải là $[0,2)$
`main.tex` dòng 215 khai báo $\mathcal{P}(C_k)\in(0,2]$.

**Chất vấn:** (i) Cận dưới: lõi rủi ro chuẩn hóa $\in[0,1]$ có thể **đúng bằng 0** (một cụm mà $\widetilde{\mathcal{E}}=\widetilde{\mathcal{F}}=\widetilde{\mathcal{N}}=0$), nhân với $\mathcal{V}_{agg}\ge1$ vẫn ra $\mathcal{P}=0$ — nên 0 **đạt được**, không phải cận mở. (ii) Cận trên: vì $\mathcal{V}_{agg}<2$ (mục A1) và lõi $\le1$, tích $\mathcal{P}<2$ **không bao giờ chạm 2** — nên 2 KHÔNG phải giá trị đạt được, không được đóng ngoặc. Cả hai đầu mút đều khai sai. Miền đúng: $\boxed{[0,2)}$.

### A3. $C_i \in (0,1]$ — SAI ở cận trên; đúng phải là $(0,1)$
`main.tex` dòng 119 khai báo $C_i\in(0,1]$.

**Chất vấn:** $C_i=\sigma(z)$ với $\sigma$ là sigmoid. Sigmoid có miền giá trị là khoảng **mở** $(0,1)$ — tiệm cận nhưng KHÔNG BAO GIỜ đạt 1 với $z$ hữu hạn. Đóng ngoặc ở 1 là bất khả về mặt toán học. Miền đúng: $\boxed{(0,1)}$.

---

## B. LỖI TRÍCH DẪN — METADATA BỊA/SAI (nghiêm trọng về liêm chính học thuật)

### B1. `madichetty2021crisisspot`: tác giả SAI, tên khóa GÂY HIỂU LẦM
`references.bib` dòng 147–152:
```bibtex
@article{madichetty2021crisisspot,
  title={A social context-aware graph-based multimodal attentive learning framework...},
  author={Kumari, Shalini and others},
  journal={arXiv preprint arXiv:2410.08814},
  year={2024}
}
```
**Chất vấn:** Tra cứu độc lập arXiv:2410.08814 cho thấy bài "CrisisSpot" thực sự do **Shahid Shafi Dar, Mohammad Zia Ur Rehman, Karan Bais, Mohammed Abdul Haseeb, Nagendra Kumara** viết, đăng trên **Expert Systems with Applications, 2024, DOI 10.1016/j.eswa.2024.125337**. Trường `author={Kumari, Shalini and others}` là **sai hoàn toàn** — không ai trong danh sách tên "Kumari" hay "Madichetty". Tên khóa `madichetty` còn ngụ ý một nhà nghiên cứu có thật khác (Madichetty có công trình riêng về phân loại tweet thảm họa) → gây hiểu lầm nghiêm trọng. *Con số "5,01–9,45%" F1 ở dòng 71 là được nguồn hóa đúng* (chính abstract bài đó báo cáo), chỉ metadata tác giả/venue sai.

*Nguồn kiểm chứng:* arXiv:2410.08814 (abstract + DOI ESWA).

### B2. Thống kê bão thiếu trích dẫn
`main.tex` dòng 49: "Vietnam...is struck by roughly **10–12 storms** and tropical depressions each year, of which **5–6 make landfall**." Đây đúng loại thống kê định lượng cụ thể BẮT BUỘC phải có nguồn, nhưng đứng trần không `\cite`. So sánh: câu "5,01–9,45%" ngay đó lại có trích dẫn.

### B3. `saaty1980ahp` — trích mà không gọi tên phương pháp
`main.tex` dòng 215 trích Saaty chỉ như "a decision matrix", không nêu tên **Analytic Hierarchy Process (AHP)** — chính là nội dung của tài liệu đó. Người đọc không rõ phương pháp gì. (Mức nhẹ.)

---

## C. LỖI THAM CHIẾU CHÉO & CẤU TRÚC

### C1. "Item~1.2" — tham chiếu GÃY
`main.tex` dòng 372: "Item~1.2's deeper question is not whether the vulnerability index...". **Chất vấn:** không tồn tại "Item 1.2" nào trong bài. Danh sách "Main contributions" (dòng 61–66) là `\itemize` (bullet không đánh số), nên không có mục nào mang nhãn "1.2". Người đọc không thể định vị. (Nó có ý trỏ tới đóng góp #2 — hệ số khuếch đại tổn thương.)

### C2. Số mục con hard-code trong văn xuôi
`main.tex` dòng 112: "(4.1) edge extraction...; (4.2)...; (4.3)...; (4.4)..." — viết số cứng thay vì `\ref{}`. Hiện khớp, nhưng sẽ lệch nếu thêm/đổi thứ tự mục con. (Mức nhẹ, dễ vỡ.)

### C3. Nhãn phương trình chết
11 nhãn (`eq:confidence`, `eq:weight`, `eq:sgeo`, `eq:stemp`, `eq:scontext`, `eq:modularity`, `eq:priority`, `eq:ntilde`, `eq:fmax`, `eq:vagg`, `eq:vagg-mu`) được định nghĩa nhưng không nơi nào `\eqref{}`. Không phải lỗi biên dịch, chỉ là nhãn thừa. (Mức nhẹ.)

---

## D. LỖI TRÌNH BÀY / FORMAT

### D1. Bảng tràn lề (Overfull \hbox)
Biên dịch cho thấy **hai bảng tràn lề vượt ngưỡng**: `tab:positioning` (dòng 89–100) tràn **111,4pt**, `tab:baselines` (dòng 318–333) tràn **60,9pt** — sẽ lòi ra ngoài cột chữ LNCS trong PDF. (Các overfull 1–17pt khác chỉ là cosmetic, bỏ qua.)

### D2. ARI/NMI dùng trước khi định nghĩa
`main.tex` dòng 43 (abstract) dùng "ARI"/"NMI" chưa giải nghĩa; mãi đến dòng 230 (Metrics) mới định nghĩa. Abstract thường đọc độc lập → nên bung nghĩa ngay lần đầu.

---

## E. LỖI TRUNG THỰC CODE ↔ TÀI LIỆU

### E1. `modularity()` âm thầm bỏ tham số `resolution`
`demo/pipeline/clustering.py` dòng 72–77: hàm `modularity(w, labels, resolution=1.0)` **nhận** tham số `resolution` nhưng dòng 77 gọi `community_louvain.modularity(part, g, weight="weight")` **không truyền** nó đi. Docstring đầu file (dòng 3–4) lại quảng cáo công thức Reichardt–Bornholdt có $\lambda$.

**Chất vấn:** Nếu ai đó gọi `modularity(..., resolution=2.0)` kỳ vọng $Q$ theo RB, họ nhận $Q$ ở $\lambda=1$ mà không hay biết. **Tác động hạn chế:** mọi $Q$ đã **công bố** (0,8311) đều ở $\lambda=1$, đúng bằng modularity chuẩn — nên không con số nào trong bài sai. Nhưng đây là lỗ hổng trung thực code↔docstring cần vá (truyền param hoặc bỏ param + sửa docstring).

### E2. Nhãn ghi chú dataset lỗi thời: "xa 90km"
`demo/data/generate.py` gắn note `'S1: ngập nóc tại Hội An (xa 90km)'` cho điểm S1_B. **Khoảng cách thực tế** giữa S1_A–S1_B tính bằng Haversine = **102,8 km**. Bài báo ghi "~103 km" (dòng 224) — **đúng**. Chỉ nhãn ghi chú nội bộ "90km" là lỗi thời/sai, gây lệch khi ai đọc code. (Con số bài báo không sai.)

### E3. Tài liệu phụ `GiaiThichCongThuc.md` lạc hậu so với bài
`resource/GiaiThichCongThuc.md` (dòng ~188) vẫn trình bày $\mathcal{V}_{agg}=1+\tanh(\frac1s\sum V_i)$ dạng gốc, **chưa có** tổng quát hóa tham số $\mu$ (eq:vagg-mu) mà bài đã thêm. Là tài liệu giải thích phụ trợ, không phải lỗi của bài, nhưng nên đồng bộ để nhất quán.

---

## TÓM TẮT MỨC ĐỘ — VÒNG 4

| # | Lỗi | Mức | File |
|---|-----|-----|------|
| A1 | $\mathcal{V}_{agg}\in(1,2)$ → $[1,2)$ | Nghiêm trọng (toán) | main.tex, các bản VN |
| A2 | $\mathcal{P}\in(0,2]$ → $[0,2)$ | Nghiêm trọng (toán) | main.tex, các bản VN |
| A3 | $C_i\in(0,1]$ → $(0,1)$ | Nghiêm trọng (toán) | main.tex, các bản VN |
| B1 | Tác giả CrisisSpot sai (Kumari→Dar et al.) | Nghiêm trọng (liêm chính) | references.bib |
| B2 | Thống kê bão thiếu `\cite` | Trung bình | main.tex |
| C1 | "Item~1.2" tham chiếu gãy | Nghiêm trọng (cấu trúc) | main.tex |
| D1 | 2 bảng tràn lề >60pt | Trung bình | main.tex |
| E1 | `modularity()` bỏ rơi `resolution` | Trung bình (code) | clustering.py |
| E2 | Note "90km" vs thực 102,8km | Nhẹ (code) | generate.py |
| B3, C2, C3, D2, E3 | Trích dẫn/nhãn/trình bày/đồng bộ | Nhẹ | nhiều |

**Điểm mạnh xác nhận (không có lỗi):** Toàn bộ số headline (ARI 0,892; NMI 0,927; đường kính 100→0,30 km; baseline 0,339/0,890/0,688/0,730; $\tau$ 0,994/0,986/0,957; equity 10,4%/8,7%; AUC 0,9651; gate 55%; byte 100–111) khớp chính xác JSON. Mọi công thức $w_{ij}, \mathcal{S}_{geo/temp/context}, \mathcal{E}_{agg}, \mathcal{F}_{max}, \widetilde{\mathcal{N}}$ khớp 1:1 code. Giá trị $C_i$ nghịch cảnh, bảng $\tanh$, hướng bất đối xứng $\tau_E>\tau_F$ đều tái lập đúng. Mọi `\cite` đều resolve, mọi hình fig1–7 tồn tại, biên dịch 19 trang 0 undefined ref.
