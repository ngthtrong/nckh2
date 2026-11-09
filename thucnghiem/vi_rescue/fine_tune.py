"""Fine-tune multilingual DistilBERT on the locked translated-text AI-silver pilot.

Six train/dev candidates are selected and hash-bound before test predictions.
The encoder is fully trainable; labels remain single-pass AI silver, not gold.
Only the already downloaded, hash-checked local encoder snapshot is loaded.
"""
from __future__ import annotations

import gc
import math
import random
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from torch import nn
from transformers import AutoModel, AutoTokenizer

from common import BASE, LABELS, OUT, PROTOCOL, ROOT, TASK, clean_text, digest, load_data, read_json, write_csv, write_json


T2_PROTOCOL = OUT / 't2-protocol.json'


class MeanPoolClassifier(nn.Module):
    def __init__(self, snapshot: Path, dropout: float):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(
            str(snapshot), local_files_only=True, use_safetensors=True)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(self.encoder.config.hidden_size, len(LABELS))
        for parameter in self.encoder.parameters():
            parameter.requires_grad_(True)

    def forward(self, **tokens):
        hidden = self.encoder(**tokens).last_hidden_state
        mask = tokens['attention_mask'].unsqueeze(-1).to(hidden.dtype)
        pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1)
        return self.classifier(self.dropout(pooled))


def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def tokenize(tokenizer, rows, max_length):
    texts = [clean_text(row['text_vi']) for row in rows]
    if not texts or any(not text for text in texts):
        raise ValueError('Empty split or cleaned text')
    return tokenizer(texts, padding=True, truncation=True,
                     max_length=max_length, return_tensors='pt')


def probabilities(model, encoded, batch_size):
    model.eval()
    values = []
    n = len(encoded['input_ids'])
    with torch.inference_mode():
        for start in range(0, n, batch_size):
            batch = {key: value[start:start + batch_size] for key, value in encoded.items()}
            values.append(torch.softmax(model(**batch), dim=-1)[:, 1].numpy())
    result = np.concatenate(values).astype(np.float64)
    if not np.isfinite(result).all() or np.any((result < 0) | (result > 1)):
        raise ValueError('Nonfinite or out-of-range T2 probability')
    return result


