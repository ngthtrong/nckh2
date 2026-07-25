# Loop 10 — Kế hoạch Giải quyết (Step 2)

**Vai trò:** Tác giả. Nguyên tắc: **`demo/results/tables/*.json` là nguồn sự thật; `paper/main.tex` là bản đã đối chiếu xong (loop 9)**. Vì vậy đồng bộ hai file Việt = dịch/căn theo `main.tex`, không viết lại từ đầu.

---

## 10.3 trước tiên — Quyết định vai trò của hai file Việt

Ba lựa chọn: (a) đóng băng như bản nháp lịch sử, (b) đồng bộ thật, (c) để lửng lơ với cảnh báo.

**Chọn (b) — đồng bộ thật.** Lý do: `BaiBao_NoiDung.md` được memory dự án ghi là "nguồn sự thật tiếng Việt" và là bản dùng cho báo cáo NCKH/thuyết trình. Đóng băng nó nghĩa là nhóm không còn tài liệu tiếng Việt dùng được. Sau khi đồng bộ, **xóa khối cảnh báo** đã dán ở loop 9 — vì để lại một cảnh báo sai (nói tài liệu chứa số cũ khi nó đã đúng) cũng là một lỗi.

Phạm vi: đồng bộ **mục Thực nghiệm + Tóm tắt + Kết luận + Threats** — tức mọi chỗ chứa số thực nghiệm. **Không** viết lại phần Phương pháp (Mục 4): công thức không đổi, và loops 1–8 đã dọn phần đó.

---

## 10.1 + 10.2 — Đồng bộ số liệu: sửa cụ thể

### A. Setup (BaiBao §5.1, Paper.md dòng 195)
Thay bằng: **341 sự kiện**, **14 nhãn GT**; 240 lõi quanh 6 ốc đảo (nhãn 0–5, 40/ốc đảo); **61 nhiễu** `gt=-1` trong đó **23 tin giả**; **41 điểm kịch bản** tạo **8 nhóm** (nhãn 100–107) cộng 1 tin giả lẻ; **S1–S5** (thêm S5: hai nhóm 6 điểm cách nhau 900 m, $F=0{,}30$ vs $0{,}95$).

**Xóa hẳn** đoạn "neo tại tâm ốc đảo / lệch 0 m / chặn trần ARI theo cấu trúc". Thay bằng: mỗi nhóm kịch bản đặt trên **satellite 3 km** khỏi tâm ốc đảo chủ (xa hơn $\sigma_{geo}=700$ m rất nhiều) nên **mọi nhãn đều tách được về không gian**; generator có assertion `assert_gt_separable` fail build nếu có điểm kịch bản vào trong 2 km của tâm ốc đảo. Thêm: độ lệch chuẩn trong-ốc-đảo 0,16 ($F$) và 0,18 ($E$) để phân bố ngữ cảnh **chồng lấn**.

Bổ sung mục **Độ đo** cho khớp `main.tex`: nói rõ đường kính có hai biến thể (**trung bình multi-member** ≥2 thành viên, và **max**), cộng số singleton và **tỉ lệ nhiễu bị hấp thụ**, cộng homogeneity/completeness. Nêu lý do: phân hoạch cô lập outlier thành singleton được thưởng đường kính 0 một cách giả tạo.

### B. Exp1 (§5.2)
- (1A) Bảng mới **5 dòng** (4 cấu hình additive + gating), có cột max diam và số cụm:

| Dạng | ARI | NMI | Đ.kính TB (km) | Max (km) | Số cụm | S1 gộp? |
|---|---|---|---|---|---|---|
| Cộng, $\alpha=0{,}34$ | 0,8763 | 0,9003 | 151,13 | 209,05 | 8 | có |
| Cộng, $\alpha=0{,}5$ | 0,9161 | 0,9361 | 151,13 | 209,05 | 8 | có |
| Cộng, $\alpha=1{,}0$ | 0,9572 | 0,9598 | 140,41 | 213,95 | 9 | có |
| Cộng chuẩn hóa 1/3 | 0,9161 | 0,9361 | 151,13 | 209,05 | 8 | có |
| **Nhân/gating** | **0,9957** | **0,9933** | **0,85** | **1,41** | 74 | **không** |

