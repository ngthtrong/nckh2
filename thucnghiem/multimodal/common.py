"""Shared paths and deterministic preprocessing for the isolated benchmark."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
OUT = ROOT / 'docs/revision-plan/outputs/multimodal-20261108'
DATA = BASE / 'data'
PROTOCOL = OUT / 'protocol.json'


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def read_json(path: Path):
    return json.loads(path.read_text())


def write_csv(path: Path, rows: list[dict], columns=None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    with path.open(newline='') as f:
        return list(csv.DictReader(f))


def clean_text(text: str) -> str:
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
    text = re.sub(r'@[\w_]+', ' ', text)
    text = re.sub(r'^\s*RT\s*:?', ' ', text, flags=re.I)
    return ' '.join(text.split()).strip()


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, i: int) -> int:
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def union(self, i: int, j: int) -> None:
        a, b = self.find(i), self.find(j)
        if a != b:
            self.parent[max(a, b)] = min(a, b)


def link_equal(uf: UnionFind, rows: list[dict], keys: list[str]) -> None:
    for key in keys:
        seen = {}
        for i, row in enumerate(rows):
            value = row[key]
            if value in seen:
                uf.union(i, seen[value])
            else:
                seen[value] = i
