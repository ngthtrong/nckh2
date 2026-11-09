"""Fixed-model CPU screening. Clean parity must pass before any corruption run.

Never trains, exports models, changes source data, or runs Android. Re-running a
stage refuses to overwrite its predictions. Protocol and every input are hashed.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import platform
import subprocess
import sys
import time

import numpy as np
import onnxruntime as ort
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'products/fe/tools'))
from quantize_model import preprocess, load_splits

SPLIT = ROOT / 'products/fe/model/Edge Ai/split_train_val_test_mobilenetv3_large.csv'
DATA = ROOT / 'products/fe/model/Dataset_Flood'
MODEL = ROOT / 'products/fe/app/assets/models/model.onnx'
CONFIG = ROOT / 'products/fe/model/Edge Ai/seed1024/config_mobilenetv3_large.json'
HISTORY = ROOT / 'products/fe/reports/seed1024/prunning_st'
CLASSES = ['low', 'medium', 'high', 'non_flood']
ORDINAL = np.array([1, 2, 3, 0])
CONDITIONS = ['clean', 'jpeg_q50', 'jpeg_q20', 'short_edge_128',
              'short_edge_64', 'blur_sigma_1', 'blur_sigma_2',
              'exposure_0.7', 'exposure_0.4']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def write_csv(name, rows):
    with (OUT / name).open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def setup():
    config = json.loads(CONFIG.read_text())
    summary = json.loads((HISTORY / 'summary.json').read_text())
    assert config['class_order'] == CLASSES
    assert json.loads((ROOT / 'products/fe/app/assets/labels.json').read_text()) == CLASSES
    assert config['image_size'] == 256 and config['letterbox_fill'] == [124, 116, 104]
    assert sha(CONFIG) == summary['metadata']['config_sha256']
    assert sha(SPLIT) == summary['metadata']['split_csv_sha256']
    assert sha(MODEL) == summary['classification_metrics']['structured_onnx']['sha256']
    assert sha(MODEL) == '2ec932a12e4730811597d297edc4de4566cdd6b381e871bc65c658ec8d794d27'
    load_splits(SPLIT, DATA, CLASSES)  # Verifies every MD5, group and cross-split boundary.
    rows = read_csv(SPLIT)
    test = [r for r in rows if r['split'] == 'test']
    assert len(test) == 256 and len({r['relative_path'] for r in test}) == 256
    for r in rows:
        r['id'] = hashlib.sha1(r['relative_path'].replace('\\', '/').encode()).hexdigest()[:12]
    assert len({r['id'] for r in rows}) == len(rows)
    sources = [MODEL, CONFIG, SPLIT, HISTORY / 'summary.json', HISTORY / 'all_predictions.csv',
               ROOT / 'products/fe/tools/quantize_model.py', Path(__file__),
               ROOT / 'docs/revision-plan/outputs/phase-04/protocol.json']
    sources += [DATA / r['relative_path'] for r in rows]
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    options = ort.SessionOptions()
    options.intra_op_num_threads = options.inter_op_num_threads = 1
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    runtime = ort.InferenceSession(str(MODEL), sess_options=options,
                                   providers=['CPUExecutionProvider'])
    inp, output = runtime.get_inputs()[0], runtime.get_outputs()[0]
    assert len(runtime.get_inputs()) == len(runtime.get_outputs()) == 1
    assert inp.shape[-3:] == [3, 256, 256] and inp.type == output.type == 'tensor(float)'
    assert output.shape[-1] == 4
    runtime.disable_fallback()
    return rows, test, hashes, runtime, inp.name


def predict(runtime, name, path):
    start = time.perf_counter_ns()
    tensor = preprocess(path)
    pre_ms = (time.perf_counter_ns() - start) / 1e6
    tick = time.perf_counter_ns()
    prob = runtime.run(None, {name: tensor})[0][0]
    pred_ms = (time.perf_counter_ns() - tick) / 1e6
    assert prob.shape == (4,) and np.isfinite(prob).all()
    assert np.all(prob >= -1e-7) and abs(float(prob.sum()) - 1) < 1e-5
    return prob, pre_ms, pred_ms


def prediction_row(r, condition, path, runtime, name):
    # Preserve all input failures as rows. A gate failure prevents degraded runs.
    try:
        prob, pre_ms, pred_ms = predict(runtime, name, path)
        idx = int(prob.argmax())
        return dict(id=r['id'], relative_path=r['relative_path'], split_group=r['split_group'],
                    label=r['label'], label_idx=int(r['label_idx']), condition=condition,
                    status='OK', prediction=CLASSES[idx], pred_idx=idx,
                    probabilities=json.dumps(prob.tolist()), confidence=float(prob.max()),
                    preprocess_ms=pre_ms, predict_ms=pred_ms,
                    preprocess_predict_ms=pre_ms + pred_ms, error='')
    except Exception as error:
        return dict(id=r['id'], relative_path=r['relative_path'], split_group=r['split_group'],
                    label=r['label'], label_idx=int(r['label_idx']), condition=condition,
                    status='FAIL', prediction='', pred_idx=-1, probabilities='[]', confidence='',
                    preprocess_ms='', predict_ms='', preprocess_predict_ms='', error=repr(error))


def transformed(clean, condition):
    if condition == 'clean':
        return clean.copy()
    if condition.startswith('jpeg_q'):
        buff = io.BytesIO()
        clean.save(buff, format='JPEG', quality=int(condition.split('q')[-1]))
        buff.seek(0)
        with Image.open(buff) as decoded:
            return decoded.convert('RGB').copy()
    if condition.startswith('short_edge_'):
        edge = int(condition.split('_')[-1])
        scale = min(1., edge / min(clean.size))
        return clean.resize(tuple(max(1, round(x * scale)) for x in clean.size),
                            Image.Resampling.BILINEAR)
    if condition.startswith('blur_sigma_'):
        return clean.filter(ImageFilter.GaussianBlur(radius=int(condition.split('_')[-1])))
    return ImageEnhance.Brightness(clean).enhance(float(condition.split('_')[-1]))


def save_variant(r, condition, clean):
    path = OUT / 'derived' / condition / (r['id'] + '.png')
    path.parent.mkdir(parents=True, exist_ok=True)
    im = transformed(clean, condition)
    im.save(path, format='PNG')
    return path, dict(parent_id=r['id'], parent_path=r['relative_path'],
                     parent_sha256=sha(DATA / r['relative_path']), split=r['split'],
                     split_group=r['split_group'], label=r['label'], condition=condition,
                     width=im.width, height=im.height, variant_sha256=sha(path),
                     path=str(path.relative_to(ROOT)), format='PNG lossless decoded transform',
                     label_validity='unadjudicated; inherited label under synthetic corruption')


def clean_stage():
    assert not (OUT / 'clean-predictions.csv').exists(), 'Refuse to overwrite clean run'
    rows, test, hashes, runtime, name = setup()
    write_json('source-hashes.json', hashes)
    protocol = dict(status='LOCKED_BEFORE_TEST_INFERENCE', scope='CPU_ONLY_ONNX',
        conditions=CONDITIONS, independent_unit='252 split_groups, 256 original test images',
        seed=20261107, bootstrap_draws=5000, ci='paired cluster percentile bootstrap, 95%, unadjusted',
        hypotheses='No null-hypothesis tests; all eight paired effect CIs reported',
        ordinal=dict(zip(CLASSES, ORDINAL.tolist())), model_sha256=sha(MODEL),
        clean_gate='100% historical structured_onnx argmax agreement and probabilities allclose atol=1e-5 rtol=1e-4',
        preprocess='repository quantize_model.preprocess: EXIF->RGB->bilinear letterbox256->ImageNet NCHW',
        transforms='independent from decoded EXIF RGB; JPEG Pillow defaults quality50/20 decoded then lossless PNG; short edge128/64 min(1,edge/min(w,h)), round; GaussianBlur radius1/2; Brightness .7/.4',
        abstention='disabled; report confidence distribution and descriptive fraction below .5, no threshold tuning',
        budget='256 clean + 2048 degraded test inferences; three separate validation smoke/warmup calls',
        timing='CPU one thread; predict and preprocess+predict recorded separately; excludes model load, derivative generation, file hashing/logging',
        order='clean first for parity gate, then image order as split CSV; eight conditions cyclically rotated by image index',
        failures='keep all 256 per condition; incorrect for accuracy/F1; decode failure counted separately from ordinal errors',
        limits='synthetic corruption labels not re-adjudicated; no real camera/Android/field claim; training split provenance remains unverified')
    write_json('protocol.json', protocol)
    write_json('environment.json', dict(python=sys.version, platform=platform.platform(),
        machine=platform.machine(), processor=platform.processor(),
        packages={p: importlib.metadata.version(p) for p in ['numpy','Pillow','onnxruntime','scipy']},
        providers=runtime.get_providers(), threads=1, android='NOT_RUN; adb/device unavailable',
        model_metadata=runtime.get_modelmeta().custom_metadata_map))
    validation = [r for r in rows if r['split'] == 'val'][:3]
    smoke = [prediction_row(r, 'validation_smoke', DATA / r['relative_path'], runtime, name) for r in validation]
    write_csv('validation-smoke-predictions.csv', smoke)
    assert all(r['status'] == 'OK' for r in smoke)
    historical = {}
    for r in read_csv(HISTORY / 'all_predictions.csv'):
        relative = r['image_path'].replace('\\','/').split('Dataset_Flood/')[-1]
        assert relative not in historical
        historical[relative] = r
    assert set(historical) == {r['relative_path'] for r in test}
    preds, manifest = [], []
    for i, r in enumerate(test):
        with Image.open(DATA / r['relative_path']) as im:
            clean = ImageOps.exif_transpose(im).convert('RGB')
        path, entry = save_variant(r, 'clean', clean)
        assert np.array_equal(preprocess(path), preprocess(DATA / r['relative_path']))
        manifest.append(entry)
        preds.append(prediction_row(r, 'clean', path, runtime, name))
        if (i+1) % 64 == 0:
            print('CLEAN', i+1, '/256', flush=True)
    write_csv('clean-predictions.csv', preds)
    write_csv('clean-manifest.csv', manifest)
    success = all(r['status'] == 'OK' for r in preds)
    actual = np.array([json.loads(r['probabilities']) for r in preds]) if success else None
    expected = np.array([json.loads(historical[r['relative_path']]['probabilities_structured_onnx']) for r in test])
    gate = dict(status='FAIL', n=256, failures=sum(r['status']!='OK' for r in preds),
                probability_atol=1e-5, probability_rtol=1e-4, source_hashes=hashes)
    if success:
        gate.update(top1_agreement=float((actual.argmax(1)==expected.argmax(1)).mean()),
                    max_abs_probability_difference=float(np.abs(actual-expected).max()),
                    probabilities_close=bool(np.allclose(actual,expected,atol=1e-5,rtol=1e-4)))
        if gate['top1_agreement'] == 1 and gate['probabilities_close']:
            gate['status'] = 'PASS_CPU_ONLY'
    write_json('clean-parity.json', gate)
    print(json.dumps({k:v for k,v in gate.items() if k!='source_hashes'},indent=2),flush=True)
    assert gate['status'] == 'PASS_CPU_ONLY', 'Clean gate failed; no degraded inference authorized'


def degraded_stage():
    assert not (OUT / 'degraded-predictions.csv').exists(), 'Refuse to overwrite degraded run'
    gate = json.loads((OUT / 'clean-parity.json').read_text())
    assert gate['status'] == 'PASS_CPU_ONLY'
    for path, digest in gate['source_hashes'].items():
        assert sha(ROOT / path) == digest, path
    _, test, _, runtime, name = setup()
    preds, manifest = [], []
    for i, r in enumerate(test):
        with Image.open(DATA / r['relative_path']) as im:
            clean = ImageOps.exif_transpose(im).convert('RGB')
        conditions = CONDITIONS[1:]
        offset = i % len(conditions)
        for condition in conditions[offset:] + conditions[:offset]:
            try:
                path, entry = save_variant(r, condition, clean)
                manifest.append(entry)
                preds.append(prediction_row(r, condition, path, runtime, name))
            except Exception as error:
                # A generation failure is retained and stops this stage; never silently drop an image.
                write_json('generation-failure.json', dict(id=r['id'],condition=condition,error=repr(error)))
                raise
        if (i+1) % 32 == 0:
            print('DEGRADED', (i+1)*8, '/2048', flush=True)
    write_csv('degraded-predictions.csv', preds)
    write_csv('predictions.csv', read_csv(OUT/'clean-predictions.csv') + preds)
    write_csv('variant-manifest.csv', read_csv(OUT/'clean-manifest.csv') + manifest)
    print('Completed 2304 test inferences; Android NOT_RUN',flush=True)


def summarize():
    predictions = read_csv(OUT / 'predictions.csv')
    groups = sorted({r['split_group'] for r in predictions})
    assert len(groups) == 252
    group_index = {g:i for i,g in enumerate(groups)}
    # Shared bootstrap group multiplicities across every condition preserves pairing.
    rng = np.random.default_rng(20261107)
    draws = rng.integers(0,len(groups),size=(5000,len(groups)))
    weights = np.zeros((5000,len(groups)), dtype=np.int32)
    np.add.at(weights,(np.arange(5000)[:,None],draws),1)
    metric_names = ['accuracy','macro_f1','recall_high','ordinal_error_ge2_rate']
    def values(cm):
        n = cm.sum(axis=(-1,-2))
        diag = np.stack([cm[...,i,i] for i in range(4)],axis=-1)
        actual = cm.sum(axis=-1)
        predicted = cm[...,:4].sum(axis=-2)
        denominator = actual + predicted
        f1 = np.divide(2*diag,denominator,out=np.zeros_like(diag,dtype=float),where=denominator!=0).mean(axis=-1)
        severe = sum(cm[...,i,j] for i in range(4) for j in range(4) if abs(ORDINAL[i]-ORDINAL[j])>=2)
        return np.stack([diag.sum(axis=-1)/n,f1,diag[...,2]/actual[...,2],severe/n],axis=-1)
    metrics, effects, bootstrap, cm_records = [], [], {}, {}
    id_sets = []
    for condition in CONDITIONS:
        rows = [r for r in predictions if r['condition']==condition]
        assert len(rows)==256 and len({r['id'] for r in rows})==256
        id_sets.append({r['id'] for r in rows})
        cm_group = np.zeros((len(groups),4,5),dtype=int)
        for r in rows:
            pred = int(r['pred_idx']) if r['status']=='OK' else 4
            cm_group[group_index[r['split_group']],int(r['label_idx']),pred] += 1
        cm = cm_group.sum(axis=0)
        point = values(cm)
        sampled = (weights @ cm_group.reshape(len(groups),-1)).reshape(5000,4,5)
        bootstrap[condition] = values(sampled)
        low,high = np.quantile(bootstrap[condition],[.025,.975],axis=0)
        record = dict(condition=condition,n_images=256,n_groups=252,failures=sum(r['status']!='OK' for r in rows))
        for i,metric in enumerate(metric_names):
            record.update({metric:float(point[i]),metric+'_ci_low':float(low[i]),metric+'_ci_high':float(high[i])})
        valid = [r for r in rows if r['status']=='OK']
        confidence = np.array([float(r['confidence']) for r in valid])
        record.update(mean_confidence=float(confidence.mean()),confidence_p10=float(np.quantile(confidence,.1)),
                      confidence_below_0_5=int((confidence<.5).sum()),abstention_enabled=False,
                      ordinal_error_ge2_count=int(round(point[3]*256)))
        for scope in ['predict_ms','preprocess_predict_ms']:
            timings = np.array([float(r[scope]) for r in valid])
            record.update({scope+'_mean':float(timings.mean()),scope+'_p50':float(np.median(timings)),
                           scope+'_p95':float(np.quantile(timings,.95))})
        metrics.append(record)
        cm_records[condition] = cm.tolist()
    assert all(s==id_sets[0] for s in id_sets)
    baseline = np.array([metrics[0][m] for m in metric_names])
    for record in metrics[1:]:
        condition=record['condition']
        delta=bootstrap[condition]-bootstrap['clean']
        low,high=np.quantile(delta,[.025,.975],axis=0)
        for i,metric in enumerate(metric_names):
            effects.append(dict(condition=condition,metric=metric,delta_degraded_minus_clean=record[metric]-baseline[i],
                                ci_low=float(low[i]),ci_high=float(high[i]),n_groups=252,n_images=256,
                                bootstrap_draws=5000,seed=20261107,p_value='NOT_TESTED',
                                correction='unadjusted percentile CI; no null hypothesis tests'))
    write_csv('metrics.csv',metrics)
    write_csv('paired-effects.csv',effects)
    write_json('confusion-matrices.json',dict(class_order=CLASSES,prediction_columns=CLASSES+['failure'],matrices=cm_records))
    manifest=read_csv(OUT/'variant-manifest.csv')
    assert len(manifest)==2304
    assert all(sha(ROOT/r['path'])==r['variant_sha256'] for r in manifest)
    write_json('validation.json',dict(status='PASS_CPU_ONLY',test_predictions=len(predictions),
        validation_inferences=3,independent_images=256,split_groups=252,conditions=9,
        failures=sum(r['status']!='OK' for r in predictions),variant_hashes_checked=len(manifest),
        paired_effects=len(effects),android='NOT_RUN',raw_inputs_unchanged='checked separately'))
    print(json.dumps(metrics,indent=2),flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['clean','degraded','summarize'])
    args=parser.parse_args()
    {'clean':clean_stage,'degraded':degraded_stage,'summarize':summarize}[args.stage]()
