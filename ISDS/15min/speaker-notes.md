# English

## Slide 01

Good morning everyone. Today, I will share our study on flood-rescue reports. In a flood, rescue teams receive many messages, and some are repeated, missing details, or even false. Our study asks a practical question: how can we turn these uncertain reports into incident groups, priority lists, and rescue trips? And more importantly, how do errors in one step affect the next?

## Slide 02

Our talk has six parts. First, we look at the rescue problem and related studies. Next, I will explain our synthetic dataset and our three-step method. Finally, we will look at the test results, main lessons, and future work.

## Slide 03

Imagine you are managing rescue boats in this flooded town. This picture is an illustration, not a real event. Many families need help, but you only have a few boats. You cannot see the whole town. Instead, you only look at a tablet with incoming reports. Each report gives a location, a time, maybe a photo, and claims about how many people are trapped or how urgent the situation is. However, these reports can be incomplete, repeated, or wrong. Before you send a boat, you must make three decisions. First, identify: which reports talk about the same incident? Second, prioritize: which incident is the most urgent? And third, schedule: which trips can your boats actually make in time?

## Slide 04

Looking at these three scenes, we can see why grouping reports is so important. In the first scene on the left, three messages describe the exact same house. If we fail to group them, we might send three boats to the same family and waste resources. In the middle scene, two houses are close to each other, but they are separate incidents. If we wrongly merge them into one group, we might miss one family completely. In the right scene, several fake reports point to empty water. Even if many messages say the same thing, it does not make the incident real. These grouping errors change our map of destinations before we even start ranking or planning routes. Because a good result at one step does not guarantee a good final rescue plan, we must test all three steps together.

## Slide 05

Our study connects three research areas. First, crisis sensing extracts flood information from social media posts and images, but it does not tell us which physical incident each message belongs to. Second, community detection algorithms, like Louvain, can group similar reports together, but a group of reports is not always a real rescue destination. Third, humanitarian logistics plans boat routes and balances fairness and speed, but it assumes the list of destinations is already correct. The gap between these areas is clear: what happens to rescue plans when upstream grouping and scoring make mistakes? We answer this through three research questions: RQ1 tests grouping, RQ2 tests priority ranking, and RQ3 tests rescue dispatch.

## Slide 06

To test failures clearly, we need to know the ground truth, so we generate a controlled synthetic dataset in four steps. In step one, we set the scenario. For our clustering tests, we use real map data from Central Vietnam, including Copernicus flood maps, OpenStreetMap, and WorldPop population data. For ranking and dispatch, we use a fully synthetic region. In step two, we simulate sixteen hidden incidents in each run. In step three, we generate observable reports from those incidents, including GPS location, time, flood level, urgency, and people count. In step four, we add controlled noise: exact copies, near copies, random fake reports, and coordinated false campaigns. Using real maps makes the locations realistic, while simulated incidents give us exact answers to check where the algorithms fail. However, the reports themselves are simulated, so tests with real, independently labeled reports are still needed.

## Slide 07

This diagram shows the most important rule in our study: the information boundary. Above the orange dashed line is what the algorithm can see. It only reads report fields like location, time, flood level, urgency, people count, and vulnerability. Using only this information, it groups reports, calculates priority scores, and schedules boat trips. If a report is missing location or time, it goes to manual review. Below the orange line is the hidden ground truth, such as true incident IDs, fake labels, deadlines, and harm values. We lock all algorithm predictions first, and only open the ground truth at the very end to calculate evaluation scores. We generate eighty runs in total: twenty for development, twenty for tuning settings, and forty held-out runs for final testing. All results today come from those forty test runs.

## Slide 08

Now let's look at how we group reports in RQ1. For every pair of reports, we calculate three similarity scores between zero and one: geographic distance G, time difference T, and report evidence C. We compare two ways to combine them into an edge weight. The Additive rule simply adds distance, time, and evidence together. The Product rule multiplies distance G with the sum of time and evidence. Look at the chart on the right for two reports with the exact same time and evidence. As distance increases to three kilometers, the Product weight drops to zero, acting as a geographic gate. In contrast, the Additive weight still keeps half of its maximum value even when reports are very far apart. Next, we keep only the strongest links using a threshold and top-k neighbors, and run Louvain to find communities. In theory, Product stops long-distance links, but we must test if this actually improves clustering.

