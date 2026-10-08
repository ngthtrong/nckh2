# Đối chiếu hướng dẫn và biểu mẫu — 08/10/2026

Căn cứ trực tiếp: `guideline/template/HinhThucBC.doc` (đối chiếu với `guideline/HinhThucBC.pdf`) và toàn bộ chín mẫu `.doc` còn lại trong `guideline/template/`. Đã đọc nội dung văn bản Word nhị phân; phần bố cục đồ họa/ô bảng cần đối chiếu trực quan với Word trước khi ký. Bản LaTeX áp dụng thứ tự và các mục nội dung, không phải bản chuyển đổi Word giống từng vị trí. Hash và nội dung trích xuất lưu tại `generated/guideline-text/`.

## Những phần thuộc quyển báo cáo tổng kết

| Căn cứ | Trước cập nhật | Sau cập nhật / còn thiếu |
| --- | --- | --- |
| Hình thức §2 và §3.1–3.6; `Bìa.doc` | Đã có hai bìa, thành viên, mục lục, danh mục bảng/hình/từ viết tắt | Giữ A4, TNR 13, dòng 1,3, lề trái 3 cm, còn lại 2 cm; kiểm tra lại số trang thân bài tối thiểu 50 sau build |
| §3.7; `Mẫu Thông tin kết quả nghiên cứu VN.doc` | Thiếu phân biệt tính mới, sản phẩm, công bố, đóng góp, chuyển giao; thiếu lớp/năm/số năm đào tạo và khối xác nhận trường | Đã sắp đủ tám mục, bổ sung metadata và khối xác nhận trường/GVHD; chưa có nhận xét GVHD, chữ ký, dấu, ngày ký hoặc chứng cứ công bố/chuyển giao |
| §3.8; `Mẫu Thông tin kết quả nghiên cứu EN.doc` | Nội dung chưa theo sáu mục mẫu | Đã sắp sáu mục: general information, objectives, creativeness, results, products, effects/transfer/applicability; bổ sung implementing institution/duration |
| §3.9; `Mẫu Thông tin về sinh viên chủ nhiệm đề tài .doc` | Thiếu nơi sinh, địa chỉ, ảnh, quá trình học tập và xác nhận trường | Đã bổ sung nơi sinh/địa chỉ theo mẫu, khung ảnh 4×6, phần học tập năm 1–4 và khối ký; **còn thiếu ảnh thật, xếp loại và thành tích từng năm, xác nhận trường/chữ ký** |
| §3.10–3.14 | Đã có Mở đầu, chương khoa học, kết luận, tài liệu tham khảo, phụ lục | Đã cập nhật hình và bảng ảnh sang model seed 1024; giữ các benchmark cũ với phạm vi lịch sử rõ ràng |
| §3.15 | Chỉ có nội dung thuyết minh nguồn | **Thiếu `evidence/approved-proposal.pdf` có phê duyệt/ký/dấu** |
| §3.16 | Có code/artifact, manifest sản phẩm | **Thiếu PDF minh chứng ứng dụng, dashboard và bộ AI**, cùng xác nhận phù hợp cam kết; không dùng code thay biên bản nghiệm thu |
| §3.17; `BẢN TIN ĐỀ TÀI .doc` | Có Việt/Anh nhưng mỗi bản 2 trang, thiếu một số trường/mục | Đã thêm kinh phí, điện thoại chủ nhiệm, thành viên và đủ bảy nhãn nội dung; rút về **1 trang A4/ngôn ngữ** theo mẫu. Mẫu cho phép bỏ ảnh khi không chọn được ảnh; bản tin hiện không dùng ảnh để tránh suy quyền phát hành ảnh dataset |
| §3.17; `BÁO CÁO TÓM TẮT .doc` | Có nội dung nhưng chưa đúng các mục chính thức | Đã sắp tám mục tiếng Việt, sáu mục tiếng Anh. Tựa tiếng Anh trong chính mẫu là INFORMATION ON RESEARCH RESULTS, được giữ dù gần giống mẫu thông tin kết quả. Mẫu này không ghi giới hạn một trang như bản tin |
| §3.17; video | Chưa có xác nhận sản phẩm video | Video nộp riêng, **không ghép vào quyển in**; còn cần xác nhận video hoàn thành/nộp |

