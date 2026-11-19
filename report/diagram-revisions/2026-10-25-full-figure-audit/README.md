# Rà soát ERD, UML và độ rõ của toàn bộ hình — 25–26/10/2026

Thực hiện trên nhánh `trong-edit-pic`, từ `b616e398fa9f394e8671b821dc82e922dae37058`. Không commit, push hoặc sửa `main`. Báo cáo giữ đủ **46 số hình**. Theo yêu cầu bổ sung, phần giao diện đã khôi phục đúng bố cục gốc: ba ảnh điện thoại hoặc hai ảnh dashboard trong cùng hình; không tách trang và không thêm vùng phóng to. PDF cuối có **167 trang**, giảm 22 trang so với lượt dàn UI 189 trang. Bản PDF hiện hành: [report/main.pdf](../../main.pdf).

## ERD 2.5

Đối chiếu bằng AST của [storage.py](../../../products/be/storage.py) và SQLite trong bộ nhớ, không khởi động ứng dụng hoặc mở cơ sở dữ liệu thật. Giữ đủ 7 bảng, 70 cột, kiểu dữ liệu, PK, NOT NULL, default và các ràng buộc UNIQUE. [Schema đầy đủ và kiểm tra](diagram-validation.json).

| Bảng | Số cột | Vai trò |
|---|---:|---|
| reports | 26 | Báo cáo cứu hộ và trạng thái nghiệp vụ |
| report_events | 10 | Nhật ký thay đổi báo cáo |
| messages_dedup | 11 | Chống lặp message và lưu kết quả xử lý |
| operators | 9 | Tài khoản điều phối |
| sessions | 5 | Phiên xác thực |
| teams | 7 | Đội cứu hộ |
| server_meta | 2 | Metadata và version máy chủ |

Sơ đồ không có icon. Dùng Crow's Foot: `||` đúng một, `o|` không hoặc một, `o<` không hoặc nhiều. Nét đứt biểu diễn quan hệ **không định danh**, vì PK của thực thể con độc lập với PK cha; không dùng nét đứt làm ký hiệu thay thế cho việc thiếu ràng buộc SQL.

Ba liên hệ logic: một report có 0..N event; mỗi event tham chiếu một report; một team có 0..N report và report có 0..1 team; một operator có 0..N session và session có 0..1 operator theo nullability DDL. Ứng dụng tạo session với operator hợp lệ và xóa session có operator_id NULL khi khởi tạo; sơ đồ vật lý vẫn thể hiện chính xác DDL hiện tại. `REF` là tham chiếu logic, **không gắn nhãn FK giả**, vì DDL chưa khai báo FOREIGN KEY. UNIQUE của dedup là cặp `(client_id, sequence_number)`; không nối dedup tới reports bằng một FK không tồn tại. `actor` của event là chuỗi tên thao tác.

Không tạo thêm bảng user di động, ảnh hoặc cluster: dữ liệu người dùng di động nằm ở Hive, ảnh là tệp uploads và snapshot cluster nằm trong RAM. Các thành phần này được trình bày ở sơ đồ kiến trúc, không biến thành thực thể SQLite.

## Use case 2.7–2.9

Giữ nền trắng, nét đen; actor stick figure nằm ngoài ranh giới subject; ca sử dụng là ellipse. Giữ 15 use case tổng thể, 8 use case mobile và 10 use case dashboard. Association không có mũi tên; `include` từ ca cơ sở tới phần dùng chung; `extend` từ ca mở rộng tới ca được mở rộng, nét đứt và đầu mũi tên mở. Đăng nhập là tiền điều kiện của thao tác bảo vệ, không nối include tới mọi chức năng.

Theo yêu cầu bổ sung, **36 liên kết nghiệp vụ đều chỉ có hai đầu mút, là đoạn thẳng trực tiếp**: tổng thể 16, mobile 10, dashboard 10. Điểm nối nằm ở mép trái/phải ellipse để không cắt qua chữ của các ca bên cạnh. Draw.io đặt `edgeStyle=none`, không có waypoint cho các liên kết này. Các đoạn tạo hình tay/chân actor không phải liên kết nghiệp vụ. [Danh sách điểm nối](diagram-validation.json), [kết quả kiểm tra](structural-checks.json).

