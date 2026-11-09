# Kế hoạch hoàn thiện nội dung báo cáo theo nhận xét 02–15

Ngày lập: **08/11/2026**, Asia/Taipei. Trạng thái: **kế hoạch biên soạn, chưa thực thi**.

## 1. Mục tiêu và phạm vi

Theo yêu cầu mới của người dùng, hoàn thiện phần trình bày trong báo cáo cho **14 nhận xét mang số 02 đến 15 của bản tổng hợp nhận xét ban đầu**. Tập này bao gồm cả 03, 04, 07 và 12 đã có nội dung đáp ứng; các mục đó được giữ và rà lại, không làm lại nghiên cứu. Không mở rộng sang nhận xét 01 hoặc 16–20.

**Không yêu cầu thí nghiệm hoặc bằng chứng thực địa mới để hoàn thành đợt biên soạn.** Dùng kết quả đã lưu cho phần kết quả; với nội dung còn thiếu, bổ sung đủ thiết kế, cơ sở lựa chọn, quy trình và kế hoạch đánh giá. Mỗi phần phải nêu ngay nó là kết quả đã có hay phương án đề xuất.

Điều kiện hoàn thành của kế hoạch này là **đủ nội dung phản hồi trong báo cáo**, không phải xác nhận đã hoàn thành mọi cam kết thực nghiệm hoặc Hội đồng đã chấp thuận. Việc bổ sung mục NLP, fusion hoặc đánh giá trên điện thoại không tự tạo ra mô hình đã triển khai, số đo mới hoặc xác nhận chuyên môn.

Đợt lập kế hoạch chỉ thêm tài liệu này và liên kết từ README. Việc sửa LaTeX, dựng PDF và cập nhật bảng đối chiếu thuộc đợt thực hiện kế hoạch sau đó.

## 2. Điểm xuất phát và nguồn dùng để biên soạn

Ưu tiên nguồn báo cáo hiện tại và kết quả của đợt bổ sung mới hơn các bảng trạng thái lịch sử:

- [Bản báo cáo hiện tại](../../report/main.pdf): **175 trang** tại thời điểm lập kế hoạch. Dòng cuối biểu mẫu tiếng Anh đã nằm trong trang PDF 20. Trang PDF 17 còn chỉ có khối ký chủ nhiệm.
- [Nguồn nhận xét đã tổng hợp](evidence/user-request.txt) và [ma trận nhận xét](01-review-matrix.md): dùng để đối chiếu nội dung; không xem phần diễn giải là lời nói nguyên văn của Hội đồng.
- [Pilot đa phương thức](outputs/multimodal-20261108/analysis.md) và [trạng thái phần còn thiếu](outputs/multimodal-20261108/review-status.csv): đã có text, ảnh và fusion trên CrisisMMD; chưa có đánh giá cứu hộ tiếng Việt hoặc tích hợp fusion vào ứng dụng.
- [Đợt bổ sung CPU và rà hồ sơ](outputs/followup-20261108/README.md): đã có clean + tám biến đổi ảnh trên CPU; còn khoảng trống nguồn ảnh và tám sai lệch thống kê RQ2.
- [Quy tắc báo cáo](../../report/RULES.md): giữ cỡ chữ, lề, cấu hình biểu mẫu và đánh số tự động.

Các chỉnh sửa gần nhất cần bảo toàn:

1. Ảnh chủ nhiệm đã được chèn qua `report/template/forms.tex`; trạng thái hoãn ảnh trong tài liệu cũ chỉ còn là lịch sử.
2. Hai đoạn cuối biểu mẫu tiếng Anh đã rút gọn; không làm xuất hiện lại trang chỉ có một dòng.
3. Mười hai trang thuyết minh được chèn riêng từng trang ở mức phóng **105%**, tương ứng trang in 133–144 tại snapshot này; giữ cách chèn trong `report/main.tex`.
4. Baseline hiện có 48 hình và 41 bảng. Khi thêm nội dung, lấy số lượng mới từ nguồn và kiểm tra tự động, không khóa các số này bằng tay.

