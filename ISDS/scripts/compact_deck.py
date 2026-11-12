#!/usr/bin/env python3
"""Compact the current editable deck, preserving untouched author edits."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

from pptx import Presentation
from pptx.util import Pt

from build_deck import (OUT, ROOT, BLUE, TEAL, ORANGE, INK, MUTED, PALE,
                        LINE, FONT, text, box, source)
from revise_deck import prepare, replace_text

DECK=OUT/'ISDS2026_Paper_6444_Conference_Deck.pptx'
ORDER=[1,2,3,4,11,5,7,8,10,12,13,16,17,18,19,20,21,22,24,25,26,9]
MERGES={7:[6,7],13:[13,14,15],22:[22,23]}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def datasets(s):
    # Retain the comparison layout and all existing suite counts.
    replace_text(list(s.shapes)[0],'Two experimental suites for separate stage tests')
    replace_text(list(s.shapes)[1],
                 'Generator 3.0: geographically anchored, semi-synthetic · Candidate 4.1: fully synthetic')
    replace_text(list(s.shapes)[2],'DATA / RQ1–RQ3')
    for sh in list(s.shapes):
        if sh.name=='Compact geographic anchors':
            sh._element.getparent().remove(sh._element)
    text(s,'RQ1 geographic anchors: Copernicus EMSR848 · OpenStreetMap · WorldPop 2025',
         .99,3.59,11.48,.29,12.4,MUTED,name='Compact geographic anchors')


def metrics(s):
    prepare(s,'Three primary evaluation metrics',
            'Separate endpoints for clustering, ranking and simulated dispatch', 'EVALUATION / METRICS')
    rows=[('ARI','HIGHER IS BETTER',BLUE,
           'Partition agreement, corrected for chance.\n1 = identical; ≈ 0 = chance; negative values are possible.'),
          ('NDCG@5','HIGHER IS BETTER',TEAL,
           'Top-five ranking by independent simulated benefit.\nPosition-discounted and normalized; 1 = the ideal ordering.'),
          ('Simulated harm','LOWER IS BETTER',ORANGE,
           'Synthetic lateness and service costs, in model units.\nThis is not observed injury, lives lost or monetary damage.')]
    for i,(name,direction,color,body) in enumerate(rows):
        y=1.87+i*1.43
        box(s,.88,y,11.66,1.25,PALE,LINE,True)
        text(s,name,1.07,y+.18,2.72,.43,22,color,True)
        text(s,direction,1.08,y+.83,2.70,.24,12,MUTED)
        text(s,body,4.05,y+.18,8.20,.91,18.5)
    source(s,'Merged original metric slides 13–15. ARI is chance-adjusted partition agreement; NDCG uses linear independent-benefit gains; harm is synthetic model units. The response-time definition of deadline misses remains in the talk track and results.')


def conclusion(s):
    prepare(s,'Conclusion and future work',
            'Local safeguards require separate validation at each downstream stage', 'CONCLUSION / NEXT STEPS')
    text(s,'Stage safeguards do not establish\nbetter dispatch.',
         1.00,1.91,7.25,1.03,26,BLUE,True)
    conclusions=[('Clustering','Conditional edge bound; no established\nProduct composition advantage.',BLUE),
                 ('Ranking','Fixed-family/input copy invariance;\nweak benefit alignment.',TEAL),
                 ('Dispatch','Safeguards do not ensure\nbetter simulated outcomes.',ORANGE)]
    for i,(heading,body,color) in enumerate(conclusions):
        y=3.20+i*.95
        text(s,heading,1.02,y,2.14,.43,21,color,True)
        text(s,body,3.29,y,4.99,.74,17.5)
    box(s,8.94,1.91,3.62,4.17,PALE,LINE,True)
    text(s,'Future work',9.15,2.14,3.18,.47,22,BLUE,True)
    next_steps=['1  Real-report linkage','2  Expert + source checks',
                '3  Transfer + missingness','4  Joint ranking / dispatch']
    for i,value in enumerate(next_steps):
        text(s,value,9.16,2.95+i*.69,3.16,.51,16.5)
    source(s,'Merged original conclusion and future-work slides 22–23. Future work remains proposed: traceable report linkage, expert priorities and source/headcount checks, transfer/missingness, and joint ranking/scheduling evaluation. No field validity is established.')


def fit_existing_labels(by_original):
    """Keep author geometry, fixing two confirmed wrapped-label collisions."""
    overview=by_original[2]
    for i in (6,9,12,15,18):
        for paragraph in list(overview.shapes)[i].text_frame.paragraphs:
            for run in paragraph.runs:
                if run.font.size and run.font.size.pt>21:run.font.size=Pt(21)
    for shape in by_original[17].shapes:
        if shape.has_text_frame and shape.text=='5× copies · Product ΔARI' and shape.width<3*914400:
            for paragraph in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    if run.font.size and run.font.size.pt>14:run.font.size=Pt(14)


def update_talk_track(old_index):
    path=OUT/'research/talk-track.json'
    old={r['slide']:r for r in old_index}
    content=json.loads(path.read_text())
    by_original={r.get('original_slide',old[r['slide']]['original_slide']):r for r in content}
    replacements={
      7:("These two suites test separate stages. Generator 3.0 has 80 runs, 16 latent incidents per run, and 26,288 reports. Its geographic and historical anchors come from Copernicus EMSR848, OpenStreetMap, and WorldPop 2025, while the incidents, reports, copies, attacks, and labels remain simulated. Candidate 4.1 is a separate, fully synthetic suite with 80 datasets and 30,229 reports. It supplies independent benefit, deadline, service, and harm parameters for RQ2 and RQ3. RQ2 uses oracle grouping to isolate ranking, while RQ3 uses predicted clusters for scheduling. These are complementary tests on separate samples, not one common-sample validation chain.",
         "Hai bộ dữ liệu này kiểm tra những giai đoạn khác nhau. Generator 3.0 gồm 80 run, mỗi run có 16 sự cố tiềm ẩn, với tổng cộng 26.288 báo cáo. Các mốc địa lý và lịch sử được lấy từ Copernicus EMSR848, OpenStreetMap và WorldPop 2025, còn sự cố, báo cáo, bản sao, tấn công và nhãn vẫn được mô phỏng. Candidate 4.1 là bộ hoàn toàn tổng hợp riêng, gồm 80 bộ dữ liệu và 30.229 báo cáo. Bộ này cung cấp các tham số độc lập về lợi ích, hạn đáp ứng, phục vụ và tổn hại cho RQ2 và RQ3. RQ2 dùng nhóm theo nhãn chuẩn để tách ảnh hưởng của xếp hạng; RQ3 dùng cụm dự đoán để lập lịch. Vì vậy, đây là các phép kiểm tra bổ sung trên những mẫu riêng, không phải một chuỗi kiểm chứng trên cùng mẫu."),
      13:("We use three primary metrics for three different endpoints. ARI compares predicted clusters with withheld incident linkage, correcting agreement for chance. One means identical partitions, a value near zero represents chance-level agreement, and negative values are possible. ARI is not the percentage of reports classified correctly. NDCG at five measures the top-five ranking by independently simulated benefit, with linear gains, position discounting, and normalization by the ideal ordering. Higher ARI and NDCG are better. Simulated harm measures lateness and service costs in model units; lower is better. It is not observed injury or loss. The complementary deadline-miss endpoint compares response time with each incident's deadline.",
          "Chúng tôi sử dụng ba độ đo chính cho ba mục tiêu khác nhau. ARI so sánh các cụm dự đoán với liên kết sự cố được giữ riêng và hiệu chỉnh mức phù hợp do ngẫu nhiên. Giá trị 1 tương ứng với hai phân hoạch giống hệt nhau, gần 0 là mức kỳ vọng do ngẫu nhiên và giá trị âm vẫn có thể xuất hiện. ARI không phải tỷ lệ báo cáo được phân loại đúng. NDCG tại năm đo chất lượng thứ tự năm sự cố đầu theo lợi ích mô phỏng độc lập, dùng lợi ích tuyến tính, chiết khấu theo vị trí và chuẩn hóa theo thứ tự lý tưởng. ARI và NDCG càng cao càng tốt. Tổn hại mô phỏng phản ánh chi phí chậm đáp ứng và phục vụ bằng đơn vị của mô hình; càng thấp càng tốt. Đây không phải thương vong hoặc thiệt hại quan sát được. Chỉ số trễ hạn bổ sung so sánh thời gian đáp ứng với hạn riêng của từng sự cố."),
      22:("The main conclusion is that stage safeguards do not establish better dispatch. Product provides a conditional edge bound, but no clustering composition advantage is established. Family-wise priority is invariant to exact copies under fixed grouping and inputs, while benefit alignment remains weak. These properties do not ensure better simulated outcomes or establish field effectiveness. Four next steps follow: collect traceable real reports with independently annotated incident linkage; validate priorities, sources, and headcounts with domain experts; test transfer and missing information; and evaluate ranking jointly with travel, service, and resource constraints. These are proposed validation steps, not completed results.",
          "Kết luận chính là những bảo đảm ở từng giai đoạn chưa xác lập được hiệu quả điều phối tốt hơn. Product cung cấp giới hạn cạnh có điều kiện, nhưng chưa chứng minh được ưu thế phân cụm của cơ chế kết hợp. Điểm ưu tiên theo nhóm bất biến trước bản sao chính xác khi cách gom nhóm và đầu vào được giữ cố định, trong khi mức phù hợp với lợi ích vẫn yếu. Các tính chất này không bảo đảm kết quả mô phỏng tốt hơn hoặc xác nhận hiệu quả thực địa. Bốn bước tiếp theo là thu thập báo cáo thực có thể truy nguyên và gán nhãn liên kết sự cố độc lập; kiểm chứng ưu tiên, nguồn và số người cùng chuyên gia; kiểm tra chuyển bối cảnh và thiếu thông tin; cuối cùng là đánh giá xếp hạng cùng với di chuyển, phục vụ và ràng buộc nguồn lực. Đây là những bước kiểm chứng được đề xuất, chưa phải kết quả đã hoàn thành.")}
    updated=[]
    for number,original in enumerate(ORDER,1):
        row=by_original[original]
        en,vi=replacements.get(original,(row['english'],row['vietnamese']))
        updated.append({'slide':number,'original_slide':original,
                        'role':'backup' if original==9 else 'main',
                        'english':en,'vietnamese':vi})
    path.write_text(json.dumps(updated,ensure_ascii=False,indent=2)+'\n')


def compact():
    before=sha(DECK)
    prs=Presentation(DECK)
    index_path=OUT/'slide-index.json'
    previous_index=json.loads(index_path.read_text())
    index_by_number={r['slide']:r for r in previous_index}
    by_original={}
    for number,s in enumerate(prs.slides,1):
        name=s._element.cSld.get('name','')
        original=int(name.rsplit('-',1)[1]) if name.startswith('ISDS6444-source-') else index_by_number[number]['original_slide']
        by_original[original]=s
        s._element.cSld.set('name',f'ISDS6444-source-{original}')
    if set(by_original) not in (set(range(1,27)),set(ORDER)):
        raise ValueError('Expected the existing full or compact ISDS deck')
    datasets(by_original[7]);metrics(by_original[13]);conclusion(by_original[22])
    fit_existing_labels(by_original)
    # Louvain is a hidden Q&A backup, after the closing slide.
    backup=by_original[9]
    replace_text(list(backup.shapes)[2],'BACKUP / LOUVAIN')
    # Remove only the four slides absorbed into the three merged pages.
    original_by_slide_id={s.slide_id:k for k,s in by_original.items()}
    for element in list(prs.slides._sldIdLst):
        original=original_by_slide_id[int(element.id)]
        if original not in ORDER:
            prs.part.drop_rel(element.rId)
            prs.slides._sldIdLst.remove(element)
    elements={int(e.id):e for e in prs.slides._sldIdLst}
    for original in ORDER:
        prs.slides._sldIdLst.append(elements[by_original[original].slide_id])
    source_path=OUT/'research/slide-sources.json'
    prior_sources={r['original_slide']:r for r in json.loads(source_path.read_text())}
    index=[];sources=[]
    for number,original in enumerate(ORDER,1):
        s=by_original[original];is_backup=original==9
        s._element.set('show','0' if is_backup else '1')
        if original not in (1,26):replace_text(list(s.shapes)[4],f'{number:02d}')
        title=next((sh.text for sh in s.shapes if sh.name=='Slide title'),
                   'Title' if original==1 else 'Thank you — Questions and discussion')
        entry={'slide':number,'original_slide':original,'title':title,
               'role':'backup' if is_backup else 'main','hidden':is_backup,
               'merged_original_slides':MERGES.get(original,[original])}
        index.append(entry)
        notes=[prior_sources[k]['source_notes'] for k in MERGES.get(original,[original]) if k in prior_sources]
        source_notes='\n\n'.join(dict.fromkeys(n for n in notes if n))
        if getattr(s,'_source_note',None):source_notes=s._source_note
        sources.append({**entry,'source_notes':source_notes})
        used=set(s._element.xpath('//@r:embed'))
        for rel in list(s.part.rels.values()):
            if rel.reltype.endswith('/image') and rel.rId not in used:s.part.drop_rel(rel.rId)
    index_path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
    source_path.write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
    revision_path=OUT/'research/revision-content.json'
    revision=json.loads(revision_path.read_text())
    revision.setdefault('source_order_26',revision['order'])
    revision.update({'order':ORDER,'main_slide_count':21,'backup_original_ids':[9],
                     'merged_original_ids':{str(k):v for k,v in MERGES.items()},
                     'compaction_date':'2026-11-11'})
    revision_path.write_text(json.dumps(revision,ensure_ascii=False,indent=2)+'\n')
    update_talk_track(previous_index)
    subprocess.run([sys.executable,str(OUT/'research/write_notes.py')],check=True)
    notes=json.loads((OUT/'research/speaker-notes.json').read_text())
    for s,row in zip(prs.slides,notes):
        s.notes_slide.notes_text_frame.text=row['notes']
        for paragraph in s.notes_slide.notes_text_frame.paragraphs:
            for run in paragraph.runs:run.font.name=FONT;run.font.size=Pt(12)
    prs.save(DECK)
    path=OUT/'build-manifest.json';manifest=json.loads(path.read_text())
    manifest.pop('pdf_sha256',None)
    historical=manifest.get('compaction',{})
    manifest.update({'slides':22,'main_slides':21,'backup_slides':1,'backup_slide_numbers':[22],
                     'deck_sha256':sha(DECK),'notes_sha256':sha(OUT/'research/speaker-notes.json'),
                     'talk_track_sha256':sha(OUT/'research/talk-track.json'),
                     'speaker_script_sha256':sha(OUT/'speaker-notes.md'),
                     'notes_generator_sha256':sha(OUT/'research/write_notes.py'),
                     'slide_sources_sha256':sha(source_path),
                     'speaker_script_order':'21 main slides plus one marked backup in English, then Vietnamese; no citations or timing metadata',
                     'scripts':{str(p.relative_to(ROOT)):sha(p) for p in sorted((OUT/'scripts').glob('*.py'))},
                     'compaction':{'date':'2026-11-11','input_deck_sha256':historical.get('input_deck_sha256',before),
                         'original_ids_in_order':ORDER,'merged_original_ids':MERGES,
                         'backup_original_id':9,'backup_hidden_in_slide_show':True,
                         'preserved_author_edits':'Unmerged slides retain current artwork, geometry and text, except updated page numbers and the backup section label.',
                         'text_fit_adjustments':'Overview headings capped at 21 pt; narrow stress delta label capped at 14 pt. Existing wording, font families and geometry preserved.',
                         'benchmark_execution':False}})
    manifest['revision']['content_sha256']=sha(revision_path)
    manifest['revision']['original_slide_order']=ORDER
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(f'{DECK}: 21 main slides + 1 hidden Louvain backup; merged data, metrics and conclusion.')


if __name__=='__main__':compact()
