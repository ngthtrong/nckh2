"""Replay saved paired statistics only; never runs clustering or writes inputs."""
from pathlib import Path
import csv,json,hashlib,importlib.util,subprocess,sys
import numpy as np,pandas as pd
from scipy.stats import wilcoxon
from importlib.metadata import version
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent;RESULTS=ROOT/'thucnghiem/results'
hashes={};checks=[];stats=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frame(rel):
 p=RESULTS/rel;hashes[str(p.relative_to(ROOT))]=sha(p);return pd.read_csv(p)
def load_module(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def close(key,actual,expected,tol=1e-8):
 atol=1e-12 if ('p_value' in key or 'Holm' in key) else tol
 ok=bool(np.isclose(float(actual),float(expected),atol=atol,rtol=tol));checks.append({'key':key,'actual':float(actual),'saved':float(expected),'tolerance_abs':atol,'tolerance_rel':tol,'match':ok})
def interval(x,seed=20260729,n=5000):
 a=np.array(x);rng=np.random.default_rng(seed);v=a[rng.integers(0,len(a),size=(n,len(a)))].mean(axis=1);return np.quantile(v,[.025,.975])
def standard(rq,section,candidate,comparator,metric,direction,values,ci,p,h,family,source,saved=None):
 a=np.array(values);return {'rq':rq,'section':section,'candidate':candidate,'comparator':comparator,'metric':metric,'direction':direction,'n_independent_pairs':len(a),'oriented_mean_improvement':float(a.mean()),'ci95_low':float(ci[0]),'ci95_high':float(ci[1]),'raw_p':p,'Holm_p':h,'wins':int((a>0).sum()),'ties':int((a==0).sum()),'losses':int((a<0).sum()),'family':family,'source':source,'status':'REPLAYED_FROM_SAVED_VALUES'}
protocol={'scope':'statistical replay of saved outputs; no model/generator/clustering campaign','path_map':{'historical src/':'current thucnghiem/'},'RQ1':{'generator':'3.0','test_runs':'run_041..run_080','n':40,'primary':'rq1_results','replication':'rq1_results_v2/full kept separate','baseline_family':'9 ARI Product-vs-baseline contrasts; Holm across nine','bootstrap':'baseline comparisons 10000 resamples seed20260812 sequential selected-method order; stress5000 using SHA256-derived seeds from locked protocol','independent_unit':'run, copies/scenarios not independent'},'RQ2':{'generator':'Candidate4.1','test_seeds':'3000..3039','n':40,'grouping':'oracle evaluator grouping','family':'3 alignment endpoints per comparator; 5 robustness endpoints per scenario','bootstrap_seed':20260729,'resamples':5000,'gold':'latent benefit independent of score but synthetic, evaluator-only'},'RQ3':{'generator':'Candidate4.1','n':40,'unit':'three resource scenarios averaged within each seed','family':'14 endpoints per fixed partition policy contrast or fixed policy partition contrast','bootstrap_seed':20260729,'resamples':5000,'direction':'positive oriented mean means candidate better'},'environment':{n:version(n) for n in ['numpy','pandas','scipy']},'tolerance':'RQ1 1e-10; RQ2/3 CSV %.10g roundoff abs/relative 1e-7; any discrepancy retained'}
(OUT/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
# RQ1 selected configurations are frozen; no fits or tuning.
selected=json.loads((RESULTS/'cij_baseline_benchmark_results/selected_configs.json').read_text())['selected'];methods=list(selected);df=frame('cij_baseline_benchmark_results/benchmark_test_40runs.csv');saved=frame('cij_baseline_benchmark_results/paired_comparisons.csv').set_index('baseline');assert len(df)==400
primary=df[df.method=='product_cij_louvain'].set_index('run_id').sort_index();rng=np.random.default_rng(20260812);rows=[]
for method in methods:
 if method=='product_cij_louvain':continue
 other=df[df.method==method].set_index('run_id').sort_index();assert list(primary.index)==list(other.index);d=primary.ari.to_numpy()-other.ari.to_numpy();boot=rng.choice(d,size=(10000,len(d)),replace=True).mean(axis=1);ci=np.quantile(boot,[.025,.975]);p=float(wilcoxon(d).pvalue) if np.any(d!=0) else 1.
 row=standard('RQ1','baseline','product_cij_louvain',method,'ari','higher',d,ci,p,None,'9 ARI comparisons','cij_baseline_benchmark_results/benchmark_test_40runs.csv');rows.append(row)
 for k,v in [('mean_delta_ari',d.mean()),('ci95_low',ci[0]),('ci95_high',ci[1]),('wilcoxon_p_raw',p),('wins',(d>0).sum()),('ties',(d==0).sum()),('losses',(d<0).sum())]:close(f'RQ1 {method} {k}',v,saved.loc[method,k],1e-10)
run=0
for i,r in enumerate(sorted(rows,key=lambda x:x['raw_p'])):
 run=max(run,min(1.,(len(rows)-i)*r['raw_p']));r['Holm_p']=run;close('RQ1 Holm '+r['comparator'],run,saved.loc[r['comparator'],'wilcoxon_p_holm'],1e-10)
stats+=rows
summ=frame('cij_baseline_benchmark_results/benchmark_summary.csv')
for _,r in summ.iterrows():close('RQ1 mean '+r['method'],df[df.method==r['method']].ari.mean(),r.ari_mean,1e-10)
# Stress mean and CI replay in verify_stress.py. Keep two sets separate here.
for prefix,label in [('rq1_results','primary'),('rq1_results_v2/full','replication')]:
 eff=frame(prefix+'/aggregate/rq1_stress_paired_effects.csv');per=frame(prefix+'/aggregate/rq1_stress_per_run.csv')
 for _,r in eff.iterrows():
  if pd.isna(r.mean_stress_minus_baseline):continue
  a=per[(per.method==r.method)&(per.scenario==r.scenario)].set_index('run_id').sort_index();b=per[(per.method==r.method)&(per.scenario=='baseline')].set_index('run_id').sort_index();d=a[r.metric].to_numpy()-b[r.metric].to_numpy();orient=1 if r.direction=='higher' else -1
  close(f'RQ1 {label} stress {r.method} {r.scenario} {r.metric}',d.mean(),r.mean_stress_minus_baseline,1e-10)
  ci=[r.bootstrap_ci95_low,r.bootstrap_ci95_high];ci=ci if orient==1 else [-ci[1],-ci[0]]
  stats.append(standard('RQ1','stress '+label,r.method+' '+r.scenario,r.method+' baseline',r.metric,r.direction,d*orient,ci,'','','descriptive paired CI; no Holm claimed',prefix+'/aggregate/rq1_stress_per_run.csv'))
# RQ2 original helper extracted byte-for-byte from source commit, imported without main.
hist=OUT/'historical-inference.py';inf=load_module('locked_stats',hist);hashes[str(hist.relative_to(ROOT))]=sha(hist)
align=frame('rq2_results/rq2_rank_alignment_test.csv');rob=frame('rq2_results/rq2_robustness_test.csv');paired=frame('rq2_results/rq2_paired_comparisons.csv');seedrob=rob.groupby(['seed','scenario','estimator'],as_index=False)[['priority_drift_abs_normalized','mean_rank_drift_normalized','top_k_churn','n_error_relative_after','v_error_relative_after']].mean()
grouped=[]
for key,group in paired.groupby(['section','candidate','comparator','scenario'],sort=False):
 section,candidate,comparator,scenario=key;family={};arrays={}
 for _,r in group.iterrows():
  if section=='alignment':
   a=align[align.method==candidate].set_index('seed').sort_index()[r.metric];b=align[align.method==comparator].set_index('seed').sort_index()[r.metric]
  else:
   sr=seedrob[seedrob.scenario==scenario];a=sr[sr.estimator==candidate].set_index('seed').sort_index()[r.metric];b=sr[sr.estimator==comparator].set_index('seed').sort_index()[r.metric]
  assert list(a.index)==list(b.index) and len(a)==40
  arrays[r.metric]=(a.to_numpy()-b.to_numpy())*(1 if r.direction=='higher' else -1)
  family[r.metric]=inf.paired_comparison(a,b,direction=r.direction,denominator={'paired_test_seeds':40})
 results=inf.apply_holm(family)
 for _,r in group.iterrows():
  res=results[r.metric];ci=res['paired_confidence_interval'];row=standard('RQ2',section+' '+scenario,candidate,comparator,r.metric,r.direction,arrays[r.metric],ci,res['raw_p_value'],res['holm_adjusted_p_value'],str(len(family))+' endpoints per contrast','rq2_results/rq2_rank_alignment_test.csv' if section=='alignment' else 'rq2_results/rq2_robustness_test.csv');stats.append(row)
  for k in ['mean','raw_p_value','holm_adjusted_p_value','n_candidate_better','n_comparator_better','n_ties']:close('RQ2 '+str(key)+' '+r.metric+' '+k,res[k],r[k],1e-7)
  for i,x in enumerate(json.loads(r.paired_confidence_interval)):close('RQ2 CI '+str(key)+' '+r.metric+str(i),ci[i],x,1e-7)
# RQ3 rebuild seed means from original 120 scenario rows; no dispatch rerun.
mod=load_module('rq3_recompute',RESULTS/'rq3_results/recompute_seed_level.py');raw=frame('rq3_results/rq3_dispatch_test.csv');seed_saved=frame('rq3_results/rq3_dispatch_test_seed.csv');metrics=list(mod.METRIC_DIRECTIONS)
counts=raw.groupby(['seed','partition','policy']).size();assert (counts==3).all()
seed=raw.groupby(['seed','partition','policy'],as_index=False)[metrics].mean();keys=['seed','partition','policy'];a=seed.set_index(keys).sort_index();b=seed_saved.set_index(keys).sort_index();assert list(a.index)==list(b.index)
for metric in metrics:
 diff=(a[metric]-b[metric]).abs();checks.append({'key':'RQ3 seed mean '+metric,'max_absolute_difference':float(diff.max()),'tolerance_abs_rel':1e-7,'match':bool(np.allclose(a[metric],b[metric],atol=1e-7,rtol=1e-7))})
pair=frame('rq3_results/rq3_paired_comparisons_seed.csv')
for key,group in pair.groupby(['dimension','candidate','comparator','fixed'],sort=False):
 dim,candidate,comparator,fixed=key;f=json.loads(fixed);family={};arrays={}
 for _,r in group.iterrows():
  if dim=='policy':
   sub=seed[seed.partition==f['partition']];aa=sub[sub.policy==candidate].set_index('seed').sort_index();bb=sub[sub.policy==comparator].set_index('seed').sort_index()
  else:
   sub=seed[seed.policy==f['policy']];aa=sub[sub.partition==candidate].set_index('seed').sort_index();bb=sub[sub.partition==comparator].set_index('seed').sort_index()
  assert list(aa.index)==list(bb.index) and len(aa)==40
  arrays[r.metric]=(aa[r.metric].to_numpy()-bb[r.metric].to_numpy())*(1 if r.direction=='higher' else -1)
  family[r.metric]=mod.paired(aa[r.metric].to_numpy(),bb[r.metric].to_numpy(),r.direction)
 assert len(family)==14
 for metric,res in mod.holm(family).items():
  r=group[group.metric==metric].iloc[0];ci=json.loads(res['paired_confidence_interval']);stats.append(standard('RQ3',dim+' '+fixed,candidate,comparator,metric,r.direction,arrays[metric],ci,res['raw_p_value'],res['holm_adjusted_p_value'],'14 endpoints per fixed contrast','rq3_results/rq3_dispatch_test.csv'))
  for k in ['mean','raw_p_value','holm_adjusted_p_value','n_candidate_better','n_comparator_better','n_ties']:close('RQ3 '+str(key)+' '+metric+' '+k,res[k],r[k],1e-7)
  for i,x in enumerate(json.loads(r.paired_confidence_interval)):close('RQ3 CI '+str(key)+' '+metric+str(i),ci[i],x,1e-7)
with (OUT/'statistics.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(stats[0]));w.writeheader();w.writerows(stats)
# Hash all original manifest-covered artifacts as well as replay inputs.
for rel in ['rq1_results/manifest.json','rq1_results_v2/full/manifest.json','rq2_results/rq2_artifact_sha256.json','rq3_results/rq3_artifact_sha256.json']:
 p=RESULTS/rel;hashes[str(p.relative_to(ROOT))]=sha(p);ob=json.loads(p.read_text());hs=ob.get('artifacts',ob)
 for name,h in hs.items():
  if isinstance(h,str) and len(h)==64:
   q=p.parent/name;actual=sha(q);hashes[str(q.relative_to(ROOT))]=actual;assert actual==h,(q,actual,h)
for p in [RESULTS/'verify_camera_ready_evidence.py',RESULTS/'rq3_results/recompute_seed_level.py',RESULTS/'cij_baseline_benchmark_results/selected_configs.json']:
 hashes[str(p.relative_to(ROOT))]=sha(p)
(OUT/'source-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n');(OUT/'comparison-checks.json').write_text(json.dumps(checks,indent=2)+'\n');fail=[c for c in checks if not c['match']];(OUT/'discrepancies.json').write_text(json.dumps(fail,indent=2)+'\n')
summary={'statistics_rows':len(stats),'numeric_checks':len(checks),'matching_checks':len(checks)-len(fail),'discrepancies':len(fail),'environment':protocol['environment'],'scope':'saved CSV statistics only, original verifier base byte check remains failed_EOL_only'};(OUT/'validation.txt').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
