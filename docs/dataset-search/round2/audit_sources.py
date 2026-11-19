#!/usr/bin/env python3
"""Reproduce round-2 file checks without exporting message text or contacts.

Python 3.10+, standard library. Raw files remain in --cache. --download fetches
only the seven reviewed public files and verifies the recorded byte hashes.
These checks measure structure/presence, not human annotation correctness.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import urllib.request
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_CACHE = Path('/tmp/nckh2-dataset-search-round2-20261029')
FIELDS = ['source_id', 'ordinal', 'text_present', 'structured_coordinates',
          'timestamp_field', 'topic_or_action_label', 'graded_priority_label',
          'same_incident_gold']


def digest(content):
    return hashlib.sha256(content).hexdigest()


def duplicates(values):
    return sum(n - 1 for n in Counter(v for v in values if v).values())


def csv_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def common(rows, id_key, text_key=None):
    return {
        'rows': len(rows), 'columns': sorted({k for row in rows for k in row}),
        'duplicate_id_excess': duplicates(str(r[id_key]) for r in rows),
        'empty_text_rows': (sum(not r.get(text_key, '').strip() for r in rows)
                            if text_key else None),
        'exact_nonempty_text_duplicate_excess': (
            duplicates(r.get(text_key, '').strip() for r in rows) if text_key else None),
    }


def haiti(cache):
    rows = csv_rows(cache / 'ushahidi_mirror.csv')
    result = common(rows, 'Serial', 'DESCRIPTION')
    result['missing_fields'] = {k: sum(not r.get(k, '').strip() for r in rows)
                                for k in rows[0]}
    points, dates, invalid = [], [], 0
    for row in rows:
        try:
            lat, lon = float(row['LATITUDE']), float(row['LONGITUDE'])
            assert math.isfinite(lat) and math.isfinite(lon)
            assert -90 <= lat <= 90 and -180 <= lon <= 180
            points.append((lat, lon))
        except (AssertionError, ValueError):
            invalid += 1
        try:
            dates.append(datetime.strptime(row['INCIDENT DATE'], '%d/%m/%Y %H:%M'))
        except ValueError:
            pass
    result.update(valid_coordinate_rows=len(points), invalid_coordinate_rows=invalid,
                  distinct_coordinate_pairs=len(set(points)),
                  largest_shared_point_group=max(Counter(points).values()),
                  parsed_timestamp_rows=len(dates), timezone='not specified in CSV',
                  earliest_timestamp=min(dates).isoformat(),
                  latest_timestamp=max(dates).isoformat())
    categories = Counter(c.strip() for row in rows for c in row['CATEGORY'].split(',') if c.strip())
    trapped = [r for r in rows if any(c.strip().startswith('1c.')
                                     for c in r['CATEGORY'].split(','))]
    result.update(category_counts=dict(categories), people_trapped_topic_rows=len(trapped),
                  people_trapped_distinct_points=len({(r['LATITUDE'], r['LONGITUDE']) for r in trapped}),
                  people_trapped_verified_counts=dict(Counter(r['VERIFIED'] for r in trapped)),
                  approved_counts=dict(Counter(r['APPROVED'] for r in rows)),
                  verified_counts=dict(Counter(r['VERIFIED'] for r in rows)))
    result['limitations'] = [
        'CSV is an export from a crisis map, not established raw inbound message history.',
        'Serial identifies exported records, not independently labelled physical incident groups.',
        'Valid numeric coordinates do not establish precise rescue sites; shared points may be geocoding defaults.',
        'People trapped is a topic label, not a count, priority grade or incident linkage.',
        'Earthquake domain; flood evidence and observed rescue benefit absent.',
        'Original catalog download is 404; mirror version/rights require source reconciliation.',
    ]
    return result, rows, lambda r: dict(text_present=bool(r['DESCRIPTION'].strip()),
        structured_coordinates=bool(r['LATITUDE'] and r['LONGITUDE']),
        timestamp_field=bool(r['INCIDENT DATE']), topic_or_action_label=bool(r['CATEGORY']))


def quatred(cache):
    rows = json.loads((cache / 'quatred.json').read_text())
    flat = [dict(r, text=''.join(r['tweet'])) for r in rows]
    result = common(flat, 'tweetId', 'text')
    # Report the released schema, not the temporary convenience field above.
    result['columns'] = sorted({k for r in rows for k in r})
    result['entity_counts'] = dict(Counter(e[2] for r in rows for e in r['entities']))
    result['relation_counts'] = dict(Counter(e[4] for r in rows for e in r['relations']))
    result['rows_with_place_impact_relation'] = sum(
        any(e[4] == 'place_impact_rel' for e in r['relations']) for r in rows)
    result['limitations'] = [
        'Entity/relation spans are within a tweet, not cross-report incident identity.',
        'No structured timestamp or resolved coordinates in this JSON.',
        'Severity or quantity mixes damage scale, duration and numbers; not trapped-person gold.',
        'No explicit data licence found in inspected repository tree/README; reuse needs clarification.',
    ]
    return result, rows, lambda r: dict(text_present=bool(''.join(r['tweet']).strip()),
                                       topic_or_action_label=bool(r['entities']))


def french(cache):
    rows = csv_rows(cache / 'french.csv')
    result = common(rows, 'tweetID')
    groups = {}
    for row in rows:
        groups.setdefault(row['tweetID'], []).append(row)
    repeated = [group for group in groups.values() if len(group) > 1]
    result['repeated_id_groups'] = len(repeated)
    result['repeated_id_urgency_conflicts'] = sum(
        len({r['urgency_annotation'] for r in group}) > 1 for group in repeated)
    result['repeated_id_crisis_conflicts'] = sum(
        len({r['crisisname'] for r in group}) > 1 for group in repeated)
    for key in ['crisisname', 'period', 'relatedness_annotation', 'urgency_annotation', 'intention_annotation']:
        result[key + '_counts'] = dict(Counter(r[key] for r in rows))
    result['limitations'] = [
        'Released CSV contains IDs and labels only; tweet content needs authorized rehydration.',
        'Period is Before/During/After/NA, not a timestamp; crisisname is not a rescue incident.',
        'Three labels include NotUseful; relevant urgency is binary, not three graded priorities.',
        '2020 base corpus is not the full 19,595-tweet collection described in the 2024 paper.',
        'Related to CrisisTS French sources; do not count publications as independent corpora.',
    ]
    return result, rows, lambda r: dict(topic_or_action_label=bool(r['urgency_annotation']))


def mash(cache):
    parts = {platform: csv_rows(cache / ('mash_' + platform + '.csv'))
             for platform in ['reddit', 'tiktok', 'youtube']}
    rows = [dict(r, platform=platform) for platform, part in parts.items() for r in part]
    result = {'rows': len(rows), 'columns': sorted({k for r in rows for k in r if k != 'platform'}),
              'platform_rows': {k: len(v) for k, v in parts.items()},
              'duplicate_platform_id_excess': duplicates((r['platform'], r['id']) for r in rows),
              'request_label_rows': sum(r['Request'] == 'True' for r in rows),
              'information_integrity_counts': dict(Counter(r['Information_Integrity'] for r in rows))}
    result['limitations'] = [
        'Only platform IDs and annotations released, with no text, timestamp or coordinates.',
        'Human-MLLM collaborative labels; not all labels were independently assigned by humans.',
        'Request is a humanitarian topic; information integrity is not urgency or rescue benefit.',
        'v1 article included X/98,662 posts; v2 and inspected release omit X/59,607 posts.',
    ]
    return result, rows, lambda r: dict(topic_or_action_label=True)


def actionable(cache):
    with zipfile.ZipFile(cache / 'requests_offers.zip') as archive:
        assert archive.testzip() is None, 'ZIP CRC failure'
        real = json.loads(archive.read('request_offers_data/real_data.json'))
        synthetic = json.loads(archive.read('request_offers_data/synthetic_data.json'))
        members = [{'name': x.filename, 'bytes': x.file_size} for x in archive.infolist()]
    labels = [r['classification'] for r in real]
    result = {
        'rows': len(real), 'unit': 'real_data.json records only',
        'synthetic_rows_excluded': len(synthetic), 'archive_members': members,
        'columns': sorted({k for r in real for k in r}),
        'classification_fields': sorted({k for c in labels for k in c}),
        'empty_text_rows': sum(not r['text'].strip() for r in real),
        'exact_nonempty_text_duplicate_excess': duplicates(r['text'].strip() for r in real),
        'real_synthetic_exact_text_overlap': len({r['text'] for r in real} & {r['text'] for r in synthetic}),
        'alpha_counts': dict(Counter(str(c.get('alpha', 'MISSING')) for c in labels)),
        'actionability_counts': dict(Counter(str(c.get('actionability', 'MISSING')) for c in labels)),
        'nonempty_location_annotation_rows': sum(bool(c.get('location')) for c in labels),
        'nonempty_time_annotation_rows': sum(bool(c.get('time')) for c in labels),
    }
    result['limitations'] = [
        'Location/time are classification fields, not established structured coordinates/event timestamps.',
        'Alpha/actionability do not establish an independently judged rescue-priority target.',
        'No per-row event, original platform ID, annotator provenance or incident linkage in top-level schema.',
        'Source page citation is Coming soon; no peer-reviewed dataset paper verified.',
        'Synthetic records are explicitly excluded from the real-data profile and proposed evaluation.',
    ]
    return result, real, lambda r: dict(text_present=bool(r['text'].strip()),
                                       topic_or_action_label=bool(r['classification']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=DEFAULT_CACHE)
    parser.add_argument('--output', type=Path, default=ROOT / 'audit')
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'sources.json').read_text())
    args.cache.mkdir(parents=True, exist_ok=True)
    for entry in manifest:
        path = args.cache / entry['file']
        if not path.exists() and args.download:
            url = entry.get('pinned_url') or entry['url']
            request = urllib.request.Request(url, headers={'User-Agent': 'nckh2-dataset-audit/2'})
            with urllib.request.urlopen(request, timeout=45) as response:
                body = response.read(20_000_001)
            assert len(body) <= 20_000_000, 'Download exceeds size limit'
            assert digest(body) == entry['sha256'], 'Remote snapshot changed: ' + entry['file']
            path.write_bytes(body)
        assert path.exists(), 'Missing cache file; use --download: ' + str(path)
        assert digest(path.read_bytes()) == entry['sha256'], 'Checksum mismatch: ' + entry['file']
    profiles, samples = {}, []
    for sid, fn in [('A02', haiti), ('A03', quatred), ('A05', french), ('A06', mash), ('A07', actionable)]:
        profile, rows, present = fn(args.cache)
        profile['source_hashes'] = {m['file']: m['sha256'] for m in manifest if m['source_id'] == sid}
        profile['sample_rows'] = min(100, len(rows))
        profiles[sid] = profile
        for i in range(profile['sample_rows']):
            ordinal = i * len(rows) // profile['sample_rows']
            sample = dict.fromkeys(FIELDS, False)
            sample.update(source_id=sid, ordinal=ordinal + 1)
            sample.update(present(rows[ordinal]))
            samples.append(sample)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'profiles.json').write_text(json.dumps({
        'scope': 'Schema/presence checks only; no human labelling or RQ experiments',
        'sources': profiles}, ensure_ascii=False, indent=2) + '\n')
    with (args.output / 'sample-presence.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(samples)
    print(json.dumps({'status': 'PASS', 'profiled_families': len(profiles),
                      'data_files': len(manifest), 'presence_rows': len(samples),
                      'human_annotations_created': 0, 'RQ_experiments_run': 0}))


if __name__ == '__main__':
    main()
