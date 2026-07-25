# Loop 14 — Báo cáo Phản biện (Step 1)

**Vai trò:** Giáo sư chủ tịch hội đồng phản biện. Loops 9–13 đã dọn: số liệu ↔ JSON (9), đồng bộ bản Việt (10), công thức ↔ mã (11), học thuật vụ/trích dẫn (12), hình vẽ và caption (13).

Loop 14 soi tầng chưa ai chạm và là tầng nguy hiểm nhất còn lại: **tính công bằng và tính đúng nhãn của phần so sánh baseline**. Câu hỏi trung tâm không phải "con số có khớp JSON không" (loop 9 đã trả lời: khớp), mà **"con số đó có đo đúng cái mà bài báo nói nó đo không?"** Một bảng baseline có thể khớp JSON tuyệt đối mà vẫn vô giá trị nếu nhãn cột mô tả sai thí nghiệm đã chạy.

Phạm vi: `demo/pipeline/baselines.py`, `metrics.py`, `demo/experiments/exp4_baselines.py`, `exp9_*`, và các đoạn tương ứng trong `main.tex`.

---

## CHẤT VẤN 14.1 — "K-Means / DBSCAN on **raw coordinates**" là **NHÃN SAI**: code đưa vào cả $F$ và $E$ (NGHIÊM TRỌNG)

**Bài báo khẳng định (4 chỗ):**
- Abstract dòng 49: *"while K-Means ($0.502$) and DBSCAN ($0.523$) **on raw coordinates** trail badly"*
- Dòng 405: *"alongside **purely geometric** baselines (K-Means, DBSCAN **on raw coordinates**)"*
- Dòng 441: *"The **purely geometric** baselines **on raw coordinates** confirm that **geography alone** is insufficient"*
- Bảng 6, dòng 422–425: bốn hàng gắn nhãn `coords`

**Sự thật trong `pipeline/baselines.py`:**
```python
def _feature_matrix(events):
    """Đặc trưng cho baseline: tọa độ + mức ngập + khẩn cấp (đã chuẩn hóa)."""
    raw = np.array([[ev.lat, ev.lng, ev.flood, ev.urgency] for ev in events])
    return StandardScaler().fit_transform(raw)
```
**Bốn** đặc trưng, không phải hai. `run_kmeans` và `run_dbscan` đều gọi `_feature_matrix`. Chính docstring của hàm nói rõ "tọa độ + mức ngập + khẩn cấp" — **code tự thừa nhận điều mà bài báo phủ nhận**.

**Vì sao đây là lỗi nghiêm trọng, không phải chuyện chữ nghĩa:**

Cả lập luận của Mục 4 dựa trên nhãn này. Câu *"geography alone is insufficient"* chỉ có nghĩa nếu baseline **thật sự chỉ dùng geography**. Nhưng baseline đã dùng geography **cộng chính hai thuộc tính ngữ cảnh** ($F$, $E$) mà phương pháp đề xuất dùng trong $\mathcal{S}_{context}$. Vậy bài báo đang lấy một baseline **dùng cùng bộ thông tin** rồi gán cho nó cái nhãn "chỉ dùng geography" để rút ra kết luận về việc geography không đủ. **Kết luận không suy ra được từ thí nghiệm đã chạy.**

**Tệ hơn — nhãn sai làm baseline yếu đi, tức có lợi cho bài báo.** Tôi chạy lại cả hai cấu hình:

| Cấu hình | ARI | NMI | mean multi (km) | noise abs. |
|---|---|---|---|---|
| K-Means $K{=}14$, **4 đặc trưng** (code hiện tại, bài in 0,5016) | **0,5016** | 0,7262 | 93,47 | 91,8% |
| K-Means $K{=}14$, **chỉ toạ độ** (đúng như nhãn) | **0,8268** | 0,8898 | 34,00 | 26,2% |
| DBSCAN eps 0,3, **4 đặc trưng** (bài in 0,2391) | 0,2391 | 0,6570 | 7,78 | 100% |
| DBSCAN eps 0,3, **chỉ toạ độ** | **0,6230** | 0,8132 | 32,73 | 18,0% |

