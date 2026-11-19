"""Select classifier heads on development data; never select on test metrics."""
from __future__ import annotations

import math
import time
import warnings

import joblib
import numpy as np
from scipy import sparse
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score

from common import BASE, LABELS, OUT, PROTOCOL, clean_text, digest, load_data, read_json, write_csv, write_json


def concat(a, b):
    return sparse.hstack([sparse.csr_matrix(a), sparse.csr_matrix(b)], format='csr') / math.sqrt(2)


def main():
    target = BASE / 'models/classifiers.joblib'
    if target.exists():
        raise SystemExit('Refusing to overwrite models')
    warnings.simplefilter('error', ConvergenceWarning)
    rows = load_data()
    feature_info = read_json(OUT / 'features.json')
    if (feature_info['dataset_sha256'] != digest(BASE / 'data/dataset.json')
            or feature_info['protocol_sha256'] != digest(PROTOCOL)):
        raise ValueError('Features bound to a different dataset/protocol')
    if digest(BASE / 'cache/embeddings.npz') != feature_info['cache_sha256']:
        raise ValueError('Feature cache changed')
    cache = np.load(BASE / 'cache/embeddings.npz', allow_pickle=False)
    if list(cache['image_ids']) != [r['image_id'] for r in rows]:
        raise ValueError('Feature alignment mismatch')
    indices = {s: np.array([i for i, r in enumerate(rows) if r['split'] == s]) for s in ['train', 'dev']}
    yi = {s: np.array([LABELS.index(rows[i]['label']) for i in idx]) for s, idx in indices.items()}
    texts = {s: [clean_text(rows[i]['text_vi']) for i in idx] for s, idx in indices.items()}
    grid = read_json(PROTOCOL)['classifier']['C_grid']
    models, selection = {}, []

    def fit_candidates(name, xt, xv):
        best = -1
        selected = None
        for c in grid:
            started = time.monotonic()
            classifier = LogisticRegression(C=c, solver='liblinear', class_weight='balanced',
                max_iter=2000, random_state=20261108)
            classifier.fit(xt, yi['train'])
            score = f1_score(yi['dev'], classifier.predict(xv), labels=[0, 1],
                             average='macro', zero_division=0)
            selection.append({'model': name, 'C': c, 'validation_macro_f1': score,
                              'seconds': time.monotonic() - started})
            if score > best:
                best, selected = score, classifier
        return selected, best

    vectorizers = {}
    for variant, kwargs in [('word', {'analyzer': 'word', 'ngram_range': (1, 2)}),
                            ('char', {'analyzer': 'char', 'ngram_range': (3, 5)})]:
        vectorizer = TfidfVectorizer(max_features=20000, min_df=2, sublinear_tf=True, **kwargs)
        xt = vectorizer.fit_transform(texts['train'])
        xv = vectorizer.transform(texts['dev'])
        classifier, score = fit_candidates('T0_' + variant, xt, xv)
        vectorizers[variant] = (vectorizer, classifier, score)
    variant = max(['word', 'char'], key=lambda name: vectorizers[name][2])
    vectorizer, models['T0'], _ = vectorizers[variant]
    tf = {s: vectorizer.transform(texts[s]) for s in ['train', 'dev']}
    tx = {s: cache['text'][idx] for s, idx in indices.items()}
    im = {s: cache['image'][idx] for s, idx in indices.items()}
    matrices = {'T1': (tx['train'], tx['dev']), 'I0': (im['train'], im['dev']),
                'F0': (concat(tf['train'], im['train']), concat(tf['dev'], im['dev'])),
                'F1': (concat(tx['train'], im['train']), concat(tx['dev'], im['dev']))}
    dev_scores = {}
    for name, (xt, xv) in matrices.items():
        models[name], dev_scores[name] = fit_candidates(name, xt, xv)
    comparator = 'T1' if dev_scores['T1'] >= dev_scores['I0'] else 'I0'
    majority = int(np.bincount(yi['train']).argmax())
    bundle = {'task': 'vi_translated_silver_request_v1', 'models': models,
              'vectorizer': vectorizer, 'majority': majority, 'label_order': LABELS,
              'protocol_sha256': digest(PROTOCOL), 'dataset_sha256': digest(BASE / 'data/dataset.json'),
              'cache_sha256': feature_info['cache_sha256']}
    joblib.dump(bundle, target, compress=3)
    write_csv(OUT / 'model-selection.csv', selection)
    write_json(OUT / 'training.json', {'status': 'LINEAR_HEADS_TRAINED_ON_AI_SILVER_LABELS',
        'model_sha256': digest(target), 'dataset_sha256': bundle['dataset_sha256'],
        'protocol_sha256': bundle['protocol_sha256'], 'cache_sha256': bundle['cache_sha256'],
        'text_variant': variant, 'tfidf_dimensions': len(vectorizer.vocabulary_),
        'selected_C': {name: model.C for name, model in models.items()},
        'primary_comparator_selected_on_dev': comparator, 'fit_count': len(selection),
        'train_n': len(indices['train']), 'dev_n': len(indices['dev']),
        'encoder_fine_tuning': False, 'T2': 'NOT_RUN: not part of translated silver pilot',
        'limits': 'No independent human labels, native Vietnamese evaluation or operational acceptance'})
    print('Heads frozen; primary comparator:', comparator, 'fits:', len(selection), flush=True)


if __name__ == '__main__':
    main()
