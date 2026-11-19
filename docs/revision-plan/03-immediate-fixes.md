# Những nội dung có thể chỉnh sửa ngay

Đây là backlog thực thi sau audit, **chưa sửa báo cáo trong phiên này**. “Tự động” nghĩa Agent có thể xử lý từ bằng chứng hiện có, không nghĩa nội dung khoa học đã được cơ quan chuyên môn chấp thuận. Không gộp nhận xét “đã giải thích hạn chế” với “đã hoàn thành thực nghiệm”.

| Tác vụ | Nhận xét | Sửa bằng chứng nào, ở đâu | Có thể tự làm? | Điều kiện nghiệm thu nội bộ |
|---|---|---|---|---|
| I01 — Chỉnh luồng E_i | B3/C3 | `rescue_record_payload.dart` gửi E_i, `cluster_service.py:130` không đọc; sửa đúng đoạn trong methods/results/architecture và research-body nếu đang khẳng định đã dùng | Có, sửa mô tả; không tự đổi server | Phân biệt computed/sent/stored/consumed; không còn claim LR đã tham gia rank nếu chưa có code/test |
| I02 — Đối chiếu cam kết NLP | B1/B4 | DOCX mục 12–16, audit 20 refs; scope.tex/introduction | Có | Đánh dấu một phần/chưa chứng minh, free-text keyword ≠ trained NLP; không lấy LR làm kết quả thay thế hoàn thành DistilBERT |
| I03 — Giải thích tích hợp | B3/B5 | Luồng ảnh→F, description→heuristic E, L/T/N/V→graph/score | Có | Có sơ đồ runtime theo code, không learned fusion; no-go ablation ghi rõ |
| I04 — Hồ sơ dataset | C1 | data.tex đã mô tả clean/split; notebook/split hiện có; thêm data card | Có phần có nguồn | Đủ 1.702/1.189/257/256; no overlap theo MD5/group; URL/license/IAA/source-group còn thiếu phải ghi unknown |
| I05 — Đặc điểm ảnh | C2 | audit-snapshot images.headers: width/height/bytes/format/mode; bảng theo split/lớp | Có, chỉ thống kê | Số mẫu khớp split; JPEG/PNG/WEBP/AVIF đúng magic header, phân biệt đuôi tên và format; không cần chạy inference |
| I06 — Giải thích PTQ/QAT/pruning | B2 | seed1024 summary/prediction, tables generated hiện có | Có, tái phân tích nhẹ | Có byte/Accuracy/F1/high-recall/lỗi nặng/CPU timing; giữ QAT kém, chưa phán nguyên nhân; speedup cùng scope |
| I07 — LR và OR baseline | C3/C7 | 32-state data, coefficient JSON, audit/source mapping | Có, dùng ngôn ngữ thận trọng | 31:1, threshold0.5, hệ số đối xứng, score theo số cờ, OR baseline chính xác; không clinical/NLP claim |
| I08 — Phân biệt căn cứ chuyên môn | C7 | registry/mapping/IITT overview, heuristic constants và sensitivity có sẵn | Có phần đã kiểm; PDF từng dấu hiệu cần đọc thêm | Căn cứ dấu hiệu khác căn cứ dispatch weights; IITT facility ≠ policy cứu hộ; source/adaptation/unknown rõ |
| I09 — Kết luận RQ1 | C4 | paired comparisons, stress primary; results/discussion/conclusion | Có | Additive .9191 và Product .9072, Holm .2560; copy5x suy giảm; không nói Product vượt toàn diện |
| I10 — Kết luận RQ2 | C4 | oracle ranking rows, robustness, sensitivity | Có | Revised NDCG .6669 < random .6763 về point estimate; không bảo vệ kết quả bằng câu “chống mọi tin giả”; tách bất biến score/graph |
| I11 — Kết luận RQ3 | C4 | bảng 40-seed paired, effect direction | Có | Revised kém nearest-first trên harm/deadline; không n=120; CI/test/family đúng; không outcome cứu hộ thực |
| I12 — Phân tầng benchmark | C6 | raw phone32, proxy2313, E2E narrative/raw thiếu | Có | Có scope PC predict/phone classifyImage/server/proxy/manual UI; không cộng n; E2E reported nhưng raw chưa xác minh |
| I13 — Sửa tóm tắt/kết luận quá mạnh | B1–4/C3–7 | Từ claim ledger, đồng bộ Vietnamese/English bodies và shared deliverable sources | Có sau P01–03 | Mỗi lợi ích gắn domain/metric; bỏ claim “hỗ trợ đắc lực/hoàn chỉnh” nếu thiếu evidence, không bịa hiệu quả |
| I14 — Future Work D1 | D1 | conclusion: IP/Wi-Fi/network-assisted location | Có, viết đề xuất | IP không mặc định hơn GPS; Wi-Fi cần reference/infrastructure; nêu uncertainty/privacy; không thêm tọa độ giả |
| I15 — Future Work D2 | D2 | conclusion: audio/ASR tiếng Việt/confirmation | Có, viết đề xuất | Nêu tiếng ồn/khẩn cấp/latency và xác nhận; chưa có speech result |
| I16 — Future Work D3 | D3 | conclusion/limitations: complete outage và không điện thoại | Có, viết đề xuất | Store≠deliver; SMS cần cell; DTN cần relay/contact; báo hộ/hotline/đội cơ động là hướng triển khai, không chức năng đã đo |
| I17 — Hình thức | A2/A4/A5 | Giữ RULES và layout patch đang có; chỉ sửa trang phát sinh sau nội dung | Có sau P07 | Build/check/PDF hai mặt và deliverables; giữ figure detail, không giảm font/lề hoặc ghi số tay |
| I18 — Công bố | A1 | Sửa provenance trước, chốt trạng thái sau nguồn cấp bài | Tự tìm nguồn được; không tự quyết trạng thái mâu thuẫn | Publication register giữ xác nhận cũ và giới hạn nguồn mới; không lấy artifact DOI hoặc dự kiến print làm xác nhận riêng bài |
| I19 — Ảnh chủ nhiệm | A3 | Giữ nguyên placeholder theo chỉ đạo bổ sung | Không làm, người dùng thêm sau | `DEFERRED_BY_USER`, không yêu cầu ảnh và không chặn các phase hiện tại |
| I20 — Hồ sơ cũ | B1/B2/C1/C6 | `docs/nghiem-thu/doi_chieu_thuyet_minh.md`, `report/generated/README.md`, CLAUDE.md có số/path cũ | Có thể lập bảng drift; chỉ cập nhật doc liên quan ở P07 | Không sửa hồi tố ghi chép lịch sử thành kết quả mới; ghi snapshot/timeline và path mapping hiện tại |

