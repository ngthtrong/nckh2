from pathlib import Path
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
initial=json.loads((OUT.parent/'run-baseline/input-hashes.json').read_text())
allowed={
'report/README.md','report/Makefile','report/bibliography/articles.bib','report/bibliography/legal.bib',
'report/chapters/introduction.tex','report/chapters/conclusion.tex',
'report/chapters/02-data-methods/sections/methods.tex','report/chapters/02-data-methods/sections/scope.tex','report/chapters/02-data-methods/sections/data.tex','report/chapters/02-data-methods/sections/image-design.tex','report/chapters/02-data-methods/sections/evaluation-design.tex',
'report/chapters/03-system/sections/architecture.tex','report/chapters/04-evaluation/sections/results.tex','report/chapters/04-evaluation/sections/setup.tex','report/chapters/04-evaluation/sections/limitations.tex','report/chapters/04-evaluation/sections/system-tests.tex',
'report/frontmatter/research-body-vi.tex','report/frontmatter/research-body-en.tex','report/deliverables/content/bulletin-vi.tex','report/deliverables/content/bulletin-en.tex',
'report/generated/README.md','report/generated/provenance.json','report/main.pdf','report/build/content/content.pdf','report/build/content-twoside/content.pdf','report/build/bulletin-vi/bulletin-vi.pdf','report/build/bulletin-en/bulletin-en.pdf','report/build/summary-vi/summary-vi.pdf','report/build/summary-en/summary-en.pdf',
'docs/revision-plan/README.md','docs/revision-plan/05-traceability-matrix.md'}
user_allowed={'tmp.md'}  # Explicit user reply: Co, giu tep hien tai.
changed=[];unexpected=[];user_changes=[];same=0
for name,expected in initial.items():
 p=ROOT/name
 actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
 if actual==expected:same+=1
 else:
  row={'path':name,'before':expected,'after':actual};changed.append(row)
  if name in user_allowed:user_changes.append(row)
  elif name not in allowed:unexpected.append(row)
result={'baseline_entries':len(initial),'unchanged':same,'authorized_changed':len(changed)-len(unexpected)-len(user_changes),'user_confirmed_changes':user_changes,'changes':changed,'unexpected_changes':unexpected,'HEAD_initial':(OUT.parent/'run-baseline/head.txt').read_text().strip(),'HEAD_final':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'scope':'byte comparison for all baseline files, including preexisting dirty/untracked files and deletions. No commit/push/reset. New run outputs are separately inventoried.'}
(OUT/'preservation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print({k:v for k,v in result.items() if k not in ['changes','unexpected_changes','scope']});print('unexpected',len(unexpected))
raise SystemExit(bool(unexpected or result['HEAD_initial']!=result['HEAD_final']))
