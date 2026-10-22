"""Export and independently check saved schema-v2 phone benchmarks; no inference."""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'report/generated/phone-benchmarks'
CLASSES = ['low', 'medium', 'high', 'non_flood']
SEVERITY = {'non_flood': 0, 'low': 1, 'medium': 2, 'high': 3}
DEVICES = ['realme15', 'redminote11', 'redminote13', 'samsungs10e']


def write_csv(name, rows):
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    split_path = ROOT / 'products/fe/model/Edge Ai/split_train_val_test_mobilenetv3_large.csv'
    split_hash = hashlib.sha256(split_path.read_bytes()).hexdigest()
    with split_path.open(encoding='utf-8-sig', newline='') as f:
        split = [r for r in csv.DictReader(f) if r['split'] == 'test']
    expected = {hashlib.sha1(r['relative_path'].replace('\\', '/').encode()).hexdigest()[:12]: r for r in split}
    assert len(expected) == len(split) == 256
    summary, predictions, classes, coverage = [], [], [], []
    seen = set()
    for path in sorted((ROOT / 'products/fe/reports').glob('seed*/mobile/seed*/*/benchmark_*.json')):
        d = json.loads(path.read_text(encoding='utf-8-sig'))
        prov = d['provenance']
        model = prov['model']
        seed = int(path.parts[-5].removeprefix('seed'))
        variant = 'baseline' if path.parts[-3].endswith('baseline') else 'pruning'
        device = path.parent.name
        key = (seed, variant, device, d['runtime'])
        assert key not in seen, ('Duplicate condition', path)
        seen.add(key)
        p = d['predictions']
        assert d['schemaVersion'] == 2 and d['split'] == 'test' and prov['splitCsvSha256'] == split_hash
        assert d['complete'] and d['expectedSamples'] == d['processedSamples'] == len(p) == len(expected)
        assert d['failedSamples'] == d['warmupErrors'] == 0 and d['warmupRuns'] == 5
        assert len({r['id'] for r in p}) == len(p) and {r['id'] for r in p} == set(expected)
        matrix = {c: {k: 0 for k in CLASSES + ['unclassified']} for c in CLASSES}
        for r in p:
            assert r['truth'] == expected[r['id']]['label'] and r['prediction'] in CLASSES
            assert math.isfinite(r['latencyMs']) and r['latencyMs'] >= 0
            assert math.isfinite(r['confidence']) and 0 <= r['confidence'] <= 1
            matrix[r['truth']][r['prediction']] += 1
        assert matrix == d['confusionMatrix']
        accuracy = sum(matrix[c][c] for c in CLASSES) / len(p)
        common = dict(seed=seed, variant=variant, device=device, runtime=d['runtime'], run_id=prov['runId'])
        class_rows = []
        for c in CLASSES:
            tp = matrix[c][c]
            support = sum(matrix[c].values())
            predicted = sum(matrix[k][c] for k in CLASSES)
            metrics = dict(precision=tp / predicted if predicted else 0,
                           recall=tp / support if support else 0,
                           f1=2 * tp / (support + predicted) if support + predicted else 0)
            assert all(math.isclose(metrics[k], d['classMetrics'][c][k], abs_tol=1e-10) for k in metrics)
            class_rows.append(dict(common, label=c, support=support, **metrics))
        f1 = sum(r['f1'] for r in class_rows) / len(CLASSES)
        assert math.isclose(accuracy, d['accuracy'], abs_tol=1e-10)
        assert math.isclose(f1, d['macroF1'], abs_tol=1e-10)
        times = sorted(r['latencyMs'] for r in p)
        latency = dict(meanMs=sum(times) / len(times), medianMs=times[math.ceil(.5 * len(times)) - 1],
                       p95Ms=times[math.ceil(.95 * len(times)) - 1])
        assert all(math.isclose(v, d['latency'][k], abs_tol=1e-7) for k, v in latency.items())
        assert prov['artifactSha256'] == model[d['runtime'] + '_sha256']
        source = path.relative_to(ROOT).as_posix()
        distances = [abs(SEVERITY[r['truth']] - SEVERITY[r['prediction']]) for r in p]
        ordinal_mae = sum(distances) / len(p)
        ordinal_rmse = math.sqrt(sum(v * v for v in distances) / len(p))
        assert 0 <= ordinal_mae <= ordinal_rmse <= 3
        high_metrics = next(r for r in class_rows if r['label'] == 'high')
        summary.append(dict(common, manufacturer=prov['device']['manufacturer'],
                            device_model=prov['device']['model'], android=prov['device']['androidRelease'],
                            android_sdk=prov['device']['androidSdk'],
                            supported_abis=';'.join(prov['device']['supportedAbis']),
                            app_version=prov['app']['versionName'], app_version_code=prov['app']['versionCode'],
                            model_version=model['version'], artifact_sha256=prov['artifactSha256'],
                            checkpoint_sha256=model['checkpoint_sha256'], split_sha256=split_hash,
                            started_at_utc=prov['startedAtUtc'], finished_at_utc=prov['finishedAtUtc'],
                            latency_scope=prov['latencyScope'], samples=len(p), warmup_runs=d['warmupRuns'],
                            accuracy=accuracy, macro_f1=f1,
                            macro_precision=sum(r['precision'] for r in class_rows) / 4,
                            macro_recall=sum(r['recall'] for r in class_rows) / 4,
                            precision_high=high_metrics['precision'], recall_high=high_metrics['recall'],
                            f1_high=high_metrics['f1'], ordinal_mae=ordinal_mae, ordinal_rmse=ordinal_rmse,
                            balanced_accuracy=sum(r['recall'] for r in class_rows) / 4,
                            mean_ms=latency['meanMs'], p50_ms=latency['medianMs'], p95_ms=latency['p95Ms'],
                            source_json=source, source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                            validation='PASS'))
        classes.extend(dict(r, source_json=source) for r in class_rows)
        predictions.extend(dict(common, **r, relative_path=expected[r['id']]['relative_path'],
                                correct=int(r['truth'] == r['prediction']), source_json=source) for r in p)
    assert summary, 'No phone benchmarks found'
    for seed in [159, 1024]:
        for variant in ['baseline', 'pruning']:
            for device in DEVICES:
                for runtime in ['onnx', 'pte']:
                    coverage.append(dict(seed=seed, variant=variant, device=device, runtime=runtime,
                                         status='AVAILABLE' if (seed, variant, device, runtime) in seen else 'MISSING'))
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in [('summary.csv', summary), ('predictions.csv', predictions),
                       ('class_metrics.csv', classes), ('coverage.csv', coverage)]:
        write_csv(name, rows)
    for device in DEVICES:
        write_csv(device + '.csv', [r for r in summary if r['device'] == device])
    print(json.dumps(dict(benchmarks=len(summary), prediction_rows=len(predictions),
                          class_rows=len(classes), missing=[r for r in coverage if r['status'] == 'MISSING'])))


if __name__ == '__main__':
    main()
