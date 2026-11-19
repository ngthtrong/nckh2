#!/usr/bin/env python3
"""Result charts and method diagrams for the 15-minute deck.

Charts read the recorded result tables and assert the values quoted in
paper/main.tex; diagrams restate the manuscript equations. Nothing is
recomputed, pooled or written back to the research artifacts.
"""
from pathlib import Path
import csv,hashlib,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch
from build_deck import BLUE,TEAL,ORANGE,INK,MUTED,PALE,LINE
BASE=Path(__file__).resolve().parents[1];ROOT=BASE.parent;RES=ROOT/'thucnghiem/results'
for f in ('readexpro/ReadexPro-Regular.ttf','readexpro/ReadexPro-Bold.ttf','k2d/K2D-Bold.ttf'):font_manager.fontManager.addfont(str(BASE/'fonts'/f))
plt.rcParams.update({'font.family':'Readex Pro','font.size':15,'text.color':'#'+INK,'axes.labelcolor':'#'+MUTED,'xtick.color':'#'+MUTED,'ytick.color':'#'+INK,'axes.edgecolor':'#'+LINE,'savefig.facecolor':'white','mathtext.fontset':'dejavusans'})
C=lambda v:'#'+v
GREY='9AA7B2'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def rows(path):
 with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def near(a,b,tol=6e-5):assert abs(a-b)<tol,(a,b)
def clean(ax,grid='x'):
 for sp in ('top','right','left'):ax.spines[sp].set_visible(False)
 (ax.xaxis if grid=='x' else ax.yaxis).grid(True,color=C(LINE),linewidth=.8);ax.set_axisbelow(True)

def clustering(out):
 """Held-out ARI with bootstrap 95% CI for every benchmarked method (paper Table 1)."""
 src=RES/'cij_baseline_benchmark_results/benchmark_summary.csv'
 names={'additive_cij_louvain':'Additive Louvain','product_cij_leiden':'Product Leiden','convex_cij_louvain':'Convex Louvain','product_cij_louvain':'Product Louvain','additive_cij_louvain_matched_density':'Matched-density Additive','coordinate_kmeans':'Coordinate K-means','spatial_agglomerative':'Spatial agglomerative','hdbscan_all':'HDBSCAN','geo_time_dbscan':'Geo-time DBSCAN','dbscan_all':'DBSCAN, all features'}
 d=sorted(((names[r['method']],float(r['ari_mean']),float(r['ari_ci95_low']),float(r['ari_ci95_high']),r['method']) for r in rows(src)),key=lambda r:-r[1])
 assert len(d)==10
 val={r[4]:r[1] for r in d};near(val['additive_cij_louvain'],.9191);near(val['product_cij_louvain'],.9072);near(val['product_cij_leiden'],.9165);near(val['geo_time_dbscan'],.4978)
 fig,ax=plt.subplots(figsize=(8.3,4.8),dpi=220);ys=list(range(len(d)-1,-1,-1))
 col=[C(TEAL) if r[4]=='additive_cij_louvain' else C(BLUE) if r[4]=='product_cij_louvain' else C(GREY) for r in d]
 ax.barh(ys,[r[1] for r in d],height=.62,color=col)
 ax.errorbar([r[1] for r in d],ys,xerr=[[r[1]-r[2] for r in d],[r[3]-r[1] for r in d]],fmt='none',ecolor=C(INK),elinewidth=1.3,capsize=3)
 for y,r in zip(ys,d):ax.text(r[3]+.015,y,f'{r[1]:.4f}'.lstrip('0'),va='center',fontsize=13.5,color=C(INK))
 ax.set_yticks(ys,[r[0] for r in d]);ax.tick_params(axis='y',length=0,pad=8,labelsize=13.5);ax.tick_params(axis='x',labelsize=13)
 ax.set_xlim(0,1.1);ax.set_xticks([0,.25,.5,.75,1]);ax.set_ylim(-.6,len(d)-.4)
 ax.set_xlabel('Mean ARI [3] · 40 held-out runs · 95% CI',fontsize=13,labelpad=10)
 clean(ax);fig.subplots_adjust(left=.33,right=.985,top=.985,bottom=.16);fig.savefig(out,dpi=220);plt.close(fig)
 return {'labels':[r[0] for r in d],'values':[r[1] for r in d],'ci95':[[r[2],r[3]] for r in d],'holm_p_product_vs_additive':.2560,'source':str(src.relative_to(ROOT)),'source_sha256':sha(src)}

