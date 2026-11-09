"""Record final PDF/text/font hashes and render changed pages plus neighbors."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
from PIL import Image, ImageDraw, ImageChops

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent/'report-checks'
VIS=OUT/'visual'
VIS.mkdir(exist_ok=True)
files={n:ROOT/'report/build'/n/(('content' if n.startswith('content') else n)+'.pdf')
       for n in ['content','content-twoside','bulletin-vi','bulletin-en','summary-vi','summary-en']}
needles=['Đối chiếu bổ sung xác nhận 1.702','Runner dùng ONNX Runtime',
         'Tám điều kiện được khóa','Clean parity đạt đồng thuận',
         'Với độ sáng nhân','Cả 15 giá trị Holm',
         'Phạm vi các phase có điều kiện','Phép bổ sung đã đánh giá tám',
         'Đánh giá bổ sung trên ONNX CPU','Additional ONNX CPU screening',
         'Chương trình ISDS chính thức xác nhận','The official ISDS program confirms']
records={}
for name,path in files.items():
    text_path=OUT/(name+'-text.txt')
    subprocess.run(['pdftotext','-layout',str(path),str(text_path)],check=True)
    info=subprocess.check_output(['pdfinfo',str(path)],text=True)
    count=int(re.search(r'Pages:\s+(\d+)',info)[1])
    fonts=subprocess.check_output(['pdffonts',str(path)],text=True)
    (OUT/(name+'-fonts.txt')).write_text(fonts)
    assert all(line.split()[-5]=='yes' for line in fonts.splitlines()[2:] if line.strip()), name
    pages=[' '.join(s.split()) for s in text_path.read_text().split('\f')]
    locators={needle:[i for i,t in enumerate(pages,1) if needle in t] for needle in needles}
    core=sorted({i for found in locators.values() for i in found}) if name.startswith('content') else list(range(1,count+1))
    neighbors=sorted({j for i in core for j in [i-1,i,i+1] if 1<=j<=count})
    dest=VIS/name;dest.mkdir(exist_ok=True)
    print('RENDER',name,count,'pages; detail',core,flush=True)
    subprocess.run(['pdftoppm','-r','30','-png',str(path),str(dest/'page')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    overview=sorted(dest.glob('page-*.png'))
    assert len(overview)==count
    thumbs=[]
    for i,p in enumerate(overview,1):
        with Image.open(p) as im:
            im=im.convert('RGB');im.thumbnail((210,300))
            thumb=Image.new('RGB',(220,324),'#eeeeee')
            thumb.paste(im,((220-im.width)//2,18));ImageDraw.Draw(thumb).text((5,3),str(i),fill='black')
            thumbs.append(thumb)
    for start in range(0,len(thumbs),36):
        sheet=Image.new('RGB',(220*6,324*6),'#bbbbbb')
        for j,thumb in enumerate(thumbs[start:start+36]):sheet.paste(thumb,((j%6)*220,(j//6)*324))
        sheet.save(VIS/(name+f'-overview-{start//36+1:02}.png'))
    detail=[]
    for page in core:
        prefix=VIS/f'{name}-detail-{page:03}'
        subprocess.run(['pdftoppm','-f',str(page),'-l',str(page),'-r','105','-singlefile','-png',str(path),str(prefix)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        detail.append(str(prefix.with_suffix('.png').relative_to(ROOT)))
    records[name]=dict(pdf=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        pages=count,text_sha256=hashlib.sha256(text_path.read_bytes()).hexdigest(),all_fonts_embedded=True,
        locators=locators,core_pages=core,neighbor_pages=neighbors,overview_all_pages=True,rendered_detail=detail)
a=sorted((VIS/'content').glob('page-*.png'));b=sorted((VIS/'content-twoside').glob('page-*.png'))
same=[];different=[]
for i,(p,q) in enumerate(zip(a,b),1):
    with Image.open(p) as im,Image.open(q) as jm:
        equal=im.size==jm.size and ImageChops.difference(im.convert('RGB'),jm.convert('RGB')).getbbox() is None
        (same if equal else different).append(i)
records['variant_comparison']=dict(dpi=30,equal_page_count=len(a)==len(b),identical_pages=same,different_pages=different)
(OUT/'pdf-inspection.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
print('Saved final PDF receipts; variant differing pages',different,flush=True)
