# Đối chiếu nhận xét và phần còn cần bằng chứng — 10/11/2026

Nguồn: [nhận xét Hội đồng](../../tmp.md), danh sách BC/ND/MC người dùng cung cấp, [hồ sơ kết quả local](outputs/local-report-update-20261110/README.md) và [hồ sơ chỉnh sửa tiếp theo](outputs/remaining-revision-20261110/README.md). “Đã sửa” dưới đây là trạng thái biên tập/cài đặt trong repo, không thay xác nhận của Hội đồng hoặc nghiệm thu vận hành.

## Các quyết định phạm vi đã áp dụng

- Ảnh có **cả hai nguồn: nhóm tự chụp và thu thập từ web**, theo xác nhận của nhóm. Không có đủ ánh xạ từng ID để suy số lượng từng nguồn, quyền sử dụng ảnh web hoặc tập camera độc lập.
- **MC-06 và MC-08: SKIPPED_BY_USER.** Không tiếp tục chẩn đoán PTQ/QAT, đo lặp CPU–điện thoại, pin/RAM. Các kết quả và giới hạn lịch sử vẫn được trình bày đúng.
- **NLP/fusion đã cập nhật vào mobile do nhóm khác phụ trách**, theo xác nhận của nhóm. Báo cáo đã ghi nhận; metric pilot vẫn là kết quả offline. Bản dịch tiếng Việt và nhãn AI đã được nhóm kiểm tra, được nhóm đánh giá gần cách diễn đạt cứu hộ tiếng Việt. Việc còn thiếu ở MC-12 là bằng chứng bàn giao/kiểm xuyên luồng, không phải yêu cầu cài lại nhánh mobile trong repo này.
- Đã thực hiện khắc phục phần mềm và kiểm thử mới bằng nguồn lực local hiện có. Không có thiết bị Android kết nối; không ghi nhận đã thử SMS hoặc mạng di động thật.
- **MC-20 và MC-21: FUTURE_WORK_ONLY.** Chỉ viết hướng phát triển điều phối xét chi phí di chuyển và thí điểm cùng đơn vị cứu hộ; không triển khai/thí điểm trong đợt này.
- **Annotations tiếp theo ngày 10/11/2026:** ưu tiên biên tập văn phong, thống nhất ký hiệu và trình bày tài liệu tham khảo. Ngày ký/nhận xét/chữ ký được bổ sung trên bản giấy sau in. Bỏ qua MC-01; không thực hiện thêm MC-02, MC-13–15, MC-17–18 trong phiên này. Bản dịch/nhãn AI được người dùng chấp nhận là dữ liệu đủ cho phạm vi hiện tại; không yêu cầu thu thêm corpus hoặc nhãn gốc trong phiên này. MC-19 chờ thông tin công bố. MC-11 giữ kết quả pilot hiện có, hoãn bổ sung vì chưa có dữ liệu ghép cặp/nhãn độc lập sẵn để xác nhận thêm.

## Bố cục và hình thức

| Mã | Trạng thái hiện tại |
|---|---|
| BC-01 | Đã rút Chương 2; chuyển chi tiết phân lớp, CSDL/API, thao tác, giao diện và bốn lưu đồ xuống phụ lục, giữ nhãn/hình gốc và đường tra cứu. |
| BC-02 | Đã cô đọng Kết luận, giữ kích thước chữ và sơ đồ; kiểm lại bố cục PDF một/hai mặt. |
| BC-03 | Đã dùng số trang liên tục của quyển cho ba minh chứng sản phẩm; trang đầu bản tác giả bài báo được bỏ theo yêu cầu mới. Bản gốc không bị sửa. Hồ sơ công bố chính thức còn ở MC-19. |
| BC-04 | Đã cập nhật mục lục, danh mục, nhãn và tham chiếu; bộ kiểm đối chiếu 50 hình, 52 bảng với PDF. |
| BC-05 | Đã thống nhất font URL, bỏ ngày truy cập lặp ở model card DistilBERT và giữ liền `https://`; kiểm lại bản PDF. Không suy metadata chapter từ sách. |
| BC-06 | Thống nhất K cho số láng giềng/top-K và k cho chỉ số cụm trong P_k; đồng bộ định nghĩa, bảng tham số, mô tả thuật toán và kiểm hồi quy. Top-5 của thước đo xếp hạng giữ nguyên. |
| BC-07 | Bảng và giá trị sinh tự động dùng dấu phẩy ở tiếng Việt; biểu mẫu tiếng Anh đổi sang dấu chấm, giữ phân biệt phần trăm/điểm phần trăm và đơn vị. |
| BC-08 | Đã build/check hai bản in, kiểm font, văn bản và ảnh render; receipt cuối trong hồ sơ chỉnh sửa. Đây không phải kiểm hồ sơ phát hành đủ chữ ký. |

