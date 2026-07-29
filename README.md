# Product-Similarity Clustering and Bounded Priority Heuristics

Kho lưu trữ này chứa mã nguồn, protocol, artifact và bản thảo cho một nghiên
cứu phương pháp về gom nhóm báo cáo cứu hộ lũ và xếp hạng ưu tiên. Đánh giá
hiện tại dùng dữ liệu **synthetic** được sinh theo protocol đã khóa. Đây không
phải là bằng chứng triển khai ngoài hiện trường, không xác nhận hiệu quả cứu hộ
thực tế và không thay thế đánh giá của chuyên gia.

Pipeline nghiên cứu gồm:

1. biểu diễn báo cáo bằng thuộc tính quan sát được;
2. xây dựng đồ thị với product similarity không gian--thời gian--ngữ cảnh;
3. phân cụm báo cáo thành các incident candidate;
4. tính bounded, duplicate-aware priority heuristic;
5. đánh giá clustering, robustness và dispatch bằng latent synthetic truth.

Các trọng số và ngưỡng priority là lựa chọn minh họa trong protocol, không phải
policy đã được cơ quan cứu hộ phê duyệt.

## Trạng thái revision và các gate

Revision hiện dùng chuỗi khóa sau:

| Mốc | Nội dung được khóa | Bản ghi có thẩm quyền |
|---|---|---|
| Gate 1 | Method contract, generator/schema, dữ liệu synthetic và môi trường | [`revision/gate1-lock.json`](revision/gate1-lock.json) |
| Gate 2 | Calibration protocol, cấu hình được chọn và thời điểm mở test split | [`revision/gate2-lock.json`](revision/gate2-lock.json) |
| X0 | Một complete held-out evaluation đã được cấp quyền và thực thi | [`revision/x0-release.json`](revision/x0-release.json) |
| Gate 3 | Accepted held-out run, recomputation, coverage và rejected-run ledger | [`revision/gate3-lock.json`](revision/gate3-lock.json) |
| G0 | Transactional promotion thành nguồn số liệu duy nhất cho manuscript | [`revision/result-lock.json`](revision/result-lock.json) |
| Gate 4 | Clean-room, claim/PDF audit và khóa submission cục bộ | [`revision/final-audit.md`](revision/final-audit.md) |

X0 đã hoàn tất và đã được Gate 3/G0 khóa. **Không chạy lại X0** trong quy trình
tái lập submission. Một X0 mới chỉ hợp lệ sau khi reopen các gate liên quan
theo đúng `reopen_conditions` trong lock; không được chạy lại để tìm kết quả
thuận lợi hơn.

## Nguồn sự thật đã promote

Mọi số thực nghiệm trong [`paper/main.tex`](paper/main.tex) phải đi qua
`\RevisionClaim{...}`. Chuỗi nguồn tương ứng là:

- [`revision/result-lock.json`](revision/result-lock.json): danh mục artifact
  đã promote cùng checksum;
- [`loop/revision/claim-selectors.json`](loop/revision/claim-selectors.json):
  catalog claim máy đọc được;
- [`paper/generated/revision_results.tex`](paper/generated/revision_results.tex):
  macro LaTeX sinh cơ học từ catalog;
- [`loop/revision/traceability.md`](loop/revision/traceability.md): hợp đồng
  truy vết và mandatory adverse disclosures;
- [`demo/results/tables/exp23_heldout_summary.json`](demo/results/tables/exp23_heldout_summary.json)
  và
  [`demo/results/tables/exp23_heldout_evaluation.json.gz`](demo/results/tables/exp23_heldout_evaluation.json.gz):
  summary cùng complete held-out archive;
- [`demo/results/tables/exp22_runtime_repro.json`](demo/results/tables/exp22_runtime_repro.json),
  [`demo/results/tables/data_distribution_report_v4.json`](demo/results/tables/data_distribution_report_v4.json)
  và
  [`demo/results/tables/data_quality_summary_v4.json`](demo/results/tables/data_quality_summary_v4.json):
  ancillary evidence được G0 ràng buộc.
- [`revision/locked-artifacts.tar.gz`](revision/locked-artifacts.tar.gz) cùng
  [`revision/artifact-package-manifest.json`](revision/artifact-package-manifest.json):
  companion package để xác minh các run manifest bị gitignore; gói không chứa
  held-out/test seed dataset và chỉ giữ một development fixture cần cho full
  clean-clone test suite.

Không chỉnh tay các file trên. Một file nằm trong `demo/results/` nhưng không
được liệt kê trong `revision/result-lock.json` không phải nguồn evidence của
revision.

## Cấu trúc hiện hành