Trong bản `content`, các mục §3.15–3.17 chưa ghép vì PDF phê duyệt/minh chứng chưa có. `full` sẽ ghép theo manifest khi đủ điều kiện. Bốn bản tin/tóm tắt được biên dịch riêng bằng `make deliverables`; việc chúng tồn tại chưa đồng nghĩa đã nằm trong bản `content`.

## Mẫu ngoài quyển và điểm cần xác nhận

| Tệp | Vai trò / tình trạng |
| --- | --- |
| `ĐƠN XIN BÁO CÁO NGHIỆM THU.doc` | Hồ sơ xin nghiệm thu riêng; §3 không yêu cầu đưa đơn vào quyển. Tệp còn chứa các trang mẫu khác; không coi tên tệp là một mẫu duy nhất. Chờ ngày ký/xác nhận và kiểm tra danh sách hội đồng theo quyết định, không tự chứng thực các tên đã điền |
| `DANH SÁCH NHẬN TIỀN.doc` | Hồ sơ kinh phí riêng, không nằm trong thứ tự §3; chưa có chứng từ/xác nhận chi trả. Không suy số tiền hoặc người nhận từ code/báo cáo |
| `Bieu mau de tai NCKH cua SV_26.5.2026.doc` | Nội dung thực tế chỉ là mẫu tiếng Anh INFORMATION ON RESEARCH RESULTS sáu mục, trùng nội dung tệp EN; không phải một bộ biểu mẫu hoàn chỉnh như tên tệp gợi ý |

Mâu thuẫn cần xử lý trước khi ký:

- Mẫu chủ nhiệm điền “06 tháng 10 năm 2026”; báo cáo giữ ngày sinh **06/10/2005** theo xác nhận trước. Nơi sinh Sóc Trăng, địa chỉ Khu vực 5, Phường Ngã Năm, Thành phố Cần Thơ được đồng bộ vào `resource/infoGroup.md` với nguồn là mẫu mới, chưa gán là một xác nhận mới của người dùng.
- Đơn xin nghiệm thu ghi **05/2026–10/2026**; metadata/thuyết minh đã đối chiếu ghi **03/2026–08/2026**. Đơn cũng thêm “Xây dựng” vào đầu tên đề tài. Giữ tên/thời gian đã xác nhận trong báo cáo; cần căn cứ quyết định gia hạn/điều chỉnh hoặc sửa đơn, không tự chọn một phiên bản.
- Hướng dẫn gọi sản phẩm ở **mục 16** của thuyết minh; thuyết minh nhóm và manifest đang ánh xạ **mục 17**. Đối chiếu thuyết minh thực tế đã phê duyệt; không đổi số mục theo một mẫu chung.
- Chưa có minh chứng công bố/tiếp nhận/chuyển giao: bản thảo ISDS 2026 chỉ là bản thảo. Những phần này được ghi theo phạm vi bằng chứng hiện có.

`official_forms_confirmed`, `commitments_confirmed` và các cờ `verified` vẫn false. Đã có mẫu chính thức để đối chiếu cấu trúc không thay thế việc xác nhận bản điền hoàn chỉnh hoặc hồ sơ ký/dấu.

## Phạm vi model mới và các hình

Sáu PNG của `mobilenetv3_large_dataset_v4_seed1024` được sao chép nguyên byte vào `assets/figures/`, hash nguồn/đầu ra ở `generated/figure-provenance.json`. Ma trận raw được đối chiếu JSON: accuracy 194/256 = 75,78125%, macro-F1 74,2649179%, 3 lỗi nặng. Có 11 hàng history. Ảnh misclassified là **validation**, không phải test.

Thư mục này chưa có manifest đường dẫn/hash split riêng hoặc prediction CSV đầy đủ trên test. Không xác nhận rằng seed 1024 trùng từng ảnh với split seed 42 chỉ từ support lớp giống nhau. Confidence-calibration, runtime/nén/cắt tỉa và mobile vẫn thuộc artifact lịch sử được ghi riêng; chưa huấn luyện hoặc benchmark lại trong đợt sửa báo cáo này.

## Kiểm tra sau cập nhật ngày 08/10/2026