## Slide 09

Once we have incident groups, how do we rank them and plan trips? Inside each group, we first put exact copies and near copies into evidence families. Each family contributes only one value: its maximum value weighted by report confidence Q. Then, we calculate a bounded priority score P. It combines urgency, flood level, and people count, and multiplies them by a vulnerability boost. This keeps the priority score strictly between zero and two. Because we take the maximum within each family, adding an exact copy into an existing family does not change the score at all, as long as the families and inputs stay fixed. However, this mathematical rule only stops duplicate copies; it cannot tell if a report is lying. Finally, the scheduler takes these groups and priority scores to assign boat trips based on travel time, service time, and available boats.

## Slide 10

Let's move to the results, starting with clustering accuracy on the forty test runs. We measure accuracy using Adjusted Rand Index, or ARI, where one is a perfect match. Graph-based methods clearly perform best, all scoring around 0.90 to 0.92, while coordinate K-means reaches 0.82 and the DBSCAN variants stay below 0.50. Comparing our two main rules, independently tuned Additive Louvain reaches 0.9191, and Product Louvain reaches 0.9072. After statistical correction, the p-value is 0.2560. This means the difference is not statistically significant, and the Product gate does not show an accuracy advantage over Additive.

## Slide 11

Next, we stress-test the clustering methods under seven fixed noise conditions without retuning their settings. As expected, adding GPS location noise or time noise reduces accuracy for every method. When we duplicate reports twice, accuracy rises slightly. However, when we add five exact copies per report, all four graph methods collapse to an ARI of about 0.30. One possible reason is that the copies crowd each node's top-k neighbors, but our protocol does not isolate the mechanism. Also, while Product Louvain keeps fake reports out of real incidents, those fake reports group together and create false destinations 16.49 percent of the time. This brings us back to the third scene in our introduction: blocking long links does not stop fake groups from forming.

## Slide 12

In RQ2, we test priority ranking on true incident groups so clustering errors cannot interfere. On the left chart, we measure how well the top five ranked incidents match the simulated rescue benefit using NDCG at five. Our revised score gets 0.6669, which is slightly higher than the legacy score at 0.6548, but the difference is not significant. In fact, simple population sorting and random ordering get similar numbers around 0.67. On the right chart, we check score stability when reports are manipulated. With two, five, or ten exact copies, our revised score has zero drift, as expected when evidence families and inputs stay fixed. However, when attackers inflate people counts or run a coordinated false campaign, the revised score shifts much more than the legacy score. So, stability against exact copies does not mean better ranking or protection against coordinated lies.

## Slide 13

In RQ3, we look at rescue dispatch using the predicted Product groups. In these two charts, bars above zero mean our revised priority performs worse than the comparator. Compared to the legacy priority, our revised rule has about fourteen more units of simulated harm and reduces missed deadlines by about two percentage points; neither difference is statistically significant. However, compared to a simple nearest-first rule, our revised priority causes nearly seventy more units of harm and eighteen percentage points more missed deadlines, which is a significant gap. One plausible reason is that ranking by need alone does not fully account for boat travel time, but this experiment does not isolate that mechanism. Furthermore, using Product groups causes eighteen more units of harm than matched-density Additive groups. This shows that upstream grouping errors do reach the rescue schedule. Note that harm here is a simulated cost, not real injuries, and nearest-first is not endorsed as a field policy.

## Slide 14

To conclude, our main takeaway is that local mathematical guarantees do not automatically create better rescue decisions. In clustering, spatial gating limits link distance, but did not beat additive grouping and still collapsed under fivefold copies. In ranking, copy invariance stops simple duplicates, but did not improve benefit alignment or stop coordinated attacks. And in dispatch, a bounded need score did not beat nearest-first routing. Our main contribution is a transparent, fail-closed evaluation pipeline with hidden truth and an open-source benchmark artifact. Before any real-world use, future work must test on real disaster reports, check source authenticity, and combine priority ranking directly with travel time limits.

