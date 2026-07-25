# Loop 14 — Kế hoạch Giải quyết (Step 2)

**Vai trò:** Tác giả (giữ tính khách quan). Nguyên tắc loop này khác các loop trước: ở đây **JSON không phải sự thật cuối cùng** — JSON đo đúng cái mà code tính, nhưng *code tính sai thứ cần đo*. Nên phải **sửa mã trước, chạy lại, rồi mới sửa bài**. Đây đúng thẩm quyền Bước 3 của quy trình ("Chỉnh sửa mã nguồn hoặc dữ liệu trực tiếp trong @demo nếu có sai sót ảnh hưởng đến bài báo").

Thứ tự bắt buộc: **sửa `metrics.py`/`baselines.py` → chạy lại exp4 + exp9 + exp12 → cập nhật `main.tex` theo JSON mới → đồng bộ bản Việt**.

---

## 14.2b — `noise_absorbed_pct` đếm thùng nhiễu như cụm thật — CHẤP NHẬN, SỬA MÃ (ưu tiên số 1)

**Thừa nhận:** Đúng, và đây là lỗi tệ nhất trong 14 vòng. Không tranh luận gì được:

```
DBSCAN eps=0,3: thùng nhiễu (-1) chứa 128 điểm = 67 có nhãn + 61 gt=-1
  metrics.noise_handling() thấy thùng này "có điểm thật" (67 điểm) nên coi
  61 điểm gt=-1 trong đó là "bị hấp thụ vào cụm thật" → 100%
  Sự thật: nhãn -1 nghĩa là "KHÔNG thuộc cụm nào". Không có hấp thụ nào cả.
  Đúng: 0,0%
```

Bài báo dùng cột này làm bằng chứng bổ trợ ("both DBSCAN settings absorb **every** noise point"), nên lỗi này **đảo ngược dấu của một so sánh theo hướng có lợi cho chúng ta**. Không thể để nguyên dưới bất kỳ lập luận nào.

**Vì sao lỗi tồn tại:** `noise_handling()` được viết cho Louvain, nơi mọi nhãn đều là cụm thật (Louvain không sinh nhãn $-1$). Khi thêm DBSCAN/HDBSCAN vào exp4, không ai xét lại giả định đó.

**Sửa `demo/pipeline/metrics.py`:**

1. Thêm tham số `noise_label: int | None = -1` cho `noise_handling()`; **bỏ qua** nhóm có nhãn $=$ `noise_label` khi tính hấp thụ và ô nhiễm — vì các điểm trong đó **chưa được gán cụm**, đúng nghĩa ngữ nghĩa của nhãn $-1$ trong sklearn.
2. Bổ sung hai trường mới thay vì im lặng đổi nghĩa cột cũ:
   - `n_unclustered`: số điểm nằm trong thùng nhiễu (thông tin thật, đáng báo cáo).
   - `labeled_dropped_to_noise`: số điểm **có nhãn** bị đẩy vào thùng nhiễu — đây là *lỗi đối ngẫu* của hấp thụ, và là nhược điểm thật của DBSCAN (eps 0,3 đánh rơi **67** điểm có nhãn). Nhờ trường này bài báo vẫn phê phán được DBSCAN, nhưng bằng **đúng lý do**.

Điểm quan trọng về tính trung thực: sửa xong, DBSCAN **thắng** chúng ta ở cột hấp thụ nhiễu (0,0% vs 0,0% — hoà; eps 0,6 là 6,56%). Ta phải báo cáo đúng vậy, đồng thời nêu cột mới cho thấy giá phải trả của nó: **67/280 điểm có nhãn bị ném ra ngoài mọi cụm**, tức DBSCAN mua vệ sinh nhiễu bằng cách từ chối phân cụm gần một phần tư dữ liệu có nhãn — điều một hệ điều phối không chấp nhận được. Đây là lập luận mạnh hơn và **đúng**.

---

## 14.2a — Thùng nhiễu bị tính vào `n_clusters` và đường kính — CHẤP NHẬN, SỬA MÃ

**Thừa nhận:** Đúng. `geographic_spread()` gom nhãn không loại trừ $-1$, nên thùng nhiễu 128 điểm rải bốn tỉnh trở thành một "cụm" đường kính 213,69 km — và chính con số đó được bài dùng để nói DBSCAN thất bại. Con số thật: **7,75 km**.