## 3. Quy ước trình bày nội dung mới

| Loại nội dung | Cách đặt tiêu đề và diễn đạt | Nội dung được đưa vào |
|---|---|---|
| Đã thực hiện | “Phương pháp hiện có”, “Kết quả đã ghi nhận”; mô tả đúng phạm vi dữ liệu và môi trường | Số liệu, mô hình, phép thử đã có trong repo |
| Thiết kế đề xuất | “Thiết kế đề xuất”, “Phương án mở rộng”; dùng “đề xuất”, “dự kiến”, “cần” | Kiến trúc, đầu vào/đầu ra, công thức, giả mã, sơ đồ và ví dụ giải thích |
| Kế hoạch đánh giá | “Thiết kế đánh giá bổ sung — chưa thực hiện” | Cấu hình so sánh, cách chọn mẫu, nhãn dự kiến, chỉ số và biểu mẫu ghi kết quả |

Ví dụ tự soạn chỉ dùng để giải thích quy trình và phải ghi **“ví dụ minh họa, không phải mẫu thực nghiệm”**. Bảng kế hoạch không điền Accuracy/F1/p-value dự đoán; dùng “Chưa đo” khi cần trường kết quả. Không bổ sung URL nguồn ảnh, giấy phép, độ đồng thuận, xác nhận chuyên gia hay checksum lịch sử nếu hồ sơ chưa có.

## 4. Ma trận nội dung cho từng nhận xét

