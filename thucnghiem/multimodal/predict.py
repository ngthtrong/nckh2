"""Local research inference, deliberately isolated from rescue urgency/ranking."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import torch

from common import BASE, OUT, clean_text, digest, read_json
from features import load_encoder, load_image
from train import concat_features


def predict(text: str | None, image_path: Path | None, language: str = 'en') -> dict:
    if language != 'en':
        raise ValueError('This artifact is evaluated on English CrisisMMD only; Vietnamese requires a separate labeled evaluation')
    cleaned = clean_text(text or '')
    if not cleaned and image_path is None:
        raise ValueError('At least one nonempty modality is required')
    model_path = BASE / 'models/classifiers.joblib'
    if digest(model_path) != read_json(OUT / 'training.json')['model_sha256']:
        raise ValueError('Model hash mismatch')
    bundle = joblib.load(model_path)
    text_features = bundle['vectorizer'].transform([cleaned]) if cleaned else None
    image_features = None
    if image_path is not None:
        torch.set_num_threads(4)
        model, transform = load_encoder()
        with torch.inference_mode():
            image_features = model(load_image(image_path, transform).unsqueeze(0)).numpy()
        image_features /= np.maximum(np.linalg.norm(image_features, axis=1, keepdims=True), 1e-12)
    if text_features is not None and image_features is not None:
        name, matrix = 'feature_concat_lr', concat_features(text_features, image_features)
    elif text_features is not None:
        name, matrix = 'text_tfidf_lr', text_features
    else:
        name, matrix = 'image_frozen_lr', image_features
    probabilities = bundle['models'][name].predict_proba(matrix)[0]
    return {
        'task': 'public_crisis_informativeness', 'language_scope': 'en',
        'prediction': bundle['label_order'][int(probabilities[1] >= .5)],
        'probabilities': dict(zip(bundle['label_order'], map(float, probabilities))),
        'model': name, 'model_sha256': digest(model_path),
        'usage': 'LOCAL_RESEARCH_ONLY',
        'urgency_mapping': 'PROHIBITED_DIFFERENT_TARGET',
        'limitations': 'No Vietnamese, rescue priority, field, mobile or probability-calibration validation'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--text')
    parser.add_argument('--image', type=Path)
    parser.add_argument('--language', default='en')
    args = parser.parse_args()
    print(json.dumps(predict(args.text, args.image, args.language), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
