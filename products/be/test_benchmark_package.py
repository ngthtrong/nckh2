import csv
import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_benchmark_package as builder


class BenchmarkPackageTest(unittest.TestCase):
    def test_package_identifies_split_and_preserves_image_offsets(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            split = root / 'split.csv'
            samples = []
            for label in ('low', 'medium', 'high', 'non_flood'):
                image = root / label / 'sample.jpg'
                image.parent.mkdir()
                image.write_bytes(label.encode())
                samples.append({'split': 'test', 'label': label,
                                'relative_path': f'{label}/sample.jpg'})
            with split.open('w', newline='', encoding='utf-8') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(samples[0]))
                writer.writeheader()
                writer.writerows(samples)
            output = root / 'package.rhb'
            with patch.multiple(builder, SPLIT_CSV=split, IMAGE_ROOT=root, OUTPUT=output):
                builder.main()
            data = output.read_bytes()
            size = struct.unpack('>I', data[4:8])[0]
            manifest = json.loads(data[8:8 + size])
            digest = hashlib.sha256(split.read_bytes()).hexdigest()
            self.assertIn('splitCsvSha256', manifest)
            self.assertEqual(manifest['splitCsvSha256'], digest)
            self.assertIn(digest[:12], manifest['datasetName'])
            for sample in manifest['samples']:
                self.assertEqual(data[sample['offset']:sample['offset'] + sample['length']],
                                 sample['label'].encode())


if __name__ == '__main__':
    unittest.main()
