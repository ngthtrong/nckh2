"""Append manual/dashboard failures to a separate, deduplicated evidence CSV."""
import csv
import hashlib
import json

FIELDS = ['ma_ghi_nhan', 'thoi_diem_utc', 'ten_benchmark', 'run', 'thiet_bi', 'case',
          'hang_muc', 'trang_thai', 'ket_qua_mong_doi', 'loi_thuc_te', 'id_bao_cao', 'tep_bang_chung']
CASES = {
    'manual_android_ui': ('7', 'Giao diện Android', 'Gửi bài, Lịch sử và dashboard hiển thị đúng nội dung/ảnh/trạng thái'),
    'manual_physical_network': ('8', 'Tắt/bật mạng thật', 'Giữ hàng đợi khi mất mạng; phục hồi nhận đúng một bài và hết pending'),
    'dashboard': ('9', 'Dashboard', 'Kiểm tra dashboard đúng các bài của benchmark và tất cả kiểm tra đạt'),
}


def save_manual_errors(destination, record, gold_run, dashboard=None):
    evidence = record.get('evidence', {})
    events = list(evidence.get('manualChecks', []))
    for previous in evidence.get('attemptHistory', []):
        events.extend(previous.get('evidence', {}).get('manualChecks', []))
    if dashboard and dashboard.get('status') == 'FAIL':
        digest = hashlib.sha256(json.dumps(dashboard, sort_keys=True).encode()).hexdigest()
        events.append({'id': 'dashboard-'+digest, 'stage': 'dashboard', 'status': 'FAIL',
                       'atUtc': dashboard.get('atUtc', record['recordedAtUtc']),
                       'detail': '; '.join(c['detail'] for c in dashboard.get('checks', []) if c['status'] == 'FAIL'),
                       'evidenceFile': 'dashboard-checks.json / dashboard-screenshots/'})
    path = destination/'loi_thu_cong.csv'
    seen = set()
    if path.exists():
        with path.open(encoding='utf-8-sig', newline='') as stream:
            seen = {r['ma_ghi_nhan'] for r in csv.DictReader(stream)}
    rows = []
    for event in events:
        if event.get('stage') not in CASES or event.get('status') != 'FAIL' or not event.get('detail', '').strip():
            continue
        identity = str(event.get('id', ''))
        if not identity or identity in seen:
            continue
        number, title, expected = CASES[event['stage']]
        rows.append(dict(zip(FIELDS, [identity, event.get('atUtc', record['recordedAtUtc']), record['sessionId'],
                    gold_run, record.get('environment', {}).get('device', {}).get('model', 'unknown'),
                    number, title, 'FAIL', expected, event['detail'], event.get('reportId', ''), event.get('evidenceFile', '')])))
        seen.add(identity)
    # Excel must display user notes as text, including notes starting with a formula marker.
    def cell(value):
        text = str(value)
        return "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) else text
    new = not path.exists()
    with path.open('a', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        if new:
            writer.writeheader()
        writer.writerows({k: cell(v) for k, v in row.items()} for row in rows)
