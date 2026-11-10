# Đối chiếu nhận xét và phần còn cần bằng chứng — 10/11/2026

Nguồn: [nhận xét Hội đồng](../../tmp.md), danh sách BC/ND/MC người dùng cung cấp, [hồ sơ kết quả local](outputs/local-report-update-20261110/README.md) và [hồ sơ chỉnh sửa tiếp theo](outputs/remaining-revision-20261110/README.md). “Đã sửa” dưới đây là trạng thái biên tập/cài đặt trong repo, không thay xác nhận của Hội đồng hoặc nghiệm thu vận hành.

## Các quyết định phạm vi đã áp dụng

- Ảnh có **cả hai nguồn: nhóm tự chụp và thu thập từ web**, theo xác nhận của nhóm. Không có đủ ánh xạ từng ID để suy số lượng từng nguồn, quyền sử dụng ảnh web hoặc tập camera độc lập.
- **MC-06 và MC-08: SKIPPED_BY_USER.** Không tiếp tục chẩn đoán PTQ/QAT, đo lặp CPU–điện thoại, pin/RAM. Các kết quả và giới hạn lịch sử vẫn được trình bày đúng.
- **NLP/fusion đã cập nhật vào mobile do nhóm khác phụ trách**, theo xác nhận của nhóm. Báo cáo đã ghi nhận; metric pilot vẫn là kết quả offline. Bản dịch tiếng Việt và nhãn AI đã được nhóm kiểm tra, được nhóm đánh giá gần cách diễn đạt cứu hộ tiếng Việt. Việc còn thiếu ở MC-12 là bằng chứng bàn giao/kiểm xuyên luồng, không phải yêu cầu cài lại nhánh mobile trong repo này.
- Đã thực hiện khắc phục phần mềm và kiểm thử mới bằng nguồn lực local hiện có. Không có thiết bị Android kết nối; không ghi nhận đã thử SMS hoặc mạng di động thật.
- **MC-20 và MC-21: FUTURE_WORK_ONLY.** Chỉ viết hướng phát triển điều phối xét chi phí di chuyển và thí điểm cùng đơn vị cứu hộ; không triển khai/thí điểm trong đợt này.

## Bố cục và hình thức

| Mã | Trạng thái hiện tại |
|---|---|
| BC-01 | Đã rút Chương 2; chuyển chi tiết phân lớp, CSDL/API, thao tác, giao diện và bốn lưu đồ xuống phụ lục, giữ nhãn/hình gốc và đường tra cứu. |
| BC-02 | Đã cô đọng Kết luận, giữ kích thước chữ và sơ đồ; kiểm lại bố cục PDF một/hai mặt. |
| BC-03 | Đã dùng số trang liên tục của quyển cho ba minh chứng sản phẩm; trang đầu bản tác giả bài báo được bỏ theo yêu cầu mới. Bản gốc không bị sửa. Hồ sơ công bố chính thức còn ở MC-19. |
| BC-04 | Đã cập nhật mục lục, danh mục, nhãn và tham chiếu; bộ kiểm đối chiếu 50 hình, 52 bảng với PDF. |
| BC-05 | Đã thống nhất font URL theo văn bản trong danh mục IEEE, thêm hai nguồn gốc và kiểm trích dẫn có số. Không suy metadata còn thiếu của chapter từ sách. |
| BC-06 | Đã dùng k cho số láng giềng/top-k; giữ riêng chỉ số cụm và vị trí cắt NDCG. |
| BC-07 | Bảng và giá trị sinh tự động dùng dấu phẩy ở tiếng Việt; biểu mẫu tiếng Anh đổi sang dấu chấm, giữ phân biệt phần trăm/điểm phần trăm và đơn vị. |
| BC-08 | Đã build/check hai bản in, kiểm font, văn bản và ảnh render; receipt cuối trong hồ sơ chỉnh sửa. Đây không phải kiểm hồ sơ phát hành đủ chữ ký. |

## Nội dung báo cáo

