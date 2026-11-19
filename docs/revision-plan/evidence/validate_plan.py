#!/usr/bin/env python3
"""Validate planning coverage and preservation, without building the report."""
from pathlib import Path
from urllib.parse import unquote
import hashlib
import json
import re
import subprocess
import sys

PLAN = Path(__file__).resolve().parent.parent
ROOT = PLAN.parent.parent


def main():
    errors = []
    expected = {f'{letter}{i}' for letter, limit in [('A',5),('B',5),('C',7),('D',3)] for i in range(1,limit+1)}
    docs = ['README.md','00-repository-audit.md','01-review-matrix.md','02-experiment-gap-analysis.md',
            '03-immediate-fixes.md','04-phase-roadmap.md','05-traceability-matrix.md']
    for name in docs:
        if not (PLAN/name).is_file(): errors.append(f'missing {name}')
    counts = {}
    for name in ['01-review-matrix.md','05-traceability-matrix.md']:
        ids = re.findall(r'^\| ([ABCD]\d) \|',(PLAN/name).read_text(),re.M)
        counts[name] = len(ids)
        if set(ids) != expected or len(ids) != 20: errors.append(f'{name}: incomplete or duplicate IDs')
    matrix = (PLAN/'01-review-matrix.md').read_text()
    for line in matrix.splitlines():
        if re.match(r'^\| [ABCD]\d \|',line) and len(line.split('|'))-2 != 11:
            errors.append('review matrix: expected 11 fields: '+line[:20])
    prompts = {}
    for i in range(9):
        p = PLAN/f'prompts/phase-{i:02}.md'
        if not p.is_file(): errors.append(f'missing {p.name}');continue
        s=p.read_text(); headings=re.findall(r'^## ([A-H])\.',s,re.M)
        if headings!=list('ABCDEFGH'):errors.append(f'{p.name}: missing or repeated A-H sections')
        for marker in ['/home/ngthtrong/nckh2','THS2026-68','A3','sau','handoff']:
            if marker not in s: errors.append(f'{p.name}: missing context marker {marker}')
        tasks=re.findall(rf'\*\*(P{i:02}\.\d{{2}}):\*\*',s)
        if len(tasks)<4:errors.append(f'{p.name}: tasks too sparse')
        if any('\u0900'<=c<='\u097f' for c in s):errors.append(f'{p.name}: unexpected script')
        prompts[p.name]={'sections':headings,'tasks':tasks,'words':len(s.split())}
    all_tasks={t for v in prompts.values() for t in v['tasks']}
    for task in re.findall(r'P\d{2}\.\d{2}',(PLAN/'05-traceability-matrix.md').read_text()):
        if task not in all_tasks:errors.append(f'traceability unknown task {task}')
    local_links=0
    for p in PLAN.rglob('*.md'):
        s=p.read_text()
        for n,line in enumerate(s.splitlines(),1):
            if line.rstrip()!=line:errors.append(f'{p.relative_to(PLAN)}:{n}: trailing whitespace')
        for target in re.findall(r'\]\(([^)]+)\)',s):
            if '://' in target or target.startswith('#'):continue
            q=unquote(target.strip('<>').split('#')[0])
            if q and not (p.parent/q).exists(): errors.append(f'{p.relative_to(PLAN)}: broken link {target}')
            local_links+=1
    snap=json.loads((PLAN/'evidence/audit-snapshot.json').read_text())
    protected={**snap['preexisting_dirty_files'],**snap['preexisting_untracked_files']}
    changed=[]
    for name,expected_hash in protected.items():
        p=ROOT/name
        actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        if actual!=expected_hash:changed.append(name)
    if changed:errors.append('pre-existing file changes: '+repr(changed))
    now=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True)
    # The initial collector stripped the first leading status-column space.
    # Normalize outer spaces; file preservation is independently checked by hash.
    def outside(text):return sorted(line.strip() for line in text.splitlines() if 'docs/revision-plan/' not in line)
    status_same=outside(now)==outside(snap['initial_git_status'])
    if not status_same:errors.append('git status outside plan differs from initial snapshot')
    # Artifact integrity checks were collected read-only, not a statistics replay.
    manifest_checks=[r for m in snap['rq_manifests'].values() for r in m['checks']]
    checks={'plan_docs':len(docs),'review_ids':counts,'prompts':prompts,'local_links_checked':local_links,
            'preexisting_files_protected':len(protected),'preexisting_files_changed':changed,
            'git_status_outside_plan_unchanged':status_same,
            'source_hashes_match':all(v['expected']==v['actual'] for v in snap['report_source_hashes'].values()),
            'manifest_checks':len(manifest_checks),'manifest_checks_match':all(r['match'] for r in manifest_checks),
            'phone_truth_and_metrics_match':all(r['truth_ids_match'] and r['metrics_match'] for r in snap['phone_runs']),
            'full_statistics_replay':'NOT_RUN; see audit tooling/version limitations',
            'errors':errors,'pass':not errors}
    dest=PLAN/'evidence/plan-validation.json'
    dest.write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in checks.items() if k!='prompts'},ensure_ascii=False))
    raise SystemExit(bool(errors))


if __name__=='__main__':main()
