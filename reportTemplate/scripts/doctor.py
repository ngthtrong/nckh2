#!/usr/bin/env python3
"""Check tools, shared resources and all four Times New Roman faces."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
missing = []
for tool in ['python3', 'make', 'xelatex', 'kpsewhich', 'pdftotext', 'pdfinfo', 'pdffonts']:
    found = shutil.which(tool)
    print(f'{tool}: {found or "MISSING"}')
    if not found:
        missing.append(tool)
for tool in ['biber', 'bibtex', 'pdftoppm']:
    print(f'{tool}: {shutil.which(tool) or "optional / not installed"}')
if not shutil.which('bibtex') and not shutil.which('biber'):
    missing.append('biber or bibtex')
if shutil.which('kpsewhich'):
    for package in ['scrreprt.cls', 'fontspec.sty', 'polyglossia.sty', 'unicode-math.sty',
                    'geometry.sty', 'setspace.sty', 'graphicx.sty', 'longtable.sty',
                    'booktabs.sty', 'tabularx.sty', 'amsmath.sty', 'tikz.sty', 'pdfpages.sty',
                    'scrlayer-scrpage.sty', 'hyperref.sty', 'bookmark.sty', 'natbib.sty', 'ieeetr.bst']:
        found = subprocess.run(['kpsewhich', package], capture_output=True, text=True).stdout.strip()
        print(f'{package}: {"OK" if found else "MISSING"}')
        if not found:
            missing.append(package)
    for package in ['ieee.bbx', 'ieee.cbx', 'xurl.sty']:
        found = subprocess.run(['kpsewhich', package], capture_output=True, text=True).stdout.strip()
        print(f'{package}: {"OK" if found else "optional / not installed"}')
if shutil.which('xelatex'):
    with tempfile.TemporaryDirectory(prefix='template-font-check-') as temp:
        source = (r'\documentclass{article}\input{template/typography}'
                  r'\begin{document}Tiếng Việt: Đ Ư Ỡ. '
                  r'\textbf{Đậm}\textit{Nghiêng}\textbf{\textit{Đậm nghiêng}}\end{document}')
        result = subprocess.run(['xelatex', '-interaction=nonstopmode', '-halt-on-error',
                                 f'-output-directory={temp}', '-jobname=font-check', source],
                                cwd=ROOT, capture_output=True, text=True)
        log = Path(temp, 'font-check.log').read_text(errors='replace')
        good = result.returncode == 0 and 'Font shape' not in log and 'Missing character' not in log
        print('Times New Roman (four faces): ' + ('OK' if good else 'MISSING / check fonts'))
        if not good:
            missing.append('Times New Roman')
print('Logo: ' + ('OK' if (ROOT / 'logo-ctu.png').is_file() else 'MISSING'))
if not (ROOT / 'logo-ctu.png').is_file():
    missing.append('logo-ctu.png')
if missing:
    raise SystemExit('Missing dependencies: ' + ', '.join(missing))
