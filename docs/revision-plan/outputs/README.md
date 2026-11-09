# Kết quả thực thi chuỗi chỉnh sửa

P01 → P02 → P03 đã thực hiện; P04–P06 đã có quyết định theo điều kiện; P07–P08 đã tích hợp và kiểm cuối. Hoàn thành công việc chỉnh sửa không có nghĩa mọi cam kết nghiên cứu đã đạt.

| Phase | Đầu ra chính | Trạng thái và giới hạn |
|---|---|---|
| [01](phase-01/handoff.md) | Scope register, dataflow, claim ledger, Future Work | Sửa claim; NLP/fusion vẫn chưa chứng minh hoàn thành, E_i chưa consumed |
| [02](phase-02/handoff.md) | Data card, profile, LR/source map, compression/scopes | Phân tích artifact; unknown provenance/expert/clinical còn giữ |
| [03](phase-03/handoff.md) | Protocol, statistics, claims, discrepancies | 3.576/3.584 kiểm tra số khớp; 8 sai lệch RQ2 còn mở |
| [04](phase-04/handoff.md) | Preflight, protocol, validation preparation | NOT_RUN inference, không có performance metrics mới |
| [05](phase-05/handoff.md) | Recovery, provenance, run plan | SKIP_RERUN benchmark ảnh; NOT_RUN E2E, raw chưa khôi phục |
| [06](phase-06/handoff.md) | Eligibility, feasibility, no-go | NO_GO ablation ảnh/văn bản vì thiếu target/paired gold chung |
| [07](phase-07/handoff.md) | Tích hợp Việt–Anh, publication, build/visual | Hai bản nội dung 171 trang; A1 vẫn OPEN cấp bài |
| [08](phase-08/handoff.md) | Final ledger, validation, response draft, hashes | Đủ 20 ID; 8 DONE, 8 PARTIAL, 2 OPEN, 2 deferred có lý do/chỉ đạo |

Báo cáo: `report/main.pdf`, `report/build/content-twoside/content.pdf`; bốn PDF bulletin/summary Việt–Anh. Build/check/diff, float, font, PDF text và visual được ghi trong P07/P08. Đây là bản nháp được kiểm kỹ thuật, chưa phải chứng nhận nghiệm thu hoặc scientific acceptance.

Mở [bàn giao cuối](phase-08/handoff.md), [ledger 20 nhận xét](phase-08/final-review-status.csv), [phản hồi nội bộ](phase-08/response-draft.md) và [khả năng tái lập](phase-08/reproducibility.md). Không gửi phản hồi cho bên ngoài, không commit/push.

Raw/model/kết quả lịch sử và sửa đổi sẵn có được so hash trong preservation.json. Riêng tmp.md do người dùng xác nhận chủ động xóa nội dung, đã giữ tệp hiện tại. Artifact lớn/copy/ảnh render giữ local theo .gitignore, kèm hash; không force-add dữ liệu nặng.