- **Bỏ hẳn** luận điểm "ARI hai dạng bằng nhau" (nay khác rõ) và luận điểm "trần ARI do GT". Thay bằng: gating **vừa** co đường kính (151→0,85 km TB, 214→1,41 km max, hệ số **151×** ở max) **vừa nâng** ARI (0,9572→0,9957). Cơ chế: mọi cấu hình cộng đều gộp hai nhóm S1 cách nhau **106,8 km**; gating cho tích bằng 0 nên tách. Hấp thụ nhiễu: cộng **93,6%** vs gating **0,4%** (61 singleton) — vô hình với ARI/NMI vì mặt nạ `gt<0`.
- Lý do ARI 0,9957 chứ không 1,0: cặp S5 (nhãn 106–107) cách **923 m** bị gộp. Phân rã: 240 điểm lõi ARI **1,0**, 40 điểm kịch bản ARI **0,821**, toàn bộ 280 điểm có nhãn **0,9957**, **0 nhóm đồng vị trí**.
- (1B): 200 người / lõi thô **66,48** → sau chuẩn hóa lõi **0,83**, $\mathcal{P}=$ **1,54**.
- (1C): S2 $\mathcal{V}_{agg}=$ **1,76**, add **1,37**, mult **1,06**, **cùng hạng 5** → lựa chọn này **không** đổi vị trí S2; max rank shift trên 74 cụm = **1**; **67/74** cụm có $\mathcal{V}_{agg}=1$ (hai dạng trùng khít). Nói thẳng: lập luận cho dạng nhân là **cấu trúc**, không phải thực nghiệm trên bộ này.
- (1F): 0,99 → **0,4457**.

### C. Exp2 (§5.3) — viết lại theo `main.tex`
- $\sigma_{geo}$: **quan trọng nhất, không phẳng** (ARI range **0,1205**): đỉnh 0,9957 trên [400,1000] m (74 cụm, max 1,41 km); 1500 m→0,9369; 2500 m→0,9156; 4000 m→0,8752 (cụm xấu nhất **15,26 km**); 200 m vụn quá (77 cụm, 63 singleton) nhưng vẫn 0,9908. Plateau [400,1000] cho biên độ sai ~2×.
- $\lambda$: range **0,1519**; **đúng 0,9957 trên toàn [0,5; 2,0]**; sụp **0,8438** tại 3,0 (77 cụm). Khoảng an toàn **[0,5; 2,0]** (không phải [0,5;1,5]).
- $s$: $s=1$ spread đầy **1,0**; $s=10$ spread 0,914 (max 1,914); $s=20$ chỉ **0,650**.
- $\tau_F,\tau_E$: 0,9957 **và 74 cụm** trên toàn lưới [0,15;0,5] → **bền vững thật** (không chỉ điểm số mà cả phân hoạch không đổi).
- $\beta/\gamma$: range **0,0448**; 0,9957 khi $\beta\le0{,}7$; tụt **0,9509** tại $\beta=0{,}9$ (75 cụm) do mất tách S5.
- Modularity **0,861**.

### D. Exp3 (§5.4)
**10 seed** (giữ), 0 cộng đồng đứt gãy, ARI **0,9957**, Modularity **0,861**. Bổ sung hai chi tiết `main.tex` đã có: chỉ **13 cộng đồng đánh giá được/seed** (61 singleton bị loại vì không thể đứt gãy), tổng **130**; Louvain và Leiden cho **phân hoạch trùng khít** trên mọi seed.

### E. Exp4 (§5.5) — thay bảng bằng **10 hàng** khớp `exp4_baselines.json`, thêm cột max-diam và noise-absorption
Và viết lại phần phân tích theo `main.tex`: **báo cáo trước tiên kết quả bất lợi** — HDBSCAN đạt ARI/NMI **1,0** (cao hơn Louvain 0,9957) vì phục hồi cả 14 nhãn kể cả cặp S5 923 m, nhưng **không dùng được**: 21 cụm, đường kính TB **55,72 km**, xấu nhất **201 km**, hấp thụ 3,3% nhiễu. Agglomerative **khớp Louvain chính xác** cả 4 chỉ số → không tuyên bố Modularity hơn linkage; ưu thế của Louvain là **không cần $K$**. Spectral K=74 sụp 0,1657; cho biết $K=14$ thì 0,9464 nhưng 38 km và hấp thụ 100% nhiễu. Kết luận **liên kết (conjunctive)**: ma trận gating cấp độ gắn kết, Modularity cấp $K$ tự động.

### F. Exp5 (§5.6)
Bảng: ±0,05 → **0,9789 / 0,9526 / 100%**; ±0,10 → **0,9552 / 0,9104 / 100%**; ±0,20 → **0,9111 / 0,8045 / 100%**. Nhấn: top-3 giữ nguyên **100% cả 600 trial**. Bổ sung ổn định theo $s$ ($\tau\ge0{,}9985$, =1,0 khi $s\ge10$) và theo $\sigma_{geo}$ (74 cụm & τ=1,0 tới 900 m; 1200 m → **73 cụm**, τ **0,9954**).

