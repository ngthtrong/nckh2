# Loop 17 — Kế hoạch Giải quyết (Step 2)

**Vai trò:** Tác giả. Nguyên tắc loop này: **mọi con số trong bài phải truy được về một trường trong JSON hoặc một hằng số trong mã.** Một con số không truy được thì không phải "sai một chút" — nó là con số **không ai kiểm chứng được**, và với một bài báo tuyên bố tái lập tuyệt đối thì đó là lỗi nặng hơn một sai số.

Thứ tự bắt buộc: **sửa/mở rộng mã sinh dữ liệu → sinh lại `dataset.json` → xác nhận sự kiện không đổi → sửa bài theo số truy được → đồng bộ bản Việt**.

---

## 17.1 — Con số "923 m" không truy được về đâu — CHẤP NHẬN, SỬA (ưu tiên số 1)

**Thừa nhận:** Đúng, và đây là lỗi tệ nhất của loop này vì nó đánh trực diện vào tuyên bố Reproducibility. Bằng chứng: chuỗi `923` xuất hiện **15 lần** trong ba artifact (`main.tex` 4, `Paper.md` 5, `BaiBao_NoiDung.md` 6) nhưng **không tồn tại** trong `demo/` dưới dạng một khoảng cách nào cả (các lần khớp trong `demo/` đều là trùng hợp chữ số trong timestamp/lat/ARI). Đo thực tế trên chính `dataset.json`:

| Đại lượng | Giá trị |
|---|---|
| Hằng số thiết kế `S5_GAP_M` | **900,0 m** |
| Khoảng cách trọng tâm–trọng tâm S5A↔S5B | **900,8 m** |
| Khoảng cách cặp điểm **nhỏ nhất** giữa hai nhóm | **696,8 m** |
| Khoảng cách cặp điểm trung bình | 913,0 m |
| Khoảng cách cặp điểm lớn nhất | 1265,5 m |
| "923 m" của bài | **không khớp cái nào** |

Đáng chú ý: 923 gần nhất với trung bình cặp điểm (913,0) — có thể là số của một phiên bản generator trước (khi `jitter_m` hoặc `step_m` khác), tức nó là **tàn tích của dữ liệu cũ**, đúng loại lỗi mà loops 9–10 đã dọn ở chỗ khác nhưng bỏ sót ở đây.

**Sửa — chọn số nào và tại sao.** Đại lượng đúng cho mệnh đề *"cặp S5 cách nhau X mà Louvain gộp"* là khoảng cách giữa **hai nhóm**, tức trọng tâm–trọng tâm: **900,8 m** ≈ hằng số thiết kế **900 m**. Không dùng min-pairwise (696,8 m) làm số chính vì nó nói về hai *điểm* gần nhau nhất, không phải khoảng cách giữa hai *nhóm* — nhưng phải **báo cáo kèm**, vì chính nó giải thích tại sao gating gộp: điểm gần nhất của hai nhóm chỉ cách 696,8 m, **nằm trong** $\sigma_{geo}=700$ m.

Viết vào bài: "$900$\,m apart (design constant `S5_GAP_M`; measured centroid separation $900.8$\,m, closest cross-group pair $696.8$\,m --- inside $\sigma_{geo}=700$\,m)". Ba con số, cả ba truy được.

**Phòng ngừa tái diễn:** phát các đại lượng này ra `dataset.json` → `meta` (`s5_centroid_distance_m`, `s5_min_pairwise_m`, `s5_max_pairwise_m`) để lần sau reviewer đọc được thẳng từ file thay vì phải tự tính. Đây là lý do gốc khiến 923 sống được 16 vòng: **không có trường nào để đối chiếu.**

---

## 17.2 — Chú thích trong generator tự mâu thuẫn — CHẤP NHẬN, sửa

`data/generate.py`:
```
# Khoảng cách giữa hai nhóm S5 (mét). Chọn 900 m: nhỏ so với sigma_geo = 700 m nên
```
$900 > 700$, nên "900 m nhỏ so với 700 m" là **sai về mặt số học**. Ý định thật (và đúng) là: ở khoảng cách này $\mathcal{S}_{geo}$ **vẫn còn đáng kể** ($0{,}4369$, khớp "≈0,44" của bài ✓) nên cổng địa lý một mình **không** tách được hai nhóm — chỉ $\mathcal{S}_{context}$ tách được. Sửa chú thích cho khớp cơ chế thật, và nêu luôn con số min-pairwise 696,8 m vì đó mới là lý do trực tiếp khiến hai nhóm bị gộp.

**Không đổi giá trị `S5_GAP_M`.** Đây chỉ là lỗi diễn đạt trong chú thích; hình học hiện tại đang phục vụ đúng mục đích thiết kế (tạo một ca mà chỉ ngữ cảnh tách được). Đổi số sẽ làm toàn bộ số liệu 16 vòng phải chạy lại mà không sửa được lỗi nào.

---

## 17.3 — `assert_gt_separable` không kiểm những gì bài nói nó kiểm — CHẤP NHẬN, mở rộng mã + sửa bài

**Thừa nhận:** Đúng, và đây là lỗi *tuyên bố vượt quá bảo đảm*. Bài (§Threats) viết:

> "asserts a $2$\,km minimum separation, so---unlike the earlier version of this dataset---**no label is co-located with another**"

