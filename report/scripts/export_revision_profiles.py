#!/usr/bin/env python3
"""Export the audited header statistics. Does not run a model or edit raw images."""
from pathlib import Path
import csv,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'docs/revision-plan/outputs/phase-02/image-profile.csv'
if not P.is_file():raise SystemExit('Missing P02 image-profile.csv; run the read-only P02 analysis first.')
rows=list(csv.DictReader(P.open()))
chosen=[r for r in rows if r['split']=='all' and r['class']!='all']
assert len(chosen)==4 and sum(int(r['n']) for r in chosen)==1702
lines=[r'\begin{table}[htbp]\centering\small',r'\caption{Đặc điểm ảnh gốc theo lớp, tính từ header của 1.702 tệp}\label{tab:image-profile}',r'\begin{tabular}{lrrrr}',r'\toprule Lớp & Số ảnh & Rộng trung vị & Cao trung vị & Dung lượng trung vị (KiB) \\',r'\midrule']
for r in chosen:
 lines.append(r['class'].replace('_',r'\_')+' & '+r['n']+' & '+format(float(r['width_q50']),'g').replace('.',',')+' & '+format(float(r['height_q50']),'g').replace('.',',')+' & '+f"{float(r['bytes_q50'])/1024:.2f}".replace('.',',')+r' \\')
lines.extend([r'\bottomrule\end{tabular}',r'\end{table}'])
p=ROOT/'report/generated/tables/image-profile.tex';p.write_text('\n'.join(lines)+'\n')
fs=[P,Path(__file__),ROOT/'docs/revision-plan/outputs/phase-02/source-hashes.json']
(ROOT/'report/generated/revision-profile-provenance.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in fs},indent=2)+'\n')
print('Exported audited image profile table (no inference).')
