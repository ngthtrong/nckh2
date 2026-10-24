# Báo cáo kiểm chứng tài liệu tham khảo

Ngày kiểm tra: **24/10/2026** (Asia/Saigon).

## 1. Phạm vi và cách kiểm tra

Kiểm tra danh mục của báo cáo chính tại `main.tex`, theo cấu hình `template/bibliography.tex`: `bibliography/legal.bib`, `bibliography/books.bib`, `bibliography/articles.bib`, `bibliography/references.bib`. Hiện cả **19 mục** đều nằm trong `bibliography/articles.bib`; ba cơ sở dữ liệu còn lại chỉ có chú thích.

Không đưa `template/smoke.bib` vào thống kê vì đây là dữ liệu thử typography, không phải danh mục của `main.tex`. Không kiểm tra danh mục riêng của `../paper/` và `../reportTemplate/`.

Phương pháp: đối chiếu tiêu đề, tác giả, năm, nơi công bố, tập/số/trang, DOI và URL với bài gốc, nhà xuất bản, kho tác giả, RFC Editor hoặc cơ quan cung cấp dữ liệu. Quét các lệnh `cite` trong nguồn LaTeX để xác định việc sử dụng. Các đường dẫn file bên dưới tính từ thư mục `report/`; số dòng là vị trí tại thời điểm kiểm tra. Các liên kết web được đặt ngay tại từng mục.

**“Có thật” chỉ xác nhận tìm được tài liệu tương ứng**, không chứng minh mọi kết quả trong tài liệu đúng hoặc mọi diễn giải của báo cáo đều được tài liệu hỗ trợ. Không dùng lỗi truy cập hoặc việc không có kết quả tìm kiếm làm bằng chứng tài liệu giả.

## 2. Kết luận tổng hợp

| Kết quả                                         |  Số lượng | Ghi chú                                               |
| ----------------------------------------------- | --------: | ----------------------------------------------------- |
| Xác nhận tài liệu tồn tại                       | **18/19** | Có nguồn gốc đối chiếu; mức đầy đủ metadata khác nhau |
| Chưa xác minh được                              |  **1/19** | `nguyen2026floodartifact`, DOI Zenodo                 |
| Khóa được dùng trong nội dung đã quét           | **18/19** | Gồm cả mục Zenodo chưa xác minh                       |
| Khóa chưa thấy được trích dẫn                   |  **1/19** | `whoIITT`                                             |
| Khóa trích dẫn không có trong bốn file danh mục |     **0** | Trong phạm vi nguồn LaTeX đã quét                     |

**Chưa đủ cơ sở kết luận danh mục có tài liệu bịa đặt.** Điểm cần xử lý trước tiên là xác minh bản công khai của artifact Zenodo, sau đó bổ sung định danh và chuẩn hóa cách ghi WorldPop, MobileNetV3. WHO IITT có thật nhưng chưa thấy được sử dụng trong phần nội dung đã quét.

## 3. Kết quả chi tiết từng tài liệu

### 01. `doan2025sar` — Có thật; thông tin chính khớp

