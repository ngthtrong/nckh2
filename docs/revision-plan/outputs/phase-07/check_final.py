from pathlib import Path
import subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT/'docs/revision-plan/outputs/phase-08'
records=[]
commands=[('check',['make','-C','report','check']),('check-twoside',['python3','report/scripts/check_report.py','--build-dir','build/content-twoside']),('float-content',['python3','report/scripts/check_float_references.py','--build-dir','build/content']),('float-twoside',['python3','report/scripts/check_float_references.py','--build-dir','build/content-twoside']),('diff-check',['git','diff','--check'])]
for name,cmd in commands:
 p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True);(OUT/(name+'.log')).write_text(p.stdout+p.stderr);records.append({'name':name,'command':cmd,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
(OUT/'final-checks.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');(OUT/'float-checks.json').write_text(json.dumps([r for r in records if r['name'].startswith('float')],ensure_ascii=False,indent=2)+'\n')
# Revalidate only source receipts, not deliberately superseded report checkpoint outputs.
coverage=[]
for phase in ['phase-02','phase-03','phase-05','phase-06']:
 p=OUT.parent/phase/'source-hashes.json';h=json.loads(p.read_text());mismatch=[]
 for name,expected in h.items():
  q=ROOT/name;actual=hashlib.sha256(q.read_bytes()).hexdigest() if q.is_file() else None
  if actual!=expected:mismatch.append({'path':name,'expected':expected,'actual':actual})
 coverage.append({'phase':phase,'input_hashes':len(h),'mismatches':mismatch})
(OUT/'input-receipt-validation.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n');print([(r['name'],r['exit']) for r in records]);print('Source receipt mismatches',[(r['phase'],len(r['mismatches'])) for r in coverage]);raise SystemExit(any(r['exit'] for r in records) or any(r['mismatches'] for r in coverage))
