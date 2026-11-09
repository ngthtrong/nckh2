"""Run authorized report builds/checks sequentially and preserve command receipts."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent / 'report-checks'
OUT.mkdir(exist_ok=True)
commands = [
    ('content', ['make', '-C', 'report', 'content']),
    ('content-twoside', ['make', '-C', 'report', 'content-twoside']),
    ('deliverables', ['make', '-C', 'report', 'deliverables']),
    ('check', ['make', '-C', 'report', 'check']),
    ('check-twoside', ['python3', 'report/scripts/check_report.py', '--build-dir', 'build/content-twoside']),
    ('float-content', ['python3', 'report/scripts/check_float_references.py', '--build-dir', 'build/content']),
    ('float-twoside', ['python3', 'report/scripts/check_float_references.py', '--build-dir', 'build/content-twoside']),
    ('diff-check', ['git', 'diff', '--check']),
]
records = []
for name, command in commands:
    print('START', name, flush=True)
    start = datetime.now(ZoneInfo('Asia/Taipei')).isoformat()
    with (OUT / (name + '.log')).open('w') as stream:
        proc = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    records.append(dict(name=name, command=command, exit=proc.returncode, started_at=start,
                        ended_at=datetime.now(ZoneInfo('Asia/Taipei')).isoformat(), log=name + '.log'))
    (OUT / 'commands.json').write_text(json.dumps(records, indent=2) + '\n')
    print('END', name, proc.returncode, flush=True)
    if proc.returncode:
        raise SystemExit(proc.returncode)
