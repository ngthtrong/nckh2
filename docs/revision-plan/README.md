# Kế hoạch chỉnh sửa THS2026-68 sau nghiệm thu

**Thực nghiệm tiếng Việt dịch/nhãn AI — 08/11/2026:** đã thực thi [pilot NLP/fusion](outputs/vi-nlp-fusion-silver-20261108/README.md) theo chỉ đạo cho phép AI tự gán nhãn. Có 179/58/59 cặp train/validation/test, 18 fit head, 6 phiên fine-tuning; fusion frozen macro-F1 64,91%, recall request 33,33% (2/6), fine-tuning văn bản trung bình 50,73%. Kiểm kỹ thuật độc lập đạt 10/10; các CI so sánh fusion chứa/chạm 0. [Bàn giao](outputs/vi-nlp-fusion-silver-20261108/handoff.md) ghi PDF và kiểm cuối. Đây là dữ liệu dịch/nhãn AI từ câu nguồn, không phải gold người độc lập hoặc xác nhận cứu hộ tiếng Việt gốc. Các đoạn dưới là snapshot của những đợt trước.

**Kế hoạch thực nghiệm tiếng Việt — 08/11/2026:** [NLP và fusion cho báo cáo cứu hộ tiếng Việt](vietnamese-nlp-fusion-experiment-plan.md). Đề xuất VN-00–VN-07: chốt task → nguồn/gán nhãn → corpus/split → pipeline riêng → NLP/ảnh → fusion → đánh giá → bàn giao. Bộ cũ vẫn có 0 bản ghi/0 nhãn và khác task nhị phân trong thiết kế ND. Kế hoạch gốc nêu cấu hình, cổng dữ liệu, tài nguyên và tiêu chí kết luận cho corpus tiếng Việt gốc/gold độc lập; pilot silver riêng và thay đổi phạm vi thực thi được liên kết ở đầu kế hoạch.

**Đã thực hiện ND-01–ND-06 — 08/11/2026:** [Hoàn thiện nội dung báo cáo cho nhận xét 02–15](report-content-completion-02-15.md). Đã bổ sung thiết kế NLP/fusion tiếng Việt, quy trình dữ liệu, LR/nén, ablation, bàn luận RQ và kế hoạch camera/Android; đồng bộ Việt–Anh và xử lý trang ký/kết luận ngắn. Hai PDF cuối đều 194 trang, 50 hình và 48 bảng; build/check và kiểm trực quan đạt trong phạm vi biên soạn. Xem [bàn giao và ma trận nội dung/thực hiện](outputs/content-completion-20261108/handoff.md). Không chạy thêm thí nghiệm; phần chưa làm vẫn là thiết kế, tám trường RQ2 còn OPEN. Các snapshot P00–P14 dưới đây tiếp tục giữ như lịch sử; ảnh chủ nhiệm hiện đã có trong PDF.

**Đợt bổ sung P09–P14 ngày 08/11/2026:** theo yêu cầu mới, đã nghiên cứu và triển khai [benchmark đa phương thức công khai và bộ chuẩn bị gán nhãn tiếng Việt](multimodal-extension.md). [Kết quả pilot](outputs/multimodal-20261108/README.md): 2.971 train/589 validation/701 test, macro-F1 text 76,60%, ảnh 76,19%, fusion 78,35%; các CI chênh lệch đều chứa 0. Đã có ablation trên common target informative của CrisisMMD; B1/B3/B4/B5 vẫn PARTIAL đối với cứu hộ tiếng Việt và tích hợp ứng dụng. Các snapshot P00–P08 dưới đây là hồ sơ lịch sử, không thay receipt của đợt mới.

Ngày khảo sát: **07/11/2026, Asia/Taipei**. Đề tài: **Xây dựng hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI**. Đây là kế hoạch đề xuất theo 20 nhận xét A1–D3 do người dùng tổng hợp, không phải biên bản Hội đồng có chữ ký hay xác nhận đã khắc phục.

**P00 là lần audit và lập kế hoạch trước đó.** Theo [chỉ đạo thực thi mới](evidence/execution-authorization-20261107.md), đã triển khai chuỗi P01–P08 với quyết định có điều kiện ở P04–P06. Snapshot cũ được giữ; snapshot thực thi mới ở [audit execution](evidence/audit-execution-20261107.json), hash/trạng thái ban đầu ở `outputs/run-baseline/`. Không sửa app/server/model hoặc raw kết quả.

