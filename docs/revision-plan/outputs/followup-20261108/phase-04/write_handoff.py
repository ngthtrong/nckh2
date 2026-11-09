"""Summarize the completed CPU experiment without changing raw predictions."""
from pathlib import Path
import csv
import json

OUT=Path(__file__).resolve().parent
with (OUT/'metrics.csv').open() as stream:
    rows=list(csv.DictReader(stream))
with (OUT/'paired-effects.csv').open() as stream:
    effects=list(csv.DictReader(stream))
assert json.loads((OUT/'validation.json').read_text())['status']=='PASS_CPU_ONLY'
table=['| Điều kiện | Accuracy % | Macro-F1 % | Recall high % | Lỗi ≥2 mức |',
       '|---|---:|---:|---:|---:|']
for r in rows:
    table.append('| '+r['condition']+' | '+' | '.join(f'{100*float(r[m]):.2f}' for m in ['accuracy','macro_f1','recall_high'])+' | '+r['ordinal_error_ge2_count']+' |')
ci=['| Điều kiện | Δ macro-F1 (đpt) | CI 95% (đpt) |','|---|---:|---:|']
for r in effects:
    if r['metric']=='macro_f1':
        ci.append(f"| {r['condition']} | {100*float(r['delta_degraded_minus_clean']):+.2f} | [{100*float(r['ci_low']):+.2f}; {100*float(r['ci_high']):+.2f}] |")