## Slide 15

Here are the key references for our clustering, ranking, and evaluation methods.

## Slide 16

And these are the references for our crisis datasets, geographic map sources, and our public GitHub release.

## Slide 17

Thank you very much for your attention. I would be happy to answer any questions.

## Slide 18 (Backup)

This backup slide summarizes our experimental protocol. First, we use two separate data bundles: Generator 3.0 with Central Vietnam map anchors for RQ1 clustering, and Candidate 4.1 with synthetic geometry for RQ2 ranking and RQ3 dispatch. Second, to respect the information boundary, RQ2 tests ranking on true oracle groups, while RQ3 schedules boat trips on predicted clusters without seeing the ground truth. Third, for dispatch statistics, we average the three boat-resource scenarios within each seed to form forty independent test pairs. Finally, our exact-copy invariance holds strictly when evidence families and input fields remain fixed.

## Slide 19 (Backup)

This slide covers four common questions. First, in RQ1, the unadjusted bootstrap confidence interval between Product and Additive does not cross zero, but the Holm-adjusted Wilcoxon p-value is 0.2560. Because they use different statistical procedures and we correct for multiple comparisons, we do not claim any winner. Second, switching from Louvain to Leiden gives an ARI of 0.9165, which is not significantly different from Product Louvain. Third, we tested twenty-one parameter variations one at a time for our scoring formula, and the average NDCG at five changed by less than 0.01, showing local parameter stability. Fourth, we use synthetic data because real flood streams do not give us exact incident truth or controlled duplicate levels needed to diagnose pipeline failures.

# Tiếng Việt

## Slide 01

Kính chào quý thầy cô và các bạn. Hôm nay, tôi xin chia sẻ nghiên cứu của chúng tôi về báo cáo cứu hộ ngập lụt. Trong lũ lụt, các đội cứu hộ nhận được rất nhiều tin báo, một số bị trùng lặp, thiếu chi tiết hoặc thậm chí là giả. Nghiên cứu đặt ra một câu hỏi thực tế: làm sao biến các báo cáo chưa chắc chắn này thành nhóm sự cố, danh sách ưu tiên và các chuyến cứu hộ? Và quan trọng hơn, lỗi ở một bước sẽ ảnh hưởng đến bước tiếp theo như thế nào?

## Slide 02

Bài trình bày gồm sáu phần. Đầu tiên là bài toán cứu hộ và các nghiên cứu liên quan. Tiếp theo, tôi sẽ giải thích bộ dữ liệu mô phỏng và phương pháp ba bước của chúng tôi. Cuối cùng là kết quả thử nghiệm, bài học chính và hướng phát triển.

## Slide 03

Hãy hình dung bạn đang điều phối các thuyền cứu hộ tại thị trấn ngập lụt này. Đây là hình minh họa giả định, không phải sự kiện thật. Nhiều gia đình cần giúp đỡ, nhưng bạn chỉ có vài chiếc thuyền. Bạn không thể nhìn thấy toàn cảnh thị trấn mà chỉ nhìn vào máy tính bảng nhận tin báo. Mỗi báo cáo có vị trí, thời gian, có thể kèm ảnh, và thông tin về số người mắc kẹt hay mức độ khẩn cấp. Tuy nhiên, tin báo có thể thiếu, trùng lặp hoặc sai. Trước khi cử thuyền đi, bạn phải đưa ra ba quyết định. Một là xác định: những báo cáo nào cùng nói về một sự cố? Hai là ưu tiên: sự cố nào khẩn cấp nhất? Và ba là lập lịch: những chuyến đi nào thuyền có thể thực hiện kịp thời?

## Slide 04