def stress(out):
 """Mean ARI under the seven fixed conditions (primary RQ1 stress artifact)."""
 src=RES/'rq1_results/aggregate/rq1_stress_summary.csv'
 methods=[('additive_cij_louvain','Additive Louvain'),('product_cij_louvain','Product Louvain'),('product_cij_leiden','Product Leiden'),('additive_cij_louvain_matched_density','Matched-density Additive'),('geo_time_dbscan','Geo-time DBSCAN')]
 conds=[('baseline','Control'),('gps_noise_100m','Location\n±100 m'),('gps_noise_300m','Location\n±300 m'),('time_noise_15min','Time\n±15 min'),('time_noise_60min','Time\n±60 min'),('exact_transport_copy_2x','Copies\n2×'),('exact_transport_copy_5x','Copies\n5×')]
 v={(r['scenario'],r['method']):float(r['ari_original_mean']) for r in rows(src)}
 assert all(int(r['ari_original_count'])==40 for r in rows(src)) and len(v)==35
 near(v['baseline','product_cij_louvain'],.9072);near(v['exact_transport_copy_5x','product_cij_louvain']-v['baseline','product_cij_louvain'],-.6108)
 assert all(abs(v['exact_transport_copy_5x',m]-.30)<.01 for m,_ in methods[:4])
 grid=[[v[c,m] for c,_ in conds] for m,_ in methods]
 fig,ax=plt.subplots(figsize=(8.3,4.8),dpi=220)
 cmap=matplotlib.colors.LinearSegmentedColormap.from_list('ari',[C(ORANGE),'#F6E3CC','#DCEBF5',C(BLUE)])
 ax.imshow(grid,cmap=cmap,vmin=.25,vmax=.95,aspect='auto')
 for i,row in enumerate(grid):
  for j,x in enumerate(row):ax.text(j,i,f'{x:.2f}'.lstrip('0'),ha='center',va='center',fontsize=15,color='white' if x>.84 or x<.36 else C(INK))
 ax.set_xticks(range(len(conds)),[c[1] for c in conds],fontsize=12.5);ax.set_yticks(range(len(methods)),[m[1] for m in methods],fontsize=13.5)
 ax.xaxis.tick_top();ax.tick_params(length=0,pad=6);ax.tick_params(axis='x',colors=C(INK))
 ax.set_xticks([x-.5 for x in range(1,len(conds))],minor=True);ax.set_yticks([y-.5 for y in range(1,len(methods))],minor=True)
 ax.grid(which='minor',color='white',linewidth=3);ax.tick_params(which='minor',length=0)
 for sp in ax.spines.values():sp.set_visible(False)
 fig.text(.5,.045,'Mean ARI over 40 held-out runs · original reports scored in every column',ha='center',fontsize=13,color=C(MUTED))
 fig.subplots_adjust(left=.30,right=.99,top=.84,bottom=.13);fig.savefig(out,dpi=220);plt.close(fig)
 return {'methods':[m[1] for m in methods],'conditions':[c[1].replace('\n',' ') for c in conds],'mean_ari':grid,'source':str(src.relative_to(ROOT)),'source_sha256':sha(src)}

