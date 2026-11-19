"""Exact-copy regression checks for the deployed adapter, not an RQ re-run."""
from copy import deepcopy
import unittest

from cluster_service import compute_clusters


def reports():
    return [{
        'id': f'r{i}', 'createdAt': f'2026-09-24T08:{i:02}:00Z',
        'lat': 16.0 + i * .0002, 'lng': 108.0 + i * .0001,
        'description': 'Có người mắc kẹt', 'trappedCount': 2,
        'injuredCount': 0, 'aiTags': [{'label': 'high', 'confidence': .9}],
        'payload': {}, 'status': 'processing',
    } for i in range(8)]


class GraphTransportDedupTest(unittest.TestCase):
    def test_multiplicity_does_not_change_graph_or_priority(self):
        original = reports()
        baseline = compute_clusters(original)
        for multiplicity in [2, 5]:
            with self.subTest(multiplicity=multiplicity):
                copied = deepcopy(original)
                for copy in range(1, multiplicity):
                    for source in original:
                        item = deepcopy(source)
                        item['id'] = f'copy-{copy}-{source["id"]}'
                        item['serverReceivedAt'] = '2026-09-25T12:00:00Z'
                        copied.append(item)
                got = compute_clusters(copied)
                self.assertEqual(got['candidatePairs'], baseline['candidatePairs'])
                self.assertEqual(got['retainedEdges'], baseline['retainedEdges'])
                self.assertEqual(got['thresholdWeight'], baseline['thresholdWeight'])
                self.assertEqual(got['graphDeduplication']['canonicalReports'], len(original))
                self.assertEqual(got['graphDeduplication']['exactCopiesRemoved'], len(copied) - len(original))
                self.assertEqual({rid for c in got['clusters'] for rid in c['reportIds']},
                                 {r['id'] for r in copied})
                expected = {frozenset(c['reportIds']): c for c in baseline['clusters']}
                for cluster in got['clusters']:
                    ids = frozenset(rid for rid in cluster['reportIds'] if not rid.startswith('copy-'))
                    before = expected[ids]
                    self.assertAlmostEqual(cluster['priority'], before['priority'])
                    self.assertEqual(cluster['centroid'], before['centroid'])

    def test_equal_scalar_features_do_not_merge_different_text(self):
        data = reports()
        other = deepcopy(data[0])
        other.update(id='different-text', description='Có người mắc kẹt, cửa đang bị chắn')
        data.append(other)
        got = compute_clusters(data)
        self.assertEqual(got['graphDeduplication']['canonicalReports'], len(data))
        self.assertEqual(got['graphDeduplication']['exactCopiesRemoved'], 0)

    def test_review_keeps_all_original_ids(self):
        data = reports()
        for identity in ['missing-1', 'missing-2']:
            row = deepcopy(data[0])
            row.update(id=identity, lat=None, lng=None)
            data.append(row)
        got = compute_clusters(data)
        self.assertEqual(set(got['review']), {'missing-1', 'missing-2'})
        self.assertNotIn('missing-1', {rid for c in got['clusters'] for rid in c['reportIds']})


if __name__ == '__main__':
    unittest.main()
