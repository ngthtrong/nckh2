# Template báo cáo nghiên cứu khoa học LaTeX

Bộ template độc lập, giữ bố cục của báo cáo gốc: A4, Times New Roman
13 bp, giãn dòng 1,3; lề trái 30 mm, phải/trên/dưới 20 mm. Hai bìa giữ
khung đôi và vùng nội dung căn giữa riêng; biểu mẫu giữ bố cục, logo và
giãn dòng riêng của bản gốc. Header/footer giữ kiểu hiện có: không có
nội dung header, số trang ở giữa footer. Hai bìa không in số trang,
phần đầu dùng số La Mã, Mở đầu bắt đầu số Ả Rập từ 1. Trang biểu mẫu
không in số trang nhưng vẫn được tính trong phần đầu.

Nội dung nghiên cứu để trống, chỉ giữ tiêu đề khái quát và comment hướng
dẫn. Ô trống và placeholder trên biểu mẫu là chủ ý. Thư mục này có thể
sao chép ra ngoài repository để sử dụng; không cần dữ liệu, mô hình,
minh chứng hoặc bước xuất số liệu. Không có kiểm tra số trang tối thiểu
hay kiểm tra hồ sơ nghiệm thu.

## Cài đặt

Yêu cầu Python **3.9+**, GNU Make, XeLaTeX và Poppler. Python chỉ dùng
thư viện chuẩn; không cần môi trường ảo, pip hay latexmk.

Trên Debian/Ubuntu có thể cài:

```bash
sudo apt update
sudo apt install make python3 texlive-xetex texlive-latex-extra \
  texlive-lang-other texlive-fonts-recommended texlive-bibtex-extra \
  biber poppler-utils fontconfig
```

Cần Times New Roman đủ bốn kiểu Regular/Bold/Italic/Bold Italic. Cài
phông có quyền sử dụng vào hệ thống rồi chạy `fc-cache -f`. Trên WSL,
template cũng nhận bốn tệp `times.ttf`, `timesbd.ttf`, `timesi.ttf`,
`timesbi.ttf` tại `/mnt/c/Windows/Fonts/`. Nếu dùng vị trí khác, chỉnh
`template/typography.tex`. Template báo lỗi khi không tìm thấy phông,
không tự thay bằng phông khác. Phông toán dùng Latin Modern Math.

Trên Windows/macOS có thể dùng TeX Live/MiKTeX/MacTeX cùng Python,
Make và Poppler tương ứng. Chạy `make doctor` để kiểm tra thực tế.

## Biên dịch

Từ repository:

```bash
make -C reportTemplate doctor
make -C reportTemplate all
make -C reportTemplate smoke
make -C reportTemplate check
```

Hoặc vào `reportTemplate/` và bỏ `-C reportTemplate` trong các lệnh.

| Lệnh Make | PDF được tạo trong thư mục template |
| --- | --- |
| `make content` | `build/content/content.pdf` — một mặt |
| `make content-twoside` | `build/content-twoside/content.pdf` — hai mặt |
| `make bulletin-vi` | `build/bulletin-vi/bulletin-vi.pdf` |
| `make bulletin-en` | `build/bulletin-en/bulletin-en.pdf` |
| `make summary-vi` | `build/summary-vi/summary-vi.pdf` |
| `make summary-en` | `build/summary-en/summary-en.pdf` |
| `make deliverables` | Bốn PDF bản tin/tóm tắt Việt–Anh |
| `make all` | Hai bản báo cáo và bốn bản tin/tóm tắt |
| `make smoke` | `build/smoke/smoke.pdf` — minh họa định dạng riêng |

Bản hai mặt giữ lề vật lý trái 30 mm/phải 20 mm trên cả trang chẵn và
lẻ như báo cáo gốc, không đảo lề và không ép chương mở ở trang lẻ.

Build mặc định ưu tiên biblatex-ieee/Biber; nếu thiếu, dùng
natbib/BibTeX với `ieeetr`. Có thể chọn rõ:

```bash
make content BIBLIOGRAPHY=biblatex
make content BIBLIOGRAPHY=bibtex
make smoke BIBLIOGRAPHY=bibtex
```

Script tự phát hiện `\cite`, `\citep`, `\citet`, `\nocite` và biên dịch
đến khi tham chiếu ổn định. Biber khởi tạo cả danh mục trống; BibTeX chỉ
chạy khi có trích dẫn. Báo cáo trống
vẫn có trang tài liệu tham khảo nhưng không sinh mục giả hoặc cảnh báo
tham chiếu chưa giải quyết. Dùng Make/script để cơ chế này hoạt động;
một lượt XeLaTeX trực tiếp chưa đủ giải quyết danh mục và tham chiếu.

`make check` kiểm tra sáu PDF, log, khổ A4, phông nhúng và tài nguyên
nội bộ; kiểm tra thêm PDF minh họa nếu đã build. Build dừng khi gặp lỗi
LaTeX, tràn khung, thiếu ký tự, nhãn lặp hoặc tham chiếu chưa giải quyết.
Log nằm cạnh từng PDF. Xem trực quan PDF sau khi thay nội dung, vì log
không phát hiện được mọi vấn đề như chữ đè lên logo.

`make clean` xóa **đầu ra do template sinh trong `build/`**, gồm các PDF;
chạy `make all smoke` để tạo lại. Chỉ PDF cuối được phép theo dõi bằng
Git; file phụ, log và tệp tạm bị bỏ qua.

