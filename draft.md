
Đã kiểm chứng xong. Dưới đây là bản phản biện của tôi vớiư cách reviewer.

Phản biện: "Weighted Graph-Based Event Clustering and Priority Scoring for Flood-Rescue Coordination Using Edge AI"
Kết luận tổng thể: Major Revision (nghiêng về Reject nếu nhắm hội nghị hạng A).

Bài báo có văn hoá báo cáo trung thực đáng khen — hiếm thấy một bản thảo tự bác bỏ tuyên bố chính của mình (Thí nghiệm 13). Nhưng chính sự trung thực đó lại phơi ra vấn đề: sau khi trừ hết những gì các tác giả tự thu hồi, phần đóng góp còn lại không đủ cho một bài báo, và ba trong số các con số còn sót lại cũng không đứng vững khi tôi kiểm tra lại bằng code của chính các tác giả.

1. Vấn đề nghiêm trọng nhất: "cửa sổ51×" là một artifact của cách chọn thước đo
   Đây là tuyên bố duy nhất còn sót lại sau Thí nghiệm 13, đượcặt vào abstract, kết luận và toàn bộ phần định vị đóng góp. Nó không đứng vững.

Từ exp13_theta_ranges.json:

| Dạng | Cửa sổ dùng được | Tỉ số (báo cáo) | Độ rộng tuyệt đối |
|---|---|
| Gating | [0.01, 0.51] | 51.0× | 0.50 |
| Additive α=1.0 | [0.96, 1.46] | 1.5× | 0.50 |

Hai cửa sổ rộng bằng nhau chính xác đến từng chữ số. Con số 51× chỉ tồn tại vì cửa sổ của gating bắt đầu gần 0, mà tỉ số $\theta_{hi}/\theta_{lo}$ phân kỳ khi $\theta_{lo}\to 0$. Đây là một đại lượng không bất biến theo tái tham số hoá: nếu chẩn hoá $\theta$ theo $w_{\max}$ của từng dạng (0.988 cho gating, 1.988 cho additive — số từ chính exp13_theta_ranges.json), cửa sổ trở thành [0.010, 0.516] so với [0.483, 0.734], tức 0.51 so với 0.25 — lợi thế 2×, không phải 51×. Nếu đo bằng độ rộng tuyệt đối thì lợi thế bằng 1×.

Nói cách khác, phát biểu đúng duy nhất là: cửa sổ của gating chứa gốc toạ độ, nên mọi $\theta$ nhỏ đều dùng được. Điều đó đúng, nhưng nó chỉ là cách phát biểu lại một sự thật tầm thường: $\mathcal{S}_{geo}$ đã triệt tiêu các cặp xa nên đồ thị đã thưa trước khi $\theta$ được áp. Không cần một bảng thí nghiệm và con số 51× để nói điều này, và tuyệt đối không nên đặt nó làm đóng góp trung tâm.

Yêu cầu: bỏ con số 51× hoặc thay bằng một đại lượng bất biến theo thang đo (ví dụ tỉ lệ cạnh giữ lại, hoặc $\theta$ chuẩn hoá theo $w_{\max}$/phân vị), và phát biểu lại đóng góp cho tương ứng.

2. Trên dữ liệu này, phương pháp thực chất là một ngưỡng khoảng cách
   Với $\sigma_{geo}=700$ m và $(\beta\mathcal{S}{temp}+\gamma\mathcal{S}{ctx})\le 1$, điều kiện $w_{ij}>0.05$ bắt buộc $\mathcal{S}_{geo}>0.05$, tức $d < 700\sqrt{2\ln 20} \approx 1710$ m. Toàn bộ đồ thị gating ở tham số mặc định không thể khác một đồ thị "nối mọi cặp cách nhau dưới ~1.7 km" nhiều hơn một chút về trọng số cạnh.

Chính các thí nghiệm của bài báo xác nhận điều này, và cả bốn cùng chỉ về một hướng:

Thí nghiệm 6: xoá hẳn $\mathcal{S}_{context}$ → phân hoạch bit-identical, $\tau=1.0$.
Thí nghiệm 2: quét toàn bộ lưới $\tau_F,\tau_E\in[0.15,0.5]$ → ARI và số cụm không đổi.
Thí nghiệm 4: Agglomerative trên cùng ma trận → trùng khớp tuyệt đối cả bốn chỉ số.
Tôi chạy lại pipeline: 74 cụm = 13 cụm thật + 61 singleton, và 61 singleton đó là đúng 61 điểm nhiễu gt=-1. Phân hoạch được phục hồi trọn vẹn ngoại trừ cặp 106/107.
Hệ quả: vector 7 chiều $(L,T,F,E,N,V,C)$ — điểm bán chính của bài — không đóng góp gì cho bước phân cụm. Chỉ có $(L)$ hoạt động. Phần "spatial–semantic–physical" trong tiêu đề Mục 4.2 không được dữ liệu ủng hộ. Bài báo có thừa nhận điều này ở Mục 6.6 nhưng vẫn giữ nguyên framing ở tiêu đề, abstract và Bảng 1 (dòng "Weighted graph ✓ (gating)").

Ngoại lệ duy nhất ($\beta=0.9$, ARI 0.9509) là một trường hợp tự tạo: cặp S5 cách 923 m được đặt vào dataset chính để làm $\gamma$ có việc làm. Một tham số chỉ chứng minh được giá trị của mình trên một cặp điểm được thiết k riêng cho nó thì chưa phải bằng chứng.

3. Dataset quyết định kết quả, không phải phương pháp
   Từ generate.py: 6 đảo với spread_m=250, các nhóm narative đặt trên vệ tinh cách tâm 3 km, cộng assert_gt_separable(min_sep_m=2000). Khoảng cách trong nhóm ~vài trăm mét; giữa nhóm ≥ 2 km. Bất kỳ phương pháp nào có ngưỡng cắt nằm giữa 1 và 2 km đều thu được đáp án gần hoàn hảo.

ARI = 0.9957 vì vậy đo tính khả tách của generator, không đo năng lực của phương pháp. Bài báo nói điều này trong Threats to Validity — nhưng rồi vẫn dùng ARI làm con số headline trong abstract, và tệ hơn, dùng nó làm tiêu chí "usable" ($\text{ARI}\ge 0.95$) của Thí nghiệm 13. Toàn bộ kết quả hiệu chuẩn $\theta$ thừa hưởng vấn đề này.

Việc thêm assertion khả tách để sửa lỗi co-location của phiên bản trước đã làm bài toán dễ hơn, không khó hơn. Một dataset mà ground truth bị bắt buộc phải tách được về không gian thì không thể dùng để chứng minh giá trị của một cơ chế gating không gian — vì cơ chế đó được đảm bảo thắng bởi cấu trúc dữ liệu.

4. ROC-AUC 0.9176 của bộ phát hiện tin giả là artifact, không phải năng lực phát hiện
   Đây là phát hiện tôi cho là nghiêm trọng nhất về mặt tính đúng đắn, vì bài báo trình bày nó như một kết quả định lượng có khoảng tin cậy bootstrap.

Tôi đo lại trên chính dữ liệu và công thức của các tác giả:

mean n_corrob:  fake 0.00 | real trong đảo 14.84 | real rải rác 0.00
AUC(-n_corrob) một mình = 0.9355   (cao hơn cả C_i)

Giới hạn vào 61 điểm rải rác (23 fake vs 38 real) — phép so sánh không tầm thường duy nhất:
  AUC(-C_i) = 0.4319          (dưới ngưỡng ngẫu nhiên 0.5)
  AP (-C_i) = 0.3495  vs baseline ngẫu nhiên 0.3770   (tệ hơn ngẫu nhiên)
Nguyên nhân: cả 23 tin giả đều nằm trong tập nhiễu rải rác, nên $n^{\text{corrob}}=0$; còn mọi báo cáo thật trong đảo có ~15 láng giềng. $C_i$ vì thế phân biệt "điểm này có nằm trong vùng dày đặc hay không", mà điều đó trùng khít với việc điểm có nhãn hay không — tức trùng khít với biến đích, qua một đường không liên quan gì đến tính giả mạo. Khi loại bỏ đường tắt đó, $C_i$ kém hơn đoán bừa.

Tương tự, "giảm 55% dân số ảo" không phải kết quả phát hiện: nó là phép nhân với $C_i=0.4502$, và 0.4502 đến từ việc generator gán cho báo cáo S3 giá trị has_image=False và đặt nó cô lập. Con số 55% được quyết định bởi $(b_0,b_1,b_2)$ do tác giả chọn, không bởi dữ liệu.

