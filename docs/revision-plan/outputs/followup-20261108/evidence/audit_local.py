"""Read-only follow-up of P02/P05 evidence; writes only beside this script."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import pickletools
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
HASHES = {}


def source(rel):
    p = ROOT / rel
    HASHES[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return p


def rows(rel):
    with source(rel).open() as f:
        return list(csv.DictReader(f))


edge = 'products/fe/model/Edge Ai/'
split_rel = edge + 'split_train_val_test_mobilenetv3_large.csv'
split = rows(split_rel)
after_rel = edge + 'mobilenetv3_large_dataset_v4_seed1024/records_after_clean_mobilenetv3_large.csv'
after = rows(after_rel)
before_rel = edge + 'mobilenetv3_large_dataset_v4_seed1024/records_before_clean_mobilenetv3_large.csv'
before = rows(before_rel)
fields = ['relative_path', 'label', 'label_idx', 'md5', 'source_group', 'dhash', 'perceptual_group', 'split_group']
canonical = lambda records: {r['relative_path']: tuple(r.get(k, '') for k in fields) for r in records}
dataset = {
    'split_rows': len(split),
    'seed1024_records_before': len(before),
    'seed1024_records_after': len(after),
    'split_counts': dict(Counter(r['split'] for r in split)),
    'nonempty_source_group': sum(bool(r['source_group'].strip()) for r in split),
    'split_vs_seed1024_after_clean_all_eight_fields_equal': canonical(split) == canonical(after),
    'claim_limit': 'Matching record inventory and existing split do not identify split bytes at training time.',
}

# Inspect serialized metadata without importing torch or executing pickle objects.
ckpt_rel = edge + 'mobilenetv3_large_dataset_v4_seed1024/flood_mobilenetv3_large_best.pth'
with zipfile.ZipFile(source(ckpt_rel)) as archive:
    member = next(n for n in archive.namelist() if n.endswith('/data.pkl'))
    operations = list(pickletools.genops(archive.read(member)))
    strings = [(arg, pos) for op, arg, pos in operations
               if op.name in ['UNICODE', 'BINUNICODE', 'SHORT_BINUNICODE'] and isinstance(arg, str)]
    key_index = next(i for i, (op, arg, pos) in enumerate(operations) if arg == 'split_csv_path')
    split_path = next(arg for op, arg, pos in operations[key_index+1:] if isinstance(arg, str))
    seed_index = next(i for i, (op, arg, pos) in enumerate(operations) if arg == 'seed')
    seed = next(arg for op, arg, pos in operations[seed_index+1:] if op.name in ['BININT', 'BININT1', 'BININT2', 'INT'])
    checkpoint = {
        'inspection': 'pickletools.genops only; never unpickled',
        'member': member,
        'config_seed': seed,
        'split_csv_path': split_path,
        'hash_named_string_keys': [a for a, pos in strings if re.search('hash|sha256|md5', a, re.I)],
        'claim_limit': 'Path is evidence of intended source location; no historical split byte hash recovered.',
    }

notebook_rel = 'products/fe/model/training_img.ipynb'
nb = json.loads(source(notebook_rel).read_text())
nb_evidence = []
for i, cell in enumerate(nb['cells']):
    text = ''.join(cell.get('source', []))
    outputs = ''.join(''.join(o.get('text', [])) for o in cell.get('outputs', []))
    if 'source_groups.csv' in outputs:
        nb_evidence.append({'cell_index_zero_based': i, 'execution_count': cell.get('execution_count'),
                            'selected_output': [line for line in outputs.splitlines()
                                                if 'source_groups.csv' in line or 'seed599' in line][:8]})

# Expand previous heads/remotes-only check to all locally available refs, including
# tags, stash and Codex captures. Never fetch, checkout, reset or run an app/DB.
refs = subprocess.check_output(['git', 'for-each-ref', '--format=%(refname)'], cwd=ROOT, text=True).splitlines()
hits = []
areas = ['experiment_mobile', 'experiment_mobile_e2e', 'experiment_e2e']
for ref in refs:
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', ref], cwd=ROOT, text=True).splitlines()
    for name in names:
        if (any(a in name for a in areas)
                and any('/' + d + '/' in name for d in ['results', 'logs', 'checkpoints', 'attempts'])
                and name.lower().endswith(('.json', '.jsonl', '.csv', '.txt', '.png', '.jpg'))):
            hits.append({'ref': ref, 'path': name})
local = []
for area in ['products/fe/experiment_mobile', 'thuc_nghiem_nq/experiment_mobile_e2e', 'thuc_nghiem_nq/experiment_e2e']:
    for p in (ROOT / area).rglob('*'):
        if p.is_file() and any(d in p.parts for d in ['results', 'logs', 'checkpoints', 'attempts']):
            local.append(str(p.relative_to(ROOT)))

for rel in [
    'docs/revision-plan/outputs/phase-02/data-card.md',
    'docs/revision-plan/outputs/phase-05/recovery-search.json',
    'docs/revision-plan/outputs/phase-05/drive-recovery.json',
    'docs/revision-plan/outputs/phase-07/publication-verification.md',
    'docs/revision-plan/evidence/user-amendments.md',
    'products/fe/experiment_mobile/README.md',
    'thuc_nghiem_nq/experiment_e2e/RESULTS.md',
    'paper/main.tex',
    'docs/ISDS_2026_paper_6444.pdf',
]:
    source(rel)
for p in OUT.glob('*.pdf'):
    HASHES[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()

result = {
    'date': '2026-11-08 Asia/Taipei',
    'verification_status': 'ANALYZED; evidence recovery only',
    'dataset': dataset,
    'checkpoint_metadata': checkpoint,
    'notebook_source_group_evidence': nb_evidence,
    'e2e': {'refs_searched': refs, 'git_raw_hits': hits, 'current_local_output_files': local,
            'scope': 'Current local experiment roots and all locally available refs. No remote fetch, LFS archive retrieval, app, server, DB or device execution.'},
    'unresolved': ['per-image URL/license', 'annotator/IAA', 'event/source independence',
                   'seed1024 training-time split bytes', 'expert dispatch validation',
                   'historical Android/Web E2E raw', 'official chapter DOI/pages/online date/publication year'],
}
(OUT / 'local-evidence-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
(OUT / 'source-hashes.json').write_text(json.dumps(HASHES, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'dataset': dataset, 'checkpoint_metadata': checkpoint,
                  'refs_searched': len(refs), 'git_raw_hits': len(hits), 'local_output_files': local}, ensure_ascii=False, indent=2))
