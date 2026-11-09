# P09–P14: nghiên cứu và benchmark đa phương thức bổ trợ

## Material Passport

- Origin: academic-research-suite / experiment-agent, plan/run/validate.
- Date: 2026-11-08, Asia/Taipei.
- Authorization: [yêu cầu và lựa chọn của người dùng](authorization.json): benchmark công khai và chuẩn bị bộ gán nhãn, vì chưa có người gán/chuyên gia.
- Status: **PUBLIC PILOT EXECUTED; VIETNAMESE RESCUE TASK NOT EVALUATED.** Trạng thái PDF/kiểm cuối nằm trong handoff và report-checks, không dùng freeze P08 cũ.

**Đã có thực nghiệm mới:** 2.971 train/589 validation/701 test CrisisMMD, tách theo sự kiện; 3 classifier text/ảnh/fusion được huấn luyện, 7 cấu hình được đánh giá. Macro-F1 text **76,60%**, ảnh **76,19%**, fusion **78,35%**. Cả ba CI chênh lệch chứa 0, chưa xác lập fusion vượt trội. Khi che ảnh, recall informative của fusion chỉ **6,04%**; giữ nguyên kết quả bất lợi.

[Bàn giao cuối và mức hoàn thành từng phase](handoff.md), [phạm vi kiểm PDF](layout-review.md). Hai bản báo cáo cuối 176 trang; bản tin Việt/Anh 1/1 trang, tóm tắt 2/3 trang. P13 chỉ hoàn thành CLI local, chưa tích hợp vào app/backend. Manifest và kết quả kiểm cuối được chốt riêng cho phiên này.

## Đọc và tái kiểm

1. [Nghiên cứu nguồn và lựa chọn nhiệm vụ](research.md), [protocol khóa](protocol.json), [giải thích phạm vi khóa](protocol-clarifications.md).
2. [Phân tích kết quả/giới hạn/11 sai lệch](analysis.md), [metrics](metrics.csv), [CI hiệu](paired-effects.csv), [dự đoán full precision](test-predictions.csv).
3. [Audit dữ liệu](data-audit.json), [nguồn ghim revision](sources.json), [split manifest](split-manifest.csv), [48 mẫu bị loại](image-audit-exclusions.csv).
4. [Chọn model bằng dev](model-selection.csv), [training receipt](training.json), [24 kiểm artifact/metric/reload](verification.json), [replay CI](effects-verification.json).
5. [Pipeline/CLI](../../../../thucnghiem/multimodal/README.md), [kiểm inference](inference-smoke.json), [commands](commands/).
6. [Bộ gán nhãn tiếng Việt](annotation-kit/README.md), [gate thực tế](vi-intake.json), [trạng thái B1/B3/B4/B5](review-status.csv).

## Mức hoàn thành

| Phase | Kết quả thực hiện | Phần còn thiếu |
|---|---|---|
| P09 | Chốt common target informative và protocol pilot | Target ưu tiên cứu hộ cần chuyên gia |
| P10 | Intake 12.708 source rows; tải 4.309 ảnh; audit còn 4.261 pairs; kit tiếng Việt | 0 dữ liệu/nhãn Việt Nam; chưa IAA/expert |
| P11 | TF-IDF+LR từ câu và frozen image+LR; artifacts có hash | Chưa đánh giá tiếng Việt/DistilBERT |
| P12 | Cùng 701 test IDs, ảnh/text/both, 3 paired CIs, missing-modality diagnostics | Chưa cứu hộ Việt Nam; chưa multi-event replication |
| P13 | CLI local, chặn dùng artifact như đã đánh giá tiếng Việt; tách informativeness khỏi urgency | Chưa tích hợp app/backend hoặc đo Android/E2E |
| P14 | Tích hợp bảng/scope/tóm tắt/kết luận; receipt kiểm báo cáo riêng | Không chấp thuận nghiệm thu, không đóng toàn bộ B1–B5 |

Raw ảnh/text, embeddings, weights, fitted models và `.venv` nằm trong `thucnghiem/multimodal/`, đều ignore và giữ local. Không commit/push/publish, không gửi dữ liệu hoặc liên hệ người khác. Các bộ model/dữ liệu/kết quả lịch sử được giữ, kiểm bảo toàn ở handoff cuối.
