"""Compare ONNX/PTE within each saved phone/model condition; no new inference."""
import csv
from statistics import mean

from export_phone_benchmarks import OUT, DEVICES, main as export_benchmarks, write_csv


def read(name):
    with (OUT / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def rounded(rows):
    return [{k: round(v, 4) if isinstance(v, float) else v for k, v in r.items()} for r in rows]


def main():
    export_benchmarks()
    rows, predictions = read('summary.csv'), read('predictions.csv')
    quality = ['accuracy', 'macro_precision', 'macro_recall', 'macro_f1',
               'precision_high', 'recall_high', 'f1_high', 'ordinal_mae', 'ordinal_rmse']
    comparisons = []
    for seed in ['159', '1024']:
        for variant in ['baseline', 'pruning']:
            for device in DEVICES:
                pair = [r for r in rows if (r['seed'], r['variant'], r['device']) == (seed, variant, device)]
                assert len(pair) == 2 and {r['runtime'] for r in pair} == {'onnx', 'pte'}
                a, b = [next(r for r in pair if r['runtime'] == t) for t in ['onnx', 'pte']]
                assert all(a[k] == b[k] for k in ['checkpoint_sha256', 'split_sha256', 'device_model', 'latency_scope'])
                pa, pb = [{r['id']: r for r in predictions if r['source_json'] == x['source_json']} for x in [a, b]]
                assert set(pa) == set(pb) and len(pa) == 256
                assert all(pa[k]['truth'] == pb[k]['truth'] for k in pa)
                agreement = sum(pa[k]['prediction'] == pb[k]['prediction'] for k in pa) / len(pa)
                assert agreement == 1 and all(float(a[k]) == float(b[k]) for k in quality)
                row = dict(seed=int(seed), model=variant, device=device, samples_per_runtime=256,
                           top1_agreement_pct=agreement * 100)
                row.update({k + '_both' + ('_pct' if k not in ['ordinal_mae', 'ordinal_rmse'] else ''):
                            float(a[k]) * (100 if k not in ['ordinal_mae', 'ordinal_rmse'] else 1) for k in quality})
                for label, source in [('mean', 'mean_ms'), ('p50', 'p50_ms'), ('p95', 'p95_ms')]:
                    row['onnx_' + label + '_ms'] = float(a[source])
                    row['pte_' + label + '_ms'] = float(b[source])
                row['p50_speedup_onnx_over_pte'] = float(a['p50_ms']) / float(b['p50_ms'])
                row['p50_reduction_pct'] = 100 * (1 - float(b['p50_ms']) / float(a['p50_ms']))
                row['pte_faster_mean_p50_p95'] = all(float(b[k]) < float(a[k]) for k in ['mean_ms', 'p50_ms', 'p95_ms'])
                row.update(onnx_source_json=a['source_json'], pte_source_json=b['source_json'])
                comparisons.append(row)
    assert len(comparisons) == 16
    write_csv('onnx_pte_comparison.csv', rounded(comparisons))

    aggregates = []
    for seed in ['159', '1024']:
        for variant in ['baseline', 'pruning']:
            for runtime in ['onnx', 'pte']:
                group = [r for r in rows if (r['seed'], r['variant'], r['runtime']) == (seed, variant, runtime)]
                assert len(group) == 4
                row = dict(seed=int(seed), model=variant, runtime=runtime, device_count=4,
                           unique_test_images=256)
                row.update({k + ('_pct' if k not in ['ordinal_mae', 'ordinal_rmse'] else '_mean'):
                            mean(float(r[k]) for r in group) * (100 if k not in ['ordinal_mae', 'ordinal_rmse'] else 1)
                            for k in quality})
                row.update(mean_latency_ms=mean(float(r['mean_ms']) for r in group),
                           mean_p50_ms=mean(float(r['p50_ms']) for r in group),
                           mean_p95_ms=mean(float(r['p95_ms']) for r in group),
                           preferred_for_project=(seed, variant, runtime) == ('1024', 'pruning', 'pte'))
                aggregates.append(row)
    write_csv('runtime_summary.csv', rounded(aggregates))
    selected = [r for r in comparisons if r['seed'] == 1024 and r['model'] == 'pruning']
    lines = ['# Đối chiếu ONNX và ExecuTorch/PTE trên điện thoại', '',
             '## Bảng chính: seed 1024 pruning', '',
             '| Điện thoại | ONNX P50 (ms) | PTE P50 (ms) | ONNX P95 (ms) | PTE P95 (ms) | Tăng tốc P50 | Macro-F1 cả hai (%) |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for r in selected:
        lines.append(f"| {r['device']} | {r['onnx_p50_ms']:.3f} | {r['pte_p50_ms']:.3f} | "
                     f"{r['onnx_p95_ms']:.3f} | {r['pte_p95_ms']:.3f} | {r['p50_speedup_onnx_over_pte']:.2f}× | {r['macro_f1_both_pct']:.2f} |")
    lines += ['', '## Chất lượng và thời gian trung bình của seed 1024 pruning', '',
              '| Runtime | Accuracy (%) | Precision macro (%) | Recall macro (%) | F1 macro (%) | MAE (mức) | RMSE (mức) | TB P50 (ms) | TB P95 (ms) |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in aggregates:
        if r['seed'] == 1024 and r['model'] == 'pruning':
            lines.append(f"| {r['runtime']} | {r['accuracy_pct']:.2f} | {r['macro_precision_pct']:.2f} | "
                         f"{r['macro_recall_pct']:.2f} | {r['macro_f1_pct']:.2f} | {r['ordinal_mae_mean']:.4f} | "
                         f"{r['ordinal_rmse_mean']:.4f} | {r['mean_p50_ms']:.3f} | {r['mean_p95_ms']:.3f} |")
    lines += ['', '## Lựa chọn và phạm vi kết luận', '',
              '- Chọn **MobileNetV3-Large seed 1024 pruning + ExecuTorch/PTE** cho bước triển khai nguyên mẫu tiếp theo: macro-F1 cao nhất trong bốn cấu hình model đã so sánh, và PTE nhanh hơn ONNX trên cả bốn máy trong các phiên đã lưu.',
              f"- Trong toàn bộ 16 cặp máy/model (hai seed × hai biến thể × bốn máy), PTE có mean/P50/P95 thấp hơn ONNX ở {sum(r['pte_faster_mean_p50_p95'] for r in comparisons)}/16 cặp. Dự đoán top-1 ONNX/PTE trùng 256/256 trong mỗi cặp, nên các chỉ số chất lượng liệt kê bằng nhau. Không khẳng định vector xác suất giống tuyệt đối.",
              '- Với seed 1024 pruning, PTE có Precision high 80,85%, Recall high 87,96% và F1 high 84,25%, bằng ONNX trên bộ ảnh đã kiểm tra. Lựa chọn model theo macro-F1 không có nghĩa thắng mọi metric; baseline 1024 có RMSE và số lỗi nặng trung bình thấp hơn.',
              '- Thời gian bao gồm giải mã ảnh, tiền xử lý và suy luận trong classifyImage, loại trừ đọc ảnh package; đây không phải thời gian toàn luồng gửi báo cáo. Có năm warmup và 256 ảnh test mỗi phiên.',
              '- Tăng tốc P50 = ONNX P50 / PTE P50 trong cùng máy/model. TB P50/P95 là trung bình percentile của bốn máy, không phải percentile gộp hoặc thời gian cho mọi điện thoại.',
              '- Chỉ có một phiên cho mỗi máy/model/runtime, thời điểm chạy khác nhau, chưa kiểm soát đầy đủ nhiệt độ/tải. Chưa có kiểm định thống kê, kết quả pin/RAM hay dữ liệu camera độc lập. Không suy ra PTE luôn nhanh hơn trên thiết bị khác.',
              '- MAE/RMSE dùng non_flood=0, low=1, medium=2, high=3, đơn vị mức phân loại; thấp hơn tốt hơn. Trong bảng tổng hợp, đây là trung bình MAE/RMSE từng máy, không gộp các lần dùng lại ảnh thành mẫu độc lập.',
              '- onnx_pte_comparison.csv: 16 cặp đầy đủ, các cột *_both là chỉ số chung của hai runtime đã xác nhận trùng dự đoán; thời gian và nguồn JSON tách riêng. runtime_summary.csv: tám hàng seed/model/runtime, gồm cả chỉ số lớp high và mean/P50/P95.',
              '- Nguồn: summary.csv và predictions.csv, truy về JSON qua source_json. Tái xuất bằng `python report/scripts/compare_phone_runtimes.py`. Không chạy lại suy luận, không đổi model triển khai, không điền mục điện thoại đang để trống trong báo cáo.', '']
    (OUT / 'onnx_pte_comparison.md').write_text('\n'.join(lines), encoding='utf-8')
    print('\n'.join(lines[:11]))
    print('Complete pairs:', len(comparisons), 'PTE faster:', sum(r['pte_faster_mean_p50_p95'] for r in comparisons))


if __name__ == '__main__':
    main()
