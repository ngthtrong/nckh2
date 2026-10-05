# Tổng hợp hướng dẫn báo cáo và định hướng cấu trúc LaTeX

Ngày phân tích: 05/10/2026. Phạm vi: toàn bộ sáu tệp trong `report/guideline/`.

Tài liệu này làm cơ sở thiết kế dự án LaTeX và kiểm tra hồ sơ báo cáo tổng kết NCKH sinh viên. **Chưa phải bộ khung LaTeX đã triển khai.** Các yêu cầu được dẫn từ tài liệu trong repository; chưa xác minh với cơ quan quản lý về thay đổi quy định sau khi các mẫu này được ban hành.

## 1. Nguồn và cách đọc

| Ký hiệu | Nguồn | Vai trò |
|---|---|---|
| HT | [HinhThucBC.pdf](guideline/HinhThucBC.pdf), [bản Word](guideline/HinhThucBC.doc) | Quy định hình thức, trình tự nội dung, cách lập tài liệu tham khảo |
| HD | [HD.pdf](guideline/HD.pdf), [bản Word](guideline/HD.doc) | Quy trình nghiệm thu, hồ sơ nộp, chữ ký, minh chứng, sản phẩm riêng |
| B | [Bìa.pdf](guideline/Bìa.pdf), [bản Word](guideline/Bìa.doc) | Mẫu bìa chính và bìa phụ |

Đã trích xuất nội dung cả PDF và phần văn bản chính trong Word; không phát hiện khác biệt nội dung yêu cầu đáng kể giữa từng cặp. Đã xem trực quan hai trang bìa và trang logo để nhận diện bố cục không thể hiện đầy đủ qua văn bản trích xuất.

- HT trang 1 chứa quy định; trang 2 là logo; trang 3 không có nội dung hướng dẫn hiển thị.
- HD trang 1–2 quy định hồ sơ; trang 3 quy định video; trang 4 là ghi chú hồ sơ thanh toán, có yêu cầu bỏ ghi chú trước khi in.
- B trang 1 là bìa chính; trang 2 là bìa phụ.

Trong tài liệu này, **bắt buộc** là yêu cầu được nêu trực tiếp trong nguồn. **Đề xuất** là lựa chọn thiết kế hoặc cách viết để đáp ứng yêu cầu; không được coi là quy định của trường. Số trang dẫn nguồn là vị trí trang trong PDF.

## 2. Các yêu cầu hình thức bắt buộc

Nguồn: HT trang 1, mục 1 và 2.

| Hạng mục | Yêu cầu | Hệ quả đối với LaTeX |
|---|---|---|
| Loại tài liệu | Báo cáo tổng kết phản ánh đầy đủ nội dung, kết quả thực hiện; đóng thành quyển | Thiết kế tài liệu dài, nhiều chương và hồ sơ đính kèm |
| Giấy | A4, 210 × 297 mm | Cấu hình kích thước giấy cho cả nội dung và bản xuất cuối |
| Độ dài | Ít nhất 50 trang, không tính mục lục, tài liệu tham khảo và phụ lục | Theo dõi riêng số trang nội dung; không dùng trang minh chứng để bù thiếu nội dung |
| Phông chữ | Nguồn ghi “Time New Roman”, hiểu là Times New Roman | Dùng phông Times New Roman thật cho bản nộp; kiểm tra đủ dấu tiếng Việt |
| Cỡ chữ | 13 | Cấu hình rõ cỡ thân bài; không dùng mặc định 12 của lớp tài liệu |
| Giãn dòng | 1,3–1,5 dòng | Chọn một mức trong khoảng và kiểm tra trên PDF |
| Lề | Trái 3 cm; trên, dưới, phải 2 cm | Tập trung cấu hình lề; kiểm tra riêng chế độ in hai mặt |

**Điểm cần diễn giải khi triển khai:** HT không nói rõ bìa, các danh mục ngoài mục lục và biểu mẫu đầu quyển có được tính vào 50 trang hay không. Đề xuất đặt mục tiêu **ít nhất 50 trang từ Mở đầu đến hết Kết luận và kiến nghị**, không tính trang trắng, để đáp ứng yêu cầu mà không phụ thuộc cách tính phần đầu. Đây là cách kiểm soát nội bộ, không phải câu chữ của quy định.

Cỡ chữ và giãn dòng trong Word không ánh xạ hoàn toàn sang thiết lập mặc định LaTeX. Word dùng point 1/72 inch, còn `pt` truyền thống của TeX là 1/72,27 inch; khi cần khớp cỡ Word nên cấu hình và kiểm tra theo `bp`. Hệ số giãn dòng cần được đối chiếu bằng bản xuất, vì `setspace` và chiều cao dòng của phông có thể cho kết quả khác Word.

