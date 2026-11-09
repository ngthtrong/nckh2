# P03 — bàn giao RQ

Đã đọc handoff01/02 và giữ phạm vi code/model/dữ liệu. HEAD/dirty baseline ../run-baseline; input-hashes trong source-hashes.json; output-hashes.json chốt source/PDF P03. P07 sẽ đổi summary/conclusion và source nhận tiếp, làm hash checkpoint stale có chủ ý.

Đầu ra thực: protocol.json, source-hashes.json, statistics.csv949hàng, rq-claims.csv, analysis.md, condition-analysis.md, comparison-checks.json, discrepancies.json, validation.txt; reanalyze.py/verify_stress.py và helper lịch sử trích từ commit a6be3e9; package pin/commands logs. Thống kê3584checks,3576khớp,8sai lệch RQ2. Không gọi exit0 của harness là mọi kiểm đều PASS.

RQ1:9baseline ARI contrasts replay khớp; primary/replication stress mỗi300bootstrap rows kiểm qua hàm verifier chỉ đọc, checkpoints/mapping/summary/source inventory được kiểm. Original full base verifier vẫn FAILED vì benchmark CSV thiếu final LF; record-equality với commit gốc được chứng minh. Không sửa CSV để pass. Path adapter chỉ src→thucnghiem trong output riêng, không đổi source gốc.

RQ2:3rawp Spearman và5Holm chưa khớp; kiểm lại exact original env2.0.2/2.2.2/1.16.3 vẫn cùng sai lệch. Không nguyên nhân phiên bản; precision/tie là giả thuyết chưa cô lập. Giữ original/replay riêng, không tăng tolerance để xóa lỗi. Mean/CI và NDCG contrasts chính khớp; chưa general benefit, exact-invariance chỉ grouping cố định, coordinated attacks bất lợi.

RQ3:40seed sau trung bình3resource scenarios,14endpoint/fixed contrast; adverse nearest-first harm/deadline được giữ. Harm Δ−69,8846, deadline−17,7083đpt; historical CSV deadline Holm1,174528414e−6 (đã sửa prose từ1,3e−6). Không n120, không field rescue outcome.

Report sửa results.tex, evaluation-design.tex, limitations.tex: trả lời từngRQ, CI/family/n/scope và sai lệch. Generated số gốc không đổi tay; không train/generate/cluster/infer mới. Script chỉ đọc các giá trị đã lưu. RQ3 env2.5.1/3.0.3/1.18.0; protocol khai tolerance và bootstrap seeds.

Commands/exit: environment-install/pin logs và .exit; verify-stress.exit0 cho independent stress replay (first full-base failure giữ riêng); reanalysis.exit0 nhưng8discrepancies; rq2-version-check.exit0; summarize.exit0 (lượt đầu thiếu tabulate đã thay bằng formatting chuẩn, không thêm dependency); build-content.exit/check.exit cho LaTeX. PDF text lưu; visual cuối P07. Build/check không scientific acceptance.

C4 PARTIAL: đã giải trình/kiểm phần lớn,8numeric discrepancies chưa giải quyết. P04/P05 quyết định có điều kiện; P06 feasibility. P07 đồng bộ kết luận/tóm tắt theo rq-claims, không gọi Product superiority/ranking benefit. A3 hoãn; A1 giữ.

Layout note: check đầu phát hiện cụm CSV/checkpoint quá dài; đã đổi cách viết thành bảng CSV và checkpoint, rebuild và check lại. Không giảm font/lề.

Phạm vi stress chính xác: mỗi bundle có 300 hàng hiệu ứng, gồm 288 CI bootstrap không rỗng được replay và 12 hàng n=0 được kiểm tra giữ trống. Tổng hai bundle: 576 CI tính lại và 24 hàng trống được kiểm.
