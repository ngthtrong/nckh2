"""Local research-only predictions from translated-text AI-silver classifiers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import torch
from PIL import Image, ImageOps

from common import BASE, LABELS, OUT, PROTOCOL, TASK, clean_text, digest, read_json, write_json
from train import concat


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--text', default='')
    parser.add_argument('--image', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    text = clean_text(args.text)
    if not text and args.image is None:
        parser.error('At least one valid text or image input is required')
    info = read_json(OUT / 'features.json')
    training = read_json(OUT / 'training.json')
    if (training['protocol_sha256'] != digest(PROTOCOL)
            or info['protocol_sha256'] != digest(PROTOCOL)):
        raise ValueError('Protocol binding mismatch')
    model_path = BASE / 'models/classifiers.joblib'
    if digest(model_path) != training['model_sha256']:
        raise ValueError('Locally trained classifier artifact changed')
    bundle = joblib.load(model_path)
    if bundle['task'] != TASK or bundle['label_order'] != LABELS:
        raise ValueError('Wrong task or labels')
    for key in ['dataset_sha256', 'protocol_sha256', 'cache_sha256']:
        if bundle[key] != training[key] or bundle[key] != info[key]:
            raise ValueError('Inference artifact binding mismatch: ' + key)
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    text_feature = image_feature = None
    if text:
        from transformers import AutoModel, AutoTokenizer
        directory = (BASE / 'cache/huggingface' /
                     ('models--' + info['text_encoder'].replace('/', '--')) /
                     'snapshots' / info['text_revision'])
        for filename, expected in info['text_files_sha256'].items():
            if digest(directory / filename) != expected:
                raise ValueError('Text encoder/tokenizer changed')
        tokenizer = AutoTokenizer.from_pretrained(directory, local_files_only=True)
        encoder = AutoModel.from_pretrained(directory, local_files_only=True,
                                             use_safetensors=True).eval()
        tokens = tokenizer([text], truncation=True, max_length=128, return_tensors='pt')
        with torch.inference_mode():
            hidden = encoder(**tokens).last_hidden_state
            mask = tokens['attention_mask'].unsqueeze(-1)
            pooled = (hidden * mask).sum(1) / mask.sum(1).clamp_min(1)
            text_feature = torch.nn.functional.normalize(pooled, p=2, dim=1).numpy()
        del encoder
    if args.image is not None:
        from torchvision.models import MobileNet_V3_Large_Weights, mobilenet_v3_large
        weights = MobileNet_V3_Large_Weights.IMAGENET1K_V2
        weight_file = BASE / 'cache/torch/checkpoints' / Path(weights.url).name
        if digest(weight_file) != info['image_weights_sha256']:
            raise ValueError('Image encoder changed')
        encoder = mobilenet_v3_large(weights=None).eval()
        encoder.load_state_dict(torch.load(weight_file, map_location='cpu', weights_only=True))
        encoder.classifier = torch.nn.Identity()
        with Image.open(args.image) as image:
            tensor = weights.transforms()(ImageOps.exif_transpose(image).convert('RGB')).unsqueeze(0)
        with torch.inference_mode():
            image_feature = torch.nn.functional.normalize(encoder(tensor), p=2, dim=1).numpy()
    if text_feature is not None and image_feature is not None:
        name, features = 'F1', concat(text_feature, image_feature)
    elif text_feature is not None:
        name, features = 'T1', text_feature
    else:
        name, features = 'I0', image_feature
    classifier = bundle['models'][name]
    if list(classifier.classes_) != [0, 1]:
        raise ValueError('Wrong class order')
    probability = float(classifier.predict_proba(features)[0, 1])
    if not np.isfinite(probability) or not 0 <= probability <= 1:
        raise ValueError('Invalid probability')
    result = {'task': TASK, 'model': name, 'label': LABELS[int(probability >= .5)],
              'probability_request': probability, 'scope': 'LOCAL_AI_SILVER_RESEARCH_ONLY',
              'label_origin': 'AI source-text annotations, not human/expert gold',
              'limits': 'Uncalibrated pilot output, no urgency/dispatch or native-Vietnamese validation'}
    if args.output:
        write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
