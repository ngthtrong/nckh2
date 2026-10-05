#!/usr/bin/env python3
"""Draw report figures from saved evidence; no inference, training or data mutation."""
import csv
import hashlib
import json
import importlib.metadata
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
from PIL import Image, ImageOps
from mobile_evidence import audit_mobile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'report/assets/figures'
SOURCES = {}
OUTPUTS = {}
BLUE, ORANGE = '#245b83', '#b55a26'
for face in ['times.ttf', 'timesbd.ttf', 'timesi.ttf', 'timesbi.ttf']:
    candidate = Path('/mnt/c/Windows/Fonts') / face
    if candidate.is_file():
        font_manager.fontManager.addfont(candidate)
FONT = ('Times New Roman' if any(f.name == 'Times New Roman' for f in font_manager.fontManager.ttflist)
        else 'DejaVu Sans')
plt.rcParams.update({'font.family': FONT, 'font.size': 12,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.titleweight': 'bold', 'pdf.fonttype': 42,
                     'savefig.facecolor': 'white'})


def read(path):
    raw = (ROOT / path).read_bytes()
    SOURCES[path] = hashlib.sha256(raw).hexdigest()
    return raw


def obj(path):
    return json.loads(read(path))


def rows(path):
    return list(csv.DictReader(read(path).decode('utf-8-sig').splitlines()))


def save(fig, name):
    fig.savefig(OUT / (name + '.pdf'), bbox_inches='tight',
                metadata={'CreationDate': None, 'ModDate': None})
    fig.savefig(OUT / (name + '.png'), bbox_inches='tight', dpi=180)
    OUTPUTS[name] = {ext: hashlib.sha256((OUT / (name + '.' + ext)).read_bytes()).hexdigest()
                     for ext in ['pdf', 'png']}
    plt.close(fig)


def image_figures(base, predictions, split):
    classes = base['metadata']['class_order']
    matrix = np.array(base['classification_metrics']['pth']['confusion_matrix'])
    normalized = matrix / matrix.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(6.8, 4.8), layout='constrained')
    heat = ax.imshow(normalized, cmap='Blues', vmin=0, vmax=1)
    for i in range(4):
        for j in range(4):
            ax.text(j, i, f'{matrix[i,j]}\n{normalized[i,j]:.1%}', ha='center', va='center',
                    color='white' if normalized[i,j] > .55 else '#172d3b', fontsize=11)
    ax.set(xticks=range(4), yticks=range(4), xticklabels=classes, yticklabels=classes,
           xlabel='Nhãn dự đoán', ylabel='Nhãn thật')
    fig.colorbar(heat, ax=ax, label='Tỷ lệ trong mỗi lớp thật')
    save(fig, 'image-confusion')

    # Reproducible illustrative selection: smallest relative path within each category.
    by_path = {r['image_path'].replace('\\', '/').split('/Dataset_Flood/', 1)[1]: r
               for r in predictions}
    selected = []
    fig, axes = plt.subplots(2, 4, figsize=(8, 5.8), layout='constrained')
    for col, label in enumerate(classes):
        for row, correct in enumerate([True, False]):
            candidates = sorted((p, r) for p, r in by_path.items()
                                if r['ground_truth'] == label and (r['pred_pth'] == label) == correct)
            path, r = candidates[0]
            relative = 'products/fe/model/Dataset_Flood/' + path
            read(relative)
            with Image.open(ROOT / relative) as source:
                picture = ImageOps.exif_transpose(source).convert('RGB')
                axes[row, col].imshow(picture)
            axes[row, col].set_title(f'Thật: {label}\nDự đoán: {r["pred_pth"]}\np = {float(r["confidence_pth"]):.3f}',
                                     fontsize=11, color=BLUE if correct else ORANGE)
            axes[row, col].axis('off')
            selected.append({'path': path, 'truth': label, 'prediction': r['pred_pth'],
                             'confidence': float(r['confidence_pth']), 'selection': 'first sorted path'})
    save(fig, 'image-examples')

    history = rows('products/fe/model/Edge Ai/mobilenetv3_large_dataset_v4_seed42/history_mobilenetv3_large.csv')
    epochs = [int(r['epoch']) for r in history]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5), layout='constrained')
    for part, name, color in [('train', 'Train', BLUE), ('val', 'Validation', ORANGE)]:
        axes[0].plot(epochs, [float(r[part + '_loss']) for r in history], 'o-', label=name, color=color)
        axes[1].plot(epochs, [float(r[part + '_acc']) * 100 for r in history], 'o-', label=name, color=color)
    axes[0].set(xlabel='Epoch đã lưu', ylabel='Loss tổng hợp')
    axes[1].set(xlabel='Epoch đã lưu', ylabel='Accuracy (%)', ylim=(0, 100))
    for ax in axes:
        ax.legend(); ax.grid(alpha=.18)
    save(fig, 'training-history')

    # Report coverage and error in bins, without interpreting confidence as medical risk.
    confidence = np.array([float(r['confidence_pth']) for r in predictions])
    correct = np.array([r['pred_pth'] == r['ground_truth'] for r in predictions])
    bins = []
    for lo in np.arange(0, 1, .1):
        mask = (confidence >= lo) & (confidence < lo + .1 if lo < .9 else confidence <= 1)
        if mask.any():
            bins.append({'lower': round(float(lo), 1), 'n': int(mask.sum()),
                         'confidence': float(confidence[mask].mean()), 'accuracy': float(correct[mask].mean())})
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), layout='constrained')
    axes[0].plot([0, 1], [0, 1], '--', color='#777777', linewidth=1, label='Đường lý tưởng')
    axes[0].plot([b['confidence'] for b in bins], [b['accuracy'] for b in bins], 'o-', color=BLUE)
    axes[0].set(xlabel='Confidence trung bình theo bin', ylabel='Tỷ lệ đúng theo bin',
                xlim=(0, 1), ylim=(0, 1)); axes[0].legend(fontsize=8)
    axes[1].bar([b['lower'] + .05 for b in bins], [b['n'] for b in bins], width=.085, color=BLUE)
    axes[1].set(xlabel='Bin confidence (độ rộng 0,1)', ylabel='Số ảnh test', xlim=(0, 1))
    save(fig, 'confidence-calibration')
    return {'illustrative_images': selected, 'confidence_bins': bins,
            'confidence_ge_090': {'samples': int((confidence >= .9).sum()),
                                 'correct': int(correct[confidence >= .9].sum())},
            'history_rows': len(history)}


