"""Replay bootstrap intervals using only saved predictions, no training code."""
from collections import defaultdict

import numpy as np

from common import OUT, PROTOCOL, digest, read_csv, read_json, write_json


def main():
    rows = read_csv(OUT / 'test-predictions.csv')
    groups = sorted({r['group_id'] for r in rows})
    indices = {g: i for i, g in enumerate(groups)}
    matrices = defaultdict(lambda: np.zeros((len(groups), 2, 2), dtype=np.int64))
    order = read_json(PROTOCOL)['label_order']
    for r in rows:
        matrices[r['model']][indices[r['group_id']], order.index(r['gold']), order.index(r['prediction'])] += 1
    rng = np.random.default_rng(read_json(PROTOCOL)['split']['seed'])
    weights = rng.multinomial(len(groups), np.ones(len(groups)) / len(groups), size=2000)
    boot = {}
    for name, counts in matrices.items():
        cm = weights @ counts.reshape(len(groups), 4)
        tn, fp, fn, tp = cm.T
        boot[name] = .5 * (2 * tn / (2 * tn + fp + fn) + 2 * tp / (2 * tp + fp + fn))
    checks = []
    for effect in read_csv(OUT / 'paired-effects.csv'):
        comparator = effect['contrast'].split(' - ')[1]
        interval = np.quantile(boot['feature_concat_lr'] - boot[comparator], [.025, .975])
        checks.append({'contrast': effect['contrast'], 'matches': bool(np.allclose(interval,
                       [float(effect['ci95_low']), float(effect['ci95_high'])], atol=1e-12, rtol=0))})
    status = 'PASS' if all(c['matches'] for c in checks) else 'FAIL'
    write_json(OUT / 'effects-verification.json', {'status': status, 'checks': checks,
               'prediction_sha256': digest(OUT / 'test-predictions.csv'),
               'effects_sha256': digest(OUT / 'paired-effects.csv'),
               'scope': 'Independent formula replay from persisted predictions with fixed groups/draw seed; not external validation'})
    print(status, checks)
    if status != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
