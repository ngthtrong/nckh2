# Loop 10 — Báo cáo Phản biện (Step 1)

**Vai trò:** Giáo sư chủ tịch hội đồng phản biện. Loop 9 đã sửa 6 lỗi trong `main.tex` và dán cảnh báo trạng thái lên hai file tiếng Việt. Loop 10 tấn công đúng món nợ mà loop 9 đã cố ý hoãn: **`resource/BaiBao_NoiDung.md` và `resource/Paper.md` vẫn mô tả một thực nghiệm không còn tồn tại**.

Phương pháp: đối chiếu từng câu trong mục Thực nghiệm của hai file Việt với JSON hiện hành. Một cảnh báo trạng thái ở đầu file là băng dán tạm, không phải lời giải: tài liệu vẫn chứa hàng chục con số sai và **nhiều mệnh đề kết luận trái dữ liệu**.

---

## CHẤT VẤN 10.1 — Toàn bộ mục Thực nghiệm dựa trên bộ dữ liệu đã bị thay thế (NGHIÊM TRỌNG, hệ thống)

Bảng đối chiếu chi tiết (bên trái: BaiBao/Paper.md hiện tại; bên phải: JSON hiện hành):

### Setup (§5.1)
| Hạng mục | Bản Việt | Sự thật (JSON/generator) |
|---|---|---|
| Số sự kiện | **285** | **341** |
| Số nhãn GT | **12** | **14** |
| Nhiễu | **20** (5 tin giả) | **61** (`gt=-1`), **23** tin giả |
| Điểm kịch bản | **25** (24 điểm/6 nhóm, nhãn 100–105) + 1 fake | **41** (40 điểm/8 nhóm, nhãn 100–107) + 1 fake |
| Số kịch bản | S1–S4 | **S1–S5** (thiếu hẳn S5) |
| Vị trí nhóm kịch bản | "**neo tại tâm ốc đảo**, lệch 0 m" | **satellite 3 km** khỏi tâm, có assertion `assert_gt_separable` (≥2 km) |
| Điểm có nhãn | 264 | **280** |

### Exp1 (§5.2)
| | Bản Việt | JSON |
|---|---|---|
| ARI gating | 0,892 | **0,9957** |
| ARI additive | 0,892 (**bằng nhau**) | **0,8763 / 0,9161 / 0,9572 / 0,9161** (4 cấu hình α) |
| Đường kính TB additive | 100,07 km | **151,13 / 140,41** km |
| Đường kính TB gating | 0,30 km | **0,85** km (multi-member) / 0,1491 (all) |
| Số cụm | 6 vs 27 | **8–9 vs 74** |
| (1B) dân số/lõi thô | 216 người, 71,65 | **200 người, 66,48** |
| (1B) sau chuẩn hóa | core 0,82, $\mathcal{P}=1{,}52$ | **0,83 / 1,54** |
| (1C) S2 | $\mathcal{V}_{agg}=1{,}97$, add 1,66, mult 1,36 | **1,76 / 1,37 / 1,06** |
| (1F) $\mathcal{F}_{max}$ gated | 0,45 | **0,4457** |

### Exp2 (§5.3)
| | Bản Việt | JSON |
|---|---|---|
| $\lambda$ | ổn định ≤1,5; 2,0→0,83; 3,0→0,67; an toàn [0,5;1,5] | **0,9957 trên toàn [0,5;2,0]**; chỉ 3,0→**0,8438**; an toàn **[0,5;2,0]** |
| $\sigma_{geo}$ | "ARI giữ 0,892 trên dải rộng", diam 0,28→1,59 km | ARI **có phản ứng** (range 0,1205): plateau [400,1000], 1500→0,9369, 2500→0,9156, 4000→**0,8752** (diam max **15,26 km**) |
| Modularity | ~0,83 | **0,861** |
| $s$ | $s=20$ → spread tới 1,78 | $s=20$ → max **1,6498** (spread 0,650) |
| $\tau_F,\tau_E$ | "ARI giữ 0,892 toàn lưới" | 0,9957 toàn lưới **và 74 cụm không đổi** |
| $\beta/\gamma$ | tụt **0,7855** khi $\beta\ge0{,}9$ | tụt **0,9509** tại $\beta=0{,}9$ (75 cụm) |