## Nội dung báo cáo

| Mã | Nội dung đã sửa và giới hạn còn lại |
|---|---|
| ND-01 | Rút Chương 2, giữ kiến trúc/luồng chính và chính sách gửi trong thân bài; chi tiết ở phụ lục. |
| ND-02 | Viết lại Kết luận theo đóng góp, câu trả lời RQ, giới hạn và hướng phát triển. |
| ND-03 | Rút tiếp Mở đầu, khái niệm, kiến trúc, đồng bộ, mô hình ảnh và lời dẫn kết quả; bỏ danh mục TN nội bộ trong lời dẫn, dùng tham chiếu cho nội dung đã giải thích. Giữ nguyên hình/bảng, phương trình và kết quả. |
| ND-04 | Bổ sung AlleyFloodNet (2025) và EmergencyNet (2020) từ nguồn gốc, phân biệt nhiệm vụ/góc nhìn. |
| ND-05 | Bổ sung đối chiếu đầu vào, đầu ra, mô hình tại biên, kết nối/chống trùng/điều phối; không tuyên bố ưu thế thuật toán chưa xác lập. |
| ND-06 | Thuyết minh DOCX yêu cầu đánh giá định lượng chất lượng, độ trễ/đồng bộ; bản Markdown nêu Accuracy/F1. Các thước đo có định nghĩa và bảng kết quả trong báo cáo. Không tìm thấy ngưỡng đạt định lượng đã đăng ký; bỏ qua việc đặt ngưỡng trong phiên này theo annotation. |
| ND-07 | Đồng bộ DistilBERT frozen/T2, số tái chạy 52,29% và tích hợp mobile theo xác nhận. Người dùng chấp nhận bản dịch/nhãn AI đủ cho phạm vi hiện tại; giữ rõ nguồn gốc dẫn xuất. |
| ND-08 | Phân biệt tiếp nhận nhiều trường, heuristic và fusion học được; ghi nhận mobile cập nhật, không chuyển metric offline thành metric APK. |
| ND-09 | Đồng bộ bảng đối chiếu thuyết minh với kết quả local, nguồn ảnh hỗn hợp, mobile, sửa phần mềm và phạm vi bỏ qua/hướng phát triển. |
| ND-10 | Giữ rõ split hiện có và lineage chưa xác nhận; grid mới chọn bằng validation, chưa thay tập test độc lập. MC-03 còn mở. |
| ND-11 | Làm rõ Accuracy/F1/lỗi nặng và từng phiên đo; thử pruning cao hơn không thay asset nguyên mẫu. |
| ND-12 | Giữ kết quả có giới hạn của RQ1–RQ3: chưa xác lập Product vượt Additive; chưa xác lập lợi ích xếp hạng chung; revised thua nearest-first trong phép thử đã có. |
| ND-13 | Tách mô tả Android lịch sử, raw còn thiếu và các kiểm thử mới. Không gán log Linux mới cho Case 8 cũ. |
| ND-14 | **DEFERRED_TO_PRINTED_COPY:** ngày ký, nhận xét và chữ ký được bổ sung trên bản giấy sau khi in theo annotation. Giữ chỗ trống trong PDF; ảnh thẻ đã có. |
| ND-15 | Đã bổ sung mục đích nghiên cứu/đào tạo, quyền truy cập, trách nhiệm xác minh và dữ liệu người yếu thế; thí điểm chỉ ở hướng phát triển. |
| ND-16 | Đồng bộ thông tin kết quả, bản tin/tóm tắt Việt–Anh, bảng đối chiếu thuyết minh, Kết luận và minh chứng. |

## Bằng chứng đã bổ sung, còn thiếu hoặc loại khỏi đợt này

