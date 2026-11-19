"""Acquire pinned original agreed-label metadata and a deterministic event pilot.

No labels are generated. Original split membership is retained for lineage, but
this study deliberately constructs a different, event-held-out split.
"""
from __future__ import annotations

import concurrent.futures
import csv
import hashlib
import io
import time
from collections import Counter, defaultdict

import requests
from PIL import Image, ImageOps

from common import (BASE, DATA, OUT, PROTOCOL, UnionFind, clean_text, digest,
                    link_equal, read_json, write_csv, write_json)


def download(url, path):
    if path.is_file():
        return {'url': url, 'sha256': digest(path), 'bytes': path.stat().st_size,
                'cache': True, 'attempts': []}
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.part')
    tmp.write_bytes(response.content)
    tmp.replace(path)
    return {'url': url, 'sha256': digest(path), 'bytes': path.stat().st_size,
            'cache': False, 'attempts': [{'status': response.status_code}]}


def image_receipt(row, protocol):
    url = (f"https://huggingface.co/datasets/{protocol['image_repo']}/resolve/"
           f"{protocol['image_revision']}/{row['image']}")
    path = DATA / row['image']
    receipt = {'pair_id': row['image_id'], 'path': str(path.relative_to(BASE))}
    try:
        receipt.update(download(url, path))
        with Image.open(path) as im:
            rgb = ImageOps.exif_transpose(im).convert('RGB')
            small = list(rgb.convert('L').resize((9, 8), Image.Resampling.BILINEAR).getdata())
            dhash = 0
            for y in range(8):
                for x in range(8):
                    dhash = (dhash << 1) | (small[y * 9 + x] > small[y * 9 + x + 1])
            receipt.update(width=rgb.width, height=rgb.height, dhash=f'{dhash:016x}', status='OK')
    except Exception as exc:
        receipt.update(status='FAILED', error=f'{type(exc).__name__}: {exc}')
    return receipt


