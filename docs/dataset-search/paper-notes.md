# Ghi chú 13 bài được đọc có mục tiêu

Mỗi mục ghi phần đã xem, khả dụng dữ liệu và hệ quả đối với RQ. Đây không phải tái lập kết quả của các bài. Bằng chứng truy cập/tệp PDF hoặc bản text đã trích có trong [paper-access.json](audit/paper-access.json); nội dung gốc được giữ ở cache ngoài repo.

## P01

**HumAID (2021).** Đã đọc §3.1–3.2, §4, phần experiments và ethical considerations. Corpus lọc trùng/gần trùng trước gán nhãn; nguồn phù hợp chọn tin nhu cầu nhưng không tái hiện đầy đủ luồng bản sao. Nhãn là humanitarian category. Audit D01 xác nhận bộ tải thiếu L/T/gold incident có cấu trúc; điều khoản trong bundle được dùng làm bằng chứng điều kiện sử dụng. [Paper](https://arxiv.org/abs/2104.03090), [dataset](https://crisisnlp.qcri.org/humaid_dataset).

## P02

**CrisisBench (2021).** Đã đọc §3 về hợp nhất, ánh xạ nhãn, loại exact/near duplicates và thiết kế chia tập. Giá trị là chuẩn hóa corpus hiện có; đổi tên corpus không tạo nguồn độc lập. Dùng để thiết kế kiểm tra giao thoa, không lấy nhãn chủ đề làm độ ưu tiên hoặc gom sự cố. Chưa audit archive CrisisBench trong đợt này. [Paper](https://arxiv.org/abs/2004.06774).

## P10

**Incident Streams 2021 off the Deep End (2022).** Đã đọc phần dataset/annotation, priority và evaluation. Nhãn phản ánh mức quan trọng thông tin đối với người tiếp nhận; loại ảnh, tác giả và khán giả cũng liên quan cách gán nhãn. D02 chỉ là bundle training 2018–2020B, không được lấy tổng quy mô trong bài làm số hàng đã audit. [Paper](https://www.dcs.gla.ac.uk/~richardm/TREC_IS/2021/TRECIS_ISCRAM_2022.pdf), [downloads](https://www.dcs.gla.ac.uk/~richardm/TREC_IS/2020/data.html).

## P11

**CrisisFACTS (ISCRAM 2023, track 2022).** Đã đọc test collection, queries, reference summaries/facts và evaluation. Bài toán là timeline/fact phục vụ nhận thức tình huống. Tệp D03 chứa gold facts, không phải bảng yêu cầu cứu hộ có gold incident. Full-stream downloader đòi thông tin tổ chức/liên hệ; chưa dùng. [Paper](https://eprints.gla.ac.uk/295806/), [repo](https://github.com/crisisfacts/utilities/tree/main/03-Evaluation/2022/01-AutoEvaluation).

## P13

**Feng và cộng sự (2022).** Đã đọc Methods, bảng dữ liệu và References. Bài mô tả nhu cầu cứu hộ Red Cross đã làm sạch, có thông tin địa điểm/nhu cầu; phân tích ở mức ZIP code. Cần bản gốc trước khử trùng để nghiên cứu duplicates. Chưa xác định tệp raw tải được trong bài/trang đã xem; không coi ba attachment bảng/hình là dữ liệu từng yêu cầu. [Paper](https://doi.org/10.32866/001c.37903).

## P14

**Wang và cộng sự (2022).** Đã đọc §3 về thu thập, lọc ZIP code/gán nhãn, thảo luận và Data Availability. Nhãn là rescue-request detection, không phải gold same-incident hay utility. Lọc ZIP có thể thiên về tin chứa địa chỉ rõ. Availability ghi “Not applicable”; trạng thái là chưa có bản dữ liệu công khai đã xác minh, không tự kết luận tác giả từ chối chia sẻ. [Paper](https://jshang2.github.io/pubs/rescue.pdf).

## P15

**VictimFinder (2022).** Đã đọc §4.1 và Data availability. Dữ liệu Harvey có nhãn yêu cầu cứu hộ; nhãn nhị phân chưa đánh giá được phân cụm hoặc xếp hạng lợi ích. Mục khả dụng ghi có thể cung cấp theo yêu cầu. Đây là đầu mối để soạn yêu cầu dữ liệu, chưa phải bộ dữ liệu nhóm đang nắm giữ. [Bản tác giả/NSF](https://par.nsf.gov/servlets/purl/10338275).

## P19

**Khallouli và cộng sự (2025).** Đã đọc §3, §4.1–4.3 và thảo luận lỗi. Có Harvey và Ian/Ida, nhưng dữ liệu theo yêu cầu; mã công khai. Tin cần cứu, tin đề nghị giúp và cập nhật đã cứu có thể khác nhau dù cùng chứa từ khóa. Cần giữ các loại này khi xây rubric và rà soát lỗi. [Paper](https://link.springer.com/article/10.1007/s13278-025-01462-7), [code](https://github.com/waelGH/rescue_tweets_detection).

## P22

**Hu và Wang (GIScience 2021).** Đã đọc §3 Dataset, annotation/location-description taxonomy và thảo luận geoparsing. Địa điểm được nói trong nội dung và nơi người đăng không đồng nhất; nhiều mô tả là đường, giao lộ hoặc vùng. Đây là cơ sở cho kiểm tra ngữ nghĩa L, chưa có gold sự cố. Là phiên bản sớm có quan hệ với P23, không tính như nguồn xác nhận độc lập. [Paper](https://drops.dagstuhl.de/opus/volltexte/2020/13041/pdf/LIPIcs-GIScience-2021-I-6.pdf).

## P23

**Sun, Hu và Joseph (2026).** Đã đọc Methods, Data Records, Technical Validation và Data availability. Dataset cung cấp footprint/topic; cần kiểm tra footprint là địa điểm nạn nhân hay ngữ cảnh. D04 audit đúng một batch St Louis; full tweet không nằm trong tệp đã đọc. Năm bài theo bản xuất bản là 2026, dù README còn ghi 2025. [Paper](https://doi.org/10.1038/s41597-026-07506-7), [data v2](https://doi.org/10.6084/m9.figshare.31044040.v2).

## P24

**CrisisTS (ACL 2025).** Đã đọc §3.1–3.3 và thiết lập đánh giá ngoài sự kiện. Nhánh tiếng Anh chuyển humanitarian labels sang urgency; đó là nhãn suy ra từ phân loại chủ đề, chưa phải đánh giá lợi ích độc lập. Liên kết khí tượng khi thiếu địa điểm cần xem như phép suy ra, không là tọa độ cứu hộ quan sát. Chỉ kiểm tra listing kho, chưa audit các bảng dữ liệu. [Paper](https://aclanthology.org/2025.acl-long.783/), [data](https://huggingface.co/datasets/Unknees/CrisisTS).

## P27

**Liang và cộng sự (2025).** Đã đọc Case study, Data collection and preprocessing, thiết lập nguồn lực và Data availability. Tình huống Shenzhen kết hợp mạng đường với các giả định nhu cầu/di chuyển và mô hình phân bổ. Có ích thiết kế sensitivity cho RQ3; không xem nghiệm tối ưu trong mô hình là kết quả quan sát của một chiến dịch cứu hộ. [Paper](https://doi.org/10.1038/s41598-025-06374-2).

## P28

**Morales và cộng sự (2026).** Đã đọc §3–4, cách lọc/chia dữ liệu và Data availability. Dữ liệu cuộc gọi là nguồn tác động thực nhưng không công khai; các dữ liệu khí tượng mở không khắc phục thiếu cuộc gọi gốc. Bài dự đoán cuộc gọi, không có đầy đủ gold báo cáo trùng hay kết quả dispatch cho RQ3. [Paper](https://nhess.copernicus.org/articles/26/3943/2026/nhess-26-3943-2026.html).

## Bằng chứng bổ sung về IDRISI-D

P26 được sàng lọc từ paper định nghĩa LMD và kiểm tra trực tiếp [README LMD](https://github.com/rsuwaileh/IDRISI/tree/main/LMD), schema và tệp train/dev. Đợt này profile chính thức chỉ tính train Harvey, không gộp 58 hàng dev vào số 360. Tệp dùng `humAID_class`, khác tên `info_class` trong README. Official test không phát hành; partition công khai không được gọi là test chưa từng được dùng. Các trường location/confidence không tự xác nhận vị trí cần cứu hoặc Q của bài hiện tại.