**Sửa `demo/pipeline/metrics.py::geographic_spread`:** thêm `noise_label: int | None = -1`, tách thùng nhiễu ra khỏi mọi thống kê cụm, thêm trường `n_unclustered`. Giữ nguyên toàn bộ ba biến thể đường kính hiện có (`all`/`multi`/`weighted`) — chúng đúng, chỉ cần đầu vào đúng.

**Bảng số sau sửa (đã tính trước, sẽ được JSON xác nhận):**

| Phương pháp | số cụm | mean multi (km) | max (km) |
|---|---|---|---|
| HDBSCAN | 21 → **20** | 55,72 → **48,69** | 201,46 (không đổi) |
| DBSCAN eps 0,3 | 32 → **31** | 7,78 → **1,14** | 213,69 → **7,75** |
| DBSCAN eps 0,6 | 8 → **7** | 38,67 → **14,33** | 209,05 → **37,37** |
| Louvain/Leiden/Agglom./K-Means/Spectral | không đổi (không sinh nhãn $-1$) | | |

**Hệ quả phải viết lại trong bài — và đây là chỗ lập luận thực sự cần suy nghĩ lại, không chỉ đổi số:**

Sau sửa, **DBSCAN eps 0,3 có mean diameter 1,14 km** — cùng cỡ với 0,85 km của Louvain. Câu cũ ở dòng 441 ("both DBSCAN settings absorb every noise point") sụp hoàn toàn. Nhưng luận điểm **vẫn đứng, bằng lý do khác và tốt hơn**: DBSCAN eps 0,3 đạt đường kính nhỏ **chỉ vì nó từ chối phân cụm 128/341 điểm** (trong đó 67 điểm có nhãn) — ARI của nó vẫn chỉ **0,2391**. Tức nó không phải một đối thủ mạnh bị ta vu oan; nó đánh đổi độ phủ lấy độ gắn kết, và mất ARI. Cách trình bày đúng: DBSCAN thất bại ở **độ phủ + độ khớp nhãn**, không phải ở hình học. Câu chuyện này chặt chẽ hơn câu chuyện cũ (vốn dựa trên một artifact đo lường).

**Không đụng tới:** ARI/NMI của mọi phương pháp — `cluster_quality()` mask `gt>=0` và **không** phụ thuộc cách gom nhãn, nên toàn bộ cột ARI/NMI **giữ nguyên**. Xác nhận lại sau khi chạy.

---

## 14.1 — "raw coordinates" là nhãn sai — CHẤP NHẬN, chạy thêm và báo cáo cả hai

**Thừa nhận:** Đúng, và docstring trong `baselines.py` ("tọa độ + mức ngập + khẩn cấp") tự tố giác. Bài báo nói "purely geometric… geography alone is insufficient" trong khi baseline dùng cả $F,E$ — **kết luận không suy ra được từ thí nghiệm đã chạy**.

**Phương án — không chọn cách dễ.** Có hai lối:
- (a) Chỉ đổi nhãn thành "coords + $F$ + $E$". Rẻ, đúng, nhưng **mất** khả năng nói "geography alone is insufficient" — mà đó là một luận điểm hợp lệ và cần thiết cho bài.
- (b) **Chạy thêm** biến thể toạ độ-thuần thật, báo cáo **cả hai**, và giữ luận điểm bằng đúng dữ liệu chứng minh nó.

Chọn **(b)**. Lý do: baseline toạ độ-thuần thật đạt ARI **0,8268** (K-Means $K{=}14$) — cao hơn nhiều con số 0,5016 đang in. Báo cáo nó là **tự làm khó mình**, nhưng nó là con số đúng, và nó dẫn tới một phát hiện đáng giá hơn: **thêm $F,E$ vào không gian Euclid làm ARI TỤT từ 0,83 xuống 0,50**. Đó chính là bằng chứng mạnh nhất cho luận điểm trung tâm của bài — rằng ngữ cảnh phải vào **dạng nhân (gating)**, không phải nối thêm chiều vào metric Euclid. Ta đang có sẵn một kết quả hỗ trợ luận điểm chính mà lại đang che nó dưới một cái nhãn sai.

**Sửa `demo/pipeline/baselines.py`:** thêm tham số `features: str = "geo_context"` cho `_feature_matrix`, `run_kmeans`, `run_dbscan`; `"geo"` → chỉ `[lat, lng]`, `"geo_context"` → `[lat, lng, flood, urgency]` (mặc định giữ nguyên để không phá exp khác).

