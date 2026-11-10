#!/usr/bin/env python3
"""Validate and export the local development replay; never train or load models."""
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'docs/revision-plan/outputs/local-report-update-20261110'
EVIDENCE = SOURCE / 'evidence'
RESULTS = EVIDENCE / 'bundle-results'
SILVER = RESULTS / 'silver_evaluation/outputs'
OUT = ROOT / 'report/generated'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def close(actual, expected):
    if not math.isclose(float(actual), float(expected), abs_tol=1e-11, rel_tol=1e-10):
        raise ValueError(f'Metric mismatch: {actual} != {expected}')


def classification(data, gold, prediction, labels):
    cm = [[sum(r[gold] == a and r[prediction] == b for r in data)
           for b in labels] for a in labels]
    tp = [cm[i][i] for i in range(len(labels))]
    support = [sum(row) for row in cm]
    predicted = [sum(row[i] for row in cm) for i in range(len(labels))]
    f1 = [2 * tp[i] / (support[i] + predicted[i]) if support[i] + predicted[i] else 0
          for i in range(len(labels))]
    return {'accuracy': sum(tp) / len(data), 'macro_f1': sum(f1) / len(labels),
            'recall_request': tp[-1] / support[-1] if support[-1] else 0,
            'precision_request': tp[-1] / predicted[-1] if predicted[-1] else 0,
            'confusion': cm}


