"""Local Windows launcher. Nothing trains unless the user invokes `run`."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import runpy
import stat
import subprocess
import sys
import time
import tempfile
import venv
import zipfile

HERE = Path(__file__).resolve().parent
ENV = HERE / '.venv-local'
WORK = HERE / 'local-work'
PAUSED = 75


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def command(args):
    print(subprocess.list2cmdline(list(map(str, args))), flush=True)
    subprocess.run(list(map(str, args)), check=True, env={**os.environ, 'PYTHONUTF8': '1'})


def torchvision_spec(torch_version, override=None):
    if override:
        return 'torchvision==' + override
    # Verified against the cu130 Windows cp311 wheel metadata: 0.28.0 -> 2.13.0.
    # Newest torchvision in the index may target a newer Torch than the reused one.
    if torch_version.split('+')[0] == '2.13.0':
        return 'torchvision==0.28.0'
    raise RuntimeError('No verified torchvision mapping for torch ' + torch_version
                       + '; specify --torchvision-version explicitly')


def check_torch_requirement(requirements, torch_version):
    from packaging.requirements import Requirement
    dependencies = [Requirement(item) for item in requirements]
    active = [item for item in dependencies if item.name.lower() == 'torch'
              and (item.marker is None or item.marker.evaluate())]
    if not active or not all(item.specifier.contains(torch_version) for item in active):
        expected = ', '.join(str(item) for item in active) or 'missing Torch requirement'
        raise RuntimeError(f'torchvision requires {expected}; existing torch is {torch_version}. '
                           'Nothing replaced. Supply --torchvision-version with a compatible CUDA wheel.')


def setup(args):
    """Reuse external site-packages; install overrides only into our own venv."""
    if not (3, 10) <= sys.version_info[:2] <= (3, 12):
        raise RuntimeError('Python 3.10-3.12 required')
    torch_dist = importlib.metadata.distribution('torch')
    torch_version = torch_dist.version
    base_site = str(torch_dist.locate_file('').resolve())
    if '+cu' not in torch_version:
        raise RuntimeError('Invoke setup with the existing CUDA-enabled CT553H Python')
    if not (ENV / 'Scripts/python.exe').exists():
        venv.EnvBuilder(with_pip=True).create(ENV)
    py = ENV / 'Scripts/python.exe'
    site = ENV / 'Lib/site-packages'
    binding = {'base_python': sys.executable, 'base_site': base_site, 'torch': torch_version}
    receipt = ENV / 'reuse-source.json'
    if receipt.exists() and read(receipt) != binding:
        raise RuntimeError('Existing local environment belongs to a different base environment')
    (site / 'reuse-ct553h.pth').write_text(base_site + '\n', encoding='utf-8')
    write(receipt, binding)
    command([py, '-c', 'import importlib.metadata as m; '
             f'assert m.version("torch") == {torch_version!r}, "Shared torch not visible"'])
    constraint = ENV / 'keep-torch.txt'
    constraint.write_text('torch==' + torch_version + '\n', encoding='utf-8')
    # Resolve torchvision alone: never let pip download a replacement torch/CUDA.
    report = ENV / 'torchvision-resolution.json'
    index = 'https://download.pytorch.org/whl/' + torch_version.split('+', 1)[1]
    spec = torchvision_spec(torch_version, args.torchvision_version)
    command([py, '-m', 'pip', 'install', '--dry-run', '--ignore-installed', '--no-deps',
             '--report', report, '--index-url', index, spec])
    candidate = read(report)['install'][0]
    requirements = candidate['metadata'].get('requires_dist', [])
    check_torch_requirement(requirements, torch_version)
    command([py, '-m', 'pip', 'install', '--no-deps', candidate['download_info']['url']])
    # All dependency changes are local; the torch constraint forbids replacing it.
    command([py, '-m', 'pip', 'install', '-c', constraint, '-r', HERE / 'requirements-gpu.txt'])
    command([py, '-m', 'pip', 'check'])
    print('Setup finished. Run doctor before training. CT553H was not modified.')


def doctor():
    import torch
    import torchvision
    from torchvision.ops import nms
    source = read(ENV / 'reuse-source.json')
    if not Path(torch.__file__).resolve().is_relative_to(Path(source['base_site']).resolve()):
        raise RuntimeError('Torch must be reused from the recorded CT553H environment')
    if torch.__version__ != source['torch']:
        raise RuntimeError('Shared Torch changed; prepare a new environment/run')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable; refusing CPU fallback')
    x = torch.ones(4, device='cuda')
    assert (x * x).sum().item() == 4
    nms(torch.tensor([[0., 0., 1., 1.]]), torch.tensor([1.]), .5)
    for line in (HERE / 'requirements-gpu.txt').read_text().splitlines():
        if line and not line.startswith('#'):
            name, expected = line.split('==')
            actual = importlib.metadata.version(name)
            if actual != expected:
                raise RuntimeError(f'{name}: expected {expected}, found {actual}')
    print(json.dumps({'torch': torch.__version__, 'torchvision': torchvision.__version__,
                      'cuda': torch.version.cuda, 'gpu': torch.cuda.get_device_name(0),
                      'torch_file': torch.__file__, 'python': sys.executable}, indent=2))


def project_path(run_id):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', run_id) or run_id in {'.', '..'}:
        raise ValueError('RUN_ID must be a simple directory name')
    return WORK / run_id


def export_results(project, run_id):
    """Publish a ZIP, retaining a uniquely named snapshot if Windows locks the latest ZIP."""
    project = Path(project)
    destination = WORK / (run_id + '-results.zip')
    fd, name = tempfile.mkstemp(prefix=run_id + '-results-', suffix='.zip.partial', dir=WORK)
    os.close(fd)
    temporary = Path(name)
    selected = ['bundle-results', 'docs/revision-plan/outputs', 'thucnghiem/vi_rescue/models',
                'thucnghiem/multimodal/models', 'thucnghiem/vi_synthetic/models',
                'thucnghiem/vi_synthetic/cache/embeddings.npz', 'thucnghiem/multimodal/features',
                'thucnghiem/vi_rescue/cache/embeddings.npz', 'local-control']
    inputs = {name for item in read(project / 'bundle-inputs.json')['packages'] for name in item['files']}
    protocols = {'protocol.json', 't2-protocol.json', 'dataset-lock.json', 'selection-lock.json', 'data-audit.json'}
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as package:
        for relative in selected:
            base = project / relative
            paths = sorted(base.rglob('*')) if base.is_dir() else [base]
            for path in paths:
                key = path.relative_to(project).as_posix()
                if path.is_file() and (key not in inputs or path.name in protocols):
                    package.write(path, key)
        for relative in ['bundle-inputs.json', 'notebook-config.json', 'toolkit/source-adaptations.json']:
            package.write(project / relative, relative)
    for attempt in range(4):
        try:
            temporary.replace(destination)
            return destination
        except PermissionError:
            if attempt < 3:
                time.sleep(.25)
    # A viewer/antivirus can hold the previous latest ZIP open on Windows.
    # The completed new ZIP remains independently usable, without touching that file.
    snapshot = temporary.with_suffix('')
    try:
        temporary.replace(snapshot)
    except PermissionError:
        snapshot = temporary
    print('Latest result ZIP is locked; saved a separate snapshot:', snapshot, flush=True)
    return snapshot


def safe_export(project, run_id):
    try:
        result = export_results(project, run_id)
        print('Saved result ZIP:', result, flush=True)
        return result
    except OSError as exc:
        print('WARNING: ZIP export failed; project/checkpoints remain on disk:', exc, flush=True)
        return None


def bootstrap(run_id):
    # Reuse the shipped notebook setup, with package installation disabled.
    notebook = read(HERE / 'dist/NCKH2_All_In_One.ipynb')
    code = next(''.join(c['source']) for c in notebook['cells']
                if c['cell_type'] == 'code' and 'def check_member(' in ''.join(c['source']))
    sys.path.insert(0, str(HERE))
    import runtime
    config = dict(runtime.DEFAULT)
    namespace = dict(Path=Path, sys=sys, os=os, json=json, time=time,
                     hashlib=hashlib, subprocess=subprocess, stat=stat)
    import shutil
    import zipfile
    namespace.update(shutil=shutil, zipfile=zipfile, ARCHIVE_DIR=HERE / 'dist',
                     WORK_ROOT=WORK, RUN_ID=run_id, CONFIG=config,
                     INSTALL_DEPENDENCIES=False, EXISTING_PYTHON=sys.executable)
    exec(compile(code, 'shipped-notebook-bootstrap', 'exec'), namespace)
    return namespace


def prune_worker(root, script, script_args):
    """Hook the existing atomic checkpoint writer, without editing bundled code."""
    root = Path(root)
    sys.path.insert(0, str(root / 'products/fe/tools'))
    sys.path.insert(0, str(root / 'toolkit'))
    module = runpy.run_path(str(root / script), run_name='local_pruning_module')
    scope = module['main'].__globals__
    original = scope['atomic_save_model']

    def save(model, path, payload, device):
        original(model, path, payload, device)
        # Let a naturally finished ratio publish its final metrics before pausing.
        epochs = int(script_args[script_args.index('--epochs') + 1]) if '--epochs' in script_args else 35
        finished = (payload.get('epoch', 0) >= epochs or
                    payload.get('stale_epochs', 0) >= int(payload.get('config', {}).get('patience', 7)))
        if (Path(path).name == 'last_training.pt' and not finished
                and (root / 'local-control/STOP').exists()):
            write(root / 'local-control/pruning-paused.json',
                  {'checkpoint': str(path), 'epoch': payload['epoch'], 'sha256': sha(path)})
            print('PAUSED after atomic epoch checkpoint:', path, flush=True)
            raise SystemExit(PAUSED)

    scope['atomic_save_model'] = save
    sys.argv = [str(root / script), *script_args]
    module['main']()


def stage_worker(root, stage):
    root = Path(root).resolve()
    sys.path.insert(0, str(root / 'toolkit'))
    import runtime

    class LocalRun(runtime.Run):
        def call(self, script, args, folder, **kwargs):
            if not str(script).endswith('/structured_pruning.py'):
                return super().call(script, args, folder, **kwargs)
            if (root / 'local-control/STOP').exists():
                write(root / 'local-control/pruning-paused.json', {'kind': 'ratio_boundary'})
                raise RuntimeError('User requested pause at pruning ratio boundary')
            folder = Path(folder)
            record = root / 'local-control' / (folder.name + '-completed.json')
            if record.exists():
                old = read(record)
                if old['bindings'] != self.binding:
                    raise ValueError('Pruning ratio binding changed')
                runtime.verify_files(folder, old['files'])
                print('SKIP verified pruning ratio', folder.name, flush=True)
                return
            resume = folder / 'last_training.pt'
            if resume.exists():
                args = [*args, '--resume', resume]
            # Runtime still writes its usual command/exit/log receipts.
            # Keep process logs outside the trainer's output directory: the
            # trainer correctly rejects a nonempty directory for a fresh run.
            process_logs = folder.parent / (folder.name + '-process')
            super().call('local-control/local_runner.py',
                         ['prune-worker', '--root', root, '--script', script, '--', *args], process_logs, **kwargs)
            write(record, {'bindings': self.binding, 'files': runtime.file_manifest(folder)})

    run = LocalRun(root, read(root / 'notebook-config.json'))
    receipt = run.out / stage / 'stage.json'
    if receipt.exists() and read(receipt)['status'] == 'PAUSED':
        old = read(receipt)
        if old['bindings'] != run.binding:
            raise RuntimeError('Paused stage binding changed')
        runtime.verify_files(run.out / stage, old.get('outputs', {}))
        archived = root / 'local-control' / f'{stage}-paused-{time.time_ns()}.json'
        receipt.replace(archived)
    pause_marker = root / 'local-control/pruning-paused.json'
    pause_marker.unlink(missing_ok=True)
    try:
        run.stage(stage)
    except Exception:
        if stage != 'image_pruning' or not pause_marker.exists():
            raise
        proof = read(pause_marker)
        if 'checkpoint' in proof and sha(proof['checkpoint']) != proof['sha256']:
            raise RuntimeError('Paused checkpoint hash mismatch')
        state = read(receipt)
        state['status'] = 'PAUSED'
        state['pause_checkpoint'] = proof
        write(receipt, state)
        raise SystemExit(PAUSED)


def run(args):
    if Path(sys.executable).resolve() != (ENV / 'Scripts/python.exe').resolve():
        raise RuntimeError('Use .venv-local/Scripts/python.exe for run')
    root = project_path(args.run_id)
    WORK.mkdir(exist_ok=True)
    lock = WORK / (args.run_id + '.lock')
    # Exclusive lock also protects extraction/configuration from concurrent runs.
    with lock.open('x', encoding='utf-8') as stream:
        json.dump({'pid': os.getpid(), 'started': time.time()}, stream)
    ns = None
    try:
        doctor()
        ns = bootstrap(args.run_id)
        control = root / 'local-control'
        control.mkdir(exist_ok=True)
        fingerprint = {'runner_sha256': sha(__file__), 'python': sys.executable,
                       'reuse_source': read(ENV / 'reuse-source.json'),
                       'packages': sorted((d.metadata['Name'].lower(), d.version)
                                          for d in importlib.metadata.distributions())}
        binding = control / 'environment.json'
        if binding.exists() and read(binding) != json.loads(json.dumps(fingerprint)):
            raise RuntimeError('Runner/environment changed. Use a new RUN_ID.')
        write(binding, fingerprint)
        import shutil
        shutil.copy2(__file__, control / 'local_runner.py')
        (control / 'STOP').unlink(missing_ok=True)
        sys.path.insert(0, str(HERE))
        import runtime
        for stage in runtime.STAGES:
            if (control / 'STOP').exists():
                print('Paused at stage boundary. Run the same command to continue.')
                return
            write(control / 'state.json', {'status': 'RUNNING', 'stage': stage, 'pid': os.getpid()})
            result = subprocess.run([sys.executable, '-u', str(control / 'local_runner.py'),
                                     'stage-worker', '--root', str(root), '--stage', stage],
                                    env={**os.environ, 'PYTHONUTF8': '1',
                                         'CUBLAS_WORKSPACE_CONFIG': ':4096:8',
                                         'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1'})
            if result.returncode == PAUSED:
                write(control / 'state.json', {'status': 'PAUSED', 'stage': stage})
                safe_export(root, args.run_id)
                return
            if result.returncode:
                write(control / 'state.json', {'status': 'FAILED', 'stage': stage})
                raise RuntimeError(f'Stage {stage} failed. Inspect logs; no automatic retry.')
            if (control / 'STOP').exists():
                write(control / 'state.json', {'status': 'PAUSED', 'after_stage': stage})
                safe_export(root, args.run_id)
                return
            write(control / 'state.json', {'status': 'STAGE_COMPLETED', 'stage': stage})
            safe_export(root, args.run_id)
        write(control / 'state.json', {'status': 'COMPLETED'})
    finally:
        try:
            if ns is not None:
                safe_export(root, args.run_id)
        finally:
            lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['setup', 'doctor', 'run', 'pause', 'status', 'stage-worker', 'prune-worker'])
    parser.add_argument('--run-id', default='local-20261110-01')
    parser.add_argument('--torchvision-version')
    parser.add_argument('--root', type=Path)
    parser.add_argument('--stage')
    parser.add_argument('--script')
    args, extra = parser.parse_known_args()
    if args.action == 'prune-worker':
        return prune_worker(args.root, args.script, extra[1:] if extra[:1] == ['--'] else extra)
    if extra:
        parser.error('Unknown arguments: ' + ' '.join(extra))
    if args.action == 'setup':
        return setup(args)
    if args.action == 'doctor':
        return doctor()
    if args.action == 'stage-worker':
        return stage_worker(args.root, args.stage)
    if args.action == 'run':
        return run(args)
    root = project_path(args.run_id)
    if args.action == 'pause':
        if not (WORK / (args.run_id + '.lock')).exists() or not (root / 'local-control').is_dir():
            raise RuntimeError('No initialized running session for this RUN_ID')
        (root / 'local-control/STOP').touch()
        print('Pause requested. Pruning saves at epoch end; other stages finish before stopping.')
    else:
        state = root / 'local-control/state.json'
        print(json.dumps(read(state), indent=2) if state.exists() else 'NOT STARTED')
        lock = WORK / (args.run_id + '.lock')
        print('Runner lock:', read(lock) if lock.exists() else 'none')


if __name__ == '__main__':
    main()