**Điều chỉnh của người dùng trong phiên:** ảnh cá nhân (A3) sẽ được thêm sau. Giữ nguyên ô ảnh, ghi `DEFERRED_BY_USER`; không tìm/chèn ảnh và không xem A3 là điều kiện chặn các phase hiện tại.

## Đọc theo thứ tự

1. [Audit và danh mục bằng chứng](00-repository-audit.md): hiện trạng, giới hạn khảo sát, chênh lệch thiết kế–mã nguồn–báo cáo.
2. [Ma trận 20 nhận xét](01-review-matrix.md): đủ 12 trường xử lý cho từng ID.
3. [Khoảng trống và protocol thực nghiệm](02-experiment-gap-analysis.md): Required/Recommended/Optional, điều kiện thực hiện hoặc bỏ qua.
4. [Việc sửa ngay](03-immediate-fixes.md): tách tác vụ tự động khỏi thông tin cần bổ sung.
5. [Roadmap và bàn giao](04-phase-roadmap.md): phạm vi tệp, phụ thuộc và cổng chuyển phase.
6. [Truy vết](05-traceability-matrix.md): nhận xét → thuyết minh → bằng chứng → tác vụ → vị trí báo cáo → tiêu chí.

## Kết luận điều hành

- Đã có nguyên mẫu Flutter–FastAPI–dashboard, MobileNetV3-Large, LR có cấu trúc, phân cụm/xếp hạng, RQ1–RQ3, PTQ/QAT/pruning và benchmark trên bốn mẫu điện thoại. Nhiều nội dung đã được báo cáo khá rõ; không lập kế hoạch từ nhận định cũ rằng chưa có mô hình nén hoặc chưa đo điện thoại.
- **Critical:** sửa phát biểu tích hợp `E_i` không khớp adapter; tách LR khỏi NLP; phản ánh kết quả âm và giới hạn dữ liệu mô phỏng trong tóm tắt/kết luận; xác minh công bố ở cấp bài báo. Không suy ra bài đã xuất bản chỉ từ trang cấp quyển.
- Bằng chứng định lượng sẵn có giải quyết phần lớn B2, C1, C3, C4, C6, C7. C2 cần thống kê header ảnh, đã thu được trong audit mà không chạy model. C5 còn thiếu khảo sát chất lượng ảnh có kiểm soát.
- Chưa tìm thấy mô hình NLP tự do hoặc dữ liệu ảnh–tin nhắn ghép cặp phù hợp sau kiểm tra 20 ref Git hiện có, 12 notebook và tìm nội dung code. Không khẳng định tuyệt đối rằng nhóm chưa từng thực hiện ở máy/tài khoản khác.
- Báo cáo mô tả hai run E2E Android và tài liệu ghi nhận hai run web; raw JSON/CSV/log tương ứng chưa có trong checkout. Tìm/khôi phục hồ sơ trước khi cân nhắc chạy lại. Benchmark ảnh trên điện thoại có đủ 32 JSON gốc và kiểm tra lại được.

## Dùng prompt ở phiên riêng

Mở repository `/home/ngthtrong/nckh2`, đưa **toàn bộ** nội dung một prompt cho Agent. Mỗi prompt tự chứa bối cảnh, nguồn, tác vụ, phạm vi, nguyên tắc và tiêu chí; không cần lịch sử chat. Việc đưa prompt thực thi sau này mới kích hoạt phạm vi sửa/chạy của phase đó. Các prompt độc lập giữ hợp đồng từng phase; trạng thái thực thi hiện tại được ghi trong các handoff và hồ sơ P08, không suy ra thí nghiệm đã chạy chỉ vì có prompt.

| Prompt | Mục đích | Tính chất |
|---|---|---|
| [phase-00.md](prompts/phase-00.md) | Làm mới audit nếu checkout hoặc nguồn thay đổi | Chỉ đọc, viết kế hoạch |
| [phase-01.md](prompts/phase-01.md) | Sửa phạm vi khoa học, luồng E_i, kết luận và Future Work | Sửa nội dung có bằng chứng |
| [phase-02.md](prompts/phase-02.md) | Hồ sơ dataset, LR và tối ưu mô hình; thống kê từ artifact | Tái phân tích nhẹ |
| [phase-03.md](prompts/phase-03.md) | Kiểm chứng/tái phân tích RQ1–RQ3, kết quả âm | Không chạy lại benchmark gốc |
| [phase-04.md](prompts/phase-04.md) | Khảo sát suy giảm chất lượng ảnh trên model cố định | Suy luận bổ sung có điều kiện |
| [phase-05.md](prompts/phase-05.md) | Khôi phục bằng chứng mobile/E2E, chỉ đo lại phần thật sự thiếu | Có nhánh không cần điện thoại |
| [phase-06.md](prompts/phase-06.md) | Đánh giá tính hợp lệ ablation nguồn thông tin | Mặc định feasibility/no-go |
| [phase-07.md](prompts/phase-07.md) | Tích hợp số liệu, xử lý công bố, rà hình thức; A3 hoãn | Sửa và build báo cáo |
| [phase-08.md](prompts/phase-08.md) | Kiểm chứng cuối, hồ sơ phản hồi từng nhận xét | Kiểm tra, không tạo bằng chứng mới |