### G. Exp7 (§5.8) — sửa cả cấu trúc lập luận
Viết lại theo `main.tex`: nêu rõ **vấn đề chọn độ đo**, rằng `time_to_vulnerable` **thiên vị dạng cộng** và `harm_weighted` thiên vị dạng nhân, nên **độ đo chính là trung lập**: *thời gian đến nạn nhân yếu thế đang ở vùng ngập nặng ($F\ge0{,}7$)*.
Số: nhân **110,2** phút vs mù **113,5** (+**2,9%**) vs cộng **122,9** (+**10,3%**). Nói thẳng: lợi ích công bằng so với chính sách mù là **nhỏ** trên độ đo trung lập — **không** phải 33% mà độ đo suy-từ-$V$ báo (165,0 vs 246,6). Chi phí: thời gian đến trung bình toàn bộ nạn nhân **2528** vs **2410** phút (mù) — đánh đổi công bằng–hiệu quả tường minh.

### H. Exp8 (§5.9)
AUC **0,9176** (CI 95% [0,8863; 0,9439], 1000 bootstrap), mean $C_i$ **0,60** giả vs **0,89** thật, **23** giả / **341**. **Thêm AP = 0,3159** (CI [0,2577; 0,4063]) so với baseline ngẫu nhiên **0,0674** → lift **4,7×**, và nói rõ vì lớp dương chỉ **6,7%** nên AUC một mình **thổi phồng** tính hữu dụng; AP là con số triển khai phải lập kế hoạch theo. Adversarial giữ: 0,45 / 0,77 / 0,74 / **0,92** — và nhấn rằng 0,92 **cao hơn** trung bình tin thật 0,89, nên cổng không chỉ trượt mà còn xếp tin giả **đáng tin hơn** tin thật trung bình.

### I. Exp9 (§5.10) — **đảo lại kết luận** cho khớp dữ liệu
Xóa toàn bộ câu chuyện "completeness phân biệt Louvain với HDBSCAN". Viết lại theo `main.tex`:
- Bảng: Louvain/Leiden/Agglom 0,9957 / H **0,9867** / C **1,0** / V **0,9933**; HDBSCAN **1,0 cả bốn**; Spectral(K=74) 0,1657 / 0,9978 / **0,5305** / 0,6927; K-Means(K=12) 0,5652 / 0,7466 / 0,7293 / 0,7378; DBSCAN(0,6) 0,5234 / 0,6277 / 0,8922 / 0,7369.
- Giá trị **thật** của phân rã: giải thích **cách** một phương pháp thất bại — Spectral thuần nhưng vỡ vụn (over-segmentation), K-Means trộn cả hai chiều, DBSCAN under-segmented.
- **Thừa nhận thẳng:** phân rã **không** cứu được ta trước HDBSCAN; **không** độ đo khớp-nhãn nào (tổng hợp hay phân rã) ưu ái Louvain. Bằng chứng phân biệt nằm **ngoài** họ độ đo này, là **hình học** (0,85 vs 55,72 km TB; 1,41 vs 201,46 km max). Bài học mạnh hơn "dùng thêm completeness": với phân cụm hướng-điều-phối, **không** độ đo khớp-phân-hoạch nào là mục tiêu đủ.
- Spread: ARI **0,8343**, H 0,3723, C 0,4695, V 0,3073.

### J. Thêm ba mục mới (§5.11–5.13), đẩy Trực quan hóa xuống §5.14
- **Exp10 — Kích thước gói metadata:** 341 gói JSON nén, **105–111 byte** (min 105, median 110, max 111) → mỗi sự kiện lọt một datagram nhỏ, MB→sub-KB.
- **Exp11 — Độ phức tạp tính toán:** $n\in\{341, 1201, 3581, 7181\}$; builder vector hóa nhanh **3,3–6,1×** so với vòng lặp đôi, sai khác $<10^{-10}$ (max **7,3×10⁻¹¹**) nên tăng tốc là **chính xác**, không xấp xỉ. Trung thực về scaling: build tăng **nhanh hơn** dự đoán $O(n^2)$ ở **cả ba** bước (20,2× vs 12,4×; 11,3× vs 8,9×; 5,6× vs 4,0×) do ma trận dày vượt cache, thành giới hạn băng thông bộ nhớ. Ở $n=7181$: tổng **37,7 s** một lõi CPU (sparsify 4,1 s, Louvain 9,0 s). Quá $\sim10^4$ phải thay ma trận dày bằng spatial index (ball-tree/geohash) — điều mà gating cho phép vì $\mathcal{S}_{geo}$ đã triệt gần hết cặp.
- **Exp12 — Kiểm chứng đa seed:** **20 seed** độc lập, sinh lại dữ liệu mỗi lần; gating thắng **100% seed** trên mọi chỉ số so được. Bảng: ARI 0,9957±0,0000 vs 0,9415±0,0141; NMI 0,9933±0,0000 vs 0,9500±0,0073; đ.kính TB 0,83±0,04 vs 149,19±11,25; max 1,57±0,25 vs 196,82±8,09; nhiễu hấp thụ 0,41±0,90% vs 93,61±10,30%; Modularity **0,8612±0,0004** vs **0,7748±0,0076**; số cụm 73,3±0,8 vs 8,6±0,7. **Kèm cảnh báo:** sd bằng 0 của gating **không** phải bằng chứng bền vững phổ quát mà vì hình học liên-nhóm của generator cố định qua các seed nên **đúng một cặp** (106–107) gộp ở **20/20** seed; phương sai khác 0 (đường kính, số cụm, singleton) đến từ vị trí nhiễu ngẫu nhiên.