Bản nội dung một mặt/hai mặt đều 98 trang, 70 trang từ Mở đầu đến hết Kết luận/kiến nghị. Bản tin Việt/Anh mỗi bản 1 trang A4; tóm tắt Việt/Anh mỗi bản 2 trang A4. Đã kiểm tra trực quan ma trận/ví dụ lỗi/loss, biểu mẫu chủ nhiệm và hai bản tin; sáu PNG khớp nguyên byte nguồn. Sáu log cuối không có overfull, tham chiếu/trích dẫn chưa giải quyết, nhãn lặp hoặc cảnh báo phông; PDF A4, phông nhúng. Đã xác nhận số liệu model mới trong văn bản PDF.

`make check`, kiểm tra bản hai mặt và `git diff --check` đạt. Git cho phép đúng sáu PDF hiện có trong build; file phụ/môi trường vẫn bỏ qua. `make check-release` chưa đạt: còn hai ghi chú ảnh/quá trình học tập và nhận xét GVHD, các cờ xác nhận hồ sơ false, thiếu thuyết minh phê duyệt và ba PDF sản phẩm. Đây là bản đã biên dịch/kiểm tra, chưa phải bộ hồ sơ đủ điều kiện nộp.

## Đối chiếu trực quan PDF mẫu bổ sung ngày 08/10/2026

Nguồn mẫu chuyển sang `guideline/template/`. Đã đọc và xem trực tiếp tám PDF (19 trang), gồm thông tin kết quả VN/EN, thông tin chủ nhiệm, bản tin hai ngôn ngữ, báo cáo tóm tắt hai ngôn ngữ, đơn/phiếu nghiệm thu và danh sách nhận tiền; bìa đối chiếu với `guideline/Bìa.pdf` hiện có. `make templates` ghi hash cả 10 Word và 8 PDF cùng văn bản trích xuất.

- Thông tin kết quả VN: tên cơ quan trước tiêu đề căn giữa, tám mục chữ đậm cỡ thân bài, thông tin chung gạch đầu dòng, ngày/chủ nhiệm bên phải, nhận xét GVHD ở trang riêng, xác nhận trường trái và người hướng dẫn phải, có họ tên dưới khoảng ký.
- Thông tin kết quả EN: tiêu đề căn giữa, sáu mục, thông tin chung thụt vào; không thêm logo/cơ quan không có trong PDF gốc.
- Tóm tắt VN: logo trái, tên cơ quan bên cạnh, tiêu đề hai dòng căn giữa, tám mục. Tóm tắt EN: tên cơ quan căn giữa, tiêu đề căn giữa, sáu mục, không thêm logo không có trong mẫu.
- Bản tin VN/EN: logo trái, tên cơ quan và tiêu đề căn giữa, các trường/nội dung theo dòng gạch đầu dòng; không giữ ô ảnh tùy chọn hoặc ghi chú hướng dẫn. Mỗi ngôn ngữ giữ một trang A4.
- Thông tin chủ nhiệm: tên cơ quan trước tiêu đề căn giữa; sơ lược trái/khung ảnh 4×6 phải; quá trình học tập kê từng năm theo các dòng ngành/đơn vị/xếp loại/thành tích, không dùng bảng thay mẫu; xác nhận trường trái/chủ nhiệm phải.
- Mẫu tài chính/đơn và phiếu của hội đồng được đối chiếu nhưng giữ ngoài quyển, không điền hoặc chứng thực nội dung do hội đồng/cơ quan lập.

Các biểu mẫu dùng font Times New Roman 13 bp, giãn dòng đơn và khoảng cách đoạn theo PDF mẫu; phần khoa học vẫn giữ giãn dòng 1,3 và lề quy định. Các ô trống học tập/ảnh/nhận xét dùng trường chờ dữ liệu, không in ghi chú TODO vào mẫu. Bộ kiểm tra release vẫn phát hiện các trường này.

Đã bỏ toàn bộ dòng `Nguồn: ...` khỏi source LaTeX và bộ xuất bảng; các ghi chú của bảng được chuyển vào `generated/provenance.json` (`table_notes`). Các nguồn ảnh/hash và hồ sơ đối chiếu vẫn lưu bên ngoài PDF. Trích dẫn bài báo khoa học và danh mục tài liệu tham khảo giữ nguyên.

## Kiểm tra sau đối chiếu PDF mẫu — 08/10/2026

Bản nội dung một mặt/hai mặt hiện đều **94 trang**, có **69 trang thân bài**. Thông tin kết quả Việt gồm trang nội dung/chủ nhiệm và trang nhận xét GVHD riêng, đúng cấu trúc hai trang mẫu; thông tin kết quả Anh và thông tin chủ nhiệm mỗi phần một trang. Khối ký chủ nhiệm nằm cùng trang nội dung, không còn trang chỉ có chữ ký. Bốn PDF bản tin/tóm tắt Việt–Anh đều **1 trang A4/bản**.

