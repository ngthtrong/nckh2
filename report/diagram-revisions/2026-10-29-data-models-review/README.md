# CDM, LDM và PDM — bản riêng để review

Ba sơ đồ dùng **tiếng Anh**. Bộ này chưa được chèn vào báo cáo, chưa thay ERD đang có và không thay đổi backend/CSDL đang vận hành.

**Xem nhanh:** [review.pdf](review.pdf) — ba trang, theo thứ tự CDM → LDM → PDM. PDM có đủ cột nên nên mở PDF/SVG và phóng to để đọc.

| Sơ đồ | PDF | Nguồn chỉnh sửa | Vector | Ảnh |
|---|---|---|---|---|
| CDM — 9 thực thể nghiệp vụ | [PDF](01-cdm.pdf) | [Draw.io](01-cdm.drawio) | [SVG](01-cdm.svg) | [PNG](01-cdm.png) |
| LDM — 10 thực thể, khóa và kiểu logic | [PDF](02-ldm.pdf) | [Draw.io](02-ldm.drawio) | [SVG](02-ldm.svg) | [PNG](02-ldm.png) |
| PDM — 13 bảng SQLite, đầy đủ cột | [PDF](03-pdm.pdf) | [Draw.io](03-pdm.drawio) | [SVG](03-pdm.svg) | [PNG](03-pdm.png) |

## Quy tắc lấy từ bộ mẫu

Đã đọc `template-diagram-system/README.md`, `erd.py`, `ve_hinh.py`, `ve_ldm.py` và `ve_pdm.py`. Phần dựng hình/định tuyến được điều chỉnh từ `erd.py`, lưu riêng tại [scripts/erd_renderer.py](scripts/erd_renderer.py); không sửa bộ mẫu gốc.

- Crow's Foot cho bốn lực lượng `1`, `0..1`, `0..many`, `1..many`.
- Chìa khóa và gạch chân thuộc tính khóa chính; `N` chỉ thuộc tính cho phép NULL.
- Trong LDM/PDM, nét liền khi toàn bộ FK tham gia PK của thực thể con; nét đứt cho quan hệ không định danh. Trong CDM, đường chỉ biểu diễn liên hệ nghiệp vụ.
- Đường đi ngang/dọc, tách cổng nối, tránh xuyên hộp, không chồng đoạn; điểm cắt có khoảng ngắt để tránh hiểu nhầm thành điểm nối.
- Header xanh nhạt và viền xanh đậm; nhóm chức năng trong PDM; dùng cùng hình học cho các đầu ra.
- Font serif có đủ ký tự toán học; dùng DejaVu Serif để dựng lại được trên Linux.

Khác bản PDM tổng quan của mẫu, PDM review này hiển thị **toàn bộ cột và kiểu SQLite**, không chỉ tên bảng. Không lược FK bằng nhãn tham chiếu vì quy mô chỉ có 13 bảng. SQL và từ điển bổ sung các CHECK, DEFAULT, UNIQUE ghép và index để tránh làm sơ đồ quá dày chữ.

## Giả định thiết kế

Giả định theo yêu cầu: đường xử lý đầy đủ đã được tích hợp; mọi bản ghi tham gia lần phân tích trong bộ thiết kế này có đủ `L, T, F, E, N, V`. `Q` là giá trị dẫn xuất theo lần chạy, không phải confidence softmax của ảnh.

Điều này không bắt buộc mọi báo cáo vừa tiếp nhận phải đầy đủ. Bảng `reports` vẫn nhận dữ liệu thiếu; chỉ dữ liệu đã đủ và thuộc đầu vào hoạt động của lần chạy mới xuất hiện trong `analysis_members`. Báo cáo thiếu `L/T` tiếp tục nằm trong hàng xem xét, không tạo tọa độ/thời gian giả. Bộ này không mô hình hóa một thực nghiệm thiếu dữ liệu.

