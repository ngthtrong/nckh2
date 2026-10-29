# Đầu vào JSON và lệnh dựng

`scripts/draw_model.py` nhận UTF-8 JSON. Không cần Graphviz hay đặc tả của
repository nguồn. Xem các tệp `../assets/*.example.json` để có ví dụ chạy
được; các khóa dưới đây có cùng ý nghĩa cho cả ba lớp.

| Khóa | Ý nghĩa |
| --- | --- |
| `layer` | Bắt buộc: `CDM`, `LDM`, `PDM` |
| `title` | Tên hình dùng trong biên bản kiểm tra; đặt tiêu đề hiển thị bằng caption tài liệu |
| `source` | Đường dẫn/version nguồn hoặc ghi rõ dữ liệu minh họa/giả định; không tự đọc tệp này |
| `entities` | Danh sách hộp, không trùng tên |
| `relations` | Danh sách quan hệ; có thể rỗng |
| `grid` | Danh sách hàng, mỗi ô là tên hộp hoặc `null`; mọi hộp xuất hiện đúng một lần |
| `colgap`, `rowgap` | Khoảng cách hộp, mặc định 120/96; tối thiểu 64 |
| `panels` | Tùy chọn: `{label, names: [...], color, fill}` để tạo nền nhóm |
| `note` | Chú giải thêm: phạm vi, tags, phần gộp/lược; tự ngắt theo độ rộng hình |

Một hộp:

```json
{
  "name": "Loan",
  "attrs": [[true, "loan_id", "identifier", false],
            [false, "return_date", "date", true]]
}
```

Mỗi thuộc tính là `[is_pk, name, type, nullable]`. Dùng boolean JSON thật,
không dùng chuỗi `"true"`. PK không nullable. Kiểu logic cho LDM, kiểu SQL
cụ thể cho PDM. Nếu cần đánh dấu FK thì ghi `[FK]` trong tên hiển thị và
giữ ánh xạ cột thật trong từ điển dữ liệu.

`context: true` cho hộp tham chiếu không thuộc tính. `compact: true` cho
hộp chỉ tên (mặc định cho CDM), có thể thêm `tags: ["R", "U×2"]`, `color`,
`fill`. Không khai báo `attrs` cùng context/compact vì sẽ ẩn dữ liệu.
Hộp LDM/PDM thường không compact; `attrs` là nội dung thật cần hiển thị.

Một quan hệ:

```json
{
  "a": "Reader", "b": "Loan", "label": "thực hiện",
  "ca": "1", "cb": "0..N", "ident": false
}
```

`ca/cb` là ký hiệu đặt sát `a/b`, không phải số hộp đích nhìn từ hộp đó.
Reader—Loan trong ví dụ: một Loan có đúng một Reader, Reader có 0..N Loan.
Các giá trị là `1`, `0..1`, `0..N`, `1..N` (N viết hoa). LDM/PDM bắt buộc
`ident`; CDM bỏ trường này, bộ dựng dùng nét liền trung tính. Tùy chọn
`sides: ["R", "L"]` ép cạnh ra/vào, mỗi cạnh thuộc `L/R/T/B`. Nhãn là
động từ hoặc vai trò, không tự trích từ tên thực thể.

Chạy từ `reportTemplate/`, sau khi cài dependencies như `SKILL.md`:

```bash
.venv-diagrams/bin/python .agents/skills/cdm-ldm-pdm/scripts/draw_model.py \
  assets/diagrams/ldm.json --out assets/diagrams/ldm --optimize

.venv-diagrams/bin/python .agents/skills/cdm-ldm-pdm/scripts/draw_model.py \
  assets/diagrams/ldm.json --out assets/diagrams/ldm \
  --layout assets/diagrams/ldm.layout.json
```

Đầu ra: `.svg`, `.png` (300 dpi), `.layout.json` (lưới), `.check.json`
(hash đầu vào, số hộp/đường, kiểm hình học, metrics và phông thực tế).
Script trả mã lỗi nếu đầu vào sai, không route được hoặc còn lỗi kiểm tra;
không xuất ảnh mới khi kiểm tra thất bại. Nếu cùng tiền tố đã có ảnh từ
lượt trước, ảnh đó vẫn là bản cũ: chỉ dùng ảnh khi lượt chạy hiện tại trả
mã 0 và `.check.json` báo PASS đúng hash model. Không lấy ảnh cũ làm
bằng chứng cho đầu vào mới thất bại.

`--check-only` vẫn định tuyến và ghi lưới/biên bản nhưng không tạo ảnh.
`--layout` lấy lưới từ tệp đã lưu; kết hợp `--optimize` nghĩa là dùng lưới
đó làm điểm xuất phát để tìm lại. Input model không bị ghi đè. Cùng đầu
vào/lưới/phông và phiên bản thư viện cho hình học tái lập; SVG cần phông
Times New Roman trên máy xem để giữ số đo chữ tương ứng.

Với XeLaTeX:

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=\textwidth]{ldm.png}
  \caption{Mô hình dữ liệu logic của [phạm vi]. [Nêu tham chiếu/phần lược nếu có].}
  \label{fig:ldm}
\end{figure}
```

Ví dụ LaTeX chỉ minh họa vị trí caption/label; điền nội dung thật trước
khi dùng trong báo cáo. Không chèn trực tiếp SVG bằng `includegraphics`.
