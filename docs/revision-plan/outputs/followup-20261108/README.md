# Bổ sung P02/P03/P04/P05/P07 — 08/11/2026

Thực hiện theo yêu cầu tiếp tục các phần còn lại có điều kiện. Người dùng xác nhận **chưa có** hồ sơ ngoài repo về nguồn/license/IAA/chuyên gia, artifact RQ2 chưa làm tròn, raw E2E hoặc DOI/chapter. Chỉ thực hiện phần đủ dữ liệu; không tạo hồ sơ hoặc phép đo thay thế. A3 vẫn DEFERRED_BY_USER.

| Phase | Việc thực hiện | Kết quả / việc còn thiếu |
|---|---|---|
| P02 | Truy vết records/checkpoint/split; tìm nguồn ảnh, license, IAA và chuyên gia | 1.702 records khớp tám trường; checkpoint ghi seed1024 và đường dẫn split lịch sử. Chưa có checksum split lúc train; source_group đều trống; chưa có hồ sơ provenance/license/IAA/expert. PARTIAL. |
| P03 | Replay và phân rã 8 sai lệch; tìm dữ liệu chưa làm tròn | 3 raw p Spearman kéo theo 5 Holm; 15/15 Holm lịch sử khớp raw p lịch sử. Chưa tìm vector trước export, cả 8 trường vẫn OPEN. Không thay số hoặc tolerance. |
| P04 | Dựng runtime riêng, clean gate, chạy clean+8 biến đổi trên model cố định | **CPU_ONLY, C5 PARTIAL**: 2.304 test predictions +3 validation smoke; 0failure; clean top1 agreement100%. Chưa Android/PTE hoặc ảnh camera độc lập. |
| P05 | Mở rộng recovery qua refs local/working tree/Drive | Chưa khôi phục raw E2E. Giữ SKIP_RERUN benchmark ảnh có 32 JSON; NOT_RUN E2E mới vì chưa device/session/config isolation thực chạy. C6 PARTIAL; không đụng DB. |
| P07 | Tích hợp kết quả CPU, split lineage, RQ2 và chương trình ISDS; build/inspect lại | Chương trình chính thức xác minh danh tính bài6444/tám tác giả. Chapter DOI/date/pages/volume/year vẫn chưa xác minh, A1 OPEN. Giữ published theo xác nhận cũ, chưa tự đổi trạng thái. Receipts build/visual ở report-checks/. |

## Kết quả mới đáng chú ý

Model **seed1024 structured-pruning ONNX**, không phải baseline FP32 gốc. Trên cùng256ảnh test, macro-F1 clean **78,26%**; JPEG q20 **74,14%**; blurσ2 **68,31%**; độ sáng×0,4 **68,04%**; cạnh ngắn64 **64,86%**. Không huấn luyện, chọn model khác hoặc tune ngưỡng theo test.

CI dùng bootstrap ghép cặp252nhóm split,5.000draw; macro-F1 tính lại từng draw. Nhóm split không chứng minh nguồn/sự kiện độc lập. CI chưa hiệu chỉnh đa so sánh, không có p-value mới. Nhãn kế thừa sau corruption chưa được chuyên gia thẩm định. Chỉ kết luận trong scope ONNX CPU và biến đổi nhân tạo.

## Đầu ra và tái lập

- [P04 analysis](phase-04/analysis.md), [handoff](phase-04/handoff.md), [metrics.csv](phase-04/metrics.csv), [paired-effects.csv](phase-04/paired-effects.csv), [predictions.csv](phase-04/predictions.csv), [protocol](phase-04/protocol.json), [validation](phase-04/validation.json).
- [P03 followup](../phase-03/followup-20261108/handoff.md) và [8 dispositions](../phase-03/followup-20261108/disposition.csv).
- [P02/P05/P07 evidence recovery](evidence/README.md), [source hashes](evidence/source-hashes.json), [Drive search receipt](evidence/drive-receipt.json). Dùng skill google-drive chỉ đọc hồ sơ đã có quyền; không gửi tin nhắn.
- `phase-04/run_cpu.py` có ba stage clean/degraded/summarize và gate bắt buộc; requirements/runtime/environment/hash/log đi kèm. PNG nặng ở phase-04/derived/ được ignore riêng, giữ nguyên bản gốc.
- Export bảng/values CPU bằng `python3 report/scripts/export_image_quality.py`, cũng được gọi từ exporter báo cáo thường. Chỉ đọc raw và kiểm hash/metric; không inference trong build.
- Build/check bằng `python3 docs/revision-plan/outputs/followup-20261108/build_report.py`; mỗi command có log/exit/timestamp trong report-checks/commands.json. Chỉ dùng receipt cuối khớp hash PDF hiện tại.

## Phạm vi bảo toàn

Không sửa app/backend/model/weights/test/CSV RQ/manifest lịch sử; không commit/push/publish hoặc gửi phản hồi ra ngoài. `protected-input-hashes.json` chốt3.818tệp trước inference; kiểm bảo toàn cuối được lưu riêng. Nguồn report trước sửa nằm trong before/, và report-before-hashes.json giữ baseline để phân biệt sửa mới với working tree đã bẩn sẵn.

Freeze/ledger P08 trước đây chỉ còn giá trị cho snapshot trước. Đợt này tạo receipts followup mới, không sửa hồi tố output P01–P08 thành kết quả mới, không tự chạy lại toàn bộ P08. PDF build/check đạt không đồng nghĩa nghiệm thu, release readiness hoặc hiệu quả cứu hộ thực địa.
