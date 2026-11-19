#!/usr/bin/env python3
"""Validate template sources/PDFs; placeholders and short reports are allowed."""
from pathlib import Path
import re
import shutil
import subprocess

from build import ROOT, UNRESOLVED, LAYOUT_ERRORS

EXPECTED = {
    'content': 'content', 'content-twoside': 'content',
    'bulletin-vi': 'bulletin-vi', 'bulletin-en': 'bulletin-en',
    'summary-vi': 'summary-vi', 'summary-en': 'summary-en',
}
errors = []


def output(args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


for tool in ['pdfinfo', 'pdftotext', 'pdffonts']:
    if not shutil.which(tool):
        raise SystemExit(f'{tool} is required; run make doctor.')

# Resolve local TeX resources; traversal/symlinks must never escape this directory.
source_files = [ROOT / 'main.tex']
for folder in ['template', 'config', 'frontmatter', 'chapters', 'appendices', 'deliverables', 'examples']:
    source_files.extend((ROOT / folder).rglob('*.tex'))
for source in source_files:
    text = '\n'.join(line.split('%', 1)[0] for line in source.read_text().splitlines())
    for command, name in re.findall(r'\\(input|include|includegraphics|includepdf)(?:\[[^]]*\])?\{([^}]+)\}', text):
        if '\\' in name:
            continue  # Macro paths are validated by the actual LaTeX build.
        candidate = ROOT / name
        if command in ['input', 'include']:
            candidate = candidate.with_suffix('.tex')
        choices = [candidate] if command in ['input', 'include', 'includepdf'] else [
            candidate, ROOT / 'assets/figures' / name, ROOT / 'assets/diagrams' / name]
        if command == 'includegraphics' and not candidate.suffix:
            choices = [p.with_suffix(ext) for p in choices for ext in ['.pdf', '.png', '.jpg', '.jpeg']]
        if not any(p.is_file() and p.resolve().is_relative_to(ROOT) for p in choices):
            errors.append(f'{source.relative_to(ROOT)}: missing or external resource {name}')
for path in ROOT.rglob('*'):
    if path.is_symlink() and not path.resolve().is_relative_to(ROOT):
        errors.append(f'External symlink: {path.relative_to(ROOT)}')

targets = dict(EXPECTED)
if (ROOT / 'build/smoke/smoke.pdf').exists():
    targets['smoke'] = 'smoke'
for folder, job in targets.items():
    directory = ROOT / 'build' / folder
    pdf = directory / f'{job}.pdf'
    log = directory / f'{job}.log'
    if not pdf.is_file() or not log.is_file():
        errors.append(f'{folder}: PDF/log missing; run make all smoke.')
        continue
    log_text = log.read_text(errors='replace')
    bad = [line for line in log_text.splitlines() if UNRESOLVED.search(line) or LAYOUT_ERRORS.search(line)]
    errors.extend(f'{folder}: {line}' for line in bad)
    info = output(['pdfinfo', str(pdf)])
    pages = int(re.search(r'^Pages:\s+(\d+)', info, re.M)[1])
    sizes = output(['pdfinfo', '-f', '1', '-l', str(pages), str(pdf)])
    dimensions = re.findall(r'(?:Page\s+\d+ size:|Page size:)\s+([\d.]+) x ([\d.]+)', sizes)
    if not dimensions or any(abs(min(float(w), float(h)) - 595.276) > 1 or
                             abs(max(float(w), float(h)) - 841.89) > 1 for w, h in dimensions):
        errors.append(f'{folder}: page size must be A4')
    font_lines = output(['pdffonts', str(pdf)]).splitlines()[2:]
    if not any('TimesNewRoman' in line.replace(' ', '') for line in font_lines):
        errors.append(f'{folder}: Times New Roman is not embedded')
    for line in font_lines:
        match = re.search(r'\s(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$', line)
        if not match or match[1] != 'yes':
            errors.append(f'{folder}: unembedded font: {line}')
    pdf_text = output(['pdftotext', '-layout', str(pdf), '-'])
    if folder in ['content', 'content-twoside']:
        for heading in ['Mở đầu', 'Kết luận và kiến nghị', 'Tài liệu tham khảo', 'Danh mục từ viết tắt']:
            if heading not in pdf_text:
                errors.append(f'{folder}: missing section {heading}')
        if 'INFORMATION ON RESEARCH RESULTS' not in pdf_text:
            errors.append(f'{folder}: English form missing')
    if folder in ['content', 'content-twoside', 'summary-vi']:
        raw_text = output(['pdftotext', '-raw', str(pdf), '-'])
        normalized = re.sub(r'\s+', ' ', raw_text).casefold()
        for heading in ['Stt', 'Tên bài báo', 'Tác giả/ nhóm tác giả', 'Tên tạp chí',
                        'Số tạp chí', 'Năm xuất bản']:
            if heading.casefold() not in normalized:
                errors.append(f'{folder}: publication-table column missing: {heading}')
    if folder in ['content', 'content-twoside']:
        headings = ['BẢN TIN ĐỀ TÀI', 'SUMMARY REPORT RESEARCH PROJECT',
                    'BÁO CÁO TÓM TẮT', 'INFORMATION ON RESEARCH RESULTS']
        positions = [pdf_text.rfind(heading) for heading in headings]
        if any(position < 0 for position in positions) or positions != sorted(positions):
            errors.append(f'{folder}: appended forms missing or out of order')
    if folder in ['bulletin-vi', 'bulletin-en'] and pages != 1:
        errors.append(f'{folder}: bulletin must fit on one page')
    if folder == 'smoke':
        bibliography = pdf_text.rsplit('Tài liệu tham khảo', 1)[-1]
        markers = ['Văn bản pháp quy', 'Sách, báo, tạp chí', '[A Author]', '[Z Author]',
                   'Bài viết và tài liệu khác']
        positions = [bibliography.find(marker) for marker in markers]
        if any(position < 0 for position in positions) or positions != sorted(positions):
            errors.append('smoke: bibliography groups or alphabetic order incorrect')
        if not re.search(r'\[1\]', bibliography):
            errors.append('smoke: numeric bibliography label [1] missing')
    print(f'{pdf.relative_to(ROOT)}: {pages} pages, A4, fonts embedded, references/layout checked')

if errors:
    raise SystemExit('\n'.join(errors))
print('PASS: standalone template; no minimum page count or acceptance-dossier requirement.')