Nhìn vào ba cảnh này, chúng ta thấy vì sao việc gom nhóm báo cáo lại quan trọng. Ở cảnh bên trái, ba tin nhắn cùng mô tả một ngôi nhà. Nếu không gom chúng lại, ta có thể cử ba thuyền đến cùng một gia đình, gây lãng phí nguồn lực. Ở cảnh giữa, hai ngôi nhà ở gần nhau nhưng là hai sự cố riêng biệt. Nếu gộp nhầm thành một nhóm, ta có thể bỏ sót hoàn toàn một gia đình. Ở cảnh bên phải, nhiều báo cáo giả cùng chỉ về một vùng nước trống. Nhiều tin nói giống nhau không biến nó thành sự cố thật. Những lỗi gom nhóm này làm sai lệch bản đồ điểm đến ngay trước khi ta xếp hạng hay lập lộ trình. Vì kết quả tốt ở một bước không đảm bảo kế hoạch cứu hộ cuối cùng tốt, chúng tôi phải kiểm tra cả ba bước.

## Slide 05

Nghiên cứu của chúng tôi kết nối ba hướng tiếp cận. Thứ nhất, cảm biến khủng hoảng trích xuất thông tin lũ lụt từ mạng xã hội và hình ảnh, nhưng không cho biết mỗi tin nhắn thuộc về sự cố thực tế nào. Thứ hai, các thuật toán phát hiện cộng đồng như Louvain có thể gom các báo cáo giống nhau, nhưng một cụm báo cáo chưa chắc là một điểm cứu hộ thật. Thứ ba, hậu cần nhân đạo lập lộ trình cho thuyền và cân bằng giữa công bằng và tốc độ, nhưng lại giả định danh sách điểm đến đầu vào đã chuẩn xác. Khoảng trống ở đây rất rõ: kế hoạch cứu hộ sẽ ra sao khi bước gom nhóm và chấm điểm phía trước mắc lỗi? Chúng tôi trả lời qua ba câu hỏi: RQ1 kiểm tra gom nhóm, RQ2 kiểm tra xếp hạng ưu tiên, và RQ3 kiểm tra điều phối cứu hộ.

## Slide 06

Để kiểm tra lỗi một cách rõ ràng, chúng tôi cần biết trước đáp án chuẩn, vì vậy chúng tôi tạo bộ dữ liệu mô phỏng có kiểm soát qua bốn bước. Bước một là dựng bối cảnh. Với bài kiểm tra gom nhóm, chúng tôi dùng dữ liệu bản đồ thực tế ở miền Trung Việt Nam từ bản đồ ngập Copernicus, OpenStreetMap và dân số WorldPop. Với xếp hạng và điều phối, chúng tôi dùng vùng mô phỏng hoàn toàn. Bước hai, mô phỏng mười sáu sự cố ẩn trong mỗi lần chạy. Bước ba, sinh ra các báo cáo từ các sự cố đó, gồm vị trí GPS, thời gian, mức ngập, độ khẩn cấp và số người. Bước bốn, thêm nhiễu có kiểm soát: bản sao y hệt, bản sao gần giống, báo cáo giả ngẫu nhiên và chiến dịch báo cáo giả có tổ chức. Dùng bản đồ thật giúp vị trí hợp lý, còn sự cố mô phỏng cho ta đáp án chính xác để tìm ra chỗ thuật toán thất bại. Tuy nhiên, bản thân các báo cáo là mô phỏng, nên vẫn cần kiểm chứng trên báo cáo thực được gán nhãn độc lập.

## Slide 07

