"""Isolated translated-Vietnamese SILVER pilot; never an expert-gold dataset."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
OUT = ROOT / 'docs/revision-plan/outputs/vi-nlp-fusion-silver-20261108'
PROTOCOL = OUT / 'protocol.json'
TASK = 'vi_translated_silver_request_v1'
LABELS = ['no_request', 'request']


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def write_csv(path, rows, columns=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def clean_text(text):
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
    text = re.sub(r'@[\w_]+', ' ', text)
    return ' '.join(text.split()).strip()


def load_data():
    data = read_json(BASE / 'data/dataset.json')
    lock = read_json(OUT / 'dataset-lock.json')
    if digest(PROTOCOL) != lock['protocol_sha256']:
        raise ValueError('Protocol changed after dataset lock')
    if digest(BASE / 'data/dataset.json') != lock['dataset_sha256']:
        raise ValueError('Dataset changed')
    if data['task'] != TASK or data['label_origin'] != 'AI_SILVER_TEXT_ONLY':
        raise ValueError('Wrong task or label origin')
    rows = data['records']
    if len({r['image_id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate pair IDs')
    for split in ['train', 'dev', 'test']:
        current = [r for r in rows if r['split'] == split]
        other = [r for r in rows if r['split'] != split]
        for key in ['image_id', 'tweet_id', 'group_id', 'image_sha256', 'event_name']:
            if {r[key] for r in current} & {r[key] for r in other}:
                raise ValueError('Cross-split overlap: ' + key)
        texts = {clean_text(r['text_vi']).casefold() for r in current}
        if texts & {clean_text(r['text_vi']).casefold() for r in other}:
            raise ValueError('Translated-text overlap across splits')
        if {r['label'] for r in current} != set(LABELS):
            raise ValueError('A split lacks both classes')
    return rows