def ranking(out):
 """Left: NDCG@5 with 95% CI. Right: priority drift, revised vs legacy, selected scenarios."""
 src=RES/'rq2_results/rq2_summary.csv';data=rows(src)
 al={r['method']:(float(r['mean']),eval(r['paired_confidence_interval'],{})) for r in data if r['section']=='alignment' and r['metric']=='ndcg_at_5'}
 near(al['duplicate_aware_robust'][0],.6669);near(al['population_only'][0],.6709);near(al['random'][0],.6763);near(al['duplicate_aware_robust'][0]-al['legacy_raw'][0],.0121)
 bars=[('Revised priority','duplicate_aware_robust',BLUE),('Legacy priority','legacy_raw',GREY),('Population only','population_only',GREY),('Random ordering','random',GREY)]
 dr={(r['scenario'],r['method']):float(r['mean']) for r in data if r['section']=='robustness' and r['metric']=='priority_drift_abs_normalized'}
 sc=[('exact_duplicate_2x','Exact copies 2×'),('exact_duplicate_5x','Exact copies 5×'),('exact_duplicate_10x','Exact copies 10×'),('near_duplicate','Near copies'),('low_confidence_inflate_N','Inflated people count'),('coordinated_high_confidence_campaign','Coordinated campaign')]
 near(dr['coordinated_high_confidence_campaign','duplicate_aware_robust'],.1688);near(dr['coordinated_high_confidence_campaign','legacy_raw'],.0309)
 assert all(dr[s,'duplicate_aware_robust']==0 for s,_ in sc[:3])
 fig,(a,b)=plt.subplots(1,2,figsize=(11.65,3.5),dpi=220,gridspec_kw={'width_ratios':[1,1.12]})
 ys=list(range(len(bars)-1,-1,-1));m=[al[k][0] for _,k,_ in bars]
 a.barh(ys,m,height=.56,color=[C(c) for *_,c in bars])
 a.errorbar(m,ys,xerr=[[al[k][0]-al[k][1][0] for _,k,_ in bars],[al[k][1][1]-al[k][0] for _,k,_ in bars]],fmt='none',ecolor=C(INK),elinewidth=1.3,capsize=3)
 for y,(_,k,_) in zip(ys,bars):a.text(al[k][1][1]+.015,y,f'{al[k][0]:.4f}'.lstrip('0'),va='center',fontsize=14)
 a.set_yticks(ys,[x[0] for x in bars]);a.tick_params(axis='y',length=0,pad=8,labelsize=14);a.tick_params(axis='x',labelsize=12.5)
 a.set_xlim(0,1.0);a.set_xticks([0,.25,.5,.75,1]);a.set_ylim(-.6,len(bars)-.4)
 a.set_title('Agreement with simulated benefit',fontsize=15,color=C(BLUE),fontfamily='K2D',fontweight='bold',loc='left',pad=10)
 a.set_xlabel('NDCG@5 [4] · 95% CI · higher is better',fontsize=12.5,labelpad=8);clean(a)
 ys=list(range(len(sc)-1,-1,-1));h=.36
 b.barh([y+h/2 for y in ys],[dr[s,'duplicate_aware_robust'] for s,_ in sc],height=h,color=C(BLUE),label='Revised')
 b.barh([y-h/2 for y in ys],[dr[s,'legacy_raw'] for s,_ in sc],height=h,color=C(GREY),label='Legacy')
 for y,(s,_) in zip(ys,sc):
  for off,k in ((h/2,'duplicate_aware_robust'),(-h/2,'legacy_raw')):b.text(dr[s,k]+.004,y+off,f'{dr[s,k]:.4f}'.lstrip('0') if dr[s,k] else '0',va='center',fontsize=11.5)
 b.set_yticks(ys,[x[1] for x in sc]);b.tick_params(axis='y',length=0,pad=8,labelsize=13.5);b.tick_params(axis='x',labelsize=12.5)
 b.set_xlim(0,.2);b.set_xticks([0,.05,.1,.15,.2]);b.set_ylim(-.6,len(sc)-.4)
 b.set_title('Score change under perturbation',fontsize=15,color=C(BLUE),fontfamily='K2D',fontweight='bold',loc='left',pad=10)
 b.set_xlabel('Mean priority drift · lower is better',fontsize=12.5,labelpad=8);b.legend(frameon=False,fontsize=12.5,loc='upper right');clean(b)
 fig.subplots_adjust(left=.155,right=.985,top=.89,bottom=.19,wspace=.66);fig.savefig(out,dpi=220);plt.close(fig)
 return {'ndcg_at_5':{n:{'mean':al[k][0],'ci95':al[k][1]} for n,k,_ in bars},'priority_drift':{n:{'revised':dr[s,'duplicate_aware_robust'],'legacy':dr[s,'legacy_raw']} for s,n in sc},'note':'Six of the eleven robustness scenarios in paper Table 3 are plotted.','source':str(src.relative_to(ROOT)),'source_sha256':sha(src)}