## Việc cần dữ liệu/thông tin ngoài các artifact đang có

- **A1:** DOI/chapter URL, acceptance/proceedings evidence hoặc xác nhận phạm vi online/print nếu nguồn hiện có vẫn chưa đủ; người dùng không phải gửi lại dữ liệu đã tìm thấy trong repo.
- **Raw Android/web E2E:** nguồn file từ máy thực nghiệm/backup đã có quyền truy cập; nếu không có, giữ reported/unverified và chuẩn bị protocol tối thiểu. Chưa cần xin chạy lại cả campaign.
- **C1/C7:** URL/license từng ảnh, người gán/IAA và xác nhận chuyên gia chỉ thêm khi có bản ghi thật. Không đoán từ filename hoặc registry.
- **C5:** cần exact model và Android khi muốn kết luận on-device robustness; thiếu device không ngăn P01–03/P07, nhưng không thể đóng C5 bằng số mobile.
- **A3:** chủ động hoãn theo người dùng; không tìm ảnh hoặc nhắc cung cấp ảnh trong các phase này.

## Đề xuất câu kết luận theo bằng chứng (cần tích hợp ở phase sau)

Hệ thống hiện là nguyên mẫu xử lý ảnh ở biên và tích hợp các trường dữ liệu/heuristic ở máy chủ. Chưa có bằng chứng triển khai mô hình hiểu văn bản cứu hộ tiếng Việt hoặc mô hình fusion học chung. LR có cấu trúc tái hiện nhãn tham chiếu OR của nhóm; điểm này chưa được adapter hiện tại dùng làm `ReportV2.E`. Các thực nghiệm mô phỏng cho thấy cả khả năng và thất bại của clustering/ranking, chưa xác lập ưu thế chung hoặc hiệu quả cứu hộ thực địa. Các hướng D1–D3 được đề xuất nghiên cứu, có điều kiện hạ tầng và truyền tin cụ thể.