| Nhận xét | Việc cần có trong bản cập nhật | Vị trí dự kiến | Mức hoàn thành trong đợt biên soạn |
|---|---|---|---|
| **02 — Khoảng trắng** | Đưa khối ký chủ nhiệm về cùng trang nội dung biểu mẫu Việt; rà trang ngắn và ngắt trang sau khi chốt nội dung | `frontmatter/research-info-vi.tex`, `research-body-vi.tex`; template chỉ khi cần | Sửa bố cục thật trong PDF |
| **03 — Ảnh chủ nhiệm** | Giữ ảnh đã có, kiểm vị trí và tỷ lệ sau khi dàn lại biểu mẫu | `frontmatter/principal-investigator.tex`, `template/forms.tex` | Giữ và kiểm lại |
| **04 — Đánh số hình** | Rà caption, label, tham chiếu, danh mục hình/bảng sau khi thêm mục hoặc sơ đồ | Các nguồn thay đổi và danh mục tự sinh | Kiểm tra lại toàn bộ số và tham chiếu |
| **05 — Chuẩn hóa định dạng** | Giữ quy tắc chữ/lề; thống nhất thuật ngữ và cách ghi trạng thái; giữ bố cục vừa sửa | Template, các chương, biểu mẫu và tóm tắt | Đồng bộ văn bản và bố cục |
| **06 — Mô hình văn bản** | Bổ sung mục riêng về bài toán NLP tiếng Việt, dữ liệu đầu vào, đầu ra, tiền xử lý, kiến trúc dự kiến, cách huấn luyện và đánh giá; đặt cạnh baseline TF-IDF đã chạy | Chương 3, mục thiết kế văn bản mới; dẫn chiếu từ Chương 2 và kết luận | Đủ thiết kế nghiên cứu; không ghi đã huấn luyện tiếng Việt |
| **07 — Nén mô hình** | Giữ bảng FP32/PTQ/QAT/pruning; giải thích đánh đổi chất lượng, lỗi nặng, dung lượng và tốc độ, cùng lý do chọn phương án | `image-design.tex`, `results.tex`, kết luận | Hoàn thiện giải trình bằng kết quả đã có |
| **08 — Đa phương thức** | Bổ sung sơ đồ và diễn giải ba trường hợp: tích hợp hệ thống hiện tại, fusion CrisisMMD đã chạy, thiết kế mở rộng cho tiếng Việt | `architecture.tex`, mục thiết kế fusion mới, `scope.tex` | Đủ kiến trúc và phân biệt mức thực hiện |
| **09 — Vai trò ngôn ngữ** | Có bảng chức năng của văn bản: phân loại, trích thông tin, bổ sung ngữ cảnh; chỉ rõ phần đã có, phần dự kiến và giới hạn | Mục thiết kế văn bản, bảng đối chiếu và kết luận | Giải thích đóng góp dự kiến và kết quả pilot hiện có |
| **10 — Ablation** | Giữ kết quả ảnh/text/fusion CrisisMMD; bổ sung thiết kế ablation cho dữ liệu cứu hộ tiếng Việt với cùng nhiệm vụ, nhãn, split và chỉ số | `evaluation-design.tex`, `multimodal-pilot.tex` | Đủ phương pháp và bảng cấu hình; không cần chạy phép thử mới |
| **11 — Quy trình dữ liệu** | Viết đủ thu thập → sàng lọc → làm sạch → gán nhãn → chia tập → quản lý phiên bản; phân biệt bước hiện có và phương án hoàn thiện | `data.tex`, phụ lục tái lập | Đủ quy trình, ghi rõ thông tin nguồn còn thiếu |
| **12 — Đặc điểm ảnh** | Giữ thống kê header và phân bố theo lớp; giải thích định dạng, độ phân giải, dung lượng, EXIF/RGB/letterbox và các rủi ro chất lượng | `data.tex`, `image-design.tex` | Mở rộng diễn giải, giữ số liệu đã có |
| **13 — Điểm khẩn cấp** | Giải thích công thức LR, nhãn OR, hệ số bằng nhau, ảnh hưởng số cờ và baseline; bổ sung sơ đồ luồng điểm hiện tại/đề xuất | `methods.tex`, `architecture.tex`, `results.tex` | Đủ giải thích toán học và thiết kế tích hợp; giữ rõ adapter chưa dùng `E_i` |
| **14 — RQ1–RQ3** | Mỗi RQ có câu trả lời, đối chứng, kết quả, cơ chế khả dĩ, điều kiện áp dụng và giới hạn; nêu riêng tám sai lệch RQ2 | `results.tex`, `limitations.tex`, kết luận | Hoàn thiện phân tích từ số đã có; không chạy lại thống kê |
| **15 — Chất lượng ảnh di động** | Trình bày kết quả suy giảm CPU hiện có và một quy trình đánh giá ảnh camera/Android đầy đủ: tình huống, phép đo và cách ghi kết quả | `evaluation-design.tex`, `setup.tex`, `results.tex`, `limitations.tex` | Đủ thiết kế đánh giá trên thiết bị; không ghi đã thực hiện |

## 5. Trình tự thực hiện đề xuất

Thứ tự dưới đây tổ chức công việc biên soạn theo phụ thuộc nội dung, không phải mức ưu tiên do Hội đồng quy định. Các mã **ND-01–ND-06** là đợt mới; không ghi đè kết quả hoặc trạng thái P00–P14 trước đây.

### ND-01 — Chốt cấu trúc và đồng bộ mô tả hiện trạng

**Mục tiêu:** tạo chỗ đặt nội dung mới và sửa các đoạn chưa đồng bộ trước khi mở rộng phương pháp.

**Công việc:**

1. Dùng ma trận 14 nhận xét ở trên làm danh sách kiểm nội dung.
2. Sửa các đoạn còn nói CrisisMMD chỉ là tài liệu tham khảo/chưa dùng để huấn luyện trong Mở đầu, bảng nghiên cứu liên quan và bảng đối chiếu thuyết minh. Nêu rõ nó đã được dùng trong pilot riêng, còn Dataset_Flood và RQ1–RQ3 có phạm vi khác.
3. Bổ sung CrisisMMD vào bản đồ dữ liệu/phương pháp, với nhãn informative; không gộp mẫu hoặc nhãn của pilot vào dataset mức ngập và khẩn cấp.
4. Chốt nơi đặt hai mục mới: `text-design.tex` và `multimodal-design.tex` dưới `report/chapters/02-data-methods/sections/`; cập nhật lời dẫn và các lệnh `input` trong chương khi triển khai.
5. Thống nhất ba cách ghi trạng thái theo Mục 3 của kế hoạch này.

