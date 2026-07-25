# Loop 12 — Báo cáo Phản biện (Step 1)

**Vai trò:** Giáo sư chủ tịch hội đồng phản biện, soi **học thuật vụ** (scholarship): trích dẫn, thư mục, phần Related Work, và mọi khẳng định về công trình của **người khác**. Loops 9–11 đã dọn số liệu và công thức. Loop 12 hỏi câu khác: **những gì bài nói về thế giới bên ngoài có được chống lưng không?**

Phạm vi: `paper/main.tex` (Related Work, Gaps, Positioning, Metrics), `paper/references.bib`.

---

## ĐÃ KIỂM ĐẦU TIÊN — cân đối trích dẫn HOÀN HẢO (ghi nhận)

Đối chiếu tự động 23 khóa BibTeX với 23 khóa được `\cite`:
- **0 khóa được cite nhưng thiếu trong .bib** (không có reference treo).
- **0 khóa trong .bib nhưng không được cite** (không có entry rác).
- Build LaTeX: 0 undefined citation.

Đây là trạng thái tốt hơn phần lớn bản thảo nộp hội nghị. Không có việc phải làm ở tầng này.

---

## CHẤT VẤN 12.1 — Bảng Positioning có một hàng **KHÔNG PHẢI một công trình** (NGHIÊM TRỌNG về học thuật vụ)

**Nơi xuất hiện:** Bảng~\ref{tab:positioning} (dòng 101):
```
Event detection (TF-IDF) & & & $\checkmark$ & & \\
```

Bốn hàng còn lại đều là công trình cụ thể có trích dẫn: CrisisSpot~\cite{dar2024crisisspot}, EmergencyNet~\cite{kyrkou2020emergencynet}, Vulnerability prioritization~\cite{gralla2014review}, và "Proposed framework". Hàng thứ hai là **"Event detection (TF-IDF)" không có trích dẫn nào** — một mô tả chung chung về cả một dòng nghiên cứu.

**Vì sao đây là lỗi thật, không phải chuyện nhỏ:** một bảng positioning tồn tại để nói "công trình X có năng lực A, B; chúng tôi có A, B, C". Đặt một **phạm trù trừu tượng** vào cùng cột với các công trình đích danh khiến hàng đó **không thể kiểm chứng và không thể phản bác**. Phản biện sẽ hỏi: TF-IDF event detection *nào*? Của ai? Nếu không nêu được thì hàng này chỉ là bù nhìn để làm nền cho cột trống mà bài tuyên bố là "khe hở".

Tệ hơn, câu ngay dưới bảng (dòng 89) khẳng định: "**No prior work** simultaneously (i)...(iv). That empty cell is the gap this paper fills." Một khẳng định "không công trình nào" đang được chống lưng bởi một bảng mà **một trong năm hàng không phải công trình**.

**Liên quan:** dòng 83 cũng viết "**Event-detection studies typically** build weighted graphs from spatiotemporal proximity and keyword co-occurrence (e.g., TF-IDF similarity). **Advanced models** incorporate Euclidean/Haversine distance to penalize links..." — hai khẳng định về hiện trạng cả một dòng nghiên cứu, **không một trích dẫn nào** trong cả đoạn. Đây chính là đoạn thiết lập khe hở nghiên cứu, nên nó là chỗ **cần** trích dẫn nhất trong bài.

---

## CHẤT VẤN 12.2 — Khẳng định về pose estimation đo độ sâu nước: không nguồn (TRUNG BÌNH)

Dòng 77: "...**some work applies human pose estimation to infer water depth** where no physical gauges exist."

Không trích dẫn. Và đây không phải kiến thức phổ thông — nó là một kỹ thuật cụ thể, khá đặc thù. Nặng hơn: khẳng định này **được tái sử dụng như một cam kết kỹ thuật của chính bài báo** ở dòng 184 ("$F_i$ physical flood level (MobileNetV3 segmentation/**pose estimation**)") và dòng 187 ("dedicated crowd counting/**pose estimation** for $N_i$"). Tức bài dựa vào một khả năng của người khác để biện minh tính khả thi của thiết kế của mình, mà không chỉ ra được người khác đó là ai.

**Câu hỏi gay gắt:** Nếu không có nguồn cho "pose estimation suy ra độ sâu nước", thì cơ sở nào để nói $F_i$ trích xuất được ở biên bằng cách đó?