| Mã | Nội dung đã sửa và giới hạn còn lại |
|---|---|
| ND-01 | Rút Chương 2, giữ kiến trúc/luồng chính và chính sách gửi trong thân bài; chi tiết ở phụ lục. |
| ND-02 | Viết lại Kết luận theo đóng góp, câu trả lời RQ, giới hạn và hướng phát triển. |
| ND-03 | Giảm chi tiết mã/lưu trữ/thao tác ở thân bài, tập hợp giới hạn chung và dùng tham chiếu. Giữ định danh cần thiết để phân biệt các lần đo. |
| ND-04 | Bổ sung AlleyFloodNet (2025) và EmergencyNet (2020) từ nguồn gốc, phân biệt nhiệm vụ/góc nhìn. |
| ND-05 | Bổ sung đối chiếu đầu vào, đầu ra, mô hình tại biên, kết nối/chống trùng/điều phối; không tuyên bố ưu thế thuật toán chưa xác lập. |
| ND-06 | Bổ sung bảng chỉ tiêu đo ảnh/văn bản/truyền tin/phân cụm/xếp hạng; giữ mục đích giảm thiệt hại ở mức dài hạn, không đặt ngưỡng hồi cứu. |
| ND-07 | Đồng bộ DistilBERT frozen/T2, số tái chạy 52,29% và tích hợp mobile do nhóm khác xác nhận; corpus gốc/gold còn ở MC-09–MC-10. |
| ND-08 | Phân biệt tiếp nhận nhiều trường, heuristic và fusion học được; ghi nhận mobile cập nhật, không chuyển metric offline thành metric APK. |
| ND-09 | Đồng bộ bảng đối chiếu thuyết minh với kết quả local, nguồn ảnh hỗn hợp, mobile, sửa phần mềm và phạm vi bỏ qua/hướng phát triển. |
| ND-10 | Giữ rõ split hiện có và lineage chưa xác nhận; grid mới chọn bằng validation, chưa thay tập test độc lập. MC-03 còn mở. |
| ND-11 | Làm rõ Accuracy/F1/lỗi nặng và từng phiên đo; thử pruning cao hơn không thay asset nguyên mẫu. |
| ND-12 | Giữ kết quả có giới hạn của RQ1–RQ3: chưa xác lập Product vượt Additive; chưa xác lập lợi ích xếp hạng chung; revised thua nearest-first trong phép thử đã có. |
| ND-13 | Tách mô tả Android lịch sử, raw còn thiếu và các kiểm thử mới. Không gán log Linux mới cho Case 8 cũ. |
| ND-14 | **Còn chờ** ngày ký thực tế, nội dung nhận xét/chữ ký người hướng dẫn và hồ sơ xác nhận. Ảnh thẻ đã có, không yêu cầu chèn lại. |
| ND-15 | Đã bổ sung mục đích nghiên cứu/đào tạo, quyền truy cập, trách nhiệm xác minh và dữ liệu người yếu thế; thí điểm chỉ ở hướng phát triển. |
| ND-16 | Đồng bộ thông tin kết quả, bản tin/tóm tắt Việt–Anh, bảng đối chiếu thuyết minh, Kết luận và minh chứng. |

## Bằng chứng đã bổ sung, còn thiếu hoặc loại khỏi đợt này