### Exp3 (§5.4)
Modularity **0,8311** → thực tế **0,861**; ARI 0,892 → **0,9957**. Thiếu chi tiết "13 cộng đồng đánh giá được/seed, 130 tổng" mà `main.tex` đã có (61 singleton bị loại khỏi phép kiểm liên thông).

### Exp4 (§5.5) — bảng baseline sai **toàn bộ 9 hàng**
| Phương pháp | Bản Việt (ARI/diam) | JSON (ARI/diam multi) |
|---|---|---|
| Louvain/Leiden | 0,892 / 0,30 | **0,9957 / 0,85** |
| Spectral K=27 | 0,339 / 14,11 | **Spectral K=74: 0,1657 / 8,79** |
| Spectral K=14 | *(thiếu hàng)* | **0,9464 / 38,16** |
| HDBSCAN | **0,890** / 11 cụm / 25,08 | **1,0** / **21** cụm / **55,72** |
| Agglomerative | 0,892 / 0,30 (K=27) | 0,9957 / 0,85 (**K=74**) |
| K-Means K=12 | 0,688 / 49,21 | **K=14: 0,5016 / 93,47** |
| K-Means K=3 | 0,433 / 102,04 | **0,3282 / 164,42** |
| DBSCAN 0,3 | 0,644 / 15,12 (15 cụm) | **0,2391 / 7,78 (32 cụm)** |
| DBSCAN 0,6 | 0,730 / 32,27 (7 cụm) | **0,5234 / 38,67 (8 cụm)** |
| Cột "Noise abs." | **không có** | có trong `main.tex` (0,0% vs 100%) |

Thiếu luôn cột `max_diam_km` — cột mà `main.tex` coi là **chỉ số quyết định** ("what actually breaks a dispatch plan").

### Exp5 (§5.6)
| | Bản Việt | JSON |
|---|---|---|
| ±0,05 | τ 0,994 / min 0,977 / top3 100% | **0,9789 / 0,9526 / 100%** |
| ±0,10 | 0,986 / 0,937 / **99,0%** | **0,9552 / 0,9104 / 100%** |
| ±0,20 | 0,957 / 0,841 / **76,5%** | **0,9111 / 0,8045 / 100%** |
| $\sigma_{geo}$ 1200 m | 26 cụm, τ 0,9815 | **73 cụm, τ 0,9954** |
| Ổn định theo $s$ | **thiếu hẳn** | τ≥0,9985, =1,0 khi $s\ge10$ |

Đáng chú ý: bản Việt báo top-3 chỉ giữ 76,5% ở ±0,20, còn dữ liệu hiện tại là **100% ở cả ba mức, cả 600 trial**. Bản Việt đang **báo cáo dưới thực tế** — nhưng vẫn là sai số liệu.

### Exp7 (§5.8) — sai cả **độ đo chính** (NGHIÊM TRỌNG về phương pháp luận)
Bản Việt: "Bỏ $V_i$ làm trễ từ 146,5 lên 163,6 phút — **cải thiện 10,4%**", "toàn bộ nạn nhân 942,9 vs 719,6 phút", "dạng cộng 133,3 phút".

JSON hiện hành: 165,01 / 246,58 / 140,69 (`time_to_vulnerable`), 110,2 / 113,53 / 122,89 (`severe_flood_vulnerable`), 2528 / 2410 / 2248 (`mean_arrival_all`).

