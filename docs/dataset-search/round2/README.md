# Khảo sát mở rộng trước khi chọn dữ liệu RQ1–RQ2

Ngày kiểm tra: **29/10/2026**. Đợt này trả lời yêu cầu tìm phương án tốt hơn **IDRISI-D cho RQ1** và **TREC-IS cho RQ2**. Kết luận dưới đây là đề xuất chọn dữ liệu có điều kiện, chưa phải quyết định thay bộ thực nghiệm của bài báo.

**Kết quả chính:** có nguồn sát bài toán cứu hộ hơn IDRISI-D, nổi bật là **KeralaRescue**, nhưng chưa xác minh lấy được bản ghi lịch sử để dùng. Trong các nguồn đã kiểm tra, **chưa có bộ sẵn sàng thay trực tiếp toàn bộ RQ1 hoặc RQ2**. TREC-IS vẫn có lợi thế cho đánh giá thứ hạng *ưu tiên thông tin do người gán*, không cung cấp gold lợi ích cứu hộ. Vì thế, không nên chốt cặp dữ liệu chỉ theo tên corpus hoặc số hàng.

Đã có bước tiếp theo sau khi người dùng tải PDF xuất bản: [xác minh bản gốc và chuẩn bị pilot KeralaRescue](../kerala-rescue/README.md). Hồ sơ mới ghi chi tiết tình trạng Slack/tên miền hiện tại, thư xin dữ liệu và các điều kiện cần trước khi chạy RQ; chưa có dữ liệu cấp yêu cầu.

## 1. Phạm vi và bằng chứng

- Thực hiện thêm **41 truy vấn**, lưu trong [search-log.json](search-log.json), ngoài 40 truy vấn của [đợt đầu](../search-log.json). Đây là tìm kiếm có ghi vết, không phải một systematic review có độ bao phủ đầy đủ.
- So sánh **12 đầu mối** trong [candidates.csv](candidates.csv), gồm nguồn mới và việc kiểm tra lại khả dụng của CrisisTS đã có ở đợt đầu. Không cộng các bài trong cùng họ dữ liệu thành những tập xác nhận độc lập.
- Tải và kiểm tra **7 tệp dữ liệu của 5 nguồn**: Ushahidi Haiti, QuaTRED, French Ecological Crisis, MASH và Actionable Requests/Offers. Đối chiếu toàn bộ cấu trúc và thống kê; xuất **500 hàng cờ hiện diện**, 100 hàng cách đều mỗi nguồn. Đây không phải 500 bản ghi được người đọc xác nhận nhãn.
- Lưu URL, trạng thái HTTP và SHA-256 trong [sources.json](sources.json). Sáu tệp từ GitHub/Hugging Face được ghim revision và tải lại tại revision đó để kiểm tra đúng mã băm. Lưu biên nhận bài báo/tài liệu và lỗi truy cập trong [source-access.json](source-access.json).

Các nhãn cùng sự cố, ưu tiên do người gán mới và kết quả RQ mới đều **chưa được tạo**. Tệp thô nằm ngoài kho mã; hồ sơ này chỉ xuất schema, thống kê và cờ hiện diện.

## 2. RQ1: nguồn nào tốt hơn IDRISI-D?

RQ1 cần phân biệt nhiều báo cáo về **cùng một sự cố cứu hộ cụ thể** với những sự cố ở gần nhau. Tọa độ, thời gian và nhãn loại sự kiện chỉ hỗ trợ đầu vào, chưa tạo ra gold này. Một ID bản ghi, một cặp tweet giống nhau hoặc một nhãn “người mắc kẹt” không tự là nhãn nhóm sự cố.