**Sửa `demo/experiments/exp4_baselines.py`:** thêm hai hàng toạ độ-thuần (`K-Means (K=14, coords only)`, `DBSCAN (eps=0.3, coords only)`) và **đổi nhãn** bốn hàng cũ thành `coords+F,E`.

**Số liệu sẽ vào bài** (đã tính, JSON sẽ xác nhận):

| | ARI | NMI | mean multi | noise abs. |
|---|---|---|---|---|
| K-Means $K{=}14$, **chỉ toạ độ** | **0,8268** | 0,8898 | 34,00 | 26,2% |
| K-Means $K{=}14$, coords+$F,E$ | 0,5016 | 0,7262 | 93,47 | (tính lại) |
| DBSCAN eps 0,3, **chỉ toạ độ** | **0,6230** | 0,8132 | 32,73 | (tính lại) |

**Viết lại dòng 441 và Abstract:** thay "geography alone is insufficient" bằng lập luận đúng — geography-thuần đạt 0,83 nhưng **vẫn kém xa 0,9957 và 34 km vs 0,85 km**; và nối $F,E$ theo dạng cộng-chiều Euclid **làm tệ đi** (0,83 → 0,50), đúng như dự đoán của bài về dạng cộng vs dạng nhân.

---

## 14.4 — Không công bố $K{=}74$ đến từ Louvain — CHẤP NHẬN, thêm một câu

**Thừa nhận:** Đúng, đây là chi tiết tái lập bắt buộc. `k_lou = len(set(run_louvain(...)))` → 74.

**Sửa `main.tex`** caption Bảng 6 + dòng 405: nói rõ *"the $K$ given to Spectral and Agglomerative is $74$, the cluster count Louvain discovers on its own — so those rows are handed our method's resolution as a free parameter; the $K{=}14$ Spectral row is given the true label count instead."* Điều này **làm yếu** vẻ độc lập của câu "Agglomerative ties Louvain exactly", nên phải nói ra.

---

## 14.3 — `needs_preset_k` bằng so khớp chuỗi — CHẤP NHẬN, sửa mã

Thay bằng cờ tường minh khai cùng lúc với định nghĩa từng baseline (dict `method → needs_k`), không suy từ tên hiển thị. Giá trị hiện tại đúng cả 10 hàng nên **không con số nào trong bài đổi** — đây là sửa để hết giòn.

---

## 14.5 — Exp9 dùng $K{=}12$, Exp4 dùng $K{=}14$ — CHẤP NHẬN, thống nhất

Đổi exp9 sang $K{=}14$ cho khớp exp4 (cùng thuật toán thì cùng tham số, nếu không phải giải thích tại sao khác). Chạy lại, cập nhật Bảng 9 và các con số spread theo JSON mới. Nếu spread thay đổi, viết lại theo số mới — **không** giữ số cũ.

---

## KHÔNG SỬA — nêu rõ để loop sau không lật lại

- **ARI/NMI mask `gt>=0`**: đúng chuẩn, đã công bố ở dòng 332, bù bằng cột hấp thụ nhiễu. Giữ.
- **$d_{ij}=1-w_{ij}/w_{\max}$** cho HDBSCAN/Agglomerative: hợp lệ, cùng thông tin đồ thị. Giữ.
- **Exp7 (`_severe_vulnerable_weight`)**: đã kiểm, ngưỡng $F>0{,}7$ thật sự không chứa $V$ lẫn `core` → tuyên bố "neutral" đúng. Giữ nguyên, không đụng.
- **Spectral `assign_labels="discretize"`**: xác định, phù hợp tuyên bố tái lập. Giữ.

---

## THỨ TỰ THỰC THI (Step 3)

