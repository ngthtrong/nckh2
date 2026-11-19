"""Notebook cell template: standard library only; does not run when imported."""
BUNDLE_INDEX = None  # replaced by builder

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def live_command(command):
    child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    try:
        for line in child.stdout:
            print(line, end='', flush=True)
        if child.wait():
            raise subprocess.CalledProcessError(child.returncode, command)
    finally:
        if child.poll() is None:
            child.kill(); child.wait()

def check_member(name):
    from pathlib import PurePosixPath
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name:
        raise ValueError('Unsafe ZIP path: ' + name)
    return p

if not (3, 10) <= sys.version_info[:2] <= (3, 12):
    raise RuntimeError('Use Python 3.10-3.12 for the pinned environment')
if not RUN_ID or Path(RUN_ID).name != RUN_ID or RUN_ID in {'.', '..'}:
    raise ValueError('RUN_ID must be a single directory name')
roots = [Path(ARCHIVE_DIR)] if ARCHIVE_DIR else [Path('/kaggle/input'), Path('/content'), Path.cwd()]
archives = {}
for item in BUNDLE_INDEX:
    candidates = []
    for base in roots:
        if base.is_dir():
            direct = base / item['name']
            candidates += [direct] if direct.is_file() else list(base.glob('*/' + item['name'])) + list(base.glob('*/*/' + item['name']))
    matches = sorted({p.resolve() for p in candidates if p.stat().st_size == item['bytes'] and sha256(p) == item['sha256']})
    if not matches:
        raise FileNotFoundError('Missing or wrong SHA256: ' + item['name'] + '. Set ARCHIVE_DIR to the folder containing all ZIP files listed in BUNDLE_INDEX.')
    archives[item['package']] = matches[0]
WORK_ROOT.mkdir(parents=True, exist_ok=True)
PROJECT = WORK_ROOT / RUN_ID
marker = PROJECT / 'bundle-inputs.json'
bindings = {'archives': {x['name']: x['sha256'] for x in BUNDLE_INDEX}}
if PROJECT.exists():
    if not marker.is_file() or json.loads(marker.read_text()).get('archive_bindings') != bindings:
        raise RuntimeError('Existing project has different/incomplete inputs; choose a NEW RUN_ID')
else:
    staging = WORK_ROOT / (RUN_ID + '.extracting')
    if staging.exists():
        raise RuntimeError('Previous partial extraction preserved at ' + str(staging) + '; choose another RUN_ID')
    staging.mkdir()
    manifests = []
    try:
        for item in BUNDLE_INDEX:
            with zipfile.ZipFile(archives[item['package']]) as package:
                names = package.namelist()
                if len(set(names)) != len(names):
                    raise ValueError('Duplicate ZIP entries')
                manifest = json.loads(package.read(item['manifest']))
                if set(names) != set(manifest['files']) | {item['manifest']}:
                    raise ValueError('Undeclared ZIP contents')
                if sum(i.file_size for i in package.infolist()) > 12 * 1024**3:
                    raise ValueError('Unexpected expansion size')
                for info in package.infolist():
                    check_member(info.filename)
                    if stat.S_ISLNK(info.external_attr >> 16):
                        raise ValueError('ZIP symlink rejected')
                    target = staging / info.filename
                    if not target.resolve().is_relative_to(staging.resolve()):
                        raise ValueError('Path escapes project')
                    expected = manifest['files'].get(info.filename)
                    if target.exists():
                        if expected is None or sha256(target) != expected:
                            raise ValueError('Conflicting duplicate input: ' + info.filename)
                        continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with package.open(info) as source, target.open('xb') as destination:
                        shutil.copyfileobj(source, destination)
                    if expected is not None and sha256(target) != expected:
                        raise ValueError('Extracted file hash mismatch')
                manifests.append(manifest)
        (staging / 'bundle-inputs.json').write_text(json.dumps({'packages': manifests, 'archive_bindings': bindings}, indent=2))
        staging.rename(PROJECT)
    except BaseException:
        print('Partial extraction preserved:', staging)
        raise

# Revalidate immutable inputs once on every notebook start, including resume.
for manifest in json.loads(marker.read_text())['packages']:
    for relative, expected in manifest['files'].items():
        path = PROJECT / relative
        check_member(relative)
        if not path.resolve().is_relative_to(PROJECT.resolve()) or not path.is_file() or sha256(path) != expected:
            raise ValueError('Input changed after extraction: ' + relative)