## 3. Trình tự toàn bộ quyển báo cáo

Nguồn: HT trang 1, mục 3.1–3.17. Phải giữ thứ tự các khối sau; cách chia tệp bên trong là lựa chọn kỹ thuật.

| Thứ tự | Khối nội dung | Ghi chú |
|---|---|---|
| 1 | Trang bìa | Theo B trang 1 |
| 2 | Trang bìa phụ | Theo B trang 2 |
| 3 | Danh sách thành viên nghiên cứu và đơn vị phối hợp chính | Không gộp mất thông tin này vào bìa phụ |
| 4 | Mục lục | Sinh tự động |
| 5 | Danh mục bảng biểu, hình ảnh | Có thể tách danh mục bảng và danh mục hình trong cùng vị trí này |
| 6 | Danh mục từ viết tắt | Xếp theo thứ tự bảng chữ cái |
| 7 | Thông tin kết quả nghiên cứu tiếng Việt | Theo mẫu; có nhận xét và chữ ký theo HD |
| 8 | Thông tin kết quả nghiên cứu tiếng Anh | Theo mẫu |
| 9 | Thông tin sinh viên chủ nhiệm | Theo mẫu; có chữ ký theo HD |
| 10 | Mở đầu | Chứa đầy đủ các nội dung tại mục 4 bên dưới |
| 11 | Kết quả nghiên cứu và phân tích, bàn luận | Trình bày thành chương 1, 2, 3, … |
| 12 | Kết luận và kiến nghị | Có cả kết luận và kiến nghị |
| 13 | Tài liệu tham khảo | Phân loại và sắp xếp theo yêu cầu tại mục 5 |
| 14 | Phụ lục khoa học, nếu có | Bảng, sơ đồ, hình vẽ, tư liệu bổ trợ |
| 15 | Thuyết minh đã phê duyệt | Bản scan/copy có ký tên, đóng dấu |
| 16 | Minh chứng sản phẩm đăng ký thuộc nhóm I, II, III | Đối chiếu trực tiếp thuyết minh đã duyệt |
| 17 | Minh chứng sản phẩm nhóm IV | Bản tin Việt/Anh, báo cáo tóm tắt Việt/Anh; video nộp riêng |

**Ba loại nội dung phải phân biệt:** thông tin kết quả nghiên cứu ở đầu quyển; báo cáo tóm tắt là sản phẩm riêng và được đính kèm cuối quyển; bản tin là sản phẩm riêng khác. Không dùng một bản abstract của bài báo để thay cả ba loại.

Không có quy định yêu cầu lời cảm ơn, lời cam đoan hoặc abstract kiểu luận văn trong sáu tệp. Nếu bổ sung, cần xác định vị trí phù hợp mà vẫn bảo toàn trình tự bắt buộc.

## 4. Cách viết nội dung khoa học

### 4.1. Mở đầu

HT mục 3.10 yêu cầu sáu nội dung:

1. Tổng quan tình hình nghiên cứu trong nước và ngoài nước thuộc lĩnh vực đề tài.
2. Lý do chọn đề tài.
3. Mục tiêu đề tài.
4. Phương pháp nghiên cứu.
5. Đối tượng nghiên cứu.
6. Phạm vi nghiên cứu.

**Đề xuất cách viết:** dẫn từ vấn đề thực tiễn tới khoảng trống nghiên cứu, rồi xác định mục tiêu và phương pháp kiểm chứng. Phân biệt mục tiêu đăng ký với kết quả thực tế; mô tả phạm vi dữ liệu, nền tảng, điều kiện thử nghiệm và giới hạn. Tổng quan phải tổng hợp và so sánh nghiên cứu có trích dẫn, không chỉ liệt kê công trình.

Mở đầu nên là khối riêng trước Chương 1. Nếu cần chương tổng quan chuyên sâu, phần Mở đầu vẫn phải có tổng quan đủ để đáp ứng mục 3.10; chương sau chỉ mở rộng nền tảng và phân tích.

### 4.2. Các chương kết quả và bàn luận

HT mục 3.11 yêu cầu trình bày kết quả đạt được và đánh giá các kết quả này thành các chương đánh số. Tài liệu không ấn định số chương, tên chương hay tỷ lệ trang.

