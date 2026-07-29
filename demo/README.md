# `demo/` — Revision Experiment Workspace

Thư mục này chứa synthetic generator, implementation phương pháp, protocol,
test suite, isolated experiment runner và promoted tables cho revision. Mục
tiêu là đánh giá phương pháp trong điều kiện synthetic được kiểm soát; đây
không phải demo triển khai cứu hộ thực tế.

## Cấu trúc hiện hành

```text
demo/
├── data/                 # Generator, schema, views và frozen synthetic data
├── pipeline/             # Weighting, clustering, priority, baselines, metrics
├── simulation/           # Dispatch simulator với latent independent outcomes
├── protocol/             # Seed/calibration/baseline/metric contracts
├── experiments/          # Experiments, no-overwrite runner và promotion tools
├── artifacts/runs/       # Run directories có manifest và per-file checksum
├── results/tables/       # Promoted revision files và historical local tables
├── environment/          # Python/system/BLAS/thread environment capture
├── tests/                # Unit, property, leakage, artifact và gate tests
├── dashboard/            # Exploratory interface; không phải revision evidence
└── run_all.py            # Legacy integration harness; không dùng cho revision
```

Không suy ra trạng thái evidence chỉ từ tên hoặc vị trí của một output. Danh
mục có thẩm quyền nằm trong
[`../revision/result-lock.json`](../revision/result-lock.json).

## Lifecycle từ Gate 1 đến G0

1. **Gate 1** khóa method/data/environment contract tại
   [`../revision/gate1-lock.json`](../revision/gate1-lock.json).
2. **Gate 2** khóa calibration selections và giải phóng held-out split tại
   [`../revision/gate2-lock.json`](../revision/gate2-lock.json).
3. **X0** là complete held-out evaluation được cấp quyền đúng một lần theo
   [`../revision/x0-release.json`](../revision/x0-release.json).
4. **Gate 3** xác minh accepted run, recompute inference/selectors và giữ cả
   adverse, tied, failed cùng infeasible outcomes tại
   [`../revision/gate3-lock.json`](../revision/gate3-lock.json).
5. **G0** promote cơ học accepted evidence thành source-of-truth tại
   [`../revision/result-lock.json`](../revision/result-lock.json).

X0 đã hoàn tất. Không gọi lại candidate runner hoặc held-out evaluator trong
reproduction. Nếu một scientific defect buộc phải thay đổi method, data,
protocol hoặc result thì phải reopen gate theo lock, không chạy lại chọn lọc.

## Promoted source-of-truth

Các consumer của revision phải bắt đầu từ:

- [`../loop/revision/claim-selectors.json`](../loop/revision/claim-selectors.json):
  claim catalog;
- [`../paper/generated/revision_results.tex`](../paper/generated/revision_results.tex):
  generated `\RevisionClaim{...}` macros;
- [`../loop/revision/traceability.md`](../loop/revision/traceability.md):
  manuscript claim contract;
- [`results/tables/exp23_heldout_summary.json`](results/tables/exp23_heldout_summary.json):
  compact held-out summary;
- [`results/tables/exp23_heldout_evaluation.json.gz`](results/tables/exp23_heldout_evaluation.json.gz):
  lossless complete held-out archive;
- [`results/tables/exp23_heldout_selectors.json`](results/tables/exp23_heldout_selectors.json):
  Gate-3 base selectors;
- [`results/tables/exp22_runtime_repro.json`](results/tables/exp22_runtime_repro.json):
  runtime, memory, equivalence và packet evidence;
- [`results/tables/data_distribution_report_v4.json`](results/tables/data_distribution_report_v4.json)
  và
  [`results/tables/data_quality_summary_v4.json`](results/tables/data_quality_summary_v4.json):
  frozen data diagnostics.

Chỉ các file được `../revision/result-lock.json` liệt kê và checksum mới là
promoted evidence. Không chỉnh tay JSON, gzip archive, selector catalog hoặc
generated TeX.

## Môi trường Python

Revision yêu cầu CPython 3.12 và exact pins trong
[`../requirements.lock`](../requirements.lock). Từ repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.lock
```

Có thể chạy test không làm thay đổi promoted results:

```bash
python -m pytest -q
```

## Clean-room reproduction

Entrypoint submission nằm ở repository root:

```bash
./reproduce.sh
```

Mặc định script tạo virtual environment tạm từ dependency lock, kiểm tra gói
artifact, promoted checksums, claim resolution và toàn bộ tests, rồi dựng và
audit manuscript, sau đó xác minh final submission lock mà không thực thi X0
lần nữa. Dùng
`./reproduce.sh --profile smoke` chỉ để chẩn đoán cục bộ nhanh; submission
evidence luôn lấy từ profile `full`.

Report/transcript của một lượt final phải được ghi ra ngoài checkout. Không
`tee` vào `revision/clean-room-full.log` trong khi chạy: file đó đã nằm trong
submission manifest. Khi reseal, tích hợp evidence được sinh ra trước, tạo lại
manifest bằng `demo.experiments.lock_submission`, rồi chạy một fresh clone với
output capture ở ngoài clone.

Các manifest run bị gitignore được phục hồi/xác minh từ
[`../revision/locked-artifacts.tar.gz`](../revision/locked-artifacts.tar.gz)
theo allowlist và checksum trong
[`../revision/artifact-package-manifest.json`](../revision/artifact-package-manifest.json).
Gói companion không chứa held-out/test seed dataset; nó chỉ giữ một
development fixture cần cho full clean-clone test suite và không gọi held-out
evaluator.

Manuscript yêu cầu XeLaTeX và BibTeX:

```bash
cd paper
xelatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

## Output discipline

- Revision experiments phải ghi vào isolated
  `demo/artifacts/runs/<run_id>/`; runner từ chối ghi đè run hiện có.
- `demo/results/tables/` chứa cả promoted files và output lịch sử. Chỉ
  `revision/result-lock.json` quyết định file nào có thẩm quyền.
- Promotion là transaction có checksum qua
  [`experiments/promote_results.py`](experiments/promote_results.py), không
  phải thao tác copy hoặc sửa JSON thủ công.
- Negative, tied, adverse, failed và no-feasible outcomes không được lọc khỏi
  evidence.

## Cảnh báo về `run_all.py`

[`run_all.py`](run_all.py) là legacy harness và có thể tái sinh các bảng hoặc
dashboard không thuộc revision. Không chạy file này để:

- tái lập manuscript;
- làm mới promoted tables;
- thay thế accepted X0;
- tạo số liệu mới cho abstract, bảng hoặc kết luận.

Mọi kết quả phát triển mới phải đi qua protocol, isolated artifact runner,
validation và gate promotion trước khi được xem là publication evidence.