def dispatch(out):
 """Paired seed-level differences, revised minus comparator, Product partition."""
 src=RES/'rq3_results/rq3_paired_comparisons_seed.csv'
 d={(r['comparator'],r['metric']):r for r in rows(src) if r['candidate']=='revised_priority' and r['fixed']=='{"partition": "product_cij"}' and r['comparator'] in ('legacy_priority','nearest_first') and r['metric'] in ('latent_harm','deadline_miss_rate')}
 assert len(d)==4 and all(int(r['n_seed_pairs'])==40 for r in d.values())
 diff=lambda c,m:float(d[c,m]['mean_difference_candidate_minus_comparator']);p=lambda c,m:float(d[c,m]['holm_adjusted_p_value'])
 near(diff('legacy_priority','latent_harm'),14.34,6e-3);near(diff('nearest_first','latent_harm'),69.88,6e-3);near(diff('legacy_priority','deadline_miss_rate')*100,-1.88,6e-3);near(diff('nearest_first','deadline_miss_rate')*100,17.71,6e-3)
 near(p('legacy_priority','latent_harm'),.563,6e-4);near(p('legacy_priority','deadline_miss_rate'),.247,6e-4);near(p('nearest_first','latent_harm'),4.1e-5,1e-6);near(p('nearest_first','deadline_miss_rate'),1.2e-6,2e-7)
 part={(r['comparator'],r['metric']):r for r in rows(src) if r['dimension']=='partition' and r['candidate']=='product_cij' and r['fixed']=='{"policy": "revised_priority"}' and r['metric'] in ('latent_harm','deadline_miss_rate')}
 pd=lambda c,m:float(part[c,m]['mean_difference_candidate_minus_comparator']);pp=lambda c,m:float(part[c,m]['holm_adjusted_p_value'])
 near(pd('additive_cij_matched_density','latent_harm'),18.34,6e-3);near(pp('additive_cij_matched_density','latent_harm'),.000168,1e-6)
 comp=[('legacy_priority','vs legacy priority',GREY),('nearest_first','vs nearest-first',ORANGE)]
 fig,axes=plt.subplots(1,2,figsize=(11.65,3.5),dpi=220)
 for ax,(metric,scale,title,xl,lim,fmt) in zip(axes,[('latent_harm',1,'Simulated harm','Revised minus comparator · model units',(-10,90),'{:+.2f}'),('deadline_miss_rate',100,'Missed deadlines','Revised minus comparator · percentage points',(-5,26),'{:+.2f} pp')]):
  vals=[diff(c,metric)*scale for c,*_ in comp];ys=[1,0]
  ax.barh(ys,vals,height=.5,color=[C(c) for *_,c in comp]);ax.axvline(0,color=C(INK),linewidth=1.2)
  for y,x in zip(ys,vals):ax.text(x+(lim[1]-lim[0])*.015 if x>0 else lim[1]*.04,y,fmt.format(x).replace('-','−'),va='center',fontsize=15)
  ax.set_yticks(ys,[c[1] for c in comp]);ax.tick_params(axis='y',length=0,pad=8,labelsize=14);ax.tick_params(axis='x',labelsize=12.5)
  ax.set_xlim(*lim);ax.set_ylim(-.6,1.6);ax.set_xlabel(xl,fontsize=12.5,labelpad=8)
  ax.set_title(title+' · above zero is worse',fontsize=15,color=C(BLUE),fontfamily='K2D',fontweight='bold',loc='left',pad=10);clean(ax)
 fig.subplots_adjust(left=.16,right=.985,top=.89,bottom=.19,wspace=.52);fig.savefig(out,dpi=220);plt.close(fig)
 return {'direction':'Revised minus comparator; positive means more simulated harm or more missed deadlines.','comparisons':{c:{m:{'mean_difference':diff(c,m),'holm_p':p(c,m)} for m in ('latent_harm','deadline_miss_rate')} for c,*_ in comp},'partition_contrasts':{'direction':'Product partition minus comparator partition under revised priority; positive means worse.','vs':{c:{m:{'mean_difference':pd(c,m),'holm_p':pp(c,m)} for m in ('latent_harm','deadline_miss_rate')} for c in ('additive_cij_matched_density','oracle')}},'source':str(src.relative_to(ROOT)),'source_sha256':sha(src)}

