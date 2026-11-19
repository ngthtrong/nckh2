# Kế hoạch thực nghiệm NLP và fusion cho báo cáo cứu hộ tiếng Việt

## Cập nhật thực thi ngày 08/11/2026

Sau khi xác nhận chưa có dữ liệu và người gán nhãn, người dùng cho phép AI tự gán lại nhãn để hoàn thiện báo cáo. Đợt thực thi mở [pilot tiếng Việt dịch và nhãn AI](outputs/vi-nlp-fusion-silver-20261108/README.md) riêng: chọn 300 cặp CrisisMMD, dịch và gán nhãn từ câu nguồn, loại bốn ca chưa rõ nghĩa trước fit, giữ 179/58/59 cặp train/validation/test. Protocol, dự đoán, kết quả và receipt được lưu trong gói pilot; mã nằm ở [thucnghiem/vi_rescue](../../thucnghiem/vi_rescue/README.md).

Đây là thay đổi phạm vi được chỉ đạo trong phiên, không phải đã thu đủ corpus bản địa hoặc nhãn người độc lập theo kế hoạch gốc. Các mục VN-00–VN-07 bên dưới giữ thiết kế xác nhận trên tin tiếng Việt gốc; trạng thái `PLAN_ONLY` trong Material Passport là snapshot lúc lập kế hoạch. Nhãn AI của pilot không làm gate human-gold cũ chuyển sang đạt. Phần kết quả đã chạy được báo riêng trong Mục “Pilot tiếng Việt dịch và nhãn AI” của báo cáo.

## Material Passport

- Origin Skill: `academic-research-suite / experiment-agent`.
- Origin Mode: `plan`, xử lý trực tiếp từ thiết kế ND-01–ND-06 đã có.
- Origin Date: **08/11/2026, Asia/Taipei**.
- Verification Status: **PLAN_ONLY — chưa thu dữ liệu, gán nhãn hoặc chạy mô hình**.
- Version Label: `vi_nlp_fusion_plan_v1`; cấu hình dưới đây là đề xuất, chưa phải protocol đã khóa hoặc quyết định chuyên môn đã xác nhận.
- Phạm vi: lập kế hoạch để thực nghiệm các phần tiếng Việt đang ghi là thiết kế. Không thực thi kế hoạch, sửa ứng dụng hoặc dựng lại PDF trong đợt này.

## 1. Mục tiêu và điểm xuất phát

Chuyển thiết kế ở [mục văn bản](../../report/chapters/02-data-methods/sections/text-design.tex), [mục đa phương thức](../../report/chapters/02-data-methods/sections/multimodal-design.tex) và [thiết kế ablation](../../report/chapters/02-data-methods/sections/evaluation-design.tex) thành một chuỗi thí nghiệm có dữ liệu thật, nhãn độc lập, đối chứng và kết quả kiểm tra lại được.

| Thành phần | Hiện có, đã đọc lại | Còn phải làm |
|---|---|---|
| Nhánh công khai | Pilot CrisisMMD tiếng Anh: text/ảnh/fusion cùng target informative; CI hiệu đều chứa 0 | Không dùng kết quả này thay đánh giá tiếng Việt |
| Thiết kế tiếng Việt | Phân loại yêu cầu hỗ trợ; DistilBERT; fusion; xử lý thiếu nguồn | Chốt nhãn, corpus và thực hiện từng cấu hình |
| Bộ gán nhãn cũ | [annotation-kit](outputs/multimodal-20261108/annotation-kit/README.md): **0 bản ghi, 0 nhãn** | Tạo phiên bản riêng sau khi chốt nhiệm vụ mới |
| Gate cũ | [validate_vi_intake.py](../../thucnghiem/multimodal/validate_vi_intake.py) yêu cầu target/expert approval, hai người gán và nhãn phân xử | Bổ sung kiểm tra ngữ nghĩa, split, thiếu nguồn và hai chế độ nhãn; chưa có gate mới |
| Mã pilot | [thucnghiem/multimodal](../../thucnghiem/multimodal/README.md) có quy trình train/evaluate/verify và bảo toàn artifact | Đường dẫn/task được viết riêng cho CrisisMMD; không chạy nguyên pipeline này trên corpus mới |
| Tích hợp | Adapter chưa dùng điểm LR trong `E_i`; chưa có NLP/fusion tiếng Việt trong app | Tích hợp là giai đoạn riêng sau đánh giá, không phải điều kiện để có kết quả offline |

[Snapshot đầu vào](outputs/vietnamese-nlp-fusion-plan-20261108/current-state.json) giữ số hàng và hash các nguồn đã đọc. Chưa chạy gate cũ trong đợt lập kế hoạch; nhận định chưa đủ điều kiện dựa trên tệp trống và yêu cầu của mã nguồn.

**Khác biệt phải xử lý trước:** bộ gán nhãn cũ đề xuất *mức ưu tiên để người trực xem xét*, còn ND đề xuất *có/không có yêu cầu hỗ trợ cứu hộ*. Không dùng chung tên task hoặc âm thầm chuyển nhãn. Kế hoạch này đi theo nhiệm vụ nhị phân của ND, với task ID dự kiến `vi_rescue_request_presence_v1`. Người phụ trách cần xác nhận định nghĩa trước khi thu nhãn; nhu cầu đánh giá urgency/ưu tiên vẫn cần protocol và chuyên môn riêng.

## 2. Câu hỏi nghiên cứu và biến kiểm soát

Các mã VN-Q dưới đây chỉ dùng cho đợt thực nghiệm mới, không đổi RQ1–RQ3 hoặc tạo câu hỏi mới trong bài đã công bố.

