from pathlib import Path
import csv,json,hashlib,re,subprocess
from collections import Counter
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent;BASE=OUT.parent
pdfs=json.loads((BASE/'phase-07/pdf-inspection.json').read_text());assert (BASE/'phase-07/layout-review.md').is_file()
records=[
('A1','OPEN','phase-07/publication-verification.md','frontmatter/research-body-vi/en.tex','Giữ published theo xác nhận nhóm, thêm provenance và giới hạn cấp bài','Tìm exact title/nguồn ISDS/Springer, đối chiếu title và tám tác giả','Chưa có chapter DOI/online date/pages/volume/year','Bổ sung minh chứng cấp bài, không suy từ metadata quyển'),
('A2','DONE_WITH_EVIDENCE','phase-07/layout-review.md','PDF hai bản và nguồn float','Giữ nền layout; kiểm lại toàn quyển bằng thumbnail và phần đổi chi tiết','Build/check, page overview và visual checklist','Khoảng trống biểu mẫu/kết thúc chương có chủ đích','Rà lại khi nội dung đổi'),
('A3','DEFERRED_BY_USER','phase-01/claim-ledger.csv','template/forms.tex; principal-investigator.tex','Giữ nguyên placeholder theo chỉ đạo','Hash StudentPhoto/forms không đổi trong preservation','Ảnh chưa thêm','Người dùng thêm sau, không chặn'),
('A4','DONE_WITH_EVIDENCE','phase-08/float-checks.json','labels/captions/LoF/LoT hai variants','Đánh số tự động; bảng metadata mới có caption/label/ref','Float checker hai bản:48 hình/38 bảng','Không xác nhận hồ sơ nghiệm thu','Chạy lại khi thêm hình/bảng'),
('A5','DONE_WITH_EVIDENCE','phase-07/commands.json','RULES và sáu PDF','Build và kiểm source/PDF/log/font/visual','content/content-twoside/deliverables/check và diff đều đạt','Placeholder hành chính còn; không release approval','Hoàn thiện hồ sơ thật khi nộp chính thức'),
('B1','PARTIAL','phase-01/scope-register.md','scope/introduction/conclusion/research-body','Công khai NLP chưa chứng minh hoàn thành, LR không thay cam kết','DOCX mục12–16, source và audit20refs','Chưa trained free-text NLP trong evidence hiện có','Nghiên cứu riêng hoặc bổ sung artifact thật nếu tồn tại'),
('B2','DONE_WITH_EVIDENCE','phase-02/compression-audit.csv','image-design/results optimization','Tính lại12cấu hình; giải thích byte/params/timing và QAT xấu','Confusion/Accuracy/F1/high recall/critical/median/hash khớp','Chưa causal QAT diagnosis hoặc quantized Android validation','Chẩn đoán/đo thêm khi có mục tiêu mới'),
('B3','PARTIAL','phase-01/dataflow.md','methods/results/architecture/research-body','Luồng computed→sent→stored, adapter chưa consumed E_LR','Đọc score/payload/storage/to_report_v2/core','Khoảng trống nối E_i; chưa learned fusion','Chỉ tích hợp code theo nhiệm vụ riêng sau xác nhận semantics'),
('B4','PARTIAL','phase-01/claim-ledger.csv','scope/conclusion/research-body','Phân biệt tiếp nhận mô tả/keywords với trained NLP','Source/code và cam kết DOCX','Đóng góp NLP/fusion chưa được đo','Không gán surrogate thành NLP; giữ gap'),
('B5','DEFERRED_WITH_REASON','phase-06/no-go.md','scope/conclusion limitations','NO_GO image/text/both vì target/paired gold chưa đủ','eligibility.csv10gates; kiểm source label lineage','Chưa thực hiện ablation','Định nghĩa common target/paired data/gold trước GO_PROTOCOL'),
('C1','PARTIAL','phase-02/data-card.md','data/evaluation-design/setup','Data card/split/counts/source unknown minh bạch','1702header/MD5; split1189/257/256, no recorded group overlap','URL/license/IAA/source-event independence và train-split lineage chưa đủ','Thu hồi provenance và đánh giá độc lập có thẩm quyền'),
('C2','DONE_WITH_EVIDENCE','phase-02/image-profile.csv','data table image-profile','Thống kê20nhóm header theo lớp/split, phân vị kích thước/tỷ lệ/byte','Format/mode từ header, tổng1702khớp split','Không phải robustness evaluation','Dùng profile làm đầu vào protocol ảnh, không suy nhận diện'),
('C3','PARTIAL','phase-02/lr-audit.csv','methods/results LR','OR32states,31:1,threshold/hệ số/count equivalence và sanity failures','Tính score JSON, đối chiếu32profiles; lr-hash-discrepancy.json','Raw byte lineage mismatch CRLF; chưa expert/clinical và chưa backend consumption','Giữ surrogate scope; giải quyết lineage/integration ở task riêng'),
('C4','PARTIAL','phase-03/validation.txt','results RQ1–3/evaluation-design/limitations','Trả lời RQ và giữ kết quả âm; replay949rows,3584numericchecks','3576khớp; RQ1stress576CI+24empty; RQ3n40','8RQ2rawp/Holm discrepancies còn; original full base check final-LF failed','Thu hồi unrounded metrics/tie handling; không sửa số để pass'),
('C5','OPEN','phase-04/NOT_RUN.md','limitations/conclusion','Không claim robustness khi chưa chạy inference','Model/split/preprocess preflight;9validationderivedinputs,0predictions','Chưa clean/degraded performance hoặc Android sessions','Runtime/clean parity/device gate trước thí nghiệm'),
('C6','PARTIAL','phase-05/provenance-audit.csv','setup/system-tests/limitations','32phoneJSON verified; E2E raw chưa khôi phục, giữ Case8FAIL','Recovery20refs/5historycommits/local/Drive; package check0','APK hash/repeats/thermal/E2E raw và SMS delivery thiếu','Khôi phục raw; nếu cần dùng isolated one-device plan'),
('C7','PARTIAL','phase-02/criterion-source-map.csv','methods/conclusion','Ánh xạ IITT/VN Điều26 có phạm vi; numerical weights vẫn heuristic','WHO official poster/reference; luật scannedp1/23/24 đã xem','Chưa chuyên gia xác nhận dispatch policy; không full legal/clinical conformance','Expert-led target/weights validation trước thí điểm'),
('D1','DONE_WITH_EVIDENCE','phase-01/future-work.md','conclusion Future Work','Định vị đa nguồn có nguồn/thời điểm/uncertainty, IP không mặc định hơn GPS','Đọc source/PDF; proposed-only','Chưa triển khai hoặc đo positioning mới','Protocol định vị và quyền riêng tư khi có nhiệm vụ'),
('D2','DONE_WITH_EVIDENCE','phase-01/future-work.md','conclusion Future Work','Audio→ASR→trích thông tin→xác nhận; nêu rủi ro tiếng ồn/giọng/latency','Đọc source/PDF; proposed-only','Chưa model/measurement ASR','Dữ liệu/nhãn/confirmation protocol trước nghiên cứu'),
('D3','DONE_WITH_EVIDENCE','phase-01/future-work.md','conclusion Future Work','Store≠deliver; SMS/DTN phụ thuộc hạ tầng; báo hộ/hotline/đội tại chỗ','Đọc source/PDF; proposed-only','Chưa đo complete outage/no-phone workflow','Diễn tập có đơn vị chuyên môn, không hứa delivery vô điều kiện')]
rows=[]
for id,status,evidence,section,action,check,remaining,nextaction in records:
 p=BASE/evidence;assert p.is_file(),p
 rows.append({'task':id,'status':status,'evidence':str(p.relative_to(ROOT)),'evidence_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'section':section,'action':action,'check':check,'remaining':remaining,'next_action':nextaction})
assert len(rows)==20 and len({r['task'] for r in rows})==20
with (OUT/'final-review-status.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
counts=dict(Counter(r['status'] for r in rows));print('Final review',counts)
response='''# Bản nháp phản hồi nội bộ — THS2026-68

Đã sửa báo cáo và tái phân tích artifact theo yêu cầu; chưa gửi Hội đồng. Trạng thái dưới đây nói mức xử lý nhận xét, không xác nhận Hội đồng chấp thuận. D1–D3 DONE là hoàn thành nội dung đề xuất, không triển khai chức năng. Giải trình B1/B3/B4 không hoàn thành thay cam kết NLP/fusion.

'''
for r in rows:
 response+=f"## {r['task']} — {r['status']}\n\nĐã xử lý: {r['action']}. Vị trí: `{r['section']}`. Kiểm chứng: {r['check']}.\n\nBằng chứng: `{r['evidence']}` (SHA-256 trong final-review-status.csv). Giới hạn: {r['remaining']}. Bước tiếp: {r['next_action']}.\n\n"
(OUT/'response-draft.md').write_text(response)
repro='''# Hồ sơ tái lập và giới hạn

HEAD không đổi; trạng thái bẩn ban đầu, hash5.347mục và source-copy ở ../run-baseline. Không commit/push/reset hoặc xóa raw. preservation.json ghi mọi khác biệt, gồm thay đổi tmp.md do người dùng xác nhận và yêu cầu giữ nguyên; không khôi phục tệp đó. Không kế thừa PASS từ receipt stale.

Nguồn thật: ảnh1.702file (nguồn/license/IAA/event independence còn unknown), mobile32JSON trên256ảnh lặp, proxy2.313request trên257validationảnh. Nguồn synthetic: LR32ORstates; RQ1Generator3.0 và RQ2/3Candidate4.1 riêng. E2EAndroid/Web là Reported/Unverified raw hiện tại. Không có clinical/field validation.

LR Implemented và fidelity trên bảng hiện tại; không NLP. App tính/gửi E_i, storage giữ payload, adapter chưa consume E_LR. Learned fusion và trained text chưa được chứng minh. P04 chỉ chuẩn bị9đầu vào validation,0inference; P05 không đo phiên mới; P06NO_GO. Không tạo số đo mới hoặc expert labels.

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

Environment thống kê riêng: NumPy2.5.1/pandas3.0.3/SciPy1.18.0 theo RQ3; kiểm RQ2 trong NumPy2.0.2/pandas2.2.2/SciPy1.16.3. Không cài đè visual-env/chung. Pip logs/pins lưu P03. Bootstrap: RQ1baseline10000seed20260812 theo method order; stress5000SHA-derivedseed; RQ2/35000seed20260729. Unit40run/seed, RQ3 average3conditions; không n120.

949statisticrows/3584checks:3576khớp,8discrepancies. Script exit0 không phải toàn bộ kiểm PASS. RQ1full base verifier thất bại byte equality do final LF; mọi CSV record khớp lịch sử, independent stress replay kiểm576nonemptyCI+24emptyrows. RQ2 còn3rawpSpearman/5Holm; original-version diagnostic không giải quyết, không chọn số thuận lợi. LRrawhash khác model, CRLF reconstruction khớp nhưng không certificate training bytes. File discrepancy/provenance giữ cả before/after hashes.

Generated qua exporter, thêm image-profile từ script; report không sửa generated tay. Không chạy generator Draw.io manual. Logs/check/visual/PDF hashes cuối đi kèm. Bản nháp còn placeholder hành chính và A1/các gap khoa học; không chạy check-release vì không đánh giá hồ sơ nghiệm thu chính thức.
'''
(OUT/'reproducibility.md').write_text(repro)
validation='''# Kiểm chứng cuối

Đã build/check final state theo phase-07/commands.json; float-checks.json ghi hai variants. Kiểm source/LoF/LoT/captions/refs, log/font và PDF text; visual phạm vi trong phase-07/layout-review.md. Nội dung và source/PDF hash cuối ở final-hashes.json. Các receipt P01–P03 là checkpoint, không thay receipt final sau các sửa P07.

Trạng thái20ID: '''+json.dumps(counts,ensure_ascii=False)+'''. Không gọi100%nhận xét đã khắc phục hoặc NLP/fusion đã thực nghiệm.

Những phần chưa chạy: inference robustness, new mobile/E2E/SMS/field experiments, train/tune, learned fusion/ASR/location deployment, full RQ campaign, check-release. P04/P05/P06 có disposition riêng; không PASS cho NOT_RUN.

Discrepancies khoa học/provenance:8RQ2p/Holm, LRbytehash/CRLF, RQ1final-LF; không sửa historical artifacts. A1OPEN cấp bài, A3DEFERRED_BY_USER, C5OPEN, E2Eraw chưa khôi phục. tmp.md được người dùng xác nhận chủ động xóa nội dung và yêu cầu giữ nguyên; preservation.json ghi riêng thay đổi này, không tính vào thay đổi của agent.

Các lỗi kỹ thuật đã sửa trong phiên: token canonical/đoạn heading gây hbox (sửa ngắt/cách diễn đạt, giữ font/lề); trailing blank EOF. Có một lượt P02check/text khi PDF đang build, receipt bị loại và đã kiểm lại sau build hoàn tất. Không dùng log/PDF cũ giả kiểm mới.
'''
(OUT/'validation.md').write_text(validation)
# Make current traceability explicit while retaining the historical planning table.
p=ROOT/'docs/revision-plan/05-traceability-matrix.md';s=p.read_text();s=s.replace('Tệp dưới `outputs/` là **đầu ra dự kiến**, chưa tạo hoặc thực thi trong lần lập kế hoạch.','Bảng kế hoạch dưới đây giữ snapshot P00; trạng thái thực thi mới được bổ sung ở cuối tài liệu và final-review-status.csv. Không suy mọi thí nghiệm đã chạy từ tên output dự kiến.')
marker='\n## Trạng thái thực thi sau P01–P08\n'
if marker in s:s=s.split(marker)[0]
s+=marker+'\nNguồn quyết định/check/hash cuối: [P08 ledger](outputs/phase-08/final-review-status.csv), [validation](outputs/phase-08/validation.md), [response draft](outputs/phase-08/response-draft.md).\n\n| ID | Status | Evidence | Gap / next action |\n|---|---|---|---|\n'
for r in rows:s+=f"| {r['task']} | {r['status']} | [{Path(r['evidence']).name}]({r['evidence'].replace('docs/revision-plan/','')}) | {r['remaining']}; {r['next_action']} |\n"
p.write_text(s.rstrip()+'\n')
(OUT/'handoff.md').write_text('''# Bàn giao cuối — P01–P08

Đã thực hiện P01→P02→P03, sau đó quyết định P04 NOT_RUN inference/P05 SKIP_RERUN image và NOT_RUN E2E/P06 NO_GO, tích hợp P07 và kiểm cuối P08. Không có phase nghiên cứu mới được ngầm thực hiện.

PDF chính report/main.pdf, bản hai mặt report/build/content-twoside/content.pdf; bốn bulletin/summary Việt–Anh đã dựng. Source/generated chỉ qua exporter; docs/revision-plan/outputs giữ protocol, hashes, CSV, discrepancies, handoff từng phase, raw/local visual artifacts. Danh sách thay đổi so baseline trong preservation.json, hash cuối final-hashes.json; artifact lớn giữ local theo outputs/.gitignore, không force-add.

Trạng thái nhận xét và giới hạn: final-review-status.csv; phản hồi nội bộ: response-draft.md; khả năng tái lập: reproducibility.md; lệnh/exit và visual: ../phase-07/commands.json, layout-review.md, PDF-inspection và float-checks. Build/check/visual là kiểm kỹ thuật, không scientific acceptance hay quyết định nghiệm thu.

Còn cần: minh chứng công bố cấp bài; nguồn/license/IAA/event provenance ảnh; giải quyết8discrepanciesRQ2 từ unrounded artifacts; xác nhận chuyên gia cho dispatch; runtime/device/clean parity để mở X02; khôi phục E2Eraw hoặc thực hiện isolated new run khi có điều kiện. NLP/fusion chưa chứng minh hoàn thành. B5NO_GO chỉ là feasibility. A3người dùng thêm sau, không yêu cầu ảnh trong phiên này.

Không đổi app/backend/weights/model/contracts, không train hoặc chạy lại campaign; không commit/push/gửi phản hồi. Người dùng xác nhận chủ động xóa nội dung tmp.md và yêu cầu giữ tệp hiện tại; ghi riêng trong preservation.json/validation.md. Sau bàn giao không tự chạy thêm phase.
''')
