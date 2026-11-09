# P01 — bàn giao

Đã sửa tám nguồn trong source-changes.json; input/HEAD/dirty baseline ở ../run-baseline, snapshot refresh ../../evidence/audit-execution-20261107.json; output-hashes.json chốt source/PDF của P01 (sau P02/P07 sẽ stale có chủ ý, không tái dùng như receipt final).

B1/B3/B4/C3/C7: đã sửa phạm vi bằng evidence; NLP/fusion vẫn UNFULFILLED/NOT_DEMONSTRATED. D1–D3 đã thêm proposed với giới hạn. A1 giữ nguyên trạng thái; A3 DEFERRED_BY_USER, placeholder không đổi. Không sửa app/backend/contract/model.

Đoạn cần giữ cho P02: methods LR đoạn computed/sent/stored/not consumed, results subsection LR, scope phân biệt ba mức đa phương thức, intro và architecture adapter. Không viết lại thành LR đã tham gia rank. Conclusion và research-body Việt–Anh đã giảm claim; RQ chưa tái tính ở P01.

Commands: python3 outputs/phase-01/revise.py exit 0; make -C report content exit trong build-content.exit; make -C report check exit trong check.exit; pdftotext exit 0, terms adapter/ASR/DTN/IP/Wi-Fi/fusion hiện diện. Log build-content.log/check.log và PDF text lưu tại đây. Chưa visual từng trang ở checkpoint này; kiểm trực quan cả variants và deliverables thực hiện P07/P08 sau nội dung ổn định. Build không phải scientific acceptance.

P02: data card, profile, LR/source-map, compression và measurement scope; sau đó P03 replay RQ. Không train. Tất cả raw/history và sửa đổi ban đầu được giữ.
