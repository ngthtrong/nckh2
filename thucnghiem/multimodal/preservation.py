"""Check session baseline without treating authorized report edits as corruption."""
import difflib
import subprocess
from pathlib import Path

from common import OUT, ROOT, digest, read_json, write_json


def main():
    baseline = read_json(OUT / 'baseline-files.json')
    before = OUT / 'before'
    allowed = {str(p.relative_to(before)) for p in before.rglob('*') if p.is_file()}
    allowed |= {'report/generated/values.tex', 'report/generated/provenance.json', 'report/main.pdf'}
    changes = []
    unchanged = 0
    for i, (relative, original) in enumerate(baseline.items(), 1):
        path = ROOT / relative
        current = digest(path) if path.is_file() else None
        if current != original:
            changes.append({'path': relative, 'before': original, 'after': current, 'authorized': relative in allowed})
        else:
            unchanged += 1
        if i % 1000 == 0:
            print('Protected files checked:', i, '/', len(baseline), flush=True)
    unexpected = [r for r in changes if not r['authorized']]
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    unchanged_head = head == read_json(OUT / 'authorization.json')['head']
    write_json(OUT / 'preservation.json', {'status': 'PASS' if not unexpected and unchanged_head else 'FAIL',
                'baseline_files': len(baseline), 'unchanged': unchanged, 'authorized_changes': changes,
                'unexpected_changes': unexpected, 'head_unchanged': unchanged_head,
                'scope': 'Existing products, models, data, raw results, report source and old revision artifacts; report/build excluded'})
    patch = []
    for old in sorted(before.rglob('*')):
        if not old.is_file():
            continue
        relative = str(old.relative_to(before))
        new = ROOT / relative
        patch.extend(difflib.unified_diff(old.read_text().splitlines(True), new.read_text().splitlines(True),
                                          fromfile='a/' + relative, tofile='b/' + relative))
    (OUT / 'session-source-diff.patch').write_text(''.join(patch))
    print('Preservation:', len(baseline), 'unchanged:', unchanged, 'authorized changes:', len(changes),
          'unexpected:', len(unexpected), flush=True)
    if unexpected or not unchanged_head:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