config_path = PROJECT / 'notebook-config.json'
if config_path.exists() and json.loads(config_path.read_text()) != CONFIG:
    raise RuntimeError('CONFIG changed for this RUN_ID; choose a new RUN_ID')
config_path.write_text(json.dumps(CONFIG, indent=2))
if EXISTING_PYTHON:
    if INSTALL_DEPENDENCIES:
        raise ValueError('Set INSTALL_DEPENDENCIES=False when using an existing interpreter; keep that environment unchanged')
    PYTHON = Path(EXISTING_PYTHON)
else:
    env_dir = WORK_ROOT / 'gpu-env-torch271-cu128-v1'
    PYTHON = env_dir / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not PYTHON.is_file():
        live_command([sys.executable, '-m', 'venv', str(env_dir)])
env_receipt = PYTHON.parent.parent / 'nckh2-environment-lock.json'
requirements = PROJECT / 'toolkit/requirements-gpu.txt'
env_binding = {'requirements_sha256': sha256(requirements), 'torch': '2.7.1', 'torchvision': '0.22.1', 'cuda_wheels': 'cu128'}
if INSTALL_DEPENDENCIES:
    if not env_receipt.exists():
        live_command([str(PYTHON), '-m', 'pip', 'install', '--progress-bar', 'off', 'torch==2.7.1', 'torchvision==0.22.1', '--index-url', 'https://download.pytorch.org/whl/cu128'])
        live_command([str(PYTHON), '-m', 'pip', 'install', '--progress-bar', 'off', '-r', str(requirements)])
        live_command([str(PYTHON), '-m', 'pip', 'check'])
        env_receipt.write_text(json.dumps(env_binding, indent=2))
    elif json.loads(env_receipt.read_text()) != env_binding:
        raise RuntimeError('Environment profile changed; use a separate environment')
os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

def export_results():
    destination = WORK_ROOT / (RUN_ID + '-results.zip')
    temporary = destination.with_suffix('.zip.tmp')
    selected = [PROJECT / 'bundle-results', PROJECT / 'docs/revision-plan/outputs',
                PROJECT / 'thucnghiem/vi_rescue/models', PROJECT / 'thucnghiem/multimodal/models',
                PROJECT / 'thucnghiem/vi_synthetic/models', PROJECT / 'thucnghiem/vi_synthetic/cache/embeddings.npz',
                PROJECT / 'thucnghiem/multimodal/features', PROJECT / 'thucnghiem/vi_rescue/cache/embeddings.npz']
    input_names = {name for m in json.loads(marker.read_text())['packages'] for name in m['files']}
    retained_protocols = {'protocol.json', 't2-protocol.json', 'dataset-lock.json', 'selection-lock.json', 'data-audit.json'}
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as package:
        for directory in selected:
            paths = directory.rglob('*') if directory.is_dir() else [directory]
            for path in sorted(paths):
                if path.is_file() and (str(path.relative_to(PROJECT)) not in input_names or path.name in retained_protocols):
                    package.write(path, str(path.relative_to(PROJECT)))
        for name in ['bundle-inputs.json', 'notebook-config.json', 'toolkit/source-adaptations.json']:
            package.write(PROJECT / name, name)
    temporary.replace(destination)
    return destination

def run_stage(name):
    child = None
    try:
        command = [str(PYTHON), str(PROJECT / 'toolkit/runtime.py'), '--root', str(PROJECT),
                   '--config', str(config_path), '--stage', name]
        child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, bufsize=1, start_new_session=os.name != 'nt')
        for line in child.stdout:
            print(line, end='', flush=True)
        if child.wait():
            raise subprocess.CalledProcessError(child.returncode, command)
    finally:
        if child is not None and child.poll() is None:
            if os.name != 'nt':
                import signal
                os.killpg(child.pid, signal.SIGTERM)
            else:
                subprocess.run(['taskkill', '/PID', str(child.pid), '/T', '/F'], check=False)
            child.wait()
        print('Saved result ZIP:', export_results())

print('Project:', PROJECT)
print('Python:', PYTHON)
print('Config:', json.dumps(CONFIG, indent=2))
