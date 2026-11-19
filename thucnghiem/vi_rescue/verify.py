"""Independently recompute metrics and paired CIs from frozen silver predictions."""
from __future__ import annotations

import csv
import math

import numpy as np

from common import BASE, LABELS, OUT, PROTOCOL, ROOT, TASK, digest, load_data, read_json, write_json


EXPECTED_MODELS = ['B0', 'T0', 'T1', 'I0', 'F0', 'F1', 'P0', 'F1_mask_image', 'F1_mask_text']
COMPARATORS = ['T1', 'I0', 'P0']


def read_csv(path):
    with path.open(newline='') as handle:
        return list(csv.DictReader(handle))


def ratio(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def independent_metrics(counts):
    tn, fp, fn, tp = (int(value) for value in counts)
    return {'n': tn + fp + fn + tp, 'accuracy': ratio(tn + tp, tn + fp + fn + tp),
        'macro_f1': (ratio(2 * tn, 2 * tn + fn + fp) + ratio(2 * tp, 2 * tp + fp + fn)) / 2,
        'precision_request': ratio(tp, tp + fp), 'recall_request': ratio(tp, tp + fn),
        'tn': tn, 'fp': fp, 'fn': fn, 'tp': tp}


def close(actual, expected, name):
    if not math.isfinite(float(actual)) or abs(float(actual) - float(expected)) > 1e-12:
        raise ValueError(f'Independent recomputation mismatch: {name}: {actual} != {expected}')


def verify_t2(test, dataset_hash, protocol_hash, threshold):
    prediction_path = OUT / 't2-predictions.csv'
    metric_path = OUT / 't2-metrics.csv'
    if not prediction_path.exists() and not metric_path.exists():
        return {'status': 'NOT_RUN', 'limits': 'No T2 predictions or metrics present; frozen pilot remains separate'}
    if not prediction_path.exists() or not metric_path.exists():
        return {'status': 'INCOMPLETE_UNVERIFIED',
                'limits': 'Only part of T2 outputs exists; no T2 verification or completion claim'}
    training_path = OUT / 't2-training.json'
    evaluation_path = OUT / 't2-evaluation.json'
    if not training_path.exists() or not evaluation_path.exists():
        return {'status': 'INCOMPLETE_UNVERIFIED',
                'limits': 'T2 CSVs exist without both final training/evaluation receipts; no T2 completion claim'}
    protocol_path = OUT / 't2-protocol.json'
    t2_protocol = read_json(protocol_path)
    if t2_protocol.get('dataset_sha256') != dataset_hash or t2_protocol.get('base_protocol_sha256') != protocol_hash:
        raise ValueError('T2 protocol is not bound to the same frozen dataset and base protocol')
    if t2_protocol.get('status') != 'LOCKED_BEFORE_ANY_TEST_PREDICTIONS':
        raise ValueError('T2 protocol is not declared locked before test predictions')
    seeds = [int(seed) for seed in t2_protocol['seeds']]
    if len(seeds) != len(set(seeds)) or not seeds:
        raise ValueError('T2 seed list is empty or duplicated')
    predictions = read_csv(prediction_path)
    metrics = read_csv(metric_path)
    tables = {seed: {} for seed in seeds}
    for row in predictions:
        seed, rid = int(row['seed']), row['image_id']
        if seed not in tables or rid not in test or rid in tables[seed]:
            raise ValueError('T2 prediction has unexpected seed/ID or duplicate seed/ID pair')
        if any(row[key] != test[rid][key] for key in ['group_id', 'event_name']):
            raise ValueError('T2 prediction metadata differs from the fixed test record')
        if row['label_ai'] != test[rid]['label']:
            raise ValueError('T2 AI label differs from the locked dataset')
        probability = float(row['probability_request'])
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError('T2 probability is not finite within [0, 1]')
        if row['predicted_label'] != LABELS[int(probability >= threshold)]:
            raise ValueError('T2 prediction does not use the same locked classification threshold')
        tables[seed][rid] = row
    if len(predictions) != len(seeds) * len(test) or any(set(table) != set(test) for table in tables.values()):
        raise ValueError('T2 seeds do not cover exactly the same complete test IDs')
    if len(metrics) != len(seeds) or {int(row['seed']) for row in metrics} != set(seeds):
        raise ValueError('T2 metric seed set is incomplete or duplicated')
    metric_map = {int(row['seed']): row for row in metrics}
    independently_computed = {}
    for seed, table in tables.items():
        counts = [0, 0, 0, 0]
        for row in table.values():
            counts[LABELS.index(row['label_ai']) * 2 + LABELS.index(row['predicted_label'])] += 1
        independently_computed[str(seed)] = independent_metrics(counts)
        for key, expected in independently_computed[str(seed)].items():
            close(metric_map[seed][key], expected, f'T2/seed{seed}/{key}')
    t2_training = read_json(training_path)
    t2_evaluation = read_json(evaluation_path)
    for receipt_name, receipt in [('training', t2_training), ('evaluation', t2_evaluation)]:
        for key, expected in [('dataset_sha256', dataset_hash), ('protocol_sha256', protocol_hash),
                              ('t2_protocol_sha256', digest(protocol_path))]:
            if receipt.get(key) != expected:
                raise ValueError(f'T2 {receipt_name} binding differs: {key}')
    for key, artifact in [('training_receipt_sha256', training_path),
                          ('predictions_sha256', prediction_path), ('metrics_sha256', metric_path)]:
        if t2_evaluation.get(key) != digest(artifact):
            raise ValueError('T2 evaluation artifact hash differs: ' + key)
    for key, artifact in [('history_sha256', OUT / 't2-history.csv'),
                          ('model_selection_sha256', OUT / 't2-model-selection.csv'),
                          ('features_receipt_sha256', OUT / 'features.json')]:
        if t2_training.get(key) != digest(artifact):
            raise ValueError('T2 training artifact hash differs: ' + key)
    features = read_json(OUT / 'features.json')
    if t2_training.get('text_revision') != features['text_revision']:
        raise ValueError('T2 encoder revision differs from the recorded base encoder')
    candidates = t2_training['candidate_models']
    expected_pairs = {(float(rate), seed) for rate in t2_protocol['learning_rates'] for seed in seeds}
    actual_pairs = {(float(row['learning_rate']), int(row['seed'])) for row in candidates}
    if len(candidates) != len(expected_pairs) or actual_pairs != expected_pairs:
        raise ValueError('T2 candidate grid differs from all prespecified learning-rate/seed pairs')
    mean_by_rate = {}
    for rate in sorted(float(value) for value in t2_protocol['learning_rates']):
        scores = [float(row['dev_macro_f1']) for row in candidates if float(row['learning_rate']) == rate]
        if any(not math.isfinite(score) or not 0 <= score <= 1 for score in scores):
            raise ValueError('Invalid T2 development metric')
        mean_by_rate[rate] = sum(scores) / len(scores)
    selected_rate = max(sorted(mean_by_rate), key=lambda rate: mean_by_rate[rate])
    if float(t2_training['selected_learning_rate']) != selected_rate:
        raise ValueError('T2 learning rate was not selected from mean development scores')
    selected = t2_training['selected_models']
    if len(selected) != len(seeds) or {int(row['seed']) for row in selected} != set(seeds):
        raise ValueError('T2 did not retain all selected learning-rate seeds')
    for row in candidates:
        if digest(ROOT / row['checkpoint']) != row['checkpoint_sha256']:
            raise ValueError('T2 candidate checkpoint hash changed')
    for row in selected:
        if float(row['learning_rate']) != selected_rate or not any(row == candidate for candidate in candidates):
            raise ValueError('T2 selected model was not one of the development-selected candidates')
    for name, expected in t2_training.get('source_sha256', {}).items():
        source = ROOT / name
        if not source.is_file():
            source = BASE / name
        if digest(source) != expected:
            raise ValueError('T2 training source changed: ' + name)
    for metric in ['accuracy', 'macro_f1', 'precision_request', 'recall_request']:
        values = [row[metric] for row in independently_computed.values()]
        for key, expected in [('mean', sum(values) / len(values)), ('min', min(values)), ('max', max(values))]:
            close(t2_evaluation['summary'][metric][key], expected, f'T2/summary/{metric}/{key}')
    return {'status': 'VERIFIED_T2_RECEIPTS_SELECTION_PREDICTIONS_AND_METRICS', 'seeds': seeds,
            'n_test_per_seed': len(test), 'prediction_rows': len(predictions),
            'metrics_independent': independently_computed,
            'mean_macro_f1': sum(value['macro_f1'] for value in independently_computed.values()) / len(seeds),
            'protocol_sha256': digest(protocol_path), 'predictions_sha256': digest(prediction_path),
            'metrics_sha256': digest(metric_path),
            'training_receipt_sha256': digest(training_path),
            'evaluation_receipt_sha256': digest(evaluation_path), 'selected_learning_rate': selected_rate,
            'limits': 'T2 development selection, model/receipt hashes and independent metric formulas checked; seed repetitions do not increase independent test sample size'}


def main():
    if (OUT / 'verification.json').exists():
        raise SystemExit('Refusing to overwrite verification receipt')
    rows = load_data()
    protocol = read_json(PROTOCOL)
    info = read_json(OUT / 'evaluation.json')
    training = read_json(OUT / 'training.json')
    features = read_json(OUT / 'features.json')
    checks = {}
    if info.get('task') != TASK or info.get('label_origin') != 'AI_SILVER_TEXT_ONLY':
        raise ValueError('Wrong evaluation task or label origin')
    checks['task_and_ai_silver_scope'] = 'PASS'
    bindings = {'dataset_sha256': digest(BASE / 'data/dataset.json'),
                'protocol_sha256': digest(PROTOCOL), 'cache_sha256': digest(BASE / 'cache/embeddings.npz')}
    for key, expected in bindings.items():
        for name, receipt in [('evaluation', info), ('training', training), ('features', features)]:
            if receipt.get(key) != expected:
                raise ValueError(f'{name} binding mismatch: {key}')
    checks['dataset_protocol_feature_bindings'] = 'PASS'
    for key, path in [('model_sha256', BASE / 'models/classifiers.joblib'),
                      ('features_receipt_sha256', OUT / 'features.json'),
                      ('training_receipt_sha256', OUT / 'training.json'),
                      ('predictions_sha256', OUT / 'predictions.csv'),
                      ('metrics_sha256', OUT / 'metrics.csv'),
                      ('paired_effects_sha256', OUT / 'paired-effects.csv')]:
        if info.get(key) != digest(path):
            raise ValueError('Evaluation artifact hash mismatch: ' + key)
    if training['model_sha256'] != info['model_sha256']:
        raise ValueError('Training model hash differs from evaluation')
    for name, expected in info['source_sha256'].items():
        if digest(BASE / name) != expected:
            raise ValueError('Evaluated source changed: ' + name)
    checks['prediction_model_receipt_and_source_hashes'] = 'PASS'
    predictions = read_csv(OUT / 'predictions.csv')
    metrics = read_csv(OUT / 'metrics.csv')
    effects = read_csv(OUT / 'paired-effects.csv')
    test = {row['image_id']: row for row in rows if row['split'] == 'test'}
    if {row['model'] for row in predictions} != set(EXPECTED_MODELS):
        raise ValueError('Missing or extra prediction configurations')
    if len(predictions) != len(test) * len(EXPECTED_MODELS):
        raise ValueError('Prediction row count differs from complete matched test IDs')
    threshold = float(protocol['classifier']['threshold'])
    if float(info['threshold']) != threshold:
        raise ValueError('Threshold changed after protocol')
    tables = {name: {} for name in EXPECTED_MODELS}
    for row in predictions:
        model, rid = row['model'], row['image_id']
        if rid not in test or rid in tables[model]:
            raise ValueError('Unexpected or duplicated test ID')
        source = test[rid]
        if any(row[key] != source[key] for key in ['group_id', 'event_name']):
            raise ValueError('Prediction metadata mismatch')
        if row['label_ai'] != source['label'] or row['label_ai'] not in LABELS:
            raise ValueError('Silver label differs from dataset')
        probability = float(row['probability_request'])
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError('Probability is not finite and within [0, 1]')
        if row['predicted_label'] != LABELS[int(probability >= threshold)]:
            raise ValueError('Prediction does not match the locked threshold')
        tables[model][rid] = row
    for model, table in tables.items():
        if set(table) != set(test):
            raise ValueError('Test IDs differ by configuration: ' + model)
    checks['same_complete_test_ids_no_duplicates'] = 'PASS'
    checks['metadata_ai_labels_probabilities_and_threshold'] = 'PASS'
    if len(metrics) != len(EXPECTED_MODELS) or {r['model'] for r in metrics} != set(EXPECTED_MODELS):
        raise ValueError('Metrics model set mismatch')
    metric_map = {row['model']: row for row in metrics}
    group_order = sorted({row['group_id'] for row in test.values()})
    group_index = {name: i for i, name in enumerate(group_order)}
    # Counts are derived directly from text labels, independently of sklearn.
    grouped_counts = {name: np.zeros((len(group_order), 4), dtype=np.int64) for name in EXPECTED_MODELS}
    independently_computed = {}
    for name, table in tables.items():
        counts = [0, 0, 0, 0]
        for rid, row in table.items():
            actual = LABELS.index(row['label_ai'])
            predicted = LABELS.index(row['predicted_label'])
            position = actual * 2 + predicted  # tn, fp, fn, tp
            counts[position] += 1
            grouped_counts[name][group_index[row['group_id']], position] += 1
        independently_computed[name] = independent_metrics(counts)
        for key, expected in independently_computed[name].items():
            close(metric_map[name][key], expected, name + '/' + key)
    checks['confusion_accuracy_precision_recall_macro_f1_independent_formulas'] = 'PASS'
    if info['n_test'] != len(test) or info['groups'] != len(group_order) or info['prediction_rows'] != len(predictions):
        raise ValueError('Evaluation summary counts mismatch')
    if info['configurations'] != EXPECTED_MODELS or info['bootstrap_group_order'] != group_order:
        raise ValueError('Configuration or bootstrap group order mismatch')
    events = sorted({row['event_name'] for row in test.values()})
    if info['events'] != events or len(events) != 1:
        raise ValueError('Test event scope mismatch')
    checks['evaluation_counts_and_one_event_scope'] = 'PASS'
    primary = training['primary_comparator_selected_on_dev']
    if primary not in ['T1', 'I0'] or info['primary_comparator_selected_on_dev'] != primary:
        raise ValueError('Primary comparator changed after development selection')
    if len(effects) != 3 or {row['comparator'] for row in effects} != set(COMPARATORS):
        raise ValueError('Paired contrast set mismatch')
    draws = int(protocol['bootstrap']['draws'])
    seed = int(protocol['classifier']['seed'])
    if info['bootstrap_draws'] != draws or info['bootstrap_seed'] != seed:
        raise ValueError('Bootstrap settings differ from protocol')
    generator = np.random.default_rng(seed)
    replay = {name: [] for name in COMPARATORS}
    absent_class_draws = 0
    for _ in range(draws):
        picked = generator.integers(0, len(group_order), size=len(group_order))
        # Same group draws for every model; sum independently built confusion counts.
        fusion_counts = grouped_counts['F1'][picked].sum(axis=0)
        tn, fp, fn, tp = (int(x) for x in fusion_counts)
        absent_class_draws += int(tn + fp == 0 or fn + tp == 0)
        fusion = independent_metrics(fusion_counts)['macro_f1']
        for name in COMPARATORS:
            replay[name].append(fusion - independent_metrics(grouped_counts[name][picked].sum(axis=0))['macro_f1'])
    for row in effects:
        name = row['comparator']
        close(row['delta'], independently_computed['F1']['macro_f1'] - independently_computed[name]['macro_f1'], name + '/delta')
        lower, upper = np.quantile(replay[name], [0.025, 0.975])
        close(row['ci_low'], lower, name + '/ci_low')
        close(row['ci_high'], upper, name + '/ci_high')
        if row['primary'] != str(name == primary) or row['adjusted'] != 'False' or int(row['draws']) != draws:
            raise ValueError('Effect interpretation metadata mismatch')
    if info['bootstrap_absent_class_draws'] != absent_class_draws:
        raise ValueError('Missing-class bootstrap count mismatch')
    checks['paired_bootstrap_cis_replayed_from_independent_confusion_counts'] = 'PASS'
    checks['primary_dev_selection_and_unadjusted_contrast_metadata'] = 'PASS'
    t2 = verify_t2(test, bindings['dataset_sha256'], bindings['protocol_sha256'], threshold)
    if t2['status'] == 'VERIFIED_T2_RECEIPTS_SELECTION_PREDICTIONS_AND_METRICS':
        checks['t2_optional_protocol_seed_ids_probabilities_and_independent_metrics'] = 'PASS'
    write_json(OUT / 'verification.json', {'status': 'VERIFIED_WITHIN_AI_SILVER_PILOT',
        'task': TASK, 'checks': checks, 'check_count': len(checks),
        'n_test': len(test), 'groups': len(group_order), 'prediction_rows': len(predictions),
        'evaluation_sha256': digest(OUT / 'evaluation.json'),
        'predictions_sha256': digest(OUT / 'predictions.csv'),
        'verifier_sha256': digest(BASE / 'verify.py'),
        'metrics_independent': independently_computed,
        'bootstrap_replayed': True, 'bootstrap_draws': draws,
        'T2': t2,
        'scope': 'Technical recomputation against AI silver labels, not scientific or expert validation',
        'limits': ['Vietnamese text was translated by AI from existing English CrisisMMD source text',
                   'AI source-text labels are not independent human or multimodal reference labels',
                   'The frozen fusion branch does not fine-tune encoders; any separate T2 result has its own status above',
                   'No native-Vietnamese, operational urgency, Android or real-world rescue-effectiveness claim']})
    print(f'PASS {len(checks)} checks; independent metrics and {draws} paired bootstrap draws replayed', flush=True)


if __name__ == '__main__':
    main()
