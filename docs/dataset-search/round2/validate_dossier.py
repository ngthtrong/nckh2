#!/usr/bin/env python3
"""Offline consistency checks; does not certify semantic label accuracy."""
import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def rows(path):
    with path.open(encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle))


def main():
    candidates = rows(ROOT / 'candidates.csv')
    queries = json.loads((ROOT / 'search-log.json').read_text())
    manifest = json.loads((ROOT / 'sources.json').read_text())
    profiles = json.loads((ROOT / 'audit/profiles.json').read_text())['sources']
    samples = rows(ROOT / 'audit/sample-presence.csv')
    assert len(candidates) == len({r['source_id'] for r in candidates}) == 12
    assert len(queries) == len({r['query_id'] for r in queries}) == 41
    assert len(manifest) == 7 and len(profiles) == 5
    for c in candidates:
        assert c['primary_url'].startswith('https://') and c['access'] and c['verdict']
        assert all(c[rq] in {'cần bổ sung nhãn', 'bằng chứng bổ trợ', 'không phù hợp'}
                   for rq in ['rq1', 'rq2', 'rq3'])
    assert {m['source_id'] for m in manifest} == set(profiles)
    for m in manifest:
        assert m['http_status'] == 200 and m['bytes'] > 0
        assert re.fullmatch('[a-f0-9]{64}', m['sha256'])
        assert profiles[m['source_id']]['source_hashes'][m['file']] == m['sha256']
        if 'resolved_revision' in m:
            assert m['resolved_revision'] in m['pinned_url'] and m['pinned_hash_verified']
    assert Counter(s['source_id'] for s in samples) == {sid: 100 for sid in profiles}
    assert all(s['same_incident_gold'] == s['graded_priority_label'] == 'False' for s in samples)
    assert profiles['A02']['rows'] == 3593
    assert profiles['A02']['people_trapped_topic_rows'] == 167
    assert profiles['A03']['rows'] == 1881
    assert profiles['A05']['rows'] == 12826
    assert profiles['A06']['rows'] == 59607
    assert profiles['A07']['rows'] == 307 and profiles['A07']['synthetic_rows_excluded'] == 1346
    for path in ROOT.rglob('*.md'):
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text()):
            if target.startswith(('https://', 'http://', '#')):
                continue
            destination = (path.parent / target.split('#')[0]).resolve()
            # This receipt is produced below, so the first invocation can link to it.
            assert destination.exists() or destination == ROOT / 'audit/validation.json', \
                f'Broken link: {path} -> {target}'
    result = {'status': 'PASS', 'queries': len(queries), 'candidate_entries': len(candidates),
              'profiled_families': len(profiles), 'data_files': len(manifest),
              'presence_sample_rows': len(samples), 'new_human_annotations': 0,
              'new_RQ_experiment_results': 0,
              'scope': 'Dossier consistency only; not semantic/source/label certification'}
    (ROOT / 'audit/validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
