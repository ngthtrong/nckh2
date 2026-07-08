
1. Phản biện về thực nghiệm (điểm yếu lớn nhất hiện tại)
   a) Toàn bộ kết quả dựa trên dữ liệu synthetic — đây là gót chân Achilles. Người phản biện sẽ đánh ngay: "ARI 0,89 nghĩa là gì khi chính bạn sinh raground-truth?" Dữ liệu tự sinh với6 cụm Gaussian tách biệt thì gần như bất kỳ thuật toán không gian nào cũng thắng — con số0,89 nói lên độ tách của dữ liệu bạn tạo, không phải sức mạnh phương pháp. Đề xuất: chạyít nhất một phần trên dữ liệu thật (CrisisMD/FlodNet có geotag, hoặc tập tin nhắn Zalo/Facebook bạn crawl như thuyết minh đã hứa), dù chỉ để định tính. Nếu không kịp, phải nói rất rõ trong Limitations rằng đây là "prof-concept trên dữ liệu mô phỏng".

b) So sánh baseline chưa công bằng (chery-picking). Bạn so Louvain trên đồ thị gating với K-Means/DBSCAN trên tọa độ thô. Louvain thắng phần lớn là nhờ đồ thị, không phải nhờ thuật toán cộng đồng. Baseline trung thực phải là:

K-Means/DBSCAN trên cùng ma trận đặc trưng đa chiều (hoặc trên ma trận khoảng cách $1-w_{ij}$), không chỉ trên lat/lng.
Thêm HDBSCAN và Spectral Clustering (spectral ăn trực tiếp ma trận affinity $w_{ij}$ — đây mới là đối thủ thật của bạn).
Quan trọng nhất: ablation "Louvain trên đồ thị additive vs gating" — bạn đã có (exp1A) nhưng nên đưa lên thành baseline chính, vì nó cô lập đúng đóng góp của bạn.
c) Đường kính 100 km → 0,30 km ngheấn tượng nhưng gần như tautology. Gating với $\sigma_{geo}=700$m định nghĩa rằng cạnh xa bị cắt, nên tất nhiên đường kính co lại. Nó chứng minh code chạy đúng, không chứng minh một khám phá. Giá trị thật nằm ở chỗ: gating co đường kính mà KHÔNG giảm ARI (0,89 giữ nguyên). Hãy đóng khung kết quả theo hướng đó, đừng bán con số 100 km như thành tựu.

d) exp3 (Louvain vs Leiden: 0 cụm đứt gãy cả hai) đang được trình bày trung thực — giữ nguyên. Nhưng người phản biện sẽ hỏi "vậy nhắc Leiden làm gì?". Câu trả lời của bạn ("bảo hiểm miễn phí") ổn, nhưng nên bổ sung: chạy trên đồ thị additive/dày đặc để tạo ra cụm đứt gãy và cho thấy Leiden sửa được — khi đó việc nhắc Leiden mới có sức nặng thực nghiệm thay vì chỉ lý thuyết.

2. Phản biện về công thức
   a) $\mathcal{S}{context}$ trộn $F$ (đã dùng ở $\mathcal{F}{max}$) và $E$ (đã dùng ở $\mathcal{E}_{ag}$) — nguy cơ double-counting. Cùng một biến vừa quyết định ai vào cụm nào (weighting) vừa quyết định cụm nào ưu tiên (priority). Không sai, nhưng phải tho luận, vì một phản biện tinh ý sẽ chỉ ra rằng cụm gom theo $F$ tương đồng thì $\mathcal{F}_{max}$ của cụm đó gần như được đảm bảo cao — hơi vòng tròn.

b) $N_{\max}$ trong chuẩn hóa $\widetilde{\mathcal{N}}$ là "cụm lớn nhất trong cửa sổ hiện tại" → thang đo trôi (non-stationary). Cùng một cụm sẽ có $\mathcal{P}$ khác nhau tùy các cụm khác xuất hiện cùng lúc. Hai vấn đề: (i) không so sánh được across time; (ii) một cụm khổng lồ đơn lẻ làm co toàn bộ phần còn lại về~0. Cân nhắc mốc cố định (dân số tham chiếu theo địa bàn) hoặc nêu rõ đây là ranking tương đối tức thời, không phải điểm tuyệt đối.

c) $\max$ trong $\mathcal{F}_{max}$ nhạy với outlier / tin giả. Một báo cáo giả $F=1.0$ lọt vào cụm sẽ chiếm trọn $\mathcal{F}{max}$. Bạn gate $C_i$ cho $\mathcal{E}$ và $\mathcal{N}$ nhưng **không gate cho $\mathcal{F}{max}$** — lỗ hổng nhất quán. Cân nhắc $\max_i (F_i \cdot C_i)$ hoặc percentile 90 thay vì max tuyệt đối.

d) Trọng số $\omega$ và $\beta,\gamma,s,\sigma_{geo}$ đều đặt tay. Phản biện sẽ hỏi độ nhạy. Bạn có exp2 (tốt), nhưng nên thêm: kết quả xp hạng $\mathcal{P}$ có ổn định khi $\omega$ dao động không? (rank correlation Kendall's τ giữa các bộ $\omega$).

3. Phản biện về lập luận
   Vòng lặp logicở Khe hở 2: bạn nói "thiếu vulnerability" là gap, rồi "giải pháp là thêm vulnerability" — đúng, nhưng chưa chứng minh bằng dữ liệu rằng thêm nó thay đổi quyết định cứu hộ theo hướng tốt hơn. exp1C cho thấy nó đổi ranking, nhưng "đổi" ≠ "đúng hơn". Cần một lập luận/ví dụ chuẩn tắc (normative) tại sao ranking mới công bằng hơn.
   "Golden hour", "sub-500ms", "MB→KB" đang dựa vào blog/vendor. Những claim định lượng này cần nguồn per-reviewed (xem kết quả agent bên dưới).
   Thiếu hẳn phần "threats to validity" — chuẩn mực trong bài báo hệ thống/ML.
4. Về việc thiếu so sánh với nghiên cứu cùng lĩnh vực (đúng như bạn nhận xét)
   Đây là thiếu sót thật. Bài hiện mô tả related work nhưng không có bảng so sánh định vị (positioning table): cột = các trục [đa phương thức / edge / đồ thị trọng số / vulnerability / priority cấp cụm], hàng = CrisisSpot, TwitterNews+, ResQConnect, EmergencyNet, các paper KG thảm họa... và ✓/✗ để cho thấy ô trống mà bạn lấp. Đây là cách thuyết phục nhất để justify novelty.

Để tôi chờ kết quả 3 agent về độ xác thực trích dẫn rồi tổng hợp danh sách trích dẫn nào cần thay và gợi ý nguồn thay thế.