Yêu cầu: hoặc rút Thí nghiệm 8 và mọi tuyên bố phát hiện tin giả (bao gồm trong abstract), hoặc thiết kế lại generator để tin giả và tin thật có phân bố $n^{\text{corrob}$ và has_image chồng lấn, rồi báo cáo lại. Con số cần báo cáo là AUC/AP có điều kiện trên mật độ láng giềng, không phải AUC biên.

5. Cách trình bày HDBSCAN vẫn nghiêng về phía các tác giả
   Bài báo dành nhiều dòng để tuyên bố nó báo cáo cả những kết quả bất lợi. Nhưng ở đúng chỗ đó, nó lại mắc đúng loại artifact mà nó tự hào đã bắt được ở nơi khác. Tôi phân rã 20 cụm của HDBSCAN:

14 cụm chứa điểm có nhãn : đường kính TB 6.47 km, max 81.2 km
   → 13/14 cụm đường kính < 1.5 km; 1 cụm bị 2 điểm nhiễu kéo ra 81 km
6 cụm chỉ gồm điểm nhiễu  : đường kính TB 147.22 km
→ trung bình gộp 20 cụm  : 48.69 km  ← con số bài báo dùng
"Mean diameter 48.69 km" và "cụm trải cả tỉnh" gần như hoàn toàn do 6 cụm chỉ gồm điểm nhiễu — mà những điểm đó không thuộc cụm ground-truth nào, nên việc HDBSCAN nhóm chúng lại không phải một lỗi điều phối theo nghĩa bài báo hm ý. Phát biểu công bằng là: HDBSCAN phục hồi cả 14 nhóm thật với hình học chặt (13/14 dưới 1.5 km), cộng thêm 6 nhóm gồm toàn nhiễu. Điều đó khiến so sánh chính của Thí nghiệm 4 và 9 yếu đi đáng kể — HDBSCAN không "không dùng được về vận hành", nó chỉ xử lý thùng nhiễu khác.

Đây cũng chính là quy ước mà bài báo tuyên bố đã cẩn thận xử lý cho DBSCAN (loại nhãn $-1$ khỏi mọi thống kê) — nhưng quy ước đó không bắt được các cụm hợp lệ chỉ gồm điểm nhiễu.

6. Định vị và tính mới: thiếu hẳn một dòng văn liệu
   "Nhân $\mathcal{S}_{geo}$ vào thay vì cộng" là một product kernel — không mới, và cóít nhất ba dòng nghiên cứu đã làm đúng điều này mà bài không trích:

Bilateral filtering (Tomasi & Manduchi, ICCV 1998): tích của kernel không gian và kernel giá trị. Cùng dạng toán, cùng động lực.
Spatially constrained clustering /ClustGeo (Chavent et al., 2018), và họ contiguity-constrained clustering trong địa thống kê — bài toán "đảm bảo cụm liền mạch về không gian" đã được nghiên cứu hệ thống.
Kernel tách được trong spectral clustering có ràng buộc không gian.
Nghiêm trọng hơn: baseline mà bài so sánh — tổng cộng $\alpha\mathcal{S}{geo}+\beta\mathcal{S}{temp}+\gamma\mathcal{S}_{ctx}$ — không có trích dẫn nào cho biết ai thực sự dùng nó. Mục 2.3 viết "that additive penalty is precisely the design we compare against" nhưng không dẫn công trình nào. Một straw man tự dng, sau đó được Thí nghiệm 13 chứng minh là thậm chí không thua, thì không tạo ra tính mới.

7. Toàn bộ phần Edge AI không có bằng chứng thực nghiệm
   MobileNetV3 và DistilBERT được nêu trong tiêu đề, abstract, contribution 1 và 3, Bảng 1 — nhưng không hề được chạy. $F, E, V, N, C$ đều do generator sinh ra. Nghĩa là:

Contribution 1 (trích xuất tại biên): 0 bằng chứng.
Contribution 3 ($V_i$, $C_i$ "edge-feasible"): 0 bằng chứng — bài tự thừa nhận $V_i$ được coi là cho trước.
Thí nghiệm 10 (105–111 byte): tautology. Nó đo json.dumps của 8 con số. Không có độ trễ trên thiết bị, không có mô hình mất gói / băng thông của mạng suy giảm, không có so sánh với kích thước ảnh thật.
Với hiện trạng này, "Using Edge AI" trong tiêu đề là quá tuyên bố. Đề nghị hoặc chạy thật hai mô hình trên một thiết bị (đo latency, RAM, năng lượng), hoặc rút Edge AI khỏi tiêu đề và abstract, giữ nó ở mức "kiến trúc đề xuất".

8. Độ chặt chẽ thống kê
   Không có kiểm định ý nghĩa hay khoảng tin cậy ở bất kỳ đâu ngoài Thí nghiệm 8.
   Thí nghiệm 7: chênh lệch 2.9% (110.2 vs 113.5 phút) trên một sed, một depot, không CI, không kiểm định. Đây là nhiễu, không phải kết quả. Bài báo đã trung thực gọi nó là "small" nhưng vẫn báo cáo với 4 chữ số ý nghĩa.
   Cũng trong Thí nghiệm 7: mô phỏng phục vụ cả 74 cụm, gồm 61 singleton là nhiễu và tin giả — nên "mean arrival 2528 phút" (42 giờ). Không điều phối viên nào cử ca nô đến 61 báo cáo giả. Mô phỏng cần giới hạn ở 13 cụm thật, và cần đa sed + CI.
   20 sed của Thí nghiệm 12 tái sinh dữ liệu nhưng giữ nguyên hình học liên nhóm, nên "thắng 100%/20 seed" không phải 20 phép thử độc lập theo nghĩa cần thiết. Bài có ghi chú điều này ở Mục 6.6, tốt — nhưng vẫn để "wins on 100% of 20 seeds" trong abstract mà không kèm điều kiện.
   $\tau$ ổn định đo tính tự nhất quán, không đo tính đúng. Với 13 cụm thật và khoảng cách điểm lớn, "top-3 giữ nguyên 100%" gần như tất yếu.
9. Các điểm kỹ thuật nhỏ hơn
   Mục 4.2: lý giải $\mathcal{S}_{temp}$ dùng bậc nhất "vì lũ có quán tính" là một non-sequitur. Quán tính biện minh cho $\tau$ lớn hơn, không cho việc đổi bậc của số mũ. Sự khác biệt bậc nhất/bậc hai là về độ nhọn gần 0, không về đuôi.
   Mục 4.3: nêu Louvain "near-$\mathcal{O}(N\log N)$" như một lý do chọn, nhưng bước dựng ma trận là $\mathcal{O}(N^2)$ và matrix_to_graph cũng là vòng lặp đôi Python — nên pipeline là $\mathcal{O}(N^2)$. Trình bày độ phức tạp của Louvain như điểm bán là gây nhầm lẫn (Thí nghiệm 11 thừa nhận một phần).
   Thí nghiệm 6 báo cáo mean_diam 0.1491 km (trung bình mọi cụm, gồm 61 singleton = 0.0) trong khi mọi chỗ khác dùng biến thể multi-member0.8487 km. Không nhất quán.
   Bảng 3 ($\tau_E=0.35$ vs $\tau_F=0.25$): lý giải "E nhiễu hơn F" không thể kiểm chứng trên dataset này vì cả hai đều trơ. Nên nu là quy ước, đừng nêu là thiết kế có căn cứ.
   Ràng buộc $\mathcal{P}\in[0,2)$ đúng về toán, nhưng do $\widetilde{\mathcal{N}}$ dùng tham chiếu động, $\mathcal{P}$ không so sánh được qua thời gian — với một hệ thống điều phối trực tuyến thì đây là hạn chế thiết kế nặng hơn mức bài báo trình bày (một cụm có thể tụt hạng chỉ vì nơi khác xuất hiện cụm lớn hơn).
10. Trình bày và tính phù hợp với venue
    Abstract ~450 từ, gấp đôi chuẩn LNCS, và phần lớn là danh mục những gì không hoạt động. Về mặt tu từ, abstract hiện tại thuyết phục reviewer rằng bài không có kết quả. Cần viết lại quanh 200 từ, nêu một tuyên bố dương tính có thể bảo vệ được.
    Bài đọc như một văn bản phản biện (rebuttal) chứ không phải bài báo: "we were wrong to present it as", "the result we must report first is the one that does not favor our method", "we reportather than hide", "an artifact in our favour". Sự minh bạch này rất đáng trọng và nên giữ trong phần Threats to Validity — nhưng khi nó tràn vào abstract, contributions và conclusion thì độ giả không còn xác định được bài khẳng định điều gì.
    13 thí nghiệm cho một bài LNCS (thường 12–16 trang). Nên gộp: 1B/1C/1D/1H là kiểm tra tính chất của công thức, không phải thí nghiệm; Thí nghiệm 10 nên là một câu trong Mục 4.1.
    main.tex:43-44: email vẫn là placeholder corresponding.author@ctu.edu.vn kèm % TODO(authors). 6 tác giả không có ORCID, không phân tách affiliation.
    main.log có 5 cảnh báo Underfull \vbox và một Underfull \hbox ở dòng 114–115 — cần xử lý trước khi nộp.
    Hai hình bị xoá khỏi paper/figures/ (fig2_map.png, fig3_heatmap.png) theo git status nhưng không còn được tham chiếu — cần xác nhận không mất hình bản đồ dataset, vì một bài về phân cụm không gian rất nên có hình phân bố dữ liệu.
    Điều gì thực sự còn lại
    Sau khi trừ đi những gì Thí nghiệm 13 thu hồi (§1), những gì Thí nghiệm 6+2+4 thu hồi (§2), những gì generator quyết định (§3), $C_i$ (§4), và phần Edge AI chưa hiện thực hoá (§7):

Còn lại: một quan sát kỹ thuật đúng và hữu ích — nếu bạn nhân kernel không gian vào thay vì cộng, đồ thịự thưa và ngưỡng sparsification trở nên gần như không cần điều chỉnh. Cộng với một cách đóng gói bài toán triage (hàm ưu tiên cấp cụm với hệ số khuếch đại công bằng) được trình bày rõ ràng và có núm chính sách $\mu$ được quét đàng hoàng.

Đó là một short paper / workshop paper tốt, hoặc phần nền cho một bài đầy đủ. Nó chưa là một bài full paper, vì tuyên bố trung tâm hiện tại đã bị chính các tác giả bác bỏ và tuyên bố thay thế không bất biến theo thang đo.

Ba việc cần làm để bài này đứng được
Đổi dữ liệu, không đổi cách viết. Chạy trên dữ liệu thật (CrisisMD/FloodNet có toạ độ, hoặc dữ liệu Zalo/Facebook giai đoạn bão) hoặc ít nhất một generator có nhóm chồng lấn về không gian, mật độ không đồng đều, và tin giả có phân bố coroboration giống tin thật. Trên dữ liệu như vậy, $\mathcal{S}_{context}$ và $C_i$ mới có cơ hội chứng minh giá trị — và §2, §3, §4 mới có thể được trả lời thay vì thừa nhận.
Phát biểu lại đóng góp bằng đại lượng bất biến. Thay "cửa sổ 51×" bằng một mệnh đề đúng và kiểm chứng được: gating khiến độ nhạy với $\theta$ triệt tiêu vì $\mathcal{S}{geo}$ đã thực hiện việc thưa hoá; chứng minh điều này bằng tỉ lệ cạnh giữ lại hoặc bằng một mệnh đề giải tích về cận trên của $w{ij}$ theo khoảng cách (bài đã gần có ở Mục 6.13 đoạn cuối — hãy biến nó thành một bổ đề, đó là đóng góp mạnh nhất mà bài đang có và nó không cần thực nghiệm nào cả).
Trích dẫn dòng văn liệu product-kernel / spatially-constrained clustering và định vị lại tính mới trên nền đó. Nếu sau khi trích dẫn vẫn còn phần mới (rất có thể là: ứng dụng vào triage cứu hộ + hàm ưu tiên cấp cụm có hệ số công bằng), thì đó chính là đóng góp nên đặt lên tiêu đề — không phải cơ chế gating.
Một ghi chú cuối, thật lòng: mức độ tự soi của bản thảo này cao hơn phần lớn bài tôi đọc. Việc tự phát hiện confound $\theta$ bằng cách audit code của chính mình (Mục 6.6) là điều rất ít nhóm làm. Vấn đề không phải là thiếu trung thực — mà là sự trung thực đó đã bào mòn hết tuyên bố, và bước còn thiếu là thay dữ liệu để giành lại một tuyên bố dương tính, chứ không phải viết cẩn thận hơn về một tuyên bố đã mấ

Đã kiểm chứng xong. Dưới đây là bản phản biện của tôi vớiư cách reviewer.

Phản biện: "Weighted Graph-Based Event Clustering and Priority Scoring for Flood-Rescue Coordination Using Edge AI"
Kết luận tổng thể: Major Revision (nghiêng về Reject nếu nhắm hội nghị hạng A).

Bài báo có văn hoá báo cáo trung thực đáng khen — hiếm thấy một bản thảo tự bác bỏ tuyên bố chính của mình (Thí nghiệm 13). Nhưng chính sự trung thực đó lại phơi ra vấn đề: sau khi trừ hết những gì các tác giả tự thu hồi, phần đóng góp còn lại không đủ cho một bài báo, và ba trong số các con số còn sót lại cũng không đứng vững khi tôi kiểm tra lại bằng code của chính các tác giả.

1. Vấn đề nghiêm trọng nhất: "cửa sổ51×" là một artifact của cách chọn thước đo
   Đây là tuyên bố duy nhất còn sót lại sau Thí nghiệm 13, đượcặt vào abstract, kết luận và toàn bộ phần định vị đóng góp. Nó không đứng vững.

Từ exp13_theta_ranges.json:

| Dạng | Cửa sổ dùng được | Tỉ số (báo cáo) | Độ rộng tuyệt đối |
|---|---|
| Gating | [0.01, 0.51] | 51.0× | 0.50 |
| Additive α=1.0 | [0.96, 1.46] | 1.5× | 0.50 |

Hai cửa sổ rộng bằng nhau chính xác đến từng chữ số. Con số 51× chỉ tồn tại vì cửa sổ của gating bắt đầu gần 0, mà tỉ số $\theta_{hi}/\theta_{lo}$ phân kỳ khi $\theta_{lo}\to 0$. Đây là một đại lượng không bất biến theo tái tham số hoá: nếu chẩn hoá $\theta$ theo $w_{\max}$ của từng dạng (0.988 cho gating, 1.988 cho additive — số từ chính exp13_theta_ranges.json), cửa sổ trở thành [0.010, 0.516] so với [0.483, 0.734], tức 0.51 so với 0.25 — lợi thế 2×, không phải 51×. Nếu đo bằng độ rộng tuyệt đối thì lợi thế bằng 1×.

Nói cách khác, phát biểu đúng duy nhất là: cửa sổ của gating chứa gốc toạ độ, nên mọi $\theta$ nhỏ đều dùng được. Điều đó đúng, nhưng nó chỉ là cách phát biểu lại một sự thật tầm thường: $\mathcal{S}_{geo}$ đã triệt tiêu các cặp xa nên đồ thị đã thưa trước khi $\theta$ được áp. Không cần một bảng thí nghiệm và con số 51× để nói điều này, và tuyệt đối không nên đặt nó làm đóng góp trung tâm.

Yêu cầu: bỏ con số 51× hoặc thay bằng một đại lượng bất biến theo thang đo (ví dụ tỉ lệ cạnh giữ lại, hoặc $\theta$ chuẩn hoá theo $w_{\max}$/phân vị), và phát biểu lại đóng góp cho tương ứng.

2. Trên dữ liệu này, phương pháp thực chất là một ngưỡng khoảng cách
   Với $\sigma_{geo}=700$ m và $(\beta\mathcal{S}{temp}+\gamma\mathcal{S}{ctx})\le 1$, điều kiện $w_{ij}>0.05$ bắt buộc $\mathcal{S}_{geo}>0.05$, tức $d < 700\sqrt{2\ln 20} \approx 1710$ m. Toàn bộ đồ thị gating ở tham số mặc định không thể khác một đồ thị "nối mọi cặp cách nhau dưới ~1.7 km" nhiều hơn một chút về trọng số cạnh.

Chính các thí nghiệm của bài báo xác nhận điều này, và cả bốn cùng chỉ về một hướng:

Thí nghiệm 6: xoá hẳn $\mathcal{S}_{context}$ → phân hoạch bit-identical, $\tau=1.0$.
Thí nghiệm 2: quét toàn bộ lưới $\tau_F,\tau_E\in[0.15,0.5]$ → ARI và số cụm không đổi.
Thí nghiệm 4: Agglomerative trên cùng ma trận → trùng khớp tuyệt đối cả bốn chỉ số.
Tôi chạy lại pipeline: 74 cụm = 13 cụm thật + 61 singleton, và 61 singleton đó là đúng 61 điểm nhiễu gt=-1. Phân hoạch được phục hồi trọn vẹn ngoại trừ cặp 106/107.
Hệ quả: vector 7 chiều $(L,T,F,E,N,V,C)$ — điểm bán chính của bài — không đóng góp gì cho bước phân cụm. Chỉ có $(L)$ hoạt động. Phần "spatial–semantic–physical" trong tiêu đề Mục 4.2 không được dữ liệu ủng hộ. Bài báo có thừa nhận điều này ở Mục 6.6 nhưng vẫn giữ nguyên framing ở tiêu đề, abstract và Bảng 1 (dòng "Weighted graph ✓ (gating)").

Ngoại lệ duy nhất ($\beta=0.9$, ARI 0.9509) là một trường hợp tự tạo: cặp S5 cách 923 m được đặt vào dataset chính để làm $\gamma$ có việc làm. Một tham số chỉ chứng minh được giá trị của mình trên một cặp điểm được thiết k riêng cho nó thì chưa phải bằng chứng.

3. Dataset quyết định kết quả, không phải phương pháp
   Từ generate.py: 6 đảo với spread_m=250, các nhóm narative đặt trên vệ tinh cách tâm 3 km, cộng assert_gt_separable(min_sep_m=2000). Khoảng cách trong nhóm ~vài trăm mét; giữa nhóm ≥ 2 km. Bất kỳ phương pháp nào có ngưỡng cắt nằm giữa 1 và 2 km đều thu được đáp án gần hoàn hảo.

ARI = 0.9957 vì vậy đo tính khả tách của generator, không đo năng lực của phương pháp. Bài báo nói điều này trong Threats to Validity — nhưng rồi vẫn dùng ARI làm con số headline trong abstract, và tệ hơn, dùng nó làm tiêu chí "usable" ($\text{ARI}\ge 0.95$) của Thí nghiệm 13. Toàn bộ kết quả hiệu chuẩn $\theta$ thừa hưởng vấn đề này.

Việc thêm assertion khả tách để sửa lỗi co-location của phiên bản trước đã làm bài toán dễ hơn, không khó hơn. Một dataset mà ground truth bị bắt buộc phải tách được về không gian thì không thể dùng để chứng minh giá trị của một cơ chế gating không gian — vì cơ chế đó được đảm bảo thắng bởi cấu trúc dữ liệu.

4. ROC-AUC 0.9176 của bộ phát hiện tin giả là artifact, không phải năng lực phát hiện
   Đây là phát hiện tôi cho là nghiêm trọng nhất về mặt tính đúng đắn, vì bài báo trình bày nó như một kết quả định lượng có khoảng tin cậy bootstrap.

Tôi đo lại trên chính dữ liệu và công thức của các tác giả:

mean n_corrob:  fake 0.00 | real trong đảo 14.84 | real rải rác 0.00
AUC(-n_corrob) một mình = 0.9355   (cao hơn cả C_i)

Giới hạn vào 61 điểm rải rác (23 fake vs 38 real) — phép so sánh không tầm thường duy nhất:
  AUC(-C_i) = 0.4319          (dưới ngưỡng ngẫu nhiên 0.5)
  AP (-C_i) = 0.3495  vs baseline ngẫu nhiên 0.3770   (tệ hơn ngẫu nhiên)
Nguyên nhân: cả 23 tin giả đều nằm trong tập nhiễu rải rác, nên $n^{\text{corrob}}=0$; còn mọi báo cáo thật trong đảo có ~15 láng giềng. $C_i$ vì thế phân biệt "điểm này có nằm trong vùng dày đặc hay không", mà điều đó trùng khít với việc điểm có nhãn hay không — tức trùng khít với biến đích, qua một đường không liên quan gì đến tính giả mạo. Khi loại bỏ đường tắt đó, $C_i$ kém hơn đoán bừa.

Tương tự, "giảm 55% dân số ảo" không phải kết quả phát hiện: nó là phép nhân với $C_i=0.4502$, và 0.4502 đến từ việc generator gán cho báo cáo S3 giá trị has_image=False và đặt nó cô lập. Con số 55% được quyết định bởi $(b_0,b_1,b_2)$ do tác giả chọn, không bởi dữ liệu.

Yêu cầu: hoặc rút Thí nghiệm 8 và mọi tuyên bố phát hiện tin giả (bao gồm trong abstract), hoặc thiết kế lại generator để tin giả và tin thật có phân bố $n^{\text{corrob}$ và has_image chồng lấn, rồi báo cáo lại. Con số cần báo cáo là AUC/AP có điều kiện trên mật độ láng giềng, không phải AUC biên.

5. Cách trình bày HDBSCAN vẫn nghiêng về phía các tác giả
   Bài báo dành nhiều dòng để tuyên bố nó báo cáo cả những kết quả bất lợi. Nhưng ở đúng chỗ đó, nó lại mắc đúng loại artifact mà nó tự hào đã bắt được ở nơi khác. Tôi phân rã 20 cụm của HDBSCAN:

14 cụm chứa điểm có nhãn : đường kính TB 6.47 km, max 81.2 km
   → 13/14 cụm đường kính < 1.5 km; 1 cụm bị 2 điểm nhiễu kéo ra 81 km
6 cụm chỉ gồm điểm nhiễu  : đường kính TB 147.22 km
→ trung bình gộp 20 cụm  : 48.69 km  ← con số bài báo dùng
"Mean diameter 48.69 km" và "cụm trải cả tỉnh" gần như hoàn toàn do 6 cụm chỉ gồm điểm nhiễu — mà những điểm đó không thuộc cụm ground-truth nào, nên việc HDBSCAN nhóm chúng lại không phải một lỗi điều phối theo nghĩa bài báo hm ý. Phát biểu công bằng là: HDBSCAN phục hồi cả 14 nhóm thật với hình học chặt (13/14 dưới 1.5 km), cộng thêm 6 nhóm gồm toàn nhiễu. Điều đó khiến so sánh chính của Thí nghiệm 4 và 9 yếu đi đáng kể — HDBSCAN không "không dùng được về vận hành", nó chỉ xử lý thùng nhiễu khác.

Đây cũng chính là quy ước mà bài báo tuyên bố đã cẩn thận xử lý cho DBSCAN (loại nhãn $-1$ khỏi mọi thống kê) — nhưng quy ước đó không bắt được các cụm hợp lệ chỉ gồm điểm nhiễu.

6. Định vị và tính mới: thiếu hẳn một dòng văn liệu
   "Nhân $\mathcal{S}_{geo}$ vào thay vì cộng" là một product kernel — không mới, và cóít nhất ba dòng nghiên cứu đã làm đúng điều này mà bài không trích:

Bilateral filtering (Tomasi & Manduchi, ICCV 1998): tích của kernel không gian và kernel giá trị. Cùng dạng toán, cùng động lực.
Spatially constrained clustering /ClustGeo (Chavent et al., 2018), và họ contiguity-constrained clustering trong địa thống kê — bài toán "đảm bảo cụm liền mạch về không gian" đã được nghiên cứu hệ thống.
Kernel tách được trong spectral clustering có ràng buộc không gian.
Nghiêm trọng hơn: baseline mà bài so sánh — tổng cộng $\alpha\mathcal{S}{geo}+\beta\mathcal{S}{temp}+\gamma\mathcal{S}_{ctx}$ — không có trích dẫn nào cho biết ai thực sự dùng nó. Mục 2.3 viết "that additive penalty is precisely the design we compare against" nhưng không dẫn công trình nào. Một straw man tự dng, sau đó được Thí nghiệm 13 chứng minh là thậm chí không thua, thì không tạo ra tính mới.

7. Toàn bộ phần Edge AI không có bằng chứng thực nghiệm
   MobileNetV3 và DistilBERT được nêu trong tiêu đề, abstract, contribution 1 và 3, Bảng 1 — nhưng không hề được chạy. $F, E, V, N, C$ đều do generator sinh ra. Nghĩa là:

Contribution 1 (trích xuất tại biên): 0 bằng chứng.
Contribution 3 ($V_i$, $C_i$ "edge-feasible"): 0 bằng chứng — bài tự thừa nhận $V_i$ được coi là cho trước.
Thí nghiệm 10 (105–111 byte): tautology. Nó đo json.dumps của 8 con số. Không có độ trễ trên thiết bị, không có mô hình mất gói / băng thông của mạng suy giảm, không có so sánh với kích thước ảnh thật.
Với hiện trạng này, "Using Edge AI" trong tiêu đề là quá tuyên bố. Đề nghị hoặc chạy thật hai mô hình trên một thiết bị (đo latency, RAM, năng lượng), hoặc rút Edge AI khỏi tiêu đề và abstract, giữ nó ở mức "kiến trúc đề xuất".

8. Độ chặt chẽ thống kê
   Không có kiểm định ý nghĩa hay khoảng tin cậy ở bất kỳ đâu ngoài Thí nghiệm 8.
   Thí nghiệm 7: chênh lệch 2.9% (110.2 vs 113.5 phút) trên một sed, một depot, không CI, không kiểm định. Đây là nhiễu, không phải kết quả. Bài báo đã trung thực gọi nó là "small" nhưng vẫn báo cáo với 4 chữ số ý nghĩa.
   Cũng trong Thí nghiệm 7: mô phỏng phục vụ cả 74 cụm, gồm 61 singleton là nhiễu và tin giả — nên "mean arrival 2528 phút" (42 giờ). Không điều phối viên nào cử ca nô đến 61 báo cáo giả. Mô phỏng cần giới hạn ở 13 cụm thật, và cần đa sed + CI.
   20 sed của Thí nghiệm 12 tái sinh dữ liệu nhưng giữ nguyên hình học liên nhóm, nên "thắng 100%/20 seed" không phải 20 phép thử độc lập theo nghĩa cần thiết. Bài có ghi chú điều này ở Mục 6.6, tốt — nhưng vẫn để "wins on 100% of 20 seeds" trong abstract mà không kèm điều kiện.
   $\tau$ ổn định đo tính tự nhất quán, không đo tính đúng. Với 13 cụm thật và khoảng cách điểm lớn, "top-3 giữ nguyên 100%" gần như tất yếu.
9. Các điểm kỹ thuật nhỏ hơn
   Mục 4.2: lý giải $\mathcal{S}_{temp}$ dùng bậc nhất "vì lũ có quán tính" là một non-sequitur. Quán tính biện minh cho $\tau$ lớn hơn, không cho việc đổi bậc của số mũ. Sự khác biệt bậc nhất/bậc hai là về độ nhọn gần 0, không về đuôi.
   Mục 4.3: nêu Louvain "near-$\mathcal{O}(N\log N)$" như một lý do chọn, nhưng bước dựng ma trận là $\mathcal{O}(N^2)$ và matrix_to_graph cũng là vòng lặp đôi Python — nên pipeline là $\mathcal{O}(N^2)$. Trình bày độ phức tạp của Louvain như điểm bán là gây nhầm lẫn (Thí nghiệm 11 thừa nhận một phần).
   Thí nghiệm 6 báo cáo mean_diam 0.1491 km (trung bình mọi cụm, gồm 61 singleton = 0.0) trong khi mọi chỗ khác dùng biến thể multi-member0.8487 km. Không nhất quán.
   Bảng 3 ($\tau_E=0.35$ vs $\tau_F=0.25$): lý giải "E nhiễu hơn F" không thể kiểm chứng trên dataset này vì cả hai đều trơ. Nên nu là quy ước, đừng nêu là thiết kế có căn cứ.
   Ràng buộc $\mathcal{P}\in[0,2)$ đúng về toán, nhưng do $\widetilde{\mathcal{N}}$ dùng tham chiếu động, $\mathcal{P}$ không so sánh được qua thời gian — với một hệ thống điều phối trực tuyến thì đây là hạn chế thiết kế nặng hơn mức bài báo trình bày (một cụm có thể tụt hạng chỉ vì nơi khác xuất hiện cụm lớn hơn).
10. Trình bày và tính phù hợp với venue
    Abstract ~450 từ, gấp đôi chuẩn LNCS, và phần lớn là danh mục những gì không hoạt động. Về mặt tu từ, abstract hiện tại thuyết phục reviewer rằng bài không có kết quả. Cần viết lại quanh 200 từ, nêu một tuyên bố dương tính có thể bảo vệ được.
    Bài đọc như một văn bản phản biện (rebuttal) chứ không phải bài báo: "we were wrong to present it as", "the result we must report first is the one that does not favor our method", "we reportather than hide", "an artifact in our favour". Sự minh bạch này rất đáng trọng và nên giữ trong phần Threats to Validity — nhưng khi nó tràn vào abstract, contributions và conclusion thì độ giả không còn xác định được bài khẳng định điều gì.
    13 thí nghiệm cho một bài LNCS (thường 12–16 trang). Nên gộp: 1B/1C/1D/1H là kiểm tra tính chất của công thức, không phải thí nghiệm; Thí nghiệm 10 nên là một câu trong Mục 4.1.
    main.tex:43-44: email vẫn là placeholder corresponding.author@ctu.edu.vn kèm % TODO(authors). 6 tác giả không có ORCID, không phân tách affiliation.
    main.log có 5 cảnh báo Underfull \vbox và một Underfull \hbox ở dòng 114–115 — cần xử lý trước khi nộp.
    Hai hình bị xoá khỏi paper/figures/ (fig2_map.png, fig3_heatmap.png) theo git status nhưng không còn được tham chiếu — cần xác nhận không mất hình bản đồ dataset, vì một bài về phân cụm không gian rất nên có hình phân bố dữ liệu.
    Điều gì thực sự còn lại
    Sau khi trừ đi những gì Thí nghiệm 13 thu hồi (§1), những gì Thí nghiệm 6+2+4 thu hồi (§2), những gì generator quyết định (§3), $C_i$ (§4), và phần Edge AI chưa hiện thực hoá (§7):

Còn lại: một quan sát kỹ thuật đúng và hữu ích — nếu bạn nhân kernel không gian vào thay vì cộng, đồ thịự thưa và ngưỡng sparsification trở nên gần như không cần điều chỉnh. Cộng với một cách đóng gói bài toán triage (hàm ưu tiên cấp cụm với hệ số khuếch đại công bằng) được trình bày rõ ràng và có núm chính sách $\mu$ được quét đàng hoàng.

Đó là một short paper / workshop paper tốt, hoặc phần nền cho một bài đầy đủ. Nó chưa là một bài full paper, vì tuyên bố trung tâm hiện tại đã bị chính các tác giả bác bỏ và tuyên bố thay thế không bất biến theo thang đo.

Ba việc cần làm để bài này đứng được
Đổi dữ liệu, không đổi cách viết. Chạy trên dữ liệu thật (CrisisMD/FloodNet có toạ độ, hoặc dữ liệu Zalo/Facebook giai đoạn bão) hoặc ít nhất một generator có nhóm chồng lấn về không gian, mật độ không đồng đều, và tin giả có phân bố coroboration giống tin thật. Trên dữ liệu như vậy, $\mathcal{S}_{context}$ và $C_i$ mới có cơ hội chứng minh giá trị — và §2, §3, §4 mới có thể được trả lời thay vì thừa nhận.
Phát biểu lại đóng góp bằng đại lượng bất biến. Thay "cửa sổ 51×" bằng một mệnh đề đúng và kiểm chứng được: gating khiến độ nhạy với $\theta$ triệt tiêu vì $\mathcal{S}{geo}$ đã thực hiện việc thưa hoá; chứng minh điều này bằng tỉ lệ cạnh giữ lại hoặc bằng một mệnh đề giải tích về cận trên của $w{ij}$ theo khoảng cách (bài đã gần có ở Mục 6.13 đoạn cuối — hãy biến nó thành một bổ đề, đó là đóng góp mạnh nhất mà bài đang có và nó không cần thực nghiệm nào cả).
Trích dẫn dòng văn liệu product-kernel / spatially-constrained clustering và định vị lại tính mới trên nền đó. Nếu sau khi trích dẫn vẫn còn phần mới (rất có thể là: ứng dụng vào triage cứu hộ + hàm ưu tiên cấp cụm có hệ số công bằng), thì đó chính là đóng góp nên đặt lên tiêu đề — không phải cơ chế gating.
Một ghi chú cuối, thật lòng: mức độ tự soi của bản thảo này cao hơn phần lớn bài tôi đọc. Việc tự phát hiện confound $\theta$ bằng cách audit code của chính mình (Mục 6.6) là điều rất ít nhóm làm. Vấn đề không phải là thiếu trung thực — mà là sự trung thực đó đã bào mòn hết tuyên bố, và bước còn thiếu là thay dữ liệu để giành lại một tuyên bố dương tính, chứ không phải viết cẩn thận hơn về một tuyên bố đã mấ

Đã kiểm chứng xong. Dưới đây là bản phản biện của tôi vớiư cách reviewer.

Phản biện: "Weighted Graph-Based Event Clustering and Priority Scoring for Flood-Rescue Coordination Using Edge AI"
Kết luận tổng thể: Major Revision (nghiêng về Reject nếu nhắm hội nghị hạng A).

Bài báo có văn hoá báo cáo trung thực đáng khen — hiếm thấy một bản thảo tự bác bỏ tuyên bố chính của mình (Thí nghiệm 13). Nhưng chính sự trung thực đó lại phơi ra vấn đề: sau khi trừ hết những gì các tác giả tự thu hồi, phần đóng góp còn lại không đủ cho một bài báo, và ba trong số các con số còn sót lại cũng không đứng vững khi tôi kiểm tra lại bằng code của chính các tác giả.

1. Vấn đề nghiêm trọng nhất: "cửa sổ51×" là một artifact của cách chọn thước đo
   Đây là tuyên bố duy nhất còn sót lại sau Thí nghiệm 13, đượcặt vào abstract, kết luận và toàn bộ phần định vị đóng góp. Nó không đứng vững.

Từ exp13_theta_ranges.json:

| Dạng | Cửa sổ dùng được | Tỉ số (báo cáo) | Độ rộng tuyệt đối |
|---|---|
| Gating | [0.01, 0.51] | 51.0× | 0.50 |
| Additive α=1.0 | [0.96, 1.46] | 1.5× | 0.50 |

Hai cửa sổ rộng bằng nhau chính xác đến từng chữ số. Con số 51× chỉ tồn tại vì cửa sổ của gating bắt đầu gần 0, mà tỉ số $\theta_{hi}/\theta_{lo}$ phân kỳ khi $\theta_{lo}\to 0$. Đây là một đại lượng không bất biến theo tái tham số hoá: nếu chẩn hoá $\theta$ theo $w_{\max}$ của từng dạng (0.988 cho gating, 1.988 cho additive — số từ chính exp13_theta_ranges.json), cửa sổ trở thành [0.010, 0.516] so với [0.483, 0.734], tức 0.51 so với 0.25 — lợi thế 2×, không phải 51×. Nếu đo bằng độ rộng tuyệt đối thì lợi thế bằng 1×.

Nói cách khác, phát biểu đúng duy nhất là: cửa sổ của gating chứa gốc toạ độ, nên mọi $\theta$ nhỏ đều dùng được. Điều đó đúng, nhưng nó chỉ là cách phát biểu lại một sự thật tầm thường: $\mathcal{S}_{geo}$ đã triệt tiêu các cặp xa nên đồ thị đã thưa trước khi $\theta$ được áp. Không cần một bảng thí nghiệm và con số 51× để nói điều này, và tuyệt đối không nên đặt nó làm đóng góp trung tâm.

Yêu cầu: bỏ con số 51× hoặc thay bằng một đại lượng bất biến theo thang đo (ví dụ tỉ lệ cạnh giữ lại, hoặc $\theta$ chuẩn hoá theo $w_{\max}$/phân vị), và phát biểu lại đóng góp cho tương ứng.

2. Trên dữ liệu này, phương pháp thực chất là một ngưỡng khoảng cách
   Với $\sigma_{geo}=700$ m và $(\beta\mathcal{S}{temp}+\gamma\mathcal{S}{ctx})\le 1$, điều kiện $w_{ij}>0.05$ bắt buộc $\mathcal{S}_{geo}>0.05$, tức $d < 700\sqrt{2\ln 20} \approx 1710$ m. Toàn bộ đồ thị gating ở tham số mặc định không thể khác một đồ thị "nối mọi cặp cách nhau dưới ~1.7 km" nhiều hơn một chút về trọng số cạnh.

Chính các thí nghiệm của bài báo xác nhận điều này, và cả bốn cùng chỉ về một hướng:

Thí nghiệm 6: xoá hẳn $\mathcal{S}_{context}$ → phân hoạch bit-identical, $\tau=1.0$.
Thí nghiệm 2: quét toàn bộ lưới $\tau_F,\tau_E\in[0.15,0.5]$ → ARI và số cụm không đổi.
Thí nghiệm 4: Agglomerative trên cùng ma trận → trùng khớp tuyệt đối cả bốn chỉ số.
Tôi chạy lại pipeline: 74 cụm = 13 cụm thật + 61 singleton, và 61 singleton đó là đúng 61 điểm nhiễu gt=-1. Phân hoạch được phục hồi trọn vẹn ngoại trừ cặp 106/107.
Hệ quả: vector 7 chiều $(L,T,F,E,N,V,C)$ — điểm bán chính của bài — không đóng góp gì cho bước phân cụm. Chỉ có $(L)$ hoạt động. Phần "spatial–semantic–physical" trong tiêu đề Mục 4.2 không được dữ liệu ủng hộ. Bài báo có thừa nhận điều này ở Mục 6.6 nhưng vẫn giữ nguyên framing ở tiêu đề, abstract và Bảng 1 (dòng "Weighted graph ✓ (gating)").

Ngoại lệ duy nhất ($\beta=0.9$, ARI 0.9509) là một trường hợp tự tạo: cặp S5 cách 923 m được đặt vào dataset chính để làm $\gamma$ có việc làm. Một tham số chỉ chứng minh được giá trị của mình trên một cặp điểm được thiết k riêng cho nó thì chưa phải bằng chứng.

3. Dataset quyết định kết quả, không phải phương pháp
   Từ generate.py: 6 đảo với spread_m=250, các nhóm narative đặt trên vệ tinh cách tâm 3 km, cộng assert_gt_separable(min_sep_m=2000). Khoảng cách trong nhóm ~vài trăm mét; giữa nhóm ≥ 2 km. Bất kỳ phương pháp nào có ngưỡng cắt nằm giữa 1 và 2 km đều thu được đáp án gần hoàn hảo.

ARI = 0.9957 vì vậy đo tính khả tách của generator, không đo năng lực của phương pháp. Bài báo nói điều này trong Threats to Validity — nhưng rồi vẫn dùng ARI làm con số headline trong abstract, và tệ hơn, dùng nó làm tiêu chí "usable" ($\text{ARI}\ge 0.95$) của Thí nghiệm 13. Toàn bộ kết quả hiệu chuẩn $\theta$ thừa hưởng vấn đề này.

Việc thêm assertion khả tách để sửa lỗi co-location của phiên bản trước đã làm bài toán dễ hơn, không khó hơn. Một dataset mà ground truth bị bắt buộc phải tách được về không gian thì không thể dùng để chứng minh giá trị của một cơ chế gating không gian — vì cơ chế đó được đảm bảo thắng bởi cấu trúc dữ liệu.

4. ROC-AUC 0.9176 của bộ phát hiện tin giả là artifact, không phải năng lực phát hiện
   Đây là phát hiện tôi cho là nghiêm trọng nhất về mặt tính đúng đắn, vì bài báo trình bày nó như một kết quả định lượng có khoảng tin cậy bootstrap.

Tôi đo lại trên chính dữ liệu và công thức của các tác giả:

mean n_corrob:  fake 0.00 | real trong đảo 14.84 | real rải rác 0.00
AUC(-n_corrob) một mình = 0.9355   (cao hơn cả C_i)

Giới hạn vào 61 điểm rải rác (23 fake vs 38 real) — phép so sánh không tầm thường duy nhất:
  AUC(-C_i) = 0.4319          (dưới ngưỡng ngẫu nhiên 0.5)
  AP (-C_i) = 0.3495  vs baseline ngẫu nhiên 0.3770   (tệ hơn ngẫu nhiên)
Nguyên nhân: cả 23 tin giả đều nằm trong tập nhiễu rải rác, nên $n^{\text{corrob}}=0$; còn mọi báo cáo thật trong đảo có ~15 láng giềng. $C_i$ vì thế phân biệt "điểm này có nằm trong vùng dày đặc hay không", mà điều đó trùng khít với việc điểm có nhãn hay không — tức trùng khít với biến đích, qua một đường không liên quan gì đến tính giả mạo. Khi loại bỏ đường tắt đó, $C_i$ kém hơn đoán bừa.

Tương tự, "giảm 55% dân số ảo" không phải kết quả phát hiện: nó là phép nhân với $C_i=0.4502$, và 0.4502 đến từ việc generator gán cho báo cáo S3 giá trị has_image=False và đặt nó cô lập. Con số 55% được quyết định bởi $(b_0,b_1,b_2)$ do tác giả chọn, không bởi dữ liệu.

Yêu cầu: hoặc rút Thí nghiệm 8 và mọi tuyên bố phát hiện tin giả (bao gồm trong abstract), hoặc thiết kế lại generator để tin giả và tin thật có phân bố $n^{\text{corrob}$ và has_image chồng lấn, rồi báo cáo lại. Con số cần báo cáo là AUC/AP có điều kiện trên mật độ láng giềng, không phải AUC biên.

5. Cách trình bày HDBSCAN vẫn nghiêng về phía các tác giả
   Bài báo dành nhiều dòng để tuyên bố nó báo cáo cả những kết quả bất lợi. Nhưng ở đúng chỗ đó, nó lại mắc đúng loại artifact mà nó tự hào đã bắt được ở nơi khác. Tôi phân rã 20 cụm của HDBSCAN:

14 cụm chứa điểm có nhãn : đường kính TB 6.47 km, max 81.2 km
   → 13/14 cụm đường kính < 1.5 km; 1 cụm bị 2 điểm nhiễu kéo ra 81 km
6 cụm chỉ gồm điểm nhiễu  : đường kính TB 147.22 km
→ trung bình gộp 20 cụm  : 48.69 km  ← con số bài báo dùng
"Mean diameter 48.69 km" và "cụm trải cả tỉnh" gần như hoàn toàn do 6 cụm chỉ gồm điểm nhiễu — mà những điểm đó không thuộc cụm ground-truth nào, nên việc HDBSCAN nhóm chúng lại không phải một lỗi điều phối theo nghĩa bài báo hm ý. Phát biểu công bằng là: HDBSCAN phục hồi cả 14 nhóm thật với hình học chặt (13/14 dưới 1.5 km), cộng thêm 6 nhóm gồm toàn nhiễu. Điều đó khiến so sánh chính của Thí nghiệm 4 và 9 yếu đi đáng kể — HDBSCAN không "không dùng được về vận hành", nó chỉ xử lý thùng nhiễu khác.

Đây cũng chính là quy ước mà bài báo tuyên bố đã cẩn thận xử lý cho DBSCAN (loại nhãn $-1$ khỏi mọi thống kê) — nhưng quy ước đó không bắt được các cụm hợp lệ chỉ gồm điểm nhiễu.

6. Định vị và tính mới: thiếu hẳn một dòng văn liệu
   "Nhân $\mathcal{S}_{geo}$ vào thay vì cộng" là một product kernel — không mới, và cóít nhất ba dòng nghiên cứu đã làm đúng điều này mà bài không trích:

Bilateral filtering (Tomasi & Manduchi, ICCV 1998): tích của kernel không gian và kernel giá trị. Cùng dạng toán, cùng động lực.
Spatially constrained clustering /ClustGeo (Chavent et al., 2018), và họ contiguity-constrained clustering trong địa thống kê — bài toán "đảm bảo cụm liền mạch về không gian" đã được nghiên cứu hệ thống.
Kernel tách được trong spectral clustering có ràng buộc không gian.
Nghiêm trọng hơn: baseline mà bài so sánh — tổng cộng $\alpha\mathcal{S}{geo}+\beta\mathcal{S}{temp}+\gamma\mathcal{S}_{ctx}$ — không có trích dẫn nào cho biết ai thực sự dùng nó. Mục 2.3 viết "that additive penalty is precisely the design we compare against" nhưng không dẫn công trình nào. Một straw man tự dng, sau đó được Thí nghiệm 13 chứng minh là thậm chí không thua, thì không tạo ra tính mới.

7. Toàn bộ phần Edge AI không có bằng chứng thực nghiệm
   MobileNetV3 và DistilBERT được nêu trong tiêu đề, abstract, contribution 1 và 3, Bảng 1 — nhưng không hề được chạy. $F, E, V, N, C$ đều do generator sinh ra. Nghĩa là:

Contribution 1 (trích xuất tại biên): 0 bằng chứng.
Contribution 3 ($V_i$, $C_i$ "edge-feasible"): 0 bằng chứng — bài tự thừa nhận $V_i$ được coi là cho trước.
Thí nghiệm 10 (105–111 byte): tautology. Nó đo json.dumps của 8 con số. Không có độ trễ trên thiết bị, không có mô hình mất gói / băng thông của mạng suy giảm, không có so sánh với kích thước ảnh thật.
Với hiện trạng này, "Using Edge AI" trong tiêu đề là quá tuyên bố. Đề nghị hoặc chạy thật hai mô hình trên một thiết bị (đo latency, RAM, năng lượng), hoặc rút Edge AI khỏi tiêu đề và abstract, giữ nó ở mức "kiến trúc đề xuất".

8. Độ chặt chẽ thống kê
   Không có kiểm định ý nghĩa hay khoảng tin cậy ở bất kỳ đâu ngoài Thí nghiệm 8.
   Thí nghiệm 7: chênh lệch 2.9% (110.2 vs 113.5 phút) trên một sed, một depot, không CI, không kiểm định. Đây là nhiễu, không phải kết quả. Bài báo đã trung thực gọi nó là "small" nhưng vẫn báo cáo với 4 chữ số ý nghĩa.
   Cũng trong Thí nghiệm 7: mô phỏng phục vụ cả 74 cụm, gồm 61 singleton là nhiễu và tin giả — nên "mean arrival 2528 phút" (42 giờ). Không điều phối viên nào cử ca nô đến 61 báo cáo giả. Mô phỏng cần giới hạn ở 13 cụm thật, và cần đa sed + CI.
   20 sed của Thí nghiệm 12 tái sinh dữ liệu nhưng giữ nguyên hình học liên nhóm, nên "thắng 100%/20 seed" không phải 20 phép thử độc lập theo nghĩa cần thiết. Bài có ghi chú điều này ở Mục 6.6, tốt — nhưng vẫn để "wins on 100% of 20 seeds" trong abstract mà không kèm điều kiện.
   $\tau$ ổn định đo tính tự nhất quán, không đo tính đúng. Với 13 cụm thật và khoảng cách điểm lớn, "top-3 giữ nguyên 100%" gần như tất yếu.
9. Các điểm kỹ thuật nhỏ hơn
   Mục 4.2: lý giải $\mathcal{S}_{temp}$ dùng bậc nhất "vì lũ có quán tính" là một non-sequitur. Quán tính biện minh cho $\tau$ lớn hơn, không cho việc đổi bậc của số mũ. Sự khác biệt bậc nhất/bậc hai là về độ nhọn gần 0, không về đuôi.
   Mục 4.3: nêu Louvain "near-$\mathcal{O}(N\log N)$" như một lý do chọn, nhưng bước dựng ma trận là $\mathcal{O}(N^2)$ và matrix_to_graph cũng là vòng lặp đôi Python — nên pipeline là $\mathcal{O}(N^2)$. Trình bày độ phức tạp của Louvain như điểm bán là gây nhầm lẫn (Thí nghiệm 11 thừa nhận một phần).
   Thí nghiệm 6 báo cáo mean_diam 0.1491 km (trung bình mọi cụm, gồm 61 singleton = 0.0) trong khi mọi chỗ khác dùng biến thể multi-member0.8487 km. Không nhất quán.
   Bảng 3 ($\tau_E=0.35$ vs $\tau_F=0.25$): lý giải "E nhiễu hơn F" không thể kiểm chứng trên dataset này vì cả hai đều trơ. Nên nu là quy ước, đừng nêu là thiết kế có căn cứ.
   Ràng buộc $\mathcal{P}\in[0,2)$ đúng về toán, nhưng do $\widetilde{\mathcal{N}}$ dùng tham chiếu động, $\mathcal{P}$ không so sánh được qua thời gian — với một hệ thống điều phối trực tuyến thì đây là hạn chế thiết kế nặng hơn mức bài báo trình bày (một cụm có thể tụt hạng chỉ vì nơi khác xuất hiện cụm lớn hơn).
10. Trình bày và tính phù hợp với venue
    Abstract ~450 từ, gấp đôi chuẩn LNCS, và phần lớn là danh mục những gì không hoạt động. Về mặt tu từ, abstract hiện tại thuyết phục reviewer rằng bài không có kết quả. Cần viết lại quanh 200 từ, nêu một tuyên bố dương tính có thể bảo vệ được.
    Bài đọc như một văn bản phản biện (rebuttal) chứ không phải bài báo: "we were wrong to present it as", "the result we must report first is the one that does not favor our method", "we reportather than hide", "an artifact in our favour". Sự minh bạch này rất đáng trọng và nên giữ trong phần Threats to Validity — nhưng khi nó tràn vào abstract, contributions và conclusion thì độ giả không còn xác định được bài khẳng định điều gì.
    13 thí nghiệm cho một bài LNCS (thường 12–16 trang). Nên gộp: 1B/1C/1D/1H là kiểm tra tính chất của công thức, không phải thí nghiệm; Thí nghiệm 10 nên là một câu trong Mục 4.1.
    main.tex:43-44: email vẫn là placeholder corresponding.author@ctu.edu.vn kèm % TODO(authors). 6 tác giả không có ORCID, không phân tách affiliation.
    main.log có 5 cảnh báo Underfull \vbox và một Underfull \hbox ở dòng 114–115 — cần xử lý trước khi nộp.
    Hai hình bị xoá khỏi paper/figures/ (fig2_map.png, fig3_heatmap.png) theo git status nhưng không còn được tham chiếu — cần xác nhận không mất hình bản đồ dataset, vì một bài về phân cụm không gian rất nên có hình phân bố dữ liệu.
    Điều gì thực sự còn lại
    Sau khi trừ đi những gì Thí nghiệm 13 thu hồi (§1), những gì Thí nghiệm 6+2+4 thu hồi (§2), những gì generator quyết định (§3), $C_i$ (§4), và phần Edge AI chưa hiện thực hoá (§7):

Còn lại: một quan sát kỹ thuật đúng và hữu ích — nếu bạn nhân kernel không gian vào thay vì cộng, đồ thịự thưa và ngưỡng sparsification trở nên gần như không cần điều chỉnh. Cộng với một cách đóng gói bài toán triage (hàm ưu tiên cấp cụm với hệ số khuếch đại công bằng) được trình bày rõ ràng và có núm chính sách $\mu$ được quét đàng hoàng.

Đó là một short paper / workshop paper tốt, hoặc phần nền cho một bài đầy đủ. Nó chưa là một bài full paper, vì tuyên bố trung tâm hiện tại đã bị chính các tác giả bác bỏ và tuyên bố thay thế không bất biến theo thang đo.

Ba việc cần làm để bài này đứng được
Đổi dữ liệu, không đổi cách viết. Chạy trên dữ liệu thật (CrisisMD/FloodNet có toạ độ, hoặc dữ liệu Zalo/Facebook giai đoạn bão) hoặc ít nhất một generator có nhóm chồng lấn về không gian, mật độ không đồng đều, và tin giả có phân bố coroboration giống tin thật. Trên dữ liệu như vậy, $\mathcal{S}_{context}$ và $C_i$ mới có cơ hội chứng minh giá trị — và §2, §3, §4 mới có thể được trả lời thay vì thừa nhận.
Phát biểu lại đóng góp bằng đại lượng bất biến. Thay "cửa sổ 51×" bằng một mệnh đề đúng và kiểm chứng được: gating khiến độ nhạy với $\theta$ triệt tiêu vì $\mathcal{S}{geo}$ đã thực hiện việc thưa hoá; chứng minh điều này bằng tỉ lệ cạnh giữ lại hoặc bằng một mệnh đề giải tích về cận trên của $w{ij}$ theo khoảng cách (bài đã gần có ở Mục 6.13 đoạn cuối — hãy biến nó thành một bổ đề, đó là đóng góp mạnh nhất mà bài đang có và nó không cần thực nghiệm nào cả).
Trích dẫn dòng văn liệu product-kernel / spatially-constrained clustering và định vị lại tính mới trên nền đó. Nếu sau khi trích dẫn vẫn còn phần mới (rất có thể là: ứng dụng vào triage cứu hộ + hàm ưu tiên cấp cụm có hệ số công bằng), thì đó chính là đóng góp nên đặt lên tiêu đề — không phải cơ chế gating.
Một ghi chú cuối, thật lòng: mức độ tự soi của bản thảo này cao hơn phần lớn bài tôi đọc. Việc tự phát hiện confound $\theta$ bằng cách audit code của chính mình (Mục 6.6) là điều rất ít nhóm làm. Vấn đề không phải là thiếu trung thực — mà là sự trung thực đó đã bào mòn hết tuyên bố, và bước còn thiếu là thay dữ liệu để giành lại một tuyên bố dương tính, chứ không phải viết cẩn thận hơn về một tuyên bố đã mấ

Phản biện: "Weighted Graph-Based Event Clustering and Priority Scoring for Flood-Rescue Coordination Using Edge AI"
Kết luận tổng thể: Major Revision (nghiêng về Reject nếu nhắm hội nghị hạng A).

Bài báo có văn hoá báo cáo trung thực đáng khen — hiếm thấy một bản thảo tự bác bỏ tuyên bố chính của mình (Thí nghiệm 13). Nhưng chính sự trung thực đó lại phơi ra vấn đề: sau khi trừ hết những gì các tác giả tự thu hồi, phần đóng góp còn lại không đủ cho một bài báo, và ba trong số các con số còn sót lại cũng không đứng vững khi tôi kiểm tra lại bằng code của chính các tác giả.

1. Vấn đề nghiêm trọng nhất: "cửa sổ51×" là một artifact của cách chọn thước đo
   Đây là tuyên bố duy nhất còn sót lại sau Thí nghiệm 13, đượcặt vào abstract, kết luận và toàn bộ phần định vị đóng góp. Nó không đứng vững.

Từ exp13_theta_ranges.json:

| Dạng | Cửa sổ dùng được | Tỉ số (báo cáo) | Độ rộng tuyệt đối |
|---|---|
| Gating | [0.01, 0.51] | 51.0× | 0.50 |
| Additive α=1.0 | [0.96, 1.46] | 1.5× | 0.50 |

Hai cửa sổ rộng bằng nhau chính xác đến từng chữ số. Con số 51× chỉ tồn tại vì cửa sổ của gating bắt đầu gần 0, mà tỉ số $\theta_{hi}/\theta_{lo}$ phân kỳ khi $\theta_{lo}\to 0$. Đây là một đại lượng không bất biến theo tái tham số hoá: nếu chẩn hoá $\theta$ theo $w_{\max}$ của từng dạng (0.988 cho gating, 1.988 cho additive — số từ chính exp13_theta_ranges.json), cửa sổ trở thành [0.010, 0.516] so với [0.483, 0.734], tức 0.51 so với 0.25 — lợi thế 2×, không phải 51×. Nếu đo bằng độ rộng tuyệt đối thì lợi thế bằng 1×.

Nói cách khác, phát biểu đúng duy nhất là: cửa sổ của gating chứa gốc toạ độ, nên mọi $\theta$ nhỏ đều dùng được. Điều đó đúng, nhưng nó chỉ là cách phát biểu lại một sự thật tầm thường: $\mathcal{S}_{geo}$ đã triệt tiêu các cặp xa nên đồ thị đã thưa trước khi $\theta$ được áp. Không cần một bảng thí nghiệm và con số 51× để nói điều này, và tuyệt đối không nên đặt nó làm đóng góp trung tâm.

Yêu cầu: bỏ con số 51× hoặc thay bằng một đại lượng bất biến theo thang đo (ví dụ tỉ lệ cạnh giữ lại, hoặc $\theta$ chuẩn hoá theo $w_{\max}$/phân vị), và phát biểu lại đóng góp cho tương ứng.

2. Trên dữ liệu này, phương pháp thực chất là một ngưỡng khoảng cách
   Với $\sigma_{geo}=700$ m và $(\beta\mathcal{S}{temp}+\gamma\mathcal{S}{ctx})\le 1$, điều kiện $w_{ij}>0.05$ bắt buộc $\mathcal{S}_{geo}>0.05$, tức $d < 700\sqrt{2\ln 20} \approx 1710$ m. Toàn bộ đồ thị gating ở tham số mặc định không thể khác một đồ thị "nối mọi cặp cách nhau dưới ~1.7 km" nhiều hơn một chút về trọng số cạnh.

Chính các thí nghiệm của bài báo xác nhận điều này, và cả bốn cùng chỉ về một hướng:

Thí nghiệm 6: xoá hẳn $\mathcal{S}_{context}$ → phân hoạch bit-identical, $\tau=1.0$.
Thí nghiệm 2: quét toàn bộ lưới $\tau_F,\tau_E\in[0.15,0.5]$ → ARI và số cụm không đổi.
Thí nghiệm 4: Agglomerative trên cùng ma trận → trùng khớp tuyệt đối cả bốn chỉ số.
Tôi chạy lại pipeline: 74 cụm = 13 cụm thật + 61 singleton, và 61 singleton đó là đúng 61 điểm nhiễu gt=-1. Phân hoạch được phục hồi trọn vẹn ngoại trừ cặp 106/107.
Hệ quả: vector 7 chiều $(L,T,F,E,N,V,C)$ — điểm bán chính của bài — không đóng góp gì cho bước phân cụm. Chỉ có $(L)$ hoạt động. Phần "spatial–semantic–physical" trong tiêu đề Mục 4.2 không được dữ liệu ủng hộ. Bài báo có thừa nhận điều này ở Mục 6.6 nhưng vẫn giữ nguyên framing ở tiêu đề, abstract và Bảng 1 (dòng "Weighted graph ✓ (gating)").

Ngoại lệ duy nhất ($\beta=0.9$, ARI 0.9509) là một trường hợp tự tạo: cặp S5 cách 923 m được đặt vào dataset chính để làm $\gamma$ có việc làm. Một tham số chỉ chứng minh được giá trị của mình trên một cặp điểm được thiết k riêng cho nó thì chưa phải bằng chứng.

3. Dataset quyết định kết quả, không phải phương pháp
   Từ generate.py: 6 đảo với spread_m=250, các nhóm narative đặt trên vệ tinh cách tâm 3 km, cộng assert_gt_separable(min_sep_m=2000). Khoảng cách trong nhóm ~vài trăm mét; giữa nhóm ≥ 2 km. Bất kỳ phương pháp nào có ngưỡng cắt nằm giữa 1 và 2 km đều thu được đáp án gần hoàn hảo.

ARI = 0.9957 vì vậy đo tính khả tách của generator, không đo năng lực của phương pháp. Bài báo nói điều này trong Threats to Validity — nhưng rồi vẫn dùng ARI làm con số headline trong abstract, và tệ hơn, dùng nó làm tiêu chí "usable" ($\text{ARI}\ge 0.95$) của Thí nghiệm 13. Toàn bộ kết quả hiệu chuẩn $\theta$ thừa hưởng vấn đề này.

Việc thêm assertion khả tách để sửa lỗi co-location của phiên bản trước đã làm bài toán dễ hơn, không khó hơn. Một dataset mà ground truth bị bắt buộc phải tách được về không gian thì không thể dùng để chứng minh giá trị của một cơ chế gating không gian — vì cơ chế đó được đảm bảo thắng bởi cấu trúc dữ liệu.

4. ROC-AUC 0.9176 của bộ phát hiện tin giả là artifact, không phải năng lực phát hiện
   Đây là phát hiện tôi cho là nghiêm trọng nhất về mặt tính đúng đắn, vì bài báo trình bày nó như một kết quả định lượng có khoảng tin cậy bootstrap.

Tôi đo lại trên chính dữ liệu và công thức của các tác giả:

mean n_corrob:  fake 0.00 | real trong đảo 14.84 | real rải rác 0.00
AUC(-n_corrob) một mình = 0.9355   (cao hơn cả C_i)

Giới hạn vào 61 điểm rải rác (23 fake vs 38 real) — phép so sánh không tầm thường duy nhất:
  AUC(-C_i) = 0.4319          (dưới ngưỡng ngẫu nhiên 0.5)
  AP (-C_i) = 0.3495  vs baseline ngẫu nhiên 0.3770   (tệ hơn ngẫu nhiên)
Nguyên nhân: cả 23 tin giả đều nằm trong tập nhiễu rải rác, nên $n^{\text{corrob}}=0$; còn mọi báo cáo thật trong đảo có ~15 láng giềng. $C_i$ vì thế phân biệt "điểm này có nằm trong vùng dày đặc hay không", mà điều đó trùng khít với việc điểm có nhãn hay không — tức trùng khít với biến đích, qua một đường không liên quan gì đến tính giả mạo. Khi loại bỏ đường tắt đó, $C_i$ kém hơn đoán bừa.

Tương tự, "giảm 55% dân số ảo" không phải kết quả phát hiện: nó là phép nhân với $C_i=0.4502$, và 0.4502 đến từ việc generator gán cho báo cáo S3 giá trị has_image=False và đặt nó cô lập. Con số 55% được quyết định bởi $(b_0,b_1,b_2)$ do tác giả chọn, không bởi dữ liệu.

Yêu cầu: hoặc rút Thí nghiệm 8 và mọi tuyên bố phát hiện tin giả (bao gồm trong abstract), hoặc thiết kế lại generator để tin giả và tin thật có phân bố $n^{\text{corrob}$ và has_image chồng lấn, rồi báo cáo lại. Con số cần báo cáo là AUC/AP có điều kiện trên mật độ láng giềng, không phải AUC biên.

5. Cách trình bày HDBSCAN vẫn nghiêng về phía các tác giả
   Bài báo dành nhiều dòng để tuyên bố nó báo cáo cả những kết quả bất lợi. Nhưng ở đúng chỗ đó, nó lại mắc đúng loại artifact mà nó tự hào đã bắt được ở nơi khác. Tôi phân rã 20 cụm của HDBSCAN:

14 cụm chứa điểm có nhãn : đường kính TB 6.47 km, max 81.2 km
   → 13/14 cụm đường kính < 1.5 km; 1 cụm bị 2 điểm nhiễu kéo ra 81 km
6 cụm chỉ gồm điểm nhiễu  : đường kính TB 147.22 km
→ trung bình gộp 20 cụm  : 48.69 km  ← con số bài báo dùng
"Mean diameter 48.69 km" và "cụm trải cả tỉnh" gần như hoàn toàn do 6 cụm chỉ gồm điểm nhiễu — mà những điểm đó không thuộc cụm ground-truth nào, nên việc HDBSCAN nhóm chúng lại không phải một lỗi điều phối theo nghĩa bài báo hm ý. Phát biểu công bằng là: HDBSCAN phục hồi cả 14 nhóm thật với hình học chặt (13/14 dưới 1.5 km), cộng thêm 6 nhóm gồm toàn nhiễu. Điều đó khiến so sánh chính của Thí nghiệm 4 và 9 yếu đi đáng kể — HDBSCAN không "không dùng được về vận hành", nó chỉ xử lý thùng nhiễu khác.

Đây cũng chính là quy ước mà bài báo tuyên bố đã cẩn thận xử lý cho DBSCAN (loại nhãn $-1$ khỏi mọi thống kê) — nhưng quy ước đó không bắt được các cụm hợp lệ chỉ gồm điểm nhiễu.

6. Định vị và tính mới: thiếu hẳn một dòng văn liệu
   "Nhân $\mathcal{S}_{geo}$ vào thay vì cộng" là một product kernel — không mới, và cóít nhất ba dòng nghiên cứu đã làm đúng điều này mà bài không trích:

Bilateral filtering (Tomasi & Manduchi, ICCV 1998): tích của kernel không gian và kernel giá trị. Cùng dạng toán, cùng động lực.
Spatially constrained clustering /ClustGeo (Chavent et al., 2018), và họ contiguity-constrained clustering trong địa thống kê — bài toán "đảm bảo cụm liền mạch về không gian" đã được nghiên cứu hệ thống.
Kernel tách được trong spectral clustering có ràng buộc không gian.
Nghiêm trọng hơn: baseline mà bài so sánh — tổng cộng $\alpha\mathcal{S}{geo}+\beta\mathcal{S}{temp}+\gamma\mathcal{S}_{ctx}$ — không có trích dẫn nào cho biết ai thực sự dùng nó. Mục 2.3 viết "that additive penalty is precisely the design we compare against" nhưng không dẫn công trình nào. Một straw man tự dng, sau đó được Thí nghiệm 13 chứng minh là thậm chí không thua, thì không tạo ra tính mới.

7. Toàn bộ phần Edge AI không có bằng chứng thực nghiệm
   MobileNetV3 và DistilBERT được nêu trong tiêu đề, abstract, contribution 1 và 3, Bảng 1 — nhưng không hề được chạy. $F, E, V, N, C$ đều do generator sinh ra. Nghĩa là:

Contribution 1 (trích xuất tại biên): 0 bằng chứng.
Contribution 3 ($V_i$, $C_i$ "edge-feasible"): 0 bằng chứng — bài tự thừa nhận $V_i$ được coi là cho trước.
Thí nghiệm 10 (105–111 byte): tautology. Nó đo json.dumps của 8 con số. Không có độ trễ trên thiết bị, không có mô hình mất gói / băng thông của mạng suy giảm, không có so sánh với kích thước ảnh thật.
Với hiện trạng này, "Using Edge AI" trong tiêu đề là quá tuyên bố. Đề nghị hoặc chạy thật hai mô hình trên một thiết bị (đo latency, RAM, năng lượng), hoặc rút Edge AI khỏi tiêu đề và abstract, giữ nó ở mức "kiến trúc đề xuất".

8. Độ chặt chẽ thống kê
   Không có kiểm định ý nghĩa hay khoảng tin cậy ở bất kỳ đâu ngoài Thí nghiệm 8.
   Thí nghiệm 7: chênh lệch 2.9% (110.2 vs 113.5 phút) trên một sed, một depot, không CI, không kiểm định. Đây là nhiễu, không phải kết quả. Bài báo đã trung thực gọi nó là "small" nhưng vẫn báo cáo với 4 chữ số ý nghĩa.
   Cũng trong Thí nghiệm 7: mô phỏng phục vụ cả 74 cụm, gồm 61 singleton là nhiễu và tin giả — nên "mean arrival 2528 phút" (42 giờ). Không điều phối viên nào cử ca nô đến 61 báo cáo giả. Mô phỏng cần giới hạn ở 13 cụm thật, và cần đa sed + CI.
   20 sed của Thí nghiệm 12 tái sinh dữ liệu nhưng giữ nguyên hình học liên nhóm, nên "thắng 100%/20 seed" không phải 20 phép thử độc lập theo nghĩa cần thiết. Bài có ghi chú điều này ở Mục 6.6, tốt — nhưng vẫn để "wins on 100% of 20 seeds" trong abstract mà không kèm điều kiện.
   $\tau$ ổn định đo tính tự nhất quán, không đo tính đúng. Với 13 cụm thật và khoảng cách điểm lớn, "top-3 giữ nguyên 100%" gần như tất yếu.
9. Các điểm kỹ thuật nhỏ hơn
   Mục 4.2: lý giải $\mathcal{S}_{temp}$ dùng bậc nhất "vì lũ có quán tính" là một non-sequitur. Quán tính biện minh cho $\tau$ lớn hơn, không cho việc đổi bậc của số mũ. Sự khác biệt bậc nhất/bậc hai là về độ nhọn gần 0, không về đuôi.
   Mục 4.3: nêu Louvain "near-$\mathcal{O}(N\log N)$" như một lý do chọn, nhưng bước dựng ma trận là $\mathcal{O}(N^2)$ và matrix_to_graph cũng là vòng lặp đôi Python — nên pipeline là $\mathcal{O}(N^2)$. Trình bày độ phức tạp của Louvain như điểm bán là gây nhầm lẫn (Thí nghiệm 11 thừa nhận một phần).
   Thí nghiệm 6 báo cáo mean_diam 0.1491 km (trung bình mọi cụm, gồm 61 singleton = 0.0) trong khi mọi chỗ khác dùng biến thể multi-member0.8487 km. Không nhất quán.
   Bảng 3 ($\tau_E=0.35$ vs $\tau_F=0.25$): lý giải "E nhiễu hơn F" không thể kiểm chứng trên dataset này vì cả hai đều trơ. Nên nu là quy ước, đừng nêu là thiết kế có căn cứ.
   Ràng buộc $\mathcal{P}\in[0,2)$ đúng về toán, nhưng do $\widetilde{\mathcal{N}}$ dùng tham chiếu động, $\mathcal{P}$ không so sánh được qua thời gian — với một hệ thống điều phối trực tuyến thì đây là hạn chế thiết kế nặng hơn mức bài báo trình bày (một cụm có thể tụt hạng chỉ vì nơi khác xuất hiện cụm lớn hơn).
10. Trình bày và tính phù hợp với venue
    Abstract ~450 từ, gấp đôi chuẩn LNCS, và phần lớn là danh mục những gì không hoạt động. Về mặt tu từ, abstract hiện tại thuyết phục reviewer rằng bài không có kết quả. Cần viết lại quanh 200 từ, nêu một tuyên bố dương tính có thể bảo vệ được.
    Bài đọc như một văn bản phản biện (rebuttal) chứ không phải bài báo: "we were wrong to present it as", "the result we must report first is the one that does not favor our method", "we reportather than hide", "an artifact in our favour". Sự minh bạch này rất đáng trọng và nên giữ trong phần Threats to Validity — nhưng khi nó tràn vào abstract, contributions và conclusion thì độ giả không còn xác định được bài khẳng định điều gì.
    13 thí nghiệm cho một bài LNCS (thường 12–16 trang). Nên gộp: 1B/1C/1D/1H là kiểm tra tính chất của công thức, không phải thí nghiệm; Thí nghiệm 10 nên là một câu trong Mục 4.1.
    main.tex:43-44: email vẫn là placeholder corresponding.author@ctu.edu.vn kèm % TODO(authors). 6 tác giả không có ORCID, không phân tách affiliation.
    main.log có 5 cảnh báo Underfull \vbox và một Underfull \hbox ở dòng 114–115 — cần xử lý trước khi nộp.
    Hai hình bị xoá khỏi paper/figures/ (fig2_map.png, fig3_heatmap.png) theo git status nhưng không còn được tham chiếu — cần xác nhận không mất hình bản đồ dataset, vì một bài về phân cụm không gian rất nên có hình phân bố dữ liệu.
    Điều gì thực sự còn lại
    Sau khi trừ đi những gì Thí nghiệm 13 thu hồi (§1), những gì Thí nghiệm 6+2+4 thu hồi (§2), những gì generator quyết định (§3), $C_i$ (§4), và phần Edge AI chưa hiện thực hoá (§7):

Còn lại: một quan sát kỹ thuật đúng và hữu ích — nếu bạn nhân kernel không gian vào thay vì cộng, đồ thịự thưa và ngưỡng sparsification trở nên gần như không cần điều chỉnh. Cộng với một cách đóng gói bài toán triage (hàm ưu tiên cấp cụm với hệ số khuếch đại công bằng) được trình bày rõ ràng và có núm chính sách $\mu$ được quét đàng hoàng.

Đó là một short paper / workshop paper tốt, hoặc phần nền cho một bài đầy đủ. Nó chưa là một bài full paper, vì tuyên bố trung tâm hiện tại đã bị chính các tác giả bác bỏ và tuyên bố thay thế không bất biến theo thang đo.

Ba việc cần làm để bài này đứng được
Đổi dữ liệu, không đổi cách viết. Chạy trên dữ liệu thật (CrisisMD/FloodNet có toạ độ, hoặc dữ liệu Zalo/Facebook giai đoạn bão) hoặc ít nhất một generator có nhóm chồng lấn về không gian, mật độ không đồng đều, và tin giả có phân bố coroboration giống tin thật. Trên dữ liệu như vậy, $\mathcal{S}_{context}$ và $C_i$ mới có cơ hội chứng minh giá trị — và §2, §3, §4 mới có thể được trả lời thay vì thừa nhận.
Phát biểu lại đóng góp bằng đại lượng bất biến. Thay "cửa sổ 51×" bằng một mệnh đề đúng và kiểm chứng được: gating khiến độ nhạy với $\theta$ triệt tiêu vì $\mathcal{S}{geo}$ đã thực hiện việc thưa hoá; chứng minh điều này bằng tỉ lệ cạnh giữ lại hoặc bằng một mệnh đề giải tích về cận trên của $w{ij}$ theo khoảng cách (bài đã gần có ở Mục 6.13 đoạn cuối — hãy biến nó thành một bổ đề, đó là đóng góp mạnh nhất mà bài đang có và nó không cần thực nghiệm nào cả).
Trích dẫn dòng văn liệu product-kernel / spatially-constrained clustering và định vị lại tính mới trên nền đó. Nếu sau khi trích dẫn vẫn còn phần mới (rất có thể là: ứng dụng vào triage cứu hộ + hàm ưu tiên cấp cụm có hệ số công bằng), thì đó chính là đóng góp nên đặt lên tiêu đề — không phải cơ chế gating.
Một ghi chú cuối, thật lòng: mức độ tự soi của bản thảo này cao hơn phần lớn bài tôi đọc. Việc tự phát hiện confound $\theta$ bằng cách audit code của chính mình (Mục 6.6) là điều rất ít nhóm làm. Vấn đề không phải là thiếu trung thực — mà là sự trung thực đó đã bào mòn hết tuyên bố, và bước còn thiếu là thay dữ liệu để giành lại một tuyên bố dương tính, chứ không phải viết cẩn thận hơn về một tuyên bố đã mấ

# Kế hoạch sửa toàn bộ vấn đề phản biện — paper/ + demo/

Phạm vi đã chốt: sửa **cả code demo và bài báo**. Sinh lại dữ liệu để bỏ trần ARI.
Hình mới: TikZ cho sơ đồ kiến trúc, Python/matplotlib cho hình có dữ liệu.

**Hệ quả bao trùm:** sinh lại dataset làm **mọi con số trong main.tex thay đổi**.
Vì vậy trình tự bắt buộc là: sửa code → chạy lại toàn bộ → mới cập nhật bài báo
theo JSON mới. Không viết số vào bài trước khi có kết quả thật.

---

## Giai đoạn 1 — Sửa bộ dữ liệu (gốc của vấn đề 1.1, 2.4, 2.3)

### 1.1 `demo/data/generate.py` — tách nhãn GT khỏi tâm đảo

Hiện `narrative_scenarios()` hard-code toạ độ **đúng bằng** tâm 6 đảo lõi (đã xác
minh: 6/6 nhóm lệch < 1 m), nên nhãn 100–105 buộc phải bị gộp vào nhãn 0–5.

Sửa: đặt mỗi nhóm kịch bản ở một **vệ tinh riêng**, cách tâm đảo chủ
`SAT_OFFSET_M = 3000` m (≫ σ_geo = 700 m, nên gating tách được; vẫn cùng vùng địa
lý nên kịch bản giữ nguyên ý nghĩa vận hành). Giữ nguyên mọi thuộc tính F/E/N/V và
ý nghĩa từng kịch bản:

- S1_A / S1_B: giữ khoảng cách ~103 km (chỉ dịch cả hai ra vệ tinh) → vẫn test gating.
- S2 (5 điểm, V=2.0): vệ tinh của Đông Hà, spread nội bộ ~150 m.
- S3 (4 điểm thật + S3_FAKE): vệ tinh của Đà Nẵng; S3_FAKE giữ nguyên vị trí cô lập.
- S4A (10 điểm, F=0.35) / S4B (3 điểm, F=0.97): vệ tinh của Phú Vang / Vĩnh Linh.

Thêm assert trong `build_dataset`: mọi nhóm gt ≥ 100 phải cách **mọi** tâm đảo

> 2000 m. Nếu vi phạm → raise. Đây là bảo hiểm để lỗi không tái xuất hiện.

### 1.2 Phá cộng tuyến ngữ cảnh ↔ địa lý (vấn đề 2.4)

Hiện mỗi đảo có `base_flood ~ U(0.35,0.9)` với σ mỗi sự kiện chỉ 0.08 → F gần như
là hàm của nhãn đảo, nên τ_F/τ_E hoàn toàn vô cảm.

Sửa hai việc:

- Tăng σ nội đảo: `flood_sigma 0.08 → 0.16`, `urg_sigma 0.10 → 0.18` (chồng lấp
  giữa các đảo, ngữ cảnh không còn suy ra được đảo).
- Thêm **S5 — kịch bản ngữ cảnh trái ngược**: hai nhóm 6 điểm nằm **cạnh nhau**
  (cách 900 m, cùng cửa sổ thời gian) nhưng F đối lập (0.30 vs 0.95), nhãn
  gt = 106 / 107. Đây là ca duy nhất mà S_context *phải* làm việc — nếu bỏ γ thì
  hai nhóm này gộp lại. Nó biến exp2 (τ_F/τ_E) và exp6 (ablation γ) từ "vô cảm"
  thành có tín hiệu thật.

Kết quả: 14 nhãn GT (0–5, 100–107).

### 1.3 Tăng công suất thống kê cho C_i (vấn đề 2.3)

`n_noise 20 → 60`, tỉ lệ fake 40% → ~24 fake. Trong số fake: **~40% có ảnh**
(hiện 1/6) để C_i không còn là bản sao của cờ `has_image`. Dự kiến AUC sẽ **giảm**
so với 0.9651 — đó là kết quả trung thực hơn, và AP sẽ có ý nghĩa với ~24 dương tính.

### 1.4 Tham số hoá seed để chạy đa hạt giống (vấn đề 2.6)

- `narrative_scenarios(rng)`: nhận rng, thêm jitter ±40 m cho từng điểm kịch bản
  (hiện hoàn toàn hard-code nên không thể đo bất định của chính các nhóm quan trọng).
- `build_dataset(seed=42)` và thêm `make_events(seed)` trả về list Event **trong bộ
  nhớ**, không ghi file — để các exp đa seed lặp không đụng `dataset.json`.
- Sửa metadata: `n_gt_clusters` tính động từ nhãn thực tế (hiện hard-code 6, sai).
- Sửa docstring vùng: 16–17°N → 15.7–17.1°N (khớp metadata và bài báo).

---

## Giai đoạn 2 — Sửa pipeline (vấn đề 1.2, 1.3)

### 2.1 `demo/pipeline/weighting.py` — bỏ α straw man

Hiện `alpha: float = 0.34` cứng trong chữ ký, trong khi β = γ = 0.5 → dạng cộng bị
hạ trọng số địa lý. Sửa:

- Thêm `alpha: float = 0.5` vào `WeightParams` (`config.py`), mặc định **đối xứng**
  với β, γ.
- `edge_weight_additive` đọc `p.alpha`; `build_weight_matrix` nhận `alpha_override`
  để exp1A quét được α.
- Đồng thời thêm biến thể **cộng chuẩn hoá** `α+β+γ = 1` (α=β=γ=1/3) làm baseline
  công bằng nhất.

### 2.2 `demo/pipeline/metrics.py` — đường kính không so số 0

Hiện singleton được gán `diameters.append(0.0)` rồi lấy trung bình không trọng số →
27 cụm nhiều singleton "thắng" 6 cụm không singleton một cách giả tạo.

`geographic_spread` trả thêm:

- `mean_diameter_km_multi` — chỉ tính cụm có ≥ 2 thành viên (**số dùng để so sánh**)
- `mean_diameter_km_weighted` — trung bình có trọng số theo số điểm
- `n_singletons`, `mean_diameter_km` (giữ để tương thích, đánh dấu là chỉ tham khảo)

Mọi exp so sánh chuyển sang dùng `max_diameter_km` + `mean_diameter_km_multi`.

### 2.3 `demo/pipeline/clustering.py` — không ẩn singleton

`count_disconnected_communities` hiện bỏ qua cụm ≤ 1 phần tử. Thêm trả về
`n_singletons` và `n_evaluated` để kết luận "zero badly-connected" nêu rõ mẫu số.

### 2.4 `demo/pipeline/priority.py` — công bố mốc chuẩn hoá

`n_max = max(n_totals.values())` luôn dùng mốc **động** (cụm lớn nhất luôn Ñ = 1.0),
bài báo không nói dùng mốc nào. Thêm tham số `n_ref: float | None = None`
(None = động, số = mốc tĩnh), ghi rõ mặc định vào output JSON để bài báo trích được.

---

## Giai đoạn 3 — Sửa và bổ sung thí nghiệm

### 3.1 Sửa các exp hiện có

| File                              | Việc                                                                                                                                                                                                                                                                                         |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `exp1_formula_validation.py`    | 1A: quét α ∈ {0.34, 0.5, 1.0, 1/3-chuẩn-hoá} × {gating}; báo cả 4. 1C: thêm cột chuẩn hoá để P_add/P_mult so được (hiện 1.66 vs 1.36 đọc ngược luận điểm). 1G: giữ phân rã ARI làm**bằng chứng đã sửa** (kỳ vọng colocated = 0, ARI toàn tập ↑). |
| `exp2_sensitivity.py`           | Thêm cột`mean_diam_multi`, `max_diam`; τ_F/τ_E giờ có S5 nên kỳ vọng không còn phẳng.                                                                                                                                                                                         |
| `exp4_baselines.py`             | Bỏ dòng`Spectral (K=n_gt true GT)` **hoặc** đưa vào bảng bài báo — chọn đưa vào bảng (thông tin thật, không nên ẩn). Thêm cột `mean_diam_multi`.                                                                                                              |
| `exp7_equity_outcome.py`        | Giữ code (đã trung thực), nhưng bổ sung metric**thứ ba trung lập**: thời-gian-đến trọng số ΣV·1[F>0.7] (không dùng dạng nhân làm hàm mục tiêu). Ghi rõ trong output rằng metric ΣV thuần **ủng hộ dạng cộng**.                                     |
| `exp8_confidence_detector.py`   | Thêm**AP** vào output đã có (đang tính nhưng bài không trích) + **bootstrap 95% CI** cho AUC và AP (1000 lần lấy mẫu lại).                                                                                                                                        |
| `exp9_discriminative_metric.py` | Chỉ cập nhật số sau khi sinh lại dữ liệu.                                                                                                                                                                                                                                              |

### 3.2 Hai thí nghiệm mới

- **`exp11_scaling.py`** — đo thời gian chạy thật: n ∈ {285, 1000, 3000, 6000,
  10000} (sinh bằng `make_events` với `n_per_cluster` tăng dần), tách thời gian
  `build_weight_matrix` / `sparsify` / `run_louvain`, khớp hệ số O(n²) và báo
  ms/sự kiện. Bài báo tuyên bố khả thi thời gian thực mà không có phép đo nào.
  Kèm bản vector-hoá `build_weight_matrix_vec` (numpy broadcast) để cho thấy
  O(n²) Python thuần chỉ là chi tiết cài đặt, không phải giới hạn thuật toán.
- **`exp12_multiseed.py`** — 20 seed dữ liệu × các số headline (ARI, NMI,
  completeness, mean_diam_multi, max_diam, modularity, ARI của 4 baseline chính),
  báo **mean ± std** và min/max. Đây là số sẽ vào abstract thay cho điểm đơn.

### 3.3 Cập nhật `run_all.py`

Thêm exp11, exp12 vào trình tự (13 bước → 15 bước), sửa lại banner đánh số.

---

## Giai đoạn 4 — Hình vẽ (vấn đề mục 3)

### 4.1 Ba hình mới

- **fig_arch (TikZ, vẽ trực tiếp trong main.tex)** — sơ đồ kiến trúc 4 tầng:
  thiết bị biên (MobileNetV3 + DistilBERT lượng tử hoá) → gói metadata < 1 KB qua
  mesh/LoRa → server dựng đồ thị có trọng số (θ, k-NN) → Louvain/Leiden → xếp hạng
  P(C_k) → điều phối. Đã xác minh `tikz.sty` và `pgfplots.sty` có sẵn trong
  TeX Live của máy, không cần cài thêm.
- **fig_map (Python)** — bản đồ vùng 15.7–17.1°N: 2 panel cạnh nhau, cùng dữ liệu,
  tô màu theo cụm — dạng cộng (gộp xuyên tỉnh) vs dạng gating (vùng tác chiến gọn).
  Đây là hình chứng minh luận điểm chính trực quan nhất và hiện đang thiếu.
- **fig_heatmap (Python)** — heatmap w_ij theo (Δd, Δt) cho hai dạng công thức,
  cùng thang màu; giải thích "gating" bằng một hình thay cho nhiều đoạn văn.

### 4.2 Dọn hình mật độ thấp

- Bỏ `fig2_tanh_saturation` (chỉ là đồ thị của công thức, đã có Bảng `tab:tanh`).
- Gộp `fig1` (2 cột) + `fig3` (2 cột) thành **một hình 2 panel** `fig_ablation`.
- Kết quả: vẫn 7 hình, nhưng có sơ đồ kiến trúc + bản đồ + heatmap thay cho 3 hình
  ít thông tin. Không tăng số trang.

Sửa `make_figures.py` tương ứng; hình mới đặt tên `figXX_*.png`, copy sang
`paper/figures/`.

---

## Giai đoạn 5 — Sửa bài báo `paper/main.tex`

### 5.1 Nội dung dở dang / treo (bắt buộc)

- **main.tex:300** — tham chiếu "Table's ``domain'' group" trỏ tới bảng không tồn
  tại. Sửa bằng cách **thêm thật** `tab:params` (bảng tham số 2 nhóm domain-set /
  tunable). Bảng này đồng thời xử lý luôn đoạn tràn lề 45.11 pt ở dòng 229–230.
- Đồng bộ `tab:baselines` với fig6 (thêm dòng Spectral K = số nhãn GT).
- Thêm citation cho dòng "Event detection (TF-IDF)" trong `tab:positioning`.
- Email liên hệ → email tổ chức (@ctu.edu.vn hoặc @student.ctu.edu.vn).

### 5.2 Sửa các tuyên bố (nội dung phản biện)

- **Abstract + Conclusion**: thay "100 km → 0.30 km" bằng **max diameter
  213.95 → 1.42 km** (số cùng đơn vị so sánh, và vẫn rất mạnh); thay điểm đơn ARI
  bằng **mean ± std trên 20 seed** từ exp12; nêu α của dạng cộng ngay tại chỗ so
  sánh; **thêm Agglomerative** vào danh sách baseline được nhắc.
- **Định vị lại đóng góp**: nói thẳng rằng Agglomerative hoà điểm ⇒ đóng góp là
  **ma trận trọng số gating**, không phải bản thân Louvain. Lập luận này mạnh và
  trung thực hơn hiện tại (mục 2.5 phản biện).
- **Exp1A**: trình bày quét α, nêu rõ kết luận đứng vững ở α nào.
- **Exp2**: định khung lại — "vô cảm ≠ bền vững". Nói rõ ARI đứng yên vì bị chặn
  bởi cấu trúc, còn tín hiệu thật nằm ở đường kính; sau khi thêm S5 thì τ_F/τ_E
  mới có ảnh hưởng đo được.
- **Exp3**: nêu mẫu số (số cụm ≥ 2 phần tử) khi nói "zero badly-connected".
- **Exp7**: định khung V_agg là **lựa chọn giá trị chuẩn tắc (triage)**, không phải
  tối ưu khách quan; nói rõ metric ΣV thuần *không* ủng hộ dạng nhân — đúng như
  docstring code đã tự nhận.
- **Exp8**: báo **AP + CI cạnh AUC**, nêu rõ n_fake; mô tả C_i đúng bản chất là
  **bộ phát hiện báo cáo cô lập**, đưa phần đối kháng lên trước.
- **Setup/Dataset**: viết lại theo dataset mới (14 nhãn, ~325 sự kiện, S5, khoảng
  cách vệ tinh 3 km, ~24 fake); **xoá** đoạn giải thích trần ARI do co-location
  (đã sửa gốc, không còn đúng).
- **Threats to Validity**: xoá mục "0.892 là trần by-construction" (đã sửa); bổ
  sung mục multi-seed đã làm; giữ và làm rõ hạn chế "một bộ dữ liệu tự sinh".
- **Discussion**: thêm 1 đoạn về exp11 (độ phức tạp + thời gian chạy thật), đồng
  thời tách đoạn "Cross-disciplinary impact" đang tràn lề 26.37 pt.
- Thêm mục **Reproducibility**: seed, phiên bản thư viện, lệnh `run_all.py`.

### 5.3 `paper/references.bib`

- `campello2013hdbscan`: `@article` → `@inproceedings` (trường `journal` đang là
  tên hội nghị).
- `macqueen1967some`: thêm publisher.
- Thay `isponre2009varcc` (2009) bằng nguồn gần đây cho phát biểu thời hiện tại về
  tần suất bão (IPCC AR6 hoặc báo cáo quốc gia mới) — giữ nguồn cũ nếu cần cho số
  liệu lịch sử, nhưng chuyển câu sang thời quá khứ/nêu năm.
- Thêm 1 citation cho event detection dùng TF-IDF.

### 5.4 Typesetting

Sau khi biên dịch, quét lại `main.log`. Mục tiêu: **0 overfull > 5 pt**. Các chỗ
nặng đã biết (229–230: 45.11 pt và 23.56 pt; 386–387: 26.37 pt và 10.09 pt;
110–111: 17.06 pt; underfull badness 2126 ở 59–63) được xử lý bằng chính các sửa
đổi cấu trúc ở 5.1/5.2, phần còn lại bằng ngắt dòng/`\sloppy` cục bộ.

---

## Giai đoạn 6 — Chạy lại và xác minh

1. `demo/.venv/bin/python run_all.py` — sinh lại dataset + 12 exp + hình + dashboard.
2. Kiểm tra bất biến: `n_colocated_narrative_groups == 0`; `ari_core_only == 1.0`;
   assert khoảng cách vệ tinh không raise.
3. `latexmk -pdf main.tex` trong `paper/` (đã xác minh có `pdflatex` + `bibtex`).
4. **Đối chiếu từng số**: lập checklist mọi con số trong main.tex ↔ JSON tương ứng
   trong `demo/results/tables/`. Không để lại số cũ.
5. Quét `main.log` cho overfull/underfull và cảnh báo tham chiếu treo
   (`LaTeX Warning: Reference`).
6. Ghi báo cáo `loop/loop9/` theo đúng dạng 8 vòng trước (review_report.md +
   resolution_plan.md) để giữ nhật ký phản biện liên tục.

---

## Rủi ro cần biết trước

- **Số sẽ xấu đi ở một số chỗ.** Sau khi sửa dữ liệu: ARI có thể lên (~0.95+, do bỏ
  trần) nhưng **AUC của C_i sẽ giảm** (fake có ảnh), và **khoảng cách gating vs
  cộng theo mean diameter sẽ hẹp lại** (bỏ số 0 của singleton). Đây là mục đích của
  việc sửa — số trung thực hơn, không phải số đẹp hơn. Tôi sẽ báo cáo đúng những gì
  chạy ra, kể cả khi ngược với bài báo hiện tại.
- **Nếu α = 0.5 làm dạng cộng tốt lên đáng kể**, luận điểm 1A phải viết yếu đi
  (gating tốt hơn ở đường kính lớn nhất, chứ không phải "cộng vô dụng"). Sẽ dựa
  vào số thật để quyết định câu chữ.
- Khối lượng: ~10 file code sửa, 2 file code mới, ~3 hình mới, main.tex sửa diện
  rộng. Thứ tự trên đảm bảo mỗi bước có thể kiểm tra được trước khi đi tiếp.

# Kế hoạch sửa toàn bộ vấn đề phản biện — paper/ + demo/

Phạm vi đã chốt: sửa **cả code demo và bài báo**. Sinh lại dữ liệu để bỏ trần ARI.
Hình mới: TikZ cho sơ đồ kiến trúc, Python/matplotlib cho hình có dữ liệu.

**Hệ quả bao trùm:** sinh lại dataset làm **mọi con số trong main.tex thay đổi**.
Vì vậy trình tự bắt buộc là: sửa code → chạy lại toàn bộ → mới cập nhật bài báo
theo JSON mới. Không viết số vào bài trước khi có kết quả thật.

---

## Giai đoạn 1 — Sửa bộ dữ liệu (gốc của vấn đề 1.1, 2.4, 2.3)

### 1.1 `demo/data/generate.py` — tách nhãn GT khỏi tâm đảo

Hiện `narrative_scenarios()` hard-code toạ độ **đúng bằng** tâm 6 đảo lõi (đã xác
minh: 6/6 nhóm lệch < 1 m), nên nhãn 100–105 buộc phải bị gộp vào nhãn 0–5.

Sửa: đặt mỗi nhóm kịch bản ở một **vệ tinh riêng**, cách tâm đảo chủ
`SAT_OFFSET_M = 3000` m (≫ σ_geo = 700 m, nên gating tách được; vẫn cùng vùng địa
lý nên kịch bản giữ nguyên ý nghĩa vận hành). Giữ nguyên mọi thuộc tính F/E/N/V và
ý nghĩa từng kịch bản:

- S1_A / S1_B: giữ khoảng cách ~103 km (chỉ dịch cả hai ra vệ tinh) → vẫn test gating.
- S2 (5 điểm, V=2.0): vệ tinh của Đông Hà, spread nội bộ ~150 m.
- S3 (4 điểm thật + S3_FAKE): vệ tinh của Đà Nẵng; S3_FAKE giữ nguyên vị trí cô lập.
- S4A (10 điểm, F=0.35) / S4B (3 điểm, F=0.97): vệ tinh của Phú Vang / Vĩnh Linh.

Thêm assert trong `build_dataset`: mọi nhóm gt ≥ 100 phải cách **mọi** tâm đảo

> 2000 m. Nếu vi phạm → raise. Đây là bảo hiểm để lỗi không tái xuất hiện.

### 1.2 Phá cộng tuyến ngữ cảnh ↔ địa lý (vấn đề 2.4)

Hiện mỗi đảo có `base_flood ~ U(0.35,0.9)` với σ mỗi sự kiện chỉ 0.08 → F gần như
là hàm của nhãn đảo, nên τ_F/τ_E hoàn toàn vô cảm.

Sửa hai việc:

- Tăng σ nội đảo: `flood_sigma 0.08 → 0.16`, `urg_sigma 0.10 → 0.18` (chồng lấp
  giữa các đảo, ngữ cảnh không còn suy ra được đảo).
- Thêm **S5 — kịch bản ngữ cảnh trái ngược**: hai nhóm 6 điểm nằm **cạnh nhau**
  (cách 900 m, cùng cửa sổ thời gian) nhưng F đối lập (0.30 vs 0.95), nhãn
  gt = 106 / 107. Đây là ca duy nhất mà S_context *phải* làm việc — nếu bỏ γ thì
  hai nhóm này gộp lại. Nó biến exp2 (τ_F/τ_E) và exp6 (ablation γ) từ "vô cảm"
  thành có tín hiệu thật.

Kết quả: 14 nhãn GT (0–5, 100–107).

### 1.3 Tăng công suất thống kê cho C_i (vấn đề 2.3)

`n_noise 20 → 60`, tỉ lệ fake 40% → ~24 fake. Trong số fake: **~40% có ảnh**
(hiện 1/6) để C_i không còn là bản sao của cờ `has_image`. Dự kiến AUC sẽ **giảm**
so với 0.9651 — đó là kết quả trung thực hơn, và AP sẽ có ý nghĩa với ~24 dương tính.

### 1.4 Tham số hoá seed để chạy đa hạt giống (vấn đề 2.6)

- `narrative_scenarios(rng)`: nhận rng, thêm jitter ±40 m cho từng điểm kịch bản
  (hiện hoàn toàn hard-code nên không thể đo bất định của chính các nhóm quan trọng).
- `build_dataset(seed=42)` và thêm `make_events(seed)` trả về list Event **trong bộ
  nhớ**, không ghi file — để các exp đa seed lặp không đụng `dataset.json`.
- Sửa metadata: `n_gt_clusters` tính động từ nhãn thực tế (hiện hard-code 6, sai).
- Sửa docstring vùng: 16–17°N → 15.7–17.1°N (khớp metadata và bài báo).

---

## Giai đoạn 2 — Sửa pipeline (vấn đề 1.2, 1.3)

### 2.1 `demo/pipeline/weighting.py` — bỏ α straw man

Hiện `alpha: float = 0.34` cứng trong chữ ký, trong khi β = γ = 0.5 → dạng cộng bị
hạ trọng số địa lý. Sửa:

- Thêm `alpha: float = 0.5` vào `WeightParams` (`config.py`), mặc định **đối xứng**
  với β, γ.
- `edge_weight_additive` đọc `p.alpha`; `build_weight_matrix` nhận `alpha_override`
  để exp1A quét được α.
- Đồng thời thêm biến thể **cộng chuẩn hoá** `α+β+γ = 1` (α=β=γ=1/3) làm baseline
  công bằng nhất.

### 2.2 `demo/pipeline/metrics.py` — đường kính không so số 0

Hiện singleton được gán `diameters.append(0.0)` rồi lấy trung bình không trọng số →
27 cụm nhiều singleton "thắng" 6 cụm không singleton một cách giả tạo.

`geographic_spread` trả thêm:

- `mean_diameter_km_multi` — chỉ tính cụm có ≥ 2 thành viên (**số dùng để so sánh**)
- `mean_diameter_km_weighted` — trung bình có trọng số theo số điểm
- `n_singletons`, `mean_diameter_km` (giữ để tương thích, đánh dấu là chỉ tham khảo)

Mọi exp so sánh chuyển sang dùng `max_diameter_km` + `mean_diameter_km_multi`.

### 2.3 `demo/pipeline/clustering.py` — không ẩn singleton

`count_disconnected_communities` hiện bỏ qua cụm ≤ 1 phần tử. Thêm trả về
`n_singletons` và `n_evaluated` để kết luận "zero badly-connected" nêu rõ mẫu số.

### 2.4 `demo/pipeline/priority.py` — công bố mốc chuẩn hoá

`n_max = max(n_totals.values())` luôn dùng mốc **động** (cụm lớn nhất luôn Ñ = 1.0),
bài báo không nói dùng mốc nào. Thêm tham số `n_ref: float | None = None`
(None = động, số = mốc tĩnh), ghi rõ mặc định vào output JSON để bài báo trích được.

---

## Giai đoạn 3 — Sửa và bổ sung thí nghiệm

### 3.1 Sửa các exp hiện có

| File                              | Việc                                                                                                                                                                                                                                                                                         |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `exp1_formula_validation.py`    | 1A: quét α ∈ {0.34, 0.5, 1.0, 1/3-chuẩn-hoá} × {gating}; báo cả 4. 1C: thêm cột chuẩn hoá để P_add/P_mult so được (hiện 1.66 vs 1.36 đọc ngược luận điểm). 1G: giữ phân rã ARI làm**bằng chứng đã sửa** (kỳ vọng colocated = 0, ARI toàn tập ↑). |
| `exp2_sensitivity.py`           | Thêm cột`mean_diam_multi`, `max_diam`; τ_F/τ_E giờ có S5 nên kỳ vọng không còn phẳng.                                                                                                                                                                                         |
| `exp4_baselines.py`             | Bỏ dòng`Spectral (K=n_gt true GT)` **hoặc** đưa vào bảng bài báo — chọn đưa vào bảng (thông tin thật, không nên ẩn). Thêm cột `mean_diam_multi`.                                                                                                              |
| `exp7_equity_outcome.py`        | Giữ code (đã trung thực), nhưng bổ sung metric**thứ ba trung lập**: thời-gian-đến trọng số ΣV·1[F>0.7] (không dùng dạng nhân làm hàm mục tiêu). Ghi rõ trong output rằng metric ΣV thuần **ủng hộ dạng cộng**.                                     |
| `exp8_confidence_detector.py`   | Thêm**AP** vào output đã có (đang tính nhưng bài không trích) + **bootstrap 95% CI** cho AUC và AP (1000 lần lấy mẫu lại).                                                                                                                                        |
| `exp9_discriminative_metric.py` | Chỉ cập nhật số sau khi sinh lại dữ liệu.                                                                                                                                                                                                                                              |

### 3.2 Hai thí nghiệm mới

- **`exp11_scaling.py`** — đo thời gian chạy thật: n ∈ {285, 1000, 3000, 6000,
  10000} (sinh bằng `make_events` với `n_per_cluster` tăng dần), tách thời gian
  `build_weight_matrix` / `sparsify` / `run_louvain`, khớp hệ số O(n²) và báo
  ms/sự kiện. Bài báo tuyên bố khả thi thời gian thực mà không có phép đo nào.
  Kèm bản vector-hoá `build_weight_matrix_vec` (numpy broadcast) để cho thấy
  O(n²) Python thuần chỉ là chi tiết cài đặt, không phải giới hạn thuật toán.
- **`exp12_multiseed.py`** — 20 seed dữ liệu × các số headline (ARI, NMI,
  completeness, mean_diam_multi, max_diam, modularity, ARI của 4 baseline chính),
  báo **mean ± std** và min/max. Đây là số sẽ vào abstract thay cho điểm đơn.

### 3.3 Cập nhật `run_all.py`

Thêm exp11, exp12 vào trình tự (13 bước → 15 bước), sửa lại banner đánh số.

---

## Giai đoạn 4 — Hình vẽ (vấn đề mục 3)

### 4.1 Ba hình mới

- **fig_arch (TikZ, vẽ trực tiếp trong main.tex)** — sơ đồ kiến trúc 4 tầng:
  thiết bị biên (MobileNetV3 + DistilBERT lượng tử hoá) → gói metadata < 1 KB qua
  mesh/LoRa → server dựng đồ thị có trọng số (θ, k-NN) → Louvain/Leiden → xếp hạng
  P(C_k) → điều phối. Đã xác minh `tikz.sty` và `pgfplots.sty` có sẵn trong
  TeX Live của máy, không cần cài thêm.
- **fig_map (Python)** — bản đồ vùng 15.7–17.1°N: 2 panel cạnh nhau, cùng dữ liệu,
  tô màu theo cụm — dạng cộng (gộp xuyên tỉnh) vs dạng gating (vùng tác chiến gọn).
  Đây là hình chứng minh luận điểm chính trực quan nhất và hiện đang thiếu.
- **fig_heatmap (Python)** — heatmap w_ij theo (Δd, Δt) cho hai dạng công thức,
  cùng thang màu; giải thích "gating" bằng một hình thay cho nhiều đoạn văn.

### 4.2 Dọn hình mật độ thấp

- Bỏ `fig2_tanh_saturation` (chỉ là đồ thị của công thức, đã có Bảng `tab:tanh`).
- Gộp `fig1` (2 cột) + `fig3` (2 cột) thành **một hình 2 panel** `fig_ablation`.
- Kết quả: vẫn 7 hình, nhưng có sơ đồ kiến trúc + bản đồ + heatmap thay cho 3 hình
  ít thông tin. Không tăng số trang.

Sửa `make_figures.py` tương ứng; hình mới đặt tên `figXX_*.png`, copy sang
`paper/figures/`.

---

## Giai đoạn 5 — Sửa bài báo `paper/main.tex`

### 5.1 Nội dung dở dang / treo (bắt buộc)

- **main.tex:300** — tham chiếu "Table's ``domain'' group" trỏ tới bảng không tồn
  tại. Sửa bằng cách **thêm thật** `tab:params` (bảng tham số 2 nhóm domain-set /
  tunable). Bảng này đồng thời xử lý luôn đoạn tràn lề 45.11 pt ở dòng 229–230.
- Đồng bộ `tab:baselines` với fig6 (thêm dòng Spectral K = số nhãn GT).
- Thêm citation cho dòng "Event detection (TF-IDF)" trong `tab:positioning`.
- Email liên hệ → email tổ chức (@ctu.edu.vn hoặc @student.ctu.edu.vn).

### 5.2 Sửa các tuyên bố (nội dung phản biện)

- **Abstract + Conclusion**: thay "100 km → 0.30 km" bằng **max diameter
  213.95 → 1.42 km** (số cùng đơn vị so sánh, và vẫn rất mạnh); thay điểm đơn ARI
  bằng **mean ± std trên 20 seed** từ exp12; nêu α của dạng cộng ngay tại chỗ so
  sánh; **thêm Agglomerative** vào danh sách baseline được nhắc.
- **Định vị lại đóng góp**: nói thẳng rằng Agglomerative hoà điểm ⇒ đóng góp là
  **ma trận trọng số gating**, không phải bản thân Louvain. Lập luận này mạnh và
  trung thực hơn hiện tại (mục 2.5 phản biện).
- **Exp1A**: trình bày quét α, nêu rõ kết luận đứng vững ở α nào.
- **Exp2**: định khung lại — "vô cảm ≠ bền vững". Nói rõ ARI đứng yên vì bị chặn
  bởi cấu trúc, còn tín hiệu thật nằm ở đường kính; sau khi thêm S5 thì τ_F/τ_E
  mới có ảnh hưởng đo được.
- **Exp3**: nêu mẫu số (số cụm ≥ 2 phần tử) khi nói "zero badly-connected".
- **Exp7**: định khung V_agg là **lựa chọn giá trị chuẩn tắc (triage)**, không phải
  tối ưu khách quan; nói rõ metric ΣV thuần *không* ủng hộ dạng nhân — đúng như
  docstring code đã tự nhận.
- **Exp8**: báo **AP + CI cạnh AUC**, nêu rõ n_fake; mô tả C_i đúng bản chất là
  **bộ phát hiện báo cáo cô lập**, đưa phần đối kháng lên trước.
- **Setup/Dataset**: viết lại theo dataset mới (14 nhãn, ~325 sự kiện, S5, khoảng
  cách vệ tinh 3 km, ~24 fake); **xoá** đoạn giải thích trần ARI do co-location
  (đã sửa gốc, không còn đúng).
- **Threats to Validity**: xoá mục "0.892 là trần by-construction" (đã sửa); bổ
  sung mục multi-seed đã làm; giữ và làm rõ hạn chế "một bộ dữ liệu tự sinh".
- **Discussion**: thêm 1 đoạn về exp11 (độ phức tạp + thời gian chạy thật), đồng
  thời tách đoạn "Cross-disciplinary impact" đang tràn lề 26.37 pt.
- Thêm mục **Reproducibility**: seed, phiên bản thư viện, lệnh `run_all.py`.

### 5.3 `paper/references.bib`

- `campello2013hdbscan`: `@article` → `@inproceedings` (trường `journal` đang là
  tên hội nghị).
- `macqueen1967some`: thêm publisher.
- Thay `isponre2009varcc` (2009) bằng nguồn gần đây cho phát biểu thời hiện tại về
  tần suất bão (IPCC AR6 hoặc báo cáo quốc gia mới) — giữ nguồn cũ nếu cần cho số
  liệu lịch sử, nhưng chuyển câu sang thời quá khứ/nêu năm.
- Thêm 1 citation cho event detection dùng TF-IDF.

### 5.4 Typesetting

Sau khi biên dịch, quét lại `main.log`. Mục tiêu: **0 overfull > 5 pt**. Các chỗ
nặng đã biết (229–230: 45.11 pt và 23.56 pt; 386–387: 26.37 pt và 10.09 pt;
110–111: 17.06 pt; underfull badness 2126 ở 59–63) được xử lý bằng chính các sửa
đổi cấu trúc ở 5.1/5.2, phần còn lại bằng ngắt dòng/`\sloppy` cục bộ.

---

## Giai đoạn 6 — Chạy lại và xác minh

1. `demo/.venv/bin/python run_all.py` — sinh lại dataset + 12 exp + hình + dashboard.
2. Kiểm tra bất biến: `n_colocated_narrative_groups == 0`; `ari_core_only == 1.0`;
   assert khoảng cách vệ tinh không raise.
3. `latexmk -pdf main.tex` trong `paper/` (đã xác minh có `pdflatex` + `bibtex`).
4. **Đối chiếu từng số**: lập checklist mọi con số trong main.tex ↔ JSON tương ứng
   trong `demo/results/tables/`. Không để lại số cũ.
5. Quét `main.log` cho overfull/underfull và cảnh báo tham chiếu treo
   (`LaTeX Warning: Reference`).
6. Ghi báo cáo `loop/loop9/` theo đúng dạng 8 vòng trước (review_report.md +
   resolution_plan.md) để giữ nhật ký phản biện liên tục.

---

## Rủi ro cần biết trước

- **Số sẽ xấu đi ở một số chỗ.** Sau khi sửa dữ liệu: ARI có thể lên (~0.95+, do bỏ
  trần) nhưng **AUC của C_i sẽ giảm** (fake có ảnh), và **khoảng cách gating vs
  cộng theo mean diameter sẽ hẹp lại** (bỏ số 0 của singleton). Đây là mục đích của
  việc sửa — số trung thực hơn, không phải số đẹp hơn. Tôi sẽ báo cáo đúng những gì
  chạy ra, kể cả khi ngược với bài báo hiện tại.
- **Nếu α = 0.5 làm dạng cộng tốt lên đáng kể**, luận điểm 1A phải viết yếu đi
  (gating tốt hơn ở đường kính lớn nhất, chứ không phải "cộng vô dụng"). Sẽ dựa
  vào số thật để quyết định câu chữ.
- Khối lượng: ~10 file code sửa, 2 file code mới, ~3 hình mới, main.tex sửa diện
  rộng. Thứ tự trên đảm bảo mỗi bước có thể kiểm tra được trước khi đi tiếp.
