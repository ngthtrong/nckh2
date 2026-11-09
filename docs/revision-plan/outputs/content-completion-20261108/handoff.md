# Bàn giao nội dung nhận xét 02–15

Ngày: 08/11/2026, Asia/Taipei. Phạm vi người dùng xác nhận: thực hiện ND-01–ND-06.

**Trạng thái:** đã hoàn thành ND-01–ND-06 trong phạm vi hoàn thiện nội dung và kiểm PDF. Không xác nhận thay Hội đồng hoặc chuyển thiết kế thành kết quả thực nghiệm.

## Nội dung đã bổ sung

- ND-01: đồng bộ CrisisMMD trong Mở đầu, nghiên cứu liên quan, bản đồ phương pháp/dữ liệu và phạm vi; bổ sung hai mục mới trong Chương 3.
- ND-02: quy trình dữ liệu sáu công đoạn; giải thích ảnh gốc, tiền xử lý, nén và LR; sơ đồ luồng khẩn cấp hiện tại/đề xuất.
- ND-03: thiết kế DistilBERT tiếng Việt, đầu vào/đầu ra, nhãn dự thảo, loss/chọn checkpoint, ví dụ minh họa; bảng vai trò văn bản; ba mức tích hợp và thiết kế fusion.
- ND-04: ablation chung nhãn/ID, xử lý thiếu nguồn, kế hoạch camera/Android; bàn luận từng RQ và bảng ranh giới bằng chứng.
- ND-05: bảng đối chiếu thuyết minh bốn cột; đồng bộ kết luận, hai nguồn dùng chung và bản tin Việt–Anh.
- ND-06: rút lặp biểu mẫu Việt để chữ ký cùng nội dung; rút tổng kết để tránh trang cuối ngắn; không đổi font/lề, ảnh hoặc cấu hình chèn thuyết minh.

## Hai trạng thái độc lập cho từng nhận xét

| Nhận xét | Nội dung phản hồi trong báo cáo | Trạng thái thực hiện/đánh giá |
|---|---|---|
| 02 — Khoảng trắng | Rút nội dung lặp trong biểu mẫu Việt, kiểm khối ký cùng trang nội dung (`form-vi`) | Đã sửa bố cục; chữ ký Việt cùng trang nội dung (PDF 17) |
| 03 — Ảnh chủ nhiệm | Giữ ảnh và kiểm lại tỷ lệ/vị trí (`form-photo`) | Ảnh đã có; chỉ kiểm bố cục |
| 04 — Đánh số hình | Caption/label/danh mục/tham chiếu tự động kể cả sơ đồ mới (`fig:multimodal-levels; fig:urgency-current-proposed`) | Kiểm toàn bộ nguồn và PDF; không đổi kết quả |
| 05 — Định dạng | Giữ font/lề; thống nhất trạng thái và thuật ngữ (`sec:text-design; sec:multimodal-design`) | Chỉ chuẩn hóa biên soạn và bố cục |
| 06 — Mô hình văn bản | Mục riêng gồm task/nhãn/tokenizer/encoder/head/loss/chọn checkpoint/trích xuất (`sec:text-design`) | Thiết kế tiếng Việt chưa huấn luyện; TF-IDF CrisisMMD đã chạy trên task khác |
| 07 — Nén mô hình | Giải thích lượng tử hóa/cắt tỉa và đánh đổi chất lượng/lỗi/dung lượng/timing (`sec:02-optimization`) | Phân tích kết quả đã lưu; không chọn lại hoặc sửa model |
| 08 — Đa phương thức | Bảng ba mức, công thức fusion pilot và sơ đồ tuyến đề xuất (`sec:multimodal-design; fig:multimodal-levels`) | Pilot CrisisMMD đã huấn luyện offline; fusion tiếng Việt/app chưa thực hiện |
| 09 — Vai trò ngôn ngữ | Bảng chức năng văn bản và ví dụ tự soạn ghi rõ minh họa (`tab:text-roles`) | NLP/trích xuất tiếng Việt là thiết kế; heuristic adapter và pilot có phạm vi riêng |
| 10 — Ablation | Giữ pilot/common test và thêm cấu hình chung task tiếng Việt (`sec:vi-ablation-plan; sec:multimodal-pilot`) | Pilot đã chạy; ablation tiếng Việt chưa thực hiện; không có CI/số mới |
| 11 — Quy trình dữ liệu | Sáu công đoạn và bảng hồ sơ có/thiếu/phương án (`sec:data-process; tab:data-process`) | Mô tả từ hồ sơ; source/license/IAA và checksum split lúc train vẫn thiếu |
| 12 — Đặc điểm ảnh | Giữ thống kê header/lớp và mở rộng EXIF/RGB/letterbox/chất lượng (`tab:image-profile; sec:image-design`) | Dùng thống kê đã lưu; không phải ảnh camera được kiểm chứng |
| 13 — Điểm khẩn cấp | OR/đối xứng/hệ số/threshold/ví dụ đại số và luồng hiện tại/đề xuất (`sec:02-urgency-lr; fig:urgency-current-proposed`) | Adapter chưa đọc E_i; không sửa tích hợp hoặc xác nhận trọng số chuyên môn |
| 14 — RQ1–RQ3 | Câu trả lời/đối chứng/cơ chế khả dĩ/giới hạn và bảng ranh giới bằng chứng (`sec:rq1-discussion; sec:rq2-discussion; sec:rq3-discussion; tab:rq-evidence-boundaries`) | Giữ số lịch sử và kết quả âm; 3 raw Spearman + 5 Holm vẫn OPEN, không thống kê lại |
| 15 — Chất lượng ảnh di động | CPU hiện có + kịch bản camera, đánh giá chất lượng và phiên timing riêng (`sec:camera-evaluation-plan; sec:camera-session-plan; sec:image-quality-cpu-results`) | CPU đã có; camera/Android suy giảm chưa thực hiện, không đo thêm |

