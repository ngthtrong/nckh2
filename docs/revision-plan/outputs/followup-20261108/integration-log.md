# Tích hợp bổ sung P07

Nguồn của đợt này là `evidence/` cho P02/P05/publication, `../phase-03/followup-20261108/` cho RQ2 và `phase-04/` cho CPU corruption. Các output P01–P08 cũ được giữ nguyên; không giả định freeze cũ còn khớp PDF sau sửa. Người dùng xác nhận chưa có hồ sơ bổ sung; những trường phụ thuộc vẫn OPEN/PARTIAL.

| Vùng report | Thay đổi | Căn cứ |
|---|---|---|
| data.tex | 1.702 records khớp tám trường, checkpoint seed1024/đường dẫn split; chưa checksum lúc train | evidence/local-evidence-audit.json; không suy source_group thành nguồn độc lập |
| evaluation-design.tex | Giới hạn câu “chỉ tái phân tích” cho phần RQ, tránh phủ định inference CPU mới | Giữ không rerun generator/clustering/training |
| setup.tex | Phép CPU mới và scope timing/group/bootstrap/label uncertainty | phase-04/protocol.json, environment.json, clean-parity.json |
| results.tex | Bảng9điều kiện và hiệu ghép cặp; RQ2:3rawp+5Holm,15Holm lịch sử tự nhất quán | Raw CPU + P03 followup; không sửa số RQ lịch sử |
| limitations/conclusion | CPU_ONLY có suy giảm; chưa Android/camera/expert; raw E2E vẫn thiếu | Scope đã đo, không ngoại suy |
| research-body Việt–Anh | Kết quả CPU mới, chương trình ISDS xác nhận danh tính bài, chapter metadata chưa xác minh | Shared source phục vụ quyển và tóm tắt; giữ user-confirmed published |
| export_results.py + export_image_quality.py | Sinh bảng/macros/provenance từ raw CPU có hash và metric audit | Không sửa generated tay, không inference trong build |

Bốn deliverables đều build lại. Bản tin không đổi nội dung vì không có khẳng định mâu thuẫn với phép CPU bổ sung; phần tóm tắt dùng shared source đã nhận kết quả mới. Không sửa template/font/lề, hình, app/backend/model, các bảng số RQ hoặc ledger cũ để tạo kết quả thuận lợi.

[Chương trình ISDS chính thức](https://isds.ctu.edu.vn/2026/author/program) và program booklet trang22 xác nhận paper6444, tiêu đề và tám tác giả. Đây là xác minh danh tính/lịch trong chương trình, không chứng nhận đã trình bày hoặc chapter đã online. DOI/date/pages/volume/year cấp bài vẫn UNKNOWN; A1 OPEN. Chi tiết hash/PDF/source/search ở evidence/README.md.

Checks và visual cuối: report-checks/commands.json, pdf-inspection.json, layout-review.md. Bản content và hai mặt174trang, bản tin1/1, tóm tắt3/3. A3 DEFERRED_BY_USER. Không chạy lại P08, gửi phản hồi ngoài, commit hoặc push.