Baseline "chỉ toạ độ" **thật** mạnh hơn hẳn: K-Means nhảy từ 0,50 lên **0,83**, DBSCAN từ 0,24 lên **0,62**. Nghĩa là bài báo đang báo cáo phiên bản **yếu hơn** của baseline dưới một cái nhãn khiến nó trông như phiên bản đơn giản nhất có thể. Việc thêm $F,E$ vào không gian Euclid **làm hỏng** cụm không gian (StandardScaler đặt $F,E$ ngang hàng với lat/lng nên hai chiều ngữ cảnh xé nát các ốc đảo) — đó là một phát hiện thú vị, nhưng phải được **gọi đúng tên**, không được ẩn dưới nhãn "raw coordinates".

**Câu hỏi gay gắt:** Một phản biện mở `baselines.py` sẽ thấy dòng docstring tiếng Việt nói thẳng "tọa độ + mức ngập + khẩn cấp", đối chiếu với câu "purely geometric… geography alone" trong bài, và kết luận tác giả **hoặc không đọc code của mình, hoặc chọn nhãn có lợi**. Cả hai đều chí tử. Phải sửa: hoặc đổi nhãn cho đúng bốn đặc trưng, hoặc chạy thêm hàng toạ độ-thuần và báo cáo cả hai.

---

## CHẤT VẤN 14.2 — Thùng nhiễu của HDBSCAN bị đếm như một "cụm", làm sai lệch mọi con số hình học của nó (NGHIÊM TRỌNG về phương pháp đo)

**Bài báo khẳng định** (dòng 437, 49, 434, 568): *"its **21 clusters** have a **mean multi-member diameter of 55.72 km**"*.

**Sự thật (chạy lại `run_hdbscan_on_graph`):**
```
HDBSCAN trả về 21 nhãn phân biệt, TRONG ĐÓ có nhãn -1 (thùng nhiễu) chứa 7 điểm
đường kính thùng nhiễu (-1): 196,30 km   ← bị tính như một cụm bình thường
n_singletons: 0
```
`geographic_spread()` trong `metrics.py` gom nhãn bằng `groups.setdefault(lab, [])` — **không có ngoại lệ nào cho nhãn $-1$**. Nên với HDBSCAN (và DBSCAN, những thuật toán dùng $-1$ làm "không thuộc cụm nào"), thùng nhiễu được:
1. **Đếm vào `n_clusters`** → "21 clusters" thực chất là **20 cụm + 1 thùng nhiễu**.
2. **Tính đường kính như một cụm** → thùng nhiễu 196,30 km bị trộn vào trung bình.

Loại bỏ đúng thùng nhiễu:

| | bài báo in | tính đúng (loại thùng $-1$) |
|---|---|---|
| số cụm | 21 | **20** |
| mean multi-member diam. | 55,72 km | **48,69 km** |
| max diam. | 201,46 km | 201,46 km (không đổi) |

**Điều then chốt về hướng của sai số:** phép sửa này **có lợi cho HDBSCAN** (55,72 → 48,69 km), tức bài báo đang **phóng đại nhược điểm của đối thủ**. Đây là thiên vị theo hướng có lợi cho phương pháp đề xuất — chính loại lỗi mà quy trình phản biện phải bắt, và nặng hơn một sai số vô hướng.

**Điểm bào chữa duy nhất và phải nói rõ:** kết luận **định tính không đổi** — 48,69 km vẫn lớn hơn 0,85 km của Louvain **57 lần**, và cụm xấu nhất 201,46 km (một cụm thật, nhãn 14, 28 điểm) không liên quan tới thùng nhiễu. Nên luận điểm "HDBSCAN không dùng được để điều phối" vẫn đứng. Nhưng con số phải đúng, và **cách đếm phải nhất quán**: `metrics.py` đã có chú thích rất cẩn thận về việc singleton làm sai lệch trung bình mà lại bỏ qua đúng cái bẫy tương tự ở thùng nhiễu.

**Hệ quả lan sang DBSCAN — và ở đây thì NẶNG HƠN NHIỀU.** Kiểm cả hai cấu hình DBSCAN:

| | bài báo in | tính đúng (thùng $-1$ = "chưa gán cụm") |
|---|---|---|
| DBSCAN eps 0,3: số cụm | 32 | **31** (+1 thùng nhiễu chứa **128** điểm) |
| DBSCAN eps 0,3: mean multi diam. | 7,78 km | **1,14 km** |
| DBSCAN eps 0,3: max diam. | 213,69 km | **7,75 km** |
| DBSCAN eps 0,6: số cụm | 8 | **7** (+1 thùng nhiễu chứa **64** điểm) |
| DBSCAN eps 0,6: mean multi diam. | 38,67 km | **14,33 km** |
| DBSCAN eps 0,6: max diam. | 209,05 km | **37,37 km** |

Thùng nhiễu của DBSCAN eps 0,3 chứa **128/341 điểm** rải khắp bốn tỉnh, nên khi bị tính như một cụm nó tạo ra một "cụm" đường kính 213,69 km — **chính là con số max-diameter mà bài báo dùng để nói DBSCAN thất bại**. Con số thật là **7,75 km**, nhỏ hơn **27 lần**.

**Và lỗi nghiêm trọng nhất của cả loop nằm ở cột `noise_absorbed_pct`:**

```
DBSCAN eps=0,3: thùng nhiễu chứa 128 điểm = 67 điểm CÓ NHÃN + 61 điểm gt=-1
   → tất cả 61 điểm gt=-1 nằm trong thùng nhiễu
   → metric hiện tại coi thùng nhiễu là "một cụm có chứa điểm thật"
     (vì nó cũng chứa 67 điểm có nhãn) → đếm cả 61 điểm là "bị hấp thụ"
   → báo cáo 100,0%
   → SỰ THẬT: DBSCAN không hấp thụ điểm nhiễu nào vào cụm thật cả. Đúng = 0,0%
```

Bài báo dòng 441 viết: *"both DBSCAN settings absorb **every** noise point"* — và Bảng 6 in **100%** cho cả bốn hàng DBSCAN + Spectral $K{=}14$ + K-Means. Với DBSCAN eps 0,3, con số đúng là **0,0%**; với eps 0,6 là **6,56%**. Nói cách khác: **DBSCAN vệ sinh nhiễu tốt hơn cả phương pháp đề xuất trên chỉ số này** (nó ném nhiễu vào thùng $-1$ đúng như thiết kế), nhưng bài báo báo cáo nó là **tệ nhất có thể**.

Đây là lỗi tệ nhất tìm được trong 14 vòng: nó **đảo ngược hoàn toàn dấu của một so sánh**, theo hướng có lợi cho bài báo, ở đúng cột mà bài dùng làm bằng chứng bổ trợ cho ưu thế "vệ sinh nhiễu" của gating.

---

## CHẤT VẤN 14.3 — `needs_preset_k` gán nhãn bằng **so khớp chuỗi**, cho kết quả sai về mặt logic (TRUNG BÌNH)

`exp4_baselines.py` dòng 63:
```python
"needs_preset_k": ("K-Means" in name or "K=" in name),
```
Cờ "phương pháp này có cần biết trước $K$ không" — một **thuộc tính thuật toán** — được suy ra bằng cách tìm chuỗi `"K="` trong **tên hiển thị**. Hệ quả:
- `"Spectral (affinity gating, K=74)"` → `True` ✓ (đúng, nhưng đúng do tình cờ có chữ "K=")
- Nếu ai đó đổi tên hàng thành `"Spectral (74 clusters)"` → `False` ✗ **sai ngay**, dù thuật toán không đổi.
- `"HDBSCAN (dist=1-w gating)"` → `False` ✓ đúng, nhưng cũng chỉ vì tên không chứa "K=".

Cột "Needs $K$?" là **một trong hai trụ đỡ của luận điểm cuối cùng** của bài (dòng 439: *"Louvain's advantage over Agglomerative is operational---it does not require $K$"*). Một claim trọng yếu như vậy không nên phụ thuộc vào chính tả của nhãn hiển thị. Giá trị hiện tại tình cờ đúng cả 10 hàng, nên **không có con số nào trong bài sai** — nhưng đây là mã dễ vỡ ở đúng chỗ không được phép vỡ.

