---
name: cdm-ldm-pdm
description: Vẽ hoặc chỉnh sửa mô hình dữ liệu CDM, LDM, PDM từ đặc tả nghiệp vụ, schema, migration hay DDL; dùng ký pháp chân chim, bố cục lưới và đường nối vuông góc để xuất SVG/PNG chèn báo cáo. Áp dụng cho sơ đồ dữ liệu, không dùng cho lưu đồ hay sơ đồ triển khai.
---

# Vẽ CDM, LDM và PDM

Tái sử dụng phương pháp của `template-diagram-system`: hộp thực thể có
thuộc tính, ký pháp chân chim, lưới bố cục lưu được, chia cổng nối và
định tuyến A* vuông góc. Các script trong skill độc lập với thư mục nguồn.

## Chọn mô hình và nguồn

- **CDM:** khái niệm nghiệp vụ và quan hệ; không đưa kiểu SQL hay FK vật lý
  lên hình. Đọc quy tắc nghiệp vụ trước khi đặt cardinality.
- **LDM:** thực thể, thuộc tính, khóa logic, tính tùy chọn và quan hệ định
  danh/không định danh; dùng kiểu logic độc lập hệ quản trị.
- **PDM:** bảng/cột, PK/FK, kiểu dữ liệu của hệ quản trị và nullability từ
  schema/migration/DDL. Bản tổng quan chỉ có tên bảng phải được ghi rõ;
  nó không thay thế bản PDM chi tiết hoặc từ điển dữ liệu.

Đọc [references/modeling-and-layout.md](references/modeling-and-layout.md)
trước khi chuyển nguồn sang mô hình, chia module hoặc rút gọn PDM. Đó là
nơi quy định chiều cardinality, định danh, tham chiếu và kiểm đếm phần lược.
Nguồn thiếu quy tắc thì ghi giả định hoặc hỏi đúng chỗ thiếu; không suy ra
tính bắt buộc ở phía con chỉ từ một FK `NOT NULL`.

## Tạo và dựng hình

1. Xác định lớp mô hình, nguồn/version, ngôn ngữ nhãn và kích thước chèn
   báo cáo. Giữ ngôn ngữ hiện có trừ khi người dùng yêu cầu đổi.
2. Tạo JSON theo [references/input-format.md](references/input-format.md).
   Dùng `assets/cdm.example.json`, `ldm.example.json`, `pdm.example.json`
   hoặc `pdm-overview.example.json` làm mẫu cấu trúc; đây là dữ liệu thư viện
   giả định để minh họa, không phải schema của dự án người dùng.
3. Ghi JSON của đề tài vào thư mục tài nguyên sơ đồ của dự án. Không sửa
   các mẫu trong skill mỗi lần dùng, không ghi schema đề tài vào skill.
4. Dựng bằng `scripts/draw_model.py`; đường dẫn script/tài nguyên luôn
   tính từ thư mục chứa `SKILL.md`, không từ thư mục hiện hành của terminal.

Ví dụ chạy từ gốc `reportTemplate/` (thay đường dẫn khi cài ở nơi khác):

```bash
python3 -m venv .venv-diagrams
.venv-diagrams/bin/python -m pip install -r .agents/skills/cdm-ldm-pdm/scripts/requirements.txt
.venv-diagrams/bin/python .agents/skills/cdm-ldm-pdm/scripts/draw_model.py \
  .agents/skills/cdm-ldm-pdm/assets/ldm.example.json \
  --out build/diagrams-demo/ldm
```

Python **3.10+**, Pillow và đủ 4 kiểu Times New Roman. Trên Windows dùng
`.venv-diagrams\Scripts\python.exe`. Script tự tìm phông trong Windows,
WSL hoặc fontconfig; nếu chưa thấy, truyền `--font-dir /duong/dan/phong`
chứa `times.ttf`, `timesbd.ttf`, `timesi.ttf`, `timesbi.ttf`. Không kèm
phông trong skill; không âm thầm đổi họ phông. Đây là phụ thuộc tùy chọn
cho sơ đồ, không phải phụ thuộc của quá trình build báo cáo trống.

