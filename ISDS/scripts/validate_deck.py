#!/usr/bin/env python3
"""Inspect deck structure, source bindings, fonts, animations and PDF export."""
import hashlib
import json
import re
from collections import Counter
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pymupdf as fitz
from PIL import Image
from pptx import Presentation

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'ISDS'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    checks=[]
    def check(name,ok,detail=None):checks.append({'check':name,'passed':bool(ok),'detail':detail})
    deck=BASE/'ISDS2026_Paper_6444_Conference_Deck.pptx'
    pdf=deck.with_suffix('.pdf')
    prs=Presentation(deck)
    check('slide_count',len(prs.slides)==26,len(prs.slides))
    texts=['\n'.join(sh.text for sh in s.shapes if sh.has_text_frame) for s in prs.slides]
    check('overview_at_slide_2','Presentation overview' in texts[1])
    authors=['Thanh-Trong Nguyen','Ngoc-Anh Le','Nhu-Quynh Nguyen','Tuong-Hung Cao',
             'Hung-Thinh Ngo','Xuan-Phuong Chau','Lan Phuong Phan','Thanh-Khoa Nguyen']
    check('current_eight_authors_on_cover',all(a in texts[0] for a in authors))
    check('two_references_slides','References (1 of 2)' in texts[23] and 'References (2 of 2)' in texts[24])
    check('separate_conclusion_and_future','Conclusion' in texts[21] and 'Future work' in texts[22])
    notes=[s.notes_slide.notes_text_frame.text for s in prs.slides]
    check('all_slides_have_speaker_notes',all(len(n)>100 for n in notes),[len(n) for n in notes])
    native_fonts=Counter(r.font.name for s in prs.slides for sh in s.shapes if sh.has_text_frame for p in sh.text_frame.paragraphs for r in p.runs)
    check('native_text_uses_template_fonts',set(native_fonts)<= {'K2D','Readex Pro'},dict(native_fonts))
    added_footnotes=[(i+1,sh.text) for i,s in enumerate(prs.slides) for sh in s.shapes
                     if sh.has_text_frame and 6.79*914400<float(sh.top)<7.03*914400 and sh.text.strip()]
    check('no_added_bottom_footnotes',not added_footnotes,added_footnotes)
    bottom_banners=[(i+1,sh.name) for i,s in enumerate(prs.slides) for sh in s.shapes
                    if 1<i+1<24 and 6.30*914400<float(sh.top)<6.80*914400]
    check('no_bottom_summary_banners',not bottom_banners,bottom_banners)
    left_bars=[(i+1,sh.name) for i,s in enumerate(prs.slides) for sh in s.shapes
               if 0<float(sh.width)<.06*914400 and float(sh.height)>914400]
    check('no_colored_box_left_borders',not left_bars,left_bars)
    paths_on_face=[(i+1,t) for i,t in enumerate(texts) if any(x in t for x in ('paper/main','thucnghiem/','ISDS/research','Source:'))]
    check('no_internal_file_paths_on_face',not paths_on_face,paths_on_face)
    oversize=[]
    for i,s in enumerate(prs.slides,1):
        for sh in s.shapes:
            if min(sh.left,sh.top)<-100 or sh.left+sh.width>prs.slide_width+100 or sh.top+sh.height>prs.slide_height+100:
                oversize.append({'slide':i,'shape':sh.name})
    check('all_added_shapes_within_canvas',not oversize,oversize)
    manifest=json.loads((BASE/'build-manifest.json').read_text())
    mismatches=[p for p,h in manifest['inputs'].items() if sha(ROOT/p)!=h]
    check('canonical_inputs_unchanged',not mismatches,mismatches)
    sci=json.loads((BASE/'assets/science/manifest.json').read_text())
    changed=[p for p,h in sci['inputs'].items() if sha(ROOT/p)!=h]
    check('scientific_source_hashes_unchanged',not changed,changed)
    # Each scientific result retains its actual machine-checkable replay record.
    replay=json.loads((BASE/'assets/science/graph_replay_values.json').read_text())
    check('one_run_replay_receipt_present',bool(replay),str(BASE/'assets/science/graph_replay_values.json'))
    with ZipFile(deck) as z:
        check('pptx_zip_integrity',z.testzip() is None)
        media={hashlib.sha256(z.read(n)).hexdigest():n for n in z.namelist() if n.startswith('ppt/media/')}
        for name,frames in [('louvain_schematic.gif',4),('graph_stress.gif',8)]:
            path=BASE/'assets/science'/name
            im=Image.open(path);durations=[];hashes=[]
            for k in range(im.n_frames):
                im.seek(k);durations.append(im.info.get('duration',0));hashes.append(hashlib.sha256(im.convert('RGB').tobytes()).hexdigest())
            check(name+'_animated',im.n_frames==frames and len(set(hashes))==frames,
                  {'frames':im.n_frames,'duration_ms':sum(durations),'dimensions':im.size})
            check(name+'_embedded_unchanged',sha(path) in media,media.get(sha(path)))
    doc=fitz.open(pdf)
    check('pdf_pages',len(doc)==26,len(doc))
    check('pdf_16_by_9',all(abs(p.rect.width/p.rect.height-16/9)<.001 for p in doc))
    pdf_fonts=sorted({f[3] for p in doc for f in p.get_fonts()})
    check('pdf_contains_actual_K2D_and_ReadexPro',any('K2D' in f for f in pdf_fonts) and any('Readex' in f for f in pdf_fonts),pdf_fonts)
    check('pdf_overview_second_page','Presentation overview' in doc[1].get_text())
    # Template-owned website/page-number footer is retained; source footnotes are not.
    bottom_text=[]
    for i,p in enumerate(doc,1):
        for b in p.get_text('dict')['blocks']:
            for l in b.get('lines',[]):
                for sp in l['spans']:
                    template_brand={'CTU','CAN THO UNIVERSITY'}
                    if (sp['bbox'][1]>6.79*72 and sp['bbox'][1]<7.03*72
                            and sp['text'].strip() and sp['text'].strip() not in template_brand):
                        bottom_text.append((i,sp['text']))
    check('pdf_has_no_added_bottom_footnotes',not bottom_text,bottom_text)
    refs=json.loads((BASE/'research/references.json').read_text())
    check('12_reference_records',[r['id'] for r in refs]==list(range(1,13)))
    check('reference_urls_complete',all(r.get('url') and r.get('verification_url') for r in refs))
    out={'deck_sha256':sha(deck),'pdf_sha256':sha(pdf),'passed':all(c['passed'] for c in checks),'checks':checks,
         'scope':'Artifact/content-bound checks; no field-validity, author-approval or scientific-acceptance conclusion.'}
    (BASE/'checks/validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'passed':out['passed'],'checks':len(checks),'failures':[c for c in checks if not c['passed']]},indent=2))
    raise SystemExit(0 if out['passed'] else 1)


if __name__=='__main__':main()
