"""Read-only analysis of local-20261110-04; writes one self-contained HTML report.

Does not load model weights or execute training/inference. Recomputes classification
metrics from saved predictions and verifies recorded output manifests.
"""
from __future__ import annotations

import base64
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta, timezone
import hashlib
from html import escape as esc
import io
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
RUN = HERE / 'local-work/local-20261110-04'
B = RUN / 'bundle-results'
OUT = HERE / 'bao-cao-phan-tich-local-20261110-04.html'
TZ = timezone(timedelta(hours=8))
SOURCES = {}
INDEPENDENT = []


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def source(path):
    path = Path(path).resolve()
    if path not in SOURCES:
        SOURCES[path] = (len(SOURCES) + 1, sha(path))
    return path


def js(relative):
    p = source(B / relative)
    return json.loads(p.read_text(encoding='utf-8'))


def rows(relative):
    p = source(B / relative)
    with p.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def refs(*relative):
    links = []
    for p in relative:
        p = source(B / p) if not isinstance(p, Path) else source(p)
        number = SOURCES[p][0]
        links.append(f'<a href="#src-{number}">[S{number:02d}]</a>')
    return '<p class="source">Nguồn: ' + ' · '.join(links) + '</p>'


def pct(x):
    return f'{float(x) * 100:.2f}%'


def pp(x):
    return f'{float(x) * 100:+.2f}'


def number(x, digits=2):
    return f'{float(x):,.{digits}f}'


def table(headers, values, caption=None):
    result = '<div class="table-wrap"><table>'
    if caption:
        result += f'<caption>{esc(caption)}</caption>'
    result += '<thead><tr>' + ''.join('<th>' + esc(str(h)) + '</th>' for h in headers) + '</tr></thead><tbody>'
    for row in values:
        result += '<tr>' + ''.join('<td>' + esc(str(value)) + '</td>' for value in row) + '</tr>'
    return result + '</tbody></table></div>'


def para(text, cls=''):
    return f'<p class="{cls}">{text}</p>'


def callout(title, text, kind='note'):
    return f'<aside class="{kind}"><strong>{title}</strong><p>{text}</p></aside>'


