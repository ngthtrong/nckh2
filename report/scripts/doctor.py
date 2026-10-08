#!/usr/bin/env python3
"""Report dependencies without installing system software."""
from pathlib import Path
import shutil
import subprocess

for tool in ['xelatex', 'bibtex', 'latexmk', 'biber', 'pandoc', 'mutool']:
    print(f'{tool}: {shutil.which(tool) or "chưa cài"}')
if shutil.which('kpsewhich'):
    for package in ['scrreprt.cls', 'fontspec.sty', 'polyglossia.sty', 'unicode-math.sty',
                    'geometry.sty', 'setspace.sty', 'longtable.sty', 'pdfpages.sty',
                    'natbib.sty', 'biblatex.sty', 'ieee.bbx', 'ieee.cbx', 'ieeetr.bst', 'algorithm.sty', 'algpseudocode.sty', 'siunitx.sty']:
        result = subprocess.run(['kpsewhich', package], capture_output=True, text=True)
        print(f'{package}: {"có" if result.stdout.strip() else "chưa cài"}')
font = subprocess.run(['fc-match', '-f', '%{family}', 'Times New Roman'], capture_output=True, text=True) if shutil.which('fc-match') else None
print('Times New Roman: ' + ('fontconfig' if font and 'Times New Roman' in font.stdout else
      '/mnt/c/Windows/Fonts/' if Path('/mnt/c/Windows/Fonts/times.ttf').is_file() else 'chưa tìm thấy'))