| Mã | Câu hỏi | Phép so sánh dự kiến | Điều cần giữ cố định |
|---|---|---|---|
| VN-Q1 | DistilBERT có cải thiện dự đoán yêu cầu hỗ trợ từ văn bản so với TF-IDF không? | T2 so với T0; T1 giúp tách biểu diễn frozen và fine-tuning | Corpus, nhãn, split, test IDs và chỉ số |
| VN-Q2 | Ghép ảnh và văn bản có thêm giá trị so với từng nguồn trên cùng nhiệm vụ không? | F1 so với nhánh tốt hơn trong T1/I0, chọn nhánh đối chứng bằng validation | Cùng encoder frozen, tiền xử lý, phép chuẩn hóa và ngân sách chọn head |
| VN-Q3 | Kết hợp hoạt động thế nào khi thiếu nguồn hoặc hai nguồn bất đồng? | F1 che block; classifier đơn; chính sách fallback | Cùng ID, điều kiện mất nguồn khóa trước, không retrain sau test |
| VN-Q4 | Có trích được địa điểm, số người và phủ định để hỗ trợ xác minh không? | Luật có phiên bản trên gold span độc lập | Không dùng F1 phân loại câu làm F1 trích xuất |

Biến thay đổi chính là nguồn đầu vào và cách học biểu diễn/head. Nhiễu cần kiểm soát gồm sự kiện, nguồn đăng, bản sao, loại tin, mất cân bằng lớp, ảnh minh họa không cùng cảnh, thông tin sinh sau báo cáo và nhãn không thể suy ra từ một modality. Đây là so sánh thuật toán trên dữ liệu quan sát, không phải thực nghiệm nhân quả về hiệu quả cứu hộ.

Giả thuyết làm việc là mô hình văn bản có thể khai thác ngữ cảnh và ảnh có thể bổ sung thông tin. Các kết quả fusion thua, ngang hoặc chưa rõ đều phải được báo; không đặt điều kiện hoàn thành là fusion bắt buộc thắng.

## 3. Đơn vị dữ liệu và định nghĩa nhãn dự thảo

### 3.1. Corpus chính

Một đơn vị là **một báo cáo gốc**, gồm ảnh và mô tả tiếng Việt thực sự được phát hành cùng nhau. Nhiều ảnh của một báo cáo hoặc các bản đăng lại phải giữ cùng nhóm. Không ghép một ảnh mức ngập bất kỳ với câu tự soạn theo nhãn ảnh.

| Giá trị | Định nghĩa cần người phụ trách xác nhận | Trường hợp cần phân xử |
|---|---|---|
| `request` | Tin thể hiện yêu cầu cứu, sơ tán, hỗ trợ hoặc tiếp tế cho người đang chịu ảnh hưởng thiên tai | Báo hộ, trích dẫn yêu cầu cũ, đã được giải quyết, điều kiện giả định |
| `no_request` | Tin đủ nội dung để xác định không có yêu cầu theo hướng dẫn: tin thời tiết, chia sẻ kiến thức, tường thuật thuần túy | Không được suy âm chỉ vì thiếu từ khóa “cứu” |
| `uncertain` | Không đủ bằng chứng hoặc còn bất đồng chưa phân xử | Là trạng thái hồ sơ, không mặc định là lớp âm hoặc lớp thứ ba của classifier |

Phải chốt trước mốc thời gian xét một yêu cầu, phạm vi “tiếp tế”, báo hộ và tin dẫn lại. Bản nháp này chưa có người chịu trách nhiệm ký xác nhận; AI không điền thay thông tin phê duyệt.

Gold chính `y_pair` do người gán xem toàn bộ báo cáo ghép cặp. T0/T1/T2/I0/F0/F1/P0 đều dự đoán **cùng `y_pair`** trên cùng tập cặp đủ nguồn. Như vậy phép ablation đo khả năng dự đoán target chung từ từng nguồn. Ảnh-only không nhất thiết nhìn thấy một yêu cầu chỉ được nêu bằng lời; sai khác này phải được phân tích, không loại mẫu khó sau khi xem prediction.

Nếu cần kết luận riêng về đọc hiểu văn bản, bổ sung `y_text` từ lượt gán **chỉ xem câu**, có blinding với ảnh và `y_pair`. Đánh giá `y_text` là phân tích thứ cấp riêng; không so F1 trên `y_text` với F1 fusion trên `y_pair`. Nếu chưa tổ chức được lượt gán text độc lập, chỉ phát biểu text classifier dự đoán target của báo cáo, không khẳng định mọi nhãn đều suy ra được từ câu.

### 3.2. Hồ sơ cần lưu

Phiên corpus mới dự kiến có các bảng dưới đây; **chưa tạo các bảng dữ liệu trong đợt lập kế hoạch**.

| Bảng | Trường tối thiểu |
|---|---|
| Inventory | `report_id`, `event_id`, `source_id`, địa chỉ/hồ sơ nguồn, ngày lấy, căn cứ sử dụng, ngôn ngữ, trạng thái đủ nguồn, lý do giữ/loại |
| Cặp dữ liệu | Văn bản gốc/đã xử lý, đường dẫn ảnh, SHA-256, ID ảnh cha, phiên bản ẩn danh, nhóm bản sao/gần trùng, liên hệ ảnh–câu |
| Nhãn từng người | `report_id`, người gán, phiên guideline, view pair/text, nhãn, uncertainty, bằng chứng, thời điểm, nguồn nhãn human |
| Phân xử | Nhãn sau phân xử, người chịu trách nhiệm, lý do, liên kết tới hai nhãn độc lập; giữ bất đồng chưa giải quyết |
| Span | Offset trong đúng phiên văn bản; loại địa điểm/số người/dấu hiệu/phủ định; tổng số và nhóm con; trạng thái thiếu |
| Chia tập | Train/dev/test, `event_id`, nhóm nguồn, nhóm bản trùng, seed chia và hash manifest |