Không con số nào khớp. Nhưng lỗi nặng hơn con số: **bản Việt dùng `time_to_vulnerable` làm độ đo chính**, trong khi JSON ghi rõ `primary_metric: "severe_flood_vulnerable_time_min"` và `metric_bias_note` đánh dấu `time_to_vulnerable` là **"thiên vị dạng CỘNG"**. `main.tex` đã xử lý đúng: chọn độ đo trung lập, báo cáo cải thiện **2,9%** thay vì con số 33% hào nhoáng. Bản Việt vẫn quote độ đo thiên vị như thể nó là kết quả chính → đúng loại lỗi mà toàn bộ quy trình này tồn tại để diệt.

### Exp8 (§5.9)
AUC **0,9651** → thực tế **0,9176**; mean $C_i$ 0,50/0,92 → **0,60/0,89**; 285 sự kiện → 341; **thiếu hoàn toàn Average Precision 0,3159** (CI [0,2577;0,4063]) và baseline 0,0674 — chính là con số mà `main.tex` nhấn mạnh là "the number a deployment should plan around" vì lớp dương chỉ 6,7%. Bản Việt chỉ có AUC → **thổi phồng tính hữu dụng** đúng như `main.tex` cảnh báo.

### Exp9 (§5.10) — mệnh đề trái dữ liệu (NGHIÊM TRỌNG)
Bản Việt: "HDBSCAN tụt còn **0,929** vì xé lẻ... homogeneity 0,915 cao hơn Louvain 0,864", completeness Spectral **0,595**, Louvain V-measure **0,927**, độ trải ARI **0,55**.

JSON hiện hành: HDBSCAN **homogeneity 1,0, completeness 1,0, V 1,0, ARI 1,0** — hoàn hảo trên **cả bốn** độ đo. Louvain: H 0,9867 / C 1,0 / V 0,9933. Spectral C **0,5305**. K-Means (K=12) 0,5652/0,7466/0,7293. Spread: ARI **0,8343**, H 0,3723, C 0,4695, V 0,3073.

Nghĩa là: **toàn bộ lập luận "completeness cứu chúng ta trước HDBSCAN" đã sụp**. `main.tex` đã sửa đúng và trung thực ("the decomposition does *not* rescue our method against HDBSCAN... no label-agreement metric favors Louvain over HDBSCAN; the distinguishing evidence is geometric"). Bản Việt vẫn kể câu chuyện cũ — tức nó đang **khẳng định một ưu thế không tồn tại**. Trớ trêu: đây chính là chỗ loop 8 đã sửa mệnh đề nhân-quả, nhưng dữ liệu sau đó đổi và bản Việt không được cập nhật theo.

### Exp6 (§5.7), Exp10–12
- Exp6: **đã sửa ở loop 9** ✓ (τ=1,0, không đổi gì).
- **Thiếu hoàn toàn Exp10 (kích thước gói 105–111 byte), Exp11 (scaling tới n=7181, 37,7 s), Exp12 (20 seed)** — ba thí nghiệm mới nhất không có mặt trong bản Việt, dù §5.1 (đã sửa loop 9) nay nói "mười hai thí nghiệm exp1–exp12". Tự mâu thuẫn: khai 12 nhưng chỉ trình bày 9.

### §5.11, Tóm tắt, Kết luận, Threats
- §5.11: "Bảy hình PNG" ✓ đúng (7 file). Nhưng liệt kê "(2) bão hòa tanh, (3) cổng $C_i$" — thực tế `fig2_map.png` là bản đồ và `fig3_heatmap.png` là heatmap; cổng $C_i$ nằm trong `fig1_ablation.png` (panel b). **Mô tả sai tên/nội dung hình.**
- Tóm tắt (dòng 9) và Kết luận (dòng 428): mọi con số cũ (285, 100 km→0,30 km, 0,892, τ 0,99/0,94, top-3 **99%**, Spectral 0,339, HDBSCAN 0,890/25 km).
- Threats (dòng 421): toàn bộ lập luận "trần ARI do GT áp đặt" đã lỗi thời (generator đã sửa, `n_colocated_narrative_groups: 0`). Dòng 424: "exp3 chạy 10 seed, các thí nghiệm khác chủ yếu seed=42. **Nên** báo cáo trung bình ± sd qua nhiều seed" — nay Exp12 **đã làm** việc đó trên 20 seed; câu này biến một việc đã hoàn thành thành một hạn chế còn tồn.

