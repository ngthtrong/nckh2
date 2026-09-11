
# Kế hoạch hoàn thiện camera-ready theo CCIS/Springer và LTP

## 1. Quy định nộp bài đã xác nhận

Dùng [remind_for_camera_ready.md](/home/ngthtrong/nckh2/docs/camera-ready/remind_for_camera_ready.md:5) làm hướng dẫn riêng cho bài Springer CCIS:

- Hạn cuối: **16/09/2026**; múi giờ chưa được ghi nên hoàn tất nội bộ chậm nhất ngày 15/09 và không chờ sát hạn.
- Giới hạn **12–15 trang nghiêm ngặt**, bao gồm tài liệu tham khảo.
- Nộp bằng tài khoản tác giả trên EasyChair:

  1. Một ZIP chứa toàn bộ LaTeX source cần thiết.
  2. PDF camera-ready tương ứng chính xác với source ZIP.
- Copyright/LTP là tài liệu riêng, phải hoàn thành và gửi sớm nhất có thể.
- Không nộp response letter vì hướng dẫn không yêu cầu; tài liệu phản hồi tiếp tục giữ nội bộ.

## 2. Công thức, biểu đồ và bố cục 15 trang

### Công thức

- Định nghĩa tại chỗ mọi ký hiệu còn thiếu: chỉ báo ảnh; các scale \(\sigma,\tau_t,\tau_F,\tau_E\); trọng số \(\alpha,\beta,\gamma,\omega\); các thành phần \(\bar E_k,\bar F_k,\bar N_k,\bar V_k\); và miền của \(P_k\).
- Đánh số liên tục bốn nhóm công thức chính: confidence, contextual similarity, graph affinities và priority.
- Nêu các ràng buộc trọng số và giới hạn \(0\le P_k\le\mu\).
- Bỏ công thức rút gọn bị lặp; thu gọn phần khai triển lại công thức trong pseudocode thành tham chiếu phương trình.
- Đối chiếu công thức với code sinh kết quả; không thay đổi thuật toán.

### Biểu đồ RQ1

- Thay bảng stress RQ1 bằng heatmap 6 stress × 5 phương pháp.
- Mỗi ô biểu diễn mean \(\Delta\)ARI stress-minus-control, có dấu và bốn chữ số thập phân.
- Nguồn duy nhất là `rq1_stress_paired_effects.csv`, lọc `metric=ari_original`.
- Xuất PDF vector, chữ tối thiểu 7 pt, đọc được khi in grayscale.
- Giữ trong văn bản kết quả Product Louvain 5×: \(\Delta=-.6108\), CI \([-.6318,-.5881]\).
- Không dùng heatmap hoặc CI để tuyên bố ưu thế thống kê giữa các phương pháp.

### Cắt phần trùng lặp

- Xóa hai hình RQ2/RQ3 và bảng headline RQ2/RQ3 vì kết quả chính đã có trong văn bản và bảng chi tiết.
- Rút đoạn mở đầu Results, caption dài và các câu lặp số liệu.
- Giữ pipeline figure, bảng benchmark RQ1, bảng robustness RQ2 và bảng sensitivity.
- Không chỉnh lề, font toàn bài hoặc cấu trúc `llncs` để ép số trang.
- Tiêu chí cuối là đúng 15 trang.

## 3. Tác giả và LTP

Theo xác nhận của bạn, danh sách tám tác giả đã được ban tổ chức chấp thuận:

- Giữ đủ tám tác giả hiện tại và lưu lại bằng chứng chấp thuận của ban tổ chức.
- Chỉ **Thanh-Trong Nguyen** được đánh dấu corresponding author.
- Danh sách và thứ tự trên bài, EasyChair và LTP phải giống hệt nhau.
- Điền vào [LTP Singapore](/home/ngthtrong/nckh2/docs/camera-ready/SNCS_ProceedingsPaper_LTP_ST_SN_Singapore.docx.md:9):

  - tên bài chính xác theo camera-ready;
  - đủ tám họ tên tác giả;
  - corresponding author: Thanh-Trong Nguyen;
  - giữ nguyên tên hội nghị và volume editors đã được điền sẵn.
