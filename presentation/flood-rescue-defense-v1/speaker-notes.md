# Ghi chú thuyết trình · Bản 01

Giả định thời lượng: khoảng 20–25 phút, chưa gồm hỏi đáp. Phần chính dừng ở slide 23.

## 1. Kiểm thử gom cụm và xếp hạng tin báo cứu hộ lũ lụt

Mở đầu: Bài báo kiểm tra liệu các bảo đảm ở bước gom cụm và tính điểm có chuyển thành kết quả điều phối tốt hơn trong mô phỏng hay không. Đây là nghiên cứu trên dữ liệu bán tổng hợp và tổng hợp. Không giới thiệu như một chính sách cứu hộ đã được xác nhận.

Nguồn: `paper/main.tex`

## 2. Nhiều tin báo, nhưng có bao nhiêu sự cố?

Dùng hình minh họa: A có nhiều bản sao, B gần A nhưng là sự cố khác, C là nhóm báo cáo giả. Đặt câu hỏi: một đội cứu hộ nên đi đâu trước? Hình là sơ đồ minh họa, không phải dữ liệu hay bản đồ thực nghiệm.

Nguồn: `paper/main.tex`

## 3. Ba tầng cần ba phép đánh giá

Khoảng trống của bài: các tài nguyên được thảo luận chưa cung cấp đồng thời nhãn liên kết sự cố, ưu tiên cứu hộ và kết quả điều phối. Đọc ba RQ trước khi giới thiệu công thức. ARI là mức đồng thuận phân hoạch đã hiệu chỉnh ngẫu nhiên, không phải phần trăm đúng. NDCG@5 đo chất lượng xếp hạng năm vị trí đầu so với benefit lý tưởng.

Nguồn: `paper/main.tex`

## 4. Xác lập tính chất và đo giới hạn

Không gắn đóng góp với một tuyên bố phương pháp luôn thắng. Phần mới cần bảo vệ là cách kiểm tra phạm vi của từng tính chất và đo hệ quả phía sau. Các kết quả bất lợi vẫn trả lời các giả thuyết nghiên cứu, nhưng không tự tạo thành bằng chứng hiệu quả ứng dụng.

Nguồn: `paper/main.tex`

## 5. Một bộ bán tổng hợp, một bộ tổng hợp

Nói rõ ngay từ đầu thay vì để hội đồng tự phát hiện ở cuối. WorldPop là bề mặt dân số, không phải số người mắc kẹt được quan sát. Candidate 4.1 không được mô tả là neo vào EMSR848. Tổng số 26.288 và 30.229 tính trên cả ba phần chia, không phải số mẫu test. Hai bộ riêng không được cộng thành một benchmark duy nhất.

Nguồn: `paper/main.tex`

## 6. Vì sao lựa chọn dữ liệu được sinh?

Đây là lý do phương pháp luận được hỗ trợ bởi thiết kế trong bài, không phải tuyên bố không tồn tại dữ liệu thực ở mọi nơi. Không nói đã kiểm thử dữ liệu thực hay đã thử thay thế dữ liệu. Hai bộ có vai trò đánh giá khác nhau; điều đó không chứng minh tính độc lập ngoài miền hoặc hợp thức hóa kết luận xuyên hai bộ.

Nguồn: `paper/main.tex`

## 7. Bất lợi ảnh hưởng trực tiếp đến kết luận

Không diễn đạt rằng dữ liệu tổng hợp tự nó vô giá trị. Nó hỗ trợ kiểm thử có kiểm soát nhưng không xác định được tỷ lệ lỗi hay hiệu quả ngoài thực địa. Nhấn mạnh sự khác nhau giữa tổng hợp bối cảnh, tổng hợp tin báo và tổng hợp kết quả. RQ1 có bối cảnh bán tổng hợp, còn incident/report labels và outcomes là mô phỏng.

Nguồn: `paper/main.tex`

## 8. Thuật toán không được xem nhãn đánh giá

Giới thiệu L và T trước vì cần để tính khoảng cách và độ lệch thời gian. F/E là evidence đầu vào của nghiên cứu thuật toán, không coi chúng là bằng chứng extractor ngoài thực tế đã chính xác. Q dựa ảnh và corroboration từ payload quan sát được. Manual-review là ranh giới thiết kế; benchmark RQ1 hiện chưa thực thi stress thiếu L/T.

Nguồn: `paper/main.tex`

## 9. Khóa lựa chọn trước khi mở tập test

Mỗi bộ có split 20/20/40 riêng. Oracle grouping nghĩa là dùng nhóm sự cố đúng của mô phỏng chỉ trong RQ2 để loại sai số gom cụm khỏi phép đánh giá điểm. Không cho scheduler xem oracle. RQ3 không dùng 120 mẫu độc lập vì ba resource scenarios của cùng seed có phụ thuộc. Bootstrap và Wilcoxon/Holm trả lời các câu hỏi khác nhau.

Nguồn: `paper/main.tex`