### K. §5.11 cũ (Trực quan hóa) — sửa mô tả hình
Sửa danh sách 7 hình cho khớp tên file thật: (1) `fig1_ablation` gating-vs-cộng **và cổng $C_i$** (2 panel), (2) `fig2_map` bản đồ cụm, (3) `fig3_heatmap` heatmap, (4) `fig4_sigma_sweep`, (5) `fig5_resolution_sweep`, (6) `fig6_baselines`, (7) `fig7_ranking_stability`.

### L. Tóm tắt + Kết luận + Threats
- **Tóm tắt:** căn theo Abstract `main.tex`: 341 sự kiện; đường kính **xấu nhất 214 km → 1,4 km** đồng thời **nâng** ARI 0,957→0,996; 20 seed thắng 100% (0,9957±0,0000 vs 0,9415±0,0141); cổng $C_i$ giảm **55%** dân số ảo nhưng adversary đạt $C_i=0{,}92$; Spectral sụp **0,166**, HDBSCAN ARI hoàn hảo nhưng **55,7 km**, K-Means **0,502**, DBSCAN **0,523**; Kendall τ TB **0,955**, min **0,910**, top-3 giữ **100%**.
- **Kết luận:** thêm đoạn "các kết quả **không** ủng hộ phương pháp" như `main.tex` (HDBSCAN ARI 1,0; Agglomerative khớp chính xác; ablation ngữ cảnh đổi **không gì**; công bằng chỉ **+2,9%**; adversary 0,92) và khẳng định hẹp lại: **ma trận gating** cấp gắn kết không gian, Modularity cấp $K$ tự động, và độ đo khớp-nhãn một mình không đánh giá được phân cụm hướng-điều-phối.
- **Threats:** xóa lập luận "trần ARI do GT"; thay bằng: generator nay đảm bảo tách được (satellite 3 km + assertion 2 km) nên **không có trần**, khoảng hở còn lại **0,0043** là cặp S5 923 m; **cái giá** là bài toán dễ hơn thực tế → vì vậy dựa vào độ đo vận hành (đường kính, hấp thụ nhiễu, thời gian điều phối) hơn là ARI. Sửa mục "conclusion validity": Exp12 **đã** báo cáo 20 seed; vấn đề còn lại là **sd = 0,0000 của gating** cần cảnh báo (hình học cố định), chứ không phải "chưa đa seed".

### M. Xóa cảnh báo trạng thái loop 9
Sau khi hoàn tất A–L, xóa khối `⚠️ CẢNH BÁO TRẠNG THÁI` ở cả hai file.

---

## THỨ TỰ THỰC THI (Step 3)

1. `BaiBao_NoiDung.md`: §5.1 setup → §5.2 → §5.3 → §5.4 → §5.5 → §5.6 → §5.8 → §5.9 → §5.10 → thêm §5.11–5.13 (Exp10/11/12) → sửa mục Trực quan hóa → Tóm tắt → Kết luận → Threats.
2. `Paper.md`: các mục tương ứng (tài liệu ngắn hơn, chủ yếu là các đoạn tóm lược ở dòng ~191–230).
3. Xóa hai khối cảnh báo.
4. Kiểm chéo lần cuối: grep các số cũ (285, 0,892, 0,7855, 0,9651, 25 km, 0,339, 0,688, 0,730, 0,929, 0,9829, 100,07) → phải **không còn** kết quả nào trong hai file.
5. `main.tex` không đụng (đã đúng ở loop 9) — nhưng chạy lại xelatex ở cuối để chắc build vẫn sạch.