---

## CHẤT VẤN 14.4 — Bài báo không nói $K$ của Agglomerative và Spectral **lấy từ kết quả Louvain** (TRUNG BÌNH, ảnh hưởng cách đọc)

`exp4_baselines.py` dòng 27–30:
```python
lou = run_louvain(ws, 1.0, 42)
k_lou = len(set(lou))          # = 74
... f"Spectral (affinity gating, K={k_lou})"
... f"Agglomerative (dist=1-w, K={k_lou})"
```
$K=74$ **không phải** một lựa chọn độc lập, cũng không phải số nhãn ground-truth (14): nó là **số cụm mà Louvain tìm được**. Bảng 6 chỉ ghi "$K{=}74$" như một tham số trần trụi.

Điều này cắt cả hai hướng và phải được nói rõ:
- **Có lợi cho Agglomerative:** nó được tặng đúng độ phân giải mà Louvain tự tìm ra — nên việc nó "khớp Louvain chính xác trên cả bốn độ đo" là kết quả **được trợ giúp**, không phải trùng hợp. Bài báo (dòng 439) đã trung thực nói ưu thế của Louvain là "không cần $K$", nhưng **chưa nói** rằng con số $K$ ấy chính là output của Louvain — làm cho câu "ties Louvain exactly" trông độc lập hơn thực tế.
- **Bất lợi cho Spectral:** ép $K=74$ lên một đồ thị thưa gần-rời-rạc là gần như tệ nhất có thể; bài đã bổ sung hàng $K=14$ để bù, tốt.

Đây là chi tiết tái lập bắt buộc: một người đọc muốn lặp lại phải biết $K$ đến từ đâu.

---

## CHẤT VẤN 14.5 — Exp9 dùng nhãn `K-Means (raw, K=12)` trong khi Exp4 dùng $K{=}14$, không giải thích (NHỎ nhưng gây nghi)

- Bảng 6 (Exp4): `K-Means ($K{=}14$, coords) … ARI 0,5016`
- Bảng 9 (Exp9): `K-Means ($K{=}12$) … ARI 0,5652`

Hai bảng cạnh nhau, cùng một thuật toán, hai giá trị $K$ khác nhau, và bảng sau cho ARI **cao hơn**. `exp9_discriminative_metric.json` xác nhận `"K-Means (raw, K=12)"` — nên **số liệu khớp JSON** (loop 9 đã kiểm đúng). Nhưng bài **không giải thích vì sao** Exp9 chọn 12 mà Exp4 chọn 14. Một phản biện sẽ đọc thành "chọn $K$ nào cho ra con số muốn có". Cần một câu nêu lý do, hoặc thống nhất về $K=14$.

---

## ĐÃ KIỂM — KHÔNG PHẢI LỖI (giữ nguyên)

