import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    'e2e_run_images', Path(__file__).resolve().parents[1] / 'e2e_system.py'
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class RunImageTests(unittest.TestCase):
    def test_run_001_uses_selected_high_image(self):
        inputs = runner.select_inputs(1, runner.CSV_PATH, None)
        self.assertEqual(inputs['image_relative_path'], 'high/flood_4800.jpg')
        self.assertEqual(inputs['image_label'], 'high')
        self.assertEqual(inputs['csv_val_count'], 257)

    def test_run_002_uses_selected_medium_image(self):
        inputs = runner.select_inputs(2, runner.CSV_PATH, None)
        self.assertEqual(inputs['image_relative_path'], 'medium/flood_6286.jpg')
        self.assertEqual(inputs['image_label'], 'medium')
        self.assertEqual(inputs['csv_val_count'], 257)

    def test_explicit_historical_high_image_remains_supported(self):
        inputs = runner.select_inputs(2, runner.CSV_PATH, 'high/floods_cambodia_avid_w.jpg')
        self.assertEqual(inputs['image_relative_path'], 'high/floods_cambodia_avid_w.jpg')
        self.assertEqual(inputs['image_label'], 'high')

    def test_explicit_medium_image_is_supported(self):
        inputs = runner.select_inputs(1, runner.CSV_PATH, 'medium/flood_6286.jpg')
        self.assertEqual(inputs['image_label'], 'medium')

    def test_non_validation_or_unsafe_path_is_rejected(self):
        with self.assertRaises(ValueError):
            runner.select_inputs(1, runner.CSV_PATH, '../outside.jpg')

    def test_pinned_label_and_hash_are_checked(self):
        original = json.loads(runner.RUN_IMAGES_FILE.read_text(encoding='utf-8'))
        for field, wrong in [('label', 'medium'), ('sha256', '0' * 64)]:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                config = json.loads(json.dumps(original))
                config['runs']['run_001'][field] = wrong
                path = Path(directory) / 'run_images.json'
                path.write_text(json.dumps(config), encoding='utf-8')
                with patch.object(runner, 'RUN_IMAGES_FILE', path), self.assertRaises(ValueError):
                    runner.select_inputs(1, runner.CSV_PATH, None)

    def test_other_run_keeps_historical_high_default(self):
        inputs = runner.select_inputs(3, runner.CSV_PATH, None)
        self.assertEqual(inputs['image_relative_path'], 'high/floods_cambodia_avid_w.jpg')


if __name__ == '__main__':
    unittest.main()
