"""Capture the authorized local report evidence without loading model weights."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
RUN = ROOT / 'thuc_nghiem_nq/notebook_bundle/local-work/local-20261110-04'


def sha(stream):
    h = hashlib.sha256()
    for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
        h.update(block)
    return h.hexdigest()


def main():
    destination = HERE / 'evidence'
    destination.mkdir(exist_ok=False)
    selected = [
        'local-control/state.json', 'bundle-results/locked-config.json',
        'bundle-results/preflight/preflight.json',
        'historical_evidence/pruning/all_predictions.csv',
        'products/fe/model/Edge Ai/split_train_val_test_mobilenetv3_large.csv',
        'bundle-results/historical_analysis/pruning-paired-statistics.json',
        'bundle-results/image_pruning/selection.json',
        'bundle-results/image_export_compare/selected-model.json',
        'bundle-results/image_ptq/report/quantization.json',
        'bundle-results/quantization_analysis/validation-debug/activation-errors.json',
    ]
    for ratio in ['0.050', '0.100', '0.200']:
        selected += [f'bundle-results/image_pruning/ratio-{ratio}/{name}'
                     for name in ['metrics.json', 'history.csv']]
    for stage in ['image_export_compare', 'quantization_analysis']:
        selected += [f'bundle-results/{stage}/{name}' for name in
                     ['paired-statistics.json', 'comparison/summary.json', 'comparison/all_predictions.csv']]
    selected += [str(p.relative_to(RUN)).replace('\\', '/') for p in
                 sorted((RUN / 'bundle-results/silver_evaluation/outputs').iterdir())
                 if p.suffix in {'.csv', '.json'}]
    for stage in ['historical_analysis', 'image_pruning', 'image_export_compare',
                  'image_ptq', 'quantization_analysis', 'silver_t2', 'silver_evaluation']:
        selected.append(f'bundle-results/{stage}/stage.json')
    manifest = {}
    for relative in selected:
        source, target = RUN / relative, destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        with target.open('rb') as stream:
            manifest[relative] = {'sha256': sha(stream), 'bytes': target.stat().st_size}
    # The two extracted files differ from their receipts. Preserve them unchanged;
    # verify the original ZIP entries instead of silently repairing model inputs.
    receipt = json.loads((RUN / 'bundle-results/silver_t2/stage.json').read_text())
    archive = RUN.parent / 'local-20261110-04-results.zip'
    checks = []
    with zipfile.ZipFile(archive) as package:
        for relative, expected in receipt['external_outputs'].items():
            if 'lr-2e-05-seed-43' not in relative or not relative.endswith('.pt'):
                continue
            normalized = relative.replace('\\', '/')
            with (RUN / normalized).open('rb') as stream:
                current = sha(stream)
            with package.open(normalized) as stream:
                archived = sha(stream)  # ZipFile also checks each entry's CRC.
            if archived != expected:
                raise ValueError('Archived checkpoint does not match receipt: ' + normalized)
            checks.append({'path': normalized, 'receipt_sha256': expected,
                           'extracted_sha256': current, 'archive_sha256': archived,
                           'extracted_matches': current == expected, 'archive_matches': True})
    if len(checks) != 2:
        raise ValueError('Expected two seed-43 checkpoint checks')
    audit = {'run_id': RUN.name, 'archive': str(archive.relative_to(ROOT)),
             'checks': checks, 'action': 'READ_ONLY_NO_CHECKPOINT_REPAIR',
             'scope': 'Archive entry SHA-256 and CRC; no inference or training reproduction'}
    (HERE / 'checkpoint-audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    (HERE / 'source-manifest.json').write_text(json.dumps({
        'run_id': RUN.name, 'source_root': str(RUN.relative_to(ROOT)),
        'files': manifest,
        'checkpoint_audit_sha256': hashlib.sha256((HERE / 'checkpoint-audit.json').read_bytes()).hexdigest(),
        'scope': 'Compact report evidence; model weights and original inputs are not modified',
    }, ensure_ascii=False, indent=2) + '\n')
    print(f'Captured {len(manifest)} evidence files; both archived seed-43 checkpoints match receipts')


if __name__ == '__main__':
    main()
