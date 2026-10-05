#!/usr/bin/env python3
"""Validate the explicit evidence list and generate LaTeX includes; never invent PDFs."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'evidence/manifest.yaml'

def validated_entries():
    data = json.loads(MANIFEST.read_text())
    errors = []
    for flag in ['commitments_confirmed', 'official_forms_confirmed']:
        if data.get(flag) is not True:
            errors.append(f'{flag}: chưa được xác nhận bằng hồ sơ chính thức')
    products = data.get('products', [])
    if not isinstance(products, list):
        raise ValueError('products must be a list (empty only if the approved project registers none).')
    proposal = data.get('approved_proposal')
    if not isinstance(proposal, dict):
        raise ValueError('approved_proposal must be an object.')
    entries = [proposal] + products
    seen = set()
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f'Mục {i}: cần một object'); continue
        title = entry.get('title', '')
        path = entry.get('path', '')
        if not title or not path or 'TODO' in title + path:
            errors.append(f'Mục {i}: còn placeholder hoặc thiếu title/path')
        if entry.get('verified') is not True:
            errors.append(f'{title or i}: chưa xác nhận tính phù hợp, chữ ký/dấu khi cần')
        if i and (entry.get('group') not in ['I', 'II', 'III'] or not entry.get('commitment') or 'TODO' in entry.get('commitment', '')):
            errors.append(f'{title or i}: thiếu nhóm I–III hoặc mapping cam kết')
        resolved = (ROOT / path).resolve()
        if not resolved.is_relative_to((ROOT / 'evidence').resolve()) or resolved.suffix.lower() != '.pdf':
            errors.append(f'{path}: phải là PDF trong evidence/')
        if not re.fullmatch(r'[A-Za-z0-9_./-]+', path) or '..' in Path(path).parts:
            errors.append(f'{path}: dùng đường dẫn ASCII an toàn, không có khoảng trắng')
        if not resolved.is_file():
            errors.append(f'Thiếu PDF: {path}')
        elif not resolved.read_bytes().startswith(b'%PDF-'):
            errors.append(f'{path}: không có header PDF')
        if path in seen:
            errors.append(f'PDF lặp lại: {path}')
        seen.add(path)
    if errors:
        raise ValueError('\n'.join(errors))
    # Proposal first, then group I, II, III, preserving registration order within groups.
    return [proposal] + sorted(products, key=lambda e: ['I', 'II', 'III'].index(e['group']))

def tex_escape(value):
    substitutions = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
                     '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    return ''.join(substitutions.get(c, c) for c in value)

def main():
    entries = validated_entries()
    output = ROOT / 'build/evidence.tex'
    output.parent.mkdir(exist_ok=True)
    output.write_text('% Generated from evidence/manifest.yaml; do not edit.\n' + ''.join(
        '\\EvidencePDF{' + tex_escape(e['title']) + '}{' + e['path'] + '}\n' for e in entries))
    print(f'Đã kiểm tra {len(entries)} PDF; tạo build/evidence.tex')

if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
