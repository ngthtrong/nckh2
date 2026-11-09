# Nghiên cứu lựa chọn nhiệm vụ và mô hình bổ sung

## Material Passport

- Origin: academic-research-suite / experiment-agent, plan/run theo yêu cầu triển khai P09–P14.
- Date: 2026-11-08, Asia/Taipei.
- Scope: nghiên cứu có mục tiêu và benchmark pilot; không phải systematic review.
- User decision: chưa có người gán nhãn/chuyên gia; dùng benchmark công khai và chuẩn bị bộ gán nhãn.

## Hai nhiệm vụ phải giữ riêng

**Nhánh thực hiện ngay:** dự đoán một cặp ảnh–tweet có informative hay không trên CrisisMMD tiếng Anh, giới hạn các cặp có nhãn hai modality thống nhất. Câu hỏi mới: trên một sự kiện lũ giữ riêng, classifier học từ đặc trưng ảnh+text có macro-F1 khác các nhánh đơn và trung bình xác suất như thế nào? Đây là thí nghiệm bổ trợ, không đổi RQ1–RQ3 của bài báo hiện có.

**Nhánh tiếng Việt:** đề xuất phân loại mức ưu tiên để người trực xem xét báo cáo cứu hộ. Nhãn và ý nghĩa chính sách chưa được chuyên gia xác nhận. Chưa có dữ liệu đủ điều kiện, nên không huấn luyện bằng nhãn OR, điểm công thức hoặc văn bản sinh theo nhãn ảnh. Bộ gán nhãn ở `annotation-kit/` chuẩn bị cho người chịu trách nhiệm; 0 mẫu không được viết thành bộ dữ liệu đã tạo.

## Nguồn đã đọc và quyết định

