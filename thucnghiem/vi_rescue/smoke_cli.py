"""Technical CLI reload/preprocessing parity on one development pair, not a benchmark."""
from __future__ import annotations

import json
import subprocess
import sys

import joblib
import numpy as np

from common import BASE, OUT, ROOT, digest, load_data, read_json, write_json
from train import concat


def main():
    rows = load_data()
    index = next(i for i, row in enumerate(rows) if row['split'] == 'dev')
    row = rows[index]
    directory = OUT / 'cli-smoke'
    directory.mkdir(exist_ok=False)
    training = read_json(OUT / 'training.json')
    assert digest(BASE / 'models/classifiers.joblib') == training['model_sha256']
    bundle = joblib.load(BASE / 'models/classifiers.joblib')
    with np.load(BASE / 'cache/embeddings.npz', allow_pickle=False) as cache:
        text, image = cache['text'][index:index + 1], cache['image'][index:index + 1]
    matrices = {'T1': text, 'I0': image, 'F1': concat(text, image)}
    checks = {}
    for name, flags in [('T1', ['--text', row['text_vi']]),
                        ('I0', ['--image', str(ROOT / row['image_path'])]),
                        ('F1', ['--text', row['text_vi'], '--image', str(ROOT / row['image_path'])])]:
        path = directory / (name + '.json')
        cmd = [sys.executable, str(BASE / 'predict.py'), *flags, '--output', str(path)]
        subprocess.run(cmd, check=True, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        value = read_json(path)
        expected = float(bundle['models'][name].predict_proba(matrices[name])[0, 1])
        assert value['model'] == name and abs(value['probability_request'] - expected) < 1e-5
        assert value['scope'] == 'LOCAL_AI_SILVER_RESEARCH_ONLY'
        assert not set(value).intersection(['urgency', 'E_i', 'priority', 'rank'])
        checks[name] = {'reload_probability_matches_cached_features': True,
                       'absolute_difference': abs(value['probability_request'] - expected)}
    write_json(OUT / 'cli-smoke.json', {'status': 'TECHNICAL_SMOKE_ONLY', 'development_id': row['image_id'],
               'checks': checks, 'limits': 'One dev example, no performance/field/fallback validation'})
    print('Three CLI modalities pass reload/preprocessing parity; technical smoke only', flush=True)


if __name__ == '__main__':
    main()
