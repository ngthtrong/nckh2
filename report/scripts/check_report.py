#!/usr/bin/env python3
"""Check draft placeholders, body page count, build warnings and release evidence."""
import argparse
from pathlib import Path
import re
import sys
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
            if re.search(r'TODO|\\DraftNote\b|FIXME|\[điền', active, re.I):
                notes.append(f'{file.relative_to(ROOT)}:{number}: còn nội dung mẫu')
    print(f'Placeholder: {len(notes)} dòng')
    for note in notes:
        print('  ' + note)
    if args.release and notes:
        errors.append('Cần hoàn tất thông tin hành chính, nội dung và các biểu mẫu trước khi xuất bản đầy đủ.')
    out = ROOT / args.build_dir
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
