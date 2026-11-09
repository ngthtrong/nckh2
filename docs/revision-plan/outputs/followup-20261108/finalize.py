"""Freeze followup receipts; never edits original results or previous phase ledgers."""
from pathlib import Path
import difflib
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


checks={}
commands=json.loads((OUT/'report-checks/commands.json').read_text())
checks['eight_build_check_commands_exit0']=len(commands)==8 and all(r['exit']==0 for r in commands)
pdfs=json.loads((OUT/'report-checks/pdf-inspection.json').read_text())
checks['final_pdf_hashes_current']=all(sha(ROOT/v['pdf'])==v['sha256'] for k,v in pdfs.items() if k!='variant_comparison')
checks['main_pdf_alias_current']=sha(ROOT/'report/main.pdf')==sha(ROOT/'report/build/content/content.pdf')
checks['all_pdf_fonts_embedded']=all(v['all_fonts_embedded'] for k,v in pdfs.items() if k!='variant_comparison')
preservation=json.loads((OUT/'preservation.json').read_text())
checks['protected_3818_files_unchanged']=preservation['status']=='PASS' and preservation['protected_files']==3818 and not preservation['mismatches']
checks['cpu_2304_predictions']=json.loads((OUT/'phase-04/validation.json').read_text())['test_predictions']==2304
checks['clean_parity_gate_pass']=json.loads((OUT/'phase-04/clean-parity.json').read_text())['status']=='PASS_CPU_ONLY'
checks['no_decode_failures']=json.loads((OUT/'phase-04/validation.json').read_text())['failures']==0
drift=[]
for receipt in [OUT/'phase-04/source-hashes.json', OUT/'phase-04/result-hashes.json',
                OUT/'evidence/source-hashes.json', OUT.parent/'phase-03/followup-20261108/source-hashes.json']:
    for path,digest in json.loads(receipt.read_text()).items():
        if not isinstance(digest,str) or len(digest)!=64:
            continue
        p=ROOT/path
        if not p.is_file() or sha(p)!=digest:
            drift.append(dict(receipt=str(receipt.relative_to(ROOT)),path=path))
checks['evidence_source_and_result_hashes_current']=not drift
proc=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
(OUT/'report-checks/final-diff-check.log').write_text(proc.stdout+proc.stderr)
checks['final_git_diff_check_exit0']=proc.returncode==0
before=json.loads((OUT/'report-before-hashes.json').read_text())
changed=[];patch=[]
for path,digest in before.items():
    p=ROOT/path
    if p.is_file() and sha(p)!=digest:
        changed.append(path)
        old=OUT/'before'/path
        if old.is_file():
            patch.extend(difflib.unified_diff(old.read_text().splitlines(True),p.read_text().splitlines(True),
                                            fromfile='before/'+path,tofile='after/'+path))
new_report=['report/scripts/export_image_quality.py','report/generated/tables/image-quality-cpu.tex',
            'report/generated/image-quality-values.tex','report/generated/image-quality-provenance.json']
for name in new_report:
    p=ROOT/name
    assert p.is_file(),name
    changed.append(name)
    patch.extend(difflib.unified_diff([],p.read_text().splitlines(True),fromfile='/dev/null',tofile='after/'+name))
(OUT/'session-source-diff.patch').write_text(''.join(patch))
(OUT/'changed-files.json').write_text(json.dumps(changed,indent=2)+'\n')
(OUT/'git-status-after.txt').write_bytes(subprocess.check_output(['git','status','--short'],cwd=ROOT))
validation=dict(status='COMPLETE_WITH_OPEN_EVIDENCE_GAPS' if all(checks.values()) else 'FAILED_VALIDATION',
                checks=checks,input_drift=drift,phase_status={'P02':'PARTIAL','P03':'PARTIAL_8_FIELDS_OPEN',
                'P04':'CPU_ONLY_C5_PARTIAL','P05':'SKIP_RERUN_IMAGE_NOT_RUN_E2E_C6_PARTIAL',
                'P07':'INTEGRATED_BUILT_CHECKED_A1_OPEN'},A3='DEFERRED_BY_USER',
                release_approval=False,previous_P08_freeze='HISTORICAL_NOT_CURRENT')
(OUT/'final-validation.json').write_text(json.dumps(validation,indent=2)+'\n')
files=[ROOT/name for name in changed]
files += [p for p in (ROOT/'report').rglob('*') if p.is_file()
          and 'build' not in p.relative_to(ROOT/'report').parts
          and p.suffix in {'.tex','.py','.bib','.json','.cls'}]
files += [p for p in OUT.rglob('*') if p.is_file() and 'derived' not in p.parts
          and 'before' not in p.parts and 'visual' not in p.parts and p.name!='final-hashes.json']
files += [OUT.parent/'phase-03/followup-20261108/handoff.md',OUT.parent/'phase-03/followup-20261108/disposition.csv']
hashes={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(files))}
(OUT/'final-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
print(json.dumps(validation,indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