| Nguồn chính | Nội dung xác minh | Hệ quả cho đợt này |
|---|---|---|
| [Alam et al., 2018](https://arxiv.org/html/1805.00713) | CrisisMMD có ảnh và tweet liên quan thiên tai, nhãn informativeness/humanitarian/damage | Chọn nhãn có thật, không suy nhãn mức ưu tiên cứu hộ |
| [Ofli et al., 2020, §4.1–4.4 và §5.1](https://arxiv.org/html/2004.11838) | Nhãn ảnh/text có thể bất đồng; thực nghiệm của tác giả dùng phần agreed-label; có baseline đa phương thức | Chọn agreed-label có giới hạn và công khai selection bias; không dùng số của bài làm kết quả chạy tại repo |
| [Kho tác giả, revision 8862149](https://github.com/firojalam/multimodal_social_media/tree/8862149a36f485f980cfd6ac719cba65e296647c/data/task_data) | Có ba TSV `task_informative_text_img_agreed_lab_*`, gồm label_text và label_image | Dùng đúng TSV gốc; xác nhận hai nhãn bằng nhau từng hàng |
| [QCRI, revision 10a5626](https://huggingface.co/datasets/QCRI/CrisisMMD/blob/10a5626ba112ab9c50369c473a2062bcf205d708/README.md) | Card tiếng Anh, giấy phép CC-BY-NC-SA-4.0 và ảnh theo đường dẫn | Tải ảnh từ chính tổ chức phát hành; nghiên cứu phi thương mại; raw/ảnh/model giữ local, không tự công bố |
| [Torchvision MobileNetV3 Small](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.mobilenet_v3_small.html) | Có trọng số ImageNet và transform đi kèm | Encoder frozen riêng cho benchmark; không dùng model ngập đã chọn trên test cũ |
| [scikit-learn 1.6.1 LogisticRegression](https://scikit-learn.org/1.6/modules/generated/sklearn.linear_model.LogisticRegression.html) | Classifier regularized, hỗ trợ sparse features | Cùng lưới C cho text/image/concat; chọn bằng validation; threshold .5 khóa |
| [VinAI PhoBERT](https://github.com/VinAIResearch/PhoBERT) | Encoder tiếng Việt; yêu cầu tách từ cho PhoBERT | Ứng viên tương lai nếu đủ dữ liệu/tài nguyên; chưa chạy, chưa thay cam kết DistilBERT hoặc gọi đã đánh giá tiếng Việt |

Trang CrisisNLP gốc bị lỗi DNS/502 trong lần truy cập này. Truy cập kho tác giả và bản phát hành QCRI thành công; URL/revision/hash tệp thực tải nằm trong `sources.json` và `image-downloads.json`. Không chuyển sang mirror không rõ nguồn. Tìm có giới hạn về nguồn tiếng Việt chưa xác minh được một bộ paired cứu hộ có common gold dùng ngay; không kết luận mọi bộ như vậy đều không tồn tại.

## Thiết kế khả thi trên CPU

`protocol.json` khóa trước download mẫu và training. Giữ Sri Lanka floods cho test, Maria cho validation, năm sự kiện còn lại cho train. Ghép lại ba split gốc để tạo split theo sự kiện mới: **không phải tái lập official split hoặc đối sánh trực tiếp leaderboard**. Chọn tối đa 3.000 train và 600 dev bằng hash, giữ toàn bộ test đủ điều kiện, không cân bằng theo nhãn. Đây là cap tài nguyên của pilot, chưa có power analysis cho hiệu ứng nhỏ hoặc tổng quát qua nhiều sự kiện.

Nối nhóm theo tweet/text trước sampling; mỗi nhóm chỉ giữ một pair. Sau tải ảnh, nối thêm SHA256 và dHash khoảng cách Hamming tối đa 4; loại mọi component xuyên split khỏi cả hai phía. DHash chỉ kiểm gần trùng heuristic, không chứng minh loại hết semantic leakage. Cần lưu cả số bị loại và phân bố lớp sau loại. Cùng test IDs được giữ cho mọi cấu hình.

Mô hình gồm majority, TF-IDF+LR trên văn bản tự do, MobileNetV3 frozen+LR, trung bình xác suất và LR trên nối hai block đặc trưng. Hai block L2 và chia căn hai; phần fusion được học bằng nhãn chung. Đây là **learned linear feature fusion**, chưa có tương tác phi tuyến hoặc fine-tuning chung hai encoder. TF-IDF là một mô hình NLP được học từ câu, khác LR trên năm cờ. Phiên bản hiện tại chỉ được đánh giá tiếng Anh.

Ba lưới C giống nhau và chỉ chọn bằng dev; mô hình frozen trước dự đoán test. Báo đủ macro-F1, accuracy, balanced accuracy, recall informative, confusion và ba hiệu so sánh fusion. CI bootstrap ghép cặp theo nhóm bản trùng, điều kiện trên **một** sự kiện test; không gọi đây là CI giữa các sự kiện độc lập. CI chưa hiệu chỉnh và phân tích thăm dò; không tuyên bố ưu thế thống kê toàn họ. Chạy mask từng block chỉ là chẩn đoán mất modality, không thay ablation huấn luyện riêng.

## Liên hệ nguyên mẫu hiện tại

`public_crisis_informativeness` khác `urgency` và `E_i`. Không nối xác suất informative vào khẩn cấp/score. CLI inference local tách task và chặn language ngoài phạm vi đã đánh giá; không sửa backend, app hoặc công thức. Việc nối `E_i` hiện có vẫn cần xác nhận ngữ nghĩa và phiên E2E riêng. C6/8 sai lệch RQ2/provenance bộ ảnh cũ không được đóng từ benchmark mới.

## Hồ sơ hoàn thành

P09: protocol/nhiệm vụ; P10: pinned intake, image/group audit và kit tiếng Việt; P11: text+image classifiers có artifacts; P12: same-test ablation/CI; P13: CLI local có giới hạn, chưa deploy; P14: tích hợp kết quả bổ trợ, ledger và kiểm báo cáo hiện tại. Trạng thái hoàn thành thực tế được ghi sau khi lệnh đã chạy, không suy từ danh sách file dự kiến.