- **Trong danh mục:** Thanh-Nghi Doan, Duc-Ngoc Le-Thi, “A Novel Deep Learning Model for Flood Detection from Synthetic Aperture Radar Images”, Journal of Advances in Information Technology, 16(1), 57–70, 2025. DOI `10.12720/jait.16.1.57-70`.
- **Bằng chứng:** PDF chính thức ghi đúng hai tác giả, tiêu đề, tạp chí và DOI; ngày công bố 09/01/2025. Bài dùng cặp ảnh SAR, kiến trúc Siamese và Swin-Transformer, phù hợp mô tả khái quát trong báo cáo.
- **Nguồn:** [PDF chính thức JAIT](https://www.jait.us/articles/2025/JAIT-V16N1-57.pdf), [DOI](https://doi.org/10.12720/jait.16.1.57-70).
- **Vị trí:** `bibliography/articles.bib:3`; trích tại `chapters/01-foundations/sections/related-work.tex:3` và `:15`.
- **Đề nghị:** Giữ thông tin hiện có.

### 02. `ngo2025urban` — Có thật; thông tin chính khớp

- **Trong danh mục:** Ngô Thanh Vũ và chín đồng tác giả, “Ứng dụng xử lý ảnh biển báo giao thông trong quan trắc ngập lụt đô thị”, Tạp chí Khoa học và Công nghệ – Đại học Đà Nẵng, 23(5A), 116–121, 2025. DOI `10.31130/ud-jst.2025.067`.
- **Bằng chứng:** PDF chính thức có tiêu đề tiếng Việt/Anh, đủ mười tác giả, DOI, trang đầu 116; bài dài sáu trang. Nội dung nghiên cứu YOLOv11 và ảnh biển báo phục vụ quan trắc ngập. Trang bài báo được tìm thấy nhưng khi mở trực tiếp có timeout; PDF vẫn đọc được.
- **Nguồn:** [Trang bài báo](https://jst-ud.vn/jst-ud/article/view/9674), [PDF chính thức](https://jst-ud.vn/jst-ud/article/download/9674/6473), [DOI](https://doi.org/10.31130/ud-jst.2025.067).
- **Vị trí:** `bibliography/articles.bib:12`; trích tại `chapters/01-foundations/sections/related-work.tex:5` và `:16`.
- **Đề nghị:** Giữ thông tin chính; có thể dùng trang bài báo làm URL chính và PDF làm liên kết đọc toàn văn.

### 03. `rfc9171` — Có thật; thông tin chính khớp

- **Trong danh mục:** Scott Burleigh, Kevin Fall, Edward Birrane, “Bundle Protocol Version 7”, RFC 9171, 2022.
- **Bằng chứng:** RFC Editor ghi RFC 9171, Standards Track, tháng 01/2022, tác giả S. Burleigh, K. Fall, E. Birrane III. Tài liệu mô tả BPv7 cho mạng gián đoạn; sự tồn tại của chuẩn không chứng minh sản phẩm đã triển khai BPv7.
- **Nguồn:** [Toàn văn RFC 9171](https://www.rfc-editor.org/rfc/rfc9171.html).
- **Vị trí:** `bibliography/articles.bib:21`; trích tại `chapters/01-foundations/sections/related-work.tex:21` và `:27`.
- **Đề nghị:** Có thể bổ sung hậu tố “III” cho Birrane theo bản chính thức.

### 04. `onnxQuantization` — Có thật; cần lưu ý tài liệu web thay đổi

- **Trong danh mục:** ONNX Runtime, “Quantize ONNX models”, không có năm, ghi truy cập 06/10/2026.
- **Bằng chứng:** Đọc được tài liệu chính thức cùng tiêu đề, trình bày lượng tử hóa mô hình và việc phân tích sai lệch độ chính xác.
- **Nguồn:** [ONNX Runtime – Quantize ONNX models](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html).
- **Vị trí:** `bibliography/articles.bib:27`; trích tại `chapters/02-data-methods/sections/image-design.tex:95`.
- **Đề nghị:** Giữ URL; nếu cần tái lập chính xác hướng dẫn đã dùng, ghi thêm phiên bản ONNX Runtime hoặc revision tài liệu. Lần kiểm tra này không xác nhận được lịch sử truy cập 06/10/2026.

### 05. `guo2017calibration` — Có thật; metadata khớp

- **Trong danh mục:** Chuan Guo, Geoff Pleiss, Yu Sun, Kilian Q. Weinberger, “On Calibration of Modern Neural Networks”, ICML/PMLR 70, 1321–1330, 2017.
- **Bằng chứng:** Trang PMLR cung cấp đầy đủ tác giả và BibTeX khớp tên bài, hội nghị, tập, trang, năm. Nội dung có khảo sát temperature scaling.
- **Nguồn:** [Trang chính thức PMLR](https://proceedings.mlr.press/v70/guo17a.html).
- **Vị trí:** `bibliography/articles.bib:33`; trích tại `chapters/04-evaluation/sections/results.tex:41`.
- **Đề nghị:** Giữ nguyên; URL PMLR đủ định danh.

### 06. `blondel2008louvain` — Có thật; thiếu DOI/URL trong danh mục

- **Trong danh mục:** Vincent D. Blondel, Jean-Loup Guillaume, Renaud Lambiotte, Etienne Lefebvre, “Fast unfolding of communities in large networks”, Journal of Statistical Mechanics: Theory and Experiment, 2008(10), P10008, 2008.
- **Bằng chứng:** Bản tác giả trên arXiv ghi đúng bốn tác giả, năm, journal reference P10008 và DOI của bản tạp chí. P10008 là mã bài, không phải khoảng trang.
- **Nguồn:** [Bản tác giả arXiv:0803.0476](https://arxiv.org/abs/0803.0476), [DOI bản xuất bản](https://doi.org/10.1088/1742-5468/2008/10/P10008).
- **Vị trí:** `bibliography/articles.bib:41`; trích tại `chapters/introduction.tex:13`, `chapters/01-foundations/sections/background.tex:24`, `related-work.tex:20` cùng thư mục sections.
- **Đề nghị:** Bổ sung DOI `10.1088/1742-5468/2008/10/P10008` và URL.

### 07. `traag2019leiden` — Có thật; thiếu DOI/URL trong danh mục

- **Trong danh mục:** Vincent A. Traag, Ludo Waltman, Nees Jan van Eck, “From Louvain to Leiden: guaranteeing well-connected communities”, Scientific Reports, 9, 5233, 2019.
- **Bằng chứng:** Nature có trang bài chính thức, công bố 26/03/2019, tập 9, **article number 5233**. Danh mục hiện dùng `pages={5233}`; số này là mã bài.
- **Nguồn:** [Scientific Reports – bài Leiden](https://www.nature.com/articles/s41598-019-41695-z), [DOI](https://doi.org/10.1038/s41598-019-41695-z).
- **Vị trí:** `bibliography/articles.bib:53`; trích tại `chapters/introduction.tex:13`, `chapters/01-foundations/sections/background.tex:24`, `related-work.tex:20` cùng thư mục sections.
- **Đề nghị:** Thêm DOI/URL; biểu diễn 5233 là mã bài nếu style hỗ trợ, tránh diễn giải thành trang 5233.

### 08. `ester1996dbscan` — Có thật; thiếu URL trong danh mục

- **Trong danh mục:** Martin Ester, Hans-Peter Kriegel, Jörg Sander, Xiaowei Xu, “A density-based algorithm for discovering clusters in large spatial databases with noise”, KDD 1996, 226–231.
- **Bằng chứng:** Đọc được bài gốc sáu trang trong kho AAAI; tiêu đề, bốn tác giả và thuật toán DBSCAN khớp. OCR trong PDF có thể hiển thị sai dấu trong tên Jörg, không phải bằng chứng tác giả khác.
- **Nguồn:** [PDF gốc trong kho AAAI](https://cdn.aaai.org/KDD/1996/KDD96-037.pdf).
- **Vị trí:** `bibliography/articles.bib:65`; trích tại `chapters/introduction.tex:13`, `chapters/01-foundations/sections/background.tex:26`.
- **Đề nghị:** Bổ sung URL bản gốc; không tự gán DOI khi chưa có nguồn xác nhận.

### 09. `alam2018crisismmd` — Có thật; thiếu DOI/URL và số phát hành

- **Trong danh mục:** Firoj Alam, Ferda Ofli, Muhammad Imran, “CrisisMMD: Multimodal Twitter datasets from natural disasters”, ICWSM, tập 12, 2018.
- **Bằng chứng:** Trang AAAI xác nhận ba tác giả, ngày 15/06/2018, tập 12 số 1 và DOI `10.1609/icwsm.v12i1.14983`.
- **Nguồn:** [Trang xuất bản AAAI](https://ojs.aaai.org/index.php/ICWSM/article/view/14983), [DOI](https://doi.org/10.1609/icwsm.v12i1.14983), [Bản tác giả arXiv](https://arxiv.org/abs/1805.00713).
- **Vị trí:** `bibliography/articles.bib:74`; trích tại `chapters/introduction.tex:9`, `chapters/01-foundations/sections/related-work.tex:17`.
- **Đề nghị:** Bổ sung DOI, URL và `number={1}`. Việc bài tồn tại không xác nhận dữ liệu CrisisMMD đã được dùng huấn luyện trong đề tài.

### 10. `rahnemoonfar2021floodnet` — Có thật; metadata chính khớp

- **Trong danh mục:** Maryam Rahnemoonfar và năm đồng tác giả, “FloodNet: A high resolution aerial imagery dataset for post flood scene understanding”, IEEE Access 9, 89644–89654, 2021.
- **Bằng chứng:** Bản tác giả có đúng tiêu đề và sáu tác giả. Hồ sơ công bố của Oak Ridge National Laboratory xác nhận IEEE Access 9, 89644–89654, 2021 và DOI. Bản arXiv nộp năm 2020 không làm cho năm xuất bản 2021 của bài tạp chí bị sai.
- **Nguồn:** [Bản tác giả arXiv:2012.02951](https://arxiv.org/abs/2012.02951), [Hồ sơ công bố ORNL](https://impact.ornl.gov/en/publications/floodnet-a-high-resolution-aerial-imagery-dataset-for-post-flood-/), [DOI](https://doi.org/10.1109/ACCESS.2021.3090981).
- **Vị trí:** `bibliography/articles.bib:83`; trích tại `chapters/introduction.tex:9`, `chapters/01-foundations/sections/related-work.tex:18`.
- **Đề nghị:** Bổ sung DOI `10.1109/ACCESS.2021.3090981` và URL.

### 11. `sakaki2010earthquake` — Có thật; thiếu DOI/URL trong danh mục

- **Trong danh mục:** Takeshi Sakaki, Makoto Okazaki, Yutaka Matsuo, “Earthquake shakes Twitter users: real-time event detection by social sensors”, WWW 2010, 851–860.
- **Bằng chứng:** Tìm được toàn văn bài trong kho hội nghị IW3C2 và kỷ yếu WWW 2010. Tiêu đề, tác giả, năm và chủ đề phát hiện sự kiện khớp. Trang ACM trả 403 trong lượt kiểm tra, nên không coi đó là nguồn toàn văn đã đọc.
- **Nguồn:** [Bài gốc trong kho IW3C2](https://www.iw3c2.org/papers/2022-Earthquake.pdf), [Bản kỷ yếu WWW 2010 tại ETH](https://www.ra.ethz.ch/cdstore/www2010/www/p851.pdf), [DOI/ACM](https://doi.org/10.1145/1772690.1772777).
- **Vị trí:** `bibliography/articles.bib:94`; trích tại `chapters/introduction.tex:9`.
- **Đề nghị:** Bổ sung DOI `10.1145/1772690.1772777` và URL. Tên file `2022-Earthquake.pdf` trong kho không phải năm xuất bản; nội dung bài ghi WWW 2010.

### 12. `gralla2014review` — Có thật; metadata khớp

- **Trong danh mục:** Erica Gralla, Jarrod Goentzel, Charles Fine, “Assessing trade-offs among multiple objectives for humanitarian aid delivery using expert preferences”, Production and Operations Management 23(6), 978–989, 2014. DOI `10.1111/poms.12110`.
- **Bằng chứng:** Trang nhà xuất bản Wiley có đúng ba tác giả, tập 23 số 6, tháng 06/2014, trang 978–989 và DOI. Đây là nghiên cứu về ưu tiên chuyên gia, không phải bài tổng quan chỉ vì khóa nội bộ có hậu tố `review`.
- **Nguồn:** [Trang xuất bản Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/poms.12110), [DOI](https://doi.org/10.1111/poms.12110).
- **Vị trí:** `bibliography/articles.bib:103`; trích tại `chapters/introduction.tex:15`, `chapters/01-foundations/sections/background.tex:34`.
- **Đề nghị:** Giữ metadata hiện tại; có thể thêm URL. Không cần đổi khóa chỉ vì tên khóa chưa mô tả chính xác loại nghiên cứu.

### 13. `tomasi1998bilateral` — Có thật; thiếu DOI/URL trong danh mục

- **Trong danh mục:** Carlo Tomasi, Roberto Manduchi, “Bilateral filtering for gray and color images”, ICCV 1998, 839–846.
- **Bằng chứng:** Đọc được bản bài gốc lưu tại Johns Hopkins, ghi hai tác giả và hội nghị IEEE Computer Vision 1998 tại Bombay. DOI dẫn tới IEEE document 710815; trang IEEE yêu cầu JavaScript/chống bot nên chưa đọc được metadata đầy đủ ở đó.
- **Nguồn:** [PDF bài gốc tại JHU](https://www.cs.jhu.edu/~misha/ReadingSeminar/Papers/Tomasi98.pdf), [Trang phòng thí nghiệm của đồng tác giả tại UCSC](https://vision.soe.ucsc.edu/taxonomy/term/52), [DOI](https://doi.org/10.1109/ICCV.1998.710815).
- **Vị trí:** `bibliography/articles.bib:116`; trích tại `chapters/02-data-methods/sections/methods.tex:57`.
- **Đề nghị:** Thêm DOI/URL. Bài là nguồn về bilateral filtering; không tự chứng minh công thức phân cụm cứu hộ của nhóm đã được kiểm chứng.

### 14. `copernicusEMSR848` — Có thật; trang động hạn chế khả năng đọc

- **Trong danh mục:** Copernicus Emergency Management Service, “EMSR848: Flood in Central Viet Nam”, 2025.
- **Bằng chứng:** Chỉ mục chính thức của Copernicus hiển thị “EMSR848 – Flood in central Viet Nam”, ngày 30/10/2025. Khi mở URL activation, công cụ chỉ trích xuất được khung trang; nội dung chỉ mục chính thức giúp đối chiếu mã, địa danh và năm.
- **Nguồn:** [Hồ sơ activation EMSR848](https://mapping.emergency.copernicus.eu/activations/EMSR848/), [Chỉ mục chính thức có EMSR848](https://mapping.emergency.copernicus.eu/search/?category=1&q=2025&sort=relevance&type=activations).
- **Vị trí:** `bibliography/articles.bib:126`; trích tại `chapters/02-data-methods/sections/data.tex:48`.
- **Đề nghị:** Giữ mã activation và URL. Chưa xác minh bản đồ cụ thể, AOI, phiên bản hoặc tệp mà đề tài thực sự đã sử dụng. Ngày truy cập 08/09/2026 trong danh mục là ghi nhận sẵn có, không được xác nhận độc lập ở lần này.

### 15. `worldpop2025vietnam` — Có thật; cách ghi hiện tại rút gọn metadata

- **Trong danh mục:** WorldPop, “2025 Constrained Estimates of Total Number of People per Grid Square for Viet Nam”, 2025; DOI `10.5258/SOTON/WP00803`; R2024B version 1, khoảng 100 m.
- **Bằng chứng:** Hồ sơ WorldPop **id=56514** ghi Viet Nam, constrained estimates cho năm 2025, 3 arc giây, cùng DOI. Trích dẫn khuyến nghị của WorldPop dùng danh sách tác giả Bondarenko và cộng sự cùng tên bộ dữ liệu bao phủ **2015–2030**, R2024B v1. DOI là định danh bộ dữ liệu rộng hơn, không riêng lát cắt Việt Nam 2025.
- **Nguồn:** [Hồ sơ đúng Việt Nam 2025 – id 56514](https://hub.worldpop.org/geodata/summary?id=56514), [DOI bộ dữ liệu](https://doi.org/10.5258/SOTON/WP00803).
- **Vị trí:** `bibliography/articles.bib:135`; trích tại `chapters/02-data-methods/sections/data.tex:48`.
- **Đề nghị:** Dùng citation khuyến nghị của WorldPop, thêm URL hồ sơ quốc gia/năm. Phân biệt năm 2025 trong citation, năm dân số 2025 và ngày sản xuất 01/12/2024. Không dùng [id 56509](https://hub.worldpop.org/geodata/summary?id=56509) thay thế: hồ sơ đó là dân số Việt Nam **2020**. Chưa đối chiếu tệp raster dự án với nguồn tải.

### 16. `nguyen2026floodartifact` — Chưa xác minh được công bố công khai

- **Trong danh mục:** Thanh-Trong Nguyen, Ngoc-Anh Le, Nhu-Quynh Nguyen, Tuong-Hung Cao, Hung-Thinh Ngo, Thanh-Khoa Nguyen, “Research Artifact for Stress-Testing Product-Gated Clustering and Bounded Priority Ranking for Flood-Rescue Reports”, Zenodo, 2026; ghi version 1.0.1 và concept DOI `10.5281/zenodo.21934401`.
- **Kết quả:** Không lấy được metadata của bản ghi qua DOI, trang Zenodo, Zenodo API và DataCite API bằng công cụ web. Tìm theo DOI/tiêu đề chưa thu được bản ghi khớp. Thử truy cập API từ môi trường shell bị lỗi phân giải DNS; đây là giới hạn kết nối, không phải phản hồi 404 của Zenodo/DataCite.
- **Liên kết đã thử, chưa xác nhận truy cập được:** [DOI trong danh mục](https://doi.org/10.5281/zenodo.21934401), [Zenodo record](https://zenodo.org/records/21934401), [Zenodo API](https://zenodo.org/api/records/21934401), [DataCite API](https://api.datacite.org/dois/10.5281/zenodo.21934401).
- **Vị trí:** `bibliography/articles.bib:145`; được viện dẫn tại `appendices/reproducibility.tex:10` để hỗ trợ khả năng kiểm chứng độc lập.
- **Chưa xác nhận:** bản ghi đã publish hay chỉ draft/reserved DOI; tác giả; tiêu đề; năm; license; version 1.0.1; DOI này có thật sự là concept DOI; nội dung và tệp đính kèm.
- **Đề nghị ưu tiên:** Mở bản ghi trong trình duyệt, kiểm tra trạng thái công khai và tải citation do Zenodo xuất. Nếu đã công khai, ghi DOI **phiên bản cụ thể** cho kết quả cần tái lập; concept DOI có thể trỏ sang phiên bản mới. Nếu chưa công khai, cần mô tả đúng trạng thái và điều chỉnh khẳng định về khả năng kiểm chứng độc lập. **Chưa có đủ bằng chứng để gọi tài liệu này là giả hoặc không tồn tại.**

### 17. `howard2019mobilenetv3` — Có thật; nên trích bản hội nghị đầy đủ

- **Trong danh mục:** Andrew Howard và 11 đồng tác giả, “Searching for MobileNetV3”, 2019; loại `misc`, URL arXiv, note ICCV 2019.
- **Bằng chứng:** arXiv:1905.02244 ghi đúng 12 tác giả và tiêu đề, nộp 06/05/2019, bản sửa cuối 20/11/2019, ghi ICCV 2019.
- **Nguồn:** [Bản tác giả arXiv:1905.02244](https://arxiv.org/abs/1905.02244).
- **Vị trí:** `bibliography/articles.bib:156`; trích tại `chapters/introduction.tex:11`, `chapters/01-foundations/sections/background.tex:12`, `related-work.tex:19` cùng thư mục sections, `chapters/02-data-methods/sections/image-design.tex:12`.
- **Đề nghị:** Cách trích arXiv hiện tại vẫn định danh được tài liệu. Có thể chuẩn hóa thành bài hội nghị sau khi lấy citation chính thức ICCV; không trộn DOI arXiv với metadata bản hội nghị mà không phân biệt phiên bản.

### 18. `whoIITT` — Có thật; chưa thấy được trích dẫn trong nội dung

- **Trong danh mục:** World Health Organization, “Interagency Integrated Triage Tool”, URL WHO; không có năm; note ngày đối chiếu 06/10/2026.
- **Bằng chứng:** Trang chính thức WHO có đúng tên công cụ, nêu hợp tác WHO/ICRC/MSF và phạm vi phân loại tại cơ sở cấp cứu. Đây không phải bằng chứng trực tiếp hợp thức hóa thuật toán ưu tiên cứu hộ ngoài hiện trường.
- **Nguồn:** [WHO – Interagency Integrated Triage Tool](https://www.who.int/tools/triage).
- **Vị trí:** `bibliography/articles.bib:162`; không thấy khóa `whoIITT` trong các lệnh trích dẫn của nội dung đã quét.
- **Đề nghị:** Kiểm tra có thực sự cần tham chiếu hay không; chỉ bổ sung trích dẫn tại đoạn sử dụng công cụ nếu có nội dung tương ứng. Với cấu hình hiện tại và không có `nocite` trong nguồn đã quét, mục này thường không xuất hiện trong danh mục in ra; cần build để xác nhận. Không tự gán năm công bố hoặc coi ngày truy cập cũ là đã được xác nhận.

### 19. `rfc8785` — Có thật; thông tin chính khớp

- **Trong danh mục:** Anders Rundgren, Bradley Jordan, Samuel Erdtman, “JSON Canonicalization Scheme (JCS)”, RFC 8785, 2020.
- **Bằng chứng:** RFC Editor xác nhận RFC 8785, tháng 06/2020, ba tác giả tương ứng, loại **Informational**. Không nên mô tả tài liệu này là IETF Standards Track.
- **Nguồn:** [Trang thông tin RFC 8785](https://www.rfc-editor.org/info/rfc8785/), [Toàn văn RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.txt).
- **Vị trí:** `bibliography/articles.bib:168`; trích tại `chapters/03-system/sections/architecture.tex:50` và `synchronization.tex:39` cùng thư mục.
- **Đề nghị:** Giữ thông tin hiện có; khi mô tả loại chuẩn, ghi đúng Informational. Việc trích RFC không chứng minh hai triển khai Dart/Python đã tạo cùng byte; việc đó cần kiểm thử riêng.

## 4. Các việc nên xử lý theo thứ tự

1. **Xác minh Zenodo:** cần bản ghi công khai, citation xuất từ Zenodo và DOI phiên bản 1.0.1 nếu viện dẫn đúng phiên bản đó. Đây là mục duy nhất chưa xác nhận tồn tại công khai trong lượt kiểm tra.
2. **Chuẩn hóa WorldPop:** dùng tác giả/tên bộ dữ liệu theo nguồn, ghi rõ lát cắt Việt Nam 2025 và thêm URL id 56514. Metadata hiện tại là tên mô tả rút gọn, không phải bằng chứng nguồn giả.
3. **Thêm định danh:** Louvain, Leiden, CrisisMMD, FloodNet, Sakaki, bilateral filtering cần DOI/URL như ghi trên; DBSCAN thêm URL bài gốc.
4. **Kiểm tra nhu cầu trích WHO IITT:** hiện có trong cơ sở dữ liệu nhưng chưa có trích dẫn trong nội dung đã quét.
5. **Chuẩn hóa loại tài liệu nếu cần:** MobileNetV3 có thể dùng citation hội nghị; RFC 8785 là Informational; 5233/P10008 là mã bài. Các việc này thuộc chất lượng metadata, không phải bằng chứng tài liệu không tồn tại.

## 5. Giới hạn và bằng chứng bàn giao

- Chỉ tạo báo cáo `reference.md`; không chỉnh `.bib`, `.tex`, không xóa file và không thay nội dung nghiên cứu.
- Đã đọc cấu hình danh mục, kiểm kê đủ 19 khóa, quét trích dẫn trong `chapters/`, `appendices/`, `frontmatter/`, `deliverables/`; kết quả 18 khóa được dùng, không có khóa thiếu định nghĩa. Có đối chiếu tìm kiếm `cite`/`nocite` trong cây nguồn `.tex`.
- Chưa biên dịch LaTeX để xác nhận số thứ tự, cách hiển thị URL/DOI và danh mục cuối trong PDF. Kiểm tra văn bản nguồn không thay thế kiểm tra PDF đã build.
- Một số bằng chứng web đến từ nội dung công khai được công cụ tìm kiếm lập chỉ mục; không phải mọi URL đều được đọc trực tiếp thành công. Mỗi hạn chế đáng kể đã được ghi tại mục tương ứng.
- Chưa xác minh lịch sử các ngày truy cập ghi sẵn trong `.bib`, trạng thái rút bài/đính chính toàn diện, tính đúng của toàn bộ kết quả khoa học, hay nguồn gốc thực tế của các tệp dữ liệu/artifact được dự án sử dụng.
- Các tài liệu hướng dẫn cũ `docs/PROJECT_STATUS.md`, `docs/DELIVERY_PLAN.md` được AGENTS.md dẫn tới hiện không tồn tại ở vị trí đó; việc kiểm tra này dùng nguồn báo cáo hiện có.

**Kết luận bàn giao:** 18 tài liệu đã có bằng chứng tồn tại; 1 mục Zenodo còn cần xác minh. Báo cáo ghi nhận vấn đề và đề nghị xử lý, chưa áp dụng thay đổi vào danh mục gốc.
