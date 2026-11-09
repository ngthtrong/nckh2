"""Independent artifact checks and metric calculation from persisted predictions."""
from __future__ import annotations

from collections import Counter, defaultdict
import math

import joblib
import numpy as np
from scipy import sparse

from common import BASE, DATA, OUT, PROTOCOL, clean_text, digest, read_csv, read_json, write_json


def main():
    protocol = read_json(PROTOCOL)
    checks = {}
    checks['protocol_lock'] = digest(PROTOCOL) == read_json(OUT / 'selection-lock.json')['protocol_sha256']
    checks['pinned_metadata_hashes'] = all(digest(BASE / r['path']) == r['sha256'] for r in read_json(OUT / 'sources.json'))
    checks['all_downloaded_image_hashes'] = all(digest(BASE / r['path']) == r['sha256'] for r in read_json(OUT / 'image-downloads.json'))
    rows = read_json(DATA / 'dataset.json')
    checks['dataset_hash'] = digest(DATA / 'dataset.json') == read_json(OUT / 'data-audit.json')['dataset_sha256']
    manifest = read_csv(OUT / 'split-manifest.csv')
    checks['manifest_matches_dataset'] = len(rows) == len(manifest) and all(
        all(str(row[k]) == value for k, value in entry.items()) for row, entry in zip(rows, manifest))
    leakage = []
    for i, left in enumerate(rows):
        for right in rows[:i]:
            if left['split'] == right['split']:
                continue
            if any(left[k] == right[k] for k in ['event_name', 'tweet_id', 'text_normalized', 'image_sha256', 'group_id']):
                leakage.append([left['image_id'], right['image_id'], 'identity'])
            if (int(left['dhash'], 16) ^ int(right['dhash'], 16)).bit_count() <= 4:
                leakage.append([left['image_id'], right['image_id'], 'dhash'])
    checks['cross_split_event_identity_and_dhash'] = not leakage
    test = [r for r in rows if r['split'] == 'test']
    checks['heldout_test_event'] = {r['event_name'] for r in test} == {protocol['split']['test_event']}
    metrics = {r['model']: r for r in read_csv(OUT / 'metrics.csv')}
    predictions = read_csv(OUT / 'test-predictions.csv')
    matrices = read_json(OUT / 'confusion-matrices.json')['models']
    gold = {r['image_id']: r['label'] for r in test}
    order = protocol['label_order']
    by_model = defaultdict(list)
    for row in predictions:
        by_model[row['model']].append(row)
    checks['seven_expected_configurations'] = len(metrics) == len(by_model) == 7
    metric_errors = []
    for name, selected in by_model.items():
        checks[f'{name}_same_test_ids'] = len(selected) == len(gold) and {r['image_id'] for r in selected} == set(gold)
        matrix = [[0, 0], [0, 0]]
        for row in selected:
            assert row['gold'] == gold[row['image_id']]
            prob = float(row['prob_informative'])
            assert 0 <= prob <= 1
            assert row['prediction'] == order[int(prob >= .5)]
            matrix[order.index(row['gold'])][order.index(row['prediction'])] += 1
        tp = [matrix[i][i] for i in range(2)]
        recall = [tp[i] / sum(matrix[i]) for i in range(2)]
        f1 = sum(2 * tp[i] / (sum(matrix[i]) + sum(r[i] for r in matrix)) for i in range(2)) / 2
        calculated = {'macro_f1': f1, 'accuracy': sum(tp) / len(selected),
                      'recall_informative': recall[1], 'balanced_accuracy': sum(recall) / 2}
        assert matrix == matrices[name]
        for field, value in calculated.items():
            if not math.isclose(float(metrics[name][field]), value, abs_tol=1e-12):
                metric_errors.append([name, field])
    checks['persisted_confusions_and_28_metrics'] = not metric_errors
    selections = read_csv(OUT / 'model-selection.csv')
    training = read_json(OUT / 'training.json')
    checks['dev_only_C_selection'] = all(
        float(max([r for r in selections if r['model'] == name],
                  key=lambda r: (float(r['validation_macro_f1']), -float(r['C'])))['C']) == c
        for name, c in training['selected_C'].items())
    bundle = joblib.load(BASE / 'models/classifiers.joblib')
    checks['fitted_model_hash'] = digest(BASE / 'models/classifiers.joblib') == training['model_sha256']
    cache = np.load(BASE / 'features/embeddings.npz')
    image = cache['embeddings'][[i for i, r in enumerate(rows) if r['split'] == 'test']]
    text = bundle['vectorizer'].transform([clean_text(r['tweet_text']) for r in test])
    concat = sparse.hstack([text, sparse.csr_matrix(image)], format='csr') / np.sqrt(2)
    for name, x in [('text_tfidf_lr', text), ('image_frozen_lr', image), ('feature_concat_lr', concat)]:
        p = bundle['models'][name].predict_proba(x)[:, 1]
        checks[f'{name}_reload_predictions'] = np.allclose(p, [float(r['prob_informative']) for r in by_model[name]], atol=1e-12, rtol=0)
    for r in read_csv(OUT / 'paired-effects.csv'):
        comparator = r['contrast'].split(' - ')[1]
        observed = float(metrics['feature_concat_lr']['macro_f1']) - float(metrics[comparator]['macro_f1'])
        checks[f'effect_{comparator}'] = math.isclose(float(r['delta_macro_f1']), observed, abs_tol=1e-12)
    result_files = ['protocol.json', 'selection-lock.json', 'sources.json', 'image-downloads.json',
                    'split-manifest.csv', 'data-audit.json', 'features.json', 'training.json', 'model-selection.csv',
                    'metrics.csv', 'test-predictions.csv', 'paired-effects.csv', 'confusion-matrices.json', 'evaluation.json']
    status = 'PASS_PUBLIC_PILOT' if all(bool(v) for v in checks.values()) else 'FAIL'
    write_json(OUT / 'verification.json', {'status': status, 'checks': {k: bool(v) for k, v in checks.items()},
                'leakage': leakage, 'metric_errors': metric_errors,
                'result_hashes': {str(OUT.relative_to(BASE.parents[1]) / f): digest(OUT / f) for f in result_files},
                'scope': 'recomputed metrics, hashes, split leakage and reloaded predictions; not full training reproduction or scientific acceptance'})
    print(status, 'checks=', len(checks), 'passed=', sum(bool(v) for v in checks.values()))
    if status != 'PASS_PUBLIC_PILOT':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