**Nguồn sửa chính:** `chapters/introduction.tex`, `01-foundations/sections/related-work.tex`, `02-data-methods/chapter.tex`, `02-data-methods/sections/overview.tex`, `data.tex`, `scope.tex`, `appendices/supplementary-results.tex`.

**Đầu ra:** cấu trúc nội dung và mô tả nguồn dữ liệu thống nhất. Chưa viết thêm kết quả mới.

### ND-02 — Hoàn thiện dữ liệu, nén mô hình và điểm LR

**Nhận xét:** 07, 11, 12, 13. Đầu vào là nguồn hiện tại sau ND-01 và các bảng đã lưu.

**Nội dung cần viết:**

- **Dữ liệu:** mô tả từng công đoạn đã biết từ notebook/artifact; đặt một bảng “hồ sơ hiện có / thông tin chưa có / phương án hoàn thiện”. Quy trình gán nhãn nhiều người và đánh giá độ đồng thuận được trình bày như phương án bổ sung nếu chưa thực hiện. Không thay các ô nguồn chưa biết bằng nguồn suy đoán.
- **Ảnh:** nối thống kê format, độ phân giải, dung lượng với tiền xử lý và khả năng mất thông tin. Phân biệt kích thước tệp gốc, tensor đầu vào và chất lượng nhận diện. Dẫn kết quả suy giảm CPU hiện có khi có liên quan, không biến mô tả header thành kiểm chứng ảnh camera.
- **Nén:** làm rõ lượng tử hóa và cắt tỉa là hai nhóm kỹ thuật khác nhau; đọc đồng thời Accuracy/F1, recall high, lỗi nặng, dung lượng và độ trễ trong cùng phiên. Giải thích lựa chọn nguyên mẫu theo đánh đổi, không khái quát rằng QAT luôn kém hoặc pruning luôn nhanh.
- **LR:** giải thích năm cờ, 32 tổ hợp, nhãn OR, công thức sigmoid, bias/hệ số và threshold. Có ví dụ tính từ hàm đã lưu, ghi rõ là minh họa đại số. Nêu vì sao hệ số bằng nhau và vì sao độ khớp OR không chứng minh giá trị nghiệp vụ.
- **Luồng điểm:** sơ đồ hiện tại thể hiện app tính/gửi LR → backend lưu payload → adapter dùng urgency/từ khóa. Sơ đồ đề xuất trình bày cách phân biệt các trường điểm và xử lý thiếu/mâu thuẫn; không ghi nó đã chạy.

**Nguồn sửa chính:** `data.tex`, `image-design.tex`, `methods.tex`, `03-system/sections/architecture.tex`, các đoạn nén/LR trong `04-evaluation/sections/results.tex`.

**Tiêu chí nội dung:** người đọc hiểu dữ liệu hình thành thế nào, phép nén đánh đổi gì và LR tính gì; mọi thông tin chưa biết vẫn được nhận diện rõ. Không cần thu thập ảnh, train hoặc chạy suy luận mới.

### ND-03 — Viết thiết kế văn bản và đa phương thức đầy đủ

**Nhận xét:** 06, 08, 09. Dựa trên phân biệt dữ liệu và ngữ nghĩa điểm của ND-01/ND-02.

**Mục thiết kế văn bản cần có:**

