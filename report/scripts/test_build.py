import unittest
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import build
import export_drawio_diagrams as diagrams


class DiagramExportTest(unittest.TestCase):
    def test_failed_export_stops_build(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'broken.drawio').touch()
            with patch.object(diagrams, 'DIAGRAMS_DIR', root), \
                 patch.object(diagrams, 'find_drawio', return_value='drawio'), \
                 patch.object(diagrams.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'drawio')), \
                 self.assertRaises(SystemExit) as error:
                diagrams.main()
            self.assertEqual(error.exception.code, 1)

    def test_exports_only_missing_or_stale_pdfs(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ['missing', 'stale', 'current']:
                source = root / (name + '.drawio')
                source.touch()
                os.utime(source, (100, 100))
            for name, timestamp in [('stale', 50), ('current', 150)]:
                pdf = root / (name + '.pdf')
                pdf.touch()
                os.utime(pdf, (timestamp, timestamp))
            with patch.object(diagrams, 'DIAGRAMS_DIR', root), \
                 patch.object(diagrams, 'find_drawio', return_value='drawio'), \
                 patch.object(diagrams.subprocess, 'run') as run:
                run.side_effect = lambda cmd, **kwargs: Path(cmd[-2]).write_bytes(b'%PDF-test')
                diagrams.main()
            self.assertEqual(
                [Path(call.args[0][-1]).stem for call in run.call_args_list],
                ['missing', 'stale'],
            )

    def test_report_refreshes_diagrams_before_compiling(self):
        with patch.object(build, 'run') as run:
            build.build_diagrams('content')
        run.assert_called_once_with([build.sys.executable, 'scripts/export_drawio_diagrams.py'])

    def test_deliverable_does_not_export_diagrams(self):
        with patch.object(build, 'run') as run:
            build.build_diagrams('summary-vi')
        run.assert_not_called()


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
