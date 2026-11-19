#!/usr/bin/env python3
"""Offline consistency checks for the survey, counts, links, and evidence scope."""
import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def csv_rows(name):
    with (ROOT / name).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def main():
    papers = csv_rows('papers.csv')
    datasets = csv_rows('datasets.csv')
    samples = csv_rows('audit/sample-presence.csv')
    queries = json.loads((ROOT / 'search-log.json').read_text())
    manifests = json.loads((ROOT / 'audit/sources.json').read_text())
    profiles = json.loads((ROOT / 'audit/profiles.json').read_text())['sources']
    access = json.loads((ROOT / 'audit/paper-access.json').read_text())
    ids = {p['paper_id'] for p in papers}
    assert len(ids) == len(papers) == 34, 'Paper count/IDs drifted; update the narrative'
    assert len({q['query_id'] for q in queries}) == len(queries) == 40
    assert len({d['dataset_id'] for d in datasets}) == len(datasets) == 12
    deep = {p['paper_id'] for p in papers if p['reading_level'] == 'targeted_full_text_review'}
    evidence = {'P01': 'humaid', 'P02': 'crisisbench', 'P10': 'trecis2022',
                'P11': 'crisisfacts', 'P13': 'harvey_feng', 'P14': 'harvey_wang',
                'P15': 'victimfinder', 'P19': 'integrated2025', 'P22': 'locations2021',
                'P23': 'disasterloc2026', 'P24': 'crisists', 'P27': 'shortest2025',
                'P28': 'flood112'}
    assert deep == set(evidence) and len(deep) == 13
    successful_access = {a['id'] for a in access if a.get('text_extracted')}
    assert set(evidence.values()) <= successful_access, 'Deep reading lacks a successful source receipt'
    for paper in papers:
        assert paper['primary_url'].startswith('https://') and paper['reason']
        assert 2010 <= int(paper['year']) <= 2026
    for dataset in datasets:
        if dataset['paper_ids'] != 'official GOV.UK dataset':
            assert set(dataset['paper_ids'].split(';')) <= ids
        for rq in ('rq1', 'rq2', 'rq3'):
            assert dataset[rq] in {'đánh giá trực tiếp', 'bằng chứng bổ trợ',
                                   'cần bổ sung nhãn', 'không phù hợp'}
            assert dataset[rq] != 'đánh giá trực tiếp', 'A new direct-evidence claim needs review'
        assert (ROOT / dataset['evidence'].split('#')[0]).is_file()
    assert len(manifests) == len(profiles) == 6
    assert {m['source_id'] for m in manifests} == set(profiles)
    for manifest in manifests:
        assert manifest['http_status'] == 200 and manifest['status'] == 'downloaded'
        assert re.fullmatch('[a-f0-9]{64}', manifest['sha256'])
        assert profiles[manifest['source_id']]['source_sha256'] == manifest['sha256']
    assert Counter(r['source_id'] for r in samples) == {sid: 100 for sid in profiles}
    assert len(samples) == 600
    for sid, profile in profiles.items():
        group = [r for r in samples if r['source_id'] == sid]
        assert len({r['ordinal'] for r in group}) == 100
        assert profile['sample_rows'] == 100 and profile['rows'] >= 100
        for row in group:
            for field in ('flood_evidence', 'urgency_input', 'trapped_count',
                          'vulnerability_input', 'incident_gold'):
                assert row[field] == 'False', 'A source label/input was inferred without evidence'
    assert profiles['D04']['rows'] == 200 and profiles['D04']['full_tweet_text_rows'] == 0
    assert profiles['D06']['rows'] == 360
    assert all(not row['reference_priority'] == 'True' or row['source_id'] == 'D02'
               for row in samples)
    assert not csv_rows('annotation-template.csv'), 'The template must not contain invented annotations'
    for path in ROOT.glob('*.md'):
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text()):
            if target.startswith(('https://', 'http://', '#')):
                continue
            local = target.split('#')[0]
            assert (path.parent / local).exists(), f'Broken local link: {path.name} -> {target}'
    print(json.dumps({'status': 'PASS', 'papers': len(papers), 'targeted_full_text_reviews': len(deep),
                      'queries': len(queries), 'candidate_sources': len(datasets),
                      'profiled_sources': len(profiles), 'presence_sample_rows': len(samples),
                      'new_human_annotations': 0, 'new_RQ_experiment_results': 0}, indent=2))


if __name__ == '__main__':
    main()