1. Bài toán phân loại nội dung tin cứu hộ tiếng Việt theo đăng ký; các thông tin có thể trích như địa điểm, số người và dấu hiệu nguy cấp. Phân biệt nhãn phân loại văn bản với mức ngập và điểm ưu tiên cuối cùng.
2. Bảng đầu vào/đầu ra, bản nháp định nghĩa nhãn và quy tắc xử lý tin ngắn, thiếu thông tin, viết tắt hoặc mâu thuẫn. Định nghĩa mới phải ghi là đề xuất, chưa phải nhãn chuyên gia đã xác nhận.
3. Chuỗi xử lý: chuẩn hóa văn bản → biểu diễn → bộ phân loại/trích thông tin → kiểm tra thiếu/mâu thuẫn → dữ liệu hỗ trợ xác minh.
4. Kiến trúc theo phương án trong thuyết minh, gồm thành phần mã hóa, đầu phân loại, loss và quy tắc chọn checkpoint dự kiến. Nếu đề xuất điều chỉnh kiến trúc, giải thích lý do; không đổi thành phát biểu đã huấn luyện.
5. TF-IDF + LR CrisisMMD được trình bày là baseline đã thực hiện trên nhiệm vụ riêng. Không gọi LR năm cờ là NLP hoặc chuyển kết quả tiếng Anh thành kết quả tiếng Việt.
6. Một ví dụ khai báo tiếng Việt tự soạn, ghi nhãn “minh họa thiết kế”, mô tả đầu ra mong muốn bằng lời; không gán confidence thực nghiệm.

**Mục thiết kế đa phương thức cần có:**

- Bảng so sánh tích hợp trường dữ liệu, kết hợp đầu ra và kết hợp đặc trưng.
- Mô tả đúng fusion tuyến tính CrisisMMD đã huấn luyện: hai nhánh đặc trưng, chuẩn hóa, phép nối và classifier. Phân biệt encoder ảnh frozen của pilot với mô hình phân loại mức ngập trong ứng dụng.
- Sơ đồ mở rộng tiếng Việt đề xuất: ảnh + mô tả + metadata → các nhánh xử lý → hợp nhất → đầu ra theo nhiệm vụ chung → người dùng/điều phối viên xác nhận. Có chú giải phần đã có và phần đề xuất.
- Phương án thiếu ảnh, thiếu văn bản hoặc hai nguồn mâu thuẫn; tách chính sách chuyển sang classifier đơn khỏi phép che block của fusion cố định.
- Bảng vai trò văn bản: thông tin bổ sung được gì, dùng ở bước nào, đã có ở pilot hay mới là thiết kế. Không ánh xạ xác suất informative trực tiếp sang urgency hoặc ưu tiên cứu hộ.

**Nguồn sửa chính:** hai tệp mới `text-design.tex`, `multimodal-design.tex`; lời dẫn chương, `scope.tex`, `architecture.tex` và các tham chiếu liên quan.

**Tiêu chí nội dung:** có phương pháp đủ cụ thể để triển khai sau này, đồng thời người đọc nhận biết ngay phần tiếng Việt/fusion trong ứng dụng chưa được thực hiện. Không cần code model hoặc sửa adapter.

### ND-04 — Hoàn thiện ablation, diễn giải RQ và thiết kế đánh giá ảnh di động

**Nhận xét:** 10, 14, 15. Dùng định nghĩa đầu ra của ND-03 và kết quả đã lưu.

**Ablation:**

1. Giữ bảng và diễn giải CrisisMMD trên cùng 701 test IDs; nêu đúng cả kết quả bất lợi khi che ảnh và CI chênh lệch chứa 0.
2. Viết thiết kế ablation tiếng Việt theo bộ cấu hình ảnh-only, text-only, ảnh + text và đối chứng kết hợp đơn giản. Phải mô tả một nhiệm vụ/nhãn chung cho mọi cấu hình; không ghép Accuracy mức ngập với độ khớp OR.
3. Đặc tả ID ghép cặp, chia theo nhóm/sự kiện, nguyên tắc giữ cùng test và chỉ số, cách xử lý thiếu modality, phân tích lỗi và độ bất định dự kiến. Định nghĩa nhãn mới là dự thảo nghiên cứu, chưa có corpus để xác nhận.
4. Bảng thiết kế gồm cấu hình, đầu vào, đầu ra, cách đánh giá và trạng thái. Phần tiếng Việt ghi “Chưa thực hiện”, không có số hiệu năng dự kiến.

**RQ1–RQ3:**

