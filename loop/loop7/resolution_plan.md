# Loop 7 — Kế hoạch Giải quyết (Step 2)

**Vai trò:** Tác giả (rời vai phản biện, giữ khách quan). Trả lời trung thực từng chất vấn Step 1, đề xuất sửa cụ thể.

---

## 7.1 — Thống kê bão mâu thuẫn giữa các artifact — CHẤP NHẬN, SỬA NGAY

**Chất vấn:** main.tex dòng 49 (đã sửa+trích dẫn ở loop 4) ghi "6–8 cơn ảnh hưởng Việt Nam, ~11 phát triển trên Biển Đông" với `\cite{isponre2009varcc}`. Nhưng BaiBao dòng 17 (chưa trích dẫn, cũ) ghi "10–12 cơn bão và áp thấp, trong đó 5–6 ảnh hưởng đất liền". Cùng một sự thật, hai bộ số khác nhau — vi phạm nhất quán ba-artifact.

**Thừa nhận:** Đúng. BaiBao là bản gốc tiếng Việt chưa được cập nhật đồng bộ khi loop 4 sửa main.tex. Kiểm chứng độc lập (Wikipedia "Tropical cyclones in Vietnam"): 6–8 cơn ảnh hưởng Việt Nam/năm; 11–13 cơn vào Biển Đông (South China Sea). Bộ số của main.tex khớp nguồn kiểm chứng; bộ số của BaiBao (10–12 / 5–6) KHÔNG khớp và không có trích dẫn.

**Sửa:** Viết lại BaiBao dòng 17 cho khớp main.tex — "khoảng 6–8 cơn bão và áp thấp nhiệt đới ảnh hưởng mỗi năm (trong số ~11 cơn hình thành trên Biển Đông)". Paper.md (bản Việt cũ hơn) không mở đầu bằng câu thống kê bão này nên không cần sửa; xác nhận lại.

**Không đụng số nào khác** — chỉ đồng bộ một câu.

**Trạng thái:** ⏳ Thực thi ở Step 3.

---

## 7.2 — Sai số lượng thí nghiệm ("chín exp1–exp9") — CHẤP NHẬN, SỬA NGAY

**Chất vấn:** BaiBao dòng 296 và Paper.md dòng 193 mô tả `demo/experiments/` chứa "chín thí nghiệm exp1–exp9". Nhưng thư mục có **exp10_packet_size.py** (thí nghiệm thật, đo kích thước gói metadata 100–111 byte). Chính BaiBao trích "xem exp10" ở dòng 113 và 404 → tự mâu thuẫn.

**Thừa nhận:** Đúng, lỗi thật. `run_all.py` liệt kê 10 thí nghiệm (exp1–exp10). exp10 có docstring, JSON output (`exp10_packet_size.json`), và được viện dẫn trong chính bài. "Chín thí nghiệm exp1–exp9" là số đếm cũ, chưa cập nhật khi exp10 được thêm.

**Sửa:**
1. BaiBao dòng 296: "chín thí nghiệm `exp1`–`exp9`" → "mười thí nghiệm `exp1`–`exp10`".
2. Paper.md dòng 193: "chín thí nghiệm `exp1`–`exp9`" → "mười thí nghiệm `exp1`–`exp10`".
3. main.tex: KHÔNG có chuỗi "nine experiments" tương đương ở phần Setup (nó chỉ nói "The full pipeline is implemented in Python (...)") — kiểm tra và xác nhận không cần sửa.

**Không đụng** số liệu kết quả nào.

**Trạng thái:** ⏳ Thực thi ở Step 3.

---

## KHÔNG SỬA (đã kiểm loop 7, đúng hoặc chấp nhận được)

- Paper.md dòng 15 "F1-score tăng từ 5% đến 9.45%": số thấp là 5,01% (làm tròn "5%"); main.tex đã dùng "5.01–9.45%" chính xác. Paper.md là bản Việt cũ, "5%" là làm tròn chấp nhận được — nhưng để nhất quán tuyệt đối có thể sửa thành "5,01%". → **Sửa nhẹ luôn cho sạch.**
- Mọi headline number (0,892; 0,927; 55%; 10,4%; 0,9651; τ 0,99/0,94; 100–111B; 0,339; 0,688; 0,730) đã kiểm ở loop 4–6, khớp demo. Không đụng.
- Cross-ref, citation, figure files: đã kiểm loop 6, sạch.

---

## THỨ TỰ THỰC THI (Step 3)

1. BaiBao_NoiDung.md dòng 17 (thống kê bão) + dòng 296 (số thí nghiệm).
2. Paper.md dòng 193 (số thí nghiệm) + dòng 15 (5% → 5,01%).
3. main.tex: xác nhận không có "nine experiments" cần sửa (Setup chỉ liệt kê thư viện).
4. Recompile main.tex → xác nhận 0 undefined refs, số trang ổn định (main.tex không đổi về số → chủ yếu để chắc chắn).
5. Cập nhật memory (paper_latex_lncs.md) với hai fix loop 7.
