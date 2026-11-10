"""Capture current PDF text, font, page and hash receipts after builds finish."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent / 'checks'
TARGETS = {
    'related': r'AlleyFloodNet',
    'objectives': r'Chỉ tiêu đánh giá|Chỉ tiêu có thể|Chất lượng ảnh|Mục tiêu và',
    'architecture': r'Tổ chức dữ liệu và triển khai',
    'integration': r'Tình trạng tích hợp di động',
    'software': r'Khắc phục phần mềm và kiểm hồi quy mới',
    'conclusion': r'KẾT LUẬN VÀ',
    'references': r'Tài liệu tham khảo',
    'comparison': r'Đối chiếu nội dung nghiên cứu với thuyết minh',
    'storage_appendix': r'Chi tiết phân lớp và lưu trữ',
}


def capture():
    OUT.mkdir(exist_ok=True)
    inventory = {}
    for name in ['content', 'content-twoside', 'bulletin-vi', 'bulletin-en',
                 'summary-vi', 'summary-en']:
        job = 'content' if name.startswith('content') else name
        pdf = ROOT / f'report/build/{name}/{job}.pdf'
        info = subprocess.check_output(['pdfinfo', str(pdf)], text=True)
        fonts = subprocess.check_output(['pdffonts', str(pdf)], text=True)
        body = subprocess.check_output(['pdftotext', '-layout', str(pdf), '-'], text=True)
        (OUT / f'{name}-text.txt').write_text(body)
        (OUT / f'{name}-fonts.txt').write_text(fonts)
        (OUT / f'{name}-info.txt').write_text(info)
        font_flags = [re.search(r'\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$', line)
                      for line in fonts.splitlines()[2:] if line.strip()]
        pages = body.split('\f')
        entry = {
            'pages': int(re.search(r'^Pages:\s+(\d+)', info, re.M)[1]),
            'all_fonts_embedded': bool(font_flags) and all(m and m[1] == 'yes' for m in font_flags),
            'font_rows': len(font_flags),
            'sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
            'target_pages': {key: [i + 1 for i, page in enumerate(pages) if re.search(pattern, page)]
                             for key, pattern in TARGETS.items()},
        }
        metrics_files = list((ROOT / f'report/build/{name}').glob('*.metrics'))
        if name.startswith('content') and metrics_files:
            metrics = dict(line.split('=', 1) for line in metrics_files[0].read_text().splitlines()
                           if '=' in line)
            entry['body_pages'] = int(metrics['body-end']) - int(metrics['body-start']) + 1
            entry['evidence_pages'] = [i + 1 for i, page in enumerate(pages)
                                       if i > 100 and re.search(r'Ứng dụng di động hỗ trợ cứu hộ thiên tai|Website quản lý thông tin cứu hộ|Bộ mô hình AI đã huấn luyện|Minh chứng bài báo', page[:160])]
        inventory[name] = entry
    (OUT / 'pdf-inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(inventory, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    capture()
