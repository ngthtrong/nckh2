# Báo cáo tổng kết NCKH sinh viên — bản nội dung sơ bộ

Đề tài **THS2026-68: Hệ thống phân tích đa phương thức và phân cụm sự kiện cứu hộ bão lũ dựa trên Edge AI**. Chủ nhiệm Lê Thị Ngọc Ảnh; giảng viên hướng dẫn TS. Nguyễn Thanh Khoa; thành viên theo `resource/infoGroup.md`.

Bản sơ bộ đã có Mở đầu đủ sáu mục, bốn chương khoa học, Kết luận/kiến nghị, hai phụ lục, thông tin kết quả Việt–Anh và bản tin/tóm tắt Việt–Anh. Nội dung dựa trên thuyết minh, mã nguồn và artifact trong repo hiện tại. Đây chưa phải hồ sơ nghiệm thu đủ điều kiện nộp.

## Biên dịch

Từ thư mục gốc repo:

```bash
make -C report doctor
make -C report results             # Xuất bảng và audit nguồn; không chạy huấn luyện
make -C report content             # Nội dung sơ bộ; tự xuất bảng trước
make -C report content-twoside
make -C report deliverables        # Bản tin/tóm tắt Việt–Anh, bốn PDF riêng
make -C report check
make -C report check-release       # Còn chặn vì metadata/mẫu/minh chứng chưa đủ
make -C report full                # Chỉ ghép khi mọi điều kiện hồ sơ được đáp ứng
make -C report full-twoside
make -C report smoke
```

PDF chính: `build/content/content.pdf`. Bốn sản phẩm riêng ở `build/bulletin-vi/`, `build/bulletin-en/`, `build/summary-vi/`, `build/summary-en/`. `build/` được Git bỏ qua. `make clean` chỉ xóa đầu ra build.

Yêu cầu XeLaTeX, KOMA-Script, các gói trong `template/packages.tex`, Python 3.9+ và Times New Roman đủ bốn kiểu. Build tự chọn biblatex/biber khi có, nếu không dùng BibTeX/natbib; có thể chỉ định `BIBLIOGRAPHY=biblatex` hoặc `BIBLIOGRAPHY=bibtex`. `xurl` được dùng khi có để ngắt đường dẫn dài. Không cần latexmk; bộ build chạy đủ lượt để giải quyết tham chiếu.

## Nội dung và căn cứ

- `config/metadata.tex`: nguồn thông tin hành chính dùng khi biên dịch, đồng bộ với `resource/infoGroup.md`. Người dùng đã xác nhận ngày 06/10/2026: chủ nhiệm nữ, dân tộc Kinh, ngành Kỹ thuật phần mềm CLC, khóa 49, năm thứ 4, chương trình 4,5 năm và các thông tin hành chính còn lại. Các trường đã có trước đó lấy từ thuyết minh và email GVHD từ bản thảo. Bìa báo cáo ghi tháng 10/2026.
- `chapters/`: bài toán, yêu cầu, dữ liệu, công thức, kiến trúc, triển khai, thực nghiệm và đối chiếu mục tiêu. Phân biệt LR khẩn cấp có cấu trúc với NLP, demo với scheduler nghiên cứu, mô phỏng với dữ liệu thực địa.
- `generated/`: 13 bảng và macro xuất bằng `scripts/export_results.py`, cùng hash nguồn/audit. Xem [quy trình số liệu](generated/README.md).
- `frontmatter/`: đủ năm thành viên và các nội dung sơ bộ; những mẫu và thông tin chưa biết còn đánh dấu rõ.
- `appendices/`: nguồn, snapshot lịch sử, tái lập, khác biệt phiên bản và kế hoạch bổ sung kiểm chứng.
- `deliverables/content/`: bản tin/tóm tắt Việt–Anh, dùng lại trong bản đầy đủ.
- `bibliography/articles.bib`: 14 nguồn thực sự trích dẫn. Không tạo văn bản pháp quy hoặc tài liệu mẫu để lấp nhóm trống.
- `evidence/`: manifest ánh xạ ba sản phẩm nhóm III theo mục 17; các cờ xác nhận giữ false và chưa có PDF minh chứng. Nhóm I/II không đăng ký; bản thảo là sản phẩm bổ sung.

