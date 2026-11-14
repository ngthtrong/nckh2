#!/usr/bin/env python3
"""Export with LibreOffice, then render actual PDF pages for inspection."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from xml.sax.saxutils import escape

import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parents[1] / '15min'


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--soffice',default=shutil.which('libreoffice') or shutil.which('soffice'))
    a=p.parse_args()
    if not a.soffice:
        raise SystemExit('LibreOffice is needed: pass --soffice /path/to/soffice.')
    deck=BASE/'ISDS2026_Paper_6444_15min.pptx'
    pdf=deck.with_suffix('.pdf')
    # Use only the bundled static fonts, without installing them system-wide.
    # A separate export directory prevents a failed conversion from silently
    # leaving an old PDF in place and being reported as a successful render.
    with tempfile.TemporaryDirectory(prefix='isds-render-') as tmp:
        temp=Path(tmp);fontdir=temp/'fonts';fontdir.mkdir()
        for path in (BASE.parent/'fonts').rglob('*.ttf'):
            if '[' not in path.name:
                (fontdir/path.name).symlink_to(path.resolve())
        config=temp/'fonts.conf'
        config.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd">'
            '<fontconfig><include ignore_missing="yes">/etc/fonts/fonts.conf</include>'
            f'<dir>{escape(str(fontdir))}</dir><cachedir>{escape(str(temp/"cache"))}</cachedir></fontconfig>')
        env=dict(os.environ,FONTCONFIG_FILE=str(config),SAL_USE_VCLPLUGIN='svp')
        font_checks=[]
        for requested in ('K2D','K2D:style=Bold','Readex Pro','Readex Pro:style=Bold'):
            match=subprocess.check_output(['fc-match','--format','%{family}|%{style}|%{file}',requested],env=env,text=True)
            family,style,file=match.split('|',2)
            font_checks.append({'requested':requested,'matched_family':family,'matched_style':style,
                                'file':str(Path(file).resolve()),
                                'sha256':hashlib.sha256(Path(file).read_bytes()).hexdigest()})
        subprocess.run([a.soffice,'--headless','--convert-to',
                        'pdf:impress_pdf_Export:{"ExportHiddenSlides":{"type":"boolean","value":"true"}}',
                        '--outdir',str(temp),str(deck)],check=True,timeout=180,env=env)
        fresh=temp/pdf.name
        if not fresh.exists() or fresh.stat().st_size==0:
            raise SystemExit('LibreOffice did not produce a fresh PDF.')
        shutil.copy2(fresh,pdf)
        (BASE/'checks/font-verification.json').write_text(json.dumps(
            {'font_source':'Bundled static fonts via a temporary Fontconfig configuration',
             'checks':font_checks},ensure_ascii=False,indent=2)+'\n')
    doc=fitz.open(pdf)
    folder=BASE/'checks/slides';folder.mkdir(parents=True,exist_ok=True)
    for old in folder.glob('slide-*.png'):
        if int(old.stem.rsplit('-',1)[1])>len(doc):old.unlink()
    text_layout=[]
    for i,page in enumerate(doc,1):
        page.get_pixmap(matrix=fitz.Matrix(1280/page.rect.width,720/page.rect.height),alpha=False).save(folder/f'slide-{i:02d}.png')
        spans=[{key:span[key] for key in ('text','size','bbox','font')}
               for block in page.get_text('dict')['blocks']
               for ln in block.get('lines',[]) for span in ln['spans']]
        text_layout.append({'slide':i,'width':page.rect.width,'height':page.rect.height,
                            'text_characters':len(page.get_text()),'spans':spans})
    (BASE/'checks/pdf-text-layout.json').write_text(json.dumps(text_layout,ensure_ascii=False,indent=2)+'\n')
    cols,tw,th,pad,label=4,480,270,16,28
    rows=(len(doc)+cols-1)//cols
    canvas=Image.new('RGB',(pad+cols*(tw+pad),pad+rows*(th+label+pad)),'#DCE5EC')
    draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
    for i in range(len(doc)):
        x=pad+(i%cols)*(tw+pad);y=pad+(i//cols)*(th+label+pad)
        draw.text((x,y),f'{i+1:02d}',fill='#33485C',font=font)
        im=Image.open(folder/f'slide-{i+1:02d}.png').convert('RGB')
        im.thumbnail((tw,th))
        canvas.paste(im,(x,y+label))
    canvas.save(BASE/'checks/contact-sheet.png')
    # Refresh the existing six-slide review sheets alongside the overview.
    review=BASE/'checks/review';review.mkdir(exist_ok=True)
    for old in review.glob('slides-*.png'):
        if int(old.stem.rsplit('-',1)[1])>len(doc):old.unlink()
    for start in range(0,len(doc),6):
        count=min(6,len(doc)-start);rows=(count+1)//2
        sheet=Image.new('RGB',(1952,rows*596+16),'#DCE5EC')
        draw=ImageDraw.Draw(sheet)
        for j in range(count):
            x=16+(j%2)*976;y=16+(j//2)*596
            draw.text((x,y),f'{start+j+1:02d}',fill='#33485C',font=font)
            im=Image.open(folder/f'slide-{start+j+1:02d}.png').convert('RGB')
            im.thumbnail((960,540));sheet.paste(im,(x,y+28))
        sheet.save(review/f'slides-{start+1:02d}.png')
    manifest_path=BASE/'build-manifest.json'
    manifest=json.loads(manifest_path.read_text())
    manifest['pdf_sha256']=hashlib.sha256(pdf.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'pdf':str(pdf),'pages':len(doc),'preview':str(BASE/'checks/contact-sheet.png')}))


if __name__=='__main__':main()