- **ARI/NMI mask `gt >= 0` là đúng và đã được công bố.** `cluster_quality()` loại điểm nhiễu khỏi phép chấm; bài báo nói rõ ở dòng 332 (*"Because ARI and NMI mask out `gt`$<0$, that noise-hygiene difference is invisible to both"*) và bù bằng cột `noise_absorbed_pct`. Xử lý đúng chuẩn và minh bạch ✓.
- **Ba biến thể đường kính** (`all` / `multi` / `weighted`) + cảnh báo singleton trong docstring `geographic_spread` — thiết kế đo lường cẩn thận, đúng như bài mô tả ở dòng 326 ✓. (Bẫy duy nhất bị bỏ sót là thùng nhiễu, mục 14.2.)
- **`noise_absorbed_pct` định nghĩa đúng** như caption Bảng 6 nói ("fraction of `gt`$=-1$ events absorbed into labeled clusters") ✓.
- **HDBSCAN không có điểm có nhãn nào trong thùng nhiễu** ở phiên bản dữ liệu hiện tại: kiểm được `labeled pts in noise bin = 0`, cả 7 điểm trong thùng đều là `gt=-1`. Điều này **xác nhận** ARI $=1{,}0$ của HDBSCAN là thật (nó phục hồi đủ 14 nhãn) và đồng thời **xác nhận loop 8 đã lỗi thời**: mệnh đề "36 điểm có nhãn bị đẩy vào thùng nhiễu" là của bộ dữ liệu cũ. Loop 10 đã xóa mệnh đề đó khỏi cả ba artifact ✓ — kiểm lại lần nữa, `main.tex` hiện không còn câu nào nói HDBSCAN xé lẻ ✓.
- **Exp7 mô phỏng điều phối:** đọc kỹ `_simulate_arrival_times` — heap 3 ca nô, mỗi ca nô đi từ vị trí hiện tại tới trọng tâm cụm kế tiếp trong hàng đợi, cộng 15 phút phục vụ. Mô hình đơn giản nhưng **mô tả trong bài khớp chính xác code** ✓. Quan trọng hơn: `_severe_vulnerable_weight` dùng ngưỡng $F>0{,}7$ **không** chứa `V` cũng không chứa `core` → tuyên bố "neutral metric" là **đúng thật**, và docstring còn ghi rõ thiên vị của hai độ đo kia. Đây là phần code trung thực nhất của cả suite ✓.
- **Depot = trọng tâm hình học của mọi cụm**, giống nhau cho cả ba chính sách → so sánh công bằng ✓.
- **Spectral `assign_labels="discretize"`** (không phải `kmeans`) → xác định, không phụ thuộc seed ✓ phù hợp tuyên bố tái lập.
- **HDBSCAN/Agglomerative dùng $d_{ij}=1-w_{ij}/w_{\max}$**, `fill_diagonal(0)` → khoảng cách hợp lệ, cùng thông tin đồ thị như Louvain ✓ đúng như bài nói "same graph".

---

## TỔNG KẾT STEP 1

| # | Lỗi | Mức | Hướng thiên vị |
|---|---|---|---|
| 14.1 | "raw coordinates / purely geometric" là nhãn sai — code dùng 4 đặc trưng gồm $F,E$; baseline toạ độ-thuần thật đạt ARI **0,83** chứ không phải 0,50 | NGHIÊM TRỌNG | **có lợi cho bài báo** |
| 14.2a | Thùng nhiễu $-1$ bị đếm như cụm → HDBSCAN "21 cụm / 55,72 km" thực là **20 cụm / 48,69 km**; DBSCAN eps 0,3 "max 213,69 km" thực là **7,75 km** | NGHIÊM TRỌNG | **có lợi cho bài báo** |
| 14.2b | `noise_absorbed_pct` đếm thùng nhiễu như cụm thật → DBSCAN eps 0,3 in **100%**, sự thật **0,0%**. Đảo ngược dấu so sánh | **NGHIÊM TRỌNG NHẤT** | **có lợi cho bài báo** |
| 14.4 | Không công bố $K{=}74$ của Agglomerative/Spectral chính là output của Louvain | TRUNG BÌNH | có lợi cho Agglomerative |
| 14.3 | `needs_preset_k` suy ra bằng so khớp chuỗi trên tên hiển thị | TRUNG BÌNH | không (hiện đúng) |
| 14.5 | Exp9 dùng $K{=}12$, Exp4 dùng $K{=}14$, không giải thích | NHỎ | không |

**Nhận định chung:** loop này khác hẳn loops 9–13. Ở đó lỗi là *sai số* hoặc *lệch artifact*. Ở đây **mọi con số đều khớp JSON** — lỗi nằm ở chỗ **JSON đo một thứ, bài báo gọi nó là thứ khác**. Và hai lỗi nghiêm trọng nhất đều nghiêng theo hướng **làm baseline trông tệ hơn thực tế**. Bài báo đã rất trung thực ở nhiều chỗ khác (thừa nhận HDBSCAN thắng ARI, Agglomerative hoà, equity chỉ 2,9%, $C_i$ bị phá ở 0,92) — nên hai lỗi này càng phải sửa để giữ được sự nhất quán về tính trung thực đó.