**Đề xuất cách viết cho từng kết quả:** nêu vấn đề/mục tiêu, mô tả phương pháp và điều kiện kiểm chứng, trình bày bằng chứng, phân tích ý nghĩa, rồi chỉ rõ giới hạn. Phân biệt thiết kế dự kiến, phần đã cài đặt và phần đã được đánh giá. Với kết quả định lượng, ghi nguồn số liệu, bộ dữ liệu, cách chia tập, cấu hình, thước đo, đối chứng và mức bất định khi có.

Ảnh giao diện và đoạn mã chỉ hỗ trợ lập luận. Các bảng chi tiết, log dài và tài liệu vận hành có thể chuyển sang phụ lục; phần thân phải giữ kết quả chính và bàn luận đủ để hội đồng đánh giá.

### 4.3. Kết luận và kiến nghị

HT mục 3.12 yêu cầu:

- **Kết luận:** kết luận về các nội dung đã thực hiện, đánh giá đóng góp mới và khả năng ứng dụng.
- **Kiến nghị:** đề xuất rút ra từ kết quả; nghiên cứu tiếp theo; biện pháp để ứng dụng; lĩnh vực sử dụng; kiến nghị cơ chế, chính sách phù hợp.

**Đề xuất:** kết luận theo từng mục tiêu ban đầu, chỉ rõ đạt đầy đủ/đạt một phần/chưa đạt bằng bằng chứng trong các chương. Kiến nghị phải có căn cứ từ hạn chế và kết quả, tránh khẳng định khả năng triển khai thực tế khi chỉ có mô phỏng hoặc kiểm thử chức năng.

## 5. Tài liệu tham khảo và những quy ước chưa được ấn định

Nguồn: HT mục 3.13.

- Liệt kê các sách, báo và tài liệu đã dùng trong quá trình nghiên cứu.
- Thông tin thường theo thứ tự: họ tên tác giả, nhan đề, các yếu tố xuất bản.
- Phân loại theo thứ tự: văn bản pháp quy; sách, báo, tạp chí; bài viết của tác giả…
- Trong mỗi loại, sắp xếp theo bảng chữ cái.

**Hệ quả:** không áp dụng nguyên xi danh mục tài liệu của bài báo LNCS trong `paper/`. Đề xuất quản lý bằng `.bib`, gắn loại/nhóm cho từng mục, rồi xuất các nhóm theo thứ tự và sắp xếp chữ cái trong từng nhóm. Ranh giới “báo, tạp chí” và “bài viết” chưa được hướng dẫn rõ; cần định nghĩa nhất quán khi lập danh mục.

HT không ấn định APA/IEEE, cách trích dẫn trong thân bài, vị trí số trang, cỡ tiêu đề, thụt đầu dòng, vị trí chú thích bảng/hình, đánh số công thức hay số cấp đề mục. Có thể đề xuất các quy ước này trong lớp LaTeX, nhưng phải ghi là lựa chọn của dự án. Thứ tự chữ cái cho tên Việt/Anh cũng cần kiểm tra thủ công; không coi sắp xếp mặc định của công cụ là bằng chứng đã tuân thủ.

## 6. Bìa, biểu mẫu và dữ liệu hành chính

### 6.1. Bìa chính

Theo B trang 1: khung đôi, các khối căn giữa, dòng “BỘ GIÁO DỤC VÀ ĐÀO TẠO”, “ĐẠI HỌC CẦN THƠ”, logo trường, tiêu đề “BÁO CÁO TỔNG KẾT”, dòng “ĐỀ TÀI NGHIÊN CỨU KHOA HỌC CỦA SINH VIÊN”, tên đề tài, mã đề tài, chủ nhiệm và “Cần Thơ, tháng/năm” ở cuối trang.

### 6.2. Bìa phụ

Theo B trang 2: giữ các khối cơ quan, logo, loại báo cáo, tên và mã đề tài; bổ sung họ tên chủ nhiệm, Nam/Nữ, dân tộc, lớp, Trường/Khoa/Viện, năm thứ/số năm đào tạo, ngành học, người hướng dẫn với chức danh khoa học và học vị. Khối thông tin cá nhân căn trái; địa điểm và tháng/năm căn giữa cuối trang.

Kích thước logo, khung và khoảng cách giữa các khối là đặc điểm của mẫu nhìn thấy, không có số đo bắt buộc trong phần hướng dẫn. Khi dựng bìa nên đối chiếu trực quan với PDF mẫu, đồng thời thử tên đề tài dài để tránh tràn trang. Có sẵn [logo-ctu.png](logo-ctu.png); cần kiểm tra độ nét ở kích thước in trước khi dùng.

### 6.3. Biểu mẫu còn thiếu

