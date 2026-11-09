"""Evaluate locked heads against AI silver labels on one held-out event.

Predictions are written and hashed before metrics or paired effects are computed.
These results do not use independent human labels and are not operational evidence.
"""
from __future__ import annotations

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score

from common import BASE, LABELS, OUT, PROTOCOL, TASK, clean_text, digest, load_data, read_json, write_csv, write_json
from train import concat


CONFIGURATIONS = ['B0', 'T0', 'T1', 'I0', 'F0', 'F1', 'P0', 'F1_mask_image', 'F1_mask_text']
COMPARATORS = ['T1', 'I0', 'P0']


def check_bindings(info, dataset_hash, protocol_hash, cache_hash):
    for key, expected in [('dataset_sha256', dataset_hash), ('protocol_sha256', protocol_hash),
                          ('cache_sha256', cache_hash)]:
        if info.get(key) != expected:
            raise ValueError('Artifact binding mismatch: ' + key)


def request_probability(classifier, matrix):
    if list(classifier.classes_) != [0, 1]:
        raise ValueError('Classifier label order differs from [0, 1]')
    probability = np.asarray(classifier.predict_proba(matrix)[:, 1], dtype=np.float64)
    if not np.isfinite(probability).all() or np.any((probability < 0) | (probability > 1)):
        raise ValueError('Invalid classifier probabilities')
    return probability


