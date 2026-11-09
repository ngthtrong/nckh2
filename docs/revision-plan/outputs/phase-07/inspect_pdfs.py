"""Render all pages at 36dpi, select changed text with neighbors, record receipts."""
from pathlib import Path
import subprocess,json,hashlib,re
from PIL import Image,ImageOps,ImageDraw,ImageChops
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent;VIS=OUT/'visual'
files={'content':'report/build/content/content.pdf','content-twoside':'report/build/content-twoside/content.pdf','bulletin-vi':'report/build/bulletin-vi/bulletin-vi.pdf','bulletin-en':'report/build/bulletin-en/bulletin-en.pdf','summary-vi':'report/build/summary-vi/summary-vi.pdf','summary-en':'report/build/summary-en/summary-en.pdf'}
receipts={}
for name,rel in files.items():
 p=ROOT/rel;dest=VIS/name;dest.mkdir(parents=True,exist_ok=True)
 text=OUT/(name+'-text.txt');proc=subprocess.run(['pdftotext','-layout',str(p),str(text)],capture_output=True,text=True);assert proc.returncode==0 and not proc.stderr,(name,proc.stderr)
 meta=subprocess.check_output(['pdfinfo',str(p)],text=True);n=int(re.search(r'Pages:\s+(\d+)',meta)[1]);fonts=subprocess.check_output(['pdffonts',str(p)],text=True);(OUT/(name+'-fonts.txt')).write_text(fonts)
 print('RENDER',name,n,flush=True)
 proc=subprocess.run(['pdftoppm','-r','36','-png',str(p),str(dest/'page')],capture_output=True,text=True);assert proc.returncode==0 and not proc.stderr,(name,proc.stderr)
 pages=sorted(dest.glob('page-*.png'));assert len(pages)==n
 thumbs=[];blank=[];sizes=[]
 for i,path in enumerate(pages,1):
  with Image.open(path) as im:
   im=im.convert('RGB');sizes.append(list(im.size));gray=im.convert('L');dark=sum(v for j,v in enumerate(gray.histogram()) if j<245)/ (gray.width*gray.height)
   if dark<.0005:blank.append(i)
   box=Image.new('RGB',(230,345),'#dddddd');small=im.copy();small.thumbnail((224,320));box.paste(small,((230-small.width)//2,18));ImageDraw.Draw(box).text((8,2),f'{name}: {i}',fill='black');thumbs.append(box)
 for start in range(0,len(thumbs),30):
  selected=thumbs[start:start+30];sheet=Image.new('RGB',(230*6,345*5),'#bbbbbb')
  for j,thumb in enumerate(selected):sheet.paste(thumb,((j%6)*230,(j//6)*345))
  sheet.save(VIS/f'{name}-contact-{start//30+1:02}.png')
 receipts[name]={'pdf':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pages':n,'pdftotext_exit':0,'pdftotext_stderr':'','overview_dpi':36,'overview_page_count':n,'near_blank_pages_threshold_0_0005':blank,'page_pixel_sizes':sorted({tuple(s) for s in sizes}),'all_fonts_embedded':all(line.split()[-5]=='yes' for line in fonts.splitlines()[2:] if len(line.split())>=8)}
# Pixel comparison of the two variants, after fixed form margins in repository template.
a=sorted((VIS/'content').glob('page-*.png'));b=sorted((VIS/'content-twoside').glob('page-*.png'));same=[];different=[]
for i,(p,q) in enumerate(zip(a,b),1):
 with Image.open(p) as im,Image.open(q) as jm:
  eq=im.size==jm.size and ImageChops.difference(im.convert('RGB'),jm.convert('RGB')).getbbox() is None
  (same if eq else different).append(i)
receipts['variant_comparison']={'dpi':36,'page_count_equal':len(a)==len(b),'identical_pages':same,'different_pages':different}
# Locate changed paragraphs, excluding TOC-only hits by requiring text fragments.
needles=['Đặc điểm tệp gốc','Hash byte của CSV LR','Trả lời RQ1','Giới hạn replay thống kê RQ2','Trả lời RQ2','Trả lời RQ3','Phạm vi kiểm chứng bổ sung','Trạng thái xác minh bằng chứng','Hướng nghiên cứu tiếp theo','Bài báo được ghi nhận đã công bố','chưa chứng minh hoàn thành cam kết nghiên cứu','raw JSON/CSV/log tương ứng chưa có','tích hợp bằng công thức và heuristic','Căn cứ dấu hiệu','Backend lưu payload gốc','Phạm vi của phương pháp','Phân tích lỗi và phạm vi suy luận','IP chính xác hơn GPS','Nghiên cứu tiếp nhận âm thanh']
page_text=[re.sub(r'\s+', ' ', t) for t in (OUT/'content-text.txt').read_text().split('\f')];loc={}
for needle in needles:
 found=[i for i,t in enumerate(page_text,1) if needle.lower() in t.lower()]
 loc[needle]=found
core=sorted({i for v in loc.values() for i in v});neighbors=sorted({j for i in core for j in [i-1,i,i+1] if 1<=j<=len(a)})
receipts['changed_text_locators']=loc;receipts['detail_pages']=core;receipts['changed_pages_plus_neighbors']=neighbors
# High-resolution selected evidence, both print variants; all standalone forms.
for name in ['content','content-twoside']:
 for i in core:
  proc=subprocess.run(['pdftoppm','-f',str(i),'-l',str(i),'-r','110','-singlefile','-png',str(ROOT/files[name]),str(VIS/f'{name}-detail-{i:03}')],capture_output=True,text=True);assert proc.returncode==0 and not proc.stderr
for name in ['bulletin-vi','bulletin-en','summary-vi','summary-en']:
 dest=VIS/name
 for i in range(1,receipts[name]['pages']+1):
  proc=subprocess.run(['pdftoppm','-f',str(i),'-l',str(i),'-r','110','-singlefile','-png',str(ROOT/files[name]),str(VIS/f'{name}-detail-{i:03}')],capture_output=True,text=True);assert proc.returncode==0 and not proc.stderr
(OUT/'pdf-inspection.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n');print('PDFs verified/rendered; detail pages',core,'with neighbor overview',neighbors,flush=True)