HT nói “theo mẫu bên dưới” đối với thông tin kết quả Việt/Anh và thông tin sinh viên chủ nhiệm, nhưng cả Word và PDF được cung cấp **không chứa các biểu mẫu đó**. Không đủ căn cứ để xác định toàn bộ nhãn trường, bảng biểu và bố cục chính thức.

HD trang 1–2 xác định được các vùng phải dành chỗ:

- Trang thông tin kết quả tiếng Việt: chữ ký chủ nhiệm; nhận xét của cán bộ hướng dẫn, viết tay hoặc đánh máy; chữ ký cán bộ hướng dẫn.
- Trang thông tin chủ nhiệm: chữ ký chủ nhiệm.
- Mỗi quyển có tổng cộng hai chữ ký của chủ nhiệm và một chữ ký của người hướng dẫn.

Đề xuất tách ba biểu mẫu thành ba tệp độc lập, có thể thay bằng đúng mẫu chính thức khi bổ sung. Không đánh dấu bản tự dựng là “đúng mẫu” trước khi đối chiếu.

## 7. Hồ sơ cuối quyển và đầu ra cần nộp

Nguồn: HD trang 1–2; HT mục 3.15–3.17.

### 7.1. PDF hoàn chỉnh

Một tệp PDF duy nhất, đúng thứ tự như quyển in, chứa toàn bộ phần khoa học và hồ sơ đính kèm cuối quyển:

1. Thuyết minh đã phê duyệt, có chữ ký và dấu.
2. Minh chứng sản phẩm đăng ký nhóm I, II, III.
3. Bản tin tiếng Việt, bản tin tiếng Anh.
4. Báo cáo tóm tắt tiếng Việt, báo cáo tóm tắt tiếng Anh.

Video không phải chèn minh chứng vào PDF hoặc quyển in; nộp tệp riêng. Mã nguồn, URL hoặc ảnh chụp có thể hỗ trợ minh chứng, nhưng không tự động chứng minh hoàn thành mọi sản phẩm đã đăng ký.

### 7.2. Bộ tệp điện tử sau nghiệm thu

| Đầu ra | Định dạng | Quan hệ với quyển báo cáo |
|---|---|---|
| Báo cáo tổng kết hoàn chỉnh | Word và PDF | Word cùng thứ tự các phần, chỉ gửi các nội dung là Word; PDF gộp đầy đủ |
| Bản tin tiếng Việt | Word và PDF | Vừa đính kèm trong PDF tổng kết, vừa nộp riêng |
| Bản tin tiếng Anh | Word và PDF | Vừa đính kèm trong PDF tổng kết, vừa nộp riêng |
| Báo cáo tóm tắt tiếng Việt | Word và PDF | Vừa đính kèm trong PDF tổng kết, vừa nộp riêng |
| Báo cáo tóm tắt tiếng Anh | Word và PDF | Vừa đính kèm trong PDF tổng kết, vừa nộp riêng |
| Video | Tệp video | Nộp riêng |

**Đề xuất kiến trúc:** LaTeX là nguồn dàn trang PDF; phải có quy trình tạo và rà soát Word song song. Có thể dùng nguồn nội dung chung hoặc chuyển đổi có kiểm soát, nhưng không mặc định chuyển `.tex` sang `.docx` sẽ giữ nguyên bảng, công thức, tham chiếu, phông và phân trang. Theo cách diễn đạt của HD, yêu cầu Word nhấn mạnh thứ tự và nội dung; không nói Word phải đồng nhất từng trang với PDF. Bản tin và báo cáo tóm tắt cần các điểm vào riêng để xuất độc lập.

### 7.3. Bản in

- Nộp hai quyển đã chỉnh sửa theo góp ý hội đồng.
- Quyển Phòng KH, CN và ĐMST giữ: trang có ảnh phải in màu; có thể in một hoặc hai mặt.
- Quyển làm hồ sơ thanh toán: in hai mặt; được trả lại sau khi Phòng ký xác nhận.
- Có thể nộp thêm quyển để lưu.
- Các quyển phải có đủ chữ ký và nhận xét tại vị trí HD quy định.

HT vẫn ghi lề trái 3 cm, phải 2 cm, không nêu lề đối xứng. Vì vậy không tự động bật đổi lề trong/ngoài ở bản in hai mặt. Có thể giữ lề vật lý trái/phải đúng nguồn; nếu muốn đổi để đóng gáy, cần đối chiếu yêu cầu của đơn vị tiếp nhận. Việc chèn trang trắng khi mở chương ở trang lẻ cũng là lựa chọn kỹ thuật, không phải yêu cầu.

