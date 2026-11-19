"""Check local inference reload for each input route against held-out artifacts."""
from pathlib import Path

import numpy as np

from common import DATA, OUT, read_csv, read_json, write_json
from predict import predict


def main():
    row = next(r for r in read_json(DATA / 'dataset.json') if r['split'] == 'test')
    stored = {r['model']: r for r in read_csv(OUT / 'test-predictions.csv') if r['image_id'] == row['image_id']}
    checks, outputs = {}, {}
    for name, text, image in [('text_tfidf_lr', row['tweet_text'], None),
                              ('image_frozen_lr', None, DATA / row['image']),
                              ('feature_concat_lr', row['tweet_text'], DATA / row['image'])]:
        output = predict(text, image)
        outputs[name] = output
        checks[name] = bool(np.isclose(output['probabilities']['informative'],
                           float(stored[name]['prob_informative']), atol=1e-5, rtol=0))
        assert output['task'] == 'public_crisis_informativeness'
        assert not ({'E', 'E_i', 'urgency', 'priority', 'rank'} & output.keys())
        assert output['prediction'] == stored[name]['prediction']
    status = 'PASS' if all(checks.values()) else 'FAIL'
    write_json(OUT / 'inference-smoke.json', {'status': status, 'pair_id': row['image_id'],
               'checks': checks, 'outputs': outputs, 'scope': 'one held-out fixture per route; no operational or device validation'})
    print(status, checks)
    if status != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
