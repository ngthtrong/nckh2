# Xác minh nguồn ngoài — 07/11/2026 (Asia/Taipei)

## Công bố bài báo (A1)

Đã tìm tiêu đề chính xác và biến thể, đối chiếu trang hội nghị và Springer. Đây là kiểm tra trạng thái hiện thời, không sửa thông tin công bố trong lần audit.

| Nguồn chính | Quan sát | Giới hạn suy luận |
|---|---|---|
| [ISDS 2026](https://isds.ctu.edu.vn/2026/) và [Authors](https://isds.ctu.edu.vn/2026/author) | Công bố kế hoạch xuất bản theo các tuyến, lịch hội nghị 14–15/11/2026 | CFP không xác nhận một paper cụ thể đã online hoặc số tập/năm của paper |
| [Springer Part I, ISBN 9789819274109](https://link.springer.com/book/9789819274109), được chuyển tới [eBook DOI cấp quyển](https://link.springer.com/book/10.1007/978-981-92-7411-6) | Hiển thị CCIS 3252, copyright 2027, thông tin eBook và bản in đặt trước | Bản in chưa phát hành không chứng minh eBook/chapter chưa online; chưa nối được paper 6444 vào chapter |
| [Springer Part II, ISBN 9789819274079](https://link.springer.com/book/9789819274079) | Hiển thị CCIS 3253, copyright 2027; trang đặt trước/ngày dự kiến tháng 12/2026 | Ngày dự kiến có khác giữa search cache và trang mở trực tiếp; không chép làm ngày xuất bản paper |

Trang Part I/II kiểm qua công cụ đọc web chưa tìm thấy mục tiêu đề paper trong phần text truy cập được. Có kết quả hiệu sách thứ cấp liệt kê tiêu đề, chỉ dùng để lần tới trang Springer, **không** làm bằng chứng xuất bản kỹ thuật. Chưa xác minh DOI chapter, số trang và ngày online của riêng bài. Trạng thái cuối cùng là **UNVERIFIED_AT_ARTICLE_LEVEL**, không phải kết luận bài chưa được chấp nhận hoặc chưa từng công bố.

`report/frontmatter/research-body-vi.tex` và audit layout ghi published đã được người dùng xác nhận ở phiên trước. Giữ provenance của xác nhận đó; khi sửa sau này cần đối chiếu minh chứng mới, không tự ghi đè thành accepted/unpublished. DOI `10.5281/zenodo.21934401` trong `CITATION.cff` là DOI artifact phần mềm, không phải DOI chapter Springer. Không tự điền CCIS 3252/3253 hay năm 2027 cho paper trước khi xác định đúng phần/chapter và phân biệt năm online với copyright.

## Căn cứ LR và ưu tiên (C7)

[WHO Interagency Integrated Triage Tool](https://www.who.int/tools/triage) mô tả công cụ phân loại bệnh nhân trong bối cảnh cơ sở y tế, gồm nhánh thường quy và mass casualty. Đây là căn cứ phạm vi để diễn giải gói LR tham chiếu, **không** xác nhận bảng tổng hợp 32 profile hoặc trọng số điều phối cứu hộ của đề tài.

Gói `products/fe/model/urgency_ei/sources/source_registry.csv` và `feature_source_map.csv` ghi nguồn cho năm dấu hiệu. Lần này đã đọc registry/mapping và trang WHO overview; **chưa tái đọc toàn văn từng PDF nguồn hoặc xác minh từng phép ánh xạ**. Phase 02 cần nối từng dấu hiệu với đoạn nguồn, giữ nội dung adapted/excluded/unclear. Không diễn giải nhận xét này thành tư vấn y tế hoặc xác nhận triển khai đầy đủ IITT.

## Ảnh cá nhân (A3)

Link có sẵn trong `report/template/forms.tex:84` được kiểm bằng plugin **Google Drive**, thao tác chỉ đọc metadata. ID `1l94xrw48SyKZvul8le54HbLgO0nCEPG_`, tên `HT34.PNG`, MIME `image/png`, kích thước 2.464.340 byte. Công cụ không xác nhận danh tính người trong ảnh; audit này chưa tải/xem nội dung. Đây là một nguồn có thể kiểm tra tiếp, chưa phải “đã có ảnh hợp lệ”.

Không gửi email, xin quyền chia sẻ, thay quyền hoặc ghi nội dung lên dịch vụ ngoài. Tra cứu dùng metadata/tiêu đề công khai, không tải bản thảo chưa công bố tới dịch vụ mô hình ngoài.

**Chỉ đạo sau khi đọc metadata:** người dùng xác nhận ảnh cá nhân sẽ được thêm sau. Dừng tìm/xác minh ảnh, giữ nguyên ô và đánh dấu A3 `DEFERRED_BY_USER`; quan sát metadata ở trên chỉ là lịch sử audit, không phải tác vụ cần tiếp tục hoặc blocker.
