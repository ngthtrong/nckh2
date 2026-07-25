# Loop 13 — Kế hoạch Giải quyết (Step 2)

**Vai trò:** Tác giả. Nguyên tắc loop này: **artifact do code sinh ra là sự thật**; nếu bản trong `paper/` lệch với bản `demo/results/` thì `paper/` phải được cập nhật, không bao giờ ngược lại. Đồng thời caption phải khớp JSON, không khớp ký ức.

---

## 13.1 — Hình 7 cũ trong `paper/figures/` — CHẤP NHẬN, SỬA NGAY (ưu tiên cao nhất)

**Thừa nhận:** Đúng hoàn toàn, và đây là lỗi tệ nhất còn lại vì nó **tự bác bỏ** câu tuyên bố Reproducibility. Bằng chứng không thể tranh cãi: 6/7 hình khớp MD5 giữa hai thư mục, chỉ `fig7` lệch (`9bae869d` vs `4fed5f9d`); chạy lại `make_figures.py` cho ra đúng bản `demo/` — nên bản `paper/` là tồn đọng từ code cũ. Nghiêm trọng hơn cả kích thước file: **hai hình khác loại biểu đồ** (đường vs cột), nên đây không phải khác biệt nén ảnh mà là hai phiên bản code khác nhau.

**Sửa:** copy bản đúng từ `demo/results/figures/` sang `paper/figures/`, rồi biên dịch lại và xác nhận MD5 khớp cho **cả 7** hình.

**Phòng ngừa tái diễn — thêm bước kiểm tự động.** Lỗi này thoát được 12 vòng phản biện vì không ai so checksum. Để loop sau không phải soi lại bằng mắt, thêm một script kiểm:
- Tạo `demo/verify_figures.py` (đặt trong `demo/` vì nó là script kiểm của bộ demo, không phải báo cáo phân tích nên **không** thuộc `loop/`): so MD5 từng hình `paper/figures/*.png` với `demo/results/figures/*.png`, in ra `OK` / `STALE` / `MISSING`, exit code khác 0 nếu có lệch.

Đây là bổ sung mã nguồn hợp lệ theo Bước 3 của quy trình ("Chỉnh sửa mã nguồn … nếu có sai sót ảnh hưởng đến bài báo") — và sai sót này ảnh hưởng trực tiếp đến bài báo.

---

## 13.2 — Caption Hình 7 — CHẤP NHẬN, viết lại cho khớp JSON

**Thừa nhận:** Đúng cả hai điểm.
- "essentially unchanged" **hạ thấp** kết quả thật: `top3_set_preserved_pct = 100.0` ở cả ba mức, và thân bài đã nói thẳng "100% of all 600 trials". Caption phải nói 100%.
- Ngưỡng "above 0.93" là con số của bộ dữ liệu **cũ** (min τ cũ 0,937). Bộ hiện hành: min τ ở ±0,10 là **0,9104** → ngưỡng đúng là **0,91**, đúng con số Abstract/thân bài/Kết luận dùng.

**Sửa `main.tex` dòng 463:**
> "Ranking stability under $\omega$ perturbation. Mean Kendall's $\tau$ stays at $0.955$ or above at realistic perturbation ($\pm0.05$--$\pm0.10$) and no trial falls below $0.91$; the top-3 clusters are preserved in $100\%$ of trials at every level."

Mọi con số ở đây (0,955 / 0,91 / 100%) đều truy về `exp5_ranking_stability.json`.

---

## 13.3 — Hai hình không dùng + lệch mô tả Việt/Anh — CHẤP NHẬN, xử lý ba việc

**Thừa nhận:** Đúng. Ba việc riêng biệt:

1. **Xóa artifact chết khỏi `paper/figures/`:** `fig2_map.png` (238 KB) và `fig3_heatmap.png` (117 KB) không được `\includegraphics` ở đâu → 355 KB rác trong thư mục nộp bài. Xóa khỏi `paper/figures/`.
   - **Giữ nguyên** trong `demo/results/figures/` — chúng là output hợp lệ của suite và dùng cho dashboard/trình bày nội bộ.
   - Cập nhật `verify_figures.py` ở 13.1 để chỉ kiểm những hình **thực sự được bài dùng** (đọc danh sách từ `\includegraphics` trong `main.tex`), tránh báo động giả về hai hình này.

