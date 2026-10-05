# Khung báo cáo tổng kết NCKH sinh viên

Khung dựa trên [lựa chọn LaTeX](lua-chon-khung-latex.md), [tổng hợp hướng dẫn](tong-hop-huong-dan.md) và mẫu trong `guideline/`. Đây là dự án để viết báo cáo, chưa phải báo cáo hoàn chỉnh hoặc hồ sơ đủ điều kiện nộp.

## Biên dịch

Chạy từ thư mục `report/`:

```bash
make doctor              # Kiểm tra công cụ và phông
make content             # Bản nháp nội dung
make content-twoside     # Bản nháp in hai mặt
make smoke               # Bản thử bìa dài, tiếng Việt, bảng dài, công thức, PDF
make deliverables        # Bốn PDF riêng: bản tin và báo cáo tóm tắt Việt/Anh
make check               # Liệt kê placeholder, số trang thân bài và cảnh báo
make check-release       # Kiểm tra điều kiện bản đầy đủ; ban đầu sẽ thất bại
make full                # Biên dịch lại nội dung, kiểm tra, rồi chèn hồ sơ
make full-twoside        # Bản đầy đủ in hai mặt
make clean               # Xóa riêng thư mục đầu ra build/
```

PDF nằm trong `build/<chế-độ>/`, ví dụ `build/content/content.pdf`, `build/smoke/smoke.pdf`, `build/summary-en/summary-en.pdf`. Chế độ hai mặt dùng thư mục có hậu tố `-twoside`; tên PDF giữ nguyên. `build/` được bỏ qua bởi Git.

`Makefile` gọi Python chuẩn và XeLaTeX nhiều lượt, chạy biber/BibTeX ở giữa và biên dịch thêm nếu tham chiếu còn cần cập nhật. Không phụ thuộc `latexmk`. Khi đã có `biblatex`, `biber`, `latexmk`, có thể chạy `latexmk -r latexmkrc -xelatex main.tex` để rà soát riêng; đầu ra ở `build/latexmk/main.pdf`. Dùng `make full` để thực hiện đầy đủ kiểm tra và ghép hồ sơ.

Yêu cầu lõi: XeLaTeX, KOMA-Script, fontspec, polyglossia, unicode-math, geometry, setspace, scrlayer-scrpage, graphicx, booktabs, longtable, tabularx, TikZ, pdfpages, hyperref, bookmark; Python 3.9+; phông Times New Roman đủ bốn kiểu.

Phông được tìm bằng fontconfig hoặc `/mnt/c/Windows/Fonts/`. Máy khác cần cài Times New Roman hợp lệ và chạy `fc-cache`; build dừng nếu không tìm được phông. Không đưa các tệp phông vào repository. Gói `texlive-science` dành cho thuật toán/đơn vị khi cần; bật các gói tương ứng trong `template/packages.tex` sau khi đã cài.

## Cấu trúc và bắt đầu viết

- `main.tex`: giữ thứ tự các khối của quyển báo cáo; chỉnh nội dung ở các tệp được gọi.
- `template/`: lớp KOMA `scrreprt`, phông, gói, lệnh ngữ nghĩa và tài liệu tham khảo.
- `config/metadata.tex`: nguồn duy nhất cho thông tin hành chính. Tên đề tài hiện lấy từ bản nháp bản tin, cần xác nhận bằng thuyết minh đã duyệt; các trường chưa biết có `TODO`.
- `frontmatter/`: hai bìa, thành viên, từ viết tắt, ba trang thông tin. Mục lục và danh mục bảng/hình sinh tự động.
- `chapters/`: Mở đầu, bốn chương theo đề xuất và Kết luận/kiến nghị. Mỗi chương có `chapter.tex` và `sections/`.
- `bibliography/`: nguồn trích dẫn; `appendices/`: phụ lục khoa học.
- `assets/`: hình và nguồn sơ đồ; `generated/`: bảng/số liệu sinh từ artifact có nguồn gốc.
- `evidence/`: bản thuyết minh đã duyệt và minh chứng sản phẩm; tách khỏi phụ lục khoa học.
- `deliverables/`: bốn điểm vào PDF riêng; `content/` được dùng lại nguyên tệp ở cuối bản đầy đủ.
- `word/`: hướng dẫn chuẩn bị Word song song; `scripts/`: build và kiểm tra.

Bước viết đầu tiên là điền metadata, danh sách thành viên và thay ba biểu mẫu đầu quyển bằng mẫu chính thức. Sau đó thay từng `\DraftNote{...}` bằng nội dung đã kiểm chứng. Mở đầu giữ đủ sáu mục; Kết luận và kiến nghị giữ cả hai phần.

Ba biểu mẫu đầu quyển và bốn sản phẩm riêng hiện chỉ có khung tạm. Nguồn không cung cấp đủ mẫu chính thức; không gọi các khung này là đúng mẫu. Đã dành vùng nhận xét và hai chữ ký chủ nhiệm, một chữ ký GVHD tại các vị trí HD yêu cầu. Chưa tạo `reference.docx`, PDF phê duyệt, chữ ký hoặc số liệu nghiên cứu.

## Quy ước hình thức

Thân bài: A4, Times New Roman 13 **bp** (point 1/72 inch), giãn dòng `1.3`, lề vật lý trái 30 mm, phải/trên/dưới 20 mm. Toán dùng Latin Modern Math. Bìa dùng khung đôi và vùng nội dung căn giữa riêng (lề 25 mm), đối chiếu với mẫu B; khôi phục lề quy định ở phần nội dung.