| Mã | Trạng thái | Việc còn cần nếu muốn khép nhận xét bằng bằng chứng |
|---|---|---|
| MC-01 | SKIPPED_BY_USER | Bỏ qua theo annotation; giữ mô tả nguồn hỗn hợp và giới hạn hồ sơ hiện có. Không tạo danh mục nguồn hoặc giấy phép mới. |
| MC-02 | SKIPPED_THIS_SESSION_BY_USER | Không thực hiện gán nhãn độc lập/đồng thuận/phân xử trong phiên này; giữ mô tả nhãn hiện có. |
| MC-03 | Còn thiếu | Checksum/lineage split lúc train hoặc protocol/tập xác nhận độc lập theo nguồn/sự kiện. Chọn validation trong grid mới không thay bằng chứng này. |
| MC-04 | Một phần | Nhóm xác nhận có ảnh tự chụp; chưa xác định tập camera/thực địa độc lập với điều kiện chụp, nhãn và kết quả Android. |
| MC-05 | Đã bổ sung | McNemar exact, cặp đúng→sai/sai→đúng, CI và Holm từ dự đoán lưu. Giới hạn độc lập mẫu vẫn theo MC-03. |
| MC-06 | SKIPPED_BY_USER | Không tiếp tục tìm nguyên nhân suy giảm PTQ/QAT trong đợt này. Không tuyên bố nguyên nhân đã được xác định. |
| MC-07 | Đã bổ sung | Grid 5/10/20%, chọn bằng validation và test mức 5%; báo cả kết quả suy giảm, không thay model nguyên mẫu. |
| MC-08 | SKIPPED_BY_USER | Không tiếp tục đo lặp CPU–điện thoại, pin/RAM. Không bổ sung kết luận hiệu năng/tiêu thụ mới. |
| MC-09 | ACCEPTED_FOR_CURRENT_SCOPE_BY_USER | Người dùng xác nhận bản dịch/nhãn AI là đủ cho phạm vi hiện tại. Không thu thêm tin gốc hoặc tạo nhãn mới; vẫn ghi đúng nguồn CrisisMMD dịch và nhãn AI đã được nhóm kiểm tra. |
| MC-10 | Đã bổ sung trong phạm vi dữ liệu được chấp nhận | Có DistilBERT frozen/T2 và mobile theo xác nhận. Trích xuất span hoặc xác nhận trên corpus gốc là hướng mở rộng, không phải việc phải thực hiện trong phiên này. |
| MC-11 | DEFERRED_THIS_SESSION | Giữ đối chứng/ablation offline và CI hiện có. Chưa có dữ liệu ghép cặp với nhãn độc lập sẵn để xác nhận thêm; không chạy lại pilot hoặc suy ưu thế fusion. |
| MC-12 | Đã ghi nhận tích hợp; chờ bàn giao | Nhóm mobile khác cung cấp phiên bản APK/commit/model, contract request/urgency/E_i và log tới đầu ra phân cụm/xếp hạng. Bản adapter trong repo này vẫn dùng urgency/từ khóa; không suy hành vi bản nhóm khác từ bản này. |
| MC-13 | SKIPPED_ADDITIONAL_VALIDATION_THIS_SESSION | Giữ cài đặt và 3 kiểm hồi quy khử bản sao exact đã có; không bổ sung đánh giá dữ liệu thật/gần trùng theo annotation. |
| MC-14 | SKIPPED_THIS_SESSION_BY_USER | Không bổ sung dữ liệu thật/kịch bản nghiệp vụ hoặc thực nghiệm phân cụm/xếp hạng trong phiên này; giữ kết quả và giới hạn lịch sử. |
| MC-15 | SKIPPED_THIS_SESSION_BY_USER | Không tái lập thêm RQ2 trong phiên này. Ba raw p Spearman và năm Holm còn sai lệch được giữ công khai; trạng thái bỏ qua không xác nhận chúng đã khớp. |
| MC-16 | Đã sửa và kiểm mới trên local | Sáu hồi quy trước sửa đều lỗi, sau sửa đều đạt; 284 Flutter đạt (3 bỏ qua), 78 backend đạt, 2 kịch bản Linux–backend đạt. Theo xác nhận mới của người dùng, lỗi gửi khi mất mạng đã hết. Giữ kết quả FAIL lịch sử và không tạo thêm số đo/log Android. |
| MC-17 | SKIPPED_THIS_SESSION_BY_USER | Không thử thêm mạng di động thật; giữ các kết quả Android lịch sử và Linux/proxy theo đúng môi trường đã đo. |
| MC-18 | SKIPPED_THIS_SESSION_BY_USER | Không thử SMS thật trong phiên này; không tạo số liệu giao nhận hoặc log gateway/backend mới. |
| MC-19 | WAITING_FOR_PUBLICATION_INFORMATION | Người dùng sẽ bổ sung khi có thông tin. Giữ bảng công bố hiện tại, không thêm trang minh chứng hoặc suy DOI/số trang chapter từ volume sách. |
| MC-20 | FUTURE_WORK_ONLY | Chỉ trình bày điều phối xét chi phí di chuyển/năng lực/thời hạn trong hướng phát triển; không cài hay chạy mới. |
| MC-21 | FUTURE_WORK_ONLY | Chỉ trình bày thí điểm với đơn vị cứu hộ, xác minh/bảo vệ dữ liệu trong hướng phát triển; không tổ chức thí điểm. |

