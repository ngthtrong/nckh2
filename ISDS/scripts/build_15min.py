#!/usr/bin/env python3
"""Reauthor the 15-minute deck using illustrations, source-bound plots and method diagrams.
Preserves only the template and the user-protected cover, references and closing.
"""
from pathlib import Path
import json,hashlib
from pptx import Presentation
from pptx.util import Pt
from build_deck import text,box,picture,BLUE,TEAL,ORANGE,INK,MUTED,PALE,LINE,FONT
from revise_deck import prepare,replace_text
from figures_15min import build_all
BASE=Path(__file__).resolve().parents[1];ROOT=BASE.parent;OUT=BASE/'15min'
IM=OUT/'assets/imagegen';CH=OUT/'assets/charts';CH.mkdir(parents=True,exist_ok=True)
SRC=BASE/'ISDS2026_Paper_6444_Conference_Deck.pptx';DEST=OUT/'ISDS2026_Paper_6444_15min.pptx'
all_content=json.loads((OUT/'content-plan.json').read_text())
content=[r for r in all_content if r['section']!='OVERVIEW' and r['title']!='Results: Clustering under stress']
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
# Charts and method diagrams are rendered from recorded tables and manuscript equations.
plotdata=build_all(CH)
(CH/'plot-data.json').write_text(json.dumps(plotdata,indent=2)+'\n')
p=Presentation(SRC);old=list(p.slides)
order=list(range(1,13))+[19,20,21,22]
# Each content slide is emptied down to its five template scaffold shapes.
subs={2:'From uncertain observations to feasible rescue decisions',3:'Three illustrative failures change where a team would be sent',4:'Connect information extraction, consolidation and resource allocation',5:'A synthetic dataset with controlled observations and known evaluation targets',6:'The algorithm cannot consult incident identity or simulated outcomes',7:'Two ways to combine distance, time and evidence before community detection',8:'Evidence families, a bounded score and a scheduler solve different problems',9:'Adjusted Rand Index of independently tuned methods · 40 held-out runs',10:'Copy invariance and benefit alignment answer different questions',11:'Revised priority minus comparator · Product partition · 40 seed pairs · Holm-adjusted p',12:'Conditional safeguards are useful properties, not evidence of field effectiveness',16:'Scope and protocol details kept outside the main talk'}
for i in list(range(2,13))+[16]:
 s=old[order[i-1]-1];r=content[i-1];prepare(s,r['title'],subs[i],r['section'])
def tx(s,v,x,y,w,h,size=21,c=INK,b=False):return text(s,v,x,y,w,h,size,c,b)
def img(s,id,x,y,w,h):return picture(s,IM/(id+'.png'),x,y,w,h,'AI-generated conceptual illustration: '+id+'; not measured data or field evidence.')
def cap(s,value,x,y,w,color=BLUE,size=21):tx(s,value,x,y,w,.55,size,color,True)
def chart(s,name,alt,wide=False):return picture(s,CH/(name+'.png'),.85,1.86 if wide else 2.0,11.65 if wide else 8.0,3.5 if wide else 4.63,alt)
def side(s,items,x=8.95,w=3.6):
 for y,h,t,c in items:cap(s,h,x,y,w,c,size=19);tx(s,t,x,y+.47,w,.8,16.5)
def below(s,items):
 for x,(h,t,c) in zip([.95,4.87,8.79],items):cap(s,h,x,5.42,3.75,c,size=18);tx(s,t,x,5.86,3.75,.7,14.5)
# 2: image-led context; only three decisions in the audience text.
s=old[1];img(s,'01-rescue-context',.86,1.95,7.75,4.37)
cap(s,'Before sending a team',8.93,1.95,3.55)
for y,h,t in [(2.72,'01  Identify','Which reports belong\nto the same incident?'),(3.94,'02  Prioritize','Which incident should\ncome first?'),(5.16,'03  Schedule','Which trips are feasible\nwith available crews?')]:
 tx(s,h,8.95,y,3.45,.37,19,TEAL,True);tx(s,t,8.95,y+.41,3.4,.7,17)
# 3: generated triptych with succinct consequences.
s=old[2];img(s,'02-report-ambiguity',.91,1.92,11.62,3.87)
for x,head,body,col in [(1.03,'Repeated observations','Risk: repeated trips',BLUE),(5.02,'Distinct nearby incidents','Risk: a missed need',TEAL),(9.04,'An invented destination','Risk: a false destination',ORANGE)]:
 tx(s,head,x,5.72,3.45,.48,18,col,True);tx(s,body,x,6.24,3.45,.32,16)