- Mỗi RQ có một đoạn theo cùng cấu trúc: câu hỏi → kết quả quan sát → đối chứng → giải thích khả dĩ → giới hạn → kết luận trả lời câu hỏi.
- RQ1: phân tích cơ chế cổng không gian, lựa chọn cấu hình, mật độ cạnh, quantile/top-k và tác động của bản sao. Không mô tả cơ chế khả dĩ như nguyên nhân đã được cô lập.
- RQ2: phân biệt bất biến sao chép khi grouping cố định với sự phù hợp của thứ tự ưu tiên; giải thích vì sao ổn định không tự chứng minh xếp đúng nhu cầu. Giữ rõ ba raw p Spearman và năm Holm còn chưa khớp.
- RQ3: phân tích quan hệ giữa phân hoạch, điểm ưu tiên, chi phí di chuyển và ràng buộc lịch; giữ kết quả thua nearest-first và đơn vị suy luận 40 seed.
- Bổ sung bảng tổng hợp “kết quả hỗ trợ điều gì / chưa hỗ trợ điều gì / cách hiểu trong phạm vi mô phỏng”. Không sửa số gốc hoặc chạy lại thống kê trong đợt biên soạn này.

**Chất lượng ảnh trên di động:**

- Giữ bảng clean + tám biến đổi CPU và diễn giải ảnh tối/mờ/giảm kích thước; ghi đúng model, split và phạm vi CPU.
- Bổ sung quy trình đề xuất cho ảnh camera: ánh sáng, mưa/che khuất, rung/mờ, góc chụp, độ phân giải và nén. Bảng kịch bản phải cho biết đầu vào, thao tác, lỗi cần quan sát và chỉ số sẽ đo.
- Mô tả riêng chất lượng phân loại và độ trễ tiền xử lý/suy luận trên thiết bị, cùng metadata phiên đo dự kiến. Nêu rõ cách so cùng ảnh và cách ghi lỗi, thay vì điền số đo Android chưa có.

**Nguồn sửa chính:** `evaluation-design.tex`, `04-evaluation/sections/setup.tex`, `results.tex`, `multimodal-pilot.tex`, `limitations.tex`.

**Tiêu chí nội dung:** có thiết kế đánh giá đủ rõ để người đọc hiểu phép so sánh; có diễn giải sâu từ số đã có. Không cần inference, bootstrap, benchmark, điện thoại hoặc ảnh mới.

### ND-05 — Đồng bộ thuyết minh, kết luận và các bản tóm tắt

**Mục tiêu:** nội dung mới không chỉ xuất hiện trong một tiểu mục của Chương 3.

1. Cập nhật bảng đối chiếu thuyết minh với các cột: nội dung đăng ký, nội dung đã thực hiện, phần thiết kế bổ sung trong báo cáo và phần chưa đánh giá.
2. Đồng bộ Mở đầu, giới thiệu chương, phạm vi, kiến trúc và kết luận. Mỗi nội dung về NLP/fusion phải giữ cùng tên nhiệm vụ và cùng trạng thái.
3. Đồng bộ hai nguồn dùng chung `research-body-vi.tex`/`research-body-en.tex`, bản tin và các tóm tắt Việt–Anh. Dùng mô tả ngắn cho phương án mới; giữ số đã có cho kết quả.
4. Phần hạn chế tập trung vào điều chưa kiểm chứng; phần phương pháp phải chứa thiết kế cụ thể, không chỉ thêm câu “sẽ nghiên cứu trong tương lai”.
5. Tạo bảng bàn giao 02–15 theo hai cột độc lập: **nội dung phản hồi trong báo cáo** và **trạng thái thực hiện/đánh giá**. Không đổi ledger nghiên cứu lịch sử thành đã chạy hoặc đã xác nhận chỉ vì bổ sung văn bản.

**Nguồn sửa chính:** `chapters/introduction.tex`, `appendices/supplementary-results.tex`, `chapters/conclusion.tex`, `frontmatter/research-body-vi.tex`, `research-body-en.tex`, `deliverables/content/` và tài liệu bàn giao mới của đợt ND.