## 10. Product dùng khoảng cách làm cổng

Công thức rút gọn cho trường hợp đã có L/T và contextual inputs, đúng với benchmark RQ1 hiện tại. G là Gaussian theo khoảng cách; T là suy giảm mũ theo chênh thời gian; C là tương đồng ngữ cảnh. Không mô tả so sánh pipeline tinh chỉnh độc lập là tác động nhân quả riêng của toán tử nhân.

Nguồn: `paper/main.tex`

## 11. Chặn cạnh không tự chặn đường kính cụm

Đặt B=β+γ. Vì T,C≤1, w×≤B exp(-d²/(2σ²)); với 0<θ<B suy ra chặn. Kết quả nói về từng cạnh được giữ. Muốn chặn đường kính cụm còn cần hop diameter quan sát được h; pipeline không kiểm soát trước h. Không diễn giải định lý là Product phải đạt ARI tốt hơn.

Nguồn: `paper/main.tex`

## 12. Chưa xác lập ưu thế của Product

Thanh ngang là khoảng tin cậy bootstrap 95% riêng từng phương pháp. Không dùng độ chồng lấn của các khoảng này để thay kiểm định ghép. Chênh lệch Product−Additive có CI bootstrap chưa hiệu chỉnh [-0.02257,-0.00240] nhưng Wilcoxon/Holm p=.2560; khác phương pháp và hiệu chỉnh nên không đọc như một kiểm định duy nhất. Bảng đầy đủ ở phụ lục.

Nguồn: `thucnghiem/results/cij_baseline_benchmark_results/benchmark_summary.csv`

## 13. Bản sao 5× làm suy giảm mạnh gom cụm

Màu và số là ARI tuyệt đối từ primary stress CSV, chỉ tính các báo cáo gốc có incident labels để giữ đơn vị đánh giá giữa các multiplicities. GPS là sigma nhiễu độc lập trên mỗi trục địa phương; time là sigma phút. Bản sao 2x tăng nhẹ, 5x giảm mạnh, không suy ngưỡng sụp đổ hoặc xu hướng đơn điệu. Các mức này là stress có kiểm soát, không phải tần suất thực địa. MD = matched density.

Nguồn: `thucnghiem/results/rq1_results/aggregate/rq1_stress_summary.csv`

## 14. Một bản sao không tạo thêm bằng chứng

Họ bằng chứng được hình thành bởi fingerprint exact và connected components cho near duplicates. Không đánh đồng họ fingerprint với nguồn độc lập đã xác thực. Max không đếm các báo cáo chồng lấn như những người khác nhau, nhưng có thể bỏ sót nhu cầu ở các trường hợp khác. Không hứa chống mọi tấn công.

Nguồn: `paper/main.tex`

## 15. Chưa xác lập đồng chỉnh với lợi ích

Giải thích NDCG@5: so sánh chất lượng năm vị trí đầu với thứ tự benefit lý tưởng. Benefit là nhãn sinh độc lập trong mô phỏng, không phải đánh giá chuyên gia hay lợi ích quan sát được ngoài hiện trường. Revised có point estimate thấp hơn random/population-only; không tuyên bố random thắng có ý nghĩa thống kê từ hai trung bình. CI bootstrap 95%.

Nguồn: `thucnghiem/results/rq2_results/rq2_summary.csv`

## 16. Bất biến bản sao có phạm vi hẹp

Độ trôi = trị tuyệt đối thay đổi điểm được chuẩn hóa, không phải xác suất tin giả. Mỗi kịch bản hiển thị có 40 perturbations/estimator. Các thanh chỉ mô tả trung bình, không có CI cho từng thanh. Exact 2x/5x/10x cho revised drift 0 khi nhóm và input cố định. Campaign: revised≈.1688, legacy≈.0309. Hiệu số độ trôi +.1379 bất lợi cho revised; Holm p≈9.1e-12 từ bài.

Nguồn: `thucnghiem/results/rq2_results/rq2_robustness_test.csv`

## 17. Lập lịch trên các cụm được dự đoán

Không so sánh ARI từ Generator 3.0 với harm Candidate 4.1 như hai đầu của cùng mẫu. RQ3 tự có predicted partitions và đối chứng oracle trong Candidate. Harm là điểm thiệt hại latent do mô hình mô phỏng quy định, không phải số ca tử vong hay người cứu được quan sát. Nearest-first là baseline chi phí di chuyển, không phải chính sách cứu hộ đã được xác nhận.

Nguồn: `paper/main.tex`

## 18. Nearest-first có trung bình thấp hơn

Các cột là trung bình trên 40 seeds trong từng resource scenario; không coi ba conditions thành ba mẫu độc lập. Hai panel có đơn vị và thang khác nhau, đều bắt đầu từ 0. Không có CI của từng scenario trên hình này, nên chỉ đọc mô tả. Kiểm định ghép theo seed nằm ở slide tiếp theo. Không diễn giải thành kết luận thực địa.

