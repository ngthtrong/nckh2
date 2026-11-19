"""Freeze AI translations/labels before classifier fitting; preserve exclusions."""
from __future__ import annotations

from collections import Counter

from common import BASE, LABELS, OUT, PROTOCOL, ROOT, TASK, clean_text, digest, read_json, write_json


def main():
    source = ROOT / 'thucnghiem/multimodal/data/dataset.json'
    protocol = read_json(PROTOCOL)
    if digest(source) != protocol['source_dataset_sha256']:
        raise ValueError('Original source dataset changed')
    selected = read_json(BASE / 'data/selection.json')
    if digest(BASE / 'data/selection.json') != protocol['selection_sha256']:
        raise ValueError('Selection changed')
    annotations = []
    for i in range(1, 4):
        inputs = read_json(OUT / 'label-batches' / f'input-{i}.json')
        outputs = read_json(OUT / 'label-batches' / f'output-{i}.json')
        if (len(outputs) != len(inputs) or len({r['image_id'] for r in outputs}) != len(outputs)
                or {r['image_id'] for r in outputs} != {r['image_id'] for r in inputs}):
            raise ValueError('AI annotation IDs do not match batch')
        annotations.extend(outputs)
    labels = {r['image_id']: r for r in annotations}
    if len(labels) != len(selected):
        raise ValueError('Missing/duplicate AI annotation')
    kept, excluded = [], []
    for r in selected:
        a = labels[r['image_id']]
        if a['label'] not in LABELS + ['uncertain'] or not a['rationale'].strip():
            raise ValueError('Invalid annotation')
        if not clean_text(a['text_vi']):
            raise ValueError('Empty translated text')
        image = ROOT / 'thucnghiem/multimodal/data' / r['image']
        if digest(image) != r['image_sha256']:
            raise ValueError('Image hash mismatch')
        row = dict(r, **{k: a[k] for k in ['text_vi', 'label', 'rationale']})
        row['image_path'] = str(image.relative_to(ROOT))
        row['label_origin'] = 'AI_SILVER_TEXT_ONLY'
        row['translation_origin'] = 'Codex assistant/native subagents, one pass'
        if a['label'] == 'uncertain':
            excluded.append(row)
        else:
            kept.append(row)
    write_json(BASE / 'data/dataset.json', {'task': TASK, 'label_origin': 'AI_SILVER_TEXT_ONLY',
               'language': 'vi_machine_translated_from_english', 'records': kept})
    write_json(BASE / 'data/excluded.json', excluded)
    write_json(OUT / 'dataset-lock.json', {
        'status': 'SILVER_DATA_FROZEN_BEFORE_CLASSIFIER_FITTING',
        'dataset_sha256': digest(BASE / 'data/dataset.json'),
        'protocol_sha256': digest(PROTOCOL),
        'selection_sha256': digest(BASE / 'data/selection.json'),
        'annotation_sha256': {f'output-{i}.json': digest(OUT / 'label-batches' / f'output-{i}.json') for i in range(1, 4)},
        'counts': {s: dict(Counter(r['label'] for r in kept if r['split'] == s)) for s in ['train', 'dev', 'test']},
        'selected': len(selected), 'kept': len(kept), 'excluded_uncertain': len(excluded),
        'human_labels': 0, 'expert_approvals': 0,
        'limits': 'AI silver, translated foreign-event text, enrichment and pre-seen event holdout; not human or pair gold'})
    from common import load_data
    load_data()
    print('Frozen:', len(kept), 'retained;', len(excluded), 'uncertain excluded', flush=True)


if __name__ == '__main__':
    main()
