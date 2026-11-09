# Rà PDF cuối — 08/11/2026

Hai bản nội dung đều **174 trang**, 48 hình và 39 bảng, 112 trang từ Mở đầu đến hết Kết luận/hướng phát triển. Bản tin Việt/Anh 1/1 trang; tóm tắt Việt/Anh 3/3 trang. `report/main.pdf` khớp nguyên mã băm với bản content cuối. Không dùng PDF cũ để báo build mới.

## Kiểm đã thực chạy

`report-checks/commands.json` ghi tám command, tất cả exit0: content, content-twoside, deliverables, check, check-twoside, float-content, float-twoside, diff-check. Checker đối chiếu nhãn/caption/danh mục với PDF đủ 48 hình/39 bảng; hai bản tin vẫn đúng giới hạn một trang. Các font trong cả sáu PDF được kiểm nhúng bằng pdffonts; text/log/hash ở `report-checks/pdf-inspection.json` và các tệp kế bên. Không có lỗi tràn khung, tham chiếu/trích dẫn chưa giải quyết hoặc nhãn lặp trong các kiểm cuối.

## Phạm vi đã xem

- Đã xem toàn bộ 174 trang content qua năm contact sheets 30dpi, gồm trang trước/sau vùng dữ liệu, phương pháp, kết quả, giới hạn, kết luận và biểu mẫu. Bản hai mặt cũng được render đủ 174 trang; không có trang khác pixel ở phép đối chiếu30dpi. Đây là kiểm bố cục tổng thể, không phải đọc chi tiết toàn văn từng hình ở độ phân giải in.
- Đã xem chi tiết105dpi các trang PDF content **16,75,97,113,114,118,130,132**: bảng công bố/ghi chú chương trình, truy vết split, thiết kế CPU, đoạn phân tích mới/bảng4.12, RQ2 còn8sai lệch, limitation và conclusion.
- Đã xem trực tiếp105dpi hai trang **97,114** của content-twoside để đối chiếu phần phương pháp và bảng mới. Các trang detail khác của cả hai bản được render và lưu; không gọi mọi ảnh đã render là đã đọc chi tiết.
- Đã xem chi tiết toàn bộ sáu trang summary Việt–Anh và hai bản tin. Bảng công bố đủ sáu cột, tám tác giả; metadata chapter vẫn chưa cập nhật theo bằng chứng thật.

## Nhận xét và giới hạn

Bảng4.12 đầy đủ chín điều kiện, không chồng chữ/tràn lề; float ở trang114, liền sau phần diễn giải trang113, không qua chương. Các trang phương pháp và kết luận giữ font/lề hiện hành. Không sửa Draw.io, hình gốc hoặc StudentPhoto.

Tóm tắt Việt tăng từ hai lên ba trang do bổ sung kết quả CPU và provenance; trang3 là phần8 tiếp nối tự nhiên. Không có giới hạn hai trang được áp trong checker; không giảm chữ/lề hoặc loại nội dung để ép hai trang. Trang17 biểu mẫu trong quyển và trang130 cuối chương có khoảng trắng kết thúc nội dung tự nhiên; các sơ đồ ngang giữ khoảng trắng để đọc được. Phần trống nhận xét GVHD và ảnh A3 vẫn theo scope cũ, không được build coi là đã hoàn thiện hồ sơ.

Build/check đạt không đồng nghĩa đã nghiệm thu hoặc đạt release. Giữ nguyên raw failures và các gap thống kê/E2E/provenance/công bố.
