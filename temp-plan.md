# Kế hoạch camera-ready đã triển khai: EasyChair và RQ1 v2

Ngày cập nhật: 11/09/2026 UTC. Baseline thực thi: nhánh `clean`, HEAD
`edefb9c`; bản đã nộp trước đây là tag `v1.0.1`. Kế hoạch này thay thế các bản
nháp trước. Commit, push, release, ký LTP và upload EasyChair không thuộc lần
triển khai này.

## 1. Audit và lựa chọn bằng chứng — đã hoàn thành

- Giữ `src/results/rq1_results/` làm nguồn chính và
  `src/results/rq1_results_v2/full/` làm lần chạy đối chiếu; không gộp thành 80
  run độc lập và không chọn nguồn theo kết quả tốt hơn.
- Cả hai gói đều đủ 280 checkpoint, 1.400 fit, 92.617 mapping, 35 summary và
  300 paired effect. Các thống kê và 5.000 bootstrap được tái tính bằng NumPy
  2.5.1 với sai số tối đa `1e-10`.
- Manifest lần đầu có 288 checksum/Python 3.13.15; v2 có 287
  checksum/Python 3.12.13. Protocol và package versions giống nhau nhưng chưa
  khóa `python_version`.
- Bảy checkpoint smoke v2 khớp full ở mọi kết quả ngoài runtime; 35 smoke fit
  chỉ là kiểm tra kỹ thuật.
- Báo cáo keyed comparison 1.400 dòng xác nhận 43 thay đổi ARI, chỉ thuộc copy
  2× của bốn phương pháp đồ thị. Control, GPS, time và copy 5× không đổi.
- Việc còn chờ: ZIP gốc và xác nhận runtime/resume của hai lần; notebook đã
  thực thi của v2. Chưa tuyên bố tái lập xuyên môi trường đạt.

## 2. Nội dung khoa học và bố cục — đã hoàn thành

- Bốn nhóm phương trình confidence, contextual similarity, graph affinities và
  priority được đánh số liên tục; ký hiệu, miền, đơn vị, scale, trọng số và
  miền `0 <= P_k <= mu` được giải thích tại chỗ.
- Pseudocode tham chiếu phương trình thay vì khai triển lặp; thuật toán, cấu
  hình và dữ liệu không đổi.
- Bảng stress RQ1 được thay bằng heatmap 6 × 5 của mean paired Delta ARI từ
  lần đầu. Script khóa nguồn, kiểm tra đúng 30 ô và xuất PDF vector có số ghi
  trực tiếp, đọc được ở grayscale.
- Giữ kết quả bất lợi Product Louvain copy 5×: Delta `-.6108`, CI
  `[-.6318,-.5881]`; nêu v2 chỉ làm thay đổi nhẹ ARI copy 2× và không gộp runs.
- Xóa hai hình RQ2/RQ3 và bảng headline trùng lặp; giữ benchmark, robustness và
  sensitivity. Bản Docker/Tectonic hiện có đúng 15 trang.
- Chỉ Thanh-Trong Nguyen là corresponding author; tám tác giả được giữ theo
  xác nhận ban tổ chức đã duyệt. Email liên hệ được ghi đầy đủ là
  `trongb2305615@student.ctu.edu.vn` và phải khớp EasyChair, LTP và đầu mối
  nhận proof.
- Audit sau cùng tách singleton khỏi hệ quả `D < h r`, bổ sung urgency
  inflation vào diễn giải bất lợi, và định nghĩa community detector/affinity
  construction ngay lần xuất hiện đầu trong Abstract.

## 3. Quyền nội dung và khả dụng dữ liệu — đã hoàn thành trong workspace

- MIT được giới hạn rõ cho source code. `LICENSE-CONTENT` không cấp CC BY mới
  từ snapshot hiện tại; contribution camera-ready thuộc LTP khi hợp đồng được
  ký, phần phi code ngoài hợp đồng được bảo lưu quyền.
- Không sửa tag/release/metadata `v1.0.1` và không tuyên bố thu hồi quyền đã cấp
  cho snapshot cũ.
- Data and Code Availability phân biệt `v1.0.1`, artifact stress chính và v2;
  kết quả mới không được mô tả là đã nằm trong release cũ.
- Remote đã được kiểm tra: `clean` công khai ở commit `5fad10d` và tag
  `v1.0.1` vẫn là `be95d4c`.

## 4. Gói EasyChair — đã build sạch, chờ nhóm duyệt

- ZIP source có `main.tex` tại root, bibliography, `main.bbl`, `llncs.cls`,
  `splncs04.bst` và chỉ hai hình đang dùng; loại notebook, kết quả, cache và tài
  liệu nội bộ.
- Trường dự kiến: main file `main.tex`, engine `xelatex`, bibliography
  `bibtex`; PDF phải tương ứng với ZIP.
- Đã có alt text cho pipeline và heatmap. Hạn ghi nhận là 16/09/2026; nhóm cần
  xác nhận giờ/múi giờ và hoàn tất nội bộ ngày 15/09.
- Build Tectonic là kiểm tra bổ sung. Chuỗi sạch
  `xelatex -> bibtex -> xelatex -> xelatex` từ ZIP đã đạt bằng TeX Live 2026,
  không có lỗi, undefined citation/reference hoặc overfull box và cho 15 trang.
  Phải chạy lại chuỗi này nếu nhóm duyệt thêm thay đổi.
- Thanh-Trong Nguyen, Ngoc-Anh Le, Nhu-Quynh Nguyen, Tuong-Hung Cao, Hung-Thinh Ngo, Xuan-Phuong Chau, Lan Phuong Phan, and Thanh-Khoa Nguyen

## 5. Việc nhóm phải hoàn tất

| Ưu tiên | Bên phụ trách             | Việc                                                                         | Bằng chứng đóng việc                         |
| --------- | ---------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------- |
| P0        | Người chạy Colab          | Gửi ZIP gốc hai lần, notebook v2 và lịch sử runtime/resume              | Hash ZIP và nguồn checkpoint được xác nhận |
| P0        | Người liên hệ hội nghị | Xác nhận giờ/múi giờ, kênh alt text và LTP                             | Lưu hướng dẫn chính thức                    |
| P1        | Nhóm tác giả              | Duyệt PDF, heatmap, kết luận, tám tác giả và một corresponding author | Chấp thuận bằng văn bản                      |
| P1        | Thanh-Trong Nguyen           | Hoàn thiện, ký tay và scan LTP sau khi nhóm đồng thuận                | PDF LTP rõ nét, metadata khớp                  |
| P2        | Artifact owner               | Quyết định release/DOI mới cho kết quả camera-ready                     | Bài trỏ đúng archive nếu phát hành         |
| P2        | Submission owner             | Upload ZIP, PDF và LTP sau duyệt cuối                                      | Biên nhận EasyChair/đăng ký                  |
