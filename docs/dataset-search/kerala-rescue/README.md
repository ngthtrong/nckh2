# KeralaRescue: các bước sau khi nhận bản bài báo gốc

Trạng thái ngày **29/10/2026**: **đã xác minh PDF xuất bản; chưa có tệp yêu cầu cứu hộ để làm pilot hoặc chạy RQ**. Mục tiêu là tiếp cận dữ liệu nghiên cứu lịch sử của lũ Kerala 2018, không lấy số liệu trong bài làm bản ghi thực nghiệm mới.

## 1. Đã thực hiện trên bản người dùng tải

Tệp: [1-s2.0-S2212420922001273-main.pdf](../paper/1-s2.0-S2212420922001273-main.pdf), 13 trang, DOI `10.1016/j.ijdrr.2022.102908`.

- Xác minh tiêu đề, DOI, số trang, mã SHA-256 và **0 tệp nhúng**; kiểm tra trực quan trang 4 và 11.
- Đọc lại §2.3, §2.5–2.6, Table 2, kết quả và Data availability. Nội dung `pdftotext -layout` của bản này trùng bản PDF đã đọc ở đợt khảo sát trước, dù mã băm hai PDF khác nhau.
- Truy nguyên các liên kết gốc; thực hiện thêm [8 truy vấn](search-log.json) có ghi ngày. Kiểm tra mã và một kho dữ liệu liên quan qua GitHub connector; không gửi tin nhắn, đăng ký hoặc ghi vào dịch vụ nguồn.
- Chuẩn bị [thư xin dữ liệu](data-request.en.md), [ánh xạ trường dự kiến](field-map.csv), [manifest tiếp nhận](intake-manifest.template.json) và [protocol pilot Kerala](pilot-protocol.md). Đây là tài liệu chuẩn bị, chưa phải adapter hay nhãn đã hoàn thành.

Biên nhận: [paper-audit.json](audit/paper-audit.json), [source-evidence.json](audit/source-evidence.json). Mã kiểm tra PDF: [audit_paper.py](audit_paper.py).

## 2. Những điều bản gốc xác nhận và ý nghĩa đối với RQ

| Chứng cứ trong PDF | Điều có thể sử dụng | Điều không suy ra được |
|---|---|---|
| §2.3, trang 4: JSON 27 cột, có dữ liệu vị trí và nhu cầu; tác giả lấy với sự cho phép của nhà phát triển | Có cơ sở để đề nghị bản dữ liệu cấp yêu cầu và data dictionary | Chúng ta đã có 27 cột đó, hoặc giấy phép CC BY của bài tự cấp quyền cho dữ liệu nguồn |
| Table 2, trang 6: 45.322 yêu cầu ban đầu; 39.950 sau lọc/định vị | Hai phiên bản cần hỏi khi xin dữ liệu | 39.950 sự cố cứu hộ độc lập; chênh lệch 5.372 đều là bản sao |
| §2.3: nguồn khử trùng bằng thông tin người yêu cầu, vị trí và thời gian; đã loại hơn 5.000 bản ghi | Cần bản trước khử trùng và lineage nếu còn | Heuristic của nguồn là gold cùng sự cố, hay tập sau khử trùng đủ để thử natural duplicates |
| §2.5, trang 5: người gửi hộ có thể ở nơi khác; ưu tiên địa điểm trong nội dung | Cần kiểm tra vai trò địa điểm, giữ tọa độ gốc và tọa độ suy ra riêng | Tọa độ/GPS của người đăng là nơi cần cứu; tâm polygon là địa chỉ chính xác |
| §2.3: loại tọa độ có sai số trên 1.000 m trong nghiên cứu gốc | Hỏi rõ ý nghĩa và đơn vị `coordinate_accuracy` | Sai số dưới 1.000 m tự đạt yêu cầu phân biệt các sự cố cứu hộ gần nhau |
| §2.6, trang 5: phân loại nhu cầu cứu hộ/thực phẩm/nước/thuốc/quần áo | Hỗ trợ lọc và mô tả nhu cầu | `needrescue` là mức ưu tiên hoặc số người mắc kẹt; độ đồng thuận phân loại nhu cầu là độ tin cậy gold RQ của nhóm |
| Results, trang 6–9: tổng hợp theo thời gian, district/taluk và tương quan giữa các nguồn | Bối cảnh về phân bố nhu cầu | Có ground truth phân cụm sự cố, priority ranking hoặc nhật ký lợi ích cứu hộ |
| Data availability, trang 11: dẫn RebuildEarth Slack | Đầu mối tiếp cận qua tác giả hoặc người quản lý dữ liệu | Có archive tải công khai ngay trong PDF |
| Table 1, trang 4: ví dụ Telegram/Twitter được ghi là fictitious | Chỉ dùng giải thích định dạng | Trích hai ví dụ làm dữ liệu thực hay pilot độc lập |