Trình tự: **01 → 02 → 03 → quyết định 04/05/06 → 07 → 08**. Phase 00 đã thực hiện và snapshot được refresh trước sửa. Phase 04 và 05 độc lập sau 02; 06 được bỏ qua có lý do khi chưa có nhiệm vụ/nhãn chung. Không tự triển khai NLP, fusion hoặc đổi thuật toán để làm đẹp kết quả.

## Bằng chứng và hạn chế

[Bản yêu cầu nguyên byte](evidence/user-request.txt), [snapshot kiểm tra](evidence/audit-snapshot.json), [nguồn ngoài](evidence/external-verification.md) và [script thu snapshot](evidence/collect_snapshot.py) hỗ trợ truy vết. Script từ chối ghi đè snapshot; tái chạy bằng `report/build/visual-env/bin/python docs/revision-plan/evidence/collect_snapshot.py audit-NEW.json`.

[Bàn giao Phase 00](outputs/phase-00/handoff.md) ghi kiểm tra đã chạy, giới hạn và bước tiếp theo. Chạy `python3 docs/revision-plan/evidence/validate_plan.py` để kiểm coverage, links và bảo toàn; kết quả ở [plan-validation.json](evidence/plan-validation.json).

Đã kiểm tra 585 mục hash trong bốn manifest, 26 nguồn của provenance báo cáo, nhãn/metric của 32 JSON mobile, header/MD5 của 1.702 ảnh và float ở hai PDF. **Không** replay toàn bộ Wilcoxon/bootstrap: verifier đang trỏ `src/results` và đòi NumPy 2.5.1, khác môi trường sẵn có. Chi tiết ở audit. Tài liệu kế hoạch không phải chứng nhận nghiệm thu hoặc xác nhận giá trị cứu hộ thực địa.

## Kết quả thực thi chuỗi

**Bổ sung ngày 08/11/2026:** đã tiếp tục P02/P03/P04/P05/P07 theo yêu cầu mới. [Gói followup](outputs/followup-20261108/README.md) có **2.304 dự đoán test ONNX CPU** clean+8 biến đổi sau clean parity; C5 chuyển sang PARTIAL/CPU_ONLY. P02 chưa có hồ sơ provenance/license/IAA/expert và checksum split lúc train; 8 sai lệch RQ2 còn OPEN; raw E2E/chapter DOI chưa khôi phục. Người dùng xác nhận chưa có hồ sơ bổ sung. Các handoff bên dưới và freeze P08 là snapshot trước đợt này, không phải kết quả kiểm cho PDF mới.

- [P01](outputs/phase-01/handoff.md): scope/claim/runtime E_i và D1–D3.
- [P02](outputs/phase-02/handoff.md): dữ liệu/LR/compression/measurement scopes từ artifact.
- [P03](outputs/phase-03/handoff.md): replay RQ; 8 sai lệch p-value/Holm RQ2 còn công khai.
- [P04](outputs/phase-04/handoff.md): NOT_RUN inference; chuẩn bị 9 đầu vào của một ảnh validation, không có metrics robustness.
- [P05](outputs/phase-05/handoff.md): SKIP_RERUN benchmark ảnh; NOT_RUN E2E, raw chưa khôi phục.
- [P06](outputs/phase-06/handoff.md): NO_GO ablation do thiếu common target/paired gold.

Hồ sơ tích hợp và kiểm cuối được ghi ở `outputs/phase-07/` và `outputs/phase-08/`; chỉ các receipt có hash/exit đúng trạng thái cuối mới được dùng. Sửa mô tả/build không hoàn thành cam kết NLP/fusion hoặc chứng minh giá trị cứu hộ thực địa. A3 vẫn DEFERRED_BY_USER; A1/C5 và các thiếu sót khác giữ trong ledger cuối.