## Điền thông tin và nội dung

- `config/metadata.tex`: tên đề tài Việt–Anh, mã số, chủ nhiệm, thông
  tin cá nhân, lớp/khóa, người hướng dẫn, đơn vị, thời gian, kinh phí,
  địa điểm và ngày báo cáo. Thông tin cơ quan có thể chỉnh ở cuối tệp.
- `config/members.tex`: tên các thành viên, hàng MSSV/lớp và danh sách
  dùng trên bản tin. Khi thêm/bớt thành viên, chỉnh cả `\MemberRows`
  và `\ProjectMembers` trong cùng tệp.
- `frontmatter/`: danh sách thành viên, chữ viết tắt, thông tin kết quả
  Việt–Anh và thông tin chủ nhiệm. Thay `\PendingField{...}` bằng nội
  dung cần kê khai; thêm/bớt khối năm học và chèn ảnh vào đúng ô.
- `chapters/introduction.tex`: sáu mục Mở đầu.
- `chapters/01-foundations/` đến `04-evaluation/`: bốn chương chính,
  mỗi chương có `chapter.tex` và các tệp mục con trong `sections/`.
- `chapters/conclusion.tex`: kết luận và kiến nghị.
- `appendices/`: hai phụ lục khái quát, có thể đổi tên/thêm/bớt.
- `deliverables/content/`: nội dung bản tin Việt–Anh; hai bản tóm tắt
  dùng lại `frontmatter/research-body-vi.tex` và `research-body-en.tex`
  để thông tin thống nhất với biểu mẫu trong báo cáo.

Các dòng bắt đầu bằng `%` là hướng dẫn không hiển thị trong PDF. Điền
văn bản dưới tiêu đề tương ứng. Đổi tên chương/mục trong đối số
`\chapter{...}`, `\section{...}`, `\subsection{...}`. Nếu đổi tên tệp,
cập nhật `\input`/`\include` tại tệp cha hoặc `main.tex`. Thêm nhãn duy
nhất ngay sau tiêu đề, ví dụ `\label{sec:phuong-phap}`.

Chữ viết tắt hiện chỉ có hàng tiêu đề; thêm dòng
`TVT & Diễn giải đầy đủ \\` trước `\bottomrule`. Danh mục bảng/hình
của báo cáo chính để trống cho đến khi có đối tượng với `\caption`.

## Hình, bảng và công thức

Đặt tài nguyên của đề tài mới vào `assets/figures/` hoặc
`assets/diagrams/`. Các gói và đường dẫn đã cấu hình sẵn. Logo dùng
chung là `logo-ctu.png`; thay tệp này khi đổi cơ quan.

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=.8\textwidth]{ten-hinh.pdf}
  \caption{Tên hình}\label{fig:ten-hinh}
\end{figure}

\begin{table}[htbp]
  \centering
  \caption{Tên bảng}\label{tab:ten-bang}
  \begin{tabularx}{\textwidth}{lX}
    \toprule Tiêu chí & Mô tả \\
    \midrule
    {}[Tiêu chí] & [Mô tả] \\
    \bottomrule
  \end{tabularx}
\end{table}

\begin{equation}\label{eq:ten-cong-thuc}
  y = \sum_{i=1}^{n} w_i x_i.
\end{equation}
Hình~\ref{fig:ten-hinh}, Bảng~\ref{tab:ten-bang},
Công thức~\eqref{eq:ten-cong-thuc}.
```

Đặt chú thích hình bên dưới, chú thích bảng phía trên; đặt `\label`
sau `\caption`. Bảng dài dùng `longtable` với `\endfirsthead` và
`\endhead` để lặp tiêu đề. Có thể viết sơ đồ TikZ ngay trong LaTeX;
không cần công cụ sinh sơ đồ từ nghiên cứu cũ. Có PDF minh họa riêng
từ `examples/formatting.tex` để xem định dạng trước khi điền nội dung.

## Tài liệu tham khảo IEEE

Bốn tệp `bibliography/*.bib` ban đầu chỉ có comment. Thêm bản ghi
thật vào tệp phù hợp: `books.bib`, `articles.bib`, `legal.bib` hoặc
`references.bib`; trích dẫn bằng `\citep{khoa-tai-lieu}`. Dùng khóa
duy nhất, bảo vệ tên riêng bằng `{...}` trong tiêu đề khi cần.

Ví dụ cấu trúc để điền (không phải một nguồn đã xác minh):

```bibtex
@article{khoa-tai-lieu,
  author  = {[Họ, Tên]},
  title   = {{[Tên bài báo]}},
  journal = {[Tên tạp chí]},
  year    = {[Năm]},
  volume  = {[Tập]},
  pages   = {[Trang]},
  doi     = {[DOI]}
}
```

Thay tất cả trường mẫu bằng dữ liệu thật trước khi sử dụng. Danh mục
đánh số liên tục theo lần trích dẫn đầu tiên. `\nocite{khóa}` dùng khi
chủ ý đưa nguồn chưa trích dẫn vào danh mục. Bản ghi placeholder trong
`examples/references.bib` chỉ phục vụ kiểm tra định dạng IEEE và không
được dùng trong báo cáo chính.

Kết quả kiểm tra của phiên bản template ban đầu được ghi tại
`VALIDATION.md`.