Đã xem trực quan các mẫu gốc và các trang biểu mẫu/bản tin/tóm tắt biên dịch; xác nhận logo, thứ tự tên cơ quan--tiêu đề, các mục, trường thông tin và vị trí khối ký. Các dòng nguồn nội bộ đã bỏ khỏi cả sáu PDF và bộ xuất bảng; trích dẫn khoa học/danh mục tài liệu giữ nguyên. Sáu log cuối không có overfull, tham chiếu/trích dẫn chưa giải quyết, nhãn lặp hoặc cảnh báo phông.

`make check`, kiểm tra hai mặt và `git diff --check` đạt. `check-release` vẫn chặn do 10 trường trống thực tế (ảnh, xếp loại/thành tích năm 1–4, nhận xét GVHD), cờ xác nhận hồ sơ và bốn PDF phê duyệt/minh chứng còn thiếu. Số trường tăng từ hai ghi chú tổng hợp sang 10 ô kê khai riêng, không có thêm yêu cầu hành chính mới.

## Bổ sung logo CTU và chuẩn IEEE theo yêu cầu — 08/10/2026

Logo CTU được đặt cố định ở góc trên trái (lề trái 30 mm, lề trên 20 mm, rộng 16 mm) cho tất cả biểu mẫu dùng `officialform`: thông tin kết quả Việt/Anh, thông tin chủ nhiệm và bốn bản tin/tóm tắt. Trang nhận xét GVHD cũng có logo riêng, với khoảng trống đầu trang để tránh đè lên nội dung. Bìa/bìa phụ giữ logo giữa theo mẫu bìa. Các PDF mẫu gốc không bị sửa. Điều này cập nhật lựa chọn trước đây không thêm logo ở một số mẫu tiếng Anh theo yêu cầu mới của người dùng.

Đã thay authoryear/sắp theo tác giả bằng IEEE: số trong ngoặc vuông, đánh theo lần trích dẫn đầu tiên, một danh mục liên tục thay các nhóm pháp quy/sách/bài viết. Yêu cầu IEEE của người dùng được áp dụng thay thứ tự nhóm/chữ cái trong hướng dẫn chung. Bản chính dùng `biblatex-ieee`/biber; fallback dùng style IEEE `ieeetr` và natbib số. Nội dung nguồn/tác giả được giữ nguyên; thêm ngoặc bảo vệ tên riêng/acronym trong title `.bib` để IEEE sentence case không đổi CrisisMMD, FloodNet, MobileNetV3, Twitter, Louvain, Leiden, Viet Nam, JSON/JCS. Phần danh mục dùng locale tiếng Anh để các nhãn trực tuyến theo IEEE hiện đúng `[Online]. Available:`.

## Kiểm tra logo CTU và IEEE — 08/10/2026

Đã biên dịch lại sáu PDF. Bản nội dung một mặt/hai mặt đều 94 trang, 69 trang thân bài; bốn bản tin/tóm tắt mỗi bản một trang A4. Logo CTU hiện ở góc trên trái của tất cả trang biểu mẫu, kể cả trang nhận xét GVHD và các mẫu tiếng Anh; đã xem trực quan để kiểm tra khoảng cách logo/nội dung. Hai bìa giữ logo giữa.

Danh mục IEEE có 19 tài liệu, đánh số liên tục [1]–[19] theo lần trích dẫn đầu tiên. Đã kiểm tra văn bản PDF, thứ tự entry, nhãn `[Online]. Available:` và tên riêng/acronym. Sáu PDF không còn dòng `Nguồn:`; sáu log không có overfull, tham chiếu/trích dẫn chưa giải quyết, nhãn lặp hoặc cảnh báo phông. Fallback BibTeX/ieeetr đã qua bản smoke.

`make check`, kiểm tra bản hai mặt, kiểm tra cú pháp Python và `git diff --check` đạt. `check-release` vẫn chưa đạt do 10 ô thiếu dữ liệu, hai cờ xác nhận và bốn PDF phê duyệt/minh chứng; không thay đổi hoặc xác nhận các hồ sơ này bằng việc sửa bố cục.
