from pathlib import Path
import subprocess,json,csv,os,zipfile,tarfile,hashlib
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
areas=['experiment_mobile','experiment_mobile_e2e','experiment_e2e']
refs=subprocess.check_output(['git','for-each-ref','--format=%(refname:short)','refs/heads','refs/remotes/origin'],cwd=ROOT,text=True).splitlines();hits=[]
# Current refs plus path history commits of the runners/results.
commits=subprocess.check_output(['git','log','--all','--format=%H','--','products/fe/experiment_mobile','thuc_nghiem_nq/experiment_mobile_e2e','thuc_nghiem_nq/experiment_e2e'],cwd=ROOT,text=True).splitlines()
for ref in dict.fromkeys(refs+commits):
 names=subprocess.check_output(['git','ls-tree','-r','--name-only',ref],cwd=ROOT,text=True).splitlines()
 for name in names:
  if any(a in name for a in areas) and any('/'+d+'/' in name for d in ['results','logs','checkpoints']) and name.endswith(('.json','.csv','.txt','.png','.jpg')):
   hits.append({'ref':ref,'path':name})
archives=[]
for top in ['products','thuc_nghiem_nq','thucnghiem','resource','docs']:
 for base,dirs,names in os.walk(ROOT/top):
  dirs[:]=[d for d in dirs if d not in ['.venv','venv','node_modules','.git','.agents','Dataset_Flood','outputs','build']]
  for n in names:
   p=Path(base)/n
   if n.endswith(('.zip','.tar','.tar.gz','.tgz')):
    item={'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'matches':[]}
    try:
     if zipfile.is_zipfile(p):
      with zipfile.ZipFile(p) as z:item['matches']=[x for x in z.namelist() if any(a in x for a in areas) and any('/'+d+'/' in x for d in ['results','logs','checkpoints'])]
     else:
      with tarfile.open(p) as z:item['matches']=[x.name for x in z if any(a in x.name for a in areas) and any('/'+d+'/' in x.name for d in ['results','logs','checkpoints'])]
    except Exception as e:item['error']=str(e)
    archives.append(item)
local=[]
for rel in ['products/fe/experiment_mobile','thuc_nghiem_nq/experiment_mobile_e2e','thuc_nghiem_nq/experiment_e2e']:
 p=ROOT/rel
 for q in p.rglob('*') if p.exists() else []:
  if q.is_file() and any(d in q.parts for d in ['results','logs','checkpoints']):local.append(str(q.relative_to(ROOT)))
result={'refs_searched':refs,'path_history_commits_searched':list(dict.fromkeys(commits)),'git_raw_hits':hits,'local_raw_files':local,'archives':archives,'scope':'local authorized workspace, available refs/history and archive directory listings; no fetch/checkout/shared DB/device/message actions','connected_external_backups':'not identified; no claim about all machines/accounts'}
(OUT/'recovery-search.json').write_text(json.dumps(result,indent=2)+'\n');print({k:(len(v) if isinstance(v,list) else v) for k,v in result.items() if k not in ['archives']});print('archives inspected',len(archives))
