# Loop 17 — Báo cáo Phản biện (Step 1)

**Vai trò:** Giáo sư chủ tịch hội đồng phản biện. Loop 14 soi phương pháp đo baseline, loop 15 soi hàm ưu tiên, loop 16 soi tính công bằng của làm thưa. Cả ba đều soi *phần xử lý*. Loop 17 đi xuống tầng cuối cùng chưa ai chạm: **bộ sinh dữ liệu** — `demo/data/generate.py` và `demo/data/dataset.json`.

Đây là tầng quan trọng nhất còn lại vì **mọi con số trong bài đều là hàm của nó**. Nếu bộ sinh sai, không phép đo nào ở trên cứu được. Câu hỏi trung tâm: *những con số bài báo dùng để mô tả hình học dữ liệu có thật sự lấy được từ dữ liệu không?*

Phương pháp: nạp trực tiếp `dataset.json`, tính lại từng đại lượng hình học mà bài viện dẫn, và đối chiếu với hằng số trong mã.

---

## CHẤT VẤN 17.1 — Con số "923 m" xuất hiện **15 lần** trong ba artifact nhưng **không tồn tại trong dữ liệu** (NGHIÊM TRỌNG)

Bài báo dùng "cặp S5 cách nhau $923$ m" làm **lời giải thích trung tâm** cho việc ARI là $0{,}9957$ chứ không $1{,}0$. Con số này xuất hiện ở:

| Artifact | Số lần |
|---|---|
| `paper/main.tex` | 4 |
| `resource/Paper.md` | 5 |
| `resource/BaiBao_NoiDung.md` | 6 |

Nó gánh nhiều trọng lượng lập luận: §Exp1 (giải thích khoảng cách tới ARI hoàn hảo), §Exp4 (vì sao HDBSCAN tách được mà Louvain không), §Exp6 (vì sao $\mathcal{S}_{context}$ có giá trị ở $\beta=0{,}9$), và §Threats (vì sao sd ARI $=0{,}0000$).

**Tôi đã tính lại mọi định nghĩa khoảng cách hợp lý giữa hai nhóm S5 từ chính `dataset.json`:**

| Đại lượng | Giá trị đo được |
|---|---|
| Khoảng cách **trọng tâm–trọng tâm** | **900,8 m** |
| Khoảng cách **cặp điểm gần nhất** | **696,8 m** |
| Khoảng cách cặp điểm **trung bình** | 913,0 m |
| Khoảng cách cặp điểm **xa nhất** | 1265,5 m |
| Hằng số `S5_GAP_M` trong mã | **900,0 m** |
| `meta.s5_gap_m` trong `dataset.json` | **900,0** |

**Không một giá trị nào bằng 923 m.** Tôi cũng đã grep toàn bộ `demo/` (mã + JSON): số 923 **không xuất hiện** ở bất kỳ trường kết quả nào — chỉ khớp ngẫu nhiên trong vài chuỗi timestamp và toạ độ không liên quan.

**Vì sao đây là lỗi nghiêm trọng chứ không phải làm tròn:** phần Reproducibility (dòng 613) tuyên bố "each number reported here **traces to a field in those files**" và "a reviewer re-running the suite obtains **identical values**". Một reviewer đi tìm 923 m sẽ không tìm được nó ở đâu — không trong JSON, không trong mã, không tính lại được từ dữ liệu. Con số gần nhất là 900 m (hằng số thiết kế) và 900,8 m (đo được). Chênh lệch 2,5% thì nhỏ, nhưng vấn đề không phải độ lớn: **một con số không truy nguyên được, lặp 15 lần, trong vai trò giải thích trung tâm** là đúng loại lỗi mà tuyên bố tái lập tồn tại để loại bỏ.

Ghi chú thêm: bài cũng viết $\mathcal{S}_{geo}\approx0{,}44$ cho cặp này. Tính tại 900,8 m cho **0,4369** ✓ — tức con số $\mathcal{S}_{geo}$ *đúng* và nó được tính từ **900,8 m**, không phải từ 923 m. Chính điều này chứng minh 923 m là số dư thừa từ một phiên bản dữ liệu trước, không phải giá trị hiện hành.

---

## CHẤT VẤN 17.2 — Chú thích trong mã **tự mâu thuẫn** về chính hằng số nó định nghĩa (TRUNG BÌNH)

`demo/data/generate.py`, ngay trên `S5_GAP_M`:

> `# Khoảng cách giữa hai nhóm S5 (mét). Chọn 900 m: nhỏ so với sigma_geo = 700 m nên`
> `# S_geo giữa hai nhóm vẫn đáng kể (~0.44) => CHỈ có S_context mới tách được chúng.`

**900 không "nhỏ so với" 700 — nó lớn hơn.** Ý định thì đúng (900 m nằm trong tầm ảnh hưởng của cổng Gaussian $\sigma_{geo}=700$ m, nên $\mathcal{S}_{geo}=0{,}44$ vẫn đáng kể), nhưng câu chữ nói ngược. Đây là chú thích giải thích **lý do thiết kế** của điểm dữ liệu quan trọng nhất trong bộ, nên diễn đạt sai ở đây làm người đọc mã hiểu sai cơ chế. Không ảnh hưởng số liệu.

---

## CHẤT VẤN 17.3 — Bài báo khai `assert_gt_separable` mạnh hơn thực tế nó kiểm (TRUNG BÌNH–NGHIÊM TRỌNG)

`main.tex` dòng 623 khẳng định:

> "The generator … asserts a $2$\,km minimum separation, so … **no label is co-located with another** and no ARI ceiling is imposed by construction"

Đọc mã `assert_gt_separable` thì phạm vi kiểm **hẹp hơn nhiều** so với câu đó:

```python
for e in events:
    if e.gt_cluster is None or e.gt_cluster < 100:   # chỉ điểm kịch bản
        continue
    dmin = min(haversine_m(e.lat, e.lng, cl[0], cl[1]) for cl in centers)  # chỉ TÂM ốc đảo
```

Ba khoảng trống, đo bằng số:

| Cặp được kiểm? | Khoảng cách nhỏ nhất thực tế | Có bị chặn? |
|---|---|---|
| Điểm kịch bản → **tâm** ốc đảo | 2846,1 m (`S3_3`) | ✅ được kiểm |
| Điểm kịch bản → **điểm** lõi thật | **2262,6 m** (`S3_3`) | ❌ **không kiểm** |
| Kịch bản → kịch bản (gt 106 vs 107) | **696,8 m** | ❌ **không kiểm** |

Điểm thứ ba là điểm quyết định: **chính cặp nhãn mà bài thừa nhận bị gộp (106–107) nằm ở 696,8 m — thấp hơn hẳn ngưỡng 2 km — và assertion không bao giờ nhìn tới nó.** Nên câu "no label is co-located with another" **không** phải điều assertion bảo đảm; nó chỉ bảo đảm "không nhãn kịch bản nào nằm sát *tâm ốc đảo lõi*".

Điều này không làm số liệu sai — bài **đã** báo cáo trung thực rằng cặp S5 bị gộp. Nhưng nó làm sai lệch **điều assertion chứng minh**, và assertion đó lại được viện dẫn ở phần Threats như một bảo đảm về tính không-áp-trần của dữ liệu. Phát biểu đúng phải hẹp hơn: assertion chặn *đúng một* chế độ lỗi (nhóm kịch bản trùng tâm ốc đảo — lỗi của phiên bản dữ liệu trước), và cặp S5 sát nhau là **cố ý** để $\mathcal{S}_{context}$ có việc làm, không phải sơ suất mà assertion bỏ lọt.

---

## CHẤT VẤN 17.4 — `dataset-backup.json` là artifact mồ côi của bộ dữ liệu đã bị thay thế (TRUNG BÌNH)

`demo/data/` chứa hai file:

| File | Sự kiện | Nhãn GT | Được tham chiếu ở đâu? |
|---|---|---|---|
| `dataset.json` | 341 | 14 | ✅ `common.py` |
| `dataset-backup.json` | **285** | **6** | ❌ **không nơi nào** |

Tôi đã grep toàn repo: **không mã nào, không script nào đọc file backup**. Nó là bản chụp của **bộ dữ liệu 285-sự-kiện/6-nhãn** mà loops 9–10 đã xác định là lỗi thời và đã đồng bộ toàn bộ artifact ra khỏi. 260/341 toạ độ vẫn khớp nên nó dễ bị nhầm là bản hợp lệ.

Rủi ro cụ thể: một reviewer (hoặc một vòng lặp sau) mở `data/` thấy hai dataset, không có gì trong tên file nói cái nào là hiện hành, và bản backup mang **đúng bộ số mà 10 vòng trước đã dọn khỏi bài**. Đây chính là loại tồn đọng mà loop 13 đã bắt được với `fig7` — cùng một chế độ lỗi, ở tầng dữ liệu.