Các trạng thái bỏ qua/chờ bổ sung ở trên là quyết định phạm vi, không phải bằng chứng khoa học mới. MC-03–04 và MC-12 giữ trạng thái theo dõi trước đó; phiên biên tập này không tự kích hoạt thu dữ liệu, thử thiết bị hoặc bàn giao mobile. Không đưa điểm synthetic vào báo cáo nghiên cứu.

## Cập nhật theo annotations

Đã rút Phụ lục A–B, các đoạn mô tả NLP/fusion, kế hoạch đánh giá và giới hạn; bỏ lời nhận định cũ về phạm vi kiểm tra biên soạn. Phần kiểm phần mềm trình bày ngắn; dữ liệu AI đã được nhóm kiểm tra và lỗi gửi lúc mất mạng đã hết được ghi theo xác nhận người dùng ngày 10/11/2026. Không tạo kết quả thực nghiệm hoặc hồ sơ Android mới.

Bản PDF sau annotations: 170 trang, thân bài 99 trang; Phụ lục A 2 trang, Phụ lục B 24 trang. Hai bản in đạt kiểm hình/bảng/trích dẫn, font và rà ảnh render; giữ đủ 224 bản ghi điện thoại. Xem [biên bản và receipt mới](../../report/audit/annotation-compaction-2026-11-10.md).

## Sắp xếp hình theo yêu cầu tiếp theo

Bỏ trang minh chứng bài báo từ bản tác giả. Các hình theo số cũ B.3–B.9 chuyển về Chương 2: CDM/LDM/PDM ở mục mô hình dữ liệu; Docker, trạng thái, điều phối và tiếp nhận thủ công ở phần triển khai. Hình 4.1–4.2 cùng một hàng; Hình 3.3–3.5 dùng bố cục hai hình trên, một hình cùng chiều rộng căn giữa dưới. Giữ nhãn và tham chiếu tự động.

Bản sau sắp xếp hình: 170 trang, thân bài 107 trang; bảy sơ đồ đã chuyển từ phụ lục về thân bài. [Biên bản và receipt](../../report/audit/figure-placement-2026-11-10.md).

## Biên tập tiếp theo theo 13 annotations

Đã rút tiếp văn phong, thống nhất K cho số láng giềng và k cho chỉ số cụm, bỏ ngày truy cập lặp và sửa điểm ngắt URL. Đã đối chiếu thuyết minh cho các thước đo; không có căn cứ để đặt ngưỡng đạt định lượng mới nên bỏ qua phần ngưỡng trong phiên này. Các trạng thái bỏ qua/chờ bổ sung/chấp nhận dữ liệu ở đầu tài liệu và các bảng trên đã cập nhật theo annotations.

Bản hiện hành: **165 trang, thân bài 102 trang**, giữ **50 hình, 52 bảng, 29/29 trích dẫn** và đủ **224 bản ghi/32 cấu hình điện thoại**. Build/check một/hai mặt, tham chiếu hình/bảng, font, văn bản, ảnh render và `git diff --check` đạt. Ngày ký/nhận xét/chữ ký để bổ sung trên bản giấy; không chạy thêm thực nghiệm hoặc viết lại tóm tắt. [Biên bản và receipt mới](../../report/audit/annotation-followup-2026-11-10.md).
