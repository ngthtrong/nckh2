"""Đóng gói ảnh/scenario theo gold run cho app Android; kiểm tra CSV/hash, không chạy AI."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import shutil
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MODEL = ROOT / 'products/fe/model/Edge Ai/seed1024/export/pruning_st/flood_mobilenetv3_large.pte'
spec = importlib.util.spec_from_file_location('mobile_web_inputs', ROOT / 'thuc_nghiem_nq/experiment_e2e/e2e_system.py')
web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(web)
MAGIC = b'RHE1'
STAGES = ['online', 'offline_recovery', 'adaptive_300', 'adaptive_20', 'no_gps', 'feedback']


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_package(data: bytes):
    if len(data) < 8 or data[:4] != MAGIC:
        raise ValueError('Không phải gói RHE1')
    length = struct.unpack('>I', data[4:8])[0]
    if not 0 < length <= min(len(data) - 8, 1024 * 1024):
        raise ValueError('Manifest không hợp lệ')
    manifest = json.loads(data[8:8 + length])
    image = data[8 + length:]
    if manifest['schemaVersion'] not in (1, 2) or len(image) != manifest['image']['length'] or sha(image) != manifest['image']['sha256']:
        raise ValueError('Ảnh/gói sai hash hoặc độ dài')
    return manifest, image


def build_package(run: int, session_id: str | None, output: Path) -> dict:
    if session_id is not None and not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', session_id):
        raise ValueError('Session ID không hợp lệ')
    inputs = web.select_inputs(run, web.CSV_PATH, None)
    # Snapshot only inference inputs; ground truth is never packaged for the app.
    inputs = dict(inputs)
    snapshot = output.parent / 'inputs' / inputs['gold_name']
    snapshot.mkdir(parents=True, exist_ok=True)
    for key in ['gold_input', 'gold_manifest', 'csv', 'image']:
        source = Path(inputs[key])
        target = snapshot / source.name
        if sha(source.read_bytes()) != inputs['sha256'][key]:
            raise ValueError('Dữ liệu nguồn đã thay đổi: ' + key)
        shutil.copy2(source, target)
        inputs[key] = str(target.resolve())
    image = Path(inputs['image']).read_bytes()
    manifest = {
        'schemaVersion': 2 if session_id is None else 1, 'goldRun': inputs['gold_name'],
        'goldInputSha256': inputs['sha256']['gold_input'], 'goldReportCount': inputs['report_count'],
        'splitCsvSha256': inputs['sha256']['csv'], 'imageSelectionSha256': inputs['sha256']['image_selection'],
        'image': {'relativePath': inputs['image_relative_path'], 'label': inputs['image_label'],
                  'length': len(image), 'sha256': sha(image)},
        'model': {'runtime': 'pte', 'seed': 1024, 'variant': 'pruning', 'sha256': sha(MODEL.read_bytes())},
        'stages': STAGES,
    }
    if session_id is not None:  # Reading archived v1 fixtures remains supported.
        manifest['sessionId'] = session_id
    header = json.dumps(manifest, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    data = MAGIC + struct.pack('>I', len(header)) + header + image
    read_package(data)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    return {'manifest': manifest, 'sha256': sha(data), 'path': str(output.resolve()), 'inputs': inputs}


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed-run', type=int, choices=range(1, 81), required=True)
    parser.add_argument('--benchmark', default='preview')
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    result = build_package(options.seed_run, options.benchmark, options.output)
    print(json.dumps({k: v for k, v in result.items() if k != 'inputs'}, ensure_ascii=False, indent=2))
