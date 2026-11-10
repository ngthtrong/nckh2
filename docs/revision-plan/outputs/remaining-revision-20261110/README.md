# Chỉnh sửa các nhận xét còn lại — 10/11/2026

Đây là đợt tiếp nối [cập nhật từ kết quả local](../local-report-update-20261110/README.md). Đã chỉnh báo cáo, sửa lỗi trong mã hiện có và kiểm hồi quy/tích hợp bằng nguồn lực local. [Bảng đối chiếu BC/ND/MC](../../remaining-comments-20261110.md) là danh sách hiện hành; hồ sơ các đợt trước giữ nguyên như lịch sử.

## Phạm vi theo xác nhận của nhóm

[user-clarifications.json](user-clarifications.json) lưu các quyết định:

- Ảnh gồm cả nhóm tự chụp và thu thập web; chưa có ánh xạ nguồn theo từng ID.
- NLP/fusion đã cập nhật vào mobile do nhóm khác phụ trách. Báo cáo ghi nhận thông tin này; không gán metric offline cho APK chưa bàn giao.
- Bỏ qua chẩn đoán PTQ/QAT bổ sung, đo lặp CPU–điện thoại, pin/RAM. Không chạy thêm các phần này.
- Khắc phục lỗi mất mạng và kiểm trong môi trường hiện có. Không có Android kết nối hoặc bằng chứng SMS/mạng di động thật.
- Điều phối xét chi phí di chuyển và thí điểm cùng đơn vị cứu hộ chỉ viết trong hướng phát triển, không thực thi.

## Thay đổi báo cáo

Chuyển phân lớp/lưu trữ/API, chi tiết thao tác, giao diện và bốn lưu đồ xuống cuối phụ lục bổ sung; giữ đủ hình và nhãn, thêm đường tra cứu. Viết lại Kết luận, mục phạm vi và chỉ tiêu đánh giá. Không giảm cỡ chữ để rút trang. [layout-moves.json](layout-moves.json) ghi các khối chuyển.

Bổ sung tổng quan và bảng đối chiếu với [AlleyFloodNet](https://www.mdpi.com/2079-9292/14/10/2082) và [EmergencyNet](https://zenodo.org/records/3963734). Metadata và nhiệm vụ đã đối chiếu nguồn gốc trong [literature-verification.json](literature-verification.json). Không so trực tiếp Accuracy khác nhiệm vụ hoặc coi feature fusion trong CNN là fusion ảnh–text.

Nguồn ảnh hỗn hợp, tích hợp mobile, Bảng B.6, kết luận và biểu mẫu/bản tin/tóm tắt Việt–Anh được đồng bộ. Ký hiệu top-k, số thập phân Việt–Anh và font URL trong danh mục được thống nhất. Ba trang minh chứng sản phẩm và trang đầu bản tác giả bài báo dùng số trang liên tục của quyển; PDF nguồn giữ nguyên. Trang bản tác giả không thay hồ sơ DOI/số trang chapter hoặc xác nhận kỷ yếu.

## Khắc phục phần mềm và bằng chứng

[software-evidence.json](software-evidence.json) khóa hash 14 tệp mã/kiểm thử/phụ thuộc và chín log gốc. Exporter báo cáo kiểm các hash này trước khi sinh số liệu; build không tự chạy kiểm thử thiết bị.

| Hạng mục | Kết quả | Bằng chứng |
|---|---|---|
| Sáu hồi quy gửi/SOS/đồng bộ sau khi controller đóng và probe mạng lỗi | Cả sáu không đạt trước sửa, cả sáu đạt sau sửa | [trước](checks/offline-regression-before.log), [sau](checks/offline-regression-after.log) |
| Flutter unit/widget toàn bộ | 284 đạt, 3 bỏ qua | [log](checks/flutter-all.log) |
| Phân tích tĩnh bốn tệp Dart thay đổi | Không có vấn đề | [log](checks/flutter-analyze.log) |
| Các suite backend API/contract/cluster liên quan | 78 đạt, gồm 3 kiểm bản sao đồ thị | [log](checks/backend-tests.log) |
| App Linux–backend HTTP thật | Hai kịch bản đạt | [log](checks/linux-integration.log), [receipt](checks/linux-integration.json) |

Controller không khởi tạo lần gửi khi đã đóng và không thông báo giao diện sau khi phản hồi muộn. Bản ghi đã lưu vẫn được giữ; probe lỗi đi theo fallback thay vì làm rơi thao tác. Không sửa trạng thái SMS thành “đã giao” khi chưa có bằng chứng.

Backend tạo nút canonical trước quantile/top-k theo khóa exact của trường mô hình và nội dung, giữ ánh xạ về mọi ID gốc. Kiểm nhân bản 2/5 lần giữ cặp/cạnh/ngưỡng/phân hoạch/ưu tiên/centroid; báo cáo khác văn bản và hàng xem xét vẫn được giữ. Khóa ảnh/liên hệ khác được giữ riêng theo chính sách; bộ hồi quy hiện không thay đánh giá sai gộp/sai tách trên dữ liệu thật. Cache ETag có namespace chính sách mới. Không thay lõi hoặc kết quả RQ1–RQ3.

Flutter SDK local 3.47.5/Dart 3.13.4 đã giải lại bốn phụ thuộc bắc cầu trong lockfile (matcher, meta, test_api, vector_math). Test power policy khởi tạo singleton Workmanager trước khi gắn fake platform để tránh fake bị thay trên Linux; không đổi lịch nền trong mã sản phẩm.

[run_local_integration.py](run_local_integration.py) khởi chạy backend với SQLite/uploads tạm và tài khoản test, sau đó chạy hai ca hiện có bằng Flutter Linux. Nó kiểm outbox khi mất mạng/phục hồi, ảnh, phản hồi trạng thái và từ chối sửa chéo. Backend được dừng, dữ liệu tạm xóa; tệp đính kèm test ở thư mục người dùng chỉ được xóa khi đúng ID từ log và hash ảnh fixture ([receipt](checks/test-attachment-cleanup.json)). Không dùng dữ liệu vận hành.

Lần Linux này không phải raw Android Case 8 lịch sử, không xác lập cùng nguyên nhân lỗi, không kiểm suy luận ảnh trên Android và không chứng minh SMS hoặc mạng di động thật đã hoạt động. [Danh sách thiết bị](checks/adb-devices.txt) không có Android kết nối.

## Kiểm báo cáo và tái kiểm

Kết quả cuối: [validation.json](validation.json), [inventory PDF](checks/pdf-inventory.json), [biên bản báo cáo](../../../../report/audit/remaining-revision-2026-11-10.md). Các log `.log` trong thư mục checks được cho phép lưu cùng hồ sơ vì exporter dùng chúng làm đầu vào xác minh.

Từ gốc repo:

```bash
make -C report content
make -C report content-twoside
make -C report check
python3 report/scripts/check_report.py --build-dir build/content-twoside
python3 report/scripts/check_float_references.py --build-dir build/content
python3 report/scripts/check_float_references.py --build-dir build/content-twoside
python3 docs/revision-plan/outputs/remaining-revision-20261110/inspect_pdfs.py
git diff --check
```

Bộ kiểm ảnh render/font/văn bản bổ sung cho build/check; không chạy check-release và không tự điền ngày ký/nhận xét GVHD. Không sửa tmp.md, checkpoint/dữ liệu notebook gốc hoặc dùng điểm synthetic làm bằng chứng nghiên cứu. Không commit/push.