# 4: newly written editorial comparison, not a re-used diagram.
s=old[3]
for x,v,w in [(1.05,'Research strand',3.2),(4.3,'What it provides',3.9),(8.3,'What still needs testing',4.1)]:cap(s,v,x,1.96,w,size=19)
items=[('Crisis sensing [6–8]','Crisis posts and flood imagery','Which physical incident?'),('Community detection [1]','Groups of related reports','A genuine rescue destination?'),('Humanitarian logistics [5]','Allocation and routing trade-offs','Consequences of upstream errors?')]
for i,row in enumerate(items):
 y=2.66+i*.84
 box(s,.9,y-.08,11.65,.72,PALE,None,True)
 for x,v,w in zip([1.07,4.32,8.32],row,[3.2,3.95,4.15]):tx(s,v,x,y+.11,w,.4,16.5)
tx(s,'Our question: do clustering and scoring safeguards improve dispatch?',1.01,5.3,11.4,.6,24,BLUE,True)
tx(s,'Tested in three steps: grouping (RQ1) → ranking (RQ2) → dispatch (RQ3)',1.01,5.98,11.4,.42,18)
# 5: construction image plus four native labels, clear synthesis provenance.
s=old[4]
for i,(t,d) in enumerate([('1  Set the scenario','EMSR848 · OSM · WorldPop\n(clustering tests)'),('2  Simulate incidents','16 hidden incidents per run'),('3  Generate reports','Location · time · evidence'),('4  Add controlled noise','Copies and false reports')]):
 cap(s,t,.99+2.94*i,1.94,2.82,size=18);tx(s,d,.99+2.94*i,2.37,2.82,.6,14.5)
img(s,'03-synthetic-construction',.88,2.98,11.7,3.66)
# 6: information-boundary diagram plus the run split.
s=old[5]
picture(s,CH/'dataset_boundary.png',.85,1.9,11.65,4.55,'Diagram: the algorithm sees report location, time, flood and urgency evidence, people count and vulnerability, then groups, ranks and schedules. Hidden truth (true incident, fake labels, benefit, deadlines, harm) is joined only after predictions and trips are fixed. 80 runs: 20 development, 20 calibration, 40 held-out test.')
# 7-8: method diagrams restating Eq. 3-4 and Algorithms 1-2 of the manuscript.
s=old[6];picture(s,CH/'method_grouping.png',.85,1.95,11.65,4.5,'Diagram: reports, pair similarity G/T/C, Product or Additive edge weight, sparsification, Louvain. Curve: normalised weight against distance for T = C = 1.')
s=old[7];picture(s,CH/'method_priority.png',.85,1.95,11.65,4.5,'Diagram: predicted group, evidence families, family maxima, bounded priority P_k, scheduler; exact-copy guarantee holds for fixed families and inputs.')
# 9: every benchmarked method with its interval.
s=old[8];chart(s,'clustering','Chart: mean ARI with 95% CI for ten methods on 40 held-out runs. Additive Louvain .9191; Product Louvain .9072.')
side(s,[(2.05,'Highest mean: Additive','ARI .9191 vs .9072\nfor Product',TEAL),(3.5,'No advantage established','Paired Wilcoxon,\nHolm p = .2560',BLUE),(4.95,'Graph methods lead','Other baselines:\nARI .47 to .82',MUTED)])
# 11: benefit alignment next to perturbation drift.
s=old[9];chart(s,'ranking','Charts: NDCG@5 with 95% CI for revised .6669, legacy .6548, population only .6709, random .6763; mean priority drift, revised vs legacy, six scenarios.',True)
below(s,[('No alignment advantage','+.0121 vs legacy, not significant;\nbelow population-only and random',TEAL),('Stable under exact copies','Zero drift at 2×, 5×, 10×\n(fixed families and inputs)',BLUE),('Still vulnerable','Coordinated campaign: drift\n.1688 vs .0309 for legacy',ORANGE)])
# 12: paired differences on both outcomes; p-values sit under the charts.
s=old[10];chart(s,'dispatch','Charts from paired CSV: revised minus comparator, simulated harm and deadline-miss rate. Above zero is worse.',True)
below(s,[('Versus legacy priority','Harm p = .563 · deadlines p = .247\nNeither difference is significant',BLUE),('Versus nearest-first','Harm and deadlines: p < .001\nBoth differences are significant',ORANGE),('Grouping errors reach the plan','Product vs matched-density Additive:\nharm +18.34 · Holm p = .000168',TEAL)])
# 12: one takeaway with brief evidence chain and concrete next validation.
s=old[11]
tx(s,'Local guarantees do not establish\nbetter rescue decisions.',1.0,1.85,11.45,1.1,28,BLUE,True)
for x,head,body,c in [(1.0,'Clustering','Spatial gating ≠\nproven clustering gain',BLUE),(5.1,'Ranking','Copy stability ≠\nbenefit alignment',TEAL),(9.0,'Dispatch','A bounded score ≠\na better schedule',ORANGE)]:
 cap(s,head,x,3.2,3.45,c,size=22);tx(s,body,x,3.82,3.4,.95,19)
