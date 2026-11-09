from pathlib import Path
import importlib.util,json
import pandas as pd
from importlib.metadata import version
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('locked',OUT/'historical-inference.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
a=pd.read_csv(ROOT/'thucnghiem/results/rq2_results/rq2_rank_alignment_test.csv');p=pd.read_csv(ROOT/'thucnghiem/results/rq2_results/rq2_paired_comparisons.csv');out=[]
for comp,g in p[p.section=='alignment'].groupby('comparator'):
 family={}
 for _,r in g.iterrows():
  aa=a[a.method==r.candidate].set_index('seed').sort_index()[r.metric];bb=a[a.method==comp].set_index('seed').sort_index()[r.metric]
  family[r.metric]=m.paired_comparison(aa,bb,direction=r.direction,denominator={'paired_test_seeds':40})
 for metric,res in m.apply_holm(family).items():
  r=g[g.metric==metric].iloc[0];out.append({'comparator':comp,'metric':metric,'raw_p_replay':res['raw_p_value'],'raw_p_saved':r.raw_p_value,'Holm_replay':res['holm_adjusted_p_value'],'Holm_saved':r.holm_adjusted_p_value})
(OUT/'rq2-version-comparison.json').write_text(json.dumps({'environment':{n:version(n) for n in ['numpy','pandas','scipy']},'source':'same rounded saved CSV, same original statistical helper; version isolation only','results':out},indent=2)+'\n');print('Replayed',len(out),'RQ2 alignment tests in original package versions')
