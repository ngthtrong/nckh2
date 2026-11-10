"""Explicit, audited repair for the known silver classifier missing-directory failure.

Leaves bundled code, environment identity and completed stages unchanged.
Reuses verified frozen features, reruns only the failed linear-head training,
then leaves the controller PAUSED for the user to resume.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import sys
import time

import local_runner as launcher


def repair(run_id):
    os.environ['PYTHONUTF8'] = '1'
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    root = launcher.project_path(run_id)
    if Path(sys.executable).resolve() != (launcher.ENV / 'Scripts/python.exe').resolve():
        raise RuntimeError('Invoke this repair with .venv-local/Scripts/python.exe')
    lock = launcher.WORK / (run_id + '.lock')
    # Never repair a running campaign, or automatically break an abandoned lock.
    with lock.open('x') as stream:
        stream.write(json.dumps({'repair': True, 'pid': os.getpid()}))
    try:
        sys.path.insert(0, str(root / 'toolkit'))
        # Import runtime explicitly from the verified extracted project.
        import importlib.util
        spec = importlib.util.spec_from_file_location('repair_runtime', root / 'toolkit/runtime.py')
        runtime = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runtime)
        run = runtime.Run(root, launcher.read(root / 'notebook-config.json'))
        folder = root / 'bundle-results/silver_fusion'
        receipt = folder / 'stage.json'
        failed = launcher.read(receipt)
        if failed['status'] != 'FAILED' or failed['bindings'] != run.binding:
            raise RuntimeError('Repair only accepts the original FAILED silver_fusion stage')
        runtime.verify_files(folder, failed.get('outputs', {}))
        if launcher.read(folder / 'features/features-exit.json')['exit_code'] != 0:
            raise RuntimeError('Feature extraction did not finish; this repair does not apply')
        log = (folder / 'train/train.log').read_text(encoding='utf-8')
        if not all(value in log for value in ['FileNotFoundError', 'classifiers.joblib', 'No such file or directory']):
            raise RuntimeError('This failure is not the reviewed missing-model-directory error')
        binding = launcher.read(root / 'local-control/environment.json')
        current = {'runner_sha256': launcher.sha(launcher.__file__), 'python': sys.executable,
                   'reuse_source': launcher.read(launcher.ENV / 'reuse-source.json'),
                   'packages': sorted((d.metadata['Name'].lower(), d.version)
                                      for d in importlib.metadata.distributions())}
        if binding != json.loads(json.dumps(current)):
            raise RuntimeError('Runner/environment changed; repair refuses identity migration')
        if launcher.sha(root / 'local-control/local_runner.py') != binding['runner_sha256']:
            raise RuntimeError('Worker source changed')
        runtime.preflight(root)  # Verify immutable packaged inputs, including all source hashes.
        base = root / 'thucnghiem/vi_rescue'
        info = launcher.read(root / runtime.SILVER / 'features.json')
        for path, key in [(base / 'data/dataset.json', 'dataset_sha256'),
                          (root / runtime.SILVER / 'protocol.json', 'protocol_sha256'),
                          (base / 'cache/embeddings.npz', 'cache_sha256')]:
            if launcher.sha(path) != info[key]:
                raise RuntimeError('Frozen feature binding changed: ' + str(path))
        target = base / 'models/classifiers.joblib'
        if target.exists():
            raise RuntimeError('Classifier already exists; refusing overwrite')
        token = str(time.time_ns())
        audit = root / 'local-control/repairs' / ('missing-model-directory-' + token)
        audit.mkdir(parents=True, exist_ok=False)
        shutil.copy2(receipt, audit / 'original-failed-stage.json')
        shutil.copy2(root / 'local-control/state.json', audit / 'original-controller-state.json')
        # Prepare both affected namespaces. No files are replaced.
        for kind in ['vi_rescue', 'vi_synthetic']:
            (root / 'thucnghiem' / kind / 'models').mkdir(parents=True, exist_ok=True)
        checkpoint = root / 'bundle-results/image_pruning/selection.json'
        original_selection_hash = launcher.sha(checkpoint)
        started = time.monotonic()
        run.call('thucnghiem/vi_rescue/train.py', [], folder / ('repair-train-' + token))
        training = launcher.read(root / runtime.SILVER / 'training.json')
        if launcher.sha(target) != training['model_sha256']:
            raise RuntimeError('Repaired classifier hash mismatch')
        if launcher.sha(checkpoint) != original_selection_hash:
            raise RuntimeError('Unrelated pruning selection changed')
        run.snapshot(root / runtime.SILVER, folder / 'outputs')
        result = {'status': 'COMPLETED', 'bindings': run.binding,
                  'seconds': failed.get('seconds', 0) + time.monotonic() - started,
                  'details': {'scope': 'AI-translated silver; same original data/protocol',
                              'repair': str(audit.relative_to(root)),
                              'reused_verified_features': True},
                  'outputs': runtime.file_manifest(folder),
                  'external_outputs': run.external_outputs('silver_fusion')}
        launcher.write(audit / 'repair.json', {
            'reason': 'ZIP omitted empty models directory; original training failed on joblib.dump',
            'repair_script_sha256': launcher.sha(__file__),
            'original_stage_sha256': launcher.sha(audit / 'original-failed-stage.json'),
            'classifier_sha256': launcher.sha(target),
            'feature_cache_sha256': info['cache_sha256'],
            'runner_and_input_code_unchanged': True,
            'prepared_output_directories': ['thucnghiem/vi_rescue/models', 'thucnghiem/vi_synthetic/models']})
        launcher.write(receipt, result)
        launcher.write(root / 'local-control/state.json',
                       {'status': 'PAUSED', 'after_stage': 'silver_fusion', 'repair': str(audit.relative_to(root))})
        launcher.safe_export(root, run_id)
        print('Repair complete; campaign PAUSED after silver_fusion. Resume with the original run command.')
    finally:
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    repair(parser.parse_args().run_id)