---

## CHẤT VẤN 10.2 — Paper.md: cùng bệnh, cộng một lỗi riêng

`resource/Paper.md` §Thực nghiệm (dòng ~195–230) lặp lại đúng các số cũ trên. Ngoài ra dòng 195 nói "**285 sự kiện**... **12 nhãn**... 20 nhiễu... 25 kịch bản (S1–S4)... nhóm neo tại tâm ốc đảo nên chặn trần ARI" — sai y hệt BaiBao.

Riêng dòng 201 (đã chỉnh nhẹ ở loop 8) hiện đọc: "HDBSCAN 0,890 nhưng chỉ 11 cụm với đường kính 25 km (bị thổi lên do thùng nhiễu + một cụm rải rác, vì nó xé lẻ ốc đảo chứ không gộp)". Với dữ liệu mới, **HDBSCAN không còn xé lẻ gì cả** (completeness 1,0) — nó đạt ARI 1,0 và thất bại **chỉ** ở hình học (55,72 km). Mệnh đề đã sửa ở loop 8 nay lại sai vì lý do khác: nó đúng với dữ liệu cũ, sai với dữ liệu mới.

---

## CHẤT VẤN 10.3 — Rủi ro quy trình: "cảnh báo trạng thái" không thay được đồng bộ (PHƯƠNG PHÁP)

Loop 9 dán cảnh báo lên đầu hai file. Điều đó đúng như một biện pháp tạm, nhưng nếu để nguyên thì dự án có **hai bộ kết quả cùng tồn tại**, một bộ được đánh dấu "đừng dùng". Trong thực tế, tài liệu tiếng Việt là bản mà nhóm dùng để viết báo cáo NCKH và thuyết trình — nghĩa là bộ số sai vẫn có đường vào sản phẩm cuối. Phải đồng bộ thật.

**Câu hỏi gay gắt:** Nếu `main.tex` đã đúng và `demo/` là nguồn sự thật, thì hai file Việt đang giữ vai trò gì? Nếu là bản nháp lịch sử thì phải nói rõ và đóng băng; nếu là tài liệu sống thì phải đồng bộ. Trạng thái lửng lơ hiện tại là tệ nhất trong ba lựa chọn.

---

## TỔNG KẾT STEP 1

Một lỗi hệ thống, biểu hiện trên **~45 vị trí số liệu** và **4 mệnh đề kết luận trái dữ liệu**:

1. **10.1** — hai file Việt mô tả bộ 285-sự-kiện/12-nhãn đã bị thay thế bởi 341-sự-kiện/14-nhãn. Sai: setup, Exp1, Exp2, Exp3, Exp4 (cả 9 hàng), Exp5, Exp7, Exp8, Exp9, Tóm tắt, Kết luận, Threats. Thiếu: Exp10, Exp11, Exp12, cột max-diameter, cột noise-absorption, Average Precision, độ đo trung lập của Exp7.
2. **Bốn mệnh đề kết luận sai** (nặng hơn sai số): (a) Exp9 khẳng định completeness phân biệt được Louvain với HDBSCAN — dữ liệu nói HDBSCAN hoàn hảo cả 4 độ đo; (b) Exp7 dùng độ đo **thiên vị** làm độ đo chính; (c) Exp8 chỉ báo AUC, bỏ AP → thổi phồng; (d) "trần ARI do GT áp đặt" đã bị generator mới vô hiệu.
3. **10.2** — Paper.md sai y hệt, cộng mệnh đề HDBSCAN "xé lẻ" nay không còn đúng.
4. **10.3** — cảnh báo trạng thái phải được thay bằng đồng bộ thật, rồi xóa cảnh báo.
