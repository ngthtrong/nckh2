# Bàn giao audit và lập kế hoạch — Phase 00

Ngày 07/11/2026, Asia/Taipei. Repository `/home/ngthtrong/nckh2`, nhánh main, HEAD lúc audit `379021d`; hash đầy đủ và dirty state trong `../../evidence/audit-snapshot.json`.

## Đã hoàn thành

- Tạo bảy tài liệu kế hoạch chính (README, 00–05), chín prompt độc lập 00–08, source evidence, collector và validator.
- Đối chiếu yêu cầu người dùng, tổng hợp nhận xét 06–20 trong `tmp.md`, thuyết minh DOCX mục 12–16, source report/app/server/dashboard/model/experiments, 20 ref Git và 12 notebook.
- Phân biệt Implemented/Executed/Evaluated/Reported/Missing/Unverified; lập ma trận 20 ID, sáu đề xuất kiểm chứng/thực nghiệm với 16 trường, backlog sửa ngay, roadmap/gates và traceability.
- Ghi nhận điều chỉnh của người dùng: **A3 ảnh cá nhân thêm sau**, DEFERRED_BY_USER, không tìm/chèn/hỏi ảnh và không chặn roadmap.

## Kiểm tra đã chạy

| Kiểm tra | Bằng chứng/kết quả | Giới hạn |
|---|---|---|
| `report/build/visual-env/bin/python docs/revision-plan/evidence/collect_snapshot.py` | Exit 0; JSON snapshot. 1.702 ảnh tồn tại/MD5/group khớp; header thống kê đủ; 32 mobile JSON đủ256 prediction/nhãn/Accuracy/F1 khớp | Đọc header/CSV/JSON, không chạy model |
| Hash RQ và source report trong collector | 585/585 mục trong bốn manifest khớp, 26/26 source hashes khớp | Không replay bootstrap/Wilcoxon, không xác nhận nguồn ảnh/clinical/field |
| `python3 report/scripts/check_float_references.py` và bản `--build-dir build/content-twoside` | Exit 0 từng bản; 48 hình/37 bảng | Không build mới hoặc visual toàn quyển; audit layout cũ được đọc riêng |
| `python3 docs/revision-plan/evidence/validate_plan.py` | Exit 0; đủ20 ID ở hai ma trận,9 prompt A–H, local links hợp lệ,228 tệp sẵn có nguyên byte/trạng thái ngoài plan không đổi | Document/integrity check, không science/release certificate |
| Đọc PDF text/pdfinfo | Main PDF165 trang, placeholder ảnh trang20; sources/PDF đã có | Không sửa PDF |

Không huấn luyện, inference, benchmark mới, build/export report, cài dependency, checkout/fetch/reset, commit/push hoặc gửi tin nhắn. Chỉ ghi trong `docs/revision-plan/`. Các thay đổi và xóa tệp có sẵn được giữ nguyên.

## Quyết định quan trọng

1. Sửa claim E_i/NLP/fusion và phạm vi thuyết minh trước; không tự thay adapter để làm mô tả đúng.
2. PTQ/QAT/pruning, mobile32 và kết quả RQ đã có: giải thích/tái phân tích, không train lại theo mặc định.
3. RQ1 chưa superiority Product; RQ2 chưa benefit alignment chung; RQ3 adverse nearest-first outcomes phải giữ. Primary/replication và hai generator riêng.
4. C5 thiếu controlled image-quality evaluation; inference mới có gate model/split/runtime/device, CPU-only không đóng mobile claim.
5. Android/web E2E được ghi nhận trong báo cáo/tài liệu nhưng raw/log còn thiếu tại checkout; khôi phục trước rerun.
6. B5 image/text/both hiện NO_GO vì target/gold/paired data chưa đủ. Không thay bằng phép so sánh hai accuracy khác nhiệm vụ.
7. A1 giữ provenance xác nhận published trước đây; tra cứu cấp quyển chưa xác minh riêng bài. Không tự điền volume/year hoặc thay trạng thái. A3 chủ động hoãn theo người dùng.

## Gap và giới hạn còn lại

- Full verifier RQ hardcode `src/results` và pin NumPy/matplotlib khác env có sẵn; chưa replay thống kê. P03 dùng harness/path map và môi trường phù hợp, không sửa manifest.
- Thiếu raw E2E/APK hash/phiên timing lặp/thermal; metadata/source/license/IAA ảnh và expert labels chưa đủ; không sáng tác lại.
- Chưa rà toàn văn từng PDF nguồn WHO hay đầy đủ quy định cứu hộ Việt Nam; P02 cần source map có phạm vi và uncertainty.
- Chưa xác minh chapter DOI/ngày online của bài ISDS; trang cấp quyển/print/eBook/copyright không thay thế nhau.

## Bước tiếp theo

Dùng **toàn bộ `docs/revision-plan/prompts/phase-01.md`** ở phiên riêng để thực hiện các sửa đổi khoa học có bằng chứng và thêm D1–D3. P00 kết thúc tại kế hoạch; **P01–08 chưa thực hiện**. Mỗi phiên phải đọc status/source/hash mới, bảo toàn dirty work hiện có và dùng handoff thật. Báo thiếu output phase trước thay vì coi nó đã tồn tại.