box(s,.91,5.0,11.65,1.5,PALE,None,True)
for y,h,t in [(5.17,'Contribution','Controlled tests of each step, with truth held by the evaluator · public artifact [12]'),(5.8,'Next','Independently labeled real reports · expert and source checks · joint ranking and scheduling')]:
 tx(s,h,1.12,y,1.7,.4,16.5,BLUE,True);tx(s,t,2.78,y+.02,9.72,.4,15.5)
# 16: a newly authored backup, not an old slide retained for convenience.
s=old[21]
for i,(h,t) in enumerate([('Separate configurations','Generator 3.0: geographic clustering stress. Candidate 4.1: synthetic ranking / dispatch.'),('Information boundary','RQ2 uses oracle incident groups. RQ3 schedules predicted clusters; truth is evaluator-only.'),('Inference unit','40 test seed pairs; three resource conditions are averaged within each seed.'),('Guarantee conditions','Exact copies preserve scores only with fixed evidence families and fixed score inputs.')]):
 y=2.0+i*1.03;tx(s,h,1.0,y,3.0,.62,20,BLUE,True);tx(s,t,4.2,y,8.1,.78,18)
# Publish, synchronize Notes and record source mapping.
ids={s.slide_id:e for s,e in zip(old,list(p.slides._sldIdLst))}
for i,s in enumerate(old,1):
 if i not in order:e=ids[s.slide_id];p.part.drop_rel(e.rId);p.slides._sldIdLst.remove(e)
index=[]
for number,orig in enumerate(order,1):
 s=old[orig-1];p.slides._sldIdLst.append(ids[s.slide_id]);r=content[number-1]
 s._element.set('show','0' if number==16 else '1')
 if orig not in (1,21):replace_text(s.shapes[4],f'{number:02d}')
 s.notes_slide.notes_text_frame.text='ENGLISH\n'+r['english']+'\n\nTIẾNG VIỆT\n'+r['vietnamese']
 for para in s.notes_slide.notes_text_frame.paragraphs:
  for run in para.runs:run.font.name=FONT;run.font.size=Pt(12)
 # Remove orphaned illustration relationships from rebuilt body slides.
 if number not in (1,13,14,15):
  used=set(s._element.xpath('//@r:embed'))
  for rel in list(s.part.rels.values()):
   if rel.reltype.endswith('/image') and rel.rId not in used:s.part.drop_rel(rel.rId)
 index.append(dict(slide=number,source_slide=orig,title=r['title'],role=r['role'],hidden=number==16,content='preserved by user' if number in (1,13,14,15) else 'newly authored'))
# Insert a text-only overview using the same template scaffold.
from copy import deepcopy
from pptx.opc.packuri import PackURI
def scaffold():
 n=p.slides.add_slide(old[1].slide_layout)
 # python-pptx names new parts by slide count, which collides with retained template slides.
 n.part.partname=PackURI('/ppt/slides/slide%d.xml'%(100+len(p.slides)))
 for sh in list(n.shapes):sh._element.getparent().remove(sh._element)
 for sh in list(old[1].shapes)[:5]:n.shapes._spTree.insert_element_before(deepcopy(sh._element),'p:extLst')
 if n.notes_slide.notes_text_frame is None:
  n.notes_slide.shapes._spTree.insert_element_before(deepcopy(old[1].notes_slide.notes_text_frame._txBody.getparent()),'p:extLst')
 return n
# 19: second hidden backup for anticipated questions; values quoted from paper/main.tex.
qa=scaffold();prepare(qa,all_content[-1]['title'],'Statistics and design choices behind the main results','BACKUP');qa._element.set('show','0')
for i,(h,t) in enumerate([('Interval vs. test (RQ1)','Product − Additive = −0.0118, unadjusted bootstrap CI [−0.0226, −0.0024]; Wilcoxon raw p = .0987, Holm p = .2560. Different procedures; no advantage is claimed.'),('Louvain vs. Leiden','Product Leiden ARI .9165 vs. Product Louvain .9072; Holm p = .1120.'),('Fixed constants','21 one-at-a-time settings on 40 test seeds: every mean NDCG@5 span is below .01 (largest .00546).'),('Why synthetic data','Known incident truth and controlled perturbations allow failure diagnosis. No field validity is claimed.')]):
 y=[2.0,3.38,4.2,5.3][i];tx(qa,h,1.0,y,3.1,.62,19,BLUE,True);tx(qa,t,4.2,y,8.2,.9,17)