# ---- Method diagrams: manuscript equations drawn as flow charts, no measured data.
def canvas(w,h):
 fig=plt.figure(figsize=(w,h),dpi=220);ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,w);ax.set_ylim(0,h);ax.axis('off');return fig,ax
def card(ax,x,y,w,h,head,body,color=BLUE,fill=PALE,hs=15,bs=12.5):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0,rounding_size=.09',fc=C(fill),ec=C(color),lw=1.4))
 ax.text(x+w/2,y+h-.2,head,ha='center',va='top',fontsize=hs,color=C(color),fontfamily='K2D',fontweight='bold')
 ax.text(x+w/2,y+h-.62,body,ha='center',va='top',fontsize=bs,color=C(INK),linespacing=1.35)
def arrow(ax,x1,y1,x2,y2,color=MUTED,dash=False):
 ax.annotate('',xy=(x2,y2),xytext=(x1,y1),arrowprops=dict(arrowstyle='-|>',color=C(color),lw=1.8,mutation_scale=16,linestyle='--' if dash else '-'))
def flow(ax,y,h,steps,x0=.05,w=2.06,gap=.3):
 for i,(head,body,color) in enumerate(steps):
  x=x0+i*(w+gap);card(ax,x,y,w,h,head,body,color)
  if i:arrow(ax,x-gap+.03,y+h/2,x-.03,y+h/2)

def method_grouping(out):
 """Eq. 3 of the paper plus Algorithm 1 steps; curve uses the selected sigma and weights."""
 W,H=11.65,4.5;fig,ax=canvas(W,H)
 flow(ax,3.12,1.3,[('Reports','location · time\nflood, urgency',BLUE),('Pair similarity','$G$ distance · $T$ time\n$C$ evidence',BLUE),('Edge weight','Product\nor Additive',TEAL),('Keep strong links','quantile threshold\nthen top-$k$ neighbours',BLUE),('Louvain','communities =\npredicted groups',ORANGE)])
 for y,head,eq,note,color in [(1.62,'Product',r'$w^{\times}_{ij}=G_{ij}\,(\beta\,T_{ij}+\gamma\,C_{ij})$','Distance gates time and evidence, cf. [2]',BLUE),(.08,'Additive',r'$w^{+}_{ij}=\alpha\,G_{ij}+\beta\,T_{ij}+\gamma\,C_{ij}$','Each signal adds on its own',TEAL)]:
  ax.add_patch(FancyBboxPatch((.05,y),5.25,1.3,boxstyle='round,pad=0,rounding_size=.09',fc='white',ec=C(color),lw=1.4))
  ax.text(.27,y+1.08,head,va='top',fontsize=15,color=C(color),fontfamily='K2D',fontweight='bold')
  ax.text(5.08,y+1.05,note,va='top',ha='right',fontsize=12,color=C(MUTED))
  ax.text(2.67,y+.42,eq,ha='center',va='center',fontsize=19,color=C(INK))
 # Normalised weight against distance for a pair that agrees on time and evidence.
 sigma,alpha,beta,gamma=700.,1.,.5,.5
 g=fig.add_axes([6.55/W,.62/H,4.95/W,1.78/H]);xs=[i*10 for i in range(301)]
 G=[math.exp(-(x*x)/(2*sigma*sigma)) for x in xs]
 g.plot([x/1000 for x in xs],G,color=C(BLUE),lw=2.6);g.plot([x/1000 for x in xs],[(alpha*v+beta+gamma)/(alpha+beta+gamma) for v in G],color=C(TEAL),lw=2.6)
 g.text(1.42,.13,'Product falls to 0',color=C(BLUE),fontsize=12.5);g.text(1.42,.60,'Additive keeps half',color=C(TEAL),fontsize=12.5)
 g.set_xlim(0,3);g.set_ylim(0,1.05);g.set_xticks([0,1,2,3]);g.set_yticks([0,.5,1]);g.tick_params(labelsize=12,length=0)
 g.set_xlabel('Distance between two reports (km)',fontsize=12.5,labelpad=5);g.set_ylabel('Share of\nmaximum weight',fontsize=12,labelpad=6);clean(g,'y');g.spines['left'].set_visible(True)
 ax.text(6.0,2.92,'Two reports with the same time and evidence',va='top',fontsize=14,color=C(BLUE),fontfamily='K2D',fontweight='bold')
 ax.text(6.0,2.6,r'$T=C=1$ · $\sigma=700$ m · $\alpha=1$, $\beta=\gamma=0.5$ (selected settings)',va='top',fontsize=11.5,color=C(MUTED))
 fig.savefig(out,dpi=220);plt.close(fig)
 return {'kind':'diagram','equations':'paper/main.tex Eq. (3), Algorithm 1','curve':{'sigma_m':sigma,'alpha':alpha,'beta':beta,'gamma':gamma,'T':1,'C':1,'product':'G','additive':'(alpha*G+beta+gamma)/(alpha+beta+gamma)'}}

