"""Scientific boundary tests; fixtures below are synthetic and never training data."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from predict import predict
from train import validate_dataset
from validate_vi_intake import validate


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.records = self.root / 'records.csv'
        self.annotations = self.root / 'annotations.csv'
        self.approval = self.root / 'approval.json'
        image = self.root / 'fixture.bin'
        image.write_bytes(b'synthetic hash fixture, not a real image')
        self.record = dict(report_id='fixture', event_id='event', source_id='source', source_url='fixture://local',
                           usage_basis='test_fixture_only', language='vi', text='fixture', image_path='fixture.bin',
                           image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(), privacy_review_ref='fixture')
        self.votes = [dict(report_id='fixture', annotator_id=a, stage=s, label='review', evidence_ref='fixture', label_origin='human')
                      for a, s in [('a', 'independent'), ('b', 'independent'), ('c', 'adjudicated')]]
        self.spec = dict(status='APPROVED_BY_RESPONSIBLE_HUMAN', task='fixture', labels=['review'],
                         approved_by='fixture', expert_ref='fixture', guideline_ref='fixture')

    def write(self, records=None, votes=None, spec=None):
        for path, rows, fields in [(self.records, records if records is not None else [self.record], list(self.record)),
                                   (self.annotations, votes if votes is not None else self.votes, list(self.votes[0]))]:
            with path.open('w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
        self.approval.write_text(json.dumps(spec if spec is not None else self.spec))

    def test_empty_is_no_go(self):
        self.write(records=[], votes=[], spec={})
        self.assertEqual(validate(self.records, self.annotations, self.approval)['status'], 'NO_GO')

    def test_fixture_pass_means_only_protocol_review(self):
        self.write()
        self.assertEqual(validate(self.records, self.annotations, self.approval)['status'], 'GO_PROTOCOL_REVIEW')

    def test_single_annotator_cannot_pass(self):
        self.write(votes=[self.votes[0], self.votes[2]])
        self.assertIn('FEWER_THAN_TWO_ANNOTATORS:fixture', validate(self.records, self.annotations, self.approval)['issues'])

    def test_generated_labels_cannot_pass(self):
        votes = [dict(r, label_origin='model') for r in self.votes]
        self.write(votes=votes)
        self.assertIn('NON_HUMAN_OR_UNDECLARED_LABEL:fixture', validate(self.records, self.annotations, self.approval)['issues'])

    def test_draft_approval_cannot_pass(self):
        self.write(spec=dict(self.spec, status='DRAFT_NOT_APPROVED'))
        self.assertIn('NO_TARGET_AND_EXPERT_APPROVAL', validate(self.records, self.annotations, self.approval)['issues'])

    def test_unapproved_label_cannot_pass(self):
        self.write(votes=[dict(r, label='new_label') for r in self.votes])
        self.assertIn('LABEL_OUTSIDE_APPROVED_SCHEMA:fixture', validate(self.records, self.annotations, self.approval)['issues'])

    def test_wrong_hash_cannot_pass(self):
        self.write(records=[dict(self.record, image_sha256='bad')])
        self.assertIn('IMAGE_HASH_MISMATCH:fixture', validate(self.records, self.annotations, self.approval)['issues'])


class BoundaryTests(unittest.TestCase):
    def test_english_artifact_rejects_vietnamese_scope(self):
        with self.assertRaisesRegex(ValueError, 'English'):
            predict('fixture', None, 'vi')

    def test_no_modalities_rejected(self):
        with self.assertRaisesRegex(ValueError, 'nonempty'):
            predict('', None, 'en')

    def test_cross_event_leakage_rejected(self):
        rows = [dict(image_id=f'{s}{i}', tweet_id=f'{s}{i}', text_normalized=f'{s}{i}',
                     image_sha256=f'{s}{i}', group_id=f'{s}{i}', event_name=s,
                     split=s, label=l) for s in ['train', 'dev', 'test'] for i, l in enumerate(['no', 'yes'])]
        validate_dataset(rows, ['no', 'yes'])
        rows[-1]['event_name'] = 'train'
        with self.assertRaisesRegex(ValueError, 'event_name'):
            validate_dataset(rows, ['no', 'yes'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