2. **Không thêm hai hình đó vào bài.** Bài đã 25 trang; thêm hình chỉ làm nặng thêm mà không phục vụ luận điểm nào chưa được bảng biểu che phủ. Đây là lựa chọn biên tập, nêu rõ để loop sau không lật lại.

3. **Sửa lệch mô tả trong BaiBao §5.14:** bản Việt hiện mô tả **bảy** hình như thể tất cả minh họa bài báo, và nhắc "dashboard bản đồ Leaflet" mà `main.tex` không đề cập. Sửa thành: nêu rõ **năm** hình được dùng trong bản LaTeX, và **hai** hình còn lại (`fig2_map`, `fig3_heatmap`) cộng dashboard là **artifact trực quan hóa của bộ demo**, không phải hình của bài báo. Cách này trung thực và giải thích được sự tồn tại của chúng.

---

## 13.4 — Caption Hình 1(b) — CHẤP NHẬN, thêm con số 55%

**Sửa dòng 357:** "(b) The confidence gate reduces the fake report's claimed population of 200 to an effective 90." → "(b) The confidence gate reduces the fake report's claimed population of 200 to an effective $90$---a $55\%$ reduction of phantom population."

Khớp `exp1_E_confidence_gate.json` (`reduction_pct: 55.0`) và nối được với headline ở Abstract/§1E/Kết luận.

---

## 13.5 — Hai overfull hbox — CHẤP NHẬN, sửa cái sửa được

- **Overfull dòng 175 (6,76pt)**: nằm trong nhãn TikZ `$v_i=(L,T,F,\!E,\!N,\!V,\!C)$` với `text width=20mm` quá chật. Sửa: nới `text width` lên `22mm`. Rủi ro thấp (hình đã `\resizebox` theo `\textwidth`).
- **Overfull dòng 115–116 (4,56pt)**: đoạn Gap 2 văn xuôi, tràn 4,56pt (~1,6mm) do một từ dài không ngắt được. Sửa bằng cách chỉnh nhẹ diễn đạt để dòng xuống tự nhiên, **không** thêm `\-` hyphenation thủ công (dễ vỡ khi chỉnh sau).

Mục tiêu sau sửa: **0 overfull** trong build log.

---

## KHÔNG SỬA — nêu rõ để loop sau không lật lại

- **PDF 25 trang.** LNCS full paper thường 12–18 trang. Đây là quyết định **phạm vi nộp bài** phụ thuộc call-for-papers cụ thể mà tôi không có. Tự ý cắt 7+ trang nội dung đã được 13 vòng phản biện kiểm chứng là hủy công việc, không phải sửa lỗi. **Ghi nhận rõ ràng để nhóm tác giả quyết định**, kèm gợi ý: nếu cần cắt, ứng viên hợp lý nhất là gộp Exp10 vào Discussion (nó chỉ có một con số) và nén Bảng 2 (tham số) vào phần phụ lục.

---

## THỨ TỰ THỰC THI (Step 3)

1. Copy `demo/results/figures/fig7_ranking_stability.png` → `paper/figures/`. Xác nhận MD5 khớp.
2. Xóa `paper/figures/fig2_map.png` và `fig3_heatmap.png`.
3. Tạo `demo/verify_figures.py` (đọc `\includegraphics` từ `main.tex`, so MD5, exit≠0 nếu lệch). Chạy → phải PASS.
4. `main.tex` 463: viết lại caption Hình 7.
5. `main.tex` 357: thêm 55% vào caption Hình 1.
6. `main.tex` 175: nới `text width` TikZ; dòng 115: chỉnh diễn đạt để hết overfull.
7. BaiBao §5.14: sửa mô tả 7 hình → 5 hình bài báo + 2 hình demo + dashboard.
8. Biên dịch `xelatex → bibtex → xelatex ×2`. Yêu cầu: **0 overfull**, 0 undefined ref, 0 multiply-defined.
9. Chạy lại `verify_figures.py` lần cuối để chốt.
