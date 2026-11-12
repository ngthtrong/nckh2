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
    index=json.loads((BASE/'slide-index.json').read_text())
    positions={row['original_slide']:row['slide']-1 for row in index}
    count=len(prs.slides)
    check('slide_count',count==22,count)
    check('21_main_and_1_backup',sum(row['role']=='main' for row in index)==21
          and sum(row['role']=='backup' for row in index)==1)
    texts=['\n'.join(sh.text for sh in s.shapes if sh.has_text_frame) for s in prs.slides]
    def face(original):return texts[positions[original]]
    check('overview_at_slide_2','Presentation overview' in texts[1])
    check('research_questions_before_methods','Research questions:' in texts[4]
          and 'Observable pipeline' in texts[5])
    check('both_generator_counts_visible',all(x in face(7) for x in
          ('80 runs','16 incidents/run','26,288 reports','80 datasets','30,229 reports')))
    check('separate_generators_and_geographic_anchors',all(x in face(7) for x in
          ('Separate samples','Copernicus EMSR848','OpenStreetMap','WorldPop 2025')))
    check('claim_verification_limit_visible','dishonest claims' in face(10)
          and 'does not verify a claim' in face(10))
    check('false_destination_result_visible','16.49%' in face(16))
    check('fivefold_stress_result_visible','−0.6108' in face(17)
          and '95% CI' in face(17))
    check('contributions_separate_evidence_levels',all(x in face(21) for x in
          ('MATHEMATICALLY','SIMULATION','ESTABLISHED','1  Product','2  Family','3  Downstream')))
    authors=['Thanh-Trong Nguyen','Ngoc-Anh Le','Nhu-Quynh Nguyen','Tuong-Hung Cao',
             'Hung-Thinh Ngo','Xuan-Phuong Chau','Lan Phuong Phan','Thanh-Khoa Nguyen']
    check('current_eight_authors_on_cover',all(a in texts[0] for a in authors))
    check('two_references_slides','References (1 of 2)' in face(24) and 'References (2 of 2)' in face(25))
    check('merged_conclusion_and_four_future_points',all(x in face(22) for x in
          ('Conclusion and future work','Real-report linkage','Expert + source checks','Transfer + missingness','Joint ranking / dispatch')))
    check('merged_primary_metrics',all(x in face(13) for x in
          ('ARI','NDCG@5','Simulated harm','HIGHER IS BETTER','LOWER IS BETTER','chance','model units')))
    check('absorbed_standalone_slides_removed',all(x not in positions for x in (6,14,15,23)))
    check('louvain_is_hidden_backup_after_closing',positions[9]==21
          and positions[9]>positions[26] and prs.slides[positions[9]]._element.get('show')=='0'
          and 'BACKUP' in face(9))
    check('main_slides_are_visible',all(s._element.get('show','1')!='0'
          for i,s in enumerate(prs.slides) if i!=positions[9]))
    notes=[s.notes_slide.notes_text_frame.text for s in prs.slides]
    check('all_slides_have_speaker_notes',all(len(n)>100 for n in notes),[len(n) for n in notes])
    check('all_slides_have_english_then_vietnamese_notes',all(
          n.startswith('English\n\n') and '\n\nTiếng Việt\n\n' in n for n in notes))
    check('no_citations_or_metadata_in_speaker_notes',all(not re.search(
          r'\[\d+(?:[–,\-]\d+)*\]|https?://|Source notes:|Suggested time:|paper/main|thucnghiem/',n)
          for n in notes))
    script=(BASE/'speaker-notes.md').read_text()
    sections=script.split('# Tiếng Việt\n',1)
    check('script_has_all_english_then_all_vietnamese_slides',len(sections)==2
          and sections[0].startswith('# English\n')
          and all(re.findall(r'^## Slide (\d{2})(?: \(Backup\))?$',part,re.M)==[f'{i:02d}' for i in range(1,count+1)]
                  for part in sections))
    check('backup_marked_in_both_scripts',len(sections)==2 and all(
          '## Slide 22 (Backup)' in part for part in sections))
    check('script_contains_only_talk_track_and_slide_labels',not re.search(
          r'\[\d+(?:[–,\-]\d+)*\]|https?://|Source notes:|Suggested time:|paper/main|thucnghiem/',script))
    bilingual=json.loads((BASE/'research/speaker-notes.json').read_text())
    check('embedded_notes_match_bilingual_json',all(
          row['notes']==actual for row,actual in zip(bilingual,notes)))
    check('both_language_scripts_match_slide_notes',len(bilingual)==count and all(
          row['notes_en'] in sections[0] and row['notes_vi'] in sections[1]
          for row in bilingual) if len(sections)==2 else False)
    check('new_report_scenarios_on_slide_3',all(x in texts[2] for x in
          ('Repeated reports','Nearby incidents','False reports','physical incident')))
    check('pipeline_has_separate_evaluator_and_missingness_branch',all(x in texts[5] for x in
          ('OBSERVABLE INPUTS ONLY','OFFLINE EVALUATION','Withheld incident truth','Fixed outputs','Manual review')))
    check('static_louvain_phases_present_in_backup',all(x in face(9) for x in
          ('Weighted graph','Local moves','Aggregate','C1','C2','Repeat on the smaller graph')))
    native_fonts=Counter(r.font.name for s in prs.slides for sh in s.shapes if sh.has_text_frame for p in sh.text_frame.paragraphs for r in p.runs)
    check('native_text_uses_template_fonts',set(native_fonts)<= {'K2D','Readex Pro'},dict(native_fonts))
    added_footnotes=[(i+1,sh.text) for i,s in enumerate(prs.slides) for sh in s.shapes
                     if sh.has_text_frame and 6.79*914400<float(sh.top)<7.03*914400 and sh.text.strip()]
    check('no_added_bottom_footnotes',not added_footnotes,added_footnotes)
    bottom_banners=[(i+1,sh.name) for i,s in enumerate(prs.slides) for sh in s.shapes
                    if i not in (positions[1],positions[26])
                    and sh.shape_type==1 and sh.width>4*914400
                    and 6.30*914400<float(sh.top)<6.80*914400]
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
    check('manifest_matches_current_deck',manifest['deck_sha256']==sha(deck))
    check('manifest_matches_current_pdf',manifest.get('pdf_sha256')==sha(pdf))
    check('manifest_matches_current_talk_track',manifest.get('talk_track_sha256')==sha(BASE/'research/talk-track.json')
          and manifest.get('speaker_script_sha256')==sha(BASE/'speaker-notes.md'))
    check('notes_follow_revised_order',all(row['title'] in texts[row['slide']-1]
          or row['original_slide'] in (1,26) for row in json.loads((BASE/'research/speaker-notes.json').read_text())))
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
            if name=='graph_stress.gif':
                check(name+'_embedded_unchanged',sha(path) in media,media.get(sha(path)))
        check('louvain_explanation_uses_static_editable_shapes',not any(
              sh.shape_type==13 for sh in prs.slides[positions[9]].shapes))
        poster=BASE/'assets/science/rq1_stress_static.png'
        check('static_stress_heatmap_embedded',sha(poster) in media)
        slide17=prs.slides[positions[17]]
        check('static_stress_heatmap_on_result_slide',any(
              sh.shape_type==13 and hashlib.sha256(sh.image.blob).hexdigest()==sha(poster)
              for sh in slide17.shapes))
        heatmap=manifest['revision']['new_static_heatmap']
        check('static_stress_result_source_unchanged',sha(ROOT/heatmap['input'])==heatmap['input_sha256'])
    doc=fitz.open(pdf)
    check('pdf_pages_including_backup',len(doc)==count,len(doc))
    check('pdf_16_by_9',all(abs(p.rect.width/p.rect.height-16/9)<.001 for p in doc))
    pdf_fonts=sorted({f[3] for p in doc for f in p.get_fonts()})
    check('pdf_contains_actual_K2D_and_ReadexPro',any('K2D' in f for f in pdf_fonts) and any('Readex' in f for f in pdf_fonts),pdf_fonts)
    check('pdf_overview_second_page','Presentation overview' in doc[1].get_text())
    check('pdf_contains_fivefold_result_without_animation','0.6108' in doc[positions[17]].get_text()
          and '95% CI' in doc[positions[17]].get_text())
    check('pdf_contains_louvain_backup','Louvain' in doc[-1].get_text()
          and 'BACKUP' in doc[-1].get_text())
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