def main():
    names = ['predictions.csv', 'metrics.csv', 'paired-effects.csv', 'evaluation.json']
    if any((OUT / name).exists() for name in names):
        raise SystemExit('Refusing to overwrite evaluation outputs')
    rows = load_data()
    protocol = read_json(PROTOCOL)
    dataset_hash = digest(BASE / 'data/dataset.json')
    protocol_hash = digest(PROTOCOL)
    cache_path = BASE / 'cache/embeddings.npz'
    cache_hash = digest(cache_path)
    feature_info = read_json(OUT / 'features.json')
    training = read_json(OUT / 'training.json')
    check_bindings(feature_info, dataset_hash, protocol_hash, cache_hash)
    check_bindings(training, dataset_hash, protocol_hash, cache_hash)
    model_path = BASE / 'models/classifiers.joblib'
    model_hash = digest(model_path)
    if model_hash != training['model_sha256']:
        raise ValueError('Model file changed after training')
    # Only the locally produced, hash-bound artifact is deserialized.
    bundle = joblib.load(model_path)
    check_bindings(bundle, dataset_hash, protocol_hash, cache_hash)
    if bundle.get('task') != TASK or bundle.get('label_order') != LABELS:
        raise ValueError('Wrong model task or label order')
    with np.load(cache_path, allow_pickle=False) as cache:
        if list(cache['image_ids']) != [r['image_id'] for r in rows]:
            raise ValueError('Feature/sample alignment mismatch')
        indices = np.array([i for i, row in enumerate(rows) if row['split'] == 'test'])
        text = cache['text'][indices]
        image = cache['image'][indices]
    if not np.isfinite(text).all() or not np.isfinite(image).all():
        raise ValueError('Nonfinite test features')
    test = [rows[i] for i in indices]
    if not test:
        raise ValueError('Empty test set')
    if len({r['event_name'] for r in test}) != 1:
        raise ValueError('This locked pilot expects one test event')
    tfidf = bundle['vectorizer'].transform([clean_text(r['text_vi']) for r in test])
    models = bundle['models']
    probabilities = {
        'B0': np.full(len(test), float(bundle['majority'])),
        'T0': request_probability(models['T0'], tfidf),
        'T1': request_probability(models['T1'], text),
        'I0': request_probability(models['I0'], image),
        'F0': request_probability(models['F0'], concat(tfidf, image)),
        'F1': request_probability(models['F1'], concat(text, image)),
        'F1_mask_image': request_probability(models['F1'], concat(text, np.zeros_like(image))),
        'F1_mask_text': request_probability(models['F1'], concat(np.zeros_like(text), image)),
    }
    probabilities['P0'] = (probabilities['T1'] + probabilities['I0']) / 2
    threshold = float(protocol['classifier']['threshold'])
    predicted = {name: (probabilities[name] >= threshold).astype(np.int64) for name in CONFIGURATIONS}
    prediction_rows = []
    for name in CONFIGURATIONS:
        for row, probability, prediction in zip(test, probabilities[name], predicted[name]):
            prediction_rows.append({'model': name, 'image_id': row['image_id'],
                'group_id': row['group_id'], 'event_name': row['event_name'],
                'probability_request': float(probability), 'predicted_label': LABELS[int(prediction)],
                'label_ai': row['label']})
    # Freeze full-precision predictions before any metric calculation.
    write_csv(OUT / 'predictions.csv', prediction_rows)
    prediction_hash = digest(OUT / 'predictions.csv')
    label_ai = np.array([LABELS.index(row['label']) for row in test], dtype=np.int64)
    metrics = []
    for name in CONFIGURATIONS:
        prediction = predicted[name]
        tn, fp, fn, tp = confusion_matrix(label_ai, prediction, labels=[0, 1]).ravel()
        metrics.append({'model': name, 'n': len(test),
            'accuracy': float(accuracy_score(label_ai, prediction)),
            'macro_f1': float(f1_score(label_ai, prediction, labels=[0, 1], average='macro', zero_division=0)),
            'precision_request': float(precision_score(label_ai, prediction, labels=[0, 1], zero_division=0)),
            'recall_request': float(recall_score(label_ai, prediction, labels=[0, 1], zero_division=0)),
            'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp)})
    write_csv(OUT / 'metrics.csv', metrics)
    by_group = {}
    for i, row in enumerate(test):
        by_group.setdefault(row['group_id'], []).append(i)
    group_order = sorted(by_group)
    members = [np.array(by_group[group], dtype=np.int64) for group in group_order]
    draws = int(protocol['bootstrap']['draws'])
    seed = int(protocol['classifier']['seed'])
    generator = np.random.default_rng(seed)
    effects = {name: [] for name in COMPARATORS}
    absent_class_draws = 0
    for _ in range(draws):
        picked = generator.integers(0, len(members), size=len(members))
        idx = np.concatenate([members[i] for i in picked])
        yy = label_ai[idx]
        absent_class_draws += int(len(np.unique(yy)) < 2)
        f1 = float(f1_score(yy, predicted['F1'][idx], labels=[0, 1], average='macro', zero_division=0))
        for name in COMPARATORS:
            baseline = float(f1_score(yy, predicted[name][idx], labels=[0, 1], average='macro', zero_division=0))
            effects[name].append(f1 - baseline)
    primary = training['primary_comparator_selected_on_dev']
    if primary not in ['T1', 'I0']:
        raise ValueError('Primary comparator was not selected from locked unimodal candidates')
    macro = {row['model']: row['macro_f1'] for row in metrics}
    paired = []
    for name in COMPARATORS:
        lower, upper = np.quantile(effects[name], [0.025, 0.975])
        paired.append({'comparator': name, 'delta': macro['F1'] - macro[name],
            'ci_low': float(lower), 'ci_high': float(upper), 'primary': name == primary,
            'draws': draws, 'adjusted': False})
    write_csv(OUT / 'paired-effects.csv', paired)
    write_json(OUT / 'evaluation.json', {'status': 'EXECUTED_AGAINST_AI_SILVER_LABELS',
        'task': TASK, 'label_origin': 'AI_SILVER_TEXT_ONLY', 'dataset_sha256': dataset_hash,
        'protocol_sha256': protocol_hash, 'cache_sha256': cache_hash, 'model_sha256': model_hash,
        'features_receipt_sha256': digest(OUT / 'features.json'),
        'training_receipt_sha256': digest(OUT / 'training.json'),
        'predictions_sha256': prediction_hash, 'metrics_sha256': digest(OUT / 'metrics.csv'),
        'paired_effects_sha256': digest(OUT / 'paired-effects.csv'),
        'n_test': len(test), 'groups': len(members), 'events': sorted({r['event_name'] for r in test}),
        'prediction_rows': len(prediction_rows), 'configurations': CONFIGURATIONS,
        'primary_comparator_selected_on_dev': primary, 'threshold': threshold,
        'bootstrap_draws': draws, 'bootstrap_seed': seed, 'bootstrap_group_order': group_order,
        'bootstrap_absent_class_draws': absent_class_draws,
        'bootstrap_quantile': 'numpy.quantile default linear, 0.025/0.975; paired shared draws',
        'scope': 'Exploratory unadjusted one-event conditional CIs against translated-text AI silver labels',
        'limits': ['No independent human or expert labels; labels came from English source text only',
                   'Not a native-Vietnamese rescue benchmark or calibrated operational urgency score',
                   'No encoder fine-tuning, joint training, Android or rescue-effectiveness validation',
                   'Prior held-out English pilot event had already been examined; retrospective development evidence'],
        'source_sha256': {name: digest(BASE / name) for name in ['common.py', 'train.py', 'evaluate.py']}})
    print(f'Evaluated {len(CONFIGURATIONS)} configurations on {len(test)} AI-silver test pairs; '
          f'{len(prediction_rows)} predictions, {draws} paired draws', flush=True)


if __name__ == '__main__':
    main()