## Bố cục và vòng sửa

- Đặt thực thể liên quan gần nhau; chừa hành lang nối, dùng `null` làm ô
  trống. Thực thể độc lập vẫn được giữ, có thể gom thành hàng cuối.
- Với tự quan hệ hoặc nhãn vòng thiếu chỗ, thêm ô/hàng `null` bên phải
  và bên dưới để mở rộng vùng vẽ; tăng `colgap` đơn thuần không mở rộng
  lề ngoài của lưới chỉ có một hộp.
- Chạy bình thường để dựng đúng lưới đầu vào. Dùng `--optimize` khi cần
  tìm lưới khác; không chạy tối ưu lại chỉ để xuất hình đã duyệt.
- Mỗi lượt lưu `<out>.layout.json` và `<out>.check.json`; dùng
  `--layout duong/dan/hinh.layout.json` để tái dựng bố cục đã chọn. Model
  gốc không bị sửa. Tối ưu dùng seed cố định, chấm lại sau định tuyến;
  không bảo đảm tìm được tối ưu toàn cục hay sơ đồ không có giao cắt.
- Đường đi vuông góc, rải cổng trên cạnh, giữ chỗ cho chân chim; không
  thay quan hệ bằng mũi tên lưu đồ. Có thể ép hai cạnh nối qua `sides`.
- Khi không định tuyến được hoặc kiểm tra thất bại: sửa lưới/tăng khoảng
  cách/chia module rồi chạy lại. Không bỏ quan hệ để làm chỉ số đẹp.

## Kiểm tra và giao kết quả

Script chỉ xuất ảnh khi không có đoạn xiên, đoạn nối chồng, đường xuyên
hộp, hộp chồng hoặc nhãn quan hệ va chạm được bộ kiểm phát hiện. Kiểm tra
này không chứng minh đúng ngữ nghĩa hoặc đủ dữ liệu. Giao cắt vuông góc
được thống kê riêng (`metrics.cross`), có nền trắng tách nét; giảm chúng
khi ảnh khó đọc. Đọc giới hạn kiểm tra trong tài liệu bố cục.

Đối chiếu thực thể/thuộc tính/PK/FK/cardinality với nguồn; kiểm đếm phần
vẽ, phần tham chiếu và phần lược. Mở PNG để xem nhãn tiếng Việt, ký hiệu
hai đầu, chú giải và kích thước thực tế. Với Word dùng SVG vector hoặc
PNG 300 dpi; với XeLaTeX dùng PNG trực tiếp hoặc chuyển SVG sang PDF bằng
công cụ có sẵn. SVG dùng phông của máy xem, không nhúng phông.

Khi người dùng yêu cầu chèn vào báo cáo, đặt ảnh thật ở `assets/diagrams/`,
thêm `figure`, `caption`, `label` đúng phần và build/kiểm tra PDF cuối.
Không tự chèn dữ liệu ví dụ vào nội dung báo cáo trống. Caption phải nói
rõ lớp mô hình, phạm vi, phiên bản schema và các rút gọn có dùng. Bàn giao
JSON nguồn, lưới đã chọn, SVG/PNG, kết quả kiểm tra và thông tin phần lược.

## Nguồn của phương pháp

`scripts/erd.py` và `scripts/toi_uu.py` được chuyển từ hai tệp cùng tên
trong `template-diagram-system/` của repository nckh2. Bản này thêm cấu
hình phông, ngắt dòng chú giải và xử lý trường hợp lưới ít phần tử.
`draw_model.py` thay các script dựng hình gắn với dự án cũ bằng đầu vào
JSON. Không cần Graphviz, `dac_ta_CDM_LDM_PDM.md`, CSV schema v8 hoặc đường
dẫn Windows của bộ gốc. Hướng dẫn CDM và các mẫu thư viện là phần bổ sung;
không xem chúng là kết quả CDM đã có trong bộ gốc.