def method_priority(out):
 """Eq. 4 of the paper and Algorithm 2 as a flow from predicted group to schedule."""
 W,H=11.65,4.5;fig,ax=canvas(W,H)
 flow(ax,3.12,1.3,[('Predicted group','reports in\none cluster',BLUE),('Evidence families','exact copies and\nnear copies together',BLUE),('One value per family','family maximum ×\nreport confidence $Q_i$',BLUE),('Priority $P_k$','bounded score\nfor the group',TEAL),('Scheduler','travel and service time\navailable boats',ORANGE)])
 ax.add_patch(FancyBboxPatch((4.25,.08),7.35,2.72,boxstyle='round,pad=0,rounding_size=.09',fc='white',ec=C(TEAL),lw=1.4))
 ax.text(4.47,2.6,'Bounded priority',va='top',fontsize=15,color=C(TEAL),fontfamily='K2D',fontweight='bold')
 ax.text(11.4,2.58,r'$0\leq P_k\leq\mu$',va='top',ha='right',fontsize=16,color=C(TEAL))
 ax.text(7.92,1.62,r'$P_k=\left[\,1+(\mu-1)\tanh(\bar V_k/s)\,\right]\;(\omega_E\bar E_k+\omega_F\bar F_k+\omega_N\bar N_k)$',ha='center',va='center',fontsize=17.5,color=C(INK))
 for x1,x2,xt,t in [(5.22,7.8,6.51,'vulnerability boost\nbetween 1 and $\\mu=2$'),(7.98,11.15,9.56,'urgency, flood, people\neach in [0, 1], weights sum to 1')]:
  ax.plot([x1,x1,x2,x2],[1.3,1.2,1.2,1.3],color=C(MUTED),lw=1.2);ax.text(xt,1.08,t,ha='center',va='top',fontsize=12,color=C(MUTED),linespacing=1.3)
 ax.add_patch(FancyBboxPatch((.05,.08),3.9,2.72,boxstyle='round,pad=0,rounding_size=.09',fc=C(PALE),ec=C(BLUE),lw=1.4))
 ax.text(.27,2.6,'Exact-copy guarantee',va='top',fontsize=15,color=C(BLUE),fontfamily='K2D',fontweight='bold')
 ax.text(.27,2.08,'An exact copy joins an existing\nfamily, so the family maximum\nand the score stay the same.',va='top',fontsize=12.5,linespacing=1.35)
 ax.text(.27,.98,'Holds only when families and\nscore inputs are fixed.',va='top',fontsize=12.5,color=C(ORANGE),linespacing=1.35)
 arrow(ax,8.16,3.12,8.16,2.82,TEAL);arrow(ax,3.44,3.12,3.44,2.82,BLUE)
 fig.savefig(out,dpi=220);plt.close(fig)
 return {'kind':'diagram','equations':'paper/main.tex Eq. (4), Algorithm 2','constants':{'omega':[.34,.33,.33],'mu':2,'s':10,'N_ref':500,'V_cap':50}}

