
Ghi chú cho Tác giả — Các chỉnh sửa đã chèn vào main.tex
Bài: Stress-Testing Product-Gated Clustering and Bounded Priority Ranking for Flood-Rescue Reports — ISDS 2026 (Long paper, 12–15 trang)

1. Đánh giá bố cục sau khi thêm Algorithm
   Cách chèn Algorithm 1 và Algorithm 2 (dùng \usepackage{algorithm} + \usepackage{algpseudocode}, đặt ngay sau Fig. 1, có \caption và \label riêng, được \ref từ văn bản) là bố cục chuẩn cho hội nghị dạng Springer LNCS/CCIS: Algorithm được coi là một loại "float" độc lập, đánh số riêng với Figure/Table, không xung đột. Việc tách công thức priority thành một subroutine riêng (Algorithm 2, gọi từ Algorithm 1) cũng là cách trình bày phổ biến khi pipeline có một bước tính toán phức tạp.
   Ba điểm cần tự kiểm tra sau khi biên dịch trên Overleaf (em không có main.tex đầy đủ + references.bib + hình gốc nên không compile được ở đây):
   •	Số trang cuối cùng: bài đã có thêm ~1–1.5 trang nội dung (2 Algorithm, 1 bảng sensitivity, vài đoạn văn). Cần đảm bảo vẫn nằm trong khung 12–15 trang cho Long paper.
   •	Hai khối \begin{algorithm}...\end{algorithm} có thể trôi vị trí (float) sang trang sau tuỳ độ dài trang hiện tại — kiểm tra chúng không đè lên Table 1/Table 2 hoặc bị đẩy quá xa khỏi đoạn văn giới thiệu.
   •	Gói algpseudocode cần bản TeX Live tương đối mới; trên Overleaf mặc định là có sẵn, nhưng nếu compile báo lỗi "Undefined control sequence" quanh \Require/\Statex, đó là dấu hiệu thiếu gói — báo lại để em hỗ trợ.
2. Toàn bộ các chỗ đã chỉnh sửa trong main.tex
   Bảng dưới liệt kê theo thứ tự xuất hiện trong bài. Toàn bộ văn bản gốc được giữ nguyên; đây là những phần được thêm mới.

# Vị trí trong bài	Nội dung đã thêm

