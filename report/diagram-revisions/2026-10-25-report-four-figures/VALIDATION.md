# Kết quả kiểm tra — 25/10/2026

## PDF báo cáo

- `make -C report content`: **PASS**. Quyển mới có **154 trang A4**; đã cập nhật cả `report/build/content/content.pdf` và `report/main.pdf` với cùng nội dung.
- Đã dựng lại bốn sản phẩm bản tin/tóm tắt theo workflow của repository. Văn bản trích xuất giống bản gốc, nên giữ nguyên byte PDF của các sản phẩm riêng để tránh tạo diff ngoài phạm vi bốn sơ đồ.
- Log cuối `build/content/content.log` không có `Overfull \\hbox`, `Overfull \\vbox`, undefined references/citations, duplicate labels hoặc missing characters.
- `git diff --check`: **PASS**.

| Hình | Trang PDF, tính từ 1 | Số trang in | Ảnh kiểm tra trực tiếp |
| --- | ---: | ---: | --- |
| 2.1 | 32 | 12 | [figure-2.1.png](pages/figure-2.1.png) |
| 2.2 | 34 | 14 | [figure-2.2.png](pages/figure-2.2.png) |
| 2.5 | 39 | 19 | [figure-2.5.png](pages/figure-2.5.png) |
| 2.12 | 47 | 27 | [figure-2.12.png](pages/figure-2.12.png) |

Đã xem trực tiếp cả bốn trang sau biên dịch: nội dung nằm trong vùng in, chữ không chạm cạnh hình thoi, không bị cắt, không có mũi tên xuyên qua chữ trong các hộp. Hình 2.2 dùng bốn dải ngang; Hình 2.5 giữ khoảng trắng giữa các nhóm bảng để đọc được tên cột và khóa.

## Hình và nguồn chỉnh sửa

- PDF vector rộng **453,5433 pt = 160 mm**. Font trong PDF được nhúng; font chữ nội dung/chú giải từ **9 pt** trở lên. `pdftohtml -xml -zoom 1` đọc các cỡ chữ làm tròn **9 và 10 pt**, lưu ở `pdf-font-sizes.json`.
- Cả bốn hình qua kiểm tra bounding box chữ trong script; source và output có SHA-256 trong `validation.json`.
- XML của bốn Draw.io riêng và bản gộp có thể phân tích; mọi `source`/`target` của cạnh tham chiếu đến ID tồn tại.
- Hash của toàn bộ tệp trong `originals/` khớp `original-manifest.json`.
- Đối chiếu tĩnh với mã nguồn; không chạy test vận hành app/backend, SMS, huấn luyện hoặc benchmark vì thay đổi chỉ ở hình và thuyết minh.

## Kiểm tra toàn báo cáo

`make -C report check`: **FAIL do bốn hash nguồn biểu đồ kết quả đã cũ từ trước**, không phải bốn sơ đồ vừa sửa:

1. `products/fe/reports/seed1024/pth_onnx_pte/summary.json`
2. `products/fe/reports/seed1024/pth_onnx_pte/all_predictions.csv`
3. `products/fe/reports/seed1024/fp32_ptq_qat/summary.json`
4. `products/fe/reports/seed1024/prunning_st/summary.json`

Đã so sánh với Git HEAD: cả bốn tệp nguồn và các hash lưu trong `figure-provenance.json` đều không bị thay đổi trong công việc này. Chi tiết digest và bằng chứng `unchanged_from_HEAD` nằm trong `preexisting-figure-provenance.json`; đầu ra kiểm tra nằm trong `check.log`. Không sửa hash để bỏ qua kiểm tra, cũng không tái tạo các biểu đồ kết quả ngoài phạm vi yêu cầu.

Kiểm tra còn ghi nhận một dòng placeholder ở `frontmatter/research-info-vi.tex:10`; đây không phải điều kiện làm bản draft thất bại. Không chạy `check-release` và không khẳng định hồ sơ đủ điều kiện nộp.

## Figma

Đã gọi công cụ `generate_diagram` cho bản FigJam quy trình tổng thể. Công cụ yêu cầu người dùng chọn team/organization trong widget trước khi tạo; chưa có file FigJam hoặc liên kết Figma được trả về. Các hình đã tích hợp dùng phương án Python được người dùng cho phép, có nguồn Draw.io/SVG để chỉnh tiếp.