def dataset_boundary(out):
 """Information boundary of Section 2 / Algorithm 1 and the split contract of Section 3."""
 W,H=11.65,4.55;fig,ax=canvas(W,H)
 ax.text(.05,4.52,'OBSERVED BY THE ALGORITHM',va='top',fontsize=14,color=C(BLUE),fontfamily='K2D',fontweight='bold')
 ax.text(3.32,4.47,'algorithm_input.json',va='top',fontsize=11.5,color=C(MUTED))
 for x,w,head,body,color in [(.05,3.3,'Each report','location · time · flood · urgency\npeople count · vulnerability',BLUE),(3.65,2.5,'Group','graph + Louvain\npredicted groups',BLUE),(6.45,2.5,'Rank','priority $P_k$ per group\nRQ2: on true groups',BLUE),(9.25,2.35,'Schedule','boat trips from\ngroups and $P_k$',ORANGE)]:
  card(ax,x,2.95,w,1.25,head,body,color)
 for x in (3.38,6.18,8.98):arrow(ax,x,3.575,x+.25,3.575)
 ax.plot([.05,11.6],[2.68,2.68],color=C(ORANGE),lw=1.6,ls=(0,(6,4)))
 ax.text(3.1,2.68,'Information boundary: truth is never read during inference',ha='center',va='center',fontsize=12,color=C(ORANGE),fontfamily='K2D',fontweight='bold',bbox=dict(fc='white',ec='none',pad=3))
 ax.text(.05,2.55,'HELD BY THE EVALUATOR',va='top',fontsize=14,color=C(TEAL),fontfamily='K2D',fontweight='bold')
 ax.text(2.98,2.52,'ground_truth.json',va='top',fontsize=11.5,color=C(MUTED))
 for x,w,head,body,color in [(.05,3.3,'Hidden truth','true incident · fake labels\nbenefit · deadlines · harm',TEAL),(6.45,2.5,'Join','after predictions\nand trips are fixed',TEAL),(9.25,2.35,'Scores','ARI · NDCG@5\nharm · deadlines',TEAL)]:
  card(ax,x,1.0,w,1.25,head,body,color)
 arrow(ax,3.38,1.625,6.42,1.625,TEAL,True);ax.text(4.9,1.71,'opened last',ha='center',fontsize=11.5,color=C(TEAL))
 arrow(ax,8.98,1.625,9.22,1.625,TEAL)
 ax.plot([10.42,10.42,7.7],[2.93,2.47,2.47],color=C(BLUE),lw=1.8,solid_joinstyle='miter');arrow(ax,7.7,2.48,7.7,2.28,BLUE)
 ax.text(9.06,2.47,'groups · ranks · trips',ha='center',va='center',fontsize=11.5,color=C(BLUE),bbox=dict(fc='white',ec='none',pad=1))
 ax.text(.05,.58,'80 runs',va='center',fontsize=15,color=C(INK),fontfamily='K2D',fontweight='bold')
 ax.text(.05,.24,'16 incidents per run',va='center',fontsize=12,color=C(MUTED))
 x=2.6
 for n,head,body,color,fill in [(20,'Development','runs 1–20',MUTED,'EEF1F4'),(20,'Calibration','selects settings',BLUE,PALE),(40,'Held-out test','every reported result',TEAL,'E6F4F1')]:
  w=9.0*n/80;ax.add_patch(FancyBboxPatch((x+.03,.05),w-.06,.78,boxstyle='round,pad=0,rounding_size=.07',fc=C(fill),ec=C(color),lw=1.3))
  ax.text(x+w/2,.58,f'{head} · {n}',ha='center',va='center',fontsize=13,color=C(color),fontfamily='K2D',fontweight='bold')
  ax.text(x+w/2,.27,body,ha='center',va='center',fontsize=11.5,color=C(INK));x+=w
 fig.savefig(out,dpi=220);plt.close(fig)
 return {'kind':'diagram','source':'paper/main.tex Sections 2-3, Algorithm 1, data contract','splits':{'development':20,'calibration':20,'test':40},'incidents_per_run':16}

def build_all(outdir):
 outdir.mkdir(parents=True,exist_ok=True)
 return {name:fn(outdir/(name+'.png')) for name,fn in [('clustering',clustering),('clustering_stress',stress),('ranking',ranking),('dispatch',dispatch),('method_grouping',method_grouping),('method_priority',method_priority),('dataset_boundary',dataset_boundary)]}

if __name__=='__main__':
 import json;print(json.dumps(build_all(BASE/'15min/assets/charts'),indent=1)[:400])
