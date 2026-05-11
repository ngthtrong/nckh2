# KẾ HOẠCH THỰC HIỆN REVIEW 2

**Mục tiêu:** Hoàn thiện bộ tài liệu + minh chứng kỹ thuật đủ thuyết phục cho buổi Review 2  
**Thời gian:** 9/5 → 12/5/2026  
**Tham chiếu:** [Đặc tả v2](./Review_2_Spec.md) · [Brainstorm](./Brainstorm_for_review_2.md)

---

## 1. Đầu ra bắt buộc cho Review 2

| # | Nhóm đầu ra | Nội dung cần có | Trạng thái |
|---|------------|----------------|-----------|
| 1 | Đặc tả hệ thống | Tài liệu đặc tả v2, use case, phạm vi, NFR | ✅ Hoàn tất |
| 2 | Thiết kế kiến trúc | Architecture diagram, Use-case diagram, ERD | 🔄 Đang làm |
| 3 | Dataset | Bộ dữ liệu chuẩn hóa + báo cáo thống kê + label schema | 🔄 Đang làm |
| 4 | Model AI | Demo inference ảnh + văn bản, có chỉ số cơ bản | 🔄 Đang làm |
| 5 | Tích hợp hệ thống | Luồng mobile → backend → dashboard (mức demo) | ⬜ Chưa bắt đầu |
| 6 | Trình bày | Slide, kịch bản demo, câu hỏi phản biện | ⬜ Chưa bắt đầu |

---

## 2. Kế hoạch theo giai đoạn

### Giai đoạn A — Chốt tài liệu đặc tả và thiết kế

**Thời gian:** 9/5 – 10/5

- [x] Hoàn thiện đặc tả chức năng / phi chức năng v2
- [x] Chốt phạm vi In scope / Out of scope theo thuyết minh
- [ ] Hoàn thiện sơ đồ Use-case tổng thể
- [ ] Hoàn thiện Architecture Diagram (đã có bản draft)
- [ ] Thiết kế ERD / Class diagram sơ bộ
- [ ] Functional Decomposition Diagram
- [ ] Activity diagram luồng xử lý mạng Mạnh/Yếu

**Đầu ra:** Bộ tài liệu thiết kế dùng trực tiếp trong slide review.

---

### Giai đoạn B — Củng cố Dataset và Model

**Thời gian:** 9/5 – 11/5

- [ ] Rà soát pipeline dữ liệu ảnh (FloodNet + CrisisMMD + VN crawl)
- [ ] Rà soát pipeline dữ liệu văn bản (UIT-VSMEC + crawl mạng xã hội)
- [ ] Chuẩn hóa báo cáo thống kê dataset (phân phối nhãn, số lượng mẫu)
- [ ] Làm rõ định nghĩa từng label: `none`, `low`, `high` cho ảnh
- [ ] Làm rõ định nghĩa từng label: `urgent_rescue`, `need_supplies`, `safe_update`, `irrelevant`
- [ ] Chạy demo inference ảnh (MobileNetV3) và lưu kết quả
- [ ] Chạy demo inference văn bản (DistilBERT/PhoBERT) và lưu kết quả
- [ ] Ghi nhận chỉ số: Accuracy, F1-score, latency, model size

**Đầu ra:** Bảng số liệu + ảnh chụp kết quả demo inference.

---

### Giai đoạn C — Tích hợp Demo hệ thống

**Thời gian:** 10/5 – 11/5

- [ ] Thiết kế database schema (PostgreSQL + PostGIS)
- [ ] Kiểm tra API nhận dữ liệu từ mobile (REST endpoint)
- [ ] Xác nhận luồng mạng mạnh/yếu và hàng đợi đồng bộ
- [ ] Kiểm tra module phân cụm DBSCAN trên server
- [ ] Kiểm tra dashboard nhận cập nhật realtime (WebSocket)
- [ ] Demo end-to-end: gửi báo cáo → backend nhận → dashboard cập nhật

**Đầu ra:** Demo end-to-end ở mức nguyên mẫu hoạt động.

---

### Giai đoạn D — Chuẩn bị báo cáo Review 2

**Thời gian:** 11/5 – 12/5

- [ ] Tạo slide theo mạch: Bài toán → Giải pháp → Demo → Kế hoạch tiếp
- [ ] Chuẩn bị kịch bản demo ngắn, ổn định
- [ ] Tổng hợp câu hỏi phản biện dự kiến + câu trả lời
- [ ] Chạy thử nội bộ toàn bộ bài trình bày
- [ ] Chuẩn bị phương án dự phòng khi demo gặp lỗi

**Đầu ra:** Bộ trình bày hoàn chỉnh cho buổi review.

---

## 3. Phân công theo vai trò

