"""Bold descriptive optima within comparable groups, preserving displayed values."""
import re
from decimal import Decimal


def highlight_results(name, rows):
    rows = [list(map(str, row)) for row in rows]

    def number(cell):
        return Decimal(re.match(r'-?\d+(?:[.,]\d+)?', cell).group().replace(',', '.'))

    def best(cells, direction):
        values = [number(rows[r][c]) for r, c in cells]
        optimum = (max if direction == 'max' else min)(values)
        for (r, c), value in zip(cells, values):
            if value == optimum:
                # CI bounds describe uncertainty, rather than additional optima.
                rows[r][c] = re.sub(r'^(-?\d+(?:[.,]\d+)?)', r'\\textbf{\1}', rows[r][c])

    columns = {
        'image-classes': {1: 'max', 2: 'max', 3: 'max'},
        'pth_onnx_pte': {1: 'max', 2: 'max', 3: 'min', 4: 'min', 5: 'min'},
        'fp32_ptq_qat': {1: 'max', 2: 'max', 3: 'min', 4: 'min', 5: 'min'},
        'mobile-runtime': {1: 'max', 2: 'max', 3: 'min', 4: 'min', 5: 'min'},
        'rq1-benchmark': {1: 'max', 2: 'max'},
        'rq2-alignment': {1: 'max'},
        'rq2-sensitivity': {2: 'min'},
        'phone-model-quality': {1: 'max', 2: 'max', 3: 'max', 4: 'max'},
        'phone-model-tradeoffs': {1: 'max', 2: 'max', 3: 'min', 4: 'min', 5: 'min'},
    }
    for c, direction in columns.get(name, {}).items():
        best([(r, c) for r in range(len(rows))], direction)
    if name == 'pruning_st':
        for start in range(0, len(rows), 2):
            for c, direction in {1: 'max', 2: 'max', 3: 'min', 4: 'min', 5: 'min'}.items():
                best([(r, c) for r in [start, start + 1]], direction)
    if name == 'rq1-stress':
        for r in range(len(rows)):
            best([(r, c) for c in range(1, 5)], 'max')
    if name == 'rq2-robustness':
        for r in range(len(rows)):
            for c in [1, 3, 5]:
                best([(r, c), (r, c + 1)], 'min')
    if name == 'phone-selected-runtimes':
        for start in range(0, len(rows), 2):
            for c in [2, 3]:
                best([(start, c), (start + 1, c)], 'min')
    return rows
