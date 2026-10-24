import unittest
from unittest.mock import patch

import build


class DeliverableBuildTest(unittest.TestCase):
    def test_content_rebuilds_all_four_deliverables(self):
        with patch.object(build, 'run') as run:
            build.build_deliverables('content', 'bibtex')
        self.assertEqual(
            [call.args[0][2] for call in run.call_args_list],
            ['bulletin-vi', 'bulletin-en', 'summary-vi', 'summary-en'],
        )
        for call in run.call_args_list:
            self.assertEqual(call.args[0][-2:], ['--bibliography', 'bibtex'])

    def test_individual_deliverable_does_not_recurse(self):
        with patch.object(build, 'run') as run:
            build.build_deliverables('summary-vi', 'auto')
        run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