def compression_figures():
    quant = obj('products/fe/reports/fp32_ptq_qat/summary.json')['classification_metrics']
    prune = obj('products/fe/reports/pruning_st/summary.json')['classification_metrics']
    fig, axes = plt.subplots(1, 2, figsize=(9.3, 4), layout='constrained')
    for k, title, color in [('onnx_fp32', 'FP32', BLUE), ('ptq_int8', 'PTQ', '#478558'), ('qat_int8', 'QAT', ORANGE)]:
        m = quant[k]
        axes[0].scatter(m['bytes'] / 1024**2, 100*m['accuracy'], s=80, c=color)
        axes[0].annotate(title, (m['bytes']/1024**2, 100*m['accuracy']), xytext=(4, 5), textcoords='offset points')
    axes[0].set(xlabel='Dung lượng ONNX (MiB)', ylabel='Accuracy summary (%)', xlim=(0, 19), ylim=(40, 85))
    keys = ['pth', 'onnx', 'pte']; x = np.arange(3)
    for prefix, offset, name, color in [('baseline', -.19, 'Gốc', BLUE), ('structured', .19, 'Cắt tỉa', ORANGE)]:
        axes[1].bar(x+offset, [prune[prefix+'_'+k]['latency_ms_median'] for k in keys], .36, label=name, color=color)
    axes[1].set(xticks=x, xticklabels=['PTH', 'ONNX', 'PTE'], ylabel='P50 predict CPU (ms)')
    axes[1].legend(); axes[0].grid(alpha=.18)
    save(fig, 'compression-tradeoffs')