Nguồn gốc: [bài báo](https://doi.org/10.1016/j.ijdrr.2022.102908). Các số trên là **do bài công bố**, chưa được tái kiểm đếm trên dữ liệu thô của nhóm.

## 3. Kết quả kiểm tra đường lấy dữ liệu hiện tại

| Đầu mối | Quan sát trong lần kiểm tra này | Hành động tiếp theo |
|---|---|---|
| `rebuildearth.slack.com` | HTTP 403, không lấy được archive nghiên cứu; không đăng nhập hay vượt kiểm soát truy cập | Hỏi tác giả về bản đã ẩn danh hoặc đường tiếp cận hợp lệ hiện tại |
| `keralarescue.in` | HTTP 200 nhưng là trang giữ/bán tên miền, không còn giao diện dữ liệu cứu hộ trong nội dung trả về | Không xem HTTP 200 là dữ liệu khả dụng; dùng đầu mối nghiên cứu/kho mã lịch sử |
| [raksha-life/rescuekerala](https://github.com/raksha-life/rescuekerala) | Có mã `Request` và `RequestUpdate`; `hig/med/low` nằm trong schema cập nhật | Xin snapshot thật và tài liệu người gán/thời điểm; chưa coi schema là nhãn ưu tiên đã nhận |
| Route `request_update/` trong mã | Hàm đã đọc xử lý POST ghi cập nhật, không phải đường tải lịch sử GET | Không gọi endpoint này để thử lấy dữ liệu; không triển khai ứng dụng để giả định sẽ có database năm 2018 |
| [raksha-life/data](https://github.com/raksha-life/data) | README nói dữ liệu từ website chính quyền; mẫu `lsgi_site_data/1.json` là metadata hành chính/dân số năm 2019 | Không nhầm với 45.322 yêu cầu cứu hộ; chưa tải toàn bộ kho |
| [OpenSalve](https://github.com/raksha-life/OpenSalve) | Có mã nền tảng liên quan, README chưa phải bản phát hành corpus nghiên cứu | Không dùng dữ liệu mẫu hoặc mã hệ thống làm bằng chứng đã có dữ liệu Kerala 2018 |

Chưa tìm thấy archive cấp yêu cầu được xác nhận là dữ liệu dùng trong bài qua những đường đã kiểm tra. Đây là giới hạn phạm vi tìm kiếm, không khẳng định dữ liệu không tồn tại ở nơi khác.

## 4. Việc đã chuẩn bị để tiếp tục

**Bước cần thực hiện bên ngoài trước:** gửi [thư xin dữ liệu](data-request.en.md) cho tác giả liên hệ. Địa chỉ `jcy204@exeter.ac.uk` lấy từ trang 1 của PDF; chưa xác minh khả năng nhận thư hiện tại. Thư đã nêu rõ nhu cầu bản gốc trước khử trùng, bản xử lý, schema/timezone, vị trí cần cứu và lịch sử cập nhật nếu có. **Thư đang ở dạng nháp, chưa gửi.**

Khi nhận được tệp:

1. Lưu bản gốc ngoài repository; điền [manifest](intake-manifest.template.json), SHA-256, phạm vi và điều kiện sử dụng. Đối chiếu schema với [field-map.csv](field-map.csv); không tự đặt tên hay suy ý nghĩa đủ 27 cột từ mô tả trong bài.
2. Profile toàn bộ cấu trúc và đọc 50–100 bản ghi theo các nhóm thiếu/trùng/địa điểm/ngôn ngữ. Đặc biệt kiểm tra người gửi hộ, timezone, phân giải vị trí và tồn tại các trường cập nhật/ảnh.
3. Chọn 100–200 báo cáo trong các cửa sổ trọn vẹn để hai người gán độc lập theo [protocol pilot](pilot-protocol.md). Pilot có thể không đạt nếu thiếu chứng cứ liên kết sự cố; không bù bằng nhãn máy.
4. Chỉ khi có đầu vào và gold đủ điều kiện mới tạo adapter, khóa cấu hình và chạy nhánh dữ liệu thực riêng. Giữ nguyên artifact camera-ready và các công thức hiện tại.

**Đối với RQ1:** ưu tiên số một là chứng cứ cùng sự cố và vị trí thực sự cần cứu. **Đối với RQ2:** các mức high/medium/low chỉ dùng được khi xác nhận người gán, mốc thời gian, đơn vị yêu cầu và quan hệ với nhóm sự cố; chúng chưa tự là benefit. **Đối với RQ3:** nếu thiếu nhật ký nguồn lực/kết quả, tiếp tục là mô phỏng trên đầu vào thực.

## 5. Kiểm tra và tái lập

Từ thư mục gốc repository:

```bash
python3 docs/dataset-search/kerala-rescue/audit_paper.py
python3 docs/dataset-search/scripts/validate_dossier.py
python3 docs/dataset-search/round2/validate_dossier.py
```

Lệnh đầu xác minh đúng PDF, các phần dữ liệu đã định vị và các tệp chuẩn bị; không đo chất lượng thuật toán hay xác nhận nhãn. `audit/paper-audit.json` giữ trạng thái `awaiting_request_level_data`, không có kết quả RQ mới. Không thể tính coverage hay chọn báo cáo pilot thực trước khi nhận dữ liệu cấp yêu cầu.