**Tiêu chí nội dung:** mọi nhận xét 02–15 trỏ được tới mục cụ thể; không còn mâu thuẫn “chưa dùng CrisisMMD”; tóm tắt không mạnh hơn kết quả trong thân bài.

### ND-06 — Hoàn thiện hình thức và kiểm PDF

**Nhận xét:** 02, 03, 04, 05. Thực hiện sau khi nội dung ND-01–ND-05 ổn định.

1. Rút gọn chỗ lặp trong biểu mẫu Việt hoặc điều chỉnh cách gom khối nội dung/ký để xử lý trang chỉ có chữ ký. Giữ cỡ chữ và lề của mẫu; không thêm khoảng âm để ép trang.
2. Kiểm lại ảnh chủ nhiệm và biểu mẫu tiếng Anh đã sửa. Giữ nguyên cách phóng từng trang thuyết minh 105%.
3. Rà mục lục, tiêu đề, đánh số hình/bảng, nhãn, chú thích, tham chiếu, sơ đồ mới và bảng dài. Không ghi số hình/trang bằng tay.
4. Dựng lại một mặt, hai mặt và các bản tin/tóm tắt qua quy trình hiện có; xem trang thay đổi, trước/sau trang đó và các phần kết biểu mẫu.
5. Kiểm log, font, tràn lề và bảng đối chiếu 14 nhận xét. Khi số trang đổi, lấy số mới từ PDF cuối.

Lệnh dự kiến khi thực hiện, từ gốc repo:

```bash
make -C report content
make -C report content-twoside
make -C report check
python3 report/scripts/check_report.py --build-dir build/content-twoside
git diff --check
```

Đây là kiểm tra biên soạn/PDF. Không chạy train, inference, benchmark, thống kê RQ hoặc kiểm thử ứng dụng. Các bảng định lượng được quản lý qua nguồn sinh hiện có; không sửa tay `generated/tables/` để thay số liệu.

**Đầu ra khi hoàn tất đợt thực hiện:** nguồn LaTeX đã sửa, `report/main.pdf`, bản hai mặt, bốn bản tin/tóm tắt và bảng bàn giao nội dung 02–15. Không tự commit/push.

## 6. Danh sách kiểm hoàn thành nội dung

- [ ] Đủ 14 nhận xét 02–15, mỗi nhận xét có vị trí phản hồi cụ thể; giữ và rà lại các mục đã đáp ứng.
- [ ] Có mục thiết kế văn bản tiếng Việt, mục thiết kế đa phương thức và bảng vai trò của văn bản.
- [ ] Có quy trình dữ liệu, giải thích LR/nén và diễn giải chất lượng ảnh đầy đủ.
- [ ] Có thiết kế ablation chung nhiệm vụ và kế hoạch đánh giá ảnh camera/Android, ghi rõ chưa thực hiện.
- [ ] RQ1–RQ3 có câu trả lời và bàn luận; kết quả âm và tám sai lệch RQ2 vẫn được trình bày đúng.
- [ ] Kết quả CrisisMMD và CPU được dùng đúng nhiệm vụ, model và môi trường; không điền số mới cho phần đề xuất.
- [ ] Mở đầu, thân bài, bảng đối chiếu, kết luận và tóm tắt Việt–Anh nhất quán.
- [ ] Trang ký lẻ được xử lý; ảnh, trang tiếng Anh và 12 trang thuyết minh vừa chỉnh vẫn đúng bố cục.
- [ ] PDF cuối qua kiểm tra nguồn/danh mục/log và xem trực quan cả hai bản in.
- [ ] Bàn giao phân biệt “đã bổ sung nội dung” với “đã thực hiện/đánh giá”; không xác nhận thay Hội đồng.

Hoàn thành danh sách này đáp ứng phạm vi **hoàn thiện nội dung báo cáo** mà người dùng yêu cầu. Những phép đo, dữ liệu hoặc xác nhận chuyên môn chưa có vẫn giữ đúng trạng thái thực tế, không chặn việc viết phần thiết kế và giải trình.