def research_figures():
    benchmark = rows('thucnghiem/results/cij_baseline_benchmark_results/benchmark_summary.csv')
    names = {'product_cij_louvain': 'Product Louvain', 'additive_cij_louvain': 'Additive Louvain',
             'product_cij_leiden': 'Product Leiden', 'convex_cij_louvain': 'Convex Louvain',
             'additive_cij_louvain_matched_density': 'Additive mật độ khớp'}
    selected = sorted([r for r in benchmark if r['method'] in names], key=lambda r: -float(r['ari_mean']))
    fig, ax = plt.subplots(figsize=(7.5, 3.5), layout='constrained')
    for i, r in enumerate(selected):
        mean = float(r['ari_mean']); low = float(r['ari_ci95_low']); high = float(r['ari_ci95_high'])
        ax.errorbar(mean, i, xerr=[[mean-low], [high-mean]], fmt='o', color=BLUE, capsize=4)
        ax.text(.95, i, f'{mean:.4f}', va='center', fontsize=9)
    ax.set(yticks=range(len(selected)), yticklabels=[names[r['method']] for r in selected],
           xlabel='ARI trung bình và CI bootstrap 95%', xlim=(.85, .99))
    ax.invert_yaxis(); ax.grid(axis='x', alpha=.18)
    save(fig, 'rq1-graph-baselines')

    rq2 = rows('thucnghiem/results/rq2_results/rq2_summary.csv')
    labels = {'duplicate_aware_robust': 'Có chặn', 'legacy_raw': 'Legacy', 'population_only': 'Chỉ số người',
              'random': 'Ngẫu nhiên', 'simple_linear': 'Tuyến tính', 'urgency_only': 'Chỉ khẩn cấp'}
    align = [r for r in rq2 if r['section'] == 'alignment' and r['metric'] == 'ndcg_at_5']
    fig, ax = plt.subplots(figsize=(7.5, 3.8), layout='constrained')
    for i, r in enumerate(align):
        mean = float(r['mean']); lo, hi = json.loads(r['paired_confidence_interval'])
        ax.errorbar(mean, i, xerr=[[mean-lo], [hi-mean]], fmt='o', capsize=4, color=BLUE)
    ax.set(yticks=range(len(align)), yticklabels=[labels[r['method']] for r in align],
           xlabel='NDCG@5 và CI 95% (40 seed, nhóm oracle)', xlim=(0, 1))
    ax.invert_yaxis(); ax.grid(axis='x', alpha=.18)
    save(fig, 'rq2-alignment')

    cases = [('exact_duplicate_10x', 'Exact ×10'), ('near_duplicate', 'Gần trùng'),
             ('low_confidence_inflate_N', 'Tăng N, Q thấp'), ('low_confidence_inflate_V', 'Tăng V, Q thấp'),
             ('coordinated_high_confidence_campaign', 'Phối hợp Q cao')]
    fig, ax = plt.subplots(figsize=(8, 3.8), layout='constrained')
    x = np.arange(len(cases))
    for key, label, offset, color in [('duplicate_aware_robust', 'Có chặn', -.19, BLUE), ('legacy_raw', 'Legacy', .19, ORANGE)]:
        vals = [float(next(r for r in rq2 if r['section'] == 'robustness' and r['metric'] == 'priority_drift_abs_normalized'
                          and r['method'] == key and r['scenario'] == case)['mean']) for case, _ in cases]
        ax.barh(x+offset, vals, .36, label=label, color=color)
    ax.set(yticks=x, yticklabels=[label for _, label in cases], xlabel='Drift điểm tuyệt đối chuẩn hóa (thấp hơn tốt hơn)',
           xlim=(0, .19))
    ax.invert_yaxis(); ax.legend(); ax.grid(axis='x', alpha=.18)
    save(fig, 'rq2-robustness')


def mobile_figure(split, predictions):
    mobile, audit = audit_mobile(read('products/fe/reports/mobile/samsung21se.json'), split)
    fig, ax = plt.subplots(figsize=(7.5, 3.6), layout='constrained')
    data = [[r['latencyMs'] for r in mobile[k]['predictions']] for k in ['onnx', 'pte']]
    ax.boxplot(data, tick_labels=['ONNX', 'ExecuTorch'], widths=.45,
               medianprops={'color': ORANGE, 'linewidth': 2}, flierprops={'markersize': 3})
    ax.set(ylabel='Thời gian classifyImage (ms)', ylim=(0, max(max(x) for x in data)*1.08))
    ax.grid(axis='y', alpha=.18)
    save(fig, 'mobile-latency')
    expected = {hashlib.sha1(r['relative_path'].replace('\\', '/').encode()).hexdigest()[:12]: r['relative_path']
                for r in split if r['split'] == 'test'}
    cpu = {r['image_path'].replace('\\', '/').split('/Dataset_Flood/', 1)[1]: r for r in predictions}
    agreement = sum(r['prediction'] == cpu[expected[r['id']]]['pred_pth'] for r in mobile['onnx']['predictions'])
    audit['cpu_top1_agreement_count'] = agreement
    return audit


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base = obj('products/fe/reports/pth_onnx_pte/summary.json')
    predictions = rows('products/fe/reports/pth_onnx_pte/all_predictions.csv')
    split = rows('products/fe/model/Edge Ai/split_train_val_test_mobilenetv3_large.csv')
    # Reuse the table exporter's split/prediction consistency check.
    from export_results import verify_predictions
    verify_predictions(base, 'products/fe/reports/pth_onnx_pte/all_predictions.csv', split)
    metrics = image_figures(base, predictions, split)
    compression_figures(); research_figures()
    metrics['mobile_audit'] = mobile_figure(split, predictions)
    for source in ['report/scripts/build_figures.py', 'report/scripts/mobile_evidence.py']:
        read(source)
    (ROOT / 'report/generated/figure-provenance.json').write_text(json.dumps(
        {'sources_sha256': SOURCES, 'figures_sha256': OUTPUTS, 'derived': metrics,
         'environment': {'font': FONT, **{name: importlib.metadata.version(name)
                                        for name in ['matplotlib', 'numpy', 'Pillow']}},
         'note': 'Saved evidence only; example photos are a deterministic illustrative subset, not new observations.'},
        ensure_ascii=False, indent=2) + '\n')
    print(f'Generated {len(OUTPUTS)} figures with input/output hashes.')


if __name__ == '__main__':
    main()
