#!/usr/bin/env python3
"""Download/profile reviewed public sources; keep raw content outside the repo.

Requires Python 3.10+ and requests. Default operation is offline against the
cache. --download fetches only entries in sources.json, with a size limit.
Outputs contain schema/counts and presence-only samples, never report text.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import struct
import tarfile
import zipfile
import zlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE = Path('/tmp/nckh2-dataset-search-20261029')
NS = {'t': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
      'x': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'}
SAMPLE_FIELDS = ['source_id', 'ordinal', 'event', 'text', 'location', 'timestamp',
                 'flood_evidence', 'urgency_input', 'trapped_count',
                 'vulnerability_input', 'reference_priority', 'incident_gold']


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_json(path):
    # Some HTTP clients/servers decode Content-Encoding despite a .gz suffix.
    with path.open('rb') as f:
        magic = f.read(2)
    opener = gzip.open if magic == b'\x1f\x8b' else open
    with opener(path, 'rt', encoding='utf-8-sig') as f:
        return json.load(f)


def sample(source_id, rows, presence):
    """Evenly spaced, deterministic 100-row schema sample; not an IID sample."""
    if not rows:
        return []
    n = min(100, len(rows))
    indexes = [i * len(rows) // n for i in range(n)]
    result = []
    for i in indexes:
        event, row = rows[i]
        d = dict.fromkeys(SAMPLE_FIELDS, False)
        d.update(source_id=source_id, ordinal=i + 1, event=event)
        d.update(presence(row))
        result.append(d)
    return result


def profile_humaid(path):
    rows, files, licensing = [], [], ''
    with tarfile.open(path) as archive:
        for member in sorted(archive.getmembers(), key=lambda x: x.name):
            if not member.isfile() or Path(member.name).name.startswith('._'):
                continue
            if member.name.endswith('/Licensing.txt'):
                licensing = archive.extractfile(member).read().decode('utf-8')
            if not member.name.endswith('.tsv'):
                continue
            with io.TextIOWrapper(archive.extractfile(member), encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter='\t')
                part = list(reader)
                files.append({'member': member.name, 'rows': len(part),
                              'columns': reader.fieldnames})
                rows.extend((Path(member.name).parent.name, r) for r in part)
    ids = [r['tweet_id'] for _, r in rows]
    texts = [r['tweet_text'] for _, r in rows]
    profile = {
        'unit': 'tweet; set1 only, all released splits', 'rows': len(rows),
        'files': files, 'columns': sorted({k for _, r in rows for k in r}),
        'event_counts': dict(Counter(e for e, _ in rows)),
        'class_counts': dict(Counter(r['class_label'] for _, r in rows)),
        'duplicate_id_excess': len(ids) - len(set(ids)),
        'exact_nonempty_text_duplicate_excess': len(texts) - len(set(texts)),
        'empty_text_rows': sum(not t.strip() for t in texts),
        'terms_observed': {
            'humanitarian_research_only': 'only for research on humanitarian computing' in licensing,
            'keep_content_confidential': 'confidential' in licensing,
            'delete_on_request_and_completion': 'upon completion' in licensing and 'upon our request' in licensing,
        },
        'limitations': ['No structured coordinates/timestamps/incident linkage/priority in inspected TSVs.',
                        'Class labels are humanitarian topics, not independent rescue benefit.',
                        'Near duplicates were filtered during source construction; raw-copy robustness is not represented.'],
    }
    samples = sample('D01', rows, lambda r: {'text': bool(r['tweet_text'].strip())})
    return profile, samples, set(ids)


def profile_trec(path):
    data = read_json(path)
    rows = [(e['eventid'], r) for e in data['events'] for r in e['tweets']]
    ids = [r['postID'] for _, r in rows]
    texts = [r.get('postText') or '' for _, r in rows]
    fields = sorted({k for _, r in rows for k in r})
    groups = {}
    for event, row in rows:
        groups.setdefault((event, row['postID']), []).append(row)
    repeated = [g for g in groups.values() if len(g) > 1]
    profile = {
        'unit': 'tweet annotation row, historical training bundle 2018-2020B',
        'rows': len(rows), 'events': len(data['events']), 'columns': fields,
        'event_counts': dict(Counter(e for e, _ in rows)),
        'priority_counts': dict(Counter(r.get('postPriority', '') for _, r in rows)),
        'category_counts': dict(Counter(c for _, r in rows for c in r.get('postCategories', []))),
        'duplicate_id_excess': len(ids) - len(set(ids)),
        'exact_nonempty_text_duplicate_excess': sum(bool(t.strip()) for t in texts)
                                                - len({t for t in texts if t.strip()}),
        'empty_text_rows': sum(not t.strip() for t in texts),
        'multiple_judgements_nonnull': sum(r.get('multipleJudgements') is not None for _, r in rows),
        'unique_event_post_pairs': len(groups),
        'repeated_event_post_groups': len(repeated),
        'repeated_groups_conflicting_priority': sum(len({r['postPriority'] for r in g}) > 1 for g in repeated),
        'groups_conflicting_nonempty_text': sum(len({r['postText'] for r in g if r.get('postText')}) > 1
                                               for g in groups.values()),
        'unique_event_post_with_text': sum(any(r.get('postText') for r in g) for g in groups.values()),
        'available_unique_by_event': dict(Counter(event for (event, _), g in groups.items()
                                                if any(r.get('postText') for r in g))),
        'limitations': ['postText is directly available in this downloaded label bundle.',
                        'No structured created_at/coordinates, fine incident gold or rescue-benefit labels.',
                        'postPriority is evaluator-only; never copy it into input urgency E.',
                        'Only historical training bundle audited, not all TREC releases.'],
    }
    samples = sample('D02', rows, lambda r: {'text': bool((r.get('postText') or '').strip()),
                                           'reference_priority': bool(r.get('postPriority'))})
    return profile, samples, set(ids)


def profile_facts(path):
    data = read_json(path)
    rows = [(e['eventID'], r) for e in data for r in e['allFacts']]
    profile = {
        'unit': 'reference fact from allFacts; not a raw social-media report',
        'rows': len(rows), 'events': len(data),
        'columns': sorted({k for _, r in rows for k in r}),
        'event_counts': dict(Counter(e for e, _ in rows)),
        'unique_source_strings': len({str(r.get('source', '')) for _, r in rows}),
        'source_kind_counts': dict(Counter('tweet_id' if str(r.get('source', '')).isdigit()
                                          else 'other_reference' for _, r in rows)),
        'empty_fact_rows': sum(not r.get('fact', '').strip() for _, r in rows),
        'limitations': ['Public reference facts were audited; full source streams were not downloaded.',
                        'dateUnix is a reference-fact/day timestamp, not report receipt time.',
                        'Reference facts and disaster IDs are not fine-grained rescue incident gold.',
                        'The official full-stream downloader asks for institution/contact details.'],
    }
    # A fact date must not be counted as observed input report time.
    samples = sample('D03', rows, lambda r: {'text': bool(r.get('fact', '').strip())})
    return profile, samples, set()


def ods_rows(path):
    table_tag = '{' + NS['t'] + '}table'
    row_tag = '{' + NS['t'] + '}table-row'
    cell_tags = {'{' + NS['t'] + '}table-cell', '{' + NS['t'] + '}covered-table-cell'}
    name_attr = '{' + NS['t'] + '}name'
    repeat_attr = '{' + NS['t'] + '}number-columns-repeated'
    row_repeat_attr = '{' + NS['t'] + '}number-rows-repeated'
    sheet = None
    with zipfile.ZipFile(path) as archive, archive.open('content.xml') as f:
        for event, element in ET.iterparse(f, events=('start', 'end')):
            if event == 'start' and element.tag == table_tag:
                sheet = element.get(name_attr)
            elif event == 'end' and element.tag == row_tag:
                if sheet in ('Datasheet', 'config'):
                    values = []
                    for cell in element:
                        if cell.tag in cell_tags:
                            value = ' '.join(''.join(p.itertext()) for p in cell.findall('x:p', NS))
                            # Trailing empty spreadsheet columns may repeat millions of times.
                            repeat = min(int(cell.get(repeat_attr, '1')), 100) if value else 1
                            values.extend([value] * repeat)
                    if any(values):
                        for _ in range(int(element.get(row_repeat_attr, '1'))):
                            yield sheet, values
                element.clear()


def profile_england(path):
    columns, count, config = None, 0, {}
    counters = {k: Counter() for k in ['FINANCIAL_YEAR', 'INCIDENT_TYPE', 'VEHICLES',
                                      'EVACUATIONS', 'RESCUES', 'FATALITY_CASUALTY']}
    empty = Counter()
    selected = []
    for sheet, values in ods_rows(path):
        if sheet == 'config':
            if len(values) >= 2:
                config[values[0]] = values[1]
            continue
        if columns is None:
            columns = [v for v in values if v]
            continue
        row = dict(zip(columns, values))
        count += 1
        for key in columns:
            empty[key] += not row.get(key, '').strip()
        for key, c in counters.items():
            c[row.get(key, '')] += 1
        # Deterministic first 100 plus whole-data counters; not a random sample.
        if len(selected) < 100:
            selected.append((row.get('FINANCIAL_YEAR', ''), row))
    profile = {
        'unit': 'attended incident, not a citizen report', 'rows': count,
        'columns': columns, 'empty_counts': dict(empty), 'workbook_config': config,
        'distributions': {k: dict(v) for k, v in counters.items()},
        'limitations': ['Only LSOA areas and financial years; no exact coordinates or dispatch timestamps.',
                        'Vehicle/evacuation values include grouped categories and codes, not exact continuous counts.',
                        'Evacuations/rescues/casualties are post-response outcomes, not pre-dispatch trapped count N.',
                        'No row identifier, report text, fine incident linkage or complete dispatch history.'],
    }
    samples = sample('D05', selected, lambda r: {})
    for row in samples:
        row['event'] = 'financial_year:' + row['event']
    return profile, samples, set()


def profile_figshare(path):
    data = read_json(path)
    subset = path.parent / 'ld10_batch1.json'
    rows = [json.loads(line) for line in subset.read_text().splitlines() if line.strip()]
    annotations = [a for r in rows for a in r.get('Annotation', [])]
    profile = {
        'unit': 'tweet annotation row; only Batch1-StlouisFloods-All.json',
        'rows': len(rows), 'version': data.get('version'), 'doi': data.get('doi'),
        'columns': sorted({k for r in rows for k in r}),
        'annotation_columns': sorted({k for a in annotations for k in a}),
        'annotation_count': len(annotations),
        'topic_counts': dict(Counter(r['MessageTopic'] for r in rows)),
        'location_category_counts': dict(Counter(a['locationCate'] for a in annotations)),
        'duplicate_id_excess': len(rows) - len({r['id'] for r in rows}),
        'full_tweet_text_rows': sum(bool(r.get('text') or r.get('tweet_text')) for r in rows),
        'rows_with_spatial_annotation': sum(any(a.get('spatialFootprint') for a in r.get('Annotation', [])) for r in rows),
        'subset_sha256': sha256(subset),
        'license': data.get('license'),
        'files': [{k: f.get(k) for k in ('id', 'name', 'size', 'download_url', 'computed_md5')}
                  for f in data.get('files', [])],
        'limitations': ['Only one 200-row St Louis flood batch was read by HTTP range; not all 7149 tweets.',
                        'IDs and location/topic annotations are available; full tweet text is absent.',
                        'Spatial footprints include non-victim locations and non-point geometries.',
                        'No fine incident gold, independent rescue-benefit labels or dispatch logs.'],
    }
    samples = sample('D04', [('StlouisFloods_Batch1', r) for r in rows],
                     lambda r: {'location': any(a.get('spatialFootprint') for a in r.get('Annotation', []))})
    # Presence of a footprint does not imply an exact rescue-destination point.
    return profile, samples, {r['id'] for r in rows}


def profile_idrisi(path):
    data = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    mentions = [m for r in data for m in r.get('location_mentions', [])]
    def has_coordinates(row):
        for mention in row.get('location_mentions', []):
            geo = mention.get('osm_json')
            if isinstance(geo, dict) and geo.get('lat') is not None and geo.get('lon') is not None:
                return True
        return False
    def valid_point(mention):
        geo = mention.get('osm_json')
        try:
            return -90 <= float(geo['lat']) <= 90 and -180 <= float(geo['lon']) <= 180
        except (TypeError, KeyError, ValueError):
            return False
    dates, date_errors = [], 0
    for row in data:
        try:
            dates.append(datetime.strptime(row['created_at'], '%a %b %d %H:%M:%S %z %Y'))
        except (KeyError, TypeError, ValueError):
            date_errors += 1
    p = {
        'unit': 'released IDRISI-D English Harvey train partition only',
        'rows': len(data), 'columns': sorted({k for r in data for k in r}),
        'location_mention_columns': sorted({k for m in mentions for k in m}),
        'mention_count': len(mentions),
        'class_counts': dict(Counter(str(r.get('humAID_class')) for r in data)),
        'location_type_counts': dict(Counter(str(m.get('type')) for m in mentions)),
        'rows_with_text': sum(bool(r.get('text')) for r in data),
        'rows_with_created_at': sum(bool(r.get('created_at')) for r in data),
        'rows_with_any_osm_latlon': sum(has_coordinates(r) for r in data),
        'duplicate_id_excess': len(data) - len({str(r['tweet_id']) for r in data}),
        'valid_coordinate_mentions': sum(valid_point(m) for m in mentions),
        'invalid_or_missing_coordinate_mentions': sum(not valid_point(m) for m in mentions),
        'created_at_parse_errors': date_errors,
        'created_at_min': min(dates).isoformat() if dates else None,
        'created_at_max': max(dates).isoformat() if dates else None,
        'limitations': ['Location annotation may refer to background/news/resource locations, not a rescue destination.',
                        'Annotator confidence 1/2/3 is not the paper provenance heuristic Q.',
                        'humAID_class is a topic label, not urgency input or evaluation priority.',
                        'The released train/dev data are not an untouched test set; official test is withheld.',
                        'Only one event/partition audited; not a multi-event transfer result.'],
    }
    s = sample('D06', [('hurricane_harvey_2017_train', r) for r in data],
               lambda r: {'text': bool(r.get('text')), 'location': has_coordinates(r),
                          'timestamp': bool(r.get('created_at'))})
    return p, s, {str(r['tweet_id']) for r in data}


PROFILERS = {'humaid_set1.tar.gz': profile_humaid,
             'trecis_train.json.gz': profile_trec,
             'crisisfacts_gold.json': profile_facts,
             'england_flood.ods': profile_england,
             'disasterlocdesc_metadata.json': profile_figshare,
             'idrisi_harvey_train.jsonl': profile_idrisi}


def download(entry, cache):
    import requests
    name, url = entry['file'], entry['url']
    path = cache / name
    if not (path.exists() and sha256(path) == entry.get('sha256')):
        with requests.get(url, stream=True, timeout=(10, 45)) as response:
            response.raise_for_status()
            size = 0
            temporary = path.with_suffix(path.suffix + '.part')
            with temporary.open('wb') as f:
                for chunk in response.iter_content(1024 * 1024):
                    size += len(chunk)
                    if size > 160 * 1024 * 1024:
                        raise ValueError('Source exceeds the 160 MiB per-file download budget')
                    f.write(chunk)
            if entry.get('sha256') and sha256(temporary) != entry['sha256']:
                temporary.unlink()
                raise ValueError(f'Source bytes changed: {name}; review before refreshing the snapshot')
            temporary.replace(path)
    subset = entry.get('subset')
    if subset:
        target = cache / subset['file']
        if target.exists() and sha256(target) == subset['extracted_sha256']:
            return
        with requests.get(subset['url'], headers={'Range': subset['range']},
                          stream=True, timeout=(10, 30)) as response:
            if response.status_code != 206:
                raise ValueError('Partial-content HTTP 206 required; do not fetch the full archive')
            if response.headers.get('Content-Range') != subset['content_range']:
                raise ValueError('Unexpected byte range from source')
            body = bytearray()
            for chunk in response.iter_content(65536):
                body.extend(chunk)
                if len(body) > 2 * 1024 * 1024:
                    raise ValueError('Partial archive exceeds the 2 MiB range budget')
        if hashlib.sha256(body).hexdigest() != subset['range_sha256']:
            raise ValueError('Archive segment bytes changed')
        header = struct.unpack('<4s5H3I2H', body[:30])
        if header[0] != b'PK\x03\x04' or header[3] != 8:
            raise ValueError('Expected a deflated local ZIP entry')
        offset = 30 + header[-2] + header[-1]
        raw = zlib.decompress(body[offset:offset + subset['compressed_bytes']], -15)
        if (hashlib.sha256(raw).hexdigest() != subset['extracted_sha256']
                or zlib.crc32(raw) != subset['crc32']):
            raise ValueError('Extracted member integrity check failed')
        target.write_bytes(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, default=DEFAULT_CACHE)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'audit')
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    entries = json.loads((ROOT / 'audit' / 'sources.json').read_text())
    profiles, samples, identifiers = {}, [], {}
    for entry in entries:
        if args.download:
            download(entry, args.cache_dir)
        path = args.cache_dir / entry['file']
        if sha256(path) != entry['sha256']:
            raise ValueError(f'Checksum mismatch: {entry["file"]}')
        if entry.get('subset'):
            s = entry['subset']
            if sha256(args.cache_dir / s['file']) != s['extracted_sha256']:
                raise ValueError('Subset checksum mismatch')
        profile, part, ids = PROFILERS[entry['file']](path)
        profile['source_sha256'] = entry['sha256']
        profile['sample_rows'] = len(part)
        profile['sample_policy'] = ('first_100_workbook_rows' if entry['source_id'] == 'D05'
                                    else 'evenly_spaced_100_in_source_order' if part else 'not_sampled')
        profiles[entry['source_id']] = profile
        samples.extend(part)
        identifiers[entry['source_id']] = ids
        print(entry['source_id'], 'rows=', profile['rows'], 'sample=', len(part), flush=True)
    overlap = len(identifiers['D01'] & identifiers['D02'])
    result = {'survey_date': '2026-10-29', 'sources': profiles,
              'cross_corpus': {'D01_D02_shared_tweet_ids': overlap,
                              'D01_D06_shared_tweet_ids': len(identifiers['D01'] & identifiers.get('D06', set())),
                              'scope': 'Only the downloaded subsets; zero overlap is not proof of corpus-wide independence.'}}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'profiles.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    with (args.output_dir / 'sample-presence.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=SAMPLE_FIELDS)
        writer.writeheader()
        writer.writerows(samples)


if __name__ == '__main__':
    main()