Sơ đồ này thể hiện nguyên tắc quan trọng nhất của nghiên cứu: ranh giới thông tin. Phía trên đường nét đứt màu cam là những gì thuật toán được phép thấy. Nó chỉ đọc các trường trên báo cáo như vị trí, thời gian, mức ngập, độ khẩn cấp, số người và mức độ dễ tổn thương. Chỉ dùng thông tin này, nó gom nhóm, tính điểm ưu tiên và lập lịch cho thuyền. Nếu báo cáo thiếu vị trí hoặc thời gian, nó sẽ được chuyển sang duyệt thủ công. Phía dưới đường cam là đáp án ẩn, gồm mã sự cố thật, nhãn tin giả, hạn chót và giá trị tổn hại. Chúng tôi khóa toàn bộ kết quả dự đoán trước, và chỉ mở đáp án ở bước cuối cùng để chấm điểm. Có tất cả tám mươi lần chạy: hai mươi để phát triển, hai mươi để tinh chỉnh tham số, và bốn mươi lần giữ riêng để kiểm tra cuối cùng. Mọi kết quả hôm nay đều lấy từ bốn mươi lần chạy kiểm tra này.

## Slide 08

Bây giờ hãy xem cách chúng tôi gom nhóm báo cáo ở RQ1. Với mỗi cặp báo cáo, chúng tôi tính ba độ tương đồng từ không đến một: khoảng cách địa lý G, chênh lệch thời gian T, và bằng chứng báo cáo C. Chúng tôi so sánh hai cách kết hợp chúng thành trọng số cạnh. Quy tắc Cộng (Additive) đơn giản là cộng khoảng cách, thời gian và bằng chứng lại. Quy tắc Nhân (Product) lấy khoảng cách G nhân với tổng của thời gian và bằng chứng. Hãy nhìn biểu đồ bên phải cho hai báo cáo có cùng thời gian và bằng chứng. Khi khoảng cách tăng lên ba ki-lô-mét, trọng số Product giảm về không, đóng vai trò như một cổng chặn địa lý. Ngược lại, trọng số Additive vẫn giữ một nửa giá trị tối đa dù hai báo cáo ở rất xa nhau. Tiếp theo, chúng tôi chỉ giữ lại các liên kết mạnh nhất qua ngưỡng cắt và láng giềng gần nhất, rồi chạy Louvain để tìm cụm. Về lý thuyết, Product chặn được liên kết xa, nhưng cần thực nghiệm để xem nó có giúp phân cụm tốt hơn không.

## Slide 09

Sau khi có các nhóm sự cố, chúng ta xếp hạng và lập lịch chuyến đi như thế nào? Trong mỗi nhóm, trước tiên chúng tôi gom các bản sao y hệt và gần giống vào các họ bằng chứng. Mỗi họ chỉ đóng góp một giá trị duy nhất: giá trị lớn nhất nhân với độ tin cậy của báo cáo Q. Sau đó, chúng tôi tính điểm ưu tiên có chặn P. Điểm này kết hợp độ khẩn cấp, mức ngập và số người, rồi nhân với hệ số khuếch đại mức dễ tổn thương. Nhờ vậy điểm ưu tiên luôn nằm trong khoảng từ không đến hai. Vì chỉ lấy giá trị lớn nhất trong mỗi họ bằng chứng, việc thêm một bản sao y hệt vào họ đã có sẽ không làm thay đổi điểm số, miễn là các họ và đầu vào giữ nguyên. Tuy nhiên, quy tắc toán học này chỉ chặn được tin trùng lặp, chứ không biết được báo cáo có nói dối hay không. Cuối cùng, bộ lập lịch lấy các nhóm và điểm ưu tiên này để phân bổ chuyến tàu dựa trên thời gian di chuyển, thời gian cứu hộ và số thuyền hiện có.

## Slide 10

Hãy chuyển sang phần kết quả, bắt đầu với độ chính xác phân cụm trên bốn mươi lần chạy kiểm tra. Chúng tôi đo độ chính xác bằng chỉ số ARI, trong đó bằng một là khớp hoàn toàn. Các phương pháp dựa trên đồ thị rõ ràng tốt nhất, đều đạt khoảng 0,90 đến 0,92, trong khi K-means theo tọa độ đạt 0,82 và các biến thể DBSCAN đều dưới 0,50. So sánh hai quy tắc chính được tinh chỉnh độc lập, Additive Louvain đạt 0,9191 và Product Louvain đạt 0,9072. Sau khi hiệu chỉnh thống kê, giá trị p là 0,2560. Điều này có nghĩa sự khác biệt không có ý nghĩa thống kê, và cổng nhân Product không cho thấy ưu thế về độ chính xác so với phép cộng Additive.