- Với báo cáo từ app trong giả định tích hợp đầy đủ: `urgency_lr` giữ điểm LR, `urgency` là `E` chuẩn hóa đưa vào công thức; dùng trực tiếp điểm LR này khi đó là nguồn khẩn cấp được chọn. Không tự đặt một công thức trộn LR/keyword mới. Nguồn SMS/tổng đài cần có đầu vào `E` hợp lệ trước khi tham gia đường xử lý đầy đủ.
- `people_count` là `N` khai báo tường minh; không bắt buộc cộng số mắc kẹt với số bị thương vì hai nhóm có thể giao nhau. `vulnerability` giữ `V` đã được xác định; không mặc định số nhóm yếu thế là số người yếu thế.
- `has_image`, nhóm nguồn, provenance và fingerprint được lưu trong snapshot. Số payload khác nhau củng cố lân cận là `n_corrob`; không đếm retry hay bản sao exact thành nguồn bằng chứng mới.
- Cấu hình và snapshot của một lần chạy hoàn tất phải được giữ bất biến ở tầng dịch vụ. Một phiên bản cấu hình dùng được cho nhiều lần chạy. SQL review chưa cung cấp trigger cho toàn bộ vòng đời này.
- Bản ghi cùng `report_id` có thể xuất hiện ở nhiều lần chạy; trong một lần chạy nó thuộc đúng một cụm và một họ. PK `(run_id, report_id)` và FK ghép tới họ ngăn thành viên trỏ nhầm sang cụm/lần chạy khác.
- `cluster_id` chỉ định danh trong một lần chạy. `cluster_key` là mã báo cáo nhỏ nhất trong cụm, không được xem là định danh sự cố vĩnh viễn.
- Cụm và họ có ít nhất một thành viên ở mức nghiệp vụ. SQLite FK bảo vệ hướng con → cha; điều kiện cha phải có con, khóa cụm là giá trị nhỏ nhất và tính đúng của các công thức cần được kiểm tra khi dịch vụ hoàn tất transaction của lần chạy.
- Đồ thị/ma trận tương đồng là dữ liệu trung gian tính toán, không đề xuất lưu mọi cạnh thành bảng. Không đưa ground truth, mã sự cố thật hay nhãn đánh giá vào đầu vào vận hành.

## Đủ tham số nào và nằm ở đâu?

| Công thức/khối | Dữ liệu hoặc tham số được mô hình hóa |
|---|---|
| Báo cáo `r_i` | Snapshot trong `analysis_members`: `lat, lng` = L; `observed_at` = T; `flood` = F; `urgency` = E; `people_count` = N; `vulnerability` = V; `q_score` = Q |
| LR tại biên | Năm dấu hiệu trong `reports.urgency_flags_json`; hệ số `lr_intercept, lr_coef_1..5`, thứ tự cờ, threshold trong `algorithm_configs`; phiên bản mô hình trong `reports` |
| Ánh xạ ngập | `flood_mapping_json`; nhãn/confidence gốc có thể giữ trong `reports.ai_tags`; F chuẩn hóa được lưu riêng |
| `Q_i` | `q_b0, q_b1, q_b2, corrob_radius_m, corrob_window_min`; `has_image, exact_fingerprint, n_corrob, q_score` trong snapshot |
| `G_ij`, thời gian, `C_ij` | `sigma_geo_m, tau_t_min, tau_f, tau_e` |
| `w_ij` Product/Additive | `graph_mode, alpha, beta, gamma`; alpha chỉ tham gia dạng Additive |
| Làm thưa và cộng đồng | `quantile_q, top_k, resolution, community_algorithm, random_seed`; theta thực tế theo dữ liệu ở `analysis_runs.actual_theta` |
| Họ bằng chứng | `near_distance_m, near_time_min, near_f_abs, near_e_abs, near_n_floor, near_n_relative, near_v_abs, near_q_abs`; hai cờ ràng buộc thêm về nhóm nguồn/trạng thái ảnh được lưu tường minh |
| Clipping và tổng hợp | `n_ref, n_claim_cap, v_cap`; kết quả `e_agg, f_agg, n_norm, v_agg` trong `clusters` |
| Ưu tiên `P(c)` | `omega_e, omega_f, omega_n, mu, v_scale`; kết quả `priority_score` trong `clusters` |
| Tái lập | `formula_version`, cấu hình cố định, `input_revision, code_version`, thời gian chạy và snapshot |

