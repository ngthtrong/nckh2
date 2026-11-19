#!/usr/bin/env python3
"""Match figure/table sources, LaTeX lists, labels and captions in the built PDF."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def group(text, start):
    """Read a balanced TeX group, including nested commands and escaped braces."""
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != '{':
        raise ValueError('Expected a TeX group: ' + text[start:start + 60])
    depth = 1
    end = start + 1
    while end < len(text):
        if text[end] == '\\':
            end += 2
            continue
        if text[end] == '{':
            depth += 1
        elif text[end] == '}':
            depth -= 1
            if not depth:
                return text[start + 1:end], end + 1
        end += 1
    raise ValueError('Unclosed TeX group')


def arguments(text, start, count):
    values = []
    for _ in range(count):
        value, start = group(text, start)
        values.append(value)
    return values


def normalize(text):
    text = text.replace('\\ignorespaces', '').replace('\\relax', '')
    return re.sub(r'\s+', ' ', text).strip()


def body_sources():
    def expand(path):
        text = re.sub(r'(?<!\\)%[^\n]*', '', path.read_text())

        def include(match):
            child = ROOT / (match.group(1) + '.tex')
            return expand(child)

        return re.sub(r'\\(?:input|include)\{([^}]+)\}', include, text)

    main = (ROOT / 'main.tex').read_text()
    paths = re.findall(r'\\include\{((?:chapters|appendices)/[^}]+)\}', main)
    return '\n'.join(expand(ROOT / (p + '.tex')) for p in paths)


def validate_floats(out):
    errors = []
    records = []
    source = body_sources()
    references = set(re.findall(r'\\(?:ref|pageref|autoref|[cC]ref)\{([^}]+)\}', source))
    expected = {'figure': [], 'table': []}
    pattern = r'\\begin\{(figure|reportlandscapefigure|table|longtable)\}.*?\\end\{\1\}'
    for match in re.finditer(pattern, source, re.S):
        block = match.group(0)
        kind = 'figure' if match.group(1) in ['figure', 'reportlandscapefigure'] else 'table'
        captions = list(re.finditer(r'\\caption(?:\[[^\]]*\])?\s*', block))
        labels = re.findall(r'\\label\{((?:fig|tab):[^}]+)\}', block)
        if not captions or len(captions) != len(labels) or (kind == 'table' and len(captions) != 1):
            errors.append(f'{kind}: mỗi caption cần đúng một label, bảng có một caption: {labels}')
            continue
        # Independent figures can share one float in minipage columns/rows.
        # Keep their numbering, source order and PDF checks separate.
        for index, caption in enumerate(captions):
            title, end = group(block, caption.end())
            next_caption = captions[index + 1].start() if index + 1 < len(captions) else len(block)
            caption_labels = re.findall(r'\\label\{((?:fig|tab):[^}]+)\}', block[end:next_caption])
            if len(caption_labels) != 1:
                errors.append(f'{kind}: caption cần một label ngay sau nó: {caption_labels}')
                continue
            label = caption_labels[0]
            expected[kind].append((label, title))
            if kind == 'figure' and label not in references:
                errors.append('Hình chưa được tham chiếu trong nội dung: ' + label)
    all_labels = re.findall(r'\\label\{([^}]+)\}', source)
    for label, count in Counter(all_labels).items():
        if count > 1:
            errors.append('Nhãn bị định nghĩa lặp: ' + label)
    if re.search(r'(?:Hình|Bảng)[~\s]+\d+\.\d+', source):
        errors.append('Có tham chiếu hình/bảng gõ số thủ công; cần dùng \\ref.')

    labels = {}
    for aux in sorted(out.rglob('*.aux'), key=lambda p: p.stat().st_mtime_ns):
        text = aux.read_text()
        for match in re.finditer(r'\\newlabel\s*', text):
            key, data = arguments(text, match.end(), 2)
            if key.startswith(('fig:', 'tab:')):
                labels[key] = arguments(data, 0, 3)

    job = next((name for name in ['content', 'full'] if (out / (name + '.pdf')).is_file()), 'content')
    pdf = out / (job + '.pdf')
    if not pdf.is_file():
        return errors + ['Thiếu PDF nội dung: ' + str(pdf)], records
    # Tectonic retains list files under its driver name while build.py renames the PDF.
    list_jobs = [name for name in [job, '_' + job + '_driver']
                 if all((out / (name + '.' + ext)).is_file() for ext in ['lof', 'lot'])]
    list_job = max(list_jobs, key=lambda name: (out / (name + '.lof')).stat().st_mtime_ns) if list_jobs else job
    pages = subprocess.check_output(['pdftotext', '-layout', str(pdf), '-'], text=True).split('\f')
    # The main body starts at Arabic page 1 after the Roman-numbered front matter.
    starts = [i for i, page in enumerate(pages)
              if re.search(r'MỞ\s+ĐẦU', page) and re.search(r'\n\s*1\s*$', page)]
    if len(starts) != 1:
        return errors + ['Không xác định duy nhất trang 1 của thân bài trong PDF.'], records
    offset = starts[0]

    for kind, suffix, prefix in [('figure', 'lof', 'Hình'), ('table', 'lot', 'Bảng')]:
        path = out / (list_job + '.' + suffix)
        if not path.is_file():
            errors.append('Thiếu danh mục: ' + str(path))
            continue
        listed = []
        text = path.read_text()
        for match in re.finditer(r'\\contentsline\s*', text):
            entry_kind, data, page, anchor = arguments(text, match.end(), 4)
            if entry_kind != kind:
                continue
            number_match = re.search(r'\\numberline\s*', data)
            number, title = arguments(data, number_match.end(), 2)
            listed.append((number, normalize(title), page, anchor))
        if len(listed) != len(expected[kind]):
            errors.append(f'{kind}: nguồn có {len(expected[kind])}, danh mục có {len(listed)}.')
        sequence = Counter()
        for (label, title), (number, listed_title, page, anchor) in zip(expected[kind], listed):
            chapter, index = number.rsplit('.', 1)
            sequence[chapter] += 1
            if int(index) != sequence[chapter]:
                errors.append('Số thứ tự không liên tục: ' + number)
            actual = labels.get(label)
            if actual is None or actual[:2] != [number, page]:
                errors.append(f'Nhãn và danh mục không khớp: {label}: {actual}, {number}, {page}')
            if normalize(title) != listed_title:
                errors.append('Tên trong nguồn và danh mục không khớp: ' + label)
            if anchor != kind + '.' + number:
                errors.append('Liên kết danh mục không khớp: ' + label)
            physical = offset + int(page)
            printed = pages[physical - 1] if 0 < physical <= len(pages) else ''
            if not re.search(r'\b' + prefix + r'\s+' + re.escape(number) + r'\s*:', printed):
                errors.append(f'Không thấy chú thích {prefix} {number} tại trang PDF {physical}.')
            records.append({'kind': kind, 'number': number, 'label': label,
                            'caption': normalize(title), 'printed_page': page, 'pdf_page': physical})
    return errors, records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', default='build/content')
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    errors, records = validate_floats(ROOT / args.build_dir)
    if args.json:
        args.json.write_text(json.dumps({'errors': errors, 'floats': records}, ensure_ascii=False, indent=2) + '\n')
    for error in errors:
        print(error)
    print(f'Đối chiếu nguồn, danh mục, nhãn và PDF: {sum(r["kind"] == "figure" for r in records)} hình, '
          f'{sum(r["kind"] == "table" for r in records)} bảng.')
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
