"""Prepare reusable inputs for a normal Flutter build; only Python stdlib required."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import tempfile

from build_package import MODEL, ROOT, build_package, read_package, sha

ASSETS = ROOT / 'products/fe/app/assets'


def prepare_assets(assets: Path = ASSETS):
    destination = assets / 'benchmarks/mobile'
    destination.mkdir(parents=True, exist_ok=True)
    models = assets / 'models'
    models.mkdir(parents=True, exist_ok=True)
    model_manifest = json.loads((MODEL.parent/'model_manifest.json').read_text(encoding='utf-8'))
    if model_manifest['pte_sha256'] != sha(MODEL.read_bytes()):
        raise ValueError('Model seed1024 không khớp manifest nguồn')
    shutil.copy2(MODEL, models/'model.pte')
    shutil.copy2(MODEL.parent/'model_manifest.json', models/'model_manifest.json')
    runs = []
    with tempfile.TemporaryDirectory() as temp:
        for run in (1, 2):
            name = f'run_{run:03d}'
            info = build_package(run, None, Path(temp)/name/'package.rhe')
            filename = name + '.rhe'
            shutil.copy2(info['path'], destination/filename)
            inputs = []
            for key in ('gold_input', 'gold_manifest'):
                source = Path(info['inputs'][key])
                target = name + '_' + source.name
                shutil.copy2(source, destination/target)
                inputs.append({'file': target, 'sha256': sha(source.read_bytes())})
            runs.append({'goldRun': name, 'file': filename, 'packageSha256': info['sha256'],
                         'image': info['manifest']['image'], 'model': info['manifest']['model'],
                         'inputs': inputs})
    catalog = {'schemaVersion': 1, 'runs': runs}
    (destination/'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return verify_assets(assets)


def verify_assets(assets: Path = ASSETS):
    root = assets/'benchmarks/mobile'
    catalog = json.loads((root/'catalog.json').read_text(encoding='utf-8'))
    if catalog.get('schemaVersion') != 1 or [r['goldRun'] for r in catalog['runs']] != ['run_001', 'run_002']:
        raise ValueError('Gói assets cần đủ run_001 và run_002')
    model_hash = sha((assets/'models/model.pte').read_bytes())
    if json.loads((assets/'models/model_manifest.json').read_text(encoding='utf-8'))['pte_sha256'] != model_hash:
        raise ValueError('Model asset không khớp manifest')
    for item in catalog['runs']:
        if item['file'] != item['goldRun']+'.rhe':
            raise ValueError('Tên file run không hợp lệ')
        data = (root/item['file']).read_bytes()
        fixture, _ = read_package(data)
        if (sha(data) != item['packageSha256'] or fixture['schemaVersion'] != 2
                or 'sessionId' in fixture or fixture['goldRun'] != item['goldRun']
                or fixture['image'] != item['image'] or fixture['model'] != item['model']
                or fixture['model'] != {'runtime': 'pte', 'seed': 1024, 'variant': 'pruning', 'sha256': model_hash}):
            raise ValueError('Gói run/model bị thay đổi; chạy lại prepare_assets.py')
        for source in item['inputs']:
            if Path(source['file']).name != source['file'] or sha((root/source['file']).read_bytes()) != source['sha256']:
                raise ValueError('Đầu vào gold bị thay đổi')
        gold = next(i for i in item['inputs'] if i['file'].endswith('_algorithm_input.json'))
        origin = next(i for i in item['inputs'] if i['file'].endswith('_run_manifest.json'))
        if gold['sha256'] != fixture['goldInputSha256'] or json.loads((root/origin['file']).read_text(encoding='utf-8'))['dataset_id'] != item['goldRun']:
            raise ValueError('Nguồn gold không khớp gói')
    return catalog


def benchmark_package(run: int, output: Path, assets: Path = ASSETS):
    """Snapshot the exact APK inputs without rebuilding or inserting timestamps."""
    catalog = verify_assets(assets)
    item = next((r for r in catalog['runs'] if r['goldRun'] == f'run_{run:03d}'), None)
    if item is None:
        raise ValueError('Benchmark mobile chỉ có run 1 và 2')
    root = assets/'benchmarks/mobile'
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root/item['file'], output)
    for source in item['inputs']:
        destination = output.parent/'inputs'/item['goldRun']/source['file']
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root/source['file'], destination)
    fixture, _ = read_package(output.read_bytes())
    return {'manifest': fixture, 'sha256': item['packageSha256'], 'path': str(output.resolve()),
            'inputs': {'gold_name': item['goldRun'], 'report_count': fixture['goldReportCount'],
                       'gold_input_sha256': fixture['goldInputSha256']}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify assets without changing them')
    options = parser.parse_args()
    result = verify_assets() if options.check else prepare_assets()
    print('Assets ready: ' + ', '.join(r['goldRun'] for r in result['runs']) + '; PTE seed1024 pruning')
