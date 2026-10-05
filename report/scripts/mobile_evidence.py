"""Audit the two concatenated mobile benchmark objects without changing the source."""
import hashlib
import json
import math

CLASSES = ['low', 'medium', 'high', 'non_flood']


def audit_mobile(data, split):
    remaining = data.decode('utf-8-sig').strip()
    blocks = []
    decoder = json.JSONDecoder()
    while remaining:
        block, end = decoder.raw_decode(remaining)
        blocks.append(block)
        remaining = remaining[end:].strip()
    if len(blocks) != 2 or {b['runtime'] for b in blocks} != {'onnx', 'pte'}:
        raise ValueError('Expected exactly one ONNX and one PTE mobile report')
    expected = {
        hashlib.sha1(r['relative_path'].replace('\\', '/').encode()).hexdigest()[:12]: r
        for r in split if r['split'] == 'test'
    }
    if len(expected) != sum(r['split'] == 'test' for r in split):
        raise ValueError('Mobile sample ID collision')
    reports = {}
    for b in blocks:
        p = b['predictions']
        if (not b['complete'] or len(p) != len(expected) or
                b['expectedSamples'] != len(expected) or b['processedSamples'] != len(expected) or
                b['failedSamples'] != 0 or b['warmupErrors'] != 0 or
                len({r['id'] for r in p}) != len(p) or {r['id'] for r in p} != set(expected)):
            raise ValueError('Incomplete or mismatched mobile test split')
        matrix = {c: {d: 0 for d in CLASSES + ['unclassified']} for c in CLASSES}
        for r in p:
            if r['truth'] != expected[r['id']]['label'] or r['prediction'] not in CLASSES:
                raise ValueError('Mobile truth/prediction mismatch')
            if not math.isfinite(r['latencyMs']) or r['latencyMs'] < 0:
                raise ValueError('Invalid mobile latency')
            if not math.isfinite(r['confidence']) or not 0 <= r['confidence'] <= 1:
                raise ValueError('Invalid mobile confidence')
            matrix[r['truth']][r['prediction']] += 1
        accuracy = sum(matrix[c][c] for c in CLASSES) / len(p)
        f1 = sum(2 * matrix[c][c] / (sum(matrix[c].values()) + sum(matrix[d][c] for d in CLASSES))
                 for c in CLASSES) / len(CLASSES)
        if matrix != b['confusionMatrix'] or abs(accuracy - b['accuracy']) > 1e-10 or abs(f1 - b['macroF1']) > 1e-10:
            raise ValueError('Mobile metrics do not match predictions')
        for c in CLASSES:
            precision = matrix[c][c] / sum(matrix[d][c] for d in CLASSES)
            recall = matrix[c][c] / sum(matrix[c].values())
            expected_metrics = {'precision': precision, 'recall': recall,
                                'f1': 2 * precision * recall / (precision + recall)}
            if any(abs(b['classMetrics'][c][key] - value) > 1e-10 for key, value in expected_metrics.items()):
                raise ValueError('Mobile per-class metrics mismatch')
        latencies = sorted(r['latencyMs'] for r in p)
        for key, value in [('meanMs', sum(latencies) / len(p)),
                           ('medianMs', latencies[math.ceil(len(p) * .5) - 1]),
                           ('p95Ms', latencies[math.ceil(len(p) * .95) - 1])]:
            if abs(b['latency'][key] - value) > 1e-7:
                raise ValueError('Mobile latency summary mismatch: ' + key)
        reports[b['runtime']] = b
    by_id = [{r['id']: r for r in reports[k]['predictions']} for k in ['onnx', 'pte']]
    agreement = sum(by_id[0][k]['prediction'] == by_id[1][k]['prediction'] for k in expected)
    return reports, {'objects': len(blocks), 'samples_per_runtime': len(expected),
                     'sample_ids_and_labels_match_split': True, 'metrics_match_predictions': True,
                     'latency_matches_nearest_rank_summary': True, 'top1_agreement_count': agreement,
                     'metadata_limitations': ['device model, OS, APK/commit, asset hashes and measurement date absent']}