def seed_metrics(seed, labels, probability, threshold):
    prediction = (probability >= threshold).astype(np.int64)
    tn, fp, fn, tp = confusion_matrix(labels, prediction, labels=[0, 1]).ravel()
    return {'seed': seed, 'n': len(labels),
            'accuracy': float(accuracy_score(labels, prediction)),
            'macro_f1': float(f1_score(labels, prediction, labels=[0, 1],
                                       average='macro', zero_division=0)),
            'precision_request': float(precision_score(labels, prediction, zero_division=0)),
            'recall_request': float(recall_score(labels, prediction, zero_division=0)),
            'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp)}


def validate_local_snapshot(feature_info):
    repo = feature_info['text_encoder']
    revision = feature_info['text_revision']
    snapshot = (BASE / 'cache/huggingface' /
                ('models--' + repo.replace('/', '--')) / 'snapshots' / revision)
    if not snapshot.is_dir():
        raise ValueError('Recorded local encoder snapshot is unavailable: ' + str(snapshot))
    for filename, expected in feature_info['text_files_sha256'].items():
        path = snapshot / filename
        if not path.is_file() or digest(path) != expected:
            raise ValueError('Encoder/tokenizer file hash mismatch: ' + filename)
    if digest(snapshot / 'model.safetensors') != feature_info['text_weights_sha256']:
        raise ValueError('Pretrained text weights hash mismatch')
    return snapshot


def main():
    output_names = ['t2-history.csv', 't2-model-selection.csv', 't2-training.json',
                    't2-predictions.csv', 't2-metrics.csv', 't2-evaluation.json']
    model_root = BASE / 'models/t2'
    if model_root.exists() or any((OUT / name).exists() for name in output_names):
        raise SystemExit('Refusing to overwrite T2 model directories or receipts')
    rows = load_data()
    protocol = read_json(T2_PROTOCOL)
    base_protocol = read_json(PROTOCOL)
    dataset_hash = digest(BASE / 'data/dataset.json')
    base_protocol_hash = digest(PROTOCOL)
    t2_protocol_hash = digest(T2_PROTOCOL)
    feature_info = read_json(OUT / 'features.json')
    if protocol.get('status') != 'LOCKED_BEFORE_ANY_TEST_PREDICTIONS':
        raise ValueError('T2 protocol was not locked before test')
    if protocol.get('dataset_sha256') != dataset_hash:
        raise ValueError('T2 dataset binding mismatch')
    if protocol.get('base_protocol_sha256') != base_protocol_hash:
        raise ValueError('T2 base-protocol binding mismatch')
    if (feature_info.get('dataset_sha256') != dataset_hash or
            feature_info.get('protocol_sha256') != base_protocol_hash):
        raise ValueError('Recorded encoder feature receipt belongs to another study')
    rates = sorted(float(value) for value in protocol['learning_rates'])
    seeds = [int(value) for value in protocol['seeds']]
    physical = int(protocol['physical_batch_size'])
    effective = int(protocol['effective_batch_size'])
    max_epochs = int(protocol['max_epochs'])
    patience = int(protocol['early_stopping_patience'])
    if (len(rates) != 2 or len(set(rates)) != 2 or any(rate <= 0 for rate in rates)
            or len(seeds) != 3 or len(set(seeds)) != 3
            or physical < 1 or effective < physical or effective % physical
            or not 1 <= max_epochs <= 5 or patience < 1):
        raise ValueError('Unexpected T2 candidate grid or batch/epoch budget')
    torch.set_num_threads(int(protocol['cpu_threads']))
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    snapshot = validate_local_snapshot(feature_info)
    tokenizer = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True)
    split_rows = {name: [row for row in rows if row['split'] == name]
                  for name in ['train', 'dev']}
    encoded = {name: tokenize(tokenizer, split_rows[name], int(protocol['max_length']))
               for name in ['train', 'dev']}
    labels = {name: np.array([LABELS.index(row['label']) for row in split_rows[name]],
                            dtype=np.int64) for name in ['train', 'dev']}
    train_labels = torch.tensor(labels['train'], dtype=torch.long)
    counts = np.bincount(labels['train'], minlength=len(LABELS))
    if np.any(counts == 0):
        raise ValueError('Training set lacks one class')
    class_weights = torch.tensor(len(train_labels) / (len(LABELS) * counts), dtype=torch.float32)
    # Sum losses per microbatch, then divide by the effective-batch weight sum.
    # This preserves weighted-CE semantics under gradient accumulation, including
    # the final short batch, instead of averaging differently weighted chunks.
    criterion = nn.CrossEntropyLoss(weight=class_weights, reduction='sum')
    threshold = float(base_protocol['classifier']['threshold'])
    bindings = {'dataset_sha256': dataset_hash, 'protocol_sha256': base_protocol_hash,
                't2_protocol_sha256': t2_protocol_hash}
    model_root.mkdir(parents=True, exist_ok=False)
    history, candidates = [], []
    start_all = time.monotonic()
    for rate in rates:
        for seed in seeds:
            seed_everything(seed)
            run_dir = model_root / f'lr-{rate:.0e}-seed-{seed}'
            run_dir.mkdir(exist_ok=False)
            model = MeanPoolClassifier(snapshot, float(protocol['dropout']))
            trainable = sum(parameter.numel() for parameter in model.parameters()
                            if parameter.requires_grad)
            optimizer = torch.optim.AdamW(model.parameters(), lr=rate,
                                           weight_decay=float(protocol['weight_decay']))
            generator = torch.Generator().manual_seed(seed)
            best_score, best_epoch, best_checkpoint = -1.0, None, None
            bad_epochs = 0
            run_start = time.monotonic()
            for epoch in range(1, max_epochs + 1):
                model.train()
                order = torch.randperm(len(train_labels), generator=generator)
                total_loss, total_weight = 0.0, 0.0
                epoch_start = time.monotonic()
                for start in range(0, len(order), effective):
                    indices = order[start:start + effective]
                    denominator = class_weights[train_labels[indices]].sum()
                    optimizer.zero_grad(set_to_none=True)
                    for micro_start in range(0, len(indices), physical):
                        micro = indices[micro_start:micro_start + physical]
                        batch = {key: value[micro] for key, value in encoded['train'].items()}
                        loss_sum = criterion(model(**batch), train_labels[micro])
                        if not torch.isfinite(loss_sum):
                            raise ValueError('Nonfinite T2 training loss')
                        (loss_sum / denominator).backward()
                        total_loss += float(loss_sum.detach())
                    total_weight += float(denominator)
                    optimizer.step()
                dev_probability = probabilities(model, encoded['dev'], physical)
                dev_prediction = (dev_probability >= threshold).astype(np.int64)
                score = float(f1_score(labels['dev'], dev_prediction, labels=[0, 1],
                                       average='macro', zero_division=0))
                row = {'learning_rate': rate, 'seed': seed, 'epoch': epoch,
                       'train_weighted_ce': total_loss / total_weight,
                       'validation_macro_f1': score,
                       'epoch_seconds': time.monotonic() - epoch_start,
                       'run_elapsed_seconds': time.monotonic() - run_start}
                history.append(row)
                print(f'T2 lr={rate:g} seed={seed} epoch={epoch} '
                      f'loss={row["train_weighted_ce"]:.6f} dev_f1={score:.6f} '
                      f'elapsed={row["run_elapsed_seconds"]:.1f}s', flush=True)
                if score > best_score:
                    best_score, best_epoch, bad_epochs = score, epoch, 0
                    best_checkpoint = run_dir / f'best-epoch-{epoch}.pt'
                    with best_checkpoint.open('xb') as stream:
                        torch.save({'model_state': model.state_dict(), 'bindings': bindings,
                                    'learning_rate': rate, 'seed': seed, 'epoch': epoch,
                                    'dev_macro_f1': score, 'task': TASK,
                                    'text_revision': feature_info['text_revision'],
                                    'head_dropout': float(protocol['dropout']),
                                    'label_order': LABELS}, stream)
                else:
                    bad_epochs += 1
                if bad_epochs >= patience:
                    break
            if best_checkpoint is None:
                raise ValueError('No T2 development checkpoint was selected')
            candidates.append({'learning_rate': rate, 'seed': seed,
                'best_epoch': best_epoch, 'dev_macro_f1': best_score,
                'epochs_run': epoch, 'trainable_parameters': trainable,
                'checkpoint': str(best_checkpoint.relative_to(ROOT)),
                'checkpoint_sha256': digest(best_checkpoint),
                'elapsed_seconds': time.monotonic() - run_start})
            del optimizer, model
            gc.collect()
    mean_dev = {rate: float(np.mean([candidate['dev_macro_f1'] for candidate in candidates
                                    if candidate['learning_rate'] == rate])) for rate in rates}
    # Ascending rates + stable max gives the lower LR on an exact dev tie.
    selected_rate = max(rates, key=lambda rate: mean_dev[rate])
    selected = [candidate for candidate in candidates if candidate['learning_rate'] == selected_rate]
    if len(selected) != len(seeds):
        raise ValueError('Selected learning rate did not retain all seed models')
    write_csv(OUT / 't2-history.csv', history)
    write_csv(OUT / 't2-model-selection.csv', candidates)
    # This immutable receipt is closed before test text is tokenized or scored.
    write_json(OUT / 't2-training.json', {
        'status': 'SIX_CANDIDATES_SELECTED_BEFORE_TEST_PREDICTIONS',
        'task': TASK, 'label_origin': 'AI_SILVER_TEXT_ONLY', **bindings,
        'features_receipt_sha256': digest(OUT / 'features.json'),
        'text_encoder': feature_info['text_encoder'], 'text_revision': feature_info['text_revision'],
        'text_weights_sha256': feature_info['text_weights_sha256'],
        'text_files_sha256': feature_info['text_files_sha256'],
        'history_sha256': digest(OUT / 't2-history.csv'),
        'model_selection_sha256': digest(OUT / 't2-model-selection.csv'),
        'candidate_models': candidates, 'selected_models': selected,
        'selected_learning_rate': selected_rate,
        'learning_rate_mean_dev_macro_f1': {str(rate): score for rate, score in mean_dev.items()},
        'class_weights_from_train': class_weights.tolist(), 'class_order': LABELS,
        'train_n': len(split_rows['train']), 'dev_n': len(split_rows['dev']),
        'physical_batch_size': physical, 'effective_batch_size': effective,
        'gradient_accumulation': 'weighted summed CE / effective-batch weight sum',
        'max_length': int(protocol['max_length']), 'max_epochs': max_epochs,
        'epochs_run_total': len(history), 'encoder_fine_tuning': True,
        'cpu_threads': int(protocol['cpu_threads']), 'torch': torch.__version__,
        'elapsed_seconds_training': time.monotonic() - start_all,
        'source_sha256': {name: digest(BASE / name) for name in ['fine_tune.py', 'common.py']},
        'limits': 'AI-translated silver labels, one known event holdout; not independent native-Vietnamese or operational validation'})
    print('T2 training and selection frozen before test; LR:', selected_rate, flush=True)
    test = [row for row in rows if row['split'] == 'test']
    test_encoded = tokenize(tokenizer, test, int(protocol['max_length']))
    probability_by_seed = {}
    for candidate in selected:
        path = ROOT / candidate['checkpoint']
        if digest(path) != candidate['checkpoint_sha256']:
            raise ValueError('Selected T2 checkpoint changed after model freeze')
        seed_everything(candidate['seed'])
        model = MeanPoolClassifier(snapshot, float(protocol['dropout']))
        checkpoint = torch.load(path, map_location='cpu', weights_only=True)
        if checkpoint['bindings'] != bindings or checkpoint['label_order'] != LABELS:
            raise ValueError('T2 checkpoint metadata mismatch')
        model.load_state_dict(checkpoint['model_state'], strict=True)
        probability_by_seed[candidate['seed']] = probabilities(model, test_encoded, physical)
        del checkpoint, model
        gc.collect()
    predictions = []
    for seed in seeds:
        for row, probability in zip(test, probability_by_seed[seed]):
            predictions.append({'seed': seed, 'image_id': row['image_id'],
                'group_id': row['group_id'], 'event_name': row['event_name'],
                'probability_request': float(probability),
                'predicted_label': LABELS[int(probability >= threshold)], 'label_ai': row['label']})
    write_csv(OUT / 't2-predictions.csv', predictions)
    prediction_hash = digest(OUT / 't2-predictions.csv')
    test_labels = np.array([LABELS.index(row['label']) for row in test], dtype=np.int64)
    metrics = [seed_metrics(seed, test_labels, probability_by_seed[seed], threshold) for seed in seeds]
    write_csv(OUT / 't2-metrics.csv', metrics)
    summary = {key: {'mean': float(np.mean([row[key] for row in metrics])),
                     'min': min(row[key] for row in metrics), 'max': max(row[key] for row in metrics)}
               for key in ['accuracy', 'macro_f1', 'precision_request', 'recall_request']}
    write_json(OUT / 't2-evaluation.json', {
        'status': 'EXECUTED_AGAINST_AI_SILVER_LABELS', 'task': TASK,
        'label_origin': 'AI_SILVER_TEXT_ONLY', **bindings,
        'training_receipt_sha256': digest(OUT / 't2-training.json'),
        'predictions_sha256': prediction_hash, 'metrics_sha256': digest(OUT / 't2-metrics.csv'),
        'selected_learning_rate': selected_rate, 'seeds': seeds,
        'n_test': len(test), 'prediction_rows': len(predictions), 'threshold': threshold,
        'seed_metrics': metrics, 'summary': summary, 'encoder_fine_tuning': True,
        'elapsed_seconds_total': time.monotonic() - start_all,
        'limits': ['No independent human/expert gold or native-Vietnamese rescue data',
                   'Three seed models evaluated on the same test IDs, not three independent datasets',
                   'No joint image/text encoder fine-tuning, Android or rescue-effectiveness validation']})
    print('T2 test complete:', len(test), 'pairs x', len(seeds), 'selected seed models; '
          'mean macro-F1:', summary['macro_f1']['mean'], flush=True)


if __name__ == '__main__':
    main()