| Thành viên | Viết tắt | Trọng tâm phụ trách |
|-----------|---------|---------------------|
| Lê Thị Ngọc Ảnh | LTNA | Tổng hợp báo cáo, dataset, backend/dashboard, slide |
| Nguyễn Như Quỳnh | NNQ | Huấn luyện/đánh giá mô hình, thực nghiệm số liệu |
| Nguyễn Thanh Trọng | NTT | Kiến trúc hệ thống, CSDL, tích hợp mobile-backend |
| Ngô Hưng Thịnh | NHT | Dữ liệu, tối ưu mô hình, phân cụm |
| Cao Tường Hưng | CTH | Mobile app, tối ưu mô hình, hỗ trợ tích hợp |

### Phân công chi tiết theo giai đoạn

| Giai đoạn | Công việc | Người thực hiện |
|-----------|----------|----------------|
| A | Use-case diagram, Architecture diagram | NTT, CTH |
| A | ERD, Functional Decomposition | NTT, CTH |
| A | Activity diagram luồng mạng | NTT |
| B | Dataset ảnh: rà soát, thống kê | LTNA, NHT |
| B | Dataset văn bản: rà soát, thống kê | LTNA, NHT |
| B | Demo inference ảnh | NNQ, NHT, CTH |
| B | Demo inference văn bản | NNQ, LTNA |
| C | Database schema + API | NTT, LTNA |
| C | Phân cụm DBSCAN | NTT, NHT |
| C | Dashboard WebSocket | LTNA, NNQ |
| D | Slide + kịch bản demo | Cả nhóm |

---

## 4. Checklist kiểm soát tiến độ

- [ ] Đặc tả v2 và sơ đồ thiết kế đã khóa phiên bản
- [ ] Use-case diagram hoàn chỉnh
- [ ] Architecture diagram hoàn chỉnh
- [ ] ERD / Class diagram sơ bộ
- [ ] Dataset report và label schema đã cập nhật
- [ ] Demo inference ảnh + văn bản chạy ổn định
- [ ] Luồng gửi metadata/full payload được minh họa rõ
- [ ] Dashboard hiển thị cụm và mức ưu tiên
- [ ] Slide review và kịch bản demo đã chạy thử nội bộ
- [ ] Có phương án dự phòng khi demo gặp lỗi mạng/mô hình
- [ ] Docs files information of project for LLM

---

## 5. Rủi ro và phương án giảm thiểu

| Rủi ro | Tác động | Giảm thiểu |
|--------|---------|-----------|
| Dữ liệu chưa cân bằng nhãn | Chất lượng demo mô hình kém | Bổ sung mẫu thiếu, tái kiểm tra phân phối |
| Độ trễ suy luận cao trên thiết bị | Demo thiếu thuyết phục về Edge AI | Dùng model nhẹ hơn / quantization, chuẩn bị mẫu demo cố định |
| Luồng đồng bộ mạng yếu chưa ổn | Mất tính thuyết phục | Chuẩn bị kịch bản mô phỏng + fallback gửi metadata |
| Dashboard cập nhật chậm | Ảnh hưởng trải nghiệm realtime | Kiểm tra WebSocket, tối ưu tần suất push |
| Demo bị lỗi khi trình bày | Mất điểm trình bày | Video backup demo + kịch bản dự phòng |

---

## 6. Câu hỏi phản biện dự kiến

| # | Câu hỏi | Hướng trả lời |
|---|--------|--------------|
| 1 | Tại sao dùng 2 model riêng (ảnh + text) thay vì 1 multimodal? | Tối ưu cho edge: model nhẹ hơn, dễ quantize, chạy song song |
| 2 | Nếu người dùng gửi nhiều lần thì xử lý thế nào? | Dedup bằng GPS + time window trong DBSCAN clustering |
| 3 | Cơ chế bảo mật? | JWT authentication + HTTPS + secure_storage trên mobile |
| 4 | Tham số ngữ cảnh (c) được tính thế nào? | Thời gian trong ngày + mật độ báo cáo lân cận (500m/2h) |
| 5 | Tại sao chọn DBSCAN mà không phải K-Means? | Không cần biết trước K, phát hiện noise, bắt cụm hình dạng bất kỳ |
| 6 | Dữ liệu FloodNet/CrisisMMD có phù hợp VN không? | Fine-tune với dữ liệu VN crawl; FloodNet/CrisisMMD chỉ là pretrain base |
| 7 | Mạng chập chờn xử lý thế nào? | Luôn gửi AI results trước (metadata); ảnh gửi khi mạng mạnh trở lại |

---

## 7. Định nghĩa hoàn thành

Review 2 được xem là hoàn thành khi đạt cả 3 điều kiện:

1. **Đủ tài liệu:** Đặc tả, thiết kế (use-case, architecture, ERD), phạm vi và kế hoạch rõ ràng.
2. **Đủ minh chứng kỹ thuật:** Dataset report + demo inference + luồng tích hợp cơ bản.
3. **Đủ năng lực trình bày:** Slide, kịch bản demo, và trả lời được câu hỏi phản biện trọng tâm.
