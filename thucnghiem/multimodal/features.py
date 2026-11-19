"""Frozen ImageNet feature extraction, without training the image encoder."""
from __future__ import annotations

import time

import numpy as np
import torch
from PIL import Image, ImageOps
from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small

from common import BASE, DATA, OUT, PROTOCOL, digest, read_json, write_json


def load_encoder():
    torch.hub.set_dir(str(BASE / 'cache/torch'))
    weights = MobileNet_V3_Small_Weights.IMAGENET1K_V1
    model = mobilenet_v3_small(weights=weights).eval()
    model.classifier = torch.nn.Identity()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    return model, weights.transforms()


def load_image(path, transform):
    with Image.open(path) as image:
        return transform(ImageOps.exif_transpose(image).convert('RGB'))


def main():
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    target = BASE / 'features/embeddings.npz'
    if target.exists():
        raise SystemExit('Refusing to overwrite existing feature cache')
    if digest(PROTOCOL) != read_json(OUT / 'selection-lock.json')['protocol_sha256']:
        raise ValueError('Protocol changed after selection')
    if digest(DATA / 'dataset.json') != read_json(OUT / 'data-audit.json')['dataset_sha256']:
        raise ValueError('Dataset changed after audit')
    rows = read_json(DATA / 'dataset.json')
    model, transform = load_encoder()
    with torch.inference_mode():
        model(load_image(DATA / rows[0]['image'], transform).unsqueeze(0))
        started = time.time()
        vectors = []
        for start in range(0, len(rows), 32):
            batch = rows[start:start + 32]
            images = torch.stack([load_image(DATA / r['image'], transform) for r in batch])
            result = model(images).numpy()
            if not np.isfinite(result).all() or result.shape != (len(batch), 576):
                raise ValueError('Nonfinite or unexpected embeddings')
            result /= np.maximum(np.linalg.norm(result, axis=1, keepdims=True), 1e-12)
            vectors.append(result)
            if start % 320 == 0:
                print(f'Embedded {start + len(batch)}/{len(rows)}', flush=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(target, image_ids=np.array([r['image_id'] for r in rows]),
                        embeddings=np.concatenate(vectors).astype(np.float32))
    checkpoint = BASE / 'cache/torch/checkpoints/mobilenet_v3_small-047dcff4.pth'
    write_json(OUT / 'features.json', {
        'status': 'COMPLETED', 'n': len(rows), 'dimensions': 576,
        'encoder': 'MobileNet_V3_Small_Weights.IMAGENET1K_V1', 'encoder_frozen': True,
        'checkpoint_sha256': digest(checkpoint), 'cache_sha256': digest(target),
        'dataset_sha256': digest(DATA / 'dataset.json'), 'protocol_sha256': digest(PROTOCOL),
        'cpu_threads': 4, 'seconds_decode_preprocess_forward': time.time() - started,
        'timing_scope': 'one CPU feature extraction session, excludes load/warmup; not Android latency',
        'torch': torch.__version__, 'transform': str(transform), 'failures': 0})
    print('Feature cache complete', flush=True)


if __name__ == '__main__':
    main()
