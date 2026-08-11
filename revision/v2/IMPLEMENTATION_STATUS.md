# Trạng thái triển khai ISDS 2026 short paper v2

Ngày chốt cục bộ: 2026-08-11.

## Quyết định

- **Triển khai khoa học và bản thảo cục bộ: COMPLETE.**
- **Venue/date gate: PASS.** Trang chính thức ISDS 2026 đang ghi short paper
  6--8 trang và hard deadline 14/08/2026.
- **Sẵn sàng nộp chính thức: CONDITIONAL NO-GO** cho đến khi có metadata tác
  giả/funding/COI và DOI artifact bất biến theo gate đã khóa của dự án.

## Evidence bindings

- Protocol: `754cdb90a592003dbf5319535ebb476d2baebe19f07a67eaab562ba99c3f575e`.
- Implementation/environment: `c4100c5e8abd4c6cea36593c4b277a9f9e2694faf8c0da377188e9fa6b00e0c5`.
- Calibration selection: `8f390f1969bafee5c6aed760332128a421da24b5e11282394e4f7c7eeb1f45da`.
- Confirmation result: `a7497eaa80d8d7260cc12a603a2240364184b04574260dee2bc685ead7333cf8`.
- Confirmation analysis: `60550c2b09295928ed3c27113a4ca8955f12228e4b64d0af5432ca9cf9b33ffb`.
- Generated TeX results: `942a46345de39bef80373b09a204d047832b500139eadfbf098aeb83475d44cf`.

Manifest có trạng thái `accepted`, `coverage_complete=true`: 40 master seeds,
40 ID + 40 OOD datasets, 320 clustering rows, 480 priority rows, 4,800 stress
rows và 1,680 predicted-cluster dispatch rows. Oracle dispatch được lưu ở
diagnostic artifact riêng và không tham gia inference/reporting.

## Kết quả phải giữ nguyên trong bài

- Product không thắng Additive: chênh lệch ARI là `-0.172` ID và `-0.100`
  OOD; OOD có thêm `4.11` false destinations/100 reports.
- Revised priority thấp hơn Legacy theo mean NDCG@5 ở cả ID và OOD, và không
  tạo lợi thế nhất quán trước các baseline đơn giản mạnh.
- Exact-duplicate score drift bằng 0 trên toàn bộ 40 ID + 40 OOD datasets,
  nhưng coordinated high-confidence nonincident campaign đạt false-priority
  lift tối đa `1.0` trong mọi seed.
- Predicted-cluster dispatch không đạt benefit gate; nearest-first tốt hơn
  revised về harm và deadline trong các headline comparisons.
- External/real-world/Vietnamese-transfer/deployment claims đều bị khóa.

## Publication QA

- `paper/short.pdf` và `paper/main.pdf`: đúng 8 trang LNCS/CCIS.
- Abstract: 161 từ; references: 17; đúng một figure và hai tables.
- XeLaTeX/BibTeX: không undefined citation/reference; không overfull/underfull.
- Hai PDF có cùng extracted-text SHA-256:
  `b5633b8a5f7d1a410c426a83d973409d103b4c1720af9a77fb8ed82e3495f803`.
- V2 tests: `150 passed`.
- `python -m demo.v2.reproduce reproduce_core`: PASS; analysis và generated
  TeX khớp byte, không gọi seed/oracle/restricted data.
- Full repository: `389 passed`, `41 subtests passed`, `3 failed` do legacy
  submission lock thiếu file Git-tracked
  `loop/revision/claim-selectors.json`; không phải regression v2.

## Submission blockers ngoài code

1. Thay `Anonymous Authors`/`Anonymous for review` theo chính sách submission;
   xác nhận author order, affiliations, funding và competing interests.
2. Tạo immutable artifact release/Zenodo DOI, kiểm tra DOI resolve và ghi DOI
   vào bản nộp nếu venue yêu cầu.
3. Quyết định xử lý legacy submission lock; không tự tạo claim selectors chỉ
   để làm test xanh.
4. Git-review rồi track/commit có chủ đích toàn bộ v2 files và generated
   evidence cần nộp.

`paper/generated/revision_results.tex` là evidence cũ, không được include hoặc
trích số cho short paper v2. Canonical entrypoint hiện là `paper/main.tex`, trỏ
tới toàn bộ nội dung trong `paper/short.tex`.
