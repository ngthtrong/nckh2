# Loop 8 — Kế hoạch Giải quyết (Step 2)

**Vai trò:** Tác giả (rời vai phản biện). Trả lời trung thực chất vấn 8.1–8.2, đề xuất sửa cụ thể. Nguyên tắc: **không đụng con số nào**, chỉ sửa mệnh đề nhân-quả cho khớp cơ chế đã kiểm chứng bằng code.

---

## 8.1 + 8.2 — Diễn giải HDBSCAN ngược cơ chế — CHẤP NHẬN, SỬA NGAY

**Chất vấn:** Bài nói HDBSCAN "gộp ốc đảo" làm completeness tụt. Nhưng gộp → giảm homogeneity; completeness tụt là do xé lẻ. Code xác nhận: HDBSCAN homogeneity 0,9154 (> Louvain 0,8639), xé lẻ lớp 1 và 4, dồn 36 điểm có nhãn vào bin nhiễu. Đường kính 25 km bị thổi bởi bin nhiễu (71 km) + cụm dư (196 km), không phải mega-cụm gộp.

**Thừa nhận:** Đúng hoàn toàn. Đây là lỗi diễn giải thật, và trớ trêu là **sửa lại còn làm lập luận Exp9 MẠNH HƠN**: completeness-tụt-do-xé-lẻ đúng chính xác định nghĩa completeness, biến ví dụ HDBSCAN thành minh họa sách-giáo-khoa cho việc "vì sao cần completeness bên cạnh ARI". Bản cũ vô tình tự mâu thuẫn (nói completeness nhưng mô tả cơ chế của homogeneity).

**Sửa cụ thể:**

1. **main.tex dòng 345** (Exp4):
   - Cũ: *"...at 25 km mean diameter, merging distinct islands;"*
   - Mới: *"...at 25 km mean diameter---but that diameter is inflated by a catch-all noise bin ($\sim$36 labeled points) plus one scattered residual cluster, while it fragments two islands rather than forming coherent zones;"*

2. **main.tex dòng 382** (Exp9):
   - Cũ: *"while HDBSCAN drops to 0.929 because it merges islands---a 0.07 completeness gap..."*
   - Mới: *"while HDBSCAN drops to 0.929 because it \emph{fragments} two islands---leaving $\sim$36 labeled points in its noise bin and splitting one island across residual clusters. This is precisely a completeness failure (a ground-truth class scattered across clusters), \emph{not} a homogeneity failure: no HDBSCAN cluster fuses two coherent islands (its homogeneity $0.915$ in fact exceeds Louvain's $0.864$). That is exactly the distinction ARI blurs---a 0.07 completeness gap where ARI shows barely 0.002."*

3. **BaiBao dòng 360** (Exp4 phân tích):
   - Cũ: *"...đường kính trung bình 25 km — gộp nhiều ốc đảo khác nhau vào cùng cụm;"*
   - Mới: *"...đường kính trung bình 25 km — nhưng đường kính này bị thổi lên bởi một bin nhiễu gom $\sim$36 điểm có nhãn cộng một cụm dư rải rác, và nó **phân mảnh** hai ốc đảo thay vì tạo cụm gắn kết;"*

4. **BaiBao dòng 390** (Exp9):
   - Cũ: *"HDBSCAN tụt xuống 0,929 vì gộp các ốc đảo — một khoảng cách completeness 0,07..."*
   - Mới: *"HDBSCAN tụt xuống 0,929 vì **xé lẻ** hai ốc đảo — dồn $\sim$36 điểm có nhãn vào bin nhiễu và tách một ốc đảo ra nhiều cụm dư. Đây đúng là lỗi *completeness* (một lớp ground-truth bị rải ra nhiều cụm), **không phải** lỗi homogeneity: không cụm HDBSCAN nào gộp hai ốc đảo gắn kết (homogeneity 0,915 của nó thực ra cao hơn 0,864 của Louvain) — đúng chỗ ARI làm mờ, khoảng cách completeness 0,07 ở nơi ARI chỉ hiện 0,002."*

5. **Paper.md dòng 211** (Exp9):
   - Cũ: *"HDBSCAN tụt còn 0,929 vì gộp các ốc đảo — khoảng cách completeness 0,07..."*
   - Mới: *"HDBSCAN tụt còn 0,929 vì **xé lẻ** hai ốc đảo (dồn $\sim$36 điểm có nhãn vào bin nhiễu, tách một ốc đảo ra nhiều cụm dư) — đây là lỗi completeness đúng nghĩa, không phải homogeneity (homogeneity 0,915 của HDBSCAN còn cao hơn 0,864 của Louvain); khoảng cách completeness 0,07 ở nơi ARI chỉ hiện 0,002."*

6. **Paper.md dòng 201** (Exp4): *"HDBSCAN 0,890 nhưng gộp thành 11 cụm với đường kính 25 km"* — "gộp thành 11 cụm" mơ hồ nhưng không sai nặng; chỉnh nhẹ: *"HDBSCAN 0,890 nhưng chỉ 11 cụm, đường kính 25 km do bin nhiễu + cụm dư"* để nhất quán.

**Không đụng:** con số 0,929 / 0,915 / 0,864 / 25 km / 0,07 / 0,002 — tất cả giữ nguyên (đã khớp JSON). Chỉ sửa mệnh đề nhân-quả.

**Trạng thái:** ⏳ Thực thi ở Step 3.

---

## THỨ TỰ THỰC THI (Step 3)

1. main.tex 345 + 382.
2. BaiBao 360 + 390.
3. Paper.md 201 + 211.
4. Recompile bằng **xelatex** (fontspec — KHÔNG dùng pdflatex): `xelatex → bibtex → xelatex ×2`. Xác nhận 20 trang, 0 undefined refs.
5. Cập nhật memory loop 8.
