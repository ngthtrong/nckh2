1/ Đọc hiểu các TN
2/ Cho chat đánh giá với các thực nghiệm mô hình thì chọn seed nào là tốt nhất: 42, 159, 1024
- Chọn 1 seed cho các thực nghiệm
3/ Kiểm tra 2 kết quả e2e và mạng yếu đã phù hợp chưa
4/ Chạy thêm thực nghiệm trên di động
lấy benchmark của NA + benmark chạy rồi thống kê lại 

3/ Đưa vào báo cáo:
- Các thực nghiệm là ok
- Bảng số liệu thực nghiệm: kèm kết quả -> nhận xét đánh giá 
- Kết quả thực nghiệm e2e và mạng yếu (giả lập trên lap)
- Kết quả thực nghiệm e2e từ di động 










TN02: Kiểm tra độ đáng tin của confidence và việc chỉ gửi metadata
ECE (Expected Calibration Error) lấy độ lệch của các nhóm, tính trung bình có trọng số theo số ảnh. ECE càng thấp càng tốt; 0 là khớp hoàn toàn theo cách chia nhóm đó.
-ECE tính dựa trên confidence

Brier tính tổng bình phương chênh lệch giữa hai hàng, rồi lấy trung bình trên các ảnh.
Đoán đúng và tự tin cao → điểm thấp.
Đoán sai nhưng rất tự tin → bị phạt nhiều.

 ##################

TN03: Chuyển mô hình sang dạng chạy được trong app
Mục đích: để kiểm tra chuyển định dạng và runtime
Chạy 3 model onnx, pth, pte trên cùng FB32 bit
Mặc dù đây là thực nghiệm trên cpu máy nhưng vẫn giữ lại để sau khi chạy trên di động sẽ so sánh

* **Chuyển PTH sang ONNX/PTE có giữ nguyên dự đoán không?**
* **Dung lượng mỗi file là bao nhiêu?**
* **Trên máy tính được đo, riêng bước suy luận của từng runtime mất bao lâu?**

####################

TN04: Đo mô hình khi chạy bên trong ứng dụng
Đo kết quả mô hình chạy trên ứng dụng di động

###################

TN05: Làm mô hình nhỏ hơn bằng cách giảm độ chính xác biểu diễn số (lượng tử hóa)
PTQ: Post-Training Quantization là kỹ thuật chuyển đổi trọng số (weights) và đôi khi là giá trị kích hoạt (activations) của một mô hình học máy/AI từ độ chính xác cao (ví dụ: FP32 - 32-bit floating point) sang độ chính xác thấp hơn (ví dụ: INT8, INT4) **sau khi** mô hình đã được đào tạo xong

QTA: Quantization-Aware Training là kỹ thuật tích hợp quá trình giảm độ chính xác của trọng số mô hình (ví dụ từ FP32 xuống INT8 hoặc 4-bit) ngay trong giai đoạn huấn luyện hoặc tinh chỉnh (fine-tune), giúp mô hình thích nghi trước với sai số số học

Chỉ so onnx với ptq và qta vì có công cụ chạy giống nhau (đều dùng onnx runtime): để đo chính xác đúng ảnh hưởng của việc chuyển FP32 -> int8
Nên để trong bảng kết quả là:


| Bản được đo | Biểu diễn số | Cách tạo                                                    |
| ------------------ | ----------------- | --------------------------------------------------------------- |
| ONNX FP32        | FP32            | Bản gốc làm mốc                                           |
| ONNX PTQ INT8    | INT8            | Lượng tử hóa sau khi train                                |
| ONNX QAT INT8    | INT8            | Có huấn luyện thêm để thích nghi với lượng tử hóa |

- Onnx FP32
- Onnx PTQ Int8
- Onnx QTA Int8

Cập nhật kết quả thực nghiệm mới nhất vào báo cáo

#####################
TN06: structure-prunning

- Mục đích: là để biết liệu khi cắt bớt phần tính toán có giúp mobilenetv3 nhẹ và nhanh hơn không


| Điểm khác nhau        | Không cấu trúc               | Có cấu trúc                            |
| -------------------------- | --------------------------------- | ------------------------------------------- |
| Bỏ gì?                 | Từng trọng số                | Cả kênh/bộ lọc/nhóm                  |
| Hình dạng mạng        | Thường giữ nguyên           | Có thể thay đổi                       |
| Tăng tốc               | Cần hỗ trợ tính toán thưa | Có thể dùng các phép tính nhỏ hơn |
| Chất lượng dự đoán | Có thể giảm                  | Có thể giảm                            |

Trong [structured_pruning.py](D:/nckh-flood-rescue/nckh2/products/fe/tools/structured_pruning.py), quy trình là:

1. Nạp trọng số từ model đã train.
2. Tính điểm dựa trên độ lớn trọng số của các nhóm kênh, dùng phương pháp GroupMagnitudeImportance(p=2).
3. Chọn các nhóm có điểm thấp để bỏ, đồng thời điều chỉnh phần liên quan ở các lớp khác.
4. Huấn luyện tinh chỉnh lại bằng tập train, chọn model theo validation.
5. Đánh giá cuối trên test.
   Đây là tiêu chí ước lượng: nhóm có trọng số nhỏ được xem là ứng viên để bỏ. Nó không bảo đảm nhóm đó hoàn toàn vô dụng, nên phải đo lại chất lượng sau khi cắt.


#################
TN07: Điểm khẩn cấp từ năm dấu hiệu do người dùng chọn
? Không có dữ liệu bệnh nhân, nhãn chuyên gia hay corpus tin nhắn: chưa hiểu
- Điểm E_i đã tính từ app nhưng gửi lên thì server không dùng, mà dùng LR (NGHI VẤN)



#################
TN08: Gom các báo cáo cùng một sự kiện: so sánh phương pháp
- So sánh những phương pháp gì
- Chưa hiểu luồng thực nghiệm như thế nào:
   Các phương pháp (method) trong csv kết quả là sao
- Kết quả benchmark_test_40runs chạy thực nghiệm là gồm đánh giá những gì


#################
TN09: Kiểm tra gom cụm khi GPS sai, thời gian lệch, báo cáo bị nhân bản
- Chưa hiểu luồng thực nghiệm như thế nào
- Giới hạn mà bạn nói: các mức do nhóm tự đặt ra, là mức gì 
- Cơ chế gây suy giảm chưa được cô lập là sao?


#################
TN10: Kiểm tra danh sách ưu tiên có xếp đúng sự kiện cần ưu tiên không
- Bộ dữ liệu bạn nói là có sẵn hả? của ai? có trong source code này không
- Chưa hiểu luồng thực nghiệm như thế nào:
- Tiêu chí đánh giá dựa trên cái gì? tại sao lại chọn những tiêu chí đó làm đánh giá? là tại đó giờ nó là như vậy hay sao

#################
TN11: Kiểm tra thứ tự ưu tiên khi có bản sao hoặc khai báo thao túng
- Chưa hiểu bộ dữ liệu là gì
- Kết quả nhận được là những cột gì
- Vè giới hạn bất biến đó, thì làm thế nào để giải thích trong báo cáo

################
TN12: Thử thay nhẹ các hệ số của công thức ưu tiên
- Đổi những hằng số nào, giữ cái nào
- Bộ dữ liệu gì
- Tại sao đưa ra tiêu chí đánh giá đó
- Tại sao thay đổi nhưng chất lượng xếp hạng yếu

################
TN13: Đo hệ quả điều phối sau khi dùng cụm dự đoán
