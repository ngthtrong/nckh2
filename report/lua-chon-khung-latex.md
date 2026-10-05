# Lựa chọn khung LaTeX cho báo cáo tổng kết NCKH

* [ ] 

## 1. Kết luận

| Thành phần            | Lựa chọn                                                                                                                               |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Lớp nền               | **KOMA-Script `scrreprt`**, bọc trong lớp riêng `template/ctu-report.cls`                                                   |
| Trình biên dịch      | **XeLaTeX** (giống `paper/main_vi.tex`)                                                                                         |
| Phông                  | `fontspec` + Times New Roman thật; toán dùng `unicode-math` + Latin Modern Math                                                   |
| Ngôn ngữ              | `polyglossia`, `vietnamese`                                                                                                          |
| Trang, lề, giãn dòng | `geometry` (trái 3 cm; trên/dưới/phải 2 cm), `setspace` với `\setstretch` trong khoảng 1,3–1,5                             |
| Tài liệu tham khảo   | Ưu tiên`biblatex` + `biber`, in theo nhóm bằng nhiều `\printbibliography[keyword=…]`. Hiện **chưa cài**, xem mục 4 |
| Hồ sơ đính kèm     | `pdfpages`                                                                                                                             |
| Build                   | `latexmk -xelatex` (hiện **chưa cài**; tạm dùng Makefile gọi `xelatex` nhiều lượt)                                    |

Không dùng lớp `llncs` của `paper/`, không dùng mẫu luận văn không chính thức của trường khác. Hướng dẫn chỉ có mẫu Word, nên một lớp riêng mỏng trên lớp chuẩn dễ đối chiếu và sửa theo mẫu hơn.

## 2. So sánh các phương án

| Tiêu chí (nguồn yêu cầu)                                                                  | `report` / `extreport`                                                                                                                    | `memoir`                                                               | **`scrreprt` (KOMA)**                                                                                         |
| ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| Cỡ chữ 13 (HT mục 2)                                                                        | `report` chỉ có 10/11/12; `extreport` có 12, 14, không có 13. Phải ghi đè `\normalsize` bằng tay, các cỡ tương đối lệch | Tùy chọn 9–12, 14, 17…; không có 13, cũng phải tự định nghĩa | **`fontsize=13bp` tự tính toàn bộ thang cỡ**; đã kiểm tra ra đúng 13,0 pt trong PDF                 |
| Khối không đánh số trong mục lục: Mở đầu, Kết luận và kiến nghị (HT 3.10, 3.12) | `\chapter*` + `\addcontentsline` thủ công                                                                                               | `\chapter*` + lệnh riêng                                             | **`\addchap`** có sẵn, tự vào mục lục và đầu trang                                                   |
| Danh mục hình/bảng, TLTK vào mục lục (HT 3.4–3.5, 3.13)                                 | Thủ công                                                                                                                                    | Có tùy chọn                                                           | **`listof=totoc`, `bibliography=totoc`**                                                                    |
| Tùy biến tiêu đề, đầu/chân trang                                                       | Cần thêm`titlesec`, `fancyhdr`                                                                                                          | Tích hợp sẵn                                                          | Tích hợp (`\addtokomafont`, `\RedeclareSectionCommand`, `scrlayer-scrpage`)                                   |
| Một/hai mặt (HD: quyển in một hoặc hai mặt)                                              | Có                                                                                                                                           | Có                                                                      | Có (`oneside`/`twoside`), lề vẫn do `geometry` quyết định                                                 |
| Tương thích XeLaTeX + polyglossia tiếng Việt                                              | Tốt                                                                                                                                          | Tốt                                                                     | Tốt, đã kiểm tra                                                                                                  |
| Rủi ro                                                                                        | Nhiều bản vá rời rạc                                                                                                                     | Lớp lớn, thay nhiều gói chuẩn, khó ghép gói khác                | Cần tắt`typearea` để `geometry` quản lý lề; tiêu đề mặc định là phông sans, phải đổi sang serif |

KOMA là phương án duy nhất đáp ứng cỡ 13 mà không phải ghi đè lõi định dạng, nên được chọn.

## 3. Kết quả kiểm tra bản mẫu

Bản mẫu một tệp gồm mục lục, `\addchap{Mở đầu}`, chương đánh số, bảng `booktabs`, công thức, TLTK và một trang `\includepdf` của `guideline/Bìa.pdf`. Biên dịch hai lượt XeLaTeX, đo bằng PyMuPDF:

| Kiểm tra           | Kết quả                                                                                                                                  |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Khổ giấy          | 595,28 × 841,89 pt = A4                                                                                                                   |
| Cỡ thân bài      | 13,0 pt (TeX báo 13,04874 pt = 13 bp, tức đúng point của Word)                                                                        |
| Phông nhúng       | Chỉ Times New Roman (thường, đậm, nghiêng, đậm nghiêng) + Latin Modern Math cho công thức                                       |
| Lề                 | Mép trái chữ 30,0 mm; mép phải chữ 190,0 mm, tức lề phải 20 mm                                                                    |
| Tiếng Việt        | Ẳ ẵ Ỡ ỡ Ự ự Đ Ư hiển thị đúng khi xem trực quan; nhãn "Mục lục", "Bảng 1.1", "Tài liệu tham khảo" lấy từ polyglossia |
| Tiêu đề chương | Mặc định ra "1 Cơ sở khoa học", chưa có chữ "Chương"; cần`chapterprefix=true` hoặc định dạng lại trong lớp             |
| Cảnh báo          | Chỉ còn cảnh báo`typearea` về DIV, vô hại vì `geometry` đặt lại lề; sẽ tắt trong lớp                                    |

Thiết lập lõi đã chạy được:

```latex
\documentclass[fontsize=13bp,a4paper,oneside,listof=totoc,
  bibliography=totoc,numbers=noenddot]{scrreprt}
\usepackage[a4paper,left=3cm,right=2cm,top=2cm,bottom=2cm]{geometry}
\usepackage{fontspec}
\IfFontExistsTF{Times New Roman}{\setmainfont{Times New Roman}}{%
  \setmainfont{times.ttf}[Path=/mnt/c/Windows/Fonts/,
    BoldFont=timesbd.ttf,ItalicFont=timesi.ttf,BoldItalicFont=timesbi.ttf]}
\usepackage{unicode-math}\setmathfont{latinmodern-math.otf}
\addtokomafont{disposition}{\rmfamily}
\usepackage{polyglossia}\setdefaultlanguage{vietnamese}
\usepackage{setspace}\setstretch{1.3}
```

Cần theo dõi: PyMuPDF trích văn bản bị dính từ sau chữ có dấu ("Mởđầu", "Cơ sởkhoa") dù trang in đúng. Phải kiểm tra sao chép/tìm kiếm trong PDF cuối bằng trình đọc thông dụng.

Chưa kiểm tra: hệ số giãn dòng so với Word (mục 2 của bản tổng hợp yêu cầu đối chiếu bằng bản xuất), bìa khung đôi, bảng nhiều trang và PDF scan thật.

## 4. Thiếu sót của môi trường cần xử lý

| Thiếu                                                                                           | Ảnh hưởng                                                       | Cách xử lý                                                                                                                                                                                           |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Times New Roman không được cài trong Linux; chỉ đọc được từ`/mnt/c/Windows/Fonts/` | Máy khác (hoặc CI) sẽ không có phông và build sai phông   | Lớp phải**dừng build** nếu không tìm thấy Times New Roman, không âm thầm dùng TeX Gyre Termes. Có thể chép phông vào `~/.fonts`                                                 |
| `biblatex`, `biber` (`texlive-bibtex-extra`, `biber`)                                    | Không phân nhóm TLTK theo HT 3.13 một cách tự động được | `sudo apt install texlive-bibtex-extra biber`. Nếu không cài được: dùng BibTeX + `natbib`, tách mỗi nhóm một tệp `.bib` và một khối danh mục (phương án dự phòng, kém hơn) |
| `latexmk`                                                                                      | Build thủ công nhiều lượt                                     | `sudo apt install latexmk`                                                                                                                                                                            |
| `algorithm`, `algpseudocode`, `siunitx` (`texlive-science`)                              | Không trình bày được Algorithm 1 như trong bài báo        | `sudo apt install texlive-science`                                                                                                                                                                    |
| `pandoc`                                                                                       | Chưa có đường chuyển sang Word theo HD                       | Cài`pandoc` khi dựng quy trình Word (bản tổng hợp, mục 7.2)                                                                                                                                    |

Lệnh cài gộp (cần quyền sudo):

```bash
sudo apt install texlive-bibtex-extra biber latexmk texlive-science pandoc
```

## 5. Bước tiếp theo

1. Cài các gói ở mục 4.
2. Dựng `template/ctu-report.cls` từ thiết lập lõi ở mục 3, thêm tiêu đề chương/mục serif có chữ "Chương", tắt cảnh báo `typearea`, đánh số trang La Mã/Ả Rập, đánh số hình/bảng theo chương.
3. Dựng `main.tex`, `config/metadata.tex`, bìa chính và bìa phụ theo cây thư mục ở mục 10.1 của bản tổng hợp.
4. Chạy bản mẫu kiểm tra: tên đề tài dài, bảng nhiều trang, công thức, PDF scan; đối chiếu giãn dòng với một trang Word cùng nội dung.