```text
.
├── demo/
│   ├── data/                 # Synthetic generator, schema và frozen datasets
│   ├── pipeline/             # Weighting, clustering, priority và metrics
│   ├── simulation/           # Independent dispatch simulator
│   ├── protocol/             # Seed, calibration, baseline và metric contracts
│   ├── experiments/          # Revision experiments, runners và promotion code
│   ├── artifacts/runs/       # Isolated no-overwrite run directories
│   ├── results/tables/       # Promoted tables cùng historical local outputs
│   ├── environment/          # Environment capture helpers
│   └── tests/                # Unit, property, protocol và artifact tests
├── paper/
│   ├── main.tex
│   ├── references.bib
│   └── generated/revision_results.tex
├── revision/                 # Contracts, gate locks, audits và response ledger
├── loop/revision/            # Claim catalog và traceability
├── archive/                  # Pre-revision assets, không thuộc submission
├── reproduce.sh              # One-command clean-room verification
├── pyproject.toml
└── requirements.lock
```

Chi tiết riêng của workspace thực nghiệm nằm tại
[`demo/README.md`](demo/README.md).

## Môi trường

Môi trường được khóa cho **CPython 3.12**; miền tương thích chính xác nằm trong
[`pyproject.toml`](pyproject.toml). Cài đúng dependency pins từ
[`requirements.lock`](requirements.lock):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.lock
```

Không thay `requirements.lock` bằng danh sách package không pin khi kiểm tra
tái lập.

## Tái lập submission

Từ thư mục gốc của repository:

```bash
./reproduce.sh
```

Mặc định, `reproduce.sh` tạo một virtual environment tạm mới từ lock, xác minh
gói artifact và mọi checksum, chạy toàn bộ test suite, kiểm tra claim
traceability, rồi dựng và audit PDF mà không gọi candidate X0 thêm lần nào.
Profile nhanh chỉ dành cho chẩn đoán cục bộ:

```bash
./reproduce.sh --profile smoke
```

Không thay thế entrypoint này bằng một lần chạy experiment tùy ý.

Kết quả clean-room chính thức được ghi tại
[`revision/clean-room-report.md`](revision/clean-room-report.md); chi tiết máy
đọc được nằm trong
[`revision/clean-room-verification.json`](revision/clean-room-verification.json).
Toàn bộ stdout/stderr của lượt chạy chính thức được lưu tại
[`revision/clean-room-full.log`](revision/clean-room-full.log).
Quyết định Gate 4 và ranh giới external-blocked nằm trong
[`revision/final-audit.md`](revision/final-audit.md); trạng thái nguồn chính xác
được khóa bằng
[`revision/submission-checksums.json`](revision/submission-checksums.json).

Yêu cầu hệ thống cho manuscript là XeLaTeX và BibTeX. Trình tự build thủ công
tương ứng là:

```bash
cd paper
xelatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

File `paper/generated/revision_results.tex` phải được giữ nguyên khi build.

## Phân biệt reproduction và mã legacy

[`demo/run_all.py`](demo/run_all.py) là integration harness của pipeline cũ.
Nó được giữ cho mục đích lịch sử/phát triển nhưng **không** phải entrypoint tái
lập revision, không tạo nguồn số liệu cho manuscript hiện tại và không được
dùng thay `./reproduce.sh`.

Các module riêng lẻ có thể dùng cho phát triển sau khi hiểu protocol, nhưng
mọi output mới chỉ là candidate artifact. Nó không trở thành evidence cho bài
báo nếu chưa đi qua gate, validation và transactional promotion.

## Phạm vi và giới hạn

- Nghiên cứu hiện chỉ được xác nhận trên dữ liệu synthetic đã khóa.
- Chưa có dữ liệu cứu hộ thật đủ quyền sử dụng và incident-level annotation.
- Chưa có expert panel xác nhận policy weights, caps hoặc operational utility.
- Dispatch là mô phỏng với latent outcomes độc lập, không phải thử nghiệm hiện
  trường.
- Runtime benchmark kiểm tra exact candidate pruning nhưng vẫn dùng dense
  compatibility storage; repository không tuyên bố implementation fully sparse.
- Tên/thứ tự tác giả, affiliation/contact, ORCID, funding và
  competing-interest declarations chưa được phê duyệt; manuscript dùng
  placeholder thay vì tự suy đoán.
- Public repository URL, DOI và release authority là external submission
  actions, không được suy đoán trong tài liệu.

## Nhóm nghiên cứu

- Giảng viên hướng dẫn: TS. Nguyễn Thanh Khoa
- Chủ nhiệm: Lê Thị Ngọc Ảnh
- Thành viên: Nguyễn Thanh Trọng, Cao Tường Hưng, Nguyễn Như Quỳnh, Ngô Hưng Thịnh

Đơn vị: Trường Công nghệ Thông tin và Truyền thông, Đại học Cần Thơ.

Danh sách nhóm repository này không phải thứ tự tác giả đã được phê duyệt cho
submission; author block chính thức vẫn là đầu vào external-blocked.