Chuẩn đối chiếu: [OMG UML 2.5.1, §18.1.4](https://www.omg.org/spec/UML/2.5.1/PDF), [Crow's Foot notation — diagrams.net](https://www.drawio.com/docs/tutorials/crows-foot-notation/).

## Độ rõ và bảo toàn nội dung

- [Bảng quyết định cho từng hình, đủ 46 hình](audit-table.md); [inventory trước](inventory-before.json), [inventory sau](inventory-after.json).
- 12 sơ đồ được xuất lại PDF/SVG/Draw.io, kiểm tra khung chữ và chồng chữ. 11 sơ đồ đen trắng có ba kênh RGB bằng nhau; hình 2.6 giữ hai vùng xanh/tím của bản gốc. Các sơ đồ kiến trúc khác giữ màu và icon hiện có.
- Các biểu đồ giữ ý nghĩa trục, thứ tự lớp/chuỗi, thang màu và dữ liệu nguồn. Loss/metrics/recall và confusion chuyển sang PDF vector có chữ lớn. Hình lỗi validation giữ đúng 12 ảnh được notebook chọn theo confidence giảm dần, cùng nhãn/confidence/true_prob. Không huấn luyện hoặc suy luận lại.
- Giữ nguyên cả tệp ảnh và bố cục 12 ảnh điện thoại, 8 ảnh dashboard theo yêu cầu bổ sung. File `user-interfaces.tex` khớp nguyên byte với HEAD trước đợt rà soát; không còn `ContinuedFloat`, vùng crop/zoom hoặc trang tách riêng. Chấp nhận cỡ chữ bên trong UI gốc để bảo toàn cách dàn trang đã yêu cầu.
- [Kiểm tra bảo toàn nguồn](source-integrity.json): 133/133 bản sao trước sửa khớp hash; 23 tệp UI và bố cục LaTeX giao diện không đổi so với HEAD; 30 đầu vào biểu đồ/ảnh ví dụ không đổi so với HEAD. Có 4 hash provenance hình đã cũ từ trước đợt sửa; `make figures` cập nhật provenance theo artifact hiện có, không sửa artifact đầu vào.

Đã xem các [contact sheet của toàn bộ hình](contact-sheets/) và các trang chi tiết ERD, UML, lưu đồ, biểu đồ; kiểm tra lại trang UI sau khi khôi phục bố cục gốc. Cỡ chữ sơ đồ sửa mới tối thiểu 9 pt ở kích thước đưa vào PDF. Đo font vector không đo được chữ đã raster hóa bên trong screenshot; vì vậy không suy diễn cỡ font UI từ font caption.

## Tái tạo và kiểm tra

Từ gốc repository:

```bash
make -C report readable-diagrams
make -C report figures
make -C report content
make -C report check
git diff --check
```

`make system-diagrams` cũng sinh sáu sơ đồ chi tiết rồi áp dụng bộ sửa đọc rõ; ERD được chuyển tới generator Crow's Foot mới để không tái xuất icon. Đã thử đường sinh sáu sơ đồ với output/review riêng trong `/tmp`, đạt cả sáu. Script `reflow_report_figures.py` chỉ là migration bố cục một lần; có chặn chạy lần hai trước mọi thao tác ghi.

Bộ nguồn sửa được: [12 trang Draw.io](readable-diagrams.drawio), [generator](../../scripts/build_readable_report_diagrams.py), [hash nguồn](diagram-sources.json), [preview](previews/). `before/` là bản lưu trước đợt sửa, không phải nguồn được chèn vào báo cáo.

Kiểm tra cuối và hash PDF được ghi trong [validation-final.json](validation-final.json). `make check` là kiểm tra bản nháp; không thay thế các điều kiện hành chính/nghiệm thu vốn có của báo cáo.