---

## CHẤT VẤN 12.3 — "UIT-VSMEC" xuất hiện không giải thích, không trích dẫn (TRUNG BÌNH)

Dòng 184: "$E_i\in[0,1]$ urgency (DistilBERT/**UIT-VSMEC** text sentiment)".

UIT-VSMEC là một **bộ dữ liệu cảm xúc tiếng Việt** cụ thể (Vietnamese Social Media Emotion Corpus). Trong bài nó xuất hiện **đúng một lần**, không định nghĩa từ viết tắt, không trích dẫn, và người đọc quốc tế của LNCS không có cách nào biết nó là gì. Với một bài báo tiếng Anh gửi hội nghị quốc tế, một acronym địa phương không nguồn là lỗi trình bày thật.

---

## CHẤT VẤN 12.4 — "gold standard" là ngôn ngữ quảng cáo, không phải mệnh đề khoa học (TRUNG BÌNH)

Dòng 86: "Network-topology methods, notably **Louvain**~\cite{blondel2008louvain}, are the **gold standard** for weighted-graph clustering".

Ba vấn đề:
1. "Gold standard" là một khẳng định về **sự đồng thuận của cộng đồng**, không phải một tính chất đo được, và nó được gán cho `blondel2008louvain` — bài báo *giới thiệu* Louvain, nên không thể là nguồn cho việc phương pháp đó **về sau** trở thành chuẩn mực.
2. Nó **tự đâm vào lập luận của chính bài**: Exp4 kết luận thẳng rằng Agglomerative khớp Louvain **chính xác** và HDBSCAN vượt Louvain về ARI. Bài đã can đảm hạ tuyên bố xuống "ưu thế là không cần $K$". Gọi Louvain là "gold standard" ở Related Work rồi tự bác ở Experiments là **không nhất quán về giọng**.
3. Nếu muốn giữ một mệnh đề mạnh, `fortunato2010community` (khảo sát) là nguồn hợp lý hơn nhiều cho tuyên bố về vị thế trong cộng đồng.

**Kèm theo, cùng dòng:** "with **observed** near-$\mathcal{O}(N\log N)$ runtime". Kiểm chứng độc lập: độ phức tạp của Louvain **chưa từng được chứng minh chặt**; các nguồn khác nhau nêu $O(n\log n)$ hoặc "về cơ bản tuyến tính theo số cạnh", và phân tích worst-case có thể lên $O(n^2)$. Bài đã cẩn thận dùng chữ "**observed**" (quan sát được) thay vì khẳng định lý thuyết → **đúng cách, không phải lỗi**. Ghi nhận là đã kiểm, giữ nguyên.

---

## CHẤT VẤN 12.5 — "DBSCAN sensitive to high dimensionality" gán sai cho nguồn (NHỎ nhưng là lỗi quy nguồn)

Dòng 86: "**DBSCAN**~\cite{ester1996dbscan} is **sensitive to high dimensionality** and parameters."

Ester et al. 1996 là bài **giới thiệu** DBSCAN; nó không phải công trình phân tích điểm yếu chiều cao của DBSCAN (đó là văn liệu về curse of dimensionality xuất hiện sau). Khẳng định thì **đúng về bản chất**, nhưng quy nó cho bài gốc là quy nguồn không chính xác — bài gốc không nói vậy về chính nó.

Ngoài ra, trong bối cảnh của **bài này**, khẳng định "chiều cao" hơi lệch chỗ: DBSCAN ở đây được chạy trên **tọa độ 2 chiều** (`exp4`: "DBSCAN (eps 0.3, coords)"). Nên điểm yếu thực sự bị phơi ra trong thực nghiệm là **độ nhạy tham số eps** và **hấp thụ 100% nhiễu**, không phải chiều cao. Lập luận sẽ mạnh hơn nếu nêu đúng điểm yếu mà chính bài đo được.

---

## CHẤT VẤN 12.6 — Số liệu bão đã có nguồn, nhưng nguồn **không kiểm chứng được công khai** (NHỎ, ghi nhận rủi ro)

Dòng 55: "roughly 6--8 typhoons... (out of the $\sim$11...)~\cite{isponre2009varcc}".