## Slide 11

Tiếp theo, chúng tôi thử thách các phương pháp phân cụm dưới bảy điều kiện nhiễu cố định mà không chỉnh lại tham số. Đúng như dự đoán, thêm nhiễu vị trí GPS hoặc nhiễu thời gian làm giảm độ chính xác của mọi phương pháp. Khi sao chép hai lần, độ chính xác tăng nhẹ. Tuy nhiên, khi thêm năm bản sao y hệt cho mỗi báo cáo, cả bốn phương pháp đồ thị đều sụt giảm mạnh xuống ARI khoảng 0,30. Một giải thích khả dĩ là các bản sao chiếm chỗ trong danh sách láng giềng gần nhất, nhưng giao thức của chúng tôi chưa tách riêng được cơ chế này. Ngoài ra, dù Product Louvain ngăn không cho báo cáo giả lẫn vào sự cố thật, các báo cáo giả lại tự gom với nhau tạo ra điểm đến giả với tỉ lệ 16,49 phần trăm. Điều này nhắc lại cảnh thứ ba ở phần mở đầu: chặn các liên kết xa không ngăn được việc hình thành các cụm giả.

## Slide 12

Ở RQ2, chúng tôi kiểm tra xếp hạng ưu tiên trên các nhóm sự cố chuẩn để lỗi phân cụm không làm ảnh hưởng. Ở biểu đồ bên trái, chúng tôi đo mức độ khớp giữa năm sự cố đứng đầu với lợi ích cứu hộ mô phỏng bằng NDCG@5. Điểm cải tiến của chúng tôi đạt 0,6669, nhỉnh hơn một chút so với điểm cũ là 0,6548, nhưng chênh lệch không có ý nghĩa thống kê. Thực tế, cách xếp theo số người hoặc xếp ngẫu nhiên cũng đạt mức tương tự quanh 0,67. Ở biểu đồ bên phải, chúng tôi kiểm tra độ ổn định của điểm khi báo cáo bị thao túng. Với hai, năm hoặc mười bản sao y hệt, điểm cải tiến không hề bị lệch, đúng như kỳ vọng khi các họ bằng chứng và đầu vào giữ nguyên. Tuy nhiên, khi kẻ xấu thổi phồng số người hoặc tung chiến dịch tin giả có phối hợp, điểm cải tiến lại bị lệch nhiều hơn điểm cũ. Vì vậy, ổn định trước bản sao không đồng nghĩa với xếp hạng tốt hơn hay chống được tin giả có tổ chức.

## Slide 13

Ở RQ3, chúng tôi xem xét kết quả điều phối cứu hộ khi dùng các nhóm dự đoán từ Product. Trong hai biểu đồ này, cột vượt quá số không nghĩa là điểm ưu tiên cải tiến kém hơn đối thủ so sánh. So với điểm ưu tiên cũ, quy tắc cải tiến có mức tổn hại mô phỏng cao hơn khoảng mười bốn đơn vị và giảm tỉ lệ trễ hạn khoảng hai điểm phần trăm; cả hai chênh lệch đều không có ý nghĩa thống kê. Tuy nhiên, so với quy tắc ưu tiên điểm gần nhất (nearest-first), điểm cải tiến gây tổn hại cao hơn gần bảy mươi đơn vị và tỉ lệ trễ hạn cao hơn mười tám điểm phần trăm, một khoảng cách rất đáng kể. Một giải thích khả dĩ là xếp hạng chỉ theo nhu cầu chưa tính đủ thời gian di chuyển của thuyền, nhưng thực nghiệm chưa tách riêng được cơ chế này. Hơn nữa, dùng nhóm của Product gây tổn hại nhiều hơn mười tám đơn vị so với nhóm Additive cùng mật độ. Điều này cho thấy lỗi gom nhóm ở bước đầu thực sự lan đến lịch cứu hộ ở bước cuối. Lưu ý, tổn hại ở đây là chi phí mô phỏng, không phải thương vong thật, và nearest-first không được khuyến nghị làm chính sách thực địa.

