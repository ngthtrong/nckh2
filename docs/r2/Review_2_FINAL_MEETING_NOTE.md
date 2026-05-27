# Đây là file quan trọng nhất 
File này ghi lại toàn bộ nội dung buổi phản biện luận án lần 2 ngày và ghi chép lại các ý kiến của giảng viên, hướng đi tiếp theo và các quyết định đã được đưa ra trong buổi báo cáo tiến độ
# Nội dung


Nghiên cứu sẽ được chia thành 2 phần, 
1. Viết báo khoa học: (tập trung hoàn thiện trước để phục vụ cho buổi báo cáo đề tài ở trường)
    - Tập trung vào công thức của community bên server, trọng số này nhiu, kia nhiu, ra quyết định tại sao như vậy.
    - Nghiên cứu về thuật toán louvain  (sử dụng bộ dữ liệu mô phỏng với thông tin mỗi sự kiện gồm: thời gian, GPS, thông tin người gửi, tag mức độ ngập lục và tag mức độ khẩn cấp từ văn bản)
    - Sau khi áp dụng louvain (hoặc một thuật toán phân cụm khác sau quá trình thực thi sẽ chốt thuật toán sau) thì đề suất một một công thức hoàn chỉnh để tính mức độ khẩn cấp (gồm điểm được tính từ các thông tin từ người gửi và các biến môi trường, ngữ cảnh: ví dụ như thời gian gửi, mật độ của vị trí gửi tại thời điểm đó,...) 

2. Hoàn thiện đề tài (từ bài báo đã viết) và báo cáo dưới hội đồng của trường
    - Tiến hành tiếp tục hoàn thiện độ dataset ảnh ngập lục
    - Lựa chọn và training model nhận diện ảnh ngập lục
    - Tiến hành tìm hiểu model (hoặc phương thức phù hơp) để xử lý gán nhãn cho ngôn ngữ tự nhiên 



### Nháp trong buổi hợp:
Công thức - đồ thị có trọng số - mỗi sk là node (gps, thông tin) - giữa các sự kiện gần bao nhiêu là có liên kết, trong 1 bán kính bao nhiu - dùng community detect ra - mật độ càng cao thì khẩn cấp càng cao 
Vd : dưới 1 km và cái trọng số -> liên kết
dùng đồ thị có trọng số 
Dựa vào mật độ để tính điểm khẩn cấp sau khi phân cụm
Dựa vào những gì đã có sẵn để làm (
louvain algorithm: giải thuật phân cụm (quá nhiều người gửi), tải về xây dựng đồ thị trọng số
Lược khảo tài liệu, công thức tự kiếm, liệt kê những gì mình đề xuất ra, được cái gì -> viết báo
Tính khoảng cách địa lý gán trọng số, tại sao chỗ này cao hơn kia, tin nhắn gửi về giống nhau thì ưu tiên ntn
Tìm hiểu louvain, công thức để xây dựng trọng số, 
App: đơn giản
Viết báo càng sớm càng tốt (tìm bài báo  lũ lụt liên quan, community, đồ thị có trọng số và gán trọng số ntn)
Điện toán biên: mobile net v3, giải quyết bài toán biên để lấy thông tin, (kp nén hình r gửi đi). Sau khi tính điện toán biên rồi -> dữ liệu nhỏ -> có thể gửi hết

Công việc cần thực hiện: tìm hiểu louvain, cài đặt thử, tạo bộ dữ liệu mô phỏng và gán thử các trọng số,... tìm kiếm thêm các bài báo khoa học liên quan, 