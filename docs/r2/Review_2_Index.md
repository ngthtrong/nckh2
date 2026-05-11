# REVIEW 2 — MỤC LỤC TÀI LIỆU

**Dự án:** Hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI  
**Ngày:** 2026-05-11  
**Buổi review:** Review 2 (9/5 – 12/5/2026)

---

## Tài liệu Review 2

| # | Tài liệu | File | Mô tả |
|---|---------|------|-------|
| 1 | **Đặc tả hệ thống v2** | [Review_2_Spec.md](./Review_2_Spec.md) | Phạm vi, use case, yêu cầu chức năng/phi chức năng, đặc tả dữ liệu, luồng nghiệp vụ, tiêu chí nghiệm thu |
| 2 | **Kế hoạch thực hiện** | [Review_2_Plan.md](./Review_2_Plan.md) | 4 giai đoạn (A–D), phân công, checklist, rủi ro, câu hỏi phản biện |
| 3 | **Chi tiết Module** | [Review_2_Modules.md](./Review_2_Modules.md) | 14 module hệ thống, API endpoints, công nghệ, người phụ trách |
| 4 | **Dataset & Model** | [Review_2_Dataset_Model.md](./Review_2_Dataset_Model.md) | Label schema, tiền xử lý, mô hình AI, benchmark, lý giải lựa chọn |
| 5 | **Đặc tả Use Case** | [Review_2_UseCase.md](./Review_2_UseCase.md) | 14 use case chi tiết, mối quan hệ include/extend, ma trận truy vết FR |

## Tài liệu nền

| # | Tài liệu | File | Mô tả |
|---|---------|------|-------|
| 5 | Thuyết minh NCKH | [Thuyết minh NCKH.md](./Thuyết%20minh%20NCKH.md) | Đề cương nghiên cứu gốc |
| 6 | Review 1 | [Review_1.md](./Review_1.md) | Báo cáo tiến độ lần 1 |
| 7 | Brainstorm | [Brainstorm_for_review_2.md](./Brainstorm_for_review_2.md) | Ghi chú brainstorm cho review 2 |
| 8 | Kiến trúc hệ thống | [architecture_design.md](../architecture_design.md) | Sơ đồ kiến trúc chi tiết (Mermaid + PlantUML) |
| 9 | Progress Report | [progress_report_data_models.md](../progress_report_data_models.md) | Báo cáo tiến độ dataset & demo inference |

## Sơ đồ thiết kế

| # | Sơ đồ | File | Định dạng |
|---|------|------|----------|
| 1 | Kiến trúc tổng quan | [diagrams/](../diagrams/) | Mermaid + PlantUML + PNG |
| 2 | Kiến trúc mobile | [diagrams/](../diagrams/) | Mermaid + PlantUML + PNG |
| 3 | Tech stack | [diagrams/](../diagrams/) | Mermaid + PlantUML + PNG |
| 4 | Sequence diagram | [diagrams/](../diagrams/) | Mermaid + PlantUML + PNG |

---

## Checklist Todo cho Review 2

> Từ [Brainstorm](./Brainstorm_for_review_2.md)

- [x] ~~Bộ dataset~~ → Xem [Review_2_Dataset_Model.md](./Review_2_Dataset_Model.md)
- [x] ~~Model sẽ chạy~~ → Xem [Review_2_Dataset_Model.md](./Review_2_Dataset_Model.md)
- [ ] Thử các môi trường, công nghệ sẽ sử dụng
- [ ] Bản thiết kế database (ERD)
- [x] ~~Báo cáo đặc tả hệ thống v1~~ → Xem [Review_2_Spec.md](./Review_2_Spec.md)
  - [ ] Use-case Diagram → cần render
  - [x] ~~Architecture Diagram~~ → Có trong [architecture_design.md](../architecture_design.md)
  - [ ] ERD / Class diagram → cần tạo
- [x] ~~Docs files information of project for LLM~~ → File index này

### Later (sau Review 2):
- [ ] Sequence Diagram chi tiết hơn
- [ ] Component Diagram
