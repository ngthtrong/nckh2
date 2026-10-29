# Ngữ nghĩa mô hình và quy tắc trình bày

## Lấy nội dung từ nguồn

Lập danh sách thực thể/bảng, thuộc tính, khóa, quan hệ và nguồn trước khi
vẽ. Ghi phiên bản schema hoặc migration khi có; đánh dấu phần thiết kế
đề xuất, phần đã triển khai và giả định chưa xác minh. Script dựng hình
không tự đọc SQL/Markdown hay kết nối cơ sở dữ liệu: agent chuyển nguồn
sang JSON và chịu trách nhiệm đối chiếu nội dung.

| Lớp | Nội dung cần thấy | Cách xử lý khóa/kiểu |
| --- | --- | --- |
| CDM | Khái niệm nghiệp vụ, động từ quan hệ, số lượng/tính tùy chọn | Mặc định chỉ tên; không cần PK/FK/kiểu SQL |
| LDM | Thực thể, thuộc tính, PK logic, tính tùy chọn, quan hệ | Kiểu logic như `identifier`, `text`, `date`; không áp kiểu hệ quản trị khi chưa chọn |
| PDM chi tiết | Tên bảng/cột thật, PK, FK, nullability, kiểu SQL | Giữ đúng độ dài/precision và khóa ghép từ schema |
| PDM tổng quan | Tên bảng, nhóm module, quan hệ/tags | Ghi rõ ẩn cột; có bản chi tiết hoặc từ điển dữ liệu đi kèm |

Một PDM chi tiết có thể ghi tên hiển thị `reader_id [FK]`; renderer chỉ có
kênh biểu diễn PK riêng, không tự nhận biết FK, UNIQUE, index hay CHECK.
Giữ metadata đầy đủ trong đặc tả/từ điển dữ liệu; thêm quy tắc quan trọng
vào caption/thuyết minh thay vì giả vờ rằng ảnh chứa mọi ràng buộc DDL.

## Cardinality phải đi theo đúng đầu

`a`, `b` là hai đầu; `ca` nằm **sát hộp a**, `cb` nằm **sát hộp b**. Ví dụ
Reader—Loan có `ca=1`, `cb=0..N`: một Loan gắn đúng một Reader, còn một
Reader có thể chưa có Loan nào hoặc có nhiều Loan. Khi đảo `a/b` để đổi
chiều đọc động từ, phải đảo cả `ca/cb`.

| Giá trị | Ký hiệu chân chim | Ý nghĩa |
| --- | --- | --- |
| `1` | hai gạch | đúng một |
| `0..1` | vòng tròn + gạch | không hoặc một |
| `0..N` | vòng tròn + chân chim | không hoặc nhiều |
| `1..N` | gạch + chân chim | ít nhất một |

Với PDM, FK `NOT NULL` thường xác định mỗi bản ghi con phải có cha,
nhưng không chứng minh mọi cha phải có con. FK nullable cho phép không
có cha; FK có UNIQUE hoặc nằm trong khóa duy nhất có thể giới hạn số con
mỗi cha. Khóa ghép cần kiểm tra cả tập cột: không coi từng cột trong FK
ghép là một FK riêng, và không kết luận quan hệ 1–1 từ một phần khóa ghép.
`1..N` phía con cần quy tắc nghiệp vụ/ràng buộc bổ sung, không tự đoán.

## Khóa và nét vẽ

- PK: biểu tượng chìa khóa + gạch chân tên thuộc tính. `N` chỉ nullable,
  không phải ký hiệu “nhiều” trong dòng thuộc tính.
- LDM/PDM: nét liền = quan hệ định danh, nét đứt = không định danh. Với
  PDM, định danh khi tập cột FK của con tham gia trong PK của con. Dùng
  ngữ nghĩa khóa logic tương ứng ở LDM; không suy từ mức độ quan trọng.
- CDM: dùng nét liền trung tính, chú giải nói rõ không hàm ý khóa vật lý.
- Tự quan hệ: giữ một hộp, đường vòng ra ngoài; bộ dựng mặc định ra cạnh
  phải và vào cạnh dưới. Nhiều quan hệ giữa hai hộp vẫn là các quan hệ
  khác nhau, có thể đặt nhãn theo vai trò.

## Chia module và rút gọn

