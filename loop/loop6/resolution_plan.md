# Loop 6 — Kế hoạch Giải quyết (Step 2)

**Vai trò:** Tác giả (khách quan). Trả lời chất vấn 6.1, đề xuất sửa cụ thể.

---

## 6.1 — "0 m offset cho cả 24 điểm" — CHẤP NHẬN, SỬA CÂU CHỮ (không đụng số/không đụng code)

**Thừa nhận:** Phản biện đúng. Kiểm tra generate.py: chỉ 6 điểm mỏ neo (k=0 mỗi nhóm) trùng tâm 0 m; 18 điểm còn lại trải 184–832 m do offset `k*0.0006…0.0008°`. Cách nói "24 narrative points sit at the same coordinates (0 m offset)" là phóng đại, không khớp dữ liệu thực. `n_colocated=6` trong exp1_G chỉ đếm mỏ neo (điều kiện `g not in seen`, ngưỡng <1 m), KHÔNG chứng minh cả 24 điểm lệch 0 m.

**Điều đúng cần giữ:** Cơ chế trần ARI vẫn vững — narrative-only ARI=1,0, all-labeled ARI=0,892 (exp1_G, đã kiểm). Lý do: mỗi nhóm kịch bản **neo tại tâm một ốc đảo và trải trong bán kính ≲0,8 km, cùng cỡ với jitter ~250 m của điểm lõi** → nằm gọn trong vùng phủ không gian của ốc đảo chủ → mọi phương pháp theo không gian buộc gộp chung → trần ARI < 1,0. Đây mới là phát biểu chính xác.

**KHÔNG sửa code/dữ liệu:** generate.py đúng như thiết kế; exp1_G `n_colocated=6` đúng (đếm mỏ neo). Chỉ sửa **câu chữ bài báo** cho khớp dữ liệu.

**Sửa cụ thể (thay "0 m offset / same coordinates / cùng tọa độ lệch 0 m" bằng mô tả "neo tại tâm ốc đảo, trải trong bán kính nhỏ ~≤0,8 km trùng vùng phủ của ốc đảo chủ"):**

1. **main.tex dòng 226** (setup): *"deliberately co-located with island centres (0 m offset)"* → *"deliberately anchored at the island centres and confined within each island's spatial footprint (≲0.8 km, comparable to the cores' own ~250 m jitter)"*.
2. **main.tex dòng 236** (exp1): *"sit at the same coordinates as the six islands"* → *"are anchored at the six island centres and lie within their spatial footprint"*; thêm mệnh đề nói vì trải trong vùng phủ nên mọi phương pháp không gian buộc gộp.
3. **BaiBao dòng 290**: *"đặt trùng tọa độ với 6 tâm ốc đảo (lệch 0 m)"* → *"neo tại 6 tâm ốc đảo và trải trong bán kính nhỏ (≤0,8 km, cùng cỡ jitter ~250 m của điểm lõi)"*.
4. **BaiBao dòng 309**: *"nằm cùng tọa độ với 6 ốc đảo"* → *"neo tại tâm 6 ốc đảo và nằm trong vùng phủ không gian của chúng"*.
5. **Paper.md dòng 193**: *"trùng tọa độ ốc đảo"* → *"neo tại tâm ốc đảo, trải trong vùng phủ"* (chỉnh ngắn).
6. **Các chỗ nhắc lại "co-located narrative labels"** (main.tex 392 limitation; BaiBao 421) — cụm "co-located" ở nghĩa "nằm trong vùng phủ ốc đảo" vẫn chấp nhận được, KHÔNG cần đổi vì không khẳng định "0 m"; chỉ đảm bảo không có "0 m offset" sót lại.

**Trạng thái:** ⏳ Thực thi Step 3.

---

## KHÔNG SỬA (đã kiểm loop 6, đúng)

- Mọi số liệu định lượng (6.2): khớp demo hoàn toàn. Không đụng.
- Trích dẫn ngoài (CrisisSpot, storm): xác minh đúng. Không đụng.
- Xref, hình, bib, placeholder (6.3): sạch. Không đụng.

---

## THỨ TỰ THỰC THI (Step 3)

1. main.tex: dòng 226 + 236 (sửa "0 m offset"/"same coordinates").
2. BaiBao_NoiDung.md: dòng 290 + 309.
3. Paper.md: dòng 193.
4. Quét lại đảm bảo không còn "0 m" / "0\,m offset" / "lệch 0 m" mô tả narrative.
5. Recompile main.tex → 0 undefined refs, số trang ổn định.
6. Cập nhật memory nếu cần (ghi phát hiện offset).