Nguồn: `thucnghiem/results/rq3_results/rq3_dispatch_test.csv`

## 19. Chưa xác lập lợi ích tổng quát của revised

Số liệu từ CSV reanalysis cấp seed, 40 cặp. Đọc chênh lệch thô, không lấy cột mean định hướng lợi ích rồi đặt nhãn revised-minus-baseline. Deadline p trong CSV là khoảng 1.17e-6, trong paper prose khoảng 1.3e-6; slide giữ giá trị CSV và nguồn để kiểm tra. Kết luận về ý nghĩa không thay đổi. Không gọi không-significant là tương đương hoặc không có tác động.

Nguồn: `thucnghiem/results/rq3_results/rq3_paired_comparisons_seed.csv`

## 20. Ba kết quả, ba phạm vi bằng chứng

Trở lại câu hỏi trung tâm. Không mô tả mọi kết quả âm là bằng chứng mô hình vô dụng; chúng chỉ bác bỏ hoặc chưa xác lập những ưu thế trong phạm vi đã kiểm tra. Các RQ dùng hai bộ riêng, nên bảng này là tổng hợp kết luận theo tầng, không phải một phép đo nhân quả từ đầu đến cuối.

Nguồn: `paper/main.tex`

## 21. Bước tiếp theo phải bổ sung bằng chứng

Slide trả lời trực tiếp câu hỏi tại sao cần Limits/Future work. Giới hạn dữ liệu đã trình ở đầu; cuối chỉ gắn từng giới hạn với phép kiểm chứng phù hợp. Đây là đề xuất tiếp theo, không phải kết quả đã chạy. Không hứa một kế hoạch đã có tài trợ, đối tác hay thời hạn. Có thể nhắc audit dữ liệu hiện hữu khi hỏi đáp, nhưng không đưa số liệu khảo sát mới vào kết quả bài báo.

Nguồn: `paper/main.tex`

## 22. Điều bài báo xác lập được

Kết thúc bằng ba câu trả lời cho RQ. Có thể nói: Chúng tôi chỉ ra rằng các bảo đảm ở một bước chưa chuyển thành lợi ích điều phối trong các mô phỏng đã thử; cần kiểm chứng độc lập bằng dữ liệu và đánh giá phù hợp trước khi mở rộng kết luận.

Nguồn: `paper/main.tex`

## 23. Cảm ơn hội đồng

Dừng tại đây trong phần trình bày chính. Dùng O để mở mục lục; các slide dự phòng A1–A5 ở cuối. Không trình chiếu phụ lục tuần tự trừ khi hội đồng yêu cầu.

Nguồn: `paper/main.tex`

## A1. Câu trả lời ngắn về dữ liệu tổng hợp

Trả lời trong 30–45 giây rồi dừng để hội đồng hỏi sâu. Không nói không có dữ liệu thực ở bất kỳ đâu, không đồng nhất nhãn cần chú ý tin nhắn với benefit cứu hộ và không dùng dân số làm người mắc kẹt.

Nguồn: `paper/main.tex`

## A2. Điều kiện của chặn không gian

Bằng chứng: a_i a_j≤1 và T,C≤1, nên w×≤B exp(-d²/2σ²). Lấy θ<w× rồi log cho chặn. Với additive, θ<αG+B dẫn tới chặn chỉ khi θ>B. Quy tắc symmetrized top-k có thể làm degree vượt k.

Nguồn: `paper/main.tex`

## A3. Đầy đủ baseline gom cụm

Đối chiếu paper Table 2 và benchmark_summary.csv. Product dùng q=.90, k=8, σ=700m; additive tinh chỉnh độc lập q=.95, k=8, σ=700m; cả hai resolution 1.2. Product−MD additive ARI≈+.00989, CI [-.00100,.02082], Holm p=.2560. Các CI riêng không thay kiểm định ghép.

Nguồn: `thucnghiem/results/cij_baseline_benchmark_results/benchmark_summary.csv`

## A4. Vai trò của các hằng số heuristic

Các aggregation dùng confidence-gated family maxima; công thức rút gọn trên slide gọi W để đọc dễ, xem Eq.4 bản tiếng Anh để biết chuẩn hóa N và clipping N/V. Không suy Nref/Vcap không có tác dụng chỉ vì mean NDCG giữ nguyên ở mức đã báo cáo. Chưa có xác nhận chuyên gia cho các trọng số.

Nguồn: `paper/main.tex`

## A5. Đọc đúng độ bất định và dấu hiệu ứng

sources.json lưu đường dẫn, SHA-256 và rows biểu đồ. Đọc bibliography của bài nếu cần nguồn nghiên cứu trước. Bản HTML tự chứa font và đồ họa, không gửi dữ liệu hay phụ thuộc CDN. Deadline-miss Holm p trong CSV khoảng 1.1745e-6, prose bài khoảng 1.3e-6; chênh lệch đã ghi trong manifest.

Nguồn: `paper/main.tex`