Các số liệu chính dùng snapshot ảnh **1.702 mẫu, test 256 ảnh, đầu vào 256**, khác README/notebook cũ (1.621/1.625 mẫu, test 244, đầu vào 224). Accuracy FP32 hiện tại 76,17% không được so với 73,77% của split cũ để kết luận cải thiện. Các kết luận cũ thiếu split/INT8/ONNX được cập nhật theo file đang tồn tại.

**Điểm cần rà soát số liệu:** PTQ/QAT summary chưa khớp hoàn toàn CSV dự đoán. QAT summary ghi Accuracy 52,34%, CSV tính ra 51,17%. Báo cáo giữ cả hai nguồn và bảng đối chiếu, chưa xem metric nén là số liệu đã chốt. FP32/pruning khớp CSV; ảnh khớp MD5/split. Mã backend chưa đọc `E_i` mà app gửi khi chuyển sang thuật toán; điều này được ghi như khoảng trống tích hợp, không sửa sản phẩm trong công việc soạn báo cáo.

## Hình thức và hồ sơ

Thân bài A4, Times New Roman 13 bp, giãn dòng 1,3; lề trái 30 mm, phải/trên/dưới 20 mm. Hai bìa dùng khung đôi, nội dung căn giữa riêng. Phần đầu đánh La Mã; Mở đầu bắt đầu số Ả Rập. Các chương không ép mở ở trang lẻ; hai mặt giữ lề vật lý quy định. Hình/bảng/công thức dùng nhãn và tham chiếu, có ghi nguồn.

`make check` cho phép bản sơ bộ và liệt kê thiếu sót. Bộ kiểm tra bản đầy đủ giữ điều kiện 50 trang thân bài theo guideline, không giới hạn tối đa; đủ số trang không thay thế nội dung/hồ sơ. Các trường giới tính, dân tộc, ngành, năm học và số năm đào tạo đã được cập nhật theo xác nhận của người dùng. Ba mẫu đầu quyển và bốn sản phẩm riêng cần đối chiếu biểu mẫu chính thức. Không có chữ ký/dấu hoặc phê duyệt được tạo giả.

Sau phụ lục khoa học, bản đầy đủ ghép thuyết minh đã phê duyệt, minh chứng đăng ký nhóm I–III và bốn sản phẩm Việt–Anh; video nộp riêng. Đường dẫn minh chứng trong manifest là nơi dành cho hồ sơ sẽ cung cấp, không phải PDF đã tồn tại. Xem [quy ước hồ sơ](evidence/README.md) và [quy trình Word](word/README.md).

Bản sơ bộ tổng hợp kết quả runtime/Colab/test lịch sử; không tuyên bố chạy lại huấn luyện, notebook, E2E hoặc Android khi viết báo cáo. Kiểm tra mới là ảnh/hash/split, CSV–metric, sinh bảng và biên dịch PDF. Các hạn chế thiết bị, mạng thật, nguồn ảnh và xác nhận chuyên gia được trình bày trong nội dung.

## Kiểm tra bản sơ bộ ngày 06/10/2026

Đã biên dịch bản nội dung 75 trang (50 trang từ Mở đầu tới hết Kết luận/kiến nghị), bản tin Việt/Anh mỗi bản 2 trang, tóm tắt Việt 2 trang và Anh 3 trang. Năm log cuối không có tràn khung, tham chiếu/trích dẫn chưa giải quyết, nhãn lặp hoặc cảnh báo phông thay thế. PDF chính A4, các phông được nhúng; đã xem các trang sơ đồ và bảng đối chiếu metric. `git diff --check` và `make check` đạt kiểm tra bản sơ bộ.

Sau khi cập nhật thông tin hành chính, `make check-release` còn chặn ở 7 ghi chú chờ mẫu chính thức và PDF/cờ xác nhận minh chứng. Phần metadata và chương/phụ lục khoa học không còn placeholder. Dù nội dung đủ 50 trang, trạng thái này chưa xác nhận hồ sơ đủ điều kiện nộp. Hai mặt, Word, huấn luyện, benchmark và kiểm thử thiết bị không được chạy lại trong đợt viết nội dung này.
