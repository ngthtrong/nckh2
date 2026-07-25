# Loop 12 — Kế hoạch Giải quyết (Step 2)

**Vai trò:** Tác giả. Ràng buộc chi phối loop này: **`promt-loop.md` cấm bịa dữ liệu**. Với lỗi thiếu trích dẫn, có hai cách sửa hợp lệ và **một cách không hợp lệ**:
- ✅ Thêm trích dẫn thật mà ta **chắc chắn** về thông tin xuất bản.
- ✅ **Viết lại mệnh đề** để nó không còn cần một nguồn mà ta không có.
- ❌ Bịa một entry BibTeX trông giống thật (số volume, số trang phỏng đoán). **Tuyệt đối không.**

Tôi đã thử tìm nguồn qua web search cho từng khẳng định; kết quả không dùng được. Vì vậy kế hoạch dưới đây chỉ thêm những entry mà tôi tự tin về **tác giả + tiêu đề + hội nghị/tạp chí + năm**, và **viết lại** phần còn lại.

---

## 12.1 — Bảng Positioning + đoạn §2.3 không trích dẫn — CHẤP NHẬN, sửa bằng **hai bước**

**Thừa nhận:** Đúng, và đây là lỗi học thuật vụ nặng nhất của bài. Một bảng dùng để chống lưng khẳng định "no prior work" thì không được có hàng là một **phạm trù** thay vì một **công trình**.

### Bước 1 — Thêm hai trích dẫn thật cho dòng nghiên cứu event detection

Hai công trình tôi tự tin về thông tin xuất bản:

```bibtex
@inproceedings{sakaki2010earthquake,
  title={Earthquake shakes Twitter users: real-time event detection by social sensors},
  author={Sakaki, Takeshi and Okazaki, Makoto and Matsuo, Yutaka},
  booktitle={Proceedings of the 19th International Conference on World Wide Web (WWW)},
  pages={851--860},
  year={2010}
}

@article{atefeh2015survey,
  title={A survey of techniques for event detection in Twitter},
  author={Atefeh, Farzindar and Khreich, Wael},
  journal={Computational Intelligence},
  volume={31},
  number={1},
  pages={132--164},
  year={2015},
  publisher={Wiley}
}
```

Cả hai là công trình nền tảng đúng chủ đề: Sakaki là bài kinh điển về social-sensing phát hiện sự kiện có yếu tố **không gian–thời gian** (đúng thứ §2.3 đang mô tả), Atefeh–Khreich là **khảo sát** nên là nguồn hợp lệ cho một khẳng định về "các nghiên cứu thường làm gì".

**Ghi chú cho nhóm tác giả:** hai entry này cần đối chiếu lần cuối với bản gốc trước khi nộp (tôi tự tin về tác giả/tiêu đề/venue/năm, nhưng số trang nên xác nhận lại). Đây là ghi chú trung thực, không phải chỗ để phỏng đoán thêm.

### Bước 2 — Sửa bảng và đoạn văn

1. **Bảng Positioning dòng 101:** `Event detection (TF-IDF)` → `Event detection~\cite{sakaki2010earthquake,atefeh2015survey}` — biến hàng phạm trù thành hàng có công trình đích danh.
2. **Dòng 83 (§2.3):** thêm trích dẫn vào hai khẳng định hiện trần:
   - "Event-detection studies typically build weighted graphs from spatiotemporal proximity and keyword co-occurrence (e.g., TF-IDF similarity)~\cite{sakaki2010earthquake,atefeh2015survey}."
   - Câu "Advanced models incorporate Euclidean/Haversine distance to \emph{penalize} links between distant events, forming geo-semantic graphs" — **không có nguồn cụ thể** nên phải **hạ cấp mệnh đề**: đổi từ khẳng định về văn liệu thành phát biểu về **thiết kế khả dĩ** mà bài sẽ so sánh với. Viết lại: "A natural extension is to let Euclidean/Haversine distance \emph{penalize} links between distant events, forming a geo-semantic graph; that additive penalty is precisely the design we compare against in Sect.~\ref{sec:exp1}, and it still omits flood depth and demographic vulnerability."
   
   Cách này **mạnh hơn** bản cũ: thay vì khẳng định mơ hồ về công trình người khác, nó nối thẳng vào baseline additive mà bài **thật sự đo** ở Exp1.
3. **Dòng 89:** làm mềm "No prior work simultaneously..." → "To our knowledge, no prior work simultaneously..." — một khẳng định phủ định toàn thể luôn cần hedge này.

---

## 12.2 — "pose estimation suy ra độ sâu nước" không nguồn — CHẤP NHẬN, **bỏ khẳng định**

**Thừa nhận:** Đúng. Tôi không có nguồn chắc chắn cho kỹ thuật cụ thể này, và nó lại đang được dùng để biện minh tính khả thi trích xuất $F_i$ — tức một khẳng định không nguồn đang chống lưng cho thiết kế của chính bài. Không được để vậy.

**Không bịa nguồn.** Thay vào đó bỏ vế đó và giữ phần có nguồn:
- **Dòng 77:** xóa "; some work applies human pose estimation to infer water depth where no physical gauges exist". Phần còn lại (ResNet/MobileNetV3, semantic segmentation) đã có `howard2019mobilenetv3` chống lưng.
- **Dòng 184:** "$F_i\in[0,1]$ physical flood level (MobileNetV3 segmentation/pose estimation)" → bỏ "pose estimation", giữ "(MobileNetV3 semantic segmentation)".
- **Dòng 187:** "(dedicated crowd counting/pose estimation for $N_i$...)" — ở đây pose estimation được nêu như **future work của chính nhóm**, không phải khẳng định về văn liệu, nên **hợp lệ**; giữ nguyên.