Entry là `@techreport` ISPONRE 2009, **không có URL, không có DOI, không số báo cáo**. Loop 7 đã kiểm chéo con số này với nguồn độc lập và thấy khớp (6–8 ảnh hưởng VN, 11–13 vào Biển Đông), nên **con số đúng**. Nhưng một reviewer muốn tra nguồn thì không có đường dẫn nào. Nên thêm `note` hoặc `url` nếu có; nếu không, ít nhất cũng nên có một nguồn thứ hai dễ tra hơn.

---

## ĐÃ KIỂM — KHÔNG PHẢI LỖI (giữ nguyên, khỏi soi lại)

- **23/23 trích dẫn cân đối**, không treo, không rác (xem trên).
- **CrisisSpot F1 5,01–9,45%**: khớp `dar2024crisisspot`, entry có **DOI đầy đủ** — đây là entry chất lượng cao nhất trong bib. Loop 4 đã kiểm.
- **Các entry kinh điển** đều đúng thông tin xuất bản: Blondel 2008 (JSTAT, P10008) ✓, Newman–Girvan 2004 (PRE 69, 026113) ✓, Traag 2019 (Sci Rep 9, 5233) ✓, Reichardt–Bornholdt 2006 (PRE 74, 016110) ✓, Fortunato 2010 (Phys Rep 486, 75–174) ✓, Hubert–Arabie 1985 (J Classification 2, 193–218) ✓, Kendall 1938 (Biometrika 30, 81–93) ✓, von Luxburg 2007 (Stat Comput 17, 395–416) ✓, Ester 1996 (KDD, 226–231) ✓, MacQueen 1967 (Berkeley Symp) ✓, Saaty 1980 (AHP) ✓, Imran 2015 (ACM CSUR 47(4)) ✓.
- **Nguồn cho mỗi độ đo** đều có: ARI~\cite{hubert1985comparing}, Kendall~\cite{kendall1938new}, Modularity~\cite{newman2004finding}, dạng resolution~\cite{reichardt2006statistical}, AHP~\cite{saaty1980ahp} — đúng chuẩn, không thiếu chỗ nào.
- **Mỗi baseline có trích dẫn**: Spectral~\cite{vonluxburg2007spectral}, HDBSCAN~\cite{campello2013hdbscan}, K-Means, DBSCAN ✓.
- **Gap 2 có hai nguồn** (`vitoriano2011multicriteria`, `gralla2014review`) ✓ — khe hở được chống lưng tử tế.
- `campello2013hdbscan` ghi journal là "Advances in Knowledge Discovery and Data Mining (PAKDD)" trong khi đây là **proceedings** (nên là `@inproceedings`). Lỗi loại entry rất nhỏ, `splncs04.bst` vẫn render được → không đáng sửa, ghi nhận.

---

## TỔNG KẾT STEP 1

Cân đối trích dẫn hoàn hảo, thư mục chất lượng tốt. Vấn đề còn lại tập trung ở **đoạn thiết lập khe hở nghiên cứu** — đúng chỗ mà một bài báo cần chắc nhất:

1. **12.1** — Bảng Positioning có hàng "Event detection (TF-IDF)" **không phải một công trình và không có trích dẫn**, trong khi bài dùng bảng đó để khẳng định "no prior work". Cả đoạn §2.3 mô tả hiện trạng dòng nghiên cứu này **không có trích dẫn nào**. NGHIÊM TRỌNG.
2. **12.2** — "pose estimation suy ra độ sâu nước" không nguồn, nhưng được dùng để biện minh tính khả thi trích xuất $F_i$. TRUNG BÌNH.
3. **12.3** — "UIT-VSMEC" xuất hiện một lần, không giải thích, không trích dẫn, trong bài tiếng Anh. TRUNG BÌNH.
4. **12.4** — "gold standard" cho Louvain là ngôn ngữ quảng cáo, gán sai nguồn, và **tự mâu thuẫn** với kết luận Exp4 của chính bài. TRUNG BÌNH. (Vế "observed near-$O(N\log N)$" thì **đúng cách**, giữ.)
5. **12.5** — "DBSCAN sensitive to high dimensionality" quy sai cho bài gốc, và lệch với điểm yếu mà chính thực nghiệm đo được (eps + hấp thụ nhiễu, trên dữ liệu 2 chiều). NHỎ.
6. **12.6** — entry ISPONRE không có URL/DOI nên reviewer không tra được, dù con số đã kiểm chéo là đúng. NHỎ.