Hồ sơ thiếu ảnh hoặc câu vẫn nằm trong inventory. Tập cặp đầy đủ dùng cho so sánh chính; tập thiếu nguồn dùng cho đánh giá chính sách riêng. Không dùng gate dành cho cặp đầy đủ để xóa các báo cáo thiếu nguồn khỏi mẫu số vận hành.

## 4. Nguồn, gán nhãn và quy mô

### 4.1. Trình tự tìm nguồn

1. Kiểm kê hồ sơ trong nhóm hoặc dữ liệu do đơn vị phối hợp cung cấp: phải có cặp gốc và căn cứ sử dụng, không mặc định đã tồn tại.
2. Khảo sát nguồn công khai hoặc bộ dữ liệu được phát hành chính thức. Kiểm ngôn ngữ, quan hệ ảnh–câu, sự kiện, quyền truy cập/sử dụng và nhãn gốc trước khi chọn; “xem công khai” không tự tạo quyền phân phối lại.
3. Bài báo có ảnh minh họa, bài đăng lại và báo cáo do người tại chỗ gửi phải phân loại riêng. Không lấy nhiều trang từ một nguồn làm nhiều sự kiện độc lập.
4. Nếu chưa có đủ cặp thật được phép dùng, dừng nhánh fusion ở trạng thái `DATA_NOT_READY`. Có thể tiếp tục kế hoạch hoặc NLP trên corpus text thật riêng, nhưng kết quả đó không đóng ablation ghép cặp.