def verify():
    manifest = read(SOURCE / 'source-manifest.json')
    for relative, expected in manifest['files'].items():
        path = EVIDENCE / relative
        if path.stat().st_size != expected['bytes'] or digest(path) != expected['sha256']:
            raise ValueError('Changed captured evidence: ' + relative)
    if digest(SOURCE / 'checkpoint-audit.json') != manifest['checkpoint_audit_sha256']:
        raise ValueError('Changed checkpoint audit')
    audit = read(SOURCE / 'checkpoint-audit.json')
    if len(audit['checks']) != 2 or not all(
            r['archive_matches'] and r['archive_sha256'] == r['receipt_sha256']
            for r in audit['checks']):
        raise ValueError('Seed-43 archive provenance is incomplete')
    for stage in RESULTS.glob('*/stage.json'):
        receipt = read(stage)
        if receipt['status'] != 'COMPLETED':
            raise ValueError('Unfinished captured stage: ' + str(stage))
        for base, entries in [(stage.parent, receipt.get('outputs', {})),
                              (EVIDENCE, receipt.get('external_outputs', {}))]:
            for relative, expected in entries.items():
                path = base / relative.replace('\\', '/')
                if path.is_file() and digest(path) != expected:
                    raise ValueError('Snapshot differs from stage receipt: ' + str(path))
    checked = 0
    labels = ['low', 'medium', 'high', 'non_flood']
    split_path = EVIDENCE / 'products/fe/model/Edge Ai/split_train_val_test_mobilenetv3_large.csv'
    split = rows(split_path)
    ids = {(r['label'], r['file_name']) for r in split if r['split'] == 'test'}
    for prefix, prediction_file in [
            ('historical_analysis/pruning', EVIDENCE / 'historical_evidence/pruning/all_predictions.csv'),
            ('image_export_compare', RESULTS / 'image_export_compare/comparison/all_predictions.csv'),
            ('quantization_analysis', RESULTS / 'quantization_analysis/comparison/all_predictions.csv')]:
        stats = read(RESULTS / (prefix + '-paired-statistics.json' if prefix.startswith('historical')
                                else prefix + '/paired-statistics.json'))
        data = rows(prediction_file)
        if digest(split_path) != stats['split_sha256']:
            raise ValueError('Saved split hash differs from paired statistics')
        keys = [(r['ground_truth'], r['image_path'].replace('\\', '/').rsplit('/', 1)[-1]) for r in data]
        if len(keys) != len(set(keys)) or set(keys) != ids or digest(prediction_file) != stats['predictions_sha256']:
            raise ValueError('Paired image identities/hash differ')
        for name, expected in stats['metrics'].items():
            got = classification(data, 'ground_truth', 'pred_' + name, labels)
            close(got['accuracy'], expected['accuracy'])
            close(got['macro_f1'], expected['macro_f1'])
            if got['confusion'] != expected['confusion']:
                raise ValueError('Image confusion differs')
            checked += 1
        raw = {}
        for name, expected in stats['pairs'].items():
            left, right = name.split(' -> ')
            for metric in ['accuracy', 'macro_f1']:
                close(stats['metrics'][right][metric] - stats['metrics'][left][metric],
                      expected['delta_' + metric])
            cw = sum(r['pred_' + left] == r['ground_truth'] and r['pred_' + right] != r['ground_truth'] for r in data)
            wc = sum(r['pred_' + left] != r['ground_truth'] and r['pred_' + right] == r['ground_truth'] for r in data)
            n = cw + wc
            p = min(1., 2 * sum(math.comb(n, k) for k in range(min(cw, wc) + 1)) / 2**n) if n else 1.
            if (cw, wc) != (expected['correct_to_wrong'], expected['wrong_to_correct']):
                raise ValueError('McNemar discordances differ')
            close(p, expected['mcnemar_exact_p_unadjusted'])
            raw[name] = p
        previous = 0.
        for rank, (name, p) in enumerate(sorted(raw.items(), key=lambda item: item[1])):
            previous = max(previous, min(1., (len(raw) - rank) * p))
            close(previous, stats['pairs'][name]['mcnemar_holm_p'])
    identity_sets = []
    for pf, mf, key in [('predictions.csv', 'metrics.csv', 'model'),
                        ('t2-predictions.csv', 't2-metrics.csv', 'seed')]:
        groups = defaultdict(list)
        for row in rows(SILVER / pf):
            groups[row[key]].append(row)
        for expected in rows(SILVER / mf):
            data = groups[expected[key]]
            identity = {(r['image_id'], r['label_ai']) for r in data}
            if len(identity) != len(data) or len(data) != int(expected['n']):
                raise ValueError('Silver IDs are duplicated or incomplete')
            identity_sets.append(identity)
            got = classification(data, 'label_ai', 'predicted_label', ['no_request', 'request'])
            for metric in ['accuracy', 'macro_f1', 'precision_request', 'recall_request']:
                close(got[metric], expected[metric])
            if got['confusion'][0] + got['confusion'][1] != [int(expected[k]) for k in ['tn', 'fp', 'fn', 'tp']]:
                raise ValueError('Silver confusion differs')
            checked += 1
    if any(s != identity_sets[0] for s in identity_sets):
        raise ValueError('T2/frozen test identities or labels differ')
    old = ROOT / 'docs/revision-plan/outputs/vi-nlp-fusion-silver-20261108'
    for name in ['metrics.csv', 'paired-effects.csv', 'protocol.json']:
        if digest(old / name) != digest(SILVER / name):
            raise ValueError('Frozen silver replay no longer matches reported pilot')
    print(f'Local evidence: {len(manifest["files"])} captured hashes, {checked} metrics and paired image tests verified')
    return {'captured_files': len(manifest['files']), 'metric_configurations': checked,
            'bootstrap': 'IMPORTED_NOT_RERUN', 'training_and_inference': 'NOT_RUN',
            'seed43_checkpoint_source': 'HASH_MATCHED_ARCHIVE_ENTRIES',
            'extracted_seed43_checkpoints': 'HASH_MISMATCH_PRESERVED'}


def fmt(value, digits=2):
    return f'{float(value):.{digits}f}'.replace('.', ',')


def table(name, caption, columns, headers, data):
    lines = ['% Generated by export_local_experiments.py; do not edit.',
             r'\begin{table}[htbp]\centering\small\setlength{\tabcolsep}{3pt}',
             r'\caption{' + caption + r'}\label{tab:' + name + '}',
             r'\begin{tabular}{' + columns + r'}\toprule',
             ' & '.join(headers) + r' \\ \midrule']
    lines += [' & '.join(map(str, row)) + r' \\' for row in data]
    lines += [r'\bottomrule\end{tabular}', r'\end{table}']
    (OUT / 'tables' / (name + '.tex')).write_text('\n'.join(lines) + '\n')


