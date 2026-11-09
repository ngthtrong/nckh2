# Kết quả pilot ảnh–văn bản trên CrisisMMD

## Material Passport

- Origin: academic-research-suite / experiment-agent, run + validate.
- Date: 2026-11-08, Asia/Taipei.
- Verification: EXECUTED; metric/hash/reload và CI được kiểm lại bằng script. Chưa replay toàn bộ training trong lần độc lập.
- Scope: một benchmark công khai, một sự kiện test; không phải đánh giá tiếng Việt hoặc cứu hộ thực địa.

## Dữ liệu và phép thử thực có

Tải ba TSV agreed-label từ kho tác giả revision `8862149a36f485f980cfd6ac719cba65e296647c` và ảnh từ QCRI revision `10a5626ba112ab9c50369c473a2062bcf205d708`. Giấy phép CC-BY-NC-SA-4.0 được khai báo trong card QCRI; dữ liệu thô/ảnh/artifacts giữ local. Tổng nguồn TSV là **12.708 cặp**, không phải toàn corpus hoặc toàn bộ 18.082 hàng của bản phát hành chung.

Protocol khóa trước training/test predictions và trước tải ảnh đã chọn; probe source/schema đã đọc metadata trước đó, xem `protocol-clarifications.md`. Gộp ba split gốc rồi giữ Sri Lanka floods cho test, Maria cho validation, năm sự kiện khác cho train. Mỗi nhóm tweet/text chỉ giữ một pair và chọn hash với cap 3.000/600, không cân bằng theo nhãn. 4.309 cặp được tải/giải mã, **0 failure**. Audit SHA256/dHash loại 48 hàng thuộc component xuyên split, giữ **4.261 cặp**. Không thay hoặc bù mẫu sau loại.

| Split | Cặp | Informative | Not informative | Nhóm bản trùng |
|---|---:|---:|---:|---:|
| Train | 2.971 | 2.188 | 783 | 2.895 |
| Validation | 589 | 340 | 249 | 583 |
| Test Sri Lanka | 701 | 182 | 519 | 682 |

Mọi cấu hình dùng cùng 701 test IDs. Dịch chuyển tỷ lệ nhãn giữa sự kiện được giữ; không chỉnh prior hay threshold dựa trên test. dHash ≤4 là heuristic bảo thủ, không chứng minh hết semantic duplicates. Không audit overlap với dữ liệu pretraining ImageNet. Card nguồn mô tả tiếng Anh; chưa đánh giá ngôn ngữ từng hàng và có lỗi mã hóa văn bản kế thừa nguồn.

## Huấn luyện

- Text: TF-IDF unigram/bigram, vocabulary fit train, thực có **5.345 chiều**, LR đọc câu tự do. Đây không phải LR năm cờ của ứng dụng.
- Ảnh: **576 chiều** MobileNetV3 Small ImageNet frozen, L2. Không dùng lại bộ phân loại mức ngập hoặc test đã chọn model cũ.
- Fusion: nối hai block L2 rồi chia căn hai, LR được học trên nhãn informative chung. Là linear feature fusion; không có cross-attention, tương tác phi tuyến hay fine-tuning chung hai encoder.
- Cùng thử C=0.1/1/10 cho ba classifier, chọn bằng validation, giữ ngưỡng 0.5. C chọn lần lượt text **0.1**, ảnh **10**, fusion **1**. Toàn bộ chín kết quả dev lưu tại `model-selection.csv`; model được đóng băng trước test.
- Một split và một seed classifier 20261108; encoder không được huấn luyện lại. Chưa có lặp nhiều sự kiện hoặc độ biến động nhiều seed học sâu.

## Kết quả test

| Cấu hình | Macro-F1 (%) | Accuracy (%) | Recall informative (%) |
|---|---:|---:|---:|
| Lớp đa số từ train | 20,61 | 25,96 | 100,00 |
| Chỉ text | 76,60 | 79,46 | 85,71 |
| Chỉ ảnh | 76,19 | 79,32 | 82,97 |
| Trung bình xác suất | 77,12 | 80,17 | 84,07 |
| **Fusion nối đặc trưng** | **78,35** | **81,17** | **86,81** |
| Fusion che ảnh, không retrain | 48,55 | 75,46 | 6,04 |
| Fusion che text, không retrain | 72,77 | 76,32 | 77,47 |

Majority được fit từ train, nên dự đoán informative cho mọi test; không được thay bằng lớp đa số test sau khi xem nhãn. Trung bình xác suất là đối chứng đơn giản chưa hiệu chuẩn. Bảy cấu hình có **4.907 hàng dự đoán**, không phải 4.907 cặp độc lập. Probability được giữ full precision trong CSV.