## Slide 14

Để kết luận, bài học chính của chúng tôi là các đảm bảo toán học cục bộ không tự động tạo ra quyết định cứu hộ tốt hơn. Ở bước gom nhóm, cổng không gian giới hạn được khoảng cách liên kết, nhưng không thắng được phép cộng và vẫn sụp đổ khi gặp bản sao gấp năm lần. Ở bước xếp hạng, tính bất biến giúp chặn các bản sao đơn giản, nhưng không giúp khớp lợi ích tốt hơn hay chặn được tấn công có tổ chức. Và ở bước điều phối, điểm nhu cầu có chặn không thắng được chiến lược đi điểm gần nhất. Đóng góp chính của chúng tôi là một quy trình đánh giá minh bạch, giấu đáp án và bộ mã nguồn mở công khai. Trước khi áp dụng thực tế, các nghiên cứu tới cần thử nghiệm trên báo cáo thiên tai thật, xác thực nguồn tin, và kết hợp trực tiếp điểm ưu tiên với giới hạn thời gian di chuyển.

## Slide 15

Đây là các tài liệu tham khảo chính cho phương pháp phân cụm, xếp hạng và đánh giá của chúng tôi.

## Slide 16

Và đây là tài liệu tham khảo cho các bộ dữ liệu khủng hoảng, nguồn bản đồ địa lý, cùng bản phát hành GitHub công khai của nhóm.

## Slide 17

Xin cảm ơn quý thầy cô và các bạn đã chú ý lắng nghe. Tôi rất sẵn lòng nhận các câu hỏi thảo luận.

## Slide 18 (Backup)

Slide dự phòng này tóm tắt giao thức thực nghiệm của chúng tôi. Thứ nhất, chúng tôi dùng hai gói dữ liệu riêng: Generator 3.0 gắn với bản đồ miền Trung Việt Nam cho phân cụm RQ1, và Candidate 4.1 với hình học tổng hợp cho xếp hạng RQ2 và điều phối RQ3. Thứ hai, để tuân thủ ranh giới thông tin, RQ2 kiểm tra xếp hạng trên nhóm chuẩn (oracle), còn RQ3 lập lịch tàu trên các cụm dự đoán mà không nhìn thấy đáp án. Thứ ba, về thống kê điều phối, chúng tôi lấy trung bình ba kịch bản nguồn lực thuyền trong mỗi seed để tạo ra bốn mươi cặp kiểm tra độc lập. Cuối cùng, tính bất biến với bản sao y hệt chỉ đúng khi các họ bằng chứng và trường đầu vào được giữ cố định.

## Slide 19 (Backup)

Slide này giải đáp bốn câu hỏi thường gặp. Thứ nhất, ở RQ1, khoảng tin cậy bootstrap chưa hiệu chỉnh giữa Product và Additive không chứa số không, nhưng giá trị p của kiểm định Wilcoxon sau hiệu chỉnh Holm là 0,2560. Vì hai thủ tục thống kê khác nhau và có hiệu chỉnh đa so sánh, chúng tôi không tuyên bố phương pháp nào thắng. Thứ hai, chuyển từ Louvain sang Leiden cho ARI đạt 0,9165, không khác biệt có ý nghĩa thống kê so với Product Louvain. Thứ ba, chúng tôi đã thử nghiệm thay đổi từng tham số một qua hai mươi mốt cấu hình trong công thức tính điểm, và NDCG@5 trung bình thay đổi dưới 0,01, cho thấy tính ổn định cục bộ của tham số. Thứ tư, chúng tôi dùng dữ liệu tổng hợp vì luồng tin lũ lụt thực tế không có sẵn đáp án sự cố chuẩn hay mức độ trùng lặp có kiểm soát để chẩn đoán lỗi hệ thống.
