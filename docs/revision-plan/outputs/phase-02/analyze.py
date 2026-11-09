"""Read-only analysis of existing image/LR/phone artifacts; output here only."""
from pathlib import Path
import csv,json,hashlib,math,statistics,sys
from collections import Counter,defaultdict
ROOT=Path(__file__).resolve().parents[4]; OUT=Path(__file__).resolve().parent
sources={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 p=ROOT/p;sources[str(p.relative_to(ROOT))]=sha(p)
 return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def js(p):
 p=ROOT/p;sources[str(p.relative_to(ROOT))]=sha(p);return json.loads(p.read_text())
def write(name,rows):
 with (OUT/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def quant(xs,p):
 xs=sorted(xs);x=(len(xs)-1)*p;i=int(x);return xs[i]+(xs[min(i+1,len(xs)-1)]-xs[i])*(x-i)
snap=js('docs/revision-plan/evidence/audit-execution-20261107.json');sp='products/fe/model/Edge Ai/split_train_val_test_mobilenetv3_large.csv';split=read(sp)
assert sha(ROOT/sp)==snap['images']['split_sha256']; assert not snap['images']['missing'] and not snap['images']['md5_mismatch']
meta=snap['images']['headers'];assert len(meta)==1702
profiles=[]
for st in ['all','train','val','test']:
 for label in ['all','low','medium','high','non_flood']:
  rr=[r for r in meta if (st=='all' or r['split']==st) and (label=='all' or r['label']==label)]
  if not rr:continue
  row={'split':st,'class':label,'n':len(rr),'formats':json.dumps(dict(Counter(r['format'] for r in rr)),sort_keys=True),'modes':json.dumps(dict(Counter(r['mode'] for r in rr)),sort_keys=True)}
  for name,fn in [('width',lambda r:r['width']),('height',lambda r:r['height']),('ratio',lambda r:r['width']/r['height']),('bytes',lambda r:r['bytes'])]:
   xs=[fn(r) for r in rr]
   for q in [0,.25,.5,.75,.95,1]:row[f'{name}_q{int(100*q)}']=quant(xs,q)
  profiles.append(row)
write('image-profile.csv',profiles)
base='products/fe/model/urgency_ei/'; model=js(base+'model/urgency_logistic_SOURCE_FINAL.json');lr=read(base+'data/urgency_training_SOURCE_FINAL.csv');lr_bytes=(ROOT/(base+'data/urgency_training_SOURCE_FINAL.csv')).read_bytes()
lineage={'raw_sha256':hashlib.sha256(lr_bytes).hexdigest(),'model_expected_sha256':model['dataset_sha256'],'CRLF_reconstruction_sha256':hashlib.sha256(lr_bytes.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')).hexdigest(),'disposition':'RAW_BYTE_MISMATCH; original hash reproduced by CRLF reconstruction only; algebra below independently evaluates current table, no exact training-byte certificate'}
assert lineage['CRLF_reconstruction_sha256']==model['dataset_sha256']
(OUT/'lr-hash-discrepancy.json').write_text(json.dumps(lineage,indent=2)+'\n')
rr=[]; bycount=defaultdict(list)
for r in lr:
 n=sum(int(r[k]) for k in model['feature_order']);score=1/(1+math.exp(-model['intercept']-sum(model['coefficients'][k]*int(r[k]) for k in model['feature_order'])));truth=int(r['urgency_label']);pred=int(score>=model['threshold']);assert truth==int(n>0)==pred;bycount[n].append(score)
 rr.append({'profile_id':r['profile_id'],'flags_count':n,'OR_label':int(n>0),'synthetic_label':truth,'LR_score':score,'LR_label':pred,'match':True,'evaluation':'full enumerated state fidelity, not generalization'})
assert len(rr)==32 and sum(r['synthetic_label'] for r in rr)==31
assert all(max(v)-min(v)<1e-12 for v in bycount.values());write('lr-audit.csv',rr)
sanity=read(base+'audits/03_model_sanity_10_rounds_unique_profiles.csv');write('lr-sanity-audit.csv',sanity)
comp=[];errors=[];checks=[];labels=['low','medium','high','non_flood'];sev={'non_flood':0,'low':1,'medium':2,'high':3}
for sub in ['pth_onnx_pte','fp32_ptq_qat','prunning_st']:
 prefix=f'products/fe/reports/seed1024/{sub}/';s=js(prefix+'summary.json');rows=read(prefix+'all_predictions.csv');assert len(rows)==256
 assert s['metadata']['split_csv_sha256']==sha(ROOT/sp)
 testtruth={r['relative_path'].replace('\\','/'):r['label'] for r in split if r['split']=='test'}
 paths={r['image_path'].replace('\\','/').split('Dataset_Flood/')[-1]:r['ground_truth'] for r in rows};assert paths==testtruth
 for name,m in s['classification_metrics'].items():
  cm=[[sum(r['ground_truth']==a and r['pred_'+name]==b for r in rows) for b in labels] for a in labels]
  acc=sum(cm[i][i] for i in range(4))/256;f1=sum(2*cm[i][i]/(sum(cm[i])+sum(v[i] for v in cm)) for i in range(4))/4;hi=cm[2][2]/sum(cm[2]);critical=sum(abs(sev[r['ground_truth']]-sev[r['pred_'+name]])>=2 for r in rows)
  lat=[float(r['latency_ms_'+name]) for r in rows];match=cm==m['confusion_matrix'] and abs(acc-m['accuracy'])<1e-12 and abs(f1-m['macro_f1'])<1e-12 and critical==m['critical_error_count'] and abs(statistics.median(lat)-m['latency_ms_median'])<1e-8;assert match,(sub,name)
  suffix=m['file'].replace('\\','/').split('/Edge Ai/')[-1];paths=[ROOT/'products/fe/model/Edge Ai'/suffix, ROOT/'products/fe/model/Edge Ai/seed1024'/suffix]
  # Exports moved to explicit seed1024 directories; map by recorded hash, never filename alone.
  candidates=[p for p in (ROOT/'products/fe/model/Edge Ai').rglob('*') if p.is_file() and p.suffix in ['.onnx','.pte','.pth','.pt'] and p.stat().st_size==m['bytes']]
  matched=[str(p.relative_to(ROOT)) for p in candidates if sha(p)==m['sha256']]
  for p in matched:sources[p]=m['sha256']
  comp.append({'bundle':sub,'model':name,'seed':1024,'n_test':256,'accuracy':acc,'macro_f1':f1,'high_recall':hi,'critical_errors':critical,'bytes':m['bytes'],'MiB':m['bytes']/2**20,'median_CPU_predict_ms':statistics.median(lat),'p95_CPU_predict_ms':quant(lat,.95),'summary_match':match,'model_hash':m['sha256'],'matching_local_artifacts':';'.join(matched),'confusion_matrix':json.dumps(cm),'source':prefix+'all_predictions.csv'})
  for a in labels:
   for b in labels:
    if a!=b and cm[labels.index(a)][labels.index(b)]:errors.append({'bundle':sub,'model':name,'truth':a,'prediction':b,'count':cm[labels.index(a)][labels.index(b)],'ordinal_distance':abs(sev[a]-sev[b]),'direction':'under' if sev[b]<sev[a] else 'over','critical':abs(sev[a]-sev[b])>=2})
write('compression-audit.csv',comp);write('error-counts.csv',errors)
phone=[]
for p in snap['phone_runs']:
 assert p['metrics_match'] and p['truth_ids_match'] and p['complete'] and p['failed']==0
 assert sha(ROOT/p['path'])==p['sha256'];sources[p['path']]=p['sha256'];o=json.loads((ROOT/p['path']).read_text());summary=read('report/generated/phone-benchmarks/summary.csv')
 matches=[r for r in summary if r['source_json']==p['path']];assert len(matches)==1 and matches[0]['source_sha256']==p['sha256']
 phone.append({'source':p['path'],'sha256':p['sha256'],'seed':p['seed'],'runtime':p['runtime'],'n':p['samples'],'accuracy_recomputed':p['accuracy_recomputed'],'macro_f1_recomputed':p['macro_f1_recomputed'],'truth_ids_match':True,'summary_hash_match':True,'APK_hash':'UNKNOWN','independent_images':256})
write('phone-audit.csv',phone)
write('measurement-scopes.csv',[
 {'scope':'CPU predict','source':'seed1024/*/all_predictions.csv','unit':'256 test images per runtime','timing':'predict only; excludes decode/preprocess/load','status':'RECOMPUTED','limits':'one saved session; same scope and bundle only for speedup'},
 {'scope':'Android classifyImage','source':'seed159,1024/mobile/**/*.json','unit':'32 sessions; 256 shared test images; 4 devices','timing':'decode + preprocess + inference, excludes package read','status':'32 RAW VERIFIED','limits':'8192 repeated predictions not independent images; APK/thermal/repeats unknown'},
 {'scope':'Server clustering','source':'RQ CSV/checkpoints','unit':'40 run/seed pairs','timing':'server clustering distinct from on-device inference','status':'P03','limits':'simulated batch analysis'},
 {'scope':'Proxy transmission PC','source':'thuc_nghiem_nq/experiment_weak_network/results/20261005-102040/weak_network.csv','unit':'2313 requests, 257 validation images x3 modes x3 profiles','timing':'proxy transfer/request','status':'RAW_PRESENT','limits':'not cell; no Flutter/model/adaptive policy'},
 {'scope':'Android UI and service E2E','source':'report setup/system-tests narrative','unit':'2 reported runs x9 cases, service/UI/dashboard scopes','timing':'case includes waits/manual/observations','status':'REPORTED_UNVERIFIED_RAW','limits':'missing raw/log/APK; Case8 failure retained'},
 {'scope':'Web E2E','source':'thuc_nghiem_nq/experiment_e2e/RESULTS.md','unit':'2 reported runs; seeded DB not app-created reports','timing':'desktop web','status':'REPORTED_UNVERIFIED_RAW','limits':'no native mobile AI or real SMS'}])
(OUT/'source-hashes.json').write_text(json.dumps(sources,indent=2,ensure_ascii=False)+'\n')
(OUT/'validation.json').write_text(json.dumps({'image_headers':len(meta),'image_groups':len(profiles),'LR_profiles':len(lr),'LR_fidelity':1,'sanity_recalls':[float(r['recall_on_unseen_positive_profiles']) for r in sanity],'compression_variants':len(comp),'phone_runs_verified':len(phone),'training_or_inference':False,'python':sys.version},indent=2)+'\n')
print('P02 verified',len(meta),'headers',len(comp),'model metrics',len(phone),'phone runs')
