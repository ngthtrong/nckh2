"""Compare saved phone benchmarks in two stages, with explicit descriptive criteria."""
import csv
from collections import Counter
from statistics import mean

from export_phone_benchmarks import OUT, DEVICES, main as export_benchmarks, write_csv


def read(name):
    with (OUT / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def main():
    export_benchmarks()
    summary, classes, predictions = [read(n) for n in ['summary.csv', 'class_metrics.csv', 'predictions.csv']]
    severity = {'non_flood': 0, 'low': 1, 'medium': 2, 'high': 3}
    aggregates = []
    for seed in ['159', '1024']:
        for variant in ['baseline', 'pruning']:
            group = [r for r in summary if r['seed'] == seed and r['variant'] == variant]
            assert len(group) == 8
            assert {(r['device'], r['runtime']) for r in group} == {(d, t) for d in DEVICES for t in ['onnx', 'pte']}
            sources = {r['source_json'] for r in group}
            assert len(sources) == 8 and len({r['split_sha256'] for r in group}) == 1
            ps = [r for r in predictions if r['source_json'] in sources]
            assert len(ps) == 8 * 256
            assert set(Counter(r['source_json'] for r in ps).values()) == {256}
            by_run = [{r['id'] for r in ps if r['source_json'] == source} for source in sources]
            assert all(ids == by_run[0] for ids in by_run)
            high = [r for r in classes if r['source_json'] in sources and r['label'] == 'high']
            assert len(high) == 8
            aggregates.append(dict(
                seed=int(seed), model=variant,
                accuracy_pct=100 * mean(float(r['accuracy']) for r in group),
                macro_precision_pct=100 * mean(float(r['macro_precision']) for r in group),
                macro_recall_pct=100 * mean(float(r['macro_recall']) for r in group),
                macro_f1_pct=100 * mean(float(r['macro_f1']) for r in group),
                precision_high_pct=100 * mean(float(r['precision']) for r in high),
                recall_high_pct=100 * mean(float(r['recall']) for r in high),
                f1_high_pct=100 * mean(float(r['f1']) for r in high),
                ordinal_mae_mean=mean(float(r['ordinal_mae']) for r in group),
                ordinal_rmse_mean=mean(float(r['ordinal_rmse']) for r in group),
                severe_errors_mean_per_256=sum(abs(severity[r['truth']] - severity[r['prediction']]) >= 2 for r in ps) / 8,
                onnx_mean_p50_ms=mean(float(r['p50_ms']) for r in group if r['runtime'] == 'onnx'),
                pte_mean_p50_ms=mean(float(r['p50_ms']) for r in group if r['runtime'] == 'pte'),
                onnx_mean_p95_ms=mean(float(r['p95_ms']) for r in group if r['runtime'] == 'onnx'),
                pte_mean_p95_ms=mean(float(r['p95_ms']) for r in group if r['runtime'] == 'pte'),
                selected_within_seed=False, selected_final=False))

    # Quality-first descriptive selection; device timing remains a separate tradeoff.
    key = lambda r: (r['macro_f1_pct'], r['accuracy_pct'])
    steps = []
    winners = []
    for seed in [159, 1024]:
        candidates = [r for r in aggregates if r['seed'] == seed]
        winner, other = sorted(candidates, key=key, reverse=True)
        winner['selected_within_seed'] = True
        winners.append(winner)
        steps.append(dict(stage=f'within_seed_{seed}', selected=f"seed{seed}_{winner['model']}",
                          compared_with=f"seed{seed}_{other['model']}",
                          delta_macro_f1_pp=winner['macro_f1_pct'] - other['macro_f1_pct'],
                          delta_accuracy_pp=winner['accuracy_pct'] - other['accuracy_pct'],
                          criterion='macro-F1 first; Accuracy breaks ties'))
    winner, other = sorted(winners, key=key, reverse=True)
    winner['selected_final'] = True
    steps.append(dict(stage='between_seed_winners', selected=f"seed{winner['seed']}_{winner['model']}",
                      compared_with=f"seed{other['seed']}_{other['model']}",
                      delta_macro_f1_pp=winner['macro_f1_pct'] - other['macro_f1_pct'],
                      delta_accuracy_pp=winner['accuracy_pct'] - other['accuracy_pct'],
                      criterion='macro-F1 first; Accuracy breaks ties'))
    write_csv('model_comparison.csv', [{k: round(v, 4) if isinstance(v, float) else v for k, v in r.items()} for r in aggregates])
    write_csv('selection_steps.csv', [{k: round(v, 4) if isinstance(v, float) else v for k, v in r.items()} for r in steps])

    lines = [
        '# So sánh baseline và pruning: seed 159, seed 1024', '',
        'Tiêu chí lựa chọn của phân tích: ưu tiên macro-F1 trung bình; nếu bằng nhau thì ưu tiên Accuracy. '
        'Macro-Precision, macro-Recall, chỉ số lớp high, MAE/RMSE thứ bậc, lỗi nặng và độ trễ được giữ riêng để đánh giá đánh đổi. '
        'Đây không phải tiêu chí đã đăng ký trước thực nghiệm. F1 đã cân bằng Precision/Recall; Accuracy chỉ dùng khi macro-F1 bằng nhau.', '',
        '| Seed | Model | Accuracy (%) | Macro-Precision (%) | Macro-Recall (%) | Macro-F1 (%) | MAE (mức) | RMSE (mức) | Chọn trong seed |',
        '|---|---|---:|---:|---:|---:|---:|---:|---|']
    for r in aggregates:
        lines.append(f"| {r['seed']} | {r['model']} | {r['accuracy_pct']:.2f} | {r['macro_precision_pct']:.2f} | "
                     f"{r['macro_recall_pct']:.2f} | {r['macro_f1_pct']:.2f} | {r['ordinal_mae_mean']:.4f} | "
                     f"{r['ordinal_rmse_mean']:.4f} | {'Có' if r['selected_within_seed'] else ''} |")
    lines += ['', '## Lớp ngập cao và hiệu năng', '',
              '| Seed | Model | Precision high (%) | Recall high (%) | F1 high (%) | Lỗi nặng TB/256 | TB P50 ONNX (ms) | TB P50 PTE (ms) |',
              '|---|---|---:|---:|---:|---:|---:|---:|']
    for r in aggregates:
        lines.append(f"| {r['seed']} | {r['model']} | {r['precision_high_pct']:.2f} | {r['recall_high_pct']:.2f} | "
                     f"{r['f1_high_pct']:.2f} | {r['severe_errors_mean_per_256']:.2f} | "
                     f"{r['onnx_mean_p50_ms']:.2f} | {r['pte_mean_p50_ms']:.2f} |")
    lines += ['', '## Chọn theo hai bước', '']
    for step in steps:
        lines.append(f"- {step['stage']}: chọn **{step['selected']}** so với {step['compared_with']}; "
                     f"macro-F1 tăng {step['delta_macro_f1_pp']:.3f} điểm phần trăm, "
                     f"Accuracy tăng {step['delta_accuracy_pp']:.3f} điểm phần trăm.")
    lines += ['', '## Cách đọc và giới hạn', '',
              '- Precision/Recall/F1 từng lớp có sẵn trong classMetrics của JSON; macro-Precision, macro-Recall và MAE/RMSE được tính bổ sung từ dữ liệu đã lưu, không phải một lượt benchmark mới. JSON gốc được giữ nguyên.',
              '- F1_c = 2 × Precision_c × Recall_c / (Precision_c + Recall_c). Macro-F1 là trung bình F1 của bốn lớp, không phải F1 tính từ macro-Precision và macro-Recall. Macro-Precision/Recall cũng lấy trung bình bằng trọng số bốn lớp; macro-Recall bằng balanced accuracy.',
              '- Precision cao nghĩa là trong các ảnh được dự đoán thuộc một lớp, phần lớn đúng lớp đó; Recall cao nghĩa là nhận ra được phần lớn ảnh thật của lớp đó. Chọn F1 nếu coi hai loại lỗi quan trọng tương đương. Nếu muốn ưu tiên tránh bỏ sót lớp high thì cần xác định chi phí lỗi/ngưỡng chấp nhận, chọn trên validation rồi xác nhận trên dữ liệu độc lập; không tự chỉnh threshold từ test. Không thể dựng đầy đủ đường Precision–Recall cho từng lớp từ JSON chỉ có confidence của top-1, thiếu vector xác suất bốn lớp.',
              '- Ánh xạ thứ bậc: non_flood=0, low=1, medium=2, high=3. MAE = mean(|dự đoán − nhãn thật|), RMSE = sqrt(mean((dự đoán − nhãn thật)^2)); thấp hơn tốt hơn, RMSE phạt lệch nhiều mức mạnh hơn. Không dùng label_idx theo thứ tự output [low, medium, high, non_flood]. Giả định mỗi mức cách nhau một đơn vị là quy ước đánh giá, không phải mét nước hay chi phí cứu hộ.',
              '- summary.csv và CSV từng máy có MAE/RMSE riêng cho từng phiên 256 ảnh. Trong bảng bốn model, MAE/RMSE là trung bình chỉ số của tám phiên; RMSE trung bình này không phải sqrt(MSE gộp). Các phiên dùng lại ảnh nên không phải quan sát độc lập.',
              '- Nguồn: summary.csv, class_metrics.csv và predictions.csv cùng thư mục; JSON gốc được truy từ source_json. Tái xuất: `python report/scripts/compare_phone_benchmarks.py`.',
              '- Mỗi hàng là trung bình bằng trọng số của 8 phiên (4 máy × 2 runtime), cùng 256 ảnh test. Không gộp thành 2.048 ảnh độc lập. ONNX/PTE của mỗi cấu hình máy/model có dự đoán top-1 giống nhau; việc lấy trung bình hai runtime không tăng số ảnh độc lập.',
              '- TB P50/P95 là trung bình các P50/P95 của bốn máy trong cùng runtime, không phải percentile của dữ liệu gộp hay độ trễ cho một máy bất kỳ. Đối chiếu từng máy ở summary.csv; không dùng trung bình này để khẳng định ưu thế trên mọi thiết bị.',
              '- Lỗi nặng là lệch ít nhất hai mức theo thứ tự non_flood → low → medium → high, cùng định nghĩa trong compare_models.py; không phải số ca gây hậu quả cứu hộ.',
              '- Pruning seed 159 thắng về macro-F1 trên 3/4 máy; Samsung S10e có macro-F1 baseline nhỉnh hơn. Pruning seed 1024 thắng baseline về macro-F1 trên cả 4 máy.',
              '- Giữa hai bản pruning, seed 1024 có macro-F1 cao hơn trên realme 15 và Samsung S10e; seed 159 cao hơn trên Redmi Note 11 và Redmi Note 13. Vì thế kết luận cuối là ưu tiên theo trung bình bộ máy này, không phải thắng trên mọi máy.',
              '- Seed 1024 pruning có ít lợi thế Accuracy so với seed 159 pruning và có lỗi nặng trung bình cao hơn (3,25 so với 3,00); so với baseline 1024, lỗi nặng tăng từ 2,25 lên 3,25. Nếu ưu tiên ít lỗi nặng thay vì macro-F1 thì lựa chọn có thể khác.',
              '- Seed 1024 pruning có ONNX trên Redmi Note 13 P50 239,020 ms, cao hơn seed 159 pruning 176,095 ms. Chưa có lặp nhiều phiên hoặc kiểm soát nhiệt độ/tải để quy nguyên nhân; không coi pruning luôn nhanh hơn.',
              '- Chọn **seed 1024 pruning** theo tiêu chí chất lượng trên benchmark hiện có. Chênh macro-F1 chỉ khoảng 0,314 điểm phần trăm; chưa kiểm định ý nghĩa thống kê. Lựa chọn dựa trên test nên cần dữ liệu độc lập nếu muốn xác nhận chất lượng cuối cùng sau lựa chọn. Không sửa model triển khai hoặc điền mục điện thoại đang để trống trong báo cáo.', '']
    (OUT / 'model_comparison.md').write_text('\n'.join(lines), encoding='utf-8')
    print('\n'.join(lines[:12]))
    print('Selected:', winner['seed'], winner['model'])


if __name__ == '__main__':
    main()