Giữ mô hình đầy đủ làm căn cứ; chọn phạm vi hình theo module nghiệp vụ.
Hộp tham chiếu đặt `context=true`: xám, nét đứt, chỉ tên. Caption chỉ nơi
có định nghĩa đầy đủ. Chỉ vẽ các quan hệ thuộc phạm vi hình; không lặp
quan hệ giữa hai hộp tham chiếu nếu chúng đã được định nghĩa ở hình khác.
Renderer vẽ đúng JSON, không tự lọc hay loại trùng quan hệ cho agent.

PDM quá nhiều FK có thể dùng tags cho các đích lặp lại, ví dụ `[R]` cho FK
tới `readers`; ký hiệu tùy từng schema, không mặc định `[T]/[U]` của bộ gốc.
Nhiều FK cùng cặp bảng có thể gộp `×n` nếu cùng cardinality và kiểu nét;
nếu vai trò, cardinality hay định danh khác nhau, giữ riêng hoặc mô tả
sự khác biệt rõ trong bản tổng quan. Không dùng `all(ident)` rồi vẽ một
nét đứt cho tập quan hệ có cả định danh và không định danh mà không giải thích.

Ghi bảng đối chiếu cạnh hình hoặc trong tài liệu nguồn:

| Phần | Cần ghi |
| --- | --- |
| Bảng/thực thể | Tổng nguồn, số vẽ đầy đủ, số tham chiếu, số lược và danh sách |
| Quan hệ/FK | Số quan hệ nguồn, số đường vẽ, số FK biểu diễn bởi các đường, số thay bằng tag, số lược |
| Gộp | Danh sách FK thuộc từng đường `×n`, không chỉ số đường |
| Lược | Lý do, danh sách, vị trí bản đầy đủ |

Kiểm tra: `FK nguồn = FK qua đường + FK qua tag + FK lược`. Tổng số đường
có thể nhỏ hơn số FK qua đường. Không lấy `relations` trong `.check.json`
làm số FK schema khi có gộp/tags. Tránh đếm hai lần FK đã xuất hiện ở cả
đường và tag. Quan hệ độc lập hoặc bảng không có FK vẫn được giữ nếu nằm
trong phạm vi; không tự tạo đường để làm hình liền mạch.

## Bố cục kế thừa bộ gốc

Hộp nằm trên lưới; đo chữ thật bằng Times New Roman để định kích thước.
Các cổng trên mỗi cạnh được xếp theo vị trí đầu bên kia, chừa khoảng cho
ký hiệu chân chim. Đường ra khỏi cổng có đoạn thẳng riêng, rồi A* tìm
đường ngang/dọc tránh hộp, phạt bẻ góc, chồng và giao cắt. Nhãn đặt trên
đoạn còn khoảng trống. SVG và PNG dùng chung hình học.

Tối ưu thử hoán đổi ô bằng seed cố định, lọc theo khoảng cách/độ cản rồi
chấm sau định tuyến: chiều dài/CELL + 25×số góc + 40×giao cắt +
400×nhãn va chạm + 3000×lỗi hình học + diện tích/3000. Trọng số là heuristic
của phương pháp gốc, không phải tiêu chuẩn chất lượng học thuật. Chỉ
chọn hình qua kiểm tra và xem bằng mắt; chia module thường hữu ích hơn
thu nhỏ chữ. Panels giữ vùng module khi tối ưu; không xếp hai module vào
các vùng lưới chồng nhau. Tiêu đề panel dài cần tự rút gọn/chia dòng ở
thuyết minh; bộ vẽ chưa kiểm toàn bộ va chạm giữa panel và các vật khác.

## Giới hạn kiểm tra và tài liệu cuối

`geometry_errors=0` kiểm đoạn xiên/chồng, hộp chồng, đường đi qua nội thất
hộp. `metrics.labels=0` là heuristic đặt nhãn không phát hiện va chạm với
các hộp, ký hiệu đầu nối, đường và nhãn khác. Vẫn phải xem toàn hình vì
bộ kiểm không bao quát chữ tràn tên panel, mọi xung đột chân chim, phông
thiếu glyph, tỷ lệ chữ khi chèn tài liệu hoặc sai cardinality từ nguồn.

Xem PNG ở kích thước sẽ in; tránh nhét hàng chục bảng vào một hình A4
nếu chữ mất đọc. SVG cần đúng họ phông trên máy người nhận; PNG chốt
diện mạo nhưng phóng quá mức sẽ mờ. Khi chèn vào LaTeX dùng PNG hoặc
PDF vector chuyển từ SVG bằng công cụ sẵn có, giữ tỉ lệ và caption dưới
hình. Build PDF cuối rồi xem trang chứa hình; kiểm tra hình riêng chưa
đủ chứng minh trang báo cáo đạt yêu cầu.