1. `pipeline/metrics.py`: thêm `noise_label` cho `noise_handling` + `geographic_spread`; thêm `n_unclustered`, `labeled_dropped_to_noise`.
2. `pipeline/baselines.py`: thêm `features="geo"|"geo_context"`.
3. `experiments/exp4_baselines.py`: hai hàng toạ độ-thuần, đổi nhãn 4 hàng cũ, cờ `needs_k` tường minh.
4. `experiments/exp9_discriminative_metric.py`: $K{=}12 \to 14$.
5. Chạy lại `exp4`, `exp9`, và **`exp12`** (dùng `noise_absorbed_pct` → cột đó có thể đổi; gating không sinh nhãn $-1$ nên có thể không đổi, phải kiểm chứ không đoán). Kiểm cả `exp1` vì nó cũng gọi `noise_handling`.
6. Cập nhật `main.tex`: Bảng 6 (số cụm, đường kính, hấp thụ nhiễu, hàng mới), Bảng 9, dòng 405, 437, 441, caption Bảng 6, Abstract dòng 49, Kết luận dòng 568.
7. Đồng bộ `resource/BaiBao_NoiDung.md` + `Paper.md` theo số mới.
8. Chạy `demo/verify_figures.py`; nếu hình baseline (`fig6`) đổi thì chạy lại `make_figures.py` và copy sang `paper/figures/`.
9. Biên dịch `xelatex → bibtex → xelatex ×2`: yêu cầu 0 overfull, 0 undefined ref.

---

## NHẬT KÝ THỰC THI (Step 3 — đã hoàn tất)

| # | Việc | Trạng thái |
|---|---|---|
| 1 | `metrics.py`: `noise_label` cho `noise_handling` + `geographic_spread`; thêm `n_unclustered`, `labeled_dropped_to_noise` | ✅ |
| 2 | `baselines.py`: `features="geo" \| "geo_context"` | ✅ |
| 3 | `exp4`: 2 hàng toạ độ-thuần, đổi nhãn 4 hàng cũ → `coords+F,E`, cờ `needs_k` tường minh | ✅ |
| 4 | `exp9`: K=12→14, số cụm loại thùng nhiễu, đổi nhãn "raw"→"coords+F,E" | ✅ |
| 5 | Chạy lại exp4, exp9, exp12, exp1 | ✅ (exp12 + exp1 **không đổi**, đúng dự đoán) |
| 6 | `main.tex`: Bảng 6 (+cột Unclust., 2 hàng mới), Bảng 9, §Metrics, dòng 405/440/449/496, caption Hình 6, Abstract, Kết luận | ✅ |
| 7 | Đồng bộ `BaiBao_NoiDung.md` + `Paper.md` | ✅ |
| 8 | `make_figures.py` → fig6 đổi → copy sang `paper/figures/`; `verify_figures.py` PASS | ✅ |
| 9 | Biên dịch xelatex×2 + bibtex: **0 overfull, 0 undefined, 0 multiply-defined**, 26 trang | ✅ |

**Số liệu đã đổi trong bài (tất cả truy về JSON mới):**

| | Cũ (sai) | Mới (đúng) |
|---|---|---|
| HDBSCAN số cụm / mean diam | 21 / 55,72 km | **20 / 48,69 km** |
| DBSCAN eps 0,3 số cụm / mean / max | 32 / 7,78 / 213,69 km | **31 / 1,14 / 7,75 km** |
| DBSCAN eps 0,3 hấp thụ nhiễu | 100% | **0,0%** (+67 điểm có nhãn bị ném vào thùng nhiễu) |
| DBSCAN eps 0,6 số cụm / mean / max | 8 / 38,67 / 209,05 km | **7 / 14,33 / 37,37 km** |
| DBSCAN eps 0,6 hấp thụ nhiễu | 100% | **6,56%** |
| K-Means toạ-độ-thuần | (không tồn tại) | **ARI 0,8268**, 34,00 km |
| K-Means H/C (exp9) | 0,7466 / 0,7293 | **0,7681 / 0,6887** (do K 12→14) |

**Không đổi (đã xác nhận, không phải bỏ qua):** toàn bộ cột ARI/NMI; mọi số của Louvain/Leiden/Agglomerative/Spectral/K-Means; exp1; exp12; các độ trải của exp9.

**Lập luận đã viết lại (không chỉ đổi số):** phê phán DBSCAN chuyển từ "hấp thụ toàn bộ nhiễu" (artifact đo lường) sang "từ chối phân cụm 128/341 điểm, ném 67 điểm có nhãn ra ngoài, ARI vẫn 0,2391" (đúng dữ liệu, và mạnh hơn). Phê phán baseline Euclid chuyển từ "geography alone is insufficient" (sai) sang "toạ độ-thuần mạnh thật (0,8268) nhưng nối thêm $F,E$ vào không gian Euclid làm TỆ ĐI (0,8268→0,5016) — bằng chứng trực tiếp cho luận điểm ngữ cảnh phải vào dạng NHÂN".