Phần đầu đánh số La Mã sau hai bìa; từ Mở đầu dùng số Ả Rập. Không chèn trang trắng để mở chương ở trang lẻ. Hai mặt giữ lề vật lý trái/phải, không tự đổi lề đóng gáy. Tiêu đề serif có tiền tố “Chương”; hình, bảng và công thức đánh số theo chương. Tiêu đề 16/14/13 bp, vị trí số trang giữa chân trang, thụt đầu dòng 1 cm là quy ước của dự án, không phải các yêu cầu bổ sung của guideline.

Dùng nhãn `chap:`, `sec:`, `fig:`, `tab:`, `eq:` và `\label`/`\ref`, không nhập số thủ công. `\SourceNote{...}` ghi nguồn, `\DraftNote{...}` đánh dấu phần cần hoàn tất. Không lấy số liệu mẫu kiểm tra làm kết quả nghiên cứu.

Giãn dòng đã thiết lập trong khoảng cho phép; vẫn cần đối chiếu bằng một trang Word cùng nội dung trước khi nộp. Bản kiểm tra PDF không thay thế rà soát trực quan hoặc kiểm tra sao chép/tìm kiếm tiếng Việt trong trình đọc PDF thông dụng.

## Tài liệu tham khảo

Build tự chọn **biblatex + biber** khi cả hai có sẵn, dùng author–year, `sorting=nyt`, locale `vi_VN`, in ba nhóm theo thứ tự:

1. `legal`: văn bản pháp quy, tệp `legal.bib`.
2. `books`: sách, báo, tạp chí, tệp `books.bib`.
3. `articles`: bài viết của tác giả, tệp `articles.bib`.

Gắn đúng một keyword tương ứng, ví dụ `keywords = {articles}`. Chỉ đưa tài liệu thực sự dùng vào danh mục; `\citep{key}` trích dẫn trong ngoặc, `\citet{key}` trích dẫn tác giả trong câu. `references.bib` dành cho các mục bổ sung hoặc nhập từ nguồn khác, vẫn phải gắn nhóm. Cần thống nhất ranh giới nhóm và kiểm tra thứ tự tên Việt/Anh bằng tay.

Có thể chọn rõ backend:

```bash
make content BIBLIOGRAPHY=biblatex
make smoke BIBLIOGRAPHY=bibtex
```

Phương án dự phòng là BibTeX + natbib, ba tệp `.bib` và ba danh mục riêng, `plainnat` sắp xếp theo tác giả. Phương án này in toàn bộ mục trong ba tệp nhóm, nên chỉ để tài liệu đã dùng và không sử dụng `references.bib`. BibTeX không đảm bảo thứ tự chữ cái tiếng Việt; phải kiểm tra thủ công. Mục Knuth minh họa chỉ nằm trong `template/smoke.bib`, không xuất hiện trong báo cáo chính.

## Bản đầy đủ và hồ sơ

Chỉnh `evidence/manifest.yaml` theo [quy ước hồ sơ](evidence/README.md): xác nhận danh sách cam kết, mẫu chính thức, bản phê duyệt và từng minh chứng. Tệp dùng cú pháp JSON hợp lệ trong YAML 1.2; Python đọc được mà không cần PyYAML. `products` có các mục thuộc nhóm I–III đúng cam kết, được xếp I → II → III. Nhóm không đăng ký không cần hồ sơ giả để lấp chỗ.

`make full` luôn biên dịch lại nội dung hiện tại trước khi kiểm tra: không còn placeholder trong các tệp nội dung/metadata, đủ 50 trang từ Mở đầu tới hết Kết luận và kiến nghị, không có lỗi tham chiếu hoặc tràn khung, đã xác nhận mẫu và có đủ PDF đã kiểm tra. Ban đầu các điều kiện này chưa đạt, nên bản đầy đủ bị chặn chủ động. `make check` cho phép bản nháp ngắn và liệt kê phần còn thiếu; `make check-release` kiểm tra bản `build/content/` đã biên dịch gần nhất.

Sau phụ lục khoa học: thuyết minh đã phê duyệt → minh chứng I–III → bản tin Việt/Anh → báo cáo tóm tắt Việt/Anh. Video nộp riêng. Trang scan giữ khổ gốc, không phủ số trang lên dấu/chữ ký; đánh số hiển thị của báo cáo dừng ở trước scan, scan giữ số trang gốc. LaTeX vẫn tính trang logic cho mục lục/bookmark; phần sản phẩm nhóm IV tiếp tục số trang logic sau scan. Cần kiểm tra trang đầu mỗi bookmark, hướng trang và khả năng đọc trong PDF cuối.

Kiểm tra tự động chỉ xác nhận tệp tồn tại/header PDF và các cờ do người soạn xác nhận; không tự xác minh chữ ký/dấu, chất lượng nghiên cứu hoặc tính đầy đủ thực tế của cam kết. Bản đầy đủ vẫn cần xem và đối chiếu hồ sơ thật trước khi bàn giao. Word chưa tự xuất; xem [quy trình Word](word/README.md).

## Kiểm tra kỹ thuật đã thực hiện

Ngày 06/10/2026: biên dịch bản nội dung, bản hai mặt, bốn PDF riêng và bản thử kỹ thuật. Kiểm tra A4, phông nhúng Times New Roman/Latin Modern Math, thân bài 13 bp, lề trái 30 mm và lề phải 20 mm; xem hai bìa với tên dài; bảng nhiều trang, công thức, tham chiếu và PDF mẫu được chèn. Khung chính có 6 trang thân bài mẫu, chưa đáp ứng yêu cầu 50 trang. Bộ kiểm tra bản đầy đủ từ chối placeholder và PDF minh chứng còn thiếu.