def figure(fig, caption):
    stream = io.BytesIO()
    fig.savefig(stream, format='png', dpi=160, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    data = base64.b64encode(stream.getvalue()).decode()
    return f'<figure><img src="data:image/png;base64,{data}" alt="{esc(caption)}"><figcaption>{esc(caption)}</figcaption></figure>'


def confusion(y, p, labels):
    matrix = np.zeros((len(labels), len(labels)), dtype=int)
    for a, b in zip(y, p):
        matrix[labels.index(a), labels.index(b)] += 1
    return matrix


def metrics(matrix):
    tp = np.diag(matrix).astype(float)
    support = matrix.sum(axis=1)
    predicted = matrix.sum(axis=0)
    precision = np.divide(tp, predicted, out=np.zeros_like(tp), where=predicted != 0)
    recall = np.divide(tp, support, out=np.zeros_like(tp), where=support != 0)
    f1 = np.divide(2 * precision * recall, precision + recall,
                   out=np.zeros_like(tp), where=(precision + recall) != 0)
    return {'accuracy': float(tp.sum() / matrix.sum()), 'macro_f1': float(f1.mean()),
            'precision_request': float(precision[-1]), 'recall_request': float(recall[-1])}


def close(a, b, context):
    if not np.isclose(float(a), float(b), atol=1e-11, rtol=1e-10):
        raise AssertionError((context, a, b))


def check_image(predictions, summary):
    rr = rows(predictions)
    info = js(summary)
    labels = info['metadata']['class_order']
    for name, saved in info['classification_metrics'].items():
        cm = confusion([r['ground_truth'] for r in rr], [r['pred_' + name] for r in rr], labels)
        assert cm.tolist() == saved['confusion_matrix']
        got = metrics(cm)
        for key in ['accuracy', 'macro_f1']:
            close(got[key], saved[key], (predictions, name, key))
        INDEPENDENT.append((predictions, name, len(rr)))


def check_binary(predictions, metric_file, gold, predicted, model_key='model', positive='request'):
    rr, mm = rows(predictions), rows(metric_file)
    groups = defaultdict(list)
    for row in rr:
        groups[row[model_key]].append(row)
    labels = ['not_informative', 'informative'] if positive == 'informative' else ['no_request', 'request']
    for saved in mm:
        name = saved[model_key]
        values = groups[name]
        assert len({row['image_id'] for row in values}) == len(values) == int(saved['n'])
        matrix = confusion([r[gold] for r in values], [r[predicted] for r in values], labels)
        calculated = metrics(matrix)
        for key in ['accuracy', 'macro_f1']:
            close(calculated[key], saved[key], (predictions, name, key))
        if 'recall_request' in saved:
            for key in ['precision_request', 'recall_request']:
                close(calculated[key], saved[key], (predictions, name, key))
            assert matrix.ravel().tolist() == [int(saved[k]) for k in ['tn', 'fp', 'fn', 'tp']]
        if 'recall_informative' in saved:
            close(calculated['recall_request'], saved['recall_informative'], name)
        INDEPENDENT.append((predictions, name, len(values)))


def verify_receipts():
    count = 0
    # Every artifact explicitly bound by a completed receipt is checked; extra
    # files are not treated as evidence of a stage having completed.
    for path in sorted(B.glob('*/stage.json')):
        receipt = json.loads(source(path).read_text(encoding='utf-8'))
        for base, entries in [(path.parent, receipt.get('outputs', {})),
                              (RUN, receipt.get('external_outputs', {}))]:
            for relative, expected in entries.items():
                artifact = (base / relative).resolve()
                assert artifact.is_relative_to(RUN.resolve())
                assert artifact.is_file() and sha(artifact) == expected, artifact
                count += 1
    return count


def bin_table(rr, include_model_names=True):
    return table(['Mô hình', 'Accuracy', 'Macro-F1', 'Precision request', 'Recall request', 'TN / FP / FN / TP'],
                 [(r.get('model', 'seed ' + str(r.get('seed', ''))), pct(r['accuracy']), pct(r['macro_f1']),
                   pct(r['precision_request']), pct(r['recall_request']),
                   ' / '.join(r[k] for k in ['tn', 'fp', 'fn', 'tp'])) for r in rr])


def effects(rr, public=False):
    if public:
        return table(['So sánh', 'Δ Macro-F1 (đpt)', 'CI 95% (đpt)', 'Số nhóm'],
                     [(r['contrast'], pp(r['delta_macro_f1']),
                       f"[{pp(r['ci95_low'])}; {pp(r['ci95_high'])}]", r['test_groups']) for r in rr])
    return table(['F1 trừ mô hình', 'Δ Macro-F1 (đpt)', 'CI 95% (đpt)', 'Đối chứng chính'],
                 [(r['comparator'], pp(r['delta']), f"[{pp(r['ci_low'])}; {pp(r['ci_high'])}]",
                   'Có' if r['primary'] == 'True' else 'Không') for r in rr])


def image_pair_table(pairs):
    return table(['So sánh', 'Đúng → sai', 'Sai → đúng', 'Δ Accuracy (đpt)', 'Δ Macro-F1 (đpt)',
                  'CI 95% Δ Macro-F1 (đpt)', 'p McNemar–Holm'],
                 [(name, v['correct_to_wrong'], v['wrong_to_correct'], pp(v['delta_accuracy']),
                   pp(v['delta_macro_f1']),
                   '[' + '; '.join(pp(x) for x in v['delta_macro_f1_ci95_unadjusted']) + ']',
                   f"{v['mcnemar_holm_p']:.6g}") for name, v in pairs.items()])


def main():
    state = json.loads(source(RUN / 'local-control/state.json').read_text())
    assert state['status'] == 'COMPLETED'
    checked = verify_receipts()
    check_image('image_export_compare/comparison/all_predictions.csv', 'image_export_compare/comparison/summary.json')
    check_image('quantization_analysis/comparison/all_predictions.csv', 'quantization_analysis/comparison/summary.json')
    check_binary('public_fusion/outputs/test-predictions.csv', 'public_fusion/outputs/metrics.csv',
                 'gold', 'prediction', positive='informative')
    check_binary('silver_evaluation/outputs/predictions.csv', 'silver_evaluation/outputs/metrics.csv',
                 'label_ai', 'predicted_label')
    check_binary('silver_evaluation/outputs/t2-predictions.csv', 'silver_evaluation/outputs/t2-metrics.csv',
                 'label_ai', 'predicted_label', model_key='seed')
    check_binary('synthetic_evaluation/outputs/predictions.csv', 'synthetic_evaluation/outputs/metrics.csv',
                 'label_synthetic', 'predicted_label')

    config = js('locked-config.json')
    preflight = js('preflight/preflight.json')
    env = preflight['environment']
    pruning = [js(f'image_pruning/ratio-{ratio}/metrics.json') for ratio in ['0.050', '0.100', '0.200']]
    selection = js('image_pruning/selection.json')
    image = js('image_export_compare/comparison/summary.json')['classification_metrics']
    quant = js('quantization_analysis/comparison/summary.json')['classification_metrics']
    image_stats = js('image_export_compare/paired-statistics.json')
    quant_stats = js('quantization_analysis/paired-statistics.json')
    public = rows('public_fusion/outputs/metrics.csv')
    silver = rows('silver_evaluation/outputs/metrics.csv')
    synthetic = rows('synthetic_evaluation/outputs/metrics.csv')
    t2 = js('silver_evaluation/outputs/t2-training.json')
    t2eval = js('silver_evaluation/outputs/t2-evaluation.json')
    t2rows = rows('silver_evaluation/outputs/t2-metrics.csv')
    t2grid = rows('silver_evaluation/outputs/t2-model-selection.csv')
    stage_rows = []
    active = 0.
    for path in sorted(B.glob('*/stage.json')):
        s = json.loads(path.read_text(encoding='utf-8'))
        active += s.get('seconds', 0)
        stage_rows.append((path.parent.name, s['status'], number(s.get('seconds', 0))))
    counts = Counter(r[1] for r in stage_rows)
    created = datetime.now(TZ).strftime('%d/%m/%Y %H:%M %z')
    sections = []

    def section(key, title, content):
        sections.append((key, title, f'<section id="{key}"><h2>{title}</h2>{content}</section>'))

    intro = callout('Kết luận chính',
        'Phiên thực nghiệm đã hoàn tất về kỹ thuật. Baseline ảnh FP32 vẫn là mốc chất lượng tốt nhất trong các '
        'biến thể ảnh được đánh giá mới. Các phương án nén hiện tại đánh đổi chất lượng rõ rệt; dữ liệu silver '
        'và synthetic chưa đủ để xác nhận hiệu quả cứu hộ ngoài thực tế.', 'important')
    intro += table(['Nhánh', 'Kết quả nổi bật', 'Diễn giải'], [
        ('Ảnh gốc / FP32', 'Accuracy 75,78%; Macro-F1 74,26%; 3/256 lỗi nặng', 'Mốc tham chiếu nội bộ, chưa kiểm chứng camera độc lập'),
        ('Pruning được chọn 5%', 'Macro-F1 68,14%; tham số giảm 8,70%', 'Không giữ được chất lượng test; lợi ích latency PTH nhỏ'),
        ('PTQ INT8 mới', 'Macro-F1 64,36%; median ONNX 5,01 ms', 'Nhanh và nhỏ hơn nhưng lỗi nặng tăng lên 17/256'),
        ('QAT lịch sử, đánh giá lại', 'Macro-F1 41,37%; median 19,53 ms', 'Không có lợi thế chất lượng hoặc tốc độ trong phép đo này'),
        ('CrisisMMD fusion', 'Macro-F1 78,35%; hơn text 1,75 đpt', 'Khoảng tin cậy chênh lệch chứa 0; kết quả thăm dò trên một sự kiện'),
        ('Silver fusion F1', 'Macro-F1 64,91%; phát hiện 2/6 request', 'Đối chứng chính có CI rộng; accuracy che khuất bỏ sót request'),
        ('Silver fine-tuning T2', 'Macro-F1 trung bình 52,29% qua 3 seed', 'Encoder đã cập nhật thật nhưng chưa có lợi thế so với frozen fusion'),
        ('Synthetic', 'T0/F0 đạt 100%; T1/F1 đạt 96,87% Macro-F1', 'Bài toán khuôn câu; ảnh ghép tùy ý, chỉ kiểm tra pipeline')])
    intro += para('“đpt” là điểm phần trăm: 74,26% xuống 68,14% tương ứng giảm 6,12 đpt, '
                  'không phải giảm 6,12% tương đối. Không so trực tiếp Macro-F1 giữa các bộ dữ liệu có nhiệm vụ và nhãn khác nhau.')
    intro += refs('image_export_compare/comparison/summary.json', 'quantization_analysis/comparison/summary.json',
                  'public_fusion/outputs/metrics.csv', 'silver_evaluation/outputs/metrics.csv',
                  'silver_evaluation/outputs/t2-evaluation.json', 'synthetic_evaluation/outputs/metrics.csv')
    section('overview', '1. Tóm tắt kết quả và ý nghĩa', intro)

    status = para(f'Trạng thái tổng: <strong>COMPLETED</strong>. Có {len(stage_rows)} stage được ghi nhận: '
                  + ', '.join(f'{v} {esc(k)}' for k, v in sorted(counts.items())) + '. '
                  'Không có stage FAILED hoặc RUNNING còn sót trong lần kiểm tra báo cáo.')
    status += table(['Stage', 'Trạng thái cuối', 'Thời gian receipt (giây)'], stage_rows)
    status += callout('Cách hiểu trạng thái',
        'COMPLETED chỉ xác nhận công việc của stage đã thực hiện. NOT_REQUESTED là mục không bật; '
        'DATA_NOT_READY là thiếu dữ liệu gold; REQUIRES_DEVICE là cần thiết bị thật. Không đổi các trạng thái '
        'này thành “đã hoàn tất nghiên cứu”.')
    status += para('Cấu hình này không huấn luyện baseline mới, không huấn luyện QAT mới, không xuất PTE mới '
                  'và không fine-tune T2 trên synthetic. QAT xuất hiện trong bảng kết quả là mô hình lịch sử được đánh giá lại.')
    status += refs(RUN / 'local-control/state.json', B / 'locked-config.json')
    section('status', '2. Phạm vi phiên chạy và mức độ hoàn tất', status)

    dataset_paths = {kind: source(RUN / f'thucnghiem/{kind}/data/dataset.json') for kind in ['multimodal', 'vi_rescue', 'vi_synthetic']}
    datasets = {k: json.loads(p.read_text(encoding='utf-8')) for k, p in dataset_paths.items()}
    datasets = {k: v['records'] if isinstance(v, dict) else v for k, v in datasets.items()}
    data = table(['Bộ dữ liệu', 'Train', 'Validation/dev', 'Test', 'Nhãn và phạm vi'], [
        ('Ảnh ngập lụt', 1189, 257, 256, '4 lớp low / medium / high / non_flood; split lịch sử'),
        ('CrisisMMD', 2971, 589, 701, 'Informative / not_informative; cặp có nhãn ảnh và text đồng thuận'),
        ('Silver tiếng Việt', 179, 58, 59, 'Dịch máy từ tiếng Anh; nhãn request do AI, không phải human gold'),
        ('Synthetic tiếng Việt', 1189, 257, 256, 'Khuôn câu tự soạn, nhãn từ text; ghép ảnh tùy ý')])
    data += para('Các nhóm ảnh được giữ theo split đã khóa; tập test ảnh có 252 split_group cho 256 ảnh. '
                 'CrisisMMD test chỉ gồm sự kiện Sri Lanka (701 cặp, 682 nhóm); dev là Hurricane Maria. '
                 'Silver giữ cùng cách chia sự kiện của pilot trước. Các tập test này đã được xem trong quá trình phát triển, '
                 'vì vậy đây là development replay, chưa phải kiểm chứng độc lập.')
    distributions = []
    for name, key in [('CrisisMMD', 'multimodal'), ('Silver', 'vi_rescue'), ('Synthetic', 'vi_synthetic')]:
        dd = datasets[key]
        label_key = 'label'
        if label_key not in dd[0]:
            label_key = 'gold' if 'gold' in dd[0] else 'informative'
        for split in ['train', 'dev', 'test']:
            ss = [r for r in dd if r['split'] == split]
            if not ss:
                continue
            labels = Counter(r[label_key] for r in ss)
            distributions.append((name, split, len(ss), '; '.join(f'{k}: {v}' for k, v in sorted(labels.items()))))
    data += table(['Bộ', 'Split', 'Số mẫu', 'Phân bố nhãn'], distributions)
    data += callout('Giới hạn nguồn dữ liệu',
        'Cả 1.702 ảnh ngập có source_group rỗng theo preflight. Các split_group không tự chứng minh '
        'độc lập theo sự kiện hoặc nguồn. Chưa có IAA/người gán độc lập cho silver và synthetic; '
        'giấy phép từng ảnh ngập chưa được xác minh đầy đủ. Không phát hành công khai ZIP dữ liệu chỉ vì pipeline đã chạy được.', 'warning')
    data += refs('preflight/preflight.json', 'public_fusion/outputs/protocol.json',
                 'silver_evaluation/outputs/protocol.json', 'synthetic_evaluation/outputs/protocol.json', *dataset_paths.values())
    section('data', '3. Dữ liệu, cách chia và độ tin cậy của nhãn', data)

    setup = table(['Thành phần', 'Giá trị ghi nhận'], [
        ('GPU', env['gpu']), ('VRAM được PyTorch nhận', f"{env['vram_bytes'] / 1024**3:.2f} GiB"),
        ('Compute capability', '.'.join(map(str, env['capability']))), ('Python', env['python'].split(' ')[0]),
        ('Nền tảng', env['platform']), ('PyTorch', env['torch']), ('torchvision', env['torchvision']),
        ('CUDA build', env['cuda_build']), ('ONNX Runtime', env['packages']['onnxruntime']),
        ('Transformers', env['packages']['transformers']), ('torch-pruning', env['packages']['torch-pruning']),
        ('Nguồn Torch', r'D:\thanhtrong\CT553H\.venv; thư viện bổ sung ở notebook_bundle\.venv-local')])
    setup += para('Môi trường thực thi dùng Torch 2.13.0/cu130 sẵn có, khác profile đóng gói ban đầu '
                  'Torch 2.7.1/cu128. Preflight đã thực thi một kernel CUDA; pruning và T2 có hồ sơ GPU thực tế. '
                  'Thành công của phiên này không đồng nghĩa đã tái lập kết quả trong môi trường ghim ban đầu.')
    setup += table(['Nhánh', 'Cấu hình chính'], [
        ('Ảnh', 'Seed 1024; input 256×256; EXIF → RGB → letterbox → ImageNet normalization'),
        ('Pruning', 'Global group magnitude channel; 5/10/20%; batch 8; tối đa 35 epoch; patience 7'),
        ('PTQ', 'QDQ static; INT8 per-channel weights / UINT8 activations; 200 ảnh train phân tầng; seed 1024'),
        ('CrisisMMD', 'MobileNetV3 Small frozen 576 chiều + TF-IDF; LogisticRegression; C=0,1/1/10'),
        ('Silver / synthetic frozen', 'DistilBERT multilingual 768 chiều + MobileNetV3 Large 960 chiều; LR heads'),
        ('T2 silver', '2 learning rate × 3 seed; tối đa 5 epoch; patience 2; physical batch 4, effective batch 16; max_length 128'),
        ('Suy luận ảnh', 'CPU máy tính, 1 luồng, batch=1; 3 warmup; không gồm load/preprocess/logging'),
        ('Khoảng tin cậy', '2.000 bootstrap draws; nhóm theo hồ sơ split; CI Macro-F1 chưa điều chỉnh đa so sánh')])
    setup += para('TF-IDF và LR/fusion ở đây là các mô hình tuyến tính trên đặc trưng đã trích, không có tầng '
                  'tương tác chéo modality được học hoặc joint fine-tuning hai encoder. Các nhánh trích đặc trưng '
                  'frozen chạy CPU 4 luồng; GPU không hoạt động liên tục là phù hợp với thiết kế.')
    setup += refs('preflight/preflight.json', 'locked-config.json', 'image_ptq/report/quantization.json',
                  'public_fusion/outputs/training.json', 'silver_evaluation/outputs/t2-training.json')
    section('setup', '4. Môi trường và quy trình thực nghiệm', setup)

    prune_rows = []
    for x in pruning:
        p = x['pruning']
        prune_rows.append((pct(p['target_ratio']), f"{p['parameter_count_after']:,}",
            pct(1 - p['parameter_count_after'] / p['parameter_count_before']),
            x['best_epoch'], len(x['history']), pct(x['best_validation']['accuracy']),
            pct(x['best_validation']['macro_f1']), x['best_validation']['critical_error_count']))
    pr = para('Trong mỗi tỷ lệ, checkpoint được chọn theo accuracy validation, dung sai 0,005 và ưu tiên '
              'ít lỗi nặng hơn theo logic script. Sau đó, tỷ lệ được chọn giữa các ứng viên bằng '
              'Macro-F1 validation, rồi accuracy, rồi tỷ lệ cắt thấp hơn. Không dùng test để chọn trong grid mới: '
              'cả ba <code>metrics.json</code> đều có <code>final_test=null</code>.')
    pr += table(['Tỷ lệ mục tiêu', 'Tham số còn', 'Giảm tham số thực', 'Epoch tốt nhất', 'Epoch đã chạy',
                 'Val accuracy', 'Val Macro-F1', 'Lỗi nặng val'], prune_rows)
    pr += para('Tỷ lệ mục tiêu 5% không đồng nghĩa giảm 5% tổng tham số: cấu trúc nhóm kênh và các liên kết '
               'phụ thuộc dẫn đến giảm 8,70% tham số. Ngay sau cắt 5%, validation accuracy rơi từ 75,10% xuống '
               '27,63%; fine-tuning phục hồi lên 76,65%. Đây là phục hồi trên validation; test không giữ được cải thiện đó.')
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.7))
    for x, color in zip(pruning, ['#176b87', '#af7a14', '#a14b5b']):
        label = str(int(x['pruning']['target_ratio'] * 100)) + '%'
        history = x['history']
        axes[0].plot([h['epoch'] for h in history], [h['val_macro_f1'] * 100 for h in history], label=label, color=color)
        axes[1].plot([h['epoch'] for h in history], [h['train_loss'] for h in history], label=label, color=color)
    axes[0].set(xlabel='Epoch', ylabel='Validation Macro-F1 (%)', title='Validation theo epoch')
    axes[1].set(xlabel='Epoch', ylabel='Train loss', title='Loss theo epoch')
    for ax in axes:
        ax.grid(alpha=.2); ax.legend(title='Pruning')
    pr += figure(fig, 'Đường học của ba tỷ lệ pruning; điểm cuối là early stopping, không phải checkpoint được chọn.')
    pr += table(['Mô hình (test 256 ảnh)', 'Accuracy', 'Macro-F1', 'Balanced accuracy', 'Lỗi nặng',
                 'ECE', 'Brier', 'Median / P95 (ms)'], [
        (name, pct(m['accuracy']), pct(m['macro_f1']), pct(m['balanced_accuracy']),
         f"{m['critical_error_count']}/256", number(m['ece'], 4), number(m['brier_score'], 4),
         f"{m['latency_ms_median']:.2f} / {m['latency_ms_p95']:.2f}") for name, m in image.items()])
    pr += para('Pruning 5% làm accuracy giảm 5,47 đpt, Macro-F1 giảm 6,12 đpt và lỗi nặng tăng từ 3 lên 7. '
               'Median PTH giảm khoảng 2,80% (10,65 → 10,35 ms), là một phép đo đơn trên CPU; chưa có '
               'độ bất định của latency để xác nhận cải thiện ổn định. Recall high nhích từ 74,07% lên 75,93% '
               'nhưng precision high giảm từ 86,96% xuống 74,55%; các lớp khác cũng bị ảnh hưởng.')
    per_class = []
    for label in ['low', 'medium', 'high', 'non_flood']:
        a, z = image['baseline']['per_class'][label], image['structured_pruned']['per_class'][label]
        per_class.append((label, a['support'], pct(a['precision']), pct(a['recall']), pct(a['f1']),
                          pct(z['precision']), pct(z['recall']), pct(z['f1'])))
    pr += table(['Lớp', 'n test', 'P baseline', 'R baseline', 'F1 baseline', 'P pruning', 'R pruning', 'F1 pruning'], per_class)
    pr += image_pair_table(image_stats['pairs'])
    pr += para('McNemar–Holm p=0,0704 kiểm tra thay đổi đúng/sai nên chưa vượt ngưỡng 0,05; '
               'CI 95% Δ Macro-F1 là [−12,15; −0,18] đpt và không chứa 0. Hai kết quả xét hai đại lượng khác nhau '
               '(accuracy và Macro-F1), nên không mâu thuẫn. CI này chưa điều chỉnh đa so sánh; '
               'không suy ra hai mô hình tương đương hoặc pruning không làm giảm chất lượng từ p&gt;0,05.')
    pr += callout('Lưu ý khi báo cáo “nén mô hình”',
        'File baseline PTH 48,51 MiB và pruning PT 14,90 MiB là checkpoint được lưu với cấu trúc/nội dung khác nhau. '
        'Không dùng mức giảm khoảng 69% dung lượng hai checkpoint này để thay cho mức giảm tham số 8,70%. '
        'Muốn so kích thước triển khai phải dùng cùng định dạng và cùng loại nội dung. '
        'ONNX pruned đã xuất và smoke-check; bảng latency pruning ở trên là PTH, chưa phải phép đo ONNX pruned trên test.', 'warning')
    baseline_onnx = source(RUN / 'products/fe/model/Edge Ai/seed1024/export/baseline/flood_mobilenetv3_large.onnx')
    pruned_onnx = source(B / 'image_export_compare/onnx/flood_mobilenetv3_large_structured.onnx')
    pr += table(['Artifact cùng định dạng ONNX', 'Byte', 'MiB', 'Giảm so baseline ONNX'], [
        ('Baseline FP32', f'{baseline_onnx.stat().st_size:,}', number(baseline_onnx.stat().st_size/1024**2), 'Mốc'),
        ('Pruning 5% FP32', f'{pruned_onnx.stat().st_size:,}', number(pruned_onnx.stat().st_size/1024**2),
         pct(1-pruned_onnx.stat().st_size/baseline_onnx.stat().st_size))])
    pr += para('So cùng định dạng ONNX, dung lượng giảm khoảng 8,68%, gần mức giảm tham số thực; '
               'đây là đối chiếu phù hợp hơn cho lợi ích lưu trữ của pruning.')
    pr += refs(baseline_onnx, pruned_onnx)
    pr += refs('image_pruning/selection.json', 'image_export_compare/comparison/summary.json',
               'image_export_compare/paired-statistics.json', 'image_export_compare/onnx/model_manifest.json',
               *[f'image_pruning/ratio-{ratio}/metrics.json' for ratio in ['0.050', '0.100', '0.200']])
    section('pruning', '5. Pruning ảnh: lựa chọn cấu hình và chất lượng test', pr)

    quant_content = para('PTQ được tạo mới từ ONNX baseline FP32, không phải lượng tử hóa mô hình pruning 5%. '
                         'QAT trong bảng là artifact lịch sử vì <code>run_qat=false</code>; phiên này chỉ chạy lại suy luận và phân tích nó.')
    quant_content += table(['Mô hình ONNX', 'Accuracy', 'Macro-F1', 'Recall high', 'Lỗi nặng / 256',
                           'ECE', 'Brier', 'Median / P95 ms', 'MiB'], [
        (name, pct(m['accuracy']), pct(m['macro_f1']), pct(quant_stats['metrics'][name]['recall_high']),
         m['critical_error_count'], number(m['ece'], 4), number(m['brier_score'], 4),
         f"{m['latency_ms_median']:.2f} / {m['latency_ms_p95']:.2f}", f"{m['bytes']/1024**2:.2f}") for name, m in quant.items()])
    fp, pt, qt = [quant[name] for name in ['onnx_fp32', 'ptq_int8', 'qat_int8']]
    quant_content += para(f"PTQ giảm dung lượng ONNX {pct(1 - pt['bytes']/fp['bytes'])}, giảm median latency "
                         f"{pct(1 - pt['latency_ms_median']/fp['latency_ms_median'])} "
                         f"(speedup {fp['latency_ms_median']/pt['latency_ms_median']:.2f}×). "
                         'Đổi lại Macro-F1 giảm 9,90 đpt, accuracy giảm 8,98 đpt và số lỗi nặng tăng 3 → 17. '
                         'QAT lịch sử vừa chậm hơn FP32 khoảng 2,98 lần vừa giảm Macro-F1 32,89 đpt; '
                         'file nhỏ không bảo đảm model chạy nhanh trên backend hiện tại.')
    quant_content += image_pair_table(quant_stats['pairs'])
    quant_content += para('Các chênh lệch lượng tử hóa đều có p McNemar sau Holm &lt;0,05 trong họ so sánh được lưu. '
                         'Đó là bằng chứng giảm chất lượng trên test phát triển này, dưới giả định đơn vị ghép cặp độc lập; '
                         'không khái quát thành kết luận cho mọi backend INT8 hay mọi thiết bị.')
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
    labels = ['FP32', 'PTQ mới', 'QAT lịch sử']
    for ax, values, ylabel, title in [
        (axes[0], [fp['macro_f1']*100, pt['macro_f1']*100, qt['macro_f1']*100], 'Macro-F1 (%)', 'Chất lượng test'),
        (axes[1], [fp['latency_ms_median'], pt['latency_ms_median'], qt['latency_ms_median']], 'Median latency (ms)', 'CPU ONNX, 1 luồng')]:
        bars = ax.bar(labels, values, color=['#176b87', '#af7a14', '#a14b5b'])
        ax.bar_label(bars, fmt='%.2f', padding=3); ax.set(ylabel=ylabel, title=title); ax.set_ylim(0, max(values)*1.2)
        ax.grid(axis='y', alpha=.2)
    quant_content += figure(fig, 'Đánh đổi chất lượng–độ trễ của ba ONNX; các số đo này không phải benchmark điện thoại.')
    confusions = [('FP32', quant_stats['metrics']['onnx_fp32']['confusion']),
                  ('PTQ mới', quant_stats['metrics']['ptq_int8']['confusion']),
                  ('QAT lịch sử', quant_stats['metrics']['qat_int8']['confusion'])]
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    for ax, (name, matrix) in zip(axes, confusions):
        matrix = np.array(matrix)
        ax.imshow(matrix, cmap='Blues', vmin=0, vmax=86)
        for i in range(4):
            for j in range(4): ax.text(j, i, str(matrix[i,j]), ha='center', va='center', color='white' if matrix[i,j]>45 else '#183147')
        ax.set(xticks=range(4), yticks=range(4), xticklabels=['low','med','high','non'],
               yticklabels=['low','med','high','non'], xlabel='Dự đoán', ylabel='Nhãn thật', title=name)
    quant_content += figure(fig, 'Ma trận nhầm lẫn test: hàng là nhãn thật, cột là dự đoán; non là non_flood.')
    quant_content += para('PTQ làm recall medium giảm từ 42/60=70,00% xuống 22/60=36,67%; '
                         '25/60 ảnh medium bị gán low. Với ảnh high, PTQ có 10 ca thành low và 3 ca thành non_flood. '
                         'QAT lịch sử chỉ nhận đúng 5/60 ảnh medium. “Lỗi nặng” dùng thứ tự '
                         'non_flood=0, low=1, medium=2, high=3 và khoảng cách ≥2; đây là định nghĩa kỹ thuật, '
                         'chưa được hiệu chuẩn bằng mức độ hậu quả của quyết định cứu hộ.')
    debug = js('quantization_analysis/validation-debug/activation-errors.json')
    quant_content += table(['Chẩn đoán tensor', 'Tensor lượng tử', 'Ghép được', 'Trạng thái'], [
        (name, v['n_quantized_tensors'], v['n_matched'], v['status']) for name, v in debug['reports'].items()])
    quant_content += para('Chẩn đoán chỉ dùng một ảnh validation xác định trước. PTQ ghép 123/416 tensor (~29,57%); '
                         'QAT không ghép được tensor tên tương ứng. Sai số MAE lớn nhất trong danh sách PTQ nằm ở '
                         '<code>features.10/Add_output_0</code> (2,2818). Không đủ căn cứ để kết luận layer đó là '
                         'nguyên nhân duy nhất làm giảm accuracy; thang đo activation khác nhau và phần lớn tensor chưa ghép được.')
    quant_content += refs('image_ptq/report/quantization.json', 'quantization_analysis/comparison/summary.json',
                          'quantization_analysis/paired-statistics.json', 'quantization_analysis/validation-debug/activation-errors.json')
    section('quantization', '6. PTQ, QAT lịch sử và lỗi theo lớp', quant_content)

    pub = para('Bài toán là informative / not_informative trên tiếng Anh, chỉ chọn các cặp mà nhãn ảnh và text '
               'đồng thuận. Đây là pilot có chia theo sự kiện, giới hạn dữ liệu train/dev và lọc trùng; '
               'không phải điểm benchmark CrisisMMD chính thức, không phải nhận diện yêu cầu cứu hộ tiếng Việt.')
    pub += table(['Cấu hình', 'Accuracy', 'Macro-F1', 'Recall informative', 'Balanced accuracy'], [
        (r['model'], pct(r['accuracy']), pct(r['macro_f1']), pct(r['recall_informative']), pct(r['balanced_accuracy'])) for r in public])
    pub += effects(rows('public_fusion/outputs/paired-effects.csv'), public=True)
    pub += para('Feature concatenation đạt Macro-F1 78,35%, hơn text 1,75 đpt và image 2,16 đpt. '
                'Cả ba CI chênh lệch đều chứa 0; chỉ nên mô tả xu hướng tăng, chưa xác nhận fusion vượt trội. '
                'CI được bootstrap theo nhóm trùng trong một sự kiện test, không phải CI cho quần thể sự kiện thiên tai.')
    pub += para('Khi che ảnh của mô hình concat, recall informative rơi từ 86,81% xuống 6,04%, dù accuracy '
                'vẫn 75,46% vì test có 519 mẫu not_informative và 182 informative. Che text còn Macro-F1 72,77%. '
                'Các phép che đầu vào là kiểm tra độ nhạy của mô hình đã huấn luyện, có thay đổi phân phối; '
                'không đồng nhất với huấn luyện lại một mô hình đơn modality.')
    pub += para('Baseline majority được học từ train dự đoán informative cho toàn bộ test, đạt accuracy 25,96% '
                'và recall 100%. Điều này minh họa lệch phân bố train–test và việc một metric đơn lẻ có thể gây hiểu nhầm. '
                'Verifier public báo PASS 24/24 kiểm tra trong phạm vi pilot.')
    pub += refs('public_fusion/outputs/metrics.csv', 'public_fusion/outputs/paired-effects.csv',
                'public_fusion/outputs/evaluation.json', 'public_fusion/outputs/verification.json', 'public_fusion/outputs/protocol.json')
    section('public', '7. CrisisMMD: fusion có xu hướng tăng, chưa đủ bằng chứng vượt trội', pub)

    names = [('B0','Luôn chọn lớp đa số từ train'), ('T0','TF-IDF + LogisticRegression'),
             ('T1','DistilBERT frozen + LogisticRegression'), ('I0','MobileNetV3 Large frozen + LogisticRegression'),
             ('F0','Nối TF-IDF và đặc trưng ảnh + LogisticRegression'),
             ('F1','Nối DistilBERT và đặc trưng ảnh + LogisticRegression'),
             ('P0','Trung bình xác suất T1 và I0'), ('F1_mask_image','F1 với khối đặc trưng ảnh bằng 0'),
             ('F1_mask_text','F1 với khối đặc trưng text bằng 0')]
    sil = table(['Mã', 'Ý nghĩa (áp dụng silver và synthetic)'], names)
    sil += callout('Accuracy cao có thể bỏ sót toàn bộ request',
        'Test silver chỉ có 6 request trên 59 mẫu (10,17%). B0 đạt accuracy 89,83% nhưng không phát hiện '
        'request nào. F1 đạt accuracy thấp hơn, 88,14%, nhưng phát hiện 2/6 request; vẫn bỏ sót 4/6. '
        'Chất lượng này chưa đủ để tuyên bố hệ thống cứu hộ hoạt động hiệu quả.', 'warning')
    sil += bin_table(silver)
    sil += effects(rows('silver_evaluation/outputs/paired-effects.csv'))
    sil += para('Đối chứng chính T1 được chọn bằng dev, không phải I0 dù I0 có Macro-F1 test cao hơn T1. '
                'F1 hơn T1 20,78 đpt, nhưng CI 95% [−3,93; +42,65] đpt chứa 0. '
                'Đối chiếu I0/P0 có cận dưới bằng 0 theo dữ liệu lưu; không xem đó là bằng chứng tăng chắc chắn. '
                'Các CI chưa điều chỉnh đa so sánh và chỉ có 59 nhóm trong một sự kiện.')
    sil += para('Với F1: TN=50, FP=3, FN=4, TP=2. Precision request 40,00% nghĩa là 2/5 cảnh báo request đúng '
                'theo nhãn AI; recall 33,33% nghĩa là phát hiện 2/6 ca request. Chỉ một mẫu request đổi kết quả '
                'đã làm recall thay đổi 16,67 đpt. Vì nhãn do AI dựa trên text, mô hình ảnh và fusion đang được '
                'chấm theo đích mang tính văn bản, chưa phải nhãn độc lập về tính phù hợp của cặp ảnh–text.')
    sil += para('F1_mask_image trở về dự đoán lớp đa số, còn F1_mask_text đạt Macro-F1 59,48%. '
                'Điều này cho thấy quyết định của head F1 nhạy với cách ghép đặc trưng trong pilot, '
                'nhưng chưa chứng minh cơ chế bổ trợ đa phương thức tổng quát. Verifier silver đạt 10/10 kiểm tra.')
    sil += refs('silver_evaluation/outputs/metrics.csv', 'silver_evaluation/outputs/paired-effects.csv',
                'silver_evaluation/outputs/evaluation.json', 'silver_evaluation/outputs/verification.json',
                'silver_evaluation/outputs/training.json')
    section('silver', '8. Silver tiếng Việt: mất cân bằng lớp và độ bất định lớn', sil)

    tuning = para('Có huấn luyện encoder thực sự trên CUDA: DistilBERT multilingual có 134.735.618 tham số '
                  'trainable, không chỉ huấn luyện một head tuyến tính. Sáu ứng viên là hai learning rate '
                  '(10⁻⁵ và 2×10⁻⁵) × ba seed (17, 29, 43); tổng 22 epoch, tối đa 5 epoch mỗi ứng viên.')
    tuning += table(['Learning rate', 'Seed', 'Epoch tốt nhất', 'Epoch chạy', 'Dev Macro-F1', 'Thời gian ứng viên (s)'], [
        (r['learning_rate'], r['seed'], r['best_epoch'], r['epochs_run'], pct(r['dev_macro_f1']), number(r['elapsed_seconds'])) for r in t2grid])
    tuning += para('Chọn learning rate 2×10⁻⁵ vì Macro-F1 dev trung bình ba seed là 62,22%, '
                  'so với 44,84% ở 10⁻⁵. Giữ cả ba seed được chọn và đánh giá cùng 59 ID test; '
                  'không chọn seed bằng test.')
    tuning += bin_table(t2rows)
    tuning += para('Macro-F1 test trung bình ba seed là 52,29%, khoảng min–max 51,37–54,11%; '
                  'accuracy trung bình 78,53%, precision request 13,89%, recall request 22,22%. '
                  'Đây là trung bình của ba metric seed, không phải metric của một ensemble và không phải '
                  'CI 95%. Các seed dùng cùng tập test nên không tạo thêm ba tập dữ liệu độc lập.')
    tuning += para('So mô tả trên cùng test: T2 trung bình cao hơn T1 frozen 8,16 đpt Macro-F1 nhưng thấp hơn '
                  'F1 frozen 12,62 đpt. Chưa có kiểm định ghép cặp T2–F1 hoặc T2–T1 được lưu, nên không tuyên bố '
                  'mức cải thiện có ý nghĩa thống kê. Việc dev cao hơn test có thể gợi ý hạn chế khái quát hóa, '
                  'nhưng riêng các số liệu này không xác định được nguyên nhân là overfitting, nhiễu nhãn hay khác biệt sự kiện.')
    updated = js('silver_evaluation/outputs/encoder-update-check.json')
    tuning += table(['Seed chọn', 'Tensor kiểm tra', 'Max |Δ weight|'], [
        (v['seed'], v['encoder_tensor'], f"{v['max_abs_change']:.8f}") for v in updated['checks']])
    tuning += para('Ba tensor kiểm tra đều thay đổi khác 0, xác nhận backbone đã được cập nhật trong mỗi model '
                  'được chọn. Kiểm tra một tensor không xác nhận chất lượng nhãn hoặc hiệu quả ứng dụng. '
                  'Receipt T2 ghi thời gian training 39,09 giây và tổng tới đánh giá test 42,01 giây; '
                  'stage silver_t2 khoảng 50,38 giây gồm kiểm encoder và thao tác phụ.')
    tuning += refs('silver_evaluation/outputs/t2-training.json', 'silver_evaluation/outputs/t2-evaluation.json',
                   'silver_evaluation/outputs/t2-model-selection.csv', 'silver_evaluation/outputs/t2-metrics.csv',
                   'silver_evaluation/outputs/encoder-update-check.json')
    section('tuning', '9. Fine-tuning T2: encoder cập nhật thật, chất lượng chưa vượt fusion frozen', tuning)

    syn = callout('Điểm synthetic không xác nhận năng lực cứu hộ',
        'Nhãn được tạo từ khuôn câu; ảnh không được xem để viết câu hay gán request. '
        'Đây là SYNTHETIC_UNPAIRED / TECHNICAL_PIPELINE_TEST_ONLY, không có human gold. '
        'Điểm 100% trên bài toán này không được dùng làm độ chính xác NLP tiếng Việt ngoài thực tế.', 'warning')
    syn += bin_table(synthetic)
    syn += effects(rows('synthetic_evaluation/outputs/paired-effects.csv'))
    predictions = rows('synthetic_evaluation/outputs/predictions.csv')
    pred_by = defaultdict(dict)
    for r in predictions:
        pred_by[r['model']][r['image_id']] = r['predicted_label']
    agreement = sum(pred_by['T1'][key] == pred_by['F1'][key] for key in pred_by['T1']) / len(pred_by['T1'])
    syn += para(f'T0 và F0 đạt 100% test; T1 và F1 cùng Macro-F1 96,87%, '
                f'đồng thuận nhãn {pct(agreement)} trên cùng 256 ID. '
                'F1−T1 bằng 0,00 đpt với CI [−1,56; +1,57] đpt: chưa có bằng chứng thêm ảnh giúp hơn text-only. '
                'I0 chỉ đạt Macro-F1 51,46%, phù hợp việc ảnh không mang nhãn request được định nghĩa từ khuôn câu.')
    syn += para('Che ảnh trong F1 còn làm Macro-F1 tăng lên 99,22%, trong khi che text giảm còn 33,33% '
                '(dự đoán lớp đa số). Các quan sát này phù hợp nhiệm vụ dựa trên text; không chứng minh ảnh gây hại '
                'trong dữ liệu cứu hộ thật. F1 hơn I0/P0 trên synthetic là kết quả trong phạm vi khuôn câu, '
                'không phải bằng chứng fusion cứu hộ hiệu quả.')
    syn += para('Train/dev/test dùng các khuôn riêng và giữ nhóm ảnh, nhưng vẫn chia sẻ miền ngôn ngữ tự soạn. '
                'Việc giữ template riêng không loại bỏ các dấu hiệu từ vựng/ngữ nghĩa dễ học giữa các split. '
                'Không có phân tích rò rỉ template bổ sung trong báo cáo này. Verifier đạt 9/9 kiểm tra, '
                'gồm metric độc lập và phát lại 2.000 bootstrap draws.')
    syn += refs('synthetic_evaluation/outputs/metrics.csv', 'synthetic_evaluation/outputs/paired-effects.csv',
                'synthetic_evaluation/outputs/evaluation.json', 'synthetic_evaluation/outputs/verification.json',
                'synthetic_evaluation/outputs/protocol.json')
    section('synthetic', '10. Synthetic: pipeline chạy đúng, lợi ích fusion chưa được chứng minh', syn)

    history_pr = js('historical_analysis/pruning-paired-statistics.json')
    history_q = js('historical_analysis/quantization-paired-statistics.json')
    history = table(['Artifact được phân tích', 'Macro-F1', 'Nguồn bằng chứng'], [
        ('Pruning ONNX lịch sử', pct(history_pr['metrics']['structured_onnx']['macro_f1']), 'CSV dự đoán có sẵn, không phải pruning mới của phiên này'),
        ('Pruning 5% mới', pct(image['structured_pruned']['macro_f1']), 'Suy luận mới từ checkpoint được chọn của phiên 04'),
        ('QAT trong dự đoán lịch sử', pct(history_q['metrics']['qat_int8']['macro_f1']), 'CSV dự đoán có sẵn'),
        ('QAT lịch sử được suy luận lại', pct(quant['qat_int8']['macro_f1']), 'Artifact QAT có sẵn, suy luận lại trong môi trường hiện tại')])
    history += para('Không thay số 68,14% bằng 78,26% từ mô hình pruning lịch sử khi mô tả phiên mới. '
                    'QAT cũng có khác biệt giữa CSV lịch sử (42,91%) và đánh giá lại (41,37%). '
                    'Chưa có đối chiếu đầy đủ checkpoint/môi trường/quy trình để quy nguyên nhân chênh lệch đó. '
                    'Báo cáo ưu tiên các dự đoán mới đã hash-bind và trình bày lịch sử thành bằng chứng riêng.')
    history += refs('historical_analysis/pruning-paired-statistics.json', 'historical_analysis/quantization-paired-statistics.json',
                    'image_export_compare/comparison/summary.json', 'quantization_analysis/comparison/summary.json')
    section('historical', '11. Phân biệt kết quả mới và bằng chứng lịch sử', history)

    timing = para(f'Tổng trường <code>seconds</code> của các receipt cuối là {active:.2f} giây '
                  f'(~{active/60:.2f} phút). Đây <strong>không phải thời gian từ đầu tới cuối phiên</strong>: '
                  'pruning có pause/resume và receipt cuối chỉ đo lượt gọi stage cuối; không tính đầy đủ các '
                  'khoảng chờ người dùng, sửa lỗi, giải nén, kiểm hash lặp lại và đóng ZIP ở controller.')
    timing += table(['Tỷ lệ pruning', 'Epoch đã chạy', 'Tổng thời gian epoch (s)', 'Giây / epoch trung bình'], [
        (pct(x['pruning']['target_ratio']), len(x['history']), number(sum(h['seconds'] for h in x['history'])),
         number(np.mean([h['seconds'] for h in x['history']]))) for x in pruning])
    timing += para('Tổng 71 epoch pruning có thời gian train+validation được lưu khoảng 1.120,38 giây '
                   '(18,67 phút). Lịch sử đầy đủ của mỗi tỷ lệ được dùng cho tổng này, bao gồm các epoch trước '
                   'khi pause. Không suy ra GPU utilization liên tục hay thời gian wall-clock từ con số đó.')
    timing += table(['Nhánh frozen', 'Text encoder CPU (s)', 'Image encoder CPU (s)'], [
        ('Silver 296 cặp', number(js('silver_evaluation/outputs/features.json')['text_seconds']),
         number(js('silver_evaluation/outputs/features.json')['image_seconds'])),
        ('Synthetic 1.702 cặp', number(js('synthetic_evaluation/outputs/features.json')['text_seconds']),
         number(js('synthetic_evaluation/outputs/features.json')['image_seconds']))])
    archive = RUN.parent / (RUN.name + '-results.zip')
    archive_size = archive.stat().st_size
    timing += para(f'ZIP kết quả có {archive_size:,} byte ({archive_size/10**9:.2f} GB thập phân; '
                   f'{archive_size/1024**3:.2f} GiB). ZIP lớn vì giữ các checkpoint T2 và kết quả; '
                   'nó không phải kích thước mô hình triển khai. Việc nén ZIP nhiều lần sau các stage '
                   'có thể chiếm đáng kể thời gian controller nhưng chưa được đo tách riêng.')
    timing += table(['Sự cố đã xử lý', 'Cách xử lý / tác động'], [
        ('Resolver torchvision', 'Ghim 0.28.0+cu130 phù hợp Torch 2.13.0; không thay CUDA/Torch CT553H'),
        ('Thiếu stat trong bootstrap', 'Bổ sung namespace; các thư mục giải nén dở của run cũ giữ nguyên'),
        ('Windows khóa ZIP', 'Retry; lưu snapshot tên riêng khi ZIP trước đang bị khóa; không dừng training'),
        ('Log chiếm output-dir pruning', 'Chuyển process log sang thư mục ratio-…-process riêng'),
        ('Thiếu thư mục classifiers silver', 'Tạo models; kiểm hash cache; chạy lại riêng head training; giữ receipt lỗi và audit repair'),
        ('Pause/resume', 'Đã kiểm thực tế epoch 2 → tiếp tục epoch 3 → pause epoch 6, phục hồi optimizer/scaler/scheduler/RNG')])
    timing += para('Không coi repair là một phiên độc lập: vẫn cùng dataset/config/nguồn runner đã khóa. '
                   'Các log lỗi cũ được giữ trong audit thay vì xóa dấu vết. Báo cáo hiện tại chỉ đọc artifact, '
                   'không tải checkpoint model vào bộ nhớ, không chạy thêm inference/training và không sửa kết quả gốc.')
    timing += refs(HERE / 'local-validation-20261110.json', HERE / 'local-repair-20261110.json',
                   'image_pruning/ratio-0.050/metrics.json', 'image_pruning/ratio-0.100/metrics.json',
                   'image_pruning/ratio-0.200/metrics.json')
    section('execution', '12. Thời gian, dung lượng và tính toàn vẹn quá trình chạy', timing)

    decisions = table(['Vấn đề', 'Kết luận từ phiên này', 'Bước tiếp theo hợp lý'], [
        ('Mốc mô hình ảnh', 'FP32 giữ chất lượng cao nhất trong các biến thể ảnh được đánh giá mới',
         'Giữ làm mốc phát triển; thiết lập tiêu chí chấp nhận trước khi thay model'),
        ('Pruning 5%', 'Giảm tham số nhưng Macro-F1 và lỗi nặng kém hơn; tốc độ tăng nhỏ',
         'Chưa thay baseline; chỉ thử protocol mới trên validation, sau đó khóa và dùng test mới'),
        ('PTQ', 'Tốt hơn về kích thước/latency CPU, xấu hơn về chất lượng',
         'Kiểm calibration, preprocessing và toán tử trên validation; không tuning bằng test đã báo cáo'),
        ('QAT', 'Artifact lịch sử hiện kém cả chất lượng lẫn tốc độ',
         'Đối chiếu checkpoint/export/backend trước khi quyết định bật QAT mới; không suy nguyên nhân từ một tensor'),
        ('CrisisMMD fusion', 'Có xu hướng tăng nhỏ; CI chứa 0',
         'Cần lặp trên nhiều sự kiện độc lập theo protocol mới trước kết luận tổng quát'),
        ('Silver', '6 positive test, nhãn AI; recall request thấp',
         'Ưu tiên dữ liệu tiếng Việt có nhãn độc lập và đủ request; đánh giá bằng recall/precision và lỗi cụ thể'),
        ('Synthetic', 'Chứng minh đường đi dữ liệu và metric hoạt động',
         'Giữ vai trò kiểm kỹ thuật; không dùng điểm 100% để chứng minh cứu hộ thực tế'),
        ('Thiết bị và vận hành', 'Chưa có evidence Android/SMS/mạng/pin/RAM',
         'Kiểm trên thiết bị và điều kiện sử dụng thật theo protocol riêng, nếu được tổ chức thực hiện')])
    decisions += callout('Câu kết luận có thể dùng trong báo cáo nghiên cứu',
        'Trong phiên phát triển local-20261110-04, pipeline đã hoàn tất các nhánh được bật và lưu đầy đủ '
        'dự đoán để đối chiếu. Pruning và lượng tử hóa hiện tại chưa bảo toàn chất lượng của baseline ảnh. '
        'Fusion trên CrisisMMD và silver có một số chênh lệch điểm ước lượng thuận lợi, nhưng các giới hạn '
        'về khoảng tin cậy, sự kiện test và nguồn nhãn chưa cho phép khẳng định ưu thế tổng quát hoặc '
        'hiệu quả cứu hộ thực tế. Kết quả synthetic chỉ xác nhận tác vụ khuôn câu và pipeline kỹ thuật.', 'important')
    decisions += para('Các đề xuất trên là diễn giải từ artifact của phiên này; báo cáo không thực hiện thêm '
                      'lựa chọn mô hình bằng test, không điều chỉnh nhãn và không thay protocol đã khóa.')
    section('decisions', '13. Kết luận và thứ tự ưu tiên sau thực nghiệm', decisions)

    audit = para(f'Khi sinh báo cáo, đã đối chiếu SHA-256 của <strong>{checked}</strong> tham chiếu artifact '
                 f'trong các receipt stage (có thể trùng đường dẫn giữa các stage). Đã tính lại confusion matrix, '
                 f'accuracy và Macro-F1 cho <strong>{len(INDEPENDENT)}</strong> cấu hình/seed từ CSV dự đoán; '
                 'precision/recall request cũng được đối chiếu cho silver và synthetic. Tất cả khớp trong '
                 'sai số số học. Kiểm tra này không chạy lại bootstrap hoặc suy luận model; các CI/p-value '
                 'được lấy từ hồ sơ thống kê đã lưu, còn verifier của từng pipeline đã có receipt PASS.')
    audit += table(['Thuật ngữ', 'Cách hiểu'], [
        ('Accuracy', 'Tỷ lệ đúng trên toàn bộ mẫu; bị ảnh hưởng bởi mất cân bằng lớp'),
        ('Macro-F1', 'Trung bình F1 của các lớp với trọng số bằng nhau'),
        ('Precision / recall request', 'TP/(TP+FP) và TP/(TP+FN); mẫu số 0 được quy ước trả 0 trong pipeline'),
        ('ECE / Brier', 'Chỉ số sai lệch xác suất; thấp hơn tốt hơn trong cùng định nghĩa và dữ liệu; không thay accuracy/recall'),
        ('CI 95%', 'Khoảng bootstrap có điều kiện theo dữ liệu/nhóm hiện có; không bảo đảm khái quát sang sự kiện mới'),
        ('McNemar–Holm', 'Kiểm thay đổi đúng/sai ghép cặp; Holm áp dụng trong họ tương phản đã liệt kê'),
        ('MiB / GB', 'MiB = 2²⁰ byte; GB thập phân = 10⁹ byte; bảng log ghi MB nhưng tính theo MiB'),
        ('PASS verifier', 'Nhất quán dữ liệu, ID, hash và cách tính trong phạm vi kiểm tra; không phải human validation')])
    audit += para('Ba điểm dễ đọc nhầm trong metadata: (1) preflight synthetic có <code>model_training=NOT_RUN</code> '
                  'vì được chụp trước huấn luyện; trạng thái cuối lấy ở stage/evaluation. (2) '
                  '<code>training.json</code> của frozen silver có T2 NOT_RUN là snapshot của nhánh frozen; '
                  '<code>t2-training.json</code> và stage silver_t2 xác nhận T2 đã chạy. (3) Manifest ONNX pruned '
                  '<code>artifacts_complete=false</code> do code yêu cầu cả hash ONNX lẫn PTE, trong khi PTE không được bật; '
                  'không đồng nghĩa export ONNX thất bại.')
    audit += '<details><summary>Xem toàn bộ cấu hình đã khóa</summary><pre>' + esc(json.dumps(config, ensure_ascii=False, indent=2)) + '</pre></details>'
    audit += refs('image_export_compare/onnx/model_manifest.json',
                  RUN / 'products/fe/tools/convert_model.py', 'silver_evaluation/outputs/training.json',
                  'silver_evaluation/outputs/t2-training.json', 'preflight/preflight.json')
    source_rows = []
    for path, (idx, digest) in SOURCES.items():
        relative = path.relative_to(HERE).as_posix()
        source_rows.append(f'<tr id="src-{idx}"><td>S{idx:02d}</td><td><a href="{esc(relative)}">{esc(relative)}</a></td>'
                           f'<td class="hash">{digest}</td></tr>')
    audit += '<h3>Danh mục nguồn và SHA-256</h3><p>Mọi nguồn là file local của phiên chạy; không dùng số liệu từ web. '
    audit += 'Các bảng/biểu đồ được nhúng trong file HTML này. Link nguồn chỉ hoạt động khi giữ cấu trúc thư mục dự án.</p>'
    audit += '<div class="table-wrap"><table class="sources"><thead><tr><th>Mã</th><th>File</th><th>SHA-256</th></tr></thead><tbody>'
    audit += ''.join(source_rows) + '</tbody></table></div>'
    section('audit', '14. Kiểm tra báo cáo, chú giải và nguồn đối chiếu', audit)

    toc = ''.join(f'<a href="#{key}">{esc(title)}</a>' for key, title, _ in sections)
    css = '''
    :root{--ink:#183147;--muted:#596777;--teal:#176b87;--line:#dce4eb;--paper:#fff}
    *{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#eef2f6;color:var(--ink);font:16px/1.65 "Segoe UI",Arial,sans-serif}
    .cover{background:#132f44;color:white;padding:58px max(28px,calc((100vw - 1120px)/2));border-bottom:7px solid #39b6aa}
    .eyebrow{color:#8ee0d5;letter-spacing:.11em;text-transform:uppercase;font-size:13px;font-weight:700}
    h1{font-size:38px;line-height:1.22;max-width:950px;margin:14px 0 20px;letter-spacing:-.02em}.cover p{max-width:900px;color:#dbe6ee}
    .meta{display:flex;gap:12px;flex-wrap:wrap;font-size:13px}.meta span{background:#25455d;border:1px solid #527185;padding:5px 12px;border-radius:5px}
    main{max-width:1200px;margin:30px auto 70px;padding:0 24px}nav,section{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:28px 34px;margin:22px 0}
    nav .links{columns:2;column-gap:32px}nav a{display:block;break-inside:avoid;margin:5px 0;font-size:14px;text-decoration:none}
    h2{font-size:25px;line-height:1.35;margin:0 0 20px;border-bottom:2px solid #d8ecef;padding-bottom:14px}h3{font-size:19px;margin-top:30px}
    p{margin:14px 0}a{color:#126b8b;text-decoration:underline;text-underline-offset:3px}.table-wrap{overflow-x:auto;margin:22px 0}
    table{border-collapse:collapse;width:100%;font-size:13px;line-height:1.5}th{background:#edf4f7;color:#24495d;text-align:left;font-weight:700}
    th,td{padding:11px 12px;border-bottom:1px solid var(--line);vertical-align:top}tr:nth-child(even) td{background:#fafcfd}td{font-variant-numeric:tabular-nums}
    caption{font-weight:700;text-align:left;margin-bottom:10px}aside{border-left:4px solid var(--teal);padding:16px 20px;background:#eef8fa;margin:22px 0;border-radius:0 6px 6px 0}
    aside p{margin:8px 0 0}.warning{background:#fff7e8;border-color:#bb861c}.important{background:#eef5f8;border-color:#176b87}
    .source{font-size:12px;color:var(--muted)}figure{margin:26px 0}figure img{width:100%;height:auto}figcaption{font-size:13px;color:var(--muted);margin:8px 0}
    code{background:#edf2f5;padding:2px 5px;border-radius:3px;font-size:.89em}pre{background:#f4f7fa;padding:20px;overflow:auto;font:13px/1.5 Consolas,monospace}
    summary{cursor:pointer;font-weight:700}.sources{font-size:11px;table-layout:fixed}.sources th:first-child{width:50px}.sources th:nth-child(2){width:52%}.sources td{overflow-wrap:anywhere}.hash{font-family:Consolas,monospace}
    footer{color:var(--muted);font-size:12px;text-align:center;padding:20px}.print-button{border:1px solid #8eb0c3;background:#25455d;color:white;padding:9px 15px;border-radius:5px;cursor:pointer;font:inherit}
    @media(max-width:700px){h1{font-size:28px}main{padding:0 12px}nav,section{padding:22px 18px}nav .links{columns:1}h2{font-size:21px}}
    @media print{body{background:white;font-size:10pt}main{max-width:none;margin:0;padding:0}.cover{padding:25px;color:#183147;background:white;border-bottom:3px solid #176b87}.cover p{color:#364e5e}h1{font-size:25pt}.meta span{color:#183147;background:#edf4f7;border-color:#dce4eb}nav{display:none}section{border:none;border-radius:0;padding:15px 0;margin:10px 0;break-before:auto}h2,h3{break-after:avoid}figure,tr,aside{break-inside:avoid}figure img{max-height:16cm;object-fit:contain}table{font-size:8pt}.sources{font-size:6.8pt}.table-wrap{overflow:visible}.print-button{display:none}a{color:inherit;text-decoration:none}details{display:block}footer{font-size:8pt}}
    '''
    content = f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Báo cáo phân tích kết quả NCKH2 — local-20261110-04</title><style>{css}</style></head><body>
    <header class="cover"><div class="eyebrow">NCKH2 · Phân tích thực nghiệm · 10/11/2026</div>
    <h1>Báo cáo phân tích chi tiết<br>kết quả phiên local-20261110-04</h1>
    <p>Ảnh ngập lụt, pruning, lượng tử hóa, CrisisMMD, silver tiếng Việt và bộ synthetic. Phân tích từ artifact đã lưu, có đối chiếu dự đoán và hồ sơ nguồn.</p>
    <div class="meta"><span>Trạng thái: COMPLETED</span><span>RTX 5060 Laptop · Torch 2.13.0+cu130</span><span>{len(INDEPENDENT)} cấu hình/seed được đối chiếu metric</span></div>
    <p style="font-size:13px">Lập báo cáo: {created} · Múi giờ Asia/Taipei (UTC+08:00)</p>
    <button class="print-button" onclick="window.print()">In hoặc lưu PDF từ trình duyệt</button></header>
    <main><nav><h2>Mục lục</h2><div class="links">{toc}</div></nav>{''.join(s[2] for s in sections)}</main>
    <footer>Phân tích chỉ đọc · Không chạy lại model hoặc chỉnh sửa kết quả gốc · File độc lập, biểu đồ được nhúng sẵn</footer></body></html>'''
    OUT.write_text(content, encoding='utf-8')
    assert content.count('<section ') == 14
    assert content.count('<figure>') == 3
    assert 'http://' not in content and 'https://' not in content
    print(json.dumps({'report': str(OUT), 'bytes': OUT.stat().st_size,
                      'receipt_artifact_references_verified': checked,
                      'metric_configurations_verified': len(INDEPENDENT),
                      'source_files': len(SOURCES), 'sections': 14, 'embedded_figures': 3}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
