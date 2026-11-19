#!/usr/bin/env python3
"""Read repository evidence; write only a new audit snapshot inside this folder.

Run with report/build/visual-env/bin/python for optional Pillow image headers.
Never runs training, inference, generators, export_results, build, or git mutation.
"""
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
import csv
import hashlib
import json
import math
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).rstrip('\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return list(csv.DictReader(path.open(encoding='utf-8-sig', newline='')))


def main():
    dest = OUT / (sys.argv[1] if len(sys.argv) > 1 else 'audit-snapshot.json')
    if dest.parent != OUT or dest.exists():
        raise SystemExit('Choose a new filename in evidence/; existing snapshots are immutable.')
    d = {'checked_at': datetime.now(ZoneInfo('Asia/Taipei')).isoformat(),
         'scope': 'read-only checks of saved artifacts; no new model results',
         'head': git('rev-parse', 'HEAD'), 'branch': git('branch', '--show-current'),
         'initial_git_status': git('status', '--short'), 'refs': [], 'notebooks': []}
    tracked = git('ls-files').splitlines()
    # Protect the existing dirty work, including deletions; filenames have no newline here.
    dirty = git('diff', '--name-only', 'HEAD').splitlines()
    d['preexisting_dirty_files'] = {p: sha(ROOT / p) if (ROOT / p).is_file() else None for p in dirty}
    d['preexisting_untracked_files'] = {p: sha(ROOT / p) for p in git('ls-files', '--others', '--exclude-standard').splitlines()
                                      if not p.startswith('docs/revision-plan/') and (ROOT / p).is_file()}
    for ref in git('for-each-ref', '--format=%(refname:short)', 'refs/heads', 'refs/remotes/origin').splitlines():
        tree = git('ls-tree', '-r', '--name-only', ref).splitlines()
        p = subprocess.run(['git', 'grep', '-l', '-i', '-E',
                            'DistilBERT|AutoTokenizer|AutoModelForSequenceClassification|PhoBERT|UIT.VSMEC|from transformers',
                            ref, '--', '*.py', '*.ipynb', '*.dart'], cwd=ROOT, text=True, capture_output=True)
        d['refs'].append({'ref': ref, 'commit': git('rev-parse', ref), 'files': len(tree),
                          'nlp_code_hits': [x for x in p.stdout.splitlines() if '/.agents/' not in x],
                          'search_exit': p.returncode})
    for name in tracked:
        p = ROOT / name
        if p.suffix == '.ipynb' and p.exists():
            nb = json.loads(p.read_text()); cells = nb.get('cells', [])
            outputs = [o for c in cells for o in c.get('outputs', [])]
            d['notebooks'].append({'path': name, 'sha256': sha(p), 'cells': len(cells),
                                   'outputs': len(outputs), 'errors': [o.get('ename') for o in outputs if o.get('output_type') == 'error']})
    prov = json.loads((ROOT / 'report/generated/provenance.json').read_text())
    d['report_source_hashes'] = {p: {'expected': h, 'actual': sha(ROOT / p) if (ROOT / p).is_file() else None}
                                for p, h in prov['sources_sha256'].items()}
    d['saved_prediction_audits'] = prov['prediction_audits']
    split_path = ROOT / 'products/fe/model/Edge Ai/split_train_val_test_mobilenetv3_large.csv'
    split = rows(split_path)
    groups = {k: defaultdict(set) for k in ['md5', 'perceptual_group', 'split_group']}
    image_meta = []; missing = []; changed = []
    try:
        from PIL import Image
    except ImportError:
        Image = None
    for r in split:
        p = ROOT / 'products/fe/model/Dataset_Flood' / r['relative_path']
        for k in groups:
            if r[k]: groups[k][r[k]].add(r['split'])
        if not p.is_file():
            missing.append(r['relative_path']); continue
        if hashlib.md5(p.read_bytes()).hexdigest() != r['md5']: changed.append(r['relative_path'])
        if Image:
            with Image.open(p) as im:
                image_meta.append({'relative_path': r['relative_path'], 'split': r['split'], 'label': r['label'],
                                   'width': im.width, 'height': im.height, 'format': im.format, 'mode': im.mode,
                                   'bytes': p.stat().st_size})
    d['images'] = {'split_sha256': sha(split_path), 'count': len(split),
                   'split_counts': dict(Counter(r['split'] for r in split)),
                   'missing': missing, 'md5_mismatch': changed,
                   'cross_split_groups': {k: sum(len(v) > 1 for v in gs.values()) for k, gs in groups.items()},
                   'header_only': True, 'pillow_available': Image is not None,
                   'formats': dict(Counter(r['format'] for r in image_meta)),
                   'modes': dict(Counter(r['mode'] for r in image_meta)), 'headers': image_meta}
    phone = []; split_truth = {hashlib.sha1(r['relative_path'].replace('\\', '/').encode()).hexdigest()[:12]: r['label']
                               for r in split if r['split'] == 'test'}
    for seed in [159, 1024]:
        for p in sorted((ROOT / f'products/fe/reports/seed{seed}/mobile').rglob('*.json')):
            ob = json.loads(p.read_text()); pred = ob.get('predictions', [])
            truth = {r['id']: r['truth'] for r in pred}; labels = ['low', 'medium', 'high', 'non_flood']
            cm = [[sum(r['truth'] == a and r['prediction'] == b for r in pred) for b in labels] for a in labels]
            acc = sum(cm[i][i] for i in range(4)) / len(pred)
            f1 = sum(2*cm[i][i]/(sum(cm[i])+sum(row[i] for row in cm)) for i in range(4))/4
            phone.append({'path': str(p.relative_to(ROOT)), 'sha256': sha(p), 'seed': seed,
                          'runtime': ob['runtime'], 'complete': ob['complete'], 'samples': len(pred),
                          'failed': ob['failedSamples'], 'truth_ids_match': truth == split_truth,
                          'accuracy_recomputed': acc, 'macro_f1_recomputed': f1,
                          'metrics_match': math.isclose(acc, ob['accuracy'], abs_tol=1e-10) and math.isclose(f1, ob['macroF1'], abs_tol=1e-10),
                          'provenance': ob['provenance']})
    d['phone_runs'] = phone
    summary = rows(ROOT / 'report/generated/phone-benchmarks/summary.csv')
    d['phone_summary'] = {'rows': len(summary), 'sources_match_hash': all(sha(ROOT / r['source_json']) == r['source_sha256'] for r in summary)}
    manifests = {}
    for p in [ROOT/'thucnghiem/results/rq1_results/manifest.json', ROOT/'thucnghiem/results/rq1_results_v2/full/manifest.json',
              ROOT/'thucnghiem/results/rq2_results/rq2_artifact_sha256.json',ROOT/'thucnghiem/results/rq3_results/rq3_artifact_sha256.json']:
        ob=json.loads(p.read_text()); hs=ob.get('artifacts',ob); checked=[]; skipped=[]
        for name,h in hs.items():
            if not isinstance(h,str) or len(h)!=64: skipped.append(name);continue
            q=p.parent/name; checked.append({'path':name,'exists':q.is_file(),'match':q.is_file() and sha(q)==h})
        manifests[str(p.relative_to(ROOT))]={'checks':checked,'metadata_not_hash_fields':skipped}
    d['rq_manifests']=manifests
    d['full_rq_verifier_not_run']={'hardcoded_results':'src/results, absent on current tree',
                                  'required_numpy':'2.5.1','available_visual_env_numpy':'2.5.3',
                                  'reason':'Avoid mutate source or install environment in audit; byte hash checks do not replay statistical tests.'}
    weak=ROOT/'thuc_nghiem_nq/experiment_weak_network/results/20261005-102040/weak_network.csv'
    wr=rows(weak); d['weak_network']={'path':str(weak.relative_to(ROOT)),'sha256':sha(weak),'rows':len(wr),'columns':list(wr[0])}
    d['pdfs']={}
    for name in ['report/main.pdf','report/build/content/content.pdf','report/build/content-twoside/content.pdf']:
        p=ROOT/name;d['pdfs'][name]={'sha256':sha(p),'pdfinfo':subprocess.check_output(['pdfinfo',str(p)],text=True)}
    d['float_checks']=[]
    for build in ['build/content','build/content-twoside']:
        p=subprocess.run([sys.executable,'report/scripts/check_float_references.py','--build-dir',build],cwd=ROOT,text=True,capture_output=True)
        d['float_checks'].append({'build':build,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    dest.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'snapshot':str(dest.relative_to(ROOT)),'refs':len(d['refs']),'images':len(split),'phone_runs':len(phone),
                      'phone_metrics_match':all(x['metrics_match'] for x in phone),'phone_truth_ids_match':all(x['truth_ids_match'] for x in phone),
                      'manifest_files':sum(len(x['checks']) for x in manifests.values()),
                      'manifest_failures':sum(not y['match'] for x in manifests.values() for y in x['checks']),
                      'weak_network_rows':len(wr)},ensure_ascii=False))


if __name__ == '__main__':
    main()