Hàm thực tế chỉ kiểm **một** quan hệ: điểm kịch bản (gt ≥ 100) ↔ **tâm** ốc đảo lõi. Nó **không** kiểm:
- điểm kịch bản ↔ **điểm** lõi thực tế (khoảng cách thật nhỏ hơn: **2262,6 m** vs 2846,1 m tới tâm — vẫn đạt ngưỡng, nhưng không được kiểm);
- **kịch bản ↔ kịch bản** — và đây mới là chỗ chí tử: cặp gt=106/107 cách nhau **696,8 m**, tức **dưới xa** ngưỡng 2000 m mà câu trên viện dẫn. Nếu hàm có kiểm quan hệ này thì nó đã **raise** ngay khi sinh dữ liệu.

Nói cách khác: câu "no label is co-located with another" **không đúng** với chính bộ dữ liệu đang dùng, và nó không đúng **một cách có chủ ý** — S5 được thiết kế để hai nhãn nằm sát nhau. Vấn đề là bài trình bày một khẳng định phổ quát trong khi thực tế có **một ngoại lệ được thiết kế**, và chính ngoại lệ đó là nguồn duy nhất của khoảng cách ARI $0{,}0043$.

**Sửa mã — mở rộng thành ba kiểm với một ngoại lệ khai tường minh:**
1. kịch bản ↔ tâm ốc đảo (giữ nguyên);
2. kịch bản ↔ **mọi điểm lõi** (mới);
3. **mọi cặp nhãn GT khác nhau** ↔ nhau (mới), với **một allow-list duy nhất** `{(106, 107)}` kèm chú thích nêu rõ đây là ca thiết kế để buộc $\mathcal{S}_{context}$ phải làm việc.

Cách này biến ngoại lệ từ *chỗ hàm không nhìn tới* thành *chỗ hàm ghi nhận và cho phép có lý do*. Trả về cả khoảng cách nhỏ nhất của từng loại kiểm để phát vào `meta`.

**Sửa bài (§Threats):** thay khẳng định phổ quát bằng phát biểu đúng: generator kiểm ba quan hệ và cho phép **đúng một** ngoại lệ khai trước (S5, 696,8 m cặp gần nhất), và ngoại lệ đó **chính là** toàn bộ khoảng cách $0{,}0043$ tới ARI hoàn hảo. Điều này *mạnh hơn* câu cũ: nó nói được chính xác nguồn của mọi sai số còn lại, thay vì một lời bảo đảm mà dữ liệu không thoả.

---

## 17.4 — `dataset-backup.json` là artifact chết của bộ dữ liệu đã bị thay thế — CHẤP NHẬN, xóa

285 sự kiện / 6 nhãn GT — đúng bộ dữ liệu cũ mà loops 9–10 đã kết luận là lỗi thời. Không file nào trong repo tham chiếu tới nó (đã grep). Rủi ro: một reviewer hoặc một lần chạy lại nhầm file sẽ tái sinh toàn bộ số liệu sai mà loops 9–10 vừa dọn. Xóa.

**Không** giữ lại "cho chắc": lịch sử git đã lưu nó, và một file dữ liệu lỗi thời nằm cạnh file đang dùng là bẫy, không phải bản lưu.

---

## 17.5 — Xác nhận (KHÔNG phải lỗi, ghi lại để loop sau không đào lại)

- **`dataset.json` khớp `make_events(42)` từng toạ độ** (0/341 lệch) → dữ liệu trên đĩa đúng là dữ liệu mã sinh ra, không phải bản chỉnh tay.
- **Đúng một cụm dự đoán chứa nhiều hơn một nhãn GT**: cụm 10 = {106, 107}; **không nhãn GT nào bị xé** qua nhiều cụm. Khớp chính xác mệnh đề "đúng một cặp bị gộp" của bài ✓.
- $\mathcal{S}_{geo}$ tại khoảng cách trọng tâm S5 = **0,4369** ✓ khớp "≈0,44" của bài.
- S1: 106,74 km đo được / 106,76 km trong `meta` / "106,8 km" trong bài — chỉ là làm tròn, **không phải lỗi**. Giữ.
- Sáu ốc đảo lõi cách nhau gần nhất 17,18 km ≫ spread 250 m → lõi khả tách thật, ARI lõi $=1{,}0$ không phải do trùng lặp.
- `SAT_OFFSET_M` cho S4A đo được 2999,5 m (khai 3000) — sai số của xấp xỉ phẳng cục bộ trong `_offset`, dưới 0,02%. Không đáng sửa.

---

## THỨ TỰ THỰC THI (Step 3)

1. `data/generate.py`: sửa chú thích `S5_GAP_M` (17.2).
2. `data/generate.py`: mở rộng `assert_gt_separable` thành ba kiểm + allow-list `{(106,107)}`; trả về khoảng cách nhỏ nhất từng loại (17.3).
3. `data/generate.py`: phát `s5_centroid_distance_m`, `s5_min_pairwise_m`, `s5_max_pairwise_m` và các trường của kiểm mới vào `meta` (17.1).
4. Sinh lại `dataset.json`; **xác nhận 341 sự kiện khớp từng toạ độ** với bản trước (chỉ `meta` được phép đổi).
5. Xóa `data/dataset-backup.json` (17.4).
6. `main.tex`: thay mọi "923 m" (4 chỗ) bằng số truy được; sửa §Threats theo 17.3.
7. Đồng bộ `resource/BaiBao_NoiDung.md` (6 chỗ) + `resource/Paper.md` (5 chỗ).
8. Chạy `verify_figures.py`; biên dịch `xelatex ×2` + bibtex: yêu cầu 0 overfull, 0 undefined, 0 multiply-defined.
9. Chạy lại một thí nghiệm bất kỳ (exp1) để chắc `meta` mới không phá đường đọc dữ liệu.
