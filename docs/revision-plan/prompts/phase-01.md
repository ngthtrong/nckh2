# Prompt Phase 01 — Sửa phạm vi khoa học và claim, bổ sung Future Work

Bạn làm việc tại `/home/ngthtrong/nckh2` cho đề tài **Xây dựng hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI (THS2026-68)**. Thực hiện riêng phase này; việc sửa báo cáo được yêu cầu bởi prompt, không tự chạy phase tiếp.

## A. Bối cảnh nghiên cứu

Hội đồng yêu cầu giải trình mô hình văn bản, tích hợp đa phương thức, LR và cơ sở ưu tiên (B1/B3/B4/C3/C7), cùng D1–D3. Đã có mô hình ảnh, LR có cấu trúc và hệ thống app–server; chưa tìm trained NLP tiếng Việt tự do hoặc learned fusion trong audit. **Người dùng sẽ thêm ảnh A3 sau**: giữ placeholder, ghi hoãn, không tìm/chèn/hỏi ảnh. Phase này sửa phát biểu theo nguồn thực tế và viết Future Work ngay, không lấp khoảng trống nghiên cứu bằng tên gọi mới.

## B. Trạng thái và nguồn

Đọc quy tắc repo, `report/README.md`, `report/RULES.md`; `docs/revision-plan/{00-repository-audit.md,01-review-matrix.md,03-immediate-fixes.md,04-phase-roadmap.md}`; request+amendment+snapshot trong `docs/revision-plan/evidence/`. Thuyết minh là `resource/Thuyết minh NCKH -THS2026-68.docx`, mục12–16: văn bản tự do/DistilBERT và bộ model đa phương thức là cam kết khác với LR hiện tại.

Đối chiếu trực tiếp `products/fe/app/lib/domain/services/urgency_logistic_model.dart`, `presentation/controllers/app_controller.dart`, `data/models/rescue_record_payload.dart` và `products/be/cluster_service.py`. Snapshot: app tính và gửi `E_i`; adapter đọc payload `urgency`, nếu thiếu dùng từ khóa description; `ReportV2.E=urgency`. Không có code đọc E_i trong backend đã khảo sát. LR v5 (`products/fe/model/urgency_ei/`) dùng32 OR states của5 cờ, không NLP/clinical gold. Report `methods.tex`, `results.tex` và research-body có mệnh đề integration mạnh hơn code. Xác minh lại trước sửa nếu code đã đổi.

P00 đã tạo plan; `outputs/phase-00/handoff.md` là artifact dự kiến nếu có refresh, có thể chưa tồn tại. Nếu thiếu, dùng audit/snapshot hiện có và ghi rõ, không giả vờ đã đọc.

## C. Mục tiêu và phạm vi

Sửa scope/claim, mô tả runtime và giới hạn; bổ sung IP/Wi-Fi, audio/voice, complete outage/no phone dưới Future Work. Không đổi code app/server, hợp đồng đồng bộ, trọng số hoặc model.

## D. Tác vụ

1. **P01.01:** ghi status/hash input; đọc DOCX và source; tạo `docs/revision-plan/outputs/phase-01/scope-register.md` theo từng cam kết registered/actual/evidence/gap. Ghi NLP một phần/chưa chứng minh, không khẳng định nhóm chưa từng nghiên cứu ngoài repo.
2. **P01.02:** tạo `dataflow.md` với đường computed→sent→stored→consumed; sửa đúng đoạn E_i trong `report/chapters/02-data-methods/sections/methods.tex`, `report/chapters/04-evaluation/sections/results.tex`, architecture/research-body khi có claim sai. Tách “thiết kế dự kiến” và adapter hiện hành. Không âm thầm nối E_i vào rank.
3. **P01.03:** sửa `scope.tex`, introduction/architecture/conclusion cần thiết: tiếp nhận nhiều loại dữ liệu, tích hợp các bằng chứng bằng công thức và học fusion là mức khác nhau. Nêu LR là surrogate 5 cờ, nguồn dấu hiệu khác xác nhận chính sách dispatch. Tạo `claim-ledger.csv` (claim,source,status,section,action); giảm claim “hoàn chỉnh/hiệu quả cứu hộ” nếu chưa đo. Kết quả âm RQ dùng số đã lưu, không tính test mới ở phase này.
4. **P01.04:** viết `future-work.md` và cập nhật `report/chapters/conclusion.tex`: D1 định vị nhiều nguồn có uncertainty, IP không mặc định hơn GPS; D2 audio→ASR→trích thông tin→xác nhận, rủi ro tiếng ồn; D3 store≠deliver, SMS cần cell/gateway, DTN cần relay/contact, người không máy cần báo hộ/hotline/đội tại chỗ. Không triển khai hoặc tạo số đo.
5. **P01.05:** đối chiếu diff với source, kiểm các mệnh đề mới, build `make -C report content` nếu môi trường đáp ứng rồi `make -C report check`/PDF text/log cho phần đổi. Không chỉnh tay generated, không tái tạo Draw.io manual. Ghi command/exit và chưa kiểm; tạo `handoff.md`.

## E. Nguyên tắc và rủi ro

Bảo toàn tất cả sửa đổi sẵn có, kết quả cũ và lỗi thực nghiệm. Không biến LR thành NLP, source-mapped IITT thành chính sách cứu hộ đã được chuyên gia xác nhận, hoặc simulated outcome thành thực địa. Không thay publication status A1 ở phase này. Không commit/push, xóa dữ liệu, gửi tin nhắn hoặc mở rộng code. Rủi ro chính là thu hẹp claim bị hiểu nhầm đã hoàn thành cam kết: ledger phải giữ “chưa hoàn thành” rõ.

## F. Deliverables

Nguồn LaTeX đã nêu; `outputs/phase-01/{scope-register.md,dataflow.md,claim-ledger.csv,future-work.md,handoff.md}`; log/check và PDF nếu build. Handoff nêu đoạn đã sửa để P02 không viết lại; raw và input hashes đi kèm.

## G. Acceptance criteria và cổng chuyển

Luồng E_i và từng mũi tên khớp code; LR≠NLP; không claim learned fusion; cam kết chưa đạt không bị che; D1–D3 đủ và chỉ proposed; A3 hoãn. Check phù hợp đạt hoặc limitation môi trường nêu rõ; không coi build pass là scientific acceptance. Bàn giao cho P02, không chạy P02 tự động.

## H. Final report

Báo: việc hoàn thành; file sửa/tạo; kiểm thử/build thực chạy và giới hạn; nhận xét xử lý bằng evidence; gap còn lại; quyết định khoa học/kỹ thuật; đường dẫn handoff và tác vụ P02. Không gọi một phép sửa mô tả là đã thực nghiệm NLP/fusion.