index.append(dict(slide=19,source_slide=None,title=all_content[-1]['title'],role='backup',hidden=True,content='newly authored'))
stress=scaffold();sr=all_content[10];prepare(stress,sr['title'],'Seven fixed conditions on the 40 held-out runs · settings not retuned',sr['section'])
chart(stress,'clustering_stress','Heatmap: mean ARI for five methods under control, location noise, time noise and exact copies.')
side(stress,[(2.05,'5× exact copies','All graph variants: ARI ≈ .30\n(Product ΔARI = −.6108)',ORANGE),(3.5,'Location and time noise','Every tested level lowers\nmean ARI for all methods',BLUE),(4.95,'False destinations','16.49% rate with Product:\nfake-only groups still form',ORANGE)])
overview=scaffold()
prepare(overview,'Overview','Six parts of the presentation','OVERVIEW')
sections=[('01','Introduction','The rescue-report problem'),('02','Related work','What earlier studies provide'),('03','Dataset','How we create the test reports'),('04','Method','Grouping, ranking and rescue trips'),('05','Results','What the tests show'),('06','Conclusion & Future work','Main lessons and next steps')]
for i,(n,heading,desc) in enumerate(sections):
 x=1.03+(i//3)*6.0;y=2.05+(i%3)*1.43
 tx(overview,n,x,y,.7,.5,25,TEAL,True)
 tx(overview,heading,x+.88,y,4.75,.62,23,BLUE,True)
 tx(overview,desc,x+.88,y+.71,4.75,.45,17)
e=p.slides._sldIdLst[-1];p.slides._sldIdLst.remove(e);p.slides._sldIdLst.insert(1,e)
e=p.slides._sldIdLst[-1];p.slides._sldIdLst.remove(e);p.slides._sldIdLst.insert(10,e)
# Renumber all slide metadata and synchronize both language scripts.
index.insert(1,dict(slide=2,source_slide=None,title='Overview',role='main',hidden=False,content='newly authored'))
index.insert(10,dict(slide=11,source_slide=None,title=sr['title'],role='main',hidden=False,content='newly authored'))
assert len(p.slides)==len(all_content)==len(index)==19
content=all_content
for number,(slide,r,entry) in enumerate(zip(p.slides,content,index),1):
 entry.update(slide=number,title=r['title'],section=r['section'],hidden=r['role']=='backup')
 if number not in (1,17):replace_text(slide.shapes[4],f'{number:02d}')
 slide._element.set('show','0' if r['role']=='backup' else '1')
 slide.notes_slide.notes_text_frame.text='ENGLISH\n'+r['english']+'\n\nTIẾNG VIỆT\n'+r['vietnamese']
 for para in slide.notes_slide.notes_text_frame.paragraphs:
  for run in para.runs:run.font.name=FONT;run.font.size=Pt(12)
p.save(DEST)
(OUT/'slide-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
(OUT/'talk-track.json').write_text(json.dumps(content,ensure_ascii=False,indent=2)+'\n')
parts=[]
for lang,key in [('English','english'),('Tiếng Việt','vietnamese')]:
 parts.append('# '+lang+'\n')
 for r in content:parts.append(f"## Slide {r['slide']:02d}"+(' (Backup)' if r['role']=='backup' else '')+'\n\n'+r[key]+'\n')
(OUT/'speaker-notes.md').write_text('\n'.join(parts))
(OUT/'build-manifest.json').write_text(json.dumps({'source':str(SRC.relative_to(BASE)),'source_sha256':sha(SRC),'deck_sha256':sha(DEST),'main_slides':17,'backup':[18,19],'source_order':[1,None]+order[1:9]+[None]+order[9:]+[None],'protected_slides':[1,15,16,17],'reauthored_slides':list(range(2,15))+[18,19],'planned_seconds':sum(r['seconds'] for r in content),'english_main_words':sum(len(r['english'].split()) for r in content[:17]),'image_generation':'Three built-in image_gen scene illustrations (slides 3, 4, 6); method slides use diagrams drawn from the manuscript equations.','data_provenance':'One synthetic construction narrative, separate evaluation configurations; original results not pooled.','content_plan_sha256':sha(OUT/'content-plan.json'),'manuscript_sha256':sha(ROOT/'paper/main.tex'),'plot_data_sha256':sha(CH/'plot-data.json')},indent=2)+'\n')
print(DEST)
