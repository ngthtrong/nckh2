# Loop 7 — Báo cáo Phản biện (Step 1)

**Vai trò:** Giáo sư chủ tịch hội đồng phản biện — vòng cuối (loop 7/7). Tập trung soi các artifact ít được bảo trì nhất (Paper.md Việt cũ, BaiBao) để bắt lỗi nhất quán số liệu còn sót sau loops 4–6.

Loops 4–6 đã xử lý: miền giá trị (V_agg/P/C_i), trích dẫn CrisisSpot, bug modularity(), dataset note cũ, NMI≡V-measure, và cách diễn đạt "0 m offset" của nhóm kịch bản. Loop 7 quét phần còn lại.

---

## CHẤT VẤN 7.1 — Số liệu bão MÂU THUẪN giữa ba artifact (nghiêm trọng)

Cùng một sự thật ("mỗi năm Việt Nam hứng chịu bao nhiêu cơn bão") nhưng ba artifact ghi ba con số khác nhau:

| Artifact | Con số | Trích dẫn? |
|---|---|---|
| `paper/main.tex` dòng 49 | "**6–8** ảnh hưởng VN (trong ~**11** hình thành ở Biển Đông)" | ✅ `isponre2009varcc` |
| `resource/BaiBao_NoiDung.md` dòng 17 | "**10–12** bão/ATNĐ, trong đó **5–6** ảnh hưởng đất liền" | ❌ không |

**Vấn đề:**
- main.tex đã được sửa ở loop 4 để khớp con số kiểm chứng được + có trích dẫn. BaiBao vẫn giữ con số cũ, khác hẳn, và **không có trích dẫn nào**.
- Đây là vi phạm nguyên tắc nhất quán ba-artifact: BaiBao là "nguồn sự thật tiếng Việt" mà lại lệch với bản tiếng Anh đã xuất bản.
- Kiểm chứng độc lập (Wikipedia "Tropical cyclones in Vietnam"): "6–8 tropical cyclones annually affect Vietnam"; "11–13 entering the South China Sea"; "4–6 make landfall". → **main.tex đúng**, BaiBao "10–12 / 5–6" sai lệch.

**Câu hỏi gay gắt:** Vì sao con số bão trong bản tiếng Việt lại khác bản tiếng Anh, và dựa vào nguồn nào để nói "10–12 cơn"? Nếu không có nguồn, đây là số liệu không kiểm chứng — đúng loại lỗi mà quy trình này phải loại bỏ.

---

## CHẤT VẤN 7.2 — Đếm sai số thí nghiệm ("chín" vs thực tế mười)

- `resource/BaiBao_NoiDung.md` dòng 296: "…mã và số liệu thô nằm trong `demo/` (**chín thí nghiệm** `exp1`–`exp9` trong `demo/experiments/`…)"
- `resource/Paper.md` dòng 193: "…**chín thí nghiệm** `exp1`–`exp9` trong `demo/experiments/`…"

Nhưng thư mục `demo/experiments/` thực tế chứa **mười** file: `exp1`…`exp9` **và `exp10_packet_size.py`** (đo kích thước gói metadata, một thí nghiệm thực thụ với JSON kết quả `exp10_packet_size.json`, chạy ở bước 11/13 trong `run_all.py`).

**Tệ hơn — tự mâu thuẫn nội bộ:** chính BaiBao ở dòng 113 ("…đo được 100–111 byte, **xem exp10**") và dòng 404 ("…**xem exp10**") lại viện dẫn exp10. Vậy cùng một tài liệu vừa nói "chín thí nghiệm exp1–exp9" vừa trích dẫn exp10 — không thể cùng đúng.

**Câu hỏi gay gắt:** Câu mô tả nội dung thư mục code đếm nhầm — có exp10 hẳn hoi và nó được trích dẫn ở chỗ khác trong cùng tài liệu. Đây là lỗi nhất quán nội bộ phải sửa.

*(Lưu ý phân biệt: main.tex đánh số các mục "Experiment 1–9" trong phần Experiments và gộp số đo gói metadata vào phần Thảo luận (dòng 386) — cách trình bày này hợp lệ vì nó nói về **mục bài báo**, không phải nội dung thư mục code. Chỉ câu mô tả `demo/experiments/` ở BaiBao/Paper.md là sai.)*

---

## ĐÃ KIỂM — KHÔNG PHẢI LỖI (giữ nguyên)

- Abstract main.tex: mọi con số (0.892, 55%, 0.339, 0.890, 0.688, 0.730, τ 0.99/0.94) khớp demo. OK.
- Paper.md dòng 15 "F1 tăng từ 5% đến 9.45%": làm tròn nhẹ của 5.01–9.45%; main.tex đã ghi chính xác "5.01–9.45%". Có thể chỉnh cho khớp nhưng không sai bản chất → chỉnh luôn cho gọn.
- Paper.md dòng 230 "ARI 0,89" (làm tròn của 0,892): chấp nhận trong văn tóm tắt.
- packet 100–111 byte, exp7 10.4%, AUC 0.9651, tanh, β/γ: đã kiểm ở loops trước, khớp.

---

## TỔNG KẾT STEP 1

Hai lỗi nhất quán số liệu thực (không phải lỗi tính toán, mà lỗi đồng bộ giữa các bản):
1. **7.1** — số bão BaiBao (10–12/5–6, không nguồn) ≠ main.tex (6–8/~11, có nguồn, kiểm chứng được). NGHIÊM TRỌNG.
2. **7.2** — "chín thí nghiệm exp1–exp9" sai: có exp10, và cùng tài liệu tự viện dẫn exp10. TRUNG BÌNH.

Cộng một chỉnh nhỏ tùy chọn: Paper.md "5%"→"5,01%".
