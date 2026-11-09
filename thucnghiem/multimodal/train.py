"""Fit identical-budget text/image/fusion classifiers; select using dev only."""
from __future__ import annotations

import importlib.metadata
import math
import platform
import time
import warnings

import joblib
import numpy as np
from scipy import sparse
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score

from common import (BASE, DATA, OUT, PROTOCOL, clean_text, digest, read_json,
                    write_csv, write_json)


def concat_features(text, image):
    return sparse.hstack([text, sparse.csr_matrix(image)], format='csr') / math.sqrt(2)


def validate_dataset(rows, label_order):
    if len({r['image_id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate pair IDs')
    for split in ('train', 'dev', 'test'):
        current = [r for r in rows if r['split'] == split]
        if {r['label'] for r in current} != set(label_order):
            raise ValueError(f'{split} lacks both classes')
        other = [r for r in rows if r['split'] != split]
        for field in ('tweet_id', 'text_normalized', 'image_sha256', 'group_id', 'event_name'):
            if {r[field] for r in current} & {r[field] for r in other}:
                raise ValueError(f'Cross-split leakage: {field}')


def main():
    warnings.simplefilter('error', ConvergenceWarning)
    protocol = read_json(PROTOCOL)
    model_path = BASE / 'models/classifiers.joblib'
    if model_path.exists():
        raise SystemExit('Refusing to overwrite fitted models')
    if digest(PROTOCOL) != read_json(OUT / 'selection-lock.json')['protocol_sha256']:
        raise ValueError('Protocol changed')
    if digest(DATA / 'dataset.json') != read_json(OUT / 'data-audit.json')['dataset_sha256']:
        raise ValueError('Dataset changed')
    rows = read_json(DATA / 'dataset.json')
    validate_dataset(rows, protocol['label_order'])
    cache_path = BASE / 'features/embeddings.npz'
    if digest(cache_path) != read_json(OUT / 'features.json')['cache_sha256']:
        raise ValueError('Feature cache changed')
    cache = np.load(cache_path)
    if list(cache['image_ids']) != [r['image_id'] for r in rows]:
        raise ValueError('Feature/sample alignment mismatch')
    image = cache['embeddings']
    train_idx = np.array([i for i, r in enumerate(rows) if r['split'] == 'train'])
    dev_idx = np.array([i for i, r in enumerate(rows) if r['split'] == 'dev'])
    # Transform test later in evaluate.py; test never participates in vocabulary or selection.
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=20000,
                                sublinear_tf=True, dtype=np.float64)
    train_text = vectorizer.fit_transform([clean_text(rows[i]['tweet_text']) for i in train_idx])
    dev_text = vectorizer.transform([clean_text(rows[i]['tweet_text']) for i in dev_idx])
    label = {x: i for i, x in enumerate(protocol['label_order'])}
    y_train = np.array([label[rows[i]['label']] for i in train_idx])
    y_dev = np.array([label[rows[i]['label']] for i in dev_idx])
    x = {
        'text_tfidf_lr': (train_text, dev_text),
        'image_frozen_lr': (image[train_idx], image[dev_idx]),
        'feature_concat_lr': (concat_features(train_text, image[train_idx]), concat_features(dev_text, image[dev_idx]))}
    models, selection = {}, []
    for name, (xt, xv) in x.items():
        best = -1.
        for c in protocol['classifier']['C_grid']:
            started = time.time()
            model = LogisticRegression(C=c, solver='liblinear', class_weight='balanced',
                                       max_iter=2000, random_state=protocol['classifier']['seed'])
            model.fit(xt, y_train)
            f1 = f1_score(y_dev, model.predict(xv), average='macro', labels=[0, 1], zero_division=0)
            selection.append({'model': name, 'C': c, 'validation_macro_f1': f1,
                              'fit_and_dev_seconds': time.time() - started,
                              'iterations': int(model.n_iter_.max())})
            if f1 > best:
                best, models[name] = f1, model
            print(name, 'C=', c, 'dev macro-F1=', f1, flush=True)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'vectorizer': vectorizer, 'models': models, 'label_order': protocol['label_order'],
                 'majority_label': int(np.bincount(y_train).argmax()),
                 'protocol_sha256': digest(PROTOCOL), 'dataset_sha256': digest(DATA / 'dataset.json')},
                model_path, compress=3)
    write_csv(OUT / 'model-selection.csv', selection)
    write_json(OUT / 'training.json', {
        'status': 'COMPLETED_AND_SELECTED_BEFORE_TEST_PREDICTIONS',
        'model_sha256': digest(model_path), 'protocol_sha256': digest(PROTOCOL),
        'dataset_sha256': digest(DATA / 'dataset.json'), 'feature_sha256': digest(cache_path),
        'selected_C': {name: model.C for name, model in models.items()},
        'train_n': len(train_idx), 'dev_n': len(dev_idx), 'text_dimensions': len(vectorizer.vocabulary_),
        'image_dimensions': 576, 'encoder_frozen': True, 'training_seed': protocol['classifier']['seed'],
        'python': platform.python_version(),
        'packages': {name: importlib.metadata.version(name) for name in
                     ['numpy', 'scipy', 'scikit-learn', 'torch', 'torchvision', 'Pillow', 'joblib']},
        'limits': 'Linear additive feature fusion; no learned cross-modal interactions or jointly fine-tuned encoders; English informativeness only'})


if __name__ == '__main__':
    main()