[example-config.json](example-config.json) cung cấp một bộ giá trị minh họa đầy đủ, đối chiếu từ công thức báo cáo, policy trong mã và model JSON. Đây là dữ liệu kiểm tra thiết kế, không phải kết quả thực nghiệm mới. Product dùng `tau_t=60`, `tau_e=0.35` theo báo cáo/cấu hình phân cụm, không lấy nhầm default của `SimilarityParamsV2`. Tham số alpha được lưu cho nhánh Additive nhưng không hoạt động trong Product; bộ ví dụ này không phải cấu hình Additive tối ưu đã được tái lập.

## Phân biệt hiện tại và đề xuất

Đối chiếu nguồn hiện tại: [architecture.tex](../../chapters/03-system/sections/architecture.tex) và [storage.py](../../../products/be/storage.py). `sources.json` giữ SHA-256 của các nguồn đã dùng.

Backend hiện có bảy bảng: `reports`, `teams`, `operators`, `report_events`, `sessions`, `messages_dedup`, `server_meta`. DDL hiện tại chưa khai báo các FK quan hệ này; phần lớn liên hệ được ứng dụng kiểm tra. Kết quả phân cụm hiện được cache trong RAM. Adapter hiện chưa đọc trực tiếp `E_i` mà app gửi.

PDM đề xuất giữ toàn bộ **tên cột và kiểu dữ liệu** của bảy bảng trên; bổ sung các trường đầu vào, các FK/CHECK và sáu bảng `sources`, `algorithm_configs`, `analysis_runs`, `clusters`, `evidence_families`, `analysis_members`. Có siết một số điều kiện NULL/domain khi thiết kế. Vì vậy đây **không phải migration có thể áp dụng ngay** lên dữ liệu cũ.

CDM/LDM tập trung vào nghiệp vụ và đường phân tích. Ba bảng kỹ thuật `sessions`, `messages_dedup`, `server_meta` chỉ xuất hiện khi triển khai PDM. LDM dùng nhóm thuộc tính/kiểu ghép để trình bày; PDM mở rộng thành từng cột vật lý. Chọn gộp thành viên cụm và thành viên họ vào `analysis_members` vì mỗi báo cáo trong lần chạy đầy đủ thuộc một họ của một cụm.

## Tệp kỹ thuật và kiểm tra

- [schema.sql](schema.sql): DDL đề xuất, chỉ thực thi trong SQLite `:memory:` khi dựng hình; không mở DB backend.
- [data-dictionary.md](data-dictionary.md): từ điển cột sinh trực tiếp từ DDL.
- [validation.json](validation.json): số hộp/quan hệ, kiểm hình học và kiểm ràng buộc SQL; điểm cắt khác với đoạn chồng nhau được đếm riêng.
- [initial-state.json](initial-state.json): trạng thái và hash trước khi tạo hình; dùng để xác nhận PDF báo cáo, chỉnh sửa dashboard sẵn có và bộ mẫu không đổi.
- [sources.json](sources.json): hash tài liệu/mã nguồn làm căn cứ.

Các kiểm tra SQL có dữ liệu giả riêng trong RAM: PK ghép không nhận hai thành viên cho cùng báo cáo/lần chạy; FK ghép không nhận họ khác cụm; snapshot không nhận E thiếu; Q không vượt miền; trọng số ưu tiên có tổng một. Dữ liệu kiểm tra được rollback. Đây là kiểm tra cấu trúc, không thay thế kiểm chứng công thức hay thực nghiệm hệ thống.

Dựng lại từ gốc repository:

```bash
report/build/visual-env/bin/python -m pip install -r report/diagram-revisions/2026-10-29-data-models-review/requirements.txt
report/build/visual-env/bin/python report/diagram-revisions/2026-10-29-data-models-review/scripts/build.py
```

Cần `pdfunite` để ghép PDF review; font DejaVu Serif hoặc `fontconfig` để tìm font. Không cần gọi các generator của báo cáo hay `make content`. Khi sửa bằng Draw.io, xuất lại PDF từ chính Draw.io để xem thay đổi; chạy lại script Python sẽ tạo lại bố cục từ định nghĩa trong script.