passport='''## Material Passport

- Origin: academic-research-suite / experiment-agent, authorized fixed-model CPU screening.
- Date: 2026-11-08, Asia/Taipei.
- Verification status: VERIFIED for the new raw CPU measurements and structural/hash checks; not a reproduction of an Android experiment.
- Scope: CPU_ONLY_ONNX, seed1024 structured pruning; no training, model export or test tuning.
'''
limits='''## Giới hạn và trạng thái

**C5 PARTIAL / CPU_ONLY.** Không chạy Android/PTE hoặc E2E; không có thiết bị/adb/session receipt. Không suy CPU timing thành mobile. 2.304 prediction rows chỉ có 256 ảnh gốc, không phải 2.304 ảnh độc lập. Có 252 split_group (249 nhóm đơn, hai nhóm đôi, một nhóm ba); đây là đơn vị lấy mẫu lại để giữ quan hệ gần trùng, chưa chứng minh 252 nguồn/sự kiện độc lập. Tên trường `independent_unit`/`independent_images` trong receipt mô tả đơn vị phân tích, không xác nhận tính độc lập khoa học theo nguồn/sự kiện.

Nhãn gốc được kế thừa cho corruption, chưa có chuyên gia thẩm định lại tính giữ nguyên ngữ nghĩa. Mọi ảnh/condition giữ trong mẫu số; không có failure trong lần này. Ordinal non_flood=0, low=1, medium=2, high=3; lỗi nặng là lệch ≥2 mức. Không bật abstention, không chọn ngưỡng sau test; confidence và số mẫu confidence<.5 chỉ mô tả.

CI là percentile bootstrap ghép cặp theo 252 nhóm, 5.000 draw seed20261107; cùng draw cho clean và tám conditions, macro-F1 tính lại từ confusion mỗi draw. 32 CI hiệu ứng không hiệu chỉnh đa so sánh; không có p-value hoặc kết luận familywise significance. Báo đủ tám điều kiện, không chọn riêng CI loại trừ0 để kết luận robust.

Timing gồm predict và preprocess+predict riêng, CPU một luồng, một phiên/scope. Ảnh đưa vào runner là PNG không mất mát của biến đổi đã giải mã; không gồm chi phí JPEG encode, tạo biến thể, hash, load model hoặc IO benchmark package. Phiên degraded nạp lại runtime và không warmup riêng. Không dùng timing để so speedup với Android hoặc phiên lịch sử. Corruption nhân tạo không thay ảnh mưa, camera hay thử nghiệm cứu hộ thực địa.
'''
fallacies='''## Kiểm diễn giải: 11/11 loại sai lệch được rà trong scope phép bổ sung

| Loại | Disposition |
|---|---|
| Simpson | Báo riêng chín conditions và metric high; không suy xu hướng từng lớp từ macro-F1. |
| Ecological | Đơn vị là ảnh/nhóm split, không ngoại suy sang người được cứu hoặc sự kiện độc lập. |
| Berkson / selection | Bộ ảnh web có chọn lọc, source/event independence chưa biết; giữ giới hạn chuyển miền. |
| Collider | Không fit mô hình có biến điều chỉnh hay chọn nhóm theo outcome; không áp dụng trong so sánh pixel này. |
| Base rate | Giữ support test low56/medium60/high54/non_flood86; recall high không phải predictive value lâm sàng. |
| Regression to mean | Cùng toàn bộ ảnh test, không chọn ảnh cực đoan theo performance để đánh giá lại. |
| Survivorship | Đủ2304/2304 rows,0failure; không loại ảnh khó hoặc condition xấu. |
| Look elsewhere | Đủ8contrasts/4metrics và CI chưa hiệu chỉnh được công bố; không gọi significance. |
| Forking paths | Mức suy giảm khóa trong protocol cũ và trước inference mới; model cố định, không tune test. |
| Correlation / causation | Chỉ đối chiếu biến đổi pixel có kiểm soát; không suy nguyên nhân vận hành hay hiệu quả cứu hộ. |
| Reverse causality | Không có phân tích nhân quả quan sát người/sự kiện; không áp dụng cho phép biến đổi pixel đã chỉ định. |
'''
preflight='''# Preflight P04 bổ sung — CPU_ONLY

Môi trường riêng `report/build/robustness-env`, packages khóa ở requirements-lock.txt. Chỉ cài ONNX Runtime/NumPy/Pillow/SciPy trong venv mới; không cài đè môi trường báo cáo hoặc RQ.

Exact model ONNX app SHA256 `2ec932a12e4730811597d297edc4de4566cdd6b381e871bc65c658ec8d794d27` khớp structured_onnx seed1024 lịch sử. Class order [low,medium,high,non_flood], config hash và split hash khớp summary lịch sử. Kiểm đủ MD5/group/cross-split cho1702ảnh bằng helper gốc; không chia lại test. Preprocess gọi nguyên helper quantize_model.preprocess, không dùng quantize entrypoint.

Ba ảnh validation smoke chạy thành công trước test, không tune corruption. Clean256 khớp100%top1; max abs probability diff8.344650268554688e-7; allclose atol1e-5/rtol1e-4 đã khóa, không nới tolerance. Clean tensor từ PNG dẫn xuất bitwise equal với preprocess ảnh gốc.

Android/PTE vẫn NOT_RUN: không có adb/device/session/APK receipt và không thay target để tuyên bố hiệu năng Android. Xem protocol/environment/source-hashes và clean-parity.json.
'''
(OUT/'preflight.md').write_text(preflight)
analysis='# Phân tích P04 bổ sung — CPU_ONLY\n\n'+passport+'\n## Kết quả từ raw\n\n'+'\n'.join(table)+'\n\n## Chênh lệch ghép cặp với clean\n\n'+'\n'.join(ci)+'\n\n'+limits+'\n'+fallacies
(OUT/'analysis.md').write_text(analysis)
handoff='''# P04 bổ sung — CPU_ONLY / C5 PARTIAL

Đã hoàn tất 2.304 test inference (clean+8×256) và3validation smoke,0failure. Exact ONNX app asset/seed1024 pruning/split/config được xác minh; clean parity đạt trước degraded. Có predictions.csv, metrics.csv, paired-effects.csv32rows, variant-manifest.csv2304rows và mã băm tất cả biến thể. Không sửa test/model/production runner hoặc artifact cũ. Dữ liệu PNG nặng ở derived/, được .gitignore riêng, không force-add.

Script: `run_cpu.py clean`, rồi `run_cpu.py degraded` chỉ khi gatePASS, rồi `run_cpu.py summarize`; dùng Python của venv trong preflight. Clean/degraded/summarize từ chối ghi đè prediction stage; tái lập ở một thư mục run mới với ROOT/OUT tương ứng, không ghi đè run này. `write_handoff.py` chỉ sinh phân tích từ raw đã lưu. Requirements pin, command log/.exit, environment/protocol/source-hashes/result-hashes đi kèm. Có independent read-only review bootstrap/group/ordinal/gate từ native worker; không dùng như external scientific validation.

Kết quả và CI đầy đủ ở analysis.md. ONNX CPU có suy giảm chất lượng, không dùng dữ liệu này để chọn lại model/threshold. C5 PARTIAL vì chưa Android/PTE hoặc ảnh camera độc lập; không giữ trạng thái NOT_RUN cho toàn bộ P04 nữa. Các NOT_RUN cũ trong phase-04 vẫn là hồ sơ lịch sử, không bị sửa hồi tố.

P07 nhận bảng mới qua report/scripts/export_image_quality.py và export_results.py; generated không sửa tay. P02 nguồn/license/IAA/expert/split-at-training hash vẫn thiếu; P03 8 discrepancies vẫn OPEN; P05 E2E NOT_RUN. A3 DEFERRED_BY_USER. Build/visual receipts cuối nằm ở ../report-checks và README followup, không tái dùng freeze P08 cũ sau khi report đã đổi.
'''
(OUT/'handoff.md').write_text(handoff)
print('Wrote CPU preflight, analysis and handoff from raw metrics.')