Không dịch CrisisMMD rồi gọi là báo cáo cứu hộ tiếng Việt thực tế. Dữ liệu dịch hoặc sinh tự động, nếu nghiên cứu sau này, phải có nhánh riêng và không xuất hiện trong test xác nhận. UIT-VSMEC có nhãn **cảm xúc**, không phải gold yêu cầu cứu hộ hay khẩn cấp ([bài gốc](https://arxiv.org/abs/1911.09339v2)).

### 4.2. Gán nhãn thử và khóa guideline

- Bố trí hai người gán độc lập và một người phân xử. Người phụ trách xác nhận task; nếu mở rộng sang urgency/ưu tiên, cần người có chuyên môn phù hợp với nội dung đó. Chưa có tên hoặc xác nhận cho các vai trò này.
- Pilot tổ chức dự kiến **60–100 báo cáo**, lấy từ nhiều nguồn/sự kiện nếu có. Đây là quy mô thử hướng dẫn và đo công sức, không phải cỡ mẫu chứng minh hiệu năng.
- Không cho người gán xem dự đoán, nhãn OR, công thức xếp hạng hoặc nhãn của nhau. Lượt text-only phải tránh người gán đã thấy ảnh/nhãn pair; nếu không tổ chức được blinding, ghi giới hạn và không gọi hai lượt độc lập.
- Báo tỷ lệ đồng thuận, Cohen kappa cho hai nhãn danh nghĩa, phân bố lớp, bảng bất đồng và nguyên nhân. Không tự đặt một ngưỡng kappa thành chứng nhận chất lượng; guideline chỉ được khóa sau khi xử lý các kiểu mơ hồ quan trọng.
- Mọi sửa guideline tạo phiên mới. Pilot có thể dùng phát triển/train về sau nhưng không vào test xác nhận. Nhãn sản xuất được giữ đủ hai lượt độc lập và lượt phân xử; các ca unresolved không bị xóa khỏi inventory.

### 4.3. Cỡ mẫu chính và số sự kiện

Cỡ mẫu cuối phải được tính sau khi biết tỷ lệ lớp, cụm bản trùng, số sự kiện và độ bất định trong pilot/development. Chưa có đầu vào để khẳng định một số mẫu là “đủ power”.

Hai kịch bản dự trù nguồn lực, chưa phải cổng thống kê:

| Kịch bản | Quy mô dự trù | Phạm vi kết luận |
|---|---|---|
| Pilot mô hình | Khoảng 300–600 cặp thật sau kiểm nguồn và nhãn | Khảo sát pipeline, lỗi và tính khả thi; ít sự kiện thì giữ phạm vi trong các sự kiện đã có |
| Nghiên cứu chính | Dự trù 1.500–3.000 cặp, cố gắng bao phủ từ khoảng 10 sự kiện khác nhau | Chỉ mở khi đã chốt thiết kế cỡ mẫu và holdout; các con số này không bảo đảm power hoặc chuyển miền |

Sau pilot, đề xuất mức hiệu ứng cần phát hiện `δ = 0,02 macro-F1` (2 điểm phần trăm) làm giả định thảo luận, **chưa được người phụ trách chọn và không phải ngưỡng an toàn cứu hộ**. Dùng mô phỏng/learning curve trong development, giữ tương quan trong nhóm và các kịch bản hiệu ứng nhỏ/không có, để ước lượng độ rộng CI hoặc khả năng phát hiện; không dùng 701 test CrisisMMD hoặc nhãn test mới để suy cỡ mẫu thuận lợi.

Nếu cần fit mô hình để ước lượng cỡ mẫu, thực hiện một sizing pilot trên phần development riêng trước khi khóa nghiên cứu chính; lưu run đó là phát triển, không đưa các mẫu đã dùng chỉnh thiết kế vào test xác nhận. Pilot nhãn 60–100 báo cáo chỉ đủ để đo quy trình tổ chức, không tự cung cấp ước lượng power đáng tin cậy. “Khóa trước fit” ở các giai đoạn sau chỉ các phép fit của nghiên cứu chính, không che giấu sizing pilot đã công bố.

Phải xem đồng thời số mẫu dương/âm và số nhóm độc lập, không chỉ tổng N. Nếu chỉ có một hoặc hai sự kiện test, không dùng bootstrap nhiều lần để tạo vẻ có nhiều sự kiện. Khi thiếu dữ liệu, hạ phạm vi kết luận và ghi nghiên cứu thăm dò; không lấp corpus bằng dữ liệu tổng hợp mang nhãn thật.

## 5. Chia tập và khóa trước khi thử mô hình

1. Khử/gom exact copy, gần trùng ảnh, văn bản lặp và báo cáo phát hành lại; audit độ đúng của việc gom, không xem dHash là chứng nhận hết trùng.
2. Định nghĩa sự kiện theo đợt thiên tai/thời gian/địa bàn có căn cứ. Nhiều bài đăng hoặc nhiều tên nguồn trong cùng một trận lũ không tự thành sự kiện mới.
3. Ghép các ràng buộc thành nhóm không được tách: cùng báo cáo, họ bản sao hoặc cùng sự kiện không đi qua nhiều split. Nếu một thành phần nối nhiều sự kiện, phải xử lý và lưu quyết định trước chia.
4. Chia theo **sự kiện/nhóm**, dự trù khoảng 60/20/20 cho train/dev/test nếu inventory cho phép. Ví dụ tổ chức 10 sự kiện thành 6/2/2 chỉ là phương án; hai sự kiện test vẫn quá ít cho khẳng định rộng. Không ép đủ tỷ lệ bằng cách tách bản sao hoặc chia một sự kiện qua nhiều tập.
5. Người quản lý dữ liệu kiểm đủ hai lớp và miền ngôn ngữ trước khóa. Quy tắc chọn holdout dùng metadata/nhãn trong quá trình xây corpus, không dùng hiệu năng mô hình; ghi rõ nếu holdout được chọn có chủ đích. Nếu không đủ điều kiện, điều chỉnh thiết kế trước fit thay vì chọn lại split sau test.
6. Lưu danh sách ID, nhóm, hash, quy tắc, seed và lý do loại. Người phát triển chỉ dùng train/dev; nhãn test do người quản lý đánh giá giữ cho tới khi model/config được đóng băng.

Vocabulary, đặc trưng có học, scaler/PCA nếu có và class weights chỉ fit train. Chọn checkpoint, `C`, learning rate hoặc threshold trên dev. Encoder tiền huấn luyện và tokenizer được pin revision/hash; audit overlap có thể kiểm với corpus mới, đồng thời ghi việc chưa kiểm được toàn bộ pretraining data.

## 6. Ma trận thí nghiệm tối thiểu

Tất cả cấu hình chính dùng cùng cặp đủ nguồn và `y_pair`. Nhánh ảnh được học đầu phân loại yêu cầu hỗ trợ, không chuyển nhãn mức ngập sang target mới.

| ID | Cấu hình | Cách học dự kiến | Vai trò |
|---|---|---|---|
| B0 | Lớp đa số | Chọn lớp từ train | Kiểm ảnh hưởng base rate |
| T0 | TF-IDF + Logistic Regression (LR) | Hai lựa chọn: word unigram/bigram hoặc char 3–5; LR regularized | Baseline văn bản tiếng Việt |
| T1 | DistilBERT đa ngôn ngữ frozen + LR | Masked mean pooling, L2; giữ encoder cố định | Đối chứng biểu diễn cho fusion F1 |
| T2 | DistilBERT fine-tuning | Mean pooling, dropout, Linear 2 lớp; cross-entropy | Thực nghiệm hướng DistilBERT đã đăng ký |
| I0 | MobileNetV3-Large ImageNet frozen + LR | Global pooling, L2; học head theo `y_pair` | Image-only đúng target |
| F0 | TF-IDF + đặc trưng I0 | Nối hai block L2, chia căn hai, LR | Fusion tuyến tính chi phí thấp, nối tiếp phương pháp pilot |
| F1 | Đặc trưng T1 + I0 | Cùng hai encoder frozen, L2 từng block, nối/chia căn hai, LR | Fusion chính, tách lợi ích thêm modality |
| P0 | Trung bình xác suất T1 và I0 | Trọng số 0,5/0,5, không fit test | Đối chứng kết hợp đầu ra đơn giản |

**Đối chứng chính VN-Q2:** chọn T1 hoặc I0 có macro-F1 dev cao hơn, khi hòa chọn T1 theo quy tắc đặt trước; so F1 với đối chứng đó trên test. Không chọn unimodal “tốt nhất” sau khi thấy test. Báo thêm F1–T1, F1–I0, F1–P0 và F0 so với các nhánh tương ứng dưới dạng đối chiếu thứ cấp.

T2 so với T0 trả lời hướng NLP; F1 so với T1/I0 trả lời thêm modality với encoder giữ nguyên. So F1 với T2 có thể báo như so sánh hệ thống khác ngân sách/khả năng học, không dùng để cô lập tác động riêng của fusion. Mọi kết quả text/ảnh/fusion vẫn phải xuất đầy đủ, kể cả khi ảnh không giúp.

### 6.1. Cấu hình khởi đầu và ngân sách lựa chọn

- LR: `C ∈ {0.1, 1, 10}`, `class_weight=balanced`, solver/tolerance/max_iter cố định và ghi phiên bản; cảnh báo không hội tụ phải được xử lý/công bố, không âm thầm bỏ lần lỗi. Vocabulary của T0 chỉ fit train; cap dự kiến 20.000 chiều, còn chiều thực ghi từ artifact.
- T0 có tối đa 6 lần fit head; T1/I0/F0/F1 mỗi cấu hình tối đa 3: tổng **18 lần fit LR** trong ma trận này. P0 và B0 không thêm quá trình fit classifier. F0 dùng kiểu TF-IDF đã chọn bằng dev ở T0, không mở thêm lưới sau khi nhìn test.
- T2 theo thiết kế báo cáo: tối đa 256 token, dropout 0,2, AdamW; learning rate `{1e-5, 2e-5}`, batch hiệu dụng 16, tối đa 5 epoch, early stopping patience 2 trên dev macro-F1. Giữ dấu, phủ định và cờ bị cắt; không thay tokenizer hoặc độ dài sau test.
- T2 dùng ba seed đề xuất `{17, 29, 43}`: 2 learning rate × 3 seed = **6 phiên**, tối đa 30 epoch tổng. Chọn learning rate theo trung bình dev của ba seed, giữ cả ba checkpoint tương ứng; khi hòa chọn learning rate nhỏ hơn, rồi checkpoint sớm hơn. Không lấy seed tốt nhất làm kết quả duy nhất.
- LR/frozen encoder dùng cấu hình tất định nếu runtime hỗ trợ; không lặp cùng fit tất định nhiều lần rồi coi là dữ liệu độc lập. Nếu solver có ngẫu nhiên ảnh hưởng, ghi seed và bổ sung độ biến động thành một nhánh đã khóa trước test.
- Fit class weights từ train. Phép so sánh xác suất giữ ngưỡng 0,5 mặc định; nếu cần hiệu chuẩn hoặc đổi ngưỡng, định trước cách tách dev và áp nhất quán, ghi riêng so với cấu hình gốc.

DistilBERT đa ngôn ngữ được model card mô tả có sáu tầng, chiều ẩn 768 và khoảng 134 triệu tham số; chưa có căn cứ thời gian/bộ nhớ cho corpus này ([model card chính thức](https://huggingface.co/distilbert/distilbert-base-multilingual-cased)). Giữ đây là hướng chính vì thiết kế hiện tại, không coi tên “distil” là bằng chứng đã phù hợp điện thoại.

PhoBERT là đối chứng tiếng Việt **tùy chọn**, không thay DistilBERT âm thầm. Nếu bổ sung, phải định trước ngân sách, tokenizer và bước tách từ theo [kho tác giả](https://github.com/VinAIResearch/PhoBERT); [bài gốc](https://aclanthology.org/2020.findings-emnlp.92/) là cơ sở chọn một encoder tiếng Việt, chưa chứng minh ưu thế trên cứu hộ. Không mở thêm nhiều backbone rồi chọn một test tốt nhất.

### 6.2. Phần mở rộng sau ma trận tối thiểu

Joint fine-tuning hai encoder, cross-attention, modality dropout và đầu gán nhãn token chỉ là các nhánh bổ sung có protocol/ngân sách riêng. Nếu thử joint fine-tuning, cần unimodal controls có mức fine-tuning tương ứng. Kết quả frozen feature fusion không được gọi là đã fine-tuning chung hai encoder.

## 7. Thiếu nguồn, mâu thuẫn và trích xuất

### 7.1. Thiếu nguồn và fallback

Khóa bốn điều kiện: đủ ảnh/câu; chỉ câu; chỉ ảnh; thiếu cả hai. Tách hai nguồn tạo điều kiện thiếu: bản ghi thực sự thiếu trong inventory và phép che nguồn nhân tạo trên cặp đầy đủ.

- Với cặp đủ nguồn, che block F1 chỉ đo phản ứng của **mô hình cố định**. Không so bằng số accuracy của test nhiều âm để che recall request giảm mạnh.
- Chính sách fallback dự kiến: đủ hai nguồn → F1; chỉ câu → T1; chỉ ảnh → I0; thiếu cả hai/lỗi giải mã → hàng xem xét. Giữ T1 để cùng encoder với F1; nếu chọn T2 cho sản phẩm, đánh giá chính sách khác và khóa riêng.
- So F1 che block với classifier đơn trên cùng tập ID theo điều kiện, báo macro-F1, recall request, tỷ lệ từ chối, tỷ lệ lỗi và coverage. Tập thiếu tự nhiên có phân bố khác tập đầy đủ nên không quy chênh lệch mean thành tác động nhân quả của mất nguồn.
- Tập ca mâu thuẫn do người gán đánh dấu trước dự đoán: khác thời điểm, ảnh minh họa, phủ định, người ngoài khung hình. Bất đồng prediction hai classifier chỉ là tín hiệu cần xem xét, không phải gold mâu thuẫn.
- Ca được chuyển người kiểm tra vẫn tính vào mẫu số phục vụ. Nếu dùng abstention, báo đồng thời lỗi trên phần được dự đoán và coverage; không tăng điểm bằng cách giấu các ca bị từ chối.

### 7.2. Trích xuất thông tin

Phiên đầu dùng luật có phiên bản để trích địa điểm, tổng số người/nhóm con và dấu hiệu kèm phủ định; không huấn luyện đầu token khi chưa có span gold. Gán span trên đúng văn bản đã ẩn danh/chuẩn hóa, lưu offset mapping để không đánh giá nhầm bản văn.

Chọn tập con theo nguồn/sự kiện và dạng câu trước khi xem prediction; khóa một phần test span độc lập. Đánh giá span precision/recall/F1 với quy tắc khớp chính xác; thêm exact match giá trị sau chuẩn hóa cho số người, tỷ lệ sai phủ định và tỷ lệ thiếu thông tin. Địa danh trích đúng chuỗi không đồng nghĩa tọa độ đã đúng. Nếu không có đủ gold span, ghi phần này chưa thực hiện, không dùng ví dụ tự soạn hoặc unit test để thay kết quả thực nghiệm.

## 8. Phân tích và tiêu chí kết luận

**Chỉ số chính:** macro-F1 nhị phân trên `y_pair` của tập test cặp đầy đủ. Báo Accuracy, precision/recall request, F1 từng lớp, confusion matrix, prevalence và số mẫu/nhóm/sự kiện. Báo theo từng sự kiện, nguồn và kiểu bằng chứng; không chỉ gộp mean. Recall request là thông tin lỗi cần theo dõi, chưa có ngưỡng đủ để cho phép vận hành cứu hộ.

| Nội dung | Cách phân tích khóa trước | Giới hạn |
|---|---|---|
| Hiệu fusion chính | Macro-F1 F1 trừ đối chứng T1/I0 đã chọn bằng dev | Không chọn lại đối chứng theo test |
| Bất định trong dữ liệu | Bootstrap ghép cặp: cùng draw cho các model; ưu tiên lấy mẫu sự kiện rồi nhóm bản trùng trong sự kiện, giữ toàn bộ hàng trong nhóm | Dự kiến 5.000 draw; đây là cấu hình, chưa chạy. Ít sự kiện không được diễn giải CI như bao phủ quần thể sự kiện rộng |
| Fine-tuning nhiều seed | Trung bình macro-F1 và khoảng min–max ba seed; CI dữ liệu dùng cùng draw ID cho từng seed rồi lấy trung bình metric | Ba seed không phải ba tập test độc lập; CI này chưa mô tả đầy đủ bất định do huấn luyện |
| Nhiều đối chứng | Một tương phản fusion chính; các hiệu khác và span là thứ cấp | CI ghi rõ chưa hiệu chỉnh; nếu thêm kiểm định hình thức phải khóa họ giả thuyết và Holm trước test, không đổi kiểm định khi thấy p |
| Nhóm lỗi | Đọc tập lỗi theo danh mục có trước, giữ cả trường hợp hai nguồn đúng/sai/ngược nhau | Phân tích sau test là mô tả; sửa model theo lỗi cần test xác nhận mới |

Quy tắc dự kiến cho mọi metric là cố định thứ tự hai lớp và `zero_division=0`. Giữ cả draw bootstrap chỉ có một lớp theo quy tắc đó, báo tỷ lệ draw thiếu lớp và giới hạn của phân bố CI; nếu hiện tượng này nhiều, cần xem lại mức dữ liệu đủ để suy luận, không bỏ draw rồi chọn CI thuận lợi hơn. Không bootstrap từng hàng độc lập khi nhiều hàng cùng sự kiện/bản sao. Cỡ mẫu suy luận là các đơn vị dữ liệu được khóa, không phải số seed × model × biến thể thiếu nguồn.

Nếu CI hiệu chứa 0, kết luận chưa xác lập ưu thế, không tự kết luận tương đương. Nếu muốn đánh giá mức cải thiện đáng kể về thực hành, phải chốt δ trước test và xem toàn CI so với δ, không chỉ dấu p. Kết quả cao hơn trên các sự kiện đã thử chưa chứng minh hiệu quả ngoài thực địa hoặc chính sách ưu tiên đúng.

**Hoàn thành thực nghiệm** nghĩa là dữ liệu/protocol hợp lệ và mọi cấu hình bắt buộc có artifact hoặc thất bại được ghi nhận, kết quả/giới hạn được bàn giao. **Đạt chất lượng để triển khai** cần tiêu chí nghiệp vụ và đánh giá riêng; không chọn một mốc F1 tùy ý để thay thế.

## 9. Các giai đoạn thực hiện và cổng chuyển

Mã **VN-00–VN-07** là nhánh mới; không ghi đè P00–P14 hoặc ND-01–ND-06.

| Giai đoạn | Công việc | Đầu ra bắt buộc | Điều kiện chuyển |
|---|---|---|---|
| VN-00 — Chốt nhiệm vụ | Thống nhất request/no_request/uncertain, thời điểm và giới hạn; chỉ định người phụ trách | `target-spec`, guideline nháp, decision log; không có chữ ký AI | Người có trách nhiệm xác nhận task và kế hoạch nhãn; không tái sử dụng approval của task ưu tiên cũ |
| VN-01 — Khả thi dữ liệu | Kiểm nguồn, quyền dùng, ảnh–câu, ngôn ngữ; pilot 60–100 báo cáo nếu có | Inventory, hồ sơ nguồn, nhãn thử, IAA và công sức | Có cặp thật dùng được; guideline đủ rõ. Nếu thiếu, giữ `DATA_NOT_READY`, chưa train fusion |
| VN-02 — Corpus và split | Thu corpus chính, hai lượt gán/phân xử, gom trùng; quyết định cỡ mẫu và holdout | Versioned corpus, annotation ledger, IAA, split/group manifest | Không còn xung đột rò rỉ chưa xử lý; đủ lớp/nhóm cho thiết kế đã chốt; protocol được khóa trước fit |
| VN-03 — Pipeline riêng | Viết mã theo task mới, gate v2, smoke train/dev và kiểm tensor/hash | Môi trường khóa, code/fixture tests, smoke receipt | Chạy đúng ID/nhãn; không đụng test hoặc ghi đè pilot cũ |
| VN-04 — NLP và ảnh | Fit B0/T0/T1/I0; T2 khi có tài nguyên đã chọn | Model, config, dev-selection, timing/tài nguyên và log từng lần | Đã chọn cấu hình bằng dev, freeze checkpoint; nếu T2 chưa chạy phải giữ riêng trạng thái cam kết DistilBERT |
| VN-05 — Fusion | Fit F0/F1/P0; khóa fallback và điều kiện che nguồn | Frozen models, hashes, manifest cấu hình và predictions chưa nối gold test | Mọi nhánh dùng cùng target/split; không thêm lưới lựa chọn sau test |
| VN-06 — Test và xác minh | Đánh giá một lần theo protocol; CI/seed/error analysis, thiếu nguồn và span nếu đủ gold | Full-precision predictions, metrics, effects, audit; kết quả âm và lỗi giữ lại | Reviewer tái tính được metric từ predictions; chỉ claim tương ứng phần thực chạy |
| VN-07 — Bàn giao | Đồng bộ đúng kết quả vào báo cáo và ma trận nhận xét | Analysis, handoff, export nguồn, PDF/check khi được thực hiện | Phân biệt đã đo/chưa đo; tích hợp app và thực địa vẫn là nhánh riêng |

Gate code chỉ kiểm cấu trúc và hash, không thay xác nhận nội dung nhãn. Gate cũ yêu cầu cả ảnh/câu và phê duyệt chuyên môn; phiên mới cần giữ kiểm tương ứng cho cohort đủ nguồn và thêm inventory thiếu nguồn, view nhãn, uncertainty, IAA, split/audit. Không bỏ kiểm tra hoặc điền `APPROVED` giả để chạy được pipeline.

## 10. Môi trường, đường dẫn và theo dõi chạy

**Hiện chưa có** thư mục `thucnghiem/vi_rescue/`. Các đường dẫn dưới đây là thiết kế cho đợt triển khai sau, không phải script hoặc artifact đã tạo.

```text
thucnghiem/vi_rescue/                  # mã và môi trường riêng
  intake.py / validate.py / split.py
  features.py / train_text.py / train_fusion.py
  evaluate.py / verify.py / predict.py
  data/<corpus_version>/              # raw, annotations, split; lưu theo quyền dùng
  artifacts/<run_id>/                 # model, cache và manifest bất biến
docs/revision-plan/outputs/vi-nlp-fusion-<run_id>/
  protocol.json / input-hashes.json / environment.json
  model-selection.csv / training.json
  predictions.csv / metrics.csv / paired-effects.csv
  missing-modality.csv / error-analysis.md
  verification.json / analysis.md / handoff.md / logs/
```

Không cung cấp lệnh train giả trỏ tới script chưa viết. Sau VN-03, README mới phải có lệnh thật đã smoke trên train/dev, thứ tự chạy và timeout; mọi script nhận `--task`, `--data-root`, `--output-dir`, từ chối ghi đè. Không sửa `common.py` cũ để trỏ toàn bộ pilot sang corpus tiếng Việt.

Python/PyTorch, Transformers, torchvision, tokenizer và các thư viện metric được khóa trong môi trường riêng sau kiểm tương thích. Không dùng môi trường report hoặc sửa dependency sản phẩm. Lưu revision/hash model, class order, pooling, transform ảnh, token length và truncation; không mặc định dùng tiền xử lý classifier ngập cho encoder ImageNet mới.

| Nhánh tài nguyên | Phạm vi phù hợp để dự trù | Việc phải xác minh trước chạy |
|---|---|---|
| CPU | TF-IDF/LR; trích đặc trưng frozen theo batch nhỏ và cache; CI từ predictions | RAM, dung lượng cache, thời gian một batch và tổng thời gian từ pilot |
| Fine-tuning T2 | Máy có tài nguyên phù hợp, có thể CPU hoặc GPU đã được bố trí | Dry-run train/dev đo peak memory và tốc độ; chọn batch vật lý/gradient accumulation trước test, không cam kết thời gian khi chưa đo |
| Thiết bị/ứng dụng | Sau đánh giá offline và tiêu chí nghiệp vụ | Đo Android/latency/pin, ngữ nghĩa đầu ra và hợp đồng tích hợp là protocol khác |

Không sử dụng GPU, tải model hoặc gửi corpus ra dịch vụ ngoài trong đợt lập kế hoạch. Khi triển khai, phải quyết định nơi tính toán và quyền đưa dữ liệu vào môi trường đó trước; không mặc định tải tin/ảnh người dân lên notebook đám mây.

Mỗi lần chạy cần command thực, start/end, exit code, timeout, log tiến độ, số mẫu xử lý/lỗi, tài nguyên và hash output. Timeout được chọn từ smoke và ngân sách, không tự retry phiên lỗi. Giữ log lỗi và receipt lần sửa có run ID mới; không xóa run bất lợi. Chỉ thêm CI sau khi đã khóa predictions; script verify không tự train lại.

## 11. Người thực hiện và tiến độ dự trù

Vai trò cần bố trí, chưa giả định có sẵn: người phụ trách task/nguồn; hai người gán; người phân xử; người quản lý split/test; người phát triển ML; người kiểm lại metric. Một người có thể kiêm vai trò khi nguồn lực ít, nhưng phải công bố giới hạn blinding/độc lập. Không chỉ định hoặc liên hệ người bên ngoài trong đợt này.

Lịch tương đối chỉ bắt đầu khi có người và nguồn đủ điều kiện; thời gian chờ quyền dùng dữ liệu hoặc chuyên môn chưa ước lượng được.

| Khoảng công việc dự trù | Nội dung |
|---|---|
| Tuần 1 | VN-00 và kiểm inventory/nguồn; chuẩn bị guideline |
| Tuần 2 | Pilot nhãn, IAA, ước lượng công sức/cỡ mẫu; thiết kế split |
| Tuần 3–6 hoặc hơn | Gán nhãn corpus, phân xử; phát triển pipeline song song trên dữ liệu development đủ điều kiện |
| Sau corpus/split khóa, khoảng 1–2 tuần công việc | Các cấu hình NLP/ảnh/fusion; thời gian máy phải ước lượng lại từ smoke |
| Khoảng 1 tuần công việc tiếp | Đánh giá khóa, xác minh và viết kết quả |

Đây không phải cam kết hoàn thành trong một số tuần cố định. Ví dụ **dự toán minh họa, chưa đo**: 1.000 báo cáo × 2 người × 2 phút/lượt = khoảng 66,7 giờ gán; nếu 25% cần phân xử 3 phút/ca thì thêm 12,5 giờ. Tổng khoảng 79,2 giờ, chưa gồm tìm nguồn, span hoặc nhãn text-only. Hai người cùng dành tổng 4 giờ/ngày cần khoảng 20 ngày làm việc cho khối lượng này. Sau pilot phải thay giả định bằng số đo thực; không chuyển giờ công minh họa thành kết quả tiết kiệm thời gian.

## 12. Điều kiện bàn giao và việc làm đầu tiên

- [ ] Task và guideline tiếng Việt có người phụ trách xác nhận; không lẫn task ưu tiên cũ.
- [ ] Cặp dữ liệu thật có nguồn/quyền dùng; nhãn độc lập, phân xử và uncertainty truy vết được.
- [ ] Có thiết kế cỡ mẫu, nhóm/sự kiện, split và protocol khóa; mọi cấu hình cùng ID/gold.
- [ ] B0/T0/T1/T2/I0/F0/F1/P0 có kết quả hoặc ghi rõ phần không chạy; không gọi bỏ T2 là đã fine-tuning DistilBERT.
- [ ] Chỉ số, hiệu ghép cặp, seed, CI và lỗi tính lại được từ prediction full precision; test không được dùng chọn lại model.
- [ ] Báo thiếu nguồn/fallback, mâu thuẫn và span theo đúng phần có gold; không ghép các task khác nhau.
- [ ] Kết luận giữ cả kết quả âm/chưa rõ; không đồng nhất request, informative, urgency hoặc ưu tiên cuối.
- [ ] Báo cáo chỉ chuyển một phần từ “thiết kế” sang “đã thực nghiệm” khi có artifact tương ứng; app/Android/thực địa vẫn đánh giá riêng.

**Việc đầu tiên khi được yêu cầu triển khai:** VN-00 và VN-01 — chốt nhiệm vụ với người phụ trách, kiểm kê nguồn cặp tiếng Việt và tổ chức pilot nhãn. Chưa nên bắt đầu bằng fine-tuning model khi bộ gán nhãn đang trống. Kế hoạch này không tự kích hoạt các bước đó.

## 13. Nguồn đã đối chiếu và phạm vi sử dụng

| Nguồn | Dùng để lập kế hoạch | Không suy ra |
|---|---|---|
| [Bàn giao ND](outputs/content-completion-20261108/handoff.md) và ba nguồn LaTeX ở mục 1 | Task/kiến trúc/ablation đang đề xuất | Đã có dữ liệu hoặc mô hình tiếng Việt |
| [Kit cũ](outputs/multimodal-20261108/annotation-kit/README.md), validator và [mã pilot](../../thucnghiem/multimodal/README.md) | Khoảng trống dữ liệu, schema/gate và phần có thể tái sử dụng | Gate hiện có đã đủ cho task mới; code cũ có thể chạy nguyên trạng |
| [DistilBERT multilingual model card](https://huggingface.co/distilbert/distilbert-base-multilingual-cased), mở 08/11/2026 | Loại encoder, cấu hình và quy mô tham số | Hiệu năng tiếng Việt cứu hộ hoặc trên điện thoại |
| [PhoBERT, bài gốc](https://aclanthology.org/2020.findings-emnlp.92/) và [kho tác giả](https://github.com/VinAIResearch/PhoBERT), mở 08/11/2026 | Đối chứng tùy chọn, yêu cầu tiền xử lý riêng | Mô hình tốt nhất hiện nay hoặc vượt DistilBERT trên task này |
| [UIT-VSMEC, phiên bản v2 của bài gốc](https://arxiv.org/abs/1911.09339v2), mở 08/11/2026 | Phân biệt nhãn cảm xúc với nhãn yêu cầu cứu hộ | Có corpus cứu hộ hoặc nhãn urgency dùng ngay |

Đây là tra cứu có mục tiêu để lập kế hoạch, không phải systematic review hoặc khảo sát đầy đủ mọi bộ dữ liệu tiếng Việt. Chưa tìm/tải corpus mới và chưa xác minh tồn tại một bộ ảnh–tin cứu hộ tiếng Việt đủ điều kiện dùng ngay.
