import unittest

from highlight_results import highlight_results


class HighlightResultsTest(unittest.TestCase):
    def test_column_directions_ties_and_decimal_comma(self):
        rows = [['A', '80,00', '75,00', '2', '4,00', '20,00'],
                ['B', '80,00', '76,00', '3', '4,50', '10,00']]
        result = highlight_results('fp32_ptq_qat', rows)
        self.assertEqual(result[0][1:4], [r'\textbf{80,00}', '75,00', r'\textbf{2}'])
        self.assertEqual(result[1][1:4], [r'\textbf{80,00}', r'\textbf{76,00}', '3'])
        self.assertEqual(result[0][4], r'\textbf{4,00}')
        self.assertEqual(result[1][5], r'\textbf{10,00}')
        self.assertEqual(rows[0][1], '80,00')

    def test_ci_and_cluster_diameter_are_not_ranked(self):
        result = highlight_results('rq1-benchmark', [
            ['A', '0.91 [0.89; 0.93]', '0.92', '0.4'],
            ['B', '0.90 [0.88; 0.94]', '0.91', '0.3']])
        self.assertEqual(result[0][1], r'\textbf{0.91} [0.89; 0.93]')
        self.assertEqual(result[1][3], '0.3')

    def test_stress_compares_methods_within_each_condition(self):
        result = highlight_results('rq1-stress', [['GPS', '0.8', '0.7', '0.9', '0.4'],
                                                    ['Copy', '0.3', '0.3', '0.3', '0.5']])
        self.assertEqual(result[0][3], r'\textbf{0.9}')
        self.assertEqual(result[1][4], r'\textbf{0.5}')
        self.assertEqual(result[1][1], '0.3')

    def test_robustness_compares_each_metric_pair_with_ties(self):
        result = highlight_results('rq2-robustness', [['Exact', '0', '0.1', '0.2', '0', '0', '0']])[0]
        self.assertEqual(result[1:], [r'\textbf{0}', '0.1', '0.2', r'\textbf{0}', r'\textbf{0}', r'\textbf{0}'])

    def test_pruning_compares_within_runtime(self):
        rows = [['PTH base', '75', '74', '3', '48', '38'], ['PTH prune', '80', '78', '4', '16', '24'],
                ['ONNX base', '75', '74', '3', '16', '10'], ['ONNX prune', '80', '78', '4', '15', '17']]
        result = highlight_results('pruning_st', rows)
        self.assertEqual(result[1][5], r'\textbf{24}')
        self.assertEqual(result[2][5], r'\textbf{10}')
        self.assertEqual(result[3][5], '17')

    def test_counts_and_contrasts_are_unchanged(self):
        for name in ['confusion', 'image-split', 'rq3-effects', 'phone-full-quality']:
            rows = [['A', '1', '2'], ['B', '3', '4']]
            self.assertEqual(highlight_results(name, rows), rows)


if __name__ == '__main__':
    unittest.main()
