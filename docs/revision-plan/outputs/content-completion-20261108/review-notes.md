# Rà soát nội dung và phạm vi

- Đã đối chiếu các mục mới với kế hoạch 02–15, thuyết minh DOCX, adapter và kết quả có sẵn.
- Ba nhánh được giữ riêng: ứng dụng hiện tại; pilot informative CrisisMMD đã chạy; thiết kế cứu hộ tiếng Việt chưa thực hiện.
- Nhãn tiếng Việt đề xuất là yêu cầu hỗ trợ, chưa phải urgency/ưu tiên chuyên môn. Ảnh-only có thể thiếu thông tin để suy ra yêu cầu; phân tích không loại mẫu khó sau khi nhìn dự đoán.
- DistilBERT đa ngôn ngữ có khoảng 134M tham số theo model card đã đọc; không khẳng định phù hợp điện thoại trước khi đo. Các hyperparameter và phép trích xuất là cấu hình đề xuất.
- Kiểm tích hợp cục bộ cùng họ mô hình đã phát hiện và bổ sung chính xác default urgency 0,4/None và quy tắc khóa có mặt nhưng lỗi; không phải xác nhận khoa học độc lập.
- Thu gọn văn bản lặp trong biểu mẫu Việt và kết luận; không chỉnh font/lề, ảnh chủ nhiệm, mẫu chữ ký hoặc tỷ lệ chèn thuyết minh.
- Script acronym đã chạy dạng advisory. Nó chỉ hỗ trợ en/zh-TW, nhận sai chữ hoa tiếng Việt và không xác nhận nhiều định nghĩa trong PDF tiếng Việt; không gọi đó là kiểm thuật ngữ đầy đủ.
- ARS PDF structural preflight bằng Python hệ thống trả UNAVAILABLE vì thiếu pypdf. Kiểm PDF thực tế dùng pdfinfo, pdftotext, pdffonts, nguồn/aux/danh mục và render Poppler; không nâng trạng thái preflight thành PASS.
- Không chạy train, inference, benchmark, bootstrap hoặc replay thống kê mới. Các exporter trong make chỉ đọc artifact và sinh bảng/provenance.