## 8. Quy trình nghiệm thu và sản phẩm ngoài LaTeX

Các mốc sau được ghi trong HD, không phải kết quả xác minh quy định hiện hành:

- Xin nghiệm thu: đơn xin báo cáo nghiệm thu và một PDF báo cáo đúng mẫu, có hồ sơ cuối quyển.
- Tổ chức nghiệm thu trong 30 ngày từ ngày ký quyết định.
- Gửi quyết định, báo cáo và phiếu nhận xét cho thành viên hội đồng ít nhất 7 ngày trước nghiệm thu.
- Thống nhất thời gian/địa điểm với người hướng dẫn và hội đồng; thông báo chính thức cho Phòng.
- Sau nghiệm thu: chỉnh sửa và nộp hồ sơ chậm nhất 20 ngày từ ngày nghiệm thu.
- Địa chỉ nhận được ghi trong tài liệu: `nguyentan@ctu.edu.vn`; cần kiểm tra lại khi thực sự nộp.

Hồ sơ họp hội đồng xếp theo thứ tự: 5 biên bản; nhận xét và chấm điểm của Chủ tịch, Phản biện 1, Phản biện 2, Ủy viên, Thư ký; phiếu giải trình chỉnh sửa có xác nhận của người hướng dẫn, Chủ tịch và Thư ký; quyết định nghiệm thu có dấu đỏ. Đây là hồ sơ riêng, không có yêu cầu đưa toàn bộ vào thân báo cáo. Cần copy phiếu nhận xét phục vụ thanh toán trước khi nộp.

HD trang 4 ghi hồ sơ thanh toán hội đồng gồm quyết định có dấu đỏ, biên bản chính có xác nhận của Phòng, bản copy 5 phiếu nhận xét và danh sách nhận tiền. Đây là ghi chú vận hành; không chép trang ghi chú vào báo cáo.

**Video theo HD trang 3:** tối đa 2 phút, tiếng Việt, giới thiệu trọng tâm kết quả/sản phẩm/quy trình; logo trường ở góc trên bên phải trong toàn video. Phần đầu có đủ mã đề tài, tên đề tài, thời gian từ tháng/năm đến tháng/năm, tổng kinh phí theo hợp đồng tính bằng đồng, chủ nhiệm kèm điện thoại, thành viên, người hướng dẫn kèm email. Có thể quay hoạt động, thuyết trình hoặc phối hợp; tài liệu nhắc kiểm tra quyền sử dụng hình/âm thanh của bên khác.

## 9. Đề xuất bố cục khoa học cho dự án hiện tại

Đây là đề xuất dựa trên phạm vi hệ thống cứu hộ, bài báo và thực nghiệm đang có trong repository, không phải tên chương bắt buộc của HT.

| Khối | Nội dung chính | Dự toán trang thân bài |
|---|---|---:|
| Mở đầu | Tổng quan trong/ngoài nước, lý do, mục tiêu, phương pháp, đối tượng, phạm vi | 7–9 |
| Chương 1. Cơ sở khoa học và yêu cầu bài toán | Edge AI, dữ liệu đa phương thức, mạng yếu, phân cụm và điều phối; yêu cầu và tiêu chí đánh giá | 8–10 |
| Chương 2. Dữ liệu và phương pháp nghiên cứu | Dữ liệu ảnh; dữ liệu báo cáo bán tổng hợp; mô hình, đồ thị, xếp hạng, thiết kế thực nghiệm | 10–12 |
| Chương 3. Thiết kế và xây dựng hệ thống | Ứng dụng, AI tại thiết bị, đồng bộ, backend, CSDL, dashboard; trạng thái triển khai | 10–12 |
| Chương 4. Thực nghiệm, kết quả và bàn luận | Kết quả mô hình ảnh; RQ1–RQ3; kiểm thử hệ thống/mạng; đối chiếu mục tiêu và sản phẩm, hạn chế | 14–18 |
| Kết luận và kiến nghị | Mức hoàn thành mục tiêu, đóng góp, khả năng ứng dụng, hướng tiếp theo | 3–4 |
| **Tổng dự toán** | **Không tính phần đầu, tài liệu tham khảo, phụ lục, hồ sơ minh chứng** | **52–65** |

Dự toán để lập kế hoạch nội dung, không phải chỉ tiêu kéo dài bằng khoảng trắng hoặc bảng biểu không cần thiết. Nếu chương thực nghiệm quá lớn có thể tách kết quả và bàn luận, vẫn giữ chương đánh số và thứ tự chung.

Nguồn nội bộ có thể tái sử dụng sau khi rà soát:

- [paper/main_vi.tex](../paper/main_vi.tex), [paper/main.tex](../paper/main.tex): lập luận và kết quả bài báo; giữ nguyên ý nghĩa các kết quả âm và giới hạn.
- [thucnghiem/data/README.md](../thucnghiem/data/README.md), `thucnghiem/results/`: mô tả dữ liệu, cấu hình, bảng kết quả và nguồn số liệu.
- [docs/system_design.md](../docs/system_design.md), [docs/contact_db.md](../docs/contact_db.md), [docs/contact_connect.md](../docs/contact_connect.md): kiến trúc, CSDL và hợp đồng đồng bộ.
- [docs/nghiem-thu/doi_chieu_thuyet_minh.md](../docs/nghiem-thu/doi_chieu_thuyet_minh.md): điểm bắt đầu đối chiếu cam kết; là ảnh chụp trạng thái ngày 27/09/2026, cần kiểm tra lại trước khi đưa vào báo cáo.
- [docs/nghiem-thu/ban_tin.md](../docs/nghiem-thu/ban_tin.md): bản nháp Việt/Anh; còn placeholder và thông tin cần kiểm chứng.

Không chép nguyên các đường dẫn trong tài liệu cũ: một số còn dùng `fe/`, `be/`, `src/`, trong khi cây hiện tại là `products/fe/`, `products/be/`, `thucnghiem/`. Không gọi dữ liệu bán tổng hợp là dữ liệu cứu hộ thực tế; không coi kiểm thử web là bằng chứng AI/SMS trên điện thoại thật. Các trạng thái hạn chế trong tài liệu đối chiếu phải được kiểm tra lại, không suy ra tự động rằng chúng vẫn đúng hiện tại.

## 10. Đề xuất cấu trúc dự án LaTeX

### 10.1. Cây thư mục dự kiến

Các tệp dưới đây là thiết kế đề xuất, chưa được tạo trong đợt phân tích này.

```text
report/
├── guideline/                    # Tài liệu nguồn giữ nguyên
├── tong-hop-huong-dan.md          # Phân tích và yêu cầu
├── logo-ctu.png
├── README.md                     # Quy ước viết, lệnh build, quy trình bàn giao
├── main.tex                      # Điều phối quyển báo cáo đúng thứ tự
├── latexmkrc                     # Cấu hình biên dịch
├── Makefile                      # Các đầu ra: nội dung, đầy đủ, sản phẩm riêng
├── template/
│   ├── ctu-report.cls            # A4, cỡ chữ, lề, tiêu đề, đánh số
│   ├── typography.tex            # Phông và giãn dòng
│   ├── packages.tex              # Gói bổ sung có quản lý
│   ├── bibliography.tex          # Nhóm tài liệu và sắp xếp
│   └── commands.tex              # Lệnh ngữ nghĩa dùng chung
├── config/
│   ├── metadata.tex              # Mã, tên đề tài, chủ nhiệm, GVHD, thời gian...
│   └── profiles.tex              # Nội dung/đầy đủ và lựa chọn in
├── frontmatter/
│   ├── cover.tex
│   ├── title-page.tex
│   ├── participants.tex
│   ├── abbreviations.tex
│   ├── research-info-vi.tex
│   ├── research-info-en.tex
│   └── principal-investigator.tex
├── chapters/
│   ├── introduction.tex
│   ├── 01-foundations/
│   │   ├── chapter.tex
│   │   └── sections/...
│   ├── 02-data-methods/...
│   ├── 03-system/...
│   ├── 04-evaluation/...
│   └── conclusion.tex
├── bibliography/
│   └── references.bib
├── assets/
│   ├── figures/                  # Hình dùng trong báo cáo
│   └── diagrams/                 # Nguồn sơ đồ và bản xuất
├── generated/
│   ├── tables/                   # Bảng sinh từ kết quả có nguồn gốc
│   └── values.tex                # Số liệu dùng lại trong nhiều đầu ra
├── appendices/
│   ├── reproducibility.tex
│   └── supplementary-results.tex
├── evidence/
│   ├── manifest.yaml             # Cam kết → sản phẩm → minh chứng → trạng thái
│   ├── approved-proposal.pdf     # Bản ký/dấu chính thức, không tự dựng
│   └── products/...
├── deliverables/
│   ├── bulletin-vi.tex
│   ├── bulletin-en.tex
│   ├── summary-vi.tex
│   ├── summary-en.tex
│   └── content/                  # Nội dung tái sử dụng cho PDF riêng và quyển
├── word/
│   ├── reference.docx            # Mẫu Word khi được cung cấp
│   └── README.md                 # Quy trình chuyển đổi và rà soát
├── scripts/
│   ├── build_evidence.py         # Kiểm tra/ghép hồ sơ theo manifest
│   ├── export_tables.py
│   └── check_report.py           # Kiểm tra thứ tự, trang, tệp thiếu, placeholder
└── build/                        # Sản phẩm biên dịch, không coi là nguồn
```

