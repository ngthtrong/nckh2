# Đăng ký và phạm vi thực có — P01

Đầu vào: DOCX mục 12–16, paragraph XML đánh số từ 0 trong `../run-baseline/proposal-paragraphs.txt`; hash DOCX và source trong `../run-baseline/input-hashes.json`. HEAD và trạng thái ban đầu trong cùng thư mục. P00 handoff đã tồn tại và đã đọc. Refresh kiểm tra `../../evidence/audit-execution-20261107.json`: 20 refs, 12 notebooks, 585 hashes RQ khớp, 32 phone raw khớp, 1.702 ảnh khớp. Không cần chạy lại toàn P00; giữ bản audit cũ nguyên byte.

| Cam kết registered | Actual | Evidence trực tiếp | Gap và trạng thái |
|---|---|---|---|
| §12.2/13/14: ảnh + văn bản cứu hộ tiếng Việt | MobileNetV3; mô tả được tiếp nhận; keyword heuristic và LR structured | training_img.ipynb; urgency_ei; cluster_service.py | PARTIAL. Chưa có bằng chứng trained free-text NLP/DistilBERT; LR không hoàn thành thay NLP |
| §13: dữ liệu UIT-VSMEC, mạng xã hội và bộ quốc tế tinh chỉnh | Dataset_Flood và bảng 32 trạng thái OR; RQ simulated | split CSV; urgency_training_SOURCE_FINAL.csv; RQ manifests | Chưa chứng minh pipeline training trên các bộ văn bản đăng ký. Không đồng nhất sentiment với urgency |
| §14: MobileNetV3 + DistilBERT và tối ưu | Ảnh có checkpoint/export/predictions PTQ/QAT/pruning; LR JSON | products/fe/reports/seed1024; urgency_ei/model | Nén ảnh Executed/Evaluated; DistilBERT chưa tìm thấy trong phạm vi repo/20 refs, không kết luận nhóm chưa nghiên cứu ngoài repo |
| §14–16: bộ model đa phương thức | Thu nhận nhiều loại dữ liệu, công thức ghép trường, mô hình ảnh + LR riêng | app payload; rescue_core/clustering.py, priority.py | PARTIAL/UNFULFILLED: chưa có learned fusion hoặc paired gold; LR chưa consumed trong adapter |
| §12/14: hoạt động mạng yếu, mobile | 32 image benchmark raw và 2.313 proxy rows; E2E narrative | snapshot mới; experiment_e2e/RESULTS.md; setup.tex | Image benchmark Evaluated trong scope; E2E Reported/Unverified, không giao tin khi mất hoàn toàn kết nối |
| §12: hỗ trợ điều phối, giảm thiệt hại | Clustering/ranking và scheduler mô phỏng | RQ1–3 manifests/CSV | Implemented/Evaluated synthetic. Chưa measured field effectiveness; các kết quả âm phải giữ |

Không thay thuyết minh để xóa cam kết, không thay model/server/weights hoặc trạng thái công bố. A3 DEFERRED_BY_USER. Việc sửa mô tả không xác nhận hoàn thành NLP/fusion.
