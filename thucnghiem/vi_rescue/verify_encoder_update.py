"""Check actual selected checkpoints contain encoder updates, not only a fitted head."""
from __future__ import annotations

import gc

import torch
from safetensors import safe_open

from common import BASE, OUT, ROOT, digest, read_json, write_json


def main():
    features = read_json(OUT / 'features.json')
    training = read_json(OUT / 't2-training.json')
    snapshot = (BASE / 'cache/huggingface' /
                ('models--' + features['text_encoder'].replace('/', '--')) /
                'snapshots' / features['text_revision'] / 'model.safetensors')
    if digest(snapshot) != features['text_weights_sha256']:
        raise ValueError('Pretrained weight hash changed')
    suffix = 'transformer.layer.0.attention.q_lin.weight'
    with safe_open(snapshot, framework='pt', device='cpu') as weights:
        key = next(key for key in weights.keys() if key.endswith(suffix))
        reference = weights.get_tensor(key).clone()
    checks = []
    for row in training['selected_models']:
        path = ROOT / row['checkpoint']
        if digest(path) != row['checkpoint_sha256']:
            raise ValueError('Selected checkpoint hash changed')
        checkpoint = torch.load(path, map_location='cpu', weights_only=True)
        actual = checkpoint['model_state']['encoder.' + suffix]
        difference = float((actual - reference).abs().max())
        if not difference > 0:
            raise ValueError('Selected checkpoint contains no update of checked encoder tensor')
        checks.append({'seed': row['seed'], 'encoder_tensor': suffix,
                       'max_abs_change': difference, 'checkpoint_sha256': row['checkpoint_sha256']})
        del checkpoint, actual
        gc.collect()
    write_json(OUT / 'encoder-update-check.json', {'status': 'SELECTED_ENCODER_WEIGHTS_UPDATED',
               'checks': checks, 'limits': 'Verifies a backbone tensor changed in each selected model; not label quality or effectiveness'})
    print('Three selected models contain actual encoder weight updates', flush=True)


if __name__ == '__main__':
    main()