| Hiệu macro-F1 fusion trừ đối chứng | Điểm phần trăm | CI 95% |
|---|---:|---:|
| So với text | +1,75 | [-2,06; +5,46] |
| So với ảnh | +2,16 | [-0,41; +4,80] |
| So với trung bình xác suất | +1,23 | [-1,20; +3,85] |

CI percentile bootstrap dùng 2.000 draw ghép cặp theo 682 nhóm bản trùng, cùng draw cho các cấu hình. **Cả ba CI chứa 0**; chưa xác lập fusion vượt trội và cũng không chứng minh tương đương. CI chưa hiệu chỉnh, phân tích thăm dò, không có p-value hoặc kết luận ý nghĩa toàn họ. Chỉ có một sự kiện test; CI không ước lượng được độ biến động giữa các sự kiện.

Che ảnh làm recall informative của fusion giảm mạnh dù classifier text riêng có recall cao. Đây là điểm yếu thực quan sát, không được che bằng accuracy 75,46% trên test nhiều mẫu âm. Che một block không giống retrain nhánh đơn; không tuyên bố fusion chịu mất modality. CLI chuyển sang classifier đơn khi chỉ có một nguồn; đó mới là smoke kỹ thuật, chưa xác nhận chính sách fallback trên mạng/điện thoại thật.

## Ý nghĩa đối với B1/B3/B4/B5

- **B1/B4 PARTIAL:** đã có mô hình học từ văn bản tự do và đánh giá trên nguồn công khai; **chưa có đánh giá văn bản cứu hộ tiếng Việt hoặc DistilBERT như cam kết**.
- **B3 PARTIAL:** đã huấn luyện learned linear feature fusion offline; chưa joint fine-tuning, chưa đưa vào app, và điểm LR cũ vẫn chưa được adapter dùng. Informativeness khác urgency, không nối vào E_i.
- **B5 PARTIAL:** đã chạy ablation ảnh/text/both hợp lệ trên common target/test của benchmark bổ trợ. Ablation cho ưu tiên cứu hộ tiếng Việt vẫn chưa đủ dữ liệu/nhãn. Không giữ phát biểu chung “chưa chạy bất kỳ ablation nào”, cũng không gọi B5 đã đóng đầy đủ.

Nghiên cứu mới chưa đóng provenance bộ ảnh cũ, 8 sai lệch RQ2, expert dispatch validation hoặc E2E/mobile. Không tạo nhãn ưu tiên hay văn bản Việt Nam từ công thức/LLM. `annotation-kit/` có 0 hàng dữ liệu, 0 nhãn; gate NO_GO là trạng thái thực.

## Rà 11/11 loại sai lệch trong scope này

| Loại | Nhận định và giới hạn |
|---|---|
| Simpson | Một event test; báo riêng lớp bằng confusion/recall, không suy từ mean xuyên sự kiện. |
| Ecological | Đơn vị là pair/nhóm bản trùng, không suy thành số người cứu hoặc hiệu quả một địa phương. |
| Berkson/selection | Lọc nhãn thống nhất và cap train/dev tạo bias chọn mẫu; giữ công khai. |
| Collider | Điều kiện agreed-label có thể thay đổi quan hệ hai nguồn; không suy quan hệ nhân quả. |
| Base rate | Báo class counts và shift train/test; không lấy accuracy che recall informative 6,04% khi mất ảnh. |
| Regression to mean | Không chọn mẫu theo performance trước đó; hash selection khóa trước model/test. |
| Survivorship | 0 lỗi tải/giải mã; loại trùng theo protocol và báo đủ 48 hàng, không loại dự đoán sai. |
| Look elsewhere | Báo đủ 7 cấu hình, 3 contrasts và 9 dev candidates; CI chưa hiệu chỉnh, không significance. |
| Forking paths | Protocol/hash/split/C grid cố định; chưa tune sau test hoặc thử nhiều holdout rồi chọn kết quả tốt. |
| Correlation/causation | So sánh dự đoán theo cấu hình, không suy tác động lên vận hành cứu hộ. |
| Reverse causality | Không dùng outcome cứu hộ hay ưu tiên do model tạo làm gold. |

Kiểm bằng script không thay người đánh giá độc lập hoặc chấp thuận chuyên môn. Bằng chứng hiện tại hỗ trợ một pilot có thể kiểm tra lại, chưa hỗ trợ claim tổng quát tiếng Việt, đa ngôn ngữ, hiệu quả cứu hộ hoặc triển khai Edge AI cho model mới.
