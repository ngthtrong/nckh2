#!/usr/bin/env python3
"""Apply print-size layout fixes while retaining figure labels and screenshots."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def reflow(path,labels):
    text=path.read_text()
    def change(match):
        block=match.group(0)
        if not any('\\label{'+label+'}' in block for label in labels):return block
        block=re.sub(r'\\begin\{figure\}(?:\[[^]]*\])?',r'\\begin{figure}[p]',block,count=1)
        block=re.sub(r'\\includegraphics\[[^]]*\]',r'\\includegraphics[width=\\linewidth]',block)
        block=block.replace('\\centering','\\centering\n\\setlength{\\abovecaptionskip}{4pt}',1)
        return '\\begin{landscape}\n'+block+'\n\\end{landscape}'
    text=re.sub(r'\\begin\{figure\}.*?\\end\{figure\}',change,text,flags=re.S)
    path.write_text(text)


def main():
    # One-time migration. Refuse a second application before writing any file.
    functional=ROOT/'chapters/03-system/sections/functional-requirements.tex'
    if '\\begin{landscape}' in functional.read_text():
        raise SystemExit('Figure layout migration is already applied; no files changed.')
    arch=ROOT/'chapters/03-system/sections/architecture.tex'
    text=arch.read_text().replace('../paper/figures/pipeline_v2.pdf','research_pipeline_report.pdf')
    text=text.replace('Nét đứt thể hiện liên hệ được mã ứng dụng kiểm soát; DDL hiện chưa khai báo ràng buộc khóa ngoại cho các liên hệ này.',
                      'Sơ đồ dùng Crow\'s Foot; REF đánh dấu tham chiếu logic. Nét đứt là quan hệ không định danh vì khóa chính của thực thể con độc lập với khóa của thực thể cha; DDL hiện chưa khai báo ràng buộc FOREIGN KEY. Nullability của cột được giữ theo DDL, gồm trường operator\\_id trong sessions.')
    arch.write_text(text)
    reflow(arch,['fig:research-pipeline'])
    reflow(ROOT/'chapters/03-system/sections/functional-requirements.tex',
           ['fig:usecase-overall','fig:usecase-mobile','fig:usecase-dashboard'])
    reflow(ROOT/'chapters/03-system/sections/synchronization.tex',['fig:flow-track-status','fig:flow-create-report'])
    impl=ROOT/'chapters/03-system/sections/implementation.tex'
    text=impl.read_text()
    def machine(m):
        b=m.group(0)
        if '\\label{fig:status-flow}' not in b:return b
        return re.sub(r'\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}',r'\\includegraphics[width=\\textwidth]{status_machine.pdf}',b,flags=re.S)
    text=re.sub(r'\\begin\{figure\}.*?\\end\{figure\}',machine,text,flags=re.S);impl.write_text(text)
    reflow(impl,['fig:deployment-infrastructure','fig:flow-adaptive-send'])
    overview=ROOT/'chapters/02-data-methods/sections/overview.tex'
    text=overview.read_text().replace('font=\\footnotesize,node distance','font=\\small,node distance').replace('font=\\scriptsize\\itshape','font=\\footnotesize\\itshape')
    overview.write_text(text)
    image=ROOT/'chapters/02-data-methods/sections/image-design.tex'
    text=image.read_text()
    for n in ['training-loss','training-metrics','validation-recall']:text=text.replace(n+'.png',n+'.pdf')
    image.write_text(text);reflow(image,['fig:flow-ai-training-optimization'])
    reflow(ROOT/'chapters/02-data-methods/sections/methods.tex',['fig:flow-clustering-priority'])
    results=ROOT/'chapters/04-evaluation/sections/results.tex'
    text=results.read_text()
    for n in ['image-confusion','image-confusion-normalized','image-examples']:text=text.replace(n+'.png',n+'.pdf')
    # Normalized confusion has no label; add one for reliable auditing.
    text=text.replace('\\caption{Ma trận nhầm lẫn test chuẩn hóa theo lớp thật của model seed 1024}',
                      '\\caption{Ma trận nhầm lẫn test chuẩn hóa theo lớp thật của model seed 1024}\\label{fig:image-confusion-normalized}')
    results.write_text(text)
    reflow(results,['fig:image-examples','fig:confidence-calibration','fig:compression-tradeoffs','fig:rq3-conditions-report'])
    # User interface figures retain their original grouping and page layout.


if __name__=='__main__':main()
