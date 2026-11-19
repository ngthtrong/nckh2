#!/usr/bin/env python3
"""Validate variant structure, notes, protected artwork, masters and PDF fonts."""
from pathlib import Path
import json, hashlib, zipfile, re
from pptx import Presentation
import pymupdf
BASE=Path(__file__).resolve().parents[1]; OUT=BASE/'15min'
a=Presentation(BASE/'ISDS2026_Paper_6444_Conference_Deck.pptx')
b=Presentation(OUT/'ISDS2026_Paper_6444_15min.pptx')
index=json.loads((OUT/'slide-index.json').read_text()); notes=json.loads((OUT/'talk-track.json').read_text());manifest=json.loads((OUT/'build-manifest.json').read_text())
checks={}
checks['source_unchanged']=hashlib.sha256((BASE/manifest['source']).read_bytes()).hexdigest()==manifest['source_sha256']
checks['slide_counts']=len(b.slides)==19 and sum(s._element.get('show')!='0' for s in b.slides)==17
checks['bilingual_notes']=all(s.notes_slide.notes_text_frame.text=='ENGLISH\n'+r['english']+'\n\nTIẾNG VIỆT\n'+r['vietnamese'] for s,r in zip(b.slides,notes))
checks['script_order']=(OUT/'speaker-notes.md').read_text().count('## Slide ')==38
checks['cover_and_thanks_unchanged']=all([sh._element.xml for sh in a.slides[x].shapes]==[sh._element.xml for sh in b.slides[y].shapes] for x,y in [(0,0),(20,16)])
checks['references_preserved']=all([sh._element.xml for i,sh in enumerate(a.slides[x].shapes) if i!=4]==[sh._element.xml for i,sh in enumerate(b.slides[y].shapes) if i!=4] for x,y in [(18,14),(19,15)])
with zipfile.ZipFile(BASE/manifest['source']) as za,zipfile.ZipFile(OUT/'ISDS2026_Paper_6444_15min.pptx') as zb:
 names=[n for n in za.namelist() if n.startswith(('ppt/slideMasters/','ppt/slideLayouts/','ppt/theme/'))]
 checks['template_parts_unchanged']=all(za.read(n)==zb.read(n) for n in names)
 for z in (za,zb):assert z.testzip() is None
assets=json.loads((OUT/'assets/imagegen/manifest.json').read_text())
checks['imagegen_assets_embedded']=all(
 hashlib.sha256((OUT/'assets/imagegen'/r['image']).read_bytes()).hexdigest()==r['sha256']
 and any(sh.shape_type==13 and hashlib.sha256(sh.image.blob).hexdigest()==r['sha256'] for sh in b.slides[r['slide']-1].shapes)
 for r in assets)
checks['prompts_saved']=all((OUT/'assets/imagegen'/r['prompt_file']).is_file() for r in assets)
checks['all_body_slides_reauthored']=all(r['content']=='newly authored' for r in index if r['slide'] not in (1,15,16,17))
pdf=pymupdf.open(OUT/'ISDS2026_Paper_6444_15min.pdf')
checks['pdf_pages']=len(pdf)==19
fonts=sorted({f[3] for page in pdf for f in page.get_fonts()})
checks['pdf_template_fonts']=any('K2D' in f for f in fonts) and any('Readex' in f for f in fonts) and not any('Browallia' in f for f in fonts)
checks['pdf_text_inside_page']=all(-1<=v['bbox'][0] and -1<=v['bbox'][1] and v['bbox'][2]<=page.rect.width+1 and v['bbox'][3]<=page.rect.height+1 for page in pdf for block in page.get_text('dict')['blocks'] for ln in block.get('lines',[]) for v in ln['spans'])
# Check every native audience text, except decorative markers, survives export.
missing=[]
norm=lambda s:re.sub(r'\s+','',s).replace('−','-').replace('–','-').replace('’',"'")
for i,(slide,page) in enumerate(zip(b.slides,pdf),1):
 content=norm(page.get_text())
 for shape in slide.shapes:
  if not shape.has_text_frame:continue
  for para in shape.text_frame.paragraphs:
   t=norm(para.text)
   if len(t)>4 and t not in content:missing.append({'slide':i,'text':para.text})
checks['native_text_visible']=not missing
report={'checks':checks,'fonts':fonts,'missing_text':missing,'status':'PASS' if all(checks.values()) else 'FAIL'}
(OUT/'checks/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2));assert all(checks.values())