### 10.2. Nguyên tắc phân tách

- `main.tex` chỉ điều phối thứ tự; không chứa phần lớn nội dung và không lặp lại cấu hình hình thức.
- Dữ liệu hành chính có một nguồn trong `config/metadata.tex` để bìa, biểu mẫu và sản phẩm riêng không lệch nhau.
- Lớp tài liệu quản lý hình thức; tác giả viết nội dung bằng lệnh ngữ nghĩa. Không rải các lệnh đổi lề/phông giữa chương.
- Mỗi chương có tệp điều phối và các mục độc lập; dùng `\include` ở cấp chương, `\input` ở cấp mục khi phù hợp.
- Quy ước nhãn dùng tiền tố `chap:`, `sec:`, `fig:`, `tab:`, `eq:` và tên có ý nghĩa; không nhập số hình/chương bằng tay.
- Bảng/số liệu sinh từ artifact nằm riêng; ghi nguồn, cấu hình và phiên bản. Không sửa thủ công kết quả thí nghiệm đã khóa trong `thucnghiem/`.
- Hồ sơ scan/minh chứng nằm riêng với phụ lục khoa học: có thể cùng tham gia PDF cuối nhưng khác vai trò và thứ tự.
- Bản tin và báo cáo tóm tắt dùng nội dung chung cho bản riêng và bản đính kèm; tránh hai bản viết độc lập rồi lệch nhau.
- Thư mục `paper/` tiếp tục là dự án bài báo; chỉ tái sử dụng nội dung/hình/số liệu đã kiểm chứng, không dùng lớp LNCS để định dạng báo cáo.

### 10.3. Lựa chọn công cụ khi triển khai

**Đề xuất:** XeLaTeX với Unicode và Times New Roman; lớp báo cáo riêng dựa trên lớp hỗ trợ tài liệu dài và cỡ chữ tùy chỉnh; quản lý build bằng `latexmk`. LuaLaTeX là phương án thay thế nếu có lý do cụ thể. Không dùng phông thay thế trong bản nộp mà coi đó là Times New Roman.

Nhóm chức năng cần có: quản lý phông/ngôn ngữ tiếng Việt; lề và giãn dòng; bảng dài/nhiều trang; công thức và thuật toán; hình và tham chiếu; danh mục; tài liệu tham khảo có phân nhóm; chèn PDF. Chỉ chọn gói và khóa cấu hình sau khi kiểm tra tương thích trong môi trường biên dịch thực tế.

Đánh số La Mã phần đầu, số Ả Rập từ Mở đầu; tiêu đề chương; cách đánh số bảng/hình theo chương; kiểu trích dẫn là **quy ước đề xuất**, không phải yêu cầu đã có trong guideline.

### 10.4. Hai chế độ xuất PDF

1. **Bản nội dung để rà soát:** phần đầu + thân bài + tài liệu tham khảo + phụ lục khoa học. Dùng trong quá trình viết; không coi là hồ sơ nộp đủ.
2. **Bản đầy đủ để nộp:** toàn bộ bản nội dung + thuyết minh đã duyệt + minh chứng nhóm I–III + bản tin và báo cáo tóm tắt Việt/Anh.

Bản đầy đủ phải dừng build khi thiếu tệp bắt buộc hoặc còn placeholder hành chính, thay vì âm thầm bỏ qua. Với PDF scan, bảo toàn chữ ký/dấu và khả năng đọc; không tùy tiện cắt, đổi tỷ lệ hoặc ép giấy làm mất nội dung. Khi chèn bằng LaTeX hoặc ghép hậu kỳ phải kiểm tra thứ tự, hướng trang, dấu trang, số trang và tham chiếu. Chọn một cách quản lý số trang cho hồ sơ đính kèm và ghi rõ trong quy trình.

## 11. Điểm còn thiếu hoặc chưa rõ trước khi triển khai bản nộp