- Thanh-Trong Nguyen ký thay mặt toàn bộ tác giả sau khi có sự đồng thuận của nhóm.
- In, ký tay, ghi ngày/địa chỉ/email và scan thành PDF rõ nét; không dùng chữ ký đánh máy.
- Sau khi ký, không thay đổi title, danh sách, thứ tự hoặc corresponding author nếu chưa xin phép lại.

## 4. Chuyển quyền nội dung từ CC BY sang LTP

Áp dụng lựa chọn “xóa CC BY cho toàn bộ content” từ trạng thái hiện tại trở đi:

- Không sửa lịch sử hoặc tag `v1.0.1`; giấy phép đã cấp cho snapshot đó không thể bị thu hồi hồi tố.
- Thay nội dung `LICENSE-CONTENT` bằng thông báo quyền mới:

  - không còn cấp CC BY cho manuscript, bảng, hình hoặc synthetic result artifacts;
  - camera-ready contribution chịu điều khoản của Springer LTP;
  - các nội dung phi phần mềm khác được bảo lưu quyền nếu không có thông báo riêng;
  - nội dung bên thứ ba tiếp tục theo giấy phép gốc.
- Giữ `LICENSE` MIT nhưng ghi rõ MIT chỉ áp dụng cho source code, không áp dụng cho manuscript, figures, tables, datasets hoặc result artifacts.
- Xóa câu khẳng định manuscript/artifact là CC BY trong Data and Code Availability.
- Không thay đổi giấy phép hoặc metadata của bản Zenodo `v1.0.1` đã phát hành.
- Không tạo release camera-ready mới trước khi thống nhất được metadata giấy phép cho gói chứa cả code MIT và content không còn CC BY.

## 5. Chuẩn bị source ZIP và accessibility

Tạo gói nộp trong thư mục staging sạch, chỉ gồm:

- `main.tex`, `references.bib`, `main.bbl`;
- `llncs.cls`, `splncs04.bst`;
- các hình thực sự được tham chiếu trong bản cuối;
- các source phụ thực sự được `\input` hoặc cần cho build.

Loại khỏi ZIP:

- `.aux`, `.log`, `.out`, cache và file tạm;
- PDF/hình cũ không còn sử dụng;
- notebook, checkpoint, CSV kết quả và tài liệu nội bộ;
- reviewer response và audit/checkpoint nội bộ.

Chuẩn bị alt text cho pipeline và heatmap vì [LTP yêu cầu alt text khi nộp hình](/home/ngthtrong/nckh2/docs/camera-ready/SNCS_ProceedingsPaper_LTP_ST_SN_Singapore.docx.md:65). Chỉ upload file alt-text riêng nếu EasyChair hoặc ban tổ chức cung cấp trường/biểu mẫu tương ứng.

## 6. Kiểm tra bàn giao

- Sinh heatmap từ CSV và kiểm tra đủ đúng 30 ô.
- Chạy audit đầy đủ RQ1/RQ2/RQ3; không thay đổi checksum artifact gốc.
- Build lại từ chính source ZIP đã giải nén trong môi trường sạch.
- Xác nhận PDF tạo từ ZIP giống nội dung PDF upload.
- Kiểm tra:

  - đúng 15 trang;
  - không lỗi LaTeX, citation/reference chưa xác định hoặc overfull box;
  - công thức được đánh số liên tục và mọi biến được giải thích;
  - hình vector, caption đúng vị trí và đọc được ở 100%/grayscale;
  - tám tác giả và một corresponding author;
  - acknowledgment, funding và disclosure đầy đủ;
  - không có nội dung kể lại quá trình phản biện.
- Chạy `git diff --check`, rà diff và cập nhật checkpoint.
- Nhóm duyệt PDF, source ZIP, LTP scan và alt text trước khi upload.
- Commit, push, release, ký LTP và upload EasyChair là các bước riêng; không tự động thực hiện.
