## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: validate
- Origin Date: 2026-11-08, Asia/Taipei
- Verification Status: ANALYZED
- Version Label: rq2_precision_followup_v1

## Kết quả

**8 sai lệch vẫn OPEN: chưa tìm được artifact seed-level chưa làm tròn.** Không sửa số lịch sử, tăng tolerance, chạy lại generator/ranking/clustering hoặc coi giá trị khôi phục theo công thức là dữ liệu gốc. Lần kiểm này là phân tích provenance và replay thống kê, không phải thí nghiệm RQ2 mới.

Đã thu hẹp 8 trường thành **3 raw p Spearman và 5 Holm phát sinh từ ba raw p đó**. Cả **15/15** giá trị Holm alignment lịch sử tự nhất quán khi tính lại từ chính các raw p đã lưu với family ba endpoint cho từng comparator. Không có bằng chứng về một lỗi độc lập trong phép hiệu chỉnh Holm. Giữa các trường replay, 22/30 khớp và 8/30 tiếp tục sai lệch ở tolerance cũ `atol=1e-12, rtol=1e-7`.

| Comparator | Endpoint/trường | Đã lưu | Replay từ CSV đã làm tròn | Disposition |
|---|---|---:|---:|---|
| legacy_raw | Spearman raw p | 0.1832767116 | 0.1767384788 | OPEN; cần vector chưa làm tròn hoặc vector rank gốc |
| legacy_raw | Spearman Holm | 0.5498301348 | 0.5302154363 | OPEN; kế thừa raw p Spearman |
| simple_linear | NDCG@5 Holm | 0.2313981927 | 0.2382354410 | OPEN; kế thừa raw p Spearman trong cùng family |
| simple_linear | Spearman raw p | 0.07713273091 | 0.07941181367 | OPEN; cần vector chưa làm tròn hoặc vector rank gốc |
| simple_linear | Spearman Holm | 0.2313981927 | 0.2382354410 | OPEN; kế thừa raw p Spearman |
| simple_linear | Top-5 overlap Holm | 0.2350254284 | 0.2382354410 | OPEN; kế thừa raw p Spearman trong cùng family |
| urgency_only | Spearman raw p | 0.01612501014 | 0.01526683839 | OPEN; cần vector chưa làm tròn hoặc vector rank gốc |
| urgency_only | Spearman Holm | 0.04837503042 | 0.04580051516 | OPEN; kế thừa raw p Spearman |

## Bằng chứng trực tiếp và giới hạn

Hai notebook đã executed tính comparison trên DataFrame trong bộ nhớ rồi mới xuất `rq2_rank_alignment_test.csv` và `rq2_paired_comparisons.csv` bằng `float_format='%.10g'`. Cell 6 của notebook ngoài và cell 8 của notebook trong `rq2_results` lưu hash CSV/plot và phần đầu bảng summary; không có 240 vector seed-level full precision trong output. Như vậy input được export có mất độ chính xác, nhưng bản ghi này **chưa đủ chứng minh toàn bộ sai lệch p do làm tròn**.

Replay cho thấy thống kê W Spearman thay đổi `311 → 309.5` ở legacy và `278.5 → 279.5` ở simple-linear. Urgency giữ W=231 nhưng p khác; các chênh lệch trị tuyệt đối hiện tại không có tie, nên SciPy 1.16.3 `method='auto'` đi nhánh exact. Code SciPy cục bộ chuyển sang asymptotic khi có tie ở n=40. Chưa có rank/tie của input trước export để xác minh nhánh mà lần chạy gốc đã dùng.

`rank-diagnostics.json` có phép kiểm nhạy cảm xuất lại dữ liệu hiện tại với chín chữ số có nghĩa. Nó cho thấy p/W có thể thay đổi khi độ chính xác lưu thay đổi. Đây chỉ là sensitivity diagnostic; **không phải dữ liệu full precision được khôi phục, không thay thế kết quả gốc và không đóng discrepancy**. Không chọn mức làm tròn nhằm tái tạo p thuận lợi.

Không thay đổi phân loại theo ngưỡng Holm 0.05 giữa hai bộ số ở những trường này; điều đó không xóa sai lệch số và không chứng minh lợi ích xếp hạng tổng quát. NDCG@5 so với random và các kết luận RQ2 trước đó không được cập nhật từ kiểm tra này.

## Phạm vi tìm kiếm

`recovery-search.json` ghi toàn bộ refs hiện có, các đường dẫn RQ2 lịch sử và reachable Git objects khớp RQ2/priority_robustness/candidate_v4. Trong lịch sử reachable chỉ có **một blob cho CSV rank alignment** và **một blob cho CSV paired comparison**; chúng là bản đang dùng, không tìm được biến thể chưa làm tròn. Hai notebook được đọc cả source lẫn danh mục output. Tìm tên có giới hạn trong `/tmp` và `/home/ngthtrong` (sâu bốn cấp) không tìm được candidate ZIP/raw RQ2 bổ sung; không coi đây là tìm mọi backup trên mọi máy/tài khoản. Search Drive, nếu có ở phiên chính, phải dùng receipt riêng; script này không khẳng định đã đọc Drive.

## Kiểm thực chạy

Command:

```bash
report/build/revision-rq2-env/bin/python docs/revision-plan/outputs/phase-03/followup-20261108/diagnose.py
```

Exit 0; NumPy 2.0.2, pandas 2.2.2, SciPy 1.16.3. Exit 0 xác nhận hoàn thành audit và bảo toàn hash, **không** xác nhận cả 8 discrepancy đã giải quyết. `validation.json`, `comparison-checks.json`, `disposition.csv`, `holm-lineage.json`, `rank-diagnostics.json` và `source-hashes.json` lưu chi tiết. Source/raw/notebook gốc giữ nguyên byte. Không sửa LaTeX nên không build PDF trong tác vụ độc lập này.

Fallacy scan 11/11 trong phạm vi lần kiểm: Simpson/ecological/Berkson/collider/base-rate/regression-to-mean/survivorship/reverse-causality không được suy diễn từ audit p-value; không chuyển seed thành event độc lập; look-elsewhere và forking-paths được kiểm soát bằng family/tolerance cũ và giữ cả tám lỗi; không suy causal precision mechanism khi thiếu input trước export. Không phải audit mới về mọi claim của nghiên cứu.

## Bàn giao P07

Đề nghị bổ sung nếu cần: “Tám sai lệch được truy về ba phép kiểm Spearman và năm p hiệu chỉnh Holm phụ thuộc; phép hiệu chỉnh Holm từ raw p lịch sử tự nhất quán. Chưa có vector trước khi xuất CSV để xác định rank/tie gốc, nên tiếp tục giữ riêng số lịch sử và replay, chưa đóng các sai lệch.”

Để đóng: lấy bản dump float64/full precision của bảng alignment trước `to_csv`, hoặc các paired difference/rank vectors và metadata của lần chạy gốc, nối được với bundle/hash/notebook. Không tự sinh lại dữ liệu hoặc gọi dump tái dựng là artifact lịch sử. C4 tiếp tục PARTIAL.
