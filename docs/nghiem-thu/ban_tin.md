# Bản tin đề tài (bản nháp để chép vào mẫu Word của ĐHCT)

Hướng dẫn nghiệm thu NCKH sinh viên ĐHCT 2026 yêu cầu hai bản tin (tiếng Việt, tiếng Anh), mỗi
bản tối đa **01 trang A4**, điền theo mẫu "Mẫu sản phẩm: Bản tin" trong file biểu mẫu. Trước khi
nộp: điền mã số đề tài, chèn ảnh đại diện (gợi ý: ảnh chụp dashboard [dashboard.png](dashboard.png),
do nhóm tự tạo nên không vướng tác quyền) và xóa dòng ghi chú của mẫu.

Nguồn thông tin: `resource/Thuyết minh NCKH.md` (thông tin hành chính), khối tác giả của
`paper/main.tex` (email cán bộ hướng dẫn), [doi_chieu_thuyet_minh.md](doi_chieu_thuyet_minh.md)
(kết quả).

---

## Bản tiếng Việt

**BẢN TIN ĐỀ TÀI NGHIÊN CỨU KHOA HỌC CỦA SINH VIÊN**

**Mã số đề tài:** [điền mã do Phòng KH, CN và ĐMST cấp]

**Tên đề tài:** Hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI

**Thời gian thực hiện:** 06 tháng (03/2026 – 08/2026)

**Tổng kinh phí:** 15.000.000 VNĐ

**Chủ nhiệm đề tài:** Lê Thị Ngọc Ảnh (0376932994)

**Thành viên tham gia nghiên cứu:** Nguyễn Như Quỳnh, Nguyễn Thanh Trọng, Ngô Hưng Thịnh, Cao Tường Hưng

**Cán bộ hướng dẫn:** TS. Nguyễn Thanh Khoa (ntkhoa@ctu.edu.vn)

**Tính cấp thiết:** Khi bão lũ, hạ tầng viễn thông thường gián đoạn hoặc quá tải; tin cầu cứu gửi
về rời rạc, trùng lặp và khó kiểm chứng, trong khi các hệ thống hiện có phụ thuộc vào đường truyền
Internet ổn định để gửi ảnh, video về máy chủ.

**Mục tiêu:** Xây dựng hệ thống phân tích sơ bộ mức ngập ngay trên điện thoại, gửi thông tin cầu
cứu gọn nhẹ khi mạng yếu, và gom nhóm các báo cáo trùng lặp để xếp hạng ưu tiên, hỗ trợ điều phối
lực lượng cứu hộ.

**Phương pháp nghiên cứu:** Học chuyển giao mô hình nhẹ MobileNetV3-Large và triển khai trên thiết
bị (ONNX Runtime, ExecuTorch); cơ chế lưu trước – gửi sau với chống trùng lặp; phân cụm đồ thị
không gian – thời gian – ngữ cảnh (Louvain) và điểm ưu tiên có chặn; thực nghiệm trên dữ liệu bán
tổng hợp và giả lập mạng 2G/3G/4G.

**Nội dung nghiên cứu:** Xây dựng bộ 1.621 ảnh với 4 mức ngập; huấn luyện và chuyển đổi mô hình;
phát triển ứng dụng di động Flutter; xây dựng máy chủ FastAPI và website bản đồ điều phối; đánh giá
thuật toán phân cụm, xếp hạng và hiệu năng truyền trong điều kiện mạng yếu.

**Kết quả đạt được:** Ứng dụng di động nhận diện mức ngập ngoại tuyến (Accuracy 73,8%, macro-F1
72,2% trên tập test độc lập); KQ_NEN website bản đồ hiển thị cụm sự kiện và thứ tự ưu tiên, tự cập nhật
mỗi 5 giây; KQ_MANG 01 bài báo tại hội nghị ISDS 2026.

**Ý nghĩa:** Đưa khả năng xử lý thông minh xuống thiết bị đầu cuối, giảm phụ thuộc vào đường truyền;
cung cấp bằng chứng định lượng về điểm mạnh và giới hạn của phân cụm, xếp hạng tin cầu cứu.

**Khả năng ứng dụng:** Tài liệu học tập, nghiên cứu cho sinh viên CNTT; nền tảng thử nghiệm cho các
đơn vị phòng chống thiên tai và tìm kiếm cứu nạn sau khi được kiểm chứng thêm với dữ liệu thực địa.

---

## English version

**SUMMARY REPORT RESEARCH PROJECT**

**Project code:** [code assigned by the Office of Science, Technology and Innovation]

**Project title:** An Edge AI–Based System for Multimodal Analysis and Clustering of Flood Rescue Events

**Project period:** 6 months (03/2026 – 08/2026)

**Total cost:** 15,000,000 VND

**Project leader:** Le Thi Ngoc Anh (0376932994)

**Project members:** Nguyen Nhu Quynh, Nguyen Thanh Trong, Ngo Hung Thinh, Cao Tuong Hung

**Advisor:** Dr. Nguyen Thanh Khoa (ntkhoa@ctu.edu.vn)

**Necessity of the project:** During storms and floods, telecommunication networks are often
disrupted or overloaded. Rescue requests arrive fragmented, duplicated and hard to verify, while
existing systems depend on a stable Internet connection to upload photos and videos.

**Objectives:** To build a system that estimates flood severity directly on the phone, sends compact
rescue reports over weak networks, and groups duplicate reports into prioritized events to support
rescue coordination.

**Methodology:** Transfer learning of the lightweight MobileNetV3-Large model deployed on device
(ONNX Runtime, ExecuTorch); store-and-forward delivery with deduplication; spatial–temporal–context
graph clustering (Louvain) with a bounded priority score; experiments on semi-synthetic data and
simulated 2G/3G/4G networks.

**Project activities:** Building a 1,621-image dataset with four flood levels; training and
converting the model; developing a Flutter mobile app; building a FastAPI server and a map-based
coordination website; evaluating clustering, ranking and transmission performance under weak
networks.

**Research results:** An offline flood-level recognition app (accuracy 73.8%, macro-F1 72.2% on an
independent test set); KQ_NEN_EN a map website showing event clusters and priority order, refreshed every
5 seconds; KQ_MANG_EN one paper at the ISDS 2026 conference.

**Research new finding:** On-device analysis reduces dependence on network connectivity; the study
gives quantitative evidence of the strengths and limits of clustering and ranking rescue reports.

**Application potentials:** Teaching and research material for IT students; a testbed for disaster
prevention and search-and-rescue agencies after further validation with field data.