def main():
    verification = verify()
    candidates = []
    for ratio in ['0.050', '0.100', '0.200']:
        data = read(RESULTS / f'image_pruning/ratio-{ratio}/metrics.json')
        p, val = data['pruning'], data['best_validation']
        if data['final_test'] is not None:
            raise ValueError('Candidate grid must defer test evaluation')
        candidates.append([fmt(100 * p['target_ratio'], 0),
                           fmt(100 * (1 - p['parameter_count_after'] / p['parameter_count_before'])),
                           fmt(100 * val['accuracy']), fmt(100 * val['macro_f1']), data['best_epoch']])
    table('local-pruning-grid', 'Thử mức cắt tỉa cao hơn: chỉ dùng validation để chọn ứng viên',
          'rrrrr', [r'Tỷ lệ mục tiêu (\%)', r'Giảm tham số (\%)', r'Acc. val (\%)', r'F1 val (\%)', 'Epoch chọn'], candidates)
    historic = read(RESULTS / 'historical_analysis/pruning-paired-statistics.json')
    pruning = read(RESULTS / 'image_export_compare/paired-statistics.json')
    quant = read(RESULTS / 'quantization_analysis/paired-statistics.json')
    paired = []
    for title, pair in [('Pruning 1\\% lịch sử', historic['pairs']['baseline_pth -> structured_pth']),
                        ('Pruning 5\\% mới', pruning['pairs']['baseline -> structured_pruned'])]:
        low, high = pair['delta_macro_f1_ci95_unadjusted']
        paired.append([title, pair['correct_to_wrong'], pair['wrong_to_correct'],
                       fmt(100 * pair['delta_macro_f1']), f'[{fmt(100 * low)}; {fmt(100 * high)}]',
                       fmt(pair['mcnemar_exact_p_unadjusted'], 4), fmt(pair['mcnemar_holm_p'], 4)])
    table('local-pruning-paired', 'Kiểm định pruning trên cùng 256 ảnh; hiệu Macro-F1 là sau trừ trước',
          'lrrrrrr', ['So sánh', r'Đ$\to$S', r'S$\to$Đ', r'$\Delta$ F1 (đpt)', 'CI 95\\%', r'$p$ exact', r'$p$ Holm'], paired)
    replay = []
    for folder, name, title in [
            ('image_export_compare', 'baseline', 'Baseline (PTH)'),
            ('image_export_compare', 'structured_pruned', r'Pruning 5\% (PTH)'),
            ('quantization_analysis', 'onnx_fp32', 'Baseline (ONNX FP32)'),
            ('quantization_analysis', 'ptq_int8', 'PTQ mới (ONNX INT8)'),
            ('quantization_analysis', 'qat_int8', 'QAT lịch sử (ONNX INT8)')]:
        m = read(RESULTS / folder / 'comparison/summary.json')['classification_metrics'][name]
        stats = pruning['metrics'][name] if folder == 'image_export_compare' else quant['metrics'][name]
        replay.append([title, fmt(100 * m['accuracy']), fmt(100 * m['macro_f1']),
                       fmt(100 * stats['recall_high']), stats['critical_errors'], fmt(m['latency_ms_median'])])
    table('local-image-replay', 'Đánh giá ảnh trong phiên local mới; latency CPU một luồng, batch 1',
          'lrrrrr', ['Mô hình', r'Acc. (\%)', r'F1 (\%)', r'Recall high (\%)', 'Lỗi nặng', 'Median ms'], replay)
    v = {'PrunedFOne': fmt(100 * pruning['metrics']['structured_pruned']['macro_f1']),
         'PrunedAccuracy': fmt(100 * pruning['metrics']['structured_pruned']['accuracy']),
         'PTQFOne': fmt(100 * quant['metrics']['ptq_int8']['macro_f1']),
         'QATFOne': fmt(100 * quant['metrics']['qat_int8']['macro_f1'])}
    (OUT / 'local-experiment-values.tex').write_text('\n'.join(
        [r'% Generated local development replay values.'] +
        [r'\providecommand{\Local' + k + '}{' + value + '}' for k, value in v.items()]) + '\n')
    verification['source_manifest_sha256'] = digest(SOURCE / 'source-manifest.json')
    verification['exporter_sha256'] = digest(Path(__file__))
    (OUT / 'local-experiment-provenance.json').write_text(json.dumps(verification, indent=2) + '\n')


if __name__ == '__main__':
    main()
