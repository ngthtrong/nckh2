"""FIXTURE_ONLY technical contracts; no corpus labels or performance evidence.

All data created here are tiny synthetic structures in TemporaryDirectory.
Tests never train a classifier, load an encoder, download weights, or access the
real pilot dataset. The required silver-origin field exercises the loader's
schema; it does not make these test strings research observations.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from scipy import sparse

import common
from train import concat


class DatasetContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='vi-rescue-fixture-only-')
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.base = root / 'technical-base'
        self.out = root / 'technical-output'
        (self.base / 'data').mkdir(parents=True)
        self.out.mkdir()
        self.protocol = self.out / 'protocol.json'
        self.protocol.write_text(json.dumps({'fixture_only': True, 'version': 1}) + '\n')
        records = []
        for split in ['train', 'dev', 'test']:
            for number, label in enumerate(common.LABELS):
                ident = f'{split}-{number}'
                records.append({
                    'image_id': 'fixture-image-' + ident,
                    'tweet_id': 'fixture-tweet-' + ident,
                    'group_id': 'fixture-group-' + ident,
                    'image_sha256': hashlib.sha256(ident.encode()).hexdigest(),
                    'event_name': 'fixture-event-' + split,
                    'split': split,
                    'text_vi': f'Chuỗi kỹ thuật {ident}, không phải bản tin thực.',
                    'label': label,
                })
        self.data = {'fixture_only': True, 'task': common.TASK,
                     'label_origin': 'AI_SILVER_TEXT_ONLY', 'records': records}
        self.dataset = self.base / 'data/dataset.json'
        self.save_and_lock()
        for key, value in [('BASE', self.base), ('OUT', self.out), ('PROTOCOL', self.protocol)]:
            current = patch.object(common, key, value)
            current.start()
            self.addCleanup(current.stop)

    def save_and_lock(self):
        self.dataset.write_text(json.dumps(self.data, ensure_ascii=False, indent=2) + '\n')
        (self.out / 'dataset-lock.json').write_text(json.dumps({
            'protocol_sha256': common.digest(self.protocol),
            'dataset_sha256': common.digest(self.dataset),
        }) + '\n')

    def assert_rejected_mutation(self, mutation, message):
        mutation(self.data)
        self.save_and_lock()
        with self.assertRaisesRegex(ValueError, message):
            common.load_data()

    def test_accepts_valid_fixture_with_two_classes_per_split(self):
        self.assertEqual(common.load_data(), self.data['records'])

    def test_duplicate_pair_id_is_rejected(self):
        self.assert_rejected_mutation(
            lambda data: data['records'][1].update(image_id=data['records'][0]['image_id']),
            'Duplicate pair IDs')

    def test_cross_split_image_hash_is_rejected(self):
        self.assert_rejected_mutation(
            lambda data: data['records'][2].update(image_sha256=data['records'][0]['image_sha256']),
            'Cross-split overlap: image_sha256')

    def test_cross_split_event_is_rejected(self):
        self.assert_rejected_mutation(
            lambda data: data['records'][2].update(event_name=data['records'][0]['event_name']),
            'Cross-split overlap: event_name')

    def test_cross_split_duplicate_group_is_rejected(self):
        self.assert_rejected_mutation(
            lambda data: data['records'][2].update(group_id=data['records'][0]['group_id']),
            'Cross-split overlap: group_id')

    def test_cross_split_source_post_is_rejected(self):
        self.assert_rejected_mutation(
            lambda data: data['records'][2].update(tweet_id=data['records'][0]['tweet_id']),
            'Cross-split overlap: tweet_id')

    def test_translated_text_overlap_ignores_urls_mentions_and_case(self):
        def mutation(data):
            data['records'][0]['text_vi'] = 'CẦN  trợ giúp https://example.invalid/a'
            data['records'][2]['text_vi'] = 'cần trợ giúp @nguoinhan'
        self.assert_rejected_mutation(mutation, 'Translated-text overlap across splits')

    def test_empty_cleaned_text_cannot_overlap_across_splits(self):
        def mutation(data):
            data['records'][0]['text_vi'] = 'https://example.invalid/a'
            data['records'][2]['text_vi'] = '@nguoinhan'
        self.assert_rejected_mutation(mutation, 'Translated-text overlap across splits')

    def test_split_missing_positive_class_is_rejected(self):
        self.assert_rejected_mutation(
            lambda data: data['records'][3].update(label='no_request'),
            'A split lacks both classes')

    def test_uncertain_is_not_silently_fitted_as_binary_class(self):
        self.assert_rejected_mutation(
            lambda data: data['records'][0].update(label='uncertain'),
            'A split lacks both classes')

    def test_dataset_byte_tampering_breaks_lock(self):
        self.dataset.write_text(self.dataset.read_text() + ' ')
        with self.assertRaisesRegex(ValueError, 'Dataset changed'):
            common.load_data()

    def test_protocol_tampering_breaks_lock(self):
        self.protocol.write_text(json.dumps({'fixture_only': True, 'version': 2}) + '\n')
        with self.assertRaisesRegex(ValueError, 'Protocol changed after dataset lock'):
            common.load_data()

    def test_different_task_is_rejected_even_with_matching_hash(self):
        self.assert_rejected_mutation(
            lambda data: data.update(task='public_crisis_informativeness'),
            'Wrong task or label origin')

    def test_human_origin_cannot_replace_silver_marker(self):
        self.assert_rejected_mutation(
            lambda data: data.update(label_origin='HUMAN_EXPERT_GOLD'),
            'Wrong task or label origin')

    def test_unspecified_origin_is_rejected(self):
        self.assert_rejected_mutation(
            lambda data: data.update(label_origin=''),
            'Wrong task or label origin')


class ImmutableOutputContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='vi-rescue-output-fixture-only-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_json_overwrite_fails_and_preserves_original_bytes(self):
        path = self.root / 'nested/result.json'
        common.write_json(path, {'fixture_only': True, 'value': 'ban đầu'})
        before = path.read_bytes()
        with self.assertRaises(FileExistsError):
            common.write_json(path, {'fixture_only': True, 'value': 'thay thế'})
        self.assertEqual(path.read_bytes(), before)

    def test_csv_overwrite_fails_and_preserves_original_bytes(self):
        path = self.root / 'nested/result.csv'
        common.write_csv(path, [{'id': 'fixture-1', 'label': 'request'}])
        before = path.read_bytes()
        with self.assertRaises(FileExistsError):
            common.write_csv(path, [{'id': 'fixture-2', 'label': 'no_request'}])
        self.assertEqual(path.read_bytes(), before)

    def test_unicode_json_roundtrips_and_has_terminal_newline(self):
        path = self.root / 'unicode.json'
        value = {'fixture_only': True, 'text': 'Không cần thêm người; có 12 người.'}
        common.write_json(path, value)
        self.assertEqual(common.read_json(path), value)
        self.assertTrue(path.read_bytes().endswith(b'\n'))

    def test_csv_explicit_column_order_roundtrips(self):
        path = self.root / 'ordered.csv'
        common.write_csv(path, [{'label': 'request', 'id': 'fixture-1'}], ['id', 'label'])
        with path.open(newline='') as stream:
            reader = csv.DictReader(stream)
            self.assertEqual(reader.fieldnames, ['id', 'label'])
            self.assertEqual(list(reader), [{'id': 'fixture-1', 'label': 'request'}])


class PreprocessingContracts(unittest.TestCase):
    def test_cleaning_preserves_vietnamese_negation_and_numbers(self):
        source = '  Không  cần cứu  Ａ 12 người @nguoinhan https://example.invalid/a  '
        self.assertEqual(common.clean_text(source), 'Không cần cứu A 12 người')

    def test_cleaning_preserves_case_and_collapses_whitespace(self):
        self.assertEqual(common.clean_text('Cần\n\tNước sạch Ở Huế'), 'Cần Nước sạch Ở Huế')

    def test_only_link_and_mention_yields_empty_not_invented_text(self):
        self.assertEqual(common.clean_text('www.example.invalid @abc'), '')

    def test_concat_scales_each_block_by_inverse_sqrt_two(self):
        text = np.array([[1., 0.], [0., 1.]])
        image = np.array([[0., 1., 0.], [1., 0., 0.]])
        result = concat(sparse.csr_matrix(text), image)
        expected = np.hstack([text, image]) / math.sqrt(2)
        self.assertTrue(sparse.isspmatrix_csr(result))
        np.testing.assert_allclose(result.toarray(), expected)
        np.testing.assert_allclose(np.linalg.norm(result.toarray(), axis=1), [1., 1.])

    def test_zero_block_stays_zero_without_renormalizing_other_block(self):
        result = concat(np.array([[1., 0.]]), sparse.csr_matrix((1, 3)))
        np.testing.assert_allclose(result.toarray(), [[1 / math.sqrt(2), 0., 0., 0., 0.]])
        self.assertEqual(result.shape, (1, 5))
        self.assertEqual(result.nnz, 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