---

## CHẤT VẤN 17.5 — Khoảng cách S1 in $106{,}8$ km, đo được $106{,}74$ km, meta ghi $106{,}76$ (NHỎ)

Ba con số cho cùng một đại lượng:

| Nguồn | Giá trị |
|---|---|
| `main.tex` (4 chỗ) | $106{,}8$ km |
| Đo lại từ `dataset.json` (trọng tâm) | **106,74 km** |
| `meta.s1_pair_distance_km` | **106,76** |

Làm tròn $106{,}74 \to 106{,}8$ là hợp lệ. Nhưng `meta` ghi 106,76 trong khi tính trọng tâm cho 106,74 — hai giá trị **cùng nằm trong dataset** lệch nhau. Nhỏ, nhưng cần một định nghĩa duy nhất.

---

## ĐÃ KIỂM — KHÔNG PHẢI LỖI (giữ nguyên, ghi để loop sau không mất công)

- **`dataset.json` khớp `make_events(42)` tuyệt đối**: 341/341 sự kiện, **0 toạ độ lệch**. Bộ sinh thật sự tất định theo seed ✓ — tuyên bố tái lập ở tầng này đúng.
- **Thành phần dữ liệu khớp bài**: 240 lõi + 60 nhiễu + 41 kịch bản $=$ **341**; 14 nhãn GT; 61 điểm `gt=-1`; **23** tin giả, tất cả đều `gt=-1` (không tin giả nào mang nhãn thật) ✓ khớp §Exp8.
- **Chỉ đúng một cụm dự đoán chứa nhiều nhãn GT**: cụm 10 chứa {106, 107}. **Không** nhãn GT nào bị xé sang nhiều cụm. Tức mô tả "duy nhất một cặp bị gộp, không có over-segmentation" **chính xác** ✓ — và điều này xác nhận `completeness = 1,0` ở Bảng 9 là thật, không phải artifact.
- **Sáu ốc đảo lõi tách biệt tốt**: cặp gần nhất (đảo 0–4) cách **17,18 km**, so với `spread_m = 250` m nội cụm. Không ốc đảo nào chồng lấn ✓.
- **Vệ tinh S4A/S4B đặt bằng toạ độ chéo 2121 m** cho độ dịch $\sqrt{2}\cdot2121 = 2999{,}5$ m $\approx$ `SAT_OFFSET_M` ✓ — thủ pháp hợp lệ, không phải sai số.
- **Độ lệch chuẩn nội cụm $F$/$E$ = 0,16/0,18**: đủ rộng để phân bố ngữ cảnh các ốc đảo chồng lấn, nên $\mathcal{S}_{context}$ không phải hàm của nhãn không gian. Đây là thiết kế **chống** một dạng vòng tròn, và nó đúng ✓.
- **Toàn bộ ngẫu nhiên qua `np.random.default_rng(seed)`**, không `Date.now()`, không `random` toàn cục ✓.

---

## TỔNG KẾT STEP 1

1. **17.1** — "923 m" lặp **15 lần** trong ba artifact nhưng **không truy nguyên được**: đo lại cho 900,8 m (trọng tâm) / 696,8 m (cặp gần nhất), hằng số mã là 900,0. Chính $\mathcal{S}_{geo}=0{,}4369$ mà bài in lại được tính từ **900,8 m**, chứng tỏ 923 m là số dư của phiên bản dữ liệu trước. Vi phạm trực tiếp tuyên bố "each number traces to a field". **NGHIÊM TRỌNG.**
2. **17.3** — Bài khai `assert_gt_separable` bảo đảm "no label is co-located with another", nhưng assertion **không** kiểm cặp kịch bản–kịch bản (nơi có 696,8 m) lẫn kịch bản–điểm lõi (2262,6 m). Điều nó thật sự chặn hẹp hơn nhiều. **TRUNG BÌNH–NGHIÊM TRỌNG.**
3. **17.4** — `dataset-backup.json` (285 sự kiện / 6 nhãn) là artifact mồ côi của bộ dữ liệu đã bị thay thế, không mã nào đọc, mang đúng bộ số mà 10 vòng trước đã dọn. **TRUNG BÌNH.**
4. **17.2** — Chú thích `S5_GAP_M` nói "900 m nhỏ so với sigma_geo = 700 m" — ngược. **TRUNG BÌNH** (chỉ tài liệu mã).
5. **17.5** — S1: bài in 106,8 km, đo 106,74 km, meta ghi 106,76. **NHỎ.**
