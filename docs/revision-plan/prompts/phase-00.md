# Prompt Phase 00 — Làm mới audit và kế hoạch

Bạn làm việc tại `/home/ngthtrong/nckh2` cho đề tài **Xây dựng hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI (THS2026-68)**. Chỉ thực hiện audit và lập kế hoạch, không triển khai các phase sửa báo cáo.

## A. Bối cảnh và mục tiêu

Hội đồng nêu 20 nhận xét A1–D3 về hình thức, cam kết văn bản/đa phương thức/nén, dữ liệu, LR, RQ1–3, chất lượng ảnh, benchmark mobile và Future Work. Người dùng đã xác nhận **ảnh cá nhân A3 sẽ thêm sau**: giữ nguyên ô ảnh, `DEFERRED_BY_USER`, không tìm hoặc yêu cầu ảnh, không xem đây là blocker. Mục tiêu phase này là cập nhật evidence/gap/roadmap khi checkout khác snapshot ngày 07/11/2026, để Agent sau không dựa vào tài liệu cũ.

## B. Trạng thái, nguồn và đầu vào

Đọc `docs/revision-plan/{README.md,00-repository-audit.md,01-review-matrix.md,02-experiment-gap-analysis.md,04-phase-roadmap.md,05-traceability-matrix.md}` và `evidence/{user-request.txt,user-amendments.md,audit-snapshot.json,external-verification.md}`. Đọc quy tắc repo, `report/README.md`, `report/RULES.md` và `report/ra-soat-va-bo-sung.md` nếu có. Đọc `tmp.md` (nhận xét 06–20 có phần diễn giải, không phải nguyên văn Hội đồng). Thuyết minh chỉnh được là `resource/Thuyết minh NCKH -THS2026-68.docx`, không sửa PDF trực tiếp.

Snapshot đã tìm: 1.702 ảnh với split1.189/257/256; 32 raw image-benchmark JSON trên bốn điện thoại; PTQ/QAT/pruning và RQ1–3 có kết quả. App gửi `E_i` nhưng `products/be/cluster_service.py` đọc `urgency`/description vào `ReportV2.E`. Chưa tìm trained free-text NLP/paired multimodal gold trong 20 refs đã kiểm. E2E mobile/web được report nhưng raw/log chưa thấy. RQ kết quả có cả âm; full verifier hardcode `src/results` và pin version khác env. Các thông tin này phải xác minh lại nếu source thay đổi. Chưa cần artifact phase trước vì đây là điểm vào.

## C. Phạm vi và kết quả cần đạt

Chỉ viết `docs/revision-plan/`. Bảo toàn working tree bẩn. Phân biệt Implemented/Executed/Evaluated/Reported/Missing/Unverified và primary/replication, real/synthetic, CPU/mobile/server. Kết quả là kế hoạch có đủ 20 nhận xét, protocol thí nghiệm thật sự cần và prompt tự chứa.

## D. Tác vụ theo thứ tự

1. **P00.01:** đọc git status/diff/ref/history, lưu snapshot mới tên riêng; dùng `evidence/collect_snapshot.py audit-<timestamp>.json` với môi trường có Pillow nếu có. Không ghi đè snapshot cũ. Ghi hash các tệp đang sửa trước khi thao tác.
2. **P00.02:** đọc DOCX XML/PDF, report sources, frontend/backend/dashboard, dataset, notebooks/configs/checkpoints/log/CSV/images. Tìm nhiều vùng/nhánh trước kết luận Missing. Không checkout/switch/fetch hoặc sửa thuật toán. Output inventory có source locators.
3. **P00.03:** kiểm hashes/row counts/split/phone predictions, scope timing và reported claims; chỉ chạy kiểm tra đọc an toàn. Không chạy exporter/build vì chúng ghi report. Ghi chưa replay thống kê nếu tooling/env chưa phù hợp.
4. **P00.04:** cập nhật bảy tài liệu kế hoạch và chín prompt; mỗi nhận xét đủ hiện trạng/bằng chứng/gap/hướng/phân loại/ưu tiên/phụ thuộc/đầu ra/tiêu chí. Thực nghiệm có16 trường, mức Required/Recommended/Optional và go/no-go. A3 hoãn nhất quán.
5. **P00.05:** kiểm đủ IDs/prompt sections/links và bảo toàn mọi tệp ngoài scope; ghi audit receipt mới. Không lấy việc tạo kế hoạch làm khắc phục nhận xét.

## E. Nguyên tắc, phụ thuộc và rủi ro

Không train/inference/benchmark tốn tài nguyên, không đổi số, xóa/di chuyển dữ liệu, sửa report/app, commit/push hoặc gửi nội dung cho bên ngoài. Không coi README cũ là authority, không bịa raw absent hoặc công bố. Tra cứu công bố chỉ metadata công khai ở cấp bài, lưu ngày/nguồn và giữ xác nhận cũ nếu mâu thuẫn. Tách observations/inferences/proposals. Nếu nguồn bị thiếu, ghi phạm vi tìm và tiếp tục phần độc lập.

## F. Deliverables

Bảy file README+00–05, prompts00–08 cập nhật trong `docs/revision-plan/`; snapshot mới/evidence verification; `outputs/phase-00/handoff.md` ghi drift và quyết định. Những output khác chưa tồn tại phải được ghi “dự kiến”, không link như đã hoàn thành.

## G. Acceptance criteria và chuyển phase

Đủ 20 ID, mỗi phase đủ mục tiêu/inputs/tasks/outputs/dependencies/acceptance/check/risk/gate; prompts độc lập; mọi số có nguồn; không còn claim Missing chỉ từ một thư mục. Kiểm git diff/hash chứng minh không sửa ngoài plan. Phase kết thúc ở kế hoạch; **không tự chạy Phase01**.

## H. Final report

Báo bằng tiếng Việt: (1) việc hoàn thành; (2) file tạo/sửa; (3) kiểm tra đã chạy, exit/scope và chưa chạy; (4) nhận xét đã audit, không gọi là đã khắc phục; (5) gap chưa giải quyết; (6) quyết định khoa học/kỹ thuật; (7) handoff cho phase01. Nêu A3 hoãn theo người dùng.
