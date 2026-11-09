# P02 — dữ liệu/LR/compression/scope

Đã đọc và giữ luồng P01. Source hashes trong source-hashes.json, HEAD/dirty baseline ../run-baseline, output-hashes.json chốt checkpoint P02; source có thể được P03/P07 cập nhật tiếp, không tái dùng hash P02 như final.

Đầu ra: data-card.md, image-profile.csv (20 nhóm), lr-audit.csv (32 trạng thái), lr-sanity-audit.csv, criterion-source-map.csv, compression-audit.csv (12 cấu hình), error-counts.csv/error-taxonomy.md, phone-audit.csv (32 phiên), measurement-scopes.csv và preflight.md. Có script analyze.py, exporter report/scripts/export_revision_profiles.py nối Makefile results; generated qua script, không chỉnh tay.

Nhận xét B2/C1/C2/C3/C6/C7: giải trình bằng raw/header/mapping. 1.702 ảnh khớp metadata; 12 model metrics khớp confusion/Accuracy/F1/critical/median và exact artifact hashes;32 phone JSON khớp ID/label/metric/summary. Không train/inference. B2 giữ QAT xấu, pruning không đồng nhất byte/params/speed. Unknown URL/license/IAA/event/source independence và split-at-training seed1024 vẫn còn. C6 PARTIAL do APK/E2E raw/thermal/repeated sessions thiếu. C7 chưa expert dispatch validation.

LR raw byte hash khác model, bản dựng CRLF trong bộ nhớ khớp hash lịch sử; giữ mismatch và không đổi dữ liệu/manifest (lr-hash-discrepancy.json). Phép kiểm đại số trên bảng hiện tại độc lập với chứng nhận byte huấn luyện. First analysis exit1 được giữ analysis-first-attempt.log; sau disposition, analysis-command.exit=0.

Nguồn ngoài: WHO poster/ref-card/overview đọc qua web, download trực tiếp403, registry S2 lớn chưa đọc toàn văn. PDF luật chính thức49trang tải được, hash raw/retrieval.json; đọc ảnh p1/p23/p24 (Điều26 khoản1 a/g/h), không suy ra numerical weights. source-verification.md ghi phạm vi.

Build content: build-content.exit; check: check.exit. Lần đầu check phát hiện token canonical quá dài tràn hbox; đã cho phép ngắt ở dấu gạch dưới, không giảm chữ/lề. Log trước sửa được giữ riêng. PDF text mới lưu tại đây; visual cuối cả variants/deliverables P07. Build/check không scientific acceptance.

P03 chỉ replay statistics từ CSV/checkpoints, không tune/refit/RQ campaign. P04/P05 cần kiểm runtime/device và phục hồi raw trước chạy. A3 DEFERRED_BY_USER; A1 chưa sửa trạng thái.

Receipt note: một lượt check/text đã chạy khi rebuild còn ghi PDF nên không hợp lệ (check-stale-during-build.log). Đã đợi build kết thúc và chạy lại; chỉ check.log/check.exit và pdftotext.log cuối được dùng.
