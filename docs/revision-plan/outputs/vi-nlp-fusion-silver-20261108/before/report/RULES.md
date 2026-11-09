# Quy tắc viết và trình bày báo cáo

Áp dụng cho báo cáo trong `report/`, cập nhật theo nhận xét ngày 07/11/2026. Đây là quy ước biên soạn của dự án; yêu cầu của trường được đối chiếu riêng trong [tổng hợp hướng dẫn](tong-hop-huong-dan.md) và các mẫu ở `guideline/`.

## Khổ giấy, chữ và tiêu đề

- Thân bài dùng A4, Times New Roman 13 bp, giãn dòng 1,3; lề trái 30 mm, các lề còn lại 20 mm. Không giảm chữ hoặc lề để ép nội dung vào trang.
- Cấu hình chữ và khoảng cách tập trung trong `template/ctu-report.cls` và `template/typography.tex`. Các biểu mẫu hành chính giữ cấu hình riêng theo mẫu gốc.
- Bìa và biểu mẫu dùng tọa độ cố định theo mẫu, với `twoside=false` trong cấu hình lề riêng; khi quay về thân bài, khôi phục chế độ in của quyển. Không để trang chẵn tự đảo lề làm lệch nội dung so với logo hoặc khung mẫu.
- Dùng `\chapter`, `\section`, `\subsection` theo thứ bậc; không gõ số đề mục bằng tay. Tiêu đề phải đi cùng phần nội dung tiếp theo.
- Khoảng trước/sau tiêu đề và khoảng giữa các mục liệt kê được cấu hình thống nhất trong template; không dùng dòng trống thủ công để tạo khoảng cách.
- Giữ cách viết thuật ngữ, tên mô hình, đơn vị và ký hiệu nhất quán; giải thích từ viết tắt khi xuất hiện lần đầu.

## Ngắt trang và khoảng trắng

- Chương mới và biểu mẫu độc lập được bắt đầu ở trang mới. Không thêm `\clearpage`, `\newpage`, dòng trống cưỡng bức hoặc `\vspace` âm trong thân chương để sửa một trang riêng lẻ.
- Hình và bảng thông thường dùng `[htbp]`; để LaTeX phân phối văn bản quanh chúng. Không đặt `\FloatBarrier` ngay sau từng hình/bảng hoặc tự động ở mọi section. Hình được giới thiệu trước khi xuất hiện và không trôi sang chương khác; chỉ đặt barrier riêng khi cần giữ một nhóm nội dung.
- Sơ đồ cần khổ ngang dùng `reportlandscapefigure`. Môi trường này chuyển hình sang một trang ngang phù hợp sau khi trang chữ hiện tại được lấp đầy, đồng thời dùng chung bộ đếm hình của chương.
- Với hình ngang, giới hạn đồng thời `width=\linewidth,height=\ReportLandscapeImageHeight,keepaspectratio`, dành chỗ cho chú thích. Không kéo giãn sai tỷ lệ hoặc cắt mất nội dung để thu gọn trang.
- Giữ nguyên nhóm ảnh giao diện và các ký hiệu (a), (b), (c). Cho phép phần diễn giải nối tiếp giữa các trang; không bắt buộc mỗi nhóm ảnh mở một trang mới.
- Rà soát trang trước, trang chứa hình/bảng và trang sau mỗi lần sửa. Khoảng dành cho ký tên và sơ đồ lớn cần đọc được là khoảng có chủ đích; trang chỉ còn một vài dòng do ngắt cưỡng bức cần xử lý.

## Hình, bảng và tham chiếu

- Đánh số tự động theo chương: hình và bảng có bộ đếm riêng. Danh mục hình và bảng phải sinh từ chú thích, không nhập tay.
- Mỗi hình/bảng được đánh số trong thân chương và phụ lục khoa học có đúng một `\caption` và một `\label` riêng; đặt label ngay sau caption. Dùng tiền tố `fig:` cho hình, `tab:` cho bảng. Bảng hành chính không đánh số giữ bố cục của biểu mẫu.
- Đặt chú thích hình bên dưới, tên bảng bên trên; giữ cùng kiểu chữ và khoảng cách do template quy định. Tên phải mô tả được nội dung, dữ liệu hoặc điều kiện đánh giá cần thiết.
- Giới thiệu và phân tích hình trong phần thuyết minh bằng `Hình~\ref{...}`; tham chiếu bảng bằng `Bảng~\ref{...}`. Không gõ số hình/bảng hoặc dùng số trong tên tệp làm số tham chiếu.
- Nếu một nhóm biểu đồ có nhiều caption thì mỗi biểu đồ phải có label riêng. Ký hiệu (a), (b), (c) trong một hình ghép cùng dùng số hình của caption chung.
- Sau khi thêm, xóa hoặc đổi thứ tự hình, biên dịch đến khi tham chiếu ổn định rồi đối chiếu nguồn, danh mục, số trang và chú thích trong PDF. Không chấp nhận nhãn trùng, tham chiếu chưa giải quyết hoặc hình tràn trang.

## Nội dung nghiên cứu và trạng thái công bố

- Phân biệt phần đề xuất, phần đã triển khai và kết quả đã được kiểm chứng. Giữ rõ nguồn số liệu, seed, tập dữ liệu, điều kiện đo và giới hạn; chỉnh bố cục không làm thay đổi kết quả nghiên cứu.
- Bài báo của đề tài được ghi **đã công bố** theo xác nhận của người dùng ngày 07/11/2026. Đồng bộ thông tin trong phần kết quả nghiên cứu và tóm tắt Việt–Anh qua nguồn dùng chung `frontmatter/research-body-vi.tex` và `research-body-en.tex`.
- Số tập, năm xuất bản, trang và DOI chỉ bổ sung khi có thông tin tương ứng. Trường chưa được cung cấp ghi “Chưa cập nhật”, tránh nhầm với trạng thái chưa công bố.

## Kiểm tra trước khi bàn giao

1. Chạy `make -C report content` và `make -C report content-twoside`; bản dựng nội dung cũng cập nhật bốn bản tin/tóm tắt dùng chung nguồn.
2. Chạy `make -C report check`, `python3 report/scripts/check_report.py --build-dir build/content-twoside` và `git diff --check`.
3. Kiểm tra log về tràn khung, hình quá lớn, nhãn lặp, tham chiếu/trích dẫn và phông chữ. Bộ kiểm tra đối chiếu toàn bộ hình và bảng với danh mục hiện tại; số lượng được lấy từ nguồn, không khóa cứng.
4. Xem PDF tổng thể và các trang đổi bố cục ở cả hai bản in, nhất là trang ngang, bảng nhiều trang, danh mục và biểu mẫu chứa thông tin công bố. PDF biên dịch thành công chưa thay thế kiểm tra trực quan.
5. Build một mặt tự đồng bộ `report/main.pdf` với `build/content/content.pdf`; bản hai mặt được giữ riêng. Không dùng kết quả kiểm tra hình thức để xác nhận hồ sơ nghiệm thu đã đầy đủ.
