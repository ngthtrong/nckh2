"""Launcher tests using fake checkpoint writers; no Torch, GPU or study data."""
from __future__ import annotations

import ast
import contextlib
import io
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import local_runner as runner


FAKE_PRUNING = '''
from pathlib import Path
def atomic_save_model(model, path, payload, device):
    Path(path).write_text('saved checkpoint')
def main():
    import sys
    folder = Path(sys.argv[sys.argv.index('--output-dir') + 1])
    atomic_save_model(None, folder / 'best.pt', {'epoch': 1}, None)
    atomic_save_model(None, folder / 'last_training.pt',
                      {'epoch': 1, 'stale_epochs': 0, 'config': {'patience': 7}}, None)
    (folder / 'finished').touch()
'''


class LocalRunnerTests(unittest.TestCase):
    def test_classifier_adapter_creates_missing_parent_directory(self):
        from build import portable_source
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'models/classifiers.joblib'
            source = ('import joblib\nfrom pathlib import Path\n'
                      'def main():\n'
                      f'    target = Path({str(target)!r})\n'
                      '    bundle = {"fixture": True}\n'
                      '    joblib.dump(bundle, target, compress=3)\n')
            patched, changes = portable_source('thucnghiem/vi_rescue/train.py', source)
            namespace = {}
            exec(compile(patched, 'fixture-classifier', 'exec'), namespace)
            namespace['main']()
            self.assertTrue(target.is_file())
            self.assertTrue(changes)

    def test_locked_latest_zip_retains_valid_separate_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            project = work / 'fixture'
            runner.write(project / 'bundle-inputs.json', {'packages': []})
            runner.write(project / 'notebook-config.json', {})
            runner.write(project / 'toolkit/source-adaptations.json', {})
            runner.write(project / 'bundle-results/checkpoint-state.json', {'epoch': 1})
            destination = work / 'fixture-results.zip'
            destination.write_bytes(b'previous ZIP held open')
            original = Path.replace

            def locked(path, target):
                if Path(target) == destination:
                    raise PermissionError('simulated Windows sharing lock')
                return original(path, target)

            with patch.object(runner, 'WORK', work), patch.object(Path, 'replace', locked), \
                    patch.object(runner.time, 'sleep'), contextlib.redirect_stdout(io.StringIO()):
                result = runner.safe_export(project, 'fixture')
            self.assertNotEqual(result, destination)
            self.assertEqual(destination.read_bytes(), b'previous ZIP held open')
            with zipfile.ZipFile(result) as archive:
                self.assertIsNone(archive.testzip())
                self.assertIn('bundle-results/checkpoint-state.json', archive.namelist())

    def test_export_io_error_does_not_abort_controller(self):
        with patch.object(runner, 'export_results', side_effect=OSError('simulated disk error')), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertIsNone(runner.safe_export(Path('.'), 'fixture'))

    def test_exact_notebook_bootstrap_extracts_and_reopens_tiny_fixture(self):
        notebook = runner.read(runner.HERE / 'dist/NCKH2_All_In_One.ipynb')
        source = next(''.join(cell['source']) for cell in notebook['cells']
                      if cell['cell_type'] == 'code' and 'def check_member(' in ''.join(cell['source']))
        tree = ast.parse(source)
        assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Name) and target.id == 'BUNDLE_INDEX'
                                  for target in node.targets))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dist = root / 'dist'
            dist.mkdir()
            payload = b'# fixture only\n'
            manifest_name = '_bundle/manifests/fixture.json'
            manifest = {'package': 'fixture', 'files': {
                'toolkit/requirements-gpu.txt': hashlib.sha256(payload).hexdigest(),
                'toolkit/source-adaptations.json': hashlib.sha256(b'{}').hexdigest()}}
            archive = dist / 'fixture.zip'
            with zipfile.ZipFile(archive, 'w') as package:
                package.writestr('toolkit/requirements-gpu.txt', payload)
                package.writestr('toolkit/source-adaptations.json', b'{}')
                package.writestr(manifest_name, json.dumps(manifest))
            index = [{'name': archive.name, 'package': 'fixture', 'bytes': archive.stat().st_size,
                      'sha256': runner.sha(archive), 'manifest': manifest_name}]
            lines = source.splitlines(keepends=True)
            lines[assignment.lineno - 1:assignment.end_lineno] = ['BUNDLE_INDEX = ' + repr(index) + '\n']
            runner.write(dist / 'NCKH2_All_In_One.ipynb',
                         {'cells': [{'cell_type': 'code', 'source': [''.join(lines)]}]})
            with patch.object(runner, 'HERE', root), patch.object(runner, 'WORK', root / 'work'), \
                    contextlib.redirect_stdout(io.StringIO()):
                first = runner.bootstrap('fixture')
                self.assertEqual((first['PROJECT'] / 'toolkit/requirements-gpu.txt').read_bytes(), payload)
                second = runner.bootstrap('fixture')
                self.assertEqual(first['PROJECT'], second['PROJECT'])
                self.assertTrue(second['export_results']().is_file())

    def test_torchvision_is_pinned_to_reused_torch(self):
        self.assertEqual(runner.torchvision_spec('2.13.0+cu130'), 'torchvision==0.28.0')
        self.assertEqual(runner.torchvision_spec('2.13.0+cu130', '0.28.0+cu130'),
                         'torchvision==0.28.0+cu130')

    def test_torch_requirement_accepts_exact_and_range_metadata(self):
        runner.check_torch_requirement(['numpy', 'torch (==2.13.0)'], '2.13.0+cu130')
        runner.check_torch_requirement(['torch>=2.13.0,<2.14'], '2.13.0+cu130')
        with self.assertRaisesRegex(RuntimeError, 'torch>=2.14.0'):
            runner.check_torch_requirement(['torch (>=2.14.0)'], '2.13.0+cu130')
        with self.assertRaisesRegex(RuntimeError, 'missing Torch requirement'):
            runner.check_torch_requirement(['numpy'], '2.13.0+cu130')

    def run_fake(self, stop, epochs):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / 'local-control').mkdir()
        if stop:
            (root / 'local-control/STOP').touch()
        (root / 'prune.py').write_text(FAKE_PRUNING, encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                runner.prune_worker(root, 'prune.py',
                                    ['--epochs', str(epochs), '--output-dir', str(root)])
            except SystemExit as exc:
                return root, exc.code
        return root, 0

    def test_pause_occurs_after_atomic_checkpoint(self):
        root, code = self.run_fake(True, 35)
        self.assertEqual(code, runner.PAUSED)
        self.assertTrue((root / 'best.pt').is_file())
        self.assertTrue((root / 'last_training.pt').is_file())
        self.assertFalse((root / 'finished').exists())
        proof = runner.read(root / 'local-control/pruning-paused.json')
        self.assertEqual(proof['sha256'], runner.sha(root / 'last_training.pt'))

    def test_without_pause_training_function_finishes(self):
        root, code = self.run_fake(False, 35)
        self.assertEqual(code, 0)
        self.assertTrue((root / 'finished').exists())

    def test_final_epoch_publishes_metrics_before_pause(self):
        root, code = self.run_fake(True, 1)
        self.assertEqual(code, 0)
        self.assertTrue((root / 'finished').exists())

    def test_bundled_pruning_has_expected_hook_and_resume(self):
        with zipfile.ZipFile(runner.HERE / 'dist/00_runtime.zip') as archive:
            source = archive.read('products/fe/tools/structured_pruning.py').decode()
        tree = ast.parse(source)
        functions = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        self.assertTrue({'main', 'atomic_save_model'} <= functions)
        self.assertIn('"--resume"', source)
        self.assertIn('"last_training.pt"', source)

    def test_run_id_cannot_escape_work_directory(self):
        for value in ('../escape', '..', 'x/y', 'D:\\escape'):
            with self.assertRaises(ValueError):
                runner.project_path(value)

    def test_stage_pause_resume_and_completed_ratio_skip(self):
        import runtime
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner.write(root / 'bundle-inputs.json', {})
            runner.write(root / 'notebook-config.json', {})
            calls = []
            pause_once = [True]

            def fake_call(instance, script, args, folder, **kwargs):
                process_logs = Path(folder)
                folder = Path(args[args.index('--output-dir') + 1])
                self.assertNotEqual(process_logs, folder)
                folder.mkdir(parents=True, exist_ok=True)
                calls.append((folder.name, list(map(str, args))))
                checkpoint = folder / 'last_training.pt'
                checkpoint.write_text('fake complete optimizer checkpoint')
                if pause_once[0]:
                    pause_once[0] = False
                    runner.write(root / 'local-control/pruning-paused.json',
                                 {'checkpoint': str(checkpoint), 'sha256': runner.sha(checkpoint)})
                    raise RuntimeError('simulated child pause')
                (folder / 'flood_mobilenetv3_large_structured_best.pt').write_text('fake best')
                runner.write(folder / 'metrics.json',
                             {'final_test': None, 'best_validation': {'macro_f1': .5, 'accuracy': .6}})

            with patch.object(runtime.Run, 'call', fake_call), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as paused:
                    runner.stage_worker(root, 'image_pruning')
                self.assertEqual(paused.exception.code, runner.PAUSED)
                receipt = root / 'bundle-results/image_pruning/stage.json'
                self.assertEqual(runner.read(receipt)['status'], 'PAUSED')
                runner.stage_worker(root, 'image_pruning')
                self.assertEqual(runner.read(receipt)['status'], 'COMPLETED')
                self.assertIn('--resume', calls[1][1])
                self.assertTrue(list((root / 'local-control').glob('image_pruning-paused-*.json')))
                count = len(calls)
                runner.stage_worker(root, 'image_pruning')
                self.assertEqual(len(calls), count)


if __name__ == '__main__':
    unittest.main()