| Nguồn | Lợi thế so với IDRISI-D | Hạn chế quyết định | Đề xuất |
|---|---|---|---|
| **KeralaRescue, lũ 2018** | Đầu vào là yêu cầu dịch vụ thực, có yêu cầu cứu hộ, mô tả nhu cầu và thông tin vị trí; sát đơn vị bài toán hơn tập tweet địa danh tổng quát | Chưa lấy được snapshot lịch sử; bài đã loại hơn 5.000 bản ghi trùng theo heuristic; chưa có gold nhóm sự cố độc lập | **Ưu tiên kiểm tra khả năng tiếp cận**, có thể đứng trước IDRISI-D nếu vượt các điều kiện bên dưới |
| **Ushahidi Haiti, động đất 2010** | Tệp đã lấy có 3.593 báo cáo, nội dung–thời gian–tọa độ cùng hàng; 167 báo cáo có chủ đề người mắc kẹt | Khác miền lũ; tọa độ không có độ chính xác; dữ liệu là bản xuất bản đồ; thiếu gold nhóm và lịch sử tin gốc | Pilot bổ trợ về liên kết báo cáo, có điều kiện nguồn/giấy phép; **chưa thay bộ chính về lũ** |
| **QuaTRED** | Quan hệ trong câu liên kết địa điểm với tác động, hữu ích tránh nhầm nơi được nhắc tới với nơi bị ảnh hưởng | Không có tọa độ đã phân giải, thời gian, gold liên kết xuyên báo cáo; chưa thấy giấy phép dữ liệu trong phần kho đã kiểm tra | Bổ trợ trích xuất trường, không phải benchmark RQ1 sẵn dùng |
| **NARMADA / needs–availability** | Nhu cầu tài nguyên, địa điểm, số lượng và liên kết nhu cầu–nguồn cung sát hoạt động hỗ trợ | Ghép nhu cầu với nguồn cung khác với gom cùng sự cố; dữ liệu nghiên cứu đã khử trùng; chưa xác minh được tệp nghiên cứu qua kho đã kiểm tra | Bổ trợ trích xuất/điều phối nhu cầu; không thay gold RQ1 |
| **DisTGranD** | Có nhãn event/sub-event và trigger/argument chi tiết | Mô tả nguồn nói rõ phân loại **loại** event/sub-event, chưa chứng minh nhãn đồng nhất **cá thể** sự cố; chưa audit bản phát hành | Không xem tên “sub-event” là bằng chứng đủ để tính ARI sự cố cứu hộ |
| **Event2012** | Có đầu mối về corpus event detection tổng quát | Khác đơn vị và miền cứu hộ; chưa kiểm tra được bản phát hành/đầu vào đủ cho thuật toán hiện tại trong đợt này | Chỉ là đối chứng phương pháp tiềm năng, không ưu tiên thay dữ liệu cứu hộ |

### KeralaRescue: ứng viên đáng theo đuổi nhất về đúng bài toán

