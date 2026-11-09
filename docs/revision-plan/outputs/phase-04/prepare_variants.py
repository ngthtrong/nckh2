"""Prepare locked corruption inputs only. No inference, labels or model edits."""
from pathlib import Path
import csv,json,hashlib,argparse,io
from PIL import Image,ImageOps,ImageEnhance,ImageFilter
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--validation-smoke',action='store_true',required=True);args=p.parse_args()
split=list(csv.DictReader((ROOT/'products/fe/model/Edge Ai/split_train_val_test_mobilenetv3_large.csv').open(encoding='utf-8-sig')))
r=next(r for r in split if r['split']=='val');source=ROOT/'products/fe/model/Dataset_Flood'/r['relative_path'];raw=source.read_bytes();sid=hashlib.sha1(r['relative_path'].replace('\\','/').encode()).hexdigest()[:12]
with Image.open(source) as im:clean=ImageOps.exif_transpose(im).convert('RGB')
variants={'clean':clean}
for q in [50,20]:
 b=io.BytesIO();clean.save(b,format='JPEG',quality=q);b.seek(0)
 with Image.open(b) as im:variants[f'jpeg_q{q}']=im.convert('RGB').copy()
for edge in [128,64]:
 scale=min(1.,edge/min(clean.size));size=tuple(max(1,round(x*scale)) for x in clean.size);variants[f'short_edge_{edge}']=clean.resize(size,Image.Resampling.BILINEAR)
for sigma in [1,2]:variants[f'blur_sigma_{sigma}']=clean.filter(ImageFilter.GaussianBlur(radius=sigma))
for exposure in [.7,.4]:variants[f'exposure_{exposure}']=ImageEnhance.Brightness(clean).enhance(exposure)
dest=OUT/'validation-smoke';dest.mkdir(exist_ok=True);rows=[]
for name,im in variants.items():
 path=dest/(sid+'__'+name+'.png');im.save(path);rows.append({'scope':'VALIDATION_PREPARATION_ONLY_NO_INFERENCE','parent_id':sid,'parent_path':r['relative_path'],'parent_sha256':hashlib.sha256(raw).hexdigest(),'split':'val','label':r['label'],'variant':name,'width':im.width,'height':im.height,'variant_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'path':str(path.relative_to(ROOT)),'label_validity':'assumed for synthetic corruption; requires review before inference interpretation'})
with (OUT/'variant-manifest.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
assert len(rows)==9 and all(x['split']=='val' for x in rows)
print('9 validation-only prepared inputs; 0 predictions; no test image altered.')
