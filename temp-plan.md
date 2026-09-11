
# Kế hoạch chỉnh sửa camera-ready theo phản hồi ISDS-2026

## 1. Mục tiêu và các quyết định đã chốt

Chuẩn bị bản camera-ready giải quyết đầy đủ ba reviewer, làm rõ giá trị của nghiên cứu, bổ sung đánh giá độ bền và giữ nguyên tính trung thực của các kết quả bất lợi.

- Dùng `v1.0.1` làm mốc bản đã nộp; tiếp tục từ bản hiện tại trên `clean`, bảo toàn thay đổi sau release.
- Giữ thông tin tám tác giả, tác giả liên hệ và tài trợ đã được bạn xác nhận.
- Giữ thuật toán hiện tại; sửa mô tả theo code đã sinh kết quả.
- Mọi thực nghiệm nặng: **chuẩn bị Colab hoặc hướng dẫn để nhóm tự chạy, sau đó gửi kết quả về để kiểm tra**.
- Hạn camera-ready và đăng ký theo mail: **16/09/2026**. Quy cách camera-ready cuối cùng chờ mail tiếp theo.

## 2. Chỉnh sửa nội dung và xử lý bất nhất

Lập bảng theo dõi từng ý reviewer, gồm nội dung yêu cầu, vị trí sửa, chứng cứ và trạng thái hoàn thành.

| Nhóm phản hồi                                       | Công việc                                                                                                                                                                                                                                  |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Ưu điểm và giá trị thực tiễn — R1, R3         | Giải thích lợi ích cụ thể: giới hạn cạnh theo khoảng cách, chống tăng điểm do lặp chính xác, và phát hiện lỗi lan truyền xuống điều phối. Nêu rõ các thuộc tính này không chứng minh ưu thế tổng thể. |
| Tính thực tế của dữ liệu — R1, R3               | Bổ sung bảng phân biệt nguồn địa lý tham chiếu, thành phần tổng hợp, tham số giả định và yếu tố chưa được kiểm chứng; tách riêng generator 3.0 và Candidate-4.1.                                                |
| Độ bền và giới hạn — R1, R3                     | Trình bày đầy đủ hơn các stress test sẵn có và bổ sung thí nghiệm nhiễu/lặp báo cáo ở mục 3.                                                                                                                             |
| ARI chưa phản ánh hiệu quả điều phối — R2, R3 | Phân tích lỗi tách/gộp, điểm đến giả và kết quả điều phối theo điều kiện nguồn lực; không ghép ARI của RQ1 với kết quả RQ3 vì khác bộ dữ liệu.                                                               |
| Misinformation và khả năng triển khai — R2, R3    | Làm rõ thất bại trước chiến dịch phối hợp có confidence cao, các giả định chính sách và yêu cầu kiểm chứng thực địa còn thiếu.                                                                                    |
| Thuật ngữ và baseline — R1, R3                     | Định nghĩa product/additive Louvain, product Leiden và matched-density ngay lần đầu xuất hiện; giải thích vai trò đối chứng của từng nhóm baseline.                                                                        |

Sửa những bất nhất đã được bạn đồng ý:

- Giả mã top‑k phải phản ánh code: lọc cạnh vượt ngưỡng, chọn top‑k từng đầu mút rồi đối xứng hóa.
- Mô tả chính xác lưới hiệu chỉnh riêng của product và additive.
- Thống nhất matched-density là đối chứng kiểm soát mật độ gần tương đương, không diễn giải thành bằng chứng nhân quả.
- Kiểm tra toàn bộ công thức, cấu hình và số liệu theo từng suite; không lấy các tệp kết quả cũ thuộc nghiên cứu khác làm nguồn cho bài hiện tại.
- Sửa hướng dẫn tái lập đang trỏ đến đường dẫn không còn tồn tại; xác định rõ mã nguồn lịch sử cần dùng.

Phần nguồn tham chiếu sẽ tra cứu tài liệu gốc. Do nhóm chưa có thêm snapshot hoặc xác nhận chuyên gia, không khẳng định dữ liệu đã được hiệu chuẩn theo hoạt động cứu hộ thực tế.

## 3. Gói phân tích và thực nghiệm bổ sung

### Phân tích từ kết quả hiện có

- Tổng hợp 11 tình huống RQ2: lặp chính xác, gần lặp, báo cáo mâu thuẫn, thiếu thông tin và các kiểu tấn công; trình bày độ lệch điểm, thay đổi thứ hạng và top‑k.
- Phân tích riêng ba điều kiện nguồn lực RQ3: `lean_hue`, `nominal_dual_depot`, `regional_surge`.
- Dùng các bảng lỗi phân cụm và phân công điểm đến để giải thích kết quả harm/deadline; xem đây là phân tích mô tả, không suy ra quan hệ nhân quả.
- Giữ phân tích chính RQ3 ở đơn vị **40 seed**, không coi 120 tổ hợp seed–scenario là các quan sát độc lập.
- Giữ kết quả độ nhạy 840 dòng đã có sau khi xác minh nguồn và checksum.