[Young et al. (2022), §2.3](https://doi.org/10.1016/j.ijdrr.2022.102908) mô tả nền tảng yêu cầu cứu hộ và hỗ trợ nhu yếu phẩm, dữ liệu JSON có 27 cột, được nhóm tác giả lấy với sự cho phép của nhà phát triển. Bài có xử lý độ chính xác tọa độ và loại trùng. Mục Data availability dẫn nguồn Slack, không cung cấp một archive nghiên cứu có phiên bản và giấy phép tải được đã xác minh ở đây.

Kiểm tra thêm [mã hệ thống](https://github.com/raksha-life/rescuekerala/blob/master/mainapp/models/models.py) cho thấy `Request` có `needrescue`, `detailrescue`, `latlng`, `latlng_accuracy`, `dateadded` và cờ `is_request_for_others`. Điểm cuối đặc biệt quan trọng: tọa độ của người gửi hộ không tự là vị trí người cần cứu. Mã cũng có `RequestUpdate`, các mức high/medium/low và thời gian cập nhật. **Đây chỉ là bằng chứng schema của mã đã kiểm tra**, chưa xác nhận các trường tồn tại, đầy đủ hoặc được gán bởi ai trong snapshot năm 2018. Không suy ra đã có gold ưu tiên vận hành.

KeralaRescue sẽ được đưa lên trước IDRISI-D khi lấy được dữ liệu hợp lệ và xác nhận: còn nội dung trước khử trùng; có thời gian từng yêu cầu; xác định vị trí cần cứu và sai số; có đủ yêu cầu cứu hộ trong các cửa sổ trọn vẹn; cho phép tạo nhãn sự cố từ chứng cứ nguồn. Không lấy quy tắc trùng theo số điện thoại/khoảng một giờ của bài gốc làm gold cho thuật toán cần đánh giá. Một người có thể gửi nhiều nhu cầu hoặc nhiều người gửi cho cùng hộ.

### Ushahidi Haiti: đủ để kiểm tra tính khả thi, chưa đủ để thay RQ1 chính

Các số sau tính từ [bản xuất đang lưu trong kho của sách Python for Data Analysis](https://github.com/wesm/pydata-book/blob/2nd-edition/datasets/haiti/Haiti.csv), không mặc định là toàn bộ tin nhắn đầu vào của nền tảng:

| Kiểm tra | Kết quả |
|---|---:|
| Bản ghi / ID khác nhau | 3.593 / 3.593 |
| Có mô tả, thời gian đọc được và cặp tọa độ hợp lệ về số học | 3.593 |
| Cặp tọa độ khác nhau | 2.781 |
| Số bản ghi cùng chia sẻ cặp tọa độ phổ biến nhất | 140 |
| Hàng dư do mô tả trùng nguyên văn sau bỏ khoảng trắng đầu/cuối | 57 |
| Chủ đề `1c. People trapped` | 167 |
| Tọa độ khác nhau trong 167 báo cáo này | 113 |
| `VERIFIED=YES` trong 167 báo cáo này | 4 |

`APPROVED` và `VERIFIED` không phải mức ưu tiên hay nhãn nhóm. Các điểm trùng có thể do địa danh chung hoặc cách định vị; không suy ra cùng sự cố. Chuỗi ngày trải từ 12/01 đến 05/07/2010 và không ghi múi giờ. Một báo cáo trên bản đồ cũng có thể đã tổng hợp nhiều tin nguồn, nên 57 mô tả lặp không đo được đầy đủ trùng lặp khi truyền tin.

[Dillingham et al. (2013)](https://openaccess.city.ac.uk/id/eprint/2123/) nghiên cứu chính sự đa dạng về độ hạt địa điểm trong Haiti Crisis Map; đây là cơ sở để yêu cầu thẩm định vị trí thay vì tin mọi tọa độ. [Catalog cũ](https://old.datahub.io/@india/ushahidi/) ghi CC BY-SA nhưng không rõ phiên bản; đường tải Haiti gốc trả **404**. Bản mirror tải được không đủ để xác nhận tính toàn vẹn với bản gốc hoặc áp giấy phép mã của sách cho dữ liệu. Cần đối chiếu nguồn và điều kiện tái sử dụng trước khi phát hành tập dẫn xuất.

Với phương pháp bài báo hiện tại, thiếu `F` được giữ là thiếu, không gán bằng 0 cho mọi báo cáo động đất; nếu chỉ gán thêm `E`, đây là nhánh thiếu một trường của kernel. Kết quả đó phải báo riêng so với thí nghiệm lũ đủ `F/E`. Tập này có thể kiểm tra cơ chế liên kết báo cáo ngoài miền; không chứng minh hiệu quả cứu hộ lũ.

## 3. RQ2: nguồn nào tốt hơn TREC-IS?

Cần tách ba mục tiêu: **ưu tiên thông tin**, **tính khẩn cấp/khả năng hành động**, và **lợi ích cứu hộ khi xếp lịch**. Đổi giữa ba mục tiêu không chỉ là đổi tên cột nhãn.

| Nguồn | Điểm hấp dẫn | Bằng chứng khả dụng và ý nghĩa nhãn | So với TREC-IS |
|---|---|---|---|
| **French Ecological Crisis / Digging Communicative Intentions** | Người gán khẩn cấp, có lũ/bão, thảo luận rõ actionability | Bản CSV đã lấy: 12.826 hàng; 2.147 Urgent, 1.442 NotUrgent, 9.237 NotUseful; chỉ ID và metadata | Đáng làm phép xác nhận bổ sung nếu khôi phục được nội dung; không thay được thứ hạng nhiều mức và benefit |
| **Kejriwal & Zhou 2020 — Nepal/Kerala urgency** | Khái niệm nhu cầu cần xử lý nhanh sát cứu hộ hơn chủ đề humanitarian chung | Bài nói dữ liệu không thể công khai vì riêng tư; mẫu gán bằng active learning, nhãn nhị phân | Sát nghĩa nhưng chưa khả dụng để tái lập; không là phương án thay ngay |
| **MASH, phiên bản v2** | Bão Helene/Milton 2024, nhiều nền tảng; nhãn Request và information integrity | 59.607 ID+nhãn từ ba nền tảng; không có nội dung, tọa độ, thời gian; nhãn người–MLLM phối hợp | Bổ trợ miền/độ tin cậy nguồn; thiếu gold ưu tiên, không có lợi thế trực tiếp cho RQ2 |
| **Actionable Requests and Offers** | Phân loại nhu cầu/đề nghị cụ thể, có `alpha` và actionability | `real_data.json` chỉ 307 hàng; 1.346 hàng tự sinh ở tệp khác bị loại; provenance người gán và đơn vị điểm chưa đủ | Không gọi `alpha` là ưu tiên cứu hộ; phù hợp khảo sát taxonomy hơn benchmark ưu tiên chính |
| **KeralaRescue updates** | Schema có mức high/medium/low gắn yêu cầu và thời gian cập nhật | Chưa có bản ghi để kiểm tra người gán, thời điểm, thay đổi trạng thái hoặc mức bao phủ | Phương án có thể vượt TREC về đúng đơn vị, **nếu** dữ liệu và nhãn lịch sử được xác nhận |
| **CrisisTS** | Kết hợp văn bản với khí tượng | Kiểm tra lại kho: phần French textual data vẫn ghi “will be released soon”; nhánh Anh dùng nhãn chuyển từ chủ đề | Chưa khắc phục được thiếu nhãn ưu tiên độc lập; không phải corpus xác nhận độc lập với IDRISI/HumAID |
| **ResQConnect 2026** | Hệ thống phân phối nguồn lực trong lũ, có liên kết dataset | Bài thừa nhận đánh giá trong tình huống synthetic có kiểm soát; trang dữ liệu không mở được qua công cụ trong lần kiểm tra | Không dùng kết quả hệ thống như bằng chứng đã có nhật ký cứu hộ thực độc lập |

### Bộ tiếng Pháp: gần hơn về khẩn cấp nhưng có hai điều kiện lớn

[Kozlowski et al. (2020)](https://doi.org/10.1016/j.ipm.2020.102284) và [Benamara et al. (2024), §4](https://aclanthology.org/2024.dnd-15.6/) cho thấy đây là họ dữ liệu được mở rộng theo thời gian. Bài 2024 có 19.595 tweet đầu vào, sau đó chọn tập con gán speech acts; **không đồng nhất các quy mô này** với 12.826 hàng CSV công khai đã kiểm tra. CSV có 12.824 ID khác nhau và không chứa văn bản. `period` chỉ là Before/During/After/NA, không là timestamp.

Urgent bao gồm thiệt hại người/hạ tầng và hướng dẫn an toàn; đó chưa nhất thiết là một người đang yêu cầu cứu hộ. Ba nhãn có cả NotUseful nên chỉ còn **hai mức khẩn cấp trên tin liên quan**. Có **2 nhóm ID lặp**, cả hai khác nhãn sự kiện và **1 nhóm khác nhãn urgency**; cần đối chiếu ngữ cảnh/sự kiện, không tùy ý chọn một nhãn hay để cùng ID lọt qua train/test. Nếu dùng, đánh giá phát hiện/ưu tiên tin khẩn cấp riêng; không ép chúng thành Low/Medium/High/Critical. Việc kiểm tra tiếng Pháp cũng cần người hiểu ngôn ngữ; dịch tự động là bước suy ra phải được ghi và kiểm tra riêng.

Mối liên hệ với CrisisTS cần được kiểm tra bằng ID khi có các phiên bản tương ứng; không cộng các bài 2020/2024/2025 thành ba nguồn xác nhận độc lập. Điều khoản [kho gốc](https://github.com/DiegoKoz/french_ecological_crisis) là CC BY-NC-SA 4.0 và yêu cầu tuân thủ điều khoản nền tảng.

Kiểm tra ID xuyên corpus trên đúng snapshot đã tải: QuaTRED có **1 ID chung với TREC-IS**, không thấy ID chung với HumAID set1 hoặc IDRISI-D Harvey train; bộ tiếng Pháp không thấy ID chung với ba phần này. [Biên nhận và phạm vi](audit/cross-corpus-overlap.json) ghi mã băm của từng tệp. Không thấy ID chung trong các phần đã tải chưa chứng minh toàn bộ phiên bản độc lập; không kiểm tra bằng ID được những nguồn không phát hành ID nền tảng hoặc chưa lấy được nội dung.

### Vì sao các nguồn mới chưa vượt TREC-IS cho vai trò hiện tại?

[TREC-IS](https://www.dcs.gla.ac.uk/~richardm/TREC_IS/2021/) có các mức ưu tiên thông tin do người đánh giá và phần văn bản lấy được đã được thống kê ở đợt đầu. Nguồn mới hoặc thiếu nội dung, hoặc chỉ có nhãn nhị phân/chủ đề, hoặc không công khai dữ liệu, hoặc không đủ provenance nhãn. Lợi thế này chỉ áp dụng cho **đánh giá bổ trợ ưu tiên thông tin ở mức báo cáo**.

RQ2 chính trong bài hỏi tương quan với benefit độc lập ở mức sự cố dưới nhiễu báo cáo. Không nguồn mới nào trong đợt này đã cung cấp đầy đủ gold cùng sự cố, `E/F/N/V/Q`, nhãn/benefit cùng đơn vị và phép kiểm soát trùng lặp. Không lấy `VERIFIED` hoặc information integrity làm `Q` của công thức hiện tại; không đưa nhãn urgency tham chiếu vào `E` rồi chấm chính nhãn đó. Cũng không lấy max priority của các báo cáo để tự tạo gold cụm rồi gọi đó là nhãn độc lập ở mức sự cố.

## 4. Khuyến nghị sau tìm kiếm mở rộng

1. **RQ1: chưa chốt IDRISI-D làm tập chính.** Xếp KeralaRescue và các nguồn Harvey chuyên cứu hộ ở đợt đầu vào nhóm ưu tiên tiếp cận vì đúng bài toán hơn. IDRISI-D vẫn là nguồn đã tải được để kiểm tra chuẩn hóa vị trí/thời gian; nhãn địa danh và tọa độ cấp thành phố không đủ để cam kết pilot liên kết sự cố thành công.
2. **Dự phòng RQ1:** Ushahidi Haiti cho pilot kiểm chứng quy trình gán nhãn/liên kết ngoài miền, sau đối chiếu nguồn/điều khoản và kiểm tra độ hạt vị trí. Nếu không tìm được các cặp cùng sự cố có chứng cứ hoặc vị trí quá thô, báo là không đạt; không tạo gold bằng ngưỡng khoảng cách.
3. **RQ2: giữ TREC-IS trong danh sách ưu tiên cho bằng chứng bổ trợ**, kèm French Ecological Crisis nếu khôi phục được nội dung. Chưa chọn bộ thay trực tiếp thí nghiệm benefit; KeralaRescue updates chỉ được xét lại khi có dữ liệu thật và hiểu quy trình gán nhãn.
4. **QuaTRED và Requests/Offers chỉ bổ trợ thiết kế trích xuất trường/taxonomy.** MASH đáng lưu như nguồn kiểm tra khác nền tảng, chưa đáng ưu tiên chi phí khôi phục nội dung cho hai RQ hiện tại.
5. **RQ3 chưa đổi kết luận:** tiếp tục cần điều phối mô phỏng trên yêu cầu thực nếu không có nhật ký vận hành đủ chi tiết. Nhãn priority hay trạng thái supplied không chứng minh tác động của chính sách thay thế.

Ưu tiên này xét đúng đơn vị/nhãn trước số hàng. Một bộ nhỏ có yêu cầu cứu hộ và nhãn độc lập có thể hữu ích hơn hàng chục nghìn bài đăng thiếu nội dung hoặc chỉ có chủ đề.

## 5. Các bước tiếp theo và điều kiện để chạy lại bài báo

| Bước | Việc cần làm | Bằng chứng phải có để đi tiếp |
|---|---|---|
| 1. Tiếp cận nguồn sát bài toán | Chuẩn bị yêu cầu dữ liệu lịch sử đã ẩn danh của KeralaRescue/Harvey; hỏi bản trước khử trùng, schema, quyền dùng và updates nếu có | Có tệp hoặc xác nhận khả dụng và điều khoản cụ thể. Đợt này **chưa gửi liên hệ** hoặc đăng ký bằng danh tính của nhóm |
| 2. Pilot đủ ngữ cảnh | Chọn 100–200 báo cáo trong cửa sổ địa bàn/thời gian trọn vẹn, giữ cả tin ngoài nhu cầu và bản lặp; kiểm tra ngôn ngữ/độ hạt địa điểm | Xác nhận có đủ báo cáo cứu hộ, các cặp cùng/khác sự cố có chứng cứ; báo cáo coverage và missingness. Không chỉ chọn các cặp dễ hoặc tự giả định sẽ đủ cụm |
| 3. Gold độc lập | Hai người gán riêng: cùng/khác/không đủ chứng cứ; thẩm định vị trí cần cứu. Nếu thêm ưu tiên, gán trên đơn vị sự cố đã khóa và nêu đúng người gán | Hướng dẫn, đồng thuận, xử lý bất đồng, nguồn chứng cứ và bộ gold versioned; không dùng đầu ra thuật toán để tạo nhãn |
| 4. Chốt protocol và split | Khóa event/block test, giữ họ bản sao cùng tập; tách gold khỏi đầu vào; Product/Additive có ngân sách tuning ngang nhau | Chứng minh test chưa được dùng để chọn tham số, công bố phần nào là dữ liệu quan sát/nhãn mới/suy ra/mô phỏng |
| 5. Tích hợp riêng | Khôi phục mã benchmark từ commit đã ghim trong [protocol](../evaluation-protocol.md); thêm adapter và bộ manifest mới, không ghi đè artifact camera-ready | Kiểm tra parser, đơn vị, timezone, provenance, fail-closed/missingness và tính bất biến với bản sao theo thiết lập cho phép |
| 6. Chạy theo tầng bằng chứng | RQ1: ARI và lỗi tách/gộp, coverage. RQ2 bổ trợ: nhãn ưu tiên cùng đơn vị; chỉ chạy công thức đầy đủ trên phần đủ trường. RQ2 benefit/RQ3: giữ rõ phần mô phỏng và mô hình nguồn lực | Báo cáo chênh lệch ghép cặp và CI theo event/block; ít event thì phân tích tình huống. Không xem mỗi tweet là một lần thử độc lập |
| 7. Cập nhật bài sau kết quả | Thêm mục dữ liệu thực, provenance nhãn, protocol, kết quả và giới hạn; giữ riêng kết quả stress test tổng hợp | Artifact chạy mới tái lập được. Chưa sửa claim trong `paper/main.tex` chỉ vì tìm được corpus |

Trước khi triển khai, dùng [yêu cầu theo RQ](../rq-requirements.md), [protocol](../evaluation-protocol.md) và [hướng dẫn gán nhãn](../annotation-guide.md) đã có. Thêm dữ liệu không đồng nghĩa mọi RQ đã có đánh giá thực địa.

## 6. Tái lập kiểm tra dữ liệu

Từ thư mục gốc repository:

```bash
python3 docs/dataset-search/round2/audit_sources.py
python3 docs/dataset-search/round2/audit_sources.py \
  --cache /tmp/nckh2-round2-reproduce --download \
  --output /tmp/nckh2-round2-reproduce-audit
python3 docs/dataset-search/round2/validate_dossier.py
python3 docs/dataset-search/round2/audit_overlap.py
python3 docs/dataset-search/scripts/validate_dossier.py
```

Lệnh đầu dùng cache đã tải; lệnh thứ hai lấy đúng snapshot công khai trong manifest và dừng khi mã băm khác. Kiểm tra overlap cần thêm cache của đợt đầu. Raw vẫn nằm ngoài kho. Kết quả: [profiles.json](audit/profiles.json), [sample-presence.csv](audit/sample-presence.csv) và [validation.json](audit/validation.json). Đã tải lại đủ 7 tệp vào cache riêng và đối chiếu đầu ra trùng từng byte trong [reproduction.json](audit/reproduction.json). Mã băm giúp xác định phiên bản tệp, không xác nhận độ đúng ngữ nghĩa, nhãn hoặc quyền tái sử dụng.
