"""Frozen DistilBERT and MobileNetV3-Large embeddings, CPU only."""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import requests
import torch
from PIL import Image, ImageOps
from huggingface_hub import snapshot_download
from transformers import AutoModel, AutoTokenizer
from torchvision.models import MobileNet_V3_Large_Weights, mobilenet_v3_large

from common import BASE, OUT, PROTOCOL, ROOT, clean_text, digest, load_data, read_json, write_json


def main():
    target = BASE / 'cache/embeddings.npz'
    if target.exists():
        raise SystemExit('Refusing to overwrite feature cache')
    rows = load_data()
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    protocol = read_json(PROTOCOL)
    repo = protocol['distilbert']['repo']
    response = requests.get('https://huggingface.co/api/models/' + repo, timeout=60)
    response.raise_for_status()
    revision = response.json()['sha']
    directory = snapshot_download(repo, revision=revision, cache_dir=BASE / 'cache/huggingface',
        allow_patterns=['config.json', 'tokenizer.json', 'tokenizer_config.json',
                        'vocab.txt', 'special_tokens_map.json', 'model.safetensors'])
    tokenizer = AutoTokenizer.from_pretrained(directory, local_files_only=True)
    model = AutoModel.from_pretrained(directory, local_files_only=True, use_safetensors=True).eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    text_vectors = []
    truncations = []
    started = time.monotonic()
    with torch.inference_mode():
        for start in range(0, len(rows), 8):
            texts = [clean_text(r['text_vi']) for r in rows[start:start + 8]]
            for text in texts:
                truncations.append(len(tokenizer(text, truncation=False)['input_ids']) > 128)
            tokens = tokenizer(texts, padding=True, truncation=True, max_length=128, return_tensors='pt')
            hidden = model(**tokens).last_hidden_state
            mask = tokens['attention_mask'].unsqueeze(-1)
            vector = (hidden * mask).sum(1) / mask.sum(1).clamp_min(1)
            vector = torch.nn.functional.normalize(vector, p=2, dim=1)
            text_vectors.append(vector.numpy())
            print(f'DistilBERT {start + len(texts)}/{len(rows)}', flush=True)
    text_seconds = time.monotonic() - started
    checkpoint = Path(directory) / 'model.safetensors'
    text_hash = digest(checkpoint)
    del model
    torch.hub.set_dir(str(BASE / 'cache/torch'))
    weights = MobileNet_V3_Large_Weights.IMAGENET1K_V2
    encoder = mobilenet_v3_large(weights=weights).eval()
    encoder.classifier = torch.nn.Identity()
    for parameter in encoder.parameters():
        parameter.requires_grad_(False)
    transform = weights.transforms()
    image_vectors = []
    started = time.monotonic()
    with torch.inference_mode():
        for start in range(0, len(rows), 16):
            chunk = rows[start:start + 16]
            tensors = []
            for r in chunk:
                if digest(ROOT / r['image_path']) != r['image_sha256']:
                    raise ValueError('Image changed before extraction: ' + r['image_id'])
                with Image.open(ROOT / r['image_path']) as im:
                    tensors.append(transform(ImageOps.exif_transpose(im).convert('RGB')))
            vector = encoder(torch.stack(tensors))
            image_vectors.append(torch.nn.functional.normalize(vector, p=2, dim=1).numpy())
            print(f'MobileNetV3-Large {start + len(chunk)}/{len(rows)}', flush=True)
    text = np.concatenate(text_vectors).astype(np.float32)
    image = np.concatenate(image_vectors).astype(np.float32)
    if text.shape != (len(rows), 768) or image.shape != (len(rows), 960):
        raise ValueError('Unexpected feature dimensions')
    if not np.isfinite(text).all() or not np.isfinite(image).all():
        raise ValueError('Nonfinite features')
    np.savez_compressed(target, image_ids=np.array([r['image_id'] for r in rows]), text=text, image=image)
    torch_file = BASE / 'cache/torch/checkpoints' / Path(weights.url).name
    write_json(OUT / 'features.json', {'status': 'FROZEN_ENCODERS_EXECUTED_CPU',
        'dataset_sha256': digest(BASE / 'data/dataset.json'), 'protocol_sha256': digest(PROTOCOL),
        'cache_sha256': digest(target), 'n': len(rows), 'text_dim': 768, 'image_dim': 960,
        'text_encoder': repo, 'text_revision': revision, 'text_weights_sha256': text_hash,
        'text_files_sha256': {p.name: digest(p) for p in Path(directory).iterdir() if p.is_file()},
        'image_encoder': str(weights), 'image_weights_sha256': digest(torch_file),
        'image_transform': str(transform), 'max_text_length': 128,
        'text_truncations': sum(truncations), 'text_seconds': text_seconds,
        'image_seconds': time.monotonic() - started, 'torch': torch.__version__, 'cpu_threads': 4,
        'fine_tuning': False, 'failures': 0,
        'limits': 'Frozen feature extraction and learned linear heads, no encoder fine-tuning or Android measurement'})


if __name__ == '__main__':
    main()