### Thực nghiệm mới giao nhóm chạy

Chuẩn bị một notebook stress test RQ1 với cấu hình cố định:

| Yếu tố          | Điều kiện bổ sung                                                                       |
| ----------------- | ------------------------------------------------------------------------------------------- |
| Đối chứng      | Dữ liệu nguyên bản                                                                      |
| Nhiễu GPS        | Nhiễu Gaussian độc lập theo hai trục địa phương, độ lệch chuẩn 100 m và 300 m |
| Nhiễu thời gian | Nhiễu Gaussian vào timestamp, độ lệch chuẩn 15 phút và 60 phút                     |
| Lặp chính xác  | Nhân mỗi payload thành tổng cộng 2 và 5 bản, chỉ thay mã vận chuyển/báo cáo    |

Các mức trên là **mức stress tổng hợp bổ sung**, không phải ước lượng sai số thực địa. Mỗi điều kiện chỉ thay một yếu tố.

- Chạy trên 40 test run RQ1 đã khóa, với năm phương pháp: product Louvain, additive Louvain, matched-density additive, product Leiden và geo-time DBSCAN.
- Tổng cộng **1.400 lượt phân cụm**; không chạy lại tìm kiếm tham số.
- Các phương pháp dùng cùng dữ liệu nhiễu theo seed. Lưu ánh xạ bản sao tới báo cáo gốc; ánh xạ này chỉ phục vụ đánh giá.
- Đo ARI/pairwise F1 trên báo cáo gốc để so sánh nhất quán; kèm chỉ số trên toàn bộ báo cáo, tỷ lệ điểm đến giả, hấp thụ/từ chối fake và mật độ đồ thị.
- Báo cáo thay đổi so với đối chứng bằng bootstrap ghép cặp theo run; đánh dấu đây là phân tích bổ sung sau phản biện, không đổi cấu hình dựa trên kết quả test.
- Không chạy mới toàn bộ RQ2/RQ3 nếu kiểm tra chứng cứ hiện có không phát hiện lỗi ảnh hưởng kết luận.

Notebook có bước kiểm tra môi trường, smoke test một run, checkpoint/resume và xuất ZIP gồm CSV theo run, cấu hình, seed, checksum, phiên bản thư viện, log và notebook đã chạy. Dự toán thời gian dựa trên smoke test của nhóm; không đưa ra thời lượng giả định như số đo thực tế.

## 4. Trình tự thực hiện và tiêu chí nghiệm thu

1. **Khóa mốc và truy xuất chứng cứ:** ghi commit, kiểm tra checksum, đối chiếu từng số liệu trong bài với CSV; xác định nguồn code lịch sử của notebook.
2. **Sửa nội dung và chuẩn bị Colab:** hoàn thành phần thuật ngữ, baseline, giới hạn, giả mã và hướng dẫn chạy; kiểm tra nhẹ trước khi giao nhóm.
3. **Nhóm chạy thực nghiệm:** gửi ZIP kết quả và notebook đã thực thi. Kết quả thiếu seed, sai cấu hình hoặc sai nguồn phải được báo lại, không âm thầm gộp vào bài.
4. **Tích hợp kết quả:** sinh bảng/hình từ dữ liệu đã kiểm tra; giữ cả kết quả không cải thiện hoặc bất lợi; cập nhật phần bàn luận và phản hồi từng reviewer.
5. **Đóng gói:** dựng PDF bằng XeLaTeX, kiểm tra công thức, trích dẫn, bảng/hình, số trang và metadata theo hướng dẫn camera-ready khi nhận được.

Bàn giao gồm bản thảo/PDF, bảng phản hồi reviewer bằng tiếng Anh, notebook và hướng dẫn cho nhóm, artifact thực nghiệm đã kiểm tra, cùng checkpoint ghi phần hoàn thành và phần còn chờ.

Không thay đổi API sản phẩm. Giao diện bổ sung chỉ gồm cấu hình chạy và định dạng artifact nghiên cứu.

## 5. Các điểm phải hỏi lại trước khi xử lý

- Nếu phát hiện code thực thi khác công thức theo cách làm thay đổi kết quả hoặc kết luận: báo bằng chứng và các phương án trước khi sửa.
- Nếu cần đổi thuật toán, tham số đã khóa, sinh lại dữ liệu nền hoặc mở rộng thực nghiệm ngoài gói trên: hỏi lại bạn.
- Nếu nhóm không kịp trả kết quả trước hạn: hỏi bạn về phương án nộp; không ghi thực nghiệm chưa chạy thành kết quả.
- Khi có quy định camera-ready mới, nếu cần cắt nội dung khoa học, thay metadata hoặc thay đổi gói nộp: xác nhận phần bị ảnh hưởng trước khi làm.
- Việc nộp bài, đăng ký hội nghị hoặc phát hành release mới là bước riêng cần chỉ đạo của bạn.
