"""Evaluate locked selected classifiers and exploratory paired effects."""
from __future__ import annotations

import joblib
import numpy as np
from scipy import sparse
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, recall_score

from common import BASE, DATA, OUT, PROTOCOL, clean_text, digest, read_json, write_csv, write_json
from train import concat_features, validate_dataset


def macro_from_confusion(c):
    tp = np.diagonal(c, axis1=-2, axis2=-1)
    denominator = c.sum(axis=-1) + c.sum(axis=-2)
    f = np.divide(2 * tp, denominator, out=np.zeros_like(tp, dtype=float), where=denominator != 0)
    return f.mean(axis=-1)


def main():
    if (OUT / 'metrics.csv').exists():
        raise SystemExit('Refusing to overwrite test evaluation')
    protocol = read_json(PROTOCOL)
    training = read_json(OUT / 'training.json')
    model_path = BASE / 'models/classifiers.joblib'
    for key, path in [('model_sha256', model_path), ('protocol_sha256', PROTOCOL),
                      ('dataset_sha256', DATA / 'dataset.json'), ('feature_sha256', BASE / 'features/embeddings.npz')]:
        if digest(path) != training[key]:
            raise ValueError(f'Frozen input changed: {key}')
    bundle = joblib.load(model_path)
    rows = read_json(DATA / 'dataset.json')
    validate_dataset(rows, protocol['label_order'])
    indices = np.array([i for i, r in enumerate(rows) if r['split'] == 'test'])
    test = [rows[i] for i in indices]
    image = np.load(BASE / 'features/embeddings.npz')['embeddings'][indices]
    text = bundle['vectorizer'].transform([clean_text(r['tweet_text']) for r in test])
    y = np.array([bundle['label_order'].index(r['label']) for r in test])
    models = bundle['models']
    probs = {
        'majority': np.full(len(test), float(bundle['majority_label'])),
        'text_tfidf_lr': models['text_tfidf_lr'].predict_proba(text)[:, 1],
        'image_frozen_lr': models['image_frozen_lr'].predict_proba(image)[:, 1],
        'feature_concat_lr': models['feature_concat_lr'].predict_proba(concat_features(text, image))[:, 1]}
    probs['mean_probability'] = (probs['text_tfidf_lr'] + probs['image_frozen_lr']) / 2
    probs['concat_missing_image'] = models['feature_concat_lr'].predict_proba(concat_features(text, np.zeros_like(image)))[:, 1]
    probs['concat_missing_text'] = models['feature_concat_lr'].predict_proba(concat_features(sparse.csr_matrix(text.shape), image))[:, 1]
    metrics, predictions, confusions, grouped = [], [], {}, {}
    group_ids, group_index = np.unique([r['group_id'] for r in test], return_inverse=True)
    for name, p in probs.items():
        pred = (p >= .5).astype(int)
        c = confusion_matrix(y, pred, labels=[0, 1])
        metrics.append({'model': name, 'n': len(test), 'macro_f1': f1_score(y, pred, average='macro', labels=[0, 1], zero_division=0),
                        'accuracy': accuracy_score(y, pred), 'recall_informative': recall_score(y, pred, zero_division=0),
                        'balanced_accuracy': balanced_accuracy_score(y, pred)})
        confusions[name] = c.tolist()
        g = np.zeros((len(group_ids), 2, 2), dtype=np.int64)
        np.add.at(g, (group_index, y, pred), 1)
        grouped[name] = g
        predictions.extend({'model': name, 'image_id': row['image_id'], 'group_id': row['group_id'],
                            'event_name': row['event_name'], 'gold': row['label'],
                            'prediction': bundle['label_order'][int(z)], 'prob_informative': float(q)}
                           for row, z, q in zip(test, pred, p))
    # Each multinomial vector represents sampling G duplicate groups with replacement.
    rng = np.random.default_rng(protocol['split']['seed'])
    draws = rng.multinomial(len(group_ids), np.full(len(group_ids), 1 / len(group_ids)), size=2000)
    boot = {name: macro_from_confusion(np.einsum('bg,gij->bij', draws, g)) for name, g in grouped.items()}
    observed = {m['model']: m['macro_f1'] for m in metrics}
    effects = []
    for comparator in ('text_tfidf_lr', 'image_frozen_lr', 'mean_probability'):
        delta = boot['feature_concat_lr'] - boot[comparator]
        low, high = np.percentile(delta, [2.5, 97.5])
        effects.append({'contrast': f'feature_concat_lr - {comparator}',
                        'delta_macro_f1': observed['feature_concat_lr'] - observed[comparator],
                        'ci95_low': float(low), 'ci95_high': float(high), 'test_groups': len(group_ids),
                        'draws': 2000, 'multiplicity': 'unadjusted_exploratory', 'scope': 'conditional_on_one_heldout_event'})
    write_csv(OUT / 'metrics.csv', metrics)
    write_csv(OUT / 'test-predictions.csv', predictions)
    write_csv(OUT / 'paired-effects.csv', effects)
    write_json(OUT / 'confusion-matrices.json', {'label_order': bundle['label_order'], 'models': confusions})
    write_json(OUT / 'evaluation.json', {
        'status': 'EXECUTED', 'protocol_sha256': digest(PROTOCOL), 'model_sha256': digest(model_path),
        'manifest_sha256': digest(OUT / 'split-manifest.csv'), 'prediction_sha256': digest(OUT / 'test-predictions.csv'),
        'test_n': len(test), 'duplicate_groups': len(group_ids), 'events': sorted({r['event_name'] for r in test}),
        'configurations': len(metrics), 'prediction_rows': len(predictions), 'failures': 0,
        'limitations': ['English public agreed-label subset', 'single event split and seed', 'capped training pilot',
                        'agreement filtering selects easier aligned evidence', 'CIs unadjusted and conditional, not event-population CIs',
                        'no Vietnamese/urgency/dispatch/mobile/field claim']})
    for m in metrics:
        print(m, flush=True)


if __name__ == '__main__':
    main()