Nguồn và nhãn cụ thể: [response-matrix.csv](response-matrix.csv). Ma trận đã có cột số mục, trang in và trang PDF lấy từ nhãn của bản cuối.

## Bản bàn giao và kết quả kiểm tra

- Một mặt: `report/main.pdf` khớp nguyên byte `report/build/content/content.pdf`, 194 trang. Hai mặt: `report/build/content-twoside/content.pdf`, 194 trang.
- Thân bài từ Mở đầu tới hết Kết luận: 132 trang; đối chiếu 50 hình và 48 bảng với nguồn/danh mục/nhãn/PDF đạt.
- Bản tin Việt/Anh: 1/1 trang; tóm tắt Việt/Anh: 2/3 trang; bốn bản đã dựng lại.
- `make -C report content`, `make -C report content-twoside`, `make -C report check`, kiểm `build/content-twoside`, kiểm float hai bản và `git diff --check`: exit 0.
- Sáu log cuối không có tràn khung/hình quá lớn, nhãn trùng, tham chiếu/trích dẫn lỗi hoặc font thay thế; các font PDF đều được nhúng.
- Đã xem 55 trang chọn ở bản một mặt và 62 trang ở bản hai mặt, cùng tổng thể bản trước chỉnh dòng kết luận cuối. Chữ ký Việt ở PDF17; biểu mẫu Anh kết thúc PDF20; ảnh ở PDF21. Kết luận kết thúc PDF153, thư mục tài liệu bắt đầu PDF154. Thuyết minh 12 trang ở PDF173–184, trang in152–163, giữ scale105%.
- Ô nhận xét GVHD còn trống có chủ đích; không chạy check-release hoặc xác nhận đầy đủ hồ sơ. ARS preflight và acronym là kiểm riêng có giới hạn ở `review-notes.md`.

[Hash/số trang PDF](checks/delivery-pdfs.json), [receipt trực quan](checks/visual-review.json), [log kiểm một mặt](checks/check-one-delivery.log), [log kiểm hai mặt](checks/check-two-delivery.log), [nhãn/số trang](label-pages-one.json).

## Kiểm chứng và phạm vi bảo toàn

Lệnh và log từng lần dựng nằm trong [checks/](checks/). Chỉ receipt `content-delivery` và `twoside-delivery` sau cùng được dùng cho bản bàn giao; các lần trước là trung gian. Kiểm khoa học không được suy từ build/check. Bốn bản tin/tóm tắt được dựng lại từ cùng nguồn trong mỗi target nội dung.

Đã lưu baseline trước sửa, [25 thay đổi nguồn báo cáo](report-source-changes.json) và [diff riêng của đợt ND](report-source-diff.patch), tách khỏi working tree đã bẩn sẵn. `main.tex`, `template/forms.tex`, `template/typography.tex` và `frontmatter/principal-investigator.tex` khớp hash đầu đợt; vòng chèn 12 trang thuyết minh với `scale=1.05` được giữ. Không sửa app/backend/model/raw RQ hoặc ledger P00–P14; không commit/push.

Hai nguồn mới cho kiến trúc DistilBERT đã được mở trực tiếp; [receipt](new-reference-checks.json) chỉ xác nhận thông tin thiết kế được trích, không xác nhận hiệu năng tiếng Việt/điện thoại. Rà soát tích hợp là kiểm cục bộ cùng họ mô hình, không phải đánh giá khoa học độc lập. Xem [ghi chú phạm vi kiểm tra](review-notes.md).

## Những phần vẫn chưa thực hiện

NLP/fusion cứu hộ tiếng Việt, corpus/nhãn chung, đánh giá camera/Android suy giảm và tích hợp điểm mới vào adapter vẫn là thiết kế. Hồ sơ nguồn/license/IAA, checksum split lúc train, raw E2E, xác nhận trọng số chuyên môn và tám trường RQ2 còn thiếu/chưa khớp. Giữ nguyên ba raw p Spearman và năm Holm OPEN; không chạy lại thống kê. Không dùng việc hoàn thiện nội dung để xác nhận nghiệm thu, hiệu quả thực địa hoặc hoàn thành cam kết thực nghiệm.
