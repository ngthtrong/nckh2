# D1–D3: đề xuất, chưa triển khai hoặc đo

D1: hợp nhất GPS, Wi-Fi, mạng di động, IP và mốc/địa chỉ được xác nhận; lưu nguồn, thời điểm, uncertainty; đánh giá coverage, sai số và quyền riêng tư. IP không mặc định tốt hơn GPS. Wi-Fi cần reference/infrastructure. Thiếu/mâu thuẫn vị trí chuyển hàng xem xét, không tọa độ giả.

D2: audio → ASR tiếng Việt → trích xuất thông tin → người gửi/điều phối viên xác nhận. Cần paired audio/transcript/slot labels có consent; đánh giá tiếng ồn mưa/gió, nhiều giọng địa phương, lỗi thiếu/sai số người và địa chỉ, latency/điện năng. Chưa có ASR results.

D3: local store không phải delivery. SMS cần sóng di động/gateway; DTN cần relay/contact và eventual path đến trung tâm. Người không có máy cần báo hộ, hotline khi còn kênh hoặc đội tại chỗ tiếp nhận, kèm xác minh/chống trùng/phản hồi. Không hứa gửi được khi mọi đường truyền không tồn tại. Chưa đo delivery ratio hoặc diễn tập các hướng này.

Đã tích hợp trong `report/chapters/conclusion.tex:Hướng nghiên cứu tiếp theo`. NLP/fusion vẫn là gap nghiên cứu riêng, không được xem các đề xuất này là đã hoàn thành cam kết đăng ký. A3 hoãn.
