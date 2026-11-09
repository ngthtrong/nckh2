# P04 bổ sung — CPU_ONLY / C5 PARTIAL

Đã hoàn tất 2.304 test inference (clean+8×256) và3validation smoke,0failure. Exact ONNX app asset/seed1024 pruning/split/config được xác minh; clean parity đạt trước degraded. Có predictions.csv, metrics.csv, paired-effects.csv32rows, variant-manifest.csv2304rows và mã băm tất cả biến thể. Không sửa test/model/production runner hoặc artifact cũ. Dữ liệu PNG nặng ở derived/, được .gitignore riêng, không force-add.

Script: `run_cpu.py clean`, rồi `run_cpu.py degraded` chỉ khi gatePASS, rồi `run_cpu.py summarize`; dùng Python của venv trong preflight. Clean/degraded/summarize từ chối ghi đè prediction stage; tái lập ở một thư mục run mới với ROOT/OUT tương ứng, không ghi đè run này. `write_handoff.py` chỉ sinh phân tích từ raw đã lưu. Requirements pin, command log/.exit, environment/protocol/source-hashes/result-hashes đi kèm. Có independent read-only review bootstrap/group/ordinal/gate từ native worker; không dùng như external scientific validation.

Kết quả và CI đầy đủ ở analysis.md. ONNX CPU có suy giảm chất lượng, không dùng dữ liệu này để chọn lại model/threshold. C5 PARTIAL vì chưa Android/PTE hoặc ảnh camera độc lập; không giữ trạng thái NOT_RUN cho toàn bộ P04 nữa. Các NOT_RUN cũ trong phase-04 vẫn là hồ sơ lịch sử, không bị sửa hồi tố.

P07 nhận bảng mới qua report/scripts/export_image_quality.py và export_results.py; generated không sửa tay. P02 nguồn/license/IAA/expert/split-at-training hash vẫn thiếu; P03 8 discrepancies vẫn OPEN; P05 E2E NOT_RUN. A3 DEFERRED_BY_USER. Build/visual receipts cuối nằm ở ../report-checks và README followup, không tái dùng freeze P08 cũ sau khi report đã đổi.
