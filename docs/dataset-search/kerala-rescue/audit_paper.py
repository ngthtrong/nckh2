#!/usr/bin/env python3
"""Verify the supplied Kerala paper and preparation files, without RQ results.

Requires Python 3.10+ and Poppler's pdfinfo/pdfdetach/pdftotext. This checks the
identified PDF and dossier consistency, not correctness of source annotations.
"""
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PDF = ROOT.parent / 'paper/1-s2.0-S2212420922001273-main.pdf'
EXPECTED_SHA256 = '2922af42234c9b613c8587dcdc83840bb0a0175bba17ca51f392914558dd62ab'


def command(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def main():
    sha = hashlib.sha256(PDF.read_bytes()).hexdigest()
    assert sha == EXPECTED_SHA256, 'PDF snapshot changed; review source before updating this audit'
    info = command('pdfinfo', str(PDF))
    text = command('pdftotext', '-layout', str(PDF), '-')
    attachments = command('pdfdetach', '-list', str(PDF))
    pages = int(re.search(r'^Pages:\s+(\d+)', info, re.M).group(1))
    assert pages == 13 and '0 embedded files' in attachments
    assert '10.1016/j.ijdrr.2022.102908' in text
    assert '45,322' in text and '39,950' in text and '27 columns' in text
    assert 'Fictitious posts' in text and 'rebuildearth.slack.com' in text
    sections = {}
    for title in ['2.3. Kerala Rescue', '2.5. Location inference',
                  '2.6. Characterising flood impacts', 'Data availability', 'A. Appendix']:
        found = [i + 1 for i, page in enumerate(text.split('\f')) if title in page]
        assert found, 'Missing reviewed section: ' + title
        sections[title] = found
    template = json.loads((ROOT / 'intake-manifest.template.json').read_text())
    assert template['status'] == 'awaiting_request_level_data'
    assert template['files'] == [] and template['local_rows_measured'] is None
    assert template['request_records_received'] is False
    assert template['new_human_annotations'] == template['new_rq_experiments'] == 0
    with (ROOT / 'field-map.csv').open(encoding='utf-8', newline='') as handle:
        mapping = list(csv.DictReader(handle))
    assert len(mapping) == len({r['target_field'] for r in mapping}) == 20
    assert all(None not in r and r['use_rule'] and r['missing_rule'] for r in mapping)
    assert next(r for r in mapping if r['target_field'] == 'priority_ref')['visibility'] == 'evaluator_only'
    queries = json.loads((ROOT / 'search-log.json').read_text())
    assert len(queries) == len({q['id'] for q in queries}) == 8
    for path in ROOT.glob('*.md'):
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text()):
            if target.startswith(('https://', 'http://', '#')):
                continue
            dest = (path.parent / target.split('#')[0]).resolve()
            assert dest.exists() or dest == ROOT / 'audit/paper-audit.json', str(dest)
    result = {
        'status': 'PASS', 'paper_file': str(PDF.relative_to(ROOT.parent)),
        'paper_doi': '10.1016/j.ijdrr.2022.102908', 'pdf_sha256': sha,
        'extracted_text_sha256': hashlib.sha256(text.encode()).hexdigest(),
        'pages': pages, 'embedded_files': 0, 'reviewed_section_pages': sections,
        'paper_reported_counts_not_local_data_counts': template['paper_reported_counts_not_locally_measured'],
        'field_mapping_entries': len(mapping), 'additional_queries': len(queries),
        'dataset_status': 'awaiting_request_level_data', 'new_human_annotations': 0,
        'new_rq_experiments': 0, 'outgoing_messages_sent': 0,
        'scope': 'PDF identity and preparation-file checks; no dataset or label certification',
    }
    out = ROOT / 'audit/paper-audit.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