Phân biệt này quan trọng: nói "chúng tôi dự định thử X trong tương lai" không cần trích dẫn; nói "có công trình đã làm được X" thì cần.

---

## 12.3 — UIT-VSMEC — CHẤP NHẬN, viết lại mô tả

Không thêm entry vì tôi không đủ tự tin về thông tin xuất bản đầy đủ của bộ dữ liệu này, và bịa số volume/trang là vi phạm ràng buộc.

**Sửa dòng 184:** "(DistilBERT/UIT-VSMEC text sentiment)" → "(a DistilBERT sentiment/urgency classifier fine-tuned on a Vietnamese social-media corpus)".

Vừa bỏ acronym địa phương không giải thích, vừa nói rõ hơn *cái gì* làm việc gì cho người đọc quốc tế, mà không cần một trích dẫn ta không có. Nếu nhóm có sẵn trích dẫn UIT-VSMEC chuẩn thì thêm sau — ghi chú lại trong plan này.

---

## 12.4 — "gold standard" — CHẤP NHẬN, sửa

**Thừa nhận:** Đúng cả ba điểm, và điểm thứ hai đáng ngại nhất: bài **tự bác** tuyên bố này ở Exp4 (Agglomerative khớp chính xác, HDBSCAN vượt ARI). Giữ "gold standard" ở Related Work rồi hạ giọng ở Experiments là không nhất quán.

**Sửa dòng 86:** "are the gold standard for weighted-graph clustering via optimization of the \textbf{Modularity} function" →
> "are **widely adopted** for weighted-graph clustering via optimization of the \textbf{Modularity} function~\cite{newman2004finding}, and are surveyed as a standard family by Fortunato~\cite{fortunato2010community}"

"Widely adopted" là mệnh đề kiểm chứng được và đủ cho mục đích; và nó **không hứa hẹn** một ưu thế mà Exp4 sẽ phủ nhận.

**Giữ nguyên** "observed near-$\mathcal{O}(N\log N)$ runtime": đã kiểm chứng độc lập rằng độ phức tạp Louvain chưa được chứng minh chặt (các nguồn nêu $O(n\log n)$ hoặc tuyến tính theo số cạnh, worst-case có thể $O(n^2)$), và chữ "**observed**" của bài đúng là cách hedge chuẩn. Không đụng.

---

## 12.5 — DBSCAN "high dimensionality" — CHẤP NHẬN, đổi sang điểm yếu **bài thật sự đo được**

**Thừa nhận:** Đúng. Quy khẳng định về điểm yếu cho bài *giới thiệu* DBSCAN là quy nguồn không chính xác; và trong bài này DBSCAN chạy trên tọa độ **2 chiều** nên "chiều cao" lệch chỗ.

**Sửa dòng 86:** "\textbf{DBSCAN}~\cite{ester1996dbscan} is sensitive to high dimensionality and parameters." →
> "\textbf{DBSCAN}~\cite{ester1996dbscan} avoids a preset $K$ but is sensitive to its density parameters, and---as Sect.~\ref{sec:exp4} shows on our data---absorbs unlabeled noise wholesale."

Lợi ích kép: quy nguồn thành trung tính (chỉ trỏ bài gốc cho *thuật toán*, không cho *phê phán*), và điểm yếu nêu ra là chính điểm yếu **bài đã đo** (eps + hấp thụ 100% nhiễu), nên Related Work và Experiments khớp nhau.

---

## 12.6 — Entry ISPONRE không tra được — CHẤP NHẬN, thêm `note`

Con số 6–8 / ~11 đã kiểm chéo ở loop 7 và đúng, nên **không đổi con số**. Chỉ thêm trường giúp tra:
```bibtex
  note={National assessment report; figures cross-checked against independent tropical-cyclone climatology for Vietnam}
```
Không thêm URL vì tôi không có URL chính thức xác thực — thêm URL đoán là bịa.

---

## THỨ TỰ THỰC THI (Step 3)

1. `references.bib`: thêm `sakaki2010earthquake`, `atefeh2015survey`; thêm `note` cho `isponre2009varcc`.
2. `main.tex` dòng 77: bỏ vế pose estimation.
3. `main.tex` dòng 83: thêm 2 trích dẫn; viết lại câu "Advanced models" thành phát biểu nối vào baseline Exp1.
4. `main.tex` dòng 86: "gold standard" → "widely adopted" + Fortunato; sửa mệnh đề DBSCAN.
5. `main.tex` dòng 89: thêm "To our knowledge".
6. `main.tex` dòng 101 (bảng): hàng TF-IDF → có trích dẫn.
7. `main.tex` dòng 184: bỏ pose estimation, thay UIT-VSMEC bằng mô tả.
8. Bản Việt: kiểm và đồng bộ các chỗ tương ứng (pose estimation, UIT-VSMEC, gold standard) bằng grep.
9. Biên dịch: `xelatex → bibtex → xelatex ×2`. Yêu cầu: 0 undefined citation, 25 entry thư mục (23 + 2 mới), 0 multiply-defined.
10. Kiểm lại cân đối trích dẫn bằng script comm như ở Step 1 — phải vẫn 0/0.
