# Hồ sơ tái lập và giới hạn

HEAD không đổi; trạng thái bẩn ban đầu, hash 5.347 mục và source-copy ở ../run-baseline. Không commit/push/reset hoặc xóa raw. preservation.json ghi mọi khác biệt, gồm thay đổi tmp.md do người dùng xác nhận và yêu cầu giữ nguyên; không khôi phục tệp đó. Không kế thừa PASS từ receipt stale.

Nguồn thật: ảnh 1.702 file (nguồn/license/IAA/event independence còn unknown), mobile 32 JSON trên 256 ảnh lặp, proxy 2.313 request trên 257 ảnh validation. Nguồn synthetic: LR 32 trạng thái OR; RQ1Generator3.0 và RQ2/3Candidate4.1 riêng. E2E Android/Web là Reported/Unverified raw hiện tại. Không có clinical/field validation.

LR Implemented và fidelity trên bảng hiện tại; không NLP. App tính/gửi E_i, storage giữ payload, adapter chưa consume E_LR. Learned fusion và trained text chưa được chứng minh. P04 chỉ chuẩn bị9 đầu vào validation,0 inference; P05 không đo phiên mới; P06 NO_GO. Không tạo số đo mới hoặc expert labels.

## Lệnh thực đã chạy

```bash
report/build/visual-env/bin/python docs/revision-plan/evidence/collect_snapshot.py audit-execution-20261107.json
report/build/visual-env/bin/python docs/revision-plan/outputs/phase-02/analyze.py
report/build/revision-stats-env/bin/python docs/revision-plan/outputs/phase-03/verify_stress.py
report/build/revision-stats-env/bin/python docs/revision-plan/outputs/phase-03/reanalyze.py
report/build/revision-rq2-env/bin/python docs/revision-plan/outputs/phase-03/rq2_version_check.py
report/build/visual-env/bin/python docs/revision-plan/outputs/phase-04/prepare_variants.py --validation-smoke
python3 products/fe/experiment_mobile/prepare_assets.py --check
python3 docs/revision-plan/outputs/phase-05/recover.py
python3 docs/revision-plan/outputs/phase-07/build_and_check.py
report/build/visual-env/bin/python docs/revision-plan/outputs/phase-07/inspect_pdfs.py
```

Các script phân tích chỉ đọc raw, ghi output riêng; revise.py P01 là script sửa nguồn có guard baseline, không chạy lại trên bản đã sửa. Snapshot collector từ chối ghi đè snapshot. Gói scientific raw không được sửa để đáp ứng hash.

Environment thống kê riêng: NumPy 2.5.1 / pandas 3.0.3 / SciPy 1.18.0 theo RQ3; kiểm RQ2 trong NumPy 2.0.2 / pandas 2.2.2 / SciPy 1.16.3. Không cài đè visual-env/chung. Pip logs/pins lưu P03. Bootstrap: RQ1 baseline: 10.000 resample, seed 20260812 theo method order; stress: 5.000 resample, seed suy từ SHA; RQ2/RQ3: 5.000 resample, seed 20260729. Đơn vị 40 run/seed, RQ3 trung bình 3 điều kiện; không n=120.

949 dòng thống kê / 3.584 kiểm tra: 3.576 khớp, 8 sai lệch. Script exit0 không phải toàn bộ kiểm PASS. RQ1full base verifier thất bại byte equality do final LF; mọi CSV record khớp lịch sử, independent stress replay kiểm576 CI không rỗng và 24 hàng trống. RQ2 còn3 raw p Spearman và 5 Holm; original-version diagnostic không giải quyết, không chọn số thuận lợi. hash raw LR khác model, CRLF reconstruction khớp nhưng không certificate training bytes. File discrepancy/provenance giữ cả before/after hashes.

Generated qua exporter, thêm image-profile từ script; report không sửa generated tay. Không chạy generator Draw.io manual. Logs/check/visual/PDF hashes cuối đi kèm. Bản nháp còn placeholder hành chính và A1/các gap khoa học; không chạy check-release vì không đánh giá hồ sơ nghiệm thu chính thức.
