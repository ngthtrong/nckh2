# Bộ mẫu slide nghiên cứu CTU

Bộ mẫu độc lập để làm slide cho đề tài khác, giữ phong cách CTU đã chốt:
**K2D / Readex Pro**, Overview ở slide 2, box đơn giản, **không footnote/tổng kết
cuối trang và không dải màu viền trái box**. Logo, artwork chân trang và số trang
CTU vẫn được giữ.

- [Skill hướng dẫn](ctu-slides/SKILL.md): dùng trực tiếp hoặc cài vào repo khác.
- [Bộ slide minh họa các bố cục](preview/ctu-layout-catalog.pptx).
- [PDF minh họa](preview/ctu-layout-catalog.pdf) · [Ảnh tổng quan](preview/checks/contact-sheet.png).
- [Cấu hình mẫu](ctu-slides/examples/catalog.json) · [Định dạng cấu hình](ctu-slides/references/spec.md).
- Khung đề tài mới: [tiếng Việt](ctu-slides/examples/starter.vi.json) · [tiếng Anh](ctu-slides/examples/starter.en.json).

Ví dụ chỉ minh họa bố cục; số liệu ví dụ được ghi rõ là giả lập. Không có nội
dung, tác giả, số liệu nghiên cứu hoặc GIF riêng của paper 6444 trong bộ mẫu.

## Dùng với Codex

Ví dụ yêu cầu:

> Đọc `templateCTU/ctu-slides/SKILL.md`. Dùng bộ mẫu CTU này để tạo slide cho
> paper tại `paper/main.pdf`, thời lượng khoảng 20 phút, lưu vào `presentation/`.
> Giải thích thuật toán và chỉ số trước phần kết quả; tự chọn số slide phù hợp.

Hoặc yêu cầu **chỉ lên dàn ý**, rồi yêu cầu dựng slide sau khi thảo luận. Skill
giữ đúng phạm vi này, không tự tạo slide từ một yêu cầu chỉ phân tích.

## Dùng bằng lệnh

Chạy từ vị trí bất kỳ; thay đường dẫn Python/skill phù hợp với máy của bạn:

```bash
python3 -m venv .venv-ctu
.venv-ctu/bin/pip install -r templateCTU/ctu-slides/requirements.txt
.venv-ctu/bin/python templateCTU/ctu-slides/scripts/ctu_slides.py init --project presentation/my-topic
```

Sửa `presentation/my-topic/deck.json`, thêm hình hoặc CSV vào project rồi chạy:

```bash
.venv-ctu/bin/python templateCTU/ctu-slides/scripts/ctu_slides.py build --spec presentation/my-topic/deck.json
.venv-ctu/bin/python templateCTU/ctu-slides/scripts/ctu_slides.py render --project presentation/my-topic
.venv-ctu/bin/python templateCTU/ctu-slides/scripts/ctu_slides.py check --project presentation/my-topic
```

Trên Windows, Python trong môi trường ảo thường ở `.venv-ctu/Scripts/python.exe`.
Để xuất PDF cần LibreOffice; dùng `--soffice <đường-dẫn-soffice>` nếu chương trình
chưa nằm trên PATH. Nếu cần chỉnh PowerPoint thủ công, cài font Regular/Bold trong
`ctu-slides/assets/fonts/` để giữ đúng bố cục. Font được phân phối kèm giấy phép OFL.

Project mới chỉ chứa các đề mục để điền nội dung, không gán sẵn tác giả hay kết
quả nghiên cứu. `build` sinh PPTX, notes Markdown và manifest; `render` sinh PDF,
ảnh từng slide và contact sheet; `check` ghi kết quả kiểm tra. Cần xem ảnh/PDF để
phát hiện chữ chồng hoặc tràn, vì kiểm tra tự động không thay thế việc xem bố cục.

## Sao chép sang repo khác

Có thể sao chép nguyên `templateCTU/` rồi gọi đường dẫn skill như ví dụ. Để Codex
tự phát hiện trong một repo, sao chép **thư mục `ctu-slides/`** vào
`.agents/skills/ctu-slides/`. Thư mục này chứa đủ template, font, script và ví dụ;
không phụ thuộc vào repo hiện tại hay thư mục `ISDS/`.

## Thành phần

```text
templateCTU/
├── README.md
├── ctu-slides/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── requirements.txt
│   ├── assets/         # PowerPoint CTU gốc, font và giấy phép
│   ├── examples/       # Catalog bố cục, CSV và GIF minh họa
│   ├── references/     # Định dạng JSON và quy ước sử dụng
│   └── scripts/       # init, build, render, check, gif
└── preview/            # PPTX/PDF catalog và ảnh kiểm tra
```

Nội dung khoa học, số lượng slide, ngôn ngữ và thời lượng thuộc từng project.
Các quy tắc hình thức là mặc định tái sử dụng, có thể điều chỉnh khi người dùng
yêu cầu. Bộ này không cài skill toàn cục và không sửa slide `ISDS/` hiện có.
