#!/usr/bin/env python3
"""Export with LibreOffice, then render actual PDF pages for inspection."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--soffice',default=shutil.which('libreoffice') or shutil.which('soffice'))
    a=p.parse_args()
    if not a.soffice:
        raise SystemExit('LibreOffice is needed: pass --soffice /path/to/soffice.')
    deck=BASE/'ISDS2026_Paper_6444_Conference_Deck.pptx'
    subprocess.run([a.soffice,'--headless','--convert-to',
                    'pdf:impress_pdf_Export:{"ExportHiddenSlides":{"type":"boolean","value":"true"}}',
                    '--outdir',str(BASE),str(deck)],check=True,timeout=180)
    pdf=deck.with_suffix('.pdf')
    doc=fitz.open(pdf)
    folder=BASE/'checks/slides';folder.mkdir(parents=True,exist_ok=True)
    for i,page in enumerate(doc,1):
        page.get_pixmap(matrix=fitz.Matrix(1280/page.rect.width,720/page.rect.height),alpha=False).save(folder/f'slide-{i:02d}.png')
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
    print(json.dumps({'pdf':str(pdf),'pages':len(doc),'preview':str(BASE/'checks/contact-sheet.png')}))


if __name__=='__main__':main()