| Mã | Trạng thái | Việc còn cần nếu muốn khép nhận xét bằng bằng chứng |
|---|---|---|
| MC-01 | Một phần | Đã sửa mô tả nguồn hỗn hợp. Còn danh mục ID–nguồn–sự kiện–thời điểm; căn cứ sử dụng ảnh web và thông tin ảnh tự chụp. |
| MC-02 | Còn thiếu | Nhãn độc lập, chỉ số đồng thuận, hồ sơ bất đồng/phân xử và thẩm định ca khó/lỗi nặng. |
| MC-03 | Còn thiếu | Checksum/lineage split lúc train hoặc protocol/tập xác nhận độc lập theo nguồn/sự kiện. Chọn validation trong grid mới không thay bằng chứng này. |
| MC-04 | Một phần | Nhóm xác nhận có ảnh tự chụp; chưa xác định tập camera/thực địa độc lập với điều kiện chụp, nhãn và kết quả Android. |
| MC-05 | Đã bổ sung | McNemar exact, cặp đúng→sai/sai→đúng, CI và Holm từ dự đoán lưu. Giới hạn độc lập mẫu vẫn theo MC-03. |
| MC-06 | SKIPPED_BY_USER | Không tiếp tục tìm nguyên nhân suy giảm PTQ/QAT trong đợt này. Không tuyên bố nguyên nhân đã được xác định. |
| MC-07 | Đã bổ sung | Grid 5/10/20%, chọn bằng validation và test mức 5%; báo cả kết quả suy giảm, không thay model nguyên mẫu. |
| MC-08 | SKIPPED_BY_USER | Không tiếp tục đo lặp CPU–điện thoại, pin/RAM. Không bổ sung kết luận hiệu năng/tiêu thụ mới. |
| MC-09 | Còn thiếu | Bản dịch/nhãn AI đã được nhóm kiểm tra và đánh giá gần cách diễn đạt cứu hộ tiếng Việt. Đánh giá tiếp theo trên tin thu nhận trực tiếp, có nguồn và nhãn độc lập; giữ đúng nguồn gốc dẫn xuất của dữ liệu hiện có. |
| MC-10 | Một phần | Đã có pilot DistilBERT frozen/T2 và cập nhật mobile theo xác nhận. Còn test tiếng Việt gốc/gold, lỗi từng loại, nhãn span nếu giữ chức năng trích xuất. |
| MC-11 | Một phần | Đã có đối chứng/ablation offline. Còn gold ghép cặp chung nhiệm vụ và bằng chứng thiếu/mâu thuẫn nguồn, chuyển xác minh; CI hiện chưa xác lập ưu thế fusion. |
| MC-12 | Đã ghi nhận tích hợp; chờ bàn giao | Nhóm mobile khác cung cấp phiên bản APK/commit/model, contract request/urgency/E_i và log tới đầu ra phân cụm/xếp hạng. Bản adapter trong repo này vẫn dùng urgency/từ khóa; không suy hành vi bản nhóm khác từ bản này. |
| MC-13 | Đã cài đặt và kiểm hồi quy | Khử bản sao exact trước quantile/top-k, giữ mọi ID gốc; 3 kiểm thử bao gồm nhân bản 2/5 lần, nội dung khác và hàng xem xét. Sai gộp/sai tách trên dữ liệu thật/gần trùng chưa được xác lập. |
| MC-14 | Còn thiếu | Báo cáo thực hoặc kịch bản được xác nhận nghiệp vụ, nhãn sự kiện/ưu tiên độc lập, thiếu/đến muộn/sai vị trí/bản sao và đối chứng cùng điều kiện. Chưa chạy đánh giá mới. |
| MC-15 | Còn thiếu | Vector RQ2 đủ độ chính xác hoặc lần tái lập đầy đủ đầu vào/tie/phép kiểm để xử lý 3 raw p Spearman và 5 Holm còn sai lệch. |
| MC-16 | Đã sửa và kiểm mới trên local | Sáu hồi quy trước sửa đều lỗi, sau sửa đều đạt; 284 Flutter đạt (3 bỏ qua), 78 backend đạt, 2 kịch bản Linux–backend đạt. Theo xác nhận mới của người dùng, lỗi gửi khi mất mạng đã hết. Giữ kết quả FAIL lịch sử và không tạo thêm số đo/log Android. |
| MC-17 | Một phần | Outbox/phục hồi/HTTP qua Linux đạt; còn điện thoại trên mạng di động thật, tỷ lệ giao/latency/mất–trùng, đóng/mở, mất ACK và phản hồi muộn. Cần thiết bị/SIM; hiện không có thiết bị Android kết nối. |
| MC-18 | Còn thiếu thiết bị/bằng chứng | SMS thật từ điện thoại tới gateway/backend; phân biệt lệnh gửi, gateway nhận và backend ghi; kiểm lỗi/latency/gộp SMS–HTTP. Kiểm tự động không chứng minh SMS đã giao. |
| MC-19 | Một phần | Đã bỏ trang đầu bản tác giả khỏi quyển theo yêu cầu mới; giữ thông tin công bố trong biểu mẫu. Còn bản xác nhận/kỷ yếu gắn đúng bài và DOI/số trang chapter khi có căn cứ; không suy từ volume sách. |
| MC-20 | FUTURE_WORK_ONLY | Chỉ trình bày điều phối xét chi phí di chuyển/năng lực/thời hạn trong hướng phát triển; không cài hay chạy mới. |
| MC-21 | FUTURE_WORK_ONLY | Chỉ trình bày thí điểm với đơn vị cứu hộ, xác minh/bảo vệ dữ liệu trong hướng phát triển; không tổ chức thí điểm. |

Các phần còn cần đầu vào bên ngoài tập trung ở hồ sơ dữ liệu/nhãn/split; gold tiếng Việt; bàn giao từ nhóm mobile; dữ liệu/đầu vào RQ; thiết bị Android/SIM/gateway; hồ sơ hành chính/công bố. Không đưa điểm synthetic vào báo cáo nghiên cứu hoặc dùng chúng để thay các bằng chứng này.

## Cập nhật theo annotations

Đã rút Phụ lục A–B, các đoạn mô tả NLP/fusion, kế hoạch đánh giá và giới hạn; bỏ lời nhận định cũ về phạm vi kiểm tra biên soạn. Phần kiểm phần mềm trình bày ngắn; dữ liệu AI đã được nhóm kiểm tra và lỗi gửi lúc mất mạng đã hết được ghi theo xác nhận người dùng ngày 10/11/2026. Không tạo kết quả thực nghiệm hoặc hồ sơ Android mới.

Bản PDF sau annotations: 170 trang, thân bài 99 trang; Phụ lục A 2 trang, Phụ lục B 24 trang. Hai bản in đạt kiểm hình/bảng/trích dẫn, font và rà ảnh render; giữ đủ 224 bản ghi điện thoại. Xem [biên bản và receipt mới](../../report/audit/annotation-compaction-2026-11-10.md).

## Sắp xếp hình theo yêu cầu tiếp theo

Bỏ trang minh chứng bài báo từ bản tác giả. Các hình theo số cũ B.3–B.9 chuyển về Chương 2: CDM/LDM/PDM ở mục mô hình dữ liệu; Docker, trạng thái, điều phối và tiếp nhận thủ công ở phần triển khai. Hình 4.1–4.2 cùng một hàng; Hình 3.3–3.5 dùng bố cục hai hình trên, một hình cùng chiều rộng căn giữa dưới. Giữ nhãn và tham chiếu tự động.

Bản sau sắp xếp hình: 170 trang, thân bài 107 trang; bảy sơ đồ đã chuyển từ phụ lục về thân bài. [Biên bản và receipt](../../report/audit/figure-placement-2026-11-10.md).
