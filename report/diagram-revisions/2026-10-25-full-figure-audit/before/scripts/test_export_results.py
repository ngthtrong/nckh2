import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import export_results


class ExportResultsTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        state = patch.multiple(export_results, OUT=Path(folder.name),
                               SOURCES={}, PREDICTION_AUDITS=[], TABLE_NOTES={})
        state.start()
        self.addCleanup(state.stop)

    def test_historical_benchmarks_are_independent_of_active_checkpoint_config(self):
        read_bytes = export_results.read_bytes

        def evidence_bytes(path):
            if path == 'products/fe/model/Edge Ai/config_mobilenetv3_large.json':
                return b'active training config is unrelated to saved benchmarks'
            return read_bytes(path)

        with patch.object(export_results, 'read_bytes', side_effect=evidence_bytes):
            with contextlib.redirect_stdout(io.StringIO()):
                export_results.main()
        values = (export_results.OUT / 'values.tex').read_text()
        sources = json.loads((export_results.ROOT / 'report/config/benchmark-sources.json').read_text())
        base = json.loads((export_results.ROOT / sources['fp32'] / 'summary.json').read_text())
        self.assertIn('\\newcommand{\\BenchmarkSeed}{' + str(base['metadata']['seed']) + '}', values)
        self.assertIn('\\newcommand{\\NewImageAccuracy}', values)

    def test_seed1024_validation_evidence_cannot_include_training_images(self):
        read_rows = export_results.rows
        train = next(row for row in read_rows(
            'products/fe/model/Edge Ai/split_train_val_test_mobilenetv3_large.csv')
                     if row['split'] == 'train')

        def rows_with_wrong_validation(path):
            if path.endswith('seed1024/misclassified_val_mobilenetv3_large.csv'):
                return [{'relative_path': train['relative_path'], 'true_label': train['label']}]
            return read_rows(path)

        with patch.object(export_results, 'rows', side_effect=rows_with_wrong_validation):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, 'Validation artifact'):
                    export_results.main()

    def test_verification_must_cover_the_same_full_test_and_checkpoint(self):
        read_object = export_results.obj
        sources = read_object('report/config/benchmark-sources.json')
        original = read_object(sources['verification'])
        for field, value in [('n_images', 3), ('evaluation_scope', 'test_subset_smoke'),
                             ('checkpoint_sha256', 'different checkpoint')]:
            with self.subTest(field=field):
                verification = copy.deepcopy(original)
                verification['metadata'][field] = value

                def object_with_wrong_verification(path):
                    return verification if path == sources['verification'] else read_object(path)

                with patch.object(export_results, 'obj', side_effect=object_with_wrong_verification):
                    with contextlib.redirect_stdout(io.StringIO()):
                        with self.assertRaisesRegex(ValueError, 'Verification scope'):
                            export_results.main()


if __name__ == '__main__':
    unittest.main()
