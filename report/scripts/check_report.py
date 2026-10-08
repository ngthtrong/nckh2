#!/usr/bin/env python3
"""Check draft placeholders, body page count, build warnings and release evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import subprocess
from build_evidence import validated_entries

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', action='store_true')
    parser.add_argument('--build-dir', default='build/content')
    args = parser.parse_args()
    errors = []
    notes = []
    sources = []
    for folder in ['config', 'frontmatter', 'chapters', 'appendices', 'deliverables/content', 'generated']:
        sources.extend((ROOT / folder).rglob('*.tex'))
    for file in sorted(sources):
        for number, line in enumerate(file.read_text().splitlines(), 1):
            active = re.split(r'(?<!\\)%', line)[0]
            if re.search(r'TODO|\\DraftNote\b|\\PendingField\b|FIXME|\[điền', active, re.I):
                notes.append(f'{file.relative_to(ROOT)}:{number}: còn nội dung mẫu')
    print(f'Placeholder: {len(notes)} dòng')
    for note in notes:
        print('  ' + note)
    if args.release and notes:
        errors.append('Cần xử lý các ghi chú còn đánh dấu và đối chiếu biểu mẫu chính thức trước khi xuất bản đầy đủ.')
    entries = sum(len(re.findall(r'@\s*(?!comment\b|preamble\b|string\b)\w+\s*[{(]', f.read_text(), re.I))
                  for f in (ROOT / 'bibliography').glob('*.bib'))
    print(f'Tài liệu tham khảo trong nguồn: {entries}')
    if args.release and entries == 0:
        errors.append('Chưa có tài liệu tham khảo thực sự trong bibliography/.')
    out = ROOT / args.build_dir
    figure_provenance = ROOT / 'generated/figure-provenance.json'
    if figure_provenance.exists():
        provenance = json.loads(figure_provenance.read_text())
        for relative, digest in provenance['sources_sha256'].items():
            source = ROOT.parent / relative
            if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != digest:
                errors.append('Nguồn hình đã thay đổi: ' + relative + '; chạy make figures.')
        for name, versions in provenance['figures_sha256'].items():
            for ext, digest in versions.items():
                source = ROOT / 'assets/figures' / (name + '.' + ext)
                if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != digest:
                    errors.append('Hình thiếu hoặc không khớp hash: ' + source.name)
        print(f"Kiểm tra nguồn và hash: {len(provenance['figures_sha256'])} hình")
    else:
        errors.append('Thiếu figure-provenance.json; chạy make figures.')
    metrics = next(iter(sorted(out.glob('*.metrics'))), None)
    if metrics:
        values = dict(line.split('=', 1) for line in metrics.read_text().splitlines() if '=' in line)
        if 'body-start' in values and 'body-end' in values:
            count = int(values['body-end']) - int(values['body-start']) + 1
            print(f'Số trang từ Mở đầu đến hết Kết luận và kiến nghị: {count}/50')
            if count < 50:
                (errors if args.release else notes).append('Thân bài chưa đủ 50 trang.')
        elif args.release:
            errors.append('Thiếu mốc số trang thân bài.')
    elif args.release:
        errors.append('Chưa có build nội dung: chạy make content trước.')
    for log in out.glob('*.log'):
        text = log.read_text(errors='replace')
        for phrase in ['There were undefined references', 'There were undefined citations', 'Overfull \\hbox', 'Overfull \\vbox']:
            if phrase in text:
                print(f'{log.relative_to(ROOT)}: {phrase}')
                if args.release:
                    errors.append('Cần xử lý cảnh báo PDF trước khi xuất bản đầy đủ.')
    pdfs = list(out.glob('*.pdf')) + [ROOT / f'build/{name}/{name}.pdf'
                                    for name in ['bulletin-vi', 'bulletin-en', 'summary-vi', 'summary-en']]
    for pdf in pdfs:
        if pdf.is_file():
            printed = subprocess.check_output(['pdftotext', '-layout', str(pdf), '-'], text=True)
            if re.search(r'^\s*Nguồn\s*:', printed, re.M):
                errors.append('PDF còn dòng nguồn nội bộ: ' + str(pdf.relative_to(ROOT)))
    # The official bilingual bulletin template limits each language to one A4 page.
    for language in ['vi', 'en']:
        pdf = ROOT / f'build/bulletin-{language}/bulletin-{language}.pdf'
        if not pdf.is_file():
            if args.release:
                errors.append('Thiếu bản tin: ' + str(pdf.relative_to(ROOT)))
            continue
        info = subprocess.check_output(['pdfinfo', str(pdf)], text=True)
        match = re.search(r'^Pages:\s+(\d+)', info, re.M)
        if not match or int(match.group(1)) != 1:
            errors.append(f'Bản tin {language} phải có đúng 1 trang theo mẫu chính thức.')
        else:
            print(f'Bản tin {language}: 1 trang A4 theo giới hạn mẫu')
    template_provenance = ROOT / 'generated/guideline-text/provenance.json'
    if template_provenance.exists():
        for relative, digests in json.loads(template_provenance.read_text()).items():
            source = ROOT / relative
            extracted = ROOT / digests['text_path']
            if (not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != digests['source_sha256']
                    or not extracted.is_file() or hashlib.sha256(extracted.read_bytes()).hexdigest() != digests['text_sha256']):
                errors.append('Mẫu/văn bản trích xuất đã đổi: ' + relative + '; chạy make templates rồi đối chiếu lại.')
    if args.release:
        try:
            validated_entries()
        except (ValueError, OSError, KeyError, TypeError) as exc:
            errors.append(str(exc))
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        sys.exit(1)
    print('Khung được kiểm tra; bản nháp chưa được xác nhận đủ điều kiện nộp.' if not args.release else 'Kiểm tra tự động đạt; vẫn cần rà soát trực quan và hồ sơ ký/dấu.')

if __name__ == '__main__':
    main()
