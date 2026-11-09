from pathlib import Path
import subprocess,json,datetime
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
commands=[('content',['make','-C','report','content']),('content-twoside',['make','-C','report','content-twoside']),('deliverables',['make','-C','report','deliverables']),('check',['make','-C','report','check']),('check-twoside',['python3','report/scripts/check_report.py','--build-dir','build/content-twoside']),('diff-check',['git','diff','--check'])]
records=[]
for name,cmd in commands:
 started=datetime.datetime.now(ZoneInfo('Asia/Taipei')).isoformat();print('START',name,flush=True)
 with (OUT/(name+'.log')).open('w') as f:p=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
 records.append({'name':name,'command':cmd,'exit':p.returncode,'started_at':started,'finished_at':datetime.datetime.now(ZoneInfo('Asia/Taipei')).isoformat(),'log':name+'.log'})
 (OUT/'commands.json').write_text(json.dumps(records,indent=2)+'\n');print('END',name,p.returncode,flush=True)
 if p.returncode and name in ['content','content-twoside','deliverables']:raise SystemExit(p.returncode)