1	Dòng comment đầu file	Đổi "short paper (6–8 pages)" → "long paper (12–15 pages)" theo yêu cầu nộp Long paper.
2	Section 1 – cuối đoạn "contributions"	Câu khẳng định giá trị khoa học nằm ở kết quả âm tính (negative results) và các lỗ hổng có thể kiểm chứng, không phải ở việc cải thiện hiệu năng.
3	Section 2 – ngay sau Fig. 1	Algorithm 1 (Fail-closed observable report pipeline): pseudocode hoá toàn bộ Fig. 1 — gating admissible, tính Q_i, dựng đồ thị tương đồng, lọc quantile/top-k, phân cụm, gom family trùng lặp, gọi PriorityScore, đưa vào scheduler, rồi mới join ground truth (đường nét đứt).
4	Section 2 – ngay sau Algorithm 1	Algorithm 2 (PriorityScore): tách công thức Eq. priority thành subroutine riêng, có ghi chú [Authors: ...] cảnh báo một khả năng mâu thuẫn ký hiệu (xem mục 3.4 bên dưới).
5	Section 2.2 – cuối đoạn về similarity graph	Câu làm rõ: phép so sánh product-vs-additive với lưới quantile hiệu chỉnh độc lập là ước lượng chính (primary) cho RQ1; phép so sánh matched-density là chẩn đoán phụ (secondary).
6	Section 2.3 – cuối đoạn về priority ranking	Câu tham chiếu tới subsection Sensitivity mới (Section~\ref{sec:sensitivity}).
7	Section 3, đoạn "Endpoints and inference"	Đoạn công bố rõ 3 nhóm giả thuyết Holm correction (RQ1 clustering, RQ2 ranking, RQ3 dispatch) và các contrast cụ thể trong mỗi nhóm, kèm ghi chú [Authors: confirm...].
8	Section 4 – đầu phần Results	Đoạn tóm tắt bằng ngôn ngữ đơn giản (plain-language summary) trước khi đi vào số liệu chi tiết.
9	Section 4 – subsection mới 4.1	"Sensitivity of Heuristic Constants": mô tả phương pháp one-at-a-time ±20%, kèm bảng 8 hằng số (b0, b1, b2, ω, μ, s, N_ref, V_cap) với cột "Metric range" để trống [FILL IN].
10	Section 6 – trước phần Kết luận	Đoạn "Data and Code Availability" với chỗ trống [REPOSITORY URL] và [LICENSE].
3. Những chỗ CẦN xác minh / điền số liệu trước khi nộp
Đây là danh sách ưu tiên — bài chưa sẵn sàng nộp nếu các mục này còn để trống hoặc chưa được nhóm xác nhận.
3.1. Bảng Sensitivity (Table, \label{tab:sensitivity}) — bắt buộc
Cả 8 dòng của cột "Metric range" hiện đang là [FILL IN]. Đây là số liệu các em cần chạy lại notebook hiệu chỉnh với từng hằng số bị nhiễu ±20% (giữ nguyên các hằng số khác) và ghi lại khoảng biến động của ARI (cho b0, b1, b2) hoặc NDCG@5 (cho ω, μ, s, N_ref, V_cap) trên đúng 40 run held-out test. Không được ước lượng/suy diễn số này.
3.2. Đoạn công bố Holm family (Section 3)
Ba nhóm giả thuyết (RQ1/RQ2/RQ3) và các contrast liệt kê trong đoạn mới cần được đối chiếu trực tiếp với notebook phân tích thống kê thật — em suy ra từ các con số Holm p đã có trong Table 1/Table 2, nhưng chỉ tác giả có quyền truy cập notebook mới xác nhận được nhóm giả thuyết đúng 100%.
3.3. Data and Code Availability (Section 6)
[REPOSITORY URL] và [LICENSE] là placeholder — cần thay bằng đường dẫn kho lưu trữ thật (GitHub/Zenodo/OSF...) và giấy phép thật trước khi nộp bản camera-ready. Nếu repo chưa public tại thời điểm nộp, cân nhắc câu thay thế kiểu "available upon request / will be released upon acceptance".
3.4. Công thức Priority / Algorithm 2 — cần xác nhận với code — quan trọng
Khi soạn Algorithm 2, phát hiện: trong Eq. priority (bản gốc), các đại lượng Ē, F̄, N̄, V̄ được viết với ký hiệu lấy tổng/max trên cả "g" và "i∈g" cùng lúc. Đọc đúng nghĩa đen, điều này khiến Ē/F̄/N̄/V̄ — và do đó P — có cùng một giá trị cho MỌI family, mâu thuẫn với việc dùng P_g để xếp hạng NDCG@5 ở Section 4 (nếu mọi report có cùng priority thì không có gì để rank).
Algorithm 2 đã viết theo cách diễn giải hợp lý về mặt toán học: max/sum chỉ trong phạm vi family g đang xét (không lấy trên toàn bộ g khác). Đây là suy đoán có căn cứ, không phải xác nhận — nhóm cần đối chiếu với code tính priority thật để: (a) xác nhận Algorithm 2 đúng với cách code implement, và (b) nếu đúng, sửa lại subscript trong Eq.~\ref{eq:priority} ở bản LaTeX gốc cho khớp (bỏ ký hiệu "g" thừa, chỉ giữ "i∈g").
3.5. Kiểm tra hai Algorithm khớp với code thật
Ngoài điểm 3.4, toàn bộ Algorithm 1 được transliterate (chuyển thể) từ văn bản mô tả trong Section 2, không phải đọc trực tiếp từ source code của nhóm. Đề nghị một thành viên có quyền truy cập notebook đọc qua Algorithm 1 một lượt để xác nhận: thứ tự các bước, điều kiện routing sang review, và cách candidate pool/top-k được áp dụng khớp với implementation thật.
4. Việc cần làm trước khi nộp (checklist ngắn)
•	Điền bảng Sensitivity bằng số liệu chạy thật (mục 3.1).
•	Xác nhận 3 nhóm Holm family với notebook (mục 3.2).
•	Điền URL kho lưu trữ + license (mục 3.3).
•	Xác nhận công thức priority per-family, sửa Eq. nếu cần, đối chiếu Algorithm 2 (mục 3.4).
•	Đọc lại Algorithm 1 so với code thật (mục 3.5).
•	Biên dịch bằng XeLaTeX trên Overleaf và kiểm tra số trang cuối cùng (12–15 trang) cùng vị trí trôi nổi của 2 Algorithm.