def main():
    started = time.time()
    protocol = read_json(PROTOCOL)
    if (OUT / 'selection-lock.json').exists():
        raise SystemExit('Selection already exists; refusing to overwrite locked selection')
    DATA.mkdir(parents=True, exist_ok=True)
    sources, rows = [], []
    for split in ('train', 'dev', 'test'):
        filename = f'task_informative_text_img_agreed_lab_{split}.tsv'
        url = (f"https://raw.githubusercontent.com/{protocol['source_repo']}/"
               f"{protocol['source_revision']}/data/task_data/{filename}")
        path = DATA / 'metadata' / filename
        receipt = download(url, path)
        receipt['path'] = str(path.relative_to(BASE))
        sources.append(receipt)
        for row in csv.DictReader(io.StringIO(path.read_text(encoding='utf-8')), delimiter='\t'):
            if row['label'] != row['label_text'] or row['label'] != row['label_image']:
                raise ValueError('Official agreed-label source contains disagreement')
            if row['label'] not in protocol['label_order']:
                raise ValueError('Unexpected target')
            row['official_split'] = split
            row['text_normalized'] = clean_text(row['tweet_text']).lower()
            if not row['text_normalized']:
                raise ValueError('Empty cleaned source text requires explicit disposition')
            rows.append(row)
    card = DATA / 'metadata' / 'QCRI-README.md'
    receipt = download(f"https://huggingface.co/datasets/{protocol['image_repo']}/resolve/"
                       f"{protocol['image_revision']}/README.md", card)
    receipt['path'] = str(card.relative_to(BASE))
    sources.append(receipt)
    write_json(OUT / 'sources.json', sources)
    uf = UnionFind(len(rows))
    link_equal(uf, rows, ['tweet_id', 'text_normalized'])
    groups = defaultdict(list)
    for i, row in enumerate(rows):
        groups[uf.find(i)].append(row)
    metadata_group_count = len(groups)
    eligible, exclusions = [], []
    seed = str(protocol['split']['seed'])
    key = lambda r: hashlib.sha256((seed + r['image_id']).encode()).hexdigest()
    for group in groups.values():
        if len({r['event_name'] for r in group}) > 1:
            exclusions.extend({'pair_id': r['image_id'], 'reason': 'metadata_group_cross_event'} for r in group)
            continue
        ordered = sorted(group, key=key)
        eligible.append(ordered[0])
        exclusions.extend({'pair_id': r['image_id'], 'reason': 'one_pair_per_metadata_group'} for r in ordered[1:])
    config = protocol['split']
    selected = []
    for split, limit in [('train', config['max_train_pairs']), ('dev', config['max_validation_pairs']), ('test', config['test_cap'])]:
        event_filter = lambda r: (
            'test' if r['event_name'] == config['test_event'] else
            'dev' if r['event_name'] == config['validation_event'] else 'train')
        pool = sorted([r for r in eligible if event_filter(r) == split], key=key)
        chosen = pool if limit is None else pool[:limit]
        for r in chosen:
            r['split'] = split
            selected.append(r)
        exclusions.extend({'pair_id': r['image_id'], 'reason': f'prespecified_{split}_cap'} for r in pool[len(chosen):])
    if {r['split'] for r in selected} != {'train', 'dev', 'test'}:
        raise ValueError('Missing split; verify event names without changing protocol to optimize results')
    write_json(DATA / 'selected-before-image-audit.json', selected)
    write_json(OUT / 'selection-lock.json', {
        'protocol_sha256': digest(PROTOCOL), 'source_sha256': [s['sha256'] for s in sources],
        'selected_sha256': digest(DATA / 'selected-before-image-audit.json'),
        'counts': dict(Counter(r['split'] for r in selected)),
        'event_counts': dict(Counter(r['event_name'] for r in selected)),
        'status': 'LOCKED_BEFORE_IMAGE_DOWNLOAD_AND_TRAINING'})
    write_csv(OUT / 'metadata-exclusions.csv', exclusions)
    print('Selection locked:', dict(Counter(r['split'] for r in selected)), flush=True)
    receipts = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(image_receipt, r, protocol) for r in selected]
        for future in concurrent.futures.as_completed(futures):
            receipts.append(future.result())
            if len(receipts) % 100 == 0:
                print(f'Downloaded/checked {len(receipts)}/{len(selected)}; failures={sum(r["status"] != "OK" for r in receipts)}', flush=True)
    receipts.sort(key=lambda r: r['pair_id'])
    write_json(OUT / 'image-downloads.json', receipts)
    failures = [r for r in receipts if r['status'] != 'OK']
    if failures:
        write_json(OUT / 'acquisition-failures.json', failures)
        raise SystemExit(f'{len(failures)} image failures; comparison blocked; no silent replacement')
    by_id = {r['pair_id']: r for r in receipts}
    for row in selected:
        row['image_sha256'] = by_id[row['image_id']]['sha256']
        row['dhash'] = by_id[row['image_id']]['dhash']
    uf = UnionFind(len(selected))
    link_equal(uf, selected, ['tweet_id', 'text_normalized', 'image_sha256'])
    hashes = [int(r['dhash'], 16) for r in selected]
    near_pairs = 0
    for i, h in enumerate(hashes):
        for j in range(i):
            if (h ^ hashes[j]).bit_count() <= 4:
                uf.union(i, j)
                near_pairs += 1
    groups = defaultdict(list)
    for i in range(len(selected)):
        groups[uf.find(i)].append(i)
    contaminated, post_exclusions = set(), []
    for indices in groups.values():
        if len({selected[i]['split'] for i in indices}) > 1:
            contaminated.update(indices)
            post_exclusions.extend({'pair_id': selected[i]['image_id'], 'reason': 'duplicate_component_cross_split'} for i in indices)
    final = []
    for i, row in enumerate(selected):
        if i in contaminated:
            continue
        row['group_id'] = f'g{uf.find(i):05d}'
        final.append(row)
    write_json(DATA / 'dataset.json', final)
    columns = ['image_id', 'tweet_id', 'event_name', 'official_split', 'split', 'label', 'group_id', 'image_sha256', 'dhash']
    write_csv(OUT / 'split-manifest.csv', [{k: r[k] for k in columns} for r in final])
    write_csv(OUT / 'image-audit-exclusions.csv', post_exclusions, ['pair_id', 'reason'])
    write_json(OUT / 'data-audit.json', {
        'source_rows': len(rows), 'metadata_groups': metadata_group_count,
        'selected_before_image_audit': len(selected), 'final_pairs': len(final),
        'split_counts': dict(Counter(r['split'] for r in final)),
        'split_labels': {s: dict(Counter(r['label'] for r in final if r['split'] == s)) for s in ('train','dev','test')},
        'groups_per_split': {s: len({r['group_id'] for r in final if r['split'] == s}) for s in ('train','dev','test')},
        'near_duplicate_pairs_hamming_le4': near_pairs, 'cross_split_removed': len(contaminated),
        'download_decode_failures': 0, 'dataset_sha256': digest(DATA / 'dataset.json'),
        'manifest_sha256': digest(OUT / 'split-manifest.csv'),
        'seconds': time.time() - started,
        'limits': 'One held-out event; dHash is a conservative heuristic, not semantic deduplication; source English card; no independent rescue priority labels'})
    print('Prepared final pairs:', len(final), flush=True)


if __name__ == '__main__':
    main()
