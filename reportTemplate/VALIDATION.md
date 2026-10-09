# Kiểm tra template — 09/10/2026

Đã hoàn tất biên dịch và kiểm tra bộ template ban đầu. Các ô trống và
placeholder là phần cần điền cho đề tài mới.

## PDF đã tạo

| Tệp | Số trang |
| --- | ---: |
| `build/content/content.pdf` | 27 |
| `build/content-twoside/content.pdf` | 27 |
| `build/bulletin-vi/bulletin-vi.pdf` | 1 |
| `build/bulletin-en/bulletin-en.pdf` | 1 |
| `build/summary-vi/summary-vi.pdf` | 1 |
| `build/summary-en/summary-en.pdf` | 1 |
| `build/smoke/smoke.pdf` | 5 |

Hai báo cáo giữ 116 tiêu đề chương/mục và 14 tiêu đề phụ lục của khung
ban đầu, với tên khái quát. Nội dung khoa học chỉ còn comment hướng dẫn
và lệnh ngắt trang vô hình `\par\penalty0` để chương trống không tràn.
Báo cáo chính không chứa hình, số liệu hay mục tài liệu tham khảo mẫu;
PDF minh họa và bản ghi placeholder nằm riêng trong `examples/`.

## Lệnh tái tạo

```bash
make -C reportTemplate doctor
make -C reportTemplate all smoke
make -C reportTemplate check
```

Đã kiểm tra thêm nhánh BibTeX trên bản sao độc lập:

```bash
make content smoke BIBLIOGRAPHY=bibtex
make check
```

## Kết quả

- Cả bảy PDF đều A4, phông Times New Roman được nhúng. Kiểm tra công cụ
  xác nhận đủ bốn kiểu chữ. Class giữ cỡ thân bài 13 bp, giãn dòng 1,3
  và lề 30/20/20/20 mm; hai bìa và biểu mẫu giữ cấu hình riêng.
- Log cuối không có lỗi LaTeX, tràn khung ngang/dọc, tham chiếu/trích
  dẫn chưa giải quyết, nhãn lặp, thiếu ký tự hoặc phông thay thế.
- Đã xem trực quan hai bìa, trang mục lục đầu, biểu mẫu kết quả Việt–Anh,
  trang nhận xét người hướng dẫn, thông tin chủ nhiệm, Mở đầu, các trang
  chương trống; cả bốn bản tin/tóm tắt và trang minh họa hình/bảng/công
  thức/tài liệu tham khảo. Đã xem thêm bìa, biểu mẫu và trang chẵn/lẻ ở
  bản hai mặt; không phát hiện chữ đè logo hoặc nội dung vượt lề.
- Rà soát nguồn và văn bản PDF: không còn giá trị metadata dài, tên các
  thành viên, mã sinh viên/lớp, khóa tài liệu tham khảo hoặc thuật ngữ
  nghiên cứu riêng của đề tài cũ. Thông tin cơ quan và logo dùng chung
  được giữ lại có chủ đích; logo khớp nguyên byte với tài nguyên gốc.
- Đã sao chép nguồn sang một thư mục độc lập trong `/tmp`, bỏ toàn bộ
  `build/` và file phụ, rồi biên dịch cả bảy PDF và chạy kiểm tra thành
  công. Nhánh BibTeX đã kiểm tra cả báo cáo không có trích dẫn và ví dụ
  có trích dẫn. Nguồn template không có liên kết tới dữ liệu/mã sản phẩm.
- Không áp dụng điều kiện số trang tối thiểu hoặc hồ sơ nghiệm thu.
- Không sửa nguồn LaTeX, metadata, script, tài nguyên hay PDF của báo
  cáo gốc. Thư mục build hiện tại của template được tạo mới khi biên
  dịch; không sao chép build, môi trường ảo hoặc tệp tạm của báo cáo gốc.
- Kiểm tra whitespace nguồn và `git diff --check` đạt.

## Danh sách tệp nguồn

Các đường dẫn dưới đây tương đối với `reportTemplate/`. Ngoài danh
sách này có bảy PDF được tạo ở bảng đầu; các log/file phụ sinh khi build
được bỏ qua bởi Git.

```text
.gitignore
Makefile
README.md
VALIDATION.md
appendices/reproducibility.tex
appendices/supplementary-results.tex
assets/README.md
assets/diagrams/.gitkeep
assets/figures/.gitkeep
bibliography/articles.bib
bibliography/books.bib
bibliography/legal.bib
bibliography/references.bib
chapters/01-foundations/chapter.tex
chapters/01-foundations/sections/background.tex
chapters/01-foundations/sections/related-work.tex
chapters/01-foundations/sections/requirements.tex
chapters/02-data-methods/chapter.tex
chapters/02-data-methods/sections/data.tex
chapters/02-data-methods/sections/methods.tex
chapters/02-data-methods/sections/research-design.tex
chapters/03-system/chapter.tex
chapters/03-system/sections/architecture.tex
chapters/03-system/sections/implementation.tex
chapters/03-system/sections/synchronization.tex
chapters/04-evaluation/chapter.tex
chapters/04-evaluation/sections/limitations.tex
chapters/04-evaluation/sections/results.tex
chapters/04-evaluation/sections/setup.tex
chapters/conclusion.tex
chapters/introduction.tex
config/members.tex
config/metadata.tex
deliverables/bulletin-en.tex
deliverables/bulletin-vi.tex
deliverables/content/bulletin-en.tex
deliverables/content/bulletin-vi.tex
deliverables/content/summary-en.tex
deliverables/content/summary-vi.tex
deliverables/summary-en.tex
deliverables/summary-vi.tex
examples/formatting.tex
examples/references.bib
frontmatter/abbreviations.tex
frontmatter/cover.tex
frontmatter/participants.tex
frontmatter/principal-investigator.tex
frontmatter/research-body-en.tex
frontmatter/research-body-vi.tex
frontmatter/research-info-en.tex
frontmatter/research-info-vi.tex
frontmatter/title-page.tex
logo-ctu.png
main.tex
scripts/build.py
scripts/check_template.py
scripts/doctor.py
template/bibliography.tex
template/commands.tex
template/ctu-report.cls
template/packages.tex
template/typography.tex
```
