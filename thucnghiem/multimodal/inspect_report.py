"""Render current PDFs into a fresh review bundle; record inspection locators."""
from __future__ import annotations

import re
import subprocess

from PIL import Image, ImageChops, ImageDraw

from common import OUT, ROOT, digest, write_json


def main():
    dest = OUT / 'report-checks'
    dest.mkdir(exist_ok=True)
    needles = ['Pilot đa phương thức', 'Pilot CrisisMMD công khai bổ sung',
               'A separate English CrisisMMD pilot', 'Đợt bổ sung đã huấn luyện',
               'fusion tuyến tính trên CrisisMMD', 'Fusion đạt macro-F1']
    records = {}
    for name in ['content', 'content-twoside', 'bulletin-vi', 'bulletin-en', 'summary-vi', 'summary-en']:
        path = ROOT / 'report/build' / name / (('content' if name.startswith('content') else name) + '.pdf')
        text = subprocess.check_output(['pdftotext', '-layout', str(path), '-'], text=True)
        (dest / (name + '.txt')).write_text(text)
        info = subprocess.check_output(['pdfinfo', str(path)], text=True)
        count = int(re.search(r'Pages:\s+(\d+)', info)[1])
        fonts = subprocess.check_output(['pdffonts', str(path)], text=True)
        (dest / (name + '-fonts.txt')).write_text(fonts)
        assert all(row.split()[-5] == 'yes' for row in fonts.splitlines()[2:] if row.strip()), name
        pages = [' '.join(page.split()) for page in text.split('\f')][:count]
        locators = {term: [i for i, page in enumerate(pages, 1) if term in page] for term in needles}
        core = sorted({i for values in locators.values() for i in values}) if name.startswith('content') else list(range(1, count + 1))
        neighbors = sorted({j for i in core for j in [i - 1, i, i + 1] if 1 <= j <= count})
        render = dest / name
        render.mkdir(exist_ok=True)
        subprocess.run(['pdftoppm', '-r', '30', '-png', str(path), str(render / 'page')],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        images = sorted(render.glob('page-*.png'))
        assert len(images) == count
        sheets = []
        for start in range(0, count, 36):
            sheet = Image.new('RGB', (1320, 1944), '#bbbbbb')
            for offset, image in enumerate(images[start:start + 36]):
                with Image.open(image) as im:
                    im = im.convert('RGB')
                    im.thumbnail((210, 300))
                    thumb = Image.new('RGB', (220, 324), 'white')
                    thumb.paste(im, ((220 - im.width) // 2, 18))
                    ImageDraw.Draw(thumb).text((3, 3), str(start + offset + 1), fill='black')
                    sheet.paste(thumb, ((offset % 6) * 220, (offset // 6) * 324))
            target = dest / f'{name}-overview-{start // 36 + 1}.png'
            sheet.save(target)
            sheets.append(str(target.relative_to(ROOT)))
        details = []
        for page in neighbors:
            target = dest / f'{name}-detail-{page:03}'
            subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page), '-r', '95', '-singlefile',
                            '-png', str(path), str(target)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            details.append(str(target.with_suffix('.png').relative_to(ROOT)))
        records[name] = {'pdf': str(path.relative_to(ROOT)), 'sha256': digest(path), 'pages': count,
                         'fonts_embedded': True, 'locators': locators, 'core_pages': core,
                         'neighbor_pages': neighbors, 'overview_sheets': sheets, 'detail_images': details}
        print(name, count, 'core pages:', core, flush=True)
    records['main_alias_matches'] = digest(ROOT / 'report/main.pdf') == records['content']['sha256']
    left = sorted((dest / 'content').glob('page-*.png'))
    right = sorted((dest / 'content-twoside').glob('page-*.png'))
    identical, different = [], []
    for i, (a, b) in enumerate(zip(left, right), 1):
        with Image.open(a) as ia, Image.open(b) as ib:
            equal = ia.size == ib.size and ImageChops.difference(ia.convert('RGB'), ib.convert('RGB')).getbbox() is None
            (identical if equal else different).append(i)
    records['variant_comparison'] = {'dpi': 30, 'equal_page_count': len(left) == len(right),
                                     'identical_pages': identical, 'different_pages': different}
    write_json(dest / 'pdf-inspection.json', records)


if __name__ == '__main__':
    main()