| Vấn đề | Bằng chứng hiện có | Việc cần hoàn tất |
|---|---|---|
| Ba biểu mẫu đầu quyển | HT chỉ nhắc tên, không cung cấp mẫu | Bổ sung mẫu chính thức Việt/Anh và thông tin chủ nhiệm |
| Mẫu bản tin và báo cáo tóm tắt | HD yêu cầu sản phẩm, không quy định bố cục/độ dài ở các tệp này | Bổ sung biểu mẫu và hướng dẫn tương ứng |
| Giới hạn một trang của bản tin | `docs/nghiem-thu/ban_tin.md` có ghi, sáu tệp guideline không có | Chưa coi là yêu cầu đã xác minh; đối chiếu nguồn mẫu riêng |
| Vị trí danh mục sản phẩm trong thuyết minh | HD/HT ghi mục 16; tài liệu đối chiếu dự án ghi mục 17 | Dùng bản thuyết minh ký/dấu để xác định cam kết thực tế, ghi mapping rõ |
| Bản thuyết minh scan đã phê duyệt | Chưa xác nhận tệp để đính kèm trong phạm vi này | Chọn đúng bản có ký/dấu; bản Markdown không thay được |
| Cách tính 50 trang | Chỉ loại rõ mục lục, TLTK, phụ lục | Dùng cách tính thân bài bảo thủ; xác nhận nếu cần |
| Lề khi in hai mặt | HT ghi lề trái/phải; HD cho phép/yêu cầu in hai mặt tùy quyển | Không tự đổi sang lề đối xứng; chốt trước khi in |
| Quy ước chi tiết về tham khảo | Có phân loại và chữ cái, chưa có style trích dẫn | Chọn và ghi quy ước nhất quán, đối chiếu danh mục mẫu nếu có |
| Word song song | HD yêu cầu Word | Thiết kế chuyển đổi và kiểm tra ngay từ đầu |
| Thông tin hành chính chính xác | Một số bản nháp còn placeholder | Chốt mã, tên, đơn vị, GVHD, thời gian, kinh phí theo hồ sơ chính thức |

Các thiếu sót này không ngăn xây dựng cấu trúc kỹ thuật và viết chương; chúng ngăn việc xác nhận bản cuối đã đầy đủ, đúng mẫu để nộp.

## 12. Checklist kiểm tra khi hiện thực hóa

- [ ] A4; thân bài Times New Roman cỡ 13; giãn dòng trong khoảng 1,3–1,5; lề trái 3 cm và ba lề còn lại 2 cm.
- [ ] Phông tiếng Việt được nhúng và hiển thị đúng; không có phông thay thế ngoài ý muốn.
- [ ] Bìa và bìa phụ khớp mẫu, tên dài không tràn; thông tin hành chính thống nhất.
- [ ] Có đủ 17 khối và giữ thứ tự theo HT, với phụ lục khoa học nếu cần.
- [ ] Có mẫu chính thức và chỗ nhận xét/chữ ký cho các biểu mẫu đầu quyển.
- [ ] Mở đầu có đủ tổng quan, lý do, mục tiêu, phương pháp, đối tượng, phạm vi.
- [ ] Chương kết quả có cả bằng chứng và đánh giá; kết luận/kiến nghị gắn với mục tiêu.
- [ ] Ít nhất 50 trang thân bài theo cách tính nội bộ; báo cáo kiểm tra tách rõ từng khối.
- [ ] Tài liệu tham khảo có nhóm và sắp xếp chữ cái; trích dẫn và liên kết chéo không lỗi.
- [ ] Từ viết tắt xếp chữ cái; mục lục và danh mục hình/bảng cập nhật.
- [ ] Số liệu truy được về artifact; không mô tả mô phỏng thành kiểm chứng thực địa.
- [ ] Thuyết minh scan có ký/dấu và minh chứng sản phẩm đúng cam kết được đính kèm.
- [ ] Bản tin và báo cáo tóm tắt Việt/Anh có cả bản đính kèm và Word/PDF riêng.
- [ ] Word được rà soát nội dung/thứ tự, bảng/công thức/tham chiếu và hình thức liên quan.
- [ ] PDF cuối gộp thành một tệp; trang scan đọc được, đúng thứ tự và hướng trang.
- [ ] Không còn placeholder, ghi chú mẫu, tham chiếu thiếu hoặc tệp bắt buộc bị bỏ qua.
- [ ] Có bộ in phù hợp, đủ nhận xét/chữ ký; video riêng đáp ứng yêu cầu HD.

Bước tiếp theo phù hợp là dựng lớp báo cáo, bìa, thứ tự khối và các điểm vào sản phẩm riêng; kiểm tra một bản mẫu có tên đề tài dài, tiếng Việt, bảng nhiều trang, công thức và PDF scan trước khi đưa toàn bộ nội dung vào.
